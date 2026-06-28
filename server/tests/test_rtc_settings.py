import pytest
from fastapi import HTTPException

from app.config import Settings
from app.main import OfferRequest, _settings_for_offer


def _settings() -> Settings:
    return Settings(app_shared_secret="x" * 32, jwt_secret="y" * 32)


def test_offer_overrides_tts_voice_and_speech_rate() -> None:
    settings = _settings()
    offer = OfferRequest(
        sdp="v=0",
        tts_voice="Ryan",
        tts_speech_rate=1.25,
    )

    session_settings = _settings_for_offer(settings, offer)

    assert session_settings.dashscope_tts_voice == "Ryan"
    assert session_settings.dashscope_tts_speech_rate == 1.25
    assert settings.dashscope_tts_voice == "Cherry"


def test_offer_rejects_unknown_tts_voice() -> None:
    with pytest.raises(HTTPException):
        _settings_for_offer(_settings(), OfferRequest(sdp="v=0", tts_voice="Unknown"))


def test_offer_rejects_out_of_range_speech_rate() -> None:
    with pytest.raises(HTTPException):
        _settings_for_offer(_settings(), OfferRequest(sdp="v=0", tts_speech_rate=2.5))
