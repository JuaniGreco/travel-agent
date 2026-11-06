"""Flujo de navegación Universal Orlando / Loews (Cabana Bay, Sapphire Falls, Hard Rock).

Un mismo flujo sirve para los 3 hoteles: se parametriza con
    s.property_name, s.check_in, s.check_out, s.adults, s.rooms
Cómo calibrar:
    playwright codegen --target python --channel chrome https://www.universalorlando.com/web/en/us/places-to-stay
Hacer la búsqueda "Hotel only" (sin tickets) a mano y pegar los pasos en `pasos_grabados`.
Terminar en la pantalla con la lista de habitaciones y tarifas.
"""
from __future__ import annotations

from tracker.models import Search
from tracker.runner import FlowNotCalibrated

from ._helpers import month_label, pause, us_date  # noqa: F401


def run(page, s: Search) -> None:
    page.goto(s.start_url, wait_until="domcontentloaded")
    pause(page, 2, 4)
    pasos_grabados(page, s)


def pasos_grabados(page, s: Search) -> None:
    # --- Pegar acá los pasos de `playwright codegen` ---------------------------
    # Ejemplo orientativo:
    # page.get_by_role("link", name="Book a Hotel").click(); pause(page)
    # page.get_by_label("Hotel").select_option(label=s.property_name)
    # (date picker) navegar hasta month_label(s.check_in) y click en el día s.check_in.day
    # page.get_by_label("Adults").fill(str(s.adults))
    # page.get_by_role("button", name="Search").click()
    raise FlowNotCalibrated("grabar pasos de Universal en flows/universal.py (playwright codegen)")

