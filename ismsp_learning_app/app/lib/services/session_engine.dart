import 'dart:math';
import '../data/content_repository.dart';
import '../data/progress_store.dart';
import '../models/control_item.dart';

/// 한 학습 세션(15~30분)에 다룰 항목을 선정한다.
/// 우선순위: 미학습 > 낮은 box(덜 숙련) > 오래전 학습. 동점은 랜덤.
class SessionEngine {
  final ContentRepository repo;
  final ProgressStore progress;
  final Random _rng;

  SessionEngine(this.repo, this.progress, [Random? rng])
      : _rng = rng ?? Random();

  /// 다음에 학습할 1개 항목을 선정.
  ControlItem pickNext({String? excludeId}) {
    final candidates =
        repo.items.where((i) => i.id != excludeId).toList(growable: false);
    final pool = candidates.isEmpty ? repo.items : candidates;

    double weight(ControlItem it) {
      final p = progress.of(it.id);
      // 미학습 항목에 큰 가중치, box가 낮을수록 가중치↑
      final base = p.studied ? (5 - p.box).toDouble() : 12.0;
      // 마지막 학습이 오래될수록 약간 가중
      final ageDays = p.lastStudiedMs == 0
          ? 0
          : (DateTime.now().millisecondsSinceEpoch - p.lastStudiedMs) /
              (1000 * 60 * 60 * 24);
      return base + min(ageDays, 14) * 0.2 + _rng.nextDouble();
    }

    pool.sort((a, b) => weight(b).compareTo(weight(a)));
    // 상위 3개 중 랜덤(약간의 다양성)
    final top = pool.take(min(3, pool.length)).toList();
    return top[_rng.nextInt(top.length)];
  }

  /// 추천 세션 구성: 목표 시간(분)에 맞춰 1~2개 항목.
  List<ControlItem> buildSession({int targetMinutes = 20}) {
    final first = pickNext();
    final session = [first];
    if (first.estimatedMinutes < targetMinutes - 6) {
      session.add(pickNext(excludeId: first.id));
    }
    return session;
  }
}
