export function createUi() {
  const ui = {
    statusEl: document.querySelector("#status"),
    deviceStatusEl: document.querySelector("#deviceStatusText"),
    transcriptEl: document.querySelector("#transcriptText"),
    answerEl: document.querySelector("#answerText"),
    debugEl: document.querySelector("#debugText"),
    recordButton: document.querySelector("#recordButton"),
    micButton: document.querySelector("#replayButton"),
    debugForm: document.querySelector("#debugForm"),
    debugInput: document.querySelector("#debugInput"),
    debugSendButton: document.querySelector("#debugSendButton"),
    debugEndButton: document.querySelector("#debugEndButton"),
    replyAudio: document.querySelector("#replyAudio"),
    settingsButton: document.querySelector("#settingsButton"),
    settingsDialog: document.querySelector("#settingsDialog"),
    audioDeviceDialog: document.querySelector("#audioDeviceDialog"),
    audioDeviceList: document.querySelector("#audioDeviceList"),
    audioDeviceHelp: document.querySelector("#audioDeviceHelp"),
    settingsFocusTarget: document.querySelector("#settingsFocusTarget"),
    bridgeUrlInput: document.querySelector("#bridgeUrlInput"),
    secretInput: document.querySelector("#secretInput"),
    ttsVoiceSelect: document.querySelector("#ttsVoiceSelect"),
    ttsVoiceDescription: document.querySelector("#ttsVoiceDescription"),
    speechRateInput: document.querySelector("#speechRateInput"),
    speechRateValue: document.querySelector("#speechRateValue"),
    debugModeInput: document.querySelector("#debugModeInput"),
    saveSettingsButton: document.querySelector("#saveSettingsButton"),
  };

  ui.micButton.disabled = true;
  ui.debugSendButton.disabled = true;
  ui.micButton.setAttribute("aria-label", "Mute microphone");

  return {
    ...ui,
    setStatus(text) {
      ui.statusEl.textContent = text;
      document.body.dataset.status = statusKind(text);
    },
    setDebug(text) {
      ui.debugEl.textContent = text || "No debug information.";
    },
    setDeviceStatus(text, details = "") {
      const label = ui.deviceStatusEl.querySelector(".device-label");
      if (label) {
        label.textContent = text;
      }
      ui.deviceStatusEl.dataset.device = deviceKind(text, details);
      ui.deviceStatusEl.setAttribute("aria-label", details || text);
      ui.deviceStatusEl.title = details || text;
    },
    setAudioDevices(devices, selectedDeviceId = "") {
      ui.audioDeviceList.replaceChildren();
      devices.forEach((device, index) => {
        const button = document.createElement("button");
        const selected = device.deviceId === selectedDeviceId
          || (!selectedDeviceId && device.isCurrent)
          || (!selectedDeviceId && index === 0);
        button.type = "button";
        button.className = "device-option";
        button.dataset.deviceId = device.deviceId;
        button.setAttribute("role", "option");
        button.setAttribute("aria-selected", String(selected));
        button.innerHTML = `<span class="device-option-icon" aria-hidden="true"></span><span>${escapeHtml(device.label)}</span><span class="device-check" aria-hidden="true">✓</span>`;
        ui.audioDeviceList.append(button);
      });
    },
    setCallingState(isCalling, options = {}) {
      document.body.classList.toggle("calling", isCalling);
      document.body.classList.toggle("debug-mode", Boolean(options.debugMode));
      ui.recordButton.disabled = false;
      ui.recordButton.setAttribute("aria-label", isCalling ? "End call" : "Start call");
      ui.micButton.disabled = !isCalling || Boolean(options.debugMode);
      ui.debugSendButton.disabled = !isCalling || !Boolean(options.debugMode);
      if (!isCalling) {
        document.body.classList.remove("muted");
        document.body.classList.remove("debug-mode");
        document.body.classList.remove("voice-active");
        ui.micButton.setAttribute("aria-label", "Mute microphone");
        ui.debugInput.value = "";
      }
    },
    setMuted(isMuted) {
      document.body.classList.toggle("muted", isMuted);
      ui.micButton.setAttribute("aria-label", isMuted ? "Unmute microphone" : "Mute microphone");
    },
    setFallbackMode(isFallback) {
      document.body.classList.toggle("fallback-mode", isFallback);
      document.body.classList.toggle("calling", isFallback);
      ui.recordButton.disabled = false;
      ui.recordButton.setAttribute("aria-label", isFallback ? "Exit fallback mode" : "Start call");
      ui.micButton.disabled = !isFallback;
      ui.micButton.setAttribute("aria-label", "Record fallback turn");
      if (!isFallback) {
        document.body.classList.remove("fallback-recording");
        document.body.classList.remove("voice-active");
      }
    },
    setFallbackRecording(isRecording) {
      document.body.classList.toggle("fallback-recording", isRecording);
      ui.micButton.setAttribute("aria-label", isRecording ? "Stop and send" : "Record fallback turn");
    },
    setVoiceActive(isActive) {
      document.body.classList.toggle("voice-active", isActive);
    },
    resetConversation() {
      ui.transcriptEl.textContent = "-";
      ui.answerEl.textContent = "-";
      ui.debugEl.textContent = "No debug information.";
    },
    setTranscript(text) {
      ui.transcriptEl.textContent = text || "-";
    },
    setAnswer(text) {
      ui.answerEl.textContent = text || "-";
    },
    setSpeechRateValue(value) {
      ui.speechRateValue.textContent = `${Number(value).toFixed(2)}x`;
    },
  };
}

function escapeHtml(value) {
  const element = document.createElement("span");
  element.textContent = String(value);
  return element.innerHTML;
}

function deviceKind(text, details = "") {
  const normalized = `${text} ${details}`.toLowerCase();
  if (normalized.includes("muted")) {
    return "muted";
  }
  if (normalized.includes("bluetooth") || normalized.includes("airpods") || normalized.includes("headset") || normalized.includes("headphone") || normalized.includes("耳机")) {
    return "headset";
  }
  if (normalized.includes("output")) {
    return "output";
  }
  return "mic";
}

function statusKind(text) {
  const normalized = String(text).toLowerCase();
  if (normalized.includes("lost") || normalized.includes("failed") || normalized.includes("error")) {
    return "error";
  }
  if (normalized.includes("unstable") || normalized.includes("reconnecting") || normalized.includes("connecting")) {
    return "busy";
  }
  if (normalized.includes("speaking") || normalized.includes("playing")) {
    return "speaking";
  }
  if (normalized.includes("off") || normalized.includes("muted")) {
    return "muted";
  }
  if (normalized.includes("listening")) {
    return "listening";
  }
  return "idle";
}
