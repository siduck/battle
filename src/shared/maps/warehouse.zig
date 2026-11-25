const std = @import("std");
const api = @import("api.zig");
const k = @import("warehouse_kit.zig");

const t = api.terrain;
const kit = k.kit;

pub const def: api.Def = .{
    .name = "Depot",
    .note = "Loading docks and trucks",
    .tint = .{ 186, 150, 100 },
    .ready = false,
    .half = 240,
    .play = 220,
    .facet = 2.5,
    .height = height,
    .ground = ground,
    .build = build,
    .spots = api.autoSpots,
    .props = &k.table,
    .palette = .{
        .sun_dir = .{ 0.5, 0.66, 0.56 },
        .fog = 0.0018,
        .fog_color = .{ 0.78, 0.82, 0.86 },
    },
    .backdrop = .{ 150, 146, 138 },
};

fn height(x: f32, z: f32) f32 {
    const yard = 1 - t.smooth(150, 190, @max(@abs(x), @abs(z)));

    return api.rollingGround(x, z) * (1 - yard);
}

fn ground(x: f32, z: f32) api.Rgb {
    const yard = @max(@abs(x), @abs(z)) < 150;
    const lane = @mod(@floor(x / 12) + @floor(z / 12), 2) == 0;
    const base: [3]f32 = if (!yard) .{ 150, 146, 120 } else if (lane) .{ 132, 132, 128 } else .{ 120, 120, 118 };

    return api.shade(base, api.light(x, z));
}

fn build(b: *api.Builder) void {
    var row: f32 = -60;

    while (row <= 60) : (row += 20) {
        var x: f32 = -60;

        while (x <= 60) : (x += 8) {
            b.put(kit.of(.pallet), x, row, 0, 1);
            b.put(kit.of(.load), x + 2.5, row, 0, 1);
            b.put(kit.of(.tote), x + 4.5, row + 2, 0, 1);
        }

        b.put(kit.of(.barrier), -66, row, api.half_pi, 1);
        b.put(kit.of(.cage), 66, row + 3, 0, 1);
        b.put(kit.of(.jack), 64, row - 3, 0.4, 1);
    }

    _ = api.building(b, k.buildings[0], 0, -90, 0);
}
