#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개인정보 동의서 점검 도구 (CLI)

사용법:
    python run.py <동의서.pdf> [--out 결과.txt]

필요 패키지: pdfplumber
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from doc_parser import load_pdf
from clause_checker import check_clauses
from format_checker import check_format

STATUS_LABEL = {
    "COMPLETE": "[발견]", "INCOMPLETE": "[내용미비]",
    "MISSING": "[누락]", "NOT_APPLICABLE": "[해당없음]",
}


def build_report(clause_results, format_results, filename):
    lines = []
    lines.append("=" * 60)
    lines.append("개인정보동의서 점검 결과")
    lines.append(f"파일: {filename}")
    lines.append("=" * 60)
    lines.append("")
    lines.append("1. 필수 조항 점검")
    lines.append("-" * 60)

    cnt = {"COMPLETE": 0, "INCOMPLETE": 0, "MISSING": 0, "NOT_APPLICABLE": 0}
    for r in clause_results:
        cnt[r["status"]] = cnt.get(r["status"], 0) + 1
        tag = STATUS_LABEL.get(r["status"], r["status"])
        lines.append(f"{tag} {r['name']}")
        if r["status"] == "COMPLETE" and r.get("header_text"):
            lines.append(f"    - 헤더: {r['header_text']}")
        if r["status"] in ("INCOMPLETE", "MISSING"):
            lines.append(f"    - {r.get('description','')}")
            for m in r.get("missing_fields", []):
                lines.append(f"      · {m}")
            if r.get("suggestion"):
                lines.append(f"    - 개선: {r['suggestion']}")
        lines.append(f"    [근거] {r['law_basis']} {r['law_detail']}")
        lines.append("")

    found = cnt["COMPLETE"]
    inc = cnt["INCOMPLETE"]
    miss = cnt["MISSING"]
    lines.append("-" * 60)
    lines.append(f"→ 필수 {found+inc+miss}개 중 발견 {found}, 내용미비 {inc}, 누락 {miss}")
    lines.append("")

    lines.append("2. 서식 점검")
    lines.append("-" * 60)
    for fr in format_results:
        mark = "통과" if fr["passed"] else "확인필요"
        lines.append(f"[{mark}] {fr['name']}: {fr['detail']}")
        for item in fr.get("failed_items", [])[:5]:
            sug = item.get("suggestion") or item.get("text", "")
            lines.append(f"    · {sug}")
    lines.append("")
    lines.append("※ 본 점검은 자동화 도구의 1차 스크리닝이며, 최종 판단은 전문가 검토가 필요합니다.")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="개인정보 동의서 점검")
    ap.add_argument("pdf", help="점검할 동의서 PDF 경로")
    ap.add_argument("--out", default=None, help="결과 저장 경로(.txt)")
    args = ap.parse_args()

    doc = load_pdf(args.pdf)
    clause_results = check_clauses(doc)
    format_results = check_format(doc)
    report = build_report(clause_results, format_results, args.pdf)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"결과 저장: {args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
