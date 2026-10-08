-- Sheet -> system.mpk entry, matched by entry name against the Steam install
-- (tests/compat/fixtures/sghd_steam_evidence.json, "sprite_sheets").
-- DesignWidth/DesignHeight are the Steam texture sizes from the owner's
-- census (Thread 06, fixtures/sghd_steam_evidence.json "system_images");
-- the profile design resolution is 1920x1080. Sprite rectangles elsewhere
-- are the PS3 rectangles scaled by 1.5 and are UNVERIFIED (check them with
-- tools/sghd_inspect.py sheets/crops on the Steam install).
-- Menu, TitleBg1 and TitleBg2 have no Steam counterpart in system.mpk, so
-- they are ScriptHandled (never read from an archive) instead of loading an
-- unrelated texture; their Path is only the renderer's surface lookup key.
root.SpriteSheets = {
    ["Data"] = {
        Path = { Mount = "system", Id = 6 }, -- DATA01.DDS
        DesignWidth = 3072,
        DesignHeight = 1788
    },
    ["Font"] = {
        Path = { Mount = "system", Id = 9 }, -- FONT.PNG (FONT2.PNG = id 10: same grid, Latin full-width centred)
        DesignWidth = 3072,
        DesignHeight = 2208
    },
    ["Menu"] = {
        -- no Steam counterpart; Path is only the renderer's lookup key (PS3 id)
        Path = { Mount = "system", Id = 8 },
        ScriptHandled = true,
        DesignWidth = 3072,
        DesignHeight = 1536
    },
    ["Title"] = {
        Path = { Mount = "system", Id = 30 }, -- TITLE_CHIP.DDS
        DesignWidth = 3072,
        DesignHeight = 1536
    },
    ["TitleBg1"] = {
        -- no Steam counterpart; Path is only the renderer's lookup key (PS3 id)
        Path = { Mount = "system", Id = 19 },
        ScriptHandled = true,
        DesignWidth = 1920,
        DesignHeight = 1080
    },
    ["TitleBg2"] = {
        -- no Steam counterpart; Path is only the renderer's lookup key (PS3 id)
        Path = { Mount = "system", Id = 20 },
        ScriptHandled = true,
        DesignWidth = 1920,
        DesignHeight = 1080
    },
    ["Backlog"] = {
        Path = {Mount = "system", Id = 2 }, -- BACKLOG.DDS (not a 1.5x PS3 layout)
        DesignWidth = 2048,
        DesignHeight = 1080
    }
};

root.Sprites = {};
