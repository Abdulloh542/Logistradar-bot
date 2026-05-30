"""
Web App ni local HTTP server bilan serve qilib,
serveo.net yoki localhost.run orqali HTTPS tunnel yaratadi.
URL avtomatik .env ga yoziladi.

/api/ads  — SQLite dan e'lonlarni qaytaradi
"""
import json
import subprocess
import threading
import re
import time
import sqlite3
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

WEBAPP_DIR = Path(__file__).parent / "webapp"
DB_PATH    = Path(__file__).parent / "yukonuz.db"
PORT = 8765
LOG  = Path(__file__).parent / "wserv.log"


def log(msg):
    print(msg, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def get_ads(page=1, limit=20, q="", truck="ALL"):
    """Fetch ads from SQLite with optional search."""
    try:
        con = sqlite3.connect(str(DB_PATH))
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        conditions, params = [], []
        if q:
            for word in q.lower().split():
                conditions.append("(LOWER(from_loc)||' '||LOWER(to_loc)||' '||LOWER(cargo)||' '||LOWER(source)) LIKE ?")
                params.append(f"%{word}%")
        if truck and truck != "ALL":
            conditions.append("LOWER(truck) LIKE ?")
            params.append(f"%{truck.lower()}%")

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        offset = (page - 1) * limit

        cur.execute(f"SELECT COUNT(*) FROM ads {where}", params)
        total = cur.fetchone()[0]

        cur.execute(
            f"SELECT * FROM ads {where} ORDER BY created DESC LIMIT ? OFFSET ?",
            params + [limit, offset]
        )
        rows = [dict(r) for r in cur.fetchall()]
        con.close()
        return {"total": total, "page": page, "limit": limit, "ads": rows}
    except Exception as e:
        return {"total": 0, "page": 1, "limit": limit, "ads": [], "error": str(e)}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs     = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/api/ads":
            page  = int(qs.get("page",  ["1"])[0])
            limit = int(qs.get("limit", ["20"])[0])
            q     = qs.get("q",     [""])[0]
            truck = qs.get("truck", ["ALL"])[0]
            data  = get_ads(page, limit, q, truck)
            body  = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._cors()
            self.end_headers()
            self.wfile.write(body)
            return

        # Serve static files from webapp/
        path = parsed.path.lstrip("/") or "index.html"
        fp   = WEBAPP_DIR / path
        if not fp.exists() or not fp.is_file():
            fp = WEBAPP_DIR / "index.html"
        try:
            content = fp.read_bytes()
            ext     = fp.suffix.lower()
            mime    = {
                ".html": "text/html; charset=utf-8",
                ".js":   "application/javascript",
                ".css":  "text/css",
                ".png":  "image/png",
                ".jpg":  "image/jpeg",
                ".svg":  "image/svg+xml",
            }.get(ext, "application/octet-stream")
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self._cors()
            self.end_headers()
            self.wfile.write(content)
        except Exception:
            self.send_response(404)
            self.end_headers()


def update_env(url: str):
    p = Path(__file__).parent / ".env"
    try:
        lines = p.read_text("utf-8").splitlines()
    except FileNotFoundError:
        lines = []
    out, found = [], False
    for ln in lines:
        if ln.startswith("WEBAPP_URL="):
            out.append(f"WEBAPP_URL={url}")
            found = True
        else:
            out.append(ln)
    if not found:
        out.append(f"WEBAPP_URL={url}")
    p.write_text("\n".join(out) + "\n", "utf-8")


def try_tunnel(cmd: list, url_pattern: str, timeout: int = 40):
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1
        )
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = proc.stdout.readline()
            if not line:
                time.sleep(0.1)
                continue
            log(f"[Tunnel] {line.strip()}")
            m = re.search(url_pattern, line)
            if m:
                return m.group(0), proc
        proc.terminate()
    except Exception as e:
        log(f"[Tunnel-ERR] {e}")
    return "", None


def serve():
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


def main():
    LOG.write_text("", encoding="utf-8")
    t = threading.Thread(target=serve, daemon=True)
    t.start()
    log(f"[HTTP] Listening on http://localhost:{PORT}")

    log("[Tunnel] Trying serveo.net ...")
    url, proc = try_tunnel(
        ["ssh", "-o", "StrictHostKeyChecking=no",
         "-o", "ServerAliveInterval=30",
         "-o", "ConnectTimeout=20",
         "-o", "ExitOnForwardFailure=yes",
         "-R", f"80:localhost:{PORT}", "serveo.net"],
        r'https://[\w\-]+\.serveousercontent\.com'
    )

    if not url:
        log("[Tunnel] serveo.net failed, trying localhost.run ...")
        url, proc = try_tunnel(
            ["ssh", "-o", "StrictHostKeyChecking=no",
             "-o", "ServerAliveInterval=30",
             "-o", "ConnectTimeout=20",
             "-R", f"80:localhost:{PORT}", "nokey@localhost.run"],
            r'https://[\w\-]+\.lhr\.life'
        )

    if url:
        update_env(url)
        log(f"[OK] WEBAPP_URL = {url}")
        log("[OK] .env updated. Restart bot now!")
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
        log("[WARN] Tunnel died, restarting in 5s...")
        time.sleep(5)
        main()
    else:
        log(f"[WARN] No tunnel. Local only: http://localhost:{PORT}")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
