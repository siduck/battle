const std = @import("std");
const rl = @import("raylib");
const ui = @import("ui.zig");
const settings = @import("settings.zig");
const assets = @import("assets.zig");
const game_mod = @import("game.zig");
const net = @import("net.zig");

const Controls = game_mod.Controls;

const Button = enum { fire, aim, jump, reload, swap, grenade, fireball, use };


const Role = union(enum) {
    move,
    look,
    board,
    button: Button,
};

const Finger = struct {
    id: i32,
    role: Role,
    last: rl.Vector2,
    seen: bool = true,
};

const Circle = struct {
    x: f32,
    y: f32,
    r: f32,
};

pub const Result = struct {
    controls: Controls = .{},
    look_x: f32 = 0,
    look_y: f32 = 0,
};

var forced: ?bool = null;

pub fn active() bool {
    if (assets.mobile) return true;

    if (forced == null) forced = std.c.getenv("DF_TOUCH") != null;

    return forced.?;
}

fn place(b: Button, w: f32, h: f32) Circle {
    const s = h / 720 * settings.touch_size;

    return switch (b) {
        .fire => .{ .x = w - 230 * s, .y = h - 330 * s, .r = 70 * s },
        .jump => .{ .x = w - 95 * s, .y = h - 260 * s, .r = 48 * s },
        .aim => .{ .x = w - 365 * s, .y = h - 420 * s, .r = 42 * s },
        .reload => .{ .x = w - 95 * s, .y = h - 410 * s, .r = 36 * s },
        .swap => .{ .x = w - 230 * s, .y = h - 485 * s, .r = 36 * s },
        .grenade => .{ .x = w - 380 * s, .y = h - 240 * s, .r = 36 * s },
        .fireball => .{ .x = w - 490 * s, .y = h - 330 * s, .r = 40 * s },
        .use => .{ .x = w - 95 * s, .y = h - 555 * s, .r = 36 * s },
    };
}

fn hit(c: Circle, p: rl.Vector2) bool {
    const dx = p.x - c.x;
    const dy = p.y - c.y;

    return dx * dx + dy * dy <= c.r * c.r * 1.25;
}

pub const Touch = struct {
    fingers: [10]?Finger = @splat(null),
    origin: rl.Vector2 = .{},
    knob: rl.Vector2 = .{},
    aiming: bool = false,

    fn find(t: *Touch, id: i32) ?*Finger {
        for (&t.fingers) |*f| {
            if (f.*) |*finger| {
                if (finger.id == id) return finger;
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

    fn roleAt(p: rl.Vector2, w: f32, h: f32) Role {
        if (net.board_rect) |r| {
            if (rl.CheckCollisionPointRec(p, r)) return .board;
        }

        for (std.enums.values(Button)) |b| {
            if (hit(place(b, w, h), p)) return .{ .button = b };
        }

        if (p.x < w * 0.4 and p.y > h * 0.3) return .move;

        return .look;
    }

    pub fn read(t: *Touch, w: f32, h: f32) Result {
        const s = h / 720;
        const reach = 90 * s;
        var out: Result = .{};
        const emulate = !assets.mobile and rl.GetTouchPointCount() == 0 and rl.IsMouseButtonDown(rl.MOUSE_BUTTON_LEFT);
        const count: usize = if (emulate) 1 else @intCast(rl.GetTouchPointCount());

        for (&t.fingers) |*f| {
            if (f.*) |*finger| finger.seen = false;
        }

        for (0..count) |i| {
            const id = if (emulate) 0 else rl.GetTouchPointId(@intCast(i));
            const p = if (emulate) rl.GetMousePosition() else rl.GetTouchPosition(@intCast(i));

            if (t.find(id)) |finger| {
                const dx = p.x - finger.last.x;
                const dy = p.y - finger.last.y;

                finger.seen = true;
                finger.last = p;

                switch (finger.role) {
                    .move => t.knob = p,
                    .board => {},
                    .look => {
                        out.look_x += dx;
                        out.look_y += dy;
                    },
                    .button => |b| if (b == .fire) {
                        out.look_x += dx;
                        out.look_y += dy;
                    },
                }

                continue;
            }

            const role = roleAt(p, w, h);

            t.add(.{ .id = id, .role = role, .last = p });

            switch (role) {
                .move => {
                    t.origin = p;
                    t.knob = p;
                },
                .look => {},
                .board => net.board_open = !net.board_open,
                .button => |b| switch (b) {
                    .fire => out.controls.fire_pressed = true,
                    .aim => t.aiming = !t.aiming,
                    .reload => out.controls.reload = true,
                    .swap => out.controls.cycle = 1,
                    .grenade => out.controls.grenade = true,
                    .use => {
                        out.controls.enter = true;
                        out.controls.interact = true;
                    },
                    .jump, .fireball => {},
                },
            }
        }

        var moving = false;

        for (&t.fingers) |*f| {
            const finger = f.* orelse continue;

            if (!finger.seen) {
                f.* = null;

                continue;
            }

            switch (finger.role) {
                .move => moving = true,
                .look, .board => {},
                .button => |b| switch (b) {
                    .fire => out.controls.fire_down = true,
                    .jump => out.controls.jump = true,
                    .fireball => out.controls.fireball = true,
                    else => {},
                },
            }
        }

        if (moving) {
            const dx = t.knob.x - t.origin.x;
            const dy = t.knob.y - t.origin.y;
            const len = @sqrt(dx * dx + dy * dy);
            const k = if (len > reach) reach / len else 1;

            t.knob = .{ .x = t.origin.x + dx * k, .y = t.origin.y + dy * k };
            out.controls.right = std.math.clamp(dx / reach, -1, 1);
            out.controls.forward = std.math.clamp(-dy / reach, -1, 1);
        } else {
            t.origin = .{ .x = 190 * s, .y = h - 190 * s };
            t.knob = t.origin;
        }

        out.controls.aim = t.aiming;

        return out;
    }

    fn held(t: *const Touch, b: Button) bool {
        for (t.fingers) |f| {
            const finger = f orelse continue;

            switch (finger.role) {
                .button => |pressed| if (pressed == b) return true,
                else => {},
            }
        }

        return false;
    }

    pub fn draw(t: *const Touch, font: rl.Font, w: f32, h: f32) void {
        const s = h / 720;

        _ = font;

        const op = settings.touch_opacity;

        rl.DrawCircleV(t.origin, 90 * s, ui.fade(ui.ink, 0.28 * op));
        rl.DrawCircleLinesV(t.origin, 90 * s, ui.fade(ui.white, 0.35 * op));
        rl.DrawCircleV(t.knob, 38 * s, ui.fade(ui.white, 0.5 * op));

        for (std.enums.values(Button)) |b| {
            const c = place(b, w, h);
            const on = t.held(b) or (b == .aim and t.aiming);
            rl.DrawCircleV(.{ .x = c.x, .y = c.y }, c.r, ui.fade(if (on) ui.white else ui.ink, (if (on) @as(f32, 0.45) else 0.32) * op));
            rl.DrawCircleLinesV(.{ .x = c.x, .y = c.y }, c.r, ui.fade(ui.white, 0.55 * op));
            icon(b, c.x, c.y, c.r * 0.46, ui.fade(ui.white, 0.92 * @max(op, 0.5)));
        }
    }
};

fn v2(x: f32, y: f32) rl.Vector2 {
    return .{ .x = x, .y = y };
}

fn icon(b: Button, x: f32, y: f32, k: f32, col: rl.Color) void {
    const t = @max(2, k * 0.16);

    switch (b) {
        .fire => {
            for ([_]f32{ -0.55, 0, 0.55 }) |dx| {
                const bx = x + dx * k;

                rl.DrawRectangleRounded(.{ .x = bx - k * 0.17, .y = y - k * 0.25, .width = k * 0.34, .height = k * 0.95 }, 0.3, 4, col);
                rl.DrawTriangle(v2(bx, y - k * 0.75), v2(bx - k * 0.17, y - k * 0.25), v2(bx + k * 0.17, y - k * 0.25), col);
            }
        },
        .aim => {
            rl.DrawRing(v2(x, y), k * 0.62, k * 0.62 + t, 0, 360, 40, col);
            rl.DrawLineEx(v2(x - k, y), v2(x - k * 0.3, y), t, col);
            rl.DrawLineEx(v2(x + k * 0.3, y), v2(x + k, y), t, col);
            rl.DrawLineEx(v2(x, y - k), v2(x, y - k * 0.3), t, col);
            rl.DrawLineEx(v2(x, y + k * 0.3), v2(x, y + k), t, col);
            rl.DrawCircleV(v2(x, y), t * 0.8, col);
        },
        .jump => {
            rl.DrawLineEx(v2(x - k * 0.7, y + k * 0.1), v2(x, y - k * 0.6), t * 1.2, col);
            rl.DrawLineEx(v2(x, y - k * 0.6), v2(x + k * 0.7, y + k * 0.1), t * 1.2, col);
            rl.DrawLineEx(v2(x - k * 0.7, y + k * 0.6), v2(x, y - k * 0.1), t * 1.2, col);
            rl.DrawLineEx(v2(x, y - k * 0.1), v2(x + k * 0.7, y + k * 0.6), t * 1.2, col);
        },
        .reload => {
            rl.DrawRing(v2(x, y), k * 0.6, k * 0.6 + t, 40, 320, 32, col);
            const a = 40.0 * std.math.pi / 180.0;
            const tip = v2(x + @cos(a) * (k * 0.6 + t * 0.5), y + @sin(a) * (k * 0.6 + t * 0.5));

            rl.DrawTriangle(v2(tip.x + k * 0.32, tip.y - k * 0.12), v2(tip.x - k * 0.1, tip.y - k * 0.32), v2(tip.x - k * 0.02, tip.y + k * 0.26), col);
        },
        .swap => {
            rl.DrawLineEx(v2(x - k * 0.7, y - k * 0.3), v2(x + k * 0.5, y - k * 0.3), t, col);
            rl.DrawTriangle(v2(x + k * 0.8, y - k * 0.3), v2(x + k * 0.45, y - k * 0.55), v2(x + k * 0.45, y - k * 0.05), col);
            rl.DrawLineEx(v2(x - k * 0.5, y + k * 0.3), v2(x + k * 0.7, y + k * 0.3), t, col);
            rl.DrawTriangle(v2(x - k * 0.8, y + k * 0.3), v2(x - k * 0.45, y + k * 0.55), v2(x - k * 0.45, y + k * 0.05), col);
        },
        .grenade => {
            rl.DrawCircleV(v2(x, y + k * 0.18), k * 0.55, col);
            rl.DrawRectangleRounded(.{ .x = x - k * 0.22, .y = y - k * 0.62, .width = k * 0.44, .height = k * 0.3 }, 0.3, 4, col);
            rl.DrawRing(v2(x + k * 0.42, y - k * 0.6), k * 0.14, k * 0.14 + t * 0.7, 0, 360, 16, col);
        },
        .fireball => {
            const flame = rl.Color{ .r = 255, .g = 150, .b = 50, .a = col.a };
            const core = rl.Color{ .r = 255, .g = 230, .b = 150, .a = col.a };

            rl.DrawCircleV(v2(x, y + k * 0.25), k * 0.55, flame);
            rl.DrawTriangle(v2(x, y - k * 0.9), v2(x - k * 0.53, y + k * 0.12), v2(x + k * 0.53, y + k * 0.12), flame);
            rl.DrawCircleV(v2(x, y + k * 0.35), k * 0.28, core);
            rl.DrawTriangle(v2(x, y - k * 0.2), v2(x - k * 0.27, y + k * 0.3), v2(x + k * 0.27, y + k * 0.3), core);
        },
        .use => {
            rl.DrawRectangleRoundedLinesEx(.{ .x = x - k * 0.1, .y = y - k * 0.7, .width = k * 0.8, .height = k * 1.4 }, 0.2, 4, t, col);
            rl.DrawLineEx(v2(x - k * 0.85, y), v2(x + k * 0.15, y), t, col);
            rl.DrawTriangle(v2(x + k * 0.42, y), v2(x + k * 0.08, y - k * 0.3), v2(x + k * 0.08, y + k * 0.3), col);
        },
    }
}
