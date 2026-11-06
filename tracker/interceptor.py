"""Intercepción de tráfico de red: captura payloads JSON de Fetch/XHR vía page.on("response")."""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse


@dataclass
class CapturedPayload:
    url: str
    status: int
    method: str
    data: Any
    post_data: Optional[str] = None
    ts: float = field(default_factory=time.time)


class JsonInterceptor:
    """Escucha respuestas de la página y guarda las que son JSON de APIs (fetch/xhr).

    Nunca lee el DOM: solo el cuerpo de las respuestas de red.
    """

    RESOURCE_TYPES = {"fetch", "xhr"}

    def __init__(self, url_patterns: Optional[list[str]] = None):
        self.patterns = [re.compile(p, re.I) for p in (url_patterns or [])]
        self.payloads: list[CapturedPayload] = []
        self.last_capture_ts: float = 0.0

    def attach(self, page) -> None:
        page.on("response", self._handler)

    def detach(self, page) -> None:
        try:
            page.remove_listener("response", self._handler)
        except Exception:
            pass

    def _wanted(self, url: str) -> bool:
        return not self.patterns or any(p.search(url) for p in self.patterns)

    def _handler(self, response) -> None:
        try:
            request = response.request
            if request.resource_type not in self.RESOURCE_TYPES:
                return
            if "json" not in (response.headers.get("content-type") or "").lower():
                return
            if not self._wanted(response.url) or response.status >= 400:
                return
            data = response.json()
        except Exception:
            return  # cuerpo no disponible / no JSON / redirección
        try:
            post_data = request.post_data
        except Exception:
            post_data = None
        self.payloads.append(CapturedPayload(response.url, response.status, request.method, data, post_data))
        self.last_capture_ts = time.time()

    def dump(self, directory: Path) -> list[Path]:
        """Guarda cada payload en un archivo JSON (para calibración/diagnóstico)."""
        directory.mkdir(parents=True, exist_ok=True)
        for old in directory.glob("*.json"):
            old.unlink()
        paths = []
        for i, p in enumerate(self.payloads, 1):
            parsed = urlparse(p.url)
            slug = re.sub(r"[^a-zA-Z0-9]+", "_", (parsed.netloc + parsed.path))[-80:]
            path = directory / f"{i:03d}_{slug}.json"
            path.write_text(
                json.dumps({"url": p.url, "status": p.status, "method": p.method,
                            "post_data": p.post_data, "data": p.data}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            paths.append(path)
        return paths


def load_dumped(directory: Path) -> list[CapturedPayload]:
    """Carga payloads previamente guardados con JsonInterceptor.dump()."""
    out = []
    for path in sorted(directory.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            out.append(CapturedPayload(raw["url"], raw.get("status", 200), raw.get("method", "GET"),
                                       raw["data"], raw.get("post_data")))
        except Exception:
            continue
    return out

