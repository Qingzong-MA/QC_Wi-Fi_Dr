ctl2bdf.exe
===========
To run ctl2bdf.exe, the input Excel files (BDF Tool - CONFIG.xlsx, BDF Tool - EXCEPTIONS.xlsx, BDF Tool - REGRULES.xlsx, Enhanced_HC_offset_table) must be in the same directory as the executable.

General Usage:
	ctl2bdf.exe -c <chip_name> -f bdwlan_5G_b02.txt

Specific Usage:
	ctl2bdf.exe -c qcn9224 -f bdwlan.txt -e CTLExceptionsList.csv
	ctl2bdf.exe -c qcn9224 -f bdwlan.txt -ho Enhanced_HC_offset_table.xlsx

1. When an exceptions table file is imported using the "-e" flag, the ctl2bdf.exe script imports it into the Exceptions Excel file and also generates the BDF based on these imported exception entries.
2. When an enhanced/expanded heavy clip MCS offset file is imported using the "-ho" flag, the ctl2bdf.exe generated the BDF based on the enhanced heavy clip offset sheet. 

bdf2ctl.exe
===========
Run bdf2ctl.exe to load CTL data in BDF to Excel files. For bdf2ctl.exe, the <bdf file to read> argument refers to the .txt
BDF file which is read in to be parsed. It outputs files named "BDF Tool - CONFIG.xlsx", "BDF Tool - REGRULES.xlsx" and "BDF Tool - EXCEPTIONS.xlsx"

Command for AP products:
	bdf2ctl.exe -f bdwlan.txt

Command for Client products:
    bdf2ctl.exe -c hmt -f bdwlan.txt


NOTE: 
=====
1. chip_names are wcn7850/qcn9224/ipq5332/qcn6432
2. ctl2bdf.exe, new BDF txt file is generated with name <bdf file>_new.txt if Enhanced_HC_offset_table.xlsx is not present
3. ctl2bdf.exe, new BDF txt file is generated with name <bdf file>_new_new.txt if Enhanced_HC_offset_table.xlsx is present
4. Please generate bin file or elf file depending on chip from generated text files.
5. Running ctl2bdf.exe with option -ho generated BDF text with name <bdf file>_new.txt
6. All the CTL sheets are maintained based on MG team's (Corporate regulatory team) inputs.