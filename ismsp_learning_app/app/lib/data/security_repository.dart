import 'dart:convert';
import 'package:flutter/services.dart' show rootBundle;
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/security_issue.dart';

/// 보안 이슈 피드 로더.
/// 우선순위: 원격 URL → 실패 시 로컬 캐시 → 그래도 없으면 동봉 샘플.
class SecurityRepository {
  /// GitHub raw URL 등으로 교체. 저장소 만들기 전엔 동봉 샘플로 폴백된다.
  /// 예: https://raw.githubusercontent.com/<user>/<repo>/main/security_feed/security_issues.json
  static const String feedUrl = String.fromEnvironment(
    'SECURITY_FEED_URL',
    defaultValue: '',
  );

  static const _cacheKey = 'security_feed_cache_v1';
  static const _asset = 'assets/feed/security_issues.json';

  /// 결과: (피드, 출처라벨). 출처라벨 = "온라인" | "캐시" | "샘플".
  Future<(SecurityFeed, String)> load({bool forceRefresh = false}) async {
    final prefs = await SharedPreferences.getInstance();

    if (feedUrl.isNotEmpty) {
      try {
        final res = await http
            .get(Uri.parse(feedUrl))
            .timeout(const Duration(seconds: 10));
        if (res.statusCode == 200) {
          final body = utf8.decode(res.bodyBytes);
          final feed = SecurityFeed.fromJson(jsonDecode(body) as Map<String, dynamic>);
          await prefs.setString(_cacheKey, body);
          return (feed, '온라인');
        }
      } catch (_) {
        // 네트워크 실패 → 아래 폴백
      }
    }

    final cached = prefs.getString(_cacheKey);
    if (cached != null) {
      try {
        return (SecurityFeed.fromJson(jsonDecode(cached) as Map<String, dynamic>), '캐시');
      } catch (_) {}
    }

    final asset = await rootBundle.loadString(_asset);
    return (SecurityFeed.fromJson(jsonDecode(asset) as Map<String, dynamic>), '샘플');
  }
}
