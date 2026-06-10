# Python ADK Agent Project

This is a clean project environment pre-configured with a VS Code Development Container (Dev Container) and the Google Agent Development Kit (ADK) framework for building, debugging, and testing AI agents.

## Getting Started

### 1. Open in Dev Container
When you open this directory in Visual Studio Code, you will see a prompt to **Reopen in Container** (if you have the "Dev Containers" extension and Docker installed). Doing so will build the container environment which automatically includes:
- **Python 3.11**
- **Google Cloud SDK (`gcloud`)**
- Useful VS Code Extensions: Python, Pylance, Ruff (linter/formatter), and Google Cloud Code.
- Automated installation of all dependencies from `pyproject.toml` using `uv`.

### 2. Configure Environment Variables
Copy `.env.example` to `.env` at the root of the project:
```bash
cp .env.example .env
```
Fill in the configuration details. If you are using the Gemini Developer API (Google AI Studio), configure your `GOOGLE_API_KEY`:
```text
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_actual_api_key
```

### 3. Authentication (GCP/Vertex AI only)
If you decide to use Google Cloud Vertex AI instead, set `GOOGLE_GENAI_USE_VERTEXAI=TRUE` in your `.env` and run the following command in the container terminal to authenticate your session:
```bash
gcloud auth application-default login
```

---

## Running and Debugging your Agent

### Interactive CLI Chat
You can chat with your agent interactively in the terminal by running:
```bash
uv run adk run src/my_agent
```
*(Alternatively, activate the virtual environment with `source .venv/bin/activate` and run `adk run src/my_agent`)*

### Visual Debugger Web UI
ADK comes with a built-in visual web debugger. To launch it, run:
```bash
uv run adk web
```
VS Code will automatically forward port `8000` and prompt you to open the browser at `http://localhost:8000`. You can inspect agent runs, trace tool calls, and test workflows interactively.

---

## Project Structure
- `.devcontainer/`: Container build configuration and VS Code setup.
- `src/my_agent/`: Your agent package code.
  - `agent.py`: Agent definition, instructions, and tools.
  - `__init__.py`: Package initialization.
- `pyproject.toml`: Python package metadata and dependencies configuration.
- `uv.lock`: Lockfile containing exact resolved dependency versions.
- `.env.example`: Configuration variables blueprint.
