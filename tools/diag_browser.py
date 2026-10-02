"""تشخيص واجهة المتصفح: التقاط أخطاء الكونسول + فحص عرض الرسائل."""
import sys
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://intimate-formula-yen-mar.trycloudflare.com/chat"

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/usr/bin/chromium",
        args=["--no-sandbox", "--disable-dev-shm-usage"],
    )
    page = browser.new_page()

    page.on("console", lambda m: print(f"  [console.{m.type}] {m.text}"))
    page.on("pageerror", lambda e: print(f"  [PAGE ERROR] {e}"))
    page.on("requestfailed", lambda r: print(f"  [REQ FAILED] {r.url} — {r.failure}"))
    page.on("response", lambda r: print(f"  [{r.status}] {r.url}") if r.status >= 400 else None)

    page.goto(URL, wait_until="load")
    page.wait_for_timeout(4000)

    print("=== حالة الاتصال ===")
    print("  status:", page.inner_text("#status"))
    print("  cipher:", page.inner_text("#cipher"))
    print("  auth  :", page.inner_text("#auth"))

    print("=== إرسال رسالة ===")
    page.fill("#text", "رسالة تشخيص")
    page.click("#send")
    page.wait_for_timeout(3000)

    print("=== محتوى سجل الدردشة ===")
    print(page.inner_text("#log"))

    print("=== عدد الرسائل في DOM ===")
    print("  .msg:", page.locator(".msg").count())

    print("=== النقر على رابط الإعدادات (بدون مصادقة) ===")
    page.click("a[href='/settings']")
    page.wait_for_timeout(2000)
    print("  URL:", page.url)
    print("  أول 120 حرفاً:", page.inner_text("body")[:120].replace("\n", " "))

    browser.close()
