const std = @import("std");
const api = @import("api.zig");
const k = @import("racing_kit.zig");

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
    .name = "Highway",
    .note = "Desert town inside a road circuit",
    .tint = .{ 214, 120, 72 },
    .half = 210,
    .play = 172,
    .facet = 2.0,
    .height = height,
    .ground = groundColor,
    .road = roadDist,
    .build = build,
    .spots = setSpots,
    .props = &k.table,
    .palette = .{
        .sun_dir = .{ 0.5, 0.62, 0.6 },
        .sun_tint = .{ 1.2, 1.02, 0.82 },
        .grade_tint = .{ 1.06, 1.0, 0.92 },
        .grade_sat = 1.16,
        .fog = 0.0028,
        .fog_color = .{ 0.88, 0.8, 0.7 },
        .amb_sky = .{ 0.94, 0.98, 1.12 },
        .amb_ground = .{ 0.94, 0.76, 0.56 },
        .shade_tint = .{ 0.9, 0.9, 1.06 },
        .zenith = .{ 0.1, 0.3, 0.62 },
    },
    .backdrop = .{ 200, 150, 104 },
    .floor_y = -4,
    .grip = 0.8,
    .tufts = 0.3,
};

const hx: f32 = 140;
const hz: f32 = 118;
const corner: f32 = 42;
const track_w: f32 = 7.5;
const street_w: f32 = 6;

fn trackSd(x: f32, z: f32) f32 {
    const qx = @abs(x) - (hx - corner);
    const qz = @abs(z) - (hz - corner);
    const ox = @max(qx, 0);
    const oz = @max(qz, 0);

    return @sqrt(ox * ox + oz * oz) + @min(@max(qx, qz), 0) - corner;
}

fn trackDist(x: f32, z: f32) f32 {
    return @abs(trackSd(x, z));
}

fn streetDist(x: f32, z: f32) f32 {
    var d: f32 = 1000;

    if (@abs(z) < hz) d = @min(d, @abs(x));

    if (@abs(x) < hx) d = @min(d, @abs(z));

    return d;
}

fn roadDist(x: f32, z: f32) f32 {
    return @min(@max(trackDist(x, z) - track_w, 0), @max(streetDist(x, z) - street_w, 0));
}

fn height(x: f32, z: f32) f32 {
    const sd = trackSd(x, z);
    const outside = tr.smooth(12, 40, sd);
    const dunes = (tr.fbm(x * 0.02 + 5, z * 0.02 - 3) - 0.35) * 7 * outside;
    const edge = tr.smooth(150, 200, @max(@abs(x), @abs(z))) * 10;
    const town = (tr.fbm(x * 0.01, z * 0.01) - 0.5) * 0.8 * (1 - outside);

    return @max(dunes, 0) + edge + town;
}

fn groundColor(x: f32, z: f32) api.Rgb {
    const light = api.light(x, z);
    const fleck = tr.fbm(x * 0.3 - 7, z * 0.3 + 5);
    const ao = contact(x, z);
    const td = trackDist(x, z);
    const sd = streetDist(x, z);

    if (td < track_w) {
        const worn = 1 - tr.smooth(1, 4, td);
        const rubber = tr.smooth(0.55, 0.7, tr.fbm(x * 0.06, z * 0.06)) * 0.3;
        const c = mix3(.{ 72, 72, 76 }, .{ 58, 58, 62 }, worn * 0.6 + rubber);

        return shade(c, light * ao);
    }

    if (td < track_w + 2.5) return shade(.{ 156, 140, 118 }, light * ao);

    if (sd < street_w) return shade(mix3(.{ 86, 86, 90 }, .{ 96, 94, 96 }, fleck), light * ao);

    if (lotAt(x, z)) return shade(mix3(.{ 104, 102, 104 }, .{ 92, 90, 94 }, fleck), light * ao);

    const sdv = trackSd(x, z);

    if (sdv < -track_w - 2) {
        const dust = mix3(.{ 206, 168, 120 }, .{ 190, 150, 106 }, fleck);
        const weed = tr.smooth(0.55, 0.7, tr.fbm(x * 0.05 + 2, z * 0.05));
        const zone = zoneTone(x, z, fleck);

        return shade(mix3(mix3(dust, zone, 0.75), .{ 150, 140, 96 }, weed * 0.45), light * ao);
    }

    const sand = mix3(.{ 222, 170, 112 }, .{ 200, 140, 92 }, tr.fbm(x * 0.04 + 1, z * 0.04 - 6));
    const scrub = tr.smooth(0.55, 0.68, tr.fbm(x * 0.08 + 9, z * 0.08));

    return shade(mix3(mix3(sand, .{ 232, 196, 150 }, std.math.clamp(fleck - 0.5, 0, 0.4)), .{ 150, 132, 88 }, scrub * 0.6), light * ao);
}

const max_lots = 120;

fn hash2(i: i32, j: i32) f32 {
    var h: u32 = @bitCast(i *% 374761393 +% j *% 668265263);

    h = (h ^ (h >> 13)) *% 1274126177;
    h ^= h >> 16;

    return @as(f32, @floatFromInt(h & 0xffff)) / 65535.0;
}

fn zoneTone(x: f32, z: f32, fleck: f32) [3]f32 {
    const wx = x + (tr.fbm(x * 0.05 + 3, z * 0.05) - 0.5) * 16;
    const wz = z + (tr.fbm(x * 0.05 - 9, z * 0.05 + 4) - 0.5) * 16;
    const cell: f32 = 26;
    const pick = hash2(@intFromFloat(@floor(wx / cell)), @intFromFloat(@floor(wz / cell)));
    const speck = tr.fbm(x * 1.9 + 5, z * 1.9 - 3);
    const gravel = mix3(mix3(.{ 160, 146, 126 }, .{ 144, 132, 114 }, fleck), .{ 192, 180, 160 }, tr.smooth(0.62, 0.72, speck));

    if (pick < 0.35) return mix3(.{ 214, 176, 126 }, .{ 198, 160, 114 }, fleck);

    if (pick < 0.6) return mix3(.{ 178, 136, 96 }, .{ 164, 124, 86 }, fleck);

    if (pick < 0.82) return gravel;

    return mix3(.{ 226, 196, 150 }, .{ 212, 182, 138 }, fleck);
}
var lots: [max_lots][4]f32 = undefined;
var lot_n: usize = 0;

fn addLot(x0: f32, z0: f32, x1: f32, z1: f32) void {
    if (lot_n >= max_lots) return;

    lots[lot_n] = .{ x0, z0, x1, z1 };
    lot_n += 1;
}

fn lotAt(x: f32, z: f32) bool {
    for (lots[0..lot_n]) |r| {
        if (x > r[0] and x < r[2] and z > r[1] and z < r[3]) return true;
    }

    return false;
}

const max_shadow = 400;
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

    return 0.7 + 0.3 * tr.smooth(0, 2.4, best);
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

var spawn_list: std.ArrayList(Vec3) = .empty;
var spawn_yaw: std.ArrayList(f32) = .empty;
var anchor_list: std.ArrayList(Vec3) = .empty;
var park_list: std.ArrayList(wd.Spot) = .empty;
var loot_list: std.ArrayList(Vec3) = .empty;

fn spawnAt(b: *Builder, x: f32, z: f32, yaw: f32) void {
    spawn_list.append(b.gpa, vec(x, tr.height(x, z) + 0.1, z)) catch {};
    spawn_yaw.append(b.gpa, yaw) catch {};
}

fn loot(b: *Builder, x: f32, z: f32) void {
    loot_list.append(b.gpa, vec(x, tr.height(x, z) + 0.1, z)) catch {};
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

fn car(b: *Builder, x: f32, z: f32, yaw: f32) void {
    const roll = rnd(b);

    if (roll < 0.22) {
        put(b, .tyres, x - 0.5, z, 0);
        put(b, .tyres, x + 0.4, z + 0.2, 0.6);
        putAt(b, .tyres, x, tr.height(x, z) + 0.96, z, 0.3);
    } else if (roll < 0.38) {
        put(b, .drum, x, z - 0.4, 0);
        put(b, .drum, x + 0.1, z + 0.4, 0.5);
        put(b, .drum, x - 0.6, z, 1.1);
    } else if (roll < 0.52) {
        put(b, .rail, x, z, yaw + half_pi);
        put(b, .cone, x + 1, z + 1.2, 0);
    } else if (roll < 0.64) {
        put(b, .planter, x, z, 0);
        put(b, .planter, x, z + 1.2, 0);
    } else if (roll < 0.74) {
        put(b, .picnic, x, z, yaw);
    } else if (roll < 0.84) {
        put(b, .ice, x, z, yaw);
        put(b, .soda, x + 1, z, yaw);
    } else {
        put(b, .cone, x, z, 0);
        put(b, .cone, x + 0.7, z + 0.4, 0);
        put(b, .cone, x - 0.6, z + 0.6, 0);
    }

    claimRect(x - 2, z - 2, x + 2, z + 2);
}

fn lotItem(b: *Builder, x: f32, z: f32, yaw: f32) void {
    if (rnd(b) < 0.45) {
        car(b, x, z, yaw);

        return;
    }

    miniModule(b, x, z);
    claimRect(x - 3, z - 3, x + 3, z + 3);
}

fn lot(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32, along_x: bool, fill: f32) void {
    addLot(x0, z0, x1, z1);

    if (along_x) {
        var x = x0 + 1.6;

        while (x < x1 - 1.5) : (x += 6.4) {
            for ([_]f32{ z0 + 3, z1 - 3 }) |z| {
                if (rnd(b) < fill + 0.35 and !taken(x, z, 0.5)) lotItem(b, x, z, if (z < (z0 + z1) / 2) pi else 0);
            }
        }
    } else {
        var z = z0 + 1.6;

        while (z < z1 - 1.5) : (z += 6.4) {
            for ([_]f32{ x0 + 3, x1 - 3 }) |x| {
                if (rnd(b) < fill + 0.35 and !taken(x, z, 0.5)) lotItem(b, x, z, if (x < (x0 + x1) / 2) -half_pi else half_pi);
            }
        }
    }
}

fn trackPoint(t: f32) [3]f32 {
    const sx = hx - corner;
    const sz = hz - corner;
    const straight_x = 2 * sx;
    const straight_z = 2 * sz;
    const arc = corner * half_pi;
    const total = 2 * straight_x + 2 * straight_z + 4 * arc;
    var d = @mod(t, total);

    if (d < straight_x) return .{ -sx + d, -hz, 0 };

    d -= straight_x;

    if (d < arc) {
        const a = -half_pi + d / corner;

        return .{ sx + @cos(a) * corner, -sz + @sin(a) * corner, d / corner };
    }

    d -= arc;

    if (d < straight_z) return .{ hx, -sz + d, half_pi };

    d -= straight_z;

    if (d < arc) {
        const a = d / corner;

        return .{ sx + @cos(a) * corner, sz + @sin(a) * corner, half_pi + d / corner };
    }

    d -= arc;

    if (d < straight_x) return .{ sx - d, hz, pi };

    d -= straight_x;

    if (d < arc) {
        const a = half_pi + d / corner;

        return .{ -sx + @cos(a) * corner, sz + @sin(a) * corner, pi + d / corner };
    }

    d -= arc;

    if (d < straight_z) return .{ -hx, sz - d, pi + half_pi };

    d -= straight_z;

    const a = pi + d / corner;

    return .{ -sx + @cos(a) * corner, -sz + @sin(a) * corner, pi + half_pi + d / corner };
}

fn trackLength() f32 {
    return 4 * (hx - corner) + 4 * (hz - corner) + 4 * corner * half_pi;
}

fn circuit(b: *Builder) void {
    const total = trackLength();
    var t: f32 = 0;
    var n: u32 = 0;

    while (t < total) : (t += 4) {
        n += 1;

        const p = trackPoint(t);
        const yaw = -p[2];
        const nx = @sin(p[2]);
        const nz = -@cos(p[2]);
        const bend = @abs(@mod(p[2] + 0.01, half_pi)) > 0.02;
        const ox = p[0] - nx * (track_w + 0.6);
        const oz = p[1] - nz * (track_w + 0.6);
        const ix = p[0] + nx * (track_w + 0.6);
        const iz = p[1] + nz * (track_w + 0.6);

        if (bend) {
            b.putAt(of(.kerb), vec(ix, tr.height(ix, iz) + 0.02, iz), yaw, 1);
            b.putAt(of(.kerb), vec(ox, tr.height(ox, oz) + 0.02, oz), yaw, 1);

            if (n % 2 == 0) {
                const wx = p[0] - nx * (track_w + 4.5);
                const wz = p[1] - nz * (track_w + 4.5);

                for ([_]f32{ -1.2, 0, 1.2 }) |o| {
                    const tx = wx + @cos(p[2]) * o;
                    const tz = wz + @sin(p[2]) * o;

                    putAt(b, .tyres, tx, tr.height(tx, tz), tz, 0);
                    putAt(b, .tyres, tx, tr.height(tx, tz) + 0.96, tz, 0.5);
                }

                claimRect(wx - 2, wz - 2, wx + 2, wz + 2);
            }
        } else {
            const gx = p[0] - nx * (track_w + 3);
            const gz = p[1] - nz * (track_w + 3);

            if (!(@abs(p[0]) < 70 and p[1] < 0)) {
                b.putAt(of(.rail), vec(gx, tr.height(gx, gz), gz), yaw, 1);
                box(b, gx - @abs(@cos(p[2])) * 2 - 0.2, tr.height(gx, gz) - 0.5, gz - @abs(@sin(p[2])) * 2 - 0.2, gx + @abs(@cos(p[2])) * 2 + 0.2, tr.height(gx, gz) + 0.9, gz + @abs(@sin(p[2])) * 2 + 0.2);
            }

            if (n % 5 == 0) {
                const lx = p[0] + nx * (track_w + 2);
                const lz = p[1] + nz * (track_w + 2);

                if (!taken(lx, lz, 1)) putAt(b, .lamp, lx, tr.height(lx, lz), lz, yaw + pi);
            }
        }

        if (n % 3 == 0) {
            const mx = p[0];
            const mz = p[1];

            if (streetDist(mx, mz) > street_w + 1) b.putAt(of(.line), vec(mx, tr.height(mx, mz) + 0.01, mz), yaw, 1);
        }

        claimRect(p[0] - track_w, p[1] - track_w, p[0] + track_w, p[1] + track_w);
    }

    putAt(b, .start, 0, tr.height(0, -hz) + 0.015, -hz, half_pi);

    for ([_]f32{ -8.5, 8.5 }) |o| putAt(b, .flag, 0, 0, -hz + o, 0);

    for ([_][2]f32{ .{ -12, -3.5 }, .{ -18, 3.5 }, .{ -24, -3.5 }, .{ -30, 3.5 }, .{ -36, -3.5 }, .{ -42, 3.5 } }) |g| {
        park_list.append(b.gpa, .{ .pos = vec(g[0], tr.height(g[0], -hz + g[1]), -hz + g[1]), .yaw = half_pi }) catch {};
    }

    for ([_][2]f32{ .{ 60, 0 }, .{ -60, 0 }, .{ 0, 60 }, .{ 0, -60 } }) |g| park_list.append(b.gpa, .{ .pos = vec(g[0], tr.height(g[0], g[1]), g[1]), .yaw = if (g[0] == 0) 0 else half_pi }) catch {};
}

fn grandstand(b: *Builder) void {
    const z: f32 = -hz - track_w - 9;
    var x: f32 = -48;

    while (x <= 48) : (x += 1) {
        if (@abs(x) < 3) continue;

        putAt(b, .stand, x, tr.height(x, z), z, 0);
        putAt(b, .roof, x, tr.height(x, z - 1), z - 1, 0);
    }

    var s: f32 = 0;

    while (s < 7) : (s += 1) {
        const step_z = z + 3.5 - s;
        const top = tr.height(0, z) + (s + 1) * 0.62;

        box(b, -48.5, top - 0.62, step_z - 1, -2.5, top, step_z);
        box(b, 2.5, top - 0.62, step_z - 1, 48.5, top, step_z);
    }

    box(b, -48.5, 0, z - 4.5, 48.5, 7.3, z - 3.6);

    for ([_]f32{ -30, -10, 10, 30 }) |tx| {
        house(b, .ticket, tx, z - 8, pi);
        put(b, .soda, tx + 2.4, z - 8, pi);
    }

    put(b, .pylon, -56, z + 2, 0);
    put(b, .pylon, 56, z + 2, 0);
    put(b, .billboard, -74, z, 0.1);
    put(b, .billboard, 74, z, -0.1);
    claimRect(-80, z - 12, 80, z + 5);
    loot(b, 0, z);
    loot(b, -40, z - 6);
    loot(b, 40, z - 6);
    spawnAt(b, -60, z - 6, 0);
    spawnAt(b, 60, z - 6, 0);
    anchor_list.append(b.gpa, vec(0, 22, z)) catch {};
}

fn mainStreet(b: *Builder) void {
    var z: f32 = -hz + track_w + 4;

    while (z < hz - track_w - 4) : (z += 4) {
        for ([_]f32{ -1, 1 }) |sd| {
            const x = sd * (street_w + 2);

            if (@abs(z) < street_w + 4) continue;

            putAt(b, .sidewalk, x, tr.height(x, z) + 0.02, z, 0);
            b.putAt(of(.curb), vec(sd * street_w, tr.height(sd * street_w, z), z), half_pi, 1);
        }

        if (@abs(z) > street_w + 4) b.putAt(of(.line), vec(0, tr.height(0, z) + 0.01, z), half_pi, 1);
    }

    var x: f32 = -hx + track_w + 4;

    while (x < hx - track_w - 4) : (x += 4) {
        for ([_]f32{ -1, 1 }) |sd| {
            const zz = sd * (street_w + 2);

            if (@abs(x) < street_w + 4) continue;

            putAt(b, .sidewalk, x, tr.height(x, zz) + 0.02, zz, 0);
            b.putAt(of(.curb), vec(x, tr.height(x, sd * street_w), sd * street_w), 0, 1);
        }

        if (@abs(x) > street_w + 4) b.putAt(of(.line), vec(x, tr.height(x, 0) + 0.01, 0), 0, 1);
    }

    for ([_][2]f32{ .{ -8.5, -8.5 }, .{ 8.5, 8.5 }, .{ -8.5, 8.5 }, .{ 8.5, -8.5 } }) |c| put(b, .light, c[0], c[1], std.math.atan2(-c[0], -c[1]));

    claimRect(-street_w - 4, -hz, street_w + 4, hz);
    claimRect(-hx, -street_w - 4, hx, street_w + 4);

    var p: f32 = -100;

    while (p < 100) : (p += 5.5) {
        if (@abs(p) < 14) continue;

        for ([_]f32{ -1, 1 }) |sd| {
            if (rnd(b) < 0.25) car(b, sd * (street_w - 1.6), p, if (sd < 0) 0 else pi);

            if (rnd(b) < 0.2) car(b, p * 1.3, sd * (street_w - 1.6), if (sd < 0) half_pi else -half_pi);
        }
    }

    var lz: f32 = -96;

    while (lz < 100) : (lz += 16) {
        if (@abs(lz) < 12) continue;

        for ([_]f32{ -1, 1 }) |sd| {
            const lx = sd * (street_w + 3.4);

            put(b, .lamp, lx, lz, if (sd < 0) -half_pi else half_pi);
            put(b, .lamp, lz * 1.3, sd * (street_w + 3.4), if (sd < 0) pi else 0);
        }
    }
}

fn quarterNW(b: *Builder) void {
    house(b, .diner, -34, 20, pi);
    put(b, .dsign, -22, 13.2, pi);
    lot(b, -60, 13, -42, 45, false, 0.35);
    park_list.append(b.gpa, .{ .pos = vec(-51, tr.height(-51, 30), 30), .yaw = 0 }) catch {};
    house(b, .gifts, -14, 22, -half_pi);
    house(b, .vending, -14, 32, -half_pi);

    for ([_][2]f32{ .{ -30, 32 }, .{ -24, 32 }, .{ -36, 32 } }) |pp| put(b, .picnic, pp[0], pp[1], 0.2);

    put(b, .phone, -16, 15, pi);
    put(b, .soda, -20, 28, pi);
    put(b, .ice, -27, 28.5, pi);
    house(b, .ranch, -30, 60, pi);
    house(b, .ranch, -60, 64, pi);
    house(b, .ranch, -90, 60, pi);
    house(b, .shops, -96, 24, pi);
    lot(b, -86, 34, -70, 48, false, 0.6);

    for ([_][2]f32{ .{ -40, 76 }, .{ -76, 80 }, .{ -100, 82 }, .{ -20, 84 } }) |t| put(b, .joshua, t[0], t[1], spin(b));

    put(b, .tower, -86, 92, 0);
    box(b, -89, 0, 89, -83, 20, 95);
    claimRect(-90, 88, -82, 96);
    loot(b, -30, 26);
    loot(b, -50, 30);
    loot(b, -60, 74);
    spawnAt(b, -44, 54, pi);
    spawnAt(b, -100, 46, half_pi);
    anchor_list.append(b.gpa, vec(-50, 20, 40)) catch {};
}

fn quarterNE(b: *Builder) void {
    house(b, .canopy, 30, 26, 0);

    for ([_]f32{ 26, 34 }) |px| {
        for ([_]f32{ 24, 28 }) |pz| put(b, .pump, px, pz, 0);
    }

    put(b, .pylon, 14, 16, 0);
    house(b, .repair, 58, 28, pi);
    house(b, .garage, 78, 26, pi);
    house(b, .vending, 44, 22, pi);
    put(b, .lift, 62, 16, half_pi);
    put(b, .cans, 47, 16, 0);
    put(b, .tyres, 50, 15, 0);
    put(b, .tyres, 50.8, 15.6, 0.4);
    put(b, .drum, 70, 18, 0);
    put(b, .drum, 70.7, 18.4, 0);
    lot(b, 90, 14, 118, 44, true, 0.6);
    put(b, .tower, 90, 84, 0);
    box(b, 87, 0, 81, 93, 20, 87);
    claimRect(86, 80, 94, 88);
    house(b, .ranch, 30, 66, pi);
    house(b, .ranch, 60, 70, pi);
    house(b, .corner, 96, 62, pi);
    lot(b, 20, 80, 70, 96, true, 0.5);

    for ([_][2]f32{ .{ 46, 86 }, .{ 110, 92 }, .{ 20, 56 } }) |t| put(b, .joshua, t[0], t[1], spin(b));

    loot(b, 30, 30);
    loot(b, 58, 18);
    loot(b, 100, 30);
    spawnAt(b, 44, 50, pi);
    spawnAt(b, 104, 72, -half_pi);
    anchor_list.append(b.gpa, vec(50, 20, 40)) catch {};
}

fn quarterSW(b: *Builder) void {
    house(b, .rooms, -40, -24, 0);
    house(b, .rooms, -40, -64, pi);
    house(b, .motel, -18, -44, -half_pi);
    lot(b, -56, -54, -22, -34, true, 0.65);
    put(b, .pylon, -14, -30, 0);
    put(b, .soda, -28, -30, 0);
    put(b, .ice, -54, -30, 0);
    park_list.append(b.gpa, .{ .pos = vec(-40, tr.height(-40, -44), -44), .yaw = half_pi }) catch {};
    house(b, .shops, -92, -24, 0);
    house(b, .corner, -96, -60, half_pi);
    put(b, .billboard, -80, -84, 0.2);

    for ([_][2]f32{ .{ -70, -80 }, .{ -112, -40 }, .{ -30, -88 } }) |t| put(b, .joshua, t[0], t[1], spin(b));

    loot(b, -40, -44);
    loot(b, -18, -30);
    loot(b, -92, -40);
    spawnAt(b, -70, -44, half_pi);
    spawnAt(b, -30, -86, 0);
    anchor_list.append(b.gpa, vec(-50, 20, -50)) catch {};
}

fn quarterSE(b: *Builder) void {
    var x: f32 = 22;

    while (x < 106) : (x += 13) house(b, if (x > 70 and x < 76) .corner else .shops, x, -20, 0);

    lot(b, 20, -48, 104, -32, true, 0.6);
    house(b, .repair, 34, -66, 0);
    house(b, .gifts, 60, -60, 0);
    house(b, .vending, 70, -60, 0);
    put(b, .billboard, 92, -68, 0);
    park_list.append(b.gpa, .{ .pos = vec(92, tr.height(92, -80), -80), .yaw = half_pi }) catch {};

    for ([_][2]f32{ .{ 110, -50 }, .{ 50, -84 }, .{ 20, -80 } }) |t| put(b, .joshua, t[0], t[1], spin(b));

    loot(b, 60, -40);
    loot(b, 34, -76);
    loot(b, 92, -82);
    spawnAt(b, 48, -54, 0);
    spawnAt(b, 104, -84, -half_pi);
    anchor_list.append(b.gpa, vec(50, 20, -50)) catch {};
}

const fronts = [_]K{ .shops, .corner, .garage, .ranch, .repair, .gifts, .shops, .vending, .corner, .ranch };

fn frontage(b: *Builder) void {
    var i: usize = 0;
    var t: f32 = -100;

    while (t < 104) : (t += 13) {
        if (@abs(t) < 12) continue;

        for ([_]f32{ -1, 1 }) |sd| {
            const e = fronts[i % fronts.len];
            const bl = bld(e);
            const off = street_w + 4.5 + bl.d / 2;

            i += 1;

            const mx = sd * off;

            if (!taken(mx, t, 3)) house(b, e, mx, t, if (sd > 0) -half_pi else half_pi);

            const e2 = fronts[(i * 3) % fronts.len];
            const bl2 = bld(e2);
            const cz = sd * (street_w + 4.5 + bl2.d / 2);
            const cx = t * 1.25;

            if (!taken(cx, cz, 3)) house(b, e2, cx, cz, if (sd > 0) pi else 0);
        }
    }
}

fn infield(b: *Builder) void {
    var z: f32 = -hz + 4;

    while (z < hz - 4) : (z += 4.5) {
        var x: f32 = -hx + 4;

        while (x < hx - 4) : (x += 4.5) {
            const px = x + b.rng.range(-1.8, 1.8);
            const pz = z + b.rng.range(-1.8, 1.8);

            if (trackSd(px, pz) > -track_w - 3 or taken(px, pz, 1) or lotAt(px, pz)) continue;

            const roll = rnd(b);

            if (roll < 0.12) put(b, .creosote, px, pz, spin(b)) else if (roll < 0.16) put(b, .weed, px, pz, spin(b)) else if (roll < 0.2) car(b, px, pz, spin(b)) else if (roll < 0.23) put(b, .joshua, px, pz, spin(b)) else if (roll < 0.25) putS(b, .outcrop, px, pz, spin(b), 0.8);
        }
    }
}

fn desert(b: *Builder) void {
    var z: f32 = -210;

    while (z < 210) : (z += 4) {
        var x: f32 = -210;

        while (x < 210) : (x += 4) {
            const px = x + b.rng.range(-1.8, 1.8);
            const pz = z + b.rng.range(-1.8, 1.8);

            if (trackSd(px, pz) < track_w + 4 or taken(px, pz, 1)) continue;

            const roll = rnd(b);

            if (roll < 0.1) {
                put(b, .creosote, px, pz, spin(b));
            } else if (roll < 0.14) {
                put(b, .saguaro, px, pz, spin(b));
            } else if (roll < 0.17) {
                put(b, .joshua, px, pz, spin(b));
            } else if (roll < 0.2) {
                putS(b, .outcrop, px, pz, spin(b), b.rng.range(0.6, 1.4));
            } else if (roll < 0.23) {
                put(b, .weed, px, pz, spin(b));
            } else if (roll < 0.25) {
                b.put(.kd_cactus_0, px, pz, spin(b), 1);
            } else if (roll < 0.27) {
                b.put(.kd_rock_2, px, pz, spin(b), 1);
            }
        }
    }

    for ([_][3]f32{ .{ -150, 150, 0.4 }, .{ 0, 186, 0.0 }, .{ 160, 160, 2.2 }, .{ 196, 0, 1.6 }, .{ 170, -170, 0.9 }, .{ -10, -196, 3.0 }, .{ -170, -160, 2.6 }, .{ -196, 10, 1.2 }, .{ 90, 196, 0.3 }, .{ -90, -196, 2.9 }, .{ 196, 100, 1.4 }, .{ -196, -90, 1.9 } }) |m| {
        putAt(b, .mesa, m[0], tr.height(m[0], m[1]) - 2, m[1], m[2]);
    }

    for ([_][3]f32{ .{ 0, 150, pi }, .{ -160, 60, half_pi }, .{ 160, -40, -half_pi } }) |s| {
        put(b, .billboard, s[0], s[1], s[2]);
        put(b, .shield, s[0] + 8, s[1] + 2, s[2]);
        put(b, .mileage, s[0] - 8, s[1] + 2, s[2]);
    }

    house(b, .gifts, -40, 146, pi);
    house(b, .vending, -30, 146, pi);
    put(b, .picnic, 30, 146, 0.2);
    put(b, .picnic, 36, 147, 0.5);
    put(b, .pylon, 46, 140, 0);
    park_list.append(b.gpa, .{ .pos = vec(0, tr.height(0, 142), 142), .yaw = half_pi }) catch {};
    loot(b, -40, 152);
    loot(b, 40, 150);
    loot(b, -156, 0);
    loot(b, 156, 0);
    spawnAt(b, -20, 156, pi);
    spawnAt(b, 20, 156, pi);
    spawnAt(b, -158, 40, half_pi);
    spawnAt(b, 158, -40, -half_pi);
}

fn rp(yaw: f32, x: f32, z: f32) [2]f32 {
    const c = @cos(yaw);
    const s = @sin(yaw);

    return .{ x * c + z * s, -x * s + z * c };
}

fn lp(b: *Builder, e: K, cx: f32, cz: f32, yaw: f32, lx: f32, lz: f32, ly: f32, lyaw: f32) void {
    const o = rp(yaw, lx, lz);
    const x = cx + o[0];
    const z = cz + o[1];

    b.putAt(of(e), vec(x, tr.height(x, z) + ly, z), yaw + lyaw, 1);
}

fn lsolid(b: *Builder, cx: f32, cz: f32, yaw: f32, l: [6]f32) void {
    const r = wd.rotBox(cx, cz, yaw, l[0], l[1], l[2], l[3]);
    const y = tr.height(cx, cz);

    box(b, r[0], y + l[4], r[1], r[2], y + l[5], r[3]);
}

fn padLot(cx: f32, cz: f32, yaw: f32, hw: f32, hd: f32) void {
    const r = wd.rotBox(cx, cz, yaw, -hw, -hd, hw, hd);

    addLot(r[0], r[1], r[2], r[3]);
}

const boxes = [_]K{ .box_red, .box_blue, .box_white };

fn paddock(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    padLot(cx, cz, yaw, 8, 7);
    lp(b, .gazebo, cx, cz, yaw, -4, -2, 0, 0);
    lp(b, .gazebo, cx, cz, yaw, 0.4, -2, 0, 0);
    lp(b, if (rnd(b) < 0.5) .box_red else .box_blue, cx, cz, yaw, -1.5, 4.2, 0, 0);
    lsolid(b, cx, cz, yaw, .{ -4.6, 2.9, 1.6, 5.5, -0.5, 2.6 });

    for ([_]f32{ 4.5, 5.4, 6.3 }) |tx| {
        lp(b, .tyres, cx, cz, yaw, tx, -4, 0, 0);
        lp(b, .tyres, cx, cz, yaw, tx, -4, 0.96, 0.4);
    }

    lp(b, .drum, cx, cz, yaw, 5, 0, 0, 0);
    lp(b, .drum, cx, cz, yaw, 5.7, 0.5, 0, 0.6);
    lp(b, .ibc, cx, cz, yaw, 5.5, 2.4, 0, 0.1);
    lp(b, .wrap, cx, cz, yaw, 5.5, 4, 0, 0);
    lp(b, .redflag, cx, cz, yaw, -7, -5.5, 0, 0);
    lp(b, .cans, cx, cz, yaw, -6.5, 1, 0, half_pi);
    lp(b, .lift, cx, cz, yaw, -2, -6.2, 0, 0);
}

fn containerYard(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    padLot(cx, cz, yaw, 8, 6);

    var i: usize = 0;

    for ([_]f32{ -2.8, 0, 2.8 }) |lz| {
        const e = boxes[(i + @as(usize, @intFromFloat(rnd(b) * 2.99))) % 3];

        lp(b, e, cx, cz, yaw, -1.5, lz, 0, 0);

        if (i != 2) lp(b, boxes[(i + 1) % 3], cx, cz, yaw, -1.5, lz, 2.64, rnd(b) * 0.06 - 0.03);

        i += 1;
    }

    lsolid(b, cx, cz, yaw, .{ -4.6, -4.1, 1.6, 4.1, -0.5, 5.3 });

    for ([_]f32{ -3, -1.8, -0.6 }) |lz| lp(b, .wrap, cx, cz, yaw, 4, lz, 0, 0);

    lp(b, .wrap, cx, cz, yaw, 4, -2.4, 1.21, 0.05);
    lp(b, .ibc, cx, cz, yaw, 4, 1.5, 0, 0);
    lp(b, .ibc, cx, cz, yaw, 4, 2.8, 0, 0.1);
    lp(b, .drum, cx, cz, yaw, 6, 4, 0, 0);
}

fn miniStand(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    var x: f32 = -6;

    while (x <= 6) : (x += 1) {
        lp(b, .stand, cx, cz, yaw, x, 0, 0, half_pi);
        lp(b, .roof, cx, cz, yaw, x, -1, 0, half_pi);
    }

    var st: f32 = 0;

    while (st < 7) : (st += 1) lsolid(b, cx, cz, yaw, .{ -6.5, 2.5 - st, 6.5, 3.5 - st, 0, (st + 1) * 0.62 });

    lsolid(b, cx, cz, yaw, .{ -6.5, -4.5, 6.5, -3.6, 0, 7.3 });
    lp(b, .redflag, cx, cz, yaw, -8, 3, 0, 0);
    lp(b, .redflag, cx, cz, yaw, 8, 3, 0, 0);

    for ([_]f32{ -5, -3, -1, 1, 3, 5 }) |fx| lp(b, .fence, cx, cz, yaw, fx, 5.2, 0, 0);

    lp(b, .snack, cx, cz, yaw, 0, -7, 0, pi);
}

fn chicane(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    padLot(cx, cz, yaw, 9, 7);

    for ([_][3]f32{ .{ -6, -4, 0 }, .{ -2, -4, 0 }, .{ 2, 0, 0 }, .{ 6, 0, 0 }, .{ -6, 4, 0 }, .{ -2, 4, 0 } }) |j| lp(b, .jersey, cx, cz, yaw, j[0], j[1], 0, j[2]);

    lp(b, .tyrewall, cx, cz, yaw, 7.5, -4.5, 0, half_pi);
    lp(b, .tyrewall, cx, cz, yaw, -7.5, 0, 0, half_pi);

    for ([_][2]f32{ .{ 0, -2 }, .{ 3, -2 }, .{ -4, 2 }, .{ 1, 2.5 }, .{ 5, 4 } }) |c| lp(b, .cone, cx, cz, yaw, c[0], c[1], 0, 0);

    lp(b, .camtower, cx, cz, yaw, 7.5, 5.5, 0, 0);
}

fn fanZone(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    padLot(cx, cz, yaw, 7, 6);
    lp(b, .shade, cx, cz, yaw, 0, 0, 0, 0);

    for ([_][2]f32{ .{ -2, -1.5 }, .{ 2, -1.5 }, .{ -2, 1.8 }, .{ 2, 1.8 } }) |p| lp(b, .picnic, cx, cz, yaw, p[0], p[1], 0, 0);

    lp(b, .snack, cx, cz, yaw, 0, -5.6, 0, 0);
    lp(b, .soda, cx, cz, yaw, 5.5, -4, 0, -half_pi);
    lp(b, .ice, cx, cz, yaw, 5.5, -2.6, 0, 0);
    lp(b, .planter, cx, cz, yaw, -6, 4.5, 0, 0);
    lp(b, .planter, cx, cz, yaw, 6, 4.5, 0, 0);
    lp(b, .redflag, cx, cz, yaw, -6, -5, 0, 0);
}

fn scrubPatch(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    putS(b, .outcrop, cx, cz, spin(b), 1.2);
    lp(b, .joshua, cx, cz, yaw, 5, 3, 0, spin(b));
    lp(b, .joshua, cx, cz, yaw, -5, -4, 0, spin(b));
    lp(b, .saguaro, cx, cz, yaw, 4, -5, 0, spin(b));

    for ([_][2]f32{ .{ -3, 4 }, .{ 6, -1 }, .{ -6, 0 }, .{ 1, 6 }, .{ 2, -6 } }) |c| lp(b, .creosote, cx, cz, yaw, c[0], c[1], 0, spin(b));

    lp(b, .speed, cx, cz, yaw, -6, 6, 0, 0);
}

fn module(b: *Builder, x: f32, z: f32) void {
    const yaw = @as(f32, @floatFromInt(@as(u32, @intFromFloat(rnd(b) * 3.99)))) * half_pi;
    const pick = rnd(b);

    if (pick < 0.24) paddock(b, x, z, yaw) else if (pick < 0.44) containerYard(b, x, z, yaw) else if (pick < 0.56) miniStand(b, x, z, yaw) else if (pick < 0.7) chicane(b, x, z, yaw) else if (pick < 0.84) fanZone(b, x, z, yaw) else scrubPatch(b, x, z, yaw);
}

fn fillInfield(b: *Builder) void {
    var z: f32 = -hz + 12;

    while (z < hz - 10) : (z += 3) {
        var x: f32 = -hx + 12;

        while (x < hx - 10) : (x += 3) {
            if (trackSd(x, z) > -track_w - 12 or taken(x, z, 9) or lotAt(x, z) or streetDist(x, z) < street_w + 10) continue;

            module(b, x, z);
            claimRect(x - 9, z - 9, x + 9, z + 9);
        }
    }
}

fn pitLane(b: *Builder) void {
    const wall_z: f32 = -hz + track_w + 1.4;
    const gz: f32 = -hz + track_w + 13;
    var x: f32 = -118;

    while (x < 118) : (x += 4) {
        if (@abs(x) < 10) continue;

        putAt(b, .jersey, x, tr.height(x, wall_z), wall_z, 0);
        box(b, x - 2, tr.height(x, wall_z) - 0.5, wall_z - 0.35, x + 2, tr.height(x, wall_z) + 0.85, wall_z + 0.35);

        if (@mod(@as(i32, @intFromFloat(x + 200)), 24) == 2) putAt(b, .redflag, x, tr.height(x, wall_z + 1), wall_z + 1, 0);
    }

    addLot(-120, wall_z + 0.5, -10, gz - 4);
    addLot(10, wall_z + 0.5, 120, gz - 4);

    var gx: f32 = -114;

    while (gx < 116) : (gx += 9) {
        if (@abs(gx) < 14 or taken(gx, gz, 1)) continue;

        house(b, if (@mod(@as(i32, @intFromFloat(gx + 300)), 4) == 0) .repair else .garage, gx, gz, pi);

        const fz = gz - 5.4;
        const fy = tr.height(gx, fz);

        putAt(b, .tyres, gx - 3, fy, fz, 0);
        putAt(b, .tyres, gx - 3, fy + 0.96, fz, 0.4);
        putAt(b, .tyres, gx - 2.1, fy, fz + 0.2, 0.2);
        putAt(b, if (@mod(@as(i32, @intFromFloat(gx + 300)), 18) < 9) .drum else .ibc, gx + 3, fy, fz, 0);
        putAt(b, .cone, gx + 1.6, fy, fz - 1, 0);

        if (@mod(@as(i32, @intFromFloat(gx + 300)), 27) < 9) putAt(b, .cans, gx + 3.4, fy, fz + 1.2, pi);
    }

    var px: f32 = -112;

    while (px < 114) : (px += 18) {
        if (@abs(px) < 16) continue;

        const z = gz + 9;

        if (taken(px, z, 2)) continue;

        put(b, .gazebo, px, z, 0);
        put(b, if (@mod(@as(i32, @intFromFloat(px + 300)), 36) < 18) .box_red else .box_white, px + 6, z + 1, half_pi);
        box(b, px + 4.7, tr.height(px, z) - 0.5, z - 2, px + 7.3, tr.height(px, z) + 2.6, z + 4);
        put(b, .tyres, px - 3.5, z - 1, 0);
        put(b, .tyres, px - 3.5, z, 0.4);
        putAt(b, .tyres, px - 3.5, tr.height(px, z) + 0.96, z - 0.5, 0.2);
        put(b, .ibc, px + 3, z + 3.5, 0);
        claimRect(px - 5, z - 3, px + 8, z + 5);
    }

    put(b, .camtower, -9, wall_z + 3, 0);
    put(b, .camtower, 9, wall_z + 3, 0);

    for ([_]f32{ -45, 45 }) |cx| park_list.append(b.gpa, .{ .pos = vec(cx, tr.height(cx, wall_z + 4), wall_z + 4), .yaw = half_pi }) catch {};

    loot(b, -45, gz - 5);
    loot(b, 45, gz - 5);
    loot(b, -90, gz + 9);
    loot(b, 90, gz + 9);
    spawnAt(b, -64, gz + 6, 0);
    spawnAt(b, 64, gz + 6, 0);
    claimRect(-122, wall_z - 1, 122, gz + 5);
}

fn infieldEdge(b: *Builder) void {
    const total = trackLength();
    var t: f32 = 2;
    var n: u32 = 0;

    while (t < total) : (t += 4) {
        n += 1;

        const p = trackPoint(t);
        const nx = @sin(p[2]);
        const nz = -@cos(p[2]);
        const ix = p[0] + nx * (track_w + 3.5);
        const iz = p[1] + nz * (track_w + 3.5);

        if (streetDist(ix, iz) < street_w + 3 or taken(ix, iz, 0)) continue;

        if (n % 9 < 6) {
            putAt(b, .fence, ix - @cos(p[2]), tr.height(ix, iz), iz - @sin(p[2]), -p[2]);
            putAt(b, .fence, ix + @cos(p[2]), tr.height(ix, iz), iz + @sin(p[2]), -p[2]);
        } else if (n % 9 == 7) {
            putAt(b, .tyrewall, ix, tr.height(ix, iz), iz, -p[2]);
            box(b, ix - 2, tr.height(ix, iz) - 0.5, iz - 2, ix + 2, tr.height(ix, iz) + 0.9, iz + 2);
        }

        if (n % 23 == 0) {
            const bx = p[0] - nx * (track_w + 14);
            const bz = p[1] - nz * (track_w + 14);

            putAt(b, .billboard, bx, tr.height(bx, bz), bz, -p[2] + pi);
        }

        if (n % 31 == 11) {
            const ox = p[0] - nx * (track_w + 12);
            const oz = p[1] - nz * (track_w + 12);

            if (!taken(ox, oz, 4)) {
                putAt(b, .shade, ox, tr.height(ox, oz), oz, -p[2]);
                putAt(b, .camtower, ox + 6 * @cos(p[2]), tr.height(ox, oz), oz + 6 * @sin(p[2]), -p[2]);
                claimRect(ox - 6, oz - 6, ox + 6, oz + 6);
            }
        }
    }
}

fn miniModule(b: *Builder, cx: f32, cz: f32) void {
    const yaw = @as(f32, @floatFromInt(@as(u32, @intFromFloat(rnd(b) * 3.99)))) * half_pi;
    const pick = rnd(b);

    if (pick < 0.22) {
        lp(b, boxes[@as(usize, @intFromFloat(rnd(b) * 2.99))], cx, cz, yaw, 0, 0, 0, 0);
        lsolid(b, cx, cz, yaw, .{ -3.1, -1.3, 3.1, 1.3, -0.5, 2.6 });
        lp(b, .wrap, cx, cz, yaw, -1.5, 2.2, 0, 0);
        lp(b, .wrap, cx, cz, yaw, -0.4, 2.2, 0, 0.1);
        lp(b, .drum, cx, cz, yaw, 2, 2, 0, 0);
    } else if (pick < 0.4) {
        for ([_]f32{ -1, 0, 1 }) |tx| {
            lp(b, .tyres, cx, cz, yaw, tx, 0, 0, 0);
            lp(b, .tyres, cx, cz, yaw, tx, 0, 0.96, 0.3);
        }

        lp(b, .tyres, cx, cz, yaw, -0.5, 0, 1.92, 0.1);
        lp(b, .drum, cx, cz, yaw, 2.4, 0.4, 0, 0);
        lp(b, .drum, cx, cz, yaw, 2.4, -0.6, 0, 0.5);
        lp(b, .cone, cx, cz, yaw, -2.5, 1.5, 0, 0);
    } else if (pick < 0.56) {
        padLot(cx, cz, yaw, 3.5, 3.5);
        lp(b, .gazebo, cx, cz, yaw, 0, 0, 0, 0);
        lp(b, .picnic, cx, cz, yaw, 0, 0.3, 0, 0);
        lp(b, .ice, cx, cz, yaw, 2.6, -1.4, 0, 0);
        lp(b, .redflag, cx, cz, yaw, -3, 3, 0, 0);
    } else if (pick < 0.7) {
        lp(b, .jersey, cx, cz, yaw, -2, 0, 0, 0);
        lp(b, .jersey, cx, cz, yaw, 2, 0, 0, 0);
        lp(b, .tyrewall, cx, cz, yaw, 0, 1.6, 0, 0);
        lsolid(b, cx, cz, yaw, .{ -4, -0.4, 4, 2.1, -0.5, 0.9 });
    } else if (pick < 0.84) {
        lp(b, .ibc, cx, cz, yaw, 0, 0, 0, 0);
        lp(b, .ibc, cx, cz, yaw, 1.3, 0, 0, 0.05);
        lp(b, .ibc, cx, cz, yaw, 0.6, 0, 1.16, 0.1);
        lp(b, .wrap, cx, cz, yaw, -1.4, 0.2, 0, 0);
        lp(b, .cans, cx, cz, yaw, 0, 2, 0, 0);
    } else {
        putS(b, .outcrop, cx, cz, spin(b), 0.9);
        lp(b, .joshua, cx, cz, yaw, 3, 2, 0, spin(b));
        lp(b, .creosote, cx, cz, yaw, -3, 1, 0, spin(b));
        lp(b, .creosote, cx, cz, yaw, 1, -3, 0, spin(b));
    }
}

fn fillMini(b: *Builder) void {
    var z: f32 = -hz + 12;

    while (z < hz - 10) : (z += 3) {
        var x: f32 = -hx + 12;

        while (x < hx - 10) : (x += 3) {
            if (trackSd(x, z) > -track_w - 8 or taken(x, z, 4) or lotAt(x, z) or streetDist(x, z) < street_w + 5) continue;

            if (rnd(b) < 0.3) continue;

            miniModule(b, x, z);
            claimRect(x - 4, z - 4, x + 4, z + 4);
        }
    }
}

fn desertCamp(b: *Builder, cx: f32, cz: f32) void {
    const yaw = spin(b);
    const pick = rnd(b);

    if (pick < 0.3) {
        lp(b, .billboard, cx, cz, yaw, 0, 0, 0, 0);
        putS(b, .outcrop, cx + 6, cz + 4, spin(b), 1.4);
        lp(b, .saguaro, cx, cz, yaw, -5, 3, 0, 0);
    } else if (pick < 0.55) {
        lp(b, .shade, cx, cz, yaw, 0, 0, 0, 0);
        lp(b, .picnic, cx, cz, yaw, 0, 0, 0, 0);
        lp(b, .ice, cx, cz, yaw, 2, 1, 0, 0);
        lp(b, .redflag, cx, cz, yaw, 4, -4, 0, 0);
        lp(b, .tyres, cx, cz, yaw, -4, 3, 0, 0);
    } else if (pick < 0.75) {
        putS(b, .outcrop, cx, cz, spin(b), b.rng.range(1.6, 2.4));
        putS(b, .outcrop, cx + 5, cz - 3, spin(b), b.rng.range(1.0, 1.6));
        lp(b, .joshua, cx, cz, yaw, -5, 4, 0, 0);
    } else {
        lp(b, if (rnd(b) < 0.5) .box_red else .box_white, cx, cz, yaw, 0, 0, 0, 0);
        lsolid(b, cx, cz, yaw, .{ -3.1, -1.3, 3.1, 1.3, -0.5, 2.6 });
        lp(b, .drum, cx, cz, yaw, 4, 1, 0, 0);
        lp(b, .tyres, cx, cz, yaw, -4, 1.5, 0, 0);
        lp(b, .weed, cx, cz, yaw, 1, 3, 0, 0);
    }
}

fn outerRing(b: *Builder) void {
    var z: f32 = -170;

    while (z < 172) : (z += 6) {
        var x: f32 = -170;

        while (x < 172) : (x += 6) {
            const sd = trackSd(x, z);

            if (sd < track_w + 16 or taken(x, z, 6)) continue;

            if (rnd(b) < 0.55) continue;

            desertCamp(b, x + b.rng.range(-2, 2), z + b.rng.range(-2, 2));
            claimRect(x - 7, z - 7, x + 7, z + 7);
        }
    }
}

fn build(b: *Builder) void {
    @memset(&occ, 0);
    shadow_n = 0;
    lot_n = 0;
    spawn_list = .empty;
    spawn_yaw = .empty;
    anchor_list = .empty;
    park_list = .empty;
    loot_list = .empty;

    circuit(b);
    mainStreet(b);
    grandstand(b);
    pitLane(b);
    quarterNW(b);
    quarterNE(b);
    quarterSW(b);
    quarterSE(b);
    frontage(b);
    infieldEdge(b);
    fillInfield(b);
    fillMini(b);
    infield(b);
    outerRing(b);
    desert(b);
}

fn setSpots(gpa: std.mem.Allocator) void {
    wd.spawns = gpa.dupe(Vec3, spawn_list.items) catch &.{};
    wd.spawn_yaws = gpa.dupe(f32, spawn_yaw.items) catch &.{};
    wd.weapon_spots = gpa.dupe(Vec3, loot_list.items) catch &.{};
    wd.drone_anchors = gpa.dupe(Vec3, anchor_list.items) catch &.{};
    wd.vehicle_spots = gpa.dupe(wd.Spot, park_list.items) catch &.{};
    wd.parkClear(gpa);
}
