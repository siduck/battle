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

const Class = enum { none, grass, sand };

const Set = struct {
    model: ?rl.Model = null,
    items: [max_items]rl.Matrix = undefined,
    n: usize = 0,
};

var ready = false;
var tufts: [2]Set = .{ .{}, .{} };
var pebbles: Set = .{};
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
        const info = shared.props.infos[@intFromEnum(pl.kind)];

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

    tufts[0].model = tuftModel(grass, 1.0, 1);
    tufts[1].model = tuftModel(grass, 1.18, 2);
    pebbles.model = pebbleModel(.{ 196, 172, 130 });
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
            const cls = classify(models.groundColor(x, z));

            if (cls == .none) continue;

            if (cls == .grass and roll > 0.85) continue;

            if (cls == .sand and roll > 0.05) continue;

            if (terrain.current == .valley and terrain.roadDistance(x, z) < terrain.road_half + 0.6) continue;

            const nrm = terrain.normal(x, z);

            if (nrm.y < 0.82) continue;

            const y = terrain.height(x, z);

            if (terrain.current == .islands and y < terrain.void_floor + 1) continue;

            const yaw = hash(ix, iz, 4) * 6.283;
            const s = 0.8 + hash(ix, iz, 5) * 0.6;
            const m = mesh.transform(.{ .x = x, .y = y - 0.02, .z = z }, mesh.Basis.yawed(yaw), s);

            if (cls == .grass) {
                const set = &tufts[if (hash(ix, iz, 6) > 0.5) 1 else 0];

                if (set.n < max_items) {
                    set.items[set.n] = m;
                    set.n += 1;
                }
            } else if (pebbles.n < max_items) {
                pebbles.items[pebbles.n] = m;
                pebbles.n += 1;
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

    r.setSway(0);

    if (pebbles.model) |m| r.drawInstanced(m, pebbles.items[0..pebbles.n], false);
}
