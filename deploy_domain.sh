#!/usr/bin/env bash
# ربط secure-chat بنطاقك الخاص عبر Cloudflare Tunnel مُسمّى (دائم).
#
# الفرق عن deploy_cloudflare.sh:
#   - هذا السكربت يُنشئ "نفقاً مُسمّى" مرتبطاً بحسابك، فيبقى الرابط ثابتاً
#     (مثل chat.example.com) بدل الرابط العشوائي trycloudflare.com.
#
# المتطلبات:
#   1) حساب Cloudflare مجاني + نطاق مُضاف إلى Cloudflare (Full setup بـ nameservers).
#   2) cloudflared مثبّت محلياً.
#
# الاستخدام:
#   DOMAIN=chat.example.com bash deploy_domain.sh
#
# الخطوات (تُنفَّذ مرة واحدة، ثم يمكنك تشغيل النفق بأمر واحد):
#   cloudflared tunnel login
#   cloudflared tunnel create secure-chat
#   cloudflared tunnel route dns secure-chat chat.example.com
#   cloudflared tunnel run secure-chat
set -u

DOMAIN="${DOMAIN:-}"
TUNNEL_NAME="${TUNNEL_NAME:-secure-chat}"
PORT="${PORT:-12000}"
CONFIG_DIR="${HOME}/.cloudflared"
CONFIG_FILE="${CONFIG_DIR}/config.yml"

if [ -z "$DOMAIN" ]; then
  echo "[!] حدّد نطاقك:  DOMAIN=chat.example.com bash deploy_domain.sh" >&2
  exit 1
fi

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "[!] cloudflared غير مثبّت. راجع deploy_cloudflare.sh لطريقة التثبيت." >&2
  exit 1
fi

echo "== 1) تسجيل الدخول إلى Cloudflare =="
echo "   سيفتح رابط في المتصفح. اختر النطاق الذي تملكه ($DOMAIN)."
echo "   سيُكتب ملف الاعتماد في: $CONFIG_DIR/cert.pem  (سرّي — لا ترفعه)"
if [ ! -f "$CONFIG_DIR/cert.pem" ]; then
  cloudflared tunnel login
else
  echo "   ✅ مسجّل دخول مسبقاً ($CONFIG_DIR/cert.pem موجود)"
fi

echo "== 2) إنشاء النفق المُسمّى '$TUNNEL_NAME' =="
if cloudflared tunnel list 2>/dev/null | grep -qw "$TUNNEL_NAME"; then
  echo "   ✅ النفق موجود مسبقاً"
else
  cloudflared tunnel create "$TUNNEL_NAME"
fi

TUNNEL_ID="$(cloudflared tunnel list --output json 2>/dev/null \
  | python -c "import json,sys; print(next(t['id'] for t in json.load(sys.stdin) if t['name']=='$TUNNEL_NAME'))" 2>/dev/null)"
if [ -z "${TUNNEL_ID:-}" ]; then
  echo "[!] تعذّر إيجاد معرّف النفق." >&2
  exit 1
fi
echo "   المعرّف: $TUNNEL_ID"

echo "== 3) ربط النطاق $DOMAIN بالنفق (إنشاء سجل CNAME) =="
cloudflared tunnel route dns "$TUNNEL_NAME" "$DOMAIN" 2>&1 | grep -v "already exists" || true

echo "== 4) كتابة ملف الإعداد $CONFIG_FILE =="
mkdir -p "$CONFIG_DIR"
cat > "$CONFIG_FILE" <<YAML
tunnel: $TUNNEL_ID
credentials-file: $CONFIG_DIR/$TUNNEL_ID.json

ingress:
  - hostname: $DOMAIN
    service: http://127.0.0.1:$PORT
  - service: http_status:404
YAML
echo "   ✅ كُتب"

echo "== 5) تشغيل السيرفر محلياً على المنفذ $PORT =="
pkill -f "server.py --port $PORT" 2>/dev/null
sleep 1
if [ -z "${ADMIN_PASSWORD:-}" ]; then
  ADMIN_PASSWORD="$(python -c 'import secrets;print(secrets.token_urlsafe(9))')"
  echo "   [i] كلمة مرور اللوحة لهذه الجلسة: $ADMIN_PASSWORD"
fi
export ADMIN_PASSWORD
setsid nohup python -u server.py --host 127.0.0.1 --port "$PORT" \
  > /tmp/secure-chat.log 2>&1 < /dev/null &
sleep 4
if ! curl -s -m 5 -o /dev/null "http://127.0.0.1:$PORT/chat"; then
  echo "[!] السيرفر لم يستجب. راجع /tmp/secure-chat.log" >&2
  exit 1
fi
echo "   ✅ السيرفر يعمل"

echo "== 6) تشغيل النفق المُسمّى =="
pkill -f "cloudflared tunnel run" 2>/dev/null
setsid nohup cloudflared tunnel run "$TUNNEL_NAME" > /tmp/cloudflared-domain.log 2>&1 < /dev/null &
sleep 6

echo
echo "======================================================"
echo "  🏠 الصفحة الرئيسية:  https://$DOMAIN"
echo "  💬 الدردشة:          https://$DOMAIN/chat"
echo "  ⚙️  لوحة التحكم:      https://$DOMAIN/settings  (تسجيل دخول)"
echo "======================================================"
echo
echo "  للتحقق:   curl -I https://$DOMAIN/chat"
echo "  للتوقف:   pkill -f 'cloudflared tunnel run'; pkill -f 'server.py --port $PORT'"
echo
echo "  💡 للتشغيل الدائم كخدمة نظام:"
echo "     sudo cloudflared service install"
