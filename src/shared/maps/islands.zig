const std = @import("std");
const api = @import("api.zig");

const tr = api.terrain;
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
const rotPoint = wd.rotPoint;
const covered = wd.covered;
const lowest = wd.lowest;
const runway = wd.runway;
const helipad = wd.helipad;
const Spot = wd.Spot;
const cHangar = wd.cHangar;
const clearance = wd.clearance;
const fuelTank = wd.fuelTank;
const levelGround = wd.levelGround;
const tent = wd.tent;


const K = enum {
    olive,
    cypress,
    agave,
    pear,
    geranium,
    basil,
    laundry,
    gwall,
    taverna,
    kafe,
    chair,
    lamp,
    boat,
    truck,
    melon,
    stand,
    light,
    boathouse,
    block,
    cube1,
    cube1b,
    cube1c,
    cube1d,
    cube2,
    cube2b,
    solar,
    dome1,
    dome2,
    stair,
    water,
    parapet,
    cave1,
    cave1b,
};

const kit = api.Kit(K);

const table = [_]api.Info{
    .{ .file = "islands/olive.glb", .scale = 1.00, .collide = .trunk, .group = .tree, .foliage = false, .min = .{ -3.154, 0.000, -1.974 }, .max = .{ 3.154, 4.523, 1.974 } },
    .{ .file = "islands/cypress.glb", .scale = 1.00, .collide = .cylinder, .group = .bush, .foliage = false, .min = .{ -0.856, 0.000, -0.900 }, .max = .{ 0.856, 8.100, 0.900 } },
    .{ .file = "islands/agave.glb", .scale = 1.00, .collide = .cylinder, .group = .bush, .foliage = false, .min = .{ -0.687, 0.000, -0.750 }, .max = .{ 0.687, 2.029, 0.750 } },
    .{ .file = "islands/pear.glb", .scale = 1.00, .collide = .cylinder, .group = .bush, .foliage = false, .min = .{ -1.067, 0.000, -0.254 }, .max = .{ 1.067, 1.815, 0.254 } },
    .{ .file = "islands/geranium.glb", .scale = 1.00, .collide = .none, .group = .bush, .foliage = false, .min = .{ -0.315, 0.000, -0.277 }, .max = .{ 0.315, 0.943, 0.277 } },
    .{ .file = "islands/basil.glb", .scale = 1.00, .collide = .none, .group = .bush, .foliage = false, .min = .{ -0.249, 0.000, -0.244 }, .max = .{ 0.249, 0.639, 0.244 } },
    .{ .file = "islands/laundry.glb", .scale = 1.00, .collide = .none, .group = .street, .foliage = false, .min = .{ -1.980, 0.000, -0.231 }, .max = .{ 1.980, 1.198, 0.231 } },
    .{ .file = "islands/gwall.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -2.000, 0.000, -0.200 }, .max = .{ 2.000, 1.000, 0.200 } },
    .{ .file = "islands/taverna.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.461, 0.000, -0.914 }, .max = .{ 0.461, 0.920, 0.914 } },
    .{ .file = "islands/kafe.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.300, 0.000, -0.300 }, .max = .{ 0.300, 0.795, 0.300 } },
    .{ .file = "islands/chair.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.230, 0.000, -0.225 }, .max = .{ 0.230, 0.920, 0.225 } },
    .{ .file = "islands/lamp.glb", .scale = 1.00, .collide = .cylinder, .group = .street, .foliage = false, .min = .{ -0.250, 0.000, -0.442 }, .max = .{ 0.250, 3.500, 0.442 } },
    .{ .file = "islands/boat.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -1.344, 0.000, -3.660 }, .max = .{ 1.344, 4.910, 3.660 } },
    .{ .file = "islands/truck.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.718, 0.000, -1.505 }, .max = .{ 0.718, 2.035, 1.505 } },
    .{ .file = "islands/melon.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.500, 0.000, -1.000 }, .max = .{ 0.500, 1.332, 1.000 } },
    .{ .file = "islands/stand.glb", .scale = 1.00, .collide = .box, .group = .street, .foliage = false, .min = .{ -0.300, 0.000, -0.293 }, .max = .{ 0.300, 1.600, 0.293 } },
    .{ .file = "islands/light.glb", .scale = 1.00, .collide = .box, .group = .building, .foliage = false, .min = .{ -2.600, 0.000, -2.600 }, .max = .{ 2.600, 6.500, 2.600 } },
    .{ .file = "islands/boathouse.glb", .scale = 1.00, .collide = .box, .group = .building, .foliage = false, .min = .{ -2.200, 0.000, -4.400 }, .max = .{ 2.200, 5.830, 4.400 } },
    .{ .file = "islands/block.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.240, -17.000, -2.240 }, .max = .{ 2.240, 0.000, 2.240 } },
    .{ .file = "islands/cube1.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.200, 0.000, -2.200 }, .max = .{ 2.200, 4.520, 2.200 } },
    .{ .file = "islands/cube1b.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.200, 0.000, -2.200 }, .max = .{ 2.200, 4.520, 2.200 } },
    .{ .file = "islands/cube1c.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.200, 0.000, -2.200 }, .max = .{ 2.200, 4.520, 2.200 } },
    .{ .file = "islands/cube1d.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.200, 0.000, -2.200 }, .max = .{ 2.200, 4.520, 2.200 } },
    .{ .file = "islands/cube2.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.200, 0.000, -2.200 }, .max = .{ 2.200, 7.820, 2.200 } },
    .{ .file = "islands/cube2b.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.200, 0.000, -2.200 }, .max = .{ 2.200, 7.820, 2.200 } },
    .{ .file = "islands/solar.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -1.000, 0.000, -0.735 }, .max = .{ 1.000, 2.460, 0.735 } },
    .{ .file = "islands/dome1.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.200, 0.000, -2.200 }, .max = .{ 2.200, 5.900, 2.200 } },
    .{ .file = "islands/dome2.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.200, 0.000, -2.200 }, .max = .{ 2.200, 9.200, 2.200 } },
    .{ .file = "islands/stair.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.200, -1.000, -0.000 }, .max = .{ 2.200, 4.250, 8.800 } },
    .{ .file = "islands/water.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -6.600, -0.200, -6.600 }, .max = .{ 6.600, 0.010, 6.600 } },
    .{ .file = "islands/parapet.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.230, 0.000, -0.220 }, .max = .{ 2.230, 0.950, 0.220 } },
    .{ .file = "islands/cave1.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.200, 0.000, -2.200 }, .max = .{ 2.200, 3.580, 2.200 } },
    .{ .file = "islands/cave1b.glb", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ -2.200, 0.000, -2.200 }, .max = .{ 2.200, 3.580, 2.200 } },
};

pub const def: api.Def = .{
    .name = "Islands",
    .note = "Harbour village, hills and coves",
    .tint = .{ 110, 180, 90 },
    .half = 275,
    .play = 250,
    .facet = 2.2,
    .runway = .{ 0, 118, 62, 12 },
    .helipads = .{ .{ 100, 30 }, .{ 120, 30 }, .{ 140, 30 } },
    .configure = buildIslands,
    .height = height,
    .ground = groundColor,
    .build = islandNature,
    .spots = setSpots,
    .props = &table,
    .palette = .{
        .sun_dir = .{ 0.58, 0.65, -0.49 },
        .sun_tint = .{ 1.15, 1.02, 0.86 },
        .grade_tint = .{ 1.03, 1, 0.96 },
        .grade_sat = 1.14,
        .fog = 0.0024,
        .fog_color = .{ 0.66, 0.82, 0.96 },
        .amb_sky = .{ 0.92, 1, 1.18 },
        .amb_ground = .{ 0.76, 0.74, 0.58 },
        .shade_tint = .{ 0.9, 0.94, 1.05 },
        .zenith = .{ 0.04, 0.26, 0.66 },
    },
    .backdrop = .{ 46, 140, 168 },
    .floor_y = tr.sea_level - 0.15,
    .aircraft = true,
    .grip = 0.84,
    .tufts = 0.025,
};

fn setSpots(gpa: std.mem.Allocator) void {
    islandSpots(gpa);
    wd.parkClear(gpa);
}

pub const Island = struct {
    x: f32,
    z: f32,
    r: f32,
    h: f32,
    seed: f32,
};


pub const isle_base: f32 = 1.0;

pub const village_cell: f32 = 4.4;
pub const village_cols: i32 = 15;
pub const village_rows: i32 = 17;
pub const village_x0: f32 = -33;
pub const village_z0: f32 = -186;

const village_tier: f32 = 3.3;
const harbour_r: f32 = 189;
const summit = [3]f32{ 0, -62, 40 };

pub fn inBasin(x: f32, z: f32) bool {
    const x0 = village_x0 + village_cell * 6 - 1.2;
    const x1 = village_x0 + village_cell * 9 + 1.2;
    const z0 = village_z0 + village_cell * 1 - 1.2;
    const z1 = village_z0 + village_cell * 4 + 1.2;

    return x > x0 and x < x1 and z > z0 and z < z1;
}

fn villageOut(x: f32, z: f32) f32 {
    const x1 = village_x0 + village_cell * @as(f32, @floatFromInt(village_cols));
    const z1 = village_z0 + village_cell * @as(f32, @floatFromInt(village_rows));
    const dx = @max(village_x0 - x, x - x1, 0);
    const dz = @max(village_z0 - z, z - z1, 0);

    return @sqrt(dx * dx + dz * dz);
}

pub fn villageMask(x: f32, z: f32) f32 {
    if (tr.current != .islands) return 0;

    return 1 - tr.smooth(0, 8, villageOut(x, z));
}

fn villageStep(z: f32) f32 {
    const row = @floor((z - village_z0) / village_cell);
    const k = std.math.clamp(@floor((row - 5) / 3), 0, 4);
    const y0 = isle_base + 0.3;

    if (row < 5) return y0;

    return y0 + k * village_tier;
}

fn villageRamp(z: f32) f32 {
    const t = (z - village_z0) / village_cell - 5;
    const y0 = isle_base + 0.3;

    return y0 + std.math.clamp(t / 3, 0, 4) * village_tier;
}

const fixed_islands = [_]Island{
    .{ .x = 0, .z = 0, .r = 206, .h = isle_base, .seed = 2 },
};

var island_buf: [4]Island = undefined;

pub var islands: []Island = island_buf[0..0];

fn buildIslands() void {
    island_buf[0] = fixed_islands[0];
    islands = island_buf[0..1];
}

pub fn islandEdge(i: Island, x: f32, z: f32) f32 {
    const ang = std.math.atan2(z - i.z, x - i.x);
    const wobble = 0.86 + 0.24 * tr.fbm(@cos(ang) * 1.7 + 7.3, @sin(ang) * 1.7 + 3.1) + 0.05 * @sin(ang * 7 + 1.3);
    const south = tr.smooth(0.62, 0.3, @abs(ang + std.math.pi / 2.0));

    return i.r * wobble * (1 - south) + harbour_r * south;
}

pub fn islandAt(x: f32, z: f32) ?usize {
    for (islands, 0..) |i, k| {
        const d = @sqrt((x - i.x) * (x - i.x) + (z - i.z) * (z - i.z));

        if (d < islandEdge(i, x, z)) return k;
    }

    return null;
}

pub fn coastDistance(x: f32, z: f32) f32 {
    if (islands.len == 0) return 0;

    const i = islands[0];
    const d = @sqrt((x - i.x) * (x - i.x) + (z - i.z) * (z - i.z));

    return islandEdge(i, x, z) - d;
}

fn height(x: f32, z: f32) f32 {
    if (islands.len == 0) return tr.void_floor;

    const i = islands[0];
    const d = @sqrt((x - i.x) * (x - i.x) + (z - i.z) * (z - i.z));
    const rr = islandEdge(i, x, z);

    if (d > rr) return @max(-30, tr.sea_level - 0.8 - (d - rr) * 1.3);

    const ang = std.math.atan2(z - i.z, x - i.x);
    const rocky = tr.smooth(0.5, 0.62, tr.fbm(@cos(ang) * 2.3 + 1.7, @sin(ang) * 2.3 - 4.2));
    const band = 16 - rocky * 11;
    const coast = tr.smooth(rr - band, rr, d);
    const hd = @sqrt((x - summit[0]) * (x - summit[0]) + (z - summit[1]) * (z - summit[1]));
    const hill = summit[2] * (1 - tr.smooth(0, 215, hd)) + 9 * (1 - tr.smooth(0, 70, @sqrt((x + 120) * (x + 120) + (z - 70) * (z - 70)))) + 7 * (1 - tr.smooth(0, 60, @sqrt((x - 115) * (x - 115) + (z - 40) * (z - 40))));
    const ridge = (tr.fbm(x * 0.018 + 4, z * 0.018 - 9) - 0.45) * 12;
    const bumps = (tr.fbm(x * 0.06, z * 0.06) - 0.5) * 2.2;
    const lift = rocky * 5 * (1 - tr.smooth(rr - band * 2.2, rr - band * 0.4, d));
    var h = i.h + @max(0, hill + ridge + bumps + lift);

    h = h * (1 - coast) + (tr.sea_level - 0.35) * coast;

    const flat = @max(tr.runwayMask(x, z), tr.padMask(x, z));

    h = h * (1 - flat) + (i.h + 3.2) * flat;

    const out = villageOut(x, z);

    if (out <= 0) {
        const basin: f32 = if (inBasin(x, z)) 1.5 else 0;

        return villageStep(z) - 0.25 - basin;
    }

    const vm = 1 - tr.smooth(0, 34, out);

    return h * (1 - vm) + (villageRamp(z) - 0.25) * vm;
}

pub const isle_hamlets = [_][3]f32{
    .{ -118, -62, 0.4 },
    .{ 122, -74, -0.5 },
    .{ -112, 82, 2.6 },
    .{ 128, 112, 2.2 },
};

pub const isle_summit = [2]f32{ 0, -62 };

pub const isle_paths = [_][4]f32{
    .{ -36, -112, 0, -62 },
    .{ 0, -62, -118, -62 },
    .{ 0, -62, 122, -74 },
    .{ 0, -62, 0, 96 },
    .{ 0, 96, -112, 82 },
    .{ 62, 100, 128, 112 },
    .{ -38, -150, -118, -62 },
    .{ 38, -150, 122, -74 },
    .{ -118, -62, -112, 82 },
    .{ 122, -74, 128, 112 },
};

pub fn pathDistance(x: f32, z: f32) f32 {
    if (tr.current != .islands) return 1000;

    var best: f32 = 1000;
    const wx = x + @sin(z * 0.07) * 2.5;
    const wz = z + @sin(x * 0.06) * 2.5;

    for (isle_paths) |sg| {
        const dx = sg[2] - sg[0];
        const dz = sg[3] - sg[1];
        const l2 = dx * dx + dz * dz;
        const t = std.math.clamp(((wx - sg[0]) * dx + (wz - sg[1]) * dz) / l2, 0, 1);
        const px = sg[0] + dx * t - wx;
        const pz = sg[1] + dz * t - wz;

        best = @min(best, @sqrt(px * px + pz * pz));
    }

    return best;
}


fn groundColor(x: f32, z: f32) api.Rgb {
    const n = tr.normal(x, z);
    const slope = 1 - n.y;
    const vary = 0.94 + tr.fbm(x * 0.08, z * 0.08) * 0.12;
    const light = vary + n.x * 0.04 - n.z * 0.03;
    const dry = tr.fbm(x * 0.025 + 40, z * 0.025 - 12);
    const fleck = tr.fbm(x * 0.3 - 7, z * 0.3 + 5);
    const h = tr.height(x, z);

    if (h < tr.sea_level - 0.05) return shade(.{ 190, 182, 150 }, light * 0.85);

    if (tr.runwayMask(x, z) > 0.6 or tr.padMask(x, z) > 0.7) return shade(.{ 196, 186, 160 }, light);

    if (villageMask(x, z) > 0.02) return shade(.{ 214, 200, 170 }, light);

    if (coastDistance(x, z) < 4.5 and h < tr.sea_level + 1.6) return shade(.{ 226, 210, 170 }, light);

    if (slope > 0.26) return shade(mix3(.{ 178, 170, 156 }, .{ 146, 136, 122 }, fleck), light * (0.92 + (1 - n.y) * 0.1));

    const pd = pathDistance(x, z);

    if (pd < 2.2) return shade(.{ 194, 160, 118 }, light);

    const scrub = tr.smooth(0.52, 0.64, tr.fbm(x * 0.045 - 13, z * 0.045 + 21));
    const grass = mix3(mix3(.{ 168, 156, 92 }, .{ 190, 168, 108 }, dry * 1.5 - 0.25), .{ 118, 128, 74 }, scrub * 0.85);
    const earth = mix3(grass, .{ 190, 158, 116 }, std.math.clamp((fleck - 0.58) * 4, 0, 0.7) + (1 - tr.smooth(2.2, 4.5, pd)) * 0.6);

    return shade(earth, light);
}

var village_spawns: std.ArrayList(Vec3) = .empty;


fn cellX(c: i32) f32 {
    return village_x0 + (@as(f32, @floatFromInt(c)) + 0.5) * village_cell;
}

fn cellZ(r: i32) f32 {
    return village_z0 + (@as(f32, @floatFromInt(r)) + 0.5) * village_cell;
}

fn cellInside(c: i32, r: i32) bool {
    if (terrain.current == .islands) return c >= 0 and r >= 0;

    const i = islands[0];
    const hc = village_cell * 0.5 + 2.5;

    for ([_]f32{ -1, 1 }) |sx| {
        for ([_]f32{ -1, 1 }) |sz| {
            const x = cellX(c) + sx * hc;
            const z = cellZ(r) + sz * hc;
            const d = @sqrt((x - i.x) * (x - i.x) + (z - i.z) * (z - i.z));

            if (d > islandEdge(i, x, z) - 3) return false;
        }
    }

    return true;
}

fn villageBlock(b: *Builder, c: i32, r: i32, top: f32) void {
    const x = cellX(c);
    const z = cellZ(r);
    const h = village_cell * 0.5;

    b.putAt(kit.of(.block), vec(x, top, z), 0, 1);
    b.solid(.{ .box = .{ .min = vec(x - h, top - 17, z - h), .max = vec(x + h, top, z + h) } });
}

fn villageHouse(b: *Builder, kind: Kind, c: i32, r: i32, base: f32, floors: f32, dome: bool) void {
    const x = cellX(c);
    const z = cellZ(r);
    const h = village_cell * 0.5;
    const top = base + floors * village_tier;

    const spin: f32 = if (dome) 0 else @floor(b.rng.next() * 3.99) * half_pi;

    b.putAt(kind, vec(x, base, z), spin, 1);
    b.solid(.{ .box = .{ .min = vec(x - h, base - 0.5, z - h), .max = vec(x + h, top, z + h) } });

    if (!dome and kind != kit.of(.cave1) and kind != kit.of(.cave1b)) {
        const lx: f32 = switch (kind) {
            kit.of(.cube1b), kit.of(.cube1d), kit.of(.cube2b) => 1.3,
            else => -1.3,
        };
        const ch = rotPoint(x, z, spin, lx, -1.5);

        b.solid(.{ .box = .{ .min = vec(ch[0] - 0.35, top, ch[1] - 0.35), .max = vec(ch[0] + 0.35, top + 1.2, ch[1] + 0.35) } });
    }

    if (floors > 1.5 and !dome and b.rng.next() < 0.4) b.putAt(kit.of(.solar), vec(x + b.rng.range(-0.8, 0.8), top, z + b.rng.range(-0.8, 0.8)), @floor(b.rng.next() * 3.99) * half_pi, 1);

    if (dome) b.solid(.{ .box = .{ .min = vec(x - 1.35, top, z - 1.35), .max = vec(x + 1.35, top + 2.0, z + 1.35) } });
}

fn villageStair(b: *Builder, c: i32, r: i32, base: f32) void {
    const x = cellX(c);
    const z0 = cellZ(r) - village_cell * 0.5;
    const run = village_cell * 2;

    b.putAt(kit.of(.stair), vec(x, base, z0), 0, 1);
    b.solid(.{ .ramp = .{ .min = vec(x - 1.4, base, z0), .max = vec(x + 1.4, base + village_tier, z0 + run), .rise = .pos_z } });
    b.solid(.{ .box = .{ .min = vec(x - 2.2, base - 0.5, z0), .max = vec(x - 1.4, base + village_tier + 0.9, z0 + run) } });
    b.solid(.{ .box = .{ .min = vec(x + 1.4, base - 0.5, z0), .max = vec(x + 2.2, base + village_tier + 0.9, z0 + run) } });
}

fn villageParapet(b: *Builder, x: f32, y: f32, z: f32, yaw: f32) void {
    const h = village_cell * 0.5;
    const along_x = @abs(@sin(yaw)) < 0.5;

    b.putAt(kit.of(.parapet), vec(x, y, z), yaw, 1);

    if (along_x) {
        b.solid(.{ .box = .{ .min = vec(x - h, y, z - 0.22), .max = vec(x + h, y + 0.95, z + 0.22) } });
    } else {
        b.solid(.{ .box = .{ .min = vec(x - 0.22, y, z - h), .max = vec(x + 0.22, y + 0.95, z + h) } });
    }
}

fn medVillage(b: *Builder) void {
    const isl = islands[0];
    const y0 = isl.h + 0.3;
    const cell = village_cell;
    const hc = cell * 0.5;
    const cols = village_cols;
    const stair_cols = [4][2]i32{ .{ 4, 10 }, .{ 7, 12 }, .{ 2, 9 }, .{ 5, 11 } };

    village_spawns = .empty;

    var c: i32 = 1;

    while (c < cols - 1) : (c += 1) {
        if (c >= 4 and c <= 10 and cellInside(c, 0)) villageBlock(b, c, 0, y0);

        if (c >= 6 and c <= 8) continue;

        var r: i32 = 1;

        while (r <= 3) : (r += 1) {
            if (cellInside(c, r)) villageBlock(b, c, r, y0);
        }
    }

    b.putAt(kit.of(.water), vec(cellX(7), y0 - 0.9, cellZ(2)), 0, 1);
    b.putAt(kit.of(.boat), vec(cellX(7) - 2.6, y0 - 0.95, cellZ(2) + 0.4), 0.15, 0.9);
    b.putAt(kit.of(.boat), vec(cellX(7) + 3.0, y0 - 0.95, cellZ(2) - 1.2), -0.3, 0.8);

    if (cellInside(4, 0)) b.putAt(kit.of(.light), vec(cellX(4), y0, cellZ(0)), 0, 0.7);

    b.putAt(kit.of(.lamp), vec(cellX(5) - 1.6, y0, cellZ(3)), 0, 1);
    b.putAt(kit.of(.lamp), vec(cellX(9) + 1.6, y0, cellZ(3)), 0, 1);

    c = 1;

    while (c < cols - 1) : (c += 1) {
        if (cellInside(c, 4)) villageBlock(b, c, 4, y0);
    }

    for ([_]i32{ 2, 4, 10, 12 }) |k| {
        if (!cellInside(k, 4)) continue;

        b.putAt(kit.of(.taverna), vec(cellX(k), y0, cellZ(4)), half_pi, 1);
        b.putAt(kit.of(.chair), vec(cellX(k) - 1.0, y0, cellZ(4)), half_pi, 1);
        b.putAt(kit.of(.chair), vec(cellX(k) + 1.0, y0, cellZ(4)), -half_pi, 1);
    }

    if (cellInside(1, 4)) b.putAt(kit.of(.boathouse), vec(cellX(1), y0, cellZ(4) - 1.0), half_pi, 1);

    for ([_][3]f32{ .{ 2, 1, 0 }, .{ 12, 2, 0 }, .{ 3, 3, 1 }, .{ 11, 1, 1 } }) |q| {
        const qc: i32 = @intFromFloat(q[0]);
        const qr: i32 = @intFromFloat(q[1]);

        if (!cellInside(qc, qr)) continue;

        const qx = cellX(qc);
        const qz = cellZ(qr);

        if (q[2] < 0.5) {
            b.putAt(kit.of(.gwall), vec(qx, y0, qz), 0, 1);
            b.solid(.{ .box = .{ .min = vec(qx - 2, y0, qz - 0.2), .max = vec(qx + 2, y0 + 1.0, qz + 0.2) } });
            b.putAt(kit.of(.geranium), vec(qx - 1.4, y0 + 1.0, qz), 0, 1);
            b.putAt(kit.of(.basil), vec(qx + 1.2, y0 + 1.0, qz), 0, 1);
        } else {
            b.putAt(kit.of(.olive), vec(qx, y0, qz), b.rng.range(0, 6.28), 0.75);
            b.putAt(kit.of(.kafe), vec(qx + 1.8, y0, qz + 1.2), 0, 1);
            b.putAt(kit.of(.chair), vec(qx + 1.8, y0, qz + 2.0), std.math.pi, 1);
        }
    }

    for ([_]i32{ 5, 9 }) |qc| {
        if (!cellInside(qc, 2)) continue;

        b.putAt(kit.of(.lamp), vec(cellX(qc) + (if (qc == 5) @as(f32, 1.6) else -1.6), y0, cellZ(2) - 1.5), 0, 1);
        b.putAt(kit.of(.kafe), vec(cellX(qc), y0, cellZ(2) + 1.6), 0, 1);
    }

    b.putAt(kit.of(.melon), vec(cellX(6), y0, cellZ(4) + 1.0), half_pi, 1);
    b.putAt(kit.of(.stand), vec(cellX(8) + 1.2, y0, cellZ(4) + 1.4), 0, 1);
    b.putAt(kit.of(.truck), vec(cellX(11), y0, cellZ(4)), half_pi, 1);
    village_spawns.append(b.gpa, vec(cellX(3), y0, cellZ(4))) catch {};
    village_spawns.append(b.gpa, vec(cellX(11), y0, cellZ(3))) catch {};

    var k: i32 = 0;

    while (k < 4) : (k += 1) {
        const lane = 5 + k * 3;
        const base = y0 + @as(f32, @floatFromInt(k)) * village_tier;
        const roof = base + village_tier;

        c = 1;

        while (c < cols - 1) : (c += 1) {
            if (!cellInside(c, lane)) continue;

            villageBlock(b, c, lane, base);

            const x = cellX(c);
            const lz = cellZ(lane);

            const roll = b.rng.next();

            const wz = lz + hc - 0.35;

            if (@mod(c, 3) == 0) b.putAt(kit.of(.lamp), vec(x + 1.6, base, lz + hc - 0.5), 0, 1);

            if (roll < 0.4) {
                b.putAt(kit.of(.geranium), vec(x - 1.0, base, wz), 0, 1.1);
                b.putAt(kit.of(.basil), vec(x - 0.3, base, wz), 0, 1);
                b.putAt(kit.of(.geranium), vec(x + 0.5, base, wz), 0.7, 1.2);
            } else if (roll < 0.75) {
                b.putAt(kit.of(.geranium), vec(x - 1.4, base, wz), 0, 1);
                b.putAt(kit.of(.basil), vec(x - 0.8, base, wz), 0, 1);
                b.putAt(kit.of(.geranium), vec(x + 1.0, base, wz), 1.0, 0.9);
            }

            if (b.rng.next() < 0.35) b.putAt(if (b.rng.next() < 0.5) kit.of(.geranium) else kit.of(.basil), vec(x + b.rng.range(-1.8, 1.8), base, wz), b.rng.range(0, 6.28), b.rng.range(0.8, 1.2));

            if (b.rng.next() < 0.22) {
                b.putAt(kit.of(.kafe), vec(x, base, lz - 1.0), 0, 1);
                b.putAt(kit.of(.chair), vec(x - 0.75, base, lz - 1.0), half_pi, 1);
                b.putAt(kit.of(.chair), vec(x + 0.75, base, lz - 1.0), -half_pi, 1);
            } else if (b.rng.next() < 0.12) {
                b.putAt(kit.of(.agave), vec(x, base, lz - 1.4), b.rng.range(0, 6.28), 0.8);
            }

            if (@mod(c, 4) == 2 and k > 0) b.putAt(kit.of(.laundry), vec(x, roof + 0.0, cellZ(lane + 2) + 0.4), 0, 1);

            if (@mod(c + k, 4) == 1) {
                wd.kit_loot.append(b.gpa, vec(x, base + 0.1, lz)) catch {};
            }

            if (@mod(c + k, 5) == 2) village_spawns.append(b.gpa, vec(x, base + 0.1, lz)) catch {};
        }

        if (k > 0) {
            for ([_]i32{ 1, cols - 2 }) |edge| {
                if (!cellInside(edge, lane)) continue;

                const ex = cellX(edge) + (if (edge == 1) -hc + 0.25 else hc - 0.25);

                villageParapet(b, ex, base, cellZ(lane), half_pi);
            }
        }

        for ([_]i32{ lane + 1, lane + 2 }) |r| {
            c = 1;

            while (c < cols - 1) : (c += 1) {
                if (!cellInside(c, r)) continue;

                const x = cellX(c);
                const z = cellZ(r);
                const is_stair = c == stair_cols[@intCast(k)][0] or c == stair_cols[@intCast(k)][1];

                villageBlock(b, c, r, base);

                if (is_stair) {
                    if (r == lane + 1) villageStair(b, c, r, base);

                    continue;
                }

                const roll = b.rng.next();
                const front = r == lane + 1;

                if (front and roll < 0.14) {
                    b.putAt(kit.of(.taverna), vec(x, base, z), half_pi, 1);
                    b.putAt(kit.of(.geranium), vec(x - 1.2, base, z + hc - 0.3), 0, 1.2);
                    b.putAt(kit.of(.olive), vec(x + 1.2, base, z + 0.6), b.rng.range(0, 6.28), 0.55);
                    villageParapet(b, x, roof, z + hc - 0.2, 0);

                    continue;
                }

                if (front and roll < 0.28) {
                    villageHouse(b, kit.of(.dome1), c, r, base, 1, true);
                } else if (!front and roll < 0.12) {
                    villageHouse(b, kit.of(.dome2), c, r, base, 2, true);
                } else if (!front and roll < 0.32) {
                    villageHouse(b, if (b.rng.next() < 0.6) kit.of(.cube2) else kit.of(.cube2b), c, r, base, 2, false);
                } else if (front and roll < 0.42) {
                    villageHouse(b, if (b.rng.next() < 0.5) kit.of(.cave1) else kit.of(.cave1b), c, r, base, 1, false);
                } else {
                    villageHouse(b, b.rng.pick(Kind, &.{ kit.of(.cube1), kit.of(.cube1), kit.of(.cube1b), kit.of(.cube1c), kit.of(.cube1d) }), c, r, base, 1, false);

                    if (!front and b.rng.next() < 0.35) b.putAt(b.rng.pick(Kind, &.{ kit.of(.laundry), kit.of(.geranium), kit.of(.basil), kit.of(.kafe) }), vec(x + b.rng.range(-1, 1), roof, z + b.rng.range(-1, 1)), @floor(b.rng.next() * 3.99) * half_pi, 1);
                }

                if (front and b.rng.next() < 0.45) villageParapet(b, x, roof, z - hc + 0.22, 0);

                if (front and b.rng.next() < 0.5) {
                    b.putAt(if (b.rng.next() < 0.5) kit.of(.geranium) else kit.of(.basil), vec(x + b.rng.range(-1.7, 1.7), roof + 0.28, z - hc + 0.15), 0, 1);
                }

                if (!front and b.rng.next() < 0.25) b.putAt(kit.of(.chair), vec(x + b.rng.range(-1, 1), base + village_tier, z + b.rng.range(-1, 0.5)), b.rng.range(0, 6.28), 1);

                if (front and b.rng.next() < 0.2) wd.kit_loot.append(b.gpa, vec(x, roof + 0.1, z)) catch {};
            }
        }
    }

    for ([_]f32{ -1, 1 }) |side| {
        var r: i32 = 2;

        while (r < village_rows) : (r += 3) {
            const x = (if (side < 0) village_x0 + cell * 0.5 else village_x0 + cell * (@as(f32, @floatFromInt(cols)) - 0.5)) + side * 1.5;
            const z = cellZ(r) + b.rng.range(-1.5, 1.5);

            if (b.rng.next() < 0.5) b.put(kit.of(.cypress), x, z, 0, b.rng.range(0.85, 1.15)) else b.put(kit.of(.olive), x, z, b.rng.range(0, 6.28), b.rng.range(0.8, 1.0));
        }
    }
}


var isle_spawns: std.ArrayList(Vec3) = .empty;
var isle_anchors: std.ArrayList(Vec3) = .empty;

fn isleOk(x: f32, z: f32, pad: f32) bool {
    if (coastDistance(x, z) < pad) return false;

    if (villageMask(x, z) > 0.05) return false;

    return terrain.runwayMask(x, z) < 0.05 and terrain.padMask(x, z) < 0.05;
}

fn isleHouse(b: *Builder, kind: Kind, x: f32, z: f32, spin: f32, floors: f32) void {
    const h = village_cell * 0.5;
    var base: f32 = -1e9;

    for ([_]f32{ -h, 0, h }) |sx| {
        for ([_]f32{ -h, 0, h }) |sz| base = @max(base, terrain.height(x + sx, z + sz));
    }

    base += 0.05;

    const top = base + floors * village_tier;
    const cave = kind == kit.of(.cave1) or kind == kit.of(.cave1b);

    b.putAt(kit.of(.block), vec(x, base, z), 0, 1);
    b.solid(.{ .box = .{ .min = vec(x - h, base - 17, z - h), .max = vec(x + h, base, z + h) } });
    b.putAt(kind, vec(x, base, z), spin, 1);
    b.solid(.{ .box = .{ .min = vec(x - h, base - 0.5, z - h), .max = vec(x + h, top, z + h) } });

    if (!cave) {
        const lx: f32 = switch (kind) {
            kit.of(.cube1b), kit.of(.cube1d), kit.of(.cube2b) => 1.3,
            else => -1.3,
        };
        const ch = rotPoint(x, z, spin, lx, -1.5);

        b.solid(.{ .box = .{ .min = vec(ch[0] - 0.35, top, ch[1] - 0.35), .max = vec(ch[0] + 0.35, top + 1.2, ch[1] + 0.35) } });
    }

    if (floors > 1.5 and b.rng.next() < 0.5) b.putAt(kit.of(.solar), vec(x + b.rng.range(-0.8, 0.8), top, z + b.rng.range(-0.8, 0.8)), @floor(b.rng.next() * 3.99) * half_pi, 1);
}

fn gwallRun(b: *Builder, x: f32, z: f32, along_x: bool, n: u32, gap: u32) void {
    var k: u32 = 0;

    while (k < n) : (k += 1) {
        if (gap > 0 and k % gap == gap - 1) continue;

        const off = @as(f32, @floatFromInt(k)) * 4;
        const px = if (along_x) x + off else x;
        const pz = if (along_x) z else z + off;

        if (!isleOk(px, pz, 5) or covered(b, px, pz, 0.6)) continue;

        b.putAt(kit.of(.gwall), vec(px, terrain.height(px, pz) - 0.1, pz), if (along_x) 0 else half_pi, 1);
    }
}

fn hamlet(b: *Builder, hm: [3]f32) void {
    var cx = hm[0];
    var cz = hm[1];

    while (coastDistance(cx, cz) < 38) {
        cx *= 0.95;
        cz *= 0.95;
    }

    const kinds = [_]Kind{ kit.of(.cube1), kit.of(.cube1b), kit.of(.cube1c), kit.of(.cube1d), kit.of(.cave1), kit.of(.cave1b), kit.of(.cube2), kit.of(.cube2b) };
    const lots = [_][2]f32{ .{ -6.6, -4.4 }, .{ -2.2, -4.4 }, .{ 4.4, -4.4 }, .{ 8.8, -4.4 }, .{ -6.6, 6.6 }, .{ 2.2, 6.6 }, .{ 6.6, 6.6 } };

    for (lots, 0..) |lot, i| {
        if (b.rng.next() < 0.15) continue;

        const x = cx + lot[0];
        const z = cz + lot[1];
        const kind = kinds[(i * 3 + @as(usize, @intFromFloat(@abs(hm[0])))) % kinds.len];
        const floors: f32 = if (kind == kit.of(.cube2) or kind == kit.of(.cube2b)) 2 else 1;

        isleHouse(b, kind, x, z, @floor(b.rng.next() * 3.99) * half_pi, floors);

        if (b.rng.next() < 0.6) b.putAt(if (b.rng.next() < 0.5) kit.of(.geranium) else kit.of(.basil), vec(x + b.rng.range(-1.8, 1.8), terrain.height(x, z + 2.9), z + (if (lot[1] < 0) @as(f32, 2.7) else -2.7)), 0, 1);
    }

    gwallRun(b, cx - 14, cz - 11, true, 8, 4);
    gwallRun(b, cx - 14, cz + 13, true, 8, 3);
    gwallRun(b, cx - 15, cz - 9, false, 6, 3);
    gwallRun(b, cx + 17, cz - 9, false, 6, 4);

    b.put(kit.of(.taverna), cx - 3, cz + 1.2, half_pi, 1);
    b.put(kit.of(.chair), cx - 4, cz + 1.2, half_pi, 1);
    b.put(kit.of(.chair), cx - 2, cz + 1.2, -half_pi, 1);
    b.put(kit.of(.lamp), cx + 2.5, cz + 2.8, 0, 1);
    b.put(if (b.rng.next() < 0.5) kit.of(.truck) else kit.of(.melon), cx + 6, cz + 1.0, half_pi, 1);
    b.put(kit.of(.laundry), cx - 4.4, cz - 1.4, 0, 1);

    for ([_][2]f32{ .{ -11, 2 }, .{ 13, -1 }, .{ 0, 11 }, .{ -9, 12 }, .{ 12, 10 } }) |o| {
        if (!covered(b, cx + o[0], cz + o[1], 1.5)) b.put(if (b.rng.next() < 0.6) kit.of(.olive) else kit.of(.cypress), cx + o[0], cz + o[1], b.rng.range(0, 6.28), b.rng.range(0.8, 1.05));
    }

    wd.kit_loot.append(b.gpa, vec(cx + 1, terrain.height(cx + 1, cz + 1) + 0.1, cz + 1)) catch {};
    wd.kit_loot.append(b.gpa, vec(cx - 8, terrain.height(cx - 8, cz + 1) + 0.1, cz + 1)) catch {};
    isle_spawns.append(b.gpa, vec(cx + 3, terrain.height(cx + 3, cz + 1.5), cz + 1.5)) catch {};
    isle_spawns.append(b.gpa, vec(cx - 12, terrain.height(cx - 12, cz - 15), cz - 15)) catch {};
    isle_anchors.append(b.gpa, vec(cx, terrain.height(cx, cz) + 16, cz)) catch {};
}

fn summitRuin(b: *Builder) void {
    const cx = isle_summit[0];
    const cz = isle_summit[1];
    const y = lowest(cx, cz, 2.6) + 0.3;

    b.putAt(kit.of(.light), vec(cx, y, cz), 0.3, 1.1);

    for ([_][3]f32{ .{ -9, -9, 1 }, .{ -9, 7, 0 }, .{ 7, -9, 1 }, .{ 7, 9, 0 } }) |w| gwallRun(b, cx + w[0], cz + w[1], w[2] > 0.5, 3, 0);

    for ([_][2]f32{ .{ -13, 2 }, .{ 12, -3 }, .{ 3, 14 }, .{ -4, -14 } }) |o| {
        isleRocks(b, cx + o[0], cz + o[1]);
        wd.kit_loot.append(b.gpa, vec(cx + o[0] * 0.7, terrain.height(cx + o[0] * 0.7, cz + o[1] * 0.7) + 0.1, cz + o[1] * 0.7)) catch {};
    }

    for ([_][2]f32{ .{ -18, -10 }, .{ 18, 12 }, .{ -16, 16 }, .{ 15, -16 } }) |o| b.put(kit.of(.cypress), cx + o[0], cz + o[1], 0, b.rng.range(0.9, 1.2));

    for ([_][2]f32{ .{ 22, 3 }, .{ -24, -4 }, .{ 2, -24 }, .{ -3, 23 } }) |o| isleRocks(b, cx + o[0], cz + o[1]);

    isle_spawns.append(b.gpa, vec(cx + 26, terrain.height(cx + 26, cz + 8), cz + 8)) catch {};
    isle_anchors.append(b.gpa, vec(cx, y + 22, cz)) catch {};
}

fn isleCoves(b: *Builder) void {
    const isl = islands[0];

    for ([_]f32{ 3.0, 0.15, 2.1, 0.95, 3.75, 5.5 }, 0..) |ang, n| {
        const dx = @cos(ang);
        const dz = @sin(ang);
        const rr = islandEdge(isl, isl.x + dx * isl.r, isl.z + dz * isl.r);
        const hx = isl.x + dx * (rr - 12);
        const hz = isl.z + dz * (rr - 12);
        const yaw = std.math.atan2(dx, dz);

        if (terrain.runwayMask(hx, hz) > 0.05 or terrain.padMask(hx, hz) > 0.05) continue;

        b.putAt(kit.of(.boathouse), vec(hx, lowest(hx, hz, 4) + 0.3, hz), yaw, 1);

        const bx = isl.x + dx * (rr + 6);
        const bz = isl.z + dz * (rr + 6);

        b.putAt(kit.of(.boat), vec(bx, terrain.sea_level - 0.45, bz), yaw + 0.4, 0.9);

        const lx = hx - dz * 6;
        const lz = hz + dx * 6;

        b.put(kit.of(.lamp), lx, lz, 0, 1);
        b.put(if (n % 2 == 0) kit.of(.agave) else kit.of(.pear), hx + dz * 6, hz - dx * 6, 0, 1);

        if (n % 2 == 1) b.put(kit.of(.truck), lx - dx * 4, lz - dz * 4, yaw, 1);

        wd.kit_loot.append(b.gpa, vec(lx - dx * 2, terrain.height(lx - dx * 2, lz - dz * 2) + 0.1, lz - dz * 2)) catch {};
        isle_spawns.append(b.gpa, vec(hx - dx * 8, terrain.height(hx - dx * 8, hz - dz * 8), hz - dz * 8)) catch {};
    }
}

fn harbourFront(b: *Builder) void {
    const z = village_z0 - 9;

    b.putAt(kit.of(.boat), vec(-22, terrain.sea_level - 0.45, z), 0.2, 1);
    b.putAt(kit.of(.boat), vec(17, terrain.sea_level - 0.45, z - 4), -0.35, 0.9);
    b.putAt(kit.of(.boat), vec(42, terrain.sea_level - 0.45, z + 3), 1.2, 0.8);
}

fn fieldWalls(b: *Builder) void {
    for ([_][4]f32{
        .{ -80, -110, 1, 10 },
        .{ 60, -120, 1, 9 },
        .{ -70, 20, 0, 9 },
        .{ 70, 10, 0, 8 },
        .{ -40, 40, 1, 12 },
        .{ 30, 60, 1, 8 },
        .{ -150, 10, 0, 8 },
        .{ 150, -10, 0, 7 },
        .{ -60, -150, 0, 6 },
        .{ 64, -160, 0, 5 },
    }) |w| gwallRun(b, w[0], w[1], w[2] > 0.5, @intFromFloat(w[3]), 4);
}

fn isleScatter(b: *Builder) void {
    const lim = terrain.play - 6;
    var x: f32 = -lim;

    while (x < lim) : (x += 6) {
        var z: f32 = -lim;

        while (z < lim) : (z += 6) {
            const px = x + b.rng.range(-2.2, 2.2);
            const pz = z + b.rng.range(-2.2, 2.2);

            if (!isleOk(px, pz, 5) or terrain.height(px, pz) < terrain.sea_level + 0.8) continue;

            if (pathDistance(px, pz) < 3.2 or covered(b, px, pz, 2)) continue;

            const n = terrain.normal(px, pz);
            const roll = b.rng.next();
            const yaw = b.rng.range(0, 6.28);
            const grove = terrain.fbm(px * 0.02 + 9, pz * 0.02 - 3);

            if (n.y < 0.86) {
                if (roll < 0.2) isleRocks(b, px, pz) else if (roll < 0.36) isleScrub(b, px, pz) else if (roll < 0.4) b.put(kit.of(.agave), px, pz, yaw, b.rng.range(0.8, 1.1));

                continue;
            }

            if (grove > 0.56) {
                if (roll < 0.42) b.put(kit.of(.olive), px, pz, yaw, b.rng.range(0.85, 1.15));

                continue;
            }

            const scrubby = terrain.smooth(0.52, 0.64, terrain.fbm(px * 0.045 - 13, pz * 0.045 + 21));

            if (roll < 0.03) {
                b.put(kit.of(.cypress), px, pz, yaw, b.rng.range(0.85, 1.2));
            } else if (roll < 0.07) {
                b.put(if (b.rng.next() < 0.5) kit.of(.agave) else kit.of(.pear), px, pz, yaw, b.rng.range(0.7, 1.0));
            } else if (roll < 0.11) {
                isleRocks(b, px, pz);
            } else if (roll < 0.2 + scrubby * 0.3) {
                isleScrub(b, px, pz);
            } else if (roll < 0.23 + scrubby * 0.3) {
                b.put(kit.of(.olive), px, pz, yaw, b.rng.range(0.7, 1.0));
            }
        }
    }
}

fn isleScrub(b: *Builder, x: f32, z: f32) void {
    const n: u32 = 2 + @as(u32, @intFromFloat(b.rng.next() * 4));
    var k: u32 = 0;

    while (k < n) : (k += 1) {
        const px = x + b.rng.range(-2.2, 2.2);
        const pz = z + b.rng.range(-2.2, 2.2);

        b.put(.kd_scrub, px, pz, b.rng.range(0, 6.28), b.rng.range(0.9, 1.4));
    }
}

fn isleRocks(b: *Builder, x: f32, z: f32) void {
    const kinds = [_]Kind{ .kd_rock_0, .kd_rock_1, .kd_rock_2, .kd_rock_4 };
    const n: u32 = 1 + @as(u32, @intFromFloat(b.rng.next() * 3));
    var k: u32 = 0;

    while (k < n) : (k += 1) {
        const px = x + b.rng.range(-2.5, 2.5);
        const pz = z + b.rng.range(-2.5, 2.5);

        b.putAt(b.rng.pick(Kind, &kinds), vec(px, lowest(px, pz, 0.8) + 0.3, pz), b.rng.range(0, 6.28), b.rng.range(0.9, 1.6));
    }

    if (b.rng.next() < 0.5) isleScrub(b, x + 3, z - 2);
}

fn islandNature(b: *Builder) void {
    wd.kit_loot = .empty;
    isle_spawns = .empty;
    isle_anchors = .empty;
    runway(b);

    for (terrain.helipads) |p| helipad(b, p[0], p[1]);

    cHangar(b, 34, 90);
    tent(b, -40, 92);
    fuelTank(b, -58, 86);

    medVillage(b);
    harbourFront(b);

    for (isle_hamlets) |hm| hamlet(b, hm);

    summitRuin(b);
    isleCoves(b);
    fieldWalls(b);
    isleScatter(b);
}

fn islandSpots(gpa: std.mem.Allocator) void {
    var spawn_list: std.ArrayList(Vec3) = .empty;
    var yaw_list: std.ArrayList(f32) = .empty;
    var spots: std.ArrayList(Vec3) = .empty;
    var anchors: std.ArrayList(Vec3) = .empty;
    var parked: std.ArrayList(Spot) = .empty;

    for (wd.kit_loot.items) |p| spots.append(gpa, p) catch {};

    for (village_spawns.items) |p| {
        spawn_list.append(gpa, p) catch {};
        yaw_list.append(gpa, std.math.pi) catch {};
    }

    for (isle_spawns.items) |p| {
        if (clearance(p) < 2) continue;

        spawn_list.append(gpa, p) catch {};
        yaw_list.append(gpa, std.math.atan2(-p.x, -p.z)) catch {};
    }

    for (isle_anchors.items) |p| anchors.append(gpa, p) catch {};

    anchors.append(gpa, vec(0, 30, -150)) catch {};

    for ([_][2]f32{ .{ -30, 146 }, .{ -18, 146 }, .{ -6, 146 }, .{ 6, 146 }, .{ 18, 146 } }) |p| parked.append(gpa, .{ .pos = vec(p[0], terrain.height(p[0], p[1]), p[1]), .yaw = half_pi }) catch {};

    for (isle_hamlets) |hm| {
        const px = hm[0] * 0.9 + 14;
        const pz = hm[1] * 0.9 + 16;

        if (levelGround(px, pz) and villageMask(px, pz) < 0.01) parked.append(gpa, .{ .pos = vec(px, terrain.height(px, pz), pz), .yaw = hm[2] }) catch {};
    }

    wd.spawns = spawn_list.toOwnedSlice(gpa) catch &.{};
    wd.spawn_yaws = yaw_list.toOwnedSlice(gpa) catch &.{};
    wd.weapon_spots = spots.toOwnedSlice(gpa) catch &.{};
    wd.drone_anchors = anchors.toOwnedSlice(gpa) catch &.{};
    wd.vehicle_spots = parked.toOwnedSlice(gpa) catch &.{};
}
