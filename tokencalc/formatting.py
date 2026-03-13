"""terminal formatting helpers."""

import os
import sys

# disable colors when piping or when NO_COLOR is set
_supports_color = hasattr(sys.stdout, "isatty") and sys.stdout.isatty() and "NO_COLOR" not in os.environ

BOLD = "\033[1m" if _supports_color else ""
DIM = "\033[2m" if _supports_color else ""
GREEN = "\033[32m" if _supports_color else ""
YELLOW = "\033[33m" if _supports_color else ""
CYAN = "\033[36m" if _supports_color else ""
RED = "\033[31m" if _supports_color else ""
MAGENTA = "\033[35m" if _supports_color else ""
RESET = "\033[0m" if _supports_color else ""


def fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def fmt_cost(c: float) -> str:
    if c < 0.01:
        return f"${c:.6f}"
    if c < 1.00:
        return f"${c:.4f}"
    return f"${c:.2f}"


def parse_token_str(s: str) -> int:
    """parse a token count string like '1000', '1k', '1.5M', '10,000'."""
    s = s.strip().replace(",", "")
    lower = s.lower()
    if lower.endswith("m"):
        return int(float(lower[:-1]) * 1_000_000)
    if lower.endswith("k"):
        return int(float(lower[:-1]) * 1_000)
    return int(s)
