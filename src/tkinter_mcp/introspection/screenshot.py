"""Screenshot capture for Tkinter windows."""

from __future__ import annotations

import base64
import io
import platform
from typing import TYPE_CHECKING

import pyautogui
from PIL import Image

if TYPE_CHECKING:
    import tkinter as tk

# Cache DPI scale factor to avoid repeated subprocess calls
_dpi_scale_cache: float | None = None


def get_dpi_scale_factor() -> float:
    """Get the DPI scaling factor for the current display.

    Returns:
        Scale factor (1.0 = no scaling, 2.0 = Retina/HiDPI)
    """
    global _dpi_scale_cache

    if _dpi_scale_cache is not None:
        return _dpi_scale_cache

    system = platform.system()

    if system == "Darwin":
        try:
            import subprocess

            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True,
                text=True,
                check=False,
            )
            if "Retina" in result.stdout:
                _dpi_scale_cache = 2.0
                return _dpi_scale_cache
        except Exception:
            pass
        _dpi_scale_cache = 1.0

    elif system == "Windows":
        try:
            import ctypes

            ctypes.windll.user32.SetProcessDPIAware()
            hdc = ctypes.windll.user32.GetDC(0)
            dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
            ctypes.windll.user32.ReleaseDC(0, hdc)
            _dpi_scale_cache = dpi / 96.0
        except Exception:
            _dpi_scale_cache = 1.0

    else:
        _dpi_scale_cache = 1.0

    return _dpi_scale_cache


def capture_window_screenshot(
    root: tk.Tk,
    max_dimension: int = 800,
    jpeg_quality: int = 70,
) -> bytes:
    """Capture a screenshot of the Tkinter window.

    Args:
        root: The Tkinter root window
        max_dimension: Maximum width or height in pixels (default 800)
        jpeg_quality: JPEG compression quality 1-100 (default 70)

    Returns:
        JPEG image data as base64-encoded bytes

    Raises:
        RuntimeError: If screenshot capture fails
    """
    root.update_idletasks()

    x = root.winfo_rootx()
    y = root.winfo_rooty()
    width = root.winfo_width()
    height = root.winfo_height()

    scale = get_dpi_scale_factor()
    if scale != 1.0:
        x = int(x * scale)
        y = int(y * scale)
        width = int(width * scale)
        height = int(height * scale)

    try:
        screenshot: Image.Image = pyautogui.screenshot(region=(x, y, width, height))

        # Resize if larger than max_dimension
        if max(screenshot.width, screenshot.height) > max_dimension:
            screenshot.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

        # Convert to RGB (JPEG doesn't support alpha)
        if screenshot.mode in ("RGBA", "P"):
            screenshot = screenshot.convert("RGB")

        # Save as JPEG with compression
        buffer = io.BytesIO()
        screenshot.save(buffer, format="JPEG", quality=jpeg_quality)

        return base64.b64encode(buffer.getvalue())

    except Exception as e:
        raise RuntimeError(f"Failed to capture screenshot: {e}") from e


def screenshot_to_base64_string(image_bytes: bytes) -> str:
    """Convert image bytes to base64 string.

    Args:
        image_bytes: Base64-encoded image bytes

    Returns:
        Base64 encoded string (decoded from bytes)
    """
    if isinstance(image_bytes, bytes):
        return image_bytes.decode("utf-8")
    return str(image_bytes)
