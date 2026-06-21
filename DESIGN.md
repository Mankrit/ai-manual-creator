# Design Document: AI Modular Manual Creator

This document outlines the expectations, architecture, tech stack, and milestones for the **AI Modular Manual Creator**. This system will help users create manuals, documentation, and tutorials for web applications by analyzing both their source code and their running user interface (UI), focusing on one controllable module/feature at a time.

---

## Step 1: Project Expectations & Goals

### Core Problem
Generating documentation for an entire application in one run is slow, hard to control, prone to context-window limitations, and difficult to verify.

### Our Solution
A **modular, code-aware, and UI-interactive documentation system**. It targets specific "features" or "modules" rather than the whole app. It analyzes the frontend/backend code first to understand *how* the feature is built (e.g., input fields, endpoints, validation rules), then uses that knowledge to navigate the UI, take screenshots, and write accurate step-by-step guides.

### Key Goals
1. **Codebase Understanding**: Read and analyze target application code (e.g., React components, routes, database schemas, controller files) to identify how a feature works.
2. **Dynamic UI Interaction**: Log in and browse the running web application, focusing specifically on the target module to capture step-by-step screenshots of user flows.
3. **Modular Generation**: Write documentation for individual features/modules separately (e.g., `login.md`, `checkout.md`) rather than all at once.
4. **Master Compilation & Stunning Presentation**: Compile individual modular guides into a unified, highly aesthetic web portal or document page (e.g., modern dark mode, glassmorphism, responsive navigation).
5. **Developer & User Dual Guides**: Able to generate both **user-facing guides** (how to use the feature) and **developer-facing guides** (how the code works under the hood).
6. **Interactive Tutorials (Future Scope)**: Output structured JSON step-by-step tours that can be used to run interactive guides directly inside the browser.

---

## Technical Solutions to Core Challenges

### 1. Code Module Differentiation (Solving Code Tangling)
Since codebase features are often interconnected (shared routes, common utilities, shared state), we will isolate modules using a three-tier strategy:
* **Entry Point Discovery (Semantic Search)**: The system searches the codebase for keywords related to the module (e.g., "login", "auth") and compiles a list of candidate files.
* **LLM Route & Import Tracing**: The agent begins at main entry points (like `App.js` or server route index) and traces imports/routes related to the target feature, ignoring general-purpose utilities (like formatting helpers) unless crucial.
* **User Hints (Scope Control)**: When running a module, the user can optionally pass hints (e.g., `"Focus on: client/src/components/Login.js and server/routes/auth.js"`). This drastically narrows down the search space and keeps the documentation accurate.

### 2. Browser Automation Tooling (Why Playwright?)
* **The Reference Project**: Used a tool called `agent-browser` (a custom model-agent tool built on top of Puppeteer or Playwright) that runs a browser instance, feeds screenshots/HTML to the LLM, and accepts mouse click/type commands.
* **Why Playwright Python is Superior for Us**:
  1. **Direct API**: Playwright provides modern, asynchronous python hooks that work seamlessly with Python `asyncio`.
  2. **Browser Recording**: Playwright has built-in video-recording and trace-viewing options, which we can use to export actual user walkthroughs as animations or video files.
  3. **Visual Testing**: It is built for visual regression, meaning it easily takes full-page, element-specific, or cropped screenshots.

### 3. Making the Results Look Premium & Stunning
We want to move beyond plain black-and-white markdown tables. Our compiler will output a **Modern Documentation Web Portal**:
* **Theme**: Modern dark mode with dark HSL tailwind/CSS palettes, glassmorphism headers, sidebar navigation, and clean Google Fonts (e.g., Outfit or Inter).
* **Media Enhancements**:
  * **Annotated Screenshots**: During browser exploration, the AI can note the bounding boxes of elements it clicks and draw overlay indicators (like red circles or number steps) on the screenshots before saving them.
  * **Flowcharts**: Embedded Mermaid diagrams showing both user interactions (UI) and API data flow (code).
* **Interactive Tutorials Playback**: An interactive player that lets the user click "Play Walkthrough" to see the step-by-step video recording of the browser agent executing the task.

---

## Step 2: Tech Stack & Architecture

We want a stack that is modern, clean, easy to learn, and highly flexible.

### 1. Programming Language & Environment
* **Language**: Python 3.12+ (standard for AI/LLM development).
* **Package Manager**: `uv` (fast, reliable, native virtual environments).

### 2. LLM Integration (The Agent Loop)
* **Custom Agent Loop (Recommended)**: We will write a lightweight custom agent loop using the standard Google Gemini or Anthropic API client. Doing this from scratch helps us learn the exact mechanics of tool-calling, status management, and prompt construction.

### 3. UI Interaction & Automation
* **Playwright (Python)**: For browser automation, interactions, and screenshots.

### 4. Interactive Portal (The Presentation Layer)
* **Vite + React / Static HTML with Premium CSS**: A lightweight portal to render the generated Markdown files as a beautiful, interactive web guide.

---

## Step 3: Project Structure & Milestones

### Proposed Project Directory
```text
AI-Manual-Creator/
├── core/
│   ├── agent.py          # Custom agent loop and tool executor
│   ├── tools/
│   │   ├── code_tools.py # Tools to search and read code files
│   │   ├── web_tools.py  # Playwright browser tools (navigate, screenshot, click, fill)
│   │   └── file_tools.py # Tools to write and update markdown files
│   └── prompts.py        # System instructions and prompt templates
├── portal/               # Stunning documentation web portal code (frontend)
├── output/               # Where modular docs and media are written
├── config.json           # Config file pointing to target codebase, target URL, credentials
├── main.py               # Entrypoint script to run the documentation flow for a module
└── compile.py            # Utility script to compile modules into the portal
```

### Proposed Milestones

* **Milestone 1: Environment Setup & Agent Core**
  * Initialize the virtual environment using `uv`.
  * Write the custom agent loop in Python that connects to the LLM (using Gemini/Claude) and handles simple tools (reading codebase).
* **Milestone 2: Playwright Integration & Browser Agent**
  * Integrate Playwright.
  * Define browser tools (navigate, fill form, click, capture screenshot).
  * Build a tool to highlight elements (e.g. draw numbers/borders on screenshots).
* **Milestone 3: Modular Documentation Generator**
  * Write the prompting structure that combines code discovery and UI exploration.
  * Document a target module, saving markdown and annotated images.
* **Milestone 4: Premium Web Portal & Interactive Tours**
  * Build the frontend presentation portal using beautiful CSS/React.
  * Compile the markdown pages into the portal, showcasing visual steps, flowcharts, and interactive screenshots.

