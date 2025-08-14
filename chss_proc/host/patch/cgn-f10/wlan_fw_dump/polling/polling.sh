#!/bin/bash
current_date=$(date +%F_%H-%M-%S)
interval=1
dir_for_store=/var/log
dir_to_check=/sys/devices/virtual/devcoredump

#get param
while getopts p:i:h opt
do
	case "${opt}" in
		p)
			dir_for_store=${OPTARG}
			;;
		i)
			interval=${OPTARG}
			if ! [[ $interval =~ ^[0-9]+$ ]]; then
				echo "-i $interval is not a number, interval invalid, exit"
				exit 1
			fi
			;;
		h)
			echo "-p set dump store path"
			echo "-i set polling interval, the interval time unit is second"
			exit 0
			;;
	esac
done

#check configuration
if [ ! -d ${dir_for_store} ]; then
	echo "$dir_for_store is invalid path, exit"
	exit 1
fi
dir_for_store=${dir_for_store%*/}
dir_to_check=${dir_to_check%*/}

echo "FW & HOST dump will be stored in $dir_for_store"
echo "Start periodic check $dir_to_check $current_date"

offset=56  # the reason offset is fixed in the driver code's struct cnss_dump_file_data

function is_fw_dump() {
    local file_path=$1  # File path passed as the first parameter
    local target_string="CNSS_FW_DUMP"  # The string to compare against

    # Check if the file exists
    if [[ ! -f "$file_path" ]]; then
        return 1  # False: File not found
    fi

    # Read the first few bytes of the file
    local file_bytes
    file_bytes=$(head -c ${#target_string} "$file_path")

    # Compare the bytes with the target string
    if [[ "$file_bytes" == "$target_string" ]]; then
        return 0  # True: Bytes match
    else
        return 1  # False: Bytes do not match
    fi
}

function get_fw_dump_reason() {
    local file_path="$tmpfile"  # The fixed file to check
    local byte_value
    local -A reason_dic  # Declare an associative array (reason_dic)

    # Initialize the reason_dic with key-value pairs (key is byte value at offset N)
    reason_dic=(
        [0]="FW_DEFAULT"  
        [2]="FW_RDDM"
        [3]="FW_TIMEOUT"
    )

    # Check if the file exists
    if [[ ! -f "$file_path" ]]; then
        echo "File not found."
        return 1
    fi

    # Read the byte value at the specified offset (using the global offset variable)
    byte_value=$(dd if="$file_path" bs=1 skip="$offset" count=1 2>/dev/null)
    decimal_val=$(printf '%d' "'$byte_value")

    # Get the reason_dic key (byte value) and print corresponding set of strings
    if [[ -n "${reason_dic["$decimal_val"]}" ]]; then
        # echo "Found key $hex_value: ${reason_dic["$decimal_val"]}"
        echo "${reason_dic["$decimal_val"]}"
    else
        # it maybe old format or new added dump reason type
        echo "FW_DEFAULT"
    fi

}

function get_host_dump_reason() {
## for now only one "HOST_DEFAULT" reason is reserver for host dump
        echo "HOST_DEFAULT"
}

function reason_to_name() {
        local -A name_dic
        local reason=$1
        local new_file_name

        name_dic=(
            ["FW_DEFAULT"]="qca_fw_dump"
            ["FW_RDDM"]="qca_fw_rddm_dump"
            ["FW_TIMEOUT"]="qca_fw_dump"
            ["HOST_DEFAULT"]="qca_host_dump"
)
    new_file_name="${name_dic[$reason]}"

        ## may need use cp instead of mv to avoid file sync issue
        mv $2 ${dir_for_store}/${new_file_name}_$3_${current_date}.dump
        sync ${dir_for_store}/${new_file_name}_$3_${current_date}.dump
}

while true;do
	if [ ! -d ${dir_to_check} ]; then
		sleep ${interval}
		continue
	fi

	for devcd_path in $(find $dir_to_check -type d -name "*devcd*"); do
		if [ -d ${devcd_path} ]; then
			current_date=$(date +%F_%H-%M-%S)
			echo "$devcd_path is created at $current_date"
			devcd_name=${devcd_path##*/}
			tmpfile=${dir_for_store}/qca_dump_tmp_${devcd_name}_${current_date}.dump
			cat ${devcd_path}/data > ${tmpfile}
			sync ${tmpfile}

            reason=$(is_fw_dump ${tmpfile} && get_fw_dump_reason || get_host_dump_reason)
            reason_to_name ${reason} ${tmpfile} ${devcd_name}

			echo 1 > ${devcd_path}/data
		fi
	done

	sleep ${interval}
done
