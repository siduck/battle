const std = @import("std");
const rl = @import("raylib");
const shared = @import("shared");
const gfx = @import("gfx.zig");
const mesh = @import("mesh.zig");
const models = @import("models.zig");
const palette = @import("palette.zig");
const assets = @import("assets.zig");

const Vec3 = shared.math.Vec3;
const terrain = shared.terrain;
const world = shared.world;
const max_items = 3600;
const step: f32 = 0.95;

const Class = enum { none, grass, sand, dirt, grey };

const Set = struct {
    model: ?rl.Model = null,
    items: [max_items]rl.Matrix = undefined,
    n: usize = 0,
};

var ready = false;
var tufts: [2]Set = .{ .{}, .{} };
var pebbles: Set = .{};
var stones: Set = .{};
var flowers: [2]Set = .{ .{}, .{} };
var litter: Set = .{};
var conf: shared.maps.Scatter = .{};
var centre: Vec3 = .{ .y = -1e6 };
var mask: []u8 = &.{};
var mask_size: usize = 0;
var mask_half: f32 = 0;

fn hash(x: i32, z: i32, salt: u32) f32 {
    const a: u32 = @bitCast(x *% 73856093);
    const b: u32 = @bitCast(z *% 19349663);
    var h = a ^ b ^ (salt *% 83492791);

    h ^= h >> 13;
    h *%= 0x5bd1e995;
    h ^= h >> 15;

    return @as(f32, @floatFromInt(h % 10000)) / 10000.0;
}

fn classify(c: palette.Rgb) Class {
    const r: f32 = @floatFromInt(c[0]);
    const g: f32 = @floatFromInt(c[1]);
    const b: f32 = @floatFromInt(c[2]);

    if (g > r * 0.95 and g > b * 1.35) return .grass;

    if (r > 165 and r > g and g > b and b < g * 0.86) return .sand;

    const mx = @max(r, @max(g, b));
    const mn = @min(r, @min(g, b));

    if (mx > 40 and (mx - mn) / mx < 0.13) return .grey;

    if (r > g and g > b and r < 175) return .dirt;

    return .none;
}

fn scaled(c: palette.Rgb, k: f32) palette.Rgb {
    return .{
        @intFromFloat(@min(255, @as(f32, @floatFromInt(c[0])) * k)),
        @intFromFloat(@min(255, @as(f32, @floatFromInt(c[1])) * k)),
        @intFromFloat(@min(255, @as(f32, @floatFromInt(c[2])) * k)),
    };
}

fn tuftModel(base: palette.Rgb, k: f32, seed: u32) rl.Model {
    var b: mesh.Builder = .{};
    const blades: u32 = 9;

    for (0..blades) |i| {
        const fi: f32 = @floatFromInt(i);
        const ang = fi * 2.39996 + @as(f32, @floatFromInt(seed));
        const rad = 0.03 + hash(@intCast(i), 3, seed) * 0.07;
        const ox = @cos(ang) * rad;
        const oz = @sin(ang) * rad;
        const h = 0.16 + hash(@intCast(i), 7, seed) * 0.2;
        const lean = 0.05 + hash(@intCast(i), 11, seed) * 0.08;
        const w: f32 = 0.034;
        const side: Vec3 = .{ .x = -@sin(ang) * w, .z = @cos(ang) * w };
        const p0: Vec3 = .{ .x = ox - side.x, .z = oz - side.z };
        const p1: Vec3 = .{ .x = ox + side.x, .z = oz + side.z };
        const tip: Vec3 = .{ .x = ox + @cos(ang) * lean, .y = h, .z = oz + @sin(ang) * lean };
        const tone = k * (0.9 + hash(@intCast(i), 13, seed) * 0.22);

        const up: Vec3 = .{ .y = 1 };

        b.style = .{ .color = scaled(base, tone) };
        b.tri(p0, p1, tip, up, up, up, up);
    }

    return rl.LoadModelFromMesh(b.finish());
}

fn pebbleModel(base: palette.Rgb) rl.Model {
    var b: mesh.Builder = .{};

    for (0..3) |i| {
        const fi: f32 = @floatFromInt(i);
        const x = @cos(fi * 2.1) * 0.12 * fi;
        const z = @sin(fi * 2.1) * 0.1 * fi;
        const s = 0.08 - fi * 0.018;

        b.style = .{ .color = scaled(base, 0.78 + fi * 0.08) };
        b.box(.{ .x = x, .y = s * 0.35, .z = z }, mesh.Basis.yawed(fi * 1.3), .{ .x = s, .y = s * 0.55, .z = s * 0.8 });
    }

    return rl.LoadModelFromMesh(b.finish());
}

fn flowerModel(petal: palette.Rgb, stem: palette.Rgb, seed: u32) rl.Model {
    var b: mesh.Builder = .{};
    const up: Vec3 = .{ .y = 1 };

    for (0..5) |i| {
        const ang = @as(f32, @floatFromInt(i)) * 2.39996 + @as(f32, @floatFromInt(seed));
        const rad = 0.05 + hash(@intCast(i), 21, seed) * 0.16;
        const cx = @cos(ang) * rad;
        const cz = @sin(ang) * rad;
        const h = 0.12 + hash(@intCast(i), 23, seed) * 0.14;
        const w: f32 = 0.012;

        b.style = .{ .color = stem };
        b.tri(.{ .x = cx - w, .z = cz }, .{ .x = cx + w, .z = cz }, .{ .x = cx, .y = h, .z = cz }, up, up, up, up);
        b.style = .{ .color = scaled(petal, 0.92 + hash(@intCast(i), 25, seed) * 0.16) };

        const p: f32 = 0.045;

        for (0..5) |k| {
            const a0 = @as(f32, @floatFromInt(k)) * 1.2566;
            const a1 = a0 + 0.9;

            b.tri(.{ .x = cx, .y = h, .z = cz }, .{ .x = cx + @cos(a0) * p, .y = h + 0.012, .z = cz + @sin(a0) * p }, .{ .x = cx + @cos(a1) * p, .y = h + 0.012, .z = cz + @sin(a1) * p }, up, up, up, up);
        }
    }

    return rl.LoadModelFromMesh(b.finish());
}

fn litterModel(seed: u32) rl.Model {
    var b: mesh.Builder = .{};
    const up: Vec3 = .{ .y = 1 };
    const tones = [_]palette.Rgb{ .{ 150, 96, 48 }, .{ 178, 128, 56 }, .{ 120, 84, 46 }, .{ 160, 140, 70 } };

    for (0..7) |i| {
        const ang = @as(f32, @floatFromInt(i)) * 2.1 + @as(f32, @floatFromInt(seed));
        const rad = hash(@intCast(i), 31, seed) * 0.35;
        const cx = @cos(ang) * rad;
        const cz = @sin(ang) * rad;
        const rot = hash(@intCast(i), 33, seed) * 6.283;
        const l: f32 = 0.06 + hash(@intCast(i), 35, seed) * 0.04;
        const w = l * 0.45;
        const fx = @cos(rot);
        const fz = @sin(rot);
        const y: f32 = 0.015 + @as(f32, @floatFromInt(i)) * 0.002;

        b.style = .{ .color = tones[i % tones.len] };
        b.tri(.{ .x = cx - fx * l, .y = y, .z = cz - fz * l }, .{ .x = cx - fz * w, .y = y, .z = cz + fx * w }, .{ .x = cx + fx * l, .y = y, .z = cz + fz * l }, up, up, up, up);
        b.tri(.{ .x = cx - fx * l, .y = y, .z = cz - fz * l }, .{ .x = cx + fx * l, .y = y, .z = cz + fz * l }, .{ .x = cx + fz * w, .y = y, .z = cz - fx * w }, up, up, up, up);
    }

    return rl.LoadModelFromMesh(b.finish());
}

fn groundRgb(x: f32, z: f32) palette.Rgb {
    return models.groundAt(x, z) orelse models.groundColor(x, z);
}

fn edgeAt(x: f32, z: f32, cls: Class) bool {
    const e: f32 = 1.3;

    return classify(groundRgb(x + e, z)) != cls or classify(groundRgb(x - e, z)) != cls or classify(groundRgb(x, z + e)) != cls or classify(groundRgb(x, z - e)) != cls;
}

fn nearProp(x: f32, z: f32) bool {
    const e: f32 = 1.4;

    return blocked(x + e, z) or blocked(x - e, z) or blocked(x, z + e) or blocked(x, z - e);
}

fn markBox(min_x: f32, min_z: f32, max_x: f32, max_z: f32) void {
    const s: f32 = @floatFromInt(mask_size);
    const x0: i32 = @intFromFloat(@max(0, @floor(min_x + mask_half)));
    const z0: i32 = @intFromFloat(@max(0, @floor(min_z + mask_half)));
    const x1: i32 = @intFromFloat(@min(s - 1, @floor(max_x + mask_half)));
    const z1: i32 = @intFromFloat(@min(s - 1, @floor(max_z + mask_half)));

    if (x1 < x0 or z1 < z0) return;

    var z = z0;

    while (z <= z1) : (z += 1) {
        var x = x0;

        while (x <= x1) : (x += 1) mask[@as(usize, @intCast(z)) * mask_size + @as(usize, @intCast(x))] = 1;
    }
}

fn buildMask() void {
    mask_half = terrain.half + 4;
    mask_size = @intFromFloat(mask_half * 2);
    mask = std.heap.page_allocator.alloc(u8, mask_size * mask_size) catch {
        mask_size = 0;

        return;
    };

    @memset(mask, 0);

    for (world.pieces) |p| {
        const bb = p.shape.bounds();
        const area = (bb.max.x - bb.min.x) * (bb.max.z - bb.min.z);

        if (area > 6000) continue;

        const g = terrain.height((bb.min.x + bb.max.x) * 0.5, (bb.min.z + bb.max.z) * 0.5);

        if (bb.max.y < g + 0.5 or bb.min.y > g + 2.5) continue;

        markBox(bb.min.x - 0.3, bb.min.z - 0.3, bb.max.x + 0.3, bb.max.z + 0.3);
    }

    for (world.placements) |pl| {
        const info = shared.props.info(pl.kind);

        if (info.group == .ground) continue;

        const g = terrain.height(pl.pos.x, pl.pos.z);

        if (pl.pos.y + info.max[1] * pl.scale < g + 0.2 or pl.pos.y + info.min[1] * pl.scale > g + 2.5) continue;

        const r = if (info.group == .tree) 0.6 else @min(12, @max(@max(@abs(info.min[0]), info.max[0]), @max(@abs(info.min[2]), info.max[2])) * pl.scale * 0.85);

        markBox(pl.pos.x - r, pl.pos.z - r, pl.pos.x + r, pl.pos.z + r);
    }
}

fn blocked(x: f32, z: f32) bool {
    if (mask_size == 0) return false;

    const fx = x + mask_half;
    const fz = z + mask_half;

    if (fx < 0 or fz < 0) return true;

    const ix: usize = @intFromFloat(fx);
    const iz: usize = @intFromFloat(fz);

    if (ix >= mask_size or iz >= mask_size) return true;

    return mask[iz * mask_size + ix] != 0;
}

fn init() void {
    ready = true;

    if (terrain.current == .prism or terrain.current == .courtyard) return;

    var sum: [3]f32 = .{ 0, 0, 0 };
    var count: f32 = 0;
    var k: i32 = 0;

    while (k < 900) : (k += 1) {
        const x = (hash(k, 1, 5) * 2 - 1) * terrain.play;
        const z = (hash(k, 2, 5) * 2 - 1) * terrain.play;
        const c = models.groundColor(x, z);

        if (classify(c) != .grass) continue;

        for (0..3) |i| sum[i] += @floatFromInt(c[i]);

        count += 1;
    }

    const grass: palette.Rgb = if (count > 10) .{ @intFromFloat(sum[0] / count), @intFromFloat(sum[1] / count), @intFromFloat(sum[2] / count) } else .{ 122, 122, 85 };

    if (shared.maps.current()) |d| conf = d.scatter;

    if (terrain.current == .facility) conf.enabled = false;

    tufts[0].model = tuftModel(grass, 1.0, 1);
    tufts[1].model = tuftModel(grass, 1.18, 2);
    pebbles.model = pebbleModel(.{ 196, 172, 130 });
    stones.model = pebbleModel(.{ 150, 148, 142 });
    flowers[0].model = flowerModel(conf.flower_colors[0], scaled(grass, 0.8), 3);
    flowers[1].model = flowerModel(conf.flower_colors[1], scaled(grass, 0.8), 4);
    litter.model = litterModel(5);
    buildMask();
}

fn rebuild(eye: Vec3) void {
    const radius: f32 = if (assets.mobile) 18 else 30;
    const lo: i32 = @intFromFloat(@floor((eye.x - radius) / step));
    const hi: i32 = @intFromFloat(@floor((eye.x + radius) / step));
    const zlo: i32 = @intFromFloat(@floor((eye.z - radius) / step));
    const zhi: i32 = @intFromFloat(@floor((eye.z + radius) / step));

    tufts[0].n = 0;
    tufts[1].n = 0;
    pebbles.n = 0;
    stones.n = 0;
    flowers[0].n = 0;
    flowers[1].n = 0;
    litter.n = 0;

    if (!conf.enabled) return;

    const tuft_rate = if (shared.maps.current()) |d| d.tufts else @as(f32, 0.85);
    var iz = zlo;

    while (iz <= zhi) : (iz += 1) {
        var ix = lo;

        while (ix <= hi) : (ix += 1) {
            const x = (@as(f32, @floatFromInt(ix)) + hash(ix, iz, 1)) * step;
            const z = (@as(f32, @floatFromInt(iz)) + hash(ix, iz, 2)) * step;
            const dx = x - eye.x;
            const dz = z - eye.z;

            if (dx * dx + dz * dz > radius * radius) continue;

            if (@abs(x) > terrain.play or @abs(z) > terrain.play) continue;

            if (blocked(x, z)) continue;

            const roll = hash(ix, iz, 3);
            const cls = classify(groundRgb(x, z));

            if (cls == .none) continue;

            if (terrain.villageMask(x, z) > 0.05) continue;

            if (terrain.current == .valley and terrain.roadDistance(x, z) < terrain.road_half + 0.6) continue;

            const nrm = terrain.normal(x, z);

            if (nrm.y < 0.82) continue;

            const y = terrain.height(x, z);

            if (terrain.current == .islands and y < terrain.void_floor + 1) continue;

            const edge = edgeAt(x, z, cls);
            const prop = nearProp(x, z);
            const patch = terrain.fbm(x * 0.09 + 5.3, z * 0.09 - 2.1);
            const yaw = hash(ix, iz, 4) * 6.283;
            const s = 0.8 + hash(ix, iz, 5) * 0.6;
            const m = mesh.transform(.{ .x = x, .y = y - 0.02, .z = z }, mesh.Basis.yawed(yaw), s);
            const pick = hash(ix, iz, 6);
            var set: ?*Set = null;

            switch (cls) {
                .grass => {
                    const flower_rate = conf.flowers * 0.16 * terrain.smooth(0.55, 0.75, patch);
                    const litter_rate = conf.litter * (if (prop) @as(f32, 0.3) else 0.02);
                    const clump_rate = tuft_rate * conf.clumps * (if (edge or prop) @as(f32, 1.25) else 1.0);

                    if (roll < flower_rate) {
                        set = &flowers[if (pick > 0.5) 1 else 0];
                    } else if (roll < flower_rate + litter_rate) {
                        set = &litter;
                    } else if (roll < flower_rate + litter_rate + clump_rate) {
                        set = &tufts[if (pick > 0.5) 1 else 0];
                    }
                },
                .sand => {
                    if (roll < conf.pebbles * (if (edge or prop) @as(f32, 0.14) else 0.04)) set = &pebbles;
                },
                .dirt => {
                    const rate = conf.pebbles * (if (edge) @as(f32, 0.3) else if (prop) @as(f32, 0.2) else 0.07);

                    if (roll < rate) {
                        set = &pebbles;
                    } else if (edge and roll < rate + conf.clumps * 0.25) {
                        set = &tufts[if (pick > 0.5) 1 else 0];
                    } else if (prop and roll < rate + conf.litter * 0.12) {
                        set = &litter;
                    }
                },
                .grey => {
                    if (roll < conf.pebbles * (if (edge or prop) @as(f32, 0.22) else 0.06)) set = &stones;
                },
                .none => {},
            }

            if (set) |st| {
                if (st.n < max_items) {
                    st.items[st.n] = m;
                    st.n += 1;
                }
            }
        }
    }
}

pub fn draw(r: *gfx.Renderer, eye: Vec3) void {
    if (r.phase == .shadow) return;

    if (!ready) init();

    if (terrain.current == .prism or terrain.current == .courtyard) return;

    const d = eye.sub(centre);

    if (d.x * d.x + d.z * d.z > 16) {
        centre = eye;
        rebuild(eye);
    }

    r.setSway(6);

    for (&tufts) |*t| {
        if (t.model) |m| r.drawInstanced(m, t.items[0..t.n], true);
    }

    r.setSway(4);

    for (&flowers) |*f| {
        if (f.model) |m| r.drawInstanced(m, f.items[0..f.n], true);
    }

    r.setSway(0);

    if (pebbles.model) |m| r.drawInstanced(m, pebbles.items[0..pebbles.n], false);

    if (stones.model) |m| r.drawInstanced(m, stones.items[0..stones.n], false);

    if (litter.model) |m| r.drawInstanced(m, litter.items[0..litter.n], false);
}
