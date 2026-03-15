"""Automated UI screenshot tool using Playwright + Flet web mode.

Launches the Daynimal app as a web server, then uses a headless browser
to navigate each tab and capture screenshots.

Usage:
    uv run python scripts/screenshot_ui.py
"""

import asyncio
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


def launch_flet_server():
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

    proc = subprocess.Popen(
        ["uv", "run", "python", "-c", launcher_code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
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


async def take_screenshots():
    """Navigate through all tabs and capture screenshots."""
    from playwright.async_api import async_playwright

    output_dir = Path("tmp/screenshots")
    output_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
            device_scale_factor=2,  # High-DPI for better quality
        )
        page = await context.new_page()

        print(f"Opening http://localhost:{PORT} ...")
        await page.goto(f"http://localhost:{PORT}")

        # Flutter Web (CanvasKit) needs time to download WASM + render
        print(f"Waiting {FLUTTER_LOAD_TIMEOUT // 1000}s for Flutter to render...")
        await page.wait_for_timeout(FLUTTER_LOAD_TIMEOUT)

        # Screenshot: Decouverte (first tab, auto-loaded)
        await page.screenshot(path=str(output_dir / "01_decouverte.png"))
        print("  [1/6] Decouverte")

        # 6 tabs in bottom navbar, spread across viewport width
        # Each tab occupies VIEWPORT_WIDTH / 6 pixels
        tab_width = VIEWPORT_WIDTH / 6
        tab_y = VIEWPORT_HEIGHT - 28  # Center of bottom navbar

        tabs = [
            # (filename, tab_index) - index 0 = leftmost tab
            ("02_historique", 1),
            ("03_favoris", 2),
            ("04_recherche", 3),
            ("05_stats", 4),
            ("06_parametres", 5),
        ]

        for name, index in tabs:
            x = tab_width * index + tab_width / 2
            await page.mouse.click(x, tab_y)
            await page.wait_for_timeout(TAB_SWITCH_DELAY)
            await page.screenshot(path=str(output_dir / f"{name}.png"))
            print(f"  [{index + 1}/6] {name}")

        await browser.close()
        print(f"\nScreenshots saved to {output_dir}/")


def main():
    print("Launching Flet web server...")
    proc = launch_flet_server()

    try:
        if not wait_for_server():
            print("ERROR: Flet server didn't start within 30s", file=sys.stderr)
            proc.terminate()
            sys.exit(1)

        print("Server ready.\n")
        asyncio.run(take_screenshots())
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
