const std = @import("std");
const api = @import("api.zig");
const k = @import("islands_kit.zig");

const tr = api.terrain;
const wd = api.world;
const Builder = api.Builder;
const Kind = api.Kind;
const Vec3 = api.Vec3;
const vec = api.vec;
const half_pi = api.half_pi;
const shade = api.shade;
const mix3 = api.mix3;
const kit = k.kit;
const K = k.K;

pub const def: api.Def = .{
    .name = "Islands",
    .note = "Hillside village, olive terraces, quarry",
    .tint = .{ 110, 180, 90 },
    .half = 215,
    .play = 172,
    .facet = 2.0,
    .height = height,
    .ground = groundColor,
    .build = build,
    .spots = setSpots,
    .props = &k.table,
    .palette = .{
        .sun_dir = .{ 0.52, 0.68, -0.52 },
        .sun_tint = .{ 1.16, 1.03, 0.88 },
        .grade_tint = .{ 1.04, 1.01, 0.95 },
        .grade_sat = 1.16,
        .fog = 0.0026,
        .fog_color = .{ 0.7, 0.84, 0.95 },
        .amb_sky = .{ 0.9, 1, 1.2 },
        .amb_ground = .{ 0.8, 0.76, 0.6 },
        .shade_tint = .{ 0.86, 0.92, 1.08 },
        .zenith = .{ 0.05, 0.3, 0.7 },
    },
    .backdrop = .{ 34, 112, 150 },
    .floor_y = 0.12,
    .grip = 0.84,
    .tufts = 0.6,
};

const sea_y: f32 = 0.35;
const pier_x: f32 = 64;
const cell: f32 = 4.4;
const tier: f32 = 3.3;
const cols: i32 = 25;
const rows: i32 = 17;
const tiers: i32 = 7;
const vx0: f32 = -55.0;
const vz0: f32 = -132;
const y0: f32 = 1.3;
const summit = [2]f32{ -4, 18 };
const farm = [2]f32{ -62, 86 };
const quarry = [2]f32{ 70, 78 };
const hamlet = [2]f32{ 112, -34 };
const cove = [2]f32{ -132, -58 };
const mills = [_][3]f32{ .{ -26, 6, 0.4 }, .{ -8, 26, 0.1 }, .{ 14, 14, -0.3 } };

pub fn villageMask(x: f32, z: f32) f32 {
    if (tr.current != .islands) return 0;

    return 1 - tr.smooth(0, 6, villageOut(x, z));
}

fn villageOut(x: f32, z: f32) f32 {
    const x1 = vx0 + cell * @as(f32, @floatFromInt(cols));
    const z1 = vz0 + cell * @as(f32, @floatFromInt(rows));
    const dx = @max(vx0 - x, x - x1, 0);
    const dz = @max(vz0 - z, z - z1, 0);

    return @sqrt(dx * dx + dz * dz);
}

fn rowLevel(r: i32) f32 {
    if (r < 3) return y0;

    const t = @divFloor(r - 3, 2);

    return y0 + @as(f32, @floatFromInt(if (@mod(r - 3, 2) == 1) t + 1 else t)) * tier;
}

fn rowOf(z: f32) i32 {
    return @intFromFloat(std.math.clamp(@floor((z - vz0) / cell), 0, @as(f32, @floatFromInt(rows - 1))));
}

fn villageRamp(z: f32) f32 {
    const t = (z - vz0) / cell - 3;

    return y0 + std.math.clamp(t / 2, 0, @as(f32, @floatFromInt(tiers))) * tier;
}

pub fn islandEdge(x: f32, z: f32) f32 {
    const ang = std.math.atan2(z, x);
    const wob = 150 * (0.86 + 0.24 * tr.fbm(@cos(ang) * 1.6 + 7.3, @sin(ang) * 1.6 + 3.1) + 0.035 * @sin(ang * 6 + 1.3));
    const s = -@sin(ang);

    if (s < 0.2) return wob;

    return @min(wob, 132 / s);
}

pub fn coastDistance(x: f32, z: f32) f32 {
    return islandEdge(x, z) - @sqrt(x * x + z * z);
}

fn dist(x: f32, z: f32, p: [2]f32) f32 {
    return @sqrt((x - p[0]) * (x - p[0]) + (z - p[1]) * (z - p[1]));
}

fn segDist(x: f32, z: f32, s: [4]f32) f32 {
    const dx = s[2] - s[0];
    const dz = s[3] - s[1];
    const l2 = dx * dx + dz * dz;
    const t = std.math.clamp(((x - s[0]) * dx + (z - s[1]) * dz) / l2, 0, 1);
    const px = s[0] + dx * t - x;
    const pz = s[1] + dz * t - z;

    return @sqrt(px * px + pz * pz);
}

const paths = [_][4]f32{
    .{ 0, -56, -4, -30 },
    .{ -4, -30, -26, 6 },
    .{ -26, 6, -8, 26 },
    .{ -8, 26, 14, 14 },
    .{ 14, 14, -4, -30 },
    .{ -8, 26, -40, 64 },
    .{ -40, 64, -62, 86 },
    .{ 14, 14, 48, 56 },
    .{ 48, 56, 70, 78 },
    .{ -46, -70, -100, -60 },
    .{ -100, -60, -132, -58 },
    .{ 46, -70, 90, -40 },
    .{ 90, -40, 112, -34 },
    .{ -26, 6, -90, 10 },
    .{ -90, 10, -100, -60 },
    .{ 14, 14, 100, 10 },
    .{ 100, 10, 112, -34 },
};

pub fn pathDistance(x: f32, z: f32) f32 {
    if (tr.current != .islands) return 1000;

    const wx = x + @sin(z * 0.08) * 1.6;
    const wz = z + @sin(x * 0.07) * 1.6;
    var best: f32 = 1000;

    for (paths) |s| best = @min(best, segDist(wx, wz, s));

    return best;
}

fn natural(x: f32, z: f32) f32 {
    const sd = dist(x, z, summit);
    const hill = 40 * (1 - tr.smooth(0, 170, sd)) + 8 * (1 - tr.smooth(0, 60, dist(x, z, .{ -70, 70 }))) + 6 * (1 - tr.smooth(0, 50, dist(x, z, .{ 100, -10 })));
    const ridge = (tr.fbm(x * 0.02 + 4, z * 0.02 - 9) - 0.45) * 9;
    const bumps = (tr.fbm(x * 0.07, z * 0.07) - 0.5) * 1.6;

    return y0 + @max(0, hill + ridge + bumps);
}

const Grove = struct { x0: f32, z0: f32, x1: f32, z1: f32, along_z: bool };

const grove_rects = [_]Grove{
    .{ .x0 = -112, .z0 = -104, .x1 = -60, .z1 = -44, .along_z = true },
    .{ .x0 = 60, .z0 = -104, .x1 = 112, .z1 = -52, .along_z = true },
    .{ .x0 = -100, .z0 = 112, .x1 = -24, .z1 = 146, .along_z = true },
    .{ .x0 = -150, .z0 = -30, .x1 = -112, .z1 = 50, .along_z = false },
    .{ .x0 = 112, .z0 = 20, .x1 = 150, .z1 = 80, .along_z = false },
    .{ .x0 = 22, .z0 = -50, .x1 = 56, .z1 = -8, .along_z = true },
    .{ .x0 = -62, .z0 = -50, .x1 = -26, .z1 = -8, .along_z = true },
    .{ .x0 = -22, .z0 = -48, .x1 = 18, .z1 = -16, .along_z = true },
    .{ .x0 = -26, .z0 = 52, .x1 = 36, .z1 = 128, .along_z = true },
    .{ .x0 = -124, .z0 = 56, .x1 = -84, .z1 = 104, .along_z = false },
};

const band_w: f32 = 6;

fn rectMask(g: Grove, x: f32, z: f32) f32 {
    const dx = @max(g.x0 - x, x - g.x1, 0);
    const dz = @max(g.z0 - z, z - g.z1, 0);

    return 1 - tr.smooth(0, 5, @max(dx, dz));
}

fn groveMask(x: f32, z: f32) f32 {
    var m: f32 = 0;

    for (grove_rects) |g| m = @max(m, rectMask(g, x, z));

    return m;
}

fn bandRef(g: Grove, v: f32) f32 {
    const o = if (g.along_z) g.z0 else g.x0;

    return o + (@floor((v - o) / band_w) + 0.5) * band_w;
}

fn terracedAt(x: f32, z: f32) f32 {
    for (grove_rects) |g| {
        const m = rectMask(g, x, z);

        if (m <= 0) continue;

        const t = if (g.along_z) natural(x, bandRef(g, z)) else natural(bandRef(g, x), z);
        const keep = m * (1 - tr.smooth(1, -1, pathDistance(x, z) - 2.5));

        return natural(x, z) * (1 - keep) + t * keep;
    }

    return natural(x, z);
}

fn quarryDepth(x: f32, z: f32) f32 {
    const dx = @abs(x - quarry[0]);
    const dz = @abs(z - quarry[1]);
    const e = @max(dx / 26, dz / 20);

    if (e > 1.25) return 0;

    const bench = std.math.clamp(@floor((1.05 - e) * 6), 0, 4);
    const lip = tr.smooth(1.25, 1.0, e);
    const d = bench * 2.6 + lip * 1.2;
    const road = 1 - tr.smooth(4, 6, dx);

    if (z > quarry[1] or road <= 0) return d;

    const lim = @max(0, z - (quarry[1] - 26)) * 0.5;

    return d * (1 - road) + @min(d, lim) * road;
}

fn landHeight(x: f32, z: f32) f32 {
    var h = terracedAt(x, z);

    const fd = dist(x, z, farm);

    if (fd < 30) h = h * tr.smooth(14, 30, fd) + (natural(farm[0], farm[1]) + 0.2) * (1 - tr.smooth(14, 30, fd));

    const hd = dist(x, z, hamlet);

    if (hd < 30) h = h * tr.smooth(16, 30, hd) + (natural(hamlet[0], hamlet[1])) * (1 - tr.smooth(16, 30, hd));

    for (mills) |m| {
        const md = dist(x, z, .{ m[0], m[1] });

        if (md < 12) h = h * tr.smooth(5, 12, md) + natural(m[0], m[1]) * (1 - tr.smooth(5, 12, md));
    }

    const qd = quarryDepth(x, z);

    if (qd > 0) {
        const rim_h = natural(quarry[0], quarry[1]) + 1;

        h = @min(h, rim_h + 4) - qd;
    }

    return h;
}

fn height(x: f32, z: f32) f32 {
    const cd = coastDistance(x, z);

    if (cd < 0) return sea_y - 0.02;

    const out = villageOut(x, z);

    if (out <= 0) return rowLevel(rowOf(z)) - 0.25;

    const quayside = z < -112 and @abs(x) < 78;
    var land = landHeight(x, z);

    if (quayside) land = land * tr.smooth(-118, -104, z) + y0 * (1 - tr.smooth(-118, -104, z));

    const vm = 1 - tr.smooth(0, 26, out);
    const blended = land * (1 - vm) + (villageRamp(z) - 0.25) * vm;
    const beach = tr.smooth(0, 7, cd);
    const cliff = tr.smooth(0.5, 0.62, tr.fbm(x * 0.02 + 5, z * 0.02 + 2));
    const shore = if (quayside) 1 else beach * (1 - cliff) + tr.smooth(0, 1.5, cd) * cliff;

    return sea_y + (blended - sea_y) * shore;
}

fn waterColor(cd: f32, x: f32, z: f32) api.Rgb {
    const d = -cd;
    const wave = tr.fbm(x * 0.05 + 3, z * 0.05 - 4) * 0.12 + 0.94;
    const shallow = [3]f32{ 118, 214, 206 };
    const mid = [3]f32{ 42, 168, 182 };
    const deep = [3]f32{ 34, 112, 150 };
    const c = if (d < 10) mix3(shallow, mid, tr.smooth(0, 10, d)) else mix3(mid, deep, tr.smooth(10, 45, d));

    return shade(c, wave);
}

fn groundColor(x: f32, z: f32) api.Rgb {
    const cd = coastDistance(x, z);

    if (cd < 0) return waterColor(cd, x, z);

    const n = tr.normal(x, z);
    const slope = 1 - n.y;
    const light = api.light(x, z);
    const h = tr.height(x, z);
    const fleck = tr.fbm(x * 0.3 - 7, z * 0.3 + 5);

    if (villageMask(x, z) > 0.5) return shade(.{ 214, 200, 170 }, light);

    if (z < -112 and @abs(x) < 78) return shade(mix3(.{ 214, 196, 160 }, .{ 196, 180, 146 }, fleck), light);

    if (h < sea_y + 1.4 and cd < 9) return shade(mix3(.{ 230, 214, 172 }, .{ 214, 196, 150 }, fleck), light);

    const qd = quarryDepth(x, z);

    if (qd > 0.3) return shade(mix3(.{ 226, 216, 192 }, .{ 200, 188, 160 }, fleck), light * (0.94 + slope * 0.2));

    const g = groveMask(x, z);

    if (slope > 0.42 and cd < 24) {
        const band = @sin(h * 2.2 + fleck * 2) * 0.5 + 0.5;

        return shade(mix3(.{ 200, 182, 148 }, .{ 168, 150, 118 }, band * 0.7), light);
    }

    if (slope > 0.34 and g > 0.4) {
        const course = @mod(h * 2.6, 1.0);
        const stone = mix3(.{ 190, 176, 148 }, .{ 158, 146, 122 }, if (course < 0.18) 1 else fleck * 0.6);

        return shade(stone, light);
    }

    const pd = pathDistance(x, z);

    if (pd < 2.0) return shade(mix3(.{ 204, 176, 132 }, .{ 190, 160, 116 }, fleck), light);

    const dry = tr.fbm(x * 0.03 + 40, z * 0.03 - 12);
    const maquis = tr.smooth(0.44, 0.56, tr.fbm(x * 0.09 + 17, z * 0.09 - 3));
    const scrub = mix3(.{ 140, 140, 78 }, .{ 176, 160, 98 }, std.math.clamp(dry * 1.6 - 0.4, 0, 1));
    const patchy = mix3(scrub, .{ 82, 100, 52 }, maquis * 0.85);
    const speck = mix3(patchy, .{ 206, 184, 96 }, std.math.clamp((fleck - 0.66) * 4, 0, 0.5));
    const furrow = 0.5 + 0.5 * @sin((x * 0.6 + z * 0.35) + fleck);
    const grove = mix3(mix3(.{ 178, 144, 100 }, .{ 160, 128, 88 }, furrow * 0.5), .{ 142, 140, 82 }, std.math.clamp(fleck * 1.5 - 0.45, 0, 0.8));
    const base = mix3(speck, grove, g * 0.9);
    const verge = mix3(base, .{ 194, 168, 126 }, 1 - tr.smooth(2, 4, pd));

    if (slope > 0.3) return shade(mix3(verge, .{ 150, 138, 96 }, (slope - 0.3) * 1.5), light);

    return shade(verge, light);
}

var occ: [430 * 430]u8 = undefined;

fn occIndex(x: f32, z: f32) ?usize {
    const ix: i32 = @intFromFloat(@floor(x + 215));
    const iz: i32 = @intFromFloat(@floor(z + 215));

    if (ix < 0 or iz < 0 or ix >= 430 or iz >= 430) return null;

    return @intCast(iz * 430 + ix);
}

fn taken(x: f32, z: f32, r: f32) bool {
    var dz: f32 = -r;

    while (dz <= r) : (dz += 1) {
        var dx: f32 = -r;

        while (dx <= r) : (dx += 1) {
            if (occIndex(x + dx, z + dz)) |i| {
                if (occ[i] != 0) return true;
            }
        }
    }

    return false;
}

fn claim(x: f32, z: f32, r: f32) void {
    var dz: f32 = -r;

    while (dz <= r) : (dz += 1) {
        var dx: f32 = -r;

        while (dx <= r) : (dx += 1) {
            if (occIndex(x + dx, z + dz)) |i| occ[i] = 1;
        }
    }
}

fn claimRect(x0: f32, z0: f32, x1: f32, z1: f32) void {
    var z = z0;

    while (z <= z1) : (z += 1) {
        var x = x0;

        while (x <= x1) : (x += 1) {
            if (occIndex(x, z)) |i| occ[i] = 1;
        }
    }
}

fn of(e: K) Kind {
    return kit.of(e);
}

fn rnd(b: *Builder) f32 {
    return b.rng.next();
}

fn spin(b: *Builder) f32 {
    return b.rng.range(0, std.math.tau);
}

fn quarter(b: *Builder) f32 {
    return @floor(b.rng.next() * 3.99) * half_pi;
}

fn cellX(c: i32) f32 {
    return vx0 + (@as(f32, @floatFromInt(c)) + 0.5) * cell;
}

fn cellZ(r: i32) f32 {
    return vz0 + (@as(f32, @floatFromInt(r)) + 0.5) * cell;
}

fn box(b: *Builder, x0: f32, ya: f32, z0: f32, x1: f32, yb: f32, z1: f32) void {
    b.solid(.{ .box = .{ .min = vec(x0, ya, z0), .max = vec(x1, yb, z1) } });
}

var spawn_list: std.ArrayList(Vec3) = .empty;
var spawn_yaw: std.ArrayList(f32) = .empty;
var anchor_list: std.ArrayList(Vec3) = .empty;
var park_list: std.ArrayList(wd.Spot) = .empty;

fn spawnAt(b: *Builder, x: f32, y: f32, z: f32, yaw: f32) void {
    spawn_list.append(b.gpa, vec(x, y, z)) catch {};
    spawn_yaw.append(b.gpa, yaw) catch {};
}

fn loot(b: *Builder, x: f32, y: f32, z: f32) void {
    wd.kit_loot.append(b.gpa, vec(x, y + 0.1, z)) catch {};
}

fn villageBlock(b: *Builder, c: i32, r: i32, top: f32) void {
    const x = cellX(c);
    const z = cellZ(r);
    const h = cell * 0.5;

    b.putAt(of(.block), vec(x, top, z), 0, 1);
    box(b, x - h, top - 17, z - h, x + h, top, z + h);
}

fn houseKind(b: *Builder, c: i32, k_: i32) struct { kind: Kind, floors: f32, dome: bool } {
    const roll = rnd(b);
    const mid = @abs(c - 12) < 6;

    if (mid and k_ >= 3 and roll < 0.06) return .{ .kind = of(.cube3), .floors = 3, .dome = false };

    if (roll < 0.07) return .{ .kind = of(.dome1), .floors = 1, .dome = true };

    if (roll < 0.1 and k_ > 1) return .{ .kind = of(.dome2), .floors = 2, .dome = true };

    if (roll < 0.38) return .{ .kind = b.rng.pick(Kind, &.{ of(.cube2), of(.cube2b), of(.cube2c) }), .floors = 2, .dome = false };

    if (roll < 0.46) return .{ .kind = b.rng.pick(Kind, &.{ of(.cave1), of(.cave1) }), .floors = 1, .dome = false };

    if (roll < 0.54) return .{ .kind = of(.cube1p), .floors = 1, .dome = false };

    return .{ .kind = b.rng.pick(Kind, &.{ of(.cube1), of(.cube1), of(.cube1b), of(.cube1c), of(.cube1b) }), .floors = 1, .dome = false };
}

fn villageHouse(b: *Builder, kind: Kind, x: f32, z: f32, base: f32, floors: f32, dome: bool) void {
    const h = cell * 0.5;
    const top = base + floors * tier;
    const cave = kind == of(.cave1) or kind == of(.cave1);
    const yaw: f32 = if (dome or kind == of(.cube1p) or kind == of(.cube3)) 0 else quarter(b);

    b.putAt(kind, vec(x, base, z), yaw, 1);
    box(b, x - h, base - 0.5, z - h, x + h, top, z + h);

    if (dome) {
        box(b, x - 1.35, top, z - 1.35, x + 1.35, top + 2.0, z + 1.35);

        return;
    }

    if (cave) return;

    if (kind == of(.cube1p)) {
        for ([_][2]f32{ .{ -1.9, -1.9 }, .{ 1.9, -1.9 }, .{ -1.9, 0.2 }, .{ 1.9, 0.2 } }) |p| {
            const q = wd.rotPoint(x, z, yaw, p[0], -p[1]);

            box(b, q[0] - 0.1, top, q[1] - 0.1, q[0] + 0.1, top + 2.3, q[1] + 0.1);
        }

        return;
    }

    const right = kind == of(.cube1b) or kind == of(.cube2b) or kind == of(.cube3);
    const lx: f32 = if (right) 1.3 else -1.3;
    const ch = wd.rotPoint(x, z, yaw, lx, -1.5);

    box(b, ch[0] - 0.4, top, ch[1] - 0.4, ch[0] + 0.4, top + 1.4, ch[1] + 0.4);

    if (floors > 1.5 and rnd(b) < 0.55) b.putAt(of(.solar), vec(x + 0.6, top, z - 0.4), quarter(b), 1);
}

fn villageStair(b: *Builder, x: f32, z_south: f32, base: f32) void {
    b.putAt(of(.stair), vec(x, base, z_south), 0, 1);
    b.solid(.{ .ramp = .{ .min = vec(x - 1.3, base, z_south), .max = vec(x + 1.3, base + tier, z_south + cell), .rise = .pos_z } });
    box(b, x - 2.2, base - 0.5, z_south, x - 1.3, base + tier + 1.0, z_south + cell);
    box(b, x + 1.3, base - 0.5, z_south, x + 2.2, base + tier + 1.0, z_south + cell);
}

fn parapetX(b: *Builder, x: f32, y: f32, z: f32) void {
    b.putAt(of(.parapet), vec(x, y, z), 0, 1);
    box(b, x - 2.2, y, z - 0.22, x + 2.2, y + 0.95, z + 0.22);
}

fn parapetZ(b: *Builder, x: f32, y: f32, z: f32) void {
    b.putAt(of(.parapet), vec(x, y, z), half_pi, 1);
    box(b, x - 0.22, y, z - 2.2, x + 0.22, y + 0.95, z + 2.2);
}

fn laneClutter(b: *Builder, x: f32, y: f32, z: f32, c: i32, k_: i32) void {
    const wall_z = z + cell * 0.5 - 0.45;
    const roll = rnd(b);

    if (@mod(c + k_, 3) == 0) b.putAt(of(.lamp), vec(x + 1.7, y, wall_z - 0.1), std.math.pi, 1);

    if (roll < 0.3) {
        b.putAt(of(.geranium), vec(x - 1.4, y, wall_z), 0, 1);
        b.putAt(of(.basil), vec(x - 0.7, y, wall_z), 0, 1);
        b.putAt(of(.pot), vec(x + 0.6, y, wall_z), spin(b), 1);
    } else if (roll < 0.5) {
        b.putAt(of(.bougain), vec(x, y, wall_z + 0.15), 0, 1);
        b.putAt(of(.geranium), vec(x + 1.2, y, wall_z - 0.1), 0, 1);
    } else if (roll < 0.64) {
        b.putAt(of(.kafe), vec(x, y, z - 0.6), 0, 1);
        b.putAt(of(.chair), vec(x - 0.8, y, z - 0.6), half_pi, 1);
        b.putAt(of(.chair), vec(x + 0.8, y, z - 0.6), -half_pi, 1);
        b.putAt(of(.basil), vec(x - 1.6, y, wall_z), 0, 1);
    } else if (roll < 0.74) {
        b.putAt(of(.jar), vec(x - 1.2, y, wall_z), spin(b), 1);
        b.putAt(of(.jar), vec(x - 0.4, y, wall_z - 0.2), spin(b), 0.8);
        b.putAt(of(.geranium), vec(x + 1.0, y, wall_z), 0, 1);
    } else if (roll < 0.8) {
        b.putAt(of(.moped), vec(x, y, wall_z - 0.5), half_pi + b.rng.range(-0.2, 0.2), 1);
    } else if (roll < 0.86) {
        b.putAt(of(.barrow), vec(x - 0.8, y, wall_z - 0.4), half_pi, 1);
        b.putAt(of(.sack), vec(x + 0.4, y, wall_z), spin(b), 1);
        b.putAt(of(.sack), vec(x + 0.9, y, wall_z - 0.1), spin(b), 1);
    } else if (roll < 0.93) {
        b.putAt(of(.agave), vec(x, y, wall_z - 0.4), spin(b), 0.8);
        b.putAt(of(.pot), vec(x + 1.4, y, wall_z), spin(b), 1.1);
    } else {
        b.putAt(of(.barrel), vec(x + 1.2, y, wall_z - 0.1), spin(b), 1);
        b.putAt(of(.basil), vec(x + 0.4, y, wall_z), 0, 1);
    }
}

fn roofClutter(b: *Builder, x: f32, top: f32, z: f32) void {
    const roll = rnd(b);

    if (roll < 0.22) {
        b.putAt(of(.parasol), vec(x - 0.4, top, z - 0.2), 0, 0.9);
        b.putAt(of(.taverna), vec(x - 0.4, top, z - 0.2), half_pi, 1);
    } else if (roll < 0.4) {
        b.putAt(of(.chair), vec(x - 0.8, top, z - 0.8), spin(b), 1);
        b.putAt(of(.chair), vec(x + 0.6, top, z - 0.9), spin(b), 1);
        b.putAt(of(.geranium), vec(x + 1.5, top + 0.28, z - 2.0), 0, 1);
    } else if (roll < 0.55) {
        b.putAt(of(.laundry), vec(x, top + 0.28, z + 0.6), 0, 1);
    } else if (roll < 0.68) {
        b.putAt(of(.pot), vec(x - 1.4, top + 0.28, z - 1.8), spin(b), 1);
        b.putAt(of(.basil), vec(x + 1.4, top + 0.28, z - 1.9), 0, 1);
    }
}

fn medVillage(b: *Builder) void {
    var c: i32 = 0;

    while (c < cols) : (c += 1) {
        var r: i32 = 0;

        while (r < 3) : (r += 1) {
            const x = cellX(c);
            const z = cellZ(r);

            if (r == 0) {
                b.putAt(of(.quay), vec(x, y0, z), 0, 1);
                box(b, x - 2.2, y0 - 6, z - 2.2, x + 2.2, y0, z + 2.2);
            } else villageBlock(b, c, r, y0);
        }
    }

    harbourQuay(b);
    harbourRow(b, 61, 1);
    harbourRow(b, -61, -1);

    var t: i32 = 1;

    while (t <= tiers) : (t += 1) {
        const hr = 3 + (t - 1) * 2;
        const lr = hr + 1;
        const base = y0 + @as(f32, @floatFromInt(t - 1)) * tier;
        const lane_y = base + tier;
        const s0: i32 = @intCast(@mod(t * 7 + 3, 6) + 4);
        const s1: i32 = @intCast(@mod(t * 5 + 1, 5) + 14);
        const edge: i32 = 2 + @divFloor(t, 2);
        const n0: i32 = @intCast(@mod((t + 1) * 7 + 3, 6) + 4);
        const n1: i32 = @intCast(@mod((t + 1) * 5 + 1, 5) + 14);
        var arch_col: i32 = 11 + @mod(t * 3, 5) - 2;

        while (arch_col == s0 or arch_col == s1 or arch_col == n0 or arch_col == n1) arch_col += 1;

        c = 0;

        while (c < cols) : (c += 1) {
            const x = cellX(c);
            const hz = cellZ(hr);
            const lz = cellZ(lr);
            const garden = c < edge or c >= cols - edge;

            villageBlock(b, c, hr, base);
            villageBlock(b, c, lr, lane_y);

            if (garden) {
                gardenCell(b, x, lane_y, lz);
                gardenCell(b, x, base, hz);

                if (c == 0 or c == cols - 1) parapetZ(b, if (c < 12) x - 2.0 else x + 2.0, lane_y, lz);

                continue;
            }

            if (c == s0 or c == s1) {
                villageStair(b, x, hz - cell * 0.5, base);
                b.putAt(of(.geranium), vec(x - 1.6, lane_y, lz - 1.6), 0, 1);

                continue;
            }

            if (c == arch_col) {
                b.putAt(of(.arch), vec(x, lane_y, lz), half_pi, 1);
                box(b, x - 2.2, lane_y - 0.5, lz - 2.2, x + 2.2, lane_y + tier, lz - 1.6);
                box(b, x - 2.2, lane_y - 0.5, lz + 1.6, x + 2.2, lane_y + tier, lz + 2.2);
                box(b, x - 2.2, lane_y + 2.9, lz - 2.2, x + 2.2, lane_y + tier, lz + 2.2);
                loot(b, x, lane_y, lz);
            }

            if (rnd(b) < 0.08) {
                gardenCell(b, x, base, hz);
                b.putAt(of(.bougain), vec(x, base, hz + 1.9), std.math.pi, 1);
                parapetX(b, x, lane_y, hz + 2.0);
                laneClutter(b, x, lane_y, lz, c, t);

                continue;
            }

            const hk = houseKind(b, c, t);

            villageHouse(b, hk.kind, x, hz, base, hk.floors, hk.dome);

            if (hk.floors < 1.5 and !hk.dome) {
                if (rnd(b) < 0.55) parapetX(b, x, lane_y, hz - 2.0);

                if (hk.kind != of(.cube1p)) roofClutter(b, x, lane_y, hz);
            }

            if (c != arch_col and rnd(b) < 0.75) laneClutter(b, x, lane_y, lz, c, t);

            if (t == 1 and rnd(b) < 0.5) b.putAt(b.rng.pick(Kind, &.{ of(.geranium), of(.basil), of(.pot), of(.jar) }), vec(x + b.rng.range(-1.6, 1.6), base, hz - 2.6), spin(b), 1);

            if (@mod(c + t, 4) == 1) loot(b, x, lane_y, lz);

            if (@mod(c * 3 + t, 11) == 4) spawnAt(b, x, lane_y + 0.1, lz, std.math.pi);
        }
    }

    const top_y = y0 + @as(f32, @floatFromInt(tiers)) * tier;

    for ([_]f32{ -30, -12, 12, 30 }) |px| {
        b.put(of(.cypress), px, vz0 + cell * @as(f32, @floatFromInt(rows)) + 3, 0, b.rng.range(0.9, 1.15));
    }

    spawnAt(b, -8, top_y, vz0 + cell * @as(f32, @floatFromInt(rows)) + 6, std.math.pi);
    anchor_list.append(b.gpa, vec(0, top_y + 18, -90)) catch {};
    anchor_list.append(b.gpa, vec(-30, top_y + 14, -110)) catch {};
    anchor_list.append(b.gpa, vec(30, top_y + 14, -110)) catch {};
    claimRect(vx0 - 4, vz0 - 4, vx0 + cell * @as(f32, @floatFromInt(cols)) + 4, vz0 + cell * @as(f32, @floatFromInt(rows)) + 4);
}

fn gardenCell(b: *Builder, x: f32, y: f32, z: f32) void {
    const roll = rnd(b);

    if (roll < 0.35) {
        b.putAt(of(.olive), vec(x + b.rng.range(-0.6, 0.6), y, z + b.rng.range(-0.6, 0.6)), spin(b), b.rng.range(0.7, 0.9));
    } else if (roll < 0.55) {
        b.putAt(of(.lemon), vec(x, y, z), spin(b), 0.85);
    } else if (roll < 0.75) {
        b.putAt(of(.rbush), vec(x - 0.8, y, z), spin(b), 1);
        b.putAt(of(.agave), vec(x + 1.1, y, z + 0.6), spin(b), 0.9);
    } else {
        b.putAt(of(.cypress), vec(x, y, z), 0, b.rng.range(0.7, 0.9));
        b.putAt(of(.bush), vec(x + 1.2, y, z - 1.0), spin(b), 0.8);
    }
}

fn harbourRow(b: *Builder, x0: f32, dir: f32) void {
    const kinds = [_]Kind{ of(.cube2), of(.cube1p), of(.cube2c), of(.dome1), of(.cube1b) };
    const floors = [_]f32{ 2, 1, 2, 1, 1 };

    for (kinds, floors, 0..) |kind, fl, i| {
        const x = x0 + dir * @as(f32, @floatFromInt(i)) * cell;

        if (@abs(x) > 74) continue;

        const z = vz0 + cell * 2.5;

        b.putAt(of(.block), vec(x, y0, z), 0, 1);
        villageHouse(b, kind, x, z, y0, fl, kind == of(.dome1));
        b.putAt(of(.block), vec(x, y0, z - cell), 0, 1);

        if (i % 2 == 0) {
            b.putAt(of(.taverna), vec(x, y0, z - 3.6), half_pi, 1);
            b.putAt(of(.parasol), vec(x, y0, z - 3.6), 0, 0.9);
        } else {
            b.putAt(of(.pot), vec(x - 1.4, y0, z - 2.7), 0, 1);
            b.putAt(of(.bougain), vec(x + 0.6, y0, z - 2.35), 0, 1);
        }
    }

    claimRect(@min(x0, x0 + dir * 13) - 3, vz0 - 2, @max(x0, x0 + dir * 13) + 3, vz0 + cell * 3 + 3);
}

fn harbourQuay(b: *Builder) void {
    const qz = vz0 + cell * 0.5;
    const front = vz0 - 0.2;

    var x: f32 = vx0 - 2.2;

    while (x > -76) : (x -= cell) {
        b.putAt(of(.quay), vec(x, y0, qz), 0, 1);
        box(b, x - 2.2, y0 - 6, qz - 2.2, x + 2.2, y0, qz + 2.2);
    }

    x = vx0 + cell * @as(f32, @floatFromInt(cols)) + 2.2;

    while (x < 76) : (x += cell) {
        b.putAt(of(.quay), vec(x, y0, qz), 0, 1);
        box(b, x - 2.2, y0 - 6, qz - 2.2, x + 2.2, y0, qz + 2.2);
    }

    var z: f32 = qz - cell;

    while (z > -166) : (z -= cell) {
        b.putAt(of(.quay), vec(pier_x, y0, z), 0, 1);
        box(b, pier_x - 2.2, y0 - 6, z - 2.2, pier_x + 2.2, y0, z + 2.2);

        if (@mod(@as(i32, @intFromFloat(@abs(z))), 3) == 0) b.putAt(of(.bollard), vec(pier_x - 1.8, y0, z), half_pi, 1);
    }

    b.putAt(of(.quay), vec(pier_x, y0, -169.4), 0, 1);
    box(b, pier_x - 2.2, y0 - 6, -171.6, pier_x + 2.2, y0, -167.2);
    b.putAt(of(.light), vec(pier_x, y0, -169.4), 0, 0.9);
    anchor_list.append(b.gpa, vec(pier_x, 22, -160)) catch {};

    for ([_][4]f32{ .{ -36, -141, 0.12, 1 }, .{ -16, -139, -0.08, 0.95 }, .{ 8, -142, 0.05, 1 }, .{ 30, -140, -0.15, 0.9 }, .{ 56, -152, 1.45, 0.85 }, .{ 73, -146, 1.6, 0.9 }, .{ -62, -142, 0.3, 0.85 } }) |bt| {
        b.putAt(of(.boat), vec(bt[0], sea_y - 0.55, bt[1]), bt[2], bt[3]);
    }

    var i: i32 = 0;

    while (i < 34) : (i += 1) {
        const px = -72 + @as(f32, @floatFromInt(i)) * 4.3;

        if (px > 76) continue;

        if (@mod(i, 3) == 0) b.putAt(of(.bollard), vec(px, y0, front + 0.9), 0, 1);

        const roll = rnd(b);

        if (roll < 0.18) {
            b.putAt(of(.nets), vec(px + 1.5, y0, front + 2.6), spin(b), 1);
        } else if (roll < 0.3) {
            b.putAt(of(.nets), vec(px + 1.2, y0, front + 2.2), quarter(b), 1);
            b.putAt(of(.nets), vec(px + 2.0, y0, front + 2.4), quarter(b), 1);
            b.putAt(of(.rope), vec(px + 0.4, y0, front + 1.8), spin(b), 1);
        } else if (roll < 0.4) {
            b.putAt(of(.barrel), vec(px + 1.5, y0, front + 2.2), spin(b), 1);
            b.putAt(of(.barrel), vec(px + 2.3, y0, front + 2.5), spin(b), 1);
        } else if (roll < 0.48) {
            b.putAt(of(.rope), vec(px + 1.2, y0, front + 1.6), spin(b), 1);
        }
    }

    const plaza_z = cellZ(2);

    for ([_]f32{ -40, -24, -6, 14, 30, 42 }, 0..) |px, n| {
        if (n % 2 == 0) {
            b.putAt(of(.parasol), vec(px, y0, plaza_z), 0, 1);
            b.putAt(of(.taverna), vec(px - 0.2, y0, plaza_z), half_pi, 1);
            b.putAt(of(.taverna), vec(px + 2.4, y0, plaza_z + 0.6), 0.3, 1);
            b.putAt(of(.chair), vec(px + 1.3, y0, plaza_z - 1.4), 2.6, 1);
        } else {
            b.putAt(of(.lamp), vec(px, y0, plaza_z - 2), 0, 1);
            b.putAt(of(.kafe), vec(px + 1.6, y0, plaza_z + 0.4), 0, 1);
            b.putAt(of(.chair), vec(px + 2.4, y0, plaza_z + 0.4), -half_pi, 1);
            b.putAt(of(.chair), vec(px + 0.8, y0, plaza_z + 0.4), half_pi, 1);
            b.putAt(of(.pot), vec(px - 1.6, y0, plaza_z + 1.4), 0, 1.2);
        }
    }

    b.putAt(of(.melon), vec(-31, y0, cellZ(1)), half_pi, 1);
    b.putAt(of(.truck), vec(20, y0, cellZ(1) + 0.4), -half_pi + 0.1, 1);
    b.putAt(of(.moped), vec(-2, y0, cellZ(1)), 0.4, 1);
    b.putAt(of(.moped), vec(-0.8, y0, cellZ(1) + 0.3), 0.5, 1);
    b.putAt(of(.barrow), vec(36, y0, cellZ(1)), 1.2, 1);

    for ([_]f32{ -70, -60, 64, 72 }) |px| b.putAt(of(.lamp), vec(px, y0, qz + 1.4), 0, 1);

    b.putAt(of(.boathouse), vec(-68, tr.height(-68, -118) + 0.1, -118), 0, 1);
    b.putAt(of(.nets), vec(-63, y0, -124), 0.4, 1);
    b.putAt(of(.cypress), vec(-74, y0, -112), 0, 1);
    b.putAt(of(.pine), vec(-60, y0, -112), spin(b), 1.0);
    b.putAt(of(.pine), vec(68, y0, -116), spin(b), 0.9);
    b.putAt(of(.hay), vec(70, y0, -122), 0.3, 1);
    b.putAt(of(.jar), vec(62, y0, -120), 0, 1);

    spawnAt(b, -56, y0, -126, 0);
    spawnAt(b, 66, y0, -124, 0);
    spawnAt(b, pier_x, y0, -152, 0);
    loot(b, pier_x, y0, -160);
    loot(b, -58, y0, -128);
    loot(b, 0, y0, cellZ(1));
    loot(b, 40, y0, cellZ(1));
}

fn wallRun(b: *Builder, kind: Kind, x0: f32, z0: f32, x1: f32, z1: f32, gap: u32) void {
    const dx = x1 - x0;
    const dz = z1 - z0;
    const len = @sqrt(dx * dx + dz * dz);
    const n: u32 = @intFromFloat(@max(1, @round(len / 4)));
    const yaw = std.math.atan2(-dz, dx);
    var i: u32 = 0;

    while (i < n) : (i += 1) {
        if (gap > 0 and i % gap == gap - 1) continue;

        const t = (@as(f32, @floatFromInt(i)) + 0.5) / @as(f32, @floatFromInt(n));
        const px = x0 + dx * t;
        const pz = z0 + dz * t;

        if (coastDistance(px, pz) < 4 or villageOut(px, pz) < 2) continue;

        wallPiece(b, kind, px, tr.height(px, pz) - 0.12, pz, yaw);
        claim(px, pz, 1);
    }
}

fn wallPiece(b: *Builder, kind: Kind, x: f32, y: f32, z: f32, yaw: f32) void {
    const info = api.props.info(kind);
    const top = y + info.max[1];
    const half_t = (info.max[2] - info.min[2]) * 0.5;
    var i: f32 = -1.5;

    b.putAt(kind, vec(x, y, z), yaw, 1);

    while (i <= 1.5) : (i += 1) {
        const p = wd.rotPoint(x, z, yaw, i, 0);
        const r = @max(half_t, 0.3);

        box(b, p[0] - r, y - 0.5, p[1] - r, p[0] + r, top, p[1] + r);
    }
}

fn windmills(b: *Builder) void {
    for (mills, 0..) |m, n| {
        const y = wd.lowest(m[0], m[1], 2.8) + 0.4;

        b.putAt(of(.windmill), vec(m[0], y, m[1]), m[2], 1);
        b.solid(.{ .cylinder = .{ .base = vec(m[0], y - 0.5, m[1]), .radius = 2.7, .height = 9 } });
        claim(m[0], m[1], 6);

        const s = @sin(m[2]);
        const c_ = @cos(m[2]);

        b.put(of(.jar), m[0] + 3.6 * c_, m[1] - 3.6 * s, 0, 1);
        b.put(of(.sack), m[0] + 4.2 * c_ + 0.6, m[1] - 4.2 * s, 0.3, 1);
        b.put(of(.agave), m[0] - 4 * c_, m[1] + 4 * s, spin(b), 0.9);
        b.put(of(.rbush), m[0] - 3 * c_ + 2, m[1] + 3 * s - 3, spin(b), 1);
        loot(b, m[0] + 4, tr.height(m[0] + 4, m[1] + 4), m[1] + 4);

        if (n == 1) {
            spawnAt(b, m[0] + 6, tr.height(m[0] + 6, m[1] - 6), m[1] - 6, std.math.pi);
            anchor_list.append(b.gpa, vec(m[0], y + 24, m[1])) catch {};
        }
    }

    wallRun(b, of(.swall), -36, -4, -16, -6, 0);
    wallRun(b, of(.swall), 2, 4, 24, 4, 3);
    wallRun(b, of(.swall), -20, 36, 4, 36, 4);
}

fn farmstead(b: *Builder) void {
    const fx = farm[0];
    const fz = farm[1];
    const y = natural(fx, fz) + 0.2;
    const lots = [_][4]f32{ .{ -8, -6, 0, 2 }, .{ -3.6, -6, 0, 1 }, .{ 6, -8, half_pi, 1 }, .{ 10, 4, half_pi, 2 } };
    const kinds = [_]Kind{ of(.cube2b), of(.cube1p), of(.cube1c), of(.cube2c) };

    for (lots, kinds) |l, kind| {
        const x = fx + l[0];
        const z = fz + l[1];
        const base = wd.lowest(x, z, 2.2) + 0.3;

        b.putAt(of(.block), vec(x, base, z), 0, 1);
        box(b, x - 2.2, base - 17, z - 2.2, x + 2.2, base, z + 2.2);
        villageHouse(b, kind, x, z, base, l[3], false);
        claim(x, z, 3);
    }

    wallRun(b, of(.gwall), fx - 16, fz - 14, fx + 16, fz - 14, 4);
    wallRun(b, of(.gwall), fx - 16, fz + 14, fx + 16, fz + 14, 0);
    wallRun(b, of(.gwall), fx - 16, fz - 14, fx - 16, fz + 14, 3);
    wallRun(b, of(.gwall), fx + 16, fz - 14, fx + 16, fz + 14, 0);

    b.put(of(.tractor), fx + 2, fz + 6, 0.1, 1);
    b.put(of(.jar), fx - 6, fz + 5, 0.2, 1);
    b.put(of(.haystack), fx + 11, fz + 10, 0, 1);
    b.put(of(.haystack), fx + 13.5, fz + 8, 0.6, 0.85);
    b.put(of(.hay), fx - 12, fz + 10, 0.2, 1);
    b.put(of(.hay), fx - 11, fz + 11.2, 0.2, 1);
    b.put(of(.hay), fx - 11.5, fz + 10.6, 1.4, 1);
    b.put(of(.barrow), fx - 2, fz + 10, 1.1, 1);
    b.put(of(.sack), fx - 3, fz + 9, 0, 1);
    b.put(of(.sack), fx - 3.6, fz + 9.4, 0.5, 1);
    b.put(of(.barrel), fx + 4, fz - 2, 0, 1);
    b.put(of(.barrel), fx + 4.8, fz - 2.4, 0.4, 1);
    b.put(of(.jar), fx - 1, fz - 1.6, 0, 1);
    b.put(of(.pot), fx - 0.2, fz - 1.8, 0, 1);
    b.put(of(.lemon), fx - 12, fz - 9, spin(b), 1);
    b.put(of(.lemon), fx + 13, fz - 9, spin(b), 0.9);
    b.put(of(.cypress), fx - 18, fz - 16, 0, 1.1);
    b.put(of(.cypress), fx + 18, fz - 16, 0, 1.0);
    b.put(of(.truck), fx + 8, fz - 1, std.math.pi - 0.1, 1);
    claimRect(fx - 17, fz - 15, fx + 17, fz + 15);

    loot(b, fx, y, fz);
    loot(b, fx + 9, y, fz + 9);
    spawnAt(b, fx + 4, y, fz + 3, std.math.pi);
    spawnAt(b, fx - 20, tr.height(fx - 20, fz - 20), fz - 20, 2.4);
    anchor_list.append(b.gpa, vec(fx, y + 18, fz)) catch {};
    park_list.append(b.gpa, .{ .pos = vec(fx - 8, tr.height(fx - 8, fz - 24), fz - 24), .yaw = 0.3 }) catch {};
}

fn quarrySite(b: *Builder) void {
    const qx = quarry[0];
    const qz = quarry[1];
    const floor_y = tr.height(qx, qz);

    claimRect(qx - 34, qz - 26, qx + 34, qz + 26);

    var bench: f32 = 1;

    while (bench <= 4) : (bench += 1) {
        const e = 1.05 - bench / 6;
        const hx = 26 * e;
        const hz = 20 * e;

        quarryEdge(b, qx - hx, qz + hz, qx + hx, qz + hz, std.math.pi);
        quarryEdge(b, qx - hx, qz - hz, qx + hx, qz - hz, 0);
        quarryEdge(b, qx + hx, qz - hz, qx + hx, qz + hz, -half_pi);
        quarryEdge(b, qx - hx, qz - hz, qx - hx, qz + hz, half_pi);
    }

    for ([_][3]f32{ .{ -6, 4, 0.1 }, .{ -3.8, 4.3, 0.05 }, .{ -5, 6, 1.5 }, .{ 6, -2, 0.4 }, .{ 8, -1, 0.5 }, .{ 7, 0.6, 0.45 }, .{ -12, -6, 1.2 }, .{ 12, 8, 0.0 } }) |s| {
        b.put(of(.sblock), qx + s[0], qz + s[1], s[2], 1);
    }

    b.putAt(of(.sblock), vec(qx - 3.8, floor_y + 1.14, qz + 4.3), 0.1, 1);
    b.putAt(of(.sblock), vec(qx + 7, floor_y + 1.14, qz - 1), 0.5, 1);

    for ([_][3]f32{ .{ 0, -4, 0 }, .{ 1.6, -4, 0 }, .{ 3.2, -4.2, 0.1 }, .{ -14, 2, 1.2 }, .{ -14, 3.4, 1.2 }, .{ 14, -6, 0.4 } }) |p| b.put(of(.pallet), qx + p[0], qz + p[1], p[2], 1);

    b.put(of(.digger), qx - 4, qz - 10, std.math.pi + 0.1, 1);
    b.put(of(.truck), qx + 10, qz - 12, -half_pi + 0.08, 1);
    b.put(of(.rock), qx + 16, qz + 4, 0.3, 1.2);
    b.put(of(.rock), qx - 16, qz + 10, 1.8, 1.2);
    b.put(of(.rock), qx - 2, qz + 12, 0.8, 1.2);
    b.put(of(.barrow), qx + 2, qz + 2, 0.4, 1);

    var i: f32 = 0;

    while (i < 5) : (i += 1) {
        b.put(of(.sblock), qx - 18 + i * 2.2, qz - 2, 0, 1);
        b.put(of(.sblock), qx - 17 + i * 2.2, qz - 0.6, 0.05, 1);

        if (i < 3) b.putAt(of(.sblock), vec(qx - 17.5 + i * 2.2, tr.height(qx - 17.5 + i * 2.2, qz - 1.3) + 1.1, qz - 1.3), 0, 1);

        b.put(of(.pallet), qx + 14 + i * 1.5, qz + 2, 0, 1);
    }

    b.put(of(.rock), qx + 6, qz + 6, 2.1, 1.2);
    b.put(of(.digger), qx + 15, qz - 5, half_pi + 0.06, 1);
    b.put(of(.barrel), qx + 9, qz - 8, 0, 1);
    b.put(of(.barrel), qx + 9.9, qz - 8.3, 0, 1);

    for ([_][2]f32{ .{ -30, -14 }, .{ 30, -20 }, .{ 32, 18 }, .{ -32, 20 }, .{ 0, 26 }, .{ 20, 26 } }) |o| {
        b.put(of(.outcrop), qx + o[0], qz + o[1], spin(b), b.rng.range(0.9, 1.3));
    }

    loot(b, qx, floor_y, qz);
    loot(b, qx + 12, tr.height(qx + 12, qz + 8), qz + 8);
    loot(b, qx - 12, tr.height(qx - 12, qz - 6), qz - 6);
    spawnAt(b, qx - 8, floor_y, qz - 2, -half_pi);
    spawnAt(b, qx + 26, tr.height(qx + 26, qz - 24), qz - 24, 0.8);
    anchor_list.append(b.gpa, vec(qx, floor_y + 20, qz)) catch {};
    park_list.append(b.gpa, .{ .pos = vec(qx - 20, tr.height(qx - 20, qz - 30), qz - 30), .yaw = 1.2 }) catch {};
}

fn quarryEdge(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32, yaw: f32) void {
    const len = @max(@abs(x1 - x0), @abs(z1 - z0));
    const n: u32 = @intFromFloat(@max(1, @floor(len / 6)));
    const ix = std.math.sign(x1 - x0);
    const iz = std.math.sign(z1 - z0);
    const inx = @sin(yaw);
    const inz = @cos(yaw);
    var i: u32 = 0;

    while (i < n) : (i += 1) {
        const t = (@as(f32, @floatFromInt(i)) + 0.5) * len / @as(f32, @floatFromInt(n));
        const px = x0 + ix * t;
        const pz = z0 + iz * t;

        if (yaw == 0 and @abs(px - quarry[0]) < 7) continue;

        const lo_y = tr.height(px + inx * 1.6, pz + inz * 1.6);
        const hi_y = tr.height(px - inx * 1.6, pz - inz * 1.6);

        if (hi_y - lo_y < 1.2) continue;

        b.putAt(of(.qface), vec(px, lo_y - 0.15, pz), yaw, 1);

        const a = wd.rotBox(px, pz, yaw, -3, -0.8, 3, 0.3);

        box(b, a[0], lo_y - 0.5, a[1], a[2], hi_y, a[3]);
    }
}

fn hamletSite(b: *Builder) void {
    const hx = hamlet[0];
    const hz = hamlet[1];
    const lots = [_][4]f32{ .{ -6.6, -5, 0, 1 }, .{ -2.2, -5, 0, 2 }, .{ 4.4, -6, 0, 1 }, .{ -6.6, 7, 0, 1 }, .{ 2.2, 7, 0, 2 }, .{ 8, 6, 0, 1 } };
    const kinds = [_]Kind{ of(.cube1), of(.cube2), of(.dome1), of(.cave1), of(.cube2b), of(.cube1b) };

    for (lots, kinds) |l, kind| {
        const x = hx + l[0];
        const z = hz + l[1];
        const base = wd.lowest(x, z, 2.2) + 0.3;
        const floors: f32 = if (kind == of(.cube2) or kind == of(.cube2b)) 2 else 1;

        b.putAt(of(.block), vec(x, base, z), 0, 1);
        box(b, x - 2.2, base - 17, z - 2.2, x + 2.2, base, z + 2.2);
        villageHouse(b, kind, x, z, base, floors, kind == of(.dome1));
        b.putAt(of(.geranium), vec(x - 1.2, tr.height(x - 1.2, z + (if (l[1] < 0) @as(f32, 2.7) else -2.7)), z + (if (l[1] < 0) @as(f32, 2.7) else -2.7)), 0, 1);
    }

    claimRect(hx - 12, hz - 10, hx + 13, hz + 12);
    b.put(of(.taverna), hx, hz + 1, half_pi, 1);
    b.put(of(.parasol), hx, hz + 1, 0, 1);
    b.put(of(.lamp), hx + 4, hz + 2, 0, 1);
    b.put(of(.moped), hx - 4, hz + 1.5, 1.2, 1);
    b.put(of(.melon), hx + 7, hz + 0.5, half_pi, 1);
    b.put(of(.bougain), hx - 2.2, hz - 2.4, 0, 1);

    wallRun(b, of(.gwall), hx - 16, hz - 12, hx + 16, hz - 12, 4);
    wallRun(b, of(.gwall), hx - 16, hz + 14, hx + 16, hz + 14, 3);

    for ([_][2]f32{ .{ -14, 2 }, .{ 15, -2 }, .{ 0, 18 }, .{ -12, 17 }, .{ 13, 17 } }) |o| b.put(if (rnd(b) < 0.5) of(.olive) else of(.cypress), hx + o[0], hz + o[1], spin(b), b.rng.range(0.85, 1.05));

    loot(b, hx + 1, tr.height(hx + 1, hz + 3), hz + 3);
    loot(b, hx - 9, tr.height(hx - 9, hz + 1), hz + 1);
    spawnAt(b, hx + 3, tr.height(hx + 3, hz + 1.5), hz + 1.5, -half_pi);
    anchor_list.append(b.gpa, vec(hx, tr.height(hx, hz) + 16, hz)) catch {};
    park_list.append(b.gpa, .{ .pos = vec(hx - 18, tr.height(hx - 18, hz - 2), hz - 2), .yaw = half_pi }) catch {};
}

fn coveSite(b: *Builder) void {
    const cx = cove[0];
    const cz = cove[1];
    const ang = std.math.atan2(cz, cx);
    const dx = @cos(ang);
    const dz = @sin(ang);
    const rr = islandEdge(cx, cz);
    const hx = dx * (rr - 10);
    const hz = dz * (rr - 10);
    const yaw = std.math.atan2(dx, dz);

    b.putAt(of(.boathouse), vec(hx, wd.lowest(hx, hz, 4) + 0.3, hz), yaw, 1);
    claim(hx, hz, 6);
    b.putAt(of(.boat), vec(dx * (rr + 8), sea_y - 0.55, dz * (rr + 8)), yaw + 0.4, 0.9);
    b.putAt(of(.boat), vec(dx * (rr + 14) - dz * 9, sea_y - 0.55, dz * (rr + 14) + dx * 9), yaw - 0.8, 0.8);

    for ([_][2]f32{ .{ -8, 4 }, .{ 8, 2 }, .{ -4, -8 }, .{ 6, -6 } }) |o| {
        const px = hx - dz * o[0] - dx * o[1];
        const pz = hz + dx * o[0] - dz * o[1];

        b.put(if (o[1] > 0) of(.nets) else of(.pine), px, pz, spin(b), 1);
    }

    b.put(of(.parasol), hx - dz * 12 + dx * 4, hz + dx * 12 + dz * 4, 0, 1);
    b.put(of(.nets), hx - dz * 4 + dx * 5, hz + dx * 4 + dz * 5, yaw, 1);
    b.put(of(.rope), hx + dz * 3 + dx * 4, hz - dx * 3 + dz * 4, 0, 1);
    loot(b, hx - dx * 5, tr.height(hx - dx * 5, hz - dz * 5), hz - dz * 5);
    spawnAt(b, hx - dx * 12, tr.height(hx - dx * 12, hz - dz * 12), hz - dz * 12, std.math.atan2(dx, dz) + std.math.pi);
}

fn terraces(b: *Builder) void {
    for (grove_rects, 0..) |g, gi| {
        const lo = if (g.along_z) g.z0 else g.x0;
        const hi = if (g.along_z) g.z1 else g.x1;
        const a0 = if (g.along_z) g.x0 else g.z0;
        const a1 = if (g.along_z) g.x1 else g.z1;
        var v = lo + band_w;

        while (v < hi) : (v += band_w) {
            var a = a0 + 2;

            while (a < a1 - 1) : (a += 4) {
                const x = if (g.along_z) a else v;
                const z = if (g.along_z) v else a;

                if (coastDistance(x, z) < 6 or villageOut(x, z) < 3 or pathDistance(x, z) < 3 or taken(x, z, 0.5)) continue;

                const e: f32 = 1.1;
                const ha = if (g.along_z) tr.height(x, z - e) else tr.height(x - e, z);
                const hb = if (g.along_z) tr.height(x, z + e) else tr.height(x + e, z);
                const upper = @max(ha, hb);

                if (upper - @min(ha, hb) < 0.35) continue;

                wallPiece(b, of(.swall), x, upper + 0.2 - 1.36, z, if (g.along_z) 0 else half_pi);
            }
        }

        v = lo + band_w * 0.5;

        var row: u32 = 0;

        while (v < hi) : (v += band_w) {
            row += 1;

            var a = a0 + 3 + @as(f32, @floatFromInt(row % 2)) * 3.5;

            while (a < a1 - 2) : (a += 7) {
                const j = b.rng.range(-0.6, 0.6);
                const x = if (g.along_z) a + j else v + j * 0.3;
                const z = if (g.along_z) v + j * 0.3 else a + j;

                if (coastDistance(x, z) < 7 or villageOut(x, z) < 5 or pathDistance(x, z) < 3.5 or taken(x, z, 1.5)) continue;

                const roll = rnd(b);

                if (roll < 0.84) {
                    b.put(of(.olive), x, z, spin(b), b.rng.range(0.85, 1.15));
                } else if (roll < 0.92 and gi == 2) {
                    b.put(of(.lemon), x, z, spin(b), b.rng.range(0.8, 1));
                } else if (roll < 0.95) {
                    b.put(of(.haystack), x, z, spin(b), 0.8);
                } else {
                    b.put(of(.barrow), x, z, spin(b), 1);
                }

                claim(x, z, 1.5);

                if (rnd(b) < 0.3) b.put(of(.rbush), x + b.rng.range(-2.5, 2.5), z + b.rng.range(-2.5, 2.5), spin(b), b.rng.range(0.5, 0.8));
            }
        }
    }
}

fn scrubland(b: *Builder) void {
    const lim: f32 = 168;
    var z: f32 = -lim;

    while (z < lim) : (z += 3.4) {
        var x: f32 = -lim;

        while (x < lim) : (x += 3.4) {
            const px = x + b.rng.range(-1.5, 1.5);
            const pz = z + b.rng.range(-1.5, 1.5);
            const cd = coastDistance(px, pz);

            if (cd < 1.5 or villageOut(px, pz) < 3 or pathDistance(px, pz) < 2.6 or taken(px, pz, 0.6)) continue;

            if (z < -112 and @abs(px) < 78) continue;

            const g = groveMask(px, pz);
            const n = tr.normal(px, pz);
            const roll = rnd(b);
            const yaw = spin(b);

            if (cd < 9 and tr.height(px, pz) < sea_y + 1.6) {
                if (roll < 0.06) b.put(of(.pine), px, pz, yaw, b.rng.range(0.8, 1.1)) else if (roll < 0.2) b.put(of(.rbush), px, pz, yaw, b.rng.range(0.6, 0.9));

                continue;
            }

            if (n.y < 0.8) {
                if (roll < 0.22) b.put(of(.rock), px, pz, yaw, b.rng.range(0.8, 1.6)) else if (roll < 0.4) b.put(of(.bush), px, pz, yaw, b.rng.range(0.8, 1.2)) else if (roll < 0.5) b.put(of(.shrub), px, pz, yaw, 1) else if (roll < 0.53) b.put(of(.outcrop), px, pz, yaw, b.rng.range(0.7, 1.1));

                continue;
            }

            if (g > 0.55) {
                if (roll < 0.08) b.put(of(.rbush), px, pz, yaw, 0.7);

                continue;
            }

            if (roll < 0.2) {
                b.put(of(.bush), px, pz, yaw, b.rng.range(0.8, 1.3));
            } else if (roll < 0.32) {
                b.put(of(.rbush), px, pz, yaw, b.rng.range(0.8, 1.2));
            } else if (roll < 0.42) {
                b.put(of(.shrub), px, pz, yaw, b.rng.range(0.6, 0.9));
            } else if (roll < 0.47) {
                b.put(of(.shrub), px, pz, yaw, b.rng.range(0.8, 1.1));
            } else if (roll < 0.51) {
                b.put(of(.shrub), px, pz, yaw, b.rng.range(0.8, 1.2));
            } else if (roll < 0.54) {
                b.put(of(.agave), px, pz, yaw, b.rng.range(0.7, 1.0));
            } else if (roll < 0.57) {
                b.put(of(.agave), px, pz, yaw, b.rng.range(0.8, 1.1));
            } else if (roll < 0.6) {
                b.put(of(.rock), px, pz, yaw, b.rng.range(0.6, 1.2));
            } else if (roll < 0.615) {
                b.put(of(.olive), px, pz, yaw, b.rng.range(0.8, 1.0));
            } else if (roll < 0.625) {
                b.put(of(.cypress), px, pz, 0, b.rng.range(0.8, 1.1));
            }
        }
    }
}

fn pathEdges(b: *Builder) void {
    for (paths, 0..) |s, n| {
        const dx = s[2] - s[0];
        const dz = s[3] - s[1];
        const len = @sqrt(dx * dx + dz * dz);
        const nx = -dz / len;
        const nz = dx / len;
        var t: f32 = 6;

        while (t < len - 4) : (t += 9) {
            const px = s[0] + dx / len * t;
            const pz = s[1] + dz / len * t;
            const side: f32 = if ((@as(u32, @intFromFloat(t)) + n) % 2 == 0) 1 else -1;
            const qx = px + nx * 3.6 * side;
            const qz = pz + nz * 3.6 * side;

            if (coastDistance(qx, qz) < 5 or villageOut(qx, qz) < 3 or taken(qx, qz, 0.5)) continue;

            const roll = rnd(b);

            if (roll < 0.3) {
                b.put(of(.cypress), qx, qz, 0, b.rng.range(0.85, 1.1));
                claim(qx, qz, 1);
            } else if (roll < 0.55) {
                wallPiece(b, of(.swall), qx, tr.height(qx, qz) - 0.15, qz, std.math.atan2(-dz, dx));
                claim(qx, qz, 1.5);
            } else if (roll < 0.7) {
                b.put(of(.agave), qx, qz, spin(b), 0.9);
            } else if (roll < 0.8) {
                b.put(of(.pot), qx, qz, spin(b), 1.2);
            }
        }
    }
}

fn shoreFoam(b: *Builder) void {
    var a: f32 = 0;

    while (a < std.math.tau) : (a += 0.035) {
        const dx = @cos(a);
        const dz = @sin(a);
        const rr = islandEdge(dx * 150, dz * 150);
        const yaw = std.math.atan2(-dx, -dz);
        const quay_front = dz * rr < -125 and @abs(dx * rr) < 76;
        const off: f32 = if (quay_front) 0.6 else 1.6;

        b.putAt(of(.foam), vec(dx * (rr + off), sea_y + 0.01, dz * (rr + off)), yaw + b.rng.range(-0.1, 0.1), b.rng.range(0.85, 1.15));

        if (@mod(@as(u32, @intFromFloat(a * 100)), 2) == 0) b.putAt(of(.ripple), vec(dx * (rr + 6 + b.rng.range(0, 4)), sea_y + 0.008, dz * (rr + 6 + b.rng.range(0, 4))), yaw, b.rng.range(0.8, 1.2));
    }

    var z: f32 = -134;

    while (z > -168) : (z -= 6) {
        b.putAt(of(.foam), vec(pier_x - 2.6, sea_y + 0.01, z), half_pi, 0.9);
        b.putAt(of(.foam), vec(pier_x + 2.6, sea_y + 0.01, z - 3), half_pi, 0.9);
    }
}

fn build(b: *Builder) void {
    @memset(&occ, 0);
    wd.kit_loot = .empty;
    spawn_list = .empty;
    spawn_yaw = .empty;
    anchor_list = .empty;
    park_list = .empty;

    medVillage(b);
    windmills(b);
    farmstead(b);
    quarrySite(b);
    hamletSite(b);
    coveSite(b);
    pathEdges(b);
    terraces(b);
    scrubland(b);
    shoreFoam(b);

    for ([_][2]f32{ .{ -90, 10 }, .{ 100, 10 }, .{ -100, -60 }, .{ 90, -40 }, .{ -40, 64 }, .{ 48, 56 } }) |p| {
        spawnAt(b, p[0], tr.height(p[0], p[1]), p[1], std.math.atan2(-p[0], -p[1]));
        loot(b, p[0] + 3, tr.height(p[0] + 3, p[1] + 3), p[1] + 3);
    }
}

fn setSpots(gpa: std.mem.Allocator) void {
    var spawns: std.ArrayList(Vec3) = .empty;
    var yaws: std.ArrayList(f32) = .empty;
    var spots: std.ArrayList(Vec3) = .empty;
    var anchors: std.ArrayList(Vec3) = .empty;
    var parked: std.ArrayList(wd.Spot) = .empty;

    for (wd.kit_loot.items) |p| spots.append(gpa, p) catch {};

    for (spawn_list.items, spawn_yaw.items) |p, y| {
        spawns.append(gpa, p) catch {};
        yaws.append(gpa, y) catch {};
    }

    for (anchor_list.items) |p| anchors.append(gpa, p) catch {};

    for (park_list.items) |p| parked.append(gpa, p) catch {};

    wd.spawns = spawns.toOwnedSlice(gpa) catch &.{};
    wd.spawn_yaws = yaws.toOwnedSlice(gpa) catch &.{};
    wd.weapon_spots = spots.toOwnedSlice(gpa) catch &.{};
    wd.drone_anchors = anchors.toOwnedSlice(gpa) catch &.{};
    wd.vehicle_spots = parked.toOwnedSlice(gpa) catch &.{};
    wd.parkClear(gpa);
}
