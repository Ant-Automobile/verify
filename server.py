#!/usr/bin/env python3
import argparse
import base64
import fcntl
import hashlib
import json
import os
import re
import secrets
import sys
import tempfile
from datetime import datetime
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

BASE = "/var/lib/ant-verify"
REG = BASE + "/registry.json"
HOST = "https://verify.antautomobile.org"
API_HOST = "api.antautomobile.org"
API_STATUS = {"gecerli": "valid", "iptal": "revoked", "yenilendi": "superseded"}
LISTEN = ("127.0.0.1", 8089)
ALPHA = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
NO_RE = re.compile(r"^ANT-[0-9A-HJKMNP-TV-Z]{4}(-[0-9A-HJKMNP-TV-Z]{4}){3}$")
TZ = ZoneInfo("Europe/Istanbul")

ICON_LIGHT = "data:image/webp;base64,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"
ICON_DARK = "data:image/webp;base64,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"

SCRIPT = r"""
const box=document.getElementById('cmp'),inp=document.getElementById('f'),out=document.getElementById('sonuc');
const want=box.dataset.sha;
async function kontrol(file){
  out.className='sonuc';out.textContent='Karşılaştırılıyor…';
  try{
    const h=await crypto.subtle.digest('SHA-256',await file.arrayBuffer());
    const hex=[...new Uint8Array(h)].map(b=>b.toString(16).padStart(2,'0')).join('');
    if(hex===want){out.className='sonuc ok';out.textContent='✓ '+file.name+' düzenlediğimiz belgeyle birebir aynı.';}
    else{out.className='sonuc no';out.textContent='✗ '+file.name+' düzenlediğimiz belgeyle aynı değil. Dosya değiştirilmiş ya da farklı bir belge olabilir.';}
  }catch(e){out.className='sonuc no';out.textContent='Dosya okunamadı.';}
}
inp.addEventListener('change',()=>{if(inp.files[0])kontrol(inp.files[0]);});
['dragenter','dragover'].forEach(t=>box.addEventListener(t,e=>{e.preventDefault();box.classList.add('uzerinde');}));
['dragleave','drop'].forEach(t=>box.addEventListener(t,e=>{e.preventDefault();box.classList.remove('uzerinde');}));
box.addEventListener('drop',e=>{const f=e.dataTransfer.files[0];if(f)kontrol(f);});
"""

SCRIPT_ARA = r"""
const box=document.getElementById('ara'),inp=document.getElementById('f'),out=document.getElementById('sonuc');
async function ara(file){
  out.className='sonuc';out.textContent='Dosyanın özeti hesaplanıyor…';
  try{
    const h=await crypto.subtle.digest('SHA-256',await file.arrayBuffer());
    location.href='/?sha='+[...new Uint8Array(h)].map(b=>b.toString(16).padStart(2,'0')).join('');
  }catch(e){out.className='sonuc no';out.textContent='Dosya okunamadı.';}
}
inp.addEventListener('change',()=>{if(inp.files[0])ara(inp.files[0]);});
['dragenter','dragover'].forEach(t=>box.addEventListener(t,e=>{e.preventDefault();box.classList.add('uzerinde');}));
['dragleave','drop'].forEach(t=>box.addEventListener(t,e=>{e.preventDefault();box.classList.remove('uzerinde');}));
box.addEventListener('drop',e=>{const f=e.dataTransfer.files[0];if(f)ara(f);});
"""
CSP = ("default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src "
       + " ".join("'sha256-%s'" % base64.b64encode(hashlib.sha256(x.encode()).digest()).decode()
                  for x in (SCRIPT, SCRIPT_ARA))
       + "; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")

STYLE = """
:root{--bg:#edefee;--card:#f6f7f6;--ink:#111513;--ink2:#4a534f;--line:#cfd5d2;--accent:#dc4219;--accent-ink:#fff;--ok:#1d7a45;--no:#b3330e}
@media(prefers-color-scheme:dark){:root{--bg:#0b0e0d;--card:#101412;--ink:#e7ebe9;--ink2:#a9b3af;--line:#252c29;--accent:#ff6436;--accent-ink:#0b0e0d;--ok:#5fd08f;--no:#ff875f}}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;padding:16px}
main{width:100%;max-width:520px;background:var(--card);border:1px solid var(--line);border-radius:2px;padding:30px 28px}
.logo{display:block;width:44px;height:44px;margin:0 0 20px;background:url(@@L@@) center/contain no-repeat}
@media(prefers-color-scheme:dark){.logo{background-image:url(@@D@@)}}
.durum{margin:0 0 4px;font-size:21px;font-weight:650;letter-spacing:-.01em}
.durum.ok{color:var(--ok)}.durum.no{color:var(--no)}
.alt{margin:0 0 20px;color:var(--ink2);font-size:14px}
dl{display:grid;grid-template-columns:auto 1fr;gap:7px 16px;margin:0 0 22px;font-size:15px}
dt{color:var(--ink2)}dd{margin:0;font-weight:550;overflow-wrap:anywhere}
.no-k{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-weight:600;letter-spacing:.02em;white-space:nowrap}
@media(max-width:480px){main{padding:24px 18px}dl{grid-template-columns:1fr;gap:0}dd{margin-bottom:9px}}
a.btn{display:block;text-align:center;padding:11px 12px;color:var(--accent-ink);background:var(--accent);border-radius:2px;text-decoration:none;font-weight:600}
a.btn:hover{filter:brightness(1.07)}
.cmp{margin-top:22px;padding-top:18px;border-top:1px solid var(--line)}
.cmp h2{margin:0 0 4px;font-size:15px;font-weight:650}
.cmp p{margin:0 0 12px;color:var(--ink2);font-size:13.5px}
.cmp label{display:block;padding:16px 12px;text-align:center;border:1px dashed var(--line);border-radius:2px;cursor:pointer;color:var(--ink2);font-size:14px}
.cmp.uzerinde label,.cmp label:hover{border-color:var(--accent);color:var(--ink)}
.cmp input{position:absolute;width:1px;height:1px;opacity:0}
.sonuc{margin:12px 0 0;font-size:14.5px;font-weight:550;min-height:1em}
.sonuc.ok{color:var(--ok)}.sonuc.no{color:var(--no)}
.ozet{margin:14px 0 0;font-size:12px;color:var(--ink2);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;overflow-wrap:anywhere}
.not{margin:20px 0 0;color:var(--ink2);font-size:12.5px}
h1{margin:0 0 6px;font-size:21px;font-weight:650;letter-spacing:-.01em}
form label.k{display:block;font-size:13px;color:var(--ink2);margin-bottom:6px}
form input{width:100%;font:inherit;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.02em;padding:11px 12px;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:2px;outline:none;text-transform:uppercase}
form input:focus{border-color:var(--accent);box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 22%,transparent)}
form button{margin-top:12px;width:100%;font:inherit;font-weight:600;padding:11px 12px;color:var(--accent-ink);background:var(--accent);border:0;border-radius:2px;cursor:pointer}
form button:hover{filter:brightness(1.07)}
.hata{margin:0 0 16px;padding:10px 12px;border-left:3px solid var(--no);color:var(--no);font-size:14px;font-weight:550}
.eslesti{margin:0 0 18px;padding:10px 12px;border-left:3px solid var(--ok);color:var(--ok);font-size:14.5px;font-weight:550}
"""

def load():
    try:
        with open(REG) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save(reg):
    fd, tmp = tempfile.mkstemp(dir=BASE, prefix=".registry-")
    with os.fdopen(fd, "w") as f:
        json.dump(reg, f, ensure_ascii=False, indent=1)
    _perm(tmp)
    os.replace(tmp, REG)

def _perm(path):
    os.chmod(path, 0o640)
    try:
        import grp
        os.chown(path, 0, grp.getgrnam("ant-verify").gr_gid)
    except (KeyError, PermissionError):
        pass

class Lock:
    def __enter__(self):
        self.f = open(BASE + "/.lock", "w")
        fcntl.flock(self.f, fcntl.LOCK_EX)
        return self

    def __exit__(self, *a):
        self.f.close()

def normalize(raw):
    s = re.sub(r"[\s-]", "", raw.upper()).translate(str.maketrans("OIL", "011"))
    if not s.startswith("ANT") or len(s) != 19:
        return None
    s = "ANT-" + "-".join(s[3 + i:7 + i] for i in range(0, 16, 4))
    return s if NO_RE.match(s) else None

def new_no(reg):
    while True:
        n = "ANT-" + "-".join("".join(secrets.choice(ALPHA) for _ in range(4)) for _ in range(4))
        if n not in reg:
            return n

_cache = {"mtime": None, "reg": {}}

def registry():
    try:
        m = os.stat(REG).st_mtime_ns
    except FileNotFoundError:
        return {}
    if m != _cache["mtime"]:
        _cache["reg"], _cache["mtime"] = load(), m
    return _cache["reg"]

def shell(body, script):
    css = STYLE.replace("@@L@@", ICON_LIGHT).replace("@@D@@", ICON_DARK)
    return (f'<!doctype html><html lang="tr"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="robots" content="noindex,nofollow,noarchive"><title>Belge doğrulama · ANT Automobile</title>'
            f'<style>{css}</style></head><body><main><div class="logo" role="img" aria-label="ANT Automobile"></div>'
            f'{body}<p class="not">ANT Automobile belge doğrulama sistemi. Sorularınız için: info@antautomobile.org</p>'
            f'</main><script>{script}</script></body></html>').encode()

def giris(hata="", no=""):
    h = f'<p class="hata" role="alert">{escape(hata)}</p>' if hata else ""
    return shell(
        '<h1>Belge doğrulama</h1><p class="alt">ANT Automobile tarafından düzenlenen bir belgeyi doğrulamak için '
        'belgenin altındaki belge numarasını girin ya da elinizdeki PDF dosyasını bırakın.</p>' + h +
        '<form method="get" action="/" autocomplete="off"><label class="k" for="no">Belge No</label>'
        f'<input id="no" name="no" required maxlength="40" spellcheck="false" placeholder="ANT-XXXX-XXXX-XXXX-XXXX" '
        f'value="{escape(no)}"><button type="submit">Doğrula</button></form>'
        '<section class="cmp" id="ara"><h2>ya da dosyayla doğrulayın</h2><p>Size gönderilen PDF dosyasını seçin ya da '
        'buraya bırakın. Dosya bilgisayarınızdan çıkmaz; yalnızca tarayıcınızda hesaplanan özeti (SHA-256) '
        'aranır.</p><label for="f">Dosya seçin ya da sürükleyip bırakın</label>'
        '<input id="f" type="file" accept="application/pdf,.pdf"><p class="sonuc" id="sonuc" aria-live="polite"></p>'
        '</section>', SCRIPT_ARA)

def page(no, rec, eslesti=False):
    durum = rec.get("durum", "gecerli")
    if durum == "gecerli":
        bas = '<p class="durum ok">✓ Geçerli belge</p><p class="alt">Bu belge ANT Automobile tarafından düzenlenmiştir.</p>'
    elif durum == "yenilendi":
        bas = ('<p class="durum no">Bu belgenin yerine yenisi düzenlendi</p><p class="alt">Belge ANT Automobile '
               'tarafından düzenlenmiş, daha sonra güncellenmiştir. Güncel belge için bizimle iletişime geçin.</p>')
    else:
        bas = ('<p class="durum no">Bu belge iptal edilmiştir</p><p class="alt">Belge ANT Automobile tarafından '
               'düzenlenmiş, daha sonra iptal edilmiştir.</p>')

    satir = [("Belge No", f'<span class="no-k">{escape(no)}</span>'), ("Düzenleyen", "ANT Automobile"),
             ("İmzalayan", escape(rec["imzalayan"])), ("Düzenlenme tarihi", escape(rec["tarih"]))]
    dl = "<dl>" + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in satir) + "</dl>"
    cmp = (f'<section class="cmp" id="cmp" data-sha="{escape(rec["sha256"])}"><h2>Elinizdeki dosyayı karşılaştırın</h2>'
           '<p>Size gönderilen PDF dosyasını seçin ya da buraya bırakın. Dosya bu sayfadan çıkmaz; karşılaştırma '
           'tarayıcınızda yapılır.</p><label for="f">Dosya seçin ya da sürükleyip bırakın</label>'
           '<input id="f" type="file" accept="application/pdf,.pdf"><p class="sonuc" id="sonuc" aria-live="polite"></p>'
           '</section>')
    es = ('<p class="eslesti">✓ Bıraktığınız dosya bu belgeyle birebir aynı.</p>' if eslesti else "")
    return shell(bas + es + dl + cmp, SCRIPT)

class H(BaseHTTPRequestHandler):
    server_version = "ant-verify"
    sys_version = ""

    def log_message(self, *a):
        pass

    def head(self, code, ctype=None, length=0, extra=()):
        self.send_response(code)
        if ctype:
            self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "private, no-store")
        self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()

    def away(self):
        self.head(302, extra=[("Location", "/")])

    def html(self, data, body_too, code=200, extra=()):
        self.head(code, "text/html; charset=utf-8", len(data),
                  [("Content-Security-Policy", CSP), ("X-Frame-Options", "DENY"), *extra])
        if body_too:
            self.wfile.write(data)

    def root(self, body_too):
        q = parse_qs(urlsplit(self.path).query)
        reg = registry()
        gorunur = lambda r: r and r.get("durum") in ("gecerli", "iptal", "yenilendi")
        if "sha" in q:
            sha = q["sha"][0].strip().lower()
            hit = next((n for n, r in sorted(reg.items(), key=lambda kv: kv[1].get("durum") != "gecerli")
                        if gorunur(r) and r.get("sha256") == sha), None) \
                if re.fullmatch(r"[0-9a-f]{64}", sha) else None
            if hit:
                return self.head(302, extra=[("Location", f"/{hit}"),
                                             ("Set-Cookie", f"vd={hit}; Path=/{hit}; Max-Age=60; HttpOnly; Secure; SameSite=Lax")])
            return self.html(giris("Bu dosya kayıtlarımızda yok. Dosya değiştirilmiş ya da bizim düzenlemediğimiz "
                                   "bir belge olabilir."), body_too)
        if "no" in q:
            raw = q["no"][0][:40]
            no = normalize(raw)
            if no and gorunur(reg.get(no)):
                return self.head(302, extra=[("Location", f"/{no}")])
            return self.html(giris("Bu numarayla kayıtlı bir belge bulunamadı. Numarayı belgedeki gibi yazdığınızdan "
                                   "emin olun.", raw), body_too)
        return self.html(giris(), body_too)

    def json(self, code, obj, body_too=True, extra=()):
        data = (json.dumps(obj, ensure_ascii=False, indent=1) + "\n").encode()
        self.head(code, "application/json; charset=utf-8", len(data),
                  [("Access-Control-Allow-Origin", "*"), ("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'"),
                   *extra])
        if body_too:
            self.wfile.write(data)

    def api(self, body_too):
        u = urlsplit(self.path)
        q = parse_qs(u.query)
        path = u.path.rstrip("/") or "/"
        if path == "/":
            return self.json(200, {
                "name": "ANT Automobile API", "version": "v1",
                "endpoints": {
                    "GET /v1/verify/{document_no}": "status of a document issued by ANT Automobile",
                    "GET /v1/verify/{document_no}?sha256={hex}": "same, plus whether your file is the registered one",
                    "GET /v1/verify?sha256={hex}": "find the document whose PDF has this SHA-256",
                },
                "status_values": ["valid", "revoked", "superseded"],
                "docs": "https://api.antautomobile.org/swagger.json",
                "human_readable": HOST + "/", "contact": "info@antautomobile.org"}, body_too)
        if path != "/v1/verify" and not path.startswith("/v1/verify/"):
            return self.json(404, {"error": "not_found"}, body_too)
        sha = (q.get("sha256") or q.get("sha") or [None])[0]
        if sha is not None:
            sha = sha.strip().lower()
            if not re.fullmatch(r"[0-9a-f]{64}", sha):
                return self.json(400, {"error": "invalid_sha256"}, body_too)
        reg = registry()
        gorunur = lambda r: r and r.get("durum") in API_STATUS
        if path == "/v1/verify":
            if sha is None:
                return self.json(400, {"error": "missing_sha256"}, body_too)
            no = next((n for n, r in sorted(reg.items(), key=lambda kv: kv[1].get("durum") != "gecerli")
                       if gorunur(r) and r.get("sha256") == sha), None)
        else:
            raw = path[len("/v1/verify/"):]
            if "/" in raw or len(raw) > 40:
                return self.json(404, {"error": "not_found"}, body_too)
            no = normalize(raw)
            if not no:
                return self.json(400, {"error": "invalid_document_no"}, body_too)
        rec = reg.get(no) if no else None
        if not gorunur(rec):
            return self.json(404, {"status": "not_found"}, body_too)
        g, a, y = rec["tarih"].split(".")
        out = {"document_no": no, "status": API_STATUS[rec["durum"]], "issuer": "ANT Automobile",
               "signed_by": rec["imzalayan"], "issued_on": f"{y}-{a}-{g}", "verify_url": f"{HOST}/{no}"}
        if sha is not None:
            out["file_matches"] = rec.get("sha256") == sha
        return self.json(200, out, body_too)

    def is_api(self):
        return (self.headers.get("Host") or "").split(":")[0].lower() == API_HOST

    def find(self):
        parts = self.path.split("?", 1)[0].strip("/").split("/")
        if len(parts) != 1:
            return None, None
        no = normalize(parts[0])
        rec = registry().get(no) if no else None
        if not rec or rec.get("durum") not in ("gecerli", "iptal", "yenilendi"):
            return None, None
        return no, rec

    def serve(self, body_too):
        if self.is_api():
            return self.api(body_too)
        if self.path.split("?", 1)[0] == "/":
            return self.root(body_too)
        no, rec = self.find()
        if not no:
            return self.away()
        canon = f"/{no}"
        if self.path.split("?", 1)[0] != canon:
            return self.head(301, extra=[("Location", canon)])
        eslesti = f"vd={no}" in (self.headers.get("Cookie") or "").replace(" ", "").split(";")
        return self.html(page(no, rec, eslesti), body_too,
                         extra=[("Set-Cookie", f"vd=; Path=/{no}; Max-Age=0; HttpOnly; Secure; SameSite=Lax")] if eslesti else ())

    def do_GET(self):
        self.serve(True)

    def do_HEAD(self):
        self.serve(False)

    def do_POST(self):
        if self.is_api():
            return self.json(405, {"error": "method_not_allowed"}, extra=[("Allow", "GET, HEAD")])
        self.away()

def cmd_add(a):
    no = normalize(a.no)
    if not no:
        sys.exit(f"invalid document number: {a.no}")
    sha = (a.sha256 or "").lower()
    if not re.fullmatch(r"[0-9a-f]{64}", sha):
        sys.exit("--sha256: 64 hex digits required")
    if a.boyut <= 0:
        sys.exit("--size: positive byte count required")
    if not re.match(r"^\d{2}\.\d{2}\.\d{4}$", a.tarih):
        sys.exit("--date must be DD.MM.YYYY")
    with Lock():
        reg = load()
        if no in reg:
            sys.exit(f"{no} is already registered")
        eski = normalize(a.yerine) if a.yerine else None
        if a.yerine and (not eski or eski not in reg):
            sys.exit(f"--replaces: no such record: {a.yerine}")
        reg[no] = {"durum": "gecerli", "konu": a.konu, "kurum": a.kurum or "", "imzalayan": a.imzalayan,
                   "tarih": a.tarih, "ref": a.ref or "", "sha256": sha,
                   "boyut": a.boyut, "kayit": datetime.now(TZ).isoformat(timespec="seconds")}
        if eski:
            reg[eski].update(durum="yenilendi", yerine=no, degisti=reg[no]["kayit"])
            reg[no]["onceki"] = eski
        save(reg)
    print(f"{no}  {reg[no]['sha256']}  {HOST}/{no}")

def cmd_revoke(a):
    no = normalize(a.no)
    with Lock():
        reg = load()
        if no not in reg:
            sys.exit(f"no such record: {a.no}")
        reg[no].update(durum="iptal", neden=a.neden or "", iptal=datetime.now(TZ).isoformat(timespec="seconds"))
        save(reg)
    print(f"revoked: {no}")

def main():
    ap = argparse.ArgumentParser(prog="ant-verify")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("serve")
    sub.add_parser("new")
    sub.add_parser("list")
    s = sub.add_parser("show")
    s.add_argument("no")
    s = sub.add_parser("add")
    s.add_argument("no")
    s.add_argument("--sha256", required=True)
    s.add_argument("--size", dest="boyut", type=int, required=True)
    s.add_argument("--subject", dest="konu", required=True)
    s.add_argument("--signer", dest="imzalayan", required=True)
    s.add_argument("--date", dest="tarih", required=True, metavar="DD.MM.YYYY")
    s.add_argument("--recipient", dest="kurum")
    s.add_argument("--ref", dest="ref")
    s.add_argument("--replaces", dest="yerine", metavar="OLD_NO")
    s = sub.add_parser("revoke")
    s.add_argument("no")
    s.add_argument("--reason", dest="neden")
    a = ap.parse_args()

    if a.cmd == "serve":
        ThreadingHTTPServer(LISTEN, H).serve_forever()
    elif a.cmd == "new":
        print(new_no(load()))
    elif a.cmd == "add":
        cmd_add(a)
    elif a.cmd == "revoke":
        cmd_revoke(a)
    elif a.cmd == "list":
        for no, r in sorted(load().items(), key=lambda kv: kv[1].get("kayit", "")):
            print(f"{no}  {r['durum']:<9} {r['tarih']}  {r.get('kurum', '')[:30]:<30}  {r['konu'][:60]}")
    elif a.cmd == "show":
        no = normalize(a.no)
        r = load().get(no)
        if not r:
            sys.exit(f"no such record: {a.no}")
        print(json.dumps(dict(r, no=no, url=f"{HOST}/{no}"), ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
