const std = @import("std");
const rl = @import("raylib");
const shared = @import("shared");
const assets = @import("assets.zig");
const settings = @import("settings.zig");
const game_mod = @import("game.zig");
const driving = @import("driving.zig");

const Vec3 = shared.math.Vec3;
const weapons = shared.weapons;
const terrain = shared.terrain;
const vehicle = shared.vehicle;
const Game = game_mod.Game;

pub const Clip = enum {
    pistol,
    magnum,
    smg,
    rifle,
    lmg,
    spinner,
    dmr,
    sniper,
    shotgun,
    cannon,
    nitro,
    launcher,
    rocket,
    rail,
    torch,
    bow,
    crossbow,
    swing1,
    swing2,
    swing3,
    swing4,
    clash1,
    clash2,
    clash3,
    clash4,
    slash,
    blunt,
    block,
    parry,
    reload_small,
    reload_rifle,
    pump,
    swap,
    dry,
    pickup,
    step_sand_L1,
    step_sand_L2,
    step_sand_L3,
    step_sand_R1,
    step_sand_R2,
    step_sand_R3,
    step_stone_L1,
    step_stone_L2,
    step_stone_L3,
    step_stone_R1,
    step_stone_R2,
    step_stone_R3,
    jump,
    land,
    hitmark,
    headshot,
    hurt,
    bot_hit,
    bot_down,
    boom1,
    boom2,
    boom_big,
    bounce,
    fireball,
    fire_blast,
    door_open,
    door_close,
    skid,
    crash,
    crash_metal,
    ui_hover,
    ui_click,
    ui_back,
    ui_toast,
    ui_error,
};

pub const Ui = enum { hover, click, back, toast, err };

const clip_count = @typeInfo(Clip).@"enum".field_names.len;
const voices = 5;

const Bank = struct {
    sounds: [voices]rl.Sound = undefined,
    count: u8 = 0,
    next: u8 = 0,
    last: f64 = -1,
};

const Listener = struct {
    pos: Vec3 = .{},
    right: Vec3 = .{ .x = 1 },
};

var ready = false;
var banks: [clip_count]Bank = @splat(.{});
var engine: ?rl.Music = null;
var tank_engine: ?rl.Music = null;
var listener: Listener = .{};
var rng = std.Random.DefaultPrng.init(0x5f3759df);

const Memory = struct {
    slot: u8 = 255,
    weapon: u8 = 255,
    mag: u16 = 0,
    reloading: bool = false,
    switching: bool = false,
    bob_step: i64 = 0,
    grounded: bool = true,
    fall: f32 = 0,
    hit_marker: f32 = 0,
    hurt_flash: f32 = 0,
    melee_t: f32 = 0,
    melee_kind: game_mod.Swing = .none,
    melee_struck: bool = false,
    cue_t: f32 = 0,
    cue: game_mod.Cue = .none,
    seat: ?usize = null,
    speed: f32 = 0,
    skid_cd: f32 = 0,
    boosting: bool = false,
    bot_shot: [16]f32 = @splat(0),
    bot_hp: [16]f32 = @splat(0),
    bot_dead: [16]f32 = @splat(-1),
    bot_swing: [16]f32 = @splat(-1),
    blast: [16]bool = @splat(false),
    blast_pos: [16]Vec3 = @splat(.{}),
    proj: [96]bool = @splat(false),
    proj_vy: [96]f32 = @splat(0),
    feed: [8]f32 = @splat(0),
};

var mem: Memory = .{};

fn fileName(c: Clip) []const u8 {
    return switch (c) {
        .swap => "switch",
        else => @tagName(c),
    };
}

fn polyphony(c: Clip) u8 {
    return switch (c) {
        .pistol, .magnum, .smg, .rifle, .lmg, .spinner, .dmr, .shotgun, .torch => voices,
        .step_sand_L1, .step_sand_L2, .step_sand_L3, .step_sand_R1, .step_sand_R2, .step_sand_R3 => 2,
        .step_stone_L1, .step_stone_L2, .step_stone_L3, .step_stone_R1, .step_stone_R2, .step_stone_R3 => 2,
        .ui_hover, .ui_click, .ui_back, .ui_toast, .ui_error, .reload_small, .reload_rifle, .pump, .swap, .door_open, .door_close => 1,
        else => 3,
    };
}

pub fn init() void {
    if (std.c.getenv("DF_MUTE") != null) return;

    if (std.c.getenv("DISPLAY")) |d| {
        if (std.mem.eql(u8, std.mem.sliceTo(d, 0), ":77")) return;
    }

    rl.InitAudioDevice();

    if (!rl.IsAudioDeviceReady()) return;

    var buf: [512]u8 = undefined;

    for (std.enums.values(Clip), 0..) |c, i| {
        var sub: [64]u8 = undefined;
        const rel = std.fmt.bufPrint(&sub, "sounds/{s}.ogg", .{fileName(c)}) catch "";
        const path = assets.file(&buf, rel);
        const base = rl.LoadSound(path.ptr);

        if (base.frameCount > 0) {
            const bank = &banks[i];
            const n = polyphony(c);

            bank.sounds[0] = base;
            bank.count = 1;

            while (bank.count < n) : (bank.count += 1) bank.sounds[bank.count] = rl.LoadSoundAlias(base);
        }
    }

    engine = loadLoop(&buf, "sounds/engine.ogg");
    tank_engine = loadLoop(&buf, "sounds/tank_engine.ogg");
    ready = true;
}

fn loadLoop(buf: []u8, rel: []const u8) ?rl.Music {
    const path = assets.file(buf, rel);
    var m = rl.LoadMusicStream(path.ptr);

    if (m.frameCount == 0) return null;

    m.looping = true;

    return m;
}

pub fn deinit() void {
    if (!ready) return;

    for (&banks) |*b| {
        if (b.count == 0) continue;

        var k: u8 = 1;

        while (k < b.count) : (k += 1) rl.UnloadSoundAlias(b.sounds[k]);

        rl.UnloadSound(b.sounds[0]);
    }

    if (engine) |m| rl.UnloadMusicStream(m);

    if (tank_engine) |m| rl.UnloadMusicStream(m);

    rl.CloseAudioDevice();
    ready = false;
}

fn rand() f32 {
    return rng.random().float(f32);
}

fn emit(c: Clip, volume: f32, pitch: f32, pan: f32) void {
    if (!ready or volume <= 0.005) return;

    const bank = &banks[@intFromEnum(c)];

    if (bank.count == 0) return;

    const now = rl.GetTime();

    if (now - bank.last < 0.025) return;

    bank.last = now;

    const s = bank.sounds[bank.next];

    bank.next = (bank.next + 1) % bank.count;
    rl.SetSoundVolume(s, std.math.clamp(volume, 0, 1));
    rl.SetSoundPitch(s, pitch);
    rl.SetSoundPan(s, std.math.clamp(pan, -1, 1));
    rl.PlaySound(s);
}

fn at(c: Clip, pos: Vec3, volume: f32, reach: f32, vary: f32) void {
    const to = pos.sub(listener.pos);
    const d = to.length();

    if (d > reach * 6) return;

    const fall = 1 / (1 + (d / reach) * (d / reach));
    const pan = if (d > 0.5) to.scale(1 / d).dot(listener.right) * 0.75 else 0;
    const pitch = 1 + (rand() - 0.5) * vary;

    emit(c, volume * fall * settings.volume(.sfx), pitch, pan);
}

fn near(c: Clip, volume: f32, vary: f32) void {
    emit(c, volume * settings.volume(.sfx), 1 + (rand() - 0.5) * vary, 0);
}

pub fn ui(kind: Ui) void {
    const c: Clip = switch (kind) {
        .hover => .ui_hover,
        .click => .ui_click,
        .back => .ui_back,
        .toast => .ui_toast,
        .err => .ui_error,
    };

    emit(c, settings.volume(.ui), 1, 0);
}

fn gunClip(weapon: u8) Clip {
    const s = weapons.specs[weapon];

    if (std.mem.eql(u8, s.name, "Spinner")) return .spinner;

    if (std.mem.eql(u8, s.name, "Rail")) return .rail;

    if (s.flame) return .torch;

    return switch (s.class) {
        .pistol => if (s.damage >= 45) .magnum else .pistol,
        .smg => .smg,
        .rifle => .rifle,
        .dmr => .dmr,
        .sniper => .sniper,
        .shotgun => .shotgun,
        .lmg => .lmg,
        .launcher => if (s.fire == .rocket) .rocket else .launcher,
        .bow => .bow,
        .crossbow => .crossbow,
        .special => .rail,
        .melee => .swing1,
    };
}

fn gunVolume(c: Clip) f32 {
    return switch (c) {
        .torch => 0.35,
        .spinner => 0.6,
        .bow, .crossbow => 0.8,
        .pistol, .smg => 0.85,
        else => 1,
    };
}

fn reloadClip(weapon: u8) ?Clip {
    const s = weapons.specs[weapon];

    return switch (s.class) {
        .pistol, .smg => .reload_small,
        .shotgun => .pump,
        .bow, .crossbow, .melee => null,
        else => .reload_rifle,
    };
}

fn swingClip() Clip {
    return @enumFromInt(@intFromEnum(Clip.swing1) + rng.random().uintLessThan(u8, 4));
}

fn clashClip() Clip {
    return @enumFromInt(@intFromEnum(Clip.clash1) + rng.random().uintLessThan(u8, 4));
}

fn stepClip(stone: bool, left: bool) Clip {
    const base: u8 = if (stone) @intFromEnum(Clip.step_stone_L1) else @intFromEnum(Clip.step_sand_L1);

    return @enumFromInt(base + (if (left) @as(u8, 0) else 3) + rng.random().uintLessThan(u8, 3));
}

fn onStone(p: Vec3) bool {
    if (p.y - terrain.height(p.x, p.z) > 0.08) return true;

    return terrain.roadDistance(p.x, p.z) < terrain.road_half - 0.5;
}

pub fn update(g: *const Game, dt: f32, fire_pressed: bool) void {
    if (!ready) return;

    const v = g.view();

    listener = .{ .pos = v.eye, .right = v.right };

    player(g, fire_pressed);
    bots(g);
    blasts(g);
    projectiles(g);
    melee(g);
    feed(g);
    vehicles(g, dt);
}

fn player(g: *const Game, fire_pressed: bool) void {
    const a = g.arsenal;
    const held = a.current();

    if (a.active == mem.slot and held.weapon == mem.weapon and held.mag < mem.mag and a.reloading <= 0) {
        const shots = @min(mem.mag - held.mag, 3);
        const c = gunClip(held.weapon);
        var k: u16 = 0;

        while (k < shots) : (k += 1) near(c, gunVolume(c), 0.08);
    }

    if (weapons.specs[held.weapon].fire != .melee and fire_pressed and held.mag == 0 and held.reserve == 0) near(.dry, 0.7, 0.05);

    const reloading = a.reloading > 0;

    if (reloading and !mem.reloading) {
        if (reloadClip(held.weapon)) |c| near(c, 0.7, 0.04);
    }

    const switching = a.switching > 0;

    if (switching and !mem.switching) near(.swap, 0.6, 0.05);

    mem.slot = a.active;
    mem.weapon = held.weapon;
    mem.mag = held.mag;
    mem.reloading = reloading;
    mem.switching = switching;

    if (driving.driving()) {
        mem.grounded = true;
        mem.fall = 0;
    } else {
        const step: i64 = @intFromFloat(@floor(g.bob / std.math.pi));
        const feet = g.player.pos;

        if (step != mem.bob_step and g.player.grounded) near(stepClip(onStone(feet), @mod(step, 2) == 0), 0.5, 0.12);

        mem.bob_step = step;

        if (mem.grounded and !g.player.grounded and g.player.vel.y > 2) near(.jump, 0.55, 0.1);

        if (!mem.grounded and g.player.grounded and mem.fall < -4) near(.land, std.math.clamp(-mem.fall / 14, 0.3, 1), 0.08);

        mem.grounded = g.player.grounded;
        mem.fall = g.player.vel.y;
    }

    if (g.hit_marker > mem.hit_marker + 0.01) {
        if (g.hit_kill) near(.headshot, 0.7, 0) else near(.hitmark, 0.65, 0.05);
    }

    mem.hit_marker = g.hit_marker;

    if (g.hurt_flash > mem.hurt_flash + 0.05) near(.hurt, 0.8, 0.1);

    mem.hurt_flash = g.hurt_flash;
}

fn bots(g: *const Game) void {
    for (g.bots.items, 0..) |b, i| {
        if (!b.active) {
            mem.bot_dead[i] = -1;
            mem.bot_shot[i] = 0;
            mem.bot_hp[i] = 0;
            mem.bot_swing[i] = -1;

            continue;
        }

        const chest = b.chest();

        if (b.shot > mem.bot_shot[i] + 0.01) {
            const c = gunClip(b.weapon);

            at(c, chest, gunVolume(c) * 0.9, 22, 0.1);
        }

        if (b.dead < 0 and b.hp < mem.bot_hp[i] - 0.5) at(.bot_hit, chest, 0.6, 14, 0.15);

        if (b.dead >= 0 and mem.bot_dead[i] < 0) at(.bot_down, b.body.pos, 0.8, 16, 0.1);

        if (b.swing >= 0 and mem.bot_swing[i] < 0) at(swingClip(), chest, 0.7, 10, 0.15);

        mem.bot_shot[i] = b.shot;
        mem.bot_hp[i] = b.hp;
        mem.bot_dead[i] = b.dead;
        mem.bot_swing[i] = b.swing;
    }
}

fn blasts(g: *const Game) void {
    for (g.explosions.items, 0..) |e, i| {
        const fresh = e.active and (!mem.blast[i] or e.pos.distance(mem.blast_pos[i]) > 0.01);

        if (fresh and e.radius >= 0.6) {
            if (e.fire) {
                at(.fire_blast, e.pos, 1, 30, 0.1);
            } else if (e.radius >= 5) {
                at(.boom_big, e.pos, 1, 45, 0.08);
                at(.boom1, e.pos, 0.7, 30, 0.1);
            } else {
                at(if (rand() < 0.5) .boom1 else .boom2, e.pos, 1, 35, 0.12);
            }
        }

        mem.blast[i] = e.active;
        mem.blast_pos[i] = e.pos;
    }
}

fn projectiles(g: *const Game) void {
    for (g.projectiles.items, 0..) |p, i| {
        if (p.active and !mem.proj[i]) {
            switch (p.kind) {
                .fireball => at(.fireball, p.pos, 0.8, 12, 0.1),
                .rocket => if (driving.inTank(g)) at(.cannon, p.pos, 1, 40, 0.05),
                else => {},
            }
        }

        if (p.active and p.kind == .grenade and mem.proj[i] and mem.proj_vy[i] < -2.5 and p.vel.y > 0.5) at(.bounce, p.pos, 0.6, 10, 0.2);

        mem.proj[i] = p.active;
        mem.proj_vy[i] = p.vel.y;
    }
}

fn melee(g: *const Game) void {
    const m = g.melee_state;

    if (m.kind != .none and (mem.melee_kind == .none or m.t < mem.melee_t - 0.01)) {
        const c = swingClip();

        if (m.kind == .heavy) emit(c, 0.9 * settings.volume(.sfx), 0.82, 0) else near(c, 0.75, 0.12);
    }

    if (m.struck and !mem.melee_struck and g.hit_marker > 0.01) near(if (m.kind == .heavy) .blunt else .slash, 0.8, 0.1);

    if (m.cue != .none and (m.cue != mem.cue or m.cue_t > mem.cue_t + 0.01)) {
        switch (m.cue) {
            .parry => near(.parry, 0.9, 0.05),
            .blocked => near(.block, 0.8, 0.1),
            .clash => near(clashClip(), 0.9, 0.08),
            .counter => near(.slash, 1, 0.05),
            .staggered => near(.blunt, 0.8, 0.1),
            .none => {},
        }
    }

    mem.melee_kind = m.kind;
    mem.melee_t = m.t;
    mem.melee_struck = m.struck;
    mem.cue = m.cue;
    mem.cue_t = m.cue_t;
}

fn feed(g: *const Game) void {
    for (g.feed.items, 0..) |f, i| {
        if (i >= mem.feed.len) break;

        if (f.active and f.life > mem.feed[i] + 0.01) {
            switch (f.kind) {
                .weapon, .ammo, .health => near(.pickup, 0.7, 0.05),
                else => {},
            }
        }

        mem.feed[i] = if (f.active) f.life else 0;
    }
}

fn vehicles(g: *const Game, dt: f32) void {
    const air = @import("air.zig");

    if (air.flying()) {
        const k = air.engineLevel();
        const vol = settings.volume(.sfx);

        if (air.isHeli()) {
            const chop = 0.75 + 0.25 * @abs(@sin(g.time * 22));

            loop(&tank_engine, &engine, 1.05 + k * 0.4, 0.55 * vol * chop);
        } else {
            loop(&tank_engine, &engine, 1.3 + k * 1.1, 0.6 * vol);
        }

        return;
    }

    const seat = driving.seat;

    if (seat != mem.seat) {
        const idx = seat orelse mem.seat;

        if (idx) |i| {
            const v = g.vehicles[i];

            switch (v.spec().class) {
                .car, .tank => near(if (seat != null) .door_open else .door_close, 0.7, 0.05),
                else => near(.swap, 0.4, 0.1),
            }
        }

        mem.speed = 0;
    }

    mem.seat = seat;
    mem.skid_cd = @max(0, mem.skid_cd - dt);

    const i = seat orelse {
        stopLoops();

        return;
    };
    const v = g.vehicles[i];
    const s = v.spec();
    const speed = @abs(v.speed);
    const frac = std.math.clamp(speed / @max(s.top_speed, 1), 0, 1);

    if (mem.speed - speed > 7) near(if (s.class == .car or s.class == .tank) .crash_metal else .crash, std.math.clamp((mem.speed - speed) / 18, 0.4, 1), 0.1);

    if (@abs(v.side) > 3 and speed > 8 and mem.skid_cd <= 0 and s.class != .tank) {
        near(.skid, 0.6, 0.1);
        mem.skid_cd = 0.35;
    }

    mem.speed = speed;

    if (v.boosting and !mem.boosting) near(.nitro, 0.9, 0.06);

    mem.boosting = v.boosting;

    const vol = settings.volume(.sfx);

    switch (s.class) {
        .cycle => stopLoops(),
        .tank => loop(&tank_engine, &engine, 0.75 + frac * 0.5, 0.55 * vol),
        .car => loop(&engine, &tank_engine, 0.7 + frac * 1.0, 0.5 * vol),
        .bike => loop(&engine, &tank_engine, 1.15 + frac * 1.25, 0.45 * vol),
        .scooter => loop(&engine, &tank_engine, 1.5 + frac * 0.9, 0.3 * vol),
    }
}

fn loop(active: *?rl.Music, other: *?rl.Music, pitch: f32, volume: f32) void {
    if (other.*) |m| {
        if (rl.IsMusicStreamPlaying(m)) rl.StopMusicStream(m);
    }

    const m = active.* orelse return;

    if (!rl.IsMusicStreamPlaying(m)) rl.PlayMusicStream(m);

    rl.SetMusicPitch(m, pitch);
    rl.SetMusicVolume(m, volume);
    rl.UpdateMusicStream(m);
}

fn stopLoops() void {
    if (engine) |m| {
        if (rl.IsMusicStreamPlaying(m)) rl.StopMusicStream(m);
    }

    if (tank_engine) |m| {
        if (rl.IsMusicStreamPlaying(m)) rl.StopMusicStream(m);
    }
}
