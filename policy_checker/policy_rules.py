# -*- coding: utf-8 -*-
"""
개인정보처리방침 점검 룰 (개인정보 보호법 제30조 기반)

각 룰 구조:
  id              : 항목 식별자
  name            : 표시 이름
  modes           : 점검 적용 모드 ("general", "finance"). 둘 다면 양쪽 리스트에 포함.
  conditional     : True면, 문서에 trigger_keywords가 있을 때만 '필수'로 판정.
                    (없으면 N/A 처리 - 예: 국외이전, CCTV)
  trigger_keywords: conditional=True일 때 해당 항목이 '적용 대상'인지 판단하는 키워드
  header_patterns : 항목 섹션(헤더)을 찾는 정규식
  content_patterns: 내용 충실성 검증 정규식 (하나라도 매칭되면 내용 있음)
  required_fields : 필수 하위 요소 [{label, patterns}] (모두 있어야 COMPLETE)
  law_basis       : 근거 법령
  description/guide/suggestion_*: 리포트 문구
"""

MANDATORY_ITEMS = [
    {
        "id": "purpose",
        "name": "개인정보의 처리 목적",
        "modes": ["general", "finance"],
        "conditional": False,
        "header_patterns": [
            r"처리\s*목적", r"수집.{0,5}이용.{0,5}목적", r"개인정보.{0,5}목적",
            r"이용\s*목적",
        ],
        "content_patterns": [
            r"(회원|서비스|민원|마케팅|광고|본인\s*확인|계약|이행|상담|배송|결제|금융거래)",
            r"목적.{0,20}(위하여|위해|이용|처리)",
        ],
        "required_fields": None,
        "law_basis": "「개인정보 보호법」 제30조①1",
        "law_detail": "개인정보처리자는 개인정보의 처리 목적을 개인정보처리방침에 포함하여 정해야 합니다.",
        "description": "'개인정보의 처리 목적'이 처리방침에 명시되지 않았습니다.",
        "incomplete_desc": "처리 목적 항목은 있으나 목적이 구체적으로 특정되지 않았습니다(추상적 표현).",
        "guide": "처리 목적을 업무별로 구체적으로 특정하세요. 예: '회원 가입·관리, 재화/서비스 제공, 민원처리, 마케팅 활용'",
    },
    {
        "id": "retention",
        "name": "처리 및 보유 기간",
        "modes": ["general", "finance"],
        "conditional": False,
        "header_patterns": [
            r"보유\s*기간", r"처리.{0,5}보유.{0,5}기간", r"보유.{0,5}이용\s*기간",
            r"보관\s*기간", r"파기",
        ],
        "content_patterns": [
            r"\d+\s*(년|개월|월|일|주)\s*(간|동안|까지|보관|보유|이용)?",
            r"(탈퇴|해지|종료|달성|거래\s*종료).{0,10}(까지|시)",
            r"(관계\s*법령|법령|상법|전자상거래|전자금융).{0,20}(보존|보관|기간)",
        ],
        "required_fields": None,
        "law_basis": "「개인정보 보호법」 제30조①2",
        "law_detail": "개인정보의 처리 및 보유 기간을 처리방침에 포함해야 하며, 목적 달성 시 지체 없이 파기해야 합니다(제21조).",
        "description": "'개인정보의 처리 및 보유 기간'이 처리방침에 명시되지 않았습니다.",
        "incomplete_desc": "보유 기간 항목은 있으나 구체적 기간 또는 법정 보존근거가 명시되지 않았습니다.",
        "guide": "목적별 구체적 보유기간과 법정 보존기간(근거 법령)을 명시하세요. 예: '회원 탈퇴 시까지, 단 전자상거래법에 따라 계약·결제 기록 5년 보관'",
    },
    {
        "id": "third_party",
        "name": "제3자 제공",
        "modes": ["general", "finance"],
        "conditional": False,
        "header_patterns": [
            r"제3자.{0,5}제공", r"제\s*3\s*자", r"제공.{0,5}관한\s*사항",
            r"개인정보.{0,5}제공",
        ],
        "content_patterns": [
            r"(제공받는\s*자|제공\s*받는|제공처)",
            r"제공.{0,5}(하지\s*않|없습니다)",  # "제3자 제공하지 않음"도 적법 명시
        ],
        "required_fields": [
            {"label": "제공받는 자", "patterns": [r"제공받는\s*자", r"제공\s*받는", r"제공처", r"제공하지\s*않"]},
            {"label": "제공 목적", "patterns": [r"제공.{0,5}목적", r"이용\s*목적", r"제공하지\s*않"]},
            {"label": "제공 항목", "patterns": [r"제공.{0,10}항목", r"제공.{0,10}정보", r"제공하지\s*않"]},
            {"label": "보유 기간", "patterns": [r"보유.{0,5}기간", r"보유.{0,5}이용", r"제공하지\s*않"]},
        ],
        "law_basis": "「개인정보 보호법」 제30조①3, 제17조",
        "law_detail": "제3자 제공 시 제공받는 자, 제공 목적, 제공 항목, 보유·이용 기간을 명시해야 합니다. 제공이 없으면 그 사실을 명시하는 것이 바람직합니다.",
        "description": "'개인정보 제3자 제공'에 관한 사항이 처리방침에 명시되지 않았습니다.",
        "incomplete_desc": "제3자 제공 항목은 있으나 필수 정보(제공받는 자/목적/항목/기간)가 일부 누락되었습니다.",
        "guide": "제공받는 자, 제공 목적, 제공 항목, 보유기간을 표로 명시하세요. 제공하지 않으면 '제3자에게 제공하지 않습니다'라고 기재하세요.",
    },
    {
        "id": "consignment",
        "name": "처리위탁",
        "modes": ["general", "finance"],
        "conditional": False,
        "header_patterns": [
            r"처리\s*위탁", r"위탁.{0,5}관한\s*사항", r"수탁", r"업무.{0,5}위탁",
        ],
        "content_patterns": [
            r"(수탁자|수탁업체|위탁받는\s*자|위탁업무)",
            r"위탁.{0,5}(하지\s*않|없습니다)",
        ],
        "required_fields": [
            {"label": "수탁자", "patterns": [r"수탁자", r"수탁업체", r"위탁받는\s*자", r"위탁하지\s*않"]},
            {"label": "위탁업무 내용", "patterns": [r"위탁업무", r"위탁.{0,10}내용", r"업무.{0,5}내용", r"위탁하지\s*않"]},
        ],
        "law_basis": "「개인정보 보호법」 제30조①3의2, 제26조",
        "law_detail": "처리위탁 시 수탁자와 위탁업무 내용을 처리방침에 공개해야 합니다.",
        "description": "'개인정보 처리위탁'에 관한 사항이 처리방침에 명시되지 않았습니다.",
        "incomplete_desc": "처리위탁 항목은 있으나 수탁자 또는 위탁업무 내용이 누락되었습니다.",
        "guide": "수탁자와 위탁업무 내용을 명시하세요. 위탁이 없으면 그 사실을 기재하세요.",
    },
    {
        "id": "rights",
        "name": "정보주체의 권리·의무 및 행사방법",
        "modes": ["general", "finance"],
        "conditional": False,
        "header_patterns": [
            r"정보주체.{0,10}권리", r"권리.{0,5}의무", r"권리.{0,5}행사",
            r"열람.{0,5}정정", r"이용자.{0,5}권리",
        ],
        "content_patterns": [
            r"(열람|정정|삭제|처리정지)",
            r"(요구|행사|신청).{0,10}(가능|할\s*수|하실\s*수)",
        ],
        "required_fields": [
            {"label": "권리 종류", "patterns": [r"열람", r"정정", r"삭제", r"처리정지"]},
            {"label": "행사 방법", "patterns": [r"행사\s*방법", r"방법.{0,10}(서면|전화|이메일|홈페이지)", r"신청.{0,10}(서면|전화|이메일|방문)", r"요구.{0,10}(서면|전화|이메일)"]},
        ],
        "law_basis": "「개인정보 보호법」 제30조①5, 제35조~제37조",
        "law_detail": "정보주체의 열람·정정·삭제·처리정지 요구권과 그 행사방법을 안내해야 합니다.",
        "description": "'정보주체의 권리·의무 및 행사방법'이 처리방침에 명시되지 않았습니다.",
        "incomplete_desc": "정보주체 권리 항목은 있으나 권리 종류 또는 구체적 행사방법이 누락되었습니다.",
        "guide": "열람·정정·삭제·처리정지 요구권과 행사방법(접수 창구·절차)을 명시하세요.",
    },
    {
        "id": "cpo",
        "name": "개인정보 보호책임자",
        "modes": ["general", "finance"],
        "conditional": False,
        "header_patterns": [
            r"개인정보\s*보호책임자", r"보호책임자", r"CPO", r"개인정보.{0,5}책임자",
        ],
        "content_patterns": [
            r"(성명|이름|직책|부서)",
            r"(연락처|전화|이메일|e-?mail|☎|☏|\d{2,4}-\d{3,4}-\d{4})",
        ],
        "required_fields": [
            {"label": "책임자 식별(성명/직책/부서)", "patterns": [r"성명", r"이름", r"직책", r"부서", r"담당자"]},
            {"label": "연락처", "patterns": [r"연락처", r"전화", r"이메일", r"e-?mail", r"\d{2,4}-\d{3,4}-\d{4}", r"@"]},
        ],
        "law_basis": "「개인정보 보호법」 제30조①6, 제31조",
        "law_detail": "개인정보 보호책임자의 성명 또는 직책·부서 및 연락처를 명시해야 합니다.",
        "description": "'개인정보 보호책임자'에 관한 사항이 처리방침에 명시되지 않았습니다.",
        "incomplete_desc": "보호책임자 항목은 있으나 식별정보(성명/직책/부서) 또는 연락처가 누락되었습니다.",
        "guide": "보호책임자의 성명 또는 직책·부서와 연락처(전화·이메일)를 명시하세요.",
    },
    {
        "id": "items",
        "name": "처리하는 개인정보 항목",
        "modes": ["general", "finance"],
        "conditional": False,
        "header_patterns": [
            r"처리.{0,5}개인정보.{0,5}항목", r"수집.{0,5}항목", r"개인정보.{0,5}항목",
            r"수집.{0,5}개인정보",
        ],
        "content_patterns": [
            r"(성명|이름)",
            r"(연락처|전화|휴대폰|이메일|e-?mail|주소|생년월일|아이디|비밀번호)",
            r"([가-힣A-Za-z]+\s*,\s*){2,}",
        ],
        "required_fields": None,
        "law_basis": "「개인정보 보호법」 제30조①, 제16조",
        "law_detail": "처리하는 개인정보의 항목을 구체적으로 명시해야 합니다.",
        "description": "'처리하는 개인정보 항목'이 처리방침에 명시되지 않았습니다.",
        "incomplete_desc": "개인정보 항목은 있으나 구체적 항목 나열이 부족합니다.",
        "guide": "수집·처리하는 개인정보 항목을 구체적으로 나열하세요. 예: '성명, 연락처, 이메일, 주소'",
    },
    {
        "id": "cookies",
        "name": "자동수집장치(쿠키 등) 설치·운영 및 거부",
        "modes": ["general", "finance"],
        "conditional": False,
        "header_patterns": [
            r"쿠키", r"자동\s*수집", r"자동수집장치", r"cookie", r"행태정보",
        ],
        "content_patterns": [
            r"(거부|차단|설정|관리).{0,15}(가능|할\s*수|방법|브라우저)",
            r"쿠키.{0,20}(저장|사용|거부|설치)",
        ],
        "required_fields": None,
        "law_basis": "「개인정보 보호법」 제30조①, 제22조의2 관련",
        "law_detail": "쿠키 등 자동수집장치의 설치·운영 및 그 거부에 관한 사항을 안내해야 합니다.",
        "description": "'자동수집장치(쿠키 등)의 설치·운영 및 거부'에 관한 사항이 없습니다.",
        "incomplete_desc": "쿠키 항목은 있으나 거부 방법 안내가 부족합니다.",
        "guide": "쿠키의 사용 목적과 브라우저를 통한 거부·차단 방법을 안내하세요.",
    },
    {
        "id": "safety",
        "name": "안전성 확보조치",
        "modes": ["general", "finance"],
        "conditional": False,
        "header_patterns": [
            r"안전성\s*확보", r"안전\s*조치", r"안전성\s*확보조치", r"기술적.{0,5}관리적",
        ],
        "content_patterns": [
            r"(암호화|접근통제|접근\s*권한|접속기록|백신|방화벽|교육|물리적)",
        ],
        "required_fields": None,
        "law_basis": "「개인정보 보호법」 제30조①, 제29조",
        "law_detail": "개인정보의 안전성 확보를 위한 기술적·관리적·물리적 조치를 기재해야 합니다.",
        "description": "'안전성 확보조치'에 관한 사항이 처리방침에 명시되지 않았습니다.",
        "incomplete_desc": "안전성 확보조치 항목은 있으나 구체적 조치(암호화/접근통제 등)가 부족합니다.",
        "guide": "기술적(암호화·접근통제·접속기록), 관리적(내부관리계획·교육), 물리적 조치를 기재하세요.",
    },
    {
        "id": "remedy",
        "name": "권익침해 구제방법",
        "modes": ["general", "finance"],
        "conditional": False,
        "header_patterns": [
            r"권익침해", r"구제\s*방법", r"분쟁조정", r"침해\s*신고",
        ],
        "content_patterns": [
            r"(개인정보\s*분쟁조정위원회|분쟁조정|개인정보침해신고센터|KISA|118|1336|대검찰청|경찰청|개인정보보호위원회)",
        ],
        "required_fields": None,
        "law_basis": "「개인정보 보호법」 제30조①, 표준 처리방침 지침",
        "law_detail": "정보주체의 권익침해 구제를 위한 분쟁조정위원회·신고센터 등 기관 안내를 권장합니다.",
        "description": "'권익침해 구제방법(분쟁조정위원회 등)' 안내가 처리방침에 없습니다.",
        "incomplete_desc": "권익침해 구제 항목은 있으나 구체적 기관 안내가 부족합니다.",
        "guide": "개인정보분쟁조정위원회, 개인정보침해신고센터(KISA), 대검찰청, 경찰청 등 구제기관과 연락처를 안내하세요.",
    },
    {
        "id": "change",
        "name": "처리방침의 변경(시행일·이전 버전)",
        "modes": ["general", "finance"],
        "conditional": False,
        "header_patterns": [
            r"처리방침.{0,5}변경", r"방침.{0,5}변경", r"시행", r"개정",
        ],
        "content_patterns": [
            r"(시행|적용)\s*(일|일자)", r"\d{4}\s*[\.\-년]\s*\d{1,2}", r"변경.{0,15}(공지|안내|고지)",
        ],
        "required_fields": None,
        "law_basis": "「개인정보 보호법」 제30조②",
        "law_detail": "처리방침을 수립·변경 시 공개하고, 변경사항과 시행일을 안내해야 합니다.",
        "description": "'처리방침의 시행일 또는 변경 안내'가 명시되지 않았습니다.",
        "incomplete_desc": "변경/시행 항목은 있으나 시행일자 또는 변경 공지 방법이 부족합니다.",
        "guide": "처리방침의 시행일자를 명시하고, 변경 시 공지 방법과 이전 버전 확인 방법을 안내하세요.",
    },

    # ---------------- 조건부(해당 시 필수) 항목 ----------------
    {
        "id": "overseas",
        "name": "개인정보 국외이전",
        "modes": ["general", "finance"],
        "conditional": True,
        "trigger_keywords": ["국외", "해외", "국외이전", "국외 제3자", "재보험사", "해외 서버", "국외에 있는"],
        "header_patterns": [
            r"국외\s*이전", r"국외.{0,5}제공", r"해외\s*이전", r"국외.{0,5}처리",
        ],
        "content_patterns": [
            r"(이전받는\s*자|이전\s*국가|이전\s*항목|이전\s*시점|이전\s*방법)",
        ],
        "required_fields": [
            {"label": "이전받는 자", "patterns": [r"이전받는\s*자", r"이전\s*받는", r"제공받는\s*자"]},
            {"label": "이전 국가", "patterns": [r"이전\s*(되는\s*)?국가", r"소재\s*국가", r"국가"]},
            {"label": "이전 항목", "patterns": [r"이전.{0,10}항목", r"이전.{0,10}정보"]},
            {"label": "이용목적·보유기간", "patterns": [r"이용\s*목적", r"보유.{0,5}기간"]},
        ],
        "law_basis": "「개인정보 보호법」 제28조의8",
        "law_detail": "국외이전 시 이전받는 자, 이전 국가, 이전 항목·시점·방법, 이용목적·보유기간을 고지하고 동의받아야 합니다.",
        "description": "국외이전이 있으나 '국외이전 고지사항'이 처리방침에 명시되지 않았습니다.",
        "incomplete_desc": "국외이전 항목은 있으나 필수 고지사항(이전받는 자/국가/항목/목적·기간)이 일부 누락되었습니다.",
        "guide": "이전받는 자, 이전 국가, 이전 항목·시점·방법, 이용목적·보유기간을 명시하세요.",
    },
    {
        "id": "pseudonym",
        "name": "가명정보 처리",
        "modes": ["general", "finance"],
        "conditional": True,
        "trigger_keywords": ["가명정보", "가명처리", "가명", "통계작성", "과학적 연구"],
        "header_patterns": [
            r"가명정보", r"가명\s*처리",
        ],
        "content_patterns": [
            r"가명.{0,15}(목적|항목|기간|처리|통계|연구)",
        ],
        "required_fields": None,
        "law_basis": "「개인정보 보호법」 제28조의2 이하",
        "law_detail": "가명정보를 처리하는 경우 처리 목적, 처리 항목, 보유기간 등을 처리방침에 포함해야 합니다.",
        "description": "가명정보 처리가 있으나 관련 사항이 처리방침에 명시되지 않았습니다.",
        "incomplete_desc": "가명정보 항목은 있으나 처리 목적·항목·기간 등이 부족합니다.",
        "guide": "가명정보의 처리 목적, 처리 항목, 보유기간을 명시하세요.",
    },
    {
        "id": "cctv",
        "name": "영상정보처리기기(CCTV) 운영·관리",
        "modes": ["general", "finance"],
        "conditional": True,
        "trigger_keywords": ["영상정보처리기기", "CCTV", "씨씨티비", "영상정보", "고정형 영상", "이동형 영상"],
        "header_patterns": [
            r"영상정보처리기기", r"CCTV", r"영상정보.{0,5}(운영|관리)",
        ],
        "content_patterns": [
            r"(설치\s*목적|설치\s*대수|촬영\s*범위|보관\s*기간|관리책임자)",
        ],
        "required_fields": None,
        "law_basis": "「개인정보 보호법」 제25조, 제25조의2",
        "law_detail": "영상정보처리기기 운영 시 설치 목적·장소·촬영범위·관리책임자·보관기간 등을 안내해야 합니다.",
        "description": "영상정보처리기기 운영이 있으나 관련 운영·관리 사항이 명시되지 않았습니다.",
        "incomplete_desc": "CCTV 항목은 있으나 설치목적·촬영범위·보관기간 등이 부족합니다.",
        "guide": "설치 목적·장소·촬영범위·관리책임자·보관기간·열람 방법을 명시하세요.",
    },
    {
        "id": "auto_decision",
        "name": "자동화된 결정(프로파일링)에 관한 사항",
        "modes": ["general", "finance"],
        "conditional": True,
        "trigger_keywords": ["자동화된 결정", "프로파일링", "자동화 결정", "완전히 자동화", "알고리즘", "자동화된 시스템"],
        "header_patterns": [
            r"자동화된?\s*결정", r"프로파일링", r"자동화\s*시스템",
        ],
        "content_patterns": [
            r"자동화.{0,20}(결정|거부|설명|기준|불이익|이의)",
        ],
        "required_fields": None,
        "law_basis": "「개인정보 보호법」 제4조, 제37조의2",
        "law_detail": "완전히 자동화된 결정이 정보주체의 권리·의무에 중대한 영향을 미치는 경우 그 기준·절차 및 거부·설명요구권을 안내해야 합니다.",
        "description": "자동화된 결정이 있으나 관련 사항(거부권·설명요구권 등)이 명시되지 않았습니다.",
        "incomplete_desc": "자동화 결정 항목은 있으나 기준·거부권·설명요구권 안내가 부족합니다.",
        "guide": "자동화된 결정의 기준·절차와 정보주체의 거부·설명 요구권을 안내하세요.",
    },

    # ---------------- 금융기관 전용 항목 ----------------
    {
        "id": "credit_info",
        "name": "신용정보 처리(신용정보법)",
        "modes": ["finance"],
        "conditional": True,
        "trigger_keywords": ["신용정보", "개인신용정보", "신용정보법", "신용정보의 이용 및 보호", "신용평가", "신용조회"],
        "header_patterns": [
            r"신용정보", r"개인신용정보", r"신용정보.{0,5}(처리|관리|보호)",
        ],
        "content_patterns": [
            r"신용정보.{0,30}(이용|보호|관리|법|제공|조회|처리)",
            r"(신용정보의\s*이용\s*및\s*보호|신용정보법)",
        ],
        "required_fields": None,
        "law_basis": "「신용정보의 이용 및 보호에 관한 법률」",
        "law_detail": "금융기관은 개인신용정보의 처리·보호에 관한 사항을 신용정보법에 따라 별도로 관리·안내해야 합니다.",
        "description": "신용정보를 처리하나 신용정보법 관련 처리·보호 사항이 명시되지 않았습니다.",
        "incomplete_desc": "신용정보 항목은 있으나 신용정보법 근거 처리·보호 사항이 부족합니다.",
        "guide": "개인신용정보의 처리·관리·보호에 관한 사항을 신용정보법 근거와 함께 명시하세요.",
    },
]


def items_for_mode(mode: str):
    """모드에 해당하는 룰만 반환."""
    return [it for it in MANDATORY_ITEMS if mode in it["modes"]]
