(() => {
  const messagesEl = document.getElementById("messages");
  const memoryListEl = document.getElementById("memoryList");
  const memoryEmptyEl = document.getElementById("memoryEmpty");
  const composer = document.getElementById("composer");
  const input = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendBtn");
  const micBtn = document.getElementById("micBtn");
  const speakToggle = document.getElementById("speakToggle");
  const clearChatBtn = document.getElementById("clearChatBtn");
  const clearMemoryBtn = document.getElementById("clearMemoryBtn");
  const statusPill = document.getElementById("statusPill");
  const floraStage = document.getElementById("floraStage");
  const floraCaption = document.getElementById("floraCaption");
  const voiceHint = document.getElementById("voiceHint");

  let busy = false;
  let speakReplies = true;
  let recognition = null;
  let listening = false;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const canSpeak = "speechSynthesis" in window;

  const mouthEl = document.querySelector(".flora-face .mouth");
  const mouthPaths = {
    idle: "M104 178 Q120 190 136 178",
    listening: "M106 180 Q120 184 134 180",
    thinking: "M108 182 Q120 178 132 182",
    speaking: "M106 180 Q120 168 134 180",
    happy: "M100 176 Q120 198 140 176",
  };
  let speakMouthTimer = null;

  function setMouth(path) {
    if (mouthEl) mouthEl.setAttribute("d", path);
  }

  function setMood(mood, caption) {
    floraStage.dataset.mood = mood;
    if (caption) floraCaption.textContent = caption;
    if (speakMouthTimer) {
      clearInterval(speakMouthTimer);
      speakMouthTimer = null;
    }
    if (mood === "speaking") {
      let open = false;
      setMouth(mouthPaths.speaking);
      speakMouthTimer = setInterval(() => {
        open = !open;
        setMouth(open ? mouthPaths.speaking : mouthPaths.listening);
      }, 180);
    } else {
      setMouth(mouthPaths[mood] || mouthPaths.idle);
    }
  }

  function appendBubble(role, text) {
    const div = document.createElement("div");
    div.className = `bubble ${role}`;
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
  }

  function autoResize() {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
  }

  function preferVoice() {
    const voices = speechSynthesis.getVoices();
    if (!voices.length) return null;
    const preferred = voices.find((v) => /female|samantha|google us english|karen|moira|zira/i.test(`${v.name} ${v.lang}`))
      || voices.find((v) => v.lang.startsWith("en"))
      || voices[0];
    return preferred;
  }

  function speak(text) {
    if (!speakReplies || !canSpeak) return;
    speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    const voice = preferVoice();
    if (voice) utter.voice = voice;
    utter.rate = 1.02;
    utter.pitch = 1.08;
    utter.onstart = () => setMood("speaking", "Flora is speaking");
    utter.onend = () => setMood("happy", "Flora is with you");
    utter.onerror = () => setMood("idle", "Flora is listening");
    speechSynthesis.speak(utter);
  }

  function stopSpeaking() {
    if (canSpeak) speechSynthesis.cancel();
  }

  async function refreshHealth() {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      const ollama = data.ollama || {};
      if (!ollama.ok) {
        statusPill.dataset.state = "error";
        statusPill.textContent = "Ollama offline — start it locally";
        return;
      }
      if (!ollama.model_ready) {
        statusPill.dataset.state = "warn";
        statusPill.textContent = `Pull model: ollama pull ${ollama.model}`;
        return;
      }
      statusPill.dataset.state = "ok";
      statusPill.textContent = `Ready · ${ollama.model}`;
    } catch {
      statusPill.dataset.state = "error";
      statusPill.textContent = "Server unreachable";
    }
  }

  function renderMemories(memories) {
    memoryListEl.innerHTML = "";
    const list = memories || [];
    memoryEmptyEl.hidden = list.length > 0;
    for (const mem of list) {
      const li = document.createElement("li");
      const key = document.createElement("span");
      key.className = "key";
      key.textContent = mem.key;
      const value = document.createElement("span");
      value.className = "value";
      value.textContent = mem.value;
      const del = document.createElement("button");
      del.type = "button";
      del.textContent = "Forget";
      del.addEventListener("click", async () => {
        const res = await fetch(`/api/memory/${encodeURIComponent(mem.key)}`, { method: "DELETE" });
        const data = await res.json();
        renderMemories(data.memories || []);
      });
      li.append(key, value, del);
      memoryListEl.appendChild(li);
    }
  }

  async function refreshMemories() {
    const res = await fetch("/api/memory");
    const data = await res.json();
    renderMemories(data.memories || []);
  }

  async function refreshHistory() {
    const res = await fetch("/api/history");
    const data = await res.json();
    messagesEl.innerHTML = "";
    const msgs = data.messages || [];
    if (!msgs.length) {
      appendBubble(
        "system",
        "Hi — I’m Flora. Talk about anything. I’ll remember what matters, and I’m here to lift you up."
      );
      return;
    }
    for (const msg of msgs) {
      if (msg.role === "user" || msg.role === "assistant") {
        appendBubble(msg.role, msg.content);
      }
    }
  }

  async function sendMessage(text) {
    const message = (text || "").trim();
    if (!message || busy) return;

    busy = true;
    sendBtn.disabled = true;
    stopSpeaking();
    appendBubble("user", message);
    input.value = "";
    autoResize();
    setMood("thinking", "Flora is thinking…");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = data.detail || "Something went wrong talking to Flora.";
        appendBubble("system", detail);
        setMood("idle", "Flora is listening");
        return;
      }
      appendBubble("assistant", data.reply);
      speak(data.reply);
      if (!canSpeak || !speakReplies) {
        setMood("happy", "Flora is with you");
        setTimeout(() => setMood("idle", "Flora is listening"), 2200);
      }
      if (data.new_memories && data.new_memories.length) {
        await refreshMemories();
      } else {
        await refreshMemories();
      }
    } catch (err) {
      appendBubble("system", "Could not reach Flora’s server. Is it running?");
      setMood("idle", "Flora is listening");
    } finally {
      busy = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }

  function setupMic() {
    if (!SpeechRecognition) {
      micBtn.disabled = true;
      micBtn.title = "Speech recognition not supported in this browser";
      voiceHint.textContent = "Tip: use Chrome/Edge for mic input. Flora can still speak replies in most browsers.";
      return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      listening = true;
      micBtn.setAttribute("aria-pressed", "true");
      setMood("listening", "Flora is listening to you");
      stopSpeaking();
    };

    recognition.onresult = (event) => {
      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        transcript += event.results[i][0].transcript;
      }
      input.value = transcript.trim();
      autoResize();
      const last = event.results[event.results.length - 1];
      if (last && last.isFinal) {
        sendMessage(transcript);
      }
    };

    recognition.onerror = () => {
      listening = false;
      micBtn.setAttribute("aria-pressed", "false");
      setMood("idle", "Flora is listening");
    };

    recognition.onend = () => {
      listening = false;
      micBtn.setAttribute("aria-pressed", "false");
      if (!busy) setMood("idle", "Flora is listening");
    };

    micBtn.addEventListener("click", () => {
      if (busy) return;
      if (listening) {
        recognition.stop();
        return;
      }
      try {
        recognition.start();
      } catch {
        /* already started */
      }
    });
  }

  composer.addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage(input.value);
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input.value);
    }
  });

  input.addEventListener("input", autoResize);

  speakToggle.addEventListener("click", () => {
    speakReplies = !speakReplies;
    speakToggle.setAttribute("aria-pressed", String(speakReplies));
    speakToggle.textContent = speakReplies ? "Voice reply on" : "Voice reply off";
    if (!speakReplies) stopSpeaking();
  });

  clearChatBtn.addEventListener("click", async () => {
    stopSpeaking();
    await fetch("/api/history", { method: "DELETE" });
    await refreshHistory();
    setMood("idle", "Flora is listening");
  });

  clearMemoryBtn.addEventListener("click", async () => {
    if (!confirm("Forget everything Flora remembers about you on this device?")) return;
    await fetch("/api/memory", { method: "DELETE" });
    await refreshMemories();
  });

  if (canSpeak) {
    speechSynthesis.onvoiceschanged = () => preferVoice();
  } else {
    speakToggle.disabled = true;
    speakToggle.textContent = "Voice reply unavailable";
    speakReplies = false;
  }

  setupMic();
  refreshHealth();
  refreshHistory();
  refreshMemories();
  setInterval(refreshHealth, 15000);
  setMood("idle", "Flora is listening");
  input.focus();
})();
