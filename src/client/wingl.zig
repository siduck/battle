const std = @import("std");

extern "opengl32" fn wglGetProcAddress(name: [*:0]const u8) callconv(.winapi) ?*const anyopaque;

fn load(comptime name: [:0]const u8, comptime F: type) *const F {
    const slot = struct {
        var ptr: ?*const F = null;
    };

    if (slot.ptr == null) slot.ptr = @ptrCast(@alignCast(wglGetProcAddress(name) orelse std.debug.panic("missing GL function {s}", .{name})));

    return slot.ptr.?;
}

export fn glGenFramebuffers(n: c_int, ids: *c_uint) callconv(.c) void {
    load("glGenFramebuffers", fn (c_int, *c_uint) callconv(.c) void)(n, ids);
}

export fn glDeleteFramebuffers(n: c_int, ids: *const c_uint) callconv(.c) void {
    load("glDeleteFramebuffers", fn (c_int, *const c_uint) callconv(.c) void)(n, ids);
}

export fn glBindFramebuffer(target: c_uint, id: c_uint) callconv(.c) void {
    load("glBindFramebuffer", fn (c_uint, c_uint) callconv(.c) void)(target, id);
}

export fn glGenRenderbuffers(n: c_int, ids: *c_uint) callconv(.c) void {
    load("glGenRenderbuffers", fn (c_int, *c_uint) callconv(.c) void)(n, ids);
}

export fn glDeleteRenderbuffers(n: c_int, ids: *const c_uint) callconv(.c) void {
    load("glDeleteRenderbuffers", fn (c_int, *const c_uint) callconv(.c) void)(n, ids);
}

export fn glBindRenderbuffer(target: c_uint, id: c_uint) callconv(.c) void {
    load("glBindRenderbuffer", fn (c_uint, c_uint) callconv(.c) void)(target, id);
}

export fn glRenderbufferStorageMultisample(target: c_uint, samples: c_int, format: c_uint, w: c_int, h: c_int) callconv(.c) void {
    load("glRenderbufferStorageMultisample", fn (c_uint, c_int, c_uint, c_int, c_int) callconv(.c) void)(target, samples, format, w, h);
}

export fn glFramebufferRenderbuffer(target: c_uint, attachment: c_uint, rb_target: c_uint, rb: c_uint) callconv(.c) void {
    load("glFramebufferRenderbuffer", fn (c_uint, c_uint, c_uint, c_uint) callconv(.c) void)(target, attachment, rb_target, rb);
}

export fn glUniformMatrix4fv(location: c_int, count: c_int, transpose: u8, value: [*]const f32) callconv(.c) void {
    load("glUniformMatrix4fv", fn (c_int, c_int, u8, [*]const f32) callconv(.c) void)(location, count, transpose, value);
}

export fn glBlitFramebuffer(sx0: c_int, sy0: c_int, sx1: c_int, sy1: c_int, dx0: c_int, dy0: c_int, dx1: c_int, dy1: c_int, mask: c_uint, filt: c_uint) callconv(.c) void {
    load("glBlitFramebuffer", fn (c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_uint, c_uint) callconv(.c) void)(sx0, sy0, sx1, sy1, dx0, dy0, dx1, dy1, mask, filt);
}

export fn glCheckFramebufferStatus(target: c_uint) callconv(.c) c_uint {
    return load("glCheckFramebufferStatus", fn (c_uint) callconv(.c) c_uint)(target);
}

export fn glFramebufferTexture2D(target: c_uint, attachment: c_uint, tex_target: c_uint, tex: c_uint, level: c_int) callconv(.c) void {
    load("glFramebufferTexture2D", fn (c_uint, c_uint, c_uint, c_uint, c_int) callconv(.c) void)(target, attachment, tex_target, tex, level);
}
