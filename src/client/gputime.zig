const std = @import("std");
const rl = @import("raylib");
const rlgl = @import("rlgl");
const assets = @import("assets.zig");

const timestamp: c_uint = 0x8E28;
const result: c_uint = 0x8866;
const available: c_uint = 0x8867;
const marks = 3;
const depth = 4;

const GenQueries = *const fn (c_int, [*]c_uint) callconv(.c) void;
const QueryCounter = *const fn (c_uint, c_uint) callconv(.c) void;
const GetQueryiv = *const fn (c_uint, c_uint, *c_int) callconv(.c) void;
const GetQueryu64v = *const fn (c_uint, c_uint, *u64) callconv(.c) void;

extern fn eglGetProcAddress(name: [*:0]const u8) ?*const anyopaque;

var gen: ?GenQueries = null;
var counter: ?QueryCounter = null;
var get_iv: ?GetQueryiv = null;
var get_u64: ?GetQueryu64v = null;
var ids: [depth][marks]c_uint = undefined;
var used: [depth]bool = @splat(false);
var frame: usize = 0;
var tried = false;
var sums: [marks - 1]f64 = @splat(0);
var count: f64 = 0;
var since: f64 = 0;

fn load() bool {
    if (tried) return counter != null;

    tried = true;

    if (!assets.mobile) return false;

    gen = @ptrCast(@alignCast(eglGetProcAddress("glGenQueriesEXT") orelse return false));
    counter = @ptrCast(@alignCast(eglGetProcAddress("glQueryCounterEXT") orelse return false));
    get_iv = @ptrCast(@alignCast(eglGetProcAddress("glGetQueryObjectivEXT") orelse return false));
    get_u64 = @ptrCast(@alignCast(eglGetProcAddress("glGetQueryObjectui64vEXT") orelse return false));

    for (&ids) |*row| gen.?(marks, row);

    return true;
}

pub fn mark(slot: usize) void {
    if (!load()) return;

    rlgl.rlDrawRenderBatchActive();
    counter.?(ids[frame % depth][slot], timestamp);

    if (slot == marks - 1) used[frame % depth] = true;
}

pub fn endFrame() void {
    if (!load()) return;

    frame += 1;

    const old = frame % depth;

    if (!used[old]) return;

    var ready: c_int = 0;

    get_iv.?(ids[old][marks - 1], available, &ready);

    if (ready == 0) return;

    var t: [marks]u64 = undefined;

    for (0..marks) |i| get_u64.?(ids[old][i], result, &t[i]);

    used[old] = false;

    for (0..marks - 1) |i| sums[i] += @as(f64, @floatFromInt(t[i + 1] -% t[i])) / 1e6;

    count += 1;

    const now = rl.GetTime();

    if (now - since < 2) return;

    since = now;

    var buf: [128]u8 = undefined;
    const line = std.fmt.bufPrintSentinel(&buf, "gpu scene {d:.2} ms final {d:.2} ms", .{ sums[0] / count, sums[1] / count }, 0) catch return;

    rl.TraceLog(rl.LOG_INFO, "%s", line.ptr);
    sums = @splat(0);
    count = 0;
}
