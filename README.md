# 🌴 Tracker de Precios Florida 2027

Monitorea 2 veces por día los precios del auto (Avis) y los hoteles de Orlando, los compara contra lo ya pagado
y escribe alertas en [`bitacora_precios.md`](bitacora_precios.md). Contexto completo y reglas: [`AGENTS.md`](AGENTS.md).

## 1. Instalación Rápida en Windows 10 (1 Clic)
Si estás en tu computadora con Windows 10, podés dejar todo listo y operativo con un solo clic:

1. Cloná o descargá el repositorio:
   ```cmd
   git clone https://github.com/JuaniGreco/travel-agent.git
   cd travel-agent
   ```
2. Hacé **doble clic en `setup_windows.bat`** (o ejecutalo desde la consola):
   - ✅ Detecta Python 3 automáticamente.
   - ✅ Crea el entorno virtual `.venv`.
   - ✅ Instala todas las dependencias (`requirements.txt`).
   - ✅ Instala Chromium para Playwright.
   - ✅ Genera tu archivo local `.env` listo para usar.
   - ✅ Ejecuta los 20 tests unitarios y valida la instalación.

3. **Para programar la ejecución desatendida:**
   - Hacé doble clic en **`instalar_tarea.bat`** y se registrará automáticamente en Windows Task Scheduler (cada 4 horas con jitter aleatorio).

---

### Instalación Manual Alternativa (PowerShell)
```powershell
cd C:\ruta\travel-agent
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
copy .env.example .env
python main.py list
```

## 2. Calibración (una vez por sitio, ~10 min cada uno)
Los sitios no aceptan links con parámetros y sus APIs internas no son públicas, así que hay que "enseñarle" al bot:

**a) Descubrir la API interna** (qué JSON trae los precios):
```powershell
python main.py discover avis_suv        # también: cabana_quad, hardrock_quad, pop_quad, ...
```
Se abre Chrome: hacés la búsqueda a mano, presionás ENTER en la consola. Se guardan todos los JSON en
`capturas/<id>/` y `capturas/<id>/index.md` muestra los endpoints con precios y sugerencias de
`url_patterns` y `price_key_regex` para pegar en [`config.py`](config.py). Si no coincide ninguna oferta,
ajustá `offer_keywords` y re-analizá sin navegar: `python main.py analyze avis_suv`.

**b) Grabar la navegación** (clicks del formulario; no se leen datos del DOM):
```powershell
playwright codegen --target python --channel chrome https://www.avis.com/en/home
```
Copiá los pasos generados dentro de `pasos_grabados()` en `flows/avis.py` (idem `flows/universal.py`,
`flows/disney.py`) reemplazando fechas/huéspedes fijos por los campos de `s` (ver docstring de cada archivo).

**c) Probar:** `python main.py run --only avis_suv` y revisar la bitácora.

**d) Probar notificaciones Telegram:** `python main.py notify-test`

## 3. Automatización (Windows Task Scheduler)
Se programa desatendido con jitter aleatorio para no emitir patrones fijos:

```powershell
# Pre-Black Friday: cada 4 horas (valor recomendado habitual)
powershell -ExecutionPolicy Bypass -File .\install_task.ps1

# Black Friday intensivo: cada 2 horas
powershell -ExecutionPolicy Bypass -File .\install_task.ps1 -IntervalHours 2 -JitterMinutes 10

# Prueba inmediata:
Start-ScheduledTask -TaskName TrackerPreciosFlorida2027
```
La PC debe estar encendida y con sesión iniciada (el navegador corre visible con Chrome real). Log: `logs\tracker.log`.

## Archivos generados
| Archivo | Contenido |
|---|---|
| `bitacora_precios.md` | Alertas + tabla de precios por ejecución (más reciente arriba) |
| `data/historial_precios.csv` | Historial completo (para mínimos históricos / gráficos) |
| `capturas/ultima/<id>/` | JSON capturados en la última ejecución (diagnóstico) |
| `capturas/errores/<id>.png` | Captura de pantalla si falló la navegación |

## 4. Ejecución con Docker (Aislado y Prolijo)
Podés ejecutar el tracker completamente dentro de un contenedor Docker sin necesidad de instalar Python ni navegadores en tu sistema host:

```bash
# 1. Crear el archivo .env local si aún no lo hiciste
copy .env.example .env    # en Windows (o 'cp .env.example .env' en Linux/macOS)

# 2. Construir la imagen con Playwright
docker compose build

# 3. Listar búsquedas configuradas
docker compose run --rm travel-agent list

# 4. Probar alerta a Telegram
docker compose run --rm travel-agent notify-test

# 5. Ejecutar una pasada completa
docker compose run --rm travel-agent run
```
Todos los archivos generados (`bitacora_precios.md`, `data/historial_precios.csv`, `logs/`, `capturas/`) se sincronizan y persisten automáticamente en tu computadora gracias a los volúmenes configurados en `docker-compose.yml`.

También podés automatizar la ejecución vía Docker usando `run_docker.bat` (en Windows Task Scheduler) o `run_docker.sh` (en Linux cron).

## Tests
```powershell
python -m unittest discover -s tests
```

