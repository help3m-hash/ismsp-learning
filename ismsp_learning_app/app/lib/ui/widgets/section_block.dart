import 'package:flutter/material.dart';
import '../../data/content_repository.dart';
import 'glossary_text.dart';

/// 학습 카드의 한 섹션(제목 + 불릿 목록).
class SectionBlock extends StatelessWidget {
  final String title;
  final IconData icon;
  final List<String> items;
  final List<GlossaryTerm> glossary;
  final bool numbered;

  const SectionBlock({
    super.key,
    required this.title,
    required this.icon,
    required this.items,
    required this.glossary,
    this.numbered = false,
  });

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return const SizedBox.shrink();
    final cs = Theme.of(context).colorScheme;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: cs.outlineVariant.withValues(alpha: 0.5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Icon(icon, size: 18, color: cs.primary),
            const SizedBox(width: 8),
            Text(title, style: TextStyle(fontWeight: FontWeight.w800, color: cs.primary)),
          ]),
          const SizedBox(height: 10),
          for (var k = 0; k < items.length; k++)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.only(top: 2, right: 8),
                    child: Text(numbered ? '${k + 1}.' : '•',
                        style: TextStyle(color: cs.primary, fontWeight: FontWeight.w700)),
                  ),
                  Expanded(
                    child: GlossaryText(
                      items[k],
                      glossary: glossary,
                      style: const TextStyle(height: 1.45, fontSize: 15),
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
