"""Caché en memoria con caducidad.

Vale mientras haya un solo proceso de backend. Si algún día hay varias réplicas,
se sustituye por una implementación con Redis que exponga los mismos métodos.
"""

import time
from collections.abc import Callable, Hashable
from dataclasses import dataclass


@dataclass
class CacheEntry[T]:
    value: T
    expires_at: float


class TTLCache[T]:
    def __init__(
        self,
        ttl_seconds: float,
        *,
        max_entries: int = 1000,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.clock = clock
        self._entries: dict[Hashable, CacheEntry[T]] = {}

    def get(self, key: Hashable) -> T | None:
        """Devuelve el valor solo si no ha caducado."""
        entry = self._entries.get(key)
        if entry is None or entry.expires_at <= self.clock():
            return None
        return entry.value

    def get_stale(self, key: Hashable) -> T | None:
        """Devuelve el último valor guardado aunque haya caducado (útil si falla el origen)."""
        entry = self._entries.get(key)
        return entry.value if entry else None

    def set(self, key: Hashable, value: T) -> None:
        self._entries.pop(key, None)
        self._entries[key] = CacheEntry(value, self.clock() + self.ttl_seconds)
        while len(self._entries) > self.max_entries:
            # Los dict mantienen el orden de inserción: el primero es el más antiguo.
            del self._entries[next(iter(self._entries))]

    def clear(self) -> None:
        self._entries.clear()
