root.BacklogMenu = {
    Type = BacklogMenuType.None,
    DrawType = DrawComponentType.ExtrasScenes,
    BacklogBackgroundSprite = "BacklogBackground",
    EntryHighlightSprite = "EntryHighlight",
    EntryHighlightPadding = 0,
    VoiceIconSprite = "VoiceIcon",
    ScrollbarTrackSprite = "ScrollbarTrack",
    ScrollbarThumbSprite = "ScrollbarThumb",
    ScrollbarPosition = { X = 1747.5, Y = 147 },
    EntriesStart = { X = 244.5, Y = 127.5 },
    RenderingBounds = { X = 130.5, Y = 124.5, Width = 1582.5, Height = 885 },
    EntryYPadding = 33,
    FadeInDuration = 0.2,
    FadeOutDuration = 0.2
};

root.Sprites["BacklogBackground"] = {
    Sheet = "Backlog",
    Bounds = { X = 0, Y = 0, Width = 1920, Height = 1080 },
};

root.Sprites["VoiceIcon"] = {
    Sheet = "Backlog",
    Bounds = { X = 1921.5, Y = 1.5, Width = 45, Height = 45 },
};

root.Sprites["EntryHighlight"] = {
    Sheet = "Data",
    Bounds = { X = 97.5, Y = 1.5, Width = 141, Height = 45 }
};

root.Sprites["ScrollbarThumb"] = {
    Sheet = "Backlog",
    Bounds = { X = 1921.5, Y = 48, Width = 45, Height = 45 },
};

root.Sprites["ScrollbarTrack"] = {
    Sheet = "Backlog",
    Bounds = { X = 2250, Y = 0, Width = 12, Height = 850.5 },
};