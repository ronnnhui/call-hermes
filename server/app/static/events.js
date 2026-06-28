export function handleBridgeEvent(raw, context) {
  let event;
  try {
    event = JSON.parse(raw);
  } catch {
    return;
  }

  const { state, ui } = context;
  const logger = context.logger || null;
  logger?.debug("bridge event", { type: event.type, state: event.state || "", source: event.source || "" });

  if (event.type === "listening") {
    state.isSpeaking = false;
    ui.setStatus(state.isMuted ? "Microphone off" : "Listening");
    return;
  }
  if (event.type === "partial_transcript") {
    ui.setTranscript(event.text || "-");
    ui.setStatus(state.isMuted ? "Microphone off" : "Listening");
    return;
  }
  if (event.type === "final_transcript") {
    state.currentTranscript = event.text || "";
    state.currentAnswer = "";
    ui.setTranscript(state.currentTranscript);
    ui.setAnswer("-");
    ui.setStatus("Thinking");
    return;
  }
  if (event.type === "thinking") {
    state.currentTranscript = event.text || state.currentTranscript;
    ui.setTranscript(state.currentTranscript);
    ui.setStatus("Thinking");
    return;
  }
  if (event.type === "answer_delta") {
    state.currentAnswer += event.text || "";
    ui.setAnswer(state.currentAnswer);
    return;
  }
  if (event.type === "speaking") {
    state.isSpeaking = event.state === "start";
    if (event.state === "interrupted") {
      state.currentAnswer = "";
      ui.setAnswer("-");
      ui.setStatus("Interrupted");
    } else {
      ui.setStatus(state.isSpeaking ? "Speaking" : state.isMuted ? "Microphone off" : "Listening");
    }
    return;
  }
  if (event.type === "microphone") {
    state.isMuted = Boolean(event.muted);
    ui.setMuted(state.isMuted);
    ui.setStatus(state.isMuted ? "Microphone off" : "Listening");
    return;
  }
  if (event.type === "asr_state") {
    ui.setDebug(event.state === "stopped" ? "ASR paused" : "ASR active");
    return;
  }
  if (event.type === "vad_state") {
    if (event.state === "speech") {
      ui.setDebug("VAD speech detected; ASR active");
      ui.setVoiceActive(true);
    } else if (event.state === "silence") {
      ui.setDebug("VAD silence; ASR paused");
      ui.setVoiceActive(false);
    } else if (event.state === "muted") {
      ui.setDebug("VAD muted; ASR paused");
      ui.setVoiceActive(false);
    }
    return;
  }
  if (event.type === "error") {
    logger?.error("bridge error event", {
      source: event.source || "",
      message: event.message || "",
    });
    ui.setStatus(event.message || "Bridge error");
    ui.setDebug(event.source ? `Error ${event.source}` : "Error");
  }
}
