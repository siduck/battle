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
};

const edge: f32 = api.arena_half - 3;
const gate_x: f32 = -44;
const tower_at = [2]f32{ 0, 8 };
const tower2_at = [2]f32{ -56, 56 };
const frame_at = [2]f32{ 42, 50 };
const pit = [4]f32{ 12, -64, 62, -18 };
const pit_c = [2]f32{ 37, -41 };
const pit_k: f32 = 0.75;
const pit_floor: f32 = -7.0;
const ramp_z = [2]f32{ -44, -32 };
const ramp_x = [2]f32{ -26, 16 };

const Rect = struct { x0: f32, z0: f32, x1: f32, z1: f32 };

const Stack = struct { x: f32, z: f32, yaw: f32, n: u8, kind: K };

const stacks = [_]Stack{
    .{ .x = -64, .z = -30, .yaw = 0, .n = 3, .kind = .box_green },
    .{ .x = -64, .z = -27.4, .yaw = 0, .n = 2, .kind = .box_blue },
    .{ .x = -64, .z = -16, .yaw = 0, .n = 2, .kind = .box_blue },
    .{ .x = -64, .z = -6, .yaw = 0, .n = 1, .kind = .box_red },
    .{ .x = -64, .z = -3.4, .yaw = 0, .n = 2, .kind = .box_green },
    .{ .x = -64, .z = 8, .yaw = 0, .n = 3, .kind = .box_red },
    .{ .x = -64, .z = 18, .yaw = 0, .n = 2, .kind = .box_green },
    .{ .x = -64, .z = 20.6, .yaw = 0, .n = 1, .kind = .box_blue },
    .{ .x = -55, .z = -22, .yaw = 0, .n = 3, .kind = .box_blue },
    .{ .x = -55, .z = -19.4, .yaw = 0, .n = 2, .kind = .box_red },
    .{ .x = -55, .z = 0, .yaw = 0, .n = 2, .kind = .box_green },
    .{ .x = -55, .z = 2.6, .yaw = 0, .n = 2, .kind = .box_blue },
    .{ .x = -55, .z = 26, .yaw = 0, .n = 1, .kind = .box_red },
};

const shade_rects = [_]Rect{
    .{ .x0 = -15, .z0 = -3, .x1 = 13, .z1 = 18 },
    .{ .x0 = -67, .z0 = 48, .x1 = -47, .z1 = 63 },
    .{ .x0 = 39.5, .z0 = 47.5, .x1 = 60.5, .z1 = 60.5 },
    .{ .x0 = -67.3, .z0 = -66, .x1 = -47.7, .z1 = -58 },
};

const Pad = struct { r: Rect, tone: u8 };

const max_pads = 160;
var pads: [max_pads]Pad = undefined;
var pad_n: usize = 0;

fn addPad(cx: f32, cz: f32, hx: f32, hz: f32, tone: u8) void {
    if (pad_n >= max_pads) return;

    pads[pad_n] = .{ .r = .{ .x0 = cx - hx, .z0 = cz - hz, .x1 = cx + hx, .z1 = cz + hz }, .tone = tone };
    pad_n += 1;
}

fn hash2(i: i32, j: i32) f32 {
    var h: u32 = @bitCast(i *% 374761393 +% j *% 668265263);

    h = (h ^ (h >> 13)) *% 1274126177;
    h ^= h >> 16;

    return @as(f32, @floatFromInt(h & 0xffff)) / 65535.0;
}

fn gravel(x: f32, z: f32, fine: f32) [3]f32 {
    const speck = t.fbm(x * 1.7 + 5, z * 1.7 - 3);
    const base = mixc(.{ 142, 130, 112 }, .{ 124, 112, 96 }, fine);

    return mixc(mixc(base, .{ 172, 158, 136 }, t.smooth(0.62, 0.72, speck)), .{ 98, 86, 72 }, t.smooth(0.3, 0.2, speck) * 0.8);
}

fn hardcore(x: f32, z: f32, fine: f32) [3]f32 {
    const speck = t.fbm(x * 2.3 - 8, z * 2.3 + 1);
    const base = mixc(.{ 110, 96, 80 }, .{ 98, 85, 71 }, fine);

    return mixc(base, .{ 156, 140, 118 }, t.smooth(0.64, 0.74, speck) * 0.9);
}

fn padTone(tone: u8, x: f32, z: f32, fine: f32) [3]f32 {
    return switch (tone) {
        0 => pad(x, z, fine),
        1 => gravel(x, z, fine),
        2 => hardcore(x, z, fine),
        else => mixc(.{ 190, 168, 120 }, .{ 172, 150, 106 }, fine),
    };
}

fn zoneColor(x: f32, z: f32, fine: f32) [3]f32 {
    const wx = x + (t.fbm(x * 0.05 + 3, z * 0.05) - 0.5) * 14;
    const wz = z + (t.fbm(x * 0.05 - 9, z * 0.05 + 4) - 0.5) * 14;
    const cell: f32 = 23;
    const i: i32 = @intFromFloat(@floor(wx / cell));
    const j: i32 = @intFromFloat(@floor(wz / cell));
    const fx = wx / cell - @floor(wx / cell);
    const fz = wz / cell - @floor(wz / cell);
    const edge_d = @min(@min(fx, 1 - fx), @min(fz, 1 - fz)) * cell;
    const pick = hash2(i, j);
    const dry = mixc(.{ 156, 134, 104 }, .{ 140, 120, 94 }, fine);
    const damp = mixc(.{ 112, 94, 74 }, .{ 100, 84, 66 }, fine);
    const zone: [3]f32 = if (pick < 0.3) dry else if (pick < 0.52) damp else if (pick < 0.72) gravel(x, z, fine) else if (pick < 0.86) hardcore(x, z, fine) else mixc(.{ 176, 156, 116 }, .{ 160, 140, 104 }, fine);
    const blend = t.smooth(0, 3.5, edge_d);

    return mixc(mixc(dry, damp, 0.5), zone, 0.35 + 0.65 * blend);
}

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
    .{ .x = 60, .z = 2, .r = 9, .h = 3.6, .tone = 1 },
    .{ .x = -8, .z = 62, .r = 7, .h = 2.6, .tone = 2 },
    .{ .x = -22, .z = -58, .r = 7, .h = 2.8, .tone = 0 },
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
    const bund = t.smooth(t.play, t.half, box) * (6 + t.fbm(x * 0.05, z * 0.05) * 5);
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

    if (joint) return .{ 143, 134, 121 };

    return mixc(mixc(.{ 173, 163, 147 }, .{ 162, 152, 137 }, fine), .{ 145, 133, 117 }, stain * 0.7);
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

        if (@abs(p.pos.x) > t.half or @abs(p.pos.z) > t.half) continue;

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
    var c: [3]f32 = zoneColor(x, z, fine);

    c = mixc(c, .{ 144, 128, 106 }, t.smooth(0.45, 0.7, patch) * 0.35);
    c = mixc(c, .{ 92, 76, 60 }, t.smooth(0.52, 0.7, blot) * 0.5);
    c = mixc(c, .{ 84, 74, 64 }, t.smooth(0.55, 0.72, grit) * 0.4);
    c = mixc(c, .{ 166, 148, 122 }, t.smooth(0.6, 0.75, t.fbm(x * 0.6 - 9, z * 0.6 + 4)) * 0.3);

    const puddle = t.smooth(0.68, 0.72, t.fbm(x * 0.06 + 70, z * 0.06 - 30));

    c = mixc(c, .{ 70, 74, 80 }, puddle * 0.9);

    const road = roadDist(x, z);

    if (road < 6.5) {
        const lane = @abs(road - 2.4);

        c = mixc(c, .{ 112, 98, 80 }, 1 - t.smooth(4.5, 6.5, road));
        c = mixc(c, .{ 92, 79, 65 }, (1 - t.smooth(0.3, 0.8, lane)) * 0.7);
    }

    if (inRect(x, z, -32, -16, 30, 34) or inRect(x, z, -72, 42, -42, 70) or inRect(x, z, 34, 42, 68, 66)) c = pad(x, z, fine);

    if (inRect(x, z, -70, -34, -50, 32)) c = mixc(.{ 152, 142, 127 }, .{ 138, 129, 115 }, fine);

    for (pads[0..pad_n]) |pd| {
        if (inRect(x, z, pd.r.x0, pd.r.z0, pd.r.x1, pd.r.z1)) c = padTone(pd.tone, x, z, fine);
    }

    if (h < -0.3) {
        const wet = t.smooth(0.55, 0.7, t.fbm(x * 0.09, z * 0.09));

        c = mixc(.{ 120, 96, 72 }, .{ 96, 78, 60 }, wet);

        if (h < pit_floor + 0.2 and inRect(x, z, pit_c[0] - 11, pit_c[1] - 10.5, pit_c[0] + 11, pit_c[1] + 10.5)) c = pad(x, z, fine);
    }

    if (slope > 0.12) c = mixc(c, .{ 124, 98, 74 }, t.smooth(0.12, 0.35, slope));

    const md = moundAt(x, z);

    if (md.h > 0.15) {
        const tones = [3][3]f32{ .{ 112, 86, 62 }, .{ 176, 156, 116 }, .{ 140, 128, 112 } };
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
    .{ gate_x, -edge, gate_x, 40 },
    .{ gate_x, 40, 44, 40 },
    .{ 44, 40, 44, -8 },
    .{ gate_x, (ramp_z[0] + ramp_z[1]) * 0.5, ramp_x[0], (ramp_z[0] + ramp_z[1]) * 0.5 },
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

fn run(b: *Builder, kind: K, x0: f32, z0: f32, x1: f32, z1: f32) void {
    const dx = x1 - x0;
    const dz = z1 - z0;
    const len = @sqrt(dx * dx + dz * dz);
    const n: u32 = @intFromFloat(@max(1, @round(len / 4)));
    const yaw = -std.math.atan2(dz, dx);
    var i: u32 = 0;

    while (i < n) : (i += 1) {
        if (i % 4 == 3) continue;

        const q = (@as(f32, @floatFromInt(i)) + 0.5) / @as(f32, @floatFromInt(n));

        put(b, kind, x0 + dx * q, z0 + dz * q, yaw);
    }
}

fn perimeter(b: *Builder) void {
    const e = edge;
    var x: f32 = -e + 2;

    while (x < e - 1) : (x += 4) {
        if (!(x > gate_x - 10 and x < gate_x + 10)) put(b, if (@mod(x + 200, 56) < 20) .fence else .hoarding, x, -e, 0);

        put(b, if (@mod(x + 200, 64) < 16) .fence else .hoarding, x, e, pi);
        put(b, if (@mod(x + 212, 40) < 16) .fence else .hoarding, -e, x, half_pi);
        put(b, .hoarding, e, x, -half_pi);
    }

    line(b, .barrier, gate_x - 8, -e, gate_x + 8, -e, 4);
    put(b, .lights, gate_x - 10, -e + 3, 0);
    put(b, .lights, gate_x + 10, -e + 3, pi);
    put(b, .sign, gate_x - 13, -e + 1.2, 0);
    put(b, .sign, gate_x + 13, -e + 1.2, 0);
    structure(b, .cabins, &S.cabins, -57.5, 0, -62, 0);

    var c: f32 = -e + 2;

    while (c < -e + 14) : (c += 3.2) {
        put(b, .cone, gate_x - 6.5, c, 0);
        put(b, .cone, gate_x + 6.5, c + 1.6, 0);
    }
}

fn core(b: *Builder) void {
    const tx = tower_at[0];
    const tz = tower_at[1];
    const F = [_]f32{ 0.3, 3.9, 7.5, 11.1, 14.7 };

    structure(b, .tower, &S.tower, tx, 0, tz, 0);
    structure(b, .crane, &S.crane, 26, 0, -6, 0.8);

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
    run(b, .fence, 38, 10, 38, 34);
}

fn pp(b: *Builder, kind: K, dx: f32, dz: f32, yaw: f32) void {
    put(b, kind, pit_c[0] + dx * pit_k, pit_c[1] + dz * pit_k, yaw);
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

    var i: i32 = -2;

    while (i <= 2) : (i += 1) {
        const fi: f32 = @floatFromInt(i);

        put(b, .core, pit_c[0] - 12 * pit_k, pit_c[1] + fi * 4.2, half_pi);
        put(b, .formwork, pit_c[0] + 12 * pit_k, pit_c[1] + fi * 4.1, -half_pi);
        put(b, .rebar, pit_c[0] + fi * 3.4, pit_c[1] - 10 * pit_k, 0);
        put(b, .rebar, pit_c[0] + fi * 3.4 + 1, pit_c[1] + 11 * pit_k, 0.2);
    }

    pp(b, .core, -4, 2, 0);
    pp(b, .core, 4, -2, 0);
    pp(b, .spool, -18, -16, 0.05);
    pp(b, .skip, 2, -22, half_pi);
    pp(b, .skip, 22, -20, 0);
    pp(b, .genset, 20, 18, half_pi + 0.05);
    pp(b, .pallet, 8, 18, 0);
    pp(b, .bag, -14, 17, 0.3);
    pp(b, .bag, -12.8, 17.6, 0.9);
    pp(b, .pipes, -4, 18, 0);
    pp(b, .pipes, 2, -15, half_pi);
    pp(b, .drums, -8, -8, 0);
    pp(b, .lamp, 22, -22, 0.6);
    pp(b, .scafstack, 4, 22, 0);
    putS(b, .spoil, pit_c[0] + 22 * pit_k, pit_c[1] + 2 * pit_k, 0.4, 2.4);
    putS(b, .spoil, pit_c[0] - 22 * pit_k, pit_c[1] + 14 * pit_k, 1.4, 2.0);

    put(b, .genset, pit[0] - 8, pit[3] - 6, 0);
    put(b, .scafstack, pit[0] - 8, pit[1] + 6, 0);
    put(b, .lamp, pit[0] - 5, pit[3] + 6, 0.7);
    run(b, .fence, pit[0] - 3, pit[1] - 3, pit[0] - 3, ramp_z[0] - 4);
    run(b, .fence, pit[0] - 3, ramp_z[1] + 4, pit[0] - 3, pit[3] - 3);
    run(b, .fence, pit[2] + 3, pit[1] - 3, pit[2] + 3, pit[3] - 3);
    run(b, .fence, pit[0] - 3, pit[1] - 3, pit[2] + 3, pit[1] - 3);
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
    run(b, .hoarding, -36, 52, -12, 52);
    run(b, .hoarding, 12, 52, 36, 52);
    line(b, .barrier, 40, -10, 48, -10, 4);
}

fn containerYard(b: *Builder) void {
    for (stacks) |st| stackAt(b, st);

    put(b, .pipes, -60, -24, half_pi);
    put(b, .drums, -60, 12, 0);
    put(b, .pallet, -60, -6, 0);
    put(b, .pallet, -58.6, -6.2, 0.1);
    put(b, .timber, -60, 30, 0);
    structure(b, .crane, &S.crane, -62, 0, 36, 1.83);
}

fn plantYard(b: *Builder) void {
    put(b, .genset, 52, 24, pi);
    put(b, .pipes, 59, 24, pi);
    put(b, .rebar, 66, 24, pi);
    put(b, .drums, 50, 14, half_pi);
    put(b, .lamp, 50, -4, 1);
}

fn roadside(b: *Builder) void {
    var z: f32 = -edge + 14;

    while (z < -48) : (z += 4) {
        if (@mod(z, 24) < 6) continue;

        put(b, .barrier, gate_x + 7, z, half_pi);
    }

    put(b, .sign, gate_x + 7, -48, half_pi);
}

const reserved = [_]Rect{
    .{ .x0 = -32, .z0 = -16, .x1 = 40, .z1 = 38 },
    .{ .x0 = -70, .z0 = 44, .x1 = -44, .z1 = 70 },
    .{ .x0 = 36, .z0 = 42, .x1 = 66, .z1 = 66 },
    .{ .x0 = 6, .z0 = -70, .x1 = 68, .z1 = -12 },
    .{ .x0 = -28, .z0 = -50, .x1 = 12, .z1 = -26 },
    .{ .x0 = -70, .z0 = -36, .x1 = -50, .z1 = 30 },
    .{ .x0 = -68, .z0 = 28, .x1 = -56, .z1 = 42 },
    .{ .x0 = -70, .z0 = -70, .x1 = -46, .z1 = -54 },
    .{ .x0 = 46, .z0 = 10, .x1 = 70, .z1 = 28 },
};

fn free(x: f32, z: f32, r: f32) bool {
    if (@abs(x) > edge - 6 or @abs(z) > edge - 6) return false;

    if (roadDist(x, z) < 7 + r) return false;

    for (reserved) |q| {
        if (x > q.x0 - r and x < q.x1 + r and z > q.z0 - r and z < q.z1 + r) return false;
    }

    for (claimed[0..claimed_n]) |q| {
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
    var gx: f32 = -edge + 6;

    while (gx < edge - 6) : (gx += 11) {
        var gz: f32 = -edge + 6;

        while (gz < edge - 6) : (gz += 11) {
            const x = gx + b.rng.range(-3, 3);
            const z = gz + b.rng.range(-3, 3);

            if (!free(x, z, 3.5)) continue;

            if (moundAt(x, z).h > 0.1 or moundAt(x + 4, z).h > 0.1 or moundAt(x - 4, z).h > 0.1) continue;

            if (b.rng.next() < 0.35) continue;

            cluster(b, x, z);
        }
    }
}

fn lp(b: *Builder, kind: K, cx: f32, cz: f32, yaw: f32, lx: f32, lz: f32, ly: f32, lyaw: f32, s: f32) void {
    const o = rot(yaw, lx, lz);
    const x = cx + o[0];
    const z = cz + o[1];

    b.putAt(kit.of(kind), vec(x, t.height(x, z) + ly, z), yaw + lyaw, s);
}

fn lbox(b: *Builder, cx: f32, cz: f32, yaw: f32, lx0: f32, lz0: f32, lx1: f32, lz1: f32, h: f32) void {
    const r = api.world.rotBox(cx, cz, yaw, lx0, lz0, lx1, lz1);
    const y = t.height(cx, cz);

    api.box(b, r[0], y - 0.5, r[1], r[2], y + h, r[3]);
}

fn lstruct(b: *Builder, kind: K, sol: []const [7]f32, cx: f32, cz: f32, yaw: f32, lx: f32, lz: f32, lyaw: f32) void {
    const o = rot(yaw, lx, lz);

    structure(b, kind, sol, cx + o[0], t.height(cx + o[0], cz + o[1]), cz + o[1], yaw + lyaw);
}

fn foundations(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    addPad(cx, cz, 9, 9, 0);

    var i: i32 = -1;

    while (i <= 1) : (i += 1) {
        var j: i32 = -1;

        while (j <= 1) : (j += 1) {
            const fi: f32 = @floatFromInt(i);
            const fj: f32 = @floatFromInt(j);

            lstruct(b, .starter, &S.starter, cx, cz, yaw, fi * 5.5, fj * 5.5, 0);
        }
    }

    lp(b, .rebarmat, cx, cz, yaw, -2.75, 0, 0.02, half_pi, 1);
    lp(b, .rebarmat, cx, cz, yaw, 2.75, 0, 0.02, half_pi, 1);
    lp(b, .formwork, cx, cz, yaw, 0, -8.2, 0, 0, 1);

    for ([_]f32{ -6, -2, 2, 6 }) |sx| {
        lp(b, .scaffold, cx, cz, yaw, sx, 8.2, 0, 0, 1);
        lp(b, .scaffold, cx, cz, yaw, sx, 8.2, 3.1, 0, 1);
    }

    lbox(b, cx, cz, yaw, -8, 7.5, 8, 8.9, 6.2);
    lp(b, .pallet, cx, cz, yaw, -8, -5, 0, 0.1, 1);
    lp(b, .bag, cx, cz, yaw, -7.6, -3.4, 0, 0.5, 1);
    lp(b, .rebar, cx, cz, yaw, 7.5, -4.5, 0, half_pi, 1);
    lp(b, .mixer, cx, cz, yaw, 6, 4, 0, 0.6, 1);
}

fn yard(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    addPad(cx, cz, 9, 7.5, 1);

    const row = [_]K{ .wrap, .wrap, .ibc, .wrap, .ibc, .ibc, .wrap, .wrap, .wrap };
    var n: usize = 0;

    for ([_]f32{ -5, -2.6 }) |lz| {
        var lx: f32 = -7;

        while (lx <= 7) : (lx += 1.75) {
            const k2 = row[(n * 5 + @as(usize, @intFromFloat(lz + 10))) % row.len];

            n += 1;
            lp(b, k2, cx, cz, yaw, lx, lz, 0, b.rng.range(-0.06, 0.06), 1);

            if (b.rng.next() < 0.35 and k2 == .wrap) lp(b, .wrap, cx, cz, yaw, lx, lz, 1.21, b.rng.range(-0.1, 0.1), 1);
        }
    }

    lp(b, .precast, cx, cz, yaw, -5, 1.6, 0, 0, 1);
    lp(b, .precast, cx, cz, yaw, -5, 1.6, 0.9, 0.04, 1);
    lp(b, .pipes, cx, cz, yaw, 0.5, 1.6, 0, 0, 1);
    lp(b, .timber, cx, cz, yaw, 5.5, 1.6, 0, 0, 1);
    lp(b, .scafstack, cx, cz, yaw, -5, 5, 0, 0, 1);
    lp(b, .spool, cx, cz, yaw, 0, 5, 0, 0.3, 1);
    lp(b, .spool, cx, cz, yaw, 1.6, 5.2, 0, 1.1, 1);
    lp(b, .bag, cx, cz, yaw, 4, 5, 0, 0.2, 1);
    lp(b, .bag, cx, cz, yaw, 5.4, 5.3, 0, 0.9, 1);

    var lx: f32 = -8;

    while (lx <= 8) : (lx += 2) lp(b, .pedbar, cx, cz, yaw, lx, -7.4, 0, 0, 1);

    lbox(b, cx, cz, yaw, -9, -7.6, 9, -7.2, 1.1);
    lp(b, .lamp, cx, cz, yaw, 8.5, 6.5, 0, 2.2, 1);
}

fn cabinRow(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    addPad(cx, cz, 10, 7, 2);

    for ([_]f32{ -6.5, -2.2, 2.1 }) |lx| lp(b, .sitecabin, cx, cz, yaw, lx, -1, 0, 0, 1);

    var i: u32 = 0;

    while (i < 3) : (i += 1) lp(b, .toilet, cx, cz, yaw, 6 + @as(f32, @floatFromInt(i)) * 1.4, -3.5, 0, 0, 1);

    lp(b, .genset, cx, cz, yaw, 7, 2, 0, half_pi, 1);
    lp(b, .sandbags, cx, cz, yaw, -4, 5.4, 0, 0, 1);
    lp(b, .sandbags, cx, cz, yaw, 2, 5.4, 0, 0.05, 1);
    lp(b, .sign, cx, cz, yaw, 8, 5.4, 0, 0, 1);
    lp(b, .ibc, cx, cz, yaw, -9, 3, 0, 0.2, 1);
    lp(b, .drums, cx, cz, yaw, -9, 5.4, 0, 0, 1);
}

fn steelBay(b: *Builder, cx: f32, cz: f32, yaw: f32, tall: bool) void {
    const sc: f32 = 1.5;
    const h: f32 = 3.095 * sc;
    const lv: usize = if (tall) 3 else 2;

    addPad(cx, cz, 8, 8, 0);

    for ([_]f32{ -3, 3 }) |lx| {
        for ([_]f32{ -3, 3 }) |lz| {
            var l: usize = 0;

            while (l < lv) : (l += 1) {
                if (l == lv - 1 and lx > 0 and lz > 0) continue;

                lp(b, .framebay, cx, cz, yaw, lx, lz, @as(f32, @floatFromInt(l)) * h, 0, sc);
            }
        }
    }

    for ([_]f32{ -5.8, -0.2, 5.8 }) |px| {
        for ([_]f32{ -5.8, -0.2, 5.8 }) |pz| lbox(b, cx, cz, yaw, px - 0.25, pz - 0.25, px + 0.25, pz + 0.25, h * @as(f32, @floatFromInt(lv)));
    }

    lp(b, .scaffold, cx, cz, yaw, -4, -7.2, 0, 0, 1);
    lp(b, .scaffold, cx, cz, yaw, 0, -7.2, 0, 0, 1);
    lp(b, .scaffold, cx, cz, yaw, -4, -7.2, 3.1, 0, 1);
    lp(b, .gantry, cx, cz, yaw, 3.5, -7.6, 0, 0, 1);
    lbox(b, cx, cz, yaw, -6, -7.9, 2, -6.5, 6.2);

    for ([_]f32{ 1.6, 5.4 }) |gx| lbox(b, cx, cz, yaw, gx - 0.2, -9.5, gx + 0.2, -5.7, 4.2);

    lp(b, .precast, cx, cz, yaw, 0, 0, 0, 0.1, 1);
    lp(b, .wrap, cx, cz, yaw, -3, 2, 0, 0, 1);
    lp(b, .ibc, cx, cz, yaw, 2.5, -2, 0, 0.3, 1);
}

fn boxStack(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    const kinds = [_]K{ .box_red, .box_blue, .box_green };
    var i: usize = 0;

    addPad(cx, cz, 8, 7, 2);

    for ([_]f32{ -3.2, 0, 3.2 }) |lz| {
        const k2 = kinds[(i + @as(usize, @intFromFloat(b.rng.range(0, 2.99)))) % 3];
        const n: u32 = if (i == 1) 3 else 2;
        var lvl: u32 = 0;

        i += 1;

        while (lvl < n) : (lvl += 1) {
            const o = rot(yaw, -1, lz);
            const x = cx + o[0];
            const z = cz + o[1];

            structure(b, k2, boxSolids(k2), x, t.height(x, z) + @as(f32, @floatFromInt(lvl)) * 2.59, z, yaw + (if (lvl > 0) b.rng.range(-0.03, 0.03) else 0));
        }
    }

    lp(b, .skip, cx, cz, yaw, 6, -4, 0, half_pi, 1);
    lp(b, .ibc, cx, cz, yaw, 6, 1, 0, 0.1, 1);
    lp(b, .ibc, cx, cz, yaw, 6, 2.3, 0, -0.1, 1);
    lp(b, .wrap, cx, cz, yaw, 6.2, 4.4, 0, 0, 1);
    lp(b, .drums, cx, cz, yaw, -6.5, 5, 0, 0, 1);
}

fn earthBank(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    addPad(cx, cz, 8, 6, 3);
    lp(b, .spoil, cx, cz, yaw, -2, 1, -0.3, 0.4, 2.2);
    lp(b, .sandbags, cx, cz, yaw, -2, -5, 0, 0, 1);
    lp(b, .sandbags, cx, cz, yaw, 2.2, -5, 0, 0.05, 1);
    lp(b, .sandbags, cx, cz, yaw, 6, -3.5, 0, half_pi, 1);
    lp(b, .pipes, cx, cz, yaw, 5, 3, 0, half_pi, 1);
    lp(b, .tplate, cx, cz, yaw, 3, -1, 0.02, 0.2, 1.4);
    lp(b, .cone, cx, cz, yaw, 4.5, -1.5, 0, 0, 1);
    lp(b, .cone, cx, cz, yaw, 1.5, 0.5, 0, 0, 1);
    lp(b, .lights, cx, cz, yaw, -7, 4, 0, 0, 1);
}

fn module(b: *Builder, x: f32, z: f32) void {
    const yaw = @as(f32, @floatFromInt(@as(u32, @intFromFloat(b.rng.range(0, 3.99))))) * half_pi;
    const pick = b.rng.next();

    if (pick < 0.2) foundations(b, x, z, yaw) else if (pick < 0.4) yard(b, x, z, yaw) else if (pick < 0.54) cabinRow(b, x, z, yaw) else if (pick < 0.72) steelBay(b, x, z, yaw, b.rng.next() < 0.4) else if (pick < 0.86) boxStack(b, x, z, yaw) else earthBank(b, x, z, yaw);
}

fn fill(b: *Builder) void {
    var gx: f32 = -edge + 10;

    while (gx < edge - 9) : (gx += 16) {
        var gz: f32 = -edge + 10;

        while (gz < edge - 9) : (gz += 16) {
            const x = gx;
            const z = gz;

            if (!free(x, z, 8.5) or moundAt(x, z).h > 0.1 or moundAt(x + 8, z).h > 0.1 or moundAt(x - 8, z).h > 0.1 or moundAt(x, z + 8).h > 0.1 or moundAt(x, z - 8).h > 0.1) continue;

            module(b, x, z);
            if (claimed_n < claimed.len) {
                claimed[claimed_n] = .{ .x0 = x - 10, .z0 = z - 10, .x1 = x + 10, .z1 = z + 10 };
                claimed_n += 1;
            }
        }
    }
}

fn mini(b: *Builder, x: f32, z: f32) void {
    const yaw = @as(f32, @floatFromInt(@as(u32, @intFromFloat(b.rng.range(0, 3.99))))) * half_pi;
    const pick = b.rng.next();

    if (pick < 0.3) {
        addPad(x, z, 4.5, 3.5, 1);

        for ([_]f32{ -2, 2 }) |lx| {
            var l: f32 = 0;

            while (l < 3) : (l += 1) lp(b, .scaffold, x, z, yaw, lx, 0, l * 3.1, 0, 1);
        }

        lbox(b, x, z, yaw, -4, -0.75, 4, 0.75, 9.3);
        lp(b, .scafstack, x, z, yaw, 0, 2.6, 0, 0, 1);
        lp(b, .wrap, x, z, yaw, -3, -2.4, 0, 0.1, 1);
    } else if (pick < 0.5) {
        addPad(x, z, 5, 3, 2);
        lp(b, .sitecabin, x, z, yaw, -1, 0, 0, half_pi, 1);
        lp(b, .toilet, x, z, yaw, 3.6, -1.2, 0, 0, 1);
        lp(b, .toilet, x, z, yaw, 3.6, 0.2, 0, 0, 1);
        lp(b, .ibc, x, z, yaw, 3.6, 2, 0, 0.3, 1);
    } else if (pick < 0.68) {
        addPad(x, z, 5, 5, 0);

        for ([_]f32{ -2.5, 2.5 }) |lx| {
            for ([_]f32{ -2.5, 2.5 }) |lz| lstruct(b, .starter, &S.starter, x, z, yaw, lx, lz, 0);
        }

        lp(b, .rebarmat, x, z, yaw, 0, 0, 0.02, 0, 0.7);
        lp(b, .formwork, x, z, yaw, 0, -4.4, 0, 0, 1);
    } else if (pick < 0.84) {
        lp(b, .spoil, x, z, yaw, 0, 0, -0.3, b.rng.range(0, 6), 1.6);
        lp(b, .sandbags, x, z, yaw, 0, -4.2, 0, 0, 1);
        lp(b, .sandbags, x, z, yaw, 4.2, 0, 0, half_pi, 1);
    } else {
        addPad(x, z, 4, 4, 1);

        for ([_]f32{ -1.2, 0, 1.2 }) |lx| lp(b, .wrap, x, z, yaw, lx, -1, 0, 0, 1);

        lp(b, .wrap, x, z, yaw, -0.6, -1, 1.21, 0.1, 1);
        lp(b, .ibc, x, z, yaw, -1, 1.2, 0, 0, 1);
        lp(b, .ibc, x, z, yaw, 0.4, 1.2, 0, 0, 1);
        lp(b, .ibc, x, z, yaw, -0.3, 1.2, 1.16, 0.05, 1);
        lp(b, .pedbar, x, z, yaw, 0, 3.2, 0, 0, 1);
        lp(b, .pedbar, x, z, yaw, 2.6, 2, 0, half_pi, 1);
    }
}

fn fillMini(b: *Builder) void {
    var gx: f32 = -edge + 8;

    while (gx < edge - 7) : (gx += 10) {
        var gz: f32 = -edge + 8;

        while (gz < edge - 7) : (gz += 10) {
            if (!free(gx, gz, 5) or moundAt(gx, gz).h > 0.1 or moundAt(gx + 5, gz).h > 0.1 or moundAt(gx - 5, gz).h > 0.1 or moundAt(gx, gz + 5).h > 0.1 or moundAt(gx, gz - 5).h > 0.1) continue;

            if (b.rng.next() < 0.55) continue;

            mini(b, gx, gz);

            if (claimed_n < claimed.len) {
                claimed[claimed_n] = .{ .x0 = gx - 6, .z0 = gz - 6, .x1 = gx + 6, .z1 = gz + 6 };
                claimed_n += 1;
            }
        }
    }
}

var claimed: [400]Rect = undefined;
var claimed_n: usize = 0;

fn pitCover(b: *Builder) void {
    const fy = pit_floor;

    for ([_][3]f32{ .{ -21, 20, 0 }, .{ -13, -20, 0.1 }, .{ 19, 20, half_pi }, .{ 21, -18, 0.3 }, .{ 7, 14, 0 }, .{ -19, -4, half_pi } }) |q| pp(b, .sandbags, q[0], q[1], q[2]);

    for ([_][2]f32{ .{ -15, 10 }, .{ -14.4, 8.8 }, .{ 15, -12 }, .{ 13.8, -12.4 } }) |q| pp(b, .ibc, q[0], q[1], 0.2);

    for ([_][2]f32{ .{ 9, -24 }, .{ 10, -24 }, .{ -23, -16 }, .{ -23, -15 } }) |q| pp(b, .wrap, q[0], q[1], 0);

    const bays = [_][2]f32{ .{ pit_c[0] - 9 * pit_k, pit_c[1] - 20 * pit_k }, .{ pit_c[0] + 15 * pit_k, pit_c[1] + 18 * pit_k } };

    b.putAt(kit.of(.framebay), vec(bays[0][0], fy, bays[0][1]), 0, 1.5);
    b.putAt(kit.of(.framebay), vec(bays[1][0], fy, bays[1][1]), half_pi, 1.5);

    for (bays) |c| {
        for ([_]f32{ -2.8, 2.8 }) |ox| {
            for ([_]f32{ -2.8, 2.8 }) |oz| api.box(b, c[0] + ox - 0.2, fy - 0.5, c[1] + oz - 0.2, c[0] + ox + 0.2, fy + 4.6, c[1] + oz + 0.2);
        }
    }

    const sz = pit[3] - 3.5;

    for ([_]f32{ -14, -10, -6 }) |dx| {
        b.putAt(kit.of(.scaffold), vec(pit_c[0] + dx, fy, sz), 0, 1);
        b.putAt(kit.of(.scaffold), vec(pit_c[0] + dx, fy + 3.1, sz), 0, 1);
    }

    api.box(b, pit_c[0] - 16, fy - 0.5, sz - 0.8, pit_c[0] - 4, fy + 6.2, sz + 0.8);
}

fn roadDressing(b: *Builder) void {
    for (roads) |r| {
        const dx = r[2] - r[0];
        const dz = r[3] - r[1];
        const len = @sqrt(dx * dx + dz * dz);
        const ux = dx / len;
        const uz = dz / len;
        const yaw = -std.math.atan2(dz, dx);
        var d: f32 = 6;
        var n: u32 = 0;

        while (d < len - 6) : (d += 11) {
            n += 1;

            for ([_]f32{ -1, 1 }) |side| {
                const off = side * b.rng.range(9, 11.5);
                const x = r[0] + ux * d - uz * off;
                const z = r[1] + uz * d + ux * off;

                if (!free(x, z, 1.8) or moundAt(x, z).h > 0.1) continue;

                const pick = b.rng.next();

                if (n % 6 == 0 and side > 0) {
                    put(b, .lamp, x, z, yaw);
                } else if (pick < 0.16) {
                    put(b, .wrap, x - ux * 0.6, z - uz * 0.6, yaw);
                    put(b, .wrap, x + ux * 0.6, z + uz * 0.6, yaw + 0.05);
                    put(b, .ibc, x + ux * 1.9, z + uz * 1.9, yaw);
                } else if (pick < 0.3) {
                    put(b, .sandbags, x, z, yaw);
                } else if (pick < 0.42) {
                    put(b, .pedbar, x - ux, z - uz, yaw);
                    put(b, .pedbar, x + ux, z + uz, yaw);
                    put(b, .cone, x + ux * 2.4, z + uz * 2.4, 0);
                } else if (pick < 0.54) {
                    put(b, .pipes, x, z, yaw);
                } else if (pick < 0.64) {
                    put(b, .blocks, x, z, yaw);
                } else if (pick < 0.72) {
                    put(b, .pallet, x, z, yaw);
                    put(b, .bag, x + ux * 1.6, z + uz * 1.6, 0.3);
                } else if (pick < 0.8) {
                    put(b, .skip, x, z, yaw);
                } else if (pick < 0.86) {
                    put(b, .genset, x, z, yaw);
                }
            }
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

    while (i < 60) : (i += 1) {
        const x = b.rng.range(-edge + 4, edge - 4);
        const z = b.rng.range(-edge + 4, edge - 4);
        const near = roadDist(x, z) < 9;
        const kind: K = if (near and b.rng.next() < 0.6) .puddle else if (b.rng.next() < 0.55) .gravel else .puddle;

        if (t.height(x, z) < -0.3 and kind == .gravel) continue;

        if (moundAt(x, z).h > 0.1 or t.normal(x, z).y < 0.985 or t.normal(x + 2, z + 2).y < 0.985 or t.normal(x - 2, z - 2).y < 0.985) continue;

        b.putAt(kit.of(kind), vec(x, t.height(x, z), z), b.rng.range(0, 6.28), b.rng.range(0.7, 1.5));
    }
}

fn build(b: *Builder) void {
    pad_n = 0;
    claimed_n = 0;
    perimeter(b);
    core(b);
    pitSite(b);
    frameSite(b);
    tower2Site(b);
    extras(b);
    containerYard(b);
    plantYard(b);
    roadside(b);
    fill(b);
    fillMini(b);
    roadDressing(b);
    pitCover(b);
    clutter(b);
    decals(b);
}

fn spots(gpa: std.mem.Allocator) void {
    api.world.autoSpots(gpa, .{ .loot = 48, .vehicles = 6 });
}
