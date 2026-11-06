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
- **Vehículo:** Full-Size SUV / Premium SUV (Chevrolet Suburban, Tahoe, Ford Expedition, GMC Yukon XL o similar).
  - **Requisito físico:** Capacidad real para 4 adultos + 4 valijas grandes (28") en el baúl.
  - **Exclusión obligatoria:** Prohibido Minivans / Vans / Traffics (Pacifica, Caravan, Transit, etc.).
- **Pick-up:** Aeropuerto de Miami (MIA) – 3 de mayo de 2027, 07:00.
- **Drop-off:** Cabana Bay Beach Resort, Orlando (código Avis **U2S**, 6550 Adventure Way) – 3 de mayo de 2027, 16:00 (devolución fuera de hora si el mostrador cerró).
- **Referencia base:** ~USD 260 (sin reserva previa aún; se busca el menor precio).

### 2. Hoteles en Orlando (4 adultos) – tarifa **Room Only** (sin tickets)

| Hotel | Check-in | Check-out | Habitación | Base pagada (Room Only) | Factura paquete total | Upgrade a evaluar |
|---|---|---|---|---|---|---|
| A. Universal's Cabana Bay Beach Resort | 2027-05-03 | 2027-05-06 | Poolside 2 Queen Beds | ~USD 1,174.14 | USD 3,174.14 (inc. 4D PTP + Volcano Bay) | Loews Sapphire Falls Resort |
| B. Hard Rock Hotel (Universal) | 2027-05-06 | 2027-05-08 | Standard 2 Queen Beds | USD 2,125.15 | USD 2,125.15 (inc. Unlimited Express Pass) | – |
| C. Disney's Pop Century Resort | 2027-05-08 | 2027-05-14 | Preferred Room | ~USD 2,406.00 | USD 4,566.57 (inc. 4-Day Tickets) | Disney's Caribbean Beach Resort (Solo Preferred Room) |

> **Criterio de disposición física y caminatas (Hoteles):**
> - En Pop Century se paga Preferred para estar cerca del Classic Hall (lobby/comedor/buses) y del Skyliner.
> - En el upgrade a Caribbean Beach Resort **SOLO se admite Preferred Room** (edificios Martinique y Barbados, al lado de Old Port Royale). No se aceptan Standard Rooms porque Caribbean Beach es enorme y caminar desde las aldeas alejadas (ej. Trinidad) toma 15-25 minutos.
> - En Universal, Loews Sapphire Falls es un único edificio cerrado con pasillos interiores y transporte en barco (water taxi), eliminando caminatas largas bajo el calor.

> **Nota sobre gestión con agente de viajes:** Las reservas de Disney y Universal se gestionan vía agente de viajes oficial (sin costo directo para el usuario). Cuando el tracker detecte una baja de tarifa oficial (ej. Black Friday), el usuario le pide a su agente que re-aplique la cotización a la reserva existente para obtener la devolución/ajuste.

## Reglas de decisión (por cada ejecución)
Comparar precios obtenidos vs presupuesto base y escribir en el Markdown si se cumple:
1. **Ahorro directo:** precio de 1 habitación cuádruple (4 adultos) < presupuesto base.
2. **Privacidad (2 habitaciones):** 2 × habitación doble (2 adultos) ≤ presupuesto base + USD 400 de tolerancia.
3. **Upgrade:** precio del hotel de categoría superior (4 adultos) ≤ presupuesto base del hotel actual.
4. **Expedia / OTA:** precio en Expedia ≤ presupuesto base - USD 500 (alerta únicamente si el ahorro supera los $500 USD para justificar salir del agente de viajes oficial y sus beneficios).
- Auto: alerta de ahorro si el total < USD 260 (y registro del nuevo mínimo).
- Si un precio es < 50 % de la base se marca "⚠️ verificar" (posible precio por noche o sin impuestos).
- Los presupuestos se asumen **con impuestos** (Orange County ≈ 12.5 %: 6.5 % sales + 6 % tourist tax).
- Notificaciones instantáneas enviadas por **Telegram** (y Discord si está configurado).

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
tracker/notifier.py     Despacho de alertas instantáneas (Telegram bot y Discord webhook)
tracker/browser.py      Contexto persistente de Playwright con higiene de cookies anti-rastreo
tracker/runner.py       Orquestación: flujo de navegación + espera de payloads + extracción
flows/{avis,universal,disney,expedia}.py  Navegación interactiva, sin lectura de datos en el DOM
Dockerfile / compose    Contenedorización basada en Microsoft Playwright Python
run_docker.bat / .sh    Ejecución del contenedor con volúmenes montados
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


