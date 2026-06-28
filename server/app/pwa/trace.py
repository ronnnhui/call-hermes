import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class TurnTrace:
    turn_id: str
    logger: logging.Logger
    started_at: float = field(default_factory=time.perf_counter)
    timings: dict[str, int] = field(default_factory=dict)
    marks: dict[str, int] = field(default_factory=dict)

    def mark(self, name: str) -> None:
        """Record a single point in time (ms since ``started_at``)."""
        elapsed_ms = int((time.perf_counter() - self.started_at) * 1000)
        self.marks[name] = elapsed_ms
        self.logger.info("turn_id=%s mark=%s at=%dms", self.turn_id, name, elapsed_ms)

    def gap(self, from_mark: str, to_mark: str) -> int | None:
        """Return ``to_mark - from_mark`` in ms, or None if either is missing."""
        if from_mark not in self.marks or to_mark not in self.marks:
            return None
        return self.marks[to_mark] - self.marks[from_mark]

    def summary(self) -> dict[str, int]:
        """All stage durations and mark timestamps plus computed inter-mark gaps."""
        out: dict[str, int] = dict(self.timings)
        out.update({f"{k}_at": v for k, v in self.marks.items()})
        for a, b in (
            ("asr_final", "hermes_first_token"),
            ("hermes_first_token", "tts_first_audio"),
            ("asr_final", "speaking_end"),
            ("hermes_first_token", "speaking_end"),
        ):
            g = self.gap(a, b)
            if g is not None:
                out[f"{a}__to__{b}_ms"] = g
        return out

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        started = time.perf_counter()
        self.logger.info("turn_id=%s stage=%s start", self.turn_id, name)
        try:
            yield
        except Exception:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            self.timings[f"{name}_ms"] = elapsed_ms
            self.logger.info(
                "turn_id=%s stage=%s failed elapsed_ms=%d",
                self.turn_id,
                name,
                elapsed_ms,
            )
            raise
        else:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            self.timings[f"{name}_ms"] = elapsed_ms
            self.logger.info(
                "turn_id=%s stage=%s complete elapsed_ms=%d",
                self.turn_id,
                name,
                elapsed_ms,
            )

    @property
    def total_ms(self) -> int:
        return int((time.perf_counter() - self.started_at) * 1000)
