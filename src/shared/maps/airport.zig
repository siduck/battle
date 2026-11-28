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

const rw = [4]f32{ 0, -60, api.arena_half - 13, 9 };
const twy_z: f32 = -41;
const twy_w: f32 = 6;
const apron = [4]f32{ -api.arena_half + 5, -35, api.arena_half - 5, 0 };
const term = [4]f32{ -56, 0, 8, 32 };
const roof: f32 = 9.5;
const hangar = [3]f32{ 46, -8, pi };
const park = [4]f32{ -66, 57, -16, 72 };
const road = [4]f32{ term[0] - 2, term[3] + 4, 20, term[3] + 16 };

pub const def: api.Def = .{
    .name = "Airport",
    .note = "Runways, terminal and hangars",
    .tint = .{ 150, 170, 196 },
    .ready = true,
    .facet = 2.5,
    .runway = rw,
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
    .grip = 0.86,
};

fn inRect(x: f32, z: f32, r: [4]f32) bool {
    return x >= r[0] and x <= r[2] and z >= r[1] and z <= r[3];
}

fn hash(x: f32, z: f32) f32 {
    return wd.hash2(x, z);
}

fn height(x: f32, z: f32) f32 {
    const edge = @max(@abs(x), @abs(z));
    const rim = t.smooth(t.play + 1, t.half - 4, edge);
    const roll = 5 + t.fbm(x * 0.03, z * 0.03) * 9;

    return rim * roll;
}

const roads = [_][4]f32{
    road,
    .{ park[2] - 6, road[3], park[2], park[1] },
};

const lots = [_][4]f32{
    park,
};

const apron_lanes = [_][4]f32{
    .{ apron[0], apron[1], apron[2], apron[1] + 3 },
    .{ apron[0], apron[1] + 3, apron[0] + 6, apron[3] },
    .{ -28, apron[1] + 3, -22, apron[3] },
    .{ 10, apron[1] + 3, 16, apron[3] },
};

const yards = [_][4]f32{
    .{ -8, park[1] - 2, 14, park[3] + 2 },
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

    if (@abs(z - twy_z) < twy_w and @abs(x) < rw[2] + 6) return api.shade(stain(x, z, slab(x, z, .{ 88, 90, 94 }, 7.5, 0.03)), l);

    if (inRect(x, z, term)) {
        const c = @mod(@floor(x / 2.5) + @floor(z / 2.5), 2) == 0;

        return if (c) .{ 214, 210, 200 } else .{ 196, 192, 182 };
    }

    if (inRect(x, z, .{ hangar[0] - 27, hangar[1] - 23, hangar[0] + 27, hangar[1] + 23 })) return api.shade(slab(x, z, .{ 150, 152, 152 }, 5, 0.03), l);

    for (apron_lanes) |r| {
        if (inRect(x, z, r)) return api.shade(stain(x, z, slab(x, z, .{ 112, 114, 118 }, 7.5, 0.03)), l);
    }

    if (inRect(x, z, apron)) return api.shade(stain(x, z, slab(x, z, .{ 172, 172, 166 }, 7.5, 0.05)), l);

    if (inRect(x, z, .{ road[0], term[3], road[2], road[1] }) or inRect(x, z, .{ road[0], road[3], road[2], road[3] + 6 })) return api.shade(slab(x, z, .{ 186, 182, 172 }, 2.5, 0.05), l);

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
    maintenance(b);
    fillApron(b);
    landside(b);
    perimeter(b);
}

fn airfield(b: *Builder) void {
    wd.runway(b);

    var x: f32 = -rw[2] + 4;

    while (x <= rw[2] - 4) : (x += 16) {
        put(b, .edge, x, rw[1] - rw[3] - 1.2, 0);
        put(b, .edge, x, rw[1] + rw[3] + 1.2, 0);
    }

    const tw = rw[2] + 4;

    x = -tw;

    while (x < tw) : (x += 10) {
        paint(b, x, twy_z - 0.18, x + 6, twy_z + 0.18, .paint_line);
        put(b, .edge, x + 3, twy_z - twy_w - 0.6, 0);
    }

    paint(b, -tw, twy_z - twy_w + 0.1, tw, twy_z - twy_w + 0.4, .paint_line);
    paint(b, -tw, twy_z + twy_w - 0.4, tw, twy_z + twy_w - 0.1, .paint_line);

    for ([_]f32{ -1, 1 }) |side| {
        for (0..3) |i| put(b, .crashbar, side * (tw + 1), twy_z - 4 + @as(f32, @floatFromInt(i)) * 4, hp);
    }

    for ([_]f32{ -36, 0, 36 }) |sx| {
        put(b, .twysign, sx, rw[1] + rw[3] + 4, 0);
        paint(b, sx - 0.18, twy_z - twy_w, sx + 0.18, rw[1] + rw[3], .paint_line);
    }

    for ([_]f32{ -1, 1 }) |side| {
        var z: f32 = rw[1] - 10;

        while (z <= rw[1] + 10) : (z += 4) place(b, .deflector, side * (rw[2] + 4), z, side * hp);

        place(b, .localizer, side * (rw[2] + 9), rw[1], hp);
    }

    put(b, .windsock, 40, rw[1] - rw[3] - 5, 0);
    put(b, .windsock, -30, twy_z + twy_w + 2, 0);

    var fx: f32 = -60;

    while (fx <= 0) : (fx += 30) place(b, .flood, fx, apron[1] + 2, 0);

    var jx: f32 = apron[0] + 2;

    while (jx < apron[2]) : (jx += 7.5) paint(b, jx, apron[1], jx + 0.1, apron[3], .scuff_soft);

    var jz: f32 = apron[1] + 7.5;

    while (jz < apron[3]) : (jz += 7.5) paint(b, apron[0], jz, apron[2], jz + 0.1, .scuff_soft);

    paint(b, apron[0], apron[1] + 0.2, apron[2], apron[1] + 0.5, .paint_line);
    paint(b, apron[0], apron[1] + 3, apron[2], apron[1] + 3.3, .marking);

    var dx: f32 = apron[0];

    while (dx < apron[2]) : (dx += 6) paint(b, dx, apron[3] - 2.4, dx + 3, apron[3] - 2.1, .marking);
}

fn terminal(b: *Builder) void {
    const x0 = term[0];
    const x1 = term[2];
    const z0 = term[1];
    const z1 = term[3];
    const doors_n = [_]usize{ 1, 4, 6 };
    const doors_s = [_]usize{ 2, 5 };
    const n: usize = @intFromFloat((x1 - x0) / 8);
    var i: usize = 0;

    while (i < n) : (i += 1) {
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
    b.mass(vec(x0, roof + 0.7, z0), vec(x0 + 0.4, roof + 1.6, z0 + 8), .f_grey_dark);
    b.mass(vec(x1 - 0.4, roof + 0.7, z0), vec(x1, roof + 1.6, z1), .f_grey_dark);

    for ([_][4]f32{ .{ 12, 6, 9, 6 }, .{ 32, 18, 7, 7 }, .{ 50, 5, 8, 6 } }) |r| {
        const u = [4]f32{ x0 + r[0], z0 + r[1], r[2], r[3] };

        b.mass(vec(u[0], roof + 0.7, u[1]), vec(u[0] + u[2], roof + 2.5, u[1] + u[3]), .f_metal);
        b.mass(vec(u[0] + 0.5, roof + 2.5, u[1] + 0.5), vec(u[0] + u[2] - 0.5, roof + 2.9, u[1] + u[3] - 0.5), .f_grey_dark);
        b.deco(vec(u[0] - 0.4, roof + 0.7, u[1] - 0.4), vec(u[0] + u[2] + 0.4, roof + 0.78, u[1] + u[3] + 0.4), .blob_soft);
    }

    for ([_][2]f32{ .{ 26, 10 }, .{ 44, 22 } }) |p| {
        b.mass(vec(x0 + p[0], roof + 0.7, z0 + p[1]), vec(x0 + p[0] + 2.2, roof + 1.6, z0 + p[1] + 2.2), .f_grey_dark);
    }

    var px: f32 = x0 + 16;

    while (px < x1 - 8) : (px += 16) {
        for ([_]f32{ z0 + 8, z0 + 24 }) |pz| b.mass(vec(px - 0.45, 0, pz - 0.45), vec(px + 0.45, roof, pz + 0.45), .concrete);
    }

    var wx: f32 = x0 + 4;

    while (wx < x1 - 12) : (wx += 16) {
        b.mass(vec(wx, 0, z0 + 15.6), vec(wx + 8, 2.4, z0 + 16.2), .f_grey);
        b.deco(vec(wx, 2.4, z0 + 15.5), vec(wx + 8, 2.6, z0 + 16.3), .f_grey_dark);
        put(b, .arch, wx + 10, z0 + 15.9, 0);
        put(b, .arch, wx + 12.5, z0 + 15.9, 0);
        put(b, .depboard, wx + 4, z0 + 17.4, 0);
    }

    for ([_]f32{ x0 + 14, x0 + 46 }) |cx| {
        var dz: f32 = 0;

        while (dz < 3) : (dz += 1) {
            put(b, .checkin, cx, z0 + 21 + dz * 2.5, hp);
            put(b, .checkin, cx + 3, z0 + 21 + dz * 2.5, -hp);
        }

        b.mass(vec(cx - 0.6, 0, z0 + 19.2), vec(cx + 3.6, 2.6, z0 + 19.8), .f_grey);
        put(b, .trolley, cx + 8, z0 + 23, b.rng.range(0, 6));
        put(b, .trolley, cx + 8.7, z0 + 23.6, b.rng.range(0, 6));
        put(b, .trolley, cx - 5, z0 + 26, b.rng.range(0, 6));
    }

    var sx: f32 = x0 + 6;

    while (sx < x1 - 8) : (sx += 10) {
        put(b, .seats, sx, z0 + 5, 0);
        put(b, .seats, sx + 2.6, z0 + 5, 0);
        put(b, .seats, sx, z0 + 8, pi);
        put(b, .seats, sx + 2.6, z0 + 8, pi);

        if (@mod(sx, 20) < 10) put(b, .depboard, sx + 7, z0 + 2.5, pi) else put(b, .trolley, sx + 7, z0 + 11, b.rng.range(0, 6));
    }

    var cx: f32 = x0 + 4;

    while (cx < x1) : (cx += 8) place(b, .canopy, cx, z1 + 6, 0);

    kerb(b, road[0], road[3], road[2], road[3] + 0.3);
    kerb(b, road[0], road[1] - 0.3, road[2], road[1]);
    kerb(b, road[0], road[3] + 5.7, road[2], road[3] + 6);

    var bx: f32 = x0 + 4;

    while (bx < x1) : (bx += 12) put(b, .bollards, bx, road[3] + 4, 0);

    var mx: f32 = road[0] + 4;

    while (mx < road[2] - 4) : (mx += 9) paint(b, mx, (road[1] + road[3]) / 2 - 0.1, mx + 4.5, (road[1] + road[3]) / 2 + 0.1, .marking);

    for ([_]f32{ road[0], road[2] }) |ex| {
        var bz: f32 = road[1] + 1.5;

        while (bz < road[3]) : (bz += 3) put(b, .barrier, ex, bz, hp);
    }

    var lx: f32 = road[0] + 4;

    while (lx < road[2]) : (lx += 18) put(b, .lamp, lx, road[3] + 4.8, pi);

    for ([_]f32{ x0 - 12, x1 + 4 }) |hx| put(b, .shrub, hx, z1 + 2, 0);
}

fn roofAccess(b: *Builder) void {
    const x0: f32 = term[0] - 8;
    const x1: f32 = term[0] - 3;
    const top = roof + 0.7;
    const z_hi: f32 = term[1] + 18;
    const z_lo: f32 = term[1] + 54;
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

const Stand = struct { x: f32, nose: f32, len: f32, span: f32 };

const stands = [_]Stand{
    .{ .x = -46, .nose = -18, .len = 12, .span = 24 },
    .{ .x = -6, .nose = -18, .len = 12, .span = 24 },
};
const box_h: f32 = 2.808;
const pallet_h: f32 = 0.144;

const Frame = struct {
    x: f32,
    z: f32,
    yaw: f32,

    fn at(f: Frame, lx: f32, lz: f32) [2]f32 {
        const c = @cos(f.yaw);
        const s = @sin(f.yaw);

        return .{ f.x + lx * c + lz * s, f.z - lx * s + lz * c };
    }

    fn sub(f: Frame, lx: f32, lz: f32, yaw: f32) Frame {
        const p = f.at(lx, lz);

        return .{ .x = p[0], .z = p[1], .yaw = f.yaw + yaw };
    }
};

fn fr(x: f32, z: f32, yaw: f32) Frame {
    return .{ .x = x, .z = z, .yaw = yaw };
}

fn lput(b: *Builder, f: Frame, e: K, lx: f32, lz: f32, yaw: f32) void {
    const p = f.at(lx, lz);

    put(b, e, p[0], p[1], f.yaw + yaw);
}

fn lup(b: *Builder, f: Frame, e: K, lx: f32, lz: f32, yaw: f32, lift: f32) void {
    const p = f.at(lx, lz);

    b.putAt(kit.of(e), vec(p[0], t.height(p[0], p[1]) + lift, p[1]), f.yaw + yaw, 1);
}

fn lpaint(b: *Builder, f: Frame, x0: f32, z0: f32, x1: f32, z1: f32, tone: api.Tone) void {
    const a = f.at(x0, z0);
    const c = f.at(x1, z1);

    paint(b, @min(a[0], c[0]), @min(a[1], c[1]), @max(a[0], c[0]), @max(a[1], c[1]), tone);
}

fn boxAt(b: *Builder, f: Frame, lx: f32, lz: f32, level: f32, grey: bool) void {
    lup(b, f, if (grey) .boxgrey else .box, lx, lz, jitter(b, 0.015), level * box_h);
}

fn palletStack(b: *Builder, f: Frame, lx: f32, lz: f32, n: usize) void {
    for (0..n) |i| lup(b, f, .pallet, lx + jitter(b, 0.04), lz + jitter(b, 0.04), jitter(b, 0.08), @as(f32, @floatFromInt(i)) * pallet_h);
}

fn stairAt(b: *Builder, f: Frame, lx: f32, lz: f32, turn: f32) void {
    const p = f.at(lx, lz);
    const yaw = f.yaw + turn;
    const q: i32 = @mod(@as(i32, @intFromFloat(@round(yaw / hp))), 4);
    const y = t.height(p[0], p[1]);
    const long = q == 0 or q == 2;
    const hx: f32 = if (long) 0.5 else 2.45;
    const hz: f32 = if (long) 2.45 else 0.5;
    const rise: api.geom.Rise = switch (q) {
        0 => .neg_z,
        1 => .neg_x,
        2 => .pos_z,
        else => .pos_x,
    };

    b.putAt(kit.of(.stair), vec(p[0], y, p[1]), yaw, 1);
    b.solid(.{ .ramp = .{ .min = vec(p[0] - hx, y, p[1] - hz), .max = vec(p[0] + hx, y + 3.95, p[1] + hz), .rise = rise } });
}

fn cones(b: *Builder, f: Frame, x0: f32, z0: f32, x1: f32, z1: f32, n: usize) void {
    for (0..n) |i| {
        const q = @as(f32, @floatFromInt(i)) / @as(f32, @floatFromInt(@max(n - 1, 1)));

        lput(b, f, .cone, x0 + (x1 - x0) * q, z0 + (z1 - z0) * q, 0);
    }
}

fn cargoStack(b: *Builder, f: Frame) void {
    const g = b.rng.next() < 0.5;

    boxAt(b, f, 0, 0, 0, g);
    boxAt(b, f, 2.5, 0, 0, !g);
    boxAt(b, f, 5.0, 0.4, 0, g);
    boxAt(b, f, 0, 0, 1, !g);

    if (b.rng.next() < 0.6) boxAt(b, f, 2.5, 0, 1, g);

    if (b.rng.next() < 0.35) boxAt(b, f, 0, 0, 2, g);

    for (0..3) |i| {
        const fi: f32 = @floatFromInt(i);

        lput(b, f, .wrapped, 8 + fi * 1.2, -1.8, jitter(b, 0.1));

        if (i < 2) lput(b, f, .wrapped, 8.4 + fi * 1.3, -0.6, jitter(b, 0.1));
    }

    lput(b, f, .ibc, 8.2, 1.4, jitter(b, 0.1));
    lput(b, f, .ibc, 9.5, 1.5, jitter(b, 0.1));
    palletStack(b, f, 8.8, 3.4, 6);
    palletStack(b, f, 10.3, 3.2, 3);
    lput(b, f, .drum, -2.2, -2.0, 0);
    lput(b, f, .drum, -2.8, -1.3, 0);
    lput(b, f, .drum, -2.1, -0.6, 0);
    lput(b, f, .cone, -3.2, 3.4, 0);
    lput(b, f, .cone, 11.4, -3.4, 0);
    lpaint(b, f, -3.6, -3.6, 11.8, -3.3, .f_hazard);
}

fn maintBay(b: *Builder, f: Frame) void {
    lput(b, f, .engine, 0, 0, 0);
    stairAt(b, f, 2.5, 0.6, pi);
    lput(b, f, .vault, -3.6, 2.8, hp);
    lput(b, f, .genset, -3.8, -2.4, hp);
    lput(b, f, .cable, 3.8, 4.2, 0.4);
    lput(b, f, .lighttower, 5.8, -3.8, 0.5);
    lput(b, f, .drum, -5.2, 0.2, 0);
    lput(b, f, .drum, -5.7, 0.9, 0);
    lput(b, f, .drum, -5.0, 1.0, 0);
    lput(b, f, .wrapped, 4.6, -1.4, 0.1);
    lput(b, f, .ibc, 4.6, 1.0, -0.1);

    for (0..4) |i| lput(b, f, .rail, -3 + @as(f32, @floatFromInt(i)) * 2.05, -5.4, 0);

    for (0..3) |i| lput(b, f, .rail, -6.6, -3.6 + @as(f32, @floatFromInt(i)) * 2.05, hp);

    lput(b, f, .cone, 6.6, 5.4, 0);
    lput(b, f, .cone, -6.6, 5.4, 0);
    lpaint(b, f, -7, -6, 7, -5.7, .f_hazard);
    lpaint(b, f, -7, 5.7, 7, 6, .f_hazard);
    lpaint(b, f, -7, -6, -6.7, 6, .f_hazard);
    lpaint(b, f, 6.7, -6, 7, 6, .f_hazard);
}

fn uldBlock(b: *Builder, f: Frame) void {
    for (0..5) |i| {
        const fi: f32 = @floatFromInt(i);

        lput(b, f, .uld, fi * 2.15, 0, jitter(b, 0.03));

        if (i != 2) lput(b, f, .uld, fi * 2.15, 1.75, pi + jitter(b, 0.03));
    }

    palletStack(b, f, -2.4, 0.8, 4);
    lput(b, f, .wrapped, 11.4, 0.2, 0.05);
    lput(b, f, .wrapped, 11.6, 1.5, -0.08);
    lput(b, f, .crashbar, 4.3, -2.2, 0);
    lput(b, f, .cone, -2.8, -2.4, 0);
    lput(b, f, .cone, 12.6, 3.0, 0);
}

fn boxWall(b: *Builder, f: Frame, n: usize) void {
    for (0..n) |i| {
        const fi: f32 = @floatFromInt(i);
        const g = i % 3 == 1;

        boxAt(b, f, 0, fi * 5.6, 0, g);

        if (i % 2 == 0) boxAt(b, f, 0, fi * 5.6, 1, !g);
    }

    lput(b, f, .drum, 1.9, -2.2, 0);
    lput(b, f, .drum, 2.3, -1.5, 0);
    lput(b, f, .wrapped, -2.0, @as(f32, @floatFromInt(n)) * 5.6 - 2.4, 0.1);
}

fn standKit(b: *Builder, s: Stand) void {
    const tail = s.nose - s.len;
    const w = s.span / 2;
    const f = fr(s.x, s.nose, 0);

    paint(b, s.x - 0.18, apron[1], s.x + 0.18, s.nose + 6, .paint_line);
    paint(b, s.x - 3, s.nose + 5.8, s.x + 3, s.nose + 6.2, .paint_line);
    paint(b, s.x - w - 2.2, tail - 3, s.x - w - 1.8, s.nose + 4, .cloth_red);
    paint(b, s.x + w + 1.8, tail - 3, s.x + w + 2.2, s.nose + 4, .cloth_red);
    paint(b, s.x - w - 2.2, s.nose + 3.8, s.x + w + 2.2, s.nose + 4.2, .cloth_red);
    b.deco(vec(s.x - 2.2, 0.008, tail + 3), vec(s.x + 2.2, 0.03, s.nose - 2), .blob_soft);

    lput(b, f, .vdgs, 0, 6.6, pi);
    lput(b, f, .chock, -1.2, -3.5, 0);
    lput(b, f, .chock, 1.2, -3.5, 0);
    lput(b, f, .genset, 4, 2.2, 0);
    lput(b, f, .cable, 6, 2.4, 0.3);
    lput(b, f, .lighttower, w + 4, 1, 0.3);
    stairAt(b, f, -6, -6, hp);
    cones(b, f, -w + 1, -s.len * 0.45, -w + 1, -s.len * 0.45 - 4, 2);
    cones(b, f, w - 1, -s.len * 0.45, w - 1, -s.len * 0.45 - 4, 2);
    lput(b, f, .cone, 0, -s.len - 2.5, 0);
    uldBlock(b, f.sub(-12, -s.len + 2, 0));
    palletStack(b, f, w - 4, -s.len + 1, 5);
    lput(b, f, .wrapped, w - 5.4, -s.len + 1, 0.1);
    lput(b, f, .ibc, w - 4, -s.len - 0.8, 0.1);
}

fn hangarFill(b: *Builder, hx: f32, hz: f32, yaw: f32) void {
    const f = fr(hx, hz, yaw);

    maintBay(b, f.sub(-12, 4, 0));
    maintBay(b, f.sub(12, 6, hp));
    stairAt(b, f, -2, -4, 0);

    for ([_]f32{ -22, -18, -10, 6, 14, 20 }) |vx| lput(b, f, .vault, vx, -12.6, 0);

    boxAt(b, f, -24.2, -9.5, 0, true);
    boxAt(b, f, 24.2, -9.5, 0, false);
    boxAt(b, f, 24.2, -9.5, 1, true);

    for (0..4) |i| {
        const fi: f32 = @floatFromInt(i);

        lput(b, f, .wrapped, -25, 2 + fi * 1.3, jitter(b, 0.1));
        lput(b, f, .ibc, 25, 3 + fi * 1.4, jitter(b, 0.1));
    }

    palletStack(b, f, -25, 9, 7);
    palletStack(b, f, -23.6, 9.2, 4);
    lput(b, f, .lighttower, 0, -10, 0);
    lput(b, f, .genset, 3.5, -10.5, 0);
    lput(b, f, .cable, -4, -11, 0);
    lput(b, f, .cabin, -21, 15.5, hp);
    lput(b, f, .uld, 18, 17, 0.1);
    lput(b, f, .drum, 22, 16, 0);
    lput(b, f, .drum, 22.7, 16.6, 0);
    uldBlock(b, f.sub(-8, 15, 0));
    smallKit(b, f.sub(6, 16, 0));
    smallKit(b, f.sub(-19, -4, hp));
    lpaint(b, f, -26, 20, 26, 20.4, .f_hazard);
}

fn gates(b: *Builder) void {
    for (stands) |s| {
        standKit(b, s);
        place(b, .lounge, s.x - 9, term[1] - 8.5, 0);
        put(b, .seats, s.x - 14, term[1] - 6, hp);
    }
}

fn smallKit(b: *Builder, f: Frame) void {
    palletStack(b, f, 0, 0, 3 + @as(usize, @intFromFloat(b.rng.range(0, 4))));
    lput(b, f, .wrapped, 1.4, 0.1, jitter(b, 0.1));
    lput(b, f, .wrapped, 1.5, 1.3, jitter(b, 0.1));
    lput(b, f, .ibc, -0.1, 1.5, jitter(b, 0.1));
    lput(b, f, .drum, -1.4, -0.6, 0);
    lput(b, f, .drum, -1.6, 0.2, 0);
    lput(b, f, .cone, 2.6, -1.6, 0);
}

fn boxPair(b: *Builder, f: Frame) void {
    const g = b.rng.next() < 0.5;

    boxAt(b, f, 0, 0, 0, g);
    boxAt(b, f, 2.5, 0, 0, !g);

    if (b.rng.next() < 0.7) boxAt(b, f, 0, 0, 1, !g);

    lput(b, f, .drum, 4.4, -2, 0);
    lput(b, f, .drum, 4.9, -1.3, 0);
}

fn cabinSet(b: *Builder, f: Frame) void {
    lput(b, f, .cabin, 0, 0, 0);
    lput(b, f, .cabin, 4.6, 0, 0);
    lput(b, f, .cabin, -4.6, 0.4, pi);
    lput(b, f, .genset, 2.3, -5.6, 0);
    lput(b, f, .vault, 7.6, -2, hp);
}

const Fill = struct { x0: f32, z0: f32, x1: f32, z1: f32 };

const fills = [_]Fill{
    .{ .x0 = -3.6, .z0 = -3.6, .x1 = 11.8, .z1 = 4.2 },
    .{ .x0 = -7, .z0 = -6, .x1 = 7, .z1 = 6 },
    .{ .x0 = -7, .z0 = -6.4, .x1 = 9.6, .z1 = 4.4 },
    .{ .x0 = -3, .z0 = -2.6, .x1 = 13, .z1 = 3 },
    .{ .x0 = -1.4, .z0 = -2.9, .x1 = 5.4, .z1 = 2.9 },
    .{ .x0 = -2.2, .z0 = -2.2, .x1 = 3, .z1 = 2.2 },
};

fn openApron(x: f32, z: f32) bool {
    if (!inRect(x, z, .{ apron[0] + 2, apron[1] + 9, apron[2] - 2, apron[3] - 6 })) return false;

    for (apron_lanes) |r| {
        if (inRect(x, z, .{ r[0] - 1, r[1] - 1, r[2] + 1, r[3] + 1 })) return false;
    }

    for (stands) |s| {
        if (@abs(x - s.x) < 4 and z < s.nose + 8 and z > s.nose - s.len) return false;
    }

    return true;
}

fn fits(b: *Builder, f: Frame, r: Fill) bool {
    var i: usize = 0;

    while (i <= 4) : (i += 1) {
        var j: usize = 0;

        while (j <= 4) : (j += 1) {
            const lx = r.x0 + (r.x1 - r.x0) * @as(f32, @floatFromInt(i)) / 4;
            const lz = r.z0 + (r.z1 - r.z0) * @as(f32, @floatFromInt(j)) / 4;
            const p = f.at(lx, lz);

            if (!openApron(p[0], p[1])) return false;

            if (wd.covered(b, p[0], p[1], 1.6)) return false;
        }
    }

    return true;
}

fn fillApron(b: *Builder) void {
    var z: f32 = apron[1] + 14;
    var line: usize = 0;

    while (z < apron[3] - 8) : (z += 9.5) {
        defer line += 1;

        var x: f32 = apron[0] + 6 + @as(f32, @floatFromInt(line % 2)) * 5.5;

        while (x < apron[2] - 6) : (x += 11) {
            if (b.rng.next() < 0.35) continue;

            const f = fr(x + jitter(b, 2), z + jitter(b, 2), if (b.rng.next() < 0.5) 0 else pi);
            const start: usize = @intFromFloat(b.rng.range(0, 3.99));

            for (0..fills.len) |n| {
                const pick = if (n < 4) (start + n) % 4 else n;

                if (!fits(b, f, fills[pick])) continue;

                switch (pick) {
                    0 => cargoStack(b, f),
                    1 => maintBay(b, f),
                    2 => cabinSet(b, f),
                    3 => uldBlock(b, f),
                    4 => boxPair(b, f),
                    else => smallKit(b, f),
                }

                break;
            }
        }
    }
}

fn maintenance(b: *Builder) void {
    place(b, .hangar, hangar[0], hangar[1], hangar[2]);
    hangarFill(b, hangar[0], hangar[1], hangar[2]);
    paint(b, hangar[0] - 0.18, apron[1], hangar[0] + 0.18, hangar[1] - 24, .paint_line);
}

fn landside(b: *Builder) void {
    var bay: f32 = park[0] + 1.5;

    while (bay < park[2]) : (bay += 2.9) {
        for ([_]f32{ park[1] + 0.5, park[3] - 5.5 }) |lz| paint(b, bay, lz, bay + 0.12, lz + 5, .marking);
    }

    var lx: f32 = park[0] + 3;

    while (lx < park[2] - 2) : (lx += 2.9) {
        for ([_]f32{ park[1] + 3, park[3] - 3 }, 0..) |lz, ri| {
            if (b.rng.next() < 0.8) continue;

            put(b, .barrier, lx + jitter(b, 0.15), lz + jitter(b, 0.25), (if (ri == 0) @as(f32, 0) else pi) + jitter(b, 0.06));
        }
    }

    row(b, .hedge, park[0] + 4, (park[1] + park[3]) / 2, park[0] + 18, (park[1] + park[3]) / 2, 5, 0);
    row(b, .hedge, park[2] - 18, (park[1] + park[3]) / 2, park[2] - 4, (park[1] + park[3]) / 2, 5, 0);
    kerb(b, park[0], park[1], park[2], park[1] + 0.3);
    kerb(b, park[0], park[3] - 0.3, park[2], park[3]);

    for ([_]f32{ park[0] + 2, (park[0] + park[2]) / 2, park[2] - 2 }) |px| {
        put(b, .lamp, px, (park[1] + park[3]) / 2, 0);
        put(b, .tree, px, park[1] - 1.5, b.rng.range(0, 6));
    }

    place(b, .tower, 3, 64, 0);
    b.deco(vec(-4, 0.008, 57), vec(10, 0.03, 71), .blob_soft);

    for ([_][2]f32{ .{ -6, 56 }, .{ 12, 56 }, .{ 12, 72 } }) |p| put(b, .tree, p[0], p[1], b.rng.range(0, 6));

    put(b, .barrier, -2, 55, 0.3);
    put(b, .barrier, 8, 55, -0.2);
    put(b, .windsock, 66, 32, 0);

    for ([_][2]f32{ .{ 24, 60 }, .{ 66, 60 } }) |p| {
        put(b, .tree, p[0], p[1], b.rng.range(0, 6));
        put(b, .shrub, p[0] + 3, p[1] - 2, 0);
    }

    for ([_]f32{ 26, 38, 50, 62 }) |ux| put(b, .uld, ux, 33, hp);

    put(b, .crashbar, 22, 30, 0);
    put(b, .crashbar, 26, 30, 0);
}

fn perimeter(b: *Builder) void {
    const e = t.play - 1;

    row(b, .fence, -e, -e, e, -e, 5, 0);
    row(b, .fence, -e, e, e, e, 5, 0);
    row(b, .fence, -e, -e, -e, e, 5, hp);
    row(b, .fence, e, -e, e, e, 5, hp);

    const reach = t.play + 8;
    var a: f32 = -reach;

    while (a < reach) : (a += 8) {
        for ([_]f32{ -1, 1 }) |s| {
            const off = t.play + 5 + b.rng.range(0, 6);

            put(b, if (b.rng.next() < 0.65) .pine else .tree, a + jitter(b, 3), s * off, b.rng.range(0, 6));
            put(b, if (b.rng.next() < 0.65) .pine else .tree, s * off, a + jitter(b, 3), b.rng.range(0, 6));
        }
    }
}
