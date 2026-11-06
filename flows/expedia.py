"""Flujo de navegación Expedia: búsqueda directa por URL parametrizada.

Carga la búsqueda con destino, fechas y adultos, cierra banners
y espera la carga de tarjetas de tarifas para que el JsonInterceptor
capture los payloads de precios.
"""
from __future__ import annotations

import logging
from tracker.models import Search
from tracker.runner import FlowNotCalibrated

from ._helpers import dismiss_cookie_banner, pause

logger = logging.getLogger("flows.expedia")


def run(page, s: Search) -> None:
    page.goto(s.start_url, wait_until="domcontentloaded")
    pause(page, 3.0, 5.0)
    dismiss_cookie_banner(page)
    pasos_grabados(page, s)


def pasos_grabados(page, s: Search) -> None:
    try:
        # Cerrar posibles modales de registro o promociones de Expedia
        close_modal = page.locator("button[aria-label*='Close' i], button:has-text('Dismiss'), button:has-text('Not now')").first
        if close_modal.is_visible(timeout=2000):
            close_modal.click()
            pause(page, 0.5, 1.0)

        # Scroll suave para activar la carga dinámica de tarjetas y tarifas (lazy loading)
        page.mouse.wheel(0, 400)
        pause(page, 1.0, 2.0)
        page.mouse.wheel(0, 400)
        pause(page, 1.0, 2.0)

    except Exception as exc:
        if isinstance(exc, FlowNotCalibrated):
            raise
        # En Expedia, la búsqueda ya viene en la start_url; un error de scroll no es crítico
        logger.debug(f"Aviso durante navegación de Expedia: {exc}")
