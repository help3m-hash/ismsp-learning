import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../data/security_repository.dart';
import '../models/security_issue.dart';

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
  String? _selectedKeyword; // null = 전체

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

  @override
  Widget build(BuildContext context) {
    final feed = _feed;
    final issues = feed == null
        ? <SecurityIssue>[]
        : (_selectedKeyword == null
            ? feed.issues
            : feed.issues.where((i) => i.keywords.contains(_selectedKeyword)).toList());

    return Scaffold(
      appBar: AppBar(
        title: const Text('보안 이슈'),
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
                    _filterChips(feed),
                    Expanded(
                      child: RefreshIndicator(
                        onRefresh: () => _load(refresh: true),
                        child: ListView.builder(
                          padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                          itemCount: issues.length,
                          itemBuilder: (_, i) => _IssueCard(issue: issues[i], onTap: () => _open(issues[i].url)),
                        ),
                      ),
                    ),
                  ],
                ),
    );
  }

  Widget _header(SecurityFeed feed) {
    final updated = feed.updatedAt.isNotEmpty ? feed.updatedAt.replaceFirst('T', ' ').split('+').first : '-';
    final isSample = _sourceLabel == '샘플';
    return Container(
      width: double.infinity,
      color: isSample ? Colors.amber.withValues(alpha: 0.18) : Colors.transparent,
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),
      child: Row(
        children: [
          Icon(isSample ? Icons.info_outline : Icons.cloud_done_outlined,
              size: 16, color: Colors.grey.shade700),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              isSample
                  ? '샘플 데이터 표시 중 — 피드 URL을 설정하면 매일 갱신됩니다.'
                  : '갱신: $updated · 출처: $_sourceLabel',
              style: TextStyle(fontSize: 12.5, color: Colors.grey.shade700),
            ),
          ),
        ],
      ),
    );
  }

  Widget _filterChips(SecurityFeed feed) {
    final kws = feed.allKeywords;
    return SizedBox(
      height: 46,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        children: [
          _chip('전체', _selectedKeyword == null, () => setState(() => _selectedKeyword = null)),
          for (final k in kws)
            _chip(k, _selectedKeyword == k, () => setState(() => _selectedKeyword = k)),
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

  static const _sevColor = {
    '긴급': Color(0xFFD32F2F),
    '높음': Color(0xFFF57C00),
    '중간': Color(0xFF1E5BCB),
    '낮음': Color(0xFF607D8B),
    '정보': Color(0xFF9E9E9E),
  };

  @override
  Widget build(BuildContext context) {
    final c = _sevColor[issue.severity] ?? _sevColor['정보']!;
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
                    decoration: BoxDecoration(color: c.withValues(alpha: 0.13), borderRadius: BorderRadius.circular(6)),
                    child: Text(issue.severity, style: TextStyle(color: c, fontWeight: FontWeight.w800, fontSize: 12)),
                  ),
                  const SizedBox(width: 8),
                  Text('${issue.source} · ${issue.published}',
                      style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
                  const Spacer(),
                  Icon(Icons.open_in_new, size: 15, color: Colors.grey.shade500),
                ],
              ),
              const SizedBox(height: 8),
              Text(issue.title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15.5, height: 1.35)),
              if (issue.summary.isNotEmpty && issue.summary != issue.title) ...[
                const SizedBox(height: 4),
                Text(issue.summary, style: TextStyle(color: Colors.grey.shade800, fontSize: 13.5, height: 1.4)),
              ],
              if (issue.keywords.isNotEmpty) ...[
                const SizedBox(height: 8),
                Wrap(
                  spacing: 6,
                  runSpacing: -4,
                  children: [
                    for (final k in issue.keywords)
                      Chip(
                        label: Text(k, style: const TextStyle(fontSize: 11)),
                        materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        visualDensity: VisualDensity.compact,
                        padding: EdgeInsets.zero,
                      ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
