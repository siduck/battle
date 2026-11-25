const std = @import("std");
const math = @import("math.zig");

const Vec3 = math.Vec3;

pub var half: f32 = 112;
pub var play: f32 = 98;
pub const town: f32 = 54;
pub const road_half: f32 = 7;

pub const Map = enum { town, desert, valley, islands, facility, conquest, prism, courtyard, airport, alpine, coast, construction, japan, forest, nyc, pirate, prehistoric, racing, lab, salvage, stadium, warehouse };

const registry = @import("maps/registry.zig");
const islands_map = @import("maps/islands.zig");

pub const villageMask = islands_map.villageMask;

pub var current: Map = .facility;

fn hash(x: i32, z: i32) f32 {
    var h: u32 = @bitCast(x *% 374761393 +% z *% 668265263);

    h = (h ^ (h >> 13)) *% 1274126177;
    h ^= h >> 16;

    return @as(f32, @floatFromInt(h & 0xffff)) / 65535.0;
}

fn noise(x: f32, z: f32) f32 {
    const xi: i32 = @intFromFloat(@floor(x));
    const zi: i32 = @intFromFloat(@floor(z));
    const fx = x - @floor(x);
    const fz = z - @floor(z);
    const ux = fx * fx * (3 - 2 * fx);
    const uz = fz * fz * (3 - 2 * fz);
    const a = hash(xi, zi);
    const b = hash(xi + 1, zi);
    const c = hash(xi, zi + 1);
    const d = hash(xi + 1, zi + 1);

    return std.math.lerp(std.math.lerp(a, b, ux), std.math.lerp(c, d, ux), uz);
}

pub fn fbm(x: f32, z: f32) f32 {
    var v: f32 = 0;
    var amp: f32 = 0.5;
    var px = x;
    var pz = z;
    var i: u32 = 0;

    while (i < 4) : (i += 1) {
        v += amp * noise(px, pz);
        px = px * 2.07 + 13.1;
        pz = pz * 2.07 + 7.7;
        amp *= 0.5;
    }

    return v;
}

pub fn smooth(edge0: f32, edge1: f32, v: f32) f32 {
    const t = math.clamp01((v - edge0) / (edge1 - edge0));

    return t * t * (3 - 2 * t);
}

pub fn onRoad(x: f32, z: f32) bool {
    return roadDistance(x, z) < road_half;
}

pub fn roadLine(z: f32) f32 {
    return switch (current) {
        .town => 0,
        .desert => 8 * @sin(z * 0.022),
        .valley => 40 * @sin(z * 0.011) + 12 * @sin(z * 0.03 + 1),
        else => 0,
    };
}

pub fn roadDistance(x: f32, z: f32) f32 {
    if (registry.current()) |d| return if (d.road) |road| road(x, z) else 1000;

    if (current == .islands or current == .prism or current == .courtyard) return 1000;

    if (current == .valley) return valleyRoad(x, z);

    if (current == .facility) return facilityRoad(x, z);

    if (current == .conquest) return conquestRoad(x, z);

    if (current != .town) return @abs(x - roadLine(z));

    var best = @min(@abs(x), @abs(z));

    if (@abs(x) < town and @abs(z) < town) {
        best = @min(best, @min(@abs(@abs(x) - 32), @abs(@abs(z) - 32)));
    }

    return best;
}

pub fn flatness(x: f32, z: f32) f32 {
    if (registry.current()) |d| return if (d.flat) |flat| flat(x, z) else 0;

    if (current == .islands or current == .facility or current == .prism or current == .courtyard) return 0;

    if (current == .conquest) return @max(@max(1 - smooth(road_half + 1, road_half + 14, conquestRoad(x, z)), districtMask(x, z)), runwayMask(x, z));

    if (current != .town) return 1 - smooth(road_half + 1, road_half + 10, roadDistance(x, z));

    const box = @max(@abs(x), @abs(z));
    const in_town = 1 - smooth(town - 2, town + 14, box);
    const near_road = 1 - smooth(road_half + 1, road_half + 12, roadDistance(x, z));

    return @max(in_town, near_road);
}

pub var oasis = [2]f32{ -70, 56 };

pub var town_center = [2]f32{ 4, -8 };

pub var town_half = [2]f32{ 58, 48 };

pub var market = [3]f32{ 30, 6, 13 };

pub const District = struct {
    name: [:0]const u8,
    x: f32,
    z: f32,
    r: f32,
};

pub const districts = [_]District{
    .{ .name = "A", .x = -150, .z = 135, .r = 58 },
    .{ .name = "B", .x = 150, .z = 150, .r = 42 },
    .{ .name = "C", .x = 145, .z = -110, .r = 62 },
    .{ .name = "D", .x = -150, .z = -150, .r = 42 },
    .{ .name = "E", .x = 0, .z = 10, .r = 46 },
};

pub var runway = [4]f32{ 300, -425, 165, 15 };

pub var helipads = [3][2]f32{ .{ 335, -325 }, .{ 358, -300 }, .{ 380, -270 } };

pub fn pocketMask(x: f32, z: f32) f32 {
    if (current != .desert) return 0;

    var best: f32 = 0;

    for ([_][3]f32{ .{ 50, -195, 34 }, .{ -130, -85, 36 } }) |p| {
        const d = @sqrt((x - p[0]) * (x - p[0]) + (z - p[1]) * (z - p[1]));

        best = @max(best, 1 - smooth(p[2] * 0.7, p[2], d));
    }

    return best;
}

pub fn padMask(x: f32, z: f32) f32 {
    var best: f32 = 0;

    for (helipads) |p| {
        const d = @sqrt((x - p[0]) * (x - p[0]) + (z - p[1]) * (z - p[1]));

        best = @max(best, 1 - smooth(11, 22, d));
    }

    return best;
}

pub fn runwayMask(x: f32, z: f32) f32 {
    const d = @max(@abs(x - runway[0]) - runway[2], @abs(z - runway[1]) - runway[3]);

    return 1 - smooth(0, 22, d);
}

const road_links = [_][2]u8{ .{ 0, 4 }, .{ 1, 4 }, .{ 2, 4 }, .{ 3, 4 }, .{ 0, 1 }, .{ 1, 2 }, .{ 3, 0 }, .{ 2, 3 } };

pub const compound = [2]f32{ 130, 120 };

pub const facility_roads = [_][4]f32{
    .{ -80, -66, 80, -66 },
    .{ -80, 66, 80, 66 },
    .{ -80, -66, -80, 66 },
    .{ 80, -66, 80, 66 },
    .{ 0, -51, 0, -192 },
    .{ 0, 51, 0, 126 },
    .{ 63, 0, 136, 0 },
    .{ -63, 0, -136, 0 },
    .{ -140, -192, 140, -192 },
};

pub fn facilityRoad(x: f32, z: f32) f32 {
    var best: f32 = 1e9;

    for (facility_roads) |sg| best = @min(best, segDistance(x, z, sg[0], sg[1], sg[2], sg[3]));

    return best;
}

fn facilityHeight(x: f32, z: f32) f32 {
    const box = @max(@abs(x) - compound[0], @abs(z) - compound[1]);
    const out = smooth(0, 60, box) * (1 - runwayMask(x, z)) * (1 - padMask(x, z)) * smooth(road_half + 1, road_half + 14, facilityRoad(x, z));
    const rolling = (fbm(x * 0.012 + 40, z * 0.012 - 11) - 0.35) * 14;
    const edge = @max(@abs(x), @abs(z));
    const ridge = smooth(play - 20, half, edge) * (7 + fbm(x * 0.04, z * 0.04) * 5);

    return @max(rolling, 0) * out + ridge;
}

pub fn configure() void {
    registry.activate();

    if (registry.current()) |d| {
        half = d.half;
        play = d.play;
        facet = d.facet;

        if (d.runway) |r| runway = r;

        if (d.helipads) |h| helipads = h;

        if (d.configure) |f| f();

        return;
    }

    if (current == .prism) {
        half = 140;
        play = 125;

        return;
    }

    if (current == .courtyard) {
        half = 175;
        play = 147;

        return;
    }

    if (current == .valley) {
        half = 275;
        play = 250;
        facet = 2.2;
        runway = .{ valley_base[0], -222, 70, 12 };
        helipads = .{ .{ 25, -192 }, .{ 47, -192 }, .{ 69, -192 } };

        return;
    }

    if (current == .facility) {
        half = 270;
        play = 250;
        runway = .{ 0, -212, 150, 13 };
        helipads = .{ .{ -108, -97 }, .{ -84, -97 }, .{ -60, -97 } };

        return;
    }

    if (current != .conquest) return;

    half = 270;
    play = 250;
    facet = 2.5;
    runway = .{ 130, -205, 95, 12 };
    helipads = .{ .{ 180, -155 }, .{ 203, -130 }, .{ 200, -95 } };
    town_center = .{ districts[0].x, districts[0].z };
    town_half = .{ 46, 40 };
    market = .{ districts[0].x + 15, districts[0].z + 8, 11 };
    oasis = .{ districts[1].x + 18, districts[1].z + 18 };
}

fn segDistance(px: f32, pz: f32, ax: f32, az: f32, bx: f32, bz: f32) f32 {
    const dx = bx - ax;
    const dz = bz - az;
    const len2 = dx * dx + dz * dz;
    const t = math.clamp01(((px - ax) * dx + (pz - az) * dz) / len2);
    const qx = ax + dx * t - px;
    const qz = az + dz * t - pz;

    return @sqrt(qx * qx + qz * qz);
}

fn bend(a: District, b: District) [2]f32 {
    const mx = (a.x + b.x) / 2;
    const mz = (a.z + b.z) / 2;
    const k = (fbm(mx * 0.02 + 3, mz * 0.02) - 0.5) * 60;

    return .{ mx + (b.z - a.z) / 350 * k, mz - (b.x - a.x) / 350 * k };
}

pub fn conquestSegments() [road_links.len * 2][4]f32 {
    var out: [road_links.len * 2][4]f32 = undefined;

    for (road_links, 0..) |l, i| {
        const a = districts[l[0]];
        const b = districts[l[1]];
        const m = bend(a, b);

        out[i * 2] = .{ a.x, a.z, m[0], m[1] };
        out[i * 2 + 1] = .{ m[0], m[1], b.x, b.z };
    }

    return out;
}

pub fn conquestRoad(x: f32, z: f32) f32 {
    var best: f32 = 1e9;

    for (road_links) |l| {
        const a = districts[l[0]];
        const b = districts[l[1]];
        const m = bend(a, b);

        best = @min(best, segDistance(x, z, a.x, a.z, m[0], m[1]));
        best = @min(best, segDistance(x, z, m[0], m[1], b.x, b.z));
    }

    return best;
}

pub fn districtMask(x: f32, z: f32) f32 {
    var m: f32 = 0;

    for (districts) |d| {
        const dist = @sqrt((x - d.x) * (x - d.x) + (z - d.z) * (z - d.z));

        m = @max(m, 1 - smooth(d.r, d.r + 25, dist));
    }

    return m;
}

pub fn districtAt(x: f32, z: f32) ?usize {
    for (districts, 0..) |d, i| {
        const dist = @sqrt((x - d.x) * (x - d.x) + (z - d.z) * (z - d.z));

        if (dist < d.r + 10) return i;
    }

    return null;
}

pub fn riverDistance(x: f32, z: f32) f32 {
    const line = 60 + 45 * @sin(z * 0.012 + 0.7) + 15 * @sin(z * 0.034);

    return @abs(x - line);
}

fn conquest(x: f32, z: f32) f32 {
    const box = @max(@abs(x), @abs(z));
    const road = 1 - smooth(road_half + 1, road_half + 14, conquestRoad(x, z));
    const dmask = @max(districtMask(x, z), runwayMask(x, z));
    const flat = @max(road, dmask);
    const wave = z * 0.04 + x * 0.01 + fbm(x * 0.015, z * 0.015) * 5;
    const crest = 1 - @abs(@sin(wave));
    const dunes = crest * crest * 3.5 * (0.3 + fbm(x * 0.02 + 5, z * 0.02));
    const rolling = (fbm(x * 0.006, z * 0.006) - 0.42) * 16 + (fbm(x * 0.018 + 11, z * 0.018 - 7) - 0.5) * 7;
    const m = fbm(x * 0.008 + 70, z * 0.008 - 30);
    const mesas = smooth(0.6, 0.62, m) * 12 + smooth(0.66, 0.68, m) * 10;
    const sw = smooth(-50, -150, x) * smooth(-40, -140, z);
    const ridge_noise = 1 - @abs(fbm(x * 0.01, z * 0.01) * 2 - 1);
    const mountains = sw * (4 + ridge_noise * ridge_noise * 10);
    const rd = riverDistance(x, z);
    const river = (1 - smooth(8, 26, rd)) * 6;
    const edge = smooth(play - 20, half - 6, box) * (8 + fbm(x * 0.03, z * 0.03) * 6);
    const od = oasisDistance(x, z);
    const pool = (1 - smooth(6, 16, od)) * 2.4;
    const features = (dunes * smooth(10, 30, rd) + @max(rolling, -2) + mesas + mountains) * (1 - flat) - river * (1 - road);
    const base = (fbm(x * 0.004 + 9, z * 0.004) - 0.5) * 10;

    return base * (1 - dmask * 0.6) + features + edge - pool;
}

pub fn townMask(x: f32, z: f32) f32 {
    const d = @max(@abs(x - town_center[0]) - town_half[0], @abs(z - town_center[1]) - town_half[1]);

    return 1 - smooth(0, 12, d);
}

pub fn oasisDistance(x: f32, z: f32) f32 {
    return @sqrt((x - oasis[0]) * (x - oasis[0]) + (z - oasis[1]) * (z - oasis[1]));
}

pub fn mesa(x: f32, z: f32) f32 {
    const m = fbm(x * 0.012 + 70, z * 0.012 - 30);
    const keep = smooth(16, 24, oasisDistance(x, z));

    return (smooth(0.58, 0.6, m) * 9 + smooth(0.63, 0.645, m) * 8 + smooth(0.68, 0.69, m) * 9) * keep;
}

fn strata(h: f32) f32 {
    const step: f32 = 4.5;
    const f = h / step;
    const lo = @floor(f);

    return (lo + smooth(0.72, 1, f - lo)) * step;
}

pub const valley_base = [4]f32{ -10, -212, 95, 30 };

pub const Branch = struct {
    z0: f32,
    x1: f32,
    z1: f32,
};

pub const branches = [_]Branch{
    .{ .z0 = 70, .x1 = 210, .z1 = 140 },
    .{ .z0 = -70, .x1 = -215, .z1 = -120 },
    .{ .z0 = 160, .x1 = -205, .z1 = 215 },
    .{ .z0 = -10, .x1 = 205, .z1 = -60 },
};

pub fn baseMask(x: f32, z: f32) f32 {
    const d = @max(@abs(x - valley_base[0]) - valley_base[2], @abs(z - valley_base[1]) - valley_base[3]);

    return 1 - smooth(0, 26, d);
}

pub fn passRise(z: f32) f32 {
    return smooth(110, 240, z) * 18;
}

pub fn riverLine(z: f32) f32 {
    return roadLine(z) + 22 + 4 * @sin(z * 0.04);
}

pub fn riverSpan(z: f32) f32 {
    return smooth(-185, -172, z) * (1 - smooth(222, 234, z));
}

pub fn branchPoint(b: Branch, t: f32) [2]f32 {
    const sx = roadLine(b.z0);

    return .{ sx + (b.x1 - sx) * t, b.z0 + (b.z1 - b.z0) * t };
}

const Trough = struct {
    d: f32,
    floor: f32,
};

fn trough(x: f32, z: f32) Trough {
    var best: Trough = .{ .d = @abs(x - roadLine(z)), .floor = passRise(z) };

    for (branches) |b| {
        const s = branchPoint(b, 0);
        const dx = b.x1 - s[0];
        const dz = b.z1 - s[1];
        const t = math.clamp01(((x - s[0]) * dx + (z - s[1]) * dz) / (dx * dx + dz * dz));
        const qx = s[0] + dx * t - x;
        const qz = s[1] + dz * t - z;
        const d = @sqrt(qx * qx + qz * qz) * 1.25 + t * 8;

        if (d < best.d) best = .{ .d = d, .floor = passRise(b.z0) + t * 12 };
    }

    return best;
}

fn valleyRoad(x: f32, z: f32) f32 {
    var best = @abs(x - roadLine(z)) + @max(0, -186 - z) * 4;

    for (branches) |b| {
        const s = branchPoint(b, 0);
        const e = branchPoint(b, 0.72);

        best = @min(best, segDistance(x, z, s[0], s[1], e[0], e[1]));
    }

    return best;
}

pub fn troughDist(x: f32, z: f32) f32 {
    return trough(x, z).d;
}

pub fn valleyFloor(x: f32, z: f32) f32 {
    return trough(x, z).floor * (1 - baseMask(x, z));
}

fn layered(h: f32, step: f32) f32 {
    const f = h / step;
    const lo = @floor(f);

    return (lo + smooth(0.66, 1, f - lo)) * step;
}

fn valley(x: f32, z: f32) f32 {
    const tr = trough(x, z);
    const base = baseMask(x, z);
    const box = @max(@abs(x), @abs(z));
    const wall = smooth(28, 80, tr.d);
    const r = 1 - @abs(fbm(x * 0.009, z * 0.009) * 2 - 1);
    const big = fbm(x * 0.005 + 20, z * 0.005 - 7);
    const mtn = wall * (12 + r * r * 24 + big * 22);
    const ends = smooth(play - 26, half - 4, box) * (46 + fbm(x * 0.02, z * 0.02) * 20) * (1 - smooth(-200, -240, z) * 0.6);
    const rock = @max(mtn, ends) * (1 - base);
    const open = (1 - wall) * (1 - base);
    const rd = @abs(x - riverLine(z));
    const ripple = (fbm(x * 0.05, z * 0.05) - 0.5) * 1.4 * (1 - flatness(x, z)) * open * smooth(6, 14, rd);
    const channel = (1 - smooth(3, 8, rd)) * 2.4 * riverSpan(z) * open;

    return tr.floor * (1 - base) + rock + ripple - channel;
}

pub var facet: f32 = 3.5;

pub fn rawHeight(x: f32, z: f32) f32 {
    if (registry.current()) |d| return d.height(x, z);

    return switch (current) {
        .town => townHeight(x, z),
        .valley => valley(x, z),
        .facility => facilityHeight(x, z),
        .conquest => conquest(x, z),
        else => 0,
    };
}

pub const void_floor: f32 = -60;
pub const sea_level: f32 = 0.4;

pub fn height(x: f32, z: f32) f32 {
    if (current == .town) return townHeight(x, z);

    const gx = @floor((x + half) / facet);
    const gz = @floor((z + half) / facet);
    const x0 = gx * facet - half;
    const z0 = gz * facet - half;
    const fx = (x - x0) / facet;
    const fz = (z - z0) / facet;
    const h00 = rawHeight(x0, z0);
    const h11 = rawHeight(x0 + facet, z0 + facet);

    if (fz > fx) {
        const h01 = rawHeight(x0, z0 + facet);

        return h00 + (h11 - h01) * fx + (h01 - h00) * fz;
    }

    const h10 = rawHeight(x0 + facet, z0);

    return h00 + (h10 - h00) * fx + (h11 - h10) * fz;
}

fn townHeight(x: f32, z: f32) f32 {
    const hills = (fbm(x * 0.018, z * 0.018) - 0.35) * 14;
    const box = @max(@abs(x), @abs(z));
    const ridge = smooth(play - 14, half, box) * (22 + fbm(x * 0.05, z * 0.05) * 18);
    const ground = @max(hills, -1.5) * (1 - flatness(x, z));

    return ground + ridge;
}

pub fn normal(x: f32, z: f32) Vec3 {
    const e: f32 = 0.5;
    const dx = height(x + e, z) - height(x - e, z);
    const dz = height(x, z + e) - height(x, z - e);

    return (Vec3{ .x = -dx, .y = 2 * e, .z = -dz }).normalize();
}

pub fn raycast(origin: Vec3, dir: Vec3, max_t: f32) ?f32 {
    var t: f32 = 0;
    var prev = origin.y - height(origin.x, origin.z);

    if (prev < 0) return 0;

    while (t < max_t) {
        const step = @max(0.25, prev * 0.5);
        const next_t = @min(t + step, max_t);
        const p = origin.add(dir.scale(next_t));
        const gap = p.y - height(p.x, p.z);

        if (gap <= 0) {
            var lo = t;
            var hi = next_t;
            var k: u32 = 0;

            while (k < 8) : (k += 1) {
                const mid = (lo + hi) / 2;
                const q = origin.add(dir.scale(mid));

                if (q.y - height(q.x, q.z) > 0) lo = mid else hi = mid;
            }

            return hi;
        }

        t = next_t;
        prev = gap;

        if (next_t >= max_t) break;
    }

    return null;
}
