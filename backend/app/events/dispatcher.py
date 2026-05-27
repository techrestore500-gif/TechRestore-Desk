from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, TypeVar


EventHandler = Callable[[Any], None]
EventT = TypeVar("EventT")


class EventDispatcher:
    def __init__(self) -> None:
        self._subscribers: dict[type, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: type[EventT], handler: Callable[[EventT], None]) -> None:
        self._subscribers[event_type].append(handler)

    def publish(self, event: Any) -> None:
        handlers = list(self._subscribers.get(type(event), []))
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                # Subscribers must never break request workflows.
                continue


event_dispatcher = EventDispatcher()
