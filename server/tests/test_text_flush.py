from app.bridge.session import _should_flush


def test_flushes_sentence_end() -> None:
    assert _should_flush("你好。")


def test_flushes_long_text() -> None:
    assert _should_flush("这是一段足够长的文本，用来触发流式语音合成分块。")
