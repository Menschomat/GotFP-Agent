# Google Gemini Integration & Configuration

This guide details how to configure the Google Gemini API (via Google AI Studio or GCP Vertex AI) and explains how **Context Caching** is leveraged to optimize performance and reduce token costs.

---

## 1. Choosing a Gemini Model

By default, the bot utilizes the highly capable **Gemini 2.5 Flash** (`gemini-2.5-flash`) model, which provides a great balance of speed, reasoning power, and low latency for text adventure parsing. 

If you want to use other models (such as Gemini 2.5 Pro or a custom model), you can configure them via the `LITELLM_MODEL` environment variable.

---

## 2. API Credentials Configuration

Configure your credentials by adding the appropriate keys to the `.env` file at the root of the project.

### Option A: Google AI Studio (Gemini Developer API)
*Recommended for local development and rapid prototyping. It is free/pay-as-you-go and easy to set up.*

1. Set the following environment variables:
   ```env
   GOOGLE_GENAI_USE_VERTEXAI=FALSE
   GOOGLE_API_KEY=your_actual_api_key_here
   ```
2. Get an API key from [Google AI Studio](https://aistudio.google.com/).

### Option B: Google Cloud Platform (Vertex AI)
*Recommended for enterprise deployments, scalability, and when running in GCP production environments.*

1. Set the following environment variables:
   ```env
   GOOGLE_GENAI_USE_VERTEXAI=TRUE
   VERTEX_PROJECT_ID=your-gcp-project-id
   VERTEX_LOCATION=us-central1
   ```
2. Authenticate your terminal session using the Google Cloud SDK:
   ```bash
   gcloud auth application-default login
   ```

---

## 3. Natively Managed Context Caching

Multi-turn agents (such as text-adventure bots playing 20+ turns per level) can consume significant input tokens on every turn due to sending the system prompt, registered tool schemas, and full conversation history repeatedly.

To mitigate this, the bot leverages Google Gemini's **Context Caching** capability natively supported by the Google Agent Development Kit (ADK) framework.

### How it is Implemented:
Inside the [agent.py](file:///workspaces/GardenOfTheForgottenPrompt/src/text_adventure_bot/agent.py) orchestrator, we define a `ContextCacheConfig` object:

```python
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.apps.app import App

cache_config = ContextCacheConfig(
    cache_intervals=10,  # Reuse the cache for up to 10 consecutive turns
    ttl_seconds=1800,    # Cache remains active for 30 minutes
    min_tokens=0,        # Cache all turns to maximize savings
)

app = App(
    name="text_adventure_bot",
    root_agent=root_agent,
    context_cache_config=cache_config,
)
```

### Benefits:
* **Latency Reduction**: Drastically cuts down time-to-first-token on later turns since the model does not need to re-evaluate the system prompt and history.
* **Cost Efficiency**: Reduces input token costs on Gemini 2.0+ models by utilizing cached states.
* **Automatic Lifecycle**: The ADK framework handles the creation, TTL management, and deletion of context caches automatically under the hood.

---

## 4. GCP 5% Platform Bonus

If you deploy the agent to a Google Cloud Platform (GCP) environment, you will receive an automatic **5% score multiplier** (the *ADK Operator Bonus*) on the game's leaderboard.

To inform the agent of its current deployment status so it can evaluate its performance accurately:
* **Local Run**: Leave `ON_GCP` set to `False` (default). The agent will be given a system prompt note warning it that local scores are 5% lower than GCP.
* **GCP Run**: Set `ON_GCP=TRUE` in your environment. The agent will know it is running at full scoring capacity.
