const std = @import("std");
const api = @import("api.zig");
const ck = @import("construction_kit.zig");

const t = api.terrain;
const kit = ck.kit;
const S = ck.solids;
const K = ck.K;
const vec = api.vec;
const Builder = api.Builder;
const half_pi = api.half_pi;
const pi = std.math.pi;

pub const def: api.Def = .{
    .name = "Construction",
    .note = "Tower crane, half-built towers and a dig",
    .tint = .{ 214, 170, 72 },
    .ready = true,
    .half = 178,
    .play = 150,
    .facet = 2.0,
    .height = height,
    .ground = ground,
    .build = build,
    .spots = spots,
    .props = &ck.table,
    .palette = .{
        .sun_dir = .{ 0.52, 0.62, -0.58 },
        .sun_tint = .{ 1.2, 1.04, 0.86 },
        .grade_tint = .{ 1.04, 1.0, 0.95 },
        .grade_sat = 1.16,
        .fog = 0.0032,
        .fog_color = .{ 0.84, 0.82, 0.78 },
        .amb_sky = .{ 0.9, 0.98, 1.16 },
        .amb_ground = .{ 0.82, 0.72, 0.58 },
        .shade_tint = .{ 0.86, 0.9, 1.06 },
        .zenith = .{ 0.08, 0.26, 0.6 },
    },
    .backdrop = .{ 132, 120, 102 },
    .floor_y = -7.6,
    .grip = 0.8,
    .tufts = 0.06,
};

const edge: f32 = 147;
const tower_at = [2]f32{ 0, 8 };
const tower2_at = [2]f32{ -70, 62 };
const frame_at = [2]f32{ 58, 50 };
const pit = [4]f32{ 58, -108, 118, -48 };
const pit_floor: f32 = -7.0;
const ramp_z = [2]f32{ -86, -74 };
const ramp_x = [2]f32{ 22, 62 };

const Rect = struct { x0: f32, z0: f32, x1: f32, z1: f32 };

const Stack = struct { x: f32, z: f32, yaw: f32, n: u8, kind: K };

const stacks = [_]Stack{
    .{ .x = -136, .z = -40, .yaw = 0, .n = 2, .kind = .box_red },
    .{ .x = -136, .z = -37.4, .yaw = 0, .n = 1, .kind = .box_blue },
    .{ .x = -136, .z = -30, .yaw = 0, .n = 3, .kind = .box_green },
    .{ .x = -136, .z = -27.4, .yaw = 0, .n = 2, .kind = .box_blue },
    .{ .x = -136, .z = -16, .yaw = 0, .n = 2, .kind = .box_blue },
    .{ .x = -136, .z = -6, .yaw = 0, .n = 1, .kind = .box_red },
    .{ .x = -136, .z = -3.4, .yaw = 0, .n = 2, .kind = .box_green },
    .{ .x = -136, .z = 8, .yaw = 0, .n = 3, .kind = .box_red },
    .{ .x = -136, .z = 18, .yaw = 0, .n = 2, .kind = .box_green },
    .{ .x = -136, .z = 20.6, .yaw = 0, .n = 1, .kind = .box_blue },
    .{ .x = -118, .z = -36, .yaw = half_pi, .n = 2, .kind = .box_blue },
    .{ .x = -115.4, .z = -36, .yaw = half_pi, .n = 1, .kind = .box_red },
    .{ .x = -118, .z = -14, .yaw = half_pi, .n = 1, .kind = .box_green },
    .{ .x = -118, .z = 6, .yaw = half_pi, .n = 2, .kind = .box_red },
    .{ .x = -115.4, .z = 6, .yaw = half_pi, .n = 3, .kind = .box_blue },
    .{ .x = -104, .z = -26, .yaw = 0, .n = 1, .kind = .box_blue },
    .{ .x = -104, .z = 16, .yaw = 0, .n = 2, .kind = .box_green },
    .{ .x = -100, .z = -8, .yaw = half_pi, .n = 1, .kind = .box_red },
    .{ .x = -126, .z = 136, .yaw = 0, .n = 2, .kind = .box_office },
    .{ .x = -119.6, .z = 136, .yaw = 0, .n = 2, .kind = .box_office },
    .{ .x = -113.2, .z = 136, .yaw = 0, .n = 1, .kind = .box_office },
    .{ .x = 130, .z = 2, .yaw = half_pi, .n = 2, .kind = .box_blue },
    .{ .x = 132.6, .z = 2, .yaw = half_pi, .n = 1, .kind = .box_green },
    .{ .x = 40, .z = 130, .yaw = 0, .n = 2, .kind = .box_red },
    .{ .x = -24, .z = -122, .yaw = half_pi, .n = 1, .kind = .box_office },
};

const shade_rects = [_]Rect{
    .{ .x0 = -15, .z0 = -3, .x1 = 13, .z1 = 18 },
    .{ .x0 = -81, .z0 = 54, .x1 = -61, .z1 = 69 },
    .{ .x0 = 55.5, .z0 = 47.5, .x1 = 76.5, .z1 = 60.5 },
    .{ .x0 = -135, .z0 = 116, .x1 = -112, .z1 = 124 },
    .{ .x0 = -100, .z0 = 116, .x1 = -77, .z1 = 124 },
    .{ .x0 = 113, .z0 = 51, .x1 = 127, .z1 = 73 },
    .{ .x0 = 0, .z0 = -138, .x1 = 20, .z1 = -126 },
};

fn rectDist(r: Rect, x: f32, z: f32) f32 {
    const dx = @max(r.x0 - x, 0, x - r.x1);
    const dz = @max(r.z0 - z, 0, z - r.z1);

    return @sqrt(dx * dx + dz * dz);
}

fn pitDepth(x: f32, z: f32) f32 {
    if (x < pit[0] - 1 or x > pit[2] + 1 or z < pit[1] - 1 or z > pit[3] + 1) return 0;

    const side = @min(@min(x - pit[0], pit[2] - x), z - pit[1]);
    const north = pit[3] - z;

    return pit_floor * @min(t.smooth(0, 9, side), t.smooth(0, 2.2, north));
}

fn rampDepth(x: f32, z: f32) f32 {
    const across = @min(z - ramp_z[0], ramp_z[1] - z);

    if (across < -3 or x < ramp_x[0] - 1 or x > ramp_x[1] + 4) return 0;

    const along = std.math.clamp((x - ramp_x[0]) / (ramp_x[1] - ramp_x[0]), 0, 1);

    return pit_floor * along * t.smooth(-3, 0.5, across);
}

const Mound = struct { x: f32, z: f32, r: f32, h: f32, tone: u8 };

const mounds = [_]Mound{
    .{ .x = -60, .z = -50, .r = 9, .h = 3.2, .tone = 0 },
    .{ .x = 70, .z = -10, .r = 10, .h = 3.8, .tone = 1 },
    .{ .x = -100, .z = 60, .r = 8, .h = 3.0, .tone = 2 },
    .{ .x = 30, .z = 80, .r = 9, .h = 3.4, .tone = 0 },
    .{ .x = -40, .z = 120, .r = 8, .h = 2.8, .tone = 1 },
    .{ .x = 140, .z = -78, .r = 7, .h = 3.2, .tone = 0 },
    .{ .x = 64, .z = 140, .r = 8, .h = 3.0, .tone = 2 },
    .{ .x = 18, .z = -120, .r = 7, .h = 2.6, .tone = 1 },
    .{ .x = -76, .z = -42, .r = 6, .h = 2.2, .tone = 2 },
    .{ .x = 128, .z = 60, .r = 8, .h = 3.0, .tone = 1 },
};

fn moundAt(x: f32, z: f32) struct { h: f32, tone: u8 } {
    var best: f32 = 0;
    var tone: u8 = 0;

    for (mounds) |m| {
        const dx = x - m.x;
        const dz = z - m.z;
        const d = @sqrt(dx * dx + dz * dz) / (m.r * (0.85 + t.fbm(x * 0.15 + m.x, z * 0.15) * 0.3));
        const h = m.h * (1 - t.smooth(0.15, 1.0, d));

        if (h > best) {
            best = h;
            tone = m.tone;
        }
    }

    return .{ .h = best, .tone = tone };
}

fn height(x: f32, z: f32) f32 {
    const box = @max(@abs(x), @abs(z));
    const bund = t.smooth(edge + 3, t.half, box) * (6 + t.fbm(x * 0.05, z * 0.05) * 5);
    const dig = @min(pitDepth(x, z), rampDepth(x, z));

    if (dig < -0.01) return dig;

    return bund + moundAt(x, z).h + (t.fbm(x * 0.03 + 7, z * 0.03 - 3) - 0.45) * 0.4 * (1 - t.smooth(edge - 10, edge, box));
}

fn mixc(a: [3]f32, b: [3]f32, q: f32) [3]f32 {
    return api.mix3(a, b, q);
}

fn inRect(x: f32, z: f32, x0: f32, z0: f32, x1: f32, z1: f32) bool {
    return x > x0 and x < x1 and z > z0 and z < z1;
}

fn pad(x: f32, z: f32, fine: f32) [3]f32 {
    const jx = @mod(x, 6);
    const jz = @mod(z, 6);
    const joint = @min(@min(jx, 6 - jx), @min(jz, 6 - jz)) < 0.45;
    const stain = t.smooth(0.5, 0.7, t.fbm(x * 0.07 + 3, z * 0.07));

    if (joint) return .{ 146, 144, 138 };

    return mixc(mixc(.{ 180, 178, 170 }, .{ 168, 165, 156 }, fine), .{ 150, 146, 136 }, stain * 0.7);
}

const occ_n: usize = 180;
const occ_cell: f32 = 2;
var occ_grid: [occ_n * occ_n]f32 = undefined;
var occ_for: usize = std.math.maxInt(usize);

fn buildOcc() void {
    const pl = api.world.placements;

    @memset(&occ_grid, 1);
    occ_for = pl.len;

    for (pl) |p| {
        const info = api.props.info(p.kind);

        if (info.group == .ground) continue;

        if (@abs(p.pos.x) > 160 or @abs(p.pos.z) > 160) continue;

        if (p.pos.y - t.height(p.pos.x, p.pos.z) > 1.0) continue;

        const quarter = @abs(@sin(p.yaw * 2)) < 0.2;
        const turned = @abs(@sin(p.yaw)) > 0.7;
        var hx = (info.max[0] - info.min[0]) * 0.5 * p.scale;
        var hz = (info.max[2] - info.min[2]) * 0.5 * p.scale;

        if (!quarter) {
            const r = @max(hx, hz) * 0.8;

            hx = r;
            hz = r;
        } else if (turned) {
            const tmp = hx;

            hx = hz;
            hz = tmp;
        }

        if (hx > 14 or hz > 14) continue;

        const c = rot(p.yaw, (info.max[0] + info.min[0]) * 0.5 * p.scale, (info.max[2] + info.min[2]) * 0.5 * p.scale);
        const cx = p.pos.x + c[0];
        const cz = p.pos.z + c[1];
        const reach: f32 = 1.6;
        const strength: f32 = if (info.group == .rock) 0.25 else 0.4;
        const ix0: i32 = @intFromFloat(@floor((cx - hx - reach + t.half) / occ_cell));
        const ix1: i32 = @intFromFloat(@ceil((cx + hx + reach + t.half) / occ_cell));
        const iz0: i32 = @intFromFloat(@floor((cz - hz - reach + t.half) / occ_cell));
        const iz1: i32 = @intFromFloat(@ceil((cz + hz + reach + t.half) / occ_cell));
        var ix = @max(ix0, 0);

        while (ix <= @min(ix1, @as(i32, occ_n - 1))) : (ix += 1) {
            var iz = @max(iz0, 0);

            while (iz <= @min(iz1, @as(i32, occ_n - 1))) : (iz += 1) {
                const gx = @as(f32, @floatFromInt(ix)) * occ_cell - t.half;
                const gz = @as(f32, @floatFromInt(iz)) * occ_cell - t.half;
                const dx = @max(@abs(gx - cx) - hx, 0);
                const dz = @max(@abs(gz - cz) - hz, 0);
                const d = @sqrt(dx * dx + dz * dz);
                const v = 1 - strength * (1 - t.smooth(0, reach, d));
                const i: usize = @intCast(ix * @as(i32, occ_n) + iz);

                occ_grid[i] = @min(occ_grid[i], v);
            }
        }
    }
}

fn occAt(x: f32, z: f32) f32 {
    if (occ_for != api.world.placements.len) buildOcc();

    const fx = (x + t.half) / occ_cell;
    const fz = (z + t.half) / occ_cell;

    if (fx < 0 or fz < 0 or fx >= @as(f32, occ_n - 1) or fz >= @as(f32, occ_n - 1)) return 1;

    const ix: usize = @intFromFloat(fx);
    const iz: usize = @intFromFloat(fz);
    const ux = fx - @floor(fx);
    const uz = fz - @floor(fz);
    const a = occ_grid[ix * occ_n + iz];
    const b2 = occ_grid[(ix + 1) * occ_n + iz];
    const c = occ_grid[ix * occ_n + iz + 1];
    const d = occ_grid[(ix + 1) * occ_n + iz + 1];

    return (a * (1 - ux) + b2 * ux) * (1 - uz) + (c * (1 - ux) + d * ux) * uz;
}

fn ground(x: f32, z: f32) api.Rgb {
    const n = t.normal(x, z);
    const slope = 1 - n.y;
    const h = t.height(x, z);
    const vary = 0.95 + t.fbm(x * 0.13, z * 0.13) * 0.1;
    const blot = t.fbm(x * 0.022 + 11, z * 0.022 - 5);
    const fine = t.fbm(x * 0.35, z * 0.35);
    const grit = t.fbm(x * 0.9 + 31, z * 0.9 - 17);
    const patch = t.fbm(x * 0.07 - 40, z * 0.07 + 9);
    var c: [3]f32 = mixc(.{ 124, 110, 92 }, .{ 108, 96, 80 }, fine);

    c = mixc(c, .{ 140, 132, 118 }, t.smooth(0.38, 0.66, patch) * 0.7);
    c = mixc(c, .{ 92, 76, 60 }, t.smooth(0.48, 0.66, blot) * 0.75);
    c = mixc(c, .{ 84, 74, 64 }, t.smooth(0.55, 0.72, grit) * 0.4);
    c = mixc(c, .{ 160, 152, 138 }, t.smooth(0.6, 0.75, t.fbm(x * 0.6 - 9, z * 0.6 + 4)) * 0.3);

    const puddle = t.smooth(0.68, 0.72, t.fbm(x * 0.06 + 70, z * 0.06 - 30));

    c = mixc(c, .{ 70, 74, 80 }, puddle * 0.9);

    const road = roadDist(x, z);

    if (road < 6.5) {
        const lane = @abs(road - 2.4);

        c = mixc(c, .{ 104, 100, 94 }, 1 - t.smooth(4.5, 6.5, road));
        c = mixc(c, .{ 84, 80, 76 }, (1 - t.smooth(0.3, 0.8, lane)) * 0.7);
    }

    if (inRect(x, z, -32, -16, 30, 34) or inRect(x, z, -86, 48, -56, 76) or inRect(x, z, 50, 42, 86, 66)) c = pad(x, z, fine);

    if (inRect(x, z, -146, 92, -78, 146) or inRect(x, z, -146, -52, -96, 34)) c = mixc(.{ 160, 156, 146 }, .{ 144, 140, 130 }, fine);

    if (inRect(x, z, -146, -146, -62, -66) and @mod(z + 146, 14) < 0.5) c = .{ 210, 200, 156 };

    if (h < -0.3) {
        const wet = t.smooth(0.55, 0.7, t.fbm(x * 0.09, z * 0.09));

        c = mixc(.{ 120, 96, 72 }, .{ 96, 78, 60 }, wet);

        if (h < pit_floor + 0.2 and inRect(x, z, 74, -94, 104, -66)) c = pad(x, z, fine);
    }

    if (slope > 0.12) c = mixc(c, .{ 124, 98, 74 }, t.smooth(0.12, 0.35, slope));

    const md = moundAt(x, z);

    if (md.h > 0.15) {
        const tones = [3][3]f32{ .{ 112, 86, 62 }, .{ 176, 156, 116 }, .{ 132, 130, 126 } };
        const grain = 0.92 + fine * 0.16;

        c = mixc(c, api.mix3(tones[md.tone], .{ tones[md.tone][0] * grain, tones[md.tone][1] * grain, tones[md.tone][2] * grain }, 1), t.smooth(0.15, 0.8, md.h));
    }

    if (@max(@abs(x), @abs(z)) > edge + 1) c = mixc(.{ 116, 104, 84 }, .{ 100, 110, 78 }, t.smooth(0.4, 0.7, t.fbm(x * 0.06, z * 0.06)));

    var occ: f32 = occAt(x, z);

    for (shade_rects) |r| occ = @min(occ, 0.7 + 0.3 * t.smooth(0, 3.2, rectDist(r, x, z)));

    for (stacks) |st| {
        const w: f32 = if (st.yaw > 0.1) 1.4 else 3.2;
        const d: f32 = if (st.yaw > 0.1) 3.2 else 1.4;
        const dx = @max(@abs(x - st.x) - w, 0);
        const dz = @max(@abs(z - st.z) - d, 0);

        occ = @min(occ, 0.74 + 0.26 * t.smooth(0, 2.2, @sqrt(dx * dx + dz * dz)));
    }

    return api.shade(c, vary * occ * (1 + n.x * 0.05 - n.z * 0.03));
}

fn segDist(x: f32, z: f32, ax: f32, az: f32, bx: f32, bz: f32) f32 {
    const dx = bx - ax;
    const dz = bz - az;
    const q = std.math.clamp(((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz), 0, 1);
    const px = ax + dx * q - x;
    const pz = az + dz * q - z;

    return @sqrt(px * px + pz * pz);
}

const roads = [_][4]f32{
    .{ -20, -152, -20, -44 },
    .{ -44, -44, 44, -44 },
    .{ -44, -44, -44, 40 },
    .{ 44, -44, 44, 40 },
    .{ -44, 40, 44, 40 },
    .{ 0, 40, 0, 140 },
    .{ -44, 0, -96, 0 },
    .{ 44, -44, 44, -80 },
    .{ 22, -80, 62, -80 },
    .{ 44, 0, 140, 0 },
    .{ -44, 40, -96, 86 },
    .{ -96, 86, -96, 140 },
    .{ 44, 40, 110, 90 },
    .{ -20, -100, -100, -100 },
};

fn roadDist(x: f32, z: f32) f32 {
    var d: f32 = 1e9;

    for (roads) |r| d = @min(d, segDist(x, z, r[0], r[1], r[2], r[3]));

    return d;
}

fn rot(yaw: f32, x: f32, z: f32) [2]f32 {
    const c = @cos(yaw);
    const s = @sin(yaw);

    return .{ x * c + z * s, -x * s + z * c };
}

fn structure(b: *Builder, kind: K, sol: []const [7]f32, x: f32, y: f32, z: f32, yaw: f32) void {
    b.putAt(kit.of(kind), vec(x, y, z), yaw, 1);

    for (sol) |q| {
        const a = rot(yaw, q[1], q[3]);
        const c = rot(yaw, q[4], q[6]);
        const e = rot(yaw, q[1], q[6]);
        const f = rot(yaw, q[4], q[3]);
        const mn = vec(@min(@min(a[0], c[0]), @min(e[0], f[0])) + x, q[2] + y, @min(@min(a[1], c[1]), @min(e[1], f[1])) + z);
        const mx = vec(@max(@max(a[0], c[0]), @max(e[0], f[0])) + x, q[5] + y, @max(@max(a[1], c[1]), @max(e[1], f[1])) + z);

        if (q[0] < 0.5) {
            b.solid(.{ .box = .{ .min = mn, .max = mx } });

            continue;
        }

        const dir: [2]f32 = switch (@as(u8, @intFromFloat(q[0]))) {
            1 => .{ 1, 0 },
            2 => .{ -1, 0 },
            3 => .{ 0, 1 },
            else => .{ 0, -1 },
        };
        const w = rot(yaw, dir[0], dir[1]);
        const rise: api.geom.Rise = if (@abs(w[0]) > @abs(w[1])) (if (w[0] > 0) .pos_x else .neg_x) else (if (w[1] > 0) .pos_z else .neg_z);

        b.solid(.{ .ramp = .{ .min = mn, .max = mx, .rise = rise } });
    }
}

fn put(b: *Builder, kind: K, x: f32, z: f32, yaw: f32) void {
    b.put(kit.of(kind), x, z, yaw, 1);
}

fn putS(b: *Builder, kind: K, x: f32, z: f32, yaw: f32, s: f32) void {
    b.put(kit.of(kind), x, z, yaw, s);
}

fn at(b: *Builder, kind: K, x: f32, y: f32, z: f32, yaw: f32) void {
    b.putAt(kit.of(kind), vec(x, y, z), yaw, 1);
}

fn line(b: *Builder, kind: K, x0: f32, z0: f32, x1: f32, z1: f32, step: f32) void {
    const dx = x1 - x0;
    const dz = z1 - z0;
    const len = @sqrt(dx * dx + dz * dz);
    const n: u32 = @intFromFloat(@max(1, @round(len / step)));
    const yaw = -std.math.atan2(dz, dx);
    var i: u32 = 0;

    while (i < n) : (i += 1) {
        const q = (@as(f32, @floatFromInt(i)) + 0.5) / @as(f32, @floatFromInt(n));

        put(b, kind, x0 + dx * q, z0 + dz * q, yaw);
    }
}

fn boxSolids(kind: K) []const [7]f32 {
    return switch (kind) {
        .box_red => &S.box_red,
        .box_blue => &S.box_blue,
        .box_green => &S.box_green,
        else => &S.box_office,
    };
}

fn stackAt(b: *Builder, st: Stack) void {
    var i: u8 = 0;

    while (i < st.n) : (i += 1) {
        const fi: f32 = @floatFromInt(i);
        const y = t.height(st.x, st.z) + fi * 2.59;
        const wob = if (i > 0) b.rng.range(-0.03, 0.03) else 0;

        structure(b, st.kind, boxSolids(st.kind), st.x, y, st.z, st.yaw + wob);
    }
}

fn perimeter(b: *Builder) void {
    const e = edge;
    var x: f32 = -e + 2;

    while (x < e - 1) : (x += 4) {
        if (!(x > -30 and x < -10)) put(b, if (@mod(x + 200, 56) < 20) .fence else .hoarding, x, -e, 0);

        put(b, if (@mod(x + 200, 64) < 16) .fence else .hoarding, x, e, pi);
        put(b, if (@mod(x + 212, 40) < 16) .fence else .hoarding, -e, x, half_pi);
        put(b, .hoarding, e, x, -half_pi);
    }

    put(b, .lights, -30, -e + 3, 0);
    put(b, .lights, -10, -e + 3, pi);
    put(b, .sign, -33, -e + 1.2, 0);
    put(b, .sign, -7, -e + 1.2, 0);
    put(b, .lights, -26, -128, 0);
    put(b, .lights, -14, -124, pi);
    put(b, .sign, -27, -118, 0.25);
    structure(b, .cabins, &S.cabins, -42, 0, -134, half_pi);

    var c: f32 = -146;

    while (c < -110) : (c += 3.2) {
        put(b, .cone, -26.5, c, 0);
        put(b, .cone, -13.5, c + 1.6, 0);
    }
}

fn city(b: *Builder) void {
    const kinds = [_]K{ .city_slab, .city_office, .city_prewar, .city_deco, .city_office, .city_prewar, .city_slab, .city_office };
    var i: u32 = 0;

    while (i < 72) : (i += 1) {
        const fi: f32 = @floatFromInt(i);
        const ring: f32 = @floatFromInt(i % 3);
        const ang = fi / 72 * std.math.tau + b.rng.range(-0.03, 0.03);
        const r = 212 + ring * 30 + b.rng.range(-6, 10);
        const kind = kinds[(i * 5 + i / 3) % kinds.len];
        const x = @sin(ang) * r;
        const z = @cos(ang) * r;
        const near = ring < 0.5;

        b.putAt(kit.of(kind), vec(x, -7.6, z), -ang + pi + (if (near) @as(f32, 0) else b.rng.range(-0.3, 0.3)), b.rng.range(0.75, 1.2) * (if (near) @as(f32, 0.8) else 1.1));
    }
}

fn core(b: *Builder) void {
    const tx = tower_at[0];
    const tz = tower_at[1];
    const F = [_]f32{ 0.3, 3.9, 7.5, 11.1, 14.7 };

    structure(b, .tower, &S.tower, tx, 0, tz, 0);
    structure(b, .crane, &S.crane, 22, 0, -12, 0.8);

    at(b, .pallet, tx - 6, F[0], tz + 6, 0);
    at(b, .pallet, tx - 4.6, F[0], tz + 6, 0.1);
    at(b, .bag, tx - 8, F[0], tz - 2, 0.4);
    at(b, .mixer, tx + 1.5, F[0], tz - 6.5, 1.2);
    at(b, .scafstack, tx - 6, F[0], tz + 1.5, 0);
    at(b, .drums, tx + 2.5, F[0], tz + 3, 0);
    at(b, .spool, tx - 9, F[0], tz + 7, 0.3);
    at(b, .pallet, tx - 9, F[1], tz + 6.5, 0);
    at(b, .pallet, tx - 9, F[1], tz + 5.2, 0);
    at(b, .bag, tx + 1.5, F[1], tz - 3, 0);
    at(b, .scafstack, tx - 2, F[1], tz + 7.8, 0);
    at(b, .genset, tx - 6, F[1], tz - 1, half_pi);
    at(b, .timber, tx + 1, F[1], tz + 1.5, 0);
    at(b, .pallet, tx + 2, F[2], tz + 2, 0.2);
    at(b, .precast, tx - 6, F[2], tz + 4, 0);
    at(b, .bag, tx - 10, F[2], tz + 7, 0.3);
    at(b, .vault, tx - 4, F[2], tz - 3.5, 0);
    at(b, .drums, tx + 3, F[2], tz - 6.5, 0);
    at(b, .pallet, tx - 10, F[3], tz - 2, 0);
    at(b, .scafstack, tx + 0.5, F[3], tz + 2.5, half_pi);
    at(b, .mixer, tx - 5, F[3], tz + 7, 0.8);
    at(b, .bag, tx - 1, F[3], tz - 7.5, 0);
    at(b, .spool, tx + 3, F[3], tz - 3, 1.2);
    at(b, .rebar, tx - 7, F[4], tz + 4, 0);
    at(b, .rebar, tx - 3.5, F[4], tz + 4, 0);
    at(b, .formwork, tx - 6, F[4], tz - 2, 0);
    at(b, .pallet, tx - 10, F[4], tz - 6, 0);
    at(b, .bag, tx - 10.5, F[4], tz + 7.5, 0);
    at(b, .timber, tx + 7, F[4], tz - 5, 0);

    put(b, .genset, tx + 20, tz + 14, half_pi);
    put(b, .scafstack, tx + 20, tz + 26, half_pi);
    put(b, .rebar, tx - 22, tz + 22, 0);
    put(b, .lamp, tx + 15, tz + 2, 0);
    put(b, .lamp, tx - 20, tz - 14, 0.4);
    put(b, .lamp, tx + 26, tz + 30, 2.3);
    put(b, .genset, tx + 15, tz - 8, 0);
    put(b, .genset, tx - 18, tz + 28, 0.3);
    put(b, .silo, tx + 30, tz - 4, 0);

    var i: u32 = 0;

    while (i < 4) : (i += 1) {
        const fi: f32 = @floatFromInt(i);

        put(b, .precast, tx - 24, tz - 4 + fi * 2.2, half_pi);
        put(b, .scafstack, tx - 28, tz - 4 + fi * 2.2, half_pi);
    }

    put(b, .rebar, tx + 24, tz + 4, 0);
    put(b, .rebar, tx + 26.5, tz + 4, 0.1);
    put(b, .skip, tx - 8, tz - 14, 0);
    put(b, .bag, tx - 4, tz - 13, 0);
    put(b, .bag, tx - 2.8, tz - 13.6, 0.4);
    put(b, .pipes, tx + 8, tz - 16, 0);
    put(b, .blocks, tx - 16, tz - 20, 0);
    put(b, .blocks, tx + 2, tz - 22, 0);
    put(b, .blocks, tx + 16, tz - 20, 0);
    put(b, .blocks, tx - 30, tz + 12, half_pi);
    put(b, .blocks, tx + 34, tz + 18, half_pi);
    put(b, .timber, tx - 30, tz + 24, half_pi);
    put(b, .spool, tx + 30, tz + 8, 0.6);
    put(b, .spool, tx + 31.6, tz + 9.2, 1.9);

    line(b, .barrier, -38, 36, -6, 36, 4);
    line(b, .barrier, 6, 36, 38, 36, 4);
    line(b, .fence, 38, -38, 38, -4, 4);
    line(b, .fence, 38, 10, 38, 34, 4);
}

fn pitSite(b: *Builder) void {
    var x: f32 = pit[0] + 4;

    while (x < pit[2] - 3) : (x += 8) {
        structure(b, .pilewall, &S.pilewall, x, 0, pit[3] - 2.25, pi);
    }

    x = pit[0] + 2;

    while (x < pit[2] - 2) : (x += 3.4) {
        b.putAt(kit.of(.tplate), vec(x, 0.02, pit[3] - 1.2), 0, 1.4);
    }

    b.solid(.{ .box = .{ .min = vec(pit[0], -0.6, pit[3] - 2.4), .max = vec(pit[2], 0.05, pit[3] + 0.2) } });

    x = pit[0] + 2;

    while (x < pit[2] - 2) : (x += 4.2) {
        if (@mod(x, 16.8) < 4) continue;

        put(b, .barrier, x, pit[3] + 1.4, 0);
    }

    const fy = pit_floor;
    const cx: f32 = 89;
    const cz: f32 = -80;
    var i: i32 = -2;

    while (i <= 2) : (i += 1) {
        const fi: f32 = @floatFromInt(i);

        at(b, .core, cx - 12, fy, cz + fi * 4.2, half_pi);
        at(b, .formwork, cx + 12, fy, cz + fi * 4.1, -half_pi);
        at(b, .rebar, cx + fi * 4, fy, cz - 10, 0);
        at(b, .rebar, cx + fi * 4 + 1, fy, cz + 11, 0.2);
    }

    at(b, .core, cx - 4, fy, cz + 2, 0);
    at(b, .core, cx + 4, fy, cz - 2, 0);
    at(b, .spool, cx - 18, fy, cz - 16, 0.05);
    at(b, .skip, cx + 2, fy, cz - 22, half_pi);
    at(b, .skip, cx + 22, fy, cz - 20, 0);
    at(b, .genset, cx + 20, fy, cz + 18, half_pi + 0.05);
    at(b, .pallet, cx + 8, fy, cz + 18, 0);
    at(b, .bag, cx - 14, fy, cz + 17, 0.3);
    at(b, .bag, cx - 12.8, fy, cz + 17.6, 0.9);
    at(b, .pipes, cx - 4, fy, cz + 18, 0);
    at(b, .pipes, cx + 2, fy, cz - 15, half_pi);
    at(b, .drums, cx - 8, fy, cz - 8, 0);
    at(b, .lamp, cx + 24, fy, cz - 24, 0.6);
    at(b, .scafstack, cx + 4, fy, cz + 22, 0);
    b.putAt(kit.of(.spoil), vec(cx + 22, fy, cz + 2), 0.4, 2.4);
    b.putAt(kit.of(.spoil), vec(cx - 22, fy, cz + 14), 1.4, 2.0);

    put(b, .drums, pit[2] + 14, -70, 0);
    put(b, .genset, pit[0] - 8, -60, 0);
    put(b, .scafstack, pit[0] - 8, -98, 0);
    put(b, .lamp, pit[0] - 5, pit[3] + 6, 0.7);
    line(b, .fence, pit[0] - 3, pit[1] - 3, pit[0] - 3, ramp_z[0] - 4, 4);
    line(b, .fence, pit[0] - 3, ramp_z[1] + 4, pit[0] - 3, pit[3] - 3, 4);
    line(b, .fence, pit[2] + 3, pit[1] - 3, pit[2] + 3, pit[3] - 3, 4);
    line(b, .fence, pit[0] - 3, pit[1] - 3, pit[2] + 3, pit[1] - 3, 4);
    line(b, .barrier, ramp_x[0], ramp_z[0] - 3.5, ramp_x[1] - 6, ramp_z[0] - 3.5, 4);
    line(b, .barrier, ramp_x[0], ramp_z[1] + 3.5, ramp_x[1] - 6, ramp_z[1] + 3.5, 4);
}

fn frameSite(b: *Builder) void {
    const fx = frame_at[0];
    const fz = frame_at[1];

    structure(b, .frame, &S.frame, fx, 0, fz, 0);
    at(b, .pallet, fx + 6, 3.6, fz + 1, 0);
    at(b, .scafstack, fx + 10, 3.6, fz + 6, half_pi);
    at(b, .vault, fx + 2, 3.6, fz + 6, 0);
    at(b, .bag, fx + 13, 7.2, fz + 2, 0);
    at(b, .pallet, fx + 6, 7.2, fz + 5, 0.3);
    at(b, .genset, fx + 9, 0, fz + 5, 0);
    at(b, .precast, fx + 4, 0, fz + 9, 0);
    at(b, .drums, fx + 14, 0, fz + 1, 0);
    put(b, .rebar, fx + 24, fz + 4, half_pi);
    put(b, .precast, fx + 6, fz - 12, half_pi);
    put(b, .precast, fx + 16, fz - 9, 0);
    put(b, .precast, fx + 16, fz - 11, 0);
    put(b, .lamp, fx + 22, fz + 16, 4);
    put(b, .timber, fx - 6, fz + 14, half_pi);
    put(b, .spool, fx - 6, fz + 4, 0);
}

fn tower2Site(b: *Builder) void {
    const tx = tower2_at[0];
    const tz = tower2_at[1];
    const F = [_]f32{ 0.3, 3.9, 7.5, 11.1 };

    structure(b, .tower2, &S.tower2, tx, 0, tz, 0);
    at(b, .pallet, tx + 3, F[0], tz + 3, 0);
    at(b, .drums, tx - 2, F[0], tz - 1, 0);
    at(b, .scafstack, tx + 3, F[1], tz - 3, 0);
    at(b, .bag, tx - 6, F[1], tz + 4, 0);
    at(b, .timber, tx + 4, F[2], tz + 2, half_pi);
    at(b, .mixer, tx - 5, F[2], tz - 2, 0.6);
    at(b, .rebar, tx - 5, F[3], tz + 3, 0);
    at(b, .bag, tx + 5, F[3], tz - 3, 0);
}

fn extras(b: *Builder) void {
    structure(b, .tower2, &S.tower2, 120, 0, 62, half_pi);
    at(b, .pallet, 118, 0.3, 60, 0);
    at(b, .drums, 122, 3.9, 64, 0);
    at(b, .timber, 120, 7.5, 58, 0);
    at(b, .rebar, 121, 11.1, 66, 0);
    structure(b, .cabins, &S.cabins, 10, 0, -132, 0);
    line(b, .hoarding, -40, -56, -22, -56, 4);
    line(b, .hoarding, -18, -56, 0, -56, 4);
    line(b, .hoarding, 12, -56, 38, -56, 4);
    line(b, .hoarding, -56, -36, -56, -8, 4);
    line(b, .hoarding, -56, 8, -56, 34, 4);
    line(b, .hoarding, 56, -30, 56, -8, 4);
    line(b, .hoarding, 56, 8, 56, 30, 4);
    line(b, .hoarding, -36, 52, -12, 52, 4);
    line(b, .hoarding, 12, 52, 36, 52, 4);
    line(b, .fence, -90, -60, -60, -60, 4);
    line(b, .fence, 70, -10, 90, -10, 4);
    line(b, .hoarding, -60, 88, -30, 88, 4);
    line(b, .hoarding, 30, 70, 30, 86, 4);
}

fn compound(b: *Builder) void {
    structure(b, .cabins, &S.cabins, -124, 0, 120, pi);
    structure(b, .cabins, &S.cabins, -89, 0, 120, pi);

    var i: u32 = 0;

    while (i < 5) : (i += 1) {
        const fi: f32 = @floatFromInt(i);

        put(b, .toilet, -142 + fi * 1.4, 104, 0);
    }

    put(b, .shelter, -140, 128, half_pi);
    put(b, .genset, -104, 136, 0);
    put(b, .vault, -108, 108, 0);
    put(b, .vault, -105.6, 108, 0);
    put(b, .lamp, -100, 104, 1.2);
    put(b, .lamp, -142, 142, 2.0);
    put(b, .precast, -120, 98, half_pi + 0.04);
    put(b, .drums, -84, 108, 0.3);
    put(b, .drums, -80, 104, 1.1);
    put(b, .skip, -86, 140, 0);
    put(b, .skip, -82, 140, 0);
    put(b, .sign, -100, 96, 0);
    put(b, .drums, -112, 104, 0);
    line(b, .fence, -146, 92, -104, 92, 4);
    line(b, .fence, -88, 92, -72, 92, 4);
    line(b, .fence, -72, 92, -72, 146, 4);
}

fn containerYard(b: *Builder) void {
    for (stacks) |st| stackAt(b, st);

    put(b, .pipes, -126, -24, half_pi);
    put(b, .precast, -108, 26, 0);
    put(b, .lamp, -96, -46, 0.3);
    put(b, .drums, -126, 12, 0);
    put(b, .drums, -110, -2, 0.4);
    put(b, .spool, -98, 4, 0.2);
    put(b, .pallet, -126, -4, 0);
    put(b, .pallet, -124.6, -4.2, 0.1);
    put(b, .blocks, -94, -20, half_pi);
    put(b, .blocks, -94, 26, half_pi);
    put(b, .timber, -112, 30, 0);
    line(b, .fence, -146, -54, -96, -54, 4);
    line(b, .fence, -146, 36, -110, 36, 4);
}

fn laydown(b: *Builder) void {
    var row: f32 = -140;
    var r: u32 = 0;

    while (row < -70) : (row += 14) {
        var x: f32 = -142;
        var c: u32 = 0;

        while (x < -64) : (x += 6.5) {
            const pick = (r * 7 + c * 3) % 10;
            const z = row + 6;

            switch (pick) {
                0, 1 => {
                    put(b, .precast, x, z, 0);
                    b.putAt(kit.of(.precast), vec(x, t.height(x, z) + 0.9, z), 0.03, 1);
                },
                2 => {
                    put(b, .scafstack, x, z, 0);
                    put(b, .scafstack, x, z + 2, 0);
                },
                3 => {
                    put(b, .rebar, x - 1, z, 0);
                    put(b, .rebar, x + 1.2, z, 0.1);
                },
                4 => {
                    put(b, .pallet, x - 1, z, 0);
                    put(b, .pallet, x + 0.4, z, 0);
                    put(b, .pallet, x - 0.3, z + 1.3, half_pi);
                    put(b, .bag, x + 1.5, z + 2, 0.4);
                },
                5 => put(b, .pipes, x, z, 0),
                6 => {
                    put(b, .bag, x - 1, z, 0.1);
                    put(b, .bag, x, z + 0.2, 0.5);
                    put(b, .bag, x + 1, z, 0.9);
                    put(b, .drums, x, z + 2.2, 0);
                },
                7 => put(b, .timber, x, z, 0),
                8 => {
                    put(b, .spool, x - 0.8, z, 0);
                    put(b, .spool, x + 0.8, z, 0.3);
                },
                else => put(b, .skip, x, z, 0),
            }

            c += 1;
        }

        r += 1;
    }

    put(b, .rebar, -96, -110, half_pi);
    put(b, .precast, -130, -72, half_pi);
    put(b, .lamp, -66, -72, 0.3);
    put(b, .lamp, -142, -144, 1);
    line(b, .fence, -146, -64, -70, -64, 4);
}

fn earthworks(b: *Builder) void {
    const heaps = [_][4]f32{
        .{ 128, -134, 4.6, 0.3 },
        .{ 140, -116, 3.6, 1.2 },
        .{ 108, -132, 3.2, 2.5 },
        .{ 84, -136, 4.0, 0.8 },
        .{ 136, -92, 3.0, 2.0 },
        .{ 60, -136, 3.4, 1.6 },
        .{ 30, -132, 3.0, 0.4 },
        .{ 136, 136, 4.0, 2.2 },
        .{ 118, 140, 3.0, 0.5 },
    };

    for (heaps) |h| putS(b, .spoil, h[0], h[1], h[3], h[2]);

    put(b, .timber, 116, -118, 0.4);
    put(b, .blocks, 96, -120, half_pi);
    put(b, .pipes, 136, -66, 0);
    put(b, .pipes, 46, -126, 0);
    put(b, .lamp, 142, -100, 4);

    const muds = [_][3]f32{ .{ 112, -124, 0 }, .{ 116, -124, 0 }, .{ 120, -124, 0 }, .{ 104, -128, 0.1 }, .{ -20, -110, 0 }, .{ -20, -106, 0 }, .{ -20, -86, 0 }, .{ 44, -60, 0 }, .{ 40, -80, 0 } };

    for (muds) |m| b.putAt(kit.of(.mud), vec(m[0], t.height(m[0], m[1]) + 0.01, m[1]), m[2], 1);
}

fn plantYard(b: *Builder) void {
    const rows = [_]struct { kind: K, x: f32, z: f32, yaw: f32 }{
        .{ .kind = .spool, .x = 104, .z = -30, .yaw = 0 },
        .{ .kind = .pipes, .x = 112, .z = -30, .yaw = 0 },
        .{ .kind = .timber, .x = 120, .z = -30, .yaw = 0 },
        .{ .kind = .blocks, .x = 128, .z = -30, .yaw = 0 },
        .{ .kind = .skip, .x = 135, .z = -30, .yaw = 0 },
        .{ .kind = .genset, .x = 104, .z = 22, .yaw = pi },
        .{ .kind = .pipes, .x = 113, .z = 22, .yaw = pi },
        .{ .kind = .rebar, .x = 122, .z = 22, .yaw = pi },
        .{ .kind = .precast, .x = 131, .z = 22, .yaw = pi },
    };

    for (rows) |r| put(b, r.kind, r.x, r.z, r.yaw);

    put(b, .drums, 96, -12, half_pi);
    put(b, .genset, 96, 12, half_pi);
    put(b, .genset, 140, -12, half_pi);
    put(b, .drums, 140, 12, 0);
    put(b, .lamp, 100, 0, 1);
    put(b, .shelter, 140, 36, -half_pi);
    line(b, .fence, 92, -40, 146, -40, 4);
    line(b, .fence, 92, 34, 120, 34, 4);
}

fn northSide(b: *Builder) void {
    var i: u32 = 0;

    while (i < 6) : (i += 1) {
        const fi: f32 = @floatFromInt(i);

        put(b, .core, -30 + fi * 4.2, 100, 0);
        put(b, .formwork, -30 + fi * 4.2, 114, 0);
        put(b, .core, -6, 98 + fi * 4.2, half_pi);
    }

    put(b, .rebar, -22, 107, 0);
    put(b, .rebar, -14, 107, 0.3);
    put(b, .mixer, -18, 106, 0.6);
    put(b, .drums, 18, 112, 0);
    put(b, .pipes, 30, 92, half_pi);
    put(b, .blocks, 52, 104, 0);
    put(b, .pipes, 26, 132, half_pi);
    put(b, .pipes, 30, 132, half_pi);
    put(b, .lamp, -36, 92, 0.2);
    put(b, .shelter, -40, 136, half_pi);
    put(b, .toilet, -40, 142, 0);
    put(b, .toilet, -38.6, 142, 0);
    put(b, .blocks, 10, 90, 0);
    put(b, .blocks, -14, 128, 0);
    put(b, .blocks, 60, 124, half_pi);

    put(b, .silo, 104, 112, 0);
    put(b, .silo, 108, 112, 0);
    put(b, .silo, 112, 112, 0);
    put(b, .scafstack, 96, 96, 0);
    put(b, .scafstack, 120, 96, 0.04);
    put(b, .drums, 124, 128, 0.4);
    put(b, .mixer, 92, 124, 1.4);
    put(b, .mixer, 94, 126, 0.2);
    put(b, .pallet, 88, 130, 0);
    put(b, .pallet, 89.4, 130, 0);
    put(b, .pipes, 136, 116, half_pi);
    put(b, .skip, 80, 140, 0);
    put(b, .skip, 84, 140, 0);
    put(b, .genset, 96, 140, 0);
    line(b, .fence, 76, 86, 146, 86, 4);
}

fn westCenter(b: *Builder) void {
    put(b, .pipes, -60, -20, 0);
    put(b, .pipes, -60, -16, 0);
    put(b, .pipes, -66, -18, half_pi);
    put(b, .spool, -72, 10, 0);
    put(b, .spool, -74, 12, 1.0);
    put(b, .spool, -70, 13, 2.0);
    put(b, .timber, -58, 16, 0);
    put(b, .timber, -58, 19, 0);
    put(b, .blocks, -66, 26, 0);
    put(b, .blocks, -80, -30, half_pi);
    put(b, .blocks, -54, -34, 0);
    put(b, .skip, -80, 18, half_pi);
    put(b, .skip, -70, -4, 0.3);
    put(b, .lamp, -54, 6, 0.6);
    put(b, .drums, -86, -12, 0);
    put(b, .scafstack, -64, 40, half_pi);
    put(b, .scafstack, -84, 40, 0);
    put(b, .scafstack, -84, 42, 0);
    put(b, .precast, -40, 74, 0.6);
    put(b, .rebar, -88, 70, 0);
    put(b, .spool, -56, 80, 0.4);
    put(b, .pipes, -52, 66, half_pi);
}

fn roadside(b: *Builder) void {
    var z: f32 = -110;

    while (z < -50) : (z += 4) {
        if (@mod(z, 24) < 6) continue;

        put(b, .barrier, -27, z, half_pi);
    }

    put(b, .lights, -16, -48, 0);
    put(b, .lights, -12, -40, 0.4);
    put(b, .sign, -27, -52, half_pi);
    put(b, .precast, -14, -90, 0);
    put(b, .lamp, -12, -70, 1.0);
    put(b, .skip, 10, -54, 0);
    put(b, .bag, 15, -55, 0.3);
    put(b, .bag, 16.2, -54.4, 1.1);
    put(b, .genset, 28, -56, 0);
    put(b, .drums, 4, -60, 0);
    put(b, .blocks, -6, -64, 0);
    put(b, .blocks, 22, -68, half_pi);
    put(b, .spool, 32, -60, 0.4);

    var c: f32 = -40;

    while (c < 42) : (c += 5) {
        put(b, .cone, c, -48.5, 0);
    }
}

const reserved = [_]Rect{
    .{ .x0 = -32, .z0 = -16, .x1 = 40, .z1 = 38 },
    .{ .x0 = -90, .z0 = 44, .x1 = -52, .z1 = 80 },
    .{ .x0 = 46, .z0 = 38, .x1 = 92, .z1 = 70 },
    .{ .x0 = 50, .z0 = -116, .x1 = 126, .z1 = -40 },
    .{ .x0 = 18, .z0 = -92, .x1 = 62, .z1 = -68 },
    .{ .x0 = -148, .z0 = 90, .x1 = -70, .z1 = 148 },
    .{ .x0 = -148, .z0 = -56, .x1 = -92, .z1 = 38 },
    .{ .x0 = -148, .z0 = -148, .x1 = -60, .z1 = -62 },
    .{ .x0 = 92, .z0 = -42, .x1 = 148, .z1 = 40 },
    .{ .x0 = 74, .z0 = 84, .x1 = 148, .z1 = 148 },
    .{ .x0 = -36, .z0 = 88, .x1 = 4, .z1 = 124 },
    .{ .x0 = -50, .z0 = -148, .x1 = 8, .z1 = -112 },
    .{ .x0 = 22, .z0 = -148, .x1 = 148, .z1 = -110 },
    .{ .x0 = 106, .z0 = 50, .x1 = 134, .z1 = 76 },
    .{ .x0 = -2, .z0 = -142, .x1 = 22, .z1 = -122 },
};

fn free(x: f32, z: f32, r: f32) bool {
    if (@abs(x) > edge - 6 or @abs(z) > edge - 6) return false;

    if (roadDist(x, z) < 7 + r) return false;

    for (reserved) |q| {
        if (x > q.x0 - r and x < q.x1 + r and z > q.z0 - r and z < q.z1 + r) return false;
    }

    return true;
}

fn cluster(b: *Builder, x: f32, z: f32) void {
    const yaw = @as(f32, @floatFromInt(@as(u32, @intFromFloat(b.rng.range(0, 3.99))))) * half_pi;
    const kind = @as(u32, @intFromFloat(b.rng.range(0, 7.99)));
    const c = @cos(yaw);
    const s = @sin(yaw);
    const P = struct { k: K, x: f32, z: f32, y: f32 = 0 };
    const sets = [8][]const P{
        &.{ .{ .k = .pallet, .x = -1, .z = 0 }, .{ .k = .pallet, .x = 0.3, .z = 0 }, .{ .k = .pallet, .x = -0.4, .z = 1.2 }, .{ .k = .bag, .x = 1.6, .z = 0.8 }, .{ .k = .bag, .x = 2.0, .z = -0.5 }, .{ .k = .drums, .x = -2.6, .z = 0.4 } },
        &.{ .{ .k = .blocks, .x = 0, .z = 0 }, .{ .k = .spool, .x = 0.5, .z = 1.6 }, .{ .k = .drums, .x = -2.4, .z = 1.5 } },
        &.{ .{ .k = .timber, .x = 0, .z = 0 }, .{ .k = .timber, .x = 0, .z = 2.2 }, .{ .k = .scafstack, .x = 0, .z = -1.8 }, .{ .k = .bag, .x = 2.8, .z = 1 } },
        &.{ .{ .k = .skip, .x = 0, .z = 0 }, .{ .k = .bag, .x = 2.6, .z = 0.2 }, .{ .k = .bag, .x = 2.4, .z = 1.3 }, .{ .k = .cone, .x = -2.6, .z = 1.2 }, .{ .k = .cone, .x = -2.2, .z = -1.2 } },
        &.{ .{ .k = .pipes, .x = 0, .z = 0 }, .{ .k = .pipes, .x = 0, .z = 2.6 }, .{ .k = .spool, .x = 2.8, .z = 1.2 } },
        &.{ .{ .k = .precast, .x = 0, .z = 0 }, .{ .k = .precast, .x = 0, .z = 0, .y = 0.9 }, .{ .k = .precast, .x = 0, .z = 1.8 }, .{ .k = .rebar, .x = 3.2, .z = 0.8 } },
        &.{ .{ .k = .box_blue, .x = 0, .z = 0 }, .{ .k = .drums, .x = 0, .z = 2.4 }, .{ .k = .pallet, .x = 2, .z = 2.2 }, .{ .k = .blocks, .x = -1, .z = -2.4 } },
        &.{ .{ .k = .genset, .x = 0, .z = 0 }, .{ .k = .vault, .x = 0, .z = 1.4 }, .{ .k = .lamp, .x = 2.6, .z = 0.4 }, .{ .k = .spool, .x = -2.4, .z = 0.6 } },
    };

    for (sets[kind]) |p| {
        const wx = x + p.x * c + p.z * s;
        const wz = z - p.x * s + p.z * c;

        if (p.k == .box_blue) {
            structure(b, .box_blue, &S.box_blue, wx, t.height(wx, wz), wz, yaw);

            continue;
        }

        b.putAt(kit.of(p.k), vec(wx, t.height(wx, wz) + p.y, wz), yaw + b.rng.range(-0.05, 0.05), 1);
    }
}

fn clutter(b: *Builder) void {
    var gx: f32 = -140;

    while (gx < 140) : (gx += 8.5) {
        var gz: f32 = -140;

        while (gz < 140) : (gz += 8.5) {
            const x = gx + b.rng.range(-3, 3);
            const z = gz + b.rng.range(-3, 3);

            if (!free(x, z, 3.5)) continue;

            if (moundAt(x, z).h > 0.1 or moundAt(x + 4, z).h > 0.1 or moundAt(x - 4, z).h > 0.1) continue;

            if (b.rng.next() < 0.12) continue;

            cluster(b, x, z);
        }
    }
}

fn decals(b: *Builder) void {
    for (roads) |r| {
        const dx = r[2] - r[0];
        const dz = r[3] - r[1];
        const len = @sqrt(dx * dx + dz * dz);
        const yaw = std.math.atan2(dx, dz);
        var d: f32 = 4;

        while (d < len - 4) : (d += 8) {
            if (b.rng.next() < 0.3) continue;

            const q = d / len;
            const off = b.rng.range(-1.2, 1.2);
            const x = r[0] + dx * q + dz / len * off;
            const z = r[1] + dz * q - dx / len * off;

            b.putAt(kit.of(.tracks), vec(x, t.height(x, z), z), yaw + b.rng.range(-0.08, 0.08), 1);
        }
    }

    var i: u32 = 0;

    while (i < 220) : (i += 1) {
        const x = b.rng.range(-142, 142);
        const z = b.rng.range(-142, 142);
        const near = roadDist(x, z) < 9;
        const kind: K = if (near and b.rng.next() < 0.6) .puddle else if (b.rng.next() < 0.55) .gravel else .puddle;

        if (t.height(x, z) < -0.3 and kind == .gravel) continue;

        if (moundAt(x, z).h > 0.1 or t.normal(x, z).y < 0.985 or t.normal(x + 2, z + 2).y < 0.985 or t.normal(x - 2, z - 2).y < 0.985) continue;

        b.putAt(kit.of(kind), vec(x, t.height(x, z), z), b.rng.range(0, 6.28), b.rng.range(0.7, 1.5));
    }
}

fn build(b: *Builder) void {
    perimeter(b);
    city(b);
    core(b);
    pitSite(b);
    frameSite(b);
    tower2Site(b);
    extras(b);
    compound(b);
    containerYard(b);
    laydown(b);
    earthworks(b);
    plantYard(b);
    northSide(b);
    westCenter(b);
    roadside(b);
    clutter(b);
    decals(b);
}

fn spots(gpa: std.mem.Allocator) void {
    api.world.autoSpots(gpa, .{ .loot = 48, .vehicles = 6 });
}
