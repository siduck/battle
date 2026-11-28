const std = @import("std");
const rl = @import("raylib");
const shared = @import("shared");
const theme = @import("theme.zig");
const mips = @import("mips.zig");
const backdrop = @import("backdrop.zig");

const Map = shared.terrain.Map;

const Entry = struct {
    map: Map,
    name: [:0]const u8,
    note: [:0]const u8,
    tint: rl.Color,
};

const max_entries = 32;
const map_count = @typeInfo(Map).@"enum".field_names.len;

var entry_buf: [max_entries]Entry = undefined;
var shots: [map_count]?rl.Texture2D = @splat(null);
var dir_buf: [512]u8 = undefined;
var dir_len: usize = 0;
var picked: usize = 0;

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

    return entry_buf[0..n];
}

fn padId() ?c_int {
    var i: c_int = 0;

    while (i < 4) : (i += 1) {
        if (rl.IsGamepadAvailable(i) and rl.GetGamepadAxisCount(i) >= 4) return i;
    }

    return null;
}

pub fn setDir(dir: []const u8) void {
    dir_len = @min(dir.len, dir_buf.len);
    @memcpy(dir_buf[0..dir_len], dir[0..dir_len]);
}

pub fn thumb(m: Map) ?rl.Texture2D {
    const i: usize = @backingInt(m);

    if (shots[i]) |t| return t;

    if (dir_len == 0) return null;

    var buf: [640]u8 = undefined;
    const path = std.fmt.bufPrintSentinel(&buf, "{s}/maps/{s}.png", .{ dir_buf[0..dir_len], @tagName(m) }, 0) catch return null;
    const tex = mips.load(path.ptr);

    if (tex.id == 0) return null;

    rl.SetTextureFilter(tex, rl.TEXTURE_FILTER_TRILINEAR);
    rl.SetTextureWrap(tex, rl.TEXTURE_WRAP_CLAMP);
    shots[i] = tex;

    return tex;
}

pub fn release(keep: ?Map) void {
    for (&shots, 0..) |*s, i| {
        if (keep) |m| {
            if (@backingInt(m) == i) continue;
        }

        if (s.*) |t| rl.UnloadTexture(t);

        s.* = null;
    }
}

pub fn picture(m: Map, r: rl.Rectangle, radius: f32, frame: rl.Color, tint: rl.Color, a: f32) void {
    if (thumb(m)) |tex| {
        const tw: f32 = @floatFromInt(tex.width);
        const th: f32 = @floatFromInt(tex.height);
        const want = r.width / r.height;
        const src_w = @min(tw, th * want);
        const src_h = @min(th, tw / want);
        const src: rl.Rectangle = .{ .x = (tw - src_w) / 2, .y = (th - src_h) / 2, .width = src_w, .height = src_h };

        rl.DrawTexturePro(tex, src, r, .{ .x = 0, .y = 0 }, 0, theme.fade(tint, a));
    } else {
        rl.DrawRectangleRec(r, theme.fade(theme.teal, a));
    }

    theme.notch(r, radius, theme.fade(frame, a));
}

pub fn pick() ?Map {
    const entries = collect();
    var cool: f32 = 0;

    if (entries.len == 0) return null;

    var sel: usize = @min(picked, entries.len - 1);

    rl.EnableCursor();

    while (!rl.WindowShouldClose()) {
        const dt = rl.GetFrameTime();
        var choose = false;
        var back = false;
        var dx: i32 = 0;
        var dy: i32 = 0;

        cool = @max(0, cool - dt);

        if (rl.IsKeyPressed(rl.KEY_RIGHT) or rl.IsKeyPressed(rl.KEY_D)) dx = 1;
        if (rl.IsKeyPressed(rl.KEY_LEFT) or rl.IsKeyPressed(rl.KEY_A)) dx = -1;
        if (rl.IsKeyPressed(rl.KEY_DOWN) or rl.IsKeyPressed(rl.KEY_S)) dy = 1;
        if (rl.IsKeyPressed(rl.KEY_UP) or rl.IsKeyPressed(rl.KEY_W)) dy = -1;
        if (rl.IsKeyPressed(rl.KEY_ENTER) or rl.IsKeyPressed(rl.KEY_SPACE)) choose = true;
        if (rl.IsKeyPressed(rl.KEY_ESCAPE) or rl.IsKeyPressed(rl.KEY_BACK)) back = true;

        const pad = padId();

        if (pad) |id| {
            const ax = rl.GetGamepadAxisMovement(id, rl.GAMEPAD_AXIS_LEFT_X);
            const ay = rl.GetGamepadAxisMovement(id, rl.GAMEPAD_AXIS_LEFT_Y);

            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_LEFT_FACE_RIGHT) or (ax > 0.6 and cool == 0)) dx = 1;
            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_LEFT_FACE_LEFT) or (ax < -0.6 and cool == 0)) dx = -1;
            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_LEFT_FACE_DOWN) or (ay > 0.6 and cool == 0)) dy = 1;
            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_LEFT_FACE_UP) or (ay < -0.6 and cool == 0)) dy = -1;
            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_FACE_DOWN)) choose = true;
            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_FACE_RIGHT)) back = true;

            if ((@abs(ax) > 0.6 or @abs(ay) > 0.6) and cool == 0) cool = 0.22;
        }

        backdrop.open(dt);
        theme.enterScene(theme.tag("maps", 0));
        theme.dim(0.6);

        const v = theme.view();
        const u = v.u;
        const gap = 22 * u;
        const keyed = v.keyed();
        const top = v.top + theme.headerHeight(v) + 30 * u;
        const avail_w = v.width();
        const avail_h = v.bottom - top - (if (keyed) 56 * u else 0);
        const ratio = 0.72;
        var cols: usize = 3;
        var cw: f32 = 0;
        var try_cols: usize = 3;

        while (try_cols <= 8) : (try_cols += 1) {
            const tc: f32 = @floatFromInt(try_cols);
            const tr: f32 = @floatFromInt((entries.len + try_cols - 1) / try_cols);
            const by_w = (avail_w - gap * (tc - 1)) / tc;
            const by_h = (avail_h - gap * (tr - 1)) / tr / ratio;
            const size = @min(by_w, by_h);

            if (size > cw) {
                cw = size;
                cols = try_cols;
            }
        }

        const n: i32 = @intCast(entries.len);

        sel = @intCast(@mod(@as(i32, @intCast(sel)) + dx + dy * @as(i32, @intCast(cols)), n));

        const rows: f32 = @floatFromInt((entries.len + cols - 1) / cols);
        const fc: f32 = @floatFromInt(cols);
        const ch = cw * ratio;
        const gx = v.cx() - (cw * fc + gap * (fc - 1)) / 2;
        const gy = top + @max(0, (avail_h - (ch * rows + gap * (rows - 1))) / 2);

        if (theme.header("CHOOSE A MAP", "")) back = true;

        for (entries, 0..) |e, i| {
            const col: f32 = @floatFromInt(i % cols);
            const row: f32 = @floatFromInt(i / cols);
            const r: rl.Rectangle = .{ .x = gx + (cw + gap) * col, .y = gy + (ch + gap) * row, .width = cw, .height = ch };
            const in = theme.reveal(1 + (col + row) * 0.8);
            const b = theme.button(theme.tag("map", i), r, 20 * u, theme.tones.cream_tone, i == sel, in);

            if (b.hot) sel = i;

            if (b.click) {
                sel = i;
                choose = true;
            }

            const f = b.face;
            const pad_in = @max(6 * u, cw * 0.022);
            const iw = f.width - pad_in * 2;
            const ih = @min(iw * 0.52, f.height * 0.7);
            const image: rl.Rectangle = .{ .x = f.x + pad_in, .y = f.y + pad_in, .width = iw, .height = ih };

            picture(e.map, image, 14 * u, theme.cream, rl.WHITE, in.a);

            const room = f.y + f.height - (image.y + image.height);
            const name_size = @min(room * 0.6, cw * 0.11);
            const note_size = @min(room * 0.36, cw * 0.064);
            const tx = f.x + pad_in + 6 * u;
            const mid = image.y + image.height;
            const name_w = iw - 12 * u;

            theme.write(theme.heavy, e.name, tx, mid + room * 0.36, theme.fit(theme.heavy, e.name, name_size, name_w), theme.fade(theme.navy, in.a));
            theme.write(theme.body, e.note, tx, mid + room * 0.75, theme.fit(theme.body, e.note, note_size, name_w), theme.fade(theme.soft, in.a));

            if (i == sel) {
                const s = cw * 0.16;
                const badge: rl.Rectangle = .{ .x = image.x + image.width - s - 10 * u, .y = image.y + image.height - s - 10 * u, .width = s, .height = s };

                theme.round(theme.offset(badge, 0, 5 * u), s / 2, theme.fade(theme.rust, in.a));
                theme.round(badge, s / 2, theme.fade(theme.coral, in.a));
                theme.icon(.play, badge.x + s / 2, badge.y + s / 2, s * 0.62, theme.fade(theme.cream, in.a));
            }
        }

        if (keyed) {
            const items: []const theme.Hint = if (theme.pad_live) &.{ .{ .key = "D-PAD", .label = "Choose" }, .{ .key = "A", .label = "Play" }, .{ .key = "B", .label = "Back" } } else &.{ .{ .key = "ARROWS", .label = "Choose" }, .{ .key = "ENTER", .label = "Play" }, .{ .key = "ESC", .label = "Back" } };
            const size = 19 * u;

            theme.hints(items, v.cx() - theme.hintsWidth(items, size) / 2, v.bottom - 16 * u, size, theme.reveal(3).a);
        }

        backdrop.close(dt);

        if (back) return null;

        if (choose) {
            picked = sel;
            rl.DisableCursor();

            return entries[sel].map;
        }
    }

    return null;
}

pub fn loading(label: [:0]const u8, progress: f32) void {
    const v = theme.view();
    const u = v.u;
    const p = std.math.clamp(progress, 0, 1);
    const m = shared.terrain.current;
    const def = shared.maps.get(m);

    rl.BeginDrawing();
    rl.ClearBackground(theme.night);

    const iw = @min(680 * u, v.width() * 0.62);
    const ih = iw * 0.5;
    const total = ih + 250 * u;
    const x = v.cx() - iw / 2;
    var y = v.h / 2 - total / 2;

    if (def) |d| {
        const frame: rl.Rectangle = .{ .x = x - 12 * u, .y = y, .width = iw + 24 * u, .height = ih + 24 * u };

        theme.panel(frame, 28 * u, theme.cream, 1);
        picture(m, .{ .x = x, .y = y + 12 * u, .width = iw, .height = ih }, 18 * u, theme.cream, rl.WHITE, 1);
        y += ih + 78 * u;
        theme.extruded(theme.heavy, d.name, v.cx() - theme.measure(theme.heavy, d.name, 76 * u) / 2, y, 76 * u, theme.cream, 1);
        y += 56 * u;
        theme.center(theme.body, d.note, v.cx(), y, 28 * u, theme.fade(theme.cream, 0.72));
        y += 56 * u;
    } else {
        const lw = @min(460 * u, iw);

        theme.lockup(v.cx() - lw / 2, v.h / 2 - theme.lockupHeight(lw) * 0.85, lw, .{}, .{});
        y = v.h / 2 + 130 * u;
    }

    const bw = @min(520 * u, iw);
    const bar: rl.Rectangle = .{ .x = v.cx() - bw / 2, .y = y, .width = bw, .height = 20 * u };

    theme.round(theme.offset(bar, 0, 5 * u), 10 * u, theme.fade(rl.BLACK, 0.35));
    theme.round(bar, 10 * u, theme.slate);

    if (p > 0.001) theme.round(.{ .x = bar.x, .y = bar.y, .width = @max(bar.height, bw * p), .height = bar.height }, 10 * u, theme.sun);

    var pct_buf: [64]u8 = undefined;
    const line = std.fmt.bufPrintSentinel(&pct_buf, "{s}  {d}%", .{ label, @as(u32, @intFromFloat(p * 100)) }, 0) catch label;

    theme.center(theme.body, line, v.cx(), bar.y + 52 * u, 25 * u, theme.fade(theme.cream, 0.82));
    theme.spinner(v.right - 30 * u, v.bottom - 30 * u, 24 * u, theme.fade(theme.cream, 0.14), theme.coral);
    rl.EndDrawing();
}
