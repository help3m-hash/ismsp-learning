import 'package:flutter/material.dart';

class AppTheme {
  static const seed = Color(0xFF1E5BCB); // ISMS-P 블루 계열

  static ThemeData light() {
    final scheme = ColorScheme.fromSeed(seedColor: seed);
    return ThemeData(
      colorScheme: scheme,
      useMaterial3: true,
      scaffoldBackgroundColor: const Color(0xFFF6F7FB),
      appBarTheme: const AppBarTheme(centerTitle: false, scrolledUnderElevation: 0),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size.fromHeight(52),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
        ),
      ),
    );
  }

  /// 영역 코드(1/2/3)별 악센트 색.
  static Color domainColor(String id) {
    switch (id.split('.').first) {
      case '1':
        return const Color(0xFF1E5BCB);
      case '2':
        return const Color(0xFF13A07A);
      case '3':
        return const Color(0xFF9A4DCE);
      default:
        return seed;
    }
  }
}
