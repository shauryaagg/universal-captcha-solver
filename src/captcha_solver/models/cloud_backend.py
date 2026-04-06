"""Cloud vision backend using LLM APIs (Anthropic Claude, OpenAI GPT-4V)."""
from __future__ import annotations

import base64
import io
import json
from captcha_solver.models.backend import BoundingBox, ModelBackend


class CloudBackend(ModelBackend):
    """Cloud-based model backend using vision LLMs."""

    def __init__(
        self,
        provider: str = "anthropic",
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.provider = provider
        self.api_key = api_key
        self.model = model or self._default_model()

    def _default_model(self) -> str:
        if self.provider == "anthropic":
            return "claude-sonnet-4-20250514"
        elif self.provider == "openai":
            return "gpt-4o"
        return "claude-sonnet-4-20250514"

    def _encode_image(self, image: bytes) -> str:
        return base64.b64encode(image).decode("utf-8")

    def _detect_media_type(self, image: bytes) -> str:
        if image[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        if image[:2] == b"\xff\xd8":
            return "image/jpeg"
        if image[:4] == b"GIF8":
            return "image/gif"
        if image[:4] == b"RIFF":
            return "image/webp"
        return "image/png"

    # --- Anthropic Implementation ---
    def _call_anthropic(self, image: bytes, prompt: str) -> str:
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package required. Install: pip install universal-captcha-solver[cloud]"
            )

        client = anthropic.Anthropic(api_key=self.api_key)
        b64 = self._encode_image(image)
        media_type = self._detect_media_type(image)

        message = client.messages.create(
            model=self.model,
            max_tokens=256,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        return message.content[0].text.strip()

    # --- OpenAI Implementation ---
    def _call_openai(self, image: bytes, prompt: str) -> str:
        try:
            import openai
        except ImportError:
            raise ImportError(
                "openai package required. Install: pip install universal-captcha-solver[cloud]"
            )

        client = openai.OpenAI(api_key=self.api_key)
        b64 = self._encode_image(image)
        media_type = self._detect_media_type(image)

        response = client.chat.completions.create(
            model=self.model,
            max_tokens=256,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{media_type};base64,{b64}"},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        return response.choices[0].message.content.strip()

    def _call_vision(self, image: bytes, prompt: str) -> str:
        """Route to the configured provider."""
        if self.provider == "anthropic":
            return self._call_anthropic(image, prompt)
        elif self.provider == "openai":
            return self._call_openai(image, prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    # --- ModelBackend interface ---
    def ocr(self, image: bytes) -> str:
        prompt = (
            "Read the text in this captcha image. Return ONLY the exact text/characters shown, "
            "nothing else. No explanation, no quotes, no punctuation unless it's part of the "
            "captcha. If it contains numbers and letters, return them exactly as shown."
        )
        return self._call_vision(image, prompt)

    def classify_image(self, image: bytes, labels: list[str] | None = None) -> str:
        if labels:
            labels_str = ", ".join(labels)
            prompt = (
                f"Look at this image and classify it. Choose exactly one label "
                f"from: [{labels_str}]. Return ONLY the label, nothing else."
            )
        else:
            prompt = (
                "What does this image show? Describe it in 2-3 words. "
                "Return ONLY the description, nothing else."
            )
        return self._call_vision(image, prompt)

    def detect_objects(self, image: bytes) -> list[BoundingBox]:
        prompt = (
            "Identify all distinct objects in this image. For each object, provide its position "
            "as a JSON array of objects with keys: x, y, width, height, label. "
            "Coordinates should be approximate pixel values. Return ONLY the JSON array."
        )
        response = self._call_vision(image, prompt)
        try:
            # Try to parse JSON from response
            # Handle cases where response has extra text around JSON
            start = response.find("[")
            end = response.rfind("]") + 1
            if start >= 0 and end > start:
                data = json.loads(response[start:end])
                return [
                    BoundingBox(
                        x=float(obj.get("x", 0)),
                        y=float(obj.get("y", 0)),
                        width=float(obj.get("width", 0)),
                        height=float(obj.get("height", 0)),
                        label=str(obj.get("label", "")),
                        confidence=0.85,
                    )
                    for obj in data
                ]
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        return []

    def transcribe_audio(self, audio: bytes) -> str:
        if self.provider == "openai":
            try:
                import openai
            except ImportError:
                raise ImportError("openai package required for audio transcription.")
            client = openai.OpenAI(api_key=self.api_key)
            audio_file = io.BytesIO(audio)
            audio_file.name = "captcha.mp3"
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )
            return transcript.text.strip()
        raise NotImplementedError(
            f"Audio transcription not supported for provider: {self.provider}"
        )

    # --- Captcha-specific methods ---
    def solve_grid_captcha(
        self,
        image: bytes,
        prompt_text: str,
        grid_size: tuple[int, int] = (3, 3),
    ) -> list[int]:
        """Solve a grid-based captcha (reCAPTCHA v2 style).

        Returns list of 1-indexed grid positions that match the prompt.
        """
        rows, cols = grid_size
        total = rows * cols
        prompt = (
            f"This is a {rows}x{cols} grid captcha image. {prompt_text} "
            f"Return ONLY the grid positions (1-{total}, numbered left-to-right, "
            f"top-to-bottom) as comma-separated numbers. Example: 1,4,7"
        )
        response = self._call_vision(image, prompt)
        # Parse comma-separated numbers
        positions: list[int] = []
        for part in response.replace(" ", "").split(","):
            try:
                num = int(part)
                if 1 <= num <= total:
                    positions.append(num)
            except ValueError:
                continue
        return positions

    def answer_text_challenge(self, question: str) -> str:
        """Answer a text-based captcha question (no image)."""
        content = (
            f"Answer this captcha question with ONLY the answer, nothing else. "
            f"Be concise - one word or short phrase only.\n\nQuestion: {question}"
        )
        if self.provider == "anthropic":
            try:
                import anthropic
            except ImportError:
                raise ImportError("anthropic package required.")
            client = anthropic.Anthropic(api_key=self.api_key)
            message = client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[{"role": "user", "content": content}],
            )
            return message.content[0].text.strip()
        elif self.provider == "openai":
            try:
                import openai
            except ImportError:
                raise ImportError("openai package required.")
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                max_tokens=100,
                messages=[{"role": "user", "content": content}],
            )
            return response.choices[0].message.content.strip()
        raise ValueError(f"Unknown provider: {self.provider}")
