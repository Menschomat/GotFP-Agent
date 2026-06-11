# Text Adventure Bot (Autonomous ADK Agent)

An advanced, autonomous AI agent built on the **Google Agent Development Kit (ADK)** designed to play and dominate the text adventure game *The Garden of the Forgotten Prompt*.

Inspired by classic text adventures like Zork and Colossal Cave Adventure, this game serves as an interactive playground where the bot parses descriptions, solves logical puzzles, manages inventory constraints, collects treasures, and navigates complex environments to climb the global leaderboard.

---

## 🚀 Key Features

* **Modular Software Architecture**: Built with clean code principles. Features are decoupled into isolated modules:
  * [agent.py](file:///workspaces/GardenOfTheForgottenPrompt/src/text_adventure_bot/agent.py) — Slim orchestrator.
  * [config.py](file:///workspaces/GardenOfTheForgottenPrompt/src/text_adventure_bot/config.py) — Environment and model configs.
  * [state.py](file:///workspaces/GardenOfTheForgottenPrompt/src/text_adventure_bot/state.py) — Typed game state tracking.
  * [api_client.py](file:///workspaces/GardenOfTheForgottenPrompt/src/text_adventure_bot/api_client.py) — Dry HTTP communication layer.
  * [logger.py](file:///workspaces/GardenOfTheForgottenPrompt/src/text_adventure_bot/logger.py) — Markdown game-session logging.
  * [validation.py](file:///workspaces/GardenOfTheForgottenPrompt/src/text_adventure_bot/validation.py) — Local rule validation (e.g. inventory constraints).
  * [knowledge.py](file:///workspaces/GardenOfTheForgottenPrompt/src/text_adventure_bot/knowledge.py) — Persistent knowledge base.
* **Persistent Long-Term Memory**: The bot learns between runs! It records passwords, path routes, and puzzle solutions into a local JSON database. When the bot starts a level or moves to a room, the relevant facts are automatically injected as context (`persistent_knowledge` or `room_memory`), allowing it to skip redundant exploration.
* **Natively Configured Context Caching**: Utilizes ADK's `ContextCacheConfig` to cache the system prompt, tool schemas, and chat history. This reduces token costs and latency by reusing attention states on Gemini 2.0+ models.
* **GCP Score Aware (`ON_GCP` Flag)**: Detects whether it is running locally or on GCP. It dynamically adjusts its prompt instructions to account for the **5% GCP Platform Bonus** (ensuring correct leaderboard expectations).
* **Dockerized (Python 3.14 + Alpine)**: Fully containerized using a lightweight Alpine-based `Dockerfile` with the high-performance `uv` package manager.
* **Automated CI/CD Pipeline**: GitHub Action configured to build and push multi-architecture Docker images (`linux/amd64` and `linux/arm64`) to the GitHub Container Registry (GHCR) using Docker Buildx and QEMU emulation.

---

## 🛠️ Getting Started

### 1. Prerequisite Setup
Make sure you have [uv](https://github.com/astral-sh/uv) installed. If you are using VS Code, opening this workspace will prompt you to reopen it in a pre-configured Dev Container containing all dependencies.

### 2. Configure Environment Variables
Copy `.env.example` to `.env` in the root of the project:
```bash
cp .env.example .env
```
Fill in the configuration details. You must provide `GAME_API_KEY` (get it from the game website) and a `GOOGLE_API_KEY` for the Gemini backend:
```env
GAME_API_KEY=your_game_api_key_here
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_gemini_api_key_here
```
*(For detailed Gemini or GCP Vertex AI configuration, check out [gemini.md](file:///workspaces/GardenOfTheForgottenPrompt/gemini.md))*

---

## 🎮 How to Run

### Interactive CLI Chat
Play or debug the agent in the terminal:
```bash
uv run adk run src/text_adventure_bot
```

### Visual Debugger Web UI
Inspect agent runs, trace tool calls, and test workflows interactively:
```bash
uv run adk web src
```
Open your browser at `http://localhost:8000` to access the web debugger.

### Running with Docker
Build and run the containerized agent:
```bash
# Build the image
docker build -t text-adventure-bot .

# Run the interactive agent CLI
docker run -it --env-file .env text-adventure-bot
```

---

## 🏆 Leaderboard Strategy

A high-ranking run requires optimizing four distinct scoring mechanisms:

1. **Base Completion Score**: Earned for finishing the level.
2. **Time Bonus (Action Efficiency)**: Awarded for solving puzzles with the minimum number of actions. The bot utilizes local cache tracking (like the `inventory` state) to avoid calling remote APIs unnecessarily.
3. **Treasure Hunter Bonus**: Awarded for finding and carrying rare items (e.g. keys, rubber ducks, coins) upon finishing the level. The bot explores all rooms to collect treasures before taking the completion item.
4. **ADK Operator Bonus**: A special 5% multiplier awarded on GCP. Set `ON_GCP=true` to enable this context flag.
5. **Micro-Awards (Mandatory Action Diversity)**: Earned by performing all 5 fundamental actions (`look`, `move`, `take`, `use`, `examine`) at least once. The bot is instructed to find natural, safe opportunities to fulfill all five actions early in the game.
