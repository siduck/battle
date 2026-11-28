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
    .note = "Seaside town, pier and promenade",
    .tint = .{ 226, 196, 140 },
    .half = api.arena_half + api.arena_rim,
    .play = api.arena_half,
    .facet = 2.0,
    .height = height,
    .water = water,
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
    .backdrop = .{ 48, 106, 128 },
    .floor_y = 0.12,
    .grip = 0.84,
};

const sea_y: f32 = 0.35;
const prom_y: f32 = 3.2;
const wall_z: f32 = -20;
const road_z0: f32 = -6;
const road_z1: f32 = 4;
const pier_x: f32 = 0;
const pier_end: f32 = -(api.arena_half - 14);
const edge: f32 = api.arena_half;
const street_end: f32 = api.arena_half - 7;

fn shoreZ(x: f32) f32 {
    return -40 + 4 * @sin(x * 0.021 + 0.7) + 2 * @sin(x * 0.053);
}

fn townLift(x: f32, z: f32) f32 {
    const street = @min(@max(0, z - 8), 52) * 0.035;
    const hill = tr.smooth(edge - 12, edge + 20, z) * 26 * (0.8 + 0.4 * tr.fbm(x * 0.012 + 3, 7));
    const side = tr.smooth(edge, edge + 16, @abs(x)) * 9;
    const roll = (tr.fbm(x * 0.03 + 3, z * 0.03 - 5) - 0.5) * 2.4 * tr.smooth(edge - 10, edge + 10, @max(z, @abs(x)));

    return street + @max(hill, side) + @max(roll, 0);
}

fn dunes(x: f32, z: f32) f32 {
    const m = tr.smooth(edge - 6, edge + 12, @abs(x));
    const wave = @sin(x * 0.11 + z * 0.07) * 0.6 + tr.fbm(x * 0.05, z * 0.05) * 3;

    return m * (wave + 5) * tr.smooth(shoreZ(x) - 2, shoreZ(x) + 14, z);
}

fn beachY(x: f32, z: f32) f32 {
    const s = shoreZ(x);
    const t = std.math.clamp((z - s) / (wall_z - 1 - s), 0, 1);

    return sea_y + t * 1.15 + dunes(x, z);
}

fn height(x: f32, z: f32) f32 {
    const s = shoreZ(x);

    if (z < s) return sea_y - 0.02;

    if (z < wall_z - 1) return beachY(x, z);

    if (z < wall_z) return std.math.lerp(beachY(x, wall_z - 1), prom_y, z - (wall_z - 1));

    return prom_y + townLift(x, z);
}

fn roadDist(x: f32, z: f32) f32 {
    var best = @max(@abs(z - (road_z0 + road_z1) / 2) - 5, 0);

    if (@abs(x) > edge + 1) return 1000;

    best = @min(best, @max(@abs(z - high_z) - 4, 0));

    for (streets_x) |sx| {
        if (z > road_z1 and z < street_end) best = @min(best, @max(@abs(x - sx) - 4, 0));
    }

    return best;
}

const streets_x = [_]f32{ -44, 44 };
const high_z: f32 = 42;

fn onStreet(x: f32, z: f32) bool {
    return roadDist(x, z) <= 0;
}

fn water(x: f32, z: f32) bool {
    return z < shoreZ(x) - 0.5;
}

fn waterColor(d: f32, x: f32, z: f32) api.Rgb {
    const wave = tr.fbm(x * 0.05 + 3, z * 0.05 - 4) * 0.1 + 0.95;
    const shallow = [3]f32{ 122, 188, 178 };
    const mid = [3]f32{ 62, 141, 150 };
    const deep = [3]f32{ 48, 106, 128 };
    const c = if (d < 12) mix3(shallow, mid, tr.smooth(0, 12, d)) else mix3(mid, deep, tr.smooth(12, 60, d));

    return shade(c, wave);
}

fn groundColor(x: f32, z: f32) api.Rgb {
    const light = api.light(x, z);
    const fleck = tr.fbm(x * 0.35 - 7, z * 0.35 + 5);

    const s = shoreZ(x);

    if (z < s) return waterColor(s - z, x, z);

    const ao = contact(x, z);

    if (z < wall_z) {
        const wet = 1 - tr.smooth(s, s + 7, z);
        const dry = mix3(.{ 214, 192, 154 }, .{ 202, 179, 141 }, fleck);
        const sand = mix3(dry, .{ 164, 142, 112 }, wet * 0.8);
        const tide = if (z - s > 7 and z - s < 8.2) @as(f32, 0.93) else 1;

        return shade(sand, light * tide * ao);
    }

    if (z < road_z0 and @abs(x) < edge + 1) {
        const cell = @mod(@floor(x / 2) + @floor(z / 2), 2);

        return shade(if (cell < 1) .{ 190, 173, 145 } else .{ 184, 167, 139 }, light * ao);
    }

    if (@abs(x) < 38 and z > 26 and z < 58) {
        const cell = @mod(@floor(x / 2) + @floor(z / 2), 2);

        return shade(if (cell < 1) .{ 180, 169, 152 } else .{ 167, 156, 140 }, light * ao);
    }

    if (onStreet(x, z)) {
        const patch = tr.fbm(x * 0.08, z * 0.08);

        return shade(mix3(.{ 96, 92, 88 }, .{ 110, 104, 97 }, patch), light * ao);
    }

    if (roadDist(x, z) < 2.6) {
        const cell = @mod(@floor(x / 1.5) + @floor(z / 1.5), 2);

        return shade(if (cell < 1) .{ 186, 177, 161 } else .{ 177, 168, 153 }, light * ao);
    }

    if (@abs(x) > edge and z < 30) {
        const marram = tr.smooth(0.45, 0.6, tr.fbm(x * 0.09, z * 0.09));

        return shade(mix3(.{ 204, 182, 144 }, .{ 138, 142, 98 }, marram * 0.8), light * ao);
    }

    const lawn = mix3(.{ 114, 132, 82 }, .{ 132, 146, 90 }, fleck);
    const worn = mix3(lawn, .{ 150, 135, 105 }, tr.smooth(0.6, 0.75, tr.fbm(x * 0.05, z * 0.05)) * 0.6);
    const lane_z = @abs(@mod(z - 84.5 + @sin(x * 0.045) * 3, 17) - 8.5);
    const lane_x = @abs(@mod(x + 22 + @sin(z * 0.06) * 4, 44) - 22);
    const lane = @max(1 - tr.smooth(1.0, 1.8, 8.5 - lane_z), 1 - tr.smooth(1.0, 1.8, 22 - lane_x));
    const gravel = mix3(.{ 188, 173, 147 }, .{ 170, 156, 133 }, tr.fbm(x * 1.3, z * 1.3));
    const bed = tr.smooth(0.62, 0.7, tr.fbm(x * 0.21 + 7, z * 0.21 - 3));
    const garden = mix3(worn, .{ 108, 85, 68 }, bed * 0.7);
    const hill = tr.smooth(68, 76, z) * (1 - tr.smooth(134, 142, z));

    return shade(mix3(if (hill > 0.5) garden else worn, gravel, lane * hill), light * ao);
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
    var x: f32 = -edge;

    while (x < edge) : (x += 4) {
        const cx = x + 2;

        if (@abs(cx - pier_x) < 5) continue;

        const by = beachY(cx, wall_z - 1.2);

        putAt(b, .seawall, cx, by - 0.2, wall_z - 1.16, pi);
        box(b, x, by - 1, wall_z - 2.3, x + 4, prom_y + 0.15, wall_z);
    }

    for ([_]f32{ -62, -40, 44, 62 }) |sx| stairsDown(b, sx);

    x = -edge + 2;

    while (x < edge - 2) : (x += 4) {
        const cx = x + 2;

        if (@abs(cx - pier_x) < 6) continue;

        if (@mod(@as(i32, @intFromFloat(x)), 16) == 0) {
            putAt(b, .lamp, cx, prom_y, wall_z + 0.6, 0);
        }

        putAt(b, .rail, cx, prom_y, wall_z + 0.15, 0);
    }

    for ([_]f32{ -1, 1 }) |sd| {
        const ex = sd * (edge - 0.3);
        var z = wall_z + 2;

        while (z < road_z0) : (z += 4) {
            putAt(b, .rail, ex, prom_y, z, half_pi);
            box(b, ex - 0.15, prom_y, z - 2, ex + 0.15, prom_y + 1.15, z + 2);
        }

        putAt(b, .lamp, ex - sd * 0.8, prom_y, wall_z + 0.6, 0);
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
    tiles(b, .paving, -edge, edge, wall_z, road_z0, prom_y);

    var x: f32 = -edge + 7;
    var n: u32 = 0;

    while (x < edge - 6) : (x += 6) {
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
                putAt(b, .bench, x, prom_y, z, 0);
                putAt(b, .bin, x + 2, prom_y, z - 1, 0);
            },
            3 => putAt(b, .planter, x, prom_y, z + 2, 0),
            4 => {
                putAt(b, .bench, x, prom_y, z, 0);
                putAt(b, .buoy, x - 2.5, prom_y, wall_z + 1.2, 0);
            },
            6 => putAt(b, .phone, x, prom_y, z + 2, pi),
            7 => putAt(b, .stall, x, prom_y, z + 2, pi),
            else => putAt(b, .shrub, x, prom_y, z + 2, 0),
        }

        if (n % 4 == 0) putAt(b, .bunting, x + 3, prom_y + 3.0, wall_z + 0.6, 0);
    }

    house(b, .kiosk, -60, wall_z + 8, 0);
    house(b, .toilets, 66, wall_z + 8, 0);
    house(b, .kiosk, 54, wall_z + 8, 0);
    house(b, .arcade, 22, wall_z + 9.2, pi);
    house(b, .kiosk, -22, wall_z + 9.5, pi);
    putAt(b, .parasol, -16, prom_y, wall_z + 4, 0);
    putAt(b, .parasol, -28, prom_y, wall_z + 4, 0);
    putAt(b, .bench, -12, prom_y, wall_z + 3, 0);
    lootY(b, -22, prom_y, wall_z + 3);
    lootY(b, 22, prom_y, wall_z + 3);
    lootY(b, -60, prom_y, wall_z + 3);
    lootY(b, 60, prom_y, wall_z + 3);
    spawnY(b, -64, prom_y, wall_z + 5, pi);
    spawnY(b, 40, prom_y, wall_z + 5, pi);
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
    putAt(b, .bench, pier_x - 8, prom_y, hz + 8, 0);
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
    lootY(b, pier_x, prom_y, wall_z - 18);
    spawnY(b, pier_x, prom_y, hz + 6, 0);
    spawnY(b, pier_x, prom_y, wall_z - 12, 0);
    anchor_list.append(b.gpa, vec(pier_x, prom_y + 18, hz)) catch {};
    anchor_list.append(b.gpa, vec(pier_x, prom_y + 16, wall_z - 20)) catch {};
    claimRect(pier_x - 13, hz - 13, pier_x + 13, wall_z);
}

fn beach(b: *Builder) void {
    var gx: f32 = -68;

    while (gx < edge - 4) : (gx += 34) {
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

        if (@abs(gx + 3) < edge - 10) spawnAt(b, gx + 3, wall_z - 12, pi);
    }

    var x: f32 = -edge + 4;

    while (x < edge - 6) : (x += 7) {
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
                put(b, .windbreak, px, z, b.rng.range(-0.5, 0.5));
            } else if (roll < 0.66) {
                put(b, .driftwood, px, z, spin(b));
            }
        }
    }

    var hx: f32 = -56;

    while (hx < -44) : (hx += 4.4) {
        if (taken(hx, wall_z - 6, 1)) continue;

        const y = beachY(hx, wall_z - 6);

        putAt(b, .hut, hx, y, wall_z - 6, pi);
        box(b, hx - 2, y - 0.5, wall_z - 8.4, hx + 2, y + 4.9, wall_z - 3.6);
    }

    claimRect(-58, wall_z - 9, -42, wall_z);
    putAt(b, .cubicles, 30, beachY(30, wall_z - 4.5), wall_z - 4.5, pi);
    box(b, 26, beachY(30, wall_z - 4.5) - 0.5, wall_z - 5.4, 34, beachY(30, wall_z - 4.5) + 2.2, wall_z - 3.6);
    claimRect(25, wall_z - 7, 35, wall_z);

    for ([_]f32{ -22, 58 }) |tx| {
        const tz = wall_z - 14;
        const y = beachY(tx, tz);

        putAt(b, .tower, tx, y, tz, pi);

        for ([_][2]f32{ .{ -1.6, -1.6 }, .{ 1.6, -1.6 }, .{ -1.6, 1.6 }, .{ 1.6, 1.6 } }) |p| box(b, tx + p[0] - 0.15, y, tz + p[1] - 0.15, tx + p[0] + 0.15, y + 3, tz + p[1] + 0.15);

        put(b, .flag, tx + 3, tz + 1, 0);
        put(b, .buoy, tx - 3, tz + 1, 0);
        claimRect(tx - 4, tz - 4, tx + 4, tz + 4);
        anchor_list.append(b.gpa, vec(tx, y + 16, tz)) catch {};
    }
}

fn jetty(b: *Builder, x: f32) void {
    const z0 = shoreZ(x) + 3;
    const deck_y = sea_y + 1.36;
    var z = z0;
    var n: u32 = 0;

    while (n < 5) : (n += 1) {
        putAt(b, .jetty, x, deck_y - 1.96, z, 0);
        z -= 4;
    }

    const zend = z + 4;

    box(b, x - 2, deck_y - 1, zend - 2, x + 2, deck_y, z0 + 2);
    b.solid(.{ .ramp = .{ .min = vec(x - 1, beachY(x, z0 + 6) - 0.2, z0 + 2), .max = vec(x + 1, deck_y, z0 + 6), .rise = .neg_z } });

    for ([_]f32{ -1.6, 0, 1.6 }) |rx| putAt(b, .rod, x + rx, deck_y, zend - 1.6, half_pi);

    putAt(b, .fishcrate, x - 1.2, deck_y, zend + 0.6, 0.2);
    putAt(b, .fishcrate, x - 0.8, deck_y, zend + 1.1, 1.0);
    putAt(b, .fishcrate, x + 1.3, deck_y, zend + 2.2, 0.4);
    putAt(b, .pots, x + 1.2, deck_y, zend + 4.6, 0);
    putAt(b, .nets, x - 1.2, deck_y, zend + 6.4, 0.3);
    putAt(b, .buoy, x + 1.7, deck_y, z0 - 1, 0);
    claimRect(x - 3, zend - 3, x + 3, z0 + 7);
    lootY(b, x, deck_y, zend + 1);
}

fn beachLife(b: *Builder) void {
    for ([_]f32{ -51, 51 }) |jx| jetty(b, jx);

    var hx: f32 = 48;

    while (hx < edge - 6) : (hx += 4.4) {
        if (@abs(hx - 62) < 4 or taken(hx, wall_z - 6, 1)) continue;

        const y = beachY(hx, wall_z - 6);

        putAt(b, .hut, hx, y, wall_z - 6, pi);
        box(b, hx - 2, y - 0.5, wall_z - 8.4, hx + 2, y + 4.9, wall_z - 3.6);
    }

    claimRect(46, wall_z - 9, edge - 4, wall_z);

    var x: f32 = -edge + 4;

    while (x < edge - 8) : (x += 5) {
        const z = wall_z - 10 - b.rng.range(0, 14);
        const px = x + b.rng.range(-1.5, 1.5);

        if (taken(px, z, 2) or z < shoreZ(px) + 5) continue;

        const roll = rnd(b);

        if (roll < 0.45) {
            put(b, .parasol, px, z, 0);
            put(b, .deckchair, px + 0.9, z - 0.8, pi + b.rng.range(-0.3, 0.3));
            put(b, .deckchair, px - 0.9, z - 0.8, pi + b.rng.range(-0.3, 0.3));
        } else if (roll < 0.7) {
            put(b, .deckchair, px, z, pi + b.rng.range(-0.4, 0.4));
            put(b, .deckchair, px + 0.9, z + 0.2, pi + b.rng.range(-0.4, 0.4));
            put(b, .deckchair, px + 1.8, z, pi + b.rng.range(-0.4, 0.4));
        } else if (roll < 0.85) {
            put(b, .windbreak, px, z, b.rng.range(-0.4, 0.4));
            put(b, .parasol, px + 1, z - 1.5, 0);
        }

        claimRect(px - 2, z - 2, px + 2, z + 2);
    }
}

fn seaRoad(b: *Builder) void {
    var x: f32 = -edge;

    while (x < edge) : (x += 4) {
        putAt(b, .kerb, x + 2, height(x + 2, road_z0), road_z0, 0);
        putAt(b, .kerb, x + 2, height(x + 2, road_z1), road_z1, 0);

        if (@mod(@as(i32, @intFromFloat(x)), 8) == 0) putAt(b, .line, x + 2, height(x + 2, -1) + 0.01, -1, 0);
    }

    var px: f32 = -edge + 6;

    while (px < edge - 4) : (px += 6.5) {
        if (rnd(b) < 0.45) continue;

        put(b, if (rnd(b) < 0.5) .planter else .tamarisk, px, road_z1 + 1.2, spin(b));
    }

    for ([_]f32{ -60, 60 }) |cx| park_list.append(b.gpa, .{ .pos = vec(cx, height(cx, high_z), high_z), .yaw = half_pi }) catch {};
    for ([_]f32{ -56, 0, 56 }) |cx| park_list.append(b.gpa, .{ .pos = vec(cx, height(cx, -2.5), -2.5), .yaw = half_pi }) catch {};
}

const terrace_kinds = [_]K{ .terrace_a, .terrace_b, .terrace_c, .terrace_d, .terrace_b, .terrace_c, .terrace_a, .terrace_d, .terrace_c };

fn terraceRow(b: *Builder, x0: f32, x1: f32, z: f32, yaw: f32, seed: u32) void {
    var x = x0 + 2.25;
    var i: u32 = seed;
    const out: f32 = if (yaw > 1) -1 else 1;

    while (x < x1 - 2) : (x += 4.5) {
        i += 1;
        house(b, terrace_kinds[(i * 5 + seed) % terrace_kinds.len], x, z, yaw);

        if ((i * 7 + seed) % 5 < 3) {
            const az = z + out * 4.55;

            putAt(b, .awning, x, tr.height(x, z) + 2.3, az, yaw);
        }

        if ((i * 3 + seed) % 7 == 2) put(b, .stall, x, z + out * 5.8, yaw);
    }
}

const blocks_x = [_][2]f32{ .{ -edge + 3, -48 }, .{ 48, edge - 3 } };

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
            put(b, .tamarisk, x, z, spin(b));
        }
    }
}

fn front(b: *Builder) void {
    tiles(b, .sidewalk, -edge, edge, road_z1, road_z1 + 6, null);
    tiles(b, .sidewalk, -edge, edge, high_z - 10, high_z - 4, null);
    tiles(b, .sidewalk, -edge, edge, high_z + 4, high_z + 8, null);
    for (blocks_x, 0..) |s, n| {
        const seed: u32 = @intCast(n * 3);

        house(b, .corner, s[0] + 4.5, 14.5, pi);
        terraceRow(b, s[0] + 9, s[1] - 9, 14, pi, seed);
        house(b, if (n % 2 == 0) .tavern else .corner, s[1] - 4.5, 14.5, pi);

        house(b, .corner, s[0] + 4.5, 29.5, 0);
        terraceRow(b, s[0] + 9, s[1] - 9, 30, 0, seed + 1);
        house(b, .corner, s[1] - 4.5, 29.5, 0);

        house(b, if (n % 2 == 1) .tavern else .corner, s[0] + 4.5, 54.5, pi);
        terraceRow(b, s[0] + 9, s[1] - 9, 54, pi, seed + 2);

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
            put(b, .stall, x, zn, pi);
        } else if (roll < 0.5) {
            put(b, .stall, x, zs, 0);
        } else if (roll < 0.62) {
            put(b, .bin, x, zn, 0);
            put(b, .tree, x + 2, zn + 0.6, 0);
        }

        if (rnd(b) < 0.25) put(b, b.rng.pick(K, &.{ .planter, .bench, .bin }), x + 1, high_z + 5 * (if (rnd(b) < 0.5) @as(f32, 1) else -1), 0);
    }

    lootY(b, (x0 + x1) / 2, tr.height((x0 + x1) / 2, high_z), high_z);
    spawnAt(b, (x0 + x1) / 2, high_z - 2.5, half_pi);
}

fn square(b: *Builder) void {
    const cz: f32 = 44;

    house(b, .clock, 0, cz, 0);

    for ([_][2]f32{ .{ -14, -9 }, .{ 14, -9 }, .{ -14, 9 }, .{ 14, 9 }, .{ -30, 0 }, .{ 30, 0 } }) |o| put(b, .tree, o[0], cz + o[1], spin(b));

    for ([_][3]f32{ .{ -6, -6, 0.8 }, .{ 6, -6, -0.8 }, .{ -6, 6, 2.3 }, .{ 6, 6, -2.3 } }) |o| put(b, .bench, o[0], cz + o[1], o[2]);

    for ([_]f32{ -22, -10, 10, 22 }) |px| put(b, .planter, px, cz + 12, 0);

    for ([_][3]f32{ .{ -26, 36, 0 }, .{ -22, 36, 0 }, .{ -18, 36, 0 }, .{ 18, 36, 0 }, .{ 22, 36, 0 }, .{ 26, 36, 0 }, .{ -26, 50, pi }, .{ -20, 50, pi }, .{ 20, 50, pi }, .{ 26, 50, pi } }) |st| {
        put(b, .stall, st[0], st[1], st[2]);
        put(b, .fishcrate, st[0] + 1.2, st[1] + (if (st[2] > 1) @as(f32, -1.2) else 1.2), 0.3);
    }

    put(b, .phone, -20, cz - 10, 0);
    put(b, .phone, -18.6, cz - 10, 0);
    put(b, .stall, 20, cz - 10, pi);
    put(b, .bench, 24, cz + 4, half_pi);
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
    var z: f32 = 66;

    while (z < edge + 12) : (z += 4) {
        var x: f32 = -edge - 12;

        while (x < edge + 12) : (x += 4.5) {
            const px = x + b.rng.range(-1.8, 1.8);
            const pz = z + b.rng.range(-1.8, 1.8);

            if (taken(px, pz, 1.2) or (@abs(px) < 40 and pz < 70)) continue;

            const roll = rnd(b);
            const far = pz > edge;

            if (roll < (if (far) @as(f32, 0.34) else 0.14)) {
                put(b, if (rnd(b) < 0.6) .pine else .tree, px, pz, spin(b));
            } else if (roll < 0.42) {
                put(b, .shrub, px, pz, spin(b));
            }
        }
    }

    anchor_list.append(b.gpa, vec(-40, 34, 50)) catch {};
    anchor_list.append(b.gpa, vec(40, 34, 50)) catch {};
}

fn edges(b: *Builder) void {
    for ([_]f32{ -1, 1 }) |sd| {
        for ([_][2]f32{ .{ road_z0 - 1, road_z1 + 6 }, .{ high_z - 10, high_z + 8 } }) |r| {
            var z = r[0] + 2;

            while (z < r[1]) : (z += 4) {
                const x = sd * (edge + 1);
                const y = tr.height(x, z);

                putAt(b, .fence, x, y, z, half_pi);
                box(b, x - 0.1, y - 0.5, z - 2, x + 0.1, y + 1.8, z + 2);
            }

            put(b, .planter, sd * (edge - 1.5), (r[0] + r[1]) / 2, 0);
        }

        var z: f32 = shoreZ(sd * edge) + 4;

        while (z < wall_z - 2) : (z += 4) {
            put(b, .dunefence, sd * (edge + 2), z, half_pi);
        }

        z = road_z1 + 7;

        while (z < 66) : (z += 4.5) {
            if (@abs(z - (high_z - 1)) < 10) continue;

            put(b, if (rnd(b) < 0.5) .pine else .tamarisk, sd * (edge + 3 + b.rng.range(0, 6)), z + b.rng.range(-1.5, 1.5), spin(b));

            if (rnd(b) < 0.5) put(b, .shrub, sd * (edge + 1.5), z + b.rng.range(-1, 1), spin(b));
        }
    }

    for (streets_x) |sx| {
        var x = sx - 4;

        while (x < sx + 4) : (x += 4) {
            const y = tr.height(x + 2, street_end);

            putAt(b, .fence, x + 2, y, street_end, 0);
            box(b, x, y - 0.5, street_end - 0.1, x + 4, y + 1.8, street_end + 0.1);
        }
    }
}

fn shoreFoam(b: *Builder) void {
    var x: f32 = -edge - 12;

    while (x < edge + 12) : (x += 6) {
        const z = shoreZ(x);
        const slope = shoreZ(x + 1) - shoreZ(x - 1);

        b.putAt(of(.foam), vec(x, sea_y + 0.01, z - 1.2), std.math.atan2(-slope * 0.5, 1) + b.rng.range(-0.08, 0.08), b.rng.range(0.9, 1.1));

        if (rnd(b) < 0.6) b.putAt(of(.ripple), vec(x + b.rng.range(-2, 2), sea_y + 0.005, z - 6 - b.rng.range(0, 6)), b.rng.range(-0.1, 0.1), b.rng.range(0.8, 1.2));
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

    pier(b);
    seaWall(b);
    promenade(b);
    seaRoad(b);
    square(b);
    front(b);
    hillside(b);
    beach(b);
    beachLife(b);
    edges(b);
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
