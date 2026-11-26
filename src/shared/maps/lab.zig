const std = @import("std");
const api = @import("api.zig");
const lk = @import("lab_kit.zig");

const t = api.terrain;
const kit = lk.kit;
const S = lk.solids;
const R = lk.rooms;
const K = lk.K;
const vec = api.vec;
const Builder = api.Builder;
const half_pi = api.half_pi;
const pi = std.math.pi;

pub const def: api.Def = .{
    .name = "Research Lab",
    .note = "Lab blocks, corridors and a campus quad",
    .tint = .{ 90, 170, 176 },
    .ready = true,
    .half = 178,
    .play = 150,
    .facet = 2.0,
    .height = height,
    .ground = ground,
    .build = build,
    .spots = spots,
    .props = &lk.table,
    .palette = .{
        .sun_dir = .{ 0.46, 0.66, -0.6 },
        .sun_tint = .{ 1.12, 1.04, 0.94 },
        .fog = 0.0028,
        .fog_color = .{ 0.8, 0.86, 0.9 },
        .zenith = .{ 0.08, 0.3, 0.64 },
    },
    .backdrop = .{ 92, 122, 84 },
    .floor_y = -3,
    .grip = 0.86,
    .tufts = 0.25,
};

const edge: f32 = 147;

const Bld = struct { kind: K, x: f32, z: f32, yaw: f32 };

const labs = [_]Bld{
    .{ .kind = .lab_big, .x = 0, .z = 54, .yaw = 0 },
    .{ .kind = .lab_tall, .x = 0, .z = -54, .yaw = 0 },
    .{ .kind = .lab_low, .x = 60, .z = 0, .yaw = half_pi },
    .{ .kind = .lab_mid, .x = -62, .z = 0, .yaw = half_pi },
    .{ .kind = .lab_big, .x = -84, .z = -112, .yaw = 0 },
    .{ .kind = .lab_low, .x = 46, .z = -116, .yaw = 0 },
    .{ .kind = .lab_mid, .x = 118, .z = -10, .yaw = half_pi },
    .{ .kind = .lab_tall, .x = -40, .z = 120, .yaw = pi },
    .{ .kind = .lab_low, .x = 40, .z = 120, .yaw = pi },
    .{ .kind = .lab_mid, .x = -122, .z = -28, .yaw = half_pi },
};

const sites = [_]Bld{
    .{ .kind = .dome, .x = 58, .z = 60, .yaw = 0.4 },
    .{ .kind = .otower, .x = 66, .z = 40, .yaw = 0 },
    .{ .kind = .glass, .x = -48, .z = 62, .yaw = 0 },
    .{ .kind = .glass, .x = -58, .z = 62, .yaw = 0 },
    .{ .kind = .gmod, .x = -55, .z = 46, .yaw = 0 },
    .{ .kind = .reactor, .x = 54, .z = -56, .yaw = 0 },
    .{ .kind = .ctower, .x = -58, .z = -58, .yaw = 0.3 },
    .{ .kind = .command, .x = 0, .z = 124, .yaw = 0 },
    .{ .kind = .dome, .x = 100, .z = 108, .yaw = 1.2 },
    .{ .kind = .dome, .x = 118, .z = 124, .yaw = 2.6 },
    .{ .kind = .otower, .x = 132, .z = 104, .yaw = 0.5 },
    .{ .kind = .glass, .x = -104, .z = 102, .yaw = 0 },
    .{ .kind = .glass, .x = -114, .z = 102, .yaw = 0 },
    .{ .kind = .glass, .x = -124, .z = 102, .yaw = 0 },
    .{ .kind = .gmod, .x = -108, .z = 124, .yaw = 0 },
    .{ .kind = .gmod, .x = -126, .z = 124, .yaw = 0 },
    .{ .kind = .gmod, .x = -134, .z = 90, .yaw = half_pi },
    .{ .kind = .command, .x = -106, .z = 58, .yaw = 0.2 },
    .{ .kind = .depot, .x = -122, .z = 8, .yaw = 0 },
    .{ .kind = .depot, .x = -120, .z = -66, .yaw = half_pi },
    .{ .kind = .gatehouse, .x = 12, .z = -134, .yaw = 0 },
    .{ .kind = .garage, .x = -28, .z = -122, .yaw = 0 },
    .{ .kind = .garage, .x = -42, .z = -122, .yaw = 0 },
    .{ .kind = .farmtank, .x = 106, .z = -112, .yaw = 0 },
    .{ .kind = .farmtank, .x = 128, .z = -126, .yaw = 1.1 },
    .{ .kind = .reactor, .x = 130, .z = -98, .yaw = 0 },
    .{ .kind = .garage, .x = 112, .z = -54, .yaw = half_pi },
    .{ .kind = .command, .x = 130, .z = 18, .yaw = -half_pi },
};

const Rect = struct { x0: f32, z0: f32, x1: f32, z1: f32 };

const yards = [_]Rect{
    .{ .x0 = 88, .z0 = 36, .x1 = 146, .z1 = 84 },
    .{ .x0 = 90, .z0 = -146, .x1 = 146, .z1 = -88 },
    .{ .x0 = -146, .z0 = 30, .x1 = -92, .z1 = 80 },
    .{ .x0 = -146, .z0 = 84, .x1 = -94, .z1 = 140 },
    .{ .x0 = -146, .z0 = -84, .x1 = -92, .z1 = -48 },
    .{ .x0 = -146, .z0 = -146, .x1 = -106, .z1 = -124 },
    .{ .x0 = 98, .z0 = -76, .x1 = 146, .z1 = -36 },
    .{ .x0 = -52, .z0 = -132, .x1 = 22, .z1 = -110 },
    .{ .x0 = 127, .z0 = -34, .x1 = 146, .z1 = 10 },
    .{ .x0 = 90, .z0 = -34, .x1 = 106, .z1 = 8 },
};

fn rot(yaw: f32, x: f32, z: f32) [2]f32 {
    const c = @cos(yaw);
    const s = @sin(yaw);

    return .{ x * c + z * s, -x * s + z * c };
}

fn footprint(l: Bld) Rect {
    const info = api.props.info(kit.of(l.kind));
    const quarter = @abs(@sin(l.yaw)) > 0.7;
    const hx = if (quarter) info.max[2] else info.max[0];
    const hz = if (quarter) info.max[0] else info.max[2];

    return .{ .x0 = l.x - hx, .z0 = l.z - hz, .x1 = l.x + hx, .z1 = l.z + hz };
}

fn rectDist(r: Rect, x: f32, z: f32) f32 {
    const dx = @max(r.x0 - x, 0, x - r.x1);
    const dz = @max(r.z0 - z, 0, z - r.z1);

    return @sqrt(dx * dx + dz * dz);
}

fn inRect(r: Rect, x: f32, z: f32) bool {
    return x > r.x0 and x < r.x1 and z > r.z0 and z < r.z1;
}

fn roadDist(x: f32, z: f32) f32 {
    const ring = @abs(@max(@abs(x), @abs(z)) - 80);
    const spine = if (z < -80) @abs(x) else 1e9;
    const east = if (x > 80 and z > 30 and z < 90) @abs(z - 60) else 1e9;
    const west = if (x < -80 and z > -10 and z < 40) @abs(z - 26) else 1e9;

    return @min(@min(ring, spine), @min(east, west));
}

fn pathDist(x: f32, z: f32) f32 {
    const box = @max(@abs(x), @abs(z));
    const cross = @min(@abs(x), @abs(z));
    const diag = @min(@abs(x - z), @abs(x + z)) * 0.7071;
    const ringp = @abs(box - 40);

    if (box < 40) return @min(@min(cross, diag), ringp);

    if (box < 76) return @min(cross, ringp);

    return 100;
}

fn nearBuilding(x: f32, z: f32, pad: f32) bool {
    for (labs) |l| {
        if (rectDist(footprint(l), x, z) < pad) return true;
    }

    for (sites) |s| {
        if (rectDist(footprint(s), x, z) < pad) return true;
    }

    return false;
}

fn inYard(x: f32, z: f32) bool {
    for (yards) |y| {
        if (inRect(y, x, z)) return true;
    }

    return false;
}

fn busy(x: f32, z: f32, pad: f32) bool {
    return nearBuilding(x, z, pad) or roadDist(x, z) < 6.5 or pathDist(x, z) < 2.5 or inYard(x, z);
}

fn height(x: f32, z: f32) f32 {
    const box = @max(@abs(x), @abs(z));
    const hills = t.smooth(edge - 2, t.half, box) * (7 + t.fbm(x * 0.05, z * 0.05) * 7);

    return hills + (t.fbm(x * 0.02, z * 0.02) - 0.45) * 0.6 * t.smooth(90, 120, box);
}

fn mixc(a: [3]f32, b: [3]f32, q: f32) [3]f32 {
    return api.mix3(a, b, q);
}

fn paving(x: f32, z: f32, fine: f32) [3]f32 {
    const jx = @mod(x, 3);
    const jz = @mod(z, 3);
    const joint = @min(@min(jx, 3 - jx), @min(jz, 3 - jz)) < 0.18;

    if (joint) return .{ 158, 154, 146 };

    return mixc(.{ 204, 198, 186 }, .{ 186, 180, 168 }, fine);
}

fn concrete(x: f32, z: f32, fine: f32) [3]f32 {
    const jx = @mod(x, 6);
    const jz = @mod(z, 6);
    const joint = @min(@min(jx, 6 - jx), @min(jz, 6 - jz)) < 0.12;

    if (joint) return .{ 128, 128, 124 };

    return mixc(.{ 166, 166, 160 }, .{ 148, 148, 142 }, fine);
}

fn lawn(x: f32, z: f32, fine: f32) [3]f32 {
    var c: [3]f32 = mixc(.{ 96, 150, 72 }, .{ 80, 134, 62 }, fine);

    c = mixc(c, .{ 120, 160, 80 }, t.smooth(0.45, 0.62, t.fbm(x * 0.05 + 3, z * 0.05)) * 0.6);

    const box = @max(@abs(x), @abs(z));

    if (box < 40 and box > 10) {
        const stripe = @mod(x + z * 0.0 + 400, 6) < 3;

        c = mixc(c, if (stripe) [3]f32{ 104, 160, 76 } else [3]f32{ 86, 140, 64 }, 0.7);
    }

    return c;
}

fn ground(x: f32, z: f32) api.Rgb {
    const n = t.normal(x, z);
    const vary = 0.95 + t.fbm(x * 0.13, z * 0.13) * 0.1;
    const fine = t.fbm(x * 0.35, z * 0.35);
    const box = @max(@abs(x), @abs(z));
    var c = lawn(x, z, fine);

    if (inRect(yards[1], x, z) or inRect(yards[6], x, z) or inRect(yards[7], x, z) or inRect(yards[8], x, z) or inRect(yards[9], x, z)) c = concrete(x, z, fine);

    if (inRect(yards[2], x, z)) c = mixc(.{ 150, 146, 136 }, .{ 128, 124, 116 }, fine);

    if (inRect(yards[4], x, z)) c = concrete(x, z, fine);

    if (inRect(yards[5], x, z)) c = mixc(.{ 146, 140, 128 }, .{ 126, 120, 110 }, fine);

    if (inRect(yards[3], x, z)) {
        const row = @mod(x, 4) < 2.2;

        c = if (row) mixc(.{ 104, 78, 54 }, .{ 88, 66, 46 }, fine) else mixc(.{ 120, 112, 84 }, .{ 104, 98, 72 }, fine);
    }

    for (labs) |l| {
        if (rectDist(footprint(l), x, z) < 5) c = paving(x, z, fine);
    }

    for (sites) |s| {
        if (rectDist(footprint(s), x, z) < 3) c = concrete(x, z, fine);
    }

    const pd = pathDist(x, z);

    if (pd < 2.2) c = paving(x, z, fine) else if (pd < 2.6) c = .{ 150, 146, 138 };

    if (box < 10) c = paving(x, z, fine);

    if (box < 10 and box > 9.4) c = .{ 170, 120, 84 };

    const rd = roadDist(x, z);

    if (rd < 6) {
        c = if (rd > 5.3) .{ 172, 170, 164 } else mixc(.{ 78, 80, 84 }, .{ 68, 70, 74 }, fine);

        if (rd < 0.15 and @mod(x + z, 6) < 3) c = .{ 214, 196, 110 };
    }

    if (inRect(yards[0], x, z)) {
        const bay = @mod(x, 3.2) < 0.16 and @abs(z - 60) > 3.5;

        c = if (bay) .{ 214, 214, 206 } else mixc(.{ 78, 80, 84 }, .{ 70, 72, 76 }, fine);
    }

    if (box > edge + 1) c = mixc(.{ 88, 132, 66 }, .{ 76, 116, 58 }, fine);

    var occ: f32 = 1;

    for (labs) |l| occ = @min(occ, 0.66 + 0.34 * t.smooth(0, 4, rectDist(footprint(l), x, z)));

    for (sites) |s| occ = @min(occ, 0.74 + 0.26 * t.smooth(0, 3, rectDist(footprint(s), x, z)));

    return api.shade(c, vary * occ * (1 + n.x * 0.05 - n.z * 0.03));
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

fn solidsOf(kind: K) []const [7]f32 {
    return switch (kind) {
        .lab_big => &S.lab_big,
        .lab_mid => &S.lab_mid,
        .lab_tall => &S.lab_tall,
        else => &S.lab_low,
    };
}

fn roomsOf(kind: K) []const [6]f32 {
    return switch (kind) {
        .lab_big => &R.lab_big,
        .lab_mid => &R.lab_mid,
        .lab_tall => &R.lab_tall,
        else => &R.lab_low,
    };
}

fn put(b: *Builder, kind: K, x: f32, z: f32, yaw: f32) void {
    b.put(kit.of(kind), x, z, yaw, 1);
}

fn putS(b: *Builder, kind: K, x: f32, z: f32, yaw: f32, s: f32) void {
    b.put(kit.of(kind), x, z, yaw, s);
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

fn fenceLine(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32, gap0: f32, gap1: f32) void {
    const dx = x1 - x0;
    const dz = z1 - z0;
    const len = @sqrt(dx * dx + dz * dz);
    const n: u32 = @intFromFloat(@max(1, @round(len / 2)));
    const yaw = -std.math.atan2(dz, dx);
    var i: u32 = 0;

    while (i < n) : (i += 1) {
        const q = (@as(f32, @floatFromInt(i)) + 0.5) / @as(f32, @floatFromInt(n));
        const d = q * len;

        if (d > gap0 and d < gap1) continue;

        put(b, .fence, x0 + dx * q, z0 + dz * q, yaw);
    }
}

fn bldOf(kind: K) api.Building {
    for (lk.buildings) |q| {
        if (q.kind == kit.of(kind)) return q;
    }

    unreachable;
}

fn site(b: *Builder, s: Bld) void {
    const q = bldOf(s.kind);
    const y0 = api.world.lowest(s.x, s.z, @max(q.w, q.d) / 2) - 0.05;

    b.putAt(kit.of(s.kind), vec(s.x, y0, s.z), s.yaw, 1);

    for (q.blocks) |bl| {
        const r = api.world.rotBox(s.x, s.z, s.yaw, bl[0], bl[1], bl[2], bl[3]);

        b.solid(.{ .box = .{ .min = vec(r[0], y0 - 0.5, r[1]), .max = vec(r[2], y0 + bl[4], r[3]) } });
    }
}

const Room = struct {
    b: *Builder,
    ox: f32,
    oz: f32,
    yaw: f32,
    y: f32,

    fn at(r: Room, kind: K, lx: f32, lz: f32, lyaw: f32) void {
        const p = rot(r.yaw, lx, lz);

        r.b.putAt(kit.of(kind), vec(r.ox + p[0], r.y, r.oz + p[1]), r.yaw + lyaw, 1);
    }
};

fn hash(x: f32, z: f32) f32 {
    const v = @sin(x * 12.9898 + z * 78.233) * 43758.5453;

    return v - @floor(v);
}

fn furnish(b: *Builder, l: Bld) void {
    for (roomsOf(l.kind), 0..) |q, idx| {
        const x0 = q[0];
        const z0 = q[1];
        const x1 = q[2];
        const z1 = q[3];
        const y = q[4];
        const stair = q[5] > 0.5;
        const north = z0 > 0;
        const r: Room = .{ .b = b, .ox = l.x, .oz = l.z, .yaw = l.yaw, .y = y };
        const cx = (x0 + x1) / 2;
        const cz = (z0 + z1) / 2;
        const ext = if (north) z1 else z0;
        const inner = if (north) z0 else z1;
        const face_in: f32 = if (north) pi else 0;
        const face_out: f32 = if (north) 0 else pi;
        const sgn: f32 = if (north) 1 else -1;
        const h = hash(l.x + @as(f32, @floatFromInt(idx)) * 3.1, l.z + y);

        if (stair) {
            r.at(.shelf, cx, inner + sgn * 0.45, face_out);
            r.at(.cylinder, x0 + 0.5, inner + sgn * 0.5, 0);

            continue;
        }

        const kind = @as(u32, @intFromFloat(h * 5));

        switch (kind) {
            0 => {
                r.at(.island, cx - 1.6, cz, half_pi);
                r.at(.island, cx + 1.6, cz, half_pi);
                r.at(.wallbench, x0 + 0.5, ext - sgn * 0.45, face_in);
                r.at(.wallbench, x0 + 1.7, ext - sgn * 0.45, face_in);
                r.at(.hood, x1 - 1.0, ext - sgn * 0.7, face_in);
                r.at(.fridge, x0 + 0.5, inner + sgn * 0.5, face_out);
            },
            1 => {
                var k: f32 = 0;

                while (k < 4) : (k += 1) r.at(.freezer, x0 + 0.6 + k * 0.95, ext - sgn * 0.5, face_in);

                r.at(.shelf, x1 - 0.4, cz, -half_pi);
                r.at(.canister, cx, cz + 0.4, 0);
                r.at(.canister, cx + 0.8, cz - 0.3, 0);
                r.at(.cylinder, x1 - 0.6, inner + sgn * 0.4, 0);
            },
            2 => {
                r.at(.bsc, cx + 0.5, ext - sgn * 0.65, face_in);
                r.at(.bsc, cx - 1.4, ext - sgn * 0.65, face_in);
                r.at(.island, cx, cz, half_pi);
                r.at(.fridge, x1 - 0.5, cz, -half_pi);
                r.at(.lockers, x0 + 0.5, inner + sgn * 0.5, face_out);
            },
            3 => {
                r.at(.desk, x0 + 1.2, ext - sgn * 0.5, face_in);
                r.at(.desk, x0 + 3.2, ext - sgn * 0.5, face_in);
                r.at(.desk, cx + 1.2, cz, face_in);
                r.at(.lockers, x1 - 0.5, cz, -half_pi);
                r.at(.shelf, x0 + 0.4, cz, half_pi);
            },
            else => {
                r.at(.crate, cx - 1.2, cz, 0.2);
                r.at(.crate, cx + 0.3, cz + 0.4, -0.3);
                r.at(.battery, x1 - 1.0, ext - sgn * 0.6, face_in);
                r.at(.battery, x1 - 2.6, ext - sgn * 0.6, face_in);
                r.at(.shelf, x0 + 0.4, cz, half_pi);
            },
        }
    }
}

fn roof(b: *Builder, l: Bld) void {
    const nf: f32 = switch (l.kind) {
        .lab_low => 1,
        .lab_tall => 3,
        else => 2,
    };
    const hw: f32 = switch (l.kind) {
        .lab_big => 20,
        .lab_mid => 16,
        else => 12,
    };
    const r: Room = .{ .b = b, .ox = l.x, .oz = l.z, .yaw = l.yaw, .y = 0.3 + 4 * nf };

    switch (l.kind) {
        .lab_big => {
            var x: f32 = -9;

            while (x < hw - 3) : (x += 4.4) {
                r.at(.solar, x, 3.2, 0);
                r.at(.solar, x, 6.4, 0);
            }
        },
        .lab_mid => {
            r.at(.dish, hw - 4, 4.5, 2.2);
            r.at(.mast, hw - 7, 5.5, 0);
            r.at(.tank, -2, 5, 0);
            r.at(.tank, 1.2, 5, 0);
            r.at(.battery, 4, 5.5, 0);
        },
        .lab_low => {
            r.at(.htank, -1, 4.5, 0);
            r.at(.htank, -1, 2.5, 0);
            r.at(.dish, hw - 3.5, 4.5, 0.4);
            r.at(.hvac, 3, 5.5, 0);
        },
        else => {
            r.at(.dish, hw - 3.5, 4.5, 2.8);
            r.at(.battery, -1, 5.5, 0);
            r.at(.battery, 0.6, 5.5, 0);
            r.at(.radiator, 4, 5.8, 0);
        },
    }
}

fn labSite(b: *Builder, l: Bld, i: usize) void {
    roof(b, l);
    structure(b, l.kind, solidsOf(l.kind), l.x, 0, l.z, l.yaw);
    furnish(b, l);

    const fp = footprint(l);
    const quarter = @abs(@sin(l.yaw)) > 0.7;

    if (quarter) {
        put(b, .hvac, fp.x0 - 1.2, fp.z0 + 3, 0);
        put(b, .hvac, fp.x0 - 1.2, fp.z0 + 4.6, 0);
        put(b, .battery, fp.x0 - 1.2, fp.z1 - 4, half_pi);
        put(b, .canister, fp.x0 - 1.0, fp.z1 - 6, 0);
        put(b, .shrub, fp.x1 + 1.2, l.z - 5, 0);
        put(b, .shrub, fp.x1 + 1.2, l.z + 5, 0);
        put(b, .planter, fp.x1 + 1.4, l.z - 3, 0);
        put(b, .planter, fp.x1 + 1.4, l.z + 3, 0);
        put(b, .mapboard, fp.x1 + 3.2, l.z + 7, half_pi);
        put(b, .crate, fp.x0 - 1.5, fp.z0 + 9, 0.3);
    } else {
        const front = if (l.yaw > 1) fp.z1 else fp.z0;
        const back = if (l.yaw > 1) fp.z0 else fp.z1;
        const fs: f32 = if (l.yaw > 1) 1 else -1;

        put(b, .hvac, fp.x0 + 3, back - fs * 1.2, 0);
        put(b, .hvac, fp.x0 + 4.6, back - fs * 1.2, 0);
        put(b, .htank, fp.x1 - 4, back - fs * 1.5, 0);
        put(b, .cylinder, fp.x1 - 7, back - fs * 0.6, 0);
        put(b, .cylinder, fp.x1 - 7.6, back - fs * 0.6, 0);
        put(b, .crate, fp.x0 + 7, back - fs * 1.4, 0.2);
        put(b, .pallet, fp.x0 + 8.6, back - fs * 1.4, 0);
        put(b, .planter, l.x - 4, front + fs * 1.4, 0);
        put(b, .planter, l.x + 4, front + fs * 1.4, 0);
        put(b, .shrub, l.x - 7, front + fs * 1.2, 0);
        put(b, .shrub, l.x + 7, front + fs * 1.2, 0);
        put(b, .mapboard, l.x + 10, front + fs * 2.6, if (fs > 0) pi else 0);

        if (i % 2 == 0) put(b, .banner, l.x - 10, front + fs * 2.6, 0) else put(b, .radiator, fp.x0 - 1.4, l.z, half_pi);
    }
}

fn qput(b: *Builder, kind: K, x: f32, z: f32, yaw: f32) void {
    if (pathDist(x, z) < 3) return;

    put(b, kind, x, z, yaw);
}

fn groveQ(b: *Builder, x: f32, z: f32, k: f32) void {
    const v = @as(u32, @intFromFloat(@mod(k * 3 + 1, 4)));

    switch (v) {
        0 => {
            qput(b, .flowers, x - 1.4, z - 1.4, 0);
            qput(b, .flowers, x, z - 1.4, 0);
            qput(b, .flowers, x + 1.4, z - 1.4, 0);
            qput(b, .flowers, x - 1.4, z, 0);
            qput(b, .flowers, x + 1.4, z, 0);
            qput(b, .pit, x, z, k);
            qput(b, .bench, x, z + 2.6, 0);
        },
        1 => {
            qput(b, .cwall, x - 2, z, 0);
            qput(b, .cwall, x - 1, z, 0);
            qput(b, .cwall, x, z, 0);
            qput(b, .cwall, x + 1, z, 0);
            qput(b, .planter, x + 2.2, z, 0);
            qput(b, .planter, x - 3.2, z, 0);
            qput(b, .shrub, x - 1, z + 2, 0);
            qput(b, .shrub, x + 1, z + 2, 0);
        },
        2 => {
            qput(b, .planter, x - 2, z - 2, 0);
            qput(b, .planter, x + 2, z - 2, 0);
            qput(b, .planter, x - 2, z + 2, 0);
            qput(b, .planter, x + 2, z + 2, 0);
            qput(b, .flowers, x, z, 0);
            qput(b, .cafe, x + 4, z, 0.6);
        },
        else => {
            qput(b, .hedge, x - 1, z - 2, 0);
            qput(b, .hedge, x + 1, z - 2, 0);
            qput(b, .hedge, x - 2, z, half_pi);
            qput(b, .shrub, x + 1.5, z + 1.5, 0);
            qput(b, .flowers, x, z, 0);
        },
    }
}

fn quad(b: *Builder) void {
    put(b, .fountain, 0, 0, 0);

    var i: u32 = 0;

    while (i < 8) : (i += 1) {
        const a = @as(f32, @floatFromInt(i)) * std.math.tau / 8 + 0.39;

        put(b, .bench, @sin(a) * 7.5, @cos(a) * 7.5, a + pi);
        put(b, .planter, @sin(a + 0.39) * 8.6, @cos(a + 0.39) * 8.6, 0);
        put(b, .lamp, @sin(a) * 11, @cos(a) * 11, 0);
    }

    for ([_]f32{ -1, 1 }) |sx| {
        for ([_]f32{ -1, 1 }) |sz| {
            const k = (sx + 1) + (sz + 1) / 2;

            line(b, .hedge, sx * 4, sz * 12, sx * 4, sz * 36, 2);
            line(b, .hedge, sx * 12, sz * 4, sx * 36, sz * 4, 2);
            line(b, .hedge, sx * 14, sz * 38, sx * 36, sz * 38, 2);
            line(b, .hedge, sx * 38, sz * 14, sx * 38, sz * 36, 2);
            putS(b, .tree, sx * 20, sz * 33, sx * 2, 1.05);
            putS(b, .tree, sx * 33, sz * 20, sz * 3, 0.95);
            putS(b, .tree2, sx * 34, sz * 30, sx, 1.1);
            putS(b, .tree2, sx * 30, sz * 34, sz, 0.9);
            putS(b, .tree2, sx * 18, sz * 10, sx, 0.8);
            put(b, .flowers, sx * 8, sz * 16, 0);
            put(b, .flowers, sx * 8, sz * 18, 0);
            put(b, .flowers, sx * 16, sz * 8, 0);
            put(b, .flowers, sx * 18, sz * 8, 0);
            put(b, .lamp, sx * 6, sz * 26, 0);
            put(b, .lamp, sx * 26, sz * 6, 0);
            put(b, .bench, sx * 6.5, sz * 22, if (sx > 0) -half_pi else half_pi);
            put(b, .bench, sx * 22, sz * 6.5, if (sz > 0) pi else 0);

            groveQ(b, sx * 27, sz * 13, k);
            groveQ(b, sx * 13, sz * 27, k + 4);
        }
    }

    qput(b, .tent, -27, -12, 0.2);
    qput(b, .tent, -12, -27, -0.3);
    qput(b, .cafe, -31, -16, 0);
    qput(b, .cafe, -16, -31, 1);
    qput(b, .kiosk, -31, 12, half_pi);
    qput(b, .cafe, -26, 9, 0.3);
    qput(b, .cafe, -33, 18, 1.2);
    qput(b, .dish, 31, -10, 2.2);
    qput(b, .floodmast, 33, -18, 0.5);
    qput(b, .tent, 12, 31, 0.6);
    qput(b, .mapboard, 10, 14, pi);

    put(b, .mapboard, 3, 40, 0);
    put(b, .mapboard, -3, -40, pi);
    put(b, .banner, 3, 30, 0);
    put(b, .banner, -3, 30, 0);
    put(b, .banner, 3, -30, 0);
    put(b, .banner, -3, -30, 0);
}

fn innerRing(b: *Builder) void {
    put(b, .flowers, 52, 52, 0);
    put(b, .crate, 50, 66, 0.3);
    put(b, .crate, 51.4, 67.2, 1.1);
    put(b, .canister, 52, 64, 0);
    put(b, .battery, 70, 52, half_pi);
    put(b, .battery, 70, 54, half_pi);
    put(b, .mast, 62, 48, 0);
    put(b, .dish, 48, 72, 2.4);
    put(b, .bench, 60, 50, pi);
    line(b, .hedge, 46, 70, 46, 50, 2);

    var g: f32 = 0;

    while (g < 3) : (g += 1) {
        put(b, .flowers, -66 + g * 1.4, 54, 0);
        put(b, .flowers, -66 + g * 1.4, 56, 0);
        put(b, .flowers, -44 - g * 1.4, 54, 0);
        put(b, .planter, -50 + g * 2.4, 70, 0);
    }

    put(b, .pallet, -64, 68, 0.2);
    put(b, .crate, -64, 70, 0.6);
    put(b, .tank, -68, 46, 0);
    fenceLine(b, -70, 40, -70, 72, 14, 20);
    fenceLine(b, -70, 72, -42, 72, 12, 16);

    put(b, .radiator, 46, -50, half_pi);
    put(b, .radiator, 46, -55, half_pi);
    put(b, .radiator, 46, -60, half_pi);
    put(b, .pipe, 54, -64, 0);
    put(b, .pipe, 58, -64, 0);
    put(b, .battery, 62, -50, 0);
    put(b, .battery, 63.6, -50, 0);
    put(b, .htank, 64, -60, half_pi);
    put(b, .genset, 66, -66, 0);
    fenceLine(b, 42, -44, 72, -44, 12, 18);
    fenceLine(b, 72, -44, 72, -72, 30, 40);
    fenceLine(b, 42, -72, 72, -72, 0, 0);
    fenceLine(b, 42, -44, 42, -72, 10, 15);

    put(b, .barrier, -50, -48, 0);
    put(b, .barrier, -46, -50, 0.4);
    put(b, .barrier, -66, -48, 0);
    put(b, .barrier, -68, -66, half_pi);
    put(b, .floodmast, -50, -66, 0.8);
    put(b, .floodmast, -66, -66, -0.8);
    put(b, .crate, -52, -68, 0.2);
    put(b, .crate, -53.2, -69.2, 0.9);
    put(b, .pallet, -64, -52, 0);
    put(b, .canister, -48, -62, 0);
    put(b, .canister, -48.6, -62.8, 0);
    put(b, .mapboard, -50, -44, pi);
}

fn stuffYard(b: *Builder, r: Rect, step: f32, seed: f32) void {
    var x = r.x0 + step / 2;

    while (x < r.x1 - 2) : (x += step) {
        var z = r.z0 + step / 2;

        while (z < r.z1 - 2) : (z += step) {
            const jx = x + (hash(x + seed, z) - 0.5) * 2;
            const jz = z + (hash(z, x - seed) - 0.5) * 2;

            if (nearBuilding(jx, jz, 3.5) or roadDist(jx, jz) < 7) continue;

            const v = hash(jx * 0.7 + seed, jz * 0.3);
            const f = v * 6;

            if (v < 0.22) {
                put(b, .crate, jx, jz, f);
                put(b, .crate, jx + 1.3, jz, f + 0.5);
                put(b, .crate, jx, jz + 1.3, f + 1);
                b.putAt(kit.of(.crate), vec(jx + 0.6, t.height(jx, jz) + 1.2, jz + 0.4), f, 1);
                put(b, .pallet, jx - 1.6, jz + 0.5, 0);
            } else if (v < 0.4) {
                put(b, .pipe, jx - 2, jz, 0);
                put(b, .pipe, jx + 2, jz, 0);
                put(b, .pipe, jx - 2, jz + 1.5, 0);
                put(b, .pipe, jx + 2, jz + 1.5, 0);
                put(b, .canister, jx + 4.4, jz + 0.6, 0);
            } else if (v < 0.55) {
                put(b, .genset, jx, jz, if (v < 0.48) 0 else half_pi);
                put(b, .battery, jx + 3, jz, 0);
                put(b, .canister, jx - 2.6, jz + 0.4, 0);
            } else if (v < 0.68) {
                put(b, .htank, jx, jz, 0);
                put(b, .htank, jx, jz + 1.6, 0);
                put(b, .radiator, jx, jz - 1.8, 0);
            } else if (v < 0.8) {
                put(b, .barrier, jx, jz, f * 0.2);
                put(b, .barrier, jx + 4, jz + 0.4, f * 0.2);
                put(b, .canister, jx + 1, jz + 1.2, 0);
                put(b, .canister, jx + 1.7, jz + 1.5, 0);
                put(b, .canister, jx + 1.3, jz + 2.1, 0);
            } else if (v < 0.9) {
                put(b, .cwall, jx - 1, jz, 0);
                put(b, .cwall, jx, jz, 0);
                put(b, .cwall, jx + 1, jz, 0);
                put(b, .hedge, jx - 1, jz + 1, 0);
                put(b, .hedge, jx + 1, jz + 1, 0);
            } else {
                put(b, .pallet, jx, jz, 0);
                put(b, .pallet, jx + 1.4, jz, 0.1);
                put(b, .crate, jx + 0.2, jz + 1.4, f);
                put(b, .floodmast, jx - 2, jz - 1, f);
            }
        }
    }
}

fn industrial(b: *Builder) void {
    stuffYard(b, yards[1], 9, 1);
    stuffYard(b, yards[6], 8, 2);
    stuffYard(b, yards[8], 7, 3);
    stuffYard(b, yards[9], 7, 4);
    fenceLine(b, 90, -34, 90, 8, 18, 26);
    fenceLine(b, 127, -34, 146, -34, 8, 12);
    fenceLine(b, 127, -34, 127, 10, 20, 26);
    fenceLine(b, 127, 10, 146, 10, 0, 0);
    const tanks = [_][2]f32{ .{ 96, -96 }, .{ 100, -96 }, .{ 104, -96 }, .{ 96, -128 }, .{ 100, -132 }, .{ 140, -110 } };

    for (tanks) |p| put(b, .tank, p[0], p[1], 0);

    var px: f32 = 112;

    while (px < 124) : (px += 4) put(b, .pipe, px, -112, 0);

    var pz: f32 = -122;

    while (pz < -102) : (pz += 4) put(b, .pipe, 118, pz, half_pi);

    put(b, .htank, 116, -100, 0);
    put(b, .htank, 116, -96, 0);
    put(b, .genset, 140, -140, 0);
    put(b, .genset, 134, -140, 0);
    put(b, .genset, 96, -140, half_pi);
    put(b, .radiator, 140, -90, 0);
    put(b, .radiator, 136, -90, 0);
    put(b, .battery, 120, -136, 0);
    put(b, .battery, 121.6, -136, 0);
    put(b, .mast, 142, -142, 0);
    put(b, .floodmast, 94, -92, 0.7);
    put(b, .floodmast, 142, -92, -0.7);
    put(b, .barrier, 102, -122, 0.2);
    put(b, .barrier, 112, -134, 1.3);
    var lx: f32 = 96;

    while (lx < 144) : (lx += 4) put(b, .pipe, lx, -92, 0);

    const piles = [_][2]f32{ .{ 98, -118 }, .{ 114, -142 }, .{ 140, -116 }, .{ 120, -92 }, .{ 96, -106 }, .{ 138, -132 } };

    for (piles, 0..) |q, n| {
        const f: f32 = @floatFromInt(n);

        put(b, .crate, q[0], q[1], f);
        put(b, .crate, q[0] + 1.3, q[1] + 0.3, f * 2);
        put(b, .pallet, q[0] - 1.5, q[1] + 0.2, 0);
        put(b, .canister, q[0] + 0.4, q[1] + 1.6, 0);
        put(b, .canister, q[0] + 1.1, q[1] + 1.8, 0);
        put(b, .barrier, q[0] + 1, q[1] - 2.6, f * 0.4);
        b.putAt(kit.of(.crate), vec(q[0], t.height(q[0], q[1]) + 1.2, q[1]), f + 0.4, 1);
    }

    fenceLine(b, 90, -88, 146, -88, 2, 10);
    fenceLine(b, 90, -146, 90, -88, 30, 38);

    put(b, .crate, 104, -62, 0.1);
    put(b, .crate, 105.3, -62, -0.2);
    put(b, .crate, 104.6, -63.4, 0.4);
    put(b, .pallet, 120, -44, 0);
    put(b, .pallet, 121.4, -44, 0.1);
    put(b, .crate, 128, -60, 0.3);
    put(b, .crate, 129.4, -61, 0.9);
    put(b, .crate, 128.2, -62.2, 1.5);
    put(b, .pallet, 136, -70, 0);
    put(b, .pallet, 136, -66, 0.4);
    put(b, .canister, 132, -46, 0);
    put(b, .canister, 133, -46.6, 0);
    put(b, .canister, 132.2, -47.4, 0);
    put(b, .barrier, 124, -72, 0);
    put(b, .barrier, 140, -54, half_pi);
    put(b, .floodmast, 100, -40, 0.6);
    put(b, .genset, 140, -40, 0);
    fenceLine(b, 98, -76, 146, -76, 18, 26);
}

fn westYards(b: *Builder) void {
    const dishes = [_][3]f32{ .{ -132, 44, 0.6 }, .{ -138, 56, 1.8 }, .{ -126, 70, 2.9 }, .{ -96, 40, 0.2 }, .{ -140, 74, 1.1 } };

    for (dishes) |p| put(b, .dish, p[0], p[1], p[2]);

    putS(b, .radar, -120, 46, 0.4, 1);
    put(b, .mast, -98, 72, 0);
    put(b, .mast, -142, 36, 0);
    put(b, .mast, -116, 76, 0);
    put(b, .genset, -100, 34, 0);
    put(b, .battery, -110, 34, 0);
    put(b, .battery, -111.6, 34, 0);
    put(b, .radiator, -128, 34, 0);
    put(b, .crate, -134, 62, 0.4);
    put(b, .crate, -135.2, 63.3, 1.2);
    put(b, .canister, -96, 50, 0);
    put(b, .canister, -96.8, 50.6, 0);
    fenceLine(b, -146, 30, -92, 30, 46, 54);
    fenceLine(b, -92, 30, -92, 80, 20, 28);

    var gx: f32 = -140;

    while (gx < -98) : (gx += 4) {
        put(b, .flowers, gx, 112, 0);
        put(b, .flowers, gx + 1.4, 112, 0);
        put(b, .flowers, gx, 136, 0);
    }

    var hz: f32 = 88;

    while (hz < 138) : (hz += 8) put(b, .planter, -96, hz, 0);

    put(b, .tank, -142, 132, 0);
    put(b, .tank, -138, 132, 0);
    put(b, .pallet, -98, 120, 0.3);
    put(b, .crate, -98, 124, 0.1);
    put(b, .tent, -120, 112, 0.2);
    fenceLine(b, -146, 84, -94, 84, 22, 30);
    fenceLine(b, -94, 84, -94, 140, 30, 36);

    var cx: f32 = -140;

    while (cx < -96) : (cx += 6) {
        put(b, .crate, cx, -56, b.rng.range(0, 1));
        put(b, .pallet, cx + 1.6, -56, 0);

        if (hash(cx, 3) < 0.6) put(b, .crate, cx, -78, b.rng.range(0, 1));

        if (hash(cx, 5) < 0.5) b.putAt(kit.of(.crate), vec(cx, t.height(cx, -56) + 1.2, -56), 0.5, 1);
    }

    put(b, .barrier, -100, -72, half_pi);
    put(b, .barrier, -104, -80, 0);
    put(b, .floodmast, -96, -52, 0.8);
    put(b, .genset, -140, -70, half_pi);
    fenceLine(b, -146, -48, -92, -48, 22, 30);

    var sx: f32 = -142;

    while (sx < -108) : (sx += 5) {
        var sz: f32 = -144;

        while (sz < -126) : (sz += 4) put(b, .solar, sx, sz, 0);
    }

    put(b, .battery, -104, -132, 0);
    put(b, .battery, -104, -136, 0);
    put(b, .radiator, -110, -140, half_pi);

    put(b, .crate, -100, 4, 0.3);
    put(b, .crate, -101.3, 5.2, 1.1);
    put(b, .pallet, -104, 16, 0);
    put(b, .canister, -130, 22, 0);
    put(b, .htank, -138, 4, half_pi);
    put(b, .barrier, -110, -8, 0);
}

fn northSouth(b: *Builder) void {
    put(b, .flowers, -6, 114, 0);
    put(b, .flowers, 6, 114, 0);
    put(b, .mast, 8, 132, 0);
    put(b, .dish, -8, 132, 0.9);
    put(b, .dish, 14, 128, 2.8);
    put(b, .genset, -14, 130, half_pi);
    put(b, .bench, -10, 112, pi);
    put(b, .bench, 10, 112, pi);
    put(b, .kiosk, 64, 104, 0);
    put(b, .cafe, 68, 100, 0.4);
    put(b, .cafe, 60, 98, 1.1);
    put(b, .battery, 108, 98, 0);
    put(b, .battery, 109.6, 98, 0);
    put(b, .crate, 126, 116, 0.3);
    put(b, .crate, 127.2, 117.4, 1.0);
    put(b, .floodmast, 108, 132, 0.4);
    put(b, .canister, 90, 120, 0);
    put(b, .canister, 90.8, 120.8, 0);
    put(b, .pipe, 108, 116, 0.6);
    put(b, .radiator, 140, 120, half_pi);
    fenceLine(b, 88, 92, 146, 92, 8, 16);

    put(b, .shrub, 126, 2, 0);
    put(b, .barrier, 98, 14, half_pi);

    put(b, .barrier, -6, -128, 0);
    put(b, .barrier, 6, -128, 0);
    put(b, .barrier, -8, -140, 0);
    put(b, .bollard, -3, -132, 0);
    put(b, .bollard, 3, -132, 0);
    put(b, .mapboard, 20, -128, 0);
    put(b, .floodmast, 22, -140, 0.6);
    put(b, .crate, -20, -114, 0.2);
    put(b, .crate, -21.3, -114.8, 1.0);
    put(b, .pallet, -50, -114, 0);
    put(b, .pallet, -50, -116, 0.3);
    put(b, .canister, -34, -112, 0);
    put(b, .canister, -34.8, -112.6, 0);
    put(b, .battery, -20, -130, half_pi);
    put(b, .kiosk, 26, -100, 0);
    put(b, .cafe, 22, -96, 0.6);
    put(b, .barrier, 64, -104, 0.3);
    put(b, .htank, 64, -124, half_pi);
    put(b, .crate, 62, -112, 0.4);
}

fn grounds(b: *Builder) void {
    var x: f32 = -76;

    while (x <= 76) : (x += 16) {
        put(b, .streetlight, x, 73.5, 0);
        put(b, .streetlight, x, -73.5, pi);
        put(b, .streetlight, 73.5, x, -half_pi);
        put(b, .streetlight, -73.5, x, half_pi);
    }

    var px: f32 = 90;

    while (px < 144) : (px += 6.4) {
        put(b, .bollard, px, 60, 0);

        if (hash(px, 4) < 0.5) put(b, .planter, px + 3.2, 60, 0);
    }

    put(b, .shrub, 88, 38, 0);
    put(b, .shrub, 88, 82, 0);
    put(b, .tree2, 146, 82, 0);
    put(b, .kiosk, 94, 28, 0);
    put(b, .bench, 98, 26, 0);
    put(b, .cafe, 100, 30, 0.6);

    var e: f32 = -edge + 1;

    while (e < edge) : (e += 2) {
        if (@abs(e) > 8) put(b, .fence, e, -edge, 0);

        put(b, .fence, e, edge, 0);
        put(b, .fence, -edge, e, half_pi);
        put(b, .fence, edge, e, half_pi);
    }
}

fn greenery(b: *Builder) void {
    var i: u32 = 0;

    while (i < 1600) : (i += 1) {
        const x = b.rng.range(-172, 172);
        const z = b.rng.range(-172, 172);
        const box = @max(@abs(x), @abs(z));

        if (box < 86) continue;

        if (box > edge - 3 and box < edge + 3) continue;

        const out = box > edge + 2;

        if (!out and busy(x, z, 7)) continue;

        const r = b.rng.next();

        if (out) {
            if (r < 0.55) putS(b, .tree, x, z, r * 9, b.rng.range(0.9, 1.4)) else if (r < 0.8) putS(b, .shrub, x, z, 0, b.rng.range(1.0, 1.6));

            continue;
        }

        if (r < 0.11) putS(b, .tree, x, z, r * 9, b.rng.range(0.85, 1.2)) else if (r < 0.24) putS(b, .tree2, x, z, r * 9, b.rng.range(0.9, 1.3)) else if (r < 0.3) putS(b, .pit, x, z, r * 9, 1.0) else if (r < 0.42) put(b, .shrub, x, z, 0) else if (r < 0.48) put(b, .flowers, x, z, 0);
    }
}

fn campusFill(b: *Builder) void {
    var i: u32 = 0;
    var placed: u32 = 0;

    while (i < 1400 and placed < 240) : (i += 1) {
        const x = b.rng.range(-72, 72);
        const z = b.rng.range(-72, 72);
        const box = @max(@abs(x), @abs(z));

        if (box < 42 or busy(x, z, 5)) continue;

        const r = b.rng.next();

        placed += 1;

        if (r < 0.3) putS(b, .tree, x, z, r * 20, b.rng.range(0.8, 1.1)) else if (r < 0.45) putS(b, .tree2, x, z, r * 9, 1) else if (r < 0.6) put(b, .shrub, x, z, 0) else if (r < 0.72) {
            const yaw = b.rng.range(0, pi);
            const c = @cos(yaw);
            const s = @sin(yaw);

            put(b, .hedge, x - c * 1, z + s * 1, yaw);
            put(b, .hedge, x + c * 1, z - s * 1, yaw);
            put(b, .hedge, x + c * 3, z - s * 3, yaw);
        } else if (r < 0.8) {
            put(b, .cwall, x, z, 0);
            put(b, .cwall, x + 1, z, 0);
            put(b, .cwall, x + 2, z, 0);
            put(b, .planter, x + 3.2, z, 0);
        } else if (r < 0.88) {
            put(b, .flowers, x, z, 0);
            put(b, .flowers, x + 1.4, z, 0);
            put(b, .bench, x + 0.7, z + 1.6, pi);
        } else if (r < 0.94) {
            put(b, .crate, x, z, r * 7);
            put(b, .pallet, x + 1.5, z + 0.3, 0);
        } else {
            put(b, .pit, x, z, r * 5);
        }
    }

    var d: f32 = -70;

    while (d <= 70) : (d += 5) {
        if (@abs(d) < 8) continue;

        const sides = [_][3]f32{ .{ d, 71, 0 }, .{ d, -71, 0 }, .{ 71, d, half_pi }, .{ -71, d, half_pi } };

        for (sides) |q| {
            if (nearBuilding(q[0], q[1], 3)) continue;

            const h = hash(q[0], q[1]);

            if (h < 0.55) put(b, .hedge, q[0], q[1], q[2]) else if (h < 0.7) put(b, .shrub, q[0], q[1], 0);
        }
    }
}

fn groves(b: *Builder) void {
    var gx: f32 = -140;

    while (gx <= 140) : (gx += 13) {
        var gz: f32 = -140;

        while (gz <= 140) : (gz += 13) {
            const jx = gx + (hash(gx, gz) - 0.5) * 6;
            const jz = gz + (hash(gz, gx) - 0.5) * 6;
            const box = @max(@abs(jx), @abs(jz));

            if (box < 87 or box > 141 or busy(jx, jz, 9)) continue;

            const v = hash(jx * 0.3, jz * 0.7);

            if (v < 0.45) {
                putS(b, .tree, jx, jz, v * 9, 1.1);
                putS(b, .tree, jx + 5, jz + 2, v * 5, 0.9);
                putS(b, .tree2, jx - 3, jz + 4, v, 1.0);
                put(b, .shrub, jx + 2, jz - 3, 0);
                put(b, .shrub, jx - 4, jz - 1, 0);
                put(b, .flowers, jx + 1, jz + 4, 0);
            } else if (v < 0.65) {
                line(b, .hedge, jx - 5, jz, jx + 5, jz, 2);
                putS(b, .tree2, jx - 6, jz + 2, v, 1.1);
                put(b, .bench, jx, jz + 1.4, pi);
                put(b, .lamp, jx + 6, jz + 1.5, 0);
            } else if (v < 0.8) {
                put(b, .cafe, jx, jz, v * 4);
                put(b, .cafe, jx + 3, jz + 2, v * 7);
                putS(b, .tree, jx + 1, jz - 4, v, 1.2);
                put(b, .planter, jx - 3, jz, 0);
                put(b, .planter, jx - 3, jz + 2, 0);
            } else {
                put(b, .crate, jx, jz, v * 3);
                put(b, .crate, jx + 1.3, jz + 0.4, v * 9);
                put(b, .pallet, jx - 1.6, jz, 0);
                put(b, .canister, jx + 0.5, jz + 1.6, 0);
                put(b, .barrier, jx, jz - 3, v);
                put(b, .floodmast, jx + 3, jz + 2, v);
            }
        }
    }
}

fn build(b: *Builder) void {
    for (labs, 0..) |l, i| labSite(b, l, i);

    for (sites) |s| site(b, s);

    quad(b);
    innerRing(b);
    industrial(b);
    westYards(b);
    northSouth(b);
    grounds(b);
    groves(b);
    greenery(b);
    campusFill(b);
}

fn lift(p: api.Vec3) api.Vec3 {
    var y = p.y;

    for (api.world.pieces) |piece| {
        const bb = piece.shape.bounds();

        if (p.x < bb.min.x or p.x > bb.max.x or p.z < bb.min.z or p.z > bb.max.z) continue;

        if (bb.max.y > y and bb.max.y < p.y + 1.5) y = bb.max.y;
    }

    return vec(p.x, y, p.z);
}

fn spots(gpa: std.mem.Allocator) void {
    api.world.autoSpots(gpa, .{ .loot = 52, .vehicles = 0 });

    for (api.world.weapon_spots) |*w| w.* = lift(w.*);

    for (api.world.spawns) |*w| w.* = lift(w.*);

    var list: std.ArrayList(api.world.Spot) = .empty;
    var x: f32 = 94;

    while (x < 142) : (x += 12) {
        list.append(gpa, .{ .pos = vec(x, t.height(x, 70), 70), .yaw = pi }) catch {};
        list.append(gpa, .{ .pos = vec(x + 6, t.height(x + 6, 50), 50), .yaw = 0 }) catch {};
    }

    api.world.vehicle_spots = list.toOwnedSlice(gpa) catch &.{};
}
