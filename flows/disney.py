"""Flujo de navegación Walt Disney World (Pop Century, Caribbean Beach).

Navega a la ficha del resort, activa el buscador de tarifas 'Room Only',
completa las fechas y cantidad de huéspedes (4 o 2 adultos) y dispara
la consulta de disponibilidad que intercepta el JsonInterceptor.
"""
from __future__ import annotations

import logging
from tracker.models import Search
from tracker.runner import FlowNotCalibrated

from ._helpers import dismiss_cookie_banner, pause, type_human, us_date

logger = logging.getLogger("flows.disney")


def run(page, s: Search) -> None:
    page.goto(s.start_url, wait_until="domcontentloaded")
    pause(page, 2.5, 4.0)
    dismiss_cookie_banner(page)
    pasos_grabados(page, s)


def pasos_grabados(page, s: Search) -> None:
    try:
        # 1. Abrir panel o botón de 'Check Rates' / 'Rooms & Rates'
        rates_btn = page.locator(
            "button:has-text('Check Rates'), a:has-text('Check Rates'), a:has-text('Rooms & Rates'), button:has-text('Check Availability'), a[href*='rates-rooms' i]"
        ).first

        if rates_btn.is_visible(timeout=4000):
            rates_btn.click()
            pause(page, 1.5, 2.5)

        # 2. Fechas de Check-in y Check-out
        if s.check_in and s.check_out:
            ci_str = us_date(s.check_in)
            co_str = us_date(s.check_out)

            ci_input = page.locator(
                "input[placeholder*='Check-in' i], input[id*='checkIn' i], input[name*='checkIn' i], input[aria-label*='Check-in' i]"
            ).first
            if ci_input.is_visible(timeout=3000):
                ci_input.click()
                ci_input.fill(ci_str)
                pause(page, 0.5, 1.0)

            co_input = page.locator(
                "input[placeholder*='Check-out' i], input[id*='checkOut' i], input[name*='checkOut' i], input[aria-label*='Check-out' i]"
            ).first
            if co_input.is_visible(timeout=3000):
                co_input.click()
                co_input.fill(co_str)
                pause(page, 0.5, 1.0)

        # 3. Cantidad de Adultos (4 o 2)
        adults_input = page.locator(
            "select[name*='adult' i], select[id*='adult' i], [aria-label*='Adults' i], select[aria-label*='Adult' i]"
        ).first

        if adults_input.is_visible(timeout=3000):
            try:
                adults_input.select_option(str(s.adults))
            except Exception:
                pass

        pause(page, 1.0, 2.0)

        # 4. Botón de búsqueda de tarifas
        find_rates_btn = page.locator(
            "button:has-text('Find Rates'), button:has-text('Check Rates'), button:has-text('View Rates'), button:has-text('Update'), button[type='submit']"
        ).first

        if find_rates_btn.is_visible(timeout=4000):
            find_rates_btn.click()
        else:
            raise FlowNotCalibrated("No se encontró el botón 'Find Rates' en Disney World.")

    except Exception as exc:
        if isinstance(exc, FlowNotCalibrated):
            raise
        raise FlowNotCalibrated(f"Disney requiere ajuste en flows/disney.py: {exc}")
