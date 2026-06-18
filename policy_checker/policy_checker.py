#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개인정보처리방침 컴플라이언스 점검 도구 (단일 실행 스크립트)

사용법:
    python policy_checker.py <처리방침.pdf> [--mode general|finance] [--out 결과.pdf|결과.txt]

예:
    python policy_checker.py privacy_policy.pdf --mode finance
    python policy_checker.py privacy_policy.pdf --mode general --out report.txt

필요 패키지: pdfplumber  (pip install pdfplumber)
조건부 항목(국외이전, CCTV, 가명정보, 자동화결정, 신용정보)은 문서에
관련 키워드가 있을 때만 '필수'로 점검하고, 없으면 'N/A(해당없음)'로 표시합니다.
"""
import re
import sys
import argparse

try:
    from policy_rules import items_for_mode
except ImportError:
    # 같은 폴더 실행 보장
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from policy_rules import items_for_mode


# ----------------------------- 문서 파싱 -----------------------------
class Paragraph:
    def __init__(self, text="", font_size=None, bold=None):
        self.text = text
        self.font_size = font_size
        self.bold = bold

    def full_text(self):
        return self.text


class ParsedDocument:
    def __init__(self, paragraphs):
        self.paragraphs = paragraphs


def load_pdf(path):
    import pdfplumber
    paras = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            # 라인 단위 텍스트
            txt = page.extract_text() or ""
            # 라인별 평균 글자 크기 추정 (서식 점검용)
            sizes_by_line = _line_font_sizes(page)
            for idx, ln in enumerate(txt.split("\n")):
                if not ln.strip():
                    continue
                fs = sizes_by_line.get(idx)
                paras.append(Paragraph(text=ln, font_size=fs))
    return ParsedDocument(paras)


def _line_font_sizes(page):
    """페이지의 라인별 대표 폰트 크기 추정(가능할 때만)."""
    out = {}
    try:
        words = page.extract_words(extra_attrs=["size"]) if hasattr(page, "extract_words") else []
        # 라인 인덱스를 정확히 매핑하기 어려우므로, top 좌표로 묶어 근사
        lines = {}
        for w in words:
            top = round(w.get("top", 0))
            lines.setdefault(top, []).append(w.get("size"))
        # top 정렬 순서를 라인 인덱스로 가정
        for i, top in enumerate(sorted(lines.keys())):
            sizes = [s for s in lines[top] if s]
            if sizes:
                out[i] = round(sum(sizes) / len(sizes), 2)
    except Exception:
        pass
    return out


# ----------------------------- 섹션 분할 -----------------------------
TITLE_KEYWORDS = [
    "목적", "항목", "기간", "권리", "제공", "위탁", "파기", "쿠키", "안전",
    "책임자", "구제", "변경", "국외", "가명", "영상", "자동화", "신용정보",
    "개인정보", "수집", "이용", "보유", "처리",
]


def _is_likely_title(p):
    text = p.full_text().strip()
    if not text:
        return False
    first = text.split("\n")[0].strip()
    if not first:
        return False
    # 글머리표로 시작하면 본문
    if first.lstrip()[:1] in ("-", "·", "•", "*", "▶", "‣", "￭", "■", "○"):
        return False
    # 서술형 종결어미면 본문
    if re.search(r"(합니다|입니다|하며|습니다|됩니다|있습니다|다\.)\s*$", first):
        return False
    # 번호형 제목 (1. 2. 제1조 등) 우대
    if re.match(r"^\s*(\d+[\.\)]|제?\s*\d+\s*[조항호])", first):
        return True
    if len(first) <= 40 and any(kw in first for kw in TITLE_KEYWORDS):
        return True
    return False


def _group_into_sections(paragraphs):
    sections = []
    current = {"header": None, "header_index": -1, "paragraphs": []}
    for i, p in enumerate(paragraphs):
        if not p.full_text().strip():
            continue
        if _is_likely_title(p):
            if current["header"] is not None or current["paragraphs"]:
                sections.append(current)
            current = {"header": p, "header_index": i, "paragraphs": []}
        else:
            current["paragraphs"].append(p)
    if current["header"] is not None or current["paragraphs"]:
        sections.append(current)
    return sections


def _find_matching_section(sections, header_patterns):
    best = None
    best_priority = 10 ** 9
    for sec in sections:
        if sec["header"] is None:
            continue
        text = sec["header"].full_text().split("\n")[0]
        for pat in header_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                priority = abs(len(text) - len(m.group()))
                if priority < best_priority:
                    best = {"section": sec, "matched_pattern": pat, "matched_text": m.group()}
                    best_priority = priority
                break
    return best


# ----------------------------- 내용 검증 -----------------------------
def _run_checks(text, content_patterns, required_fields):
    """text에 대해 내용 패턴/필수필드를 검사하고 누락 목록 반환."""
    missing = []
    if content_patterns:
        if not any(re.search(p, text, re.IGNORECASE) for p in content_patterns):
            missing.append("구체적 내용이 확인되지 않습니다")
    if required_fields:
        for f in required_fields:
            if not any(re.search(p, text, re.IGNORECASE) for p in f["patterns"]):
                missing.append(f"'{f['label']}' 누락")
    return missing


def _validate(section_paras, item, doc_text):
    section_text = " ".join(p.full_text() for p in section_paras if p.full_text()).strip()
    missing = _run_checks(section_text, item.get("content_patterns"), item.get("required_fields"))
    # 표 구조 등으로 섹션 본문이 비거나 검증 실패 시 문서 전체로 2차 검증
    if missing and doc_text:
        missing_doc = _run_checks(doc_text, item.get("content_patterns"), item.get("required_fields"))
        if not missing_doc:
            missing = []
    return (len(missing) == 0), missing


def _search_globally(paragraphs, header_patterns, content_patterns):
    """헤더 섹션을 못 찾았을 때, 문서 전체에서 항목 존재 흔적 탐색."""
    all_text = " ".join(p.full_text() for p in paragraphs if p.full_text())
    pats = list(header_patterns) + list(content_patterns or [])
    for pat in pats:
        m = re.search(pat, all_text, re.IGNORECASE)
        if m:
            return True
    return False


# ----------------------------- 점검 엔진 -----------------------------
def check_policy(doc, mode):
    all_text = " ".join(p.full_text() for p in doc.paragraphs if p.full_text())
    sections = _group_into_sections(doc.paragraphs)
    results = []

    for item in items_for_mode(mode):
        # 조건부 항목: 트리거 키워드 없으면 N/A
        if item.get("conditional"):
            trig = item.get("trigger_keywords", [])
            if not any(kw in all_text for kw in trig):
                results.append(_result(item, "NA"))
                continue

        match = _find_matching_section(sections, item["header_patterns"])
        if match:
            ok, missing = _validate(match["section"]["paragraphs"], item, all_text)
            status = "COMPLETE" if ok else "INCOMPLETE"
            results.append(_result(item, status, header=match["matched_text"], missing=missing))
        else:
            # 헤더 못 찾음 → 전체 검색으로 흔적이라도 있으면 INCOMPLETE, 없으면 MISSING
            if _search_globally(doc.paragraphs, item["header_patterns"], item.get("content_patterns")):
                # 전체 텍스트로 내용 검증까지 통과하면 COMPLETE 승격
                ok, missing = _validate([Paragraph(all_text)], item, all_text)
                results.append(_result(item, "COMPLETE" if ok else "INCOMPLETE", missing=missing))
            else:
                results.append(_result(item, "MISSING"))
    return results


def _result(item, status, header="", missing=None):
    return {
        "id": item["id"], "name": item["name"], "status": status,
        "header": header, "missing": missing or [],
        "law_basis": item["law_basis"], "law_detail": item["law_detail"],
        "description": item["description"],
        "incomplete_desc": item.get("incomplete_desc", item["description"]),
        "guide": item["guide"], "conditional": item.get("conditional", False),
    }


# ----------------------------- 서식 점검 -----------------------------
def check_format(doc, min_size=9):
    """처리방침 권고: 본문은 읽기 쉬운 크기(기본 9pt 기준). 측정 가능할 때만."""
    small = []
    measurable = 0
    for i, p in enumerate(doc.paragraphs):
        if p.font_size is not None:
            measurable += 1
            if p.font_size < min_size:
                small.append((i, p.full_text()[:40], p.font_size))
    return {"min_size": min_size, "measurable": measurable, "small": small,
            "total": len([p for p in doc.paragraphs if p.full_text().strip()])}


# ----------------------------- 리포트 -----------------------------
STATUS_LABEL = {"COMPLETE": "[적합]", "INCOMPLETE": "[보완필요]", "MISSING": "[누락]", "NA": "[해당없음]"}


def build_report(results, fmt, mode, filename):
    lines = []
    lines.append("=" * 60)
    lines.append("개인정보처리방침 컴플라이언스 점검 결과")
    lines.append(f"대상 파일: {filename}")
    lines.append(f"점검 모드: {'금융기관' if mode == 'finance' else '일반기업'}")
    lines.append("=" * 60)
    lines.append("")
    lines.append("1. 필수/조건부 항목 점검")
    lines.append("-" * 60)

    cnt = {"COMPLETE": 0, "INCOMPLETE": 0, "MISSING": 0, "NA": 0}
    for r in results:
        cnt[r["status"]] += 1
        tag = STATUS_LABEL[r["status"]]
        cond = " (조건부)" if r["conditional"] else ""
        lines.append(f"{tag} {r['name']}{cond}")
        if r["status"] == "COMPLETE" and r["header"]:
            lines.append(f"    - 확인 위치: {r['header']}")
        if r["status"] == "INCOMPLETE":
            lines.append(f"    - 문제: {r['incomplete_desc']}")
            for m in r["missing"]:
                lines.append(f"      · {m}")
            lines.append(f"    - 개선: {r['guide']}")
        if r["status"] == "MISSING":
            lines.append(f"    - 문제: {r['description']}")
            lines.append(f"    - 개선: {r['guide']}")
        if r["status"] == "NA":
            lines.append(f"    - 문서에 해당 처리 정황이 없어 점검 대상에서 제외")
        lines.append(f"    [근거] {r['law_basis']}")
        lines.append("")

    applicable = cnt["COMPLETE"] + cnt["INCOMPLETE"] + cnt["MISSING"]
    lines.append("-" * 60)
    lines.append(f"→ 점검대상 {applicable}개 중 적합 {cnt['COMPLETE']}, "
                 f"보완필요 {cnt['INCOMPLETE']}, 누락 {cnt['MISSING']} "
                 f"(해당없음 {cnt['NA']}개 제외)")
    lines.append("")

    # 서식
    lines.append("2. 서식 점검")
    lines.append("-" * 60)
    f = fmt
    if f["measurable"] == 0:
        lines.append("본문 글자 크기: 측정 불가 (스캔/이미지 PDF로 서식 정보 없음)")
    else:
        if f["small"]:
            lines.append(f"본문 글자 크기({f['min_size']}pt 미만) {len(f['small'])}개 문단 발견:")
            for idx, txt, sz in f["small"][:5]:
                lines.append(f"    · {idx+1}번째 '{txt}...' ({sz}pt)")
            if len(f["small"]) > 5:
                lines.append(f"    · ...외 {len(f['small'])-5}개")
        else:
            lines.append(f"본문 글자 크기: 기준({f['min_size']}pt) 충족")
    lines.append(f"[근거] 「개인정보 보호법」 제30조③ 처리방침은 정보주체가 쉽게 확인할 수 있도록 작성")
    lines.append("")
    lines.append("※ 본 점검은 자동화 도구의 1차 스크리닝이며, 최종 적합 판단은 전문가 검토가 필요합니다.")
    return "\n".join(lines)


# ----------------------------- 메인 -----------------------------
def main():
    ap = argparse.ArgumentParser(description="개인정보처리방침 컴플라이언스 점검")
    ap.add_argument("pdf", help="점검할 처리방침 PDF 경로")
    ap.add_argument("--mode", choices=["general", "finance"], default="general",
                    help="점검 모드: general(일반기업, 기본) / finance(금융기관)")
    ap.add_argument("--out", default=None, help="결과 저장 경로(.txt). 미지정 시 화면 출력")
    ap.add_argument("--min-size", type=float, default=9.0, help="본문 최소 글자 크기(pt)")
    args = ap.parse_args()

    doc = load_pdf(args.pdf)
    results = check_policy(doc, args.mode)
    fmt = check_format(doc, args.min_size)
    report = build_report(results, fmt, args.mode, args.pdf)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fp:
            fp.write(report)
        print(f"결과 저장: {args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
