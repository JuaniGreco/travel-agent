"""Flujo de navegación Avis: búsqueda one-way MIA -> Cabana Bay (U2S).

Utiliza selectores resilientes y pausas humanas para completar el formulario
y desencadenar las respuestas JSON de tarifas de vehículos.
"""
from __future__ import annotations

import logging
from tracker.models import Search
from tracker.runner import FlowNotCalibrated

from ._helpers import dismiss_cookie_banner, pause, select_autocomplete_option, type_human, us_date, us_time

logger = logging.getLogger("flows.avis")


def run(page, s: Search) -> None:
    page.goto(s.start_url, wait_until="domcontentloaded")
    pause(page, 2.5, 4.0)
    dismiss_cookie_banner(page)
    pasos_grabados(page, s)


def pasos_grabados(page, s: Search) -> None:
    try:
        # 1. Ubicación de Pick-up (MIA)
        pic_input = page.locator("#pic-loc, input[name='pickupLocation'], input[aria-label*='Pick-up' i]").first
        if not pic_input.is_visible(timeout=5000):
            raise FlowNotCalibrated("No se visualizó el campo Pick-up Location en Avis.")

        select_autocomplete_option(
            page,
            pic_input,
            s.pickup_location,
            suggestion_selector=".angucomplete-row, .location-suggestion, [role='option'], .angucomplete-title",
            match_text="Miami",
        )
        pause(page, 1.0, 2.0)

        # 2. Activar devolución en ubicación diferente (One-Way)
        diff_checkbox = page.locator(
            "#res-home-drop-off, input[name='different-dropoff'], label:has-text('Return to a different location')"
        ).first
        if diff_checkbox.is_visible():
            diff_checkbox.click()
            pause(page, 0.8, 1.5)

        # 3. Ubicación de Drop-off (U2S - Cabana Bay Resort)
        drop_input = page.locator("#drop-loc, input[name='dropoffLocation'], input[aria-label*='Drop-off' i], input[aria-label*='Return' i]").first
        if drop_input.is_visible(timeout=4000):
            select_autocomplete_option(
                page,
                drop_input,
                s.dropoff_location,
                suggestion_selector=".angucomplete-row, .location-suggestion, [role='option'], .angucomplete-title",
                match_text="Cabana",
            )
            pause(page, 1.0, 1.8)

        # 4. Fechas (Pick-up y Drop-off)
        if s.pickup_at and s.dropoff_at:
            p_date = us_date(s.pickup_at)
            d_date = us_date(s.dropoff_at)

            from_input = page.locator("#from, input[name='from'], input[aria-label*='Pick-up Date' i]").first
            if from_input.is_visible():
                from_input.click()
                from_input.fill(p_date)
                pause(page, 0.5, 1.0)

            to_input = page.locator("#to, input[name='to'], input[aria-label*='Drop-off Date' i], input[aria-label*='Return Date' i]").first
            if to_input.is_visible():
                to_input.click()
                to_input.fill(d_date)
                pause(page, 0.5, 1.0)

            # 5. Horarios (07:00 AM y 16:00 / 4:00 PM)
            p_time = us_time(s.pickup_at)
            d_time = us_time(s.dropoff_at)

            p_time_select = page.locator("select[name='pic-time'], select#pic-time, select[aria-label*='Pick-up Time' i]").first
            if p_time_select.is_visible():
                try:
                    p_time_select.select_option(label=p_time)
                except Exception:
                    pass

            d_time_select = page.locator("select[name='drop-time'], select#drop-time, select[aria-label*='Drop-off Time' i]").first
            if d_time_select.is_visible():
                try:
                    d_time_select.select_option(label=d_time)
                except Exception:
                    pass

        pause(page, 1.0, 2.0)

        # 6. Click en 'Select My Car' / Buscar
        search_btn = page.locator(
            "#res-home-select-car, button:has-text('Select My Car'), button:has-text('Find a Car'), button[type='submit']"
        ).first
        if search_btn.is_visible():
            search_btn.click()
        else:
            raise FlowNotCalibrated("Botón de búsqueda en Avis no encontrado.")

    except Exception as exc:
        if isinstance(exc, FlowNotCalibrated):
            raise
        raise FlowNotCalibrated(f"Avis requiere ajuste en flows/avis.py: {exc}")
