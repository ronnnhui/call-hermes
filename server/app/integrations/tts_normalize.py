"""TTS-friendly text normalization.

Strips Markdown so TTS reads the words, not the punctuation. The original
Markdown is still returned to the UI unchanged — this module only rewrites
the text that becomes speech.

The five effects (applied in this order on the full text) match what the
voice-mode system prompt asks Hermes to produce, so they double as a
defensive cleanup for whatever slips through:

1. ``[text](url)`` → ``text``
2. `` `code` ``   → ``code``
3. Leading ``-`` / ``*`` / ``#`` (followed by whitespace) → dropped
4. ``**bold**`` / ``*italic*`` → plain text
5. Runs of blank lines → single ``。`` (sentence break)

Safety nets beyond the five: fenced code blocks and ``---`` horizontal
rules are silently dropped so the upstream model straying from the prompt
does not leak code into the audio.

Two entry points:

* :class:`StreamingTTSNormalizer` — stateful, line-buffered. Call
  ``feed(chunk)`` with each chunk of streaming text and concatenate the
  returned pieces. Call ``flush()`` once at end of stream.
* :func:`normalize_for_tts` — single-shot helper for the PWA path that
  already has the full answer in hand.
"""

from __future__ import annotations

import re

_INLINE_CODE = re.compile(r"`([^`\n]+)`")
_BOLD = re.compile(r"\*\*([^*\n]+)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_UNDERSCORE_BOLD = re.compile(r"(?<!\w)__([^_\n]+)__(?!\w)")
_UNDERSCORE_ITALIC = re.compile(r"(?<!\w)_([^_\n]+)_(?!\w)")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_LINE_START_MARKER = re.compile(r"^\s*(?:#{1,6}|[-*])\s+", re.MULTILINE)
_HR = re.compile(r"^[-*_]{3,}\s*$", re.MULTILINE)
_CODE_FENCE = re.compile(r"```[^\n]*\n.*?\n```|~~~[^\n]*\n.*?\n~~~", re.DOTALL)
_BLANK_LINES = re.compile(r"\n\s*\n")
_FENCE_LINE = re.compile(r"^\s{0,3}(```|~~~)")


def _strip_inline(line: str) -> str:
    line = _LINK.sub(r"\1", line)
    line = _INLINE_CODE.sub(r"\1", line)
    line = _BOLD.sub(r"\1", line)
    line = _ITALIC.sub(r"\1", line)
    line = _UNDERSCORE_BOLD.sub(r"\1", line)
    line = _UNDERSCORE_ITALIC.sub(r"\1", line)
    return line


def normalize_for_tts(text: str) -> str:
    """Strip Markdown from ``text`` so TTS reads the words, not the punctuation."""
    text = _CODE_FENCE.sub("", text)
    text = _LINK.sub(r"\1", text)
    text = _INLINE_CODE.sub(r"\1", text)
    text = _LINE_START_MARKER.sub("", text)
    text = _BOLD.sub(r"\1", text)
    text = _ITALIC.sub(r"\1", text)
    text = _UNDERSCORE_BOLD.sub(r"\1", text)
    text = _UNDERSCORE_ITALIC.sub(r"\1", text)
    text = _HR.sub("", text)
    text = _BLANK_LINES.sub("。", text)
    # Drop remaining single newlines so output matches StreamingTTSNormalizer
    # (one logical sentence per line; TTS does its own chunking).
    text = text.replace("\n", "")
    return text.strip()


class StreamingTTSNormalizer:
    """Line-buffered equivalent of :func:`normalize_for_tts`.

    Tracks a pending blank-line separator so a single ``。`` is emitted before
    the next non-blank line, matching the single-shot behavior. Also tracks
    fenced code-block state so multi-line code blocks are dropped as a single
    unit, not line-by-line.
    """

    def __init__(self) -> None:
        self._line_buffer = ""
        self._in_code_block = False
        self._pending_blank = False

    def feed(self, chunk: str) -> str:
        if not chunk:
            return ""
        self._line_buffer += chunk
        out: list[str] = []
        while "\n" in self._line_buffer:
            line, self._line_buffer = self._line_buffer.split("\n", 1)
            emitted = self._consume(line)
            if emitted:
                out.append(emitted)
        return "".join(out)

    def flush(self) -> str:
        line, self._line_buffer = self._line_buffer, ""
        if not line:
            self._pending_blank = False
            return ""
        return self._consume(line)

    def _consume(self, line: str) -> str:
        if _FENCE_LINE.match(line):
            entering = not self._in_code_block
            self._in_code_block = not self._in_code_block
            # Exiting a code block leaves a "gap" in the spoken output — treat it
            # like a blank line so the next non-blank line gets a "。" prefix,
            # matching the single-shot behavior where the fence regex creates a
            # blank line that the blank-line rule turns into a sentence break.
            self._pending_blank = not entering
            return ""
        if self._in_code_block:
            return ""
        normalized = _LINE_START_MARKER.sub("", _strip_inline(line))
        if not normalized:
            self._pending_blank = True
            return ""
        if self._pending_blank:
            self._pending_blank = False
            return "。" + normalized
        return normalized
