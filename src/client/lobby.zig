const std = @import("std");
const builtin = @import("builtin");
const rl = @import("raylib");
const shared = @import("shared");
const net = @import("net.zig");
const mapselect = @import("mapselect.zig");
const game_mod = @import("game.zig");
const audio = @import("audio.zig");
const theme = @import("theme.zig");
const backdrop = @import("backdrop.zig");
const menu_mod = @import("menu.zig");

const Map = shared.terrain.Map;
const net_shared = shared.net;
const View = theme.View;
const tones = theme.tones;

const Screen = enum { home, difficulty, name, online, join, connecting, code };

const Home = enum { play, online, settings, exit };

const Option = struct {
    name: [:0]const u8,
    note: [:0]const u8,
    tint: rl.Color,
    edge: rl.Color,
    art: Art,
};

const Art = union(enum) {
    bars: usize,
    icon: theme.Icon,
};

const difficulty_options = [_]Option{
    .{ .name = "EASY", .note = "Slow bots, loose aim", .tint = theme.leaf, .edge = theme.moss, .art = .{ .bars = 1 } },
    .{ .name = "NORMAL", .note = "The usual fight", .tint = theme.sun, .edge = theme.amber, .art = .{ .bars = 2 } },
    .{ .name = "HARD", .note = "Fast, tough and accurate", .tint = theme.brick, .edge = theme.clay, .art = .{ .bars = 3 } },
};

const online_options = [_]Option{
    .{ .name = "CREATE ROOM", .note = "Pick a map, share the code", .tint = theme.coral, .edge = theme.rust, .art = .{ .icon = .flag } },
    .{ .name = "JOIN ROOM", .note = "Type a friend's 3 digit code", .tint = theme.teal, .edge = theme.deep, .art = .{ .icon = .join } },
};

const keypad = [_][:0]const u8{ "1", "2", "3", "4", "5", "6", "7", "8", "9", "DEL", "0", "JOIN" };

const KeyAction = enum { char, shift, space, erase, done };

const Key = struct {
    label: [:0]const u8,
    row: u8,
    col: u8,
    span: u8 = 1,
    action: KeyAction = .char,
};

const key_rows = [_][]const u8{ "1234567890", "QWERTYUIOP", "ASDFGHJKL-", "ZXCVBNM._!" };
const key_cols = 10;

const keyboard = blk: {
    var keys: [44]Key = undefined;
    var n: usize = 0;

    for (key_rows, 0..) |row, r| {
        for (row, 0..) |ch, col| {
            keys[n] = .{ .label = &[_:0]u8{ch}, .row = @intCast(r), .col = @intCast(col) };
            n += 1;
        }
    }

    keys[n] = .{ .label = "SHIFT", .row = 4, .col = 0, .span = 2, .action = .shift };
    keys[n + 1] = .{ .label = "SPACE", .row = 4, .col = 2, .span = 4, .action = .space };
    keys[n + 2] = .{ .label = "DEL", .row = 4, .col = 6, .span = 2, .action = .erase };
    keys[n + 3] = .{ .label = "DONE", .row = 4, .col = 8, .span = 2, .action = .done };

    break :blk keys;
};

const done_key = keyboard.len - 1;

const NameEntry = struct {
    text: [net_shared.name_len]u8 = @splat(0),
    len: usize = 0,
    upper: bool = true,
    focus: usize = 0,
    age: f32 = 0,

    fn load(e: *NameEntry) void {
        const n = net.defaultName();

        e.text = n;
        e.len = net_shared.nameSlice(&n).len;
        e.upper = e.len == 0;
        e.focus = done_key;
        e.age = 0;
    }

    fn put(e: *NameEntry, ch: u8) void {
        if (e.len >= e.text.len or ch < 32 or ch >= 127) return;

        if (ch == ' ' and e.len == 0) return;

        var c = ch;

        if (std.ascii.isAlphabetic(c)) c = if (e.upper) std.ascii.toUpper(c) else std.ascii.toLower(c);

        e.text[e.len] = c;
        e.len += 1;

        if (std.ascii.isAlphabetic(c)) e.upper = false;
    }

    fn typed(e: *NameEntry, ch: u8) void {
        if (e.len >= e.text.len or ch < 32 or ch >= 127) return;

        if (ch == ' ' and e.len == 0) return;

        e.text[e.len] = ch;
        e.len += 1;
        e.upper = false;
    }

    fn erase(e: *NameEntry) void {
        if (e.len == 0) return;

        e.len -= 1;
        e.text[e.len] = 0;

        if (e.len == 0) e.upper = true;
    }

    fn ready(e: NameEntry) bool {
        return std.mem.trim(u8, e.text[0..e.len], " ").len > 0;
    }

    fn move(e: *NameEntry, dx: i32, dy: i32) void {
        const k = keyboard[e.focus];

        if (dx != 0) {
            var i: i32 = @intCast(e.focus);

            while (true) {
                i = @mod(i + dx, @as(i32, keyboard.len));

                if (keyboard[@intCast(i)].row == k.row) break;
            }

            e.focus = @intCast(i);
        }

        if (dy != 0) {
            const rows: i32 = key_rows.len + 1;
            const row: u8 = @intCast(@mod(@as(i32, k.row) + dy, rows));
            const center = @as(f32, @floatFromInt(k.col)) + @as(f32, @floatFromInt(k.span)) / 2;

            for (keyboard, 0..) |o, i| {
                if (o.row != row) continue;

                if (center >= @as(f32, @floatFromInt(o.col)) and center < @as(f32, @floatFromInt(o.col + o.span))) {
                    e.focus = i;

                    return;
                }
            }
        }
    }

    fn press(e: *NameEntry, i: usize) bool {
        const k = keyboard[i];

        switch (k.action) {
            .char => e.put(k.label[0]),
            .shift => e.upper = !e.upper,
            .space => e.put(' '),
            .erase => e.erase(),
            .done => return e.ready(),
        }

        return false;
    }
};

const Input = struct {
    dx: i32 = 0,
    dy: i32 = 0,
    ok: bool = false,
    back: bool = false,
    erase: bool = false,
    digit: ?u8 = null,
    enter: bool = false,
    start: bool = false,
    shift: bool = false,
};

var cool: f32 = 0;
var name_draw: [32]u8 = undefined;

fn padId() ?c_int {
    var i: c_int = 0;

    while (i < 4) : (i += 1) {
        if (rl.IsGamepadAvailable(i) and rl.GetGamepadAxisCount(i) >= 4) return i;
    }

    return null;
}

fn readInput(dt: f32, typing: bool) Input {
    var in: Input = .{};

    cool = @max(0, cool - dt);

    if (rl.IsKeyPressed(rl.KEY_RIGHT) or (!typing and rl.IsKeyPressed(rl.KEY_D))) in.dx = 1;
    if (rl.IsKeyPressed(rl.KEY_LEFT) or (!typing and rl.IsKeyPressed(rl.KEY_A))) in.dx = -1;
    if (rl.IsKeyPressed(rl.KEY_DOWN) or (!typing and rl.IsKeyPressed(rl.KEY_S))) in.dy = 1;
    if (rl.IsKeyPressed(rl.KEY_UP) or (!typing and rl.IsKeyPressed(rl.KEY_W))) in.dy = -1;
    if (rl.IsKeyPressed(rl.KEY_ENTER) or rl.IsKeyPressed(rl.KEY_KP_ENTER) or (!typing and rl.IsKeyPressed(rl.KEY_SPACE))) in.ok = true;
    if (rl.IsKeyPressed(rl.KEY_ENTER) or rl.IsKeyPressed(rl.KEY_KP_ENTER)) in.enter = true;
    if (rl.IsKeyPressed(rl.KEY_ESCAPE) or rl.IsKeyPressed(rl.KEY_BACK)) in.back = true;
    if (rl.IsKeyPressed(rl.KEY_BACKSPACE) or rl.IsKeyPressed(rl.KEY_DELETE)) in.erase = true;

    var k: u8 = 0;

    while (k < 10 and !typing) : (k += 1) {
        if (rl.IsKeyPressed(rl.KEY_ZERO + @as(c_int, k)) or rl.IsKeyPressed(rl.KEY_KP_0 + @as(c_int, k))) in.digit = k;
    }

    if (padId()) |id| {
        const ax = rl.GetGamepadAxisMovement(id, rl.GAMEPAD_AXIS_LEFT_X);
        const ay = rl.GetGamepadAxisMovement(id, rl.GAMEPAD_AXIS_LEFT_Y);

        if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_LEFT_FACE_RIGHT) or (ax > 0.6 and cool == 0)) in.dx = 1;
        if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_LEFT_FACE_LEFT) or (ax < -0.6 and cool == 0)) in.dx = -1;
        if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_LEFT_FACE_DOWN) or (ay > 0.6 and cool == 0)) in.dy = 1;
        if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_LEFT_FACE_UP) or (ay < -0.6 and cool == 0)) in.dy = -1;
        if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_FACE_DOWN) or rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_MIDDLE_RIGHT)) in.ok = true;
        if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_FACE_RIGHT)) in.back = true;
        if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_FACE_LEFT)) in.erase = true;
        if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_MIDDLE_RIGHT)) in.start = true;
        if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_FACE_UP)) in.shift = true;

        if ((@abs(ax) > 0.6 or @abs(ay) > 0.6) and cool == 0) cool = 0.22;
    }

    return in;
}

fn mapName(m: u8) [:0]const u8 {
    if (m >= std.enums.values(Map).len) return "unknown";

    return @tagName(@as(Map, @fromBackingInt(@intCast(m))));
}

fn reasonText(r: shared.net.Reason) [:0]const u8 {
    return switch (r) {
        .no_room => "No room with that code",
        .full => "That room is full",
        .bad_version => "Server runs a different game version",
        .bad_map => "Server does not know this map",
        .busy => "Server is busy, try again",
        _ => "Server refused",
    };
}

fn footer(v: View, keys: []const theme.Hint, pad: []const theme.Hint) void {
    if (!v.keyed()) return;

    const items = if (theme.pad_live) pad else keys;
    const size = 19 * v.u;

    theme.hints(items, v.cx() - theme.hintsWidth(items, size) / 2, v.bottom - 16 * v.u, size, theme.reveal(4).a);
}

fn bodyTop(v: View) f32 {
    return v.top + theme.headerHeight(v) + 22 * v.u;
}

fn bodyBottom(v: View) f32 {
    return v.bottom - (if (v.keyed()) 52 * v.u else 0);
}

fn wide(key: u32, r: rl.Rectangle, tone: theme.Tone, focused: bool, e: theme.Reveal, icon: theme.Icon, title: [:0]const u8, sub: [:0]const u8, title_size: f32) theme.Hit {
    const u = theme.view().u;
    const b = theme.button(key, r, 26 * u, tone, focused, e);
    const f = b.face;
    const mid = f.y + f.height / 2;
    const disc = @min(f.height * 0.62, 86 * u);
    const ix = f.x + 24 * u + disc / 2;
    const tx = f.x + 24 * u + disc + 24 * u;
    const room = f.x + f.width - tx - 18 * u;

    theme.dot(ix, mid, disc / 2, theme.fade(tone.edge, e.a * 0.55));
    theme.icon(icon, ix, mid, disc * 0.66, theme.fade(tone.ink, e.a));

    if (sub.len == 0) {
        theme.write(theme.heavy, title, tx, mid, theme.fit(theme.heavy, title, title_size, room), theme.fade(tone.ink, e.a));
    } else {
        const small = @min(30 * u, title_size * 0.6);

        theme.write(theme.heavy, title, tx, mid - small * 0.55, theme.fit(theme.heavy, title, title_size, room), theme.fade(tone.ink, e.a));
        theme.write(theme.body, sub, tx, mid + title_size * 0.4, theme.fit(theme.body, sub, small, room), theme.fade(tone.ink, e.a * 0.86));
    }

    return b;
}

fn plain(key: u32, r: rl.Rectangle, tone: theme.Tone, focused: bool, e: theme.Reveal, title: [:0]const u8, size: f32) theme.Hit {
    const b = theme.button(key, r, 20 * theme.view().u, tone, focused, e);
    const f = b.face;

    theme.center(theme.heavy, title, f.x + f.width / 2, f.y + f.height / 2, theme.fit(theme.heavy, title, size, f.width - 20 * theme.view().u), theme.fade(tone.ink, e.a));

    return b;
}

fn home(v: View, sel: *usize) ?Home {
    const u = v.u;
    const exits = !builtin.abi.isAndroid();
    const play_h = v.tap(128);
    const online_h = v.tap(100);
    const row_h = v.tap(76);
    const gap = 22 * u;
    const hint_h: f32 = if (v.keyed()) 56 * u else 0;
    const buttons = play_h + online_h + row_h + gap * 2 + 12 * u;
    const space = 52 * u;
    const room = v.height() - hint_h - buttons - space - 8 * u;
    var title_w = @min(590 * u, v.width() * 0.46);

    title_w = @min(title_w, title_w * room / theme.lockupHeight(title_w));

    const title_h = theme.lockupHeight(title_w);
    const total = title_h + space + buttons;
    const top = v.top + @max(0, (v.height() - hint_h - total) * 0.46);
    const x = v.left + 12 * u;
    const bw = @min(500 * u, v.width() * 0.46);
    var chosen: ?Home = null;

    rl.DrawRectangleGradientH(0, 0, @intFromFloat(v.w * 0.62), @intFromFloat(v.h), theme.fade(theme.night, 0.36), theme.fade(theme.night, 0));
    theme.lockup(x, top, title_w, theme.reveal(0), theme.reveal(1.2));

    var y = top + title_h + space;
    const play = wide(theme.tag("home", 0), .{ .x = x, .y = y, .width = bw, .height = play_h }, tones.coral_tone, sel.* == 0, theme.reveal(3), .play, "PLAY", "Offline against bots", 70 * u);

    y += play_h + gap + 6 * u;

    const online = wide(theme.tag("home", 1), .{ .x = x, .y = y, .width = bw, .height = online_h }, tones.teal_tone, sel.* == 1, theme.reveal(4), .signal, "ONLINE", "Rooms with friends", 50 * u);

    y += online_h + gap + 6 * u;

    const half = if (exits) (bw - 18 * u) / 2 else bw;
    const gear = wide(theme.tag("home", 2), .{ .x = x, .y = y, .width = half, .height = row_h }, tones.cream_tone, sel.* == 2, theme.reveal(5), .gear, "SETTINGS", "", 36 * u);

    if (play.hot) sel.* = 0;
    if (online.hot) sel.* = 1;
    if (gear.hot) sel.* = 2;
    if (play.click) chosen = .play;
    if (online.click) chosen = .online;
    if (gear.click) chosen = .settings;

    if (exits) {
        const leave = wide(theme.tag("home", 3), .{ .x = x + half + 18 * u, .y = y, .width = half, .height = row_h }, tones.sand_tone, sel.* == 3, theme.reveal(5.6), .exit, "EXIT", "", 36 * u);

        if (leave.hot) sel.* = 3;
        if (leave.click) chosen = .exit;
    }

    if (v.keyed()) {
        const items: []const theme.Hint = if (theme.pad_live) &.{ .{ .key = "D-PAD", .label = "Choose" }, .{ .key = "A", .label = "Select" }, .{ .key = "Y", .label = "Settings" } } else &.{ .{ .key = "ARROWS", .label = "Choose" }, .{ .key = "ENTER", .label = "Select" }, .{ .key = "TAB", .label = "Settings" } };

        theme.hints(items, x, v.bottom - 16 * u, 19 * u, theme.reveal(6).a);
    }

    place(v);

    return chosen;
}

fn place(v: View) void {
    const label = backdrop.name();
    const u = v.u;
    const e = theme.reveal(7);
    const size = 28 * u;
    const h = 56 * u;
    const w = theme.measure(theme.body, label, size) + 80 * u;
    const r: rl.Rectangle = .{ .x = v.right - w, .y = v.bottom - h + e.dy, .width = w, .height = h };

    if (label.len == 0) return;

    theme.round(theme.offset(r, 5 * u, 7 * u), h / 2, theme.fade(theme.night, 0.3 * e.a));
    theme.round(r, h / 2, theme.fade(theme.navy, 0.92 * e.a));
    theme.icon(.pin, r.x + 34 * u, r.y + h / 2, 34 * u, theme.fade(theme.coral, e.a));
    theme.write(theme.body, label, r.x + 58 * u, r.y + h / 2, size, theme.fade(theme.cream, e.a));
}

fn art(a: Art, cx: f32, cy: f32, s: f32, ink: rl.Color, off: rl.Color) void {
    switch (a) {
        .icon => |i| theme.icon(i, cx, cy, s, ink),
        .bars => |count| {
            const bw = s * 0.22;
            const step = s * 0.3;

            for (0..3) |i| {
                const fi: f32 = @floatFromInt(i);
                const bh = s * (0.34 + fi * 0.28);

                theme.round(.{ .x = cx - step - bw / 2 + fi * step, .y = cy + s * 0.45 - bh, .width = bw, .height = bh }, bw * 0.34, if (i < count) ink else off);
            }
        },
    }
}

fn cards(v: View, options: []const Option, sel: *usize, reserve: f32) bool {
    const u = v.u;
    const gap = 36 * u;
    const n: f32 = @floatFromInt(options.len);
    const cw = @min((if (options.len == 2) @as(f32, 440) else 370) * u, (v.width() - gap * (n - 1)) / n);
    const space = bodyBottom(v) - bodyTop(v) - reserve;
    const ch = @min(430 * u, space - 12 * u);
    const gx = v.cx() - (cw * n + gap * (n - 1)) / 2;
    const gy = bodyTop(v) + (space - ch) * 0.45;
    var chosen = false;

    for (options, 0..) |o, i| {
        const r: rl.Rectangle = .{ .x = gx + (cw + gap) * @as(f32, @floatFromInt(i)), .y = gy, .width = cw, .height = ch };
        const e = theme.reveal(1 + @as(f32, @floatFromInt(i)));
        const b = theme.button(theme.tag("card", i + options.len * 8), r, 30 * u, tones.cream_tone, i == sel.*, e);
        const f = b.face;
        const inset = 18 * u;
        const tile: rl.Rectangle = .{ .x = f.x + inset, .y = f.y + inset, .width = f.width - inset * 2, .height = f.height * 0.56 };

        if (b.hot) sel.* = i;

        if (b.click) {
            sel.* = i;
            chosen = true;
        }

        theme.round(tile, 20 * u, theme.fade(o.edge, e.a));
        theme.round(.{ .x = tile.x, .y = tile.y, .width = tile.width, .height = tile.height - 8 * u }, 20 * u, theme.fade(o.tint, e.a));
        art(o.art, tile.x + tile.width / 2, tile.y + tile.height / 2 - 4 * u, @min(tile.height * 0.62, 150 * u), theme.fade(theme.cream, e.a), theme.fade(theme.night, 0.22 * e.a));

        const room = f.y + f.height - (tile.y + tile.height);
        const name_size = @min(62 * u, room * 0.5);
        const note_size = @min(28 * u, room * 0.24);

        theme.center(theme.heavy, o.name, f.x + f.width / 2, tile.y + tile.height + room * 0.37, theme.fit(theme.heavy, o.name, name_size, tile.width), theme.fade(theme.navy, e.a));
        theme.center(theme.body, o.note, f.x + f.width / 2, tile.y + tile.height + room * 0.74, theme.fit(theme.body, o.note, note_size, tile.width), theme.fade(theme.soft, e.a));
    }

    return chosen;
}

fn pill(cx: f32, y: f32, text: [:0]const u8, face: rl.Color, ink: rl.Color, e: theme.Reveal) void {
    const u = theme.view().u;
    const size = 28 * u;
    const w = theme.measure(theme.body, text, size) + 52 * u;
    const r: rl.Rectangle = .{ .x = cx - w / 2, .y = y + e.dy, .width = w, .height = 52 * u };

    theme.round(theme.offset(r, 4 * u, 6 * u), 26 * u, theme.fade(theme.night, 0.32 * e.a));
    theme.round(r, 26 * u, theme.fade(face, e.a));
    theme.center(theme.body, text, cx, r.y + r.height / 2, size, theme.fade(ink, e.a));
}

fn nameScreen(v: View, entry: *NameEntry, back: *bool) ?usize {
    const u = v.u;
    const compact = v.cramped();
    const gap = 12 * u;
    const head = theme.headerHeight(v);
    const field_h = if (compact) head else v.tap(94);
    const top = if (compact) v.top + head + 20 * u else bodyTop(v) + field_h + 24 * u;
    const rows: f32 = key_rows.len + 1;
    const fit_h = (bodyBottom(v) - top - gap * (rows - 1) - 10 * u) / rows;
    const kh = @min(@max(v.tap(84), 84 * u), fit_h);
    const kw = @min(kh * 1.5, (v.width() - gap * (key_cols - 1)) / key_cols);
    const span = kw * key_cols + gap * (key_cols - 1);
    const kx = v.cx() - span / 2;
    var press: ?usize = null;

    back.* = theme.header(if (compact) "" else "YOUR NAME", if (compact) "" else "Shown on the scoreboard and kill feed");

    const title_w = theme.measure(theme.heavy, "YOUR NAME", 66 * u);
    const field_x = if (compact) v.left + v.tap(72) + 30 * u + title_w + 36 * u else kx;
    const field_w = if (compact) v.right - field_x else span;
    const field: rl.Rectangle = .{ .x = field_x, .y = if (compact) v.top else bodyTop(v), .width = field_w, .height = field_h - 8 * u };
    const e = theme.reveal(1);
    const f = e.move(field);
    const size = @min(56 * u, field.height * 0.62);
    const shown = std.fmt.bufPrintSentinel(&name_draw, "{s}", .{entry.text[0..entry.len]}, 0) catch "";
    const tw = theme.measure(theme.heavy, shown, size);
    const mid = f.y + f.height / 2;
    const tx = f.x + 30 * u;

    if (compact) theme.extruded(theme.heavy, "YOUR NAME", v.left + v.tap(72) + 30 * u, v.top + head / 2 + e.dy, 66 * u, theme.cream, e.a);

    theme.panel(f, 22 * u, theme.cream, e.a);

    if (entry.len == 0) theme.write(theme.body, "Type your name", tx + 12 * u, mid, size * 0.82, theme.fade(theme.soft, 0.7 * e.a));

    theme.write(theme.heavy, shown, tx, mid, size, theme.fade(theme.navy, e.a));

    if (@mod(rl.GetTime(), 1.0) < 0.55) theme.round(.{ .x = tx + tw + 4 * u, .y = mid - size * 0.38, .width = 5 * u, .height = size * 0.76 }, 2 * u, theme.fade(theme.coral, e.a));

    var count_buf: [16]u8 = undefined;
    const count = std.fmt.bufPrintSentinel(&count_buf, "{d} / {d}", .{ entry.len, entry.text.len }, 0) catch "";

    theme.write(theme.body, count, f.x + f.width - 28 * u - theme.measure(theme.body, count, 26 * u), mid, 26 * u, theme.fade(theme.soft, e.a));

    for (keyboard, 0..) |k, i| {
        const r: rl.Rectangle = .{
            .x = kx + (kw + gap) * @as(f32, @floatFromInt(k.col)),
            .y = top + (kh + gap) * @as(f32, @floatFromInt(k.row)),
            .width = kw * @as(f32, @floatFromInt(k.span)) + gap * @as(f32, @floatFromInt(k.span - 1)),
            .height = kh - 6 * u,
        };
        const is_done = k.action == .done;
        const tone = if (is_done) (if (entry.ready()) tones.coral_tone else tones.dim_tone) else if (k.action == .shift and entry.upper) tones.teal_tone else if (k.action != .char) tones.sand_tone else tones.cream_tone;
        const in = theme.reveal(1.4 + @as(f32, @floatFromInt(k.row)) * 0.5 + @as(f32, @floatFromInt(k.col)) * 0.06);

        if (theme.pointer.over(.{ .x = r.x, .y = r.y, .width = r.width, .height = kh })) {
            if (entry.age > 0.3 and theme.pointer.moved) entry.focus = i;

            if (theme.pointer.pressed and theme.settled()) {
                entry.focus = i;
                press = i;
            }
        }

        var one = [2:0]u8{ k.label[0], 0 };
        const label: [:0]const u8 = if (k.action != .char) k.label else if (entry.upper or !std.ascii.isAlphabetic(k.label[0])) k.label else blk: {
            one[0] = std.ascii.toLower(k.label[0]);

            break :blk one[0..1 :0];
        };

        _ = plain(theme.tag("key", i), r, tone, i == entry.focus and v.keyed(), in, label, if (k.action != .char) 32 * u else 42 * u);
    }

    footer(v, &.{ .{ .key = "ENTER", .label = "Done" }, .{ .key = "ESC", .label = "Back" } }, &.{ .{ .key = "A", .label = "Type" }, .{ .key = "X", .label = "Delete" }, .{ .key = "Y", .label = "Shift" }, .{ .key = "START", .label = "Done" }, .{ .key = "B", .label = "Back" } });

    return press;
}

fn joinScreen(v: View, digits: [3]u8, typed: usize, focus: *usize, err: ?[:0]const u8) ?usize {
    const u = v.u;
    const gap = 16 * u;
    const top = bodyTop(v);
    const space = bodyBottom(v) - top;
    const kh = @min(@max(v.tap(98), 98 * u), (space - gap * 3 - 12 * u) / 4);
    const kw = kh * 1.55;
    const grid_w = kw * 3 + gap * 2;
    const grid_h = kh * 4 + gap * 3;
    const right = v.cx() + v.width() * 0.23;
    const kx = right - grid_w / 2;
    const ky = top + (space - grid_h) * 0.45;
    const left = v.cx() - v.width() * 0.2;
    const bw = @min(158 * u, v.width() * 0.13);
    const bh = bw * 1.28;
    const bgap = 22 * u;
    const bx = left - (bw * 3 + bgap * 2) / 2;
    const by = ky + grid_h / 2 - bh / 2;
    var press: ?usize = null;

    const e = theme.reveal(1);

    theme.center(theme.heavy, "ROOM CODE", left, by - 52 * u + e.dy, 38 * u, theme.fade(theme.sun, e.a));

    for (0..3) |i| {
        const in = theme.reveal(1.4 + @as(f32, @floatFromInt(i)) * 0.5);
        const r = in.move(.{ .x = bx + (bw + bgap) * @as(f32, @floatFromInt(i)), .y = by, .width = bw, .height = bh });

        if (i == typed) theme.round(theme.grow(r, 7 * u), 31 * u, theme.fade(theme.sun, in.a));

        theme.panel(r, 24 * u, theme.cream, in.a);

        if (i < typed) {
            var one = [2:0]u8{ '0' + digits[i], 0 };

            theme.center(theme.heavy, one[0..1 :0], r.x + bw / 2, r.y + bh / 2, bh * 0.82, theme.fade(theme.navy, in.a));
        }
    }

    if (err) |msg| pill(left, by + bh + 40 * u, msg, theme.brick, theme.cream, theme.reveal(0));

    for (keypad, 0..) |label, i| {
        const col: f32 = @floatFromInt(i % 3);
        const row: f32 = @floatFromInt(i / 3);
        const r: rl.Rectangle = .{ .x = kx + (kw + gap) * col, .y = ky + (kh + gap) * row, .width = kw, .height = kh - 6 * u };
        const tone = if (i == 11) (if (typed == 3) tones.coral_tone else tones.dim_tone) else if (i == 9) tones.sand_tone else tones.cream_tone;

        if (theme.pointer.over(r)) {
            if (theme.pointer.moved) focus.* = i;

            if (theme.pointer.pressed and theme.settled()) {
                focus.* = i;
                press = i;
            }
        }

        _ = plain(theme.tag("pad", i), r, tone, i == focus.* and v.keyed(), theme.reveal(1.6 + row * 0.6 + col * 0.15), label, if (label.len > 1) 36 * u else 52 * u);
    }

    footer(v, &.{ .{ .key = "0-9", .label = "Type" }, .{ .key = "BKSP", .label = "Delete" }, .{ .key = "ESC", .label = "Back" } }, &.{ .{ .key = "A", .label = "Type" }, .{ .key = "X", .label = "Delete" }, .{ .key = "B", .label = "Back" } });

    return press;
}

const Connect = enum { none, retry, cancel };

fn connecting(v: View, joining: bool) Connect {
    const u = v.u;
    const e = theme.reveal(0);
    const pw = @min(700 * u, v.width());
    const ph = 440 * u;
    const r = e.move(.{ .x = v.cx() - pw / 2, .y = v.top + (v.height() - ph) * 0.45, .width = pw, .height = ph });
    const failed = net.status == .timeout or net.status == .rejected;
    const label: [:0]const u8 = if (net.status == .timeout) "SERVER NOT REACHABLE" else if (net.status == .rejected) "COULD NOT JOIN" else if (joining) "JOINING ROOM" else "CREATING ROOM";
    var out: Connect = .none;

    theme.panel(r, 34 * u, theme.cream, e.a);

    if (failed) {
        theme.dot(v.cx(), r.y + 108 * u, 54 * u, theme.fade(theme.brick, e.a));
        theme.icon(.signal, v.cx(), r.y + 106 * u, 70 * u, theme.fade(theme.cream, e.a));
    } else {
        theme.spinner(v.cx(), r.y + 112 * u, 56 * u, theme.fade(theme.sand, e.a), theme.fade(theme.coral, e.a));
    }

    theme.center(theme.heavy, label, v.cx(), r.y + 220 * u, theme.fit(theme.heavy, label, 52 * u, pw - 60 * u), theme.fade(theme.navy, e.a));

    const note: [:0]const u8 = if (net.status == .rejected) reasonText(net.reason) else if (net.status == .timeout) "Check the connection and try again" else "Talking to the server";

    theme.center(theme.body, note, v.cx(), r.y + 270 * u, 28 * u, theme.fade(theme.soft, e.a));

    const bh = v.tap(88);
    const bw = @min(250 * u, (pw - 90 * u) / 2);
    const by = r.y + ph - bh - 36 * u;

    if (failed) {
        if (plain(theme.tag("connect", 0), .{ .x = v.cx() - bw - 12 * u, .y = by, .width = bw, .height = bh }, tones.coral_tone, true, e, "RETRY", 42 * u).click) out = .retry;
        if (plain(theme.tag("connect", 1), .{ .x = v.cx() + 12 * u, .y = by, .width = bw, .height = bh }, tones.sand_tone, false, e, "BACK", 42 * u).click) out = .cancel;

        footer(v, &.{ .{ .key = "ENTER", .label = "Retry" }, .{ .key = "ESC", .label = "Back" } }, &.{ .{ .key = "A", .label = "Retry" }, .{ .key = "B", .label = "Back" } });
    } else {
        if (plain(theme.tag("connect", 2), .{ .x = v.cx() - bw / 2, .y = by, .width = bw, .height = bh }, tones.sand_tone, false, e, "CANCEL", 42 * u).click) out = .cancel;

        footer(v, &.{.{ .key = "ESC", .label = "Cancel" }}, &.{.{ .key = "B", .label = "Cancel" }});
    }

    return out;
}

const Code = enum { none, start, close };

fn codeScreen(v: View) Code {
    const u = v.u;
    var out: Code = .none;

    if (theme.header("ROOM READY", "Share this code with your friends")) out = .close;

    const back: rl.Rectangle = .{ .x = v.left, .y = v.top, .width = v.tap(72) + 14 * u, .height = theme.headerHeight(v) };
    const bh = v.tap(106);
    const top = bodyTop(v);
    const space = bodyBottom(v) - top;
    const pw = @min(1120 * u, v.width());
    const ph = @min(400 * u, space - bh - 48 * u);
    const y = top + @max(0, (space - ph - bh - 36 * u) * 0.45);
    const e = theme.reveal(1);
    const r = e.move(.{ .x = v.cx() - pw / 2, .y = y, .width = pw, .height = ph });
    const inset = 20 * u;
    const shot_w = pw * 0.4;
    const shot: rl.Rectangle = .{ .x = r.x + inset, .y = r.y + inset, .width = shot_w, .height = ph - inset * 2 - 56 * u };

    theme.panel(r, 34 * u, theme.cream, e.a);

    if (net.map < std.enums.values(Map).len) {
        const m: Map = @fromBackingInt(@intCast(net.map));

        mapselect.picture(m, shot, 20 * u, theme.cream, rl.WHITE, e.a);

        if (shared.maps.get(m)) |d| theme.center(theme.heavy, d.name, shot.x + shot.width / 2, shot.y + shot.height + 38 * u, 40 * u, theme.fade(theme.navy, e.a));
    }

    const right = r.x + inset * 2 + shot_w;
    const rw = r.x + pw - inset - right;
    const mid = right + rw / 2;
    const tw = @min(164 * u, (rw - 36 * u) / 3);
    const th = @min(tw * 1.34, ph - 140 * u);
    const tx = mid - (tw * 3 + 36 * u) / 2;
    const ty = r.y + (ph - th) / 2 + 30 * u;
    var buf: [8]u8 = undefined;
    const room = std.fmt.bufPrintSentinel(&buf, "{d:0>3}", .{net.code}, 0) catch "---";
    const font = theme.displayFont(th * 0.96);

    theme.center(theme.heavy, "ROOM CODE", mid, ty - 42 * u, 40 * u, theme.fade(theme.teal, e.a));

    for (0..3) |i| {
        const in = theme.reveal(2 + @as(f32, @floatFromInt(i)));
        const tile = in.move(.{ .x = tx + (tw + 18 * u) * @as(f32, @floatFromInt(i)), .y = ty, .width = tw, .height = th });
        var one = [2:0]u8{ room[@min(i, room.len - 1)], 0 };

        theme.round(theme.offset(tile, 0, 7 * u), 22 * u, theme.fade(theme.night, in.a));
        theme.round(tile, 22 * u, theme.fade(theme.navy, in.a));
        theme.center(font, one[0..1 :0], tile.x + tw / 2, tile.y + th / 2, th * 0.96, theme.fade(theme.sun, in.a));
    }

    const bw = @min(520 * u, pw);
    _ = wide(theme.tag("start", 0), .{ .x = v.cx() - bw / 2, .y = y + ph + 34 * u, .width = bw, .height = bh }, tones.coral_tone, true, theme.reveal(5), .play, "START MATCH", "", 52 * u);

    if (!theme.pointer.over(back) and theme.press(theme.tag("anywhere", 0), .{ .x = 0, .y = 0, .width = v.w, .height = v.h })) out = .start;

    footer(v, &.{ .{ .key = "ENTER", .label = "Start" }, .{ .key = "ESC", .label = "Close the room" } }, &.{ .{ .key = "A", .label = "Start" }, .{ .key = "B", .label = "Close the room" } });

    return out;
}

pub fn run(ui_dir: []const u8, apply: *const fn () void) ?Map {
    mapselect.setDir(ui_dir);

    if (std.c.getenv("DF_ONLINE")) |spec| return auto(std.mem.sliceTo(spec, 0));

    var screen: Screen = .home;
    var sel: usize = 0;
    var diff_sel: usize = 1;
    var online_sel: usize = 0;
    var digits: [3]u8 = undefined;
    var typed: usize = 0;
    var focus: usize = 0;
    var err: ?[:0]const u8 = null;
    var joining = false;
    var entry: NameEntry = .{};
    var menu: menu_mod.Menu = .{};
    var maps_first = false;

    menu.touch_enabled = theme.view().touch;

    if (std.c.getenv("DF_LOBBY")) |start| {
        const want = std.mem.sliceTo(start, 0);

        screen = std.meta.stringToEnum(Screen, want) orelse .home;
        maps_first = std.mem.eql(u8, want, "maps");
        entry.load();

        if (std.mem.startsWith(u8, want, "settings")) {
            menu.tab = std.fmt.parseInt(usize, want["settings".len..], 10) catch 0;
            menu.show();
        }

        if (screen == .code) net.map = @backingInt(Map.coast);
    }

    backdrop.begin();

    while (!rl.WindowShouldClose()) {
        const dt = rl.GetFrameTime();
        var in = readInput(dt, screen == .name);
        const was_open = menu.open;
        var next = screen;
        var pick = maps_first;
        var quit = false;

        maps_first = false;

        if (rl.IsCursorHidden()) rl.EnableCursor();

        net.pump();
        menu.update(dt, padId());
        apply();
        backdrop.open(dt);
        theme.enterScene(theme.tag("screen", @backingInt(screen)));

        const busy = was_open or menu.open;
        const live = theme.pointer;

        if (busy) {
            in = .{};
            theme.pointer = .{};
        }

        const v = theme.view();

        theme.dim(if (screen == .home) 0 else 0.58);

        switch (screen) {
            .home => {
                const count: i32 = if (builtin.abi.isAndroid()) 3 else 4;

                sel = @intCast(@mod(@as(i32, @intCast(sel)) + in.dx + in.dy, count));

                var chosen = if (menu.t > 0.5) null else home(v, &sel);

                if (in.ok) chosen = @fromBackingInt(@intCast(sel));

                if (!busy and (rl.IsKeyPressed(rl.KEY_TAB) or rl.IsKeyPressed(rl.KEY_O) or (if (padId()) |id| rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_FACE_UP) else false))) chosen = .settings;

                if (chosen) |c| {
                    audio.ui(.toast);
                    err = null;

                    switch (c) {
                        .play => next = .difficulty,
                        .online => {
                            next = .name;
                            entry.load();
                        },
                        .settings => menu.show(),
                        .exit => quit = true,
                    }
                }
            },
            .difficulty => {
                if (in.dx != 0) diff_sel = @intCast(@mod(@as(i32, @intCast(diff_sel)) + in.dx, @as(i32, difficulty_options.len)));

                const back = theme.header("DIFFICULTY", "Bots get faster, tougher and more accurate");
                const click = cards(v, &difficulty_options, &diff_sel, 0);

                footer(v, &.{ .{ .key = "ARROWS", .label = "Choose" }, .{ .key = "ENTER", .label = "Select" }, .{ .key = "ESC", .label = "Back" } }, &.{ .{ .key = "D-PAD", .label = "Choose" }, .{ .key = "A", .label = "Select" }, .{ .key = "B", .label = "Back" } });

                if (in.back or back) {
                    next = .home;
                } else if (click or in.ok) {
                    game_mod.difficulty = @fromBackingInt(@intCast(diff_sel));
                    audio.ui(.toast);
                    pick = true;
                }
            },
            .online => {
                if (in.dx != 0) online_sel = @intCast(@mod(@as(i32, @intCast(online_sel)) + in.dx, @as(i32, online_options.len)));

                const back = theme.header("ONLINE", "One player creates a room, the others join with its code");
                const chip_h = v.tap(76);
                const click = cards(v, &online_options, &online_sel, chip_h + 22 * v.u);
                var label_buf: [64]u8 = undefined;
                const playing_as = std.fmt.bufPrintSentinel(&label_buf, "Playing as {s}", .{net.nameText()}, 0) catch "";
                const chip_w = @min(theme.measure(theme.heavy, playing_as, 32 * v.u) + 200 * v.u, v.width());
                const chip_r: rl.Rectangle = .{ .x = v.cx() - chip_w / 2, .y = bodyBottom(v) - chip_h - 10 * v.u, .width = chip_w, .height = chip_h };
                const ce = theme.reveal(3);
                const chip = theme.button(theme.tag("who", 0), chip_r, chip_h / 2, tones.navy_tone, theme.pointer.over(chip_r), ce);
                const mid = chip.face.y + chip.face.height / 2;

                theme.write(theme.heavy, playing_as, chip.face.x + 36 * v.u, mid, 32 * v.u, theme.fade(theme.cream, ce.a));
                theme.write(theme.body, "Change", chip.face.x + chip.face.width - 36 * v.u - theme.measure(theme.body, "Change", 28 * v.u), mid, 28 * v.u, theme.fade(theme.sun, ce.a));

                if (err) |msg| pill(v.cx(), chip_r.y - 62 * v.u, msg, theme.brick, theme.cream, theme.reveal(0));

                footer(v, &.{ .{ .key = "ARROWS", .label = "Choose" }, .{ .key = "ENTER", .label = "Select" }, .{ .key = "ESC", .label = "Back" } }, &.{ .{ .key = "D-PAD", .label = "Choose" }, .{ .key = "A", .label = "Select" }, .{ .key = "B", .label = "Back" } });

                if (in.back or back or chip.click) {
                    next = .name;
                    entry.load();
                } else if (click or in.ok) {
                    audio.ui(.toast);
                    err = null;

                    if (online_sel == 1) {
                        next = .join;
                        typed = 0;
                        focus = 0;
                    } else {
                        pick = true;
                    }
                }
            },
            .name => {
                var leave = false;

                entry.age += dt;

                if (in.dx != 0 or in.dy != 0) entry.move(in.dx, in.dy);

                var press = nameScreen(v, &entry, &leave);

                if (in.back or leave) {
                    next = .home;
                } else {
                    var ch = rl.GetCharPressed();

                    while (ch > 0) : (ch = rl.GetCharPressed()) {
                        if (ch < 127) entry.typed(@intCast(ch));
                    }

                    if (in.erase) entry.erase();

                    if (in.shift) entry.upper = !entry.upper;

                    var finish = (in.enter or in.start) and entry.ready();

                    if (in.ok and !in.enter and !in.start) press = entry.focus;

                    if (press) |i| {
                        if (entry.press(i)) finish = true;

                        audio.ui(.toast);
                    }

                    if (finish) {
                        net.setName(entry.text[0..entry.len]);
                        next = .online;
                        err = null;
                    }
                }
            },
            .join => {
                if (in.dx != 0) focus = focus - focus % 3 + @as(usize, @intCast(@mod(@as(i32, @intCast(focus % 3)) + in.dx, 3)));
                if (in.dy != 0) focus = @intCast(@mod(@as(i32, @intCast(focus)) + in.dy * 3, 12));

                const back = theme.header("JOIN ROOM", "Type the 3 digit code your friend sees");
                var press = joinScreen(v, digits, typed, &focus, err);

                if (in.ok) press = focus;

                if (in.back or back) {
                    next = .online;
                } else {
                    var add: ?u8 = in.digit;
                    var del = in.erase;
                    var go = in.ok and typed == 3 and in.digit == null and press == null;

                    if (press) |p| {
                        if (p < 9) add = @intCast(p + 1);
                        if (p == 10) add = 0;
                        if (p == 9) del = true;
                        if (p == 11) go = typed == 3;
                    }

                    if (add) |d| {
                        if (typed < 3) {
                            digits[typed] = d;
                            typed += 1;
                            err = null;
                            audio.ui(.toast);

                            if (typed == 3) focus = 11;
                        }
                    }

                    if (del and typed > 0) typed -= 1;

                    if (go) {
                        const room = @as(u16, digits[0]) * 100 + @as(u16, digits[1]) * 10 + digits[2];

                        net.join(room);
                        joining = true;
                        next = .connecting;
                    }
                }
            },
            .connecting => {
                const action = connecting(v, joining);
                const failed = net.status == .timeout or net.status == .rejected;

                if (in.back or action == .cancel) {
                    net.cancel();
                    next = if (joining) .join else .online;
                    err = null;
                } else if (net.status == .rejected and joining) {
                    err = reasonText(net.reason);
                    typed = 0;
                    focus = 0;
                    net.status = .idle;
                    next = .join;
                } else {
                    if (failed and (in.ok or action == .retry)) {
                        if (joining) net.join(net.code) else net.create(net.map);
                    }

                    if (net.status == .joined) {
                        if (joining) {
                            net.active = true;
                            backdrop.close(dt);

                            return @fromBackingInt(@intCast(net.map));
                        }

                        next = .code;
                    }
                }
            },
            .code => {
                const action = codeScreen(v);

                if (in.back or action == .close) {
                    net.cancel();
                    next = .online;
                } else if (in.ok or action == .start) {
                    net.active = true;
                    rl.DisableCursor();
                    backdrop.close(dt);

                    return @fromBackingInt(@intCast(net.map));
                }
            },
        }

        theme.pointer = live;
        menu.draw(theme.pad_live);
        backdrop.close(dt);
        screen = next;

        if (quit) return null;

        if (pick) {
            const chosen = mapselect.pick() orelse {
                if (rl.WindowShouldClose()) return null;

                continue;
            };

            if (screen != .online) return chosen;

            net.create(@backingInt(chosen));
            joining = false;
            screen = .connecting;
        }
    }

    return null;
}

fn auto(spec: []const u8) ?Map {
    var it = std.mem.splitScalar(u8, spec, ':');
    const verb = it.next() orelse "";
    const arg = it.next() orelse "";

    if (std.mem.eql(u8, verb, "create")) {
        const m = std.meta.stringToEnum(Map, arg) orelse .facility;

        net.create(@backingInt(m));
    } else {
        net.join(std.fmt.parseInt(u16, arg, 10) catch 0);
    }

    while (!rl.WindowShouldClose()) {
        net.pump();
        mapselect.loading("Connecting", 0.05);

        if (net.status == .joined) {
            if (builtin.os.tag != .windows) {
                var buf: [512]u8 = undefined;
                const dir = std.mem.sliceTo(std.c.getenv("HOME") orelse return null, 0);
                const path = std.fmt.bufPrintSentinel(&buf, "{s}/.cache/mp/room-{d}.txt", .{ dir, std.c.getpid() }, 0) catch return null;
                var text: [16]u8 = undefined;
                const line = std.fmt.bufPrint(&text, "{d}\n", .{net.code}) catch "";
                const f = std.c.open(path.ptr, .{ .ACCMODE = .WRONLY, .CREAT = true, .TRUNC = true }, @as(c_uint, 0o644));

                if (f >= 0) {
                    _ = std.c.write(f, line.ptr, line.len);
                    _ = std.c.close(f);
                }
            }

            std.debug.print("joined room {d} slot {d} map {s}\n", .{ net.code, net.slot, mapName(net.map) });
            net.active = true;

            return @fromBackingInt(@intCast(net.map));
        }

        if (net.status == .timeout or net.status == .rejected) {
            std.debug.print("online failed: {s}\n", .{@tagName(net.status)});

            return null;
        }
    }

    return null;
}
