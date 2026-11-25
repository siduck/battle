const std = @import("std");

pub const math = @import("../math.zig");
pub const geom = @import("../geom.zig");
pub const props = @import("../props.zig");
pub const terrain = @import("../terrain.zig");
pub const world = @import("../world.zig");
pub const movement = @import("../movement.zig");

pub const Vec3 = math.Vec3;
pub const vec = math.vec;
pub const Builder = world.Builder;
pub const Rng = world.Rng;
pub const Kind = props.Kind;
pub const Info = props.Info;
pub const Tone = world.Tone;
pub const Rgb = [3]u8;

pub const half_pi: f32 = std.math.pi / 2.0;

pub const Palette = struct {
    sun_dir: [3]f32 = .{ 0.55, 0.64, 0.53 },
    sun_tint: [3]f32 = .{ 1.15, 1.0, 0.86 },
    grade_tint: [3]f32 = .{ 1.03, 1.0, 0.96 },
    grade_sat: f32 = 1.12,
    fog: f32 = 0.0022,
    fog_color: [3]f32 = .{ 0.72, 0.8, 0.9 },
    amb_sky: [3]f32 = .{ 0.92, 1.0, 1.18 },
    amb_ground: [3]f32 = .{ 0.8, 0.74, 0.6 },
    shade_tint: [3]f32 = .{ 0.9, 0.93, 1.05 },
    zenith: [3]f32 = .{ 0.05, 0.24, 0.62 },
};

pub const Scatter = struct {
    enabled: bool = true,
    clumps: f32 = 1,
    flowers: f32 = 0.35,
    pebbles: f32 = 1,
    litter: f32 = 0.5,
    flower_colors: [2]Rgb = .{ .{ 236, 214, 96 }, .{ 238, 238, 230 } },
};

pub const Def = struct {
    name: [:0]const u8,
    note: [:0]const u8,
    tint: Rgb,
    ready: bool = true,
    half: f32 = 250,
    play: f32 = 230,
    facet: f32 = 2.5,
    configure: ?*const fn () void = null,
    height: *const fn (x: f32, z: f32) f32,
    ground: *const fn (x: f32, z: f32) Rgb,
    road: ?*const fn (x: f32, z: f32) f32 = null,
    flat: ?*const fn (x: f32, z: f32) f32 = null,
    build: *const fn (b: *Builder) void,
    spots: *const fn (gpa: std.mem.Allocator) void,
    props: []const Info = &.{},
    palette: Palette = .{},
    backdrop: Rgb = .{ 150, 140, 120 },
    floor_y: f32 = -0.2,
    runway: ?[4]f32 = null,
    helipads: ?[3][2]f32 = null,
    aircraft: bool = false,
    tanks: bool = false,
    grip: f32 = 0.84,
    tufts: f32 = 0.85,
    paved: bool = false,
    scatter: Scatter = .{},
};

pub fn kind(i: usize) Kind {
    return props.localKind(i);
}

pub fn Kit(comptime E: type) type {
    return struct {
        pub fn of(e: E) Kind {
            return props.localKind(@intFromEnum(e));
        }
    };
}

pub fn shade(base: [3]f32, k: f32) Rgb {
    return .{ @intFromFloat(std.math.clamp(base[0] * k, 0, 255)), @intFromFloat(std.math.clamp(base[1] * k, 0, 255)), @intFromFloat(std.math.clamp(base[2] * k, 0, 255)) };
}

pub fn mix3(a: [3]f32, c: [3]f32, k: f32) [3]f32 {
    const q = std.math.clamp(k, 0, 1);

    return .{ a[0] + (c[0] - a[0]) * q, a[1] + (c[1] - a[1]) * q, a[2] + (c[2] - a[2]) * q };
}

pub fn light(x: f32, z: f32) f32 {
    const n = terrain.normal(x, z);
    const vary = 0.94 + terrain.fbm(x * 0.08, z * 0.08) * 0.12;

    return vary + n.x * 0.04 - n.z * 0.03;
}

pub fn flatGround(x: f32, z: f32) f32 {
    _ = x;
    _ = z;

    return 0;
}

pub fn rollingGround(x: f32, z: f32) f32 {
    const edge = @max(@abs(x), @abs(z));
    const rim = terrain.smooth(terrain.play - 25, terrain.half, edge) * (10 + terrain.fbm(x * 0.04, z * 0.04) * 8);
    const roll = (terrain.fbm(x * 0.012 + 40, z * 0.012 - 11) - 0.4) * 6;

    return @max(roll, 0) + rim;
}

pub fn plainColor(x: f32, z: f32) Rgb {
    const n = terrain.normal(x, z);

    return shade(mix3(.{ 150, 150, 136 }, .{ 128, 124, 112 }, terrain.smooth(0.2, 0.45, 1 - n.y)), light(x, z));
}

pub fn autoSpots(gpa: std.mem.Allocator) void {
    world.autoSpots(gpa, .{});
}

pub fn noBuild(b: *Builder) void {
    _ = b;
}

pub fn stub(comptime name: [:0]const u8, comptime note: [:0]const u8, comptime tint: Rgb) Def {
    return .{
        .name = name,
        .note = note,
        .tint = tint,
        .ready = false,
        .height = rollingGround,
        .ground = plainColor,
        .build = noBuild,
        .spots = autoSpots,
    };
}

pub const Building = struct {
    kind: Kind,
    w: f32,
    d: f32,
    blocks: []const [5]f32,
};

pub fn building(b: *Builder, bld: Building, x: f32, z: f32, yaw: f32) f32 {
    const y0 = world.lowest(x, z, @max(bld.w, bld.d) / 2 + 0.5) + 0.4;

    b.putAt(bld.kind, vec(x, y0, z), yaw, 1);

    for (bld.blocks) |bl| {
        const r = world.rotBox(x, z, yaw, bl[0], bl[1], bl[2], bl[3]);

        b.solid(.{ .box = .{ .min = vec(r[0], y0 - 0.9, r[1]), .max = vec(r[2], y0 + bl[4] + 0.1, r[3]) } });
    }

    return y0;
}

pub fn box(b: *Builder, x0: f32, y0: f32, z0: f32, x1: f32, y1: f32, z1: f32) void {
    b.solid(.{ .box = .{ .min = vec(x0, y0, z0), .max = vec(x1, y1, z1) } });
}

pub fn scatter(b: *Builder, kinds: []const Kind, count: u32, x0: f32, z0: f32, x1: f32, z1: f32, keep: *const fn (x: f32, z: f32) bool) void {
    var i: u32 = 0;
    var tries: u32 = 0;

    while (i < count and tries < count * 20) : (tries += 1) {
        const x = b.rng.range(x0, x1);
        const z = b.rng.range(z0, z1);

        if (!keep(x, z)) continue;

        b.put(b.rng.pick(Kind, kinds), x, z, b.rng.range(0, std.math.tau), b.rng.range(0.85, 1.15));
        i += 1;
    }
}

pub fn clutter(b: *Builder, kinds: []const Kind, x: f32, z: f32, r0: f32, r1: f32, count: u32) void {
    var i: u32 = 0;

    while (i < count) : (i += 1) {
        const a = b.rng.range(0, std.math.tau);
        const d = b.rng.range(r0, r1);

        b.put(b.rng.pick(Kind, kinds), x + @cos(a) * d, z + @sin(a) * d, b.rng.range(0, std.math.tau), b.rng.range(0.85, 1.15));
    }
}

pub fn anywhere(x: f32, z: f32) bool {
    _ = x;
    _ = z;

    return true;
}
