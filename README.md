# Code-Generator

An AI-powered code generation and auto-execution agent built with FastAPI and a locally hosted LLM (Llama 3.2 3B via Ollama). Given a natural language description, the system generates a runnable Python script, saves it to disk, and automatically executes it — returning both the code and any output or plots produced.

---

## Purpose

Writing boilerplate code for data analysis, visualization, and scripting tasks is repetitive. This project explores whether a small, locally hosted LLM can reliably generate syntactically correct, runnable Python from plain English descriptions — and then execute that code without human intervention. The auto-run feature closes the loop between code generation and validation, making it possible to verify model output immediately.

---

## Technologies Used

| Technology | Role |
|---|---|
| Python | Core language |
| FastAPI | REST API framework |
| Ollama | Local LLM inference engine |
| Llama 3.2 3B | Language model for code generation |
| Uvicorn | ASGI server |
| Matplotlib | Visualization (for generated plot scripts) |
| Requests | HTTP client for model communication |

---

## Setup & Installation

### Prerequisites
- Python 3.9+
- [Ollama](https://ollama.com) installed on your machine

### Steps

**1. Install Ollama**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**2. Pull the Llama 3.2 3B model**
```bash
ollama pull llama3.2:3b
```

**3. Clone the repository**
```bash
git clone https://github.com/yomi-adamo/Code-Generator.git
cd Code-Generator
```

**4. Create and activate a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

**5. Install dependencies**
```bash
pip install fastapi uvicorn requests matplotlib
```

**6. Run the server**
```bash
uvicorn main:app --reload
```

---

## Usage

Send a POST request to the `/generate-code` endpoint with a natural language description and an `auto_run` flag:

```bash
curl -X POST http://localhost:8000/generate-code \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a Python script that generates a sine wave and plots it using matplotlib.",
    "auto_run": true
  }'
```

When `auto_run` is set to `true`, the API saves the generated script and executes it automatically, returning any console output or confirming plot generation.

---

## Key Features

- **Natural language to code** — Describe what you want in plain English; the LLM generates a complete Python script.
- **Auto-execution** — With `auto_run: true`, generated code is saved and run immediately without manual intervention.
- **Local inference** — Runs entirely on-device via Ollama; no external API calls or usage costs.
- **FastAPI interface** — Clean REST API with interactive Swagger docs at `/docs`.
- **Matplotlib support** — Tested with visualization tasks including waveform and signal plots.

---

## My Contribution

This was a solo personal project. I built the entire system independently: the FastAPI application structure, the Ollama prompt pipeline for code generation, the file-save and subprocess-based auto-execution logic, and all documentation. I also debugged a key issue where matplotlib's `show()` function caused the subprocess to hang in non-interactive environments, and resolved it by configuring a non-interactive backend.

---

## Reflection

This project pushed me to think carefully about the boundary between AI-generated output and executable code — a non-trivial problem when the model occasionally produces incomplete or syntactically invalid scripts. Handling execution failures gracefully and sanitizing model output before running it were the most technically interesting challenges. It also deepened my understanding of subprocess management and local LLM prompt engineering, both of which are directly relevant to my interest in edge-deployed AI systems.
