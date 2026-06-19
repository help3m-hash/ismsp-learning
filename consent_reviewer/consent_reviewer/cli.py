"""명령행 진입점 (별도 API 미사용 — 판단은 Claude Code가 직접 수행).

워크플로:
  1) extract : 동의서 파일을 파싱해 '리뷰 패킷'(본문 텍스트 + 점검표 + 법령 컨텍스트)을 JSON으로 출력.
               이미지/스캔 PDF는 Claude Code가 파일을 직접 열람하도록 플래그만 남긴다.
  2) (판단)  : Claude Code가 패킷/문서를 읽고 항목별로 판단하여 findings.json을 작성.
  3) report  : findings.json을 읽어 엑셀 점검표를 생성.

사용 예:
  python -m consent_reviewer extract samples/*.txt --out review_packet.json
  python -m consent_reviewer skeleton samples/*.txt --out findings.json   # (선택) 판단 채울 틀
  python -m consent_reviewer report findings.json --out 동의서_점검결과.xlsx
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

from . import config


def _collect_files(patterns: list[str], supported: set[str]) -> list[str]:
    """글롭 패턴/경로 목록을 실제 파일 경로로 펼친다(지원 확장자만, 중복 제거)."""
    files: list[str] = []
    seen: set[str] = set()
    for pat in patterns:
        matches = glob.glob(pat)
        if not matches and os.path.exists(pat):
            matches = [pat]
        for m in matches:
            if not os.path.isfile(m):
                continue
            if os.path.splitext(m)[1].lower() not in supported:
                print(f"  - 건너뜀(미지원 형식): {m}", file=sys.stderr)
                continue
            ap = os.path.abspath(m)
            if ap in seen:
                continue
            seen.add(ap)
            files.append(m)
    return files


def _cmd_extract(args) -> int:
    from .parser import SUPPORTED_EXTS, parse_document
    from .knowledge import build_legal_context, get_checklist

    files = _collect_files(args.paths, SUPPORTED_EXTS)
    if not files:
        print("점검할 파일이 없습니다. 경로/패턴과 지원 형식을 확인하세요.", file=sys.stderr)
        print(f"지원 형식: {', '.join(sorted(SUPPORTED_EXTS))}", file=sys.stderr)
        return 1

    documents = []
    for path in files:
        try:
            doc = parse_document(path)
        except Exception as e:  # noqa: BLE001
            documents.append({
                "source_path": path, "file_type": "unknown",
                "needs_visual_read": False, "empty": True, "text": None,
                "note": f"파싱 실패: {e}",
            })
            continue
        documents.append({
            "source_path": doc.source_path,
            "file_type": doc.file_type,
            "needs_visual_read": doc.needs_visual_read(),
            "empty": doc.is_empty(),
            "text": doc.text if doc.is_text_based() else None,
            "note": doc.parser_note,
        })

    checklist = [
        {
            "item_id": c.item_id, "area": c.area, "item_name": c.item_name,
            "law_basis": c.law_basis, "judgment_criteria": c.judgment_criteria,
            "conditional": c.conditional,
        }
        for c in get_checklist()
    ]
    packet = {
        "review_method": config.REVIEW_METHOD,
        "legal_context": build_legal_context(),
        "checklist": checklist,
        "documents": documents,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(packet, f, ensure_ascii=False, indent=2)

    print(f"리뷰 패킷 저장: {os.path.abspath(args.out)}  (문서 {len(documents)}건)")
    visual = [d["source_path"] for d in documents if d.get("needs_visual_read")]
    if visual:
        print("※ 다음 파일은 텍스트가 없어 Claude Code가 직접 열람해야 합니다:")
        for v in visual:
            print(f"   - {v}")
    print(
        "\n다음 단계: Claude Code가 패킷의 법령 컨텍스트/점검표에 따라 각 문서를 판단하고 "
        "findings.json을 작성한 뒤, `report` 명령으로 엑셀을 생성하세요."
    )
    return 0


def _cmd_skeleton(args) -> int:
    """판단을 채울 findings.json 틀을 생성(모든 항목 verdict 비움)."""
    from .parser import SUPPORTED_EXTS, parse_document  # noqa: F401
    from .knowledge import get_checklist

    files = _collect_files(args.paths, SUPPORTED_EXTS)
    if not files:
        print("대상 파일이 없습니다.", file=sys.stderr)
        return 1
    checklist = get_checklist()
    results = []
    for path in files:
        results.append({
            "source_path": path,
            "overall_summary": "",
            "findings": [
                {
                    "item_id": c.item_id, "item_name": c.item_name,
                    "verdict": "", "found_content": "", "legal_basis": c.law_basis,
                    "issue": "", "recommendation": "", "confidence": "높음",
                }
                for c in checklist
            ],
        })
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"results": results}, f, ensure_ascii=False, indent=2)
    print(f"findings 틀 저장: {os.path.abspath(args.out)}  (문서 {len(results)}건)")
    print("각 finding의 verdict/근거/사유/권고를 Claude Code가 채운 뒤 `report`를 실행하세요.")
    return 0


def _cmd_report(args) -> int:
    from .report import write_report
    from .models import ReviewResult

    try:
        with open(args.findings, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"findings 파일을 찾을 수 없습니다: {args.findings}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"findings JSON 파싱 오류: {e}", file=sys.stderr)
        return 1

    raw_results = data.get("results", data if isinstance(data, list) else [])
    if not raw_results:
        print("findings.json에 results가 없습니다.", file=sys.stderr)
        return 1
    try:
        results = [ReviewResult.model_validate(r) for r in raw_results]
    except Exception as e:  # noqa: BLE001
        print(f"findings 형식 오류: {e}", file=sys.stderr)
        return 1

    write_report(results, args.out)
    print(f"엑셀 점검표 저장: {os.path.abspath(args.out)}  (문서 {len(results)}건)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="consent_reviewer",
        description="개인정보 동의서 점검 도구 — 판단은 Claude Code가 직접 수행(무과금), Python은 파싱/엑셀만 담당.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_ex = sub.add_parser("extract", help="동의서를 파싱해 리뷰 패킷(JSON) 생성")
    p_ex.add_argument("paths", nargs="+", help="파일 경로 또는 글롭 패턴")
    p_ex.add_argument("--out", "-o", default=config.DEFAULT_PACKET)
    p_ex.set_defaults(func=_cmd_extract)

    p_sk = sub.add_parser("skeleton", help="판단을 채울 findings.json 틀 생성")
    p_sk.add_argument("paths", nargs="+", help="파일 경로 또는 글롭 패턴")
    p_sk.add_argument("--out", "-o", default=config.DEFAULT_FINDINGS)
    p_sk.set_defaults(func=_cmd_skeleton)

    p_rp = sub.add_parser("report", help="findings.json으로 엑셀 점검표 생성")
    p_rp.add_argument("findings", help="판단 결과 findings.json 경로")
    p_rp.add_argument("--out", "-o", default=config.DEFAULT_REPORT)
    p_rp.set_defaults(func=_cmd_report)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
