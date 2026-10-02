"""تدفق كامل في متصفح حقيقي: هبوط → دردشة → دخول اللوحة → تبديل إعداد."""
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
PW = sys.argv[2] if len(sys.argv) > 2 else "test-admin-pw"

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/usr/bin/chromium",
        args=["--no-sandbox", "--disable-dev-shm-usage"],
    )
    page = browser.new_page()
    page.on("pageerror", lambda e: print(f"  [PAGE ERROR] {e}"))
    page.on("response", lambda r: print(f"  [{r.status}] {r.url}") if r.status >= 400 else None)

    print("1) الصفحة الرئيسية (/)")
    page.goto(BASE + "/", wait_until="load")
    print("   العنوان:", page.title())
    print("   يحتوي الدردشة:", "فتح الدردشة" in page.content())

    print("2) الدردشة (/chat)")
    page.goto(BASE + "/chat", wait_until="load")
    page.wait_for_timeout(3500)
    print("   الحالة:", page.inner_text("#status"), "| المصادقة:", page.inner_text("#auth"))
    page.fill("#text", "رسالة من التدفق الكامل")
    page.click("#send")
    page.wait_for_timeout(2500)
    msgs = page.locator(".msg").all_inner_texts()
    mine = [m for m in msgs if "التدفق الكامل" in m]
    print(f"   عدد مرات ظهور رسالتي: {len(mine)}  {'✅' if len(mine) == 1 else '❌ ازدواجية!'}")

    print("3) النقر على ⚙️ الإعدادات (بدون جلسة → /login)")
    page.click("a[href='/settings']")
    page.wait_for_timeout(1500)
    print("   URL:", page.url)
    assert page.url.endswith("/login"), "لم يُحوَّل إلى /login"

    print("4) تسجيل الدخول بكلمة خاطئة")
    page.fill("#u", "admin"); page.fill("#p", "wrong")
    page.click("button[type=submit]")
    page.wait_for_timeout(1200)
    print("   ظهر خطأ:", "غير صحيحة" in page.content())

    print("5) تسجيل الدخول الصحيح")
    page.fill("#u", "admin"); page.fill("#p", PW)
    page.click("button[type=submit]")
    page.wait_for_timeout(1500)
    print("   URL:", page.url)
    assert page.url.endswith("/settings"), "لم يصل إلى /settings"

    print("6) تبديل التشفير من اللوحة")
    before = page.is_checked("#ENCRYPTION")
    page.click("#ENCRYPTION + .sl")
    page.click("text=حفظ الإعدادات")
    page.wait_for_timeout(1500)
    print("   رسالة الحفظ:", page.inner_text("#msg"))
    after = page.evaluate("fetch('/api/config').then(r=>r.json()).then(c=>c.ENCRYPTION)")
    print(f"   ENCRYPTION قبل={before} بعد={after}  {'✅ تغيّر' if before != after else '❌ لم يتغيّر'}")
    page.click("#ENCRYPTION + .sl")
    page.click("text=حفظ الإعدادات")
    page.wait_for_timeout(1200)

    print("7) الخروج")
    page.click("a[href='/logout']")
    page.wait_for_timeout(1200)
    page.goto(BASE + "/settings", wait_until="load")
    print("   بعد الخروج /settings →", page.url)

    browser.close()
    print("=== التدفق الكامل نجح ===")
