const std = @import("std");
const shared = @import("shared");
const rl = @import("raylib");
const assets = @import("assets.zig");

const Vec3 = shared.math.Vec3;
const terrain = shared.terrain;
const world = shared.world;
const grid = shared.grid;

const cell: f32 = 32;
const reach: f32 = 420;
const eye_h: f32 = 1.7;
const high_eye: f32 = 7;
const min_occluder: f32 = 3.5;
const magic: u32 = 0x31535650;

const Header = extern struct {
    magic: u32,
    n: u32,
    origin: f32,
    pieces: u32,
    hash: u64,
};

var origin_x: f32 = 0;
var origin_z: f32 = 0;
var n: usize = 0;
var bits: []u64 = &.{};
var words: usize = 0;
var ready = false;

fn index(x: f32, z: f32) ?usize {
    const fx = @floor((x - origin_x) / cell);
    const fz = @floor((z - origin_z) / cell);

    if (fx < 0 or fz < 0) return null;

    const ix: usize = @intFromFloat(fx);
    const iz: usize = @intFromFloat(fz);

    if (ix >= n or iz >= n) return null;

    return iz * n + ix;
}

fn center(i: usize) [2]f32 {
    const ix: f32 = @floatFromInt(i % n);
    const iz: f32 = @floatFromInt(i / n);

    return .{ origin_x + (ix + 0.5) * cell, origin_z + (iz + 0.5) * cell };
}

fn ground(x: f32, z: f32) f32 {
    return terrain.height(x, z);
}

fn worldHash() u64 {
    var h = std.hash.Wyhash.init(7);

    for (world.pieces) |p| {
        const b = p.shape.bounds();

        h.update(std.mem.asBytes(&b));
    }

    return h.final();
}

fn clear(a: Vec3, b: Vec3) bool {
    const d = b.sub(a);
    const len = d.length();

    if (len < 0.5) return true;

    const dir = d.scale(1 / len);
    var t: f32 = 6;

    while (t < len - 2) : (t += 6) {
        const p = a.add(dir.scale(t));

        if (p.y < ground(p.x, p.z) - 0.5) return false;
    }

    var near = grid.ray(world.pieces, a, dir, len - 0.3);

    while (near.next()) |piece| {
        const b2 = piece.shape.bounds();

        if (b2.max.y - b2.min.y < min_occluder) continue;

        if (piece.shape.raycast(a, dir, len - 0.3) != null) return false;
    }

    return true;
}

fn sees(from: usize, to: usize) bool {
    if (from == to) return true;

    const a = center(from);
    const b = center(to);
    const dx = b[0] - a[0];
    const dz = b[1] - a[1];

    if (@abs(dx) <= cell * 1.5 and @abs(dz) <= cell * 1.5) return true;

    if (dx * dx + dz * dz > (reach + cell) * (reach + cell)) return true;

    const q = cell * 0.32;
    const eyes = [_][2]f32{ .{ 0, 0 }, .{ -q, -q }, .{ q, -q }, .{ -q, q }, .{ q, q } };
    const targets = [_][2]f32{ .{ 0, 0 }, .{ -q, -q }, .{ q, -q }, .{ -q, q }, .{ q, q } };
    const lifts = [_]f32{ 1.5, 12 };

    for (lifts) |lift| {
        for (targets) |t| {
            const tx = b[0] + t[0];
            const tz = b[1] + t[1];
            const goal = Vec3{ .x = tx, .y = ground(tx, tz) + lift, .z = tz };

            for (eyes) |e| {
                const ex = a[0] + e[0];
                const ez = a[1] + e[1];

                if (clear(.{ .x = ex, .y = ground(ex, ez) + eye_h, .z = ez }, goal)) return true;
            }
        }
    }

    return false;
}

fn set(from: usize, to: usize) void {
    bits[from * words + to / 64] |= @as(u64, 1) << @intCast(to % 64);
}

fn layout() void {
    const half = terrain.play + cell * 4;

    origin_x = -half;
    origin_z = -half;
    n = @intFromFloat(@ceil(half * 2 / cell));
    words = (n * n + 63) / 64;
}

fn compute() bool {
    const gpa = std.heap.page_allocator;

    layout();
    bits = gpa.alloc(u64, n * n * words) catch return false;
    @memset(bits, 0);

    for (0..n * n) |from| {
        for (from..n * n) |to| {
            if (!sees(from, to)) continue;

            set(from, to);
            set(to, from);
        }
    }

    return true;
}

pub fn generate(out_dir: []const u8, map_name: []const u8) void {
    const t0 = rl.GetTime();

    if (!compute()) return;

    const head = Header{ .magic = magic, .n = @intCast(n), .origin = origin_x, .pieces = @intCast(world.pieces.len), .hash = worldHash() };
    var path_buf: [512]u8 = undefined;
    const path = std.fmt.bufPrintSentinel(&path_buf, "{s}/{s}.bin", .{ out_dir, map_name }, 0) catch return;
    const total = @sizeOf(Header) + bits.len * 8;
    const data = std.heap.page_allocator.alloc(u8, total) catch return;

    defer std.heap.page_allocator.free(data);
    @memcpy(data[0..@sizeOf(Header)], std.mem.asBytes(&head));
    @memcpy(data[@sizeOf(Header)..], std.mem.sliceAsBytes(bits));
    _ = rl.SaveFileData(path.ptr, data.ptr, @intCast(total));

    var hidden: usize = 0;

    for (0..n * n) |i| {
        for (0..n * n) |j| {
            if (bits[i * words + j / 64] & (@as(u64, 1) << @intCast(j % 64)) == 0) hidden += 1;
        }
    }

    std.debug.print("pvs {s}: {d}x{d} cells, {d}% hidden pairs, {d:.1} s\n", .{ map_name, n, n, hidden * 100 / (n * n * n * n), rl.GetTime() - t0 });
}

pub fn load(map_name: []const u8) void {
    ready = false;

    if (std.c.getenv("DF_NOPVS") != null) return;

    var rel: [96]u8 = undefined;
    const sub = std.fmt.bufPrint(&rel, "pvs/{s}.bin", .{map_name}) catch return;
    var buf: [512]u8 = undefined;
    const path = assets.file(&buf, sub);

    if (!assets.exists(path)) return;

    var size: c_int = 0;
    const raw = rl.LoadFileData(path.ptr, &size) orelse return;

    defer rl.UnloadFileData(raw);

    const len: usize = @intCast(size);

    if (len < @sizeOf(Header)) return;

    const head = std.mem.bytesToValue(Header, raw[0..@sizeOf(Header)]);

    layout();

    if (head.magic != magic or head.n != n or head.pieces != world.pieces.len or head.hash != worldHash()) return;

    if (len != @sizeOf(Header) + n * n * words * 8) return;

    const gpa = std.heap.page_allocator;

    gpa.free(bits);
    bits = gpa.alloc(u64, n * n * words) catch return;
    @memcpy(std.mem.sliceAsBytes(bits), raw[@sizeOf(Header)..len]);
    ready = true;
}

pub fn visible(eye: Vec3, at: Vec3, radius: f32) bool {
    if (!ready) return true;

    if (eye.y > ground(eye.x, eye.z) + high_eye) return true;

    const from = index(eye.x, eye.z) orelse return true;
    const lo = index(at.x - radius, at.z - radius) orelse return true;
    const hi = index(at.x + radius, at.z + radius) orelse return true;

    for (lo / n..hi / n + 1) |z| {
        for (lo % n..hi % n + 1) |x| {
            const to = z * n + x;

            if (bits[from * words + to / 64] & (@as(u64, 1) << @intCast(to % 64)) != 0) return true;
        }
    }

    return false;
}
