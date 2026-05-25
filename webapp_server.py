"""
Web App ni local HTTP server bilan serve qilib,
serveo.net yoki localhost.run orqali HTTPS tunnel yaratadi.
URL avtomatik .env ga yoziladi.
"""
import subprocess, threading, re, time, sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

WEBAPP_DIR = Path(__file__).parent / "webapp"
PORT = 8765
LOG = Path(__file__).parent / "wserv.log"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(WEBAPP_DIR), **kw)
    def log_message(self, *_):
        pass


def log(msg):
    print(msg, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def serve():
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


def update_env(url: str):
    p = Path(__file__).parent / ".env"
    try:
        lines = p.read_text("utf-8").splitlines()
    except FileNotFoundError:
        lines = []
    out = []
    found = False
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
    """Run SSH tunnel command, return (url, proc) or ('', None)."""
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
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


def main():
    LOG.write_text("", encoding="utf-8")  # reset log

    # Start HTTP server
    t = threading.Thread(target=serve, daemon=True)
    t.start()
    log(f"[HTTP] Listening on http://localhost:{PORT}")

    # Try serveo.net first (more reliable)
    log("[Tunnel] Trying serveo.net ...")
    url, proc = try_tunnel(
        ["ssh", "-o", "StrictHostKeyChecking=no",
         "-o", "ServerAliveInterval=30",
         "-o", "ConnectTimeout=20",
         "-o", "ExitOnForwardFailure=yes",
         "-R", f"80:localhost:{PORT}",
         "serveo.net"],
        r'https://[\w\-]+\.serveousercontent\.com'
    )

    # Fallback: localhost.run
    if not url:
        log("[Tunnel] serveo.net failed, trying localhost.run ...")
        url, proc = try_tunnel(
            ["ssh", "-o", "StrictHostKeyChecking=no",
             "-o", "ServerAliveInterval=30",
             "-o", "ConnectTimeout=20",
             "-R", f"80:localhost:{PORT}",
             "nokey@localhost.run"],
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
        # Tunnel died — try to reconnect
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
