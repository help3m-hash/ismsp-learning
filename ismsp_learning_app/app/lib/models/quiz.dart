enum QuizType { ox, mcq }

/// 퀴즈 1문항. OX(answer=bool) 또는 MCQ(answer=정답 index).
class QuizQuestion {
  final QuizType type;
  final String question;
  final List<String> choices; // MCQ에서만 사용
  final int answerIndex; // MCQ: 정답 index / OX: 1=O(true), 0=X(false)
  final String explanation;
  final String source; // 원문 출처(QA 추적용, 해설에 함께 노출)

  QuizQuestion({
    required this.type,
    required this.question,
    required this.choices,
    required this.answerIndex,
    required this.explanation,
    required this.source,
  });

  /// OX 문항에서 정답이 O(true)인지 여부.
  bool get oxAnswer => type == QuizType.ox && answerIndex == 1;

  /// 사용자가 고른 선택지 index가 정답인지 검사.
  /// OX 화면은 O를 1, X를 0으로 전달한다.
  bool isCorrect(int selectedIndex) => selectedIndex == answerIndex;

  factory QuizQuestion.fromJson(Map<String, dynamic> j) {
    final t = (j['type'] as String? ?? 'mcq') == 'ox' ? QuizType.ox : QuizType.mcq;
    int ans;
    if (t == QuizType.ox) {
      ans = (j['answer'] == true) ? 1 : 0;
    } else {
      ans = (j['answer'] as num?)?.toInt() ?? 0;
    }
    return QuizQuestion(
      type: t,
      question: j['question'] as String? ?? '',
      choices: (j['choices'] as List?)?.map((e) => e.toString()).toList() ??
          const ['O', 'X'],
      answerIndex: ans,
      explanation: j['explanation'] as String? ?? '',
      source: j['source'] as String? ?? '',
    );
  }
}
