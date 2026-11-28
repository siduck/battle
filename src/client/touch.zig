const std = @import("std");
const rl = @import("raylib");
const shared = @import("shared");
const ui = @import("ui.zig");
const art = @import("touchart.zig");
const settings = @import("settings.zig");
const assets = @import("assets.zig");
const game_mod = @import("game.zig");
const driving = @import("driving.zig");
const air = @import("air.zig");
const theme = @import("theme.zig");
const net = @import("net.zig");

const Controls = game_mod.Controls;

pub const Button = enum { fire, fire2, aim, jump, boost, reload, swap, grenade, use, pause };

const buttons = std.enums.values(Button);

pub const slots = game_mod.knife_slot + 1;

pub const Mode = enum { foot, car, jet };

const State = struct {
    mode: Mode = .foot,
    usable: bool = false,
    pickup: bool = false,
    empty: bool = false,

    fn flying(s: State) bool {
        return s.mode == .jet;
    }

    fn armed(s: State) bool {
        return s.mode == .foot or s.mode == .car;
    }
};

var state: State = .{};

pub var shown = false;

const Role = union(enum) {
    move,
    look,
    board,
    slot: u8,
    button: Button,
};

const Finger = struct {
    id: i32,
    role: Role,
    last: rl.Vector2,
    start: rl.Vector2,
    sliding: bool = false,
    seen: bool = true,
};

pub const Circle = struct {
    x: f32,
    y: f32,
    r: f32,
};

const Spot = struct {
    x: f32,
    y: f32,
    d: f32,
    anchor: enum { right, left, top } = .right,
};

pub const Layout = struct {
    unit: f32,
    buttons: [buttons.len]?Circle,
    stick: Circle,
    bar: ?rl.Rectangle,
    armed: bool,
    dock: f32,

    pub fn slot(l: Layout, index: usize) rl.Rectangle {
        const bar = l.bar orelse return .{ .x = 0, .y = 0, .width = 0, .height = 0 };
        const step = bar.width / slots;
        const space = 0.9 * l.unit;

        return .{ .x = @round(bar.x + step * @as(f32, @floatFromInt(index)) + space / 2), .y = bar.y, .width = @round(step - space), .height = bar.height };
    }
};

pub const Result = struct {
    controls: Controls = .{},
    look_x: f32 = 0,
    look_y: f32 = 0,
    pause: bool = false,
};

var forced: ?bool = null;

pub fn active() bool {
    if (assets.mobile) return true;

    if (forced == null) forced = std.c.getenv("DF_TOUCH") != null;

    return forced.?;
}

pub fn context(g: *const game_mod.Game, usable: bool) void {
    state = .{ .usable = usable };

    if (air.current() != null) {
        state.mode = .jet;
    } else if (driving.current(g) != null) {
        state.mode = .car;
    } else {
        state.pickup = g.dead <= 0 and g.near_drop != null;
    }

    const held = g.arsenal.current();

    state.empty = held.spec().mag > 0 and held.mag == 0;
}

const AndroidActivity = extern struct {
    callbacks: ?*anyopaque,
    vm: *const *const [8]?*const anyopaque,
    env: ?*anyopaque,
    clazz: ?*anyopaque,
};

const AndroidApp = extern struct {
    user_data: ?*anyopaque,
    on_app_cmd: ?*anyopaque,
    on_input_event: ?*anyopaque,
    activity: ?*AndroidActivity,
    config: ?*anyopaque,
};

extern fn GetAndroidApp() ?*anyopaque;
extern fn AConfiguration_getDensity(config: ?*anyopaque) i32;

const Env = *const *const [240]?*const anyopaque;

fn jni(env: Env, index: usize, comptime T: type) T {
    return @ptrCast(@alignCast(env.*[index].?));
}

fn displayDpi(activity: *AndroidActivity) f32 {
    const Attach = *const fn (*const anyopaque, *?*anyopaque, ?*anyopaque) callconv(.c) c_int;
    const Detach = *const fn (*const anyopaque) callconv(.c) c_int;
    const GetClass = *const fn (*const anyopaque, ?*anyopaque) callconv(.c) ?*anyopaque;
    const GetId = *const fn (*const anyopaque, ?*anyopaque, [*:0]const u8, [*:0]const u8) callconv(.c) ?*anyopaque;
    const Call = *const fn (*const anyopaque, ?*anyopaque, ?*anyopaque, ?*const anyopaque) callconv(.c) ?*anyopaque;
    const GetFloat = *const fn (*const anyopaque, ?*anyopaque, ?*anyopaque) callconv(.c) f32;
    const attach: Attach = @ptrCast(@alignCast(activity.vm.*[4].?));
    const detach: Detach = @ptrCast(@alignCast(activity.vm.*[5].?));
    var raw: ?*anyopaque = null;

    if (attach(@ptrCast(activity.vm), &raw, null) != 0) return 0;

    defer _ = detach(@ptrCast(activity.vm));

    const env: Env = @ptrCast(@alignCast(raw orelse return 0));
    const e: *const anyopaque = @ptrCast(env);
    const getClass = jni(env, 31, GetClass);
    const getMethod = jni(env, 33, GetId);
    const call = jni(env, 36, Call);
    const getField = jni(env, 94, GetId);
    const getFloat = jni(env, 102, GetFloat);
    const own = getClass(e, activity.clazz);
    const resources = call(e, activity.clazz, getMethod(e, own, "getResources", "()Landroid/content/res/Resources;"), null) orelse return 0;
    const kind = getClass(e, resources);
    const metrics = call(e, resources, getMethod(e, kind, "getDisplayMetrics", "()Landroid/util/DisplayMetrics;"), null) orelse return 0;
    const shape = getClass(e, metrics);
    const x = getFloat(e, metrics, getField(e, shape, "xdpi", "F"));
    const y = getFloat(e, metrics, getField(e, shape, "ydpi", "F"));

    return (x + y) / 2;
}

fn androidDpi() f32 {
    const app: *AndroidApp = @ptrCast(@alignCast(GetAndroidApp() orelse return 320));
    const measured = if (app.activity) |activity| displayDpi(activity) else 0;
    const physical = if (measured > 10 and measured < 80) measured * 10 else measured;

    if (physical > 100 and physical < 800) return physical;

    const density = AConfiguration_getDensity(app.config);

    return if (density > 0 and density < 1000) @floatFromInt(density) else 320;
}

fn monitorDpi() f32 {
    const monitor = rl.GetCurrentMonitor();
    const mm = rl.GetMonitorPhysicalHeight(monitor);
    const px = rl.GetMonitorHeight(monitor);

    if (mm <= 0 or px <= 0) return 160;

    return @as(f32, @floatFromInt(px)) / @as(f32, @floatFromInt(mm)) * 25.4;
}

var dpi_cache: f32 = 0;

fn dpi() f32 {
    if (dpi_cache > 0) return dpi_cache;

    dpi_cache = if (assets.mobile) androidDpi() else monitorDpi();
    rl.TraceLog(rl.LOG_INFO, "touch: %.0f dpi", @as(f64, dpi_cache));

    return dpi_cache;
}

const look_per_mm: f32 = 2.0 * std.math.pi / 180.0;
const slide_mm: f32 = 1.5;
const dead_zone: f32 = 0.12;
const full_zone: f32 = 0.85;
const leash: f32 = 1.35;

pub fn pxPerMm() f32 {
    return dpi() / 25.4;
}

pub fn lookScale() f32 {
    return look_per_mm / pxPerMm();
}

fn tablet(h: f32) f32 {
    return std.math.clamp((h / dpi() * 25.4 - 68) / 80, 0, 1);
}

fn unitFor(w: f32, h: f32) f32 {
    const size = dpi() / 25.4 * (1 + 0.4 * tablet(h)) * settings.touch_size;

    return @min(size, @min(w / 118, h / 62));
}

fn at(x: f32, y: f32, d: f32) Spot {
    return .{ .x = x, .y = y, .d = d };
}

fn spot(b: Button) ?Spot {
    if (b == .pause) return .{ .x = 8.5, .y = 8.5, .d = 8.5, .anchor = .top };
    if (b == .use and !state.usable) return null;
    if (b == .fire2) return .{ .x = 11, .y = 43, .d = 11, .anchor = .left };

    return switch (state.mode) {
        .foot => switch (b) {
            .fire => at(24.5, 22, 16),
            .jump => at(9, 23, 10.5),
            .aim => at(15.5, 35.5, 10.5),
            .reload => at(15, 9.5, 9.5),
            .swap => at(33.5, 9.5, 9.5),
            .grenade => at(33.5, 36, 9.5),
            .use => at(43.5, 23, 10.5),
            else => null,
        },
        .car => switch (b) {
            .jump => at(12.5, 13.5, 15),
            .boost => at(31.5, 12.5, 12),
            .fire => at(13, 33, 13),
            .aim => at(29, 29.5, 10),
            .reload => at(44, 19, 10),
            .swap => at(44, 35, 10),
            .grenade => at(29, 43.5, 10),
            .use => at(10.5, 50, 10.5),
            else => null,
        },
        .jet => switch (b) {
            .fire => at(30, 20, 16),
            .boost => at(11, 15, 13),
            .aim => at(23.5, 39, 12),
            .use => at(10.5, 50, 10.5),
            else => null,
        },
    };
}

pub fn layout(w: f32, h: f32) Layout {
    const u = unitFor(w, h);
    const lift = 11 * tablet(h) * dpi() / 25.4;
    const floor = h - theme.bottomInset();
    var l: Layout = .{
        .unit = u,
        .buttons = @splat(null),
        .stick = .{ .x = @round(24 * u), .y = @round(floor - 21 * u - lift), .r = @round(14 * u) },
        .bar = null,
        .armed = state.armed(),
        .dock = floor - 2.5 * u,
    };

    for (buttons) |b| {
        const s = spot(b) orelse continue;

        l.buttons[@intFromEnum(b)] = .{
            .x = @round(if (s.anchor == .right) w - s.x * u else s.x * u),
            .y = @round(if (s.anchor == .top) s.y * u else floor - s.y * u - lift),
            .r = @round(s.d * u / 2),
        };
    }

    if (state.mode != .foot) return l;

    const bu = u / @max(1, settings.touch_size);
    const top = floor - 10 * bu;
    var half = 29.5 * bu;

    for (l.buttons) |maybe| {
        const c = maybe orelse continue;

        if (c.y + c.r > top - u) half = @min(half, @abs(c.x - w / 2) - c.r - 1.5 * u);
    }

    if (l.stick.y + l.stick.r > top) half = @min(half, w / 2 - l.stick.x - l.stick.r - 1.5 * u);

    const tall = @round(@min(7.5 * bu, half * 2 / slots * 0.72));

    l.bar = .{ .x = @round(w / 2 - half), .y = @round(floor - 2.5 * bu - tall), .width = @round(half * 2), .height = tall };
    l.dock = l.bar.?.y;

    return l;
}

pub fn besidePause(w: f32, h: f32) rl.Vector2 {
    const u = unitFor(w, h);

    return .{ .x = 15.5 * u, .y = 8.5 * u };
}

pub fn feedLeft(w: f32, h: f32) f32 {
    return 19 * unitFor(w, h);
}

pub fn feedRight(w: f32, h: f32) ?f32 {
    if (state.mode == .foot) return null;

    return w - 18 * unitFor(w, h);
}

fn nearest(l: Layout, p: rl.Vector2) ?Button {
    var best: ?Button = null;
    var edge: f32 = 0;

    for (buttons) |b| {
        const c = l.buttons[@intFromEnum(b)] orelse continue;
        const slop: f32 = if (b == .fire or b == .pause) 2.2 else 1.4;
        const distance = std.math.hypot(p.x - c.x, p.y - c.y) - c.r;

        if (distance <= slop * l.unit and (best == null or distance < edge)) {
            best = b;
            edge = distance;
        }
    }

    return best;
}

pub const Touch = struct {
    fingers: [10]?Finger = @splat(null),
    origin: rl.Vector2 = .{},
    knob: rl.Vector2 = .{},
    thumb: rl.Vector2 = .{},
    aiming: bool = false,
    moving: bool = false,
    sprinting: bool = false,
    press: [buttons.len]f32 = @splat(0),

    fn find(t: *Touch, id: i32, p: rl.Vector2, dt: f32) ?*Finger {
        const reach = @max(18, 2500 * dt) * pxPerMm();

        for (&t.fingers) |*f| {
            if (f.*) |*finger| {
                if (finger.id != id) continue;

                if (std.math.hypot(p.x - finger.last.x, p.y - finger.last.y) <= reach) return finger;

                f.* = null;

                return null;
            }
        }

        return null;
    }

    fn add(t: *Touch, finger: Finger) void {
        for (&t.fingers) |*f| {
            if (f.* == null) {
                f.* = finger;

                return;
            }
        }
    }

    fn roleAt(l: Layout, p: rl.Vector2, w: f32, h: f32) Role {
        if (net.board_rect) |r| {
            if (rl.CheckCollisionPointRec(p, r)) return .board;
        }

        if (nearest(l, p)) |b| return .{ .button = b };

        if (l.bar) |bar| {
            if (p.x >= bar.x and p.x < bar.x + bar.width and p.y >= bar.y - l.unit) {
                const index: u8 = @intFromFloat((p.x - bar.x) / bar.width * slots);

                return .{ .slot = @min(index, slots - 1) };
            }
        }

        if (p.x < w * 0.4 and p.y > h * 0.3) return .move;

        return .look;
    }

    pub fn read(t: *Touch, w: f32, h: f32) Result {
        const l = layout(w, h);
        const reach = l.stick.r;
        var out: Result = .{};
        const emulate = !assets.mobile and rl.GetTouchPointCount() == 0 and rl.IsMouseButtonDown(rl.MOUSE_BUTTON_LEFT);
        const count: usize = if (emulate) 1 else @intCast(rl.GetTouchPointCount());

        if (!state.armed()) t.aiming = false;

        for (&t.fingers) |*f| {
            if (f.*) |*finger| finger.seen = false;
        }

        for (0..count) |i| {
            const id = if (emulate) 0 else rl.GetTouchPointId(@intCast(i));
            const p = if (emulate) rl.GetMousePosition() else rl.GetTouchPosition(@intCast(i));

            if (t.find(id, p, rl.GetFrameTime())) |finger| {
                const dx = p.x - finger.last.x;
                const dy = p.y - finger.last.y;

                finger.seen = true;
                finger.last = p;

                switch (finger.role) {
                    .move => t.knob = p,
                    .board, .slot => {},
                    .look => {
                        out.look_x += dx;
                        out.look_y += dy;
                    },
                    .button => |b| if (steers(b)) {
                        if (finger.sliding) {
                            out.look_x += dx;
                            out.look_y += dy;
                        } else {
                            finger.sliding = std.math.hypot(p.x - finger.start.x, p.y - finger.start.y) > slide_mm * pxPerMm();
                        }
                    },
                }

                continue;
            }

            const role = roleAt(l, p, w, h);

            t.add(.{ .id = id, .role = role, .last = p, .start = p });

            switch (role) {
                .move => {
                    t.origin = p;
                    t.knob = p;
                },
                .look => {},
                .board => net.board_open = !net.board_open,
                .slot => |index| out.controls.select = index,
                .button => |b| switch (b) {
                    .fire, .fire2 => out.controls.fire_pressed = true,
                    .aim => if (state.armed()) {
                        t.aiming = !t.aiming;
                    },
                    .reload => out.controls.reload = true,
                    .swap => out.controls.cycle = 1,
                    .grenade => out.controls.grenade = true,
                    .use => {
                        out.controls.enter = true;
                        out.controls.interact = true;
                    },
                    .pause => out.pause = true,
                    .jump, .boost => {},
                },
            }
        }

        const fade = rl.GetFrameTime() / 0.14;

        for (&t.press) |*p| p.* = @max(0, p.* - fade);

        t.moving = false;

        for (&t.fingers) |*f| {
            const finger = f.* orelse continue;

            if (!finger.seen) {
                f.* = null;

                continue;
            }

            switch (finger.role) {
                .move => t.moving = true,
                .look, .board, .slot => {},
                .button => |b| {
                    t.press[@intFromEnum(b)] = 1;

                    switch (b) {
                        .fire, .fire2 => out.controls.fire_down = true,
                        .jump => out.controls.jump = true,
                        .boost => out.controls.boost = true,
                        .aim => if (state.flying()) {
                            out.controls.aim = true;
                        },
                        else => {},
                    }
                },
            }
        }

        if (t.moving) {
            var dx = t.knob.x - t.origin.x;
            var dy = t.knob.y - t.origin.y;
            var len = @sqrt(dx * dx + dy * dy);

            if (len > reach * leash) {
                const pull = (len - reach * leash) / len;

                t.origin.x += dx * pull;
                t.origin.y += dy * pull;
                dx -= dx * pull;
                dy -= dy * pull;
                len = reach * leash;
            }

            const k = if (len > reach) reach / len else 1;
            const tilt = len / reach;
            const strength = std.math.clamp((tilt - dead_zone) / (full_zone - dead_zone), 0, 1);
            const side = if (len > 0) dx / len else 0;
            const ahead = if (len > 0) -dy / len else 0;

            out.controls.right = side * strength;
            out.controls.forward = ahead * strength;
            out.controls.sprint = tilt >= 0.98 and ahead > 0.7;
            t.thumb = .{ .x = t.origin.x + dx * k, .y = t.origin.y + dy * k };
        } else {
            t.origin = .{ .x = l.stick.x, .y = l.stick.y };
            t.knob = t.origin;
            t.thumb = t.origin;
        }

        t.sprinting = out.controls.sprint and state.mode == .foot;

        if (t.aiming) out.controls.aim = true;

        return out;
    }

    pub fn draw(t: *const Touch, font: rl.Font, w: f32, h: f32) void {
        const l = layout(w, h);
        const u = l.unit;
        const op = settings.touch_opacity;
        const rest = !t.moving;
        const center = if (rest) rl.Vector2{ .x = l.stick.x, .y = l.stick.y } else t.origin;
        const knob = if (rest) center else t.thumb;

        _ = font;

        art.prepare(u);
        art.disc(center.x, center.y, l.stick.r, 1, ui.fade(shade, (if (rest) @as(f32, 0.32) else 0.42) * op));
        art.ring(center.x, center.y, l.stick.r, 0.28 * u, 1, ui.fade(ui.white, (if (rest) @as(f32, 0.3) else 0.5) * op));
        art.disc(knob.x, knob.y, 5.5 * u, 1, ui.fade(ui.white, (if (rest) @as(f32, 0.55) else 0.9) * op));

        if (t.sprinting) {
            const above = center.y - l.stick.r - 10 * u;

            art.disc(center.x, above, 4 * u, 1, ui.fade(shade, 0.5 * op));
            art.icon(.sprint, center.x, above, 5.5 * u, 1, ui.fade(ui.white, 0.96 * @max(op, 0.5)));
        }

        for (buttons) |b| {
            const c = l.buttons[@intFromEnum(b)] orelse continue;
            const press = t.press[@intFromEnum(b)];
            const on: f32 = if (b == .aim and t.aiming) 1 else press;
            const warn = b == .reload and state.empty and state.armed();

            button(c, glyphFor(b), u, on, 1 - 0.07 * press, b == .fire, warn);
        }
    }
};

fn steers(b: Button) bool {
    return switch (b) {
        .fire, .aim, .jump, .boost => true,
        else => false,
    };
}

const shade = ui.rgba(10, 13, 20, 255);

fn mix(a: rl.Color, b: rl.Color, k: f32) rl.Color {
    const Part = struct {
        fn of(x: u8, y: u8, f: f32) u8 {
            const from: f32 = @floatFromInt(x);
            const to: f32 = @floatFromInt(y);

            return @intFromFloat(@round(from + (to - from) * f));
        }
    };

    return .{ .r = Part.of(a.r, b.r, k), .g = Part.of(a.g, b.g, k), .b = Part.of(a.b, b.b, k), .a = Part.of(a.a, b.a, k) };
}

fn button(c: Circle, kind: art.Icon, u: f32, on: f32, scale: f32, primary: bool, warn: bool) void {
    const op = settings.touch_opacity;
    const solid = @max(op, 0.5);
    const idle = ui.fade(shade, (if (primary) @as(f32, 0.56) else 0.5) * op);
    const rim = if (warn) ui.fade(ui.accent, solid) else ui.fade(ui.white, (if (primary) @as(f32, 0.62) else 0.32) * op);
    const part: f32 = if (primary) 0.56 else if (kind == .pause) 0.46 else 0.55;
    const ink = if (warn) ui.accent else ui.white;

    art.disc(c.x, c.y, c.r, scale, mix(idle, ui.fade(ui.white, 0.9 * solid), on));
    art.ring(c.x, c.y, c.r, (if (primary) @as(f32, 0.5) else 0.28) * u, scale, mix(rim, ui.fade(ui.white, solid), on));
    art.icon(kind, c.x, c.y, c.r * 2 * part, scale, mix(ui.fade(ink, 0.96 * solid), ui.fade(shade, 0.95), on));
}

fn glyphFor(b: Button) art.Icon {
    return switch (b) {
        .fire, .fire2 => .fire,
        .aim => if (state.flying()) .missile else .aim,
        .jump => if (state.mode == .foot) .jump else .brake,
        .boost => .boost,
        .reload => .reload,
        .swap => .swap,
        .grenade => .grenade,
        .use => if (state.mode != .foot) .exit else if (state.pickup) .pickup else .enter,
        .pause => .pause,
    };
}

pub fn boardButton(left: f32, middle: f32, on: bool) rl.Rectangle {
    const w: f32 = @floatFromInt(rl.GetScreenWidth());
    const h: f32 = @floatFromInt(rl.GetScreenHeight());
    const u = unitFor(w, h);
    const r = @round(4.25 * u);
    const c: Circle = .{ .x = @round(left + 2 * u + r), .y = @round(@max(middle, r + 2.5 * u)), .r = r };

    art.prepare(u);
    button(c, .board, u, if (on) 1 else 0, 1, false, false);

    return .{ .x = c.x - r * 1.4, .y = c.y - r * 1.4, .width = r * 2.8, .height = r * 2.8 };
}
