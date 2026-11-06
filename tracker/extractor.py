"""Extracción heurística de ofertas (descripción + precio) desde payloads JSON arbitrarios.

Las APIs internas de Avis/Universal/Disney no están documentadas y cambian, así que en lugar
de depender de una ruta JSON fija se recorre el árbol buscando objetos que tengan:
  - una clave de precio (total/price/amount/rate/...) con valor numérico, y
  - textos descriptivos (name/title/description/roomType/vehicle/...) propios o de sus ancestros.
Si tras `discover` se conoce la clave exacta, se fija con `Search.price_key_regex`.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Optional

from .models import Offer, Search

PRICE_KEY = re.compile(r"total|price|amount|rate|cost|fare|charge", re.I)
EXCLUDE_KEY = re.compile(
    r"discount|saving|strike|was|original|before|regular|points|percent|pct|count|qty|quantity|"
    r"number|rating|score|review|deposit|code|id$|index|max|min|limit|occupan|adult|child|"
    r"exchange|conversion|miles|duration|distance|mileage|km",
    re.I,
)
TAX_FEE_KEY = re.compile(r"tax|fee|surcharge", re.I)
INCL_TAX_KEY = re.compile(r"(with|incl|including|plus|after|grand)[_\s-]?(tax|fee)|grand.?total|all.?in", re.I)
NIGHTLY_KEY = re.compile(r"night|daily|per.?day|perday|avg|average|base.?rate", re.I)
TOTAL_KEY = re.compile(r"total|grand", re.I)
LABEL_KEY = re.compile(
    r"name|title|desc|room.?type|roomtype|vehicle|make|model|class|category|type|label|bed|view|group",
    re.I,
)
MONEY_STR = re.compile(
    r"^\s*(?:US)?\$?\s*(\d{1,3}(?:,\d{3})+|\d+)(\.\d{1,2})?\s*(?:USD)?(?:\s*(?:total|per\s*night|\/night|\/day))?\s*$",
    re.I,
)
AMOUNT_SUBKEY = re.compile(r"^(amount|value|price|total|usd|amt|raw|numeric)$", re.I)


def _to_number(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace("\xa0", " ").strip()
        m = MONEY_STR.match(cleaned)
        if m:
            return float(m.group(1).replace(",", "") + (m.group(2) or ""))
    return None


def _classify(path: str) -> Optional[tuple[int, bool, bool]]:
    """Devuelve (prioridad, nightly, incluye_impuestos) o None si la clave no es un precio."""
    if not PRICE_KEY.search(path):
        return None
    includes_tax = bool(INCL_TAX_KEY.search(path))
    if TAX_FEE_KEY.search(path) and not includes_tax:
        return None
    if EXCLUDE_KEY.search(path.replace("grand", "")):
        return None
    nightly = bool(NIGHTLY_KEY.search(path)) and not TOTAL_KEY.search(path)
    if includes_tax:
        prio = 0
    elif TOTAL_KEY.search(path) and not nightly:
        prio = 1
    elif not nightly:
        prio = 2
    else:
        prio = 3
    return prio, nightly, includes_tax


def _dedupe(items: Iterable[str]) -> list[str]:
    seen, out = set(), []
    for it in items:
        key = it.lower()
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out


def iter_offers(data: Any, url: str = "", price_key_regex: Optional[str] = None) -> list[Offer]:
    """Recorre el JSON y devuelve todas las ofertas candidatas (1 por objeto con precio)."""
    key_filter = re.compile(price_key_regex, re.I) if price_key_regex else None
    offers: list[Offer] = []

    def walk(node: Any, labels: list[str], parent_key: str, depth: int) -> None:
        if depth > 40:
            return
        if isinstance(node, list):
            for item in node:
                walk(item, labels, parent_key, depth + 1)
            return
        if not isinstance(node, dict):
            return

        own = [v.strip() for k, v in node.items()
               if isinstance(v, str) and LABEL_KEY.search(k) and 2 < len(v.strip()) <= 150
               and not v.strip().startswith(("http", "/"))]
        ctx = labels + own

        cands: list[tuple[str, float]] = []
        for k, v in node.items():
            num = _to_number(v)
            if num is not None:
                cands.append((f"{parent_key}.{k}" if parent_key else k, num))
            elif isinstance(v, dict):  # {"amount": 123, "currency": "USD"}
                for k2, v2 in v.items():
                    n2 = _to_number(v2)
                    if n2 is not None and AMOUNT_SUBKEY.match(k2):
                        cands.append((f"{k}.{k2}", n2))

        best: Optional[tuple[int, float, str, bool, bool]] = None
        for path, num in cands:
            if key_filter and not key_filter.search(path):
                continue
            cls = _classify(path) if not key_filter else (_classify(path) or (2, False, False))
            if cls is None or num <= 0:
                continue
            prio, nightly, incl = cls
            # mejor prioridad; a igual prioridad, el mayor (total con cargos > subtotal)
            if best is None or prio < best[0] or (prio == best[0] and num > best[1]):
                best = (prio, num, path, nightly, incl)
        if best is not None:
            offers.append(Offer(label=" | ".join(_dedupe(ctx)[-8:]), raw_price=best[1], price_key=best[2],
                                nightly=best[3], includes_tax=best[4], url=url))

        for k, v in node.items():
            if isinstance(v, (dict, list)):
                walk(v, ctx, k, depth + 1)

    walk(data, [], "", 0)
    return offers


def offer_total(offer: Offer, search: Search) -> float:
    """Convierte el precio crudo a total de la estadía/alquiler en USD con impuestos estimados."""
    price = offer.raw_price
    nightly = offer.nightly if search.price_mode == "auto" else search.price_mode == "nightly"
    if nightly:
        price *= search.units
    if not (search.prices_include_tax or offer.includes_tax):
        price *= 1 + search.tax_rate
    return round(price, 2)


def matches(offer: Offer, search: Search) -> bool:
    text = offer.label
    if not any(re.search(k, text, re.I) for k in search.offer_keywords):
        return False
    return not any(re.search(k, text, re.I) for k in search.exclude_keywords)


def select_best(payloads, search: Search):
    """Devuelve (mejor_oferta_que_coincide, total, mas_barata_cualquiera, total_cualquiera)."""
    best = best_total = any_best = any_total = None
    for p in payloads:
        for offer in iter_offers(p.data, p.url, search.price_key_regex):
            total = offer_total(offer, search)
            if not (search.min_price <= total <= search.max_price):
                continue
            if any_total is None or total < any_total:
                any_best, any_total = offer, total
            if matches(offer, search) and (best_total is None or total < best_total):
                best, best_total = offer, total
    return best, best_total, any_best, any_total

