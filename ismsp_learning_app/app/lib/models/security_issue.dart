/// 보안 이슈 1건(원격 security_issues.json의 issues 항목).
class SecurityIssue {
  final String id;
  final String title;
  final String summary;
  final String source;
  final String url;
  final String published;
  final String severity; // 긴급/높음/중간/낮음/정보
  final List<String> keywords;

  SecurityIssue({
    required this.id,
    required this.title,
    required this.summary,
    required this.source,
    required this.url,
    required this.published,
    required this.severity,
    required this.keywords,
  });

  factory SecurityIssue.fromJson(Map<String, dynamic> j) => SecurityIssue(
        id: j['id']?.toString() ?? '',
        title: j['title']?.toString() ?? '',
        summary: j['summary']?.toString() ?? '',
        source: j['source']?.toString() ?? '',
        url: j['url']?.toString() ?? '',
        published: j['published']?.toString() ?? '',
        severity: j['severity']?.toString() ?? '정보',
        keywords: (j['keywords'] as List?)?.map((e) => e.toString()).toList() ?? const [],
      );
}

/// 피드 전체(갱신시각 + 이슈 목록).
class SecurityFeed {
  final String updatedAt;
  final List<SecurityIssue> issues;

  SecurityFeed({required this.updatedAt, required this.issues});

  factory SecurityFeed.fromJson(Map<String, dynamic> j) => SecurityFeed(
        updatedAt: j['updated_at']?.toString() ?? '',
        issues: (j['issues'] as List? ?? const [])
            .map((e) => SecurityIssue.fromJson(e as Map<String, dynamic>))
            .toList(),
      );

  /// 이슈들에 등장하는 모든 키워드(필터 칩용).
  List<String> get allKeywords {
    final s = <String>{};
    for (final i in issues) {
      s.addAll(i.keywords);
    }
    final list = s.toList()..sort();
    return list;
  }
}
