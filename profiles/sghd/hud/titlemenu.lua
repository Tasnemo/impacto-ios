-- STEINS;GATE (Steam) title menu, driven by 10 34 (Thread 07c protocol:
-- docs/threads/07c-title-menu.md). The engine reports decisions through
-- SF_TITLEEND (1241) and, in the main menu, SW_TITLECUR (2139).
--
-- Item order and choice ids come from the script's switch after the main
-- menu loop (SW_TITLECUR == 0 / 10, 11 / 20-24 / 30 / 40) and the five
-- entries of the original title (START LOAD EXTRA CONFIG HELP). Only START
-- is enabled: LOAD and EXTRA open sub-menus whose ids are not mapped yet,
-- CONFIG and HELP lead to screens impacto does not have for SGHD.
--
-- ItemBounds are hit boxes in 1080p design pixels, measured on the owner's
-- 1280x720 screenshot of the original title (orange bar + chip, x1.5;
-- +-3 px): bar at x 1041, chips to x 1170, rows every 79 px from y 123.
--
-- Windows visual preview: owner-supplied opaque rectangles from the local
-- Steam TITLE_CHIP.DDS atlas, NOT validated semantic labels. The five
-- x-separated pairs below are plausible normal/selected menu states.
-- The large top-left opaque region is a candidate title background.
-- Keep readable fallback labels until each mapping is confirmed visually.
-- No copyrighted pixels are bundled; only coordinates into system.mpk.
root.TitleMenu = {
    Type = TitleMenuType.SGHD,
    DrawType = DrawComponentType.SystemMenu,
    -- members the shared loader requires; unused by the SGHD menu
    MenuEntriesNum = 0,
    PressToStartPos = { X = 0, Y = 0 },
    PressToStartAnimDurationIn = 0.5,
    PressToStartAnimDurationOut = 0.5,
    PressToStartSprite = "TitleMenuPressToStart",

    -- SW_TITLEMODE value while the main menu loop runs (script: 4 = fade
    -- from press-start, then 3 with SW_TITLEDISPCT 32 before the loop)
    MainMenuMode = 3,
    ItemChoiceIds = { 0, 10, 20, 30, 40 },
    PreviewBackgroundSprite = "SghdPreviewTitleBg",
    ItemSprites = {
        "SghdTitleCandidate1Normal",
        "SghdTitleCandidate2Normal",
        "SghdTitleCandidate3Normal",
        "SghdTitleCandidate4Normal",
        "SghdTitleCandidate5Normal",
    },
    ItemSelectedSprites = {
        "SghdTitleCandidate1Selected",
        "SghdTitleCandidate2Selected",
        "SghdTitleCandidate3Selected",
        "SghdTitleCandidate4Selected",
        "SghdTitleCandidate5Selected",
    },

    ItemEnabled = { 1, 0, 0, 0, 0 },
    ItemBounds = {
        { X = 1557, Y = 112, Width = 198, Height = 50 },
        { X = 1557, Y = 230.5, Width = 198, Height = 50 },
        { X = 1557, Y = 349, Width = 198, Height = 50 },
        { X = 1557, Y = 467.5, Width = 198, Height = 50 },
        { X = 1557, Y = 586, Width = 198, Height = 50 },
    },
};

root.Sprites["TitleMenuPressToStart"] = {
    Sheet = "Title",
    Bounds = { X = 0, Y = 0, Width = 0, Height = 0 },
};

-- Candidate title background crop: opaque alpha region spans roughly
-- X=0 Y=0 W=1932 H=1125. Display at 1920x1080 for the game viewport.
root.Sprites["SghdPreviewTitleBg"] = {
    Sheet = "Title",
    Bounds = { X = 0, Y = 0, Width = 1920, Height = 1080 },
};

-- Candidate paired menu chips in the Steam title atlas. Each left/right
-- column pair has nearly identical dimensions; actual text and state
-- assignment are intentionally marked provisional until checked visually.
local pairedRegions = {
    { 1939, 1,   2140, 1,   179, 47 },
    { 1939, 50,  2140, 50,  180, 48 },
    { 1939, 100, 2140, 100, 179, 47 },
    { 1939, 149, 2140, 149, 180, 48 },
    { 2341, 1,   2542, 1,   179, 47 },
};
for i, region in ipairs(pairedRegions) do
    root.Sprites["SghdTitleCandidate" .. i .. "Normal"] = {
        Sheet = "Title",
        Bounds = { X = region[1], Y = region[2],
                   Width = region[5], Height = region[6] },
    };
    root.Sprites["SghdTitleCandidate" .. i .. "Selected"] = {
        Sheet = "Title",
        Bounds = { X = region[3], Y = region[4],
                   Width = region[5], Height = region[6] },
    };
end
