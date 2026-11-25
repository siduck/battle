const rl = @import("raylib");

pub fn rgba(r: u8, g: u8, b: u8, a: u8) rl.Color {
    return .{ .r = r, .g = g, .b = b, .a = a };
}

pub const white = rgba(244, 246, 250, 255);
pub const ink = rgba(12, 15, 22, 255);
pub const panel = rgba(14, 17, 26, 178);
pub const edge = rgba(255, 255, 255, 26);
pub const dim = rgba(170, 178, 196, 255);
pub const red = rgba(240, 92, 86, 255);
pub const green = rgba(110, 206, 138, 255);
pub const blue = rgba(96, 160, 248, 255);
pub const orange = rgba(244, 152, 70, 255);
pub const yellow = rgba(250, 200, 80, 255);
pub const purple = rgba(176, 128, 248, 255);
pub const gray = rgba(186, 192, 208, 255);
pub const accent = yellow;

pub const rarity = [_]rl.Color{ gray, green, blue, purple, yellow };

pub fn fade(c: rl.Color, alpha: f32) rl.Color {
    return .{ .r = c.r, .g = c.g, .b = c.b, .a = @intFromFloat(@as(f32, @floatFromInt(c.a)) * @min(1, @max(0, alpha))) };
}

pub fn v2(x: f32, y: f32) rl.Vector2 {
    return .{ .x = x, .y = y };
}

pub fn width(font: rl.Font, str: [:0]const u8, size: f32) f32 {
    return rl.MeasureTextEx(font, str.ptr, size, size * 0.02).x;
}

pub fn text(font: rl.Font, str: [:0]const u8, x: f32, y: f32, size: f32, color: rl.Color) void {
    const off = @max(1, size * 0.035);
    const alpha = @as(f32, @floatFromInt(color.a)) / 255;

    rl.DrawTextEx(font, str.ptr, v2(x, y + off), size, size * 0.02, fade(ink, alpha * 0.4));
    rl.DrawTextEx(font, str.ptr, v2(x, y), size, size * 0.02, color);
}

pub fn outlined(font: rl.Font, str: [:0]const u8, x: f32, y: f32, size: f32, color: rl.Color) void {
    const alpha = @as(f32, @floatFromInt(color.a)) / 255;
    const off = @max(1.5, size * 0.03);

    rl.DrawTextEx(font, str.ptr, v2(x, y + off * 1.5), size, size * 0.02, fade(ink, alpha * 0.35));
    rl.DrawTextEx(font, str.ptr, v2(x, y + off * 0.6), size, size * 0.02, fade(ink, alpha * 0.4));
    rl.DrawTextEx(font, str.ptr, v2(x, y), size, size * 0.02, color);
}

pub fn capsWidth(font: rl.Font, str: [:0]const u8, size: f32) f32 {
    return rl.MeasureTextEx(font, str.ptr, size, size * 0.14).x;
}

pub fn caps(font: rl.Font, str: [:0]const u8, x: f32, y: f32, size: f32, color: rl.Color) void {
    rl.DrawTextEx(font, str.ptr, v2(x, y), size, size * 0.14, color);
}

pub fn box(x: f32, y: f32, w: f32, h: f32, color: rl.Color) void {
    const r = @min(1, 10 / @max(1, @min(w, h)));

    rl.DrawRectangleRounded(.{ .x = x, .y = y, .width = w, .height = h }, r, 8, color);
}

pub fn card(x: f32, y: f32, w: f32, h: f32, alpha: f32) void {
    const r = @min(1, 10 / @max(1, @min(w, h)));
    const rect: rl.Rectangle = .{ .x = x, .y = y, .width = w, .height = h };

    rl.DrawRectangleRounded(rect, r, 8, fade(panel, alpha));
    rl.DrawRectangleRoundedLinesEx(rect, r, 8, 1, fade(edge, alpha));
}

pub fn keycap(font: rl.Font, key: [:0]const u8, x: f32, y: f32, size: f32, alpha: f32) f32 {
    const tw = width(font, key, size);
    const w = @max(size * 1.4, tw + size * 0.8);
    const h = size * 1.4;

    rl.DrawRectangleRounded(.{ .x = x, .y = y, .width = w, .height = h }, 0.3, 6, fade(white, 0.12 * alpha));
    rl.DrawRectangleRoundedLinesEx(.{ .x = x, .y = y, .width = w, .height = h }, 0.3, 6, 1, fade(white, 0.28 * alpha));
    rl.DrawTextEx(font, key.ptr, v2(x + (w - tw) / 2, y + size * 0.2), size, size * 0.02, fade(white, 0.92 * alpha));

    return w;
}

pub fn bar(x: f32, y: f32, w: f32, h: f32, frac: f32, color: rl.Color) void {
    rl.DrawRectangleRounded(.{ .x = x, .y = y, .width = w, .height = h }, 1, 8, fade(white, 0.14));

    if (frac > 0.01) rl.DrawRectangleRounded(.{ .x = x, .y = y, .width = @max(h, w * frac), .height = h }, 1, 8, color);
}
