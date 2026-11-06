"""Contexto de navegador persistente con higiene de cookies y anti-rastreo."""
from __future__ import annotations

from pathlib import Path

PROFILE_DIR = Path(__file__).resolve().parent.parent / ".browser_profile"


def open_context(playwright, headless: bool, channel: str | None, clean_cookies: bool = True):
    """Abre un contexto de navegador Chrome real con protección anti-detección.

    Args:
        clean_cookies: Si es True, limpia las cookies al iniciar para evitar que
            los sitios rastreen búsquedas repetidas o apliquen precios dinámicos inflados.
    """
    kwargs = dict(
        user_data_dir=str(PROFILE_DIR),
        headless=headless,
        locale="en-US",
        timezone_id="America/New_York",
        viewport={"width": 1366, "height": 860},
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
        ],
    )
    context = None
    if channel:
        try:
            context = playwright.chromium.launch_persistent_context(channel=channel, **kwargs)
        except Exception as exc:  # Chrome no instalado => Chromium de Playwright
            print(f"[browser] No se pudo abrir channel={channel!r} ({exc}); uso Chromium.")

    if context is None:
        context = playwright.chromium.launch_persistent_context(**kwargs)

    if clean_cookies:
        try:
            context.clear_cookies()
        except Exception:
            pass

    return context
