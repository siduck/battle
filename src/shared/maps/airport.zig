const std = @import("std");
const api = @import("api.zig");
const k = @import("airport_kit.zig");

const t = api.terrain;
const wd = api.world;
const kit = k.kit;
const K = k.K;
const vec = api.vec;
const Builder = api.Builder;
const pi = std.math.pi;
const hp = api.half_pi;

const rw = [4]f32{ 0, -158, 180, 14 };
const twy_z: f32 = -122;
const apron = [4]f32{ -188, -113, 188, -14 };
const term = [4]f32{ -96, -14, 32, 18 };
const roof: f32 = 9.5;
const hangar = [3]f32{ 140, -10, pi };
const park = [4]f32{ -98, 44, -18, 100 };

pub const def: api.Def = .{
    .name = "Airport",
    .note = "Runways, terminal and hangars",
    .tint = .{ 150, 170, 196 },
    .ready = true,
    .half = 215,
    .play = 190,
    .facet = 2.5,
    .runway = rw,
    .helipads = .{ .{ 108, 52 }, .{ 132, 52 }, .{ 156, 52 } },
    .height = height,
    .ground = ground,
    .build = build,
    .spots = api.autoSpots,
    .props = &k.table,
    .palette = .{
        .sun_dir = .{ 0.46, 0.7, 0.55 },
        .sun_tint = .{ 1.16, 1.04, 0.9 },
        .grade_tint = .{ 1.02, 1.0, 0.97 },
        .grade_sat = 1.18,
        .fog = 0.003,
        .fog_color = .{ 0.76, 0.83, 0.9 },
        .amb_sky = .{ 0.9, 0.98, 1.16 },
        .amb_ground = .{ 0.78, 0.76, 0.66 },
        .shade_tint = .{ 0.86, 0.9, 1.08 },
        .zenith = .{ 0.08, 0.3, 0.66 },
    },
    .backdrop = .{ 150, 166, 150 },
    .aircraft = true,
    .tanks = true,
    .grip = 0.86,
    .tufts = 0.6,
};

fn inRect(x: f32, z: f32, r: [4]f32) bool {
    return x >= r[0] and x <= r[2] and z >= r[1] and z <= r[3];
}

fn hash(x: f32, z: f32) f32 {
    return wd.hash2(x, z);
}

fn height(x: f32, z: f32) f32 {
    const edge = @max(@abs(x), @abs(z));
    const rim = t.smooth(t.play + 6, t.half, edge);
    const roll = 5 + t.fbm(x * 0.03, z * 0.03) * 9;

    return rim * roll;
}

const roads = [_][4]f32{
    .{ -132, 22, 70, 34 },
    .{ 40, 22, 52, 192 },
    .{ -192, 110, 192, 122 },
    .{ -132, 34, -120, 110 },
    .{ 52, 64, 100, 74 },
    .{ 100, 64, 112, 110 },
};

const lots = [_][4]f32{
    park,
    .{ 58, 128, 104, 176 },
    .{ -192, 126, -96, 188 },
    .{ 58, 78, 98, 100 },
    .{ -188, 28, -176, 106 },
};

const yards = [_][4]f32{
    .{ -188, -14, -128, 22 },
    .{ 128, 64, 188, 106 },
    .{ 108, 128, 188, 192 },
    .{ 60, 30, 100, 62 },
    .{ -24, 54, 24, 100 },
};

fn mown(x: f32, z: f32) [3]f32 {
    const band = @mod(@floor((x + z * 0.12) / 7.5), 2) == 0;
    const n = t.fbm(x * 0.05 + 3, z * 0.05 - 7);
    const base: [3]f32 = if (band) .{ 114, 152, 80 } else .{ 100, 138, 70 };
    const dry = t.smooth(0.55, 0.78, n);

    return api.mix3(base, .{ 146, 148, 90 }, dry * 0.55);
}

fn slab(x: f32, z: f32, base: [3]f32, size: f32, amount: f32) [3]f32 {
    const h = hash(@floor(x / size) + 0.37, @floor(z / size) - 0.71);
    const kk = 1 - amount + h * amount * 2;

    return .{ base[0] * kk, base[1] * kk, base[2] * kk };
}

fn stain(x: f32, z: f32, c: [3]f32) [3]f32 {
    const n = t.fbm(x * 0.09 + 11, z * 0.09 - 4);
    const d = t.smooth(0.58, 0.72, n) * 0.12;

    return .{ c[0] * (1 - d), c[1] * (1 - d), c[2] * (1 - d * 0.8) };
}

fn ground(x: f32, z: f32) api.Rgb {
    const l = api.light(x, z);

    if (@abs(x) > t.play + 2 or @abs(z) > t.play + 2) return api.shade(api.mix3(mown(x, z), .{ 90, 116, 68 }, 0.35), l);

    if (@abs(z - rw[1]) < rw[3] + 3 and @abs(x) < rw[2] + 4) return api.shade(stain(x, z, .{ 76, 78, 82 }), l);

    if (@abs(z - twy_z) < 9 and @abs(x) < 186) return api.shade(stain(x, z, slab(x, z, .{ 88, 90, 94 }, 7.5, 0.03)), l);

    if (inRect(x, z, term)) {
        const c = @mod(@floor(x / 2.5) + @floor(z / 2.5), 2) == 0;

        return if (c) .{ 214, 210, 200 } else .{ 196, 192, 182 };
    }

    if (inRect(x, z, .{ hangar[0] - 27, hangar[1] - 23, hangar[0] + 27, hangar[1] + 23 })) return api.shade(slab(x, z, .{ 150, 152, 152 }, 5, 0.03), l);

    if (inRect(x, z, apron)) return api.shade(stain(x, z, slab(x, z, .{ 172, 172, 166 }, 7.5, 0.05)), l);

    if (inRect(x, z, .{ -132, 18, 70, 22 }) or inRect(x, z, .{ -132, 34, 70, 40 })) return api.shade(slab(x, z, .{ 186, 182, 172 }, 2.5, 0.05), l);

    for (roads) |r| {
        if (inRect(x, z, r)) return api.shade(stain(x, z, slab(x, z, .{ 82, 84, 88 }, 10, 0.02)), l);
    }

    for (lots) |r| {
        if (inRect(x, z, r)) return api.shade(stain(x, z, slab(x, z, .{ 94, 96, 100 }, 10, 0.02)), l);
    }

    for (yards) |r| {
        if (inRect(x, z, r)) return api.shade(stain(x, z, slab(x, z, .{ 160, 160, 154 }, 5, 0.05)), l);
    }

    return api.shade(mown(x, z), l);
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

fn scaled(b: *Builder, e: K, x: f32, z: f32, yaw: f32, s: f32) void {
    b.put(kit.of(e), x, z, yaw, s);
}

fn paint(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32, tone: api.Tone) void {
    b.deco(vec(x0, 0.012, z0), vec(x1, 0.04, z1), tone);
}

fn kerb(b: *Builder, x0: f32, z0: f32, x1: f32, z1: f32) void {
    b.deco(vec(x0, 0, z0), vec(x1, 0.16, z1), .concrete);
}

fn row(b: *Builder, e: K, x0: f32, z0: f32, x1: f32, z1: f32, step: f32, yaw: f32) void {
    const dx = x1 - x0;
    const dz = z1 - z0;
    const len = @sqrt(dx * dx + dz * dz);
    const n: usize = @intFromFloat(@max(1, @floor(len / step + 0.5)));
    var i: usize = 0;

    while (i <= n) : (i += 1) {
        const f = @as(f32, @floatFromInt(i)) / @as(f32, @floatFromInt(n));

        put(b, e, x0 + dx * f, z0 + dz * f, yaw);
    }
}

fn jitter(b: *Builder, a: f32) f32 {
    return b.rng.range(-a, a);
}

fn build(b: *Builder) void {
    airfield(b);
    terminal(b);
    roofAccess(b);
    gates(b);
    service(b);
    cargo(b);
    maintenance(b);
    clutter(b);
    landside(b);
    north(b);
    perimeter(b);
}

fn airfield(b: *Builder) void {
    wd.runway(b);

    for (t.helipads) |p| wd.helipad(b, p[0], p[1]);

    var x: f32 = -rw[2] + 4;

    while (x <= rw[2] - 4) : (x += 16) {
        put(b, .edge, x, rw[1] - rw[3] - 1.2, 0);
        put(b, .edge, x, rw[1] + rw[3] + 1.2, 0);
    }

    x = -182;

    while (x < 182) : (x += 10) {
        paint(b, x, twy_z - 0.18, x + 6, twy_z + 0.18, .paint_line);
        put(b, .edge, x + 3, twy_z - 9.6, 0);
    }

    paint(b, -186, twy_z - 8.9, 186, twy_z - 8.6, .paint_line);
    paint(b, -186, twy_z + 8.6, 186, twy_z + 8.9, .paint_line);

    for ([_]f32{ -150, -90, -30, 30, 90, 150 }) |sx| {
        put(b, .twysign, sx, rw[1] + rw[3] + 7, 0);
        put(b, .twysign, sx + 6, twy_z - 11, 0);
        paint(b, sx - 0.18, twy_z - 8.6, sx + 0.18, rw[1] + rw[3], .paint_line);
    }

    for ([_]f32{ -1, 1 }) |side| {
        var z: f32 = rw[1] - 10;

        while (z <= rw[1] + 10) : (z += 4) place(b, .deflector, side * (rw[2] + 5), z, side * hp);
    }

    place(b, .localizer, 120, -180, 0);
    place(b, .localizer, -120, -180, 0);
    put(b, .windsock, 60, -180, 0);
    put(b, .windsock, -40, -138, 0);

    var fx: f32 = -170;

    while (fx <= 170) : (fx += 34) place(b, .flood, fx, -110, 0);

    var jx: f32 = -186;

    while (jx < 186) : (jx += 7.5) paint(b, jx, apron[1], jx + 0.1, apron[3], .scuff_soft);

    var jz: f32 = apron[1] + 7.5;

    while (jz < apron[3]) : (jz += 7.5) paint(b, apron[0], jz, apron[2], jz + 0.1, .scuff_soft);

    paint(b, apron[0], apron[1] + 0.2, apron[2], apron[1] + 0.5, .paint_line);
    paint(b, apron[0], -24.4, apron[2], -24.1, .marking);
    paint(b, apron[0], -19.4, apron[2], -19.1, .marking);

    var dx: f32 = apron[0];

    while (dx < apron[2]) : (dx += 6) paint(b, dx, -21.9, dx + 3, -21.6, .marking);
}

fn terminal(b: *Builder) void {
    const x0 = term[0];
    const x1 = term[2];
    const z0 = term[1];
    const z1 = term[3];
    const doors_n = [_]usize{ 2, 7, 12 };
    const doors_s = [_]usize{ 4, 10 };
    var i: usize = 0;

    while (i < 16) : (i += 1) {
        const cx = x0 + 4 + @as(f32, @floatFromInt(i)) * 8;
        const open_n = std.mem.indexOfScalar(usize, &doors_n, i) != null;
        const open_s = std.mem.indexOfScalar(usize, &doors_s, i) != null;

        if (!open_n) place(b, .facade, cx, z1 - 2, 0) else {
            b.mass(vec(cx - 4, 3.8, z1 - 0.8), vec(cx + 4, roof, z1), .f_grey);
            b.deco(vec(cx - 4, 3.4, z1 - 0.9), vec(cx + 4, 3.8, z1 + 0.1), .f_grey_dark);
            put(b, .kiosk, cx - 3, z1 - 4, pi);
            put(b, .kiosk, cx + 3, z1 - 4, pi);
        }

        if (!open_s) place(b, .facade, cx, z0 + 2, pi) else {
            b.mass(vec(cx - 4, 3.8, z0), vec(cx + 4, roof, z0 + 0.8), .f_grey);
            b.deco(vec(cx - 4, 3.4, z0 - 0.1), vec(cx + 4, 3.8, z0 + 0.9), .f_grey_dark);
        }
    }

    var j: usize = 0;

    while (j < 4) : (j += 1) {
        const cz = z0 + 4 + @as(f32, @floatFromInt(j)) * 8;

        place(b, .facade, x0 + 2, cz, -hp);
        place(b, .facade, x1 - 2, cz, hp);
    }

    b.mass(vec(x0, roof, z0), vec(x1, roof + 0.7, z1), .f_grey);
    b.deco(vec(x0 + 0.5, roof - 0.3, z0 + 0.5), vec(x1 - 0.5, roof, z1 - 0.5), .marking);

    var lz: f32 = z0 + 3;

    while (lz < z1 - 2) : (lz += 6) b.deco(vec(x0 + 2, roof - 0.42, lz), vec(x1 - 2, roof - 0.3, lz + 0.5), .f_light);

    b.mass(vec(x0, roof + 0.7, z0), vec(x1, roof + 1.6, z0 + 0.4), .f_grey_dark);
    b.mass(vec(x0, roof + 0.7, z1 - 0.4), vec(x1, roof + 1.6, z1), .f_grey_dark);
    b.mass(vec(x0, roof + 0.7, z0), vec(x0 + 0.4, roof + 1.6, -6), .f_grey_dark);
    b.mass(vec(x1 - 0.4, roof + 0.7, z0), vec(x1, roof + 1.6, z1), .f_grey_dark);

    for ([_][4]f32{ .{ -84, -8, 9, 6 }, .{ -60, 4, 7, 7 }, .{ -34, -10, 12, 5 }, .{ -6, 2, 8, 9 }, .{ 14, -8, 8, 6 } }) |u| {
        b.mass(vec(u[0], roof + 0.7, u[1]), vec(u[0] + u[2], roof + 2.5, u[1] + u[3]), .f_metal);
        b.mass(vec(u[0] + 0.5, roof + 2.5, u[1] + 0.5), vec(u[0] + u[2] - 0.5, roof + 2.9, u[1] + u[3] - 0.5), .f_grey_dark);
        b.deco(vec(u[0] - 0.4, roof + 0.7, u[1] - 0.4), vec(u[0] + u[2] + 0.4, roof + 0.78, u[1] + u[3] + 0.4), .blob_soft);
    }

    for ([_][2]f32{ .{ -70, -4 }, .{ -20, 8 }, .{ 4, -10 } }) |p| {
        b.mass(vec(p[0], roof + 0.7, p[1]), vec(p[0] + 2.2, roof + 1.6, p[1] + 2.2), .f_grey_dark);
    }

    var px: f32 = x0 + 16;

    while (px < x1 - 8) : (px += 16) {
        for ([_]f32{ -6, 10 }) |pz| b.mass(vec(px - 0.45, 0, pz - 0.45), vec(px + 0.45, roof, pz + 0.45), .concrete);
    }

    var wx: f32 = x0 + 4;

    while (wx < x1 - 12) : (wx += 16) {
        b.mass(vec(wx, 0, 1.6), vec(wx + 8, 2.4, 2.2), .f_grey);
        b.deco(vec(wx, 2.4, 1.5), vec(wx + 8, 2.6, 2.3), .f_grey_dark);
        put(b, .arch, wx + 10, 1.9, 0);
        put(b, .arch, wx + 12.5, 1.9, 0);
        put(b, .depboard, wx + 4, 3.4, 0);
    }

    for ([_]f32{ -82, -50, -18, 12 }) |cx| {
        var dz: f32 = 0;

        while (dz < 3) : (dz += 1) {
            put(b, .checkin, cx, 7 + dz * 2.5, hp);
            put(b, .checkin, cx + 3, 7 + dz * 2.5, -hp);
        }

        b.mass(vec(cx - 0.6, 0, 5.2), vec(cx + 3.6, 2.6, 5.8), .f_grey);
        put(b, .trolley, cx + 8, 9, b.rng.range(0, 6));
        put(b, .trolley, cx + 8.7, 9.6, b.rng.range(0, 6));
        put(b, .trolley, cx - 5, 12, b.rng.range(0, 6));
    }

    var sx: f32 = x0 + 6;

    while (sx < x1 - 8) : (sx += 10) {
        put(b, .seats, sx, -9, 0);
        put(b, .seats, sx + 2.6, -9, 0);
        put(b, .seats, sx, -6, pi);
        put(b, .seats, sx + 2.6, -6, pi);

        if (@mod(sx, 20) < 10) put(b, .depboard, sx + 7, -11.5, pi) else put(b, .trolley, sx + 7, -3, b.rng.range(0, 6));
    }

    var cx: f32 = x0 + 4;

    while (cx < x1) : (cx += 8) place(b, .canopy, cx, z1 + 6, 0);

    kerb(b, -132, 34, 70, 34.3);
    kerb(b, -132, 21.7, 70, 22);
    kerb(b, -132, 39.7, 70, 40);

    var bx: f32 = -92;

    while (bx < 30) : (bx += 12) put(b, .bollards, bx, 38, 0);

    var mx: f32 = -128;

    while (mx < 66) : (mx += 9) paint(b, mx, 27.9, mx + 4.5, 28.1, .marking);

    put(b, .uld, 56, 30, hp);
    put(b, .barrier, -70, 31, hp);
    put(b, .barrier, -48, 25.5, -hp);
    put(b, .barrier, -30, 31, hp);
    put(b, .barrier, 4, 25.5, -hp);
    put(b, .barrier, -112, 31, hp);
    put(b, .barrier, 22, 25.5, -hp);

    var lx: f32 = -128;

    while (lx < 70) : (lx += 18) put(b, .lamp, lx, 38.8, pi);

    for ([_]f32{ -114, -104, 40, 48 }) |hx| put(b, .shrub, hx, 20, 0);
}

fn roofAccess(b: *Builder) void {
    const x0: f32 = -104;
    const x1: f32 = -99;
    const top = roof + 0.7;
    const z_hi: f32 = 4;
    const z_lo: f32 = 40;
    const n: usize = 30;
    var i: usize = 0;

    b.solid(.{ .ramp = .{ .min = vec(x0, 0, z_hi), .max = vec(x1, top, z_lo), .rise = .neg_z } });

    while (i < n) : (i += 1) {
        const f = @as(f32, @floatFromInt(i)) / @as(f32, @floatFromInt(n));
        const za = z_lo - (z_lo - z_hi) * f;
        const zb = za - (z_lo - z_hi) / @as(f32, @floatFromInt(n));
        const y = top * (f + 1.0 / @as(f32, @floatFromInt(n)));

        b.deco(vec(x0 + 0.15, y - 0.12, zb), vec(x1 - 0.15, y, za), .concrete);
        b.deco(vec(x0, y - 0.7, zb), vec(x0 + 0.15, y - 0.1, za), .f_grey_dark);
        b.deco(vec(x1 - 0.15, y - 0.7, zb), vec(x1, y - 0.1, za), .f_grey_dark);
        b.deco(vec(x0, y + 0.95, zb), vec(x0 + 0.08, y + 1.05, za), .f_metal);
        b.deco(vec(x1 - 0.08, y + 0.95, zb), vec(x1, y + 1.05, za), .f_metal);

        if (i % 3 == 0) {
            b.deco(vec(x0, y, za - 0.08), vec(x0 + 0.06, y + 1.0, za), .f_metal);
            b.deco(vec(x1 - 0.06, y, za - 0.08), vec(x1, y + 1.0, za), .f_metal);
        }

        if (i % 6 == 3) {
            b.deco(vec(x0 + 0.1, 0, za - 0.3), vec(x0 + 0.4, y - 0.6, za), .f_grey);
            b.deco(vec(x1 - 0.4, 0, za - 0.3), vec(x1 - 0.1, y - 0.6, za), .f_grey);
        }
    }

    row(b, .fence, x0 - 0.2, z_hi + 3, x0 - 0.2, z_lo - 6, 5, hp);
    row(b, .fence, x1 + 0.2, z_hi + 3, x1 + 0.2, z_lo - 6, 5, hp);
    b.mass(vec(x0, top - 0.3, z_hi - 10), vec(term[0], top, z_hi + 6), .concrete);

    for ([_][2]f32{ .{ x0, z_hi - 10 }, .{ x1 - 0.5, z_hi - 10 }, .{ x0, z_hi - 0.5 }, .{ x1 - 0.5, z_hi - 0.5 } }) |c| {
        b.mass(vec(c[0], 0, c[1]), vec(c[0] + 0.5, top - 0.3, c[1] + 0.5), .f_grey);
    }

    b.deco(vec(x0, top + 0.95, z_hi - 10), vec(x0 + 0.08, top + 1.05, z_hi), .f_metal);
    b.deco(vec(x0, top + 0.95, z_hi - 10), vec(term[0], top + 1.05, z_hi - 9.92), .f_metal);
    b.solid(.{ .box = .{ .min = vec(x0 - 0.1, top, z_hi - 10), .max = vec(x0 + 0.1, top + 1.05, z_hi) } });
    b.solid(.{ .box = .{ .min = vec(x0, top, z_hi - 10.1), .max = vec(term[0], top + 1.05, z_hi - 9.9) } });
}

const Stand = struct { x: f32, nose: f32, len: f32, span: f32, bridge: bool };

const stands = [_]Stand{
    .{ .x = -60, .nose = -36, .len = 38, .span = 36, .bridge = true },
    .{ .x = 6, .nose = -36, .len = 64, .span = 60, .bridge = true },
    .{ .x = 72, .nose = -40, .len = 38, .span = 36, .bridge = false },
    .{ .x = -122, .nose = -42, .len = 27, .span = 27, .bridge = false },
};

fn gates(b: *Builder) void {
    for (stands) |s| {
        const cz = s.nose - s.len / 2;
        const tail = s.nose - s.len;
        const w = s.span / 2;
        paint(b, s.x - 0.18, apron[1], s.x + 0.18, s.nose + 6, .paint_line);
        paint(b, s.x - 3, s.nose + 5.8, s.x + 3, s.nose + 6.2, .paint_line);
        paint(b, s.x - w - 2.2, tail - 3, s.x - w - 1.8, s.nose + 4, .cloth_red);
        paint(b, s.x + w + 1.8, tail - 3, s.x + w + 2.2, s.nose + 4, .cloth_red);
        paint(b, s.x - w - 2.2, s.nose + 3.8, s.x + w + 2.2, s.nose + 4.2, .cloth_red);
        b.deco(vec(s.x - 2.2, 0.008, tail + 3), vec(s.x + 2.2, 0.03, s.nose - 2), .blob_soft);

        put(b, .barrier, s.x, s.nose + 4.5, pi);
        put(b, .barrier, s.x + 5, s.nose - 4, 0.25);
        put(b, .chock, s.x, s.nose - 3.5, 0);
        put(b, .chock, s.x - 3, cz - 1, 0);
        put(b, .chock, s.x + 3, cz - 1, 0);
        put(b, .cone, s.x - w + 1, cz, 0);
        put(b, .cone, s.x + w - 1, cz, 0);
        put(b, .cone, s.x, tail - 2.5, 0);
        put(b, .cone, s.x - w * 0.42, cz + 5, 0);
        put(b, .cone, s.x + w * 0.42, cz + 5, 0);
        put(b, .uld, s.x + 4.5, tail + s.len * 0.3, -0.45);
        put(b, .barrier, s.x + 11, tail + s.len * 0.22, 0);
        put(b, .uld, s.x + 11, tail + s.len * 0.22 - 4.2, 0);
        put(b, .uld, s.x + 11, tail + s.len * 0.22 - 8.4, 0);
        put(b, .uld, s.x + 11, tail + s.len * 0.22 - 12.2, 0);
        put(b, .uld, s.x + 14.5, tail + s.len * 0.22 - 5, 0);
        put(b, .uld, s.x + 14.5, tail + s.len * 0.22 - 7, 0);
        put(b, .uld, s.x + 6.5, s.nose - s.len * 0.78, hp);
        put(b, .uld, s.x - w * 0.55, cz - s.len * 0.36, 0);
        put(b, .barrier, s.x - 5.5, tail + s.len * 0.2, 0.35);

        if (s.bridge) {
            place(b, .lounge, s.x - 26, -22, 0);
            place(b, .bridge, s.x - 18, s.nose - 6, 0);
            put(b, .seats, s.x - 32, -18, hp);
            put(b, .uld, s.x - 22, -19, 0.1);
            put(b, .uld, s.x - 22, -17, 0);
        } else {
            put(b, .barrier, s.x - 5, s.nose - 6, -0.3);
            put(b, .uld, s.x - 15, s.nose - 2, 0);
            put(b, .barrier, s.x + 10, s.nose + 8, 0.6);
        }
    }
}

fn gseRow(b: *Builder, e: K, x: f32, z: f32, n: usize, step: f32, yaw: f32) void {
    var i: usize = 0;

    while (i < n) : (i += 1) put(b, e, x + @as(f32, @floatFromInt(i)) * step, z, yaw + jitter(b, 0.04));
}

fn workZone(b: *Builder, x: f32, z: f32) void {
    for ([_]f32{ -6, -2, 2, 6 }) |o| {
        put(b, .crashbar, x + o, z - 8, 0);
        put(b, .crashbar, x + o, z + 8, 0);
    }

    for ([_]f32{ -4, 0, 4 }) |o| {
        put(b, .crashbar, x - 8, z + o, hp);
        put(b, .crashbar, x + 8, z + o, hp);
    }

    put(b, .barrier, x - 2, z, 0.2);
    put(b, .uld, x + 3, z + 3, 2.2);
    put(b, .uld, x + 4, z - 4, 0);
    put(b, .uld, x + 4, z - 5.8, 0);
    put(b, .cone, x - 10, z - 10, 0);
    put(b, .cone, x + 10, z + 10, 0);
    paint(b, x - 9, z - 9, x + 9, z - 8.7, .f_hazard);
    paint(b, x - 9, z + 8.7, x + 9, z + 9, .f_hazard);
}

fn train(b: *Builder, x: f32, z: f32, yaw: f32, n: usize) void {
    const dx = @sin(yaw);
    const dz = @cos(yaw);
    var i: usize = 0;

    put(b, .barrier, x, z, yaw);

    while (i < n) : (i += 1) {
        const d = 3.8 + @as(f32, @floatFromInt(i)) * 4.0;

        put(b, .uld, x - dx * d, z - dz * d, yaw + jitter(b, 0.05));
    }
}

fn clutter(b: *Builder) void {
    var z: f32 = -104;

    while (z < -30) : (z += 15) {
        var x: f32 = -180;

        while (x < 180) : (x += 17) {
            const px = x + jitter(b, 4);
            const pz = z + jitter(b, 4);

            if (wd.covered(b, px, pz, 5)) continue;

            const roll = b.rng.next();
            const yaw = b.rng.range(0, std.math.tau);

            if (roll < 0.22) {
                train(b, px, pz, yaw, 2 + @as(usize, @intFromFloat(b.rng.range(0, 3))));
            } else if (roll < 0.4) {
                put(b, .uld, px, pz, yaw);
                put(b, .uld, px + 2.1, pz, yaw);
                put(b, .uld, px + 1, pz + 2.6, yaw);
            } else if (roll < 0.55) {
                put(b, .barrier, px, pz, yaw);
                put(b, .cone, px + 3, pz + 2, 0);
            } else if (roll < 0.68) {
                put(b, .barrier, px, pz, yaw);
            } else if (roll < 0.8) {
                put(b, .crashbar, px, pz, yaw);
                put(b, .crashbar, px + 4 * @cos(yaw), pz - 4 * @sin(yaw), yaw);
            } else {
                put(b, .uld, px, pz, yaw);
                put(b, .cone, px - 2, pz - 3, 0);
            }
        }
    }
}

fn service(b: *Builder) void {
    workZone(b, -92, -70);
    workZone(b, 100, -92);
    train(b, -100, -44, hp, 4);
    train(b, -20, -104, -hp, 5);
    train(b, 44, -60, 0, 3);
    train(b, 120, -40, hp, 3);
    put(b, .barrier, -84, -100, 0.6);
    put(b, .uld, 100, -56, 0.1);
    put(b, .uld, 104, -72, pi);
    put(b, .barrier, -36, -100, 0.4);
    put(b, .barrier, 46, -100, -0.8);
    put(b, .uld, -6, -108, hp);

    for (0..4) |i| {
        const f: f32 = @floatFromInt(i);

        put(b, .uld, -76 + f * 2.2, -24, 0);
        put(b, .uld, -76 + f * 2.2, -26.2, 0);
    }

    gseRow(b, .uld, 40, -18, 8, 2.3, 0);
    gseRow(b, .uld, 40, -24, 8, 2.3, 0);
    gseRow(b, .barrier, 62, -18, 3, 2.6, 0);
    gseRow(b, .barrier, 72, -22, 3, 4, 0);
    gseRow(b, .uld, 88, -20, 3, 3.2, 0);
    gseRow(b, .uld, 40, -29, 6, 2.2, 0);
    gseRow(b, .uld, 40, -31, 6, 2.2, 0);
    paint(b, 38, -33, 102, -32.7, .paint_line);
    paint(b, 38, -33, 38.3, -14, .paint_line);
    paint(b, 101.7, -33, 102, -14, .paint_line);

    var hx: f32 = 40;

    while (hx < 100) : (hx += 6) paint(b, hx, -35, hx + 2.5, -33.5, .f_hazard);

    put(b, .crashbar, 106, -16, hp);
    put(b, .crashbar, 106, -20, hp);
    put(b, .crashbar, 106, -24, hp);
    put(b, .barrier, 104, -40, 0.3);
    put(b, .barrier, 50, -40, 1.2);
    put(b, .uld, 30, -108, hp);
    put(b, .uld, -24, -104, 0.2);
    put(b, .barrier, -96, -96, 0.4);
    put(b, .uld, -110, -18, hp);
    put(b, .uld, -110, -26, hp);

    for (0..5) |i| {
        const f: f32 = @floatFromInt(i);

        put(b, .uld, -40 + f * 2.2, -16, 0);
    }

    put(b, .barrier, -46, -16, 0);
}

fn cargo(b: *Builder) void {
    place(b, .cargo, -160, 4, pi);
    paint(b, -164.2, apron[1], -163.8, -56, .paint_line);
    b.deco(vec(-166.2, 0.008, -98), vec(-161.8, 0.03, -64), .blob_soft);
    put(b, .uld, -156, -60, pi);
    put(b, .barrier, -164, -57, pi);
    put(b, .uld, -170, -96, 0.5);
    put(b, .uld, -178, -84, 0);

    var r: usize = 0;

    while (r < 3) : (r += 1) {
        const rz = -22 - @as(f32, @floatFromInt(r)) * 6;
        var c: usize = 0;

        while (c < 7) : (c += 1) {
            const cxx = -184 + @as(f32, @floatFromInt(c)) * 2.3;
            if ((c + r) % 3 != 0) put(b, .uld, cxx, rz, hp);
        }

        put(b, .barrier, -188, rz, hp);
    }

    for (0..9) |i| {
        const f: f32 = @floatFromInt(i);

        put(b, .uld, -148 + f * 2.2, -20, 0);
        put(b, .uld, -148 + f * 2.2, -22.2, 0);

        if (i % 2 == 0) b.putAt(kit.of(.uld), vec(-148 + f * 2.2, 1.64, -21.1), 0, 1);
    }

    put(b, .uld, -136, -18, 0.6);
    put(b, .uld, -176, -10, -0.4);
    put(b, .uld, -150, -12, 2.6);
    put(b, .uld, -132, -30, 0);
    put(b, .barrier, -146, -40, 1.4);

    for ([_]f32{ -146, -146, -146 }, 0..) |cxv, i| put(b, .cone, cxv, -50 - @as(f32, @floatFromInt(i)) * 7, 0);

    for ([_]f32{ -180, -172, -164, -156, -148, -140 }) |fx| {
        put(b, .uld, fx, 18, 0);
        put(b, .uld, fx + 2.1, 18, 0);
    }

    put(b, .uld, -134, 14, hp);
    place(b, .radar, -176, 40, 0);
}

fn maintenance(b: *Builder) void {
    const hx = hangar[0];
    const hz = hangar[1];

    place(b, .hangar, hx, hz, hangar[2]);
    put(b, .barrier, hx + 16, hz - 6, hp);
    put(b, .barrier, hx - 18, hz + 8, pi);
    put(b, .barrier, hx + 4, hz - 12, pi);
    put(b, .uld, hx + 20, hz + 14, 0.8);
    put(b, .uld, hx - 22, hz + 16, 0);
    put(b, .uld, hx - 20, hz + 16, 0);
    put(b, .barrier, hx - 4, hz - 4, 0.4);
    paint(b, hx - 0.18, apron[1], hx + 0.18, hz - 22, .paint_line);

    for (0..4) |i| {
        const f: f32 = @floatFromInt(i);
        put(b, .chock, 118 + f * 17, -64, 0);
        put(b, .cone, 112 + f * 17, -66, 0);
    }
    put(b, .barrier, 184, -78, 0.5);
    put(b, .uld, 114, -96, hp);
    put(b, .barrier, 174, -88, 0);

    for ([_]f32{ 184, 184, 184, 184 }, 0..) |cxv, i| put(b, .crashbar, cxv, -40 - @as(f32, @floatFromInt(i)) * 4.2, hp);

    put(b, .uld, 178, -30, 0.2);
    put(b, .uld, 180, -30, 0);
}

fn landside(b: *Builder) void {
    var lx: f32 = park[0] + 3;

    while (lx < park[2] - 2) : (lx += 2.9) {
        for ([_]f32{ 49, 59, 71, 81, 93 }, 0..) |lz, ri| {
            const roll = b.rng.next();

            if (roll < 0.86) continue;

            const e: K = .barrier;
            const face: f32 = if (ri % 2 == 0) 0 else pi;

            put(b, e, lx + jitter(b, 0.15), lz + jitter(b, 0.25), face + jitter(b, 0.06));
        }
    }

    var bay: f32 = park[0] + 1.5;

    while (bay < park[2]) : (bay += 2.9) {
        for ([_]f32{ 46.5, 56.5, 68.5, 78.5, 90.5 }) |lz| paint(b, bay, lz, bay + 0.12, lz + 5, .marking);
    }

    for ([_]f32{ 65, 87 }) |hz| row(b, .hedge, park[0] + 4, hz, park[2] - 4, hz, 5, 0);

    for ([_][2]f32{ .{ -96, 65 }, .{ -96, 87 }, .{ -20, 65 }, .{ -20, 87 }, .{ -58, 65 }, .{ -58, 87 } }) |p| {
        put(b, .lamp, p[0], p[1], 0);
        put(b, .tree, p[0] + 6, p[1] + 0.5, b.rng.range(0, 6));
    }

    kerb(b, park[0], park[1], park[2], park[1] + 0.3);
    kerb(b, park[0], park[3] - 0.3, park[2], park[3]);
    kerb(b, park[2] - 0.3, park[1], park[2], park[3]);

    place(b, .carpark, -150, 72, hp);
    put(b, .barrier, -126, 44, hp);
    put(b, .barrier, -126, 104, hp);

    for ([_]f32{ -176, -172, -168, -164 }) |cxv| {
        put(b, .barrier, cxv, 102, 0);
        put(b, .barrier, cxv + 1, 42, pi);
    }

    place(b, .tower, 80, 46, 0);
    b.deco(vec(73, 0.008, 39), vec(87, 0.03, 53), .blob_soft);

    for ([_][2]f32{ .{ 64, 34 }, .{ 96, 34 }, .{ 64, 58 }, .{ 96, 58 } }) |p| put(b, .tree, p[0], p[1], b.rng.range(0, 6));

    put(b, .barrier, 70, 40, 0.3);
    put(b, .barrier, 90, 38, -0.2);
    put(b, .barrier, 94, 40, -0.2);

    place(b, .fire, 158, 90, pi);

    for ([_]f32{ 142, 152, 164, 174 }) |tx| put(b, .uld, tx, 72, pi);

    put(b, .barrier, 184, 70, 0.4);
    put(b, .windsock, 184, 52, 0);
    put(b, .crashbar, 120, 66, 0);
    put(b, .crashbar, 124, 66, 0);

    place(b, .cargo, 0, 82, 0);
    put(b, .uld, -10, 64, 0.4);
    put(b, .uld, 8, 62, 2.4);
    put(b, .uld, 18, 60, hp);
    put(b, .uld, -24, 70, 0);

    for (0..6) |i| {
        const f: f32 = @floatFromInt(i);

        put(b, .uld, -12 + f * 2.2, 58, 0);

        if (i % 2 == 1) b.putAt(kit.of(.uld), vec(-12 + f * 2.2, 1.64, 58), 0.1, 1);
    }

    for ([_]f32{ -28, 28 }) |sx| {
        put(b, .tree, sx, 98, b.rng.range(0, 6));
        put(b, .shrub, sx, 92, 0);
        put(b, .shrub, sx, 66, 0);
    }

    var ex: f32 = 62;

    while (ex < 96) : (ex += 2.9) {
        for ([_]f32{ 82, 96 }, 0..) |ez, ri| {
            if (b.rng.next() < 0.86) continue;

            put(b, .barrier, ex, ez, if (ri == 0) 0 else pi);
        }
    }

    row(b, .hedge, 60, 89, 96, 89, 5, 0);

    var wz: f32 = 30;

    while (wz < 104) : (wz += 2.9) {
        if (b.rng.next() < 0.84) continue;

        put(b, .barrier, -182, wz, hp);
    }

    for ([_]f32{ 36, 60, 84 }) |tz| put(b, .tree, -174, tz, b.rng.range(0, 6));
}

fn north(b: *Builder) void {
    place(b, .hotel, -60, 152, pi);
    b.deco(vec(-73, 0.008, 143), vec(-47, 0.03, 161), .blob_soft);

    for ([_]f32{ -84, -36 }) |tx| {
        put(b, .tree, tx, 140, b.rng.range(0, 6));
        put(b, .tree, tx, 166, b.rng.range(0, 6));
    }

    put(b, .barrier, -70, 130, hp);
    put(b, .barrier, -58, 130, hp);
    put(b, .uld, -40, 128, hp);
    put(b, .canopy, -50, 134, 0);
    row(b, .hedge, -88, 136, -32, 136, 5, 0);

    var gx: f32 = -188;

    while (gx < -100) : (gx += 2.9) {
        for ([_]f32{ 132, 144, 158, 170, 182 }, 0..) |gz, ri| {
            if (b.rng.next() < 0.86) continue;

            const e: K = .barrier;

            put(b, e, gx, gz, if (ri % 2 == 0) 0 else pi);
        }
    }

    var bx: f32 = 62;

    while (bx < 102) : (bx += 4.6) {
        put(b, .uld, bx, 140, 0);

        if (b.rng.next() < 0.7) put(b, .uld, bx, 162, pi);
    }

    for ([_][2]f32{ .{ 126, 146 }, .{ 154, 146 }, .{ 126, 174 }, .{ 154, 174 } }) |p| place(b, .tank, p[0], p[1], 0);

    b.deco(vec(112, 0.2, 132), vec(170, 0.5, 132.3), .concrete);
    put(b, .uld, 140, 134, hp);
    put(b, .uld, 172, 160, 0);
    put(b, .uld, 176, 176, 0);
    row(b, .fence, 110, 128, 186, 128, 5, 0);
    row(b, .fence, 110, 128, 110, 188, 5, hp);

    place(b, .gatehouse, 46, 176, 0);
    put(b, .barrier, 43, 170, 0);
    put(b, .barrier, 49, 182, pi);

    var ax: f32 = -186;

    while (ax < 190) : (ax += 20) put(b, .lamp, ax, 124, 0);

    var az: f32 = 40;

    while (az < 190) : (az += 20) put(b, .lamp, 54, az, hp);

    var mx: f32 = -190;

    while (mx < 190) : (mx += 9) paint(b, mx, 115.9, mx + 4.5, 116.1, .marking);

    var mz: f32 = 24;

    while (mz < 190) : (mz += 9) paint(b, 45.9, mz, 46.1, mz + 4.5, .marking);

    kerb(b, -192, 109.7, 192, 110);
    kerb(b, -192, 122, 192, 122.3);

    for ([_][2]f32{ .{ -30, 176 }, .{ -14, 160 }, .{ 2, 180 }, .{ 18, 150 }, .{ -10, 136 }, .{ 24, 172 }, .{ 120, 104 }, .{ 30, 104 }, .{ -34, 104 } }) |p| {
        put(b, .tree, p[0], p[1], b.rng.range(0, 6));
        put(b, .shrub, p[0] + 3, p[1] - 2, 0);
    }

}

fn perimeter(b: *Builder) void {
    const e = t.play - 1;

    row(b, .fence, -e, -e, e, -e, 5, 0);
    row(b, .fence, -e, e, e, e, 5, 0);
    row(b, .fence, -e, -e, -e, e, 5, hp);
    row(b, .fence, e, -e, e, e, 5, hp);

    var a: f32 = -t.half + 2;

    while (a < t.half - 2) : (a += 8) {
        for ([_]f32{ -1, 1 }) |s| {
            const off = t.play + 6 + b.rng.range(0, 14);

            put(b, if (b.rng.next() < 0.65) .pine else .tree, a + jitter(b, 3), s * off, b.rng.range(0, 6));
            put(b, if (b.rng.next() < 0.65) .pine else .tree, s * off, a + jitter(b, 3), b.rng.range(0, 6));
        }
    }

    for ([_][3]f32{ .{ -160, 212, 1.0 }, .{ -110, 210, 0.85 }, .{ 70, 214, 1.1 }, .{ 130, 211, 0.9 } }) |p| scaled(b, .hotel, p[0], p[1], pi, p[2]);

    for ([_][2]f32{ .{ -20, 214 }, .{ 190, 210 } }) |p| scaled(b, .carpark, p[0], p[1], 0, 1);

    place(b, .vor, -100, -196, 0);
}
