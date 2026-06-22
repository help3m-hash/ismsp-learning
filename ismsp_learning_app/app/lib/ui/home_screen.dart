import 'package:flutter/material.dart';
import '../main.dart';
import '../models/control_item.dart';
import '../theme/app_theme.dart';
import 'study_card_screen.dart';
import 'progress_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Future<void> _startSession({ControlItem? item}) async {
    final app = AppState.of(context);
    final session = item != null ? [item] : app.engine.buildSession(targetMinutes: 20);
    await Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => StudyCardScreen(session: session, indexInSession: 0),
    ));
    if (mounted) setState(() {}); // 진도 갱신 반영
  }

  @override
  Widget build(BuildContext context) {
    final app = AppState.of(context);
    final items = app.repo.items;
    final total = items.length;
    final studied = app.progress.studiedCount;
    final mastery = app.progress.masteryPct(total);

    return Scaffold(
      appBar: AppBar(
        title: const Text('ISMS-P 학습', style: TextStyle(fontWeight: FontWeight.w800)),
        actions: [
          IconButton(
            tooltip: '진도',
            icon: const Icon(Icons.bar_chart),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const ProgressScreen()),
            ).then((_) => setState(() {})),
          ),
        ],
      ),
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, c) {
            final hero = _HeroCard(
              studied: studied,
              total: total,
              mastery: mastery,
              onStart: () => _startSession(),
            );
            final list = _ItemList(items: items, onTap: (it) => _startSession(item: it));
            // 폴드 6 메인 화면(펼친 상태) 등 넓은 화면 → 2단 구성
            if (c.maxWidth >= 720) {
              return Padding(
                padding: const EdgeInsets.all(20),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(
                      width: 320,
                      child: SingleChildScrollView(child: hero),
                    ),
                    const SizedBox(width: 20),
                    Expanded(child: SingleChildScrollView(child: list)),
                  ],
                ),
              );
            }
            // 커버 화면 등 좁은 화면 → 단일 스크롤
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [hero, const SizedBox(height: 16), list],
            );
          },
        ),
      ),
    );
  }
}

class _HeroCard extends StatelessWidget {
  final int studied, total, mastery;
  final VoidCallback onStart;
  const _HeroCard({
    required this.studied,
    required this.total,
    required this.mastery,
    required this.onStart,
  });

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        gradient: LinearGradient(
          colors: [cs.primary, cs.primary.withValues(alpha: 0.78)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('오늘의 학습',
              style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w800)),
          const SizedBox(height: 6),
          const Text('통제항목 1개 + 퀴즈 · 약 15~25분',
              style: TextStyle(color: Colors.white70, fontSize: 14)),
          const SizedBox(height: 18),
          _MiniBar(label: '학습한 항목', value: '$studied / $total'),
          const SizedBox(height: 10),
          _MiniBar(label: '숙련도', value: '$mastery%'),
          const SizedBox(height: 18),
          FilledButton.icon(
            onPressed: onStart,
            style: FilledButton.styleFrom(
              backgroundColor: Colors.white,
              foregroundColor: cs.primary,
            ),
            icon: const Icon(Icons.play_arrow_rounded),
            label: const Text('학습 시작'),
          ),
        ],
      ),
    );
  }
}

class _MiniBar extends StatelessWidget {
  final String label, value;
  const _MiniBar({required this.label, required this.value});
  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(color: Colors.white70)),
        Text(value, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800)),
      ],
    );
  }
}

class _ItemList extends StatelessWidget {
  final List<ControlItem> items;
  final void Function(ControlItem) onTap;
  const _ItemList({required this.items, required this.onTap});

  @override
  Widget build(BuildContext context) {
    // 분야(category)별 그룹화
    final groups = <String, List<ControlItem>>{};
    for (final it in items) {
      groups.putIfAbsent(it.category, () => []).add(it);
    }
    final app = AppState.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final entry in groups.entries) ...[
          Padding(
            padding: const EdgeInsets.fromLTRB(4, 8, 4, 8),
            child: Text(entry.key,
                style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
          ),
          for (final it in entry.value)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: _ItemTile(
                item: it,
                box: app.progress.of(it.id).box,
                studied: app.progress.of(it.id).studied,
                lastScore: app.progress.of(it.id).lastScorePct,
                onTap: () => onTap(it),
              ),
            ),
        ],
      ],
    );
  }
}

class _ItemTile extends StatelessWidget {
  final ControlItem item;
  final int box, lastScore;
  final bool studied;
  final VoidCallback onTap;
  const _ItemTile({
    required this.item,
    required this.box,
    required this.studied,
    required this.lastScore,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final color = AppTheme.domainColor(item.id);
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Container(
                width: 44,
                height: 44,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(item.id,
                    style: TextStyle(color: color, fontWeight: FontWeight.w800, fontSize: 12)),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(item.title,
                        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
                    const SizedBox(height: 2),
                    Text(studied ? '최근 정답률 $lastScore% · 숙련 $box/4' : '미학습 · 약 ${item.estimatedMinutes}분',
                        style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
                  ],
                ),
              ),
              if (studied)
                Icon(Icons.check_circle, color: color, size: 20)
              else
                const Icon(Icons.chevron_right, color: Colors.grey),
            ],
          ),
        ),
      ),
    );
  }
}
