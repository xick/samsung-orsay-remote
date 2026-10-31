# Root plan — Samsung UE48J5248 (`T-N14MJDEUC-1150.0`)

Goal: root the TV so we get a shell (`samyGOrc`, `tzcinfo`, …) and can send the
keys the TV refuses over Wi‑Fi today — **channel, arrows, OK, menu** — then feed
them into the web remote.

> **This is a community procedure, not an official one. I have not tested it on
> your TV and cannot guarantee it. There is a real risk of hangs or a brick.
> Read every step before touching the TV. The root lives on a USB stick that
> must stay plugged in.**

---

## Why this method

The firmware string is `T-N14MJDEUC`. SamyGO's wiki states:

> Rooting J series TV rooting method can be
> used (because TVs with `T-NT14MJ*` fw are renamed H series).**

So we use the **H "Network" root**, with the **`newvdfs.img`** variant (the plain
`samyext4.img` "does not correctly support NT14M and NT14MJDEUC"). 

If the Network root fails, fall back to the **H Root Enabler**, or downgrade
first with the **`[FW 0000] … T-N14MJDEUC`** package (links below).

---

## Risk and prerequisites

- **Brick risk:** yes. Have the physical remote and patience.
- **Root USB must stay plugged in** for root to exist; it holds the sysroot.
- **Wi‑Fi required** for the Network root (not Ethernet).
- In the TV menu, turn **off**: `System → General → Samsung Instant ON` and
  `Quickly Power OFF` (if present), and `Smart Hub → Auto update apps`.
- In the **service menu**, **disable Watchdog** (random crashes otherwise).
- You need a **FAT32 USB stick**. A second USB/HDD acting as a "recording
  device" reportedly helps a lot.

### Update blocking

The auto-update is what deletes the root, so it must never reach Samsung. The
last firmware is ~10 years old so a *firmware* update is unlikely — but Smart Hub
**app/widget sync can still delete the root widget**, which is why the J-root
thread insists on blocking `osb-apps.samsungqbe.com`.

- Keep `Auto update apps` **off**.
- Block at the router *before* rooting: `msecnd.net`, `samsungotn.net`, `otn.samsungcloudcdn.com`,
  `samsungcloudsolution.net`, `osb-apps.samsungqbe.com`.
- TV-side (once rooted): copy [`samygo/01_10_block_updates.init`](samygo/01_10_block_updates.init)
  to `/mnt/etc/init.d/` on the TV — at boot it resolves the Samsung update and
  widget hostnames and adds `ip route ... blackhole` entries for their current
  IPs. 
- Because it is IP-based, it is refreshed on each boot. If Samsung rotates IPs
  between boots, reboot to re-resolve.

---

## Files (from the SamyGO forum)

Method thread: `[ROOT] H "Network" root` — forum.samygo.tv `viewtopic.php?t=9622`

Fallbacks:
- H Root Enabler — `viewtopic.php?t=13249`
- FW 0000 downgrade — `viewtopic.php?t=10138`
- Wiki: `wiki.samygo.tv → Rooting_H_series_TV`, `The_J_Series_Wiki`

---

## USB preparation

1. Format a stick **FAT32**.
2. Copy `SamyGO`and `InstallSamyGO-H` folders to the stick root
3. Put **`newvdfs.img`** into `SamyGO/` (or `samyext4.img` if not NT14M or NT14MJDEUC).
4. Copy the web app: put the **contents** of the repo's `remote/` into
   `<USB>/remote/`. Apache serves them through the symlink created by
   `run1.sh`; 
   
| File | Purpose |
|------|---------|
| `SamyGO` | runtime files + `run1.sh`, `patch.sh`/`patch.bat`, `patch_antysfd.sh` |
| `InstallSamyGO-H` | the widget that triggers root |
| `newvdfs.zip` | the NT14M/MJDEUC root image → extract to `newvdfs.img` |
| `sfd.sh.zip` | fallback if `vermagic.txt` is missing/empty |

---

## Procedure

1. Plug the USB in (some people must plug it in **while the TV is off**).
2. Smart Hub → launch **InstallSamyGO-H** (reboot the TV if it doesn't appear, or eject and plug the usb again).
3. Press Enter. **Photograph the on-screen app log** — needed if you ask for help.
   Wait for five "OK" lines.
4. It asks to reboot → reboot and wait ~5 min. On this first boot `sfd.sh`
   reads the TV's vermagic from dmesg, patches `/tmp/antysfd.ko` with
   `patch_antysfd.sh`, retries `insmod`, and writes the patched module back to
   `SamyGO/antysfd.ko` on the USB. **No PC step and no second reboot are
   needed.** The first `insmod` is expected to fail with
   `invalid module format`; the script then patches and retries. Do not stop
   at that error.
5. Verify from the TV or over telnet:
   - `dmesg | grep -i antysfd` should show `Patching sfd.ko successful!!!`
   - `ls`, `cat`, `id` should work instead of returning `Terminated`.
   - `SamyGO/vermagic.txt` is still written for diagnostics.
6. If the self-patch failed, use the manual fallback: run `patch.sh`
   (Linux/macOS) or `patch.bat` (Windows) **from inside `SamyGO/`**, replug
   the USB, and reboot.

---

## Verify root
From a computer on the same network:

```bash
telnet 192.168.1.216 23        # and port 3123
ssh root@192.168.1.216         # password: SamyGO   (port 22)
ftp  192.168.1.216             # port 21
```

If telnet/FTP answers, you're rooted.

```bash
samyGOrc            # prints usage; sends remote keys (channel, arrows, OK, ...)
tzcinfo live        # reads current channel/source/program info
```

Deploy the update block (the script is already on the USB):

```sh
chmod +x /mnt/etc/init.d/01_10_block_updates.init   # /mnt = SYSROOT
sh /mnt/etc/init.d/01_10_block_updates.init start    # apply now
ip route | grep blackhole                            # verify
# log: /dtv/block_updates.log
```

---
## If you remove the USB

- **While the TV is on:** don't — the running system has the sysroot mounted
  from it; expect a freeze/crash.
- **TV off, USB out, power on:** the TV boots normally but **without root**
  (no telnet/FTP/`samyGOrc`). Not bricked — root returns when the USB is back.
- If root won't come back: delete `SamyGO.shm` from the USB root and retry
  (first boot after that can take up to ~5 min).

---

## Known Issues
On some models after every boot it can take a minimum of 5 minutes for everything to set (root, os patching , telnet and apache server)


## Recovery / rollback

- Create an empty file **`STOP_SAMYGO`** in the USB root to stop the root.
- Use telnet **3123** or FTP **21** to fix problems.
- To remove root permanently, telnet in and run
  `rm /mtd_rwarea/network/runSamyGO.sh` **before** unplugging
