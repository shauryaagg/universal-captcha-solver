"""Tests for captcha_solver.browser.behavior module."""

from unittest.mock import MagicMock

from captcha_solver.browser.behavior import (
    bezier_curve,
    simulate_human_delay,
    simulate_mouse_movement,
    simulate_reading,
    simulate_scroll,
    simulate_typing,
)


class TestBezierCurve:
    def test_returns_correct_number_of_points(self):
        points = bezier_curve((0, 0), (100, 100), num_points=20)
        assert len(points) == 21  # num_points + 1

    def test_returns_correct_number_of_points_custom(self):
        points = bezier_curve((0, 0), (500, 500), num_points=10)
        assert len(points) == 11

    def test_first_point_near_start(self):
        points = bezier_curve((50, 50), (300, 300), num_points=20)
        x, y = points[0]
        assert x == 50
        assert y == 50

    def test_last_point_near_end(self):
        points = bezier_curve((0, 0), (200, 200), num_points=20)
        x, y = points[-1]
        assert abs(x - 200) <= 1
        assert abs(y - 200) <= 1

    def test_points_are_int_tuples(self):
        points = bezier_curve((10, 20), (300, 400), num_points=5)
        for x, y in points:
            assert isinstance(x, int)
            assert isinstance(y, int)


class TestSimulateMouseMovement:
    def test_calls_execute_js(self):
        adapter = MagicMock()
        simulate_mouse_movement(adapter, (0, 0), (100, 100))
        assert adapter.execute_js.call_count > 0


class TestSimulateScroll:
    def test_calls_execute_js(self):
        adapter = MagicMock()
        simulate_scroll(adapter, amount=100)
        assert adapter.execute_js.call_count > 0


class TestSimulateHumanDelay:
    def test_does_not_crash(self):
        # Just verify it completes without error
        simulate_human_delay(1, 5)


class TestSimulateReading:
    def test_calls_execute_js(self):
        adapter = MagicMock()
        simulate_reading(adapter, duration=0.1)
        assert adapter.execute_js.call_count > 0


class TestSimulateTyping:
    def test_calls_type_text_for_each_char(self):
        adapter = MagicMock()
        element = MagicMock()
        simulate_typing(adapter, element, "abc")
        assert adapter.type_text.call_count == 3
        adapter.type_text.assert_any_call(element, "a")
        adapter.type_text.assert_any_call(element, "b")
        adapter.type_text.assert_any_call(element, "c")
