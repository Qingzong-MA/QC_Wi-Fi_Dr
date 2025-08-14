#!/bin/bash
CRASH_CMD="$(pwd)/crash"

ret_u32=0
ret_u64=0
ret_str=foo.bin

read_u32() {
    ret_hex=0

    temp_buffer=`hd -s $1 -n 5 $fw_sram_file | (read b1 b2 b3 b4 b5 b6;echo $b5$b4$b3$b2)`
    ret_hex=${temp_buffer}

    ((ret_u32=16#$ret_hex))
}

read_u64() {
    ret_hex=0

    temp_buffer=`hd -s $1 -n 9 $fw_sram_file | (read b1 b2 b3 b4 b5 b6 b7 b8 b9 b10;echo $b9$b8$b7$b6$b5$b4$b3$b2)`
    ret_hex=${temp_buffer}

    ((ret_u64=16#$ret_hex))
}

read_name() {
    temp_buffer=`hd -e '20/1 "%c"' -s $1 -n 20 $fw_sram_file`
    char_buffer=`expr substr "$temp_buffer" 80 20`
    ret_str=${char_buffer%%000*}
}

read_buffer_to_file() {
    dd if=$fw_sram_file of=$3 bs=1 count=$2 skip=$1
}

#------------------------------------------------------------------------------
##define MAX_RAMDUMP_TABLE_SIZE  6
#typedef struct
#{
#  uint64 base_address;
#  uint64 actual_phys_address;
#  uint64 size;
#  char description[20];
#  char file_name[20];
#}ramdump_entry;

#typedef struct
#{
#  uint32 version;
#  uint32 header_size;
#  ramdump_entry ramdump_table[MAX_RAMDUMP_TABLE_SIZE];
#}ramdump_header_t;

#ramdump_header_t rddm_dump_header =
#{
#  0x1, /*version*/
#  sizeof(ramdump_header_t),
#  {
#    Q6_SRAM_FULL_RAMDUMP_HEADER,
#    ETB_SOC_RAMDUMP_HEADER,
#    ETB_WCSS_RAMDUMP_HEADER,
#    M3_PHYA_RAMDUMP_HEADER,
#    M3_PHYB_RAMDUMP_HEADER,
#  }
#};

##define Q6_SRAM_FULL_RAMDUMP_HEADER     {SRAM_BASE_ADDRESS, SRAM_BASE_ADDRESS, SRAM_SIZE, "Q6-SRAM", "Q6-SRAM.bin"}
##define ETB_SOC_RAMDUMP_HEADER          {ETB_TEMP_BUFFER_ADDRESS, NULL, ETB_SOC_SIZE, "ETB_SOC_16K", "ETB_SOC.bin"}
##define ETB_WCSS_RAMDUMP_HEADER         {ETB_TEMP_BUFFER_ADDRESS, NULL, ETB_WCSS_SIZE, "ETB_WCSS_8K", "ETB_WCSS.bin"}
##define M3_PHYA_RAMDUMP_HEADER          {M3_PDMEM_TEMP_BUFFER_ADDR, M3_PHYA_PDMEM_BASE_ADDR, M3_PHYA_PDMEM_SIZE, "PHYA-M3", "PHYA-M3.3.bin"}
##define M3_PHYB_RAMDUMP_HEADER          {M3_PDMEM_TEMP_BUFFER_ADDR, M3_PHYB_PDMEM_BASE_ADDR, M3_PHYB_PDMEM_SIZE, "PHYB-M3", "PHYB-M3.3.bin"}
#------------------------------------------------------------------------------
sram_parser() {
    echo "Parsing $1 to get separate dump files..."

    header_offset=0
    file_offset=0

    # get version
    read_u32 $header_offset
    echo dump version $ret_u32
    let header_offset+=4

    # get header length
    read_u32 $header_offset
    file_offset=$ret_u32
    echo dump header length $file_offset

    # version + header_size size = 8
    # ramdump_entry size = 64
    let "entries = ($file_offset - 8) / 64"
    echo ramdump_table entries is $entries
    let header_offset+=4

    for (( i = 1; i <= $entries; i++ )); do
        tmp=0

        # get file length and file name
        let tmp=$header_offset+16
        read_u64 $tmp

        if [ $ret_u64 -ne 0 ]; then
            let tmp=$header_offset+44
            read_name $tmp
            echo file $i name $ret_str with length $ret_u64

            # write file
            read_buffer_to_file $file_offset $ret_u64 $ret_str
            let file_offset+=$ret_u64
        fi

        let header_offset+=64
    done
}

print_usage() {
  echo "Usage:"
  echo "Format1: $0 <vmlinux> <vmcore>"
  echo "Format2: $0"
  echo ""
  echo "Options:"
  echo "     -h: Display this help message"
}
while getopts "h" opt; do
    case $opt in
        h) print_usage; exit 0 ;;
    esac
done

if [ $# -ne 0 ] && [ $# -ne 2 ]; then
  echo "Parameters incorrect, please refer:"
  print_usage
  exit 1
fi

fw_sram_file="fwsramfull.bin"
fw_paging_dump_file="paging.bin"
fw_remote_mem_dump_file="remote.bin"

###############################################################################
# Prepare vmlinux file for crash
#------------------------------------------------------------------------------
vmlinux_file=$1
if [ ! -e "${vmlinux_file}" ]; then
    echo -n "vmlinux path and filename?:"
    read vmlinux_file_in
    if [ -n "${vmlinux_file_in}" ]; then
        vmlinux_file=${vmlinux_file_in}
    fi
fi
if [ ! -e "${vmlinux_file}" ]; then
    echo "${vmlinux_file} not exists!!!!!!"
    exit
fi
echo ${vmlinux_file} is existed.
#------------------------------------------------------------------------------

###############################################################################
# Prepare VmCore file for crash
#------------------------------------------------------------------------------
vmcore_file=$2
if [ ! -e "${vmcore_file}" ]; then
    echo -n "VmCore path and filename?:"
    read vmcore_file_in
    if [ -n "${vmcore_file_in}" ]; then
        vmcore_file=${vmcore_file_in}
    fi
fi
if [ ! -e "${vmcore_file}" ]; then
    echo "${vmcore_file} not exists!!!!!!"
    exit
fi
echo ${vmcore_file} is existed.
#------------------------------------------------------------------------------

rm -f *.bin *.log *.cmd

echo "Extracting the kernel log from the crash dump..."
echo "log > kern.log" > extract_kern_log.cmd
echo "quit" >> extract_kern_log.cmd
eval ${CRASH_CMD} ${vmlinux_file} ${vmcore_file} -i extract_kern_log.cmd -s

echo "Extracting wlan firmware log from the crash dump..."

grep "\[FOR PARSING VmCore\] fw_rddm_dump" kern.log > firmware_dump.log;
grep "\[FOR PARSING VmCore\] fw_paging_dump" kern.log > fw_paging_dump.log;
grep "\[FOR PARSING VmCore\] remote_dump" kern.log > fw_remote_mem_dump.log

echo "Generate wlan firmware dumps start..."
echo "Generate wlan firmware remote dump..."
seg_addr=`grep "mem:" fw_remote_mem_dump.log|awk -F ": |," '{print $3}'`
seg_size=`grep "mem:" fw_remote_mem_dump.log|awk -F ": |," '{print $5}'`
echo "rd -x $seg_addr $seg_size -r ${fw_remote_mem_dump_file}" > fw_remote_mem_dump.cmd
echo "quit" >> fw_remote_mem_dump.cmd
eval ${CRASH_CMD} ${vmlinux_file} ${vmcore_file} -i fw_remote_mem_dump.cmd -s

echo "Generate wlan firmware sram dump..."
seg_addr=`grep "mem:" firmware_dump.log|awk -F ": |," '{print $3}'`
seg_size=`grep "mem:" firmware_dump.log|awk -F ": |," '{print $5}'`
echo "rd -x $seg_addr $seg_size -r ${fw_sram_file}" > firmware_dump.cmd
echo "quit" >> firmware_dump.cmd
eval ${CRASH_CMD} ${vmlinux_file} ${vmcore_file} -i firmware_dump.cmd -s

echo "Generate wlan firmware paging dump..."
seg_addr=`grep "mem:" fw_paging_dump.log|awk -F ": |," '{print $3}'`
seg_size=`grep "mem:" fw_paging_dump.log|awk -F ": |," '{print $5}'`
echo "rd -x $seg_addr $seg_size -r ${fw_paging_dump_file}" > fw_paging_dump.cmd
echo "quit" >> fw_paging_dump.cmd
eval ${CRASH_CMD} ${vmlinux_file} ${vmcore_file} -i fw_paging_dump.cmd -s

echo "Generate wlan firmware dumps done"

sram_parser ${fw_sram_file}

echo "clear tmp files"
rm -f tmp.bin *.log *.cmd