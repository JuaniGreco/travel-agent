"""Bitácora Markdown (bitacora_precios.md) + historial CSV."""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Alert, Search, SearchResult
from .rules import usd

MARKER = "<!-- ENTRADAS (la más reciente arriba) -->"
CSV_FIELDS = ["timestamp", "search_id", "price_usd", "matched", "offer", "price_key", "error"]


def _header(trip: str) -> str:
    return (
        f"# 📒 Bitácora de Precios – {trip}\n\n"
        "Generada automáticamente por `main.py run` (2 veces por día). "
        "Precios en USD, total de la estadía/alquiler con impuestos estimados.\n\n"
        "**Reglas:** 1) Ahorro directo · 2) Privacidad: 2 hab. dobles ≤ base + USD 400 · "
        "3) Upgrade ≤ base actual.\n\n"
        f"{MARKER}\n"
    )


def _cell(text: str, limit: int = 70) -> str:
    text = (text or "").replace("|", "/").replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def render_entry(
    when: datetime,
    searches: list[Search],
    results: dict[str, SearchResult],
    alerts: list[Alert],
    bases: dict[str, Optional[float]],
) -> str:
    lines = [f"\n## {when:%Y-%m-%d %H:%M}\n"]

    if alerts:
        lines.append("### 🚨 Alertas\n")
        for a in alerts:
            flag = " ⚠️ *verificar: posible precio por noche/sin impuestos*" if a.suspicious else ""
            lines.append(f"- **[{a.kind}] {a.target}:** {a.message}{flag}")
        lines.append("")
    else:
        lines.append("_Sin alertas en esta ejecución._\n")

    lines.append("### 💲 Precios capturados\n")
    lines.append("| Búsqueda | Total | Base | Oferta detectada |")
    lines.append("|---|---:|---:|---|")
    problems = []
    for s in searches:
        r = results.get(s.id)
        if r is None:
            continue
        base = bases.get(s.id)
        if r.error:
            lines.append(f"| {s.label} | ❌ | {usd(base)} | {_cell(r.error)} |")
            problems.append(f"- `{s.id}`: {r.error}")
        elif r.matched:
            lines.append(f"| {s.label} | **{usd(r.price)}** | {usd(base)} | {_cell(r.offer.label if r.offer else '')} |")
        else:
            hint = (f"sin coincidencia; más barata: {usd(r.cheapest_any_price)} "
                    f"({_cell(r.cheapest_any.label, 40)})") if r.cheapest_any else "sin precios en payloads"
            lines.append(f"| {s.label} | ❔ | {usd(base)} | {_cell(hint, 90)} |")
            problems.append(f"- `{s.id}`: {hint} · {r.payloads} payloads JSON capturados")
    lines.append("")
    if problems:
        lines.append("<details><summary>⚠️ Errores / sin datos</summary>\n")
        lines.extend(problems)
        lines.append("\n</details>\n")
    lines.append("---")
    return "\n".join(lines) + "\n"


def write_logbook(path: Path, trip: str, entry: str) -> None:
    content = path.read_text(encoding="utf-8") if path.exists() else _header(trip)
    if MARKER not in content:
        content = content.rstrip() + "\n\n" + MARKER + "\n"
    head, tail = content.split(MARKER, 1)
    path.write_text(head + MARKER + "\n" + entry + tail.lstrip("\n"), encoding="utf-8")


def append_history(path: Path, when: datetime, results: dict[str, SearchResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if new:
            w.writeheader()
        for r in results.values():
            w.writerow({
                "timestamp": when.isoformat(timespec="seconds"),
                "search_id": r.search_id,
                "price_usd": "" if r.price is None else f"{r.price:.2f}",
                "matched": int(r.matched),
                "offer": r.offer.label if r.offer else "",
                "price_key": r.offer.price_key if r.offer else "",
                "error": r.error or "",
            })


def historical_min(path: Path) -> dict[str, float]:
    """Precio mínimo histórico (solo ofertas que coincidieron) por búsqueda."""
    mins: dict[str, float] = {}
    if not path.exists():
        return mins
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("matched") != "1" or not row.get("price_usd"):
                continue
            price = float(row["price_usd"])
            sid = row["search_id"]
            if sid not in mins or price < mins[sid]:
                mins[sid] = price
    return mins

