const std = @import("std");
const rl = @import("raylib");
const shared = @import("shared");
const ui = @import("ui.zig");

const Map = shared.terrain.Map;

const Entry = struct {
    map: Map,
    name: [:0]const u8,
    note: [:0]const u8,
    tint: rl.Color,
};

const legacy = [_]Entry{
    .{ .map = .facility, .name = "Facility", .note = "Industrial hangar, close combat", .tint = .{ .r = 96, .g = 170, .b = 150, .a = 255 } },
    .{ .map = .conquest, .name = "Conquest", .note = "Military base, vehicles, aircraft", .tint = .{ .r = 210, .g = 120, .b = 70, .a = 255 } },
    .{ .map = .valley, .name = "Valley", .note = "Mountain pass and compounds", .tint = .{ .r = 150, .g = 130, .b = 110, .a = 255 } },
    .{ .map = .prism, .name = "Prism", .note = "Glass arena", .tint = .{ .r = 96, .g = 196, .b = 200, .a = 255 } },
    .{ .map = .courtyard, .name = "Courtyard", .note = "Desert arena", .tint = .{ .r = 226, .g = 176, .b = 132, .a = 255 } },
};

const max_entries = 32;

var entry_buf: [max_entries]Entry = undefined;

fn collect() []const Entry {
    var n: usize = 0;

    inline for (@typeInfo(Map).@"enum".field_names) |tag| {
        const m = @field(Map, tag);

        if (shared.maps.get(m)) |d| {
            if (d.ready and n < max_entries) {
                entry_buf[n] = .{ .map = m, .name = d.name, .note = d.note, .tint = .{ .r = d.tint[0], .g = d.tint[1], .b = d.tint[2], .a = 255 } };
                n += 1;
            }
        }
    }

    for (legacy) |e| {
        entry_buf[n] = e;
        n += 1;
    }

    return entry_buf[0..n];
}

fn padId() ?c_int {
    var i: c_int = 0;

    while (i < 4) : (i += 1) {
        if (rl.IsGamepadAvailable(i) and rl.GetGamepadAxisCount(i) >= 4) return i;
    }

    return null;
}

pub fn pick(font: rl.Font, dir: []const u8) ?Map {
    const entries = collect();
    var shots: [max_entries]?rl.Texture2D = @splat(null);

    for (entries, 0..) |e, i| {
        var buf: [512]u8 = undefined;
        const path = std.fmt.bufPrintSentinel(&buf, "{s}/maps/{s}.png", .{ dir, @tagName(e.map) }, 0) catch continue;

        if (!rl.FileExists(path.ptr)) continue;

        const tex = rl.LoadTexture(path.ptr);

        rl.SetTextureFilter(tex, rl.TEXTURE_FILTER_BILINEAR);
        shots[i] = tex;
    }

    defer for (shots[0..entries.len]) |s| {
        if (s) |t| rl.UnloadTexture(t);
    };

    var sel: usize = 0;
    var t: f32 = 0;
    var cool: f32 = 0;

    rl.EnableCursor();

    while (!rl.WindowShouldClose()) {
        const dt = rl.GetFrameTime();
        const w: f32 = @floatFromInt(rl.GetScreenWidth());
        const h: f32 = @floatFromInt(rl.GetScreenHeight());
        const u = h / 900;
        const cols: usize = 4;
        const gap = 22 * u;
        const rows: f32 = @floatFromInt((entries.len + cols - 1) / cols);
        const room = h * 0.7;
        const fit = (room - gap * (rows - 1)) / rows / 0.56;
        const cw = @min(@min(300 * u, (w - 160 * u - gap * 3) / 4), fit);
        const ch = cw * 0.56;
        const gx = (w - (cw * 4 + gap * 3)) / 2;
        const gy = h * 0.27;
        const pad = padId();
        var choose = false;

        t += dt;
        cool = @max(0, cool - dt);

        var dx: i32 = 0;
        var dy: i32 = 0;

        if (rl.IsKeyPressed(rl.KEY_RIGHT) or rl.IsKeyPressed(rl.KEY_D)) dx = 1;
        if (rl.IsKeyPressed(rl.KEY_LEFT) or rl.IsKeyPressed(rl.KEY_A)) dx = -1;
        if (rl.IsKeyPressed(rl.KEY_DOWN) or rl.IsKeyPressed(rl.KEY_S)) dy = 1;
        if (rl.IsKeyPressed(rl.KEY_UP) or rl.IsKeyPressed(rl.KEY_W)) dy = -1;
        if (rl.IsKeyPressed(rl.KEY_ENTER) or rl.IsKeyPressed(rl.KEY_SPACE)) choose = true;

        if (pad) |id| {
            const ax = rl.GetGamepadAxisMovement(id, rl.GAMEPAD_AXIS_LEFT_X);
            const ay = rl.GetGamepadAxisMovement(id, rl.GAMEPAD_AXIS_LEFT_Y);

            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_LEFT_FACE_RIGHT) or (ax > 0.6 and cool == 0)) dx = 1;
            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_LEFT_FACE_LEFT) or (ax < -0.6 and cool == 0)) dx = -1;
            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_LEFT_FACE_DOWN) or (ay > 0.6 and cool == 0)) dy = 1;
            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_LEFT_FACE_UP) or (ay < -0.6 and cool == 0)) dy = -1;
            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_FACE_DOWN)) choose = true;
            if (@abs(ax) > 0.6 or @abs(ay) > 0.6) {
                if (cool == 0) cool = 0.22;
            }
        }

        const n: i32 = @intCast(entries.len);
        var s: i32 = @intCast(sel);

        s += dx + dy * @as(i32, @intCast(cols));
        s = @mod(s, n);
        sel = @intCast(s);

        const mouse = rl.GetMousePosition();
        const moved = rl.GetMouseDelta().x != 0 or rl.GetMouseDelta().y != 0;

        rl.BeginDrawing();
        rl.ClearBackground(.{ .r = 11, .g = 13, .b = 20, .a = 255 });
        rl.DrawRectangleGradientV(0, 0, @intFromFloat(w), @intFromFloat(h), .{ .r = 20, .g = 24, .b = 36, .a = 255 }, .{ .r = 9, .g = 11, .b = 17, .a = 255 });

        const kicker: [:0]const u8 = "DRONEFIRE";
        const ks = 14 * u;

        ui.caps(font, kicker, gx, h * 0.1, ks, ui.accent);

        const title: [:0]const u8 = "SELECT MAP";
        const ts = 46 * u;

        ui.caps(font, title, gx, h * 0.1 + 22 * u, ts, ui.white);

        const sub: [:0]const u8 = "Arrows or stick to move    Enter or A to play";
        const ss = 15 * u;

        ui.text(font, sub, gx, h * 0.1 + 22 * u + ts + 10 * u, ss, ui.fade(ui.white, 0.5));

        for (entries, 0..) |e, i| {
            const col: f32 = @floatFromInt(i % cols);
            const row: f32 = @floatFromInt(i / cols);
            const r: rl.Rectangle = .{ .x = gx + (cw + gap) * col, .y = gy + (ch + gap) * row, .width = cw, .height = ch };

            if (rl.CheckCollisionPointRec(mouse, r)) {
                if (moved) sel = i;

                if (rl.IsMouseButtonPressed(rl.MOUSE_BUTTON_LEFT)) {
                    sel = i;
                    choose = true;
                }
            }

            const on = i == sel;
            const lift: f32 = if (on) -4 * u else 0;
            const card: rl.Rectangle = .{ .x = r.x, .y = r.y + lift, .width = r.width, .height = r.height };
            const img_h = card.height * 0.64;
            const round: f32 = 0.06;

            rl.DrawRectangleRounded(card, round, 8, .{ .r = 22, .g = 26, .b = 38, .a = 255 });

            if (shots[i]) |tex| {
                const tw: f32 = @floatFromInt(tex.width);
                const th: f32 = @floatFromInt(tex.height);
                const want = card.width / img_h;
                const src_h = @min(th, tw / want);
                const src: rl.Rectangle = .{ .x = 0, .y = (th - src_h) / 2, .width = tw, .height = src_h };
                const dst: rl.Rectangle = .{ .x = card.x, .y = card.y, .width = card.width, .height = img_h };

                rl.BeginScissorMode(@intFromFloat(card.x), @intFromFloat(card.y), @intFromFloat(card.width), @intFromFloat(img_h));
                rl.DrawTexturePro(tex, src, dst, .{ .x = 0, .y = 0 }, 0, if (on) rl.WHITE else rl.Color{ .r = 170, .g = 174, .b = 184, .a = 255 });
                rl.EndScissorMode();
            } else {
                rl.DrawRectangleRec(.{ .x = card.x, .y = card.y, .width = card.width, .height = img_h }, ui.fade(e.tint, 0.5));
            }

            rl.DrawRectangleGradientV(@intFromFloat(card.x), @intFromFloat(card.y + img_h * 0.55), @intFromFloat(card.width), @intFromFloat(img_h * 0.45 + 1), ui.fade(ui.ink, 0), ui.fade(.{ .r = 22, .g = 26, .b = 38, .a = 255 }, 1));

            const ns = @min(26 * u, cw * 0.087);
            const name_y = card.y + img_h + 8 * u;

            ui.caps(font, e.name, card.x + 18 * u, name_y, ns, ui.white);
            ui.text(font, e.note, card.x + 18 * u, name_y + ns + 6 * u, @min(15 * u, cw * 0.05), ui.fade(ui.white, 0.55));
            rl.DrawRectangleRec(.{ .x = card.x + 18 * u, .y = name_y - 6 * u, .width = 22 * u, .height = 2 * u }, ui.fade(e.tint, 0.9));

            rl.DrawRectangleRoundedLinesEx(card, round, 8, if (on) 2 * u else 1, if (on) ui.fade(ui.white, 0.85) else ui.edge);
        }

        rl.EndDrawing();

        if (choose) {
            rl.DisableCursor();

            return entries[sel].map;
        }
    }

    return null;
}

pub fn loading(font: rl.Font, label: [:0]const u8, progress: f32) void {
    const w: f32 = @floatFromInt(rl.GetScreenWidth());
    const h: f32 = @floatFromInt(rl.GetScreenHeight());
    const u = h / 900;
    const t: f32 = @floatCast(rl.GetTime());
    const c: rl.Vector2 = .{ .x = w / 2, .y = h / 2 - 20 * u };
    const r = 30 * u;
    const head = @mod(t * 320, 360);
    const span = 80 + 40 * @sin(t * 3);
    const p = std.math.clamp(progress, 0, 1);

    rl.BeginDrawing();
    rl.DrawRectangleGradientV(0, 0, @intFromFloat(w), @intFromFloat(h), .{ .r = 20, .g = 24, .b = 36, .a = 255 }, .{ .r = 9, .g = 11, .b = 17, .a = 255 });
    rl.DrawRing(c, r - 2.5 * u, r, 0, 360, 64, ui.fade(ui.white, 0.1));
    rl.DrawRing(c, r - 2.5 * u, r, head, head + span, 48, ui.accent);

    const ls = 14 * u;
    const lw = ui.capsWidth(font, label, ls);

    ui.caps(font, label, c.x - lw / 2, c.y + r + 26 * u, ls, ui.fade(ui.white, 0.7));

    const bw = 220 * u;
    const by = c.y + r + 52 * u;

    rl.DrawRectangleRec(.{ .x = c.x - bw / 2, .y = by, .width = bw, .height = 2 * u }, ui.fade(ui.white, 0.12));
    rl.DrawRectangleRec(.{ .x = c.x - bw / 2, .y = by, .width = bw * p, .height = 2 * u }, ui.accent);
    rl.EndDrawing();
}
