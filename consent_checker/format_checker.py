from rules import FORMAT_RULES
from doc_parser import ParsedDocument


TITLE_KEYWORDS = ["목적", "항목", "기간", "권리", "제공", "철회", "개인정보", "수집", "이용", "보유", "동의", "처리", "위탁"]


def _is_likely_title(p) -> bool:
    text = p.full_text().strip()
    if not text:
        return False
    style = (p.style_name or "").lower()
    if style in ("h1", "h2", "h3", "h4", "h5", "h6", "th", "title", "heading"):
        return True
    if not text.rstrip().endswith(".") and len(text) <= 30:
        if any(kw in text for kw in TITLE_KEYWORDS):
            return True
        if ":" in text:
            return True
    return False


def check_format(doc: ParsedDocument) -> list[dict]:
    results = []
    fm = FORMAT_RULES["min_body_font_size"]
    min_size = fm["value"]

    small_font_paras = []
    non_bold_titles = []
    no_format_paras = []

    for i, p in enumerate(doc.paragraphs):
        text = p.full_text()
        if not text:
            continue

        if p.font_size is not None and p.font_size < min_size:
            sug = f"{i+1}번째 문단 '{text[:40]}...'의 글자 크기가 {p.font_size}pt로 기준({min_size}pt) 미만입니다. 글자 크기를 {min_size}pt 이상으로 조정하세요."
            small_font_paras.append({
                "index": i,
                "text": text[:60],
                "size": p.font_size,
                "suggestion": sug,
            })

        if _is_likely_title(p):
            if p.bold is not None and not p.bold:
                sug = f"{i+1}번째 문단 '{text[:40]}...'은(는) 제목으로 판단되나 굵게(Bold) 처리되지 않았습니다. Bold 서식을 적용하여 가독성을 높이세요."
                non_bold_titles.append({
                    "index": i,
                    "text": text[:60],
                    "suggestion": sug,
                })
            elif p.bold is None:
                sug = f"{i+1}번째 문단 '{text[:40]}...'은(는) 제목으로 보이나 서식 정보가 없습니다. Bold 서식을 적용하는 것을 권장합니다."
                non_bold_titles.append({
                    "index": i,
                    "text": text[:60],
                    "suggestion": sug,
                })

        if p.font_size is None and text.strip():
            no_format_paras.append({
                "index": i,
                "text": text[:60],
            })

    ft = FORMAT_RULES["title_required_bold"]
    results.append({
        "check": "min_font_size",
        "name": "본문 폰트 크기",
        "passed": len(small_font_paras) == 0,
        "detail": f"최소 기준: {min_size}pt",
        "failed_items": small_font_paras,
        "guide": f"본문 텍스트는 최소 {min_size}pt 이상을 권장합니다.",
        "law_basis": fm["law_basis"],
        "law_detail": fm["law_detail"],
    })

    results.append({
        "check": "title_bold",
        "name": "제목 굵게 표시",
        "passed": len(non_bold_titles) == 0,
        "detail": f"제목/헤더 {len(non_bold_titles)}개가 Bold 처리되지 않음" if non_bold_titles else "모든 제목 Bold 처리됨",
        "failed_items": non_bold_titles,
        "guide": "제목 또는 섹션 헤더는 굵게(Bold) 표시하여 가독성을 높이세요.",
        "law_basis": ft["law_basis"],
        "law_detail": ft["law_detail"],
    })

    total_paras = len([p for p in doc.paragraphs if p.full_text().strip()])
    results.append({
        "check": "format_coverage",
        "name": "서식 정보 가용성",
        "passed": len(no_format_paras) == 0,
        "detail": f"전체 {total_paras}개 문단 중 {len(no_format_paras)}개 문단에서 서식 정보 없음",
        "failed_items": no_format_paras[:10],
        "guide": "문서 형식에 따라 서식 정보가 제한적일 수 있습니다 (PDF 스캔본, TIFF 이미지, HWP 등).",
        "law_basis": fm["law_basis"],
        "law_detail": fm["law_detail"],
    })

    return results
