"""Flujo de navegación Walt Disney World (Pop Century, Caribbean Beach).

`s.start_url` ya apunta a la página del resort. Parametrizar con
    s.check_in, s.check_out, s.adults
Cómo calibrar:
    playwright codegen --target python --channel chrome https://disneyworld.disney.go.com/resorts/pop-century-resort/
Ir a "Check Rates" / "Rooms & Rates", elegir fechas y 4 (o 2) adultos, "Find Rates".
Terminar en la lista de habitaciones (Room Only, sin tickets).
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
    # page.get_by_role("link", name="Check Rates").click(); pause(page)
    # page.get_by_label("Check-in").fill(us_date(s.check_in))
    # page.get_by_label("Check-out").fill(us_date(s.check_out))
    # page.get_by_label("Adults").select_option(str(s.adults))
    # page.get_by_role("button", name="Find Rates").click()
    raise FlowNotCalibrated("grabar pasos de Disney en flows/disney.py (playwright codegen)")

