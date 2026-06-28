# CLAUDE.md

This file provides repository guidance for coding agents.

## Project

Call Hermes is a FastAPI voice bridge with a Safari/PWA client. Browser microphone audio is sent over WebRTC, transcribed by Alibaba Cloud Model Studio, passed to an OpenAI-compatible Hermes chat endpoint, synthesized through realtime TTS, and returned over a WebRTC audio track.

There is no native iOS application in this repository. The supported client is the PWA in `server/app/static/`.

## Layout

- `server/app/main.py`: FastAPI application, authentication, health checks, WebRTC signaling, and static PWA hosting.
- `server/app/bridge/`: per-call WebRTC session and audio conversion.
- `server/app/integrations/`: DashScope ASR/TTS and Hermes clients.
- `server/app/pwa/`: HTTPS recording fallback endpoint and audio processing.
- `server/app/static/`: PWA UI, WebRTC client, device selection, and client diagnostics.
- `server/tests/`: pytest suite.
- `scripts/`: host-based launch and diagnostic scripts.
- `deploy/`: optional Caddy and coturn examples.

## Commands

```bash
cd server
source .venv/bin/activate
ruff check app tests
pytest -q
node --check app/static/app.js
node --check app/static/rtc.js
node --check app/static/ui.js
```

Run HTTPS from the repository root:

```bash
cp server/.env.example server/.env
./scripts/run_https.sh
```

The default HTTPS certificate paths are `ssl/fullchain.pem` and `ssl/privkey.pem`. Local `.env` files, certificates, logs, virtual environments, and PID files must remain untracked.

## Architecture Rules

- Secrets remain server-side. The PWA receives only a short-lived JWT after `/auth/session`.
- Keep the Hermes integration compatible with `/v1/chat/completions` streaming responses.
- Preserve 16 kHz mono PCM input for ASR and 48 kHz WebRTC output.
- Keep browser audio output routing under iOS control; only exposed input devices can be selected by the PWA.
- Maintain barge-in behavior and stop ASR audio forwarding while the microphone is muted.
- Add focused tests when changing shared session, audio, authentication, or streaming behavior.
