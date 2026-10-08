root.SaveData = {
    -- Fork-native format (docs/sghd-save-format.md), not Steam's SAVEDATA.DAT.
    Type = SaveDataType.SGHD,
    SaveFilePath = root.BasePaths.RootSavesDir .. "/sghd/impacto-sghd.sav",
    -- (start, length) pairs saved per slot. FlagWork ranges are byte offsets
    -- (8 flags per byte). Values follow the CHLCC/sgps3 script-variable
    -- layout and are unverified for the Steam release.
    FlagWorkRanges = { 50, 50, 300, 100 },
    ScrWorkRanges = { 300, 300, 2300, 1300 },
    -- Global (system) variables, saved once per file by 00 2A type 0 and
    -- restored by type 2. CHLCC system-data layout (FlagWork bytes 100-149
    -- and 460-499, ScrWork 600-999); every census reference to flags
    -- 800-1199 / 3680-3999 and ScrWork 600-999 falls inside it (e.g. the
    -- startup flags 3875/3876). Unverified against Steam's SAVEDATA.DAT.
    SystemFlagWorkRanges = { 100, 50, 460, 40 },
    SystemScrWorkRanges = { 600, 400 },
};
