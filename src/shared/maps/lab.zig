const std = @import("std");
const api = @import("api.zig");
const lk = @import("lab_kit.zig");

const t = api.terrain;
const kit = lk.kit;
const S = lk.solids;
const R = lk.rooms;
const K = lk.K;
const vec = api.vec;
const Builder = api.Builder;
const half_pi = api.half_pi;
const pi = std.math.pi;

pub const def: api.Def = .{
    .name = "Research Lab",
    .note = "Lab blocks, corridors and a campus quad",
    .tint = .{ 90, 170, 176 },
    .ready = true,
    .half = 178,
    .play = 150,
    .facet = 2.0,
    .height = height,
    .ground = ground,
    .build = build,
    .spots = spots,
    .props = &lk.table,
    .palette = .{
        .sun_dir = .{ 0.46, 0.66, -0.6 },
        .sun_tint = .{ 1.12, 1.04, 0.94 },
        .fog = 0.0028,
        .fog_color = .{ 0.8, 0.86, 0.9 },
        .zenith = .{ 0.08, 0.3, 0.64 },
    },
    .backdrop = .{ 92, 122, 84 },
    .floor_y = -3,
    .grip = 0.86,
    .tufts = 0.25,
};

const edge: f32 = 147;

const Bld = struct { kind: K, x: f32, z: f32, yaw: f32 };

const labs = [_]Bld{
    .{ .kind = .lab_big, .x = 0, .z = 52, .yaw = 0 },
    .{ .kind = .lab_mid, .x = 0, .z = -50, .yaw = 0 },
    .{ .kind = .lab_low, .x = 62, .z = 0, .yaw = half_pi },
    .{ .kind = .lab_mid, .x = -64, .z = 0, .yaw = half_pi },
    .{ .kind = .lab_big, .x = -84, .z = -104, .yaw = 0 },
    .{ .kind = .lab_low, .x = 96, .z = 100, .yaw = 0 },
    .{ .kind = .lab_low, .x = -100, .z = 100, .yaw = pi },
    .{ .kind = .lab_mid, .x = 116, .z = -8, .yaw = half_pi },
    .{ .kind = .lab_low, .x = 44, .z = -112, .yaw = 0 },
    .{ .kind = .lab_low, .x = -122, .z = -22, .yaw = half_pi },
    .{ .kind = .lab_mid, .x = -40, .z = 118, .yaw = 0 },
    .{ .kind = .lab_low, .x = 40, .z = 118, .yaw = 0 },
};

const extras = [_][3]f32{ .{ 110, -40, half_pi }, .{ -122, -62, half_pi }, .{ 0, 132, 0 }, .{ 130, 22, half_pi }, .{ -134, 6, half_pi }, .{ 70, -128, 0 }, .{ -40, -126, 0 } };

const Rect = struct { x0: f32, z0: f32, x1: f32, z1: f32 };

fn rot(yaw: f32, x: f32, z: f32) [2]f32 {
    const c = @cos(yaw);
    const s = @sin(yaw);

    return .{ x * c + z * s, -x * s + z * c };
}

fn footprint(l: Bld) Rect {
    const info = api.props.info(kit.of(l.kind));
    const quarter = @abs(@sin(l.yaw)) > 0.7;
    const hx = if (quarter) info.max[2] else info.max[0];
    const hz = if (quarter) info.max[0] else info.max[2];

    return .{ .x0 = l.x - hx, .z0 = l.z - hz, .x1 = l.x + hx, .z1 = l.z + hz };
}

fn rectDist(r: Rect, x: f32, z: f32) f32 {
    const dx = @max(r.x0 - x, 0, x - r.x1);
    const dz = @max(r.z0 - z, 0, z - r.z1);

    return @sqrt(dx * dx + dz * dz);
}

fn roadDist(x: f32, z: f32) f32 {
    const ring = @abs(@max(@abs(x), @abs(z)) - 80);
    const spine = if (z < -80) @abs(x) else 1e9;
    const east = if (x > 80 and z > 30 and z < 90) @abs(z - 60) else 1e9;

    return @min(@min(ring, spine), east);
}

fn pathDist(x: f32, z: f32) f32 {
    const cross = @min(@abs(x), @abs(z));
    const diag = @min(@abs(x - z), @abs(x + z)) * 0.7071;
    const inside = @max(@abs(x), @abs(z)) < 44;

    return if (inside) @min(cross, diag) else @min(@abs(x), @abs(z)) + (if (@max(@abs(x), @abs(z)) > 76) @as(f32, 100) else 0);
}

fn height(x: f32, z: f32) f32 {
    const box = @max(@abs(x), @abs(z));
    const hills = t.smooth(edge - 2, t.half, box) * (7 + t.fbm(x * 0.05, z * 0.05) * 7);
    const berm = t.smooth(96, 120, box) * (1 - t.smooth(128, 140, box)) * 0;

    return hills + berm + (t.fbm(x * 0.02, z * 0.02) - 0.45) * 0.6 * t.smooth(90, 120, box);
}

fn mixc(a: [3]f32, b: [3]f32, q: f32) [3]f32 {
    return api.mix3(a, b, q);
}

fn paving(x: f32, z: f32, fine: f32) [3]f32 {
    const jx = @mod(x, 3);
    const jz = @mod(z, 3);
    const joint = @min(@min(jx, 3 - jx), @min(jz, 3 - jz)) < 0.3;

    if (joint) return .{ 150, 150, 146 };

    return mixc(.{ 196, 194, 186 }, .{ 182, 180, 172 }, fine);
}

fn ground(x: f32, z: f32) api.Rgb {
    const n = t.normal(x, z);
    const vary = 0.95 + t.fbm(x * 0.13, z * 0.13) * 0.1;
    const fine = t.fbm(x * 0.35, z * 0.35);
    const box = @max(@abs(x), @abs(z));
    var c: [3]f32 = mixc(.{ 96, 152, 74 }, .{ 82, 136, 64 }, fine);

    c = mixc(c, .{ 118, 162, 82 }, t.smooth(0.45, 0.62, t.fbm(x * 0.05 + 3, z * 0.05)) * 0.6);

    for (labs) |l| {
        const r = footprint(l);
        const d = rectDist(r, x, z);

        if (d < 5) c = paving(x, z, fine);
    }

    const pd = pathDist(x, z);

    if (pd < 2.6) c = paving(x, z, fine);

    if (box < 9) c = paving(x, z, fine);

    const rd = roadDist(x, z);

    if (rd < 6) {
        c = if (rd > 5.2) .{ 168, 166, 160 } else mixc(.{ 78, 80, 84 }, .{ 68, 70, 74 }, fine);
    }

    if (x > 86 and x < 146 and z > 36 and z < 84) {
        const bay = @mod(x, 3.2) < 0.18 and @abs(z - 60) > 3.5;

        c = if (bay) .{ 214, 214, 206 } else mixc(.{ 78, 80, 84 }, .{ 70, 72, 76 }, fine);
    }

    if ((x > 88 and z < -88) or (x < -88 and z > 30 and z < 80)) c = mixc(.{ 160, 158, 150 }, .{ 146, 144, 136 }, fine);

    if (x < -88 and z < -40 and z > -80) c = mixc(.{ 140, 128, 104 }, .{ 120, 110, 90 }, fine);

    if (box > edge + 1) c = mixc(.{ 88, 132, 66 }, .{ 76, 116, 58 }, fine);

    var occ: f32 = 1;

    for (labs) |l| occ = @min(occ, 0.66 + 0.34 * t.smooth(0, 4, rectDist(footprint(l), x, z)));

    return api.shade(c, vary * occ * (1 + n.x * 0.05 - n.z * 0.03));
}

fn structure(b: *Builder, kind: K, sol: []const [7]f32, x: f32, y: f32, z: f32, yaw: f32) void {
    b.putAt(kit.of(kind), vec(x, y, z), yaw, 1);

    for (sol) |q| {
        const a = rot(yaw, q[1], q[3]);
        const c = rot(yaw, q[4], q[6]);
        const e = rot(yaw, q[1], q[6]);
        const f = rot(yaw, q[4], q[3]);
        const mn = vec(@min(@min(a[0], c[0]), @min(e[0], f[0])) + x, q[2] + y, @min(@min(a[1], c[1]), @min(e[1], f[1])) + z);
        const mx = vec(@max(@max(a[0], c[0]), @max(e[0], f[0])) + x, q[5] + y, @max(@max(a[1], c[1]), @max(e[1], f[1])) + z);

        if (q[0] < 0.5) {
            b.solid(.{ .box = .{ .min = mn, .max = mx } });

            continue;
        }

        const dir: [2]f32 = switch (@as(u8, @intFromFloat(q[0]))) {
            1 => .{ 1, 0 },
            2 => .{ -1, 0 },
            3 => .{ 0, 1 },
            else => .{ 0, -1 },
        };
        const w = rot(yaw, dir[0], dir[1]);
        const rise: api.geom.Rise = if (@abs(w[0]) > @abs(w[1])) (if (w[0] > 0) .pos_x else .neg_x) else (if (w[1] > 0) .pos_z else .neg_z);

        b.solid(.{ .ramp = .{ .min = mn, .max = mx, .rise = rise } });
    }
}

fn solidsOf(kind: K) []const [7]f32 {
    return switch (kind) {
        .lab_big => &S.lab_big,
        .lab_mid => &S.lab_mid,
        else => &S.lab_low,
    };
}

fn roomsOf(kind: K) []const [6]f32 {
    return switch (kind) {
        .lab_big => &R.lab_big,
        .lab_mid => &R.lab_mid,
        else => &R.lab_low,
    };
}

fn put(b: *Builder, kind: K, x: f32, z: f32, yaw: f32) void {
    b.put(kit.of(kind), x, z, yaw, 1);
}

fn putS(b: *Builder, kind: K, x: f32, z: f32, yaw: f32, s: f32) void {
    b.put(kit.of(kind), x, z, yaw, s);
}

fn line(b: *Builder, kind: K, x0: f32, z0: f32, x1: f32, z1: f32, step: f32) void {
    const dx = x1 - x0;
    const dz = z1 - z0;
    const len = @sqrt(dx * dx + dz * dz);
    const n: u32 = @intFromFloat(@max(1, @round(len / step)));
    const yaw = -std.math.atan2(dz, dx);
    var i: u32 = 0;

    while (i < n) : (i += 1) {
        const q = (@as(f32, @floatFromInt(i)) + 0.5) / @as(f32, @floatFromInt(n));

        put(b, kind, x0 + dx * q, z0 + dz * q, yaw);
    }
}

const Room = struct {
    b: *Builder,
    ox: f32,
    oz: f32,
    yaw: f32,
    y: f32,

    fn at(r: Room, kind: K, lx: f32, lz: f32, lyaw: f32) void {
        const p = rot(r.yaw, lx, lz);

        r.b.putAt(kit.of(kind), vec(r.ox + p[0], r.y, r.oz + p[1]), r.yaw + lyaw, 1);
    }
};

fn hash(x: f32, z: f32) f32 {
    const v = @sin(x * 12.9898 + z * 78.233) * 43758.5453;

    return v - @floor(v);
}

fn furnish(b: *Builder, l: Bld) void {
    for (roomsOf(l.kind), 0..) |q, idx| {
        const x0 = q[0];
        const z0 = q[1];
        const x1 = q[2];
        const z1 = q[3];
        const y = q[4];
        const stair = q[5] > 0.5;
        const north = z0 > 0;
        const r: Room = .{ .b = b, .ox = l.x, .oz = l.z, .yaw = l.yaw, .y = y };
        const cx = (x0 + x1) / 2;
        const ext = if (north) z1 else z0;
        const inner = if (north) z0 else z1;
        const face_in: f32 = if (north) pi else 0;
        const face_out: f32 = if (north) 0 else pi;
        const sgn: f32 = if (north) 1 else -1;
        const h = hash(l.x + @as(f32, @floatFromInt(idx)) * 3.1, l.z + y);

        if (stair) {
            r.at(.firepoint, x0 + 0.3, inner + sgn * 0.6, half_pi);
            r.at(.shelf, cx, inner + sgn * 0.45, face_out);

            continue;
        }

        const kind = @as(u32, @intFromFloat(h * 5));

        switch (kind) {
            0 => {
                r.at(.island, cx - 1.6, (z0 + z1) / 2, half_pi);
                r.at(.island, cx + 1.6, (z0 + z1) / 2, half_pi);
                r.at(.stool, cx - 1.6, (z0 + z1) / 2 + 1.3, 0);
                r.at(.stool, cx + 1.0, (z0 + z1) / 2 - 1.3, 0);
                r.at(.wallbench, x0 + 0.5, ext - sgn * 0.45, face_in);
                r.at(.wallbench, x0 + 1.7, ext - sgn * 0.45, face_in);
                r.at(.hood, x1 - 1.0, ext - sgn * 0.7, face_in);
                r.at(.fridge, x0 + 0.5, inner + sgn * 0.5, face_out);
                r.at(.shower, x1 - 0.4, inner + sgn * 0.5, face_out);
            },
            1 => {
                var k: f32 = 0;

                while (k < 4) : (k += 1) r.at(.freezer, x0 + 0.6 + k * 0.95, ext - sgn * 0.5, face_in);

                r.at(.gascab, x1 - 0.7, ext - sgn * 0.4, face_in);
                r.at(.shelf, x1 - 0.4, (z0 + z1) / 2, -half_pi);
                r.at(.dewar, cx, (z0 + z1) / 2 + 0.4, 0);
                r.at(.dewar, cx + 0.8, (z0 + z1) / 2 - 0.3, 0);
                r.at(.cart, cx - 1.6, (z0 + z1) / 2, half_pi);
                r.at(.vented, x0 + 0.4, inner + sgn * 0.5, face_out);
            },
            2 => {
                r.at(.airlock, x0 + 1.0, inner + sgn * 1.0, 0);
                r.at(.bsc, cx + 0.5, ext - sgn * 0.65, face_in);
                r.at(.laminar, x1 - 1.0, ext - sgn * 0.5, face_in);
                r.at(.glovebox, cx, (z0 + z1) / 2, half_pi);
                r.at(.incubator, x1 - 0.5, (z0 + z1) / 2, -half_pi);
                r.at(.autoclave, x1 - 0.5, (z0 + z1) / 2 + sgn * 1.0, -half_pi);
            },
            3 => {
                r.at(.desk, x0 + 1.2, ext - sgn * 0.5, face_in);
                r.at(.desk, x0 + 3.2, ext - sgn * 0.5, face_in);
                r.at(.desk, cx + 1.2, (z0 + z1) / 2, face_in);
                r.at(.stool, x0 + 1.2, ext - sgn * 1.2, 0);
                r.at(.lockers, x1 - 0.5, (z0 + z1) / 2, -half_pi);
                r.at(.shelf, x0 + 0.4, (z0 + z1) / 2, half_pi);
            },
            else => {
                r.at(.optics, cx - 1.2, (z0 + z1) / 2, 0);
                r.at(.optics, cx + 1.2, (z0 + z1) / 2, 0);
                r.at(.sink, x0 + 1.4, ext - sgn * 0.45, face_in);
                r.at(.cart, x1 - 1.0, ext - sgn * 0.5, face_in);
                r.at(.stool, cx, (z0 + z1) / 2 + sgn * 1.2, 0);
            },
        }
    }
}

fn labSite(b: *Builder, l: Bld) void {
    structure(b, l.kind, solidsOf(l.kind), l.x, 0, l.z, l.yaw);
    furnish(b, l);

    const fp = footprint(l);
    const quarter = @abs(@sin(l.yaw)) > 0.7;

    if (quarter) {
        put(b, .hvac, fp.x0 - 1.2, fp.z0 + 3, 0);
        put(b, .hvac, fp.x0 - 1.2, fp.z0 + 4.6, 0);
        put(b, .bush, fp.x1 + 1.2, l.z - 4, 0);
        put(b, .bush, fp.x1 + 1.2, l.z + 4, 0);
        put(b, .bikes, fp.x1 + 2.2, l.z + 8, half_pi);
    } else {
        put(b, .hvac, fp.x0 + 3, fp.z1 + 1.2, 0);
        put(b, .hvac, fp.x0 + 4.6, fp.z1 + 1.2, 0);
        put(b, .cylinder, fp.x1 - 3, fp.z1 + 0.6, 0);
        put(b, .cylinder, fp.x1 - 3.5, fp.z1 + 0.6, 0);
        put(b, .bush, l.x - 5, fp.z0 - 1.2, 0);
        put(b, .bush, l.x + 5, fp.z0 - 1.2, 0);
        put(b, .bikes, l.x + 9, fp.z0 - 2.2, 0);
        put(b, .totem, l.x - 8, fp.z0 - 2.4, 0);
    }
}

fn quad(b: *Builder) void {
    put(b, .fountain, 0, 0, 0);

    const trees = [_][2]f32{ .{ 18, 18 }, .{ -18, 18 }, .{ 18, -18 }, .{ -18, -18 }, .{ 32, 8 }, .{ -32, -8 }, .{ 8, -32 }, .{ -8, 30 }, .{ 30, -26 }, .{ -30, 26 } };

    for (trees) |p| putS(b, .tree, p[0], p[1], p[0], b.rng.range(0.9, 1.15));

    var i: u32 = 0;

    while (i < 8) : (i += 1) {
        const a = @as(f32, @floatFromInt(i)) * std.math.tau / 8 + 0.39;

        put(b, .bench, @sin(a) * 10, @cos(a) * 10, a + pi);
        put(b, .lamp, @sin(a) * 13, @cos(a) * 13, 0);
    }

    const planters = [_][2]f32{ .{ 4, 12 }, .{ -4, 12 }, .{ 4, -12 }, .{ -4, -12 }, .{ 12, 4 }, .{ 12, -4 }, .{ -12, 4 }, .{ -12, -4 } };

    for (planters) |p| put(b, .planter, p[0], p[1], 0);

    line(b, .hedge, 6, 22, 30, 22, 2);
    line(b, .hedge, -30, -22, -6, -22, 2);
    line(b, .hedge, 22, -30, 22, -6, 2);
    line(b, .hedge, -22, 6, -22, 30, 2);
    put(b, .kiosk, 26, 36, pi);
    put(b, .bench, 30, 34, 0);
    put(b, .totem, 3, 40, 0);
    put(b, .totem, -3, -38, pi);
}

fn grounds(b: *Builder) void {
    var x: f32 = -76;

    while (x <= 76) : (x += 16) {
        put(b, .streetlight, x, 74, 0);
        put(b, .streetlight, x, -74, pi);
        put(b, .streetlight, 74, x, -half_pi);
        put(b, .streetlight, -74, x, half_pi);
    }

    var px: f32 = 90;

    while (px < 144) : (px += 6.4) {
        put(b, .bollard, px, 60, 0);

        if (hash(px, 4) < 0.4) put(b, .planter, px + 3.2, 60, 0);
    }

    put(b, .kiosk, 86, 30, 0);
    put(b, .bench, 88, 26, 0);
    put(b, .bench, -86, -26, pi);

    const tanks = [_][2]f32{ .{ 100, -100 }, .{ 106, -100 }, .{ 112, -100 }, .{ 100, -108 }, .{ 106, -108 } };

    for (tanks) |p| put(b, .tank, p[0], p[1], 0);

    put(b, .htank, 124, -96, 0);
    put(b, .htank, 124, -101, 0);
    put(b, .htank, 124, -106, 0);
    put(b, .genset, 132, -120, 0);
    put(b, .genset, 132, -126, 0);
    put(b, .genset, 118, -130, half_pi);
    put(b, .dish, 100, -128, 0.7);
    put(b, .dish, 112, -136, 2.2);
    put(b, .mast, 140, -140, 0);
    line(b, .fence, 92, -90, 146, -90, 2);
    line(b, .fence, 92, -146, 92, -94, 2);

    var sx: f32 = -140;

    while (sx < -92) : (sx += 5) {
        var sz: f32 = -140;

        while (sz < -92) : (sz += 4) {
            if (@abs(sx + 84) < 30 and sz > -116) continue;

            put(b, .solar, sx, sz, 0);
        }
    }

    const dishes = [_][2]f32{ .{ -130, 50 }, .{ -116, 62 }, .{ -104, 44 }, .{ -128, 72 } };

    for (dishes) |p| put(b, .dish, p[0], p[1], p[0] * 0.1);

    put(b, .mast, -100, 70, 0);
    put(b, .mast, -140, 40, 0);
    put(b, .genset, -112, 36, 0);
    line(b, .fence, -146, 32, -92, 32, 2);
    line(b, .fence, -92, 32, -92, 80, 2);
    put(b, .ward, extras[0][0], extras[0][1], extras[0][2]);
    put(b, .ward, extras[1][0], extras[1][1], extras[1][2]);
    put(b, .ward, extras[2][0], extras[2][1], extras[2][2]);
    put(b, .annexe, extras[3][0], extras[3][1], extras[3][2]);
    put(b, .annexe, extras[4][0], extras[4][1], extras[4][2]);
    put(b, .annexe, extras[5][0], extras[5][1], extras[5][2]);
    put(b, .annexe, extras[6][0], extras[6][1], extras[6][2]);
    put(b, .genset, 24, -128, 0);
    put(b, .genset, 120, 126, half_pi);
    put(b, .canopy, 0, -37.5, 0);
    put(b, .kiosk, 0, -136, 0);
    put(b, .bollard, -4, -128, 0);
    put(b, .bollard, 4, -128, 0);
    put(b, .bollard, -6, -128, 0);
    put(b, .bollard, 6, -128, 0);

    var e: f32 = -edge + 1;

    while (e < edge) : (e += 2) {
        if (@abs(e) > 8) put(b, .fence, e, -edge, 0);

        put(b, .fence, e, edge, 0);
        put(b, .fence, -edge, e, half_pi);
        put(b, .fence, edge, e, half_pi);
    }
}

fn greenery(b: *Builder) void {
    var i: u32 = 0;

    while (i < 1400) : (i += 1) {
        const x = b.rng.range(-170, 170);
        const z = b.rng.range(-170, 170);
        const box = @max(@abs(x), @abs(z));

        if (box < 84) continue;

        if (roadDist(x, z) < 8) continue;

        if (x > 86 and x < 146 and z > 36 and z < 84) continue;

        if ((x > 88 and z < -88) or (x < -88 and z < -88) or (x < -88 and z > 30 and z < 80)) continue;

        var blocked = false;

        for (labs) |l| {
            if (rectDist(footprint(l), x, z) < 8) blocked = true;
        }

        for (extras) |q| {
            if (@abs(x - q[0]) < 12 and @abs(z - q[1]) < 12) blocked = true;
        }

        if (blocked) continue;

        const out = box > edge + 2;
        const r = b.rng.next();

        if (out) {
            if (r < 0.55) putS(b, .tree, x, z, r * 9, b.rng.range(0.9, 1.4)) else if (r < 0.8) putS(b, .shrub, x, z, 0, b.rng.range(1.0, 1.6));

            continue;
        }

        if (r < 0.14) putS(b, .tree, x, z, r * 9, b.rng.range(0.85, 1.2)) else if (r < 0.24) putS(b, .tree2, x, z, r * 9, 1.0) else if (r < 0.32) put(b, .shrub, x, z, 0) else if (r < 0.42) put(b, .bush, x, z, 0);
    }

    i = 0;

    while (i < 40) : (i += 1) {
        const a = b.rng.range(0, std.math.tau);
        const rr = b.rng.range(48, 74);
        const x = @sin(a) * rr;
        const z = @cos(a) * rr;
        var blocked = false;

        for (labs) |l| {
            if (rectDist(footprint(l), x, z) < 6) blocked = true;
        }

        if (blocked or roadDist(x, z) < 7 or pathDist(x, z) < 4) continue;

        putS(b, if (b.rng.next() < 0.5) .tree2 else .pit, x, z, a, 1);
    }
}

fn campusFill(b: *Builder) void {
    var d: f32 = -70;

    while (d <= 70) : (d += 7) {
        if (@abs(d) < 10) continue;

        const sides = [_][3]f32{ .{ d, 72.5, 0 }, .{ d, -72.5, pi }, .{ 72.5, d, half_pi }, .{ -72.5, d, -half_pi } };

        for (sides, 0..) |q, k| {
            const h = hash(q[0] + @as(f32, @floatFromInt(k)), q[1]);
            var blocked = false;

            for (labs) |l| {
                if (rectDist(footprint(l), q[0], q[1]) < 4) blocked = true;
            }

            if (blocked) continue;

            if (h < 0.7) {
                put(b, .hedge, q[0] - 1, q[1], q[2]);
                put(b, .hedge, q[0] + 1, q[1], q[2]);
            } else if (h < 0.85) {
                put(b, .bench, q[0], q[1], q[2] + pi);
            }
        }
    }

    var i: u32 = 0;

    while (i < 70) : (i += 1) {
        const x = b.rng.range(-70, 70);
        const z = b.rng.range(-70, 70);
        var blocked = false;

        for (labs) |l| {
            if (rectDist(footprint(l), x, z) < 7) blocked = true;
        }

        if (blocked or pathDist(x, z) < 4 or @max(@abs(x), @abs(z)) < 24 or (@abs(x - 28) < 6 and @abs(z - 35) < 5)) continue;

        const r = b.rng.next();

        if (r < 0.4) putS(b, .tree, x, z, r * 20, b.rng.range(0.8, 1.1)) else if (r < 0.6) put(b, .shrub, x, z, 0) else if (r < 0.8) {
            put(b, .cwall, x, z, 0);
            put(b, .cwall, x + 1, z, 0);
            put(b, .cwall, x + 2, z, 0);
            put(b, .planter, x + 3.2, z, 0);
        } else put(b, .bush, x, z, 0);
    }
}

fn build(b: *Builder) void {
    for (labs) |l| labSite(b, l);

    quad(b);
    grounds(b);
    greenery(b);
    campusFill(b);
}

fn lift(p: api.Vec3) api.Vec3 {
    var y = p.y;

    for (api.world.pieces) |piece| {
        const bb = piece.shape.bounds();

        if (p.x < bb.min.x or p.x > bb.max.x or p.z < bb.min.z or p.z > bb.max.z) continue;

        if (bb.max.y > y and bb.max.y < p.y + 1.5) y = bb.max.y;
    }

    return vec(p.x, y, p.z);
}

fn spots(gpa: std.mem.Allocator) void {
    api.world.autoSpots(gpa, .{ .loot = 48, .vehicles = 0 });

    for (api.world.weapon_spots) |*w| w.* = lift(w.*);

    for (api.world.spawns) |*w| w.* = lift(w.*);

    var list: std.ArrayList(api.world.Spot) = .empty;
    var x: f32 = 94;

    while (x < 142) : (x += 8) {
        list.append(gpa, .{ .pos = vec(x, t.height(x, 70), 70), .yaw = pi }) catch {};
        list.append(gpa, .{ .pos = vec(x + 4, t.height(x + 4, 50), 50), .yaw = 0 }) catch {};
    }

    api.world.vehicle_spots = list.toOwnedSlice(gpa) catch &.{};
}
