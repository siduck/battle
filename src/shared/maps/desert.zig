const std = @import("std");
const api = @import("api.zig");

const wd = api.world;
const terrain = api.terrain;
const props = api.props;
const geom = api.geom;
const movement = api.movement;
const Builder = api.Builder;
const Rng = api.Rng;
const Kind = api.Kind;
const Vec3 = api.Vec3;
const vec = api.vec;
const half_pi = api.half_pi;
const shade = api.shade;
const mix3 = api.mix3;
const coverNode = wd.coverNode;
const lowest = wd.lowest;
const covered = wd.covered;
const clearance = wd.clearance;
const safeSpawns = wd.safeSpawns;
const kitHouse = wd.kitHouse;
const rotPoint = wd.rotPoint;
const kit_houses = wd.kit_houses;
const runway = wd.runway;
const helipad = wd.helipad;
const airstripPocket = wd.airstripPocket;
const ruinsPocket = wd.ruinsPocket;
const oasisPocket = wd.oasisPocket;
const compound = wd.compound;

pub const def: api.Def = .{
    .name = "Frontier Town",
    .note = "Western main street, mine camp",
    .tint = .{ 232, 168, 90 },
    .half = 280,
    .play = 250,
    .facet = 2.5,
    .runway = .{ 150, -200, 80, 15 },
    .helipads = .{ .{ 90, -168 }, .{ 115, -168 }, .{ 140, -168 } },
    .height = height,
    .ground = groundColor,
    .road = roadDist,
    .flat = flatMask,
    .build = desertNature,
    .spots = setSpots,
    .palette = .{
        .sun_dir = .{ 0.55, 0.64, 0.53 },
        .sun_tint = .{ 1.18, 0.98, 0.78 },
        .grade_tint = .{ 1.05, 1, 0.92 },
        .grade_sat = 1.18,
        .fog = 0.0042,
        .fog_color = .{ 0.86, 0.84, 0.78 },
        .amb_sky = .{ 0.95, 1, 1.18 },
        .amb_ground = .{ 0.88, 0.7, 0.52 },
        .shade_tint = .{ 0.9, 0.92, 1.05 },
        .zenith = .{ 0.05, 0.2, 0.58 },
    },
    .backdrop = .{ 206, 186, 146 },
    .aircraft = true,
    .tanks = true,
    .grip = 0.72,
    .tufts = 0.85,
};

fn roadDist(x: f32, z: f32) f32 {
    return @min(@abs(x - terrain.roadLine(z)), @min(@abs(z - (150 + 10 * @sin(x * 0.013))), @abs(z - (-140 + 5 * @sin(x * 0.017)))));
}

fn flatMask(x: f32, z: f32) f32 {
    return 1 - terrain.smooth(terrain.road_half + 1, terrain.road_half + 10, terrain.roadDistance(x, z));
}

fn waterLevel() f32 {
    return terrain.rawHeight(terrain.oasis[0] + 12, terrain.oasis[1]) - 0.6;
}

fn setSpots(gpa: std.mem.Allocator) void {
    wd.roadside(gpa);
    townLoot(gpa);
    wd.parkClear(gpa);
    townSpawns(gpa);
}

fn height(x: f32, z: f32) f32 {
    const flat = terrain.flatness(x, z);
    const box = @max(@abs(x), @abs(z));
    const wave = (z * 0.026 + x * 0.008 + terrain.fbm(x * 0.01, z * 0.01) * 2.6) / (2 * std.math.pi);
    const u = wave - @floor(wave);
    const profile = if (u < 0.78) terrain.smooth(0, 0.78, u) else 1 - terrain.smooth(0.78, 1, u);
    const dunes = profile * 6.5 * (0.5 + terrain.fbm(x * 0.014 + 5, z * 0.014));
    const rolling = (terrain.fbm(x * 0.01, z * 0.01) - 0.4) * 7;
    const ridge = terrain.smooth(terrain.play - 10, terrain.half, box) * 10;
    const od = terrain.oasisDistance(x, z);
    const pool = (1 - terrain.smooth(6, 15, od)) * 2.6;
    const open = terrain.smooth(8, 18, od);

    const inside = terrain.townMask(x, z);
    const strip = @max(@max(terrain.runwayMask(x, z), terrain.padMask(x, z)), terrain.pocketMask(x, z));

    return (dunes + @max(rolling, -1)) * (1 - flat) * open * (1 - inside) * (1 - strip) + ridge - pool;
}

fn groundColor(x: f32, z: f32) api.Rgb {
    const t = api.terrain;
    const n = t.normal(x, z);
    const slope = 1 - n.y;
    const h = t.height(x, z);
    const vary = 0.93 + t.fbm(x * 0.09, z * 0.09) * 0.14;
    const od = t.oasisDistance(x, z);
    const light = vary + n.x * 0.05 - n.z * 0.03;

    const town = t.townMask(x, z);
    const md = @sqrt((x - t.market[0]) * (x - t.market[0]) + (z - t.market[1]) * (z - t.market[1]));

    if (town > 0.5 and md < t.market[2]) {
        const cell = @mod(@floor(x / t.facet) + @floor(z / t.facet), 2);

        return shade(if (cell < 1) .{ 214, 186, 132 } else .{ 194, 164, 112 }, vary);
    }

    if (town > 0.5 and t.roadDistance(x, z) < t.road_half - 0.5) return shade(.{ 172, 146, 108 }, vary);

    const rd = t.roadDistance(x, z);

    if (rd < t.road_half + 2) {
        const k = t.smooth(t.road_half - 3, t.road_half + 2, rd);
        const dirt = [3]f32{ 172, 150, 112 };
        const sand = [3]f32{ 206, 186, 146 };

        return shade(.{ dirt[0] + (sand[0] - dirt[0]) * k, dirt[1] + (sand[1] - dirt[1]) * k, dirt[2] + (sand[2] - dirt[2]) * k }, vary);
    }

    const sand = [3]f32{ 206, 186, 146 };
    const lane = @min(@min(@abs(z - -36), @abs(z - 22)), @min(@abs(x - -30), @abs(x - 46)));
    const town_k = t.smooth(0.3, 0.7, town);

    if (town_k > 0) {
        const street = mix3(.{ 200, 180, 140 }, .{ 196, 160, 108 }, t.smooth(4.5, 2.0, lane));

        if (town_k >= 1) return shade(sandPatches(street, x, z, 0.6), light);

        return shade(sandPatches(mix3(sand, street, town_k), x, z, 0.8), light);
    }

    if (od < 13 and h > waterLevel() - 0.2) return shade(.{ 150, 156, 104 }, light);

    const strata = [_][3]f32{ .{ 142, 110, 85 }, .{ 158, 124, 96 }, .{ 176, 142, 110 }, .{ 192, 162, 126 }, .{ 206, 182, 144 } };
    const level: usize = @intFromFloat(std.math.clamp(@floor(@max(h, 0) / 4.5), 0, @as(f32, @floatFromInt(strata.len - 1))));
    const rock = strata[level];
    const ground = mix3(sand, rock, t.smooth(0.4, 0.62, slope));

    return shade(sandPatches(mix3(.{ 206, 150, 92 }, ground, t.smooth(13, 24, od)), x, z, 1 - t.smooth(0.3, 0.55, slope)), light);
}

fn sandPatches(c: [3]f32, x: f32, z: f32, amount: f32) [3]f32 {
    const t = api.terrain;
    const p = t.fbm(x * 0.028 + 17, z * 0.028 - 5);
    const q = t.fbm(x * 0.11 - 3, z * 0.11 + 9);
    const warm = t.smooth(0.5, 0.64, p) * amount;
    const pale = t.smooth(0.46, 0.34, p) * amount;
    const a = mix3(c, .{ 186, 150, 106 }, warm * 0.9);
    const b2 = mix3(a, .{ 230, 216, 182 }, pale * 0.8);
    const k = 0.94 + q * 0.12;

    return .{ b2[0] * k, b2[1] * k, b2[2] * k };
}

fn inStreet(x: f32, z: f32, pad: f32) bool {
    if (terrain.roadDistance(x, z) < terrain.road_half + pad) return true;

    for ([_]f32{ -28, 30 }) |oz| {
        if (@abs(z - (terrain.town_center[1] + oz)) < 3.5 + pad) return true;
    }

    for ([_]f32{ -34, 42 }) |ox| {
        if (@abs(x - (terrain.town_center[0] + ox)) < 3.5 + pad) return true;
    }

    const mx = x - terrain.market[0];
    const mz = z - terrain.market[1];

    return @sqrt(mx * mx + mz * mz) < terrain.market[2] + pad;
}

fn facing(x: f32, z: f32) [2]f32 {
    const road = x - terrain.roadLine(z);
    var best: f32 = if (terrain.current == .conquest) 1e9 else @abs(road);
    var dir: [2]f32 = if (road > 0) .{ -1, 0 } else .{ 1, 0 };

    for ([_]f32{ terrain.town_center[1] - 28, terrain.town_center[1] + 30 }) |sz| {
        if (@abs(z - sz) < best) {
            best = @abs(z - sz);
            dir = if (z > sz) .{ 0, -1 } else .{ 0, 1 };
        }
    }

    for ([_]f32{ terrain.town_center[0] - 34, terrain.town_center[0] + 42 }) |sx| {
        if (@abs(x - sx) < best) {
            best = @abs(x - sx);
            dir = if (x > sx) .{ -1, 0 } else .{ 1, 0 };
        }
    }

    return dir;
}

fn bazaar(b: *Builder) void {
    const mx = terrain.market[0];
    const mz = terrain.market[1];
    var i: u32 = 0;

    while (i < 7) : (i += 1) {
        const a = @as(f32, @floatFromInt(i)) * 0.8976 + 0.3;
        const r = terrain.market[2] - 3.2;
        const sx = mx + @cos(a) * r;
        const sz = mz + @sin(a) * r;
        const y = terrain.height(sx, sz);
        const stalls = [_]Kind{ .kd_stall_0, .kd_stall_1, .kd_stall_0 };

        b.putAt(stalls[i % stalls.len], vec(sx, y, sz), std.math.atan2(mx - sx, mz - sz), 1);
        b.put(b.rng.pick(Kind, &.{ .kd_box, .kd_chest, .kd_crate }), sx + @sin(a) * 1.6, sz - @cos(a) * 1.6, b.rng.range(0, 6.28), 1);
    }

    for ([_][2]f32{ .{ -6, -5 }, .{ 6, 5 }, .{ -5, 6 } }) |o| coverNode(b, mx + o[0], mz + o[1], b.rng.range(0, 6.28));

    b.put(.kd_lantern, mx - 3, mz, 0, 1);
    b.put(.kd_lantern, mx + 3, mz, 0, 1);
    b.put(.kd_palm_0, mx, mz, 0.4, 1.1);
    b.put(.kd_chest, mx + 1.5, mz + 2.5, 0.6, 1);
    b.put(.kd_lantern, mx - 6, mz - 6, 0.8, 1);
    b.put(.kd_lantern, mx + 6, mz + 6, 3.9, 1);
}

fn rowFree(built: []const [4]f32, cx: f32, cz: f32, hx: f32, hz: f32) bool {
    for (built) |h| {
        if (@abs(cx - h[0]) < hx + h[2] and @abs(cz - h[1]) < hz + h[3]) return false;
    }

    const mx = cx - terrain.market[0];
    const mz = cz - terrain.market[1];

    if (@sqrt(mx * mx + mz * mz) < terrain.market[2] + @max(hx, hz)) return false;

    for ([_][2]f32{ .{ -1, -1 }, .{ 1, -1 }, .{ -1, 1 }, .{ 1, 1 }, .{ 0, 0 } }) |k| {
        const x = cx + k[0] * hx;
        const z = cz + k[1] * hz;

        if (terrain.roadDistance(x, z) < terrain.road_half + 0.6) return false;
        if (@abs(x - terrain.town_center[0]) > terrain.town_half[0] or @abs(z - terrain.town_center[1]) > terrain.town_half[1]) return false;
    }

    return true;
}

fn streetDress(b: *Builder, along_x: bool, line: f32, a0: f32, a1: f32) void {
    const tc = terrain.town_center;
    var t = a0;
    var i: u32 = 0;

    while (t < a1) : (t += 4) {
        for ([_]f32{ -2, 2 }) |o| {
            const x = if (along_x) t + 2 else line + o;
            const z = if (along_x) line + o else t + 2;

            if (terrain.roadDistance(x, z) < terrain.road_half + 2) continue;

            if (b.rng.next() < 0.12) b.putAt(.kd_patch_1, vec(x, terrain.height(x, z), z), b.rng.range(0, 6.28), 1);
        }

        for ([_]f32{ -1, 1 }) |side| {
            const x = if (along_x) t + 2 else line + side * 4.05;
            const z = if (along_x) line + side * 4.05 else t + 2;

            if (terrain.roadDistance(x, z) < terrain.road_half + 2) continue;

            for ([_]f32{ -1, 1 }) |h| {
                const wx = if (along_x) x + h else x;
                const wz = if (along_x) z else z + h;

                b.putAt(.kd_walk, vec(wx, terrain.height(wx, wz) - 0.12, wz), if (along_x) 0 else std.math.pi / 2.0, 1);
            }

            if (i % 4 == 1 and side > 0) {
                const lx = if (along_x) x else x - side * 0.4;
                const lz = if (along_x) z - side * 0.4 else z;

                b.putAt(.kd_lantern, vec(lx, terrain.height(lx, lz), lz), if (along_x) -side * std.math.pi / 2.0 else (if (side > 0) std.math.pi else 0), 1);
            }
        }

        if (i % 4 == 0 and b.rng.next() < 0.75) {
            const cx = if (along_x) t + 2 else line - 3.4;
            const cz = if (along_x) line - 3.4 else t + 2;

            if (terrain.roadDistance(cx, cz) > terrain.road_half + 3) {
                b.putAt(.kd_flag, vec(cx, terrain.height(cx, cz), cz), if (along_x) 0 else std.math.pi / 2.0, 1);
            }
        }

        if (i % 5 == 2) {
            const side: f32 = if (b.rng.next() < 0.5) -1 else 1;
            const px = if (along_x) t + 2 else line + side * 2.6;
            const pz = if (along_x) line + side * 2.6 else t + 2;

            if (terrain.roadDistance(px, pz) > terrain.road_half + 2) {
                const pick = b.rng.pick(Kind, &.{ .kd_cart, .kd_bench, .kd_crate, .kd_chest });

                b.putAt(pick, vec(px, terrain.height(px, pz), pz), if (along_x) 0 else std.math.pi / 2.0, 1);
            }
        }

        i += 1;
    }

    _ = tc;
}

fn rowHouses(b: *Builder, built: *std.ArrayList([4]f32)) void {
    const tc = terrain.town_center;
    const th = terrain.town_half;
    const lines = [_]struct { along_x: bool, line: f32 }{
        .{ .along_x = true, .line = tc[1] - 28 },
        .{ .along_x = true, .line = tc[1] + 30 },
        .{ .along_x = false, .line = tc[0] - 34 },
        .{ .along_x = false, .line = tc[0] + 42 },
    };

    for (lines) |l| {
        const a0 = if (l.along_x) tc[0] - th[0] + 1 else tc[1] - th[1] + 1;
        const a1 = if (l.along_x) tc[0] + th[0] - 1 else tc[1] + th[1] - 1;

        for ([_]f32{ -1, 1 }) |side| {
            var t = a0 + b.rng.range(0, 2);
            var run: u32 = 0;

            while (t < a1) {
                const variant: usize = @intFromFloat(@floor(b.rng.next() * (@as(f32, @floatFromInt(kit_houses.len)) - 0.01)));
                const w = kit_houses[variant].w;
                const d = kit_houses[variant].d;
                const off = 4.6 + d / 2;
                const cx = if (l.along_x) t + w / 2 else l.line + side * off;
                const cz = if (l.along_x) l.line + side * off else t + w / 2;
                const hx = (if (l.along_x) w else d) / 2 + 0.05;
                const hz = (if (l.along_x) d else w) / 2 + 0.05;
                const front: [2]f32 = if (l.along_x) .{ 0, -side } else .{ -side, 0 };

                if (rowFree(built.items, cx, cz, hx, hz)) {
                    built.append(b.gpa, .{ cx, cz, hx, hz }) catch {};
                    kitHouse(b, cx, cz, front, variant);
                    run += 1;
                    t += w + 0.15;

                    if (run >= 3 and b.rng.next() < 0.5) {
                        t += b.rng.range(3.2, 4.5);
                        run = 0;
                    }
                } else {
                    t += 1.5;
                    run = 0;
                }
            }
        }

        streetDress(b, l.along_x, l.line, a0, a1);
    }
}

fn desertTown(b: *Builder) void {
    var built: std.ArrayList([4]f32) = .empty;
    var tries: u32 = 0;
    const tc = terrain.town_center;
    const th = terrain.town_half;

    const landmarks = [_]struct { kind: Kind, x: f32, z: f32, r: f32 }{
        .{ .kind = .kd_fountain, .x = -17, .z = 4, .r = 3.2 },
        .{ .kind = .kd_obelisk, .x = -17, .z = 17, .r = 3.0 },
        .{ .kind = .kd_stall_2, .x = 52, .z = -44, .r = 2.4 },
    };

    for (landmarks) |l| {
        const lx = tc[0] - 4 + l.x;
        const lz = tc[1] + 8 + l.z;

        b.putAt(l.kind, vec(lx, lowest(lx, lz, l.r) + 0.4, lz), std.math.pi / 2.0, 1);
        built.append(b.gpa, .{ lx, lz, l.r + 1, l.r + 1 }) catch {};
    }

    rowHouses(b, &built);

    while (tries < 900 and built.items.len < 78) : (tries += 1) {
        const cx = tc[0] + b.rng.range(-th[0] + 4, th[0] - 4);
        const cz = tc[1] + b.rng.range(-th[1] + 4, th[1] - 4);
        const front = facing(cx, cz);
        const variant: usize = @intFromFloat(@floor(b.rng.next() * (@as(f32, @floatFromInt(kit_houses.len)) - 0.01)));
        const w = kit_houses[variant].w;
        const d = kit_houses[variant].d;
        const hx = (if (front[0] != 0) d else w) / 2 + 0.9;
        const hz = (if (front[0] != 0) w else d) / 2 + 0.9;
        var clear_spot = true;

        for ([_][2]f32{ .{ -1, -1 }, .{ 1, -1 }, .{ -1, 1 }, .{ 1, 1 }, .{ 0, 0 }, .{ 0, -1 }, .{ 0, 1 }, .{ -1, 0 }, .{ 1, 0 } }) |k| {
            if (inStreet(cx + k[0] * hx, cz + k[1] * hz, 0.2)) clear_spot = false;
        }

        for (built.items) |h| {
            if (@abs(cx - h[0]) < hx + h[2] and @abs(cz - h[1]) < hz + h[3]) clear_spot = false;
        }

        if (!clear_spot) continue;

        built.append(b.gpa, .{ cx, cz, hx, hz }) catch {};
        kitHouse(b, cx, cz, front, variant);

        if (b.rng.next() < 0.3) b.put(.kd_palm_2, cx + hx + 0.3, cz - hz + 0.8, b.rng.range(0, 6.28), 1);
    }

    bazaar(b);

    for ([_][2]f32{ .{ -1, -1 }, .{ 1, -1 }, .{ -1, 1 }, .{ 1, 1 } }) |k| {
        b.put(.kd_pillar, tc[0] + k[0] * (th[0] + 3), tc[1] + k[1] * (th[1] + 3), b.rng.range(0, 6.28), 1);
        b.put(.kd_flag, tc[0] + k[0] * (th[0] + 6), tc[1] + k[1] * (th[1] + 1), 0, 1);
    }
}


fn kdScatter(b: *Builder) void {
    var x: f32 = -terrain.play + 6;

    while (x < terrain.play - 6) : (x += 7) {
        var z: f32 = -terrain.play + 6;

        while (z < terrain.play - 6) : (z += 7) {
            const px = x + b.rng.range(-3, 3);
            const pz = z + b.rng.range(-3, 3);

            if (terrain.roadDistance(px, pz) < terrain.road_half + 0.5 or terrain.oasisDistance(px, pz) < 13) continue;

            if (terrain.runwayMask(px, pz) > 0.05 or terrain.padMask(px, pz) > 0.05) continue;

            if (1 - terrain.normal(px, pz).y > 0.08) continue;

            if (covered(b, px, pz, 1.5)) continue;

            const roll = b.rng.next();
            const in_town = terrain.townMask(px, pz) > 0.3;

            if (!in_town and roll < 0.1) {
                b.putAt(if (b.rng.next() < 0.7) .kd_patch_0 else .kd_patch_1, vec(px, lowest(px, pz, 3) + 0.38, pz), b.rng.range(0, 6.28), b.rng.range(0.7, 1.3));
            } else if (!in_town and roll < 0.22) {
                b.put(.kd_scrub, px, pz, b.rng.range(0, 6.28), b.rng.range(0.8, 1.5));
            } else if (!in_town and roll < 0.26) {
                b.putAt(b.rng.pick(Kind, &.{ .kd_rock_0, .kd_rock_4 }), vec(px, lowest(px, pz, 1) + 0.3, pz), b.rng.range(0, 6.28), b.rng.range(0.5, 1.0));
            }
        }
    }
}

fn desertNature(b: *Builder) void {
    desertTown(b);

    var x: f32 = -terrain.half + 4;

    while (x < terrain.half - 4) : (x += 8) {
        var z: f32 = -terrain.half + 4;

        while (z < terrain.half - 4) : (z += 8) {
            const px = x + b.rng.range(-3.5, 3.5);
            const pz = z + b.rng.range(-3.5, 3.5);
            const od = terrain.oasisDistance(px, pz);

            if (terrain.roadDistance(px, pz) < terrain.road_half + 2 or od < 13) continue;

            if (terrain.townMask(px, pz) > 0.05) continue;

            if (terrain.runwayMask(px, pz) > 0.05 or terrain.padMask(px, pz) > 0.05 or terrain.pocketMask(px, pz) > 0.1) continue;

            if (@max(@abs(px), @abs(pz)) > 130 and b.rng.next() < 0.35) continue;

            if (1 - terrain.normal(px, pz).y > 0.3) continue;

            const roll = b.rng.next();

            if (roll < 0.12) {
                b.put(b.rng.pick(Kind, &.{ .kd_cactus_0, .kd_cactus_1, .kd_cactus_1 }), px, pz, b.rng.range(0, 6.28), b.rng.range(0.8, 1.2));
            } else if (roll < 0.15) {
                b.put(.kd_cactus_0, px, pz, b.rng.range(0, 6.28), b.rng.range(0.8, 1.2));
            } else if (roll < 0.21) {
                const kind = b.rng.pick(Kind, &.{ .kd_rock_0, .kd_rock_1, .kd_rock_2, .kd_rock_3, .kd_rock_4, .kd_rock_1 });
                const k = b.rng.range(0.6, 1.5);

                b.putAt(kind, vec(px, lowest(px, pz, 1.5 * k) + 0.2, pz), b.rng.range(0, 6.28), k);
            }
        }
    }

    var a: f32 = 0;

    while (a < 6.28) : (a += 0.42) {
        const r = b.rng.range(13.5, 17);

        b.put(if (b.rng.next() < 0.6) .kd_palm_0 else .kd_palm_2, terrain.oasis[0] + @cos(a) * r, terrain.oasis[1] + @sin(a) * r, b.rng.range(0, 6.28), b.rng.range(0.85, 1.2));
    }


    b.put(.kd_obelisk, terrain.roadLine(-70) + 16, -70, 0.3, 1);

    runway(b);

    for (terrain.helipads) |p| helipad(b, p[0], p[1]);

    airstripPocket(b);
    ruinsPocket(b);
    oasisPocket(b);
    kdScatter(b);

    var gx: f32 = -200;

    while (gx <= 200) : (gx += 30) {
        var gz: f32 = -200;

        while (gz <= 200) : (gz += 30) {
            const ox = gx + b.rng.range(-9, 9);
            const oz = gz + b.rng.range(-9, 9);
            const rx = @abs(ox - terrain.town_center[0]) - terrain.town_half[0];
            const rz = @abs(oz - terrain.town_center[1]) - terrain.town_half[1];
            const out = @max(rx, rz);

            if (out < 10 or out > 150) continue;

            if (terrain.roadDistance(ox, oz) < terrain.road_half + 6 or terrain.runwayMask(ox, oz) > 0.02 or terrain.padMask(ox, oz) > 0.02 or terrain.pocketMask(ox, oz) > 0.05 or terrain.oasisDistance(ox, oz) < 22) continue;

            if (1 - terrain.normal(ox, oz).y > 0.12) continue;

            const yaw = b.rng.range(0, 6.28);
            const roll = b.rng.next();
            const g = terrain.height(ox, oz);

            if (roll < 0.3) {
                var j: u32 = 0;
                const n = 3 + @as(u32, @intFromFloat(b.rng.next() * 2.99));

                while (j < n) : (j += 1) {
                    const ang = yaw + @as(f32, @floatFromInt(j)) * 2.1;
                    const d = b.rng.range(1.5, 4.5);

                    b.put(if (j % 2 == 0) .kd_palm_0 else .kd_palm_2, ox + @cos(ang) * d, oz + @sin(ang) * d, b.rng.range(0, 6.28), b.rng.range(0.85, 1.2));
                }

                b.put(.kd_scrub, ox + 3.5, oz - 2.5, yaw, 1.1);
                b.putAt(.dk_drift_1, vec(ox - 4, lowest(ox - 4, oz + 3, 3) + 0.15, oz + 3), yaw, 0.9);
            } else if (roll < 0.5) {
                b.putAt(.kd_tent_0, vec(ox, g, oz), yaw, 1);
                b.putAt(.kd_tent_0, vec(ox + @cos(yaw) * 7, terrain.height(ox + @cos(yaw) * 7, oz - @sin(yaw) * 7), oz - @sin(yaw) * 7), yaw + 0.5, 0.9);
                b.put(.kd_crate, ox + @sin(yaw) * 3.5, oz + @cos(yaw) * 3.5, yaw, 1);
                b.put(.kd_box, ox + @sin(yaw) * 3.8 + 1.2, oz + @cos(yaw) * 3.8, yaw, 1);
                b.put(.kd_barrel, ox - @sin(yaw) * 3.5, oz - @cos(yaw) * 3.5, yaw, 1);
                b.put(.kd_palm_2, ox - 5, oz + 4, yaw, 1);
            } else if (roll < 0.68) {
                b.putAt(.dk_truck_wreck, vec(ox, g - 0.05, oz), yaw, 1);
                b.putAt(.dk_drift_0, vec(ox + @sin(yaw) * 2, lowest(ox, oz, 3) + 0.15, oz + @cos(yaw) * 2), yaw + 1.4, 0.9);
                b.put(.kd_barrel, ox + @cos(yaw) * 3.4, oz - @sin(yaw) * 3.4, yaw, 1);
                b.put(.kd_scrub, ox - 3, oz + 2, yaw, 1);
            } else if (roll < 0.86) {
                b.putAt(.kd_fence, vec(ox, lowest(ox, oz, 3) + 0.3, oz), yaw, 1.1);
                b.putAt(.kd_fence, vec(ox + @sin(yaw) * 4.5, lowest(ox + @sin(yaw) * 4.5, oz + @cos(yaw) * 4.5, 3) + 0.3, oz + @cos(yaw) * 4.5), yaw + 1.57, 0.9);
                b.putAt(b.rng.pick(Kind, &.{ .kd_rock_1, .kd_rock_3 }), vec(ox - 3, lowest(ox - 3, oz - 3, 2) + 0.2, oz - 3), yaw, 1);
                b.put(.kd_palm_2, ox + 3, oz - 4, yaw, 1);
            } else {
                b.putAt(.dk_drift_2, vec(ox, lowest(ox, oz, 4) + 0.15, oz), yaw, 1.2);
                b.put(.kd_scrub, ox + 4, oz + 1, yaw, 1.2);
                b.put(.kd_scrub, ox - 3, oz - 2, yaw, 0.9);
            }
        }
    }

    var cx_: f32 = -terrain.play + 12;

    while (cx_ < terrain.play - 12) : (cx_ += 22) {
        var cz_: f32 = -terrain.play + 12;

        while (cz_ < terrain.play - 12) : (cz_ += 22) {
            const ox = cx_ + b.rng.range(-8, 8);
            const oz = cz_ + b.rng.range(-8, 8);

            if (terrain.townMask(ox, oz) > 0.02 or terrain.roadDistance(ox, oz) < terrain.road_half + 4 or terrain.runwayMask(ox, oz) > 0.02 or terrain.padMask(ox, oz) > 0.02 or terrain.pocketMask(ox, oz) > 0.05 or terrain.oasisDistance(ox, oz) < 20) continue;

            const roll = b.rng.next();
            const yaw = b.rng.range(0, 6.28);

            const flat_spot = 1 - terrain.normal(ox, oz).y < 0.06;

            if (roll < 0.3 and flat_spot) {
                b.putAt(b.rng.pick(Kind, &.{ .dk_drift_0, .dk_drift_1, .dk_drift_2 }), vec(ox, lowest(ox, oz, 3) + 0.15, oz), yaw, b.rng.range(0.8, 1.3));
                b.put(.kd_scrub, ox + 3, oz + 1.5, yaw, b.rng.range(0.8, 1.3));
            } else if (roll < 0.5) {
                b.putAt(.kd_fence, vec(ox, lowest(ox, oz, 3) + 0.3, oz), yaw, 1);
                if (flat_spot) b.putAt(.dk_drift_0, vec(ox + @cos(yaw) * 1.5, lowest(ox, oz, 3) + 0.15, oz - @sin(yaw) * 1.5), yaw + 0.3, 0.8);
                b.put(b.rng.pick(Kind, &.{ .kd_crate, .kd_barrel, .kd_chest }), ox + 2.5, oz - 2, yaw, 1);
            } else if (roll < 0.75) {
                b.putAt(b.rng.pick(Kind, &.{ .kd_rock_0, .kd_rock_2, .kd_rock_4 }), vec(ox, lowest(ox, oz, 2) + 0.2, oz), yaw, b.rng.range(1.0, 1.6));
                b.put(.kd_scrub, ox + 2.6, oz - 1.2, yaw, 1);
                b.put(.kd_scrub, ox - 2.2, oz + 2, yaw + 1, 0.8);
            } else if (roll < 0.9) {
                b.put(b.rng.pick(Kind, &.{ .kd_scrub, .kd_cactus_0, .kd_cactus_1 }), ox, oz, yaw, b.rng.range(0.9, 1.3));
            }
        }
    }

    var ma: f32 = 0.2;

    while (ma < 6.28) : (ma += 0.42) {
        const rr = terrain.play + 30 + b.rng.range(-6, 14);
        const sq = 1 / @max(@abs(@cos(ma)), @abs(@sin(ma)));
        const mx = @cos(ma) * rr * @min(sq, 1.25);
        const mz = @sin(ma) * rr * @min(sq, 1.25);

        b.putAt(b.rng.pick(Kind, &.{ .kd_mesa_0, .kd_mesa_1, .kd_mesa_2 }), vec(mx, terrain.height(mx, mz) - 3, mz), b.rng.range(0, 6.28), b.rng.range(0.8, 1.2));
    }

    const outposts = [_][3]f32{ .{ -150, 110, 0 }, .{ 170, 190, 1 }, .{ -200, -80, 0 }, .{ 200, 40, 1 }, .{ -110, -200, 1 }, .{ 70, 205, 0 }, .{ -205, 205, 1 }, .{ -30, -205, 0 }, .{ 120, -90, 1 }, .{ -90, 190, 0 } };

    for (outposts) |o| {
        if (terrain.roadDistance(o[0], o[1]) < terrain.road_half + 14) continue;

        compound(b, o[0], o[1], 18, o[2] > 0.5);
        b.put(.kd_box, o[0] + 3, o[1] + 2, 0.3, 1);
        b.put(.kd_crate, o[0] - 2, o[1] + 4, 1.1, 1);
        b.put(b.rng.pick(Kind, &.{ .kd_barrel, .kd_barrel, .kd_chest }), o[0] - 4, o[1] - 3, 0, 1);
    }
}

fn townSpawns(gpa: std.mem.Allocator) void {
    var list: std.ArrayList(Vec3) = .empty;
    var yaws: std.ArrayList(f32) = .empty;
    var r: Rng = .{ .state = 9191 };
    const tc = terrain.town_center;
    const th = terrain.town_half;
    const fixed = [_][3]f32{ .{ 14, 2, -1.5 }, .{ 26, -4, -1.45 } };

    for (fixed) |f| {
        const p = vec(f[0], terrain.height(f[0], f[1]), f[1]);

        if (clearance(p) < 2) continue;

        list.append(gpa, p) catch {};
        yaws.append(gpa, f[2]) catch {};
    }

    var tries: u32 = 0;

    while (tries < 6000 and list.items.len < 10) : (tries += 1) {
        const x = tc[0] + r.range(-th[0] + 6, th[0] - 6);
        const z = tc[1] + r.range(-th[1] + 6, th[1] - 6);

        if (terrain.townMask(x, z) < 0.6 or !inStreet(x, z, 0)) continue;

        const p = vec(x, terrain.height(x, z), z);

        if (clearance(p) < 3) continue;

        var spread = true;

        for (list.items) |q| {
            if (q.sub(p).length() < 14) spread = false;
        }

        if (!spread) continue;

        var best_yaw: f32 = 0;
        var best: f32 = 0;
        var i: u32 = 0;

        while (i < 16) : (i += 1) {
            const yaw = @as(f32, @floatFromInt(i)) * (std.math.pi / 8.0);
            const dir = vec(@sin(yaw), 0, @cos(yaw));
            const reach = if (movement.raycast(wd.pieces, p.add(.{ .y = 1.6 }), dir, 45)) |h| h.t else 45;
            const ahead = p.add(dir.scale(@min(reach, 30)));

            if (terrain.townMask(ahead.x, ahead.z) < 0.5) continue;

            if (reach > best) {
                best = reach;
                best_yaw = yaw;
            }
        }

        if (best < 20) continue;

        list.append(gpa, p) catch {};
        yaws.append(gpa, best_yaw) catch {};
    }

    if (list.items.len < 3) return safeSpawns(gpa);

    wd.spawns = list.toOwnedSlice(gpa) catch wd.spawns;
    wd.spawn_yaws = yaws.toOwnedSlice(gpa) catch wd.spawn_yaws;
}


fn townLoot(gpa: std.mem.Allocator) void {
    if (wd.town_loot.items.len == 0) return;

    var all: std.ArrayList(Vec3) = .empty;

    all.appendSlice(gpa, wd.weapon_spots) catch return;

    var i: usize = 0;

    while (i < wd.town_loot.items.len and all.items.len < 60) : (i += 3) all.append(gpa, wd.town_loot.items[i]) catch {};

    wd.weapon_spots = all.toOwnedSlice(gpa) catch wd.weapon_spots;
}

