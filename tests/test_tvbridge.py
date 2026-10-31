"""Tests for the samyGOrc bridge (stdlib only)."""
from __future__ import annotations

import asyncio
import unittest

from tvbridge import KEY_CODES, TVError, TVShell, key_code


class KeyCodeTest(unittest.TestCase):
    def test_representative_codes(self) -> None:
        self.assertEqual(KEY_CODES["KEY_UP"], 96)
        self.assertEqual(KEY_CODES["KEY_DOWN"], 97)
        self.assertEqual(KEY_CODES["KEY_LEFT"], 101)
        self.assertEqual(KEY_CODES["KEY_RIGHT"], 98)
        self.assertEqual(KEY_CODES["KEY_ENTER"], 104)
        self.assertEqual(KEY_CODES["KEY_RETURN"], 88)
        self.assertEqual(KEY_CODES["KEY_MENU"], 26)
        self.assertEqual(KEY_CODES["KEY_SOURCE"], 1)
        self.assertEqual(KEY_CODES["KEY_CHUP"], 18)
        self.assertEqual(KEY_CODES["KEY_CHDOWN"], 16)
        self.assertEqual(KEY_CODES["KEY_0"], 17)
        self.assertEqual(KEY_CODES["KEY_1"], 4)
        self.assertEqual(KEY_CODES["KEY_9"], 14)
        self.assertEqual(KEY_CODES["KEY_POWER"], 2)
        self.assertEqual(KEY_CODES["KEY_POWER_OFF"], 152)
        self.assertEqual(KEY_CODES["KEY_POWER_ON"], 153)

    def test_key_code_returns_int(self) -> None:
        self.assertEqual(key_code("KEY_INFO"), 31)

    def test_unknown_key_raises(self) -> None:
        with self.assertRaises(KeyError):
            key_code("KEY_NOPE")

    def test_unknown_key_is_not_a_shell_metacharacter_key(self) -> None:
        with self.assertRaises(KeyError):
            key_code("KEY_UP;reboot")


class FakeTV:
    """A tiny telnet shell that behaves like the TV's port 3123.

    It prints the boot banner and prompt, echoes each command, then replies
    with the command's output and a fresh prompt.
    """

    def __init__(self) -> None:
        self.server: asyncio.AbstractServer | None = None
        self.port = 0
        self.commands: list[str] = []
        self.connections = 0
        self.close_once = False
        self.key_fail = False
        self.delay_once = 0.0
        self.split_prompt = False

    async def start(self) -> None:
        self.server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]

    async def stop(self) -> None:
        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()

    def _reply(self, command: str) -> str:
        if command.startswith("echo "):
            return command[5:]
        if "samyGOrc" in command:
            return "__KEYFAIL__" if self.key_fail else ""
        return "ok"

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.connections += 1
        writer.write(b"\r\ncan't access tty; job control turned off\r\nVDLinux#> ")
        await writer.drain()
        try:
            while True:
                line = await reader.readline()
                if not line:
                    return
                command = line.decode().strip()
                self.commands.append(command)
                if self.close_once:
                    self.close_once = False
                    return
                if self.delay_once:
                    delay, self.delay_once = self.delay_once, 0.0
                    await asyncio.sleep(delay)
                data = (command + "\r\n" + self._reply(command) + "\r\nVDLinux#> ").encode()
                try:
                    if self.split_prompt:  # split the prompt across two reads
                        cut = len(data) // 2
                        writer.write(data[:cut])
                        await writer.drain()
                        await asyncio.sleep(0.05)
                        writer.write(data[cut:])
                    else:
                        writer.write(data)
                    await writer.drain()
                except (ConnectionError, OSError):
                    return
        finally:
            writer.close()


class TVShellTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.tv = FakeTV()
        await self.tv.start()
        self.shell = TVShell("127.0.0.1", self.tv.port)

    async def asyncTearDown(self) -> None:
        await self.shell.close()
        await self.tv.stop()

    async def test_run_strips_banner_and_prompt(self) -> None:
        self.assertEqual(await self.shell.run("echo hi", timeout=2), "hi")
        self.assertEqual(self.tv.connections, 1)

    async def test_run_reuses_one_connection(self) -> None:
        self.assertEqual(await self.shell.run("echo one", timeout=2), "one")
        self.assertEqual(await self.shell.run("echo two", timeout=2), "two")
        self.assertEqual(self.tv.connections, 1)

    async def test_concurrent_runs_do_not_interleave(self) -> None:
        first, second = await asyncio.gather(
            self.shell.run("echo one", timeout=2),
            self.shell.run("echo two", timeout=2),
        )
        self.assertEqual((first, second), ("one", "two"))
        self.assertEqual(self.tv.connections, 1)

    async def test_reconnects_on_the_next_request(self) -> None:
        self.tv.close_once = True
        with self.assertRaises(TVError):
            await self.shell.run("echo hi", timeout=1)
        self.assertEqual(await self.shell.run("echo hi", timeout=2), "hi")
        self.assertEqual(self.tv.connections, 2)

    async def test_timed_out_command_is_not_replayed(self) -> None:
        self.tv.delay_once = 2.0
        with self.assertRaises(TVError):
            await self.shell.run("echo hi", timeout=0.5)
        self.assertEqual(len(self.tv.commands), 1)
        self.assertEqual(await self.shell.run("echo hi", timeout=2), "hi")
        self.assertEqual(len(self.tv.commands), 2)

    async def test_split_prompt_is_reassembled(self) -> None:
        self.tv.split_prompt = True
        self.assertEqual(await self.shell.run("echo hi", timeout=2), "hi")

    async def test_ping_true_while_connected(self) -> None:
        self.assertIs(await self.shell.ping(), True)

    async def test_ping_false_when_tv_is_gone(self) -> None:
        await self.tv.stop()
        self.assertIs(await self.shell.ping(), False)

    async def test_send_key_uses_whitelisted_code(self) -> None:
        await self.shell.send_key("KEY_INFO")
        command = self.tv.commands[-1]
        self.assertIn("/mnt/opt/privateer/usr/bin/samyGOrc", command)
        self.assertIn("pidof exeTV", command)
        self.assertIn(" 31", command)
        # The command must run the binary when a PID exists, not only when the
        # PID is missing (a missing `else` made every key a silent no-op).
        self.assertIn('if [ -z "$p" ]; then echo __KEYFAIL__; else', command)
        self.assertIn('"$rc" -p "$p" 31 || echo __KEYFAIL__', command)

    async def test_send_key_without_tv_process_is_an_error(self) -> None:
        self.tv.key_fail = True
        with self.assertRaises(TVError):
            await self.shell.send_key("KEY_UP")

    async def test_send_key_rejects_unknown_name_before_shell(self) -> None:
        with self.assertRaises(KeyError):
            await self.shell.send_key("KEY_NOPE")
        with self.assertRaises(KeyError):
            await self.shell.send_key("KEY_UP; reboot")
        self.assertEqual(self.tv.commands, [])



if __name__ == "__main__":
    unittest.main()
