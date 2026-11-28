const std = @import("std");
const map = @import("map.zig");
const geom = @import("geom.zig");
const Vec3 = @import("math.zig").Vec3;

const cell: f32 = 8;
const max_side: usize = 512;
const big_cells: usize = 96;
const cap: usize = 8192;

var built_ptr: usize = 0;
var built_len: usize = 0;
var usable = false;
var min_x: f32 = 0;
var min_z: f32 = 0;
var nx: usize = 0;
var nz: usize = 0;
var starts: []u32 = &.{};
var items: []u32 = &.{};
var big: []u32 = &.{};
var stamp: []u32 = &.{};
var query_id: u32 = 0;
var out: [cap]u32 = undefined;

const gpa = std.heap.page_allocator;

fn cellRange(lo: f32, hi: f32, origin: f32, n: usize) [2]usize {
    const a = @floor((lo - origin) / cell);
    const b = @floor((hi - origin) / cell);
    const last: f32 = @floatFromInt(n - 1);

    return .{ @intFromFloat(std.math.clamp(a, 0, last)), @intFromFloat(std.math.clamp(b, 0, last)) };
}

fn release() void {
    gpa.free(starts);
    gpa.free(items);
    gpa.free(big);
    gpa.free(stamp);
    starts = &.{};
    items = &.{};
    big = &.{};
    stamp = &.{};
}

pub fn reset() void {
    release();
    built_ptr = 0;
    built_len = 0;
    usable = false;
}

fn build(pieces: []const map.Piece) void {
    release();
    built_ptr = @intFromPtr(pieces.ptr);
    built_len = pieces.len;
    usable = false;

    if (pieces.len < 64) return;

    var lo_x: f32 = 1e9;
    var lo_z: f32 = 1e9;
    var hi_x: f32 = -1e9;
    var hi_z: f32 = -1e9;

    for (pieces) |p| {
        const b = p.shape.bounds();

        lo_x = @min(lo_x, b.min.x);
        lo_z = @min(lo_z, b.min.z);
        hi_x = @max(hi_x, b.max.x);
        hi_z = @max(hi_z, b.max.z);
    }

    min_x = lo_x;
    min_z = lo_z;
    nx = @min(max_side, @as(usize, @intFromFloat(@max(1, @ceil((hi_x - lo_x) / cell)))));
    nz = @min(max_side, @as(usize, @intFromFloat(@max(1, @ceil((hi_z - lo_z) / cell)))));

    const counts = gpa.alloc(u32, nx * nz + 1) catch return;

    @memset(counts, 0);

    var big_count: usize = 0;

    for (pieces) |p| {
        const b = p.shape.bounds();
        const rx = cellRange(b.min.x, b.max.x, min_x, nx);
        const rz = cellRange(b.min.z, b.max.z, min_z, nz);

        if ((rx[1] - rx[0] + 1) * (rz[1] - rz[0] + 1) > big_cells) {
            big_count += 1;

            continue;
        }

        for (rz[0]..rz[1] + 1) |z| {
            for (rx[0]..rx[1] + 1) |x| counts[z * nx + x + 1] += 1;
        }
    }

    for (1..counts.len) |i| counts[i] += counts[i - 1];

    items = gpa.alloc(u32, counts[counts.len - 1]) catch return gpa.free(counts);
    big = gpa.alloc(u32, big_count) catch return gpa.free(counts);
    stamp = gpa.alloc(u32, pieces.len) catch return gpa.free(counts);
    @memset(stamp, 0);
    starts = counts;

    const fill = gpa.alloc(u32, nx * nz) catch return;

    defer gpa.free(fill);
    @memcpy(fill, starts[0 .. nx * nz]);

    var bi: usize = 0;

    for (pieces, 0..) |p, i| {
        const b = p.shape.bounds();
        const rx = cellRange(b.min.x, b.max.x, min_x, nx);
        const rz = cellRange(b.min.z, b.max.z, min_z, nz);

        if ((rx[1] - rx[0] + 1) * (rz[1] - rz[0] + 1) > big_cells) {
            big[bi] = @intCast(i);
            bi += 1;

            continue;
        }

        for (rz[0]..rz[1] + 1) |z| {
            for (rx[0]..rx[1] + 1) |x| {
                items[fill[z * nx + x]] = @intCast(i);
                fill[z * nx + x] += 1;
            }
        }
    }

    usable = true;
}

fn ready(pieces: []const map.Piece) bool {
    if (@intFromPtr(pieces.ptr) != built_ptr or pieces.len != built_len) build(pieces);

    return usable;
}

const Gather = struct {
    n: usize = 0,
    full: bool = false,

    fn add(g: *Gather, i: u32) void {
        if (stamp[i] == query_id) return;

        if (g.n == cap) {
            g.full = true;

            return;
        }

        stamp[i] = query_id;
        out[g.n] = i;
        g.n += 1;
    }

    fn area(g: *Gather, lo_x: f32, lo_z: f32, hi_x: f32, hi_z: f32) void {
        const rx = cellRange(lo_x, hi_x, min_x, nx);
        const rz = cellRange(lo_z, hi_z, min_z, nz);

        for (rz[0]..rz[1] + 1) |z| {
            for (rx[0]..rx[1] + 1) |x| {
                const c = z * nx + x;

                for (items[starts[c]..starts[c + 1]]) |i| g.add(i);
            }
        }
    }
};

fn begin() Gather {
    query_id +%= 1;

    if (query_id == 0) {
        @memset(stamp, 0);
        query_id = 1;
    }

    var g: Gather = .{};

    for (big) |i| g.add(i);

    return g;
}

pub const Near = struct {
    pieces: []const map.Piece,
    idx: ?[]const u32,
    i: usize = 0,

    pub fn next(it: *Near) ?*const map.Piece {
        if (it.idx) |idx| {
            if (it.i >= idx.len) return null;

            defer it.i += 1;

            return &it.pieces[idx[it.i]];
        }

        if (it.i >= it.pieces.len) return null;

        defer it.i += 1;

        return &it.pieces[it.i];
    }
};

pub fn rect(pieces: []const map.Piece, f: geom.Rect) Near {
    if (!ready(pieces)) return .{ .pieces = pieces, .idx = null };

    var g = begin();

    g.area(f.min_x, f.min_z, f.max_x, f.max_z);

    if (g.full) return .{ .pieces = pieces, .idx = null };

    return .{ .pieces = pieces, .idx = out[0..g.n] };
}

pub fn ray(pieces: []const map.Piece, origin: Vec3, dir: Vec3, len: f32) Near {
    if (!ready(pieces) or !(len < 4000)) return .{ .pieces = pieces, .idx = null };

    var g = begin();
    const step: f32 = 24;
    var t: f32 = 0;

    while (t < len) : (t += step) {
        const a = origin.add(dir.scale(t));
        const b = origin.add(dir.scale(@min(len, t + step)));

        g.area(@min(a.x, b.x) - 0.5, @min(a.z, b.z) - 0.5, @max(a.x, b.x) + 0.5, @max(a.z, b.z) + 0.5);

        if (g.full) return .{ .pieces = pieces, .idx = null };
    }

    return .{ .pieces = pieces, .idx = out[0..g.n] };
}
