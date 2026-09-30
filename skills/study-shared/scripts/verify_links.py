#!/usr/bin/env python3
"""Verify that URLs really resolve before they are written into a study plan.

Usage:  verify_links.py URL [URL ...]      or      cat urls.txt | verify_links.py
One line per URL:  STATUS CODE URL [-> FINAL_URL]

  OK            2xx, with no redirect or only a cosmetic one (slash, http->https, www)
  REDIRECT      ends on a different page: write FINAL_URL instead, or drop the link
  RATE-LIMITED  429/503 after retries: unverified today, not broken
  BLOCKED       401/403: bot wall or login; unverifiable, not broken
  SPA?          the host answers an invented path with the same <title>: a 200 proves nothing
  BAD           anything else (404, 5xx, network error)

Exit code: 0 all OK · 1 any BAD · 2 no BAD but something is not OK.
Why: a plan with a dead or wrong link teaches nothing and erodes trust in every other link.
"""
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

UA = "study-skills/2 (link check)"
BACKOFF = [float(x) for x in os.environ.get("STUDY_LINK_BACKOFF", "2,6").split(",") if x != ""]
TITLE = re.compile(rb"<title[^>]*>(.*?)</title>", re.I | re.S)


class Follow308(urllib.request.HTTPRedirectHandler):
    """Python < 3.11 refuses to follow 308; treat it like 307 (same method, new URL)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req, fp, 307 if code == 308 else code, msg, headers, newurl)

    http_error_308 = urllib.request.HTTPRedirectHandler.http_error_302


OPENER = urllib.request.build_opener(Follow308)


def fetch(url, timeout=20):
    """Return (code, final_url, title). code is an int, or 'ERR:<Exception>' on network failure."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with OPENER.open(req, timeout=timeout) as r:
            m = TITLE.search(r.read(200_000))
            return r.status, r.geturl(), (m.group(1).strip() if m else b"")
    except urllib.error.HTTPError as e:
        return e.code, e.geturl() or url, b""
    except Exception as e:  # noqa: BLE001 - any network failure is a BAD link, reported by name
        return f"ERR:{type(e).__name__}", url, b""


def fetch_with_retry(url):
    code, final, title = fetch(url)
    for wait in BACKOFF:
        if code not in (429, 503):
            break
        time.sleep(wait)
        code, final, title = fetch(url)
    return code, final, title


def canonical(url):
    p = urllib.parse.urlsplit(url)
    host = p.netloc.lower()
    host = host[4:] if host.startswith("www.") else host
    return host, (p.path.rstrip("/") or "/"), p.query


_probes = {}


def probe_title(url):
    """Title the host returns for a path that cannot exist, or None if it answers non-200."""
    p = urllib.parse.urlsplit(url)
    key = (p.scheme, p.netloc)
    if key not in _probes:
        code, _, title = fetch(f"{p.scheme}://{p.netloc}/__study_probe_{uuid.uuid4().hex[:10]}")
        _probes[key] = title if code == 200 else None
    return _probes[key]


def classify(url):
    code, final, title = fetch_with_retry(url)
    if isinstance(code, str):
        return "BAD", code, None
    if code in (429, 503):
        return "RATE-LIMITED", code, None
    if code in (401, 403):
        return "BLOCKED", code, None
    if not 200 <= code < 300:
        return "BAD", code, (final if final != url else None)
    if canonical(url) != canonical(final):
        return "REDIRECT", code, final
    fake = probe_title(final)
    if fake is not None and title == fake:
        return "SPA?", code, None
    return "OK", code, None


def main():
    urls = [a for a in sys.argv[1:] if a.strip()] or [l.strip() for l in sys.stdin if l.strip()]
    worst = 0
    for u in urls:
        status, code, final = classify(u)
        print(f"{status:<12} {code} {u}" + (f" -> {final}" if final else ""))
        worst = max(worst, 1 if status == "BAD" else (0 if status == "OK" else 0.5))
    sys.exit(1 if worst == 1 else (2 if worst else 0))


if __name__ == "__main__":
    main()
