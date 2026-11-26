const std = @import("std");
const rl = @import("raylib");
const ui = @import("ui.zig");
const settings = @import("settings.zig");
const assets = @import("assets.zig");

const v2 = ui.v2;

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
        const l = layout();
        const tabs = tabsFor(m.touch_enabled);

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
            const row = rowRect(l, i);

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

    pub fn drawGear(m: *const Menu, font: rl.Font, pad: bool) void {
        if (m.t > 0.99) return;

        const r = gearRect();
        const u = unit();
        const mp = rl.GetMousePosition();
        const hot = rl.CheckCollisionPointRec(mp, r);
        const a = 1 - m.t;
        const label: [:0]const u8 = "SETTINGS";
        const hint: [:0]const u8 = if (pad) "Y" else "TAB";
        const size = 22 * u;

        rl.DrawRectangleRounded(.{ .x = r.x + 3 * u, .y = r.y + 5 * u, .width = r.width, .height = r.height }, 0.5, 12, ui.fade(ui.ink, 0.35 * a));
        rl.DrawRectangleRounded(r, 0.5, 12, ui.fade(if (hot) ui.white else ui.ink, (if (hot) @as(f32, 0.95) else 0.82) * a));
        gearIcon(r.x + 34 * u, r.y + r.height / 2, 12 * u, ui.fade(if (hot) ui.ink else ui.yellow, a));
        ui.text(font, label, r.x + 58 * u, r.y + r.height / 2 - size / 2, size, ui.fade(if (hot) ui.ink else ui.white, a));

        const kx = r.x + r.width - 18 * u - ui.width(font, hint, 15 * u) - 14 * u;
        const kw = ui.width(font, hint, 15 * u) + 14 * u;

        rl.DrawRectangleRounded(.{ .x = kx, .y = r.y + r.height / 2 - 13 * u, .width = kw, .height = 26 * u }, 0.4, 8, ui.fade(if (hot) ui.ink else ui.white, 0.16 * a));
        ui.text(font, hint, kx + 7 * u, r.y + r.height / 2 - 8 * u, 15 * u, ui.fade(if (hot) ui.ink else ui.white, 0.75 * a));
    }

    pub fn draw(m: *const Menu, font: rl.Font, pad: bool) void {
        if (m.t <= 0.001) return;

        const w: f32 = @floatFromInt(rl.GetScreenWidth());
        const h: f32 = @floatFromInt(rl.GetScreenHeight());
        const u = unit();
        const e = ease(m.t);
        const l = layout();
        const tabs = tabsFor(m.touch_enabled);
        const items = tabs[m.tab].items;
        const lift = (1 - e) * 28 * u;
        const p = rl.Rectangle{ .x = l.panel.x, .y = l.panel.y + lift, .width = l.panel.width, .height = l.panel.height };
        const dy = lift;

        rl.DrawRectangle(0, 0, @intFromFloat(w), @intFromFloat(h), ui.fade(ui.ink, 0.5 * e));
        rl.DrawRectangleRounded(.{ .x = p.x + 6 * u, .y = p.y + 14 * u, .width = p.width, .height = p.height }, 0.06, 16, ui.fade(ui.rgba(6, 8, 16, 255), 0.45 * e));
        rl.DrawRectangleRounded(p, 0.06, 16, ui.fade(ui.rgba(30, 35, 56, 255), e));
        rl.DrawRectangleRounded(.{ .x = p.x, .y = p.y, .width = p.width, .height = 108 * u }, 0.35, 16, ui.fade(ui.rgba(40, 46, 72, 255), e));
        rl.DrawRectangle(@intFromFloat(p.x), @intFromFloat(p.y + 70 * u), @intFromFloat(p.width), @intFromFloat(38 * u), ui.fade(ui.rgba(40, 46, 72, 255), e));
        rl.DrawRectangle(@intFromFloat(p.x + 28 * u), @intFromFloat(p.y + 108 * u), @intFromFloat(p.width - 56 * u), @intFromFloat(@max(1, 1.5 * u)), ui.fade(ui.white, 0.08 * e));

        gearIcon(p.x + 46 * u, p.y + 38 * u, 14 * u, ui.fade(ui.yellow, e));
        ui.caps(font, "SETTINGS", p.x + 72 * u, p.y + 22 * u, 36 * u, ui.fade(ui.white, e));

        for (tabs, 0..) |tab, i| {
            const r = shift(tabRect(l, i, tabs.len), dy);
            const active = i == m.tab;
            const size = 19 * u;
            const tw = ui.width(font, tab.name, size);
            const hot = m.using_mouse and rl.CheckCollisionPointRec(rl.GetMousePosition(), r);

            if (hot and !active) rl.DrawRectangleRounded(r, 0.5, 10, ui.fade(ui.white, 0.08 * e));

            ui.text(font, tab.name, r.x + r.width / 2 - tw / 2, r.y + r.height / 2 - size / 2 - 2 * u, size, ui.fade(ui.white, (if (active) @as(f32, 1.0) else 0.55) * e));
        }

        const from = shift(tabRect(l, @intFromFloat(@floor(m.slide)), tabs.len), dy);
        const to = shift(tabRect(l, @min(tabs.len - 1, @as(usize, @intFromFloat(@ceil(m.slide)))), tabs.len), dy);
        const k = m.slide - @floor(m.slide);
        const ux = from.x + (to.x - from.x) * k;
        const uw = from.width + (to.width - from.width) * k;

        rl.DrawRectangleRounded(.{ .x = ux + 14 * u, .y = from.y + from.height - 5 * u, .width = uw - 28 * u, .height = 4 * u }, 1, 8, ui.fade(ui.yellow, e));

        for (items[0..@min(items.len, max_rows)], 0..) |it, i| m.drawRow(font, l, it, i, dy, e);

        if (std.mem.eql(u8, tabs[m.tab].name, "Controller")) layoutPreview(font, l, controller.len, dy, e);

        footer(m, font, l, dy, e, pad);
    }

    fn drawRow(m: *const Menu, font: rl.Font, l: Layout, it: Item, i: usize, dy: f32, e: f32) void {
        const u = unit();
        const row = shift(rowRect(l, i), dy);
        const g = m.glow[i];
        const size = 21 * u;
        const cy = row.y + row.height / 2;

        if (g > 0.01) {
            rl.DrawRectangleRounded(row, 0.3, 10, ui.fade(ui.white, 0.07 * g * e));
            rl.DrawRectangleRounded(.{ .x = row.x, .y = row.y + 10 * u, .width = 4 * u, .height = row.height - 20 * u }, 1, 6, ui.fade(ui.yellow, g * e));
        }

        if (it.note) |note| {
            ui.text(font, it.label, row.x + 22 * u, cy - size + 1 * u, size, ui.fade(ui.white, e));
            ui.text(font, note, row.x + 22 * u, cy + 3 * u, 14 * u, ui.fade(ui.white, 0.45 * e));
        } else {
            ui.text(font, it.label, row.x + 22 * u, cy - size / 2 - 1 * u, size, ui.fade(ui.white, e));
        }

        const c = shift(controlRect(l, i), dy);

        switch (it.kind) {
            .slider => |s| {
                const track = shift(sliderTrack(l, i), dy);
                const f = (s.ptr.* - s.min) / (s.max - s.min);
                const kx = track.x + track.width * f;
                var buf: [24]u8 = undefined;
                const label = switch (s.fmt) {
                    .percent => std.fmt.bufPrintSentinel(&buf, "{d}%", .{@as(i32, @intFromFloat(@round(s.ptr.* * 100)))}, 0),
                    .times => std.fmt.bufPrintSentinel(&buf, "{d:.2}x", .{s.ptr.*}, 0),
                    .degrees => std.fmt.bufPrintSentinel(&buf, "{d}", .{@as(i32, @intFromFloat(@round(s.ptr.*)))}, 0),
                } catch "";
                const vs = 18 * u;
                const active = m.drag != null and m.drag.? == i;

                rl.DrawRectangleRounded(track, 1, 8, ui.fade(ui.white, 0.14 * e));
                rl.DrawRectangleRounded(.{ .x = track.x, .y = track.y, .width = @max(track.height, track.width * f), .height = track.height }, 1, 8, ui.fade(ui.yellow, e));
                rl.DrawCircleV(v2(kx + 1.5 * u, cy + 2.5 * u), (if (active) @as(f32, 13.0) else 11.0) * u, ui.fade(ui.ink, 0.4 * e));
                rl.DrawCircleV(v2(kx, cy), (if (active) @as(f32, 13.0) else 11.0) * u, ui.fade(ui.white, e));
                const deg: f32 = if (s.fmt == .degrees) 9 * u else 0;
                const lx = c.x + c.width - ui.width(font, label, vs) - deg;

                ui.text(font, label, lx, cy - vs / 2 - 1 * u, vs, ui.fade(ui.white, 0.85 * e));

                if (deg > 0) rl.DrawRing(v2(lx + ui.width(font, label, vs) + 5 * u, cy - vs / 2 + 3 * u), 2 * u, 3.6 * u, 0, 360, 16, ui.fade(ui.white, 0.85 * e));
            },
            .toggle => {
                const kn = m.knob[i];
                const tw = 66 * u;
                const th = 34 * u;
                const tx = c.x + c.width - tw;
                const on_col = ui.rgba(92, 214, 120, 255);
                const off_col = ui.rgba(255, 255, 255, 46);
                const col = rl.Color{
                    .r = lerpU8(off_col.r, on_col.r, kn),
                    .g = lerpU8(off_col.g, on_col.g, kn),
                    .b = lerpU8(off_col.b, on_col.b, kn),
                    .a = lerpU8(off_col.a, on_col.a, kn),
                };
                const kx = tx + th / 2 + (tw - th) * kn;

                rl.DrawRectangleRounded(.{ .x = tx, .y = cy - th / 2, .width = tw, .height = th }, 1, 12, ui.fade(col, e));
                rl.DrawCircleV(v2(kx + 1 * u, cy + 2 * u), th / 2 - 4 * u, ui.fade(ui.ink, 0.35 * e));
                rl.DrawCircleV(v2(kx, cy), th / 2 - 4 * u, ui.fade(ui.white, e));
            },
            .choice => |ch| choiceDraw(font, c, cy, ch.names[@min(ch.ptr.*, ch.names.len - 1)], if (ch.swatch) settings.crosshairColor() else null, e, ch.ptr.*, ch.names.len),
            .preset => choiceDraw(font, c, cy, settings.preset_names[@intFromEnum(settings.preset)], null, e, @intFromEnum(settings.preset), 3),
            .reset_touch => {
                const bw = 120 * u;
                const r = rl.Rectangle{ .x = c.x + c.width - bw, .y = cy - 18 * u, .width = bw, .height = 36 * u };
                const s2 = 17 * u;

                rl.DrawRectangleRounded(r, 0.5, 10, ui.fade(ui.white, 0.14 * e));
                ui.text(font, "Reset", r.x + bw / 2 - ui.width(font, "Reset", s2) / 2, cy - s2 / 2 - 1 * u, s2, ui.fade(ui.white, e));
            },
        }
    }
};

fn lerpU8(a: u8, b: u8, t: f32) u8 {
    const fa: f32 = @floatFromInt(a);
    const fb: f32 = @floatFromInt(b);

    return @intFromFloat(std.math.clamp(fa + (fb - fa) * t, 0, 255));
}

fn choiceDraw(font: rl.Font, c: rl.Rectangle, cy: f32, name: [:0]const u8, swatch: ?rl.Color, e: f32, index: usize, count: usize) void {
    const u = unit();
    const size = 19 * u;
    const nw = ui.width(font, name, size);
    const sw: f32 = if (swatch != null) 24 * u else 0;
    const mid = c.x + c.width / 2;

    arrow(c.x + 12 * u, cy, -1, 7 * u, ui.fade(ui.white, (if (index > 0) @as(f32, 0.8) else 0.25) * e));
    arrow(c.x + c.width - 12 * u, cy, 1, 7 * u, ui.fade(ui.white, (if (index + 1 < count) @as(f32, 0.8) else 0.25) * e));

    if (swatch) |col| {
        rl.DrawCircleV(v2(mid - (nw + sw) / 2 + 8 * u, cy), 8 * u, ui.fade(ui.ink, 0.5 * e));
        rl.DrawCircleV(v2(mid - (nw + sw) / 2 + 8 * u, cy), 6.5 * u, ui.fade(col, e));
    }

    ui.text(font, name, mid - (nw + sw) / 2 + sw, cy - size / 2 - 1 * u, size, ui.fade(ui.white, e));

    const dots_w = @as(f32, @floatFromInt(count)) * 12 * u;

    for (0..count) |k| {
        const dx = mid - dots_w / 2 + @as(f32, @floatFromInt(k)) * 12 * u + 6 * u;

        rl.DrawCircleV(v2(dx, cy + 19 * u), 2.4 * u, ui.fade(ui.white, (if (k == index) @as(f32, 0.9) else 0.22) * e));
    }
}

fn arrow(x: f32, y: f32, dir: f32, s: f32, col: rl.Color) void {
    if (dir < 0) {
        rl.DrawTriangle(v2(x - s * 0.6, y), v2(x + s * 0.5, y + s), v2(x + s * 0.5, y - s), col);
    } else {
        rl.DrawTriangle(v2(x + s * 0.6, y), v2(x - s * 0.5, y - s), v2(x - s * 0.5, y + s), col);
    }
}

fn gearIcon(x: f32, y: f32, r: f32, col: rl.Color) void {
    var k: f32 = 0;

    while (k < 8) : (k += 1) {
        const a = k * std.math.pi / 4;
        const d = v2(@cos(a), @sin(a));

        rl.DrawLineEx(v2(x + d.x * r * 0.55, y + d.y * r * 0.55), v2(x + d.x * r * 1.05, y + d.y * r * 1.05), r * 0.42, col);
    }

    rl.DrawCircleV(v2(x, y), r * 0.82, col);
    rl.DrawCircleV(v2(x, y), r * 0.34, ui.ink);
}

fn layoutPreview(font: rl.Font, l: Layout, rows: usize, dy: f32, e: f32) void {
    const u = unit();
    const top = rowRect(l, rows).y + 14 * u + dy;
    const x = l.rows.x;
    const wdt = l.rows.width;
    const lines = [_][2][:0]const u8{
        .{ "Left stick", "Move" },
        .{ "Right stick", "Look" },
        .{ "RT / LT", "Shoot / Aim" },
        .{ "A", "Jump" },
        .{ "X  (hold)", "Reload  (pick up)" },
        .{ "RB", "Grenade" },
        .{ "Y", "Enter vehicle" },
        .{ "R3", "Fireball" },
        .{ "D-pad", "Switch weapon" },
        .{ "Start", "Pause" },
    };
    const box_h = @min(l.panel.y + l.panel.height - 86 * u + dy - top, 5 * 34 * u + 46 * u);

    if (box_h < 80 * u) return;

    rl.DrawRectangleRounded(.{ .x = x, .y = top, .width = wdt, .height = box_h }, 0.08, 10, ui.fade(ui.ink, 0.45 * e));
    ui.text(font, "Button layout", x + 22 * u, top + 12 * u, 15 * u, ui.fade(ui.yellow, 0.9 * e));

    const col_w = (wdt - 44 * u) / 2;
    const per_col = (lines.len + 1) / 2;

    for (lines, 0..) |ln, i| {
        const cx = x + 22 * u + @as(f32, @floatFromInt(i / per_col)) * col_w;
        const ly = top + 40 * u + @as(f32, @floatFromInt(i % per_col)) * 26 * u;

        if (ly + 20 * u > top + box_h) continue;

        const ks = 15 * u;
        const kw = ui.width(font, ln[0], ks) + 14 * u;

        rl.DrawRectangleRounded(.{ .x = cx, .y = ly - 2 * u, .width = kw, .height = 22 * u }, 0.4, 8, ui.fade(ui.white, 0.14 * e));
        ui.text(font, ln[0], cx + 7 * u, ly + 1 * u, ks, ui.fade(ui.white, 0.9 * e));
        ui.text(font, ln[1], cx + kw + 10 * u, ly + 1 * u, ks, ui.fade(ui.white, 0.6 * e));
    }
}

fn footer(m: *const Menu, font: rl.Font, l: Layout, dy: f32, e: f32, pad: bool) void {
    const u = unit();
    const mp = rl.GetMousePosition();
    const hint: [:0]const u8 = if (pad) "D-pad select    Left / Right adjust    A toggle    LB / RB tabs    X reset    B back" else if (assets.mobile) "Tap to change    Drag sliders" else "Arrows select    Left / Right adjust    Enter toggle    Q / E tabs    Esc back";
    const hs = 15 * u;
    const reset = shift(l.reset, dy);
    const back = shift(l.back, dy);

    ui.text(font, hint, l.panel.x + 30 * u, reset.y + reset.height / 2 - hs / 2, hs, ui.fade(ui.white, 0.45 * e));

    for ([_]struct { r: rl.Rectangle, label: [:0]const u8, primary: bool }{ .{ .r = reset, .label = if (m.flash > 0) "Done!" else "Reset all", .primary = false }, .{ .r = back, .label = "Back", .primary = true } }) |b| {
        const hot = m.using_mouse and rl.CheckCollisionPointRec(mp, b.r);
        const bg = if (b.primary) ui.yellow else ui.white;
        const alpha: f32 = if (b.primary) (if (hot) @as(f32, 1.0) else 0.92) else (if (hot) @as(f32, 0.22) else 0.12);
        const s = 18 * u;
        const tc = if (b.primary) ui.ink else ui.white;

        rl.DrawRectangleRounded(b.r, 0.5, 10, ui.fade(bg, alpha * e));

        const tw = ui.width(font, b.label, s);

        rl.DrawTextEx(font, b.label.ptr, v2(b.r.x + b.r.width / 2 - tw / 2, b.r.y + b.r.height / 2 - s / 2 - 1 * u), s, 0.5, ui.fade(tc, e));
    }
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
            const cur: i32 = @intFromEnum(settings.preset);
            const next: i32 = if (settings.preset == .custom) (if (dir > 0) 2 else 1) else @mod(cur + dir, 3);

            settings.applyPreset(@enumFromInt(next));
        },
        .reset_touch => {
            settings.touch_size = 1;
            settings.touch_opacity = 1;
            settings.touch_look = 1;
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

fn unit() f32 {
    const w: f32 = @floatFromInt(rl.GetScreenWidth());
    const h: f32 = @floatFromInt(rl.GetScreenHeight());

    return @min(h / 900, w / 1500);
}

fn ease(t: f32) f32 {
    const k = 1 - t;

    return 1 - k * k * k;
}

fn shift(r: rl.Rectangle, dy: f32) rl.Rectangle {
    return .{ .x = r.x, .y = r.y + dy, .width = r.width, .height = r.height };
}

const Layout = struct {
    panel: rl.Rectangle,
    rows: rl.Rectangle,
    reset: rl.Rectangle,
    back: rl.Rectangle,
};

fn layout() Layout {
    const w: f32 = @floatFromInt(rl.GetScreenWidth());
    const h: f32 = @floatFromInt(rl.GetScreenHeight());
    const u = unit();
    const pw = @min(1000 * u, w - 40 * u);
    const ph = @min(760 * u, h - 40 * u);
    const px = (w - pw) / 2;
    const py = (h - ph) / 2;

    return .{
        .panel = .{ .x = px, .y = py, .width = pw, .height = ph },
        .rows = .{ .x = px + 28 * u, .y = py + 128 * u, .width = pw - 56 * u, .height = ph - 128 * u - 84 * u },
        .reset = .{ .x = px + pw - 28 * u - 140 * u - 14 * u - 140 * u, .y = py + ph - 66 * u, .width = 140 * u, .height = 44 * u },
        .back = .{ .x = px + pw - 28 * u - 140 * u, .y = py + ph - 66 * u, .width = 140 * u, .height = 44 * u },
    };
}

fn tabRect(l: Layout, i: usize, n: usize) rl.Rectangle {
    const u = unit();
    const start = l.panel.x + 380 * u;
    const avail = l.panel.x + l.panel.width - 28 * u - start;
    const tw = avail / @as(f32, @floatFromInt(n));

    return .{ .x = start + tw * @as(f32, @floatFromInt(i)), .y = l.panel.y + 22 * u, .width = tw, .height = 56 * u };
}

fn rowRect(l: Layout, i: usize) rl.Rectangle {
    const u = unit();
    const rh = 64 * u;

    return .{ .x = l.rows.x, .y = l.rows.y + rh * @as(f32, @floatFromInt(i)), .width = l.rows.width, .height = rh - 6 * u };
}

fn controlRect(l: Layout, i: usize) rl.Rectangle {
    const u = unit();
    const row = rowRect(l, i);
    const cw = 380 * u;

    return .{ .x = row.x + row.width - cw - 22 * u, .y = row.y, .width = cw, .height = row.height };
}

fn sliderTrack(l: Layout, i: usize) rl.Rectangle {
    const u = unit();
    const c = controlRect(l, i);
    const cy = c.y + c.height / 2;

    return .{ .x = c.x + 10 * u, .y = cy - 4 * u, .width = c.width - 100 * u, .height = 8 * u };
}

fn slotRect(slot: f32) rl.Rectangle {
    const g = gearRect();
    const u = unit();

    return .{ .x = g.x, .y = g.y + (g.height + 14 * u) * slot, .width = g.width, .height = g.height };
}

pub fn homeRect() rl.Rectangle {
    return slotRect(2);
}

pub fn quitRect() rl.Rectangle {
    return slotRect(3);
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

pub fn drawQuit(font: rl.Font, pad: bool, fade: f32) void {
    pauseButton(font, homeRect(), "MAIN MENU", if (pad) "R1" else "M", fade);
    pauseButton(font, quitRect(), "EXIT GAME", if (pad) "X" else "F10", fade);
}

fn pauseButton(font: rl.Font, r: rl.Rectangle, label: [:0]const u8, hint: [:0]const u8, fade: f32) void {
    const u = unit();
    const hot = rl.CheckCollisionPointRec(rl.GetMousePosition(), r);
    const size = 22 * u;
    const a = 1 - fade;

    rl.DrawRectangleRounded(.{ .x = r.x + 3 * u, .y = r.y + 5 * u, .width = r.width, .height = r.height }, 0.5, 12, ui.fade(ui.ink, 0.35 * a));
    rl.DrawRectangleRounded(r, 0.5, 12, ui.fade(if (hot) ui.white else ui.ink, (if (hot) @as(f32, 0.95) else 0.82) * a));
    ui.text(font, label, r.x + 30 * u, r.y + r.height / 2 - size / 2, size, ui.fade(if (hot) ui.ink else ui.white, a));

    const kw = ui.width(font, hint, 15 * u) + 14 * u;
    const kx = r.x + r.width - 18 * u - kw;

    rl.DrawRectangleRounded(.{ .x = kx, .y = r.y + r.height / 2 - 13 * u, .width = kw, .height = 26 * u }, 0.4, 8, ui.fade(if (hot) ui.ink else ui.white, 0.16 * a));
    ui.text(font, hint, kx + 7 * u, r.y + r.height / 2 - 8 * u, 15 * u, ui.fade(if (hot) ui.ink else ui.white, 0.75 * a));
}

pub fn gearRect() rl.Rectangle {
    const w: f32 = @floatFromInt(rl.GetScreenWidth());
    const h: f32 = @floatFromInt(rl.GetScreenHeight());
    const u = unit();
    const bw = 250 * u;

    return .{ .x = w / 2 - bw / 2, .y = h / 2 + 120 * u, .width = bw, .height = 54 * u };
}
