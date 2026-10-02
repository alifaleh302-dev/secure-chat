#!/usr/bin/env bash
# يتحقق أن كل وضع تشفير يعمل من طرف إلى طرف (عميل بايثون)
cd /workspace/project
pkill -f "python -u server.py" 2>/dev/null
sleep 1
for mode in RC4 AES-ECB AES-CBC AES-CTR AES-GCM; do
  CIPHER=$mode python -u server.py --port 5000 > /tmp/mode.log 2>&1 &
  sleep 2
  out=$(timeout 20 python test_integration.py 2>&1)
  if echo "$out" | grep -q "ALL TESTS DONE"; then
    printf "  %-8s  ✅ يعمل\n" "$mode"
  else
    printf "  %-8s  ❌ فشل\n" "$mode"
    echo "$out" | tail -5
  fi
  pkill -f "python -u server.py" 2>/dev/null
  sleep 1
done
