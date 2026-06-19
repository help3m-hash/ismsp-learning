"""설정 상수.

판단은 Claude Code가 직접 수행하므로 API 키/모델 설정이 필요 없다.
여기에는 리포트 표시에 쓰는 상수만 둔다.
"""

from __future__ import annotations

# 리포트 제목 및 판단 방식 표기.
REPORT_TITLE = "개인정보 동의서 점검 결과"
REVIEW_METHOD = "Claude 직접 판단 (별도 API 미사용)"

# review_packet / findings 기본 파일명.
DEFAULT_PACKET = "review_packet.json"
DEFAULT_FINDINGS = "findings.json"
DEFAULT_REPORT = "동의서_점검결과.xlsx"
