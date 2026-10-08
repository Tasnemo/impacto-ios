-- BacklogMenuType.None: the generic backlog only buffers entries; no sprite
-- is drawn. Thread 07 removed the inherited sprite rectangles (one lay
-- outside the 2048x1080 Steam BACKLOG.DDS). The Steam sheet's opaque
-- regions are recorded in tests/compat/fixtures/sghd_steam_evidence.json
-- ("sheet_regions") for a future SG backlog implementation.
root.BacklogMenu = {
    Type = BacklogMenuType.None,
    DrawType = DrawComponentType.ExtrasScenes,
};
