const std = @import("std");
const rl = @import("raylib");
const rlgl = @import("rlgl");
const assets = @import("assets.zig");

extern fn glGenTextures(n: c_int, ids: *c_uint) callconv(.c) void;
extern fn glBindTexture(target: c_uint, id: c_uint) callconv(.c) void;
extern fn glCompressedTexImage2D(target: c_uint, level: c_int, format: c_uint, w: c_int, h: c_int, border: c_int, size: c_int, data: ?*const anyopaque) callconv(.c) void;
extern fn glTexParameteri(target: c_uint, name: c_uint, value: c_int) callconv(.c) void;
extern fn glGetError() callconv(.c) c_uint;

const tex_2d: c_uint = 0x0DE1;

pub fn apply(model: rl.Model, path: []const u8) void {
    if (!assets.mobile or !std.mem.endsWith(u8, path, ".glb")) return;

    const stem = path[0 .. path.len - 4];

    for (1..@intCast(model.materialCount)) |j| {
        const map = &model.materials[j].maps[rl.MATERIAL_MAP_ALBEDO];

        if (map.texture.id <= 1) continue;

        var buf: [512]u8 = undefined;
        const file = std.fmt.bufPrintSentinel(&buf, "{s}.m{d}.etc", .{ stem, j }, 0) catch continue;

        if (!assets.exists(file)) continue;

        const texture = load(file) orelse continue;

        rl.UnloadTexture(map.texture);
        map.texture = texture;
    }
}

fn load(path: [:0]const u8) ?rl.Texture2D {
    var size: c_int = 0;
    const raw = rl.LoadFileData(path.ptr, &size) orelse return null;

    defer rl.UnloadFileData(raw);

    const data = raw[0..@intCast(size)];

    if (data.len < 10 or !std.mem.eql(u8, data[0..4], "DFE2")) return null;

    const w = std.mem.readInt(u16, data[4..6], .little);
    const h = std.mem.readInt(u16, data[6..8], .little);
    const mips = data[8];
    const alpha = data[9] != 0;
    const gl_format: c_uint = if (alpha) 0x9278 else 0x9274;
    var id: c_uint = 0;
    var at: usize = 10;
    var lw: c_int = w;
    var lh: c_int = h;

    while (glGetError() != 0) {}

    glGenTextures(1, &id);

    if (id == 0) return null;

    glBindTexture(tex_2d, id);

    for (0..mips) |level| {
        if (at + 4 > data.len) break;

        const n = std.mem.readInt(u32, data[at..][0..4], .little);

        if (at + 4 + n > data.len) break;

        glCompressedTexImage2D(tex_2d, @intCast(level), gl_format, lw, lh, 0, @intCast(n), data[at + 4 ..].ptr);
        at += 4 + n;
        lw = @max(4, @divTrunc(lw, 2));
        lh = @max(4, @divTrunc(lh, 2));
    }

    glTexParameteri(tex_2d, 0x813D, mips - 1);
    glBindTexture(tex_2d, 0);

    if (glGetError() != 0) {
        rlgl.rlUnloadTexture(id);

        return null;
    }

    const format: c_int = if (alpha) rl.PIXELFORMAT_COMPRESSED_ETC2_EAC_RGBA else rl.PIXELFORMAT_COMPRESSED_ETC2_RGB;
    const texture: rl.Texture2D = .{ .id = id, .width = w, .height = h, .mipmaps = mips, .format = format };

    rl.SetTextureFilter(texture, if (mips > 1) rl.TEXTURE_FILTER_TRILINEAR else rl.TEXTURE_FILTER_BILINEAR);

    return texture;
}
