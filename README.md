# Universal Captcha Solver

Solve any captcha with one line of Python.

## Features

- **Auto-detection** -- automatically identifies captcha type from image characteristics
- **Multiple solver types** -- text/image OCR, math expression, slider puzzle, and more
- **CLI tool** -- solve captchas directly from the command line
- **REST API** -- FastAPI server with file upload and base64 endpoints
- **Cloud backends** -- optional GPT-4V / Claude Vision support (coming soon)
- **Browser integration** -- Selenium and Playwright helpers (coming soon)
- **GPU acceleration** -- optional ONNX Runtime GPU support for faster inference
- **Extensible** -- plugin-based solver registry with priority ordering

## Quickstart

### Install

```bash
pip install universal-captcha-solver
```

With optional extras:

```bash
# CLI support
pip install universal-captcha-solver[cli]

# REST API server
pip install universal-captcha-solver[server]

# Everything
pip install universal-captcha-solver[all]
```

### Python

```python
from captcha_solver import solve

result = solve("captcha.png")
print(result.solution)      # "abc123"
print(result.confidence)    # 0.85
print(result.captcha_type)  # "text"
```

With explicit type:

```python
result = solve("math_captcha.png", captcha_type="math")
```

Detection only:

```python
from captcha_solver import detect

captcha_type, confidence = detect("captcha.png")
print(f"{captcha_type.value}: {confidence:.0%}")
```

### CLI

```bash
# Solve a captcha
captcha-solver solve captcha.png

# With JSON output
captcha-solver solve captcha.png --output json

# Detect type only
captcha-solver detect captcha.png

# List available models
captcha-solver models list

# Start REST API server
captcha-solver serve --host 0.0.0.0 --port 8000
```

### REST API

Start the server:

```bash
captcha-solver serve
```

Solve via file upload:

```bash
curl -X POST http://localhost:8000/solve \
  -F "image=@captcha.png"
```

Detect captcha type:

```bash
curl -X POST http://localhost:8000/detect \
  -F "image=@captcha.png"
```

Health check:

```bash
curl http://localhost:8000/health
```

## Supported Captcha Types

| Type | Status | Approach |
|------|--------|----------|
| Text/Image | Supported | ONNX OCR model |
| Math | Supported | OCR + safe expression evaluation |
| Slider | Supported | Edge detection for gap offset |
| reCAPTCHA v2 | Planned | Image classification grid |
| reCAPTCHA v3 | Planned | Score-based behavioral |
| hCaptcha | Planned | Image classification |
| Cloudflare Turnstile | Planned | Browser automation |
| Audio | Planned | Speech-to-text |
| GeeTest | Planned | Slide + icon click |

## Configuration

Configuration is managed via environment variables or the `Settings` class:

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `CAPTCHA_SOLVER_MODEL_BACKEND` | `local` | `local` (ONNX) or `cloud` |
| `CAPTCHA_SOLVER_MODEL_DIR` | `~/.cache/captcha-solver/models` | Local model storage path |
| `CAPTCHA_SOLVER_GPU_ENABLED` | `false` | Enable GPU acceleration |
| `CAPTCHA_SOLVER_MIN_CONFIDENCE` | `0.7` | Minimum confidence threshold |
| `CAPTCHA_SOLVER_MAX_RETRIES` | `2` | Number of retry attempts |
| `CAPTCHA_SOLVER_TIMEOUT_SECONDS` | `30.0` | Solver timeout |
| `CAPTCHA_SOLVER_OPENAI_API_KEY` | | OpenAI API key for cloud backend |
| `CAPTCHA_SOLVER_ANTHROPIC_API_KEY` | | Anthropic API key for cloud backend |
| `CAPTCHA_SOLVER_CLOUD_PROVIDER` | `openai` | Cloud provider (`openai` or `anthropic`) |
| `CAPTCHA_SOLVER_SERVER_HOST` | `127.0.0.1` | REST API server host |
| `CAPTCHA_SOLVER_SERVER_PORT` | `8000` | REST API server port |
| `CAPTCHA_SOLVER_LOG_LEVEL` | `INFO` | Logging level |

Or configure programmatically:

```python
from captcha_solver.config import Settings
from captcha_solver.core.pipeline import SolverPipeline

settings = Settings(gpu_enabled=True, min_confidence=0.9)
pipeline = SolverPipeline(settings=settings)
result = pipeline.solve("captcha.png")
```

## Development

### Setup

```bash
git clone https://github.com/yourusername/universal-captcha-solver.git
cd universal-captcha-solver
pip install -e ".[dev,cli,server]"
```

### Run Tests

```bash
pytest -v
```

With coverage:

```bash
pytest --cov=captcha_solver --cov-report=term-missing
```

### Integration Tests

Integration tests run against live 2captcha.com demo pages using Playwright and the cloud vision backend. They require:

- An API key: `export ANTHROPIC_API_KEY=your-key` or `export OPENAI_API_KEY=your-key`
- Playwright: `pip install playwright && playwright install chromium`

Run integration tests:

```bash
pytest tests/integration/ -v -s
```

Skip integration tests when running the full suite:

```bash
pytest -m "not integration"
```

### Linting

```bash
ruff check src/ tests/
ruff format src/ tests/
```

### Type Checking

```bash
mypy src/captcha_solver
```

## License

MIT
