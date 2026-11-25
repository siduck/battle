const std = @import("std");
const api = @import("api.zig");
const k = @import("japan_kit.zig");

const t = api.terrain;
const wd = api.world;
const kit = k.kit;
const K = k.K;
const vec = api.vec;
const Builder = api.Builder;
const pi = std.math.pi;
const hp = api.half_pi;

const edge: f32 = 146;

const Line = struct { at: f32, hw: f32, kind: Street };
const Street = enum { edge, alley, secondary, main };

const xs = [_]Line{
    .{ .at = -edge, .hw = 0, .kind = .edge },
    .{ .at = -100, .hw = 4.5, .kind = .secondary },
    .{ .at = -50, .hw = 2.5, .kind = .alley },
    .{ .at = 0, .hw = 7, .kind = .main },
    .{ .at = 50, .hw = 2.5, .kind = .alley },
    .{ .at = 100, .hw = 4.5, .kind = .secondary },
    .{ .at = edge, .hw = 0, .kind = .edge },
};

const zs = [_]Line{
    .{ .at = -edge, .hw = 0, .kind = .edge },
    .{ .at = -100, .hw = 4.5, .kind = .secondary },
    .{ .at = -50, .hw = 2.5, .kind = .alley },
    .{ .at = 0, .hw = 13, .kind = .main },
    .{ .at = 50, .hw = 2.5, .kind = .alley },
    .{ .at = 100, .hw = 4.5, .kind = .secondary },
    .{ .at = edge, .hw = 0, .kind = .edge },
};

const Use = enum { row, park, parking, lot };

fn blockUse(i: usize, j: usize) Use {
    if (i == 1 and j == 1) return .park;
    if (i == 4 and j == 4) return .park;
    if (i == 4 and j == 1) return .parking;
    if (i == 1 and j == 4) return .parking;
    if (i == 2 and j == 5) return .lot;
    if (i == 5 and j == 2) return .lot;

    return .row;
}

pub const def: api.Def = .{
    .name = "Suburb",
    .note = "Shop streets, trams and alleys",
    .tint = .{ 226, 150, 170 },
    .ready = true,
    .half = 172,
    .play = 150,
    .facet = 2,
    .height = height,
    .ground = ground,
    .build = build,
    .spots = api.autoSpots,
    .props = &k.table,
    .palette = .{
        .sun_dir = .{ 0.52, 0.62, 0.58 },
        .sun_tint = .{ 1.18, 1.02, 0.9 },
        .grade_tint = .{ 1.03, 0.99, 0.98 },
        .grade_sat = 1.24,
        .fog = 0.0042,
        .fog_color = .{ 0.82, 0.8, 0.86 },
        .amb_sky = .{ 0.92, 0.96, 1.14 },
        .amb_ground = .{ 0.82, 0.76, 0.7 },
        .shade_tint = .{ 0.86, 0.88, 1.08 },
        .zenith = .{ 0.12, 0.32, 0.66 },
    },
    .backdrop = .{ 170, 168, 176 },
    .grip = 0.86,
    .tufts = 0.5,
};

fn hash(x: f32, z: f32) f32 {
    return wd.hash2(x, z);
}

fn height(x: f32, z: f32) f32 {
    const e = @max(@abs(x), @abs(z));
    const rim = t.smooth(edge + 6, t.half, e);

    return rim * (6 + t.fbm(x * 0.03, z * 0.03) * 10);
}

fn near(v: f32, lines: []const Line) ?Line {
    for (lines) |l| {
        if (@abs(v - l.at) <= l.hw) return l;
    }

    return null;
}

fn sidewalk(l: Line) f32 {
    return switch (l.kind) {
        .main => 3,
        .secondary => 1.6,
        else => 0,
    };
}

fn mix(a: [3]f32, c: [3]f32, f: f32) [3]f32 {
    return api.mix3(a, c, f);
}

fn ground(x: f32, z: f32) api.Rgb {
    const l = api.light(x, z);
    const e = @max(@abs(x), @abs(z));
    const n = t.fbm(x * 0.07 + 5, z * 0.07 - 3);

    if (e > edge) return api.shade(mix(.{ 104, 136, 78 }, .{ 128, 140, 86 }, n), l);

    const sx = near(x, &xs);
    const sz = near(z, &zs);

    if (sz) |s| {
        if (s.kind == .main and @abs(z) < 4.4) return api.shade(.{ 132, 128, 120 }, l);

        if (@abs(z - s.at) > s.hw - sidewalk(s)) return paver(x, z, l);

        return asphalt(x, z, l, s.kind);
    }

    if (sx) |s| {
        if (@abs(x - s.at) > s.hw - sidewalk(s)) return paver(x, z, l);

        return asphalt(x, z, l, s.kind);
    }

    const i = cell(x, &xs);
    const j = cell(z, &zs);

    return switch (blockUse(i, j)) {
        .park => api.shade(mix(.{ 108, 146, 80 }, .{ 96, 132, 72 }, @mod(@floor(x / 4) + @floor(z / 4), 2)), l),
        .parking => api.shade(mix(.{ 88, 90, 96 }, .{ 96, 98, 104 }, n), l),
        .lot => api.shade(mix(.{ 168, 150, 120 }, .{ 150, 132, 104 }, n), l),
        .row => yard(x, z, l, n),
    };
}

fn cell(v: f32, lines: []const Line) usize {
    var i: usize = 0;

    while (i + 1 < lines.len) : (i += 1) {
        if (v < lines[i + 1].at) return i;
    }

    return lines.len - 2;
}

fn paver(x: f32, z: f32, l: f32) api.Rgb {
    const c = hash(@floor(x / 2), @floor(z / 2));
    const base = mix(.{ 186, 182, 174 }, .{ 172, 168, 160 }, c);

    return api.shade(base, l);
}

fn asphalt(x: f32, z: f32, l: f32, kind: Street) api.Rgb {
    const n = t.fbm(x * 0.11 - 2, z * 0.11 + 8);

    if (kind == .alley) return api.shade(mix(.{ 150, 146, 138 }, .{ 136, 132, 124 }, n), l);

    return api.shade(mix(.{ 76, 78, 84 }, .{ 66, 68, 74 }, n), l);
}

fn yard(x: f32, z: f32, l: f32, n: f32) api.Rgb {
    const g = t.smooth(0.45, 0.62, t.fbm(x * 0.05 - 9, z * 0.05 + 4));
    const dirt = mix(.{ 160, 150, 132 }, .{ 146, 136, 118 }, n);

    return api.shade(mix(dirt, .{ 112, 138, 82 }, g * 0.8), l);
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

fn width(e: K) f32 {
    return switch (e) {
        .parlour, .konbini, .wide => 8,
        .apartment, .tower => 12,
        else => 4,
    };
}

const Side = struct { x: f32, z: f32, dx: f32, dz: f32, yaw: f32, len: f32, kind: Street };

fn local(s: Side, along: f32, out: f32) [2]f32 {
    const ox = @sin(s.yaw);
    const oz = @cos(s.yaw);

    return .{ s.x + s.dx * along + ox * out, s.z + s.dz * along + oz * out };
}

fn pick(b: *Builder, kind: Street, room: f32) K {
    const r = b.rng.next();

    const want: K = switch (kind) {
        .main => if (r < 0.14) .parlour else if (r < 0.3) .wide else if (r < 0.52) .shop3 else if (r < 0.7) .shop2 else if (r < 0.82) .konbini else .corner,
        .secondary => if (r < 0.14) .tower else if (r < 0.3) .apartment else if (r < 0.48) .wide else if (r < 0.7) .shop2 else if (r < 0.85) .shop3 else .konbini,
        .alley => if (r < 0.45) .barhut else if (r < 0.8) .shop2 else .shop3,
        .edge => .shop2,
    };

    if (width(want) <= room) return want;

    return if (b.rng.next() < 0.5) .shop2 else .shop3;
}

fn frontage(b: *Builder, s: Side, e: K, along: f32) void {
    const w = width(e);
    const front: f32 = 0.0;
    const r = b.rng.next();
    const p = local(s, along, front + 0.9);
    const yaw = s.yaw;

    if (@abs(p[1]) < 14 and @abs(@abs(p[0]) - 69) < 9) return;

    if (e == .barhut) {
        const lp = local(s, along - 1.2, front + 0.1);
        const rp = local(s, along + 1.2, front + 0.1);

        putY(b, .lantern, lp[0], 2.2, lp[1], yaw);
        putY(b, .lantern, rp[0], 2.2, rp[1], yaw);

        const np = local(s, along, front + 0.05);

        putY(b, .noren, np[0], 1.65, np[1], yaw);

        return;
    }

    if (s.kind == .main and w >= 4 and r < 0.45) {
        const a = local(s, along, front + 0.6);

        putY(b, .awning, a[0], 2.3, a[1], yaw);
    }

    if (r < 0.2) {
        put(b, .vending, p[0], p[1], yaw);

        if (w >= 8) {
            const q = local(s, along + 1.2, front + 0.9);

            put(b, .vending, q[0], q[1], yaw);
        }
    } else if (r < 0.34) {
        put(b, .bike, p[0], p[1], yaw + hp + jitter(b, 0.2));

        const q = local(s, along + 0.8, front + 0.9);

        put(b, .bike, q[0], q[1], yaw + hp + jitter(b, 0.2));
    } else if (r < 0.44) {
        put(b, .potted, p[0], p[1], 0);
        put(b, .planter, local(s, along + 1.4, front + 0.6)[0], local(s, along + 1.4, front + 0.6)[1], yaw);
    } else if (r < 0.52) {
        put(b, .board, p[0], p[1], yaw);
    } else if (r < 0.6) {
        put(b, .moped, p[0], p[1], yaw + hp);
    } else if (r < 0.68) {
        const sh = local(s, along, front + 0.3);

        put(b, .shutter, sh[0], sh[1], yaw);
    } else if (r < 0.74) {
        put(b, .crate, p[0], p[1], b.rng.range(0, 3));
        putY(b, .crate, p[0], 0.36, p[1], b.rng.range(0, 3));
        put(b, .crate, local(s, along + 0.5, front + 0.9)[0], local(s, along + 0.5, front + 0.9)[1], 0.2);
    }

    if (e == .shop3 or e == .corner or e == .wide or e == .parlour) {
        if (b.rng.next() < 0.5) {
            const kp = local(s, along + w / 2 - 0.6, front + 0.15);

            putY(b, .kanji, kp[0], 3.2, kp[1], yaw + hp);
        }
    }

    if (b.rng.next() < 0.35) {
        const ap = local(s, along - w / 2 + 0.8, front + 0.2);

        putY(b, .ac, ap[0], if (b.rng.next() < 0.5) 0 else 3.4, ap[1], yaw);
    }
}

fn roofHeight(e: K) f32 {
    return switch (e) {
        .parlour => 9.42,
        .apartment => 9.4,
        .tower => 18.8,
        .konbini => 3.42,
        .corner => 9.48,
        .shop3 => 9.4,
        else => 0,
    };
}

fn rooftop(b: *Builder, e: K, x: f32, z: f32, yaw: f32) void {
    const h = roofHeight(e);

    if (h == 0) return;

    const w = width(e);

    if ((e == .shop3 or e == .corner) and chance(b, 0.45)) {
        b.putAt(kit.of(.roof), vec(x, h - 0.05, z), yaw, 1);

        return;
    }

    const n: usize = @intFromFloat(@max(1, w / 3));
    var i: usize = 0;

    while (i < n) : (i += 1) {
        const lx = b.rng.range(-w / 2 + 0.8, w / 2 - 0.8);
        const lz = b.rng.range(-1.2, 1.2);
        const p = wd.rotPoint(x, z, yaw, lx, lz);
        const r = b.rng.next();

        if (r < 0.45) {
            b.putAt(kit.of(.ac), vec(p[0], h, p[1]), yaw + @round(b.rng.range(0, 4)) * hp, 1);
        } else if (r < 0.65) {
            b.deco(vec(p[0] - 0.6, h, p[1] - 0.6), vec(p[0] + 0.6, h + 0.5, p[1] + 0.6), .f_grey_dark);
            b.putAt(kit.of(.drum), vec(p[0], h + 0.5, p[1]), 0, 1.4);
        } else if (r < 0.85) {
            b.deco(vec(p[0] - 0.9, h, p[1] - 0.7), vec(p[0] + 0.9, h + 2.1, p[1] + 0.7), .f_grey);
            b.deco(vec(p[0] - 1.0, h + 2.1, p[1] - 0.8), vec(p[0] + 1.0, h + 2.25, p[1] + 0.8), .f_grey_dark);
        } else {
            b.deco(vec(p[0] - 0.05, h, p[1] - 0.05), vec(p[0] + 0.05, h + 2.6, p[1] + 0.05), .f_metal);
            b.deco(vec(p[0] - 0.7, h + 2.2, p[1] - 0.04), vec(p[0] + 0.7, h + 2.28, p[1] + 0.04), .f_metal);
        }
    }
}

fn wallHeight(e: K) f32 {
    return switch (e) {
        .shop2 => 5.6,
        .wide => 6.0,
        .barhut => 0,
        else => roofHeight(e),
    };
}

fn backWindows(b: *Builder, s: Side, e: K, along: f32) void {
    const h = wallHeight(e);

    if (h < 5) return;

    const w = width(e);
    const floors: usize = @intFromFloat(@floor(h / 3.1));
    var f: usize = 0;

    while (f < floors) : (f += 1) {
        var u = -w / 2 + 2;

        while (u < w / 2 - 1) : (u += 4) {
            if (f == 0 and chance(b, 0.5)) continue;

            const y = 1.3 + @as(f32, @floatFromInt(f)) * 3.1;
            const a = local(s, along + u - 0.55, -4.06);
            const c = local(s, along + u + 0.55, -4.12);

            b.deco(vec(@min(a[0], c[0]), y, @min(a[1], c[1])), vec(@max(a[0], c[0]), y + 1.2, @max(a[1], c[1])), .f_black);

            const sa = local(s, along + u - 0.7, -4.05);
            const sc = local(s, along + u + 0.7, -4.2);

            b.deco(vec(@min(sa[0], sc[0]), y - 0.12, @min(sa[1], sc[1])), vec(@max(sa[0], sc[0]), y, @max(sa[1], sc[1])), .concrete);
        }
    }
}

fn gapDress(b: *Builder, s: Side, along: f32) void {
    for ([_]f32{ -1, 1 }) |sd| {
        const p = local(s, along + sd * 2.15, -1.5);
        const yaw = s.yaw + sd * hp;

        if (chance(b, 0.7)) b.putAt(kit.of(.ac), vec(p[0], 2.8 + @round(b.rng.range(0, 2)) * 2.6, p[1]), yaw, 1);
        if (chance(b, 0.5)) put(b, .meter, local(s, along + sd * 2.2, -0.8)[0], local(s, along + sd * 2.2, -0.8)[1], yaw);
    }

    const q = local(s, along, -3.2);

    if (chance(b, 0.5)) put(b, .bike, q[0], q[1], s.yaw + hp) else put(b, .potted, q[0], q[1], 0);
}

fn lineSide(b: *Builder, s: Side, gap: bool) void {
    var a: f32 = 0;
    const mid = s.len / 2;
    var gapped = !gap;

    while (a < s.len - 3.9) {
        const room = s.len - a;

        if (!gapped and a + 4 > mid - 2) {
            gapped = true;
            gapDress(b, s, a + 2.25);
            a += 4.5;

            continue;
        }

        const e = pick(b, s.kind, room);
        const w = width(e);
        const c = local(s, a + w / 2, -2);

        place(b, e, c[0], c[1], s.yaw);
        rooftop(b, e, c[0], c[1], s.yaw);
        backWindows(b, s, e, a + w / 2);
        frontage(b, s, e, a + w / 2);
        a += w;
    }

    if (s.len - a > 0.5) {
        const c = local(s, a + (s.len - a) / 2, -0.2);

        put(b, .blockwall, c[0], c[1], s.yaw);
    }
}

fn wallSide(b: *Builder, s: Side) void {
    var a: f32 = 2;

    while (a < s.len - 1) : (a += 4) {
        const c = local(s, a, -0.3);

        put(b, if (s.kind == .edge) .stonefence else .blockwall, c[0], c[1], s.yaw);
    }
}

fn sides(x0: f32, z0: f32, x1: f32, z1: f32, kw: Street, ke: Street, ks: Street, kn: Street) [4]Side {
    return .{
        .{ .x = x0 + 4, .z = z0, .dx = 1, .dz = 0, .yaw = pi, .len = x1 - x0 - 8, .kind = ks },
        .{ .x = x1 - 4, .z = z1, .dx = -1, .dz = 0, .yaw = 0, .len = x1 - x0 - 8, .kind = kn },
        .{ .x = x0, .z = z1 - 4, .dx = 0, .dz = -1, .yaw = -hp, .len = z1 - z0 - 8, .kind = kw },
        .{ .x = x1, .z = z0 + 4, .dx = 0, .dz = 1, .yaw = hp, .len = z1 - z0 - 8, .kind = ke },
    };
}

fn rank(s: Street) u8 {
    return switch (s) {
        .edge => 0,
        .alley => 1,
        .secondary => 2,
        .main => 3,
    };
}

fn rowBlock(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32, kw: Street, ke: Street, ks: Street, kn: Street) void {
    const ss = sides(x0, z0, x1, z1, kw, ke, ks, kn);
    var gaps: usize = 0;

    for (ss, 0..) |s, si| {
        if (s.kind == .edge) {
            wallSide(b, s);

            continue;
        }

        const gap = (si % 2 == 0 and gaps < 2) or (s.kind == .alley and chance(b, 0.5));

        if (gap) gaps += 1;

        lineSide(b, s, gap);
    }

    const corners = [_][4]f32{ .{ x0 + 2, z0 + 2, 2, 0 }, .{ x1 - 2, z0 + 2, 3, 0 }, .{ x0 + 2, z1 - 2, 2, 1 }, .{ x1 - 2, z1 - 2, 3, 1 } };

    for (corners) |c| {
        const a = ss[@intFromFloat(c[2])];
        const o = ss[@intFromFloat(c[3])];

        if (a.kind == .edge and o.kind == .edge) continue;

        const yaw = if (rank(a.kind) >= rank(o.kind)) a.yaw else o.yaw;

        if (a.kind == .edge or o.kind == .edge) {
            place(b, .shop2, c[0], c[1], yaw);
        } else {
            place(b, .corner, c[0], c[1], yaw);
            rooftop(b, .corner, c[0], c[1], yaw);
        }
    }

    backyard(b, x0 + 4.6, z0 + 4.6, x1 - 4.6, z1 - 4.6);
}

fn backyard(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32) void {
    if (x1 - x0 < 4 or z1 - z0 < 4) return;

    var a: f32 = x0 + 1;

    while (a < x1 - 1) : (a += 3.2) {
        if (chance(b, 0.4)) put(b, .ac, a, z0 + 0.35, 0);
        if (chance(b, 0.4)) put(b, .ac, a, z1 - 0.35, pi);
        if (chance(b, 0.12)) put(b, .drum, a + 1, z0 + 0.6, 0);
        if (chance(b, 0.12)) put(b, .wheelie, a + 1, z1 - 0.6, pi);
    }

    var c: f32 = z0 + 1;

    while (c < z1 - 1) : (c += 3.2) {
        if (chance(b, 0.35)) put(b, .ac, x0 + 0.35, c, hp);
        if (chance(b, 0.35)) put(b, .ac, x1 - 0.35, c, -hp);
        if (chance(b, 0.15)) put(b, .meter, x0 + 0.3, c + 1, hp);
    }

    const cx = (x0 + x1) / 2;
    const cz = (z0 + z1) / 2;

    if (chance(b, 0.5)) {
        var w = x0 + 2;

        while (w < x1 - 2) : (w += 4) {
            if (@abs(w - cx) < 3) continue;

            put(b, .blockwall, w, cz, 0);
        }
    }

    var n: usize = 0;

    while (n < 30) : (n += 1) {
        const px = b.rng.range(x0 + 2, x1 - 2);
        const pz = b.rng.range(z0 + 2, z1 - 2);

        if (wd.covered(b, px, pz, 1.4)) continue;

        const r = b.rng.next();

        if (r < 0.14) {
            place(b, .barhut, px, pz, @round(b.rng.range(0, 4)) * hp);
        } else if (r < 0.26) {
            put(b, .keivan, px, pz, @round(b.rng.range(0, 4)) * hp + jitter(b, 0.1));
        } else if (r < 0.4) {
            put(b, .maple, px, pz, b.rng.range(0, 6));
        } else if (r < 0.52) {
            put(b, .drum, px, pz, 0);
            put(b, .drum, px + 0.7, pz + 0.2, 0);
            put(b, .crate, px - 0.6, pz, 0.3);
        } else if (r < 0.62) {
            put(b, .bike, px, pz, b.rng.range(0, 6));
            put(b, .bikerack, px + 1, pz, 0);
        } else if (r < 0.72) {
            put(b, .potted, px, pz, 0);
            put(b, .rock, px + 1.2, pz, b.rng.range(0, 6));
        } else if (r < 0.8) {
            put(b, .wheelie, px, pz, 0);
            put(b, .wheelie, px + 0.8, pz, 0);
        } else if (r < 0.88) {
            put(b, .hatch, px, pz, @round(b.rng.range(0, 4)) * hp);
        } else {
            put(b, .bush, px, pz, b.rng.range(0, 6));
        }
    }
}

fn park(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32) void {
    var a: f32 = x0 + 2;

    while (a < x1 - 1) : (a += 4) {
        if (@abs(a - (x0 + x1) / 2) > 3) {
            put(b, .stonefence, a, z0 + 0.3, 0);
            put(b, .stonefence, a, z1 - 0.3, 0);
        }
    }

    var c: f32 = z0 + 2;

    while (c < z1 - 1) : (c += 4) {
        if (@abs(c - (z0 + z1) / 2) > 3) {
            put(b, .stonefence, x0 + 0.3, c, hp);
            put(b, .stonefence, x1 - 0.3, c, hp);
        }
    }

    const cx = (x0 + x1) / 2;
    const cz = (z0 + z1) / 2;

    paint(b, cx - 1.5, z0, cx + 1.5, z1, .sandbag);
    paint(b, x0, cz - 1.5, x1, cz + 1.5, .sandbag);
    b.deco(vec(cx - 5, 0.01, cz - 5), vec(cx + 5, 0.06, cz + 5), .sandbag);
    b.deco(vec(cx - 3, 0.06, cz - 3), vec(cx + 3, 0.12, cz + 3), .cloth_blue);
    b.deco(vec(cx - 3.3, 0, cz - 3.3), vec(cx + 3.3, 0.45, cz - 3), .concrete);
    b.deco(vec(cx - 3.3, 0, cz + 3), vec(cx + 3.3, 0.45, cz + 3.3), .concrete);
    b.deco(vec(cx - 3.3, 0, cz - 3.3), vec(cx - 3, 0.45, cz + 3.3), .concrete);
    b.deco(vec(cx + 3, 0, cz - 3.3), vec(cx + 3.3, 0.45, cz + 3.3), .concrete);

    for ([_][2]f32{ .{ -1, -1 }, .{ 1, -1 }, .{ -1, 1 }, .{ 1, 1 } }) |q| {
        const qx = cx + q[0] * (x1 - x0) * 0.27;
        const qz = cz + q[1] * (z1 - z0) * 0.27;

        put(b, .cherry, qx + jitter(b, 2), qz + jitter(b, 2), b.rng.range(0, 6));
        put(b, .cherry, qx + 6 + jitter(b, 2), qz - 4 + jitter(b, 2), b.rng.range(0, 6));
        put(b, .bench, qx - q[0] * 6, cz + q[1] * 3, if (q[1] < 0) 0 else pi);
        put(b, .rock, qx - 5, qz + 4, b.rng.range(0, 6));
        put(b, .bush, qx + 3, qz + 5, b.rng.range(0, 6));
        put(b, .bush, qx - 4, qz - 5, b.rng.range(0, 6));
        put(b, .planter, cx + q[0] * 6, cz + q[1] * 1.2, 0);
    }

    put(b, .tree, x0 + 4, z0 + 4, 0);
    put(b, .tree, x1 - 4, z1 - 4, 1);
    put(b, .lamp, cx - 2, cz - 6, 0);
    put(b, .lamp, cx + 2, cz + 6, pi);
    put(b, .bin, cx + 2.5, z0 + 3, 0);
    put(b, .vending, x0 + 2, cz + 3, hp);
    put(b, .vending, x0 + 2, cz + 4.2, hp);
    put(b, .bikerack, x1 - 3, cz + 4, hp);
}

fn parking(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32) void {
    var z = z0 + 4;
    var ri: usize = 0;

    while (z < z1 - 3) : (z += 7) {
        var x = x0 + 2;

        while (x < x1 - 2) : (x += 2.6) {
            paint(b, x - 0.06, z - 2.5, x + 0.06, z + 2.5, .marking);

            if (chance(b, 0.3)) {
                continue;
            }

            const r = b.rng.next();
            const e: K = if (r < 0.35) .keivan else if (r < 0.6) .taxi else .hatch;

            put(b, e, x + 1.3, z, (if (ri % 2 == 0) @as(f32, 0) else pi) + jitter(b, 0.05));
        }

        ri += 1;
    }

    put(b, .lamp, x0 + 1, z0 + 1, 0);
    put(b, .lamp, x1 - 1, z1 - 1, pi);
    put(b, .vending, x0 + 1, z1 - 1.5, hp);
    put(b, .bin, x0 + 1, z1 - 3, 0);
    wallSide(b, .{ .x = x0 + 2, .z = z0, .dx = 1, .dz = 0, .yaw = pi, .len = (x1 - x0) * 0.4, .kind = .alley });
}

fn lot(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32) void {
    var a: f32 = x0 + 2;

    while (a < x1 - 1) : (a += 4) {
        if (@abs(a - (x0 + x1) / 2) > 4) {
            put(b, .guardrail, a, z0 + 0.4, 0);
            put(b, .guardrail, a, z1 - 0.4, 0);
        }
    }

    var n: usize = 0;

    while (n < 70) : (n += 1) {
        const px = b.rng.range(x0 + 3, x1 - 3);
        const pz = b.rng.range(z0 + 3, z1 - 3);

        if (wd.covered(b, px, pz, 1.8)) continue;

        const r = b.rng.next();
        const yaw = @round(b.rng.range(0, 4)) * hp;

        if (r < 0.2) {
            put(b, .keivan, px, pz, yaw + jitter(b, 0.2));
        } else if (r < 0.38) {
            put(b, .guardrail, px, pz, yaw);
            put(b, .cone, px + 2.4, pz + 0.6, 0);
        } else if (r < 0.55) {
            put(b, .drum, px, pz, 0);
            put(b, .drum, px + 0.7, pz, 0);
            put(b, .drum, px + 0.35, pz + 0.6, 0);
        } else if (r < 0.7) {
            put(b, .blockwall, px, pz, yaw);
        } else if (r < 0.82) {
            put(b, .keivan, px, pz, yaw);
        } else {
            put(b, .cone, px, pz, 0);
            put(b, .cone, px + 1, pz + 1, 0);
            put(b, .crate, px - 1, pz, 0);
        }
    }
}

fn streets(b: *Builder) void {
    var x: f32 = -edge;

    while (x < edge) : (x += 4) {
        if (@abs(x) < 7) continue;

        put(b, .track, x + 2, -2.2, hp);
        put(b, .track, x + 2, 2.2, hp);
    }

    for (xs) |l| {
        if (l.kind == .edge) continue;

        poles(b, l.at - l.hw + 0.4, -edge + 4, l.at - l.hw + 0.4, edge - 4, true);
        lamps(b, l.at + l.hw - 0.5, -edge + 8, l.at + l.hw - 0.5, edge - 8, true);

        if (l.kind != .alley) dashes(b, l.at, true);
    }

    for (zs) |l| {
        if (l.kind == .edge) continue;

        poles(b, -edge + 4, l.at + l.hw - 0.4, edge - 4, l.at + l.hw - 0.4, false);
        lamps(b, -edge + 8, l.at - l.hw + 0.5, edge - 8, l.at - l.hw + 0.5, false);

        if (l.kind == .secondary) dashes(b, l.at, false);
    }

    for ([_]f32{ -1, 1 }) |sd| {
        var dx: f32 = -edge;

        while (dx < edge) : (dx += 8) {
            if (@abs(dx) < 9) continue;

            paint(b, dx, sd * 7.2 - 0.08, dx + 4, sd * 7.2 + 0.08, .marking);
        }

        paint(b, -edge, sd * 4.5 - 0.06, edge, sd * 4.5 + 0.06, .paint_line);
    }

    for ([_]f32{ -1, 1 }) |sd| {
        var c: f32 = -6;

        while (c < 6) : (c += 1.2) {
            paint(b, c, sd * 15.5 - 1.8, c + 0.6, sd * 15.5 + 1.8, .marking);
            paint(b, sd * 9 - 1.4, c * 1.6, sd * 9 + 1.4, c * 1.6 + 0.9, .marking);
        }

        put(b, .signal, sd * 6, sd * 10.5, if (sd < 0) pi else 0);
        put(b, .signal, -sd * 6.4, sd * 12, if (sd < 0) -hp else hp);
    }

    for (xs) |lx| {
        for (zs) |lz| {
            if (lx.kind != .alley and lz.kind != .alley) continue;

            if (lx.kind == .edge or lz.kind == .edge) continue;

            put(b, .mirror, lx.at + lx.hw + 0.4, lz.at + lz.hw + 0.4, -pi * 0.75);
        }
    }
}

fn dashes(b: *Builder, at: f32, along_z: bool) void {
    var a: f32 = -edge;

    while (a < edge) : (a += 8) {
        if (@abs(a) < 16 and along_z) continue;

        if (along_z) paint(b, at - 0.08, a, at + 0.08, a + 4, .marking) else paint(b, a, at - 0.08, a + 4, at + 0.08, .marking);
    }
}

fn poles(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32, along_z: bool) void {
    const len = if (along_z) z1 - z0 else x1 - x0;
    var a: f32 = 0;

    while (a <= len) : (a += 8.19) {
        const x = if (along_z) x0 else x0 + a;
        const z = if (along_z) z0 + a else z0;

        if (near(if (along_z) z else x, if (along_z) &zs else &xs)) |s| {
            if (s.kind != .edge and s.kind != .alley) continue;
        }

        put(b, .pole, x, z, if (along_z) 0 else hp);
    }
}

fn lamps(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32, along_z: bool) void {
    const len = if (along_z) z1 - z0 else x1 - x0;
    var a: f32 = 6;

    while (a <= len) : (a += 18) {
        const x = if (along_z) x0 else x0 + a;
        const z = if (along_z) z0 + a else z0;

        if (near(if (along_z) z else x, if (along_z) &zs else &xs) != null) continue;

        put(b, .lamp, x, z, if (along_z) -hp else pi);
    }
}

fn footbridge(b: *Builder, x: f32) void {
    const deck: f32 = 5.4;
    const hw: f32 = 1.5;
    const z0: f32 = -13;
    const z1: f32 = 13;

    b.mass(vec(x - hw, deck - 0.35, z0), vec(x + hw, deck, z1), .concrete);
    b.deco(vec(x - hw, deck, z0), vec(x - hw + 0.12, deck + 1.1, z1), .f_metal);
    b.deco(vec(x + hw - 0.12, deck, z0), vec(x + hw, deck + 1.1, z1), .f_metal);
    b.solid(.{ .box = .{ .min = vec(x - hw - 0.05, deck, z0), .max = vec(x - hw + 0.12, deck + 1.1, z1) } });
    b.solid(.{ .box = .{ .min = vec(x + hw - 0.12, deck, z0), .max = vec(x + hw + 0.05, deck + 1.1, z1) } });

    for ([_]f32{ -8, 8 }) |pz| b.mass(vec(x - 0.4, 0, pz - 0.4), vec(x + 0.4, deck - 0.35, pz + 0.4), .f_grey);

    for ([_]f32{ -1, 1 }) |sd| {
        const zc = sd * 11.5;
        const za = zc - 1.4;
        const zb = zc + 1.4;
        const run: f32 = 12;
        const xa = x + hw;
        const xb = xa + run;
        const n: usize = 18;
        var i: usize = 0;

        b.solid(.{ .ramp = .{ .min = vec(xa, 0, za), .max = vec(xb, deck, zb), .rise = .neg_x } });

        while (i < n) : (i += 1) {
            const f = @as(f32, @floatFromInt(i)) / @as(f32, @floatFromInt(n));
            const sa = xb - run * f;
            const sb = sa - run / @as(f32, @floatFromInt(n));
            const y = deck * (f + 1 / @as(f32, @floatFromInt(n)));

            b.deco(vec(sb, y - 0.12, za + 0.1), vec(sa, y, zb - 0.1), .concrete);
            b.deco(vec(sb, y - 0.6, za), vec(sa, y - 0.1, za + 0.12), .f_grey_dark);
            b.deco(vec(sb, y - 0.6, zb - 0.12), vec(sa, y - 0.1, zb), .f_grey_dark);
            b.deco(vec(sb, y + 0.95, za), vec(sa, y + 1.05, za + 0.06), .f_metal);
            b.deco(vec(sb, y + 0.95, zb - 0.06), vec(sa, y + 1.05, zb), .f_metal);

            if (i % 4 == 0) {
                b.deco(vec(sa - 0.06, y, za), vec(sa, y + 1.0, za + 0.06), .f_metal);
                b.deco(vec(sa - 0.06, y, zb - 0.06), vec(sa, y + 1.0, zb), .f_metal);
            }
        }

        b.mass(vec(x - hw, deck - 0.35, za), vec(xa, deck, zb), .concrete);
        b.mass(vec(xb - 0.5, 0, za), vec(xb, 0.2, zb), .concrete);
        b.mass(vec(xa + 4, 0, zc - 0.3), vec(xa + 4.6, deck * 0.6, zc + 0.3), .f_grey);
    }
}

fn avenue(b: *Builder) void {
    footbridge(b, -75);
    footbridge(b, 75);

    put(b, .tram, -30, 2.2, hp);
    put(b, .tram, -21.8, 2.2, hp);
    put(b, .tram, 118, -2.2, -hp);
    put(b, .tram, -128, -2.2, hp + 0.02);

    for ([_]f32{ -38, -26 }) |sx| {
        put(b, .bench, sx, 10.4, pi);
        put(b, .bin, sx + 2, 10.6, 0);
    }

    put(b, .kanji, -32, 10.6, 0);
    put(b, .taxi, 30, -7, hp);
    put(b, .taxi, 60, 7.2, -hp);
    put(b, .keivan, -60, -7, hp);
    put(b, .hatch, 96, 7.2, -hp);
    put(b, .keivan, -110, 7, -hp);
    put(b, .taxi, 3.5, 40, 0);
    put(b, .hatch, -3.5, -60, pi);
    put(b, .keivan, 3.5, 120, 0);
    put(b, .ramen, 20, 11.5, pi);
    put(b, .ramen, -96, -11.5, 0);
    put(b, .postbox, 9, 12, 0);
    put(b, .postbox, -9, -12, 0);

    for ([_]f32{ -140, -60, 40, 130 }) |cx| {
        put(b, .cone, cx, -6, 0);
        put(b, .cone, cx + 1.5, -6.4, 0);
    }
}

fn perimeter(b: *Builder) void {
    var a: f32 = -t.half + 3;

    while (a < t.half - 3) : (a += 7) {
        for ([_]f32{ -1, 1 }) |s| {
            const off = edge + 6 + b.rng.range(0, 10);

            put(b, if (b.rng.next() < 0.5) .tree else .cherry, a + jitter(b, 2), s * off, b.rng.range(0, 6));
            put(b, if (b.rng.next() < 0.5) .tree else .maple, s * off, a + jitter(b, 2), b.rng.range(0, 6));
        }
    }

    for ([_][3]f32{ .{ -120, 166, 0 }, .{ -40, 168, 0 }, .{ 60, 165, 0 }, .{ 140, 168, 0 }, .{ -166, -60, hp }, .{ -168, 80, hp }, .{ 166, -100, -hp }, .{ 168, 30, -hp }, .{ 20, -166, pi }, .{ -100, -168, pi }, .{ 110, -166, pi } }) |p| {
        b.putAt(kit.of(.tower), vec(p[0], t.height(p[0], p[1]), p[1]), p[2], 1.2);
    }
}

fn build(b: *Builder) void {
    streets(b);
    avenue(b);

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
                .parking => parking(b, x0, z0, x1, z1),
                .lot => lot(b, x0, z0, x1, z1),
            }
        }
    }

    perimeter(b);
}
