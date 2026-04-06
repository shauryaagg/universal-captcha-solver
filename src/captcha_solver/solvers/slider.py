"""Slider captcha solver using edge detection."""
from __future__ import annotations

import time

import numpy as np

from captcha_solver.core.result import CaptchaResult
from captcha_solver.preprocessing.image import load_image
from captcha_solver.solvers.base import BaseSolver, CaptchaType, SolverInput


class SliderSolver(BaseSolver):
    @property
    def captcha_type(self) -> CaptchaType:
        return CaptchaType.SLIDER

    @property
    def name(self) -> str:
        return "SliderSolver"

    def can_solve(self, solver_input: SolverInput) -> bool:
        return solver_input.image is not None

    def solve(self, solver_input: SolverInput) -> CaptchaResult:
        if solver_input.image is None:
            raise ValueError("SliderSolver requires an image input")

        start = time.perf_counter()
        offset = self._find_gap_offset(solver_input.image)
        elapsed = (time.perf_counter() - start) * 1000

        return CaptchaResult(
            solution=str(offset),
            captcha_type=CaptchaType.SLIDER.value,
            confidence=0.80,
            solver_name=self.name,
            elapsed_ms=elapsed,
        )

    def _find_gap_offset(self, image_bytes: bytes) -> int:
        """Find the horizontal offset of the gap in a slider captcha using edge detection."""
        img = load_image(image_bytes).convert("L")
        arr = np.array(img, dtype=np.float32)

        # Simple edge detection: horizontal gradient (Sobel-like)
        # Compute difference between adjacent columns
        if arr.shape[1] < 2:
            return 0

        gradient = np.abs(np.diff(arr, axis=1))

        # Sum gradient vertically for each column to find columns with strong edges
        col_energy = np.sum(gradient, axis=0)

        # Normalize
        if col_energy.max() == 0:
            return 0
        col_energy = col_energy / col_energy.max()

        # Find the region with highest edge concentration
        # Use a sliding window to find the gap area (typically ~50px wide)
        width = img.size[0]
        window_size = max(width // 10, 20)  # ~10% of image width

        best_offset = 0
        best_energy = 0.0

        # Skip the leftmost 10% (usually the slider piece starting position)
        start_col = max(width // 10, 10)

        for i in range(start_col, len(col_energy) - window_size):
            window_energy = float(np.sum(col_energy[i : i + window_size]))
            if window_energy > best_energy:
                best_energy = window_energy
                best_offset = i + window_size // 2  # Center of the gap

        return best_offset
