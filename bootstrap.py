"""Super DM VPN bootstrap: zero-touch setup for PasarGuard on Railway. Idempotent: safe on every boot."""
import json, os, sys, threading, time, urllib.error, urllib.parse, urllib.request

BASE = "http://127.0.0.1:8000"
DATA = os.getenv("JINX_DATA", "/var/lib/pasarguard")
DOMAIN = (os.getenv("PUBLIC_DOMAIN") or os.getenv("RAILWAY_PUBLIC_DOMAIN") or "").strip()
import subprocess
USER, PASS = "admin", "admin"          # first-boot login; change it later in the panel or with the owner key
RESELLER_USER, RESELLER_PASS, RESELLER_GB = "reseller", "reseller", 50
CORE_NAME, NODE_NAME = "JinX-Core", "JinX-Core"  # تگ فنی هسته بدون تغییر برای حفظ پینگ
PRO_GROUP, STD_GROUP = "DM VPN Pro", "DM VPN"   # نام نمایشی گروه‌ها
OLD_GROUP = "jinx-all"                         # گروه قدیمی برای حفظ کاربران قبلی
TITLE = os.getenv("CONFIG_TITLE", "DM VPN | 𝙎𝙪𝙥𝙚𝙧 𝗗𝗠 𝗩𝗣𝗡")   # عنوان نمایشی کانفیگ‌ها
GB = 1024 ** 3
DAY = 86400

# تگ‌های فنی و مسیرها کاملاً استاندارد دست‌نخورده باقی مانده‌اند تا پینگ و اتصال برقرار بماند
INBOUNDS = [
    # tag              proto     port  net            server path                                   fp       name         group
    ("JX-VLESS-WS-1", "vless",  10001, "ws",          "/ws/",     "chrome",  "𝗣𝗿𝗼",        "pro"),
    ("JX-VLESS-WS-2", "vless",  10002, "ws",          "/stream/", "firefox", "⚡ 𝗙𝗹𝗮𝘀𝗵",    "std"),
    ("JX-TROJAN-WS",  "trojan", 10003, "ws",          "/live/",   "safari",  "🔥 𝗙𝗶𝗿𝗲",     "std"),
    ("JX-VMESS-WS",   "vmess",  10004, "ws",          "/gw/",    "edge",    "💎 𝗗𝗶𝗮𝗺𝗼𝗻𝗱", "std"),
]
EARLY_DATA = "?ed=2560"

try:
    _P = json.load(open(f"{DATA}/paths.json"))
    INBOUNDS = [(t, pr, po, n, _P.get(t, pa), fp, nm, g) for (t, pr, po, n, pa, fp, nm, g) in INBOUNDS]
except Exception as _e:
    print("[bootstrap] paths.json missing, run genpaths.py first:", _e, flush=True); sys.exit(1)

TEMPLATES = [  # نام قالب‌های حجمی نمایشی
    ("10GB - 30 روز", 10, 30, "std"), ("30GB - 30 روز", 30, 30, "std"), ("50GB - 30 روز", 50, 30, "std"),
    ("100GB - 30 روز", 100, 30, "std"), ("200GB - 60 روز", 200, 60, "std"), ("نامحدود - 30 روز", 0, 30, "std"),
    ("Pro 30GB - 30 روز", 30, 30, "pro"), ("Pro 50GB - 30 روز", 50, 30, "pro"),
    ("Pro 100GB - 30 روز", 100, 30, "pro"), ("Pro نامحدود - 30 روز", 0, 30, "pro"),
]
OLD_TEST_USERS = ("jinx_user1",)

TOKEN = None

def log(*a): print("[bootstrap]", *a, flush=True)
_GLOBAL = object()

def req(method, path, body=None, form=False, ok=(200, 201, 204), token=_GLOBAL):
    url = BASE + path
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        if form:
            data = urllib.parse.urlencode(body).encode(); headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            data = json.dumps(body).encode(); headers["Content-Type"] = "application/json"
    tok = TOKEN if token is _GLOBAL else token
    if tok: headers["Authorization"] = f"Bearer {tok}"
    r = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read().decode()
            try: return resp.status, json.loads(raw) if raw.strip() else None
            except ValueError: return resp.status, raw
    except urllib.error.HTTPError as e:
        txt = e.read().decode(errors="ignore")
        try: return e.code, json.loads(txt)
        except Exception: return e.code, txt

def must(method, path, body=None):
    code, res = req(method, path, body)
    if code not in (200, 201, 204):
        raise RuntimeError(f"{method} {path} -> {code}: {res}")
    return res

def as_list(res, key):
    if isinstance(res, list): return res
    if isinstance(res, dict): return res.get(key) or []
    return []

def wait_panel():
    for _ in range(180):
        try:
            code, _ = req("GET", "/api/system")
            if code in (200, 401, 403): return
        except Exception: pass
        time.sleep(2)
    raise RuntimeError("panel did not come up")

TEMP_KEY_PY = """
import asyncio
from app.db.base import GetDB
from app.db.crud.temp_key import create_temp_key
async def main():
    async with GetDB() as db:
        k = await create_temp_key(db)
        print("KEY=" + k.key)
asyncio.run(main())
"""

def temp_key():
    out = subprocess.run([sys.executable, "-c", TEMP_KEY_PY], cwd="/code", capture_output=True, text=True, timeout=60)
    for line in out.stdout.splitlines():
        if line.startswith("KEY="): return line[4:].strip()
    raise RuntimeError(f"temp key failed: {out.stderr[-500:]}")

ADMIN_PW_PY = """
import asyncio, sys
from app.db.base import GetDB
from app.db.crud.admin import get_owner, get_admin
from app.models.admin import _hash_password_sync
async def main():
    mode, user, pw = sys.argv[1], sys.argv[2], sys.argv[3]
    async with GetDB() as db:
        if mode == "owner":
            o = await get_owner(db)
        else:
            o = await get_admin(db, user, load_users=False, load_usage_logs=False)
        if o is None:
            print("MISSING"); return
        o.username = user
        o.hashed_password = _hash_password_sync(pw)
        await db.commit()
        print("OK")
asyncio.run(main())
"""

def write_password(mode, user, pw):
    out = subprocess.run([sys.executable, "-c", ADMIN_PW_PY, mode, user, pw], cwd="/code",
                         capture_output=True, text=True, timeout=90)
    ok = out.stdout.strip().splitlines()[-1:] == ["OK"]
    if not ok: log(f"password write ({mode} {user}) failed:", (out.stdout + out.stderr)[-400:])
    return ok

ADMIN_DB_PY = r"""
import asyncio, json, sys
req = json.loads(sys.argv[1])
def _hash(pw):
    try:
        from app.models.admin import _hash_password_sync
        return _hash_password_sync(pw)
    except Exception:
        import bcrypt
        return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
def _check(pw, h):
    if not h: return False
    try:
        import bcrypt
        return bcrypt.checkpw(pw.encode(), h.encode())
    except Exception:
        try:
            from passlib.context import CryptContext
            return CryptContext(schemes=["bcrypt"]).verify(pw, h)
        except Exception:
            return None
async def main():
    from sqlalchemy import select, func
    from app.db.base import GetDB
    from app.db.models import Admin
    out = {"ok": False}
    async with GetDB() as db:
        async def by_name(n):
            r = await db.execute(select(Admin).where(func.lower(Admin.username) == n.strip().lower()))
            return r.scalars().first()
        def is_owner(a):
            try:
                role = getattr(a, "role", None)
                if role is not None and getattr(role, "is_owner", False): return True
            except Exception: pass
            return bool(getattr(a, "is_sudo", False) and getattr(a, "is_owner", True))
        op = req["op"]
        if op == "selftest":
            await db.execute(select(Admin).limit(1)); _hash("x"); out = {"ok": True, "check": _check("x", _hash("x"))}
        elif op == "verify":
            a = await by_name(req["username"])
            if a is not None:
                c = _check(req["password"], a.hashed_password)
                out = {"ok": c is True, "unknown": c is None, "username": a.username, "owner": is_owner(a)}
        elif op == "set":
            a = await by_name(req["username"])
            if a is None: out = {"ok": False, "error": "missing"}
            else:
                new_name = (req.get("new_username") or "").strip()
                if new_name and new_name.lower() != a.username.lower():
                    other = await by_name(new_name)
                    if other is not None: print("RESULT=" + json.dumps({"ok": False, "error": "taken"})); return
                    a.username = new_name
                a.hashed_password = _hash(req["password"])
                await db.commit()
                await db.refresh(a)
                out = {"ok": _check(req["password"], a.hashed_password) is not False, "username": a.username}
    print("RESULT=" + json.dumps(out))
asyncio.run(main())
"""

def admin_db(**req):
    try:
        out = subprocess.run([sys.executable, "-c", ADMIN_DB_PY, json.dumps(req)], cwd="/code",
                             capture_output=True, text=True, timeout=90)
        for line in out.stdout.splitlines():
            if line.startswith("RESULT="): return json.loads(line[7:])
    except Exception as e:
        log("account tool error:", e)
    return {"ok": False, "error": "tool"}

def client_ip(handler):
    xff = (handler.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
    return xff or (handler.headers.get("X-Real-IP") or handler.client_address[0]).strip()

_attempts = {}
def limited(bucket, ip, fail=False):
    k = f"{bucket}:{ip}"; now = time.time()
    hist = [t for t in _attempts.get(k, []) if now - t < 600]
    if fail: hist.append(now)
    _attempts[k] = hist
    return len(hist) >= 5

def strong_tmp():
    import secrets
    return "DM" + secrets.token_hex(8) + "Aa9!Zz7"

TOKEN_PY = """
import asyncio
from app.db.base import GetDB
from app.db.crud.admin import get_owner
from app.utils.jwt import create_admin_token
async def main():
    async with GetDB() as db:
        o = await get_owner(db)
        if o is None:
            print("NOOWNER"); return
        print("TOKEN=" + await create_admin_token(o.id, o.username))
asyncio.run(main())
"""

def owner_token():
    out = subprocess.run([sys.executable, "-c", TOKEN_PY], cwd="/code", capture_output=True, text=True, timeout=60)
    for line in out.stdout.splitlines():
        if line.startswith("TOKEN="): return line[6:].strip()
        if line.strip() == "NOOWNER": return None
    raise RuntimeError(f"token failed: {(out.stdout + out.stderr)[-400:]}")

MARKER = f"{DATA}/.owner_initialized"
RESELLER_MARKER = f"{DATA}/.reseller_initialized"

def ensure_owner():
    if owner_token() is None:
        code, res = req("POST", "/api/setup/owner", {"key": temp_key(), "username": "dmowner", "password": strong_tmp()})
        if code not in (200, 201, 409): log(f"owner create failed {code}: {res}")
        if os.path.exists(MARKER): os.remove(MARKER)
    if not os.path.exists(MARKER):
        if write_password("owner", USER, PASS):
            open(MARKER, "w").write(str(int(time.time())))
            log("owner ready:", USER, "/", PASS, "(first boot)")

_owner_keys = {}
KEY_TTL = 300

def new_owner_key():
    import secrets
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    k = "DM-" + "-".join("".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(3))
    now = time.time()
    for old in [x for x, exp in _owner_keys.items() if exp < now]: _owner_keys.pop(old, None)
    _owner_keys[k] = now + KEY_TTL
    return k

def use_owner_key(k):
    k = str(k or "").strip().upper()
    exp = _owner_keys.pop(k, None)
    return bool(exp and exp >= time.time())

def print_owner_key():
    k = new_owner_key()
    log("=" * 60)
    log("OWNER KEY (valid 5 min, one use):", k)
    log("=" * 60)

def login():
    global TOKEN
    ensure_owner()
    for _ in range(30):
        tok = owner_token()
        if tok:
            TOKEN = tok; return
        time.sleep(3)
    raise RuntimeError("could not get an owner token")

def inbound(tag, proto, port, net, path):
    stream = {"network": net, "security": "none"}
    if net == "ws": stream["wsSettings"] = {"path": path}
    elif net == "httpupgrade": stream["httpupgradeSettings"] = {"path": path}
    elif net == "xhttp": stream["xhttpSettings"] = {"path": path, "mode": "auto"}
    settings = {"clients": []}
    if proto == "vless": settings["decryption"] = "none"
    return {"tag": tag, "listen": "127.0.0.1", "port": port, "protocol": proto,
            "settings": settings, "streamSettings": stream,
            "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic"], "routeOnly": True}}

CORE_CONFIG = {
    "log": {"loglevel": "warning"},
    "dns": {"servers": ["localhost", "https+local://1.1.1.1/dns-query", "8.8.8.8"], "queryStrategy": "UseIPv4"},
    "inbounds": [inbound(*i[:5]) for i in INBOUNDS],
    "outbounds": [
        {"protocol": "freedom", "tag": "DIRECT", "settings": {"domainStrategy": "UseIPv4"}},
        {"protocol": "blackhole", "tag": "BLOCK"},
    ],
    "routing": {"domainStrategy": "AsIs", "rules": [
        {"type": "field", "ip": ["geoip:private"], "outboundTag": "BLOCK"},
        {"type": "field", "protocol": ["bittorrent"], "outboundTag": "BLOCK"},
    ]},
    "policy": {"levels": {"0": {"handshake": 4, "connIdle": 300, "uplinkOnly": 1, "downlinkOnly": 1, "bufferSize": 512}}},
}

def ensure_core():
    cores = as_list(must("GET", "/api/cores"), "cores")
    for c in cores:
        if c.get("name") in (CORE_NAME, "jinx-core"):
            if c.get("name") == CORE_NAME and c.get("config") == CORE_CONFIG:
                log("core ok (unchanged)", c["id"]); return c["id"]
            body = {"name": CORE_NAME, "config": CORE_CONFIG, "exclude_inbound_tags": [], "fallbacks_inbound_tags": []}
            code, res = req("PUT", f"/api/core/{c['id']}?restart_nodes=true", body)
            if code not in (200, 201):
                code, res = req("PUT", f"/api/core/{c['id']}?restart_nodes=false", body)
            return c["id"]
    c = must("POST", "/api/core", {"name": CORE_NAME, "config": CORE_CONFIG,
                                    "exclude_inbound_tags": [], "fallbacks_inbound_tags": []})
    return c["id"]

def ensure_node(core_id):
    api_key = open(f"{DATA}/node_api_key").read().strip()
    cert = open(f"{DATA}/node-certs/cert.pem").read().strip()
    body = {"name": NODE_NAME, "address": "127.0.0.1", "port": 62050, "usage_coefficient": 1,
            "connection_type": "grpc", "server_ca": cert, "keep_alive": 60,
            "core_config_id": core_id, "api_key": api_key}
    for n in as_list(must("GET", "/api/nodes"), "nodes"):
        if n.get("name") in (NODE_NAME, "jinx-local"):
            must("PUT", f"/api/node/{n['id']}", body); return
    must("POST", "/api/node", body)

def ensure_groups():
    want = {"pro": (PRO_GROUP, [i[0] for i in INBOUNDS if i[7] == "pro"]),
            "std": (STD_GROUP, [i[0] for i in INBOUNDS if i[7] == "std"])}
    groups = as_list(must("GET", "/api/groups"), "groups")
    by_name = {g.get("name"): g for g in groups}
    if STD_GROUP not in by_name and OLD_GROUP in by_name:
        by_name[STD_GROUP] = by_name.pop(OLD_GROUP)
    if STD_GROUP not in by_name and "جینکس" in by_name:
        by_name[STD_GROUP] = by_name.pop("جینکس")
    if STD_GROUP not in by_name and "𝗝𝗶𝗻𝗫" in by_name:
        by_name[STD_GROUP] = by_name.pop("𝗝𝗶𝗻𝗫")
    ids = {}
    for key, (name, tags) in want.items():
        g = by_name.get(name)
        if g:
            if g.get("name") != name or sorted(g.get("inbound_tags") or []) != sorted(tags):
                must("PUT", f"/api/group/{g['id']}", {"name": name, "inbound_tags": tags})
            ids[key] = g["id"]
        else:
            g = must("POST", "/api/group", {"name": name, "inbound_tags": tags}); ids[key] = g["id"]
    return ids

QUIET = {}
def _norm(v):
    if isinstance(v, list): return [str(x).lower() for x in v]
    if v is None: return None
    if isinstance(v, bool): return v
    return [str(v).lower()] if isinstance(v, str) and "," not in v else str(v).lower()

def ensure_hosts():
    if not DOMAIN: return
    existing = as_list(must("GET", "/api/hosts"), "hosts")
    wanted = {i[0] for i in INBOUNDS}
    for h in existing:
        if str(h.get("inbound_tag") or "").startswith("JX-") and h.get("inbound_tag") not in wanted:
            req("DELETE", f"/api/host/{h['id']}")
    for idx, (tag, proto, port, net, path, fp, name, grp) in enumerate(INBOUNDS):
        body = {"remark": f"{name} | {TITLE}", "allowinsecure": False, "address": [DOMAIN], "inbound_tag": tag,
                "port": 443, "sni": [DOMAIN], "host": [DOMAIN], "path": path + EARLY_DATA, "security": "tls",
                "alpn": ["http/1.1"], "fingerprint": fp, "priority": idx + 1, "is_disabled": False}
        mine = [h for h in existing if h.get("inbound_tag") == tag]
        if mine:
            cur = mine[0]
            if any(_norm(cur.get(k)) != _norm(v) for k, v in body.items()):
                must("PUT", f"/api/host/{cur['id']}", {**body, "id": cur["id"]})
            for extra in mine[1:]:
                req("DELETE", f"/api/host/{extra['id']}")
        else:
            must("POST", "/api/host/", body)

def ensure_settings():
    if not DOMAIN: return
    code, s = req("GET", "/api/settings")
    if code != 200 or not isinstance(s, dict) or "subscription" not in s: return
    sub = s["subscription"]
    want = {"url_prefix": f"https://{DOMAIN}", "profile_title": TITLE, "update_interval": 12}
    if all(sub.get(k) == v for k, v in want.items()): return
    sub.update(want)
    req("PUT", "/api/settings", {"subscription": sub})

RESELLER_ROLE = "نماینده DM VPN"

def ensure_reseller_role(gids):
    own = {"scope": 1}
    role = {
        "name": RESELLER_ROLE,
        "permissions": {
            "users": {"create": own, "read": own, "read_simple": own, "update": own, "delete": own,
                      "reset_usage": own, "revoke_sub": own, "activate_next_plan": own},
            "templates": {"read": True, "read_simple": True},
            "groups": {"read_simple": True},
            "system": {"read": True},
            "settings": {"read_general": True},
        },
        "access": {"require_template": True, "allowed_group_ids": sorted(gids.values())},
        "disabled_when_limited": True,
    }
    for base in ("/api/admin-role",):
        code, res = req("GET", base + "s")
        if code != 200: continue
        roles = as_list(res, "roles")
        mine = [r for r in roles if r.get("name") in (RESELLER_ROLE, "نماینده")]
        if mine:
            req("PUT", f"{base}/{mine[0]['id']}", {"access": role["access"]})
            return
        code, res = req("POST", base, role)
        if code in (200, 201): return

def role_id_by_name(name):
    code, res = req("GET", "/api/admin-roles")
    for r in as_list(res, "roles") if code == 200 else []:
        if r.get("name") in (name, "نماینده"): return r["id"]
    return None

def ensure_demo_reseller():
    if os.getenv("DEMO_RESELLER", "on").lower() in ("off", "false", "0", "no"): return
    if os.path.exists(RESELLER_MARKER): return
    rid = role_id_by_name(RESELLER_ROLE)
    if not rid: return
    code, _ = req("POST", "/api/admin/token", {"username": RESELLER_USER, "password": RESELLER_PASS}, form=True)
    if code == 200: open(RESELLER_MARKER, "w").write("1"); return
    code, res = req("POST", "/api/admin", {"username": RESELLER_USER, "password": strong_tmp(),
                                           "role_id": rid, "data_limit": RESELLER_GB * GB,
                                           "profile_title": TITLE})
    if code in (200, 201):
        if write_password("user", RESELLER_USER, RESELLER_PASS): open(RESELLER_MARKER, "w").write("1")
    elif code == 409: open(RESELLER_MARKER, "w").write("1")

def ensure_templates(gids):
    have = {t.get("name"): t for t in as_list(must("GET", "/api/user_templates"), "templates")}
    for name, gb, days, grp in TEMPLATES:
        body = {"name": name, "data_limit": gb * GB, "expire_duration": days * DAY, "group_ids": [gids[grp]],
                "status": "active", "data_limit_reset_strategy": "no_reset"}
        if name in have:
            if have[name].get("group_ids") != [gids[grp]]: req("PUT", f"/api/user_template/{have[name]['id']}", body)
        else:
            must("POST", "/api/user_template", body)

def remove_demo_user():
    for name in OLD_TEST_USERS:
        code, u = req("GET", f"/api/user/{name}")
        if code == 200 and isinstance(u, dict):
            req("DELETE", f"/api/user/{name}")

def attach_orphans(gids):
    code, res = req("GET", "/api/users?no_group=true&limit=200")
    if code == 401: login(); code, res = req("GET", "/api/users?no_group=true&limit=200")
    if code != 200: return
    for u in as_list(res, "users"):
        if not isinstance(u, dict) or "group_ids" not in u or u.get("group_ids"): continue
        req("PUT", f"/api/user/{u['username']}", {"group_ids": [gids["std"]]})

def heal_node(state):
    code, res = req("GET", "/api/nodes")
    if code == 401: login(); code, res = req("GET", "/api/nodes")
    if code != 200: return
    for n in as_list(res, "nodes"):
        if n.get("name") != NODE_NAME: continue
        st = str(n.get("status") or "")
        if st in ("connected", "disabled"): state["bad"] = 0; return
        state["bad"] = state.get("bad", 0) + 1
        if state["bad"] >= 2:
            req("POST", f"/api/core/{n.get('core_config_id')}/restart")
            state["bad"] = 0
        return

def main():
    wait_panel(); login(); print_owner_key()
    core_id = ensure_core()
    time.sleep(2)
    ensure_node(core_id)
    gid = None
    for _ in range(10):
        gid = ensure_groups()
        if gid: break
        time.sleep(3)
    if not gid: raise RuntimeError("groups could not be created")
    ensure_hosts()
    ensure_settings()
    ensure_templates(gid)
    ensure_reseller_role(gid)
    ensure_demo_reseller()
    remove_demo_user()
    log("DONE ->", f"https://{DOMAIN}/dashboard/" if DOMAIN else "generate a Railway domain")

if __name__ == "__main__":
    try: main()
    except Exception as e: log("FATAL", e); sys.exit(1)
