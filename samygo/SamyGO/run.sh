#!/bin/sh
/bin/sleep 30
echo OK > /tmp/rooted
echo OK > "$1/SamyGO/getroot.ok"
/bin/busybox sync

/bin/rm  "$1/SamyGO/sam.log"

/bin/sh -x "$1/SamyGO/sfd.sh" "$1" >> "$1/SamyGO/sam.log"  2>&1

if [ -e "$1/SamyGO/ext3.sh" ]
then
    /bin/sh -x "$1/SamyGO/ext3.sh" "$1" >> "$1/SamyGO/sam.log"  2>&1
fi

if [ -e "$1/SamyGO/lan.sh" ]
then
    /bin/sh -x "$1/SamyGO/lan.sh" "$1" >> "$1/SamyGO/sam.log"  2>&1
fi

/bin/sh -x "$1/SamyGO/run1.sh" "$1" >> "$1/SamyGO/sam.log"  2>&1
