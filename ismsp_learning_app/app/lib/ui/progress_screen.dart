import 'package:flutter/material.dart';
import '../main.dart';
import '../theme/app_theme.dart';

class ProgressScreen extends StatefulWidget {
  const ProgressScreen({super.key});
  @override
  State<ProgressScreen> createState() => _ProgressScreenState();
}

class _ProgressScreenState extends State<ProgressScreen> {
  @override
  Widget build(BuildContext context) {
    final app = AppState.of(context);
    final items = app.repo.items;
    final total = items.length;
    final studied = app.progress.studiedCount;
    final mastery = app.progress.masteryPct(total);

    return Scaffold(
      appBar: AppBar(
        title: const Text('학습 진도'),
        actions: [
          TextButton(
            onPressed: () async {
              final ok = await showDialog<bool>(
                context: context,
                builder: (_) => AlertDialog(
                  title: const Text('진도 초기화'),
                  content: const Text('모든 학습 기록을 삭제할까요?'),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('취소')),
                    TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('삭제')),
                  ],
                ),
              );
              if (ok == true) {
                await app.progress.resetAll();
                if (mounted) setState(() {});
              }
            },
            child: const Text('초기화'),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Row(
              children: [
                Expanded(child: _stat('학습한 항목', '$studied / $total')),
                const SizedBox(width: 12),
                Expanded(child: _stat('전체 숙련도', '$mastery%')),
              ],
            ),
            const SizedBox(height: 8),
            for (final it in items)
              Builder(builder: (context) {
                final p = app.progress.of(it.id);
                final color = AppTheme.domainColor(it.id);
                return Card(
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Row(
                      children: [
                        SizedBox(
                          width: 48,
                          child: Text(it.id,
                              style: TextStyle(color: color, fontWeight: FontWeight.w800)),
                        ),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(it.title, style: const TextStyle(fontWeight: FontWeight.w700)),
                              const SizedBox(height: 6),
                              LinearProgressIndicator(
                                value: p.box / 4,
                                color: color,
                                backgroundColor: color.withValues(alpha: 0.12),
                                minHeight: 6,
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 12),
                        Text(p.studied ? '${p.lastScorePct}%' : '-',
                            style: TextStyle(color: Colors.grey.shade600, fontWeight: FontWeight.w700)),
                      ],
                    ),
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }

  Widget _stat(String label, String value) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(color: Colors.grey.shade600)),
          const SizedBox(height: 6),
          Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
        ],
      ),
    );
  }
}
