const std = @import("std");
const rl = @import("raylib");
const gfx = @import("gfx.zig");
const game_mod = @import("game.zig");
const models_mod = @import("models.zig");
const render = @import("render.zig");
const hud = @import("hud.zig");
const rumble_mod = @import("rumble.zig");
const gunart = @import("gunart.zig");
const propart = @import("propart.zig");
const icons_mod = @import("icons.zig");
const soldier = @import("soldier.zig");
const vehicleart = @import("vehicleart.zig");
const driving = @import("driving.zig");
const air = @import("air.zig");
const shared = @import("shared");
const assets = @import("assets.zig");
const touch_mod = @import("touch.zig");
const mapselect = @import("mapselect.zig");
const mesh_mod = @import("mesh.zig");
const audio = @import("audio.zig");
const ui = @import("ui.zig");
const settings = @import("settings.zig");
const menu_mod = @import("menu.zig");
const loadout_mod = @import("loadout.zig");

const Game = game_mod.Game;
const Controls = game_mod.Controls;

const mouse_sensitivity: f32 = 0.0022;
const move_deadzone: f32 = 0.15;
const trigger_threshold: f32 = 0.3;
const yaw_rate: f32 = 3.4;
const pitch_rate: f32 = 2.4;
const hold_to_pick: f32 = 0.3;

const font_data = @embedFile("assets/BarlowCondensed-SemiBold.ttf");
const extra_mappings = "03000000373500001201000011010000,GameSir G8+ MFi,a:b0,b:b1,back:b10,dpdown:h0.4,dpleft:h0.8,dpright:h0.2,dpup:h0.1,guide:b12,leftshoulder:b6,leftstick:b13,lefttrigger:a5,leftx:a0,lefty:a1,misc1:b15,rightshoulder:b7,rightstick:b14,righttrigger:a4,rightx:a2,righty:a3,start:b11,x:b3,y:b4,platform:Linux,\n";
const controller_db = @embedFile("assets/gamecontrollerdb.txt") ++ "\n" ++ extra_mappings;

fn parseVec(text: []const u8) shared.math.Vec3 {
    var it = std.mem.splitScalar(u8, text, ',');
    var out: [3]f32 = .{ 0, 0, 0 };

    for (&out) |*o| o.* = std.fmt.parseFloat(f32, it.next() orelse "0") catch 0;

    return .{ .x = out[0], .y = out[1], .z = out[2] };
}

fn parse4(text: []const u8, fallback: [4]f32) [4]f32 {
    var out = fallback;
    var it = std.mem.splitScalar(u8, text, ',');
    var i: usize = 0;

    while (it.next()) |part| : (i += 1) {
        if (i >= 4) break;

        out[i] = std.fmt.parseFloat(f32, part) catch out[i];
    }

    return out;
}

fn loadFont(data: []const u8) rl.Font {
    var font = rl.LoadFontFromMemory(".ttf", data.ptr, @intCast(data.len), 96, null, 0);

    rl.GenTextureMipmaps(&font.texture);
    rl.SetTextureFilter(font.texture, rl.TEXTURE_FILTER_TRILINEAR);

    return font;
}

fn winSize(part: usize, fallback: c_int) c_int {
    const t = std.c.getenv("DF_WIN") orelse return fallback;
    var it = std.mem.splitScalar(u8, std.mem.sliceTo(t, 0), 'x');

    if (part == 1) _ = it.next();

    return std.fmt.parseInt(c_int, it.next() orelse return fallback, 10) catch fallback;
}

fn axis(negative: c_int, positive: c_int) f32 {
    var value: f32 = 0;

    if (rl.IsKeyDown(positive)) value += 1;
    if (rl.IsKeyDown(negative)) value -= 1;

    return value;
}

const Stick = struct {
    x: f32 = 0,
    y: f32 = 0,
    mag: f32 = 0,
};

fn stick(pad: c_int, ax: c_int, ay: c_int, deadzone: f32) Stick {
    const x = rl.GetGamepadAxisMovement(pad, ax);
    const y = rl.GetGamepadAxisMovement(pad, ay);
    const len = @sqrt(x * x + y * y);

    if (len < deadzone) return .{};

    const scaled = @min(1, (len - deadzone) / (0.95 - deadzone));

    return .{ .x = x / len * scaled, .y = y / len * scaled, .mag = scaled };
}

fn trigger(pad: c_int, ax: c_int) f32 {
    return @min(1, @max(0, (rl.GetGamepadAxisMovement(pad, ax) + 1) / 2));
}

const Pad = struct {
    id: ?c_int = null,
    fire_held: bool = false,
    aim_held: bool = false,
    x_held: f32 = 0,
    y_held: f32 = 0,
    y_used: bool = false,
    x_used: bool = false,
    edge_time: f32 = 0,
    active: bool = false,
    hall: bool = false,

    fn find(p: *Pad) void {
        var i: c_int = 0;

        p.id = null;

        if (no_pad) return;

        while (i < 4) : (i += 1) {
            if (rl.IsGamepadAvailable(i) and realPad(std.mem.span(rl.GetGamepadName(i)))) {
                p.id = i;
                p.hall = std.mem.indexOf(u8, std.mem.span(rl.GetGamepadName(i)), "GameSir") != null;

                return;
            }
        }
    }

    fn pressed(p: Pad, button: c_int) bool {
        const id = p.id orelse return false;

        return rl.IsGamepadButtonPressed(id, button);
    }

    fn down(p: Pad, button: c_int) bool {
        const id = p.id orelse return false;

        return rl.IsGamepadButtonDown(id, button);
    }
};

const Frame = struct {
    controls: Controls = .{},
    look: Stick = .{},
    aim_started: bool = false,
    pad_used: bool = false,
    pad_button: bool = false,
};

fn readKeyboard(captured: bool, scoped: bool) Controls {
    if (!captured) return .{};

    const keys = [_]c_int{ rl.KEY_ONE, rl.KEY_TWO, rl.KEY_THREE, rl.KEY_FOUR, rl.KEY_FIVE };
    var select: ?u8 = null;

    for (keys, 0..) |k, i| {
        if (rl.IsKeyPressed(k)) select = @intCast(i);
    }

    const wheel = rl.GetMouseWheelMove();

    return .{
        .forward = axis(rl.KEY_S, rl.KEY_W),
        .right = axis(rl.KEY_A, rl.KEY_D),
        .jump = rl.IsKeyDown(rl.KEY_SPACE),
        .fire_down = rl.IsMouseButtonDown(rl.MOUSE_BUTTON_LEFT),
        .fire_pressed = rl.IsMouseButtonPressed(rl.MOUSE_BUTTON_LEFT),
        .aim = rl.IsMouseButtonDown(rl.MOUSE_BUTTON_RIGHT),
        .reload = rl.IsKeyPressed(rl.KEY_R),
        .grenade = rl.IsKeyPressed(rl.KEY_G),
        .interact = rl.IsKeyPressed(rl.KEY_E),
        .select = select,
        .cycle = if (scoped) 0 else if (wheel > 0) -1 else if (wheel < 0) 1 else 0,
        .quick_swap = rl.IsKeyPressed(rl.KEY_Q),
        .zoom_step = if (!scoped) 0 else if (wheel > 0) 1 else if (wheel < 0) -1 else 0,
        .steady = rl.IsKeyDown(rl.KEY_LEFT_SHIFT),
        .boost = rl.IsKeyDown(rl.KEY_LEFT_SHIFT) or rl.IsKeyDown(rl.KEY_RIGHT_SHIFT),
        .throw_gun = rl.IsKeyPressed(rl.KEY_T),
        .fireball = rl.IsKeyDown(rl.KEY_X),
        .enter = rl.IsKeyPressed(rl.KEY_F),
    };
}

fn readPad(p: *Pad, dt: f32, knife_active: bool, scoped: bool) Frame {
    const id = p.id orelse return .{};
    const look_dead = if (p.hall and settings.deadzone == 0.12) 0.04 else settings.deadzone;
    const move = stick(id, rl.GAMEPAD_AXIS_LEFT_X, rl.GAMEPAD_AXIS_LEFT_Y, if (p.hall) 0.05 else move_deadzone);
    const look = stick(id, rl.GAMEPAD_AXIS_RIGHT_X, rl.GAMEPAD_AXIS_RIGHT_Y, look_dead);
    const in_car = driving.driving() or air.flying();
    const rt = trigger(id, rl.GAMEPAD_AXIS_RIGHT_TRIGGER);
    const lt = trigger(id, rl.GAMEPAD_AXIS_LEFT_TRIGGER);
    const fire = if (in_car) p.down(rl.GAMEPAD_BUTTON_RIGHT_TRIGGER_1) else rt > trigger_threshold;
    const aim = if (in_car) p.down(rl.GAMEPAD_BUTTON_LEFT_TRIGGER_1) else lt > trigger_threshold;
    const fire_pressed = fire and !p.fire_held;
    const aim_started = aim and !p.aim_held;
    var reload = false;
    var interact = false;

    p.fire_held = fire;
    p.aim_held = aim;

    if (p.down(rl.GAMEPAD_BUTTON_RIGHT_FACE_LEFT)) {
        p.x_held += dt;

        if (p.x_held >= hold_to_pick and !p.x_used) {
            interact = true;
            p.x_used = true;
        }
    } else {
        if (p.x_held > 0 and !p.x_used) reload = true;

        p.x_held = 0;
        p.x_used = false;
    }

    var enter = false;
    var reset = false;

    if (in_car and p.down(rl.GAMEPAD_BUTTON_RIGHT_FACE_UP)) {
        p.y_held += dt;

        if (p.y_held >= 0.7 and !p.y_used) {
            reset = true;
            p.y_used = true;
        }
    } else {
        if (in_car and p.y_held > 0 and !p.y_used) enter = true;

        p.y_held = 0;
        p.y_used = false;
    }

    if (!in_car and p.pressed(rl.GAMEPAD_BUTTON_RIGHT_FACE_UP)) enter = true;

    var cycle: i32 = 0;

    if (p.pressed(rl.GAMEPAD_BUTTON_LEFT_FACE_RIGHT)) cycle = 1;
    if (p.pressed(rl.GAMEPAD_BUTTON_LEFT_FACE_LEFT)) cycle = -1;

    var zoom_step: i32 = 0;

    if (scoped and p.pressed(rl.GAMEPAD_BUTTON_LEFT_FACE_UP)) zoom_step = 1;
    if (scoped and p.pressed(rl.GAMEPAD_BUTTON_LEFT_FACE_DOWN)) zoom_step = -1;

    const knife_button = (!in_car and p.pressed(rl.GAMEPAD_BUTTON_RIGHT_FACE_RIGHT)) or (!scoped and p.pressed(rl.GAMEPAD_BUTTON_LEFT_FACE_UP));
    const jump = p.down(rl.GAMEPAD_BUTTON_RIGHT_FACE_DOWN);
    const buttons = jump or p.down(rl.GAMEPAD_BUTTON_RIGHT_FACE_LEFT) or p.down(rl.GAMEPAD_BUTTON_RIGHT_FACE_UP) or p.down(rl.GAMEPAD_BUTTON_RIGHT_FACE_RIGHT);

    return .{
        .controls = .{
            .forward = -move.y,
            .right = move.x,
            .jump = jump,
            .fire_down = fire,
            .fire_pressed = fire_pressed,
            .aim = aim,
            .reload = reload,
            .grenade = !in_car and p.pressed(rl.GAMEPAD_BUTTON_RIGHT_TRIGGER_1),
            .gas = if (in_car) pedalAxis(rt) else 0,
            .brake_pedal = if (in_car) pedalAxis(lt) else 0,
            .interact = interact,
            .select = if (knife_button and !knife_active) game_mod.knife_slot else null,
            .cycle = cycle,
            .quick_swap = p.pressed(rl.GAMEPAD_BUTTON_LEFT_TRIGGER_1) or (knife_button and knife_active),
            .zoom_step = zoom_step,
            .steady = p.down(rl.GAMEPAD_BUTTON_LEFT_THUMB),
            .boost = in_car and (p.down(rl.GAMEPAD_BUTTON_LEFT_THUMB) or p.down(rl.GAMEPAD_BUTTON_RIGHT_FACE_RIGHT)),
            .throw_gun = !scoped and p.pressed(rl.GAMEPAD_BUTTON_LEFT_FACE_DOWN),
            .fireball = p.down(rl.GAMEPAD_BUTTON_RIGHT_THUMB),
            .enter = enter,
            .reset = reset,
        },
        .look = look,
        .aim_started = aim_started,
        .pad_used = move.mag > 0 or look.mag > 0 or fire or aim or buttons,
        .pad_button = buttons,
    };
}

fn merge(a: Controls, b: Controls) Controls {
    return .{
        .forward = std.math.clamp(a.forward + b.forward, -1, 1),
        .right = std.math.clamp(a.right + b.right, -1, 1),
        .gas = @max(a.gas, b.gas),
        .brake_pedal = @max(a.brake_pedal, b.brake_pedal),
        .jump = a.jump or b.jump,
        .fire_down = a.fire_down or b.fire_down,
        .fire_pressed = a.fire_pressed or b.fire_pressed,
        .aim = a.aim or b.aim,
        .reload = a.reload or b.reload,
        .grenade = a.grenade or b.grenade,
        .interact = a.interact or b.interact,
        .select = a.select orelse b.select,
        .cycle = a.cycle + b.cycle,
        .quick_swap = a.quick_swap or b.quick_swap,
        .boost = a.boost or b.boost,
        .zoom_step = a.zoom_step + b.zoom_step,
        .steady = a.steady or b.steady,
        .throw_gun = a.throw_gun or b.throw_gun,
        .fireball = a.fireball or b.fireball,
        .enter = a.enter or b.enter,
        .reset = a.reset or b.reset,
    };
}

const AndroidApp = extern struct {
    user_data: ?*anyopaque,
    on_app_cmd: ?*anyopaque,
    on_input_event: ?*anyopaque,
    activity: ?*anyopaque,
};

extern fn GetAndroidApp() ?*AndroidApp;
extern fn ANativeActivity_setWindowFlags(activity: ?*anyopaque, add: u32, remove: u32) void;

fn keepScreenOn() void {
    const app = GetAndroidApp() orelse return;

    ANativeActivity_setWindowFlags(app.activity, 0x80, 0);
}

fn placeCamera(game: *Game, spec: []const u8) void {
    var it = std.mem.tokenizeScalar(u8, spec, ',');
    var v: [5]f32 = .{ 0, 0, 0, 0, 0 };
    var i: usize = 0;

    while (it.next()) |tok| : (i += 1) {
        if (i >= v.len) break;

        v[i] = std.fmt.parseFloat(f32, tok) catch 0;
    }

    game.player.pos = .{ .x = v[0], .y = v[1], .z = v[2] };
    game.yaw = v[3];
    game.pitch = v[4];
    game.wave_break = 1e9;
}

fn restart(app_dir: []const u8) void {
    var buf: [1024]u8 = undefined;
    const path = std.fmt.bufPrintSentinel(&buf, "{s}dronefire", .{app_dir}, 0) catch return;
    const argv = [_:null]?[*:0]const u8{path.ptr};

    logLine("restart (F5)", .{});

    const rc = std.c.execve(path.ptr, &argv, @ptrCast(std.c.environ));

    std.debug.print("restart failed: {d} errno {d}\n", .{ rc, std.c._errno().* });
}

fn physTest() void {
    const vehicle = shared.vehicle;
    var stuck: usize = 0;

    for (shared.world.vehicle_spots, 0..) |spot, n| {
        const kind: u8 = @intCast(n % vehicle.count);
        var v = vehicle.spawn(kind, spot.pos, spot.yaw);

        vehicle.settle(&v, shared.world.pieces);

        const start = v.pos;
        var t: usize = 0;

        while (t < 120) : (t += 1) vehicle.step(&v, .{ .throttle = 1 }, shared.world.pieces, 1.0 / 60.0);

        const moved = v.pos.sub(start).flatLength();

        if (moved < 3) {
            stuck += 1;
            std.debug.print("STUCK spot {d} kind {s} at {d:.1},{d:.1} yaw {d:.2} moved {d:.2} speed {d:.1}\n", .{ n, v.spec().name, spot.pos.x, spot.pos.z, spot.yaw, moved, v.speed });
        }
    }

    std.debug.print("spots {d} stuck {d}\n", .{ shared.world.vehicle_spots.len, stuck });
}

fn pedalAxis(v: f32) f32 {
    return std.math.clamp((v - 0.12) / 0.83, 0, 1);
}

fn realPad(name: []const u8) bool {
    const skip = [_][]const u8{ "touchpad", "mouse", "keyboard", "consumer control", "system control", "power button", "video bus", "fingerprint", "uinput", "gpio", "accelerometer", "sensor" };
    var low: [128]u8 = undefined;
    const n = @min(name.len, low.len);

    for (name[0..n], 0..) |c, k| low[k] = std.ascii.toLower(c);

    for (skip) |word| {
        if (std.mem.indexOf(u8, low[0..n], word) != null) return false;
    }

    return true;
}

extern "c" fn signal(sig: c_int, handler: ?*const fn (c_int) callconv(.c) void) ?*const anyopaque;
extern "c" fn mkdir(path: [*:0]const u8, mode: c_uint) c_int;

var log_fd: c_int = -1;

fn logLine(comptime fmt: []const u8, args: anytype) void {
    if (log_fd < 0) return;

    var buf: [160]u8 = undefined;
    const line = std.fmt.bufPrint(&buf, fmt ++ "\n", args) catch return;

    _ = std.c.write(log_fd, line.ptr, line.len);
}

fn onSignal(sig: c_int) callconv(.c) void {
    logLine("signal {d}", .{sig});
    std.c._exit(128 + sig);
}

fn openSessionLog() void {
    if (assets.mobile) return;

    const home = std.c.getenv("HOME") orelse return;
    var dir: [512]u8 = undefined;
    var file: [512]u8 = undefined;
    const d = std.fmt.bufPrintSentinel(&dir, "{s}/.cache/dronefire", .{std.mem.sliceTo(home, 0)}, 0) catch return;
    const f = std.fmt.bufPrintSentinel(&file, "{s}/.cache/dronefire/session.log", .{std.mem.sliceTo(home, 0)}, 0) catch return;

    _ = mkdir(d.ptr, 0o755);
    log_fd = std.c.open(f.ptr, .{ .ACCMODE = .WRONLY, .CREAT = true, .APPEND = true }, @as(c_uint, 0o644));
    logLine("start pid {d}", .{std.c.getpid()});

    for ([_]c_int{ 1, 2, 3, 6, 11, 15 }) |sig| _ = signal(sig, &onSignal);
}

var ads_test = false;
var gun_test_frames: u32 = 240;
var pad_seen = false;
var pad_log = false;
var pad_toast: f32 = 0;
var pad_name: [64:0]u8 = @splat(0);
var pad_name_len: usize = 0;

fn padToast(font: rl.Font, on: bool, name: [:0]const u8, left: f32) void {
    const w: f32 = @floatFromInt(rl.GetScreenWidth());
    const h: f32 = @floatFromInt(rl.GetScreenHeight());
    const s = h / 720;
    const in = std.math.clamp((3.2 - left) / 0.25, 0, 1);
    const out = std.math.clamp(left / 0.4, 0, 1);
    const a = @min(in, out);
    const title: [:0]const u8 = if (on) "Controller connected" else "Controller disconnected";
    const ts = 17 * s;
    const ns = 13 * s;
    const tw = ui.width(font, title, ts);
    const nw = if (on and name.len > 0) ui.width(font, name, ns) else 0;
    const iw = 34 * s;
    const pw = iw + 14 * s + @max(tw, nw) + 34 * s;
    const ph: f32 = if (nw > 0) 58 * s else 44 * s;
    const x = (w - pw) / 2;
    const y = h - 190 * s + (1 - in) * 16 * s;
    const ix = x + 18 * s;
    const iy = y + ph / 2;
    const accent = if (on) ui.rgba(120, 220, 150, 255) else ui.rgba(240, 120, 110, 255);

    rl.DrawRectangleRounded(.{ .x = x, .y = y, .width = pw, .height = ph }, 0.5, 12, ui.fade(ui.ink, 0.78 * a));
    rl.DrawRectangleRounded(.{ .x = ix, .y = iy - 8 * s, .width = iw, .height = 17 * s }, 0.8, 8, ui.fade(accent, a));
    rl.DrawCircleV(.{ .x = ix + 8 * s, .y = iy + 6 * s }, 6 * s, ui.fade(accent, a));
    rl.DrawCircleV(.{ .x = ix + iw - 8 * s, .y = iy + 6 * s }, 6 * s, ui.fade(accent, a));
    rl.DrawCircleV(.{ .x = ix + 9 * s, .y = iy - 0.5 * s }, 2.2 * s, ui.fade(ui.ink, a));
    rl.DrawCircleV(.{ .x = ix + iw - 9 * s, .y = iy - 0.5 * s }, 2.2 * s, ui.fade(ui.ink, a));

    const tx = ix + iw + 14 * s;

    if (nw > 0) {
        ui.text(font, title, tx, y + 9 * s, ts, ui.fade(ui.white, a));
        ui.text(font, name, tx, y + 9 * s + ts + 4 * s, ns, ui.fade(ui.white, 0.6 * a));
    } else {
        ui.text(font, title, tx, iy - ts / 2, ts, ui.fade(ui.white, a));
    }
}

var boom_test = false;
var boom_timer: f32 = 1;

var menu: menu_mod.Menu = .{};
var loadout: loadout_mod.Loadout = .{};
var no_pad = false;
var shadows_cleared = false;
var vsync_on = true;
var scene_rt: ?rl.RenderTexture2D = null;

fn applyLive() void {
    game_mod.god_mode = std.c.getenv("DF_MORTAL") == null;
    render.base_fov = settings.fov;

    if (assets.mobile) return;

    if (settings.vsync != vsync_on) {
        vsync_on = settings.vsync;

        if (vsync_on) rl.SetWindowState(rl.FLAG_VSYNC_HINT) else rl.ClearWindowState(rl.FLAG_VSYNC_HINT);
    }

    if (settings.fullscreen != rl.IsWindowFullscreen()) rl.ToggleFullscreen();
}

var prism_glow: gfx.Glow = .{};
var auto_scale: f32 = 1;
var slow_time: f32 = 0;
var fast_time: f32 = 0;

fn sceneScale() f32 {
    return settings.render_scale * auto_scale;
}

fn adaptScale(dt: f32) void {
    if (!assets.mobile) return;

    if (dt > 1.0 / 40.0) slow_time += dt else slow_time = 0;
    if (dt < 1.0 / 57.0) fast_time += dt else fast_time = 0;

    if (slow_time > 1.5 and auto_scale > 0.55) {
        auto_scale = @max(0.5, auto_scale - 0.1);
        slow_time = 0;
    } else if (fast_time > 8 and auto_scale < 1) {
        auto_scale = @min(1, auto_scale + 0.1);
        fast_time = 0;
    }
}

fn sceneTarget() ?rl.RenderTexture2D {
    if (sceneScale() >= 0.99 and shared.terrain.current != .prism) return null;

    const w: c_int = @intFromFloat(@max(64, @as(f32, @floatFromInt(rl.GetScreenWidth())) * sceneScale()));
    const h: c_int = @intFromFloat(@max(64, @as(f32, @floatFromInt(rl.GetScreenHeight())) * sceneScale()));

    if (scene_rt) |rt| {
        if (rt.texture.width == w and rt.texture.height == h) return rt;

        rl.UnloadRenderTexture(rt);
    }

    const rt = rl.LoadRenderTexture(w, h);

    rl.SetTextureFilter(rt.texture, rl.TEXTURE_FILTER_BILINEAR);
    scene_rt = rt;

    return rt;
}

fn viewer(path: [:0]const u8) void {
    rl.InitWindow(1280, 720, "dronefire viewer");
    defer rl.CloseWindow();
    rl.SetTargetFPS(30);

    const model = rl.LoadModel(path.ptr);
    const box = rl.GetModelBoundingBox(model);
    const size = @max(box.max.x - box.min.x, @max(box.max.y - box.min.y, box.max.z - box.min.z));
    const center: rl.Vector3 = .{ .x = (box.min.x + box.max.x) / 2, .y = (box.min.y + box.max.y) / 2, .z = (box.min.z + box.max.z) / 2 };
    var angle: f32 = 0.7;

    while (!rl.WindowShouldClose()) {
        angle += rl.GetFrameTime() * 0.5;

        const cam: rl.Camera3D = .{
            .position = .{ .x = center.x + @cos(angle) * size * 1.3, .y = center.y + size * 0.45, .z = center.z + @sin(angle) * size * 1.3 },
            .target = center,
            .up = .{ .y = 1 },
            .fovy = 40,
            .projection = rl.CAMERA_PERSPECTIVE,
        };

        rl.BeginDrawing();
        rl.ClearBackground(.{ .r = 120, .g = 136, .b = 160, .a = 255 });
        rl.BeginMode3D(cam);
        rl.DrawModel(model, .{}, 1, rl.WHITE);
        rl.EndMode3D();
        rl.EndDrawing();
    }
}

var load_font: ?rl.Font = null;
var world_done = std.atomic.Value(bool).init(false);

fn buildWorldThread() void {
    shared.world.build(std.heap.page_allocator);
    world_done.store(true, .release);
}

fn buildWorldAnimated() void {
    if (load_font == null) return shared.world.build(std.heap.page_allocator);

    const thread = std.Thread.spawn(.{}, buildWorldThread, .{}) catch return shared.world.build(std.heap.page_allocator);
    var p: f32 = 0.1;

    while (!world_done.load(.acquire)) {
        p += (0.33 - p) * 0.02;
        loadStep("Building map", p);
    }

    thread.join();
}

var tick_label: [:0]const u8 = "Loading";
var tick_progress: f32 = 0;

fn loadTick() void {
    tick_progress = @min(tick_progress + 0.004, 0.97);
    loadStep(tick_label, tick_progress);
}

fn loadStep(label: [:0]const u8, progress: f32) void {
    const f = load_font orelse return;

    tick_label = label;
    tick_progress = @max(tick_progress, progress);
    mapselect.loading(f, label, tick_progress);
}

pub fn main() void {
    if (std.c.getenv("DF_VIEW")) |v| return viewer(std.mem.sliceTo(v, 0));

    if (!assets.mobile) settings.load();

    if (std.c.getenv("DF_FX")) |t| settings.effects = std.fmt.parseInt(u8, std.mem.sliceTo(t, 0), 10) catch settings.effects;

    if (assets.mobile) {
        rl.SetConfigFlags(@intCast(rl.FLAG_VSYNC_HINT | rl.FLAG_FULLSCREEN_MODE));
        rl.InitWindow(0, 0, "dronefire");
        keepScreenOn();
    } else {
        const msaa: c_uint = if (settings.msaa) rl.FLAG_MSAA_4X_HINT else 0;
        const vsync: c_uint = if (settings.vsync) rl.FLAG_VSYNC_HINT else 0;

        rl.SetConfigFlags(@intCast(vsync | rl.FLAG_WINDOW_RESIZABLE | msaa));
        openSessionLog();
    defer logLine("exit normal", .{});
    rl.InitWindow(winSize(0, 1280), winSize(1, 720), "dronefire");
        vsync_on = settings.vsync;
    }
    defer rl.CloseWindow();

    audio.init();
    defer audio.deinit();

    _ = rl.SetGamepadMappings(controller_db);
    rl.SetWindowMinSize(640, 360);
    rl.SetExitKey(rl.KEY_NULL);
    rl.DisableCursor();

    if (assets.mobile) settings.load();

    menu.touch_enabled = touch_mod.active();
    gfx.shadow_res = if (assets.mobile) @min(1024, settings.shadowRes()) else settings.shadowRes();
    applyLive();

    if (std.c.getenv("DF_MAP")) |name| {
        shared.terrain.current = std.meta.stringToEnum(shared.terrain.Map, std.mem.sliceTo(name, 0)) orelse .facility;
    } else {
        const pick_font = loadFont(font_data);

        var ui_buf: [1024]u8 = undefined;
        const ui_dir = if (assets.mobile) assets.dir(&ui_buf, "ui") else std.fmt.bufPrint(&ui_buf, "{s}../share/dronefire/ui", .{std.mem.span(rl.GetApplicationDirectory())}) catch "share/dronefire/ui";

        shared.terrain.current = mapselect.pick(pick_font, ui_dir) orelse return;
        load_font = pick_font;
    }

    gunart.tick = &loadTick;
    vehicleart.tick = &loadTick;
    loadStep("Building map", 0.1);
    shared.terrain.configure();
    buildWorldAnimated();
    loadStep("Loading models", 0.35);

    if (std.c.getenv("DF_PHYSTEST") != null) {
        physTest();

        return;
    }

    const models = models_mod.Models.build();
    var dir_buf: [1024]u8 = undefined;
    const app_dir = std.mem.span(rl.GetApplicationDirectory());
    const gun_dir = assets.dir(&dir_buf, "guns");
    loadStep("Loading weapons", 0.5);
    const arts = gunart.loadAll(gun_dir);
    var sky_buf: [1024]u8 = undefined;
    const sky_path = assets.file(&sky_buf, "sky/sky.hdr");
    var renderer = gfx.Renderer.init(sky_path, models.sky);
    var ground_buf: [1024]u8 = undefined;

    renderer.loadGround(assets.dir(&ground_buf, "textures"));

    if (std.c.getenv("DF_NOGROUND") == null) {
        const g0 = rl.GetTime();

        models_mod.buildGroundMap();
        logLine("ground map {d:.0} ms", .{(rl.GetTime() - g0) * 1000});
    }

    renderer.setGroundMap(models_mod.ground_map, models_mod.ground_extent);


    if (shared.terrain.current == .facility) {
        const mag = (renderer.sun_color[0] + renderer.sun_color[1] + renderer.sun_color[2]) / 3;

        renderer.sun_dir = (shared.math.Vec3{ .x = 0.5, .y = 0.66, .z = 0.56 }).normalize();
        renderer.sun_color = .{ mag * 1.1, mag * 1.02, mag * 0.92 };
        renderer.env_scale *= 0.8;
        renderer.grade_tint = .{ 1.03, 1.0, 0.96 };
        renderer.grade_sat = 1.1;
        renderer.fog = 0.0014;
        renderer.fog_color = .{ 0.72, 0.78, 0.84 };
        renderer.amb_sky = .{ 1.22, 1.2, 1.16 };
        renderer.amb_ground = .{ 1.18, 1.1, 0.98 };
        renderer.shade_tint = .{ 1.02, 1.0, 0.97 };
        renderer.zenith = .{ 0.06, 0.24, 0.6 };
    }

    if (shared.terrain.current == .conquest) {
        const mag = (renderer.sun_color[0] + renderer.sun_color[1] + renderer.sun_color[2]) / 3;

        renderer.sun_dir = (shared.math.Vec3{ .x = 0.55, .y = 0.62, .z = 0.56 }).normalize();
        renderer.sun_color = .{ mag * 1.22, mag * 0.98, mag * 0.74 };
        renderer.grade_tint = .{ 1.05, 1, 0.93 };
        renderer.grade_sat = 1.12;
        renderer.fog = 0.0016;
        renderer.fog_color = .{ 0.8, 0.8, 0.76 };
        renderer.amb_sky = .{ 0.92, 0.98, 1.15 };
        renderer.amb_ground = .{ 0.82, 0.7, 0.52 };
        renderer.shade_tint = .{ 0.9, 0.92, 1.05 };
        renderer.zenith = .{ 0.06, 0.22, 0.58 };
    }

    if (shared.terrain.current == .valley) {
        const mag = (renderer.sun_color[0] + renderer.sun_color[1] + renderer.sun_color[2]) / 3;

        renderer.sun_dir = (shared.math.Vec3{ .x = -0.6, .y = 0.64, .z = 0.47 }).normalize();
        renderer.sun_color = .{ mag * 1.2, mag * 1, mag * 0.78 };
        renderer.grade_tint = .{ 1.04, 1, 0.94 };
        renderer.grade_sat = 1.12;
        renderer.fog = 0.0021;
        renderer.fog_color = .{ 0.66, 0.74, 0.82 };
        renderer.amb_sky = .{ 0.9, 0.98, 1.18 };
        renderer.amb_ground = .{ 0.74, 0.7, 0.52 };
        renderer.shade_tint = .{ 0.9, 0.93, 1.05 };
        renderer.zenith = .{ 0.05, 0.24, 0.62 };
    }

    if (shared.terrain.current == .prism) {
        renderer.sun_dir = (shared.math.Vec3{ .x = 0.35, .y = 0.85, .z = 0.4 }).normalize();
        renderer.sun_color = .{ 1.0, 0.98, 0.94 };
        renderer.fog_color = .{ 0.24, 0.58, 0.63 };
        renderer.fog = 0.0036;
        renderer.grade_tint = .{ 1.0, 1.0, 1.0 };
        renderer.grade_sat = 1.05;
        renderer.exposure = 0.78;
    }

    if (shared.terrain.current == .courtyard) {
        const mag = (renderer.sun_color[0] + renderer.sun_color[1] + renderer.sun_color[2]) / 3;

        renderer.sun_dir = (shared.math.Vec3{ .x = 0.7, .y = 0.62, .z = 0.35 }).normalize();
        renderer.sun_color = .{ mag * 1.12, mag * 1.02, mag * 0.9 };
        renderer.grade_tint = .{ 1.02, 1, 0.97 };
        renderer.grade_sat = 1.08;
        renderer.fog = 0.0018;
        renderer.fog_color = .{ 0.78, 0.86, 0.96 };
        renderer.amb_sky = .{ 1.3, 1.3, 1.38 };
        renderer.amb_ground = .{ 1.3, 1.14, 0.98 };
        renderer.shade_tint = .{ 1.0, 0.98, 1.02 };
        renderer.zenith = .{ 0.08, 0.32, 0.74 };
    }

    if (shared.maps.current()) |d| {
        const mag = (renderer.sun_color[0] + renderer.sun_color[1] + renderer.sun_color[2]) / 3;
        const p = d.palette;

        renderer.sun_dir = (shared.math.Vec3{ .x = p.sun_dir[0], .y = p.sun_dir[1], .z = p.sun_dir[2] }).normalize();
        renderer.sun_color = .{ mag * p.sun_tint[0], mag * p.sun_tint[1], mag * p.sun_tint[2] };
        renderer.grade_tint = p.grade_tint;
        renderer.grade_sat = p.grade_sat;
        renderer.fog = p.fog;
        renderer.fog_color = p.fog_color;
        renderer.amb_sky = p.amb_sky;
        renderer.amb_ground = p.amb_ground;
        renderer.shade_tint = p.shade_tint;
        renderer.zenith = p.zenith;
    }
    var props_buf: [1024]u8 = undefined;
    const props_dir = assets.dir(&props_buf, "props");
    loadStep("Loading props", 0.65);
    var scenery = propart.Props.load(std.heap.page_allocator, props_dir);
    const icons = icons_mod.Icons.build(&arts, &models);
    var char_buf: [1024]u8 = undefined;
    const char_path = assets.file(&char_buf, "characters/soldier.glb");
    loadStep("Loading soldiers", 0.8);
    var rig = soldier.Rig.load(char_path);
    const kit = soldier.Kit.build();
    var cars_buf: [512]u8 = undefined;
    const cars_dir = assets.dir(&cars_buf, "cars");
    loadStep("Loading vehicles", 0.9);
    const cars = vehicleart.Art.build(cars_dir);

    air.load();
    const font = loadFont(font_data);
    var game = Game.init(@intFromFloat(rl.GetTime() * 1000 + 7));

    mesh_mod.releaseScratch();
    var pad: Pad = .{};
    var touch: touch_mod.Touch = .{};

    game.parkVehicles();

    if (std.c.getenv("DF_SHOWCASE") != null) game.showcase(0);

    if (std.c.getenv("DF_GARAGE")) |pick| game.garage(std.fmt.parseInt(usize, std.mem.sliceTo(pick, 0), 10) catch 0);

    if (std.c.getenv("DF_SWORD")) |name| game.swordTest(std.mem.sliceTo(name, 0));

    if (std.c.getenv("DF_GUN")) |name| game.gunTest(std.mem.sliceTo(name, 0));

    ads_test = std.c.getenv("DF_ADS") != null;

    if (std.c.getenv("DF_VMYAW")) |t| render.yaw_side = std.fmt.parseFloat(f32, std.mem.sliceTo(t, 0)) catch render.yaw_side;
    if (std.c.getenv("DF_VMROLL")) |t| render.roll_side = std.fmt.parseFloat(f32, std.mem.sliceTo(t, 0)) catch render.roll_side;
    if (std.c.getenv("DF_PREACH")) |t| render.pistol_reach = std.fmt.parseFloat(f32, std.mem.sliceTo(t, 0)) catch render.pistol_reach;
    if (std.c.getenv("DF_ROFF")) |t| render.r_off = parseVec(std.mem.sliceTo(t, 0));
    if (std.c.getenv("DF_LOFF")) |t| render.l_off = parseVec(std.mem.sliceTo(t, 0));
    if (std.c.getenv("DF_VMREACH")) |t| render.vm_reach = std.fmt.parseFloat(f32, std.mem.sliceTo(t, 0)) catch 0;
    if (std.c.getenv("DF_SHARP")) |t| gfx.sharpen_amount = std.fmt.parseFloat(f32, std.mem.sliceTo(t, 0)) catch gfx.sharpen_amount;
    if (std.c.getenv("DF_ADSR")) |t| render.ads_r = parse4(std.mem.sliceTo(t, 0), render.ads_r);
    if (std.c.getenv("DF_ADSL")) |t| render.ads_l = parse4(std.mem.sliceTo(t, 0), render.ads_l);
    if (std.c.getenv("DF_VMDOWN")) |t| render.vm_down = std.fmt.parseFloat(f32, std.mem.sliceTo(t, 0)) catch 0;
    if (std.c.getenv("DF_LROLL")) |t| render.l_roll = std.fmt.parseFloat(f32, std.mem.sliceTo(t, 0)) catch 0;
    if (std.c.getenv("DF_LROLLFAR")) |t| render.l_roll_far = std.fmt.parseFloat(f32, std.mem.sliceTo(t, 0)) catch 0;
    if (std.c.getenv("DF_MTILT")) |t| render.melee_tilt = std.fmt.parseFloat(f32, std.mem.sliceTo(t, 0)) catch render.melee_tilt;
    if (std.c.getenv("DF_ARMSCALE")) |t| render.arm_scale = std.fmt.parseFloat(f32, std.mem.sliceTo(t, 0)) catch render.arm_scale;
    if (std.c.getenv("DF_ADSLIFT")) |t| render.ads_lift = std.fmt.parseFloat(f32, std.mem.sliceTo(t, 0)) catch 0;
    if (std.c.getenv("DF_PDOWN")) |t| render.pistol_down = std.fmt.parseFloat(f32, std.mem.sliceTo(t, 0)) catch render.pistol_down;

    if (std.c.getenv("DF_CAR")) |pick| game.spotlight(std.fmt.parseInt(usize, std.mem.sliceTo(pick, 0), 10) catch 0);

    if (std.c.getenv("DF_CAM")) |spec| placeCamera(&game, std.mem.sliceTo(spec, 0));

    render.clean_shot = std.c.getenv("DF_NOHUD") != null;

    driving.vtest = std.c.getenv("DF_VTEST") != null;
    if (std.c.getenv("DF_DRIVE")) |pick| driving.start(&game, std.fmt.parseInt(usize, std.mem.sliceTo(pick, 0), 10) catch 0);

    if (std.c.getenv("DF_FLY")) |pick| air.start(&game, std.fmt.parseInt(usize, std.mem.sliceTo(pick, 0), 10) catch 0);

    driving.autodrive = std.c.getenv("DF_AUTODRIVE") != null;
    air.autofly = std.c.getenv("DF_AUTOFLY") != null;
    air.autofire = std.c.getenv("DF_AUTOFIRE") != null;
    driving.autoboost = std.c.getenv("DF_AUTOBOOST") != null;
    driving.lean_test = std.c.getenv("DF_LEAN") != null;

    boom_test = std.c.getenv("DF_BOOM") != null;
    pad_log = std.c.getenv("DF_PADLOG") != null;

    if (std.c.getenv("DF_BLAST")) |pick| driving.blast_test = std.fmt.parseInt(usize, std.mem.sliceTo(pick, 0), 10) catch null;
    var rumble: rumble_mod.Rumble = .{};
    var playing = true;

    if (std.c.getenv("DF_SETTINGS")) |tab| {
        playing = false;
        rl.EnableCursor();
        menu.tab = std.fmt.parseInt(usize, std.mem.sliceTo(tab, 0), 10) catch 0;
        menu.show();
    }

    if (std.c.getenv("DF_PAUSE") != null) {
        playing = false;
        rl.EnableCursor();
    }

    no_pad = std.c.getenv("DF_NOPAD") != null;

    if (std.c.getenv("DF_LOADOUT")) |tab| {
        playing = false;
        rl.EnableCursor();
        loadout.show(&game, false);
        loadout.tab = std.fmt.parseInt(usize, std.mem.sliceTo(tab, 0), 10) catch loadout.tab;
    }
    var skip_click = false;
    var settle: u8 = 3;
    var pad_check: f32 = 0;

    defer rumble.detach();

    while (!rl.WindowShouldClose()) {
        const frame_dt = rl.GetFrameTime();

        if (rl.IsKeyPressed(rl.KEY_F5)) restart(app_dir);

        if (boom_test) {
            boom_timer -= frame_dt;

            if (boom_timer <= 0) {
                boom_timer = 2.6;
                game.explode(game.player.pos.add(shared.math.flatDir(game.yaw).scale(11)).add(.{ .y = 1 }), 3.5, 0, 0);
            }
        }

        pad_check -= frame_dt;

        if (pad_check <= 0) {
            pad_check = 1;
            pad.find();

            if (pad_log) std.debug.print("pad id={?d} active={} name={s}\n", .{ pad.id, pad.active, if (pad.id) |id| std.mem.span(rl.GetGamepadName(id)) else "-" });

            if ((pad.id != null and pad.active) != pad_seen and (pad.active or pad.id == null)) {
                pad_seen = pad.id != null and pad.active;
                pad_toast = 3.2;
                audio.ui(if (pad_seen) .toast else .back);
                pad_name_len = 0;

                if (pad.id) |id| {
                    const name = std.mem.span(rl.GetGamepadName(id));
                    const n = @min(name.len, pad_name.len - 1);

                    @memcpy(pad_name[0..n], name[0..n]);
                    pad_name_len = n;
                }

                pad_name[pad_name_len] = 0;
            }

            if (pad.id) |id| {
                rumble.attach(std.mem.span(rl.GetGamepadName(id)));
            } else {
                rumble.detach();
            }
        }

        if (assets.mobile and playing and !rl.IsWindowFocused()) playing = false;

        if (rl.IsKeyPressed(rl.KEY_F11)) settings.fullscreen = !rl.IsWindowFullscreen();

        const menu_was_open = menu.open;
        const loadout_was_open = loadout.open;

        loadout.update(frame_dt, pad.id, &game);
        menu.update(frame_dt, pad.id);
        applyLive();

        const loadout_busy = loadout_was_open or loadout.open;

        if (loadout_was_open and !loadout.open and loadout.from_game) {
            playing = true;
            skip_click = true;
            settle = 3;
            rl.DisableCursor();
        }

        if (!loadout_busy and !menu_was_open and !menu.open and loadout.wantsOpen(!playing, pad.id)) {
            const from_game = playing;

            playing = false;
            rl.EnableCursor();
            loadout.show(&game, from_game);
        } else if (!loadout_busy and !menu_was_open and !menu.open and !playing and menu_mod.wantsQuit(pad.id)) {
            break;
        } else if (!loadout_busy and !menu_was_open and !playing and menu.wantsOpen(pad.id)) {
            menu.show();
        } else if (!loadout_busy and !menu_was_open and !menu.open and (rl.IsKeyPressed(rl.KEY_ESCAPE) or rl.IsKeyPressed(rl.KEY_BACK) or pad.pressed(rl.GAMEPAD_BUTTON_MIDDLE_RIGHT))) {
            playing = !playing;

            if (playing) {
                rl.DisableCursor();
                settle = 3;
            } else {
                rl.EnableCursor();
            }
        }


        const start_pressed = rl.IsMouseButtonPressed(rl.MOUSE_BUTTON_LEFT) or rl.IsMouseButtonReleased(rl.MOUSE_BUTTON_LEFT) or rl.IsKeyPressed(rl.KEY_ENTER) or rl.IsKeyPressed(rl.KEY_SPACE);

        if (!playing and !menu.open and !menu_was_open and !loadout_busy and !loadout.open and start_pressed) {
            playing = true;
            skip_click = true;
            settle = 3;
            rl.DisableCursor();
        }


        const captured = playing and rl.IsCursorHidden();
        const pad_frame: Frame = if (playing) readPad(&pad, frame_dt, game.arsenal.active == game_mod.knife_slot, game.scoped()) else .{};
        const mouse = rl.GetMouseDelta();

        if (if (assets.mobile) pad_frame.pad_button else pad_frame.pad_used) pad.active = true;

        if (assets.mobile and rl.GetTouchPointCount() > 0) pad.active = false;

        if (mouse.x != 0 or mouse.y != 0 or rl.GetKeyPressed() != 0) pad.active = false;

        var controls = merge(readKeyboard(captured, game.scoped()), pad_frame.controls);

        if (ads_test) controls.aim = true;

        if (gun_test_frames > 0) {
            gun_test_frames -= 1;

            if (std.c.getenv("DF_GUN")) |name| game.gunEquip(std.mem.sliceTo(name, 0));
        }

        if (skip_click) {
            controls.fire_down = false;
            controls.fire_pressed = false;

            if (!rl.IsMouseButtonDown(rl.MOUSE_BUTTON_LEFT)) skip_click = false;
        }

        const aim_sens = 1 + (settings.ads_sens - 1) * game.ads;
        const flip: f32 = if (settings.invert_y) -1 else 1;

        if (captured and settle == 0) game.look(mouse.x, mouse.y * flip, mouse_sensitivity * settings.mouse_sens * aim_sens);

        if (settle > 0) settle -= 1;

        if (playing and pad.id != null) {
            const look = pad_frame.look;
            const move_mag = @min(1, @sqrt(controls.forward * controls.forward + controls.right * controls.right));
            const raw_slow = if (settings.aim_assist > 0.01) game.aimAssist(frame_dt, look.mag, move_mag, pad_frame.aim_started) else 1;
            const slow = 1 - (1 - raw_slow) * settings.aim_assist;

            if (look.mag > 0.97) pad.edge_time += frame_dt else pad.edge_time = 0;

            if (look.mag > 0) {
                const curve = std.math.pow(f32, look.mag, 1.8);
                const boost = 1 + std.math.clamp((pad.edge_time - 0.15) / 0.35, 0, 1) * 0.7;
                const scale = curve / look.mag * boost * slow * frame_dt;

                const car_k: f32 = if (driving.driving()) 0.55 else 1;
                const stick_scale = scale * settings.stick_sens * aim_sens * car_k;

                game.turn(-look.x * yaw_rate * stick_scale, -look.y * pitch_rate * stick_scale * flip);
            }
        }

        if (touch_mod.active() and playing and !(pad.id != null and pad.active)) {
            const screen_w: f32 = @floatFromInt(rl.GetScreenWidth());
            const screen_h: f32 = @floatFromInt(rl.GetScreenHeight());
            const tap = touch.read(screen_w, screen_h);

            controls = merge(controls, tap.controls);
            game.look(tap.look_x, tap.look_y * flip, mouse_sensitivity * 1.4 * 720 / screen_h * settings.touch_look * aim_sens);
        }

        game.simulate(frame_dt, controls);

        const view = game.view();

        game.update(frame_dt, controls, view);

        if (std.c.getenv("DF_HOLDCAM") != null) {
            if (std.c.getenv("DF_CAM")) |spec| placeCamera(&game, std.mem.sliceTo(spec, 0));

    render.clean_shot = std.c.getenv("DF_NOHUD") != null;
        }

        audio.update(&game, frame_dt, controls.fire_pressed);

        if (game.buzz.time > 0) {
            if (settings.vibration) rumble.pulse(game.buzz.strong, game.buzz.weak, game.buzz.time);

            game.buzz = .{};
        }

        rumble.update(frame_dt);

        const now = if (air.flying()) air.smooth(game.view(), frame_dt) else if (driving.driving()) driving.smooth(game.view(), frame_dt) else game.view();
        const cam = render.camera(game, now);

        renderer.shadows_on = settings.shadows > 0 and shared.terrain.current != .prism and shared.terrain.current != .courtyard and shared.terrain.current != .facility;

        if (settings.shadows > 0 and shared.terrain.current != .prism and shared.terrain.current != .courtyard and shared.terrain.current != .facility) {
            shadows_cleared = false;

            for (0..renderer.cascades) |cascade| {
                renderer.beginShadow(game.player.pos, cascade);
                render.scene(&renderer, &models, &arts, &scenery, &rig, kit, &cars, game, now, frame_dt);
                renderer.endShadow();
            }
        } else if (!shadows_cleared) {
            shadows_cleared = true;

            for (0..renderer.cascades) |cascade| {
                renderer.beginShadow(game.player.pos, cascade);
                renderer.endShadow();
            }
        }

        adaptScale(frame_dt);
        renderer.render_scale = sceneScale();
        renderer.post = false;
        renderer.ssao = false;
        renderer.fxaa = false;
        renderer.fx.samples = if (settings.msaa and std.c.getenv("DF_NOMSAA") == null) 4 else 0;

        const target = if (renderer.post) null else sceneTarget();

        if (target) |rt| {
            rl.BeginTextureMode(rt);
            renderer.begin(cam, game.time);
            render.scene(&renderer, &models, &arts, &scenery, &rig, kit, &cars, game, now, frame_dt);
            renderer.end();
            rl.EndTextureMode();

            if (shared.terrain.current == .prism) prism_glow.process(rt.texture);
        }

        rl.BeginDrawing();

        if (target) |rt| {
            const src = rl.Rectangle{ .x = 0, .y = 0, .width = @floatFromInt(rt.texture.width), .height = @floatFromInt(-rt.texture.height) };
            const dst = rl.Rectangle{ .x = 0, .y = 0, .width = @floatFromInt(rl.GetScreenWidth()), .height = @floatFromInt(rl.GetScreenHeight()) };

            rl.DrawTexturePro(rt.texture, src, dst, .{}, 0, rl.WHITE);

            if (shared.terrain.current == .prism) prism_glow.composite();
        } else {
            renderer.begin(cam, game.time);
            render.scene(&renderer, &models, &arts, &scenery, &rig, kit, &cars, game, now, frame_dt);
            renderer.end();
        }
        if (!render.clean_shot) {
            render.overlay(game, now, cam, font);
            hud.draw(game, font, &icons, playing, pad.active and pad.id != null);
            hud.vehicleStatus(game, font);
            air.hud(game, font, cam);
        }

        if (touch_mod.active() and playing and !(pad.id != null and pad.active)) touch.draw(font, @floatFromInt(rl.GetScreenWidth()), @floatFromInt(rl.GetScreenHeight()));

        if (!playing) menu.drawGear(font, pad.active and pad.id != null);

        if (!playing and !menu.open and !loadout.open) menu_mod.drawQuit(font, pad.active and pad.id != null, menu.t);

        if (!playing) loadout.drawButton(font, pad.active and pad.id != null, menu.t);

        menu.draw(font, pad.active and pad.id != null);
        loadout.draw(font, &icons, &game, pad.active and pad.id != null);

        if (pad_toast > 0) {
            pad_toast -= frame_dt;
            padToast(font, pad_seen, pad_name[0..pad_name_len :0], pad_toast);
        }
        rl.EndDrawing();
    }
}
