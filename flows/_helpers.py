"""Utilidades comunes para los flujos de navegación interactivos."""
from __future__ import annotations

import random
from datetime import date, datetime
from typing import Optional


def pause(page, a: float = 0.8, b: float = 2.0) -> None:
    """Pausa humana aleatoria entre acciones."""
    page.wait_for_timeout(int(random.uniform(a, b) * 1000))


def type_human(locator, text: str) -> None:
    """Escribe texto con delay variable por pulsación para emular tecleo humano."""
    locator.click()
    locator.press_sequentially(text, delay=random.randint(65, 130))


def dismiss_cookie_banner(page, timeout_ms: int = 3000) -> bool:
    """Detecta y cierra banners de cookies o consentimientos (OneTrust, TrustArc, etc.)."""
    common_selectors = [
        "#onetrust-accept-btn-handler",
        "button[id*='accept-cookie']",
        "button[id*='onetrust-accept']",
        "button:has-text('Accept All')",
        "button:has-text('Accept All Cookies')",
        "button:has-text('Accept Cookies')",
        "button:has-text('I Agree')",
        "button:has-text('Allow All')",
        "button:has-text('Aceptar todas')",
    ]
    for sel in common_selectors:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=timeout_ms // len(common_selectors)):
                btn.click()
                pause(page, 0.5, 1.0)
                return True
        except Exception:
            continue
    return False


def select_autocomplete_option(
    page,
    input_locator,
    text: str,
    suggestion_selector: str,
    match_text: Optional[str] = None,
) -> bool:
    """Escribe en un campo de autocompletado y selecciona la opción coincidente."""
    type_human(input_locator, text)
    pause(page, 1.0, 2.0)
    try:
        suggestions = page.locator(suggestion_selector)
        suggestions.first.wait_for(state="visible", timeout=4000)
        if match_text:
            matching = suggestions.filter(has_text=match_text).first
            if matching.is_visible():
                matching.click()
                return True
        suggestions.first.click()
        return True
    except Exception:
        # Fallback: presionar Flecha Abajo y Enter
        input_locator.press("ArrowDown")
        pause(page, 0.2, 0.5)
        input_locator.press("Enter")
        return False


def us_date(d: date | datetime) -> str:
    """Formato MM/DD/YYYY utilizado por formularios de EE.UU."""
    return d.strftime("%m/%d/%Y")


def iso_date(d: date | datetime) -> str:
    return d.strftime("%Y-%m-%d")


def us_time(dt: datetime) -> str:
    """07:00 -> '7:00 AM'; 16:00 -> '4:00 PM'."""
    return dt.strftime("%I:%M %p").lstrip("0")


def month_label(d: date | datetime) -> str:
    """'May 2027'."""
    return d.strftime("%B %Y")
