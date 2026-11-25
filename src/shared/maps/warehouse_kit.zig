const api = @import("api.zig");

pub const K = enum {
    bay,
    pallet,
    load,
    tote,
    barrier,
    cage,
    jack,
};

pub const kit = api.Kit(K);

pub const table = [_]api.Info{
    .{ .file = "warehouse/bay.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.000, -1.000, -2.480 }, .max = .{ 2.480, 0.991, 2.000 } },
    .{ .file = "warehouse/pallet.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.600, 0.000, -0.600 }, .max = .{ 0.600, 0.144, 0.600 } },
    .{ .file = "warehouse/load.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.520, 0.000, -0.420 }, .max = .{ 0.520, 1.211, 0.420 } },
    .{ .file = "warehouse/tote.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.600, 0.000, -0.501 }, .max = .{ 0.600, 1.160, 0.501 } },
    .{ .file = "warehouse/barrier.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -1.000, 0.000, -0.130 }, .max = .{ 1.000, 1.100, 0.130 } },
    .{ .file = "warehouse/cage.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.416, 0.000, -0.362 }, .max = .{ 0.416, 1.800, 0.362 } },
    .{ .file = "warehouse/jack.glb", .scale = 1.00, .collide = .none, .group = .street, .foliage = false, .min = .{ -0.270, 0.000, -0.789 }, .max = .{ 0.270, 1.280, 0.789 } },
};

pub const buildings = [_]api.Building{
    .{ .kind = kit.of(.bay), .w = 4.000, .d = 4.000, .blocks = &.{ .{ -2.000, -2.500, 2.500, 2.000, 2.400 } } },
};
