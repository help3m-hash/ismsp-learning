#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""영역 2·3(85개 항목) 콘텐츠 JSON 일괄 생성.
- 학습카드 필드: extract_content 로 raw에서 추출(인증기준 verbatim).
- 결함사례: 첨부 JSON(verbatim).
- 퀴즈: 결함사례 기반 안전 템플릿 4문항(원문추적 source 포함).
실행: python tools/build_content.py   (영역1 16개는 건드리지 않음)
"""
import json, os, re, random
import extract_content as ex

ROOT = ex.ROOT
OUT = os.path.join(ROOT, 'content', 'items')

CATEGORY = {
    '2.1': '정책, 조직, 자산 관리', '2.2': '인적 보안', '2.3': '외부자 보안',
    '2.4': '물리 보안', '2.5': '인증 및 권한관리', '2.6': '접근통제',
    '2.7': '암호화 적용', '2.8': '정보시스템 도입 및 개발 보안',
    '2.9': '시스템 및 서비스 운영관리', '2.10': '시스템 및 서비스 보안관리',
    '2.11': '사고 예방 및 대응', '2.12': '재해 복구',
    '3.1': '개인정보 수집 시 보호조치', '3.2': '개인정보 보유 및 이용 시 보호조치',
    '3.3': '개인정보 제공 시 보호조치', '3.4': '개인정보 파기 시 보호조치',
    '3.5': '정보주체 권리보호',
}
DOMAIN = {'2': '2. 보호대책 요구사항', '3': '3. 개인정보 처리 단계별 요구사항'}


def short(text, limit=95):
    t = re.sub(r'\s+', ' ', text).strip().rstrip('수 ').strip()
    if len(t) <= limit:
        return t
    cut = t[:limit]
    sp = cut.rfind(' ')
    return (cut[:sp] if sp > 40 else cut).strip() + '…'


def make_quiz(code, name, cases, pool, rng):
    """결함사례 기반 4문항 생성. pool: [(code,name,text), ...] 전체."""
    own = [c['text'].strip() for c in cases]
    others = [p for p in pool if p[0] != code]
    rng.shuffle(others)

    quiz = []
    # 1) OX(참): 자기 결함사례
    quiz.append({
        'type': 'ox',
        'question': f'다음은 {code} {name}의 결함사례에 해당한다.\n\n「{short(own[0], 140)}」',
        'answer': True,
        'explanation': f'맞습니다. 이는 {code} {name}의 결함사례입니다.',
        'source': '결함사례 1',
    })
    # 2) OX(거짓): 다른 항목의 결함사례
    oc, on, ot = others[0]
    quiz.append({
        'type': 'ox',
        'question': f'다음은 {code} {name}의 결함사례에 해당한다.\n\n「{short(ot, 140)}」',
        'answer': False,
        'explanation': f'아닙니다. 이는 {oc} {on}의 결함사례입니다. {name}의 결함과 구분하세요.',
        'source': f'대조: {oc}',
    })
    # 3) MCQ: 이 항목의 결함사례 고르기
    own_idx = 1 if len(own) > 1 else 0
    correct = short(own[own_idx])
    distract = [short(t) for (_, _, t) in others[1:4]]
    choices = distract + [correct]
    rng.shuffle(choices)
    quiz.append({
        'type': 'mcq',
        'question': f'다음 중 {code} {name}의 결함사례에 해당하는 것은?',
        'choices': choices,
        'answer': choices.index(correct),
        'explanation': f'정답은 {code} {name}의 실제 결함사례이며, 나머지는 다른 인증기준의 결함사례입니다.',
        'source': f'결함사례 {own_idx + 1}',
    })
    # 4) MCQ: 결함사례 → 인증기준 코드 맞추기
    case_for_q = own[-1]
    od = others[4:7] if len(others) >= 7 else others[1:4]
    opts = [f'{oc2} {on2}' for (oc2, on2, _) in od]
    answer_label = f'{code} {name}'
    opts4 = opts + [answer_label]
    rng.shuffle(opts4)
    quiz.append({
        'type': 'mcq',
        'question': f'다음 결함사례는 어느 인증기준에 해당하는가?\n\n「{short(case_for_q, 140)}」',
        'choices': opts4,
        'answer': opts4.index(answer_label),
        'explanation': f'이 사례는 {code} {name}의 결함사례입니다.',
        'source': f'결함사례 {len(own)}',
    })
    return quiz


def build():
    lines = open(ex.RAW, encoding='utf-8').read().splitlines()
    data, by = ex.load_cases()
    codes = [c['code'] for c in data]
    starts = ex.find_block_starts(lines, codes)
    ordered = sorted(starts.items(), key=lambda kv: kv[1])
    idxmap = {c: n for n, (c, _) in enumerate(ordered)}

    # 결함사례 전체 풀(거짓 OX·오답용)
    pool = [(c['code'], ex.sanitize_name(c['name']), cs['text'].strip())
            for c in data for cs in c['cases']]

    targets = [c for c in codes if c.split('.')[0] in ('2', '3')]
    written = 0
    for code in targets:
        n = idxmap[code]
        s = ordered[n][1]
        e = ordered[n + 1][1] if n + 1 < len(ordered) else len(lines)
        f = ex.parse_block(lines, s, e)
        info = by[code]
        name = ex.sanitize_name(info['name'])
        cat_key = code.rsplit('.', 1)[0]
        rng = random.Random('seed-' + code)  # 재현 가능
        cases = info['cases']
        ncase = len(cases)
        item = {
            'id': code,
            'domain': DOMAIN[code.split('.')[0]],
            'category': f'{cat_key} {CATEGORY[cat_key]}',
            'title': name,
            'estimated_minutes': max(15, min(30, 14 + 2 * min(ncase, 5) + (1 if f['related_laws'] else 0))),
            'standard': f['standard'],
            'checkpoints': f['checkpoints'],
            'explanation': f['explanation'],
            'evidence_examples': f['evidence'],
            'deficiency_cases': [c['text'].strip() for c in cases],
            'related_laws': f['related_laws'],
            'quiz': make_quiz(code, name, cases, pool, rng),
        }
        path = os.path.join(OUT, code + '.json')
        json.dump(item, open(path, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=2)
        written += 1
    print(f'생성 완료: {written}개 (영역 2·3)')


if __name__ == '__main__':
    build()
