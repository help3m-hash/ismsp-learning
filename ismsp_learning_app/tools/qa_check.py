#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ISMS-P 학습 콘텐츠 외부 QA 회귀검사.
content/items/*.json 을 원문(content/raw/ismsp_guide_2023.txt)과 대조한다.
사용법:  python tools/qa_check.py     (프로젝트 루트에서 실행)
"""
import json, glob, re, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'content', 'raw', 'ismsp_guide_2023.txt')
ITEMS = os.path.join(ROOT, 'content', 'items', '*.json')

def norm(s): return re.sub(r'\s+', '', s)

def main():
    raw = open(RAW, encoding='utf-8').read()
    nraw = norm(raw)
    files = sorted(glob.glob(ITEMS))
    errs, warns = [], []
    total_q = 0
    for f in files:
        d = json.load(open(f, encoding='utf-8'))
        rid = d.get('id', os.path.basename(f))
        # 필수 필드
        for k in ['domain', 'category', 'title', 'standard', 'checkpoints',
                  'explanation', 'deficiency_cases', 'quiz']:
            if not d.get(k):
                errs.append(f'{rid}: 필드 누락/빈값 {k}')
        # 인증기준 원문 일치 (핵심)
        if norm(d.get('standard', '')) not in nraw:
            errs.append(f'{rid}: 인증기준(standard)이 원문과 불일치')
        # 법령 인용 원문 존재
        for law in d.get('related_laws', []):
            key = norm(law.split('(')[0])
            if key and key not in nraw:
                warns.append(f'{rid}: 법령 인용 원문 미확인 -> {law}')
        # 퀴즈
        qs = d.get('quiz', [])
        total_q += len(qs)
        ncase = len(d.get('deficiency_cases', []))
        for i, q in enumerate(qs):
            t = q.get('type')
            if t == 'ox':
                if not isinstance(q.get('answer'), bool):
                    errs.append(f'{rid} q{i}: ox answer가 bool 아님')
            elif t == 'mcq':
                ch = q.get('choices', [])
                a = q.get('answer')
                if len(ch) < 2 or not isinstance(a, int) or not (0 <= a < len(ch)):
                    errs.append(f'{rid} q{i}: mcq choices/answer 오류')
            else:
                errs.append(f'{rid} q{i}: 알 수 없는 type {t}')
            if not q.get('source'):
                errs.append(f'{rid} q{i}: source 누락')
            if not q.get('explanation'):
                errs.append(f'{rid} q{i}: explanation 누락')
            m = re.search(r'결함사례\s*(\d+)', q.get('source', ''))
            if m and int(m.group(1)) > ncase:
                errs.append(f'{rid} q{i}: source={q["source"]} 인데 결함사례는 {ncase}개')

    print(f'검사 파일: {len(files)}개, 총 퀴즈: {total_q}문항')
    if warns:
        print('\n[경고]')
        print('\n'.join(' - ' + w for w in warns))
    if errs:
        print('\n[오류]')
        print('\n'.join(' - ' + e for e in errs))
        sys.exit(1)
    print('\nQA PASS: 구조/원문/법령/출처 이상 없음')

if __name__ == '__main__':
    main()
