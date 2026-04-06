"""Integration test: Text captcha on 2captcha.com/demo/text."""
from __future__ import annotations

import re

import pytest

from tests.integration.conftest import requires_api_key, requires_playwright


@requires_api_key
@requires_playwright
class TestTextCaptcha:
    """Test solving text-based captcha questions."""

    def test_solve_text_question(self, page, cloud_provider, api_key):
        """Solve a text question captcha using cloud LLM."""
        from captcha_solver.models.cloud_backend import CloudBackend

        page.goto("https://2captcha.com/demo/text", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Extract the question text from the page
        question_el = page.query_selector(".captcha-question") or page.query_selector("p.question")

        if not question_el:
            # Try to find any text that looks like a question
            all_text = page.inner_text("main") or page.inner_text("body")
            questions = re.findall(r"(?:If|What|How|When|Where|Which|Who).*?\?", all_text)
            question = questions[0] if questions else ""
        else:
            question = question_el.inner_text()

        print(f"Text captcha question: '{question}'")

        if not question:
            pytest.skip("Could not find question on page")

        backend = CloudBackend(provider=cloud_provider, api_key=api_key)
        answer = backend.answer_text_challenge(question)

        print(f"Answer: '{answer}'")
        assert answer, "Expected non-empty answer"
