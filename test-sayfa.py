# /// script
# dependencies = ["playwright"]
# ///
import sys
from playwright.sync_api import sync_playwright
url, good, bad = sys.argv[1:4]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/chromium")
    pg = b.new_page()
    errs = []
    pg.on("console", lambda m: errs.append(m.text))
    pg.goto(url)
    for f in (good, bad):
        pg.set_input_files("#f", f)
        pg.wait_for_function("document.getElementById('sonuc').className!=='sonuc'")
        print(pg.inner_text("#sonuc"))
    print("console:", errs)
    b.close()
