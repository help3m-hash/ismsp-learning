import re
from rules import MANDATORY_CLAUSES
from doc_parser import ParsedDocument

TITLE_KEYWORDS = [
    "목적", "항목", "기간", "권리", "제공", "철회",
    "개인정보", "수집", "이용", "보유", "동의", "처리", "위탁",
]


def _first_line(text: str) -> str:
    return text.split("\n")[0].strip()


def _body_after_header(paragraph) -> str:
    text = paragraph.full_text()
    if "\n" in text:
        rest = text.split("\n", 1)[1].strip()
        return rest
    return ""


def _is_likely_title(p) -> bool:
    text = p.full_text().strip()
    if not text:
        return False
    first = _first_line(text)
    if not first:
        return False
    style = (p.style_name or "").lower()
    if style in ("h1", "h2", "h3", "h4", "h5", "h6", "th", "title", "heading"):
        return True
    # 글머리표(-, ·, •)로 시작하면 본문 항목이지 제목이 아님
    if first.lstrip()[:1] in ("-", "·", "•", "*"):
        return False
    # 서술형 종결어미로 끝나면 본문 문장 (제목은 보통 명사구로 끝남)
    if re.search(r"(합니다|입니다|하며|습니다|됩니다|있습니다|준수)\s*\.?$", first):
        return False
    if not first.rstrip().endswith(".") and len(first) <= 30:
        if any(kw in first for kw in TITLE_KEYWORDS):
            return True
        # 콜론은 뒤따르는 내용이 짧을 때만 제목으로 (긴 나열은 본문)
        if ":" in first and len(first.split(":", 1)[1].strip()) <= 10:
            return True
    return False


def _make_body_paragraph(body_text: str, original_index: int):
    from doc_parser import Paragraph
    p = Paragraph(text=body_text)
    return p


def _group_into_sections(paragraphs: list) -> list[dict]:
    sections = []
    current = {"header": None, "header_index": -1, "paragraphs": []}

    for i, p in enumerate(paragraphs):
        if not p.full_text().strip():
            continue
        if _is_likely_title(p):
            if current["header"] is not None or current["paragraphs"]:
                sections.append(current)
            rest = _body_after_header(p)
            current = {
                "header": p,
                "header_index": i,
                "paragraphs": [],
            }
            if rest:
                current["paragraphs"].append(_make_body_paragraph(rest, i))
        else:
            current["paragraphs"].append(p)

    if current["header"] is not None or current["paragraphs"]:
        sections.append(current)

    return sections


def _find_matching_section(sections: list[dict], header_patterns: list[str]):
    best = None
    best_priority = 999

    for sec in sections:
        if sec["header"] is None:
            continue
        text = _first_line(sec["header"].full_text())
        for pat in header_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                priority = abs(len(text) - len(m.group()))
                if best is None or priority < best_priority:
                    best = {
                        "section": sec,
                        "matched_pattern": pat,
                        "matched_text": m.group(),
                    }
                    best_priority = priority
                break

    return best


def _search_globally(paragraphs: list, patterns: list[str], limit=3):
    for i, p in enumerate(paragraphs):
        text = p.full_text()
        if not text:
            continue
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                start = max(0, m.start() - 20)
                end = min(len(text), m.end() + 20)
                context = text[start:end].strip()
                return {
                    "paragraph_index": i,
                    "matched_pattern": pat,
                    "matched_text": m.group(),
                    "context": context,
                }
    return None


def _check_trigger(paragraphs: list, trigger_patterns: list[str]) -> bool:
    all_text = " ".join(p.full_text() for p in paragraphs if p.full_text())
    for kw in trigger_patterns:
        if kw in all_text:
            return True
    return False


def _run_checks(all_text: str, section_text: str, content_rules: dict) -> list[str]:
    missing = []
    min_length = content_rules.get("min_length", 0)
    if min_length and len(all_text) < min_length:
        missing.append(f"내용이 너무 짧습니다 (최소 {min_length}자 필요, 현재 {len(section_text)}자)")

    required_fields = content_rules.get("required_fields")
    if required_fields:
        for field in required_fields:
            found = any(re.search(pat, all_text, re.IGNORECASE) for pat in field["patterns"])
            if not found:
                missing.append(f"'{field['label']}' 항목 누락")

    required_patterns = content_rules.get("required_patterns")
    if required_patterns:
        # 서명란 날짜(예: '2019년 월 일')는 보유기간 값이 아니므로 제외
        scan_text = re.sub(r"\d{4}\s*년\s*\d{0,2}\s*월\s*\d{0,2}\s*일", " ", all_text)
        found_any = any(re.search(pat, scan_text, re.IGNORECASE) for pat in required_patterns)
        if not found_any:
            missing.append("필수 항목 내용(구체적 값)이 명시되지 않았습니다")
    return missing


def _validate_content(paragraphs: list, content_rules: dict, doc_text: str = "") -> tuple[bool, list[str]]:
    section_text = " ".join(p.full_text() for p in paragraphs if p.full_text()).strip()

    # 1차: 섹션 본문으로 검증
    missing = _run_checks(section_text, section_text, content_rules)

    # 2차: 섹션 검증 실패 시, 표 구조(라벨/내용 분리) 대비 문서 전체로 재검증
    # 단, 내용성 검증(required_fields/patterns)이 있는 항목만 doc_text로 구제.
    # min_length 단독 항목은 doc_text 전체가 거의 항상 통과하므로 구제 대상에서 제외.
    if missing and doc_text:
        has_content_rule = bool(content_rules.get("required_fields") or content_rules.get("required_patterns"))
        if has_content_rule:
            missing_doc = _run_checks(doc_text, section_text, content_rules)
            # doc_text 기준으로 내용 검증을 통과하면 구제 (min_length 메시지는 무시)
            content_missing = [m for m in missing_doc if not m.startswith("내용이 너무 짧")]
            if not content_missing:
                missing = []

    is_valid = len(missing) == 0
    return is_valid, missing


def _make_result(clause: dict, status: str, header_found: bool, header_text: str,
                 matched_pattern: str, matched_contexts: list, missing_fields: list,
                 description: str, suggestion: str) -> dict:
    return {
        "id": clause["id"],
        "name": clause["name"],
        "status": status,
        "found": status == "COMPLETE",
        "header_found": header_found,
        "header_text": header_text,
        "matched_pattern": matched_pattern,
        "matched_contexts": matched_contexts,
        "missing_fields": missing_fields,
        "description": description,
        "guide": clause.get("guide", ""),
        "suggestion": suggestion,
        "law_basis": clause["law_basis"],
        "law_detail": clause["law_detail"],
    }


def check_clauses(doc: ParsedDocument) -> list[dict]:
    all_text = " ".join(p.full_text() for p in doc.paragraphs if p.full_text())
    sections = _group_into_sections(doc.paragraphs)
    results = []

    for clause in MANDATORY_CLAUSES:
        trigger = clause.get("conditional_trigger")
        if trigger and not _check_trigger(doc.paragraphs, trigger):
            results.append(_make_result(
                clause, "NOT_APPLICABLE",
                header_found=False, header_text="",
                matched_pattern="", matched_contexts=[],
                missing_fields=[],
                description=clause["description"],
                suggestion="",
            ))
            continue

        header_patterns = clause.get("header_patterns", clause["patterns"])
        content_rules = clause.get("content_rules", {})

        match = _find_matching_section(sections, header_patterns)

        if match is not None:
            sec = match["section"]
            is_valid, missing_fields = _validate_content(sec["paragraphs"], content_rules, all_text)
            header_text = sec["header"].full_text().strip() if sec["header"] else ""

            if is_valid:
                status = "COMPLETE"
            else:
                status = "INCOMPLETE"

            if status == "COMPLETE":
                suggestion = clause.get("suggestion_complete", "")
            else:
                suggestion = clause.get("suggestion_incomplete", clause.get("guide", ""))

            results.append(_make_result(
                clause, status,
                header_found=True,
                header_text=header_text,
                matched_pattern=match["matched_pattern"],
                matched_contexts=[{
                    "paragraph_index": sec["header_index"],
                    "matched_text": match["matched_text"],
                    "context": header_text,
                }],
                missing_fields=missing_fields,
                description=clause.get("incomplete_desc", clause["description"]) if status == "INCOMPLETE" else clause["description"],
                suggestion=suggestion,
            ))
        else:
            global_match = _search_globally(doc.paragraphs, clause["patterns"])
            if global_match:
                # 헤더 섹션은 못 찾았지만 문서 어딘가에 패턴 존재(표 구조 등).
                # 내용성 검증(required_fields/patterns)이 있으면 문서 전체로 검증해 COMPLETE 승격 허용.
                has_content_rule = bool(content_rules.get("required_fields") or content_rules.get("required_patterns"))
                g_status = "INCOMPLETE"
                if has_content_rule:
                    content_missing = _run_checks(all_text, all_text, {
                        k: v for k, v in content_rules.items() if k != "min_length"
                    })
                    if not content_missing:
                        g_status = "COMPLETE"

                results.append(_make_result(
                    clause, g_status,
                    header_found=False, header_text="",
                    matched_pattern=global_match["matched_pattern"],
                    matched_contexts=[{
                        "paragraph_index": global_match["paragraph_index"],
                        "matched_text": global_match["matched_text"],
                        "context": global_match["context"],
                    }],
                    missing_fields=[],
                    description=clause["description"] if g_status == "COMPLETE" else clause.get("incomplete_desc", clause["description"]),
                    suggestion=clause.get("suggestion_complete", "") if g_status == "COMPLETE" else clause.get("suggestion_missing", clause.get("guide", "")),
                ))
            else:
                results.append(_make_result(
                    clause, "MISSING",
                    header_found=False, header_text="",
                    matched_pattern="", matched_contexts=[],
                    missing_fields=[],
                    description=clause["description"],
                    suggestion=clause.get("suggestion_missing", clause.get("guide", "")),
                ))

    return results
