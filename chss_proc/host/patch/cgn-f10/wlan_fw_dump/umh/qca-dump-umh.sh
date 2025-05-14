#!/bin/bash

DEVPATH=$(readlink -f /sys/devices/virtual/devcoredump/devcd*)
timestamp=$(date +%F_%H-%M-%S)
dev=${DEVPATH##*/}
if [ "$1" == "fw_rddm" ]; then
filename=/var/log/qca-fw-error_${dev}_${timestamp}.dump
elif [ "$1" == "fw_sram" ]; then
filename=/var/log/qca-fw-sram_${dev}_${timestamp}.dump
elif [ "$1" == "host_ram" ]; then
filename=/var/log/qca-host-dump_${dev}_${timestamp}.dump
fi
echo "${DEVPATH}" > ${filename}
echo "\n" > ${filename}
cat ${DEVPATH}/data > ${filename}
sync ${filename}
echo 1 > ${DEVPATH}/data
