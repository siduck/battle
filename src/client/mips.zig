const std = @import("std");
const rl = @import("raylib");
const assets = @import("assets.zig");

fn channels(format: c_int) usize {
    return switch (format) {
        rl.PIXELFORMAT_UNCOMPRESSED_GRAYSCALE => 1,
        rl.PIXELFORMAT_UNCOMPRESSED_GRAY_ALPHA => 2,
        rl.PIXELFORMAT_UNCOMPRESSED_R8G8B8 => 3,
        rl.PIXELFORMAT_UNCOMPRESSED_R8G8B8A8 => 4,
        else => 0,
    };
}

pub fn upload(image: rl.Image) rl.Texture2D {
    const n = channels(image.format);

    if (!assets.mobile or n == 0) {
        var texture = rl.LoadTextureFromImage(image);

        if (texture.id != 0) rl.GenTextureMipmaps(&texture);

        return texture;
    }

    var w: usize = @intCast(image.width);
    var h: usize = @intCast(image.height);
    var total: usize = w * h * n;
    var levels: c_int = 1;

    while (w > 1 or h > 1) : (levels += 1) {
        w = @max(1, w / 2);
        h = @max(1, h / 2);
        total += w * h * n;
    }

    const gpa = std.heap.page_allocator;
    const chain = gpa.alloc(u8, total) catch return rl.LoadTextureFromImage(image);

    defer gpa.free(chain);

    w = @intCast(image.width);
    h = @intCast(image.height);
    @memcpy(chain[0 .. w * h * n], @as([*]const u8, @ptrCast(image.data))[0 .. w * h * n]);

    var from: usize = 0;

    while (w > 1 or h > 1) {
        const nw = @max(1, w / 2);
        const nh = @max(1, h / 2);
        const to = from + w * h * n;

        for (0..nh) |y| {
            const top = from + @min(y * 2, h - 1) * w * n;
            const low = from + @min(y * 2 + 1, h - 1) * w * n;

            for (0..nw) |x| {
                const left = @min(x * 2, w - 1) * n;
                const right = @min(x * 2 + 1, w - 1) * n;

                for (0..n) |c| {
                    const sum = @as(u32, chain[top + left + c]) + chain[top + right + c] + chain[low + left + c] + chain[low + right + c];

                    chain[to + (y * nw + x) * n + c] = @intCast((sum + 2) / 4);
                }
            }
        }

        from = to;
        w = nw;
        h = nh;
    }

    var full = image;

    full.data = chain.ptr;
    full.mipmaps = levels;

    return rl.LoadTextureFromImage(full);
}

pub fn load(path: [*c]const u8) rl.Texture2D {
    const image = rl.LoadImage(path);

    if (image.data == null) return std.mem.zeroes(rl.Texture2D);

    defer rl.UnloadImage(image);

    return upload(image);
}

pub fn font(data: []const u8, px: c_int, points: [*c]c_int, count: c_int) rl.Font {
    if (!assets.mobile) {
        var out = rl.LoadFontFromMemory(".ttf", data.ptr, @intCast(data.len), px, points, count);

        rl.GenTextureMipmaps(&out.texture);

        return out;
    }

    var out = std.mem.zeroes(rl.Font);

    out.baseSize = px;
    out.glyphPadding = 4;
    out.glyphs = rl.LoadFontData(data.ptr, @intCast(data.len), px, points, if (count > 0) count else 95, rl.FONT_DEFAULT, &out.glyphCount);

    if (out.glyphs == null) return rl.GetFontDefault();

    const atlas = rl.GenImageFontAtlas(out.glyphs, &out.recs, out.glyphCount, px, out.glyphPadding, 0);

    defer rl.UnloadImage(atlas);

    out.texture = upload(atlas);

    return out;
}
