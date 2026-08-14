const STATES = Object.freeze({
  READY: "READY",
  CONNECTING: "CONNECTING",
  LISTENING: "LISTENING",
  SPEAKING: "SPEAKING",
  ENDED: "ENDED",
  ERROR: "ERROR",
});

const copy = {
  READY: ["Ready to talk", "Start a short, private voice conversation when you are ready."],
  CONNECTING: ["Connecting...", "Please wait while DhanBuddy joins."],
  LISTENING: ["Listening to you", "Speak naturally. DhanBuddy is listening."],
  SPEAKING: ["DhanBuddy is speaking", "You will hear the response through your speaker."],
  ENDED: ["Conversation ended", "You can start another conversation whenever you are ready."],
};

const ui = {
  label: document.querySelector("#state-label"),
  title: document.querySelector("#status-title"),
  detail: document.querySelector("#status-detail"),
  visualizer: document.querySelector("#visualizer"),
  start: document.querySelector("#start-button"),
  end: document.querySelector("#end-button"),
  retry: document.querySelector("#retry-button"),
  upload: document.querySelector("#upload-button"),
  billInput: document.querySelector("#bill-input"),
  uploadNote: document.querySelector("#upload-note"),
  errorBox: document.querySelector("#error-box"),
  errorTitle: document.querySelector("#error-title"),
  errorMessage: document.querySelector("#error-message"),
  audioOutput: document.querySelector("#audio-output"),
};

let agentState = STATES.READY;
let room = null;
let endingIntentionally = false;

function setAgentState(state, error = null) {
  agentState = state;
  const visibleState = state === STATES.ERROR ? STATES.READY : state;
  const [title, detail] = copy[visibleState];
  ui.label.textContent = state;
  ui.title.textContent = title;
  ui.detail.textContent = detail;
  ui.visualizer.className = `visualizer ${visibleState.toLowerCase()}`;
  ui.errorBox.hidden = !error;
  ui.start.hidden = ![STATES.READY, STATES.ENDED].includes(state);
  ui.start.textContent = state === STATES.ENDED ? "Start again" : "Start conversation";
  ui.end.hidden = ![STATES.CONNECTING, STATES.LISTENING, STATES.SPEAKING].includes(state);
  ui.retry.hidden = state !== STATES.ERROR;
  ui.upload.hidden = ![STATES.READY, STATES.ENDED, STATES.ERROR].includes(state);
  ui.start.disabled = state === STATES.CONNECTING;

  if (error) {
    ui.errorTitle.textContent = error.title;
    ui.errorMessage.textContent = error.message;
  }
}

function friendlyError(error) {
  console.error("DhanBuddy connection error", error);
  const denied = error?.name === "NotAllowedError" || error?.name === "PermissionDeniedError";
  return denied
    ? {
        title: "Microphone access is blocked.",
        message: "Enable microphone permission in your browser settings and try again.",
      }
    : {
        title: "DhanBuddy could not connect.",
        message: "Check your connection and try again.",
      };
}

function attachRemoteAudio(track) {
  if (track.kind !== LivekitClient.Track.Kind.Audio) return;
  const element = track.attach();
  element.autoplay = true;
  ui.audioOutput.appendChild(element);
}

async function startConversation() {
  if (!window.LivekitClient) {
    setAgentState(STATES.ERROR, { title: "Voice service did not load.", message: "Check your connection and try again." });
    return;
  }

  endingIntentionally = false;
  setAgentState(STATES.CONNECTING);
  try {
    const permissionStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    permissionStream.getTracks().forEach((track) => track.stop());

    const response = await fetch("/api/token", { method: "POST" });
    if (!response.ok) throw new Error(`Token request failed with status ${response.status}`);
    const { serverUrl, participantToken } = await response.json();

    room = new LivekitClient.Room({ adaptiveStream: true, disconnectOnPageLeave: true });
    room
      .on(LivekitClient.RoomEvent.TrackSubscribed, attachRemoteAudio)
      .on(LivekitClient.RoomEvent.ActiveSpeakersChanged, (speakers) => {
        const agentSpeaking = speakers.some(
          (participant) => participant.identity !== room.localParticipant.identity,
        );
        setAgentState(agentSpeaking ? STATES.SPEAKING : STATES.LISTENING);
      })
      .on(LivekitClient.RoomEvent.Disconnected, () => {
        if (!endingIntentionally) setAgentState(STATES.ENDED);
        room = null;
      })
      .on(LivekitClient.RoomEvent.MediaDevicesError, (error) => {
        setAgentState(STATES.ERROR, friendlyError(error));
      });

    await room.connect(serverUrl, participantToken);
    await room.startAudio();
    await room.localParticipant.setMicrophoneEnabled(true);
    setAgentState(STATES.LISTENING);
  } catch (error) {
    if (room) await room.disconnect();
    room = null;
    setAgentState(STATES.ERROR, friendlyError(error));
  }
}

async function endConversation() {
  endingIntentionally = true;
  if (room) await room.disconnect();
  room = null;
  ui.audioOutput.replaceChildren();
  setAgentState(STATES.ENDED);
}

ui.start.addEventListener("click", startConversation);
ui.retry.addEventListener("click", startConversation);
ui.end.addEventListener("click", endConversation);
ui.upload.addEventListener("click", () => ui.billInput.click());
ui.billInput.addEventListener("change", async () => {
  const file = ui.billInput.files[0];
  if (!file) return;
  ui.uploadNote.hidden = false;
  ui.uploadNote.textContent = "Reading your bill...";
  const form = new FormData();
  form.append("file", file);
  try {
    const response = await fetch("/api/documents", { method: "POST", body: form });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || "Upload failed");
    const merchant = result.document.merchant || "Unknown merchant";
    const count = result.document.line_items.length;
    ui.uploadNote.textContent = `Saved ${merchant} with ${count} detected item${count === 1 ? "" : "s"}.`;
  } catch (error) {
    console.error("Bill upload error", error);
    ui.uploadNote.textContent = error.message || "DhanBuddy could not read that bill. Please try again.";
  } finally {
    ui.billInput.value = "";
  }
});
window.addEventListener("pagehide", () => room?.disconnect());
setAgentState(STATES.READY);

async function refreshHealth() {
  try {
    const response = await fetch("/api/health"); if (!response.ok) throw new Error("Health unavailable");
    const health = await response.json();
    document.querySelector("#health-overall").textContent = `● ${health.status === "healthy" ? "Agent healthy" : "Agent unavailable"}`;
    document.querySelector("#health-details").textContent = `Database ${health.database_status} · Agent ${health.agent_status} · LiveKit ${health.livekit_status}`;
    document.querySelector("#health-activity").textContent = health.last_activity ? `Last activity ${new Date(health.last_activity).toLocaleString()}` : "No call activity yet";
  } catch (error) {
    console.error("Health check failed", error);
    document.querySelector("#health-overall").textContent = "● Agent unavailable";
  }
}
refreshHealth(); setInterval(refreshHealth, 10000);
