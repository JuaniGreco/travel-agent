"""Utilidades para flujos grabados con `playwright codegen`."""
from __future__ import annotations

import random
from datetime import date, datetime


def pause(page, a: float = 0.6, b: float = 1.8) -> None:
    """Pausa humana aleatoria entre acciones."""
    page.wait_for_timeout(int(random.uniform(a, b) * 1000))


def type_human(locator, text: str) -> None:
    """Escribe con delay por tecla (algunos autocompletes lo necesitan)."""
    locator.click()
    locator.press_sequentially(text, delay=random.randint(60, 140))


def us_date(d: date | datetime) -> str:
    """03/05/2027 -> '05/03/2027' (formato MM/DD/YYYY de sitios de EE.UU.)."""
    return d.strftime("%m/%d/%Y")


def iso_date(d: date | datetime) -> str:
    return d.strftime("%Y-%m-%d")


def us_time(dt: datetime) -> str:
    """07:00 -> '7:00 AM'; 16:00 -> '4:00 PM'."""
    return dt.strftime("%I:%M %p").lstrip("0")


def month_label(d: date | datetime) -> str:
    """'May 2027' (útil para navegar date pickers)."""
    return d.strftime("%B %Y")

