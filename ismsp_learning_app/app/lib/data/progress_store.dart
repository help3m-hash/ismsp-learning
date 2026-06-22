import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

/// 항목별 학습 진도(간단한 Leitner 방식 SRS).
class ItemProgress {
  int timesStudied;
  int box; // 0~4, 높을수록 잘 아는 항목(다시 볼 우선순위↓)
  int lastScorePct; // 최근 퀴즈 정답률(%)
  int lastStudiedMs; // epoch millis, 0=미학습

  ItemProgress({
    this.timesStudied = 0,
    this.box = 0,
    this.lastScorePct = 0,
    this.lastStudiedMs = 0,
  });

  bool get studied => timesStudied > 0;

  Map<String, dynamic> toJson() => {
        't': timesStudied,
        'b': box,
        's': lastScorePct,
        'l': lastStudiedMs,
      };

  factory ItemProgress.fromJson(Map<String, dynamic> j) => ItemProgress(
        timesStudied: (j['t'] as num?)?.toInt() ?? 0,
        box: (j['b'] as num?)?.toInt() ?? 0,
        lastScorePct: (j['s'] as num?)?.toInt() ?? 0,
        lastStudiedMs: (j['l'] as num?)?.toInt() ?? 0,
      );
}

/// shared_preferences 기반 오프라인 진도 저장소.
class ProgressStore {
  static const _key = 'ismsp_progress_v1';
  final Map<String, ItemProgress> _map = {};

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == null) return;
    final decoded = jsonDecode(raw) as Map<String, dynamic>;
    decoded.forEach((id, v) {
      _map[id] = ItemProgress.fromJson(v as Map<String, dynamic>);
    });
  }

  ItemProgress of(String id) => _map[id] ??= ItemProgress();

  /// 세션 완료 후 결과를 반영(정답률에 따라 Leitner box 증감).
  Future<void> recordResult(String id, int scorePct) async {
    final p = of(id);
    p.timesStudied += 1;
    p.lastScorePct = scorePct;
    p.lastStudiedMs = DateTime.now().millisecondsSinceEpoch;
    if (scorePct >= 80) {
      p.box = (p.box + 1).clamp(0, 4);
    } else if (scorePct < 50) {
      p.box = (p.box - 1).clamp(0, 4);
    }
    await _save();
  }

  Future<void> resetAll() async {
    _map.clear();
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }

  int get studiedCount => _map.values.where((p) => p.studied).length;

  /// 전체 항목 대비 가중 숙련도(0~100). box(0~4)를 25%씩 환산.
  int masteryPct(int totalItems) {
    if (totalItems == 0) return 0;
    final sum = _map.values.fold<int>(0, (a, p) => a + p.box);
    return ((sum / (totalItems * 4)) * 100).round().clamp(0, 100);
  }

  Future<void> _save() async {
    final prefs = await SharedPreferences.getInstance();
    final obj = _map.map((k, v) => MapEntry(k, v.toJson()));
    await prefs.setString(_key, jsonEncode(obj));
  }
}
