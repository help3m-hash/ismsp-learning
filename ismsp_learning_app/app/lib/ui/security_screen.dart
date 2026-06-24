import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../data/security_repository.dart';
import '../models/security_issue.dart';

/// "오늘의 이슈" — 전 분야 뉴스 피드 화면.
class SecurityScreen extends StatefulWidget {
  const SecurityScreen({super.key});

  @override
  State<SecurityScreen> createState() => _SecurityScreenState();
}

class _SecurityScreenState extends State<SecurityScreen> {
  final _repo = SecurityRepository();
  SecurityFeed? _feed;
  String _sourceLabel = '';
  bool _loading = true;
  String? _selectedDomain; // null = 전체
  String? _selectedRegion; // null = 전체

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load({bool refresh = false}) async {
    setState(() => _loading = true);
    final (feed, label) = await _repo.load(forceRefresh: refresh);
    if (!mounted) return;
    setState(() {
      _feed = feed;
      _sourceLabel = label;
      _loading = false;
    });
  }

  Future<void> _open(String url) async {
    final uri = Uri.tryParse(url);
    if (uri == null) return;
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('링크를 열 수 없습니다.')),
        );
      }
    }
  }

  List<SecurityIssue> _filtered(SecurityFeed feed) {
    return feed.issues.where((i) {
      final okDom = _selectedDomain == null || i.domain == _selectedDomain;
      final okReg = _selectedRegion == null || i.region == _selectedRegion;
      return okDom && okReg;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final feed = _feed;
    final issues = feed == null ? <SecurityIssue>[] : _filtered(feed);

    return Scaffold(
      appBar: AppBar(
        title: const Text('오늘의 이슈'),
        actions: [
          IconButton(
            tooltip: '새로고침',
            icon: const Icon(Icons.refresh),
            onPressed: _loading ? null : () => _load(refresh: true),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : feed == null
              ? const Center(child: Text('피드를 불러오지 못했습니다.'))
              : Column(
                  children: [
                    _header(feed),
                    _domainChips(feed),
                    if (feed.regions.length > 1) _regionChips(feed),
                    Expanded(
                      child: RefreshIndicator(
                        onRefresh: () => _load(refresh: true),
                        child: issues.isEmpty
                            ? ListView(children: const [
                                SizedBox(height: 80),
                                Center(child: Text('해당 조건의 이슈가 없습니다.')),
                              ])
                            : ListView.builder(
                                padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                                itemCount: issues.length,
                                itemBuilder: (_, i) =>
                                    _IssueCard(issue: issues[i], onTap: () => _open(issues[i].url)),
                              ),
                      ),
                    ),
                  ],
                ),
    );
  }

  Widget _header(SecurityFeed feed) {
    final updated = feed.updatedAt.isNotEmpty
        ? feed.updatedAt.replaceFirst('T', ' ').split('+').first
        : '-';
    final isSample = _sourceLabel == '샘플';
    return Container(
      width: double.infinity,
      color: isSample ? Colors.amber.withValues(alpha: 0.18) : Colors.transparent,
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 6),
      child: Row(
        children: [
          Icon(isSample ? Icons.info_outline : Icons.cloud_done_outlined,
              size: 16, color: Colors.grey.shade700),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              isSample
                  ? '샘플 데이터 표시 중 — 피드 URL을 설정하면 매일 갱신됩니다.'
                  : '갱신: $updated · 출처: $_sourceLabel · ${feed.issues.length}건',
              style: TextStyle(fontSize: 12.5, color: Colors.grey.shade700),
            ),
          ),
        ],
      ),
    );
  }

  Widget _domainChips(SecurityFeed feed) {
    final doms = feed.filterDomains;
    return SizedBox(
      height: 46,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        children: [
          _chip('전체', _selectedDomain == null, () => setState(() => _selectedDomain = null)),
          for (final d in doms)
            _chip(d, _selectedDomain == d, () => setState(() => _selectedDomain = d)),
        ],
      ),
    );
  }

  Widget _regionChips(SecurityFeed feed) {
    return SizedBox(
      height: 42,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        children: [
          _chip('전체 지역', _selectedRegion == null, () => setState(() => _selectedRegion = null)),
          for (final r in feed.regions)
            _chip(r, _selectedRegion == r, () => setState(() => _selectedRegion = r)),
        ],
      ),
    );
  }

  Widget _chip(String label, bool selected, VoidCallback onTap) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 6),
      child: ChoiceChip(
        label: Text(label),
        selected: selected,
        onSelected: (_) => onTap(),
      ),
    );
  }
}

class _IssueCard extends StatelessWidget {
  final SecurityIssue issue;
  final VoidCallback onTap;
  const _IssueCard({required this.issue, required this.onTap});

  static const _domainColor = {
    '정치·국제': Color(0xFF9A4DCE),
    '사회·경제': Color(0xFF1E5BCB),
    '주식·증시': Color(0xFFC62828),
    '스포츠·문화': Color(0xFF13A07A),
    'IT·과학': Color(0xFF3949AB),
    '보안': Color(0xFFF57C00),
  };

  @override
  Widget build(BuildContext context) {
    final c = _domainColor[issue.domain] ?? const Color(0xFF9E9E9E);
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                        color: c.withValues(alpha: 0.13), borderRadius: BorderRadius.circular(6)),
                    child: Text(issue.domain,
                        style: TextStyle(color: c, fontWeight: FontWeight.w800, fontSize: 11.5)),
                  ),
                  const SizedBox(width: 6),
                  if (issue.region == '해외')
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                      decoration: BoxDecoration(
                          color: Colors.grey.withValues(alpha: 0.16),
                          borderRadius: BorderRadius.circular(6)),
                      child: Text('해외',
                          style: TextStyle(
                              color: Colors.grey.shade800, fontWeight: FontWeight.w700, fontSize: 11)),
                    ),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text('${issue.source} · ${issue.publishedDate}',
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
                  ),
                  Icon(Icons.open_in_new, size: 15, color: Colors.grey.shade500),
                ],
              ),
              const SizedBox(height: 8),
              Text(issue.title,
                  style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15.5, height: 1.35)),
              if (issue.summary.isNotEmpty && issue.summary != issue.title) ...[
                const SizedBox(height: 4),
                Text(issue.summary,
                    maxLines: 3,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(color: Colors.grey.shade800, fontSize: 13.5, height: 1.4)),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
