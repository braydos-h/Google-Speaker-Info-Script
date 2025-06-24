#!/usr/bin/env python3
"""
googlespeakerinfo.py – CLI dashboard & utility for the
/setup/eureka_info endpoint
-------------------------------------------------------------------------------
• Live, colour‑coded dashboard that refreshes every *n* seconds
• Interactive text menu to tweak URL, refresh interval, or dump raw JSON
• Pure‑stdlib except for *colour* – if the optional **colorama** package is
  present, the output will be ANSI‑coloured; otherwise it degrades gracefully.

Usage (Windows, macOS, Linux):
  python googlespeakerinfo.py

If you want colours on Windows classic console:
  pip install colorama

Author: maybe braydos but mainly vibe coded (2025‑05‑19)
"""

from __future__ import annotations

import datetime as _dt
import json as _json
import os as _os
import sys as _sys
import time as _time
import urllib.error as _ue
import urllib.request as _ur
from types import SimpleNamespace as _NS

# ── Optional colour support via colourama ───────
try:
    from colorama import Fore, Style, init as _cinit  # type: ignore

    _cinit()  # initialise on Windows so ANSI works

    class _Pal:
        CYAN = Fore.CYAN + Style.BRIGHT
        GREEN = Fore.GREEN + Style.BRIGHT
        YELLOW = Fore.YELLOW + Style.BRIGHT
        RED = Fore.RED + Style.BRIGHT
        HEADER = Style.BRIGHT + Fore.WHITE + "\x1b[45m"  # purple background
        RESET = Style.RESET_ALL

    def _c(txt: str, colour: str | None = None) -> str:  # colour‑helper
        if colour is None:
            return txt
        pal = getattr(_Pal, colour, "")
        return f"{pal}{txt}{_Pal.RESET}"

except (
    ModuleNotFoundError
):  # colourama not installed – fall back to plain text

    class _Pal:  # dummy placeholders so attr look‑ups don’t explode
        CYAN = GREEN = YELLOW = RED = HEADER = RESET = ""

    def _c(
        txt: str, colour: str | None = None
    ) -> str:  # noqa: D401 – simple style
        return txt


# ── Small helpers ─────────────


def _clear() -> None:
    """Clear the terminal/console window (cross‑platform)."""
    _os.system("cls" if _os.name == "nt" else "clear")


def _fetch(url: str, timeout: float = 3.0) -> dict:
    """Fetch JSON from *url* and return as dict, raising on errors."""
    with _ur.urlopen(url, timeout=timeout) as resp:
        return _json.load(resp)


def _wifi_colour(rssi: int) -> str:
    """Return colour name for Wi‑Fi RSSI (dBm)."""
    if rssi >= -55:
        return "GREEN"
    if rssi >= -65:
        return "YELLOW"
    return "RED"


def _line(label: str, value: object, colour: str | None = None) -> None:
    pad = f"{label}:".ljust(18)
    print(_c(pad, "CYAN"), _c(value, colour))


# ── Dashboard renderer ───────────


def _dash(data: dict) -> None:
    boot_utc = _dt.datetime.utcnow() - _dt.timedelta(
        seconds=data.get("uptime", 0)
    )
    up_span = _dt.timedelta(seconds=data.get("uptime", 0))

    update_col = "YELLOW" if data.get("has_update") else "CYAN"
    wifi_rssi = int(data.get("signal_level", -100))

    term_width = _os.get_terminal_size().columns
    header = _c(" Google‑Speaker Info ", "HEADER")
    print(header.ljust(term_width))
    print()

    _line("Timestamp", _dt.datetime.now().strftime("%Y‑%m‑%d %H:%M:%S"))
    _line("Name", data.get("name", "?"), "GREEN")
    _line("Build Rev", data.get("cast_build_revision"))
    _line("Track", data.get("release_track"))
    _line("Update Pending", data.get("has_update"), update_col)
    _line("Uptime", str(up_span))
    _line("Boot (UTC)", boot_utc.strftime("%Y‑%m‑%d %H:%M:%S"))
    print()

    _line("SSID", data.get("ssid"))
    _line("BSSID", data.get("bssid"))
    _line("Wi‑Fi RSSI", f"{wifi_rssi} dBm", _wifi_colour(wifi_rssi))
    _line("Noise Floor", f"{data.get('noise_level', '?')} dBm")
    _line("IP", data.get("ip_address"))
    _line("MAC", data.get("mac_address"))
    _line("Ethernet", data.get("ethernet_connected"))
    print()

    _line("Locale", data.get("locale"))
    _line("Country", data.get("location", {}).get("country_code"))
    _line("Fuchsia Ver", data.get("version"))
    _line("Time‑Zone", data.get("timezone"))
    _line("Opt‑In Crash", data.get("opt_in", {}).get("crash"))
    _line("Opt‑In Stats", data.get("opt_in", {}).get("stats"))
    print()
    print(
        _c("Green = good · Yellow = meh · Red = bad/needs attention", "CYAN")
    )


# ── Live dashboard loop ──────────


def _live(url: str, interval: int) -> None:
    while True:
        try:
            data = _fetch(url)
            _clear()
            _dash(data)
        except (_ue.URLError, _ue.HTTPError, TimeoutError, ValueError) as exc:
            print(_c(f"Error: {exc}", "RED"))
        except KeyboardInterrupt:
            print("\nInterrupted. Returning to menu…")
            return
        _time.sleep(interval)


# ── One‑shot JSON dump ───────────


def _dump(url: str, path: str) -> None:
    data = _fetch(url)
    with open(path, "w", encoding="utf‑8") as fh:
        _json.dump(data, fh, indent=2)
    print(f"Wrote {len(data)} top‑level keys to {path}")


# ── Main interactive menu ───────────


def _menu():
    state = _NS(
        url="http://192.168.8.110:8008/setup/eureka_info?options=detail",
        interval=5,
    )
    while True:
        print("\n── Google Speaker Info ─────────────")
        print(f"Current URL            : {state.url}")
        print(f"Current refresh interval: {state.interval} s")
        print("1) Start live dashboard")
        print("2) Change URL")
        print("3) Change interval")
        print("4) One‑off JSON dump")
        print("5) Exit")
        choice = input("Select > ").strip()
        if choice == "1":
            _live(state.url, state.interval)
        elif choice == "2":
            new = input("New URL > ").strip()
            if new:
                state.url = new
        elif choice == "3":
            try:
                state.interval = int(input("Interval (seconds) > ").strip())
            except ValueError:
                print("Not a number → keeping previous interval.")
        elif choice == "4":
            path = (
                input("File to save (default eureka.json) > ").strip()
                or "eureka.json"
            )
            try:
                _dump(state.url, path)
            except Exception as exc:  # broad: user just wants message
                print(_c(f"Dump failed: {exc}", "RED"))
        elif choice == "5":
            print("Bye!")
            _sys.exit(0)
        else:
            print("Unknown selection – try again.")


# ── Entry point ───────────
if __name__ == "__main__":
    try:
        _menu()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
