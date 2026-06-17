# Gemma 4 World Cup Analyst Demo

This project provides a live, interactive, dual-mode demo of Gemma 4's Thinking Mode and Structured Output. It features a World Cup Penalty Shootout analysis tool that can automatically fall back to a local Ollama model if the Google AI Studio API is unavailable or rate-limited.

## Features

*   **Interactive CLI:** Choose between predefined high-stakes scenarios or type your own based on live audience suggestions.
*   **Dual-Mode Execution:** Uses the Gemini API for cloud execution, falling back seamlessly to local `gemma4:12b` via Ollama.
*   **Structured Output:** Generates a consistent JSON schema including a commentator script, tactical breakdown, and an excitement index.
*   **Streaming Support:** Production FastAPI implementation streams reasoning thoughts to the client in real-time.

## Prerequisites

1.  Python 3.11+
2.  **(Optional)** [Ollama](https://ollama.com/) installed with the `gemma4:12b` model pulled locally (`ollama run gemma4:12b`) for offline fallback.
3.  **(Optional)** Google Gemini API Key for cloud mode. Set as an environment variable: `export GEMINI_API_KEY="your_api_key"`
4.  **(Optional)** Docker & Docker Compose for containerized deployment.

## Installation

Install the required Python dependencies for the FastAPI server:

```bash
pip3 install -r requirements.txt
```

---

## Demo Options

### Option 1: Interactive CLI Demo (Python Script)

This is a standalone Python script perfect for live terminal presentations. It interacts with the audience and streams thought processes directly to standard output.

```bash
python3 world_cup_analyst.py
```

*   **Tip:** You can force local mode and bypass the API check by using the `--local` flag:
    ```bash
    python3 world_cup_analyst.py --local
    ```

### Option 2: Production FastAPI Microservice (Native)

Run the full web API natively on your machine to demonstrate production readiness, standard HTTP routing, and SSE (Server-Sent Events) streaming endpoints.

1.  Start the FastAPI server using Uvicorn:
    ```bash
    uvicorn app:app --reload --port 8080
    ```
2.  Send a POST request in another terminal to test the standard JSON endpoint:
    ```bash
    curl -X POST http://localhost:8080/analyze \
      -H "Content-Type: application/json" \
      -d '{"scenario": "90th min penalty shootout, USA vs Canada, Pulisic vs Crepeau", "local": true}'
    ```

### Option 3: Docker Compose (Local Testing)

Orchestrate the FastAPI service and link it to your host's Ollama instance. This demonstrates container networking with a local AI model.

1.  Start the Docker Compose stack:
    ```bash
    docker-compose up --build
    ```
    *(This exposes port `8080` and connects the container to `http://host.docker.internal:11434`)*
2.  Test the API from another terminal as shown in Option 2.

### Option 4: Deploy to Google Cloud Run (Serverless)

Build and deploy the application to Google Cloud Run using the provided `Dockerfile`.

1.  Build the Docker container locally:
    ```bash
    docker build -t gemma4-worldcup-api .
    ```
2.  Test the container locally before deployment:
    ```bash
    docker run -p 8080:8080 -e GEMINI_API_KEY="your-api-key" gemma4-worldcup-api
    ```
3.  Deploy to Google Cloud Run:
    ```bash
    gcloud run deploy gemma4-worldcup-api \
      --source . \
      --port 8080 \
      --allow-unauthenticated
    ```

---

*See [world_cup_demo.md](world_cup_demo.md) for more architectural details and setup concepts.*
