#!/bin/sh
# Ramp the TV volume with paced samyGOrc presses.
# Usage: volume_sweep.sh CODE COUNT
# api/volume.php returns before this finishes; the UI polls the result.
code="$1"
count="$2"

exec 9>/tmp/samygo-volume.lock
/dtv/bin/flock -n 9 || exit 0

pid=$(/dtv/bin/pidof exeTV || /dtv/bin/pidof exeAPP || /dtv/bin/pidof exeDSP)
[ -z "$pid" ] && exit 1

rc=/mnt/opt/privateer/usr/bin/samyGOrc
[ -x "$rc" ] || rc=/mnt/opt/privateer/usr/schedulepvr/libs/samyGOrc
[ -x "$rc" ] || exit 1

i=0
while [ "$i" -lt "$count" ]; do
    "$rc" -p "$pid" "$code" >/dev/null 2>&1
    /dtv/bin/sleep 0.15
    i=$((i + 1))
done
