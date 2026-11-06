"""Modelos de datos del tracker."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class Search:
    """Una búsqueda concreta en un sitio (un auto o un hotel con una ocupación)."""

    id: str
    site: str                      # "avis" | "universal" | "disney" (módulo en flows/)
    kind: str                      # "car" | "hotel"
    label: str
    start_url: str
    url_patterns: list[str]        # regex de URLs de respuestas JSON a capturar
    offer_keywords: list[str]      # regex: la oferta debe matchear alguna (habitación / vehículo)
    exclude_keywords: list[str] = field(default_factory=list)

    # Hotel
    property_name: str = ""
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    adults: int = 0
    rooms: int = 1

    # Auto
    pickup_location: str = ""
    dropoff_location: str = ""
    pickup_at: Optional[datetime] = None
    dropoff_at: Optional[datetime] = None

    # Interpretación del precio
    tax_rate: float = 0.0              # se suma si el precio capturado no incluye impuestos
    prices_include_tax: bool = True
    price_mode: str = "auto"           # "auto" | "total" | "nightly"
    price_key_regex: Optional[str] = None  # si se define, solo se usan claves JSON que matcheen
    min_price: float = 20.0
    max_price: float = 30000.0

    @property
    def units(self) -> int:
        """Noches (hotel) o días de alquiler (auto)."""
        if self.kind == "hotel" and self.check_in and self.check_out:
            return max((self.check_out - self.check_in).days, 1)
        if self.kind == "car" and self.pickup_at and self.dropoff_at:
            hours = (self.dropoff_at - self.pickup_at).total_seconds() / 3600
            return max(math.ceil(hours / 24), 1)
        return 1


@dataclass
class HotelGroup:
    """Hotel actual + búsquedas asociadas para aplicar las 3 reglas."""

    id: str
    label: str
    base_usd: Optional[float]
    quad_search: str                   # 1 habitación, 4 adultos
    double_search: Optional[str] = None  # 1 habitación, 2 adultos (se multiplica x2)
    upgrade_search: Optional[str] = None
    upgrade_label: str = ""


@dataclass
class CarRule:
    search: str
    label: str
    base_usd: float


@dataclass
class Offer:
    label: str
    raw_price: float
    price_key: str
    nightly: bool = False
    includes_tax: bool = False
    url: str = ""


@dataclass
class SearchResult:
    search_id: str
    price: Optional[float] = None          # total final en USD (con impuestos estimados)
    offer: Optional[Offer] = None
    matched: bool = False                  # la oferta coincide con las keywords
    cheapest_any: Optional[Offer] = None   # oferta más barata sin filtrar (diagnóstico)
    cheapest_any_price: Optional[float] = None
    payloads: int = 0
    error: Optional[str] = None


@dataclass
class Alert:
    kind: str           # "AHORRO DIRECTO" | "PRIVACIDAD" | "UPGRADE" | "MÍNIMO HISTÓRICO"
    target: str
    message: str
    suspicious: bool = False

