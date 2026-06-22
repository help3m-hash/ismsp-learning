import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ismsp_learning/main.dart';

void main() {
  testWidgets('앱이 빌드되고 부트스트랩 후 홈 화면이 표시된다', (WidgetTester tester) async {
    SharedPreferences.setMockInitialValues(<String, Object>{});

    await tester.pumpWidget(const IsmspApp());
    // 빌드 직후: MaterialApp 구성 확인(로딩 단계)
    expect(find.byType(MaterialApp), findsOneWidget);

    // 에셋(콘텐츠 16개) 비동기 로드가 끝날 때까지 펌프
    for (var i = 0; i < 12; i++) {
      await tester.pump(const Duration(milliseconds: 100));
    }

    // 홈 화면 핵심 요소가 렌더되는지 확인
    expect(find.text('오늘의 학습'), findsOneWidget);
    expect(find.text('학습 시작'), findsOneWidget);
  });
}
