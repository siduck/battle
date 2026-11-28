const std = @import("std");
const rl = @import("raylib");
const ui = @import("ui.zig");
const assets = @import("assets.zig");
const touch = @import("touch.zig");
const mips = @import("mips.zig");

const rgba = ui.rgba;
const v2 = ui.v2;

pub const navy = rgba(25, 42, 68, 255);
pub const night = rgba(13, 24, 42, 255);
const abyss = rgba(8, 34, 66, 255);
pub const slate = rgba(46, 66, 96, 255);
pub const cream = rgba(255, 244, 220, 255);
pub const sand = rgba(240, 220, 182, 255);
pub const dune = rgba(206, 172, 122, 255);
pub const soft = rgba(98, 100, 116, 255);
pub const coral = rgba(238, 92, 56, 255);
pub const rust = rgba(164, 50, 32, 255);
pub const sun = rgba(255, 194, 60, 255);
pub const amber = rgba(198, 126, 22, 255);
pub const teal = rgba(24, 146, 146, 255);
pub const deep = rgba(13, 90, 100, 255);
pub const leaf = rgba(86, 160, 82, 255);
pub const moss = rgba(48, 104, 56, 255);
pub const brick = rgba(206, 64, 52, 255);
pub const clay = rgba(138, 36, 34, 255);

pub const Tone = struct {
    face: rl.Color,
    edge: rl.Color,
    ink: rl.Color,
    ring: rl.Color,
};

pub const tones = struct {
    pub const coral_tone: Tone = .{ .face = coral, .edge = rust, .ink = cream, .ring = sun };
    pub const teal_tone: Tone = .{ .face = teal, .edge = deep, .ink = cream, .ring = sun };
    pub const cream_tone: Tone = .{ .face = cream, .edge = dune, .ink = navy, .ring = sun };
    pub const sun_tone: Tone = .{ .face = sun, .edge = amber, .ink = navy, .ring = cream };
    pub const sand_tone: Tone = .{ .face = sand, .edge = dune, .ink = navy, .ring = sun };
    pub const dim_tone: Tone = .{ .face = rgba(186, 178, 164, 255), .edge = rgba(132, 124, 114, 255), .ink = rgba(84, 82, 88, 255), .ring = sun };
    pub const navy_tone: Tone = .{ .face = slate, .edge = night, .ink = cream, .ring = sun };
};

const semi_data = @embedFile("assets/BarlowCondensed-SemiBold.ttf");
const bold_data = @embedFile("assets/BarlowCondensed-Bold.ttf");
const display_set = blk: {
    var set: [37]c_int = undefined;

    for ("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ", 0..) |ch, i| set[i] = ch;

    break :blk set;
};

const cell: usize = 128;
const sheet_cols: usize = 4;

pub const Icon = enum { play, signal, gear, exit, back, flag, join, pin, blaster, home, check, chevron };

const icon_count = @typeInfo(Icon).@"enum".field_names.len;
const sheet_rows = (icon_count + sheet_cols - 1) / sheet_cols;

pub var body: rl.Font = undefined;
pub var heavy: rl.Font = undefined;
var display: ?rl.Font = null;
var display_px: c_int = 0;
var disc: rl.Texture2D = undefined;
var hollow: rl.Texture2D = undefined;
var sheet: rl.Texture2D = undefined;
var ready = false;

fn load(data: []const u8, px: c_int, set: ?[]const c_int) rl.Font {
    const points: [*c]c_int = if (set) |s| @constCast(s.ptr) else null;
    const font = mips.font(data, px, points, if (set) |s| @intCast(s.len) else 0);

    rl.SetTextureFilter(font.texture, rl.TEXTURE_FILTER_TRILINEAR);

    return font;
}

fn upload(pixels: []u8, w: usize, h: usize) rl.Texture2D {
    const img: rl.Image = .{ .data = pixels.ptr, .width = @intCast(w), .height = @intCast(h), .mipmaps = 1, .format = rl.PIXELFORMAT_UNCOMPRESSED_R8G8B8A8 };
    const tex = mips.upload(img);

    rl.SetTextureFilter(tex, rl.TEXTURE_FILTER_TRILINEAR);
    rl.SetTextureWrap(tex, rl.TEXTURE_WRAP_CLAMP);

    return tex;
}

fn put(pixels: []u8, at: usize, cover: f32) void {
    pixels[at * 4] = 255;
    pixels[at * 4 + 1] = 255;
    pixels[at * 4 + 2] = 255;
    pixels[at * 4 + 3] = @intFromFloat(std.math.clamp(cover, 0, 1) * 255);
}

fn makeCorner(inverse: bool) rl.Texture2D {
    const n = 256;
    const gpa = std.heap.page_allocator;
    const pixels = gpa.alloc(u8, n * n * 4) catch return std.mem.zeroes(rl.Texture2D);

    defer gpa.free(pixels);

    for (0..n) |y| {
        for (0..n) |x| {
            const dx = @as(f32, @floatFromInt(x)) + 0.5 - n / 2;
            const dy = @as(f32, @floatFromInt(y)) + 0.5 - n / 2;
            const cover = std.math.clamp(@as(f32, n / 2) - @sqrt(dx * dx + dy * dy) + 0.5, 0, 1);

            put(pixels, y * n + x, if (inverse) 1 - cover else cover);
        }
    }

    return upload(pixels, n, n);
}

const P = struct { x: f32, y: f32 };

fn circle(p: P, cx: f32, cy: f32, r: f32) f32 {
    return @sqrt((p.x - cx) * (p.x - cx) + (p.y - cy) * (p.y - cy)) - r;
}

fn box(p: P, x0: f32, y0: f32, x1: f32, y1: f32, r: f32) f32 {
    const qx = @abs(p.x - (x0 + x1) / 2) - ((x1 - x0) / 2 - r);
    const qy = @abs(p.y - (y0 + y1) / 2) - ((y1 - y0) / 2 - r);
    const ox = @max(qx, 0);
    const oy = @max(qy, 0);

    return @sqrt(ox * ox + oy * oy) + @min(@max(qx, qy), 0) - r;
}

fn line(p: P, ax: f32, ay: f32, bx: f32, by: f32, half: f32) f32 {
    const dx = bx - ax;
    const dy = by - ay;
    const t = std.math.clamp(((p.x - ax) * dx + (p.y - ay) * dy) / (dx * dx + dy * dy), 0, 1);

    return circle(p, ax + dx * t, ay + dy * t, half);
}

fn poly(p: P, pts: []const [2]f32, bevel: f32) f32 {
    var d: f32 = 1e9;
    var inside = false;
    var j = pts.len - 1;

    for (pts, 0..) |a, i| {
        const b = pts[j];

        d = @min(d, line(p, a[0], a[1], b[0], b[1], 0));

        if ((a[1] > p.y) != (b[1] > p.y) and p.x < (b[0] - a[0]) * (p.y - a[1]) / (b[1] - a[1]) + a[0]) inside = !inside;

        j = i;
    }

    return (if (inside) -d else d) - bevel;
}

fn glyph(which: Icon, p: P) f32 {
    switch (which) {
        .play => return poly(p, &.{ .{ 42, 30 }, .{ 100, 64 }, .{ 42, 98 } }, 8),
        .signal => {
            var d = circle(p, 64, 96, 13);
            const dx = p.x - 64;
            const dy = p.y - 96;
            const r = @sqrt(dx * dx + dy * dy);
            const wedge = @abs(dx) * 0.7 + dy * 0.7;

            for ([_]f32{ 38, 68 }) |ring| {
                d = @min(d, @max(@abs(r - ring) - 8, wedge));
            }

            return d;
        },
        .gear => {
            const dx = p.x - 64;
            const dy = p.y - 64;
            var d = circle(p, 64, 64, 40);
            var k: f32 = 0;

            while (k < 8) : (k += 1) {
                const a = k * std.math.pi / 4;
                const q: P = .{ .x = dx * @cos(a) + dy * @sin(a), .y = -dx * @sin(a) + dy * @cos(a) };

                d = @min(d, box(q, 30, -11, 56, 11, 5));
            }

            return @max(d, -circle(p, 64, 64, 18));
        },
        .exit => {
            const frame = @max(box(p, 18, 18, 80, 110, 12), -box(p, 32, 32, 66, 96, 4));
            const gap = @max(frame, -box(p, 56, 44, 100, 84, 0));
            const shaft = line(p, 56, 64, 106, 64, 8);
            const head = @min(line(p, 108, 64, 88, 44, 8), line(p, 108, 64, 88, 84, 8));

            return @min(gap, @min(shaft, head));
        },
        .back => return @min(line(p, 40, 64, 76, 28, 11), line(p, 40, 64, 76, 100, 11)),
        .chevron => return @min(line(p, 88, 64, 52, 28, 11), line(p, 88, 64, 52, 100, 11)),
        .flag => {
            const pole = line(p, 32, 20, 32, 112, 8);
            const cloth = poly(p, &.{ .{ 40, 22 }, .{ 62, 18 }, .{ 82, 30 }, .{ 106, 24 }, .{ 106, 66 }, .{ 82, 74 }, .{ 62, 62 }, .{ 40, 68 } }, 3);

            return @min(pole, cloth);
        },
        .join => {
            const frame = @max(box(p, 48, 18, 110, 110, 12), -box(p, 62, 32, 96, 96, 4));
            const gap = @max(frame, -box(p, 28, 44, 70, 84, 0));
            const shaft = line(p, 18, 64, 74, 64, 8);
            const head = @min(line(p, 76, 64, 56, 44, 8), line(p, 76, 64, 56, 84, 8));

            return @min(gap, @min(shaft, head));
        },
        .pin => {
            const head = circle(p, 64, 50, 34);
            const tip = poly(p, &.{ .{ 35, 66 }, .{ 93, 66 }, .{ 64, 112 } }, 3);

            return @max(@min(head, tip), -circle(p, 64, 50, 13));
        },
        .blaster => {
            var d = box(p, 12, 44, 100, 68, 7);

            d = @min(d, box(p, 94, 49, 120, 59, 3));
            d = @min(d, poly(p, &.{ .{ 26, 66 }, .{ 46, 66 }, .{ 36, 98 }, .{ 18, 94 } }, 3));
            d = @min(d, poly(p, &.{ .{ 62, 66 }, .{ 80, 66 }, .{ 90, 92 }, .{ 74, 96 } }, 3));
            d = @min(d, box(p, 40, 30, 70, 40, 3));

            return d;
        },
        .home => {
            const roof = poly(p, &.{ .{ 64, 20 }, .{ 112, 62 }, .{ 16, 62 } }, 6);
            const walls = box(p, 30, 58, 98, 108, 6);

            return @max(@min(roof, walls), -box(p, 52, 76, 76, 116, 4));
        },
        .check => return @min(line(p, 28, 66, 52, 92, 11), line(p, 52, 92, 102, 38, 11)),
    }
}

fn makeSheet() rl.Texture2D {
    const w = cell * sheet_cols;
    const h = cell * sheet_rows;
    const gpa = std.heap.page_allocator;
    const pixels = gpa.alloc(u8, w * h * 4) catch return std.mem.zeroes(rl.Texture2D);

    defer gpa.free(pixels);

    for (0..h) |y| {
        for (0..w) |x| put(pixels, y * w + x, 0);
    }

    for (0..icon_count) |i| {
        const which: Icon = @fromBackingInt(@intCast(i));

        for (0..cell) |y| {
            for (0..cell) |x| {
                const d = glyph(which, .{ .x = @as(f32, @floatFromInt(x)) + 0.5, .y = @as(f32, @floatFromInt(y)) + 0.5 });
                const at = (i / sheet_cols * cell + y) * w + (i % sheet_cols) * cell + x;

                put(pixels, at, 0.5 - d);
            }
        }
    }

    return upload(pixels, w, h);
}

pub fn init() void {
    if (ready) return;

    ready = true;
    body = load(semi_data, 96, null);
    heavy = load(bold_data, 144, null);
    disc = makeCorner(false);
    hollow = makeCorner(true);
    sheet = makeSheet();
}

pub fn displayFont(px: f32) rl.Font {
    const want: c_int = @intFromFloat(std.math.clamp(@ceil(px), 64, 420));

    if (display) |f| {
        if (display_px >= want and display_px < want * 2) return f;

        rl.UnloadFont(f);
    }

    display = load(bold_data, want, &display_set);
    display_px = want;

    return display.?;
}

pub fn dropDisplay() void {
    if (display) |f| rl.UnloadFont(f);

    display = null;
    display_px = 0;
}

pub const View = struct {
    w: f32,
    h: f32,
    u: f32,
    left: f32,
    top: f32,
    right: f32,
    bottom: f32,
    mm: f32,
    touch: bool,

    pub fn tap(v: View, design: f32) f32 {
        return if (v.touch) @max(design * v.u, 9.2 * v.mm) else design * v.u;
    }

    pub fn width(v: View) f32 {
        return v.right - v.left;
    }

    pub fn height(v: View) f32 {
        return v.bottom - v.top;
    }

    pub fn cramped(v: View) bool {
        return v.touch and v.height() < 100 * v.mm;
    }

    pub fn keyed(v: View) bool {
        return !v.touch or pad_live;
    }

    pub fn cx(v: View) f32 {
        return (v.left + v.right) / 2;
    }
};

var forced_mm: ?f32 = null;
var forced_mobile: ?bool = null;

fn millimetre() f32 {
    if (forced_mm == null) forced_mm = if (std.c.getenv("DF_DPI")) |t| (std.fmt.parseFloat(f32, std.mem.sliceTo(t, 0)) catch 0) / 25.4 else 0;

    return if (forced_mm.? > 0) forced_mm.? else touch.pxPerMm();
}

fn handheld() bool {
    if (assets.mobile) return true;

    if (forced_mobile == null) forced_mobile = std.c.getenv("DF_MOBILE_UI") != null;

    return forced_mobile.?;
}

pub fn view() View {
    const w: f32 = @floatFromInt(rl.GetScreenWidth());
    const h: f32 = @floatFromInt(rl.GetScreenHeight());
    const mobile = handheld();
    const u = if (mobile) @min(h / 780, w / 1380) else @min(h / 900, w / 1440);
    const side = 52 * u;
    const edge = 34 * u;
    const in = insets;

    return .{
        .w = w,
        .h = h,
        .u = u,
        .left = @max(side, in[0] + 18 * u),
        .top = @max(edge, in[1] + 12 * u),
        .right = w - @max(side, in[2] + 18 * u),
        .bottom = h - @max(edge, in[3] + 12 * u),
        .mm = millimetre(),
        .touch = touch.active(),
    };
}

var insets: [4]f32 = @splat(0);
var inset_next: f64 = 0;

fn refreshInsets() void {
    if (!assets.mobile or rl.GetTime() < inset_next) return;

    inset_next = rl.GetTime() + 2;

    if (readInsets()) |in| insets = in;
}

pub fn bottomInset() f32 {
    refreshInsets();

    return insets[3];
}

const Callback = ?*const anyopaque;

const Focus = *const fn (*Activity, c_int) callconv(.c) void;

const Callbacks = extern struct {
    start: Callback,
    resumed: Callback,
    save: Callback,
    pause: Callback,
    stop: Callback,
    destroy: Callback,
    focus: ?Focus,
};

var previous_focus: ?Focus = null;

pub fn keepImmersive() void {
    if (!assets.mobile) return;

    const app: *App = @ptrCast(@alignCast(GetAndroidApp() orelse return));
    const activity = app.activity orelse return;
    const callbacks = activity.callbacks orelse return;

    previous_focus = callbacks.focus;
    callbacks.focus = onFocus;
}

fn onFocus(activity: *Activity, focused: c_int) callconv(.c) void {
    if (previous_focus) |next| next(activity, focused);

    if (focused != 0) hideSystemBars(activity);
}

fn hideSystemBars(activity: *Activity) void {
    const j: Java = .{ .env = @ptrCast(@alignCast(activity.env orelse return)) };
    const window = j.object(activity.clazz orelse return, "getWindow", "()Landroid/view/Window;") orelse return;
    const decor = j.object(window, "getDecorView", "()Landroid/view/View;") orelse return;
    const found = j.method(decor, "setSystemUiVisibility", "(I)V") orelse return;
    const flags = [_]i64{0x1606};

    j.at(63, *const fn (Env, ?*anyopaque, ?*anyopaque, ?*const anyopaque) callconv(.c) void)(j.env, decor, found, &flags);

    if (j.at(228, *const fn (Env) callconv(.c) u8)(j.env) != 0) j.at(17, *const fn (Env) callconv(.c) void)(j.env);
}

const Activity = extern struct {
    callbacks: ?*Callbacks,
    vm: *const *const [8]?*const anyopaque,
    env: ?*anyopaque,
    clazz: ?*anyopaque,
};

const App = extern struct {
    user_data: ?*anyopaque,
    on_app_cmd: ?*anyopaque,
    on_input_event: ?*anyopaque,
    activity: ?*Activity,
};

extern fn GetAndroidApp() ?*anyopaque;

const Env = *const *const [240]?*const anyopaque;

const Java = struct {
    env: Env,

    fn at(j: Java, index: usize, comptime T: type) T {
        return @ptrCast(@alignCast(j.env.*[index].?));
    }

    fn method(j: Java, target: *anyopaque, name: [*:0]const u8, sig: [*:0]const u8) ?*anyopaque {
        const getClass = j.at(31, *const fn (Env, ?*anyopaque) callconv(.c) ?*anyopaque);
        const getMethod = j.at(33, *const fn (Env, ?*anyopaque, [*:0]const u8, [*:0]const u8) callconv(.c) ?*anyopaque);
        const found = getMethod(j.env, getClass(j.env, target), name, sig);

        if (j.at(228, *const fn (Env) callconv(.c) u8)(j.env) != 0) {
            j.at(17, *const fn (Env) callconv(.c) void)(j.env);

            return null;
        }

        return found;
    }

    fn object(j: Java, target: *anyopaque, name: [*:0]const u8, sig: [*:0]const u8) ?*anyopaque {
        const found = j.method(target, name, sig) orelse return null;

        return j.at(36, *const fn (Env, ?*anyopaque, ?*anyopaque, ?*const anyopaque) callconv(.c) ?*anyopaque)(j.env, target, found, null);
    }

    fn int(j: Java, target: *anyopaque, name: [*:0]const u8) f32 {
        const found = j.method(target, name, "()I") orelse return 0;
        const value = j.at(51, *const fn (Env, ?*anyopaque, ?*anyopaque, ?*const anyopaque) callconv(.c) i32)(j.env, target, found, null);

        return @floatFromInt(@max(0, value));
    }
};

fn readInsets() ?[4]f32 {
    const app: *App = @ptrCast(@alignCast(GetAndroidApp() orelse return null));
    const activity = app.activity orelse return null;
    const attach: *const fn (*const anyopaque, *?Env, ?*anyopaque) callconv(.c) c_int = @ptrCast(@alignCast(activity.vm.*[4].?));
    const detach: *const fn (*const anyopaque) callconv(.c) c_int = @ptrCast(@alignCast(activity.vm.*[5].?));
    var env: ?Env = null;

    if (attach(@ptrCast(activity.vm), &env, null) != 0) return null;

    defer _ = detach(@ptrCast(activity.vm));

    const j: Java = .{ .env = env orelse return null };
    const window = j.object(activity.clazz orelse return null, "getWindow", "()Landroid/view/Window;") orelse return null;
    const decor = j.object(window, "getDecorView", "()Landroid/view/View;") orelse return null;
    const all = j.object(decor, "getRootWindowInsets", "()Landroid/view/WindowInsets;") orelse return null;
    var out = [4]f32{
        j.int(all, "getSystemWindowInsetLeft"),
        j.int(all, "getSystemWindowInsetTop"),
        j.int(all, "getSystemWindowInsetRight"),
        j.int(all, "getSystemWindowInsetBottom"),
    };

    if (j.object(all, "getDisplayCutout", "()Landroid/view/DisplayCutout;")) |cut| {
        out[0] = @max(out[0], j.int(cut, "getSafeInsetLeft"));
        out[1] = @max(out[1], j.int(cut, "getSafeInsetTop"));
        out[2] = @max(out[2], j.int(cut, "getSafeInsetRight"));
        out[3] = @max(out[3], j.int(cut, "getSafeInsetBottom"));
    }

    return out;
}

pub const Pointer = struct {
    at: rl.Vector2 = .{ .x = -1, .y = -1 },
    moved: bool = false,
    pressed: bool = false,
    down: bool = false,
    released: bool = false,

    pub fn over(p: Pointer, r: rl.Rectangle) bool {
        return rl.CheckCollisionPointRec(p.at, r);
    }
};

pub var pointer: Pointer = .{};
pub var delta: f32 = 0;
var armed: u32 = 0;
pub var pad_live: bool = false;
var age: f32 = 0;
var scene: u32 = 0;

const Anim = struct {
    id: u32 = 0,
    hot: f32 = 0,
    press: f32 = 0,
};

var anims: [192]Anim = @splat(.{});
var anim_next: usize = 0;

fn anim(id: u32) *Anim {
    for (&anims) |*a| {
        if (a.id == id) return a;
    }

    const slot = &anims[anim_next];

    anim_next = (anim_next + 1) % anims.len;
    slot.* = .{ .id = id };

    return slot;
}

pub fn begin(dt: f32) void {
    const d = rl.GetMouseDelta();

    delta = @min(dt, 0.05);
    age += delta;
    pointer = .{
        .at = rl.GetMousePosition(),
        .moved = d.x != 0 or d.y != 0,
        .pressed = rl.IsMouseButtonPressed(rl.MOUSE_BUTTON_LEFT),
        .down = rl.IsMouseButtonDown(rl.MOUSE_BUTTON_LEFT),
        .released = rl.IsMouseButtonReleased(rl.MOUSE_BUTTON_LEFT),
    };

    if (!pointer.down and !pointer.released) armed = 0;

    trackDevice();

    refreshInsets();
}

fn trackDevice() void {
    var i: c_int = 0;

    while (i < 4) : (i += 1) {
        if (!rl.IsGamepadAvailable(i) or rl.GetGamepadAxisCount(i) < 4) continue;

        var b: c_int = 1;

        while (b < 18) : (b += 1) {
            if (rl.IsGamepadButtonPressed(i, b)) pad_live = true;
        }

        if (@abs(rl.GetGamepadAxisMovement(i, rl.GAMEPAD_AXIS_LEFT_X)) > 0.6 or @abs(rl.GetGamepadAxisMovement(i, rl.GAMEPAD_AXIS_LEFT_Y)) > 0.6) pad_live = true;
    }

    if (pointer.moved or pointer.pressed) pad_live = false;

    for ([_]c_int{ rl.KEY_UP, rl.KEY_DOWN, rl.KEY_LEFT, rl.KEY_RIGHT, rl.KEY_ENTER, rl.KEY_ESCAPE, rl.KEY_TAB, rl.KEY_SPACE }) |key| {
        if (rl.IsKeyPressed(key)) pad_live = false;
    }
}

pub fn enterScene(id: u32) void {
    if (id == scene) return;

    scene = id;
    age = 0;
    armed = 0;
    anims = @splat(.{});
    anim_next = 0;
}

pub fn settled() bool {
    return age > 0.25;
}

pub const Reveal = struct {
    a: f32 = 1,
    dy: f32 = 0,

    pub fn move(e: Reveal, r: rl.Rectangle) rl.Rectangle {
        return .{ .x = r.x, .y = r.y + e.dy, .width = r.width, .height = r.height };
    }
};

pub fn reveal(order: f32) Reveal {
    const t = std.math.clamp((age - order * 0.05) / 0.34, 0, 1);
    const k = 1 - t;
    const eased = 1 - k * k * k;

    return .{ .a = std.math.clamp(t * 1.8, 0, 1), .dy = (1 - eased) * 34 * view().u };
}

pub fn tag(comptime name: []const u8, index: usize) u32 {
    const base = comptime std.hash.Fnv1a_32.hash(name);

    return base +% @as(u32, @intCast(index)) +% 1;
}

pub fn fade(c: rl.Color, a: f32) rl.Color {
    return ui.fade(c, a);
}

pub fn mix(a: rl.Color, b: rl.Color, t: f32) rl.Color {
    const k = std.math.clamp(t, 0, 1);
    const one = struct {
        fn of(x: u8, y: u8, m: f32) u8 {
            return @intFromFloat(@as(f32, @floatFromInt(x)) + (@as(f32, @floatFromInt(y)) - @as(f32, @floatFromInt(x))) * m);
        }
    }.of;

    return .{ .r = one(a.r, b.r, k), .g = one(a.g, b.g, k), .b = one(a.b, b.b, k), .a = one(a.a, b.a, k) };
}

pub fn grow(r: rl.Rectangle, by: f32) rl.Rectangle {
    return .{ .x = r.x - by, .y = r.y - by, .width = r.width + by * 2, .height = r.height + by * 2 };
}

pub fn offset(r: rl.Rectangle, dx: f32, dy: f32) rl.Rectangle {
    return .{ .x = r.x + dx, .y = r.y + dy, .width = r.width, .height = r.height };
}

fn piece(tex: rl.Texture2D, sx: f32, sy: f32, sw: f32, sh: f32, x: f32, y: f32, w: f32, h: f32, color: rl.Color) void {
    if (w <= 0 or h <= 0) return;

    rl.DrawTexturePro(tex, .{ .x = sx, .y = sy, .width = sw, .height = sh }, .{ .x = x, .y = y, .width = w, .height = h }, .{ .x = 0, .y = 0 }, 0, color);
}

pub fn round(r: rl.Rectangle, radius: f32, color: rl.Color) void {
    if (color.a == 0) return;

    const x0 = @round(r.x);
    const y0 = @round(r.y);
    const x3 = @round(r.x + r.width);
    const y3 = @round(r.y + r.height);
    const k = @round(@max(0, @min(radius, @min(x3 - x0, y3 - y0) / 2)));
    const x1 = x0 + k;
    const x2 = x3 - k;
    const y1 = y0 + k;
    const y2 = y3 - k;

    piece(disc, 0, 0, 128, 128, x0, y0, k, k, color);
    piece(disc, 128, 0, 128, 128, x2, y0, k, k, color);
    piece(disc, 0, 128, 128, 128, x0, y2, k, k, color);
    piece(disc, 128, 128, 128, 128, x2, y2, k, k, color);
    piece(disc, 127, 127, 2, 2, x1, y0, x2 - x1, k, color);
    piece(disc, 127, 127, 2, 2, x1, y2, x2 - x1, k, color);
    piece(disc, 127, 127, 2, 2, x0, y1, x3 - x0, y2 - y1, color);
}

pub fn notch(r: rl.Rectangle, radius: f32, color: rl.Color) void {
    const k = @round(radius);
    const x0 = @round(r.x);
    const y0 = @round(r.y);
    const x2 = @round(r.x + r.width) - k;
    const y2 = @round(r.y + r.height) - k;

    piece(hollow, 0, 0, 128, 128, x0, y0, k, k, color);
    piece(hollow, 128, 0, 128, 128, x2, y0, k, k, color);
    piece(hollow, 0, 128, 128, 128, x0, y2, k, k, color);
    piece(hollow, 128, 128, 128, 128, x2, y2, k, k, color);
}

pub fn dot(x: f32, y: f32, r: f32, color: rl.Color) void {
    piece(disc, 0, 0, 256, 256, x - r, y - r, r * 2, r * 2, color);
}

pub fn panel(r: rl.Rectangle, radius: f32, face: rl.Color, a: f32) void {
    const u = view().u;

    round(offset(r, 10 * u, 14 * u), radius, fade(night, 0.34 * a));
    round(offset(r, 0, 7 * u), radius, fade(mix(face, night, 0.24), a));
    round(r, radius, fade(face, a));
}

pub fn icon(which: Icon, cx: f32, cy: f32, size: f32, color: rl.Color) void {
    const i: usize = @backingInt(which);
    const sx: f32 = @floatFromInt(i % sheet_cols * cell);
    const sy: f32 = @floatFromInt(i / sheet_cols * cell);

    piece(sheet, sx, sy, cell, cell, @round(cx - size / 2), @round(cy - size / 2), size, size, color);
}

pub fn measure(font: rl.Font, str: [:0]const u8, size: f32) f32 {
    return rl.MeasureTextEx(font, str.ptr, size, size * 0.012).x;
}

pub fn write(font: rl.Font, str: [:0]const u8, x: f32, cy: f32, size: f32, color: rl.Color) void {
    rl.DrawTextEx(font, str.ptr, v2(@round(x), @round(cy - size * 0.54)), size, size * 0.012, color);
}

pub fn center(font: rl.Font, str: [:0]const u8, cx: f32, cy: f32, size: f32, color: rl.Color) void {
    write(font, str, cx - measure(font, str, size) / 2, cy, size, color);
}

pub fn fit(font: rl.Font, str: [:0]const u8, size: f32, max: f32) f32 {
    const w = measure(font, str, size);

    return if (w > max) size * max / w else size;
}

pub fn shadowed(font: rl.Font, str: [:0]const u8, x: f32, cy: f32, size: f32, color: rl.Color) void {
    const off = @max(2, size * 0.055);
    const a = @as(f32, @floatFromInt(color.a)) / 255;

    write(font, str, x + off * 0.8, cy + off, size, fade(night, a * a * 0.85));
    write(font, str, x, cy, size, color);
}

pub fn extruded(font: rl.Font, str: [:0]const u8, x: f32, cy: f32, size: f32, color: rl.Color, a: f32) void {
    const depth = size * 0.052;
    const steps: usize = @intFromFloat(std.math.clamp(@ceil(depth / 2), 3, 12));
    var i = steps;

    while (i > 0) : (i -= 1) {
        const k = depth * @as(f32, @floatFromInt(i)) / @as(f32, @floatFromInt(steps));

        write(font, str, x + k * 0.75, cy + k, size, fade(night, a * a * a));
    }

    write(font, str, x, cy, size, fade(color, a));
}

pub const Hit = struct {
    click: bool = false,
    hot: bool = false,
    face: rl.Rectangle,
};

pub fn press(key: u32, r: rl.Rectangle) bool {
    const over = pointer.over(r);

    if (over and pointer.pressed and settled()) armed = key;

    if (over and pointer.released and armed == key) {
        armed = 0;

        return true;
    }

    return false;
}

pub fn button(key: u32, r: rl.Rectangle, radius: f32, tone: Tone, focused: bool, e: Reveal) Hit {
    const u = view().u;
    const click = press(key, r);
    const over = pointer.over(r);
    const held = armed == key and over and pointer.down;
    const a = anim(key);

    a.hot += ((if (focused) @as(f32, 1) else 0) - a.hot) * @min(1, delta * 18);
    a.press += ((if (held) @as(f32, 1) else 0) - a.press) * @min(1, delta * 34);

    const depth = std.math.clamp(r.height * 0.075, 4 * u, 10 * u);
    const base = e.move(r);
    const shrink = a.press * @min(5 * u, r.height * 0.04);
    const face = offset(grow(base, -shrink), 0, a.press * depth - a.hot * 4 * u * (1 - a.press));
    const foot = offset(grow(base, -shrink), 0, depth);

    round(offset(foot, 7 * u, 9 * u), radius, fade(night, 0.3 * e.a));

    if (a.hot > 0.02) {
        const ring = 6 * u * a.hot;
        const outer: rl.Rectangle = .{ .x = face.x - ring, .y = face.y - ring, .width = face.width + ring * 2, .height = foot.y + foot.height - face.y + ring * 2 };

        round(outer, radius + ring, fade(tone.ring, e.a * a.hot));
    }

    round(foot, radius, fade(tone.edge, e.a));
    round(face, radius, fade(tone.face, e.a));

    return .{ .click = click, .hot = over and pointer.moved, .face = face };
}

pub fn scrim(a: f32) void {
    const v = view();

    rl.DrawRectangle(0, 0, @intFromFloat(v.w), @intFromFloat(v.h), fade(abyss, a));
}

var dimmed: f32 = 0;

pub fn dim(target: f32) void {
    dimmed += (target - dimmed) * @min(1, delta * 11);

    if (dimmed > 0.004) scrim(dimmed);
}

pub const Hint = struct {
    key: [:0]const u8,
    label: [:0]const u8,
};

pub fn hintsWidth(items: []const Hint, size: f32) f32 {
    var total: f32 = 0;

    for (items, 0..) |h, i| {
        total += @max(size * 1.5, measure(heavy, h.key, size) + size * 0.9) + size * 0.45 + measure(body, h.label, size * 1.1);

        if (i + 1 < items.len) total += size * 1.5;
    }

    return total;
}

pub fn hints(items: []const Hint, x: f32, cy: f32, size: f32, a: f32) void {
    var at = x;

    for (items) |h| {
        const tw = measure(heavy, h.key, size);
        const kw = @max(size * 1.5, tw + size * 0.9);
        const r: rl.Rectangle = .{ .x = at, .y = cy - size * 0.74, .width = kw, .height = size * 1.4 };

        round(offset(r, 0, size * 0.2), size * 0.34, fade(night, a));
        round(r, size * 0.34, fade(cream, a));
        center(heavy, h.key, at + kw / 2, cy - size * 0.04, size, fade(navy, a));
        at += kw + size * 0.45;
        shadowed(body, h.label, at, cy, size * 1.1, fade(cream, a));
        at += measure(body, h.label, size * 1.1) + size * 1.5;
    }
}

pub fn spinner(cx: f32, cy: f32, r: f32, track: rl.Color, fill: rl.Color) void {
    const t: f32 = @floatCast(rl.GetTime());
    const head = @mod(t * 300, 360);
    const span = 100 + 50 * @sin(t * 3);

    rl.DrawRing(v2(cx, cy), r * 0.74, r, 0, 360, 64, track);
    rl.DrawRing(v2(cx, cy), r * 0.74, r, head, head + span, 48, fill);

    for ([_]f32{ head, head + span }) |deg| {
        const a = deg * std.math.pi / 180;

        dot(cx + @cos(a) * r * 0.87, cy + @sin(a) * r * 0.87, r * 0.13, fill);
    }
}

pub fn headerHeight(v: View) f32 {
    return @max(v.tap(72), 96 * v.u);
}

pub fn header(title: [:0]const u8, sub: [:0]const u8) bool {
    const v = view();
    const e = reveal(0);
    const s = v.tap(72);
    const h = headerHeight(v);
    const r: rl.Rectangle = .{ .x = v.left, .y = v.top + (h - s) / 2, .width = s, .height = s };
    const b = button(tag("back", 0), r, 20 * v.u, tones.cream_tone, pointer.over(r), e);

    icon(.back, b.face.x + b.face.width * 0.47, b.face.y + b.face.height / 2, s * 0.52, fade(navy, e.a));

    const x = r.x + s + 30 * v.u;
    const size = 66 * v.u;
    const mid = v.top + h / 2 + e.dy;

    if (sub.len == 0) {
        extruded(heavy, title, x, mid, size, cream, e.a);
    } else {
        extruded(heavy, title, x, mid - 15 * v.u, size, cream, e.a);
        shadowed(body, sub, x + 2 * v.u, mid + 33 * v.u, 27 * v.u, fade(cream, e.a));
    }

    return b.click;
}

pub fn lockupSize(width: f32) [2]f32 {
    const one = width * 100 / measure(heavy, "DRONEFIRE", 100);
    const two = width * 100 / measure(heavy, "BATTLE", 100);

    return .{ one, two };
}

pub fn lockupHeight(width: f32) f32 {
    const s = lockupSize(width);

    return s[0] * 0.62 + s[1] * 0.66;
}

pub fn lockup(x: f32, y: f32, width: f32, first: Reveal, second: Reveal) void {
    const s = lockupSize(width);
    const font = displayFont(s[1]);
    const one = s[0] * width / measure(font, "DRONEFIRE", s[0]);
    const two = s[1] * width / measure(font, "BATTLE", s[1]);
    const top = y + s[0] * 0.29;

    extruded(font, "DRONEFIRE", x, top + first.dy, one, cream, first.a);
    extruded(font, "BATTLE", x - two * 0.004, top + s[0] * 0.33 + s[1] * 0.35 + second.dy, two, sun, second.a);
}
