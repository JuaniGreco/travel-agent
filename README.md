# 🌴 Tracker de Precios Florida 2027

Monitorea 2 veces por día los precios del auto (Avis) y los hoteles de Orlando, los compara contra lo ya pagado
y escribe alertas en [`bitacora_precios.md`](bitacora_precios.md). Contexto completo y reglas: [`AGENTS.md`](AGENTS.md).

## 1. Instalación y Configuración (Windows)
```powershell
cd C:\ruta\travel-agent
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium      # respaldo si no tenés Google Chrome instalado

# Crear archivo de configuración local a partir de la plantilla
copy .env.example .env
# (Editar .env con tus presupuestos base y ajustes)

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

## Tests
```powershell
python -m unittest discover -s tests
```

