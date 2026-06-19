"""공유 데이터 계약 (interface).

판단은 별도 API 호출 없이 **Claude Code가 직접** 수행한다(과금 없음). 따라서
이 모듈에는 LLM 호출용 구조가 없고, 결정적(deterministic) 파이프라인의 데이터 모델만 둔다.

흐름:
- parser.py   → ParsedDocument 생성(텍스트 추출/이미지·PDF 식별)
- knowledge.py→ ChecklistItem 목록 + 법령 컨텍스트 제공
- cli extract → ParsedDocument + 점검표 + 법령컨텍스트를 'review_packet.json'으로 출력
- (Claude Code가 직접 판단) → findings.json 작성
- cli report  → findings.json + 점검표 → 엑셀(ReviewResult 기반)
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

# ---- 입력(파서) ----------------------------------------------------------

FileType = Literal["txt", "docx", "html", "pdf_text", "pdf_image", "image"]


class ParsedDocument(BaseModel):
    """파서가 만든 점검 대상 문서.

    - 텍스트 추출형(txt/docx/html/pdf_text): `text`에 본문.
    - 비텍스트형(pdf_image/image): `text`=None. Claude Code가 파일을 직접 열람해 판단한다
      (별도 API/OCR 불필요). `media_blocks`는 과거 API 경로 잔재로 더는 사용하지 않는다.
    """

    source_path: str
    file_type: FileType
    text: Optional[str] = None
    media_blocks: list[dict] = Field(default_factory=list)  # (미사용, 호환용)
    parser_note: str = ""

    def is_text_based(self) -> bool:
        return self.file_type in ("txt", "docx", "html", "pdf_text")

    def needs_visual_read(self) -> bool:
        """Claude Code가 파일을 직접 열람해야 하는 문서인지(이미지/스캔 PDF)."""
        return not self.is_text_based() and not (self.text and self.text.strip())

    def is_empty(self) -> bool:
        """점검할 실질 내용이 없는 문서인지(빈 텍스트이며 시각 열람 대상도 아님)."""
        if self.is_text_based():
            return not (self.text and self.text.strip())
        # 비텍스트형은 파일 자체를 시각 열람하므로 '빈 문서'로 보지 않는다.
        return False


# ---- 점검 항목(지식베이스) ----------------------------------------------


class ChecklistItem(BaseModel):
    """동의서 점검 항목 1개와 그 판정 기준."""

    item_id: str          # 예: "retention"
    area: str = ""        # 점검 영역(엑셀 그룹). 예: "보유·이용 기간"
    item_name: str        # 세부 점검항목. 예: "보유·이용 기간 + 기간 적정성"
    law_basis: str        # 근거 법령. 예: "개인정보 보호법 제15조, 제21조"
    # 단순 존재 여부가 아니라 '무엇을 어떻게 판단해야 하는가'를 서술 — 판단의 기준.
    judgment_criteria: str
    # 조건부 항목(예: 민감정보/고유식별정보는 해당 수집 시에만) 여부.
    conditional: bool = False


# ---- 결과(판단) ---------------------------------------------------------

Verdict = Literal["적합", "보완필요", "누락", "해당없음"]
Confidence = Literal["높음", "중간", "낮음"]


class Finding(BaseModel):
    """점검 항목 1개에 대한 판단 결과 (엑셀 1행에 대응)."""

    item_id: str
    item_name: str = Field(default="", description="세부 점검항목명(비우면 점검표에서 보충)")
    verdict: Verdict
    found_content: str = Field(default="", description="근거(인용): 문서에서 발견한 실제 문구")
    legal_basis: str = Field(default="", description="근거 법령(비우면 점검표 값 사용)")
    issue: str = Field(default="", description="미흡 사유. 적합이면 빈 문자열")
    recommendation: str = Field(default="", description="개선 권고. 적합이면 빈 문자열")
    confidence: Confidence = Field(default="중간", description="판단 신뢰도")


class ReviewResult(BaseModel):
    """문서 1건에 대한 전체 점검 결과."""

    source_path: str
    findings: list[Finding]
    overall_summary: str = Field(default="", description="문서 전반 적합성 종합 의견")
