#!/usr/bin/python
#===============================================================================
# NVM Utility Script
#===============================================================================
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# All rights reserved.
# Confidential and Proprietary - Qualcomm Technologies, Inc.
# 2017 by QUALCOMM Atheros, Incorporated.
#===============================================================================

import binascii
import os
import sys
from datetime import datetime
import re
import argparse
from lxml import etree as ET

Description = """
Description :
    This is a Utility Script used for converting or merging different NVM files. Output file extension will decide merging into bin/text file.
        - Converting NVM or NVMX to BIN format
        - Converting BIN to NVM format
        - Merges Multiple NVM files to Single NVM file(if tags are duplicated, further right file has precedence)
        - Merges Multiple NVMX files to Single NVMX file (if tags are duplicated, further right file has precedence)
        - Combines BT and FM NVM files and generates a Multi BIN file.
        - In all the cases it takes multiple input files of same type to generate a single Output file.
        - Working with NVMX files, needs corresponding TCFX file to be given as reference.
        - Converting Multi Bin file to Split nvm files as split_bt.nvm and split_fm.nvm from input.bin file.
        - Split single binary file into multiple binary files based on file type in the header. New files are generated as split_bt/fm_#.bin

Usage:
    %prog [--BT/FM] <input file list> [--TCF <input TCF files mandatory for NVMX operations>] -o <outputfilename.nvm/bin>

    BT single nvm->bin conversion
        %prog --BT input1.nvm -o output.bin
        %prog --BT input1.nvmx --TCF input2.tcfx -o output.bin

    BT single bin->nvm conversion
        %prog input1.bin -o output.nvm

    BT single bin-> multi bin conversion
        %prog --bin_split input.bin
        
    BT multiple nvm->bin conversion
        %prog --BT intput0.nvm input1.nvm [...] [-o output.bin]
        %prog --BT intput0.nvmx input1.nvmx [...] --TCF <input TCFX file> [-o output.bin]

    BT multiple bin->nvm conversion
        %prog intput0.bin input1.bin [...] [-o output.nvm]

    BT multiple nvm merge
        %prog intput0.nvm input1.nvm [...] [-o output.nvm]
        %prog --BT intput0.nvm input1.nvm [...] [-o output.nvm]
        %prog --BT intput0.nvmx input1.nvmx [...] --TCF <input TCFX file> [-o output.nvmx]

    BT&&FM bin merge
        %prog intput0.bin input1.bin [...] [-o output.bin]

    BT&&FM nvm->bin conversion
        %prog --BT intput0.nvm [...] --FM input0.nvm [...] [-o output.bin]
        %prog --BT intput0.nvmx [...] --FM input0.nvmx [...] --TCF <input TCFX file> [-o output.bin]

    BT&&FM nvm merge
        N/A

    BT&&FM bin->nvm conversion
        %prog -s input.bin

    BT or FM multiple nvm verify
        %prog --NVM input.nvm [...] --TCF input.tcf

"""

# script is upated to support for python 3.9 or higher version
PYTHON_VERSION = (3, 9)

# Debug flag to enable more log messages.
DEBUG_INFO_FLAG = 0

#binary file header size 
NVM_TLV_HEADER_SIZE = 4

# TLV values now handled as ints in bytearrays
# TLV Types to identify or parse the Bin Format.
NVM_TLV_VERSION_BT = 2      # if bin file only contains BT NVMs
NVM_TLV_VERSION_FM = 3      # if bin file only contains FM NVMs
NVM_TLV_VERSION_BTFM = 4    # if bin file contains multiple NVMs like BT and FM.

NVM_TLV_BIN_LEN_SIZE = 3    # Size of file length in bin file.
NVM_TLV_DATA_START = 4      # Position of TLV Data in bin file.
NVM_TLV_TAG = 2             # Size of Tag ID
NVM_TLV_LEN = 2             # Size of Tag Len
NVM_TLV_ZERO_PADDING = 8    # Size of Zero Padding for Tag Pointer (4 bytes) and Extended Flags (4 bytes)
NVM_HEADER = ''

# Data representation of bin file.
IsLittleEndian = True

# Is nvm type xml or text format.
IsCTM = False

# Create lists that stores whole bin file
list_input_bt = []
list_input_fm = []
bt_list_output = []
fm_list_output = []
input_files = []
output_file = ''

#Default file names for split operation.
output_split_files = ['split_bt.nvm', 'split_fm.nvm']

#Default output file used if not provided through the command argument.
DEFAULT_FILE_OUTPUT = 'merged_nvm_' + datetime.now().strftime('%H%M%S')

# Different Modes of operation performed by the tool.
MERGER_MODE = ''    # input files type decides the merger's mode, bin or nvm-text
BIN_MODE = 'bin'    # merge binary files of NVM
NVM_MODE = 'nvm'    # merge text files of NVM
TRANS_MODE = False  # output involves a bin->nvm/nvm->bin transfer
BTFM_MODE = False   # if input files has both BT and FM bin/nvm files
SPLIT_MODE = False  # Extract out BT and FM nvms from combined bin file
VERIFY_MODE = False # Verify NVM file against .TCF/.TCFX file

BT_CNT = 0 # BT NVM file counts
FM_CNT = 0 # FM NVM file counts
NVM_CNT = 0 # NVM file count
TCF_CNT = 0 # TCF file count
NVM_FILES = 'nvm'
TCF_FILES = 'tcf'

# Error Codes defined
EXIT_CODE_SUCCESS = 0
EXIT_CODE_INVALID_PARAM = 1
EXIT_NVM_CHECK_FAILED = 2
EXIT_CODE_FAILURE = -1

# NVMX
# class to represent NVMX Data
# TCFX file is mandatory to realize the size, type of the NVMX elements
# Loads the TCFX file and Parses the NVMX file to extract needed data
# Multiple NVMX files can be merged to be converted to NVMX
# NVMX file can be converted to BIN file
# Features to be added:
#   a. Multiple TCFX files to have Internal and External Tags seperately
#   b. Bin to NVMX format ( supported by CTM tool already )
#   c. Bin + NVMX ( with TCFX reference to the tags ) to be converted to resultant Bin
###########################################################################
# Generic Functions to be used in NVMX class
###########################################################################

# Exit on Failure with error message
def EXIT_ON_FAILURE(msg):
    msg = msg + '''\n\tIf you have edited TAGS in TCFX file and the elements are not
        updated in NVMX files, please use : Parse Tags to bring NVMX files aligned with
        the updates done in TCFX file.\n\t
        python parse_tags.py <Input TCFX file> --merge=<single nvmx file or folder\*.nvmx> --alignToTCFX'''
    print(msg)
    exit(EXIT_CODE_FAILURE)

# Print the values if top level DEBUG_INFO_FLAG is enabled
def debug_print(msg):
    if DEBUG_INFO_FLAG:
        print(msg)

# Returns List of BYTES
def hex_format(number, size):
    #For BIT Field the size is represented as zero, consider it as 1
    if size == "0":
        size = 1
    size = int(size)
    number = number.lstrip("0x").zfill(size * 2).replace("L", "")

    output = []
    for i in range(0, len(number), 2):
        output.append ( number[i:i+2] )

    if IsLittleEndian:
        output.reverse()

    return output

class NVMX:
    def __init__ (self, TCFX_File, NVMX_File):
        tcfx = ET.parse ( TCFX_File ).getroot()
        self.tcfx_tags = tcfx.find("TAGS")

        #Needed for merge
        self.nvmxobj = ET.parse ( NVMX_File )

        self.nvmx = self.nvmxobj.getroot()

        self.nvmx_tags = self.nvmx.find("TAGS")

        #This should be for BIN format , should see for Merger
        self.tag_dict = {}

    ##########################################################################
    # Return the TCFX tag which is aligned with NVMX Tag
    ##########################################################################
    def getTCFXtag (self, name, ExitOnFailure = True):
        for tcfx_tag in self.tcfx_tags:
            if tcfx_tag.get("Name") == name:
                return tcfx_tag
        if ExitOnFailure:
            EXIT_ON_FAILURE("{0} tag is not found in TCFX file".format (name))

    ##########################################################################
    # Return the Total size of the TCFX tag which is present at the first child
    ##########################################################################
    def get_tagsize(self, tcfx_tag):
        element = tcfx_tag.find("ELEMENTS")

        if element == None:
            EXIT_ON_FAILURE("Malformed TCFX with no ELEMENTS")

        size = element.get("Size")
        if not size:
            EXIT_ON_FAILURE("Malformed TCFX ELEMENTS has no SIZE")

        return size

    ##########################################################################
    #Convert BIT Field into Bytes
    ##########################################################################
    def bits2hex (self, nvmx, tcfx):
        tag_size    = int(tcfx.get("Size"))
        total_bits  = (tag_size * 8) - 1
        highestBit  = 0
        FinalValue  = 0

        nvmx_elements = nvmx.findall("ELEMENTS")
        tcfx_elements = tcfx.findall("ELEMENTS")

        if len(nvmx_elements) != len(tcfx_elements):
                EXIT_ON_FAILURE("TAG : {0} BIT FIELD {1} is not aligned with tcfx".format(self.tagname, tcfx.get("Name")))

        for i in range(len(nvmx_elements)):
            if nvmx_elements[i].get("Name") != tcfx_elements[i].get("Name"):
                EXIT_ON_FAILURE("TAG : {0} BIT FIELD {1} is not aligned with tcfx".format(self.tagName, tcfx_elements[i].get("Name")))

            start_bit   = int(tcfx_elements[i].get("Start"))
            end_bit     = int(tcfx_elements[i].get("End"))

            bitElem = int(nvmx_elements[i].get("Value"), 16)

            FinalValue  |= (bitElem << start_bit)

            highestBit  = end_bit

            if highestBit > total_bits:
                EXIT_ON_FAILURE("TAG : {0} BIT FIELD {1} exceeded upper bound : {2} bits".format(self.tagname, tcfx_elements[i].get("Name"), total_bits))

        hex_num = hex(FinalValue)

        return hex(FinalValue)

    ##########################################################################
    # Recursive function to fetch the NVM tag elements , and their values
    # For now we can do the length check at the end, probably we can start
    # to check if the tag names being used in TCFX are aligned with NVMX or not
    ##########################################################################
    def arrangevalues (self, nvmx , tcfx, fixedarraysize=None):
        if nvmx.get("Name") != tcfx.get("Name") and self.tag_dict[self.tagnum]['hasVarArray'] != True:
            EXIT_ON_FAILURE("28 : NVMX is not aligned with TCFX file : {0} | {1}".format (nvmx.get("Name"), tcfx.get("Name")))

        #Handle BITFIELD to generate HEX value , no recursion involved
        if tcfx.get("Type") == 'BITFIELD':
            self.calc_tagsize += int(tcfx.get("Size"))
            value = self.bits2hex (nvmx, tcfx)
            self.tag_dict[self.tagnum]['Value'] += hex_format(value, tcfx.get("Size"))
        ###############################################################

        #For other TAG ELEMENT types
        else:
            nvmx_elements = nvmx.findall("ELEMENTS")
            tcfx_elements = tcfx.findall("ELEMENTS")

            # For Fixed Array individual elements won't have Size Field.
            if tcfx.get("Type") == "FIXED_ARRAY":
                fixedarraysize = tcfx.get("ElementSize")

            #TCFX is expected to have only one TYPE element and is to be replicated
            #the number of elements size. Needs further review.
            if tcfx.get("Type") == "VARIABLE_ARRAY":
                self.tag_dict[self.tagnum]['hasVarArray'] = True

                no_elements = len(nvmx_elements)

                # Only for Variable Array, we need to find the number of underlying elements
                # The size of Elements is defined as VariableSize in TCFX
                self.tag_dict[self.tagnum]['Value'] += hex_format(hex(no_elements), tcfx.get("VariableSize"))

                #Contributes to the size of number of elements
                self.calc_tagsize += int(tcfx.get("VariableSize"))

                debug_print("{0} {1} {2}".format(nvmx.get("Name").ljust(60), tcfx.get("VariableSize").ljust(10), hex(no_elements)))

                for i in range(no_elements - 1):
                    tcfx_elements.append(tcfx_elements[0])

            if tcfx.get("Type") != "ENUM" and len(nvmx_elements) != len(tcfx_elements):
                    EXIT_ON_FAILURE("34 : NVMX is not aligned with TCFX file -- {0}".format (nvmx.get("Name")))

            # Recursive function to get the Values accordingly.
            for i in range(len(nvmx_elements)):
                self.arrangevalues(nvmx_elements[i],tcfx_elements[i], fixedarraysize)

            # Older revisions of CTM tool added value attribute at top level for Fixed Array, which is not intended.
            # Adding a check to skip such values during NVMX operations.
            if "Value" in nvmx.attrib and tcfx.get("Type") not in ["VARIABLE_ARRAY", "FIXED_ARRAY", "STRUCT_ARRAY", "STRUCTURE"]:
                if fixedarraysize:
                    debug_print("{0} {1} {2} *".format(nvmx.get("Name").ljust(60), str(fixedarraysize).ljust(10), nvmx.get("Value")))
                    val = hex_format(nvmx.get("Value"), fixedarraysize)
                    self.calc_tagsize += int(fixedarraysize)
                    self.tag_dict[self.tagnum]['Value'] += val
                else:
                    debug_print("{0} {1} {2}".format(nvmx.get("Name").ljust(60), tcfx.get("Size").ljust(10), nvmx.get("Value")))
                    self.calc_tagsize += int(tcfx.get("Size"))
                    self.tag_dict[self.tagnum]['Value'] += hex_format(nvmx.get("Value"), tcfx.get("Size"))
            else:
                debug_print("The value is not proper : {0}".format(nvmx.get("Name")))

    ##########################################################################
    # Get the values of each tag, generate a dictionary accordingly
    ##########################################################################
    def get_nvm_values(self):
        for nvmx_tag in self.nvmx_tags:

            tcfx_tag = self.getTCFXtag (nvmx_tag.get("Name"))

            self.tagnum = int(tcfx_tag.get("Number"))

            self.tagname        = tcfx_tag.get("Name")
            self.tagsize        = self.get_tagsize (tcfx_tag)
            self.calc_tagsize   = 0

            debug_print("{0} {1}".format (self.tagname.ljust(71), self.tagnum))
            debug_print("Tag overall size {0}".format (self.tagsize.rjust(59)))

            self.tag_dict[self.tagnum] = { 'tagName':       self.tagname,
                                            'Size':         self.tagsize,
                                            'hasVarArray':  False,
                                            'Value':        [],
                                            'calc_tagsize': 0,
                                            'node':         nvmx_tag
                                        }

            self.arrangevalues(nvmx_tag.find("ELEMENTS"), tcfx_tag.find("ELEMENTS"))
            self.tag_dict[self.tagnum]['calc_tagsize'] = self.calc_tagsize
            debug_print("\n")
            debug_print((" ").join(self.tag_dict[self.tagnum]['Value']))
            debug_print("="*20)
            debug_print("\n")

    ##########################################################################
    # Write the Found NVM values into Binary as per pre - defined format
    ##########################################################################
    def validatenvmx(self):
        self.get_nvm_values ()

    ##########################################################################
    # Write the Found NVM values into Binary as per pre - defined format
    ##########################################################################
    def write2bin(self, BinType, filename):
        global BUILD_LABEL

        bin_size = 0

        if BUILD_LABEL and self.getTCFXtag ("BUILD_LABEL", False) is not None:
            BuildLabelTag = self.getTCFXtag ("BUILD_LABEL")

            self.tag_dict[int(BuildLabelTag.get("Number"))] = { 'tagName':      "BUILD_LABEL",
                                                                'Size':         self.get_tagsize (BuildLabelTag),
                                                                'hasVarArray':  False,
                                                                'Value':        BUILD_LABEL,
                                                                'calc_tagsize': int(self.get_tagsize (BuildLabelTag)),
                                                                'node':         None
                                                            }

        with open(filename, 'wb') as fp:
            fp.write(bytearray([BinType])) #Default Type of NVM Binary is 0x02

            #Reserved bytes, later will be replaced by actual size
            fp.write(binascii.a2b_hex('00'))
            fp.write(binascii.a2b_hex('00'))
            fp.write(binascii.a2b_hex('00'))

            tags = list(self.tag_dict.keys())
            tags.sort()
            for tagnum in tags:
                byte_stream = []

                #Tag number converted to Hex
                byte_stream += hex_format(hex(tagnum), NVM_TLV_TAG)
                #Size of the tag converted to Hex
                byte_stream += hex_format(hex(self.tag_dict[tagnum]['calc_tagsize']), NVM_TLV_TAG)
                #Append bytes which correspond to flags in bin
                byte_stream += ['00'] * NVM_TLV_ZERO_PADDING
                #Append the value stream
                byte_stream += self.tag_dict[tagnum]['Value']

                if DEBUG_INFO_FLAG >= 1: print (byte_stream)
                for byte in byte_stream:
                    fp.write(binascii.a2b_hex(byte))

                bin_size += len(byte_stream)

            #Replacing the reserved Bytes
            fp.seek(1, 0)
            bin_size_bytes = hex_format(hex(bin_size), NVM_TLV_BIN_LEN_SIZE)
            for byte in bin_size_bytes:
                fp.write(binascii.a2b_hex(byte))

            fp.close()

##########################################################################
# Convert NVMX to Binary Files
##########################################################################
def nvmx2bin(BinType, TCFXFile, NVMXFile, BinFile):
    obj = NVMX (TCFXFile[0], NVMXFile[0]) #Currently doing only for 1 file
    obj.get_nvm_values()
    obj.write2bin(BinType, BinFile)

##########################################################################
# Generate NVMX File from Dictionary
##########################################################################
def write2nvmx(out_file, outputFile):
    NVMX = ET.Element("NVM")

    format_version = ET.SubElement( NVMX, "FORMAT_VERSION")
    format_version.text = '1.0'

    ChangeSummary = ET.SubElement ( NVMX, "ChangeSummary" )
    ChangeSummary.text = "Merged File from NvmUtility"

    TAG_ROOT = ET.SubElement(NVMX, "TAGS")

    tags = list(out_file.tag_dict.keys())
    tags.sort()

    for tag in tags:
        TAG_ROOT.append(out_file.tag_dict[tag]['node'])

    NVMXText = ET.tostring(NVMX, pretty_print=True, encoding='utf-8', method="xml", xml_declaration=True)
    # Making this inline with CTM tool
    NVMXText = NVMXText.replace(bytearray("<TAGS><TAG", 'utf-8'), bytearray("<TAGS>\n    <TAG", 'utf-8'))
    # Adding Space to end of the ELEMENTS to make it inline with CTM tool
    NVMXText = NVMXText.replace(bytearray("/>", "utf-8"), bytearray(" />", "utf-8"))

    NVMXfile = open(outputFile, "wb")
    NVMXfile.write(NVMXText)
    NVMXfile.close()

##########################################################################
# Merge NVMX Files to generate Single Output NVMX File
##########################################################################
def mergenvmx(TCFXFile, ListOfNVMXFiles, OutputNVMXFile):
    ListofNVMObjs = []

    for file in ListOfNVMXFiles:
        nvmx_obj = NVMX (TCFXFile[0], file)
        nvmx_obj.validatenvmx()

        #Capture all NVMX file Roots as objects
        ListofNVMObjs.append(nvmx_obj)

    #Select the fist file as Out and merge the tags from next files to this
    out_file = ListofNVMObjs[0]

    for in_file in ListofNVMObjs[1:]:
        tags = in_file.tag_dict.keys()
        for tag in tags:
            out_file.tag_dict[tag] = in_file.tag_dict[tag]

    write2nvmx(out_file , OutputNVMXFile)



# NVMTag #
# class to represent NVM tag
# TagIndex: Tag0, Tag1, ...
# TagNum: integer representation of Tag #
# TagNumLSB: bin representation of Tag #
# TagNumMSB: bin representation of Tag #
# TagLength: integer representation of Tag length
# TagLengthLSB: bin representation of Tag length
# TagLengthMSB: bin representation of Tag length
# TagValue:
# binary mode represented by a list of bin values
# text mode represented by a list of str, only first element used
class NVMTag:
    def __init__(self, TIDX, TNL=None, TNB=None, TLL=None, TLM=None, TagNum=0, TagLength=0):
        self.TagIndex = TIDX
        self.TagValue = []
        self.TagNum = TagNum
        self.TagLength = TagLength
        if TNL is not None and TNB is not None and TLL is not None and TLM is not None:
            # BIN_MODE only attributes
            self.TagNumLSB = TNL
            self.TagNumMSB = TNB
            self.TagLengthLSB = TLL
            self.TagLengthMSB = TLM
        else:
            self.TagNumLSB = binascii.a2b_hex(hex((self.TagNum % 256)).lstrip('0x').zfill(2))
            self.TagNumMSB = binascii.a2b_hex(hex((self.TagNum // 256)).lstrip('0x').zfill(2))
            self.TagLengthLSB = binascii.a2b_hex(hex((self.TagLength % 256)).lstrip('0x').zfill(2))
            self.TagLengthMSB = binascii.a2b_hex(hex((self.TagLength // 256)).lstrip('0x').zfill(2))


    def inputval(self, finput=None, valstr=None, index=None):
        if MERGER_MODE == BIN_MODE:
           
            if not isinstance(self.TagLengthLSB, bytes):
                iLSB = int(binascii.b2a_hex(self.TagLengthLSB.to_bytes(1, 'big')), 16)
            else:
                iLSB = int(binascii.b2a_hex(self.TagLengthLSB), 16)
            
            if not isinstance(self.TagLengthMSB, bytes):
                iMSB = int(binascii.b2a_hex(self.TagLengthMSB.to_bytes(1, 'big')), 16)
            else:
                iMSB = int(binascii.b2a_hex(self.TagLengthMSB), 16)
                
            self.TagLength = iLSB + iMSB*16*16
            
            if not isinstance(self.TagNumLSB, bytes):
                nLSB = int(binascii.b2a_hex(self.TagNumLSB.to_bytes(1, 'big')), 16)
            else:
                nLSB = int(binascii.b2a_hex(self.TagNumLSB), 16)
            
            if not isinstance(self.TagNumMSB, bytes):
                nMSB = int(binascii.b2a_hex(self.TagNumMSB.to_bytes(1, 'big')), 16)
            else:
                nMSB = int(binascii.b2a_hex(self.TagNumMSB), 16)
                
            self.TagNum = nLSB + nMSB*16*16

            if index is None:
                for i in range(self.TagLength):
                    # use file I/O to read
                    x = finput.read(1)
                    self.TagValue.append(x)
            else:
                for i in range(index, index+self.TagLength):
                    self.TagValue.append(finput[i])

        elif MERGER_MODE == NVM_MODE and valstr is not None:
            valist = valstr.split('=')
            self.TagValue.append(valist[1])
        else:
            if DEBUG_INFO_FLAG >= 1: print('\n\tNo TagValue inserted\n')


    def printall(self):
        print('/' * 10)
        print('TagNum: %d' %self.TagNum)
        if MERGER_MODE == BIN_MODE:
            print(binascii.b2a_hex(self.TagNumLSB).upper())
            print(binascii.b2a_hex(self.TagNumMSB).upper())
            print(binascii.b2a_hex(self.TagLengthLSB).upper())
            print(binascii.b2a_hex(self.TagLengthMSB).upper())
            for i in range(self.TagLength):
                print(binascii.b2a_hex(self.TagValue[i]).upper())
        if MERGER_MODE == NVM_MODE:
            print(self.TagLength)
            print(self.TagValue[0])
        print('\\' * 10)

# vararg_cb #
# callback to support variable argument in optparse
def vararg_cb(opt, opt_str, val, parser):
    assert val is None
    val = []
    #print '#option'
    #print opt.dest
    #print '#option string'
    #print opt_str
    #print parser.rargs

    for arg in parser.rargs:
        if arg[:2] == "--" and len(arg) > 2:
            #print arg
            break
        if arg[:1] == "-" and len(arg) > 1:
            break
        val.append(arg)

    del parser.rargs[:len(val)]
    setattr(parser.values, opt.dest, val)

def isCTMMode (files):
    global IsCTM
    for file in files:
        if file.endswith('.nvmx'):
            IsCTM = True
        elif IsCTM and not file.endswith('.nvmx'):
            EXIT_ON_FAILURE("Mixed File formats, is not supported.")

    return IsCTM

def split_binary_file(input_file):
    '''
    This method reads a binary file with a specific header format and splits it into multiple binary files based on embedded sub-headers.
    Iteratively reads each sub-header (4 bytes), extracts the file type and content length, and writes the corresponding content to a new binary file.
    Supports file types 2 (saved as bt) and 3 (saved as fm).
    '''
  
    with open(input_file, 'rb') as f:
        # read the first 4 bytes (global header )
        header = f.read(NVM_TLV_HEADER_SIZE)
      
        file_type = header[0]
        file_size = int.from_bytes(header[1:][::-1], 'big')
        print("Total file size", file_size + NVM_TLV_HEADER_SIZE)
        if file_type != NVM_TLV_VERSION_BTFM :
            print("The given binary file cannot be split into multiple binary files because it contains only a single header")
            sys.exit()
        
        index = 0
        while True:
            # Read the next 4 bytes for the header
            sub_header = f.read(NVM_TLV_HEADER_SIZE)
            if len(sub_header) < NVM_TLV_HEADER_SIZE:
                break  # End of file

            file_type = sub_header[0]
            if file_type == NVM_TLV_VERSION_BT:
                file_type = 'bt'
            elif file_type == NVM_TLV_VERSION_FM:
                file_type = 'fm'
            
            file_length = int.from_bytes(sub_header[1:][::-1],'big')
            #Read the content of the specified length
            content = f.read(file_length)
            if len(content) < file_length:
                print("Incomplete content for file {0}, expected {1} bytes.".format(index, file_length))
                sys.exit(1)

            # Write to a new binary file
            output_filename = "split_{0}_{1}.bin".format(file_type, index)
            with open(output_filename, 'wb') as out_file:
                out_file.write(sub_header)
                out_file.write(content)

            print("Created {0} with {1} bytes.".format(output_filename, file_length))
            index += 1
    sys.exit()

# optParser #
# command-line input processor
def optParser():
    global input_files, output_file, BUILD_LABEL
    global BTFM_MODE, MERGER_MODE, SPLIT_MODE, BT_CNT, FM_CNT
    global VERIFY_MODE, NVM_CNT, TCF_CNT
    global IsCTM

    # Get current version
    major = sys.version_info.major
    minor = sys.version_info.minor
    micro = sys.version_info.micro

    if (major, minor) < PYTHON_VERSION:
        print("your current Python version: {}.{}.{}".format(major, minor, micro))
        print("Your Python version is lower than 3.9.")
        print("Please upgrade to Python 3.9 or higher for better compatibility and features.")
        sys.exit(1)

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description = Description)
    parser.add_argument('input_files', nargs='*', help='NVM bin/text files to merge')
    parser.add_argument('-o', '--output', metavar='output_file', type=str, help='NVM bin/text output file name after merger')
    # for BTFM_MODE text-based merge
    parser.add_argument('--BT', metavar='BT.nvm', nargs='*', help='BT NVM text-based input files')
    parser.add_argument('--FM', metavar='FM.nvm', nargs='*', help='FM NVM text-based input files')
    parser.add_argument('-s', action='store_true', help='To enable split mode')
    parser.add_argument('--bin_split', metavar='input.bin', type=str, help='Path to the binary file to be split')
    parser.add_argument('--NVM', metavar='input.nvm', nargs='*', help='NVM text-based input file to verify')
    parser.add_argument('--TCF', metavar='input.tcf', nargs='*', help='TCF text-based input file used to verify')
    parser.add_argument('--BUILD_LABEL', metavar='BUILD_LABEL', type=str, help='Build Label String to be converted to template NVMX', default=None)

    args = parser.parse_args()
    input_files = args.input_files
    output_file = args.output
    SPLIT_MODE = args.s

    if args.bin_split:
       try:
          split_binary_file(args.bin_split.strip())
       except Exception as e:
           print("Error splitting binary input file {0}: {1}".format(args.bin_split, e))
           sys.exit(1)
           
    if args.BUILD_LABEL:
        BUILD_LABEL = args.BUILD_LABEL
    elif os.getenv('BUILD_LABEL', None):
        BUILD_LABEL = os.getenv('BUILD_LABEL')
    else:
        BUILD_LABEL = None

    if input_files:
        isCTMMode(input_files)
    if args.BT:
        isCTMMode(args.BT)
    if args.FM:
        isCTMMode(args.FM)

    if len(input_files) == 0:  # imply non-binary mode, otherwise simply using positional argument
        if not IsCTM and (args.NVM is not None or args.TCF is not None):
            if args.NVM is None:
                if DEBUG_INFO_FLAG >= 1: print('\tNo NVM input file to verify')
                exit(EXIT_CODE_INVALID_PARAM)
            if args.TCF is None:
                if DEBUG_INFO_FLAG >= 1: print('\tNo TCF input file to verify against')
                exit(EXIT_CODE_INVALID_PARAM)
            VERIFY_MODE = True
            NVM_CNT = len(args.NVM)
            TCF_CNT = len(args.TCF)
            if TCF_CNT != 1:
                if DEBUG_INFO_FLAG >= 1: print('\tPlease supply one, and only one, TCF file')
                exit(EXIT_CODE_INVALID_PARAM)
            input_files = [NVM_FILES, args.NVM, TCF_FILES, args.TCF]
        else:
            # imply NVM_MODE, otherwise simply using positional argument
            MERGER_MODE = NVM_MODE
            if SPLIT_MODE:
                if DEBUG_INFO_FLAG >= 1: print('\tNo input file to split')
                exit(EXIT_CODE_INVALID_PARAM)
            if args.BT is not None and args.FM is not None:
                BT_CNT = len(args.BT)
                FM_CNT = len(args.FM)
                input_files = [NVM_TLV_VERSION_BT, args.BT, NVM_TLV_VERSION_FM, args.FM]
                BTFM_MODE = True
            elif args.BT is not None:
                BT_CNT = len(args.BT)
                input_files = [NVM_TLV_VERSION_BT, args.BT]
                if IsCTM and args.TCF is None:
                   if DEBUG_INFO_FLAG >= 1: print('\nTCFX file is mandatory for NVMX files.')
                   exit(EXIT_CODE_INVALID_PARAM)
                elif IsCTM:
                    input_files.append(args.TCF)
            elif args.FM is not None:
                FM_CNT = len(args.FM)
                input_files = [NVM_TLV_VERSION_FM, args.FM]
                if IsCTM and args.TCF is None:
                   if DEBUG_INFO_FLAG >= 1: print('\nTCFX file is mandatory for NVMX files.')
                   exit(EXIT_CODE_INVALID_PARAM)
                elif IsCTM:
                    input_files.append(args.TCF)
            else:
                parser.print_help()
                if DEBUG_INFO_FLAG >= 1: print('\n\tNo input files\t\n')
                exit(EXIT_CODE_INVALID_PARAM)
    else:
        if args.BT is not None or args.FM is not None:
            parser.print_help()
            if DEBUG_INFO_FLAG >= 1: print('\nFor BTFM-NVM merge:')
            if DEBUG_INFO_FLAG >= 1: print('\tPlease append all BT-NVM text file after --BT, all FM-NVM text file after --FM')
            exit(EXIT_CODE_INVALID_PARAM)

    if BUILD_LABEL is not None:
        #Stripping BUILD_LABEL to be max. 64 characters which is allowed in Firmware
        BUILD_LABEL = BUILD_LABEL[:64]
        ascii_values = []
        for character in BUILD_LABEL:
            ascii_values.append(hex(ord(character)).lstrip("0x").upper())
        BUILD_LABEL = ascii_values + ["00"] * (64 - len(ascii_values))
        if DEBUG_INFO_FLAG >= 1: print("Modified BUILD_LABEL", BUILD_LABEL)

    if SPLIT_MODE:
        if output_file is not None:
            if DEBUG_INFO_FLAG >= 1: print('\n\tNo need to specify output file name for split mode. Exit\n')
            exit(EXIT_CODE_INVALID_PARAM)
    else:
        if len(input_files) == 1 and output_file is None :
            if DEBUG_INFO_FLAG >= 1: print('\n\tNothing to be done. Exit\n')
            exit(EXIT_CODE_INVALID_PARAM)
        elif BT_CNT == 1 and FM_CNT == 0 and output_file is None :
            if DEBUG_INFO_FLAG >= 1: print('\n\tNothing to be done. Exit\n')
            exit(EXIT_CODE_INVALID_PARAM)
        elif BT_CNT == 0 and FM_CNT == 1 and output_file is None :
            if DEBUG_INFO_FLAG >= 1: print('\n\tNothing to be done. Exit\n')
            exit(EXIT_CODE_INVALID_PARAM)
        elif output_file is None:
            #print 'use default name'
            #considering the default out format is bin.
            output_file = DEFAULT_FILE_OUTPUT + '.bin'

# Reads information related to a supplied TCF file and returns a dictionary
# containing the tag number and associated information.
## input: filename of TCF to read ##
## return: dictionary object containing tag numbers as keys, and various qualities as values ##
## Note: Only 'TagLength' and 'UseDynMem' are currently supported. Augment as needed
def readTcfInfo(tcfFileName):
    tcfDict = {}
    fileNumOfTags = -1
    tagNum = -1
    tagLength = -1
    UseDynMem = -1
    if DEBUG_INFO_FLAG >= 1: print("TCF file = '" + tcfFileName + "'")

    # The TCF fields we're interested in have the following format in the TCF file:
    # [Tags56]
    # Number = 95
    # Name = Bluetooth Local Features Control
    # ...
    # UseDynMem = 0
    # ...
    # [Tags56_Type3]
    # Name = BT local features control
    # TagLength = 120

    try:
        with open(tcfFileName, 'r') as f:
            for line in f:
                if line.startswith('[Tags]'):
                    fileNumOfTags = int(next(f).strip('Num = '), 10)
                elif line.startswith('Number = '):
                    tagNum = int(line.strip('Number = '),10)
                    # A new tag is found, invalidate tag qualities
                    tagLength = -1
                    UseDynMem = -1
                elif line.startswith('UseDynMem = '):
                    UseDynMem = int(line.strip('UseDynMem = '),10)
                elif line.startswith('TagLength = '):
                    # TagLength is used to describe the overall tag as well as
                    # individual elements.  For simplicity sake, just grab the
                    # first length after the tag number.
                    if tagNum >= 0:
                        tagLength = int(line.strip('TagLength = '), 10)
                        tcfDict[tagNum] ={}
                        tcfDict[tagNum]['TagLength'] = tagLength
                        tcfDict[tagNum]['UseDynMem'] = UseDynMem
                        tagNum = -1
                        UseDynMem = -1
            f.close()

        if fileNumOfTags <= 0:
            if DEBUG_INFO_FLAG >= 1: print('\n\t' + tcfFileName + ' has improper TCF text format, exit...\n')
            return None
    except ValueError:
        if DEBUG_INFO_FLAG >= 1: print('\n\tFiles have improper TCF text format, exit...1\n')
        return None
    except IOError:
        if DEBUG_INFO_FLAG >= 1: print('\n\t' + tcfFileName + ' does not exist, exit...\n')
        return None

    return tcfDict

# Based on the file list that contains a series of NVM files and one TCF file,
# this function will parse the TCF file to extract the lengths, and then parse
# each NVM file and ensure the lengths match.
## input: list of NVM and TCF files ##
## return: True is there are no length mismatches in the NVMs, False otherwise ##
def doesNvmMatchTcf(nvmTcfFileList):
    nvmList = []
    tcfList = []
    tcfDict = {}
    retStatus = True
    if NVM_CNT > 0 and TCF_CNT > 0:
        # Make two lists with our input NVM and TCF files
        ptr = iter(nvmTcfFileList)
        for i in ptr:
            if i == NVM_FILES:
                tmp = next(ptr)
                nvmList += tmp
            if i == TCF_FILES:
                tmp = next(ptr)
                tcfList += tmp

        # There should be one, and only one, TCF file provided. Read the tag
        # information into a dictionary for quick look up.
        tcfDict = readTcfInfo(tcfList[0])

        # Verify we got a valid dictionary containing the TCF info
        if tcfDict == None or len(tcfDict) == 0:
            return False

        # For each NVM file provided, check the tag lengths against the supplied TCF file
        for nvmFileName in nvmList:
            if DEBUG_INFO_FLAG >= 1: print("NVM file = '" + nvmFileName + "'")
            fileNumOfTags = -1
            nvmIsValid = True

            # NVM file format:
            # [Tag]
            # Num = 8
            #
            # [Tag0]
            # TagNum = 17
            # TagLength = 6
            # TagValue = 01 02 03 ...
            try:
                with open(nvmFileName, 'r') as f:
                    for line in f:
                        if '[Tag]' in line:
                            fileNumOfTags = int(next(f).strip('Num ='), 10)

                        elif 'TagNum =' in line:
                            tagNum = -1
                            tagLength = -1
                            tagNum = int(line.strip('TagNum ='), 10)
                            tagLength = int(next(f).strip('TagLength ='), 10)

                            # Make sure we actually read a tag/length from the NVM
                            if tagNum < 0 or tagLength < 0:
                                if DEBUG_INFO_FLAG >= 1: print('\n\tFiles have improper NVM text format, exit...\n')
                                nvmIsValid = False
                                break

                            # Make sure the tag number actually exists in the TCF
                            elif tcfDict.get(tagNum) == None:
                                print("\n\tNVM tag #" + str(tagNum) + " in '" + nvmFileName + "' does not exists in " + tcfList[0] + ", exit...\n")
                                nvmIsValid = False

                            # Ensure the tag length in the NVM matches the tag length in the TCF
                            elif tcfDict[tagNum]['UseDynMem'] == 0 and tagLength != tcfDict[tagNum]['TagLength']:
                                print("\n\tNVM tag #" + str(tagNum) + "'s length (" + str(tagLength) + \
                                      ") in '" + nvmFileName + "' does not match the expected TCF length (" \
                                    + str(tcfDict[tagNum]['TagLength']) + ") in " + tcfList[0] + ", exit...\n")
                                nvmIsValid = False

                    if nvmIsValid == True:
                        if DEBUG_INFO_FLAG >= 1: print("NVM file has no errors")
                    else:
                        if DEBUG_INFO_FLAG >= 1: print("NVM file has errors!!!")
                        retStatus = False
                    f.close()

                if fileNumOfTags <= 0:
                    if DEBUG_INFO_FLAG >= 1: print('\n\t' + nvmFileName + ' has improper NVM text format, exit...\n')
                    return False
            except ValueError:
                if DEBUG_INFO_FLAG >= 1: print('\n\tFiles have improper NVM text format, exit...\n')
                return False
            except IOError:
                if DEBUG_INFO_FLAG >= 1: print('\n\t' + nvmFileName + ' does not exist, exit...\n')
                return False

    fnamelist = []
    return retStatus

def CheckIfBinFiles(Files):
    AreBinFiles = True
    for fname in Files:
        with open(fname, 'rb') as f:
            fheader = bytearray(f.read(NVM_TLV_DATA_START))
            f.close()
            if fheader[0] in [NVM_TLV_VERSION_BT, NVM_TLV_VERSION_FM, NVM_TLV_VERSION_BTFM]:
                ByteStreamSize = os.stat(fname).st_size - NVM_TLV_DATA_START #TotalSize - LengthofHeader
                DataLengthFromHeader = getDataLength(fheader) #Predefined function to read 2,3,4 bytes to get Data Length
                if DataLengthFromHeader != ByteStreamSize:
                    if DEBUG_INFO_FLAG >= 1: print('\n\t' + fname + ' is not a valid Bin file, exit...\n')
                    AreBinFiles = False
            else:
                AreBinFiles = False
    return AreBinFiles

# nvmChecker #
# check if:
#    1) input files' extension are bin or nvm
#    2) the bin file is valid:
#        BT nvm first byte is 0x02
#        FM nvm first byte is 0x03
#        BTFM nvm first byte is 0x04
# flist has two forms:
#    1) non BTFM_MODE: list of input file names
#    2) BTFM_MODE: bianry type code + list of input file names
def nvmChecker(flist):
    # check the file extension
    global MERGER_MODE, BTFM_MODE, VERIFY_MODE
    global BT_CNT, FM_CNT, NVM_CNT, TCF_CNT

    if BT_CNT == 0 and FM_CNT == 0 and VERIFY_MODE == False:
        ftlist = []
        for fname in flist:
            ftlist.append(fname[-3:])

        if ftlist.count('nvm') == len(ftlist):
            MERGER_MODE = NVM_MODE
        #Detect multiple Bin files such as .bin / .b48 / .ba4 which are being created.
        elif CheckIfBinFiles (flist):
            MERGER_MODE = BIN_MODE
        else:
            if DEBUG_INFO_FLAG >= 1: print('\n\tInput file extensions not valid, exit...\n')
            return False

    if MERGER_MODE == BIN_MODE:
        for fname in flist:
            try:
                # extract the NVM header
                with open(fname, 'rb') as f:
                    fheader = f.read(NVM_TLV_DATA_START)
                    f.close()
                fheader_tlv = bytearray(fheader)[0]
                #print('{:02}'.format(fheader_tlv).upper())
                # first type is the TLV type
                if SPLIT_MODE:
                    # split mode only works for BTFM bin file
                    if fheader_tlv != NVM_TLV_VERSION_BTFM:
                        print('\n\t' + fname + ' has invalid header, exit...\n')
                        return False

                if fheader_tlv == NVM_TLV_VERSION_BT:
                    BT_CNT += 1
                elif fheader_tlv == NVM_TLV_VERSION_FM:
                    FM_CNT += 1
                elif fheader_tlv == NVM_TLV_VERSION_BTFM:
                    continue
                else:
                    if DEBUG_INFO_FLAG >= 1: print('\n\t' + fname + ' has invalid header, exit...\n')
                    return False
            except IOError:
                if DEBUG_INFO_FLAG >= 1: print('\n\t' + fname + ' not exist, exit...\n')
                return False

        if BT_CNT != len(flist) and FM_CNT != len(flist):
            BTFM_MODE = True

    elif MERGER_MODE == NVM_MODE:
        fnamelist = []
        if BT_CNT > 0 or FM_CNT > 0:
            ptr = iter(flist)
            for i in ptr:
                if i == NVM_TLV_VERSION_BT:
                    tmp = next(ptr)
                    #print 'BT length %d' %len(tmp)
                    fnamelist += tmp
                if i == NVM_TLV_VERSION_FM:
                    tmp = next(ptr)
                    #print 'FM length %d' %len(tmp)
                    fnamelist += tmp
        else:
            fnamelist = flist
        for fname in fnamelist:
            f_tag_num = -1
            try:
                with open(fname, 'r') as f:
                    for line in f:
                        if '[Tag]' in line:
                            f_tag_num = int(next(f).strip('Num ='), 10)
                            break
                    f.close()

                if f_tag_num <= 0:
                    if DEBUG_INFO_FLAG >= 1: print('\n\t' + fname + ' has improper NVM text format, exit...\n')
                    return False
            except ValueError:
                if DEBUG_INFO_FLAG >= 1: print('\n\tFiles have improper NVM text format, exit...\n')
                return False
            except IOError:
                if DEBUG_INFO_FLAG >= 1: print('\n\t' + fname + ' not exist, exit...\n')
                return False
    elif VERIFY_MODE == True:
        # Verify all NVM files against the supplied TCF file.
        return doesNvmMatchTcf(flist)
    return True

# populate all nvms into the list
## input:
##      flist: a list of file names
##      btlist: a list to save BT NVMTag
##      fmlist: a list to save FM NVMTag
#
def bin2list(flist, btlist=None, fmlist=None):
    btindex = 0 # index of btlist (across all input files)
    fmindex = 0 # index of fmlist (across all input files)
    for fname in flist:
        finfo = os.stat(fname)
        fsize = finfo.st_size
        # open the file
        with open(fname, 'rb') as fobj:
            # check the file type
            # move cursor to where data starts
            fheader = bytearray(fobj.read(NVM_TLV_DATA_START))
            fheader_tlv = fheader[0]
            if fheader_tlv == NVM_TLV_VERSION_BT:
                i = 0
                while (fobj.tell() < fsize) :
                    btlist.append(
                        NVMTag(i, fobj.read(1), fobj.read(1), fobj.read(1), fobj.read(1))
                    )
                    fobj.seek(NVM_TLV_ZERO_PADDING, 1)
                    btlist[btindex].inputval(fobj)
                    i += 1
                    btindex += 1
            elif fheader_tlv == NVM_TLV_VERSION_FM:
                i = 0
                while (fobj.tell() < fsize) :
                    fmlist.append(
                        NVMTag(i, fobj.read(1), fobj.read(1), fobj.read(1), fobj.read(1))
                    )
                    fobj.seek(NVM_TLV_ZERO_PADDING, 1)
                    fmlist[fmindex].inputval(fobj)
                    i += 1
                    fmindex += 1
            elif fheader_tlv == NVM_TLV_VERSION_BTFM:
                # loop for BT and FM sections
                flen = getDataLength(fheader)
                while(flen > 0):
                    dh = bytearray(fobj.read(NVM_TLV_DATA_START))
                    dh_tlv = dh[0]
                    dlen = getDataLength(dh)
                    data = fobj.read(dlen)

                    if dh_tlv == NVM_TLV_VERSION_BT:
                        # BT data, put in btlist #
                        if DEBUG_INFO_FLAG >= 1: print('\n\tBT data dlen: %d\n' %dlen)
                        i = 0 # index in data
                        li = btindex # index in list
                        while(i < dlen):
                            btlist.append(
                                NVMTag(li, data[i],
                                data[i+1], data[i+2], data[i+3])
                                )
                            i += NVM_TLV_TAG + NVM_TLV_LEN
                            i += NVM_TLV_ZERO_PADDING
                            btlist[li].inputval(finput=data,index=i)
                            i += btlist[li].TagLength
                            #btlist[li].printall()
                            li += 1
                        btindex = li

                    if dh_tlv == NVM_TLV_VERSION_FM:
                        # FM data, put in fmlist #
                        if DEBUG_INFO_FLAG >= 1: print('\n\tFM data dlen: %d\n' %dlen)
                        i = 0 # index in data
                        li = fmindex # index in the list
                        while(i < dlen):
                            fmlist.append(
                                NVMTag(li, data[i],
                                data[i+1], data[i+2], data[i+3])
                                )
                            i += NVM_TLV_TAG + NVM_TLV_LEN
                            i += NVM_TLV_ZERO_PADDING
                            fmlist[li].inputval(finput=data,index=i)
                            i += fmlist[li].TagLength
                            #fmlist[li].printall()
                            li += 1
                        fmindex = li

                    flen -= NVM_TLV_DATA_START
                    flen -= dlen

            #print fobj.tell()
            fobj.close()

# append header for BIN file
def getBinHeader(btype, ilist, llen):
    if ilist is None:
        llen = hex(llen).lstrip('0x').zfill(6)
    elif llen is None:
        llen = 0
        for i in ilist:
            llen += NVM_TLV_TAG + NVM_TLV_LEN + NVM_TLV_ZERO_PADDING + i.TagLength
        llen = hex(llen).lstrip('0x').zfill(6)
    blen = binascii.a2b_hex(llen[4:]) + binascii.a2b_hex(llen[2:4]) + binascii.a2b_hex(llen[:2])
    return bytearray([btype]) + bytearray(blen)

# write the list to BIN file
# input:
#    key-value pair (Dictionary)
#    file object to write
# {BTHEADER: BTLIST, FMHEADER: FMLIST, ...}
def list2bin(dicts, fobj):
    # lengh in top-level header, not includes top-level header itself
    tlv_len = 0
    if len(dicts) > 1:
        # multiple lists, save first 4 bytes for top-level header
        fobj.seek(NVM_TLV_DATA_START)
    for bincode in sorted(dicts):
        nvmlist = dicts[bincode]
        # write header for every list
        fobj.write(getBinHeader(bincode, nvmlist, None))
        tlv_len += 4
        # write NVMs
        for nvm in nvmlist:
            fobj.write(nvm.TagNumLSB)
            fobj.write(nvm.TagNumMSB)
            fobj.write(nvm.TagLengthLSB)
            fobj.write(nvm.TagLengthMSB)
            for i in range(NVM_TLV_ZERO_PADDING):
                fobj.write(b'\x00')
            if MERGER_MODE == BIN_MODE:
                for j in range(nvm.TagLength):
                    fobj.write(nvm.TagValue[j])
            elif TRANS_MODE:
                # strip CR and LF to avoid TypeError exception from binascii
                valist = nvm.TagValue[0].strip('\r\n').split(' ')
                for val in valist:
                    #print (val)
                    fobj.write(binascii.a2b_hex(val))
            tlv_len += (NVM_TLV_TAG + NVM_TLV_LEN + NVM_TLV_ZERO_PADDING + nvm.TagLength)

    # write top-level header
    if len(dicts) > 1:
        fobj.seek(0)
        fobj.write(getBinHeader(NVM_TLV_VERSION_BTFM, None, tlv_len))


# get BIN file payload length from header
## input: 4 bytes header as a bytearray ##
## return: length of the BIN payload ##
def getDataLength(h):
    h1 = h[1]
    h2 = h[2]
    h3 = h[3]
    length = (h1%16) + (h1//16)*16
    length += ((h2%16) + (h2//16)*16)*256
    length += ((h3%16) + (h3//16)*16)*65536
    return length

# write the header of NVM-text file
def writeHeaderToFile(ilist, fobj):
        fobj.write('#\n#\n')
        fobj.write('#    Tag Listfile\n')
        fobj.write('#\n#\n')
        fobj.write('\n')
        fobj.write('[General]\n')
        fobj.write('Signature = windows\n')
        fobj.write('FormatVersion = 1.0\n')

        s = ' '
        dt = datetime.now()
        s += dt.strftime('%A %B %d, %Y   %I:%M:%S %p')

        fobj.write('TimeStamp =' + s)
        fobj.write('\n\n')
        fobj.write('[Tag]\n')

        s = 'Num = ' + str(len(ilist)) + '\n\n'
        fobj.write(s)

# write the list to NVM-text file
def list2NVMfile(nvm_list, fobj):
    #print '* list size %d' %len(nvm_list)
    for nvm in nvm_list:
        sHeader = '[Tag' + str(nvm.TagIndex) + ']\n'
        sTagNum = 'TagNum = ' + str(nvm.TagNum) + '\n'
        sTagLength = 'TagLength = ' + str(nvm.TagLength) + '\n'
        sTagValue = 'TagValue ='
        if MERGER_MODE == NVM_MODE:
            sTagValue += nvm.TagValue[0]
            if nvm.TagIndex != len(nvm_list) - 1:
                sTagValue += '\n'
        elif MERGER_MODE == BIN_MODE:
            for i in nvm.TagValue: # a list of bytes
                sTagValue += ' '
                if not isinstance(i, bytes):
                    sTagValue += f'{i:02x}'
                else:
                    sTagValue += f'{i.hex()}'
            sTagValue += '\n'
            if nvm.TagIndex != len(nvm_list) - 1:
                sTagValue += '\n'

        fobj.write(sHeader)
        fobj.write(sTagNum)
        fobj.write(sTagLength)
        fobj.write(sTagValue)


# populate all nvms into the list
def nvm2list(flist, nvm_list, nvm_type):
    global BUILD_LABEL
    nlindex = 0
    for fname in flist:
        tagIndex = 0
        tagNum = 0
        tagLen = 0

        with open(fname, 'r') as fobj:
            for line in fobj:
                if 'TagNum' in line:
                    tagNum = int(line.strip('TagNum ='), 10)
                elif 'TagLength' in line:
                    tagLen = int(line.strip('TagLength ='), 10)
                elif 'TagValue' in line:
                    nvm_list.append(NVMTag(tagIndex,TagNum=tagNum,TagLength=tagLen))
                    nvm_list[nlindex].inputval(valstr=line)
                    #nvm_list[nlindex].printall()
                    tagIndex += 1
                    nlindex += 1
                else:
                    continue
            fobj.close()
    #Reading BUILD LABEL as TAG Number 1 and adding the details to BT NVM Objects only if the conversion is to BIN file
    if BUILD_LABEL and MERGER_MODE == BIN_MODE and nvm_type == 'BT':
        nvm_list.append(NVMTag(tagIndex,TagNum=1,TagLength=64))
        nvm_list[tagIndex].inputval(valstr="TagValue = {}".format((" ").join(BUILD_LABEL)))

# merge input lists and sort them based on Tag num
def mergelists(ilist):
    nvm_list = sorted(ilist, key=lambda nvm: nvm.TagNum)
    for nvm in nvm_list:
        for nvmr in reversed(nvm_list):
            if nvm.TagNum == nvmr.TagNum:
                if nvm is not nvmr:
                    #print('Same TagNum but not same object: ' + str(nvm.TagNum))
                    #nvm.printall()
                    #nvmr.printall()
                    nvm.TagNum = -1

    complete_list = []
    # redefine TagIndex after merging
    for i in range(len(nvm_list)):
        if nvm_list[i].TagNum != -1:
            complete_list.append(nvm_list[i])

    for i in range(len(complete_list)):
        complete_list[i].TagIndex = i
    #complete_list[i].printall()

    return complete_list

# main function
def nvmUtility():
    global output_file, bt_list_output, fm_list_output
    global TRANS_MODE
    optParser()

    ## Check file format and decides MODE
    if not IsCTM and not nvmChecker(input_files):
        exit(EXIT_NVM_CHECK_FAILED)

    # If in verify mode, nothing else needs to be done. Exit with success!
    if VERIFY_MODE == True:
        exit(EXIT_CODE_SUCCESS)

    if DEBUG_INFO_FLAG >= 1: print('\tPass input file checks, starting to '+ MERGER_MODE + ' merger...\n')

    if MERGER_MODE == BIN_MODE:
        ofname = DEFAULT_FILE_OUTPUT + '.bin'
        if SPLIT_MODE:
            # split mode has to be bin->nvm
            TRANS_MODE = True
        elif output_file[-3:] == 'nvm':
            TRANS_MODE = True
        elif output_file is not None:
            ofname = output_file
            # BUILD_LABEL is mandatory for bin file creation.
            if BUILD_LABEL is None:
                print ("\nPlease give --BUILD_LABEL <Build Label> (max. 64 characters) to describe the change done.\n")
                exit(EXIT_CODE_FAILURE)
        else:
            if DEBUG_INFO_FLAG >= 1: print('\tNo valid output file name specified, using default one...')

        if not IsCTM:
            bin2list(input_files, list_input_bt, list_input_fm)


        if BTFM_MODE:
            bt_list_output = mergelists(list_input_bt)
            fm_list_output = mergelists(list_input_fm)
            #for bnvm in bt_list_output:
            #    bnvm.printall()
            #return
            #for fnvm in fm_list_output:
            #    fnvm.printall()
            #return
            complete_dic = {
                    NVM_TLV_VERSION_BT: bt_list_output,
                    NVM_TLV_VERSION_FM: fm_list_output
                    }
            if not TRANS_MODE:
                m = open(ofname, 'w+b')
                list2bin(complete_dic, m)
                m.close()

        else:
            # BT-only or FM-only merger
            if BT_CNT > 0:
                bt_list_output = mergelists(list_input_bt)
                complete_dic = {
                    NVM_TLV_VERSION_BT: bt_list_output
                    }
                if not TRANS_MODE:
                    m = open(ofname, 'w+b')
                    list2bin(complete_dic, m)
                    m.close()
            if FM_CNT > 0:
                fm_list_output = mergelists(list_input_fm)
                complete_dic = {
                    NVM_TLV_VERSION_FM: fm_list_output
                    }
                if not TRANS_MODE:
                    m = open(ofname, 'w+b')
                    list2bin(complete_dic, m)
                    m.close()

    elif MERGER_MODE == NVM_MODE:
        ofname = DEFAULT_FILE_OUTPUT + '.nvm'
        if output_file[-3:] == 'nvm':
            if BT_CNT > 0 and FM_CNT > 0:
                if DEBUG_INFO_FLAG >= 1: print('\tBT+FM nvm merger is not applicable\n')
                exit(EXIT_CODE_INVALID_PARAM)
            # pure-BT or pure-FM
            ofname = output_file
        elif output_file is not None:
            TRANS_MODE = True
            # BUILD_LABEL is mandatory for bin file creation.
            if BUILD_LABEL is None:
                print ("\nPlease give --BUILD_LABEL <Build Label> (max. 64 characters) to describe the change done.\n")
                exit(EXIT_CODE_FAILURE)
        else:
            if DEBUG_INFO_FLAG >= 1: print('\tNo valid output file name specified, using default one...')

        if BTFM_MODE:
            # this won't merge into one NVM file, since it's not possible
            # only merge BT NVMs into one, FM NVMs into one
            nvm2list(input_files[1], list_input_bt, 'BT')
            nvm2list(input_files[3], list_input_fm, 'FM')
            bt_list_output = mergelists(list_input_bt)
            fm_list_output = mergelists(list_input_fm)

        else:
            if BT_CNT > 0:
                if IsCTM:
                    if output_file[-4:] == 'nvmx':
                        mergenvmx(input_files[2], input_files[1], output_file)
                    else: #If not NVMX , making default Output File type as Bin format
                        nvmx2bin(input_files[0], input_files[2], input_files[1], output_file)
                else:
                    nvm2list(input_files[1], list_input_bt, 'BT')
                    bt_list_output = mergelists(list_input_bt)
                    if not TRANS_MODE:
                        m = open(ofname, 'w+')
                        writeHeaderToFile(bt_list_output, m)
                        list2NVMfile(bt_list_output, m)
                        m.close()
            elif FM_CNT > 0:
                if IsCTM:
                    if output_file[-4:] == 'nvmx':
                        mergenvmx(input_files[2], input_files[1], output_file)
                    else: #If not NVMX , making default Output File type as Bin format
                        nvmx2bin(input_files[0], input_files[2], input_files[1], output_file)
                else:
                    nvm2list(input_files[1], list_input_fm, 'FM')
                    fm_list_output = mergelists(list_input_fm)
                    if not TRANS_MODE:
                        m = open(ofname, 'w+')
                        writeHeaderToFile(fm_list_output, m)
                        list2NVMfile(fm_list_output, m)
                        m.close()
            elif FM_CNT == 0 or BT_CNT == 0:
                if IsCTM:
                    nvmx2bin (input_files[2], input_files[1], output_file)
                non_spec_list = []
                nvm2list(input_files, non_spec_list, None)
                non_spec_list_output = mergelists(non_spec_list)
                if not TRANS_MODE:
                    m = open(ofname, 'w+')
                    writeHeaderToFile(non_spec_list_output, m)
                    list2NVMfile(non_spec_list_output, m)
                    m.close()

    if TRANS_MODE:
        try:
            if SPLIT_MODE:
            # output_file has to be None
                for ofname in output_split_files:
                    with open(ofname, 'w+') as s:
                        if ofname == output_split_files[0]:
                            writeHeaderToFile(bt_list_output, s)
                            list2NVMfile(bt_list_output, s)
                        elif ofname == output_split_files[1]:
                            writeHeaderToFile(fm_list_output, s)
                            list2NVMfile(fm_list_output, s)
                        s.close()
            elif output_file[-3:] == 'nvm':
            # BIN -> NVM
                if BTFM_MODE:
                    if DEBUG_INFO_FLAG >= 1: print('\tBTFM bin to nvm is not applicable.\n')
                    exit(EXIT_CODE_INVALID_PARAM)
                else:
                    with open(output_file, 'w+') as m:
                        if BT_CNT > 0:
                            writeHeaderToFile(bt_list_output, m)
                            list2NVMfile(bt_list_output, m)
                        if FM_CNT > 0:
                            writeHeaderToFile(fm_list_output, m)
                            list2NVMfile(fm_list_output, m)
                        m.close()
            elif not IsCTM and output_file is not None:
            # NVM -> BIN
                if BT_CNT == 0 and FM_CNT == 0:
                    if DEBUG_INFO_FLAG >= 1: print('\tFailed. NVM to BIN conversion needs to specify input NVM type.\n')
                    exit(EXIT_CODE_INVALID_PARAM)

                with open(output_file, 'w+b') as m:
                    if BTFM_MODE:
                        complete_dic = {
                            NVM_TLV_VERSION_BT: bt_list_output,
                            NVM_TLV_VERSION_FM: fm_list_output
                            }
                        list2bin(complete_dic, m)
                    else:
                        if BT_CNT > 0:
                            complete_dic = {
                                NVM_TLV_VERSION_BT: bt_list_output
                            }
                            list2bin(complete_dic, m)
                        if FM_CNT > 0:
                            complete_dic = {
                                NVM_TLV_VERSION_FM: fm_list_output
                            }
                            list2bin(complete_dic, m)

                    m.close()
        except IOError:
            if DEBUG_INFO_FLAG >= 1: print('\tCannot open \"' + output_file + '\"\n')
    if DEBUG_INFO_FLAG >= 1: print('\n\tMerge completes\t\n')

# start main function
nvmUtility()
