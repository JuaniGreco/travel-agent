"""Flujo de navegación Avis: búsqueda one-way MIA -> U2S.

Cómo calibrar (una sola vez, ver README):
    playwright codegen --target python --channel chrome https://www.avis.com/en/home
Hacer la búsqueda a mano, copiar las líneas generadas (page.get_by_...) dentro de
`pasos_grabados` y reemplazar los valores fijos por los de `s`:
    s.pickup_location ("MIA"), s.dropoff_location ("U2S"),
    us_date(s.pickup_at), us_time(s.pickup_at), us_date(s.dropoff_at), us_time(s.dropoff_at)
Terminar en la pantalla de resultados de vehículos: el precio lo captura el interceptor.
"""
from __future__ import annotations

from tracker.models import Search
from tracker.runner import FlowNotCalibrated

from ._helpers import pause, type_human, us_date, us_time  # noqa: F401


def run(page, s: Search) -> None:
    page.goto(s.start_url, wait_until="domcontentloaded")
    pause(page, 2, 4)
    pasos_grabados(page, s)


def pasos_grabados(page, s: Search) -> None:
    # --- Pegar acá los pasos de `playwright codegen` ---------------------------
    # Ejemplo orientativo (los nombres reales salen de codegen):
    # type_human(page.get_by_label("Pick-up Location"), s.pickup_location)
    # page.get_by_text("Miami International Airport").first.click(); pause(page)
    # page.get_by_label("Return to a different location").check()
    # type_human(page.get_by_label("Return Location"), s.dropoff_location)
    # ...
    # page.get_by_role("button", name="Select My Car").click()
    raise FlowNotCalibrated("grabar pasos de Avis en flows/avis.py (playwright codegen)")

