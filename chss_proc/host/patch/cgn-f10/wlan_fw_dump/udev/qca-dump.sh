#!/bin/bash

# 1. save origin dump data
timestamp=$(date +%F_%H-%M-%S)
dev=${DEVPATH##*/}
tmpfile=/var/log/qca_dump_tmp_${dev}_${timestamp}.dump

# use this to avoid invoke dev_coredumpm free callback too early
exec 3</sys/${DEVPATH}/data

cat <&3 > ${tmpfile}
sync ${tmpfile}

offset=56  # the reason offset is fixed in the driver code's struct cnss_dump_file_data

function is_fw_dump() {
    local file_path="$tmpfile"  # File path passed as the first parameter
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

# 2. get dump reason
reason=$(is_fw_dump && get_fw_dump_reason || get_host_dump_reason)

# 3. rename dump according to dump reason
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
        mv ${tmpfile} /var/log/${new_file_name}_${dev}_${timestamp}.dump
        sync /var/log/${new_file_name}_${dev}_${timestamp}.dump
}

reason_to_name ${reason}

echo 1 > /sys/${DEVPATH}/data
# release and invoke free
exec 3<&-
