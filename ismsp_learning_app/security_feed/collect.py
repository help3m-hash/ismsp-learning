#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""보안 이슈 수집·분류 → security_issues.json 생성.

수집: 국내 RSS(보안뉴스 등) + 해외 NVD CVE API.
분류: keywords.json 기준 태깅, 심각도(CVSS/휴리스틱) 산정.
요약: 원문 복제를 피하기 위해 제목 기반 한 줄 요약(개인 학습용). Claude Code 루틴으로
      돌릴 경우 이 결과의 summary를 Claude가 패러프레이즈로 개선할 수 있음.

사용: python security_feed/collect.py [--days N] [--max M]
출력: security_feed/security_issues.json
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
KST = dt.timezone(dt.timedelta(hours=9))
UA = {"User-Agent": "Mozilla/5.0 (security-feed-collector)"}

# 국내/벤더 RSS (실패 시 자동 스킵). 필요에 맞게 추가/삭제.
RSS_FEEDS = [
    ("보안뉴스", "https://www.boannews.com/media/news_rss.xml"),
    ("데일리시큐", "https://www.dailysecu.com/rss/allArticle.xml"),
]
# 해외: NVD CVE API 2.0 (최근 발행 CVE)
NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def clean(text):
    text = re.sub(r"<[^>]+>", "", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def load_keywords():
    data = json.load(open(os.path.join(HERE, "keywords.json"), encoding="utf-8"))
    return data["keywords"]


def tag_keywords(text, kw):
    tags = []
    low = text.lower()
    for k in kw:
        for m in k["match"]:
            if m.lower() in low:
                tags.append(k["tag"])
                break
    return tags


def summarize(title):
    """원문 복제 회피용 간결 요약(제목 정규화). 루틴에서 Claude가 개선 가능."""
    t = clean(title)
    return t[:120]


def decode_xml(b):
    """EUC-KR/CP949 등 비UTF-8 RSS를 안전하게 유니코드 XML로 변환(인코딩 선언 제거)."""
    enc = "utf-8"
    m = re.search(rb'encoding=["\']([\w-]+)["\']', b[:200])
    if m:
        enc = m.group(1).decode("ascii", "ignore")
    try:
        s = b.decode(enc, errors="replace")
    except LookupError:
        s = b.decode("utf-8", errors="replace")
    s = re.sub(r"<\?xml[^>]*\?>", "", s, count=1)
    return s.lstrip()


def parse_rss(source, xml_bytes, kw, since):
    out = []
    root = ET.fromstring(decode_xml(xml_bytes))
    for item in root.iter("item"):
        title = clean(item.findtext("title", ""))
        link = (item.findtext("link", "") or "").strip()
        desc = clean(item.findtext("description", ""))
        pub = item.findtext("pubDate", "") or ""
        published = parse_date(pub)
        if not title or not link:
            continue
        if published and published < since:
            continue
        text = title + " " + desc
        tags = tag_keywords(text, kw)
        out.append({
            "title": title,
            "summary": summarize(title),
            "source": source,
            "url": link,
            "published": (published or dt.date.today()).isoformat(),
            "keywords": tags,
            "severity": severity_from_text(text),
        })
    return out


def parse_date(s):
    s = s.strip()
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def severity_from_text(text):
    low = text.lower()
    if any(w in low for w in ["제로데이", "긴급", "rce", "원격코드실행", "zero-day", "actively exploited"]):
        return "높음"
    if any(w in text for w in ["취약점", "유출", "랜섬웨어", "침해"]):
        return "중간"
    return "정보"


def severity_from_cvss(score):
    if score is None:
        return "정보"
    if score >= 9.0:
        return "긴급"
    if score >= 7.0:
        return "높음"
    if score >= 4.0:
        return "중간"
    return "낮음"


def fetch_nvd(kw, since, limit=15):
    out = []
    start = since.strftime("%Y-%m-%dT00:00:00.000")
    end = dt.datetime.now(KST).strftime("%Y-%m-%dT23:59:59.000")
    url = f"{NVD_API}?pubStartDate={start}&pubEndDate={end}&resultsPerPage={limit}"
    data = json.loads(fetch(url, timeout=30))
    for v in data.get("vulnerabilities", []):
        c = v.get("cve", {})
        cid = c.get("id", "")
        descs = c.get("descriptions", [])
        en = next((d["value"] for d in descs if d.get("lang") == "en"), "")
        score = None
        metrics = c.get("metrics", {})
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            if metrics.get(key):
                score = metrics[key][0]["cvssData"]["baseScore"]
                break
        title = f"{cid} 취약점 (CVSS {score if score is not None else 'N/A'})"
        text = cid + " " + en
        tags = list(dict.fromkeys(["취약점·CVE"] + tag_keywords(text, kw)))
        out.append({
            "title": title,
            "summary": f"{cid}: 신규 등록된 취약점. CVSS 기준 {severity_from_cvss(score)} 등급.",
            "source": "NVD",
            "url": f"https://nvd.nist.gov/vuln/detail/{cid}",
            "published": (c.get("published", "")[:10] or dt.date.today().isoformat()),
            "keywords": tags,
            "severity": severity_from_cvss(score),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=2, help="최근 N일")
    ap.add_argument("--max", type=int, default=40, help="최대 항목 수")
    args = ap.parse_args()

    kw = load_keywords()
    since = dt.date.today() - dt.timedelta(days=args.days)
    issues, errors = [], []

    for source, url in RSS_FEEDS:
        try:
            issues += parse_rss(source, fetch(url), kw, since)
        except Exception as e:  # 피드 하나 실패해도 계속
            errors.append(f"{source}: {e}")

    try:
        issues += fetch_nvd(kw, since)
    except Exception as e:
        errors.append(f"NVD: {e}")

    # 중복 제거(url 기준) + 최신순 + 상한
    seen, dedup = set(), []
    for it in sorted(issues, key=lambda x: x["published"], reverse=True):
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        dedup.append(it)
    dedup = dedup[: args.max]

    # id 부여
    today = dt.date.today().strftime("%Y%m%d")
    for i, it in enumerate(dedup, 1):
        it["id"] = f"{today}-{i:03d}"

    result = {
        "updated_at": dt.datetime.now(KST).isoformat(timespec="seconds"),
        "count": len(dedup),
        "issues": dedup,
    }
    out_path = os.path.join(HERE, "security_issues.json")
    json.dump(result, open(out_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"수집 {len(dedup)}건 → {out_path}")
    if errors:
        print("경고(스킵된 피드):", *errors, sep="\n  - ", file=sys.stderr)


if __name__ == "__main__":
    main()
