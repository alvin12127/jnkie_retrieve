#!/usr/bin/env python3
# jnkie_retrieve.py — 공개 배포된 JNKIE 스크립트의 로더 체인을 순서대로 내려받는 도구.


import argparse
import hashlib
import re
import sys
import urllib.error
import urllib.request

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "Roblox/WinInet RobloxApp/0.0.0.0 (GlobalDist; RobloxDirectDownload)"
)

DELIVERY_RE = re.compile(
    r"https://[^\s\"')]+/api/v1/luascripts/"
    r"(?:delivery|public)/([0-9a-fA-F]{64})((?:[/?][^\s\"')]*)?)"
)
SIGNED_URL_RE = re.compile(r"^https://\S+$")

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def http_get(url, headers=None):
    h = {"User-Agent": DEFAULT_UA}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h, method="GET")
    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()

def http_post(url, body, headers=None):
    h = {"User-Agent": DEFAULT_UA}
    if headers:
        h.update(headers)
    data = body.encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()

def get_header(headers, name):
    for k, v in headers.items():
        if k.lower() == name.lower():
            return v
    return None

def main():
    ap = argparse.ArgumentParser(description="Retrieve a JNKIE-protected Lua script.")
    ap.add_argument("loader_url", help="public loader URL (CDN or /public/<hash>/download)")
    ap.add_argument("--key", default="KEYLESS",
                    help='SCRIPT_KEY to POST. Default "KEYLESS" is what public/open '
                         'scripts expect - keep it unless you were given a real key.')
    ap.add_argument("--out", default=None, help="output .lua path (default: <hash>.lua)")
    ap.add_argument("--referer", default=None, help="optional Referer header")
    ap.add_argument("--debug", action="store_true", help="print every HTTP hop")
    args = ap.parse_args()

    hdrs = {"Referer": args.referer} if args.referer else None

    print(f"[*] GET loader: {args.loader_url}")
    status, headers, body = http_get(args.loader_url, hdrs)
    print(f"[*] {status}  {len(body)} bytes")
    if status != 200 or not body:
        print("[!] loader fetch failed", file=sys.stderr)
        sys.exit(1)

    text = body.decode("utf-8", "replace")

    m = re.search(r"/([0-9a-fA-F]{64})\.lua(?:\?|$)", args.loader_url)
    if m:
        want = m.group(1).lower()
        got = hashlib.sha256(body).hexdigest()
        ok = want == got
        print(f"[*] content-address: {'OK' if ok else 'MISMATCH'}")
        print(f"    expected {want}")
        print(f"    actual   {got}")

    dm = DELIVERY_RE.search(text)
    if not dm:
        print("[!] no delivery endpoint found; saving body as-is.")
        out = args.out or "downloaded.lua"
        with open(out, "wb") as f:
            f.write(body)
        print(f"[+] wrote {out}")
        return

    script_hash = dm.group(1)
    delivery_url = dm.group(0)
    print(f"[*] delivery: {delivery_url}")
    print(f"[*] script hash: {script_hash}")

    print(f"[*] POST key ({args.key!r}) ...")
    status, headers, body = http_post(
        delivery_url, args.key,
        {"Content-Type": "text/plain"},
    )
    if args.debug:
        print(f"[*] {status} {headers!r}")
    print(f"[*] delivery response: {status}")

    if status in (400, 401, 403):
        msg = body.decode("utf-8", "replace")
        print(f"[!] denied: {msg}", file=sys.stderr)
        sys.exit(2)

    payload = None
    if status == 200 and body.strip() and body.decode("utf-8", "replace").strip().startswith("https://"):
        signed = body.decode("utf-8", "replace").strip()
        print(f"[*] signed URL: {signed}")
        s2, h2, b2 = http_get(signed, hdrs)
        print(f"[*] {s2}  {len(b2)} bytes")
        payload = b2
    elif status in (302, 303):
        loc = get_header(headers, "Location")
        print(f"[*] redirect -> {loc}")
        s2, h2, b2 = http_get(loc, hdrs)
        print(f"[*] {s2}  {len(b2)} bytes")
        payload = b2
    elif status == 200:
        payload = body

    if not payload:
        print("[!] no payload retrieved", file=sys.stderr)
        sys.exit(1)

    out = args.out or f"{script_hash}.lua"
    with open(out, "wb") as f:
        f.write(payload)
    print(f"[+] wrote {out} ({len(payload)} bytes)")
    print(f"[+] sha256 {hashlib.sha256(payload).hexdigest()}")

if __name__ == "__main__":
    main()
