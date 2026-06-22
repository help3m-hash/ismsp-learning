import 'quiz.dart';

/// ISMS-P 인증기준 1개(학습 카드 + 퀴즈)에 대응하는 모델.
class ControlItem {
  final String id; // 예: "1.1.1"
  final String domain;
  final String category;
  final String title;
  final int estimatedMinutes;
  final String standard;
  final List<String> checkpoints;
  final List<String> explanation;
  final List<String> evidenceExamples;
  final List<String> deficiencyCases;
  final List<String> relatedLaws;
  final List<QuizQuestion> quiz;

  ControlItem({
    required this.id,
    required this.domain,
    required this.category,
    required this.title,
    required this.estimatedMinutes,
    required this.standard,
    required this.checkpoints,
    required this.explanation,
    required this.evidenceExamples,
    required this.deficiencyCases,
    required this.relatedLaws,
    required this.quiz,
  });

  /// "1.1.1 경영진의 참여"
  String get displayTitle => '$id $title';

  static List<String> _strList(dynamic v) =>
      (v as List?)?.map((e) => e.toString()).toList() ?? const [];

  factory ControlItem.fromJson(Map<String, dynamic> j) {
    return ControlItem(
      id: j['id'] as String,
      domain: j['domain'] as String? ?? '',
      category: j['category'] as String? ?? '',
      title: j['title'] as String? ?? '',
      estimatedMinutes: (j['estimated_minutes'] as num?)?.toInt() ?? 20,
      standard: j['standard'] as String? ?? '',
      checkpoints: _strList(j['checkpoints']),
      explanation: _strList(j['explanation']),
      evidenceExamples: _strList(j['evidence_examples']),
      deficiencyCases: _strList(j['deficiency_cases']),
      relatedLaws: _strList(j['related_laws']),
      quiz: (j['quiz'] as List? ?? const [])
          .map((q) => QuizQuestion.fromJson(q as Map<String, dynamic>))
          .toList(),
    );
  }
}
