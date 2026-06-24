#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
보안/개인정보 이슈 수집·분류 스크립트  (ISMS-P Learning 앱 연동용 루틴 엔진)

동작: RSS 소스 수집 → 키워드 분류 → 중복 제거 → JSON 생성
국내/해외(region) 구분 + 카테고리 목록(categories) 포함.

사용법:
    python collect.py
    python collect.py --out security_issues.json --days 3
    python collect.py --all            # 키워드 미매칭 항목도 포함

필요 패키지: feedparser  (pip install feedparser)

[저작권] 기사 본문 전문을 저장/표시하지 않습니다. 제목 + 자체요약(앞부분 일부) +
원문 링크 + 출처만 다룹니다. 앱 표시 시에도 반드시 원문 링크를 함께 노출합니다.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta

try:
    import feedparser
except ImportError:
    print("feedparser가 필요합니다: pip install feedparser")
    sys.exit(1)

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(HERE, "security_issues.json")

# ============================================================
# 1) 설정 — 여기만 수정하면 됩니다
# ============================================================

RSS_SOURCES = [
    # ── 국내 ──
    {"name": "보안뉴스",          "url": "https://www.boannews.com/media/news_rss.xml?mkind=1", "region": "국내"},
    {"name": "데일리시큐",        "url": "https://www.dailysecu.com/rss/allArticle.xml",         "region": "국내"},
    {"name": "KISA 보호나라",     "url": "https://www.boho.or.kr/kr/rss.do",                      "region": "국내"},
    # ── 해외 ──
    {"name": "The Hacker News",   "url": "https://feeds.feedburner.com/TheHackersNews",           "region": "해외"},
    {"name": "BleepingComputer",  "url": "https://www.bleepingcomputer.com/feed/",                "region": "해외"},
    {"name": "Krebs on Security", "url": "https://krebsonsecurity.com/feed/",                     "region": "해외"},
    {"name": "CISA Advisories",   "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml", "region": "해외"},
]

KEYWORD_CATEGORIES = {
    "ISMS-P·인증": [
        "ISMS", "ISMS-P", "인증", "정보보호 관리체계", "인증심사", "ISO 27001", "ISO 27701",
    ],
    "개인정보보호법·규제": [
        "개인정보", "프라이버시", "privacy", "개인정보보호법", "GDPR", "처리방침",
        "개인정보위", "정보주체", "동의", "가명정보", "CI", "DI", "유출",
    ],
    "취약점·CVE·패치": [
        "취약점", "vulnerability", "CVE", "패치", "patch", "zero-day", "제로데이",
        "exploit", "익스플로잇", "RCE", "권고", "advisory",
    ],
    "랜섬웨어·침해사고": [
        "랜섬웨어", "ransomware", "침해", "해킹", "hack", "breach", "유출사고",
        "malware", "악성코드", "피싱", "phishing", "APT", "DDoS",
    ],
    "금융보안": [
        "금융보안", "전자금융", "FDS", "이상거래", "금융권", "은행", "핀테크",
        "fintech", "financial",
    ],
    "클라우드·AI보안": [
        "클라우드", "cloud", "AWS", "Azure", "AI 보안", "LLM", "쿠버네티스",
        "kubernetes", "컨테이너", "공급망", "supply chain",
    ],
}

SEVERITY_HIGH = ["긴급", "critical", "심각", "제로데이", "zero-day", "RCE", "대규모", "유출"]
SEVERITY_MID = ["주의", "경고", "warning", "high", "취약점", "패치"]


# ============================================================
# 2) 수집·분류 로직 (보통 수정 불필요)
# ============================================================

def clean_text(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def make_summary(entry, limit=120):
    raw = ""
    if getattr(entry, "summary", None):
        raw = clean_text(entry.summary)
    elif getattr(entry, "description", None):
        raw = clean_text(entry.description)
    if len(raw) > limit:
        raw = raw[:limit].rstrip() + "…"
    return raw


def classify(text):
    hits = []
    low = text.lower()
    for cat, kws in KEYWORD_CATEGORIES.items():
        for kw in kws:
            if kw.lower() in low:
                hits.append(cat)
                break
    return hits


def estimate_severity(text):
    low = text.lower()
    if any(k.lower() in low for k in SEVERITY_HIGH):
        return "높음"
    if any(k.lower() in low for k in SEVERITY_MID):
        return "보통"
    return "낮음"


def parse_published(entry):
    t = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if t:
        dt = datetime(*t[:6], tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=9)))
        return dt.isoformat()
    return None


def entry_id(link, title):
    return hashlib.md5((link or title).encode("utf-8")).hexdigest()[:12]


def collect(days=2, only_classified=True):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    seen = set()
    issues = []

    for src in RSS_SOURCES:
        try:
            feed = feedparser.parse(src["url"])
        except Exception as e:
            print(f"[경고] {src['name']} 수집 실패: {e}", file=sys.stderr)
            continue
        if getattr(feed, "bozo", 0) and not feed.entries:
            print(f"[경고] {src['name']} 피드 비어있음/오류", file=sys.stderr)
            continue

        for e in feed.entries:
            title = clean_text(getattr(e, "title", ""))
            link = getattr(e, "link", "")
            if not title or not link:
                continue

            pub_parsed = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
            if pub_parsed:
                pub_dt = datetime(*pub_parsed[:6], tzinfo=timezone.utc)
                if pub_dt < cutoff:
                    continue

            uid = entry_id(link, title)
            if uid in seen:
                continue
            seen.add(uid)

            summary = make_summary(e)
            cls_text = f"{title} {summary}"
            cats = classify(cls_text)
            if only_classified and not cats:
                continue

            issues.append({
                "id": uid,
                "title": title,
                "summary": summary,
                "source": src["name"],
                "region": src["region"],
                "url": link,
                "published": parse_published(e),
                "keywords": cats,
                "severity": estimate_severity(cls_text),
            })

    issues.sort(key=lambda x: x["published"] or "", reverse=True)
    return issues


def build_output(issues):
    return {
        "updated_at": datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds"),
        "count": len(issues),
        "categories": list(KEYWORD_CATEGORIES.keys()),
        "issues": issues,
    }


def main():
    ap = argparse.ArgumentParser(description="보안 이슈 RSS 수집·분류")
    ap.add_argument("--out", default=DEFAULT_OUT, help="출력 JSON 경로")
    ap.add_argument("--days", type=int, default=2, help="최근 N일치 수집 (기본 2)")
    ap.add_argument("--max", type=int, default=60, help="최대 항목 수")
    ap.add_argument("--all", action="store_true", help="키워드 미매칭 항목도 포함")
    args = ap.parse_args()

    issues = collect(days=args.days, only_classified=not args.all)[: args.max]
    output = build_output(issues)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"수집 완료: {len(issues)}건  →  {args.out}")
    cat_count = Counter(c for it in issues for c in it["keywords"])
    reg_count = Counter(it["region"] for it in issues)
    for cat in KEYWORD_CATEGORIES:
        print(f"  - {cat}: {cat_count.get(cat, 0)}건")
    print("  지역:", dict(reg_count))


if __name__ == "__main__":
    main()
