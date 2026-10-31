# Gotchas — Samsung UE48J5248 (`T-N14MJDEUC`) + SamyGO

Practical traps found while rooting, blocking updates, and building the
TV-hosted remote. “Verified” means observed on this TV; “expected” means
documented by SamyGO or inferred from a script.

## Rooting / TV side

- **`run1.sh` hard-codes `/dev/loop3`, which a Smart Hub widget can already
  own.** The boot log shows
  `mount: mounting /tmp/loopnone on /mnt failed: Device or resource busy`, then
  `/mnt` is empty: telnet 3123 answers but `samyGOrc`/`samyGOso` are missing and
  `/dtv/SGO.env` is never created. Recover without rebooting by mounting the
  image on a free loop device and starting `rcSGO`:

  ```sh
  mknod /tmp/loop4 b 7 4
  losetup /tmp/loop4 /dtv/usb/sda1/SamyGO/newvdfs.img
  mount -t vdfs -o sync,exec /tmp/loop4 /mnt
  /mnt/bin/busybox2 sh -x /mnt/rcSGO /mnt
  ```


- **`antysfd.ko` vermagic mismatch — now self-patched on first boot.** The
  module ships as `0177, product SMP preempt mod_unload ARMv7`; this specific TV's
  kernel expects `0143, perf preempt mod_unload ARMv7`. `sfd.sh` now reads the
  expected string from dmesg, patches `/tmp/antysfd.ko` with
  `patch_antysfd.sh`, retries `insmod`, and writes the patched module back to
  `SamyGO/antysfd.ko` on the USB. No PC step and no second reboot. If it
  fails, `SamyGO/vermagic.txt` and the manual `patch.sh`/`patch.bat` remain as
  fallback. Without `antysfd`, Samsung's SFD protection stays active and kills
  external commands (`ls`, `cat`, `id` → `Terminated`). Shell builtins
  (`echo`, `read`, `test`) still work, which makes the shell look broken.
- **`patch.sh` is bash-only and path-sensitive — manual fallback only.** It
  uses `{700..3000}` and `==`, plus relative `./antysfd.ko` /
  `./vermagic.txt`. Run it with `bash` from inside `SamyGO/`, not with `sh`.
  The TV-side `patch_antysfd.sh` is POSIX sh and scans the module itself.
- **`KMOD_VER` is a trap.** `/.version` says `0144.1342`, so `rcSGO` sets
  `KMOD_VER=0144`, but the kernel's real vermagic is `0143, perf…`.
  `samyGOkover … 0144` produces another mismatch.
- **`samyGOkover` only changes the numeric prefix.** It accepts `0143`, not a
  full vermagic string. It cannot turn `product` into `perf`.
- **`anyver.ko` is SMP-built.** This TV's kernel is UP and does not export
  `_raw_spin_lock` / `_raw_spin_unlock`. The module fails with
  `Unknown symbol` and never runs. `insmod -f` does **not** bypass the check.
- **Do not force the module chain.** `anyver` → `newmount` is the SamyGO
  design, but the ABI does not match this kernel. Forcing it is the real
  brick/hang risk. The safe failures (`unknown symbol`, `invalid module
  format`) mean nothing was loaded.
- **Bind mounts are blocked by the kernel.** `mount -o bind` fails with
  `Invalid argument`; dmesg says *“BIND option … You can't use this dangerous
  function on embedded system.”* Blocked for both `busybox` and `mount`.
  `newmount.ko` is the sanctioned unlock, but it cannot load here.
- **`/etc` is read-only squashfs despite 777 permissions.** `touch /etc/x` →
  `Read-only file system`. Editing `/etc/hosts` directly is impossible.
- **USB mount point changes.** Seen as `/dtv/usb/sda1` and later
  `MOUNT_PATH=/dtv/usb/sdj`. Do not hard-code `sda1`.
- **Root USB must stay plugged in.** Removing it while the TV is on can
  freeze/crash it. An empty `STOP_SAMYGO` in the USB root disables root.

## Shell / tooling

- **Telnet 3123 has no TTY.** It prints `can't access tty; job control turned
  off`. Piping commands through `nc` gets them `Terminated`; hold the socket
  open and read until the `VDLinux#>` prompt.
- **`PATH` is incomplete in the interactive shell.** `samyGOrc`,
  `samyGOso`, and `samyGOkover` are not found unless you
  `. /dtv/SGO.env` or use full paths.
- **BusyBox `grep` has no `-a`.** `grep -a` fails silently under
  `2>/dev/null`, which made the firmware domain search look empty.
  `grep -rli` works on text but not binary.
- **BusyBox `timeout` needs `-t`.** `timeout 5 cmd` → `can't execute '5'`;
  use `timeout -t 5 cmd`.
- **The TV's BusyBox has no `wc` applet.** `/bin/busybox wc -c` prints
  `wc: applet not found`. `patch_antysfd.sh` therefore uses `dd` only and
  never calls `wc`. Do not add `wc`-based helpers.
- **`dd` exists but rejects `conv=notrunc`.** A seek write with
  `conv=notrunc` exits 1 and leaves the file unchanged. `patch_antysfd.sh`
  therefore rebuilds the module with basic `dd` and shell appends instead of
  writing in place.
- **`modinfo` fails without `modules.dep`.** Use
  `strings file | grep vermagic` instead.
- **`nslookup` output has the reverse name after the IP.**
  `Address 1: 1.2.3.4 hostname`; parse `$3`, not `$NF`.
- **Useful tools that do exist:** `strings`, `hexdump`, `od`, `base64`,
  `awk`, `ip`, `dnsd`, `insmod`, `rmmod`.

## Keys (`samyGOrc`)

- **This TV's key symbols live in `exeTV` (PID 120), not `exeAPP`.** Running
  `samyGOrc -p $(pidof exeAPP)` reports *cannot find
  `_ZN15KeyInputCreator12NewKeyCommonEv`*. Use
  `pidof exeTV || pidof exeAPP || pidof exeDSP`; the root's own
  `schedulepvr/screenoff.sh` does the same.
- **`SGO.env` does not add the privateer bin directory to `PATH`.** Call
  `/mnt/opt/privateer/usr/bin/samyGOrc` (and `samyGOso`) by full path.

- **Two different `samyGOrc` tools exist.** The Orsay build
  (`-p PID key…`, bugficks 2013) and the Tizen J/K build (`keyname`,
  zoelechat 2016). This TV has the **Orsay** one. Do not use the Tizen key
  list.
- **Orsay codes are the wiki *Index* column, in decimal — not names, not the
  *Code* column, not hex.** Confirmed by `schedulepvr.sh`: `SOURCE=1`,
  `POWER=2`, `VOLUP=7`, `VOLDOWN=11`, `TOOLS=75`, `DOWN=97`, `ENTER=104`.
- **Common codes:** Up 96, Down 97, Left 101, Right 98, OK 104, Back 88,
  Menu 26, Exit 45, Info 31, Tools 75, ChUp 18, ChDown 16, digits
  `1=4 … 9=14`, `0=17`.
- **`samyGOrc` needs a live PID.** `pidof exeAPP` (121 on this TV) or
  `pidof exeDSP`. The PID changes if the app restarts; resolve it on every
  call.
- **Max 32 keys per invocation.**
- **Power codes:** `2` = toggle (used by schedulepvr as `BD_POWER`),
  `152` = power off, `153` = power on. Test last.
- **Smart Hub is unconfirmed.** Try `121` (`KEY_CONTENTS`), then `118`
  (`KEY_HOME`).
- **Volume reads work over UPnP from the TV itself; writes do not.** The exact
  `SetVolume`/`SetMute` request that works from the PC is silently ignored when
  the TV sends it to its own IP; only `GetVolume`/`GetMute` answer. The
  TV-hosted app reads over UPnP and changes volume with keys `7` (up),
  `11` (down), `15` (mute). A slider `set` runs a paced background sweep; the
  HTTP request returns at once and the page polls the ramp.

## TV-hosted app (Apache / PHP)

- **Apache 2.2.14 + PHP 5.2.16 already run on the TV**, as root, on
  `0.0.0.0:1080`, started by `/mnt/etc/init.d/06_05_apache.init`.
- **DocumentRoot is `/dtv/www`, a symlink to `/mnt/var/www`.** The app lives on
  the USB root at `remote/`; the patched `SamyGO/run1.sh` creates
  `/mnt/var/www/remote -> "$1/remote"` after mounting the image. Apache follows
  the symlink (`Options FollowSymLinks`), so the page and PHP API come from the
  USB and survive reboots. The old `/mnt/var/www/remote` directory (from the
  retired deploy method) is removed at boot.
- **PHP is fully usable:** `disable_functions` empty, `allow_url_fopen` On,
  `safe_mode` Off, `curl`/`json`/`sockets`/`SimpleXML` loaded. Keep code
  PHP 5.2-compatible.
- **The USB mounts `noexec` and FAT32 has no reliable execute bit.** Apache
  only reads the app; `volume_sweep.sh` is launched as `/bin/sh <script>` and
  checked with `is_file()`, not `is_executable()`.
- **A multi-key `samyGOrc` invocation drops keys.** `samyGOrc -p PID 7 7 7`
  moved the volume +1, not +3. Send one key per process with ~150 ms spacing;
  `lib/volume_sweep.sh` runs the slider ramp in the background and holds
  `/tmp/samygo-volume.lock` so a second set gets 409.
- **Renderer path is `/smp_13_`** for `RenderingControl` on port 7676. It is a
  firmware path; re-scan `smp_1_`..`smp_30_` if it changes.
- **`SERVER_ADDR` is the TV's LAN IP** when the phone loads the page; use it
  for the renderer URL. `127.0.0.1:7676` is refused.

## Update blocking

- **No iptables, no nftables, no dnsmasq** on this TV.
- **`/etc/hosts` is exact-match only.** Wildcards like
  `az*.vo.msecnd.net` cannot be expressed.
- **Hosts bind-mount is a dead end here** because bind is blocked and
  `newmount.ko` is incompatible.
- **`ip route add blackhole <ip>/32` works** and is reversible; verified with
  a test route. It is IP-based, so it must re-resolve at boot.
- **Some domains are dead:** `msecnd.net`, `www.msecnd.net`,
  `vo.msecnd.net`, `otn.samsungcloudcdn.com`, `samsungcloudsolution.net`
  currently return NXDOMAIN.
- **`osb-apps.samsungqbe.com` resolves to four AWS IPs;** blocking them
  could affect other AWS-backed services. `osb-v2` resolves to one.
- **`/etc/resolv.conf` is a symlink to writable `/mtd_rwarea/resolv.conf`**
  (currently `192.168.1.1`), but there is no local forwarder to point it at.
- **Route blackhole does not survive an IP rotation.** Reboot or re-run
  `/mnt/etc/init.d/01_10_block_updates.init` to refresh.

## Web bridge / security

- **Never reboot the TV from a script or agent.** `reboot` is frequently
  ignored or kills the telnet session, and the TV is a device someone may be
  watching. Ask the owner to reboot it (or power-cycle it) instead; do not send
  `reboot`, `KEY_POWER`, `KEY_POWER_OFF` or `KEY_POWER_ON` unasked.
- **Port 3123 is an unauthenticated root shell.** The web app must never
  expose a generic “run command” endpoint — only fixed
  `samyGOrc` commands with whitelisted numeric codes.
- **The TV-hosted app has no auth.** Auth and CSRF were explicitly out of
  scope; anyone on the LAN can send keys. The whitelist is input validation,
  not a security boundary.
- **The key endpoint maps `KEY_*` names to Orsay codes in
  `remote/lib/keys.php`**; the request value never reaches the shell.
- **No PC state.** `state.json` is gone; the renderer host comes from
  `SERVER_ADDR` and the path is a constant in `remote/lib/config.php`.
- **No deploy service.** The app is copied to the USB; the root shell is only
  for setup and recovery. The app runs `samyGOrc` locally on each request.

