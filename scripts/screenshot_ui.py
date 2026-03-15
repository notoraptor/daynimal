"""Automated UI screenshot tool using Playwright + Flet web mode.

Modes:
    (default)   Comprehensive audit: empty states, interactions, dark theme
    --quick     Quick capture of the 6 main tabs only (real DB, with data)

Usage:
    uv run python scripts/screenshot_ui.py           # Full audit (~14 screenshots)
    uv run python scripts/screenshot_ui.py --quick   # Quick mode (6 screenshots)
"""

import asyncio
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


PORT = 8550
VIEWPORT_WIDTH = 420
VIEWPORT_HEIGHT = 820
FLUTTER_LOAD_TIMEOUT = 15000  # ms - Flutter/CanvasKit init takes time
TAB_SWITCH_DELAY = 3000  # ms - wait for view content to load
ACTION_DELAY = 2000  # ms - wait after a click/interaction
SEARCH_DELAY = 4000  # ms - wait for search results (local DB query)
ANIMAL_LOAD_DELAY = 10000  # ms - wait for animal load + enrichment

# Database paths
REAL_DB = Path("daynimal.db")
TEMP_DB = Path("tmp/screenshot.db")

# --- Navigation coordinates (420x820 viewport) ---
TAB_WIDTH = VIEWPORT_WIDTH / 6
TAB_Y = VIEWPORT_HEIGHT - 28  # center of bottom nav bar


def _tab_x(index: int) -> float:
    """Center X coordinate for nav bar tab at given index (0-5)."""
    return TAB_WIDTH * index + TAB_WIDTH / 2


# Interactive element coordinates (approximate, may need tuning).
# Measured from actual screenshots at 2x scale (divide by 2 for CSS pixels).
# Layout reference:
#   [0-48px]   Header (padding=10, title 28px, padding=10)
#   [48-49px]  Divider
#   [49-~130]  Subheader (if present: search bar, info text)
#   [~130-740] Scrollable content
#   [~740]     Footer (pagination, if present)
#   [740-820]  Nav bar
COORDS = {
    # Shuffle button: header right side (3-col layout, END-aligned actions)
    "shuffle_btn": (390, 24),
    # Search field: in subheader, center of TextField (~49+padding+field/2)
    "search_field": (200, 125),
    # First search result card: content area top
    "first_result": (210, 210),
}


# =========================================================================
# Database preparation
# =========================================================================


def prepare_temp_db(dark_theme: bool = False):
    """Copy real DB to temp location and clear user data for clean state."""
    TEMP_DB.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REAL_DB, TEMP_DB)

    conn = sqlite3.connect(str(TEMP_DB))
    conn.execute("DELETE FROM animal_history")
    conn.execute("DELETE FROM favorites")
    conn.execute("DELETE FROM user_settings")
    # Disable auto-load so we see the welcome screen
    conn.execute(
        "INSERT INTO user_settings (key, value) VALUES ('auto_load_on_start', 'false')"
    )
    if dark_theme:
        conn.execute(
            "INSERT INTO user_settings (key, value) VALUES ('theme_mode', 'dark')"
        )
    conn.commit()
    conn.close()


# =========================================================================
# Server management
# =========================================================================


def launch_flet_server(use_temp_db: bool = False):
    """Launch Flet app in web mode without opening a browser."""
    launcher_code = (
        """
import webbrowser
webbrowser.open = lambda *a, **kw: None  # Suppress auto-open browser

import flet as ft
from daynimal.app import DaynimalApp, _install_asyncio_exception_handler

def app_main(page: ft.Page):
    _install_asyncio_exception_handler()
    DaynimalApp(page)

ft.run(main=app_main, view=ft.AppView.WEB_BROWSER, port=%d)
"""
        % PORT
    )

    env = os.environ.copy()
    if use_temp_db:
        env["DAYNIMAL_DATABASE_URL"] = f"sqlite:///{TEMP_DB.as_posix()}"

    proc = subprocess.Popen(
        ["uv", "run", "python", "-c", launcher_code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    return proc


def wait_for_server(timeout: int = 30) -> bool:
    """Wait for the Flet web server to be ready."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(f"http://localhost:{PORT}", timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def _stop_server(proc):
    """Terminate the Flet server process."""
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


# =========================================================================
# Playwright helpers
# =========================================================================


async def _click(page, x, y, delay=ACTION_DELAY):
    """Click at coordinates and wait."""
    await page.mouse.click(x, y)
    await page.wait_for_timeout(delay)


async def _click_tab(page, index, delay=TAB_SWITCH_DELAY):
    """Click a navigation bar tab by index (0-5)."""
    await page.mouse.click(_tab_x(index), TAB_Y)
    await page.wait_for_timeout(delay)


async def _type_in_search(page, query):
    """Focus search field, type query via Flutter's hidden input, and submit.

    Flutter Web (CanvasKit) renders on a <canvas> — standard keyboard events
    don't reach TextFields. Instead, Flutter creates a hidden <input> in the
    DOM when a TextField is focused. We interact with that element directly.
    """
    # Click on the search field area to trigger Flutter focus
    await page.mouse.click(*COORDS["search_field"])
    await page.wait_for_timeout(1500)  # Wait for Flutter to create hidden input

    # Find Flutter's hidden text input and type into it
    input_el = page.locator("input").last
    await input_el.fill(query, force=True, timeout=5000)
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(SEARCH_DELAY)


async def _screenshot(page, output_dir, name, step, total):
    """Take a screenshot and print progress."""
    path = output_dir / f"{name}.png"
    await page.screenshot(path=str(path))
    print(f"  [{step}/{total}] {name}")


# =========================================================================
# Quick mode: 6 tabs (real DB)
# =========================================================================


async def take_quick_screenshots():
    """Capture the 6 main tabs with current app state."""
    from playwright.async_api import async_playwright

    output_dir = Path("tmp/screenshots")
    output_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
            device_scale_factor=2,
        )
        page = await context.new_page()

        print(f"Opening http://localhost:{PORT} ...")
        await page.goto(f"http://localhost:{PORT}")
        print(f"Waiting {FLUTTER_LOAD_TIMEOUT // 1000}s for Flutter to render...")
        await page.wait_for_timeout(FLUTTER_LOAD_TIMEOUT)

        await _screenshot(page, output_dir, "01_decouverte", 1, 6)

        tabs = [
            ("02_historique", 1),
            ("03_favoris", 2),
            ("04_recherche", 3),
            ("05_stats", 4),
            ("06_reglages", 5),
        ]
        for i, (name, index) in enumerate(tabs, 2):
            await _click_tab(page, index)
            await _screenshot(page, output_dir, name, i, 6)

        await browser.close()
        print(f"\nDone: 6 screenshots in {output_dir}/")


# =========================================================================
# Full audit mode: comprehensive screenshots (temp DB)
# =========================================================================


async def _open_browser_and_wait(playwright):
    """Open a Playwright browser, navigate to the app, and wait for Flutter."""
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
        device_scale_factor=2,
    )
    page = await context.new_page()

    print(f"  Opening http://localhost:{PORT} ...")
    await page.goto(f"http://localhost:{PORT}")
    print(f"  Waiting {FLUTTER_LOAD_TIMEOUT // 1000}s for Flutter to render...")
    await page.wait_for_timeout(FLUTTER_LOAD_TIMEOUT)

    return browser, page


async def take_full_screenshots(proc_holder):
    """Comprehensive audit: empty states, search, animal, dark theme.

    Phase 3 (dark theme) requires restarting the server with theme_mode=dark
    pre-configured in the DB, since Flutter/CanvasKit Switch widgets don't
    respond reliably to Playwright coordinate clicks.

    Args:
        proc_holder: mutable list holding the server process [proc],
                     so we can restart it for phase 3.
    """
    from playwright.async_api import async_playwright

    output_dir = Path("tmp/screenshots")
    output_dir.mkdir(parents=True, exist_ok=True)

    total = 14
    step = 0

    async with async_playwright() as p:
        # =============================================================
        # Pass 1: Light theme (phases 1 & 2)
        # =============================================================
        browser, page = await _open_browser_and_wait(p)

        # --- Phase 1: Empty states ---
        print("\n--- Phase 1: Empty states ---")

        step += 1
        await _screenshot(page, output_dir, "01_accueil_bienvenue", step, total)

        step += 1
        await _click_tab(page, 1)
        await _screenshot(page, output_dir, "02_historique_vide", step, total)

        step += 1
        await _click_tab(page, 2)
        await _screenshot(page, output_dir, "03_favoris_vide", step, total)

        step += 1
        await _click_tab(page, 3)
        await _screenshot(page, output_dir, "04_recherche_vide", step, total)

        step += 1
        await _click_tab(page, 4)
        await _screenshot(page, output_dir, "05_stats", step, total)

        step += 1
        await _click_tab(page, 5)
        await _screenshot(page, output_dir, "06_reglages", step, total)

        # --- Phase 2: Search + Animal ---
        print("\n--- Phase 2: Search + Animal ---")

        await _click_tab(page, 3)
        await _type_in_search(page, "panthera")

        step += 1
        await _screenshot(page, output_dir, "07_recherche_resultats", step, total)

        await _click(page, *COORDS["first_result"], delay=ANIMAL_LOAD_DELAY)

        step += 1
        await _screenshot(page, output_dir, "08_accueil_animal", step, total)

        await page.mouse.move(VIEWPORT_WIDTH // 2, VIEWPORT_HEIGHT // 2)
        await page.mouse.wheel(0, 400)
        await page.wait_for_timeout(1000)

        step += 1
        await _screenshot(page, output_dir, "09_accueil_animal_details", step, total)

        await page.mouse.wheel(0, -400)
        await page.wait_for_timeout(500)

        await _click_tab(page, 3)
        await _type_in_search(page, "xyznotfound123")

        step += 1
        await _screenshot(page, output_dir, "10_recherche_aucun_resultat", step, total)

        step += 1
        await _click_tab(page, 1)
        await _screenshot(page, output_dir, "11_historique_avec_donnees", step, total)

        await browser.close()

        # =============================================================
        # Pass 2: Dark theme (phase 3) — restart server with dark DB
        # =============================================================
        print("\n--- Phase 3: Dark theme (restarting server) ---")

        # Stop current server
        _stop_server(proc_holder[0])

        # Rebuild temp DB with dark theme + auto-load enabled
        prepare_temp_db(dark_theme=True)

        # Restart server
        proc_holder[0] = launch_flet_server(use_temp_db=True)
        if not wait_for_server():
            print("ERROR: Server restart failed", file=sys.stderr)
            return

        browser, page = await _open_browser_and_wait(p)

        # Settings in dark mode
        step += 1
        await _click_tab(page, 5)
        await _screenshot(page, output_dir, "12_reglages_sombre", step, total)

        # Load an animal via shuffle button
        await _click_tab(page, 0)
        await _click(page, *COORDS["shuffle_btn"], delay=ANIMAL_LOAD_DELAY)

        step += 1
        await _click_tab(page, 0)
        await _screenshot(page, output_dir, "13_accueil_sombre", step, total)

        await _click_tab(page, 3)
        await _type_in_search(page, "panthera")

        step += 1
        await _screenshot(page, output_dir, "14_recherche_sombre", step, total)

        await browser.close()
        print(f"\nDone: {step} screenshots in {output_dir}/")


# =========================================================================
# Entry point
# =========================================================================


def main():
    quick_mode = "--quick" in sys.argv

    if not REAL_DB.exists():
        print(f"ERROR: Database not found: {REAL_DB}", file=sys.stderr)
        print("Run the setup commands first (see CLAUDE.md).", file=sys.stderr)
        sys.exit(1)

    if quick_mode:
        print("Quick mode: 6 tab screenshots\n")
        print("Launching Flet web server...")
        proc = launch_flet_server(use_temp_db=False)
        try:
            if not wait_for_server():
                print("ERROR: Server didn't start within 30s", file=sys.stderr)
                proc.terminate()
                sys.exit(1)
            print("Server ready.")
            asyncio.run(take_quick_screenshots())
        finally:
            _stop_server(proc)
    else:
        print("Full audit: 14 comprehensive screenshots\n")
        prepare_temp_db()
        print("Launching Flet web server (temp DB)...")
        proc = launch_flet_server(use_temp_db=True)
        # Mutable holder so take_full_screenshots can restart the server
        proc_holder = [proc]
        try:
            if not wait_for_server():
                print("ERROR: Server didn't start within 30s", file=sys.stderr)
                proc.terminate()
                sys.exit(1)
            print("Server ready.")
            asyncio.run(take_full_screenshots(proc_holder))
        finally:
            _stop_server(proc_holder[0])


if __name__ == "__main__":
    main()
