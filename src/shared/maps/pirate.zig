const std = @import("std");
const api = @import("api.zig");
const k = @import("pirate_kit.zig");

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
const pi = std.math.pi;

pub const def: api.Def = .{
    .name = "Pirate Cove",
    .note = "Lagoon docks, ships and a hilltop fort",
    .tint = .{ 120, 190, 170 },
    .half = 210,
    .play = 168,
    .facet = 2.0,
    .height = height,
    .ground = groundColor,
    .build = build,
    .spots = setSpots,
    .props = &k.table,
    .palette = .{
        .sun_dir = .{ 0.4, 0.72, -0.56 },
        .sun_tint = .{ 1.18, 1.04, 0.86 },
        .grade_tint = .{ 1.04, 1.0, 0.94 },
        .grade_sat = 1.18,
        .fog = 0.0024,
        .fog_color = .{ 0.68, 0.86, 0.9 },
        .amb_sky = .{ 0.88, 1.02, 1.14 },
        .amb_ground = .{ 0.86, 0.8, 0.6 },
        .shade_tint = .{ 0.84, 0.94, 1.06 },
        .zenith = .{ 0.06, 0.34, 0.66 },
    },
    .backdrop = .{ 24, 100, 128 },
    .floor_y = 0.12,
    .grip = 0.84,
    .tufts = 0.45,
};

const sea_y: f32 = 0.35;
const town_y: f32 = 2.6;
const dock_top: f32 = sea_y + 1.25;

const Isle = struct { x: f32, z: f32, rx: f32, rz: f32, h: f32, seed: f32 };

const isles = [_]Isle{
    .{ .x = 0, .z = -128, .rx = 160, .rz = 64, .h = 5, .seed = 1 },
    .{ .x = -132, .z = 12, .rx = 54, .rz = 112, .h = 18, .seed = 2 },
    .{ .x = 40, .z = 128, .rx = 110, .rz = 44, .h = 13, .seed = 3 },
    .{ .x = 136, .z = -24, .rx = 30, .rz = 38, .h = 2.2, .seed = 4 },
    .{ .x = -18, .z = 26, .rx = 18, .rz = 13, .h = 1.6, .seed = 5 },
    .{ .x = 56, .z = 14, .rx = 13, .rz = 11, .h = 1.4, .seed = 6 },
};

fn isleE(i: Isle, x: f32, z: f32) f32 {
    const dx = (x - i.x) / i.rx;
    const dz = (z - i.z) / i.rz;
    const ang = std.math.atan2(dz, dx);
    const wob = 0.88 + 0.24 * tr.fbm(@cos(ang) * 1.5 + i.seed * 3.1, @sin(ang) * 1.5 + i.seed * 1.7);

    return @sqrt(dx * dx + dz * dz) / wob;
}

fn coast(x: f32, z: f32) f32 {
    var best: f32 = 9;

    for (isles) |i| best = @min(best, isleE(i, x, z));

    return best;
}

fn isleHeight(i: Isle, e: f32, x: f32, z: f32) f32 {
    if (e >= 1) return -1;

    const beach = tr.smooth(1, 0.86, e);
    const body = tr.smooth(0.9, 0.35, e);
    const hills = (tr.fbm(x * 0.03 + i.seed * 7, z * 0.03 - i.seed * 3) - 0.35) * i.h * 0.9;
    const top = i.h + @max(hills, -i.h * 0.4);

    return sea_y + beach * 1.0 + body * top;
}

fn townMask(x: f32, z: f32) f32 {
    const dx = @max(@abs(x) - 92, 0);
    const dz = @max(@abs(z + 104) - 32, 0);

    return 1 - tr.smooth(0, 14, @sqrt(dx * dx + dz * dz));
}

fn fortMask(x: f32, z: f32) f32 {
    return 1 - tr.smooth(16, 30, dist(x, z, fort));
}

const fort = [2]f32{ 92, 128 };
const camp = [2]f32{ -112, 34 };

fn dist(x: f32, z: f32, p: [2]f32) f32 {
    return @sqrt((x - p[0]) * (x - p[0]) + (z - p[1]) * (z - p[1]));
}

fn height(x: f32, z: f32) f32 {
    var h: f32 = sea_y - 0.02;

    for (isles) |i| h = @max(h, isleHeight(i, isleE(i, x, z), x, z));

    const tm = townMask(x, z) * tr.smooth(-62, -76, z);

    if (tm > 0) h = h * (1 - tm) + (town_y + (tr.fbm(x * 0.05, z * 0.05) - 0.5) * 0.6) * tm;

    const fm = fortMask(x, z);

    if (fm > 0) h = h * (1 - fm) + (isleHeight(isles[2], isleE(isles[2], fort[0], fort[1]), fort[0], fort[1])) * fm;

    return h;
}

fn waterColor(x: f32, z: f32) api.Rgb {
    const e = coast(x, z);
    const wave = tr.fbm(x * 0.05 + 3, z * 0.05 - 4) * 0.1 + 0.95;
    const lagoon = 1 - tr.smooth(60, 110, @sqrt(x * x + z * z));
    const d = (e - 1) * 60;
    const shallow = [3]f32{ 110, 222, 206 };
    const mid = [3]f32{ 40, 176, 182 };
    const deep = [3]f32{ 24, 100, 128 };
    const c = if (d < 10) mix3(shallow, mid, tr.smooth(0, 10, d)) else mix3(mid, deep, tr.smooth(10, 50, d) * (1 - lagoon * 0.6));

    return shade(c, wave);
}

fn groundColor(x: f32, z: f32) api.Rgb {
    const h = tr.height(x, z);

    if (h < sea_y + 0.05) return waterColor(x, z);

    const light = api.light(x, z);
    const n = tr.normal(x, z);
    const fleck = tr.fbm(x * 0.3 - 7, z * 0.3 + 5);
    const ao = contact(x, z);
    const sand = mix3(.{ 238, 218, 168 }, .{ 224, 200, 150 }, fleck);

    if (h < sea_y + 1.0) return shade(mix3(.{ 200, 176, 130 }, sand, tr.smooth(sea_y + 0.05, sea_y + 0.7, h)), light * ao);

    if (h < sea_y + 1.6) return shade(sand, light * ao);

    if (1 - n.y > 0.4) return shade(mix3(.{ 150, 144, 132 }, .{ 120, 116, 108 }, fleck), light * ao);

    const fd = dist(x, z, fort);

    if (fd < 26) {
        const jx = @mod(x + 0.3 * @floor(z / 1.4), 1.8);
        const jz = @mod(z, 1.4);
        const flag = fd < 12.6 and (jx < 0.12 or jz < 0.12);
        const earth = mix3(.{ 176, 150, 112 }, .{ 158, 132, 96 }, fleck);
        const stone = mix3(.{ 168, 160, 146 }, .{ 150, 142, 130 }, tr.fbm(x * 0.7, z * 0.7));
        const inner = if (flag) mix3(stone, .{ 110, 104, 96 }, 0.6) else stone;
        const outer = mix3(earth, .{ 120, 158, 74 }, tr.smooth(16, 26, fd) * (0.4 + 0.6 * tr.smooth(0.4, 0.6, tr.fbm(x * 0.09, z * 0.09))));

        return shade(if (fd < 12.6) mix3(inner, earth, 0.25) else outer, light * ao);
    }

    const tm = townMask(x, z);

    if (tm > 0.3 and z > -142) {
        const path = @abs(z + 97) < 5 or @abs(@mod(x + 200, 40) - 20) < 3;
        const dirt = mix3(.{ 196, 170, 126 }, .{ 172, 146, 104 }, fleck);

        if (path) return shade(dirt, light * ao);

        const grassy = tr.smooth(0.5, 0.66, tr.fbm(x * 0.07 + 4, z * 0.07));

        return shade(mix3(mix3(dirt, .{ 186, 168, 120 }, 0.4), .{ 120, 158, 74 }, grassy * tm), light * ao);
    }

    const jungle = tr.smooth(0.45, 0.6, tr.fbm(x * 0.04 + 9, z * 0.04 - 2));
    const grass = mix3(.{ 112, 168, 70 }, .{ 84, 140, 56 }, jungle);
    const patch = mix3(grass, .{ 150, 168, 88 }, std.math.clamp((fleck - 0.6) * 3, 0, 0.6));
    const edge = tr.smooth(sea_y + 1.6, sea_y + 2.6, h);

    return shade(mix3(sand, patch, edge), light * ao);
}

const max_shadow = 600;
var shadows: [max_shadow][4]f32 = undefined;
var shadow_n: usize = 0;

fn addShadow(x0: f32, z0: f32, x1: f32, z1: f32) void {
    if (shadow_n >= max_shadow) return;

    shadows[shadow_n] = .{ x0, z0, x1, z1 };
    shadow_n += 1;
}

fn contact(x: f32, z: f32) f32 {
    var best: f32 = 10;

    for (shadows[0..shadow_n]) |r| {
        const dx = @max(r[0] - x, x - r[2], 0);
        const dz = @max(r[1] - z, z - r[3], 0);

        best = @min(best, @sqrt(dx * dx + dz * dz));
    }

    return 0.72 + 0.28 * tr.smooth(0, 2.2, best);
}

var occ: [420 * 420]u8 = undefined;

fn occIndex(x: f32, z: f32) ?usize {
    const ix: i32 = @intFromFloat(@floor(x + 210));
    const iz: i32 = @intFromFloat(@floor(z + 210));

    if (ix < 0 or iz < 0 or ix >= 420 or iz >= 420) return null;

    return @intCast(iz * 420 + ix);
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

fn bld(e: K) api.Building {
    for (k.buildings) |b| {
        if (b.kind == kit.of(e)) return b;
    }

    unreachable;
}

fn rnd(b: *Builder) f32 {
    return b.rng.next();
}

fn spin(b: *Builder) f32 {
    return b.rng.range(0, std.math.tau);
}

fn box(b: *Builder, x0: f32, ya: f32, z0: f32, x1: f32, yb: f32, z1: f32) void {
    b.solid(.{ .box = .{ .min = vec(x0, ya, z0), .max = vec(x1, yb, z1) } });
}

fn lbox(b: *Builder, cx: f32, cz: f32, yaw: f32, y: f32, l: [6]f32) void {
    const r = wd.rotBox(cx, cz, yaw, l[0], l[1], l[2], l[3]);

    box(b, r[0], y + l[4], r[1], r[2], y + l[5], r[3]);
}

var spawn_list: std.ArrayList(Vec3) = .empty;
var spawn_yaw: std.ArrayList(f32) = .empty;
var anchor_list: std.ArrayList(Vec3) = .empty;
var loot_list: std.ArrayList(Vec3) = .empty;

fn spawnAt(b: *Builder, x: f32, z: f32, yaw: f32) void {
    spawn_list.append(b.gpa, vec(x, tr.height(x, z) + 0.1, z)) catch {};
    spawn_yaw.append(b.gpa, yaw) catch {};
}

fn spawnY(b: *Builder, x: f32, y: f32, z: f32, yaw: f32) void {
    spawn_list.append(b.gpa, vec(x, y + 0.1, z)) catch {};
    spawn_yaw.append(b.gpa, yaw) catch {};
}

fn loot(b: *Builder, x: f32, z: f32) void {
    loot_list.append(b.gpa, vec(x, tr.height(x, z) + 0.1, z)) catch {};
}

fn lootY(b: *Builder, x: f32, y: f32, z: f32) void {
    loot_list.append(b.gpa, vec(x, y + 0.1, z)) catch {};
}

fn house(b: *Builder, e: K, x: f32, z: f32, yaw: f32) void {
    const bl = bld(e);
    const r = wd.rotBox(x, z, yaw, -bl.w / 2, -bl.d / 2, bl.w / 2, bl.d / 2);

    _ = api.building(b, bl, x, z, yaw);
    addShadow(r[0], r[1], r[2], r[3]);
    claimRect(r[0] - 1, r[1] - 1, r[2] + 1, r[3] + 1);
}

fn put(b: *Builder, e: K, x: f32, z: f32, yaw: f32) void {
    b.put(of(e), x, z, yaw, 1);
}

fn putS(b: *Builder, e: K, x: f32, z: f32, yaw: f32, s: f32) void {
    b.put(of(e), x, z, yaw, s);
}

fn putAt(b: *Builder, e: K, x: f32, y: f32, z: f32, yaw: f32) void {
    b.putAt(of(e), vec(x, y, z), yaw, 1);
}

fn pierRun(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32) void {
    const along_z = @abs(z1 - z0) > @abs(x1 - x0);
    const len = if (along_z) @abs(z1 - z0) else @abs(x1 - x0);
    const n: u32 = @intFromFloat(@floor(len / 3));
    const sx = std.math.sign(x1 - x0);
    const sz = std.math.sign(z1 - z0);
    const yaw: f32 = if (along_z) 0 else half_pi;
    var i: u32 = 0;

    while (i < n) : (i += 1) {
        const t = (@as(f32, @floatFromInt(i)) + 0.5) * 3;
        const x = if (along_z) x0 else x0 + sx * t;
        const z = if (along_z) z0 + sz * t else z0;

        putAt(b, .pier, x, dock_top - 1.2, z, yaw);

        if (i % 4 == 1) putAt(b, .mooring, x + (if (along_z) @as(f32, 2.3) else 0), sea_y - 0.2, z + (if (along_z) @as(f32, 0) else 2.3), 0);

        if (i % 5 == 3) putAt(b, .lantern, x - (if (along_z) @as(f32, 1.7) else 0), dock_top, z - (if (along_z) @as(f32, 0) else 1.7), if (along_z) half_pi else 0);

        if (i % 3 == 1) {
            const side: f32 = if (i % 2 == 0) 1.2 else -1.2;
            const cx = x + (if (along_z) side else 0);
            const cz = z + (if (along_z) 0 else side);
            const pick = (i * 7 + @as(u32, @intFromFloat(@abs(x0)))) % 5;

            switch (pick) {
                0 => {
                    putAt(b, .freight, cx, dock_top, cz, yaw);
                },
                1 => {
                    putAt(b, .barrel, cx, dock_top, cz, 0);
                    putAt(b, .barrel, cx + 0.5, dock_top, cz + 0.5, 1);
                },
                2 => {
                    putAt(b, .rope, cx, dock_top, cz, 0);
                    putAt(b, .sack, cx + 0.6, dock_top, cz - 0.4, 0.4);
                },
                3 => {
                    putAt(b, .crate, cx, dock_top, cz, 0.2);
                    putAt(b, .wcrate, cx, dock_top + 0.96, cz, 0.5);
                },
                else => putAt(b, .netrack, cx, dock_top, cz, yaw),
            }
        }
    }

    const end_x = if (along_z) x0 else x0 + sx * @as(f32, @floatFromInt(n)) * 3;
    const end_z = if (along_z) z0 + sz * @as(f32, @floatFromInt(n)) * 3 else z0;

    box(b, @min(x0, end_x) - (if (along_z) @as(f32, 2) else 0), dock_top - 1, @min(z0, end_z) - (if (along_z) @as(f32, 0) else 2), @max(x0, end_x) + (if (along_z) @as(f32, 2) else 0), dock_top, @max(z0, end_z) + (if (along_z) @as(f32, 0) else 2));
    claimRect(@min(x0, end_x) - 3, @min(z0, end_z) - 3, @max(x0, end_x) + 3, @max(z0, end_z) + 3);
}

fn galleon(b: *Builder, x: f32, z: f32, yaw: f32) void {
    const y = sea_y - 2.6;

    putAt(b, .galleon, x, y, z, yaw);
    lbox(b, x, z, yaw, y, .{ -3.1, -2, 3.1, 12.6, 0, 4.2 });
    lbox(b, x, z, yaw, y, .{ -3.3, -13, 3.3, -3.2, 0, 6.4 });
    b.solid(.{ .ramp = .{ .min = vec(x - 0.9, y + 4.2, z - 3.3), .max = vec(x + 0.9, y + 6.4, z - 1.9), .rise = .neg_z } });

    for ([_]f32{ 4, -2, 9 }) |mz| {
        const m = wd.rotPoint(x, z, yaw, 0, mz);

        b.solid(.{ .cylinder = .{ .base = vec(m[0], y + 4, m[1]), .radius = 0.45, .height = 12 } });
    }

    lootY(b, x, y + 4.3, z + 6);
    lootY(b, x, y + 6.5, z - 9);
    spawnY(b, x, y + 6.5, z - 7, 0);
    anchor_list.append(b.gpa, vec(x, y + 20, z)) catch {};
    addShadow(x - 4, z - 14, x + 4, z + 14);
}

fn brig(b: *Builder, x: f32, z: f32) void {
    const y = sea_y - 2.2;

    putAt(b, .brig, x, y, z, half_pi);
    box(b, x - 2.1, y, z - 1, x + 2.1, y + 3.3, z + 7.4);
    box(b, x - 2.2, y, z - 8, x + 2.2, y + 4.35, z - 1);

    for ([_]f32{ 3.5, -3.5 }) |mz| b.solid(.{ .cylinder = .{ .base = vec(x, y + 3.3, z + mz), .radius = 0.35, .height = 10 } });

    lootY(b, x, y + 3.4, z + 4);
}

fn sloop(b: *Builder, e: K, x: f32, z: f32, yaw: f32) void {
    const y = sea_y - 0.9;

    putAt(b, e, x, y, z, yaw);
    lbox(b, x, z, yaw, y, .{ -1.4, -4.6, 1.4, 4.6, 0, 1.6 });

    if (e == .sloop) lbox(b, x, z, yaw, y, .{ -1.3, -4.4, 1.3, -1.6, 0, 2.75 });
}

fn docks(b: *Builder) void {
    const shore: f32 = -66;

    pierRun(b, -52, shore - 2, -52, -24);
    pierRun(b, 0, shore - 2, 0, -18);
    pierRun(b, 52, shore - 2, 52, -28);
    pierRun(b, -52, -36, -28, -36);
    pierRun(b, 0, -30, 20, -30);
    pierRun(b, -88, shore + 2, -88, -30);
    pierRun(b, -88, -30, -104, -30);

    galleon(b, 9.2, -42, 0);
    brig(b, -45.5, -34);
    sloop(b, .sloop, 58.6, -44, 0);
    sloop(b, .hull, 46, -40, 0.05);
    sloop(b, .sloop, -95.6, -42, pi);

    putAt(b, .gangplank, 4.6, dock_top - 0.2, -36, -half_pi);
    b.solid(.{ .ramp = .{ .min = vec(2, dock_top, -36.5), .max = vec(6.2, dock_top + 0.4, -35.5), .rise = .pos_x } });
    putAt(b, .gangplank, -48.4, dock_top - 0.2, -30, half_pi);

    putAt(b, .crane, -2.6, dock_top, -50, half_pi);
    b.solid(.{ .cylinder = .{ .base = vec(-2.6, dock_top, -50), .radius = 0.8, .height = 6.5 } });
    putAt(b, .crane, 54.5, dock_top, -38, -half_pi);
    b.solid(.{ .cylinder = .{ .base = vec(54.5, dock_top, -38), .radius = 0.8, .height = 6.5 } });

    for ([_][4]f32{ .{ -1.2, -56, 0, 0 }, .{ 1.2, -57, 1, 0.4 }, .{ -1.3, -40, 0, 0.2 }, .{ 1.3, -26, 1, 0 }, .{ -50.8, -50, 0, 0.1 }, .{ -53.2, -44, 1, 0.3 }, .{ 50.8, -52, 0, 0 }, .{ 53.2, -60, 1, 0.5 }, .{ -40, -36, 0, 0.2 }, .{ 14, -30, 1, 0 } }) |c| {
        if (c[2] < 0.5) {
            putAt(b, .barrel, c[0], dock_top, c[1], c[3]);
            putAt(b, .barrel, c[0] + 0.1, dock_top, c[1] + 0.75, c[3] + 1);
            putAt(b, .crate, c[0], dock_top, c[1] - 1.1, c[3]);
        } else {
            putAt(b, .crate, c[0], dock_top, c[1], c[3]);
            putAt(b, .wcrate, c[0], dock_top + 0.96, c[1], c[3] + 0.3);
            putAt(b, .sack, c[0] + 0.1, dock_top, c[1] + 0.9, 0);
            putAt(b, .rope, c[0] - 0.2, dock_top, c[1] - 1.2, 0);
        }
    }

    putAt(b, .capstan, 0, dock_top, -22, 0);
    putAt(b, .anchor, 52, dock_top, -30, half_pi);
    putAt(b, .wheel, -88, dock_top, -32, 0);

    lootY(b, 0, dock_top, -26);
    lootY(b, -52, dock_top, -28);
    lootY(b, 52, dock_top, -32);
    lootY(b, -100, dock_top, -30);
    spawnY(b, 52, dock_top, -30, pi);
    spawnY(b, -88, dock_top, -34, pi);
    anchor_list.append(b.gpa, vec(0, 18, -40)) catch {};
}

fn town(b: *Builder) void {
    const north = [_]K{ .warehouse, .shack, .boatshed, .shack, .warehouse, .shack, .boatshed, .warehouse, .shack, .tavern, .shack, .warehouse, .boatshed, .shack, .warehouse, .shack, .boatshed };
    const south = [_]K{ .shack, .tavern, .shack, .warehouse, .shack, .shack, .tavern, .shack, .warehouse, .shack, .tavern, .shack, .shack, .warehouse, .shack, .tavern, .shack };

    for (north, 0..) |e, i| {
        const x = -84 + @as(f32, @floatFromInt(i)) * 10.5;

        if (@abs(x) < 4) continue;

        house(b, e, x, -84 + b.rng.range(-1, 1), pi);
    }

    for (south, 0..) |e, i| {
        const x = -84 + @as(f32, @floatFromInt(i)) * 10.5;

        if (@abs(x - 21) < 4) continue;

        house(b, e, x, -110 + b.rng.range(-1, 1), 0);
    }

    for ([_]f32{ -70, -36, 36, 72 }) |x| {
        house(b, .shack, x, -124, 0);
        house(b, .shack, x + 10, -128, half_pi);
    }

    for ([_][2]f32{ .{ -72, -60 }, .{ -30, -58 }, .{ 28, -58 }, .{ 76, -60 } }) |p| {
        var dx: f32 = -4.5;

        while (dx <= 4.5) : (dx += 3) {
            var dz: f32 = -4;

            while (dz <= 4) : (dz += 4) putAt(b, .pier, p[0] + dx, dock_top - 1.2, p[1] + dz, half_pi);
        }

        box(b, p[0] - 6, dock_top - 1, p[1] - 6, p[0] + 6, dock_top, p[1] + 6);
        putAt(b, .shack, p[0], dock_top, p[1] + 1, pi);
        box(b, p[0] - 2.4, dock_top, p[1] - 1.2, p[0] + 2.4, dock_top + 5.4, p[1] + 3.2);
        putAt(b, .netrack, p[0] + 3.6, dock_top, p[1] - 4, 0);
        putAt(b, .barrel, p[0] - 4, dock_top, p[1] - 4, 0);
        putAt(b, .rope, p[0] - 3, dock_top, p[1] - 4.6, 0);
        claimRect(p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6);
    }

    for ([_][3]f32{ .{ -12, -92, 0 }, .{ 12, -92, 0 }, .{ -52, -101, 0 }, .{ 52, -101, 0 }, .{ -88, -92, 0 }, .{ 88, -101, 0 }, .{ -30, -101, 0 }, .{ 30, -92, 0 } }) |p| {
        put(b, .torch, p[0], p[1], 0);
        put(b, .signboard, p[0] + 3, p[1] + 3, half_pi);
    }

    var x: f32 = -90;

    while (x < 92) : (x += 3.2) {
        const zs = [_]f32{ -91, -102, -118, -78 };

        for (zs) |z| {
            if (rnd(b) < 0.3 or taken(x, z, 0.5)) continue;

            const roll = rnd(b);

            if (roll < 0.25) {
                put(b, .barrel, x, z, spin(b));
                put(b, .barrel, x + 0.7, z + 0.3, spin(b));
            } else if (roll < 0.45) {
                put(b, .crate, x, z, spin(b));
                put(b, .sack, x + 0.8, z, 0);
            } else if (roll < 0.55) {
                put(b, .cannon, x, z, spin(b));
            } else if (roll < 0.65) {
                put(b, .netrack, x, z, 0);
            } else if (roll < 0.75) {
                put(b, .palm, x, z, spin(b));
            } else if (roll < 0.85) {
                put(b, .stump, x, z, spin(b));
                put(b, .rope, x + 1, z, 0);
            } else {
                put(b, .chest, x, z, spin(b));
            }
        }
    }

    var px: f32 = -96;

    while (px < 96) : (px += 2.4) {
        if (@abs(px) < 6 or @abs(px - 60) < 4 or @abs(px + 60) < 4) continue;

        const z: f32 = -140;
        const y = tr.height(px, z);

        putAt(b, .palisade, px, y - 0.1, z, 0);
        box(b, px - 1.2, y - 0.5, z - 0.15, px + 1.2, y + 1.4, z + 0.15);
    }

    house(b, .shack, -96, -136, half_pi);
    putAt(b, .tower, 0, tr.height(0, -146), -146, 0);

    for ([_][2]f32{ .{ -1.2, -1.3 }, .{ 1.2, -1.3 }, .{ -1.2, 1.3 }, .{ 1.2, 1.3 } }) |o| box(b, o[0] - 0.15, tr.height(0, -146), -146 + o[1] - 0.15, o[0] + 0.15, tr.height(0, -146) + 9, -146 + o[1] + 0.15);

    putAt(b, .campfire, 30, tr.height(30, -130), -130, 0);

    for ([_][3]f32{ .{ 28, -128, 0.4 }, .{ 32.4, -131, 1.6 }, .{ 27.6, -132, 2.8 } }) |s| put(b, .stump, s[0], s[1], s[2]);

    claimRect(-100, -150, 100, -70);
    loot(b, 0, -100);
    loot(b, -40, -100);
    loot(b, 40, -100);
    loot(b, 30, -126);
    loot(b, -70, -128);
    spawnAt(b, 0, -104, 0);
    spawnAt(b, -70, -104, 0.4);
    spawnAt(b, 70, -104, -0.4);
    spawnAt(b, -30, -150, 0);
    spawnAt(b, 40, -150, 0);
    anchor_list.append(b.gpa, vec(-40, 20, -100)) catch {};
    anchor_list.append(b.gpa, vec(40, 20, -100)) catch {};
}

fn fortress(b: *Builder) void {
    const fx = fort[0];
    const fz = fort[1];
    const y = tr.height(fx, fz);
    const r: f32 = 14;
    const gate: f32 = 4.4;
    var a: f32 = 0;

    while (a < std.math.tau - 0.01) : (a += std.math.tau / 22.0) {
        if (@abs(a - gate) < 0.2) continue;

        const wx = fx + @cos(a) * r;
        const wz = fz + @sin(a) * r;
        const yaw = std.math.atan2(-@cos(a), -@sin(a));
        const wy = tr.height(wx, wz) - 0.2;

        putAt(b, .battery, wx, wy, wz, yaw);
        lbox(b, wx, wz, yaw, wy, .{ -2, -0.6, 2, 0.6, -0.5, 2.4 });
    }

    const deck_r: f32 = 11.6;
    const deck_h: f32 = 1.6;
    const steps: f32 = 24;
    var i: f32 = 0;

    while (i < steps) : (i += 1) {
        const da = i / steps * std.math.tau;

        if (@abs(da - gate) < 0.42 or @abs(da) < 0.14 or @abs(da - pi) < 0.14) continue;

        const dx = fx + @cos(da) * deck_r;
        const dz = fz + @sin(da) * deck_r;
        const dy = tr.height(dx, dz);
        const yaw = std.math.atan2(-@cos(da), -@sin(da));

        putAt(b, .pier, dx, dy + deck_h - 1.56, dz, yaw);
        box(b, dx - 1.2, dy - 0.5, dz - 1.2, dx + 1.2, dy + deck_h, dz + 1.2);

        if (@mod(i, 2) == 0) {
            const cx = fx + @cos(da) * (deck_r + 0.6);
            const cz = fz + @sin(da) * (deck_r + 0.6);

            b.putAt(of(.cannon), vec(cx, dy + deck_h, cz), std.math.atan2(@cos(da), @sin(da)), 1.3);
            putAt(b, .balls, cx - @cos(da) * 1.4, dy + deck_h, cz - @sin(da) * 1.4, 0);
        } else {
            putAt(b, .barrel, dx - @cos(da) * 0.8, dy + deck_h, dz - @sin(da) * 0.8, i);
        }
    }

    for ([_]f32{ 0, pi }) |ra| {
        const sx = @cos(ra);
        const x0 = fx + sx * (deck_r - 3.6);
        const x1 = fx + sx * (deck_r - 1.2);
        const ry = tr.height(fx + sx * deck_r, fz);

        putAt(b, .gangplank, (x0 + x1) / 2, ry, fz, if (sx > 0) -half_pi else half_pi);
        b.solid(.{ .ramp = .{ .min = vec(@min(x0, x1), ry - 0.2, fz - 0.7), .max = vec(@max(x0, x1), ry + deck_h, fz + 0.7), .rise = if (sx > 0) .pos_x else .neg_x } });
        box(b, fx + sx * deck_r - 1.2, ry - 0.5, fz - 1.2, fx + sx * deck_r + 1.2, ry + deck_h, fz + 1.2);
        putAt(b, .pier, fx + sx * deck_r, ry + deck_h - 1.56, fz, half_pi);
    }

    putAt(b, .tower, fx, y, fz, 0);

    for ([_][2]f32{ .{ -1.2, -1.3 }, .{ 1.2, -1.3 }, .{ -1.2, 1.3 }, .{ 1.2, 1.3 } }) |o| box(b, fx + o[0] - 0.15, y, fz + o[1] - 0.15, fx + o[0] + 0.15, y + 9, fz + o[1] + 0.15);

    putAt(b, .flag, fx + 2.2, y, fz + 1.6, 0.4);
    putAt(b, .bigtent, fx - 4.6, tr.height(fx - 4.6, fz + 4.4), fz + 4.4, 0.8);
    box(b, fx - 7, y - 0.5, fz + 2, fx - 2.2, y + 3.4, fz + 6.8);
    putAt(b, .walltent, fx + 5, tr.height(fx + 5, fz + 4.6), fz + 4.6, -0.7);
    box(b, fx + 2.8, y - 0.5, fz + 2.4, fx + 7.2, y + 4.4, fz + 6.8);
    putAt(b, .tarp, fx + 5, tr.height(fx + 5, fz - 4), fz - 4, 0.3);

    for ([_][3]f32{ .{ 4.2, -3.4, 0 }, .{ 5.4, -3.6, 0.3 }, .{ 4.6, -4.8, 1.2 }, .{ 6.2, -4.6, 0.1 } }) |c| put(b, .freight, fx + c[0], fz + c[1], c[2]);

    putAt(b, .crate, fx + 5, tr.height(fx + 5, fz - 4) + 0.9, fz - 4.1, 0.2);
    put(b, .barrel, fx + 3.4, fz - 5.4, 0);
    put(b, .barrel, fx + 4.1, fz - 5.8, 1);
    put(b, .barrel, fx + 6.8, fz - 2.8, 2);
    putAt(b, .campfire, fx - 4.4, y, fz - 3.6, 0);

    for ([_][3]f32{ .{ -6.6, -3, 0.3 }, .{ -4.2, -6, 1.4 }, .{ -2.4, -3.2, 2.6 } }) |s| put(b, .stump, fx + s[0], fz + s[1], s[2]);

    put(b, .chest, fx - 7.4, fz - 0.4, 1.2);
    put(b, .rope, fx - 6.8, fz + 1.4, 0);
    put(b, .wcrate, fx - 2.6, fz + 7.6, 0.2);
    put(b, .wcrate, fx - 1.6, fz + 8, 0.9);
    put(b, .sack, fx + 0.6, fz + 7.8, 0);
    put(b, .balls, fx + 1.4, fz - 7, 0);
    put(b, .balls, fx + 1.8, fz - 6.6, 0);
    put(b, .swivel, fx - 0.8, fz - 7.4, 0);

    for ([_]f32{ -1, 1 }) |sd| {
        const ga = gate + sd * 0.32;
        const gx = fx + @cos(ga) * (r + 1.8);
        const gz = fz + @sin(ga) * (r + 1.8);

        putAt(b, .flag, gx, tr.height(gx, gz), gz, 0);
        putAt(b, .torch, fx + @cos(ga) * (r + 0.4), tr.height(gx, gz), fz + @sin(ga) * (r + 0.4), 0);
    }

    const pr: f32 = 24;
    var pa: f32 = 0;

    while (pa < std.math.tau) : (pa += 2.4 / pr) {
        if (@abs(pa - gate) < 0.22) continue;

        const px = fx + @cos(pa) * pr;
        const pz = fz + @sin(pa) * pr;
        const py = tr.height(px, pz);

        if (py < sea_y + 1.5) continue;

        putAt(b, .palisade, px, py - 0.1, pz, std.math.atan2(-@sin(pa), @cos(pa)) + half_pi);
        box(b, px - 0.9, py - 0.5, pz - 0.9, px + 0.9, py + 1.4, pz + 0.9);
    }

    for ([_]f32{ 0.9, 2.3, 5.6 }) |ta| {
        const tx = fx + @cos(ta) * 20;
        const tz = fz + @sin(ta) * 20;
        const ty = tr.height(tx, tz);

        putAt(b, .tower, tx, ty, tz, ta);

        for ([_][2]f32{ .{ -1.2, -1.3 }, .{ 1.2, -1.3 }, .{ -1.2, 1.3 }, .{ 1.2, 1.3 } }) |o| {
            const q = wd.rotPoint(tx, tz, ta, o[0], o[1]);

            box(b, q[0] - 0.15, ty, q[1] - 0.15, q[0] + 0.15, ty + 9, q[1] + 0.15);
        }

        put(b, .barrel, tx + 2.4, tz + 1, 0);
        put(b, .crate, tx - 2.2, tz + 1.4, 0.4);
    }

    for ([_][3]f32{ .{ -20, -6, 0.2 }, .{ -16, -14, 1.1 }, .{ 18, -12, 2.0 }, .{ -4, 19, 0.6 }, .{ 10, 18, 2.6 }, .{ 19, 4, 1.4 } }) |c| {
        const cx = fx + c[0];
        const cz = fz + c[1];

        if (tr.height(cx, cz) < sea_y + 1.5) continue;

        put(b, .freight, cx, cz, c[2]);
        put(b, .barrel, cx + 1.2, cz + 0.4, 0);
        put(b, .barrel, cx + 1.4, cz - 0.6, 1);
        put(b, .tent, cx - 3, cz + 2, c[2] + 0.4);
        box(b, cx - 4.6, tr.height(cx, cz) - 0.5, cz, cx - 1.4, tr.height(cx, cz) + 2, cz + 4);
    }

    for ([_][4]f32{ .{ -14, -16, 0.3, 0 }, .{ -10, -20, 1.2, 1 }, .{ 4, -18, 2.8, 2 }, .{ 9, -16, 0.4, 3 }, .{ 13, -12, 1.9, 0 }, .{ -17, -9, 2.2, 1 }, .{ 0, -21, 0.9, 3 } }) |c| {
        const cx = fx + c[0];
        const cz = fz + c[1];
        const cy = tr.height(cx, cz);

        if (cy < sea_y + 1.5) continue;

        switch (@as(u32, @intFromFloat(c[3]))) {
            0 => {
                putAt(b, .walltent, cx, cy, cz, c[2]);
                box(b, cx - 2.2, cy - 0.5, cz - 2.2, cx + 2.2, cy + 4.4, cz + 2.2);
                put(b, .barrel, cx + 3, cz + 1, 0);
                put(b, .crate, cx + 3, cz - 0.4, 0.3);
            },
            1 => {
                b.putAt(of(.cannon), vec(cx, cy, cz), c[2] + pi, 1.3);
                put(b, .balls, cx + 1.2, cz + 0.6, 0);
                put(b, .barrel, cx - 1.4, cz + 0.8, 0);
                put(b, .freight, cx + 1.5, cz - 1.6, c[2]);
            },
            2 => {
                putAt(b, .tarp, cx, cy, cz, c[2]);

                for ([_][2]f32{ .{ -0.8, 0 }, .{ 0.4, 0.5 }, .{ -0.2, -0.9 }, .{ 1, -0.6 } }) |o| put(b, .freight, cx + o[0], cz + o[1], c[2]);

                putAt(b, .crate, cx - 0.4, cy + 0.9, cz + 0.2, 0.4);
                put(b, .rope, cx + 1.8, cz + 1.4, 0);
            },
            else => {
                putAt(b, .campfire, cx, cy, cz, 0);

                for ([_][3]f32{ .{ -1.6, 0.2, 0 }, .{ 1.4, 0.8, 1 }, .{ 0.2, -1.6, 2 } }) |o| put(b, .stump, cx + o[0], cz + o[1], o[2]);

                put(b, .flag, cx + 3, cz + 2, 0);
            },
        }
    }

    claimRect(fx - 26, fz - 26, fx + 26, fz + 26);
    loot(b, fx + 3, fz);
    loot(b, fx - 4, fz - 2);
    lootY(b, fx, y + deck_h, fz + deck_r);
    loot(b, fx - 16, fz - 12);
    spawnAt(b, fx - 4, fz + 8, pi);
    spawnAt(b, fx - 30, fz - 16, 0.8);
    anchor_list.append(b.gpa, vec(fx, y + 22, fz)) catch {};
}

fn jungleCamp(b: *Builder) void {
    const cx = camp[0];
    const cz = camp[1];

    house(b, .cave, cx + 18, cz - 12, -half_pi + 0.3);
    putS(b, .karst, cx - 18, cz - 6, 0.4, 0.8);
    b.solid(.{ .cylinder = .{ .base = vec(cx - 18, tr.height(cx - 18, cz - 6) - 1, cz - 6), .radius = 8, .height = 30 } });
    claimRect(cx - 28, cz - 16, cx - 8, cz + 4);
    put(b, .campfire, cx, cz, 0);

    for ([_][3]f32{ .{ -2.4, 0, 0.3 }, .{ 2.4, 0.4, 1.7 }, .{ 0, 2.6, 2.9 } }) |s| put(b, .stump, cx + s[0], cz + s[1], s[2]);

    for ([_][3]f32{ .{ 6, 4, 0 }, .{ 8, -4, 1 }, .{ -6, 6, 0 } }) |c| {
        put(b, .chest, cx + c[0], cz + c[1], c[2]);
        put(b, .barrel, cx + c[0] + 1, cz + c[1], 0);
        put(b, .sack, cx + c[0] - 0.8, cz + c[1], 0);
    }

    for ([_][2]f32{ .{ -4, -4 }, .{ 4, -5 }, .{ -5, 3 }, .{ 5, 5 } }) |t| put(b, .torch, cx + t[0], cz + t[1], 0);

    putAt(b, .tower, cx - 6, tr.height(cx - 6, cz + 40), cz + 40, 0.3);

    for ([_][2]f32{ .{ -1.2, -1.3 }, .{ 1.2, -1.3 }, .{ -1.2, 1.3 }, .{ 1.2, 1.3 } }) |o| {
        const p = wd.rotPoint(cx - 6, cz + 40, 0.3, o[0], o[1]);

        box(b, p[0] - 0.15, tr.height(cx - 6, cz + 40), p[1] - 0.15, p[0] + 0.15, tr.height(cx - 6, cz + 40) + 9, p[1] + 0.15);
    }

    claimRect(cx - 10, cz - 8, cx + 10, cz + 8);
    loot(b, cx + 3, cz + 3);
    loot(b, cx + 14, cz - 10);
    loot(b, cx - 6, cz + 36);
    spawnAt(b, cx + 6, cz + 12, half_pi);
    spawnAt(b, cx - 10, cz - 40, 0.4);
    spawnAt(b, cx + 10, cz + 70, 2.6);
    anchor_list.append(b.gpa, vec(cx, 30, cz)) catch {};
}

fn sandbar(b: *Builder) void {
    const sx: f32 = 136;
    const sz: f32 = -24;

    putAt(b, .wreck, sx - 4, tr.height(sx - 4, sz + 2) - 0.6, sz + 2, 0.7);
    lbox(b, sx - 4, sz + 2, 0.7, tr.height(sx - 4, sz + 2) - 0.6, .{ -1.6, -4.4, 1.6, 4.4, 0, 2.2 });
    putAt(b, .hull, sx + 10, sea_y - 1.2, sz + 18, 2.4);
    lbox(b, sx + 10, sz + 18, 2.4, sea_y - 1.2, .{ -1.4, -4.6, 1.4, 4.6, 0, 1.6 });

    for ([_][3]f32{ .{ 6, -8, 0.4 }, .{ -8, 10, 1.9 }, .{ 2, 14, 2.7 }, .{ 12, 0, 0.9 } }) |d| put(b, .driftwood, sx + d[0], sz + d[1], d[2]);

    for ([_][2]f32{ .{ 4, 6 }, .{ -6, -12 }, .{ 8, -16 } }) |c| {
        put(b, .chest, sx + c[0], sz + c[1], spin(b));
        put(b, .barrel, sx + c[0] + 1, sz + c[1] + 0.4, spin(b));
    }

    put(b, .driftwood, sx - 12, sz - 6, 1.2);
    put(b, .anchor, sx + 2, sz - 2, 0.3);
    claimRect(sx - 14, sz - 18, sx + 14, sz + 22);
    loot(b, sx, sz);
    loot(b, sx + 6, sz - 14);
    spawnAt(b, sx - 2, sz - 20, -0.6);
}

fn stacks(b: *Builder) void {
    for ([_][4]f32{ .{ 168, 60, 1.0, 0.3 }, .{ 176, -90, 0.8, 1.2 }, .{ -40, 186, 0.9, 2.0 }, .{ -190, -110, 1.0, 0.7 }, .{ 150, 170, 0.7, 2.6 }, .{ -186, 160, 0.9, 1.5 }, .{ 100, 30, 0.45, 0.2 }, .{ 92, -40, 0.35, 1.1 } }) |s| {
        putAt(b, .karst, s[0], sea_y - 4, s[1], s[3]);
        _ = s[2];

        if (@abs(s[0]) < 168 and @abs(s[1]) < 168) b.solid(.{ .cylinder = .{ .base = vec(s[0], sea_y - 4, s[1]), .radius = 9, .height = 40 } });
    }

    for ([_][3]f32{ .{ 110, 50, 0.3 }, .{ 118, 40, 1.6 }, .{ 122, -70, 0.7 }, .{ -40, 60, 2.2 }, .{ 20, 70, 0.9 }, .{ -70, -40, 1.4 } }) |s| {
        putAt(b, .stack, s[0], sea_y - 1, s[1], s[2]);
        b.solid(.{ .cylinder = .{ .base = vec(s[0], sea_y - 1, s[1]), .radius = 1.8, .height = 11 } });
    }
}

fn islets(b: *Builder) void {
    for ([_][2]f32{ .{ -18, 26 }, .{ 56, 14 } }, 0..) |c, n| {
        for ([_][2]f32{ .{ -3, 0 }, .{ 3, 2 }, .{ 0, -4 }, .{ 5, -2 } }) |o| put(b, .palm, c[0] + o[0], c[1] + o[1], spin(b));

        put(b, .chest, c[0] + 1, c[1], 0.4);
        put(b, .barrel, c[0] - 1, c[1] + 1, 0);
        put(b, .fern, c[0] + 4, c[1] + 4, 0);
        put(b, if (n == 0) .campfire else .driftwood, c[0] - 2, c[1] - 2, 0);
        claimRect(c[0] - 8, c[1] - 6, c[0] + 8, c[1] + 6);
        loot(b, c[0], c[1] + 2);
    }
}

fn vegetation(b: *Builder) void {
    var z: f32 = -200;

    while (z < 200) : (z += 3.2) {
        var x: f32 = -200;

        while (x < 200) : (x += 3.2) {
            const px = x + b.rng.range(-1.4, 1.4);
            const pz = z + b.rng.range(-1.4, 1.4);
            const h = tr.height(px, pz);

            if (h < sea_y + 0.3 or taken(px, pz, 0.8)) continue;

            const n = tr.normal(px, pz);
            const roll = rnd(b);
            const yaw = spin(b);
            const jungle = tr.smooth(0.42, 0.58, tr.fbm(px * 0.04 + 9, pz * 0.04 - 2));
            const tm = townMask(px, pz);

            if (h < sea_y + 1.5) {
                if (roll < 0.05) put(b, .palm, px, pz, yaw) else if (roll < 0.14) put(b, .grass, px, pz, yaw) else if (roll < 0.16) put(b, .driftwood, px, pz, yaw) else if (roll < 0.18) put(b, .mrock, px, pz, yaw);

                continue;
            }

            if (1 - n.y > 0.42) {
                if (roll < 0.25) putS(b, .coastal, px, pz, yaw, b.rng.range(0.8, 1.8)) else if (roll < 0.35) put(b, .fern, px, pz, yaw) else if (roll < 0.4) putS(b, .spire, px, pz, yaw, b.rng.range(0.6, 1.0));

                continue;
            }

            if (tm > 0.5) {
                if (roll < 0.05) put(b, .palm, px, pz, yaw) else if (roll < 0.1) put(b, .fern, px, pz, yaw);

                continue;
            }

            const dense = 0.3 + jungle * 0.5;

            if (roll < dense * 0.32) {
                put(b, .palm, px, pz, yaw);
            } else if (roll < dense * 0.5) {
                put(b, if (rnd(b) < 0.5) .banana else .treefern, px, pz, yaw);
            } else if (roll < dense * 0.62) {
                put(b, .bamboo, px, pz, yaw);
            } else if (roll < dense) {
                put(b, .fern, px, pz, yaw);
            } else if (roll < dense + 0.06) {
                put(b, .sapling, px, pz, yaw);
            } else if (roll < dense + 0.09) {
                putS(b, .boulder, px, pz, yaw, b.rng.range(0.7, 1.4));
            } else if (roll < dense + 0.11) {
                put(b, .mrock, px, pz, yaw);
            } else if (roll < dense + 0.13) {
                put(b, .stump, px, pz, yaw);
            }
        }
    }
}

fn shoreFoam(b: *Builder) void {
    var z: f32 = -208;

    while (z < 208) : (z += 2.5) {
        var x: f32 = -208;

        while (x < 208) : (x += 2.5) {
            const e = coast(x, z);

            if (e < 1.0 or e > 1.04) continue;

            if (rnd(b) < 0.45) continue;

            const gx = coast(x + 1, z) - coast(x - 1, z);
            const gz = coast(x, z + 1) - coast(x, z - 1);
            const yaw = std.math.atan2(gx, gz);

            b.putAt(of(.foam), vec(x, sea_y + 0.01, z), yaw + b.rng.range(-0.1, 0.1), b.rng.range(0.6, 0.9));
        }
    }

    var n: u32 = 0;

    while (n < 160) : (n += 1) {
        const x = b.rng.range(-200, 200);
        const zz = b.rng.range(-200, 200);
        const e = coast(x, zz);

        if (e < 1.12 or e > 1.5) continue;

        b.putAt(of(.ripple), vec(x, sea_y + 0.005, zz), spin(b), b.rng.range(0.7, 1.2));
    }
}

fn build(b: *Builder) void {
    @memset(&occ, 0);
    shadow_n = 0;
    spawn_list = .empty;
    spawn_yaw = .empty;
    anchor_list = .empty;
    loot_list = .empty;

    docks(b);
    town(b);
    fortress(b);
    jungleCamp(b);
    sandbar(b);
    islets(b);
    stacks(b);
    vegetation(b);
    shoreFoam(b);
}

fn setSpots(gpa: std.mem.Allocator) void {
    wd.spawns = gpa.dupe(Vec3, spawn_list.items) catch &.{};
    wd.spawn_yaws = gpa.dupe(f32, spawn_yaw.items) catch &.{};
    wd.weapon_spots = gpa.dupe(Vec3, loot_list.items) catch &.{};
    wd.drone_anchors = gpa.dupe(Vec3, anchor_list.items) catch &.{};
    wd.vehicle_spots = &.{};
}
