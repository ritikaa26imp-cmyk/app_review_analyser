# Flora

A fully local personal companion you can talk with every day — free of cost.

Flora has a face, remembers key things about you on your machine, and aims to lift your spirits and motivation. Chat by typing or **speaking**; she can **read replies aloud** using your browser’s built-in speech features. No cloud AI bills.

## What you need

1. **Python 3.10+**
2. **[Ollama](https://ollama.com)** (runs the language model on your computer)
3. A modern browser (**Chrome or Edge** recommended for microphone input)

## Setup

### 1. Install Ollama and pull a model

```bash
# Install from https://ollama.com , then:
ollama serve
ollama pull llama3.2
```

Lighter alternatives if your machine is small:

```bash
ollama pull phi3
# or
ollama pull gemma2:2b
```

If you use another model, set it when starting Flora:

```bash
export OLLAMA_MODEL=phi3
```

### 2. Install Flora

```bash
cd /path/to/this/repo
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run Flora

```bash
python main.py
```

Open **http://127.0.0.1:8000** in your browser.

## Speed tips

Flora streams replies so you see/hear the first words sooner. Still, local models on CPU can feel slow.

- Prefer a small model: `gemma2:2b` or `phi3` on modest machines
- Keep Ollama running so the model stays warm (`keep_alive` defaults to 60m)
- A GPU makes a big difference if you have one
- Memory extraction no longer blocks chat replies (runs in the background)

## Talking and listening

| Feature | How |
|--------|-----|
| **Speak to Flora** | Click the mic button and talk. When you pause, your words are sent. |
| **Hear Flora** | “Voice reply on” (default). She speaks each answer aloud. Toggle off anytime. |
| **Type** | Works the same as voice — mix both freely. |

Speech uses the **Web Speech API** in your browser (free, no API keys). Mic access may ask for permission once. Recognition works best in Chromium-based browsers.

### Mic not working?

1. Use **Chrome or Edge** (Firefox often cannot listen).
2. Open Flora at **http://127.0.0.1:8000** (not a LAN IP / random host).
3. When prompted, click **Allow** for the microphone (or: lock icon near the URL → Site settings → Microphone → Allow).
4. Stay **online** — Chrome/Edge speech-to-text uses a browser cloud service (still free; no Flora API key). Hearing Flora aloud works offline.

## Memory

Flora stores short facts (name, goals, preferences, and so on) in a local SQLite file at `data/flora.db`. Nothing is uploaded. You can forget individual facts or clear everything from the side panel.

## Configuration

Optional environment variables:

| Variable | Default | Meaning |
|----------|---------|---------|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama server |
| `OLLAMA_MODEL` | `llama3.2` | Model name |
| `HOST` | `127.0.0.1` | Bind address |
| `PORT` | `8000` | Web port |

## Privacy

Everything stays on your device: chat history, memories, and model inference via Ollama. Flora is a supportive companion, not a therapist — seek real-world help in a crisis.
