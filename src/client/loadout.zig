const std = @import("std");
const rl = @import("raylib");
const shared = @import("shared");
const ui = @import("ui.zig");
const audio = @import("audio.zig");
const icons_mod = @import("icons.zig");
const game_mod = @import("game.zig");

const weapons = shared.weapons;
const Class = weapons.Class;
const Game = game_mod.Game;
const Held = game_mod.Held;
const v2 = ui.v2;

const Group = struct {
    name: [:0]const u8,
    classes: []const Class,
};

const groups = [_]Group{
    .{ .name = "All", .classes = &.{ .pistol, .smg, .rifle, .dmr, .sniper, .shotgun, .lmg, .launcher, .special, .bow, .crossbow } },
    .{ .name = "Pistols", .classes = &.{.pistol} },
    .{ .name = "SMGs", .classes = &.{.smg} },
    .{ .name = "Assault Rifles", .classes = &.{.rifle} },
    .{ .name = "Marksman", .classes = &.{.dmr} },
    .{ .name = "Snipers", .classes = &.{.sniper} },
    .{ .name = "Shotguns", .classes = &.{.shotgun} },
    .{ .name = "Machine Guns", .classes = &.{.lmg} },
    .{ .name = "Heavy", .classes = &.{ .launcher, .special } },
    .{ .name = "Bows", .classes = &.{ .bow, .crossbow } },
    .{ .name = "Knives", .classes = &.{.melee} },
};

const max_cards = 64;
const slot_count = game_mod.knife_slot + 1;

const List = struct {
    items: [max_cards]u8 = undefined,
    len: usize = 0,
};

fn listFor(tab: usize) List {
    var out: List = .{};

    for (weapons.specs, 0..) |s, i| {
        if (out.len == max_cards) break;

        for (groups[tab].classes) |c| {
            if (s.class == c) {
                out.items[out.len] = @intCast(i);
                out.len += 1;

                break;
            }
        }
    }

    return out;
}

fn isMelee(w: u8) bool {
    return weapons.specs[w].class == .melee;
}

pub const Loadout = struct {
    open: bool = false,
    t: f32 = 0,
    tab: usize = 2,
    sel: usize = 0,
    slot: u8 = 0,
    rarity: u8 = 2,
    slide: f32 = 2,
    glow: [max_cards]f32 = @splat(0),
    slot_glow: [slot_count]f32 = @splat(0),
    flash: f32 = 0,
    flash_slot: u8 = 0,
    from_game: bool = false,
    hold: f32 = 0,
    hold_x: i32 = 0,
    hold_y: i32 = 0,
    mouse_last: rl.Vector2 = .{},
    using_mouse: bool = true,
    stick_ready: bool = false,
    hot_last: ?usize = null,
    spin: f32 = 0,

    pub fn show(l: *Loadout, g: *const Game, from_game: bool) void {
        l.open = true;
        l.from_game = from_game;
        l.stick_ready = false;
        l.slot = g.arsenal.active;
        l.focusHeld(g);
        audio.ui(.click);
    }

    pub fn close(l: *Loadout) void {
        l.open = false;
        audio.ui(.back);
    }

    fn focusHeld(l: *Loadout, g: *const Game) void {
        const held = heldIn(g, l.slot) orelse return;

        for (groups, 0..) |_, tab| {
            const list = listFor(tab);

            for (list.items[0..list.len], 0..) |w, i| {
                if (w != held.weapon) continue;

                l.tab = tab;
                l.sel = i;
                l.rarity = @intFromEnum(held.rarity);

                return;
            }
        }
    }

    pub fn wantsOpen(l: *const Loadout, paused: bool, pad: ?c_int) bool {
        _ = l;

        if (rl.IsKeyPressed(rl.KEY_L)) return true;

        if (pad) |id| {
            if (!paused and rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_MIDDLE_LEFT)) return true;

            if (paused and rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_LEFT_TRIGGER_1)) return true;
        }

        if (paused and rl.IsMouseButtonPressed(rl.MOUSE_BUTTON_LEFT)) return rl.CheckCollisionPointRec(rl.GetMousePosition(), buttonRect());

        return false;
    }

    pub fn update(l: *Loadout, dt: f32, pad: ?c_int, g: *Game) void {
        l.t = std.math.clamp(l.t + (if (l.open) dt else -dt) * 6, 0, 1);
        l.slide += (@as(f32, @floatFromInt(l.tab)) - l.slide) * @min(1, dt * 14);
        l.flash = @max(0, l.flash - dt * 1.6);
        l.spin *= @exp(-dt * 10);

        const list = listFor(l.tab);

        l.sel = @min(l.sel, if (list.len == 0) 0 else list.len - 1);

        for (0..max_cards) |i| {
            const want: f32 = if (i < list.len and i == l.sel) 1 else 0;

            l.glow[i] += (want - l.glow[i]) * @min(1, dt * 16);
        }

        for (0..slot_count) |i| {
            const want: f32 = if (i == l.slot) 1 else 0;

            l.slot_glow[i] += (want - l.slot_glow[i]) * @min(1, dt * 16);
        }

        if (!l.open) return;

        const back = rl.IsKeyPressed(rl.KEY_ESCAPE) or rl.IsKeyPressed(rl.KEY_BACKSPACE) or rl.IsKeyPressed(rl.KEY_L) or rl.IsKeyPressed(rl.KEY_BACK) or (if (pad) |id| rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_FACE_RIGHT) or rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_MIDDLE_LEFT) or rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_MIDDLE_RIGHT) else false);

        if (back) {
            l.close();

            return;
        }

        var tab_dir: i32 = 0;
        var slot_dir: i32 = 0;
        var x: i32 = 0;
        var y: i32 = 0;
        var equip_now = rl.IsKeyPressed(rl.KEY_ENTER) or rl.IsKeyPressed(rl.KEY_SPACE);
        var rarity_dir: i32 = 0;

        if (rl.IsKeyPressed(rl.KEY_E) or rl.IsKeyPressed(rl.KEY_PAGE_DOWN)) tab_dir = 1;
        if (rl.IsKeyPressed(rl.KEY_Q) or rl.IsKeyPressed(rl.KEY_PAGE_UP)) tab_dir = -1;
        if (rl.IsKeyPressed(rl.KEY_R)) rarity_dir = 1;
        if (rl.IsKeyPressed(rl.KEY_F)) rarity_dir = -1;
        if (rl.IsKeyDown(rl.KEY_RIGHT) or rl.IsKeyDown(rl.KEY_D)) x = 1;
        if (rl.IsKeyDown(rl.KEY_LEFT) or rl.IsKeyDown(rl.KEY_A)) x = -1;
        if (rl.IsKeyDown(rl.KEY_DOWN) or rl.IsKeyDown(rl.KEY_S)) y = 1;
        if (rl.IsKeyDown(rl.KEY_UP) or rl.IsKeyDown(rl.KEY_W)) y = -1;

        for (0..slot_count) |k| {
            if (rl.IsKeyPressed(rl.KEY_ONE + @as(c_int, @intCast(k)))) l.pickSlot(g, @intCast(k));
        }

        if (pad) |id| {
            const sx = rl.GetGamepadAxisMovement(id, rl.GAMEPAD_AXIS_LEFT_X);
            const sy = rl.GetGamepadAxisMovement(id, rl.GAMEPAD_AXIS_LEFT_Y);

            if (@abs(sx) < 0.3 and @abs(sy) < 0.3) l.stick_ready = true;

            const live = l.stick_ready;

            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_TRIGGER_1)) tab_dir = 1;
            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_LEFT_TRIGGER_1)) tab_dir = -1;
            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_TRIGGER_2)) slot_dir = 1;
            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_LEFT_TRIGGER_2)) slot_dir = -1;
            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_FACE_LEFT)) rarity_dir = 1;
            if (rl.IsGamepadButtonPressed(id, rl.GAMEPAD_BUTTON_RIGHT_FACE_DOWN)) equip_now = true;
            if (rl.IsGamepadButtonDown(id, rl.GAMEPAD_BUTTON_LEFT_FACE_RIGHT) or (live and sx > 0.55)) x = 1;
            if (rl.IsGamepadButtonDown(id, rl.GAMEPAD_BUTTON_LEFT_FACE_LEFT) or (live and sx < -0.55)) x = -1;
            if (rl.IsGamepadButtonDown(id, rl.GAMEPAD_BUTTON_LEFT_FACE_DOWN) or (live and sy > 0.55)) y = 1;
            if (rl.IsGamepadButtonDown(id, rl.GAMEPAD_BUTTON_LEFT_FACE_UP) or (live and sy < -0.55)) y = -1;
        }

        if (tab_dir != 0) l.setTab(@intCast(@mod(@as(i32, @intCast(l.tab)) + tab_dir, @as(i32, groups.len))));

        if (slot_dir != 0) l.pickSlot(g, @intCast(@mod(@as(i32, l.slot) + slot_dir, @as(i32, slot_count))));

        if (rarity_dir != 0) {
            l.rarity = @intCast(@mod(@as(i32, l.rarity) + rarity_dir, @as(i32, weapons.rarity_names.len)));
            audio.ui(.hover);
        }

        if (x != 0 or y != 0) l.using_mouse = false;

        if (l.repeat(x, y, dt)) {
            if (y != 0) {
                l.setTab(@intCast(@mod(@as(i32, @intCast(l.tab)) + y, @as(i32, groups.len))));
            } else if (list.len > 0) {
                l.step(x, list.len);
            }
        }

        if (equip_now and list.len > 0) l.equip(g, list.items[l.sel]);

        l.mouse(g, list);
    }

    fn repeat(l: *Loadout, x: i32, y: i32, dt: f32) bool {
        if (x == 0 and y == 0) {
            l.hold_x = 0;
            l.hold_y = 0;
            l.hold = 0;

            return false;
        }

        if (x != l.hold_x or y != l.hold_y) {
            l.hold_x = x;
            l.hold_y = y;
            l.hold = 0.32;

            return true;
        }

        l.hold -= dt;

        if (l.hold > 0) return false;

        l.hold = 0.1;

        return true;
    }

    fn step(l: *Loadout, dir: i32, n: usize) void {
        const len: i32 = @intCast(n);

        l.sel = @intCast(@mod(@as(i32, @intCast(l.sel)) + dir, len));
        l.spin = @as(f32, @floatFromInt(dir));
        audio.ui(.hover);
    }

    fn setTab(l: *Loadout, tab: usize) void {
        l.tab = tab;
        l.sel = 0;
        audio.ui(.hover);
    }

    fn pickSlot(l: *Loadout, g: *const Game, slot: u8) void {
        if (slot == l.slot) return;

        l.slot = slot;
        l.focusHeld(g);
        audio.ui(.hover);
    }

    fn mouse(l: *Loadout, g: *Game, list: List) void {
        const mp = rl.GetMousePosition();
        const moved = mp.x != l.mouse_last.x or mp.y != l.mouse_last.y;
        const click = rl.IsMouseButtonPressed(rl.MOUSE_BUTTON_LEFT);
        const lay = layout();

        l.mouse_last = mp;

        if (moved or click) l.using_mouse = true;

        const wheel = rl.GetMouseWheelMove();

        if (wheel != 0 and list.len > 0) l.step(if (wheel > 0) -1 else 1, list.len);

        var hot: ?usize = null;
        const car = carousel(lay);

        if (list.len > 0 and click) {
            if (rl.CheckCollisionPointRec(mp, car.left) or rl.CheckCollisionPointRec(mp, car.arrow_l)) {
                l.step(-1, list.len);

                return;
            }

            if (rl.CheckCollisionPointRec(mp, car.right) or rl.CheckCollisionPointRec(mp, car.arrow_r)) {
                l.step(1, list.len);

                return;
            }

            if (rl.CheckCollisionPointRec(mp, car.equip) or rl.CheckCollisionPointRec(mp, car.center)) {
                l.equip(g, list.items[l.sel]);

                return;
            }
        }

        if (rl.CheckCollisionPointRec(mp, car.equip)) hot = l.sel;

        if (hot != null and hot != l.hot_last and moved) audio.ui(.hover);

        l.hot_last = hot;

        if (!click) return;

        for (groups, 0..) |_, i| {
            if (rl.CheckCollisionPointRec(mp, tabRect(lay, i))) {
                l.setTab(i);

                return;
            }
        }

        for (0..slot_count) |i| {
            if (rl.CheckCollisionPointRec(mp, slotRect(lay, i))) {
                l.pickSlot(g, @intCast(i));

                return;
            }
        }

        for (0..weapons.rarity_names.len) |i| {
            if (rl.CheckCollisionPointRec(mp, rarityRect(lay, i))) {
                l.rarity = @intCast(i);
                audio.ui(.click);

                return;
            }
        }

        if (rl.CheckCollisionPointRec(mp, lay.back)) l.close();
    }

    fn equip(l: *Loadout, g: *Game, w: u8) void {
        const a = &g.arsenal;
        const held = Held.fresh(w, @enumFromInt(l.rarity));
        var slot = l.slot;

        if (isMelee(w)) {
            slot = game_mod.knife_slot;
        } else if (slot == game_mod.knife_slot) {
            slot = if (a.active < game_mod.knife_slot) a.active else blk: {
                for (a.slots, 0..) |s, k| {
                    if (s == null) break :blk @intCast(k);
                }

                break :blk 0;
            };
        }

        if (slot == game_mod.knife_slot) a.blade = held else a.slots[slot] = held;

        if (a.active != slot) a.previous = a.active;

        a.active = slot;
        a.reloading = 0;
        a.cooldown = 0;
        a.swing = 0;
        a.charge = 0;
        a.spin = 0;
        a.burst_left = 0;
        a.switching = 0.32;
        a.shown = 2.5;
        l.slot = slot;
        l.flash = 1;
        l.flash_slot = slot;
        audio.ui(.click);
    }

    pub fn drawButton(l: *const Loadout, font: rl.Font, pad: bool, hidden: f32) void {
        if (l.t > 0.99 or hidden > 0.99) return;

        const r = buttonRect();
        const u = unit();
        const hot = rl.CheckCollisionPointRec(rl.GetMousePosition(), r);
        const a = (1 - l.t) * (1 - hidden);
        const label: [:0]const u8 = "LOADOUT";
        const hint: [:0]const u8 = if (pad) "LB" else "L";
        const size = 22 * u;

        rl.DrawRectangleRounded(.{ .x = r.x + 3 * u, .y = r.y + 5 * u, .width = r.width, .height = r.height }, 0.5, 12, ui.fade(ui.ink, 0.35 * a));
        rl.DrawRectangleRounded(r, 0.5, 12, ui.fade(if (hot) ui.white else ui.ink, (if (hot) @as(f32, 0.95) else 0.82) * a));
        gunGlyph(r.x + 34 * u, r.y + r.height / 2, 13 * u, ui.fade(if (hot) ui.ink else ui.yellow, a));
        ui.text(font, label, r.x + 58 * u, r.y + r.height / 2 - size / 2, size, ui.fade(if (hot) ui.ink else ui.white, a));

        const kw = ui.width(font, hint, 15 * u) + 14 * u;
        const kx = r.x + r.width - 18 * u - kw;

        rl.DrawRectangleRounded(.{ .x = kx, .y = r.y + r.height / 2 - 13 * u, .width = kw, .height = 26 * u }, 0.4, 8, ui.fade(if (hot) ui.ink else ui.white, 0.16 * a));
        ui.text(font, hint, kx + 7 * u, r.y + r.height / 2 - 8 * u, 15 * u, ui.fade(if (hot) ui.ink else ui.white, 0.75 * a));
    }

    pub fn draw(l: *const Loadout, font: rl.Font, icons: *const icons_mod.Icons, g: *const Game, pad: bool) void {
        if (l.t <= 0.001) return;

        const w: f32 = @floatFromInt(rl.GetScreenWidth());
        const h: f32 = @floatFromInt(rl.GetScreenHeight());
        const u = unit();
        const e = ease(l.t);
        const lay = layout();
        const dy = (1 - e) * 28 * u;
        const p = shift(lay.panel, dy);
        const list = listFor(l.tab);

        rl.DrawRectangleGradientV(0, 0, @intFromFloat(w), @intFromFloat(h), ui.fade(ui.rgba(24, 28, 42, 255), e), ui.fade(ui.rgba(9, 11, 17, 255), e));
        rl.DrawCircleGradient(.{ .x = w / 2, .y = h * 0.42 }, w * 0.4, ui.fade(ui.rgba(120, 140, 180, 255), 0.12 * e), ui.fade(ui.rgba(120, 140, 180, 255), 0));
        rl.DrawRectangle(0, @intFromFloat(p.y), @intFromFloat(w), @intFromFloat(150 * u), ui.fade(ui.rgba(8, 10, 16, 255), 0.35 * e));
        rl.DrawRectangle(@intFromFloat(p.x + 28 * u), @intFromFloat(p.y + 150 * u), @intFromFloat(p.width - 56 * u), @intFromFloat(@max(1, 1.5 * u)), ui.fade(ui.white, 0.08 * e));

        gunGlyph(p.x + 48 * u, p.y + 44 * u, 17 * u, ui.fade(ui.yellow, e));
        ui.caps(font, "LOADOUT", p.x + 76 * u, p.y + 24 * u, 38 * u, ui.fade(ui.white, e));
        l.drawRarity(font, lay, dy, e);

        for (groups, 0..) |gr, i| {
            const r = shift(tabRect(lay, i), dy);
            const active = i == l.tab;
            const size = 18 * u;
            const tw = ui.width(font, gr.name, size);
            const hot = l.using_mouse and rl.CheckCollisionPointRec(rl.GetMousePosition(), r);

            const chip = rl.Rectangle{ .x = r.x + 3 * u, .y = r.y + 8 * u, .width = r.width - 6 * u, .height = r.height - 14 * u };
            const fit = @min(size, size * (chip.width - 18 * u) / @max(tw, 1));
            const fw = ui.width(font, gr.name, fit);

            rl.DrawRectangleRounded(chip, 0.25, 6, ui.fade(if (active) ui.white else if (hot) ui.rgba(54, 60, 78, 255) else ui.rgba(30, 35, 50, 255), 0.95 * e));
            ui.text(font, gr.name, chip.x + chip.width / 2 - fw / 2, chip.y + chip.height / 2 - fit / 2 - 1 * u, fit, ui.fade(if (active) ui.ink else ui.white, (if (active) @as(f32, 1.0) else 0.8) * e));
        }

        const fi: usize = @intFromFloat(@floor(l.slide));
        const from = shift(tabRect(lay, fi), dy);
        const to = shift(tabRect(lay, @min(groups.len - 1, fi + 1)), dy);
        const k = l.slide - @floor(l.slide);
        const ux = from.x + (to.x - from.x) * k;

        _ = ux;

        const equipped = heldIn(g, l.slot);

        l.drawCarousel(font, icons, lay, list, dy, e, equipped);

        l.drawSlots(font, icons, g, lay, dy, e);
        footer(font, lay, dy, e, pad);
    }

    fn drawRarity(l: *const Loadout, font: rl.Font, lay: Layout, dy: f32, e: f32) void {
        const u = unit();
        const label: [:0]const u8 = "RARITY";
        const ls = 14 * u;
        const first = shift(rarityRect(lay, 0), dy);

        ui.text(font, label, first.x - ui.width(font, label, ls) - 14 * u, first.y + first.height / 2 - ls / 2, ls, ui.fade(ui.white, 0.45 * e));

        for (weapons.rarity_names, 0..) |name, i| {
            const r = shift(rarityRect(lay, i), dy);
            const col = ui.rarity[i];
            const on = i == l.rarity;
            const size = 15 * u;
            const tw = ui.width(font, name, size);

            rl.DrawRectangleRounded(r, 0.5, 10, ui.fade(col, (if (on) @as(f32, 0.95) else 0.14) * e));

            if (on) rl.DrawRectangleRoundedLinesEx(r, 0.5, 10, 2 * u, ui.fade(ui.white, 0.9 * e));

            ui.text(font, name, r.x + r.width / 2 - tw / 2, r.y + r.height / 2 - size / 2 - 1 * u, size, ui.fade(if (on) ui.ink else col, e));
        }
    }

    fn drawCarousel(l: *const Loadout, font: rl.Font, icons: *const icons_mod.Icons, lay: Layout, list: List, dy: f32, e: f32, equipped: ?Held) void {
        const u = unit();
        const car = carouselShift(carousel(lay), dy);

        if (list.len == 0) return;

        const n = list.len;
        const wpn = list.items[l.sel];
        const s = weapons.specs[wpn];
        const col = ui.rarity[l.rarity];
        const cx = car.center.x + car.center.width / 2;
        const cy = car.center.y + car.center.height * 0.55;

        rl.DrawCircleGradient(.{ .x = cx, .y = cy }, car.center.width * 0.46, ui.fade(ui.rgba(150, 170, 210, 255), 0.14 * e), ui.fade(ui.rgba(150, 170, 210, 255), 0));
        rl.DrawEllipse(@intFromFloat(cx), @intFromFloat(car.center.y + car.center.height * 0.93), car.center.width * 0.34, 14 * u, ui.fade(ui.rgba(0, 0, 0, 255), 0.28 * e));

        if (n > 1) {
            const lw = list.items[(l.sel + n - 1) % n];
            const rw = list.items[(l.sel + 1) % n];

            neighbour(font, icons, car.left, lw, l.rarity, e);
            neighbour(font, icons, car.right, rw, l.rarity, e);
            arrow(car.arrow_l, -1, e);
            arrow(car.arrow_r, 1, e);
        }

        const t: f32 = @floatCast(rl.GetTime());
        const yaw = 0.42 + @sin(t * 0.7) * 0.32 + l.spin * 0.6;
        const rim = [3]f32{ @as(f32, @floatFromInt(col.r)) / 255, @as(f32, @floatFromInt(col.g)) / 255, @as(f32, @floatFromInt(col.b)) / 255 };

        icons.renderLive(wpn, yaw, rim);

        const tex = icons.live.texture;
        const src = rl.Rectangle{ .x = 0, .y = 0, .width = @floatFromInt(tex.width), .height = -@as(f32, @floatFromInt(tex.height)) };
        const bob = @sin(t * 1.6) * 4 * u;
        const iw = car.center.width;
        const ih = iw / 2;
        const dst = rl.Rectangle{ .x = car.center.x, .y = cy - ih / 2 + bob - l.spin * 0, .width = iw, .height = ih };

        rl.DrawTexturePro(tex, src, dst, v2(0, 0), 0, ui.fade(ui.white, e));

        var name_buf: [64:0]u8 = @splat(0);
        const nm = std.ascii.upperString(name_buf[0..@min(s.name.len, 63)], s.name[0..@min(s.name.len, 63)]);
        const name: [:0]const u8 = name_buf[0..nm.len :0];
        const ns = 30 * u;
        const nw = ui.capsWidth(font, name, ns);
        const ny = car.center.y - ns * 0.35;

        ui.caps(font, name, cx - nw / 2, ny, ns, ui.fade(ui.white, e));
        diamond(cx + nw / 2 + 18 * u, ny + ns * 0.5, 9 * u, ui.fade(col, e));

        const rname = weapons.rarity_names[l.rarity];
        const rs = 15 * u;

        ui.text(font, rname, cx + nw / 2 + 32 * u, ny + ns * 0.5 - rs / 2, rs, ui.fade(col, e));

        const melee = s.class == .melee;
        const pw = icons_mod.power(s, l.rarity);
        const pmax = icons_mod.power(s, @intCast(weapons.rarity_names.len - 1));
        var pbuf: [16:0]u8 = @splat(0);
        var mbuf: [24:0]u8 = @splat(0);
        const ptxt = std.fmt.bufPrintSentinel(&pbuf, "{d}", .{pw}, 0) catch "";
        const mtxt = std.fmt.bufPrintSentinel(&mbuf, "MAX {d}", .{pmax}, 0) catch "";
        const sy = car.stats.y;
        const px = car.stats.x;
        const pl: [:0]const u8 = "POWER";

        ui.text(font, pl, px, sy, 15 * u, ui.fade(ui.white, 0.75 * e));
        ui.text(font, ptxt, px, sy + 18 * u, 54 * u, ui.fade(ui.white, e));

        const pww = ui.width(font, ptxt, 54 * u);
        const mw = ui.width(font, mtxt, 14 * u) + 16 * u;

        rl.DrawRectangleRounded(.{ .x = px + pww + 10 * u, .y = sy + 50 * u, .width = mw, .height = 22 * u }, 0.4, 6, ui.fade(ui.yellow, e));
        ui.text(font, mtxt, px + pww + 18 * u, sy + 54 * u, 14 * u, ui.fade(ui.ink, e));

        const dmg = s.damage * @as(f32, @floatFromInt(@max(s.pellets, 1))) * weapons.rarity_damage[l.rarity];
        const acc: u32 = @intFromFloat(std.math.clamp((1 - s.spread / 0.11) * 100, 5, 100));
        const rate: u32 = @intFromFloat(@round(60 / @max(s.interval, 0.01)));
        var b1: [16:0]u8 = @splat(0);
        var b2: [16:0]u8 = @splat(0);
        var b3: [16:0]u8 = @splat(0);
        const v1 = if (melee) std.fmt.bufPrintSentinel(&b1, "{d}", .{@as(u32, @intFromFloat(dmg))}, 0) catch "" else std.fmt.bufPrintSentinel(&b1, "{d}", .{acc}, 0) catch "";
        const v2s = if (melee) std.fmt.bufPrintSentinel(&b2, "{d}", .{rate}, 0) catch "" else std.fmt.bufPrintSentinel(&b2, "{d}", .{@as(u32, @intFromFloat(s.range))}, 0) catch "";
        const v3 = if (melee) std.fmt.bufPrintSentinel(&b3, "{d}", .{@as(u32, @intFromFloat(s.range * 10))}, 0) catch "" else std.fmt.bufPrintSentinel(&b3, "{d}", .{s.mag}, 0) catch "";
        const labels = if (melee) [3][:0]const u8{ "DAMAGE", "SPEED", "REACH" } else [3][:0]const u8{ "ACCURACY", "RANGE", "MAGAZINE" };
        const vals = [3][:0]const u8{ v1, v2s, v3 };
        const colw = (car.stats.width - 250 * u) / 3;

        for (0..3) |k| {
            const x = car.stats.x + 250 * u + colw * @as(f32, @floatFromInt(k));

            ui.text(font, labels[k], x, sy + 6 * u, 13 * u, ui.fade(ui.white, 0.6 * e));
            ui.text(font, vals[k], x, sy + 26 * u, 34 * u, ui.fade(ui.white, e));
        }

        const on = equipped != null and equipped.?.weapon == wpn and @intFromEnum(equipped.?.rarity) == l.rarity;
        const eb = car.equip;
        const hot = l.using_mouse and rl.CheckCollisionPointRec(rl.GetMousePosition(), eb);
        const fill = if (on) ui.rgba(46, 52, 68, 255) else if (hot) ui.rgba(255, 216, 120, 255) else ui.accent;
        const label: [:0]const u8 = if (on) "ACTIVE" else "EQUIP";
        const ls = 30 * u;

        rl.DrawRectangleRounded(eb, 0.2, 8, ui.fade(fill, e));
        ui.caps(font, label, eb.x + eb.width / 2 - ui.capsWidth(font, label, ls) / 2, eb.y + eb.height / 2 - ls / 2 - 2 * u, ls, ui.fade(if (on) ui.rgba(170, 176, 190, 255) else ui.ink, e));

        var cbuf: [24:0]u8 = @splat(0);
        const ctxt = std.fmt.bufPrintSentinel(&cbuf, "{d} / {d}", .{ l.sel + 1, n }, 0) catch "";
        const cs = 14 * u;

        ui.text(font, ctxt, cx - ui.width(font, ctxt, cs) / 2, eb.y - cs - 10 * u, cs, ui.fade(ui.white, 0.45 * e));
    }

    fn drawSlots(l: *const Loadout, font: rl.Font, icons: *const icons_mod.Icons, g: *const Game, lay: Layout, dy: f32, e: f32) void {
        const u = unit();
        const title: [:0]const u8 = "SLOTS";
        const ts = 14 * u;
        const first = shift(slotRect(lay, 0), dy);

        ui.text(font, title, first.x, first.y - ts - 10 * u, ts, ui.fade(ui.white, 0.45 * e));

        for (0..slot_count) |i| {
            const r = shift(slotRect(lay, i), dy);
            const gl = l.slot_glow[i];
            const held = heldIn(g, @intCast(i));
            var buf: [8]u8 = undefined;
            const key = std.fmt.bufPrintSentinel(&buf, "{d}", .{i + 1}, 0) catch "";
            const pop = if (l.flash > 0 and l.flash_slot == i) l.flash else 0;
            const grow = pop * 6 * u;
            const box = rl.Rectangle{ .x = r.x - grow, .y = r.y - grow, .width = r.width + grow * 2, .height = r.height + grow * 2 };

            rl.DrawRectangleRounded(box, 0.12, 10, ui.fade(ui.rgba(22, 26, 38, 255), e));
            rl.DrawRectangleRoundedLinesEx(box, 0.12, 10, 1, ui.fade(ui.edge, e));

            if (gl > 0.01) rl.DrawRectangleRoundedLinesEx(box, 0.12, 10, 2 * u, ui.fade(ui.white, 0.85 * gl * e));

            if (pop > 0) rl.DrawRectangleRounded(box, 0.2, 10, ui.fade(ui.white, pop * 0.25 * e));

            ui.text(font, key, box.x + 10 * u, box.y + 7 * u, 14 * u, ui.fade(ui.white, (0.4 + gl * 0.5) * e));

            if (i == game_mod.knife_slot) {
                const ms = 11 * u;
                const mt: [:0]const u8 = "MELEE";

                ui.text(font, mt, box.x + box.width - ui.width(font, mt, ms) - 10 * u, box.y + 9 * u, ms, ui.fade(ui.white, 0.35 * e));
            }

            const hd = held orelse {
                const em: [:0]const u8 = "Empty";
                const es = 14 * u;

                ui.text(font, em, box.x + box.width / 2 - ui.width(font, em, es) / 2, box.y + box.height / 2 - es / 2, es, ui.fade(ui.white, 0.25 * e));

                continue;
            };
            const tex = icons.tex[hd.weapon].texture;
            const pad = 10 * u;
            const ih = box.height - pad * 2 - 14 * u;
            const iw = @min(box.width - pad * 2, ih * 2);
            const dst = rl.Rectangle{ .x = box.x + box.width / 2 - iw / 2, .y = box.y + pad + 6 * u, .width = iw, .height = iw / 2 };
            const src = rl.Rectangle{ .x = 0, .y = 0, .width = @floatFromInt(tex.width), .height = -@as(f32, @floatFromInt(tex.height)) };

            rl.DrawTexturePro(tex, src, dst, v2(0, 0), 0, ui.fade(ui.white, (0.6 + gl * 0.4) * e));
            rl.DrawRectangleRounded(.{ .x = box.x + 10 * u, .y = box.y + box.height - 8 * u, .width = box.width - 20 * u, .height = 3 * u }, 1, 6, ui.fade(ui.rarity[@intFromEnum(hd.rarity)], e));

            const ns = 12 * u;
            const name = weapons.specs[hd.weapon].name;

            ui.text(font, name, box.x + box.width / 2 - ui.width(font, name, ns) / 2, box.y + box.height - 24 * u, ns, ui.fade(ui.white, (0.55 + gl * 0.45) * e));
        }
    }
};

fn heldIn(g: *const Game, slot: u8) ?Held {
    if (slot == game_mod.knife_slot) return g.arsenal.blade;

    return g.arsenal.slots[slot];
}

const Stat = struct {
    label: [:0]const u8,
    value: f32,
};

const Stats = struct {
    items: [4]Stat = undefined,
    len: usize = 0,
};

fn statsFor(s: weapons.Spec, rarity: u8) Stats {
    var out: Stats = .{};
    const dmg = s.damage * @as(f32, @floatFromInt(@max(s.pellets, 1))) * weapons.rarity_damage[rarity];
    const rate = 1 / @max(s.interval, 0.01);

    if (s.class == .melee) {
        out.items[0] = .{ .label = "DMG", .value = std.math.clamp(dmg / 120, 0.04, 1) };
        out.items[1] = .{ .label = "SPEED", .value = std.math.clamp(rate / 3, 0.04, 1) };
        out.items[2] = .{ .label = "REACH", .value = std.math.clamp(s.range / 4, 0.04, 1) };
        out.len = 3;

        return out;
    }

    out.items[0] = .{ .label = "DMG", .value = std.math.clamp(@sqrt(dmg / 160), 0.06, 1) };
    out.items[1] = .{ .label = "RATE", .value = std.math.clamp(@sqrt(rate / 20), 0.06, 1) };
    out.items[2] = .{ .label = "ACC", .value = std.math.clamp(1 - s.spread / 0.11, 0.06, 1) };
    out.items[3] = .{ .label = "MAG", .value = std.math.clamp(@sqrt(@as(f32, @floatFromInt(s.mag)) / 120), 0.06, 1) };
    out.len = 4;

    return out;
}

fn footer(font: rl.Font, lay: Layout, dy: f32, e: f32, pad: bool) void {
    const u = unit();
    const b = shift(lay.back, dy);
    const hint: [:0]const u8 = if (pad) "LB/RB class   LT/RT slot   A equip   X rarity   B back" else "Q/E class   1-5 slot   Enter or click equip   R rarity   Esc back";
    const hs = 14 * u;
    const bs = 19 * u;
    const label: [:0]const u8 = "Done";
    const hot = rl.CheckCollisionPointRec(rl.GetMousePosition(), b);

    ui.text(font, hint, lay.panel.x + 30 * u, b.y + b.height / 2 - hs / 2, hs, ui.fade(ui.white, 0.4 * e));
    rl.DrawRectangleRounded(b, 0.5, 10, ui.fade(if (hot) ui.white else ui.yellow, e));
    ui.text(font, label, b.x + b.width / 2 - ui.width(font, label, bs) / 2, b.y + b.height / 2 - bs / 2 - 1 * u, bs, ui.fade(ui.ink, e));
}

fn gunGlyph(x: f32, y: f32, r: f32, col: rl.Color) void {
    rl.DrawRectangleRounded(.{ .x = x - r * 1.2, .y = y - r * 0.45, .width = r * 2.4, .height = r * 0.55 }, 0.4, 6, col);
    rl.DrawRectangleRounded(.{ .x = x - r * 0.95, .y = y - r * 0.1, .width = r * 0.5, .height = r * 0.95 }, 0.4, 6, col);
    rl.DrawRectangleRounded(.{ .x = x + r * 0.2, .y = y - r * 0.05, .width = r * 0.35, .height = r * 0.7 }, 0.3, 6, col);
    rl.DrawRectangle(@intFromFloat(x + r * 1.1), @intFromFloat(y - r * 0.35), @intFromFloat(r * 0.5), @intFromFloat(@max(1, r * 0.2)), col);
}

const Layout = struct {
    panel: rl.Rectangle,
    cards: rl.Rectangle,
    slots: rl.Rectangle,
    back: rl.Rectangle,
};

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

fn layout() Layout {
    const w: f32 = @floatFromInt(rl.GetScreenWidth());
    const h: f32 = @floatFromInt(rl.GetScreenHeight());
    const u = unit();
    const pw = @min(1320 * u, w - 40 * u);
    const ph = @min(860 * u, h - 40 * u);
    const px = (w - pw) / 2;
    const py = (h - ph) / 2;
    const foot = 66 * u;
    const slots_h = 112 * u;
    const top = py + 168 * u;
    const slots_y = py + ph - foot - slots_h - 14 * u;

    return .{
        .panel = .{ .x = px, .y = py, .width = pw, .height = ph },
        .cards = .{ .x = px + 28 * u, .y = top, .width = pw - 56 * u, .height = slots_y - 40 * u - top },
        .slots = .{ .x = px + 28 * u, .y = slots_y, .width = pw - 56 * u, .height = slots_h },
        .back = .{ .x = px + pw - 28 * u - 150 * u, .y = py + ph - foot + 8 * u, .width = 150 * u, .height = 44 * u },
    };
}

fn tabRect(lay: Layout, i: usize) rl.Rectangle {
    const u = unit();
    const x0 = lay.panel.x + 20 * u;
    const tw = (lay.panel.width - 40 * u) / @as(f32, groups.len);

    return .{ .x = x0 + tw * @as(f32, @floatFromInt(i)), .y = lay.panel.y + 96 * u, .width = tw, .height = 50 * u };
}

fn rarityRect(lay: Layout, i: usize) rl.Rectangle {
    const u = unit();
    const cw = 108 * u;
    const gap = 8 * u;
    const n: f32 = @floatFromInt(weapons.rarity_names.len);
    const x0 = lay.panel.x + lay.panel.width - 28 * u - (cw * n + gap * (n - 1));

    return .{ .x = x0 + (cw + gap) * @as(f32, @floatFromInt(i)), .y = lay.panel.y + 28 * u, .width = cw, .height = 34 * u };
}

const Carousel = struct {
    center: rl.Rectangle,
    left: rl.Rectangle,
    right: rl.Rectangle,
    arrow_l: rl.Rectangle,
    arrow_r: rl.Rectangle,
    stats: rl.Rectangle,
    equip: rl.Rectangle,
};

fn carousel(lay: Layout) Carousel {
    const u = unit();
    const c = lay.cards;
    const cw = c.width * 0.52;
    const ch = c.height * 0.6;
    const side_w = c.width * 0.2;
    const side_h = ch * 0.6;
    const mid_y = c.y + ch * 0.55;
    const eq_w = 300 * u;
    const eq_h = 60 * u;

    return .{
        .center = .{ .x = c.x + c.width / 2 - cw / 2, .y = c.y, .width = cw, .height = ch },
        .left = .{ .x = c.x + 40 * u, .y = mid_y - side_h / 2, .width = side_w, .height = side_h },
        .right = .{ .x = c.x + c.width - 40 * u - side_w, .y = mid_y - side_h / 2, .width = side_w, .height = side_h },
        .arrow_l = .{ .x = c.x - 6 * u, .y = mid_y - 30 * u, .width = 40 * u, .height = 60 * u },
        .arrow_r = .{ .x = c.x + c.width - 34 * u, .y = mid_y - 30 * u, .width = 40 * u, .height = 60 * u },
        .stats = .{ .x = c.x + c.width / 2 - 360 * u, .y = c.y + ch + 6 * u, .width = 720 * u, .height = 90 * u },
        .equip = .{ .x = c.x + c.width / 2 - eq_w / 2, .y = c.y + c.height - eq_h, .width = eq_w, .height = eq_h },
    };
}

fn carouselShift(c: Carousel, dy: f32) Carousel {
    return .{ .center = shift(c.center, dy), .left = shift(c.left, dy), .right = shift(c.right, dy), .arrow_l = shift(c.arrow_l, dy), .arrow_r = shift(c.arrow_r, dy), .stats = shift(c.stats, dy), .equip = shift(c.equip, dy) };
}

fn neighbour(font: rl.Font, icons: *const icons_mod.Icons, r: rl.Rectangle, w: u8, rarity: u8, e: f32) void {
    const u = unit();
    const tex = icons.tex[w].texture;
    const src = rl.Rectangle{ .x = 0, .y = 0, .width = @floatFromInt(tex.width), .height = -@as(f32, @floatFromInt(tex.height)) };
    const iw = r.width;
    const dst = rl.Rectangle{ .x = r.x, .y = r.y + r.height / 2 - iw / 4, .width = iw, .height = iw / 2 };
    const hot = rl.CheckCollisionPointRec(rl.GetMousePosition(), r);
    const s = weapons.specs[w];
    var name_buf: [64:0]u8 = @splat(0);
    const nm = std.ascii.upperString(name_buf[0..@min(s.name.len, 63)], s.name[0..@min(s.name.len, 63)]);
    const name: [:0]const u8 = name_buf[0..nm.len :0];
    const ns = 20 * u;
    var pbuf: [16:0]u8 = @splat(0);
    const ptxt = std.fmt.bufPrintSentinel(&pbuf, "{d}", .{icons_mod.power(s, rarity)}, 0) catch "";

    rl.DrawTexturePro(tex, src, dst, v2(0, 0), 0, ui.fade(ui.white, (if (hot) @as(f32, 0.85) else 0.55) * e));
    ui.text(font, name, r.x + r.width / 2 - ui.width(font, name, ns) / 2, r.y - ns, ns, ui.fade(ui.white, 0.7 * e));
    ui.text(font, "POWER", r.x + r.width / 2 - ui.width(font, "POWER", 12 * u) / 2, r.y + r.height + 4 * u, 12 * u, ui.fade(ui.white, 0.5 * e));
    ui.text(font, ptxt, r.x + r.width / 2 - ui.width(font, ptxt, 28 * u) / 2, r.y + r.height + 20 * u, 28 * u, ui.fade(ui.white, 0.8 * e));
}

fn arrow(r: rl.Rectangle, dir: f32, e: f32) void {
    const hot = rl.CheckCollisionPointRec(rl.GetMousePosition(), r);
    const cx = r.x + r.width / 2;
    const cy = r.y + r.height / 2;
    const k = r.width * 0.32;
    const col = ui.fade(ui.white, (if (hot) @as(f32, 0.95) else 0.5) * e);

    if (dir < 0) {
        rl.DrawTriangle(v2(cx + k, cy - k * 1.4), v2(cx - k, cy), v2(cx + k, cy + k * 1.4), col);
    } else {
        rl.DrawTriangle(v2(cx - k, cy - k * 1.4), v2(cx - k, cy + k * 1.4), v2(cx + k, cy), col);
    }
}

fn diamond(x: f32, y: f32, r: f32, col: rl.Color) void {
    rl.DrawTriangle(v2(x, y - r), v2(x - r, y), v2(x + r, y), col);
    rl.DrawTriangle(v2(x - r, y), v2(x, y + r), v2(x + r, y), col);
}

fn slanted(r: rl.Rectangle, k: f32, col: rl.Color) void {
    const a = v2(r.x + k, r.y);
    const b = v2(r.x + r.width, r.y);
    const c = v2(r.x + r.width - k, r.y + r.height);
    const d = v2(r.x, r.y + r.height);

    rl.DrawTriangle(a, d, c, col);
    rl.DrawTriangle(a, c, b, col);
}

fn slotRect(lay: Layout, i: usize) rl.Rectangle {
    const u = unit();
    const gap = 14 * u;
    const n: f32 = @floatFromInt(slot_count);
    const sw = (lay.slots.width - gap * (n - 1)) / n;

    return .{ .x = lay.slots.x + (sw + gap) * @as(f32, @floatFromInt(i)), .y = lay.slots.y, .width = sw, .height = lay.slots.height };
}

pub fn buttonRect() rl.Rectangle {
    const w: f32 = @floatFromInt(rl.GetScreenWidth());
    const h: f32 = @floatFromInt(rl.GetScreenHeight());
    const u = unit();
    const bw = 250 * u;

    return .{ .x = w / 2 - bw / 2, .y = h / 2 + 175 * u + 66 * u, .width = bw, .height = 54 * u };
}
