#!/usr/bin/env python3
"""Platzi course lookup for the study-* skills: catalog, course index, class summary.

  platzi.py catalog [--refresh]   JSON [{slug, url}] from the public course sitemap (cached 7 days)
  platzi.py course <slug>         JSON {slug, title, description, level, total_minutes, classes:[...]}
  platzi.py summary <class-url>   the class's written summary, to stdout only

Rules this script enforces (see study-shared/references/videos.md): honest User-Agent, a pause
between requests, retries with backoff, and nothing from Platzi's content is ever written to disk
except titles, durations and URLs. The summary is printed so the model can decide, never saved.
Exit code 3 = Platzi refused or failed after retries: the plan must be generated without videos.
"""
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

BASE = "https://platzi.com"
UA = "study-skills/2 (personal study planner)"
PAUSE = float(os.environ.get("STUDY_PLATZI_PAUSE", "2.5"))
BACKOFF = [float(x) for x in os.environ.get("STUDY_PLATZI_BACKOFF", "5,15").split(",") if x != ""]
CACHE = Path(os.environ.get("STUDY_HOME", Path.home() / ".study")) / "cache" / "platzi"
CACHE_DAYS = 7
_last_request = [0.0]


# ------------------------------------------------------------------ parsing
def _text(fragment):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def _visible(page):
    return re.sub(r"<script.*?</script>|<style.*?</style>", " ", page, flags=re.S)


def parse_catalog(xml):
    rows, seen = [], set()
    for url, slug in re.findall(r"<loc>\s*(https://platzi\.com/cursos/([a-z0-9-]+)/)\s*</loc>", xml):
        if slug not in seen:
            seen.add(slug)
            rows.append({"slug": slug, "url": url})
    return rows


def parse_course(page, slug):
    title = _text((re.search(r"<title>(.*?)</title>", page, re.S) or [None, ""])[1])
    title = re.sub(r"\s*[-|]\s*Platzi\s*$", "", title)
    desc = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', page)
    level = re.search(r"Nivel (Básico|Intermedio|Avanzado)", _text(_visible(page)))
    classes, seen = [], set()
    pattern = r'href="/cursos/%s/([a-z0-9-]+)/"[^>]*>(.*?)</a>' % re.escape(slug)
    for cslug, inner in re.findall(pattern, page, re.S):
        m = re.match(r"^(\d+)\s+(.*?)\s+(\d{1,3}):(\d{2})\s*min", _text(inner))
        if m and cslug not in seen:
            seen.add(cslug)
            secs = int(m.group(3)) * 60 + int(m.group(4))
            classes.append({"n": int(m.group(1)), "title": m.group(2),
                            "duration": f"{m.group(3)}:{m.group(4)}", "minutes": round(secs / 60, 1),
                            "url": f"{BASE}/cursos/{slug}/{cslug}/"})
    classes.sort(key=lambda c: c["n"])
    return {"slug": slug, "url": f"{BASE}/cursos/{slug}/", "title": title,
            "description": html.unescape(desc.group(1)) if desc else "",
            "level": level.group(1) if level else None,
            "total_minutes": round(sum(c["minutes"] for c in classes), 1), "classes": classes}


def parse_summary(page):
    """Text of the class summary block; '' if Platzi changed the markup (decide by title then)."""
    v = _visible(page)
    start = v.find("Resources__summary")
    if start == -1:
        return ""
    ends = [e for e in (v.find("</section>", start), v.find("<footer", start)) if e != -1]
    block = v[start:min(ends) if ends else start + 60000]
    parts = [_text(x) for x in re.findall(r"<(?:p|li|h2|h3)[^>]*>(.*?)</(?:p|li|h2|h3)>", block, re.S)]
    return "\n".join(p for p in parts if p)


# ------------------------------------------------------------------ network
def get(url):
    """GET with an honest UA, a pause between requests and backoff on 403/429/503."""
    for attempt, wait in enumerate([0.0] + BACKOFF):
        time.sleep(max(wait, _last_request[0] + PAUSE - time.time(), 0))
        _last_request[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            if e.code not in (403, 429, 503) or attempt == len(BACKOFF):
                fail(f"Platzi answered {e.code} for {url}")
        except Exception as e:  # noqa: BLE001
            if attempt == len(BACKOFF):
                fail(f"could not reach Platzi ({type(e).__name__})")
    fail(f"Platzi refused {url} after retries")


def fail(msg):
    print(f"error: {msg}. Generate the plan without videos and note it in PLAN.md.", file=sys.stderr)
    sys.exit(3)


# ------------------------------------------------------------------ commands
def catalog(refresh=False):
    f = CACHE / "cursos.json"
    if f.exists() and not refresh:
        data = json.loads(f.read_text(encoding="utf-8"))
        if datetime.now() - datetime.fromisoformat(data["fetched"]) < timedelta(days=CACHE_DAYS):
            return data["courses"]
    rows = parse_catalog(get(f"{BASE}/sitemap-cursos.xml"))
    if not rows:
        fail("the course sitemap came back empty or changed format")
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"fetched": datetime.now().isoformat(timespec="seconds"), "courses": rows},
                            ensure_ascii=False), encoding="utf-8")
    return rows


def main():
    args = sys.argv[1:]
    if args[:1] == ["catalog"]:
        print(json.dumps(catalog("--refresh" in args), ensure_ascii=False, indent=1))
    elif args[:1] == ["course"] and len(args) == 2:
        data = parse_course(get(f"{BASE}/cursos/{args[1]}/"), args[1])
        if not data["classes"]:
            fail(f"no classes found for course '{args[1]}' (wrong slug or markup changed)")
        print(json.dumps(data, ensure_ascii=False, indent=1))
    elif args[:1] == ["summary"] and len(args) == 2:
        print(parse_summary(get(args[1])))
    else:
        print(__doc__, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
