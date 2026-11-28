const std = @import("std");
const rl = @import("raylib");
const shared = @import("shared");
const ui = @import("ui.zig");
const theme = @import("theme.zig");
const menu = @import("menu.zig");
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
                l.rarity = @backingInt(held.rarity);

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
        const held = Held.fresh(w, @fromBackingInt(@intCast(l.rarity)));
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

    pub fn drawButton(l: *const Loadout, pad: bool, hidden: f32) void {
        if (l.t > 0.99 or hidden > 0.99) return;

        menu.pauseButton(0, buttonRect(), .blaster, "LOADOUT", if (pad) "LB" else "L", theme.tones.sun_tone, 1 - (1 - l.t) * (1 - hidden));
    }

    pub fn draw(l: *const Loadout, icons: *const icons_mod.Icons, g: *const Game, pad: bool) void {
        if (l.t <= 0.001) return;

        const w: f32 = @floatFromInt(rl.GetScreenWidth());
        const h: f32 = @floatFromInt(rl.GetScreenHeight());
        const u = unit();
        const e = ease(l.t);
        const lay = layout();
        const dy = (1 - e) * 28 * u;
        const title = shift(lay.title, dy);
        const list = listFor(l.tab);
        const mid = title.y + title.height / 2;

        rl.DrawRectangle(0, 0, @intFromFloat(w), @intFromFloat(h), theme.fade(theme.navy, e));
        theme.round(shift(lay.stage, dy), 32 * u, theme.fade(theme.night, 0.5 * e));
        theme.dot(title.x + 30 * u, mid, 30 * u, theme.fade(theme.sun, e));
        theme.icon(.blaster, title.x + 30 * u, mid, 42 * u, theme.fade(theme.navy, e));
        theme.extruded(theme.heavy, "LOADOUT", title.x + 76 * u, mid, 60 * u, theme.cream, e);
        l.drawRarity(lay, dy, e);

        const bar = shift(.{ .x = tabRect(lay, 0).x, .y = tabRect(lay, 0).y, .width = tabRect(lay, 0).width * groups.len, .height = tabRect(lay, 0).height }, dy);

        theme.round(bar, 22 * u, theme.fade(theme.night, 0.75 * e));

        for (groups, 0..) |gr, i| {
            const r = shift(tabRect(lay, i), dy);
            const active = i == l.tab;
            const hot = l.using_mouse and rl.CheckCollisionPointRec(rl.GetMousePosition(), r);
            const chip = theme.grow(r, -6 * u);
            const fit = theme.fit(theme.heavy, gr.name, 30 * u, chip.width - 14 * u);

            if (active) theme.round(chip, 17 * u, theme.fade(theme.sun, e)) else if (hot) theme.round(chip, 17 * u, theme.fade(theme.cream, 0.12 * e));

            theme.center(theme.heavy, gr.name, chip.x + chip.width / 2, chip.y + chip.height / 2, fit, theme.fade(if (active) theme.navy else theme.cream, (if (active or hot) @as(f32, 1) else 0.8) * e));
        }

        const equipped = heldIn(g, l.slot);

        l.drawCarousel(icons, lay, list, dy, e, equipped);

        l.drawSlots(icons, g, lay, dy, e);
        footer(lay, dy, e, pad);
    }

    fn drawRarity(l: *const Loadout, lay: Layout, dy: f32, e: f32) void {
        const u = unit();
        const label: [:0]const u8 = "RARITY";
        const ls = 24 * u;
        const first = shift(rarityRect(lay, 0), dy);

        theme.write(theme.heavy, label, first.x - theme.measure(theme.heavy, label, ls) - 16 * u, first.y + first.height / 2, ls, theme.fade(theme.cream, 0.6 * e));

        for (weapons.rarity_names, 0..) |name, i| {
            const r = shift(rarityRect(lay, i), dy);
            const col = ui.rarity[i];
            const on = i == l.rarity;
            const size = theme.fit(theme.heavy, name, 25 * u, r.width - 14 * u);

            if (on) theme.round(theme.grow(r, 5 * u), 19 * u, theme.fade(theme.cream, e));

            theme.round(r, 15 * u, theme.fade(if (on) col else theme.night, (if (on) @as(f32, 1) else 0.75) * e));
            theme.center(theme.heavy, name, r.x + r.width / 2, r.y + r.height / 2, size, theme.fade(if (on) theme.navy else col, e));
        }
    }

    fn drawCarousel(l: *const Loadout, icons: *const icons_mod.Icons, lay: Layout, list: List, dy: f32, e: f32, equipped: ?Held) void {
        const u = unit();
        const car = carouselShift(carousel(lay), dy);

        if (list.len == 0) return;

        const n = list.len;
        const wpn = list.items[l.sel];
        const s = weapons.specs[wpn];
        const col = ui.rarity[l.rarity];
        const cx = car.center.x + car.center.width / 2;
        const cy = car.center.y + car.center.height * 0.57;

        theme.dot(cx, cy, @min(car.center.height * 0.43, car.center.width * 0.34), theme.fade(theme.slate, 0.55 * e));
        rl.DrawEllipse(@intFromFloat(cx), @intFromFloat(car.center.y + car.center.height * 0.93), car.center.width * 0.3, 14 * u, theme.fade(theme.night, 0.5 * e));

        if (n > 1) {
            const lw = list.items[(l.sel + n - 1) % n];
            const rw = list.items[(l.sel + 1) % n];

            neighbour(icons, car.left, lw, l.rarity, e);
            neighbour(icons, car.right, rw, l.rarity, e);
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
        const iw = @min(car.center.width, car.center.height * 2.1);
        const ih = iw / 2;
        const dst = rl.Rectangle{ .x = cx - iw / 2, .y = cy - ih / 2 + bob, .width = iw, .height = ih };

        rl.DrawTexturePro(tex, src, dst, v2(0, 0), 0, ui.fade(ui.white, e));

        var name_buf: [64:0]u8 = @splat(0);
        const nm = std.ascii.upperString(name_buf[0..@min(s.name.len, 63)], s.name[0..@min(s.name.len, 63)]);
        const name: [:0]const u8 = name_buf[0..nm.len :0];
        const ns = 50 * u;
        const rname = weapons.rarity_names[l.rarity];
        const rs = 26 * u;
        const nw = theme.measure(theme.heavy, name, ns);
        const rw = theme.measure(theme.heavy, rname, rs) + 28 * u;
        const ny = car.center.y + 30 * u;
        const nx = cx - (nw + 16 * u + rw) / 2;
        const chip: rl.Rectangle = .{ .x = nx + nw + 16 * u, .y = ny - 19 * u, .width = rw, .height = 38 * u };

        theme.extruded(theme.heavy, name, nx, ny, ns, theme.cream, e);
        theme.round(chip, 12 * u, theme.fade(col, e));
        theme.center(theme.heavy, rname, chip.x + rw / 2, ny, rs, theme.fade(theme.navy, e));

        const melee = s.class == .melee;
        const pw = icons_mod.power(s, l.rarity);
        const pmax = icons_mod.power(s, @intCast(weapons.rarity_names.len - 1));
        var pbuf: [16:0]u8 = @splat(0);
        var mbuf: [24:0]u8 = @splat(0);
        const ptxt = std.fmt.bufPrintSentinel(&pbuf, "{d}", .{pw}, 0) catch "";
        const mtxt = std.fmt.bufPrintSentinel(&mbuf, "MAX {d}", .{pmax}, 0) catch "";
        const sy = car.stats.y;
        const px = car.stats.x;
        const card: rl.Rectangle = .{ .x = px, .y = sy, .width = car.stats.width, .height = car.stats.height };

        theme.panel(card, 22 * u, theme.cream, e);
        theme.write(theme.body, "POWER", px + 24 * u, sy + 22 * u, 24 * u, theme.fade(theme.soft, e));
        theme.write(theme.heavy, ptxt, px + 24 * u, sy + 60 * u, 52 * u, theme.fade(theme.navy, e));

        const pww = theme.measure(theme.heavy, ptxt, 52 * u);
        const mw = theme.measure(theme.heavy, mtxt, 22 * u) + 18 * u;
        const max_chip: rl.Rectangle = .{ .x = px + 34 * u + pww, .y = sy + 46 * u, .width = mw, .height = 30 * u };

        theme.round(max_chip, 9 * u, theme.fade(theme.sun, e));
        theme.center(theme.heavy, mtxt, max_chip.x + mw / 2, max_chip.y + 15 * u, 22 * u, theme.fade(theme.navy, e));

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
        const start = @max(250 * u, pww + mw + 70 * u);
        const colw = (car.stats.width - start) / 3;

        for (0..3) |k| {
            const x = px + start + colw * @as(f32, @floatFromInt(k));

            theme.write(theme.body, labels[k], x, sy + 22 * u, theme.fit(theme.body, labels[k], 24 * u, colw - 8 * u), theme.fade(theme.soft, e));
            theme.write(theme.heavy, vals[k], x, sy + 60 * u, 46 * u, theme.fade(theme.navy, e));
        }

        const on = equipped != null and equipped.?.weapon == wpn and @backingInt(equipped.?.rarity) == l.rarity;
        const eb = car.equip;
        const hot = l.using_mouse and rl.CheckCollisionPointRec(rl.GetMousePosition(), eb);
        const tone = if (on) theme.tones.navy_tone else theme.tones.coral_tone;
        const face = theme.button(theme.tag("equip", 0), eb, 24 * u, tone, hot and !on, .{ .a = e }).face;
        const label: [:0]const u8 = if (on) "ACTIVE" else "EQUIP";
        const ls = 48 * u;
        const lw = theme.measure(theme.heavy, label, ls);
        const lx = face.x + face.width / 2 - (lw + (if (on) 52 * u else 0)) / 2;
        const lm = face.y + face.height / 2;

        if (on) theme.icon(.check, lx + 18 * u, lm, 40 * u, theme.fade(theme.sun, e));

        theme.write(theme.heavy, label, lx + (if (on) 52 * u else 0), lm, ls, theme.fade(tone.ink, e));

        var cbuf: [24:0]u8 = @splat(0);
        const ctxt = std.fmt.bufPrintSentinel(&cbuf, "{d} / {d}", .{ l.sel + 1, n }, 0) catch "";

        theme.write(theme.body, ctxt, lay.stage.x + 24 * u, lay.stage.y + 30 * u + dy, 26 * u, theme.fade(theme.cream, 0.6 * e));
    }

    fn drawSlots(l: *const Loadout, icons: *const icons_mod.Icons, g: *const Game, lay: Layout, dy: f32, e: f32) void {
        const u = unit();
        const title: [:0]const u8 = "SLOTS";
        const first = shift(slotRect(lay, 0), dy);

        theme.write(theme.heavy, title, first.x, first.y - 22 * u, 24 * u, theme.fade(theme.cream, 0.6 * e));

        for (0..slot_count) |i| {
            const r = shift(slotRect(lay, i), dy);
            const gl = l.slot_glow[i];
            const held = heldIn(g, @intCast(i));
            var buf: [8]u8 = undefined;
            const key = std.fmt.bufPrintSentinel(&buf, "{d}", .{i + 1}, 0) catch "";
            const pop = if (l.flash > 0 and l.flash_slot == i) l.flash else 0;
            const box = theme.grow(r, pop * 6 * u);

            if (gl > 0.01) theme.round(theme.grow(box, 5 * u * gl), 23 * u, theme.fade(theme.sun, gl * e));

            theme.round(theme.offset(box, 0, 6 * u), 18 * u, theme.fade(theme.night, e));
            theme.round(box, 18 * u, theme.fade(theme.slate, e));

            if (pop > 0) theme.round(box, 18 * u, theme.fade(theme.cream, pop * 0.3 * e));

            theme.write(theme.heavy, key, box.x + 14 * u, box.y + 18 * u, 24 * u, theme.fade(theme.cream, (0.55 + gl * 0.45) * e));

            if (i == game_mod.knife_slot) {
                const mt: [:0]const u8 = "MELEE";

                theme.write(theme.body, mt, box.x + box.width - theme.measure(theme.body, mt, 18 * u) - 12 * u, box.y + 18 * u, 18 * u, theme.fade(theme.cream, 0.5 * e));
            }

            const hd = held orelse {
                theme.center(theme.body, "Empty", box.x + box.width / 2, box.y + box.height / 2, 24 * u, theme.fade(theme.cream, 0.4 * e));

                continue;
            };
            const tex = icons.tex[hd.weapon].texture;
            const pad = 10 * u;
            const ih = box.height - pad * 2 - 18 * u;
            const iw = @min(box.width - pad * 2, ih * 2);
            const dst = rl.Rectangle{ .x = box.x + box.width / 2 - iw / 2, .y = box.y + pad + 4 * u, .width = iw, .height = iw / 2 };
            const src = rl.Rectangle{ .x = 0, .y = 0, .width = @floatFromInt(tex.width), .height = -@as(f32, @floatFromInt(tex.height)) };

            rl.DrawTexturePro(tex, src, dst, v2(0, 0), 0, ui.fade(ui.white, (0.7 + gl * 0.3) * e));
            theme.round(.{ .x = box.x + 14 * u, .y = box.y + box.height - 10 * u, .width = box.width - 28 * u, .height = 5 * u }, 2.5 * u, theme.fade(ui.rarity[@backingInt(hd.rarity)], e));

            const name = weapons.specs[hd.weapon].name;
            var name_z: [48]u8 = undefined;
            const text = std.fmt.bufPrintSentinel(&name_z, "{s}", .{name}, 0) catch "";

            theme.center(theme.body, text, box.x + box.width / 2, box.y + box.height - 26 * u, theme.fit(theme.body, text, 20 * u, box.width - 16 * u), theme.fade(theme.cream, (0.7 + gl * 0.3) * e));
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

fn footer(lay: Layout, dy: f32, e: f32, pad: bool) void {
    const u = unit();
    const b = shift(lay.back, dy);
    const hint: [:0]const u8 = if (pad) "LB / RB class   LT / RT slot   A equip   X rarity   B back" else "Q / E class   1-5 slot   Enter or click equip   R rarity   Esc back";
    const hot = rl.CheckCollisionPointRec(rl.GetMousePosition(), b);
    const face = theme.button(theme.tag("loadout-done", 0), b, 20 * u, theme.tones.sun_tone, hot, .{ .a = e }).face;

    theme.center(theme.heavy, "DONE", face.x + face.width / 2, face.y + face.height / 2, 40 * u, theme.fade(theme.navy, e));

    if (!theme.view().touch or pad) theme.write(theme.body, hint, lay.panel.x + 30 * u, b.y + b.height / 2, 24 * u, theme.fade(theme.cream, 0.65 * e));
}

const Layout = struct {
    panel: rl.Rectangle,
    title: rl.Rectangle,
    tabs: rl.Rectangle,
    stage: rl.Rectangle,
    cards: rl.Rectangle,
    slots: rl.Rectangle,
    back: rl.Rectangle,
    rarity_h: f32,
    touch: bool,
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
    const v = theme.view();
    const least: f32 = if (v.touch) 9.2 * v.mm else 0;
    const pw = @min(1380 * u, w - (v.left + w - v.right) + 20 * u);
    const ph = @min(880 * u, h - 24 * u);
    const px = (w - pw) / 2;
    const py = (h - ph) / 2;
    const inner = pw - 40 * u;
    const head_h = @max(66 * u, least);
    const title: rl.Rectangle = .{ .x = px + 20 * u, .y = py + 8 * u, .width = 340 * u, .height = head_h };
    const tabs: rl.Rectangle = .{ .x = px + 20 * u, .y = title.y + head_h + 14 * u, .width = inner, .height = @max(62 * u, least) };
    const foot: f32 = if (v.touch) 0 else 72 * u;
    const slots_h = @max(116 * u, least);
    const slots_y = py + ph - foot - slots_h - 10 * u;
    const done_w: f32 = if (v.touch) 200 * u else 0;
    const slots: rl.Rectangle = .{ .x = px + 20 * u, .y = slots_y, .width = inner - (if (v.touch) done_w + 20 * u else 0), .height = slots_h };
    const stage_y = tabs.y + tabs.height + 14 * u;
    const stage: rl.Rectangle = .{ .x = px + 20 * u, .y = stage_y, .width = inner, .height = slots_y - 48 * u - stage_y };

    return .{
        .panel = .{ .x = px, .y = py, .width = pw, .height = ph },
        .title = title,
        .tabs = tabs,
        .stage = stage,
        .cards = theme.grow(stage, -12 * u),
        .slots = slots,
        .back = if (v.touch)
            .{ .x = px + pw - 20 * u - done_w, .y = slots_y, .width = done_w, .height = slots_h }
        else
            .{ .x = px + pw - 20 * u - 190 * u, .y = py + ph - foot + 6 * u, .width = 190 * u, .height = 56 * u },
        .rarity_h = @max(44 * u, least),
        .touch = v.touch,
    };
}

fn tabRect(lay: Layout, i: usize) rl.Rectangle {
    const tw = lay.tabs.width / @as(f32, groups.len);

    return .{ .x = lay.tabs.x + tw * @as(f32, @floatFromInt(i)), .y = lay.tabs.y, .width = tw, .height = lay.tabs.height };
}

fn rarityRect(lay: Layout, i: usize) rl.Rectangle {
    const u = unit();
    const cw = 124 * u;
    const gap = 12 * u;
    const n: f32 = @floatFromInt(weapons.rarity_names.len);
    const x0 = lay.panel.x + lay.panel.width - 24 * u - (cw * n + gap * (n - 1));

    return .{ .x = x0 + (cw + gap) * @as(f32, @floatFromInt(i)), .y = lay.title.y + (lay.title.height - lay.rarity_h) / 2, .width = cw, .height = lay.rarity_h };
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
    const eq_w = 300 * u;
    const eq_h = if (lay.touch) @max(104 * u, 9.2 * theme.view().mm) else 104 * u;
    const row_y = c.y + c.height - eq_h;
    const ch = c.height - eq_h - 16 * u;
    const cw = c.width * 0.52;
    const side_w = c.width * 0.18;
    const side_h = ch * 0.5;
    const mid_y = c.y + ch * 0.57;
    const arrow_s = @max(72 * u, if (lay.touch) 9.2 * theme.view().mm else 0);
    const stats_w = @min(820 * u, c.width - eq_w - 24 * u);
    const row_x = c.x + (c.width - stats_w - eq_w - 24 * u) / 2;

    return .{
        .center = .{ .x = c.x + c.width / 2 - cw / 2, .y = c.y, .width = cw, .height = ch },
        .left = .{ .x = c.x + arrow_s + 24 * u, .y = mid_y - side_h / 2, .width = side_w, .height = side_h },
        .right = .{ .x = c.x + c.width - arrow_s - 24 * u - side_w, .y = mid_y - side_h / 2, .width = side_w, .height = side_h },
        .arrow_l = .{ .x = c.x + 6 * u, .y = mid_y - arrow_s / 2, .width = arrow_s, .height = arrow_s },
        .arrow_r = .{ .x = c.x + c.width - arrow_s - 6 * u, .y = mid_y - arrow_s / 2, .width = arrow_s, .height = arrow_s },
        .stats = .{ .x = row_x, .y = row_y + (eq_h - 94 * u) / 2, .width = stats_w, .height = 94 * u },
        .equip = .{ .x = row_x + stats_w + 24 * u, .y = row_y, .width = eq_w, .height = eq_h - 8 * u },
    };
}

fn carouselShift(c: Carousel, dy: f32) Carousel {
    return .{ .center = shift(c.center, dy), .left = shift(c.left, dy), .right = shift(c.right, dy), .arrow_l = shift(c.arrow_l, dy), .arrow_r = shift(c.arrow_r, dy), .stats = shift(c.stats, dy), .equip = shift(c.equip, dy) };
}

fn neighbour(icons: *const icons_mod.Icons, r: rl.Rectangle, w: u8, rarity: u8, e: f32) void {
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
    var pbuf: [32:0]u8 = @splat(0);
    const ptxt = std.fmt.bufPrintSentinel(&pbuf, "POWER {d}", .{icons_mod.power(s, rarity)}, 0) catch "";
    const cx = r.x + r.width / 2;

    rl.DrawTexturePro(tex, src, dst, v2(0, 0), 0, ui.fade(ui.white, (if (hot) @as(f32, 0.9) else 0.6) * e));
    theme.center(theme.heavy, name, cx, dst.y - 12 * u, theme.fit(theme.heavy, name, 30 * u, r.width), theme.fade(theme.cream, 0.85 * e));
    theme.center(theme.body, ptxt, cx, dst.y + dst.height + 16 * u, 24 * u, theme.fade(theme.cream, 0.65 * e));
}

fn arrow(r: rl.Rectangle, dir: f32, e: f32) void {
    const u = unit();
    const hot = rl.CheckCollisionPointRec(rl.GetMousePosition(), r);
    const face = theme.button(theme.tag("arrow", if (dir < 0) 0 else 1), r, 20 * u, theme.tones.cream_tone, hot, .{ .a = e }).face;

    theme.icon(if (dir < 0) .back else .chevron, face.x + face.width / 2, face.y + face.height / 2, face.width * 0.6, theme.fade(theme.navy, e));
}

fn slotRect(lay: Layout, i: usize) rl.Rectangle {
    const u = unit();
    const gap = 14 * u;
    const n: f32 = @floatFromInt(slot_count);
    const sw = (lay.slots.width - gap * (n - 1)) / n;

    return .{ .x = lay.slots.x + (sw + gap) * @as(f32, @floatFromInt(i)), .y = lay.slots.y, .width = sw, .height = lay.slots.height };
}

pub fn buttonRect() rl.Rectangle {
    return menu.pauseSlot(0);
}
