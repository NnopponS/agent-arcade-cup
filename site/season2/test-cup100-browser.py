"""Exercise the staged Agent Arcade Cup at its GitHub Pages subpath."""
import os
import subprocess
from datetime import datetime, timedelta, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[2]


class PreviewHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def check_replay_library(browser, site, width):
    context = browser.new_context(viewport={"width": width, "height": 900}, reduced_motion="reduce")
    context.grant_permissions(["clipboard-read", "clipboard-write"])
    page = context.new_page()
    page.set_default_timeout(5000)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    baseline = datetime(2026, 1, 1, tzinfo=timezone.utc)
    page.clock.install(time=baseline)
    assert page.goto(site).ok
    expect(page.get_by_role("heading", name="Agent Arcade Cup.")).to_be_visible()
    page.get_by_role("link", name="Watch the final", exact=False).click()
    assert page.url == site + "cup100.html?match=R7-01#cup-replay"
    expect(page.locator("#outcome")).to_have_text("LAYA-09 won by engine KO")
    page.get_by_role("slider").press("End")
    expect(page.get_by_text("28 HP", exact=True)).to_be_visible()
    page.go_back()
    page.get_by_role("link", name="Replays", exact=True).click()
    expect(page.get_by_role("heading", name="Replay library")).to_be_visible()
    assert page.url == site + "cup100.html#bracket"

    table = page.locator("#bracket-table")
    count = page.locator("#filter-count")
    search = page.get_by_role("searchbox", name="Match or entrant")
    round_select = page.get_by_label("Round", exact=True)
    entry_type = page.get_by_label("Entry type")
    expect(count).to_have_text("12 of 99 entries")
    page.get_by_role("button", name="Show 12 more").click()
    expect(table.get_by_role("row")).to_have_count(25)

    search.fill("kev qwen")
    round_select.select_option("R3")
    expect(table.get_by_role("link", name="Watch R3-06")).to_be_visible()
    assert all("KEV" in row and "QWEN" in row for row in table.get_by_role("row").all_inner_texts()[1:])
    search.fill("kev-07")
    expect(count).to_have_text("1 of 1 entry")
    table.get_by_role("link", name="Watch R3-06").click()
    assert page.url == site + "cup100.html?match=R3-06#cup-replay"
    expect(page.get_by_role("heading", name="Match replay")).to_be_focused()
    expect(page.locator("#outcome")).to_have_text("KEV-07 won by engine KO")
    expect(page.get_by_role("button", name="Play", exact=True)).to_be_enabled()

    slider = page.get_by_role("slider", name="Seek match timeline")
    expect(slider).to_have_value("0")
    page.get_by_label("Speed").select_option("4")
    page.clock.pause_at(baseline + timedelta(minutes=10))
    page.get_by_role("button", name="Play", exact=True).press("Space")
    page.clock.run_for(1000)
    assert 225 <= int(slider.input_value()) <= 245, "4× should play nearly four seconds"
    page.get_by_role("button", name="Pause", exact=True).press("Space")
    page.clock.resume()
    slider.press("End")
    expect(page.get_by_text("10 HP", exact=True)).to_be_visible()
    expect(page.get_by_text("0 HP", exact=True)).to_be_visible()
    expect(page.get_by_text("K.O.", exact=True)).to_be_visible()
    slider.press("Home")
    expect(page.get_by_text("K.O.", exact=True)).to_be_hidden()
    page.get_by_role("button", name="Copy replay link").click()
    expect(page.get_by_text("Replay link copied.")).to_be_visible()
    assert page.evaluate("navigator.clipboard.readText()") == page.url

    page.go_back()
    expect(search).to_have_value("kev-07")
    expect(round_select).to_have_value("R3")
    assert page.url == site + "cup100.html#bracket"
    search.fill("no such entrant")
    expect(page.get_by_text("No results for those filters.", exact=False)).to_be_visible()
    page.get_by_role("button", name="Clear filters").click()
    expect(search).to_be_focused()
    entry_type.select_option("bye")
    expect(count).to_have_text("12 of 28 entries")
    expect(table.get_by_role("link")).to_have_count(0)
    round_select.select_option("R7")
    expect(table).to_be_hidden()
    page.get_by_role("button", name="Clear filters").click()
    round_select.select_option("R7")
    expect(table.get_by_role("link", name="Watch R7-01")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")

    expect(page.get_by_role("link", name="Research", exact=True)).to_be_visible()
    page.get_by_role("link", name="Research", exact=True).click()
    assert page.url == site + "#decision-lab"
    expect(page.get_by_text("Practice results only:", exact=True)).to_be_visible()
    page.get_by_text("FightingICE Choice benchmark", exact=True).click()
    expect(page.get_by_role("region", name="Fixed-scenario benchmark measurements")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors, errors
    context.close()
    print(f"Passed: replay discovery, playback, shared URL, and research at {width}px")


def check_direct_routes(browser, site):
    page = browser.new_page()
    page.set_default_timeout(5000)
    page.goto(site + "cup100.html?match=../anything#cup-replay")
    expect(page.locator("#outcome")).to_have_text("LAYA-09 won by engine KO")
    expect(page.get_by_role("button", name="Play", exact=True)).to_be_enabled()
    expect(page.get_by_role("slider")).to_have_value("0")

    page.route("**/cup100-replay/R2-24.json", lambda route: route.abort(), times=1)
    page.goto(site + "cup100.html?match=R2-24#cup-replay")
    expect(page.get_by_text("Could not load the replay.")).to_be_visible()
    expect(page.get_by_role("button", name="Play", exact=True)).to_be_disabled()
    page.get_by_role("button", name="Retry replay").click()
    expect(page.locator("#outcome")).to_have_text("SMOL-06 won by engine KO")
    page.get_by_role("button", name="KO", exact=False).click()
    expect(page.get_by_text("14 HP", exact=True)).to_be_visible()
    page.close()

    page = browser.new_page(java_script_enabled=False)
    page.goto(site + "cup100.html#bracket")
    expect(page.get_by_role("link", name="Watch R7-01")).to_be_visible()
    expect(page.locator("#bracket-table").get_by_role("row")).to_have_count(128)
    page.close()
    print("Passed: safe fallback, direct route, failed request recovery, and no-JavaScript bracket")


def main():
    with TemporaryDirectory() as directory, sync_playwright() as playwright:
        subprocess.run(["bash", ROOT / "site/season2/stage-pages.sh", Path(directory) / "agent-arcade-cup"], check=True)
        with ThreadingHTTPServer(("127.0.0.1", 0), partial(PreviewHandler, directory=directory)) as server:
            Thread(target=server.serve_forever, daemon=True).start()
            site = f"http://127.0.0.1:{server.server_port}/agent-arcade-cup/"
            browser = playwright.chromium.launch(executable_path=os.getenv("CHROME_PATH"))
            try:
                for width in (320, 390, 1440):
                    check_replay_library(browser, site, width)
                check_direct_routes(browser, site)
            finally:
                browser.close()
                server.shutdown()


if __name__ == "__main__":
    main()
