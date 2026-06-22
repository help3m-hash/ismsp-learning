import 'package:flutter/material.dart';
import '../main.dart';
import '../models/control_item.dart';
import '../models/quiz.dart';
import '../theme/app_theme.dart';
import 'result_screen.dart';

class QuizScreen extends StatefulWidget {
  final List<ControlItem> session;
  final int indexInSession;
  const QuizScreen({super.key, required this.session, required this.indexInSession});

  @override
  State<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends State<QuizScreen> {
  int _q = 0;
  int? _selected;
  bool _revealed = false;
  int _correct = 0;

  ControlItem get item => widget.session[widget.indexInSession];
  QuizQuestion get q => item.quiz[_q];

  void _choose(int i) {
    if (_revealed) return;
    setState(() {
      _selected = i;
      _revealed = true;
      if (q.isCorrect(i)) _correct++;
    });
  }

  Future<void> _next() async {
    if (_q < item.quiz.length - 1) {
      setState(() {
        _q++;
        _selected = null;
        _revealed = false;
      });
      return;
    }
    // 마지막 문항 → 진도 기록 후 결과 화면
    final pct = ((_correct / item.quiz.length) * 100).round();
    await AppState.of(context).progress.recordResult(item.id, pct);
    if (!mounted) return;
    Navigator.of(context).pushReplacement(MaterialPageRoute(
      builder: (_) => ResultScreen(
        session: widget.session,
        indexInSession: widget.indexInSession,
        correct: _correct,
        total: item.quiz.length,
      ),
    ));
  }

  @override
  Widget build(BuildContext context) {
    final color = AppTheme.domainColor(item.id);
    final isOx = q.type == QuizType.ox;
    return Scaffold(
      appBar: AppBar(
        title: Text('${item.id} 퀴즈'),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(4),
          child: LinearProgressIndicator(
            value: (_q + (_revealed ? 1 : 0)) / item.quiz.length,
            color: color,
            backgroundColor: color.withValues(alpha: 0.12),
          ),
        ),
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 640),
            child: ListView(
              padding: const EdgeInsets.all(20),
              children: [
                Text('문항 ${_q + 1} / ${item.quiz.length}',
                    style: TextStyle(color: Colors.grey.shade600, fontWeight: FontWeight.w700)),
                const SizedBox(height: 12),
                Text(q.question,
                    style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w800, height: 1.4)),
                const SizedBox(height: 20),
                if (isOx) _oxButtons(color) else _mcqButtons(color),
                if (_revealed) ...[
                  const SizedBox(height: 18),
                  _Feedback(q: q, selected: _selected!),
                ],
              ],
            ),
          ),
        ),
      ),
      bottomNavigationBar: _revealed
          ? SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: FilledButton(
                  onPressed: _next,
                  child: Text(_q < item.quiz.length - 1 ? '다음 문항' : '결과 보기'),
                ),
              ),
            )
          : null,
    );
  }

  Widget _oxButtons(Color color) {
    // O = index 1, X = index 0 (QuizQuestion.answerIndex와 일치)
    return Row(
      children: [
        Expanded(child: _choiceTile(label: 'O (맞다)', index: 1, color: color, big: true)),
        const SizedBox(width: 12),
        Expanded(child: _choiceTile(label: 'X (틀리다)', index: 0, color: color, big: true)),
      ],
    );
  }

  Widget _mcqButtons(Color color) {
    return Column(
      children: [
        for (var i = 0; i < q.choices.length; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: _choiceTile(label: q.choices[i], index: i, color: color),
          ),
      ],
    );
  }

  Widget _choiceTile({required String label, required int index, required Color color, bool big = false}) {
    Color bg = Colors.white;
    Color border = Colors.grey.shade300;
    Widget? trailing;
    if (_revealed) {
      final isAnswer = index == q.answerIndex;
      final isPicked = index == _selected;
      if (isAnswer) {
        bg = Colors.green.withValues(alpha: 0.10);
        border = Colors.green;
        trailing = const Icon(Icons.check_circle, color: Colors.green);
      } else if (isPicked) {
        bg = Colors.red.withValues(alpha: 0.08);
        border = Colors.red;
        trailing = const Icon(Icons.cancel, color: Colors.red);
      }
    }
    return Material(
      color: bg,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: () => _choose(index),
        child: Container(
          padding: EdgeInsets.symmetric(horizontal: 16, vertical: big ? 26 : 16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: border, width: 1.5),
          ),
          child: Row(
            children: [
              Expanded(
                child: Text(label,
                    textAlign: big ? TextAlign.center : TextAlign.start,
                    style: TextStyle(
                        fontSize: big ? 20 : 15.5,
                        fontWeight: big ? FontWeight.w800 : FontWeight.w600,
                        height: 1.35)),
              ),
              if (trailing != null) trailing,
            ],
          ),
        ),
      ),
    );
  }
}

class _Feedback extends StatelessWidget {
  final QuizQuestion q;
  final int selected;
  const _Feedback({required this.q, required this.selected});

  @override
  Widget build(BuildContext context) {
    final correct = q.isCorrect(selected);
    final c = correct ? Colors.green : Colors.red;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: c.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: c.withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Icon(correct ? Icons.check_circle : Icons.cancel, color: c, size: 20),
            const SizedBox(width: 6),
            Text(correct ? '정답' : '오답',
                style: TextStyle(color: c, fontWeight: FontWeight.w800, fontSize: 16)),
          ]),
          const SizedBox(height: 8),
          Text(q.explanation, style: const TextStyle(height: 1.45, fontSize: 14.5)),
          const SizedBox(height: 8),
          Text('원문 근거: ${q.source}',
              style: TextStyle(color: Colors.grey.shade600, fontSize: 12.5, fontStyle: FontStyle.italic)),
        ],
      ),
    );
  }
}
