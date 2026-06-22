import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import '../../data/content_repository.dart';

/// 본문 텍스트에서 용어집(CISO/CPO/DoA 등)을 찾아 점선 밑줄을 긋고,
/// 탭하면 정의 다이얼로그를 띄운다.
class GlossaryText extends StatefulWidget {
  final String text;
  final List<GlossaryTerm> glossary;
  final TextStyle? style;

  const GlossaryText(this.text, {super.key, required this.glossary, this.style});

  @override
  State<GlossaryText> createState() => _GlossaryTextState();
}

class _GlossaryTextState extends State<GlossaryText> {
  final List<TapGestureRecognizer> _recognizers = [];

  @override
  void dispose() {
    for (final r in _recognizers) {
      r.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final base = widget.style ?? DefaultTextStyle.of(context).style;
    final text = widget.text;
    if (widget.glossary.isEmpty) return Text(text, style: base);

    for (final r in _recognizers) {
      r.dispose();
    }
    _recognizers.clear();

    final terms = [...widget.glossary]
      ..sort((a, b) => b.term.length.compareTo(a.term.length));
    final spans = <InlineSpan>[];
    int i = 0;
    while (i < text.length) {
      GlossaryTerm? hit;
      for (final t in terms) {
        if (t.term.isNotEmpty && text.startsWith(t.term, i)) {
          hit = t;
          break;
        }
      }
      if (hit != null) {
        final term = hit;
        final rec = TapGestureRecognizer()..onTap = () => _showDef(context, term);
        _recognizers.add(rec);
        spans.add(TextSpan(
          text: term.term,
          style: base.copyWith(
            decoration: TextDecoration.underline,
            decorationStyle: TextDecorationStyle.dotted,
            fontWeight: FontWeight.w700,
            color: Theme.of(context).colorScheme.primary,
          ),
          recognizer: rec,
        ));
        i += term.term.length;
      } else {
        spans.add(TextSpan(text: text[i], style: base));
        i++;
      }
    }
    return Text.rich(TextSpan(children: spans));
  }

  void _showDef(BuildContext context, GlossaryTerm t) {
    showDialog<void>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text('${t.term} · ${t.full}'),
        content: Text(t.desc),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('닫기')),
        ],
      ),
    );
  }
}
