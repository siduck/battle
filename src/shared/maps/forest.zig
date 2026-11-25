const std = @import("std");
const api = @import("api.zig");
const k = @import("forest_kit.zig");

const t = api.terrain;
const wd = api.world;
const kit = k.kit;
const K = k.K;
const Builder = api.Builder;
const vec = api.vec;
const mix3 = api.mix3;
const hp = api.half_pi;

const water: f32 = -0.9;

pub const def: api.Def = .{
    .name = "Forest Camp",
    .note = "Pine woods, lake camp and river",
    .tint = .{ 96, 160, 88 },
    .ready = true,
    .half = 268,
    .play = 214,
    .facet = 2.5,
    .height = height,
    .ground = ground,
    .build = build,
    .spots = setSpots,
    .props = &k.table,
    .palette = .{
        .sun_dir = .{ 0.52, 0.62, 0.58 },
        .sun_tint = .{ 1.18, 1.05, 0.86 },
        .grade_tint = .{ 1.02, 1.0, 0.95 },
        .grade_sat = 1.2,
        .fog = 0.0021,
        .fog_color = .{ 0.74, 0.84, 0.86 },
        .amb_sky = .{ 0.86, 0.98, 1.14 },
        .amb_ground = .{ 0.76, 0.8, 0.58 },
        .shade_tint = .{ 0.84, 0.94, 1.08 },
        .zenith = .{ 0.1, 0.34, 0.7 },
    },
    .backdrop = .{ 52, 104, 110 },
    .floor_y = water,
    .grip = 0.84,
    .tufts = 0.9,
};

const cell: f32 = 2;
const grid_n = 280;
const grid_half: f32 = 280;

var shade_grid: [grid_n * grid_n]f32 = @splat(0);

const Claim = struct { x: f32, z: f32, r: f32 };

var claims: [1024]Claim = undefined;
var claim_n: usize = 0;

fn claim(x: f32, z: f32, r: f32) void {
    if (claim_n >= claims.len) return;

    claims[claim_n] = .{ .x = x, .z = z, .r = r };
    claim_n += 1;
}

fn open(x: f32, z: f32, r: f32) bool {
    for (claims[0..claim_n]) |c| {
        const dx = c.x - x;
        const dz = c.z - z;

        if (dx * dx + dz * dz < (c.r + r) * (c.r + r)) return false;
    }

    return true;
}

fn splat(x: f32, z: f32, r: f32, strength: f32) void {
    const x0: i32 = @intFromFloat(@floor((x - r + grid_half) / cell));
    const x1: i32 = @intFromFloat(@ceil((x + r + grid_half) / cell));
    const z0: i32 = @intFromFloat(@floor((z - r + grid_half) / cell));
    const z1: i32 = @intFromFloat(@ceil((z + r + grid_half) / cell));
    var j = @max(z0, 0);

    while (j <= @min(z1, grid_n - 1)) : (j += 1) {
        var i = @max(x0, 0);

        while (i <= @min(x1, grid_n - 1)) : (i += 1) {
            const cx = @as(f32, @floatFromInt(i)) * cell - grid_half;
            const cz = @as(f32, @floatFromInt(j)) * cell - grid_half;
            const d = @sqrt((cx - x) * (cx - x) + (cz - z) * (cz - z)) / r;

            if (d >= 1) continue;

            const idx: usize = @intCast(j * grid_n + i);

            shade_grid[idx] = @min(1, shade_grid[idx] + (1 - d) * (1 - d) * strength);
        }
    }
}

fn shadeAt(x: f32, z: f32) f32 {
    const fx = (x + grid_half) / cell;
    const fz = (z + grid_half) / cell;

    if (fx < 0 or fz < 0 or fx >= grid_n - 1 or fz >= grid_n - 1) return 0;

    const i: usize = @intFromFloat(fx);
    const j: usize = @intFromFloat(fz);
    const ux = fx - @as(f32, @floatFromInt(i));
    const uz = fz - @as(f32, @floatFromInt(j));
    const a = std.math.lerp(shade_grid[j * grid_n + i], shade_grid[j * grid_n + i + 1], ux);
    const c = std.math.lerp(shade_grid[(j + 1) * grid_n + i], shade_grid[(j + 1) * grid_n + i + 1], ux);

    return std.math.lerp(a, c, uz);
}

fn segDist(px: f32, pz: f32, s: [4]f32) f32 {
    const dx = s[2] - s[0];
    const dz = s[3] - s[1];
    const l2 = dx * dx + dz * dz;
    const u = std.math.clamp(((px - s[0]) * dx + (pz - s[1]) * dz) / l2, 0, 1);
    const qx = s[0] + dx * u - px;
    const qz = s[1] + dz * u - pz;

    return @sqrt(qx * qx + qz * qz);
}

const lake = [3]f32{ 74, 52, 40 };

fn lakeEdge(x: f32, z: f32) f32 {
    const a = std.math.atan2(z - lake[1], x - lake[0]);
    const wob = 0.82 + 0.3 * t.fbm(@cos(a) * 1.6 + 4, @sin(a) * 1.6 + 2) + 0.06 * @sin(a * 5 + 1);

    return lake[2] * wob;
}

fn lakeDist(x: f32, z: f32) f32 {
    const d = @sqrt((x - lake[0]) * (x - lake[0]) + (z - lake[1]) * (z - lake[1]));

    return d - lakeEdge(x, z);
}

const river = [_][2]f32{ .{ 50, 22 }, .{ 22, -18 }, .{ -14, -40 }, .{ -46, -76 }, .{ -58, -118 }, .{ -48, -160 }, .{ -76, -206 }, .{ -100, -262 } };

const crossings = [_][2]f32{ .{ 6, -30 }, .{ -52, -96 }, .{ -54, -150 } };

fn riverDist(x: f32, z: f32) f32 {
    const wx = x + @sin(z * 0.05) * 3;
    var best: f32 = 1000;
    var i: usize = 0;

    while (i + 1 < river.len) : (i += 1) {
        best = @min(best, segDist(wx, z, .{ river[i][0], river[i][1], river[i + 1][0], river[i + 1][1] }));
    }

    return best;
}

fn riverHalf(x: f32, z: f32) f32 {
    var w: f32 = 5.5 + 1.5 * t.fbm(x * 0.03, z * 0.03);

    for (crossings) |c| {
        const d = @sqrt((x - c[0]) * (x - c[0]) + (z - c[1]) * (z - c[1]));

        w = std.math.lerp(3.2, w, t.smooth(4, 16, d));
    }

    return w;
}

const trails = [_][4]f32{
    .{ -40, 10, 6, -30 },
    .{ 6, -30, 40, -80 },
    .{ 40, -80, 44, -140 },
    .{ -40, 10, -52, -96 },
    .{ -52, -96, -110, -96 },
    .{ -52, -96, -54, -150 },
    .{ -54, -150, 0, -176 },
    .{ 0, -176, 44, -140 },
    .{ -40, 10, -96, 60 },
    .{ -96, 60, -128, 116 },
    .{ -40, 10, 0, 70 },
    .{ 0, 70, 24, 96 },
    .{ 24, 96, 76, 106 },
    .{ 76, 106, 130, 140 },
    .{ 130, 140, 150, 60 },
    .{ 150, 60, 124, 2 },
    .{ 124, 2, 40, -80 },
    .{ -96, 60, -150, -20 },
    .{ -150, -20, -110, -96 },
    .{ 0, 70, -40, 150 },
    .{ -40, 150, 40, 170 },
    .{ 40, 170, 76, 106 },
};

fn trailDist(x: f32, z: f32) f32 {
    const wx = x + @sin(z * 0.07) * 2.2;
    const wz = z + @sin(x * 0.06) * 2.2;
    var best: f32 = 1000;

    for (trails) |s| best = @min(best, segDist(wx, wz, s));

    return best;
}

const clearings = [_][3]f32{
    .{ -40, 10, 30 },
    .{ 40, -140, 26 },
    .{ -112, -96, 22 },
    .{ 130, 140, 22 },
    .{ 18, 82, 16 },
    .{ -128, 118, 16 },
    .{ -150, -20, 14 },
};

fn clearingMask(x: f32, z: f32) f32 {
    var m: f32 = 0;

    for (clearings) |c| {
        const d = @sqrt((x - c[0]) * (x - c[0]) + (z - c[1]) * (z - c[1]));

        m = @max(m, 1 - t.smooth(c[2] * 0.75, c[2] * 1.15, d));
    }

    return m;
}

fn rimEdge(x: f32, z: f32) f32 {
    return @max(@abs(x), @abs(z)) + (t.fbm(x * 0.02 + 5, z * 0.02 - 3) - 0.45) * 24;
}

fn hillAt(x: f32, z: f32, cx: f32, cz: f32, r: f32, h: f32) f32 {
    const d = @sqrt((x - cx) * (x - cx) + (z - cz) * (z - cz));

    return h * (1 - t.smooth(r * 0.25, r, d));
}

fn height(x: f32, z: f32) f32 {
    const n1 = t.fbm(x * 0.016 + 3, z * 0.016 - 7);
    const n2 = t.fbm(x * 0.07, z * 0.07);
    var h = (n1 - 0.4) * 9 + (n2 - 0.45) * 1.6;

    h += hillAt(x, z, -130, 118, 60, 16);
    h += hillAt(x, z, -160, -30, 50, 9) + hillAt(x, z, 150, 70, 55, 8) + hillAt(x, z, 10, 150, 50, 7);

    const cm = clearingMask(x, z);

    h = std.math.lerp(h, @max(h * 0.4 + 0.8, 0.5), cm * 0.8);
    h = @max(h, 0.3 + (n2 - 0.45));

    const e = rimEdge(x, z);
    const m = t.smooth(def.play - 14, def.half - 6, e);
    const ridged = 1 - @abs(2 * t.fbm(x * 0.012 + 9, z * 0.012 + 2) - 1);

    h += m * m * (26 + 44 * ridged + 8 * n2);

    const ld = lakeDist(x, z);
    const shore = t.smooth(10, -6, ld);

    h = std.math.lerp(h, water - 2.2, shore);

    const rd = riverDist(x, z) - riverHalf(x, z);
    const bank = t.smooth(5, -2, rd) * (1 - t.smooth(def.play - 30, def.play + 10, e));

    h = std.math.lerp(h, water - 1.0, bank);

    return h;
}

fn ground(x: f32, z: f32) api.Rgb {
    const n = t.normal(x, z);
    const slope = 1 - n.y;
    const h = t.height(x, z);
    const vary = 0.94 + t.fbm(x * 0.11, z * 0.11) * 0.12;
    const p1 = t.fbm(x * 0.03 + 11, z * 0.03 - 4);
    const p2 = t.fbm(x * 0.09 - 3, z * 0.09 + 8);
    var c = mix3(.{ 82, 134, 52 }, .{ 112, 158, 58 }, t.smooth(0.3, 0.6, p1));

    c = mix3(c, .{ 146, 168, 70 }, t.smooth(0.6, 0.78, p2) * 0.7);
    c = mix3(c, .{ 70, 118, 50 }, t.smooth(0.55, 0.7, t.fbm(x * 0.2, z * 0.2)) * 0.4);

    const under = shadeAt(x, z);

    c = mix3(c, mix3(.{ 74, 92, 44 }, .{ 108, 90, 58 }, t.smooth(0.4, 0.7, p2)), t.smooth(0.15, 0.6, under));

    const td = trailDist(x, z);

    c = mix3(c, .{ 132, 120, 74 }, 1 - t.smooth(2.6, 5, td));
    c = mix3(c, .{ 156, 122, 82 }, 1 - t.smooth(1.4, 3, td));

    const cm = clearingMask(x, z);

    c = mix3(c, .{ 150, 126, 86 }, cm * t.smooth(0.5, 0.75, t.fbm(x * 0.15 + 2, z * 0.15)) * 0.8);

    const wet = @min(lakeDist(x, z), riverDist(x, z) - riverHalf(x, z));

    c = mix3(c, .{ 104, 116, 60 }, 1 - t.smooth(2, 7, wet));
    c = mix3(c, .{ 150, 138, 104 }, 1 - t.smooth(-1.5, 2.5, wet));

    if (h < water + 0.05) c = .{ 96, 104, 84 };

    const rock = mix3(.{ 112, 110, 104 }, .{ 140, 136, 126 }, t.fbm(x * 0.15, z * 0.4));

    const rim = t.smooth(def.play - 14, def.half - 30, rimEdge(x, z));

    c = mix3(c, mix3(c, .{ 96, 124, 62 }, 0.6), t.smooth(0.2, 0.32, slope));
    c = mix3(c, rock, t.smooth(0.38 + rim * 0.14, 0.54 + rim * 0.16, slope + (t.fbm(x * 0.06, z * 0.06) - 0.45) * 0.3 * rim));
    c = mix3(c, .{ 178, 168, 92 }, t.smooth(0.66, 0.8, t.fbm(x * 0.018 + 30, z * 0.018)) * 0.45 * (1 - under));

    const ao = 1 - 0.4 * under;

    return api.shade(c, vary * ao + n.x * 0.04 - n.z * 0.03);
}

fn bld(e: K) api.Building {
    for (k.buildings) |b| {
        if (b.kind == kit.of(e)) return b;
    }

    return k.buildings[0];
}

fn house(b: *Builder, e: K, x: f32, z: f32, yaw: f32) void {
    const info = bld(e);

    claim(x, z, @max(info.w, info.d) * 0.5 + 1);
    _ = api.building(b, info, x, z, yaw);
}

fn put(b: *Builder, e: K, x: f32, z: f32, yaw: f32, s: f32) void {
    b.put(kit.of(e), x, z, yaw, s);
}

fn sink(b: *Builder, e: K, x: f32, z: f32, yaw: f32, s: f32, d: f32) void {
    b.putAt(kit.of(e), vec(x, t.height(x, z) - d, z), yaw, s);
}

fn jit(b: *Builder, a: f32) f32 {
    return b.rng.range(-a, a);
}

fn dry(x: f32, z: f32, pad: f32) bool {
    return lakeDist(x, z) > pad and riverDist(x, z) - riverHalf(x, z) > pad;
}

fn row(b: *Builder, e: K, x0: f32, z0: f32, x1: f32, z1: f32, step: f32, s: f32) void {
    const dx = x1 - x0;
    const dz = z1 - z0;
    const len = @sqrt(dx * dx + dz * dz);
    const n: usize = @intFromFloat(@max(1, @round(len / step)));
    const yaw = std.math.atan2(dx, dz) + hp;
    var i: usize = 0;

    while (i <= n) : (i += 1) {
        const u = @as(f32, @floatFromInt(i)) / @as(f32, @floatFromInt(n));

        put(b, e, x0 + dx * u, z0 + dz * u, yaw, s);
    }
}

fn scatterIn(b: *Builder, kinds: []const K, n: usize, cx: f32, cz: f32, r: f32, smin: f32, smax: f32) void {
    var i: usize = 0;
    var tries: usize = 0;

    while (i < n and tries < n * 12) : (tries += 1) {
        const a = b.rng.range(0, std.math.tau);
        const d = r * @sqrt(b.rng.next());
        const x = cx + @cos(a) * d;
        const z = cz + @sin(a) * d;

        if (!open(x, z, 0.8) or trailDist(x, z) < 2.5 or !dry(x, z, 1)) continue;

        put(b, kinds[i % kinds.len], x, z, b.rng.range(0, std.math.tau), b.rng.range(smin, smax));
        i += 1;
    }
}

fn around(b: *Builder, x: f32, z: f32, yaw: f32, w: f32, d: f32) void {
    const c = @cos(yaw);
    const s = @sin(yaw);
    const kinds = [_]K{ .firewood, .barrel, .bench, .cordwood, .cart, .barrel, .firewood, .table };
    var i: usize = 0;

    while (i < 5) : (i += 1) {
        const side = i % 4;
        const u = b.rng.range(-0.7, 0.7);
        const lx: f32 = switch (side) {
            0 => u * w,
            1 => w + 1.4,
            2 => u * w,
            else => -w - 1.4,
        };
        const lz: f32 = switch (side) {
            0 => d + 1.4,
            1 => u * d,
            2 => -d - 1.4,
            else => u * d,
        };
        const wx = x + lx * c + lz * s;
        const wz = z - lx * s + lz * c;

        if (trailDist(wx, wz) < 2 or !open(wx, wz, 0.5)) continue;

        put(b, kinds[(b.rng.state >> 33) % kinds.len], wx, wz, yaw + @as(f32, @floatFromInt(side)) * hp, 1);
        b.rng.state +%= 7;
    }

    put(b, .bush, x + (w + 1.8) * c, z - (w + 1.8) * s, b.rng.range(0, 6), b.rng.range(0.9, 1.3));
    put(b, .fern, x - (w + 1.5) * c + d * s, z + (w + 1.5) * s + d * c, b.rng.range(0, 6), 1.2);
}

fn camp(b: *Builder) void {
    house(b, .ranger, -40, 34, std.math.pi);
    around(b, -40, 34, std.math.pi, 4, 2.7);
    house(b, .logcabin, -66, 14, hp);
    around(b, -66, 14, hp, 4.2, 4.9);
    house(b, .woodshed, -62, -8, hp);
    house(b, .outhouse, -58, 34, std.math.pi);
    house(b, .leanto, -16, 26, std.math.pi);
    put(b, .kiosk, -28, -6, 0.5, 1);
    put(b, .sign, -36, -12, 0.3, 1);
    put(b, .well, -48, 4, 0, 1);

    put(b, .firepit, -38, 8, 0, 1);
    put(b, .tripod, -38, 8, 0.4, 1);
    put(b, .bench, -38, 12.4, std.math.pi, 1);
    put(b, .bench, -38, 3.6, 0, 1);
    put(b, .bench, -42.4, 8, hp, 1);
    put(b, .bench, -33.6, 8, -hp, 1);
    claim(-38, 8, 5);

    for ([_][3]f32{ .{ -22, 8, 0.2 }, .{ -26, 16, -0.1 }, .{ -52, 22, 1.6 } }) |p| {
        put(b, .table, p[0], p[1], p[2], 1);
        put(b, .cooler, p[0] + 1.4, p[1] + 1.4, 0.3, 1);
    }

    put(b, .lights, -38, 16, 0, 1);
    put(b, .lights, -30, 12, hp, 1);
    put(b, .pickup, -18, -6, 2.6, 1);
    put(b, .van, -70, -16, 0.3, 1);

    for ([_][3]f32{ .{ -20, 40, 0 }, .{ -12, 44, 0.3 }, .{ -4, 38, -0.4 } }) |p| {
        put(b, .walltent, p[0], p[1], p[2] + std.math.pi, 1);
        claim(p[0], p[1], 3);
    }

    for ([_][2]f32{ .{ -36, 56 }, .{ -46, -14 }, .{ -24, -16 }, .{ -70, 36 }, .{ -14, 4 } }) |p| put(b, .lantern, p[0], p[1], 0, 1);

    row(b, .fence, -78, -24, -78, 40, 2.6, 1);
    put(b, .gate, -78, 8, hp, 1);
}

fn lakeshore(b: *Builder) void {
    var a: f32 = 0;

    while (a < std.math.tau) : (a += 0.09) {
        const r = lakeEdge(lake[0] + @cos(a) * 30, lake[1] + @sin(a) * 30);
        const x = lake[0] + @cos(a) * (r + 1.5);
        const z = lake[1] + @sin(a) * (r + 1.5);
        const roll = b.rng.next();

        if (!open(x, z, 1)) continue;

        if (roll < 0.35) {
            put(b, .reeds, x, z, a + hp, b.rng.range(0.9, 1.3));
        } else if (roll < 0.6) {
            put(b, .cattail, x + jit(b, 1), z + jit(b, 1), b.rng.range(0, 6), b.rng.range(0.9, 1.4));
            put(b, .cattail, x + jit(b, 1.5), z + jit(b, 1.5), b.rng.range(0, 6), b.rng.range(0.9, 1.4));
        } else if (roll < 0.72) {
            sink(b, .rock, x, z, b.rng.range(0, 6), b.rng.range(1, 1.6), 0.3);
        }

        if (b.rng.next() < 0.4) {
            const lr = r - b.rng.range(3, 10);

            b.putAt(kit.of(.lily), vec(lake[0] + @cos(a) * lr, water + 0.03, lake[1] + @sin(a) * lr), b.rng.range(0, 6), b.rng.range(0.8, 1.4));
        }
    }

    const dock_a: f32 = 2.5;
    const dr = lakeEdge(lake[0] + @cos(dock_a) * 30, lake[1] + @sin(dock_a) * 30);
    var i: usize = 0;

    while (i < 6) : (i += 1) {
        const rr = dr + 2 - @as(f32, @floatFromInt(i)) * 3.2;
        const x = lake[0] + @cos(dock_a) * rr;
        const z = lake[1] + @sin(dock_a) * rr;
        const yaw = std.math.atan2(@cos(dock_a), @sin(dock_a));

        b.putAt(kit.of(.dock), vec(x, water + 0.45, z), yaw + hp, 1);
        api.box(b, x - 1.7, water - 3, z - 1.7, x + 1.7, water + 1.35, z + 1.7);
    }

    const tip_x = lake[0] + @cos(dock_a) * (dr - 18);
    const tip_z = lake[1] + @sin(dock_a) * (dr - 18);

    b.putAt(kit.of(.rowboat), vec(tip_x + 3, water + 0.1, tip_z + 1), 0.4, 1);
    b.putAt(kit.of(.canoe), vec(tip_x - 2, water + 0.1, tip_z - 3.5), 1.2, 1);
    b.putAt(kit.of(.raft), vec(lake[0] + 4, water - 0.4, lake[1] - 6), 0.3, 1);
    b.putAt(kit.of(.raft), vec(lake[0] + 14, water - 0.4, lake[1] + 10), 1.1, 1);

    const shore_x = lake[0] + @cos(dock_a) * (dr + 8);
    const shore_z = lake[1] + @sin(dock_a) * (dr + 8);

    put(b, .rack, shore_x, shore_z + 4, 0.2, 1);
    put(b, .canoe, shore_x + 3, shore_z - 3, 1.4, 1);
    put(b, .rowboat, shore_x - 3, shore_z - 4, 2.2, 1);
    put(b, .barrel, shore_x - 4, shore_z + 2, 0, 1);
    put(b, .barrel, shore_x - 4.8, shore_z + 3, 0, 1);
    claim(shore_x, shore_z, 6);

    house(b, .washhouse, 18, 82, 0);
    around(b, 18, 82, 0, 4.8, 2.4);
    house(b, .aframe, 112, 98, -2.4);
    house(b, .porch, 128, 16, -hp);
    around(b, 128, 16, -hp, 5, 5);
    put(b, .trailer, 116, 30, 0.6, 1);
    put(b, .dome, 104, 18, 0.3, 1);
    put(b, .dome, 100, 26, -0.6, 1);
    put(b, .firepit, 108, 28, 0, 1);
    put(b, .bench, 108, 32, std.math.pi, 1);
    put(b, .tent, 30, 104, 0.5, 1);
    put(b, .tent, 36, 98, 1.2, 1);
    put(b, .table, 26, 96, 0.2, 1);
}

fn logging(b: *Builder) void {
    house(b, .woodshed, 40, -126, 0);
    house(b, .hiproof, 56, -148, -hp);
    around(b, 56, -148, -hp, 4.8, 2.4);
    put(b, .pickup, 30, -150, 0.5, 1);
    put(b, .cart, 44, -158, 1, 1);

    var i: usize = 0;

    while (i < 7) : (i += 1) {
        const fi = @as(f32, @floatFromInt(i));

        put(b, .cordwood, 22 + fi * 2.7, -134, 0, 1);
        put(b, .fallen, 26 + fi * 1.2, -142 - fi * 1.8, 0.1 + fi * 0.2, 1.1);
    }

    scatterIn(b, &.{ .stump, .stump, .roots, .firewood }, 30, 40, -140, 26, 0.8, 1.2);
}

fn campground(b: *Builder) void {
    const pitches = [_][3]f32{ .{ -100, -84, 0.3 }, .{ -114, -82, -0.2 }, .{ -124, -92, 1.4 }, .{ -120, -106, 2.1 }, .{ -104, -110, 2.8 }, .{ -96, -100, -1.2 } };

    for (pitches, 0..) |p, i| {
        const e: K = if (i % 3 == 0) .walltent else if (i % 3 == 1) .tent else .dome;

        put(b, e, p[0], p[1], p[2], 1);
        claim(p[0], p[1], 3);
        put(b, .table, p[0] + 3 * @cos(p[2]), p[1] - 3 * @sin(p[2]), p[2], 1);
        put(b, .cooler, p[0] - 2.5 * @cos(p[2]), p[1] + 2.5 * @sin(p[2]), 0.4, 1);
    }

    put(b, .firepit, -110, -96, 0, 1);
    put(b, .tripod, -110, -96, 0.2, 1);
    claim(-110, -96, 3);
    house(b, .outhouse, -132, -110, hp);
    put(b, .kiosk, -98, -92, 0.8, 1);
    put(b, .van, -132, -78, 0.9, 1);
    put(b, .trailer, -90, -118, 2.4, 1);
    put(b, .lights, -110, -88, 0, 1);
}

fn outposts(b: *Builder) void {
    house(b, .lookout, -128, 118, 0.3);
    around(b, -128, 118, 0.3, 3.4, 3.4);
    scatterIn(b, &.{ .spire, .boulder, .rock }, 16, -128, 118, 22, 0.9, 1.4);

    house(b, .logcabin, 128, 146, std.math.pi);
    house(b, .porch, 146, 130, -hp);
    house(b, .woodshed, 114, 136, hp);
    around(b, 128, 146, std.math.pi, 4.2, 4.9);
    around(b, 146, 130, -hp, 5, 5);
    put(b, .pickup, 134, 124, 1.2, 1);
    put(b, .well, 122, 128, 0, 1);

    house(b, .leanto, -150, -20, hp);
    scatterIn(b, &.{ .spire, .boulder, .rock, .spire }, 26, -160, -30, 34, 0.9, 1.6);
    put(b, .firepit, -144, -22, 0, 1);

    house(b, .hiproof, -40, 150, 0);
    around(b, -40, 150, 0, 4.8, 2.4);
    house(b, .aframe, 40, 170, std.math.pi);

    for (crossings) |c| {
        const seg = blk: {
            var best: usize = 0;
            var bd: f32 = 1e9;
            var i: usize = 0;

            while (i + 1 < river.len) : (i += 1) {
                const d = segDist(c[0], c[1], .{ river[i][0], river[i][1], river[i + 1][0], river[i + 1][1] });

                if (d < bd) {
                    bd = d;
                    best = i;
                }
            }

            break :blk best;
        };
        const dx = river[seg + 1][0] - river[seg][0];
        const dz = river[seg + 1][1] - river[seg][1];
        const yaw = std.math.atan2(dx, dz);
        const y = @max(t.height(c[0] + @cos(yaw) * 6, c[1] - @sin(yaw) * 6), t.height(c[0] - @cos(yaw) * 6, c[1] + @sin(yaw) * 6));

        b.putAt(kit.of(.bridge), vec(c[0], y - 0.35, c[1]), yaw, 1);
        api.box(b, c[0] - 2.6, water - 2, c[1] - 2.6, c[0] + 2.6, y + 0.15, c[1] + 2.6);
        claim(c[0], c[1], 6);
        put(b, .sign, c[0] + 6, c[1] + 5, yaw, 1);
    }
}

fn forestDensity(x: f32, z: f32) f32 {
    const e = rimEdge(x, z);

    if (e > def.half - 12) return 0;

    if (1 - t.normal(x, z).y > 0.55) return 0.15;

    if (!dry(x, z, 3)) return 0;

    if (trailDist(x, z) < 4) return 0;

    const cm = clearingMask(x, z);
    const patch = t.smooth(0.3, 0.55, t.fbm(x * 0.022 + 11, z * 0.022 + 4));
    const glade = 1 - t.smooth(0.62, 0.7, t.fbm(x * 0.05 - 3, z * 0.05 + 7)) * 0.8;

    return (0.12 + 0.88 * patch * patch) * (1 - cm) * glade + t.smooth(def.play - 20, def.play + 10, e) * 0.7;
}

fn treeKind(b: *Builder, x: f32, z: f32) K {
    const conifer = @max(t.smooth(0.35, 0.65, t.fbm(x * 0.012 - 20, z * 0.012 + 5)), t.smooth(def.play - 30, def.play, rimEdge(x, z)) * 0.8);
    const roll = b.rng.next();

    if (roll < 0.04) return .dead;

    if (b.rng.next() < conifer) {
        return if (roll < 0.45) .pine else if (roll < 0.75) .pines else .young;
    }

    return if (roll < 0.52) .oak else if (roll < 0.8) .birch else if (roll < 0.87) .maple else .young;
}

fn forest(b: *Builder) void {
    const step: f32 = 6.5;
    var z: f32 = -def.half + 8;

    while (z < def.half - 8) : (z += step) {
        var x: f32 = -def.half + 8;

        while (x < def.half - 8) : (x += step) {
            const px = x + b.rng.range(-2.6, 2.6);
            const pz = z + b.rng.range(-2.6, 2.6);
            const d = forestDensity(px, pz);

            if (b.rng.next() > d) continue;

            if (!open(px, pz, 2.2)) continue;

            const e = treeKind(b, px, pz);
            const s: f32 = switch (e) {
                .oak => b.rng.range(1.3, 2.1),
                .birch => b.rng.range(1.2, 1.7),
                .maple => b.rng.range(1.3, 1.9),
                .pine => b.rng.range(1.0, 1.6),
                .pines => b.rng.range(0.9, 1.3),
                .young => b.rng.range(1.0, 1.6),
                else => b.rng.range(1.2, 1.5),
            };

            put(b, e, px, pz, b.rng.range(0, std.math.tau), s);

            const under = b.rng.next();

            if (under < 0.3) {
                put(b, .fern, px + jit(b, 3), pz + jit(b, 3), b.rng.range(0, 6), b.rng.range(0.9, 1.5));
            } else if (under < 0.5) {
                put(b, .bush, px + jit(b, 3.5), pz + jit(b, 3.5), b.rng.range(0, 6), b.rng.range(0.8, 1.4));
            } else if (under < 0.56) {
                put(b, .fallen, px + jit(b, 3), pz + jit(b, 3), b.rng.range(0, 6), b.rng.range(0.8, 1.1));
            } else if (under < 0.62) {
                put(b, .stump, px + jit(b, 3), pz + jit(b, 3), b.rng.range(0, 6), 1);
            } else if (under < 0.68) {
                put(b, .toadstool, px + jit(b, 2), pz + jit(b, 2), b.rng.range(0, 6), b.rng.range(0.8, 1.3));
                put(b, .toadstool, px + jit(b, 2), pz + jit(b, 2), b.rng.range(0, 6), b.rng.range(0.6, 1));
            } else if (under < 0.74) {
                sink(b, .boulder, px + jit(b, 4), pz + jit(b, 4), b.rng.range(0, 6), b.rng.range(0.7, 1.3), 0.3);
            } else if (under < 0.78) {
                put(b, .roots, px + jit(b, 2), pz + jit(b, 2), b.rng.range(0, 6), 1);
            }
        }
    }
}

fn meadow(b: *Builder) void {
    var i: usize = 0;

    while (i < 2600) : (i += 1) {
        const x = b.rng.range(-def.play, def.play);
        const z = b.rng.range(-def.play, def.play);

        if (!dry(x, z, 0.5) or trailDist(x, z) < 1.6 or !open(x, z, 0.3)) continue;

        const roll = b.rng.next();

        if (roll < 0.5) {
            put(b, .tuft, x, z, b.rng.range(0, 6), b.rng.range(0.8, 1.4));
        } else if (roll < 0.8) {
            put(b, .flower, x, z, b.rng.range(0, 6), b.rng.range(0.8, 1.3));
        } else if (roll < 0.93) {
            put(b, .fern, x, z, b.rng.range(0, 6), b.rng.range(0.8, 1.3));
        } else {
            put(b, .stone, x, z, b.rng.range(0, 6), b.rng.range(0.7, 1.2));
        }
    }

    i = 0;

    while (i < 160) : (i += 1) {
        const x = b.rng.range(-def.play + 6, def.play - 6);
        const z = b.rng.range(-def.play + 6, def.play - 6);

        if (!dry(x, z, 2) or trailDist(x, z) < 3.5 or !open(x, z, 2.5)) continue;

        const roll = b.rng.next();

        if (roll < 0.4) {
            sink(b, .boulder, x, z, b.rng.range(0, 6), b.rng.range(1, 1.7), 0.35);
            put(b, .bush, x + 2, z + 1, 0, 1);
        } else if (roll < 0.65) {
            put(b, .fallen, x, z, b.rng.range(0, 6), b.rng.range(1, 1.3));
            put(b, .fern, x + 1, z + 1.5, 0, 1.2);
        } else if (roll < 0.8) {
            sink(b, .spire, x, z, b.rng.range(0, 6), b.rng.range(0.7, 1.1), 0.4);
            sink(b, .rock, x + 2, z - 1, b.rng.range(0, 6), 1.2, 0.2);
        } else {
            put(b, .firewood, x, z, b.rng.range(0, 6), 1);
            put(b, .stump, x + 1.8, z + 0.6, 0, 1);
        }

        claim(x, z, 2);
    }
}

fn trailside(b: *Builder) void {
    for (trails, 0..) |s, ti| {
        const dx = s[2] - s[0];
        const dz = s[3] - s[1];
        const len = @sqrt(dx * dx + dz * dz);
        var d: f32 = 8;

        while (d < len - 6) : (d += 13) {
            const u = d / len;
            const side: f32 = if ((ti + @as(usize, @intFromFloat(d))) % 2 == 0) 1 else -1;
            const x = s[0] + dx * u + dz / len * 3.6 * side;
            const z = s[1] + dz * u - dx / len * 3.6 * side;

            if (!open(x, z, 1) or !dry(x, z, 1)) continue;

            const roll = b.rng.next();

            if (roll < 0.25) {
                put(b, .lantern, x, z, std.math.atan2(dx, dz), 1);
            } else if (roll < 0.4) {
                put(b, .sign, x, z, std.math.atan2(dx, dz), 1);
            } else if (roll < 0.7) {
                put(b, .fence, x, z, std.math.atan2(dx, dz) + hp, 1);
                put(b, .fence, x + dx / len * 2.6, z + dz / len * 2.6, std.math.atan2(dx, dz) + hp, 1);
            } else {
                put(b, .bush, x, z, b.rng.range(0, 6), 1.2);
            }
        }
    }
}

fn shadeProps(b: *Builder) void {
    for (b.placed.items) |pl| {
        const info = api.props.info(pl.kind);
        const ext = @max(info.max[0] - info.min[0], info.max[2] - info.min[2]) * pl.scale;

        if (@abs(pl.pos.y - t.height(pl.pos.x, pl.pos.z)) > 2.5) continue;

        switch (info.group) {
            .tree => splat(pl.pos.x, pl.pos.z, @max(ext * 0.6, 3), 0.5),
            .building => splat(pl.pos.x, pl.pos.z, std.math.clamp(ext * 0.7, 2, 12), 0.5),
            .rock => splat(pl.pos.x, pl.pos.z, std.math.clamp(ext * 0.7, 1, 8), 0.35),
            .street => if (ext > 1.5) splat(pl.pos.x, pl.pos.z, std.math.clamp(ext * 0.6, 1, 4), 0.3),
            else => {},
        }
    }
}

fn build(b: *Builder) void {
    claim_n = 0;
    @memset(&shade_grid, 0);

    camp(b);
    lakeshore(b);
    logging(b);
    campground(b);
    outposts(b);
    trailside(b);
    meadow(b);
    forest(b);
    shadeProps(b);
}

fn keepDry(gpa: std.mem.Allocator, list: []api.Vec3) []api.Vec3 {
    var out: std.ArrayList(api.Vec3) = .empty;

    for (list) |p| {
        if (t.height(p.x, p.z) > water + 0.4) out.append(gpa, p) catch {};
    }

    return out.toOwnedSlice(gpa) catch list;
}

fn setSpots(gpa: std.mem.Allocator) void {
    wd.autoSpots(gpa, .{ .loot = 48, .vehicles = 6, .seed = 913 });

    var spawns: std.ArrayList(api.Vec3) = .empty;
    var yaws: std.ArrayList(f32) = .empty;

    for (wd.spawns, 0..) |p, i| {
        if (t.height(p.x, p.z) <= water + 0.4) continue;

        spawns.append(gpa, p) catch {};
        yaws.append(gpa, wd.spawn_yaws[i]) catch {};
    }

    if (spawns.items.len >= 3) {
        wd.spawns = spawns.toOwnedSlice(gpa) catch wd.spawns;
        wd.spawn_yaws = yaws.toOwnedSlice(gpa) catch wd.spawn_yaws;
    }

    wd.weapon_spots = keepDry(gpa, wd.weapon_spots);

    var cars: std.ArrayList(wd.Spot) = .empty;

    for (wd.vehicle_spots) |v| {
        if (t.height(v.pos.x, v.pos.z) > water + 0.4 and dry(v.pos.x, v.pos.z, 4)) cars.append(gpa, v) catch {};
    }

    wd.vehicle_spots = cars.toOwnedSlice(gpa) catch wd.vehicle_spots;
}
