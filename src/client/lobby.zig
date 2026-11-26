const std = @import("std");
const builtin = @import("builtin");
const rl = @import("raylib");
const shared = @import("shared");
const ui = @import("ui.zig");
const net = @import("net.zig");
const mapselect = @import("mapselect.zig");
const game_mod = @import("game.zig");
const audio = @import("audio.zig");

const Map = shared.terrain.Map;
const net_shared = shared.net;

const Screen = enum { home, difficulty, name, online, join, connecting, code };

const Option = struct {
    name: [:0]const u8,
    note: [:0]const u8,
    tint: rl.Color,
    icon: Icon,
};

const Icon = enum { bots, globe, easy, normal, hard, create, join };

const home_options = [_]Option{
    .{ .name = "Offline", .note = "Play against bots", .tint = ui.rgba(110, 206, 138, 255), .icon = .bots },
    .{ .name = "Online", .note = "Play with friends in a room", .tint = ui.rgba(96, 160, 248, 255), .icon = .globe },
};

const difficulty_options = [_]Option{
    .{ .name = "Easy", .note = "Slow bots, loose aim", .tint = ui.rgba(110, 206, 138, 255), .icon = .easy },
    .{ .name = "Normal", .note = "The usual fight", .tint = ui.rgba(250, 200, 80, 255), .icon = .normal },
    .{ .name = "Hard", .note = "Fast, tough and accurate", .tint = ui.rgba(240, 92, 86, 255), .icon = .hard },
};

const online_options = [_]Option{
    .{ .name = "Create room", .note = "Pick a map, share the code", .tint = ui.rgba(250, 200, 80, 255), .icon = .create },
    .{ .name = "Join room", .note = "Type a friend's 3 digit code", .tint = ui.rgba(96, 160, 248, 255), .icon = .join },
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

fn background(w: f32, h: f32) void {
    rl.ClearBackground(.{ .r = 11, .g = 13, .b = 20, .a = 255 });
    rl.DrawRectangleGradientV(0, 0, @intFromFloat(w), @intFromFloat(h), .{ .r = 20, .g = 24, .b = 36, .a = 255 }, .{ .r = 9, .g = 11, .b = 17, .a = 255 });
}

fn heading(font: rl.Font, x: f32, h: f32, u: f32, kicker: [:0]const u8, title: [:0]const u8, sub: [:0]const u8) void {
    const ts = 46 * u;

    ui.caps(font, kicker, x, h * 0.1, 14 * u, ui.accent);
    ui.caps(font, title, x, h * 0.1 + 22 * u, ts, ui.white);
    ui.text(font, sub, x, h * 0.1 + 22 * u + ts + 10 * u, 15 * u, ui.fade(ui.white, 0.5));
}

fn drawIcon(icon: Icon, cx: f32, cy: f32, u: f32, color: rl.Color) void {
    const v = ui.v2;

    switch (icon) {
        .bots => {
            rl.DrawRectangleRounded(.{ .x = cx - 26 * u, .y = cy - 20 * u, .width = 52 * u, .height = 40 * u }, 0.35, 8, color);
            rl.DrawCircleV(v(cx - 11 * u, cy - 2 * u), 5 * u, ui.ink);
            rl.DrawCircleV(v(cx + 11 * u, cy - 2 * u), 5 * u, ui.ink);
            rl.DrawRectangleRec(.{ .x = cx - 2 * u, .y = cy - 32 * u, .width = 4 * u, .height = 12 * u }, color);
            rl.DrawCircleV(v(cx, cy - 34 * u), 5 * u, color);
        },
        .globe => {
            rl.DrawRing(v(cx, cy), 28 * u, 32 * u, 0, 360, 48, color);
            rl.DrawEllipseLines(@intFromFloat(cx), @intFromFloat(cy), 12 * u, 30 * u, color);
            rl.DrawEllipseLines(@intFromFloat(cx), @intFromFloat(cy), 13 * u, 31 * u, color);
            rl.DrawRectangleRec(.{ .x = cx - 30 * u, .y = cy - 1.5 * u, .width = 60 * u, .height = 3 * u }, color);
            rl.DrawRectangleRec(.{ .x = cx - 24 * u, .y = cy - 15 * u, .width = 48 * u, .height = 2.5 * u }, color);
            rl.DrawRectangleRec(.{ .x = cx - 24 * u, .y = cy + 12.5 * u, .width = 48 * u, .height = 2.5 * u }, color);
        },
        .easy, .normal, .hard => {
            const count: usize = switch (icon) {
                .easy => 1,
                .normal => 2,
                else => 3,
            };

            for (0..3) |i| {
                const x = cx - 30 * u + @as(f32, @floatFromInt(i)) * 22 * u;
                const bh = (16 + @as(f32, @floatFromInt(i)) * 14) * u;
                const on = i < count;

                rl.DrawRectangleRounded(.{ .x = x, .y = cy + 22 * u - bh, .width = 16 * u, .height = bh }, 0.3, 6, if (on) color else ui.fade(ui.white, 0.14));
            }
        },
        .create => {
            rl.DrawRectangleRounded(.{ .x = cx - 6 * u, .y = cy - 28 * u, .width = 12 * u, .height = 56 * u }, 0.5, 6, color);
            rl.DrawRectangleRounded(.{ .x = cx - 28 * u, .y = cy - 6 * u, .width = 56 * u, .height = 12 * u }, 0.5, 6, color);
        },
        .join => {
            for (0..3) |row| {
                for (0..3) |col| {
                    const x = cx - 24 * u + @as(f32, @floatFromInt(col)) * 18 * u;
                    const y = cy - 24 * u + @as(f32, @floatFromInt(row)) * 18 * u;

                    rl.DrawRectangleRounded(.{ .x = x, .y = y, .width = 12 * u, .height = 12 * u }, 0.35, 6, color);
                }
            }
        },
    }
}

fn cardWidth(count: usize, w: f32, u: f32) f32 {
    const n: f32 = @floatFromInt(count);

    return @min(340 * u, (w - 160 * u - 22 * u * (n - 1)) / n);
}

fn gridX(count: usize, w: f32, u: f32) f32 {
    const n: f32 = @floatFromInt(count);

    return (w - (cardWidth(count, w, u) * n + 22 * u * (n - 1))) / 2;
}

fn cards(font: rl.Font, options: []const Option, sel: *usize, w: f32, h: f32, u: f32) bool {
    const gap = 22 * u;
    const cw = cardWidth(options.len, w, u);
    const ch = cw * 0.72;
    const gx = gridX(options.len, w, u);
    const gy = h * 0.32;
    const mouse = rl.GetMousePosition();
    const moved = rl.GetMouseDelta().x != 0 or rl.GetMouseDelta().y != 0;
    var chosen = false;

    for (options, 0..) |o, i| {
        const r: rl.Rectangle = .{ .x = gx + (cw + gap) * @as(f32, @floatFromInt(i)), .y = gy, .width = cw, .height = ch };

        if (rl.CheckCollisionPointRec(mouse, r)) {
            if (moved) sel.* = i;

            if (rl.IsMouseButtonPressed(rl.MOUSE_BUTTON_LEFT)) {
                sel.* = i;
                chosen = true;
            }
        }

        const on = i == sel.*;
        const card: rl.Rectangle = .{ .x = r.x, .y = r.y + (if (on) -4 * u else 0), .width = r.width, .height = r.height };
        const art_h = card.height * 0.58;
        const round: f32 = 0.06;

        rl.DrawRectangleRounded(card, round, 8, .{ .r = 22, .g = 26, .b = 38, .a = 255 });
        rl.BeginScissorMode(@intFromFloat(card.x), @intFromFloat(card.y), @intFromFloat(card.width), @intFromFloat(art_h));
        rl.DrawRectangleRounded(.{ .x = card.x, .y = card.y, .width = card.width, .height = art_h + 20 * u }, round, 8, ui.fade(o.tint, if (on) 0.2 else 0.1));
        rl.EndScissorMode();
        drawIcon(o.icon, card.x + card.width / 2, card.y + art_h / 2, u, ui.fade(o.tint, if (on) 1 else 0.7));

        const ns = 26 * u;
        const name_y = card.y + art_h + 14 * u;

        rl.DrawRectangleRec(.{ .x = card.x + 18 * u, .y = name_y - 6 * u, .width = 22 * u, .height = 2 * u }, ui.fade(o.tint, 0.9));
        ui.caps(font, o.name, card.x + 18 * u, name_y, ns, ui.white);
        ui.text(font, o.note, card.x + 18 * u, name_y + ns + 6 * u, 15 * u, ui.fade(ui.white, 0.55));
        rl.DrawRectangleRoundedLinesEx(card, round, 8, if (on) 2 * u else 1, if (on) ui.fade(ui.white, 0.85) else ui.edge);
    }

    return chosen;
}

fn hint(font: rl.Font, text: [:0]const u8, w: f32, h: f32, u: f32) void {
    const s = 14 * u;

    ui.text(font, text, (w - ui.width(font, text, s)) / 2, h - 60 * u, s, ui.fade(ui.white, 0.45));
}

fn backButton(font: rl.Font, u: f32) bool {
    const r: rl.Rectangle = .{ .x = 36 * u, .y = 30 * u, .width = 92 * u, .height = 34 * u };
    const hover = rl.CheckCollisionPointRec(rl.GetMousePosition(), r);

    ui.card(r.x, r.y, r.width, r.height, if (hover) 1 else 0.7);
    ui.caps(font, "BACK", r.x + 26 * u, r.y + 10 * u, 13 * u, ui.fade(ui.white, if (hover) 1 else 0.7));

    return hover and rl.IsMouseButtonPressed(rl.MOUSE_BUTTON_LEFT);
}

fn mapName(m: u8) [:0]const u8 {
    if (m >= std.enums.values(Map).len) return "unknown";

    return @tagName(@as(Map, @fromBackingInt(@intCast(m))));
}

fn spinner(cx: f32, cy: f32, u: f32) void {
    const t: f32 = @floatCast(rl.GetTime());
    const head = @mod(t * 320, 360);
    const span = 80 + 40 * @sin(t * 3);

    rl.DrawRing(.{ .x = cx, .y = cy }, 27.5 * u, 30 * u, 0, 360, 64, ui.fade(ui.white, 0.1));
    rl.DrawRing(.{ .x = cx, .y = cy }, 27.5 * u, 30 * u, head, head + span, 48, ui.accent);
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

fn centered(font: rl.Font, text: [:0]const u8, cx: f32, y: f32, size: f32, color: rl.Color) void {
    ui.text(font, text, cx - ui.width(font, text, size) / 2, y, size, color);
}

fn centeredCaps(font: rl.Font, text: [:0]const u8, cx: f32, y: f32, size: f32, color: rl.Color) void {
    ui.caps(font, text, cx - ui.capsWidth(font, text, size) / 2, y, size, color);
}

pub fn run(font: rl.Font, ui_dir: []const u8) ?Map {
    if (std.c.getenv("DF_ONLINE")) |spec| return auto(font, std.mem.sliceTo(spec, 0));

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

    if (std.c.getenv("DF_LOBBY")) |start| {
        screen = std.meta.stringToEnum(Screen, std.mem.sliceTo(start, 0)) orelse .home;
        entry.load();
    }

    while (!rl.WindowShouldClose()) {
        const dt = rl.GetFrameTime();
        const w: f32 = @floatFromInt(rl.GetScreenWidth());
        const h: f32 = @floatFromInt(rl.GetScreenHeight());
        const u = h / 900;
        const in = readInput(dt, screen == .name);

        if (rl.IsCursorHidden()) rl.EnableCursor();
        net.pump();
        rl.BeginDrawing();
        background(w, h);

        switch (screen) {
            .home => {
                heading(font, gridX(home_options.len, w, u), h, u, "DRONEFIRE", "BATTLE", "Arrows or stick to move    Enter or A to choose");

                if (in.dx != 0) sel = @intCast(@mod(@as(i32, @intCast(sel)) + in.dx, @as(i32, home_options.len)));

                const click = cards(font, &home_options, &sel, w, h, u);

                if (click or in.ok) {
                    audio.ui(.toast);
                    screen = if (sel == 0) .difficulty else .name;
                    err = null;

                    if (screen == .name) entry.load();
                }
            },
            .difficulty => {
                heading(font, gridX(difficulty_options.len, w, u), h, u, "OFFLINE", "DIFFICULTY", "Bots get faster, tougher and more accurate");

                if (in.dx != 0) diff_sel = @intCast(@mod(@as(i32, @intCast(diff_sel)) + in.dx, @as(i32, difficulty_options.len)));

                const click = cards(font, &difficulty_options, &diff_sel, w, h, u);
                const back = backButton(font, u);

                rl.EndDrawing();

                if (in.back or back) {
                    screen = .home;

                    continue;
                }

                if (click or in.ok) {
                    game_mod.difficulty = @fromBackingInt(@intCast(diff_sel));
                    audio.ui(.toast);

                    if (mapselect.pick(font, ui_dir)) |m| return m;

                    if (rl.WindowShouldClose()) return null;
                }

                continue;
            },
            .online => {
                heading(font, gridX(online_options.len, w, u), h, u, "ONLINE", "PLAY WITH FRIENDS", "One player creates a room, everyone else joins with its code");

                if (in.dx != 0) online_sel = @intCast(@mod(@as(i32, @intCast(online_sel)) + in.dx, @as(i32, online_options.len)));

                const click = cards(font, &online_options, &online_sel, w, h, u);
                const back = backButton(font, u);

                if (err) |e| centered(font, e, w / 2, h * 0.32 + 340 * u * 0.72 + 40 * u, 16 * u, ui.red);

                var label_buf: [48]u8 = undefined;
                const playing_as = std.fmt.bufPrintSentinel(&label_buf, "Playing as {s}", .{net.nameText()}, 0) catch "";

                hint(font, playing_as, w, h, u);
                rl.EndDrawing();

                if (in.back or back) {
                    screen = .name;
                    entry.load();

                    continue;
                }

                if (click or in.ok) {
                    audio.ui(.toast);
                    err = null;

                    if (online_sel == 1) {
                        screen = .join;
                        typed = 0;
                        focus = 0;

                        continue;
                    }

                    const m = mapselect.pick(font, ui_dir) orelse {
                        if (rl.WindowShouldClose()) return null;

                        continue;
                    };

                    net.create(@backingInt(m));
                    joining = false;
                    screen = .connecting;
                }

                continue;
            },
            .name => {
                const back = backButton(font, u);
                const kw = 64 * u;
                const kh = 54 * u;
                const kgap = 10 * u;
                const span = kw * key_cols + kgap * (key_cols - 1);
                const kx = w / 2 - span / 2;
                const fy = h * 0.27;
                const fh = 86 * u;
                const ky = fy + fh + 30 * u;
                const mouse = rl.GetMousePosition();
                const moved = entry.age > 0.3 and (rl.GetMouseDelta().x != 0 or rl.GetMouseDelta().y != 0);
                var press: ?usize = null;

                entry.age += dt;
                heading(font, kx, h, u, "ONLINE", "YOUR NAME", "Other players see it on the scoreboard and kill feed");

                const field: rl.Rectangle = .{ .x = kx, .y = fy, .width = span, .height = fh };
                const ts = 40 * u;
                const shown = std.fmt.bufPrintSentinel(&name_draw, "{s}", .{entry.text[0..entry.len]}, 0) catch "";
                const tw = ui.width(font, shown, ts);
                const blink = @mod(rl.GetTime(), 1.0) < 0.55;

                rl.DrawRectangleRounded(field, 0.14, 8, ui.rgba(22, 26, 38, 255));
                rl.DrawRectangleRoundedLinesEx(field, 0.14, 8, 2 * u, ui.fade(ui.accent, 0.9));

                if (entry.len == 0) ui.text(font, "Type your name", field.x + 28 * u, field.y + fh / 2 - ts / 2, ts, ui.fade(ui.white, 0.25));

                ui.text(font, shown, field.x + 28 * u, field.y + fh / 2 - ts / 2, ts, ui.white);

                if (blink) rl.DrawRectangleRec(.{ .x = field.x + 30 * u + tw, .y = field.y + fh / 2 - ts * 0.45, .width = 3 * u, .height = ts * 0.9 }, ui.accent);

                var count_buf: [16]u8 = undefined;
                const count = std.fmt.bufPrintSentinel(&count_buf, "{d} / {d}", .{ entry.len, entry.text.len }, 0) catch "";

                ui.caps(font, count, field.x + span - 28 * u - ui.capsWidth(font, count, 13 * u), field.y + fh / 2 - 6.5 * u, 13 * u, ui.fade(ui.white, 0.4));

                if (in.dx != 0 or in.dy != 0) entry.move(in.dx, in.dy);

                for (keyboard, 0..) |k, i| {
                    const r: rl.Rectangle = .{
                        .x = kx + (kw + kgap) * @as(f32, @floatFromInt(k.col)),
                        .y = ky + (kh + kgap) * @as(f32, @floatFromInt(k.row)),
                        .width = kw * @as(f32, @floatFromInt(k.span)) + kgap * @as(f32, @floatFromInt(k.span - 1)),
                        .height = kh,
                    };

                    if (rl.CheckCollisionPointRec(mouse, r)) {
                        if (moved) entry.focus = i;

                        if (rl.IsMouseButtonPressed(rl.MOUSE_BUTTON_LEFT)) {
                            entry.focus = i;
                            press = i;
                        }
                    }

                    const on = i == entry.focus;
                    const is_done = k.action == .done;
                    const lit = (is_done and entry.ready()) or (k.action == .shift and entry.upper);
                    const fill = if (is_done and entry.ready()) ui.fade(ui.accent, if (on) 1 else 0.8) else if (lit) ui.fade(ui.white, 0.16) else ui.rgba(22, 26, 38, 255);

                    rl.DrawRectangleRounded(r, 0.2, 8, fill);
                    rl.DrawRectangleRoundedLinesEx(r, 0.2, 8, if (on) 2 * u else 1, if (on) ui.fade(ui.white, 0.85) else ui.edge);

                    var one = [2:0]u8{ k.label[0], 0 };
                    const label: [:0]const u8 = if (k.action != .char) k.label else if (entry.upper or !std.ascii.isAlphabetic(k.label[0])) k.label else blk: {
                        one[0] = std.ascii.toLower(k.label[0]);

                        break :blk one[0..1 :0];
                    };
                    const size = if (k.action != .char) 14 * u else 22 * u;
                    const ink = if (is_done and entry.ready()) ui.ink else if (is_done) ui.fade(ui.white, 0.35) else ui.white;

                    if (k.action == .char) {
                        centered(font, label, r.x + r.width / 2, r.y + kh / 2 - size / 2, size, ink);
                    } else {
                        centeredCaps(font, label, r.x + r.width / 2, r.y + kh / 2 - size / 2, size, ink);
                    }
                }

                hint(font, "Type or use the keys    Enter or Start when done    Esc or B to go back", w, h, u);
                rl.EndDrawing();

                if (in.back or back) {
                    screen = .home;

                    continue;
                }

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
                    screen = .online;
                    err = null;
                }

                continue;
            },
            .join => {
                const back = backButton(font, u);
                const bw = 96 * u;
                const bh = 116 * u;
                const bgap = 18 * u;
                const bx = w / 2 - (bw * 3 + bgap * 2) / 2;
                const by = h * 0.3;

                heading(font, gridX(2, w, u), h, u, "ONLINE", "JOIN ROOM", "Type the 3 digit code your friend sees");

                for (0..3) |i| {
                    const r: rl.Rectangle = .{ .x = bx + (bw + bgap) * @as(f32, @floatFromInt(i)), .y = by, .width = bw, .height = bh };
                    const current = i == typed;

                    rl.DrawRectangleRounded(r, 0.12, 8, .{ .r = 22, .g = 26, .b = 38, .a = 255 });
                    rl.DrawRectangleRoundedLinesEx(r, 0.12, 8, if (current) 2 * u else 1, if (current) ui.fade(ui.accent, 0.9) else ui.edge);

                    if (i < typed) {
                        var one = [2:0]u8{ '0' + digits[i], 0 };

                        centeredCaps(font, one[0..1 :0], r.x + bw / 2, r.y + bh / 2 - 34 * u, 68 * u, ui.white);
                    }
                }

                const kw = 92 * u;
                const kh = 54 * u;
                const kgap = 10 * u;
                const kx = w / 2 - (kw * 3 + kgap * 2) / 2;
                const ky = by + bh + 34 * u;
                const mouse = rl.GetMousePosition();
                const moved = rl.GetMouseDelta().x != 0 or rl.GetMouseDelta().y != 0;
                var press: ?usize = null;

                if (in.dx != 0) focus = focus - focus % 3 + @as(usize, @intCast(@mod(@as(i32, @intCast(focus % 3)) + in.dx, 3)));
                if (in.dy != 0) focus = @intCast(@mod(@as(i32, @intCast(focus)) + in.dy * 3, 12));

                for (keypad, 0..) |label, i| {
                    const col: f32 = @floatFromInt(i % 3);
                    const row: f32 = @floatFromInt(i / 3);
                    const r: rl.Rectangle = .{ .x = kx + (kw + kgap) * col, .y = ky + (kh + kgap) * row, .width = kw, .height = kh };
                    const is_join = i == 11;
                    const ready = typed == 3;

                    if (rl.CheckCollisionPointRec(mouse, r)) {
                        if (moved) focus = i;

                        if (rl.IsMouseButtonPressed(rl.MOUSE_BUTTON_LEFT)) {
                            focus = i;
                            press = i;
                        }
                    }

                    const on = i == focus;
                    const fill = if (is_join and ready) ui.fade(ui.accent, if (on) 1 else 0.8) else ui.rgba(22, 26, 38, 255);

                    rl.DrawRectangleRounded(r, 0.2, 8, fill);
                    rl.DrawRectangleRoundedLinesEx(r, 0.2, 8, if (on) 2 * u else 1, if (on) ui.fade(ui.white, 0.85) else ui.edge);

                    const size = if (label.len > 1) 15 * u else 24 * u;
                    const ink = if (is_join and ready) ui.ink else if (is_join) ui.fade(ui.white, 0.35) else ui.white;

                    centeredCaps(font, label, r.x + kw / 2, r.y + kh / 2 - size / 2, size, ink);
                }

                if (err) |e| centered(font, e, w / 2, by - 34 * u, 16 * u, ui.red);

                hint(font, "Type digits or use the keypad    Backspace or X to delete    Esc or B to go back", w, h, u);
                rl.EndDrawing();

                if (in.ok) press = focus;

                if (in.back or back) {
                    screen = .online;

                    continue;
                }

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
                    screen = .connecting;
                }

                continue;
            },
            .connecting => {
                spinner(w / 2, h * 0.42, u);

                const failed = net.status == .timeout or net.status == .rejected;
                const label: [:0]const u8 = if (net.status == .timeout) "SERVER NOT REACHABLE" else if (net.status == .rejected) "COULD NOT JOIN" else if (joining) "JOINING ROOM" else "CREATING ROOM";

                centeredCaps(font, label, w / 2, h * 0.42 + 56 * u, 14 * u, if (failed) ui.red else ui.fade(ui.white, 0.7));

                if (net.status == .rejected) centered(font, reasonText(net.reason), w / 2, h * 0.42 + 84 * u, 16 * u, ui.fade(ui.white, 0.6));

                hint(font, if (failed) "Enter or A to retry    Esc or B to go back" else "Esc or B to cancel", w, h, u);
                rl.EndDrawing();

                if (in.back) {
                    net.cancel();
                    screen = if (joining) .join else .online;
                    err = null;

                    continue;
                }

                if (net.status == .rejected and joining) {
                    err = reasonText(net.reason);
                    typed = 0;
                    focus = 0;
                    net.status = .idle;
                    screen = .join;

                    continue;
                }

                if (failed and in.ok) {
                    if (joining) net.join(net.code) else net.create(net.map);
                }

                if (net.status == .joined) {
                    if (joining) {
                        net.active = true;

                        return @fromBackingInt(@intCast(net.map));
                    }

                    screen = .code;
                }

                continue;
            },
            .code => {
                var buf: [64]u8 = undefined;
                const room = std.fmt.bufPrintSentinel(&buf, "{d:0>3}", .{net.code}, 0) catch "---";
                const size = 168 * u;
                const cy = h * 0.22;

                centeredCaps(font, "ROOM CODE", w / 2, cy, 14 * u, ui.accent);
                centeredCaps(font, room, w / 2, cy + 30 * u, size, ui.white);

                const name = mapName(net.map);
                const where = std.fmt.bufPrintSentinel(buf[8..], "Map  {c}{s}", .{ std.ascii.toUpper(name[0]), name[1..] }, 0) catch "";

                centered(font, "Share this code with your friends", w / 2, cy + 40 * u + size, 18 * u, ui.fade(ui.white, 0.7));
                centered(font, where, w / 2, cy + 70 * u + size, 15 * u, ui.fade(ui.white, 0.45));
                hint(font, "Enter or A to start    Esc or B to close the room", w, h, u);
                rl.EndDrawing();

                if (in.back) {
                    net.cancel();
                    screen = .online;

                    continue;
                }

                if (in.ok or rl.IsMouseButtonPressed(rl.MOUSE_BUTTON_LEFT)) {
                    net.active = true;
                    rl.DisableCursor();

                    return @fromBackingInt(@intCast(net.map));
                }

                continue;
            },
        }

        rl.EndDrawing();
    }

    return null;
}

fn auto(font: rl.Font, spec: []const u8) ?Map {
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
        mapselect.loading(font, "Connecting", 0.05);

        if (net.status == .joined) {
            if (builtin.os.tag != .windows) {
                var buf: [512]u8 = undefined;
                const home = std.mem.sliceTo(std.c.getenv("HOME") orelse return null, 0);
                const path = std.fmt.bufPrintSentinel(&buf, "{s}/.cache/mp/room-{d}.txt", .{ home, std.c.getpid() }, 0) catch return null;
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
