"""Tracker de Precios Florida 2027 – punto de entrada.

Uso:
    python main.py run [--only ID ...] [--headed|--headless]   # ejecución programada
    python main.py discover ID                                  # calibración asistida (búsqueda manual)
    python main.py analyze ID [--dir capturas/ID]               # re-analiza payloads guardados
    python main.py list                                         # lista las búsquedas configuradas
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import config
from tracker.extractor import iter_offers, matches, offer_total, select_best
from tracker.interceptor import JsonInterceptor, load_dumped
from tracker.logbook import append_history, historical_min, render_entry, write_logbook
from tracker.rules import evaluate, usd

ROOT = Path(__file__).resolve().parent
LOGBOOK = ROOT / "bitacora_precios.md"
HISTORY = ROOT / "data" / "historial_precios.csv"
CAPTURAS = ROOT / "capturas"

SEARCHES = {s.id: s for s in config.SEARCHES}


def bases_by_search() -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for g in config.HOTEL_GROUPS:
        for sid in (g.quad_search, g.double_search, g.upgrade_search):
            if sid:
                out[sid] = g.base_usd
    for c in config.CAR_RULES:
        out[c.search] = c.base_usd
    return out


# --------------------------------------------------------------------------- run
def cmd_run(args) -> int:
    from playwright.sync_api import sync_playwright

    from tracker.browser import open_context
    from tracker.runner import human_pause, run_search

    selected = [SEARCHES[i] for i in args.only] if args.only else list(SEARCHES.values())
    headless = config.HEADLESS if args.headless is None else args.headless
    results = {}
    with sync_playwright() as p:
        context = open_context(p, headless=headless, channel=config.BROWSER_CHANNEL)
        try:
            for n, s in enumerate(selected):
                if n:
                    human_pause(config.PAUSA_ENTRE_BUSQUEDAS_S)
                print(f"[{datetime.now():%H:%M:%S}] {s.id}: buscando…", flush=True)
                r = run_search(context, s, config.TIMEOUT_BUSQUEDA_S, config.SETTLE_S, config.GUARDAR_PAYLOADS)
                results[s.id] = r
                status = usd(r.price) if r.matched else (r.error or "sin coincidencia")
                print(f"    → {status}  ({r.payloads} payloads)", flush=True)
        finally:
            context.close()

    now = datetime.now()
    alerts = evaluate(results, config.HOTEL_GROUPS, config.CAR_RULES,
                      tolerance=config.TOLERANCIA_PRIVACIDAD_USD,
                      suspicious_ratio=config.UMBRAL_SOSPECHOSO,
                      historical_min=historical_min(HISTORY))
    entry = render_entry(now, selected, results, alerts, bases_by_search())
    write_logbook(LOGBOOK, config.TRIP_NAME, entry)
    append_history(HISTORY, now, results)
    print(f"\n{len(alerts)} alerta(s). Bitácora actualizada: {LOGBOOK}")
    for a in alerts:
        print(f"  🚨 [{a.kind}] {a.target}: {a.message}")
    return 0


# ---------------------------------------------------------------------- discover
def describe(s) -> str:
    if s.kind == "car":
        return (f"Pick-up {s.pickup_location} {s.pickup_at:%m/%d/%Y %I:%M %p} · "
                f"Drop-off {s.dropoff_location} {s.dropoff_at:%m/%d/%Y %I:%M %p} · Full-Size SUV")
    return (f"{s.property_name} · {s.check_in:%m/%d/%Y} → {s.check_out:%m/%d/%Y} · "
            f"{s.adults} adultos · {s.rooms} habitación · Room Only (sin tickets)")


def cmd_discover(args) -> int:
    from playwright.sync_api import sync_playwright

    from tracker.browser import open_context

    s = SEARCHES[args.id]
    out_dir = CAPTURAS / s.id
    interceptor = JsonInterceptor()  # sin filtro: captura TODO el JSON para descubrir endpoints
    with sync_playwright() as p:
        context = open_context(p, headless=False, channel=config.BROWSER_CHANNEL)
        page = context.pages[0] if context.pages else context.new_page()
        interceptor.attach(page)
        context.on("page", interceptor.attach)  # por si el sitio abre pestañas nuevas
        page.goto(s.start_url, wait_until="domcontentloaded")
        print("\n=== MODO DESCUBRIMIENTO ===")
        print(f"Hacé la búsqueda a mano en el navegador:\n  {describe(s)}")
        print("Cuando veas la lista de precios, volvé acá y presioná ENTER.")
        input()
        paths = interceptor.dump(out_dir)
        context.close()
    print(f"{len(paths)} payloads JSON guardados en {out_dir}")
    return analyze(s, interceptor.payloads, out_dir)


def cmd_analyze(args) -> int:
    s = SEARCHES[args.id]
    directory = Path(args.dir) if args.dir else CAPTURAS / s.id
    return analyze(s, load_dumped(directory), directory)


def analyze(s, payloads, directory: Path) -> int:
    """Resume qué endpoints traen precios y qué ofertas coinciden; escribe index.md."""
    rows, key_counts, host_paths = [], defaultdict(int), defaultdict(int)
    for i, p in enumerate(payloads, 1):
        offers = [o for o in iter_offers(p.data, p.url, s.price_key_regex)
                  if s.min_price <= offer_total(o, s) <= s.max_price]
        ok = [o for o in offers if matches(o, s)]
        if offers:
            parsed = urlparse(p.url)
            host_paths[parsed.netloc + parsed.path] += len(ok)
            for o in ok:
                key_counts[o.price_key] += 1
            rows.append((i, p, offers, ok))

    lines = [f"# Descubrimiento `{s.id}` – {datetime.now():%Y-%m-%d %H:%M}\n", f"{describe(s)}\n",
             f"Payloads totales: {len(payloads)} · con precios: {len(rows)}\n"]
    for i, p, offers, ok in rows:
        lines.append(f"## #{i:03d} {p.method} {p.url[:160]}\n")
        lines.append(f"Ofertas: {len(offers)} · coinciden keywords: {len(ok)}\n")
        for o in sorted(ok or offers, key=lambda o: offer_total(o, s))[:12]:
            mark = "✅" if o in ok else "·"
            lines.append(f"- {mark} {usd(offer_total(o, s))} (crudo {o.raw_price} `{o.price_key}`"
                         f"{' por noche/día' if o.nightly else ''}) — {o.label[:140]}")
        lines.append("")

    best, total, _, _ = select_best(payloads, s)
    sug_start = len(lines)
    lines.append("## Sugerencias para config.py\n")
    if host_paths:
        top = sorted(host_paths.items(), key=lambda kv: -kv[1])[:3]
        for path, n in top:
            lines.append(f"- url_patterns candidato: `r\"{re.escape(path)}\"` ({n} ofertas que coinciden)")
    if key_counts:
        key = max(key_counts, key=key_counts.get)
        lines.append(f"- price_key_regex candidato: `r\"{re.escape(key)}$\"`")
    lines.append(f"- Mejor oferta que coincide: {usd(total)} — {best.label if best else 'ninguna'}")

    directory.mkdir(parents=True, exist_ok=True)
    (directory / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[sug_start:]))
    print(f"\nDetalle completo: {directory / 'index.md'}")
    return 0


def cmd_list(_args) -> int:
    for s in config.SEARCHES:
        print(f"{s.id:16} {s.label}")
    return 0


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # consola Windows
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Tracker de Precios Florida 2027")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="ejecuta todas (o algunas) búsquedas y actualiza la bitácora")
    r.add_argument("--only", nargs="+", choices=list(SEARCHES), help="ids de búsquedas a correr")
    g = r.add_mutually_exclusive_group()
    g.add_argument("--headed", dest="headless", action="store_false", default=None)
    g.add_argument("--headless", dest="headless", action="store_true")
    r.set_defaults(func=cmd_run)

    d = sub.add_parser("discover", help="calibración: búsqueda manual + captura de todos los JSON")
    d.add_argument("id", choices=list(SEARCHES))
    d.set_defaults(func=cmd_discover)

    a = sub.add_parser("analyze", help="re-analiza payloads guardados (tras ajustar keywords/regex)")
    a.add_argument("id", choices=list(SEARCHES))
    a.add_argument("--dir", help="carpeta con payloads (default capturas/ID)")
    a.set_defaults(func=cmd_analyze)

    sub.add_parser("list", help="lista búsquedas").set_defaults(func=cmd_list)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
