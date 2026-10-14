#!/usr/bin/env python3
"""Meldet alle Seiten aus der Live-Sitemap per IndexNow an Bing & Co. (Bing, Ecosia, DuckDuckGo-Ergebnisse, Yandex …).

Google nutzt IndexNow nicht – dort helfen Sitemap und Search Console. Läuft nach jedem Deploy im GitHub-Workflow;
ein Fehler bricht nichts ab. Aufruf: python tools/indexnow.py
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402


def main():
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    basis = build.basis_url(cfg)
    if "localhost" in basis:
        raise SystemExit("Nur für die echte Adresse (GITHUB_REPOSITORY setzen).")
    sitemap = urllib.request.urlopen(f"{basis}/sitemap.xml", timeout=30).read().decode("utf-8")
    urls = re.findall(r"<loc>([^<]+)</loc>", sitemap)
    daten = {"host": urlsplit(basis).netloc, "key": build.INDEXNOW_KEY,
             "keyLocation": f"{basis}/{build.INDEXNOW_KEY}.txt", "urlList": urls}
    anfrage = urllib.request.Request("https://api.indexnow.org/indexnow", data=json.dumps(daten).encode("utf-8"),
                                     headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(anfrage, timeout=30) as antwort:
            print(f"IndexNow: {len(urls)} Seiten gemeldet (HTTP {antwort.status})")
    except urllib.error.HTTPError as fehler:
        print(f"IndexNow: HTTP {fehler.code} – {fehler.read().decode('utf-8', 'replace')[:200]}")


if __name__ == "__main__":
    main()
