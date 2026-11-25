const std = @import("std");
const api = @import("api.zig");
const sk = @import("salvage_kit.zig");

const t = api.terrain;
const kit = sk.kit;
const S = sk.solids;
const K = sk.K;
const vec = api.vec;
const Builder = api.Builder;
const half_pi = api.half_pi;
const pi = std.math.pi;

pub const def: api.Def = .{
    .name = "Scrapyard",
    .note = "Salvage town, junk heaps and farm plots",
    .tint = .{ 96, 176, 150 },
    .ready = true,
    .half = 178,
    .play = 150,
    .facet = 2.0,
    .height = height,
    .ground = ground,
    .build = build,
    .spots = spots,
    .props = &sk.table,
    .palette = .{
        .sun_dir = .{ -0.5, 0.62, -0.6 },
        .sun_tint = .{ 1.18, 1.04, 0.88 },
        .fog = 0.003,
        .fog_color = .{ 0.8, 0.86, 0.84 },
        .zenith = .{ 0.1, 0.34, 0.62 },
    },
    .backdrop = .{ 96, 128, 74 },
    .floor_y = -4,
    .grip = 0.82,
    .tufts = 0.5,
};

const edge: f32 = 147;
const plaza_r: f32 = 17;
const ring: f32 = 58;

const Rect = struct { x0: f32, z0: f32, x1: f32, z1: f32 };

const Mound = struct { x: f32, z: f32, r: f32, h: f32 };

const heaps = [_]Mound{
    .{ .x = 96, .z = -30, .r = 11, .h = 4.5 },
    .{ .x = 124, .z = 20, .r = 13, .h = 6.0 },
    .{ .x = 84, .z = 36, .r = 9, .h = 3.5 },
    .{ .x = 132, .z = -50, .r = 10, .h = 5.0 },
    .{ .x = 108, .z = 52, .r = 8, .h = 3.2 },
    .{ .x = 76, .z = -52, .r = 7, .h = 3.0 },
};

fn rot(yaw: f32, x: f32, z: f32) [2]f32 {
    const c = @cos(yaw);
    const s = @sin(yaw);

    return .{ x * c + z * s, -x * s + z * c };
}

fn heapAt(x: f32, z: f32) f32 {
    var best: f32 = 0;

    for (heaps) |m| {
        const dx = x - m.x;
        const dz = z - m.z;
        const d = @sqrt(dx * dx + dz * dz) / (m.r * (0.85 + t.fbm(x * 0.12 + m.x, z * 0.12) * 0.3));

        best = @max(best, m.h * (1 - t.smooth(0.1, 1.0, d)));
    }

    return best;
}

const ew = [_]f32{ -108, -72, -36, 0, 36, 72, 108 };

fn streetDist(x: f32, z: f32) f32 {
    var d = @abs(x);

    if (@abs(z) < 112) d = @min(d, @abs(@abs(x) - 64) + (if (@abs(x) > 64) @as(f32, 0) else 0));

    for (ew) |sz| {
        const reach: f32 = if (sz == 0) 160 else 68;
        const over = @max(@abs(x) - reach, 0);

        d = @min(d, @abs(z - sz) + over);
    }

    return d;
}

fn height(x: f32, z: f32) f32 {
    const box = @max(@abs(x), @abs(z));
    const hills = t.smooth(edge - 4, t.half, box) * (8 + t.fbm(x * 0.04, z * 0.04) * 8);
    const roll = (t.fbm(x * 0.018 + 3, z * 0.018 - 7) - 0.45) * 5;
    const inner = 1 - t.smooth(100, 130, box);
    const flat = 1 - t.smooth(4, 9, streetDist(x, z));

    return hills + roll * (1 - inner) * (1 - flat * 0.8) + heapAt(x, z);
}

fn mixc(a: [3]f32, b: [3]f32, q: f32) [3]f32 {
    return api.mix3(a, b, q);
}

fn cobble(x: f32, z: f32) [3]f32 {
    const cx = @mod(x, 1.6);
    const cz = @mod(z + (if (@mod(@floor(x / 1.6), 2) == 0) @as(f32, 0) else 0.8), 1.6);
    const seam = @min(@min(cx, 1.6 - cx), @min(cz, 1.6 - cz)) < 0.18;
    const v = t.fbm(x * 0.7, z * 0.7);

    if (seam) return .{ 112, 104, 92 };

    return mixc(.{ 168, 156, 134 }, .{ 146, 134, 114 }, v);
}

const occ_n: usize = 180;
const occ_cell: f32 = 2;
var occ_grid: [occ_n * occ_n]f32 = undefined;
var occ_for: usize = std.math.maxInt(usize);

fn buildOcc() void {
    const pl = api.world.placements;

    @memset(&occ_grid, 1);
    occ_for = pl.len;

    for (pl) |p| {
        const info = api.props.info(p.kind);

        if (info.group == .ground or info.group == .bush) continue;

        if (@abs(p.pos.x) > 170 or @abs(p.pos.z) > 170) continue;

        if (p.pos.y - t.height(p.pos.x, p.pos.z) > 1.0) continue;

        const quarter = @abs(@sin(p.yaw * 2)) < 0.2;
        const turned = @abs(@sin(p.yaw)) > 0.7;
        var hx = (info.max[0] - info.min[0]) * 0.5 * p.scale;
        var hz = (info.max[2] - info.min[2]) * 0.5 * p.scale;

        if (info.group == .tree) {
            hx = 1.2 * p.scale;
            hz = 1.2 * p.scale;
        } else if (!quarter) {
            const r = @max(hx, hz) * 0.8;

            hx = r;
            hz = r;
        } else if (turned) {
            const tmp = hx;

            hx = hz;
            hz = tmp;
        }

        if (hx > 14 or hz > 14) continue;

        const c = rot(p.yaw, (info.max[0] + info.min[0]) * 0.5 * p.scale, (info.max[2] + info.min[2]) * 0.5 * p.scale);
        const cx = p.pos.x + c[0];
        const cz = p.pos.z + c[1];
        const reach: f32 = 1.8;
        const strength: f32 = if (info.group == .rock) 0.25 else 0.42;
        const ix0: i32 = @intFromFloat(@floor((cx - hx - reach + t.half) / occ_cell));
        const ix1: i32 = @intFromFloat(@ceil((cx + hx + reach + t.half) / occ_cell));
        const iz0: i32 = @intFromFloat(@floor((cz - hz - reach + t.half) / occ_cell));
        const iz1: i32 = @intFromFloat(@ceil((cz + hz + reach + t.half) / occ_cell));
        var ix = @max(ix0, 0);

        while (ix <= @min(ix1, @as(i32, occ_n - 1))) : (ix += 1) {
            var iz = @max(iz0, 0);

            while (iz <= @min(iz1, @as(i32, occ_n - 1))) : (iz += 1) {
                const gx = @as(f32, @floatFromInt(ix)) * occ_cell - t.half;
                const gz = @as(f32, @floatFromInt(iz)) * occ_cell - t.half;
                const dx = @max(@abs(gx - cx) - hx, 0);
                const dz = @max(@abs(gz - cz) - hz, 0);
                const d = @sqrt(dx * dx + dz * dz);
                const v = 1 - strength * (1 - t.smooth(0, reach, d));
                const i: usize = @intCast(ix * @as(i32, occ_n) + iz);

                occ_grid[i] = @min(occ_grid[i], v);
            }
        }
    }
}

fn occAt(x: f32, z: f32) f32 {
    if (occ_for != api.world.placements.len) buildOcc();

    const fx = (x + t.half) / occ_cell;
    const fz = (z + t.half) / occ_cell;

    if (fx < 0 or fz < 0 or fx >= @as(f32, occ_n - 1) or fz >= @as(f32, occ_n - 1)) return 1;

    const ix: usize = @intFromFloat(fx);
    const iz: usize = @intFromFloat(fz);
    const ux = fx - @floor(fx);
    const uz = fz - @floor(fz);
    const a = occ_grid[ix * occ_n + iz];
    const b2 = occ_grid[(ix + 1) * occ_n + iz];
    const c = occ_grid[ix * occ_n + iz + 1];
    const d = occ_grid[(ix + 1) * occ_n + iz + 1];

    return (a * (1 - ux) + b2 * ux) * (1 - uz) + (c * (1 - ux) + d * ux) * uz;
}

fn ground(x: f32, z: f32) api.Rgb {
    const n = t.normal(x, z);
    const slope = 1 - n.y;
    const vary = 0.95 + t.fbm(x * 0.13, z * 0.13) * 0.1;
    const fine = t.fbm(x * 0.35, z * 0.35);
    const patch = t.fbm(x * 0.05 + 21, z * 0.05 - 8);
    const box = @max(@abs(x), @abs(z));
    var c: [3]f32 = mixc(.{ 104, 150, 70 }, .{ 84, 132, 58 }, fine);

    c = mixc(c, .{ 136, 158, 76 }, t.smooth(0.45, 0.62, patch) * 0.7);
    c = mixc(c, .{ 124, 104, 74 }, t.smooth(0.6, 0.72, t.fbm(x * 0.09 - 3, z * 0.09 + 1)) * 0.6);

    if (x < -70 and x > -146 and @abs(z) < 60) {
        const row = @mod(z, 4.0);

        c = if (row < 1.6) mixc(.{ 110, 82, 56 }, .{ 96, 70, 48 }, fine) else mixc(.{ 120, 150, 66 }, .{ 100, 136, 56 }, fine);
    }

    if (x > 70 and @abs(z) < 64) c = mixc(c, mixc(.{ 120, 100, 78 }, .{ 100, 82, 64 }, fine), 0.85);

    if (z > 106 and @abs(x) < 130) c = mixc(c, mixc(.{ 140, 134, 120 }, .{ 120, 114, 102 }, fine), 0.75);

    const sd = streetDist(x, z);

    if (sd < 7.5) {
        const k = 1 - t.smooth(4.5, 7.5, sd);
        const rut = 1 - t.smooth(0.25, 0.7, @abs(@abs(sd) - 1.9));
        const dirt = mixc(mixc(.{ 150, 128, 96 }, .{ 132, 112, 84 }, fine), .{ 108, 90, 68 }, rut * 0.55);

        c = mixc(c, dirt, k);
    }

    const r = @sqrt(x * x + z * z);

    if (r < plaza_r) {
        const ring_line = @abs(r - plaza_r + 1.5) < 0.6 or @abs(r - 7) < 0.5;

        c = if (ring_line) .{ 196, 150, 86 } else cobble(x, z);
    }

    const hp = heapAt(x, z);

    if (hp > 0.2) c = mixc(c, mixc(.{ 108, 66, 40 }, .{ 82, 56, 40 }, fine), t.smooth(0.2, 1.2, hp));

    if (slope > 0.15 and box > edge) c = mixc(c, .{ 96, 120, 64 }, 0.5);

    return api.shade(c, vary * occAt(x, z) * (1 + n.x * 0.05 - n.z * 0.03));
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
        .hall_cottage => &S.hall_cottage,
        .terrace => &S.terrace,
        .dome => &S.dome,
        .loft => &S.loft,
        .conserv => &S.conserv,
        .shed => &S.shed,
        .gate => &S.gate,
        .cottage => &S.cottage,
        .silo => &S.silo,
        .water => &S.water,
        .deck => &S.deck,
        .deck_long => &S.deck_long,
        .junk_a => &S.junk_a,
        .junk_b => &S.junk_b,
        .junk_c => &S.junk_c,
        .plates => &S.plates,
        else => &.{},
    };
}

fn house(b: *Builder, kind: K, x: f32, z: f32, yaw: f32) void {
    const info = api.props.info(kit.of(kind));
    const r = @max(info.max[0] - info.min[0], info.max[2] - info.min[2]) * 0.5;
    const y = api.world.lowest(x, z, r) + 0.02;

    structure(b, kind, solidsOf(kind), x, y, z, yaw);
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

const Lot = struct { kind: K, x: f32, z: f32, yaw: f32 };

fn hash(x: f32, z: f32) f32 {
    const v = @sin(x * 12.9898 + z * 78.233) * 43758.5453;

    return v - @floor(v);
}

fn nearestStreetZ(z: f32) f32 {
    var best: f32 = 0;

    for (ew) |sz| {
        if (@abs(sz) > 100) continue;

        if (@abs(z - sz) < @abs(z - best)) best = sz;
    }

    return best;
}

fn town(b: *Builder) void {
    house(b, .water, 0, 0, 0.3);

    const xs = [_]f32{ -52, -40, -28, -16, 16, 28, 40, 52 };
    const zs = [_]f32{ -96, -84, -60, -48, -24, -12, 12, 24, 48, 60, 84, 96 };
    const kinds = [_]K{ .hall_cottage, .cottage, .dome, .loft, .cottage, .conserv, .hall_cottage, .dome, .shed, .cottage, .loft };
    const yard = [_]K{ .crate, .drum, .butt, .planter, .butt, .bale, .panel };

    for (xs) |x| {
        for (zs) |z| {
            if (@sqrt(x * x + z * z) < plaza_r + 8) continue;

            const h = hash(x, z);
            const sz = nearestStreetZ(z);
            const yaw: f32 = if (sz > z) 0 else pi;
            const front = if (sz > z) z + 4.6 else z - 4.6;

            if (h < 0.16) {
                if (h < 0.08) house(b, .deck, x, z + (if (sz > z) @as(f32, 2) else -2), yaw) else {
                    putS(b, .tree, x, z, h * 40, 1.1);
                    put(b, .bush, x + 2.5, z + 1, 0);
                    put(b, .bale, x - 2.4, z - 1.2, h * 9);
                }

                continue;
            }

            const kind = kinds[@as(usize, @intFromFloat(h * 1000)) % kinds.len];

            house(b, kind, x + (hash(z, x) - 0.5) * 1.6, z, yaw);

            const side: f32 = if (hash(x + 1, z) < 0.5) -1 else 1;

            put(b, yard[@as(usize, @intFromFloat(h * 777)) % yard.len], x + side * 5.4, front, h * 6);

            if (h > 0.5) put(b, yard[@as(usize, @intFromFloat(h * 333)) % yard.len], x + side * 5.6, front + (if (sz > z) @as(f32, -1.2) else 1.2), h * 3);

            if (h > 0.75) put(b, .lamp, x - side * 5.2, front + (if (sz > z) @as(f32, 1.2) else -1.2), 0);
        }
    }

    var z: f32 = -100;

    while (z < 100) : (z += 14) {
        if (@abs(z) < plaza_r + 2) continue;

        put(b, .lamp, 5.5, z, 0);
        put(b, .lamp, -5.5, z + 7, 0);
    }

    house(b, .deck_long, 20, 34, 0);
    house(b, .deck_long, -20, -38, pi);
    house(b, .deck, 46, -36, 0);
    house(b, .deck, -46, 38, pi);
    put(b, .washing, -28, 30, 0);
    put(b, .washing, 30, -30, 0);
    put(b, .washing, 40, 66, 0);
    put(b, .washing, -34, -66, 0);

    var a: f32 = 0;

    while (a < std.math.tau) : (a += std.math.tau / 12.0) {
        const x = @sin(a) * (plaza_r - 3);
        const zz = @cos(a) * (plaza_r - 3);

        if (@abs(x) < 4 or @abs(zz) < 4) continue;

        put(b, if (@mod(a, 1.0) < 0.5) .planter else .bush, x, zz, -a);
        put(b, .lamp, @sin(a) * (plaza_r - 1), @cos(a) * (plaza_r - 1), 0);
    }
}

fn scrapyard(b: *Builder) void {
    const piles = [_]Lot{
        .{ .kind = .junk_a, .x = 80, .z = -8, .yaw = 0.4 },
        .{ .kind = .junk_b, .x = 92, .z = 12, .yaw = 1.2 },
        .{ .kind = .junk_c, .x = 104, .z = -12, .yaw = 0 },
        .{ .kind = .junk_a, .x = 116, .z = -26, .yaw = 2.0 },
        .{ .kind = .junk_b, .x = 140, .z = -4, .yaw = 0.3 },
        .{ .kind = .junk_c, .x = 98, .z = -46, .yaw = half_pi },
        .{ .kind = .junk_a, .x = 118, .z = 44, .yaw = 0.8 },
        .{ .kind = .junk_b, .x = 96, .z = 34, .yaw = 2.6 },
        .{ .kind = .junk_c, .x = 136, .z = 40, .yaw = 0 },
        .{ .kind = .junk_a, .x = 140, .z = -36, .yaw = 1.6 },
        .{ .kind = .junk_b, .x = 76, .z = 50, .yaw = 0.5 },
        .{ .kind = .junk_a, .x = 84, .z = -58, .yaw = 2.4 },
    };

    for (piles) |l| {
        const y = t.height(l.x, l.z);

        structure(b, l.kind, solidsOf(l.kind), l.x, y - 0.2, l.z, l.yaw);
    }

    house(b, .shed, 110, 6, half_pi);
    house(b, .shed, 86, -26, 0);
    house(b, .plates, 100, 22, 0);
    house(b, .plates, 128, -16, half_pi);
    house(b, .plates, 112, -40, 0);
    house(b, .plates, 74, 26, half_pi);
    put(b, .arm, 128, -2, 2.2);
    put(b, .platform, 104, 40, 0.6);
    put(b, .arm, 96, -2, 0.3);
    put(b, .arm, 124, 30, 2.0);
    put(b, .platform, 136, 56, half_pi);
    put(b, .platform, 82, 6, 0);
    put(b, .platform, 120, -54, half_pi);
    put(b, .junction, 88, 44, 1.0);
    put(b, .pipe, 132, 18, 0.4);

    var i: u32 = 0;

    while (i < 60) : (i += 1) {
        const x = b.rng.range(70, 144);
        const z = b.rng.range(-60, 60);

        if (heapAt(x, z) > 0.5 or @abs(z) < 5) continue;

        const kinds = [_]K{ .crate, .crate, .drum, .pipe, .junction, .butt, .panel, .rock };

        put(b, b.rng.pick(K, &kinds), x, z, b.rng.range(0, 6.28));
    }

    for (heaps) |m| {
        var k: u32 = 0;

        while (k < 14) : (k += 1) {
            const a = b.rng.range(0, std.math.tau);
            const r = b.rng.range(0.2, 0.85) * m.r;
            const x = m.x + @sin(a) * r;
            const z = m.z + @cos(a) * r;
            const kinds = [_]K{ .crate, .drum, .pipe, .butt, .junction, .rock, .panel };

            b.putAt(kit.of(b.rng.pick(K, &kinds)), vec(x, t.height(x, z) - 0.15, z), b.rng.range(0, 6.28), b.rng.range(0.9, 1.3));
        }
    }

    const more = [_]Lot{
        .{ .kind = .junk_c, .x = 90, .z = -36, .yaw = 0.2 },
        .{ .kind = .junk_a, .x = 110, .z = 24, .yaw = 2.2 },
        .{ .kind = .junk_b, .x = 142, .z = 20, .yaw = 1.0 },
        .{ .kind = .junk_c, .x = 122, .z = -6, .yaw = half_pi },
        .{ .kind = .junk_a, .x = 78, .z = 22, .yaw = 0.7 },
        .{ .kind = .plates, .x = 88, .z = 0, .yaw = half_pi },
        .{ .kind = .plates, .x = 136, .z = -22, .yaw = 0 },
        .{ .kind = .plates, .x = 106, .z = 56, .yaw = 0 },
    };

    for (more) |l| structure(b, l.kind, solidsOf(l.kind), l.x, t.height(l.x, l.z) - 0.2, l.z, l.yaw);

    line(b, .fence, 70, -64, 146, -64, 4);
    line(b, .fence, 70, 64, 146, 64, 4);
}

fn farm(b: *Builder) void {
    var z: f32 = -56;

    while (z < 56) : (z += 4) {
        if (@abs(z) < 7) continue;

        var x: f32 = -142;

        while (x < -72) : (x += 2.2) {
            if (b.rng.next() < 0.55) put(b, .crop, x + b.rng.range(-0.3, 0.3), z + 0.8, b.rng.range(0, 6.28));
        }
    }

    house(b, .conserv, -80, 30, half_pi);
    house(b, .conserv, -80, -30, half_pi);
    house(b, .cottage, -130, 34, 0);
    house(b, .shed, -128, -34, 0);
    house(b, .loft, -104, 50, pi);
    put(b, .spinner, -96, 22, 0.4);
    put(b, .spinner, -118, -22, 1.4);
    put(b, .spinner, -140, 10, 2.4);
    put(b, .junction, -100, -10, 0.3);
    put(b, .pipe, -122, 16, half_pi);
    put(b, .platform, -112, -48, 0);
    put(b, .platform, -90, 8, 0);

    var i: u32 = 0;

    while (i < 14) : (i += 1) {
        const fi: f32 = @floatFromInt(i);

        put(b, .bale, -140 + fi * 5.3, -6.5, b.rng.range(0, 1));
        put(b, .tracker, -142 + fi * 5.5, 60, 0);
    }

    line(b, .fence, -146, 62, -66, 62, 4);
    line(b, .fence, -146, -62, -66, -62, 4);
    line(b, .fence, -70, 8, -70, 58, 4);
    line(b, .fence, -70, -58, -70, -8, 4);
    put(b, .fgate, -70, 34, half_pi);
}

fn industry(b: *Builder) void {
    house(b, .silo, -40, 124, 0);
    house(b, .silo, -34, 124, 0);
    house(b, .silo, -28, 124, 0);
    house(b, .silo, 40, 132, 0);
    house(b, .silo, 46, 132, 0);
    house(b, .water, -60, 132, 0.6);
    house(b, .terrace, 22, 120, pi);
    house(b, .shed, -14, 134, pi);
    house(b, .hall_cottage, 60, 120, half_pi);
    house(b, .hall_cottage, -80, 124, half_pi);
    house(b, .loft, 82, 128, pi);
    house(b, .deck_long, 0, 128, 0);
    house(b, .terrace, -112, 130, pi);
    house(b, .shed, 110, 126, pi);
    put(b, .chimney, 128, 136, 0.4);
    put(b, .platform, 122, 142, 0);
    put(b, .chimney, 28, 128, 0);
    put(b, .chimney, -20, 126, 0);

    var x: f32 = -100;

    while (x < 100) : (x += 4) {
        if (@abs(x) < 7) continue;

        put(b, .pipe, x, 114, 0);
    }

    put(b, .junction, -9, 114, 0);
    put(b, .junction, 9, 114, pi);
    put(b, .catwalk, -50, 118, 0);
    put(b, .catwalk, -46, 118, 0);
    put(b, .catwalk, 70, 118, 0);
    put(b, .catwalk, 74, 118, 0);
    put(b, .platform, 10, 140, half_pi);
    put(b, .butt, -50, 140, 0.3);
    put(b, .junction, 96, 138, 2.2);
    house(b, .shed, -100, 112, 0);
    house(b, .silo, 100, 112, 0);
    house(b, .silo, 106, 112, 0);
    house(b, .deck, 60, 140, pi);
    house(b, .junk_c, -130, 112, 0);
    house(b, .plates, 34, 108, 0);
    house(b, .plates, -66, 108, 0);
    put(b, .platform, -26, 140, half_pi);
    put(b, .platform, 130, 112, 2.6);
}

fn south(b: *Builder) void {
    house(b, .gate, 0, -112, 0);
    line(b, .fence, -146, -112, -6, -112, 4);
    line(b, .fence, 6, -112, 146, -112, 4);
    house(b, .cottage, -30, -126, 0);
    house(b, .dome, -46, -130, 0);
    house(b, .terrace, 30, -128, 0);
    house(b, .conserv, 52, -126, 0);
    house(b, .loft, -64, -128, 0);
    house(b, .cottage, 80, -128, 0);
    house(b, .hall_cottage, -96, -128, half_pi);
    put(b, .washing, -30, -118, 0);
    put(b, .washing, 30, -118, 0);
    put(b, .butt, 10, -120, 0.4);
    put(b, .platform, -12, -122, half_pi);

    var x: f32 = -140;

    while (x < 140) : (x += 8) {
        if (@abs(x) < 10) continue;

        putS(b, .tree, x + b.rng.range(-2, 2), -141 + b.rng.range(-2, 2), b.rng.range(0, 6.28), b.rng.range(0.8, 1.2));
    }
}

fn perimeter(b: *Builder) void {
    var x: f32 = -edge + 2;

    while (x < edge - 1) : (x += 4) {
        if (@abs(x) > 7) {
            put(b, .fence, x, -edge, 0);
            put(b, .fence, x, edge, pi);
            put(b, .fence, -edge, x, half_pi);
            put(b, .fence, edge, x, -half_pi);
        }
    }

    var i: u32 = 0;

    while (i < 220) : (i += 1) {
        const a = b.rng.range(0, std.math.tau);
        const r = b.rng.range(152, 200);
        const x2 = @sin(a) * r;
        const z2 = @cos(a) * r;
        const xx = std.math.clamp(x2, -t.half + 4, t.half - 4);
        const zz = std.math.clamp(z2, -t.half + 4, t.half - 4);

        if (@max(@abs(xx), @abs(zz)) < edge + 3) continue;

        putS(b, if (b.rng.next() < 0.75) .tree else .bush, xx, zz, b.rng.range(0, 6.28), b.rng.range(1.0, 1.8));
    }
}

const reserved = [_]Rect{
    .{ .x0 = -64, .z0 = -104, .x1 = 64, .z1 = 104 },
    .{ .x0 = 66, .z0 = -64, .x1 = 148, .z1 = 64 },
    .{ .x0 = -148, .z0 = -64, .x1 = -66, .z1 = 64 },
};

fn free(x: f32, z: f32, r: f32) bool {
    if (@abs(x) > edge - 6 or @abs(z) > edge - 6) return false;

    if (streetDist(x, z) < 6 + r) return false;

    for (reserved) |q| {
        if (x > q.x0 - r and x < q.x1 + r and z > q.z0 - r and z < q.z1 + r) return false;
    }

    return true;
}

fn cluster(b: *Builder, x: f32, z: f32) void {
    const yaw = @as(f32, @floatFromInt(@as(u32, @intFromFloat(b.rng.range(0, 3.99))))) * half_pi;
    const which = @as(u32, @intFromFloat(b.rng.range(0, 5.99)));
    const c = @cos(yaw);
    const s = @sin(yaw);
    const P = struct { k: K, x: f32, z: f32 };
    const sets = [6][]const P{
        &.{ .{ .k = .tree, .x = 0, .z = 0 }, .{ .k = .bush, .x = 2, .z = 1 }, .{ .k = .rock, .x = -2, .z = 1.5 }, .{ .k = .flower, .x = 1, .z = -1.5 } },
        &.{ .{ .k = .bale, .x = 0, .z = 0 }, .{ .k = .bale, .x = 1.4, .z = 0.2 }, .{ .k = .bale, .x = 0.7, .z = 1.4 }, .{ .k = .butt, .x = -2.2, .z = 0 } },
        &.{ .{ .k = .crate, .x = 0, .z = 0 }, .{ .k = .crate, .x = 1, .z = 0.1 }, .{ .k = .drum, .x = 0.5, .z = 1.2 }, .{ .k = .butt, .x = -1.4, .z = 0.6 } },
        &.{ .{ .k = .tree, .x = 0, .z = 0 }, .{ .k = .tree, .x = 4, .z = 2 }, .{ .k = .bush, .x = 2, .z = -2 } },
        &.{ .{ .k = .rock, .x = 0, .z = 0 }, .{ .k = .rock, .x = 1.6, .z = 0.8 }, .{ .k = .bush, .x = -1.5, .z = 1 }, .{ .k = .tuft, .x = 0.5, .z = -1.4 } },
        &.{ .{ .k = .pipe, .x = 0, .z = 0 }, .{ .k = .junction, .x = 3.4, .z = 0 }, .{ .k = .crate, .x = 0, .z = 1.6 } },
    };

    for (sets[which]) |p| {
        const wx = x + p.x * c + p.z * s;
        const wz = z - p.x * s + p.z * c;

        b.put(kit.of(p.k), wx, wz, yaw + b.rng.range(-0.1, 0.1), b.rng.range(0.9, 1.1));
    }
}

fn clutter(b: *Builder) void {
    var gx: f32 = -140;

    while (gx < 140) : (gx += 9) {
        var gz: f32 = -140;

        while (gz < 140) : (gz += 9) {
            const x = gx + b.rng.range(-3, 3);
            const z = gz + b.rng.range(-3, 3);

            if (!free(x, z, 3)) continue;

            if (b.rng.next() < 0.15) continue;

            cluster(b, x, z);
        }
    }

    var i: u32 = 0;

    while (i < 500) : (i += 1) {
        const x = b.rng.range(-145, 145);
        const z = b.rng.range(-145, 145);

        if (streetDist(x, z) < 6 or heapAt(x, z) > 0.2 or @sqrt(x * x + z * z) < plaza_r + 1) continue;

        if (x > 64 and @abs(z) < 64) continue;

        put(b, if (b.rng.next() < 0.6) .tuft else .flower, x, z, b.rng.range(0, 6.28));
    }

    i = 0;

    while (i < 120) : (i += 1) {
        const x = b.rng.range(-140, 140);
        const z = b.rng.range(-140, 140);

        if (t.normal(x, z).y < 0.985) continue;

        const near = streetDist(x, z) < 6;

        if (!near and b.rng.next() < 0.5) continue;

        b.putAt(kit.of(if (near and b.rng.next() < 0.5) .puddle else .gravel), vec(x, t.height(x, z), z), b.rng.range(0, 6.28), b.rng.range(0.6, 1.2));
    }
}

fn build(b: *Builder) void {
    perimeter(b);
    town(b);
    scrapyard(b);
    farm(b);
    industry(b);
    south(b);
    clutter(b);
}

fn spots(gpa: std.mem.Allocator) void {
    api.world.autoSpots(gpa, .{ .loot = 48, .vehicles = 6 });
}
