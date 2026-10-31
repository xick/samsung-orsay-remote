#!/bin/sh
# emergency skript exit to prevent boot loop
      for USB in ${1:- \
         /dtv/usb/sd* } ; do
         echo "checking $USB"
		 /bin/sleep 1
         if [ -e $USB/STOP_SAMYGO ]; then
            "STOP found. Script exit..."
            exit 1
         fi
      done
cd /tmp
mkdir /tmp/bin
echo OK > /tmp/rooted
if [ -e /dtv/qcm_samygo ]
then
    exit
else
    touch  /dtv/qcm_samygo
fi
cp $1/SamyGO/samygo_telnetd /dtv/
chmod +x /dtv/samygo_telnetd
/dtv/samygo_telnetd 33&
	

cp "$1/SamyGO/busybox" /tmp/bin/
chmod +x /tmp/bin/busybox
/tmp/bin/busybox --install -s /tmp/bin
sync
export PATH=/tmp/bin:$PATH
export LD_LIBRARY_PATH=/tmp/bin:$LD_LIBRARY_PATH
sync
/tmp/bin/busybox tcpsvd -vE 0.0.0.0 21 /tmp/bin/busybox ftpd -w / &
sync

# pick a free loop device; /dev/loop3 is often taken by a Smart Hub widget
LOOPN=$(/tmp/bin/busybox losetup -f)
LOOPNUM=${LOOPN#/dev/loop}
/tmp/bin/busybox mknod /tmp/samloop b 7 "$LOOPNUM" 2>/dev/null
rm -f /tmp/loopnone
ln -s /tmp/samloop /tmp/loopnone
sync
if [ -e "$1/SamyGO/newvdfs.img" ]
then
	/tmp/bin/busybox losetup /tmp/loopnone  "$1/SamyGO/newvdfs.img"
	/tmp/bin/busybox mount -t vdfs -o sync,exec /tmp/loopnone /mnt
else
	/tmp/bin/busybox losetup /tmp/loopnone  "$1/SamyGO/samyext4.img"
	/tmp/bin/busybox mount -t ext4 -o sync,exec /tmp/loopnone /mnt
fi

# Serve the web app from the USB root (remote/), not from the image.
mkdir -p /mnt/var/www
rm -rf /mnt/var/www/remote
ln -s "$1/remote" /mnt/var/www/remote
/tmp/bin/busybox --install -s /mnt/bin
sync
rm /mnt/sam.log 
ls -la /mnt/* >> /mnt/sam.log 2>&1
echo "===========================" >> /mnt/sam.log 2>&1
echo "Starting rcSGO from run1.sh" >> /mnt/sam.log 2>&1
echo "===========================" >> /mnt/sam.log 2>&1
/mnt/bin/busybox2 sh -x /mnt/rcSGO /mnt >> /mnt/sam.log 2>&1

