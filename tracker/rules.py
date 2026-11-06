"""Reglas de decisión del agente: comparan precios contra el presupuesto base y generan alertas."""
from __future__ import annotations

from typing import Optional

from .models import Alert, CarRule, HotelGroup, SearchResult


def usd(value: Optional[float]) -> str:
    return "—" if value is None else f"${value:,.0f}"


def _ok(results: dict[str, SearchResult], search_id: Optional[str]) -> Optional[float]:
    """Precio válido (con coincidencia de habitación/vehículo) o None."""
    if not search_id:
        return None
    r = results.get(search_id)
    if r is None or r.error or not r.matched or r.price is None:
        return None
    return r.price


def evaluate(
    results: dict[str, SearchResult],
    hotel_groups: list[HotelGroup],
    car_rules: list[CarRule],
    tolerance: float = 400,
    suspicious_ratio: float = 0.5,
    historical_min: Optional[dict[str, float]] = None,
    expedia_min_saving: float = 500.0,
) -> list[Alert]:
    historical_min = historical_min or {}
    alerts: list[Alert] = []

    def suspicious(price: float, base: Optional[float]) -> bool:
        return bool(base) and price < base * suspicious_ratio

    # Auto
    for rule in car_rules:
        price = _ok(results, rule.search)
        if price is not None and price < rule.base_usd:
            alerts.append(Alert(
                "AHORRO DIRECTO", rule.label,
                f"Total {usd(price)} vs base {usd(rule.base_usd)} → ahorro {usd(rule.base_usd - price)}",
                suspicious(price, rule.base_usd)))

    # Hoteles
    for g in hotel_groups:
        quad = _ok(results, g.quad_search)
        double = _ok(results, g.double_search)
        upgrade = _ok(results, g.upgrade_search)
        base = g.base_usd

        # Regla 1: ahorro directo (o mínimo histórico si no hay base)
        if quad is not None:
            if base is not None:
                if quad < base:
                    alerts.append(Alert(
                        "AHORRO DIRECTO", g.label,
                        f"1 hab. cuádruple {usd(quad)} vs base {usd(base)} → ahorro {usd(base - quad)}",
                        suspicious(quad, base)))
            else:
                prev = historical_min.get(g.quad_search)
                if prev is not None and quad < prev:
                    alerts.append(Alert(
                        "MÍNIMO HISTÓRICO", g.label,
                        f"1 hab. cuádruple {usd(quad)} (mínimo anterior {usd(prev)}, baja {usd(prev - quad)})"))

        # Regla 2: privacidad (2 habitaciones dobles)
        ref = base if base is not None else quad
        if double is not None and ref is not None:
            two_rooms = round(double * 2, 2)
            limit = ref + tolerance
            if two_rooms <= limit:
                ref_txt = f"base {usd(ref)}" if base is not None else f"1 hab. actual {usd(ref)}"
                alerts.append(Alert(
                    "PRIVACIDAD", g.label,
                    f"2 hab. dobles = {usd(two_rooms)} (2 × {usd(double)}) ≤ {ref_txt} + {usd(tolerance)} "
                    f"= {usd(limit)} → diferencia vs base {usd(two_rooms - ref)}",
                    suspicious(two_rooms, ref)))

        # Regla 3: upgrade
        if upgrade is not None and base is not None and upgrade <= base:
            alerts.append(Alert(
                "UPGRADE", g.label,
                f"{g.upgrade_label}: {usd(upgrade)} ≤ base actual {usd(base)} → diferencia {usd(base - upgrade)} a favor",
                suspicious(upgrade, base)))

        # Regla 4: Expedia / OTA (alerta solo si el ahorro supera el umbral de $500 USD)
        expedia = _ok(results, g.expedia_search)
        if expedia is not None and base is not None:
            ahorro = base - expedia
            if ahorro >= expedia_min_saving:
                alerts.append(Alert(
                    "AHORRO EXPEDIA", f"{g.label} (Expedia)",
                    f"Habitación cuádruple {usd(expedia)} vs base oficial {usd(base)} → "
                    f"ahorro de {usd(ahorro)} (supera umbral de ${expedia_min_saving:,.0f} USD)",
                    suspicious(expedia, base)))

    return alerts

