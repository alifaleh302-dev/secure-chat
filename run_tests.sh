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
echo "  -- بدون مصادقة (متوقع 401 للوحة التحكم، 200 للدردشة) --"
for p in /settings /api/config /api/status /api/identity; do
  code=$(curl -s -m 5 -o /dev/null -w '%{http_code}' "http://127.0.0.1:5000$p")
  printf "  %-14s -> %s\n" "$p" "$code"
done
code=$(curl -s -m 5 -o /dev/null -w '%{http_code}' "http://127.0.0.1:5000/chat")
printf "  %-14s -> %s (عام)\n" "/chat" "$code"

echo "  -- مع مصادقة admin --"
for p in /settings /api/config /api/status /api/identity; do
  code=$(curl -s -m 5 -u "admin:$ADMIN_PASSWORD" -o /dev/null -w '%{http_code}' "http://127.0.0.1:5000$p")
  printf "  %-14s -> %s\n" "$p" "$code"
done
echo
echo "########## 5) SERVER LOG ##########"
cat /tmp/final.log
pkill -f "python -u server.py" 2>/dev/null
