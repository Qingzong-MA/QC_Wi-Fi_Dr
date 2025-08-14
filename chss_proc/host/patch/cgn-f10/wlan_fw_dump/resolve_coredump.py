#!/usr/bin/python3.8

import sys
import os
import struct

dump_dic = {
    0:"paging.bin",
    1:"fwsramfull.bin",
    2:"remote.bin",
    3:"fwsramonly.bin",
    4:"qdss_ddr.bin"
}

has_rddm_bin = False

def createDumpFile(dumpType):
    global has_rddm_bin
    dump_name=""
	#  print ("dump type: ", dumpType)

    if dumpType == 1:
        has_rddm_bin=True
    if dumpType in dump_dic:
        dump_name=dump_dic[dumpType]
    else:
        print("unknow dump bin type:{}, the dump bin may crack or this is a new dump bin type".format(dumpType))
        dump_name="unknow_dump_type_" + str(dumpType) + ".bin"

    fd = open(dump_name, "wb")

    return fd

fileName = sys.argv[1]
fd = open(fileName, 'rb')
filesize=os.path.getsize(fileName)
print ("fileSize", filesize)

fd.seek(64, os.SEEK_SET);

data = fd.read(8)
fileread = 72
while data != "":
    val = struct.unpack('<II', data)
    print("dump type: {}, length: {}".format(val[0], val[1]))
    if val[1] > 0:
        fileread = fileread + val[1]
        data = fd.read(val[1])
        fdPart = createDumpFile(val[0])
        fdPart.write(data)
        fdPart.close()
    if (fileread + 8 < filesize):
        data = fd.read(8)
        fileread = fileread + 8
    else:
        break;
fd.close()

if not os.path.exists("fwsramfull.bin") or False == has_rddm_bin:
    print("rddm full bin not found, should be a active dump")
    sys.exit("Finish!")

print ("Found rddm full bin")
print ("Begin to parse rddm binary......")
fileName = "fwsramfull.bin"
fd = open(fileName, 'rb')
	
data = fd.read(8)
val = struct.unpack('<II', data)
print ("version", val[0]) 
print ("head_size",  val[1])

entries = (val[1] - 8) // 64

print ("entries:", entries)

data_start=64*entries

data = fd.read()
for i in range(0,entries):
    val = struct.unpack('<qqq20s20s', data[i*64:(i+1)*64])
    #print ("entry head", val[0], val[1], val[2], val[3], val[4])
    filename = val[4].decode('ascii')
    filename = filename.strip("\0")
    if filename == "Q6-SRAM.bin":
        filename = "fwsram.bin"
    if val[2] <= 0:
        print("find 0 length file, the dump may broken, skip..")
        continue
    print("Write to", filename, "len", val[2])
    fdw = open(filename, 'wb')
    fdw.write(data[data_start:data_start+val[2]])
    fdw.close()
    data_start=data_start+val[2]

fd.close()
    


    
    
    


