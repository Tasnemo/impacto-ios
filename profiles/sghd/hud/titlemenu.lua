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
-- No artwork yet: ItemSprites / ItemSelectedSprites / CursorSprite (sheet
-- "Title" = TITLE_CHIP.DDS) are added once the owner has named the regions
-- (docs/handoff.md). Nothing is drawn until then; keyboard (Enter / arrow
-- keys) and mouse (click on an item box) already work.
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
