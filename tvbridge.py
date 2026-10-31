"""samyGOrc bridge for rooted Orsay Samsung TVs.

The TV's root shell listens on telnet port 3123 (no login).  This module keeps
one serialized connection to it and exposes only one fixed command:
``samyGOrc`` with a numeric key code from :data:`KEY_CODES`.

It never exposes a generic "run this text" endpoint: callers pass a key name
that must exist in :data:`KEY_CODES`, so no user input reaches the shell.
"""
from __future__ import annotations

import asyncio

# SamyGO wiki ``samyGOrc`` **Index** column, decimal values (Orsay build).
# Confirmed by ``schedulepvr.sh`` on this TV: SOURCE=1, POWER=2, VOLUP=7,
# VOLDOWN=11, TOOLS=75, DOWN=97, ENTER=104.  Do not substitute the Tizen key
# names or the hex "Code" column.
KEY_CODES: dict[str, int] = {
    # power / source
    "KEY_SOURCE": 1,
    "KEY_POWER": 2,
    "KEY_POWER_OFF": 152,
    "KEY_POWER_ON": 153,
    "KEY_SLEEP": 3,
    # digits (volume up/down sit at 7 and 11 in the index, so digits skip them)
    "KEY_1": 4,
    "KEY_2": 5,
    "KEY_3": 6,
    "KEY_4": 8,
    "KEY_5": 9,
    "KEY_6": 10,
    "KEY_7": 12,
    "KEY_8": 13,
    "KEY_9": 14,
    "KEY_0": 17,
    # volume / channel
    "KEY_VOLUP": 7,
    "KEY_VOLDOWN": 11,
    "KEY_MUTE": 15,
    "KEY_CHUP": 18,
    "KEY_CHDOWN": 16,
    "KEY_PRECH": 19,
    "KEY_CH_LIST": 107,
    # navigation
    "KEY_UP": 96,
    "KEY_DOWN": 97,
    "KEY_LEFT": 101,
    "KEY_RIGHT": 98,
    "KEY_ENTER": 104,
    "KEY_RETURN": 88,
    "KEY_EXIT": 45,
    # menus / info
    "KEY_MENU": 26,
    "KEY_INFO": 31,
    "KEY_TOOLS": 75,
    "KEY_GUIDE": 79,
    "KEY_TV": 27,
    "KEY_ASPECT": 62,
    "KEY_PMODE": 40,
    # Smart Hub candidates (CONTENTS confirmed on the Samsung remote as the
    # Smart Hub key; HOME is the Tizen spelling, kept for testing)
    "KEY_CONTENTS": 121,
    "KEY_HOME": 118,
    "KEY_APP_LIST": 143,
    "KEY_ENTERTAINMENT": 148,
    "KEY_HDMI": 139,
    # media
    "KEY_PLAY": 71,
    "KEY_PAUSE": 74,
    "KEY_STOP": 70,
    "KEY_REWIND": 69,
    "KEY_FF": 72,
    "KEY_REC": 73,
    # colour buttons
    "KEY_RED": 108,
    "KEY_GREEN": 20,
    "KEY_YELLOW": 21,
    "KEY_CYAN": 22,
}


def key_code(name: str) -> int:
    """Return the Orsay key code for ``name``; raise ``KeyError`` if unknown."""
    return KEY_CODES[name]


# -- telnet shell ----------------------------------------------------------
PROMPT = b"VDLinux#>"
KEY_FAIL_MARKER = "__KEYFAIL__"
# Canonical path from the plan; the schedulepvr copy is an equivalent build
# used as a fallback if the bin copy is missing.
RC_BIN = "/mnt/opt/privateer/usr/bin/samyGOrc"
RC_BIN_FALLBACK = "/mnt/opt/privateer/usr/schedulepvr/libs/samyGOrc"
_BANNER_MARKERS = ("job control turned off", "can't access tty")


class TVError(RuntimeError):
    """The TV's shell did not answer as expected."""


def _strip_iac(data: bytes) -> bytes:
    """Drop telnet IAC negotiations; the shell output is plain text."""
    out = bytearray()
    i = 0
    while i < len(data):
        byte = data[i]
        if byte != 255:  # IAC
            out.append(byte)
            i += 1
            continue
        i += 1
        if i >= len(data):
            break
        command = data[i]
        i += 1
        if command in (251, 252, 253, 254):  # WILL WONT DO DONT: one option byte
            i += 1
        elif command == 250:  # SB ... IAC SE
            end = data.find(b"\xff\xf0", i)
            i = len(data) if end == -1 else end + 2
    return bytes(out)


class TVShell:
    """One serialized telnet connection to the TV's root shell (port 3123)."""

    def __init__(self, host: str, port: int = 3123) -> None:
        self.host = host
        self.port = port
        self._lock = asyncio.Lock()
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._buffer = b""

    # -- connection ------------------------------------------------------
    async def _connect(self, timeout: float) -> None:
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port), timeout
        )
        self._buffer = b""
        await self._read_until_prompt(timeout)  # discard the boot banner

    async def _read_until_prompt(self, timeout: float) -> bytes:
        if self._reader is None:
            raise TVError("not connected")
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while True:
            index = self._buffer.find(PROMPT)
            if index != -1:
                payload = self._buffer[:index]
                self._buffer = self._buffer[index + len(PROMPT):].lstrip(b" ")
                return payload
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise TVError("timed out waiting for the TV prompt")
            chunk = await asyncio.wait_for(self._reader.read(4096), remaining)
            if not chunk:
                raise TVError("the TV closed the shell connection")
            self._buffer += _strip_iac(chunk)

    async def close(self) -> None:
        writer, self._writer = self._writer, None
        self._reader = None
        self._buffer = b""
        if writer is not None:
            try:
                writer.close()
                await writer.wait_closed()
            except (OSError, ConnectionError):
                pass

    # -- commands --------------------------------------------------------
    @staticmethod
    def _clean(payload: bytes, command: str) -> str:
        text = payload.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n")
        lines = [line for line in text.split("\n")
                 if line.strip() and not any(marker in line for marker in _BANNER_MARKERS)]
        if lines and lines[0].strip() == command.strip():  # the shell echoes input
            lines.pop(0)
        return "\n".join(lines).strip("\n")

    async def run(self, command: str, timeout: float = 6.0) -> str:
        """Run one fixed command on the shell.

        A failure after the write is not retried: replaying the command could
        press a toggle key (power) twice.  The connection is dropped instead,
        and the next call reconnects.
        """
        async with self._lock:
            if self._writer is None or self._writer.is_closing():
                try:
                    await self._connect(timeout)
                except (OSError, asyncio.TimeoutError, ConnectionError) as err:
                    await self.close()
                    raise TVError(
                        f"TV shell at {self.host}:{self.port} is unreachable: {err}"
                    ) from err
            assert self._writer is not None
            try:
                self._writer.write((command + "\n").encode())
                await self._writer.drain()
                payload = await self._read_until_prompt(timeout)
            except (TVError, OSError, asyncio.TimeoutError, ConnectionError) as err:
                await self.close()
                raise TVError(
                    f"TV shell at {self.host}:{self.port} failed: {err}"
                ) from err
            return self._clean(payload, command)

    async def ping(self, timeout: float = 1.5) -> bool:
        """True when the root shell answers a trivial command."""
        try:
            await self.run("true", timeout=timeout)
            return True
        except TVError:
            return False

    async def send_key(self, name: str) -> None:
        """Send a whitelisted key; unknown names raise ``KeyError`` unconnected."""
        code = key_code(name)
        # exeTV owns the key symbols on this J-series set; exeAPP/exeDSP are
        # fallbacks for other Orsay builds.  Full paths: SGO.env does not add
        # the privateer bin directory to PATH.
        command = (
            ". /dtv/SGO.env; "
            "p=$(pidof exeTV || pidof exeAPP || pidof exeDSP); "
            f'rc={RC_BIN}; [ -x "$rc" ] || rc={RC_BIN_FALLBACK}; '
            f'if [ -z "$p" ]; then echo {KEY_FAIL_MARKER}; '
            f'else "$rc" -p "$p" {code} || echo {KEY_FAIL_MARKER}; fi'
        )
        output = await self.run(command)
        if KEY_FAIL_MARKER in output:
            raise TVError(
                "samyGOrc did not send the key (no exeTV/exeAPP PID or symbol lookup failed)"
            )
