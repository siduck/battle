const std = @import("std");
const shared = @import("shared");

const math = shared.math;
const geom = shared.geom;
const map = shared.map;
const movement = shared.movement;
const weapons = shared.weapons;
const Vec3 = math.Vec3;
const Rarity = weapons.Rarity;
const world = shared.world;
const terrain = shared.terrain;
const vehicle = shared.vehicle;
const driving = @import("driving.zig");
const air = @import("air.zig");

var pieces: []const map.Piece = &.{};
const tau: f32 = std.math.pi * 2;

pub const max_hp: f32 = 100;

pub const fire_max: f32 = 3;
pub const fire_recharge: f32 = 2.4;
pub const fire_charge_time: f32 = 0.55;
const fire_speed: f32 = 36;
const fire_radius: f32 = 3.4;
const fire_push: f32 = 15.5;

pub var god_mode = true;

pub var bots_passive = false;

fn bot_index(g: *Game, b: *const Bot) usize {
    return (@intFromPtr(b) - @intFromPtr(&g.bots.items[0])) / @sizeOf(Bot);
}
const regen_delay: f32 = 5;
const regen_rate: f32 = 14;
const respawn_time: f32 = 3;
const switch_time: f32 = 0.32;
const bot_reaction: f32 = 0.45;
const bot_strike: f32 = 0.45;
const bot_swing: f32 = 0.85;
const melee_bot_share: f32 = 0.3;
const max_alive: usize = 6;
fn bounds() f32 {
    return terrain.play - 4;
}
const pickup_reach: f32 = 2.2;
const spot_respawn: f32 = 30;
pub const gun_slots = 4;
pub const knife_slot = gun_slots;

pub fn Pool(comptime T: type, comptime n: usize) type {
    return struct {
        items: [n]T = @splat(.{}),
        next: usize = 0,

        const Self = @This();

        pub fn spawn(self: *Self, item: T) void {
            for (&self.items) |*slot| {
                if (slot.active) continue;

                slot.* = item;
                slot.active = true;

                return;
            }

            self.items[self.next] = item;
            self.items[self.next].active = true;
            self.next = (self.next + 1) % n;
        }

        pub fn age(self: *Self, dt: f32) void {
            for (&self.items) |*slot| {
                if (!slot.active) continue;

                slot.life -= dt;

                if (slot.life <= 0) slot.active = false;
            }
        }

        pub fn countActive(self: Self) usize {
            var total: usize = 0;

            for (self.items) |slot| {
                if (slot.active) total += 1;
            }

            return total;
        }
    };
}

pub const Tracer = struct {
    active: bool = false,
    from: Vec3 = .{},
    to: Vec3 = .{},
    life: f32 = 0,
    flame: bool = false,
};

pub const Impact = struct {
    active: bool = false,
    pos: Vec3 = .{},
    life: f32 = 0,
    seed: f32 = 0,
};

pub const Explosion = struct {
    active: bool = false,
    pos: Vec3 = .{},
    radius: f32 = 0,
    life: f32 = 0,
    total: f32 = 0,
    fire: bool = false,
};

pub const Popup = struct {
    active: bool = false,
    pos: Vec3 = .{},
    value: u32 = 0,
    life: f32 = 0,
};

pub const ProjectileKind = enum { rocket, grenade, orb, arrow, gun, fireball };

pub const Projectile = struct {
    active: bool = false,
    kind: ProjectileKind = .orb,
    pos: Vec3 = .{},
    vel: Vec3 = .{},
    life: f32 = 0,
    damage: f32 = 0,
    splash: f32 = 0,
    knockback: f32 = 0,
    gravity: f32 = 0,
    spin: f32 = 0,
    stuck: bool = false,
    heading: Vec3 = .{ .z = -1 },
    item: ?Held = null,
};

pub const Swing = enum { none, light, heavy };

pub const Cue = enum { none, parry, blocked, clash, counter, staggered };

pub const Melee = struct {
    weapon: u8 = 255,
    kind: Swing = .none,
    arc: u8 = 0,
    t: f32 = 0,
    length: f32 = 0,
    struck: bool = false,
    queued: bool = false,
    chain: f32 = 0,
    hold: f32 = 0,
    holding: bool = false,
    power: f32 = 0,
    block: f32 = -1,
    stagger: f32 = 0,
    counter: f32 = 0,
    lunge: f32 = 0,
    lunge_vel: Vec3 = .{},
    hitstop: f32 = 0,
    shake: f32 = 0,
    cue: Cue = .none,
    cue_t: f32 = 0,

    pub const strike_at: f32 = 0.38;
    pub const heavy_after: f32 = 0.2;
    pub const heavy_full: f32 = 0.75;
    pub const parry_window: f32 = 0.2;

    pub fn progress(m: Melee) f32 {
        if (m.kind == .none or m.length <= 0) return 0;

        return math.clamp01(m.t / m.length);
    }

    pub fn striking(m: Melee) bool {
        const p = m.progress();

        return m.kind != .none and p > strike_at - 0.14 and p < strike_at + 0.08;
    }

    pub fn charging(m: Melee) f32 {
        if (!m.holding or m.hold < heavy_after) return 0;

        return math.clamp01((m.hold - heavy_after) / (heavy_full - heavy_after));
    }
};

pub const Bot = struct {
    active: bool = false,
    body: movement.Player = .{ .pos = .{} },
    prev: Vec3 = .{},
    yaw: f32 = 0,
    pitch: f32 = 0,
    hp: f32 = 100,
    max_hp: f32 = 100,
    weapon: u8 = 0,
    mag: u16 = 0,
    reload: f32 = 0,
    fire_cd: f32 = 0,
    goal: Vec3 = .{},
    retarget: f32 = 0,
    strafe: f32 = 1,
    strafe_t: f32 = 0,
    seen: f32 = 0,
    stuck: f32 = 0,
    input: movement.Input = .{},
    dead: f32 = -1,
    flash: f32 = 0,
    anim: f32 = 0,
    shot: f32 = 0,
    life: f32 = 1,
    frozen: bool = false,
    swing: f32 = -1,
    struck: bool = false,
    guard: f32 = -1,
    parry: bool = false,
    stagger: f32 = 0,
    melee_cd: f32 = 0,

    pub fn alive(b: Bot) bool {
        return b.active and b.dead < 0;
    }

    pub fn chest(b: Bot) Vec3 {
        return b.body.pos.add(.{ .y = 1.2 });
    }
};

pub const BotHit = struct {
    index: usize,
    t: f32,
    head: bool,
};

pub const PickupKind = enum { ammo, health };

pub const Pickup = struct {
    active: bool = false,
    kind: PickupKind = .ammo,
    pos: Vec3 = .{},
    life: f32 = 0,
    phase: f32 = 0,
};

pub const Held = struct {
    weapon: u8,
    rarity: Rarity = .common,
    mag: u16,
    reserve: u16,

    pub fn fresh(weapon: u8, rarity: Rarity) Held {
        const s = weapons.specs[weapon];

        return .{ .weapon = weapon, .rarity = rarity, .mag = s.mag, .reserve = s.reserve };
    }

    pub fn spec(h: Held) weapons.Spec {
        return weapons.specs[h.weapon];
    }
};

pub const Drop = struct {
    active: bool = false,
    held: Held = .{ .weapon = 0, .mag = 0, .reserve = 0 },
    pos: Vec3 = .{},
    life: f32 = 0,
    phase: f32 = 0,
    spot: ?u8 = null,
};

pub const FeedKind = enum { bot_down, wave_clear, ammo, health, weapon };

pub const Feed = struct {
    active: bool = false,
    kind: FeedKind = .bot_down,
    value: u32 = 0,
    weapon: u8 = 0,
    rarity: Rarity = .common,
    life: f32 = 0,
};

pub const Banner = enum { none, wave_start, wave_clear, erased };

pub const Assist = struct {
    target: ?usize = null,
    last_yaw: f32 = 0,
    last_pitch: f32 = 0,
    snap: f32 = 0,
};

pub const Buzz = struct {
    strong: f32 = 0,
    weak: f32 = 0,
    time: f32 = 0,

    fn add(b: *Buzz, strong: f32, weak: f32, time: f32) void {
        b.strong = @max(b.strong, strong);
        b.weak = @max(b.weak, weak);
        b.time = @max(b.time, time);
    }
};

fn wrapAngle(a: f32) f32 {
    return a - tau * @round(a / tau);
}

pub const Controls = struct {
    forward: f32 = 0,
    right: f32 = 0,
    gas: f32 = 0,
    brake_pedal: f32 = 0,
    boost: bool = false,
    jump: bool = false,
    fire_down: bool = false,
    fire_pressed: bool = false,
    aim: bool = false,
    reload: bool = false,
    grenade: bool = false,
    interact: bool = false,
    select: ?u8 = null,
    cycle: i32 = 0,
    quick_swap: bool = false,
    zoom_step: i32 = 0,
    steady: bool = false,
    throw_gun: bool = false,
    fireball: bool = false,
    enter: bool = false,
};

pub const View = struct {
    eye: Vec3,
    forward: Vec3,
    right: Vec3,
    up: Vec3,
    muzzle: Vec3,
};

pub const Arsenal = struct {
    slots: [gun_slots]?Held = .{ Held.fresh(weapons.indexOf("Liner"), .common), Held.fresh(weapons.indexOf("Pocket"), .common), null, null },
    blade: Held = Held.fresh(weapons.knife, .common),
    active: u8 = 0,
    previous: u8 = 1,
    cooldown: f32 = 0,
    reloading: f32 = 0,
    switching: f32 = 0,
    grenades: u8 = 3,
    throw_cd: f32 = 0,
    kick: f32 = 0,
    swing: f32 = 0,
    flash: f32 = 0,
    charge: f32 = 0,
    spin: f32 = 0,
    burst_left: u8 = 0,
    burst_timer: f32 = 0,
    shown: f32 = 2.5,

    pub fn held(a: *Arsenal) *Held {
        if (a.active == knife_slot) return &a.blade;

        return &a.slots[a.active].?;
    }

    pub fn current(a: Arsenal) Held {
        if (a.active == knife_slot) return a.blade;

        return a.slots[a.active].?;
    }

    pub fn spec(a: Arsenal) weapons.Spec {
        return a.current().spec();
    }

    fn has(a: Arsenal, slot: u8) bool {
        return slot == knife_slot or (slot < gun_slots and a.slots[slot] != null);
    }

    fn equip(a: *Arsenal, slot: u8) void {
        if (slot == a.active or !a.has(slot)) return;

        a.previous = a.active;
        a.active = slot;
        a.reloading = 0;
        a.switching = switch_time;
        a.cooldown = 0;
        a.swing = 0;
        a.charge = 0;
        a.spin = 0;
        a.burst_left = 0;
        a.shown = 2.5;
    }

    fn cycle(a: *Arsenal, dir: i32) void {
        var slot: i32 = a.active;
        var tries: u8 = 0;

        while (tries < gun_slots + 1) : (tries += 1) {
            slot = @mod(slot + dir, gun_slots + 1);

            if (a.has(@intCast(slot))) {
                a.equip(@intCast(slot));

                return;
            }
        }
    }
};

pub const Game = struct {
    prng: std.Random.DefaultPrng,
    time: f32 = 0,
    player: movement.Player,
    prev_pos: Vec3,
    accumulator: f32 = 0,
    yaw: f32,
    pitch: f32 = 0,
    recoil: f32 = 0,
    recoil_yaw: f32 = 0,
    ads: f32 = 0,
    hp: f32 = max_hp,
    since_hurt: f32 = 10,
    dead: f32 = 0,
    arsenal: Arsenal = .{},
    melee_state: Melee = .{},
    melee_auto: bool = false,
    melee_auto_down: bool = false,
    tracers: Pool(Tracer, 64) = .{},
    impacts: Pool(Impact, 48) = .{},
    shards: Pool(Impact, 16) = .{},
    explosions: Pool(Explosion, 16) = .{},
    popups: Pool(Popup, 32) = .{},
    projectiles: Pool(Projectile, 96) = .{},
    bots: Pool(Bot, 16) = .{},
    pickups: Pool(Pickup, 16) = .{},
    drops: Pool(Drop, 40) = .{},
    spot_timers: [128]f32 = @splat(0.1),
    feed: Pool(Feed, 5) = .{},
    near_drop: ?usize = null,
    wave: u32 = 0,
    to_spawn: u32 = 0,
    spawn_timer: f32 = 0,
    wave_break: f32 = 2.5,
    banner: f32 = 0,
    banner_kind: Banner = .none,
    score: u32 = 0,
    kills: u32 = 0,
    hit_marker: f32 = 0,
    hit_kill: bool = false,
    hurt_flash: f32 = 0,
    hurt_dir: f32 = 0,
    bob: f32 = 0,
    assist: Assist = .{},
    buzz: Buzz = .{},
    vehicles: [vehicle.count]vehicle.Vehicle = undefined,
    fire_charges: f32 = fire_max,
    fire_cd: f32 = 0,
    fire_hold: f32 = 0,
    fire_held: bool = false,
    scope_level: u8 = 0,
    breath: f32 = 4,
    steadying: bool = false,
    sway_x: f32 = 0,
    sway_y: f32 = 0,

    pub fn init(seed: u64) Game {
        const start = world.spawns[0];

        pieces = world.pieces;

        return .{
            .prng = std.Random.DefaultPrng.init(seed),
            .player = movement.Player.spawn(start),
            .prev_pos = start,
            .yaw = world.spawn_yaws[0],
        };
    }

    pub fn rand(g: *Game) f32 {
        return g.prng.random().float(f32);
    }

    fn rollRarity(g: *Game) Rarity {
        const r = g.rand() - @min(0.15, @as(f32, @floatFromInt(g.wave)) * 0.01);

        if (r < 0.52) return .common;
        if (r < 0.76) return .uncommon;
        if (r < 0.9) return .rare;
        if (r < 0.97) return .epic;

        return .legendary;
    }

    fn rollWeapon(g: *Game) u8 {
        return g.prng.random().uintLessThan(u8, weapons.knife);
    }

    pub fn scopeMultiplier(g: Game) f32 {
        if (!g.hasScope()) return 1;

        const levels = [_]f32{ 1, 1.7, 2.9 };

        return levels[@min(g.scope_level, 2)];
    }

    pub fn hasScope(g: Game) bool {
        const optic = g.arsenal.spec().look.optic;

        return optic == .scope4 or optic == .scope8;
    }

    pub fn zoom(g: Game) f32 {
        const full = g.arsenal.spec().ads_zoom * g.scopeMultiplier();

        return 1 + (full - 1) * g.ads;
    }

    pub fn scoped(g: Game) bool {
        const optic = g.arsenal.spec().look.optic;

        return (optic == .scope4 or optic == .scope8) and g.ads > 0.85;
    }

    pub fn look(g: *Game, dx: f32, dy: f32, sensitivity: f32) void {
        if (g.dead > 0) return;

        const s = sensitivity / g.zoom();

        g.yaw -= dx * s;
        g.pitch = std.math.clamp(g.pitch - dy * s, -1.5, 1.5);
    }

    pub fn turn(g: *Game, dyaw: f32, dpitch: f32) void {
        if (g.dead > 0) return;

        const z = g.zoom();

        g.yaw += dyaw / z;
        g.pitch = std.math.clamp(g.pitch + dpitch / z, -1.5, 1.5);
    }

    pub fn aimAssist(g: *Game, dt: f32, look_input: f32, move_input: f32, aim_started: bool) f32 {
        if (g.dead > 0 or g.arsenal.spec().fire == .melee) {
            g.assist.target = null;

            return 1;
        }

        const eye = g.player.eye();
        const forward = math.lookDir(g.yaw, g.pitch);
        var best: ?usize = null;
        var best_angle: f32 = 1e9;
        var best_cone: f32 = 0;
        var best_yaw: f32 = 0;
        var best_pitch: f32 = 0;

        for (g.bots.items, 0..) |d, i| {
            if (!d.alive()) continue;

            const to = d.chest().sub(eye);
            const dist = to.length();

            if (dist > 70 or dist < 0.5) continue;

            const dir = to.scale(1 / dist);
            const angle = std.math.acos(std.math.clamp(dir.dot(forward), -1, 1));
            const cone = std.math.atan(1.3 / dist) + 0.03 + 0.02 * g.ads;

            if (angle > cone * 2.6 or angle >= best_angle) continue;

            if (movement.raycast(pieces, eye, dir, dist) != null) continue;

            best = i;
            best_angle = angle;
            best_cone = cone;
            best_yaw = std.math.atan2(dir.x, dir.z);
            best_pitch = std.math.asin(std.math.clamp(dir.y, -1, 1));
        }

        const index = best orelse {
            g.assist.target = null;

            return 1;
        };

        if (aim_started) g.assist.snap = 0.14;

        const dy = wrapAngle(best_yaw - g.yaw);
        const dp = best_pitch - g.pitch;

        if (g.assist.snap > 0) {
            const k = @min(1, dt * 16) * 0.75;

            g.assist.snap -= dt;
            g.yaw += dy * k;
            g.pitch += dp * k;
        }

        const same = if (g.assist.target) |t| t == index else false;

        if (same and (look_input > 0.05 or move_input > 0.1) and best_angle < best_cone * 1.8) {
            g.yaw += wrapAngle(best_yaw - g.assist.last_yaw) * 0.45;
            g.pitch += (best_pitch - g.assist.last_pitch) * 0.45;
        }

        g.assist.target = index;
        g.assist.last_yaw = best_yaw;
        g.assist.last_pitch = best_pitch;

        if (best_angle < best_cone) return 0.5;

        return 0.75;
    }

    pub fn simulate(g: *Game, frame_dt: f32, c: Controls) void {
        const alive = g.dead <= 0;
        const guard: f32 = if (g.meleeBlocking()) 0.5 else 1;
        const input: movement.Input = .{
            .forward = if (alive) c.forward * guard else 0,
            .right = if (alive) c.right * guard else 0,
            .jump = alive and c.jump,
            .aiming = g.ads > 0.5,
            .yaw = g.yaw,
        };

        g.accumulator += @min(frame_dt, 0.25);

        while (g.accumulator >= movement.dt) {
            g.prev_pos = g.player.pos;

            if (air.flying()) air.tick(g, c) else if (driving.driving()) driving.tick(g, c) else movement.step(&g.player, input, pieces);

            if (!air.flying()) air.tick(g, .{});

            if (!driving.driving()) driving.tick(g, .{});

            for (&g.bots.items) |*b| {
                if (!b.active) continue;

                b.prev = b.body.pos;

                if (b.dead < 0) movement.step(&b.body, b.input, pieces);
            }

            driving.solid(g);

            for (&g.bots.items, 0..) |*b, i| {
                if (b.active and b.dead < 0 and b.body.pos.y < movement.kill_y) g.damageBot(i, 1e6, b.body.pos, false);
            }

            g.accumulator -= movement.dt;
        }

        if (g.player.pos.y < movement.kill_y) g.respawn();
    }

    pub fn view(g: Game) View {
        if (air.view(g)) |v| return v;

        if (driving.view(g)) |v| return v;

        const alpha = g.accumulator / movement.dt;
        const pos = g.prev_pos.lerp(g.player.pos, alpha);
        const shake = g.meleeShake();
        const pitch = std.math.clamp(g.pitch + g.recoil + g.sway_y + shake[1], -1.55, 1.55);
        const forward = math.lookDir(g.yaw + g.recoil_yaw + g.sway_x + shake[0], pitch);
        const right = forward.cross(math.up).normalize();
        const up = right.cross(forward);
        const eye = pos.add(.{ .y = movement.eye_height });
        const side = 0.17 * (1 - g.ads);
        const reach = 0.32 + g.arsenal.spec().reach();

        return .{
            .eye = eye,
            .forward = forward,
            .right = right,
            .up = up,
            .muzzle = eye.add(right.scale(side)).add(up.scale(-0.12 + 0.06 * g.ads)).add(forward.scale(reach)),
        };
    }

    pub fn update(g: *Game, dt: f32, c: Controls, v: View) void {
        g.time += dt;
        g.hit_marker = @max(0, g.hit_marker - dt);
        g.hurt_flash = @max(0, g.hurt_flash - dt);
        g.banner = @max(0, g.banner - dt);
        g.since_hurt += dt;
        g.recoil *= @exp(-dt * 6);
        g.recoil_yaw *= @exp(-dt * 6);

        g.tracers.age(dt);
        g.impacts.age(dt);
        g.shards.age(dt);
        g.explosions.age(dt);
        g.popups.age(dt);
        g.feed.age(dt);

        for (&g.popups.items) |*p| {
            if (p.active) p.pos.y += dt * 1.2;
        }

        g.tickMelee(dt);
        g.updateScope(dt, c);
        g.updateSpots(dt);
        g.findNearDrop();
        var car_c = c;

        if (air.update(g, dt, c) or air.flying()) car_c.enter = false;

        driving.update(g, dt, car_c);

        if (g.dead > 0) {
            g.dead -= dt;
            g.ads = 0;

            if (g.dead <= 0) g.respawn();
        } else {
            if (g.since_hurt > regen_delay) g.hp = @min(max_hp, g.hp + regen_rate * dt);

            if (c.interact) g.pickUp();

            if (air.flying()) {} else if (driving.inTank(g)) driving.tankFire(g, c) else g.updateArsenal(dt, c, v);
            g.updateFireball(dt, c, v);
        }

        const speed = g.player.vel.flatLength();

        if (g.player.grounded and speed > 0.5) g.bob += dt * speed * 1.5;

        g.updateProjectiles(dt);
        g.updateBots(dt);
        g.updatePickups(dt);
        g.updateWaves(dt);
    }

    fn updateScope(g: *Game, dt: f32, c: Controls) void {
        const scoped_in = g.scoped();

        if (!g.hasScope()) g.scope_level = 0;

        if (scoped_in and c.zoom_step != 0) {
            const next = @as(i32, g.scope_level) + c.zoom_step;

            g.scope_level = @intCast(std.math.clamp(next, 0, 2));
        }

        g.steadying = scoped_in and c.steady and g.breath > 0;

        if (g.steadying) g.breath = @max(0, g.breath - dt) else g.breath = @min(4, g.breath + dt * (if (c.steady) @as(f32, 0) else @as(f32, 0.8)));

        const amount: f32 = if (!scoped_in) 0 else if (g.steadying) 0.0004 else 0.0035 / @sqrt(g.scopeMultiplier());
        const t = g.time;
        const target_x = (@sin(t * 0.9) + @sin(t * 2.3) * 0.35) * amount;
        const target_y = (@cos(t * 0.7) * 0.8 + @sin(t * 1.9) * 0.3) * amount;
        const k = @min(1, dt * 6);

        g.sway_x += (target_x - g.sway_x) * k;
        g.sway_y += (target_y - g.sway_y) * k;
    }

    fn updateSpots(g: *Game, dt: f32) void {
        for (g.spot_timers[0..@min(world.weapon_spots.len, g.spot_timers.len)], 0..) |*t, i| {
            if (t.* <= 0) continue;

            t.* -= dt;

            if (t.* > 0) continue;

            g.drops.spawn(.{
                .held = Held.fresh(g.rollWeapon(), g.rollRarity()),
                .pos = world.weapon_spots[i].add(.{ .y = 0.55 }),
                .life = 1e9,
                .phase = g.rand() * tau,
                .spot = @intCast(i),
            });
        }

        for (&g.drops.items) |*d| {
            if (!d.active) continue;

            d.phase += dt * 1.4;
            d.life -= dt;

            if (d.life <= 0) d.active = false;
        }
    }

    fn findNearDrop(g: *Game) void {
        const center = g.player.center();
        var best: f32 = pickup_reach;

        g.near_drop = null;

        for (g.drops.items, 0..) |d, i| {
            if (!d.active) continue;

            const dist = d.pos.distance(center);

            if (dist < best) {
                best = dist;
                g.near_drop = i;
            }
        }
    }

    fn pickUp(g: *Game) void {
        const index = g.near_drop orelse return;
        const drop = &g.drops.items[index];
        const a = &g.arsenal;
        var target: ?u8 = null;

        for (a.slots, 0..) |s, i| {
            if (s == null) {
                target = @intCast(i);

                break;
            }
        }

        const slot: u8 = target orelse (if (a.active == knife_slot) 0 else a.active);
        const old = a.slots[slot];

        a.slots[slot] = drop.held;

        if (drop.spot) |spot| g.spot_timers[spot] = spot_respawn;

        g.feed.spawn(.{ .kind = .weapon, .weapon = drop.held.weapon, .rarity = drop.held.rarity, .life = 2.5 });
        drop.active = false;
        g.near_drop = null;

        if (old) |o| {
            g.drops.spawn(.{ .held = o, .pos = g.player.pos.add(.{ .y = 0.5 }), .life = 40, .phase = g.rand() * tau });
        }

        a.active = slot +% 1;
        a.equip(slot);
    }

    fn updateArsenal(g: *Game, dt: f32, c: Controls, v: View) void {
        const a = &g.arsenal;

        a.cooldown = @max(0, a.cooldown - dt);
        a.kick = @max(0, a.kick - dt * 8);
        a.swing = @max(0, a.swing - dt);
        a.flash = @max(0, a.flash - dt);
        a.throw_cd = @max(0, a.throw_cd - dt);
        a.shown = @max(0, a.shown - dt);

        if (c.select) |slot| a.equip(slot);

        if (c.quick_swap) a.equip(a.previous);

        if (c.cycle != 0) a.cycle(c.cycle);

        const spec = a.spec();
        const charging = spec.charge > 0 and a.charge > 0;
        const aim_target: f32 = if ((c.aim or (charging and spec.class == .bow)) and spec.fire != .melee and a.switching <= 0 and a.reloading <= 0) 1 else 0;

        g.ads = math.approach(g.ads, aim_target, dt * (if (aim_target > 0) @as(f32, 6) else @as(f32, 9)));

        if (a.switching > 0) {
            a.switching -= dt;

            return;
        }

        const held = a.held();

        if (a.reloading > 0) {
            a.reloading -= dt;

            if (a.reloading <= 0) {
                const take = @min(spec.mag - held.mag, held.reserve);

                a.reloading = 0;
                held.mag += take;
                held.reserve -= take;
            }
        }

        const reload_time = spec.reload * weapons.rarity_reload[@intFromEnum(held.rarity)];

        if (c.reload and spec.mag > 0 and held.mag < spec.mag and held.reserve > 0 and a.reloading <= 0) {
            a.reloading = reload_time;
            a.charge = 0;
            a.burst_left = 0;
        }

        if (c.throw_gun and a.active != knife_slot and a.throw_cd <= 0) {
            if (a.slots[a.active]) |thrown| {
                a.slots[a.active] = null;
                a.throw_cd = 0.4;
                g.projectiles.spawn(.{
                    .kind = .gun,
                    .pos = v.eye.add(v.forward.scale(0.5)),
                    .vel = v.forward.scale(24).add(.{ .y = 2.5 }).add(g.player.vel.scale(0.6)),
                    .life = 6,
                    .damage = 60,
                    .gravity = 14,
                    .heading = v.forward,
                    .item = thrown,
                });
                a.cycle(1);

                return;
            }
        }

        if (c.grenade and a.grenades > 0 and a.throw_cd <= 0) {
            a.grenades -= 1;
            a.throw_cd = weapons.grenade.interval;
            g.throwGrenade(v, weapons.grenade, 4.5, 1);
        }

        if (spec.fire == .melee) {
            g.updateMelee(dt, if (g.melee_auto) g.autoMelee(c) else c, v, spec, held.rarity);

            return;
        }

        if (a.burst_left > 0) {
            a.burst_timer -= dt;

            if (a.burst_timer <= 0 and held.mag > 0) {
                g.shoot(v, spec, held, 1);
                a.burst_left -= 1;
                a.burst_timer = 0.07;
            }

            if (held.mag == 0) a.burst_left = 0;

            return;
        }

        if (spec.spinup > 0) {
            if (c.fire_down and a.reloading <= 0) a.spin = @min(spec.spinup, a.spin + dt) else a.spin = @max(0, a.spin - dt * 1.5);

            if (a.spin < spec.spinup) return;
        }

        if (a.reloading > 0 or a.cooldown > 0) {
            a.charge = 0;

            return;
        }

        if (spec.charge > 0) {
            if (held.mag == 0) {
                if (c.fire_pressed and held.reserve > 0) a.reloading = reload_time;

                return;
            }

            if (c.fire_down) {
                a.charge = @min(spec.charge, a.charge + dt);

                if (spec.fire == .hitscan and a.charge >= spec.charge) {
                    a.charge = 0;
                    g.shoot(v, spec, held, 1);
                }

                return;
            }

            if (a.charge > 0 and spec.fire != .hitscan) g.shoot(v, spec, held, std.math.clamp(a.charge / spec.charge, 0.2, 1));

            a.charge = 0;

            return;
        }

        const wants = if (spec.auto) c.fire_down else c.fire_pressed;

        if (!wants) return;

        if (spec.fire == .melee) {
            a.cooldown = spec.interval;
            a.swing = 0.28;
            g.melee(v, spec);

            return;
        }

        if (held.mag == 0) {
            if (held.reserve > 0) a.reloading = reload_time;

            return;
        }

        g.shoot(v, spec, held, 1);

        if (spec.burst > 1) {
            a.burst_left = spec.burst - 1;
            a.burst_timer = 0.07;
        }
    }

    fn shoot(g: *Game, v: View, spec: weapons.Spec, held: *Held, power: f32) void {
        const a = &g.arsenal;
        const damage = spec.damage * weapons.rarity_damage[@intFromEnum(held.rarity)] * power;

        held.mag -= 1;
        a.cooldown = spec.interval;
        a.kick = 1;
        a.flash = if (spec.class == .bow or spec.class == .crossbow) 0 else 0.05;
        g.recoil += spec.recoil * (1 - 0.4 * g.ads);
        g.recoil_yaw += (g.rand() - 0.5) * spec.recoil * 0.6;
        g.buzz.add(@min(0.8, spec.recoil * 9), @min(0.9, 0.25 + spec.recoil * 6), @min(0.18, 0.05 + spec.recoil));

        switch (spec.fire) {
            .hitscan => g.fireHitscan(v, spec, damage),
            .rocket => g.projectiles.spawn(.{
                .kind = .rocket,
                .pos = v.eye.add(v.forward.scale(0.3)),
                .vel = v.forward.scale(spec.speed),
                .life = 6,
                .damage = damage,
                .splash = spec.splash,
                .knockback = spec.knockback,
                .heading = v.forward,
            }),
            .grenade => g.throwGrenade(v, spec, 3, damage / spec.damage),
            .arrow, .bolt => g.projectiles.spawn(.{
                .kind = .arrow,
                .pos = v.eye.add(v.forward.scale(0.4)),
                .vel = v.forward.scale(spec.speed * (0.35 + 0.65 * power)),
                .life = 8,
                .damage = damage,
                .gravity = spec.gravity,
                .heading = v.forward,
            }),
            .melee => {},
        }

        if (held.mag == 0 and held.reserve > 0) a.reloading = spec.reload * weapons.rarity_reload[@intFromEnum(held.rarity)];
    }

    fn spreadDir(g: *Game, v: View, spread: f32) Vec3 {
        const r = spread * @sqrt(g.rand());
        const ang = g.rand() * tau;

        return v.forward.add(v.right.scale(@cos(ang) * r)).add(v.up.scale(@sin(ang) * r)).normalize();
    }

    fn fireHitscan(g: *Game, v: View, spec: weapons.Spec, damage: f32) void {
        const moving = math.clamp01(g.player.vel.flatLength() / 7);
        const airborne: f32 = if (g.player.grounded) 0 else 0.02;
        const spread = spec.spread + (spec.ads_spread - spec.spread) * g.ads + (moving * 0.015 + airborne) * (1 - g.ads);
        var pellet: u8 = 0;

        while (pellet < spec.pellets) : (pellet += 1) {
            const dir = g.spreadDir(v, spread);
            const wall_hit = movement.raycast(pieces, v.eye, dir, spec.range);
            const wall_t = if (wall_hit) |h| h.t else spec.range;

            if (spec.pierce) {
                var reach_t = wall_t;
                var hits: u8 = 0;

                while (hits < 4) : (hits += 1) {
                    const hit = g.hitBot(v.eye, dir, reach_t, null) orelse break;

                    g.damageBot(hit.index, damage * (if (hit.head) @as(f32, 1.8) else @as(f32, 1)), v.eye.add(dir.scale(hit.t)), hit.head);
                    reach_t = wall_t;

                    if (g.bots.items[hit.index].alive()) break;
                }

                g.tracers.spawn(.{ .from = v.muzzle, .to = v.eye.add(dir.scale(wall_t)), .life = 0.25 });

                if (wall_hit != null) g.impacts.spawn(.{ .pos = v.eye.add(dir.scale(wall_t)), .life = 2, .seed = g.rand() });

                continue;
            }

            const car_hit = driving.hitVehicle(g, v.eye, dir, wall_t);
            const struck = g.hitBot(v.eye, dir, if (car_hit) |h| h.t else wall_t, null);
            const limit = if (struck) |hit| hit.t else if (car_hit) |h| h.t else wall_t;

            if (struck == null) {
                if (car_hit) |h| driving.damage(g, h.index, damage, v.eye.add(dir.scale(h.t)));
            }

            const end = v.eye.add(dir.scale(limit));

            if (spec.flame) {
                g.tracers.spawn(.{ .from = v.muzzle, .to = end, .life = 0.12, .flame = true });
            } else if (pellet < 3 or g.rand() < 0.4) {
                g.tracers.spawn(.{ .from = v.muzzle, .to = end, .life = 0.07 });
            }

            if (struck) |hit| {
                const falloff: f32 = if (limit > spec.range * 0.5) 0.7 else 1;
                const head: f32 = if (hit.head) 1.8 else 1;

                g.damageBot(hit.index, damage * falloff * head, end, hit.head);
            } else if (wall_hit != null and !spec.flame) {
                if (world.breakGlass(end)) |at| {
                    g.shards.spawn(.{ .pos = at, .life = 1.4, .seed = g.rand() });
                } else {
                    g.impacts.spawn(.{ .pos = end, .life = 1.6, .seed = g.rand() });
                }
            }
        }
    }

    fn tickMelee(g: *Game, dt: f32) void {
        const m = &g.melee_state;

        m.shake *= @exp(-dt * 9);
        m.cue_t = @max(0, m.cue_t - dt);

        if (weapons.isMelee(g.arsenal.spec()) and g.dead <= 0) return;

        m.* = .{ .shake = m.shake, .cue = m.cue, .cue_t = m.cue_t };
    }

    pub fn blastShake(g: *Game, at: Vec3, radius: f32) void {
        const reach = 10 + radius * 6;
        const near = math.clamp01(1 - g.player.center().distance(at) / reach);

        if (near <= 0) return;

        g.melee_state.shake = @max(g.melee_state.shake, near * near * (1.2 + radius * 0.25));
    }

    pub fn meleeShake(g: Game) [2]f32 {
        const k = g.melee_state.shake;

        return .{ @sin(g.time * 53) * k * 0.025, @sin(g.time * 41 + 1.3) * k * 0.025 };
    }

    pub fn meleeBlocking(g: Game) bool {
        return g.melee_state.block >= 0;
    }

    fn cueMelee(g: *Game, cue: Cue) void {
        g.melee_state.cue = cue;
        g.melee_state.cue_t = 0.8;
    }

    fn autoMelee(g: *Game, c: Controls) Controls {
        var out = c;
        var best: f32 = 1e9;

        for (g.bots.items) |b| {
            if (!b.alive()) continue;

            const to = b.body.pos.sub(g.player.pos);
            const d = to.flatLength();

            if (d < best) {
                best = d;
                g.yaw = std.math.atan2(to.x, to.z);
            }
        }

        const t = @mod(g.time, 7);
        const down = if (t < 2.2) @mod(t, 0.22) < 0.06 else t >= 2.6 and t < 3.6;

        out.fire_down = down;
        out.fire_pressed = down and !g.melee_auto_down;
        out.aim = t >= 4.2 and t < 6.6;
        g.melee_auto_down = down;

        return out;
    }

    fn updateMelee(g: *Game, dt: f32, c: Controls, v: View, spec: weapons.Spec, rarity: Rarity) void {
        const m = &g.melee_state;
        const weapon = g.arsenal.current().weapon;

        if (m.weapon != weapon) m.* = .{ .weapon = weapon, .shake = m.shake, .cue = m.cue, .cue_t = m.cue_t };

        m.chain = @max(0, m.chain - dt);
        m.counter = @max(0, m.counter - dt);

        if (m.lunge > 0) {
            m.lunge -= dt;
            g.player.vel.x = m.lunge_vel.x;
            g.player.vel.z = m.lunge_vel.z;
        }

        if (m.hitstop > 0) {
            m.hitstop -= dt;

            return;
        }

        if (m.stagger > 0) {
            m.stagger -= dt;
            m.block = -1;
            m.holding = false;
            m.hold = 0;

            return;
        }

        if (m.kind != .none) {
            m.t += dt;

            if (!m.struck and m.progress() >= Melee.strike_at) {
                m.struck = true;
                g.strike(v, spec, rarity);
            }

            if (m.kind == .none) return;

            if (c.fire_pressed and m.kind == .light and m.arc < 2 and m.progress() > 0.2) m.queued = true;

            if (m.t >= m.length) {
                const next = m.queued;
                const arc = m.arc;

                m.kind = .none;
                m.queued = false;
                m.chain = if (arc < 2) 0.4 else 0;

                if (next) g.startSwing(v, spec, .light, arc + 1, 0);
            }

            return;
        }

        if (c.aim) {
            m.block = if (m.block < 0) 0 else m.block + dt;
            m.holding = false;
            m.hold = 0;

            return;
        }

        m.block = -1;

        if (c.fire_down) {
            if (!m.holding) {
                if (!c.fire_pressed) return;

                m.holding = true;
                m.hold = 0;
            }

            m.hold += dt;

            return;
        }

        if (!m.holding) return;

        m.holding = false;

        if (m.hold >= Melee.heavy_after) {
            g.startSwing(v, spec, .heavy, 3, math.clamp01((m.hold - Melee.heavy_after) / (Melee.heavy_full - Melee.heavy_after)));
        } else {
            const arc: u8 = if (m.chain > 0) (m.arc + 1) % 3 else 0;

            g.startSwing(v, spec, .light, arc, 0);
        }

        m.hold = 0;
    }

    fn startSwing(g: *Game, v: View, spec: weapons.Spec, kind: Swing, arc: u8, power: f32) void {
        const m = &g.melee_state;

        m.kind = kind;
        m.arc = arc;
        m.t = 0;
        m.struck = false;
        m.queued = false;
        m.power = power;
        m.length = switch (kind) {
            .heavy => spec.interval * 1.7,
            else => if (arc == 2) spec.interval * 1.25 else spec.interval,
        };

        g.lungeToward(v, spec, if (kind == .heavy) 1.4 + power else 1);
        g.botsReact(spec);
    }

    fn lungeToward(g: *Game, v: View, spec: weapons.Spec, strength: f32) void {
        const m = &g.melee_state;
        const flat = (Vec3{ .x = v.forward.x, .z = v.forward.z }).normalize();
        var best: ?Vec3 = null;
        var best_d: f32 = spec.range + 3.5 * strength;

        for (g.bots.items) |b| {
            if (!b.alive()) continue;

            const to = b.body.pos.sub(g.player.pos);
            const d = to.flatLength();

            if (d > best_d or d < spec.range * 0.6) continue;

            const dir = (Vec3{ .x = to.x, .z = to.z }).scale(1 / @max(d, 0.01));

            if (dir.dot(flat) < 0.82) continue;

            best_d = d;
            best = dir;
        }

        const dir = best orelse flat;
        const speed: f32 = if (best != null) std.math.clamp((best_d - spec.range * 0.55) / 0.16, 2, 11) else 3 * strength;

        m.lunge = 0.16;
        m.lunge_vel = dir.scale(speed);
    }

    fn botsReact(g: *Game, spec: weapons.Spec) void {
        for (&g.bots.items) |*b| {
            if (!b.alive() or b.swing >= 0 or b.stagger > 0) continue;

            if (!weapons.isMelee(weapons.specs[b.weapon])) continue;

            if (b.body.pos.sub(g.player.pos).flatLength() > spec.range + 2) continue;

            if (g.rand() > 0.4) continue;

            b.guard = 0;
            b.parry = g.rand() < 0.35;
        }
    }

    fn sparks(g: *Game, at: Vec3, count: u8) void {
        const size = 0.1 + @as(f32, @floatFromInt(count)) * 0.025;

        g.explosions.spawn(.{ .pos = at, .radius = size, .life = 0.16, .total = 0.16 });
    }

    fn strike(g: *Game, v: View, spec: weapons.Spec, rarity: Rarity) void {
        const m = &g.melee_state;
        const heavy = m.kind == .heavy;
        const reach = spec.range * (if (heavy) @as(f32, 1.15) else 1);
        const cone: f32 = if (heavy) 0.42 else 0.6;
        const finisher = m.arc == 2 and !heavy;
        var damage = spec.damage * weapons.rarity_damage[@intFromEnum(rarity)];
        var push = spec.knockback;

        if (heavy) {
            damage *= 1.6 + m.power * 0.9;
            push *= 1.6 + m.power;
        } else if (finisher) {
            damage *= 1.4;
            push *= 1.5;
        }

        if (m.counter > 0) {
            damage *= 1.5;
            m.counter = 0;
            g.cueMelee(.counter);
        }

        var hits: u8 = 0;
        var healed: f32 = 0;

        for (&g.bots.items, 0..) |*b, i| {
            if (!b.alive()) continue;

            const center = b.body.pos.add(.{ .y = 1.1 });
            const to = center.sub(v.eye);
            const d = to.length();

            if (d > reach + 0.45) continue;

            const dir = to.scale(1 / @max(d, 0.01));

            if (dir.dot(v.forward) < cone) continue;

            if (movement.raycast(pieces, v.eye, dir, d - 0.4) != null) continue;

            const contact = v.eye.add(dir.scale(@max(0.3, d - 0.35)));
            const flat = (Vec3{ .x = dir.x, .z = dir.z }).normalize();
            const facing = math.flatDir(b.yaw).dot(flat.neg()) > 0.3;
            var dealt = damage;

            if (b.swing >= 0 and !b.struck and b.swing > bot_strike - 0.16 and facing) {
                g.clash(b, contact, flat);

                return;
            }

            if (b.guard >= 0 and facing) {
                if (b.parry and !heavy) {
                    m.stagger = 0.7;
                    m.kind = .none;
                    m.shake = 0.5;
                    m.hitstop = 0.07;
                    b.guard = -1;
                    b.melee_cd = 0;
                    g.sparks(contact, 6);
                    g.cueMelee(.staggered);

                    return;
                }

                dealt *= if (heavy) @as(f32, 0.6) else 0.2;
                b.guard = -1;
                g.sparks(contact, 3);
                g.cueMelee(.blocked);
            }

            g.damageBot(i, dealt, contact, false);
            b.body.vel = b.body.vel.add(flat.scale(push)).add(.{ .y = 1.6 + push * 0.18 });
            b.body.grounded = false;
            b.stagger = @max(b.stagger, if (heavy) @as(f32, 0.55) else 0.22);
            b.swing = -1;
            healed += dealt * spec.lifesteal;
            hits += 1;
            g.sparks(contact, 2);

            if (!heavy) break;
        }

        if (hits > 0) {
            m.hitstop = if (heavy) 0.11 else 0.055;
            m.shake = @max(m.shake, if (heavy) @as(f32, 0.45) else 0.22);
            g.buzz.add(if (heavy) 0.6 else 0.3, 0.5, 0.1);

            if (healed > 0) {
                g.hp = @min(max_hp, g.hp + healed);
                g.feed.spawn(.{ .kind = .health, .value = @intFromFloat(healed), .life = 1.5 });
            }

            return;
        }

        if (movement.raycast(pieces, v.eye, v.forward, reach)) |h| {
            g.sparks(v.eye.add(v.forward.scale(h.t)), 1);
            m.shake = @max(m.shake, 0.12);
        }
    }

    fn clash(g: *Game, b: *Bot, at: Vec3, flat: Vec3) void {
        const m = &g.melee_state;

        b.swing = -1;
        b.stagger = 0.35;
        b.melee_cd = 0.4;
        b.body.vel = b.body.vel.add(flat.scale(4)).add(.{ .y = 1.5 });
        g.player.vel = g.player.vel.add(flat.scale(-4));
        m.kind = .none;
        m.stagger = 0.25;
        m.hitstop = 0.09;
        m.shake = 0.5;
        g.sparks(at, 8);
        g.buzz.add(0.5, 0.5, 0.12);
        g.cueMelee(.clash);
    }

    fn botMelee(g: *Game, b: *Bot, dt: f32, dist: f32, los: bool) void {
        const spec = weapons.specs[b.weapon];

        b.melee_cd -= dt;

        if (b.swing >= 0) {
            b.swing += dt;
            b.input.forward = if (dist > spec.range * 0.7) 0.6 else 0;
            b.input.right = 0;

            if (!b.struck and b.swing >= bot_strike) {
                b.struck = true;
                g.botStrike(b, spec, dist);
            }

            if (b.swing >= bot_swing) {
                b.swing = -1;
                b.melee_cd = 0.5 + g.rand() * 0.7;
            }

            return;
        }

        if (b.guard >= 0) {
            b.guard += dt;
            b.input.forward = 0;
            b.input.right *= 0.3;

            if (b.guard > 0.8) b.guard = -1;

            return;
        }

        if (!los) return;

        b.input.forward = if (dist > spec.range * 0.85) 1 else if (dist < 1.9) -0.6 else 0;
        b.input.right = if (dist < 5) b.strafe * 0.35 else b.strafe * 0.6;

        if (dist < spec.range + 0.4 and b.melee_cd <= 0 and b.seen > bot_reaction) {
            b.swing = 0;
            b.struck = false;
        }
    }

    fn botStrike(g: *Game, b: *Bot, spec: weapons.Spec, dist: f32) void {
        const m = &g.melee_state;
        const to = g.player.center().sub(b.body.eye());
        const flat = (Vec3{ .x = to.x, .z = to.z }).normalize();

        if (g.dead > 0 or dist > spec.range + 0.5 or math.flatDir(b.yaw).dot(flat) < 0.5) return;

        const at = b.body.eye().add(to.scale(0.6));

        if (m.striking()) {
            g.clash(b, at, flat.neg());

            return;
        }

        const guarded = m.block >= 0 and math.flatDir(g.yaw).dot(flat.neg()) > 0.4;

        if (guarded and m.block <= Melee.parry_window) {
            b.stagger = 1.1;
            b.swing = -1;
            b.body.vel = b.body.vel.add(flat.scale(-3));
            m.counter = 1.2;
            m.hitstop = 0.08;
            m.shake = 0.35;
            g.sparks(at, 8);
            g.buzz.add(0.4, 0.5, 0.1);
            g.cueMelee(.parry);

            return;
        }

        if (guarded) {
            m.shake = 0.25;
            g.sparks(at, 4);
            g.cueMelee(.blocked);
            g.player.vel = g.player.vel.add(flat.scale(2.5));
        } else {
            g.player.vel = g.player.vel.add(flat.scale(spec.knockback * 0.8)).add(.{ .y = 1.5 + spec.knockback * 0.15 });
            g.player.grounded = false;
            m.kind = .none;
            m.stagger = @max(m.stagger, 0.2);
            m.shake = @max(m.shake, 0.3);
        }

        g.hurt(spec.damage * 0.55 * (if (guarded) @as(f32, 0.15) else 1), b.body.eye());
    }

    fn melee(g: *Game, v: View, spec: weapons.Spec) void {
        const wall_hit = movement.raycast(pieces, v.eye, v.forward, spec.range);
        const limit = if (wall_hit) |h| h.t else spec.range;

        if (g.hitBot(v.eye, v.forward, limit, 0.25)) |hit| {
            g.damageBot(hit.index, spec.damage, v.eye.add(v.forward.scale(hit.t)), hit.head);

            if (spec.lifesteal > 0) {
                const heal = spec.damage * spec.lifesteal;

                g.hp = @min(max_hp, g.hp + heal);
                g.feed.spawn(.{ .kind = .health, .value = @intFromFloat(heal), .life = 1.5 });
            }

            return;
        }

        if (wall_hit) |h| g.impacts.spawn(.{ .pos = v.eye.add(v.forward.scale(h.t)), .life = 1.6, .seed = g.rand() });
    }

    fn throwGrenade(g: *Game, v: View, spec: weapons.Spec, lift: f32, damage_scale: f32) void {
        g.projectiles.spawn(.{
            .kind = .grenade,
            .pos = v.eye.add(v.forward.scale(0.4)).add(v.right.scale(0.1)),
            .vel = v.forward.scale(spec.speed).add(.{ .y = lift }).add(g.player.vel.scale(0.5)),
            .life = 2.1,
            .damage = spec.damage * damage_scale,
            .splash = spec.splash,
            .knockback = spec.knockback,
            .gravity = spec.gravity,
        });
    }

    fn hitBot(g: *Game, origin: Vec3, dir: Vec3, limit: f32, pad: ?f32) ?BotHit {
        const extra = pad orelse 0;
        var best: ?BotHit = null;
        var reach = limit;

        for (g.bots.items, 0..) |b, i| {
            if (!b.alive()) continue;

            const base = b.body.pos;
            const parts = [_]struct { y: f32, r: f32, head: bool }{
                .{ .y = 0.45, .r = 0.3, .head = false },
                .{ .y = 1.12, .r = 0.36, .head = false },
                .{ .y = 1.68, .r = 0.2, .head = true },
            };

            for (parts) |part| {
                const t = geom.raySphere(origin, dir, reach, base.add(.{ .y = part.y }), part.r + extra) orelse continue;

                reach = t;
                best = .{ .index = i, .t = t, .head = part.head };
            }
        }

        return best;
    }

    pub fn damageBot(g: *Game, index: usize, amount: f32, at: Vec3, head: bool) void {
        const b = &g.bots.items[index];

        if (!b.alive()) return;

        b.hp -= amount;
        b.flash = 0.12;
        b.seen = @max(b.seen, bot_reaction);
        g.hit_marker = 0.15;
        g.hit_kill = false;
        g.popups.spawn(.{ .pos = at.add(.{ .y = 0.3 }), .value = @intFromFloat(@max(1, @round(amount))), .life = 0.8 });

        if (b.hp > 0) return;

        b.dead = 0;
        b.anim = 0;
        g.kills += 1;
        g.score += if (head) 150 else 100;
        g.hit_kill = true;
        g.buzz.add(0.2, 0.5, 0.1);
        g.feed.spawn(.{ .kind = .bot_down, .value = if (head) 150 else 100, .life = 3 });

        const ground = b.body.pos;

        g.drops.spawn(.{ .held = Held.fresh(b.weapon, if (g.rand() < 0.75) .common else .uncommon), .pos = ground.add(.{ .y = 0.55 }), .life = 40, .phase = g.rand() * tau });

        if (g.rand() < 0.35) g.pickups.spawn(.{ .kind = if (g.rand() < 0.6) .ammo else .health, .pos = ground.add(.{ .x = 0.8, .y = 0.4 }), .life = 25, .phase = g.rand() * tau });
    }

    fn groundBelow(at: Vec3) f32 {
        const down: Vec3 = .{ .y = -1 };
        const hit = movement.raycast(pieces, at, down, 40);

        return if (hit) |h| at.y - h.t else 0;
    }

    fn dropLoot(g: *Game, at: Vec3) void {
        const roll = g.rand();
        const ground: Vec3 = .{ .x = at.x, .y = groundBelow(at), .z = at.z };

        if (roll < 0.2) {
            g.drops.spawn(.{ .held = Held.fresh(g.rollWeapon(), g.rollRarity()), .pos = ground.add(.{ .y = 0.55 }), .life = 40, .phase = g.rand() * tau });
        } else if (roll < 0.5) {
            g.pickups.spawn(.{ .kind = .ammo, .pos = ground.add(.{ .y = 0.4 }), .life = 25, .phase = g.rand() * tau });
        } else if (roll < 0.62) {
            g.pickups.spawn(.{ .kind = .health, .pos = ground.add(.{ .y = 0.4 }), .life = 25, .phase = g.rand() * tau });
        }
    }

    fn hurt(g: *Game, amount: f32, from: Vec3) void {
        if (g.dead > 0) return;

        const to = from.sub(g.player.center());

        if (driving.absorb(g, amount, from)) return;

        if (god_mode) return;

        g.hp -= amount;
        g.since_hurt = 0;
        g.hurt_flash = 0.45;
        g.hurt_dir = std.math.atan2(to.x, to.z) - g.yaw;
        g.buzz.add(@min(1, 0.3 + amount / 30), 0.4, 0.22);

        if (g.hp > 0) return;

        g.hp = 0;
        g.dead = respawn_time;
        g.banner = respawn_time;
        g.banner_kind = .erased;
    }

    pub fn explode(g: *Game, at: Vec3, radius: f32, damage: f32, knockback: f32) void {
        g.explosions.spawn(.{ .pos = at, .radius = radius, .life = 1.8, .total = 1.8 });
        driving.splash(g, at, radius, damage);
        air.splash(g, at, radius, damage);

        const near = math.clamp01(1 - g.player.center().distance(at) / 25);

        if (near > 0) g.buzz.add(near, near * 0.6, 0.3 * near);

        g.blastShake(at, radius);

        for (g.bots.items, 0..) |d, i| {
            if (!d.alive()) continue;

            const f = weapons.splashFalloff(d.chest().distance(at), radius + 0.5);

            if (f > 0) g.damageBot(i, damage * f, d.chest(), false);
        }

        if (g.dead > 0) return;

        const center = g.player.center();
        const f = weapons.splashFalloff(center.distance(at), radius);

        if (f <= 0) return;

        var dir = center.sub(at).normalize();

        if (dir.length() < 0.5) dir = math.up;

        movement.launch(&g.player, dir.scale(knockback * f * 1.15).add(.{ .y = knockback * f * 0.55 }));
        g.hurt(damage * f * 0.12, at);
    }

    fn edgeAhead(pos: Vec3, input: movement.Input) bool {
        const fwd = math.flatDir(input.yaw);
        const side = fwd.cross(math.up);
        const wish = fwd.scale(input.forward).add(side.scale(input.right));

        if (wish.flatLength() < 0.1) return false;

        const ahead = pos.add(wish.normalize().scale(1.8));

        return terrain.height(ahead.x, ahead.z) < pos.y - 5 and movement.raycast(pieces, ahead.add(.{ .y = 1 }), .{ .y = -1 }, 7) == null;
    }

    fn updateFireball(g: *Game, dt: f32, c: Controls, v: View) void {
        g.fire_cd = @max(0, g.fire_cd - dt);

        if (g.fire_charges < fire_max) g.fire_charges = @min(fire_max, g.fire_charges + dt / fire_recharge);

        if (c.fireball and g.fire_charges >= 1 and g.fire_cd <= 0) {
            g.fire_held = true;
            g.fire_hold = @min(fire_charge_time, g.fire_hold + dt);

            return;
        }

        if (!g.fire_held) return;

        const power = g.fire_hold / fire_charge_time;

        g.fire_held = false;
        g.fire_hold = 0;
        g.fire_charges -= 1;
        g.fire_cd = 0.18;
        g.projectiles.spawn(.{
            .kind = .fireball,
            .pos = v.eye.add(v.forward.scale(0.45)),
            .vel = v.forward.scale(fire_speed).add(g.player.vel.scale(0.35)),
            .life = 2.5,
            .gravity = 3,
            .splash = fire_radius * (1 + 0.45 * power),
            .knockback = fire_push * (1 + 0.5 * power),
            .heading = v.forward,
        });
        g.buzz.add(0.25, 0.1, 0.08);
    }

    fn fireballBlast(g: *Game, at: Vec3, radius: f32, push: f32) void {
        g.explosions.spawn(.{ .pos = at, .radius = radius, .life = 2.0, .total = 2.0, .fire = true });
        g.blastShake(at, radius);

        const near = math.clamp01(1 - g.player.center().distance(at) / 20);

        if (near > 0) g.buzz.add(near * 0.8, near * 0.5, 0.25 * near);

        for (&g.bots.items, 0..) |*d, i| {
            if (!d.alive()) continue;

            const f = fireFalloff(d.body.center().distance(at), radius);

            if (f <= 0) continue;

            fling(&d.body, d.body.center().sub(at), push * 1.15 * f);
            g.damageBot(i, 12 * f, d.chest(), false);
        }

        if (g.dead > 0) return;

        const f = fireFalloff(g.player.center().distance(at), radius);

        if (f <= 0) return;

        fling(&g.player, g.player.center().sub(at), push * f);
        g.hurt(4 * f, at);
    }

    fn fireFalloff(dist: f32, radius: f32) f32 {
        if (dist >= radius) return 0;

        return @sqrt(1 - dist / radius);
    }

    fn fling(body: *movement.Player, away: Vec3, strength: f32) void {
        var dir = away.normalize();

        if (away.length() < 0.2) dir = math.up;

        const impulse = dir.scale(strength).add(.{ .y = strength * 0.22 });

        if (impulse.y > 0) body.vel.y = @max(body.vel.y, 0);

        movement.launch(body, impulse);
    }

    fn updateProjectiles(g: *Game, dt: f32) void {
        for (&g.projectiles.items) |*p| {
            if (!p.active) continue;

            p.life -= dt;
            p.spin += dt * 12;

            if (p.life <= 0) {
                p.active = false;

                if (p.kind == .gun) {
                    if (p.item) |item| g.drops.spawn(.{ .held = item, .pos = p.pos, .life = 40, .phase = 0 });
                }

                if (p.kind == .grenade) g.explode(p.pos, p.splash, p.damage, p.knockback);

                if (p.kind == .fireball) g.fireballBlast(p.pos, p.splash, p.knockback);

                continue;
            }

            if (p.stuck) continue;

            p.vel.y -= p.gravity * dt;

            const travel = p.vel.scale(dt);
            const len = travel.length();

            if (len < 1e-6) continue;

            const dir = travel.scale(1 / len);
            const wall = movement.raycast(pieces, p.pos, dir, len);
            var limit = if (wall) |h| h.t else len;
            var struck: ?usize = null;

            if (p.kind != .orb) {
                if (g.hitBot(p.pos, dir, limit, if (p.kind == .fireball) 0.25 else 0.05)) |hit| {
                    limit = hit.t;
                    struck = hit.index;
                }
            }

            if (p.kind == .arrow) p.heading = dir;

            if (p.kind == .gun) {
                if (struck) |i| {
                    g.damageBot(i, p.damage, p.pos.add(dir.scale(limit)), false);
                    p.vel = p.vel.scale(-0.2);
                    p.damage = 0;
                }

                if (wall) |h| {
                    const rest = p.pos.add(dir.scale(@max(0, h.t - 0.05)));

                    p.active = false;

                    if (p.item) |item| g.drops.spawn(.{ .held = item, .pos = rest.add(.{ .y = 0.45 }), .life = 40, .phase = g.rand() * tau });

                    continue;
                }

                p.pos = p.pos.add(travel);

                continue;
            }

            switch (p.kind) {
                .gun => {},
                .fireball => {
                    if (wall != null or struck != null) {
                        p.active = false;
                        g.fireballBlast(p.pos.add(dir.scale(@max(0, limit - 0.1))), p.splash, p.knockback);

                        continue;
                    }

                    p.pos = p.pos.add(travel);
                },
                .rocket => {
                    if (wall != null or struck != null) {
                        p.active = false;
                        g.explode(p.pos.add(dir.scale(@max(0, limit - 0.15))), p.splash, p.damage, p.knockback);

                        continue;
                    }

                    p.pos = p.pos.add(travel);
                },
                .grenade => {
                    if (struck != null) {
                        p.active = false;
                        g.explode(p.pos.add(dir.scale(limit)), p.splash, p.damage, p.knockback);

                        continue;
                    }

                    if (wall) |h| {
                        const vn = p.vel.dot(h.normal);

                        p.pos = p.pos.add(dir.scale(@max(0, h.t - 0.02))).add(h.normal.scale(0.12));
                        p.vel = p.vel.sub(h.normal.scale(vn * 1.55)).scale(0.62);
                    } else {
                        p.pos = p.pos.add(travel);
                    }
                },
                .arrow => {
                    if (struck) |i| {
                        p.active = false;
                        g.damageBot(i, p.damage, p.pos.add(dir.scale(limit)), false);

                        continue;
                    }

                    if (wall != null) {
                        p.pos = p.pos.add(dir.scale(limit - 0.1));
                        p.stuck = true;
                        p.life = 6;

                        continue;
                    }

                    p.pos = p.pos.add(travel);
                },
                .orb => {
                    if (g.dead <= 0) {
                        const center = g.player.center();
                        const along = std.math.clamp(center.sub(p.pos).dot(dir), 0, limit);
                        const closest = p.pos.add(dir.scale(along));

                        if (closest.distance(center) < 0.75) {
                            p.active = false;
                            g.hurt(p.damage, p.pos);

                            continue;
                        }
                    }

                    if (wall != null) {
                        p.active = false;
                        g.impacts.spawn(.{ .pos = p.pos.add(dir.scale(limit)), .life = 1, .seed = g.rand() });

                        continue;
                    }

                    p.pos = p.pos.add(travel);
                },
            }
        }
    }

    fn botWeapon(g: *Game) u8 {
        var attempt: u32 = 0;

        if (g.rand() < melee_bot_share) return weapons.swords[g.prng.random().uintLessThan(usize, weapons.swords.len)];

        while (attempt < 40) : (attempt += 1) {
            const pick = g.prng.random().uintLessThan(u8, weapons.knife);
            const spec = weapons.specs[pick];

            if (spec.fire != .hitscan or spec.charge > 0 or spec.spinup > 0 or spec.flame) continue;

            switch (spec.class) {
                .pistol, .smg, .rifle, .shotgun, .dmr, .lmg => return pick,
                else => {},
            }
        }

        return comptime weapons.indexOf("Liner");
    }

    fn pickGoal(g: *Game, near: Vec3) Vec3 {
        var attempt: u32 = 0;

        while (attempt < 8) : (attempt += 1) {
            const ang = g.rand() * tau;
            const dist = 5 + g.rand() * 12;
            const x = std.math.clamp(near.x + @sin(ang) * dist, -bounds(), bounds());
            const z = std.math.clamp(near.z + @cos(ang) * dist, -bounds(), bounds());
            const at: Vec3 = .{ .x = x, .y = terrain.height(x, z), .z = z };

            if (!movement.solidAt(pieces, at) and at.y > movement.kill_y + 6) return at;
        }

        return near;
    }

    fn turnToward(current: f32, target: f32, rate: f32) f32 {
        const d = wrapAngle(target - current);

        return current + std.math.clamp(d, -rate, rate);
    }

    fn updateBots(g: *Game, dt: f32) void {
        const wave_f: f32 = @floatFromInt(g.wave);
        const target = g.player.center();

        for (&g.bots.items) |*b| {
            if (!b.active) continue;

            b.flash = @max(0, b.flash - dt);
            b.shot = @max(0, b.shot - dt);
            b.anim += dt;

            if (b.dead >= 0) {
                b.dead += dt;
                b.input = .{ .yaw = b.yaw };

                if (b.dead > 6) b.active = false;

                continue;
            }

            if (bots_passive and !b.frozen) {
                const ahead = math.flatDir(g.yaw);
                const side = ahead.cross(math.up);
                const spot = target.add(ahead.scale(12)).add(side.scale((@as(f32, @floatFromInt(bot_index(g, b))) - 2.5) * 2.5));
                const to = spot.sub(b.body.pos);
                const far = to.flatLength() > 0.8;
                const face = target.sub(b.body.pos);

                b.yaw = std.math.atan2(-face.x, -face.z);
                b.input = .{ .yaw = b.yaw, .forward = if (far) 1 else 0 };

                if (far) b.yaw = std.math.atan2(-to.x, -to.z);

                b.input.yaw = b.yaw;

                if (edgeAhead(b.body.pos, b.input)) b.input.forward = 0;

                continue;
            }

            if (b.frozen) {
                b.input = .{ .yaw = b.yaw };
                b.seen = 1;

                continue;
            }

            if (b.stagger > 0) {
                b.stagger -= dt;
                b.swing = -1;
                b.guard = -1;
                b.input = .{ .yaw = b.yaw };

                continue;
            }

            const eye = b.body.eye();
            const to = target.sub(eye);
            const dist = @max(to.length(), 0.01);
            const dir = to.scale(1 / dist);
            const los = g.dead <= 0 and dist < 70 and movement.raycast(pieces, eye, dir, dist - 0.5) == null;

            b.seen = if (los) b.seen + dt else @max(0, b.seen - dt * 0.5);
            b.retarget -= dt;
            b.strafe_t -= dt;

            if (b.strafe_t <= 0) {
                b.strafe = if (g.rand() < 0.5) -1 else 1;
                b.strafe_t = 0.9 + g.rand() * 1.6;
            }

            var input: movement.Input = .{};

            if (los) {
                b.yaw = turnToward(b.yaw, std.math.atan2(dir.x, dir.z), dt * 6);
                b.pitch = std.math.asin(std.math.clamp(dir.y, -1, 1));
                input.forward = if (dist > 24) 1 else if (dist < 9) -0.7 else 0;
                input.right = b.strafe * 0.85;
                b.goal = g.player.pos;
            } else {
                if (b.retarget <= 0 or b.body.pos.distance(b.goal) < 2) {
                    b.goal = g.pickGoal(g.player.pos);
                    b.retarget = 2.5 + g.rand() * 2;
                }

                const go = b.goal.sub(b.body.pos);

                b.yaw = turnToward(b.yaw, std.math.atan2(go.x, go.z), dt * 5);
                b.pitch *= 0.9;
                input.forward = 1;
            }

            if (b.body.vel.flatLength() < 0.6 and (input.forward != 0 or input.right != 0)) b.stuck += dt else b.stuck = 0;

            if (b.stuck > 0.5) {
                input.jump = true;
                b.strafe = -b.strafe;
                b.retarget = 0;
                b.stuck = 0;
            }

            input.yaw = b.yaw;

            if (edgeAhead(b.body.pos, input)) {
                input.forward = 0;
                input.right = 0;
                b.retarget = 0;
            }

            b.input = input;

            if (weapons.isMelee(weapons.specs[b.weapon])) {
                g.botMelee(b, dt, dist, los);

                continue;
            }

            b.fire_cd -= dt;

            if (b.reload > 0) {
                b.reload -= dt;

                if (b.reload <= 0) b.mag = weapons.specs[b.weapon].mag;

                continue;
            }

            if (!los or b.seen < bot_reaction or b.fire_cd > 0) continue;

            const spec = weapons.specs[b.weapon];

            if (b.mag == 0) {
                b.reload = spec.reload * 1.2;

                continue;
            }

            b.mag -= 1;
            b.fire_cd = @max(spec.interval, 0.09) * (1.6 + g.rand() * 0.8);
            b.shot = 0.12;

            const right = (Vec3{ .x = @cos(b.yaw), .z = -@sin(b.yaw) }).neg();
            const muzzle = eye.add(math.flatDir(b.yaw).scale(0.6)).add(right.scale(0.18)).add(.{ .y = -0.15 });
            const spread = 0.5 + dist * 0.05 + g.player.vel.flatLength() * 0.07 - @min(wave_f * 0.012, 0.2);
            var pellet: u8 = 0;

            while (pellet < spec.pellets) : (pellet += 1) {
                const miss: Vec3 = .{ .x = (g.rand() - 0.5) * 2 * spread, .y = (g.rand() - 0.5) * 2 * spread, .z = (g.rand() - 0.5) * 2 * spread };
                const aim = target.add(miss).sub(muzzle);
                const len = aim.length();
                const shot_dir = aim.scale(1 / len);
                const wall = movement.raycast(pieces, muzzle, shot_dir, len + 30);
                const reach = if (wall) |h| h.t else len + 30;
                const along = std.math.clamp(target.sub(muzzle).dot(shot_dir), 0, reach);
                const closest = muzzle.add(shot_dir.scale(along));
                const end = muzzle.add(shot_dir.scale(@min(reach, along + 0.5)));

                g.tracers.spawn(.{ .from = muzzle, .to = if (closest.distance(target) < 0.5) end else muzzle.add(shot_dir.scale(reach)), .life = 0.07 });

                if (closest.distance(target) < 0.5 and along < reach) {
                    g.hurt(spec.damage * 0.3, muzzle);
                } else if (wall != null) {
                    g.impacts.spawn(.{ .pos = muzzle.add(shot_dir.scale(reach)), .life = 1.2, .seed = g.rand() });
                }
            }
        }
    }

    fn updatePickups(g: *Game, dt: f32) void {
        const center = g.player.center();

        for (&g.pickups.items) |*p| {
            if (!p.active) continue;

            p.life -= dt;
            p.phase += dt * 2;

            if (p.life <= 0) {
                p.active = false;

                continue;
            }

            if (g.dead > 0 or p.pos.distance(center) > 1.5) continue;

            p.active = false;

            switch (p.kind) {
                .ammo => {
                    for (&g.arsenal.slots) |*maybe| {
                        if (maybe.*) |*h| {
                            const s = h.spec();

                            h.reserve = @min(s.reserve, h.reserve + s.mag * 2);
                        }
                    }

                    g.arsenal.grenades = @min(4, g.arsenal.grenades + 1);
                    g.feed.spawn(.{ .kind = .ammo, .life = 2.5 });
                },
                .health => {
                    g.hp = @min(max_hp, g.hp + 35);
                    g.feed.spawn(.{ .kind = .health, .value = 35, .life = 2.5 });
                },
            }
        }
    }

    pub fn parkVehicles(g: *Game) void {
        driving.park(g);
        air.park(g);
    }

    pub fn spotlight(g: *Game, index: usize) void {
        const fwd = math.flatDir(g.yaw);
        const at = g.player.pos.add(fwd.scale(6.5));

        g.wave_break = 1e9;

        for (&g.vehicles) |*v| v.pos = v.pos.add(.{ .y = -50 });

        g.vehicles[index] = vehicle.spawn(@intCast(index), .{ .x = at.x, .y = terrain.height(at.x, at.z), .z = at.z }, g.yaw + 2.3);
        vehicle.settle(&g.vehicles[index], world.pieces);
    }

    pub fn garage(g: *Game, start: usize) void {
        const fwd = math.flatDir(g.yaw);
        const side = fwd.cross(math.up);
        const base = g.player.pos.add(fwd.scale(8));

        g.wave_break = 1e9;

        for (&g.vehicles, 0..) |*v, i| {
            if (i < start or i >= start + 5) {
                v.wreck = 1e9;
                v.pos = v.pos.add(.{ .y = -100 });

                continue;
            }

            const fi: f32 = @floatFromInt(i - start);
            const gap: f32 = if (v.spec().class == .car) 5.4 else 3.2;
            const at = base.add(side.scale((fi - 2) * gap));

            v.* = vehicle.spawn(@intCast(i), .{ .x = at.x, .y = terrain.height(at.x, at.z), .z = at.z }, g.yaw + std.math.pi + 0.7);
            vehicle.settle(v, world.pieces);
        }
    }

    pub fn gunEquip(g: *Game, name: []const u8) void {
        for (weapons.specs, 0..) |sp, i| {
            if (!std.ascii.eqlIgnoreCase(sp.name, name)) continue;

            if (g.arsenal.slots[0] == null or g.arsenal.slots[0].?.weapon != i) g.arsenal.slots[0] = Held.fresh(@intCast(i), .rare);

            g.arsenal.active = 0;
        }
    }

    pub fn gunTest(g: *Game, name: []const u8) void {
        var weapon: ?u8 = null;

        for (weapons.specs, 0..) |sp, i| {
            if (std.ascii.eqlIgnoreCase(sp.name, name)) weapon = @intCast(i);
        }

        const w = weapon orelse return;
        const at = g.player.pos.add(math.flatDir(g.yaw).scale(4.5)).add(math.flatDir(g.yaw + std.math.pi / 2.0).scale(-1.2));

        g.arsenal.slots[0] = Held.fresh(w, .rare);
        g.arsenal.active = 0;
        g.wave_break = 1e9;
        g.bots.spawn(.{
            .active = true,
            .body = movement.Player.spawn(.{ .x = at.x, .y = terrain.height(at.x, at.z) + 0.5, .z = at.z }),
            .prev = at,
            .yaw = g.yaw + std.math.pi * 0.6,
            .weapon = w,
            .hp = 400,
            .max_hp = 400,
        });
    }

    pub fn swordTest(g: *Game, name: []const u8) void {
        var weapon: u8 = weapons.swords[0];

        for (weapons.specs, 0..) |sp, i| {
            if (std.ascii.eqlIgnoreCase(sp.name, name)) weapon = @intCast(i);
        }

        g.arsenal.slots[0] = Held.fresh(weapon, .rare);
        g.melee_auto = std.c.getenv("DF_SWORD_AUTO") != null;
        g.arsenal.active = 0;
        g.wave_break = 1e9;

        var k: u32 = 0;

        while (k < 3) : (k += 1) {
            const ang = g.yaw + (@as(f32, @floatFromInt(k)) - 1) * 0.7;
            const at = g.player.pos.add(math.flatDir(ang).scale(7 + @as(f32, @floatFromInt(k))));

            g.bots.spawn(.{
                .active = true,
                .body = movement.Player.spawn(.{ .x = at.x, .y = terrain.height(at.x, at.z) + 0.5, .z = at.z }),
                .prev = at,
                .yaw = g.yaw + std.math.pi,
                .weapon = weapons.swords[k % weapons.swords.len],
                .hp = 400,
                .max_hp = 400,
                .seen = 1,
            });
        }
    }

    pub fn showcase(g: *Game, angle: f32) void {
        const ahead = g.player.pos.add(math.flatDir(g.yaw + angle).scale(3.2));

        g.wave_break = 1e9;
        g.bots.spawn(.{
            .body = movement.Player.spawn(.{ .x = ahead.x, .y = terrain.height(ahead.x, ahead.z), .z = ahead.z }),
            .prev = ahead,
            .yaw = g.yaw + std.math.pi + 0.5,
            .weapon = comptime weapons.indexOf("Liner"),
            .mag = 30,
            .frozen = true,
            .seen = 1,
        });
    }

    fn spawnBot(g: *Game) void {
        var at: Vec3 = g.player.pos;
        var attempt: u32 = 0;

        while (attempt < 30) : (attempt += 1) {
            const ang = g.rand() * tau;
            const dist = 32 + g.rand() * 26;
            const x = std.math.clamp(g.player.pos.x + @sin(ang) * dist, -bounds(), bounds());
            const z = std.math.clamp(g.player.pos.z + @cos(ang) * dist, -bounds(), bounds());
            const p: Vec3 = .{ .x = x, .y = terrain.height(x, z), .z = z };

            if (movement.solidAt(pieces, p) or p.y < movement.kill_y + 6) continue;

            at = p;

            break;
        }

        const weapon = g.botWeapon();
        const hp = 80 + @as(f32, @floatFromInt(g.wave)) * 8;

        g.bots.spawn(.{
            .body = movement.Player.spawn(at),
            .prev = at,
            .yaw = std.math.atan2(g.player.pos.x - at.x, g.player.pos.z - at.z),
            .hp = hp,
            .max_hp = hp,
            .weapon = weapon,
            .mag = weapons.specs[weapon].mag,
            .fire_cd = 1 + g.rand(),
            .goal = g.player.pos,
            .anim = g.rand() * 3,
        });
    }

    fn updateWaves(g: *Game, dt: f32) void {
        if (g.wave_break > 0) {
            g.wave_break -= dt;

            if (g.wave_break <= 0) {
                g.wave += 1;
                g.to_spawn = 2 + g.wave * 2;
                g.spawn_timer = 0;
                g.banner = 2.2;
                g.banner_kind = .wave_start;
            }

            return;
        }

        const alive = g.bots.countActive();

        if (g.to_spawn > 0) {
            g.spawn_timer -= dt;

            if (g.spawn_timer <= 0 and alive < max_alive) {
                g.spawnBot();
                g.to_spawn -= 1;
                g.spawn_timer = 0.9;
            }

            return;
        }

        if (alive > 0) return;

        const bonus = 250 * g.wave;

        g.score += bonus;
        g.feed.spawn(.{ .kind = .wave_clear, .value = bonus, .life = 3.5 });
        g.banner = 3;
        g.banner_kind = .wave_clear;
        g.wave_break = 4;
    }

    fn respawn(g: *Game) void {
        var best: usize = 0;
        var best_score: f32 = -1;

        for (world.spawns, 0..) |s, i| {
            var nearest: f32 = 1e9;

            for (g.bots.items) |d| {
                if (d.alive()) nearest = @min(nearest, d.body.pos.distance(s));
            }

            if (nearest > best_score) {
                best_score = nearest;
                best = i;
            }
        }

        g.player = movement.Player.spawn(world.spawns[best]);
        g.prev_pos = g.player.pos;
        g.yaw = world.spawn_yaws[best];
        g.pitch = 0;
        g.recoil = 0;
        g.recoil_yaw = 0;
        g.hp = max_hp;
        g.dead = 0;
        g.arsenal = .{};
    }
};
