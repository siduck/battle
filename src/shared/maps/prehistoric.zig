const std = @import("std");
const api = @import("api.zig");
const k = @import("prehistoric_kit.zig");

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
    .name = "Volcano",
    .note = "Jungle river, hot springs, lava fields",
    .tint = .{ 200, 110, 60 },
    .ready = true,
    .half = 272,
    .play = 212,
    .facet = 2.5,
    .height = height,
    .ground = ground,
    .build = build,
    .spots = setSpots,
    .props = &k.table,
    .palette = .{
        .sun_dir = .{ 0.5, 0.6, 0.62 },
        .sun_tint = .{ 1.2, 1.02, 0.84 },
        .grade_tint = .{ 1.04, 1.0, 0.94 },
        .grade_sat = 1.18,
        .fog = 0.0022,
        .fog_color = .{ 0.84, 0.8, 0.72 },
        .amb_sky = .{ 0.9, 0.96, 1.1 },
        .amb_ground = .{ 0.8, 0.74, 0.56 },
        .shade_tint = .{ 0.86, 0.92, 1.06 },
        .zenith = .{ 0.16, 0.36, 0.66 },
    },
    .backdrop = .{ 62, 98, 90 },
    .floor_y = water,
    .grip = 0.84,
    .tufts = 0.7,
};

const cell: f32 = 2;
const grid_n = 284;
const grid_half: f32 = 284;

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

const volcano = [3]f32{ -14, 250, 125 };
const lake = [3]f32{ 34, -150, 30 };
const springs = [3]f32{ -128, -118, 40 };
const highland = [3]f32{ -150, 92, 56 };
const karst_zone = [2]f32{ 140, -70 };

fn lakeEdge(x: f32, z: f32) f32 {
    const a = std.math.atan2(z - lake[1], x - lake[0]);
    const wob = 0.8 + 0.34 * t.fbm(@cos(a) * 1.6 + 7, @sin(a) * 1.6 + 1) + 0.07 * @sin(a * 4 + 2);

    return lake[2] * wob;
}

fn lakeDist(x: f32, z: f32) f32 {
    const d = @sqrt((x - lake[0]) * (x - lake[0]) + (z - lake[1]) * (z - lake[1]));

    return d - lakeEdge(x, z);
}

const river = [_][2]f32{ .{ 300, 58 }, .{ 196, 40 }, .{ 126, 72 }, .{ 62, 44 }, .{ 12, 12 }, .{ -42, 32 }, .{ -98, 2 }, .{ -160, -26 }, .{ -222, -8 }, .{ -300, -30 } };

const crossings = [_][2]f32{ .{ 94, 58 }, .{ 12, 12 }, .{ -128, -12 } };

fn riverSeg(x: f32, z: f32) usize {
    var best: usize = 0;
    var bd: f32 = 1e9;
    var i: usize = 0;

    while (i + 1 < river.len) : (i += 1) {
        const d = segDist(x, z, .{ river[i][0], river[i][1], river[i + 1][0], river[i + 1][1] });

        if (d < bd) {
            bd = d;
            best = i;
        }
    }

    return best;
}

fn riverDist(x: f32, z: f32) f32 {
    const wz = z + @sin(x * 0.045) * 4;
    var best: f32 = 1000;
    var i: usize = 0;

    while (i + 1 < river.len) : (i += 1) {
        best = @min(best, segDist(x, wz, .{ river[i][0], river[i][1], river[i + 1][0], river[i + 1][1] }));
    }

    return best;
}

fn riverHalf(x: f32, z: f32) f32 {
    var w: f32 = 6.5 + 2.5 * t.fbm(x * 0.03, z * 0.03);

    for (crossings) |c| {
        const d = @sqrt((x - c[0]) * (x - c[0]) + (z - c[1]) * (z - c[1]));

        w = std.math.lerp(3.4, w, t.smooth(5, 18, d));
    }

    return w;
}

const trails = [_][4]f32{
    .{ 12, 12, 30, -60 },
    .{ 30, -60, 34, -112 },
    .{ 30, -60, 120, -40 },
    .{ 120, -40, 160, -110 },
    .{ 12, 12, -60, -60 },
    .{ -60, -60, -128, -118 },
    .{ -128, -118, -40, -186 },
    .{ -40, -186, 34, -186 },
    .{ 12, 12, -20, 90 },
    .{ -20, 90, -14, 150 },
    .{ -20, 90, -120, 60 },
    .{ -120, 60, -128, -12 },
    .{ -128, -12, -128, -118 },
    .{ 94, 58, 60, 120 },
    .{ 60, 120, -14, 150 },
    .{ 94, 58, 160, 110 },
    .{ 160, 110, 180, 20 },
    .{ 180, 20, 120, -40 },
};

fn trailDist(x: f32, z: f32) f32 {
    const wx = x + @sin(z * 0.07) * 2.5;
    const wz = z + @sin(x * 0.06) * 2.5;
    var best: f32 = 1000;

    for (trails) |s| best = @min(best, segDist(wx, wz, s));

    return best;
}

fn dist2(x: f32, z: f32, cx: f32, cz: f32) f32 {
    return @sqrt((x - cx) * (x - cx) + (z - cz) * (z - cz));
}

fn rimEdge(x: f32, z: f32) f32 {
    return @max(@abs(x), @abs(z)) + (t.fbm(x * 0.02 + 5, z * 0.02 - 3) - 0.45) * 24;
}

fn volcanoH(x: f32, z: f32) f32 {
    const d = dist2(x, z, volcano[0], volcano[1]);
    const cone = volcano[2] * @exp(-d / 46);
    const crater = 22 * (1 - t.smooth(8, 20, d));
    const gully = (t.fbm(std.math.atan2(z - volcano[1], x - volcano[0]) * 4 + 3, d * 0.02) - 0.5) * 6 * t.smooth(10, 40, d);

    return cone - crater + gully * (1 - t.smooth(80, 140, d));
}

fn lavaField(x: f32, z: f32) f32 {
    return t.smooth(70, 150, z) * (1 - t.smooth(60, 160, @abs(x - volcano[0]))) * t.smooth(0.3, 0.5, t.fbm(x * 0.02 + 40, z * 0.02));
}

fn terraceH(x: f32, z: f32) f32 {
    const d = dist2(x, z, springs[0], springs[1]);
    const m = 1 - t.smooth(springs[2] * 0.7, springs[2] * 1.2, d);
    const raw = (1 - t.smooth(0, springs[2], d)) * 7;
    const step: f32 = 1.4;
    const q = raw / step;
    const f = @floor(q);
    const stepped = (f + t.smooth(0.82, 1, q - f)) * step;

    return m * stepped;
}

fn highlandH(x: f32, z: f32) f32 {
    const d = dist2(x * 1.0, z * 1.2, highland[0], highland[1] * 1.2);
    const edge = highland[2] + (t.fbm(x * 0.05, z * 0.05) - 0.45) * 22;
    const ramp = 1 - t.smooth(6, 16, @min(trailDist(x, z), 1000));

    return 11 * std.math.lerp(t.smooth(edge + 3, edge - 3, d), t.smooth(edge + 30, edge - 6, d), ramp);
}

fn height(x: f32, z: f32) f32 {
    const n1 = t.fbm(x * 0.016 + 3, z * 0.016 - 7);
    const n2 = t.fbm(x * 0.07, z * 0.07);
    var h = 2.4 + (n1 - 0.4) * 8 + (n2 - 0.45) * 1.8;

    h = @max(h, 0.6);
    h += highlandH(x, z);
    h = std.math.lerp(h, 1.2 + terraceH(x, z), 1 - t.smooth(springs[2] * 0.9, springs[2] * 1.4, dist2(x, z, springs[0], springs[1])));
    h += lavaField(x, z) * 2.2 * t.fbm(x * 0.12, z * 0.12);
    h += volcanoH(x, z);

    const e = rimEdge(x, z);
    const m = t.smooth(def.play - 12, def.half - 6, e) * t.smooth(40, 90, dist2(x, z, volcano[0], volcano[1]));
    const ridged = 1 - @abs(2 * t.fbm(x * 0.012 + 9, z * 0.012 + 2) - 1);

    h += m * m * (28 + 40 * ridged + 8 * n2);

    const shore = t.smooth(8, -6, lakeDist(x, z));

    h = std.math.lerp(h, water - 2.0, shore);

    const rd = riverDist(x, z) - riverHalf(x, z);
    const gorge = t.smooth(9, -1.5, rd);

    h = std.math.lerp(h, water - 1.2, gorge);

    return h;
}

fn ground(x: f32, z: f32) api.Rgb {
    const n = t.normal(x, z);
    const slope = 1 - n.y;
    const h = t.height(x, z);
    const vary = 0.94 + t.fbm(x * 0.11, z * 0.11) * 0.12;
    const p1 = t.fbm(x * 0.03 + 11, z * 0.03 - 4);
    const p2 = t.fbm(x * 0.09 - 3, z * 0.09 + 8);
    var c = mix3(.{ 74, 116, 42 }, .{ 108, 138, 48 }, t.smooth(0.3, 0.62, p1));

    c = mix3(c, .{ 136, 146, 60 }, t.smooth(0.62, 0.78, p2) * 0.6);
    c = mix3(c, .{ 146, 98, 60 }, t.smooth(0.6, 0.72, t.fbm(x * 0.045 + 21, z * 0.045)) * 0.75);

    const under = shadeAt(x, z);

    c = mix3(c, mix3(.{ 58, 84, 36 }, .{ 104, 78, 50 }, t.smooth(0.4, 0.7, p2)), t.smooth(0.15, 0.6, under));

    const td = trailDist(x, z);

    c = mix3(c, .{ 150, 112, 70 }, 1 - t.smooth(2.6, 5, td));
    c = mix3(c, .{ 170, 124, 80 }, 1 - t.smooth(1.4, 3, td));

    const wet = @min(lakeDist(x, z), riverDist(x, z) - riverHalf(x, z));

    c = mix3(c, .{ 92, 104, 52 }, 1 - t.smooth(2, 9, wet));
    c = mix3(c, .{ 128, 110, 82 }, 1 - t.smooth(-1.5, 3, wet));

    const sd = dist2(x, z, springs[0], springs[1]);
    const trav = 1 - t.smooth(springs[2] * 0.85, springs[2] * 1.15, sd);

    c = mix3(c, mix3(.{ 200, 182, 150 }, .{ 196, 142, 96 }, t.smooth(0.4, 0.65, t.fbm(x * 0.2, z * 0.2))), trav * 0.9);
    c = mix3(c, .{ 214, 150, 90 }, trav * t.smooth(0.25, 0.3, slope) * 0.6);

    const rock = mix3(.{ 96, 90, 86 }, .{ 128, 120, 110 }, t.fbm(x * 0.15, z * 0.4));

    c = mix3(c, mix3(c, .{ 90, 110, 56 }, 0.6), t.smooth(0.2, 0.32, slope));
    c = mix3(c, rock, t.smooth(0.4, 0.56, slope));

    const vd = dist2(x, z, volcano[0], volcano[1]);
    const ash = @max(t.smooth(140, 70, vd), lavaField(x, z));
    const basalt = mix3(.{ 46, 42, 44 }, .{ 70, 62, 60 }, t.fbm(x * 0.2, z * 0.2));

    c = mix3(c, basalt, ash);

    const ang = std.math.atan2(z - volcano[1], x - volcano[0]);
    const flow = t.smooth(0.56, 0.64, t.fbm(ang * 5 + 1, vd * 0.012)) * (1 - t.smooth(40, 95, vd));

    c = mix3(c, .{ 236, 96, 30 }, flow);
    c = mix3(c, .{ 255, 150, 50 }, 1 - t.smooth(10, 22, vd));
    c = mix3(c, .{ 150, 44, 24 }, lavaField(x, z) * t.smooth(0.66, 0.7, t.fbm(x * 0.3, z * 0.3)) * 0.8);

    if (h < water + 0.05) c = .{ 88, 92, 70 };

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

fn thermal(b: *Builder) void {
    const cx = springs[0];
    const cz = springs[1];
    var a: f32 = 0;
    var i: usize = 0;

    while (a < std.math.tau) : (a += 0.36) {
        for ([_]f32{ 8, 15, 22, 29, 36 }) |r| {
            const x = cx + @cos(a + r * 0.05) * r;
            const z = cz + @sin(a + r * 0.05) * r;

            if (trailDist(x, z) < 3 or !open(x, z, 2)) continue;

            const e: K = switch (i % 9) {
                0, 3, 6 => .spring,
                1 => .mud,
                2 => .geyser,
                4 => .fumarole,
                5 => .reeds,
                7 => .palm,
                else => .columns,
            };

            put(b, e, x, z, b.rng.range(0, 6), b.rng.range(0.9, 1.2));
            claim(x, z, 2.5);
            i += 1;

            if (b.rng.next() < 0.5) put(b, .stones, x + 2.5, z + 1, b.rng.range(0, 6), 1);
        }
    }

    put(b, .geyser, cx, cz, 0, 1.6);
    put(b, .spring, cx + 3, cz - 2, 0.4, 1.3);
    claim(cx, cz, 5);
    scatterIn(b, &.{ .columns, .boulder, .reeds, .lavapile }, 14, cx, cz, springs[2] + 8, 0.8, 1.3);
}

fn volcanicField(b: *Builder) void {
    var i: usize = 0;

    while (i < 220) : (i += 1) {
        const x = b.rng.range(-def.play + 8, def.play - 8);
        const z = b.rng.range(60, def.play - 4);
        const ash = @max(lavaField(x, z), t.smooth(150, 80, dist2(x, z, volcano[0], volcano[1])));

        if (b.rng.next() > ash or !open(x, z, 2) or trailDist(x, z) < 3 or dist2(x, z, volcano[0], volcano[1]) < 70) continue;

        const roll = b.rng.next();

        if (roll < 0.22) {
            sink(b, .volcanic, x, z, b.rng.range(0, 6), b.rng.range(1, 2), 0.3);
        } else if (roll < 0.38) {
            sink(b, .lavapile, x, z, b.rng.range(0, 6), b.rng.range(1, 1.6), 0.2);
        } else if (roll < 0.5) {
            sink(b, .fang, x, z, b.rng.range(0, 6), b.rng.range(0.8, 1.6), 0.3);
            put(b, .obsidian, x + 2, z + 1, b.rng.range(0, 6), 1);
        } else if (roll < 0.62) {
            put(b, .scorched, x, z, b.rng.range(0, 6), b.rng.range(0.8, 1.2));
        } else if (roll < 0.74) {
            put(b, .snag, x, z, b.rng.range(0, 6), b.rng.range(0.9, 1.3));
        } else if (roll < 0.86) {
            sink(b, .columns, x, z, b.rng.range(0, 6), b.rng.range(1, 2.2), 0.3);
        } else if (roll < 0.93) {
            put(b, .fumarole, x, z, b.rng.range(0, 6), b.rng.range(0.9, 1.4));
        } else {
            sink(b, .basalt, x, z, b.rng.range(0, 6), b.rng.range(1, 1.8), 0.3);
        }

        claim(x, z, 1.8);
    }
}

fn karstForest(b: *Builder) void {
    const towers = [_][3]f32{ .{ 126, -46, 0 }, .{ 162, -84, 1 }, .{ 118, -104, 0 }, .{ 176, -30, 0 }, .{ 196, -120, 1 }, .{ 86, -88, 0 }, .{ 150, -150, 0 }, .{ 200, 70, 1 }, .{ 70, 150, 0 } };

    for (towers, 0..) |p, i| {
        const e: K = if (p[2] > 0.5) .karst_big else .karst;

        house(b, e, p[0], p[1], @as(f32, @floatFromInt(i)) * 1.3);
        put(b, .bamboo, p[0] + 9, p[1] + 4, b.rng.range(0, 6), b.rng.range(0.9, 1.2));
        put(b, .palm, p[0] - 7, p[1] + 8, b.rng.range(0, 6), b.rng.range(0.9, 1.2));
        put(b, .fernrock, p[0] + 5, p[1] - 9, b.rng.range(0, 6), 1.2);
    }
}

fn highlandWest(b: *Builder) void {
    const ax: f32 = -84;
    const az: f32 = 70;

    house(b, .arch, ax, az, std.math.atan2(@as(f32, -100), -30) + hp);
    house(b, .cave, -176, 54, hp);
    house(b, .arch, 150, 20, 0.3);

    var a: f32 = 0;

    while (a < std.math.tau) : (a += 0.14) {
        const r = highland[2] + 2;
        const x = highland[0] + @cos(a) * r;
        const z = highland[1] + @sin(a) * r / 1.2;

        if (trailDist(x, z) < 6 or !open(x, z, 2)) continue;

        if (b.rng.next() < 0.6) sink(b, .columns, x, z, b.rng.range(0, 6), b.rng.range(1.5, 2.6), 0.4) else sink(b, .fernrock, x, z, b.rng.range(0, 6), b.rng.range(1, 1.6), 0.3);
    }

    scatterIn(b, &.{ .araucaria, .cycad, .fernrock, .columns }, 22, highland[0], highland[1], highland[2] - 10, 0.8, 1.2);
}

fn bridges(b: *Builder) void {
    for (crossings) |c| {
        const s = riverSeg(c[0], c[1]);
        const dx = river[s + 1][0] - river[s][0];
        const dz = river[s + 1][1] - river[s][1];
        const yaw = std.math.atan2(dx, dz);
        const y = @max(t.height(c[0] + @cos(yaw) * 7, c[1] - @sin(yaw) * 7), t.height(c[0] - @cos(yaw) * 7, c[1] + @sin(yaw) * 7));

        b.putAt(kit.of(.ropebridge), vec(c[0], y - 0.6, c[1]), yaw, 1);
        api.box(b, c[0] - 2.4, water - 2, c[1] - 2.4, c[0] + 2.4, y - 0.1, c[1] + 2.4);
        claim(c[0], c[1], 7);
    }
}

fn waterEdges(b: *Builder) void {
    var a: f32 = 0;

    while (a < std.math.tau) : (a += 0.1) {
        const r = lakeEdge(lake[0] + @cos(a) * 20, lake[1] + @sin(a) * 20);
        const x = lake[0] + @cos(a) * (r + 1.5);
        const z = lake[1] + @sin(a) * (r + 1.5);
        const roll = b.rng.next();

        if (roll < 0.35) put(b, .reeds, x, z, b.rng.range(0, 6), b.rng.range(0.9, 1.3)) else if (roll < 0.5) put(b, .horsetail, x, z, b.rng.range(0, 6), 1) else if (roll < 0.6) put(b, .driftwood, x, z, a, 1);

        if (b.rng.next() < 0.6) {
            const lr = r - b.rng.range(3, 12);
            const e: K = if (b.rng.next() < 0.5) .lilies else .lotus;

            b.putAt(kit.of(e), vec(lake[0] + @cos(a) * lr, water - 0.05, lake[1] + @sin(a) * lr), b.rng.range(0, 6), b.rng.range(0.8, 1.3));
        }
    }

    var i: usize = 0;

    while (i + 1 < river.len) : (i += 1) {
        const dx = river[i + 1][0] - river[i][0];
        const dz = river[i + 1][1] - river[i][1];
        const len = @sqrt(dx * dx + dz * dz);
        var d: f32 = 0;

        while (d < len) : (d += 7) {
            const u = d / len;
            const side: f32 = if (b.rng.next() < 0.5) -1 else 1;
            const off = side * (riverHalf(river[i][0] + dx * u, river[i][1] + dz * u) + b.rng.range(1, 4));
            const x = river[i][0] + dx * u + dz / len * off;
            const z = river[i][1] + dz * u - dx / len * off;

            if (@max(@abs(x), @abs(z)) > def.play - 4 or !open(x, z, 1.5)) continue;

            const roll = b.rng.next();

            if (roll < 0.3) put(b, .reeds, x, z, b.rng.range(0, 6), 1) else if (roll < 0.45) put(b, .stones, x, z, b.rng.range(0, 6), 1.2) else if (roll < 0.58) put(b, .horsetail, x, z, 0, b.rng.range(0.8, 1.2)) else if (roll < 0.66) put(b, .driftwood, x, z, b.rng.range(0, 6), 1) else if (roll < 0.74) sink(b, .boulder, x, z, b.rng.range(0, 6), b.rng.range(0.8, 1.3), 0.3);

            if (b.rng.next() < 0.25) {
                b.putAt(kit.of(.lilies), vec(river[i][0] + dx * u + dz / len * off * 0.6, water - 0.05, river[i][1] + dz * u - dx / len * off * 0.6), b.rng.range(0, 6), 1);
            }
        }
    }
}

fn jungleDensity(x: f32, z: f32) f32 {
    const e = rimEdge(x, z);

    if (e > def.half - 10) return 0;

    if (!dry(x, z, 2.5) or trailDist(x, z) < 4) return 0;

    if (1 - t.normal(x, z).y > 0.5) return 0.08;

    if (dist2(x, z, volcano[0], volcano[1]) < 105) return 0;

    if (dist2(x, z, springs[0], springs[1]) < springs[2] * 1.1) return 0.05;

    const ash = @max(lavaField(x, z), t.smooth(150, 80, dist2(x, z, volcano[0], volcano[1])));
    const patch = t.smooth(0.28, 0.55, t.fbm(x * 0.024 + 11, z * 0.024 + 4));
    const glade = 1 - t.smooth(0.64, 0.72, t.fbm(x * 0.05 - 3, z * 0.05 + 7)) * 0.85;

    return ((0.15 + 0.85 * patch * patch) * glade + t.smooth(def.play - 20, def.play + 10, e) * 0.6) * (1 - ash * 0.85);
}

fn jungleKind(b: *Builder, x: f32, z: f32) K {
    const tall = t.smooth(0.4, 0.62, t.fbm(x * 0.014 - 20, z * 0.014 + 5));
    const roll = b.rng.next();

    if (b.rng.next() < tall * 0.6) {
        return if (roll < 0.35) .redwood else if (roll < 0.6) .araucaria else if (roll < 0.85) .ginkgo else .magnolia;
    }

    return if (roll < 0.24) .palm else if (roll < 0.44) .treefern else if (roll < 0.6) .cycad else if (roll < 0.72) .williamsonia else if (roll < 0.82) .bamboo else if (roll < 0.92) .magnolia else .ginkgo;
}

fn jungle(b: *Builder) void {
    const step: f32 = 6;
    var z: f32 = -def.half + 8;

    while (z < def.half - 8) : (z += step) {
        var x: f32 = -def.half + 8;

        while (x < def.half - 8) : (x += step) {
            const px = x + b.rng.range(-2.5, 2.5);
            const pz = z + b.rng.range(-2.5, 2.5);

            if (b.rng.next() > jungleDensity(px, pz)) continue;

            if (!open(px, pz, 2.2)) continue;

            const e = jungleKind(b, px, pz);
            const s: f32 = switch (e) {
                .redwood => b.rng.range(0.8, 1.3),
                .araucaria => b.rng.range(0.7, 1.1),
                .ginkgo => b.rng.range(0.8, 1.2),
                else => b.rng.range(0.85, 1.35),
            };

            put(b, e, px, pz, b.rng.range(0, std.math.tau), s);

            const under = b.rng.next();

            if (under < 0.3) {
                put(b, .fern, px + jit(b, 3), pz + jit(b, 3), b.rng.range(0, 6), b.rng.range(0.9, 1.5));
            } else if (under < 0.45) {
                put(b, .shrub, px + jit(b, 3), pz + jit(b, 3), b.rng.range(0, 6), b.rng.range(0.9, 1.4));
            } else if (under < 0.55) {
                put(b, .sapling, px + jit(b, 3), pz + jit(b, 3), b.rng.range(0, 6), b.rng.range(0.8, 1.3));
            } else if (under < 0.6) {
                put(b, .mushroom, px + jit(b, 2), pz + jit(b, 2), b.rng.range(0, 6), b.rng.range(0.8, 1.3));
            } else if (under < 0.65) {
                put(b, .hollow, px + jit(b, 3), pz + jit(b, 3), b.rng.range(0, 6), 1);
            } else if (under < 0.7) {
                put(b, .fungus, px + jit(b, 3), pz + jit(b, 3), b.rng.range(0, 6), 1);
            } else if (under < 0.75) {
                put(b, .stump, px + jit(b, 3), pz + jit(b, 3), b.rng.range(0, 6), 1);
            } else if (under < 0.8) {
                sink(b, .fernrock, px + jit(b, 4), pz + jit(b, 4), b.rng.range(0, 6), b.rng.range(0.8, 1.3), 0.3);
            } else if (under < 0.86) {
                put(b, .litter, px + jit(b, 2), pz + jit(b, 2), b.rng.range(0, 6), 1);
            }
        }
    }
}

fn groundCover(b: *Builder) void {
    var i: usize = 0;

    while (i < 2200) : (i += 1) {
        const x = b.rng.range(-def.play, def.play);
        const z = b.rng.range(-def.play, def.play);

        if (!dry(x, z, 0.5) or trailDist(x, z) < 1.6 or !open(x, z, 0.3)) continue;

        if (lavaField(x, z) > 0.4 or dist2(x, z, volcano[0], volcano[1]) < 105) continue;

        const roll = b.rng.next();

        if (roll < 0.35) put(b, .moss, x, z, b.rng.range(0, 6), b.rng.range(0.8, 1.3)) else if (roll < 0.65) put(b, .fern, x, z, b.rng.range(0, 6), b.rng.range(0.7, 1.2)) else if (roll < 0.8) put(b, .shrub, x, z, b.rng.range(0, 6), b.rng.range(0.7, 1.1)) else if (roll < 0.9) put(b, .litter, x, z, b.rng.range(0, 6), 1) else put(b, .stones, x, z, b.rng.range(0, 6), 1);
    }

    i = 0;

    while (i < 180) : (i += 1) {
        const x = b.rng.range(-def.play + 6, def.play - 6);
        const z = b.rng.range(-def.play + 6, def.play - 6);

        if (!dry(x, z, 2) or trailDist(x, z) < 3.5 or !open(x, z, 2.5)) continue;

        const roll = b.rng.next();

        if (roll < 0.3) {
            sink(b, .fernrock, x, z, b.rng.range(0, 6), b.rng.range(1, 1.6), 0.3);
            put(b, .fern, x + 2, z + 1, 0, 1.2);
        } else if (roll < 0.5) {
            put(b, .hollow, x, z, b.rng.range(0, 6), b.rng.range(1, 1.2));
            put(b, .mushroom, x + 1.5, z + 1.5, 0, 1);
        } else if (roll < 0.65) {
            sink(b, .boulder, x, z, b.rng.range(0, 6), b.rng.range(1, 1.6), 0.4);
            sink(b, .basalt, x + 2.5, z - 1, b.rng.range(0, 6), 1, 0.2);
        } else if (roll < 0.8) {
            put(b, .petrified, x, z, b.rng.range(0, 6), b.rng.range(1, 1.3));
            put(b, .petrified, x + 2.2, z + 0.4, b.rng.range(0, 6), 0.8);
        } else {
            put(b, .fungus, x, z, b.rng.range(0, 6), 1);
            put(b, .geode, x + 2, z - 1.5, b.rng.range(0, 6), 1);
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

        while (d < len - 6) : (d += 10) {
            const u = d / len;
            const side: f32 = if ((ti + @as(usize, @intFromFloat(d))) % 2 == 0) 1 else -1;
            const x = s[0] + dx * u + dz / len * 3.8 * side;
            const z = s[1] + dz * u - dx / len * 3.8 * side;

            if (!open(x, z, 1) or !dry(x, z, 1)) continue;

            const roll = b.rng.next();

            if (roll < 0.3) put(b, .sapling, x, z, b.rng.range(0, 6), 1.2) else if (roll < 0.5) sink(b, .scoria, x, z, b.rng.range(0, 6), b.rng.range(0.7, 1.1), 0.1) else if (roll < 0.7) put(b, .cycad, x, z, b.rng.range(0, 6), 0.8) else put(b, .shrub, x, z, b.rng.range(0, 6), 1.2);
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

    bridges(b);
    highlandWest(b);
    karstForest(b);
    thermal(b);
    volcanicField(b);
    waterEdges(b);
    trailside(b);
    groundCover(b);
    jungle(b);
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
    wd.autoSpots(gpa, .{ .loot = 48, .vehicles = 6, .seed = 517 });

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
