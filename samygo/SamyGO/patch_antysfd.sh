#!/bin/sh
# Patch the vermagic string inside a kernel module so the TV kernel will load it.
#
# Usage: patch_antysfd <module> <vermagic>
#
# BUSYBOX may be set to the BusyBox binary to use; on the TV it defaults to
# /bin/busybox.  The module is replaced in place.
#
# The TV's BusyBox has no wc applet and its dd rejects conv=notrunc, so this
# script uses dd only and rebuilds the module instead of writing in place.

patch_antysfd() {
	mod="$1"
	good="$2"
	bb="${BUSYBOX:-/bin/busybox}"

	[ -f "$mod" ] || { echo "patch_antysfd: $mod not found"; return 1; }
	[ -n "$good" ] || { echo "patch_antysfd: empty vermagic"; return 1; }

	pos=0

	# Fastest path: the stock module has vermagic= at offset 1329.
	v=`"$bb" dd if="$mod" bs=1 skip=1329 count=9 2>/dev/null`
	if [ "$v" = "vermagic=" ]; then
		pos=1338
	fi

	# Fast path: scan the usual range.  Stop at EOF.
	if [ "$pos" -le 0 ]; then
		i=700
		while [ "$i" -le 3000 ]; do
			v=`"$bb" dd if="$mod" bs=1 skip="$i" count=9 2>/dev/null`
			[ -z "$v" ] && break
			if [ "$v" = "vermagic=" ]; then
				pos=$((i + 9))
				break
			fi
			i=$((i + 1))
		done
	fi

	# Slow path: scan from the start.  Stop at EOF.
	if [ "$pos" -le 0 ]; then
		i=0
		while [ "$i" -le 8192 ]; do
			v=`"$bb" dd if="$mod" bs=1 skip="$i" count=9 2>/dev/null`
			[ -z "$v" ] && break
			if [ "$v" = "vermagic=" ]; then
				pos=$((i + 9))
				break
			fi
			i=$((i + 1))
		done
	fi

	if [ "$pos" -le 0 ]; then
		echo "patch_antysfd: vermagic= not found in $mod"
		return 1
	fi

	# Find the NUL that ends the old vermagic value.
	old_end=0
	i="$pos"
	while [ "$i" -le 8192 ]; do
		c=`"$bb" dd if="$mod" bs=1 skip="$i" count=1 2>/dev/null`
		if [ -z "$c" ]; then
			old_end="$i"
			break
		fi
		i=$((i + 1))
	done

	if [ "$old_end" -le "$pos" ]; then
		echo "patch_antysfd: cannot find end of old vermagic"
		return 1
	fi

	old_len=$((old_end - pos))
	new_len=${#good}
	if [ "$new_len" -gt "$old_len" ]; then
		echo "patch_antysfd: new vermagic is longer than the old one"
		return 1
	fi
	pad=$((old_len - new_len))

	# Build a replacement module.  This avoids dd conv=notrunc, which the
	# TV's BusyBox rejects, and keeps the original file size.
	new="$mod.new"
	"$bb" dd if="$mod" bs=1 count="$pos" of="$new" 2>/dev/null || return 1
	printf '%s' "$good" >> "$new" || return 1
	"$bb" dd if=/dev/zero bs=1 count=1 >> "$new" 2>/dev/null || return 1
	if [ "$pad" -gt 0 ]; then
		"$bb" dd if="$mod" bs=1 skip=$((pos + new_len + 1)) count="$pad" >> "$new" 2>/dev/null || return 1
	fi
	"$bb" dd if="$mod" bs=1 skip=$((old_end + 1)) >> "$new" 2>/dev/null || return 1

	# Verify the replacement before overwriting the original.
	v=`"$bb" dd if="$new" bs=1 skip="$pos" count="$new_len" 2>/dev/null`
	[ "$v" = "$good" ] || { echo "patch_antysfd: verification failed"; return 1; }
	check_off=$((pos + new_len + 4))
	tail_byte=`"$bb" dd if="$new" bs=1 skip="$check_off" count=1 2>/dev/null`
	[ -n "$tail_byte" ] || { echo "patch_antysfd: replacement looks truncated"; return 1; }

	"$bb" dd if="$new" of="$mod" bs=1 2>/dev/null || return 1

	echo "patch_antysfd: vermagic patched successfully"
	return 0
}
