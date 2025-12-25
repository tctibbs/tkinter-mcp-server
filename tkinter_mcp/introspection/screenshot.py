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


def get_dpi_scale_factor() -> float:
    """Get the DPI scaling factor for the current display.

    Returns:
        Scale factor (1.0 = no scaling, 2.0 = Retina/HiDPI)
    """
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
                return 2.0
        except Exception:
            pass
        return 1.0

    elif system == "Windows":
        try:
            import ctypes

            ctypes.windll.user32.SetProcessDPIAware()
            hdc = ctypes.windll.user32.GetDC(0)
            dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
            ctypes.windll.user32.ReleaseDC(0, hdc)
            return dpi / 96.0
        except Exception:
            pass

    return 1.0


def capture_window_screenshot(root: tk.Tk) -> bytes:
    """Capture a screenshot of the Tkinter window.

    Args:
        root: The Tkinter root window

    Returns:
        PNG image data as base64-encoded bytes

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

        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        png_bytes = buffer.getvalue()

        return base64.b64encode(png_bytes)

    except Exception as e:
        raise RuntimeError(f"Failed to capture screenshot: {e}") from e


def screenshot_to_base64_string(png_bytes: bytes) -> str:
    """Convert PNG bytes to base64 string.

    Args:
        png_bytes: Base64-encoded PNG image bytes

    Returns:
        Base64 encoded string (decoded from bytes)
    """
    if isinstance(png_bytes, bytes):
        return png_bytes.decode("utf-8")
    return str(png_bytes)
