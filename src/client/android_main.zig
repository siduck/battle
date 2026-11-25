const std = @import("std");
const game = @import("main.zig");

const File = opaque {};
const Open = *const fn ([*:0]const u8, [*:0]const u8) callconv(.c) ?*File;

extern fn __wrap_fopen(name: [*:0]const u8, mode: [*:0]const u8) ?*File;
extern fn dlsym(handle: ?*anyopaque, name: [*:0]const u8) ?*anyopaque;

const rtld_next: ?*anyopaque = @ptrFromInt(std.math.maxInt(usize));

var real_open: ?Open = null;

export fn fopen(name: [*:0]const u8, mode: [*:0]const u8) ?*File {
    return __wrap_fopen(name, mode);
}

export fn __real_fopen(name: [*:0]const u8, mode: [*:0]const u8) ?*File {
    if (real_open == null) real_open = @ptrCast(@alignCast(dlsym(rtld_next, "fopen") orelse return null));

    return real_open.?(name, mode);
}

export fn main(argc: c_int, argv: ?[*]?[*:0]u8) c_int {
    _ = argc;
    _ = argv;

    game.main();

    return 0;
}
