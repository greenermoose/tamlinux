#!/usr/bin/env python3
"""Wayland virtual keyboard and pointer synthesis for Tamlinux desktop tests.

Connects directly to the active Wayland compositor via libwayland-client.so.0
and binds:
  - zwp_virtual_keyboard_manager_v1 (uploading the real active XKB keymap compiled
    via libxkbcommon.so.0 so evdev keycodes, code:N binds, keypad binds, and
    modifier chords match physical hardware input)
  - zwlr_virtual_pointer_manager_v1 (emitting motion_absolute, relative motion,
    button, axis/scroll, and frame events)

Includes dual emergency-stop protection:
  1. Reserved keybinding (Meta + Shift + Escape -> `tam-desktop-test --stop`),
     which signals the active test process and writes the stop sentinel file.
  2. Physical mouse grab detection: if the compositor cursor position diverges
     from the last synthesized virtual pointer target by more than the grab
     threshold (default 25 px), the controller raises EmergencyStopError and
     immediately releases all held keys, modifiers, and mouse buttons.
"""

from __future__ import annotations

import ctypes
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time
from typing import Callable, Iterable, Sequence

# Wayland wire constants
WL_MARSHAL_FLAG_DESTROY = 1 << 0
WL_REGISTRY_BIND = 0
WL_DISPLAY_GET_REGISTRY = 1
WL_DISPLAY_SYNC = 0

WL_KEYBOARD_KEYMAP_FORMAT_XKB_V1 = 1
WL_KEYBOARD_KEY_STATE_RELEASED = 0
WL_KEYBOARD_KEY_STATE_PRESSED = 1

WL_POINTER_BUTTON_STATE_RELEASED = 0
WL_POINTER_BUTTON_STATE_PRESSED = 1
WL_POINTER_AXIS_VERTICAL_SCROLL = 0
WL_POINTER_AXIS_HORIZONTAL_SCROLL = 1
WL_POINTER_AXIS_SOURCE_WHEEL = 0

# Linux input-event-codes.h buttons
BTN_LEFT = 272
BTN_RIGHT = 273
BTN_MIDDLE = 274

BUTTON_CODES: dict[str, int] = {
    "left": BTN_LEFT,
    "lmb": BTN_LEFT,
    "mouse:272": BTN_LEFT,
    "right": BTN_RIGHT,
    "rmb": BTN_RIGHT,
    "mouse:273": BTN_RIGHT,
    "middle": BTN_MIDDLE,
    "mmb": BTN_MIDDLE,
    "mouse:274": BTN_MIDDLE,
}

# XKB modifier bitmasks
MOD_SHIFT = 1
MOD_CAPS = 2
MOD_CTRL = 4
MOD_ALT = 8
MOD_NUM = 16
MOD_META = 64

# Linux evdev keycodes (XKB keycode = evdev + 8)
EVDEV_KEYS: dict[str, int] = {
    "ESC": 1,
    "ESCAPE": 1,
    "1": 2,
    "2": 3,
    "3": 4,
    "4": 5,
    "5": 6,
    "6": 7,
    "7": 8,
    "8": 9,
    "9": 10,
    "0": 11,
    "MINUS": 12,
    "EQUAL": 13,
    "BACKSPACE": 14,
    "TAB": 15,
    "Q": 16,
    "W": 17,
    "E": 18,
    "R": 19,
    "T": 20,
    "Y": 21,
    "U": 22,
    "I": 23,
    "O": 24,
    "P": 25,
    "LEFTBRACE": 26,
    "BRACKETLEFT": 26,
    "RIGHTBRACE": 27,
    "BRACKETRIGHT": 27,
    "ENTER": 28,
    "RETURN": 28,
    "LEFTCTRL": 29,
    "CTRL": 29,
    "CONTROL": 29,
    "A": 30,
    "S": 31,
    "D": 32,
    "F": 33,
    "G": 34,
    "H": 35,
    "J": 36,
    "K": 37,
    "L": 38,
    "SEMICOLON": 39,
    "APOSTROPHE": 40,
    "GRAVE": 41,
    "LEFTSHIFT": 42,
    "SHIFT": 42,
    "BACKSLASH": 43,
    "Z": 44,
    "X": 45,
    "C": 46,
    "V": 47,
    "B": 48,
    "N": 49,
    "M": 50,
    "COMMA": 51,
    "PERIOD": 52,
    "DOT": 52,
    "SLASH": 53,
    "RIGHTSHIFT": 54,
    "KPASTERISK": 55,
    "LEFTALT": 56,
    "ALT": 56,
    "SPACE": 57,
    "CAPSLOCK": 58,
    "F1": 59,
    "F2": 60,
    "F3": 61,
    "F4": 62,
    "F5": 63,
    "F6": 64,
    "F7": 65,
    "F8": 66,
    "F9": 67,
    "F10": 68,
    "NUMLOCK": 69,
    "SCROLLLOCK": 70,
    "KP_7": 71,
    "KP7": 71,
    "KP_8": 72,
    "KP8": 72,
    "KP_9": 73,
    "KP9": 73,
    "KPMINUS": 74,
    "KP_4": 75,
    "KP4": 75,
    "KP_5": 76,
    "KP5": 76,
    "KP_6": 77,
    "KP6": 77,
    "KPPLUS": 78,
    "KP_1": 79,
    "KP1": 79,
    "KP_2": 80,
    "KP2": 80,
    "KP_3": 81,
    "KP3": 81,
    "KP_0": 82,
    "KP0": 82,
    "KPDOT": 83,
    "F11": 87,
    "F12": 88,
    "KPENTER": 96,
    "RIGHTCTRL": 97,
    "KPSLASH": 98,
    "SYSRQ": 99,
    "PRINT": 99,
    "RIGHTALT": 100,
    "HOME": 102,
    "UP": 103,
    "PAGEUP": 104,
    "PRIOR": 104,
    "LEFT": 105,
    "RIGHT": 106,
    "END": 107,
    "DOWN": 108,
    "PAGEDOWN": 109,
    "NEXT": 109,
    "INSERT": 110,
    "DELETE": 111,
    "MUTE": 113,
    "VOLUMEDOWN": 114,
    "VOLUMEUP": 115,
    "POWER": 116,
    "PAUSE": 119,
    "LEFTMETA": 125,
    "META": 125,
    "SUPER": 125,
    "WIN": 125,
    "RIGHTMETA": 126,
}

MODIFIER_SPECS: dict[str, tuple[int, int]] = {
    "SHIFT": (EVDEV_KEYS["LEFTSHIFT"], MOD_SHIFT),
    "LEFTSHIFT": (EVDEV_KEYS["LEFTSHIFT"], MOD_SHIFT),
    "RIGHTSHIFT": (EVDEV_KEYS["RIGHTSHIFT"], MOD_SHIFT),
    "CTRL": (EVDEV_KEYS["LEFTCTRL"], MOD_CTRL),
    "CONTROL": (EVDEV_KEYS["LEFTCTRL"], MOD_CTRL),
    "LEFTCTRL": (EVDEV_KEYS["LEFTCTRL"], MOD_CTRL),
    "RIGHTCTRL": (EVDEV_KEYS["RIGHTCTRL"], MOD_CTRL),
    "ALT": (EVDEV_KEYS["LEFTALT"], MOD_ALT),
    "LEFTALT": (EVDEV_KEYS["LEFTALT"], MOD_ALT),
    "RIGHTALT": (EVDEV_KEYS["RIGHTALT"], MOD_ALT),
    "META": (EVDEV_KEYS["LEFTMETA"], MOD_META),
    "SUPER": (EVDEV_KEYS["LEFTMETA"], MOD_META),
    "WIN": (EVDEV_KEYS["LEFTMETA"], MOD_META),
    "LOGO": (EVDEV_KEYS["LEFTMETA"], MOD_META),
    "MOD4": (EVDEV_KEYS["LEFTMETA"], MOD_META),
    "LEFTMETA": (EVDEV_KEYS["LEFTMETA"], MOD_META),
    "RIGHTMETA": (EVDEV_KEYS["RIGHTMETA"], MOD_META),
}

# US layout character to (key_name, needs_shift)
CHAR_TO_KEY: dict[str, tuple[str, bool]] = {
    " ": ("SPACE", False),
    "\n": ("RETURN", False),
    "\t": ("TAB", False),
    "-": ("MINUS", False),
    "_": ("MINUS", True),
    "=": ("EQUAL", False),
    "+": ("EQUAL", True),
    "[": ("LEFTBRACE", False),
    "{": ("LEFTBRACE", True),
    "]": ("RIGHTBRACE", False),
    "}": ("RIGHTBRACE", True),
    "\\": ("BACKSLASH", False),
    "|": ("BACKSLASH", True),
    ";": ("SEMICOLON", False),
    ":": ("SEMICOLON", True),
    "'": ("APOSTROPHE", False),
    '"': ("APOSTROPHE", True),
    "`": ("GRAVE", False),
    "~": ("GRAVE", True),
    ",": ("COMMA", False),
    "<": ("COMMA", True),
    ".": ("PERIOD", False),
    ">": ("PERIOD", True),
    "/": ("SLASH", False),
    "?": ("SLASH", True),
    "!": ("1", True),
    "@": ("2", True),
    "#": ("3", True),
    "$": ("4", True),
    "%": ("5", True),
    "^": ("6", True),
    "&": ("7", True),
    "*": ("8", True),
    "(": ("9", True),
    ")": ("0", True),
}
for _ch in "abcdefghijklmnopqrstuvwxyz":
    CHAR_TO_KEY[_ch] = (_ch.upper(), False)
    CHAR_TO_KEY[_ch.upper()] = (_ch.upper(), True)
for _d in "0123456789":
    CHAR_TO_KEY[_d] = (_d, False)


class EmergencyStopError(RuntimeError):
    """Raised when the user aborts the desktop test via keybinding or mouse grab."""


def runtime_state_paths() -> tuple[Path, Path]:
    """Return (pid_path, stop_sentinel_path) in XDG_RUNTIME_DIR or /tmp."""
    base = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/tmp/tamlinux-{os.getuid()}")
    base.mkdir(parents=True, exist_ok=True)
    return (
        base / "tamlinux-desktop-test.pid",
        base / "tamlinux-desktop-test.stop",
    )


def trigger_emergency_stop(reason: str = "Emergency stop keybinding pressed") -> bool:
    """Write the stop sentinel and signal any active test-battery process."""
    pid_path, stop_path = runtime_state_paths()
    stop_path.write_text(f"{reason}\n", encoding="utf-8")
    signaled = False
    if pid_path.exists():
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip())
            os.kill(pid, signal.SIGUSR1)
            signaled = True
        except (ValueError, ProcessLookupError, PermissionError):
            pass
    return signaled


def resolve_evdev_key(key: str | int) -> int:
    """Resolve a key name, XKB `code:N` token, or integer to a Linux evdev keycode."""
    if isinstance(key, int):
        if key <= 0:
            raise ValueError(f"invalid evdev keycode: {key}")
        return key
    token = str(key).strip()
    if not token:
        raise ValueError("empty key token")
    if token.lower().startswith("code:"):
        xkb_code = int(token.split(":", 1)[1])
        if xkb_code < 8:
            raise ValueError(f"XKB keycode must be >= 8: {token}")
        return xkb_code - 8
    upper = token.upper()
    if upper in EVDEV_KEYS:
        return EVDEV_KEYS[upper]
    if len(token) == 1 and token in CHAR_TO_KEY:
        key_name, _ = CHAR_TO_KEY[token]
        return EVDEV_KEYS[key_name]
    raise ValueError(f"unknown key token: {key!r}")


def resolve_modifiers(mods: Iterable[str]) -> tuple[list[int], int]:
    """Return (ordered unique evdev modifier keycodes, combined XKB modmask)."""
    keycodes: list[int] = []
    mask = 0
    for mod in mods:
        token = str(mod).strip().upper()
        if not token:
            continue
        if token not in MODIFIER_SPECS:
            raise ValueError(f"unknown modifier: {mod!r}")
        code, bit = MODIFIER_SPECS[token]
        if code not in keycodes:
            keycodes.append(code)
        mask |= bit
    return keycodes, mask


def parse_chord(chord: str) -> tuple[list[str], str]:
    """Split a chord string such as 'META + SHIFT + ESCAPE' into (mods, key)."""
    parts = [part.strip() for part in str(chord).split("+") if part.strip()]
    if not parts:
        raise ValueError("empty chord")
    mods: list[str] = []
    key = ""
    for idx, part in enumerate(parts):
        if part.upper() in MODIFIER_SPECS and idx < len(parts) - 1:
            mods.append(part.upper())
        else:
            key = part
    if not key:
        raise ValueError(f"chord has no primary key: {chord!r}")
    return mods, key


def interpolate_path(
    x1: int, y1: int, x2: int, y2: int, steps: int = 6
) -> list[tuple[int, int]]:
    """Generate smooth intermediate integer points from (x1, y1) to (x2, y2)."""
    steps = max(1, int(steps))
    points: list[tuple[int, int]] = []
    for i in range(1, steps + 1):
        t = i / steps
        # Smoothstep easing (3t^2 - 2t^3) for natural human-like eye tracking
        s = t * t * (3.0 - 2.0 * t)
        px = round(x1 + (x2 - x1) * s)
        py = round(y1 + (y2 - y1) * s)
        if not points or points[-1] != (px, py):
            points.append((px, py))
    if not points or points[-1] != (int(x2), int(y2)):
        points.append((int(x2), int(y2)))
    return points


def wl_fixed_from_double(value: float) -> int:
    """Convert float to Wayland 24.8 signed fixed-point int32."""
    return int(round(float(value) * 256.0))


# --- ctypes structures for libwayland-client and libxkbcommon ---


class _WlMessage(ctypes.Structure):
    pass


class _WlInterface(ctypes.Structure):
    pass


_WlMessage._fields_ = [
    ("name", ctypes.c_char_p),
    ("signature", ctypes.c_char_p),
    ("types", ctypes.POINTER(ctypes.POINTER(_WlInterface))),
]

_WlInterface._fields_ = [
    ("name", ctypes.c_char_p),
    ("version", ctypes.c_int),
    ("method_count", ctypes.c_int),
    ("methods", ctypes.POINTER(_WlMessage)),
    ("event_count", ctypes.c_int),
    ("events", ctypes.POINTER(_WlMessage)),
]


class _WlArgument(ctypes.Union):
    _fields_ = [
        ("i", ctypes.c_int32),
        ("u", ctypes.c_uint32),
        ("f", ctypes.c_int32),
        ("s", ctypes.c_char_p),
        ("o", ctypes.c_void_p),
        ("n", ctypes.c_uint32),
        ("a", ctypes.c_void_p),
        ("h", ctypes.c_int32),
    ]


class _XkbRuleNames(ctypes.Structure):
    _fields_ = [
        ("rules", ctypes.c_char_p),
        ("model", ctypes.c_char_p),
        ("layout", ctypes.c_char_p),
        ("variant", ctypes.c_char_p),
        ("options", ctypes.c_char_p),
    ]


def compile_xkb_keymap(
    rules: str = "evdev",
    model: str = "pc105",
    layout: str = "us",
    variant: str = "",
    options: str = "",
) -> bytes:
    """Compile an XKB keymap string (NUL-terminated) using libxkbcommon.so.0."""
    xkb_lib = os.environ.get("TAMLINUX_XKBCOMMON") or "libxkbcommon.so.0"
    xkb = ctypes.CDLL(xkb_lib)
    xkb.xkb_context_new.argtypes = [ctypes.c_int]
    xkb.xkb_context_new.restype = ctypes.c_void_p
    xkb.xkb_context_unref.argtypes = [ctypes.c_void_p]
    xkb.xkb_context_unref.restype = None

    xkb.xkb_keymap_new_from_names.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(_XkbRuleNames),
        ctypes.c_int,
    ]
    xkb.xkb_keymap_new_from_names.restype = ctypes.c_void_p
    xkb.xkb_keymap_get_as_string.argtypes = [ctypes.c_void_p, ctypes.c_int]
    xkb.xkb_keymap_get_as_string.restype = ctypes.c_void_p
    xkb.xkb_keymap_unref.argtypes = [ctypes.c_void_p]
    xkb.xkb_keymap_unref.restype = None

    libc = ctypes.CDLL("libc.so.6")
    libc.free.argtypes = [ctypes.c_void_p]
    libc.free.restype = None

    ctx = xkb.xkb_context_new(0)
    if not ctx:
        raise RuntimeError("xkb_context_new failed")
    try:
        names = _XkbRuleNames(
            rules=rules.encode("utf-8") if rules else None,
            model=model.encode("utf-8") if model else None,
            layout=layout.encode("utf-8") if layout else None,
            variant=variant.encode("utf-8") if variant else None,
            options=options.encode("utf-8") if options else None,
        )
        keymap = xkb.xkb_keymap_new_from_names(ctx, ctypes.byref(names), 0)
        if not keymap:
            raise RuntimeError(
                f"xkb_keymap_new_from_names failed for layout={layout!r} variant={variant!r}"
            )
        try:
            ptr = xkb.xkb_keymap_get_as_string(keymap, WL_KEYBOARD_KEYMAP_FORMAT_XKB_V1)
            if not ptr:
                raise RuntimeError("xkb_keymap_get_as_string returned NULL")
            try:
                raw = ctypes.string_at(ptr)
                return raw + b"\x00"
            finally:
                libc.free(ptr)
        finally:
            xkb.xkb_keymap_unref(keymap)
    finally:
        xkb.xkb_context_unref(ctx)


def detect_active_xkb_config() -> dict[str, str]:
    """Query `hyprctl devices -j` for the active keyboard RMLVO settings."""
    defaults = {
        "rules": "evdev",
        "model": "pc105",
        "layout": "us",
        "variant": "",
        "options": "",
    }
    try:
        out = subprocess.check_output(
            ["hyprctl", "devices", "-j"], text=True, timeout=3
        )
        data = json.loads(out)
        keyboards = data.get("keyboards") or []
        chosen = next((k for k in keyboards if k.get("main")), None) or (
            keyboards[0] if keyboards else None
        )
        if chosen:
            for field in ("rules", "model", "layout", "variant", "options"):
                val = chosen.get(field)
                if isinstance(val, str) and (val or field in ("variant", "options")):
                    defaults[field] = val
    except Exception:
        pass
    return defaults


class _WaylandProtocolDefinitions:
    """Builds and holds the static wl_interface tables for virtual input."""

    def __init__(self, wl: ctypes.CDLL) -> None:
        self.wl = wl
        self.wl_seat_interface = _WlInterface.in_dll(wl, "wl_seat_interface")
        self.wl_output_interface = _WlInterface.in_dll(wl, "wl_output_interface")
        self.wl_registry_interface = _WlInterface.in_dll(wl, "wl_registry_interface")
        self.wl_callback_interface = _WlInterface.in_dll(wl, "wl_callback_interface")

        null_ifaces = (ctypes.POINTER(_WlInterface) * 8)()
        self._keepalive: list[object] = [null_ifaces]

        # zwp_virtual_keyboard_v1
        vk_methods = (_WlMessage * 4)(
            _WlMessage(b"keymap", b"uhu", null_ifaces),
            _WlMessage(b"key", b"uuu", null_ifaces),
            _WlMessage(b"modifiers", b"uuuu", null_ifaces),
            _WlMessage(b"destroy", b"", null_ifaces),
        )
        self.zwp_virtual_keyboard_v1_interface = _WlInterface(
            name=b"zwp_virtual_keyboard_v1",
            version=1,
            method_count=4,
            methods=vk_methods,
            event_count=0,
            events=None,
        )

        # zwp_virtual_keyboard_manager_v1
        vkm_types = (ctypes.POINTER(_WlInterface) * 2)(
            ctypes.pointer(self.wl_seat_interface),
            ctypes.pointer(self.zwp_virtual_keyboard_v1_interface),
        )
        vkm_methods = (_WlMessage * 1)(
            _WlMessage(b"create_virtual_keyboard", b"on", vkm_types),
        )
        self.zwp_virtual_keyboard_manager_v1_interface = _WlInterface(
            name=b"zwp_virtual_keyboard_manager_v1",
            version=1,
            method_count=1,
            methods=vkm_methods,
            event_count=0,
            events=None,
        )

        # zwlr_virtual_pointer_v1
        vp_methods = (_WlMessage * 9)(
            _WlMessage(b"motion", b"uff", null_ifaces),
            _WlMessage(b"motion_absolute", b"uuuuu", null_ifaces),
            _WlMessage(b"button", b"uuu", null_ifaces),
            _WlMessage(b"axis", b"uuf", null_ifaces),
            _WlMessage(b"frame", b"", null_ifaces),
            _WlMessage(b"axis_source", b"u", null_ifaces),
            _WlMessage(b"axis_stop", b"uu", null_ifaces),
            _WlMessage(b"axis_discrete", b"uufi", null_ifaces),
            _WlMessage(b"destroy", b"1", null_ifaces),
        )
        self.zwlr_virtual_pointer_v1_interface = _WlInterface(
            name=b"zwlr_virtual_pointer_v1",
            version=2,
            method_count=9,
            methods=vp_methods,
            event_count=0,
            events=None,
        )

        # zwlr_virtual_pointer_manager_v1
        vpm_types_0 = (ctypes.POINTER(_WlInterface) * 2)(
            ctypes.pointer(self.wl_seat_interface),
            ctypes.pointer(self.zwlr_virtual_pointer_v1_interface),
        )
        vpm_types_2 = (ctypes.POINTER(_WlInterface) * 3)(
            ctypes.pointer(self.wl_seat_interface),
            ctypes.pointer(self.wl_output_interface),
            ctypes.pointer(self.zwlr_virtual_pointer_v1_interface),
        )
        vpm_methods = (_WlMessage * 3)(
            _WlMessage(b"create_virtual_pointer", b"?on", vpm_types_0),
            _WlMessage(b"destroy", b"1", null_ifaces),
            _WlMessage(b"create_virtual_pointer_with_output", b"2?o?on", vpm_types_2),
        )
        self.zwlr_virtual_pointer_manager_v1_interface = _WlInterface(
            name=b"zwlr_virtual_pointer_manager_v1",
            version=2,
            method_count=3,
            methods=vpm_methods,
            event_count=0,
            events=None,
        )

        self._keepalive.extend(
            [
                vk_methods,
                vkm_types,
                vkm_methods,
                vp_methods,
                vpm_types_0,
                vpm_types_2,
                vpm_methods,
            ]
        )


class WaylandVirtualInput:
    """High-level Wayland virtual keyboard and pointer controller."""

    def __init__(
        self,
        display_name: str | None = None,
        mouse_grab_threshold_px: float = 25.0,
        event_sink: Callable[[dict], None] | None = None,
    ) -> None:
        self.display_name = display_name
        self.mouse_grab_threshold_px = float(mouse_grab_threshold_px)
        self.event_sink = event_sink
        self._start_monotonic = time.monotonic()
        self._pressed_keys: set[int] = set()
        self._pressed_mods: int = 0
        self._pressed_buttons: set[int] = set()
        self.last_target_pos: tuple[int, int] | None = None
        self._aborted_reason: str | None = None

        wl_lib = os.environ.get("TAMLINUX_WAYLAND_CLIENT") or "libwayland-client.so.0"
        self.wl = ctypes.CDLL(wl_lib)
        self._setup_ctypes()
        self.proto = _WaylandProtocolDefinitions(self.wl)

        self.display: int | None = None
        self.registry: int | None = None
        self.seat: int | None = None
        self.vk_manager: int | None = None
        self.vp_manager: int | None = None
        self.vk: int | None = None
        self.vp: int | None = None
        self._keymap_fd: int | None = None
        self._globals: dict[str, tuple[int, int]] = {}
        self.xkb_config: dict[str, str] = {}

    def _setup_ctypes(self) -> None:
        self.wl.wl_display_connect.argtypes = [ctypes.c_char_p]
        self.wl.wl_display_connect.restype = ctypes.c_void_p
        self.wl.wl_display_disconnect.argtypes = [ctypes.c_void_p]
        self.wl.wl_display_disconnect.restype = None
        self.wl.wl_display_roundtrip.argtypes = [ctypes.c_void_p]
        self.wl.wl_display_roundtrip.restype = ctypes.c_int
        self.wl.wl_display_flush.argtypes = [ctypes.c_void_p]
        self.wl.wl_display_flush.restype = ctypes.c_int
        self.wl.wl_proxy_get_version.argtypes = [ctypes.c_void_p]
        self.wl.wl_proxy_get_version.restype = ctypes.c_uint32
        self.wl.wl_proxy_destroy.argtypes = [ctypes.c_void_p]
        self.wl.wl_proxy_destroy.restype = None
        self.wl.wl_proxy_add_listener.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]
        self.wl.wl_proxy_add_listener.restype = ctypes.c_int
        self.wl.wl_proxy_marshal_array_flags.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(_WlInterface),
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.POINTER(_WlArgument),
        ]
        self.wl.wl_proxy_marshal_array_flags.restype = ctypes.c_void_p

    def _now_ms(self) -> int:
        return int((time.monotonic() - self._start_monotonic) * 1000) & 0xFFFFFFFF

    def _emit_log(self, kind: str, **payload: object) -> None:
        if self.event_sink is not None:
            record = {"ts": time.time(), "kind": kind, **payload}
            self.event_sink(record)

    def connect(self) -> None:
        """Connect to the Wayland display, bind virtual input globals, and upload keymap."""
        name_bytes = self.display_name.encode("utf-8") if self.display_name else None
        self.display = self.wl.wl_display_connect(name_bytes)
        if not self.display:
            raise RuntimeError(
                f"Failed to connect to Wayland display {self.display_name or os.environ.get('WAYLAND_DISPLAY')!r}"
            )

        # Get wl_registry
        args = (_WlArgument * 1)()
        args[0].n = 0
        self.registry = self.wl.wl_proxy_marshal_array_flags(
            self.display,
            WL_DISPLAY_GET_REGISTRY,
            ctypes.byref(self.proto.wl_registry_interface),
            self.wl.wl_proxy_get_version(self.display),
            0,
            args,
        )
        if not self.registry:
            raise RuntimeError("wl_display_get_registry failed")

        GLOBAL_CB = ctypes.CFUNCTYPE(
            None,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_char_p,
            ctypes.c_uint32,
        )
        REMOVE_CB = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32
        )

        def _on_global(_data: int, _reg: int, name: int, iface: bytes, ver: int) -> None:
            iface_name = iface.decode("utf-8", errors="replace")
            if iface_name not in self._globals:
                self._globals[iface_name] = (int(name), int(ver))

        def _on_remove(_data: int, _reg: int, _name: int) -> None:
            pass

        self._global_cb = GLOBAL_CB(_on_global)
        self._remove_cb = REMOVE_CB(_on_remove)
        self._registry_listener = (ctypes.c_void_p * 2)(
            ctypes.cast(self._global_cb, ctypes.c_void_p),
            ctypes.cast(self._remove_cb, ctypes.c_void_p),
        )
        self.wl.wl_proxy_add_listener(
            self.registry, ctypes.byref(self._registry_listener), None
        )
        self.wl.wl_display_roundtrip(self.display)

        for required in (
            "wl_seat",
            "zwp_virtual_keyboard_manager_v1",
            "zwlr_virtual_pointer_manager_v1",
        ):
            if required not in self._globals:
                raise RuntimeError(
                    f"Compositor does not expose required Wayland protocol {required!r}"
                )

        self.seat = self._registry_bind(
            "wl_seat", self.proto.wl_seat_interface, max_version=1
        )
        self.vk_manager = self._registry_bind(
            "zwp_virtual_keyboard_manager_v1",
            self.proto.zwp_virtual_keyboard_manager_v1_interface,
            max_version=1,
        )
        self.vp_manager = self._registry_bind(
            "zwlr_virtual_pointer_manager_v1",
            self.proto.zwlr_virtual_pointer_manager_v1_interface,
            max_version=2,
        )

        # Create virtual keyboard
        vk_args = (_WlArgument * 2)()
        vk_args[0].o = self.seat
        vk_args[1].n = 0
        self.vk = self.wl.wl_proxy_marshal_array_flags(
            self.vk_manager,
            0,  # create_virtual_keyboard
            ctypes.byref(self.proto.zwp_virtual_keyboard_v1_interface),
            1,
            0,
            vk_args,
        )
        if not self.vk:
            raise RuntimeError("create_virtual_keyboard failed")

        # Compile and upload the active system XKB keymap
        self.xkb_config = detect_active_xkb_config()
        keymap_bytes = compile_xkb_keymap(**self.xkb_config)
        fd = os.memfd_create("tamlinux-vkbd-keymap", os.MFD_CLOEXEC)
        os.write(fd, keymap_bytes)
        os.lseek(fd, 0, os.SEEK_SET)
        self._keymap_fd = fd

        km_args = (_WlArgument * 3)()
        km_args[0].u = WL_KEYBOARD_KEYMAP_FORMAT_XKB_V1
        km_args[1].h = fd
        km_args[2].u = len(keymap_bytes)
        self.wl.wl_proxy_marshal_array_flags(
            self.vk, 0, None, 1, 0, km_args  # keymap
        )

        # Create virtual pointer
        vp_ver = min(2, self._globals["zwlr_virtual_pointer_manager_v1"][1])
        vp_args = (_WlArgument * 2)()
        vp_args[0].o = self.seat
        vp_args[1].n = 0
        self.vp = self.wl.wl_proxy_marshal_array_flags(
            self.vp_manager,
            0,  # create_virtual_pointer
            ctypes.byref(self.proto.zwlr_virtual_pointer_v1_interface),
            vp_ver,
            0,
            vp_args,
        )
        if not self.vp:
            raise RuntimeError("create_virtual_pointer failed")

        self.wl.wl_display_roundtrip(self.display)
        pos = self.query_cursor_pos()
        if pos is not None:
            self.last_target_pos = pos

    def _registry_bind(
        self, name: str, iface: _WlInterface, max_version: int
    ) -> int:
        global_name, adv_ver = self._globals[name]
        version = max(1, min(int(max_version), int(adv_ver)))
        args = (_WlArgument * 4)()
        args[0].u = global_name
        args[1].s = iface.name
        args[2].u = version
        args[3].n = 0
        proxy = self.wl.wl_proxy_marshal_array_flags(
            self.registry,
            WL_REGISTRY_BIND,
            ctypes.byref(iface),
            version,
            0,
            args,
        )
        if not proxy:
            raise RuntimeError(f"wl_registry_bind failed for {name}")
        return proxy

    def notify_signal_abort(self, reason: str) -> None:
        """Record an asynchronous emergency stop signal."""
        self._aborted_reason = reason

    @staticmethod
    def query_cursor_pos() -> tuple[int, int] | None:
        """Return current compositor cursor position (x, y) via `hyprctl cursorpos -j`."""
        try:
            out = subprocess.check_output(
                ["hyprctl", "cursorpos", "-j"], text=True, timeout=2
            )
            data = json.loads(out)
            return int(data["x"]), int(data["y"])
        except Exception:
            return None

    @staticmethod
    def query_layout_box() -> tuple[int, int, int, int]:
        """Return (min_x, min_y, extent_x, extent_y) across all compositor monitors."""
        try:
            out = subprocess.check_output(
                ["hyprctl", "monitors", "all", "-j"], text=True, timeout=2
            )
            monitors = [m for m in json.loads(out) if not m.get("disabled", False)]
            if monitors:
                min_x = min(int(m["x"]) for m in monitors)
                min_y = min(int(m["y"]) for m in monitors)
                max_x = max(
                    int(m["x"] + round(m["width"] / float(m.get("scale") or 1.0)))
                    for m in monitors
                )
                max_y = max(
                    int(m["y"] + round(m["height"] / float(m.get("scale") or 1.0)))
                    for m in monitors
                )
                return min_x, min_y, max(1, max_x - min_x), max(1, max_y - min_y)
        except Exception:
            pass
        return 0, 0, 1920, 1080

    def check_emergency_stop(self, check_mouse: bool = True) -> None:
        """Raise EmergencyStopError if the stop keybinding fired or user moved the mouse."""
        if self._aborted_reason:
            raise EmergencyStopError(self._aborted_reason)
        _, stop_path = runtime_state_paths()
        if stop_path.exists():
            try:
                reason = stop_path.read_text(encoding="utf-8").strip()
            except OSError:
                reason = "Emergency stop sentinel detected"
            self._aborted_reason = reason or "Emergency stop sentinel detected"
            raise EmergencyStopError(self._aborted_reason)

        if (
            check_mouse
            and self.mouse_grab_threshold_px > 0
            and self.last_target_pos is not None
        ):
            actual = self.query_cursor_pos()
            if actual is not None:
                dx = actual[0] - self.last_target_pos[0]
                dy = actual[1] - self.last_target_pos[1]
                dist = math.hypot(dx, dy)
                if dist > self.mouse_grab_threshold_px:
                    self._aborted_reason = (
                        f"Physical mouse grab detected: cursor moved to {actual} "
                        f"({dist:.1f} px from expected {self.last_target_pos})"
                    )
                    raise EmergencyStopError(self._aborted_reason)

    def _pointer_frame(self) -> None:
        if not self.vp:
            return
        args = (_WlArgument * 1)()
        self.wl.wl_proxy_marshal_array_flags(self.vp, 4, None, 1, 0, args)

    def _pointer_motion_abs(
        self, x: int, y: int, min_x: int, min_y: int, ext_x: int, ext_y: int
    ) -> None:
        if not self.vp:
            return
        scale = 65535
        nx = max(0, min(scale, int(round((x - min_x) * scale / max(1, ext_x)))))
        ny = max(0, min(scale, int(round((y - min_y) * scale / max(1, ext_y)))))
        args = (_WlArgument * 5)()
        args[0].u = self._now_ms()
        args[1].u = nx
        args[2].u = ny
        args[3].u = scale
        args[4].u = scale
        self.wl.wl_proxy_marshal_array_flags(self.vp, 1, None, 1, 0, args)
        self._pointer_frame()

    def _pointer_motion_rel(self, dx: float, dy: float) -> None:
        if not self.vp:
            return
        args = (_WlArgument * 3)()
        args[0].u = self._now_ms()
        args[1].f = wl_fixed_from_double(dx)
        args[2].f = wl_fixed_from_double(dy)
        self.wl.wl_proxy_marshal_array_flags(self.vp, 0, None, 1, 0, args)
        self._pointer_frame()

    def move_to(
        self,
        x: int,
        y: int,
        duration_ms: int = 60,
        steps: int = 6,
        check_abort: bool = True,
    ) -> tuple[int, int]:
        """Smoothly glide the pointer to logical coordinates (x, y)."""
        if check_abort:
            self.check_emergency_stop(check_mouse=True)
        target_x, target_y = int(round(x)), int(round(y))
        start = self.query_cursor_pos() or self.last_target_pos or (target_x, target_y)
        min_x, min_y, ext_x, ext_y = self.query_layout_box()
        waypoints = interpolate_path(start[0], start[1], target_x, target_y, steps=steps)
        step_sleep = max(0.0, (duration_ms / 1000.0) / max(1, len(waypoints)))

        for wx, wy in waypoints:
            self._pointer_motion_abs(wx, wy, min_x, min_y, ext_x, ext_y)
            self.wl.wl_display_flush(self.display)
            if step_sleep > 0:
                time.sleep(step_sleep)

        self.wl.wl_display_roundtrip(self.display)
        actual = self.query_cursor_pos()
        if actual is not None and (
            abs(actual[0] - target_x) > 1 or abs(actual[1] - target_y) > 1
        ):
            # Closed-loop relative adjustment via virtual pointer
            self._pointer_motion_rel(target_x - actual[0], target_y - actual[1])
            self.wl.wl_display_roundtrip(self.display)
            actual = self.query_cursor_pos()

        self.last_target_pos = actual if actual is not None else (target_x, target_y)
        self._emit_log(
            "pointer_move",
            target=[target_x, target_y],
            actual=list(self.last_target_pos),
            duration_ms=duration_ms,
        )
        return self.last_target_pos

    def button_down(self, button: str | int = "left") -> int:
        """Press and hold a mouse button via zwlr_virtual_pointer_v1."""
        code = (
            button
            if isinstance(button, int)
            else BUTTON_CODES.get(str(button).lower(), BTN_LEFT)
        )
        args = (_WlArgument * 3)()
        args[0].u = self._now_ms()
        args[1].u = code
        args[2].u = WL_POINTER_BUTTON_STATE_PRESSED
        self.wl.wl_proxy_marshal_array_flags(self.vp, 2, None, 1, 0, args)
        self._pointer_frame()
        self.wl.wl_display_roundtrip(self.display)
        self._pressed_buttons.add(code)
        return code

    def button_up(self, button: str | int = "left") -> int:
        """Release a mouse button via zwlr_virtual_pointer_v1."""
        code = (
            button
            if isinstance(button, int)
            else BUTTON_CODES.get(str(button).lower(), BTN_LEFT)
        )
        args = (_WlArgument * 3)()
        args[0].u = self._now_ms()
        args[1].u = code
        args[2].u = WL_POINTER_BUTTON_STATE_RELEASED
        self.wl.wl_proxy_marshal_array_flags(self.vp, 2, None, 1, 0, args)
        self._pointer_frame()
        self.wl.wl_display_roundtrip(self.display)
        self._pressed_buttons.discard(code)
        return code

    def click(
        self,
        button: str | int = "left",
        x: int | None = None,
        y: int | None = None,
        mods: Sequence[str] = (),
        hold_ms: int = 18,
        move_duration_ms: int = 55,
    ) -> None:
        """Optionally move to (x, y) and click `button` with optional keyboard modifiers."""
        self.check_emergency_stop(check_mouse=True)
        if x is not None and y is not None:
            self.move_to(x, y, duration_ms=move_duration_ms)
        mod_codes, mod_mask = resolve_modifiers(mods)
        try:
            if mod_codes:
                self._press_modifiers(mod_codes, mod_mask)
            code = self.button_down(button)
            if hold_ms > 0:
                time.sleep(hold_ms / 1000.0)
            self.button_up(code)
        finally:
            if mod_codes:
                self._release_modifiers(mod_codes)
        pos = self.query_cursor_pos()
        if pos is not None:
            self.last_target_pos = pos
        self._emit_log(
            "pointer_click",
            button=str(button),
            mods=list(mods),
            pos=list(self.last_target_pos or (0, 0)),
        )

    def drag(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        button: str | int = "left",
        mods: Sequence[str] = (),
        duration_ms: int = 80,
        steps: int = 8,
    ) -> None:
        """Move to (x1, y1), hold modifiers + button, glide to (x2, y2), and release."""
        self.check_emergency_stop(check_mouse=True)
        self.move_to(x1, y1, duration_ms=50)
        mod_codes, mod_mask = resolve_modifiers(mods)
        code = (
            button
            if isinstance(button, int)
            else BUTTON_CODES.get(str(button).lower(), BTN_LEFT)
        )
        try:
            if mod_codes:
                self._press_modifiers(mod_codes, mod_mask)
                time.sleep(0.01)
            self.button_down(code)
            time.sleep(0.015)
            # Interpolate drag path without tripping physical mouse check mid-drag
            self.move_to(x2, y2, duration_ms=duration_ms, steps=steps, check_abort=False)
            time.sleep(0.015)
        finally:
            if code in self._pressed_buttons:
                self.button_up(code)
            if mod_codes:
                self._release_modifiers(mod_codes)
        pos = self.query_cursor_pos()
        if pos is not None:
            self.last_target_pos = pos
        self._emit_log(
            "pointer_drag",
            button=str(button),
            mods=list(mods),
            start=[int(x1), int(y1)],
            end=[int(x2), int(y2)],
        )

    def scroll(
        self,
        dy: float = 15.0,
        discrete: int = 1,
        axis: int = WL_POINTER_AXIS_VERTICAL_SCROLL,
        mods: Sequence[str] = (),
    ) -> None:
        """Emit a discrete scroll wheel step."""
        self.check_emergency_stop(check_mouse=True)
        mod_codes, mod_mask = resolve_modifiers(mods)
        try:
            if mod_codes:
                self._press_modifiers(mod_codes, mod_mask)
            src_args = (_WlArgument * 1)()
            src_args[0].u = WL_POINTER_AXIS_SOURCE_WHEEL
            self.wl.wl_proxy_marshal_array_flags(self.vp, 5, None, 1, 0, src_args)

            disc_args = (_WlArgument * 4)()
            disc_args[0].u = self._now_ms()
            disc_args[1].u = axis
            disc_args[2].f = wl_fixed_from_double(dy)
            disc_args[3].i = int(discrete)
            self.wl.wl_proxy_marshal_array_flags(self.vp, 7, None, 1, 0, disc_args)
            self._pointer_frame()
            self.wl.wl_display_roundtrip(self.display)
        finally:
            if mod_codes:
                self._release_modifiers(mod_codes)
        self._emit_log("pointer_scroll", axis=axis, dy=dy, discrete=discrete, mods=list(mods))

    def _send_key(self, evdev_code: int, state: int) -> None:
        if not self.vk:
            return
        args = (_WlArgument * 3)()
        args[0].u = self._now_ms()
        args[1].u = int(evdev_code)
        args[2].u = int(state)
        self.wl.wl_proxy_marshal_array_flags(self.vk, 1, None, 1, 0, args)
        if state == WL_KEYBOARD_KEY_STATE_PRESSED:
            self._pressed_keys.add(int(evdev_code))
        else:
            self._pressed_keys.discard(int(evdev_code))

    def _send_modifiers(self, depressed: int, latched: int = 0, locked: int = 0, group: int = 0) -> None:
        if not self.vk:
            return
        args = (_WlArgument * 4)()
        args[0].u = int(depressed)
        args[1].u = int(latched)
        args[2].u = int(locked)
        args[3].u = int(group)
        self.wl.wl_proxy_marshal_array_flags(self.vk, 2, None, 1, 0, args)
        self._pressed_mods = int(depressed)

    def _press_modifiers(self, mod_codes: Sequence[int], mod_mask: int) -> None:
        for code in mod_codes:
            self._send_key(code, WL_KEYBOARD_KEY_STATE_PRESSED)
        self._send_modifiers(mod_mask)
        self.wl.wl_display_roundtrip(self.display)

    def _release_modifiers(self, mod_codes: Sequence[int]) -> None:
        for code in reversed(mod_codes):
            self._send_key(code, WL_KEYBOARD_KEY_STATE_RELEASED)
        self._send_modifiers(0)
        self.wl.wl_display_roundtrip(self.display)

    def key_tap(
        self,
        key: str | int,
        mods: Sequence[str] = (),
        hold_ms: int = 12,
        check_mouse: bool = True,
    ) -> None:
        """Press and release a key with optional modifiers."""
        self.check_emergency_stop(check_mouse=check_mouse)
        evdev_code = resolve_evdev_key(key)
        mod_codes, mod_mask = resolve_modifiers(mods)
        try:
            if mod_codes:
                self._press_modifiers(mod_codes, mod_mask)
            self._send_key(evdev_code, WL_KEYBOARD_KEY_STATE_PRESSED)
            self.wl.wl_display_roundtrip(self.display)
            if hold_ms > 0:
                time.sleep(hold_ms / 1000.0)
            self._send_key(evdev_code, WL_KEYBOARD_KEY_STATE_RELEASED)
            self.wl.wl_display_roundtrip(self.display)
        finally:
            if mod_codes:
                self._release_modifiers(mod_codes)
        pos = self.query_cursor_pos()
        if pos is not None:
            self.last_target_pos = pos
        self._emit_log("key_tap", key=str(key), evdev=evdev_code, mods=list(mods))

    def chord(self, chord_spec: str, hold_ms: int = 12) -> None:
        """Execute a chord string such as 'META + K' or 'META + SHIFT + U'."""
        mods, key = parse_chord(chord_spec)
        if key.lower().startswith("mouse:"):
            self.click(button=key.lower(), mods=mods, hold_ms=hold_ms)
        else:
            self.key_tap(key, mods=mods, hold_ms=hold_ms)

    def type_text(self, text: str, delay_ms: int = 8) -> None:
        """Type an ASCII string character by character through the virtual keyboard."""
        self.check_emergency_stop(check_mouse=True)
        for ch in text:
            if ch not in CHAR_TO_KEY:
                raise ValueError(f"unsupported character in type_text: {ch!r}")
            key_name, needs_shift = CHAR_TO_KEY[ch]
            mods = ("SHIFT",) if needs_shift else ()
            self.key_tap(key_name, mods=mods, hold_ms=max(4, delay_ms // 2))
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
        self._emit_log("type_text", text=text, length=len(text))

    def release_all(self) -> None:
        """Release any held mouse buttons, keys, or modifiers immediately."""
        if not self.display:
            return
        try:
            for btn in list(self._pressed_buttons):
                try:
                    self.button_up(btn)
                except Exception:
                    pass
            for code in list(self._pressed_keys):
                try:
                    self._send_key(code, WL_KEYBOARD_KEY_STATE_RELEASED)
                except Exception:
                    pass
            if self._pressed_mods or self._pressed_keys:
                self._send_modifiers(0, 0, 0, 0)
            self.wl.wl_display_roundtrip(self.display)
        except Exception:
            pass

    def close(self) -> None:
        """Release all virtual inputs and disconnect from Wayland."""
        self.release_all()
        if self._keymap_fd is not None:
            try:
                os.close(self._keymap_fd)
            except OSError:
                pass
            self._keymap_fd = None
        for proxy_attr in ("vp", "vk", "vp_manager", "vk_manager", "seat", "registry"):
            proxy = getattr(self, proxy_attr, None)
            if proxy:
                try:
                    self.wl.wl_proxy_destroy(proxy)
                except Exception:
                    pass
                setattr(self, proxy_attr, None)
        if self.display:
            try:
                self.wl.wl_display_disconnect(self.display)
            except Exception:
                pass
            self.display = None

    def __enter__(self) -> "WaylandVirtualInput":
        self.connect()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()
