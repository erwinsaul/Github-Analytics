"""Monitoreo y control preventivo de cuotas de consumo en GitHub API."""

import logging
import time
from datetime import datetime, timezone
import httpx

logger = logging.getLogger(__name__)

class RateLimitTracker:
    """Rastrea cabeceras de rate limit y aplica pausas si la cuota está agotada."""

    def __init__(self, safety_margin_remainging: int = 5) -> None:
        self.safety_margin = safety_margin_remainging
        self.remaining: int = 5000
        self.limit: int = 5000
        self.reset_timestamp: int = 0
    
    def update_from_headers(self, headers: httpx.Headers) -> None:
        """Actualiza es estado interno a partir de las cabeceras de la respuesta."""

        if "x-ratelimit-remaining" in headers:
            try:
                self.remaining = int(headers["x-ratelimit-remaining"])
                self.limit = int(headers.get("x-ratelimit-limit", 5000))
                self.reset_timestamp = int(headers.get("x-ratelimit-reset", 0))
            except ValueError:
                pass
    
    def check_and_wait_if_needed(self) -> None:
        """Si la cuota de peticiones disponibles es crítica, suspende la ejecución."""
        if self.remaining <= self.safety_margin and self.reset_timestamp > 0:
            now_ts = int(datetime.now(timezone.utc).timestamp())
            sleep_duration = max(self.reset_timestamp - now_ts + 2, 1)
            logger.warning(
                "Límite de GitHub API alcanzado (%d%d restantes). Pausando ejecución por %d segundos.",
                self.remaining,
                self.limit,
                sleep_duration,
            )
            time.sleep(sleep_duration)    