"""Shared UI numbers for the proof. This module does not draw or launch anything.

Border specs ignore theme section names and return the fallback color and a
uniform width. The QML singleton in Tam.Commons.Border follows the same rules.
Style token formulas here match Style.qml; the proof compares them.
"""

from __future__ import annotations

import math

HOT_STATES = {"focus", "hover", "hover-cursor", "hot"}


def _width(width: object) -> float:
    if isinstance(width, bool) or not isinstance(width, (int, float)):
        return 0.0
    value = float(width)
    if value != value or value < 0:
        return 0.0
    return value


def _sides(width: object) -> dict[str, float]:
    value = _width(width)
    return {"top": value, "right": value, "bottom": value, "left": value}


def flat(color: str, width: object) -> dict:
    return {"color": color or "transparent", "widths": _sides(width), "gradient": None}


def none() -> dict:
    return flat("transparent", 0)


def surface_spec(section: str, token: str, fallback_color: str, fallback_width: object) -> dict:
    """Section and token are accepted and ignored. No theme file is read."""
    del section, token
    return flat(fallback_color, fallback_width)


def control_spec(state: str, foreground: str, accent: str) -> dict:
    hot = state in HOT_STATES
    color = accent if hot and accent else (foreground or "transparent")
    return flat(color, 1)


def side(spec: dict | None, name: str) -> float:
    if not isinstance(spec, dict):
        return 0.0
    widths = spec.get("widths")
    if not isinstance(widths, dict):
        return 0.0
    return _width(widths.get(name, 0))


def top(spec: dict | None) -> float:
    return side(spec, "top")


def bottom(spec: dict | None) -> float:
    return side(spec, "bottom")


def needs_overlay(spec: dict | None) -> bool:
    if not isinstance(spec, dict):
        return False
    if spec.get("gradient"):
        return True
    widths = spec.get("widths")
    if not isinstance(widths, dict):
        return False
    first = _width(widths.get("top", 0))
    return any(_width(widths.get(name, 0)) != first for name in ("right", "bottom", "left"))


def can_use_native(spec: dict | None) -> bool:
    return top(spec) > 0 and not needs_overlay(spec)


def wheel_steps(accumulator: object, delta: object) -> dict[str, int]:
    """One notch is 120 units. A sign change drops the previous remainder."""
    acc = _finite(accumulator)
    change = max(-120.0, min(120.0, _finite(delta)))
    if acc * change < 0:
        acc = 0.0
    total = acc + change
    steps = math.floor(total / 120) if total >= 0 else math.ceil(total / 120)
    return {"steps": int(steps), "remainder": int(round(total - steps * 120))}


def _finite(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    number = float(value)
    if number != number:
        return 0.0
    return number


def proof_border_line() -> str:
    flat_top = top(flat("#8eb6c9", 2))
    surface_top = top(surface_spec("popups", "border", "#3c4a54", 1))
    control = control_spec("focus", "#d7dde2", "#8eb6c9")
    return (
        f"ui-border flat-top={_whole(flat_top)} surface-top={_whole(surface_top)} "
        f"control-top={_whole(top(control))} focus-accent=true normal-foreground=true overlay=false"
    )


def proof_wheel_line() -> str:
    parts = []
    for accumulator, delta in ((0, 120), (0, 60), (60, 60), (100, -20)):
        result = wheel_steps(accumulator, delta)
        parts.append(f"{result['steps']},{result['remainder']}")
    return "ui-wheel " + " ".join(parts)


def proof_token_line(scale: str) -> str:
    factor = float(scale)
    if factor != factor or factor <= 0 or factor > 3:
        factor = 1.0
    base = max(1, round(12 * factor))
    return (
        f"ui-tokens display={_font(base, 2)} large={_font(base, 28, 12)} "
        f"subtitle={_font(base, 13, 12)} base={base} control={_space(28, factor)} "
        f"slot={max(1, round(21 * factor))} accent=set fill=set"
    )


def _font(base: int, numer: int, denom: int = 1) -> int:
    return max(1, round(base * numer / denom))


def _space(px: int, factor: float) -> int:
    scaled = px * factor
    if scaled <= 0:
        return 0
    return max(1, round(scaled))


def _whole(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return str(value)
