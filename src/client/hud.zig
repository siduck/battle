const std = @import("std");
const rl = @import("raylib");
const shared = @import("shared");
const ui = @import("ui.zig");
const touch = @import("touch.zig");
const theme = @import("theme.zig");
const menu = @import("menu.zig");
const settings = @import("settings.zig");
const game_mod = @import("game.zig");
const icons_mod = @import("icons.zig");

const weapons = shared.weapons;
const Game = game_mod.Game;
const v2 = ui.v2;

fn print(buf: []u8, comptime fmt: []const u8, args: anytype) [:0]const u8 {
    return std.mem.printSentinel(buf, fmt, args, 0) catch "";
}

fn shadowLine(a: rl.Vector2, b: rl.Vector2, thick: f32, color: rl.Color) void {
    rl.DrawLineEx(a, b, thick + 2.5, ui.fade(ui.ink, 0.6));
    rl.DrawLineEx(a, b, thick, color);
}

pub fn draw(g: Game, font: rl.Font, icons: *const icons_mod.Icons, playing: bool, pad: bool) void {
    const w: f32 = @floatFromInt(rl.GetScreenWidth());
    const h: f32 = @floatFromInt(rl.GetScreenHeight());
    const u = @min(h / 900, w / 1500);
    const cx = w / 2;
    const cy = h / 2;
    var buf: [96]u8 = undefined;

    if (g.hurt_flash > 0) hurt(g, w, h, u, cx, cy);

    font_ref = font;

    const in_air = @import("air.zig").flying();

    if (!in_air) crosshair(g, cx, cy, u);

    if (!playing) {} else if (touch.shown) {
        dock(g, font, icons, u, w, h, &buf);
    } else {
        vitals(g, font, u, 36 * u, h - 36 * u, &buf);

        if (!in_air) inventory(g, font, icons, u, w, h, &buf);
    }

    if (!game_mod.online) topBar(g, font, u, w, &buf);
    feed(g, font, u, w, &buf);
    banner(g, font, u, cx, h, &buf);
    prompt(g, font, u, cx, cy, pad, &buf);

    if (settings.show_fps) {
        const n = rl.GetFPS();
        const fps = print(&buf, "{d} FPS", .{n});
        const size = 15 * u;
        const tw = ui.capsWidth(font, fps, size);
        const anchor = touch.besidePause(w, h);
        const px = if (touch.shown) anchor.x else 20 * u;
        const py = if (touch.shown) anchor.y - 15 * u else 20 * u;
        const dot: rl.Color = if (n >= 55) ui.rgba(96, 214, 120, 255) else if (n >= 30) ui.rgba(255, 196, 90, 255) else ui.red;

        rl.DrawRectangleRounded(.{ .x = px, .y = py, .width = tw + 40 * u, .height = 30 * u }, 1, 12, ui.fade(ui.ink, 0.72));
        rl.DrawCircleV(.{ .x = px + 15 * u, .y = py + 15 * u }, 4.5 * u, dot);
        ui.caps(font, fps, px + 27 * u, py + 15 * u - size / 2, size, ui.white);
    }

    if (!playing) pause(pad);
}

fn hurt(g: Game, w: f32, h: f32, u: f32, cx: f32, cy: f32) void {
    const a = g.hurt_flash / 0.45;
    const red = ui.fade(ui.red, a * 0.35);
    const clear = ui.fade(ui.red, 0);
    const edge: c_int = @intFromFloat(90 * u);
    const wi: c_int = @intFromFloat(w);
    const hi: c_int = @intFromFloat(h);

    rl.DrawRectangleGradientV(0, 0, wi, edge, red, clear);
    rl.DrawRectangleGradientV(0, hi - edge, wi, edge, clear, red);
    rl.DrawRectangleGradientH(0, 0, edge, hi, red, clear);
    rl.DrawRectangleGradientH(wi - edge, 0, edge, hi, clear, red);

    const ang = -90 - g.hurt_dir * 180 / std.math.pi;

    rl.DrawRing(v2(cx, cy), 78 * u, 90 * u, ang - 24, ang + 24, 24, ui.fade(ui.red, a));
}

fn sightReticle(g: Game, cx: f32, cy: f32, u: f32, h: f32, k: f32) void {
    const zoom = if (g.hasScope()) g.currentZoom() else 2;
    const red = ui.fade(ui.rgba(255, 52, 40, 255), k);
    const ink = ui.fade(ui.rgba(10, 11, 13, 255), 0.9 * k);

    if (zoom < 3) {
        rl.DrawRing(v2(cx, cy), 7 * u, 11.5 * u, 0, 360, 48, ui.fade(ui.ink, 0.35 * k));
        rl.DrawRing(v2(cx, cy), 8.3 * u, 10.2 * u, 0, 360, 48, ui.fade(ui.rgba(150, 255, 214, 255), k));
        rl.DrawCircleV(v2(cx, cy), 1.4 * u, red);

        return;
    }

    const far = zoom >= 5;
    const lens = h * @as(f32, if (far) 0.265 else 0.178);
    const thin = @max(1, 1.4 * u);
    const gap = 9 * u;

    rl.DrawRing(v2(cx, cy), lens * 0.93, lens * 1.01, 0, 360, 72, ui.fade(ink, 0.22));
    rl.DrawLineEx(v2(cx - lens, cy), v2(cx - gap, cy), thin, ink);
    rl.DrawLineEx(v2(cx + gap, cy), v2(cx + lens, cy), thin, ink);
    rl.DrawLineEx(v2(cx, cy + gap), v2(cx, cy + lens), thin, ink);

    if (!far) {
        rl.DrawLineEx(v2(cx, cy - lens), v2(cx, cy - gap), thin, ink);
        rl.DrawLineEx(v2(cx - 8 * u, cy + 9 * u), v2(cx, cy), 2.6 * u, red);
        rl.DrawLineEx(v2(cx + 8 * u, cy + 9 * u), v2(cx, cy), 2.6 * u, red);
    } else {
        rl.DrawLineEx(v2(cx, cy - lens), v2(cx, cy - gap), thin, ink);
        rl.DrawLineEx(v2(cx - gap, cy), v2(cx + gap, cy), @max(1, 0.8 * u), ink);
        rl.DrawLineEx(v2(cx, cy - gap), v2(cx, cy + gap), @max(1, 0.8 * u), ink);
        rl.DrawCircleV(v2(cx, cy), 1.9 * u, red);
        rl.DrawRectangleRec(.{ .x = cx - lens, .y = cy - 2 * u, .width = lens * 0.42, .height = 4 * u }, ink);
        rl.DrawRectangleRec(.{ .x = cx + lens * 0.58, .y = cy - 2 * u, .width = lens * 0.42, .height = 4 * u }, ink);
        rl.DrawRectangleRec(.{ .x = cx - 2 * u, .y = cy + lens * 0.62, .width = 4 * u, .height = lens * 0.38 }, ink);

        var i: f32 = 1;

        while (i <= 4) : (i += 1) {
            const step = lens * 0.12 * i;
            const wide = (13 - i * 2) * u;

            rl.DrawLineEx(v2(cx - wide, cy + step), v2(cx + wide, cy + step), thin, ink);
            rl.DrawLineEx(v2(cx - step, cy - 4 * u), v2(cx - step, cy + 4 * u), thin, ink);
            rl.DrawLineEx(v2(cx + step, cy - 4 * u), v2(cx + step, cy + 4 * u), thin, ink);
        }
    }

    var low: [24]u8 = undefined;
    const level = print(&low, "{d:.0}x", .{zoom});

    ui.outlined(font_ref, level, cx + lens * 0.45, cy + lens * 0.5, 22 * u, ui.fade(ui.white, 0.85 * k));

    if (!g.scoped()) return;

    const breath_w = 150 * u;
    const bx = cx - breath_w / 2;
    const by = @min(cy + lens + 14 * u, h - 150 * u);

    rl.DrawRectangleRec(.{ .x = bx, .y = by, .width = breath_w, .height = 4 * u }, ui.fade(ui.white, 0.25));
    rl.DrawRectangleRec(.{ .x = bx, .y = by, .width = breath_w * g.breath / 4, .height = 4 * u }, if (g.steadying) ui.yellow else ui.fade(ui.white, 0.8));

    if (touch.shown) return;

    const hint: [:0]const u8 = "Wheel zoom    Shift hold breath";

    ui.outlined(font_ref, hint, cx - ui.width(font_ref, hint, 15 * u) / 2, by + 12 * u, 15 * u, ui.fade(ui.white, 0.7));
}

var font_ref: rl.Font = undefined;

fn meleeReticle(g: Game, cx: f32, cy: f32, u: f32) void {
    const m = g.melee_state;
    const charge = m.charging();

    rl.DrawCircleV(v2(cx, cy), 4.5 * u, ui.fade(ui.ink, 0.6));
    rl.DrawCircleV(v2(cx, cy), 3 * u, ui.white);

    if (m.holding and m.hold > 0.12) {
        const full = charge >= 1;

        rl.DrawRing(v2(cx, cy), 13 * u, 16.5 * u, 0, 360, 48, ui.fade(ui.ink, 0.45));
        rl.DrawRing(v2(cx, cy), 13.6 * u, 15.9 * u, -90, -90 + 360 * charge, 48, if (full) ui.rgba(255, 196, 64, 255) else ui.white);
    }

    if (m.block >= 0) {
        const fresh = m.block < 0.2;
        const col = if (fresh) ui.rgba(255, 220, 120, 255) else ui.white;

        shadowLine(v2(cx - 18 * u, cy - 10 * u), v2(cx - 18 * u, cy + 10 * u), 3 * u, col);
        shadowLine(v2(cx + 18 * u, cy - 10 * u), v2(cx + 18 * u, cy + 10 * u), 3 * u, col);
    }

    if (m.cue_t <= 0 or m.cue == .none) return;

    const label: [:0]const u8 = switch (m.cue) {
        .parry => "PARRY",
        .blocked => "BLOCKED",
        .clash => "CLASH",
        .counter => "COUNTER",
        .staggered => "STAGGERED",
        .none => "",
    };
    const tint = switch (m.cue) {
        .parry, .counter => ui.rgba(255, 206, 84, 255),
        .clash => ui.rgba(255, 240, 220, 255),
        .staggered => ui.rgba(255, 92, 80, 255),
        else => ui.white,
    };
    const alpha = @min(1, m.cue_t / 0.3);
    const pop = 1 + @max(0, m.cue_t - 0.6) * 1.5;
    const size = 26 * u * pop;

    ui.outlined(font_ref, label, cx - ui.width(font_ref, label, size) / 2, cy + 34 * u, size, ui.fade(tint, alpha));
}

fn crosshair(g: Game, cx: f32, cy: f32, u: f32) void {
    if (g.dead > 0) return;

    const a = g.arsenal;
    const spec = a.spec();
    const gap = (6 + g.aimSpread() * 500) * u;
    const len = 9 * u;
    const t = 2.5 * u;

    if (spec.class == .melee) {
        meleeReticle(g, cx, cy, u);
    } else if (spec.class == .shotgun and spec.pellets > 1 and g.ads < 0.6) {
        rl.DrawRing(v2(cx, cy), gap + 2 * u, gap + 5.5 * u, 0, 360, 48, ui.fade(ui.ink, 0.6));
        rl.DrawRing(v2(cx, cy), gap + 2.8 * u, gap + 4.7 * u, 0, 360, 48, ui.white);
        rl.DrawCircleV(v2(cx, cy), 2 * u, ui.white);
    } else if (g.ads < 0.6) {
        const col = settings.crosshairColor();

        switch (settings.crosshair_style) {
            1 => {
                rl.DrawCircleV(v2(cx, cy), 4 * u, ui.fade(ui.ink, 0.6));
                rl.DrawCircleV(v2(cx, cy), 2.6 * u, col);
            },
            2 => {
                rl.DrawRing(v2(cx, cy), gap + 3 * u, gap + 6.5 * u, 0, 360, 48, ui.fade(ui.ink, 0.6));
                rl.DrawRing(v2(cx, cy), gap + 3.8 * u, gap + 5.7 * u, 0, 360, 48, col);
                rl.DrawCircleV(v2(cx, cy), 1.8 * u, col);
            },
            3 => {
                shadowLine(v2(cx - len * 1.2, cy), v2(cx + len * 1.2, cy), t, col);
                shadowLine(v2(cx, cy - len * 1.2), v2(cx, cy + len * 1.2), t, col);
            },
            else => {
                shadowLine(v2(cx - gap - len, cy), v2(cx - gap, cy), t, col);
                shadowLine(v2(cx + gap, cy), v2(cx + gap + len, cy), t, col);
                shadowLine(v2(cx, cy - gap - len), v2(cx, cy - gap), t, col);
                shadowLine(v2(cx, cy + gap), v2(cx, cy + gap + len), t, col);
                rl.DrawCircleV(v2(cx, cy), 1.6 * u, col);
            },
        }
    } else {
        const glow = ui.rgba(255, 60, 50, 255);
        const k = std.math.clamp((g.ads - 0.6) / 0.4, 0, 1);
        const h: f32 = @floatFromInt(rl.GetScreenHeight());

        switch (spec.look.optic) {
            .holo => {
                rl.DrawRing(v2(cx, cy), 13 * u, 14.6 * u, 0, 360, 48, ui.fade(glow, 0.85 * k));
                rl.DrawCircleV(v2(cx, cy), 2 * u, ui.fade(glow, k));
            },
            .scope2, .scope4, .scope8 => sightReticle(g, cx, cy, u, h, k),
            else => {
                rl.DrawCircleV(v2(cx, cy), 4.5 * u, ui.fade(glow, 0.25 * k));
                rl.DrawCircleV(v2(cx, cy), 2.3 * u, ui.fade(glow, k));
            },
        }
    }

    if (spec.charge > 0 and a.charge > 0) {
        const f = a.charge / spec.charge;

        rl.DrawRing(v2(cx, cy), 24 * u, 29 * u, -90, -90 + 360 * f, 48, if (f >= 1) ui.yellow else ui.white);
    }

    if (spec.spinup > 0 and a.spin > 0 and a.spin < spec.spinup) {
        rl.DrawRing(v2(cx, cy), 24 * u, 28 * u, -90, -90 + 360 * a.spin / spec.spinup, 48, ui.orange);
    }

    if (a.reloading > 0) {
        const total = spec.reload * weapons.rarity_reload[@backingInt(a.current().rarity)];
        const f = 1 - a.reloading / total;

        rl.DrawRing(v2(cx, cy), 30 * u, 35 * u, 0, 360, 48, ui.fade(ui.ink, 0.45));
        rl.DrawRing(v2(cx, cy), 30 * u, 35 * u, -90, -90 + 360 * f, 48, ui.white);
    }

    if (g.hit_marker > 0) {
        const c = if (g.hit_kill) ui.red else ui.white;
        const s0 = 9 * u;
        const s1 = 17 * u;

        shadowLine(v2(cx - s0, cy - s0), v2(cx - s1, cy - s1), 3 * u, c);
        shadowLine(v2(cx + s0, cy - s0), v2(cx + s1, cy - s1), 3 * u, c);
        shadowLine(v2(cx - s0, cy + s0), v2(cx - s1, cy + s1), 3 * u, c);
        shadowLine(v2(cx + s0, cy + s0), v2(cx + s1, cy + s1), 3 * u, c);
    }
}

pub fn dockBase(w: f32, h: f32, u: f32) f32 {
    const l = touch.layout(w, h);

    return l.dock - 1.2 * l.unit - 10 * u;
}

fn dock(g: Game, font: rl.Font, icons: *const icons_mod.Icons, u: f32, w: f32, h: f32, buf: []u8) void {
    const l = touch.layout(w, h);
    const hp = print(buf, "{d}", .{@as(u32, @intFromFloat(@ceil(g.hp)))});
    const health = ui.width(font, hp, 44 * u) + 222 * u;
    const ammo_w = if (l.armed) compactWidth(g, font, u, buf) + 28 * u else 0;
    const space = if (l.armed) 8 * u else 0;
    const left = w / 2 - (health + space + ammo_w) / 2;
    const base = dockBase(w, h, u);

    vitals(g, font, u, left + 14 * u, base, buf);

    if (l.armed) ammoCompact(g, font, u, left + health + space + ammo_w - 14 * u, base, buf);

    if (l.bar == null) return;

    var i: u8 = 0;

    while (i < touch.slots) : (i += 1) slotCard(g, icons, u, i, l.slot(i));
}

fn vitals(g: Game, font: rl.Font, u: f32, x: f32, base: f32, buf: []u8) void {
    const frac = math01(g.hp / game_mod.max_hp);
    const low = frac < 0.3;
    const hp = print(buf, "{d}", .{@as(u32, @intFromFloat(@ceil(g.hp)))});
    const size = 44 * u;
    const nw = ui.width(font, hp, size);
    const bar_x = x + nw + 14 * u;
    const bar_w = 180 * u;
    const bar_h = 5 * u;
    const bar_y = base - 12 * u;
    const segs: f32 = 4;
    const gap = 3 * u;
    const seg_w = (bar_w - gap * (segs - 1)) / segs;
    const fill_color = if (low) ui.red else ui.white;
    var i: f32 = 0;

    ui.card(x - 14 * u, base - size - 8 * u, nw + bar_w + 42 * u, size + 18 * u, 0.85);
    ui.text(font, hp, x, base - size + 2 * u, size, fill_color);

    while (i < segs) : (i += 1) {
        const sx = bar_x + i * (seg_w + gap);
        const fill = math01(frac * segs - i);

        rl.DrawRectangleRec(.{ .x = sx, .y = bar_y, .width = seg_w, .height = bar_h }, ui.fade(ui.white, 0.16));

        if (fill > 0) rl.DrawRectangleRec(.{ .x = sx, .y = bar_y, .width = seg_w * fill, .height = bar_h }, fill_color);
    }

    ui.caps(font, "HEALTH", bar_x, bar_y - 20 * u, 12 * u, ui.fade(ui.white, 0.55));

    const icon_y = bar_y - 14 * u;
    var f: f32 = 0;

    while (f < game_mod.fire_max) : (f += 1) {
        const fx = bar_x + 84 * u + f * 13 * u;
        const fill = math01(g.fire_charges - f);
        const at = v2(fx, icon_y);

        rl.DrawCircleV(at, 4 * u, ui.fade(ui.white, 0.16));

        if (fill >= 1) rl.DrawCircleV(at, 4 * u, ui.orange) else if (fill > 0) rl.DrawCircleSector(at, 4 * u, -90, -90 + 360 * fill, 16, ui.fade(ui.orange, 0.6));
    }

    if (g.fire_held) rl.DrawRing(v2(bar_x + 97 * u, icon_y), 22 * u, 24 * u, -90, -90 + 360 * (g.fire_hold / game_mod.fire_charge_time), 32, ui.fade(ui.orange, 0.9));

    var k: u8 = 0;

    while (k < g.arsenal.grenades) : (k += 1) {
        const gx = bar_x + bar_w - @as(f32, @floatFromInt(k)) * 13 * u - 4 * u;

        rl.DrawCircleV(v2(gx, icon_y), 4 * u, ui.fade(ui.white, 0.85));
    }
}

fn math01(v: f32) f32 {
    return @min(1, @max(0, v));
}

fn inventory(g: Game, font: rl.Font, icons: *const icons_mod.Icons, u: f32, w: f32, h: f32, buf: []u8) void {
    const right = w - 36 * u;
    const slot_w = 84 * u;
    const slot_h = 42 * u;
    const gap = 4 * u;
    const row_y = h - 36 * u - slot_h;
    const row_x = right - slot_w * 5 - gap * 4;
    var i: u8 = 0;

    while (i <= game_mod.knife_slot) : (i += 1) {
        const x = row_x + @as(f32, @floatFromInt(i)) * (slot_w + gap);
        const key = print(buf, "{d}", .{i + 1});

        slotCard(g, icons, u, i, .{ .x = x, .y = row_y, .width = slot_w, .height = slot_h });
        ui.caps(font, key, x + 6 * u, row_y + 3 * u, 11 * u, ui.fade(ui.white, if (i == g.arsenal.active) @as(f32, 0.85) else @as(f32, 0.4)));
    }

    ammo(g, font, u, right, row_y - 10 * u, buf);
}

fn slotCard(g: Game, icons: *const icons_mod.Icons, u: f32, i: u8, rect: rl.Rectangle) void {
    const a = g.arsenal;
    const maybe: ?game_mod.Held = if (i == game_mod.knife_slot) a.blade else a.slots[i];
    const active = i == a.active;

    rl.DrawRectangleRounded(rect, 0.18, 6, ui.fade(ui.panel, if (active) @as(f32, 0.95) else @as(f32, 0.55)));
    rl.DrawRectangleRoundedLinesEx(rect, 0.18, 6, 1, if (active) ui.fade(ui.white, 0.55) else ui.edge);

    const held = maybe orelse return;
    const tex = icons.tex[held.weapon].texture;
    const pad = 6 * u;
    const fit_w = @min(rect.width - pad * 2, (rect.height - pad * 2) * 2.4);
    const fit_h = fit_w / 2.4;
    const dst: rl.Rectangle = .{ .x = rect.x + (rect.width - fit_w) / 2, .y = rect.y + (rect.height - fit_h) / 2, .width = fit_w, .height = fit_h };
    const src: rl.Rectangle = .{ .x = 0, .y = 0, .width = @floatFromInt(tex.width), .height = -@as(f32, @floatFromInt(tex.height)) };

    rl.DrawTexturePro(tex, src, dst, v2(0, 0), 0, ui.fade(ui.white, if (active) @as(f32, 1) else @as(f32, 0.45)));

    if (active) rl.DrawRectangleRec(.{ .x = rect.x + 8 * u, .y = rect.y + rect.height - 3 * u, .width = rect.width - 16 * u, .height = 2 * u }, ui.accent);
}

fn compactWidth(g: Game, font: rl.Font, u: f32, buf: []u8) f32 {
    const cur = g.arsenal.current();
    const spec = cur.spec();

    if (spec.mag == 0) return ui.capsWidth(font, print(buf, "{s}", .{spec.name}), 14 * u) + 12 * u;

    const reserve = ui.width(font, print(buf, "{d}", .{cur.reserve}), 22 * u);
    const mag = ui.width(font, print(buf, "{d}", .{cur.mag}), 48 * u);

    return reserve + mag + 20 * u;
}

fn ammoCompact(g: Game, font: rl.Font, u: f32, right: f32, base: f32, buf: []u8) void {
    const cur = g.arsenal.current();
    const spec = cur.spec();
    const card_w = compactWidth(g, font, u, buf);
    const middle = base - 21 * u;

    ui.card(right - card_w - 14 * u, base - 52 * u, card_w + 28 * u, 62 * u, 0.85);

    if (spec.mag == 0) {
        ui.caps(font, print(buf, "{s}", .{spec.name}), right - card_w + 6 * u, middle - 7 * u, 14 * u, ui.fade(ui.white, 0.8));

        return;
    }

    const reserve = print(buf, "{d}", .{cur.reserve});
    const rw = ui.width(font, reserve, 22 * u);

    ui.text(font, reserve, right - rw, middle - 6 * u, 22 * u, ui.fade(ui.white, 0.55));

    const sep_x = right - rw - 10 * u;

    rl.DrawRectangleRec(.{ .x = sep_x, .y = middle - 13 * u, .width = 1.5 * u, .height = 26 * u }, ui.fade(ui.white, 0.3));

    const mag = print(buf, "{d}", .{cur.mag});
    const mw = ui.width(font, mag, 48 * u);

    ui.text(font, mag, sep_x - 10 * u - mw, middle - 25 * u, 48 * u, if (cur.mag == 0) ui.red else ui.white);
}

fn ammoWidth(g: Game, font: rl.Font, u: f32, buf: []u8) f32 {
    const cur = g.arsenal.current();
    const spec = cur.spec();
    const nm = print(buf, "{s}", .{spec.name});
    const name_w = ui.capsWidth(font, nm, 14 * u) + 12 * u;

    if (spec.mag == 0) return name_w;

    const rv = print(buf, "{d}", .{cur.reserve});
    const rvw = ui.width(font, rv, 22 * u);
    const mg = print(buf, "{d}", .{cur.mag});
    const mgw = ui.width(font, mg, 48 * u);

    return @max(name_w, rvw + mgw + 20 * u);
}

fn ammo(g: Game, font: rl.Font, u: f32, right: f32, base: f32, buf: []u8) void {
    const cur = g.arsenal.current();
    const spec = cur.spec();
    const card_w = ammoWidth(g, font, u, buf);
    const card_h: f32 = if (spec.mag > 0) 78 * u else 30 * u;

    ui.card(right - card_w - 14 * u, base - 84 * u, card_w + 28 * u, card_h, 0.85);

    if (spec.mag > 0) {
        const reserve = print(buf, "{d}", .{cur.reserve});
        const rsize = 22 * u;
        const rw = ui.width(font, reserve, rsize);

        ui.text(font, reserve, right - rw, base - rsize - 6 * u, rsize, ui.fade(ui.white, 0.55));

        const sep_x = right - rw - 10 * u;

        rl.DrawRectangleRec(.{ .x = sep_x, .y = base - 36 * u, .width = 1.5 * u, .height = 26 * u }, ui.fade(ui.white, 0.3));

        const mag = print(buf, "{d}", .{cur.mag});
        const msize = 48 * u;
        const mw = ui.width(font, mag, msize);

        ui.text(font, mag, sep_x - 10 * u - mw, base - msize - 2 * u, msize, if (cur.mag == 0) ui.red else ui.white);
    }

    const name = print(buf, "{s}", .{spec.name});
    const nsize = 14 * u;
    const nw = ui.capsWidth(font, name, nsize);
    const rc = ui.rarity[@backingInt(cur.rarity)];

    ui.caps(font, name, right - nw, base - 74 * u, nsize, ui.fade(ui.white, 0.8));
    rl.DrawCircleV(v2(right - nw - 9 * u, base - 74 * u + nsize * 0.55), 3.5 * u, rc);
}

fn topBar(g: Game, font: rl.Font, u: f32, w: f32, buf: []u8) void {
    const left = g.to_spawn + @as(u32, @intCast(g.bots.countActive()));
    const size = 15 * u;
    const y = 22 * u;

    if (g.wave == 0) {
        const line: [:0]const u8 = "GET READY";
        const tw = ui.capsWidth(font, line, size);
        const pw = tw + 36 * u;

        ui.card(w / 2 - pw / 2, y, pw, 34 * u, 0.9);
        ui.caps(font, line, w / 2 - tw / 2, y + 9 * u, size, ui.white);

        return;
    }

    const wave = print(buf[0..32], "WAVE {d}", .{g.wave});
    const rest = print(buf[32..64], "{d} LEFT", .{left});
    const pts = print(buf[64..96], "{d} PTS", .{g.score});
    const ww = ui.capsWidth(font, wave, size);
    const rw = ui.capsWidth(font, rest, size);
    const pw = ui.capsWidth(font, pts, size);
    const gap = 26 * u;
    const total = ww + rw + pw + gap * 2 + 40 * u;
    var x = w / 2 - total / 2;

    ui.card(x, y, total, 34 * u, 0.9);
    x += 20 * u;
    ui.caps(font, wave, x, y + 9 * u, size, ui.accent);
    x += ww + gap;
    rl.DrawRectangleRec(.{ .x = x - gap / 2, .y = y + 10 * u, .width = 1, .height = 14 * u }, ui.fade(ui.white, 0.25));
    ui.caps(font, rest, x, y + 9 * u, size, ui.white);
    x += rw + gap;
    rl.DrawRectangleRec(.{ .x = x - gap / 2, .y = y + 10 * u, .width = 1, .height = 14 * u }, ui.fade(ui.white, 0.25));
    ui.caps(font, pts, x, y + 9 * u, size, ui.fade(ui.white, 0.75));
}

fn feed(g: Game, font: rl.Font, u: f32, w: f32, buf: []u8) void {
    var row: f32 = 0;

    for (g.feed.items) |f| {
        if (!f.active) continue;

        const line = switch (f.kind) {
            .bot_down => print(buf, "Enemy down  +{d}", .{f.value}),
            .wave_clear => print(buf, "Wave cleared  +{d}", .{f.value}),
            .ammo => print(buf, "Ammo restocked", .{}),
            .health => print(buf, "Healed  +{d}", .{f.value}),
            .weapon => print(buf, "{s} {s}", .{ weapons.rarity_names[@backingInt(f.rarity)], weapons.specs[f.weapon].name }),
        };
        const size = 16 * u;
        const color = switch (f.kind) {
            .weapon => ui.rarity[@backingInt(f.rarity)],
            .bot_down, .wave_clear => ui.accent,
            .ammo, .health => ui.green,
        };
        const tw = ui.width(font, line, size);
        const alpha = @min(1, f.life * 2);
        const slide = (1 - math01(f.life * 4)) * 0;
        const y = 76 * u + row * 34 * u;
        const bw = tw + 30 * u;
        const clear = if (touch.shown) touch.feedRight(w, @floatFromInt(rl.GetScreenHeight())) else null;
        const bx = (clear orelse w - 36 * u) - bw + slide;

        ui.card(bx, y, bw, 28 * u, alpha);
        rl.DrawRectangleRec(.{ .x = bx, .y = y + 6 * u, .width = 2 * u, .height = 16 * u }, ui.fade(color, alpha));
        ui.text(font, line, bx + 16 * u, y + 6 * u, size, ui.fade(ui.white, alpha * 0.92));
        row += 1;
    }
}

fn banner(g: Game, font: rl.Font, u: f32, cx: f32, h: f32, buf: []u8) void {
    if (g.banner <= 0) return;

    const line = switch (g.banner_kind) {
        .none => return,
        .wave_start => print(buf, "WAVE {d}", .{g.wave}),
        .wave_clear => print(buf, "WAVE {d} CLEARED", .{g.wave}),
        .erased => print(buf, "DOWN  BACK IN {d:.1}", .{@max(0, g.dead)}),
    };
    const sub: [:0]const u8 = switch (g.banner_kind) {
        .wave_start => "INCOMING",
        .wave_clear => "WELL DONE",
        else => "",
    };
    const color = switch (g.banner_kind) {
        .erased => ui.red,
        .wave_clear => ui.green,
        else => ui.accent,
    };
    const alpha = @min(1, g.banner * 2);
    const rise = (1 - alpha) * 10 * u;
    const size = 46 * u;
    const tw = ui.capsWidth(font, line, size);
    const y = h * 0.22 + rise;

    if (sub.len > 0) {
        const ss = 13 * u;
        const sw = ui.capsWidth(font, sub, ss);

        ui.caps(font, sub, cx - sw / 2, y - 22 * u, ss, ui.fade(color, alpha));
    }

    rl.DrawTextEx(font, line.ptr, v2(cx - tw / 2, y + 2 * u), size, size * 0.14, ui.fade(ui.ink, alpha * 0.35));
    ui.caps(font, line, cx - tw / 2, y, size, ui.fade(ui.white, alpha));

    const lw = 60 * u;
    const ly = y + size * 0.55;

    rl.DrawRectangleRec(.{ .x = cx - tw / 2 - lw - 18 * u, .y = ly, .width = lw, .height = 2 * u }, ui.fade(color, alpha * 0.8));
    rl.DrawRectangleRec(.{ .x = cx + tw / 2 + 18 * u, .y = ly, .width = lw, .height = 2 * u }, ui.fade(color, alpha * 0.8));
}

fn prompt(g: Game, font: rl.Font, u: f32, cx: f32, cy: f32, pad: bool, buf: []u8) void {
    const index = g.near_drop orelse return;
    const d = g.drops.items[index];

    if (!d.active or g.dead > 0) return;

    const spec = d.held.spec();
    const color = ui.rarity[@backingInt(d.held.rarity)];
    const key: [:0]const u8 = if (pad) "X" else "E";
    const verb: [:0]const u8 = if (pad) "HOLD" else "PICK UP";

    interact(font, u, cx, cy + 90 * u, key, verb, print(buf, "{s}", .{spec.name}), color);
}

pub fn interact(font: rl.Font, u: f32, cx: f32, y: f32, key: [:0]const u8, verb: [:0]const u8, name: [:0]const u8, color: rl.Color) void {
    const label: [:0]const u8 = if (touch.shown) "TAP" else key;
    const ks = 14 * u;
    const vs = 12 * u;
    const ns = 18 * u;
    const kw = @max(ks * 1.4, ui.width(font, label, ks) + ks * 0.8);
    const vw = ui.capsWidth(font, verb, vs);
    const nw = ui.width(font, name, ns);
    const pw = 14 * u + kw + 12 * u + vw + 10 * u + nw + 18 * u;
    const ph = 40 * u;
    const x = cx - pw / 2;

    ui.card(x, y, pw, ph, 1);
    _ = ui.keycap(font, label, x + 14 * u, y + (ph - ks * 1.4) / 2, ks, 1);
    ui.caps(font, verb, x + 14 * u + kw + 12 * u, y + (ph - vs) / 2 - 1 * u, vs, ui.fade(ui.white, 0.6));
    ui.text(font, name, x + 14 * u + kw + 12 * u + vw + 10 * u, y + (ph - ns) / 2 - 1 * u, ns, ui.white);
    rl.DrawRectangleRec(.{ .x = x + 12 * u, .y = y + ph - 2 * u, .width = pw - 24 * u, .height = 2 * u }, color);
}

fn pause(pad: bool) void {
    const v = theme.view();
    const u = v.u;
    const buttons = menu.pauseSlot(0);
    const touching = v.touch and !pad;
    const top = v.top;
    const bottom = buttons.y - 24 * u;

    theme.scrim(0.66);

    const Bind = struct { k: [:0]const u8, a: [:0]const u8 };
    const keyboard = [_]Bind{
        .{ .k = "WASD", .a = "Move" },       .{ .k = "Space", .a = "Jump" },
        .{ .k = "LMB", .a = "Shoot" },       .{ .k = "RMB", .a = "Aim" },
        .{ .k = "1-4", .a = "Guns" },        .{ .k = "5", .a = "Knife" },
        .{ .k = "R", .a = "Reload" },        .{ .k = "G", .a = "Grenade" },
        .{ .k = "E", .a = "Pick up" },       .{ .k = "T", .a = "Throw gun" },
        .{ .k = "F", .a = "Enter vehicle" }, .{ .k = "Esc", .a = "Free mouse" },
    };
    const controller = [_]Bind{
        .{ .k = "LS", .a = "Move" },        .{ .k = "RS", .a = "Look" },
        .{ .k = "RT", .a = "Shoot" },       .{ .k = "LT", .a = "Aim" },
        .{ .k = "A", .a = "Jump" },         .{ .k = "X", .a = "Reload" },
        .{ .k = "RB", .a = "Grenade" },     .{ .k = "Y", .a = "Switch / vehicle" },
        .{ .k = "LB", .a = "Last weapon" }, .{ .k = "B", .a = "Knife" },
        .{ .k = "Hold X", .a = "Pick up" }, .{ .k = "Start", .a = "Pause" },
    };
    const binds: []const Bind = if (pad) &controller else &keyboard;
    const cols: usize = 3;
    const rows: f32 = @floatFromInt((binds.len + cols - 1) / cols);
    const row_h = 46 * u;
    const col_w = 290 * u;
    const title_h = 170 * u;
    const resume_h = v.tap(100);
    const card_h = if (touching) 0 else rows * row_h + 40 * u;
    const gap = 34 * u;
    const total = title_h + resume_h + (if (touching) 0 else card_h + gap);
    const y = top + @max(0, (bottom - top - total) * 0.55);
    const title_y = y + 58 * u;
    const size = 130 * u;

    theme.extruded(theme.heavy, "PAUSED", v.cx() - theme.measure(theme.heavy, "PAUSED", size) / 2, title_y, size, theme.cream, 1);

    const how: [:0]const u8 = if (pad) "Press Start to play" else if (touching) "Tap anywhere to play" else "Click anywhere to play";

    theme.center(theme.body, how, v.cx(), title_y + 82 * u, 30 * u, theme.fade(theme.cream, 0.82));

    var at = y + title_h;
    const bw = @min(460 * u, v.width());
    const play: rl.Rectangle = .{ .x = v.cx() - bw / 2, .y = at, .width = bw, .height = resume_h - 8 * u };
    const face = theme.button(theme.tag("resume", 0), play, 26 * u, theme.tones.coral_tone, rl.CheckCollisionPointRec(rl.GetMousePosition(), play), .{}).face;
    const label_size = 58 * u;
    const label_w = theme.measure(theme.heavy, "RESUME", label_size);
    const mid = face.y + face.height / 2;
    const x = face.x + face.width / 2 - (label_w + 68 * u) / 2;

    theme.icon(.play, x + 26 * u, mid, 54 * u, theme.cream);
    theme.write(theme.heavy, "RESUME", x + 68 * u, mid, label_size, theme.cream);

    if (touching) return;

    at += resume_h + gap;

    const pw = @min(col_w * @as(f32, @floatFromInt(cols)) + 40 * u, v.width());
    const cw = (pw - 40 * u) / @as(f32, @floatFromInt(cols));
    const card: rl.Rectangle = .{ .x = v.cx() - pw / 2, .y = at, .width = pw, .height = card_h };

    theme.panel(card, 28 * u, theme.cream, 1);

    for (binds, 0..) |b, i| {
        const col: f32 = @floatFromInt(i % cols);
        const row: f32 = @floatFromInt(i / cols);
        const bx = card.x + 32 * u + col * cw;
        const by = card.y + 20 * u + row * row_h + row_h / 2;
        const ks = 23 * u;
        const kw = @max(36 * u, theme.measure(theme.heavy, b.k, ks) + 20 * u);

        theme.round(.{ .x = bx, .y = by - 17 * u + 3 * u, .width = kw, .height = 34 * u }, 9 * u, theme.night);
        theme.round(.{ .x = bx, .y = by - 17 * u, .width = kw, .height = 34 * u }, 9 * u, theme.navy);
        theme.center(theme.heavy, b.k, bx + kw / 2, by, ks, theme.cream);
        theme.write(theme.body, b.a, bx + kw + 14 * u, by, theme.fit(theme.body, b.a, 27 * u, cw - kw - 30 * u), theme.navy);
    }
}

fn speedLines(w: f32, h: f32, u: f32, k: f32) void {
    const t: f32 = @floatCast(rl.GetTime());
    const cx = w / 2;
    const cy = h / 2;
    const reach = @sqrt(cx * cx + cy * cy);
    var i: f32 = 0;

    while (i < 42) : (i += 1) {
        const seed = @sin(i * 12.9898) * 43758.5453;
        const r0 = seed - @floor(seed);
        const ang = i / 42 * std.math.tau + r0 * 0.3;
        const phase = @mod(t * (1.6 + r0 * 1.8) + r0 * 7, 1);
        const start = reach * (0.52 + phase * 0.42);
        const len = reach * (0.06 + 0.1 * math01(k)) * (0.6 + r0);
        const dx = @cos(ang);
        const dy = @sin(ang);
        const a = (1 - phase) * 0.55 * math01(k * 1.3);

        rl.DrawLineEx(.{ .x = cx + dx * start, .y = cy + dy * start }, .{ .x = cx + dx * (start + len), .y = cy + dy * (start + len) }, (1.5 + r0 * 2) * u, ui.fade(ui.rgba(210, 235, 255, 255), a));
    }
}

pub fn vehicleStatus(g: Game, font: rl.Font) void {
    const driving = @import("driving.zig");
    const vehicle = shared.vehicle;
    const w: f32 = @floatFromInt(rl.GetScreenWidth());
    const h: f32 = @floatFromInt(rl.GetScreenHeight());
    const u = @min(h / 900, w / 1500);
    var buf: [64]u8 = undefined;

    if (driving.current(&g)) |v| {
        const s = v.spec();
        const x = if (touch.shown) w / 2 - 160 * u else 40 * u;
        const base = if (touch.shown) dockBase(w, h, u) - 74 * u else h - 118 * u;
        const kmh = print(&buf, "{d}", .{@as(u32, @intFromFloat(@abs(v.speed) * 3.6))});
        const size = 40 * u;
        const nw = ui.width(font, kmh, size);
        const bar_x = x + @max(nw, 60 * u) + 16 * u;
        const bar_w = 200 * u;
        const bar_h = 7 * u;
        const bar_y = base - 14 * u;
        const frac = math01(v.hp / s.hp);
        const low = frac < 0.3;
        const segs: f32 = 4;
        const gap = 3 * u;
        const seg_w = (bar_w - gap * (segs - 1)) / segs;
        var i: f32 = 0;

        if (touch.shown) ui.card(x - 14 * u, base - 44 * u, @max(nw, 60 * u) + bar_w + 82 * u, 68 * u, 0.85);

        ui.text(font, kmh, x, base - size, size, ui.white);
        ui.text(font, "KM/H", x, base + 2 * u, 13 * u, ui.fade(ui.white, 0.6));

        while (i < segs) : (i += 1) {
            const sx = bar_x + i * (seg_w + gap);
            const fill = math01(frac * segs - i);

            rl.DrawRectangleRec(.{ .x = sx, .y = bar_y, .width = seg_w, .height = bar_h }, ui.fade(ui.ink, 0.45));

            if (fill > 0) rl.DrawRectangleRec(.{ .x = sx, .y = bar_y, .width = seg_w * fill, .height = bar_h }, if (low) ui.red else ui.rgba(255, 196, 90, 255));
        }

        ui.text(font, s.name, bar_x, bar_y - 22 * u, 15 * u, ui.fade(ui.white, 0.6));

        const ny = bar_y + 13 * u;
        const nh = 6 * u;
        const glow = if (v.boosting) 0.5 + 0.5 * @sin(@as(f32, @floatCast(rl.GetTime())) * 30) else 0;
        const blue = ui.rgba(90, 190, 255, 255);

        rl.DrawRectangleRounded(.{ .x = bar_x, .y = ny, .width = bar_w, .height = nh }, 1, 6, ui.fade(ui.ink, 0.45));

        if (v.nitro > 0.01) rl.DrawRectangleRounded(.{ .x = bar_x, .y = ny, .width = bar_w * math01(v.nitro), .height = nh }, 1, 6, if (v.nitro >= 0.999) ui.rgba(150, 220, 255, 255) else blue);

        if (v.boosting) rl.DrawRectangleRounded(.{ .x = bar_x - 2 * u, .y = ny - 2 * u, .width = bar_w * math01(v.nitro) + 4 * u, .height = nh + 4 * u }, 1, 6, ui.fade(blue, 0.25 * glow));

        ui.text(font, "NITRO", bar_x + bar_w + 8 * u, ny - 3 * u, 12 * u, ui.fade(blue, if (v.nitro >= 0.999) 1 else 0.7));

        if (v.boosting) speedLines(w, h, u, @abs(v.speed) / @max(s.top_speed, 1));

        return;
    }

    if (g.dead > 0) return;

    const at = g.player.center();

    for (g.vehicles) |v| {
        if (!v.alive() or !vehicle.usableBy(at, v) or !vehicle.inView(at, g.yaw, v)) continue;

        interact(font, u, w / 2, h / 2 + 90 * u, "F", "ENTER", print(&buf, "{s}", .{v.spec().name}), ui.accent);

        return;
    }
}
