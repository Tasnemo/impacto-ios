-- Steam release archives: USRDIR/*.mpk (lowercase names, MPK v2.0), verified
-- against the owner's install (tests/compat/fixtures/sghd_steam_evidence.json).
-- Copy them flat into <gamedata>/sghd/.
-- Movies are not mounted: the Steam files are loose Bink 2 (.bk2) files that
-- FFmpeg cannot decode, and the playNo -> file mapping (inside Game.exe) is
-- unknown. With no "movie" mount, PlayMovie logs an error and the script
-- continues (docs/sghd-steam-evidence.md). manual.mpk, shader.mpk and mgsshader.mpk
-- are not used by impacto.
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
