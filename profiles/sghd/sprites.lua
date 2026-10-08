-- Sheet -> system.mpk entry, matched by entry name against the Steam install
-- (tests/compat/fixtures/sghd_steam_evidence.json, "sprite_sheets").
-- DesignWidth/DesignHeight and every sprite rectangle are still the PS3
-- values: Steam sheet sizes are unverified (tools/sghd_census.py --assets).
-- Menu, TitleBg1 and TitleBg2 have no Steam counterpart in system.mpk, so
-- they are ScriptHandled (never read from an archive) instead of loading an
-- unrelated texture; their Path is only the renderer's surface lookup key.
root.SpriteSheets = {
    ["Data"] = {
        Path = { Mount = "system", Id = 6 }, -- DATA01.DDS
        DesignWidth = 2048,
        DesignHeight = 1024
    },
    ["Font"] = {
        Path = { Mount = "system", Id = 9 }, -- FONT.PNG (FONT2.PNG = id 10, role unknown)
        DesignWidth = 2048,
        DesignHeight = 448
    },
    ["Menu"] = {
        -- no Steam counterpart; Path is only the renderer's lookup key (PS3 id)
        Path = { Mount = "system", Id = 8 },
        ScriptHandled = true,
        DesignWidth = 2048,
        DesignHeight = 1024
    },
    ["Title"] = {
        Path = { Mount = "system", Id = 30 }, -- TITLE_CHIP.DDS
        DesignWidth = 2048,
        DesignHeight = 1024
    },
    ["TitleBg1"] = {
        -- no Steam counterpart; Path is only the renderer's lookup key (PS3 id)
        Path = { Mount = "system", Id = 19 },
        ScriptHandled = true,
        DesignWidth = 1280,
        DesignHeight = 720
    },
    ["TitleBg2"] = {
        -- no Steam counterpart; Path is only the renderer's lookup key (PS3 id)
        Path = { Mount = "system", Id = 20 },
        ScriptHandled = true,
        DesignWidth = 1280,
        DesignHeight = 720
    },
    ["Backlog"] = {
        Path = {Mount = "system", Id = 2 }, -- BACKLOG.DDS
        DesignWidth = 2048,
        DesignHeight = 720
    }
};

root.Sprites = {};
