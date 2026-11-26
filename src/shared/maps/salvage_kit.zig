const api = @import("api.zig");

pub const K = enum {
    hall_cottage,
    terrace,
    dome,
    loft,
    conserv,
    shed,
    gate,
    cottage,
    silo,
    water,
    deck,
    deck_long,
    heap_a,
    heap_b,
    heap_c,
    plates,
    tyres,
    tyre,
    debris,
    pallet,
    barrel,
    barrel_b,
    barrel_t,
    girders,
    box,
    box_rust,
    crane,
    hull,
    wreck,
    cable,
    skip,
    rails,
    sleepers,
    puddle,
    gravel,
    crate,
    fence,
    fgate,
    catwalk,
    platform,
    pipe,
    junction,
    drum,
    butt,
    lamp,
    chimney,
    panel,
    planter,
    crop,
    bale,
    tree,
    bush,
    rock,
    tuft,
    flower,
    tracker,
    spinner,
    washing,
};

pub const kit = api.Kit(K);

pub const table = [_]api.Info{
    .{ .file = "salvage/hall_cottage.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.300, -1.200, -4.880 }, .max = .{ 2.680, 11.414, 4.600 } },
    .{ .file = "salvage/terrace.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -6.900, -1.200, -2.380 }, .max = .{ 7.080, 8.874, 4.600 } },
    .{ .file = "salvage/dome.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.311, -1.200, -4.162 }, .max = .{ 2.669, 10.570, 2.318 } },
    .{ .file = "salvage/loft.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.300, -1.200, -2.300 }, .max = .{ 4.180, 6.900, 2.300 } },
    .{ .file = "salvage/conserv.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.300, -1.200, -4.680 }, .max = .{ 2.680, 6.900, 2.300 } },
    .{ .file = "salvage/shed.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -4.600, -1.200, -2.680 }, .max = .{ 4.880, 4.738, 2.300 } },
    .{ .file = "salvage/gate.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -4.600, -1.200, -2.680 }, .max = .{ 4.880, 7.868, 2.300 } },
    .{ .file = "salvage/cottage.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.300, -1.200, -4.180 }, .max = .{ 2.680, 8.874, 2.300 } },
    .{ .file = "salvage/silo.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.300, -1.200, -2.300 }, .max = .{ 2.680, 10.350, 2.744 } },
    .{ .file = "salvage/water.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.300, -1.200, -2.300 }, .max = .{ 2.300, 13.018, 2.300 } },
    .{ .file = "salvage/deck.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -4.050, -0.066, -11.024 }, .max = .{ 4.050, 4.520, 2.050 } },
    .{ .file = "salvage/deck_long.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -6.050, 0.000, -2.050 }, .max = .{ 6.050, 4.520, 2.050 } },
    .{ .file = "salvage/heap_a.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -5.938, -1.312, -4.345 }, .max = .{ 6.621, 5.350, 5.761 } },
    .{ .file = "salvage/heap_b.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -5.817, -0.899, -5.487 }, .max = .{ 5.251, 5.897, 5.373 } },
    .{ .file = "salvage/heap_c.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -8.293, -1.384, -3.844 }, .max = .{ 9.355, 4.107, 5.788 } },
    .{ .file = "salvage/plates.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -5.980, 0.000, -0.350 }, .max = .{ 5.980, 2.542, 0.110 } },
    .{ .file = "salvage/tyres.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.496, 0.025, -0.510 }, .max = .{ 0.474, 1.329, 0.513 } },
    .{ .file = "salvage/tyre.glb", .scale = 1.00, .collide = .none, .group = .street, .foliage = false, .min = .{ -0.443, 0.007, -0.459 }, .max = .{ 0.443, 0.273, 0.459 } },
    .{ .file = "salvage/debris.glb", .scale = 1.00, .collide = .none, .group = .ground, .foliage = false, .min = .{ -3.081, -0.027, -2.482 }, .max = .{ 2.610, 0.142, 2.734 } },
    .{ .file = "salvage/pallet.glb", .scale = 1.00, .collide = .none, .group = .street, .foliage = false, .min = .{ -0.600, 0.000, -0.600 }, .max = .{ 0.600, 0.140, 0.600 } },
    .{ .file = "salvage/barrel.glb", .scale = 1.00, .collide = .cylinder, .group = .street, .foliage = false, .min = .{ -0.304, 0.000, -0.320 }, .max = .{ 0.304, 0.900, 0.320 } },
    .{ .file = "salvage/barrel_b.glb", .scale = 1.00, .collide = .cylinder, .group = .street, .foliage = false, .min = .{ -0.304, 0.000, -0.320 }, .max = .{ 0.304, 0.900, 0.320 } },
    .{ .file = "salvage/barrel_t.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.450, -0.004, -0.320 }, .max = .{ 0.450, 0.604, 0.320 } },
    .{ .file = "salvage/girders.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -3.184, 0.000, -0.900 }, .max = .{ 3.193, 1.065, 0.900 } },
    .{ .file = "salvage/box.glb", .scale = 1.00, .collide = .box, .group = .building, .foliage = false, .min = .{ -1.188, 0.000, -2.700 }, .max = .{ 1.188, 2.808, 2.700 } },
    .{ .file = "salvage/box_rust.glb", .scale = 1.00, .collide = .box, .group = .building, .foliage = false, .min = .{ -1.188, 0.000, -2.700 }, .max = .{ 1.188, 2.808, 2.700 } },
    .{ .file = "salvage/crane.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -5.438, 0.000, -2.640 }, .max = .{ 5.438, 14.197, 2.640 } },
    .{ .file = "salvage/hull.glb", .scale = 1.00, .collide = .box, .group = .building, .foliage = false, .min = .{ -2.051, 0.000, -1.884 }, .max = .{ 2.051, 2.422, 1.884 } },
    .{ .file = "salvage/wreck.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -1.728, 0.000, -2.362 }, .max = .{ 1.728, 2.514, 2.362 } },
    .{ .file = "salvage/cable.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.578, 0.000, -0.559 }, .max = .{ 0.578, 1.100, 0.559 } },
    .{ .file = "salvage/skip.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -1.801, 0.000, -0.850 }, .max = .{ 1.801, 1.316, 0.850 } },
    .{ .file = "salvage/rails.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.656, 0.000, -4.168 }, .max = .{ 0.656, 0.378, 4.168 } },
    .{ .file = "salvage/sleepers.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -1.351, 0.000, -1.345 }, .max = .{ 1.351, 1.260, 1.345 } },
    .{ .file = "salvage/puddle.glb", .scale = 1.00, .collide = .none, .group = .ground, .foliage = false, .min = .{ -2.090, 0.030, -1.880 }, .max = .{ 2.577, 0.040, 1.708 } },
    .{ .file = "salvage/gravel.glb", .scale = 1.00, .collide = .none, .group = .ground, .foliage = false, .min = .{ -1.775, 0.000, -1.772 }, .max = .{ 1.808, 0.062, 1.543 } },
    .{ .file = "salvage/crate.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.482, 0.000, -0.483 }, .max = .{ 0.482, 0.960, 0.483 } },
    .{ .file = "salvage/fence.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -2.000, 0.000, -0.185 }, .max = .{ 2.000, 1.835, 0.185 } },
    .{ .file = "salvage/fgate.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -1.990, 0.000, -0.246 }, .max = .{ 1.990, 1.945, 0.246 } },
    .{ .file = "salvage/catwalk.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -2.000, 0.000, -0.726 }, .max = .{ 2.000, 1.673, 0.726 } },
    .{ .file = "salvage/platform.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -2.000, 0.000, -2.000 }, .max = .{ 2.000, 2.584, 2.000 } },
    .{ .file = "salvage/pipe.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -2.000, 0.000, -0.376 }, .max = .{ 2.000, 0.981, 0.376 } },
    .{ .file = "salvage/junction.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -1.170, 0.000, -1.580 }, .max = .{ 1.170, 1.562, 1.580 } },
    .{ .file = "salvage/drum.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.486, 0.000, -0.263 }, .max = .{ 0.486, 0.838, 0.263 } },
    .{ .file = "salvage/butt.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.447, 0.000, -0.493 }, .max = .{ 0.447, 1.155, 0.493 } },
    .{ .file = "salvage/lamp.glb", .scale = 1.00, .collide = .cylinder, .group = .street, .foliage = false, .min = .{ -0.307, 0.000, -0.399 }, .max = .{ 0.307, 2.600, 0.399 } },
    .{ .file = "salvage/chimney.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.800, 0.000, -0.800 }, .max = .{ 0.800, 3.978, 0.800 } },
    .{ .file = "salvage/panel.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.600, 0.000, -0.188 }, .max = .{ 0.600, 0.600, 0.188 } },
    .{ .file = "salvage/planter.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.611, 0.000, -0.274 }, .max = .{ 0.611, 0.488, 0.274 } },
    .{ .file = "salvage/crop.glb", .scale = 1.00, .collide = .none, .group = .bush, .foliage = false, .min = .{ -0.399, 0.000, -0.389 }, .max = .{ 0.399, 0.777, 0.389 } },
    .{ .file = "salvage/bale.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.652, 0.000, -0.651 }, .max = .{ 0.652, 1.000, 0.651 } },
    .{ .file = "salvage/tree.glb", .scale = 1.00, .collide = .trunk, .group = .tree, .foliage = false, .min = .{ -2.095, 0.000, -1.542 }, .max = .{ 2.095, 5.199, 1.542 } },
    .{ .file = "salvage/bush.glb", .scale = 1.00, .collide = .none, .group = .bush, .foliage = false, .min = .{ -0.584, 0.000, -0.579 }, .max = .{ 0.584, 1.257, 0.579 } },
    .{ .file = "salvage/rock.glb", .scale = 1.00, .collide = .box, .group = .rock, .foliage = false, .min = .{ -0.840, 0.000, -0.827 }, .max = .{ 0.840, 1.224, 0.827 } },
    .{ .file = "salvage/tuft.glb", .scale = 1.00, .collide = .none, .group = .bush, .foliage = false, .min = .{ -0.271, 0.000, -0.226 }, .max = .{ 0.271, 0.473, 0.226 } },
    .{ .file = "salvage/flower.glb", .scale = 1.00, .collide = .none, .group = .bush, .foliage = false, .min = .{ -0.113, 0.000, -0.100 }, .max = .{ 0.113, 0.661, 0.100 } },
    .{ .file = "salvage/tracker.glb", .scale = 1.00, .collide = .cylinder, .group = .street, .foliage = false, .min = .{ -2.188, 0.000, -1.088 }, .max = .{ 2.188, 6.981, 1.088 } },
    .{ .file = "salvage/spinner.glb", .scale = 1.00, .collide = .cylinder, .group = .street, .foliage = false, .min = .{ -1.548, 0.000, -0.738 }, .max = .{ 1.548, 6.038, 0.738 } },
    .{ .file = "salvage/washing.glb", .scale = 1.00, .collide = .none, .group = .street, .foliage = false, .min = .{ -2.000, 0.000, -0.406 }, .max = .{ 2.000, 2.962, 0.406 } },
};

pub const buildings = [_]api.Building{
};

pub const solids = struct {
    pub const hall_cottage = [_][7]f32{
        .{ 0.000, -2.300, -0.600, 3.100, 2.700, 10.249, 4.600 },
        .{ 0.000, -2.300, -0.600, -4.900, 2.200, 11.414, 3.100 },
        .{ 0.000, 2.200, -0.600, -2.400, 2.700, 10.672, 2.600 },
        .{ 0.000, 2.200, -0.600, -4.900, 2.700, 3.200, -2.900 },
    };
    pub const terrace = [_][7]f32{
        .{ 0.000, -6.900, -0.600, -0.400, 6.600, 7.962, 2.600 },
        .{ 0.000, -6.900, -0.600, -2.400, -1.900, 5.664, -0.400 },
        .{ 0.000, -4.900, -0.600, 2.600, 4.600, 5.654, 4.600 },
        .{ 0.000, 2.100, -0.600, -2.400, 7.100, 8.874, -0.400 },
        .{ 0.000, 6.600, -0.600, -0.400, 7.100, 7.962, 2.100 },
    };
    pub const dome = [_][7]f32{
        .{ 0.000, -2.311, -0.600, -4.182, -1.811, 7.935, 2.318 },
        .{ 0.000, -1.811, -0.600, -4.182, 2.689, 10.570, 1.818 },
        .{ 0.000, -1.311, -0.600, 1.818, 1.189, 7.935, 2.318 },
        .{ 0.000, 1.689, -0.600, 1.818, 2.689, 3.200, 2.318 },
    };
    pub const loft = [_][7]f32{
        .{ 0.000, -2.300, -0.600, 0.800, -1.300, 3.200, 1.800 },
        .{ 0.000, -2.300, -0.600, -2.200, -1.300, 3.200, -1.200 },
        .{ 0.000, 1.200, -0.600, 0.800, 4.200, 6.818, 1.800 },
        .{ 0.000, 1.200, -0.600, -2.200, 2.200, 3.200, -1.200 },
        .{ 0.000, 2.700, -0.600, 1.800, 3.700, 3.200, 2.300 },
        .{ 0.000, 2.700, -0.600, 0.300, 3.700, 2.962, 0.800 },
    };
    pub const conserv = [_][7]f32{
        .{ 0.000, -2.300, -0.600, -2.700, 2.700, 6.900, 2.300 },
        .{ 0.000, -1.300, -0.600, -4.700, 1.200, 2.400, -2.700 },
    };
    pub const shed = [_][7]f32{
        .{ 0.000, -4.600, -0.600, 1.800, -3.600, 3.200, 2.300 },
        .{ 0.000, -4.600, -0.600, -2.200, -4.100, 4.738, 1.800 },
        .{ 0.000, -4.100, -0.600, -2.200, 4.900, 4.738, -1.700 },
        .{ 0.000, -3.100, -0.600, -2.700, 0.900, 4.429, -2.200 },
        .{ 0.000, -1.100, -0.600, 1.300, -0.600, 3.200, 2.300 },
        .{ 0.000, -0.100, -0.600, 1.300, 0.400, 3.200, 2.300 },
        .{ 0.000, 0.900, -0.600, 1.300, 1.900, 3.200, 2.300 },
        .{ 0.000, 1.400, -0.600, -2.700, 4.400, 4.738, -2.200 },
        .{ 0.000, 3.900, -0.600, 1.300, 4.900, 3.200, 2.300 },
        .{ 0.000, 4.400, -0.600, -1.700, 4.900, 4.038, 1.300 },
    };
    pub const gate = [_][7]f32{
        .{ 0.000, -4.600, -0.600, -2.700, -3.100, 7.739, 2.300 },
        .{ 0.000, -3.100, -0.600, 1.300, -2.600, 3.200, 1.800 },
        .{ 0.000, 2.900, -0.600, -2.700, 4.900, 7.739, 2.300 },
    };
    pub const cottage = [_][7]f32{
        .{ 0.000, -2.300, -0.600, -4.200, 2.700, 8.874, 2.300 },
    };
    pub const silo = [_][7]f32{
        .{ 0.000, -2.300, -0.600, -1.256, 2.200, 10.350, 1.744 },
        .{ 0.000, -1.800, -0.600, 1.744, 1.700, 8.878, 2.244 },
        .{ 0.000, -1.800, -0.600, -1.756, 2.200, 9.473, -1.256 },
        .{ 0.000, -1.300, -0.600, -2.256, 1.200, 8.878, -1.756 },
        .{ 0.000, -0.800, -0.600, 2.244, 0.700, 3.200, 2.744 },
        .{ 0.000, 2.200, -0.600, -1.256, 2.700, 2.400, -0.756 },
    };
    pub const water = [_][7]f32{
        .{ 0.000, -2.300, -0.600, 0.800, -0.800, 12.190, 2.300 },
        .{ 0.000, -2.300, -0.600, -2.200, 2.200, 12.190, -0.700 },
        .{ 0.000, -1.800, -0.600, -0.700, 2.200, 13.018, 0.800 },
        .{ 0.000, -0.800, -0.600, 0.800, 2.200, 12.190, 1.800 },
        .{ 0.000, 0.700, -0.600, 1.800, 2.200, 3.200, 2.300 },
    };
    pub const deck = [_][7]f32{
        .{ 0.000, -4.000, 3.100, -2.000, 4.000, 3.400, 2.000 },
        .{ 0.000, -3.930, 0.000, -1.930, -3.670, 3.400, -1.670 },
        .{ 0.000, -3.930, 0.000, 1.670, -3.670, 3.400, 1.930 },
        .{ 0.000, -0.130, 0.000, -1.930, 0.130, 3.400, -1.670 },
        .{ 0.000, -0.130, 0.000, 1.670, 0.130, 3.400, 1.930 },
        .{ 0.000, 3.670, 0.000, -1.930, 3.930, 3.400, -1.670 },
        .{ 0.000, 3.670, 0.000, 1.670, 3.930, 3.400, 1.930 },
        .{ 0.000, -4.000, 3.400, 1.920, 4.000, 4.500, 2.080 },
        .{ 0.000, 3.920, 3.400, -2.000, 4.080, 4.500, 2.000 },
        .{ 0.000, -1.800, 3.400, -2.080, 4.000, 4.500, -1.920 },
        .{ 0.000, -4.080, 3.400, -2.000, -3.920, 4.500, 2.000 },
        .{ 3.000, -3.900, 0.000, -11.000, -1.900, 3.400, -2.000 },
        .{ 0.000, -1.850, 0.000, -11.000, -1.700, 4.500, -2.000 },
        .{ 0.000, -2.500, 3.400, 1.000, -1.700, 4.200, 1.800 },
        .{ 0.000, -0.100, 3.400, 1.000, 0.700, 4.200, 1.800 },
        .{ 0.000, 2.300, 3.400, 1.000, 3.100, 4.200, 1.800 },
    };
    pub const deck_long = [_][7]f32{
        .{ 0.000, -6.000, 3.100, -2.000, 6.000, 3.400, 2.000 },
        .{ 0.000, -5.930, 0.000, -1.930, -5.670, 3.400, -1.670 },
        .{ 0.000, -5.930, 0.000, 1.670, -5.670, 3.400, 1.930 },
        .{ 0.000, -0.130, 0.000, -1.930, 0.130, 3.400, -1.670 },
        .{ 0.000, -0.130, 0.000, 1.670, 0.130, 3.400, 1.930 },
        .{ 0.000, 5.670, 0.000, -1.930, 5.930, 3.400, -1.670 },
        .{ 0.000, 5.670, 0.000, 1.670, 5.930, 3.400, 1.930 },
        .{ 0.000, -6.000, 3.400, 1.920, 6.000, 4.500, 2.080 },
        .{ 0.000, 5.920, 3.400, -2.000, 6.080, 4.500, 2.000 },
        .{ 0.000, -6.080, 3.400, -2.000, -5.920, 4.500, 2.000 },
        .{ 0.000, -6.000, 3.400, -2.080, 6.000, 4.500, -1.920 },
        .{ 0.000, -4.500, 3.400, 1.000, -3.700, 4.200, 1.800 },
        .{ 0.000, -2.100, 3.400, 1.000, -1.300, 4.200, 1.800 },
        .{ 0.000, 0.300, 3.400, 1.000, 1.100, 4.200, 1.800 },
    };
    pub const heap_a = [_][7]f32{
        .{ 0.000, -3.176, -0.500, -2.223, 3.176, 1.000, 2.223 },
        .{ 0.000, -2.664, 1.000, -1.865, 2.664, 2.000, 1.865 },
        .{ 0.000, -1.924, 2.000, -1.346, 1.924, 3.000, 1.346 },
        .{ 0.000, -0.000, 3.000, -0.000, 0.000, 4.000, 0.000 },
    };
    pub const heap_b = [_][7]f32{
        .{ 0.000, -2.540, -0.500, -2.540, 2.540, 1.250, 2.540 },
        .{ 0.000, -2.132, 1.250, -2.132, 2.132, 2.500, 2.132 },
        .{ 0.000, -1.539, 2.500, -1.539, 1.539, 3.750, 1.539 },
        .{ 0.000, -0.000, 3.750, -0.000, 0.000, 5.000, 0.000 },
    };
    pub const heap_c = [_][7]f32{
        .{ 0.000, -4.446, -0.500, -1.905, 4.446, 0.800, 1.905 },
        .{ 0.000, -3.730, 0.800, -1.599, 3.730, 1.600, 1.599 },
        .{ 0.000, -2.693, 1.600, -1.154, 2.693, 2.400, 1.154 },
        .{ 0.000, -0.000, 2.400, -0.000, 0.000, 3.200, 0.000 },
    };
    pub const plates = [_][7]f32{
        .{ 0.000, -6.000, 0.000, -0.100, -4.000, 2.223, 0.100 },
        .{ 0.000, -4.000, 0.000, -0.100, -2.000, 1.959, 0.100 },
        .{ 0.000, -2.000, 0.000, -0.100, 0.000, 2.542, 0.100 },
        .{ 0.000, 0.000, 0.000, -0.100, 2.000, 2.252, 0.100 },
        .{ 0.000, 2.000, 0.000, -0.100, 4.000, 1.629, 0.100 },
        .{ 0.000, 4.000, 0.000, -0.100, 6.000, 2.376, 0.100 },
    };
    pub const tyres = [_][7]f32{
        .{ 0.000, -0.450, 0.000, -0.450, 0.450, 1.500, 0.450 },
    };
    pub const tyre = [_][7]f32{
    };
    pub const debris = [_][7]f32{
    };
    pub const pallet = [_][7]f32{
    };
    pub const barrel = [_][7]f32{
        .{ 0.000, -0.300, 0.000, -0.300, 0.300, 0.900, 0.300 },
    };
    pub const barrel_b = [_][7]f32{
        .{ 0.000, -0.300, 0.000, -0.300, 0.300, 0.900, 0.300 },
    };
    pub const barrel_t = [_][7]f32{
        .{ 0.000, -0.450, 0.000, -0.300, 0.450, 0.600, 0.300 },
    };
    pub const girders = [_][7]f32{
        .{ 0.000, -3.200, 0.000, -0.900, 3.200, 1.100, 0.900 },
    };
    pub const puddle = [_][7]f32{
    };
    pub const gravel = [_][7]f32{
    };
};
