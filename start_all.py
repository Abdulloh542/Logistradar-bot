"""
Logistradar ishga tushiruvchi skript:
1. Cloudflare tunnel ishga tushiradi
2. URL ni aniqlaydi (.env ni yangilaydi)
3. Botni ishga tushiradi
"""
import subprocess
import sys
import os
import re
import time
import threading
import signal

BASE = os.path.dirname(os.path.abspath(__file__))
CF_EXE = r"C:\Users\user\cloudflared.exe"
ENV_FILE = os.path.join(BASE, ".env")
LOG_FILE = os.path.join(BASE, "cf.log")


def update_env(url: str):
    """WEBAPP_URL ni .env da yangilaydi."""
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r"WEBAPP_URL=.*", f"WEBAPP_URL={url}", content)
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"OK .env yangilandi: WEBAPP_URL={url}")
    except Exception as e:
        print(f"WARN .env yangilashda xato: {e}")


def start_cloudflared():
    """Cloudflare tunnel ishga tushiradi va URL qaytaradi."""
    if not os.path.exists(CF_EXE):
        print("WARN: cloudflared.exe topilmadi, tunnel o'tkazib yuborildi")
        return None, None

    try:
        os.remove(LOG_FILE)
    except Exception:
        pass

    print("Cloudflare tunnel ishga tushmoqda...")
    proc = subprocess.Popen(
        [CF_EXE, "tunnel", "--url", "http://localhost:8888", "--logfile", LOG_FILE],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    url_pattern = re.compile(r"https://[a-z0-9\-]+\.trycloudflare\.com")
    for _ in range(40):
        time.sleep(0.5)
        try:
            with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            m = url_pattern.search(text)
            if m:
                print(f"OK Tunnel URL: {m.group(0)}")
                return m.group(0), proc
        except Exception:
            pass

    print("WARN: Tunnel URL topilmadi (timeout)")
    return None, proc


def main():
    print("=" * 50)
    print("   Logistradar Bot")
    print("=" * 50)

    cf_result = start_cloudflared()
    if cf_result and cf_result[0]:
        tunnel_url, cf_proc = cf_result
        update_env(tunnel_url)
    else:
        print("INFO: Tunnel yo'q -- bot polling mode da ishlaydi")

    print("\nBot ishga tushmoqda...\n")
    bot_proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE, "main.py")],
        cwd=BASE,
    )

    def on_exit(sig, frame):
        print("\nTo'xtatilmoqda...")
        bot_proc.terminate()
        if cf_result and len(cf_result) > 1 and cf_result[1]:
            cf_result[1].terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, on_exit)
    signal.signal(signal.SIGTERM, on_exit)

    bot_proc.wait()


if __name__ == "__main__":
    main()
