const std = @import("std");
const math = @import("math.zig");
const geom = @import("geom.zig");
const map = @import("map.zig");
const props = @import("props.zig");
const terrain = @import("terrain.zig");
const movement = @import("movement.zig");
const courtyard = @import("courtyard_layout.zig");
const registry = @import("maps/registry.zig");

const Vec3 = math.Vec3;
const vec = math.vec;
const Kind = props.Kind;

pub const Placement = struct {
    kind: Kind,
    pos: Vec3,
    yaw: f32,
    scale: f32,
};

pub var placements: []Placement = &.{};
pub var pieces: []map.Piece = &.{};
pub var spawns: []Vec3 = &.{};
pub var spawn_yaws: []f32 = &.{};
pub var drone_anchors: []Vec3 = &.{};
pub var weapon_spots: []Vec3 = &.{};

pub const Spot = struct {
    pos: Vec3,
    yaw: f32,
};

pub var vehicle_spots: []Spot = &.{};

pub const Tone = enum { mud, house, roof, ruin, adobe, floor, stair, beam, wood, cloth_red, cloth_blue, cloth_yellow, f_floor, f_floor_dark, f_line, f_mint, f_mint_dark, f_grey, f_grey_dark, f_hazard, f_black, f_rail, f_light, f_screen, f_metal, f_ceiling, f_crate, f_crate_teal, f_container_red, f_container_blue, f_vault, f_red_light, f_pipe, f_pipe_red, f_barrel, f_barrel_red, f_rubber, f_sign, f_stain, f_wood_pallet, f_panel, olive, sandbag, concrete, tarmac, marking, cap_ring, flag_cloth, pole, rust, char, tent, sign, trim, plinth, shutter, frame, tank, rug, leaf, pot, scuff, scuff_soft, paint_line, blob, blob_soft };

pub const Structure = struct {
    min: Vec3,
    max: Vec3,
    tone: Tone,
    tint: u8 = 0,
};

pub var structures: []Structure = &.{};

pub const CapturePoint = struct {
    pos: Vec3,
    radius: f32,
    name: [:0]const u8,
};

pub var capture_points: []CapturePoint = &.{};

pub const Rng = struct {
    state: u64,

    pub fn next(r: *Rng) f32 {
        r.state = r.state *% 6364136223846793005 +% 1442695040888963407;

        return @as(f32, @floatFromInt(r.state >> 40)) / 16777216.0;
    }

    pub fn range(r: *Rng, lo: f32, hi: f32) f32 {
        return lo + (hi - lo) * r.next();
    }

    pub fn pick(r: *Rng, comptime T: type, items: []const T) T {
        const i: usize = @intFromFloat(@min(@as(f32, @floatFromInt(items.len - 1)), r.next() * @as(f32, @floatFromInt(items.len))));

        return items[i];
    }
};

pub const Builder = struct {
    gpa: std.mem.Allocator,
    placed: std.ArrayList(Placement) = .empty,
    solids: std.ArrayList(map.Piece) = .empty,
    rng: Rng = .{ .state = 0x5eed_d201e_f11e },
    masses: std.ArrayList(Structure) = .empty,
    tint: u8 = 0,
    ghost: bool = false,

    pub fn deco(b: *Builder, min: Vec3, max: Vec3, tone: Tone) void {
        if (b.ghost) return;

        b.masses.append(b.gpa, .{ .min = min, .max = max, .tone = tone, .tint = b.tint }) catch return;
    }

    pub fn mass(b: *Builder, min: Vec3, max: Vec3, tone: Tone) void {
        if (b.ghost) {
            b.solid(.{ .box = .{ .min = min, .max = max } });

            return;
        }

        b.masses.append(b.gpa, .{ .min = min, .max = max, .tone = tone, .tint = b.tint }) catch return;
        b.solid(.{ .box = .{ .min = min, .max = max } });
    }

    pub fn put(b: *Builder, kind: Kind, x: f32, z: f32, yaw: f32, scale: f32) void {
        b.putAt(kind, vec(x, terrain.height(x, z), z), yaw, scale);
    }

    pub fn putAt(b: *Builder, kind: Kind, pos: Vec3, yaw: f32, scale: f32) void {
        const info = props.info(kind);
        const s = info.scale * scale;

        b.placed.append(b.gpa, .{ .kind = kind, .pos = pos, .yaw = yaw, .scale = s }) catch return;

        switch (info.collide) {
            .none => {},
            .trunk => b.solid(.{ .cylinder = .{ .base = pos.sub(.{ .y = 0.5 }), .radius = 0.32 * s, .height = 4.5 * s } }),
            .cylinder => b.solid(.{ .cylinder = .{ .base = pos, .radius = 0.18, .height = (info.max[1] - info.min[1]) * s } }),
            .box => {
                const quarter = @mod(@as(i32, @intFromFloat(@round(yaw / (std.math.pi / 2.0)))), 2) != 0;
                const sx = (info.max[0] - info.min[0]) * s * 0.5;
                const sz = (info.max[2] - info.min[2]) * s * 0.5;
                const hx = if (quarter) sz else sx;
                const hz = if (quarter) sx else sz;
                const cx = (info.max[0] + info.min[0]) * 0.5 * s;
                const cz = (info.max[2] + info.min[2]) * 0.5 * s;
                const c = @cos(yaw);
                const sn = @sin(yaw);
                const ox = cx * c + cz * sn;
                const oz = -cx * sn + cz * c;
                const shrink: f32 = if (info.group == .rock) 0.7 else 0.96;

                b.solid(.{ .box = .{
                    .min = vec(pos.x + ox - hx * shrink, pos.y - 0.5, pos.z + oz - hz * shrink),
                    .max = vec(pos.x + ox + hx * shrink, pos.y + info.max[1] * s * (if (info.group == .rock) @as(f32, 0.8) else 1), pos.z + oz + hz * shrink),
                } });
            },
        }
    }

    pub fn solid(b: *Builder, shape: geom.Shape) void {
        b.solids.append(b.gpa, .{ .shape = shape }) catch {};
    }
};

const houses = [_]Kind{ .building_type_a, .building_type_b, .building_type_c, .building_type_d, .building_type_e, .building_type_f, .building_type_g, .building_type_h };
const shops = [_]Kind{ .building_a, .building_b, .building_c, .building_d, .building_e, .building_f, .building_g, .building_h, .building_skyscraper_a, .building_skyscraper_b };
const pines = [_]Kind{ .pine_1, .pine_2, .pine_3, .pine_4, .pine_5 };
const leafy = [_]Kind{ .commontree_1, .commontree_2, .commontree_3, .commontree_4, .commontree_5 };
const rocks = [_]Kind{ .rock_medium_1, .rock_medium_2, .rock_medium_3 };
const bushes = [_]Kind{ .fern_1, .plant_1_big, .fern_1 };
const cacti = [_]Kind{ .cactus_1, .cactus_2, .cactus_3 };
const grasses = [_]Kind{ .grass_common_short, .grass_common_tall, .grass_wispy_tall, .grass_common_short };

const tile: f32 = 8;
const half_pi: f32 = std.math.pi / 2.0;

fn roads(b: *Builder) void {
    const lines = [_]f32{ -32, 0, 32 };
    var t: f32 = -96;

    while (t <= 96) : (t += tile) {
        for (lines) |line| {
            const long = line == 0;
            const inside = @abs(t) <= 32;

            if (!long and !inside) continue;

            const at_cross_x = for (lines) |other| {
                if (@abs(t - other) < 0.1) break true;
            } else false;

            if (at_cross_x and (long or inside)) {
                b.put(.road_crossroad, line, t, 0, 1);
                b.put(.road_crossroad, t, line, 0, 1);

                continue;
            }

            b.put(.road_straight, line, t, 0, 1);
            b.put(.road_straight, t, line, half_pi, 1);
        }
    }
}

fn block(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32, downtown: bool) void {
    const set: []const Kind = if (downtown) &shops else &houses;
    const sides = [_]struct { horizontal: bool, at: f32, yaw: f32 }{
        .{ .horizontal = true, .at = z0 + 6, .yaw = std.math.pi },
        .{ .horizontal = true, .at = z1 - 6, .yaw = 0 },
        .{ .horizontal = false, .at = x0 + 6, .yaw = -half_pi },
        .{ .horizontal = false, .at = x1 - 6, .yaw = half_pi },
    };

    for (sides) |side| {
        var t: f32 = if (side.horizontal) x0 + 9 else z0 + 9;
        const end = if (side.horizontal) x1 - 9 else z1 - 9;

        while (t <= end) : (t += 11) {
            const x = if (side.horizontal) t else side.at;
            const z = if (side.horizontal) side.at else t;

            if (b.rng.next() < 0.15) continue;

            b.put(b.rng.pick(Kind, set), x, z, side.yaw, 1);
        }
    }
}

fn town(b: *Builder) void {
    const edges = [_]f32{ -54, -32, 0, 32, 54 };
    var i: usize = 0;

    while (i < 4) : (i += 1) {
        var j: usize = 0;

        while (j < 4) : (j += 1) {
            const x0 = edges[i] + terrain.road_half;
            const x1 = edges[i + 1] - terrain.road_half;
            const z0 = edges[j] + terrain.road_half;
            const z1 = edges[j + 1] - terrain.road_half;
            const downtown = (i == 1 or i == 2) and (j == 1 or j == 2);

            if (x1 - x0 < 14 or z1 - z0 < 14) continue;

            block(b, x0, z0, x1, z1, downtown);
        }
    }

    var t: f32 = -44;

    while (t <= 44) : (t += 16) {
        for ([_]f32{ -32, 0, 32 }) |line| {
            if (@abs(t - line) < 6) continue;

            b.put(.light_square, line + terrain.road_half + 0.6, t, half_pi, 1);
            b.put(.light_square, t, line - terrain.road_half - 0.6, 0, 1);
        }
    }

    for ([_]f32{ -32, 32 }) |x| {
        for ([_]f32{ -32, 32 }) |z| {
            b.put(.traffic_light, x + 6.5, z + 6.5, 0, 1);
        }
    }

    b.put(.construction_barrier, 4, 50, 0, 1);
    b.put(.construction_cone, -3, 47, 0, 1);
    b.put(.construction_cone, -1, 49, 0, 1);
}

fn clear(x: f32, z: f32) bool {
    if (terrain.roadDistance(x, z) < terrain.road_half + 2) return false;

    return @max(@abs(x), @abs(z)) > terrain.town + 4;
}

fn nature(b: *Builder) void {
    var x: f32 = -terrain.half + 4;

    while (x < terrain.half - 4) : (x += 7) {
        var z: f32 = -terrain.half + 4;

        while (z < terrain.half - 4) : (z += 7) {
            const px = x + b.rng.range(-3, 3);
            const pz = z + b.rng.range(-3, 3);

            if (!clear(px, pz)) continue;

            const density = terrain.fbm(px * 0.03 + 50, pz * 0.03 - 20);

            if (density > 0.47 and b.rng.next() < 0.85) {
                const kind = if (density > 0.56 or b.rng.next() < 0.4) b.rng.pick(Kind, &pines) else b.rng.pick(Kind, &leafy);

                b.put(kind, px, pz, b.rng.range(0, 6.28), b.rng.range(0.85, 1.35));
            } else if (b.rng.next() < 0.12) {
                b.put(b.rng.pick(Kind, &rocks), px, pz, b.rng.range(0, 6.28), b.rng.range(0.7, 1.6));
            } else if (b.rng.next() < 0.4) {
                b.put(b.rng.pick(Kind, &bushes), px, pz, b.rng.range(0, 6.28), b.rng.range(0.8, 1.3));
            }
        }
    }

    x = -terrain.half + 2;

    while (x < terrain.half - 2) : (x += 2.6) {
        var z: f32 = -terrain.half + 2;

        while (z < terrain.half - 2) : (z += 2.6) {
            const px = x + b.rng.range(-1.2, 1.2);
            const pz = z + b.rng.range(-1.2, 1.2);

            if (terrain.roadDistance(px, pz) < terrain.road_half + 0.5) continue;

            if (@max(@abs(px), @abs(pz)) < terrain.town - 6 and b.rng.next() < 0.9) continue;

            if (b.rng.next() < 0.55) b.put(b.rng.pick(Kind, &grasses), px, pz, b.rng.range(0, 6.28), b.rng.range(0.7, 1.3));
        }
    }
}

pub fn walls(b: *Builder) void {
    const p = terrain.play;

    b.solid(.{ .box = .{ .min = vec(-p - 2, -10, -p - 2), .max = vec(p + 2, 80, -p) } });
    b.solid(.{ .box = .{ .min = vec(-p - 2, -10, p), .max = vec(p + 2, 80, p + 2) } });
    b.solid(.{ .box = .{ .min = vec(-p - 2, -10, -p), .max = vec(-p, 80, p) } });
    b.solid(.{ .box = .{ .min = vec(p, -10, -p), .max = vec(p + 2, 80, p) } });
}

pub fn lowest(x: f32, z: f32, half: f32) f32 {
    var y = terrain.height(x, z);

    for ([_]f32{ -1, 1 }) |sx| {
        for ([_]f32{ -1, 1 }) |sz| y = @min(y, terrain.height(x + sx * half, z + sz * half));
    }

    return y - 0.4;
}

pub fn compound(b: *Builder, cx: f32, cz: f32, size: f32, ruined: bool) void {
    const h = size * 0.5;
    const y = lowest(cx, cz, h + 1);
    const t: f32 = 0.45;
    const tone: Tone = if (ruined) .ruin else .mud;
    const gate_side: f32 = if (cx > terrain.roadLine(cz)) -1 else 1;
    var k: f32 = -h;

    while (k < h) : (k += 2) {
        const seg_end = @min(k + 2, h);

        for ([_]f32{ -1, 1 }) |side| {
            const top = if (ruined) b.rng.range(0.6, 2.8) else 2.8;
            const skip = ruined and b.rng.next() < 0.25;

            if (!skip) b.mass(vec(cx + k, y, cz + side * h - t), vec(cx + seg_end, y + 0.4 + top, cz + side * h + t), tone);

            const gate = side == gate_side and @abs(k + 1) < 2;
            const top2 = if (ruined) b.rng.range(0.6, 2.8) else 2.8;

            if (!gate and !(ruined and b.rng.next() < 0.25)) b.mass(vec(cx + side * h - t, y, cz + k), vec(cx + side * h + t, y + 0.4 + top2, cz + seg_end), tone);
        }
    }

    const hx = cx - gate_side * (h - 4);
    const hz = cz + b.rng.range(-h * 0.4, h * 0.4);
    const wall_h: f32 = if (ruined) 2.2 else 3.6;

    b.mass(vec(hx - 3, y, hz - 3.5), vec(hx + 3, y + 0.4 + wall_h, hz + 3.5), if (ruined) .ruin else .house);

    if (!ruined) b.mass(vec(hx - 3.2, y + 0.4 + wall_h, hz - 3.7), vec(hx + 3.2, y + 0.65 + wall_h, hz + 3.7), .roof);

    if (b.rng.next() < 0.4) {
        const tx = cx + gate_side * (h - 1.6);
        const tz = cz + h - 1.6;

        b.mass(vec(tx - 1.5, y, tz - 1.5), vec(tx + 1.5, y + 7.5, tz + 1.5), tone);

        if (!ruined) b.mass(vec(tx - 1.7, y + 7.5, tz - 1.7), vec(tx + 1.7, y + 7.8, tz + 1.7), .roof);
    }
}

const Frame = struct {
    c: [2]f32,
    r: [2]f32,
    n: [2]f32,
    depth: f32,

    fn at(f: Frame, u: f32, v: f32) [2]f32 {
        const k = v - f.depth / 2;

        return .{ f.c[0] + f.r[0] * u - f.n[0] * k, f.c[1] + f.r[1] * u - f.n[1] * k };
    }

    fn box(f: Frame, ua: f32, v0: f32, ub: f32, v1: f32, y0: f32, y1: f32) [2]Vec3 {
        const a = f.at(ua, v0);
        const c = f.at(ub, v1);

        return .{ vec(@min(a[0], c[0]), y0, @min(a[1], c[1])), vec(@max(a[0], c[0]), y1, @max(a[1], c[1])) };
    }

    fn rise(f: Frame, up: bool) geom.Rise {
        const d = if (up) f.r else [2]f32{ -f.r[0], -f.r[1] };

        if (d[0] > 0.5) return .pos_x;

        if (d[0] < -0.5) return .neg_x;

        if (d[1] > 0.5) return .pos_z;

        return .neg_z;
    }
};

const Opening = struct {
    c: f32,
    w: f32,
    lo: f32,
    hi: f32,
};

const wall_t: f32 = 0.35;
const storey: f32 = 3.3;
const slab_t: f32 = 0.28;
const stair_len: f32 = 4.4;
const stair_w: f32 = 1.3;

pub var town_loot: std.ArrayList(Vec3) = .empty;

fn part(b: *Builder, f: Frame, ua: f32, v0: f32, ub: f32, v1: f32, y0: f32, y1: f32, tone: Tone, solid_part: bool) void {
    if (ub - ua < 0.02 or v1 - v0 < 0.02 or y1 - y0 < 0.02) return;

    const bx = f.box(ua, v0, ub, v1, y0, y1);

    if (solid_part) b.mass(bx[0], bx[1], tone) else b.deco(bx[0], bx[1], tone);
}

fn wallRun(b: *Builder, f: Frame, along_u: bool, a0: f32, a1: f32, c0: f32, c1: f32, y0: f32, y1: f32, holes: []const Opening) void {
    var cur = a0;

    for (holes) |h| {
        const lo = h.c - h.w / 2;
        const hi = h.c + h.w / 2;

        for ([_][4]f32{ .{ cur, lo, y0, y1 }, .{ lo, hi, y0, y0 + h.lo }, .{ lo, hi, y0 + h.hi, y1 } }) |s| {
            if (along_u) part(b, f, s[0], c0, s[1], c1, s[2], s[3], .adobe, true) else part(b, f, c0, s[0], c1, s[1], s[2], s[3], .adobe, true);
        }

        cur = hi;
    }

    if (along_u) part(b, f, cur, c0, a1, c1, y0, y1, .adobe, true) else part(b, f, c0, cur, c1, a1, y0, y1, .adobe, true);
}

fn slab(b: *Builder, f: Frame, w: f32, d: f32, y: f32, hole: [4]f32, tone: Tone) void {
    const ua = -w / 2;
    const ub = w / 2;

    part(b, f, ua, 0, ub, hole[1], y, y + slab_t, tone, true);
    part(b, f, ua, hole[3], ub, d, y, y + slab_t, tone, true);
    part(b, f, ua, hole[1], hole[0], hole[3], y, y + slab_t, tone, true);
    part(b, f, hole[2], hole[1], ub, hole[3], y, y + slab_t, tone, true);
}

fn stair(b: *Builder, f: Frame, ua: f32, v0: f32, y0: f32, y1: f32, up: bool) void {
    const ub = ua + stair_len;
    const v1 = v0 + stair_w;
    const bx = f.box(ua, v0, ub, v1, y0, y1);
    const steps: u32 = 12;
    const du = stair_len / @as(f32, @floatFromInt(steps));
    var i: u32 = 0;

    b.solid(.{ .ramp = .{ .min = bx[0], .max = bx[1], .rise = f.rise(up) } });

    while (i < steps) : (i += 1) {
        const fi: f32 = @floatFromInt(i);
        const top = y0 + (y1 - y0) * (fi + 1) / @as(f32, @floatFromInt(steps));
        const a = if (up) ua + fi * du else ub - (fi + 1) * du;

        part(b, f, a, v0, a + du, v1, y0, top, .stair, false);
    }
}

fn trimFront(b: *Builder, f: Frame, c: f32, w: f32, ylo: f32, yhi: f32, v_out: f32, dir: f32, door: bool) void {
    const a = c - w / 2;
    const z = c + w / 2;
    const v0 = if (dir < 0) v_out - 0.1 else v_out;
    const v1 = if (dir < 0) v_out else v_out + 0.1;
    const s0 = if (dir < 0) v_out - 0.16 else v_out;
    const s1 = if (dir < 0) v_out else v_out + 0.16;

    part(b, f, a - 0.14, v0, a, v1, ylo, yhi, .frame, false);
    part(b, f, z, v0, z + 0.14, v1, ylo, yhi, .frame, false);
    part(b, f, a - 0.22, v0, z + 0.22, v1, yhi, yhi + 0.18, .frame, false);

    if (door) return;

    part(b, f, a - 0.12, s0, z + 0.12, s1, ylo - 0.1, ylo, .trim, false);
    part(b, f, a - 0.5, v0, a - 0.16, v1, ylo + 0.04, yhi - 0.04, .shutter, false);
    part(b, f, z + 0.16, v0, z + 0.5, v1, ylo + 0.04, yhi - 0.04, .shutter, false);
}

fn trimSide(b: *Builder, f: Frame, c: f32, w: f32, ylo: f32, yhi: f32, u_out: f32, dir: f32) void {
    const a = c - w / 2;
    const z = c + w / 2;
    const ua_ = if (dir < 0) u_out - 0.1 else u_out;
    const ub_ = if (dir < 0) u_out else u_out + 0.1;
    const s0 = if (dir < 0) u_out - 0.16 else u_out;
    const s1 = if (dir < 0) u_out else u_out + 0.16;

    part(b, f, ua_, a - 0.14, ub_, a, ylo, yhi, .frame, false);
    part(b, f, ua_, z, ub_, z + 0.14, ylo, yhi, .frame, false);
    part(b, f, ua_, a - 0.22, ub_, z + 0.22, yhi, yhi + 0.18, .frame, false);
    part(b, f, s0, a - 0.12, s1, z + 0.12, ylo - 0.1, ylo, .trim, false);
}

fn roofClutter(b: *Builder, f: Frame, w: f32, d: f32, y: f32) void {
    const r = b.rng.next();

    if (r < 0.55) {
        const u = w / 2 - 1.3;
        const v = 1.2;

        for ([_][2]f32{ .{ -0.4, -0.4 }, .{ 0.4, -0.4 }, .{ -0.4, 0.4 }, .{ 0.4, 0.4 } }) |o| part(b, f, u + o[0] - 0.05, v + o[1] - 0.05, u + o[0] + 0.05, v + o[1] + 0.05, y, y + 0.6, .frame, false);

        part(b, f, u - 0.55, v - 0.55, u + 0.55, v + 0.55, y + 0.6, y + 1.7, .tank, false);
        part(b, f, u - 0.18, v - 0.18, u + 0.18, v + 0.18, y + 1.7, y + 1.85, .tank, false);
    }

    if (b.rng.next() < 0.6) {
        const u = -w / 2 + 1.4 + b.rng.range(0, 1);
        const v = d / 2 + b.rng.range(-1, 1);

        part(b, f, u - 1.0, v - 0.7, u + 1.0, v + 0.7, y, y + 0.03, .rug, false);
    }

    if (b.rng.next() < 0.7) {
        const u = w / 2 - 0.9;
        const v = d - 0.9;

        part(b, f, u - 0.28, v - 0.28, u + 0.28, v + 0.28, y, y + 0.45, .pot, false);
        part(b, f, u - 0.36, v - 0.36, u + 0.36, v + 0.36, y + 0.45, y + 0.95, .leaf, false);
    }
}

pub const kit_houses = [_]struct { w: f32, d: f32, kind: Kind, blocks: []const [5]f32 }{
    .{ .w = 9.57, .d = 11.44, .kind = .kd_house_0, .blocks = &.{ .{ -4.78, -2.78, 3.72, -1.78, 5.87 }, .{ -4.78, -4.28, 3.22, -2.78, 5.87 }, .{ -4.28, -0.78, 4.22, 0.22, 5.87 }, .{ -4.28, -1.78, 3.72, -0.78, 5.87 }, .{ -3.78, 1.22, 4.72, 2.72, 5.87 }, .{ -3.78, 0.22, 4.22, 1.22, 5.87 }, .{ -3.78, -4.78, 3.22, -4.28, 5.94 }, .{ -3.28, 2.72, 4.22, 4.72, 7.50 }, .{ -2.78, 4.72, -0.28, 5.72, 7.50 }, .{ -1.78, -5.28, 2.72, -4.78, 5.94 }, .{ -0.28, 4.72, 1.72, 5.22, 3.20 }, .{ 0.72, -5.78, 2.72, -5.28, 3.20 }, .{ 4.22, 3.72, 5.22, 4.22, 3.20 }, .{ 4.22, 2.72, 4.72, 3.72, 3.20 } } },
    .{ .w = 8.88, .d = 10.99, .kind = .kd_house_1, .blocks = &.{ .{ -4.44, -2.00, 4.06, -1.00, 5.53 }, .{ -4.44, -4.50, 3.56, -2.00, 6.31 }, .{ -3.94, 1.50, 4.56, 2.50, 7.50 }, .{ -3.94, -1.00, 4.06, 1.50, 5.53 }, .{ -3.44, 2.50, 0.56, 5.50, 7.50 }, .{ -2.94, -5.00, 3.56, -4.50, 5.61 }, .{ 0.56, 2.50, 4.06, 5.00, 4.12 }, .{ 0.56, -5.50, 3.06, -5.00, 4.95 }, .{ 4.06, 2.50, 4.56, 4.50, 3.20 } } },
    .{ .w = 7.65, .d = 12.59, .kind = .kd_house_2, .blocks = &.{.{ -3.83, -6.21, 4.17, 6.29, 9.12 }} },
    .{ .w = 9.01, .d = 11.07, .kind = .kd_house_3, .blocks = &.{ .{ -4.50, -1.96, 4.00, -0.96, 2.40 }, .{ -4.50, -4.46, 3.50, -1.96, 7.38 }, .{ -4.00, 1.04, 4.50, 2.04, 7.50 }, .{ -4.00, -0.96, 4.00, 1.04, 6.91 }, .{ -3.50, 2.04, 3.50, 5.04, 7.50 }, .{ -3.50, -4.96, 3.50, -4.46, 6.88 }, .{ -3.00, 5.04, -0.00, 5.54, 5.00 }, .{ -0.00, -5.46, 3.00, -4.96, 6.35 }, .{ 3.50, 4.04, 5.00, 4.54, 3.20 }, .{ 3.50, 2.04, 4.50, 4.04, 6.75 } } },
    .{ .w = 7.78, .d = 10.20, .kind = .kd_house_4, .blocks = &.{ .{ -3.89, -4.90, 4.11, 5.10, 5.62 }, .{ -3.39, -5.40, 3.61, -4.90, 4.67 } } },
    .{ .w = 12.22, .d = 12.47, .kind = .kd_house_5, .blocks = &.{ .{ -6.11, -1.26, 4.39, -0.77, 6.18 }, .{ -6.11, -1.76, 3.89, -1.26, 6.16 }, .{ -5.61, -0.27, 5.39, 0.23, 6.88 }, .{ -5.61, -0.77, 4.89, -0.27, 6.18 }, .{ -5.61, -2.27, 3.89, -1.76, 5.16 }, .{ -5.11, 0.23, 5.89, 0.73, 6.88 }, .{ -5.11, -2.77, 3.39, -2.27, 6.16 }, .{ -4.61, 0.73, 6.39, 1.24, 6.16 }, .{ -4.61, -3.27, 2.89, -2.77, 6.16 }, .{ -4.11, 1.24, 6.39, 1.74, 6.24 }, .{ -3.61, 1.74, 5.89, 2.23, 6.24 }, .{ -3.61, -3.77, 2.39, -3.27, 6.69 }, .{ -3.11, 2.23, 5.39, 2.73, 5.78 }, .{ -3.11, -4.26, 1.89, -3.77, 6.69 }, .{ -2.61, 2.73, 3.89, 3.73, 6.88 }, .{ -2.61, -4.76, 1.39, -4.26, 5.58 }, .{ -2.11, 3.73, 3.39, 4.24, 6.88 }, .{ -2.11, -5.26, 0.89, -4.76, 5.16 }, .{ -1.61, 4.24, 2.89, 4.74, 6.18 }, .{ -1.61, -5.76, 0.39, -5.26, 3.20 }, .{ -1.11, 4.74, 2.39, 5.24, 4.31 }, .{ -1.11, -6.26, 0.39, -5.76, 3.20 }, .{ -0.61, 5.24, 1.89, 5.74, 4.31 }, .{ -0.11, 5.74, 1.39, 6.24, 3.20 }, .{ 3.89, 2.73, 4.89, 3.23, 3.20 } } },
    .{ .w = 7.80, .d = 11.05, .kind = .kd_house_6, .blocks = &.{ .{ -3.90, 2.52, 1.60, 4.52, 6.25 }, .{ -3.40, 0.52, 2.10, 2.52, 7.08 }, .{ -2.90, -0.98, 2.60, 0.52, 5.81 }, .{ -2.40, 4.52, 1.60, 5.02, 5.65 }, .{ -2.40, -2.48, 3.10, -0.98, 3.63 }, .{ -1.90, -3.98, 3.60, -2.48, 3.38 }, .{ -1.40, -4.48, 4.10, -3.98, 3.13 }, .{ -1.40, -4.98, 2.60, -4.48, 3.17 }, .{ -1.40, -5.48, 1.10, -4.98, 3.12 }, .{ -0.90, 5.02, 1.10, 5.52, 3.20 }, .{ -0.90, -5.98, -0.40, -5.48, 3.06 }, .{ 1.60, 2.52, 2.10, 3.52, 3.20 }, .{ 2.10, 0.52, 2.60, 2.02, 3.20 }, .{ 2.60, -0.98, 3.10, 0.02, 3.20 }, .{ 3.10, -2.48, 3.60, -1.48, 3.20 }, .{ 3.60, -3.98, 4.10, -2.98, 3.13 } } },
    .{ .w = 7.78, .d = 8.80, .kind = .kd_house_7, .blocks = &.{ .{ -3.89, -1.60, 2.61, -1.10, 4.12 }, .{ -3.89, -2.60, 2.11, -1.60, 4.99 }, .{ -3.39, -0.60, 3.11, -0.10, 4.12 }, .{ -3.39, -1.10, 2.61, -0.60, 4.12 }, .{ -2.89, 0.40, 3.61, 0.90, 4.12 }, .{ -2.89, -0.10, 3.11, 0.40, 4.12 }, .{ -2.89, -3.10, 1.61, -2.60, 8.09 }, .{ -2.39, 1.40, 4.11, 1.90, 6.25 }, .{ -2.39, 0.90, 3.61, 1.40, 6.25 }, .{ -2.39, -3.60, 1.61, -3.10, 8.09 }, .{ -1.89, 1.90, 3.61, 2.90, 6.25 }, .{ -1.39, 2.90, 1.61, 3.90, 6.25 }, .{ -0.89, 3.90, 0.61, 4.40, 2.40 }, .{ -0.89, -4.10, 1.11, -3.60, 3.20 }, .{ 0.11, -4.60, 1.11, -4.10, 3.20 }, .{ 1.61, 2.90, 2.61, 3.40, 2.40 }, .{ 3.61, 1.90, 4.11, 2.40, 2.40 } } },
    .{ .w = 7.50, .d = 7.50, .kind = .kd_house_8, .blocks = &.{.{ -3.75, -3.75, 4.25, 3.75, 7.75 }} },
    .{ .w = 15.48, .d = 16.00, .kind = .kd_house_9, .blocks = &.{ .{ -7.74, -1.50, -2.74, -1.00, 6.80 }, .{ -7.74, -2.00, -3.24, -1.50, 6.80 }, .{ -7.24, -1.00, -2.74, -0.50, 6.80 }, .{ -7.24, -2.50, -3.74, -2.00, 6.80 }, .{ -6.74, -0.50, -2.24, -0.00, 6.80 }, .{ -6.74, -3.00, -4.24, -2.50, 6.80 }, .{ -6.24, 0.50, -1.24, 1.00, 6.80 }, .{ -6.24, -0.00, -1.74, 0.50, 6.80 }, .{ -5.74, 1.00, -0.74, 1.50, 6.80 }, .{ -5.74, -3.50, -4.24, -3.00, 3.20 }, .{ -5.24, 1.50, -0.24, 2.00, 6.80 }, .{ -5.24, -4.00, -3.74, -3.50, 3.20 }, .{ -4.74, 2.50, 0.26, 3.00, 6.80 }, .{ -4.74, 2.00, -0.24, 2.50, 6.80 }, .{ -4.74, -4.50, -3.24, -4.00, 3.20 }, .{ -4.24, 3.00, -0.24, 3.50, 6.80 }, .{ -3.74, 3.50, -1.74, 4.50, 5.01 }, .{ -3.74, -5.00, -2.24, -4.50, 3.20 }, .{ -3.24, 4.50, -2.24, 5.00, 3.20 }, .{ -3.24, -5.50, -1.74, -5.00, 3.20 }, .{ -2.74, 5.00, -1.74, 5.50, 3.20 }, .{ -2.74, -6.00, -1.24, -5.50, 3.20 }, .{ -2.24, 6.00, 1.76, 6.50, 5.89 }, .{ -2.24, 5.50, -1.24, 6.00, 3.20 }, .{ -1.74, 6.50, 1.76, 7.00, 5.21 }, .{ -1.74, 3.50, -0.74, 4.00, 2.40 }, .{ -1.74, -6.50, -0.24, -6.00, 3.20 }, .{ -1.24, 7.00, 1.26, 7.50, 5.01 }, .{ -1.24, -7.00, 0.26, -6.50, 3.20 }, .{ -0.74, 7.50, 0.76, 8.00, 2.40 }, .{ -0.74, 5.50, 1.26, 6.00, 3.20 }, .{ -0.74, -7.50, 1.26, -7.00, 3.20 }, .{ 0.26, 5.00, 1.26, 5.50, 3.20 }, .{ 0.26, 4.50, 0.76, 5.00, 3.20 }, .{ 0.26, -8.00, 0.76, -7.50, 3.20 }, .{ 0.76, 2.50, 2.26, 4.00, 8.42 }, .{ 0.76, -6.50, 2.26, -6.00, 3.20 }, .{ 0.76, -7.00, 1.76, -6.50, 3.20 }, .{ 1.26, -6.00, 2.26, -5.50, 3.20 }, .{ 1.76, 2.00, 3.76, 2.50, 3.20 }, .{ 1.76, -5.50, 2.76, -5.00, 3.20 }, .{ 2.26, 2.50, 3.26, 3.50, 3.20 }, .{ 2.26, 1.50, 3.26, 2.00, 2.40 }, .{ 2.26, -5.00, 3.26, -4.00, 3.20 }, .{ 2.76, -4.00, 3.76, -3.50, 3.20 }, .{ 3.26, 2.50, 3.76, 3.00, 2.40 }, .{ 3.26, -3.50, 4.26, -3.00, 3.20 }, .{ 3.76, -3.00, 4.76, -2.00, 3.20 }, .{ 4.26, 1.50, 7.76, 2.50, 6.80 }, .{ 4.26, -2.00, 5.26, -1.50, 3.20 }, .{ 4.76, 2.50, 7.26, 3.00, 6.80 }, .{ 4.76, -1.00, 6.26, -0.50, 3.20 }, .{ 4.76, -1.50, 5.76, -1.00, 3.20 }, .{ 5.26, 3.00, 5.76, 4.00, 2.40 }, .{ 5.26, -0.50, 6.26, -0.00, 3.20 }, .{ 5.76, 3.00, 6.76, 3.50, 2.40 }, .{ 5.76, 1.00, 7.26, 1.50, 3.20 }, .{ 5.76, -0.00, 6.76, 0.50, 3.20 }, .{ 6.26, 0.50, 7.26, 1.00, 3.20 } } },
    .{ .w = 8.35, .d = 10.62, .kind = .kd_house_10, .blocks = &.{ .{ -4.18, -4.69, 3.82, 0.81, 7.50 }, .{ -3.68, 0.81, 2.32, 5.31, 10.14 }, .{ -1.18, -5.19, 3.82, -4.69, 7.62 }, .{ 2.32, 0.81, 4.32, 4.81, 5.62 } } },
    .{ .w = 5.94, .d = 5.88, .kind = .kd_house_11, .blocks = &.{ .{ -2.97, -0.06, 3.03, 0.44, 4.48 }, .{ -2.97, -2.06, 2.53, -0.06, 5.72 }, .{ -2.47, 0.44, 0.53, 2.44, 4.48 }, .{ -1.47, -2.56, 2.53, -2.06, 4.06 }, .{ 0.53, 0.44, 3.03, 1.94, 3.65 }, .{ 0.53, -3.06, 2.03, -2.56, 3.20 }, .{ 1.03, 1.94, 2.53, 2.44, 3.13 } } },
};

pub fn kitHouse(b: *Builder, cx: f32, cz: f32, front: [2]f32, v: usize) void {
    const k = kit_houses[v];
    const y0 = lowest(cx, cz, @max(k.w, k.d) / 2 + 0.5) + 0.4;
    const yaw = std.math.atan2(front[0], front[1]);

    b.putAt(k.kind, vec(cx, y0, cz), yaw, 1);

    for (k.blocks) |bl| {
        const r = rotBox(cx, cz, yaw, bl[0], bl[1], bl[2], bl[3]);

        b.solid(.{ .box = .{ .min = vec(r[0], y0 - 0.9, r[1]), .max = vec(r[2], y0 + bl[4] + 0.1, r[3]) } });
    }

    const f: Frame = .{ .c = .{ cx, cz }, .n = front, .r = .{ -front[1], front[0] }, .depth = k.d };
    const spot = f.at(-k.w / 2 + 0.8, -0.9);
    const door = f.at(0, -1.6);
    const roll = b.rng.next();

    town_loot.append(b.gpa, vec(door[0], terrain.height(door[0], door[1]) + 0.1, door[1])) catch {};

    if (roll < 0.35) {
        b.putAt(.kd_barrel, vec(spot[0], terrain.height(spot[0], spot[1]), spot[1]), b.rng.range(0, 6.28), 1);
    } else if (roll < 0.6) {
        b.putAt(.kd_box, vec(spot[0], terrain.height(spot[0], spot[1]), spot[1]), b.rng.range(0, 6.28), 1);
    } else if (roll < 0.8) {
        b.putAt(.kd_crate, vec(spot[0], terrain.height(spot[0], spot[1]), spot[1]), b.rng.range(0, 6.28), 1);
    }
}

fn house(b: *Builder, cx: f32, cz: f32, front: [2]f32, w: f32, d: f32, floors: u32) void {
    b.tint = @intFromFloat(@floor(b.rng.next() * 4.99));
    defer b.tint = 0;

    const f: Frame = .{ .c = .{ cx, cz }, .n = front, .r = .{ -front[1], front[0] }, .depth = d };
    const y0 = lowest(cx, cz, @max(w, d) / 2 + 0.5) + 0.4;
    const top = y0 + storey * @as(f32, @floatFromInt(floors));
    const t = wall_t;
    const cloth = b.rng.pick(Tone, &.{ .cloth_red, .cloth_blue, .cloth_yellow });
    const first_hole = [4]f32{ -w / 2 + t, d - t - stair_w, -w / 2 + t + stair_len, d - t };
    const second_hole = [4]f32{ w / 2 - t - stair_len, t, w / 2 - t, t + stair_w };
    var level: u32 = 0;

    part(b, f, -w / 2, 0, w / 2, d, y0 - 0.6, y0 + 0.12, .floor, true);

    while (level < floors) : (level += 1) {
        const yb = y0 + storey * @as(f32, @floatFromInt(level)) + (if (level == 0) @as(f32, 0.12) else slab_t);
        const ye = y0 + storey * @as(f32, @floatFromInt(level + 1));
        const side_window = [_]Opening{.{ .c = d / 2, .w = 1.0, .lo = 1.1, .hi = 2.0 }};
        const door = [_]Opening{.{ .c = 0.4, .w = 1.6, .lo = 0, .hi = 2.5 }};
        const pair = [_]Opening{ .{ .c = -w / 4, .w = 1.1, .lo = 1.0, .hi = 1.9 }, .{ .c = w / 4, .w = 1.1, .lo = 1.0, .hi = 1.9 } };
        const none = [_]Opening{};
        const front_holes: []const Opening = if (level == 0) &door else &pair;
        const back_holes: []const Opening = if (level == 0) &none else &pair;

        wallRun(b, f, true, -w / 2, w / 2, 0, t, yb, ye, front_holes);
        wallRun(b, f, true, -w / 2, w / 2, d - t, d, yb, ye, back_holes);
        wallRun(b, f, false, t, d - t, -w / 2, -w / 2 + t, yb, ye, &side_window);
        wallRun(b, f, false, t, d - t, w / 2 - t, w / 2, yb, ye, &side_window);

        if (level == 0) stair(b, f, first_hole[0], first_hole[1], yb, ye + slab_t, true) else stair(b, f, second_hole[0], second_hole[1], yb, ye + slab_t, false);

        const hole = if (level == 0) first_hole else second_hole;

        slab(b, f, w, d, ye, hole, if (level + 1 == floors) .adobe else .floor);
    }

    for ([_][4]f32{ .{ -w / 2, 0, w / 2, 0.25 }, .{ -w / 2, d - 0.25, w / 2, d }, .{ -w / 2, 0.25, -w / 2 + 0.25, d - 0.25 }, .{ w / 2 - 0.25, 0.25, w / 2, d - 0.25 } }) |p| {
        part(b, f, p[0], p[1], p[2], p[3], top + slab_t, top + slab_t + 0.85, .adobe, true);
        part(b, f, p[0] - 0.06, p[1] - 0.06, p[2] + 0.06, p[3] + 0.06, top + slab_t + 0.85, top + slab_t + 0.97, .trim, false);
    }

    part(b, f, -w / 2 - 0.07, -0.07, w / 2 + 0.07, 0.0, y0 - 0.2, y0 + 0.5, .plinth, false);
    part(b, f, -w / 2 - 0.07, d, w / 2 + 0.07, d + 0.07, y0 - 0.2, y0 + 0.5, .plinth, false);
    part(b, f, -w / 2 - 0.07, 0, -w / 2, d, y0 - 0.2, y0 + 0.5, .plinth, false);
    part(b, f, w / 2, 0, w / 2 + 0.07, d, y0 - 0.2, y0 + 0.5, .plinth, false);

    var lv: u32 = 0;

    while (lv < floors) : (lv += 1) {
        const yb = y0 + storey * @as(f32, @floatFromInt(lv)) + (if (lv == 0) @as(f32, 0.12) else slab_t);

        if (lv == 0) {
            trimFront(b, f, 0.4, 1.6, yb, yb + 2.5, 0, -1, true);
        } else {
            trimFront(b, f, -w / 4, 1.1, yb + 1.0, yb + 1.9, 0, -1, false);
            trimFront(b, f, w / 4, 1.1, yb + 1.0, yb + 1.9, 0, -1, false);
            trimFront(b, f, -w / 4, 1.1, yb + 1.0, yb + 1.9, d, 1, false);
            trimFront(b, f, w / 4, 1.1, yb + 1.0, yb + 1.9, d, 1, false);
        }

        trimSide(b, f, d / 2, 1.0, yb + 1.1, yb + 2.0, -w / 2, -1);
        trimSide(b, f, d / 2, 1.0, yb + 1.1, yb + 2.0, w / 2, 1);
    }

    roofClutter(b, f, w, d, top + slab_t);

    var u: f32 = -w / 2 + 0.6;

    while (u < w / 2 - 0.4) : (u += 0.9) {
        part(b, f, u - 0.11, -0.42, u + 0.11, 0.05, top - 0.3, top - 0.08, .beam, false);
        part(b, f, u - 0.11, d - 0.05, u + 0.11, d + 0.42, top - 0.3, top - 0.08, .beam, false);
    }

    part(b, f, -0.75, -1.0, 1.55, 0, y0 + 2.7, y0 + 2.8, cloth, false);

    const corner = f.at(w / 2 - 1.0, d - 1.0);
    const jar_spot = f.at(-w / 2 + 0.9, 1.0);

    b.putAt(if (b.rng.next() < 0.5) .arena_crate_large else .arena_crate_small, vec(corner[0], y0 + 0.12, corner[1]), b.rng.range(0, 6.28), 1);
    b.putAt(b.rng.pick(Kind, &.{ .arena_jar_1, .arena_jar_2, .arena_jar_3 }), vec(jar_spot[0], y0 + 0.12, jar_spot[1]), b.rng.range(0, 6.28), 1);

    const mid = f.at(0.5, d / 2);
    const roof_mid = f.at(1.0, d / 2 + 0.5);

    town_loot.append(b.gpa, vec(mid[0], (if (floors > 1) y0 + storey + slab_t else y0 + 0.12), mid[1])) catch {};
    town_loot.append(b.gpa, vec(roof_mid[0], top + slab_t, roof_mid[1])) catch {};
}

pub fn coverNode(b: *Builder, x: f32, z: f32, yaw: f32) void {
    b.putAt(.kd_box, vec(x, terrain.height(x, z), z), yaw, 1);

    const n = 4 + @as(u32, @intFromFloat(b.rng.next() * 5.99));
    var i: u32 = 0;

    while (i < n) : (i += 1) {
        const a = yaw + 0.9 + @as(f32, @floatFromInt(i)) * 0.85 + b.rng.range(-0.2, 0.2);
        const d = b.rng.range(2.0, 3.6);
        const px = x + @sin(a) * d;
        const pz = z + @cos(a) * d;

        b.putAt(b.rng.pick(Kind, &.{ .kd_crate, .kd_barrel, .kd_barrel, .kd_box, .kd_chest, .kd_crate }), vec(px, terrain.height(px, pz), pz), b.rng.range(0, 6.28), b.rng.range(0.9, 1.1));
    }
}

pub fn airstripPocket(b: *Builder) void {
    const hx: f32 = 40;
    const hz: f32 = -200;
    const y = lowest(hx, hz, 11) + 0.4;

    b.putAt(.dk_hangar, vec(hx, y, hz), std.math.pi, 1);
    b.ghost = true;
    b.mass(vec(hx - 11, y, hz - 7.4), vec(hx + 11, y + 3.2, hz - 6.6), .rust);
    b.mass(vec(hx - 11, y, hz + 6.6), vec(hx + 11, y + 3.2, hz + 7.4), .rust);
    b.mass(vec(hx - 11.4, y, hz - 7), vec(hx - 10.8, y + 6.6, hz + 7), .rust);
    b.ghost = false;

    const containers = [_]Kind{ .mil_container_sand, .mil_container_teal, .mil_container_rust };

    for ([_][3]f32{ .{ 62, -178, 0 }, .{ 62, -224, 0.1 }, .{ 30, -178, 1.57 } }, 0..) |c, i| {
        b.putAt(containers[i % containers.len], vec(c[0], terrain.height(c[0], c[1]), c[1]), c[2], 1);
    }

    coverNode(b, 70, -190, 0.4);
    coverNode(b, 66, -212, 2.0);
    coverNode(b, 100, -150, 1.2);
    coverNode(b, 150, -150, 3.4);
    coverNode(b, 48, -165, 0.2);
    b.putAt(.kd_tent_0, vec(25, terrain.height(25, -168), -168), 0.3, 1);
    b.putAt(.dk_truck_wreck, vec(80, terrain.height(80, -176), -176), 0.8, 1);
    b.putAt(.dk_water_tower, vec(20, lowest(20, -222, 2.4) + 0.4, -222), 0, 1);
}

pub fn ruinsPocket(b: *Builder) void {
    const cx: f32 = -130;
    const cz: f32 = -85;
    const shells = [_][3]f32{ .{ -14, -10, 0 }, .{ 10, -14, 0.3 }, .{ -6, 14, 1.2 }, .{ 16, 10, 2.0 }, .{ 0, 0, 0.7 } };

    for (shells) |sh| {
        const x = cx + sh[0];
        const z = cz + sh[1];

        kitHouse(b, x, z, .{ @sin(sh[2]), @cos(sh[2]) }, 11);
    }

    coverNode(b, cx - 2, cz - 20, 0.5);
    coverNode(b, cx + 22, cz - 2, 2.1);
    coverNode(b, cx - 22, cz + 6, 4.0);

    for ([_][2]f32{ .{ -26, -20 }, .{ 24, 22 }, .{ -18, 26 }, .{ 28, -22 } }) |o| {
        const x = cx + o[0];
        const z = cz + o[1];

        b.putAt(b.rng.pick(Kind, &.{ .kd_rock_0, .kd_rock_2, .kd_rock_1 }), vec(x, lowest(x, z, 2) + 0.2, z), b.rng.range(0, 6.28), 1.4);
        b.putAt(.dk_drift_1, vec(x + 3, lowest(x + 3, z + 2, 3) + 0.15, z + 2), b.rng.range(0, 6.28), 1);
    }

    b.put(.kd_palm_0, cx + 6, cz + 4, 0.4, 1);
    b.put(.kd_palm_2, cx + 8, cz + 6, 1.4, 1);

    var gx: f32 = -10;

    while (gx <= 10) : (gx += 4) {
        var gz: f32 = -6;

        while (gz <= 6) : (gz += 4) {
            if (b.rng.next() < 0.45) continue;

            const px = cx + gx;
            const pz = cz + gz;

            b.putAt(.kd_patch_0, vec(px, terrain.height(px, pz) - 0.02, pz), b.rng.range(-0.08, 0.08), 1);
        }
    }

    for ([_][3]f32{ .{ -9, -4, 0 }, .{ 9, 5, 3.14 }, .{ 2, -16, 1.57 } }) |o| {
        const px = cx + o[0];
        const pz = cz + o[1];

        b.putAt(.kd_tent_0, vec(px, terrain.height(px, pz), pz), o[2], 1);
    }

    b.putAt(.kd_crate, vec(cx - 4, terrain.height(cx - 4, cz + 8), cz + 8), 2.4, 1);
    b.putAt(.kd_bench, vec(cx + 4, terrain.height(cx + 4, cz - 7), cz - 7), 0.2, 1);
    b.putAt(.kd_lantern, vec(cx - 12, terrain.height(cx - 12, cz), cz), 0, 1);
    b.putAt(.kd_lantern, vec(cx + 12, terrain.height(cx + 12, cz), cz), std.math.pi, 1);
    b.putAt(.kd_tent_1, vec(cx + 2, terrain.height(cx + 2, cz + 22), cz + 22), 0, 1);
}

pub fn oasisPocket(b: *Builder) void {
    const ox = terrain.oasis[0];
    const oz = terrain.oasis[1];

    for ([_][3]f32{ .{ 26, 0, 1.57 }, .{ 20, 2.2, 0.6 }, .{ 24, 4.4, 2.4 }, .{ 22, 3.3, 4.2 } }) |t| {
        const x = ox + @cos(t[1]) * t[0];
        const z = oz + @sin(t[1]) * t[0];

        b.putAt(.kd_tent_0, vec(x, terrain.height(x, z), z), t[2], 1);
    }

    for ([_][2]f32{ .{ 22, 1.1 }, .{ 23, 3.0 }, .{ 21, 5.4 } }) |t| {
        const x = ox + @cos(t[1]) * t[0];
        const z = oz + @sin(t[1]) * t[0];

        b.putAt(b.rng.pick(Kind, &.{ .kd_box, .kd_crate }), vec(x, terrain.height(x, z), z), std.math.atan2(ox - x, oz - z), 1);
    }

    coverNode(b, ox + 28, oz - 10, 0.6);
    coverNode(b, ox - 26, oz + 12, 3.3);
}

pub fn viewOpen(p: Vec3, yaw: f32) bool {
    var d: f32 = 0.8;

    while (d <= 14) : (d += 1.2) {
        if (clearance(vec(p.x + @sin(yaw) * d, p.y, p.z + @cos(yaw) * d)) < 0.6) return false;
    }

    return true;
}

pub fn clearance(p: Vec3) f32 {
    var best: f32 = 1e9;

    for (pieces) |piece| {
        const bb = piece.shape.bounds();

        if (bb.max.y < p.y + 0.4 or bb.min.y > p.y + 2.2) continue;

        const dx = @max(bb.min.x - p.x, 0, p.x - bb.max.x);
        const dz = @max(bb.min.z - p.z, 0, p.z - bb.max.z);

        best = @min(best, @sqrt(dx * dx + dz * dz));
    }

    for (structures) |st| {
        if (st.max.y < p.y + 0.4 or st.min.y > p.y + 3.4) continue;

        const dx = @max(st.min.x - p.x, 0, p.x - st.max.x);
        const dz = @max(st.min.z - p.z, 0, p.z - st.max.z);

        best = @min(best, @sqrt(dx * dx + dz * dz));
    }

    for (placements) |pl| {
        if (props.info(pl.kind).collide == .none and props.info(pl.kind).group != .tree) continue;

        best = @min(best, @sqrt((pl.pos.x - p.x) * (pl.pos.x - p.x) + (pl.pos.z - p.z) * (pl.pos.z - p.z)) - 1.5);
    }

    for (vehicle_spots) |v| best = @min(best, @sqrt((v.pos.x - p.x) * (v.pos.x - p.x) + (v.pos.z - p.z) * (v.pos.z - p.z)) - 3);

    return best;
}

pub fn openYaw(p: Vec3) struct { yaw: f32, reach: f32 } {
    var best_yaw: f32 = 0;
    var best: f32 = -1;
    var i: u32 = 0;

    while (i < 16) : (i += 1) {
        const yaw = @as(f32, @floatFromInt(i)) * (std.math.pi / 8.0);
        const dir = vec(@sin(yaw), 0, @cos(yaw));
        const reach = if (movement.raycast(pieces, p.add(.{ .y = 1.6 }), dir, 45)) |h| h.t else 45;

        if (reach > best) {
            best = reach;
            best_yaw = yaw;
        }
    }

    return .{ .yaw = best_yaw, .reach = best };
}

pub fn parkClear(gpa: std.mem.Allocator) void {
    var kept: std.ArrayList(Spot) = .empty;

    for (vehicle_spots) |v| {
        var ok = true;

        for (pieces) |piece| {
            const bb = piece.shape.bounds();

            if (bb.max.y < v.pos.y + 0.4) continue;

            if (v.pos.x > bb.min.x - 2.5 and v.pos.x < bb.max.x + 2.5 and v.pos.z > bb.min.z - 2.5 and v.pos.z < bb.max.z + 2.5) ok = false;
        }

        if (ok) kept.append(gpa, v) catch {};
    }

    vehicle_spots = kept.toOwnedSlice(gpa) catch vehicle_spots;
}
pub const AutoSpots = struct {
    loot: usize = 40,
    vehicles: usize = 6,
    seed: u64 = 777,
};

pub fn autoSpots(gpa: std.mem.Allocator, opt: AutoSpots) void {
    spawns = &.{};
    spawn_yaws = &.{};
    safeSpawns(gpa);

    var r: Rng = .{ .state = opt.seed };
    var anchors: std.ArrayList(Vec3) = .empty;
    var loot: std.ArrayList(Vec3) = .empty;
    var parked: std.ArrayList(Spot) = .empty;
    var tries: u32 = 0;

    while (tries < 8000 and (loot.items.len < opt.loot or parked.items.len < opt.vehicles)) : (tries += 1) {
        const x = r.range(-terrain.play + 10, terrain.play - 10);
        const z = r.range(-terrain.play + 10, terrain.play - 10);
        const p = vec(x, terrain.height(x, z), z);

        if (1 - terrain.normal(x, z).y > 0.3) continue;

        const room = clearance(p);

        if (parked.items.len < opt.vehicles and room > 6) {
            parked.append(gpa, .{ .pos = p, .yaw = r.range(0, std.math.tau) }) catch {};

            continue;
        }

        if (loot.items.len < opt.loot and room > 1.2) loot.append(gpa, p) catch {};
    }

    var i: u32 = 0;

    while (i < 24) : (i += 1) {
        const x = r.range(-terrain.play * 0.8, terrain.play * 0.8);
        const z = r.range(-terrain.play * 0.8, terrain.play * 0.8);

        anchors.append(gpa, vec(x, terrain.height(x, z) + r.range(9, 16), z)) catch {};
    }

    weapon_spots = loot.toOwnedSlice(gpa) catch &.{};
    vehicle_spots = parked.toOwnedSlice(gpa) catch &.{};
    drone_anchors = anchors.toOwnedSlice(gpa) catch &.{};

    if (spawns.len >= 3) return;

    const corner = terrain.play * 0.6;
    const fixed = [_]Vec3{ vec(corner, 0, corner), vec(-corner, 0, -corner), vec(corner, 0, -corner), vec(-corner, 0, corner) };
    const yaws = [_]f32{ -2.356, 0.785, -0.785, 2.356 };
    var list: [4]Vec3 = undefined;

    for (fixed, 0..) |p, k| list[k] = vec(p.x, terrain.height(p.x, p.z), p.z);

    spawns = gpa.dupe(Vec3, &list) catch &.{};
    spawn_yaws = gpa.dupe(f32, &yaws) catch &.{};
}

pub fn safeSpawns(gpa: std.mem.Allocator) void {
    var list: std.ArrayList(Vec3) = .empty;
    var yaws: std.ArrayList(f32) = .empty;
    var r: Rng = .{ .state = 4242 };
    var tries: u32 = 0;

    while (tries < 4000 and list.items.len < 10) : (tries += 1) {
        const x = r.range(-terrain.play + 14, terrain.play - 14);
        const z = r.range(-terrain.play + 14, terrain.play - 14);
        const p = vec(x, terrain.height(x, z), z);

        if (1 - terrain.normal(x, z).y > 0.25 or terrain.oasisDistance(x, z) < 15) continue;

        if (clearance(p) < 4) continue;

        var spread = true;

        for (list.items) |q| {
            if (q.sub(p).length() < 22) spread = false;
        }

        if (!spread) continue;

        const view = openYaw(p);

        if (view.reach < 18) continue;

        list.append(gpa, p) catch {};
        yaws.append(gpa, view.yaw) catch {};
    }

    if (list.items.len < 3) return;

    spawns = list.toOwnedSlice(gpa) catch spawns;
    spawn_yaws = yaws.toOwnedSlice(gpa) catch spawn_yaws;
}

pub fn reset(gpa: std.mem.Allocator) void {
    gpa.free(placements);
    gpa.free(pieces);
    gpa.free(structures);
    placements = &.{};
    pieces = &.{};
    structures = &.{};
    spawns = &.{};
    spawn_yaws = &.{};
    drone_anchors = &.{};
    weapon_spots = &.{};
    vehicle_spots = &.{};
    capture_points = &.{};
    town_loot = .empty;
    kit_loot = .empty;
    pocket_spawns = .empty;
    conquest_points = .empty;
    hangar_count = 0;
    pane_n = 0;
    panes = &.{};
    @import("grid.zig").reset();
}

pub fn build(gpa: std.mem.Allocator) void {
    var b: Builder = .{ .gpa = gpa };

    hangar_count = 0;

    const def = registry.current();

    if (def) |d| d.build(&b) else switch (terrain.current) {
        .town => {
            roads(&b);
            town(&b);
            nature(&b);
        },
        .valley => valleyNature(&b),
        .facility => facility(&b),
        .conquest => conquestMap(&b),
        .prism => prismMap(&b),
        .courtyard => courtyardMap(&b),
        else => {},
    }

    walls(&b);

    placements = b.placed.toOwnedSlice(gpa) catch &.{};
    pieces = b.solids.toOwnedSlice(gpa) catch &.{};
    structures = b.masses.toOwnedSlice(gpa) catch &.{};
    terrain.bakeHeights(gpa);

    if (def) |d| {
        d.spots(gpa);

        return;
    }

    if (terrain.current == .prism) {
        prismSpots(gpa);

        return;
    }

    if (terrain.current == .courtyard) {
        courtyardSpots(gpa);

        return;
    }

    if (terrain.current == .facility) {
        facilitySpots(gpa);

        return;
    }

    if (terrain.current == .conquest) {
        conquestSpots(gpa, &b);

        return;
    }

    if (terrain.current == .valley) {
        valleySpots(gpa);
        parkClear(gpa);

        return;
    }

    if (terrain.current != .town) {
        roadside(gpa);

        return;
    }

    const spawn_list = [_]Vec3{ vec(0, 0, 44), vec(0, 0, -44), vec(44, 0, 0), vec(-44, 0, 0), vec(16, 0, 16), vec(-16, 0, -16) };
    const yaw_list = [_]f32{ std.math.pi, 0, -half_pi, half_pi, -2.356, 0.785 };

    spawns = gpa.dupe(Vec3, &spawn_list) catch &.{};
    spawn_yaws = gpa.dupe(f32, &yaw_list) catch &.{};

    var anchors: std.ArrayList(Vec3) = .empty;
    var spots: std.ArrayList(Vec3) = .empty;
    var r: Rng = .{ .state = 99 };
    var i: u32 = 0;

    while (i < 24) : (i += 1) {
        const x = r.range(-80, 80);
        const z = r.range(-80, 80);

        anchors.append(gpa, vec(x, terrain.height(x, z) + r.range(9, 16), z)) catch {};
    }

    const spot_list = [_][2]f32{ .{ 4, 4 }, .{ -4, -4 }, .{ 36, 4 }, .{ -36, -4 }, .{ 4, 36 }, .{ -4, -36 }, .{ 20, 20 }, .{ -20, 20 }, .{ 20, -20 }, .{ -20, -20 }, .{ 70, 10 }, .{ -70, -10 }, .{ 10, 70 }, .{ -10, -70 }, .{ 60, 60 }, .{ -60, -60 } };

    for (spot_list) |s| spots.append(gpa, vec(s[0], terrain.height(s[0], s[1]), s[1])) catch {};

    var parked: std.ArrayList(Spot) = .empty;
    var t: f32 = -44;

    while (t <= 44) : (t += 9) {
        for ([_]f32{ -32, 0, 32 }) |line| {
            if (@abs(t - line) < 8) continue;

            const x = line - terrain.road_half + 2.4;
            const z = t + 2;

            parked.append(gpa, .{ .pos = vec(x, terrain.height(x, z), z), .yaw = if (@mod(t, 18) < 9) 0 else std.math.pi }) catch {};
        }
    }

    var d: f32 = 60;

    while (d <= 92) : (d += 8) {
        parked.append(gpa, .{ .pos = vec(4.5, terrain.height(4.5, d), d), .yaw = 0 }) catch {};
        parked.append(gpa, .{ .pos = vec(-d, terrain.height(-d, -4.5), -4.5), .yaw = half_pi }) catch {};
    }

    vehicle_spots = parked.toOwnedSlice(gpa) catch &.{};
    drone_anchors = anchors.toOwnedSlice(gpa) catch &.{};
    weapon_spots = spots.toOwnedSlice(gpa) catch &.{};
}

fn onRoad(z: f32, offset: f32) Vec3 {
    const x = terrain.roadLine(z) + offset;

    return vec(x, terrain.height(x, z), z);
}

pub fn roadside(gpa: std.mem.Allocator) void {
    var spawn_list: std.ArrayList(Vec3) = .empty;
    var yaw_list: std.ArrayList(f32) = .empty;
    var spots: std.ArrayList(Vec3) = .empty;
    var anchors: std.ArrayList(Vec3) = .empty;
    var parked: std.ArrayList(Spot) = .empty;
    var z: f32 = -78;
    var i: u32 = 0;

    while (z <= 78) : ({
        z += 13;
        i += 1;
    }) {
        const side: f32 = if (i % 2 == 0) 1 else -1;
        const ahead = terrain.roadLine(z + 1) - terrain.roadLine(z);
        const yaw = std.math.atan2(ahead, 1);

        spots.append(gpa, onRoad(z, side * 3)) catch {};
        anchors.append(gpa, onRoad(z, side * 20).add(.{ .y = 12 })) catch {};
        parked.append(gpa, .{ .pos = onRoad(z + 4, side * (terrain.road_half - 1.6)), .yaw = if (side > 0) yaw else yaw + std.math.pi }) catch {};
        parked.append(gpa, .{ .pos = onRoad(z - 4, -side * (terrain.road_half - 1.6)), .yaw = if (side > 0) yaw + std.math.pi else yaw }) catch {};

        if (i % 3 == 0) {
            spawn_list.append(gpa, onRoad(z, -side * 2)) catch {};
            yaw_list.append(gpa, if (z > 0) std.math.pi else 0) catch {};
        }
    }

    spawns = spawn_list.toOwnedSlice(gpa) catch &.{};
    spawn_yaws = yaw_list.toOwnedSlice(gpa) catch &.{};
    weapon_spots = spots.toOwnedSlice(gpa) catch &.{};
    drone_anchors = anchors.toOwnedSlice(gpa) catch &.{};
    vehicle_spots = parked.toOwnedSlice(gpa) catch &.{};
}

const fx_out: f32 = 56;
const fz_out: f32 = 44;
const hall_x: f32 = 30;
const hall_z: f32 = 26;
const hall_h: f32 = 16;
const deck: f32 = 5;
const deck_w: f32 = 4;
const fwall: f32 = 0.6;

fn fbox(b: *Builder, x0: f32, y0: f32, z0: f32, x1: f32, y1: f32, z1: f32, tone: Tone) void {
    b.mass(vec(@min(x0, x1), @min(y0, y1), @min(z0, z1)), vec(@max(x0, x1), @max(y0, y1), @max(z0, z1)), tone);
}

fn fdeco(b: *Builder, x0: f32, y0: f32, z0: f32, x1: f32, y1: f32, z1: f32, tone: Tone) void {
    b.deco(vec(@min(x0, x1), @min(y0, y1), @min(z0, z1)), vec(@max(x0, x1), @max(y0, y1), @max(z0, z1)), tone);
}

fn wallX(b: *Builder, x: f32, z0: f32, z1: f32, h: f32, doors: []const [2]f32, face: f32) void {
    var z = z0;

    for (doors) |d| {
        if (d[0] > z) wallSegX(b, x, z, d[0], 0, h, face);

        wallSegX(b, x, d[0], d[1], 4.6, h, face);
        hazardFrameX(b, x, d[0], d[1], face);
        z = d[1];
    }

    if (z < z1) wallSegX(b, x, z, z1, 0, h, face);
}

fn wallZ(b: *Builder, z: f32, x0: f32, x1: f32, h: f32, doors: []const [2]f32, face: f32) void {
    var x = x0;

    for (doors) |d| {
        if (d[0] > x) wallSegZ(b, z, x, d[0], 0, h, face);

        wallSegZ(b, z, d[0], d[1], 4.6, h, face);
        hazardFrameZ(b, z, d[0], d[1], face);
        x = d[1];
    }

    if (x < x1) wallSegZ(b, z, x, x1, 0, h, face);
}

fn wallSegX(b: *Builder, x: f32, z0: f32, z1: f32, y0: f32, y1: f32, face: f32) void {
    fbox(b, x - fwall / 2, y0, z0, x + fwall / 2, y1, z1, .f_grey);

    if (y0 > 0.1) return;

    const f = x + face * (fwall / 2 + 0.03);

    fdeco(b, f, 0, z0, f + face * 0.04, 0.45, z1, .f_black);
    fdeco(b, f, 0.45, z0, f + face * 0.04, @min(6, y1), z1, .f_mint);
    fdeco(b, f, @min(6, y1) - 0.12, z0, f + face * 0.05, @min(6, y1), z1, .f_mint_dark);

    var z = z0 + 2;

    while (z < z1 - 0.5) : (z += 4) fdeco(b, f, 0.45, z - 0.04, f + face * 0.06, @min(6, y1) - 0.12, z + 0.04, .f_mint_dark);
}

fn wallSegZ(b: *Builder, z: f32, x0: f32, x1: f32, y0: f32, y1: f32, face: f32) void {
    fbox(b, x0, y0, z - fwall / 2, x1, y1, z + fwall / 2, .f_grey);

    if (y0 > 0.1) return;

    const f = z + face * (fwall / 2 + 0.03);

    fdeco(b, x0, 0, f, x1, 0.45, f + face * 0.04, .f_black);
    fdeco(b, x0, 0.45, f, x1, @min(6, y1), f + face * 0.04, .f_mint);
    fdeco(b, x0, @min(6, y1) - 0.12, f, x1, @min(6, y1), f + face * 0.05, .f_mint_dark);

    var x = x0 + 2;

    while (x < x1 - 0.5) : (x += 4) fdeco(b, x - 0.04, 0.45, f, x + 0.04, @min(6, y1) - 0.12, f + face * 0.06, .f_mint_dark);
}

fn hazardFrameX(b: *Builder, x: f32, z0: f32, z1: f32, face: f32) void {
    for ([_]f32{ face, -face }) |side| {
        const f = x + side * (fwall / 2 + 0.02);
        var z = z0;
        var k: u32 = 0;

        while (z < z1) : ({
            z += 0.5;
            k += 1;
        }) fdeco(b, f, 4.6, z, f + side * 0.05, 5.0, @min(z + 0.5, z1), if (k % 2 == 0) .f_hazard else .f_black);

        fdeco(b, f, 0, z0 - 0.25, f + side * 0.05, 4.6, z0, .f_hazard);
        fdeco(b, f, 0, z1, f + side * 0.05, 4.6, z1 + 0.25, .f_hazard);
    }
}

fn hazardFrameZ(b: *Builder, z: f32, x0: f32, x1: f32, face: f32) void {
    for ([_]f32{ face, -face }) |side| {
        const f = z + side * (fwall / 2 + 0.02);
        var x = x0;
        var k: u32 = 0;

        while (x < x1) : ({
            x += 0.5;
            k += 1;
        }) fdeco(b, x, 4.6, f, @min(x + 0.5, x1), 5.0, f + side * 0.05, if (k % 2 == 0) .f_hazard else .f_black);

        fdeco(b, x0 - 0.25, 0, f, x0, 4.6, f + side * 0.05, .f_hazard);
        fdeco(b, x1, 0, f, x1 + 0.25, 4.6, f + side * 0.05, .f_hazard);
    }
}

fn crate(b: *Builder, x: f32, z: f32, s: f32, y: f32, tone: Tone) void {
    _ = tone;

    b.putAt(.int_crate, vec(x, y, z), @mod(x * 0.7 + z * 0.3, 0.4) - 0.2, s / 1.2);
}

fn container(b: *Builder, x: f32, z: f32, along_x: bool, tone: Tone) void {
    b.putAt(if (tone == .f_container_red) .mil_container_rust else .mil_container_teal, vec(x, 0, z), if (along_x) 0 else half_pi, 1);
}

fn barrier(b: *Builder, x: f32, z: f32, along_x: bool) void {
    const l: f32 = 3;
    const ex = if (along_x) l / 2 else 0.3;
    const ez = if (along_x) 0.3 else l / 2;

    fbox(b, x - ex, 0, z - ez, x + ex, 1.1, z + ez, .f_grey_dark);

    var k: f32 = -l / 2;
    var i: u32 = 0;

    while (k < l / 2) : ({
        k += 0.5;
        i += 1;
    }) {
        const tone: Tone = if (i % 2 == 0) .f_hazard else .f_black;

        if (along_x) fdeco(b, x + k, 0.75, z - ez - 0.03, x + k + 0.5, 0.95, z + ez + 0.03, tone) else fdeco(b, x - ex - 0.03, 0.75, z + k, x + ex + 0.03, 0.95, z + k + 0.5, tone);
    }
}

fn pillar(b: *Builder, x: f32, z: f32) void {
    fbox(b, x - 0.6, 0, z - 0.6, x + 0.6, hall_h, z + 0.6, .f_grey_dark);

    var y: f32 = 0;
    var i: u32 = 0;

    while (y < 1.6) : ({
        y += 0.4;
        i += 1;
    }) fdeco(b, x - 0.63, y, z - 0.63, x + 0.63, y + 0.4, z + 0.63, if (i % 2 == 0) .f_hazard else .f_black);

    fdeco(b, x - 0.64, 3.2, z - 0.64, x + 0.64, 3.5, z + 0.64, .f_light);
}

fn rail(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32, y: f32) void {
    fbox(b, x0, y, z0, x1, y + 1.1, z1, .f_rail);
}

fn railDeco(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32, y: f32) void {
    const along_x = (x1 - x0) > (z1 - z0);

    b.solid(.{ .box = .{ .min = vec(@min(x0, x1), y, @min(z0, z1)), .max = vec(@max(x0, x1), y + 1.1, @max(z0, z1)) } });
    fdeco(b, x0, y + 1.0, z0, x1, y + 1.1, z1, .f_rail);
    fdeco(b, x0, y + 0.68, z0, x1, y + 0.74, z1, .f_rail);
    fdeco(b, x0, y + 0.36, z0, x1, y + 0.42, z1, .f_rail);
    fdeco(b, x0, y, z0, x1, y + 0.14, z1, .f_hazard);

    if (along_x) {
        var x = @min(x0, x1);

        while (x <= @max(x0, x1)) : (x += 1.2) fdeco(b, x - 0.05, y, @min(z0, z1) - 0.02, x + 0.05, y + 1.1, @max(z0, z1) + 0.02, .f_rail);
    } else {
        var z = @min(z0, z1);

        while (z <= @max(z0, z1)) : (z += 1.2) fdeco(b, @min(x0, x1) - 0.02, y, z - 0.05, @max(x0, x1) + 0.02, y + 1.1, z + 0.05, .f_rail);
    }
}

fn deckStrip(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32) void {
    fbox(b, x0, deck - 0.35, z0, x1, deck, z1, .f_metal);
    fdeco(b, x0, deck - 0.55, z0, x1, deck - 0.35, z1, .f_ceiling);
}

fn stairs(b: *Builder, x0: f32, x1: f32, z0: f32, z1: f32, up: geom.Rise) void {
    b.solid(.{ .ramp = .{ .min = vec(x0, 0, z0), .max = vec(x1, deck, z1), .rise = up } });

    const steps: u32 = 14;
    var i: u32 = 0;

    while (i < steps) : (i += 1) {
        const fi: f32 = @floatFromInt(i);
        const t0 = fi / @as(f32, @floatFromInt(steps));
        const t1 = (fi + 1) / @as(f32, @floatFromInt(steps));
        const y = deck * t1;

        switch (up) {
            .pos_z => fdeco(b, x0, 0, z0 + (z1 - z0) * t0, x1, y, z0 + (z1 - z0) * t1, if (i % 2 == 0) .f_metal else .f_grey_dark),
            .neg_z => fdeco(b, x0, 0, z1 - (z1 - z0) * t1, x1, y, z1 - (z1 - z0) * t0, if (i % 2 == 0) .f_metal else .f_grey_dark),
            .pos_x => fdeco(b, x0 + (x1 - x0) * t0, 0, z0, x0 + (x1 - x0) * t1, y, z1, if (i % 2 == 0) .f_metal else .f_grey_dark),
            .neg_x => fdeco(b, x1 - (x1 - x0) * t1, 0, z0, x1 - (x1 - x0) * t0, y, z1, if (i % 2 == 0) .f_metal else .f_grey_dark),
        }
    }

    var k: u32 = 0;

    while (k <= steps) : (k += 2) {
        const fk: f32 = @floatFromInt(k);
        const t = fk / @as(f32, @floatFromInt(steps));
        const top = deck * t + 1.0;

        switch (up) {
            .pos_z, .neg_z => {
                const z = if (up == .pos_z) z0 + (z1 - z0) * t else z1 - (z1 - z0) * t;

                fdeco(b, x0 - 0.05, deck * t, z - 0.04, x0 + 0.03, top, z + 0.04, .f_rail);
                fdeco(b, x1 - 0.03, deck * t, z - 0.04, x1 + 0.05, top, z + 0.04, .f_rail);
            },
            .pos_x, .neg_x => {
                const x = if (up == .pos_x) x0 + (x1 - x0) * t else x1 - (x1 - x0) * t;

                fdeco(b, x - 0.04, deck * t, z0 - 0.05, x + 0.04, top, z0 + 0.03, .f_rail);
                fdeco(b, x - 0.04, deck * t, z1 - 0.03, x + 0.04, top, z1 + 0.05, .f_rail);
            },
        }
    }
}

fn floorLines(b: *Builder) void {
    fdeco(b, -fx_out, -0.3, -fz_out, fx_out, 0.0, fz_out, .f_floor);

    var x: f32 = -hall_x + 2;

    while (x < hall_x - 1) : (x += 4) fdeco(b, x - 0.02, 0.0, -hall_z, x + 0.02, 0.012, hall_z, .f_floor_dark);

    var z: f32 = -hall_z + 2;

    while (z < hall_z - 1) : (z += 4) fdeco(b, -hall_x, 0.0, z - 0.02, hall_x, 0.012, z + 0.02, .f_floor_dark);

    for ([_]f32{ -9, 9 }) |lx| fdeco(b, lx - 0.15, 0.0, -hall_z + 6, lx + 0.15, 0.02, hall_z - 6, .f_line);
    for ([_]f32{ -14, 14 }) |lz| fdeco(b, -hall_x + 6, 0.0, lz - 0.15, hall_x - 6, 0.02, lz + 0.15, .f_line);

    var k: f32 = -6;
    var i: u32 = 0;

    while (k < 6) : ({
        k += 0.8;
        i += 1;
    }) {
        fdeco(b, k, 0.0, -6, k + 0.8, 0.022, -5.6, if (i % 2 == 0) .f_hazard else .f_black);
        fdeco(b, k, 0.0, 5.6, k + 0.8, 0.022, 6, if (i % 2 == 0) .f_hazard else .f_black);
        fdeco(b, -6, 0.0, k, -5.6, 0.022, k + 0.8, if (i % 2 == 0) .f_hazard else .f_black);
        fdeco(b, 5.6, 0.0, k, 6, 0.022, k + 0.8, if (i % 2 == 0) .f_hazard else .f_black);
    }
}

fn ceiling(b: *Builder) void {
    fdeco(b, -fx_out, hall_h, -fz_out, fx_out, hall_h + 0.5, fz_out, .f_ceiling);
    b.solid(.{ .box = .{ .min = vec(-fx_out, hall_h, -fz_out), .max = vec(fx_out, hall_h + 2, fz_out) } });

    var x: f32 = -hall_x + 3;

    var row: u32 = 0;

    while (x < hall_x) : ({
        x += 6;
        row += 1;
    }) {
        b.putAt(.int_truss, vec(x, hall_h - 2.7, 0), 0, 1);

        if (x + 3 > hall_x) continue;

        var lz: f32 = -hall_z + 5;

        while (lz < hall_z - 4) : (lz += 10) {
            fdeco(b, x + 1.4, hall_h - 0.12, lz - 0.2, x + 4.6, hall_h - 0.02, lz + 6.2, .f_metal);
            fdeco(b, x + 1.6, hall_h - 0.16, lz, x + 4.4, hall_h - 0.12, lz + 6, .f_light);
        }
    }

    b.putAt(.int_gantry, vec(6, 11.6, 0), 0, 1);

    for ([_]f32{ -1, 1 }) |sx| {
        for ([_]f32{ -1, 1 }) |sz| fdeco(b, sx * (hall_x - 0.9), 5.5, sz * (hall_z - 0.9), sx * (hall_x - 0.3), 5.9, sz * (hall_z - 0.3), .f_red_light);
    }
}

fn hangar(b: *Builder) void {
    const doors_x = [_][2]f32{.{ -2.5, 2.5 }};
    const doors_z = [_][2]f32{ .{ -14, -9 }, .{ 9, 14 } };

    wallX(b, -hall_x, -hall_z, hall_z, hall_h, &doors_x, 1);
    wallX(b, hall_x, -hall_z, hall_z, hall_h, &doors_x, -1);
    wallZ(b, -hall_z, -hall_x, hall_x, hall_h, &doors_z, 1);
    wallZ(b, hall_z, -hall_x, hall_x, hall_h, &doors_z, -1);

    deckStrip(b, -hall_x + fwall / 2, -hall_z + fwall / 2, hall_x - fwall / 2, -hall_z + deck_w);
    deckStrip(b, -hall_x + fwall / 2, hall_z - deck_w, hall_x - fwall / 2, hall_z - fwall / 2);
    deckStrip(b, -hall_x + fwall / 2, -hall_z + deck_w, -hall_x + deck_w, hall_z - deck_w);
    deckStrip(b, hall_x - deck_w, -hall_z + deck_w, hall_x - fwall / 2, hall_z - deck_w);

    railDeco(b, -hall_x + deck_w, -hall_z + deck_w - 0.06, hall_x - deck_w, -hall_z + deck_w, deck);
    railDeco(b, -hall_x + deck_w, hall_z - deck_w, hall_x - deck_w, hall_z - deck_w + 0.06, deck);
    railDeco(b, -hall_x + deck_w - 0.06, -hall_z + deck_w, -hall_x + deck_w, 4, deck);
    railDeco(b, -hall_x + deck_w - 0.06, 6.6, -hall_x + deck_w, hall_z - deck_w, deck);
    railDeco(b, hall_x - deck_w, -hall_z + deck_w, hall_x - deck_w + 0.06, -6.6, deck);
    railDeco(b, hall_x - deck_w, -4, hall_x - deck_w + 0.06, hall_z - deck_w, deck);

    for ([_]f32{ -1, 1 }) |sz| {
        var x: f32 = -hall_x + 1;
        var i: u32 = 0;

        while (x < hall_x - 1) : ({
            x += 0.6;
            i += 1;
        }) {
            const zf = sz * (hall_z - deck_w) - sz * 0.02;

            fdeco(b, x, deck - 0.55, zf, x + 0.6, deck - 0.3, zf + sz * 0.05, if (i % 2 == 0) .f_hazard else .f_black);
        }
    }

    stairs(b, -hall_x + deck_w, -hall_x + deck_w + 9, 4, 6.6, .neg_x);
    stairs(b, hall_x - deck_w - 9, hall_x - deck_w, -6.6, -4, .pos_x);

    for ([_]f32{ -1, 1 }) |sx| {
        for ([_]f32{ -1, 1 }) |sz| pillar(b, sx * 12, sz * 10);
    }

    container(b, -18, -4, false, .f_container_red);
    container(b, 19, 5, false, .f_container_blue);
    container(b, 0, 17, true, .f_container_blue);
    container(b, 2, -18, true, .f_container_red);

    crate(b, -16, 6, 1.4, 0, .f_crate);
    crate(b, -14.4, 6.6, 1.2, 0, .f_crate);
    crate(b, -15.2, 6.2, 1.1, 1.4, .f_crate_teal);
    crate(b, 16, -6, 1.4, 0, .f_crate_teal);
    crate(b, 17.4, -5.4, 1.2, 0, .f_crate);
    crate(b, -5, 11, 1.3, 0, .f_crate);
    crate(b, 6, -11, 1.3, 0, .f_crate_teal);
    crate(b, -24, 18, 1.4, 0, .f_crate);
    crate(b, 24, -18, 1.4, 0, .f_crate);

    barrier(b, -7, 0, false);
    barrier(b, 7, 0, false);
    barrier(b, 0, 8, true);
    barrier(b, 0, -8, true);
    barrier(b, -22, -14, true);
    barrier(b, 22, 14, true);

    fdeco(b, -hall_x + 0.32, 6.5, -6, -hall_x + 0.45, 14, 6, .f_vault);
    fdeco(b, -hall_x + 0.45, 9.6, -1.2, -hall_x + 0.55, 10.9, 1.2, .f_black);
}

fn sideRooms(b: *Builder) void {
    const outer = [_][2]f32{.{ -5, 5 }};

    wallX(b, -fx_out, -fz_out, fz_out, hall_h, &outer, 1);
    wallX(b, fx_out, -fz_out, fz_out, hall_h, &outer, -1);
    wallZ(b, -fz_out, -fx_out, fx_out, hall_h, &outer, 1);
    wallZ(b, fz_out, -fx_out, fx_out, hall_h, &outer, -1);

    wallZ(b, hall_z + 9, -fx_out, -hall_x, hall_h, &[_][2]f32{.{ -46, -42 }}, -1);
    wallZ(b, hall_z + 9, hall_x, fx_out, hall_h, &[_][2]f32{.{ 42, 46 }}, -1);
    wallZ(b, -hall_z - 9, -fx_out, -hall_x, hall_h, &[_][2]f32{.{ -46, -42 }}, 1);
    wallZ(b, -hall_z - 9, hall_x, fx_out, hall_h, &[_][2]f32{.{ 42, 46 }}, 1);

    for ([_]f32{ -1, 1 }) |sx| {
        const cx = sx * 43;

        container(b, cx, -6, false, if (sx < 0) .f_container_blue else .f_container_red);
        container(b, cx + sx * 6, 8, false, .f_container_red);
        crate(b, cx - sx * 5, 12, 1.4, 0, .f_crate);
        crate(b, cx - sx * 5, -14, 1.4, 0, .f_crate_teal);
        crate(b, cx - sx * 3.6, -14.6, 1.2, 0, .f_crate);
        barrier(b, cx, 18, true);
        barrier(b, cx, -20, true);
        pillar(b, cx, 0);
    }

    for ([_]f32{ -1, 1 }) |sz| {
        const cz = sz * 39;

        barrier(b, -20, cz, true);
        barrier(b, 20, cz, true);
        crate(b, -6, cz, 1.3, 0, .f_crate);
        crate(b, 8, cz + sz * 1.5, 1.3, 0, .f_crate_teal);
        container(b, -40, cz, true, .f_container_blue);
        container(b, 40, cz, true, .f_container_red);
    }

    fbox(b, 10, 0, 33, 22, 1.0, 34.2, .f_grey_dark);
    fdeco(b, 10.2, 1.0, 33.1, 21.8, 1.9, 33.3, .f_screen);
    fbox(b, -22, 0, -34.2, -10, 1.0, -33, .f_grey_dark);
    fdeco(b, -21.8, 1.0, -33.3, -10.2, 1.9, -33.1, .f_screen);

    var x: f32 = -fx_out + 4;

    while (x < fx_out - 2) : (x += 8) {
        fdeco(b, x - 1.2, hall_h - 0.2, hall_z + 4, x + 1.2, hall_h, hall_z + 5, .f_light);
        fdeco(b, x - 1.2, hall_h - 0.2, -hall_z - 5, x + 1.2, hall_h, -hall_z - 4, .f_light);
    }

    var z: f32 = -fz_out + 4;

    while (z < fz_out - 2) : (z += 8) {
        fdeco(b, hall_x + 12, hall_h - 0.2, z - 1.2, hall_x + 14, hall_h, z + 1.2, .f_light);
        fdeco(b, -hall_x - 14, hall_h - 0.2, z - 1.2, -hall_x - 12, hall_h, z + 1.2, .f_light);
    }
}

fn facility(b: *Builder) void {
    floorLines(b);
    ceiling(b);
    hangar(b);
    sideRooms(b);
    facilityClutter(b);
    complex(b);
}

fn hangarShell(b: *Builder) void {
    const out: f32 = fwall / 2 + 0.02;
    var x: f32 = -fx_out + 4;

    while (x < fx_out - 1) : (x += 8) {
        if (@abs(x) < 7) continue;

        const kind: Kind = if (@abs(@abs(x) - 28) < 1) .hangar_mark else if (@mod(x + fx_out, 24) < 8) .hangar_bay_vent else .hangar_bay;

        b.putAt(kind, vec(x, 0, fz_out + out), 0, 1);
        b.putAt(kind, vec(-x, 0, -fz_out - out), std.math.pi, 1);
    }

    var z: f32 = -fz_out + 4;

    while (z < fz_out - 1) : (z += 8) {
        if (@abs(z) < 7) continue;

        const kind: Kind = if (@mod(z + fz_out, 24) < 8) .hangar_bay_vent else .hangar_bay;

        b.putAt(kind, vec(fx_out + out, 0, -z), half_pi, 1);
        b.putAt(kind, vec(-fx_out - out, 0, z), -half_pi, 1);
    }

    b.putAt(.hangar_door, vec(0, 0, fz_out + out), 0, 1);
    b.putAt(.hangar_door, vec(0, 0, -fz_out - out), std.math.pi, 1);
    b.putAt(.hangar_door, vec(fx_out + out, 0, 0), half_pi, 1);
    b.putAt(.hangar_door, vec(-fx_out - out, 0, 0), -half_pi, 1);
}

fn roadStrip(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32, y: f32) void {
    const w = terrain.road_half - 1;

    if (@abs(x1 - x0) > @abs(z1 - z0)) {
        const lo = @min(x0, x1) - w;
        const hi = @max(x0, x1) + w;

        trim(b, lo, y, z0 - w, hi, y + 0.03, z0 + w, .tarmac);
        trim(b, lo, y + 0.03, z0 - w + 0.3, hi, y + 0.045, z0 - w + 0.45, .marking);
        trim(b, lo, y + 0.03, z0 + w - 0.45, hi, y + 0.045, z0 + w - 0.3, .marking);

        var x = lo + 2;

        while (x < hi - 3) : (x += 6) trim(b, x, y + 0.03, z0 - 0.1, x + 3, y + 0.045, z0 + 0.1, .marking);
    } else {
        const lo = @min(z0, z1) - w;
        const hi = @max(z0, z1) + w;

        trim(b, x0 - w, y, lo, x0 + w, y + 0.03, hi, .tarmac);
        trim(b, x0 - w + 0.3, y + 0.03, lo, x0 - w + 0.45, y + 0.045, hi, .marking);
        trim(b, x0 + w - 0.45, y + 0.03, lo, x0 + w - 0.3, y + 0.045, hi, .marking);

        var z = lo + 2;

        while (z < hi - 3) : (z += 6) trim(b, x0 - 0.1, y + 0.03, z, x0 + 0.1, y + 0.045, z + 3, .marking);
    }
}

fn fenceLine(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32) void {
    const dx = x1 - x0;
    const dz = z1 - z0;
    const len = @sqrt(dx * dx + dz * dz);
    const n: u32 = @intFromFloat(@max(1, @floor(len / 4)));
    const yaw: f32 = if (@abs(dx) > @abs(dz)) (if (dx > 0) 0 else std.math.pi) else (if (dz > 0) -half_pi else half_pi);
    var i: u32 = 0;

    while (i < n) : (i += 1) {
        const t = (@as(f32, @floatFromInt(i)) + 0.5) / @as(f32, @floatFromInt(n));
        const x = x0 + dx * t;
        const z = z0 + dz * t;

        if (terrain.roadDistance(x, z) < terrain.road_half + 1.5) continue;

        b.putAt(.mil_fence, vec(x, ground(x, z), z), yaw, 1);
    }
}

pub fn fuelTank(b: *Builder, cx: f32, cz: f32) void {
    b.putAt(.mil_fueltank, vec(cx, lowest(cx, cz, 3.4) + 0.4, cz), 0, 1);
}

fn mast(b: *Builder, cx: f32, cz: f32) void {
    const y = ground(cx, cz);

    b.putAt(.mil_mast, vec(cx, y, cz), 0, 1);
    b.solid(.{ .box = .{ .min = vec(cx - 1.3, y - 0.5, cz - 1.3), .max = vec(cx + 1.3, y + 6, cz + 1.3) } });
}

fn lamp(b: *Builder, x: f32, z: f32) void {
    const y = ground(x, z);

    b.putAt(.mil_lamp, vec(x, y, z), 0, 1);
    b.solid(.{ .cylinder = .{ .base = vec(x, y, z), .radius = 0.15, .height = 7 } });
}

const Rect = [4]f32;

fn blocked(list: []const Rect, x: f32, z: f32, r: f32) bool {
    for (list) |q| {
        if (x + r > q[0] and x - r < q[2] and z + r > q[1] and z - r < q[3]) return true;
    }

    return false;
}

fn savannaHut(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    const kinds = [_]Kind{ .dk_house_0, .dk_house_1, .dk_house_2, .dk_house_3, .dk_house_4, .dk_house_5 };
    const y = lowest(cx, cz, 4.5) + 0.6;

    b.putAt(kinds[@as(usize, @intFromFloat(@abs(cx * 0.31 + cz * 0.17))) % kinds.len], vec(cx, y, cz), yaw, 1);
    b.solid(.{ .box = .{ .min = vec(cx - 3.8, y - 0.6, cz - 3.8), .max = vec(cx + 3.8, y + 5.2, cz + 3.8) } });
}

fn conquestHeights(b: *Builder) void {
    const d = terrain.districts;

    for ([_][3]f32{ .{ d[2].x - 40, d[2].z + 2, 0 }, .{ d[4].x + 30, d[4].z - 26, half_pi }, .{ d[1].x - 20, d[1].z + 22, 0 } }) |o| {
        const x = o[0];
        const z = o[1];
        const y = lowest(x, z, 3.2) + 0.45;

        cContainer(b, x, z, o[2] == 0, 1, .f_container_red);
        b.putAt(.mil_stairs, vec(x + (if (o[2] == 0) @as(f32, 0) else 2.9), y, z + (if (o[2] == 0) @as(f32, 2.9) else 0)), o[2], 1);

        if (o[2] == 0) {
            b.solid(.{ .ramp = .{ .min = vec(x - 0.6, y, z + 1.25), .max = vec(x + 0.6, y + 2.6, z + 5.6), .rise = .neg_z } });
        } else {
            b.solid(.{ .ramp = .{ .min = vec(x + 1.25, y, z - 0.6), .max = vec(x + 5.6, y + 2.6, z + 0.6), .rise = .neg_x } });
        }

        b.putAt(.mil_sandbags, vec(x, y + 2.6, z), o[2], 0.7);
    }
}

fn pointCover(b: *Builder, cx: f32, cz: f32) void {
    var a: f32 = b.rng.range(0, 1);

    while (a < 6.28) : (a += 0.7) {
        const r = b.rng.range(20, 36);
        const x = cx + @cos(a) * r;
        const z = cz + @sin(a) * r;
        const roll = b.rng.next();

        if (terrain.roadDistance(x, z) < terrain.road_half + 2 or terrain.runwayMask(x, z) > 0.1) continue;

        for (0..5) |_| b.put(.mil_grass, x + b.rng.range(-4, 4), z + b.rng.range(-4, 4), b.rng.range(0, 6.28), b.rng.range(1.0, 1.6));

        if (roll < 0.35) {
            b.putAt(.dk_ruin_wall, vec(x, lowest(x, z, 3) + 0.3, z), a + half_pi, 1);
        } else if (roll < 0.6) {
            sandbags(b, x, z, a + half_pi, 3);
        } else if (roll < 0.8) {
            b.putAt(b.rng.pick(Kind, &.{ .mil_rock_1, .mil_rock_3, .mil_rock_4 }), vec(x, lowest(x, z, 2) + 0.1, z), b.rng.range(0, 6.28), b.rng.range(0.8, 1.3));
        } else {
            b.put(.dk_scrub, x, z, 0, 1.4);
            b.put(.dk_scrub, x + 2, z - 1, 0, 1.2);
        }
    }
}

fn savanna(b: *Builder) void {
    var placed: std.ArrayList([2]f32) = .empty;
    var tries: u32 = 0;
    var n: u32 = 0;

    while (tries < 3000 and n < 70) : (tries += 1) {
        const px = b.rng.range(-terrain.play + 25, terrain.play - 25);
        const pz = b.rng.range(-terrain.play + 25, terrain.play - 25);

        if (terrain.districtMask(px, pz) > 0.02 or terrain.townMask(px, pz) > 0.02 or terrain.runwayMask(px, pz) > 0.05) continue;

        if (terrain.roadDistance(px, pz) < terrain.road_half + 7) continue;

        var far = true;

        for (placed.items) |q| {
            if ((q[0] - px) * (q[0] - px) + (q[1] - pz) * (q[1] - pz) < 26 * 26) far = false;
        }

        if (!far) continue;

        placed.append(b.gpa, .{ px, pz }) catch {};
        n += 1;

        const y = lowest(px, pz, 3);

        switch (n % 7) {
            0, 1 => {
                for (0..5) |_| {
                    const a = b.rng.range(0, 6.28);
                    const r = b.rng.range(2, 9);

                    b.put(.mil_acacia, px + @cos(a) * r, pz + @sin(a) * r, b.rng.range(0, 6.28), b.rng.range(0.9, 1.5));
                }

                b.put(.mil_termite, px + 4, pz - 6, 0, b.rng.range(0.8, 1.3));
            },
            2 => {
                if (terrain.height(px, pz) - lowest(px, pz, 14) < 2.5) b.putAt(.mil_outcrop_1, vec(px, lowest(px, pz, 9) - 1.5, pz), b.rng.range(0, 6.28), b.rng.range(0.6, 0.9));
                b.put(.mil_acacia, px + 9, pz + 3, 0, 1.2);
            },
            3 => {
                b.putAt(.mil_kraal, vec(px, y + 0.1, pz), b.rng.range(0, 6.28), 1);
                savannaHut(b, px + 10, pz + 2, b.rng.range(0, 6.28));
                b.put(.mil_acacia, px - 8, pz + 6, 0, 1.3);
            },
            4 => {
                wreck(b, px, pz, b.rng.next() < 0.5);
                wreck(b, px + 5, pz + 3, b.rng.next() < 0.5);
                b.put(.mil_tyres, px - 3, pz + 2, 0, 1);
                b.put(.mil_termite, px + 7, pz - 5, 0, 1);
            },
            5 => {
                b.putAt(.dk_water_tower, vec(px, y + 0.3, pz), b.rng.range(0, 6.28), 1);
                b.put(.mil_drums, px + 4, pz + 2, 0, 1);
                b.put(.mil_acacia, px - 6, pz - 5, 0, 1.1);
            },
            else => {
                for (0..3) |k| b.put(.mil_termite, px + @as(f32, @floatFromInt(k)) * 4 - 4, pz + b.rng.range(-3, 3), 0, b.rng.range(0.7, 1.4));

                b.putAt(.mil_outcrop_3, vec(px + 8, lowest(px + 8, pz, 5) - 0.6, pz), 0, 1);
            },
        }
    }
}

fn districtTufts(b: *Builder) void {
    const p = terrain.play - 8;
    var x: f32 = -p;

    while (x < p) : (x += 5) {
        var z: f32 = -p;

        while (z < p) : (z += 5) {
            const px = x + b.rng.range(-2, 2);
            const pz = z + b.rng.range(-2, 2);
            const roll = b.rng.next();

            if (terrain.townMask(px, pz) > 0.1) continue;

            if (terrain.roadDistance(px, pz) < terrain.road_half + 1 or terrain.runwayMask(px, pz) > 0.2) continue;

            if (roll < 0.42) {
                b.put(.mil_grass, px, pz, b.rng.range(0, 6.28), b.rng.range(0.8, 1.5));
            } else if (roll < 0.45) {
                b.putAt(.mil_debris, vec(px, ground(px, pz) + 0.02, pz), b.rng.range(0, 6.28), 1);
            } else if (roll < 0.5) {
                b.put(.dk_scrub, px, pz, b.rng.range(0, 6.28), b.rng.range(0.9, 1.4));
            }
        }
    }
}

fn outcropRing(b: *Builder) void {
    var a: f32 = 0.05;

    while (a < 6.28) : (a += 0.22) {
        const rr = terrain.play + 6 + b.rng.range(-2, 8);
        const sq = 1 / @max(@abs(@cos(a)), @abs(@sin(a)));
        const mx = @cos(a) * rr * @min(sq, 1.06);
        const mz = @sin(a) * rr * @min(sq, 1.06);

        const sc = b.rng.range(1.2, 2.0);

        b.putAt(b.rng.pick(Kind, &.{ .mil_outcrop_1, .mil_outcrop_2, .mil_outcrop_2 }), vec(mx, lowest(mx, mz, 12 * sc) - 3 * sc, mz), b.rng.range(0, 6.28), sc);
    }
}

fn mesaRing(b: *Builder, scale: f32) void {
    var a: f32 = 0.1;

    while (a < 6.28) : (a += 0.38) {
        const rr = terrain.play + 8 + b.rng.range(-2, 8);
        const sq = 1 / @max(@abs(@cos(a)), @abs(@sin(a)));
        const mx = @cos(a) * rr * @min(sq, 1.06);
        const mz = @sin(a) * rr * @min(sq, 1.06);

        b.putAt(b.rng.pick(Kind, &.{ .dk_mesa_0, .dk_mesa_1, .dk_mesa_2 }), vec(mx, terrain.height(mx, mz) - 3, mz), b.rng.range(0, 6.28), b.rng.range(0.75, 1.1) * scale);
    }
}

fn cluster(b: *Builder, x: f32, z: f32, kind: u32) void {
    const yaw: f32 = @as(f32, @floatFromInt(@as(u32, @intFromFloat(@abs(x * 3 + z * 7))) % 4)) * half_pi;
    const c = @cos(yaw);
    const sn = @sin(yaw);
    const at = struct {
        fn f(bb: *Builder, k: Kind, cx: f32, cz: f32, lx: f32, lz: f32, cc: f32, ss: f32, yy: f32, extra: f32) void {
            const px = cx + lx * cc + lz * ss;
            const pz = cz - lx * ss + lz * cc;

            bb.putAt(k, vec(px, ground(px, pz), pz), yy + extra, 1);
        }
    }.f;

    switch (kind) {
        0 => {
            cContainer(b, x, z, @mod(yaw, std.math.pi) < 0.1, 1 + @as(u32, @intFromFloat(@abs(x + z))) % 3, if (@mod(x, 2) < 1) .f_container_red else .f_container_blue);
            at(b, .mil_pallets, x, z, 0, 2.6, c, sn, yaw, 0);
            at(b, .mil_pallets, x, z, 1.3, 2.7, c, sn, yaw, 0.1);
            at(b, .mil_forklift, x, z, -3.5, 3.6, c, sn, yaw, 0.5);
        },
        1 => {
            at(b, .mil_generator, x, z, 0, 0, c, sn, yaw, 0);
            at(b, .mil_light_tower, x, z, 3.2, 1.5, c, sn, yaw, 0.3);
            at(b, .mil_cable_drum, x, z, -2.5, 1.8, c, sn, yaw, 0);
            at(b, .mil_drums, x, z, -1.0, -2.0, c, sn, yaw, 0);
        },
        2 => {
            at(b, .mil_pallets, x, z, 0, 0, c, sn, yaw, 0);
            at(b, .mil_pallets, x, z, 1.3, 0, c, sn, yaw, 0.05);
            at(b, .mil_pallets, x, z, 0.6, 1.2, c, sn, yaw, 0);
            at(b, .mil_drums, x, z, -2.0, 0.5, c, sn, yaw, 0);
            at(b, .mil_cable_drum, x, z, 3.2, 1.0, c, sn, yaw, 0.2);
        },
        3 => {
            at(b, .mil_hesco, x, z, 0, 0, c, sn, yaw, 0);
            at(b, .mil_sandbags, x, z, 0, 1.6, c, sn, yaw, 0);
            at(b, .mil_drums, x, z, 2.6, 1.6, c, sn, yaw, 0);
        },
        else => {
            at(b, .mil_drums, x, z, 0, 0, c, sn, yaw, 0);
            at(b, .mil_pallets, x, z, 1.6, 0.3, c, sn, yaw, 0.2);
        },
    }
}

fn decal(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32, y: f32, tone: Tone) void {
    trim(b, x0, y, z0, x1, y + 0.008, z1, tone);
}

fn kerbs(b: *Builder) void {
    for (terrain.facility_roads) |r| {
        const along_x = @abs(r[2] - r[0]) > @abs(r[3] - r[1]);
        const lo = if (along_x) @min(r[0], r[2]) else @min(r[1], r[3]);
        const hi = if (along_x) @max(r[0], r[2]) else @max(r[1], r[3]);
        var t = lo + 2;

        while (t < hi - 1) : (t += 4) {
            for ([_]f32{ -1, 1 }) |sd| {
                const x = if (along_x) t else r[0] + sd * 6.3;
                const z = if (along_x) r[1] + sd * 6.3 else t;
                var crossing = false;

                for (terrain.facility_roads) |o| {
                    if (o[0] == r[0] and o[1] == r[1] and o[2] == r[2] and o[3] == r[3]) continue;

                    const ox = @max(@min(o[0], o[2]), @min(x, @max(o[0], o[2])));
                    const oz = @max(@min(o[1], o[3]), @min(z, @max(o[1], o[3])));

                    if (@abs(ox - x) < 9 and @abs(oz - z) < 9) crossing = true;
                }

                if (crossing or (@abs(x) < fx_out + 1 and @abs(z) < fz_out + 1)) continue;

                b.putAt(.mil_kerb, vec(x, ground(x, z), z), if (along_x) 0 else half_pi, 1);
            }
        }
    }
}

fn mark(b: *Builder, x: f32, z: f32, len: f32, wid: f32, along_x: bool) void {
    const fade = @min(1.2, len * 0.2);
    const y: f32 = 0.004;
    const t: f32 = 0.008;

    if (along_x) {
        trim(b, x, y, z - wid * 0.35, x + fade, y + t, z + wid * 0.35, .scuff_soft);
        trim(b, x + fade, y, z - wid / 2, x + len - fade, y + t, z + wid / 2, .scuff);
        trim(b, x + len - fade, y, z - wid * 0.35, x + len, y + t, z + wid * 0.35, .scuff_soft);
    } else {
        trim(b, x - wid * 0.35, y, z, x + wid * 0.35, y + t, z + fade, .scuff_soft);
        trim(b, x - wid / 2, y, z + fade, x + wid / 2, y + t, z + len - fade, .scuff);
        trim(b, x - wid * 0.35, y, z + len - fade, x + wid * 0.35, y + t, z + len, .scuff_soft);
    }
}

fn groundBreaks(b: *Builder, used: []const Rect) void {
    const cw = terrain.compound;
    var x: f32 = -cw[0] + 3;

    while (x < cw[0] - 3) : (x += 4.5) {
        var z: f32 = -cw[1] + 3;

        while (z < cw[1] - 3) : (z += 4.5) {
            const px = x + b.rng.range(-1.5, 1.5);
            const pz = z + b.rng.range(-1.5, 1.5);
            const roll = b.rng.next();
            const rd = terrain.roadDistance(px, pz);

            if (@abs(px) < fx_out + 2 and @abs(pz) < fz_out + 2) continue;

            if (rd < terrain.road_half + 1 or blocked(used, px, pz, 1.5)) continue;

            const along = b.rng.next() < 0.5;

            if (roll < 0.14) {
                const w = b.rng.range(1.2, 2.2);

                mark(b, px - w / 2, pz, w, w * 0.7, true);
            } else if (roll < 0.24) {
                mark(b, px, pz, b.rng.range(1.5, 3), 0.1, along);
            } else if (roll < 0.32) {
                const l = b.rng.range(5, 8);

                for ([_]f32{ -0.8, 0.8 }) |o| {
                    if (along) mark(b, px, pz + o, l, 0.35, true) else mark(b, px + o, pz, l, 0.35, false);
                }
            } else if (roll < 0.42) {
                b.putAt(.mil_debris, vec(px, ground(px, pz) + 0.02, pz), b.rng.range(0, 6.28), 1);
            } else if (roll < 0.45) {
                b.putAt(.mil_tyres, vec(px, ground(px, pz), pz), b.rng.range(0, 6.28), 1);
            } else if (roll < 0.49) {
                trim(b, px - 1.6, 0.004, pz - 1.6, px + 1.6, 0.012, pz - 1.45, .paint_line);
                trim(b, px - 1.6, 0.004, pz + 1.45, px + 1.6, 0.012, pz + 1.6, .paint_line);
                trim(b, px - 1.6, 0.004, pz - 1.6, px - 1.45, 0.012, pz + 1.6, .paint_line);
                trim(b, px + 1.45, 0.004, pz - 1.6, px + 1.6, 0.012, pz + 1.6, .paint_line);
            }
        }
    }
}

fn blobAt(b: *Builder, x: f32, z: f32, rx: f32, rz: f32) void {
    const y = ground(x, z);

    if (1 - terrain.normal(x, z).y > 0.12) return;

    trim(b, x - rx * 1.25, y + 0.01, z - rz * 1.25, x + rx * 1.25, y + 0.016, z + rz * 1.25, .blob_soft);
    trim(b, x - rx, y + 0.016, z - rz, x + rx, y + 0.022, z + rz, .blob);
}

fn blobs(b: *Builder) void {
    const skip = [_][]const u8{ "mil_grass", "mil_kerb", "mil_fence", "mil_lamp", "mil_powerpole", "mil_outcrop", "mil_rock", "mil_debris", "mil_signpost", "mil_mast", "mil_trench", "mil_kraal", "hangar", "int_truss", "int_gantry", "int_wall", "int_screen", "mil_watchtower", "mil_warehouse", "mil_quonset", "mil_office", "mil_workshop" };
    const n = b.placed.items.len;

    for (b.placed.items[0..n]) |pl| {
        const name = props.name(pl.kind);

        if (!std.mem.startsWith(u8, name, "mil_") and !std.mem.startsWith(u8, name, "int_")) continue;

        var bad = false;

        for (skip) |k| {
            if (std.mem.startsWith(u8, name, k)) bad = true;
        }

        if (bad) continue;

        if (@abs(pl.pos.y - ground(pl.pos.x, pl.pos.z)) > 0.6) continue;

        const info = props.info(pl.kind);
        const sx = (info.max[0] - info.min[0]) * pl.scale * 0.5;
        const sz = (info.max[2] - info.min[2]) * pl.scale * 0.5;
        const quarter = @mod(@as(i32, @intFromFloat(@round(pl.yaw / half_pi))), 2) != 0;
        const r = if (std.mem.eql(u8, name, "mil_acacia")) @as(f32, 2.6) else 0;

        if (r > 0) {
            blobAt(b, pl.pos.x, pl.pos.z, r, r);
        } else {
            blobAt(b, pl.pos.x, pl.pos.z, if (quarter) sz else sx, if (quarter) sx else sz);
        }
    }
}

const facility_lots = [_][3]f32{
    .{ 60, -70, 0 },        .{ 72, -70, 0 },           .{ -60, 70, std.math.pi }, .{ -72, 70, std.math.pi },
    .{ 104, 4, half_pi },   .{ 120, 4, half_pi },      .{ -104, -4, -half_pi },   .{ -120, -4, -half_pi },
    .{ 4, 100, 0 },         .{ -4, 112, std.math.pi }, .{ 4, -110, 0 },           .{ -4, -165, std.math.pi },
    .{ 60, -190, half_pi }, .{ -60, -190, -half_pi },
};

fn overwatch(b: *Builder) void {
    for ([_][3]f32{ .{ -110, 62, 0 }, .{ 84, 52, half_pi }, .{ -40, -60, 0 } }) |o| {
        const x = o[0];
        const z = o[1];

        cContainer(b, x, z, o[2] == 0, 1, .f_container_blue);

        const sx: f32 = if (o[2] == 0) 0 else 2.9;
        const sz: f32 = if (o[2] == 0) 2.9 else 0;

        b.putAt(.mil_stairs, vec(x + sx, ground(x + sx, z + sz), z + sz), o[2], 1);

        if (o[2] == 0) {
            b.solid(.{ .ramp = .{ .min = vec(x - 0.6, ground(x, z), z + 1.25), .max = vec(x + 0.6, ground(x, z) + 3.05, z + 5.6), .rise = .neg_z } });
        } else {
            b.solid(.{ .ramp = .{ .min = vec(x + 1.25, ground(x, z), z - 0.6), .max = vec(x + 5.6, ground(x, z) + 3.05, z + 0.6), .rise = .neg_x } });
        }

        b.putAt(.mil_sandbags, vec(x, ground(x, z) + 3.05, z - (if (o[2] == 0) @as(f32, 0.6) else 0)), o[2], 0.7);
    }
}

fn complex(b: *Builder) void {
    const cw = terrain.compound;
    var used: std.ArrayList(Rect) = .empty;

    hangarShell(b);
    runway(b);

    for (terrain.facility_roads, 0..) |r, i| roadStrip(b, r[0], r[1], r[2], r[3], 0.04 + @as(f32, @floatFromInt(i)) * 0.006);

    fenceLine(b, -cw[0], -cw[1], cw[0], -cw[1]);
    fenceLine(b, -cw[0], cw[1], cw[0], cw[1]);
    fenceLine(b, -cw[0], -cw[1], -cw[0], cw[1]);
    fenceLine(b, cw[0], -cw[1], cw[0], cw[1]);

    var fx: f32 = -cw[0] + 6;

    while (fx < cw[0] - 4) : (fx += 17) {
        for ([_]f32{ -1, 1 }) |sd| {
            if (terrain.roadDistance(fx, sd * cw[1]) < 14) continue;

            b.putAt(b.rng.pick(Kind, &.{ .dk_drift_0, .dk_drift_1, .dk_drift_2 }), vec(fx, ground(fx, sd * cw[1]) - 0.05, sd * (cw[1] + 2)), if (sd < 0) 0 else std.math.pi, b.rng.range(0.8, 1.2));
            b.putAt(b.rng.pick(Kind, &.{ .dk_drift_0, .dk_drift_1, .dk_drift_2 }), vec(sd * (cw[0] + 2), ground(sd * cw[0], fx) - 0.05, fx * 0.9), if (sd < 0) half_pi else -half_pi, b.rng.range(0.8, 1.2));
        }
    }

    for ([_][2]f32{ .{ -1, -1 }, .{ 1, -1 }, .{ -1, 1 }, .{ 1, 1 } }) |k| tower(b, k[0] * (cw[0] - 9), k[1] * (cw[1] - 12));

    tower(b, -16, -cw[1] + 10);

    warehouse(b, 104, -97, 12, 8);
    warehouse(b, -104, 98, 12, 8);
    b.putAt(.fc_office, vec(35.5, ground(35.5, -97.5), -97.5), std.math.pi, 1);
    b.putAt(.fc_workshop, vec(36, ground(36, 98), 98), std.math.pi, 1);
    cHangar(b, 100, 98);
    b.putAt(.mil_pallets, vec(36, 0.08, 88), 0, 1);
    b.putAt(.fc_pipebridge, vec(70, ground(70, 46), 46), half_pi, 1);
    b.putAt(.fc_pipebridge, vec(-70, ground(-70, -46), -46), half_pi, 1);

    for ([_]Rect{ .{ 90, -107, 118, -85 }, .{ -118, 88, -90, 108 }, .{ 32, -102, 48, -90 }, .{ 27, 91, 45, 105 }, .{ 84, 86, 116, 110 }, .{ -64, -52, 64, 52 } }) |q| used.append(b.gpa, q) catch {};

    b.solid(.{ .box = .{ .min = vec(29.2, -0.5, -102.8), .max = vec(41.8, 7.9, -92.2) } });

    b.solid(.{ .box = .{ .min = vec(29.2, -0.5, 93), .max = vec(42.8, 6.4, 103) } });

    for ([_]f32{ -1, 1 }) |sd| {
        for ([_]f32{ -1, 1 }) |sy| b.solid(.{ .box = .{ .min = vec(70 + sy * 7 - 0.2, -0.5, 46 + sd * 0.9 - 0.2), .max = vec(70 + sy * 7 + 0.2, 6.4, 46 + sd * 0.9 + 0.2) } });
    }

    var cx: f32 = -122;

    while (cx < -92) : (cx += 7) {
        var cz: f32 = 14;

        while (cz < 56) : (cz += 10) {
            cContainer(b, cx, cz, false, 1 + @as(u32, @intFromFloat(@abs(cx * 0.37 + cz * 0.11))) % 3, if (@mod(cx, 14) < 7) .f_container_blue else .f_container_red);
        }
    }

    used.append(b.gpa, .{ -126, 8, -88, 60 }) catch {};

    for ([_][2]f32{ .{ 98, 22 }, .{ 108, 22 }, .{ 118, 22 }, .{ 98, 36 }, .{ 108, 36 } }) |c| fuelTank(b, c[0], c[1]);

    pipes(b, 92, 46, 124, 46);
    used.append(b.gpa, .{ 90, 16, 126, 50 }) catch {};
    mast(b, 118, -55);
    mast(b, -116, -40);
    used.append(b.gpa, .{ 114, -59, 122, -51 }) catch {};

    for ([_][2]f32{ .{ -52, 100 }, .{ -40, 100 }, .{ -28, 100 } }) |c| tent(b, c[0], c[1]);

    used.append(b.gpa, .{ -58, 94, -22, 106 }) catch {};
    bunker(b, -36, -112, 0);
    bunker(b, 66, -112, 1);
    nest(b, -28, -84);
    nest(b, 28, 84);
    sandbags(b, 0, -104, 0, 9);

    for ([_][3]f32{ .{ 22, -78, 0 }, .{ -22, 78, 0 }, .{ 74, 80, half_pi }, .{ -126, -66, 0 }, .{ 126, 62, half_pi } }) |q| b.putAt(.mil_hesco, vec(q[0], ground(q[0], q[1]) + 0.3, q[1]), q[2], 1);

    for ([_][3]f32{ .{ -6, -124, 0 }, .{ 6, -124, 0 }, .{ 134, -4, half_pi }, .{ -134, 4, half_pi } }) |q| b.putAt(.mil_barrier, vec(q[0], ground(q[0], q[1]), q[1]), q[2], 1);

    var lx: f32 = -66;

    while (lx <= 66) : (lx += 22) {
        lamp(b, lx, -74);
        lamp(b, lx, 74);
    }

    var lz: f32 = -96;

    while (lz > -190) : (lz -= 24) lamp(b, 10, lz);

    var gx: f32 = -118;
    var kind: u32 = 0;

    while (gx < 120) : (gx += 13) {
        var gz: f32 = -110;

        while (gz < 112) : (gz += 13) {
            const x = gx + b.rng.range(-2, 2);
            const z = gz + b.rng.range(-2, 2);

            if (terrain.roadDistance(x, z) < terrain.road_half + 5 or blocked(used.items, x, z, 6)) continue;

            kind += 1;
            cluster(b, x, z, (kind * 7 + @as(u32, @intFromFloat(@abs(x * 0.3)))) % 5);
            used.append(b.gpa, .{ x - 6, z - 6, x + 6, z + 6 }) catch {};
        }
    }

    for ([_][3]f32{ .{ 60, -78, 0 }, .{ 72, -78, 0 }, .{ -60, 78, 0 }, .{ -72, 78, 0 } }) |q| {
        decal(b, q[0] - 1.6, q[1] - 3, q[0] - 1.45, q[1] + 3, 0.004, .paint_line);
        decal(b, q[0] + 1.45, q[1] - 3, q[0] + 1.6, q[1] + 3, 0.004, .paint_line);
    }

    for ([_][2]f32{ .{ 0, 50 }, .{ 0, -50 } }) |d| {
        var k: f32 = -9;

        while (k < 9) : (k += 2) decal(b, d[0] + k, d[1] - 0.4, d[0] + k + 1, d[1] + 0.4, 0.112, .paint_line);
    }

    var rx: f32 = -fx_out + 4;

    while (rx < fx_out) : (rx += 8) {
        var rz: f32 = -fz_out + 4;

        while (rz < fz_out) : (rz += 8) b.putAt(.hangar_roof, vec(rx, hall_h + 0.5, rz), 0, 1);
    }

    kerbs(b);
    groundBreaks(b, used.items);
    overwatch(b);

    for (facility_lots) |l| blobAt(b, l[0], l[1], if (@abs(@sin(l[2])) > 0.5) @as(f32, 1.3) else 2.6, if (@abs(@sin(l[2])) > 0.5) @as(f32, 2.6) else 1.3);

    blobs(b);
    mesaRing(b, 0.9);
    scrub(b);
}

fn scrub(b: *Builder) void {
    const half = terrain.half;
    const cw = terrain.compound;
    var x: f32 = -half + 16;

    while (x < half - 16) : (x += 12) {
        var z: f32 = -half + 16;

        while (z < half - 16) : (z += 12) {
            const px = x + b.rng.range(-5, 5);
            const pz = z + b.rng.range(-5, 5);
            const roll = b.rng.next();

            if (@max(@abs(px), @abs(pz)) > terrain.play - 6) continue;

            if (@abs(px) < cw[0] + 6 and @abs(pz) < cw[1] + 6) continue;

            if (terrain.roadDistance(px, pz) < terrain.road_half + 3 or terrain.runwayMask(px, pz) > 0.1) continue;

            if (1 - terrain.normal(px, pz).y > 0.4) continue;

            const dens = terrain.fbm(px * 0.02 + 40, pz * 0.02 - 11);

            if (dens > 0.56 and roll < 0.5) {
                const kinds = [_]Kind{ .mil_rock_1, .mil_rock_2, .mil_rock_3, .mil_rock_4 };
                const size = b.rng.range(0.7, 2.2);

                b.putAt(b.rng.pick(Kind, &kinds), vec(px, lowest(px, pz, size) + 0.15, pz), b.rng.range(0, 6.28), size);
            } else if (roll < 0.2) {
                b.put(.dk_scrub, px, pz, b.rng.range(0, 6.28), b.rng.range(1.0, 1.6));
            } else if (roll < 0.26) {
                b.put(b.rng.pick(Kind, &.{ .mil_acacia, .mil_drytree }), px, pz, b.rng.range(0, 6.28), b.rng.range(0.8, 1.2));
            } else if (roll < 0.32) {
                b.putAt(b.rng.pick(Kind, &.{ .dk_rocks_0, .dk_rocks_2, .dk_rocks_4 }), vec(px, lowest(px, pz, 2) + 0.2, pz), b.rng.range(0, 6.28), b.rng.range(0.8, 1.3));
            }
        }
    }
}

fn pallet(b: *Builder, x: f32, z: f32) void {
    fbox(b, x - 0.6, 0, z - 0.5, x + 0.6, 0.16, z + 0.5, .f_wood_pallet);
}

fn barrel(b: *Builder, x: f32, z: f32, tone: Tone) void {
    _ = tone;

    b.putAt(.int_drum, vec(x, 0, z), x * 3, 1);
    b.solid(.{ .cylinder = .{ .base = vec(x, 0, z), .radius = 0.3, .height = 0.92 } });
}

fn pipeX(b: *Builder, x0: f32, x1: f32, y: f32, z: f32, r: f32, tone: Tone) void {
    fdeco(b, x0, y - r, z - r, x1, y + r, z + r, tone);

    var x = x0 + 2;

    while (x < x1 - 1) : (x += 4) fdeco(b, x - 0.06, y - r - 0.06, z - r - 0.06, x + 0.06, y + r + 0.06, z + r + 0.06, .f_grey_dark);
}

fn pipeZ(b: *Builder, z0: f32, z1: f32, y: f32, x: f32, r: f32, tone: Tone) void {
    fdeco(b, x - r, y - r, z0, x + r, y + r, z1, tone);

    var z = z0 + 2;

    while (z < z1 - 1) : (z += 4) fdeco(b, x - r - 0.06, y - r - 0.06, z - 0.06, x + r + 0.06, y + r + 0.06, z + 0.06, .f_grey_dark);
}

fn crateStack(b: *Builder, x: f32, z: f32) void {
    b.putAt(.mil_pallets, vec(x, 0, z), 0, 1);
    b.putAt(.int_crate, vec(x + 1.4, 0, z + 0.2), 0.1, 0.9);
    b.putAt(.int_crate, vec(x + 1.3, 1.08, z + 0.1), -0.15, 0.75);
}

fn forklift(b: *Builder, x: f32, z: f32) void {
    b.putAt(.mil_forklift, vec(x, 0, z), half_pi, 1);
}

fn workbench(b: *Builder, x: f32, z: f32, along_x: bool) void {
    b.putAt(.int_bench, vec(x, 0, z), if (along_x) 0 else half_pi, 1);
    b.putAt(.int_cabinet, vec(x + (if (along_x) @as(f32, 2.3) else 0), 0, z + (if (along_x) @as(f32, 0) else 2.3)), if (along_x) 0 else half_pi, 1);
}

fn shelf(b: *Builder, x: f32, z0: f32, z1: f32, face: f32) void {
    var z = z0 + 2.05;

    while (z < z1 + 0.5) : (z += 4.2) b.putAt(.int_shelving, vec(x, 0, z), if (face > 0) half_pi else -half_pi, 1);
}

fn sign(b: *Builder, x: f32, y: f32, z: f32, along_x: bool, face: f32) void {
    const yaw: f32 = if (along_x) (if (face > 0) 0 else std.math.pi) else (if (face > 0) half_pi else -half_pi);

    b.putAt(.int_wallsign, vec(x, y - 0.5, z), yaw, 1.2);
}

fn vent(b: *Builder, x: f32, y: f32, z: f32, along_x: bool, face: f32) void {
    const yaw: f32 = if (along_x) (if (face > 0) 0 else std.math.pi) else (if (face > 0) half_pi else -half_pi);

    b.putAt(.int_wallvent, vec(x, y - 0.8, z), yaw, 1);
}

fn drone(b: *Builder, x: f32, z: f32) void {
    fbox(b, x - 3.2, 0, z - 3.2, x + 3.2, 0.32, z + 3.2, .f_grey_dark);
    fdeco(b, x - 3.25, 0.32, z - 3.25, x + 3.25, 0.4, z - 3.0, .f_hazard);
    fdeco(b, x - 3.25, 0.32, z + 3.0, x + 3.25, 0.4, z + 3.25, .f_hazard);
    fdeco(b, x - 3.25, 0.32, z - 3.0, x - 3.0, 0.4, z + 3.0, .f_hazard);
    fdeco(b, x + 3.0, 0.32, z - 3.0, x + 3.25, 0.4, z + 3.0, .f_hazard);
    fbox(b, x - 1.0, 0.32, z - 1.6, x + 1.0, 1.4, z + 1.6, .f_panel);
    fdeco(b, x - 0.7, 1.4, z - 1.1, x + 0.7, 1.75, z + 0.9, .f_grey);
    fdeco(b, x - 0.35, 0.9, z + 1.6, x + 0.35, 1.25, z + 1.75, .f_screen);

    for ([_][2]f32{ .{ -1, -1 }, .{ 1, -1 }, .{ -1, 1 }, .{ 1, 1 } }) |c| {
        const ax = x + c[0] * 2.3;
        const az = z + c[1] * 2.3;

        fdeco(b, @min(x, ax) - 0.1, 1.05, @min(z, az) - 0.1, @max(x, ax) + 0.1, 1.2, @max(z, az) + 0.1, .f_grey_dark);
        fdeco(b, ax - 0.22, 1.0, az - 0.22, ax + 0.22, 1.35, az + 0.22, .f_pipe);
        fdeco(b, ax - 0.95, 1.38, az - 0.06, ax + 0.95, 1.42, az + 0.06, .f_black);
        fdeco(b, ax - 0.06, 1.38, az - 0.95, ax + 0.06, 1.42, az + 0.95, .f_black);
    }

    fdeco(b, x - 0.25, 0.32, z - 1.4, x + 0.25, 0.9, z - 1.0, .f_rubber);
}

fn wallDressing(b: *Builder) void {
    const kinds = [_]Kind{ .int_cabinet, .int_wallsign, .int_shelving, .int_wallvent, .int_compressor };
    var k: usize = 0;

    for ([_]f32{ -1, 1 }) |sd| {
        var t: f32 = -hall_x + 7;

        while (t < hall_x - 5) : (t += 9) {
            k += 1;

            const z = sd * (hall_z - deck_w - 0.6);

            if (@abs(t) < 3 or @abs(@abs(t) - 11.5) < 4) continue;

            const kind = kinds[k % kinds.len];
            const y: f32 = if (kind == .int_wallsign) 1.6 else if (kind == .int_wallvent) 0.6 else 0;
            const zz = if (kind == .int_wallsign or kind == .int_wallvent) sd * (hall_z - 0.32) else z;

            b.putAt(kind, vec(t, y, zz), if (sd < 0) 0 else std.math.pi, 1);
        }

        var u: f32 = -hall_z + 9;

        while (u < hall_z - 8) : (u += 8) {
            k += 1;

            if (@abs(u) < 7.5) continue;

            const kind = kinds[k % kinds.len];
            const y: f32 = if (kind == .int_wallsign) 1.6 else if (kind == .int_wallvent) 0.6 else 0;
            const xx = if (kind == .int_wallsign or kind == .int_wallvent) sd * (hall_x - 0.32) else sd * (hall_x - deck_w - 0.6);

            b.putAt(kind, vec(xx, y, u), if (sd < 0) half_pi else -half_pi, 1);
        }
    }
}

fn facilityClutter(b: *Builder) void {
    drone(b, -6, 2);

    crateStack(b, -22, -14);
    crateStack(b, 23, 13);
    crateStack(b, -9, -21);
    crateStack(b, 11, 21);
    crateStack(b, 25, -22);

    for ([_][2]f32{ .{ -25, -6 }, .{ -24.3, -6.6 }, .{ -25.4, -5.2 }, .{ -24.6, -5.6 } }) |p| barrel(b, p[0], p[1], .f_barrel);

    for ([_][2]f32{ .{ 25, 7 }, .{ 25.7, 7.6 }, .{ 24.4, 8 } }) |p| barrel(b, p[0], p[1], .f_barrel_red);

    for ([_][2]f32{ .{ -2, -24 }, .{ -1.3, -24.4 } }) |p| barrel(b, p[0], p[1], .f_barrel);

    fdeco(b, -26, 0.005, -7.5, -23, 0.012, -4, .f_stain);
    fdeco(b, 23.5, 0.005, 6.4, 26.6, 0.012, 9.2, .f_stain);

    forklift(b, 9, -9);

    workbench(b, -42, 18, true);
    workbench(b, 42, -18, true);
    workbench(b, 44, 16, false);

    shelf(b, -54, -14, -4, 1);
    shelf(b, -54, 4, 14, 1);
    shelf(b, 54, -14, -4, -1);
    shelf(b, 54, 4, 14, -1);

    for ([_]f32{ -1, 1 }) |sz| {
        var px: f32 = -hall_x + 4.5;

        while (px < hall_x - 4) : (px += 8) {
            b.putAt(.int_wallpipes, vec(px, 12.2, sz * (hall_z - 0.32)), if (sz < 0) 0 else std.math.pi, 1);
            b.putAt(.int_wallpipes, vec(px, 2.6, sz * (hall_z - 0.32)), if (sz < 0) 0 else std.math.pi, 1);
        }
    }

    b.putAt(.int_screen, vec(hall_x - 0.32, 6.6, 0), -half_pi, 1.6);
    fdeco(b, hall_x - 0.56, 9.0, -2.88, hall_x - 0.53, 9.8, -0.32, .f_screen);
    fdeco(b, hall_x - 0.56, 9.0, 0, hall_x - 0.53, 9.8, 2.88, .f_screen);

    for ([_][2]f32{ .{ -20.9, -22.5 }, .{ 12.4, -23.7 } }) |l| fdeco(b, l[0], 2.0, l[1], l[0] + 0.2, 2.15, l[1] + 0.05, .f_light);
    b.putAt(.int_cnc, vec(-20, 0, -23.4), 0, 1);
    b.putAt(.int_lathe, vec(14, 0, -24.2), 0, 1);
    b.putAt(.int_compressor, vec(22, 0, 24.2), std.math.pi, 1);
    b.putAt(.int_cabinet, vec(-26, 0, 25.2), std.math.pi, 1);
    b.putAt(.int_cabinet, vec(-24.7, 0, 25.2), std.math.pi, 1);
    b.putAt(.int_bench, vec(-16, 0, 25), std.math.pi, 1);
    b.putAt(.int_carlift, vec(-44, 0, 27), 0, 1);
    b.solid(.{ .box = .{ .min = vec(-46.3, 0, 25.2), .max = vec(-41.7, 3, 28.8) } });
    b.putAt(.int_cnc, vec(-36, 0, -29), half_pi, 1);
    b.putAt(.int_lathe, vec(38, 0, 29), std.math.pi, 1);
    b.putAt(.int_compressor, vec(48, 0, -29), 0, 1);
    b.putAt(.int_cabinet, vec(33, 0, -30), half_pi, 1);
    for ([_]f32{ -1, 1 }) |sz| {
        var x: f32 = -20;

        while (x <= 20) : (x += 20) {
            sign(b, x, 8.5, sz * (hall_z - 0.05), true, -sz);
            vent(b, x + 8, 9.5, sz * (hall_z - 0.05), true, -sz);
        }
    }

    for ([_]f32{ -1, 1 }) |sx| {
        sign(b, sx * (hall_x - 0.05), 8.5, 12, false, -sx);
        vent(b, sx * (hall_x - 0.05), 9.5, -14, false, -sx);
    }

    fdeco(b, -14, 0.005, 14, -10, 0.012, 16, .f_stain);
    fdeco(b, 14, 0.005, -16, 17, 0.012, -13.5, .f_stain);

    wallDressing(b);
}

fn facilitySpots(gpa: std.mem.Allocator) void {
    const spawn_list = [_]Vec3{
        vec(-22, 0, 12),  vec(22, 0, -12), vec(0, 0, -21),  vec(-2, 0, 21),  vec(-43, 0, 2),  vec(43, 0, -2),    vec(-30, 0, 39), vec(30, 0, -39),
        vec(-86, 0, -14), vec(86, 0, 14),  vec(-64, 0, 86), vec(64, 0, -86), vec(110, 0, 70), vec(-110, 0, -70),
    };
    const inside = [_]Vec3{
        vec(0, 0, 0),      vec(-12, 0, 0),   vec(12, 0, 0),      vec(0, 0, 12),      vec(0, 0, -12),
        vec(-43, 0, -16),  vec(43, 0, 16),   vec(-30, 0, -39),   vec(30, 0, 39),     vec(-10, 0, 39),
        vec(10, 0, -39),   vec(-50, 0, 30),  vec(50, 0, -30),    vec(-27, deck, 0),  vec(27, deck, 0),
        vec(0, deck, -24), vec(0, deck, 24), vec(-20, deck, 24), vec(20, deck, -24),
    };
    const outside = [_][2]f32{
        .{ -86, 4 },   .{ -84, 64 },    .{ 96, -76 },  .{ 92, 70 },  .{ 112, 4 },    .{ -100, 114 },
        .{ -30, 112 }, .{ 30, 112 },    .{ -50, -86 }, .{ 50, -86 }, .{ -78, -112 }, .{ 0, -140 },
        .{ 84, -140 }, .{ -150, -150 }, .{ 150, 150 }, .{ 62, 44 },  .{ -62, -46 },  .{ 30, -196 },
    };
    var spots: std.ArrayList(Vec3) = .empty;
    var anchors: std.ArrayList(Vec3) = .empty;
    var parked: std.ArrayList(Spot) = .empty;

    for (inside) |p| spots.append(gpa, p) catch {};

    for (outside) |o| spots.append(gpa, vec(o[0], ground(o[0], o[1]), o[1])) catch {};

    for (inside) |p| anchors.append(gpa, p.add(.{ .y = 8 })) catch {};

    for (outside) |o| anchors.append(gpa, vec(o[0], ground(o[0], o[1]) + 14, o[1])) catch {};

    for (facility_lots) |l| parked.append(gpa, .{ .pos = vec(l[0], ground(l[0], l[1]), l[1]), .yaw = l[2] }) catch {};

    var all = spawn_list;

    for (&all) |*p| p.y = ground(p.x, p.z);

    spawns = gpa.dupe(Vec3, &all) catch &.{};
    var yaws: [all.len]f32 = undefined;

    for (all, 0..) |p, k| {
        const tx: f32 = if (@abs(p.x) < fx_out and @abs(p.z) < fz_out) 0 else p.x * 0.4;
        const tz: f32 = if (@abs(p.x) < fx_out and @abs(p.z) < fz_out) 0 else p.z * 0.4;

        yaws[k] = std.math.atan2(tx - p.x, tz - p.z);
    }

    spawn_yaws = gpa.dupe(f32, &yaws) catch &.{};
    weapon_spots = spots.toOwnedSlice(gpa) catch &.{};
    drone_anchors = anchors.toOwnedSlice(gpa) catch &.{};
    vehicle_spots = parked.toOwnedSlice(gpa) catch &.{};
}

fn ground(x: f32, z: f32) f32 {
    return terrain.height(x, z);
}

fn box(b: *Builder, x0: f32, y0: f32, z0: f32, x1: f32, y1: f32, z1: f32, tone: Tone) void {
    b.mass(vec(@min(x0, x1), y0, @min(z0, z1)), vec(@max(x0, x1), y1, @max(z0, z1)), tone);
}

fn trim(b: *Builder, x0: f32, y0: f32, z0: f32, x1: f32, y1: f32, z1: f32, tone: Tone) void {
    b.deco(vec(@min(x0, x1), y0, @min(z0, z1)), vec(@max(x0, x1), y1, @max(z0, z1)), tone);
}

fn sandbags(b: *Builder, cx: f32, cz: f32, yaw: f32, len: f32) void {
    const dx = @cos(yaw);
    const dz = @sin(yaw);
    const n: u32 = @intFromFloat(@max(1, @round(len / 3)));
    var i: u32 = 0;

    while (i < n) : (i += 1) {
        const t = (@as(f32, @floatFromInt(i)) - @as(f32, @floatFromInt(n - 1)) / 2) * 3;
        const x = cx + dx * t;
        const z = cz + dz * t;

        b.putAt(.mil_sandbags, vec(x, lowest(x, z, 1.5) + 0.35, z), -yaw, 1);
    }
}

fn nest(b: *Builder, cx: f32, cz: f32) void {
    const r: f32 = 2.6;
    var a: f32 = 0.5;

    while (a < 5.9) : (a += 1.2) {
        const x = cx + @cos(a) * r;
        const z = cz + @sin(a) * r;

        b.putAt(.mil_sandbags, vec(x, lowest(x, z, 1.5) + 0.35, z), -(a + half_pi), 1);
    }
}

fn tower(b: *Builder, cx: f32, cz: f32) void {
    const y = lowest(cx, cz, 2.2) + 0.35;
    const deck_y = y + 6;

    b.putAt(.mil_watchtower, vec(cx, y, cz), 0, 1);

    for ([_][2]f32{ .{ -1.7, -1.7 }, .{ 1.7, -1.7 }, .{ -1.7, 1.7 }, .{ 1.7, 1.7 } }) |p| b.solid(.{ .cylinder = .{ .base = vec(cx + p[0], y, cz + p[1]), .radius = 0.15, .height = 8.6 } });

    b.solid(.{ .box = .{ .min = vec(cx - 1.85, deck_y - 0.25, cz - 1.85), .max = vec(cx + 1.85, deck_y, cz + 1.85) } });
    b.solid(.{ .box = .{ .min = vec(cx - 1.8, deck_y, cz - 1.8), .max = vec(cx + 1.8, deck_y + 1.2, cz - 1.68) } });
    b.solid(.{ .box = .{ .min = vec(cx - 1.8, deck_y, cz - 1.8), .max = vec(cx - 1.68, deck_y + 1.2, cz + 1.8) } });
    b.solid(.{ .box = .{ .min = vec(cx + 1.68, deck_y, cz - 1.8), .max = vec(cx + 1.8, deck_y + 1.2, cz + 1.8) } });
    b.solid(.{ .box = .{ .min = vec(cx - 1.8, deck_y, cz + 1.68), .max = vec(cx + 0.95, deck_y + 1.2, cz + 1.8) } });
    b.solid(.{ .ramp = .{ .min = vec(cx + 1.0, y, cz + 2.0), .max = vec(cx + 2.0, deck_y, cz + 7.3), .rise = .neg_z } });
}

fn bunker(b: *Builder, cx: f32, cz: f32, yaw_quarter: u32) void {
    b.putAt(.mil_bunker, vec(cx, lowest(cx, cz, 3.6) + 0.4, cz), @as(f32, @floatFromInt(yaw_quarter)) * half_pi, 1);
}

fn walledYard(b: *Builder, cx: f32, cz: f32, size: f32) void {
    const h = size / 2;
    const n: u32 = @intFromFloat(@max(1, @floor(size / 6)));
    var i: u32 = 0;

    while (i < n) : (i += 1) {
        const t = -h + 3 + @as(f32, @floatFromInt(i)) * 6;

        if (@abs(t) > 2.5) b.putAt(.dk_ruin_wall, vec(cx + t, lowest(cx + t, cz - h, 3) + 0.3, cz - h), 0, 1);

        b.putAt(.dk_ruin_wall, vec(cx + t, lowest(cx + t, cz + h, 3) + 0.3, cz + h), std.math.pi, 1);
        b.putAt(.dk_ruin_wall, vec(cx - h, lowest(cx - h, cz + t, 3) + 0.3, cz + t), half_pi, 1);
        b.putAt(.dk_ruin_wall, vec(cx + h, lowest(cx + h, cz + t, 3) + 0.3, cz + t), -half_pi, 1);
    }

    b.putAt(.mil_drums, vec(cx + h - 3, lowest(cx + h - 3, cz + h - 3, 1.5) + 0.2, cz + h - 3), 0, 1);
}

fn kitBlock(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    const kinds = [_]Kind{ .dk_house_0, .dk_house_1, .dk_house_2, .dk_house_3, .dk_house_4, .dk_house_5 };
    const y = lowest(cx, cz, 4.5) + 0.6;

    b.putAt(kinds[@as(usize, @intFromFloat(@abs(cx * 0.31 + cz * 0.17))) % kinds.len], vec(cx, y, cz), yaw, 1);
    b.solid(.{ .box = .{ .min = vec(cx - 3.8, y - 0.6, cz - 3.8), .max = vec(cx + 3.8, y + 5.2, cz + 3.8) } });
}

pub var hangar_zones: [8][3]f32 = undefined;
pub var hangar_count: usize = 0;

pub fn cHangar(b: *Builder, cx: f32, cz: f32) void {
    const y = lowest(cx, cz, 15) + 0.3;

    if (hangar_count < hangar_zones.len) {
        hangar_zones[hangar_count] = .{ cx, cz, y };
        hangar_count += 1;
    }

    b.putAt(.mil_quonset, vec(cx, y, cz), 0, 1);
    b.putAt(.mil_hangar_doors, vec(cx - 14.25, y, cz), 0, 1);
    b.putAt(.mil_hangar_lamps, vec(cx, y + 8.8, cz), 0, 1);
    b.putAt(.mil_hangar_lining, vec(cx, y, cz), 0, 1);
    b.solid(.{ .box = .{ .min = vec(cx + 13.7, y - 0.5, cz - 10), .max = vec(cx + 14.1, y + 10, cz + 10) } });

    for ([_]f32{ -1, 1 }) |sd| {
        b.solid(.{ .box = .{ .min = vec(cx - 14, y - 0.5, cz + sd * 9.6 - 0.4), .max = vec(cx + 14, y + 4.3, cz + sd * 9.6 + 0.4) } });
        b.solid(.{ .box = .{ .min = vec(cx - 14, y + 4.3, cz + sd * 8.3 - 0.9), .max = vec(cx + 14, y + 6.8, cz + sd * 8.3 + 0.9) } });
    }

    b.solid(.{ .box = .{ .min = vec(cx - 14, y + 6.8, cz - 7.4), .max = vec(cx + 14, y + 10.2, cz + 7.4) } });
    b.putAt(.mil_forklift, vec(cx - 4, y, cz + 4), 0.4, 1);
    b.putAt(.mil_pallets, vec(cx + 6, y, cz - 6), 0, 1);
    b.putAt(.mil_drums, vec(cx + 9, y, cz + 6), half_pi, 1);
}

pub fn tent(b: *Builder, cx: f32, cz: f32) void {
    b.putAt(.mil_tent, vec(cx, lowest(cx, cz, 3) + 0.4, cz), 0, 1);
}

fn cContainer(b: *Builder, cx: f32, cz: f32, along_x: bool, stack: u32, tone: Tone) void {
    const y = lowest(cx, cz, 3.2) + 0.45;
    const kinds = [_]Kind{ .mil_container_rust, .mil_container_teal, .mil_container_olive, .mil_container_sand };
    const first: usize = if (tone == .f_container_red) 0 else 1;
    var k: u32 = 0;

    while (k < stack) : (k += 1) {
        const pick = kinds[(first + k * 2 + @as(usize, @intFromFloat(@abs(cx * 0.13 + cz * 0.07)))) % kinds.len];

        b.putAt(pick, vec(cx, y + @as(f32, @floatFromInt(k)) * 2.61, cz), if (along_x) 0 else half_pi, 1);
    }
}

fn warehouse(b: *Builder, cx: f32, cz: f32, hx: f32, hz: f32) void {
    _ = hx;
    _ = hz;

    const y = lowest(cx, cz, 13) + 0.4;
    const t: f32 = 0.2;

    b.putAt(.mil_warehouse, vec(cx, y, cz), 0, 1);

    for ([_]f32{ -1, 1 }) |s| {
        b.solid(.{ .box = .{ .min = vec(cx - 12, y - 0.5, cz + s * 8 - t), .max = vec(cx + 12, y + 7, cz + s * 8 + t) } });
        b.solid(.{ .box = .{ .min = vec(cx + s * 12 - t, y - 0.5, cz - 8), .max = vec(cx + s * 12 + t, y + 7, cz - 3.6) } });
        b.solid(.{ .box = .{ .min = vec(cx + s * 12 - t, y - 0.5, cz + 3.6), .max = vec(cx + s * 12 + t, y + 7, cz + 8) } });
        b.solid(.{ .box = .{ .min = vec(cx + s * 12 - t, y + 5, cz - 3.6), .max = vec(cx + s * 12 + t, y + 9.6, cz + 3.6) } });
    }

    b.solid(.{ .box = .{ .min = vec(cx - 12.5, y + 7, cz - 8.5), .max = vec(cx + 12.5, y + 9.8, cz + 8.5) } });
    b.putAt(.mil_forklift, vec(cx - 6, y, cz + 2), 0.3, 1);
    b.putAt(.mil_pallets, vec(cx + 7, y, cz + 4), 0, 1);
    b.putAt(.mil_pallets, vec(cx + 8.4, y, cz + 4), 0.1, 1);
    b.putAt(.mil_drums, vec(cx + 8, y, cz - 5), half_pi, 1);
}

fn pipes(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32) void {
    _ = z1;

    var x = @min(x0, x1) + 4;

    while (x <= @max(x0, x1) - 3) : (x += 8) b.putAt(.mil_pipe_rack, vec(x, lowest(x, z0, 4) + 0.2, z0), 0, 1);
}

fn wreck(b: *Builder, cx: f32, cz: f32, along_x: bool) void {
    b.putAt(.mil_wreck, vec(cx, lowest(cx, cz, 2) + 0.3, cz), if (along_x) 0 else half_pi, 1);
}

fn signpost(b: *Builder, x: f32, z: f32) void {
    b.putAt(.mil_signpost, vec(x, ground(x, z), z), b.rng.range(0, 6.28), 1);
}

fn capturePoint(b: *Builder, list: *std.ArrayList(CapturePoint), d: terrain.District, cx: f32, cz: f32) void {
    const y = ground(cx, cz);
    const radius: f32 = 12;

    box(b, cx - 0.15, y, cz - 0.15, cx + 0.15, y + 9, cz + 0.15, .pole);
    trim(b, cx + 0.15, y + 7, cz - 0.05, cx + 2.6, y + 8.6, cz + 0.05, .flag_cloth);
    trim(b, cx - 0.7, y, cz - 0.7, cx + 0.7, y + 0.35, cz + 0.7, .concrete);

    list.append(b.gpa, .{ .pos = vec(cx, y, cz), .radius = radius, .name = d.name }) catch {};
}

fn baseDistrict(b: *Builder, d: terrain.District) void {
    const r = d.r;

    var a: f32 = 0;

    while (a < 6.28) : (a += 0.06) {
        const x = d.x + @cos(a) * (r - 4);
        const z = d.z + @sin(a) * (r - 4);

        if (terrain.conquestRoad(x, z) < terrain.road_half + 3) continue;

        const y = ground(x, z);

        box(b, x - 0.9, y - 0.3, z - 0.9, x + 0.9, y + 1.1, z + 0.9, .concrete);
        trim(b, x - 0.12, y + 1.1, z - 0.12, x + 0.12, y + 2.6, z + 0.12, .pole);
    }

    for ([_][2]f32{ .{ -1, -1 }, .{ 1, -1 }, .{ -1, 1 }, .{ 1, 1 } }) |k| tower(b, d.x + k[0] * (r - 12), d.z + k[1] * (r - 12));

    cHangar(b, d.x - 30, d.z - 40);
    bunker(b, d.x - 40, d.z + 20, 0);
    bunker(b, d.x + 30, d.z + 40, 1);
    bunker(b, d.x - 10, d.z + 55, 0);
    for ([_][2]f32{ .{ 14, 14 }, .{ 14, 27 }, .{ -6, 32 } }) |o| {
        const bx = d.x + o[0];
        const bz = d.z + o[1];

        b.putAt(.mil_barracks, vec(bx, lowest(bx, bz, 7) + 0.4, bz), 0, 1);
    }

    tent(b, d.x - 22, d.z + 38);
    b.putAt(.mil_comms, vec(d.x + 42, ground(d.x + 42, d.z - 28), d.z - 28), 0.5, 1);
    cContainer(b, d.x - 55, d.z - 5, false, 2, .f_container_red);
    cContainer(b, d.x - 50, d.z - 5, false, 1, .f_container_blue);
    cContainer(b, d.x + 50, d.z + 15, true, 1, .f_container_red);
    nest(b, d.x - 18, d.z + 5);
    nest(b, d.x + 45, d.z - 5);
    sandbags(b, d.x - 25, d.z - 15, 0.3, 6);
    sandbags(b, d.x + 15, d.z - 20, 1.4, 6);

    b.put(.mil_pallets, d.x + 5, d.z, 0.2, 1);
    b.put(.mil_drums, d.x + 7, d.z + 3, 1.2, 1);
    b.put(.mil_light_tower, d.x - 6, d.z + 3, 0.4, 1);
    b.put(.mil_generator, d.x - 9, d.z + 6, 1.4, 1);
    b.put(.mil_office, d.x + 40, d.z + 25, 0, 1);
}

pub fn runway(b: *Builder) void {
    const r = terrain.runway;
    const y = ground(r[0], r[1]) + 0.04;

    trim(b, r[0] - r[2], y, r[1] - r[3], r[0] + r[2], y + 0.05, r[1] + r[3], .tarmac);

    var x = r[0] - r[2] + 10;

    while (x < r[0] + r[2] - 10) : (x += 14) trim(b, x, y + 0.05, r[1] - 0.35, x + 7, y + 0.07, r[1] + 0.35, .marking);

    for ([_]f32{ -1, 1 }) |side| {
        trim(b, r[0] - r[2], y + 0.05, r[1] + side * (r[3] - 1.2) - 0.25, r[0] + r[2], y + 0.07, r[1] + side * (r[3] - 1.2) + 0.25, .marking);

        var k: f32 = -4;

        while (k <= 4) : (k += 2) trim(b, r[0] - r[2] + 4, y + 0.05, r[1] + k * 1.2 - 0.4, r[0] - r[2] + 14, y + 0.07, r[1] + k * 1.2 + 0.4, .marking);
    }
}

fn oasisDistrict(b: *Builder, d: terrain.District) void {
    var a: f32 = 0;

    while (a < 6.28) : (a += 0.36) {
        const rr = b.rng.range(14, 19);

        b.put(if (b.rng.next() < 0.6) .palm_big else .palm_small, terrain.oasis[0] + @cos(a) * rr, terrain.oasis[1] + @sin(a) * rr, b.rng.range(0, 6.28), b.rng.range(0.85, 1.2));
    }

    for ([_][3]f32{ .{ -30, -15, 16 }, .{ -5, -35, 14 }, .{ -38, 18, 15 } }) |c| walledYard(b, d.x + c[0], d.z + c[1], c[2]);

    for ([_][2]f32{ .{ 10, -12 }, .{ -14, 2 }, .{ 20, 10 } }) |h| {
        const cx = d.x + h[0];
        const cz = d.z + h[1];
        const dx = d.x - cx;
        const dz = d.z - cz;
        const front: [2]f32 = if (@abs(dx) > @abs(dz)) .{ std.math.sign(dx), 0 } else .{ 0, std.math.sign(dz) };

        kitBlock(b, cx, cz, std.math.atan2(front[0], front[1]));
    }

    b.put(.arena_brazier, d.x, d.z + 4, 0, 1);

    for (0..6) |i| b.put(b.rng.pick(Kind, &.{ .arena_jar_1, .arena_jar_2, .arena_jar_3 }), d.x + @as(f32, @floatFromInt(i)) * 1.3 - 3, d.z - 4, b.rng.range(0, 6.28), 1);
}

fn outpostDistrict(b: *Builder, d: terrain.District) void {
    walledYard(b, d.x - 14, d.z - 10, 18);
    walledYard(b, d.x + 18, d.z + 12, 14);
    tower(b, d.x + 6, d.z - 22);
    nest(b, d.x - 20, d.z + 20);
    nest(b, d.x + 24, d.z - 18);
    sandbags(b, d.x, d.z + 8, 0, 7);
    tent(b, d.x + 28, d.z - 2);
    b.put(.mil_pallets, d.x - 2, d.z + 14, 0.2, 1);
    b.put(.mil_drums, d.x + 1, d.z + 16, 1.1, 1);
    b.put(.mil_generator, d.x + 8, d.z + 4, 0.6, 1);
}

fn industryDistrict(b: *Builder, d: terrain.District) void {
    warehouse(b, d.x - 26, d.z - 22, 14, 10);
    warehouse(b, d.x + 28, d.z + 20, 12, 9);
    cContainer(b, d.x + 22, d.z - 26, true, 2, .f_container_blue);
    cContainer(b, d.x + 30, d.z - 18, true, 1, .f_container_red);
    cContainer(b, d.x - 30, d.z + 24, false, 2, .f_container_red);
    cContainer(b, d.x - 22, d.z + 30, false, 1, .f_container_blue);
    pipes(b, d.x - 40, d.z + 6, d.x - 6, d.z + 8);
    pipes(b, d.x + 8, d.z - 8, d.x + 40, d.z - 6);

    fuelTank(b, d.x + 38, d.z + 38);
    fuelTank(b, d.x + 38, d.z + 30);
    b.put(.mil_workshop, d.x - 4, d.z + 38, std.math.pi, 1);
    b.put(.mil_cable_drum, d.x + 14, d.z + 2, 0.4, 1);
    b.put(.mil_forklift, d.x + 18, d.z - 10, 1.2, 1);
    nest(b, d.x - 8, d.z - 30);
    sandbags(b, d.x + 10, d.z + 34, 0, 5);

    for (0..3) |i| b.put(.mil_pallets, d.x - 6 + @as(f32, @floatFromInt(i)) * 1.5, d.z + 16, 0, 1);
}

fn hut(b: *Builder, cx: f32, cz: f32) void {
    const front: [2]f32 = if (b.rng.next() < 0.5) .{ 1, 0 } else .{ 0, 1 };

    house(b, cx, cz, front, b.rng.range(6, 7.5), b.rng.range(5.6, 7), 1);
}

fn countryside(b: *Builder) void {
    const half = terrain.half;
    var x: f32 = -half + 20;

    while (x < half - 20) : (x += 13) {
        var z: f32 = -half + 20;

        while (z < half - 20) : (z += 13) {
            const px = x + b.rng.range(-5, 5);
            const pz = z + b.rng.range(-5, 5);

            if (@max(@abs(px), @abs(pz)) > terrain.play - 6) continue;

            if (terrain.districtMask(px, pz) > 0.3 or terrain.roadDistance(px, pz) < terrain.road_half + 2.5 or terrain.runwayMask(px, pz) > 0.2) continue;

            if (1 - terrain.normal(px, pz).y > 0.35) continue;

            const dens = terrain.fbm(px * 0.02 + 40, pz * 0.02 - 11);
            const roll = b.rng.next();

            for (0..3) |_| {
                const gx = px + b.rng.range(-6, 6);
                const gz = pz + b.rng.range(-6, 6);

                if (terrain.roadDistance(gx, gz) > terrain.road_half + 1) b.put(.mil_grass, gx, gz, b.rng.range(0, 6.28), b.rng.range(0.8, 1.5));
            }

            if (dens > 0.5 and dens < 0.56) {
                for (0..4) |_| b.put(.dk_scrub, px + b.rng.range(-5, 5), pz + b.rng.range(-5, 5), b.rng.range(0, 6.28), b.rng.range(1.0, 1.6));
            }

            if (dens > 0.55 and roll < 0.55 and terrain.height(px, pz) - lowest(px, pz, 12) < 2.5) {
                const kinds = [_]Kind{ .mil_outcrop_3, .mil_rock_1, .mil_rock_3, .mil_outcrop_3, .mil_rock_2 };
                const size = b.rng.range(0.8, 2.6);

                b.putAt(b.rng.pick(Kind, &kinds), vec(px, lowest(px, pz, size) + 0.15, pz), b.rng.range(0, 6.28), size);

                if (b.rng.next() < 0.5) b.put(b.rng.pick(Kind, &kinds), px + b.rng.range(-4, 4), pz + b.rng.range(-4, 4), b.rng.range(0, 6.28), b.rng.range(0.5, 1.2));
            } else if (roll < 0.26) {
                b.put(b.rng.pick(Kind, &.{ .mil_acacia, .mil_acacia, .dk_scrub }), px, pz, b.rng.range(0, 6.28), b.rng.range(0.9, 1.4));
            } else if (roll < 0.3) {
                b.put(b.rng.pick(Kind, &.{ .mil_acacia, .mil_acacia, .mil_drytree }), px, pz, b.rng.range(0, 6.28), b.rng.range(0.8, 1.25));
            } else if (roll < 0.36 and terrain.riverDistance(px, pz) < 40) {
                b.put(.dk_scrub, px, pz, b.rng.range(0, 6.28), b.rng.range(1.0, 1.6));
            } else if (roll < 0.4) {
                b.put(.dk_scrub, px, pz, b.rng.range(0, 6.28), b.rng.range(0.8, 1.3));
            }
        }
    }

    var placed: std.ArrayList([2]f32) = .empty;
    var tries: u32 = 0;

    while (tries < 600 and placed.items.len < 26) : (tries += 1) {
        const px = b.rng.range(-terrain.play + 40, terrain.play - 40);
        const pz = b.rng.range(-terrain.play + 40, terrain.play - 40);

        if (terrain.districtMask(px, pz) > 0.05 or terrain.runwayMask(px, pz) > 0.05) continue;

        const rd = terrain.roadDistance(px, pz);

        if (rd < terrain.road_half + 8 or rd > 90) continue;

        if (1 - terrain.normal(px, pz).y > 0.2) continue;

        var far = true;

        for (placed.items) |p| {
            if ((p[0] - px) * (p[0] - px) + (p[1] - pz) * (p[1] - pz) < 70 * 70) far = false;
        }

        if (!far) continue;

        placed.append(b.gpa, .{ px, pz }) catch {};

        switch (placed.items.len % 5) {
            0 => walledYard(b, px, pz, 14),
            1 => {
                kitBlock(b, px, pz, b.rng.range(0, 6.28));
                b.put(.mil_drytree, px + 7, pz + 2, 0, 1);
            },
            2 => {
                nest(b, px, pz);
                b.put(.mil_drums, px + 4, pz + 1, 0.3, 1);
            },
            3 => {
                wreck(b, px, pz, b.rng.next() < 0.5);
                b.put(.mil_rock_3, px + 4, pz - 2, 0.5, 1.2);
            },
            else => {
                kitBlock(b, px, pz, 0);
                tent(b, px + 10, pz + 4);
            },
        }
    }

    roadDressing(b);
}

fn roadDressing(b: *Builder) void {
    for (terrain.conquestSegments(), 0..) |sg, si| {
        const dx = sg[2] - sg[0];
        const dz = sg[3] - sg[1];
        const len = @sqrt(dx * dx + dz * dz);
        const ux = dx / len;
        const uz = dz / len;
        var d: f32 = 20;
        var n: u32 = 0;

        while (d < len - 20) : (d += 28) {
            const side: f32 = if (si % 2 == 0) 1 else -1;
            const x = sg[0] + ux * d - uz * (terrain.road_half + 3) * side;
            const z = sg[1] + uz * d + ux * (terrain.road_half + 3) * side;

            n += 1;

            if (terrain.districtMask(x, z) > 0.2) continue;

            b.putAt(.mil_powerpole, vec(x, ground(x, z), z), std.math.atan2(ux, uz), 1);
        }

        if (si % 2 == 1) continue;

        const mx = sg[2];
        const mz = sg[3];

        if (terrain.districtMask(mx, mz) > 0.1) continue;

        const yaw = std.math.atan2(ux, uz);
        const ox = -uz * (terrain.road_half + 4);
        const oz = ux * (terrain.road_half + 4);

        b.putAt(.mil_checkpoint, vec(mx + ox, lowest(mx + ox, mz + oz, 2) + 0.2, mz + oz), yaw + half_pi, 1);
        b.putAt(.mil_tyres, vec(mx - ox, ground(mx - ox, mz - oz), mz - oz), 0, 1);
        sandbags(b, mx + ox * 1.8, mz + oz * 1.8, yaw, 6);
        wreck(b, mx - ox * 1.6 + ux * 12, mz - oz * 1.6 + uz * 12, @abs(ux) > @abs(uz));

        for ([_]f32{ -1, 1 }) |sd| {
            const tx = mx + ux * 30 * sd - uz * 22 * sd;
            const tz = mz + uz * 30 * sd + ux * 22 * sd;

            if (terrain.roadDistance(tx, tz) < terrain.road_half + 6) continue;

            for ([_]f32{ -8, 0, 8 }) |k| {
                const px = tx + ux * k;
                const pz = tz + uz * k;

                b.putAt(.mil_trench, vec(px, lowest(px, pz, 2) + 0.15, pz), std.math.atan2(uz, -ux) + half_pi, 1);
            }

            b.putAt(.mil_drums, vec(tx + ux * 13, ground(tx + ux * 13, tz + uz * 13), tz + uz * 13), 0.3, 1);
        }
    }
}

var conquest_points: std.ArrayList(CapturePoint) = .empty;

fn conquestTown(b: *Builder) void {
    const tc = terrain.town_center;
    const town_shops = [_]Kind{ .sv_shop_a, .sv_shop_b, .sv_shop_c };
    const widths = [_]f32{ 8.4, 7.4, 9.4 };
    const front: f32 = 5.6;
    const street_y = lowest(tc[0], tc[1], 6) + 0.4;
    var n: u32 = 0;

    for ([_]f32{ -1, 1 }) |side| {
        var x = tc[0] - 44;
        var run: u32 = 0;

        while (x < tc[0] + 44) {
            const k = n % town_shops.len;
            const w = widths[k];

            n += 1;

            if (@abs(x + w * 0.5 - tc[0]) < 9) {
                x += w;

                continue;
            }

            if (run == 3) {
                run = 0;

                const ax = x + 1.8;

                b.putAt(.mil_drums, vec(ax, terrain.height(ax, tc[1] + side * (front + 3)), tc[1] + side * (front + 3)), 0.4 * side, 1);
                x += 3.6;

                continue;
            }

            const cx = x + w * 0.5;
            const cz = tc[1] + side * (front + 3.45);
            const y = @max(lowest(cx, cz, 4.5) + 0.35, street_y - 0.6);

            b.putAt(town_shops[k], vec(cx, y, cz), if (side < 0) 0 else std.math.pi, 1);
            run += 1;

            const bz = cz + side * 11;

            if (run != 2 and terrain.conquestRoad(cx, bz) > terrain.road_half + 3) b.putAt(.sv_shed, vec(cx, lowest(cx, bz, 5.5) + 0.35, bz), if (side < 0) 0 else std.math.pi, 1);

            x += w + 0.2;
        }

        var kx = tc[0] - 42;

        while (kx < tc[0] + 42) : (kx += 4) {
            if (@abs(kx - tc[0]) < 9) continue;

            const kz = tc[1] + side * front;

            b.put(.mil_kerb, kx, kz, 0, 1);
        }

        var px = tc[0] - 40;

        while (px < tc[0] + 40) : (px += 15) {
            const pz = tc[1] + side * (front - 0.8);

            if (@abs(px - tc[0]) < 10) continue;

            b.put(.mil_powerpole, px + side * 3, pz, 0, 1);
        }

        b.put(.mil_signpost, tc[0] + side * 9.5, tc[1] + side * (front - 1.0), half_pi, 1);
    }

    b.put(.mil_acacia, tc[0], tc[1] + 9, 0.4, 1.1);
    b.put(.mil_acacia, tc[0] - 3, tc[1] - 10, 2.1, 0.9);

    for ([_][3]f32{ .{ -4, 6.5, 0 }, .{ 4, 6.5, 0 }, .{ -4, -6.5, std.math.pi }, .{ 4, -6.5, std.math.pi } }) |bn| {
        const bx = tc[0] + bn[0];
        const bz = tc[1] + bn[1];

        b.putAt(.sv_bench, vec(bx, terrain.height(bx, bz), bz), bn[2], 1);
    }

    const wx = tc[0] + 20;
    const wz = tc[1] + 30;

    b.putAt(.sv_watertower, vec(wx, lowest(wx, wz, 2.5) + 0.2, wz), 0.3, 1);

    const fx = tc[0] - 30;
    const fz = tc[1] - 32;
    const fy = lowest(fx, fz, 7) + 0.25;

    b.putAt(.sv_fuel, vec(fx, fy, fz), 0, 1);
    b.solid(.{ .box = .{ .min = vec(fx - 4, fy - 0.5, fz + 4.5), .max = vec(fx + 4, fy + 3.6, fz + 8.5) } });

    for ([_][2]f32{ .{ -4.5, -2.2 }, .{ 4.5, -2.2 }, .{ -4.5, 2.2 }, .{ 4.5, 2.2 } }) |o| b.solid(.{ .box = .{ .min = vec(fx + o[0] - 0.2, fy, fz + o[1] - 0.2), .max = vec(fx + o[0] + 0.2, fy + 5, fz + o[1] + 0.2) } });

    for ([_][2]f32{ .{ -3, 0 }, .{ 3, 0 } }) |o| b.solid(.{ .box = .{ .min = vec(fx + o[0] - 1.3, fy, fz - 0.5), .max = vec(fx + o[0] + 1.3, fy + 2.2, fz + 0.5) } });

    sandbags(b, tc[0] + 30, tc[1] + 22, 0.2, 9);
    sandbags(b, tc[0] - 34, tc[1] + 20, 1.7, 6);
    nest(b, tc[0] + 36, tc[1] - 26);
    nest(b, tc[0] - 38, tc[1] + 30);
}

fn conquestMap(b: *Builder) void {
    const d = terrain.districts;

    conquestTown(b);
    capturePoint(b, &conquest_points, d[0], terrain.town_center[0] - 8, terrain.town_center[1] + 2);
    oasisDistrict(b, d[1]);
    capturePoint(b, &conquest_points, d[1], d[1].x, d[1].z);
    baseDistrict(b, d[2]);
    runway(b);
    capturePoint(b, &conquest_points, d[2], d[2].x + 10, d[2].z);
    outpostDistrict(b, d[3]);
    capturePoint(b, &conquest_points, d[3], d[3].x, d[3].z);
    industryDistrict(b, d[4]);
    capturePoint(b, &conquest_points, d[4], d[4].x, d[4].z);
    for (conquest_points.items) |cp| pointCover(b, cp.pos.x, cp.pos.z);

    countryside(b);
    savanna(b);
    conquestHeights(b);
    blobs(b);
    districtTufts(b);
    outcropRing(b);

    for ([_][3]f32{ .{ -205, -150, 1.3 }, .{ -150, -210, 1.1 }, .{ -200, -200, 1.5 }, .{ 60, 120, 0.8 }, .{ -40, -150, 0.9 } }) |m| b.putAt(.mil_outcrop_2, vec(m[0], lowest(m[0], m[1], 12 * m[2]) - 1.2 * m[2], m[1]), m[0] * 0.1, m[2]);
}

fn freeSpot(p: Vec3, need: f32) bool {
    return clearance(p) >= need and 1 - terrain.normal(p.x, p.z).y < 0.3;
}

fn conquestSpots(gpa: std.mem.Allocator, b: *Builder) void {
    capture_points = conquest_points.toOwnedSlice(gpa) catch &.{};

    var spawn_list: std.ArrayList(Vec3) = .empty;
    var yaw_list: std.ArrayList(f32) = .empty;
    var spots: std.ArrayList(Vec3) = .empty;
    var anchors: std.ArrayList(Vec3) = .empty;
    var parked: std.ArrayList(Spot) = .empty;

    for (capture_points) |cp| {
        var got: u32 = 0;
        var tries: u32 = 0;

        while (tries < 300 and got < 3) : (tries += 1) {
            const a = b.rng.range(0, 6.28);
            const r = b.rng.range(16, 34);
            const x = cp.pos.x + @cos(a) * r;
            const z = cp.pos.z + @sin(a) * r;
            const p = vec(x, ground(x, z), z);

            if (!freeSpot(p, 3) or terrain.roadDistance(x, z) < terrain.road_half + 1) continue;

            const want = std.math.atan2(cp.pos.x - x, cp.pos.z - z);

            if (!viewOpen(p, want)) continue;

            spawn_list.append(gpa, p) catch {};
            yaw_list.append(gpa, want) catch {};
            got += 1;
        }

        var w: u32 = 0;

        tries = 0;

        while (tries < 400 and w < 14) : (tries += 1) {
            const a = b.rng.range(0, 6.28);
            const r = b.rng.range(4, 60);
            const x = cp.pos.x + @cos(a) * r;
            const z = cp.pos.z + @sin(a) * r;
            const p = vec(x, ground(x, z), z);

            if (!freeSpot(p, 1.2)) continue;

            spots.append(gpa, p) catch {};
            w += 1;
        }

        anchors.append(gpa, cp.pos.add(.{ .y = 14 })) catch {};
    }

    for (terrain.districts, 0..) |d, i| {
        _ = i;

        const n: u32 = 7;
        var k: u32 = 0;
        var tries: u32 = 0;

        while (tries < 400 and k < n and parked.items.len < 34) : (tries += 1) {
            const a = b.rng.range(0, 6.28);
            const r = b.rng.range(d.r * 0.4, d.r + 20);
            const x = d.x + @cos(a) * r;
            const z = d.z + @sin(a) * r;

            if (terrain.roadDistance(x, z) > terrain.road_half - 1) continue;

            const p = vec(x, ground(x, z), z);

            if (clearance(p) < 4) continue;

            var spread = true;

            for (spawn_list.items) |sp| {
                if (sp.sub(p).length() < 8) spread = false;
            }

            for (parked.items) |q| {
                if (q.pos.sub(p).length() < 9) spread = false;
            }

            if (!spread) continue;

            parked.append(gpa, .{ .pos = p, .yaw = b.rng.range(0, 6.28) }) catch {};
            k += 1;
        }
    }

    spawns = spawn_list.toOwnedSlice(gpa) catch &.{};
    spawn_yaws = yaw_list.toOwnedSlice(gpa) catch &.{};
    weapon_spots = spots.toOwnedSlice(gpa) catch &.{};
    drone_anchors = anchors.toOwnedSlice(gpa) catch &.{};
    vehicle_spots = parked.toOwnedSlice(gpa) catch &.{};

    var extra: std.ArrayList(Structure) = .empty;

    extra.appendSlice(gpa, structures) catch {};

    for (vehicle_spots) |sp| {
        const y = ground(sp.pos.x, sp.pos.z);

        if (1 - terrain.normal(sp.pos.x, sp.pos.z).y > 0.12) continue;

        extra.append(gpa, .{ .min = vec(sp.pos.x - 2.6, y + 0.01, sp.pos.z - 2.6), .max = vec(sp.pos.x + 2.6, y + 0.016, sp.pos.z + 2.6), .tone = .blob_soft }) catch {};
        extra.append(gpa, .{ .min = vec(sp.pos.x - 1.9, y + 0.016, sp.pos.z - 1.9), .max = vec(sp.pos.x + 1.9, y + 0.022, sp.pos.z + 1.9), .tone = .blob }) catch {};
    }

    structures = extra.toOwnedSlice(gpa) catch structures;
}

pub fn rotBox(cx: f32, cz: f32, yaw: f32, x0: f32, z0: f32, x1: f32, z1: f32) [4]f32 {
    const c = @cos(yaw);
    const s = @sin(yaw);
    var lo = [2]f32{ 1e9, 1e9 };
    var hi = [2]f32{ -1e9, -1e9 };

    for ([_][2]f32{ .{ x0, z0 }, .{ x1, z0 }, .{ x0, z1 }, .{ x1, z1 } }) |p| {
        const wx = cx + p[0] * c + p[1] * s;
        const wz = cz - p[0] * s + p[1] * c;

        lo = .{ @min(lo[0], wx), @min(lo[1], wz) };
        hi = .{ @max(hi[0], wx), @max(hi[1], wz) };
    }

    return .{ lo[0], lo[1], hi[0], hi[1] };
}

pub fn rotPoint(cx: f32, cz: f32, yaw: f32, lx: f32, lz: f32) [2]f32 {
    return .{ cx + lx * @cos(yaw) + lz * @sin(yaw), cz - lx * @sin(yaw) + lz * @cos(yaw) };
}

pub fn kitSolid(b: *Builder, cx: f32, cz: f32, yaw: f32, y: f32, l: [6]f32) void {
    const r = rotBox(cx, cz, yaw, l[0], l[1], l[2], l[3]);

    b.solid(.{ .box = .{ .min = vec(r[0], y + l[4], r[1]), .max = vec(r[2], y + l[5], r[3]) } });
}

pub fn covered(b: *Builder, x: f32, z: f32, pad: f32) bool {
    for (b.solids.items) |s| {
        switch (s.shape) {
            .box => |bx| {
                if (bx.max.y - bx.min.y > 60) continue;

                if (x > bx.min.x - pad and x < bx.max.x + pad and z > bx.min.z - pad and z < bx.max.z + pad) return true;
            },
            else => {},
        }
    }

    return false;
}

const compound_solids = [_][6]f32{
    .{ -8.3, -8.3, 8.3, -7.7, -0.5, 3.2 },
    .{ -8.3, 7.7, -1.6, 8.3, -0.5, 3.2 },
    .{ 1.6, 7.7, 8.3, 8.3, -0.5, 3.2 },
    .{ -8.3, -8.3, -7.7, 8.3, -0.5, 3.2 },
    .{ 7.7, -8.3, 8.3, 8.3, -0.5, 3.2 },
    .{ -8.7, -8.7, -7.3, -7.3, -0.5, 3.8 },
    .{ 7.3, -8.7, 8.7, -7.3, -0.5, 3.8 },
    .{ -8.7, 7.3, -7.3, 8.7, -0.5, 3.8 },
    .{ 7.3, 7.3, 8.7, 8.7, -0.5, 3.8 },
    .{ -2.5, 7.55, -1.6, 8.45, -0.5, 4.0 },
    .{ 1.6, 7.55, 2.5, 8.45, -0.5, 4.0 },
    .{ -4.6, -6.7, 4.6, -0.5, -0.5, 4.15 },
    .{ -5.2, 2.5, -3.4, 4.3, -0.5, 0.9 },
    .{ -9.0, -1.0, -7.0, 1.0, -0.5, 5.0 },
    .{ 7.0, -1.0, 9.0, 1.0, -0.5, 5.0 },
    .{ -1.0, -9.0, 1.0, -7.0, -0.5, 5.0 },
};

pub var kit_loot: std.ArrayList(Vec3) = .empty;

fn kitCompound(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    const y = lowest(cx, cz, 8.5) + 0.3;

    b.placed.append(b.gpa, .{ .kind = .iv_compound, .pos = vec(cx, y, cz), .yaw = yaw, .scale = 1 }) catch {};

    for (compound_solids) |l| kitSolid(b, cx, cz, yaw, y, l);

    const yard = rotPoint(cx, cz, yaw, 2.5, 3.5);

    if (b.rng.next() < 0.6) {
        const f = rotPoint(cx, cz, yaw, 3.0, 9.8);

        b.putAt(.iv_flag, vec(f[0], terrain.height(f[0], f[1]) - 0.1, f[1]), yaw, 1);
    }

    const gate = rotPoint(cx, cz, yaw, 0, 11);

    kit_loot.append(b.gpa, vec(yard[0], y + 0.1, yard[1])) catch {};
    villageDress(b, cx, cz, yaw);

    if (b.rng.next() < 0.7) b.put(.iv_tree_round, gate[0] + b.rng.range(-5, 5), gate[1], b.rng.range(0, 6.28), b.rng.range(0.7, 0.9));
}

fn kitTower(b: *Builder, x: f32, z: f32, yaw: f32) void {
    b.putAt(.iv_tower, vec(x, lowest(x, z, 2) + 0.3, z), yaw, 1);
}

fn seatRock(b: *Builder, x: f32, z: f32, size: f32) void {
    const kinds = [_]Kind{ .iv_rock_a, .iv_rock_b, .iv_rock_c };

    b.putAt(b.rng.pick(Kind, &kinds), vec(x, lowest(x, z, size * 1.1) + 0.4 - size * 0.12, z), b.rng.range(0, 6.28), size);
}

fn bridgeRun(b: *Builder, ax: f32, az: f32, ay: f32, bx: f32, bz: f32, by: f32, sag: f32) void {
    const dx = bx - ax;
    const dz = bz - az;
    const len = @sqrt(dx * dx + dz * dz);
    const n: u32 = @intFromFloat(@ceil(len / 3.8));
    const yaw = std.math.atan2(-dz / len, dx / len);
    var k: u32 = 0;

    while (k < n) : (k += 1) {
        const t = (@as(f32, @floatFromInt(k)) + 0.5) / @as(f32, @floatFromInt(n));
        const x = ax + dx * t;
        const z = az + dz * t;
        const y = std.math.lerp(ay, by, t) - @sin(t * std.math.pi) * sag;

        b.placed.append(b.gpa, .{ .kind = .iv_bridge, .pos = vec(x, y, z), .yaw = yaw, .scale = 1 }) catch {};

        for ([_][2]f32{ .{ -2, -0.67 }, .{ -0.67, 0.67 }, .{ 0.67, 2 } }) |s| kitSolid(b, x, z, yaw, y, .{ s[0], -1.15, s[1], 1.15, -0.3, 0.06 });
    }
}

fn valleyBase(b: *Builder) void {
    runway(b);

    airstripPocket(b);
    ruinsPocket(b);
    oasisPocket(b);

    cHangar(b, -62, -194);
    tent(b, -98, -205);
    tent(b, -98, -230);
    fuelTank(b, 80, -228);
    kitTower(b, -40, -188, 0);
    kitTower(b, 82, -186, 0);

    const pass = terrain.roadLine(228);

    bunker(b, pass + 14, 228, 1);
    sandbags(b, pass - 11, 222, half_pi, 6);
    kitTower(b, pass - 16, 236, 0);
}

fn valleyBridges(b: *Builder) void {
    for (terrain.branches) |br| {
        if (br.x1 < 0) continue;

        var t: f32 = 0;
        var best_t: f32 = 0;
        var best: f32 = 1e9;

        while (t < 0.7) : (t += 0.004) {
            const p = terrain.branchPoint(br, t);
            const d = @abs(p[0] - terrain.riverLine(p[1]));

            if (d < best) {
                best = d;
                best_t = t;
            }
        }

        const c = terrain.branchPoint(br, best_t);
        const e = terrain.branchPoint(br, best_t + 0.01);
        const dx = e[0] - c[0];
        const dz = e[1] - c[1];
        const l = @sqrt(dx * dx + dz * dz);
        const ux = dx / l;
        const uz = dz / l;
        const y = terrain.valleyFloor(c[0], c[1]) + 0.12;

        bridgeRun(b, c[0] - ux * 9, c[1] - uz * 9, y, c[0] + ux * 9, c[1] + uz * 9, y, 0);
    }
}

fn valleyPlants(b: *Builder) void {
    const lim = terrain.play - 6;
    var x: f32 = -lim;

    while (x < lim) : (x += 6) {
        var z: f32 = -lim;

        while (z < lim) : (z += 6) {
            const px = x + b.rng.range(-2.5, 2.5);
            const pz = z + b.rng.range(-2.5, 2.5);

            if (terrain.baseMask(px, pz) > 0.05) continue;

            if (terrain.roadDistance(px, pz) < terrain.road_half + 2) continue;

            const rd = @abs(px - terrain.riverLine(pz));
            const wet = terrain.riverSpan(pz) > 0.5;

            if (wet and rd < 6) continue;

            if (covered(b, px, pz, 2.5)) continue;

            const h = terrain.height(px, pz);
            const rel = h - terrain.valleyFloor(px, pz);
            const n = terrain.normal(px, pz);
            const roll = b.rng.next();

            if (rel < 3) {
                if (wet and rd < 20) {
                    if (roll < 0.14) b.put(.iv_tree_round, px, pz, b.rng.range(0, 6.28), b.rng.range(0.75, 1.05)) else if (roll < 0.24) b.put(.iv_flowers, px, pz, b.rng.range(0, 6.28), b.rng.range(1, 1.5)) else if (roll < 0.4) b.put(b.rng.pick(Kind, &grasses), px, pz, b.rng.range(0, 6.28), b.rng.range(0.9, 1.3));
                } else if (roll < 0.03) {
                    b.put(.iv_tree_round, px, pz, b.rng.range(0, 6.28), b.rng.range(0.7, 0.95));
                } else if (roll < 0.05) {
                    seatRock(b, px, pz, b.rng.range(0.6, 1.1));
                } else if (roll < 0.1) {
                    b.put(.iv_bush, px, pz, b.rng.range(0, 6.28), b.rng.range(0.7, 1.2));
                } else if (roll < 0.24) {
                    b.put(b.rng.pick(Kind, &grasses), px, pz, b.rng.range(0, 6.28), b.rng.range(0.9, 1.3));
                }
            } else if (n.y > 0.82 and rel < 30 and terrain.troughDist(px, pz) < 44) {
                if (roll < 0.04) seatRock(b, px, pz, b.rng.range(0.9, 1.6)) else if (roll < 0.1) b.put(.iv_bush, px, pz, b.rng.range(0, 6.28), b.rng.range(0.8, 1.3)) else if (roll < 0.2) b.put(b.rng.pick(Kind, &grasses), px, pz, b.rng.range(0, 6.28), 1.2);
            }
        }
    }
}

fn cliffAt(b: *Builder, x: f32, z: f32, fx: f32, fz: f32, k: u32) void {
    const kinds = [_]Kind{ .iv_cliff_a, .iv_cliff_b, .iv_cliff_c };
    const depth = [_]f32{ 8.4, 7.0, 5.5 };
    const kind = kinds[k % 3];
    const s = b.rng.range(0.9, 1.2);
    const cx = x - fx * depth[k % 3] * s;
    const cz = z - fz * depth[k % 3] * s;

    if (terrain.baseMask(cx, cz) > 0.02 or covered(b, x, z, 6) or covered(b, cx, cz, 8)) return;

    if (terrain.roadDistance(x, z) < terrain.road_half + 4) return;

    var y = terrain.height(x, z);

    for ([_]f32{ -1, -0.5, 0.5, 1 }) |w| y = @min(y, terrain.height(x + fz * w * 12 * s, z - fx * w * 12 * s));

    b.putAt(kind, vec(cx, y - 1.0, cz), std.math.atan2(fx, fz) + b.rng.range(-0.12, 0.12), s);

    for ([_]f32{ -1, 1 }) |side| {
        const rx = x + fz * side * 7 * s + fx * 1.5;
        const rz = z - fx * side * 7 * s + fz * 1.5;

        if (b.rng.next() < 0.7) seatRock(b, rx, rz, b.rng.range(0.8, 1.5));
    }
}

fn valleyCliffs(b: *Builder) void {
    var z: f32 = -168;
    var k: u32 = 0;

    while (z < 238) : ({
        z += 24;
        k += 1;
    }) {
        const line = terrain.roadLine(z);
        const slope = terrain.roadLine(z + 1) - line;
        const l = @sqrt(1 + slope * slope);

        for ([_]f32{ -1, 1 }) |side| {
            const off: f32 = if (side > 0) 36 else 34;
            const x = line + side * off;

            if (terrain.troughDist(x, z) < off - 3) continue;

            cliffAt(b, x, z, -side / l, slope * side / l, k + @as(u32, if (side > 0) 1 else 0));
        }
    }

    for (terrain.branches) |br| {
        var t: f32 = 0.22;

        while (t < 0.95) : (t += 0.14) {
            const p = terrain.branchPoint(br, t);
            const q = terrain.branchPoint(br, t + 0.01);
            const dx = q[0] - p[0];
            const dz = q[1] - p[1];
            const l = @sqrt(dx * dx + dz * dz);
            const nx = -dz / l;
            const nz = dx / l;

            for ([_]f32{ -1, 1 }) |side| {
                const cx = p[0] + nx * side * 27;
                const cz = p[1] + nz * side * 27;

                if (@abs(cx - terrain.roadLine(cz)) < 40) continue;

                k += 1;
                cliffAt(b, cx, cz, -nx * side, -nz * side, k);
            }
        }
    }
}

fn roadGate(b: *Builder, z: f32) void {
    const x = terrain.roadLine(z);
    const yaw = std.math.atan2(terrain.roadLine(z + 1) - x, 1);
    const y = @min(terrain.height(x - 9, z), terrain.height(x + 9, z)) - 0.2;

    b.placed.append(b.gpa, .{ .kind = .iv_gate, .pos = vec(x, y, z), .yaw = yaw, .scale = 1 }) catch {};
    kitSolid(b, x, z, yaw, y, .{ -9.95, -0.95, -8.05, 0.95, -0.5, 6.6 });
    kitSolid(b, x, z, yaw, y, .{ 8.05, -0.95, 9.95, 0.95, -0.5, 6.6 });
}

fn landmark(b: *Builder, x: f32, z: f32, yaw: f32) void {
    b.putAt(.iv_landmark, vec(x, lowest(x, z, 2.2) + 0.3, z), yaw, 1);
}

fn terraceAt(b: *Builder, x: f32, z: f32, side: f32) void {
    if (covered(b, x, z, 1)) return;

    for ([_][2]f32{ .{ 0, 0 }, .{ -5, 6 }, .{ 5, 6 }, .{ 0, -6 } }) |o| {
        if (terrain.normal(x + o[0], z + o[1]).y < 0.9) return;
    }

    b.putAt(.iv_terrace, vec(x, lowest(x, z, 6) + 0.2, z), -side * half_pi, b.rng.range(0.95, 1.1));
}

fn ridgeAt(b: *Builder, x: f32, z: f32, fx: f32, fz: f32, k: u32) void {
    const big = k % 3 != 2;
    const half_d: f32 = if (big) 27.5 else 22.5;
    const s = b.rng.range(0.9, 1.15);
    const cx = x - fx * half_d * s;
    const cz = z - fz * half_d * s;

    if (terrain.baseMask(x, z) > 0.05 or covered(b, x, z, 3)) return;

    var y = terrain.height(x, z);

    for ([_]f32{ -1, -0.5, 0.5, 1 }) |w| y = @min(y, terrain.height(x + fz * w * 30 * s, z - fx * w * 30 * s));

    b.putAt(if (big) .iv_ridge_a else .iv_ridge_b, vec(cx, y - 1.5, cz), std.math.atan2(fx, fz) + b.rng.range(-0.15, 0.15), s);
}

fn valleyRidges(b: *Builder) void {
    var z: f32 = -150;
    var k: u32 = 0;

    while (z < 250) : ({
        z += 40;
        k += 1;
    }) {
        const line = terrain.roadLine(z);

        for ([_]f32{ -1, 1 }, 0..) |side, n| {
            const x = line + side * (46 + @as(f32, @floatFromInt((k + n) % 2)) * 30);

            if (terrain.troughDist(x, z) < 34) continue;

            const slope = terrain.roadLine(z + 1) - line;
            const l = @sqrt(1 + slope * slope);

            ridgeAt(b, x, z, -side / l, slope * side / l, k + @as(u32, if (side > 0) 1 else 0));
        }
    }

    for (terrain.branches) |br| {
        for ([_]f32{ 0.45, 0.85 }) |t| {
            const p = terrain.branchPoint(br, t);
            const q = terrain.branchPoint(br, t + 0.01);
            const dx = q[0] - p[0];
            const dz = q[1] - p[1];
            const l = @sqrt(dx * dx + dz * dz);
            const nx = -dz / l;
            const nz = dx / l;

            for ([_]f32{ -1, 1 }) |side| {
                k += 1;
                ridgeAt(b, p[0] + nx * side * 40, p[1] + nz * side * 40, -nx * side, -nz * side, k);
            }
        }
    }

    var sx: f32 = -150;

    while (sx <= 150) : (sx += 50) {
        var y = terrain.height(sx, -244);

        for ([_]f32{ -30, -15, 15, 30 }) |w| y = @min(y, terrain.height(sx + w, -244));

        b.putAt(if (@mod(sx, 100) == 0) .iv_ridge_a else .iv_ridge_b, vec(sx, y - 1.5, -244 - 26), b.rng.range(-0.12, 0.12), b.rng.range(1.1, 1.3));
    }

    var a: f32 = 0;

    while (a < 6.28) : (a += 0.3) {
        const r: f32 = 305;
        const x = @sin(a) * r;
        const z2 = @cos(a) * r;

        b.placed.append(b.gpa, .{ .kind = .iv_range, .pos = vec(x, terrain.height(x * 0.82, z2 * 0.82) - 6, z2), .yaw = a + std.math.pi + b.rng.range(-0.1, 0.1), .scale = b.rng.range(0.9, 1.3) }) catch {};
    }
}

fn forests(b: *Builder) void {
    const lim = terrain.play - 10;
    var x: f32 = -lim;

    while (x < lim) : (x += 26) {
        var z: f32 = -lim;

        while (z < lim) : (z += 26) {
            const cx = x + b.rng.range(-10, 10);
            const cz = z + b.rng.range(-10, 10);
            const rel = terrain.height(cx, cz) - terrain.valleyFloor(cx, cz);
            const td = terrain.troughDist(cx, cz);

            if (b.rng.next() > 0.6 or rel < 2 or rel > 40 or td > 62 or terrain.normal(cx, cz).y < 0.55) continue;

            if (terrain.baseMask(cx, cz) > 0.05 or terrain.roadDistance(cx, cz) < terrain.road_half + 6 or covered(b, cx, cz, 6)) continue;

            const count: u32 = @intFromFloat(b.rng.range(10, 30));
            const radius = b.rng.range(8, 16);
            var i: u32 = 0;

            while (i < count) : (i += 1) {
                const a = b.rng.range(0, 6.28);
                const r = radius * @sqrt(b.rng.next());
                const px = cx + @cos(a) * r;
                const pz = cz + @sin(a) * r;

                if (terrain.normal(px, pz).y < 0.55 or terrain.roadDistance(px, pz) < terrain.road_half + 2 or covered(b, px, pz, 1.5)) continue;

                const edge = r / radius;
                const kind: Kind = if (b.rng.next() < 0.55) .iv_pine_a else .iv_pine_b;

                b.put(kind, px, pz, b.rng.range(0, 6.28), b.rng.range(0.6, 1.0) + (1 - edge) * 0.45);
            }

            if (b.rng.next() < 0.6) seatRock(b, cx + radius + 2, cz, b.rng.range(1, 1.8));
        }
    }
}

fn villageDress(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    const spots = [_][4]f32{ .{ 11.5, -3, 0, 0 }, .{ -12, 2, 1.57, 1 }, .{ 11, 6, 0, 2 }, .{ -11, -7, 0, 2 }, .{ 3, -11.5, 0, 2 }, .{ -5, -11.5, 0, 3 }, .{ 12.5, 1, 0, 3 } };

    for (spots) |sp| {
        const w = rotPoint(cx, cz, yaw, sp[0], sp[1]);

        if (covered(b, w[0], w[1], 1.2) or terrain.roadDistance(w[0], w[1]) < terrain.road_half + 1) continue;

        const kind: Kind = switch (@as(u32, @intFromFloat(sp[3]))) {
            0 => .iv_hay,
            1 => .iv_cart,
            2 => .iv_bush,
            else => .iv_flowers,
        };

        b.put(kind, w[0], w[1], yaw + sp[2] + b.rng.range(-0.2, 0.2), 1);
    }

    var k: f32 = -8;

    while (k <= 8) : (k += 4.2) {
        const w = rotPoint(cx, cz, yaw, -14.5, k);

        if (covered(b, w[0], w[1], 0.6) or terrain.roadDistance(w[0], w[1]) < terrain.road_half + 1) continue;

        b.put(.iv_fence, w[0], w[1], yaw + half_pi + b.rng.range(-0.05, 0.05), 1);
    }
}

fn valleyLandmarks(b: *Builder) void {
    roadGate(b, -176);
    roadGate(b, 6);
    roadGate(b, 212);
    landmark(b, terrain.roadLine(-29) - 34, -29, half_pi);
    landmark(b, terrain.roadLine(240) + 24, 240, -half_pi);

    for ([_][2]f32{ .{ -80, -186 }, .{ -46, -186 }, .{ 30, -204 }, .{ 58, -204 } }) |p| b.putAt(.iv_flag, vec(p[0], terrain.height(p[0], p[1]), p[1]), 0, 1);

    for (valley_west) |z| {
        terraceAt(b, terrain.roadLine(z) - 38, z, -1);
        terraceAt(b, terrain.roadLine(z) + 42, z, 1);
    }
}

fn orchards(b: *Builder) void {
    for ([_][2]f32{ .{ 70, 100 }, .{ 150, 200 } }) |r| {
        var z = r[0];

        while (z < r[1]) : (z += 5) {
            var d: f32 = 12;

            while (d < 27) : (d += 5) {
                const x = terrain.roadLine(z) - d;

                if (covered(b, x, z, 2.5) or terrain.roadDistance(x, z) < terrain.road_half + 2) continue;

                b.put(.iv_orchard, x + b.rng.range(-0.4, 0.4), z + b.rng.range(-0.4, 0.4), b.rng.range(0, 6.28), b.rng.range(0.85, 1.1));
            }
        }
    }
}

var pocket_spawns: std.ArrayList([4]f32) = .empty;

fn pocketSpawn(b: *Builder, x: f32, z: f32, tx: f32, tz: f32) void {
    pocket_spawns.append(b.gpa, .{ x, z, tx, tz }) catch {};
}

fn ivPlatform(b: *Builder, x: f32, z: f32, quarter: u2) void {
    const yaw = @as(f32, @floatFromInt(quarter)) * half_pi;

    if (covered(b, x, z, 2.5)) return;

    const st = rotPoint(x, z, yaw, 0, 4);

    if (covered(b, st[0], st[1], 1.5) or terrain.roadDistance(st[0], st[1]) < terrain.road_half) return;

    const y = lowest(x, z, 2.2) + 0.4;
    const rise: geom.Rise = switch (quarter) {
        0 => .neg_z,
        1 => .neg_x,
        2 => .pos_z,
        3 => .pos_x,
    };
    const r = rotBox(x, z, yaw, -0.75, 2.0, 0.75, 6.0);

    b.placed.append(b.gpa, .{ .kind = .iv_platform, .pos = vec(x, y, z), .yaw = yaw, .scale = 1 }) catch {};
    kitSolid(b, x, z, yaw, y, .{ -2.0, -2.0, 2.0, 2.0, 2.95, 3.1 });
    kitSolid(b, x, z, yaw, y, .{ -2.0, -2.05, 2.0, -1.85, 3.1, 3.7 });
    kitSolid(b, x, z, yaw, y, .{ -2.05, -2.0, -1.85, 2.0, 3.1, 3.7 });
    kitSolid(b, x, z, yaw, y, .{ 1.85, -2.0, 2.05, 2.0, 3.1, 3.7 });

    for ([_][2]f32{ .{ -1.8, -1.8 }, .{ 1.8, -1.8 }, .{ -1.8, 1.8 }, .{ 1.8, 1.8 } }) |c| kitSolid(b, x, z, yaw, y, .{ c[0] - 0.12, c[1] - 0.12, c[0] + 0.12, c[1] + 0.12, -0.5, 2.95 });

    b.solid(.{ .ramp = .{ .min = vec(r[0], y, r[1]), .max = vec(r[2], y + 3.05, r[3]), .rise = rise } });
    kit_loot.append(b.gpa, vec(x, y + 3.1, z)) catch {};
}

fn ivPut(b: *Builder, kind: Kind, x: f32, z: f32, yaw: f32, pad: f32) void {
    if (covered(b, x, z, pad) or terrain.roadDistance(x, z) < terrain.road_half + 0.5) return;

    if (terrain.current == .islands and terrain.height(x, z) < terrain.void_floor + 5) return;

    b.put(kind, x, z, yaw, 1);
}

fn ivArch(b: *Builder, x: f32, z: f32, yaw: f32) void {
    if (covered(b, x, z, 3)) return;

    const y = lowest(x, z, 3) + 0.3;

    b.placed.append(b.gpa, .{ .kind = .iv_ruin_arch, .pos = vec(x, y, z), .yaw = yaw, .scale = 1 }) catch {};
    kitSolid(b, x, z, yaw, y, .{ -2.95, -0.55, -1.85, 0.55, -0.5, 5.3 });
    kitSolid(b, x, z, yaw, y, .{ 1.85, -0.55, 2.95, 0.55, -0.5, 5.3 });
    kitSolid(b, x, z, yaw, y, .{ -2.95, -0.6, 2.95, 0.6, 5.0, 7.2 });
}

fn market(b: *Builder, cx: f32, cz: f32) void {
    var k: f32 = 0;

    while (k < 6) : (k += 1) {
        const a = k / 6 * 6.283 + 0.25;
        const x = cx + @cos(a) * 11;
        const z = cz + @sin(a) * 11;

        ivPut(b, .iv_stall, x, z, std.math.atan2(cx - x, cz - z) + std.math.pi, 1);

        const a2 = a + 0.52;
        const x2 = cx + @cos(a2) * 8;
        const z2 = cz + @sin(a2) * 8;

        ivPut(b, b.rng.pick(Kind, &.{ .iv_hay, .iv_cart, .arena_crate_large, .iv_logs }), x2, z2, a2, 1);
        ivPut(b, b.rng.pick(Kind, &.{ .arena_jar_1, .arena_jar_2, .arena_crate_small }), x2 + 1.4, z2 + 0.6, a2, 0.3);
    }

    ivPut(b, .iv_flag, cx, cz, 0, 1);
    ivPlatform(b, cx - 18, cz, 1);
    kit_loot.append(b.gpa, vec(cx + 3, terrain.height(cx + 3, cz), cz)) catch {};
}

fn camp(b: *Builder, cx: f32, cz: f32) void {
    for ([_][3]f32{ .{ -6, -4, 0 }, .{ -6, 0, 0.1 }, .{ -5, 4, 1.57 }, .{ 6, 5, 0.3 }, .{ 7, -3, 1.2 } }) |o| ivPut(b, .iv_logs, cx + o[0], cz + o[1], o[2], 0.8);

    ivPut(b, .mil_tent, cx + 2, cz - 9, 0, 1.5);
    ivPut(b, .mil_tent, cx - 9, cz + 8, half_pi, 1.5);
    ivPut(b, .iv_cart, cx + 9, cz + 1, 0.4, 1);
    ivPut(b, .iv_hay, cx - 2, cz + 7, 0, 0.8);
    ivPlatform(b, cx + 2, cz + 13, 2);
}

fn valleyPockets(b: *Builder) void {
    pocket_spawns = .empty;

    const mz: f32 = -90;
    const mx = terrain.roadLine(mz) - 24;

    market(b, mx, mz);
    pocketSpawn(b, terrain.roadLine(-60) + 12, -60, mx, mz);

    const br = terrain.branches[1];
    const c = terrain.branchPoint(br, 0.42);

    camp(b, c[0], c[1] + 14);
    pocketSpawn(b, terrain.branchPoint(br, 0.25)[0], terrain.branchPoint(br, 0.25)[1], c[0], c[1] + 14);

    const pass = terrain.roadLine(228);

    ivPlatform(b, pass - 22, 214, 0);
    ivPlatform(b, pass + 26, 236, 2);
    pocketSpawn(b, terrain.roadLine(190) + 12, 190, pass, 230);

    ivPlatform(b, -100, -194, 0);
    ivPlatform(b, 92, -206, 0);

    for (valley_west, 0..) |z, i| {
        if (i % 2 == 1) ivPlatform(b, terrain.roadLine(z) + 12, z + 11, 2);
    }

    pocketSpawn(b, terrain.roadLine(10) + 12, 10, terrain.roadLine(40) - 19, 40);
    pocketSpawn(b, terrain.roadLine(95) + 12, 95, terrain.roadLine(120) - 19, 120);
    pocketSpawn(b, terrain.roadLine(-160) + 12, -160, terrain.roadLine(-29) - 34, -29);
}

fn islandPockets(b: *Builder) void {
    const isl = terrain.islands;
    const h = isl[2];
    const r = isl[3];

    ivPlatform(b, h.x, h.z + 22, 0);
    ivPlatform(b, -48, -118, 1);
    ivPlatform(b, 52, -184, 3);
    ivPlatform(b, r.x + 6, r.z + 2, 3);
}

const valley_west = [_]f32{ -150, -128, -40, -18, 30, 52, 110, 132 };

const village_houses = [_]struct { kind: Kind, w: f32, d: f32, side: f32 }{
    .{ .kind = .vl_house_a, .w = 7.6, .d = 6.4, .side = 0 },
    .{ .kind = .vl_house_b, .w = 6.8, .d = 6.0, .side = 1.6 },
    .{ .kind = .vl_house_c, .w = 8.8, .d = 6.8, .side = 0 },
};

pub fn hash2(a: f32, b: f32) f32 {
    const v = @sin(a * 12.9898 + b * 78.233) * 43758.5453;

    return v - @floor(v);
}

fn villageClear(x: f32, z: f32) bool {
    for (pocket_spawns.items) |ps| {
        if (@abs(ps[0] - x) < 11 and @abs(ps[1] - z) < 11) return false;
    }

    for (valley_west) |cz| {
        if (@abs(z - cz) < 12.5 and x < terrain.roadLine(z) and x > terrain.roadLine(z) - 32) return false;
    }

    for ([_]f32{ -176, 6, 212 }) |gz| {
        if (@abs(z - gz) < 11) return false;
    }

    if (terrain.riverSpan(z) > 0.05 and @abs(x - terrain.riverLine(z)) < 9.5) return false;

    if (@abs(x - terrain.valley_base[0]) < terrain.valley_base[2] + 14 and @abs(z - terrain.valley_base[1]) < terrain.valley_base[3] + 14) return false;

    return @abs(x) < terrain.play - 12 and @abs(z) < terrain.play - 12;
}

fn villageGround(x: f32, z: f32, r: f32) ?f32 {
    var hi: f32 = -1e9;
    var lo: f32 = 1e9;

    for ([_]f32{ -1, 0, 1 }) |sx| {
        for ([_]f32{ -1, 0, 1 }) |sz| {
            const h = terrain.height(x + sx * r, z + sz * r);

            hi = @max(hi, h);
            lo = @min(lo, h);
        }
    }

    if (hi - lo > 1.1) return null;

    return lo + 0.15;
}

fn valleyVillages(b: *Builder) void {
    var z: f32 = -terrain.play + 14;
    var n: u32 = 0;

    while (z < terrain.play - 14) : (z += 10.5) {
        for ([_][2]f32{ .{ -1, 0 }, .{ 1, 0 }, .{ -1, 1 }, .{ 1, 1 }, .{ -1, 2 }, .{ 1, 2 } }) |sr| {
            const side = sr[0];
            const pick = village_houses[(n + @as(u32, @intFromFloat(@abs(z))) / 7) % village_houses.len];
            const h1 = hash2(z * 0.31 + sr[1] * 7, side * 3.1);
            const h2 = hash2(z * 0.17 - sr[1] * 5, side * 1.7 + 2);
            const off = terrain.road_half + 2.6 + pick.d * 0.5 + sr[1] * (11.5 + h1 * 3) + h2 * 2.6;
            const zz = z + (h2 - 0.5) * 3.2;
            const x = terrain.roadLine(zz) + side * off;

            n += 1;

            if (h1 < 0.14) continue;

            if (sr[1] == 0 and @mod(@as(i32, @intFromFloat(@floor((z + 300) / 10.5))), 7) == 3) {
                if (!covered(b, x, zz, 3) and villageClear(x, zz)) {
                    const fy = terrain.height(x, zz) - 0.1;

                    for ([_][2]f32{ .{ -2, -2 }, .{ 2, -2 }, .{ -2, 2 }, .{ 2, 2 } }) |o| {
                        const px = x + o[0];
                        const pz = zz + o[1];

                        b.placed.append(b.gpa, .{ .kind = .vl_paving, .pos = vec(px, terrain.height(px, pz) + 0.03, pz), .yaw = 0, .scale = 1 }) catch {};
                    }

                    b.putAt(.vl_fountain, vec(x, fy, zz), 0, 1);
                }

                continue;
            }

            if (!villageClear(x, zz) or covered(b, x, zz, 4.6)) continue;

            const y = villageGround(x, zz, 4.4) orelse continue;
            const yaw = (if (side < 0) half_pi else -half_pi) + (h1 - 0.5) * 0.36;

            b.placed.append(b.gpa, .{ .kind = pick.kind, .pos = vec(x, y, zz), .yaw = yaw, .scale = 1 }) catch {};
            kitSolid(b, x, zz, yaw, y, .{ -pick.w * 0.5, -pick.d * 0.5, pick.w * 0.5 + pick.side, pick.d * 0.5, -1.6, 8.0 });

            const front = rotPoint(x, zz, yaw, 0, pick.d * 0.5 + 1.9);

            if (sr[1] == 0) {
                for ([_]f32{ -3.5, 0.5 }) |lx| {
                    const tp = rotPoint(front[0], front[1], yaw, lx, 0);
                    const th = terrain.height(tp[0], tp[1]);

                    if (@abs(th - y) < 0.8) b.placed.append(b.gpa, .{ .kind = .vl_paving, .pos = vec(tp[0], th + 0.03, tp[1]), .yaw = yaw, .scale = 1 }) catch {};
                }
            }

            if (sr[1] == 0 and n % 9 == 4) {
                const f = rotPoint(x, zz, yaw, -pick.w * 0.5 - 4.5, 1.0);

                if (!covered(b, f[0], f[1], 2.6)) b.putAt(.vl_fountain, vec(f[0], terrain.height(f[0], f[1]) - 0.1, f[1]), yaw, 1);
            }
        }
    }
}

fn valleyNature(b: *Builder) void {
    kit_loot = .empty;
    valleyBase(b);

    for (valley_west, 0..) |z, i| {
        kitCompound(b, terrain.roadLine(z) - 19, z, half_pi);

        if (i % 2 == 0) kitTower(b, terrain.roadLine(z - 14) - 12, z - 14, 0);
    }

    for (terrain.branches) |br| {
        const p = terrain.branchPoint(br, 0.6);
        const q = terrain.branchPoint(br, 0.61);
        const dx = q[0] - p[0];
        const dz = q[1] - p[1];
        const l = @sqrt(dx * dx + dz * dz);
        const nx = -dz / l;
        const nz = dx / l;

        for ([_]f32{ -1, 1 }) |s| {
            const cx = p[0] + nx * s * 19;
            const cz = p[1] + nz * s * 19;

            kitCompound(b, cx, cz, std.math.atan2(-nx * s, -nz * s));
        }

        const t = terrain.branchPoint(br, 0.8);

        kitTower(b, t[0], t[1], 0);
    }

    valleyBridges(b);
    valleyPockets(b);
    valleyVillages(b);
    valleyLandmarks(b);
    orchards(b);
    valleyRidges(b);
    forests(b);
    valleyPlants(b);
}

pub fn levelGround(x: f32, z: f32) bool {
    const h = terrain.height(x, z);

    if (terrain.current == .valley and terrain.riverSpan(z) > 0.05 and @abs(x - terrain.riverLine(z)) < 12) return false;

    for ([_][2]f32{ .{ -2.5, 0 }, .{ 2.5, 0 }, .{ 0, -2.5 }, .{ 0, 2.5 } }) |o| {
        if (@abs(terrain.height(x + o[0], z + o[1]) - h) > 0.25) return false;
    }

    return true;
}

fn valleySpots(gpa: std.mem.Allocator) void {
    var spawn_list: std.ArrayList(Vec3) = .empty;
    var yaw_list: std.ArrayList(f32) = .empty;
    var spots: std.ArrayList(Vec3) = .empty;
    var anchors: std.ArrayList(Vec3) = .empty;
    var parked: std.ArrayList(Spot) = .empty;
    var z: f32 = -176;
    var i: u32 = 0;

    while (z <= 226) : ({
        z += 18;
        i += 1;
    }) {
        const side: f32 = if (i % 2 == 0) 1 else -1;
        const ahead = terrain.roadLine(z + 1) - terrain.roadLine(z);
        const yaw = std.math.atan2(ahead, 1);

        spots.append(gpa, onRoad(z, side * 3)) catch {};

        if (i % 2 == 0) anchors.append(gpa, onRoad(z, side * 16).add(.{ .y = 13 })) catch {};

        const park = onRoad(z + 4, side * (terrain.road_half - 2.5));

        if (i % 2 == 0 and levelGround(park.x, park.z)) parked.append(gpa, .{ .pos = park, .yaw = if (side > 0) yaw else yaw + std.math.pi }) catch {};
    }

    for (kit_loot.items) |p| spots.append(gpa, p) catch {};

    for (pocket_spawns.items) |ps| {
        if (clearance(vec(ps[0], terrain.height(ps[0], ps[1]), ps[1])) < 2.5) continue;

        const sp = vec(ps[0], terrain.height(ps[0], ps[1]), ps[1]);
        const want = std.math.atan2(ps[2] - ps[0], ps[3] - ps[1]);
        var yaw = want;

        for ([_]f32{ 0, 0.45, -0.45, 0.9, -0.9, 1.4, -1.4, std.math.pi }) |off| {
            if (viewOpen(sp, want + off)) {
                yaw = want + off;

                break;
            }
        }

        spawn_list.append(gpa, sp) catch {};
        yaw_list.append(gpa, yaw) catch {};
    }

    spawns = spawn_list.toOwnedSlice(gpa) catch &.{};
    spawn_yaws = yaw_list.toOwnedSlice(gpa) catch &.{};
    weapon_spots = spots.toOwnedSlice(gpa) catch &.{};
    drone_anchors = anchors.toOwnedSlice(gpa) catch &.{};
    vehicle_spots = parked.toOwnedSlice(gpa) catch &.{};
}

const prism_tower_at: f32 = 64;
const prism_deck: f32 = 6;

fn prismBox(b: *Builder, x0: f32, y0: f32, z0: f32, x1: f32, y1: f32, z1: f32) void {
    b.solid(.{ .box = .{ .min = vec(@min(x0, x1), y0, @min(z0, z1)), .max = vec(@max(x0, x1), y1, @max(z0, z1)) } });
}

fn prismRotBox(b: *Builder, cx: f32, cz: f32, yaw: f32, hx: f32, hz: f32, y0: f32, y1: f32) void {
    const quarter = @mod(@as(i32, @intFromFloat(@round(yaw / half_pi))), 2) != 0;
    const ex = if (quarter) hz else hx;
    const ez = if (quarter) hx else hz;

    prismBox(b, cx - ex, y0, cz - ez, cx + ex, y1, cz + ez);
}

fn prismStair(b: *Builder, kind: Kind, fx: f32, fz: f32, y: f32, dir: geom.Rise, len: f32, w: f32, rise: f32) void {
    const yaw: f32 = switch (dir) {
        .neg_z => 0,
        .pos_z => std.math.pi,
        .neg_x => half_pi,
        .pos_x => -half_pi,
    };

    b.putAt(kind, vec(fx, y, fz), yaw, 1);

    const hw = w / 2;
    const r: geom.Ramp = switch (dir) {
        .neg_z => .{ .min = vec(fx - hw, y, fz - len), .max = vec(fx + hw, y + rise, fz), .rise = .neg_z },
        .pos_z => .{ .min = vec(fx - hw, y, fz), .max = vec(fx + hw, y + rise, fz + len), .rise = .pos_z },
        .neg_x => .{ .min = vec(fx - len, y, fz - hw), .max = vec(fx, y + rise, fz + hw), .rise = .neg_x },
        .pos_x => .{ .min = vec(fx, y, fz - hw), .max = vec(fx + len, y + rise, fz + hw), .rise = .pos_x },
    };

    b.solid(.{ .ramp = r });
}

fn prismCover(b: *Builder, x: f32, y: f32, z: f32, yaw: f32) void {
    b.putAt(.prism_cover, vec(x, y, z), yaw, 1);
    prismRotBox(b, x, z, yaw, 1.45, 0.5, y - 0.3, y + 1.2);
}

fn prismWall(b: *Builder, x: f32, y: f32, z: f32, yaw: f32) void {
    b.putAt(.prism_wall, vec(x, y, z), yaw, 1);
    prismRotBox(b, x, z, yaw, 4.0, 0.4, y - 0.3, y + 3.2);
}

pub const Pane = struct {
    min: Vec3,
    max: Vec3,
    pos: Vec3,
    piece: usize,
    broken: bool = false,
};

var pane_buf: [96]Pane = undefined;
var pane_n: usize = 0;

pub var panes: []Pane = &.{};

pub fn breakGlass(p: Vec3) ?Vec3 {
    for (panes) |*g| {
        if (g.broken) continue;

        if (p.x < g.min.x - 0.25 or p.x > g.max.x + 0.25 or p.y < g.min.y - 0.25 or p.y > g.max.y + 0.25 or p.z < g.min.z - 0.25 or p.z > g.max.z + 0.25) continue;

        g.broken = true;

        if (g.piece < pieces.len) pieces[g.piece].shape = .{ .box = .{ .min = vec(0, -900, 0), .max = vec(0.01, -899.99, 0.01) } };

        return g.min.add(g.max).scale(0.5);
    }

    return null;
}

pub fn paneBroken(pos: Vec3) bool {
    for (panes) |g| {
        if (g.broken and @abs(g.pos.x - pos.x) < 0.01 and @abs(g.pos.z - pos.z) < 0.01 and @abs(g.pos.y - pos.y) < 0.01) return true;
    }

    return false;
}

fn prismGlass(b: *Builder, x: f32, y: f32, z: f32, yaw: f32) void {
    b.putAt(.prism_glass_frame, vec(x, y, z), yaw, 1);
    b.putAt(.prism_glass_pane, vec(x, y, z), yaw, 1);

    const quarter = @mod(@as(i32, @intFromFloat(@round(yaw / half_pi))), 2) != 0;
    const ex: f32 = if (quarter) 0.12 else 2.1;
    const ez: f32 = if (quarter) 2.1 else 0.12;

    if (pane_n < pane_buf.len) {
        pane_buf[pane_n] = .{ .min = vec(x - ex, y, z - ez), .max = vec(x + ex, y + 2.5, z + ez), .pos = vec(x, y, z), .piece = b.solids.items.len };
        pane_n += 1;
    }

    prismRotBox(b, x, z, yaw, 2.1, 0.12, y - 0.3, y + 2.5);
}

fn prismPillar(b: *Builder, x: f32, y: f32, z: f32) void {
    b.putAt(.prism_pillar, vec(x, y, z), 0, 1);
    prismBox(b, x - 0.75, y - 0.3, z - 0.75, x + 0.75, y + 7, z + 0.75);
}

fn prismPlaza(b: *Builder) void {
    b.putAt(.prism_plaza, vec(0, 0, 0), 0, 1);
    prismBox(b, -14.4, -0.5, -14.4, 14.4, 2, 14.4);

    prismStair(b, .prism_stair_lo, 0, 20, 0, .neg_z, 6, 6, 2);
    prismStair(b, .prism_stair_lo, 0, -20, 0, .pos_z, 6, 6, 2);
    prismStair(b, .prism_stair_lo, 20, 0, 0, .neg_x, 6, 6, 2);
    prismStair(b, .prism_stair_lo, -20, 0, 0, .pos_x, 6, 6, 2);

    b.putAt(.prism_monolith, vec(0, 2, 0), half_pi * 0.5, 1);
    prismBox(b, -1.9, 2, -1.9, 1.9, 20, 1.9);
    b.putAt(.prism_ring, vec(0, 21, 0), 0, 1.6);
    b.putAt(.prism_ring, vec(0, 23.1, 0), half_pi, 1.25);

    for ([_]f32{ -1, 1 }) |sx| {
        for ([_]f32{ -1, 1 }) |sz| {
            prismCover(b, sx * 8, 2, sz * 9.5, 0);
            prismCover(b, sx * 9.5, 2, sz * 8, half_pi);
            b.putAt(.prism_plinth, vec(sx * 11.5, 2, sz * 11.5), 0, 1);
        }

        prismGlass(b, sx * 5.5, 2, 0, half_pi);
        prismGlass(b, 0, 2, sx * 5.5, 0);
    }
}

fn prismColonnade(b: *Builder, along_x: bool, side: f32) void {
    var i: i32 = -3;

    while (i <= 3) : (i += 1) {
        const t: f32 = @as(f32, @floatFromInt(i)) * 8;

        for ([_]f32{ 30, 38 }) |row| {
            if (i == 0) continue;

            if (along_x) prismPillar(b, t, 0, side * row) else prismPillar(b, side * row, 0, t);
        }

        if (i < 3) {
            const m = t + 4;

            if (along_x) b.putAt(.prism_slab, vec(m, 7, side * 34), 0, 1) else b.putAt(.prism_slab, vec(side * 34, 7, m), 0, 1);

            if (along_x) prismBox(b, m - 4, 7, side * 34 - 4, m + 4, 7.6, side * 34 + 4) else prismBox(b, side * 34 - 4, 7, m - 4, side * 34 + 4, 7.6, m + 4);
        }
    }
}

fn prismTower(b: *Builder, sx: f32, sz: f32) void {
    const cx = sx * prism_tower_at;
    const cz = sz * prism_tower_at;
    const top = prism_deck;

    b.putAt(.prism_tower, vec(cx, top - 6.6, cz), 0, 1);
    prismBox(b, cx - 8, top - 0.6, cz - 8, cx + 8, top, cz + 8);

    for ([_]f32{ -6.5, 6.5 }) |lx| {
        for ([_]f32{ -6.5, 6.5 }) |lz| prismBox(b, cx + lx - 0.8, -0.5, cz + lz - 0.8, cx + lx + 0.8, top - 0.6, cz + lz + 0.8);
    }

    const foot = sx * (prism_tower_at - 8 - 12);

    prismStair(b, .prism_stair_hi, foot, sz * (prism_tower_at - 5), 0, if (sx > 0) .pos_x else .neg_x, 12, 4, top);

    prismGlass(b, cx - sx * 4, top, cz - sz * 7.2, 0);
    prismGlass(b, cx - sx * 7.2, top, cz - sz * 1.5, half_pi);
    prismCover(b, cx + sx * 3, top, cz + sz * 2, half_pi * 0.0);
    b.putAt(.prism_plinth, vec(cx, top, cz), 0, 1);
}

fn prismRing(b: *Builder) void {
    const span = prism_tower_at - 8;
    var k: i32 = 0;

    while (k < 7) : (k += 1) {
        const t = -span + 8 + @as(f32, @floatFromInt(k)) * 16;

        for ([_]f32{ -1, 1 }) |s| {
            const edge = s * prism_tower_at;
            const y = prism_deck - 0.6;

            b.putAt(.prism_bridge, vec(t, y, edge), half_pi, 1);
            b.putAt(.prism_bridge, vec(edge, y, t), 0, 1);
            prismBox(b, t - 8, y, edge - 2.2, t + 8, prism_deck, edge + 2.2);
            prismBox(b, edge - 2.2, y, t - 8, edge + 2.2, prism_deck, t + 8);
            prismBox(b, t - 8, prism_deck, edge - 2.2, t + 8, prism_deck + 1.0, edge - 1.9);
            prismBox(b, t - 8, prism_deck, edge + 1.9, t + 8, prism_deck + 1.0, edge + 2.2);
            prismBox(b, edge - 2.2, prism_deck, t - 8, edge - 1.9, prism_deck + 1.0, t + 8);
            prismBox(b, edge + 1.9, prism_deck, t - 8, edge + 2.2, prism_deck + 1.0, t + 8);

            if (k > 0) {
                const j = t - 8;

                b.putAt(.prism_pillar, vec(j, y - 7, edge), 0, 1);
                b.putAt(.prism_pillar, vec(edge, y - 7, j), 0, 1);
                prismBox(b, j - 0.75, -0.5, edge - 0.75, j + 0.75, y, edge + 0.75);
                prismBox(b, edge - 0.75, -0.5, j - 0.75, edge + 0.75, y, j + 0.75);
            }
        }
    }
}

fn prismArches(b: *Builder) void {
    for ([_]f32{ -1, 1 }) |s| {
        for ([_]f32{ 50, 86 }) |d| {
            b.putAt(.prism_arch, vec(0, 0, s * d), 0, 1);
            b.putAt(.prism_arch, vec(s * d, 0, 0), half_pi, 1);

            for ([_]f32{ -1, 1 }) |leg| {
                prismBox(b, leg * 4.2 - 1.0, -0.5, s * d - 0.8, leg * 4.2 + 1.0, 8, s * d + 0.8);
                prismBox(b, s * d - 0.8, -0.5, leg * 4.2 - 1.0, s * d + 0.8, 8, leg * 4.2 + 1.0);
            }

            prismBox(b, -5, 4.6 + 3.4 * 0.85, s * d - 0.8, 5, 8.2, s * d + 0.8);
            prismBox(b, s * d - 0.8, 4.6 + 3.4 * 0.85, -5, s * d + 0.8, 8.2, 5);
        }
    }
}

fn prismQuadrants(b: *Builder) void {
    const wall_list = [_][3]f32{
        .{ 40, 22, 0 },       .{ 22, 44, half_pi }, .{ 30, 52, 0 },  .{ 52, 30, half_pi },
        .{ 96, 40, half_pi }, .{ 40, 100, 0 },      .{ 78, 104, 0 }, .{ 104, 78, half_pi },
    };
    const cover_list = [_][3]f32{
        .{ 28, 18, 0.3 },  .{ 18, 26, 1.2 },     .{ 46, 38, 0 },       .{ 38, 46, half_pi },
        .{ 58, 22, 0.8 },  .{ 22, 58, 0.8 },     .{ 74, 40, half_pi }, .{ 40, 74, 0 },
        .{ 90, 20, 0 },    .{ 20, 90, half_pi }, .{ 100, 58, 0.4 },    .{ 58, 100, 1.1 },
        .{ 84, 84, 0.78 }, .{ 70, 30, 0 },       .{ 30, 70, half_pi }, .{ 110, 104, 0 },
    };
    const pane_list = [_][3]f32{
        .{ 34, 12, half_pi }, .{ 12, 34, 0 }, .{ 48, 58, 0 }, .{ 58, 48, half_pi }, .{ 88, 30, half_pi }, .{ 30, 88, 0 },
    };

    for ([_]f32{ -1, 1 }) |sx| {
        for ([_]f32{ -1, 1 }) |sz| {
            for (wall_list) |w| prismWall(b, sx * w[0], 0, sz * w[1], w[2]);

            for (cover_list) |c| prismCover(b, sx * c[0], 0, sz * c[1], sx * sz * c[2]);

            for (pane_list) |g| prismGlass(b, sx * g[0], 0, sz * g[1], g[2]);

            prismTower(b, sx, sz);
        }
    }
}

fn prismOuter(b: *Builder) void {
    var a: f32 = 0;
    var i: u32 = 0;

    while (a < std.math.tau - 0.01) : (a += std.math.tau / 20.0) {
        const r: f32 = 118;
        const x = @sin(a) * r;
        const z = @cos(a) * r;
        const tall = 0.8 + 0.5 * @abs(@sin(a * 3.0));

        b.putAt(.prism_monolith, vec(x, 0, z), a, tall);
        prismRotBox(b, x, z, 0, 2.2 * tall, 2.2 * tall, -0.5, 18 * tall);
        i += 1;
    }

    var k: u32 = 0;

    while (k < 12) : (k += 1) {
        const pa = @as(f32, @floatFromInt(k)) * std.math.tau / 12.0 + 0.26;

        b.putAt(.prism_pad, vec(@sin(pa) * 96, 0.01, @cos(pa) * 96), 0, 1);
    }

    var rng: Rng = .{ .state = 0x9919 };
    var n: u32 = 0;

    while (n < 18) : (n += 1) {
        const ang = rng.range(0, std.math.tau);
        const dist = rng.range(72, 135);
        const x = @sin(ang) * dist;
        const z = @cos(ang) * dist;
        const y = if (dist > 100) rng.range(6, 30) else rng.range(12, 34);
        const s = rng.range(0.6, 2.4);

        b.putAt(.prism_cube, vec(x, y, z), rng.range(0, 6.28), s);
    }

    for ([_]f32{ -1, 1 }) |sx| {
        for ([_]f32{ -1, 1 }) |sz| {
            b.putAt(.prism_ring, vec(sx * 100, 4, sz * 100), sx * sz * 0.785, 2.2);

            var c: u32 = 0;

            while (c < 3) : (c += 1) {
                const fc: f32 = @floatFromInt(c);
                const x = sx * (108 - fc * 4);
                const z = sz * (82 + fc * 6);

                b.putAt(.prism_cube, vec(x, 0, z), fc * 0.4, 1.3);
                prismBox(b, x - 1.6, -0.3, z - 1.6, x + 1.6, 3.1, z + 1.6);
            }
        }
    }

    var d: f32 = 26;

    while (d < 118) : (d += 11) {
        for ([_]f32{ -1, 1 }) |s| {
            if (@abs(d - 50) < 6 or @abs(d - 86) < 6) continue;

            b.putAt(.prism_strip, vec(3.6, 0.01, s * d), half_pi, 1);
            b.putAt(.prism_strip, vec(-3.6, 0.01, s * d), half_pi, 1);
            b.putAt(.prism_strip, vec(s * d, 0.01, 3.6), 0, 1);
            b.putAt(.prism_strip, vec(s * d, 0.01, -3.6), 0, 1);
        }
    }
}

fn prismMap(b: *Builder) void {
    prismPlaza(b);

    for ([_]f32{ -1, 1 }) |s| {
        prismColonnade(b, true, s);
        prismColonnade(b, false, s);
    }

    prismRing(b);
    prismArches(b);
    prismQuadrants(b);
    prismOuter(b);
}

fn prismSpots(gpa: std.mem.Allocator) void {
    var spawn_list: std.ArrayList(Vec3) = .empty;
    var yaw_list: std.ArrayList(f32) = .empty;
    var spots: std.ArrayList(Vec3) = .empty;
    var anchors: std.ArrayList(Vec3) = .empty;
    var parked: std.ArrayList(Spot) = .empty;
    var k: u32 = 0;

    while (k < 12) : (k += 1) {
        const a = @as(f32, @floatFromInt(k)) * std.math.tau / 12.0 + 0.26;
        const p = vec(@sin(a) * 96, 0, @cos(a) * 96);

        spawn_list.append(gpa, p) catch {};
        yaw_list.append(gpa, a + std.math.pi) catch {};
    }

    for ([_]f32{ -1, 1 }) |sx| {
        for ([_]f32{ -1, 1 }) |sz| {
            spots.append(gpa, vec(sx * 11.5, 2.9, sz * 11.5)) catch {};
            spots.append(gpa, vec(sx * prism_tower_at, prism_deck + 0.9, sz * prism_tower_at)) catch {};
            spots.append(gpa, vec(sx * 34, 0, sz * 12)) catch {};
            spots.append(gpa, vec(sx * 70, 0, sz * 70)) catch {};
            spots.append(gpa, vec(sx * 100, 0, sz * 20)) catch {};
            parked.append(gpa, .{ .pos = vec(sx * 104, 0, sz * 30), .yaw = if (sx > 0) -half_pi else half_pi }) catch {};
        }
    }

    for (spots.items) |p| anchors.append(gpa, p.add(.{ .y = 10 })) catch {};

    spawns = spawn_list.toOwnedSlice(gpa) catch &.{};
    spawn_yaws = yaw_list.toOwnedSlice(gpa) catch &.{};
    weapon_spots = spots.toOwnedSlice(gpa) catch &.{};
    drone_anchors = anchors.toOwnedSlice(gpa) catch &.{};
    vehicle_spots = parked.toOwnedSlice(gpa) catch &.{};
    panes = pane_buf[0..pane_n];
}

fn courtyardMap(b: *Builder) void {
    const first = @backingInt(Kind.cy_t0);

    for (courtyard.tiles, 0..) |t, i| b.putAt(@fromBackingInt(@intCast(first + i)), vec(t[0], 0, t[1]), 0, 1);

    for (courtyard.boxes) |q| b.solid(.{ .box = .{ .min = vec(q[0], q[1], q[2]), .max = vec(q[3], q[4], q[5]) } });

    for (courtyard.ramps) |r| b.solid(.{ .ramp = .{ .min = vec(r.min[0], r.min[1], r.min[2]), .max = vec(r.max[0], r.max[1], r.max[2]), .rise = r.rise } });

    for (courtyard.palms) |p| b.putAt(if (p[3] < 0.5) .dk_palm_0 else .dk_palm_1, vec(p[0], p[1], p[2]), 0, 1);
}

fn courtyardSpots(gpa: std.mem.Allocator) void {
    var spawn_list: std.ArrayList(Vec3) = .empty;
    var yaw_list: std.ArrayList(f32) = .empty;
    var spots: std.ArrayList(Vec3) = .empty;
    var anchors: std.ArrayList(Vec3) = .empty;

    for (courtyard.spawns) |s| {
        spawn_list.append(gpa, vec(s[0], s[1], s[2])) catch {};
        yaw_list.append(gpa, s[3]) catch {};
    }

    for (courtyard.weapons) |w| {
        spots.append(gpa, vec(w[0], w[1], w[2])) catch {};
        anchors.append(gpa, vec(w[0], w[1] + 10, w[2])) catch {};
    }

    spawns = spawn_list.toOwnedSlice(gpa) catch &.{};
    spawn_yaws = yaw_list.toOwnedSlice(gpa) catch &.{};
    weapon_spots = spots.toOwnedSlice(gpa) catch &.{};
    drone_anchors = anchors.toOwnedSlice(gpa) catch &.{};
    vehicle_spots = &.{};
    panes = &.{};
}
