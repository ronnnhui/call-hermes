import base64
import logging
import os
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Header, HTTPException, Response, UploadFile, status
from pydantic import BaseModel

from app.auth import verify_bearer_token
from app.config import Settings, get_settings
from app.pwa.audio import transcode_to_wav_mono_16k_file, wav_duration_seconds
from app.pwa.service import voice_turn
from app.pwa.trace import TurnTrace

logger = logging.getLogger("call_hermes.pwa")


class TurnResponse(BaseModel):
    turn_id: str
    transcript: str
    answer: str
    audio_mime: str
    audio_base64: str
    timings: dict[str, int]


class TurnError(BaseModel):
    turn_id: str
    message: str


router = APIRouter(prefix="/pwa", tags=["pwa"])


@router.post("/turn", response_model=TurnResponse, deprecated=True)
async def pwa_turn(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
    audio: UploadFile = File(...),
) -> TurnResponse:
    verify_bearer_token(settings, authorization)
    response.headers["X-Call-Hermes-Mode"] = "fallback-pwa-turn"
    response.headers["Deprecation"] = "true"
    turn_id = uuid4().hex[:12]
    trace = TurnTrace(turn_id=turn_id, logger=logger)
    data = await audio.read(settings.pwa_max_upload_bytes + 1)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=TurnError(turn_id=turn_id, message="No audio was recorded.").model_dump(),
        )
    if len(data) > settings.pwa_max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=TurnError(
                turn_id=turn_id,
                message="Recording is too large. Please keep it under 60 seconds.",
            ).model_dump(),
        )

    suffix = Path(audio.filename or "").suffix
    try:
        with trace.stage("transcode"):
            wav_path = transcode_to_wav_mono_16k_file(data, suffix)
        try:
            logger.info(
                "turn_id=%s pwa turn start filename=%s content_type=%s bytes=%d wav=%s duration=%.2fs",
                turn_id,
                audio.filename,
                audio.content_type,
                len(data),
                wav_path,
                wav_duration_seconds(wav_path),
            )
            transcript, answer, wav = await voice_turn(settings, wav_path, trace)
        finally:
            try:
                os.unlink(wav_path)
            except OSError:
                logger.warning("turn_id=%s failed to remove temp wav %s", turn_id, wav_path, exc_info=True)
    except Exception as exc:  # noqa: BLE001
        message = friendly_error_message(exc)
        logger.exception("turn_id=%s pwa turn failed user_message=%s", turn_id, message)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=TurnError(turn_id=turn_id, message=message).model_dump(),
        ) from exc

    trace.timings["total_ms"] = trace.total_ms
    logger.info(
        "turn_id=%s pwa turn complete transcript_len=%d answer_len=%d wav_bytes=%d timings=%s",
        turn_id,
        len(transcript),
        len(answer),
        len(wav),
        trace.timings,
    )
    return TurnResponse(
        turn_id=turn_id,
        transcript=transcript,
        answer=answer,
        audio_mime="audio/wav",
        audio_base64=base64.b64encode(wav).decode("ascii"),
        timings=trace.timings,
    )


def friendly_error_message(exc: Exception) -> str:
    text = str(exc)
    if "Audio decode failed" in text:
        return "I could not read that recording. Please try recording again."
    if "empty transcript" in text or "ASR returned" in text:
        return "I could not hear speech clearly. Please try again."
    if "TTS" in text:
        return "Speech synthesis failed. Please try again."
    if "Hermes" in text:
        return "Hermes is temporarily unavailable."
    return "The voice turn failed. Please try again."
