#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ISMS-P 안내서 원문(raw)에서 인증기준별 구조 필드를 추출한다.
- 결함사례는 첨부 JSON(원문추출)을 사용(검증된 verbatim).
- 나머지(인증기준/주요 확인사항/관련 법규/세부 설명/증거자료)는 raw에서 추출.
본문(제2장) 블록 = '코드  이름' 헤더 직후 2줄 내 '인증기준' 헤더가 오는 위치.
"""
import json, re, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'content', 'raw', 'ismsp_guide_2023.txt')

BULLET_MAIN = chr(0xf06e)   # 세부설명 대주제 불릿
BULLET_DOT = chr(0xf09f)    # 확인사항/법규/증거자료 불릿
SUB_MARKS = (chr(0x25b6), chr(0x203b), chr(0xb7), chr(0x2219), chr(0xf0a7))
SECTIONS = ['인증기준', '주요 확인사항', '관련 법규', '세부 설명', '증거자료', '결함사례']

def load_cases():
    p = os.environ.get('CASES_JSON',
                        r'C:\Users\SECUI\Downloads\ISMS-P_결함사례_원문추출.json')
    data = json.load(open(p, encoding='utf-8'))
    return data, {c['code']: c for c in data}

def is_noise(l):
    s = l.strip()
    if s == '':
        return True
    if s.startswith('=====') and 'PAGE' in s:
        return True
    if s.startswith('제2장') or s.startswith('제1장'):
        return True
    if s == '정보보호 및 개인정보보호 관리체계 인증제도 안내서':
        return True
    if re.fullmatch(r'\d{1,3}', s):       # 페이지 번호
        return True
    if len(s) == 1:                        # 세로 사이드바 단일 음절
        return True
    return False

def find_block_starts(lines, codes):
    """각 코드의 본문 헤더 라인 index를 반환.
    본문 블록 = '코드  이름' 헤더 직후 1~3줄 내에 '인증기준'(별도줄 또는 인라인)이 오는 위치."""
    starts = {}
    codeset = set(codes)
    for i, l in enumerate(lines):
        m = re.match(r'^\s*(\d+\.\d+\.\d+)\s{1,}(\S.*)$', l)
        if not m:
            continue
        code = m.group(1)
        if code not in codeset:
            continue
        nxt = [lines[j].strip() for j in range(i + 1, min(i + 4, len(lines)))]
        if any(s == '인증기준' or s.startswith('인증기준') for s in nxt):
            starts.setdefault(code, i)
    return starts

def section_of(s):
    """라인 stripped가 섹션 헤더면 (섹션명, 인라인 잔여텍스트) 반환, 아니면 (None, None)."""
    for sec in SECTIONS:
        if s == sec:
            return sec, ''
        if s.startswith(sec) and len(s) > len(sec) and s[len(sec)] == ' ':
            return sec, s[len(sec):].strip()
    return None, None

_HDR_RE = re.compile(r'(?<=[.?다함음])(주요 확인사항)')

def explode(line):
    """줄 중간에 글자붙은 섹션헤더가 있으면 분리해 여러 논리줄로 반환."""
    parts = _HDR_RE.split(line)
    return [x for x in parts if x.strip() != '']

def clean(s):
    return s.strip().lstrip(BULLET_MAIN + BULLET_DOT + '·∙▶※ ').strip()

def split_bullets(seg_lines, marker=BULLET_DOT):
    """marker로 시작하는 불릿 단위로 묶고 연속줄을 합친다."""
    items, cur = [], None
    for l in seg_lines:
        s = l.rstrip()
        if s.lstrip().startswith(marker):
            if cur is not None:
                items.append(cur)
            cur = clean(s)
        else:
            if cur is not None:
                cur += ' ' + s.strip()
    if cur is not None:
        items.append(cur)
    return [re.sub(r'\s+', ' ', x).strip() for x in items if x.strip()]

def lead_sentence(text, sub_marks):
    """대주제 본문에서 하위 마커(▶/※/·...) 이전의 리드 문장만 취한다."""
    idxs=[text.find(m) for m in sub_marks if text.find(m)>=0]
    return (text[:min(idxs)] if idxs else text).strip()

def parse_block(lines, start, end):
    buckets={k:[] for k in SECTIONS}
    logical=[]
    for i in range(start, end):
        for piece in explode(lines[i]):
            logical.append(piece)
    cur=None; i=0
    while i<len(logical):
        s=logical[i].strip()
        sec,inline=section_of(s)
        if sec is not None:
            cur=sec
            if inline: buckets[cur].append(inline)
            i+=1; continue
        if cur=='증거자료' and s=='예시':
            i+=1; continue
        if is_noise(logical[i]) or s=='항  목' or re.match(r'^\d+\.\d+\.\d+\s', s):
            i+=1; continue
        if cur is not None: buckets[cur].append(logical[i])
        i+=1
    standard=re.sub(r'\s+',' ',' '.join(x.strip() for x in buckets['인증기준'])).strip()
    standard=re.sub(r'\s*안내서\s*$','',standard).strip()
    checkpoints=split_bullets(buckets['주요 확인사항'], BULLET_DOT)
    laws=split_bullets(buckets['관련 법규'], BULLET_DOT)
    evidence=split_bullets(buckets['증거자료'], BULLET_DOT)
    sd=buckets['세부 설명']
    if any(l.lstrip().startswith(BULLET_MAIN) for l in sd):
        main=BULLET_MAIN; subs=(chr(0x25b6),chr(0x203b),BULLET_DOT,chr(0xf0a7))
    else:
        main=BULLET_DOT; subs=(chr(0x25b6),chr(0x203b),chr(0xf0a7))
    expl=[lead_sentence(t,subs) for t in split_bullets(sd, main)]
    expl=[e for e in expl if len(e)>8]
    return dict(standard=standard, checkpoints=checkpoints,
                related_laws=laws, evidence=evidence, explanation=expl)

def sanitize_name(nm):
    nm=nm.strip()
    nm=re.sub(r'\s+[가-힣]$','',nm)  # 끝의 사이드바 단일음절(예 ' 운') 제거
    return nm.strip()

def main():
    code = sys.argv[1] if len(sys.argv) > 1 else '2.1.1'
    lines = open(RAW, encoding='utf-8').read().splitlines()
    cases, by = load_cases()
    codes = [c['code'] for c in cases]
    starts = find_block_starts(lines, codes)
    ordered = sorted(starts.items(), key=lambda kv: kv[1])
    idxmap = {c: n for n, (c, _) in enumerate(ordered)}
    print('본문 블록 발견:', len(starts), '/', len(codes))
    miss = [c for c in codes if c not in starts]
    if miss:
        print('미발견:', miss)
    if code not in starts:
        print('!! 대상 코드 본문 미발견:', code); return
    n = idxmap[code]
    start = ordered[n][1]
    end = ordered[n + 1][1] if n + 1 < len(ordered) else len(lines)
    fields = parse_block(lines, start, end)
    info = by[code]
    print('\n===== %s %s (page %s) =====' % (code, sanitize_name(info['name']), info.get('page')))
    print('\n[인증기준]\n', fields['standard'])
    print('\n[주요 확인사항] (%d)' % len(fields['checkpoints']))
    for c in fields['checkpoints']:
        print(' -', c)
    print('\n[세부 설명 대주제] (%d)' % len(fields['explanation']))
    for c in fields['explanation']:
        print(' -', c)
    print('\n[증거자료] (%d)' % len(fields['evidence']))
    for c in fields['evidence']:
        print(' -', c)
    print('\n[관련 법규] (%d)' % len(fields['related_laws']))
    for c in fields['related_laws']:
        print(' -', c)
    print('\n[결함사례(첨부)] (%d)' % len(info['cases']))
    for c in info['cases']:
        print(' -', c['text'].strip())

if __name__ == '__main__':
    main()
