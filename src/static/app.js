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

  let pendingSpeech = "";

  function preferVoice() {
    const voices = speechSynthesis.getVoices();
    if (!voices.length) return null;
    const preferred = voices.find((v) => /female|samantha|google us english|karen|moira|zira/i.test(`${v.name} ${v.lang}`))
      || voices.find((v) => v.lang.startsWith("en"))
      || voices[0];
    return preferred;
  }

  function speakChunk(text) {
    if (!speakReplies || !canSpeak) return;
    const utter = new SpeechSynthesisUtterance(text);
    const voice = preferVoice();
    if (voice) utter.voice = voice;
    utter.rate = 1.05;
    utter.pitch = 1.08;
    utter.onstart = () => setMood("speaking", "Flora is speaking");
    utter.onend = () => {
      if (!speechSynthesis.speaking && !pendingSpeech) {
        setMood("happy", "Flora is with you");
      }
    };
    utter.onerror = () => setMood("idle", "Flora is listening");
    speechSynthesis.speak(utter);
  }

  function flushSpeech(force) {
    if (!speakReplies || !canSpeak) {
      pendingSpeech = "";
      return;
    }
    let text = pendingSpeech;
    if (!force) {
      const match = text.match(/^[\s\S]*?[.!?…](?=\s|$)/);
      if (!match) return;
      text = match[0];
      pendingSpeech = pendingSpeech.slice(text.length);
    } else {
      pendingSpeech = "";
    }
    text = text.trim();
    if (text) speakChunk(text);
  }

  function speak(text) {
    if (!speakReplies || !canSpeak) return;
    speechSynthesis.cancel();
    pendingSpeech = "";
    speakChunk(text);
  }

  function stopSpeaking() {
    pendingSpeech = "";
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

    const assistantBubble = appendBubble("assistant", "");
    let full = "";

    try {
      const res = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const detail = data.detail || "Something went wrong talking to Flora.";
        assistantBubble.remove();
        appendBubble("system", detail);
        setMood("idle", "Flora is listening");
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      setMood("speaking", "Flora is answering…");

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";
        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data:")) continue;
          let payload;
          try {
            payload = JSON.parse(line.slice(5).trim());
          } catch {
            continue;
          }
          if (payload.error) {
            assistantBubble.remove();
            appendBubble("system", payload.error);
            setMood("idle", "Flora is listening");
            return;
          }
          if (payload.token) {
            full += payload.token;
            assistantBubble.textContent = full;
            messagesEl.scrollTop = messagesEl.scrollHeight;
            pendingSpeech += payload.token;
            flushSpeech(false);
          }
        }
      }

      if (!full.trim()) {
        assistantBubble.textContent = "…";
      }
      flushSpeech(true);
      if (!canSpeak || !speakReplies) {
        setMood("happy", "Flora is with you");
        setTimeout(() => setMood("idle", "Flora is listening"), 1800);
      }
      setTimeout(() => { refreshMemories(); }, 1200);
    } catch (err) {
      assistantBubble.remove();
      appendBubble("system", "Could not reach Flora’s server. Is it running?");
      setMood("idle", "Flora is listening");
    } finally {
      busy = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }

  function micErrorMessage(code) {
    switch (code) {
      case "not-allowed":
      case "service-not-allowed":
        return "Microphone blocked. Allow mic access for this site in the browser address bar, then try again.";
      case "no-speech":
        return "I didn’t catch that — click the mic and speak a bit louder.";
      case "audio-capture":
        return "No microphone found. Plug one in or check system sound settings.";
      case "network":
        return "Speech recognition needs an internet connection in Chrome/Edge (browser limitation). Check you’re online, then retry.";
      case "aborted":
        return null;
      default:
        return `Mic error (${code || "unknown"}). Try Chrome/Edge on http://127.0.0.1:8000.`;
    }
  }

  function showMicStatus(text, isError) {
    if (!text) return;
    voiceHint.textContent = text;
    voiceHint.style.color = isError ? "var(--petal-deep)" : "";
    if (isError) appendBubble("system", text);
  }

  async function ensureMicPermission() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      return true;
    }
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach((t) => t.stop());
    return true;
  }

  function setupMic() {
    if (!SpeechRecognition) {
      micBtn.disabled = true;
      micBtn.title = "Speech recognition not supported in this browser";
      voiceHint.textContent = "Mic needs Chrome or Edge. Flora can still speak replies in most browsers.";
      return;
    }

    if (!window.isSecureContext) {
      micBtn.disabled = true;
      voiceHint.textContent = "Mic only works on https:// or http://127.0.0.1 — open Flora via http://127.0.0.1:8000";
      return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = navigator.language || "en-US";

    recognition.onstart = () => {
      listening = true;
      micBtn.setAttribute("aria-pressed", "true");
      setMood("listening", "Flora is listening to you");
      showMicStatus("Listening… speak now, then pause.", false);
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
      if (last && last.isFinal && transcript.trim()) {
        sendMessage(transcript);
      }
    };

    recognition.onerror = (event) => {
      listening = false;
      micBtn.setAttribute("aria-pressed", "false");
      setMood("idle", "Flora is listening");
      const msg = micErrorMessage(event.error);
      if (msg) showMicStatus(msg, true);
    };

    recognition.onend = () => {
      listening = false;
      micBtn.setAttribute("aria-pressed", "false");
      if (!busy) setMood("idle", "Flora is listening");
    };

    micBtn.addEventListener("click", async () => {
      if (busy) return;
      if (listening) {
        recognition.stop();
        return;
      }
      try {
        await ensureMicPermission();
      } catch {
        showMicStatus(
          "Microphone blocked. Click the lock/tune icon near the URL → allow Microphone → reload.",
          true
        );
        return;
      }
      try {
        recognition.start();
      } catch {
        try {
          recognition.stop();
          setTimeout(() => recognition.start(), 200);
        } catch {
          showMicStatus("Could not start the mic. Refresh the page and try again.", true);
        }
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
