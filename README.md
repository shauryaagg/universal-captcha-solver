<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/logo-dark.svg">
    <img alt="captcha-solver" src="assets/logo.svg" width="560">
  </picture>
</p>

<p align="center">
  <strong>One line to solve any captcha. Built for AI agents.</strong>
</p>

<p align="center">
  <a href="https://github.com/shauryaagg/universal-captcha-solver/actions"><img src="https://img.shields.io/badge/tests-288%20passed-brightgreen?style=flat-square" alt="Tests"></a>
  <a href="https://github.com/shauryaagg/universal-captcha-solver/actions"><img src="https://img.shields.io/badge/coverage-78%25-yellow?style=flat-square" alt="Coverage"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License: MIT"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/code%20style-ruff-000000?style=flat-square" alt="Ruff"></a>
  <a href="https://mypy-lang.org/"><img src="https://img.shields.io/badge/type%20checked-mypy-blue?style=flat-square" alt="mypy"></a>
</p>

<p align="center">
  <a href="#quickstart">Quickstart</a> &middot;
  <a href="#supported-captcha-types">Captcha Types</a> &middot;
  <a href="#browser-automation">Browser Automation</a> &middot;
  <a href="#rest-api">REST API</a> &middot;
  <a href="#configuration">Configuration</a>
</p>

---

## Why captcha-solver?

Every existing solution is either expensive, unreliable, or only handles one captcha type. **captcha-solver** auto-detects the captcha type and solves it through one unified API -- locally or via cloud vision models.

- **One-liner API** -- `solve("captcha.png")` and you're done
- **9 captcha types** -- text, math, slider, reCAPTCHA v2/v3, hCaptcha, Turnstile, audio, GeeTest
- **Browser native** -- drop-in Selenium and Playwright support with `solve_captcha(driver)`
- **Dual backend** -- local ONNX models (free, fast) or cloud vision APIs (GPT-4o, Claude)
- **Self-hostable** -- REST API server, CLI tool, or import as a library
- **Plugin system** -- add custom solvers via Python entry points
- **GPU accelerated** -- optional CUDA support via ONNX Runtime

## Quickstart

### Install

```bash
pip install universal-captcha-solver
```

```bash
# With all optional dependencies
pip install universal-captcha-solver[all]

# Or pick what you need
pip install universal-captcha-solver[cli]          # CLI tool
pip install universal-captcha-solver[server]       # REST API server
pip install universal-captcha-solver[cloud]        # OpenAI + Anthropic vision
pip install universal-captcha-solver[selenium]     # Selenium integration
pip install universal-captcha-solver[playwright]   # Playwright integration
pip install universal-captcha-solver[gpu]          # CUDA acceleration
```

### Solve in one line

```python
from captcha_solver import solve

result = solve("captcha.png")
print(result.solution)      # "xK7mN"
print(result.confidence)    # 0.95
print(result.captcha_type)  # "text"
print(result.elapsed_ms)    # 142.5
```

### With cloud vision (GPT-4o / Claude)

```python
import os
os.environ["CAPTCHA_SOLVER_MODEL_BACKEND"] = "cloud"
os.environ["CAPTCHA_SOLVER_CLOUD_PROVIDER"] = "openai"     # or "anthropic"
os.environ["OPENAI_API_KEY"] = "sk-..."                     # or ANTHROPIC_API_KEY

from captcha_solver import solve
result = solve("hard_captcha.png")
```

### Auto-detect captcha type

```python
from captcha_solver import detect

captcha_type, confidence = detect("unknown_captcha.png")
# CaptchaType.SLIDER, 0.90
```

## Supported Captcha Types

| Type | Approach | Backend | Status |
|:-----|:---------|:--------|:------:|
| **Text / Image** | OCR via ONNX or cloud vision | Local / Cloud | :white_check_mark: |
| **Math** | OCR + safe expression evaluation | Local / Cloud | :white_check_mark: |
| **Slider** | Edge detection for gap offset | Local | :white_check_mark: |
| **reCAPTCHA v2** | Grid image classification | Cloud | :white_check_mark: |
| **reCAPTCHA v3** | Browser behavior simulation | Browser | :white_check_mark: |
| **hCaptcha** | Image classification | Cloud | :white_check_mark: |
| **Cloudflare Turnstile** | Stealth browser automation | Browser | :white_check_mark: |
| **Audio** | Speech-to-text (Whisper / cloud STT) | Local / Cloud | :white_check_mark: |
| **GeeTest** | Slide + click + icon matching | Local / Cloud | :white_check_mark: |

## Browser Automation

Drop into any existing Selenium or Playwright workflow. One function handles detection, screenshotting, solving, and submission.

### Selenium

```python
from selenium import webdriver
from captcha_solver.browser import solve_captcha

driver = webdriver.Chrome()
driver.get("https://example.com/login")

result = solve_captcha(driver)
print(result.solution)
```

### Playwright

```python
from playwright.sync_api import sync_playwright
from captcha_solver.browser import solve_captcha

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://example.com/login")

    result = solve_captcha(page)
    print(result.solution)
```

### Async Playwright

```python
from captcha_solver.browser import asolve_captcha

result = await asolve_captcha(page)
```

The `solve_captcha()` function auto-detects whether you pass a Selenium WebDriver or Playwright Page -- no adapter code needed.

## CLI

```bash
# Solve a captcha image
captcha-solver solve captcha.png
# Solution: xK7mN  (type: text, confidence: 0.95, 142ms)

# JSON output for scripting
captcha-solver solve captcha.png --output json

# Detect captcha type
captcha-solver detect captcha.png

# Start the REST API server
captcha-solver serve --host 0.0.0.0 --port 8000

# Manage models
captcha-solver models list
captcha-solver models download text-ocr-v1
```

## REST API

Start the server:

```bash
captcha-solver serve
# or: uvicorn captcha_solver.server.app:app
```

### Endpoints

```bash
# Solve via file upload
curl -X POST http://localhost:8000/solve \
  -F "image=@captcha.png"

# Solve with explicit type
curl -X POST http://localhost:8000/solve \
  -F "image=@captcha.png" \
  -F "captcha_type=text"

# Detect captcha type
curl -X POST http://localhost:8000/detect \
  -F "image=@captcha.png"

# Health check
curl http://localhost:8000/health

# List registered solvers
curl http://localhost:8000/solvers
```

### Response format

```json
{
  "solution": "xK7mN",
  "captcha_type": "text",
  "confidence": 0.95,
  "elapsed_ms": 142.5,
  "solver_name": "TextSolver"
}
```

Interactive API docs are available at `/docs` when the server is running.

## Configuration

All settings can be configured via environment variables (prefixed `CAPTCHA_SOLVER_`), a `.env` file, or programmatically.

| Variable | Default | Description |
|:---------|:--------|:------------|
| `CAPTCHA_SOLVER_MODEL_BACKEND` | `local` | `local` (ONNX) or `cloud` (vision APIs) |
| `CAPTCHA_SOLVER_CLOUD_PROVIDER` | `anthropic` | `openai` or `anthropic` |
| `CAPTCHA_SOLVER_GPU_ENABLED` | `false` | Enable CUDA GPU acceleration |
| `CAPTCHA_SOLVER_MIN_CONFIDENCE` | `0.7` | Minimum confidence threshold |
| `CAPTCHA_SOLVER_MAX_RETRIES` | `2` | Retry attempts per solver |
| `CAPTCHA_SOLVER_FALLBACK_TO_CLOUD` | `true` | Auto-fallback to cloud if local fails |
| `OPENAI_API_KEY` | | OpenAI API key |
| `ANTHROPIC_API_KEY` | | Anthropic API key |

<details>
<summary><strong>All configuration options</strong></summary>

| Variable | Default | Description |
|:---------|:--------|:------------|
| `CAPTCHA_SOLVER_MODEL_DIR` | `~/.cache/captcha-solver/models` | Local model storage |
| `CAPTCHA_SOLVER_TIMEOUT_SECONDS` | `30.0` | Solver timeout |
| `CAPTCHA_SOLVER_SERVER_HOST` | `127.0.0.1` | REST API host |
| `CAPTCHA_SOLVER_SERVER_PORT` | `8000` | REST API port |
| `CAPTCHA_SOLVER_LOG_LEVEL` | `INFO` | Logging level |
| `CAPTCHA_SOLVER_OPENAI_MODEL` | `gpt-4o` | OpenAI model |
| `CAPTCHA_SOLVER_ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | Anthropic model |

</details>

### Programmatic configuration

```python
from captcha_solver.config import Settings
from captcha_solver.core.pipeline import SolverPipeline

settings = Settings(
    model_backend="cloud",
    cloud_provider="openai",
    gpu_enabled=True,
    min_confidence=0.9,
)

pipeline = SolverPipeline(settings=settings)
result = pipeline.solve("captcha.png")
```

## Extending with plugins

Create custom solvers and register them via Python entry points.

```python
# my_solver.py
from captcha_solver.solvers.base import BaseSolver, CaptchaType, SolverInput
from captcha_solver.core.result import CaptchaResult

class MySolver(BaseSolver):
    @property
    def captcha_type(self) -> CaptchaType:
        return CaptchaType.TEXT

    @property
    def name(self) -> str:
        return "MySolver"

    def can_solve(self, solver_input: SolverInput) -> bool:
        return solver_input.image is not None

    def solve(self, solver_input: SolverInput) -> CaptchaResult:
        # Your solving logic here
        ...
```

Register in your `pyproject.toml`:

```toml
[project.entry-points."captcha_solver.solvers"]
my_solver = "my_package:MySolver"
```

Plugins are auto-discovered at runtime.

## Architecture

```
Image/URL/Browser
       │
       ▼
  ┌──────────┐     ┌────────────┐     ┌───────────┐
  │  Detect  │────▶│ Preprocess │────▶│   Solve   │
  │   Type   │     │   Image    │     │  (retry)  │
  └──────────┘     └────────────┘     └───────────┘
       │                                     │
       │           ┌────────────┐            │
       └──────────▶│  Registry  │◀───────────┘
                   │ (plugins)  │
                   └────────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         ┌────────┐ ┌────────┐ ┌────────┐
         │  ONNX  │ │ Cloud  │ │Browser │
         │ Local  │ │ Vision │ │Automate│
         └────────┘ └────────┘ └────────┘
```

## Development

```bash
git clone https://github.com/shauryaagg/universal-captcha-solver.git
cd universal-captcha-solver
pip install -e ".[dev,cli,server]"
```

### Tests

```bash
# Unit tests (278 tests)
pytest

# With coverage
pytest --cov=captcha_solver

# Integration tests (requires API key + Playwright)
export OPENAI_API_KEY="sk-..."   # or ANTHROPIC_API_KEY
pytest tests/integration/ -v -s

# Lint
ruff check src/ tests/
```

### Project structure

```
src/captcha_solver/
├── __init__.py          # Public API: solve(), detect()
├── config.py            # Settings (pydantic-settings)
├── core/                # Pipeline, registry, detector
├── solvers/             # All solver implementations
├── models/              # ONNX + cloud backends
├── browser/             # Selenium/Playwright adapters
├── server/              # FastAPI REST API
├── cli/                 # Typer CLI
└── preprocessing/       # Image & audio utilities
```

## License

[MIT](LICENSE)
