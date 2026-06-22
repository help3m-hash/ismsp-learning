# ISMS-P 학습 앱 (Flutter)

ISMS-P 인증기준을 학습하는 **완전 오프라인** 안드로이드 앱(갤럭시 폴드 6 타깃).
통제항목 1개(학습 카드) + 퀴즈로 구성된 15~30분 마이크로러닝 세션.

## 화면 흐름
홈 → 학습 카드(인증기준·확인사항·세부설명·결함사례·증거자료·관련법규) → 퀴즈(OX/MCQ, 즉시 피드백+원문 근거) → 결과(점수·복습 안내) → 진도

- **폴더블 대응**: 화면 폭 ≥ 720dp(폴드 펼친 메인 화면)이면 2단 레이아웃, 좁으면(커버 화면) 1단.
- **오프라인 진도**: `shared_preferences` 기반 Leitner SRS(box 0~4). 서버 없음.
- **용어집 툴팁**: CISO/CPO/DoA 등 약어는 본문에서 점선 밑줄 + 탭 시 정의 표시.
- **콘텐츠**: `assets/content/items/*.json` (외부 QA 검수 완료한 16개), `glossary.json`.

## 실행 방법 (Flutter SDK 필요)
이 저장소에는 `lib/`, `pubspec.yaml`, `assets/`만 손으로 작성되어 있고
플랫폼 폴더(android/ 등)는 없습니다. 아래 순서로 생성·실행하세요.

```bash
cd ismsp_learning_app/app

# 1) 안드로이드 플랫폼 폴더 생성 (lib/ pubspec.yaml은 보존됨)
flutter create . --platforms=android --project-name ismsp_learning

# 2) 의존성 설치
flutter pub get

# 3) 갤럭시 폴드 6(또는 에뮬레이터) 연결 후 실행
flutter devices
flutter run
```

> `flutter create .` 는 기존 `lib/main.dart` 를 덮어쓰지 않습니다(이미 존재하면 건너뜀).
> 콘텐츠를 추가/수정하면 루트의 `tools/qa_check.py` 회귀검사를 다시 돌리고,
> `app/assets/content/` 로 복사한 뒤 재빌드하세요.

## 구조
```
lib/
  main.dart                  앱 진입 + 전역 상태(AppState) 주입
  models/                    ControlItem, QuizQuestion
  data/                      ContentRepository(에셋 로드), ProgressStore(SRS)
  services/session_engine    다음 학습 항목 선정(미학습>저숙련>오래전)
  ui/                        home / study_card / quiz / result / progress
  ui/widgets/                glossary_text(툴팁), section_block
  theme/app_theme            M3 테마 + 영역별 악센트 색
```

## 알려진 한정사항
- 이 환경에는 Flutter SDK가 없어 **컴파일/실기기 검증은 아직 수행되지 않음**(코드 작성·정적 점검까지 완료). 설치 후 위 절차로 첫 빌드 시 검증 필요.
- 현재 파일럿 콘텐츠는 영역 1(16개 항목)만 포함.
