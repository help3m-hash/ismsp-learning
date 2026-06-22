import 'package:flutter/material.dart';
import '../models/control_item.dart';
import '../theme/app_theme.dart';
import 'study_card_screen.dart';

class ResultScreen extends StatelessWidget {
  final List<ControlItem> session;
  final int indexInSession;
  final int correct;
  final int total;
  const ResultScreen({
    super.key,
    required this.session,
    required this.indexInSession,
    required this.correct,
    required this.total,
  });

  @override
  Widget build(BuildContext context) {
    final item = session[indexInSession];
    final color = AppTheme.domainColor(item.id);
    final pct = total == 0 ? 0 : ((correct / total) * 100).round();
    final hasNext = indexInSession + 1 < session.length;
    final (msg, emoji) = pct >= 80
        ? ('아주 좋아요! 이 항목은 잘 이해했어요.', '🎉')
        : pct >= 50
            ? ('괜찮아요. 결함사례를 한 번 더 보면 좋아요.', '👍')
            : ('이 항목은 곧 다시 복습 대상으로 올라옵니다.', '📌');

    return Scaffold(
      appBar: AppBar(title: const Text('학습 결과')),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 480),
            child: ListView(
              shrinkWrap: true,
              padding: const EdgeInsets.all(24),
              children: [
                Text(emoji, style: const TextStyle(fontSize: 56), textAlign: TextAlign.center),
                const SizedBox(height: 12),
                Text(item.displayTitle,
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                const SizedBox(height: 20),
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: color.withValues(alpha: 0.35)),
                  ),
                  child: Column(
                    children: [
                      Text('$pct점',
                          style: TextStyle(
                              fontSize: 44, fontWeight: FontWeight.w900, color: color)),
                      Text('$correct / $total 정답',
                          style: TextStyle(color: Colors.grey.shade700, fontWeight: FontWeight.w700)),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                Text(msg, textAlign: TextAlign.center, style: const TextStyle(fontSize: 15, height: 1.4)),
                const SizedBox(height: 28),
                if (hasNext)
                  FilledButton.icon(
                    onPressed: () => Navigator.of(context).pushReplacement(MaterialPageRoute(
                      builder: (_) => StudyCardScreen(
                          session: session, indexInSession: indexInSession + 1),
                    )),
                    icon: const Icon(Icons.arrow_forward),
                    label: const Text('다음 항목 학습'),
                  ),
                if (hasNext) const SizedBox(height: 10),
                OutlinedButton.icon(
                  style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(52)),
                  onPressed: () => Navigator.of(context).popUntil((r) => r.isFirst),
                  icon: const Icon(Icons.home),
                  label: const Text('홈으로'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
