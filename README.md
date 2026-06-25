# AI Modular Manual Creator

An AI-powered, model-agnostic technical writer agent that documents web applications module-by-module. It analyzes source code to understand inputs and endpoints, launches a browser via Playwright to walk through forms, captures glowing annotated screenshots of interactions, and generates comprehensive user-facing and developer-facing Markdown manuals.

---

## Prerequisites

* **Python 3.12+**
* **[uv](https://docs.astral.sh/uv/)** — Extremely fast Python package manager and virtual environment runner.
* **Node.js 18+** — Required for running the React Documentation Portal.

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
Open `config.json` and customize the paths, models, and metadata layers for your local setup.

#### Configuration Keys:
* **`target_codebase_path`**: Absolute path to your target application code.
* **`target_app_url`**: Entry URL of the web application.
* **`models`**: LLM configurations for the agents.
* **`project_metadata_path`** (Optional): Path to a JSON metadata catalog mapping modules to their specific code files and descriptions to reduce exploration overhead.
* **`login_flow`** (Optional): A list of browser automation actions (`navigate`, `fill`, `click`, `wait_for`) executed automatically to authenticate the browser session before starting the documentation agent. If you are documenting the login process itself, the system automatically skips this flow.

Example `config.json`:
```json
{
  "target_codebase_path": "c:/Users/QP-202349/Desktop/AI project & learning/documentation project/AI Manual Creator/mock_app",
  "target_app_url": "http://localhost:3001/login.html",
  "credentials": {
    "username": "admin@example.com",
    "password": "password123"
  },
  "models": {
    "routing": "openai/MiniMax-M3",
    "writer": "openai/MiniMax-M3",
    "verifier": "openai/MiniMax-M3"
  },
  "project_metadata_path": "project_metadata.json",
  "login_flow": null
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
From the project root, trigger the orchestrator CLI for the `"User Settings"` module of the mock application by passing its configuration profile:
```bash
uv run python main.py --config config.mock.json --module "User Settings"
```
*(By default, if `--config` is omitted, the script automatically falls back to `config.json`).*

### 3. View the Results
Once completed:
* The generated Markdown file will be saved under **`output/user_login/user_login.md`**.
* The captured screenshots with visual glowing highlights will be saved under the **`output/user_login/`** directory.

---

## Frontend / UI

### Step 1: Compile the Documentation
Assemble all documentation modules and visual assets into the portal public directory:
```bash
python compile.py
```
*(This script scans the `output/` directory, extracts titles, lists screenshots, creates `catalog.json`, and copies files).*

### Step 2: Start the Portal
Run the Vite development server to view the portal:
```bash
# Navigate to portal directory
cd portal

# Run local development server
npm run dev
```

*Note:* If you run into command parsing errors on Windows due to special characters (like `&` or spaces) in your folder paths, run Vite directly using Node:
```bash
node node_modules/vite/bin/vite.js
```

Open your browser and navigate to:
**`http://localhost:5173/`**
