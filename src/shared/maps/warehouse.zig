const std = @import("std");
const api = @import("api.zig");
const wk = @import("warehouse_kit.zig");

const t = api.terrain;
const kit = wk.kit;
const S = wk.solids;
const K = wk.K;
const vec = api.vec;
const Vec3 = api.Vec3;
const Builder = api.Builder;
const half_pi = api.half_pi;
const pi = std.math.pi;

pub const def: api.Def = .{
    .name = "Depot",
    .note = "Warehouses, loading docks and container stacks",
    .tint = .{ 186, 150, 100 },
    .ready = true,
    .half = 178,
    .play = 150,
    .facet = 2.0,
    .height = height,
    .ground = ground,
    .build = build,
    .spots = spots,
    .props = &wk.table,
    .palette = .{
        .sun_dir = .{ 0.5, 0.6, 0.62 },
        .sun_tint = .{ 1.16, 1.02, 0.88 },
        .fog = 0.003,
        .fog_color = .{ 0.82, 0.84, 0.86 },
        .zenith = .{ 0.1, 0.28, 0.58 },
    },
    .backdrop = .{ 104, 120, 88 },
    .floor_y = -3,
    .grip = 0.86,
    .tufts = 0.2,
};

const edge: f32 = 147;

const Shed = struct { kind: K, x: f32, z: f32, yaw: f32, w: f32, d: f32, mezz: bool };

const sheds = [_]Shed{
    .{ .kind = .shed_a, .x = -48, .z = 48, .yaw = 0, .w = 64, .d = 32, .mezz = true },
    .{ .kind = .shed_b, .x = 66, .z = 56, .yaw = 0, .w = 48, .d = 28, .mezz = true },
    .{ .kind = .shed_c, .x = -14, .z = -76, .yaw = pi, .w = 72, .d = 24, .mezz = false },
};

const Rect = struct { x0: f32, z0: f32, x1: f32, z1: f32 };

fn rot(yaw: f32, x: f32, z: f32) [2]f32 {
    const c = @cos(yaw);
    const s = @sin(yaw);

    return .{ x * c + z * s, -x * s + z * c };
}

fn shedRect(s: Shed) Rect {
    const info = api.props.info(kit.of(s.kind));
    const flip = @abs(s.yaw - pi) < 0.1;
    const z0 = if (flip) -info.max[2] else info.min[2];
    const z1 = if (flip) -info.min[2] else info.max[2];

    return .{ .x0 = s.x + info.min[0], .z0 = s.z + z0, .x1 = s.x + info.max[0], .z1 = s.z + z1 };
}

fn rectDist(r: Rect, x: f32, z: f32) f32 {
    const dx = @max(r.x0 - x, 0, x - r.x1);
    const dz = @max(r.z0 - z, 0, z - r.z1);

    return @sqrt(dx * dx + dz * dz);
}

const Stack = struct { x: f32, z: f32, yaw: f32, n: u8, kind: K };

const stacks = [_]Stack{
    .{ .x = 112, .z = -130, .yaw = 0, .n = 3, .kind = .box_red },
    .{ .x = 112, .z = -127.4, .yaw = 0, .n = 2, .kind = .box_blue },
    .{ .x = 112, .z = -118, .yaw = 0, .n = 2, .kind = .box_green },
    .{ .x = 112, .z = -106, .yaw = 0, .n = 3, .kind = .box_blue },
    .{ .x = 112, .z = -103.4, .yaw = 0, .n = 1, .kind = .box_red },
    .{ .x = 112, .z = -90, .yaw = 0, .n = 2, .kind = .box_red },
    .{ .x = 112, .z = -78, .yaw = 0, .n = 3, .kind = .box_green },
    .{ .x = 112, .z = -75.4, .yaw = 0, .n = 2, .kind = .box_blue },
    .{ .x = 112, .z = -60, .yaw = 0, .n = 1, .kind = .box_blue },
    .{ .x = 112, .z = -46, .yaw = 0, .n = 2, .kind = .box_red },
    .{ .x = 112, .z = -32, .yaw = 0, .n = 3, .kind = .box_blue },
    .{ .x = 112, .z = -29.4, .yaw = 0, .n = 1, .kind = .box_green },
    .{ .x = 112, .z = -14, .yaw = 0, .n = 2, .kind = .box_green },
    .{ .x = 112, .z = 2, .yaw = 0, .n = 3, .kind = .box_red },
    .{ .x = 126, .z = -134, .yaw = 0, .n = 2, .kind = .box_blue },
    .{ .x = 126, .z = -120, .yaw = 0, .n = 1, .kind = .box_red },
    .{ .x = 126, .z = -117.4, .yaw = 0, .n = 3, .kind = .box_green },
    .{ .x = 126, .z = -100, .yaw = 0, .n = 2, .kind = .box_red },
    .{ .x = 126, .z = -84, .yaw = 0, .n = 3, .kind = .box_blue },
    .{ .x = 126, .z = -66, .yaw = 0, .n = 2, .kind = .box_green },
    .{ .x = 126, .z = -63.4, .yaw = 0, .n = 2, .kind = .box_blue },
    .{ .x = 126, .z = -48, .yaw = 0, .n = 1, .kind = .box_red },
    .{ .x = 126, .z = -36, .yaw = 0, .n = 3, .kind = .box_green },
    .{ .x = 126, .z = -18, .yaw = 0, .n = 2, .kind = .box_blue },
    .{ .x = 126, .z = -15.4, .yaw = 0, .n = 3, .kind = .box_red },
    .{ .x = 126, .z = 4, .yaw = 0, .n = 1, .kind = .box_green },
    .{ .x = 140, .z = -126, .yaw = 0, .n = 3, .kind = .box_green },
    .{ .x = 140, .z = -110, .yaw = 0, .n = 2, .kind = .box_red },
    .{ .x = 140, .z = -94, .yaw = 0, .n = 3, .kind = .box_blue },
    .{ .x = 140, .z = -72, .yaw = 0, .n = 2, .kind = .box_green },
    .{ .x = 140, .z = -52, .yaw = 0, .n = 3, .kind = .box_red },
    .{ .x = 140, .z = -30, .yaw = 0, .n = 2, .kind = .box_blue },
    .{ .x = 140, .z = -8, .yaw = 0, .n = 3, .kind = .box_green },
    .{ .x = 140, .z = 10, .yaw = 0, .n = 2, .kind = .box_red },
    .{ .x = -12, .z = -24, .yaw = half_pi, .n = 2, .kind = .box_blue },
    .{ .x = -9.4, .z = -24, .yaw = half_pi, .n = 1, .kind = .box_red },
    .{ .x = 30, .z = -10, .yaw = 0, .n = 1, .kind = .box_green },
    .{ .x = 30, .z = -7.4, .yaw = 0, .n = 2, .kind = .box_red },
    .{ .x = -60, .z = -8, .yaw = 0, .n = 2, .kind = .box_green },
    .{ .x = -46, .z = -30, .yaw = half_pi, .n = 1, .kind = .box_blue },
    .{ .x = 58, .z = -30, .yaw = half_pi, .n = 3, .kind = .box_blue },
    .{ .x = 4, .z = 6, .yaw = 0, .n = 1, .kind = .box_red },
    .{ .x = -40, .z = 110, .yaw = 0, .n = 2, .kind = .box_office },
    .{ .x = -33.6, .z = 110, .yaw = 0, .n = 2, .kind = .box_office },
    .{ .x = -27.2, .z = 110, .yaw = 0, .n = 1, .kind = .box_office },
    .{ .x = 20, .z = 120, .yaw = half_pi, .n = 2, .kind = .box_office },
};

fn height(x: f32, z: f32) f32 {
    const box = @max(@abs(x), @abs(z));

    return t.smooth(edge - 2, t.half, box) * (7 + t.fbm(x * 0.05, z * 0.05) * 6);
}

fn mixc(a: [3]f32, b: [3]f32, q: f32) [3]f32 {
    return api.mix3(a, b, q);
}

fn ground(x: f32, z: f32) api.Rgb {
    const n = t.normal(x, z);
    const vary = 0.95 + t.fbm(x * 0.13, z * 0.13) * 0.1;
    const fine = t.fbm(x * 0.35, z * 0.35);
    const box = @max(@abs(x), @abs(z));
    var c: [3]f32 = mixc(.{ 92, 94, 96 }, .{ 80, 82, 84 }, fine);

    c = mixc(c, .{ 112, 112, 110 }, t.smooth(0.5, 0.65, t.fbm(x * 0.05 + 9, z * 0.05)) * 0.6);
    c = mixc(c, .{ 64, 66, 68 }, t.smooth(0.62, 0.72, t.fbm(x * 0.12 - 2, z * 0.12 + 5)) * 0.5);

    for (sheds) |s| {
        const r = shedRect(s);
        const d = rectDist(r, x, z);

        if (d < 3) c = mixc(.{ 158, 156, 150 }, .{ 146, 144, 138 }, fine);
    }


    if (x > 104 and z < 36) c = mixc(.{ 132, 128, 118 }, .{ 118, 114, 104 }, fine);

    if (x < -96 and z > -56 and z < 24) c = mixc(.{ 150, 148, 140 }, .{ 136, 134, 126 }, fine);

    if (z > 86 or box > edge + 1 or (z > 78 and @abs(x) > 104)) {
        c = mixc(.{ 96, 140, 70 }, .{ 82, 124, 62 }, fine);

        if (z > 96 and z < 136 and x > -60 and x < 60 and box < edge) c = mixc(.{ 86, 88, 92 }, .{ 76, 78, 82 }, fine);
    }

    var occ: f32 = 1;

    for (sheds) |s| occ = @min(occ, 0.68 + 0.32 * t.smooth(0, 4, rectDist(shedRect(s), x, z)));

    for (stacks) |st| {
        const w: f32 = if (st.yaw > 0.1) 1.4 else 3.2;
        const d: f32 = if (st.yaw > 0.1) 3.2 else 1.4;
        const dx = @max(@abs(x - st.x) - w, 0);
        const dz = @max(@abs(z - st.z) - d, 0);

        occ = @min(occ, 0.72 + 0.28 * t.smooth(0, 2.4, @sqrt(dx * dx + dz * dz)));
    }

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
        .shed_a => &S.shed_a,
        .shed_b => &S.shed_b,
        .shed_c => &S.shed_c,
        .rack => &S.rack,
        .rack_half => &S.rack_half,
        .box_red => &S.box_red,
        .box_blue => &S.box_blue,
        .box_green => &S.box_green,
        .box_office => &S.box_office,
        .drums => &S.drums,
        .blocks => &S.blocks,
        .mast => &S.mast,
        else => &.{},
    };
}

fn put(b: *Builder, kind: K, x: f32, z: f32, yaw: f32) void {
    b.put(kit.of(kind), x, z, yaw, 1);
}

fn putS(b: *Builder, kind: K, x: f32, z: f32, yaw: f32, s: f32) void {
    b.put(kit.of(kind), x, z, yaw, s);
}

fn custom(b: *Builder, kind: K, x: f32, z: f32, yaw: f32) void {
    structure(b, kind, solidsOf(kind), x, t.height(x, z), z, yaw);
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

fn hash(x: f32, z: f32) f32 {
    const v = @sin(x * 12.9898 + z * 78.233) * 43758.5453;

    return v - @floor(v);
}

const Local = struct {
    b: *Builder,
    s: Shed,

    fn at(l: Local, kind: K, lx: f32, y: f32, lz: f32, lyaw: f32) void {
        const p = rot(l.s.yaw, lx, lz);

        l.b.putAt(kit.of(kind), vec(l.s.x + p[0], y, l.s.z + p[1]), l.s.yaw + lyaw, 1);
    }

    fn solid(l: Local, kind: K, lx: f32, y: f32, lz: f32, lyaw: f32) void {
        const p = rot(l.s.yaw, lx, lz);

        structure(l.b, kind, solidsOf(kind), l.s.x + p[0], y, l.s.z + p[1], l.s.yaw + lyaw);
    }
};

fn shedSite(b: *Builder, s: Shed) void {
    structure(b, s.kind, solidsOf(s.kind), s.x, 0, s.z, s.yaw);

    const l: Local = .{ .b = b, .s = s };
    const fl: f32 = 1.21;
    const x0 = -s.w / 2 + 2;
    const x1 = s.w / 2 - (if (s.mezz) @as(f32, 20) else 3);
    var rz = -s.d / 2 + 4.6;
    var row: u32 = 0;

    while (rz < s.d / 2 - 2) : (rz += 1.3) {
        if (@abs(rz) < 3.4) {
            rz = 3.4 - 1.3 + 0.75;
            row = 0;

            continue;
        }

        var x = x0 + 4.2;
        var k: u32 = 0;

        while (x + 4.2 < x1) : (x += 8.4) {
            if (k % 3 == 2) {
                x += 3.0;
                k += 1;

                continue;
            }

            const kind: K = if (hash(x + s.x, rz) < 0.6) .rack else .rack_half;

            l.solid(kind, x, fl, rz, if (row % 2 == 0) 0 else pi);
            k += 1;
        }

        row += 1;

        if (row % 2 == 0) rz += 2.9;
    }

    var d: f32 = -s.w / 2 + 3;

    while (d < s.w / 2 - 3) : (d += 4) {
        l.at(.bumper, d - 0.9, 0.3, -s.d / 2 - 4.03, 0);
        l.at(.bumper, d + 0.9, 0.3, -s.d / 2 - 4.03, 0);
    }

    var i: u32 = 0;

    while (i < 14) : (i += 1) {
        const fi: f32 = @floatFromInt(i);
        const px = -s.w / 2 + 3 + fi * (s.w - 6) / 14;
        const h = hash(px, s.z);

        if (h < 0.35) {
            l.at(.load, px, fl, -s.d / 2 + 2.0, 0);
            l.at(.load, px + 1.1, fl, -s.d / 2 + 2.0, 0);
        } else if (h < 0.55) {
            l.at(.tote, px, fl, -s.d / 2 + 2.0, 0);
        } else if (h < 0.7) {
            l.at(.cage, px, fl, -s.d / 2 + 2.2, 0);
            l.at(.cage, px + 0.9, fl, -s.d / 2 + 2.2, 0);
        } else if (h < 0.8) {
            l.at(.jack, px, fl, -s.d / 2 + 2.4, 0.3);
        }

        if (h > 0.5) {
            l.at(.load, px + 0.4, 1.2, -s.d / 2 - 2.4, 0);
        } else if (h > 0.3) {
            l.at(.pallet, px, 1.2, -s.d / 2 - 2.0, 0);
            l.at(.pallet, px, 1.35, -s.d / 2 - 2.0, 0.1);
        }
    }

    if (s.mezz) {
        const mx = s.w / 2 - 12;

        l.at(.bench, mx + 3, fl + 4.0, -2, 0);
        l.at(.bench, mx + 6, fl + 4.0, -2, 0);
        l.at(.load, mx + 4, fl + 4.0, 3, 0);
        l.at(.cage, mx + 8, fl + 4.0, 4, 0);
        l.at(.bench, mx + 3, fl, 2, pi);
        l.at(.scale, mx - 3, fl, 6, 0);
        l.at(.ladder, mx - 2, fl, -6, 0);
    }

    var sx = -s.w / 2 + 6;

    while (sx < s.w / 2 - 14) : (sx += 12) {
        l.at(.sign, sx, fl + 6.0, 0, 0);
    }
}

fn yard(b: *Builder) void {
    for (stacks) |st| {
        var i: u8 = 0;

        while (i < st.n) : (i += 1) {
            const fi: f32 = @floatFromInt(i);
            const wob = if (i > 0) b.rng.range(-0.03, 0.03) else 0;

            structure(b, st.kind, solidsOf(st.kind), st.x, fi * 2.59, st.z, st.yaw + wob);
        }
    }

    const masts = [_][2]f32{ .{ -70, -30 }, .{ 0, -40 }, .{ 70, -20 }, .{ 30, 16 }, .{ -40, 18 }, .{ 119, -140 }, .{ 119, -60 }, .{ 119, 20 }, .{ -120, -20 } };

    for (masts) |m| custom(b, .mast, m[0], m[1], 0);

    const walls = [_][3]f32{ .{ -80, -16, 0 }, .{ -30, -46, 0 }, .{ 10, -34, half_pi }, .{ 50, -12, 0 }, .{ 80, -44, half_pi }, .{ -20, 0, 0 }, .{ 84, 8, 0 }, .{ -84, 12, half_pi } };

    for (walls) |w| {
        const c = rot(w[2], 5, 0);

        custom(b, .blocks, w[0] - c[0], w[1] - c[1], w[2]);
        custom(b, .blocks, w[0], w[1], w[2]);
        custom(b, .blocks, w[0] + c[0], w[1] + c[1], w[2]);
    }

    const piles = [_][2]f32{ .{ -50, -20 }, .{ 40, -40 }, .{ 20, 4 }, .{ -70, 2 }, .{ 70, 4 }, .{ -10, -44 } };

    for (piles) |p| {
        var k: u32 = 0;

        while (k < 6) : (k += 1) {
            const fk: f32 = @floatFromInt(k);
            const x = p[0] + @mod(fk, 3) * 1.3;
            const z = p[1] + @floor(fk / 3) * 1.1;
            const h = hash(x, z);

            if (h < 0.4) put(b, .load, x, z, 0) else if (h < 0.7) put(b, .tote, x, z, 0) else {
                put(b, .pallet, x, z, 0);
                b.putAt(kit.of(.pallet), vec(x, 0.15, z), 0.05, 1);
                b.putAt(kit.of(.pallet), vec(x, 0.3, z), -0.04, 1);
            }
        }

        custom(b, .drums, p[0] + 4.5, p[1] + 0.5, 0);
    }

    line(b, .barrier, -88, 26, -12, 26, 2);
    line(b, .barrier, 40, 30, 96, 30, 2);
    line(b, .barrier, -56, -52, 28, -52, 2);
}

fn westYard(b: *Builder) void {
    var x: f32 = -142;

    while (x < -100) : (x += 5) {
        var z: f32 = -50;

        while (z < 20) : (z += 4.5) {
            const h = hash(x, z);

            if (h < 0.15) continue;

            if (h < 0.45) {
                put(b, .load, x, z, 0);
                put(b, .load, x + 1.1, z, 0);
                b.putAt(kit.of(.load), vec(x + 0.5, 1.21, z), 0.02, 1);
            } else if (h < 0.7) {
                put(b, .tote, x, z, 0);
                put(b, .tote, x + 1.25, z, 0);
                b.putAt(kit.of(.tote), vec(x + 0.6, 1.16, z), 0, 1);
            } else if (h < 0.85) {
                custom(b, .drums, x, z, 0);
            } else {
                var k: f32 = 0;

                while (k < 6) : (k += 1) b.putAt(kit.of(.pallet), vec(x, k * 0.145, z), k * 0.03, 1);
            }
        }
    }

    line(b, .fence, -146, 24, -98, 24, 2);
    line(b, .fence, -98, -54, -98, 24, 2);
}

fn south(b: *Builder) void {
    const tanks = [_][2]f32{ .{ -130, -130 }, .{ -124, -130 }, .{ -118, -130 }, .{ -130, -122 }, .{ -124, -122 } };

    for (tanks) |p| put(b, .tank, p[0], p[1], 0);

    put(b, .htank, -104, -132, 0);
    put(b, .htank, -104, -126, 0);
    put(b, .genset, -110, -112, 0);
    put(b, .genset, -100, -112, 0);
    line(b, .fence, -146, -106, -94, -106, 2);
    line(b, .fence, -94, -146, -94, -106, 2);
    put(b, .booth, 8, -138, 0);
    put(b, .bollard, 4, -132, 0);
    put(b, .bollard, -4, -132, 0);
    line(b, .barrier, 12, -140, 24, -140, 2);

    var x: f32 = 40;

    while (x < 96) : (x += 6) {
        var z: f32 = -140;

        while (z < -104) : (z += 6) {
            const h = hash(x, z);

            if (h < 0.3) custom(b, .box_blue, x, z, 0) else if (h < 0.55) {
                put(b, .load, x, z, 0);
                put(b, .load, x + 1.1, z, 0);
            } else if (h < 0.7) custom(b, .drums, x, z, 0) else if (h < 0.85) custom(b, .blocks, x, z, half_pi);
        }
    }
}

fn north(b: *Builder) void {
    put(b, .hvac, -44, 106, 0);
    put(b, .hvac, -42.6, 106, 0);
    put(b, .genset, -20, 104, 0);

    var x: f32 = -140;

    while (x < 140) : (x += 9) {
        if (@abs(x) < 64 and x > -64) {
            put(b, .light, x, 96, 0);

            continue;
        }

        putS(b, .tree, x + b.rng.range(-2, 2), 128 + b.rng.range(-8, 8), b.rng.range(0, 6), b.rng.range(0.9, 1.2));
        putS(b, .tree, x + b.rng.range(-2, 2), 104 + b.rng.range(-8, 8), b.rng.range(0, 6), b.rng.range(0.9, 1.2));
    }

    line(b, .hedge, -60, 92, 60, 92, 2);
    line(b, .hedge, -60, 140, 60, 140, 2);

    var e: f32 = -edge + 1;

    while (e < edge) : (e += 2) {
        if (@abs(e - 6) > 8) put(b, .fence, e, -edge, 0);

        put(b, .fence, e, edge, 0);
        put(b, .fence, -edge, e, half_pi);
        put(b, .fence, edge, e, half_pi);
    }

    var i: u32 = 0;

    while (i < 160) : (i += 1) {
        const a = b.rng.range(0, std.math.tau);
        const r = b.rng.range(152, 200);
        const xx = std.math.clamp(@sin(a) * r, -t.half + 4, t.half - 4);
        const zz = std.math.clamp(@cos(a) * r, -t.half + 4, t.half - 4);

        if (@max(@abs(xx), @abs(zz)) < edge + 3) continue;

        putS(b, if (b.rng.next() < 0.7) .tree else .shrub, xx, zz, b.rng.range(0, 6.28), b.rng.range(1.0, 1.5));
    }
}

fn decals(b: *Builder) void {
    var i: u32 = 0;

    while (i < 120) : (i += 1) {
        const x = b.rng.range(-100, 100);
        const z = b.rng.range(-56, 26);
        const k: K = if (b.rng.next() < 0.6) .tracks else .puddle;

        b.putAt(kit.of(k), vec(x, t.height(x, z), z), if (k == .tracks) (if (b.rng.next() < 0.5) @as(f32, 0) else half_pi) else b.rng.range(0, 6), 1);
    }
}

fn free(x: f32, z: f32) bool {
    if (@abs(x) > edge - 8 or @abs(z) > edge - 8) return false;

    for (sheds) |s| {
        if (rectDist(shedRect(s), x, z) < 9) return false;
    }

    for (stacks) |st| {
        if (@abs(st.x - x) < 7 and @abs(st.z - z) < 7) return false;
    }

    if (x > 100 and z < 36) return false;

    if (x < -94 and z > -56 and z < 26) return false;

    if (z > 84) return false;

    if (x < -90 and z < -100) return false;

    if (@abs(x - 6) < 14 and z < -126) return false;

    return true;
}

fn cluster(b: *Builder, x: f32, z: f32) void {
    const h = hash(x, z);
    const yaw: f32 = if (hash(z, x) < 0.5) 0 else half_pi;
    const c = rot(yaw, 1, 0);

    if (h < 0.22) {
        custom(b, if (h < 0.08) .box_red else if (h < 0.15) .box_green else .box_blue, x, z, yaw);
        put(b, .load, x + c[1] * 2.2, z + c[0] * 2.2, yaw);
        put(b, .tote, x + c[1] * 2.2 + c[0] * 1.3, z + c[0] * 2.2 - c[1] * 1.3, yaw);
    } else if (h < 0.42) {
        custom(b, .blocks, x, z, yaw);
        custom(b, .blocks, x + c[0] * 4.8, z + c[1] * 4.8, yaw);
        custom(b, .drums, x + c[1] * 1.8, z + c[0] * 1.8, 0);
    } else if (h < 0.62) {
        var k: f32 = 0;

        while (k < 4) : (k += 1) {
            put(b, .load, x + c[0] * k * 1.15, z + c[1] * k * 1.15, yaw);

            if (k < 2) b.putAt(kit.of(.load), vec(x + c[0] * k * 1.15, 1.21, z + c[1] * k * 1.15), yaw, 1);
        }

        put(b, .jack, x + c[1] * 1.6, z + c[0] * 1.6, yaw + 0.4);
    } else if (h < 0.78) {
        put(b, .tote, x, z, yaw);
        put(b, .tote, x + c[0] * 1.25, z + c[1] * 1.25, yaw);
        put(b, .tote, x + c[1] * 1.1, z + c[0] * 1.1, yaw);
        b.putAt(kit.of(.tote), vec(x, 1.16, z), yaw, 1);
        line(b, .barrier, x - c[1] * 2, z - c[0] * 2, x - c[1] * 2 + c[0] * 6, z - c[0] * 2 + c[1] * 6, 2);
    } else {
        put(b, .cage, x, z, yaw);
        put(b, .cage, x + c[0] * 0.9, z + c[1] * 0.9, yaw);
        put(b, .cage, x + c[0] * 1.8, z + c[1] * 1.8, yaw);
        var k: f32 = 0;

        while (k < 5) : (k += 1) b.putAt(kit.of(.pallet), vec(x + c[1] * 2, k * 0.145, z + c[0] * 2), yaw + k * 0.04, 1);
    }
}

fn fill(b: *Builder) void {
    var gx: f32 = -138;

    while (gx < 138) : (gx += 12) {
        var gz: f32 = -138;

        while (gz < 138) : (gz += 12) {
            const x = gx + (hash(gx, gz) - 0.5) * 5;
            const z = gz + (hash(gz, gx) - 0.5) * 5;

            if (!free(x, z)) continue;

            if (hash(x * 0.3, z * 0.7) < 0.25) continue;

            cluster(b, x, z);
        }
    }
}

fn build(b: *Builder) void {
    for (sheds) |s| shedSite(b, s);

    fill(b);

    yard(b);
    westYard(b);
    south(b);
    north(b);
    decals(b);
}

fn lift(p: Vec3) Vec3 {
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
    const park = [_][3]f32{ .{ -10, 112, 0 }, .{ 0, 112, 0 }, .{ 10, 112, 0 }, .{ 40, 112, pi }, .{ 50, 112, pi }, .{ -20, -10, half_pi }, .{ 40, 10, half_pi }, .{ -60, 14, 0 } };

    for (park) |q| list.append(gpa, .{ .pos = vec(q[0], t.height(q[0], q[1]), q[1]), .yaw = q[2] }) catch {};

    api.world.vehicle_spots = list.toOwnedSlice(gpa) catch &.{};
}
