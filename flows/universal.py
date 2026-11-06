"""Flujo de navegación Universal Orlando / Loews Hotels (Cabana Bay, Sapphire Falls, Hard Rock).

Automatiza la selección de hotel, fechas y huéspedes asegurando la tarifa
'Room Only' (solo habitación, sin tickets de parque).
"""
from __future__ import annotations

import logging
from tracker.models import Search
from tracker.runner import FlowNotCalibrated

from ._helpers import dismiss_cookie_banner, iso_date, month_label, pause, type_human, us_date

logger = logging.getLogger("flows.universal")


def run(page, s: Search) -> None:
    page.goto(s.start_url, wait_until="domcontentloaded")
    pause(page, 2.5, 4.0)
    dismiss_cookie_banner(page)
    pasos_grabados(page, s)


def pasos_grabados(page, s: Search) -> None:
    try:
        # 1. Abrir widget de reserva o buscar el hotel
        book_widget_btn = page.locator(
            "button:has-text('Check Availability'), a:has-text('Book a Hotel'), button:has-text('Book a Hotel'), a[aria-label*='Book a Hotel' i]"
        ).first

        if book_widget_btn.is_visible(timeout=4000):
            book_widget_btn.click()
            pause(page, 1.0, 2.0)

        # 2. Selector de Hotel (si está presente en el widget)
        hotel_dropdown = page.locator(
            "select[name*='hotel' i], select[id*='hotel' i], [aria-label*='Select Hotel' i], button:has-text('Select a Hotel')"
        ).first

        if hotel_dropdown.is_visible(timeout=3000):
            try:
                hotel_dropdown.select_option(label=s.property_name)
            except Exception:
                hotel_dropdown.click()
                pause(page, 0.5, 1.0)
                matching_option = page.locator(f"text={s.property_name}").first
                if matching_option.is_visible():
                    matching_option.click()
        else:
            # Estrategia alternativa: buscar la tarjeta específica del hotel en la página
            short_name = s.property_name.replace("Universal's ", "").replace(" Resort", "")
            hotel_card = page.locator(f"div:has-text('{short_name}')").first
            if hotel_card.is_visible():
                card_btn = hotel_card.locator("a:has-text('Book'), a:has-text('Check Rates'), button:has-text('Book')").first
                if card_btn.is_visible():
                    card_btn.click()
                    pause(page, 1.5, 3.0)

        # 3. Selección de Fechas
        if s.check_in and s.check_out:
            ci_str = us_date(s.check_in)
            co_str = us_date(s.check_out)

            ci_input = page.locator("input[placeholder*='Check-in' i], input[name*='checkIn' i], input[id*='checkIn' i]").first
            if ci_input.is_visible(timeout=3000):
                ci_input.click()
                ci_input.fill(ci_str)
                pause(page, 0.5, 1.0)

            co_input = page.locator("input[placeholder*='Check-out' i], input[name*='checkOut' i], input[id*='checkOut' i]").first
            if co_input.is_visible(timeout=3000):
                co_input.click()
                co_input.fill(co_str)
                pause(page, 0.5, 1.0)

        # 4. Cantidad de Adultos (4 o 2)
        adults_selector = page.locator(
            "select[name*='adult' i], select[id*='adult' i], [aria-label*='Adults' i]"
        ).first
        if adults_selector.is_visible(timeout=3000):
            try:
                adults_selector.select_option(str(s.adults))
            except Exception:
                pass

        pause(page, 1.0, 2.0)

        # 5. Ejecutar búsqueda
        search_btn = page.locator(
            "button:has-text('Search'), button:has-text('Find Rates'), button:has-text('Check Rates'), button[type='submit']"
        ).first
        if search_btn.is_visible(timeout=4000):
            search_btn.click()
        else:
            raise FlowNotCalibrated("No se encontró el botón de búsqueda de tarifas en Universal.")

    except Exception as exc:
        if isinstance(exc, FlowNotCalibrated):
            raise
        raise FlowNotCalibrated(f"Universal requiere ajuste en flows/universal.py: {exc}")
