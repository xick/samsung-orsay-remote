#!/bin/sh
/bin/sleep 30
if [ -f "$1/SamyGO/patch_antysfd.sh" ]; then
	. "$1/SamyGO/patch_antysfd.sh"
fi

/dtv/bin/ls > /dev/null;
if [ $? -eq 143 ]; then 
	echo "SFD detected. Insmoding..."; 
	/bin/cp "$1/SamyGO/antysfd.ko" /tmp/
	/bin/cp "$1/SamyGO/ntkfree" /tmp/
	/sbin/insmod /tmp/antysfd.ko
	if [ $? -ne 0 ]
	then
		good_vermagic=`/bin/dmesg | /bin/grep antysfd | /bin/busybox tail  -n 1 | /bin/busybox cut -d "'" -f 4`
		echo "good vermagic='$good_vermagic'"
		echo "$good_vermagic" > "$1/SamyGO/vermagic.txt"

		if [ -n "$good_vermagic" ] && patch_antysfd /tmp/antysfd.ko "$good_vermagic"
		then
			echo "Retrying insmod with patched vermagic..."
			/sbin/insmod /tmp/antysfd.ko
			if [ $? -eq 0 ]
			then
				echo "antysfd loaded after vermagic patch"
				if /bin/cp /tmp/antysfd.ko "$1/SamyGO/antysfd.ko" 2>/dev/null
				then
					echo "patched antysfd.ko written back to USB"
					/bin/busybox sync
				else
					echo "could not write patched antysfd.ko back to USB; /tmp copy is patched"
				fi
			else
				echo "antysfd still failed after vermagic patch"
			fi
		else
			echo "antysfd vermagic patch skipped or failed"
		fi
	fi
	/bin/dmesg | /bin/busybox grep "anty"
	chmod +x /tmp/ntkfree
	mknod /dtv/ntkaxis c 140 0
	/tmp/ntkfree
else 
	echo "NOT-SFD";
fi
