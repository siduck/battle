const std = @import("std");
const api = @import("api.zig");
const k = @import("coast_kit.zig");

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
    .name = "Boardwalk",
    .note = "Seaside town, pier and harbour",
    .tint = .{ 226, 196, 140 },
    .half = 215,
    .play = 168,
    .facet = 2.0,
    .height = height,
    .ground = groundColor,
    .road = roadDist,
    .build = build,
    .spots = setSpots,
    .props = &k.table,
    .palette = .{
        .sun_dir = .{ -0.45, 0.66, -0.6 },
        .sun_tint = .{ 1.14, 1.04, 0.92 },
        .grade_tint = .{ 1.02, 1.01, 0.98 },
        .grade_sat = 1.12,
        .fog = 0.0024,
        .fog_color = .{ 0.74, 0.84, 0.92 },
        .amb_sky = .{ 0.92, 1, 1.16 },
        .amb_ground = .{ 0.86, 0.8, 0.66 },
        .shade_tint = .{ 0.88, 0.93, 1.06 },
        .zenith = .{ 0.12, 0.36, 0.7 },
    },
    .backdrop = .{ 44, 112, 140 },
    .floor_y = 0.12,
    .grip = 0.84,
    .tufts = 0.35,
};

const sea_y: f32 = 0.35;
const prom_y: f32 = 3.2;
const wall_z: f32 = -20;
const road_z0: f32 = -6;
const road_z1: f32 = 4;
const pier_x: f32 = 0;
const pier_end: f32 = -150;
const harbour_x: f32 = 100;

fn shoreZ(x: f32) f32 {
    return -56 + 5 * @sin(x * 0.021 + 0.7) + 3 * @sin(x * 0.053);
}

fn harbourWater(x: f32, z: f32) bool {
    return x > harbour_x + 8 and z < -26 and z > -110;
}

fn seaDist(x: f32, z: f32) f32 {
    if (harbourWater(x, z)) return @min(@min(x - harbour_x - 8, z - -110 + 40), -26 - z);

    return shoreZ(x) - z;
}

fn townLift(x: f32, z: f32) f32 {
    const street = @min(@max(0, z - 8), 52) * 0.035;
    const hill = tr.smooth(58, 140, z) * 34 * (0.8 + 0.4 * tr.fbm(x * 0.012 + 3, 7));
    const west = (1 - tr.smooth(-200, -110, x)) * tr.smooth(-10, 60, z) * 9;
    const roll = (tr.fbm(x * 0.03 + 3, z * 0.03 - 5) - 0.5) * 2.4 * tr.smooth(62, 90, z);

    return street + @max(hill, west) + roll;
}

fn dunes(x: f32, z: f32) f32 {
    const m = 1 - tr.smooth(-120, -96, x);
    const wave = @sin(x * 0.11 + z * 0.07) * 0.6 + tr.fbm(x * 0.05, z * 0.05) * 3;

    return m * wave * tr.smooth(-58, -36, z);
}

fn beachY(x: f32, z: f32) f32 {
    const s = shoreZ(x);
    const t = std.math.clamp((z - s) / (wall_z - 1 - s), 0, 1);

    return sea_y + t * 1.15 + dunes(x, z);
}

fn height(x: f32, z: f32) f32 {
    if (harbourWater(x, z)) return sea_y - 0.02;

    if (x > harbour_x - 2 and z < wall_z and z > -112) return prom_y;

    const s = shoreZ(x);

    if (z < s) return sea_y - 0.02;

    if (z < wall_z - 1) return beachY(x, z);

    if (z < wall_z) return std.math.lerp(beachY(x, wall_z - 1), prom_y, z - (wall_z - 1));

    return prom_y + townLift(x, z);
}

fn roadDist(x: f32, z: f32) f32 {
    var best = @max(@abs(z - (road_z0 + road_z1) / 2) - 5, 0);

    if (x > -170 and x < 170) best = @min(best, @max(@abs(z - high_z) - 4, 0));

    for (streets_x) |sx| {
        if (z > road_z1 and z < 72) best = @min(best, @max(@abs(x - sx) - 4, 0));
    }

    return best;
}

const streets_x = [_]f32{ -100, -44, 44, 100 };
const high_z: f32 = 42;

fn onStreet(x: f32, z: f32) bool {
    return roadDist(x, z) <= 0;
}

fn waterColor(d: f32, x: f32, z: f32) api.Rgb {
    const wave = tr.fbm(x * 0.05 + 3, z * 0.05 - 4) * 0.1 + 0.95;
    const shallow = [3]f32{ 126, 206, 196 };
    const mid = [3]f32{ 52, 160, 172 };
    const deep = [3]f32{ 44, 112, 140 };
    const c = if (d < 12) mix3(shallow, mid, tr.smooth(0, 12, d)) else mix3(mid, deep, tr.smooth(12, 60, d));

    return shade(c, wave);
}

fn groundColor(x: f32, z: f32) api.Rgb {
    const light = api.light(x, z);
    const fleck = tr.fbm(x * 0.35 - 7, z * 0.35 + 5);

    if (harbourWater(x, z)) return waterColor(@min(x - harbour_x - 8, -26 - z) * 0.6, x, z);

    const s = shoreZ(x);

    if (z < s and !(x > harbour_x - 2 and z > -112)) return waterColor(s - z, x, z);

    const ao = contact(x, z);

    if (x > harbour_x - 2 and z < wall_z) return shade(mix3(.{ 178, 172, 160 }, .{ 158, 152, 142 }, fleck), light * ao);

    if (z < wall_z) {
        const wet = 1 - tr.smooth(s, s + 7, z);
        const dry = mix3(.{ 232, 212, 168 }, .{ 220, 198, 152 }, fleck);
        const sand = mix3(dry, .{ 184, 160, 120 }, wet * 0.8);
        const tide = if (z - s > 7 and z - s < 8.2) @as(f32, 0.93) else 1;

        return shade(sand, light * tide * ao);
    }

    if (z < road_z0) {
        const cell = @mod(@floor(x / 2) + @floor(z / 2), 2);
        const band = @mod(@floor(x / 8), 2);
        const base: [3]f32 = if (band < 1) .{ 214, 204, 186 } else .{ 200, 178, 160 };

        return shade(if (cell < 1) base else mix3(base, .{ 170, 160, 148 }, 0.25), light * ao);
    }

    if (@abs(x) < 38 and z > 26 and z < 58) {
        const cell = @mod(@floor(x / 2) + @floor(z / 2), 2);

        return shade(if (cell < 1) .{ 198, 186, 166 } else .{ 186, 174, 154 }, light * ao);
    }

    if (onStreet(x, z)) {
        const patch = tr.fbm(x * 0.08, z * 0.08);

        return shade(mix3(.{ 84, 86, 90 }, .{ 100, 100, 104 }, patch), light * ao);
    }

    if (roadDist(x, z) < 2.6) {
        const cell = @mod(@floor(x / 1.5) + @floor(z / 1.5), 2);

        return shade(if (cell < 1) .{ 186, 182, 174 } else .{ 176, 172, 164 }, light * ao);
    }

    if (x < -110 and z < 30) {
        const marram = tr.smooth(0.45, 0.6, tr.fbm(x * 0.09, z * 0.09));

        return shade(mix3(.{ 220, 200, 156 }, .{ 150, 150, 92 }, marram * 0.8), light * ao);
    }

    const lawn = mix3(.{ 112, 150, 72 }, .{ 136, 162, 84 }, fleck);
    const worn = mix3(lawn, .{ 150, 140, 104 }, tr.smooth(0.6, 0.75, tr.fbm(x * 0.05, z * 0.05)) * 0.6);

    return shade(worn, light * ao);
}

const max_shadow = 900;
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

var spawn_list: std.ArrayList(Vec3) = .empty;
var spawn_yaw: std.ArrayList(f32) = .empty;
var anchor_list: std.ArrayList(Vec3) = .empty;
var park_list: std.ArrayList(wd.Spot) = .empty;
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

fn putAt(b: *Builder, e: K, x: f32, y: f32, z: f32, yaw: f32) void {
    b.putAt(of(e), vec(x, y, z), yaw, 1);
}

fn seaWall(b: *Builder) void {
    var x: f32 = -174;

    while (x < harbour_x - 4) : (x += 4) {
        const cx = x + 2;

        if (@abs(cx - pier_x) < 5) continue;

        const by = beachY(cx, wall_z - 1.2);

        putAt(b, .seawall, cx, by - 0.2, wall_z - 1.16, pi);
        box(b, x, by - 1, wall_z - 2.3, x + 4, prom_y + 0.15, wall_z);
    }

    for ([_]f32{ -150, -84, -40, 44, 74 }) |sx| stairsDown(b, sx);

    x = -172;

    while (x < harbour_x - 4) : (x += 4) {
        const cx = x + 2;

        if (@abs(cx - pier_x) < 6) continue;

        if (@mod(@as(i32, @intFromFloat(x)), 16) == 0) {
            putAt(b, .lamp, cx, prom_y, wall_z + 0.6, 0);
        }

        putAt(b, .rail, cx, prom_y, wall_z + 0.15, 0);
    }
}

fn stairsDown(b: *Builder, x: f32) void {
    const by = beachY(x, wall_z - 7);

    putAt(b, .walkover, x, by, wall_z - 3.6, 0);
    b.solid(.{ .ramp = .{ .min = vec(x - 0.95, by, wall_z - 7.6), .max = vec(x + 0.95, prom_y, wall_z - 0.1), .rise = .pos_z } });
    claimRect(x - 3, wall_z - 9, x + 3, wall_z);
}

fn tiles(b: *Builder, e: K, x0: f32, x1: f32, z0: f32, z1: f32, y: ?f32) void {
    var z = z0 + 2;

    while (z < z1 - 1) : (z += 4) {
        var x = x0 + 2;

        while (x < x1 - 1) : (x += 4) {
            putAt(b, e, x, (y orelse tr.height(x, z)) + 0.02, z, 0);
        }
    }
}

fn promenade(b: *Builder) void {
    tiles(b, .paving, -172, harbour_x - 2, wall_z, road_z0, prom_y);

    var x: f32 = -168;
    var n: u32 = 0;

    while (x < harbour_x - 6) : (x += 6) {
        n += 1;

        if (@abs(x - pier_x) < 10) continue;

        const z = wall_z + 4.5;
        const roll = (n * 7) % 9;

        switch (roll) {
            0, 5 => {
                putAt(b, .bench, x, prom_y, z, 0);
                putAt(b, .bin, x + 1.8, prom_y, z, 0);
            },
            1 => putAt(b, .shelter, x, prom_y, z + 1.5, pi),
            2 => {
                putAt(b, .icecream, x, prom_y, z, half_pi);
                putAt(b, .bin, x + 2, prom_y, z - 1, 0);
            },
            3 => putAt(b, .planter, x, prom_y, z + 2, 0),
            4 => {
                putAt(b, .bench, x, prom_y, z, 0);
                putAt(b, .buoy, x - 2.5, prom_y, wall_z + 1.2, 0);
            },
            6 => putAt(b, .phone, x, prom_y, z + 2, pi),
            7 => putAt(b, .newsstand, x, prom_y, z + 2, pi),
            else => putAt(b, .shrub, x, prom_y, z + 2, 0),
        }

        if (n % 4 == 0) putAt(b, .bunting, x + 3, prom_y + 3.0, wall_z + 0.6, 0);
    }

    house(b, .kiosk, -60, wall_z + 8, 0);
    house(b, .toilets, -120, wall_z + 8, 0);
    house(b, .kiosk, 60, wall_z + 8, 0);
    house(b, .arcade, 22, wall_z + 9.2, pi);
    house(b, .kiosk, -22, wall_z + 9.5, pi);
    putAt(b, .parasol, -16, prom_y, wall_z + 4, 0);
    putAt(b, .parasol, -28, prom_y, wall_z + 4, 0);
    putAt(b, .bench, -12, prom_y, wall_z + 3, 0);
    lootY(b, -22, prom_y, wall_z + 3);
    lootY(b, 22, prom_y, wall_z + 3);
    lootY(b, -60, prom_y, wall_z + 3);
    lootY(b, 60, prom_y, wall_z + 3);
    spawnY(b, -110, prom_y, wall_z + 5, pi);
    spawnY(b, 80, prom_y, wall_z + 5, pi);
}

fn pier(b: *Builder) void {
    var z: f32 = wall_z - 2;

    while (z > pier_end + 10) : (z -= 4) {
        for ([_]f32{ -2, 2 }) |dx| {
            putAt(b, .deck, pier_x + dx, prom_y, z, 0);
            putAt(b, .piles, pier_x + dx, prom_y, z, 0);
        }

        putAt(b, .rail, pier_x - 4.1, prom_y, z, half_pi);
        putAt(b, .rail, pier_x + 4.1, prom_y, z, half_pi);

        if (@mod(@as(i32, @intFromFloat(-z)), 24) == 2) {
            putAt(b, .lamp, pier_x - 3.4, prom_y, z, 0);
            putAt(b, .lamp, pier_x + 3.4, prom_y, z, 0);
        }

        if (@mod(@as(i32, @intFromFloat(-z)), 32) == 10) {
            putAt(b, .bench, pier_x - 2.6, prom_y, z, half_pi);
            putAt(b, .bench, pier_x + 2.6, prom_y, z + 2, half_pi);
        }
    }

    box(b, pier_x - 4, prom_y - 1, pier_end + 8, pier_x + 4, prom_y, wall_z);
    box(b, pier_x - 4.25, prom_y, pier_end + 8, pier_x - 3.95, prom_y + 1.15, wall_z - 2);
    box(b, pier_x + 3.95, prom_y, pier_end + 8, pier_x + 4.25, prom_y + 1.15, wall_z - 2);

    const hz = pier_end;

    var ix: f32 = -10;

    while (ix <= 10) : (ix += 4) {
        var iz: f32 = -10;

        while (iz <= 10) : (iz += 4) {
            putAt(b, .deck, pier_x + ix, prom_y, hz + iz, 0);
            putAt(b, .piles, pier_x + ix, prom_y, hz + iz, 0);
        }
    }

    box(b, pier_x - 12, prom_y - 1, hz - 12, pier_x + 12, prom_y, hz + 12);

    var e: f32 = -10;

    while (e <= 10) : (e += 4) {
        putAt(b, .rail, pier_x + e, prom_y, hz - 12, 0);

        if (@abs(e) > 5) putAt(b, .rail, pier_x + e, prom_y, hz + 12, 0);

        putAt(b, .rail, pier_x - 12, prom_y, hz + e, half_pi);
        putAt(b, .rail, pier_x + 12, prom_y, hz + e, half_pi);
    }

    box(b, pier_x - 12.2, prom_y, hz - 12.2, pier_x + 12.2, prom_y + 1.15, hz - 11.9);
    box(b, pier_x - 12.2, prom_y, hz - 12.2, pier_x - 11.9, prom_y + 1.15, hz + 12.2);
    box(b, pier_x + 11.9, prom_y, hz - 12.2, pier_x + 12.2, prom_y + 1.15, hz + 12.2);

    const bs = bld(.bandstand);

    b.putAt(bs.kind, vec(pier_x, prom_y, hz - 2), 0, 1);

    for (bs.blocks) |bl| {
        const r = wd.rotBox(pier_x, hz - 2, 0, bl[0], bl[1], bl[2], bl[3]);

        if (bl[4] > 5) box(b, r[0], prom_y, r[1], r[2], prom_y + 0.4, r[3]);
    }

    for ([_][2]f32{ .{ -3.6, -5.6 }, .{ 3.6, -5.6 }, .{ -3.6, 1.6 }, .{ 3.6, 1.6 } }) |p| box(b, pier_x + p[0] - 0.2, prom_y, hz - 2 + p[1] - 0.2, pier_x + p[0] + 0.2, prom_y + 6, hz - 2 + p[1] + 0.2);

    putAt(b, .kiosk, pier_x + 8, prom_y, hz + 8, pi);
    box(b, pier_x + 6, prom_y, hz + 6, pier_x + 10, prom_y + 3.4, hz + 10);
    putAt(b, .icecream, pier_x - 8, prom_y, hz + 8, 0);
    putAt(b, .bench, pier_x - 9, prom_y, hz - 9, 0.8);
    putAt(b, .bench, pier_x + 9, prom_y, hz - 9, -0.8);
    putAt(b, .flag, pier_x - 11, prom_y, hz - 11, 0);
    putAt(b, .flag, pier_x + 11, prom_y, hz - 11, 0);
    putAt(b, .buoy, pier_x, prom_y, hz - 11.4, 0);
    putAt(b, .pots, pier_x + 10, prom_y, hz - 2, 0);
    putAt(b, .pots, pier_x + 10.4, prom_y, hz - 1, 0.3);
    putAt(b, .nets, pier_x - 9.5, prom_y, hz, 0.4);
    putAt(b, .bin, pier_x - 4, prom_y, hz + 10, 0);

    lootY(b, pier_x, prom_y, hz);
    lootY(b, pier_x - 8, prom_y, hz - 8);
    lootY(b, pier_x, prom_y, -70);
    spawnY(b, pier_x, prom_y, hz + 6, 0);
    spawnY(b, pier_x, prom_y, -90, 0);
    anchor_list.append(b.gpa, vec(pier_x, prom_y + 18, hz)) catch {};
    anchor_list.append(b.gpa, vec(pier_x, prom_y + 16, -80)) catch {};
    claimRect(pier_x - 13, hz - 13, pier_x + 13, wall_z);
}

fn beach(b: *Builder) void {
    var gx: f32 = -136;

    while (gx < harbour_x - 10) : (gx += 34) {
        if (@abs(gx - pier_x) < 12) continue;

        var z: f32 = wall_z - 4;

        while (z > shoreZ(gx) - 14) : (z -= 4) {
            const y = @max(beachY(gx, z), sea_y - 0.1);

            putAt(b, .groyne, gx, y - 0.25, z, half_pi);
            box(b, gx - 0.4, y - 1, z - 2, gx + 0.4, y + 1.1, z + 2);
        }

        claimRect(gx - 1, shoreZ(gx) - 14, gx + 1, wall_z);
        put(b, .pots, gx + 3, shoreZ(gx) + 6, 0.4);
        put(b, .driftwood, gx + 5, shoreZ(gx) + 9, 1.3);
        loot(b, gx + 2.5, wall_z - 10);
        spawnAt(b, gx + 3, wall_z - 12, pi);
    }

    var x: f32 = -150;

    while (x < harbour_x - 6) : (x += 7) {
        if (@abs(x - pier_x) < 7) continue;

        const z0 = wall_z - 5;
        const z1 = shoreZ(x) + 6;
        var z = z0 - b.rng.range(0, 4);

        while (z > z1) : (z -= b.rng.range(5, 9)) {
            const px = x + b.rng.range(-2.5, 2.5);

            if (taken(px, z, 1)) continue;

            const roll = rnd(b);

            if (roll < 0.2) {
                put(b, .parasol, px, z, 0);
                put(b, .lounger, px + 1.1, z - 0.4, 0.1);
                put(b, .lounger, px - 1.1, z - 0.4, -0.1);
            } else if (roll < 0.34) {
                put(b, .windbreak, px, z, b.rng.range(-0.4, 0.4));
                put(b, .lounger, px + 0.4, z - 1.4, pi + 0.3);
            } else if (roll < 0.46) {
                put(b, .lounger, px, z, pi + b.rng.range(-0.4, 0.4));
                put(b, .lounger, px + 1.1, z + 0.2, pi + b.rng.range(-0.4, 0.4));
            } else if (roll < 0.6) {
                put(b, .dinghy, px, z, b.rng.range(-0.5, 0.5));
            } else if (roll < 0.66) {
                put(b, .driftwood, px, z, spin(b));
            }
        }
    }

    var hx: f32 = -100;

    while (hx < -60) : (hx += 4.4) {
        const e: K = switch (@as(u32, @intFromFloat(@mod(hx, 3)))) {
            0 => .hut,
            1 => .hut_b,
            else => .hut,
        };
        const y = beachY(hx, wall_z - 6);

        putAt(b, e, hx, y, wall_z - 6, pi);
        box(b, hx - 2, y - 0.5, wall_z - 8.4, hx + 2, y + 4.9, wall_z - 3.6);
    }

    claimRect(-102, wall_z - 9, -58, wall_z);
    putAt(b, .cubicles, 30, beachY(30, wall_z - 4.5), wall_z - 4.5, pi);
    box(b, 26, beachY(30, wall_z - 4.5) - 0.5, wall_z - 5.4, 34, beachY(30, wall_z - 4.5) + 2.2, wall_z - 3.6);
    claimRect(25, wall_z - 7, 35, wall_z);

    for ([_]f32{ -70, 66 }) |tx| {
        const tz = wall_z - 22;
        const y = beachY(tx, tz);

        putAt(b, .tower, tx, y, tz, pi);

        for ([_][2]f32{ .{ -1.6, -1.6 }, .{ 1.6, -1.6 }, .{ -1.6, 1.6 }, .{ 1.6, 1.6 } }) |p| box(b, tx + p[0] - 0.15, y, tz + p[1] - 0.15, tx + p[0] + 0.15, y + 3, tz + p[1] + 0.15);

        put(b, .flag, tx + 3, tz + 1, 0);
        put(b, .buoy, tx - 3, tz + 1, 0);
        claimRect(tx - 4, tz - 4, tx + 4, tz + 4);
        anchor_list.append(b.gpa, vec(tx, y + 16, tz)) catch {};
    }
}

fn dunesWest(b: *Builder) void {
    var z: f32 = wall_z - 4;

    while (z < 40) : (z += 3) {
        var x: f32 = -176;

        while (x < -104) : (x += 3) {
            const px = x + b.rng.range(-1.2, 1.2);
            const pz = z + b.rng.range(-1.2, 1.2);

            if (taken(px, pz, 0.6) or pz < shoreZ(px) + 4) continue;

            const roll = rnd(b);

            if (roll < 0.3) put(b, .marram, px, pz, spin(b)) else if (roll < 0.34) put(b, .shrub, px, pz, spin(b)) else if (roll < 0.36 and pz > 0) put(b, .pine, px, pz, spin(b));
        }
    }

    var fz: f32 = -14;

    while (fz < 36) : (fz += 12) {
        var fx: f32 = -172;

        while (fx < -112) : (fx += 4) {
            if (@mod(@as(i32, @intFromFloat(-fx)), 20) < 4) continue;

            put(b, .dunefence, fx, fz, 0);
        }
    }

    spawnAt(b, -150, 10, half_pi);
    spawnAt(b, -130, -30, half_pi);
    loot(b, -140, 0);
    loot(b, -160, 24);
}

fn harbour(b: *Builder) void {
    var z: f32 = -26;

    while (z > -110) : (z -= 4) {
        putAt(b, .seawall, harbour_x + 6.8, sea_y - 1.4, z - 2, half_pi);
        box(b, harbour_x + 5.6, sea_y - 2, z - 4, harbour_x + 8, prom_y, z);
    }

    var x: f32 = harbour_x + 10;

    while (x < 214) : (x += 4) {
        putAt(b, .revet, x, sea_y - 0.3, -112, 0);
        putAt(b, .revet, x, sea_y - 0.2, -114, pi);
    }

    box(b, harbour_x + 8, -2, -115, 215, prom_y - 0.6, -110);

    putAt(b, .slipway, harbour_x + 14, sea_y - 0.6, -30, 0);
    house(b, .boatshed, harbour_x - 6, -40, -half_pi);
    house(b, .boatshed, harbour_x - 6, -56, -half_pi);
    house(b, .hmhut, harbour_x - 4, -76, -half_pi);
    house(b, .toilets, harbour_x - 4, -94, -half_pi);

    for ([_][3]f32{ .{ 120, -48, 0.1 }, .{ 134, -60, -0.2 }, .{ 150, -44, 0.3 }, .{ 128, -86, 1.4 }, .{ 158, -80, -0.1 } }) |bt| {
        putAt(b, .fishboat, bt[0], sea_y - 0.4, bt[1], bt[2]);
    }

    z = -32;

    while (z > -108) : (z -= 6) {
        putAt(b, .bollard, harbour_x + 4.6, prom_y, z, half_pi);
    }

    for ([_][3]f32{ .{ 103, -48, 0 }, .{ 102, -64, 0.6 }, .{ 103, -84, 1.3 }, .{ 104, -102, 0.2 } }) |p| {
        putAt(b, .pots, p[0], prom_y, p[1], p[2]);
        putAt(b, .pots, p[0] - 0.8, prom_y, p[1] + 0.6, p[2]);
        putAt(b, .nets, p[0] - 1, prom_y, p[1] - 3, p[2]);
        putAt(b, .dinghy, p[0] - 2.4, prom_y, p[1] + 3.6, p[2] + 1.4);
    }

    claimRect(harbour_x - 12, -112, 176, wall_z);
    lootY(b, harbour_x - 2, prom_y, -66);
    lootY(b, harbour_x + 2, prom_y, -100);
    spawnY(b, harbour_x - 2, prom_y, -104, 0);
    spawnY(b, harbour_x - 8, prom_y, -30, -half_pi);
    anchor_list.append(b.gpa, vec(140, 18, -70)) catch {};
}

fn seaRoad(b: *Builder) void {
    var x: f32 = -170;

    while (x < 170) : (x += 4) {
        putAt(b, .kerb, x + 2, height(x + 2, road_z0), road_z0, 0);
        putAt(b, .kerb, x + 2, height(x + 2, road_z1), road_z1, 0);

        if (@mod(@as(i32, @intFromFloat(x)), 8) == 0) putAt(b, .line, x + 2, height(x + 2, -1) + 0.01, -1, 0);
    }

    var px: f32 = -160;

    while (px < 160) : (px += 6.5) {
        if (rnd(b) < 0.45) continue;

        const e: K = b.rng.pick(K, &.{ .camper, .hatch, .sedan, .hatch });

        put(b, e, px, road_z1 - 1.6, half_pi + (if (rnd(b) < 0.5) @as(f32, 0) else pi));
    }

    for ([_]f32{ -140, -70, 0, 70, 140 }) |cx| park_list.append(b.gpa, .{ .pos = vec(cx, height(cx, -2.5), -2.5), .yaw = half_pi }) catch {};
}

const terrace_kinds = [_]K{ .terrace_a, .terrace_b, .terrace_c, .terrace_d, .terrace_b, .terrace_c, .terrace_a, .terrace_d, .terrace_c };

fn terraceRow(b: *Builder, x0: f32, x1: f32, z: f32, yaw: f32, seed: u32) void {
    var x = x0 + 2.25;
    var i: u32 = seed;

    while (x < x1 - 2) : (x += 4.5) {
        i += 1;
        house(b, terrace_kinds[(i * 5 + seed) % terrace_kinds.len], x, z, yaw);
    }
}

const blocks_x = [_][2]f32{ .{ -168, -104 }, .{ -96, -48 }, .{ 48, 96 }, .{ 104, 166 } };

fn yard(b: *Builder, x0: f32, x1: f32, z0: f32, z1: f32) void {
    var x = x0 + 2;

    while (x < x1 - 2) : (x += 4) {
        putAt(b, .fence, x, tr.height(x, (z0 + z1) / 2), (z0 + z1) / 2, 0);
        box(b, x - 2, tr.height(x, (z0 + z1) / 2) - 0.5, (z0 + z1) / 2 - 0.15, x + 2, tr.height(x, (z0 + z1) / 2) + 1.8, (z0 + z1) / 2 + 0.15);
    }

    x = x0 + 4;

    while (x < x1 - 4) : (x += 9) {
        const roll = rnd(b);
        const side: f32 = if (rnd(b) < 0.5) -2 else 2;
        const z = (z0 + z1) / 2 + side;

        if (roll < 0.25) {
            put(b, .shed, x, z, if (side < 0) pi else 0);
        } else if (roll < 0.45) {
            put(b, .tree, x, z, spin(b));
        } else if (roll < 0.6) {
            put(b, .bin, x, z, 0);
            put(b, .bin, x + 1, z, 0);
        } else if (roll < 0.75) {
            put(b, .shrub, x, z, spin(b));
            put(b, .planter, x + 1.6, z, 0);
        } else {
            put(b, .bikes, x, z, 0);
        }
    }
}

fn front(b: *Builder) void {
    tiles(b, .sidewalk, -172, 172, road_z1, road_z1 + 6, null);
    tiles(b, .sidewalk, -172, 172, high_z - 10, high_z - 4, null);
    tiles(b, .sidewalk, -172, 172, high_z + 4, high_z + 8, null);
    for (blocks_x, 0..) |s, n| {
        const seed: u32 = @intCast(n * 3);

        house(b, .corner, s[0] + 4.5, 14.5, pi);
        terraceRow(b, s[0] + 9, s[1] - 9, 14, pi, seed);
        house(b, if (n % 2 == 0) .tavern else .corner, s[1] - 4.5, 14.5, pi);

        house(b, .corner, s[0] + 4.5, 29.5, 0);
        terraceRow(b, s[0] + 9, s[1] - 9, 30, 0, seed + 1);
        house(b, .corner, s[1] - 4.5, 29.5, 0);

        house(b, if (n % 2 == 1) .tavern else .corner, s[0] + 4.5, 54.5, pi);

        if (n == 1 or n == 2) {
            terraceRow(b, s[0] + 9, s[1] - 24, 54, pi, seed + 2);
            house(b, .hotel, s[1] - 19, 54.5, pi);
            house(b, .hotel, s[1] - 11, 54.5, pi);
        } else terraceRow(b, s[0] + 9, s[1] - 9, 54, pi, seed + 2);

        house(b, .corner, s[1] - 4.5, 54.5, pi);
        yard(b, s[0] + 9, s[1] - 9, 18.5, 25.5);
        highStreet(b, s[0], s[1]);
    }

    house(b, .hotel, -32, 14.5, pi);
    house(b, .hotel, -24, 14.5, pi);
    terraceRow(b, -20, 20, 14, pi, 7);
    house(b, .hotel, 24, 14.5, pi);
    house(b, .hotel, 32, 14.5, pi);
    yard(b, -36, 36, 18.5, 25.5);

    for (streets_x) |sx| {
        put(b, .tree, sx - 5.6, road_z1 + 3.6, 0);
        put(b, .tree, sx + 5.6, road_z1 + 3.6, 0);
        put(b, .lamp, sx + 5.0, high_z - 5.4, 0);
        put(b, .lamp, sx - 5.0, high_z + 5.4, 0);
        spawnAt(b, sx, 24, pi);
    }
}

fn highStreet(b: *Builder, x0: f32, x1: f32) void {
    var x = x0 + 6;

    while (x < x1 - 4) : (x += 5.5) {
        const roll = rnd(b);
        const zs = high_z - 5.6;
        const zn = high_z + 5.6;

        if (roll < 0.14) {
            put(b, .bench, x, zs, 0);
        } else if (roll < 0.26) {
            put(b, .planter, x, zn, 0);
        } else if (roll < 0.34) {
            put(b, .phone, x, zs, 0);
        } else if (roll < 0.42) {
            put(b, .bikes, x, zn, 0);
        } else if (roll < 0.5) {
            put(b, .newsstand, x, zs, 0);
        } else if (roll < 0.62) {
            put(b, .bin, x, zn, 0);
            put(b, .tree, x + 2, zn + 0.6, 0);
        }

        if (rnd(b) < 0.5) put(b, b.rng.pick(K, &.{ .hatch, .sedan, .camper, .hatch }), x + 1, high_z + 2.3 * (if (rnd(b) < 0.5) @as(f32, 1) else -1), half_pi + (if (rnd(b) < 0.5) @as(f32, 0) else pi));
    }

    lootY(b, (x0 + x1) / 2, tr.height((x0 + x1) / 2, high_z), high_z);
    spawnAt(b, (x0 + x1) / 2 + 6, high_z, half_pi);
}

fn square(b: *Builder) void {
    const cz: f32 = 44;

    house(b, .clock, 0, cz, 0);

    for ([_][2]f32{ .{ -14, -9 }, .{ 14, -9 }, .{ -14, 9 }, .{ 14, 9 }, .{ -30, 0 }, .{ 30, 0 } }) |o| put(b, .tree, o[0], cz + o[1], spin(b));

    for ([_][3]f32{ .{ -6, -6, 0.8 }, .{ 6, -6, -0.8 }, .{ -6, 6, 2.3 }, .{ 6, 6, -2.3 } }) |o| put(b, .bench, o[0], cz + o[1], o[2]);

    for ([_]f32{ -22, -10, 10, 22 }) |px| put(b, .planter, px, cz + 12, 0);

    put(b, .phone, -20, cz - 10, 0);
    put(b, .phone, -18.6, cz - 10, 0);
    put(b, .newsstand, 20, cz - 10, pi);
    put(b, .icecream, 24, cz + 4, half_pi);
    put(b, .shelter, -24, cz + 6, half_pi);
    terraceRow(b, -36, -10, 62, pi, 4);
    house(b, .tavern, -4, 62, pi);
    house(b, .corner, 6, 62, pi);
    terraceRow(b, 12, 36, 62, pi, 5);
    claimRect(-40, 26, 40, 58);
    lootY(b, 0, tr.height(0, 36), 36);
    lootY(b, -12, tr.height(-12, 52), 52);
    spawnAt(b, 0, 54, pi);
    anchor_list.append(b.gpa, vec(0, tr.height(0, 44) + 22, 44)) catch {};
}

fn hillside(b: *Builder) void {
    const villas = [_]K{ .villa, .cottage, .villa, .tavern, .cottage, .villa };
    var z: f32 = 76;
    var row: u32 = 0;

    while (z < 128) : (z += 17) {
        row += 1;

        var x: f32 = -160 + @as(f32, @floatFromInt(row % 2)) * 10;

        while (x < 160) : (x += 22) {
            const px = x + b.rng.range(-3, 3);

            if (taken(px, z, 5)) continue;

            house(b, villas[@as(usize, @intFromFloat(@abs(px))) % villas.len], px, z, pi);

            const y = tr.height(px, z + 7);

            putAt(b, .picket, px - 2, y, z - 6.5, 0);
            putAt(b, .picket, px + 2, y, z - 6.5, 0);
            put(b, .tree, px + 7, z + 3, spin(b));
            put(b, .shrub, px - 6, z - 4, spin(b));

            if (rnd(b) < 0.4) put(b, b.rng.pick(K, &.{ .hatch, .camper }), px + 6, z - 5, 0.1);

            if (rnd(b) < 0.5) lootY(b, px + 4, tr.height(px + 4, z - 7), z - 7);
        }
    }

    z = 66;

    while (z < 210) : (z += 4) {
        var x: f32 = -214;

        while (x < 214) : (x += 4.5) {
            const px = x + b.rng.range(-1.8, 1.8);
            const pz = z + b.rng.range(-1.8, 1.8);

            if (taken(px, pz, 1.2) or (@abs(px) < 40 and pz < 70)) continue;

            const roll = rnd(b);
            const far = pz > 140;

            if (roll < (if (far) @as(f32, 0.34) else 0.14)) {
                put(b, if (rnd(b) < 0.6) .pine else .tree, px, pz, spin(b));
            } else if (roll < 0.42) {
                put(b, .shrub, px, pz, spin(b));
            }
        }
    }

    for ([_]f32{ -120, -60, 0, 60, 120 }) |sx| spawnAt(b, sx, 100, pi);

    anchor_list.append(b.gpa, vec(-80, 50, 110)) catch {};
    anchor_list.append(b.gpa, vec(80, 50, 110)) catch {};
}

fn shoreFoam(b: *Builder) void {
    var x: f32 = -214;

    while (x < 214) : (x += 6) {
        if (x > harbour_x + 2) continue;

        const z = shoreZ(x);
        const slope = shoreZ(x + 1) - shoreZ(x - 1);

        b.putAt(of(.foam), vec(x, sea_y + 0.01, z - 1.2), std.math.atan2(-slope * 0.5, 1) + b.rng.range(-0.08, 0.08), b.rng.range(0.9, 1.1));

        if (rnd(b) < 0.6) b.putAt(of(.ripple), vec(x + b.rng.range(-2, 2), sea_y + 0.005, z - 6 - b.rng.range(0, 6)), b.rng.range(-0.1, 0.1), b.rng.range(0.8, 1.2));
    }

    var z: f32 = -28;

    while (z > -108) : (z -= 6) b.putAt(of(.foam), vec(harbour_x + 8.8, sea_y + 0.01, z), half_pi, 0.9);

    var px: f32 = harbour_x + 12;

    while (px < 214) : (px += 6) {
        b.putAt(of(.foam), vec(px, sea_y + 0.01, -116), 0, 1);
        b.putAt(of(.foam), vec(px + 3, sea_y + 0.01, -109.5), 0, 0.8);
    }

    var pz: f32 = wall_z - 30;

    while (pz > pier_end - 12) : (pz -= 4) {
        b.putAt(of(.ripple), vec(pier_x - 4.5, sea_y + 0.01, pz), half_pi, 0.5);
        b.putAt(of(.ripple), vec(pier_x + 4.5, sea_y + 0.01, pz - 2), half_pi, 0.5);
    }
}

fn build(b: *Builder) void {
    @memset(&occ, 0);
    shadow_n = 0;
    spawn_list = .empty;
    spawn_yaw = .empty;
    anchor_list = .empty;
    park_list = .empty;
    loot_list = .empty;

    harbour(b);
    pier(b);
    seaWall(b);
    promenade(b);
    seaRoad(b);
    square(b);
    front(b);
    hillside(b);
    beach(b);
    dunesWest(b);
    shoreFoam(b);
}

fn setSpots(gpa: std.mem.Allocator) void {
    wd.spawns = gpa.dupe(Vec3, spawn_list.items) catch &.{};
    wd.spawn_yaws = gpa.dupe(f32, spawn_yaw.items) catch &.{};
    wd.weapon_spots = gpa.dupe(Vec3, loot_list.items) catch &.{};
    wd.drone_anchors = gpa.dupe(Vec3, anchor_list.items) catch &.{};
    wd.vehicle_spots = gpa.dupe(wd.Spot, park_list.items) catch &.{};
    wd.parkClear(gpa);
}
