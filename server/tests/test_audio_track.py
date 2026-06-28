import numpy as np

from app.bridge.audio import QueueAudioTrack


async def test_playback_does_not_end_before_utterance_finished() -> None:
    track = QueueAudioTrack(prebuffer_seconds=0)
    pcm = np.zeros(960, dtype=np.int16).tobytes()

    await track.push_pcm16(pcm, sample_rate=48000)
    await track.recv()

    assert track._playing_audio is True
    assert track._idle_event.is_set() is False

    await track.recv()

    assert track._playing_audio is True
    assert track._underrun_frames == 1

    track.finish_utterance()
    await track.recv()

    assert track._playing_audio is False
    assert track._idle_event.is_set() is True
