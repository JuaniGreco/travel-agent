"""Carga y lectura segura de variables de entorno desde .env."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_env(path: Optional[Path] = None) -> None:
    """Carga variables desde el archivo .env sin sobreescribir variables ya existentes."""
    target = path or ENV_PATH
    if not target.exists():
        return

    # Si python-dotenv está disponible, se utiliza
    try:
        import dotenv
        dotenv.load_dotenv(dotenv_path=target, override=False)
        return
    except ImportError:
        pass

    # Parser nativo liviano de respaldo (sin dependencias externas)
    try:
        content = target.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
            if not match:
                continue
            key, val = match.group(1), match.group(2).strip()
            # Eliminar comillas dobles o simples envolventes
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            if key not in os.environ:
                os.environ[key] = val
    except Exception:
        pass


def get_str(key: str, default: str = "") -> str:
    val = os.getenv(key)
    return default if val is None or val.strip() == "" else val.strip()


def get_float(key: str, default: Optional[float] = None) -> Optional[float]:
    val = os.getenv(key)
    if val is None or val.strip() == "":
        return default
    try:
        return float(val.strip())
    except ValueError:
        return default


def get_int(key: str, default: int = 0) -> int:
    val = os.getenv(key)
    if val is None or val.strip() == "":
        return default
    try:
        return int(val.strip())
    except ValueError:
        return default


def get_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key)
    if val is None or val.strip() == "":
        return default
    return val.strip().lower() in ("true", "1", "yes", "si", "on")

