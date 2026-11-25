const std = @import("std");
const builtin = @import("builtin");
const rl = @import("raylib");

pub const mobile = builtin.abi.isAndroid();

const File = opaque {};

extern fn __wrap_fopen(name: [*:0]const u8, mode: [*:0]const u8) ?*File;
extern fn fclose(handle: *File) c_int;

pub fn dir(buf: []u8, sub: []const u8) []const u8 {
    if (mobile) return sub;

    const app = std.mem.span(rl.GetApplicationDirectory());

    return std.fmt.bufPrint(buf, "{s}../share/dronefire/{s}", .{ app, sub }) catch sub;
}

pub fn file(buf: []u8, sub: []const u8) [:0]const u8 {
    if (mobile) return std.fmt.bufPrintSentinel(buf, "{s}", .{sub}, 0) catch "";

    const app = std.mem.span(rl.GetApplicationDirectory());

    return std.fmt.bufPrintSentinel(buf, "{s}../share/dronefire/{s}", .{ app, sub }, 0) catch "";
}

pub fn exists(path: [:0]const u8) bool {
    if (!mobile) return rl.FileExists(path.ptr);

    const handle = __wrap_fopen(path.ptr, "rb") orelse return false;

    _ = fclose(handle);

    return true;
}
