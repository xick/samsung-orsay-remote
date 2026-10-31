#!/usr/bin/env python3
"""Experiment: can the TV's UPnP SendKeyCode action change the channel?

No channel action is advertised anywhere on this TV, so the only candidate is
SendKeyCode, which accepted every volume key we tried and did nothing. This sends
channel-key variants to every service that exposes SendKeyCode, and prints a tag
before each attempt so you can watch the TV and say which tag (if any) changed the
channel. Each attempt sends up then down, so a working pair cancels itself.

    python3 channel_test.py 192.168.1.216              # description variants (safe)
    python3 channel_test.py 192.168.1.216 --codes 40   # also try KeyCode 0..40

WATCH THE TV while it runs. Keep the physical remote handy to put the channel back.
"""
from __future__ import annotations

import argparse
import sys
import time

import upnp
from keycode_test import find_services

# (up description, down description) spellings seen in various Samsung tools.
DESC_PAIRS = [
    ("KEY_CHUP", "KEY_CHDOWN"),
    ("KEY_CHANNELUP", "KEY_CHANNELDOWN"),
    ("CHUP", "CHDOWN"),
    ("KEY_CH+", "KEY_CH-"),
]


def send(svc: dict, code: int, desc: str) -> tuple[int | None, dict]:
    return upnp.soap(
        svc["control"], "SendKeyCode",
        [("KeyCode", code), ("KeyDescription", desc)],
        service_type=svc["type"],
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("host")
    ap.add_argument("--codes", type=int, default=0,
                    help="also sweep KeyCode 0..N with KEY_CHUP/KEY_CHDOWN (default 0 = none)")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between sends")
    opts = ap.parse_args()

    print(f"Looking for SendKeyCode services on {opts.host} ...\n")
    services = find_services(opts.host)
    if not services:
        print("No SendKeyCode service answered. Is the TV fully on?")
        return 1
    for i, s in enumerate(services, 1):
        print(f"S{i}: {s['device']}  {s['type']}")
        print(f"    control: {s['control']}")
    print("\nWATCH THE TV. Tags look like [S1P2] (phase 1) or [S1C7] (phase 2, code 7).\n")

    # Phase 1: description variants with KeyCode 0 (how most community tools send it).
    for i, svc in enumerate(services, 1):
        for j, (up, down) in enumerate(DESC_PAIRS, 1):
            tag = f"S{i}P{j}"
            print(f"[{tag}] {up} / {down}  code=0")
            st, out = send(svc, 0, up)
            print(f"      up   -> HTTP {st}{(' ' + out['_error']) if '_error' in out else ''}", flush=True)
            time.sleep(opts.delay)
            st, out = send(svc, 0, down)
            print(f"      down -> HTTP {st}{(' ' + out['_error']) if '_error' in out else ''}", flush=True)
            time.sleep(opts.delay)

    # Phase 2: numeric KeyCode sweep, only if asked.
    if opts.codes:
        print(f"\nPhase 2: KeyCode 0..{opts.codes} with KEY_CHUP/KEY_CHDOWN\n")
        for i, svc in enumerate(services, 1):
            for code in range(0, opts.codes + 1):
                tag = f"S{i}C{code}"
                print(f"[{tag}] up/down code={code}", flush=True)
                send(svc, code, "KEY_CHUP")
                time.sleep(opts.delay)
                send(svc, code, "KEY_CHDOWN")
                time.sleep(opts.delay)

    print("\n=== Done ===")
    print("Tell me every tag whose attempt moved the channel (or 'none').")
    print("If none did, SendKeyCode is a stub for channel and this TV has no Wi-Fi channel control.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
