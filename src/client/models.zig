const std = @import("std");
const rl = @import("raylib");
const mips = @import("mips.zig");
const shared = @import("shared");
const mesh = @import("mesh.zig");
const palette = @import("palette.zig");

const Vec3 = shared.math.Vec3;
const vec = shared.math.vec;
const map = shared.map;
const weapons = shared.weapons;
const Paint = map.Paint;
const Builder = mesh.Builder;
const Basis = mesh.Basis;

pub const Chunk = struct {
    hi: rl.Mesh,
    lo: rl.Mesh,
    things: [6]rl.Mesh = undefined,
    things_n: usize = 0,
    cx: f32,
    cz: f32,
    r: f32,
};

pub var chunks: []Chunk = &.{};

pub const Scenery = struct {
    world: rl.Mesh,
    backdrop: rl.Mesh,
    sky: rl.Mesh,
};

pub fn buildScenery() Scenery {
    buildBlobs();

    if (shared.maps.current() != null) buildChunks();

    return .{ .world = buildWorld(), .backdrop = buildBackdrop(), .sky = buildSky() };
}

pub fn dropScenery(s: Scenery) void {
    const gpa = std.heap.page_allocator;

    rl.UnloadMesh(s.world);
    rl.UnloadMesh(s.backdrop);
    rl.UnloadMesh(s.sky);

    for (chunks) |c| {
        rl.UnloadMesh(c.hi);
        rl.UnloadMesh(c.lo);

        for (c.things[0..c.things_n]) |t| rl.UnloadMesh(t);
    }

    gpa.free(chunks);
    chunks = &.{};

    for (extra[0..extra_n]) |e| rl.UnloadMesh(e);

    extra_n = 0;
    gpa.free(blob);
    blob = &.{};
    blob_n = 0;

    if (ground_map) |t| rl.UnloadTexture(t);

    ground_map = null;
    gpa.free(ground_pixels);
    ground_pixels = &.{};
    ground_n = 0;
}

pub const Models = struct {
    world: rl.Mesh,
    backdrop: rl.Mesh,
    clouds: rl.Mesh,
    guns: [weapons.count]rl.Mesh,
    bands: [5]rl.Mesh,
    beams: [5]rl.Mesh,
    arrow: rl.Mesh,
    drone_body: rl.Mesh,
    drone_rotor: rl.Mesh,
    rocket: rl.Mesh,
    grenade: rl.Mesh,
    orb: rl.Mesh,
    blast: rl.Mesh,
    pickup: rl.Mesh,
    medkit: rl.Mesh,
    sky: rl.Mesh,
    sleeve: rl.Mesh,
    block_sleeve: rl.Mesh,
    block_glove: rl.Mesh,
    cuff: rl.Mesh,
    glove: rl.Mesh,

    pub fn build() Models {
        var models: Models = undefined;

        buildBlobs();

        if (shared.maps.current() != null or shared.terrain.current == .conquest or shared.terrain.current == .valley or shared.terrain.current == .facility) buildChunks();

        models.world = buildWorld();
        models.backdrop = buildBackdrop();
        models.clouds = buildClouds();

        for (&models.guns, weapons.specs) |*g, s| {
            g.* = buildGun(s);
        }

        for (&models.bands, &models.beams, palette.rarity_paint) |*band, *beam, p| {
            band.* = buildBand(p);
            beam.* = buildBeam(p);
        }

        models.arrow = buildArrow();
        models.drone_body = buildDroneBody();
        models.drone_rotor = buildDroneRotor();
        models.rocket = buildRocket();
        models.grenade = buildGrenade();
        models.orb = buildOrb(.orange, 255);
        models.blast = buildOrb(.yellow, 200);
        models.pickup = buildPickup();
        models.medkit = buildMedkit();
        models.sky = buildSky();
        models.sleeve = buildLimb(.glove, 14);
        models.cuff = buildLimb(.glove, 14);
        models.glove = buildGlove();
        models.block_sleeve = buildLimb(.olive, 4);
        models.block_glove = buildBlockGlove();

        return models;
    }
};

fn shade(base: [3]f32, k: f32) palette.Rgb {
    return .{ @intFromFloat(@min(255, base[0] * k)), @intFromFloat(@min(255, base[1] * k)), @intFromFloat(@min(255, base[2] * k)) };
}

fn conquestColor(x: f32, z: f32) palette.Rgb {
    const t = shared.terrain;
    const n = t.normal(x, z);
    const slope = 1 - n.y;
    const h = t.height(x, z);
    const vary = 0.96 + t.fbm(x * 0.08, z * 0.08) * 0.08;
    const light = vary + n.x * 0.02 - n.z * 0.015;
    const rd = t.roadDistance(x, z);
    const patch = t.fbm(x * 0.03 + 17, z * 0.03 - 4);
    const od = t.oasisDistance(x, z);
    var c: [3]f32 = mix3(.{ 138, 135, 89 }, .{ 147, 144, 96 }, t.smooth(0.25, 0.42, patch));

    c = mix3(c, .{ 153, 155, 106 }, t.smooth(0.6, 0.76, patch));
    c = mix3(c, .{ 143, 143, 97 }, t.districtMask(x, z) * 0.7);
    c = mix3(c, .{ 132, 131, 90 }, (1 - t.smooth(8, 18, t.riverDistance(x, z))) * 0.6);
    c = mix3(c, .{ 129, 120, 79 }, t.smooth(0.2, 0.4, slope));
    c = mix3(c, .{ 141, 135, 92 }, t.smooth(14, 30, h) * 0.6);
    c = mix3(c, .{ 123, 120, 80 }, (1 - t.smooth(t.road_half - 1, t.road_half + 5, rd)) * 0.7);
    c = mix3(c, .{ 125, 120, 65 }, 1 - t.smooth(16, 24, od));

    if (od < 13 and h > water_level - 0.2) c = .{ 86, 120, 51 };

    return shade(c, light);
}

var blob: []f32 = &.{};
var blob_n: usize = 0;

fn blobAt(x: f32, z: f32) f32 {
    if (blob_n == 0) return 0;

    const fx = x + shared.terrain.half;
    const fz = z + shared.terrain.half;

    if (fx < 0 or fz < 0) return 0;

    const i: usize = @intFromFloat(fx);
    const j: usize = @intFromFloat(fz);

    if (i >= blob_n or j >= blob_n) return 0;

    return blob[j * blob_n + i];
}

fn splat(x: f32, z: f32, r: f32, strength: f32) void {
    const t = shared.terrain;
    const x0: i32 = @intFromFloat(@floor(x + t.half - r));
    const x1: i32 = @intFromFloat(@ceil(x + t.half + r));
    const z0: i32 = @intFromFloat(@floor(z + t.half - r));
    const z1: i32 = @intFromFloat(@ceil(z + t.half + r));
    var j = @max(z0, 0);

    while (j <= @min(z1, @as(i32, @intCast(blob_n)) - 1)) : (j += 1) {
        var i = @max(x0, 0);

        while (i <= @min(x1, @as(i32, @intCast(blob_n)) - 1)) : (i += 1) {
            const cx = @as(f32, @floatFromInt(i)) + 0.5 - t.half;
            const cz = @as(f32, @floatFromInt(j)) + 0.5 - t.half;
            const d = @sqrt((cx - x) * (cx - x) + (cz - z) * (cz - z)) / r;

            if (d >= 1) continue;

            const k: usize = @intCast(j * @as(i32, @intCast(blob_n)) + i);

            blob[k] = @max(blob[k], (1 - d) * (1 - d) * strength);
        }
    }
}

fn buildBlobs() void {
    const t = shared.terrain;

    if (t.current != .valley and t.current != .islands and shared.maps.current() == null) return;

    blob_n = @intFromFloat(@ceil(t.half * 2));
    blob = std.heap.page_allocator.alloc(f32, blob_n * blob_n) catch {
        blob_n = 0;

        return;
    };
    @memset(blob, 0);

    for (shared.world.placements) |pl| {
        const name = shared.props.name(pl.kind);

        if (std.mem.startsWith(u8, name, "iv_ridge") or std.mem.startsWith(u8, name, "iv_range") or std.mem.startsWith(u8, name, "iv_under") or std.mem.startsWith(u8, name, "iv_cloud") or std.mem.startsWith(u8, name, "iv_waterfall") or std.mem.startsWith(u8, name, "grass")) continue;

        const info = shared.props.info(pl.kind);
        const ext = @max(info.max[0] - info.min[0], info.max[2] - info.min[2]) * pl.scale;
        const r = std.math.clamp(ext * 0.62, 0.9, 12);
        const strength: f32 = if (info.group == .tree) 0.55 else 0.45;

        if (@abs(pl.pos.y - t.height(pl.pos.x, pl.pos.z)) > 3) continue;

        splat(pl.pos.x, pl.pos.z, r, strength);
    }

    for (shared.world.vehicle_spots) |v| splat(v.pos.x, v.pos.z, 3.2, 0.5);
}

fn grounded(c: palette.Rgb, x: f32, z: f32, tri: u32) palette.Rgb {
    _ = tri;
    const k = 1 - 0.42 * blobAt(x, z);
    var out: palette.Rgb = undefined;

    for (0..3) |i| out[i] = @intFromFloat(@min(255, @as(f32, @floatFromInt(c[i])) * k));

    return out;
}

fn faceMix(a: palette.Rgb, c: palette.Rgb, e: palette.Rgb) palette.Rgb {
    var out: palette.Rgb = undefined;

    for (0..3) |i| {
        const sum = @as(u32, a[i]) + c[i] + e[i];

        out[i] = @intCast(sum / 3);
    }

    return out;
}

fn smoothNormal(x: f32, z: f32, e: f32) Vec3 {
    const t = shared.terrain;
    const dx = t.height(x + e, z) - t.height(x - e, z);
    const dz = t.height(x, z + e) - t.height(x, z - e);

    return (Vec3{ .x = -dx, .y = 2 * e, .z = -dz }).normalize();
}

fn smoothCorner(x: f32, z: f32) palette.Rgb {
    return grounded(groundColor(x, z), x, z, 0);
}

fn smoothTerrain() bool {
    if (shared.maps.current() != null) return true;

    return switch (shared.terrain.current) {
        .desert, .valley, .islands, .conquest, .facility => true,
        else => false,
    };
}

fn terrainCell(b: *Builder, x: f32, z: f32, cell: f32) void {
    const t = shared.terrain;
    const p00 = vec(x, t.height(x, z), z);
    const p10 = vec(x + cell, t.height(x + cell, z), z);
    const p01 = vec(x, t.height(x, z + cell), z + cell);
    const p11 = vec(x + cell, t.height(x + cell, z + cell), z + cell);

    if (smoothTerrain()) {
        const e = @max(cell * 0.8, 1.2);
        const n00 = smoothNormal(x, z, e);
        const n10 = smoothNormal(x + cell, z, e);
        const n01 = smoothNormal(x, z + cell, e);
        const n11 = smoothNormal(x + cell, z + cell, e);
        const c00 = smoothCorner(x, z);
        const c10 = smoothCorner(x + cell, z);
        const c01 = smoothCorner(x, z + cell);
        const c11 = smoothCorner(x + cell, z + cell);
        const low = t.void_floor + 1;
        const skip_low = t.current == .islands or t.current == .valley;

        if (!skip_low or (p00.y > low and p01.y > low and p11.y > low)) b.smoothTri(.{ p00, p01, p11 }, .{ n00, n01, n11 }, .{ c00, c01, c11 });

        if (!skip_low or (p00.y > low and p11.y > low and p10.y > low)) b.smoothTri(.{ p00, p11, p10 }, .{ n00, n11, n10 }, .{ c00, c11, c10 });

        return;
    }

    if (t.current == .islands or t.current == .valley) {
        const low = t.void_floor + 1;
        const c00 = groundColor(x, z);
        const c10 = groundColor(x + cell, z);
        const c01 = groundColor(x, z + cell);
        const c11 = groundColor(x + cell, z + cell);

        if (p00.y > low and p01.y > low and p11.y > low) {
            b.style = .{ .color = grounded(faceMix(c00, c01, c11), x + cell * 0.3, z + cell * 0.7, 0) };
            b.flat(p00, p01, p11, .{ .y = 1 });
        }

        if (p00.y > low and p11.y > low and p10.y > low) {
            b.style = .{ .color = grounded(faceMix(c00, c11, c10), x + cell * 0.7, z + cell * 0.3, 1) };
            b.flat(p00, p11, p10, .{ .y = 1 });
        }

        return;
    }

    b.style = .{ .color = groundColor(x + cell * 0.3, z + cell * 0.7) };
    b.flat(p00, p01, p11, .{ .y = 1 });
    b.style = .{ .color = groundColor(x + cell * 0.7, z + cell * 0.3) };
    b.flat(p00, p11, p10, .{ .y = 1 });
}

fn skirt(b: *Builder, a: Vec3, c: Vec3, out: Vec3) void {
    if (shared.terrain.current == .islands and @min(a.y, c.y) < shared.terrain.void_floor + 1) return;

    b.style = .{ .color = groundColor((a.x + c.x) / 2, (a.z + c.z) / 2) };
    b.quad(a, c, c.sub(.{ .y = 6 }), a.sub(.{ .y = 6 }), out);
}

fn buildChunks() void {
    const t = shared.terrain;
    const per: f32 = t.facet * 28;
    const n: usize = @intFromFloat(@ceil(t.half * 2 / per));
    const gpa = std.heap.page_allocator;
    const list = gpa.alloc(Chunk, n * n) catch return;

    water_level = t.rawHeight(t.oasis[0] + 12, t.oasis[1]) - 0.6;

    for (0..n) |ci| {
        for (0..n) |cj| {
            const x0 = -t.half + @as(f32, @floatFromInt(ci)) * per;
            const z0 = -t.half + @as(f32, @floatFromInt(cj)) * per;
            const x1 = @min(x0 + per, t.half);
            const z1 = @min(z0 + per, t.half);
            var b: Builder = .{};
            var x = x0;

            while (x < x1 - 0.01) : (x += t.facet) {
                var z = z0;

                while (z < z1 - 0.01) : (z += t.facet) {
                    if (!underHangar(x, z, t.facet)) terrainCell(&b, x, z, t.facet);
                }
            }

            const hi = b.finish();
            var lb: Builder = .{};
            const coarse = t.facet * 4;

            x = x0;

            while (x < x1 - 0.01) : (x += coarse) {
                var z = z0;

                while (z < z1 - 0.01) : (z += coarse) {
                    if (!underHangar(x, z, coarse)) terrainCell(&lb, x, z, @min(coarse, @min(x1 - x, z1 - z)));
                }
            }

            x = x0;

            while (x < x1 - 0.01) : (x += coarse) {
                const xe = @min(x + coarse, x1);

                skirt(&lb, vec(x, t.height(x, z0), z0), vec(xe, t.height(xe, z0), z0), .{ .z = -1 });
                skirt(&lb, vec(x, t.height(x, z1), z1), vec(xe, t.height(xe, z1), z1), .{ .z = 1 });
            }

            var z = z0;

            while (z < z1 - 0.01) : (z += coarse) {
                const ze = @min(z + coarse, z1);

                skirt(&lb, vec(x0, t.height(x0, z), z), vec(x0, t.height(x0, ze), ze), .{ .x = -1 });
                skirt(&lb, vec(x1, t.height(x1, z), z), vec(x1, t.height(x1, ze), ze), .{ .x = 1 });
            }

            var ch: Chunk = .{ .hi = hi, .lo = lb.finish(), .cx = (x0 + x1) / 2, .cz = (z0 + z1) / 2, .r = per * 0.72 };
            var sb: Builder = .{};

            for (shared.world.structures, 0..) |st, i| {
                const cx = (st.min.x + st.max.x) / 2;
                const cz = (st.min.z + st.max.z) / 2;

                if (cx < x0 or cx >= x1 or cz < z0 or cz >= z1) continue;

                if (indoor(cx, cz)) continue;

                if (sb.full() and ch.things_n < ch.things.len - 1) {
                    ch.things[ch.things_n] = sb.finish();
                    ch.things_n += 1;
                }

                const gc = groundColor(cx, cz);
                const gk: f32 = if (st.tone == .blob) 0.72 else 0.86;
                const base = if (st.tone == .blob or st.tone == .blob_soft) [3]f32{ @as(f32, @floatFromInt(gc[0])) * gk, @as(f32, @floatFromInt(gc[1])) * gk, @as(f32, @floatFromInt(gc[2])) * gk } else toneBase(st.tone);
                const h = (i *% 2654435761) % 1000;
                const vary = 0.98 + @as(f32, @floatFromInt(h)) / 1000.0 * 0.04;
                const size = st.max.sub(st.min);
                const glow: u8 = if (st.tone == .cap_ring or st.tone == .marking) 30 else 0;
                const big = @min(size.x, @min(size.y, size.z));

                if (shared.terrain.current == .desert) {
                    desertPiece(&sb, st, base);

                    continue;
                }

                sb.style = .{ .color = shade(base, vary), .glow = glow };
                sb.grime = if (size.y > 0.5) .{ .floor = st.min.y } else null;

                if (big > 0.12) sb.bevelBox(st.min, st.max, @min(0.08, big * 0.2)) else sb.box(st.min.add(st.max).scale(0.5), Basis.world, size.scale(0.5));

                sb.grime = null;
            }

            if (sb.count > 0 and ch.things_n < ch.things.len) {
                ch.things[ch.things_n] = sb.finish();
                ch.things_n += 1;
            }

            list[ci * n + cj] = ch;
        }
    }

    chunks = list;
}

fn ribbon(b: *Builder, sg: [4]f32, off: f32, w: f32, lift: f32, color: palette.Rgb) void {
    const t = shared.terrain;
    const dx = sg[2] - sg[0];
    const dz = sg[3] - sg[1];
    const len = @sqrt(dx * dx + dz * dz);
    const ux = dx / len;
    const uz = dz / len;
    const px = -uz;
    const pz = ux;
    const steps: u32 = @intFromFloat(@ceil(len / 3));
    var i: u32 = 0;

    b.style = .{ .color = color };

    while (i < steps) : (i += 1) {
        const a = @as(f32, @floatFromInt(i)) / @as(f32, @floatFromInt(steps)) * len;
        const c = @as(f32, @floatFromInt(i + 1)) / @as(f32, @floatFromInt(steps)) * len;
        var q: [4]Vec3 = undefined;

        for ([_]f32{ a, c }, 0..) |d, k| {
            for ([_]f32{ -1, 1 }, 0..) |sd, m| {
                const x = sg[0] + ux * d + px * (off + sd * w);
                const z = sg[1] + uz * d + pz * (off + sd * w);

                q[k * 2 + m] = vec(x, t.height(x, z) + lift, z);
            }
        }

        b.flat(q[0], q[2], q[3], .{ .y = 1 });
        b.flat(q[0], q[3], q[1], .{ .y = 1 });
    }
}

fn capRing(b: *Builder, cx: f32, cz: f32, r: f32) void {
    const t = shared.terrain;
    const n: u32 = 64;
    var i: u32 = 0;

    b.style = .{ .color = .{ 226, 220, 200 }, .glow = 30 };

    while (i < n) : (i += 1) {
        if (i % 4 == 3) continue;

        const a0 = @as(f32, @floatFromInt(i)) / @as(f32, @floatFromInt(n)) * std.math.tau;
        const a1 = @as(f32, @floatFromInt(i + 1)) / @as(f32, @floatFromInt(n)) * std.math.tau;
        var q: [4]Vec3 = undefined;

        for ([_]f32{ a0, a1 }, 0..) |a, k| {
            for ([_]f32{ r - 0.35, r + 0.35 }, 0..) |rr, m| {
                const x = cx + @cos(a) * rr;
                const z = cz + @sin(a) * rr;

                q[k * 2 + m] = vec(x, t.height(x, z) + 0.1, z);
            }
        }

        b.flat(q[0], q[2], q[3], .{ .y = 1 });
        b.flat(q[0], q[3], q[1], .{ .y = 1 });
    }
}

fn roadRibbon(b: *Builder, sg: [4]f32) void {
    ribbon(b, sg, 0, 5.6, 0.12, .{ 158, 138, 108 });
    ribbon(b, sg, -2.4, 0.55, 0.15, .{ 128, 110, 86 });
    ribbon(b, sg, 2.4, 0.55, 0.15, .{ 128, 110, 86 });
}

fn indoor(x: f32, z: f32) bool {
    return shared.terrain.current == .facility and @abs(x) < 57 and @abs(z) < 45;
}

fn underHangar(x: f32, z: f32, cell: f32) bool {
    return indoor(x, z) and indoor(x + cell, z + cell);
}

fn prismColor(x: f32, z: f32) palette.Rgb {
    const r = @sqrt(x * x + z * z);
    const centre = 1 - std.math.clamp(r / 120, 0, 1);
    const cell = @mod(@floor(x / 7) + @floor(z / 7), 2);
    const k = 0.58 + centre * centre * 0.5 + cell * 0.02;

    return .{
        @intFromFloat(std.math.clamp(112 * k, 0, 255)),
        @intFromFloat(std.math.clamp(176 * k, 0, 255)),
        @intFromFloat(std.math.clamp(182 * k, 0, 255)),
    };
}

fn facilityColor(x: f32, z: f32) palette.Rgb {
    const t = shared.terrain;
    const n = t.normal(x, z);
    const slope = 1 - n.y;
    const h = t.height(x, z);
    const vary = 0.95 + t.fbm(x * 0.09, z * 0.09) * 0.1;
    const light = vary + n.x * 0.05 - n.z * 0.03;
    const patch = t.fbm(x * 0.025 + 9, z * 0.025 - 31);
    const yard = @abs(x) < t.compound[0] + 4 and @abs(z) < t.compound[1] + 4;

    if (slope > 0.4 or h > 26) {
        const top = std.math.clamp((h - 20) / 40, 0, 1);

        return shade(.{ 150 + top * 36, 128 + top * 32, 104 + top * 28 }, light);
    }

    if (slope > 0.22 or h > 10) return shade(.{ 158, 142, 110 }, light);

    if (yard) {
        if (patch > 0.62) return shade(.{ 122, 118, 104 }, vary);

        return shade(.{ 132, 127, 112 }, vary);
    }

    if (patch > 0.6) return shade(.{ 156, 142, 108 }, light);

    if (patch < 0.32) return shade(.{ 150, 142, 104 }, light);

    return shade(.{ 166, 150, 116 }, light);
}

var water_level: f32 = 0;

fn mix3(a: [3]f32, c: [3]f32, k: f32) [3]f32 {
    const q = std.math.clamp(k, 0, 1);

    return .{ a[0] + (c[0] - a[0]) * q, a[1] + (c[1] - a[1]) * q, a[2] + (c[2] - a[2]) * q };
}

fn valleyColor(x: f32, z: f32) palette.Rgb {
    const t = shared.terrain;
    const n = t.normal(x, z);
    const h = t.height(x, z);
    const rel = h - t.valleyFloor(x, z);
    const vary = 0.95 + t.fbm(x * 0.09, z * 0.09) * 0.1;
    const light = vary + n.x * 0.05 - n.z * 0.02;
    const d = t.roadDistance(x, z);
    const rd = @abs(x - t.riverLine(z));
    const wet = t.riverSpan(z) > 0.3;

    if (d < t.road_half - 2) return shade(.{ 136, 118, 92 }, light);

    if (d < t.road_half) return shade(.{ 140, 132, 92 }, light);

    if (t.baseMask(x, z) > 0.5) return shade(if (t.fbm(x * 0.05, z * 0.05) > 0.55) .{ 154, 148, 104 } else .{ 122, 132, 84 }, light);

    if (h > 66 + t.fbm(x * 0.04, z * 0.04) * 14 and n.y > 0.5) return shade(.{ 220, 221, 218 }, 0.98 + vary * 0.04);

    if (rel > 2.2) {
        const k = rel / 70;
        const band = @mod(@floor(rel / 6), 2);
        const rock = if (k < 0.5) mix3(.{ 150, 116, 88 }, .{ 128, 124, 116 }, k * 2) else mix3(.{ 128, 124, 116 }, .{ 112, 120, 132 }, k * 2 - 1);
        const banded = if (band > 0.5) mix3(rock, .{ 176, 160, 132 }, 0.22) else rock;

        if ((n.y > 0.86 and rel < 52) or (n.y > 0.7 and rel < 14)) return shade(if (t.fbm(x * 0.05 + 3, z * 0.05) > 0.62) .{ 154, 148, 104 } else mix3(.{ 96, 118, 72 }, .{ 118, 132, 82 }, rel / 30), light);

        return shade(if (n.y < 0.55) mix3(banded, .{ 79, 81, 84 }, 0.45) else banded, light);
    }

    if (wet and rd < 8) return shade(.{ 169, 156, 126 }, light);

    const fields = [_][3]f32{ .{ 107, 127, 79 }, .{ 92, 116, 70 }, .{ 128, 140, 86 }, .{ 154, 148, 104 }, .{ 116, 132, 80 } };
    const along = z - t.roadLine(z) * 0.2;
    const fx: i32 = @intFromFloat(@floor((x - t.roadLine(z)) / 16));
    const fz: i32 = @intFromFloat(@floor(along / 22));
    const pick: usize = @intCast(@mod(fx * 7 + fz * 13 + @divFloor(fz * fx, 3), 5));

    const verge = mix3(.{ 128, 134, 86 }, fields[pick], t.smooth(t.road_half + 1.0, t.road_half + 4.0, d));

    return shade(mix3(.{ 158, 138, 108 }, verge, t.smooth(t.road_half - 1.5, t.road_half + 1.0, d)), light);
}

fn ivWorld(b: *Builder) void {
    const t = shared.terrain;

    if (t.current == .islands) return;

    var z: f32 = -190;
    var k: u32 = 0;

    while (z < 238) : ({
        z += 4;
        k += 1;
    }) {
        const s0 = t.riverSpan(z);
        const s1 = t.riverSpan(z + 4);

        if (s0 < 0.05 and s1 < 0.05) continue;

        const x0 = t.riverLine(z);
        const x1 = t.riverLine(z + 4);
        const y0 = t.valleyFloor(x0, z) - 1.0;
        const y1 = t.valleyFloor(x1, z + 4) - 1.0;
        const w0 = 5.0 * s0;
        const w1 = 5.0 * s1;
        const cuts = [_]f32{ -1, -0.55, 0.55, 1 };

        for (0..3) |j| {
            const a0 = cuts[j];
            const a1 = cuts[j + 1];
            const edge = j != 1;

            b.style = .{ .color = if (edge) .{ 94, 154, 148 } else .{ 47, 94, 104 }, .glow = if (edge) 30 else 20 };
            b.flat(vec(x0 + w0 * a0, y0, z), vec(x1 + w1 * a0, y1, z + 4), vec(x1 + w1 * a1, y1, z + 4), .{ .y = 1 });
            b.flat(vec(x0 + w0 * a0, y0, z), vec(x1 + w1 * a1, y1, z + 4), vec(x0 + w0 * a1, y0, z), .{ .y = 1 });
        }

        if (k % 3 == 0) {
            const off = @sin(z * 0.7) * w0 * 0.3;

            b.style = .{ .color = .{ 176, 206, 200 }, .glow = 50 };
            b.flat(vec(x0 + off - 0.5, y0 + 0.02, z + 0.6), vec(x0 + off - 0.2, y0 + 0.02, z + 2.6), vec(x0 + off + 0.5, y0 + 0.02, z + 2.4), .{ .y = 1 });
        }
    }

    flush(b);
}

pub fn groundColor(x: f32, z: f32) palette.Rgb {
    const t = shared.terrain;

    if (shared.maps.current()) |d| return d.ground(x, z);

    switch (t.current) {
        .town => {},
        .valley => return valleyColor(x, z),
        .facility => return facilityColor(x, z),
        .conquest => return conquestColor(x, z),
        .prism => return prismColor(x, z),
        .courtyard => return .{ 228, 228, 224 },
        else => {},
    }

    const n = t.normal(x, z);
    const slope = 1 - n.y;
    const box = @max(@abs(x), @abs(z));
    const paved = box < t.town - 1;
    const vary = t.fbm(x * 0.09, z * 0.09);
    const dirt = t.fbm(x * 0.035 + 31, z * 0.035 - 17);

    if (paved) {
        const g: u8 = @intFromFloat(150 + vary * 30);

        return .{ g, g, @intFromFloat(@as(f32, @floatFromInt(g)) * 0.97) };
    }

    if (slope > 0.42 or t.height(x, z) > 24) return .{ @intFromFloat(92 + vary * 24), @intFromFloat(90 + vary * 22), @intFromFloat(84 + vary * 20) };

    if (slope > 0.25 or t.height(x, z) > 12) return .{ @intFromFloat(88 + vary * 30), @intFromFloat(110 + vary * 30), @intFromFloat(62 + vary * 20) };

    if (dirt > 0.62) return .{ @intFromFloat(140 + vary * 25), @intFromFloat(108 + vary * 20), @intFromFloat(72 + vary * 15) };

    return .{ @intFromFloat(84 + vary * 46), @intFromFloat(136 + vary * 42), @intFromFloat(52 + vary * 24) };
}

fn buildWorld() rl.Mesh {
    const t = shared.terrain;
    var b: Builder = .{};

    if (t.current == .courtyard) {
        b.style = .{ .color = .{ 226, 204, 168 } };
        b.flat(vec(0, -40, 0), vec(0, -40, 1), vec(1, -40, 1), .{ .y = 1 });

        return b.finish();
    }

    if (t.current == .valley or t.current == .islands) {
        ivWorld(&b);

        return b.finish();
    }

    if (t.current == .conquest or t.current == .desert) {
        b.style = .{ .color = .{ 52, 150, 168 }, .glow = 40 };
        b.cylinder(vec(t.oasis[0], water_level - 0.4, t.oasis[1]), vec(t.oasis[0], water_level, t.oasis[1]), 12.5, 24, true);

        if (t.current == .conquest) {
            for (t.conquestSegments()) |sg| roadRibbon(&b, sg);

            for (shared.world.capture_points) |cp| capRing(&b, cp.pos.x, cp.pos.z, cp.radius);
        }

        return b.finish();
    }

    if (shared.maps.current() != null) {
        structures(&b);

        return b.finish();
    }

    const faceted = t.current != .town;
    const cell: f32 = if (faceted) t.facet else 2;

    water_level = t.rawHeight(t.oasis[0] + 12, t.oasis[1]) - 0.6;
    var x: f32 = -t.half;

    if (t.current == .facility) x = t.half;

    while (x < t.half) : (x += cell) {
        var z: f32 = -t.half;

        while (z < t.half) : (z += cell) {
            const p00 = vec(x, t.height(x, z), z);
            const p10 = vec(x + cell, t.height(x + cell, z), z);
            const p01 = vec(x, t.height(x, z + cell), z + cell);
            const p11 = vec(x + cell, t.height(x + cell, z + cell), z + cell);
            const n00 = t.normal(x, z);
            const n10 = t.normal(x + cell, z);
            const n01 = t.normal(x, z + cell);
            const n11 = t.normal(x + cell, z + cell);

            if (t.current == .islands) {
                const low = t.void_floor + 1;

                if (p00.y > low and p01.y > low and p11.y > low) {
                    b.style = .{ .color = groundColor(x + cell * 0.3, z + cell * 0.7) };
                    b.flat(p00, p01, p11, .{ .y = 1 });
                }

                if (p00.y > low and p11.y > low and p10.y > low) {
                    b.style = .{ .color = groundColor(x + cell * 0.7, z + cell * 0.3) };
                    b.flat(p00, p11, p10, .{ .y = 1 });
                }

                continue;
            }

            if (faceted) {
                b.style = .{ .color = groundColor(x + cell * 0.3, z + cell * 0.7) };
                b.flat(p00, p01, p11, .{ .y = 1 });
                b.style = .{ .color = groundColor(x + cell * 0.7, z + cell * 0.3) };
                b.flat(p00, p11, p10, .{ .y = 1 });

                continue;
            }

            b.style = .{ .color = groundColor(x + cell * 0.5, z + cell * 0.5) };
            b.tri(p00, p01, p11, n00, n01, n11, .{ .y = 1 });
            b.tri(p00, p11, p10, n00, n11, n10, .{ .y = 1 });
        }
    }

    structures(&b);

    if (t.current == .desert) {
        b.style = .{ .color = .{ 52, 150, 168 }, .glow = 40 };
        b.cylinder(vec(t.oasis[0], water_level - 0.4, t.oasis[1]), vec(t.oasis[0], water_level, t.oasis[1]), 12.5, 24, true);
    }

    return b.finish();
}

fn toneBase(tone: shared.world.Tone) [3]f32 {
    return switch (tone) {
        .mud => .{ 172, 136, 98 },
        .house => .{ 184, 150, 108 },
        .roof => .{ 118, 94, 70 },
        .ruin => .{ 214, 156, 100 },
        .adobe => .{ 226, 196, 142 },
        .floor => .{ 178, 146, 100 },
        .stair => .{ 206, 176, 118 },
        .beam => .{ 112, 74, 44 },
        .wood => .{ 122, 80, 46 },
        .cloth_red => .{ 196, 98, 62 },
        .cloth_blue => .{ 70, 128, 132 },
        .cloth_yellow => .{ 214, 164, 72 },
        .f_floor => .{ 142, 140, 134 },
        .f_floor_dark => .{ 124, 122, 116 },
        .f_line => .{ 196, 176, 110 },
        .f_mint => .{ 172, 172, 164 },
        .f_mint_dark => .{ 146, 152, 140 },
        .f_grey => .{ 172, 170, 164 },
        .f_grey_dark => .{ 140, 140, 136 },
        .f_hazard => .{ 184, 152, 72 },
        .f_black => .{ 98, 100, 100 },
        .f_rail => .{ 184, 152, 72 },
        .f_light => .{ 236, 226, 196 },
        .f_screen => .{ 58, 80, 86 },
        .f_metal => .{ 142, 144, 140 },
        .f_ceiling => .{ 156, 154, 146 },
        .f_crate => .{ 150, 124, 84 },
        .f_crate_teal => .{ 88, 112, 112 },
        .f_container_red => .{ 150, 86, 58 },
        .f_container_blue => .{ 74, 112, 116 },
        .f_vault => .{ 120, 128, 132 },
        .f_red_light => .{ 200, 70, 54 },
        .f_pipe => .{ 120, 124, 122 },
        .f_pipe_red => .{ 150, 70, 52 },
        .f_barrel => .{ 90, 110, 116 },
        .f_barrel_red => .{ 140, 70, 50 },
        .f_rubber => .{ 44, 44, 46 },
        .f_sign => .{ 214, 208, 192 },
        .f_stain => .{ 70, 72, 70 },
        .f_wood_pallet => .{ 150, 112, 70 },
        .f_panel => .{ 110, 128, 118 },
        .olive => .{ 112, 118, 74 },
        .sandbag => .{ 186, 164, 116 },
        .concrete => .{ 168, 164, 154 },
        .tarmac => .{ 70, 72, 74 },
        .marking => .{ 236, 232, 214 },
        .cap_ring => .{ 250, 250, 245 },
        .flag_cloth => .{ 236, 236, 230 },
        .pole => .{ 92, 96, 100 },
        .rust => .{ 150, 84, 46 },
        .char => .{ 44, 40, 38 },
        .tent => .{ 150, 140, 98 },
        .sign => .{ 46, 120, 70 },
        .trim => .{ 238, 220, 180 },
        .plinth => .{ 168, 132, 92 },
        .shutter => .{ 92, 138, 136 },
        .frame => .{ 120, 82, 50 },
        .tank => .{ 150, 156, 150 },
        .rug => .{ 168, 82, 60 },
        .leaf => .{ 112, 146, 70 },
        .pot => .{ 186, 108, 70 },
        .scuff => .{ 112, 108, 96 },
        .scuff_soft => .{ 122, 118, 104 },
        .paint_line => .{ 196, 176, 110 },
        .blob => .{ 0, 0, 0 },
        .blob_soft => .{ 0, 0, 0 },
    };
}

fn structures(b: *Builder) void {
    for (shared.world.structures, 0..) |st, i| {
        const base = if (st.tone == .blob or st.tone == .blob_soft) toneBase(.f_floor_dark) else toneBase(st.tone);
        const k: f32 = switch (st.tone) {
            .mud, .house, .roof, .ruin => 0.94 + @as(f32, @floatFromInt(i % 5)) * 0.03,
            else => 1,
        };

        const glow: u8 = switch (st.tone) {
            .f_light => 140,
            .f_ceiling => 40,
            .f_screen => 80,
            .f_red_light => 110,
            else => 0,
        };

        if (shared.terrain.current == .facility) {
            const c = st.min.add(st.max).scale(0.5);

            if (!indoor(c.x, c.z)) continue;

            facilityPiece(b, st, base, glow, i);

            continue;
        }

        if (shared.terrain.current == .desert) {
            flush(b);
            desertPiece(b, st, base);

            continue;
        }

        b.style = .{ .color = shade(base, k), .glow = glow };
        b.box(st.min.add(st.max).scale(0.5), Basis.world, st.max.sub(st.min).scale(0.5));
    }
}

var extra: [24]rl.Mesh = undefined;
var extra_n: usize = 0;

pub fn extraMeshes() []const rl.Mesh {
    return extra[0..extra_n];
}

fn flush(b: *Builder) void {
    if (!b.full() or extra_n >= extra.len) return;

    extra[extra_n] = b.finish();
    extra_n += 1;
}

const plasters = [_][3]f32{
    .{ 226, 196, 142 },
    .{ 232, 208, 162 },
    .{ 214, 178, 128 },
    .{ 222, 186, 150 },
    .{ 206, 184, 140 },
};

const shutters = [_][3]f32{
    .{ 92, 138, 136 },
    .{ 112, 124, 92 },
    .{ 150, 104, 72 },
    .{ 96, 118, 140 },
    .{ 132, 120, 90 },
};

fn desertPiece(b: *Builder, st: shared.world.Structure, base: [3]f32) void {
    const size = st.max.sub(st.min);
    const t = @min(st.tint, plasters.len - 1);
    const col: [3]f32 = switch (st.tone) {
        .adobe => plasters[t],
        .trim => .{ @min(255, plasters[t][0] * 1.06), @min(255, plasters[t][1] * 1.06), @min(255, plasters[t][2] * 1.07) },
        .plinth => .{ plasters[t][0] * 0.76, plasters[t][1] * 0.72, plasters[t][2] * 0.68 },
        .shutter => shutters[t],
        else => base,
    };
    const m = @min(size.x, @min(size.y, size.z));
    const flat_face = st.tone == .adobe or st.tone == .floor or st.tone == .plinth;
    const bevel: f32 = if (flat_face) 0 else if (m > 0.2) 0.03 else 0.0;
    const ground = shared.terrain.height((st.min.x + st.max.x) / 2, (st.min.z + st.max.z) / 2);

    b.style = .{ .color = .{ @intFromFloat(col[0]), @intFromFloat(col[1]), @intFromFloat(col[2]) } };
    b.grime = if (flat_face or size.y > 0.6) .{ .floor = ground, .dark = 0.16, .span = 9 } else null;
    defer b.grime = null;

    if (bevel > 0) b.bevelBox(st.min, st.max, bevel) else b.box(st.min.add(st.max).scale(0.5), Basis.world, size.scale(0.5));
}

fn facilityPiece(b: *Builder, st: shared.world.Structure, base: [3]f32, glow: u8, i: usize) void {
    flush(b);

    const h = (i *% 2654435761) % 1000;
    const vary = 0.95 + @as(f32, @floatFromInt(h)) / 1000.0 * 0.1;
    const size = st.max.sub(st.min);
    const lo = st.min;
    const hi = st.max;

    b.style = .{ .color = shade(base, vary), .glow = glow };
    b.grime = if (glow > 0) null else .{ .ceiling = 16 };
    defer b.grime = null;

    switch (st.tone) {
        .f_pipe, .f_pipe_red => {
            const c = lo.add(hi).scale(0.5);
            const r = @min(size.x, @min(size.y, size.z)) * 0.5;
            var a = c;
            var z = c;

            if (size.x >= size.y and size.x >= size.z) {
                a.x = lo.x;
                z.x = hi.x;
            } else if (size.y >= size.z) {
                a.y = lo.y;
                z.y = hi.y;
            } else {
                a.z = lo.z;
                z.z = hi.z;
            }

            b.cylinder(a, z, r, 12, true);
        },
        .f_barrel, .f_barrel_red => {
            const c = lo.add(hi).scale(0.5);
            const r = @min(size.x, size.z) * 0.5;

            b.cylinder(vec(c.x, lo.y, c.z), vec(c.x, hi.y, c.z), r, 16, true);
            b.style = .{ .color = shade(base, 0.7) };
            b.cylinder(vec(c.x, lo.y + size.y * 0.3, c.z), vec(c.x, lo.y + size.y * 0.34, c.z), r * 1.03, 16, false);
            b.cylinder(vec(c.x, lo.y + size.y * 0.66, c.z), vec(c.x, lo.y + size.y * 0.7, c.z), r * 1.03, 16, false);
        },
        .f_stain, .f_line, .f_sign => b.box(lo.add(hi).scale(0.5), Basis.world, size.scale(0.5)),
        else => {
            const m = @min(size.x, @min(size.y, size.z));
            const bevel: f32 = if (m > 2) 0.07 else if (m > 0.5) 0.04 else 0.012;

            b.bevelBox(lo, hi, bevel);
        },
    }
}

fn floorTiles(b: *Builder, min: Vec3, max: Vec3) void {
    const tile: f32 = 4;
    var z = min.z;
    var row: u32 = 0;

    while (z < max.z) : ({
        z += tile;
        row += 1;
    }) {
        var x = min.x;
        var col: u32 = 0;

        while (x < max.x) : ({
            x += tile;
            col += 1;
        }) {
            b.paint(if ((row + col) % 2 == 0) .floor else .floor_alt);
            b.quad(vec(x, max.y, z), vec(x, max.y, z + tile), vec(x + tile, max.y, z + tile), vec(x + tile, max.y, z), .{ .y = 1 });
        }
    }
}

fn buildBackdrop() rl.Mesh {
    var b: Builder = .{};
    const hill_paints = [_]Paint{ .green, .mint, .teal, .lavender, .grass };
    var i: u32 = 0;

    const def = shared.maps.current();

    b.style = .{ .color = if (def) |d| d.backdrop else switch (shared.terrain.current) {
        .town => .{ 120, 196, 110 },
        .valley => .{ 150, 128, 100 },
        .facility => .{ 150, 148, 120 },
        .conquest => .{ 214, 168, 112 },
        .prism => .{ 120, 190, 196 },
        .courtyard => .{ 226, 204, 168 },
        else => .{ 150, 140, 120 },
    } };

    const floor_y: f32 = if (def) |d| d.floor_y else switch (shared.terrain.current) {
        .valley => -8,
        else => -0.2,
    };

    b.cylinder(vec(0, floor_y, 0), vec(0, floor_y + 0.15, 0), @max(260, shared.terrain.half * 2.4), 48, true);

    while (i < 0) : (i += 1) {
        const fi: f32 = @floatFromInt(i);
        const ang = fi * 0.1428 + @sin(fi * 2.3) * 0.05;
        const dist = 85 + @mod(fi * 37, 70);
        const height = 14 + @mod(fi * 23, 26);
        const radius = 18 + @mod(fi * 13, 22);
        const base = vec(@sin(ang) * dist, -0.1, @cos(ang) * dist);

        b.paint(hill_paints[i % hill_paints.len]);
        b.cone(base, base.add(.{ .y = height }), radius, 9);
    }

    return b.finish();
}

fn buildClouds() rl.Mesh {
    var b: Builder = .{};
    var i: u32 = 0;

    b.glowing(.white, 120);

    while (i < 14) : (i += 1) {
        const fi: f32 = @floatFromInt(i);
        const ang = fi * 0.449 + 0.3;
        const dist = 60 + @mod(fi * 31, 70);
        const center = vec(@sin(ang) * dist, 34 + @mod(fi * 7, 14), @cos(ang) * dist);
        var k: u32 = 0;

        while (k < 4) : (k += 1) {
            const fk: f32 = @floatFromInt(k);
            const off = vec((fk - 1.5) * 4.5, @sin(fk * 2.1) * 1.2, @cos(fk * 1.7) * 2);

            b.sphere(center.add(off), 4 + @mod(fk * 1.7 + fi, 2.5), 8, 12);
        }
    }

    return b.finish();
}

const body_paint: Paint = .dark;
const metal: Paint = .steel;

fn classPaint(c: weapons.Class) Paint {
    return switch (c) {
        .pistol => .orange,
        .smg => .teal,
        .rifle => .coral,
        .dmr => .mint,
        .sniper => .blue,
        .shotgun => .red,
        .lmg => .yellow,
        .launcher => .orange,
        .special => .purple,
        .bow, .crossbow => .wood,
        .melee => .red,
    };
}

fn part(b: *Builder, p: Paint, x: f32, y: f32, z: f32, hx: f32, hy: f32, hz: f32) void {
    b.paint(p);
    b.box(vec(x, y, z), Basis.world, vec(hx, hy, hz));
}

fn tube(b: *Builder, p: Paint, z0: f32, z1: f32, y: f32, radius: f32) void {
    b.paint(p);
    b.cylinder(vec(0, y, z0), vec(0, y, z1), radius, 12, true);
}

fn rod(b: *Builder, p: Paint, a: Vec3, c: Vec3, radius: f32) void {
    b.paint(p);
    b.cylinder(a, c, radius, 10, true);
}

fn shape(b: *Builder, p: Paint, half: f32, pts: []const [2]f32) void {
    b.paint(p);
    b.slab(0, pts, half, @min(half * 0.45, 0.006));
}

fn grip(b: *Builder, p: Paint, z: f32, y: f32) void {
    shape(b, p, 0.016, &.{ .{ z - 0.02, y }, .{ z + 0.022, y }, .{ z + 0.046, y - 0.1 }, .{ z + 0.034, y - 0.112 }, .{ z + 0.004, y - 0.106 } });
}

fn trigger(b: *Builder, z: f32, y: f32) void {
    shape(b, .dark, 0.006, &.{ .{ z - 0.07, y - 0.032 }, .{ z - 0.016, y - 0.032 }, .{ z - 0.016, y - 0.04 }, .{ z - 0.07, y - 0.04 } });
    shape(b, .dark, 0.006, &.{ .{ z - 0.074, y }, .{ z - 0.066, y }, .{ z - 0.066, y - 0.04 }, .{ z - 0.074, y - 0.036 } });
    shape(b, .steel, 0.004, &.{ .{ z - 0.046, y }, .{ z - 0.038, y }, .{ z - 0.034, y - 0.026 }, .{ z - 0.042, y - 0.024 } });
}

fn optic(b: *Builder, o: weapons.Optic, h: f32, body: f32) void {
    const top = h + 0.004;

    switch (o) {
        .iron => {
            part(b, body_paint, 0, top + 0.01, -body * 0.9, 0.004, 0.01, 0.004);
            part(b, body_paint, 0, top + 0.008, body * 0.6, 0.012, 0.008, 0.004);
        },
        .dot => {
            part(b, body_paint, 0, top + 0.016, -body * 0.15, 0.013, 0.016, 0.024);
            b.glowing(.red, 255);
            b.box(vec(0, top + 0.02, -body * 0.15 - 0.025), Basis.world, vec(0.008, 0.008, 0.002));
        },
        .holo => {
            part(b, body_paint, 0, top + 0.008, -body * 0.15, 0.016, 0.008, 0.03);
            part(b, body_paint, 0.014, top + 0.03, -body * 0.15 - 0.022, 0.003, 0.018, 0.004);
            part(b, body_paint, -0.014, top + 0.03, -body * 0.15 - 0.022, 0.003, 0.018, 0.004);
            part(b, body_paint, 0, top + 0.046, -body * 0.15 - 0.022, 0.016, 0.003, 0.004);
        },
        .scope2, .scope4, .scope8 => {
            const len: f32 = switch (o) {
                .scope2 => 0.07,
                .scope4 => 0.1,
                else => 0.14,
            };
            const r: f32 = switch (o) {
                .scope2 => 0.017,
                .scope4 => 0.02,
                else => 0.023,
            };
            const y = top + r + 0.012;

            part(b, body_paint, 0, top + 0.006, -body * 0.1, 0.008, 0.008, len * 0.6);
            tube(b, body_paint, -body * 0.1 + len, -body * 0.1 - len, y, r);
            tube(b, metal, -body * 0.1 - len, -body * 0.1 - len - 0.03, y, r * 1.35);
            tube(b, metal, -body * 0.1 + len, -body * 0.1 + len + 0.02, y, r * 1.15);
            b.glowing(.blue, 180);
            b.cylinder(vec(0, y, -body * 0.1 - len - 0.03), vec(0, y, -body * 0.1 - len - 0.032), r * 1.2, 12, true);
        },
    }
}

fn magazine(b: *Builder, m: weapons.Mag, h: f32, body: f32, accent: Paint) void {
    const z = -body * 0.3;
    const y = -h;

    switch (m) {
        .none => {},
        .box => shape(b, body_paint, 0.013, &.{ .{ z - 0.022, y }, .{ z + 0.02, y }, .{ z + 0.028, y - 0.09 }, .{ z + 0.022, y - 0.096 }, .{ z - 0.016, y - 0.096 }, .{ z - 0.022, y - 0.09 } }),
        .curved => shape(b, body_paint, 0.013, &.{ .{ z - 0.022, y }, .{ z + 0.02, y }, .{ z + 0.03, y - 0.05 }, .{ z + 0.02, y - 0.11 }, .{ z - 0.026, y - 0.1 }, .{ z - 0.032, y - 0.05 } }),
        .drum => {
            b.paint(accent);
            b.cylinder(vec(-0.026, y - 0.045, z), vec(0.026, y - 0.045, z), 0.048, 24, true);
            b.paint(body_paint);
            b.cylinder(vec(-0.03, y - 0.045, z), vec(0.03, y - 0.045, z), 0.018, 16, true);
        },
        .tube => tube(b, metal, -body, -body - 0.2, -h * 0.6, 0.012),
        .belt => {
            shape(b, body_paint, 0.024, &.{ .{ z - 0.04, y + 0.01 }, .{ z + 0.04, y + 0.01 }, .{ z + 0.044, y - 0.07 }, .{ z - 0.044, y - 0.07 } });
            part(b, .yellow, -0.03, y + 0.02, z - 0.01, 0.01, 0.012, 0.03);
        },
    }
}

fn firearm(b: *Builder, s: weapons.Spec) void {
    const l = s.look;
    const h = l.height;
    const body = l.body;
    const accent = classPaint(s.class);
    const gz = body * 0.45;
    const radius: f32 = switch (s.class) {
        .shotgun => 0.016,
        .lmg => 0.013,
        .sniper => 0.011,
        else => 0.01,
    };

    if (s.class == .pistol) {
        shape(b, body_paint, 0.018, &.{ .{ -body, -h }, .{ body, -h }, .{ body, h * 0.3 }, .{ -body, h * 0.3 } });
        shape(b, accent, 0.021, &.{ .{ -body, h * 0.3 }, .{ body, h * 0.3 }, .{ body, h + 0.016 }, .{ body * 0.82, h + 0.026 }, .{ -body * 0.9, h + 0.026 }, .{ -body, h + 0.012 } });
        grip(b, body_paint, body * 0.5, -h + 0.01);
        trigger(b, body * 0.5, -h);
    } else {
        shape(b, body_paint, 0.022, &.{ .{ -body, -h }, .{ body * 0.9, -h }, .{ body, -h * 0.3 }, .{ body, h * 0.7 }, .{ body * 0.85, h }, .{ -body * 0.8, h }, .{ -body, h * 0.55 } });
        shape(b, accent, 0.0232, &.{ .{ -body * 0.7, h * 0.1 }, .{ body * 0.7, h * 0.1 }, .{ body * 0.76, h * 0.45 }, .{ -body * 0.76, h * 0.45 } });
        shape(b, metal, 0.009, &.{ .{ -body * 0.75, h }, .{ body * 0.7, h }, .{ body * 0.66, h + 0.012 }, .{ -body * 0.71, h + 0.012 } });
        grip(b, body_paint, gz, -h + 0.01);
        trigger(b, gz, -h);
    }

    if (s.spinup > 0) {
        var i: u32 = 0;

        while (i < 6) : (i += 1) {
            const ang = @as(f32, @floatFromInt(i)) * 1.0472;
            const off = vec(@cos(ang) * 0.022, @sin(ang) * 0.022, 0);

            rod(b, metal, vec(off.x, off.y, -body), vec(off.x, off.y, -body - l.barrel), 0.008);
        }

        b.paint(accent);
        b.cylinder(vec(0, 0, -body - l.barrel * 0.4), vec(0, 0, -body - l.barrel * 0.5), 0.036, 20, true);
        b.cylinder(vec(0, 0, -body - l.barrel * 0.9), vec(0, 0, -body - l.barrel * 0.95), 0.034, 20, true);
    } else {
        b.paint(metal);
        b.cylinder(vec(0, h * 0.25, -body), vec(0, h * 0.25, -body - l.barrel), radius, 16, true);
        b.paint(body_paint);
        b.cylinder(vec(0, h * 0.25, -body - l.barrel + 0.03), vec(0, h * 0.25, -body - l.barrel), radius * 1.45, 16, true);
        b.cone(vec(0, h * 0.25, -body - l.barrel + 0.03), vec(0, h * 0.25, -body - l.barrel + 0.05), radius * 1.45, 16);
    }

    if (s.class == .shotgun and s.mag == 2) {
        b.paint(metal);
        b.cylinder(vec(0, -h * 0.4, -body), vec(0, -h * 0.4, -body - l.barrel), radius, 16, true);
    }

    if (s.class == .shotgun and s.mag != 2) {
        b.paint(accent);
        b.cylinder(vec(0, -h * 0.45, -body - l.barrel * 0.25), vec(0, -h * 0.45, -body - l.barrel * 0.6), 0.02, 12, true);
    }

    if (l.guard) {
        b.paint(accent);
        b.cylinder(vec(0, h * 0.1, -body + 0.005), vec(0, h * 0.1, -body - l.barrel * 0.6), h * 0.95, 8, true);
        b.paint(metal);
        b.cylinder(vec(0, h * 0.1 + h * 0.9, -body), vec(0, h * 0.1 + h * 0.9, -body - l.barrel * 0.55), 0.006, 8, true);
    }

    if (s.charge > 0 and s.fire == .hitscan) {
        var k: u32 = 0;

        while (k < 4) : (k += 1) {
            const z = -body - 0.04 - @as(f32, @floatFromInt(k)) * 0.07;

            b.glowing(.blue, 200);
            b.cylinder(vec(0, h * 0.25, z), vec(0, h * 0.25, z - 0.025), 0.027, 20, true);
        }
    }

    if (s.flame) {
        b.paint(.orange);
        b.cylinder(vec(0, -h - 0.05, 0.05), vec(0, -h - 0.05, -0.14), 0.04, 20, true);
        b.sphere(vec(0, -h - 0.05, 0.05), 0.04, 8, 16);
        b.sphere(vec(0, -h - 0.05, -0.14), 0.04, 8, 16);
        b.glowing(.red, 160);
        b.cylinder(vec(0, h * 0.25, -body - l.barrel), vec(0, h * 0.25, -body - l.barrel - 0.03), 0.022, 16, true);
    }

    if (l.stock > 0) {
        const st = l.stock;

        shape(b, accent, 0.017, &.{ .{ body - 0.005, h * 0.65 }, .{ body + st, h * 0.45 }, .{ body + st, -h * 1.6 }, .{ body + st * 0.7, -h * 1.7 }, .{ body - 0.005, -h * 0.5 } });
        shape(b, body_paint, 0.019, &.{ .{ body + st, h * 0.5 }, .{ body + st + 0.012, h * 0.5 }, .{ body + st + 0.012, -h * 1.65 }, .{ body + st, -h * 1.65 } });
    }

    magazine(b, l.mag, h, body, accent);
    optic(b, l.optic, h, body);
}

fn bow(b: *Builder, s: weapons.Spec) void {
    const reach: f32 = if (s.charge > 1) 0.44 else 0.36;
    const steps = 6;
    var prev = vec(0, -reach, 0.07);
    var i: u32 = 1;

    while (i <= steps * 2) : (i += 1) {
        const t = -1 + @as(f32, @floatFromInt(i)) / steps;
        const next = vec(0, t * reach, 0.07 * t * t - 0.02 * (1 - t * t));
        const p: Paint = if (@abs(t) < 0.2) .dark else if (@abs(t) > 0.85) .mint else .wood;

        rod(b, p, prev, next, 0.012);
        prev = next;
    }

    rod(b, .white, vec(0, reach, 0.07), vec(0, -reach, 0.07), 0.0025);
    part(b, .dark, 0, 0, -0.02, 0.014, 0.05, 0.016);
}

fn crossbow(b: *Builder, s: weapons.Spec) void {
    const l = s.look;

    shape(b, .wood, 0.02, &.{ .{ -l.body, -0.015 }, .{ l.body, -0.025 }, .{ l.body, 0.02 }, .{ -l.body * 0.9, 0.025 }, .{ -l.body, 0.015 } });
    part(b, .dark, 0, 0.026, -0.02, 0.006, 0.004, l.body * 0.9);
    trigger(b, l.body * 0.4, -0.02);
    rod(b, metal, vec(0, 0.01, -l.body), vec(0.22, 0.01, -l.body + 0.08), 0.012);
    rod(b, metal, vec(0, 0.01, -l.body), vec(-0.22, 0.01, -l.body + 0.08), 0.012);
    rod(b, .white, vec(0.22, 0.01, -l.body + 0.08), vec(-0.22, 0.01, -l.body + 0.08), 0.0025);
    grip(b, .dark, l.body * 0.4, -0.01);

    if (l.stock > 0) shape(b, .wood, 0.016, &.{ .{ l.body - 0.005, 0.02 }, .{ l.body + l.stock, 0.012 }, .{ l.body + l.stock, -0.06 }, .{ l.body + l.stock * 0.6, -0.065 }, .{ l.body - 0.005, -0.02 } });

    magazine(b, l.mag, 0.025, l.body, .wood);
    optic(b, l.optic, 0.025, l.body);
}

fn knife(b: *Builder) void {
    shape(b, .white, 0.004, &.{ .{ -0.015, 0.018 }, .{ -0.2, 0.018 }, .{ -0.27, 0.0 }, .{ -0.22, -0.016 }, .{ -0.015, -0.022 } });
    shape(b, .dark, 0.02, &.{ .{ -0.02, 0.032 }, .{ -0.008, 0.032 }, .{ -0.008, -0.034 }, .{ -0.02, -0.034 } });
    shape(b, .red, 0.013, &.{ .{ -0.008, 0.016 }, .{ 0.09, 0.012 }, .{ 0.1, 0.0 }, .{ 0.09, -0.018 }, .{ -0.008, -0.02 } });
}

fn sword(b: *Builder) void {
    shape(b, .steel, 0.006, &.{ .{ -0.06, 0.022 }, .{ -0.62, 0.016 }, .{ -0.72, 0.0 }, .{ -0.62, -0.016 }, .{ -0.06, -0.022 } });
    b.glowing(.red, 200);
    b.box(vec(0, 0, -0.36), Basis.world, vec(0.0065, 0.004, 0.27));
    shape(b, .dark, 0.03, &.{ .{ -0.075, 0.07 }, .{ -0.05, 0.07 }, .{ -0.05, -0.07 }, .{ -0.075, -0.07 } });
    shape(b, .red, 0.016, &.{ .{ -0.05, 0.018 }, .{ 0.08, 0.016 }, .{ 0.08, -0.016 }, .{ -0.05, -0.018 } });
    b.paint(.dark);
    b.sphere(vec(0, 0, 0.095), 0.024, 5, 8);
}

fn launcher(b: *Builder, s: weapons.Spec) void {
    if (s.fire == .rocket) {
        tube(b, .mint, 0.32, -0.36, 0.02, 0.055);
        tube(b, .orange, -0.36, -0.42, 0.02, 0.065);
        tube(b, .dark, 0.32, 0.36, 0.02, 0.062);
        part(b, .dark, 0, -0.06, -0.06, 0.014, 0.05, 0.02);
        grip(b, .dark, 0.05, -0.02);
        part(b, .yellow, -0.07, 0.04, -0.12, 0.012, 0.025, 0.035);

        return;
    }

    tube(b, .dark, 0.1, -0.24, 0.0, 0.045);
    b.paint(.green);
    b.cylinder(vec(-0.05, -0.02, -0.06), vec(0.05, -0.02, -0.06), 0.06, 16, true);
    tube(b, .orange, -0.24, -0.28, 0.0, 0.05);
    grip(b, .dark, 0.06, -0.03);
    part(b, .green, 0, -0.02, 0.16, 0.018, 0.04, 0.07);
}

fn buildGun(s: weapons.Spec) rl.Mesh {
    var b: Builder = .{};

    switch (s.class) {
        .melee => if (s.lifesteal > 0) sword(&b) else knife(&b),
        .bow => bow(&b, s),
        .crossbow => crossbow(&b, s),
        .launcher => launcher(&b, s),
        else => firearm(&b, s),
    }

    return b.finish();
}

fn buildBand(p: Paint) rl.Mesh {
    var b: Builder = .{};

    b.glowing(p, 90);
    b.box(.{}, Basis.world, vec(0.024, 0.012, 0.03));

    return b.finish();
}

fn buildBeam(p: Paint) rl.Mesh {
    var b: Builder = .{};

    const segs: usize = 28;

    b.glowing(p, 70);

    for (0..segs) |i| {
        const a0 = @as(f32, @floatFromInt(i)) / @as(f32, @floatFromInt(segs)) * std.math.tau;
        const a1 = @as(f32, @floatFromInt(i + 1)) / @as(f32, @floatFromInt(segs)) * std.math.tau;
        const r0: f32 = 0.38;
        const r1: f32 = 0.42;
        const y: f32 = -0.47;

        b.quad(vec(@cos(a0) * r0, y, @sin(a0) * r0), vec(@cos(a1) * r0, y, @sin(a1) * r0), vec(@cos(a1) * r1, y, @sin(a1) * r1), vec(@cos(a0) * r1, y, @sin(a0) * r1), .{ .y = 1 });
    }

    b.glowing(p, 25);
    b.cylinder(vec(0, -0.47, 0), vec(0, -0.05, 0), 0.006, 5, false);

    return b.finish();
}

fn buildArrow() rl.Mesh {
    var b: Builder = .{};

    rod(&b, .wood, vec(0, 0, 0.3), vec(0, 0, -0.25), 0.006);
    b.paint(.steel);
    b.cone(vec(0, 0, -0.25), vec(0, 0, -0.31), 0.014, 8);
    b.paint(.red);
    b.flat(vec(0, 0, 0.22), vec(0, 0.035, 0.3), vec(0, 0, 0.3), vec(1, 0, 0));
    b.flat(vec(0, 0, 0.22), vec(0, -0.035, 0.3), vec(0, 0, 0.3), vec(-1, 0, 0));
    b.flat(vec(0, 0, 0.22), vec(0.035, 0, 0.3), vec(0, 0, 0.3), vec(0, 1, 0));

    return b.finish();
}

fn buildDroneBody() rl.Mesh {
    var b: Builder = .{};

    b.paint(.white);
    b.sphere(.{}, 0.45, 12, 16);
    b.paint(.red);
    b.cylinder(vec(0, -0.12, 0), vec(0, 0.12, 0), 0.47, 20, true);
    b.paint(.dark);
    b.cylinder(vec(0, -0.05, -0.3), vec(0, -0.05, -0.5), 0.16, 16, true);
    b.glowing(.yellow, 255);
    b.sphere(vec(0, -0.05, -0.5), 0.1, 8, 12);

    b.paint(.dark);
    b.box(vec(0, 0.28, 0), Basis.world, vec(0.75, 0.035, 0.06));
    b.box(vec(0, 0.28, 0), Basis.world, vec(0.06, 0.035, 0.75));
    b.paint(.red);

    const tips = [_]Vec3{ vec(0.75, 0.28, 0), vec(-0.75, 0.28, 0), vec(0, 0.28, 0.75), vec(0, 0.28, -0.75) };

    for (tips) |t| b.cylinder(t, t.add(.{ .y = 0.1 }), 0.06, 12, true);

    return b.finish();
}

fn buildDroneRotor() rl.Mesh {
    var b: Builder = .{};

    b.paint(.steel);
    b.box(.{}, Basis.world, vec(0.28, 0.01, 0.035));
    b.box(.{}, Basis.world, vec(0.035, 0.01, 0.28));

    return b.finish();
}

fn buildRocket() rl.Mesh {
    var b: Builder = .{};

    b.paint(.white);
    b.cylinder(vec(0, 0, 0.25), vec(0, 0, -0.15), 0.07, 12, true);
    b.paint(.red);
    b.cone(vec(0, 0, -0.15), vec(0, 0, -0.32), 0.07, 12);
    b.paint(.orange);
    b.box(vec(0, 0, 0.22), Basis.world, vec(0.13, 0.008, 0.05));
    b.box(vec(0, 0, 0.22), Basis.world, vec(0.008, 0.13, 0.05));
    b.glowing(.yellow, 255);
    b.sphere(vec(0, 0, 0.3), 0.06, 6, 8);

    return b.finish();
}

fn buildGrenade() rl.Mesh {
    var b: Builder = .{};

    b.paint(.green);
    b.sphere(.{}, 0.12, 8, 12);
    b.paint(.dark);
    b.cylinder(vec(0, 0.1, 0), vec(0, 0.17, 0), 0.04, 10, true);
    b.glowing(.red, 255);
    b.sphere(vec(0, 0.17, 0), 0.025, 4, 6);

    return b.finish();
}

fn buildOrb(p: Paint, glow: u8) rl.Mesh {
    var b: Builder = .{};

    b.glowing(p, glow);
    b.sphere(.{}, 0.16, 8, 12);

    return b.finish();
}

fn buildPickup() rl.Mesh {
    var b: Builder = .{};

    b.paint(.green);
    b.box(.{}, Basis.world, vec(0.3, 0.22, 0.22));
    b.paint(.yellow);
    b.box(vec(0, 0, 0.225), Basis.world, vec(0.14, 0.04, 0.01));
    b.box(vec(0, 0, 0.225), Basis.world, vec(0.04, 0.14, 0.01));

    return b.finish();
}

fn buildMedkit() rl.Mesh {
    var b: Builder = .{};

    b.paint(.white);
    b.box(.{}, Basis.world, vec(0.26, 0.18, 0.18));
    b.paint(.red);
    b.box(vec(0, 0, 0.185), Basis.world, vec(0.12, 0.035, 0.01));
    b.box(vec(0, 0, 0.185), Basis.world, vec(0.035, 0.12, 0.01));
    b.box(vec(0, 0, -0.185), Basis.world, vec(0.12, 0.035, 0.01));
    b.box(vec(0, 0, -0.185), Basis.world, vec(0.035, 0.12, 0.01));

    return b.finish();
}

fn buildSky() rl.Mesh {
    var b: Builder = .{};

    b.sphere(.{}, 500, 24, 48);

    return b.finish();
}

fn buildLimb(p: Paint, segments: u32) rl.Mesh {
    var b: Builder = .{};

    b.paint(p);
    b.cylinder(.{}, vec(0, 1, 0), 1, segments, true);

    return b.finish();
}

fn buildBlockGlove() rl.Mesh {
    var b: Builder = .{};

    b.paint(.glove);
    b.bevelBox(vec(-0.044, -0.04, -0.05), vec(0.044, 0.034, 0.042), 0.012);
    b.paint(.steel);
    b.bevelBox(vec(-0.046, 0.016, -0.056), vec(0.046, 0.04, -0.022), 0.007);
    b.paint(.glove);
    b.bevelBox(vec(-0.04, -0.034, -0.068), vec(0.04, 0.012, -0.046), 0.008);
    b.paint(.olive);
    b.bevelBox(vec(-0.048, -0.045, 0.038), vec(0.048, 0.04, 0.066), 0.008);

    return b.finish();
}

fn buildGlove() rl.Mesh {
    var b: Builder = .{};

    b.paint(.glove);
    b.sphere(vec(0, 0.004, 0.012), 0.036, 6, 12);
    b.cylinder(vec(-0.034, -0.006, -0.022), vec(0.034, -0.006, -0.022), 0.024, 12, true);
    b.sphere(vec(-0.034, -0.006, -0.022), 0.024, 5, 10);
    b.sphere(vec(0.034, -0.006, -0.022), 0.024, 5, 10);
    b.cylinder(vec(0.03, 0.02, 0.01), vec(0.02, 0.028, -0.03), 0.013, 10, true);
    b.paint(.olive);
    b.cylinder(vec(0, -0.012, 0.022), vec(0, -0.05, 0.045), 0.024, 14, true);

    return b.finish();
}

pub var ground_map: ?rl.Texture2D = null;
pub var ground_extent: f32 = 0;
pub var ground_pixels: []u8 = &.{};
pub var ground_n: usize = 0;

pub fn groundAt(x: f32, z: f32) ?palette.Rgb {
    if (ground_n == 0) return null;

    const s: f32 = @floatFromInt(ground_n);
    const fx = (x + ground_extent) / (2 * ground_extent) * s;
    const fz = (z + ground_extent) / (2 * ground_extent) * s;

    if (fx < 0 or fz < 0 or fx >= s or fz >= s) return null;

    const o = (@as(usize, @intFromFloat(fz)) * ground_n + @as(usize, @intFromFloat(fx))) * 4;

    return .{ ground_pixels[o], ground_pixels[o + 1], ground_pixels[o + 2] };
}

fn blobSmooth(x: f32, z: f32) f32 {
    if (blob_n == 0) return 0;

    const fx = x + shared.terrain.half - 0.5;
    const fz = z + shared.terrain.half - 0.5;
    const x0 = @floor(fx);
    const z0 = @floor(fz);
    const kx = fx - x0;
    const kz = fz - z0;
    const a = blobAt(x0 - shared.terrain.half + 0.5, z0 - shared.terrain.half + 0.5);
    const b = blobAt(x0 - shared.terrain.half + 1.5, z0 - shared.terrain.half + 0.5);
    const c = blobAt(x0 - shared.terrain.half + 0.5, z0 - shared.terrain.half + 1.5);
    const d = blobAt(x0 - shared.terrain.half + 1.5, z0 - shared.terrain.half + 1.5);

    return (a * (1 - kx) + b * kx) * (1 - kz) + (c * (1 - kx) + d * kx) * kz;
}

const GroundGrid = struct {
    coarse: []f32,
    cn: usize,
    raw: []f32,
    out: []u8,
    n: usize,
    extent: f32,
    texel: f32,
    reach: f32,

    fn at(g: *const GroundGrid, i: i32, j: i32) [3]f32 {
        const m: i32 = @intCast(g.n - 1);
        const ci: usize = @intCast(std.math.clamp(i, 0, m));
        const cj: usize = @intCast(std.math.clamp(j, 0, m));
        const k = (cj * g.n + ci) * 3;

        return .{ g.raw[k], g.raw[k + 1], g.raw[k + 2] };
    }

    fn sample(g: *const GroundGrid, fi: f32, fj: f32) [3]f32 {
        const x0 = @floor(fi);
        const z0 = @floor(fj);
        const kx = fi - x0;
        const kz = fj - z0;
        const ix: i32 = @intFromFloat(x0);
        const iz: i32 = @intFromFloat(z0);
        const a = g.at(ix, iz);
        const b = g.at(ix + 1, iz);
        const c = g.at(ix, iz + 1);
        const d = g.at(ix + 1, iz + 1);
        var out: [3]f32 = undefined;

        for (0..3) |q| out[q] = (a[q] * (1 - kx) + b[q] * kx) * (1 - kz) + (c[q] * (1 - kx) + d[q] * kx) * kz;

        return out;
    }

    fn pos(g: *const GroundGrid, i: usize) f32 {
        return -g.extent + (@as(f32, @floatFromInt(i)) + 0.5) * g.texel;
    }

    fn coarsePos(g: *const GroundGrid, i: usize) f32 {
        return -g.extent + @as(f32, @floatFromInt(i)) * (g.extent * 2 / @as(f32, @floatFromInt(g.cn - 1)));
    }

    fn rawRows(g: *GroundGrid, r0: usize, r1: usize) void {
        for (r0..r1) |j| {
            const z = g.coarsePos(j);

            for (0..g.cn) |i| {
                const c = groundColor(g.coarsePos(i), z);
                const k = (j * g.cn + i) * 3;

                for (0..3) |q| g.coarse[k + q] = @as(f32, @floatFromInt(c[q])) / 255.0;
            }
        }
    }

    fn upRows(g: *GroundGrid, r0: usize, r1: usize) void {
        const scale = @as(f32, @floatFromInt(g.cn - 1)) / (g.extent * 2);

        for (r0..r1) |j| {
            const fz = (g.pos(j) + g.extent) * scale;
            const z0: usize = @min(g.cn - 2, @as(usize, @intFromFloat(@max(0, @floor(fz)))));
            const kz = std.math.clamp(fz - @as(f32, @floatFromInt(z0)), 0, 1);

            for (0..g.n) |i| {
                const fx = (g.pos(i) + g.extent) * scale;
                const x0: usize = @min(g.cn - 2, @as(usize, @intFromFloat(@max(0, @floor(fx)))));
                const kx = std.math.clamp(fx - @as(f32, @floatFromInt(x0)), 0, 1);
                const a = (z0 * g.cn + x0) * 3;
                const b = a + 3;
                const c = a + g.cn * 3;
                const d = c + 3;
                const k = (j * g.n + i) * 3;

                for (0..3) |q| g.raw[k + q] = (g.coarse[a + q] * (1 - kx) + g.coarse[b + q] * kx) * (1 - kz) + (g.coarse[c + q] * (1 - kx) + g.coarse[d + q] * kx) * kz;
            }
        }
    }

    fn crispRows(g: *GroundGrid, r0: usize, r1: usize) void {
        const reach: f32 = g.reach / g.texel;
        const k: i32 = @max(2, @as(i32, @intFromFloat(@round(reach * 0.5))));

        for (r0..r1) |j| {
            const z = g.pos(j);
            const jj: i32 = @intCast(j);

            for (0..g.n) |i| {
                const x = g.pos(i);
                const ii: i32 = @intCast(i);
                const c = g.at(ii, jj);
                var out = c;
                const xa = g.at(ii + k, jj);
                const xb = g.at(ii - k, jj);
                const za = g.at(ii, jj + k);
                const zb = g.at(ii, jj - k);
                const gx = sub3(xa, xb);
                const gz = sub3(za, zb);
                const e = if (dot3(gx, gz) >= 0) add3(gx, gz) else sub3(gx, gz);

                if (l1(e) > 0.05 and std.c.getenv("DF_GROUNDRAW") == null) {
                    var dx = dot3(gx, e);
                    var dz = dot3(gz, e);
                    const len = @sqrt(dx * dx + dz * dz);

                    if (len > 1e-5) {
                        dx /= len;
                        dz /= len;

                        const fi: f32 = @floatFromInt(i);
                        const fj: f32 = @floatFromInt(j);
                        const ca = g.sample(fi - dx * reach, fj - dz * reach);
                        const cb = g.sample(fi + dx * reach, fj + dz * reach);
                        const ca2 = g.sample(fi - dx * reach * 1.7, fj - dz * reach * 1.7);
                        const cb2 = g.sample(fi + dx * reach * 1.7, fj + dz * reach * 1.7);
                        const diff = sub3(cb, ca);
                        const len2 = dot3(diff, diff);
                        const span = l1(diff) + 0.02;
                        const plateau = 1 - shared.terrain.smooth(0.2, 0.45, (l1(sub3(ca2, ca)) + l1(sub3(cb2, cb))) / span);
                        const strength = plateau * @max(shared.terrain.smooth(0.16, 0.36, l1(sub3(chroma(ca), chroma(cb)))), shared.terrain.smooth(0.4, 0.7, @abs(@log((luma(ca) + 0.02) / (luma(cb) + 0.02)))));

                        if (len2 > 1e-5 and strength > 0) {
                            const t = std.math.clamp(dot3(sub3(c, ca), diff) / len2, 0, 1);
                            const th = 0.5 + (shared.terrain.fbm(x * 0.55 + 13.1, z * 0.55 - 7.7) - 0.5) * 0.55 + (shared.terrain.fbm(x * 2.1, z * 2.1) - 0.5) * 0.18;
                            const s = shared.terrain.smooth(th - 0.07, th + 0.07, t);
                            const rim = 1 - 0.12 * (1 - shared.terrain.smooth(0.0, 0.09, @abs(t - th)));

                            for (0..3) |q| {
                                const crisp = (ca[q] + diff[q] * s) * rim;

                                out[q] = c[q] + (crisp - c[q]) * strength;
                            }
                        }
                    }
                }

                const ao = 1 - 0.42 * blobSmooth(x, z);
                const o = (j * g.n + i) * 4;

                for (0..3) |q| g.out[o + q] = @intFromFloat(std.math.clamp(out[q] * ao * 255.0, 0, 255));

                g.out[o + 3] = 255;
            }
        }
    }
};

fn sub3(a: [3]f32, b: [3]f32) [3]f32 {
    return .{ a[0] - b[0], a[1] - b[1], a[2] - b[2] };
}

fn add3(a: [3]f32, b: [3]f32) [3]f32 {
    return .{ a[0] + b[0], a[1] + b[1], a[2] + b[2] };
}

fn dot3(a: [3]f32, b: [3]f32) f32 {
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

fn l1(a: [3]f32) f32 {
    return @abs(a[0]) + @abs(a[1]) + @abs(a[2]);
}

fn luma(a: [3]f32) f32 {
    return a[0] * 0.3 + a[1] * 0.59 + a[2] * 0.11;
}

fn chroma(a: [3]f32) [3]f32 {
    const s = a[0] + a[1] + a[2] + 0.03;

    return .{ a[0] * 3 / s, a[1] * 3 / s, a[2] * 3 / s };
}

fn groundRaw(g: *GroundGrid, r0: usize, r1: usize) void {
    g.rawRows(r0, r1);
}

fn groundUp(g: *GroundGrid, r0: usize, r1: usize) void {
    g.upRows(r0, r1);
}

fn groundCrisp(g: *GroundGrid, r0: usize, r1: usize) void {
    g.crispRows(r0, r1);
}

fn runRows(g: *GroundGrid, rows: usize, comptime f: fn (*GroundGrid, usize, usize) void) void {
    const cpus = std.Thread.getCpuCount() catch 1;
    const workers = std.math.clamp(cpus, 1, 8);
    var threads: [8]?std.Thread = @splat(null);
    const per = (rows + workers - 1) / workers;

    for (1..workers) |w| {
        const r0 = @min(rows, w * per);
        const r1 = @min(rows, r0 + per);

        threads[w] = std.Thread.spawn(.{}, f, .{ g, r0, r1 }) catch blk: {
            f(g, r0, r1);

            break :blk null;
        };
    }

    f(g, 0, @min(rows, per));

    for (threads) |t| {
        if (t) |th| th.join();
    }
}

pub fn buildGroundMap() void {
    const t = shared.terrain;

    if (ground_map) |m| rl.UnloadTexture(m);

    ground_map = null;

    if (chunks.len == 0 or t.current == .prism or t.current == .courtyard) return;

    const extent = t.half + 2;
    const n: usize = @intFromFloat(@min(1024, @ceil(extent * 2 / 0.48)));
    const gpa = std.heap.page_allocator;
    const raw = gpa.alloc(f32, n * n * 3) catch return;
    defer gpa.free(raw);
    const cn = n / 2 + 1;
    const coarse = gpa.alloc(f32, cn * cn * 3) catch return;
    defer gpa.free(coarse);
    if (ground_pixels.len > 0) gpa.free(ground_pixels);

    ground_pixels = &.{};
    ground_n = 0;

    const out = gpa.alloc(u8, n * n * 4) catch return;
    var g: GroundGrid = .{ .coarse = coarse, .cn = cn, .raw = raw, .out = out, .n = n, .extent = extent, .texel = extent * 2 / @as(f32, @floatFromInt(n)), .reach = 3.2 };

    runRows(&g, cn, groundRaw);
    runRows(&g, n, groundUp);
    runRows(&g, n, groundCrisp);

    const img: rl.Image = .{ .data = out.ptr, .width = @intCast(n), .height = @intCast(n), .mipmaps = 1, .format = rl.PIXELFORMAT_UNCOMPRESSED_R8G8B8A8 };

    if (std.c.getenv("DF_GROUNDDUMP")) |p| _ = rl.ExportImage(img, p);
    const tex = mips.upload(img);

    ground_pixels = out;
    ground_n = n;
    ground_extent = extent;

    if (tex.id == 0) return;

    rl.SetTextureFilter(tex, rl.TEXTURE_FILTER_TRILINEAR);
    rl.SetTextureWrap(tex, rl.TEXTURE_WRAP_CLAMP);
    ground_map = tex;
}
