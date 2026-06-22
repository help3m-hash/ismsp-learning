import 'package:flutter/material.dart';
import 'data/content_repository.dart';
import 'data/progress_store.dart';
import 'services/session_engine.dart';
import 'theme/app_theme.dart';
import 'ui/home_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const IsmspApp());
}

/// 앱 전역 상태(레포지토리/진도/세션엔진)를 자식 위젯에 전달.
class AppState extends InheritedWidget {
  final ContentRepository repo;
  final ProgressStore progress;
  final SessionEngine engine;

  const AppState({
    super.key,
    required this.repo,
    required this.progress,
    required this.engine,
    required super.child,
  });

  static AppState of(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<AppState>()!;

  @override
  bool updateShouldNotify(AppState oldWidget) => false;
}

class IsmspApp extends StatefulWidget {
  const IsmspApp({super.key});

  @override
  State<IsmspApp> createState() => _IsmspAppState();
}

class _IsmspAppState extends State<IsmspApp> {
  final _repo = ContentRepository();
  final _progress = ProgressStore();
  late final SessionEngine _engine = SessionEngine(_repo, _progress);
  late final Future<void> _bootstrap = _init();

  Future<void> _init() async {
    await _repo.load();
    await _progress.load();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ISMS-P 학습',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      // builder로 Navigator(=child) 위에 AppState를 두어, 푸시되는 모든 화면이
      // AppState.of(context)에 접근할 수 있게 한다.
      builder: (context, child) {
        return FutureBuilder<void>(
          future: _bootstrap,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) {
              return const Directionality(
                textDirection: TextDirection.ltr,
                child: ColoredBox(
                  color: Color(0xFFF6F7FB),
                  child: Center(child: CircularProgressIndicator()),
                ),
              );
            }
            if (snap.hasError) {
              return Directionality(
                textDirection: TextDirection.ltr,
                child: ColoredBox(
                  color: const Color(0xFFF6F7FB),
                  child: Center(
                    child: Text('콘텐츠 로드 실패\n${snap.error}', textAlign: TextAlign.center),
                  ),
                ),
              );
            }
            return AppState(
              repo: _repo,
              progress: _progress,
              engine: _engine,
              child: child!,
            );
          },
        );
      },
      home: const HomeScreen(),
    );
  }
}
