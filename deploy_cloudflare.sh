#!/usr/bin/env bash
# تشغيل secure-chat محلياً + نشره على الإنترنت عبر Cloudflare Tunnel.
# لا يحتاج حساباً ولا بطاقة — النفق السريع (quick tunnel) مجاني.
set -u

PORT="${PORT:-12000}"
HOST_BIND="${HOST_BIND:-127.0.0.1}"
LOG_DIR="${LOG_DIR:-/tmp}"

# كلمة مرور لوحة التحكم (/settings و /api/*). إن لم تُضبط، يولّد السيرفر
# كلمة عشوائية ويطبعها في السجل.
if [ -z "${ADMIN_PASSWORD:-}" ]; then
  ADMIN_PASSWORD="$(python -c 'import secrets;print(secrets.token_urlsafe(9))')"
  echo "[i] كلمة مرور لوحة التحكم لهذه الجلسة: $ADMIN_PASSWORD"
fi
export ADMIN_PASSWORD

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "[!] cloudflared غير مثبّت. ثبّته أولاً:" >&2
  echo "    curl -sL -o /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb" >&2
  echo "    sudo dpkg -i /tmp/cloudflared.deb" >&2
  exit 1
fi

echo "== 1) تشغيل السيرفر على المنفذ $PORT =="
pkill -f "server.py --port $PORT" 2>/dev/null
sleep 1
setsid nohup python -u server.py --host "$HOST_BIND" --port "$PORT" \
  > "$LOG_DIR/secure-chat.log" 2>&1 < /dev/null &
sleep 4

if ! curl -s -m 5 -o /dev/null "http://127.0.0.1:$PORT/chat"; then
  echo "[!] السيرفر لم يستجب. راجع السجل: $LOG_DIR/secure-chat.log" >&2
  tail -20 "$LOG_DIR/secure-chat.log" >&2
  exit 1
fi
echo "    ✅ السيرفر يعمل: http://127.0.0.1:$PORT/chat"

echo "== 2) فتح نفق Cloudflare =="
pkill -f "cloudflared tunnel --url" 2>/dev/null
sleep 1
setsid nohup cloudflared tunnel --url "http://127.0.0.1:$PORT" --no-autoupdate \
  > "$LOG_DIR/cloudflared.log" 2>&1 < /dev/null &

url=""
for _ in $(seq 1 30); do
  url=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" "$LOG_DIR/cloudflared.log" 2>/dev/null | head -1)
  [ -n "$url" ] && break
  sleep 1
done

if [ -z "$url" ]; then
  echo "[!] لم يظهر رابط النفق. راجع: $LOG_DIR/cloudflared.log" >&2
  tail -20 "$LOG_DIR/cloudflared.log" >&2
  exit 1
fi

echo
echo "======================================================"
echo "  🌐 الرابط العام:   $url/chat"
echo "  ⚙️  الإعدادات:      $url/settings"
echo "======================================================"
echo
echo "  للتوقف:  pkill -f 'cloudflared tunnel --url'; pkill -f 'server.py --port $PORT'"
