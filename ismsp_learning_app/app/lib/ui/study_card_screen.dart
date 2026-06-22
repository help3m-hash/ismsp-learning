import 'package:flutter/material.dart';
import '../data/content_repository.dart';
import '../main.dart';
import '../models/control_item.dart';
import '../theme/app_theme.dart';
import 'quiz_screen.dart';
import 'widgets/glossary_text.dart';
import 'widgets/section_block.dart';

class StudyCardScreen extends StatelessWidget {
  final List<ControlItem> session;
  final int indexInSession;
  const StudyCardScreen({super.key, required this.session, required this.indexInSession});

  ControlItem get item => session[indexInSession];

  @override
  Widget build(BuildContext context) {
    final app = AppState.of(context);
    final glossary = app.repo.glossary;
    final color = AppTheme.domainColor(item.id);

    // 카드 섹션들
    final left = <Widget>[
      _StandardCard(item: item, glossary: glossary, color: color),
      const SizedBox(height: 12),
      SectionBlock(
          title: '주요 확인사항',
          icon: Icons.checklist_rtl,
          items: item.checkpoints,
          glossary: glossary),
      const SizedBox(height: 12),
      SectionBlock(
          title: '세부 설명', icon: Icons.menu_book, items: item.explanation, glossary: glossary),
    ];
    final right = <Widget>[
      SectionBlock(
          title: '결함사례',
          icon: Icons.report_gmailerrorred,
          items: item.deficiencyCases,
          glossary: glossary,
          numbered: true),
      const SizedBox(height: 12),
      SectionBlock(
          title: '증거자료 예시',
          icon: Icons.folder_open,
          items: item.evidenceExamples,
          glossary: glossary),
      if (item.relatedLaws.isNotEmpty) ...[
        const SizedBox(height: 12),
        SectionBlock(
            title: '관련 법규', icon: Icons.gavel, items: item.relatedLaws, glossary: glossary),
      ],
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text(item.category, style: const TextStyle(fontSize: 15)),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(2),
          child: Container(height: 3, color: color),
        ),
      ),
      body: SafeArea(
        child: LayoutBuilder(builder: (context, c) {
          final header = _Header(item: item, color: color);
          if (c.maxWidth >= 600) {
            return Column(
              children: [
                Padding(padding: const EdgeInsets.fromLTRB(20, 16, 20, 0), child: header),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(child: ListView(children: left)),
                        const SizedBox(width: 16),
                        Expanded(child: ListView(children: right)),
                      ],
                    ),
                  ),
                ),
              ],
            );
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [header, const SizedBox(height: 12), ...left, const SizedBox(height: 12), ...right],
          );
        }),
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: FilledButton.icon(
            onPressed: () => Navigator.of(context).pushReplacement(MaterialPageRoute(
              builder: (_) => QuizScreen(session: session, indexInSession: indexInSession),
            )),
            icon: const Icon(Icons.quiz),
            label: Text('퀴즈 풀기 (${item.quiz.length}문항)'),
          ),
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  final ControlItem item;
  final Color color;
  const _Header({required this.item, required this.color});
  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(10)),
          child: Text(item.id,
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800)),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Text(item.title,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
        ),
        Icon(Icons.timer_outlined, size: 16, color: Colors.grey.shade500),
        const SizedBox(width: 4),
        Text('${item.estimatedMinutes}분', style: TextStyle(color: Colors.grey.shade600)),
      ],
    );
  }
}

class _StandardCard extends StatelessWidget {
  final ControlItem item;
  final List<GlossaryTerm> glossary;
  final Color color;
  const _StandardCard({required this.item, required this.glossary, required this.color});
  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Icon(Icons.flag, size: 18, color: color),
            const SizedBox(width: 8),
            Text('인증기준', style: TextStyle(fontWeight: FontWeight.w800, color: color)),
          ]),
          const SizedBox(height: 10),
          GlossaryText(item.standard,
              glossary: glossary,
              style: const TextStyle(height: 1.5, fontSize: 15.5, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
