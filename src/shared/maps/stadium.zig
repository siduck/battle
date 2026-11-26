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
    .note = "Stands, pitch, training grounds",
    .tint = .{ 90, 160, 90 },
    .ready = true,
    .half = 262,
    .play = 210,
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
    .tufts = 0.15,
};

const cell: f32 = 2;
const grid_n = 280;
const grid_half: f32 = 280;

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

fn segDist(px: f32, pz: f32, s: [4]f32) f32 {
    const dx = s[2] - s[0];
    const dz = s[3] - s[1];
    const l2 = dx * dx + dz * dz;
    const u = std.math.clamp(((px - s[0]) * dx + (pz - s[1]) * dz) / l2, 0, 1);
    const qx = s[0] + dx * u - px;
    const qz = s[1] + dz * u - pz;

    return @sqrt(qx * qx + qz * qz);
}

const pitch_x: f32 = 52.5;
const pitch_z: f32 = 34;
const track_in: f32 = 38;
const track_out: f32 = 47;
const stand_front: f32 = 49;
const stand_depth: f32 = 10.5;
const stand_x: f32 = 60;
const end_front: f32 = 88;

fn ovalDist(x: f32, z: f32) f32 {
    const dx = @max(@abs(x) - 46, 0);

    return @sqrt(dx * dx + z * z);
}

const paths = [_][4]f32{
    .{ 0, 60, 0, 190 },
    .{ -200, 76, 200, 76 },
    .{ -76, -60, -76, 190 },
    .{ 76, -60, 76, 190 },
    .{ -200, -66, 200, -66 },
    .{ 0, -66, 0, -200 },
    .{ -150, -66, -150, 76 },
    .{ 150, -66, 150, 76 },
};

fn trailDist(x: f32, z: f32) f32 {
    var best: f32 = 1000;

    for (paths) |s| best = @min(best, segDist(x, z, s));

    return best;
}

fn dry(x: f32, z: f32, pad: f32) bool {
    _ = x;
    _ = z;
    _ = pad;

    return true;
}

fn inBox(x: f32, z: f32, x0: f32, z0: f32, x1: f32, z1: f32) bool {
    return x > x0 and x < x1 and z > z0 and z < z1;
}

fn rimEdge(x: f32, z: f32) f32 {
    return @max(@abs(x), @abs(z)) + (t.fbm(x * 0.02 + 5, z * 0.02 - 3) - 0.45) * 24;
}

fn height(x: f32, z: f32) f32 {
    const n1 = t.fbm(x * 0.014 + 3, z * 0.014 - 7);
    const n2 = t.fbm(x * 0.06, z * 0.06);
    const core = 1 - t.smooth(150, 190, @max(@abs(x), @abs(z)));
    var h = ((n1 - 0.4) * 7 + (n2 - 0.45) * 1.2) * (1 - core) + 0.2;

    h = @max(h, 0.1);

    const e = rimEdge(x, z);
    const m = t.smooth(def.play - 14, def.half - 6, e);
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

const islands = [_][2]f32{ .{ 30, -116 }, .{ 92, -116 }, .{ 30, -138 }, .{ 92, -138 }, .{ -30, -116 }, .{ -92, -116 }, .{ -30, -138 }, .{ -92, -138 } };

fn fanLane(x: f32) bool {
    return @abs(x) < 7 or @abs(@abs(x) - 61) < 3.6;
}

fn walkBand(z: f32) bool {
    return @abs(z + 106) < 2.6 or @abs(z + 127) < 2.6;
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

        if (!walkBand(z) and (@abs(@abs(x) - 6.8) < 0.2 or @abs(@abs(@abs(x) - 61) - 3.4) < 0.2)) c = .{ 190, 186, 176 };
    } else if (joint) {
        c = mix3(c, .{ 110, 106, 100 }, 0.6);
    }

    if (walkBand(z) and !fanLane(x) and (@abs(@abs(z + 106) - 2.4) < 0.2 or @abs(@abs(z + 127) - 2.4) < 0.2)) c = .{ 190, 186, 176 };

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

    const od = ovalDist(x, z);

    if (@abs(x) < pitch_x + 3 and @abs(z) < pitch_z + 3) {
        c = turf(x, z, 5.25);
    } else if (od < track_out and od > track_in - 0.5) {
        c = mix3(.{ 176, 82, 60 }, .{ 164, 74, 56 }, t.fbm(x * 0.3, z * 0.3));
    } else if (od < track_in) {
        c = mix3(.{ 92, 146, 56 }, .{ 102, 154, 60 }, t.fbm(x * 0.2, z * 0.2));
    } else if (@abs(x) < 101 and z > -80 and z < 110) {
        const tile = @mod(@floor(x / 4) + @floor(z / 4), 2);

        c = if (tile < 1) .{ 168, 166, 158 } else .{ 156, 154, 148 };
    }

    if (inBox(x, z, -130, -150, 130, -82)) c = plaza(x, z);

    if (inBox(x, z, 104, -58, 196, 52)) {
        const od2 = @sqrt(@max(@abs(x - 150) - 26, 0) * @max(@abs(x - 150) - 26, 0) + (z + 3) * (z + 3));

        if (od2 < 26 and od2 > 20) c = mix3(.{ 176, 84, 62 }, .{ 164, 76, 58 }, t.fbm(x * 0.3, z * 0.3));
        if (od2 <= 20) c = turf(x - 150, z, 4);
    }

    for ([_][2]f32{ .{ 110, 110 }, .{ 160, 110 } }) |p| {
        if (inBox(x, z, p[0] - 19, p[1] - 29, p[0] + 19, p[1] + 29)) c = turf(z - p[1] + 100, x, 4);
    }

    const pd = trailDist(x, z);

    if (!inBox(x, z, -130, -150, 130, -84)) c = mix3(c, .{ 132, 132, 134 }, 1 - t.smooth(3, 4.5, pd));

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

fn sink(b: *Builder, e: K, x: f32, z: f32, yaw: f32, s: f32, d: f32) void {
    b.putAt(kit.of(e), vec(x, t.height(x, z) - d, z), yaw, s);
}

fn jit(b: *Builder, a: f32) f32 {
    return b.rng.range(-a, a);
}

fn row(b: *Builder, e: K, x0: f32, z0: f32, x1: f32, z1: f32, step: f32, s: f32) void {
    const dx = x1 - x0;
    const dz = z1 - z0;
    const len = @sqrt(dx * dx + dz * dz);
    const n: usize = @intFromFloat(@max(1, @round(len / step)));
    const yaw = std.math.atan2(dx, dz) + hp;
    var i: usize = 0;

    while (i <= n) : (i += 1) {
        const u = @as(f32, @floatFromInt(i)) / @as(f32, @floatFromInt(n));

        put(b, e, x0 + dx * u, z0 + dz * u, yaw, s);
    }
}

fn scatterIn(b: *Builder, kinds: []const K, n: usize, cx: f32, cz: f32, r: f32, smin: f32, smax: f32) void {
    var i: usize = 0;
    var tries: usize = 0;

    while (i < n and tries < n * 12) : (tries += 1) {
        const a = b.rng.range(0, std.math.tau);
        const d = r * @sqrt(b.rng.next());
        const x = cx + @cos(a) * d;
        const z = cz + @sin(a) * d;

        if (!open(x, z, 0.8) or trailDist(x, z) < 2.5 or !dry(x, z, 1)) continue;

        put(b, kinds[i % kinds.len], x, z, b.rng.range(0, std.math.tau), b.rng.range(smin, smax));
        i += 1;
    }
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
    line(b, -pitch_x, -pitch_z, pitch_x, -pitch_z);
    line(b, -pitch_x, pitch_z, pitch_x, pitch_z);
    line(b, -pitch_x, -pitch_z, -pitch_x, pitch_z);
    line(b, pitch_x, -pitch_z, pitch_x, pitch_z);
    line(b, 0, -pitch_z, 0, pitch_z);
    ring(b, 0, 0, 9.15, 0, std.math.tau);
    line(b, -0.2, -0.2, 0.2, 0.2);

    for ([_]f32{ -1, 1 }) |s| {
        const gx = s * pitch_x;
        const bx = gx - s * 16.5;
        const sx = gx - s * 5.5;

        line(b, bx, -20.15, bx, 20.15);
        line(b, gx, -20.15, bx, -20.15);
        line(b, gx, 20.15, bx, 20.15);
        line(b, sx, -9.16, sx, 9.16);
        line(b, gx, -9.16, sx, -9.16);
        line(b, gx, 9.16, sx, 9.16);
        line(b, gx - s * 11 - 0.15, -0.15, gx - s * 11 + 0.15, 0.15);

        if (s > 0) ring(b, gx - 11, 0, 9.15, std.math.pi - 0.927, std.math.pi + 0.927) else ring(b, gx + 11, 0, 9.15, -0.927, 0.927);
        b.putAt(kit.of(.goal), vec(gx + s * 1, t.height(gx, 0), 0), -s * hp, 1);
    }

    for ([_][2]f32{ .{ -1, -1 }, .{ -1, 1 }, .{ 1, -1 }, .{ 1, 1 } }) |c| put(b, .cornerflag, c[0] * pitch_x, c[1] * pitch_z, 0, 1);

    var lane: f32 = track_in + 1.5;

    while (lane < track_out) : (lane += 1.5) {
        line(b, -46, -lane, 46, -lane);
        line(b, -46, lane, 46, lane);

        if (lane < track_in + 2 or lane > track_out - 2) {
            ring(b, 46, 0, lane, -hp, hp);
            ring(b, -46, 0, lane, hp, 3 * hp);
        }
    }
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

fn bowl(b: *Builder) void {
    standRow(b, -stand_x, -6, -stand_front, -1, true);
    standRow(b, 6, stand_x, -stand_front, -1, true);
    standRow(b, -stand_x, stand_x, stand_front, 1, false);
    terraceRow(b, end_front, 1, -30, 30);
    terraceRow(b, -end_front, -1, -30, 30);
    house(b, .tunnel, 0, -stand_front - 2, 0);
    house(b, .pressbox, 0, -stand_front - stand_depth - 4, std.math.pi);

    for ([_][2]f32{ .{ -78, -62 }, .{ 78, -62 }, .{ -78, 62 }, .{ 78, 62 } }) |p| {
        put(b, .flood, p[0], p[1], std.math.atan2(-p[0], -p[1]), 1);
        claim(p[0], p[1], 3);
    }

    boardsX(b, -48, 48, -pitch_z - 3, 0, 1, &.{ -27, 0, 27 }, 0);
    boardsX(b, -48, 48, pitch_z + 3, std.math.pi, 1, &.{ -27, 27 }, 1);
    boardsZ(b, -30, 30, -pitch_x - 4, hp, 1, &.{ -15, 15 }, 2);
    boardsZ(b, -30, 30, pitch_x + 4, -hp, 1, &.{ -15, 15 }, 0);

    put(b, .dugout, -12, pitch_z + 6.5, std.math.pi, 1);
    put(b, .dugout, 12, pitch_z + 6.5, std.math.pi, 1);
    put(b, .bench, -20, pitch_z + 6, std.math.pi, 1);
    put(b, .bench, 20, pitch_z + 6, std.math.pi, 1);
    put(b, .scoreboard, end_front - 4, 36, -hp - 0.4, 1);
    put(b, .scoreboard, -end_front + 4, -36, hp - 0.4, 1);

    for ([_][3]f32{ .{ -36, pitch_z + 6.2, 0 }, .{ 36, pitch_z + 6.2, 0 }, .{ -30, -pitch_z - 6.2, 0 }, .{ 30, -pitch_z - 6.2, 0 } }) |p| {
        put(b, .crate, p[0], p[1], p[2], 1);
        put(b, .crate, p[0] + 0.8, p[1] + 0.1, 0.3, 1);
        put(b, .kitbag, p[0] - 1.2, p[1], 1.2, 1);
    }
}

fn facade(b: *Builder, x: f32, z: f32, yaw: f32, gate: bool) void {
    const y = t.height(x, z) - 0.1;

    b.putAt(kit.of(if (gate) .sback_gate else .sback_wall), vec(x, y, z), yaw, 1);
}

fn standBacks(b: *Builder) void {
    const zb = stand_front + stand_depth + 0.75;
    var i: usize = 0;
    var x: f32 = -57;

    while (x < 58) : (x += 6) {
        const gate = i % 3 == 1;

        facade(b, x, zb, 0, gate);

        if (@abs(x) > 8) facade(b, x, -zb, std.math.pi, gate);

        i += 1;
    }

    var z: f32 = -27;

    i = 0;

    while (z < 28) : (z += 6) {
        facade(b, end_front + 10.1, z, hp, i % 4 == 1);
        facade(b, -end_front - 10.1, z, -hp, i % 4 == 2);
        i += 1;
    }

    const front = zb + 0.6;

    for ([_]f32{ -1, 1 }) |s| {
        const yaw: f32 = if (s > 0) 0 else std.math.pi;
        const z0 = s * front;

        for ([_]f32{ -45, -15, 15, 45 }) |kx| {
            house(b, .kiosk, kx, z0 + s * 2.2, yaw);
            put(b, .bin, kx + 3, z0 + s * 1.2, 0, 1);
            put(b, .pallet, kx - 3, z0 + s * 0.8, 0.2, 1);
            put(b, .crate, kx - 3.2, z0 + s * 2.0, 0.5, 1);
        }

        for ([_]f32{ -54, -30, 30, 54 }) |px| {
            put(b, .planter, px - 1.6, z0 + s * 1.2, 0, 1.3);
            put(b, .planter, px + 1.6, z0 + s * 1.2, 0, 1.3);
            put(b, .banner, px, z0 + s * 1.0, 0, 1);
        }
    }

    for ([_]f32{ -1, 1 }) |s| {
        var q: f32 = -24;

        while (q < 26) : (q += 16) {
            put(b, .bin, s * 99.6, q + 3, 0, 1);
            put(b, .planter, s * 99.8, q - 2, 0, 1.2);
        }
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
    spots(b, &pitch_cover, 0, 0, true);
    put(b, .inflatable, 0, -pitch_z - 0.5, 0, 1);
    put(b, .medtent, -6, 0, 0.3, 1);
    put(b, .medtent, 6, 0, 0.3 + std.math.pi, 1);
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
    const zg: f32 = 104;

    house(b, .gate, 0, zg, 0);

    for ([_]f32{ -24, -14, 14, 24 }) |x| house(b, .turnstile, x, zg, 0);

    for ([_]f32{ -40, 40 }) |x| house(b, .booth, x, zg - 2, 0);

    var x: f32 = -96;

    while (x < 96) : (x += 2.4) {
        if (@abs(x) < 34 or @abs(x - 76) < 5 or @abs(x + 76) < 5) continue;

        put(b, .wall, x, zg, 0, 1);
    }

    for ([_]f32{ -1, 1 }) |s| {
        barrierLine(b, .rail, s * 9, 92, s * 9, 100, 2, 1);
        barrierLine(b, .rail, s * 19, 90, s * 19, 100, 2, 1);
        barrierLine(b, .rail, s * 29, 92, s * 29, 100, 2, 1);
        put(b, .banner, s * 34, 100, 0, 1);
        put(b, .banner, s * 4.5, 100, 0, 1);

        picnicSet(b, s * 30, 75, 0.3);
        picnicSet(b, s * 36, 78, 1.1);
        picnicSet(b, s * 24, 79, 2.0);
        picnicSet(b, s * 60, 76, 0.6);
        picnicSet(b, s * 66, 80, 2.4);
        put(b, .oak, s * 12, 76, s, 1.2);
        put(b, .planter, s * 10, 74, 0, 1.3);
        put(b, .planter, s * 14, 74, 0, 1.3);
        put(b, .planter, s * 10, 78, 0, 1.3);
        put(b, .planter, s * 14, 78, 0, 1.3);
        claim(s * 12, 76, 3);
        house(b, .snackbox, s * 48, 88, if (s > 0) std.math.pi else 0);
        put(b, .crate, s * 44.5, 85.6, 0.2, 1);
        put(b, .pallet, s * 52, 86, 0.4, 1);
        stallRow(b, if (s > 0) 70 else -88, 88, 5, std.math.pi);
        loos(b, s * 92, 82, if (s > 0) hp else -hp);
        put(b, .flood, s * 82, 98, 0, 0.8);
        put(b, .bin, s * 80, 94, 0, 1);
        put(b, .ad_red, s * 72, 68, 0.15 * s, 1.6);
        put(b, .ad_gold, s * 86, 72, hp + 0.2 * s, 1.6);
    }

    for ([_]f32{ -1, 1 }) |s| {
        const zs: f32 = -stand_front - stand_depth - 3.2;

        put(b, .ad_navy, s * 22, zs - 9, 0, 1.6);
        put(b, .ad_gold, s * 64, zs - 6, 0, 1.6);
        picnicSet(b, s * 34, zs - 9, 0.6);
        picnicSet(b, s * 76, zs - 8, 1.6);
        house(b, .snackbox, s * 88, zs - 3, if (s > 0) -hp else hp);
        put(b, .stall, s * 12, zs - 13, 0, 1.35);
        put(b, .stall, s * 16.6, zs - 13, 0, 1.35);
        put(b, .pallet, s * 9.5, zs - 12, 0.2, 1);
        barrierLine(b, .waterbar, s * 40, zs - 14, s * 56, zs - 14, 4, 1);
        put(b, .bin, s * 30, zs - 2, 0, 1);
        put(b, .banner, s * 50, zs - 1.5, 0, 1);
    }

    for ([_][4]f32{ .{ -102, -80, -102, 104 }, .{ 102, -80, 102, 104 } }) |s| {
        var z = s[1];

        while (z < s[3]) : (z += 2.4) {
            if (@abs(z - 76) < 6 or @abs(z + 66) < 6 or @abs(z) < 5) continue;

            put(b, .mesh, s[0], z, hp, 1);
        }
    }
}

fn cluster(b: *Builder, x: f32, z: f32, pick: usize, yaw: f32, i: usize) void {
    const cx = @cos(yaw);
    const sz = -@sin(yaw);

    switch (pick % 9) {
        0 => {
            picnicSet(b, x, z, yaw);
            picnicSet(b, x + cx * 3.6, z + sz * 3.6, yaw + 0.5);
        },
        1 => {
            put(b, .stall, x, z, yaw, 1.35);
            put(b, .stall, x + cx * 4.4, z + sz * 4.4, yaw, 1.35);
            put(b, .pallet, x - cx * 2.6, z - sz * 2.6 + 1, yaw, 1);
            put(b, .crate, x + cx * 6.6, z + sz * 6.6, 0.3, 1);
        },
        2 => {
            put(b, ad(i), x, z, yaw, 1.8);
            put(b, .bin, x + sz * 1.6, z - cx * 1.6, 0, 1);
            put(b, .planter, x + cx * 6 + sz * 1.2, z + sz * 6 - cx * 1.2, 0, 1.3);
        },
        3 => {
            put(b, .waterbar, x, z, yaw, 1);
            put(b, .waterbar, x + cx * 3.6 + sz * 1.4, z + sz * 3.6 - cx * 1.4, yaw + 0.6, 1);
            put(b, .crate, x - cx * 2.6, z - sz * 2.6, 0.2, 1);
            put(b, .crate, x - cx * 2.0, z - sz * 2.0 + 0.6, 0.9, 1);
        },
        4 => {
            put(b, .ptoilet, x, z, yaw, 1);
            put(b, .ptoilet, x + cx * 1.4, z + sz * 1.4, yaw, 1);
            put(b, .ptoilet, x + cx * 2.8, z + sz * 2.8, yaw, 1);
            put(b, .generator, x + cx * 5.4, z + sz * 5.4, yaw + hp, 1);
        },
        5 => {
            put(b, .tarp, x, z, yaw, 1);
            put(b, .tarp, x + sz * 2.4, z - cx * 2.4, yaw, 1);
            put(b, .pallet, x + cx * 2.6, z + sz * 2.6, yaw, 1);
            put(b, .pallet, x + cx * 3.7, z + sz * 3.7, yaw + 0.2, 1);
            put(b, .pallet, x + cx * 3.1, z + sz * 3.1 - 1.1, yaw, 1);
        },
        6 => {
            put(b, .oak, x, z, yaw, b.rng.range(0.9, 1.2));
            put(b, .planter, x + 1.8, z + 1.2, 0, 1.3);
            put(b, .planter, x - 1.8, z + 1.2, 0, 1.3);
            put(b, .planter, x, z - 1.9, 0, 1.3);
            put(b, .banner, x + cx * 3.5, z + sz * 3.5, yaw, 1);
        },
        7 => {
            put(b, .jersey, x, z, yaw, 1.3);
            put(b, .jersey, x + cx * 2.7, z + sz * 2.7, yaw, 1.3);
            put(b, .jersey, x + cx * 5.4, z + sz * 5.4, yaw, 1.3);
            put(b, .kitbag, x + sz * 1.2, z - cx * 1.2, 0.4, 1);
        },
        else => {
            put(b, .medtent, x, z, yaw, 1);
            put(b, .rack, x + cx * 3.6, z + sz * 3.6, yaw, 1);
            put(b, .crate, x - cx * 3, z - sz * 3, 0.1, 1);
        },
    }

    claim(x, z, 3.6);
}

fn plazaFill(b: *Builder) void {
    var i: usize = 0;

    while (i < 320) : (i += 1) {
        const x = b.rng.range(-98, 98);
        const z = b.rng.range(-78, 108);

        if (@abs(x) < stand_x + 4 and @abs(z) < stand_front + stand_depth + 7) continue;

        if (@abs(x) < end_front + 13 and @abs(z) < 34) continue;

        if (trailDist(x, z) < 4 or !open(x, z, 4)) continue;

        cluster(b, x, z, @intFromFloat(b.rng.range(0, 9)), b.rng.range(0, 6), i);
    }
}

fn grid(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32, step: f32, seed: usize) void {
    var z = z0;
    var i: usize = seed;

    while (z <= z1) : (z += step) {
        var x = x0;

        while (x <= x1) : (x += step) {
            const px = x + jit(b, step * 0.25);
            const pz = z + jit(b, step * 0.25);

            i += 1;

            if (inBox(px, pz, -130, -150, 130, -82) and (fanLane(px) or fanLane(px + 3) or fanLane(px - 3) or walkBand(pz) or walkBand(pz + 3) or walkBand(pz - 3) or island(px, pz, 3))) continue;

            if ((!inBox(px, pz, -130, -150, 130, -82) and trailDist(px, pz) < 4) or !open(px, pz, 3)) continue;

            const yaw = @round(b.rng.range(0, 4)) * hp + jit(b, 0.25);

            cluster(b, px, pz, i * 7 + @as(usize, @intFromFloat(b.rng.range(0, 3))), yaw, i);
        }
    }
}

fn clubSide(b: *Builder) void {
    house(b, .clubhouse, -128, 112, 0);
    house(b, .firstaid, -104, 128, -hp);
    house(b, .toilets, -150, 132, std.math.pi);
    house(b, .pressbox, -164, 102, hp);
    house(b, .toilets, -40, -94, 0);
    house(b, .firstaid, 52, -92, 0);
    house(b, .store, -112, 98, hp);
    put(b, .medtent, -108, 88, 0.1, 1);
    put(b, .flagpole, -128, 98, 0, 1);
    put(b, .flagpole, -122, 98, 0, 1);
    put(b, .flagpole, -134, 98, 0, 1);
    picnicSet(b, -140, 98, 0.3);
    picnicSet(b, -146, 104, 1.4);
    put(b, .shelter, -150, 116, 0.2, 1);
    claim(-150, 116, 5);
    barrierLine(b, .fence, -172, 90, -172, 140, 4, 1);
    barrierLine(b, .fence, -172, 140, -100, 140, 4, 1);
    scatterIn(b, &.{ .kitbag, .bin, .crate, .pallet, .planter, .rack, .sled }, 22, -130, 116, 26, 0.9, 1.1);
}

fn training(b: *Builder) void {
    for ([_][2]f32{ .{ 110, 110 }, .{ 160, 110 } }) |p| {
        put(b, .tgoal, p[0], p[1] - 27, 0, 1);
        put(b, .tgoal, p[0], p[1] + 27, std.math.pi, 1);
        line(b, p[0] - 18, p[1] - 28, p[0] + 18, p[1] - 28);
        line(b, p[0] - 18, p[1] + 28, p[0] + 18, p[1] + 28);
        line(b, p[0] - 18, p[1] - 28, p[0] - 18, p[1] + 28);
        line(b, p[0] + 18, p[1] - 28, p[0] + 18, p[1] + 28);
        line(b, p[0] - 18, p[1], p[0] + 18, p[1]);
        ring(b, p[0], p[1], 6, 0, std.math.tau);

        const drill = [_]Spot{
            .{ .e = .sled, .x = -6, .z = 14, .yaw = 0.2 },
            .{ .e = .sled, .x = 7, .z = -12, .yaw = 3.0 },
            .{ .e = .dummy, .x = -4, .z = -16, .yaw = 0 },
            .{ .e = .dummy, .x = 1, .z = -15, .yaw = 0 },
            .{ .e = .dummy, .x = 6, .z = -16.5, .yaw = 0 },
            .{ .e = .dummy, .x = -10, .z = 4, .yaw = 0 },
            .{ .e = .dummy, .x = -9, .z = 7, .yaw = 0 },
            .{ .e = .rack, .x = 12, .z = 14, .yaw = 0.4 },
            .{ .e = .tactics, .x = -14, .z = 2, .yaw = hp },
            .{ .e = .bench, .x = -19.5, .z = -6, .yaw = hp },
            .{ .e = .bench, .x = -19.5, .z = 6, .yaw = hp },
            .{ .e = .tarp, .x = 10, .z = 2, .yaw = 0.2 },
            .{ .e = .tarp, .x = 10.6, .z = 4.4, .yaw = 0.2 },
            .{ .e = .ad_navy, .x = 0, .z = 22, .yaw = 0, .s = 1.1 },
            .{ .e = .ad_red, .x = -12, .z = -22, .yaw = 0.4, .s = 1.1 },
            .{ .e = .crate, .x = 13, .z = 16, .yaw = 0.3 },
            .{ .e = .kitbag, .x = -18, .z = 0, .yaw = 0.1 },
            .{ .e = .cones, .x = 4, .z = 8, .yaw = 0.7 },
            .{ .e = .cones, .x = -3, .z = -6, .yaw = 2.2 },
        };

        spots(b, &drill, p[0], p[1], false);
    }

    var x: f32 = 88;

    while (x < 184) : (x += 2.4) {
        if (@abs(x - 135) < 5) continue;

        put(b, .mesh, x, 80, 0, 1);
        put(b, .mesh, x, 141, 0, 1);
    }

    var z: f32 = 80;

    while (z < 141) : (z += 2.4) {
        if (@abs(z - 110) < 5) continue;

        put(b, .mesh, 87, z, hp, 1);
        put(b, .mesh, 184, z, hp, 1);
    }

    house(b, .booth, 135, 76, 0);
    house(b, .store, 135, 126, std.math.pi);
    house(b, .store, 135, 94, 0);
    put(b, .scaffold, 135, 110, 0, 1);
    put(b, .rack, 133, 102, hp, 1);
    put(b, .pallet, 137, 118, 0.3, 1);
    put(b, .pallet, 138.2, 118.4, 0.1, 1);
    put(b, .tarp, 132, 116, 1.6, 1);
    loos(b, 176, 72, 0);
    put(b, .medtent, 100, 72, 0.2, 1);
    put(b, .ptoilet, 94, 72, 0, 1);
}

fn athletics(b: *Builder) void {
    put(b, .discus, 186, 30, 0, 1);
    api.box(b, 181.4, 0, 25, 182.4, 6, 35);
    api.box(b, 189.6, 0, 25, 190.6, 6, 35);
    api.box(b, 182, 0, 34, 190, 6, 35);
    put(b, .highjump, 150, -3, 0, 1);
    put(b, .highjump, 136, 6, 0.4, 1);

    for ([_]f32{ -27.5, -24.5 }) |zz| {
        var x: f32 = 128;

        while (x < 182) : (x += 9) put(b, .hurdle, x, zz, hp, 1);
    }

    for ([_]f32{ 18.5, 21.5 }) |zz| {
        var x: f32 = 132;

        while (x < 180) : (x += 9) put(b, .hurdle, x, zz, hp, 1);
    }

    const kit_spots = [_]Spot{
        .{ .e = .ad_navy, .x = 134, .z = 10, .yaw = 0.3, .s = 1.1 },
        .{ .e = .ad_gold, .x = 166, .z = -16, .yaw = -0.3, .s = 1.1 },
        .{ .e = .waterbar, .x = 158, .z = 12, .yaw = 0 },
        .{ .e = .waterbar, .x = 162, .z = 12, .yaw = 0 },
        .{ .e = .waterbar, .x = 140, .z = -18, .yaw = 0 },
        .{ .e = .tarp, .x = 148, .z = 4, .yaw = 1.5 },
        .{ .e = .tarp, .x = 150.4, .z = 4.2, .yaw = 1.5 },
        .{ .e = .rack, .x = 136, .z = -4, .yaw = 0.6 },
        .{ .e = .sled, .x = 156, .z = -12, .yaw = 0.2 },
        .{ .e = .pallet, .x = 168, .z = 10, .yaw = 0 },
        .{ .e = .pallet, .x = 169.1, .z = 10.2, .yaw = 0.3 },
        .{ .e = .crate, .x = 146, .z = -9, .yaw = 0.3 },
        .{ .e = .kitbag, .x = 147, .z = -10, .yaw = 1.1 },
        .{ .e = .medtent, .x = 142, .z = 9, .yaw = 0.4 },
        .{ .e = .rack, .x = 158, .z = -7, .yaw = 1.1 },
        .{ .e = .dummy, .x = 166, .z = 3, .yaw = 0 },
        .{ .e = .dummy, .x = 167.5, .z = 5.5, .yaw = 0 },
        .{ .e = .dummy, .x = 165, .z = 7, .yaw = 0 },
        .{ .e = .waterbar, .x = 134, .z = -9, .yaw = 0.5 },
        .{ .e = .sled, .x = 144, .z = -14, .yaw = 2.6 },
        .{ .e = .crate, .x = 141, .z = 6.6, .yaw = 0.3 },
        .{ .e = .pallet, .x = 159.5, .z = -4.6, .yaw = 0.3 },
        .{ .e = .medtent, .x = 112, .z = -12, .yaw = hp },
        .{ .e = .medtent, .x = 188, .z = 8, .yaw = -hp },
        .{ .e = .tarp, .x = 160, .z = 6, .yaw = 0.3 },
        .{ .e = .tarp, .x = 161, .z = 8.4, .yaw = 0.3 },
        .{ .e = .tarp, .x = 140, .z = -12, .yaw = 1.2 },
        .{ .e = .ad_gold, .x = 150, .z = 14, .yaw = 0, .s = 1.3 },
        .{ .e = .ad_navy, .x = 150, .z = -20, .yaw = 0, .s = 1.3 },
        .{ .e = .ad_red, .x = 128, .z = 2, .yaw = hp, .s = 1.3 },
        .{ .e = .ad_red, .x = 172, .z = -8, .yaw = hp, .s = 1.3 },
        .{ .e = .scaffold, .x = 176, .z = 12, .yaw = 0 },
        .{ .e = .scaffold, .x = 124, .z = -18, .yaw = 0 },
        .{ .e = .rack, .x = 116, .z = 10, .yaw = 0.2 },
        .{ .e = .sled, .x = 166, .z = -16, .yaw = 0.4 },
        .{ .e = .shelter, .x = 116, .z = 44, .yaw = 0 },
        .{ .e = .shelter, .x = 184, .z = -50, .yaw = 0.4 },
        .{ .e = .waterbar, .x = 150, .z = -44, .yaw = 0 },
        .{ .e = .waterbar, .x = 146, .z = -44, .yaw = 0 },
        .{ .e = .jersey, .x = 132, .z = -46, .yaw = 0.3, .s = 1.2 },
        .{ .e = .pallet, .x = 113, .z = 12, .yaw = 0 },
        .{ .e = .crate, .x = 117, .z = 13, .yaw = 0.5 },
        .{ .e = .kitbag, .x = 158, .z = 4, .yaw = 0.2 },
        .{ .e = .planter, .x = 172, .z = -40, .yaw = 0, .s = 1.3 },
    };

    spots(b, &kit_spots, 0, 0, false);
    standRow(b, 132, 168, 29.5, 1, true);

    var x: f32 = 132;
    var i: usize = 0;

    while (x < 168) : (x += 6) {
        facade(b, x + 3, 29.5 + stand_depth + 0.75, 0, i % 3 == 1);
        i += 1;
    }

    boardsX(b, 126, 174, 27, std.math.pi, 1, &.{150}, 0);
    boardsX(b, 126, 174, -33, 0, 1, &.{ 138, 162 }, 1);

    for ([_][2]f32{ .{ 116, -42 }, .{ 184, -42 }, .{ 118, 40 }, .{ 180, 44 } }) |p| put(b, .flood, p[0], p[1], std.math.atan2(150 - p[0], -3 - p[1]), 0.7);

    house(b, .clubhouse, 150, -80, 0);
    house(b, .toilets, 176, 60, std.math.pi);
    grid(b, 110, -58, 192, -36, 12, 11);
    grid(b, 104, 46, 124, 66, 11, 17);
    house(b, .store, 120, 60, 0);
    house(b, .store, 106, -40, hp);
}

fn fanZone(b: *Builder) void {
    defer grid(b, -124, -147, 124, -86, 6.5, 3);

    const deck_y = t.height(0, -136) + 0.9;

    b.mass(vec(-9, deck_y - 2, -142), vec(9, deck_y, -132), .concrete);
    b.solid(.{ .ramp = .{ .min = vec(-4, deck_y - 2, -132), .max = vec(4, deck_y, -128), .rise = .neg_z } });
    b.deco(vec(-4, deck_y - 2, -132), vec(4, deck_y - 0.4, -128), .concrete);
    b.putAt(kit.of(.ad_navy), vec(0, deck_y + 3.2, -141.6), 0, 2.6);
    b.putAt(kit.of(.scaffold), vec(-10.5, deck_y - 0.9, -140), 0, 1);
    b.putAt(kit.of(.scaffold), vec(10.5, deck_y - 0.9, -140), 0, 1);
    put(b, .generator, -13, -134, hp, 1);
    put(b, .pallet, 12.5, -133, 0.2, 1);
    claim(0, -136, 14);

    for (islands) |q| {
        put(b, .oak, q[0], q[1], q[0] * 0.1, 1.2);
        put(b, .bush, q[0] - 3.6, q[1] + 0.8, 0.3, 0.9);
        put(b, .bush, q[0] + 3.8, q[1] - 0.6, 1.3, 0.8);
        put(b, .banner, q[0] + 5.2, q[1] + 2.4, 0, 1);
        put(b, .bin, q[0] - 6.6, q[1] - 2.2, 0, 1);
        claim(q[0], q[1], 6);
    }

    for ([_]f32{ -1, 1 }) |s| {
        const off: f32 = if (s < 0) 4.6 * 4 else 0;

        stallRow(b, s * 20 - off, -96, 5, std.math.pi);
        stallRow(b, s * 70 - off, -96, 5, std.math.pi);
        stallRow(b, s * 22 - off, -132.5, 5, 0);
        house(b, .snackbox, s * 48, -94, std.math.pi);
        house(b, .snackbox, s * 104, -100, if (s > 0) -hp else hp);
        house(b, .snackbox, s * 104, -120, if (s > 0) -hp else hp);
        house(b, .snackbox, s * 46, -142, 0);

        for ([_][2]f32{ .{ 14, -114 }, .{ 42, -114 }, .{ 70, -112 }, .{ 82, -118 }, .{ 110, -112 }, .{ 74, -142 } }) |p| picnicSet(b, s * p[0], p[1], b.rng.range(0, 6));

        put(b, .shelter, s * 50, -116, 0.1 * s, 1);
        claim(s * 50, -116, 5);
        put(b, .picnic, s * 49, -115, 0.1, 1.1);
        put(b, .picnic, s * 51.5, -118, 0.1, 1.1);
        loos(b, s * 112 - 3, -140, 0);
        put(b, .ad_red, s * 18, -118, hp, 2);
        put(b, .ad_gold, s * 76, -121, 0, 2);
        put(b, .ad_navy, s * 104, -134, hp, 2);
        put(b, .ad_red, s * 28, -146, 0, 2);
        put(b, .ad_gold, s * 122, -112, hp, 2);
        barrierLine(b, .waterbar, s * 8, -86, s * 8, -102, 4, 1);
        barrierLine(b, .jersey, s * 66, -137, s * 84, -137, 2.4, 1.2);
        barrierLine(b, .jersey, s * 100, -86, s * 126, -86, 2.4, 1.2);
        barrierLine(b, .fence, s * 130, -82, s * 130, -150, 4, 1);
        barrierLine(b, .fence, s * 12, -150, s * 130, -150, 4, 1);
        put(b, .flood, s * 52, -147, if (s > 0) 0.6 else -0.6, 0.9);
        put(b, .scaffold, s * 40, -138, 0, 1);
        put(b, .tarp, s * 70, -132, 0.4, 1);
        put(b, .tarp, s * 71, -134.4, 0.4, 1);
        put(b, .pallet, s * 75, -133, 0.1, 1);
        put(b, .pallet, s * 76.1, -133.2, 0.3, 1);
        put(b, .crate, s * 74.4, -134.2, 0.3, 1);
        put(b, .generator, s * 50, -100, 0, 1);

        for ([_]f32{ -103.1, -108.9, -124.1, -129.9 }) |rz| {
            var x0: f32 = 9;

            while (x0 < 124) : (x0 += 14) {
                const x1 = @min(x0 + 9, 126);

                if (x1 > 56.6 and x0 < 65.4) continue;

                barrierLine(b, .rail, s * x0, rz, s * x1, rz, 2, 1);
            }
        }

        for ([_]f32{ 56.9, 65.1 }) |lx| {
            for ([_][2]f32{ .{ -100, -88 }, .{ -121, -112 }, .{ -146, -133 } }) |seg| barrierLine(b, .rail, s * lx, seg[0], s * lx, seg[1], 2, 1);
        }

        for ([_]f32{ -90, -116, -140 }) |bz| put(b, .banner, s * 7.6, bz, 0, 1);
    }

}

fn park(b: *Builder) void {
    var i: usize = 0;

    while (i < 2400) : (i += 1) {
        const x = b.rng.range(-def.half + 8, def.half - 8);
        const z = b.rng.range(-def.half + 8, def.half - 8);
        const e = rimEdge(x, z);

        if (e > def.half - 10) continue;

        const inner = @max(@abs(x), @abs(z)) < 190 and !inBox(x, z, -190, -66, -110, 76);

        if (inner and !inBox(x, z, -100, -200, 100, -150)) {
            if (inBox(x, z, -102, -82, 102, 104) or inBox(x, z, 86, 78, 186, 142) or inBox(x, z, 102, -60, 196, 70) or inBox(x, z, -130, -150, 130, -82) or inBox(x, z, -172, 88, -96, 140)) continue;
        }

        if (trailDist(x, z) < 5 or !open(x, z, 3)) continue;

        const roll = b.rng.next();
        const tree: K = if (roll < 0.45) .oak else if (roll < 0.75) .birch else .pine;

        put(b, tree, x, z, b.rng.range(0, 6), b.rng.range(1.0, 1.8));

        if (b.rng.next() < 0.4) put(b, .bush, x + jit(b, 3), z + jit(b, 3), b.rng.range(0, 6), b.rng.range(0.8, 1.3));
    }

    for (paths) |s| {
        const dx = s[2] - s[0];
        const dz = s[3] - s[1];
        const len = @sqrt(dx * dx + dz * dz);
        var d: f32 = 10;

        while (d < len - 5) : (d += 24) {
            const u = d / len;
            const x = s[0] + dx * u + dz / len * 5;
            const z = s[1] + dz * u - dx / len * 5;

            if (!open(x, z, 1.5) or inBox(x, z, -102, -82, 102, 104)) continue;

            put(b, .picnic, x, z, std.math.atan2(dx, dz) + hp, 1.1);
            put(b, .bin, x + dx / len * 2, z + dz / len * 2, 0, 1);
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
    standBacks(b);
    concourse(b);
    clubSide(b);
    training(b);
    athletics(b);
    plazaFill(b);
    fanZone(b);
    park(b);
    shadeProps(b);
}

fn setSpots(gpa: std.mem.Allocator) void {
    wd.autoSpots(gpa, .{ .loot = 48, .vehicles = 6, .seed = 331 });
}
