import json
import logging
from dataclasses import dataclass
from typing import Any


logger = logging.getLogger("call_hermes.events")


@dataclass(frozen=True)
class BridgeEvent:
    type: str
    payload: dict[str, Any]

    def to_json(self) -> str:
        return json.dumps({"type": self.type, **self.payload}, ensure_ascii=False)


class EventSink:
    def __init__(self) -> None:
        self._channel: Any | None = None
        self.history: list[BridgeEvent] = []

    def bind_channel(self, channel: Any) -> None:
        self._channel = channel
        for event in self.history[-20:]:
            self._send(event)

    def emit(self, event_type: str, **payload: Any) -> None:
        event = BridgeEvent(event_type, payload)
        self.history.append(event)
        self._send(event)

    def _send(self, event: BridgeEvent) -> None:
        if self._channel and self._channel.readyState == "open":
            try:
                self._channel.send(event.to_json())
            except Exception:
                logger.debug("failed to send bridge event type=%s", event.type, exc_info=True)
