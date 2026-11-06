# Contexto del Proyecto: Tracker de Precios Florida 2027

> Este archivo es la fuente de verdad del proyecto para cualquier agente/IA que trabaje en el repo.
> Si cambian fechas, presupuestos o reglas, actualizar **acá, en `.env.example` y en `.env`**.

## Objetivo principal
Script automatizado en Python que monitorea **2 veces al día** los precios de hoteles y alquiler de autos
para un viaje a Florida (mayo 2027). Extrae precios, aplica una lógica de decisión basada en el presupuesto
y registra historial + alertas en `bitacora_precios.md` (y `data/historial_precios.csv`).

## Stack tecnológico y estrategia anti-bot (REGLAS OBLIGATORIAS)
- **Lenguaje:** Python 3.10+.
- **Herramienta:** Playwright (API sincrónica).
- **Prohibido scrapear selectores CSS/HTML para obtener datos.** Los precios se obtienen SOLO interceptando
  tráfico de red con `page.on("response", handler)` y leyendo los payloads JSON (Fetch/XHR) de las APIs internas.
  - Los locators (`get_by_role`, `get_by_label`, etc.) se permiten únicamente para **navegar/completar formularios**
    (en `flows/`), nunca para leer precios.
- **Despliegue:** local, vía **Windows Task Scheduler** (IP residencial, evita bloqueos de datacenter).
- Perfil de navegador persistente (`.browser_profile/`), Chrome real (`channel="chrome"`), modo visible por defecto,
  pausas humanas y jitter aleatorio en el horario.

## Entidades a monitorear

### 1. Alquiler de auto (Avis)
- **Vehículo:** Full-Size SUV (Chevrolet Suburban, Ford Expedition o similar).
- **Pick-up:** Aeropuerto de Miami (MIA) – 3 de mayo de 2027, 07:00.
- **Drop-off:** Cabana Bay Beach Resort, Orlando (código Avis **U2S**, 6550 Adventure Way) – 3 de mayo de 2027, 16:00.
- **Referencia base:** ~USD 260.

### 2. Hoteles en Orlando (4 adultos) – tarifa **Room Only** (sin tickets)

| Hotel | Check-in | Check-out | Habitación | Base pagada | Upgrade a evaluar |
|---|---|---|---|---|---|
| A. Universal's Cabana Bay Beach Resort | 2027-05-03 | 2027-05-06 | Standard | ~USD 1,174 | Loews Sapphire Falls Resort |
| B. Hard Rock Hotel (Universal) | 2027-05-06 | 2027-05-08 | Standard 2 Queen Beds | *(sin dato – completar en `config.py`)* | – |
| C. Disney's Pop Century Resort | 2027-05-08 | 2027-05-14 | Preferred Room | ~USD 2,406 | Disney's Caribbean Beach Resort |

## Reglas de decisión (por cada ejecución)
Comparar precios obtenidos vs presupuesto base y escribir en el Markdown si se cumple:
1. **Ahorro directo:** precio de 1 habitación cuádruple (4 adultos) < presupuesto base.
2. **Privacidad (2 habitaciones):** 2 × habitación doble (2 adultos) ≤ presupuesto base + USD 400 de tolerancia.
3. **Upgrade:** precio del hotel de categoría superior (4 adultos) ≤ presupuesto base del hotel actual.
- Auto: alerta de ahorro si el total < USD 260.
- Si un hotel no tiene base (Hard Rock): regla 1 = nuevo mínimo histórico; regla 2 usa como base el precio actual de 1 habitación.
- Si un precio es < 50 % de la base se marca "⚠️ verificar" (posible precio por noche o sin impuestos).
- Los presupuestos se asumen **con impuestos** (Orange County ≈ 12.5 %: 6.5 % sales + 6 % tourist tax).

## Arquitectura
```
main.py                 CLI: run | discover | analyze | list
config.py               Parámetros del viaje, búsquedas y lectura de variables de entorno
.env.example / .env     Configuración local segura (presupuestos, tolerancias, flags)
tracker/env.py          Cargador seguro de variables de entorno con fallback nativo
tracker/models.py       Dataclasses (Search, HotelGroup, CarRule, Offer, SearchResult, Alert)
tracker/interceptor.py  JsonInterceptor -> page.on("response") captura JSON de fetch/xhr
tracker/extractor.py    Extracción heurística de ofertas (label + precio) desde JSON arbitrario
tracker/rules.py        Reglas de decisión -> alertas
tracker/logbook.py      bitacora_precios.md (más nuevo arriba) + data/historial_precios.csv
tracker/browser.py      Contexto persistente de Playwright
tracker/runner.py       Orquestación: flujo de navegación + espera de payloads + extracción
flows/{avis,universal,disney}.py  Navegación (grabada con `playwright codegen`), sin lectura de datos
run_tracker.bat / install_task.ps1  Despliegue en Windows Task Scheduler (09:00 y 21:00 ± 20 min)
tests/                  Tests unitarios (unittest) de extractor, reglas y bitácora
```

## Estado de calibración
Los sitios (Avis, Universal/Loews, Disney) no aceptan deep links con parámetros: la búsqueda se hace por formulario
y las APIs internas cambian. Por eso hay dos pasos manuales por sitio, hechos una vez:
1. `python main.py discover <search_id>` → el usuario hace la búsqueda a mano; se guardan todos los JSON en
   `capturas/<id>/` con un índice de endpoints con precios. Con eso se ajustan `url_patterns` y `price_key_regex`.
2. `playwright codegen` → grabar los pasos de navegación y pegarlos en `flows/<sitio>.py` (`pasos_grabados`).

| Sitio | Patrón de URL calibrado | Flujo grabado |
|---|---|---|
| Avis | ❌ pendiente | ❌ pendiente |
| Universal (Cabana Bay / Sapphire Falls / Hard Rock) | ❌ pendiente | ❌ pendiente |
| Disney (Pop Century / Caribbean Beach) | ❌ pendiente | ❌ pendiente |

## Convenciones y flujo de trabajo (Git & Issues)
- Idioma de UI/bitácora/comentarios: español rioplatense. Montos en USD.
- No commitear `.env`, `.browser_profile/`, `capturas/`, `logs/`, `.venv/`. Mantener sincronizado `.env.example`.
- Correr tests: `python -m unittest discover -s tests`.
- **Commits y Push frecuentes:** Realizar commits y push de manera periódica ante cada hito, refactor o avance significativo para no perder el progreso y mantener el historial sincronizado y seguro.
- **Creación y seguimiento de Issues:** Crear y gestionar los issues necesarios (en GitHub o registro de tareas) para desglosar funcionalidades, calibraciones pendientes, bugs o mejoras, estructurando así el trabajo colaborativo en el desarrollo del agente.


