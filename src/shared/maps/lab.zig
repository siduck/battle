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
};

const edge: f32 = api.arena_half + 1;
const ring: f32 = api.arena_half - 4;

const Bld = struct { kind: K, x: f32, z: f32, yaw: f32 };

const labs = [_]Bld{
    .{ .kind = .lab_big, .x = 0, .z = 54, .yaw = 0 },
    .{ .kind = .lab_tall, .x = 0, .z = -54, .yaw = 0 },
    .{ .kind = .lab_low, .x = 60, .z = 0, .yaw = half_pi },
    .{ .kind = .lab_mid, .x = -62, .z = 0, .yaw = half_pi },
};

const sites = [_]Bld{
    .{ .kind = .dome, .x = 58, .z = 60, .yaw = 0.4 },
    .{ .kind = .otower, .x = 66, .z = 40, .yaw = 0 },
    .{ .kind = .glass, .x = -48, .z = 62, .yaw = 0 },
    .{ .kind = .glass, .x = -58, .z = 62, .yaw = 0 },
    .{ .kind = .gmod, .x = -55, .z = 46, .yaw = 0 },
    .{ .kind = .reactor, .x = 54, .z = -56, .yaw = 0 },
    .{ .kind = .ctower, .x = -58, .z = -58, .yaw = 0.3 },
};

const Rect = struct { x0: f32, z0: f32, x1: f32, z1: f32 };


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

fn lane(x: f32, z: f32) f32 {
    return @abs(x - z - 5) * 0.7071;
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

fn busy(x: f32, z: f32, pad: f32) bool {
    return nearBuilding(x, z, pad) or pathDist(x, z) < 2.5 or lane(x, z) < 4;
}

fn height(x: f32, z: f32) f32 {
    const box = @max(@abs(x), @abs(z));

    return t.smooth(edge + 1, t.half, box) * (7 + t.fbm(x * 0.05, z * 0.05) * 7);
}

fn mixc(a: [3]f32, b: [3]f32, q: f32) [3]f32 {
    return api.mix3(a, b, q);
}

fn paving(x: f32, z: f32, fine: f32) [3]f32 {
    const jx = @mod(x, 3);
    const jz = @mod(z, 3);
    const joint = @min(@min(jx, 3 - jx), @min(jz, 3 - jz)) < 0.18;

    if (joint) return .{ 150, 153, 151 };

    return mixc(.{ 198, 198, 192 }, .{ 181, 182, 176 }, fine);
}

fn concrete(x: f32, z: f32, fine: f32) [3]f32 {
    const jx = @mod(x, 6);
    const jz = @mod(z, 6);
    const joint = @min(@min(jx, 6 - jx), @min(jz, 6 - jz)) < 0.12;

    if (joint) return .{ 124, 130, 132 };

    return mixc(.{ 162, 167, 167 }, .{ 146, 151, 152 }, fine);
}

fn lawn(x: f32, z: f32, fine: f32) [3]f32 {
    var c: [3]f32 = mixc(.{ 95, 145, 78 }, .{ 81, 130, 68 }, fine);

    c = mixc(c, .{ 115, 155, 86 }, t.smooth(0.45, 0.62, t.fbm(x * 0.05 + 3, z * 0.05)) * 0.6);

    const box = @max(@abs(x), @abs(z));

    if (box < 40 and box > 10) {
        const stripe = @mod(x + z * 0.0 + 400, 6) < 3;

        c = mixc(c, if (stripe) [3]f32{ 101, 153, 82 } else [3]f32{ 86, 135, 71 }, 0.7);
    }

    return c;
}

fn ground(x: f32, z: f32) api.Rgb {
    const n = t.normal(x, z);
    const vary = 0.95 + t.fbm(x * 0.13, z * 0.13) * 0.1;
    const fine = t.fbm(x * 0.35, z * 0.35);
    const box = @max(@abs(x), @abs(z));
    var c = lawn(x, z, fine);

    for (labs) |l| {
        if (rectDist(footprint(l), x, z) < 5) c = paving(x, z, fine);
    }

    for (sites) |s| {
        if (rectDist(footprint(s), x, z) < 3) c = concrete(x, z, fine);
    }

    const pd = pathDist(x, z);

    if (pd < 2.2) c = paving(x, z, fine) else if (pd < 2.6) c = .{ 142, 146, 145 };

    if (box < 10) c = paving(x, z, fine);

    if (box < 10 and box > 9.4) c = .{ 84, 134, 136 };

    if (box > ring + 1.5 and box < edge) c = paving(x, z, fine);

    if (box > edge + 1) c = mixc(.{ 87, 128, 73 }, .{ 76, 113, 64 }, fine);

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

fn run(b: *Builder, kind: K, x0: f32, z0: f32, x1: f32, z1: f32, gap0: f32, gap1: f32) void {
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

        if (@mod(d, 16) > 12) continue;

        put(b, kind, x0 + dx * q, z0 + dz * q, yaw);
    }
}

fn fenceLine(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32, gap0: f32, gap1: f32) void {
    run(b, .fence, x0, z0, x1, z1, gap0, gap1);
}

fn hedgeLine(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32) void {
    run(b, .hedge, x0, z0, x1, z1, 0, 0);
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
    if (pathDist(x, z) < 3 or lane(x, z) < 3) return;

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

            hedgeLine(b, sx * 4, sz * 12, sx * 4, sz * 36);
            hedgeLine(b, sx * 12, sz * 4, sx * 36, sz * 4);
            hedgeLine(b, sx * 14, sz * 38, sx * 36, sz * 38);
            hedgeLine(b, sx * 38, sz * 14, sx * 38, sz * 36);
            putS(b, .tree, sx * 20, sz * 33, sx * 2, 1.05);
            putS(b, .tree, sx * 33, sz * 20, sz * 3, 0.95);
            putS(b, .tree2, sx * 34, sz * 30, sx, 1.1);
            putS(b, .tree2, sx * 30, sz * 34, sz, 0.9);
            if (lane(sx * 18, sz * 10) > 4) putS(b, .tree2, sx * 18, sz * 10, sx, 0.8);
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
    hedgeLine(b, 46, 70, 46, 50);

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

fn grounds(b: *Builder) void {
    var x: f32 = -ring + 4;

    while (x <= ring - 4) : (x += 16) {
        put(b, .streetlight, x, ring + 2.5, 0);
        put(b, .streetlight, x, -ring - 2.5, pi);
        put(b, .streetlight, ring + 2.5, x, -half_pi);
        put(b, .streetlight, -ring - 2.5, x, half_pi);
    }

    var e: f32 = -edge + 1;

    while (e < edge) : (e += 2) {
        put(b, .fence, e, -edge, 0);
        put(b, .fence, e, edge, 0);
        put(b, .fence, -edge, e, half_pi);
        put(b, .fence, edge, e, half_pi);
    }
}

fn greenery(b: *Builder) void {
    const out = api.arena_half + 11;
    var i: u32 = 0;

    while (i < 360) : (i += 1) {
        const x = b.rng.range(-out, out);
        const z = b.rng.range(-out, out);
        const box = @max(@abs(x), @abs(z));

        if (box < edge + 2) continue;

        const r = b.rng.next();

        if (r < 0.6) putS(b, .tree, x, z, r * 9, b.rng.range(0.9, 1.4)) else if (r < 0.85) putS(b, .shrub, x, z, 0, b.rng.range(1.0, 1.6));
    }
}

fn campusFill(b: *Builder) void {
    var i: u32 = 0;
    var placed: u32 = 0;

    while (i < 1400 and placed < 60) : (i += 1) {
        const x = b.rng.range(-ring, ring);
        const z = b.rng.range(-ring, ring);
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
            put(b, .hedge, x, z, 0);
            put(b, .hedge, x + 2, z, 0);
            put(b, .planter, x + 3.6, z, 0);
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

    var d: f32 = -ring + 1;

    while (d <= ring - 1) : (d += 5) {
        if (@abs(d) < 8) continue;

        const sides = [_][3]f32{ .{ d, ring, 0 }, .{ d, -ring, 0 }, .{ ring, d, half_pi }, .{ -ring, d, half_pi } };

        for (sides) |q| {
            if (nearBuilding(q[0], q[1], 3)) continue;

            const h = hash(q[0], q[1]);

            if (h < 0.55) put(b, .hedge, q[0], q[1], q[2]) else if (h < 0.7) put(b, .shrub, q[0], q[1], 0);
        }
    }
}

fn build(b: *Builder) void {
    for (labs, 0..) |l, i| labSite(b, l, i);

    for (sites) |s| site(b, s);

    quad(b);
    innerRing(b);
    grounds(b);
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
    api.world.autoSpots(gpa, .{ .loot = 28, .vehicles = 2 });

    for (api.world.weapon_spots) |*w| w.* = lift(w.*);

    for (api.world.spawns) |*w| w.* = lift(w.*);
}
