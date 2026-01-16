import sys
import math
import os
import traceback
from pathlib import Path 

def numerical_val(val_bytes, nBits, signVal):
    """
    Converts a byte object to an integer, handling endianness and signed values.
    val_bytes: Byte object (e.g., b'\x01\x02')
    nBits: Total number of bits for the value
    signVal: 'i' for signed, 'u' for unsigned
    """
    a = nBits // 8
    numVal = 0
    # Handle byte order
    if sys.byteorder == "little":
        for b in range(a):
            numVal = (numVal << 8) + val_bytes[a - 1 - b]
    else:  # Big-endian
        for b in range(a):
            numVal = (numVal << 8) + val_bytes[b]
    # Handle signed values
    if signVal == 'i' and numVal >= (1 << (nBits - 1)):
        return numVal - (1 << nBits)
    return numVal

def num_bytes(typeVal):
    """Determines the number of bytes based on the type string."""
    # Extract the last two characters of the type string as length identifier
    len_suffix = typeVal[-2:] if len(typeVal) >= 2 else ""
    len_map = {
        "t8": 1,
        "16": 2,
        "32": 4,
        "64": 8
    }
    return len_map.get(len_suffix, 1)  # Default to 1 byte

def process_files(bin_file_path, txt_file_path):
    """Main function to process file conversion, suitable for module calls."""
    try:
        # Use Path for path handling, improving cross-platform compatibility
        txt_path = Path(txt_file_path)
        bin_path = Path(bin_file_path)

        # Extract base filename (without extension)
        txt_base = txt_path.stem

        # Read template file
        with open(txt_path, "r", encoding='utf-8') as txt:
            txt_lines = txt.readlines()

        # Read binary file
        with open(bin_path, "rb") as f:
            data = f.read()  # Read all data at once for efficiency

        seek_val = 0
        i = 0
        total_lines = len(txt_lines)

        while i < total_lines:
            current_line = txt_lines[i].strip()
            if not current_line:  # Skip empty lines
                i += 1
                continue

            line_parts = current_line.split('\t')

            # Process bit fields (format like "NAME_X_Y")
            if len(line_parts[0]) >= 2 and line_parts[0][-2] == '_':
                # Check if there are enough bytes to read
                if seek_val >= len(data):
                    print(f"Warning: Offset {seek_val} exceeds file bounds, exiting loop.")
                    break
                current_byte = data[seek_val]
                s = 1
                processed_bits = 0
                while s:
                    # Prevent index out of bounds
                    if i >= total_lines:
                        break
                    current_line = txt_lines[i].strip()
                    line_parts = current_line.split('\t')

                    # Parse bit field definition
                    field_parts = line_parts[0].split('_')
                    if len(field_parts) < 3:
                        print(f"Error: Malformed bit field format '{line_parts[0]}'")
                        break
                    try:
                        start_bit = int(field_parts[-2])
                        width_bit = int(field_parts[-1])
                    except ValueError:
                        print(f"Error: Failed to parse bit field numerical values for '{line_parts[0]}'")
                        break
                    
                    # Extract bit field value
                    mask = (1 << width_bit) - 1
                    num = (current_byte >> start_bit) & mask

                    # Update line data
                    if len(line_parts) >= 3:
                        line_parts[2] = f" {num}" if num >= 0 else str(num)
                        txt_lines[i] = '\t'.join(line_parts)
                    
                    processed_bits += width_bit
                    if processed_bits >= 8:  # Finished processing one byte
                        s = 0
                        seek_val += 1  # Move to the next byte
                    i += 1  # Process the next line
            else:  # Process regular fields
                # Get the number of bytes required for this field
                r = num_bytes(line_parts[0])

                # Check if there are enough bytes
                if seek_val + r > len(data):
                    print(f"Warning: Field '{line_parts[0]}' has insufficient bytes, needs {r} bytes, remaining {len(data) - seek_val} bytes.")
                    break
                
                # Extract bytes and convert
                val_bytes = data[seek_val : seek_val + r]
                seek_val += r
                sign = line_parts[0][0] if line_parts[0] else 'u'
                try:
                    fin = numerical_val(val_bytes, r * 8, sign)
                except Exception as e:
                    print(f"Error processing field '{line_parts[0]}': {e}")
                    i += 1
                    continue
                
                # Update line data
                if len(line_parts) >= 3:
                    line_parts[2] = f" {fin}" if fin >= 0 else str(fin)
                    txt_lines[i] = '\t'.join(line_parts)
                i += 1

        # Write output file
        output_path = txt_path.parent / f"{txt_base}_new.txt"
        with open(output_path, "w", encoding='utf-8') as txt_new:
            for line in txt_lines:
                txt_new.write(f"{line} \n")
        return f"Generated {output_path} from {bin_path}"
    except FileNotFoundError as e:
        return f"File not found error: {e}"
    except Exception as e:
        return f"Processing error: {str(e)}\n{traceback.format_exc()}"

def main():
    if len(sys.argv) != 3:
        print("Usage: python RegDB_bin2txt.py <binary_file.bin> <template_file.txt>")
        sys.exit(1)
    script, bin_file, txt_file = sys.argv
    result = process_files(bin_file, txt_file)
    print(f"\n{result}")
    sys.exit(0)  

if __name__ == "__main__":
    main()
