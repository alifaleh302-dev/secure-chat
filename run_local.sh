#!/usr/bin/env bash
# تشغيل secure-chat محلياً على جهازك — بلا إنترنت، بلا تكاليف.
#
# الاستخدام:
#   bash run_local.sh              # تشغيل عادي (AES-GCM)
#   CIPHER=AES-ECB bash run_local.sh   # لتجربة كشف الأنماط في Wireshark
#   ENCRYPTION=0 bash run_local.sh     # نص واضح تماماً (تجربة السرية)
set -u

PORT="${PORT:-5000}"
HOST="${HOST:-127.0.0.1}"

# كلمة مرور ثابتة للوحة التحكم (بدلها بأي شيء تريده)
export ADMIN_PASSWORD="${ADMIN_PASSWORD:-local-demo-1234}"

# فحص سريع للمكتبات
if ! python -c "import Crypto, cryptography" 2>/dev/null; then
  echo "[!] المكتبات غير مثبّتة. ثبّتها مرة واحدة:"
  echo "    pip install -r requirements.txt"
  exit 1
fi

echo "======================================================"
echo "  تشغيل secure-chat محلياً"
echo "======================================================"
echo "  الدردشة:        http://localhost:$PORT/chat"
echo "  لوحة التحكم:    http://localhost:$PORT/settings"
echo "  المستخدم:       admin"
echo "  كلمة المرور:    $ADMIN_PASSWORD"
echo
echo "  لتشغيل عميل بايثون (طرفية أخرى):"
echo "    python client.py --name ali"
echo
echo "  للإيقاف: Ctrl+C"
echo "======================================================"
echo

exec python -u server.py --host "$HOST" --port "$PORT"
