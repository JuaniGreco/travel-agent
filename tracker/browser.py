"""Contexto de navegador persistente (cookies/sesión reales = menos fricción anti-bot)."""
from __future__ import annotations

from pathlib import Path

PROFILE_DIR = Path(__file__).resolve().parent.parent / ".browser_profile"


def open_context(playwright, headless: bool, channel: str | None):
    kwargs = dict(
        user_data_dir=str(PROFILE_DIR),
        headless=headless,
        locale="en-US",
        timezone_id="America/New_York",
        viewport={"width": 1366, "height": 860},
        args=["--disable-blink-features=AutomationControlled"],
    )
    if channel:
        try:
            return playwright.chromium.launch_persistent_context(channel=channel, **kwargs)
        except Exception as exc:  # Chrome no instalado => Chromium de Playwright
            print(f"[browser] No se pudo abrir channel={channel!r} ({exc}); uso Chromium.")
    return playwright.chromium.launch_persistent_context(**kwargs)

