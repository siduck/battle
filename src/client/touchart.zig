const std = @import("std");
const rl = @import("raylib");

pub const Icon = enum { fire, aim, jump, brake, boost, reload, swap, grenade, enter, exit, pickup, missile, pause, board, sprint };

const Shape = union(enum) {
    disc: i32,
    ring: struct { half: i32, thick: i32 },
    icon: struct { kind: Icon, size: i32 },
};

const Entry = struct {
    key: u64,
    x: i32,
    y: i32,
    w: i32,
    h: i32,
};

const wide = 2048;
const tall = 1024;
const gap = 2;
const spill = 3;

var texture: rl.Texture2D = std.mem.zeroes(rl.Texture2D);
var entries: [128]Entry = undefined;
var used: usize = 0;
var cursor_x: i32 = gap;
var cursor_y: i32 = gap;
var shelf: i32 = 0;
var built_for: f32 = 0;

pub fn prepare(unit: f32) void {
    if (texture.id != 0 and unit == built_for) return;

    built_for = unit;
    clear();
}

fn clear() void {
    const bytes = std.heap.page_allocator.alloc(u8, wide * tall * 2) catch return;
    defer std.heap.page_allocator.free(bytes);

    blank(bytes);

    if (texture.id == 0) {
        const image: rl.Image = .{ .data = bytes.ptr, .width = wide, .height = tall, .mipmaps = 1, .format = rl.PIXELFORMAT_UNCOMPRESSED_GRAY_ALPHA };

        texture = rl.LoadTextureFromImage(image);
        rl.SetTextureFilter(texture, rl.TEXTURE_FILTER_BILINEAR);
    } else {
        rl.UpdateTexture(texture, bytes.ptr);
    }

    used = 0;
    cursor_x = gap;
    cursor_y = gap;
    shelf = 0;
}

fn blank(bytes: []u8) void {
    var i: usize = 0;

    while (i < bytes.len) : (i += 2) {
        bytes[i] = 255;
        bytes[i + 1] = 0;
    }
}

fn keyOf(shape: Shape) u64 {
    return switch (shape) {
        .disc => |half| (1 << 40) | @as(u64, @intCast(half)),
        .ring => |r| (2 << 40) | (@as(u64, @intCast(r.thick)) << 20) | @as(u64, @intCast(r.half)),
        .icon => |i| (3 << 40) | (@as(u64, @intFromEnum(i.kind)) << 20) | @as(u64, @intCast(i.size)),
    };
}

fn find(shape: Shape) ?Entry {
    const key = keyOf(shape);

    for (entries[0..used]) |e| {
        if (e.key == key) return e;
    }

    return add(shape, key);
}

fn add(shape: Shape, key: u64) ?Entry {
    const wanted: i32 = switch (shape) {
        .disc => |half| half + spill,
        .ring => |r| r.half + spill,
        .icon => |i| i.size,
    };
    const w = wanted + @mod(wanted, 2);

    if (w <= 0 or w + gap * 2 > tall or used >= entries.len) return null;

    if (cursor_x + w + gap > wide) {
        cursor_x = gap;
        cursor_y += shelf + gap;
        shelf = 0;
    }

    if (cursor_y + w + gap > tall) return null;

    const n: usize = @intCast(w);
    const bytes = std.heap.page_allocator.alloc(u8, n * n * 2) catch return null;
    defer std.heap.page_allocator.free(bytes);

    for (0..n) |row| {
        for (0..n) |col| {
            const x = @as(f32, @floatFromInt(col)) + 0.5;
            const y = @as(f32, @floatFromInt(row)) + 0.5;
            const at = (row * n + col) * 2;

            bytes[at] = 255;
            bytes[at + 1] = @intFromFloat(@round(coverage(shape, x, y) * 255));
        }
    }

    const e: Entry = .{ .key = key, .x = cursor_x, .y = cursor_y, .w = w, .h = w };

    rl.UpdateTextureRec(texture, .{ .x = @floatFromInt(e.x), .y = @floatFromInt(e.y), .width = @floatFromInt(w), .height = @floatFromInt(w) }, bytes.ptr);
    entries[used] = e;
    used += 1;
    cursor_x += w + gap;
    shelf = @max(shelf, w);

    return e;
}

fn coverage(shape: Shape, x: f32, y: f32) f32 {
    const d = switch (shape) {
        .disc => |half| blk: {
            const r: f32 = @floatFromInt(half);

            break :blk length(x - r, y - r) - r;
        },
        .ring => |ring_| blk: {
            const r: f32 = @floatFromInt(ring_.half);
            const t: f32 = @floatFromInt(ring_.thick);

            break :blk @abs(length(x - r, y - r) - (r - t / 2)) - t / 2;
        },
        .icon => |i| blk: {
            const k = @as(f32, @floatFromInt(i.size)) / 2;

            break :blk glyph(i.kind, .{ x / k - 1, y / k - 1 }) * k;
        },
    };

    return std.math.clamp(0.5 - d, 0, 1);
}

fn quads(e: Entry, half: i32, x: f32, y: f32, scale: f32, color: rl.Color) void {
    const h: f32 = @floatFromInt(half);
    const r = h * scale;
    const sx: f32 = @floatFromInt(e.x);
    const sy: f32 = @floatFromInt(e.y);

    rl.DrawTexturePro(texture, .{ .x = sx, .y = sy, .width = h, .height = h }, .{ .x = x - r, .y = y - r, .width = r, .height = r }, .{}, 0, color);
    rl.DrawTexturePro(texture, .{ .x = sx, .y = sy, .width = -h, .height = h }, .{ .x = x, .y = y - r, .width = r, .height = r }, .{}, 0, color);
    rl.DrawTexturePro(texture, .{ .x = sx, .y = sy, .width = h, .height = -h }, .{ .x = x - r, .y = y, .width = r, .height = r }, .{}, 0, color);
    rl.DrawTexturePro(texture, .{ .x = sx, .y = sy, .width = -h, .height = -h }, .{ .x = x, .y = y, .width = r, .height = r }, .{}, 0, color);
}

pub fn disc(x: f32, y: f32, radius: f32, scale: f32, color: rl.Color) void {
    const half: i32 = @intFromFloat(@round(radius));
    const e = find(.{ .disc = half }) orelse return;

    quads(e, half, x, y, scale, color);
}

pub fn ring(x: f32, y: f32, radius: f32, thick: f32, scale: f32, color: rl.Color) void {
    const half: i32 = @intFromFloat(@round(radius));
    const e = find(.{ .ring = .{ .half = half, .thick = @intFromFloat(@max(2, @round(thick))) } }) orelse return;

    quads(e, half, x, y, scale, color);
}

pub fn icon(kind: Icon, x: f32, y: f32, size: f32, scale: f32, color: rl.Color) void {
    const px: i32 = @intFromFloat(@round(size / 2) * 2);
    const e = find(.{ .icon = .{ .kind = kind, .size = px } }) orelse return;
    const w: f32 = @floatFromInt(e.w);
    const s = w * scale;
    const src: rl.Rectangle = .{ .x = @floatFromInt(e.x), .y = @floatFromInt(e.y), .width = w, .height = w };

    rl.DrawTexturePro(texture, src, .{ .x = x - s / 2, .y = y - s / 2, .width = s, .height = s }, .{}, 0, color);
}

const P = [2]f32;

fn length(x: f32, y: f32) f32 {
    return @sqrt(x * x + y * y);
}

fn circle(p: P, cx: f32, cy: f32, r: f32) f32 {
    return length(p[0] - cx, p[1] - cy) - r;
}

fn hoop(p: P, cx: f32, cy: f32, r: f32, t: f32) f32 {
    return @abs(circle(p, cx, cy, r)) - t / 2;
}

fn line(p: P, a: P, b: P, t: f32) f32 {
    const px = p[0] - a[0];
    const py = p[1] - a[1];
    const bx = b[0] - a[0];
    const by = b[1] - a[1];
    const h = std.math.clamp((px * bx + py * by) / (bx * bx + by * by), 0, 1);

    return length(px - bx * h, py - by * h) - t / 2;
}

fn path(p: P, points: []const P, t: f32) f32 {
    var d: f32 = 1e9;

    for (points[1..], 0..) |b, i| d = @min(d, line(p, points[i], b, t));

    return d;
}

fn box(p: P, cx: f32, cy: f32, hx: f32, hy: f32, r: f32) f32 {
    const qx = @abs(p[0] - cx) - hx + r;
    const qy = @abs(p[1] - cy) - hy + r;

    return length(@max(qx, 0), @max(qy, 0)) + @min(@max(qx, qy), 0) - r;
}

fn poly(p: P, points: []const P) f32 {
    var d: f32 = 1e9;
    var sign: f32 = 1;
    var j = points.len - 1;

    for (points, 0..) |a, i| {
        const b = points[j];
        const ex = b[0] - a[0];
        const ey = b[1] - a[1];
        const wx = p[0] - a[0];
        const wy = p[1] - a[1];
        const h = std.math.clamp((wx * ex + wy * ey) / (ex * ex + ey * ey), 0, 1);
        const dx = wx - ex * h;
        const dy = wy - ey * h;
        const above = p[1] >= a[1];
        const below = p[1] < b[1];
        const left = ex * wy > ey * wx;

        d = @min(d, dx * dx + dy * dy);

        if ((above and below and left) or (!above and !below and !left)) sign = -sign;

        j = i;
    }

    return sign * @sqrt(d);
}

fn sweep(p: P, r: f32, t: f32, from: f32, span: f32) f32 {
    const turn = std.math.tau;
    const angle = @mod(std.math.atan2(p[1], p[0]) - from, turn);

    if (angle <= span) return hoop(p, 0, 0, r, t);

    const a = circle(p, @cos(from) * r, @sin(from) * r, t / 2);
    const b = circle(p, @cos(from + span) * r, @sin(from + span) * r, t / 2);

    return @min(a, b);
}

fn turned(p: P, angle: f32) P {
    const c = @cos(angle);
    const s = @sin(angle);

    return .{ p[0] * c + p[1] * s, -p[0] * s + p[1] * c };
}

fn cartridge(p: P) f32 {
    const tip = poly(p, &.{ .{ -0.29, -0.2 }, .{ -0.25, -0.5 }, .{ -0.15, -0.74 }, .{ 0, -0.92 }, .{ 0.15, -0.74 }, .{ 0.25, -0.5 }, .{ 0.29, -0.2 } });
    const case = box(p, 0, 0.24, 0.29, 0.32, 0.04);
    const rim = box(p, 0, 0.77, 0.33, 0.11, 0.05);
    const groove = box(p, 0, -0.14, 0.5, 0.045, 0);

    return @min(@max(@min(tip, case), -groove), rim);
}

fn glyph(kind: Icon, p: P) f32 {
    const x = p[0];
    const y = p[1];

    switch (kind) {
        .fire => return cartridge(turned(p, std.math.pi * 0.25)),
        .aim => {
            const a: P = .{ @abs(x), @abs(y) };
            const ticks = @min(box(a, 0.68, 0, 0.27, 0.075, 0.07), box(a, 0, 0.68, 0.075, 0.27, 0.07));

            return @min(@min(hoop(p, 0, 0, 0.62, 0.14), ticks), circle(p, 0, 0, 0.12));
        },
        .jump => {
            const arrow = @min(line(p, .{ 0, 0.18 }, .{ 0, -0.56 }, 0.22), path(p, &.{ .{ -0.46, -0.22 }, .{ 0, -0.68 }, .{ 0.46, -0.22 } }, 0.22));

            return @min(arrow, line(p, .{ -0.5, 0.62 }, .{ 0.5, 0.62 }, 0.22));
        },
        .brake => {
            const left = sweep(p, 0.88, 0.14, std.math.pi * 0.8, std.math.pi * 0.4);
            const right = sweep(p, 0.88, 0.14, -std.math.pi * 0.2, std.math.pi * 0.4);
            const mark = @min(line(p, .{ 0, -0.24 }, .{ 0, 0.07 }, 0.17), circle(p, 0, 0.29, 0.1));

            return @min(@min(hoop(p, 0, 0, 0.57, 0.15), mark), @min(left, right));
        },
        .boost => return poly(p, &.{ .{ 0.16, -0.94 }, .{ -0.56, 0.14 }, .{ -0.08, 0.14 }, .{ -0.16, 0.94 }, .{ 0.56, -0.16 }, .{ 0.08, -0.16 } }) - 0.02,
        .reload => {
            const from = -std.math.pi / 9.0;
            const span = std.math.pi * 1.52;
            const end = from + span;
            const at: P = .{ @cos(end) * 0.72, @sin(end) * 0.72 };
            const along: P = .{ -@sin(end), @cos(end) };
            const out: P = .{ @cos(end), @sin(end) };
            const head = poly(p, &.{
                .{ at[0] + along[0] * 0.4, at[1] + along[1] * 0.4 },
                .{ at[0] + out[0] * 0.26, at[1] + out[1] * 0.26 },
                .{ at[0] - out[0] * 0.26, at[1] - out[1] * 0.26 },
            });
            const round = cartridge(.{ x / 0.46, (y - 0.02) / 0.46 }) * 0.46;

            return @min(@min(sweep(p, 0.72, 0.16, from, span), head), round);
        },
        .swap => {
            const top = @min(line(p, .{ -0.68, -0.38 }, .{ 0.38, -0.38 }, 0.2), poly(p, &.{ .{ 0.86, -0.38 }, .{ 0.3, -0.74 }, .{ 0.3, -0.02 } }));
            const bottom = @min(line(p, .{ 0.68, 0.38 }, .{ -0.38, 0.38 }, 0.2), poly(p, &.{ .{ -0.86, 0.38 }, .{ -0.3, 0.02 }, .{ -0.3, 0.74 } }));

            return @min(top, bottom);
        },
        .grenade => {
            const body = box(p, -0.04, 0.3, 0.5, 0.6, 0.46);
            const bands = @min(box(p, -0.04, 0.28, 0.7, 0.045, 0), box(p, -0.04, 0.34, 0.045, 0.7, 0));
            const cut = @max(body, -bands);
            const cap = box(p, -0.04, -0.46, 0.26, 0.14, 0.04);
            const lever = path(p, &.{ .{ 0.12, -0.66 }, .{ 0.44, -0.58 }, .{ 0.66, -0.16 } }, 0.17);
            const pin = hoop(p, -0.48, -0.68, 0.19, 0.1);

            return @min(@min(cut, cap), @min(lever, pin));
        },
        .enter => {
            const frame = path(p, &.{ .{ 0.14, -0.72 }, .{ 0.68, -0.72 }, .{ 0.68, 0.72 }, .{ 0.14, 0.72 } }, 0.17);
            const arrow = @min(line(p, .{ -0.76, 0 }, .{ -0.14, 0 }, 0.2), poly(p, &.{ .{ 0.34, 0 }, .{ -0.18, -0.44 }, .{ -0.18, 0.44 } }));

            return @min(frame, arrow);
        },
        .exit => {
            const frame = path(p, &.{ .{ -0.14, -0.72 }, .{ -0.68, -0.72 }, .{ -0.68, 0.72 }, .{ -0.14, 0.72 } }, 0.17);
            const arrow = @min(line(p, .{ -0.24, 0 }, .{ 0.38, 0 }, 0.2), poly(p, &.{ .{ 0.86, 0 }, .{ 0.34, -0.44 }, .{ 0.34, 0.44 } }));

            return @min(frame, arrow);
        },
        .pickup => {
            const arrow = @min(line(p, .{ 0, -0.72 }, .{ 0, -0.2 }, 0.22), poly(p, &.{ .{ 0, 0.34 }, .{ -0.46, -0.2 }, .{ 0.46, -0.2 } }));
            const tray = path(p, &.{ .{ -0.7, 0.3 }, .{ -0.7, 0.7 }, .{ 0.7, 0.7 }, .{ 0.7, 0.3 } }, 0.18);

            return @min(arrow, tray);
        },
        .missile => {
            const q = turned(p, std.math.pi * 0.25);
            const hull = box(q, 0, 0.04, 0.23, 0.46, 0.03);
            const nose = poly(q, &.{ .{ -0.23, -0.38 }, .{ -0.15, -0.68 }, .{ 0, -0.92 }, .{ 0.15, -0.68 }, .{ 0.23, -0.38 } });
            const fins = poly(.{ @abs(q[0]), q[1] }, &.{ .{ 0.18, 0.16 }, .{ 0.42, 0.42 }, .{ 0.42, 0.66 }, .{ 0.18, 0.52 } });
            const flame = line(q, .{ 0, 0.68 }, .{ 0, 0.88 }, 0.17);

            return @min(@min(hull, nose), @min(fins, flame));
        },
        .pause => return box(.{ @abs(x), y }, 0.34, 0, 0.17, 0.66, 0.09),
        .board => {
            var d: f32 = 1e9;

            for ([_]f32{ -0.52, 0, 0.52 }) |row| d = @min(d, @min(circle(p, -0.64, row, 0.13), line(p, .{ -0.24, row }, .{ 0.66, row }, 0.19)));

            return d;
        },
        .sprint => return @min(path(p, &.{ .{ -0.56, -0.08 }, .{ 0, -0.62 }, .{ 0.56, -0.08 } }, 0.2), path(p, &.{ .{ -0.56, 0.52 }, .{ 0, -0.02 }, .{ 0.56, 0.52 } }, 0.2)),
    }
}
