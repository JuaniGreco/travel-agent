"""Orquestación de una búsqueda: navegar (flows/) + interceptar JSON + extraer precio."""
from __future__ import annotations

import importlib
import random
import time
from pathlib import Path

from .extractor import select_best
from .interceptor import JsonInterceptor
from .models import Search, SearchResult

ROOT = Path(__file__).resolve().parent.parent
CAPTURAS = ROOT / "capturas"


class FlowNotCalibrated(RuntimeError):
    """El flujo de navegación del sitio todavía no fue grabado (ver README)."""


def get_flow(site: str):
    return importlib.import_module(f"flows.{site}")


def wait_for_offers(page, interceptor: JsonInterceptor, search: Search, timeout_s: float, settle_s: float):
    """Espera hasta tener una oferta que coincida y que dejen de llegar payloads (o timeout)."""
    deadline = time.time() + timeout_s
    checked = 0
    found = False
    while time.time() < deadline:
        page.wait_for_timeout(1000)
        if len(interceptor.payloads) != checked:
            checked = len(interceptor.payloads)
            found = select_best(interceptor.payloads, search)[0] is not None
        if found and time.time() - interceptor.last_capture_ts >= settle_s:
            return


def run_search(context, search: Search, timeout_s: float, settle_s: float, save_payloads: bool) -> SearchResult:
    result = SearchResult(search_id=search.id)
    interceptor = JsonInterceptor(search.url_patterns)
    page = context.new_page()
    interceptor.attach(page)
    try:
        flow = get_flow(search.site)
        flow.run(page, search)
        wait_for_offers(page, interceptor, search, timeout_s, settle_s)
    except FlowNotCalibrated as exc:
        result.error = f"Flujo sin calibrar: {exc}"
    except Exception as exc:
        result.error = f"{type(exc).__name__}: {str(exc).splitlines()[0][:150]}"
        try:
            (CAPTURAS / "errores").mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(CAPTURAS / "errores" / f"{search.id}.png"))
        except Exception:
            pass
    finally:
        interceptor.detach(page)

    result.payloads = len(interceptor.payloads)
    if save_payloads and interceptor.payloads:
        interceptor.dump(CAPTURAS / "ultima" / search.id)

    best, total, any_best, any_total = select_best(interceptor.payloads, search)
    result.cheapest_any, result.cheapest_any_price = any_best, any_total
    if best is not None:
        result.offer, result.price, result.matched = best, total, True
        result.error = None  # si hubo precio válido, el error de navegación no importa
    elif result.error is None and not interceptor.payloads:
        result.error = "No se capturaron payloads JSON (¿bloqueo o URL patterns incorrectos?)"
    try:
        page.close()
    except Exception:
        pass
    return result


def human_pause(range_s: tuple[float, float]) -> None:
    time.sleep(random.uniform(*range_s))

