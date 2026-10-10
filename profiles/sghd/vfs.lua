-- Steam release archives: USRDIR/*.mpk (lowercase names, MPK v2.0), verified
-- against the owner's install (tests/compat/fixtures/sghd_steam_evidence.json).
-- Copy them flat into <gamedata>/sghd/.
-- Movie ID -> original name mapping comes from Steam Game.exe and is
-- implemented only for SGHD by src/vm/inst_movie.cpp. An OPTIONAL local
-- folder containing user-converted MP4s (name preserved, e.g. title.mp4)
-- supplies the video. Original BK2 files are neither usable by FFmpeg nor
-- required here. A missing movie-converted folder is non-fatal; movie opcodes
-- skip playback cleanly. Never commit original or converted game footage.
-- manual.mpk, shader.mpk and mgsshader.mpk are not used by impacto.
root.Vfs = {
    Mounts = {
        ["script"] = {root.BasePaths.RootGamedataDir .. "/sghd/script.mpk"},
        ["system"] = {root.BasePaths.RootGamedataDir .. "/sghd/system.mpk"},
        ["bgm"] = {root.BasePaths.RootGamedataDir .. "/sghd/bgm.mpk"},
        ["se"] = {root.BasePaths.RootGamedataDir .. "/sghd/se.mpk"},
        ["voice"] = {root.BasePaths.RootGamedataDir .. "/sghd/voice.mpk"},
        ["bg"] = {root.BasePaths.RootGamedataDir .. "/sghd/bg.mpk"},
        ["chara"] = {root.BasePaths.RootGamedataDir .. "/sghd/chara.mpk"},
        ["mask"] = {root.BasePaths.RootGamedataDir .. "/sghd/mask.mpk"},
        ["movie"] = {root.BasePaths.RootGamedataDir .. "/sghd/movie-converted"}
    }
};
