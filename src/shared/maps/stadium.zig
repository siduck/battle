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
    .tufts = 0.6,
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
        const band = @mod(@floor((x + pitch_x) / 5.25), 2);

        c = if (band < 1) .{ 70, 146, 110 } else .{ 84, 162, 122 };
    } else if (od < track_out and od > track_in - 0.5) {
        c = mix3(.{ 176, 82, 60 }, .{ 164, 74, 56 }, t.fbm(x * 0.3, z * 0.3));
    } else if (od < track_in) {
        c = .{ 80, 150, 112 };
    } else if (@abs(x) < 101 and z > -80 and z < 110) {
        const tile = @mod(@floor(x / 4) + @floor(z / 4), 2);

        c = if (tile < 1) .{ 168, 166, 158 } else .{ 156, 154, 148 };
    }

    if (inBox(x, z, -130, -150, 130, -82)) {
        c = mix3(.{ 150, 144, 132 }, .{ 136, 130, 120 }, t.fbm(x * 0.2, z * 0.2));
    }

    if (inBox(x, z, 104, -58, 196, 52)) {
        const lane = @abs(z + 3) < 6;

        c = if (lane) .{ 176, 84, 62 } else c;
    }

    for ([_][2]f32{ .{ 110, 110 }, .{ 160, 110 } }) |p| {
        if (inBox(x, z, p[0] - 18, p[1] - 28, p[0] + 18, p[1] + 28)) {
            const band = @mod(@floor((z - p[1]) / 5), 2);

            c = if (band < 1) .{ 74, 148, 112 } else .{ 86, 160, 120 };
        }
    }

    const pd = trailDist(x, z);

    c = mix3(c, .{ 132, 132, 134 }, 1 - t.smooth(3, 4.5, pd));

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

fn line(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32) void {
    const y = t.height((x0 + x1) / 2, (z0 + z1) / 2);

    b.deco(vec(@min(x0, x1) - 0.08, y + 0.02, @min(z0, z1) - 0.08), vec(@max(x0, x1) + 0.08, y + 0.05, @max(z0, z1) + 0.08), .flag_cloth);
}

fn ring(b: *Builder, cx: f32, cz: f32, r: f32, a0: f32, a1: f32) void {
    const n: usize = 16;
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
        b.putAt(kit.of(.goal), vec(gx + s * 1, t.height(gx, 0), 0), -s * hp, 1);
    }

    for ([_][2]f32{ .{ -1, -1 }, .{ -1, 1 }, .{ 1, -1 }, .{ 1, 1 } }) |c| put(b, .cornerflag, c[0] * pitch_x, c[1] * pitch_z, 0, 1);

    var lane: f32 = track_in + 1.5;

    while (lane < track_out) : (lane += 1.5) {
        line(b, -46, -lane, 46, -lane);
        line(b, -46, lane, 46, lane);
        ring(b, 46, 0, lane, -hp, hp);
        ring(b, -46, 0, lane, hp, 3 * hp);
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

    var x: f32 = -pitch_x + 2;

    while (x < pitch_x - 1) : (x += 1.4) {
        if (@mod(x + pitch_x, 16) < 3) continue;

        put(b, .hoarding, x, -pitch_z - 3, 0, 1);
        put(b, .hoarding, x, pitch_z + 3, std.math.pi, 1);
    }

    var z: f32 = -pitch_z + 2;

    while (z < pitch_z - 1) : (z += 1.4) {
        if (@abs(z) < 6 or @mod(z + pitch_z, 12) < 3) continue;

        put(b, .hoarding, -pitch_x - 4, z, hp, 1);
        put(b, .hoarding, pitch_x + 4, z, -hp, 1);
    }

    put(b, .dugout, -12, pitch_z + 6.5, std.math.pi, 1);
    put(b, .dugout, 12, pitch_z + 6.5, std.math.pi, 1);
    put(b, .bench, -20, pitch_z + 6, std.math.pi, 1);
    put(b, .bench, 20, pitch_z + 6, std.math.pi, 1);
    put(b, .scoreboard, end_front - 4, 36, -hp - 0.4, 1);
    put(b, .scoreboard, -end_front + 4, -36, hp - 0.4, 1);
    put(b, .clock, -end_front + 3, 34, hp, 1);
}

fn standBacks(b: *Builder) void {
    const back = stand_front + stand_depth + 1.4;
    var x: f32 = -stand_x + 3;
    var i: usize = 0;

    while (x < stand_x - 2) : (x += 6) {
        if (@abs(x) < 9) continue;

        for ([_]f32{ -1, 1 }) |s| {
            const z = s * back;
            const yaw: f32 = if (s > 0) std.math.pi else 0;

            switch (i % 4) {
                0 => {
                    put(b, .hoarding, x - 0.7, z, yaw, 1.6);
                    put(b, .hoarding, x + 0.7, z, yaw, 1.6);
                },
                1 => put(b, .flagpole, x, z + s * 1.5, 0, 1),
                2 => {
                    put(b, .bin, x, z + s * 0.6, 0, 1);
                    put(b, .bush, x + 2, z + s * 1.2, 0, 1.1);
                },
                else => put(b, .birch, x, z + s * 2.5, b.rng.range(0, 6), 1.3),
            }
        }

        i += 1;
    }

    var z: f32 = -26;

    while (z < 28) : (z += 7) {
        for ([_]f32{ -1, 1 }) |s| {
            const bx = s * (end_front + 10.6);

            if (@mod(z + 26, 14) < 7) put(b, .hoarding, bx, z, -s * hp, 1.6) else put(b, .oak, bx + s * 2.5, z, b.rng.range(0, 6), 1.1);
        }
    }
}

fn matchDay(b: *Builder) void {
    const kits = [_]struct { e: K, x: f32, z: f32, yaw: f32 }{
        .{ .e = .inflatable, .x = 0, .z = -pitch_z - 0.5, .yaw = 0 },
        .{ .e = .medtent, .x = -30, .z = -pitch_z + 4, .yaw = 0.2 },
        .{ .e = .medtent, .x = 36, .z = pitch_z - 5, .yaw = 2.9 },
        .{ .e = .tarp, .x = -18, .z = 8, .yaw = 0.3 },
        .{ .e = .tarp, .x = -16, .z = 10.5, .yaw = 0.3 },
        .{ .e = .tarp, .x = 22, .z = -12, .yaw = -0.4 },
        .{ .e = .tarp, .x = 24, .z = -9.5, .yaw = -0.4 },
        .{ .e = .tarp, .x = 8, .z = 18, .yaw = 1.2 },
        .{ .e = .tarp, .x = -36, .z = -14, .yaw = 0.1 },
        .{ .e = .trolley, .x = -40, .z = 22, .yaw = 0.6 },
        .{ .e = .trolley, .x = 40, .z = 10, .yaw = -0.2 },
        .{ .e = .linecart, .x = -6, .z = -20, .yaw = 0.9 },
        .{ .e = .ballcart, .x = 30, .z = 24, .yaw = 0.4 },
        .{ .e = .ballcart, .x = -26, .z = -26, .yaw = 0.2 },
        .{ .e = .scaffold, .x = -24, .z = pitch_z + 9.5, .yaw = 0 },
        .{ .e = .scaffold, .x = 30, .z = -pitch_z - 9.5, .yaw = 0 },
        .{ .e = .scaffold, .x = end_front - 12, .z = -14, .yaw = 0 },
        .{ .e = .tactics, .x = -10, .z = pitch_z + 2, .yaw = 0 },
        .{ .e = .stretcher, .x = -28, .z = -pitch_z + 7, .yaw = 0.3 },
        .{ .e = .chain, .x = 0, .z = pitch_z + 1.6, .yaw = 0 },
    };

    for (kits) |p| {
        put(b, p.e, p.x, p.z, p.yaw, 1);
        claim(p.x, p.z, 2);
    }

    const walls = [_][4]f32{ .{ -40, -8, 6, 0 }, .{ -40, -8, 4, 1 }, .{ 32, 6, 6, 0 }, .{ 36, 6, 4, 1 }, .{ -14, 22, 5, 0 }, .{ 10, -24, 5, 0 }, .{ -4, 6, 4, 1 }, .{ 18, 20, 4, 1 }, .{ -24, -18, 4, 1 }, .{ 44, -28, 5, 0 }, .{ -46, 24, 4, 1 } };

    for (walls) |w| {
        var j: usize = 0;
        const n: usize = @intFromFloat(w[2]);

        while (j < n) : (j += 1) {
            const off = @as(f32, @floatFromInt(j)) * 1.4;

            if (w[3] < 0.5) put(b, .hoarding, w[0] + off, w[1], 0, 1.3) else put(b, .hoarding, w[0], w[1] + off, hp, 1.3);
        }

        claim(w[0], w[1], 3);
    }

    for ([_][3]f32{ .{ -12, -8, 0.4 }, .{ 26, 16, 2.6 }, .{ -36, 14, 1.2 }, .{ 40, -14, 0.1 } }) |p| {
        put(b, .medtent, p[0], p[1], p[2], 1);
        claim(p[0], p[1], 3);
    }

    put(b, .inflatable, -46, -4, hp, 1);
    put(b, .inflatable, 46, 4, -hp, 1);
    put(b, .scaffold, 0, 18, 0, 1);
    put(b, .scaffold, -20, -4, 0, 1);
    put(b, .scaffold, 20, 0, 0, 1);

    for ([_][2]f32{ .{ 12, -2 }, .{ 14, 1 }, .{ 11, 3.5 }, .{ -32, 4 }, .{ -30, 6.5 }, .{ 44, -22 }, .{ 46, -19 } }) |p| put(b, .dummy, p[0], p[1], 0, 1);

    scatterIn(b, &.{ .kitbag, .crate, .medbag, .cones, .yardmark }, 40, 0, 0, 40, 0.9, 1.2);
    scatterIn(b, &.{ .kitbag, .crate, .bin, .cones }, 30, 0, -pitch_z - 7, 30, 0.9, 1.2);
}

fn concourse(b: *Builder) void {
    const zg: f32 = 104;

    house(b, .gate, 0, zg, 0);

    for ([_]f32{ -24, -14, 14, 24 }) |x| house(b, .turnstile, x, zg, 0);

    for ([_]f32{ -40, 40 }) |x| house(b, .booth, x, zg - 2, 0);

    for ([_][3]f32{ .{ -46, 78, 0 }, .{ -20, 82, 0 }, .{ 22, 82, 0 }, .{ 48, 78, 0 }, .{ -46, -70, std.math.pi }, .{ 46, -70, std.math.pi } }) |p| {
        house(b, .kiosk, p[0], p[1], p[2]);
        put(b, .bin, p[0] + 3, p[1] - 2.5, 0, 1);
        put(b, .crate, p[0] - 2.6, p[1] - 2.2, 0.3, 1);
    }

    var x: f32 = -60;

    while (x <= 60) : (x += 12) {
        put(b, if (@mod(x, 24) == 0) .horn else .flagpole, x, 70, 0, 1);
        put(b, .bin, x + 4, 70.5, 0, 1);
    }

    for ([_][2]f32{ .{ -8, 90 }, .{ 8, 90 }, .{ -60, 96 }, .{ 60, 96 } }) |p| put(b, .clock, p[0], p[1], 0, 1);

    x = -96;

    while (x < 96) : (x += 2.4) {
        if (@abs(x) < 34 or @abs(x - 76) < 5 or @abs(x + 76) < 5) continue;

        put(b, .wall, x, zg, 0, 1);
    }

    for ([_][4]f32{ .{ -102, -80, -102, 104 }, .{ 102, -80, 102, 104 } }) |s| {
        var z = s[1];

        while (z < s[3]) : (z += 2.4) {
            if (@abs(z - 76) < 6 or @abs(z + 66) < 6 or @abs(z) < 5) continue;

            put(b, .mesh, s[0], z, hp, 1);
        }
    }
}

fn plaza(b: *Builder) void {
    var i: usize = 0;

    while (i < 420) : (i += 1) {
        const x = b.rng.range(-98, 98);
        const z = b.rng.range(-78, 108);

        if (@abs(x) < stand_x + 4 and @abs(z) < stand_front + stand_depth + 4) continue;

        if (@abs(x) < end_front + 12 and @abs(z) < 34) continue;

        if (trailDist(x, z) < 5 or !open(x, z, 3.5)) continue;

        const roll = b.rng.next();

        if (roll < 0.3) {
            put(b, if (b.rng.next() < 0.5) .birch else .oak, x, z, b.rng.range(0, 6), b.rng.range(0.9, 1.3));
            put(b, .bush, x + 1.6, z + 1.2, 0, 0.9);
            put(b, .parkbench, x, z - 2.6, 0, 1);
        } else if (roll < 0.45) {
            put(b, .bin, x, z, 0, 1);
            put(b, .bush, x + 1.4, z, 0, 1);
        } else if (roll < 0.58) {
            put(b, .scaffold, x, z, if (b.rng.next() < 0.5) 0 else hp, 1);
        } else if (roll < 0.7) {
            put(b, .hoarding, x, z, 0, 1.5);
            put(b, .hoarding, x + 1.5, z, 0, 1.5);
            put(b, .hoarding, x + 3, z, 0, 1.5);
        } else if (roll < 0.8) {
            put(b, .tarp, x, z, b.rng.range(0, 6), 1);
            put(b, .trolley, x + 2, z + 1, b.rng.range(0, 6), 1);
            put(b, .crate, x - 1.5, z + 1, 0, 1);
        } else if (roll < 0.9) {
            put(b, .tarp, x, z, b.rng.range(0, 6), 1);
            put(b, .linecart, x + 2, z - 1, 0.4, 1);
        } else {
            put(b, .medtent, x, z, b.rng.range(0, 6), 1);
            put(b, .stretcher, x + 3, z, 0.2, 1);
        }

        claim(x, z, 3);
    }
}

fn clubSide(b: *Builder) void {
    house(b, .clubhouse, -128, 112, 0);
    house(b, .firstaid, -104, 128, -hp);
    house(b, .toilets, -150, 132, std.math.pi);
    house(b, .pressbox, -164, 102, hp);
    house(b, .toilets, -40, -94, 0);
    house(b, .firstaid, 52, -92, 0);
    put(b, .medtent, -108, 92, 0.1, 1);
    put(b, .flagpole, -128, 98, 0, 1);
    put(b, .flagpole, -122, 98, 0, 1);
    scatterIn(b, &.{ .kitbag, .bin, .crate, .ballcart, .parkbench }, 18, -130, 116, 24, 0.9, 1.1);
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
        put(b, .ladder, p[0] - 8, p[1] + 8, 0, 1);
        put(b, .bags, p[0] + 8, p[1] - 10, 0, 1);
        put(b, .dummy, p[0] - 4, p[1] - 16, 0, 1);
        put(b, .dummy, p[0] + 1, p[1] - 15, 0, 1);
        put(b, .dummy, p[0] + 6, p[1] - 16.5, 0, 1);
        put(b, .ballcart, p[0] + 12, p[1] + 14, 0.4, 1);
        put(b, .tactics, p[0] - 14, p[1] + 2, hp, 1);
        put(b, .bench, p[0] - 19.5, p[1] - 6, hp, 1);
        put(b, .bench, p[0] - 19.5, p[1] + 6, hp, 1);
        scatterIn(b, &.{ .cones, .kitbag, .crate }, 10, p[0], p[1], 16, 0.9, 1.2);
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
}

fn athletics(b: *Builder) void {
    put(b, .discus, 170, 30, 0, 1);
    api.box(b, 165.4, 0, 25, 166.4, 6, 35);
    api.box(b, 173.6, 0, 25, 174.6, 6, 35);
    api.box(b, 166, 0, 34, 174, 6, 35);
    put(b, .highjump, 130, 30, 0, 1);
    put(b, .longjump, 120, -3, hp, 1);
    put(b, .longjump, 150, -3, hp, 1);
    put(b, .shotput, 140, 30, 0, 1);
    put(b, .shotput, 186, -40, 0, 1);

    var x: f32 = 112;

    while (x < 190) : (x += 10) {
        put(b, .hurdle, x, -30, hp, 1);
        put(b, .hurdle, x + 5, -36, hp, 1);
        put(b, .hurdle, x, -42, hp, 1);
    }

    for ([_]f32{ -30, -36, -42 }) |z| put(b, .blocks, 106, z, hp, 1);

    scatterIn(b, &.{ .kitbag, .crate, .cones, .bin }, 14, 150, 0, 40, 0.9, 1.2);
    scatterIn(b, &.{ .oak, .bush, .parkbench, .birch, .tarp, .bush, .medtent, .tarp }, 46, 150, -5, 50, 0.9, 1.25);
    house(b, .clubhouse, 150, -80, 0);
    house(b, .toilets, 176, 60, std.math.pi);
}

fn carPark(b: *Builder) void {
    var x: f32 = -120;

    while (x <= 120) : (x += 5) {
        for ([_]f32{ -96, -118, -140 }) |z| {
            line(b, x, z - 4.5, x, z + 4.5);

            if (b.rng.next() < 0.18 and @abs(x) > 8) put(b, .hoarding, x + 2.5, z, hp, 1.5);
        }
    }

    for ([_]f32{ -107, -129 }) |z| {
        x = -120;

        while (x < 120) : (x += 20) {
            put(b, .bush, x + 10, z, 0, 1);
            put(b, .oak, x, z, b.rng.range(0, 6), 1.1);
        }
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

            put(b, .parkbench, x, z, std.math.atan2(dx, dz) + hp, 1);
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
    plaza(b);
    carPark(b);
    park(b);
    shadeProps(b);
}

fn setSpots(gpa: std.mem.Allocator) void {
    wd.autoSpots(gpa, .{ .loot = 48, .vehicles = 6, .seed = 331 });
}
