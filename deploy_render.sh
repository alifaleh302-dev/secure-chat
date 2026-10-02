#!/usr/bin/env bash
# نشر المستودع على Render عبر الـ API.
# يتطلب: RENDER_API_KEY في البيئة.
set -u

REPO_NAME="secure-chat"
REPO_URL="https://github.com/alifaleh302-dev/secure-chat"
BRANCH="main"
SERVICE_NAME="secure-chat"
API="https://api.render.com/v1"

if [ -z "${RENDER_API_KEY:-}" ]; then
  echo "[!] RENDER_API_KEY غير موجود في البيئة." >&2
  exit 1
fi

auth=(-H "Authorization: Bearer $RENDER_API_KEY" -H "Accept: application/json")

echo "== 1) التحقق من المفتاح وجلب المالك =="
owner=$(curl -s -m 20 "${auth[@]}" "$API/owners?limit=1" | python -c "
import sys,json
try:
    d=json.load(sys.stdin)
except Exception:
    print('ERROR'); sys.exit()
if isinstance(d,list) and d:
    o=d[0].get('owner',d[0])
    print(o.get('id',''))
else:
    print('ERROR')
")
if [ -z "$owner" ] || [ "$owner" = "ERROR" ]; then
  echo "[!] فشل التحقق من المفتاح — تحقق من صحته وصلاحياته." >&2
  exit 1
fi
echo "    ownerId = $owner"

echo "== 2) البحث عن المستودع في حساب Render =="
repo_id=$(curl -s -m 30 "${auth[@]}" "$API/repos?limit=100" | python -c "
import sys,json
want='$REPO_NAME'
try:
    d=json.load(sys.stdin)
except Exception:
    print(''); sys.exit()
for item in d:
    r=item.get('repo',item)
    full=(r.get('name') or '')+' '+(r.get('owner',{}).get('name') if isinstance(r.get('owner'),dict) else '')
    if want in full or (r.get('name','').endswith('/'+want)):
        print(r.get('id','')); break
")
if [ -n "$repo_id" ]; then
  echo "    repoId = $repo_id"
  REPO_FIELD="\"repo\": \"$repo_id\""
else
  echo "    لم يوجد repoId — سنستخدم رابط المستودع مباشرة (قد ينجح إن كان GitHub مرتبطاً)"
  REPO_FIELD="\"repo\": \"$REPO_URL\""
fi

echo "== 3) إنشاء خدمة الويب =="
body=$(cat <<JSON
{
  "type": "web_service",
  "name": "$SERVICE_NAME",
  "ownerId": "$owner",
  $REPO_FIELD,
  "branch": "$BRANCH",
  "autoDeploy": "yes",
  "envVars": [
    {"key": "HOST", "value": "0.0.0.0"},
    {"key": "CIPHER", "value": "AES-GCM"},
    {"key": "ENCRYPTION", "value": "1"},
    {"key": "INTEGRITY", "value": "1"},
    {"key": "AUTHENTICATION", "value": "1"},
    {"key": "KEY_EXCHANGE", "value": "ECDH"}
  ],
  "serviceDetails": {
    "env": "docker",
    "plan": "free",
    "region": "oregon",
    "healthCheckPath": "/chat",
    "envSpecificDetails": {"dockerfilePath": "./Dockerfile"}
  }
}
JSON
)

resp=$(curl -s -m 60 -X POST "${auth[@]}" -H "Content-Type: application/json" \
  "$API/services" -d "$body")

echo "$resp" | python -c "
import sys,json
try:
    d=json.load(sys.stdin)
except Exception:
    print('[!] رد غير متوقع:', sys.stdin.read()[:400]); sys.exit(1)
s=d.get('service',d)
if 'id' in s:
    print('    ✅ أُنشئت الخدمة:', s['id'])
    print('    الرابط:', s.get('serviceDetails',{}).get('url') or ('https://%s.onrender.com' % s.get('name')))
    print('    لوحة التحكم: https://dashboard.render.com/web/'+s['id'])
else:
    print('[!] فشل الإنشاء:', json.dumps(d)[:500]); sys.exit(1)
"
