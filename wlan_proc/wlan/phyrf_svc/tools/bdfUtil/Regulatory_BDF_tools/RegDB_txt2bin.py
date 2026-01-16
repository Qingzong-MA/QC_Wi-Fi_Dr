
import sys
import struct
import math
from pathlib import Path
import traceback

class Txt2BinConverter:
    """Wrapper class for text to binary conversion, avoiding global variable issues."""
    def __init__(self):
        self.byte_count = 0
        self.check_sum = 0
        self.word_val = 0
        self.word_check = 0
        # Set default packing order based on system endianness
        self.order = '<' if sys.byteorder == "little" else '>'

    def checksum_cal(self, type_val, checksum_val, byte_size, num):
        """Method to calculate the checksum."""
        len_val = type_val[-2:] if len(type_val) >= 2 else ""
        res = num  # Default value

        # Handle signed values of different lengths
        len_mapping = {
            "t8": 8,
            "16": 16,
            "32": 32,
            "64": 64
        }
        if len_val in len_mapping and type_val[0] == 'i' and num < 0:
            res = (1 << len_mapping[len_val]) + num

        # Handle checksum logic
        if checksum_val == "checksum":
            self.byte_count += 2
            self.word_check = self.byte_count % 2 
            self.check_sum = (self.check_sum + 0) & 65535
        else:
            remaining_bytes = byte_size
            while remaining_bytes > 0:
                self.byte_count += 1
                self.word_check = self.byte_count % 2
                if self.word_check == 1:
                    self.word_val = res % 256
                else:
                    self.word_val |= (res % 256) * 256
                if self.word_check == 0:
                    self.check_sum ^= self.word_val
                res = res // 256  # Integer division
                remaining_bytes -= 1

    def num_bytes(self, type_val):
        """Determines the number of bytes for a given type."""
        if not type_val:
            return 1
        len_val = type_val[-2:] if len(type_val) >= 2 else ""
        if len_val == "t8" or (len(type_val) >= 2 and type_val[-2] == '_'):
            return 1
        elif len_val == "16":
            return 2
        elif len_val == "32":
            return 4
        elif len_val == "64":
            return 8
        return 1

    def data_type(self, type_val):
        """Determines the struct format character for the data type."""
        if not type_val:
            return 'b'  # Default type

        len_val = type_val[-2:] if len(type_val) >= 2 else ""
        # First character determines signedness ('i' for signed)
        sign_char = 'i' if type_val and type_val[0] == 'i' else 'u'
        
        type_map = {
            ("t8", 'i'): 'b',
            ("t8", 'u'): 'B',
            ("16", 'i'): 'h',
            ("16", 'u'): 'H',
            ("32", 'i'): 'l',
            ("32", 'u'): 'L',
            ("64", 'i'): 'q',
            ("64", 'u'): 'Q'
        }
        return type_map.get((len_val, sign_char), 'b')  # Default type

    def bit_pack(self, a, txt_lines):
        """Handles bit packing logic."""
        num = 0
        byt = 0 # Not used in current logic, consider removing if no longer needed
        current_a = a
        total_bits = 0

        while True:
            if current_a >= len(txt_lines):
                break
            line = txt_lines[current_a].strip()
            if not line:
                current_a += 1
                continue
            line_parts = line.split('\t')
            if len(line_parts) < 3:
                current_a += 1
                continue

            # Extract value
            if line_parts[2].startswith(' '):
                val_str = line_parts[2].split(' ')[1]
            else:
                val_str = line_parts[2]

            # Handle hexadecimal values
            if val_str.startswith("0x"):
                val = int(val_str, 0)
            else:
                try:
                    val = int(val_str)
                except ValueError:
                    val = 0  # Error handling: default value

            # Parse bit offset
            if len(line_parts[0]) >= 3:
                byte_offset = line_parts[0][-3:]
                try:
                    shift = int(byte_offset[0])
                    bits = int(byte_offset[2])
                except (ValueError, IndexError):
                    shift = 0
                    bits = 0
            else:
                shift = 0
                bits = 0
            
            # Bitwise operation
            num |= val * (2 ** shift)
            total_bits += bits
            current_a += 1

            # One byte processed
            if total_bits >= 8:
                break
        return current_a, num

    def convert(self, txt_file_path, bin_file_path):
        """Main conversion method."""
        try:
            # Reset state variables
            self.byte_count = 0
            self.check_sum = 0
            self.word_val = 0
            self.word_check = 0

            # Process paths
            txt_path = Path(txt_file_path)
            bin_path = Path(bin_file_path)

            # Read text file
            with open(txt_path, "r", encoding='utf-8') as txt:
                txt_lines = txt.readlines()

            # Write binary file
            with open(bin_path, "wb") as f:
                f.truncate(0)  # Clear file content

                seek_val = 0
                a = 0
                total_lines = len(txt_lines)

                while a < total_lines:
                    line = txt_lines[a].strip()
                    if not line:
                        a += 1
                        continue
                    line_parts = line.split('\t')
                    if len(line_parts) < 3:
                        a += 1
                        continue

                    # Extract numerical value
                    if line_parts[2].startswith(' '):
                        num_str = line_parts[2].split(' ')[1]
                    else:
                        num_str = line_parts[2]

                    # Handle hexadecimal and decimal values
                    try:
                        if num_str.startswith("0x"):
                            num = int(num_str, 0)
                        else:
                            num = int(num_str)
                    except ValueError:
                        print(f"Warning: Could not convert value '{num_str}', using default 0.")
                        num = 0

                    # Calculate offset and byte size
                    type_val = line_parts[0]
                    byte_size = self.num_bytes(type_val)

                    # Process bit fields
                    if len(type_val) >= 2 and type_val[-2] == '_':
                        a, packed_num = self.bit_pack(a, txt_lines)
                        f.seek(seek_val)
                        f.write(struct.pack(f"{self.order}B", packed_num))
                        self.checksum_cal("uint8", "WrongVal", 1, packed_num)
                        seek_val += 1
                    else:
                        # Process regular fields
                        data_fmt = self.data_type(type_val)
                        f.seek(seek_val)
                        f.write(struct.pack(f"{self.order}{data_fmt}", num))
                        # Calculate checksum
                        checksum_part = line_parts[1][-8:] if len(line_parts[1]) >=8 else ""
                        self.checksum_cal(type_val, checksum_part, byte_size, num)
                        seek_val += byte_size
                    a += 1

                # Calculate final checksum
                self.check_sum = 65535 ^ self.check_sum

                # Write checksum
                seek_val = 0
                a = 0
                while a < total_lines:
                    line = txt_lines[a].strip()
                    if not line:
                        a += 1
                        continue
                    line_parts = line.split('\t')
                    if len(line_parts) < 2:
                        a += 1
                        continue

                    # Find checksum field and write
                    if len(line_parts[1]) >= 8 and line_parts[1][-8:] == "checksum":
                        f.seek(seek_val)
                        f.write(struct.pack(f"{self.order}H", self.check_sum))
                        break
                    seek_val += self.num_bytes(line_parts[0])
                    a += 1
            return f"Generated {bin_path} from {txt_path}"
        except Exception as e:
            return f"Conversion error: {str(e)}\n{traceback.format_exc()}"

def main():
    """Command-line entry point."""
    if len(sys.argv) != 3:
        print("Usage: python RegDB_txt2bin.py <template_file.txt> <output_binary_file.bin>")
        sys.exit(1)
    _, txt_file, bin_file = sys.argv
    converter = Txt2BinConverter()
    result = converter.convert(txt_file, bin_file)
    print(f"\n{result}")
    sys.exit(0)

if __name__ == "__main__":
    main()
