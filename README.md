# AI Modular Manual Creator

An AI-powered, model-agnostic technical writer agent that documents web applications module-by-module. It analyzes source code to understand inputs and endpoints, launches a browser via Playwright to walk through forms, captures glowing annotated screenshots of interactions, and generates comprehensive user-facing and developer-facing Markdown manuals.

---

## Prerequisites

* **Python 3.12+**
* **[uv](https://docs.astral.sh/uv/)** — Extremely fast Python package manager and virtual environment runner.

---

## Quick Start Setup (For Cloned Repositories)

If you have cloned this repository, follow these steps to set up your environment:

### Step 1: Install Dependencies
Run the following command in the project root. `uv` will automatically read `.python-version` and `pyproject.toml`, set up a virtual environment (`.venv`), and install all dependencies:
```bash
uv sync
```

### Step 2: Install Playwright Browsers
Download the required Chromium browser binary:
```bash
uv run playwright install chromium
```

### Step 3: Configure Environment Variables
Copy the template `.env.example` file to create a local `.env` file:
```bash
copy .env.example .env
```
Open `.env` and fill in your API key and base URL (e.g. for TokenRouter, OpenRouter, or other LLM providers):
```env
OPENAI_API_BASE="https://api.tokenrouter.com/v1"
OPENAI_API_KEY="tr_your_api_key_here"
```

### Step 4: Configure Local Project Settings
Copy the template configuration file to create `config.json`:
```bash
copy config.example.json config.json
```
Open `config.json` and customize the paths and model choices for your local setup:
```json
{
  "target_codebase_path": "c:/Users/QP-202349/Desktop/AI project & learning/documentation project/AI Manual Creator/mock_app",
  "target_app_url": "http://localhost:3001/login.html",
  "credentials": {
    "username": "test@example.com",
    "password": "password123"
  },
  "models": {
    "routing": "openai/MiniMax-M3",
    "writer": "openai/MiniMax-M3",
    "verifier": "openai/MiniMax-M3"
  }
}
```

---

## Running the Application (Mock Application Walkthrough)

To verify the installation, you can run the pipeline against the self-contained mock application included in this repository.

### 1. Start the Mock Server
Start Python's built-in HTTP server in a separate terminal to host the mock app:
```bash
# Set your terminal working directory to mock_app/
python -m http.server 3001
```
*(Verify it's running by visiting `http://localhost:3001/login.html` in your browser).*

### 2. Run the Documentation Agent Pipeline
From the project root, trigger the orchestrator CLI for the `"User Login"` module:
```bash
uv run python main.py --module "User Login" --hints "login.html and dashboard.html"
```

### 3. View the Results
Once completed:
* The generated Markdown file will be saved under **`output/user_login.md`**.
* The captured screenshots with visual glowing highlights will be saved under the **`output/`** directory.
