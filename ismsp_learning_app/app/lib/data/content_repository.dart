import 'dart:convert';
import 'package:flutter/services.dart' show rootBundle;
import '../models/control_item.dart';

class GlossaryTerm {
  final String term;
  final String full;
  final String desc;
  GlossaryTerm(this.term, this.full, this.desc);
}

/// 앱 에셋에 동봉된 콘텐츠(16개 인증기준 + 용어집)를 로드한다. 완전 오프라인.
class ContentRepository {
  static const _base = 'assets/content';
  List<ControlItem> _items = const [];
  List<GlossaryTerm> _glossary = const [];

  List<ControlItem> get items => _items;
  List<GlossaryTerm> get glossary => _glossary;

  bool get isLoaded => _items.isNotEmpty;

  Future<void> load() async {
    if (isLoaded) return;
    final indexStr = await rootBundle.loadString('$_base/index.json');
    final ids = (jsonDecode(indexStr)['items'] as List).cast<String>();

    final loaded = <ControlItem>[];
    for (final id in ids) {
      final str = await rootBundle.loadString('$_base/items/$id.json');
      loaded.add(ControlItem.fromJson(jsonDecode(str) as Map<String, dynamic>));
    }
    loaded.sort((a, b) => _cmpId(a.id, b.id));
    _items = loaded;

    try {
      final gStr = await rootBundle.loadString('$_base/glossary.json');
      final terms = (jsonDecode(gStr)['terms'] as List? ?? const []);
      _glossary = terms
          .map((t) => GlossaryTerm(
                t['term'] as String? ?? '',
                t['full'] as String? ?? '',
                t['desc'] as String? ?? '',
              ))
          .toList();
    } catch (_) {
      _glossary = const [];
    }
  }

  ControlItem byId(String id) => _items.firstWhere((e) => e.id == id);

  /// "1.10.2" 같은 다단계 코드도 자연 정렬.
  static int _cmpId(String a, String b) {
    final pa = a.split('.').map(int.parse).toList();
    final pb = b.split('.').map(int.parse).toList();
    for (var i = 0; i < pa.length && i < pb.length; i++) {
      final c = pa[i].compareTo(pb[i]);
      if (c != 0) return c;
    }
    return pa.length.compareTo(pb.length);
  }
}
