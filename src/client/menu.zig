const std = @import("std");
const rl = @import("raylib");
const theme = @import("theme.zig");
const settings = @import("settings.zig");
const assets = @import("assets.zig");

const v2 = @import("ui.zig").v2;

const Fmt = enum { percent, times, degrees };

const Slider = struct {
    ptr: *f32,
    min: f32,
    max: f32,
    step: f32,
    fmt: Fmt,
};

const Choice = struct {
    ptr: *u8,
    names: []const [:0]const u8,
    swatch: bool = false,
};

const Kind = union(enum) {
    slider: Slider,
    toggle: *bool,
    choice: Choice,
    preset,
    reset_touch,
};

const Item = struct {
    label: [:0]const u8,
    kind: Kind,
    note: ?[:0]const u8 = null,
    custom: bool = false,
};

const gameplay = [_]Item{
    .{ .label = "Mouse sensitivity", .kind = .{ .slider = .{ .ptr = &settings.mouse_sens, .min = 0.2, .max = 3, .step = 0.05, .fmt = .times } } },
    .{ .label = "Aim sensitivity", .kind = .{ .slider = .{ .ptr = &settings.ads_sens, .min = 0.3, .max = 1.5, .step = 0.05, .fmt = .times } }, .note = "While aiming down sights" },
    .{ .label = "Invert look", .kind = .{ .toggle = &settings.invert_y } },
    .{ .label = "Field of view", .kind = .{ .slider = .{ .ptr = &settings.fov, .min = 70, .max = 110, .step = 1, .fmt = .degrees } } },
    .{ .label = "Crosshair", .kind = .{ .choice = .{ .ptr = &settings.crosshair_style, .names = &settings.crosshair_styles } } },
    .{ .label = "Crosshair colour", .kind = .{ .choice = .{ .ptr = &settings.crosshair_color, .names = &settings.crosshair_names, .swatch = true } } },
    .{ .label = "Show FPS", .kind = .{ .toggle = &settings.show_fps } },
};

const controller = [_]Item{
    .{ .label = "Look sensitivity", .kind = .{ .slider = .{ .ptr = &settings.stick_sens, .min = 0.3, .max = 2.5, .step = 0.05, .fmt = .times } } },
    .{ .label = "Aim assist", .kind = .{ .slider = .{ .ptr = &settings.aim_assist, .min = 0, .max = 1, .step = 0.05, .fmt = .percent } } },
    .{ .label = "Stick deadzone", .kind = .{ .slider = .{ .ptr = &settings.deadzone, .min = 0.04, .max = 0.3, .step = 0.01, .fmt = .percent } } },
    .{ .label = "Vibration", .kind = .{ .toggle = &settings.vibration } },
};

const graphics_desktop = [_]Item{
    .{ .label = "Quality", .kind = .preset },
    .{ .label = "Shadows", .kind = .{ .choice = .{ .ptr = &settings.shadows, .names = &settings.shadow_names } }, .note = "Medium / High apply after restart", .custom = true },
    .{ .label = "Render scale", .kind = .{ .slider = .{ .ptr = &settings.render_scale, .min = 0.5, .max = 1, .step = 0.05, .fmt = .percent } }, .custom = true },
    .{ .label = "View distance", .kind = .{ .slider = .{ .ptr = &settings.view_dist, .min = 0.4, .max = 1.5, .step = 0.05, .fmt = .percent } }, .custom = true },
    .{ .label = "Effects", .kind = .{ .choice = .{ .ptr = &settings.effects, .names = &settings.effects_names } }, .note = "Lighting, ambient occlusion, glow", .custom = true },
    .{ .label = "Anti-aliasing", .kind = .{ .toggle = &settings.msaa }, .note = "Applies after restart" },
    .{ .label = "VSync", .kind = .{ .toggle = &settings.vsync } },
    .{ .label = "Fullscreen", .kind = .{ .toggle = &settings.fullscreen } },
};

const graphics_mobile = [_]Item{
    .{ .label = "Quality", .kind = .preset },
    .{ .label = "Shadows", .kind = .{ .choice = .{ .ptr = &settings.shadows, .names = &settings.shadow_names } }, .note = "Medium / High apply after restart", .custom = true },
    .{ .label = "Render scale", .kind = .{ .slider = .{ .ptr = &settings.render_scale, .min = 0.5, .max = 1, .step = 0.05, .fmt = .percent } }, .custom = true },
    .{ .label = "View distance", .kind = .{ .slider = .{ .ptr = &settings.view_dist, .min = 0.4, .max = 1.5, .step = 0.05, .fmt = .percent } }, .custom = true },
};

const audio = [_]Item{
    .{ .label = "Master volume", .kind = .{ .slider = .{ .ptr = &settings.master, .min = 0, .max = 1, .step = 0.05, .fmt = .percent } } },
    .{ .label = "Effects", .kind = .{ .slider = .{ .ptr = &settings.sfx, .min = 0, .max = 1, .step = 0.05, .fmt = .percent } } },
    .{ .label = "Interface", .kind = .{ .slider = .{ .ptr = &settings.ui, .min = 0, .max = 1, .step = 0.05, .fmt = .percent } } },
};

const touch = [_]Item{
    .{ .label = "Button size", .kind = .{ .slider = .{ .ptr = &settings.touch_size, .min = 0.7, .max = 1.4, .step = 0.05, .fmt = .times } } },
    .{ .label = "Button opacity", .kind = .{ .slider = .{ .ptr = &settings.touch_opacity, .min = 0.3, .max = 1, .step = 0.05, .fmt = .percent } } },
    .{ .label = "Look sensitivity", .kind = .{ .slider = .{ .ptr = &settings.touch_look, .min = 0.3, .max = 2.5, .step = 0.05, .fmt = .times } } },
    .{ .label = "Aim sensitivity", .kind = .{ .slider = .{ .ptr = &settings.touch_ads, .min = 0.3, .max = 1.5, .step = 0.05, .fmt = .times } }, .note = "While aiming down sights" },
    .{ .label = "Aim assist", .kind = .{ .slider = .{ .ptr = &settings.touch_assist, .min = 0, .max = 1, .step = 0.05, .fmt = .percent } } },
    .{ .label = "Reset touch layout", .kind = .reset_touch },
};

const Tab = struct {
    name: [:0]const u8,
    items: []const Item,
};

const max_rows = 8;

pub const Menu = struct {
    open: bool = false,
    t: f32 = 0,
    tab: usize = 0,
    sel: usize = 0,
    slide: f32 = 0,
    glow: [max_rows]f32 = @splat(0),
    knob: [max_rows]f32 = @splat(0),
    drag: ?usize = null,
    hold: f32 = 0,
    hold_dir: i32 = 0,
    vhold: f32 = 0,
    vhold_dir: i32 = 0,
    mouse_last: rl.Vector2 = .{},
    using_mouse: bool = true,
    pressed_footer: ?u8 = null,
    flash: f32 = 0,
    touch_enabled: bool = false,
    stick_ready: bool = false,

    pub fn show(m: *Menu) void {
        m.open = true;
        m.stick_ready = false;
        m.sel = 0;
        m.drag = null;

        for (tabsFor(m.touch_enabled)[m.tab].items, 0..) |it, i| {
            if (i < max_rows) m.knob[i] = if (it.kind == .toggle and it.kind.toggle.*) 1 else 0;
        }
    }

    pub fn close(m: *Menu) void {
        m.open = false;
        m.drag = null;
        settings.save();
    }

    pub fn wantsOpen(m: *Menu, pad: ?c_int) bool {
        _ = m;

        if (rl.IsKeyPressed(rl.KEY_TAB) or rl.IsKeyPressed(rl.KEY_O)) return true;

        if (pad) |id| {
            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_FACE_UP) or rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_MIDDLE_LEFT)) return true;
        }

        if (rl.IsMouseButtonPressed(rl.MOUSE_BUTTON_LEFT)) {
            const b = gearRect();

            return rl.CheckCollisionPointRec(rl.GetMousePosition(), b);
        }

        return false;
    }

    pub fn update(m: *Menu, dt: f32, pad: ?c_int) void {
        m.t = std.math.clamp(m.t + (if (m.open) dt else -dt) * 6, 0, 1);
        m.slide += (@as(f32, @floatFromInt(m.tab)) - m.slide) * @min(1, dt * 14);
        m.flash = @max(0, m.flash - dt * 2.5);

        const tabs = tabsFor(m.touch_enabled);

        m.tab = @min(m.tab, tabs.len - 1);

        const items = tabs[m.tab].items;
        const rows = @min(items.len, max_rows);

        for (0..max_rows) |i| {
            const want: f32 = if (i < rows and i == m.sel) 1 else 0;
            const on: f32 = if (i < rows and items[i].kind == .toggle and items[i].kind.toggle.*) 1 else 0;

            m.glow[i] += (want - m.glow[i]) * @min(1, dt * 16);
            m.knob[i] += (on - m.knob[i]) * @min(1, dt * 18);
        }

        if (!m.open) return;

        const back = rl.IsKeyPressed(rl.KEY_ESCAPE) or rl.IsKeyPressed(rl.KEY_BACK) or rl.IsKeyPressed(rl.KEY_BACKSPACE) or (if (pad) |id| rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_FACE_RIGHT) or rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_MIDDLE_RIGHT) else false);

        if (back) {
            m.close();

            return;
        }

        var tab_dir: i32 = 0;

        if (rl.IsKeyPressed(rl.KEY_E) or rl.IsKeyPressed(rl.KEY_PAGE_DOWN)) tab_dir = 1;
        if (rl.IsKeyPressed(rl.KEY_Q) or rl.IsKeyPressed(rl.KEY_PAGE_UP)) tab_dir = -1;

        if (pad) |id| {
            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_TRIGGER_1)) tab_dir = 1;
            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_LEFT_TRIGGER_1)) tab_dir = -1;
        }

        if (tab_dir != 0) m.setTab(@intCast(@mod(@as(i32, @intCast(m.tab)) + tab_dir, @as(i32, @intCast(tabs.len)))));

        var vert: i32 = 0;
        var horiz: i32 = 0;
        var activate = rl.IsKeyPressed(rl.KEY_ENTER) or rl.IsKeyPressed(rl.KEY_SPACE);

        if (rl.IsKeyDown(rl.KEY_DOWN) or rl.IsKeyDown(rl.KEY_S)) vert = 1;
        if (rl.IsKeyDown(rl.KEY_UP) or rl.IsKeyDown(rl.KEY_W)) vert = -1;
        if (rl.IsKeyDown(rl.KEY_RIGHT) or rl.IsKeyDown(rl.KEY_D)) horiz = 1;
        if (rl.IsKeyDown(rl.KEY_LEFT) or rl.IsKeyDown(rl.KEY_A)) horiz = -1;

        if (pad) |id| {
            const sx = rl.GetGamepadAxisMovement(id, rl.GAMEPAD_AXIS_LEFT_X);
            const sy = rl.GetGamepadAxisMovement(id, rl.GAMEPAD_AXIS_LEFT_Y);

            if (@abs(sx) < 0.3 and @abs(sy) < 0.3) m.stick_ready = true;

            const live = m.stick_ready;

            if (rl.IsGamepadButtonDown(id, rl.GAMEPAD_BUTTON_LEFT_FACE_DOWN) or (live and sy > 0.55)) vert = 1;
            if (rl.IsGamepadButtonDown(id, rl.GAMEPAD_BUTTON_LEFT_FACE_UP) or (live and sy < -0.55)) vert = -1;
            if (rl.IsGamepadButtonDown(id, rl.GAMEPAD_BUTTON_LEFT_FACE_RIGHT) or (live and sx > 0.55)) horiz = 1;
            if (rl.IsGamepadButtonDown(id, rl.GAMEPAD_BUTTON_LEFT_FACE_LEFT) or (live and sx < -0.55)) horiz = -1;

            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_FACE_DOWN)) activate = true;

            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_FACE_LEFT)) {
                settings.reset();
                m.flash = 1;
            }
        }

        if (vert != 0 or horiz != 0) m.using_mouse = false;

        if (repeat(&m.vhold, &m.vhold_dir, vert, dt)) m.sel = @intCast(@mod(@as(i32, @intCast(m.sel)) + vert, @as(i32, @intCast(rows))));

        if (repeat(&m.hold, &m.hold_dir, horiz, dt)) adjust(items[m.sel], horiz);

        if (activate) adjust(items[m.sel], 1);

        m.mouse(items[0..rows]);
    }

    fn setTab(m: *Menu, tab: usize) void {
        m.tab = tab;
        m.sel = 0;
        m.drag = null;

        const items = tabsFor(m.touch_enabled)[tab].items;

        for (0..max_rows) |i| {
            m.knob[i] = if (i < items.len and items[i].kind == .toggle and items[i].kind.toggle.*) 1 else 0;
        }
    }

    fn mouse(m: *Menu, items: []const Item) void {
        const mp = rl.GetMousePosition();
        const moved = mp.x != m.mouse_last.x or mp.y != m.mouse_last.y;
        const click = rl.IsMouseButtonPressed(rl.MOUSE_BUTTON_LEFT);
        const down = rl.IsMouseButtonDown(rl.MOUSE_BUTTON_LEFT);
        const tabs = tabsFor(m.touch_enabled);
        const l = layout(tabs, m.tab);

        m.mouse_last = mp;

        if (moved or click) m.using_mouse = true;

        if (!down) m.drag = null;

        if (click) {
            for (0..tabs.len) |i| {
                if (rl.CheckCollisionPointRec(mp, tabRect(l, i, tabs.len))) {
                    m.setTab(i);

                    return;
                }
            }

            if (rl.CheckCollisionPointRec(mp, l.reset)) {
                settings.reset();
                m.flash = 1;

                return;
            }

            if (rl.CheckCollisionPointRec(mp, l.back)) {
                m.close();

                return;
            }
        }

        for (items, 0..) |it, i| {
            var row = rowRect(l, i);

            row.height = l.row_h;

            if (moved and m.drag == null and rl.CheckCollisionPointRec(mp, row)) m.sel = i;

            if (click and rl.CheckCollisionPointRec(mp, row)) {
                m.sel = i;

                switch (it.kind) {
                    .slider => m.drag = i,
                    .toggle, .reset_touch => adjust(it, 1),
                    .choice, .preset => {
                        const c = controlRect(l, i);

                        adjust(it, if (mp.x < c.x + c.width / 2) -1 else 1);
                    },
                }
            }
        }

        if (m.drag) |i| {
            const it = items[i];
            const s = it.kind.slider;
            const track = sliderTrack(l, i);
            const f = std.math.clamp((mp.x - track.x) / track.width, 0, 1);
            const raw = s.min + (s.max - s.min) * f;

            s.ptr.* = std.math.clamp(@round(raw / s.step) * s.step, s.min, s.max);

            if (it.custom) settings.preset = .custom;
        }
    }

    pub fn drawGear(m: *const Menu, pad: bool) void {
        if (m.t > 0.99) return;

        pauseButton(1, gearRect(), .gear, "SETTINGS", if (pad) "Y" else "TAB", theme.tones.cream_tone, m.t);
    }

    pub fn draw(m: *const Menu, pad: bool) void {
        if (m.t <= 0.001) return;

        const tabs = tabsFor(m.touch_enabled);
        const items = tabs[m.tab].items;
        const l = layout(tabs, m.tab);
        const u = l.u;
        const e = ease(m.t);
        const lift = (1 - e) * 36 * u;
        const p = shift(l.panel, lift);

        theme.scrim(0.6 * e);
        theme.panel(p, 36 * u, theme.cream, e);

        const mid = shift(l.title, lift);
        const size = 58 * u;

        theme.dot(mid.x + 30 * u, mid.y + mid.height / 2, 30 * u, theme.fade(theme.coral, e));
        theme.icon(.gear, mid.x + 30 * u, mid.y + mid.height / 2, 40 * u, theme.fade(theme.cream, e));
        theme.write(theme.heavy, "SETTINGS", mid.x + 76 * u, mid.y + mid.height / 2, size, theme.fade(theme.navy, e));

        const bar = shift(l.tabs, lift);

        theme.round(bar, 22 * u, theme.fade(theme.navy, e));

        const from = shift(tabRect(l, @intFromFloat(@floor(m.slide)), tabs.len), lift);
        const to = shift(tabRect(l, @min(tabs.len - 1, @as(usize, @intFromFloat(@ceil(m.slide)))), tabs.len), lift);
        const k = m.slide - @floor(m.slide);
        const chip: rl.Rectangle = theme.grow(.{ .x = from.x + (to.x - from.x) * k, .y = from.y, .width = from.width + (to.width - from.width) * k, .height = from.height }, -7 * u);

        theme.round(chip, 17 * u, theme.fade(theme.sun, e));

        for (tabs, 0..) |tab, i| {
            const r = shift(tabRect(l, i, tabs.len), lift);
            const active = i == m.tab;
            const hot = m.using_mouse and rl.CheckCollisionPointRec(rl.GetMousePosition(), r);
            const ts = theme.fit(theme.heavy, tab.name, 32 * u, r.width - 28 * u);

            if (hot and !active) theme.round(theme.grow(r, -7 * u), 17 * u, theme.fade(theme.cream, 0.12 * e));

            theme.center(theme.heavy, tab.name, r.x + r.width / 2, r.y + r.height / 2, ts, theme.fade(if (active) theme.navy else theme.cream, (if (active or hot) @as(f32, 1) else 0.78) * e));
        }

        for (items[0..@min(items.len, max_rows)], 0..) |it, i| m.drawRow(l, it, i, lift, e);

        if (hasPreview(tabs[m.tab])) layoutPreview(l, @min(items.len, l.per), lift, e);

        footer(m, l, lift, e, pad);
    }

    fn drawRow(m: *const Menu, l: Layout, it: Item, i: usize, dy: f32, e: f32) void {
        const u = l.u;
        const row = shift(rowRect(l, i), dy);
        const g = m.glow[i];
        const size = 34 * u;
        const cy = row.y + row.height / 2;
        const c = shift(controlRect(l, i), dy);
        const room = c.x - row.x - 40 * u;

        theme.round(row, 18 * u, theme.fade(theme.sand, (0.42 + 0.58 * g) * e));

        if (g > 0.01) theme.round(.{ .x = row.x + 10 * u, .y = row.y + 12 * u, .width = 8 * u, .height = row.height - 24 * u }, 4 * u, theme.fade(theme.coral, g * e));

        if (it.note) |note| {
            theme.write(theme.heavy, it.label, row.x + 32 * u, cy - 12 * u, theme.fit(theme.heavy, it.label, size, room), theme.fade(theme.navy, e));
            theme.write(theme.body, note, row.x + 32 * u, cy + 19 * u, theme.fit(theme.body, note, 23 * u, room), theme.fade(theme.soft, e));
        } else {
            theme.write(theme.heavy, it.label, row.x + 32 * u, cy, theme.fit(theme.heavy, it.label, size, room), theme.fade(theme.navy, e));
        }

        switch (it.kind) {
            .slider => |s| {
                const track = shift(sliderTrack(l, i), dy);
                const f = std.math.clamp((s.ptr.* - s.min) / (s.max - s.min), 0, 1);
                const kx = track.x + track.width * f;
                var buf: [24]u8 = undefined;
                const label = switch (s.fmt) {
                    .percent => std.fmt.bufPrintSentinel(&buf, "{d}%", .{@as(i32, @intFromFloat(@round(s.ptr.* * 100)))}, 0),
                    .times => std.fmt.bufPrintSentinel(&buf, "{d:.2}x", .{s.ptr.*}, 0),
                    .degrees => std.fmt.bufPrintSentinel(&buf, "{d}", .{@as(i32, @intFromFloat(@round(s.ptr.*)))}, 0),
                } catch "";
                const vs = 32 * u;
                const active = m.drag != null and m.drag.? == i;
                const knob = (if (active) @as(f32, 22.0) else 18.0) * u;

                theme.round(track, track.height / 2, theme.fade(theme.dune, 0.75 * e));
                theme.round(.{ .x = track.x, .y = track.y, .width = @max(track.height, track.width * f), .height = track.height }, track.height / 2, theme.fade(theme.coral, e));
                theme.dot(kx, cy + 4 * u, knob, theme.fade(theme.night, 0.3 * e));
                theme.dot(kx, cy, knob, theme.fade(theme.coral, e));
                theme.dot(kx, cy, knob - 6 * u, theme.fade(theme.cream, e));

                const deg: f32 = if (s.fmt == .degrees) 14 * u else 0;
                const lx = c.x + c.width - theme.measure(theme.heavy, label, vs) - deg;

                theme.write(theme.heavy, label, lx, cy, vs, theme.fade(theme.navy, e));

                if (deg > 0) rl.DrawRing(v2(lx + theme.measure(theme.heavy, label, vs) + 8 * u, cy - 8 * u), 2.5 * u, 5.5 * u, 0, 360, 20, theme.fade(theme.navy, e));
            },
            .toggle => {
                const kn = m.knob[i];
                const tw = 100 * u;
                const th = 52 * u;
                const tx = c.x + c.width - tw;
                const kx = tx + th / 2 + (tw - th) * kn;

                theme.round(.{ .x = tx, .y = cy - th / 2 + 4 * u, .width = tw, .height = th }, th / 2, theme.fade(theme.mix(theme.dune, theme.deep, kn), e));
                theme.round(.{ .x = tx, .y = cy - th / 2, .width = tw, .height = th - 2 * u }, th / 2, theme.fade(theme.mix(.{ .r = 218, .g = 190, .b = 146, .a = 255 }, theme.teal, kn), e));
                theme.dot(kx, cy + 2 * u, th / 2 - 5 * u, theme.fade(theme.night, 0.28 * e));
                theme.dot(kx, cy - 1 * u, th / 2 - 6 * u, theme.fade(theme.cream, e));
                theme.center(theme.heavy, if (kn > 0.5) "ON" else "OFF", tx - 40 * u, cy, 28 * u, theme.fade(if (kn > 0.5) theme.deep else theme.soft, e));
            },
            .choice => |ch| choiceDraw(c, cy, ch.names[@min(ch.ptr.*, ch.names.len - 1)], if (ch.swatch) settings.crosshairColor() else null, e, ch.ptr.*, ch.names.len, true),
            .preset => choiceDraw(c, cy, settings.preset_names[@backingInt(settings.preset)], null, e, @backingInt(settings.preset), 3, false),
            .reset_touch => {
                const bw = 180 * u;
                const r: rl.Rectangle = .{ .x = c.x + c.width - bw, .y = cy - row.height * 0.34, .width = bw, .height = row.height * 0.62 };

                theme.round(theme.offset(r, 0, 5 * u), 16 * u, theme.fade(theme.rust, e));
                theme.round(r, 16 * u, theme.fade(theme.coral, e));
                theme.center(theme.heavy, "RESET", r.x + bw / 2, r.y + r.height / 2, 30 * u, theme.fade(theme.cream, e));
            },
        }
    }
};

fn choiceDraw(c: rl.Rectangle, cy: f32, name: [:0]const u8, swatch: ?rl.Color, e: f32, index: usize, count: usize, wraps: bool) void {
    const u = theme.view().u;
    const sw: f32 = if (swatch != null) 40 * u else 0;
    const box = @min(c.height - 12 * u, 60 * u);
    const size = theme.fit(theme.heavy, name, 32 * u, c.width - box * 2 - sw - 24 * u);
    const nw = theme.measure(theme.heavy, name, size);
    const mid = c.x + c.width / 2;

    for ([_]f32{ c.x, c.x + c.width - box }, 0..) |x, side| {
        const live = wraps or (if (side == 0) index > 0 else index + 1 < count);
        const r: rl.Rectangle = .{ .x = x, .y = cy - box / 2 - 2 * u, .width = box, .height = box };
        const a = (if (live) @as(f32, 1) else 0.35) * e;

        theme.round(theme.offset(r, 0, 5 * u), 16 * u, theme.fade(theme.deep, a));
        theme.round(r, 16 * u, theme.fade(theme.teal, a));
        theme.icon(if (side == 0) .back else .chevron, r.x + box / 2, r.y + box / 2, box * 0.58, theme.fade(theme.cream, a));
    }

    if (swatch) |col| {
        const x = mid - (nw + sw) / 2 + 13 * u;

        theme.dot(x, cy - 5 * u, 15 * u, theme.fade(theme.navy, e));
        theme.dot(x, cy - 5 * u, 11 * u, theme.fade(col, e));
    }

    theme.write(theme.heavy, name, mid - (nw + sw) / 2 + sw, cy - 5 * u, size, theme.fade(theme.navy, e));

    const step = 15 * u;
    const dots_w = @as(f32, @floatFromInt(count)) * step;

    for (0..count) |k| {
        const dx = mid - dots_w / 2 + @as(f32, @floatFromInt(k)) * step + step / 2;

        theme.dot(dx, cy + 21 * u, (if (k == index) @as(f32, 5) else 3.5) * u, theme.fade(if (k == index) theme.coral else theme.dune, e));
    }
}

fn hasPreview(tab: Tab) bool {
    return std.mem.eql(u8, tab.name, "Controller");
}

fn layoutPreview(l: Layout, rows: usize, dy: f32, e: f32) void {
    const u = l.u;
    const top = rowRect(l, rows - 1).y + l.row_h + 6 * u + dy;
    const x = l.rows.x;
    const wdt = l.rows.width;
    const lines = [_][2][:0]const u8{
        .{ "Left stick", "Move" },
        .{ "Right stick", "Look" },
        .{ "RT / LT", "Shoot / Aim" },
        .{ "A", "Jump" },
        .{ "X (hold)", "Reload (pick up)" },
        .{ "RB", "Grenade" },
        .{ "Y", "Enter vehicle" },
        .{ "R3", "Fireball" },
        .{ "D-pad", "Switch weapon" },
        .{ "Start", "Pause" },
    };
    const cols: usize = if (wdt > 1200 * u) 5 else if (wdt > 800 * u) 3 else 2;
    const per_col = (lines.len + cols - 1) / cols;
    const line_h = 38 * u;
    const box_h = @min(l.rows.y + l.rows.height + dy - top, @as(f32, @floatFromInt(per_col)) * line_h + 66 * u);

    if (box_h < 120 * u) return;

    theme.round(.{ .x = x, .y = top, .width = wdt, .height = box_h }, 20 * u, theme.fade(theme.navy, e));
    theme.write(theme.heavy, "BUTTON LAYOUT", x + 28 * u, top + 28 * u, 28 * u, theme.fade(theme.sun, e));

    const col_w = (wdt - 56 * u) / @as(f32, @floatFromInt(cols));

    for (lines, 0..) |ln, i| {
        const cx = x + 28 * u + @as(f32, @floatFromInt(i / per_col)) * col_w;
        const ly = top + 68 * u + @as(f32, @floatFromInt(i % per_col)) * line_h;

        if (ly + 18 * u > top + box_h) continue;

        const ks = 23 * u;
        const kw = theme.measure(theme.heavy, ln[0], ks) + 20 * u;

        theme.round(.{ .x = cx, .y = ly - 16 * u, .width = kw, .height = 32 * u }, 9 * u, theme.fade(theme.cream, e));
        theme.write(theme.heavy, ln[0], cx + 10 * u, ly, ks, theme.fade(theme.navy, e));
        theme.write(theme.body, ln[1], cx + kw + 12 * u, ly, theme.fit(theme.body, ln[1], 25 * u, col_w - kw - 18 * u), theme.fade(theme.cream, e));
    }
}

fn footer(m: *const Menu, l: Layout, dy: f32, e: f32, pad: bool) void {
    const u = l.u;
    const mp = rl.GetMousePosition();
    const touching = theme.view().touch;
    const hint: [:0]const u8 = if (pad) "D-pad select   Left / Right adjust   A toggle   LB / RB tabs   X reset   B back" else if (touching) "Tap to change, drag the sliders" else "Arrows select   Left / Right adjust   Enter toggle   Q / E tabs   Esc back";
    const reset = shift(l.reset, dy);
    const back = shift(l.back, dy);
    const room = reset.x - l.rows.x - 24 * u;

    theme.write(theme.body, hint, l.rows.x + 6 * u, reset.y + reset.height / 2, theme.fit(theme.body, hint, 24 * u, room), theme.fade(theme.soft, e));

    const hot_reset = m.using_mouse and rl.CheckCollisionPointRec(mp, reset);
    const hot_back = m.using_mouse and rl.CheckCollisionPointRec(mp, back);
    const first = theme.button(theme.tag("reset", 0), reset, 20 * u, theme.tones.sand_tone, hot_reset, .{ .a = e });
    const second = theme.button(theme.tag("done", 0), back, 20 * u, theme.tones.coral_tone, hot_back, .{ .a = e });

    theme.center(theme.heavy, if (m.flash > 0) "DONE!" else "RESET ALL", first.face.x + first.face.width / 2, first.face.y + first.face.height / 2, 32 * u, theme.fade(theme.navy, e));
    theme.center(theme.heavy, "BACK", second.face.x + second.face.width / 2, second.face.y + second.face.height / 2, 38 * u, theme.fade(theme.cream, e));
}

fn repeat(timer: *f32, last: *i32, dir: i32, dt: f32) bool {
    if (dir == 0) {
        timer.* = 0;
        last.* = 0;

        return false;
    }

    if (dir != last.*) {
        last.* = dir;
        timer.* = -0.32;

        return true;
    }

    timer.* += dt;

    if (timer.* >= 0.07) {
        timer.* = 0;

        return true;
    }

    return false;
}

fn adjust(it: Item, dir: i32) void {
    switch (it.kind) {
        .slider => |s| {
            s.ptr.* = std.math.clamp(@round((s.ptr.* + s.step * @as(f32, @floatFromInt(dir))) / s.step) * s.step, s.min, s.max);
        },
        .toggle => |b| b.* = !b.*,
        .choice => |c| {
            const n: i32 = @intCast(c.names.len);

            c.ptr.* = @intCast(@mod(@as(i32, c.ptr.*) + dir, n));
        },
        .preset => {
            const cur: i32 = @backingInt(settings.preset);
            const next: i32 = if (settings.preset == .custom) (if (dir > 0) 2 else 1) else @mod(cur + dir, 3);

            settings.applyPreset(@fromBackingInt(@intCast(next)));
        },
        .reset_touch => {
            settings.touch_size = 1;
            settings.touch_opacity = 1;
            settings.touch_look = 1;
            settings.touch_ads = 0.95;
            settings.touch_assist = 0.5;
        },
    }

    if (it.custom) settings.preset = .custom;
}

fn tabsFor(touch_enabled: bool) []const Tab {
    const all = struct {
        const desktop = [_]Tab{
            .{ .name = "Gameplay", .items = &gameplay },
            .{ .name = "Controller", .items = &controller },
            .{ .name = "Graphics", .items = &graphics_desktop },
            .{ .name = "Audio", .items = &audio },
        };
        const mobile = [_]Tab{
            .{ .name = "Gameplay", .items = &gameplay },
            .{ .name = "Controller", .items = &controller },
            .{ .name = "Graphics", .items = &graphics_mobile },
            .{ .name = "Audio", .items = &audio },
            .{ .name = "Touch", .items = &touch },
        };
    };

    if (touch_enabled) return &all.mobile;

    return if (assets.mobile) all.mobile[0..4] else &all.desktop;
}

fn ease(t: f32) f32 {
    const k = 1 - t;

    return 1 - k * k * k;
}

fn shift(r: rl.Rectangle, dy: f32) rl.Rectangle {
    return .{ .x = r.x, .y = r.y + dy, .width = r.width, .height = r.height };
}

const Layout = struct {
    u: f32,
    panel: rl.Rectangle,
    title: rl.Rectangle,
    tabs: rl.Rectangle,
    rows: rl.Rectangle,
    reset: rl.Rectangle,
    back: rl.Rectangle,
    cols: usize,
    per: usize,
    row_h: f32,
};

const Grid = struct {
    cols: usize,
    per: usize,
    height: f32,
};

fn grid(tab: Tab, room: f32, compact: bool) Grid {
    const v = theme.view();
    const count = @min(tab.items.len, max_rows);
    const want = @max(v.tap(76), 76 * v.u);
    const full = @as(f32, @floatFromInt(count)) * want;
    const preview: f32 = if (hasPreview(tab)) 200 * v.u else 0;
    const cols: usize = if (full > room or (compact and full + preview > room)) 2 else 1;
    const per = (count + cols - 1) / cols;

    return .{ .cols = cols, .per = per, .height = @min(room, @as(f32, @floatFromInt(per)) * want + preview) };
}

fn layout(tabs: []const Tab, at: usize) Layout {
    const v = theme.view();
    const u = v.u;
    const compact = v.height() < 840 * u;
    const pw = @min((if (compact) @as(f32, 1560) else 1160) * u, v.width());
    const top = v.top - 14 * u;
    const space = v.h - top - (v.h - v.bottom) + 14 * u;
    const inset = 28 * u;
    const tab_h = v.tap(68);
    const title_w = 300 * u;
    const head = if (compact) 16 * u + tab_h + 14 * u else 24 * u + 68 * u + 18 * u + tab_h + 22 * u;
    const foot_h = v.tap(72);
    const foot = foot_h + (if (compact) 18 * u else 24 * u) + 16 * u;
    const room = @min(860 * u, space) - head - foot;
    var content: f32 = 0;

    for (tabs) |t| content = @max(content, grid(t, room, compact).height);

    const g = grid(tabs[at], room, compact);
    const ph = head + content + foot;
    const px = v.cx() - pw / 2;
    const py = top + (space - ph) / 2;
    const title: rl.Rectangle = .{ .x = px + inset, .y = py + (if (compact) 16 * u else 24 * u), .width = title_w, .height = if (compact) tab_h else 68 * u };
    const tabs_r: rl.Rectangle = if (compact)
        .{ .x = title.x + title_w, .y = title.y, .width = pw - inset * 2 - title_w, .height = tab_h }
    else
        .{ .x = px + inset, .y = title.y + title.height + 18 * u, .width = pw - inset * 2, .height = tab_h };
    const rows: rl.Rectangle = .{ .x = px + inset, .y = py + head, .width = pw - inset * 2, .height = content };
    const foot_y = rows.y + content + 16 * u;
    const row_h = @min(@max(v.tap(76), 76 * u), room / @as(f32, @floatFromInt(g.per)));
    const bw = 210 * u;

    return .{
        .u = u,
        .panel = .{ .x = px, .y = py, .width = pw, .height = ph },
        .title = title,
        .tabs = tabs_r,
        .rows = rows,
        .reset = .{ .x = px + pw - inset - bw * 2 - 18 * u, .y = foot_y, .width = bw, .height = foot_h },
        .back = .{ .x = px + pw - inset - bw, .y = foot_y, .width = bw, .height = foot_h },
        .cols = g.cols,
        .per = g.per,
        .row_h = row_h,
    };
}

fn tabRect(l: Layout, i: usize, n: usize) rl.Rectangle {
    const tw = l.tabs.width / @as(f32, @floatFromInt(n));

    return .{ .x = l.tabs.x + tw * @as(f32, @floatFromInt(i)), .y = l.tabs.y, .width = tw, .height = l.tabs.height };
}

fn rowRect(l: Layout, i: usize) rl.Rectangle {
    const u = l.u;
    const gap = 16 * u;
    const cols: f32 = @floatFromInt(l.cols);
    const cw = (l.rows.width - gap * (cols - 1)) / cols;

    return .{ .x = l.rows.x + (cw + gap) * @as(f32, @floatFromInt(i / l.per)), .y = l.rows.y + l.row_h * @as(f32, @floatFromInt(i % l.per)), .width = cw, .height = l.row_h - 8 * u };
}

fn controlRect(l: Layout, i: usize) rl.Rectangle {
    const u = l.u;
    const row = rowRect(l, i);
    const cw = @min(460 * u, row.width * 0.56);

    return .{ .x = row.x + row.width - cw - 20 * u, .y = row.y, .width = cw, .height = row.height };
}

fn sliderTrack(l: Layout, i: usize) rl.Rectangle {
    const u = l.u;
    const c = controlRect(l, i);
    const cy = c.y + c.height / 2;

    return .{ .x = c.x + 22 * u, .y = cy - 7 * u, .width = c.width - 150 * u, .height = 14 * u };
}

pub fn pauseSlot(i: usize) rl.Rectangle {
    const v = theme.view();
    const u = v.u;
    const gap = 24 * u;
    const bw = @min(310 * u, (v.width() - gap * 3) / 4);
    const bh = v.tap(86);
    const x = v.cx() - (bw * 4 + gap * 3) / 2;

    return .{ .x = x + (bw + gap) * @as(f32, @floatFromInt(i)), .y = v.bottom - bh - 8 * u, .width = bw, .height = bh };
}

pub fn homeRect() rl.Rectangle {
    return pauseSlot(2);
}

pub fn quitRect() rl.Rectangle {
    return pauseSlot(3);
}

pub fn wantsHome(pad: ?c_int) bool {
    if (rl.IsKeyPressed(rl.KEY_M)) return true;

    if (pad) |id| {
        if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_TRIGGER_1)) return true;
    }

    return rl.IsMouseButtonPressed(rl.MOUSE_BUTTON_LEFT) and rl.CheckCollisionPointRec(rl.GetMousePosition(), homeRect());
}

pub fn wantsQuit(pad: ?c_int) bool {
    if (rl.IsKeyPressed(rl.KEY_F10)) return true;

    if (pad) |id| {
        if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_FACE_LEFT)) return true;
    }

    return rl.IsMouseButtonPressed(rl.MOUSE_BUTTON_LEFT) and rl.CheckCollisionPointRec(rl.GetMousePosition(), quitRect());
}

pub fn drawQuit(pad: bool, fade: f32) void {
    pauseButton(2, homeRect(), .home, "MAIN MENU", if (pad) "R1" else "M", theme.tones.cream_tone, fade);
    pauseButton(3, quitRect(), .exit, "EXIT GAME", if (pad) "X" else "F10", theme.tones.sand_tone, fade);
}

pub fn pauseButton(slot: usize, r: rl.Rectangle, icon: theme.Icon, label: [:0]const u8, hint: [:0]const u8, tone: theme.Tone, fade: f32) void {
    const v = theme.view();
    const u = v.u;
    const a = std.math.clamp(1 - fade, 0, 1);
    const b = theme.button(theme.tag("pause", slot), r, 22 * u, tone, rl.CheckCollisionPointRec(rl.GetMousePosition(), r), .{ .a = a });
    const f = b.face;
    const mid = f.y + f.height / 2;
    const keys = !v.touch;
    const ks = 20 * u;
    const kw = if (keys) theme.measure(theme.heavy, hint, ks) + 18 * u else 0;
    const art = 40 * u;
    const size = theme.fit(theme.heavy, label, 36 * u, f.width - art - kw - 50 * u);
    const total = art + 10 * u + theme.measure(theme.heavy, label, size);
    const x = f.x + (f.width - kw - total) / 2;

    theme.icon(icon, x + art / 2, mid, art, theme.fade(tone.ink, a));
    theme.write(theme.heavy, label, x + art + 10 * u, mid, size, theme.fade(tone.ink, a));

    if (!keys) return;

    const key: rl.Rectangle = .{ .x = f.x + f.width - kw - 12 * u, .y = mid - 16 * u, .width = kw, .height = 32 * u };

    theme.round(key, 9 * u, theme.fade(theme.navy, 0.14 * a));
    theme.center(theme.heavy, hint, key.x + kw / 2, mid, ks, theme.fade(tone.ink, 0.8 * a));
}

pub fn gearRect() rl.Rectangle {
    return pauseSlot(1);
}
