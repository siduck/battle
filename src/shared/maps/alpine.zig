const std = @import("std");
const api = @import("api.zig");
const k = @import("alpine_kit.zig");

const t = api.terrain;
const kit = k.kit;
const K = k.K;
const Builder = api.Builder;
const vec = api.vec;
const mix3 = api.mix3;
const hp = api.half_pi;

const rim: f32 = 40;

pub const def: api.Def = .{
    .name = "Alpine",
    .note = "Ski village, piste and icefall ridge",
    .tint = .{ 200, 214, 230 },
    .ready = true,
    .half = api.arena_half + rim,
    .play = api.arena_half,
    .facet = 2.5,
    .height = height,
    .ground = ground,
    .build = build,
    .spots = api.autoSpots,
    .props = &k.table,
    .palette = .{
        .sun_dir = .{ 0.42, 0.6, -0.68 },
        .sun_tint = .{ 1.18, 1.06, 0.92 },
        .grade_tint = .{ 0.99, 1.0, 1.03 },
        .grade_sat = 1.16,
        .fog = 0.0017,
        .fog_color = .{ 0.8, 0.87, 0.96 },
        .amb_sky = .{ 0.82, 0.94, 1.2 },
        .amb_ground = .{ 0.86, 0.9, 1.0 },
        .shade_tint = .{ 0.78, 0.87, 1.12 },
        .zenith = .{ 0.08, 0.3, 0.7 },
    },
    .backdrop = .{ 214, 222, 234 },
    .grip = 0.8,
};

const cell: f32 = 2;
const grid_half: f32 = api.arena_half + rim;
const grid_n: comptime_int = @intFromFloat(grid_half * 2 / cell + 1);

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

const street_z: f32 = -55;
const street_end: f32 = api.arena_half - 3;

const trails = [_][4]f32{
    .{ -street_end, street_z, street_end, street_z },
    .{ -60, street_z, -64, -20 },
    .{ -64, -20, -56, 20 },
    .{ -56, 20, -34, 60 },
    .{ -56, 20, -26, 22 },
    .{ 32, -33, 44, -2 },
    .{ 44, -2, 46, 30 },
    .{ 46, 30, 36, 62 },
    .{ -6, street_z, -6, -33 },
    .{ 32, street_z, 32, -33 },
};

fn trailDist(x: f32, z: f32) f32 {
    const wx = x + @sin(z * 0.08) * 1.8;
    const wz = z + @sin(x * 0.07) * 1.8;
    var best: f32 = 1000;

    for (trails) |s| best = @min(best, segDist(wx, wz, s));

    return best;
}

fn pisteX(z: f32) f32 {
    return 20 + 8 * @sin(z * 0.035);
}

fn pisteDist(x: f32, z: f32) f32 {
    const along = t.smooth(-34, -22, z);

    return @abs(x - pisteX(z)) + (1 - along) * 60;
}

fn cliffX(z: f32) f32 {
    return -def.play - 4 + 3 * @sin(z * 0.05) + 2 * @sin(z * 0.13 + 1);
}

const mounds = [_][4]f32{
    .{ -6, -4, 7, 2.2 }, .{ 12, 5, 6, 1.8 }, .{ 30, -6, 7, 2.4 }, .{ 48, 4, 6, 2 },
};

fn moundAt(x: f32, z: f32) f32 {
    var h: f32 = 0;

    for (mounds) |m| {
        const dx = x - (pisteX(m[0]) + m[1]);
        const dz = (z - m[0]) * 0.7;
        const d = @sqrt(dx * dx + dz * dz);

        h = @max(h, m[3] * (1 - t.smooth(0, m[2], d)));
    }

    return h;
}

fn villageMask(x: f32, z: f32) f32 {
    const dx = @max(-def.play - 1 - x, x - def.play - 1, 0);
    const dz = @max(-def.play - 7 - z, z + 12, 0);

    return 1 - t.smooth(0, 14, @sqrt(dx * dx + dz * dz));
}

const pond = [3]f32{ 58, -16, 11 };

fn pondDist(x: f32, z: f32) f32 {
    return @sqrt((x - pond[0]) * (x - pond[0]) + (z - pond[1]) * (z - pond[1])) - pond[2];
}

fn rise(x: f32, z: f32) f32 {
    return 6 * t.smooth(-14, def.play - 3, z) * (1 - 0.45 * t.smooth(30, def.play, x));
}

fn rimEdge(x: f32, z: f32) f32 {
    return @max(@abs(x), @abs(z)) + (t.fbm(x * 0.02 + 5, z * 0.02 - 3) - 0.45) * 12;
}

fn mountains(x: f32, z: f32) f32 {
    const e = rimEdge(x, z);
    const m = t.smooth(def.play + 1, def.half - 6, e);

    if (m <= 0) return 0;

    const ridged = 1 - @abs(2 * t.fbm(x * 0.008 + 9, z * 0.008 + 2) - 1);
    const crags = 1 - @abs(2 * t.fbm(x * 0.03 - 4, z * 0.03 + 6) - 1);
    const shoulder = t.smooth(0, 0.35, m) * 10;

    return shoulder + m * m * (30 + 80 * ridged * ridged) + m * crags * 12;
}

fn height(x: f32, z: f32) f32 {
    const n1 = t.fbm(x * 0.018 + 3, z * 0.018 - 7);
    const n2 = t.fbm(x * 0.06, z * 0.06);
    const groom = 1 - t.smooth(18, 34, pisteDist(x, z));
    const bumps = ((n1 - 0.45) * 3.5 + (n2 - 0.45) * 1.2) * (1 - 0.8 * groom) * (1 - 0.7 * (1 - t.smooth(2, 7, trailDist(x, z))));
    var h = rise(x, z) + bumps + moundAt(x, z);
    const cx = cliffX(z);
    const west = t.smooth(cx + 2.5, cx - 2.5, x);

    h += west * (15 + 7 * n1);
    h += t.smooth(-30, -70, x) * (1 - west) * 4 * n2;

    const vm = villageMask(x, z);

    h = h * (1 - vm) + (0.6 + (n2 - 0.45) * 0.5) * vm;

    const pd = pondDist(x, z);

    if (pd < 6) h = std.math.lerp(h, -0.5, 1 - t.smooth(-2, 6, pd));

    return h + mountains(x, z);
}

fn ground(x: f32, z: f32) api.Rgb {
    const n = t.normal(x, z);
    const slope = 1 - n.y;
    const h = t.height(x, z);
    const vary = 0.95 + t.fbm(x * 0.11, z * 0.11) * 0.1;
    const drift = t.fbm(x * 0.022 + 4, z * 0.022);
    var c = mix3(.{ 202, 214, 234 }, .{ 228, 232, 240 }, t.smooth(0.3, 0.62, drift));

    c = mix3(c, .{ 236, 236, 238 }, t.smooth(0.62, 0.8, t.fbm(x * 0.07 - 2, z * 0.07 + 9)) * 0.7);

    const pd = pisteDist(x, z);
    const lane = 1 - t.smooth(15, 20, pd);
    const cord = t.smooth(0.35, 0.65, @abs(@sin((x - pisteX(z)) * 0.9)));

    c = mix3(c, mix3(.{ 226, 230, 238 }, .{ 238, 240, 244 }, cord), lane);

    const td = trailDist(x, z);
    const vm = villageMask(x, z);
    const street = @max(1 - t.smooth(1.6, 3.6, td), vm * (1 - t.smooth(3, 7, td)));

    c = mix3(c, .{ 214, 216, 222 }, (1 - t.smooth(3.4, 6, td)) * 0.7);
    c = mix3(c, .{ 200, 198, 200 }, street);
    c = mix3(c, .{ 170, 160, 150 }, street * t.smooth(0.5, 0.72, t.fbm(x * 0.35, z * 0.35)) * 0.85);

    const under = shadeAt(x, z);

    c = mix3(c, .{ 182, 186, 192 }, t.smooth(0.25, 0.7, under) * (1 - street) * 0.6);

    const rock = mix3(.{ 84, 86, 98 }, .{ 124, 120, 126 }, t.fbm(x * 0.12, z * 0.5));
    const peak = t.smooth(def.play + 2, def.half - 10, rimEdge(x, z));
    const streak = (t.fbm(x * 0.05 + 3, z * 0.2) - 0.45) * 0.4 * peak;
    const lo = std.math.lerp(@as(f32, 0.34), 0.22, peak);
    const hi = std.math.lerp(@as(f32, 0.52), 0.36, peak);
    const bare = t.smooth(lo, hi, slope + streak) * (1 - t.smooth(120, 150, h) * 0.5);

    c = mix3(c, .{ 188, 198, 216 }, t.smooth(0.18, 0.3, slope));
    c = mix3(c, rock, bare);

    const pdist = pondDist(x, z);

    c = mix3(c, .{ 150, 196, 220 }, 1 - t.smooth(-1, 0.5, pdist));
    c = mix3(c, .{ 196, 222, 236 }, (1 - t.smooth(-4, -2, pdist)) * t.smooth(0.5, 0.6, t.fbm(x * 0.3, z * 0.3)));

    const ao = 1 - 0.36 * under;

    return api.shade(c, vary * ao + n.x * 0.04 - n.z * 0.03);
}

fn bld(e: K) api.Building {
    for (k.buildings) |b| {
        if (b.kind == kit.of(e)) return b;
    }

    return k.buildings[0];
}

fn house(b: *Builder, e: K, x: f32, z: f32, yaw: f32) f32 {
    const info = bld(e);
    const r = @max(info.w, info.d) * 0.5;

    claim(x, z, r + 1);

    return api.building(b, info, x, z, yaw);
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

        if (!open(x, z, 0.8) or trailDist(x, z) < 2.5) continue;

        put(b, kinds[i % kinds.len], x, z, b.rng.range(0, std.math.tau), b.rng.range(smin, smax));
        i += 1;
    }
}

fn yard(b: *Builder, x: f32, z: f32, yaw: f32, w: f32, d: f32) void {
    const c = @cos(yaw);
    const s = @sin(yaw);
    const side = [_]K{ .logs, .cordwood, .skirack, .boards, .trough, .drum, .bench, .skis };
    const ground_bits = [_]K{ .toboggan, .probe, .skis, .akja };
    var i: usize = 0;

    while (i < 2) : (i += 1) {
        const u = b.rng.range(-0.8, 0.8) * w;
        const lx = u;
        const lz = d + 1.2;
        const sign: f32 = if (i % 2 == 0) 1 else -1;
        const wx = x + lx * c + lz * sign * s;
        const wz = z - lx * s + lz * sign * c;

        if (trailDist(wx, wz) < 2) continue;

        put(b, side[b.rng.state % side.len], wx, wz, yaw + (if (sign > 0) @as(f32, 0) else std.math.pi), b.rng.range(1.05, 1.3));
        b.rng.state +%= 1;
    }

    const gx = x + (w + 1.6) * c;
    const gz = z - (w + 1.6) * s;

    put(b, ground_bits[b.rng.state % ground_bits.len], gx, gz, yaw + hp, 1.2);
    b.rng.state +%= 3;
    put(b, .cordwood, x - (w + 1.0) * c, z + (w + 1.0) * s, yaw + hp, 1.3);
}

fn village(b: *Builder) void {
    const north = [_]struct { e: K, x: f32 }{
        .{ .e = .barn, .x = -64 }, .{ .e = .cabin, .x = -44 }, .{ .e = .refuge, .x = -26 },
        .{ .e = .chalet, .x = 52 }, .{ .e = .aframe, .x = 69 },
    };
    const south = [_]struct { e: K, x: f32 }{
        .{ .e = .logcabin, .x = -66 }, .{ .e = .washhouse, .x = -50 }, .{ .e = .chalet, .x = -30 },
        .{ .e = .barn, .x = -4 }, .{ .e = .chalet, .x = 18 }, .{ .e = .cabin, .x = 40 }, .{ .e = .refuge, .x = 60 },
    };

    for (north) |h| {
        const info = bld(h.e);

        _ = house(b, h.e, h.x, street_z + 6 + info.d * 0.5 + 1, std.math.pi);
        yard(b, h.x, street_z + 6 + info.d * 0.5 + 1, std.math.pi, info.w * 0.5, info.d * 0.5);
    }

    for (south) |h| {
        const info = bld(h.e);

        _ = house(b, h.e, h.x, street_z - 6 - info.d * 0.5 - 1, 0);
        yard(b, h.x, street_z - 6 - info.d * 0.5 - 1, 0, info.w * 0.5, info.d * 0.5);
    }

    _ = house(b, .base, -18, -19, std.math.pi);
    _ = house(b, .patrol, 6, -23, -hp);

    var x: f32 = -street_end + 2;

    while (x < street_end - 2) : (x += 4.6) {
        if (@abs(x + 6) < 5 or @abs(x - 32) < 5 or @abs(x + 18) < 4) continue;

        if (@mod(x + street_end, 27.6) > 13.8) continue;

        const north_kind: K = if (@mod(x + street_end, 27.6) < 7) .fence else .logs;
        const south_kind: K = if (@mod(x + street_end, 27.6) < 7) .logs else .fence;

        if (open(x, street_z + 5.6, 0.5)) put(b, north_kind, x + jit(b, 0.3), street_z + 5.6, 0, if (north_kind == .logs) 1.3 else 1.2);

        if (x + 9 < street_end - 2 and open(x + 9, street_z - 5.6, 0.5)) put(b, south_kind, x + 9 + jit(b, 0.3), street_z - 5.6, std.math.pi, if (south_kind == .logs) 1.3 else 1.2);
    }

    for ([_]f32{ -1, 1 }) |s| {
        row(b, .fence, s * street_end, street_z - 4, s * street_end, street_z + 4, 2.6, 1.2);
        put(b, .cordwood, s * (street_end - 2), street_z - 5.4, hp, 1.3);
        put(b, .logs, s * (street_end - 2), street_z + 5.4, hp, 1.4);
    }

    for ([_]f32{ -6, 32, -60 }) |px| {
        put(b, .finger, px + 3.2, street_z + 3.4, 0.4, 1.2);
    }

    const plaza = [_][2]f32{ .{ 2, -41 }, .{ 20, -39 }, .{ -8, -37 }, .{ 26, -45 } };

    put(b, .firepit, 12, -41, 0, 1.4);
    put(b, .bench, 12, -37.4, std.math.pi, 1.2);
    put(b, .bench, 12, -44.6, 0, 1.2);
    put(b, .bench, 8.4, -41, hp, 1.2);
    put(b, .bench, 15.6, -41, -hp, 1.2);

    for (plaza, 0..) |p, i| {
        const kinds = [_]K{ .skirack, .boards, .skirack, .wayfinder };

        put(b, kinds[i], p[0], p[1], if (i % 2 == 0) 0 else hp, 1.25);
    }

    put(b, .sled, 24, -31, 0.3, 1.25);
    put(b, .sled, 27, -30, 0.1, 1.25);
    put(b, .sled, 30, -31.5, -0.2, 1.25);
    put(b, .gondola, -30, -31, 0, 1.2);
    put(b, .gondola, -34, -30, 0, 1.2);
    put(b, .fort, -40, -23, hp, 1.5);
    put(b, .drum, -46, -25, 0, 1.2);
    put(b, .drum, -46.5, -22.8, 0, 1.2);
    put(b, .winch, -36, -16, 0, 1.4);
    put(b, .flood, -6, -27, 0, 1.4);
    put(b, .flood, 28, -25, 0, 1.4);
    put(b, .tow, -2, -11, 0, 1.3);
    put(b, .tow, -2, 27, std.math.pi, 1.3);

    var pz: f32 = -9;

    while (pz < 25) : (pz += 6) put(b, .marker, -4.2, pz, 0, 1);

    for ([_][2]f32{ .{ 46, -12 }, .{ 70, -14 }, .{ 58, -2 }, .{ 54, -30 } }) |p| {
        put(b, .bench, p[0], p[1], std.math.atan2(pond[0] - p[0], pond[1] - p[1]), 1.2);
    }

    scatterIn(b, &.{ .toboggan, .akja, .probe }, 4, pond[0], pond[1], 7, 1.1, 1.3);
    villageFill(b);
}

fn villageFill(b: *Builder) void {
    const fronts = [_][2]f32{ .{ street_z + 13, 1 }, .{ street_z - 13, -1 } };

    for (fronts) |f| {
        var x: f32 = -street_end + 2;

        while (x < street_end - 2) : (x += 5) {
            const z = f[0] + f[1] * b.rng.range(0, 3);

            if (b.rng.next() < 0.5 or !open(x, z, 2.2)) continue;

            const roll = b.rng.next();

            if (roll < 0.35) {
                put(b, .spruce, x, z + f[1] * 2, b.rng.range(0, 6), b.rng.range(0.9, 1.4));
            } else if (roll < 0.5) {
                put(b, .picnic, x, z, hp + jit(b, 0.1), 1);
            } else if (roll < 0.62) {
                put(b, .board, x, z, if (f[1] > 0) std.math.pi else 0, 1);
            } else if (roll < 0.78) {
                put(b, .logs, x, z, 0, 1.4);
                put(b, .cordwood, x + 1.6, z + f[1] * 1.2, 0, 1.3);
            } else {
                put(b, .dwarf, x, z, b.rng.range(0, 6), 1.2);
            }

            claim(x, z, 2);
        }
    }

    for ([_][2]f32{ .{ -68, -49 }, .{ 68, -61 }, .{ -16, -43 }, .{ 44, -45 } }) |p| put(b, .trailsign, p[0], p[1], 0, 1);
}

fn lift(b: *Builder) void {
    const lx: f32 = -18;
    const z0: f32 = 2;
    const z1: f32 = 50;
    const top_z: f32 = def.play - 11;
    const n: usize = 4;
    var tops: [n + 2]api.Vec3 = undefined;
    const base_y = t.height(lx, -19) + 9.5;
    const top_y = t.height(lx, top_z + 2) + 10.5;

    tops[0] = vec(lx, base_y, -13);
    tops[n + 1] = vec(lx, top_y, top_z - 6);

    var i: usize = 0;

    while (i < n) : (i += 1) {
        const z = z0 + (z1 - z0) * @as(f32, @floatFromInt(i)) / @as(f32, @floatFromInt(n - 1));
        const y = world_lowest(lx, z);

        b.putAt(kit.of(.pylon), vec(lx, y, z), 0, 1.3);
        api.box(b, lx - 0.7, y - 1, z - 0.7, lx + 0.7, y + 12.4, z + 0.7);
        tops[i + 1] = vec(lx, y + 12.0, z);
        put(b, .scree, lx + 1.5, z + 1.2, b.rng.range(0, 6), 1.2);
    }

    i = 0;

    while (i < n + 1) : (i += 1) {
        const a = tops[i];
        const c = tops[i + 1];
        const len = c.z - a.z;
        const pieces: usize = @intFromFloat(@max(1, @round(len / 14)));
        const s = len / @as(f32, @floatFromInt(pieces)) / 12;
        var p: usize = 0;

        while (p < pieces) : (p += 1) {
            const u = (@as(f32, @floatFromInt(p)) + 0.5) / @as(f32, @floatFromInt(pieces));
            const y = std.math.lerp(a.y, c.y, u) - 0.25;

            b.putAt(kit.of(.rope), vec(lx, y, std.math.lerp(a.z, c.z, u)), 0, s);

            if (p % 2 == 0) {
                const side: f32 = if ((i + p) % 4 == 0) -1.9 else 1.9;

                b.putAt(kit.of(.chair), vec(lx + side, y - 3.9, std.math.lerp(a.z, c.z, u)), if (side < 0) std.math.pi else 0, 1);
            }
        }
    }

    _ = house(b, .top, lx, top_z, 0);
}

fn world_lowest(x: f32, z: f32) f32 {
    return api.world.lowest(x, z, 1.2) + 0.4;
}

fn piste(b: *Builder) void {
    var z: f32 = -24;
    var i: usize = 0;

    for (mounds, 0..) |m, mi| {
        const mx = pisteX(m[0]) + m[1];

        claim(mx, m[0], m[2] * 0.6);

        if (mi % 2 == 0) put(b, .gate, mx, m[0] - m[2] * 0.4, 0, 1.2) else put(b, .marker, mx + 1.5, m[0], 0, 1.2);
    }

    while (z < def.play - 8) : (z += 17) {
        const px = pisteX(z);

        put(b, .marker, px - 19, z, 0, 1.1);
        put(b, .marker, px + 19, z + 8, 0, 1.1);

        if (i % 3 == 1) put(b, .cannon, px + 23, z, hp + 0.5, 1.15);

        if (i % 3 == 2) put(b, .cannon, px - 23, z + 6, -hp - 0.5, 1.15);

        i += 1;
    }

    z = 30;
    i = 0;

    while (z < def.play - 10) : (z += 13) {
        const px = pisteX(z) + (if (i % 2 == 0) @as(f32, -6) else 6);

        put(b, .gate, px, z, 0, 1.2);
        i += 1;
    }

    const islands = [_][3]f32{ .{ -16, 8, 2 }, .{ 2, -9, 1 }, .{ 20, 10, 0 }, .{ 40, 9, 2 }, .{ 56, -8, 0 } };

    for (islands) |isl| {
        const pz = isl[0];
        const px = pisteX(pz) + isl[1];
        const v: usize = @intFromFloat(isl[2]);

        claim(px, pz, 4);

        switch (v) {
            0 => {
                put(b, .logs, px - 2, pz, 0, 1.5);
                put(b, .logs, px + 0.6, pz, 0, 1.5);
                put(b, .fort, px, pz + 3.4, std.math.pi, 1.5);
                put(b, .fence, px - 3.6, pz - 1.5, 0, 1.2);
                put(b, .fence, px - 1.2, pz - 1.6, 0, 1.2);
            },
            1 => {
                put(b, .fort, px, pz, 0.15, 1.5);
                put(b, .drum, px + 3.2, pz - 2, 0, 1.2);
                put(b, .drum, px + 3.4, pz + 0.3, 0, 1.2);
                put(b, .cordwood, px - 3.4, pz + 1, hp, 1.4);
                put(b, .winch, px + 0.5, pz + 4.5, 0, 1.3);
            },
            else => {
                put(b, .fort, px, pz, 0, 1.6);
                put(b, .fort, px + 4.2, pz + 1.8, -hp, 1.4);
                put(b, .fence, px - 3.4, pz + 2, hp, 1.2);
                put(b, .exploder, px + 6.5, pz - 2, 0, 1.25);
                put(b, .akja, px - 1.5, pz - 3.5, 0.3, 1.3);
            },
        }
    }

    const mid_z: f32 = 18;
    const mid_x = pisteX(mid_z) + 32;

    _ = house(b, .patrol, mid_x, mid_z, -hp);
    _ = house(b, .starthut, pisteX(def.play - 14) + 8, def.play - 14, std.math.pi);
    put(b, .fort, mid_x + 2, mid_z + 10, 1.2, 1.5);
    put(b, .flood, mid_x - 5, mid_z - 6, 0, 1.4);
    put(b, .logs, mid_x + 4, mid_z - 8, hp, 1.4);
    put(b, .logs, mid_x + 4, mid_z - 10, hp, 1.4);
    put(b, .drum, mid_x - 4, mid_z, 0, 1.2);
    put(b, .drum, mid_x - 4.3, mid_z + 2.2, 0, 1.2);
    put(b, .akja, mid_x - 3.5, mid_z - 3, 0, 1.3);
    put(b, .probe, mid_x + 1, mid_z + 5, 0, 1.2);
    put(b, .sled, mid_x + 6, mid_z + 1, 0.2, 1.25);

    row(b, .net, pisteX(34) + 24, 34, pisteX(50) + 25, 52, 2.2, 1.2);
}

fn summit(b: *Builder) void {
    const z = def.play - 12;

    put(b, .mast, 6, z + 2, 0, 1.4);
    put(b, .exploder, -40, z, -0.6, 1.3);

    for ([_][2]f32{ .{ -2, z + 6 }, .{ -50, z + 4 }, .{ 30, z + 8 } }) |p| put(b, .cairn, p[0], p[1], b.rng.range(0, 6), 1.6);

    scatterIn(b, &.{ .outcrop, .boulders, .outcrop }, 5, 4, z - 2, 8, 1.6, 3.0);
    scatterIn(b, &.{ .dwarf, .scree, .dwarf }, 8, -30, z - 4, 9, 1.1, 1.8);
}

fn westRidge(b: *Builder) void {
    var z: f32 = -10;
    var i: usize = 0;

    while (z < def.play + 4) : (z += 9) {
        const cx = cliffX(z);
        const s = b.rng.range(2.8, 4.4);

        sink(b, .outcrop, cx + 1 + jit(b, 1), z + jit(b, 3), b.rng.range(0, 6), s, s * 0.35);

        if (i % 3 == 1) {
            b.putAt(kit.of(.falls), vec(cx + 1.2, t.height(cx + 6, z) - 0.6, z), -hp, 2.6);
            put(b, .scree, cx + 7, z + 2, 0.4, 2);
        } else if (i % 2 == 0) {
            const ss = b.rng.range(2.5, 4);

            sink(b, .slab, cx - 3 + jit(b, 1.5), z + jit(b, 3), b.rng.range(0, 6), ss, ss * 0.3);
        }

        i += 1;
    }

    _ = house(b, .logcabin, -60, 4, hp);
    yard(b, -60, 4, hp, 3.6, 4.2);
    _ = house(b, .barn, -48, 26, 0);
    yard(b, -48, 26, 0, 3.9, 5.2);
    _ = house(b, .lookout, -58, 50, 0);
    put(b, .trough, -54, 16, 0, 1.3);
    put(b, .firepit, -62, 36, 0, 1.3);
    put(b, .bench, -62, 39.4, std.math.pi, 1.2);
    put(b, .cordwood, -68, 18, 0.4, 1.3);

    scatterIn(b, &.{ .boulders, .outcrop, .slab }, 8, -44, -4, 12, 1.6, 3.2);
    scatterIn(b, &.{ .dwarf, .scree }, 10, -44, 44, 14, 1.1, 1.8);
}

fn eastCamp(b: *Builder) void {
    _ = house(b, .aframe, 66, 44, -hp);
    _ = house(b, .cabin, 58, 63, std.math.pi);
    yard(b, 66, 44, -hp, 2.5, 5);
    yard(b, 58, 63, std.math.pi, 5, 5);
    put(b, .firepit, 54, 36, 0, 1.4);
    put(b, .bench, 54, 39.6, std.math.pi, 1.2);
    put(b, .bench, 50.4, 36, hp, 1.2);
    put(b, .sled, 64, 30, 0.4, 1.25);
    put(b, .sled, 66, 32.5, 0.2, 1.25);
    put(b, .trough, 70, 54, hp, 1.3);

    scatterIn(b, &.{ .logs, .cordwood, .dwarf }, 6, 64, 6, 8, 1.2, 1.5);
}

fn forestDensity(x: f32, z: f32) f32 {
    const e = rimEdge(x, z);

    if (e > def.play + 9 or api.arenaEdge(x, z) > def.play + 10) return 0;

    const n = t.normal(x, z);

    if (1 - n.y > 0.42) return 0;

    if (pisteDist(x, z) < 23) return 0;

    if (@abs(x + 18) < 5 and z > -26 and z < def.play) return 0;

    if (trailDist(x, z) < 4.5) return 0;

    if (villageMask(x, z) > 0.3 and z > street_z - 15) return 0;

    if (pondDist(x, z) < 5) return 0;

    const patch = t.smooth(0.38, 0.58, t.fbm(x * 0.025 + 11, z * 0.025 + 4));
    const east = t.smooth(40, 62, x) * (0.3 + 0.6 * patch);
    const west = t.smooth(-30, -56, x) * 0.45 * patch;
    const edge = t.smooth(def.play - 14, def.play + 2, e) * 0.6;
    const mid = t.smooth(-20, 0, z) * t.smooth(0.42, 0.6, t.fbm(x * 0.04 - 7, z * 0.04 + 3)) * 0.6;

    return @max(@max(east, west), @max(edge, mid)) + 0.03;
}

fn forest(b: *Builder) void {
    const step: f32 = 7.5;
    const reach = def.play + 8;
    var z: f32 = -reach;

    while (z < reach) : (z += step) {
        var x: f32 = -reach;

        while (x < reach) : (x += step) {
            const px = x + b.rng.range(-3, 3);
            const pz = z + b.rng.range(-3, 3);
            const d = forestDensity(px, pz);

            if (b.rng.next() > d) continue;

            if (!open(px, pz, 2.5)) continue;

            const h = t.height(px, pz);
            const roll = b.rng.next();
            const e: K = if (h > 30 and roll < 0.5) .larch else if (roll < 0.55) .spruce else if (roll < 0.72) .pines else if (roll < 0.86) .pine else if (roll < 0.94) .larch else .rowan;
            const s: f32 = switch (e) {
                .spruce => b.rng.range(1.3, 2.4),
                .pine, .pines => b.rng.range(0.9, 1.35),
                else => b.rng.range(0.9, 1.3),
            };

            put(b, e, px, pz, b.rng.range(0, std.math.tau), s);

            if (!api.inArena(px, pz, 4)) continue;

            if (b.rng.next() < 0.3) put(b, .dwarf, px + b.rng.range(-3, 3), pz + b.rng.range(-3, 3), b.rng.range(0, 6), b.rng.range(0.9, 1.5));

            if (b.rng.next() < 0.06) put(b, .logs, px + 2.5, pz + 1, b.rng.range(0, 6), 1.3);
        }
    }
}

fn trailside(b: *Builder) void {
    for (trails, 0..) |s, i| {
        if (i == 0) continue;

        const dx = s[2] - s[0];
        const dz = s[3] - s[1];
        const len = @sqrt(dx * dx + dz * dz);
        var d: f32 = 6;

        while (d < len - 4) : (d += 18) {
            const u = d / len;
            const side: f32 = if (@mod(d, 36) < 18) 1 else -1;
            const x = s[0] + dx * u + dz / len * 4.2 * side;
            const z = s[1] + dz * u - dx / len * 4.2 * side;

            if (!open(x, z, 1)) continue;

            const roll = b.rng.next();

            if (roll < 0.3) {
                put(b, .fence, x, z, std.math.atan2(dx, dz) + hp, 1.2);
            } else if (roll < 0.45) {
                put(b, .wayfinder, x, z, std.math.atan2(dx, dz), 1.2);
            } else if (roll < 0.7) {
                sink(b, .boulders, x, z, b.rng.range(0, 6), b.rng.range(1.2, 2), 0.2);
            } else {
                put(b, .dwarf, x, z, b.rng.range(0, 6), 1.2);
            }
        }
    }
}

fn knot(b: *Builder, x: f32, z: f32, v: usize) void {
    claim(x, z, 4);

    switch (v % 3) {
        0 => {
            const s = b.rng.range(2.4, 3.6);

            sink(b, .outcrop, x, z, b.rng.range(0, 6), s, s * 0.3);
            put(b, .spruce, x + 4, z + 2, b.rng.range(0, 6), b.rng.range(1.3, 2));
            put(b, .spruce, x - 3, z + 4.5, b.rng.range(0, 6), b.rng.range(1.1, 1.6));
            put(b, .dwarf, x + 1, z - 3.5, 0, 1.4);
            sink(b, .boulders, x - 4, z - 2, b.rng.range(0, 6), 1.6, 0.2);
        },
        1 => {
            put(b, .pines, x, z, b.rng.range(0, 6), b.rng.range(1, 1.3));
            put(b, .spruce, x + 3.5, z - 2.5, b.rng.range(0, 6), b.rng.range(1.4, 2.2));
            put(b, .logs, x - 3, z + 1, hp, 1.5);
            put(b, .logs, x - 3, z + 3.2, hp, 1.5);
            put(b, .dwarf, x + 2, z + 4, 0, 1.3);
        },
        else => {
            const s = b.rng.range(1.8, 2.6);

            sink(b, .boulders, x, z, b.rng.range(0, 6), s, 0.2);
            sink(b, .slab, x + 3, z + 2, b.rng.range(0, 6), 2.6, 0.75);
            put(b, .larch, x - 3, z + 3, b.rng.range(0, 6), 1.1);
            put(b, .fence, x - 1, z - 3.5, 0, 1.2);
            put(b, .fence, x + 1.4, z - 3.5, 0, 1.2);
        },
    }
}

fn midfield(b: *Builder) void {
    const spots = [_][2]f32{ .{ -34, -4 }, .{ -32, 34 }, .{ -2, 50 }, .{ 40, -4 }, .{ -58, -26 }, .{ 30, 40 } };

    for (spots, 0..) |p, i| {
        const x = p[0] + jit(b, 3);
        const z = p[1] + jit(b, 3);

        if (open(x, z, 5) and @abs(x + 18) > 7) knot(b, x, z, i);
    }
}

fn rimDressing(b: *Builder) void {
    const span = def.play + 4;
    var side: usize = 0;

    while (side < 4) : (side += 1) {
        var a: f32 = -span;

        while (a < span) : (a += 14) {
            const along = a + jit(b, 4);
            const out = def.play + b.rng.range(5, 10);
            const x = switch (side) {
                0 => along,
                1 => along,
                2 => -out,
                else => out,
            };
            const z = switch (side) {
                0 => -out,
                1 => out,
                else => along,
            };

            if (side == 2 and z > -14) continue;

            const s = b.rng.range(3, 5);

            sink(b, .outcrop, x, z, b.rng.range(0, 6), s, s * 0.4);
        }
    }
}

fn shadeProps(b: *Builder) void {
    for (b.placed.items) |pl| {
        const info = api.props.info(pl.kind);
        const ext = @max(info.max[0] - info.min[0], info.max[2] - info.min[2]) * pl.scale;

        if (@abs(pl.pos.y - t.height(pl.pos.x, pl.pos.z)) > 2.5) continue;

        switch (info.group) {
            .tree => splat(pl.pos.x, pl.pos.z, @max(ext * 0.55, 2.5), 0.55),
            .building => splat(pl.pos.x, pl.pos.z, std.math.clamp(ext * 0.7, 2, 12), 0.5),
            .rock => splat(pl.pos.x, pl.pos.z, std.math.clamp(ext * 0.7, 1, 8), 0.4),
            .street => if (ext > 1.2) splat(pl.pos.x, pl.pos.z, std.math.clamp(ext * 0.6, 1, 4), 0.35),
            else => {},
        }
    }
}

fn build(b: *Builder) void {
    claim_n = 0;
    @memset(&shade_grid, 0);

    village(b);
    lift(b);
    piste(b);
    summit(b);
    westRidge(b);
    eastCamp(b);
    midfield(b);
    trailside(b);
    forest(b);
    rimDressing(b);
    shadeProps(b);
}
