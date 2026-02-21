const sid = `s-${Math.random().toString(36).slice(2, 8)}`;
document.getElementById("sid").textContent = sid;

const live = document.getElementById("live");
const assistant = document.getElementById("assistant");
const action = document.getElementById("action");
const typedInput = document.getElementById("typedInput");

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
  if ("speechSynthesis" in window) {
    window.speechSynthesis.speak(new SpeechSynthesisUtterance(data.assistant_say));
  }
}

document.getElementById("sendTyped").addEventListener("click", () => {
  sendTranscript(typedInput.value);
  typedInput.value = "";
});

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!SpeechRecognition) {
  live.textContent = "Web Speech API unavailable. Use typed fallback.";
  document.getElementById("startBtn").disabled = true;
  document.getElementById("stopBtn").disabled = true;
} else {
  const rec = new SpeechRecognition();
  rec.continuous = true;
  rec.interimResults = true;

  rec.onresult = (event) => {
    let interim = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const t = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        sendTranscript(t);
      } else {
        interim += t;
      }
    }
    live.textContent = interim;
  };

  document.getElementById("startBtn").onclick = () => rec.start();
  document.getElementById("stopBtn").onclick = () => rec.stop();
}
