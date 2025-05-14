
CTL_REGION = {
    'FCC' : 0,
    'ETSI' : 1,
    'JAPAN' : 2,
    'KOREA' : 3,
    'CHINA' : 4,
    'USERDEFINED' : 5,
}

#Device Category for RegRules
DEVICE_CATEGORY = {
    'AP' : 1,
    'STA': 2,
    'Both AP and STA' : 3,
    'AP (6G VLP)' : 4,
    'STA (6G VLP)' : 5,
    'Both AP and STA (6G VLP)' : 6,
    'AP (6G SP)' : 7,
    'STA (6G SP)' : 8,
    'Both AP and STA (6G SP)' : 9,
    'AP (6G LPI)' : 10,
    'STA (6G LPI)' : 11,
    'Both AP and STA (6G LPI)' : 12,
    'Indoor Enabled AP and STA': 13,
    'Indoor standard power AP': 14
}

FREQ_BAND = {
    'FREQ_BAND_UNII_1' : 0,
    'FREQ_BAND_UNII_2a' : 1,
    'FREQ_BAND_UNII_2c' : 2,
    'FREQ_BAND_UNII_3' : 3,
    'FREQ_BAND_UNII_4' : 4,
    'FREQ_BAND_UNII_5' : 5,
    'FREQ_BAND_UNII_6' : 6,
    'FREQ_BAND_UNII_7' : 7,
    'FREQ_BAND_UNII_8' : 8,
    'FREQ_BAND_UNII_5678' : 9,
    'FREQ_BAND_2G' : 10,
}


POWER_RULES = {
    'FCC AP UNII-1' : 0,
    'FCC STA UNII-1,2a,2c' : 1,
    'ETSI UNII-1,2a, ETSI-2c_STA, China 2a, ETSI LPI UNII5' : 2,
    'JAPAN UNII-1, 2a' : 3,
    'KOREA UNII-1, 2a, 2c' : 4,
    'ETSI AP UNII-2c, FCC SP UNII-5,7' : 5,
    'JAPAN UNII-2c' : 6,
    'FCC UNII-3' : 7,
    'FCC AP UNII-4' : 8,
    'FCC STA UNII-4' : 9,
    'CHINA UNII-3' : 10,
    'FCC 2G' : 11,
    'ETSI and China 2G' : 12,
    'JAPAN 2G' : 13,
    'KOREA 2G' : 14,
    'FCC LPI AP  UNII5678' : 15,
    'FCC LPI STA  UNII5678' : 16,
    'FCC SP AP UNII-5,7' : 17,
    'ETSI & KOREA VLP UNII-5' : 18,
    'KOREA LPI UNII-5678' : 19,
    'JAPAN LPI UNII-5' : 20,
    'JAPAN VLP UNII-5' : 21,
    'FCC VLP UNII5678': 22
}


ARRAY_GAIN_RULES = {
    'FCC and Related' : 0,
    'ETSI and Related' : 1,
    'No Array Gain' : 2,
}


POWER_TYPE_6G = {
    'LPI' : 1,
    'SP' : 2,
    'VLP' : 3,
}

# For Exception Table

SUBBAND_EXCEPTIONS = {
    'SUB_BAND_2G' : 0,
    'SUB_BAND_UNII_1' : 1,
    'SUB_BAND_UNII_2a' : 2,
    'SUB_BAND_UNII_2c' : 3,
    'SUB_BAND_UNII_3_4' : 4,
    'SUB_BAND_UNII_5_LPI' : 5,
    'SUB_BAND_UNII_6_LPI' : 6,
    'SUB_BAND_UNII_7_LPI' : 7,
    'SUB_BAND_UNII_8_LPI' : 8,
    'SUB_BAND_UNII_5_VLP' : 9,
    'SUB_BAND_UNII_6_VLP' : 10,
    'SUB_BAND_UNII_7_VLP' : 11,
    'SUB_BAND_UNII_8_VLP' : 12,
    'SUB_BAND_UNII_5_SP' : 13,
    'SUB_BAND_UNII_6_SP' : 14,
    'SUB_BAND_UNII_7_SP' : 15,
    'SUB_BAND_UNII_8_SP' : 16,
}

CTL_GROUPS_5G_6G = {
    '5/6G_20_11a' : 0,
    '5/6G_20_HT/VHT/HE/EHT' : 1,
    '5/6G_20_DL_OFDMA' : 2,
    '5/6G_20_RU242' : 3,
    '5/6G_20_RU106_RU106+26' : 4,
    '5/6G_20_RU52_RU52+26' : 5,
    '5/6G_20_RU26' : 6,
    '5/6G_40_HT/VHT/HE/EHT' : 7,
    '5/6G_40_DL_OFDMA' : 8,
    '5/6G_40_RU484_RU484+242' : 9,
    '5/6G_80_VHT/HE/EHT' : 10,
    '5/6G_80_DL_OFDMA' : 11,
    '5/6G_80_RU996' : 12,
    '5/6G_160_VHT/HE/EHT' : 13,
    '5/6G_160_DL_OFDMA' : 14,
    '5/6G_160_RU996x2' : 15,
    '5G_RU996x3' : 16,
    '5/6G_320_EHT' : 17,
    '5/6G_320_DL_OFDMA' : 18,
    '6G_320_RU996x4' : 19,
}


CTL_GROUPS_2G = {
    '2G_20_CCK' : 0,
    '2G_20_11g' : 1,
    '2G_20_HT/VHT/HE/EHT' : 2,
    '2G_20_DL_OFDMA' : 3,
    '2G_20_RU242' : 4,
    '2G_20_RU106_RU106+26' : 5,
    '2G_20_RU52_RU52+26' : 6,
    '2G_20_RU26' : 7,
    '2G_40_HT/VHT/HE/EHT' : 8,
    '2G_40_DL_OFDMA' : 9,
    '2G_40_RU484' : 10,
}

## ENHANCED_HEAVY_CLIP need re-visit based on enablement of feature for MCC
ENHANCED_HEAVY_CLIP = {
    "FILE_NAME" : "Enhanced_HC_offset_table.xlsx",
    "SHEET_NAME" : "HC_offset_table",
    "PHY" : ["PHYA0", "PHYA1"],
    "BAND_PHY_REL" : {"2G" : "PHYA0", "5G" : ["PHYA0", "PHYA1"], "6G" : ["PHYA0", "PHYA1"]},
    "MAX_CHANNEL" : { "2G" : 22, "5G" : 39, "6G" : 29 },
    "MCS_GROUP" : 4,
    "SUPPORT_CTL_ENGINE" : True,
    "BDF_FIELDS" : {
        "ctl_domain" : "HC_CtlRegion_map",
        "mcs_group" : "HC_McsOffset_Map",
        "ndp_mcs" : "HC_NDP_MCS_Index",
        "chan_start_idx" : "HC_Freq_Start_Index",
        "chan_end_idx" : "HC_Freq_End_Index",
        "chan_number" : "HC_Channel_Index_Map",
        "mcs_offset" : "HC_ctl_mcs_offset",
        "nonht_dup" : "CTL_nonHT_Duplicate_Offset",
        "enable_flag" : "HC_offset_ext_feature_enable",
    },
    "BDF_NAME" : "bdwlan.txt",
}