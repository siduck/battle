const std = @import("std");
const builtin = @import("builtin");
const rl = @import("raylib");
const assets = @import("assets.zig");

pub const Preset = enum { low, medium, high, custom };

pub var master: f32 = 1;
pub var sfx: f32 = 1;
pub var ui: f32 = 0.8;

pub var mouse_sens: f32 = 1;
pub var ads_sens: f32 = 0.75;
pub var invert_y = false;
pub var fov: f32 = 74;
pub var crosshair_style: u8 = 0;
pub var crosshair_color: u8 = 0;
pub var show_fps = true;
pub var god_mode = true;

pub var stick_sens: f32 = 1;
pub var aim_assist: f32 = 1;
pub var deadzone: f32 = 0.12;
pub var vibration = true;

pub var preset: Preset = .high;
pub var shadows: u8 = if (assets.mobile) 0 else 0;
pub var effects: u8 = if (assets.mobile) 0 else 1;
pub var msaa = true;
pub var render_scale: f32 = 1;
pub var view_dist: f32 = 1;
pub var vsync = true;
pub var fullscreen = false;

pub var touch_size: f32 = 1;
pub var touch_opacity: f32 = 1;
pub var touch_look: f32 = 1;

pub var player_name: [16]u8 = @splat(0);

pub const crosshair_styles = [_][:0]const u8{ "Classic", "Dot", "Circle", "Cross" };
pub const crosshair_names = [_][:0]const u8{ "White", "Green", "Yellow", "Cyan", "Red" };
pub const crosshair_colors = [_]rl.Color{
    .{ .r = 255, .g = 255, .b = 255, .a = 255 },
    .{ .r = 110, .g = 240, .b = 140, .a = 255 },
    .{ .r = 255, .g = 214, .b = 70, .a = 255 },
    .{ .r = 90, .g = 230, .b = 255, .a = 255 },
    .{ .r = 255, .g = 90, .b = 90, .a = 255 },
};
pub const shadow_names = [_][:0]const u8{ "Off", "Medium", "High" };
pub const effects_names = [_][:0]const u8{ "Off", "High", "Ultra" };
pub const preset_names = [_][:0]const u8{ "Low", "Medium", "High", "Custom" };

pub fn crosshairColor() rl.Color {
    return crosshair_colors[@min(crosshair_color, crosshair_colors.len - 1)];
}

pub fn shadowRes() c_int {
    return if (shadows <= 1) 1024 else 2048;
}

pub fn volume(kind: enum { sfx, ui }) f32 {
    return master * switch (kind) {
        .sfx => sfx,
        .ui => ui,
    };
}

pub fn applyPreset(p: Preset) void {
    preset = p;

    switch (p) {
        .low => {
            shadows = 0;
            effects = 0;
            render_scale = 0.7;
            view_dist = 0.6;
        },
        .medium => {
            shadows = if (assets.mobile) 0 else 0;
            effects = if (assets.mobile) 0 else 1;
            render_scale = 0.85;
            view_dist = 0.8;
        },
        .high => {
            shadows = if (assets.mobile) 0 else 0;
            effects = if (assets.mobile) 0 else 1;
            render_scale = 1;
            view_dist = 1;
        },
        .custom => {},
    }
}

pub fn reset() void {
    master = 1;
    sfx = 1;
    ui = 0.8;
    mouse_sens = 1;
    ads_sens = 0.75;
    invert_y = false;
    fov = 74;
    crosshair_style = 0;
    crosshair_color = 0;
    show_fps = true;
    god_mode = true;
    stick_sens = 1;
    aim_assist = 1;
    deadzone = 0.12;
    vibration = true;
    msaa = true;
    vsync = true;
    fullscreen = false;
    touch_size = 1;
    touch_opacity = 1;
    touch_look = 1;
    applyPreset(if (assets.mobile) .medium else .high);
}

var path_buf: [512]u8 = undefined;

fn readPath() ?[:0]const u8 {
    if (assets.mobile) return "/data/data/com.dronefire.game/files/settings.ini";

    return writePath();
}

extern "c" fn _mkdir(path: [*:0]const u8) c_int;

fn writePath() ?[:0]const u8 {
    if (assets.mobile) return "settings.ini";

    if (builtin.os.tag == .windows) {
        const base = std.c.getenv("APPDATA") orelse return null;
        const dir = std.fmt.bufPrintSentinel(&path_buf, "{s}\\dronefire", .{std.mem.sliceTo(base, 0)}, 0) catch return null;

        _ = _mkdir(dir.ptr);

        return std.fmt.bufPrintSentinel(&path_buf, "{s}\\dronefire\\settings.ini", .{std.mem.sliceTo(base, 0)}, 0) catch null;
    }

    if (std.c.getenv("XDG_CONFIG_HOME")) |base| {
        const dir = std.fmt.bufPrintSentinel(&path_buf, "{s}/dronefire", .{std.mem.sliceTo(base, 0)}, 0) catch return null;

        _ = std.c.mkdir(dir.ptr, 0o755);

        return std.fmt.bufPrintSentinel(&path_buf, "{s}/dronefire/settings.ini", .{std.mem.sliceTo(base, 0)}, 0) catch null;
    }

    const home = std.c.getenv("HOME") orelse return null;
    const config = std.fmt.bufPrintSentinel(&path_buf, "{s}/.config", .{std.mem.sliceTo(home, 0)}, 0) catch return null;

    _ = std.c.mkdir(config.ptr, 0o755);

    const dir = std.fmt.bufPrintSentinel(&path_buf, "{s}/.config/dronefire", .{std.mem.sliceTo(home, 0)}, 0) catch return null;

    _ = std.c.mkdir(dir.ptr, 0o755);

    return std.fmt.bufPrintSentinel(&path_buf, "{s}/.config/dronefire/settings.ini", .{std.mem.sliceTo(home, 0)}, 0) catch null;
}

const Field = struct {
    name: []const u8,
    ptr: union(enum) { f: *f32, b: *bool, u: *u8, s: *[16]u8 },
};

fn fields() [25]Field {
    return .{
        .{ .name = "master", .ptr = .{ .f = &master } },
        .{ .name = "sfx", .ptr = .{ .f = &sfx } },
        .{ .name = "ui", .ptr = .{ .f = &ui } },
        .{ .name = "mouse_sens", .ptr = .{ .f = &mouse_sens } },
        .{ .name = "ads_sens", .ptr = .{ .f = &ads_sens } },
        .{ .name = "invert_y", .ptr = .{ .b = &invert_y } },
        .{ .name = "fov", .ptr = .{ .f = &fov } },
        .{ .name = "crosshair_style", .ptr = .{ .u = &crosshair_style } },
        .{ .name = "crosshair_color", .ptr = .{ .u = &crosshair_color } },
        .{ .name = "show_fps", .ptr = .{ .b = &show_fps } },
        .{ .name = "stick_sens", .ptr = .{ .f = &stick_sens } },
        .{ .name = "aim_assist", .ptr = .{ .f = &aim_assist } },
        .{ .name = "deadzone", .ptr = .{ .f = &deadzone } },
        .{ .name = "vibration", .ptr = .{ .b = &vibration } },
        .{ .name = "shadows", .ptr = .{ .u = &shadows } },
        .{ .name = "effects", .ptr = .{ .u = &effects } },
        .{ .name = "msaa", .ptr = .{ .b = &msaa } },
        .{ .name = "render_scale", .ptr = .{ .f = &render_scale } },
        .{ .name = "view_dist", .ptr = .{ .f = &view_dist } },
        .{ .name = "vsync", .ptr = .{ .b = &vsync } },
        .{ .name = "fullscreen", .ptr = .{ .b = &fullscreen } },
        .{ .name = "touch_size", .ptr = .{ .f = &touch_size } },
        .{ .name = "touch_opacity", .ptr = .{ .f = &touch_opacity } },
        .{ .name = "touch_look", .ptr = .{ .f = &touch_look } },
        .{ .name = "name", .ptr = .{ .s = &player_name } },
    };
}

pub fn load() void {
    reset();

    const path = readPath() orelse return;

    if (!rl.FileExists(path.ptr)) return;

    const data = rl.LoadFileText(path.ptr);

    if (data == null) return;

    defer rl.UnloadFileText(data);

    const text: [*:0]const u8 = @ptrCast(data);
    var lines = std.mem.splitScalar(u8, std.mem.sliceTo(text, 0), '\n');
    const all = fields();

    while (lines.next()) |raw| {
        const line = std.mem.trim(u8, raw, " \r\t");
        const eq = std.mem.indexOfScalar(u8, line, '=') orelse continue;
        const key = std.mem.trim(u8, line[0..eq], " ");
        const val = std.mem.trim(u8, line[eq + 1 ..], " ");

        if (std.mem.eql(u8, key, "preset")) {
            preset = std.meta.stringToEnum(Preset, val) orelse preset;

            continue;
        }

        for (all) |f| {
            if (!std.mem.eql(u8, f.name, key)) continue;

            switch (f.ptr) {
                .f => |p| p.* = std.fmt.parseFloat(f32, val) catch p.*,
                .b => |p| p.* = std.mem.eql(u8, val, "1") or std.mem.eql(u8, val, "true"),
                .u => |p| p.* = std.fmt.parseInt(u8, val, 10) catch p.*,
                .s => |p| {
                    p.* = @splat(0);

                    var n: usize = 0;

                    for (val) |ch| {
                        if (n >= 12 or ch < 32 or ch >= 127) continue;

                        p[n] = ch;
                        n += 1;
                    }
                },
            }
        }
    }

    shadows = @min(shadows, 2);
    effects = if (assets.mobile) 0 else @min(effects, 2);
    crosshair_style = @min(crosshair_style, crosshair_styles.len - 1);
    crosshair_color = @min(crosshair_color, crosshair_colors.len - 1);
}

pub fn save() void {
    const path = writePath() orelse return;
    var buf: [2048]u8 = undefined;
    var len: usize = 0;
    const head = std.fmt.bufPrint(buf[len..], "preset={s}\n", .{@tagName(preset)}) catch return;

    len += head.len;

    for (fields()) |f| {
        const line = switch (f.ptr) {
            .f => |p| std.fmt.bufPrint(buf[len..], "{s}={d:.3}\n", .{ f.name, p.* }),
            .b => |p| std.fmt.bufPrint(buf[len..], "{s}={d}\n", .{ f.name, @intFromBool(p.*) }),
            .u => |p| std.fmt.bufPrint(buf[len..], "{s}={d}\n", .{ f.name, p.* }),
            .s => |p| std.fmt.bufPrint(buf[len..], "{s}={s}\n", .{ f.name, std.mem.sliceTo(p, 0) }),
        } catch return;

        len += line.len;
    }

    if (len >= buf.len) return;

    buf[len] = 0;
    _ = rl.SaveFileText(path.ptr, @ptrCast(&buf));
}
