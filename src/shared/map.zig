const math = @import("math.zig");
const geom = @import("geom.zig");

const Vec3 = math.Vec3;
const vec = math.vec;

pub const Paint = enum(u8) { floor, floor_alt, wall, coral, coral_dark, teal, teal_dark, cream, sunny, wood, red, blue, orange, mint, lavender, steel, yellow, white, purple, green, dark, grass, olive, tan, glove };

pub const Piece = struct {
    shape: geom.Shape,
    paint: Paint = .cream,
};

pub const Beam = struct {
    a: Vec3,
    b: Vec3,
    radius: f32,
    paint: Paint = .yellow,
};

pub const half_size: f32 = 32;
pub const wall_height: f32 = 6;

fn box(x0: f32, y0: f32, z0: f32, x1: f32, y1: f32, z1: f32, paint: Paint) Piece {
    return .{
        .shape = .{ .box = .{ .min = vec(x0, y0, z0), .max = vec(x1, y1, z1) } },
        .paint = paint,
    };
}

fn ramp(x0: f32, y0: f32, z0: f32, x1: f32, y1: f32, z1: f32, rise: geom.Rise) Piece {
    return .{
        .shape = .{ .ramp = .{ .min = vec(x0, y0, z0), .max = vec(x1, y1, z1), .rise = rise } },
        .paint = .sunny,
    };
}

fn cylinder(x: f32, y: f32, z: f32, radius: f32, height: f32, paint: Paint) Piece {
    return .{
        .shape = .{ .cylinder = .{ .base = vec(x, y, z), .radius = radius, .height = height } },
        .paint = paint,
    };
}

fn crate(x: f32, z: f32, size: f32, paint: Paint) Piece {
    const h = size / 2;

    return box(x - h, 0, z - h, x + h, size, z + h, paint);
}

fn barrel(x: f32, z: f32, paint: Paint) Piece {
    return cylinder(x, 0, z, 0.55, 1.2, paint);
}

fn building(comptime sx: f32, comptime sz: f32, comptime wall: Paint, comptime roof: Paint) [17]Piece {
    const X = struct {
        fn x(v: f32) f32 {
            return v * sx;
        }

        fn z(v: f32) f32 {
            return v * sz;
        }
    };

    return .{
        box(@min(X.x(-28), X.x(-27.5)), 0, @min(X.z(-28), X.z(-16)), @max(X.x(-28), X.x(-27.5)), wall_height, @max(X.z(-28), X.z(-16)), wall),
        box(@min(X.x(-28), X.x(-14)), 0, @min(X.z(-28), X.z(-27.5)), @max(X.x(-28), X.x(-14)), wall_height, @max(X.z(-28), X.z(-27.5)), wall),
        box(@min(X.x(-14.5), X.x(-14)), 0, @min(X.z(-28), X.z(-16)), @max(X.x(-14.5), X.x(-14)), wall_height, @max(X.z(-28), X.z(-16)), wall),

        box(@min(X.x(-28), X.x(-25)), 0, @min(X.z(-16.5), X.z(-16)), @max(X.x(-28), X.x(-25)), wall_height, @max(X.z(-16.5), X.z(-16)), wall),
        box(@min(X.x(-25), X.x(-22.5)), 0, @min(X.z(-16.5), X.z(-16)), @max(X.x(-25), X.x(-22.5)), 1.2, @max(X.z(-16.5), X.z(-16)), wall),
        box(@min(X.x(-25), X.x(-22.5)), 3, @min(X.z(-16.5), X.z(-16)), @max(X.x(-25), X.x(-22.5)), wall_height, @max(X.z(-16.5), X.z(-16)), wall),
        box(@min(X.x(-22.5), X.x(-20)), 0, @min(X.z(-16.5), X.z(-16)), @max(X.x(-22.5), X.x(-20)), wall_height, @max(X.z(-16.5), X.z(-16)), wall),
        box(@min(X.x(-20), X.x(-17)), 3, @min(X.z(-16.5), X.z(-16)), @max(X.x(-20), X.x(-17)), wall_height, @max(X.z(-16.5), X.z(-16)), wall),
        box(@min(X.x(-17), X.x(-14.5)), 0, @min(X.z(-16.5), X.z(-16)), @max(X.x(-17), X.x(-14.5)), wall_height, @max(X.z(-16.5), X.z(-16)), wall),

        box(@min(X.x(-28), X.x(-14)), wall_height, @min(X.z(-28), X.z(-16)), @max(X.x(-28), X.x(-14)), wall_height + 0.4, @max(X.z(-28), X.z(-16)), roof),

        box(@min(X.x(-26.5), X.x(-25)), 0, @min(X.z(-26.5), X.z(-25)), @max(X.x(-26.5), X.x(-25)), 1.5, @max(X.z(-26.5), X.z(-25)), .orange),
        box(@min(X.x(-24.8), X.x(-23.8)), 0, @min(X.z(-26.5), X.z(-25.5)), @max(X.x(-24.8), X.x(-23.8)), 1, @max(X.z(-26.5), X.z(-25.5)), .wood),
        box(@min(X.x(-18), X.x(-15.5)), 0, @min(X.z(-23), X.z(-21)), @max(X.x(-18), X.x(-15.5)), 1.1, @max(X.z(-23), X.z(-21)), .wood),

        cylinder(X.x(-26.5), 0, X.z(-18), 0.55, 1.2, .red),
        cylinder(X.x(-25.2), 0, X.z(-18.4), 0.55, 1.2, .blue),

        box(@min(X.x(-11), X.x(-9)), 0, @min(X.z(-30), X.z(-28)), @max(X.x(-11), X.x(-9)), 2, @max(X.z(-30), X.z(-28)), .wood),
        box(@min(X.x(-10.5), X.x(-9.5)), 2, @min(X.z(-29.5), X.z(-28.5)), @max(X.x(-10.5), X.x(-9.5)), 3, @max(X.z(-29.5), X.z(-28.5)), .mint),
    };
}

fn stairs(comptime sx: f32, comptime sz: f32) [12]Piece {
    var out: [12]Piece = undefined;

    for (&out, 0..) |*p, i| {
        const fi: f32 = @floatFromInt(i);
        const za = (-16.5 - (fi + 1) * 0.9) * sz;
        const zb = (-16.5 - fi * 0.9) * sz;
        const xa = -14 * sx;
        const xb = -12 * sx;

        p.* = box(@min(xa, xb), 0, @min(za, zb), @max(xa, xb), (fi + 1) * 0.5, @max(za, zb), .cream);
    }

    return out;
}

const outer = [_]Piece{
    box(-half_size, -1, -half_size, half_size, 0, half_size, .floor),

    box(-half_size - 1, 0, -half_size - 1, half_size + 1, wall_height, -half_size, .wall),
    box(-half_size - 1, 0, half_size, half_size + 1, wall_height, half_size + 1, .wall),
    box(-half_size - 1, 0, -half_size, -half_size, wall_height, half_size, .wall),
    box(half_size, 0, -half_size, half_size + 1, wall_height, half_size, .wall),
};

const plaza = [_]Piece{
    box(-6, 0, -6, 6, 1.5, 6, .cream),
    ramp(-2, 0, -12, 2, 1.5, -6, .pos_z),
    ramp(-2, 0, 6, 2, 1.5, 12, .neg_z),
    ramp(6, 0, -2, 12, 1.5, 2, .neg_x),
    ramp(-12, 0, -2, -6, 1.5, 2, .pos_x),

    cylinder(0, 1.5, 0, 1.6, 0.8, .white),
    cylinder(0, 2.3, 0, 0.45, 1.8, .blue),

    cylinder(-5.7, 1.5, -5.7, 0.08, 1.0, .steel),
    cylinder(5.7, 1.5, -5.7, 0.08, 1.0, .steel),
    cylinder(-5.7, 1.5, 5.7, 0.08, 1.0, .steel),
    cylinder(5.7, 1.5, 5.7, 0.08, 1.0, .steel),
};

const tower = [_]Piece{
    cylinder(18.2, 0, -21.8, 0.25, 7, .steel),
    cylinder(21.8, 0, -21.8, 0.25, 7, .steel),
    cylinder(18.2, 0, -18.2, 0.25, 7, .steel),
    cylinder(21.8, 0, -18.2, 0.25, 7, .steel),
    cylinder(20, 7, -20, 3, 3.5, .lavender),
    cylinder(20, 10.5, -20, 0.6, 0.6, .purple),
};

const yard = [_]Piece{
    box(-27, 0, 10, -21, 2.6, 12.5, .blue),
    box(-27, 2.6, 10.2, -22, 5.2, 12.5, .orange),
    box(-27, 0, 14, -24.5, 2.6, 20, .teal),

    box(21, 0, -10, 27, 2.6, -7.5, .orange),
    box(24.5, 0, -6, 27, 2.6, 0, .blue),

    crate(-14, 8, 1.4, .wood),
    crate(-12.6, 8.2, 1, .mint),
    crate(14, -8, 1.4, .wood),
    crate(12.6, -8.3, 1, .wood),
    crate(9, 20, 1.6, .sunny),
    crate(-9, -20, 1.6, .wood),
    crate(-9, -18.6, 1, .wood),
    crate(26, 26, 1.8, .wood),
    crate(-26, -2, 1.4, .wood),

    barrel(-4, 18, .red),
    barrel(-2.8, 18.6, .teal),
    barrel(4, -18, .blue),
    barrel(16, 6, .red),
    barrel(-16, -6, .teal),
    barrel(27, 12, .red),

    box(-20, 0, 4, -12, 1.2, 4.6, .mint),
    box(12, 0, -4.6, 20, 1.2, -4, .mint),
    box(4, 0, 24, 4.6, 1.2, 30, .mint),
    box(-4.6, 0, -30, -4, 1.2, -24, .mint),
    box(14, 0, 24, 20, 1.2, 24.6, .mint),
    box(-20, 0, -24.6, -14, 1.2, -24, .mint),
};

pub const pieces = outer ++ plaza ++ tower ++ yard ++ building(1, 1, .coral, .coral_dark) ++ stairs(1, 1) ++ building(-1, -1, .teal, .teal_dark) ++ stairs(-1, -1);

pub const beams = [_]Beam{
    .{ .a = vec(-31.6, 4.4, -31.6), .b = vec(31.6, 4.4, -31.6), .radius = 0.22, .paint = .yellow },
    .{ .a = vec(-31.6, 3.8, -31.6), .b = vec(31.6, 3.8, -31.6), .radius = 0.14, .paint = .red },
    .{ .a = vec(31.6, 4.4, -31.6), .b = vec(31.6, 4.4, 31.6), .radius = 0.22, .paint = .yellow },
    .{ .a = vec(-31.6, 4.4, 31.6), .b = vec(31.6, 4.4, 31.6), .radius = 0.22, .paint = .yellow },

    .{ .a = vec(-5.7, 2.4, -5.7), .b = vec(-2.2, 2.4, -5.7), .radius = 0.05, .paint = .steel },
    .{ .a = vec(2.2, 2.4, -5.7), .b = vec(5.7, 2.4, -5.7), .radius = 0.05, .paint = .steel },
    .{ .a = vec(-5.7, 2.4, 5.7), .b = vec(-2.2, 2.4, 5.7), .radius = 0.05, .paint = .steel },
    .{ .a = vec(2.2, 2.4, 5.7), .b = vec(5.7, 2.4, 5.7), .radius = 0.05, .paint = .steel },
    .{ .a = vec(-5.7, 2.4, -5.7), .b = vec(-5.7, 2.4, -2.2), .radius = 0.05, .paint = .steel },
    .{ .a = vec(-5.7, 2.4, 2.2), .b = vec(-5.7, 2.4, 5.7), .radius = 0.05, .paint = .steel },
    .{ .a = vec(5.7, 2.4, -5.7), .b = vec(5.7, 2.4, -2.2), .radius = 0.05, .paint = .steel },
    .{ .a = vec(5.7, 2.4, 2.2), .b = vec(5.7, 2.4, 5.7), .radius = 0.05, .paint = .steel },

    .{ .a = vec(18.2, 3.5, -21.8), .b = vec(21.8, 3.5, -18.2), .radius = 0.1, .paint = .steel },
    .{ .a = vec(21.8, 3.5, -21.8), .b = vec(18.2, 3.5, -18.2), .radius = 0.1, .paint = .steel },
    .{ .a = vec(20, 10.5, -20), .b = vec(20, 14, -20), .radius = 0.05, .paint = .red },
};

pub const spawns = [_]Vec3{
    vec(0, 0, 22),
    vec(-22, 0, 0),
    vec(22, 0, 0),
    vec(0, 0, -22),
    vec(-21, 0, -20),
    vec(21, 0, 20),
};

pub const spawn_yaws = [_]f32{ 3.14159, 1.5708, -1.5708, 0, 0.785, -2.356 };

pub const drone_anchors = [_]Vec3{
    vec(0, 8, 0),
    vec(-16, 7, 0),
    vec(16, 7, 0),
    vec(0, 7, -16),
    vec(0, 7, 16),
    vec(-20, 9, 20),
    vec(20, 8, -8),
    vec(-8, 6, 20),
    vec(8, 6, -22),
    vec(-24, 8, 6),
    vec(24, 8, 4),
    vec(10, 5, 10),
    vec(-10, 5, -10),
    vec(-20, 10, -22),
    vec(22, 10, 22),
};

pub const weapon_spots = [_]Vec3{
    vec(0, 1.5, 3.6),
    vec(-21, 0, -22),
    vec(21, 0, 22),
    vec(-21, 6.4, -22),
    vec(21, 6.4, 22),
    vec(16, 0, -14),
    vec(-25.7, 2.6, 17),
    vec(25.7, 2.6, -3),
    vec(0, 0, -27),
    vec(0, 0, 27),
    vec(-27, 0, 4),
    vec(27, 0, 6),
    vec(-9, 0, 24),
    vec(9, 0, -26),
    vec(-14, 0, -10),
    vec(14, 0, 10),
};
