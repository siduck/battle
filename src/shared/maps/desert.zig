const std = @import("std");
const api = @import("api.zig");
const dk = @import("desert_kit.zig");

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
const rotPoint = wd.rotPoint;
const kit_houses = wd.kit_houses;
const compound = wd.compound;
const kitHouse = wd.kitHouse;
const kit = dk.kit;

pub const def: api.Def = .{
    .name = "Frontier Town",
    .note = "Western main street, mine camp",
    .tint = .{ 232, 168, 90 },
    .facet = 2.5,
    .configure = setup,
    .height = height,
    .ground = groundColor,
    .road = roadDist,
    .flat = flatMask,
    .build = frontier,
    .spots = setSpots,
    .props = &dk.table,
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
    .grip = 0.72,
};

const HouseSite = struct { first: usize, count: usize, variant: usize, x: f32, z: f32, yaw: f32 };

var house_sites: [128]HouseSite = undefined;
var site_count: usize = 0;

fn frontier(b: *Builder) void {
    site_count = 0;
    desertNature(b);
    refit(b);
    clearHouses(b);
    seatMesas(b);

    for (b.placed.items) |*p| p.kind = reskin(p.kind);
}

fn house(b: *Builder, x: f32, z: f32, front: [2]f32, v: usize) void {
    const first = b.solids.items.len;

    kitHouse(b, x, z, front, v);

    if (site_count == house_sites.len) return;

    house_sites[site_count] = .{ .first = first, .count = b.solids.items.len - first, .variant = v, .x = x, .z = z, .yaw = std.math.atan2(front[0], front[1]) };
    site_count += 1;
}

fn refit(b: *Builder) void {
    var i = site_count;

    while (i > 0) {
        i -= 1;

        const s = house_sites[i];
        const y = lowest(s.x, s.z, @max(kit_houses[s.variant].w, kit_houses[s.variant].d) / 2 + 0.5) + 0.4;
        const blocks = dk.blocks(look(s.variant));
        var fitted: [8]std.meta.Child(@TypeOf(b.solids.items)) = undefined;

        for (blocks, 0..) |bl, k| {
            const r = wd.rotBox(s.x, s.z, s.yaw, bl[0], bl[1], bl[2], bl[3]);

            fitted[k] = .{ .shape = .{ .box = .{ .min = vec(r[0], y - 0.9, r[1]), .max = vec(r[2], y + bl[4] + 0.1, r[3]) } } };
        }

        b.solids.replaceRange(b.gpa, s.first, s.count, fitted[0..blocks.len]) catch {};
    }
}

fn clearHouses(b: *Builder) void {
    var i = b.placed.items.len;

    while (i > 0) {
        i -= 1;

        const p = b.placed.items[i];

        if (p.kind != .kd_walk and buried(p.kind, p.pos.x, p.pos.z)) _ = b.placed.orderedRemove(i);
    }
}

fn buried(kind: Kind, x: f32, z: f32) bool {
    for (kit_houses) |h| {
        if (h.kind == kind) return false;
    }

    if (kind == .kd_flag and nearHouse(x, z, 1.2)) return true;

    for (house_sites[0..site_count]) |s| {
        for (dk.blocks(look(s.variant))) |bl| {
            if (bl[4] < 1) continue;

            const r = wd.rotBox(s.x, s.z, s.yaw, bl[0], bl[1], bl[2], bl[3]);

            if (x > r[0] + 0.15 and x < r[2] - 0.15 and z > r[1] + 0.15 and z < r[3] - 0.15) return true;
        }
    }

    return false;
}

fn nearHouse(x: f32, z: f32, margin: f32) bool {
    for (house_sites[0..site_count]) |s| {
        const info = dk.table[@intFromEnum(look(s.variant))];
        const r = wd.rotBox(s.x, s.z, s.yaw, info.min[0], info.min[2], info.max[0], info.max[2]);

        if (x > r[0] - margin and x < r[2] + margin and z > r[1] - margin and z < r[3] + margin) return true;
    }

    return false;
}

fn seatMesas(b: *Builder) void {
    const inner = terrain.play + 9;
    const outer = terrain.play + 16;

    for (b.placed.items) |*p| {
        if (p.kind != .kd_mesa_0 and p.kind != .kd_mesa_1 and p.kind != .kd_mesa_2) continue;

        if (@abs(@abs(p.pos.x) - inner) < 0.1) p.pos.x = std.math.sign(p.pos.x) * outer;
        if (@abs(@abs(p.pos.z) - inner) < 0.1) p.pos.z = std.math.sign(p.pos.z) * outer;

        p.pos.y = terrain.height(p.pos.x, p.pos.z) - 3;
    }
}

fn look(v: usize) dk.K {
    return switch (v) {
        0, 5 => .house_0,
        1 => .house_1,
        3 => .house_3,
        4 => .house_4,
        2, 6 => .house_6,
        7 => .house_7,
        8 => .house_8,
        9, 10 => .house_10,
        else => .house_11,
    };
}

fn reskin(k: Kind) Kind {
    for (kit_houses, 0..) |h, v| {
        if (h.kind == k) return kit.of(look(v));
    }

    return switch (k) {
        .kd_barrel => kit.of(.barrel),
        .kd_bench => kit.of(.bench),
        .kd_box => kit.of(.box),
        .kd_cactus_0 => kit.of(.cactus),
        .kd_cactus_1 => kit.of(.pear),
        .kd_chest => kit.of(.chest),
        .kd_crate => kit.of(.crate),
        .kd_fence => kit.of(.fence),
        .kd_flag => kit.of(.pole),
        .kd_fountain => kit.of(.watertower),
        .kd_lantern => kit.of(.lantern),
        .kd_mesa_0 => kit.of(.mesa_0),
        .kd_mesa_1 => kit.of(.mesa_1),
        .kd_mesa_2 => kit.of(.mesa_2),
        .kd_obelisk => kit.of(.headframe),
        .kd_palm_0 => kit.of(.deadtree),
        .kd_palm_2 => kit.of(.saguaro),
        .kd_patch_0 => kit.of(.gravel),
        .kd_patch_1 => kit.of(.tumbleweed),
        .kd_pillar => kit.of(.pillar),
        .kd_rock_0 => kit.of(.rock_0),
        .kd_rock_1 => kit.of(.rock_1),
        .kd_rock_2 => kit.of(.rock_2),
        .kd_rock_3 => kit.of(.rock_3),
        .kd_rock_4 => kit.of(.rock_4),
        .kd_scrub => kit.of(.sage),
        .kd_stall_2 => kit.of(.windmill),
        .kd_tent_0 => kit.of(.orebin),
        .kd_walk => kit.of(.walk),
        .dk_drift_0 => kit.of(.drift),
        .dk_truck_wreck => kit.of(.spoil),
        else => k,
    };
}

fn setup() void {
    terrain.town_center = .{ 0, -2 };
    terrain.town_half = .{ 50, 42 };
    terrain.market = .{ 24, 10, 12 };
    terrain.oasis = .{ -58, 57 };
}

fn roadDist(x: f32, z: f32) f32 {
    return @abs(x - terrain.roadLine(z));
}

fn flatMask(x: f32, z: f32) f32 {
    return 1 - terrain.smooth(terrain.road_half + 1, terrain.road_half + 10, terrain.roadDistance(x, z));
}

fn waterLevel() f32 {
    return terrain.rawHeight(terrain.oasis[0] + 12, terrain.oasis[1]) - 0.6;
}

fn setSpots(gpa: std.mem.Allocator) void {
    roadSpots(gpa);
    townLoot(gpa);
    wd.parkClear(gpa);
    townSpawns(gpa);
}

fn onRoad(z: f32, offset: f32) Vec3 {
    const x = terrain.roadLine(z) + offset;

    return vec(x, terrain.height(x, z), z);
}

fn roadSpots(gpa: std.mem.Allocator) void {
    var spots: std.ArrayList(Vec3) = .empty;
    var anchors: std.ArrayList(Vec3) = .empty;
    var parked: std.ArrayList(wd.Spot) = .empty;
    const reach = api.arena_half - 14;
    var z: f32 = -reach;
    var i: u32 = 0;

    while (z <= reach) : ({
        z += 13;
        i += 1;
    }) {
        const side: f32 = if (i % 2 == 0) 1 else -1;
        const ahead = terrain.roadLine(z + 1) - terrain.roadLine(z);
        const yaw = std.math.atan2(ahead, 1);

        spots.append(gpa, onRoad(z, side * 3)) catch {};
        anchors.append(gpa, onRoad(z, side * 20).add(.{ .y = 12 })) catch {};

        if (i % 2 == 0) parked.append(gpa, .{ .pos = onRoad(z + 4, side * (terrain.road_half - 1.6)), .yaw = if (side > 0) yaw else yaw + std.math.pi }) catch {};
    }

    wd.weapon_spots = spots.toOwnedSlice(gpa) catch &.{};
    wd.drone_anchors = anchors.toOwnedSlice(gpa) catch &.{};
    wd.vehicle_spots = parked.toOwnedSlice(gpa) catch &.{};
}

fn height(x: f32, z: f32) f32 {
    const flat = terrain.flatness(x, z);
    const box = @max(@abs(x), @abs(z));
    const wave = (z * 0.026 + x * 0.008 + terrain.fbm(x * 0.01, z * 0.01) * 2.6) / (2 * std.math.pi);
    const u = wave - @floor(wave);
    const profile = if (u < 0.78) terrain.smooth(0, 0.78, u) else 1 - terrain.smooth(0.78, 1, u);
    const dunes = profile * 6.5 * (0.5 + terrain.fbm(x * 0.014 + 5, z * 0.014));
    const rolling = (terrain.fbm(x * 0.01, z * 0.01) - 0.4) * 7;
    const ridge = terrain.smooth(terrain.play - 1, terrain.half - 6, box) * 12;
    const od = terrain.oasisDistance(x, z);
    const pool = (1 - terrain.smooth(6, 15, od)) * 2.6;
    const open = terrain.smooth(8, 18, od);

    const inside = terrain.townMask(x, z);

    return (dunes + @max(rolling, -0.15)) * (1 - flat) * open * (1 - inside) + ridge - pool;
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
    const tc = t.town_center;
    const lane = @min(@min(@abs(z - (tc[1] - 28)), @abs(z - (tc[1] + 30))), @min(@abs(x - (tc[0] - 34)), @abs(x - (tc[0] + 42))));
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
        const stalls = [_]Kind{ .kd_box, .kd_crate, .kd_box };

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
                const pick = b.rng.pick(Kind, &.{ .kd_barrel, .kd_bench, .kd_crate, .kd_chest });

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
                    house(b, cx, cz, front, variant);
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

    while (tries < 900 and built.items.len < 56) : (tries += 1) {
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
        house(b, cx, cz, front, variant);

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

    const edge = terrain.play - 3;
    var x: f32 = -edge;

    while (x < edge) : (x += 8) {
        var z: f32 = -edge;

        while (z < edge) : (z += 8) {
            const px = x + b.rng.range(-3.5, 3.5);
            const pz = z + b.rng.range(-3.5, 3.5);
            const od = terrain.oasisDistance(px, pz);

            if (terrain.roadDistance(px, pz) < terrain.road_half + 2 or od < 13) continue;

            if (terrain.townMask(px, pz) > 0.05) continue;

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

    oasisCamp(b);
    b.put(.kd_obelisk, terrain.roadLine(-60) + 16, -60, 0.3, 1);
    kdScatter(b);
    compounds(b);
    camps(b);
    coverClusters(b);
    edgeRocks(b);
}

fn oasisCamp(b: *Builder) void {
    const ox = terrain.oasis[0];
    const oz = terrain.oasis[1];

    for ([_][3]f32{ .{ 20, 0, 1.57 }, .{ 20, -0.6, 4.2 } }) |t| {
        const x = ox + @cos(t[1]) * t[0];
        const z = oz + @sin(t[1]) * t[0];

        b.putAt(.kd_tent_0, vec(x, terrain.height(x, z), z), t[2], 1);
    }

    coverNode(b, ox + 26, oz - 6, 0.6);
}

fn compounds(b: *Builder) void {
    const c = terrain.play - 14;
    const sites = [_][3]f32{ .{ -c, -c, 0 }, .{ c, -c, 1 }, .{ c, c, 0 } };

    for (sites) |o| {
        compound(b, o[0], o[1], 16, o[2] > 0.5);
        b.put(.kd_box, o[0] + 3, o[1] + 2, 0.3, 1);
        b.put(.kd_crate, o[0] - 2, o[1] + 4, 1.1, 1);
        b.put(b.rng.pick(Kind, &.{ .kd_barrel, .kd_barrel, .kd_chest }), o[0] - 4, o[1] - 3, 0, 1);
    }
}

fn camps(b: *Builder) void {
    const edge = terrain.play - 8;
    var gx: f32 = -edge;

    while (gx <= edge) : (gx += 30) {
        var gz: f32 = -edge;

        while (gz <= edge) : (gz += 30) {
            const ox = gx + b.rng.range(-9, 9);
            const oz = gz + b.rng.range(-9, 9);
            const rx = @abs(ox - terrain.town_center[0]) - terrain.town_half[0];
            const rz = @abs(oz - terrain.town_center[1]) - terrain.town_half[1];

            if (@max(rx, rz) < 10 or !api.inArena(ox, oz, 6)) continue;

            if (terrain.roadDistance(ox, oz) < terrain.road_half + 6 or terrain.oasisDistance(ox, oz) < 22 or covered(b, ox, oz, 8)) continue;

            if (1 - terrain.normal(ox, oz).y > 0.12) continue;

            const yaw = b.rng.range(0, 6.28);
            const roll = b.rng.next();
            const g = terrain.height(ox, oz);

            if (roll < 0.35) {
                b.putAt(.kd_tent_0, vec(ox, g, oz), yaw, 1);
                b.put(.kd_crate, ox + @sin(yaw) * 3.5, oz + @cos(yaw) * 3.5, yaw, 1);
                b.put(.kd_box, ox + @sin(yaw) * 3.8 + 1.2, oz + @cos(yaw) * 3.8, yaw, 1);
                b.put(.kd_barrel, ox - @sin(yaw) * 3.5, oz - @cos(yaw) * 3.5, yaw, 1);
                b.put(.kd_palm_2, ox - 5, oz + 4, yaw, 1);
            } else if (roll < 0.65) {
                b.putAt(.dk_truck_wreck, vec(ox, g - 0.05, oz), yaw, 1);
                b.putAt(.dk_drift_0, vec(ox + @sin(yaw) * 2, lowest(ox, oz, 3) + 0.15, oz + @cos(yaw) * 2), yaw + 1.4, 0.9);
                b.put(.kd_barrel, ox + @cos(yaw) * 3.4, oz - @sin(yaw) * 3.4, yaw, 1);
                b.put(.kd_scrub, ox - 3, oz + 2, yaw, 1);
            } else {
                b.putAt(.kd_fence, vec(ox, lowest(ox, oz, 3) + 0.3, oz), yaw, 1.1);
                b.putAt(.kd_fence, vec(ox + @sin(yaw) * 4.5, lowest(ox + @sin(yaw) * 4.5, oz + @cos(yaw) * 4.5, 3) + 0.3, oz + @cos(yaw) * 4.5), yaw + 1.57, 0.9);
                b.putAt(b.rng.pick(Kind, &.{ .kd_rock_1, .kd_rock_3 }), vec(ox - 3, lowest(ox - 3, oz - 3, 2) + 0.2, oz - 3), yaw, 1);
                b.put(.kd_palm_2, ox + 3, oz - 4, yaw, 1);
            }
        }
    }
}

fn coverCluster(b: *Builder, cx: f32, cz: f32) void {
    const n = 3 + @as(u32, @intFromFloat(b.rng.next() * 3.99));
    const yaw = b.rng.range(0, 6.28);
    var i: u32 = 0;

    while (i < n) : (i += 1) {
        const a = yaw + @as(f32, @floatFromInt(i)) * 1.1 + b.rng.range(-0.2, 0.2);
        const d = if (i == 0) 0 else b.rng.range(1.6, 3.4);
        const px = cx + @sin(a) * d;
        const pz = cz + @cos(a) * d;
        const roll = b.rng.next();

        if (roll < 0.4) {
            const k = b.rng.range(0.7, 1.05);

            b.putAt(.kd_rock_0, vec(px, lowest(px, pz, k) + 0.15, pz), b.rng.range(0, 6.28), k);
        } else if (roll < 0.65) {
            const k = b.rng.range(1.0, 1.3);

            b.putAt(.kd_rock_4, vec(px, lowest(px, pz, 0.6 * k) + 0.1, pz), b.rng.range(0, 6.28), k);
        } else if (roll < 0.8) {
            b.putAt(.kd_box, vec(px, terrain.height(px, pz), pz), a, 1);
        } else {
            b.putAt(.kd_crate, vec(px, terrain.height(px, pz), pz), a, 1.2);
        }
    }

    b.put(.kd_scrub, cx + @cos(yaw) * 4, cz - @sin(yaw) * 4, yaw, 1.1);
    b.put(.kd_scrub, cx - @cos(yaw) * 3.5, cz + @sin(yaw) * 3.5, yaw + 1, 0.9);
}

fn coverClusters(b: *Builder) void {
    const tc = terrain.town_center;
    const th = terrain.town_half;
    const p = terrain.play;
    const x0 = (tc[0] - th[0] - p) / 2;
    const x1 = (tc[0] + th[0] + p) / 2;
    const z0 = (tc[1] - th[1] - p) / 2;
    const z1 = (tc[1] + th[1] + p) / 2;
    const ring = [_][4]f32{ .{ x0, z0, x1, z0 }, .{ x1, z0, x1, z1 }, .{ x1, z1, x0, z1 }, .{ x0, z1, x0, z0 } };

    for (ring) |r| {
        const len = @abs(r[2] - r[0]) + @abs(r[3] - r[1]);
        var d: f32 = b.rng.range(4, 12);

        while (d < len) : (d += b.rng.range(25, 34)) {
            const k = d / len;
            const cx = r[0] + (r[2] - r[0]) * k + b.rng.range(-5, 5);
            const cz = r[1] + (r[3] - r[1]) * k + b.rng.range(-5, 5);

            if (terrain.roadDistance(cx, cz) < terrain.road_half + 3 or terrain.oasisDistance(cx, cz) < 18 or covered(b, cx, cz, 6)) continue;

            coverCluster(b, cx, cz);
        }
    }

    for ([_]f32{ -1, 1 }) |side| {
        const start = if (side > 0) tc[1] + th[1] + 12 else tc[1] - th[1] - 12;
        var z = start;

        while (@abs(z) < p - 8) : (z += side * 14) {
            for ([_]f32{ -1, 1 }) |sx| {
                const cx = terrain.roadLine(z) + sx * (terrain.road_half + 5);

                if (covered(b, cx, z, 5)) continue;

                coverCluster(b, cx, z + sx * 4);
            }
        }
    }
}

fn edgeRocks(b: *Builder) void {
    const ring = terrain.play + 9;
    var a: f32 = -ring + 8;
    var i: u32 = 0;

    while (a < ring) : (a += 24) {
        for ([_][2]f32{ .{ a, -ring }, .{ a, ring }, .{ -ring, a }, .{ ring, a } }) |m| {
            const mesas = [_]Kind{ .kd_mesa_0, .kd_mesa_1, .kd_mesa_2 };
            const kind = mesas[i % 3];

            b.putAt(kind, vec(m[0], terrain.height(m[0], m[1]) - 3, m[1]), @as(f32, @floatFromInt(i)) * 1.7, b.rng.range(0.5, 0.65));
            i += 1;
        }
    }

    for ([_]f32{ -1, 1 }) |side| {
        const z = side * (terrain.play - 2);
        const rx = terrain.roadLine(z);
        var o: f32 = -terrain.road_half;

        while (o <= terrain.road_half) : (o += 2.5) b.putAt(.kd_fence, vec(rx + o, lowest(rx + o, z, 1.2) + 0.3, z), 0, 1);

        b.putAt(.kd_rock_1, vec(rx - terrain.road_half - 2, lowest(rx - terrain.road_half - 2, z, 1) + 0.2, z), 0.4, 1.2);
        b.putAt(.kd_rock_2, vec(rx + terrain.road_half + 2, lowest(rx + terrain.road_half + 2, z, 1) + 0.2, z), 1.9, 1.1);
    }
}

fn townSpawns(gpa: std.mem.Allocator) void {
    var list: std.ArrayList(Vec3) = .empty;
    var yaws: std.ArrayList(f32) = .empty;
    var r: Rng = .{ .state = 9191 };
    const tc = terrain.town_center;
    const th = terrain.town_half;
    const c = terrain.play - 13;
    const fixed = [_][3]f32{ .{ 14, 2, -1.5 }, .{ 26, -4, -1.45 }, .{ -c, -c + 14, 0.8 }, .{ c - 14, -c, -0.8 }, .{ c, c - 14, -2.4 }, .{ -c + 18, c, 2.4 } };

    for (fixed) |f| {
        const p = vec(f[0], terrain.height(f[0], f[1]), f[1]);

        if (clearance(p) < 2) continue;

        list.append(gpa, p) catch {};
        yaws.append(gpa, f[2]) catch {};
    }

    var tries: u32 = 0;

    while (tries < 6000 and list.items.len < 12) : (tries += 1) {
        const x = tc[0] + r.range(-th[0] + 6, th[0] - 6);
        const z = tc[1] + r.range(-th[1] + 6, th[1] - 6);

        if (terrain.townMask(x, z) < 0.6 or !inStreet(x, z, 0)) continue;

        const p = vec(x, terrain.height(x, z), z);

        if (clearance(p) < 3) continue;

        var spread = true;

        for (list.items) |q| {
            if (q.sub(p).length() < 20) spread = false;
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

