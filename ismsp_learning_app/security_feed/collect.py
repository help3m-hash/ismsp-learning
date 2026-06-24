#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
뉴스·이슈 수집·분류 스크립트  (ISMS-P Learning 앱 "오늘의 이슈" 연동 루틴 엔진)

전 분야(정치·국제 / 사회·경제 / 주식·증시 / 스포츠·문화 / IT·과학 / 보안) 뉴스를
RSS로 수집, 분야 분류 + 제목장사(클릭베이트) 필터 + 중복 제거 후 JSON 생성.

출처 계층(tier): 1차(정부 보도자료) · 통신 · 증권 · 종합 · 보안
※ 관점(perspective)은 출처별 라벨 칸만 제공하며 임의로 단정하지 않음(사용자 큐레이션).

사용법:
    pip install feedparser
    python collect.py --days 2 --max 90
"""
import argparse
import hashlib
import html
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
DEFAULT_OUT = os.path.join(HERE, "security_issues.json")  # 파일명은 호환 위해 유지

DOMAINS = ["정치·국제", "사회·경제", "주식·증시", "스포츠·문화", "IT·과학", "보안"]

# ── 출처 (domain=None 이면 기사별 키워드로 분야 자동분류) ───────────────
SOURCES = [
    # 1차 — 정부 보도자료
    {"name": "정책브리핑", "url": "https://www.korea.kr/rss/policy.xml", "region": "국내", "tier": "1차", "domain": None, "perspective": ""},
    # 통신사 — 연합뉴스 분야별
    {"name": "연합뉴스", "url": "https://www.yna.co.kr/rss/news.xml",         "region": "국내", "tier": "통신", "domain": None,        "perspective": ""},
    {"name": "연합뉴스", "url": "https://www.yna.co.kr/rss/politics.xml",     "region": "국내", "tier": "통신", "domain": "정치·국제",  "perspective": ""},
    {"name": "연합뉴스", "url": "https://www.yna.co.kr/rss/international.xml", "region": "국내", "tier": "통신", "domain": "정치·국제",  "perspective": ""},
    {"name": "연합뉴스", "url": "https://www.yna.co.kr/rss/economy.xml",      "region": "국내", "tier": "통신", "domain": None,        "perspective": ""},
    {"name": "연합뉴스", "url": "https://www.yna.co.kr/rss/industry.xml",     "region": "국내", "tier": "통신", "domain": None,        "perspective": ""},
    {"name": "연합뉴스", "url": "https://www.yna.co.kr/rss/society.xml",      "region": "국내", "tier": "통신", "domain": "사회·경제",  "perspective": ""},
    {"name": "연합뉴스", "url": "https://www.yna.co.kr/rss/sports.xml",       "region": "국내", "tier": "통신", "domain": "스포츠·문화", "perspective": ""},
    {"name": "연합뉴스", "url": "https://www.yna.co.kr/rss/culture.xml",      "region": "국내", "tier": "통신", "domain": "스포츠·문화", "perspective": ""},
    # 주식·증시 전용
    {"name": "연합뉴스",    "url": "https://www.yna.co.kr/rss/market.xml",                  "region": "국내", "tier": "증권", "domain": "주식·증시", "perspective": ""},
    {"name": "매일경제",    "url": "https://www.mk.co.kr/rss/50200011/",                    "region": "국내", "tier": "증권", "domain": "주식·증시", "perspective": ""},
    {"name": "머니투데이",  "url": "https://rss.mt.co.kr/mt_news_stock.xml",                "region": "국내", "tier": "증권", "domain": "주식·증시", "perspective": ""},
    {"name": "파이낸셜뉴스", "url": "https://www.fnnews.com/rss/r20/fn_realnews_stock.xml", "region": "국내", "tier": "증권", "domain": "주식·증시", "perspective": ""},
    # 종합지 — 분야 자동분류
    {"name": "한겨레",     "url": "https://www.hani.co.kr/rss/",                       "region": "국내", "tier": "종합", "domain": None, "perspective": ""},
    {"name": "경향신문",   "url": "https://www.khan.co.kr/rss/rssdata/total_news.xml", "region": "국내", "tier": "종합", "domain": None, "perspective": ""},
    {"name": "오마이뉴스", "url": "http://rss.ohmynews.com/rss/ohmynews.xml",          "region": "국내", "tier": "종합", "domain": None, "perspective": ""},
    {"name": "프레시안",   "url": "https://www.pressian.com/api/v3/site/rss/news",     "region": "국내", "tier": "종합", "domain": None, "perspective": ""},
    {"name": "서울신문",   "url": "https://www.seoul.co.kr/xml/rss/rss_politics.xml",  "region": "국내", "tier": "종합", "domain": None, "perspective": ""},
    # 보안 전문 (유지)
    {"name": "보안뉴스",       "url": "https://www.boannews.com/media/news_rss.xml?mkind=1", "region": "국내", "tier": "보안", "domain": "보안", "perspective": ""},
    {"name": "데일리시큐",     "url": "https://www.dailysecu.com/rss/allArticle.xml",        "region": "국내", "tier": "보안", "domain": "보안", "perspective": ""},
    {"name": "The Hacker News", "url": "https://feeds.feedburner.com/TheHackersNews",        "region": "해외", "tier": "보안", "domain": "보안", "perspective": ""},
    {"name": "BleepingComputer","url": "https://www.bleepingcomputer.com/feed/",            "region": "해외", "tier": "보안", "domain": "보안", "perspective": ""},
]

# ── 분야 자동분류 키워드 (broad 피드용) — 위에서부터 우선 매칭 ──────────
DOMAIN_KEYWORDS = [
    ("보안", ["해킹", "보안", "취약점", "랜섬", "CVE", "침해", "악성코드", "피싱", "정보유출",
             "DDoS", "사이버", "정보보호", "개인정보 유출", "제로데이", "악성"]),
    ("주식·증시", ["증시", "코스피", "코스닥", "주가", "주식", "상장", "공모주", "IPO", "배당",
                 "공매도", "나스닥", "다우", "S&P", "시가총액", "시총", "순매수", "증권", "종목",
                 "ETF", "펀드", "환율", "상한가", "하한가"]),
    ("스포츠·문화", ["야구", "축구", "손흥민", "올림픽", "월드컵", "골프", "배구", "농구", "프로야구",
                   "영화", "드라마", "K팝", "케이팝", "공연", "전시", "연예", "배우", "가수",
                   "아이돌", "콘서트", "미술", "스포츠"]),
    ("IT·과학", ["AI", "인공지능", "반도체", "과학", "우주", "위성", "네이버", "카카오", "삼성전자",
               "애플", "구글", "앱", "스타트업", "로봇", "배터리", "전기차", "양자", "바이오", "IT"]),
    ("정치·국제", ["대통령", "국회", "여당", "야당", "민주당", "국민의힘", "외교", "정상회담", "북한",
                 "미국", "중국", "일본", "유엔", "국제", "전쟁", "선거", "장관", "대통령실",
                 "총리", "외교부", "안보"]),
    ("사회·경제", ["경제", "금융", "물가", "기업", "산업", "고용", "노동", "복지", "법원", "검찰",
                 "경찰", "교육", "환경", "날씨", "사고", "재판", "수출", "부동산"]),
]

# ── 제목장사(클릭베이트) 필터 ───────────────────────────────────────────
CLICKBAIT_WORDS = [
    "충격", "경악", "발칵", "헉", "소름", "깜짝", "대박", "이럴수가", "이럴 수가",
    "알고보니", "알고 보니", "결국", "충격적", "화들짝", "난리", "터졌다", "발칵 뒤집",
    "눈물", "오열", "폭로", "막장", "참담", "분노 폭발",
]

_ENTITY_FIX = {"quot;": '"', "middot;": "·", "hellip;": "…", "amp;": "&",
               "nbsp;": " ", "lt;": "<", "gt;": ">", "ldquo;": '"', "rdquo;": '"',
               "lsquo;": "'", "rsquo;": "'", "apos;": "'"}


def clean_text(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    for k, v in _ENTITY_FIX.items():
        s = s.replace(k, v)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_clickbait(title):
    if any(w in title for w in CLICKBAIT_WORDS):
        return True
    if title.count("?") + title.count("!") >= 3:
        return True
    return False


def make_summary(entry, limit=120):
    raw = clean_text(getattr(entry, "summary", "") or getattr(entry, "description", ""))
    return raw[:limit].rstrip() + "…" if len(raw) > limit else raw


def classify_domain(text):
    low = text.lower()
    for dom, kws in DOMAIN_KEYWORDS:
        if any(k.lower() in low for k in kws):
            return dom
    return "사회·경제"


def topic_tags(text):
    tags, low = [], text.lower()
    for dom, kws in DOMAIN_KEYWORDS:
        for k in kws:
            if k.lower() in low:
                tags.append(k)
                break
    return tags[:2]


def parse_published(entry):
    t = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if t:
        return datetime(*t[:6], tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=9))).isoformat()
    return None


def entry_id(link, title):
    return hashlib.md5((link or title).encode("utf-8")).hexdigest()[:12]


def collect(days=2):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    seen, issues, dropped = set(), [], 0

    for src in SOURCES:
        try:
            feed = feedparser.parse(src["url"])
        except Exception as e:
            print(f"[경고] {src['name']} 수집 실패: {e}", file=sys.stderr)
            continue
        if getattr(feed, "bozo", 0) and not feed.entries:
            print(f"[경고] {src['name']} ({src['url']}) 비어있음", file=sys.stderr)
            continue

        for e in feed.entries:
            title = clean_text(getattr(e, "title", ""))
            link = getattr(e, "link", "")
            if not title or not link:
                continue
            if is_clickbait(title):
                dropped += 1
                continue

            pub_parsed = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
            if pub_parsed and datetime(*pub_parsed[:6], tzinfo=timezone.utc) < cutoff:
                continue

            uid = entry_id(link, title)
            if uid in seen:
                continue
            seen.add(uid)

            summary = make_summary(e)
            text = f"{title} {summary}"
            domain = src["domain"] or classify_domain(text)
            issues.append({
                "id": uid,
                "title": title,
                "summary": summary,
                "source": src["name"],
                "region": src["region"],
                "tier": src["tier"],
                "domain": domain,
                "url": link,
                "published": parse_published(e),
                "keywords": topic_tags(text),
            })

    issues.sort(key=lambda x: x["published"] or "", reverse=True)
    return issues, dropped


def build_output(issues):
    return {
        "updated_at": datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds"),
        "count": len(issues),
        "domains": DOMAINS,
        "issues": issues,
    }


def main():
    ap = argparse.ArgumentParser(description="뉴스·이슈 RSS 수집·분류")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--days", type=int, default=2)
    ap.add_argument("--max", type=int, default=90)
    args = ap.parse_args()

    issues, dropped = collect(days=args.days)
    issues = issues[: args.max]
    json.dump(build_output(issues), open(args.out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    print(f"수집 {len(issues)}건 (제목장사 {dropped}건 제외)  →  {args.out}")
    print("  분야:", dict(Counter(i["domain"] for i in issues)))
    print("  지역:", dict(Counter(i["region"] for i in issues)))


if __name__ == "__main__":
    main()
