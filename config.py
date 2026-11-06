"""Configuración del Tracker de Precios Florida 2027.

Toda la información de negocio y parámetros se carga desde variables de entorno (.env)
con valores por defecto seguros.
Ver AGENTS.md para el contexto completo.
"""
from datetime import date, datetime

from tracker.env import get_bool, get_float, get_int, get_str, load_env
from tracker.models import CarRule, HotelGroup, Search

load_env()

TRIP_NAME = get_str("TRIP_NAME", "Florida 2027")

# --- Presupuestos Base Pagados / de Referencia (USD) -------------------------
BASE_CABANA = get_float("CABANA_BAY_BASE_USD", 1174.14)
BASE_HARDROCK = get_float("HARD_ROCK_BASE_USD", 2125.15)
BASE_POP = get_float("POP_CENTURY_BASE_USD", 2406.0)
BASE_AVIS_SUV = get_float("AVIS_SUV_BASE_USD", 260.0)

# --- Reglas -----------------------------------------------------------------
TOLERANCIA_PRIVACIDAD_USD = get_float("TOLERANCIA_PRIVACIDAD_USD", 400.0)
UMBRAL_SOSPECHOSO = get_float("UMBRAL_SOSPECHOSO", 0.5)

# Impuestos Orange County (Universal y Disney): 6.5 % sales + 6 % tourist development tax
TAX_ORLANDO = get_float("TAX_ORLANDO", 0.125)

# --- Navegador / anti-bot / anti-rastreo -----------------------------------
HEADLESS = get_bool("BROWSER_HEADLESS", False)
BROWSER_CHANNEL = get_str("BROWSER_CHANNEL", "chrome") or None
TIMEOUT_BUSQUEDA_S = get_int("SEARCH_TIMEOUT_SECONDS", 90)
SETTLE_S = get_int("SEARCH_SETTLE_SECONDS", 4)
PAUSA_MIN = get_int("PAUSE_BETWEEN_SEARCHES_MIN", 8)
PAUSA_MAX = get_int("PAUSE_BETWEEN_SEARCHES_MAX", 25)
PAUSA_ENTRE_BUSQUEDAS_S = (PAUSA_MIN, PAUSA_MAX)
GUARDAR_PAYLOADS = get_bool("GUARDAR_PAYLOADS", True)
CLEAR_COOKIES_EACH_RUN = get_bool("CLEAR_COOKIES_EACH_RUN", True)

# --- Patrones de URL de APIs internas (ajustar tras `python main.py discover`) ---
URLS_AVIS = [r"avis\.com/"]
URLS_UNIVERSAL = [r"universalorlando\.com/", r"loewshotels\.com/"]
URLS_DISNEY = [r"disney\.go\.com/", r"wdpromedia|disney\.com/"]

START_AVIS = "https://www.avis.com/en/home"
START_UNIVERSAL = "https://www.universalorlando.com/web/en/us/places-to-stay"
START_DISNEY_POP = "https://disneyworld.disney.go.com/resorts/pop-century-resort/"
START_DISNEY_CBR = "https://disneyworld.disney.go.com/resorts/caribbean-beach-resort/"

SUV_KEYWORDS = [r"suburban", r"expedition", r"full[\s-]?size\s*suv", r"premium\s*suv",
                r"large\s*suv", r"yukon\s*xl", r"tahoe"]

# --- Búsquedas ----------------------------------------------------------------
_CABANA = dict(check_in=date(2027, 5, 3), check_out=date(2027, 5, 6))
_HARDROCK = dict(check_in=date(2027, 5, 6), check_out=date(2027, 5, 8))
_POP = dict(check_in=date(2027, 5, 8), check_out=date(2027, 5, 14))
_HOTEL_TAX = dict(tax_rate=TAX_ORLANDO, prices_include_tax=False)

SEARCHES: list[Search] = [
    # 1. Auto
    Search(
        id="avis_suv", site="avis", kind="car",
        label="Avis Full-Size SUV · MIA 03/05 07:00 → Cabana Bay (U2S) 03/05 16:00",
        start_url=START_AVIS, url_patterns=URLS_AVIS,
        offer_keywords=SUV_KEYWORDS,
        exclude_keywords=[
            r"van", r"minivan", r"transit", r"traffic", r"caravan", r"pacifica",
            r"wagon", r"sedan", r"compact", r"mid[\s-]?size", r"standard\s*suv"
        ],
        pickup_location="MIA", dropoff_location="U2S",
        pickup_at=datetime(2027, 5, 3, 7, 0), dropoff_at=datetime(2027, 5, 3, 16, 0),
        prices_include_tax=True,
    ),
    # 2A. Cabana Bay + upgrade Sapphire Falls
    Search(
        id="cabana_quad", site="universal", kind="hotel",
        label="Cabana Bay · Poolside 2 Queen · 4 adultos", property_name="Universal's Cabana Bay Beach Resort",
        start_url=START_UNIVERSAL, url_patterns=URLS_UNIVERSAL,
        offer_keywords=[r"poolside", r"pool view", r"standard", r"queen", r"courtyard"], exclude_keywords=[r"suite"],
        adults=4, **_CABANA, **_HOTEL_TAX,
    ),
    Search(
        id="cabana_doble", site="universal", kind="hotel",
        label="Cabana Bay · Poolside 2 Queen · 2 adultos", property_name="Universal's Cabana Bay Beach Resort",
        start_url=START_UNIVERSAL, url_patterns=URLS_UNIVERSAL,
        offer_keywords=[r"poolside", r"pool view", r"standard", r"queen", r"courtyard"], exclude_keywords=[r"suite"],
        adults=2, **_CABANA, **_HOTEL_TAX,
    ),
    Search(
        id="sapphire_quad", site="universal", kind="hotel",
        label="Loews Sapphire Falls · 1 hab. · 4 adultos", property_name="Loews Sapphire Falls Resort",
        start_url=START_UNIVERSAL, url_patterns=URLS_UNIVERSAL,
        offer_keywords=[r"standard", r"queen"], exclude_keywords=[r"suite", r"club", r"king"],
        adults=4, **_CABANA, **_HOTEL_TAX,
    ),
    # 2B. Hard Rock
    Search(
        id="hardrock_quad", site="universal", kind="hotel",
        label="Hard Rock Hotel · Standard 2 Queen · 4 adultos", property_name="Hard Rock Hotel",
        start_url=START_UNIVERSAL, url_patterns=URLS_UNIVERSAL,
        offer_keywords=[r"(2|two|double)\s*queen"], exclude_keywords=[r"suite", r"club", r"king"],
        adults=4, **_HARDROCK, **_HOTEL_TAX,
    ),
    Search(
        id="hardrock_doble", site="universal", kind="hotel",
        label="Hard Rock Hotel · Standard 2 Queen · 2 adultos", property_name="Hard Rock Hotel",
        start_url=START_UNIVERSAL, url_patterns=URLS_UNIVERSAL,
        offer_keywords=[r"(2|two|double)\s*queen"], exclude_keywords=[r"suite", r"club", r"king"],
        adults=2, **_HARDROCK, **_HOTEL_TAX,
    ),
    # 2C. Pop Century + upgrade Caribbean Beach
    Search(
        id="pop_quad", site="disney", kind="hotel",
        label="Pop Century · Preferred · 4 adultos", property_name="Disney's Pop Century Resort",
        start_url=START_DISNEY_POP, url_patterns=URLS_DISNEY,
        offer_keywords=[r"preferred"], exclude_keywords=[r"suite"],
        adults=4, **_POP, **_HOTEL_TAX,
    ),
    Search(
        id="pop_doble", site="disney", kind="hotel",
        label="Pop Century · Preferred · 2 adultos", property_name="Disney's Pop Century Resort",
        start_url=START_DISNEY_POP, url_patterns=URLS_DISNEY,
        offer_keywords=[r"preferred"], exclude_keywords=[r"suite"],
        adults=2, **_POP, **_HOTEL_TAX,
    ),
    Search(
        id="caribbean_quad", site="disney", kind="hotel",
        label="Caribbean Beach · Preferred Room · 4 adultos", property_name="Disney's Caribbean Beach Resort",
        start_url=START_DISNEY_CBR, url_patterns=URLS_DISNEY,
        offer_keywords=[r"preferred"], exclude_keywords=[r"suite", r"under the sea", r"standard"],
        adults=4, **_POP, **_HOTEL_TAX,
    ),
]

# --- Reglas de negocio --------------------------------------------------------
HOTEL_GROUPS: list[HotelGroup] = [
    HotelGroup(id="cabana_bay", label="Universal's Cabana Bay (03→06/05)", base_usd=BASE_CABANA,
               quad_search="cabana_quad", double_search="cabana_doble",
               upgrade_search="sapphire_quad", upgrade_label="Loews Sapphire Falls"),
    HotelGroup(id="hard_rock", label="Hard Rock Hotel (06→08/05)", base_usd=BASE_HARDROCK,
               quad_search="hardrock_quad", double_search="hardrock_doble"),
    HotelGroup(id="pop_century", label="Disney's Pop Century (08→14/05)", base_usd=BASE_POP,
               quad_search="pop_quad", double_search="pop_doble",
               upgrade_search="caribbean_quad", upgrade_label="Disney's Caribbean Beach (Preferred Room)"),
]

CAR_RULES: list[CarRule] = [
    CarRule(search="avis_suv", label="Avis Full-Size SUV (MIA → U2S)", base_usd=BASE_AVIS_SUV),
]
