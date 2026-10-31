#!/usr/bin/env python3
"""Prove that the TV's UPnP volume/mute really work, before the web remote uses them.

Pure standard library, nothing to install:

    python3 verify_volume.py 192.168.1.216

It discovers the RenderingControl service, reads the current volume and mute, sets
volume up and down by one step, toggles mute, reads each change back, and then
restores your original volume and mute. It reports exactly what answered, so a
no-op service cannot pass. Turn the TV on first.
"""
from __future__ import annotations

import sys

from upnp import (
    discover_rendering_control,
    get_mute,
    get_volume,
    set_mute,
    set_volume,
)

results: list[tuple[str, bool, str]] = []


def check(label: str, ok: bool, note: str) -> None:
    results.append((label, ok, note))
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {note}", flush=True)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    host = sys.argv[1]
    print(f"Verifying UPnP volume on {host}\n")

    control = discover_rendering_control(host)
    if control is None:
        print("No RenderingControl service answered. Is the TV fully on and on this network?")
        return 1
    print(f"RenderingControl control URL: {control}\n")

    try:
        base_vol = get_volume(control)
        base_mute = get_mute(control)
    except RuntimeError as err:
        print(f"Could not read the TV's volume: {err}")
        return 1
    print(f"Current state: volume={base_vol} mute={base_mute}\n")

    try:
        up = base_vol + 1 if base_vol < 100 else base_vol - 1
        set_volume(control, up)
        after = get_volume(control)
        check("SetVolume changes volume", after == up, f"set {up}, read back {after}")

        down = base_vol - 1 if base_vol > 0 else base_vol + 1
        set_volume(control, down)
        after = get_volume(control)
        check("SetVolume works both directions", after == down, f"set {down}, read back {after}")

        set_volume(control, base_vol)
        after = get_volume(control)
        check("volume restored", after == base_vol, f"set {base_vol}, read back {after}")

        set_mute(control, not base_mute)
        after = get_mute(control)
        check("SetMute toggles mute", after == (not base_mute), f"set {not base_mute}, read back {after}")

        set_mute(control, base_mute)
        after = get_mute(control)
        check("mute restored", after == base_mute, f"set {base_mute}, read back {after}")
    except RuntimeError as err:
        check("write test", False, str(err))
    finally:
        try:
            set_volume(control, base_vol)
            set_mute(control, base_mute)
        except RuntimeError:
            pass

    print("\n=== Summary ===")
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"{passed}/{len(results)} checks passed")
    if passed == len(results) and results:
        print("UPnP volume and mute work. The web remote can be built on them.")
        return 0
    print("Not all checks passed. Do NOT build the UI on this until it works;")
    print("send the output above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
