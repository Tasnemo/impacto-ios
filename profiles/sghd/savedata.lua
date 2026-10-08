root.SaveData = {
    -- Fork-native format (docs/sghd-save-format.md), not Steam's SAVEDATA.DAT.
    Type = SaveDataType.SGHD,
    SaveFilePath = root.BasePaths.RootSavesDir .. "/sghd/impacto-sghd.sav",
    -- (start, length) pairs saved per slot. FlagWork ranges are byte offsets
    -- (8 flags per byte). Values follow the CHLCC/sgps3 script-variable
    -- layout and are unverified for the Steam release.
    FlagWorkRanges = { 50, 50, 300, 100 },
    ScrWorkRanges = { 300, 300, 2300, 1300 },
};
