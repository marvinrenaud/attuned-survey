-- Migration 033: Disable Apple-flagged activities for App Store compliance
-- Date: 2026-02-02
-- Reason: Apple compliance review flagged 113 activities that need temporary removal
-- Source: attuned_apple_compliance_analysis.xlsx "All Flagged Activities" tab
-- Reversible: Yes, see rollback_033.sql

-- Disable flagged activities by setting is_active = false
-- This prevents them from being served to users while preserving the data

UPDATE activities
SET is_active = false,
    updated_at = NOW()
WHERE activity_id IN (
    822, 823, 824, 825, 826, 832, 833, 835, 842, 843,
    844, 845, 846, 852, 853, 854, 855, 857, 858, 859,
    860, 863, 864, 865, 870, 871, 875, 876, 877, 894,
    899, 900, 908, 911, 912, 916, 917, 922, 923, 924,
    926, 927, 930, 931, 932, 933, 936, 937, 942, 945,
    957, 959, 964, 966, 967, 969, 971, 976, 983, 986,
    990, 994, 999, 1000, 1002, 1004, 1005, 1007, 1019, 1024,
    1026, 1039, 1051, 1065, 1066, 1088, 1109, 1117, 1125, 1135,
    1138, 1146, 1172, 1173, 1175, 1199, 1200, 1245, 1247, 1313,
    1323, 1324, 1329, 1343, 1356, 1358, 1363, 1386, 1389, 1472,
    1479, 1498, 1516, 1553, 1555, 1563, 1590, 1618, 1661, 1666,
    1667, 1669, 1670
);

-- Report what was updated
SELECT
    'Apple compliance: disabled activities' as operation,
    COUNT(*) as activities_disabled
FROM activities
WHERE activity_id IN (
    822, 823, 824, 825, 826, 832, 833, 835, 842, 843,
    844, 845, 846, 852, 853, 854, 855, 857, 858, 859,
    860, 863, 864, 865, 870, 871, 875, 876, 877, 894,
    899, 900, 908, 911, 912, 916, 917, 922, 923, 924,
    926, 927, 930, 931, 932, 933, 936, 937, 942, 945,
    957, 959, 964, 966, 967, 969, 971, 976, 983, 986,
    990, 994, 999, 1000, 1002, 1004, 1005, 1007, 1019, 1024,
    1026, 1039, 1051, 1065, 1066, 1088, 1109, 1117, 1125, 1135,
    1138, 1146, 1172, 1173, 1175, 1199, 1200, 1245, 1247, 1313,
    1323, 1324, 1329, 1343, 1356, 1358, 1363, 1386, 1389, 1472,
    1479, 1498, 1516, 1553, 1555, 1563, 1590, 1618, 1661, 1666,
    1667, 1669, 1670
)
AND is_active = false;
