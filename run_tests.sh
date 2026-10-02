#!/usr/bin/env bash
cd /workspace/project
export ADMIN_PASSWORD="test-admin-pw"
pkill -f "python -u server.py" 2>/dev/null
pkill -f "python server.py" 2>/dev/null
sleep 1
python -u server.py --port 5000 > /tmp/final.log 2>&1 &
sleep 3

echo "########## 1) SELFTEST ##########"
python selftest.py 2>&1 | tail -3
echo
echo "########## 2) INTEGRATION (2 python clients) ##########"
timeout 30 python test_integration.py 2>&1 | tail -8
echo
echo "########## 3) BROWSER PATH ##########"
timeout 30 python test_browser.py 2>&1 | tail -7
echo
echo "########## 4) HTTP ENDPOINTS ##########"
echo "  -- عام (متوقع 200) --"
for p in / /chat /login /favicon.ico /robots.txt; do
  code=$(curl -s -m 5 -o /dev/null -w '%{http_code}' "http://127.0.0.1:5000$p")
  printf "  %-14s -> %s\n" "$p" "$code"
done
echo "  -- محمي بدون جلسة (متوقع 302 لـ /settings و 401 للـ API) --"
printf "  %-14s -> %s\n" "/settings" "$(curl -s -m 5 -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/settings)"
for p in /api/config /api/status /api/identity; do
  code=$(curl -s -m 5 -o /dev/null -w '%{http_code}' "http://127.0.0.1:5000$p")
  printf "  %-14s -> %s\n" "$p" "$code"
done
echo "  -- بعد تسجيل الدخول --"
curl -s -m 5 -c /tmp/cj.txt -o /dev/null -X POST \
  -d "username=admin&password=$ADMIN_PASSWORD" http://127.0.0.1:5000/login
for p in /settings /api/config /api/status /api/identity; do
  code=$(curl -s -m 5 -b /tmp/cj.txt -o /dev/null -w '%{http_code}' "http://127.0.0.1:5000$p")
  printf "  %-14s -> %s\n" "$p" "$code"
done
echo "  -- دخول بكلمة خاطئة (متوقع 401) --"
printf "  %-14s -> %s\n" "/login" "$(curl -s -m 5 -o /dev/null -w '%{http_code}' -X POST -d 'username=admin&password=wrong' http://127.0.0.1:5000/login)"
echo
echo "########## 5) SERVER LOG ##########"
cat /tmp/final.log
pkill -f "python -u server.py" 2>/dev/null
