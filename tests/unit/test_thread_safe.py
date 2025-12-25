"""Unit tests for thread-safe utilities."""

import threading

from tkinter_mcp.bridge.thread_safe import ThreadSafeResult, is_main_thread


class TestThreadSafeResult:
    """Tests for ThreadSafeResult dataclass."""

    def test_success_result(self) -> None:
        result = ThreadSafeResult(success=True, value=42)

        assert result.success is True
        assert result.value == 42
        assert result.error is None

    def test_error_result(self) -> None:
        error = ValueError("test error")
        result = ThreadSafeResult(success=False, error=error)

        assert result.success is False
        assert result.error is error
        assert result.value is None

    def test_success_with_none_value(self) -> None:
        result = ThreadSafeResult(success=True, value=None)

        assert result.success is True
        assert result.value is None

    def test_success_with_complex_value(self) -> None:
        complex_value = {"key": [1, 2, 3], "nested": {"a": "b"}}
        result = ThreadSafeResult(success=True, value=complex_value)

        assert result.success is True
        assert result.value == complex_value


class TestIsMainThread:
    """Tests for is_main_thread function."""

    def test_returns_true_on_main_thread(self) -> None:
        assert is_main_thread() is True

    def test_returns_false_on_background_thread(self) -> None:
        results: list[bool] = []

        def check_thread() -> None:
            results.append(is_main_thread())

        thread = threading.Thread(target=check_thread)
        thread.start()
        thread.join()

        assert len(results) == 1
        assert results[0] is False

    def test_multiple_background_threads(self) -> None:
        results: list[bool] = []
        lock = threading.Lock()

        def check_thread() -> None:
            with lock:
                results.append(is_main_thread())

        threads = [threading.Thread(target=check_thread) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 5
        assert all(r is False for r in results)
