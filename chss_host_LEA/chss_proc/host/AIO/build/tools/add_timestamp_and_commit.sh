#!/bin/bash

VER_INC_PATH="${ATH_TOPDIR}/drivers/qcacld-3.0/core/hdd/inc"
VER_INC_FILE="${VER_INC_PATH}/wlan_hdd_ver.h"
TIME_STAMP=`git log -1 | sed -n '3p' | awk '{sub($1 FS, "");print}' | sed 's/^[ ]*//g'`
COMMIT_ID=`git log -1 | head -n 1 | awk '{print $2}'`
DRIVER_VER=`cat ${ATH_TOPDIR}/drivers/qcacld-3.0/core/mac/inc/qwlan_version.h | grep 'QWLAN_VERSIONSTR' | awk '{print $3}' | tr -d '"'`
FW_VER=
MODULE_TYPE=${1:-"FC64EABMD"}
LOCAL_TIME=

## Get the local time when comiple the driver
export LANG="en_US.UTF-8"
export LC_TIME="en_US.UTF-8"
LOCAL_TIME=`date +"%a %b %d %H:%M:%S %Y %z"`
## Save version info in the header file, and then transfer to
## PROC file while insmod Driver.
if [ -d ${VER_INC_PATH} ]; then
	echo "struct verinfo {" > ${VER_INC_FILE}
	echo -e "\tchar timestamp[32];" >> ${VER_INC_FILE}
	echo -e "\tchar commit_id[32];" >> ${VER_INC_FILE}
	echo -e "\tchar driver_version[16];" >> ${VER_INC_FILE}
	echo -e "\tchar fw_version[16];" >> ${VER_INC_FILE}
	echo -e "\tchar module_type[16];" >> ${VER_INC_FILE}
	echo "};" >> ${VER_INC_FILE}
	if echo "${TIME_STAMP}" | grep -q "not a git repository"; then
		echo "struct verinfo wifi_verinfo = {\"${LOCAL_TIME:0:30}\", \"\", \"\", \"\", \"\"};" >> ${VER_INC_FILE}
	else
		echo "struct verinfo wifi_verinfo = {\"${TIME_STAMP:0:30}\", \"${COMMIT_ID:0:30}\", \"${DRIVER_VER:0:14}\", \"${FW_VER:0:14}\", \"${MODULE_TYPE:0:14}\"};" >> ${VER_INC_FILE}

	fi
fi
