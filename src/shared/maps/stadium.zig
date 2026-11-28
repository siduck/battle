const std = @import("std");
const api = @import("api.zig");
const k = @import("stadium_kit.zig");

const t = api.terrain;
const wd = api.world;
const kit = k.kit;
const K = k.K;
const Builder = api.Builder;
const vec = api.vec;
const mix3 = api.mix3;
const hp = api.half_pi;

pub const def: api.Def = .{
    .name = "Stadium",
    .note = "Main stand, pitch and fan plaza",
    .tint = .{ 90, 160, 90 },
    .ready = true,
    .facet = 2.5,
    .height = height,
    .ground = ground,
    .build = build,
    .spots = setSpots,
    .props = &k.table,
    .palette = .{
        .sun_dir = .{ 0.48, 0.64, 0.6 },
        .sun_tint = .{ 1.16, 1.04, 0.9 },
        .grade_tint = .{ 1.02, 1.0, 0.97 },
        .grade_sat = 1.16,
        .fog = 0.0019,
        .fog_color = .{ 0.76, 0.84, 0.92 },
        .amb_sky = .{ 0.88, 0.98, 1.16 },
        .amb_ground = .{ 0.78, 0.78, 0.66 },
        .shade_tint = .{ 0.86, 0.92, 1.08 },
        .zenith = .{ 0.08, 0.3, 0.68 },
    },
    .backdrop = .{ 120, 150, 100 },
    .grip = 0.86,
};

const cell: f32 = 2;
const grid_half: f32 = api.arena_half + api.arena_rim;
const grid_n: comptime_int = @intFromFloat(grid_half * 2 / cell + 1);

var shade_grid: [grid_n * grid_n]f32 = @splat(0);

const Claim = struct { x: f32, z: f32, r: f32 };

var claims: [1024]Claim = undefined;
var claim_n: usize = 0;

fn claim(x: f32, z: f32, r: f32) void {
    if (claim_n >= claims.len) return;

    claims[claim_n] = .{ .x = x, .z = z, .r = r };
    claim_n += 1;
}

fn open(x: f32, z: f32, r: f32) bool {
    for (claims[0..claim_n]) |c| {
        const dx = c.x - x;
        const dz = c.z - z;

        if (dx * dx + dz * dz < (c.r + r) * (c.r + r)) return false;
    }

    return true;
}

fn splat(x: f32, z: f32, r: f32, strength: f32) void {
    const x0: i32 = @intFromFloat(@floor((x - r + grid_half) / cell));
    const x1: i32 = @intFromFloat(@ceil((x + r + grid_half) / cell));
    const z0: i32 = @intFromFloat(@floor((z - r + grid_half) / cell));
    const z1: i32 = @intFromFloat(@ceil((z + r + grid_half) / cell));
    var j = @max(z0, 0);

    while (j <= @min(z1, grid_n - 1)) : (j += 1) {
        var i = @max(x0, 0);

        while (i <= @min(x1, grid_n - 1)) : (i += 1) {
            const cx = @as(f32, @floatFromInt(i)) * cell - grid_half;
            const cz = @as(f32, @floatFromInt(j)) * cell - grid_half;
            const d = @sqrt((cx - x) * (cx - x) + (cz - z) * (cz - z)) / r;

            if (d >= 1) continue;

            const idx: usize = @intCast(j * grid_n + i);

            shade_grid[idx] = @min(1, shade_grid[idx] + (1 - d) * (1 - d) * strength);
        }
    }
}

fn shadeAt(x: f32, z: f32) f32 {
    const fx = (x + grid_half) / cell;
    const fz = (z + grid_half) / cell;

    if (fx < 0 or fz < 0 or fx >= grid_n - 1 or fz >= grid_n - 1) return 0;

    const i: usize = @intFromFloat(fx);
    const j: usize = @intFromFloat(fz);
    const ux = fx - @as(f32, @floatFromInt(i));
    const uz = fz - @as(f32, @floatFromInt(j));
    const a = std.math.lerp(shade_grid[j * grid_n + i], shade_grid[j * grid_n + i + 1], ux);
    const c = std.math.lerp(shade_grid[(j + 1) * grid_n + i], shade_grid[(j + 1) * grid_n + i + 1], ux);

    return std.math.lerp(a, c, uz);
}

const pitch_x: f32 = 52.5;
const pitch_z: f32 = 34;
const track_in: f32 = 38;
const track_out: f32 = 43.5;
const stand_front: f32 = 44;
const stand_depth: f32 = 10.5;
const stand_x: f32 = 60;
const end_front: f32 = api.arena_half - 9.5;
const pz: f32 = -(api.arena_half - 1 - stand_depth - stand_front);
const plaza_z: f32 = pz + pitch_z + 5;
const gate_z: f32 = api.arena_half - 2.5;
const fence_x: f32 = api.arena_half - 0.4;

fn inBox(x: f32, z: f32, x0: f32, z0: f32, x1: f32, z1: f32) bool {
    return x > x0 and x < x1 and z > z0 and z < z1;
}

fn rimEdge(x: f32, z: f32) f32 {
    return @max(@abs(x), @abs(z)) + (t.fbm(x * 0.02 + 5, z * 0.02 - 3) - 0.45) * 8;
}

fn height(x: f32, z: f32) f32 {
    const n1 = t.fbm(x * 0.014 + 3, z * 0.014 - 7);
    const n2 = t.fbm(x * 0.06, z * 0.06);
    const core = 1 - t.smooth(def.play + 2, def.play + 14, @max(@abs(x), @abs(z)));
    var h = ((n1 - 0.4) * 7 + (n2 - 0.45) * 1.2) * (1 - core) + 0.2;

    h = @max(h, 0.1);

    const e = rimEdge(x, z);
    const m = t.smooth(def.play + 4, def.half - 4, e);
    const ridged = 1 - @abs(2 * t.fbm(x * 0.012 + 9, z * 0.012 + 2) - 1);

    return h + m * m * (20 + 30 * ridged + 6 * n2);
}

fn turf(x: f32, z: f32, w: f32) [3]f32 {
    const band = @mod(@floor(x / w), 2);
    const check = @mod(@floor(z / (w * 1.6)), 2);
    const wear = t.fbm(x * 0.09 + 4, z * 0.09 - 2);
    var c: [3]f32 = if (band < 1) .{ 70, 134, 46 } else .{ 96, 160, 58 };

    c = mix3(c, if (check < 1) [3]f32{ 62, 124, 42 } else [3]f32{ 104, 166, 62 }, 0.18);
    c = mix3(c, .{ 128, 148, 72 }, t.smooth(0.62, 0.8, wear) * 0.3);

    return c;
}

const islands = [_][2]f32{ .{ 26, 44 }, .{ -26, 44 }, .{ 56, 42 }, .{ 20, 62 } };

fn fanLane(x: f32) bool {
    return @abs(x) < 7;
}

fn walkBand(z: f32) bool {
    return @abs(z - (plaza_z + 13)) < 2.6;
}

fn island(x: f32, z: f32, pad: f32) bool {
    for (islands) |q| {
        if (@abs(x - q[0]) < 6 + pad and @abs(z - q[1]) < 3.2 + pad) return true;
    }

    return false;
}

fn plaza(x: f32, z: f32) [3]f32 {
    const fx = x / 2 - @floor(x / 2);
    const fz = z / 2 - @floor(z / 2);
    const joint = fx < 0.05 or fz < 0.05;
    const slab = @mod(@floor(x / 2) * 3 + @floor(z / 2) * 7, 5) / 5;
    var c = mix3(.{ 176, 172, 162 }, .{ 158, 154, 146 }, slab * 0.8 + t.fbm(x * 0.15, z * 0.15) * 0.2);

    if (fanLane(x) or walkBand(z)) {
        const brick = @mod(@floor(x / 1.2) + @floor(z / 0.6), 2);

        c = if (brick < 1) .{ 132, 88, 74 } else .{ 120, 80, 68 };

        if (!walkBand(z) and @abs(@abs(x) - 6.8) < 0.2) c = .{ 190, 186, 176 };
    } else if (joint) {
        c = mix3(c, .{ 110, 106, 100 }, 0.6);
    }

    if (walkBand(z) and !fanLane(x) and @abs(@abs(z - (plaza_z + 13)) - 2.4) < 0.2) c = .{ 190, 186, 176 };

    if (island(x, z, 0.35)) c = .{ 196, 192, 182 };

    if (island(x, z, 0)) c = mix3(.{ 84, 140, 52 }, .{ 108, 156, 60 }, t.fbm(x * 0.4, z * 0.4));

    return c;
}

fn ground(x: f32, z: f32) api.Rgb {
    const n = t.normal(x, z);
    const slope = 1 - n.y;
    const vary = 0.95 + t.fbm(x * 0.11, z * 0.11) * 0.1;
    const p1 = t.fbm(x * 0.03 + 11, z * 0.03 - 4);
    var c = mix3(.{ 88, 138, 58 }, .{ 116, 156, 66 }, t.smooth(0.3, 0.62, p1));

    c = mix3(c, .{ 146, 160, 78 }, t.smooth(0.64, 0.8, t.fbm(x * 0.08 - 3, z * 0.08 + 8)) * 0.5);

    const under = shadeAt(x, z);

    c = mix3(c, .{ 76, 104, 50 }, t.smooth(0.15, 0.6, under) * 0.8);

    const lz = z - pz;

    if (@abs(x) < pitch_x + 3 and @abs(lz) < pitch_z + 3) {
        c = turf(x, lz, 5.25);
    } else if (lz < -track_in + 0.5 and lz > -track_out and @abs(x) < stand_x) {
        c = mix3(.{ 176, 82, 60 }, .{ 164, 74, 56 }, t.fbm(x * 0.3, z * 0.3));
    } else if (inBox(x, z, -def.play - 1, plaza_z, def.play + 1, def.play + 1)) {
        c = plaza(x, z);
    } else if (@abs(x) < def.play + 1 and @abs(z) < def.play + 1) {
        const tile = @mod(@floor(x / 4) + @floor(z / 4), 2);

        c = if (tile < 1) .{ 168, 166, 158 } else .{ 156, 154, 148 };
    }

    const rock = mix3(.{ 112, 110, 104 }, .{ 140, 136, 126 }, t.fbm(x * 0.15, z * 0.4));

    c = mix3(c, mix3(c, .{ 96, 124, 62 }, 0.6), t.smooth(0.2, 0.32, slope));
    c = mix3(c, rock, t.smooth(0.42, 0.58, slope));

    const ao = 1 - 0.36 * under;

    return api.shade(c, vary * ao + n.x * 0.03 - n.z * 0.02);
}

fn bld(e: K) api.Building {
    for (k.buildings) |b| {
        if (b.kind == kit.of(e)) return b;
    }

    return k.buildings[0];
}

fn house(b: *Builder, e: K, x: f32, z: f32, yaw: f32) void {
    const info = bld(e);

    claim(x, z, @max(info.w, info.d) * 0.5 + 1);
    _ = api.building(b, info, x, z, yaw);
}

fn put(b: *Builder, e: K, x: f32, z: f32, yaw: f32, s: f32) void {
    b.put(kit.of(e), x, z, yaw, s);
}

fn jit(b: *Builder, a: f32) f32 {
    return b.rng.range(-a, a);
}

fn dash(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32) void {
    const y = t.height((x0 + x1) / 2, (z0 + z1) / 2);

    b.deco(vec(@min(x0, x1) - 0.07, y + 0.02, @min(z0, z1) - 0.07), vec(@max(x0, x1) + 0.07, y + 0.05, @max(z0, z1) + 0.07), .flag_cloth);
}

fn line(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32) void {
    const dx = x1 - x0;
    const dz = z1 - z0;

    if (@abs(dx) < 0.05 or @abs(dz) < 0.05) return dash(b, x0, z0, x1, z1);

    const len = @sqrt(dx * dx + dz * dz);
    const n: usize = @intFromFloat(@ceil(len / 0.3));
    var i: usize = 0;

    while (i < n) : (i += 1) {
        const ua = @as(f32, @floatFromInt(i)) / @as(f32, @floatFromInt(n));
        const ub = @as(f32, @floatFromInt(i + 1)) / @as(f32, @floatFromInt(n));

        dash(b, x0 + dx * ua, z0 + dz * ua, x0 + dx * ub, z0 + dz * ub);
    }
}

fn ring(b: *Builder, cx: f32, cz: f32, r: f32, a0: f32, a1: f32) void {
    const n: usize = @intFromFloat(@max(8, @ceil(@abs(a1 - a0) * r / 2)));
    var i: usize = 0;

    while (i < n) : (i += 1) {
        const ua = a0 + (a1 - a0) * @as(f32, @floatFromInt(i)) / @as(f32, @floatFromInt(n));
        const ub = a0 + (a1 - a0) * @as(f32, @floatFromInt(i + 1)) / @as(f32, @floatFromInt(n));

        line(b, cx + @cos(ua) * r, cz + @sin(ua) * r, cx + @cos(ub) * r, cz + @sin(ub) * r);
    }
}

fn pitchLines(b: *Builder) void {
    line(b, -pitch_x, pz - pitch_z, pitch_x, pz - pitch_z);
    line(b, -pitch_x, pz + pitch_z, pitch_x, pz + pitch_z);
    line(b, -pitch_x, pz - pitch_z, -pitch_x, pz + pitch_z);
    line(b, pitch_x, pz - pitch_z, pitch_x, pz + pitch_z);
    line(b, 0, pz - pitch_z, 0, pz + pitch_z);
    ring(b, 0, pz, 9.15, 0, std.math.tau);
    line(b, -0.2, pz - 0.2, 0.2, pz + 0.2);

    for ([_]f32{ -1, 1 }) |s| {
        const gx = s * pitch_x;
        const bx = gx - s * 16.5;
        const sx = gx - s * 5.5;

        line(b, bx, pz - 20.15, bx, pz + 20.15);
        line(b, gx, pz - 20.15, bx, pz - 20.15);
        line(b, gx, pz + 20.15, bx, pz + 20.15);
        line(b, sx, pz - 9.16, sx, pz + 9.16);
        line(b, gx, pz - 9.16, sx, pz - 9.16);
        line(b, gx, pz + 9.16, sx, pz + 9.16);
        line(b, gx - s * 11 - 0.15, pz - 0.15, gx - s * 11 + 0.15, pz + 0.15);

        if (s > 0) ring(b, gx - 11, pz, 9.15, std.math.pi - 0.927, std.math.pi + 0.927) else ring(b, gx + 11, pz, 9.15, -0.927, 0.927);
        b.putAt(kit.of(.goal), vec(gx + s * 1, t.height(gx, pz), pz), -s * hp, 1);
    }

    for ([_][2]f32{ .{ -1, -1 }, .{ -1, 1 }, .{ 1, -1 }, .{ 1, 1 } }) |c| put(b, .cornerflag, c[0] * pitch_x, pz + c[1] * pitch_z, 0, 1);

    var lane: f32 = track_in + 1.1;

    while (lane < track_out) : (lane += 1.1) line(b, -stand_x + 2, pz - lane, stand_x - 2, pz - lane);
}

fn standRow(b: *Builder, x0: f32, x1: f32, zf: f32, side: f32, roofed: bool) void {
    const y = t.height((x0 + x1) / 2, zf) - 0.05;
    const yaw: f32 = if (side < 0) 0 else std.math.pi;
    const zc = zf + side * stand_depth / 2;
    var x = x0 + 0.75;

    while (x < x1) : (x += 1.5) {
        b.putAt(kit.of(.seats), vec(x, y, zc), yaw, 1);

        if (roofed) b.putAt(kit.of(.roof), vec(x, y, zc - side * 0.4), yaw, 1);
    }

    const za = @min(zf, zf + side * stand_depth);
    const zb = @max(zf, zf + side * stand_depth);

    b.solid(.{ .ramp = .{ .min = vec(x0, y, za), .max = vec(x1, y + 6.3, zb), .rise = if (side < 0) .neg_z else .pos_z } });

    const back = zf + side * (stand_depth + 0.3);

    api.box(b, x0, y - 1, @min(back, back - side * 0.4), x1, y + 7.4, @max(back, back - side * 0.4));

    for ([_]f32{ x0 - 0.9, x1 + 0.9 }) |gx| {
        b.putAt(kit.of(.gable), vec(gx, y, zc), hp, 1);
        api.box(b, gx - 0.9, y - 1, zc - 5.4, gx + 0.9, y + 9, zc + 5.4);
    }

    claim((x0 + x1) / 2, zc, 0);
}

fn terraceRow(b: *Builder, xf: f32, side: f32, z0: f32, z1: f32) void {
    const y = t.height(xf, (z0 + z1) / 2) - 0.05;
    const yaw: f32 = if (side > 0) -hp else hp;
    const xc = xf + side * 4.5;
    var z = z0 + 0.75;

    while (z < z1) : (z += 1.5) b.putAt(kit.of(.terrace), vec(xc, y, z), yaw, 1);

    const xa = @min(xf, xf + side * 9);
    const xb = @max(xf, xf + side * 9);

    b.solid(.{ .ramp = .{ .min = vec(xa, y, z0), .max = vec(xb, y + 7.2, z1), .rise = if (side > 0) .pos_x else .neg_x } });

    const back = xf + side * 9.3;

    api.box(b, @min(back, back + side * 0.4), y - 1, z0, @max(back, back + side * 0.4), y + 8, z1);
}

const ads = [_]K{ .ad_red, .ad_navy, .ad_gold };

fn ad(i: usize) K {
    return ads[i % ads.len];
}

const Spot = struct { e: K, x: f32, z: f32, yaw: f32, s: f32 = 1 };

fn spots(b: *Builder, list: []const Spot, ox: f32, oz: f32, mirror: bool) void {
    for (list) |p| {
        put(b, p.e, ox + p.x, oz + p.z, p.yaw, p.s);
        claim(ox + p.x, oz + p.z, 1.5);

        if (mirror) {
            put(b, p.e, ox - p.x, oz - p.z, p.yaw + std.math.pi, p.s);
            claim(ox - p.x, oz - p.z, 1.5);
        }
    }
}

fn boardsX(b: *Builder, x0: f32, x1: f32, z: f32, yaw: f32, s: f32, skip: []const f32, seed: usize) void {
    const step = 6 * s;
    var x = x0 + step / 2;
    var i: usize = seed;

    outer: while (x < x1) : (x += step) {
        for (skip) |q| if (@abs(x - q) < step / 2) continue :outer;

        put(b, ad(i), x, z, yaw, s);
        i += 1;
    }
}

fn boardsZ(b: *Builder, z0: f32, z1: f32, x: f32, yaw: f32, s: f32, skip: []const f32, seed: usize) void {
    const step = 6 * s;
    var z = z0 + step / 2;
    var i: usize = seed;

    outer: while (z < z1) : (z += step) {
        for (skip) |q| if (@abs(z - q) < step / 2) continue :outer;

        put(b, ad(i), x, z, yaw, s);
        i += 1;
    }
}

fn facade(b: *Builder, x: f32, z: f32, yaw: f32, gate: bool) void {
    const y = t.height(x, z) - 0.1;

    b.putAt(kit.of(if (gate) .sback_gate else .sback_wall), vec(x, y, z), yaw, 1);
}

fn bowl(b: *Builder) void {
    const zf = pz - stand_front;

    standRow(b, -stand_x, -6, zf, -1, true);
    standRow(b, 6, stand_x, zf, -1, true);
    terraceRow(b, end_front, 1, pz - 30, pz + 30);
    terraceRow(b, -end_front, -1, pz - 30, pz + 30);
    house(b, .tunnel, 0, zf - 2, 0);

    const zb = zf - stand_depth - 0.75;
    var i: usize = 0;
    var x: f32 = -57;

    while (x < 58) : (x += 6) {
        if (@abs(x) > 8) facade(b, x, zb, std.math.pi, i % 3 == 1);

        i += 1;
    }

    var z: f32 = pz - 27;

    i = 0;

    while (z < pz + 28) : (z += 6) {
        facade(b, end_front + 10.1, z, hp, i % 4 == 1);
        facade(b, -end_front - 10.1, z, -hp, i % 4 == 2);
        i += 1;
    }

    for ([_][2]f32{ .{ -69, pz - track_in + 1 }, .{ 69, pz - track_in + 1 }, .{ -69, pz + track_in }, .{ 69, pz + track_in } }) |p| {
        put(b, .flood, p[0], p[1], std.math.atan2(-p[0], pz - p[1]), 1);
        claim(p[0], p[1], 3);
    }

    boardsX(b, -48, 48, pz - pitch_z - 3, 0, 1, &.{ -27, 0, 27 }, 0);
    boardsX(b, -48, 48, pz + pitch_z + 3, std.math.pi, 1, &.{ -27, 27 }, 1);
    boardsZ(b, pz - 30, pz + 30, -pitch_x - 4, hp, 1, &.{ pz - 15, pz + 15 }, 2);
    boardsZ(b, pz - 30, pz + 30, pitch_x + 4, -hp, 1, &.{ pz - 15, pz + 15 }, 0);

    put(b, .dugout, -12, pz + pitch_z + 6.5, std.math.pi, 1);
    put(b, .dugout, 12, pz + pitch_z + 6.5, std.math.pi, 1);
    put(b, .bench, -20, pz + pitch_z + 6, std.math.pi, 1);
    put(b, .bench, 20, pz + pitch_z + 6, std.math.pi, 1);
    put(b, .scoreboard, end_front - 4, pz + 36, -hp - 0.4, 1);
    put(b, .scoreboard, -end_front + 4, pz - 36, hp - 0.4, 1);

    for ([_]f32{ -36, 36 }) |px| {
        put(b, .crate, px, pz + pitch_z + 6.2, 0, 1);
        put(b, .crate, px + 0.8, pz + pitch_z + 6.3, 0.3, 1);
        put(b, .kitbag, px - 1.2, pz + pitch_z + 6.2, 1.2, 1);
    }

    for ([_]f32{ track_in + 1.6, track_in + 3.8 }) |lz| {
        x = -40;

        while (x < 41) : (x += 10) put(b, .hurdle, x, pz - lz, hp, 1);
    }

    for ([_]f32{ -1, 1 }) |s| {
        house(b, .kiosk, s * 68, zf - 6.5, if (s > 0) -hp else hp);
        put(b, .bin, s * 65, zf - 2.5, 0, 1);
        put(b, .pallet, s * 71, zf - 0.5, 0.2, 1);
        put(b, .crate, s * 71.5, zf - 1.9, 0.5, 1);
        barrierLine(b, .mesh, s * fence_x, zf - 10.5, s * fence_x, pz - 30, 2.4, 1);
        barrierLine(b, .mesh, s * (stand_x + 1.8), zf - 10.8, s * fence_x, zf - 10.8, 2.4, 1);
    }
}

const pitch_cover = [_]Spot{
    .{ .e = .ad_red, .x = 18, .z = 8, .yaw = 0, .s = 1.2 },
    .{ .e = .ad_navy, .x = 22, .z = 12, .yaw = hp, .s = 1.2 },
    .{ .e = .ad_gold, .x = 36, .z = -14, .yaw = hp, .s = 1.2 },
    .{ .e = .ad_navy, .x = 6, .z = -24, .yaw = 0, .s = 1.2 },
    .{ .e = .ad_red, .x = 44, .z = 22, .yaw = 0.3, .s = 1.2 },
    .{ .e = .medtent, .x = 30, .z = 20, .yaw = 2.6 },
    .{ .e = .scaffold, .x = 32, .z = 2, .yaw = 0 },
    .{ .e = .scaffold, .x = 0, .z = 20, .yaw = 0.2 },
    .{ .e = .tarp, .x = 12, .z = -6, .yaw = 0.3 },
    .{ .e = .tarp, .x = 13, .z = -3.4, .yaw = 0.3 },
    .{ .e = .tarp, .x = 24, .z = -24, .yaw = 1.4 },
    .{ .e = .sled, .x = 26, .z = -5, .yaw = 0.4 },
    .{ .e = .sled, .x = 8, .z = 14, .yaw = -0.2 },
    .{ .e = .dummy, .x = 44, .z = -6, .yaw = 0 },
    .{ .e = .dummy, .x = 45, .z = -3, .yaw = 0 },
    .{ .e = .dummy, .x = 43.5, .z = 0, .yaw = 0 },
    .{ .e = .rack, .x = 40, .z = 10, .yaw = 1.2 },
    .{ .e = .rack, .x = 16, .z = 24, .yaw = 0.1 },
    .{ .e = .inflatable, .x = 48, .z = -22, .yaw = -hp },
    .{ .e = .tactics, .x = 20, .z = 5.5, .yaw = 0.5 },
    .{ .e = .crate, .x = 19, .z = 6.6, .yaw = 0 },
    .{ .e = .crate, .x = 33, .z = -12.5, .yaw = 0.4 },
    .{ .e = .kitbag, .x = 34, .z = -15.8, .yaw = 1 },
    .{ .e = .pallet, .x = 7, .z = -22.4, .yaw = 0 },
    .{ .e = .pallet, .x = 8.1, .z = -22.5, .yaw = 0.2 },
    .{ .e = .cones, .x = 28, .z = 12, .yaw = 0.8 },
    .{ .e = .cones, .x = 4, .z = 6, .yaw = 2.1 },
};

fn matchDay(b: *Builder) void {
    spots(b, &pitch_cover, 0, pz, true);
    put(b, .inflatable, 0, pz - pitch_z - 0.5, 0, 1);
    put(b, .medtent, -6, pz, 0.3, 1);
    put(b, .medtent, 6, pz, 0.3 + std.math.pi, 1);
}

fn picnicSet(b: *Builder, x: f32, z: f32, yaw: f32) void {
    put(b, .parasol, x, z, yaw, 1.15);
    put(b, .picnic, x + @cos(yaw) * 0.1, z - @sin(yaw) * 0.1, yaw, 1.1);
    put(b, .bin, x + 2.2, z + 1.4, 0, 1);
    claim(x, z, 2.5);
}

fn stallRow(b: *Builder, x0: f32, z: f32, n: usize, yaw: f32) void {
    var i: usize = 0;

    while (i < n) : (i += 1) {
        const x = x0 + @as(f32, @floatFromInt(i)) * 4.6;

        put(b, .stall, x, z, yaw, 1.35);
        put(b, if (i % 2 == 0) .crate else .pallet, x + 2.3, z + 1.2, 0.3, 1);
        claim(x, z, 2.5);
    }
}

fn loos(b: *Builder, x: f32, z: f32, yaw: f32) void {
    var i: usize = 0;
    const cx = @cos(yaw);
    const sz = -@sin(yaw);

    while (i < 5) : (i += 1) {
        const o = @as(f32, @floatFromInt(i)) * 1.5;

        put(b, .ptoilet, x + cx * o, z + sz * o, yaw, 1);
    }

    put(b, .generator, x + cx * 9, z + sz * 9, yaw + hp, 1);
    claim(x + cx * 3, z + sz * 3, 5);
}

fn barrierLine(b: *Builder, e: K, x0: f32, z0: f32, x1: f32, z1: f32, step: f32, s: f32) void {
    const dx = x1 - x0;
    const dz = z1 - z0;
    const len = @sqrt(dx * dx + dz * dz);
    const n: usize = @intFromFloat(@max(1, @round(len / step)));
    const yaw = std.math.atan2(dx, dz) - hp;
    var i: usize = 0;

    while (i < n) : (i += 1) {
        const u = (@as(f32, @floatFromInt(i)) + 0.5) / @as(f32, @floatFromInt(n));

        put(b, e, x0 + dx * u, z0 + dz * u, yaw, s);
    }
}

fn concourse(b: *Builder) void {
    house(b, .gate, 0, gate_z, 0);

    for ([_]f32{ -24, -14, 14, 24 }) |x| house(b, .turnstile, x, gate_z, 0);

    for ([_]f32{ -40, 40 }) |x| house(b, .booth, x, gate_z - 2, 0);

    var x: f32 = -fence_x + 1.2;

    while (x < fence_x) : (x += 2.4) {
        if (@abs(x) < 4.4 or @abs(@abs(x) - 14) < 2.1 or @abs(@abs(x) - 24) < 2.1) continue;

        put(b, .wall, x, fence_x, 0, 1);
    }

    for ([_]f32{ -1, 1 }) |s| {
        barrierLine(b, .rail, s * 9, gate_z - 12, s * 9, gate_z - 4, 2, 1);
        barrierLine(b, .rail, s * 19, gate_z - 14, s * 19, gate_z - 4, 2, 1);
        barrierLine(b, .rail, s * 29, gate_z - 12, s * 29, gate_z - 4, 2, 1);
        put(b, .banner, s * 34, gate_z - 4, 0, 1);
        put(b, .banner, s * 4.5, gate_z - 4, 0, 1);
        barrierLine(b, .mesh, s * fence_x, pz + 31, s * fence_x, fence_x - 1, 2.4, 1);
    }
}

fn stage(b: *Builder, cx: f32, cz: f32) void {
    const deck_y = t.height(cx, cz) + 0.9;

    b.mass(vec(cx - 9, deck_y - 2, cz - 5), vec(cx + 9, deck_y, cz + 5), .concrete);
    b.solid(.{ .ramp = .{ .min = vec(cx - 4, deck_y - 2, cz - 9), .max = vec(cx + 4, deck_y, cz - 5), .rise = .pos_z } });
    b.deco(vec(cx - 4, deck_y - 2, cz - 9), vec(cx + 4, deck_y - 0.4, cz - 5), .concrete);
    b.putAt(kit.of(.ad_navy), vec(cx, deck_y + 3.2, cz + 4.6), std.math.pi, 2.6);
    b.putAt(kit.of(.scaffold), vec(cx - 10.5, deck_y - 0.9, cz + 4), std.math.pi, 1);
    b.putAt(kit.of(.scaffold), vec(cx + 10.5, deck_y - 0.9, cz + 4), std.math.pi, 1);
    put(b, .generator, cx - 12, cz - 2, hp, 1);
    claim(cx, cz, 13);
}

fn cluster(b: *Builder, x: f32, z: f32, pick: usize, yaw: f32, i: usize) void {
    const cx = @cos(yaw);
    const sz = -@sin(yaw);

    switch (pick % 6) {
        0 => {
            put(b, ad(i), x, z, yaw, 1.8);
            put(b, .bin, x + sz * 1.6, z - cx * 1.6, 0, 1);
            put(b, .planter, x + cx * 6 + sz * 1.2, z + sz * 6 - cx * 1.2, 0, 1.3);
        },
        1 => {
            put(b, .waterbar, x, z, yaw, 1);
            put(b, .waterbar, x + cx * 3.6 + sz * 1.4, z + sz * 3.6 - cx * 1.4, yaw + 0.6, 1);
            put(b, .crate, x - cx * 2.6, z - sz * 2.6, 0.2, 1);
            put(b, .crate, x - cx * 2.0, z - sz * 2.0 + 0.6, 0.9, 1);
        },
        2 => {
            put(b, .tarp, x, z, yaw, 1);
            put(b, .tarp, x + sz * 2.4, z - cx * 2.4, yaw, 1);
            put(b, .pallet, x + cx * 2.6, z + sz * 2.6, yaw, 1);
            put(b, .pallet, x + cx * 3.7, z + sz * 3.7, yaw + 0.2, 1);
        },
        3 => {
            put(b, .jersey, x, z, yaw, 1.3);
            put(b, .jersey, x + cx * 2.7, z + sz * 2.7, yaw, 1.3);
            put(b, .jersey, x + cx * 5.4, z + sz * 5.4, yaw, 1.3);
            put(b, .kitbag, x + sz * 1.2, z - cx * 1.2, 0.4, 1);
        },
        4 => {
            put(b, .medtent, x, z, yaw, 1);
            put(b, .rack, x + cx * 3.6, z + sz * 3.6, yaw, 1);
            put(b, .crate, x - cx * 3, z - sz * 3, 0.1, 1);
        },
        else => {
            put(b, .stall, x, z, yaw, 1.35);
            put(b, .stall, x + cx * 4.4, z + sz * 4.4, yaw, 1.35);
            put(b, .pallet, x - cx * 2.6, z - sz * 2.6 + 1, yaw, 1);
        },
    }

    claim(x, z, 4);
}

fn fanPlaza(b: *Builder) void {
    stage(b, -46, gate_z - 16);

    for (islands) |q| {
        put(b, .oak, q[0], q[1], q[0] * 0.1, 1.2);
        put(b, .bush, q[0] - 3.6, q[1] + 0.8, 0.3, 0.9);
        put(b, .bush, q[0] + 3.8, q[1] - 0.6, 1.3, 0.8);
        put(b, .banner, q[0] + 5.2, q[1] + 2.4, 0, 1);
        put(b, .bin, q[0] - 6.6, q[1] - 2.2, 0, 1);
        claim(q[0], q[1], 6);
    }

    for ([_]f32{ -1, 1 }) |s| {
        stallRow(b, if (s > 0) 36 else -49.8, plaza_z + 6, 4, std.math.pi);
        house(b, .snackbox, s * 66, plaza_z + 8, if (s > 0) -hp else hp);
        put(b, .ad_red, s * 16, plaza_z + 24, hp, 2);
        put(b, .bin, s * 10, plaza_z + 3, 0, 1);
    }

    picnicSet(b, 34, gate_z - 20, 0.6);
    picnicSet(b, 46, gate_z - 24, 2.0);
    picnicSet(b, 40, gate_z - 10, 1.2);
    picnicSet(b, -22, gate_z - 14, 0.3);
    put(b, .shelter, 60, gate_z - 18, 0.1, 1);
    claim(60, gate_z - 18, 5);
    put(b, .picnic, 59, gate_z - 17, 0.1, 1.1);
    loos(b, 56, gate_z - 6, 0);
    loos(b, -70, plaza_z + 16, -hp);
    put(b, .flood, 0, plaza_z + 22, 0, 0.8);
    claim(0, plaza_z + 22, 2);

    var placed: usize = 0;
    var tries: usize = 0;

    while (placed < 8 and tries < 300) : (tries += 1) {
        const x = b.rng.range(-def.play + 8, def.play - 8);
        const z = b.rng.range(plaza_z + 6, gate_z - 6);

        if (fanLane(x) or fanLane(x + 4) or fanLane(x - 4) or walkBand(z) or walkBand(z + 4) or walkBand(z - 4) or island(x, z, 3)) continue;

        if (!open(x, z, 6)) continue;

        cluster(b, x, z, placed + tries, @round(b.rng.range(0, 4)) * hp + jit(b, 0.25), placed);
        placed += 1;
    }
}

fn treeLine(b: *Builder) void {
    const span = def.play + 6;
    var side: usize = 0;

    while (side < 4) : (side += 1) {
        var a: f32 = -span;

        while (a < span) : (a += 9) {
            const along = a + jit(b, 3);
            const out = def.play + b.rng.range(4, 10);
            const x = switch (side) {
                0, 1 => along,
                2 => -out,
                else => out,
            };
            const z = switch (side) {
                0 => -out,
                1 => out,
                else => along,
            };
            const roll = b.rng.next();
            const tree: K = if (roll < 0.45) .oak else if (roll < 0.75) .birch else .pine;

            put(b, tree, x, z, b.rng.range(0, 6), b.rng.range(1.1, 1.8));

            if (b.rng.next() < 0.3) put(b, .bush, x + jit(b, 2), z + jit(b, 2), b.rng.range(0, 6), b.rng.range(0.8, 1.3));
        }
    }
}

fn shadeProps(b: *Builder) void {
    for (b.placed.items) |pl| {
        const info = api.props.info(pl.kind);
        const ext = @max(info.max[0] - info.min[0], info.max[2] - info.min[2]) * pl.scale;

        if (@abs(pl.pos.y - t.height(pl.pos.x, pl.pos.z)) > 2.5) continue;

        switch (info.group) {
            .tree => splat(pl.pos.x, pl.pos.z, @max(ext * 0.6, 3), 0.5),
            .building => splat(pl.pos.x, pl.pos.z, std.math.clamp(ext * 0.7, 2, 12), 0.5),
            .rock => splat(pl.pos.x, pl.pos.z, std.math.clamp(ext * 0.7, 1, 8), 0.35),
            .street => if (ext > 1.5) splat(pl.pos.x, pl.pos.z, std.math.clamp(ext * 0.6, 1, 4), 0.3),
            else => {},
        }
    }
}

fn build(b: *Builder) void {
    claim_n = 0;
    @memset(&shade_grid, 0);

    bowl(b);
    pitchLines(b);
    matchDay(b);
    concourse(b);
    fanPlaza(b);
    treeLine(b);
    shadeProps(b);
}

fn setSpots(gpa: std.mem.Allocator) void {
    wd.autoSpots(gpa, .{ .loot = 30, .vehicles = 4, .seed = 331 });
}
