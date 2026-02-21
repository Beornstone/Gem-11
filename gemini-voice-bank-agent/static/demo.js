const sid = `s-${Math.random().toString(36).slice(2, 8)}`;
document.getElementById("sid").textContent = sid;

const live = document.getElementById("live");
const assistant = document.getElementById("assistant");
const action = document.getElementById("action");
const typedInput = document.getElementById("typedInput");

let currentAudio;

async function playAssistantAudio(text) {
  if (!text?.trim()) return;
  const res = await fetch("/api/voice/tts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) return;
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);

  if (currentAudio) {
    currentAudio.pause();
    URL.revokeObjectURL(currentAudio.src);
  }
  currentAudio = new Audio(url);
  currentAudio.onended = () => URL.revokeObjectURL(url);
  currentAudio.play();
}

async function sendTranscript(text) {
  if (!text.trim()) return;
  const res = await fetch("/api/agent/turn", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sid, transcript: text }),
  });
  const data = await res.json();
  assistant.textContent = data.assistant_say;
  action.textContent = JSON.stringify(data.ui_action, null, 2);
  await playAssistantAudio(data.assistant_say);
}

document.getElementById("sendTyped").addEventListener("click", () => {
  sendTranscript(typedInput.value);
  typedInput.value = "";
});

let recorder;
let mediaStream;

async function transcribeChunk(blob) {
  if (!blob || blob.size === 0) return;
  const form = new FormData();
  form.append("audio", blob, "chunk.webm");

  const sttRes = await fetch("/api/voice/stt", {
    method: "POST",
    body: form,
  });

  if (!sttRes.ok) {
    live.textContent = "Mic transcription unavailable. Use typed fallback.";
    return;
  }

  const data = await sttRes.json();
  const transcript = (data.transcript || "").trim();
  if (!transcript || transcript === "(ambient noise)") {
    return;
  }

  live.textContent = transcript;
  await sendTranscript(transcript);
}

const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");

startBtn.onclick = async () => {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recorder = new MediaRecorder(mediaStream, { mimeType: "audio/webm" });
    recorder.ondataavailable = (event) => {
      transcribeChunk(event.data);
    };
    recorder.start(4000);
    live.textContent = "Listening...";
  } catch (err) {
    live.textContent = "Microphone unavailable. Use typed fallback.";
  }
};

stopBtn.onclick = () => {
  if (recorder && recorder.state !== "inactive") recorder.stop();
  if (mediaStream) mediaStream.getTracks().forEach((track) => track.stop());
  live.textContent = "Stopped.";
};
