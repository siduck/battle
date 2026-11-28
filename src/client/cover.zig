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

    pebbles.model = pebbleModel(.{ 196, 172, 130 });
    stones.model = pebbleModel(.{ 150, 148, 142 });
    flowers[0].model = flowerModel(conf.flower_colors[0], scaled(grass, 0.8), 3);
    flowers[1].model = flowerModel(conf.flower_colors[1], scaled(grass, 0.8), 4);
    litter.model = litterModel(5);
    buildMask();
}

const Item = struct {
    m: rl.Matrix,
    x: f32,
    z: f32,
    set: u8,
};

const bucket: f32 = 8;
var items: []Item = &.{};
var starts: []u32 = &.{};
var buckets_n: usize = 0;
var baked = false;

fn sets(k: u8) *Set {
    return switch (k) {
        0 => &flowers[0],
        1 => &flowers[1],
        2 => &pebbles,
        3 => &stones,
        else => &litter,
    };
}

fn cell(ix: i32, iz: i32) ?Item {
    const x = (@as(f32, @floatFromInt(ix)) + hash(ix, iz, 1)) * step;
    const z = (@as(f32, @floatFromInt(iz)) + hash(ix, iz, 2)) * step;

    if (@abs(x) > terrain.play or @abs(z) > terrain.play) return null;

    if (blocked(x, z)) return null;

    const roll = hash(ix, iz, 3);
    const cls = classify(groundRgb(x, z));

    if (cls == .none) return null;

    if (terrain.villageMask(x, z) > 0.05) return null;

    if (terrain.current == .valley and terrain.roadDistance(x, z) < terrain.road_half + 0.6) return null;

    const nrm = terrain.normal(x, z);

    if (nrm.y < 0.82) return null;

    const y = terrain.height(x, z);

    if (terrain.current == .islands and y < terrain.void_floor + 1) return null;

    const edge = edgeAt(x, z, cls);
    const prop = nearProp(x, z);
    const patch = terrain.fbm(x * 0.09 + 5.3, z * 0.09 - 2.1);
    const yaw = hash(ix, iz, 4) * 6.283;
    const s = 0.8 + hash(ix, iz, 5) * 0.6;
    const m = mesh.transform(.{ .x = x, .y = y - 0.02, .z = z }, mesh.Basis.yawed(yaw), s);
    const pick = hash(ix, iz, 6);
    var set: ?u8 = null;

    switch (cls) {
        .grass => {
            const flower_rate = conf.flowers * 0.16 * terrain.smooth(0.55, 0.75, patch);
            const litter_rate = conf.litter * (if (prop) @as(f32, 0.3) else 0.02);

            if (roll < flower_rate) {
                set = if (pick > 0.5) 1 else 0;
            } else if (roll < flower_rate + litter_rate) {
                set = 4;
            }
        },
        .sand => {
            if (roll < conf.pebbles * (if (edge or prop) @as(f32, 0.14) else 0.04)) set = 2;
        },
        .dirt => {
            const rate = conf.pebbles * (if (edge) @as(f32, 0.3) else if (prop) @as(f32, 0.2) else 0.07);

            if (roll < rate) {
                set = 2;
            } else if (prop and roll < rate + conf.litter * 0.12) {
                set = 4;
            }
        },
        .grey => {
            if (roll < conf.pebbles * (if (edge or prop) @as(f32, 0.22) else 0.06)) set = 3;
        },
        .none => {},
    }

    const k = set orelse return null;

    return .{ .m = m, .x = x, .z = z, .set = k };
}

fn bucketOf(v: f32) usize {
    const half = @as(f32, @floatFromInt(buckets_n)) * bucket / 2;

    return @intFromFloat(std.math.clamp(@floor((v + half) / bucket), 0, @as(f32, @floatFromInt(buckets_n - 1))));
}

fn bake() void {
    baked = true;

    const gpa = std.heap.page_allocator;
    const reach = terrain.play + step;
    const lim: i32 = @intFromFloat(@ceil(reach / step));

    buckets_n = @intFromFloat(@ceil(2 * reach / bucket));

    var list: std.ArrayList(Item) = .empty;
    var iz = -lim;

    while (iz <= lim) : (iz += 1) {
        var ix = -lim;

        while (ix <= lim) : (ix += 1) {
            if (cell(ix, iz)) |it| list.append(gpa, it) catch return;
        }
    }

    const all = list.toOwnedSlice(gpa) catch return;
    const counts = gpa.alloc(u32, buckets_n * buckets_n + 1) catch return;

    @memset(counts, 0);

    for (all) |it| counts[bucketOf(it.z) * buckets_n + bucketOf(it.x) + 1] += 1;

    for (1..counts.len) |b| counts[b] += counts[b - 1];

    const sorted = gpa.alloc(Item, all.len) catch return;
    const fill = gpa.alloc(u32, buckets_n * buckets_n) catch return;

    @memcpy(fill, counts[0 .. counts.len - 1]);

    for (all) |it| {
        const b = bucketOf(it.z) * buckets_n + bucketOf(it.x);

        sorted[fill[b]] = it;
        fill[b] += 1;
    }

    gpa.free(fill);
    gpa.free(all);
    items = sorted;
    starts = counts;
}

fn rebuild(eye: Vec3) void {
    const radius: f32 = if (assets.mobile) 18 else 30;

    pebbles.n = 0;
    stones.n = 0;
    flowers[0].n = 0;
    flowers[1].n = 0;
    litter.n = 0;

    if (!conf.enabled) return;

    if (!baked) bake();

    if (buckets_n == 0 or starts.len == 0) return;

    const bx0 = bucketOf(eye.x - radius);
    const bx1 = bucketOf(eye.x + radius);
    const bz0 = bucketOf(eye.z - radius);
    const bz1 = bucketOf(eye.z + radius);

    for (bz0..bz1 + 1) |bz| {
        for (bx0..bx1 + 1) |bx| {
            const b = bz * buckets_n + bx;

            for (items[starts[b]..starts[b + 1]]) |it| {
                const dx = it.x - eye.x;
                const dz = it.z - eye.z;

                if (dx * dx + dz * dz > radius * radius) continue;

                const st = sets(it.set);

                if (st.n < max_items) {
                    st.items[st.n] = it.m;
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

    r.setSway(4);

    for (&flowers) |*f| {
        if (f.model) |m| r.drawInstanced(m, f.items[0..f.n], true);
    }

    r.setSway(0);

    if (pebbles.model) |m| r.drawInstanced(m, pebbles.items[0..pebbles.n], false);

    if (stones.model) |m| r.drawInstanced(m, stones.items[0..stones.n], false);

    if (litter.model) |m| r.drawInstanced(m, litter.items[0..litter.n], false);
}
