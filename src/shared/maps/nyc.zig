const std = @import("std");
const api = @import("api.zig");
const k = @import("nyc_kit.zig");

const t = api.terrain;
const wd = api.world;
const kit = k.kit;
const K = k.K;
const vec = api.vec;
const Builder = api.Builder;
const pi = std.math.pi;
const hp = api.half_pi;

const edge: f32 = 146;

const Street = enum { edge, alley, street, avenue, broadway };
const Line = struct { at: f32, hw: f32, kind: Street };

const xs = [_]Line{
    .{ .at = -edge, .hw = 0, .kind = .edge },
    .{ .at = -100, .hw = 10, .kind = .avenue },
    .{ .at = -50, .hw = 3, .kind = .alley },
    .{ .at = 0, .hw = 12, .kind = .broadway },
    .{ .at = 50, .hw = 3, .kind = .alley },
    .{ .at = 100, .hw = 10, .kind = .avenue },
    .{ .at = edge, .hw = 0, .kind = .edge },
};

const zs = [_]Line{
    .{ .at = -edge, .hw = 0, .kind = .edge },
    .{ .at = -105, .hw = 7, .kind = .street },
    .{ .at = -35, .hw = 7, .kind = .street },
    .{ .at = 35, .hw = 7, .kind = .street },
    .{ .at = 105, .hw = 7, .kind = .street },
    .{ .at = edge, .hw = 0, .kind = .edge },
};

const Use = enum { row, park, site, plaza };

fn blockUse(i: usize, j: usize) Use {
    if (i == 2 and j == 3) return .park;
    if (i == 4 and j == 1) return .site;
    if (i == 1 and j == 2) return .plaza;

    return .row;
}

pub const def: api.Def = .{
    .name = "Downtown",
    .note = "Avenues, alleys and rooftops",
    .tint = .{ 176, 120, 96 },
    .ready = true,
    .half = 175,
    .play = 150,
    .facet = 2,
    .height = height,
    .ground = ground,
    .build = build,
    .spots = api.autoSpots,
    .props = &k.table,
    .palette = .{
        .sun_dir = .{ 0.42, 0.7, 0.58 },
        .sun_tint = .{ 1.2, 1.04, 0.86 },
        .grade_tint = .{ 1.04, 1.0, 0.96 },
        .grade_sat = 1.2,
        .fog = 0.0045,
        .fog_color = .{ 0.8, 0.8, 0.82 },
        .amb_sky = .{ 0.88, 0.94, 1.12 },
        .amb_ground = .{ 0.82, 0.74, 0.66 },
        .shade_tint = .{ 0.84, 0.88, 1.08 },
        .zenith = .{ 0.1, 0.28, 0.6 },
    },
    .backdrop = .{ 160, 156, 154 },
    .grip = 0.88,
    .tufts = 0.4,
};

fn hash(x: f32, z: f32) f32 {
    return wd.hash2(x, z);
}

fn height(x: f32, z: f32) f32 {
    const e = @max(@abs(x), @abs(z));
    const rim = t.smooth(edge + 8, t.half, e);

    return rim * (3 + t.fbm(x * 0.03, z * 0.03) * 4);
}

fn near(v: f32, lines: []const Line) ?Line {
    for (lines) |l| {
        if (@abs(v - l.at) <= l.hw) return l;
    }

    return null;
}

fn walk(l: Line) f32 {
    return switch (l.kind) {
        .avenue => 3.2,
        .broadway => 3,
        .street => 2.6,
        else => 0,
    };
}

fn mix(a: [3]f32, c: [3]f32, f: f32) [3]f32 {
    return api.mix3(a, c, f);
}

fn cell(v: f32, lines: []const Line) usize {
    var i: usize = 0;

    while (i + 1 < lines.len) : (i += 1) {
        if (v < lines[i + 1].at) return i;
    }

    return lines.len - 2;
}

fn ground(x: f32, z: f32) api.Rgb {
    const l = api.light(x, z);
    const e = @max(@abs(x), @abs(z));
    const n = t.fbm(x * 0.09 + 5, z * 0.09 - 3);

    if (e > edge + 4) return api.shade(mix(.{ 128, 124, 118 }, .{ 116, 112, 106 }, n), l);

    if (e > edge) return slabs(x, z, l);

    const sx = near(x, &xs);
    const sz = near(z, &zs);

    if (sx) |s| blk: {
        if (s.kind == .alley and sz != null) break :blk;

        if (s.kind == .broadway and @abs(x) < 4) return plaza(x, z, l);

        if (sz != null and s.kind != .alley) return road(x, z, l, n);

        if (@abs(x - s.at) > s.hw - walk(s)) return slabs(x, z, l);

        return if (s.kind == .alley) alley(l, n) else road(x, z, l, n);
    }

    if (sz) |s| {
        if (@abs(z - s.at) > s.hw - walk(s)) return slabs(x, z, l);

        return road(x, z, l, n);
    }

    const i = cell(x, &xs);
    const j = cell(z, &zs);

    return switch (blockUse(i, j)) {
        .park => api.shade(mix(.{ 104, 140, 76 }, .{ 92, 126, 68 }, n), l),
        .site => api.shade(mix(.{ 150, 132, 104 }, .{ 132, 116, 92 }, n), l),
        .plaza => plaza(x, z, l),
        .row => yardGround(x, z, l, n),
    };
}

fn slabs(x: f32, z: f32, l: f32) api.Rgb {
    const c = hash(@floor(x / 2), @floor(z / 2));

    return api.shade(mix(.{ 172, 170, 166 }, .{ 156, 154, 150 }, c), l);
}

fn plaza(x: f32, z: f32, l: f32) api.Rgb {
    const c = @mod(@floor(x / 2) + @floor(z / 2), 2) == 0;

    return api.shade(if (c) .{ 184, 170, 150 } else .{ 150, 136, 120 }, l);
}

fn road(x: f32, z: f32, l: f32, n: f32) api.Rgb {
    const p = t.fbm(x * 0.3 - 2, z * 0.3 + 8);
    const patch = t.smooth(0.62, 0.7, p) * 0.12;

    return api.shade(mix(mix(.{ 70, 70, 74 }, .{ 60, 60, 64 }, n), .{ 92, 90, 88 }, patch), l);
}

fn yardGround(x: f32, z: f32, l: f32, n: f32) api.Rgb {
    const tile = hash(@floor(x / 3), @floor(z / 3));
    const seam = @min(@abs(@mod(x, 3) - 1.5), @abs(@mod(z, 3) - 1.5));
    const patch = t.smooth(0.44, 0.52, t.fbm(x * 0.07 + 13, z * 0.07 - 2));
    const stain = t.smooth(0.56, 0.66, t.fbm(x * 0.2 - 7, z * 0.2 + 3));
    var c = mix(.{ 150, 140, 126 }, .{ 124, 116, 106 }, tile);

    c = mix(c, mix(.{ 86, 84, 84 }, .{ 76, 74, 76 }, n), patch);
    c = mix(c, .{ 92, 86, 80 }, stain * 0.6);
    c = mix(c, .{ 104, 98, 92 }, (1 - t.smooth(1.38, 1.48, seam)) * (1 - patch));

    return api.shade(c, l);
}

fn alley(l: f32, n: f32) api.Rgb {
    return api.shade(mix(.{ 120, 114, 106 }, .{ 104, 98, 92 }, n), l);
}

fn place(b: *Builder, e: K, x: f32, z: f32, yaw: f32) void {
    const y = t.height(x, z);

    b.putAt(kit.of(e), vec(x, y, z), yaw, 1);

    for (k.solids[@intFromEnum(e)]) |s| {
        const r = wd.rotBox(x, z, yaw, s[0], s[1], s[2], s[3]);

        b.solid(.{ .box = .{ .min = vec(r[0], y + s[4], r[1]), .max = vec(r[2], y + s[5], r[3]) } });
    }
}

fn put(b: *Builder, e: K, x: f32, z: f32, yaw: f32) void {
    b.put(kit.of(e), x, z, yaw, 1);
}

fn putY(b: *Builder, e: K, x: f32, y: f32, z: f32, yaw: f32) void {
    b.putAt(kit.of(e), vec(x, y, z), yaw, 1);
}

fn paint(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32, tone: api.Tone) void {
    b.deco(vec(x0, 0.012, z0), vec(x1, 0.04, z1), tone);
}

fn jitter(b: *Builder, a: f32) f32 {
    return b.rng.range(-a, a);
}

fn chance(b: *Builder, p: f32) bool {
    return b.rng.next() < p;
}

fn size(e: K) [2]f32 {
    const i = k.table[@intFromEnum(e)];

    return .{ i.max[0] - i.min[0], i.max[2] - i.min[2] };
}

fn roofOf(e: K) f32 {
    return k.roofs[@intFromEnum(e)];
}

const Side = struct { x: f32, z: f32, dx: f32, dz: f32, yaw: f32, len: f32, kind: Street, deep: f32 };

fn local(s: Side, along: f32, out: f32) [2]f32 {
    return .{ s.x + s.dx * along + @sin(s.yaw) * out, s.z + s.dz * along + @cos(s.yaw) * out };
}

fn pick(b: *Builder, s: Side, room: f32) K {
    const r = b.rng.next();
    const want: K = switch (s.kind) {
        .broadway => if (r < 0.16) .dept else if (r < 0.3) .theater else if (r < 0.42) .bank else if (r < 0.54) .office else if (r < 0.64) .prewar else if (r < 0.72) .slab else if (r < 0.78) .deco else if (r < 0.9) .shoprow else .diner,
        .avenue => if (r < 0.14) .office else if (r < 0.26) .prewar else if (r < 0.36) .slab else if (r < 0.48) .loft else if (r < 0.6) .shoprow else if (r < 0.7) .dept else if (r < 0.8) .garage else if (r < 0.9) .tenement else .diner,
        .street => if (r < 0.2) .tenement else if (r < 0.38) .brownstone else if (r < 0.5) .walkup else if (r < 0.62) .loft else if (r < 0.7) .cornerten else if (r < 0.78) .firehouse else if (r < 0.86) .repair else if (r < 0.92) .school else .garage,
        else => .brownstone,
    };

    const sz = size(want);

    if (sz[0] <= room and sz[1] <= s.deep) return want;

    const fallback = [_]K{ .brownstone, .tenement, .walkup, .loft, .office };
    const f = fallback[@intFromFloat(@floor(b.rng.range(0, 4.99)))];

    if (size(f)[0] <= room and size(f)[1] <= s.deep) return f;

    return .walkup;
}

fn frontage(b: *Builder, s: Side, e: K, along: f32, w: f32) void {
    const r = b.rng.next();
    const p = local(s, along + jitter(b, w * 0.3), 1.1);

    if (r < 0.12) {
        put(b, .newsstand, p[0], p[1], s.yaw);
    } else if (r < 0.24) {
        put(b, .can, p[0], p[1], 0);
        put(b, .can, p[0] + 0.7, p[1] + 0.2, 0.4);
    } else if (r < 0.32) {
        put(b, .mailbox, p[0], p[1], s.yaw);
    } else if (r < 0.4) {
        put(b, .bikerack, p[0], p[1], s.yaw + hp);
    } else if (r < 0.48 and s.kind != .street) {
        const q = local(s, along, 1.5);

        put(b, .dining, q[0], q[1], s.yaw);
    } else if (r < 0.55) {
        put(b, .hydrant, p[0], p[1], 0);
    }

    if (e == .shoprow or e == .diner or e == .cornershop) return;

    if (chance(b, 0.4)) {
        const a = local(s, along - w * 0.25, 0.45);

        putY(b, .awning, a[0], 2.6, a[1], s.yaw);
    }

    if (chance(b, 0.35)) {
        const g = local(s, along + w * 0.5 - 0.6, 0.3);

        putY(b, .sign, g[0], 3.0, g[1], s.yaw + hp);
    }

    if (e == .theater) {
        const g = local(s, along + w * 0.5 - 1.2, 0.45);

        putY(b, .theatersign, g[0], 4.0, g[1], s.yaw);
    }

    if ((e == .prewar or e == .slab or e == .deco or e == .office) and chance(b, 0.5)) {
        const c = local(s, along, 2);

        put(b, .canopy, c[0], c[1], s.yaw);
    }
}

fn rooftop(b: *Builder, e: K, x: f32, z: f32, yaw: f32) void {
    const h = roofOf(e);

    if (h < 4 or h > 30) return;

    const sz = size(e);
    const r = b.rng.next();

    if (r < 0.35) {
        const p = wd.rotPoint(x, z, yaw, b.rng.range(-sz[0] * 0.25, sz[0] * 0.25), -sz[1] * 0.2);

        b.putAt(kit.of(.ac), vec(p[0], h, p[1]), yaw, 1);
        b.putAt(kit.of(.ac), vec(p[0] + 1.8, h, p[1]), yaw, 1);
    } else if (r < 0.55) {
        const p = wd.rotPoint(x, z, yaw, 0, sz[1] * 0.25);

        b.putAt(kit.of(.billboard), vec(p[0], h, p[1]), yaw, 1);
    } else if (r < 0.75) {
        const p = wd.rotPoint(x, z, yaw, sz[0] * 0.2, -sz[1] * 0.15);

        b.putAt(kit.of(.watertower), vec(p[0], h, p[1]), 0, 1);
    }
}

fn wallDress(b: *Builder, s: Side, along: f32, back: f32) void {
    const c = local(s, along, -back - 0.05);

    if (chance(b, 0.5)) putY(b, .wallad, c[0], 2.5, c[1], s.yaw + pi);

    const d = local(s, along + 2, -back - 1.0);

    if (chance(b, 0.6)) put(b, .dumpster, d[0], d[1], s.yaw);

    if (chance(b, 0.5)) put(b, .can, d[0] + 1.6, d[1], 0);
}

fn lineSide(b: *Builder, s: Side) void {
    var a: f32 = 0;
    var gap_done = s.kind == .street and s.len < 20;

    while (a < s.len - 3.9) {
        const room = s.len - a;

        if (!gap_done and a > s.len * 0.4) {
            gap_done = true;

            const g = local(s, a + 0.6, 0.8);

            put(b, .can, g[0], g[1], 0);

            const wa = local(s, a + 0.05, -4.5);
            const wb = local(s, a + 4.95, -4.5);

            putY(b, .wallad, wa[0], 0.3, wa[1], s.yaw - hp);
            putY(b, .wallad, wb[0], 0.3, wb[1], s.yaw + hp);
            a += 5;

            continue;
        }

        const e = pick(b, s, room);
        const sz = size(e);
        const c = local(s, a + sz[0] / 2, -sz[1] / 2);

        place(b, e, c[0], c[1], s.yaw);
        rooftop(b, e, c[0], c[1], s.yaw);
        frontage(b, s, e, a + sz[0] / 2, sz[0]);

        if (chance(b, 0.3)) wallDress(b, s, a + sz[0] / 2, sz[1]);

        backDress(b, s, e, a + sz[0] / 2, sz[0], sz[1]);

        a += sz[0];
    }
}

fn rank(s: Street) u8 {
    return @intFromEnum(s);
}

fn rowBlock(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32, kw: Street, ke: Street, ks: Street, kn: Street) void {
    const c: f32 = 8.85;
    const ns_deep = (z1 - z0) / 2 - 1;
    const ss = [_]Side{
        .{ .x = x0 + c, .z = z0, .dx = 1, .dz = 0, .yaw = pi, .len = x1 - x0 - 2 * c, .kind = ks, .deep = ns_deep },
        .{ .x = x1 - c, .z = z1, .dx = -1, .dz = 0, .yaw = 0, .len = x1 - x0 - 2 * c, .kind = kn, .deep = ns_deep },
        .{ .x = x0, .z = z1 - c, .dx = 0, .dz = -1, .yaw = -hp, .len = z1 - z0 - 2 * c, .kind = kw, .deep = 9.5 },
        .{ .x = x1, .z = z0 + c, .dx = 0, .dz = 1, .yaw = hp, .len = z1 - z0 - 2 * c, .kind = ke, .deep = 9.5 },
    };

    for (ss) |s| {
        if (s.kind == .alley) {
            alleySide(b, s);

            continue;
        }

        lineSide(b, if (s.kind == .edge) Side{ .x = s.x, .z = s.z, .dx = s.dx, .dz = s.dz, .yaw = s.yaw, .len = s.len, .kind = .street, .deep = s.deep } else s);
    }

    const corners = [_][4]f32{ .{ x0 + c / 2, z0 + c / 2, 2, 0 }, .{ x1 - c / 2, z0 + c / 2, 3, 0 }, .{ x0 + c / 2, z1 - c / 2, 2, 1 }, .{ x1 - c / 2, z1 - c / 2, 3, 1 } };

    for (corners) |q| {
        const sa = ss[@intFromFloat(q[2])];
        const so = ss[@intFromFloat(q[3])];

        if (sa.kind == .alley and so.kind == .alley) continue;

        const yaw = if (rank(sa.kind) >= rank(so.kind)) sa.yaw else so.yaw;

        if (sa.kind == .alley or so.kind == .alley) {
            place(b, .brownstone, q[0], q[1], yaw);
        } else {
            place(b, .cornershop, q[0], q[1], yaw);
        }
    }

    courtyard(b, x0 + 1, z0 + 1, x1 - 1, z1 - 1);
}

fn alleySide(b: *Builder, s: Side) void {
    var a: f32 = 2;

    while (a < s.len - 2) : (a += 4) {
        const p = local(s, a, 0.6);
        const r = b.rng.next();

        if (r < 0.22) {
            put(b, .dumpster, p[0], p[1], s.yaw + hp);
        } else if (r < 0.4) {
            put(b, .can, p[0], p[1], 0);
            put(b, .can, p[0] + 0.6, p[1] + 0.4, 0);
        } else if (r < 0.5) {
            put(b, .steam, p[0], p[1], 0);
        } else if (r < 0.6) {
            put(b, .barricade, p[0], p[1], s.yaw);
        }
    }

    var w: f32 = 0;

    while (w < s.len) : (w += 4) {
        if (@abs(w + 2 - s.len * 0.3) < 3 or @abs(w + 2 - s.len * 0.75) < 3) continue;

        const p = local(s, w + 2, -0.15);

        put(b, .hoarding, p[0], p[1], s.yaw);
    }
}

fn atl(b: *Builder, e: K, cx: f32, cz: f32, yaw: f32, lx: f32, lz: f32, y: f32, turn: f32) void {
    const p = wd.rotPoint(cx, cz, yaw, lx, lz);

    b.putAt(kit.of(e), vec(p[0], t.height(p[0], p[1]) + y, p[1]), yaw + turn, 1);
}

fn clear(b: *Builder, cx: f32, cz: f32, r: f32) bool {
    for ([_][2]f32{ .{ 0, 0 }, .{ -1, -1 }, .{ 1, -1 }, .{ -1, 1 }, .{ 1, 1 }, .{ 0, 1 }, .{ 0, -1 }, .{ 1, 0 }, .{ -1, 0 } }) |o| {
        if (wd.covered(b, cx + o[0] * r, cz + o[1] * r, 0.6)) return false;
    }

    return true;
}

fn stack(b: *Builder, cx: f32, cz: f32, yaw: f32, lx: f32, lz: f32, n: usize) void {
    var i: usize = 0;

    while (i < n) : (i += 1) atl(b, .pallet, cx, cz, yaw, lx, lz, @as(f32, @floatFromInt(i)) * 0.14, jitter(b, 0.08));
}

fn fenceRun(b: *Builder, cx: f32, cz: f32, yaw: f32, lx0: f32, lz0: f32, lx1: f32, lz1: f32, gap: f32) void {
    const dx = lx1 - lx0;
    const dz = lz1 - lz0;
    const len = @sqrt(dx * dx + dz * dz);
    const n: usize = @intFromFloat(@max(1, @round(len / 4)));
    const turn = std.math.atan2(dz, dx);
    var i: usize = 0;

    while (i < n) : (i += 1) {
        const u = (@as(f32, @floatFromInt(i)) + 0.5) / @as(f32, @floatFromInt(n));

        if (gap >= 0 and @abs(u - gap) < 0.5 / @as(f32, @floatFromInt(n))) continue;

        atl(b, .chainlink, cx, cz, yaw, lx0 + dx * u, lz0 + dz * u, 0, -turn);
    }
}

fn loading(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    atl(b, .palletload, cx, cz, yaw, -2.8, -2.4, 0, 0);
    atl(b, .palletload, cx, cz, yaw, -1.6, -2.4, 0, 0.1);
    atl(b, .palletload, cx, cz, yaw, -2.8, -1.3, 0, -0.1);
    atl(b, .palletload, cx, cz, yaw, -2.8, -1.3, 1.21, 0);
    stack(b, cx, cz, yaw, 1.4, -2.6, 4);
    stack(b, cx, cz, yaw, 2.8, -2.6, 2);
    atl(b, .crates, cx, cz, yaw, 2.2, 0.4, 0, 0.3);
    atl(b, .crates, cx, cz, yaw, -0.4, 1.6, 0, hp);
    atl(b, .drum, cx, cz, yaw, 3.2, 2.6, 0, 0);
    atl(b, .drum, cx, cz, yaw, 3.8, 2.4, 0, 0.5);
    atl(b, .drum, cx, cz, yaw, 3.4, 3.2, 0, 1);
    atl(b, .hvac, cx, cz, yaw, -3.2, 2.6, 0, 0);
    atl(b, .hvac, cx, cz, yaw, -2.1, 2.6, 0, 0);
}

fn binYard(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    atl(b, .dumpster, cx, cz, yaw, -1.7, -2.4, 0, 0);
    atl(b, .dumpster, cx, cz, yaw, 1.6, -2.3, 0, 0.05);
    atl(b, .can, cx, cz, yaw, -3.6, -0.6, 0, 0);
    atl(b, .can, cx, cz, yaw, -3.1, 0.1, 0, 0.6);
    atl(b, .can, cx, cz, yaw, -3.7, 0.5, 0, 1.2);
    atl(b, .drum, cx, cz, yaw, 3.6, -0.2, 0, 0);
    atl(b, .crates, cx, cz, yaw, 2.6, 2.4, 0, 0.6);
    stack(b, cx, cz, yaw, -1, 2.6, 3);
    fenceRun(b, cx, cz, yaw, -4, -3.8, 4, -3.8, -1);
    fenceRun(b, cx, cz, yaw, -4.1, -3.6, -4.1, 0.4, -1);
}

fn market(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    atl(b, .stall, cx, cz, yaw, -2.4, -0.6, 0, 0);
    atl(b, .stall, cx, cz, yaw, 1.6, -0.6, 0, 0);
    atl(b, .crates, cx, cz, yaw, -2.6, 1.8, 0, 0.2);
    atl(b, .crates, cx, cz, yaw, 1.4, 1.9, 0, -0.3);
    atl(b, .planterbox, cx, cz, yaw, -4.2, 3, 0, 0);
    atl(b, .planterbox, cx, cz, yaw, 4.2, 3, 0, 0);
    atl(b, .planterbox, cx, cz, yaw, 4.2, -3, 0, 0);
    atl(b, .picnic, cx, cz, yaw, -0.4, 3.6, 0, 0);
    atl(b, .can, cx, cz, yaw, 3.6, 1.2, 0, 0);
    atl(b, .palletload, cx, cz, yaw, -4.2, -2.6, 0, 0.3);
}

fn scaffoldTower(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    for ([_]f32{ -2, 2 }) |lx| {
        atl(b, .scaffold, cx, cz, yaw, lx, -1.5, 0, 0);
        atl(b, .scaffold, cx, cz, yaw, lx, -1.5, 3, 0);
    }

    const p = wd.rotPoint(cx, cz, yaw, 0, -1.5);
    const y = t.height(p[0], p[1]);
    const r = wd.rotBox(p[0], p[1], yaw, -4, -1, 4, 1);

    b.deco(vec(r[0], y + 2.9, r[1]), vec(r[2], y + 3.05, r[3]), .f_wood_pallet);
    b.solid(.{ .box = .{ .min = vec(r[0], y + 2.9, r[1]), .max = vec(r[2], y + 3.05, r[3]) } });
    atl(b, .hoarding, cx, cz, yaw, -2, 1.4, 0, 0);
    atl(b, .palletload, cx, cz, yaw, 2.2, 1.6, 0, 0.2);
    atl(b, .palletload, cx, cz, yaw, 3.3, 1.7, 0, -0.1);
    stack(b, cx, cz, yaw, 1.2, 3.2, 3);
    atl(b, .barricade, cx, cz, yaw, -2.4, 3.4, 0, 0);
    atl(b, .cone, cx, cz, yaw, 0, 3.4, 0, 0);
}

fn plant(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    atl(b, .generator, cx, cz, yaw, 0, -2.2, 0, 0);
    atl(b, .hvac, cx, cz, yaw, -3.4, 1.4, 0, 0);
    atl(b, .hvac, cx, cz, yaw, -2.3, 1.4, 0, 0);
    atl(b, .hvac, cx, cz, yaw, -1.2, 1.4, 0, 0);
    atl(b, .drum, cx, cz, yaw, 2.8, 1.2, 0, 0);
    atl(b, .drum, cx, cz, yaw, 3.4, 1.5, 0, 0.4);
    atl(b, .barricade, cx, cz, yaw, 2.2, 3.4, 0, 0);
    atl(b, .cone, cx, cz, yaw, 0.4, 3.3, 0, 0);
    fenceRun(b, cx, cz, yaw, -4, -4, 4, -4, -1);
    fenceRun(b, cx, cz, yaw, 4.1, -3.8, 4.1, 0.2, -1);
}

fn picnicYard(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    atl(b, .picnic, cx, cz, yaw, -1.8, -1.2, 0, 0);
    atl(b, .picnic, cx, cz, yaw, 1.8, 1.2, 0, 0.1);
    atl(b, .tree, cx, cz, yaw, 3, -2.6, 0, 0);
    atl(b, .tree, cx, cz, yaw, -3, 2.8, 0, 1);

    for ([_][2]f32{ .{ -4, -3.6 }, .{ -2.8, -3.6 }, .{ 4, 3.6 }, .{ 2.8, 3.6 }, .{ 4.1, -0.4 } }) |q| atl(b, .planterbox, cx, cz, yaw, q[0], q[1], 0, 0);

    atl(b, .can, cx, cz, yaw, -4, 0.8, 0, 0);
    atl(b, .globe, cx, cz, yaw, 0, -3.8, 0, 0);
}

fn fencedLot(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    fenceRun(b, cx, cz, yaw, -4, -4, 4, -4, -1);
    fenceRun(b, cx, cz, yaw, -4, 4, 4, 4, 0.25);
    fenceRun(b, cx, cz, yaw, -4, -4, -4, 4, -1);
    fenceRun(b, cx, cz, yaw, 4, -4, 4, 4, 0.75);

    for ([_][2]f32{ .{ -2.6, -2.6 }, .{ -1.5, -2.7 }, .{ -2.7, -1.5 }, .{ 2.5, 2.2 } }) |q| atl(b, .palletload, cx, cz, yaw, q[0], q[1], 0, jitter(b, 0.2));

    atl(b, .crates, cx, cz, yaw, 1.6, -2.4, 0, 0.1);
    atl(b, .crates, cx, cz, yaw, 1.6, -2.4, 0.9, 0.4);
    stack(b, cx, cz, yaw, -2.4, 2.4, 5);
    atl(b, .drum, cx, cz, yaw, 0.4, 0.6, 0, 0);
    atl(b, .drum, cx, cz, yaw, 1, 0.9, 0, 0);
}

fn court(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    const y = t.height(cx, cz);
    const r = wd.rotBox(cx, cz, yaw, -3.4, -4.4, 3.4, 4.4);

    b.deco(vec(r[0], y + 0.01, r[1]), vec(r[2], y + 0.03, r[3]), .f_mint_dark);
    atl(b, .hoop, cx, cz, yaw, 0, -3.8, 0, 0);
    atl(b, .hoop, cx, cz, yaw, 0, 3.8, 0, std.math.pi);
    fenceRun(b, cx, cz, yaw, -4.4, -4.6, 4.4, -4.6, -1);
    fenceRun(b, cx, cz, yaw, -4.6, -4.4, -4.6, 4.4, 0.5);
    fenceRun(b, cx, cz, yaw, 4.6, -4.4, 4.6, 4.4, 0.5);
    atl(b, .bench, cx, cz, yaw, 3.6, 4.8, 0, 0);
}

fn stackYard(b: *Builder, cx: f32, cz: f32, yaw: f32) void {
    var lx: f32 = -3.4;

    while (lx < 3.5) : (lx += 1.1) {
        atl(b, .palletload, cx, cz, yaw, lx, -2.6, 0, jitter(b, 0.05));

        if (@abs(lx) > 0.8) atl(b, .palletload, cx, cz, yaw, lx, -2.6, 1.21, jitter(b, 0.08));
    }

    atl(b, .crates, cx, cz, yaw, -2.6, 0.6, 0, 0);
    atl(b, .crates, cx, cz, yaw, -2.6, 0.6, 0.9, 0.3);
    atl(b, .crates, cx, cz, yaw, 2.4, 1.2, 0, -0.2);
    stack(b, cx, cz, yaw, 0, 1.6, 6);
    stack(b, cx, cz, yaw, 1.3, 3, 2);
    atl(b, .dumpster, cx, cz, yaw, -1.4, 3.4, 0, 0);
    atl(b, .drum, cx, cz, yaw, 3.6, -0.4, 0, 0);
}

fn cluster(b: *Builder, cx: f32, cz: f32) void {
    const yaw = @round(b.rng.range(0, 4)) * hp;
    const r = b.rng.next();

    if (r < 0.16) loading(b, cx, cz, yaw) else if (r < 0.28) binYard(b, cx, cz, yaw) else if (r < 0.4) market(b, cx, cz, yaw) else if (r < 0.54) scaffoldTower(b, cx, cz, yaw) else if (r < 0.64) plant(b, cx, cz, yaw) else if (r < 0.72) picnicYard(b, cx, cz, yaw) else if (r < 0.82) fencedLot(b, cx, cz, yaw) else if (r < 0.94) stackYard(b, cx, cz, yaw) else court(b, cx, cz, yaw);
}

fn small(b: *Builder, cx: f32, cz: f32) void {
    const yaw = @round(b.rng.range(0, 4)) * hp + jitter(b, 0.1);
    const r = b.rng.next();

    if (r < 0.25) {
        atl(b, .palletload, cx, cz, yaw, -0.6, -0.5, 0, 0);
        atl(b, .palletload, cx, cz, yaw, 0.5, -0.5, 0, 0.1);
        stack(b, cx, cz, yaw, 0, 0.9, 3);
        atl(b, .crates, cx, cz, yaw, 1.4, 1.2, 0, 0.4);
    } else if (r < 0.45) {
        atl(b, .dumpster, cx, cz, yaw, 0, 0, 0, 0);
        atl(b, .can, cx, cz, yaw, 1.9, 0.2, 0, 0);
        atl(b, .can, cx, cz, yaw, 1.9, -0.6, 0, 0.5);
    } else if (r < 0.6) {
        atl(b, .hvac, cx, cz, yaw, -1.1, 0, 0, 0);
        atl(b, .hvac, cx, cz, yaw, 0, 0, 0, 0);
        atl(b, .hvac, cx, cz, yaw, 1.1, 0, 0, 0);
        atl(b, .drum, cx, cz, yaw, 0.4, 1.3, 0, 0);
    } else if (r < 0.75) {
        atl(b, .chainlink, cx, cz, yaw, 0, -1, 0, 0);
        atl(b, .crates, cx, cz, yaw, -0.8, 0.2, 0, 0);
        atl(b, .drum, cx, cz, yaw, 0.9, 0.1, 0, 0);
        atl(b, .drum, cx, cz, yaw, 1.5, 0.3, 0, 0);
    } else if (r < 0.88) {
        atl(b, .barricade, cx, cz, yaw, 0, 0, 0, 0);
        atl(b, .cone, cx, cz, yaw, 1.6, 0.4, 0, 0);
        atl(b, .palletload, cx, cz, yaw, -0.4, 1.1, 0, 0.2);
    } else {
        atl(b, .planterbox, cx, cz, yaw, -0.6, 0, 0, 0);
        atl(b, .planterbox, cx, cz, yaw, 0.6, 0, 0, 0);
        atl(b, .picnic, cx, cz, yaw, 0, 1.6, 0, 0);
    }
}

fn backDress(b: *Builder, s: Side, e: K, along: f32, w: f32, deep: f32) void {
    const h = roofOf(e);

    switch (e) {
        .tenement, .brownstone, .walkup, .cornerten, .loft, .prewar, .slab, .school => {},
        else => return,
    }

    if (chance(b, 0.75)) {
        const p = local(s, along + jitter(b, w * 0.2), -deep - 0.7);
        var y: f32 = 3.2;

        while (y + 4.1 < h) : (y += 4.13) putY(b, .escape, p[0], t.height(p[0], p[1]) + y, p[1], s.yaw + pi);
    }

    if (chance(b, 0.6)) {
        const q = local(s, along - w * 0.3, -deep - 0.6);

        put(b, .hvac, q[0], q[1], s.yaw + pi);

        const q2 = local(s, along - w * 0.3 + 1.1, -deep - 0.6);

        put(b, .hvac, q2[0], q2[1], s.yaw + pi);
    }
}

fn courtyard(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32) void {
    const inner = [_]K{ .repair, .shoprow, .diner, .firehouse, .shoprow };
    var m: usize = 0;
    var built: usize = 0;

    while (m < 14 and built < 1) : (m += 1) {
        const e = inner[@intFromFloat(@floor(b.rng.range(0, 4.99)))];
        const sz = size(e);
        const yaw = @round(b.rng.range(0, 4)) * hp;
        const r = @max(sz[0], sz[1]) / 2 + 1.5;
        const px = b.rng.range(x0 + r, x1 - r);
        const pz = b.rng.range(z0 + r, z1 - r);

        if (x1 - x0 < 2 * r or z1 - z0 < 2 * r) continue;

        var free = true;

        for ([_][2]f32{ .{ 0, 0 }, .{ -1, -1 }, .{ 1, -1 }, .{ -1, 1 }, .{ 1, 1 }, .{ 0, 1 }, .{ 0, -1 }, .{ 1, 0 }, .{ -1, 0 } }) |o| {
            if (wd.covered(b, px + o[0] * (r - 1), pz + o[1] * (r - 1), 1.2)) free = false;
        }

        if (!free) continue;

        place(b, e, px, pz, yaw);
        built += 1;
    }

    var tries: usize = 0;

    while (tries < 120) : (tries += 1) {
        const cx = b.rng.range(x0 + 4, x1 - 4);
        const cz = b.rng.range(z0 + 4, z1 - 4);

        if (clear(b, cx, cz, 4.0)) cluster(b, cx, cz);
    }

    tries = 0;

    while (tries < 260) : (tries += 1) {
        const cx = b.rng.range(x0 + 2, x1 - 2);
        const cz = b.rng.range(z0 + 2, z1 - 2);

        if (clear(b, cx, cz, 2.2)) small(b, cx, cz);
    }

    var n: usize = 0;

    while (n < 160) : (n += 1) {
        const px = b.rng.range(x0, x1);
        const pz = b.rng.range(z0, z1);

        if (wd.covered(b, px, pz, 1.2)) continue;

        const r = b.rng.next();
        const yaw = @round(b.rng.range(0, 4)) * hp + jitter(b, 0.15);

        if (r < 0.06) {
            put(b, .dumpster, px, pz, yaw);
        } else if (r < 0.16) {
            put(b, .tree, px, pz, b.rng.range(0, 6));
            put(b, .planterbox, px + 1.2, pz + 0.4, 0);
        } else if (r < 0.26) {
            put(b, .can, px, pz, 0);
            put(b, .can, px + 0.7, pz + 0.3, 0);
        } else if (r < 0.38) {
            stack(b, px, pz, yaw, 0, 0, 3);
            put(b, .palletload, px + 1.3, pz, yaw);
        } else if (r < 0.5) {
            put(b, .crates, px, pz, yaw);
        } else if (r < 0.6) {
            put(b, .hvac, px, pz, yaw);
            put(b, .hvac, px + 1.1, pz, yaw);
        } else if (r < 0.7) {
            put(b, .drum, px, pz, 0);
            put(b, .drum, px + 0.65, pz + 0.2, 0.4);
        } else if (r < 0.78) {
            put(b, .barricade, px, pz, yaw);
        } else if (r < 0.85) {
            put(b, .steam, px, pz, 0);
        } else if (r < 0.93) {
            put(b, .planterbox, px, pz, 0);
        } else {
            put(b, .chainlink, px, pz, yaw);
        }
    }
}

fn park(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32) void {
    const cx = (x0 + x1) / 2;
    const cz = (z0 + z1) / 2;
    var a: f32 = x0 + 2;

    while (a < x1 - 1) : (a += 4) {
        if (@abs(a - cx) > 3) {
            put(b, .railing, a, z0 + 0.3, 0);
            put(b, .railing, a, z1 - 0.3, 0);
        }
    }

    var c: f32 = z0 + 2;

    while (c < z1 - 1) : (c += 4) {
        if (@abs(c - cz) > 3) {
            put(b, .railing, x0 + 0.3, c, hp);
            put(b, .railing, x1 - 0.3, c, hp);
        }
    }

    paint(b, cx - 2, z0, cx + 2, z1, .sandbag);
    paint(b, x0, cz - 2, x1, cz + 2, .sandbag);

    var tx: f32 = x0 + 5;

    while (tx < x1 - 3) : (tx += 7) {
        var tz: f32 = z0 + 5;

        while (tz < z1 - 3) : (tz += 8) {
            if (@abs(tx - cx) < 4 or @abs(tz - cz) < 4) continue;

            put(b, .tree, tx + jitter(b, 1.5), tz + jitter(b, 1.5), b.rng.range(0, 6));
        }
    }

    for ([_]f32{ -1, 1 }) |sd| {
        put(b, .bench, cx + sd * 3.4, cz + 8, sd * hp);
        put(b, .bench, cx + sd * 3.4, cz - 8, sd * hp);
        put(b, .globe, cx + sd * 3, cz + 3, 0);
        put(b, .globe, cx + sd * 3, cz - 3, 0);
        put(b, .bench, cx + 8, cz + sd * 3.4, if (sd < 0) 0 else pi);
    }

    put(b, .hotdog, cx + 1, cz + 14, 0.4);
    put(b, .newsstand, cx - 2.6, z0 + 3, pi);
    put(b, .can, cx + 2.6, z0 + 2.5, 0);
}

fn plazaBlock(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32) void {
    const cx = (x0 + x1) / 2;
    const cz = (z0 + z1) / 2;

    place(b, .deco, cx + 4, cz + 6, -hp);

    for ([_]f32{ -20, -12, 12, 20 }) |dz| {
        put(b, .dining, cx - 12, cz + dz, hp);
        put(b, .tree, cx - 16, cz + dz + 3, b.rng.range(0, 6));
        put(b, .bench, cx - 8, cz + dz + 2, -hp);
    }
    place(b, .subway, cx - 12, z0 + 6, pi);
    place(b, .subway, cx + 12, z1 - 6, 0);

    for ([_]f32{ -1, 1 }) |sd| {
        put(b, .tree, cx + sd * 12, cz - 12, b.rng.range(0, 6));
        put(b, .tree, cx + sd * 12, cz - 20, b.rng.range(0, 6));
        put(b, .bench, cx + sd * 8, cz - 16, hp);
        put(b, .globe, cx + sd * 5, z0 + 3, 0);
        put(b, .bollard, cx + sd * 2, z0 + 1, 0);
        put(b, .bollard, cx + sd * 4, z0 + 1, 0);
    }

    put(b, .newsstand, cx + 10, z0 + 14, hp);
    put(b, .hotdog, cx - 4, z0 + 10, 0.3);
    put(b, .newsstand, cx + 4, cz - 8, pi);
    put(b, .dining, cx - 9, cz - 6, hp);
}

fn site(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32) void {
    var a: f32 = x0 + 2;

    while (a < x1 - 1) : (a += 4) {
        if (@abs(a - (x0 + x1) / 2) > 4) {
            put(b, .hoarding, a, z0 + 0.4, pi);
            put(b, .hoarding, a, z1 - 0.4, 0);
        }
    }

    var c: f32 = z0 + 2;

    while (c < z1 - 1) : (c += 4) {
        put(b, .hoarding, x0 + 0.4, c, -hp);
        put(b, .hoarding, x1 - 0.4, c, hp);
    }

    const fx0 = x0 + 6;
    const fz0 = z0 + 10;
    const fw: f32 = 24;
    const fd: f32 = 22;
    const levels = [_]f32{ 4.2, 8.4, 12.6 };

    for (levels, 0..) |y, li| {
        const hole_x = if (li % 2 == 0) fx0 + fw - 4 else fx0;

        b.mass(vec(fx0, y - 0.35, fz0), vec(hole_x, y, fz0 + fd), .concrete);
        b.mass(vec(hole_x + 4, y - 0.35, fz0), vec(fx0 + fw, y, fz0 + fd), .concrete);
        b.mass(vec(hole_x, y - 0.35, fz0 + 13), vec(hole_x + 4, y, fz0 + fd), .concrete);

        var px: f32 = fx0;

        while (px <= fx0 + fw) : (px += 6) {
            var pz: f32 = fz0;

            while (pz <= fz0 + fd) : (pz += 5.5) {
                b.mass(vec(px - 0.3, y - 4.2, pz - 0.3), vec(px + 0.3, y - 0.35, pz + 0.3), .f_grey);
            }
        }

        const r0 = y - 4.2;
        const rz0 = fz0 + 0.2;
        const rz1 = fz0 + 13;
        const rx0 = hole_x + 0.3;
        const rx1 = hole_x + 3.7;

        b.solid(.{ .ramp = .{ .min = vec(rx0, r0, rz0), .max = vec(rx1, y, rz1), .rise = .pos_z } });

        const n: usize = 16;
        var i: usize = 0;

        while (i < n) : (i += 1) {
            const f = @as(f32, @floatFromInt(i)) / @as(f32, @floatFromInt(n));
            const za = rz0 + (rz1 - rz0) * f;
            const zb = za + (rz1 - rz0) / @as(f32, @floatFromInt(n));
            const sy = r0 + (y - r0) * (f + 1 / @as(f32, @floatFromInt(n)));

            b.deco(vec(rx0, sy - 0.15, za), vec(rx1, sy, zb), .concrete);
            b.deco(vec(rx0 - 0.1, sy + 0.95, za), vec(rx0, sy + 1.05, zb), .f_metal);
        }

        if (li == levels.len - 1) {
            b.deco(vec(fx0, y, fz0), vec(fx0 + fw, y + 1.0, fz0 + 0.12), .f_metal);
            b.deco(vec(fx0, y, fz0 + fd - 0.12), vec(fx0 + fw, y + 1.0, fz0 + fd), .f_metal);
        }
    }

    for ([_][2]f32{ .{ fx0 + 3, fz0 + 4 }, .{ fx0 + 14, fz0 + 16 }, .{ fx0 + 20, fz0 + 6 } }) |p| {
        put(b, .dumpster, p[0], p[1], 0.3);
    }

    for ([_][2]f32{ .{ fx0 + 8, fz0 + 9 }, .{ fx0 + 16, fz0 + 3 } }) |p| {
        putY(b, .ac, p[0], 4.2, p[1], 0);
        putY(b, .dumpster, p[0] + 4, 8.4, p[1] + 6, hp);
    }

    var sx: f32 = fx0;

    while (sx < fx0 + fw) : (sx += 4) {
        put(b, .scaffold, sx + 2, fz0 - 1.2, 0);
        putY(b, .scaffold, sx + 2, 3, fz0 - 1.2, 0);
    }

    for ([_][2]f32{ .{ x0 + 4, z1 - 6 }, .{ x1 - 6, z1 - 6 }, .{ x1 - 4, z0 + 4 } }) |p| {
        put(b, .cone, p[0], p[1], 0);
        put(b, .cone, p[0] + 1, p[1] + 0.6, 0);
        put(b, .barricade, p[0] + 2, p[1], 0);
    }

    put(b, .dumpster, x1 - 6, z0 + 14, 0);
    put(b, .dumpster, x0 + 4, z1 - 14, 0.1);

    var n: usize = 0;

    var tries: usize = 0;

    while (tries < 60) : (tries += 1) {
        const cx = b.rng.range(x0 + 5, x1 - 5);
        const cz = b.rng.range(z0 + 5, z1 - 5);

        if (!clear(b, cx, cz, 3.6)) continue;

        const yaw = @round(b.rng.range(0, 4)) * hp;

        if (chance(b, 0.4)) stackYard(b, cx, cz, yaw) else if (chance(b, 0.5)) loading(b, cx, cz, yaw) else plant(b, cx, cz, yaw);
    }

    while (n < 90) : (n += 1) {
        const px = b.rng.range(x0 + 3, x1 - 3);
        const pz = b.rng.range(z0 + 3, z1 - 3);

        if (wd.covered(b, px, pz, 2.0)) continue;

        const r = b.rng.next();
        const yaw = @round(b.rng.range(0, 4)) * hp;

        if (r < 0.2) {
            if (chance(b, 0.5)) small(b, px, pz) else put(b, .dumpster, px, pz, yaw);
        } else if (r < 0.4) {
            put(b, .scaffold, px, pz, yaw);

            if (chance(b, 0.5)) putY(b, .scaffold, px, 3, pz, yaw);
        } else if (r < 0.55) {
            put(b, .hoarding, px, pz, yaw);
        } else if (r < 0.7) {
            b.mass(vec(px - 1.6, 0, pz - 1.2), vec(px + 1.6, 0.9, pz + 1.2), .sandbag);
            b.deco(vec(px - 1.0, 0.9, pz - 0.7), vec(px + 1.0, 1.4, pz + 0.7), .sandbag);
        } else if (r < 0.85) {
            put(b, .barricade, px, pz, yaw);
            put(b, .cone, px + 1.5, pz, 0);
        } else {
            put(b, .hoarding, px, pz, yaw);
        }
    }
}

fn streets(b: *Builder) void {
    for (xs) |l| {
        if (l.kind == .edge) continue;

        if (l.kind == .alley) continue;

        furniture(b, l.at - l.hw + 0.8, l.at + l.hw - 0.8, true, l.kind);

        if (l.kind == .broadway) {
            median(b);
        } else {
            dashes(b, l.at, true);
        }
    }

    for (zs) |l| {
        if (l.kind == .edge) continue;

        furniture(b, l.at - l.hw + 0.8, l.at + l.hw - 0.8, false, l.kind);
        dashes(b, l.at, false);
    }

    for (xs) |lx| {
        if (lx.kind == .edge or lx.kind == .alley) continue;

        for (zs) |lz| {
            if (lz.kind == .edge) continue;

            crossing(b, lx, lz);
        }
    }
}

fn furniture(b: *Builder, a0: f32, a1: f32, along_z: bool, kind: Street) void {
    var a: f32 = -edge + 6;

    while (a < edge - 6) : (a += 12) {
        if (near(a, if (along_z) &zs else &xs) != null) continue;

        for ([_]f32{ a0, a1 }, 0..) |o, si| {
            const x = if (along_z) o else a;
            const z = if (along_z) a else o;
            const face: f32 = if (along_z) (if (si == 0) hp else -hp) else (if (si == 0) 0 else pi);

            if (@mod(a, 24) < 12) {
                put(b, if (kind == .broadway) .globe else .lamp, x, z, face);
            } else if (chance(b, 0.7)) {
                put(b, .tree, x, z, b.rng.range(0, 6));
            }

            const hx: f32 = if (along_z) 0 else 3;

            if (chance(b, 0.12)) put(b, .hydrant, x + hx, z + 3 - hx, 0);
        }
    }
}

fn dashes(b: *Builder, at: f32, along_z: bool) void {
    var a: f32 = -edge;

    while (a < edge) : (a += 9) {
        if (near(a + 2, if (along_z) &zs else &xs)) |s| {
            if (s.kind != .alley) continue;
        }

        if (along_z) paint(b, at - 0.1, a, at + 0.1, a + 4.5, .paint_line) else paint(b, a, at - 0.1, a + 4.5, at + 0.1, .marking);
    }
}

fn median(b: *Builder) void {
    var z: f32 = -edge + 4;

    while (z < edge - 4) : (z += 4) {
        if (near(z, &zs) != null) continue;

        b.deco(vec(-4, 0, z - 2), vec(-3.7, 0.2, z + 2), .concrete);
        b.deco(vec(3.7, 0, z - 2), vec(4, 0.2, z + 2), .concrete);

        const m = @mod(z + edge, 24);

        if (m < 4) {
            put(b, .tree, -1.6, z, b.rng.range(0, 6));
            put(b, .tree, 1.6, z + 2, b.rng.range(0, 6));
        } else if (m < 8) {
            put(b, .bench, 0, z, hp);
        } else if (m < 12 and chance(b, 0.6)) {
            put(b, if (chance(b, 0.5)) .newsstand else .hotdog, 0, z, if (chance(b, 0.5)) hp else -hp);
        } else if (m < 16) {
            put(b, .globe, 0, z, 0);
        }
    }

    place(b, .subway, -1.5, -60, 0);
    place(b, .subway, 1.5, 70, pi);
}

fn crossing(b: *Builder, lx: Line, lz: Line) void {
    const ex = lx.hw;
    const ez = lz.hw;
    var c: f32 = -ex + 1;

    while (c < ex - 1) : (c += 1.3) {
        paint(b, lx.at + c, lz.at - ez - 2.6, lx.at + c + 0.65, lz.at - ez - 0.4, .marking);
        paint(b, lx.at + c, lz.at + ez + 0.4, lx.at + c + 0.65, lz.at + ez + 2.6, .marking);
    }

    var d: f32 = -ez + 1;

    while (d < ez - 1) : (d += 1.3) {
        paint(b, lx.at - ex - 2.6, lz.at + d, lx.at - ex - 0.4, lz.at + d + 0.65, .marking);
        paint(b, lx.at + ex + 0.4, lz.at + d, lx.at + ex + 2.6, lz.at + d + 0.65, .marking);
    }

    put(b, .light, lx.at - ex + 0.6, lz.at - ez - 0.6, pi);
    put(b, .light, lx.at + ex - 0.6, lz.at + ez + 0.6, 0);
    put(b, .light, lx.at - ex - 0.6, lz.at + ez - 0.6, -hp);
    put(b, .light, lx.at + ex + 0.6, lz.at - ez + 0.6, hp);
}

fn traffic(b: *Builder) void {
    const cars = [_]K{ .barricade, .dumpster, .barricade, .newsstand, .hoarding, .barricade, .dumpster, .hoarding, .barricade, .newsstand, .dumpster };

    for (xs) |l| {
        if (l.kind == .edge or l.kind == .alley) continue;

        var z: f32 = -edge + 10;

        while (z < edge - 10) : (z += b.rng.range(22, 40)) {
            if (near(z, &zs) != null) continue;

            const lane: f32 = if (l.kind == .broadway) (if (chance(b, 0.5)) 6.5 else -6.5) else (if (chance(b, 0.5)) 4.5 else -4.5);
            const e = cars[@intFromFloat(@floor(b.rng.range(0, @as(f32, @floatFromInt(cars.len)) - 0.01)))];

            put(b, e, l.at + lane, z, (if (lane > 0) @as(f32, 0) else pi) + jitter(b, 0.05));
        }
    }

    for (zs) |l| {
        if (l.kind == .edge) continue;

        var x: f32 = -edge + 10;

        while (x < edge - 10) : (x += b.rng.range(24, 44)) {
            if (near(x, &xs)) |s| {
                if (s.kind != .alley) continue;
            }

            const lane: f32 = if (chance(b, 0.5)) 2.2 else -2.2;
            const e = cars[@intFromFloat(@floor(b.rng.range(0, 5.99)))];

            put(b, e, x, l.at + lane, (if (lane > 0) -hp else hp) + jitter(b, 0.05));
        }
    }

    for ([_][3]f32{ .{ 100, -35, 0 }, .{ -100, 35, 1 } }) |p| {
        put(b, .barricade, p[0] + 3, p[1] + 11, 0.4);
        put(b, .barricade, p[0] - 4, p[1] + 12, -0.3);
        put(b, .barricade, p[0], p[1] + 9, 0);
        put(b, .barricade, p[0] + 2.6, p[1] + 9, 0);
        put(b, .barricade, p[0] - 2.6, p[1] + 9, 0);
        put(b, .cone, p[0] + 5, p[1] + 8, 0);
        put(b, .steam, p[0] - 1, p[1] + 14, 0);
    }

    put(b, .hoarding, -100, -60, 0.05);
    put(b, .steam, 40, -35, 0);
    put(b, .steam, -60, 105, 0);
    put(b, .steam, 4.2, 20, 0);
}

fn skyline(b: *Builder) void {
    const towers = [_]K{ .deco, .slab, .prewar, .office, .slab, .prewar };
    var a: f32 = -t.half + 6;
    var i: usize = 0;

    while (a < t.half - 6) : (a += 22) {
        for ([_]f32{ -1, 1 }) |s| {
            const e1 = towers[i % towers.len];
            const e2 = towers[(i + 3) % towers.len];
            const off = edge + 18 + b.rng.range(0, 8);

            b.putAt(kit.of(e1), vec(a, t.height(a, s * off), s * off), if (s > 0) pi else 0, b.rng.range(0.9, 1.3));
            b.putAt(kit.of(e2), vec(s * off, t.height(s * off, a), a), if (s > 0) -hp else hp, b.rng.range(0.9, 1.3));
            i += 1;
        }
    }

    const ring = [_]K{ .brownstone, .tenement, .walkup, .loft, .cornerten, .tenement, .garage, .brownstone };
    var side: usize = 0;

    while (side < 4) : (side += 1) {
        var u: f32 = -edge - 10;
        var j: usize = side * 3;

        while (u < edge + 10) {
            const e = ring[j % ring.len];
            const sz = size(e);
            const off = edge + 5 + sz[1] / 2;
            const m = u + sz[0] / 2;
            const p: [3]f32 = switch (side) {
                0 => .{ m, off, pi },
                1 => .{ m, -off, 0 },
                2 => .{ off, m, -hp },
                else => .{ -off, m, hp },
            };

            b.putAt(kit.of(e), vec(p[0], t.height(p[0], p[1]), p[1]), p[2], 1);

            const c = if (side < 2) [2]f32{ m, (edge + 3.6) * (if (side == 0) @as(f32, 1) else -1) } else [2]f32{ (edge + 3.6) * (if (side == 2) @as(f32, 1) else -1), m };
            const r = b.rng.next();

            if (@abs(m) < edge - 4) {
                if (r < 0.25) {
                    put(b, .dumpster, c[0], c[1], p[2] + hp);
                } else if (r < 0.45) {
                    put(b, .can, c[0], c[1], 0);
                    put(b, .can, c[0] + 0.6, c[1] + 0.5, 0);
                    put(b, .palletload, c[0] - 0.8, c[1] - 0.6, p[2]);
                } else if (r < 0.6) {
                    put(b, .hvac, c[0], c[1], p[2]);
                    put(b, .drum, c[0] + 1, c[1] + 0.4, 0);
                } else if (r < 0.72) {
                    put(b, .tree, c[0], c[1], r * 9);
                }
            }

            u += sz[0] + 0.2;
            j += 1;
        }
    }
}

fn build(b: *Builder) void {
    streets(b);
    traffic(b);

    var i: usize = 0;

    while (i + 1 < xs.len) : (i += 1) {
        var j: usize = 0;

        while (j + 1 < zs.len) : (j += 1) {
            const x0 = xs[i].at + xs[i].hw;
            const x1 = xs[i + 1].at - xs[i + 1].hw;
            const z0 = zs[j].at + zs[j].hw;
            const z1 = zs[j + 1].at - zs[j + 1].hw;

            switch (blockUse(i, j)) {
                .row => rowBlock(b, x0, z0, x1, z1, xs[i].kind, xs[i + 1].kind, zs[j].kind, zs[j + 1].kind),
                .park => park(b, x0, z0, x1, z1),
                .site => site(b, x0, z0, x1, z1),
                .plaza => plazaBlock(b, x0, z0, x1, z1),
            }
        }
    }

    skyline(b);
}
