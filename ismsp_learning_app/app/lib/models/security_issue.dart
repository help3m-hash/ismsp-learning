/// 보안 이슈 1건(원격 security_issues.json의 issues 항목).
class SecurityIssue {
  final String id;
  final String title;
  final String summary;
  final String source;
  final String region; // 국내/해외
  final String tier; // 1차/통신/종합/보안
  final String domain; // 정치·국제 / 사회·경제 / 스포츠·문화 / IT·과학·보안
  final String url;
  final String published;
  final List<String> keywords;

  SecurityIssue({
    required this.id,
    required this.title,
    required this.summary,
    required this.source,
    required this.region,
    required this.tier,
    required this.domain,
    required this.url,
    required this.published,
    required this.keywords,
  });

  /// published(ISO8601)에서 날짜(YYYY-MM-DD)만.
  String get publishedDate =>
      published.isEmpty ? '' : published.split('T').first;

  factory SecurityIssue.fromJson(Map<String, dynamic> j) => SecurityIssue(
        id: j['id']?.toString() ?? '',
        title: j['title']?.toString() ?? '',
        summary: j['summary']?.toString() ?? '',
        source: j['source']?.toString() ?? '',
        region: j['region']?.toString() ?? '',
        tier: j['tier']?.toString() ?? '',
        domain: j['domain']?.toString() ?? '기타',
        url: j['url']?.toString() ?? '',
        published: j['published']?.toString() ?? '',
        keywords: (j['keywords'] as List?)?.map((e) => e.toString()).toList() ?? const [],
      );
}

/// 피드 전체(갱신시각 + 이슈 목록).
class SecurityFeed {
  final String updatedAt;
  final List<String> domains; // 피드가 제공하는 분야 목록
  final List<SecurityIssue> issues;

  SecurityFeed({required this.updatedAt, required this.domains, required this.issues});

  factory SecurityFeed.fromJson(Map<String, dynamic> j) => SecurityFeed(
        updatedAt: j['updated_at']?.toString() ?? '',
        domains: (j['domains'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        issues: (j['issues'] as List? ?? const [])
            .map((e) => SecurityIssue.fromJson(e as Map<String, dynamic>))
            .toList(),
      );

  /// 분야 필터용. 최상위 domains가 있으면 그것을, 없으면 이슈에서 유도.
  List<String> get filterDomains {
    if (domains.isNotEmpty) return domains;
    final s = <String>{};
    for (final i in issues) {
      if (i.domain.isNotEmpty) s.add(i.domain);
    }
    return s.toList()..sort();
  }

  /// 피드에 실제 등장하는 지역(국내/해외).
  List<String> get regions {
    final s = <String>{};
    for (final i in issues) {
      if (i.region.isNotEmpty) s.add(i.region);
    }
    return s.toList()..sort();
  }
}
