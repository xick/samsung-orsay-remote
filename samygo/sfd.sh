#!/bin/sh
/bin/sleep 30
/dtv/bin/ls > /dev/null;
if [ $? -eq 143 ]; 
then 
	echo "SFD detected. Insmoding..."; 
	/bin/cp "$1/SamyGO/antysfd.ko" /tmp/
	/bin/cp "$1/SamyGO/ntkfree" /tmp/
	/sbin/insmod /tmp/antysfd.ko
	if [ $? -ne 0 ]
	then
		good_vermagic=`/bin/dmesg | /bin/grep antysfd | /bin/busybox tail  -n 1 | /bin/busybox cut -d "'" -f 4`
		if [ -z "$good_vermagic" ]
		then
			good_vermagic=`/bin/busybox grep "vermagic=" /mtd_cmmlib/WIFI_LIB/QCA/cfg80211.ko | /bin/busybox head  -n 1 | /bin/busybox cut -d "=" -f 2`
		fi
		if [ -z "$good_vermagic" ]
		then
			good_vermagic=`/bin/busybox grep "vermagic=" /lib/modules/cfg80211.ko | /bin/busybox head  -n 1 | /bin/busybox cut -d "=" -f 2`

		fi
		echo "good vermagic='$good_vermagic'"
		echo "$good_vermagic" > "$1/SamyGO/vermagic.txt"
	fi
	/bin/dmesg | /bin/busybox grep "anty"
	chmod +x /tmp/ntkfree
	mknod /dtv/ntkaxis c 140 0
	/tmp/ntkfree
else 
	echo "NOT-SFD";
fi
