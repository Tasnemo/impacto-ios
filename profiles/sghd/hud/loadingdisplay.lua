root.LoadingDisplay = {
    ResourceLoadBgAnim = "ResourceLoadingBg",
    SaveLoadBgAnim = "SaveLoadingBg",
    LoadingIconAnim = "LoadingDisc",
    LoadingTextAnim = "LoadingText",
    ResourceBgPos = { X = 1611, Y = 916.5 },
    SaveBgPos = { X = 1528.5, Y = 897 },
    IconPos = { X = 1479, Y = 912 },
    TextPos = { X = 1537.5, Y = 942 },
    FadeInDuration = 0.66,
    FadeOutDuration = 0.33
};

MakeAnimation({
    Name = "ResourceLoadingBg",
    Sheet = "Data",
    FirstFrameX = 832.5,
    FirstFrameY = 816,
    FrameWidth = 309,
    ColWidth = 309,
    FrameHeight = 87,
    RowHeight = 90,
    Frames = 8,
    Duration = 0.8,
    Rows = 8,
    Columns = 1,
    PrimaryDirection = AnimationDirections.Down
});

MakeAnimation({
    Name = "SaveLoadingBg",
    Sheet = "Data",
    FirstFrameX = 582,
    FirstFrameY = 0,
    FrameWidth = 415.5,
    ColWidth = 418.5,
    FrameHeight = 121.5,
    RowHeight = 124.5,
    Frames = 4,
    Duration = 0.8,
    Rows = 2,
    Columns = 2,
    PrimaryDirection = AnimationDirections.Down,
    SecondaryDirection = AnimationDirections.Right
});

MakeAnimation({
    Name = "LoadingDisc",
    Sheet = "Data",
    FirstFrameX = 258,
    FirstFrameY = 1.5,
    FrameWidth = 90,
    ColWidth = 93,
    FrameHeight = 90,
    RowHeight = 93,
    Frames = 3,
    Duration = 0.8,
    Rows = 1,
    Columns = 3,
    PrimaryDirection = AnimationDirections.Right
});
root.Animations["LoadingDisc"].Frames[#root.Animations["LoadingDisc"].Frames + 1] = "LoadingDisc1";

MakeAnimation({
    Name = "LoadingText",
    Sheet = "Data",
    FirstFrameX = 259.5,
    FirstFrameY = 136.5,
    FrameWidth = 321,
    ColWidth = 321,
    FrameHeight = 31.5,
    RowHeight = 34.5,
    Frames = 5,
    Duration = 0.8,
    Rows = 5,
    Columns = 1,
    PrimaryDirection = AnimationDirections.Down
});