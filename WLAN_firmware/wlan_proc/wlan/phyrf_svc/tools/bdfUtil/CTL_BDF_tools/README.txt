Usage:
>ctl2bdf.exe <chip> <2g excel file> <5g excel file> [-f6 <6g excel file>] <bdf txt file> <num reg dmns config> <num chan rows config> [-v <version number>]

Note:
 - Make sure genctl_compress.exe is run before giving above args. Please use the generated compressed format excel files.
 - reg domains and chan rows config can be 3,2 or 6,1 typically. If error values are given, prints are provided to guide right values.
 - new BDF txt file is generated with name <bdf txt file>_new.txt. Please generate bin file or elf file depending on chip.
 - command line arguments mentioned within rectangular braces i.e., [] are optional

Ex command:
>ctl2bdf.exe hst Qualcomm_CTL2GHz_STA_-1dB-Penalty_optimized.xlsx Qualcomm_CTL5GHz_STA_-1dB-Penalty_optimized.xlsx -f6 Qualcomm_CTL6GHz_STA_-1dB-Penalty_optimized.xlsx bdwlan_b10.txt 3 2 -v 17

Current configs supported:
- hk
- hst
- hsp
- msl
- cyp
- pine
- maple
- spruce
