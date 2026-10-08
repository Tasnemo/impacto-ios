-- Steam release archive names (lowercase .mpk under USRDIR, unverified against
-- a real installation; see tests/compat/README.md "Local validation").
-- Movies are not mounted: their location/format (Bink 2?) is unknown (M2).
root.Vfs = {
    Mounts = {
        ["script"] = {root.BasePaths.RootGamedataDir .. "/sghd/script.mpk"},
        ["system"] = {root.BasePaths.RootGamedataDir .. "/sghd/system.mpk"},
        ["bgm"] = {root.BasePaths.RootGamedataDir .. "/sghd/bgm.mpk"},
        ["se"] = {root.BasePaths.RootGamedataDir .. "/sghd/se.mpk"},
        ["voice"] = {root.BasePaths.RootGamedataDir .. "/sghd/voice.mpk"},
        ["bg"] = {root.BasePaths.RootGamedataDir .. "/sghd/bg.mpk"},
        ["chara"] = {root.BasePaths.RootGamedataDir .. "/sghd/chara.mpk"},
        ["mask"] = {root.BasePaths.RootGamedataDir .. "/sghd/mask.mpk"}
    }
};
