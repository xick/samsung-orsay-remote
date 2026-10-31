#!/bin/sh
good_vermagic=`cat ./vermagic.txt`
file_position=0
for current_position in {700..3000};
do
	test_value=`dd if=./antysfd.ko bs=1 skip=$current_position count=9 conv=notrunc of=/dev/stdout 2> /dev/null`
	if [ "$test_value" == "vermagic=" ]
	then
		file_position=$[current_position + 9]
		echo "Found vermagic at: $file_position";
		break;
	fi
done
echo "$good_vermagic" | dd of=antysfd.ko bs=1 seek=$file_position count=${#good_vermagic} conv=notrunc
dd if=/dev/zero of=antysfd.ko bs=1 seek=$(( $file_position + ${#good_vermagic} )) count=1 conv=notrunc
