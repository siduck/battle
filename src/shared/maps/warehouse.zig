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

const Shed = struct { kind: K, x: f32, z: f32, yaw: f32, w: f32, d: f32, mezz: bool, rear: f32, office: f32 };

const sheds = [_]Shed{
    .{ .kind = .shed_a, .x = -48, .z = 48, .yaw = 0, .w = 64, .d = 32, .mezz = true, .rear = 2, .office = 10 },
    .{ .kind = .shed_b, .x = 66, .z = 56, .yaw = 0, .w = 48, .d = 28, .mezz = true, .rear = 1, .office = 8 },
    .{ .kind = .shed_c, .x = -14, .z = -76, .yaw = pi, .w = 72, .d = 24, .mezz = false, .rear = 2, .office = 10 },
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

const stacks = [_]Stack{};

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

    const pads = [_][4]f32{ .{ -56, -50, 12, 20 }, .{ 64, -58, 100, 18 }, .{ -90, -146, -10, -104 }, .{ 36, -146, 100, -104 }, .{ -147, 28, -96, 80 }, .{ 104, 36, 147, 80 } };

    for (pads) |r| {
        if (x > r[0] and x < r[2] and z > r[1] and z < r[3]) c = mixc(.{ 128, 126, 120 }, .{ 114, 112, 106 }, fine);
    }

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
        .cartons => &S.cartons,
        .cartons_b => &S.cartons_b,
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
            l.solid(.cartons, px, fl, -s.d / 2 + 2.2, 0);
            l.solid(.cartons_b, px + 1.3, fl, -s.d / 2 + 2.2, 0);
        } else if (h < 0.8) {
            l.at(.crate, px, fl, -s.d / 2 + 2.4, 0.3);
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
        l.solid(.cartons, mx + 8, fl + 4.0, 4, 0);
        l.at(.bench, mx + 3, fl, 2, pi);
        l.at(.tote, mx - 3, fl, 6, 0);
        l.at(.crate, mx - 2, fl, -6, 0.4);
    }

    const ox0 = -s.w / 2 + s.w / (2 * s.rear) + 3;
    const ox1 = ox0 + s.office + 10;
    var rx = -s.w / 2 + 2.5;
    var slot: u32 = 0;

    while (rx < s.w / 2 - 2) : (rx += 3.6) {
        var near = rx > ox0 - 1.5 and rx < ox1;
        var k: f32 = 0;

        while (k < s.rear) : (k += 1) {
            if (@abs(rx - (-s.w / 2 + s.w * (k + 0.5) / s.rear)) < 3) near = true;
        }

        if (near) continue;

        const wz = s.d / 2 + 1.3;

        switch (slot % 6) {
            0 => {
                l.at(.hvac, rx - 0.7, 0, wz, 0);
                l.at(.hvac, rx + 0.7, 0, wz, 0);
            },
            1 => {
                var q: f32 = 0;

                while (q < 6) : (q += 1) l.at(.pallet, rx, q * 0.145, wz + 0.2, q * 0.03);
            },
            2 => l.at(.skip, rx, 0, wz + 0.4, 0),
            3 => {
                l.at(.pdrum, rx - 0.4, 0, wz, 0);
                l.at(.pdrum, rx + 0.3, 0, wz - 0.1, 0);
                l.at(.pdrum, rx, 0, wz + 0.6, 0);
            },
            4 => l.at(.dumpy, rx, 0, wz, 0.4),
            else => {
                l.solid(.cartons_b, rx - 0.6, 0, wz, 0);
                l.at(.carton, rx + 0.5, 0, wz, 0.4);
            },
        }

        slot += 1;
    }

    l.at(.genset, s.w / 2 + 2.6, 0, -s.d / 4, half_pi);
    l.at(.hvac, s.w / 2 + 1.5, 0, s.d / 4 - 3, 0);
    l.at(.hvac, s.w / 2 + 1.5, 0, s.d / 4 - 4.5, 0);
    l.at(.skip, s.w / 2 + 2.2, 0, s.d / 2 - 2, half_pi);
    l.at(.pdrum, -s.w / 2 - 1.2, 0, -s.d / 4, 0);
    l.at(.pdrum, -s.w / 2 - 1.3, 0, -s.d / 4 + 0.7, 0);
    l.at(.dumpy, -s.w / 2 - 1.5, 0, s.d / 4, 0.2);
    l.at(.crate, -s.w / 2 - 1.4, 0, s.d / 4 + 1.4, 0.5);

    var sx = -s.w / 2 + 6;

    while (sx < s.w / 2 - 14) : (sx += 12) {
        l.at(.sign, sx, fl + 6.0, 0, 0);
    }
}

const boxes = [_]K{ .box_red, .box_blue, .box_green, .box_blue, .box_red, .box_green };

fn boxKind(h: f32) K {
    return boxes[@min(@as(usize, @intFromFloat(h * 6)), 5)];
}

fn stackAt(b: *Builder, kind: K, x: f32, z: f32, yaw: f32, n: u8) void {
    var i: u8 = 0;

    while (i < n) : (i += 1) {
        const fi: f32 = @floatFromInt(i);
        const wob = if (i > 0) b.rng.range(-0.04, 0.04) else 0;

        structure(b, kind, solidsOf(kind), x, t.height(x, z) + fi * 2.59, z, yaw + wob);
    }
}

fn boxRow(b: *Builder, x0: f32, z0: f32, count: u32, along_x: bool, tall: u8) void {
    var i: u32 = 0;

    while (i < count) : (i += 1) {
        const fi: f32 = @floatFromInt(i);
        const x = if (along_x) x0 + fi * 6.25 else x0;
        const z = if (along_x) z0 else z0 + fi * 6.25;
        const h = hash(x * 0.7, z * 1.3);
        const n: u8 = @min(tall, 1 + @as(u8, @intFromFloat(h * 3)));

        stackAt(b, boxKind(hash(z, x)), x, z, if (along_x) 0 else half_pi, n);
    }
}

fn stock(b: *Builder, x0: f32, z0: f32, cols: u32, rows: u32, yaw: f32) void {
    var i: u32 = 0;

    while (i < cols) : (i += 1) {
        var j: u32 = 0;

        while (j < rows) : (j += 1) {
            const lx = @as(f32, @floatFromInt(i)) * 1.15;
            const lz = @as(f32, @floatFromInt(j)) * 0.95;
            const p = rot(yaw, lx, lz);
            const x = x0 + p[0];
            const z = z0 + p[1];
            const y = t.height(x, z);
            const h = hash(x * 3.1, z * 2.7);

            if (h < 0.08) continue;

            if (h < 0.42) {
                b.putAt(kit.of(.load), vec(x, y, z), yaw, 1);

                if (h < 0.25) b.putAt(kit.of(.load), vec(x, y + 1.21, z), yaw + 0.02, 1);
            } else if (h < 0.7) {
                structure(b, if (h < 0.56) .cartons else .cartons_b, solidsOf(if (h < 0.56) .cartons else .cartons_b), x, y, z, yaw + (h - 0.5) * 0.2);
            } else if (h < 0.85) {
                b.putAt(kit.of(.tote), vec(x, y, z), yaw, 1);

                if (h < 0.78) b.putAt(kit.of(.tote), vec(x, y + 1.16, z), yaw, 1);
            } else {
                b.putAt(kit.of(.crate), vec(x, y, z), yaw + 0.1, 1);
            }
        }
    }
}

fn pallets(b: *Builder, x: f32, z: f32, n: u32, yaw: f32) void {
    var k: u32 = 0;
    const y = t.height(x, z);

    while (k < n) : (k += 1) b.putAt(kit.of(.pallet), vec(x, y + @as(f32, @floatFromInt(k)) * 0.145, z), yaw + @as(f32, @floatFromInt(k % 3)) * 0.03, 1);
}

fn rackRun(b: *Builder, x0: f32, z0: f32, count: u32, along_x: bool) void {
    var i: u32 = 0;

    while (i < count) : (i += 1) {
        const fi: f32 = @floatFromInt(i);
        const x = if (along_x) x0 + fi * 8.5 else x0;
        const z = if (along_x) z0 else z0 + fi * 8.5;
        const kind: K = if (hash(x, z) < 0.55) .rack else .rack_half;

        custom(b, kind, x, z, if (along_x) 0 else half_pi);
    }
}

fn walls(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32) void {
    const dx = x1 - x0;
    const dz = z1 - z0;
    const len = @sqrt(dx * dx + dz * dz);
    const n: u32 = @intFromFloat(@max(1, @round(len / 4.8)));
    const yaw = -std.math.atan2(dz, dx);
    var i: u32 = 0;

    while (i < n) : (i += 1) {
        const q = (@as(f32, @floatFromInt(i)) + 0.5) / @as(f32, @floatFromInt(n));

        custom(b, .blocks, x0 + dx * q, z0 + dz * q, yaw);
    }
}

fn loose(b: *Builder, x: f32, z: f32) void {
    putS(b, .carton, x, z, hash(x, z) * 6, 1.5);
    putS(b, .carton, x + 0.8, z + 0.2, hash(z, x) * 6, 1.4);
    b.putAt(kit.of(.carton), vec(x + 0.3, t.height(x, z) + 0.45, z + 0.1), hash(x + 1, z) * 6, 1.3);
    put(b, .cone, x - 1.2, z + 0.8, 0);
}

fn cones(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32, n: u32) void {
    var i: u32 = 0;

    while (i < n) : (i += 1) {
        const q = @as(f32, @floatFromInt(i)) / @as(f32, @floatFromInt(@max(n - 1, 1)));

        put(b, .cone, x0 + (x1 - x0) * q, z0 + (z1 - z0) * q, 0);
    }
}

fn planter(b: *Builder, x: f32, z: f32) void {
    put(b, .hedge, x, z - 1.3, 0);
    put(b, .hedge, x, z + 1.3, 0);
    put(b, .hedge, x - 1.3, z, half_pi);
    put(b, .hedge, x + 1.3, z, half_pi);
    putS(b, .tree, x, z, hash(x, z) * 6, 0.8);
}

fn post(b: *Builder, x: f32, z: f32, yaw: f32) void {
    put(b, .cabin, x, z, yaw);

    const s = rot(yaw, 3.6, 0);
    const k = rot(yaw, -3.4, 2.6);

    put(b, .skip, x + s[0] + k[0] * 0.2, z + s[1] + 3.6, yaw + half_pi);
    put(b, .dumpy, x + k[0], z + k[1], 0.3);
    put(b, .pdrum, x + k[0] + 1.2, z + k[1], 0);
    put(b, .pdrum, x + k[0] + 1.5, z + k[1] + 0.7, 0);
}

fn materials(b: *Builder, x: f32, z: f32) void {
    put(b, .precast, x, z, 0);
    b.putAt(kit.of(.precast), vec(x, t.height(x, z) + 0.9, z), 0.03, 1);
    put(b, .tubes, x, z + 2.2, 0);
    b.putAt(kit.of(.tubes), vec(x, t.height(x, z) + 0.59, z + 2.2), -0.04, 1);
    put(b, .dumpy, x + 3.2, z - 0.4, 0.3);
    put(b, .dumpy, x + 4.4, z - 0.3, 0.1);
    put(b, .dumpy, x + 3.6, z + 0.9, 0.6);
    put(b, .skip, x + 1, z + 5, 0);
    put(b, .pdrum, x - 2.8, z + 0.2, 0);
    put(b, .pdrum, x - 2.8, z + 0.9, 0);
    put(b, .pdrum, x - 3.5, z + 0.5, 0);
}

fn offices(b: *Builder, x: f32, z: f32, yaw: f32) void {
    var i: f32 = 0;

    while (i < 3) : (i += 1) {
        const p = rot(yaw, i * 4.4, 0);

        put(b, .cabin, x + p[0], z + p[1], yaw);
    }

    const g = rot(yaw, -3.6, 2.5);

    put(b, .genset, x + g[0], z + g[1], yaw + half_pi);

    const c = rot(yaw, 13.4, -1.0);

    stackAt(b, .box_office, x + c[0], z + c[1], yaw + half_pi, 2);

    const e = rot(yaw, 13.4, 4.0);

    put(b, .pdrum, x + e[0], z + e[1], 0);
    put(b, .hvac, x + e[0] + 1, z + e[1], yaw);
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

    _ = api.building(b, wk.buildings[0], 44, -22, 0);
    _ = api.building(b, wk.buildings[1], -70, -30, half_pi);
    _ = api.building(b, wk.buildings[1], 13, 58, 0);

    const masts = [_][2]f32{ .{ -84, -4 }, .{ -2, -52 }, .{ 66, -57 }, .{ 30, 22 }, .{ -40, 22 }, .{ 119, -140 }, .{ 119, -60 }, .{ 119, 20 }, .{ -120, -20 }, .{ 98, 30 } };

    for (masts) |m| custom(b, .mast, m[0], m[1], 0);

    block(b, -52, -48, 3, 4, true, 3);
    block(b, -14, -48, 3, 3, true, 2);
    stock(b, -32, -47, 6, 5, 0);
    rackRun(b, -50, -31, 3, true);
    rackRun(b, -50, -27, 3, true);
    boxRow(b, -20, -30, 3, true, 3);
    stock(b, -6, -24, 4, 3, 0);
    block(b, -52, -17, 2, 3, true, 2);
    block(b, -30, -19, 3, 2, true, 3);
    block(b, -44, -4, 4, 2, true, 3);
    stock(b, -10, 2, 4, 4, 0);
    block(b, -52, 8, 2, 2, true, 1);
    boxRow(b, -22, 10, 3, true, 2);
    boxRow(b, 6, -40, 3, false, 2);
    boxRow(b, 6, -12, 2, false, 3);
    custom(b, .drums, -30, -40, 0);
    custom(b, .drums, -2, -8, 0.4);
    custom(b, .drums, -40, 4, 0);
    pallets(b, -24, -23, 7, 0);
    pallets(b, -22.6, -23, 4, 0.2);
    pallets(b, -2, 16, 6, 0);
    walls(b, -50, 18, -36, 18);
    walls(b, -18, 18, -4, 18);
    block(b, 24, 4, 3, 3, true, 2);
    stock(b, 46, 6, 6, 4, 0);
    custom(b, .drums, 56, 0, 0);
    pallets(b, 60, 8, 6, 0);
    put(b, .skip, 50, 16, 0);

    rackRun(b, 76, -48, 6, false);
    rackRun(b, 84, -48, 6, false);
    rackRun(b, 92, -44, 5, false);
    stock(b, 70, 10, 6, 4, 0);
    stock(b, 86, 10, 6, 4, 0);
    walls(b, 70, -54, 96, -54);
    custom(b, .drums, 80, 2, 0);
    custom(b, .drums, 96, -50, 0);
    pallets(b, 71, 0, 8, 0);
    pallets(b, 72.3, 0, 5, 0.1);

    stock(b, 30, -50, 8, 3, 0);
    stock(b, 50, -50, 6, 3, 0);
    custom(b, .drums, 62, -48, 0);
    boxRow(b, 68, -2, 1, true, 2);

    offices(b, -86, 8, 0);
    materials(b, -88, -20);
    materials(b, -86, -44);
    boxRow(b, -60, -50, 2, true, 2);
    boxRow(b, -60, 8, 2, true, 1);
    stock(b, -58, -14, 4, 4, 0);
    walls(b, -94, -54, -60, -54);

    put(b, .gantry, 32, 38, 0);
    put(b, .fueltank, 0, 40, half_pi);
    stackAt(b, .box_blue, 24, 70, half_pi, 2);
    stackAt(b, .box_red, 26.6, 70, half_pi, 1);
    stock(b, -6, 66, 4, 5, 0);
    custom(b, .drums, 32, 52, 0);
    put(b, .skip, 30, 62, half_pi);
    pallets(b, 36, 46, 6, 0);

    block(b, -142, 34, 6, 3, false, 3);
    block(b, -142, 56, 6, 2, false, 2);
    stock(b, -124, 34, 8, 5, 0);
    stock(b, -124, 50, 8, 5, 0);
    rackRun(b, -122, 64, 2, true);
    rackRun(b, -122, 68, 2, true);
    materials(b, -102, 40);
    offices(b, -100, 72, 0);
    custom(b, .drums, -110, 56, 0);
    pallets(b, -106, 30, 7, 0);
    block(b, 108, 40, 6, 3, false, 3);
    block(b, 128, 40, 6, 2, false, 2);
    stock(b, 110, 64, 8, 4, 0);
    stock(b, 124, 64, 8, 4, 0);
    materials(b, 136, 66);
    custom(b, .drums, 100, 50, 0);
    pallets(b, 102, 66, 6, 0);

    var dx: f32 = -72;

    while (dx < -20) : (dx += 8) {
        put(b, .orange, dx, 25, half_pi);

        if (hash(dx, 3) < 0.55) {
            stock(b, dx + 1.6, 23.2, 3, 2, 0);
            topUp(b, dx + 1.6, 23.2, 3, 2);
        }
    }

    dx = 50;

    while (dx < 86) : (dx += 8) {
        put(b, .orange, dx, 35, half_pi);

        if (hash(dx, 5) < 0.55) stock(b, dx + 1.6, 33.2, 3, 2, 0);
    }

    stock(b, 24, -46, 4, 3, 0);
    custom(b, .cartons, 46, -44, 0);
    custom(b, .cartons_b, 47.3, -44, 0);
    loose(b, 36, -42);

    stock(b, -9, 29, 4, 6, 0);
    topUp(b, -9, 29, 4, 6);
    stock(b, 92, 34, 4, 6, 0);
    line(b, .fence, 18, -56, 18, -40, 2);
    post(b, 66, -46, 0);
    stock(b, -95, -36, 6, 4, 0);
    topUp(b, -95, -36, 6, 4);
    stock(b, -95, -28, 6, 3, 0);
    block(b, -95, -10, 2, 1, false, 2);
    line(b, .fence, -78, -56, -78, -42, 2);
    line(b, .fence, -78, -16, -78, 0, 2);
    post(b, -40, -106, half_pi);
    post(b, 92, -108, half_pi);
    custom(b, .mast, -34, -103, 0);
    custom(b, .mast, 86, -103, 0);
    custom(b, .mast, -60, 84, 0);
    custom(b, .mast, 60, 84, 0);
    post(b, -84, 84, half_pi);
    post(b, 40, 84, half_pi);
    post(b, 84, 82, half_pi);
    stock(b, -4, 80, 6, 4, 0);
    planter(b, -40, 86);
    planter(b, -20, 86);
    planter(b, 20, 86);
    planter(b, 60, 88);
    planter(b, -60, 88);
    planter(b, 100, 26);
    planter(b, -100, -60);
    planter(b, 102, -60);
    loose(b, -30, 24);
    loose(b, 8, 26);
    loose(b, 62, 32);
    loose(b, -20, -54);
    loose(b, 40, -56);
    loose(b, 80, -58);
    loose(b, 98, 0);
    loose(b, -92, 20);
    loose(b, 20, 0);
    loose(b, -34, -22);
    loose(b, 10, -100);
    loose(b, -60, -96);
    cones(b, -14, 22, -2, 22, 5);
    cones(b, 36, 28, 46, 28, 4);
    cones(b, 18, -58, 28, -58, 4);
    cones(b, 101, -20, 101, -8, 5);
    cones(b, 10, -132, 10, -120, 5);

    line(b, .barrier, -70, 25, -58, 25, 2);
    line(b, .barrier, -38, 25, -26, 25, 2);
    dx = -42;

    while (dx < 16) : (dx += 8) {
        put(b, .orange, dx, -57.5, half_pi);

        if (hash(dx, 7) < 0.6) {
            stock(b, dx + 1.6, -56.5, 3, 2, 0);
            topUp(b, dx + 1.6, -56.5, 3, 2);
        }
    }

    line(b, .orange, 30, -58, 60, -58, 4);
}

fn topUp(b: *Builder, x0: f32, z0: f32, cols: u32, rows: u32) void {
    var i: u32 = 0;

    while (i < cols) : (i += 1) {
        var j: u32 = 0;

        while (j < rows) : (j += 1) {
            const x = x0 + @as(f32, @floatFromInt(i)) * 1.15;
            const z = z0 + @as(f32, @floatFromInt(j)) * 0.95;
            const h = hash(x * 3.1, z * 2.7);

            if (h >= 0.25 and h < 0.42) b.putAt(kit.of(.load), vec(x, t.height(x, z) + 1.21, z), 0.02, 1);
        }
    }
}

fn westYard(b: *Builder) void {
    var z: f32 = -54;

    while (z < 20) : (z += 6.5) {
        stock(b, -145, z, 10, 3, 0);
        stock(b, -131, z, 10, 3, 0);
        topUp(b, -145, z, 10, 3);
        stock(b, -116, z, 6, 2, 0);
        custom(b, if (hash(z, 3) < 0.5) .cartons else .cartons_b, -107, z + 1, 0);
        custom(b, .cartons_b, -105.6, z + 1, 0);
    }

    custom(b, .drums, -103, -46, 0);
    custom(b, .drums, -103, -20, 0);
    put(b, .skip, -104, 16, half_pi);
    custom(b, .mast, -118, 22, 0);

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
    put(b, .pdrum, 4, -132, 0);
    put(b, .pdrum, -4, -132, 0);
    line(b, .barrier, 12, -140, 24, -140, 2);

    block(b, -86, -142, 4, 5, true, 3);
    block(b, -48, -142, 4, 4, true, 2);
    block(b, 40, -142, 5, 5, true, 3);
    block(b, 78, -142, 3, 5, true, 2);
    stock(b, -50, -122, 8, 4, 0);
    stock(b, -84, -118, 6, 3, 0);
    stock(b, 42, -120, 10, 3, 0);
    stock(b, 66, -120, 6, 3, 0);
    boxRow(b, -24, -116, 2, false, 2);
    block(b, 18, -128, 2, 4, true, 3);
    stock(b, 18, -114, 8, 3, 0);
    stock(b, -6, -120, 5, 4, 0);
    custom(b, .drums, 2, -110, 0);
    pallets(b, -12, -106, 6, 0);
    put(b, .skip, 26, -106, 0);
    boxRow(b, 30, -128, 2, false, 3);
    rackRun(b, 44, -106, 5, true);
    rackRun(b, 44, -98, 5, true);
    offices(b, 50, -80, 0);
    block(b, 76, -96, 3, 4, true, 2);
    materials(b, 90, -78);
    materials(b, -70, -108);
    walls(b, -62, -100, -36, -100);
    custom(b, .drums, -40, -132, 0);
    custom(b, .drums, 30, -114, 0);
    custom(b, .drums, 62, -110, 0.3);
    pallets(b, -18, -126, 7, 0);
    pallets(b, 36, -88, 5, 0);
    line(b, .orange, 32, -66, 60, -66, 4);
}

fn block(b: *Builder, x0: f32, z0: f32, nx: u32, nz: u32, along_x: bool, maxh: u8) void {
    const sx: f32 = if (along_x) 6.2 else 2.5;
    const sz: f32 = if (along_x) 2.5 else 6.2;
    var i: u32 = 0;

    while (i < nx) : (i += 1) {
        var j: u32 = 0;

        while (j < nz) : (j += 1) {
            const x = x0 + @as(f32, @floatFromInt(i)) * sx;
            const z = z0 + @as(f32, @floatFromInt(j)) * sz;
            const h = hash(x * 0.37 + 1, z * 0.91);
            var n: u8 = @intFromFloat(h * @as(f32, @floatFromInt(maxh + 1)));

            if (n > maxh) n = maxh;

            if (n == 0 and hash(z, x * 1.7) < 0.6) n = 1;

            if (n == 0) continue;

            stackAt(b, boxKind(hash(z * 1.3, x)), x, z, if (along_x) 0 else half_pi, n);
        }
    }
}

fn terminal(b: *Builder) void {
    const rows = [_]f32{ -140, -106, -72, -38, -4 };

    for (rows) |zc| {
        block(b, 106, zc, 6, 4, false, 4);
        block(b, 127, zc, 6, 4, false, 3);
    }
}

fn north(b: *Builder) void {
    offices(b, -54, 106, 0);
    walls(b, -50, 122, -12, 122);
    walls(b, 12, 122, 56, 122);
    put(b, .skip, 56, 100, 0);
    put(b, .skip, 56, 132, 0);
    put(b, .dumpy, -58, 132, 0.3);
    put(b, .dumpy, -57, 133.2, 0.8);
    put(b, .booth, 4, 96, half_pi);
    line(b, .shrub, -63, 98, -63, 136, 4);
    line(b, .shrub, 63, 98, 63, 136, 4);
    line(b, .shrub, -50, 116, -14, 116, 4);
    line(b, .shrub, 14, 116, 54, 116, 4);

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

fn paint(b: *Builder, kind: K, x0: f32, z0: f32, x1: f32, z1: f32, step: f32) void {
    const dx = x1 - x0;
    const dz = z1 - z0;
    const len = @sqrt(dx * dx + dz * dz);
    const n: u32 = @intFromFloat(@max(1, @round(len / step)));
    const yaw = std.math.atan2(dx, dz);
    var i: u32 = 0;

    while (i < n) : (i += 1) {
        const q = (@as(f32, @floatFromInt(i)) + 0.5) / @as(f32, @floatFromInt(n));
        const x = x0 + dx * q;
        const z = z0 + dz * q;

        b.putAt(kit.of(kind), vec(x, t.height(x, z), z), yaw, 1);
    }
}

fn decals(b: *Builder) void {
    paint(b, .lane, -96, 22, 100, 22, 5);
    paint(b, .lane, -96, -57, 28, -57, 5);
    paint(b, .lane, 101, -140, 101, 30, 5);
    paint(b, .lane, 16, -52, 16, 20, 5);
    paint(b, .lane, -27, -52, -27, 20, 5);
    paint(b, .lane, 68, -52, 68, 20, 5);
    paint(b, .lane, 12, -146, 12, -62, 5);
    paint(b, .lane, -96, -100, 100, -100, 5);

    var px: f32 = -57;

    while (px < 58) : (px += 3) {
        if (@abs(px) < 6) continue;

        b.putAt(kit.of(.bay), vec(px, t.height(px, 104), 104), 0, 1);
        b.putAt(kit.of(.bay), vec(px, t.height(px, 128), 128), 0, 1);
    }

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

    const zones = [_][4]f32{ .{ -56, -50, 12, 22 }, .{ 20, -42, 68, -2 }, .{ 64, -58, 102, 18 }, .{ -98, -58, -48, 16 }, .{ 24, -60, 66, -44 }, .{ -14, 28, 44, 78 }, .{ -100, 24, 102, 30 }, .{ -90, -146, 100, -94 }, .{ 28, -100, 100, -62 }, .{ -147, 28, -88, 80 }, .{ 96, 36, 147, 80 } };

    for (zones) |r| {
        if (x > r[0] - 3 and x < r[2] + 3 and z > r[1] - 3 and z < r[3] + 3) return false;
    }

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

        put(b, .crate, x + c[1] * 1.6, z + c[0] * 1.6, yaw + 0.4);
    } else if (h < 0.78) {
        put(b, .tote, x, z, yaw);
        put(b, .tote, x + c[0] * 1.25, z + c[1] * 1.25, yaw);
        put(b, .tote, x + c[1] * 1.1, z + c[0] * 1.1, yaw);
        b.putAt(kit.of(.tote), vec(x, 1.16, z), yaw, 1);
        line(b, .barrier, x - c[1] * 2, z - c[0] * 2, x - c[1] * 2 + c[0] * 6, z - c[0] * 2 + c[1] * 6, 2);
    } else if (h < 0.88) {
        materials(b, x, z);
    } else {
        custom(b, .cartons, x, z, yaw);
        custom(b, .cartons_b, x + c[0] * 1.3, z + c[1] * 1.3, yaw);
        loose(b, x + c[0] * 2.8, z + c[1] * 2.8);
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
    terminal(b);
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
    const park = [_][3]f32{ .{ -10, 112, 0 }, .{ 0, 112, 0 }, .{ 10, 112, 0 }, .{ 40, 112, pi }, .{ 50, 112, pi }, .{ -20, -10, half_pi }, .{ 16, -2, 0 }, .{ -60, 14, 0 } };

    for (park) |q| list.append(gpa, .{ .pos = vec(q[0], t.height(q[0], q[1]), q[1]), .yaw = q[2] }) catch {};

    api.world.vehicle_spots = list.toOwnedSlice(gpa) catch &.{};
}
