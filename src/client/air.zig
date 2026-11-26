const std = @import("std");
const rl = @import("raylib");
const shared = @import("shared");
const gfx = @import("gfx.zig");
const mesh = @import("mesh.zig");
const ui = @import("ui.zig");
const assets = @import("assets.zig");
const game_mod = @import("game.zig");
const driving = @import("driving.zig");
const models_mod = @import("models.zig");

const math = shared.math;
const terrain = shared.terrain;
const world = shared.world;
const movement = shared.movement;
const geom = shared.geom;
const Vec3 = math.Vec3;
const vec = math.vec;
const Basis = mesh.Basis;
const Game = game_mod.Game;
const Controls = game_mod.Controls;
const View = game_mod.View;

pub const Kind = enum { jet, heli };

pub const Spec = struct {
    name: [:0]const u8,
    dir: [:0]const u8,
    kind: Kind,
    hp: f32,
    top: f32,
    stall: f32 = 0,
    agility: f32,
    missiles: u8 = 0,
    rockets: u8 = 0,
    radius: f32,
    height: f32,
    rotor: Vec3 = .{},
    tail: ?Vec3 = null,
    gun: f32 = 0.06,
};

pub const specs = [_]Spec{
    .{ .name = "Raptor", .dir = "raptor", .kind = .jet, .hp = 900, .top = 84, .stall = 27, .agility = 1.25, .missiles = 4, .radius = 8, .height = 4.6 },
    .{ .name = "Viper", .dir = "su57", .kind = .jet, .hp = 900, .top = 87, .stall = 27, .agility = 1.3, .missiles = 4, .radius = 8.5, .height = 3.8 },
    .{ .name = "Falcon", .dir = "mig29", .kind = .jet, .hp = 800, .top = 81, .stall = 26, .agility = 1.35, .missiles = 2, .radius = 7.5, .height = 3.9 },
    .{ .name = "Tomcat", .dir = "f14", .kind = .jet, .hp = 950, .top = 81, .stall = 29, .agility = 1.1, .missiles = 4, .radius = 8.5, .height = 4.9 },
    .{ .name = "Kestrel", .dir = "rafale", .kind = .jet, .hp = 850, .top = 84, .stall = 26, .agility = 1.3, .missiles = 3, .radius = 7.5, .height = 5.9 },
    .{ .name = "Warthog", .dir = "a10", .kind = .jet, .hp = 1500, .top = 62, .stall = 22, .agility = 0.95, .missiles = 2, .rockets = 12, .radius = 8, .height = 4.7, .gun = 0.035 },
    .{ .name = "Hopper", .dir = "harrier", .kind = .jet, .hp = 750, .top = 67, .stall = 17, .agility = 1.15, .missiles = 2, .rockets = 8, .radius = 6.5, .height = 4.1 },
    .{ .name = "Shrike", .dir = "su47", .kind = .jet, .hp = 900, .top = 84, .stall = 27, .agility = 1.4, .missiles = 3, .radius = 9.5, .height = 5.5 },
    .{ .name = "Wyvern", .dir = "wyvern", .kind = .jet, .hp = 850, .top = 90, .stall = 29, .agility = 1.3, .missiles = 4, .radius = 8, .height = 3.5 },
    .{ .name = "Lancer", .dir = "b1", .kind = .jet, .hp = 2600, .top = 70, .stall = 30, .agility = 0.6, .rockets = 24, .radius = 14, .height = 6.3, .gun = 0.12 },
    .{ .name = "Talon", .dir = "ka52", .kind = .heli, .hp = 1300, .top = 44, .agility = 1, .missiles = 2, .rockets = 16, .radius = 7, .height = 4.2, .rotor = .{ .y = 3.436, .z = 0.043 } },
    .{ .name = "Mule", .dir = "uh60", .kind = .heli, .hp = 1600, .top = 38, .agility = 0.8, .rockets = 8, .radius = 8, .height = 5, .rotor = .{ .y = 3.216 } },
    .{ .name = "Sparrow", .dir = "md500", .kind = .heli, .hp = 700, .top = 50, .agility = 1.4, .rockets = 6, .radius = 4.5, .height = 3.5, .rotor = .{ .y = 2.916, .z = 0.662 }, .tail = .{ .x = 0.146, .y = 2.021, .z = -3.994 } },
};

pub const count = specs.len;

const wreck_time: f32 = 12;
const airspace: f32 = 260;

fn outside(p: Vec3) f32 {
    return @max(@abs(p.x), @abs(p.z)) - terrain.play;
}

fn blocked(a: Craft) bool {
    const fwd = math.flatDir(a.yaw);
    const reach = @max(40, a.speed * 1.8);
    var t: f32 = 10;

    while (t <= reach) : (t += 10) {
        const p = a.pos.add(fwd.scale(t));

        if (terrain.height(p.x, p.z) > a.pos.y - 6) return true;
    }

    const from = a.pos.add(.{ .y = a.spec().height * 0.5 });

    return hitsWorld(from, fwd, reach) or hitsWorld(from.sub(.{ .y = 8 }), fwd, reach);
}

fn hitsWorld(from: Vec3, dir: Vec3, len: f32) bool {
    const hit = movement.raycast(world.pieces, from, dir, len) orelse return false;

    return outside(from.add(dir.scale(hit.t))) < -2.5;
}

fn homeward(p: Vec3, want: f32) f32 {
    const w = math.clamp01((outside(p) + 90) / 130);

    if (w <= 0) return want;

    const back = std.math.atan2(-p.x, -p.z);
    const d = std.math.atan2(@sin(back - want), @cos(back - want));

    return want + d * w;
}

pub fn leaving() bool {
    const a = current() orelse return false;

    return outside(a.pos) > 0;
}
const respawn_time: f32 = 20;

pub const Craft = struct {
    kind: u8,
    pos: Vec3 = .{},
    prev: Vec3 = .{},
    vel: Vec3 = .{},
    yaw: f32 = 0,
    pitch: f32 = 0,
    roll: f32 = 0,
    speed: f32 = 0,
    throttle: f32 = 0,
    hp: f32 = 0,
    wreck: f32 = 0,
    home: Vec3 = .{},
    home_yaw: f32 = 0,
    grounded: bool = true,
    rotor: f32 = 0,
    lift: f32 = 0,
    gun_cd: f32 = 0,
    missile_cd: f32 = 0,
    rocket_cd: f32 = 0,
    missiles: u8 = 0,
    rockets: u8 = 0,
    reload: f32 = 0,
    since_hurt: f32 = 99,
    respawn: f32 = 0,
    active: bool = false,
    remote: bool = false,

    pub fn spec(c: Craft) Spec {
        return specs[c.kind];
    }

    pub fn alive(c: Craft) bool {
        return c.active and c.hp > 0;
    }

    pub fn forward(c: Craft) Vec3 {
        return math.lookDir(c.yaw, c.pitch);
    }

    pub fn basis(c: Craft) Basis {
        return orient(c.yaw, c.pitch, c.roll);
    }

    pub fn center(c: Craft) Vec3 {
        return c.pos.add(.{ .y = c.spec().height * 0.45 });
    }
};

const Missile = struct {
    active: bool = false,
    pos: Vec3 = .{},
    vel: Vec3 = .{},
    life: f32 = 0,
    target: ?Target = null,
};

const Target = union(enum) {
    vehicle: usize,
    craft: usize,
};

const Art = struct {
    body: rl.Model,
    rotor: ?rl.Model = null,
    tail: ?rl.Model = null,
    span: f32 = 0,
    nose: f32 = 0,
    rear: f32 = 0,
};

pub var crafts: [24]Craft = @splat(.{ .kind = 0 });
pub var seat: ?usize = null;
pub var autofly = false;
pub var autofire = false;
var art: [count]?Art = @splat(null);
var missiles: [16]Missile = @splat(.{});
var lock: ?Target = null;
var lock_time: f32 = 0;
var cam_pos: Vec3 = .{};
var cam_focus: Vec3 = .{};
var cam_ready = false;
var last_aim = false;
var last_fire_alt = false;

pub fn flying() bool {
    return seat != null;
}

pub fn current() ?Craft {
    const i = seat orelse return null;

    return crafts[i];
}

fn orient(yaw: f32, pitch: f32, roll: f32) Basis {
    const f = math.lookDir(yaw, pitch);
    var x0 = math.up.cross(f);

    if (x0.length() < 1e-4) x0 = .{ .x = 1 };

    x0 = x0.normalize();

    const up0 = f.cross(x0);
    const c = @cos(roll);
    const s = @sin(roll);

    return .{ .x = x0.scale(c).add(up0.scale(s)), .y = up0.scale(c).sub(x0.scale(s)), .z = f };
}

fn rotate(v: Vec3, axis: Vec3, angle: f32) Vec3 {
    const c = @cos(angle);
    const s = @sin(angle);

    return v.scale(c).add(axis.cross(v).scale(s)).add(axis.scale(axis.dot(v) * (1 - c)));
}

fn spin(b: Basis, axis: Vec3, angle: f32) Basis {
    return .{ .x = rotate(b.x, axis, angle), .y = rotate(b.y, axis, angle), .z = rotate(b.z, axis, angle) };
}

fn local(c: Craft, b: Basis, p: Vec3) Vec3 {
    _ = c;

    return b.x.scale(p.x).add(b.y.scale(p.y)).add(b.z.scale(p.z));
}

pub fn load() void {
    for (specs, 0..) |s, i| {
        var buf: [512]u8 = undefined;
        const body_path = assets.file(&buf, std.fmt.bufPrint(buf[256..], "air/{s}/body.glb", .{s.dir}) catch continue);

        if (!assets.exists(body_path)) continue;

        var a: Art = .{ .body = rl.LoadModel(body_path.ptr) };

        if (a.body.meshCount == 0) continue;

        const box = rl.GetModelBoundingBox(a.body);

        a.span = @max(@abs(box.min.x), @abs(box.max.x));
        a.nose = box.max.z;
        a.rear = -box.min.z;

        mesh.smoothModel(a.body, 38);

        var rb: [512]u8 = undefined;
        const rotor_path = assets.file(&rb, std.fmt.bufPrint(rb[256..], "air/{s}/rotor.glb", .{s.dir}) catch "");

        if (s.kind == .heli and assets.exists(rotor_path)) a.rotor = rl.LoadModel(rotor_path.ptr);

        var tb: [512]u8 = undefined;
        const tail_path = assets.file(&tb, std.fmt.bufPrint(tb[256..], "air/{s}/tail.glb", .{s.dir}) catch "");

        if (s.tail != null and assets.exists(tail_path)) a.tail = rl.LoadModel(tail_path.ptr);

        art[i] = a;
    }
}

pub fn dropUnused() void {
    var used: [count]bool = @splat(false);

    for (crafts) |c| {
        if (c.active) used[c.kind] = true;
    }

    for (&art, 0..) |*slot, i| {
        if (used[i]) continue;

        const a = slot.* orelse continue;

        rl.UnloadModel(a.body);

        if (a.rotor) |m| rl.UnloadModel(m);

        if (a.tail) |m| rl.UnloadModel(m);

        slot.* = null;
    }
}

fn place(slot: usize, kind: u8, pos: Vec3, yaw: f32) void {
    const s = specs[kind];

    crafts[slot] = .{
        .kind = kind,
        .pos = pos,
        .prev = pos,
        .yaw = yaw,
        .hp = s.hp,
        .home = pos,
        .home_yaw = yaw,
        .missiles = s.missiles,
        .rockets = s.rockets,
        .active = true,
    };
}

fn halfSpan(kind: u8) f32 {
    if (art[kind]) |a| return a.span;

    return specs[kind].radius * 0.9;
}

fn noseLen(kind: u8) f32 {
    if (art[kind]) |a| return a.nose;

    return specs[kind].radius;
}

fn rearLen(kind: u8) f32 {
    if (art[kind]) |a| return a.rear;

    return specs[kind].radius;
}

fn footprint(kind: u8, x: f32, z: f32, yaw: f32) [5]Vec3 {
    const f = math.flatDir(yaw);
    const side = vec(f.z, 0, -f.x);
    const c = vec(x, 0, z);
    const nose = noseLen(kind) * 0.7;
    const rear = rearLen(kind) * 0.5;
    const wing = halfSpan(kind) * 0.45;

    return .{ c, c.add(f.scale(nose)), c.sub(f.scale(rear)).add(side.scale(wing)), c.sub(f.scale(rear)).sub(side.scale(wing)), c.sub(f.scale(rear)) };
}

fn rest(kind: u8, x: f32, z: f32, yaw: f32) f32 {
    var top: f32 = -1e9;

    for (footprint(kind, x, z, yaw)) |p| top = @max(top, groundAt(p.x, p.z));

    return top;
}

fn spotFree(kind: u8, x: f32, z: f32, yaw: f32, level: f32) bool {
    const f = math.flatDir(yaw);
    const side = vec(f.z, 0, -f.x);
    const c = vec(x, 0, z);
    const reach = [_]Vec3{ f.scale(noseLen(kind)), f.scale(-rearLen(kind)), side.scale(halfSpan(kind)), side.scale(-halfSpan(kind)), .{} };
    const bound = terrain.play - 6;

    for (reach) |o| {
        const p = c.add(o);
        const h = groundAt(p.x, p.z);

        if (@abs(p.x) > bound or @abs(p.z) > bound) return false;

        if (h < level - 2 or h > level + 2) return false;

        if (movement.raycast(world.pieces, vec(p.x, h + 30, p.z), vec(0, -1, 0), 29.6)) |_| return false;
    }

    return true;
}

fn overlaps(slot: usize, kind: u8, x: f32, z: f32) bool {
    const reach = @max(halfSpan(kind), @max(noseLen(kind), rearLen(kind)));

    for (crafts[0..slot]) |o| {
        if (!o.active) continue;

        const other = @max(halfSpan(o.kind), @max(noseLen(o.kind), rearLen(o.kind)));

        if (vec(x, 0, z).distance(vec(o.pos.x, 0, o.pos.z)) < (reach + other) * 0.72 + 2) return true;
    }

    return false;
}

fn groundAt(x: f32, z: f32) f32 {
    const h = terrain.height(x, z);

    if (terrain.runwayMask(x, z) > 0.05) return @max(h, terrain.height(terrain.runway[0], terrain.runway[1]) + 0.09);

    return h;
}

pub fn park(g: *Game) void {
    _ = g;

    seat = null;

    for (&crafts) |*c| c.active = false;

    const flies = if (shared.maps.current()) |d| d.aircraft else terrain.current == .conquest or terrain.current == .facility or terrain.current == .valley;

    if (!flies) return;

    const r = terrain.runway;
    const level = groundAt(r[0], r[1]);
    var slot: usize = 0;
    const inward: f32 = if (r[0] > 0) -1 else 1;
    var spare: f32 = r[0] + inward * (r[2] - 6);

    for (terrain.helipads, 0..) |p, i| {
        const kind: u8 = @intCast(10 + i);

        place(slot, kind, vec(p[0], rest(kind, p[0], p[1], std.math.pi * 0.5), p[1]), std.math.pi * 0.5);
        slot += 1;
    }

    var k: u8 = 0;

    while (k < 10) : (k += 1) {
        var done = false;

        for ([_]f32{ 0, 1, 2 }) |row| {
            for ([_]f32{ -1, 1 }) |sd| {
                if (done) break;

                const yaw: f32 = if (sd < 0) 0 else std.math.pi;
                const z = r[1] + sd * (r[3] + 4 + noseLen(k) + row * 26);
                var x = r[0] - r[2] + halfSpan(k) + 2;

                while (x < r[0] + r[2] - halfSpan(k)) : (x += 3) {
                    if (overlaps(slot, k, x, z)) continue;

                    if (!spotFree(k, x, z, yaw, level)) continue;

                    place(slot, k, vec(x, rest(k, x, z, yaw), z), yaw);
                    slot += 1;
                    done = true;

                    break;
                }
            }
        }

        if (done) continue;

        const face = -inward * std.math.pi * 0.5;
        const x = spare - inward * rearLen(k);

        place(slot, k, vec(x, rest(k, x, r[1], face), r[1]), face);
        slot += 1;
        spare = x - inward * (noseLen(k) + 6);
    }
}

pub fn start(g: *Game, kind: usize) void {
    var index: usize = crafts.len;

    for (crafts, 0..) |c, i| {
        if (c.active and c.kind == kind) index = i;
    }

    if (index >= crafts.len) return;

    enter(g, index);

    const c = &crafts[index];

    if (c.spec().kind == .jet and std.c.getenv("DF_TAKEOFF") != null) {
        const r = terrain.runway;
        const west = r[0] > 0;
        const x = if (west) r[0] + r[2] - noseLen(c.kind) - 4 else r[0] - r[2] + noseLen(c.kind) + 4;

        c.yaw = if (west) -std.math.pi * 0.5 else std.math.pi * 0.5;
        c.pos = vec(x, rest(c.kind, x, r[1], c.yaw), r[1]);
        g.yaw = c.yaw;
    } else if (c.spec().kind == .jet) {
        c.pos = c.pos.add(.{ .y = 120 });
        c.speed = c.spec().top * 0.7;
        c.throttle = 0.7;
        c.grounded = false;
    }

    c.prev = c.pos;

    if (std.c.getenv("DF_AIRCAM") != null) {
        const r = terrain.runway;

        g.yaw = std.math.atan2(r[0] - c.pos.x, r[1] - c.pos.z);
        g.pitch = -0.32;
    }
}

fn enter(g: *Game, i: usize) void {
    seat = i;
    cam_ready = false;
    lock = null;
    lock_time = 0;
    g.yaw = crafts[i].yaw;
    g.pitch = -0.1;
}

pub fn exit(g: *Game) void {
    const i = seat orelse return;
    const c = &crafts[i];
    const side = c.basis().x.scale(c.spec().radius * 0.5 + 1.5);
    var spot = c.pos.add(side).add(.{ .y = 0.5 });

    if (c.grounded) spot.y = @max(spot.y, groundAt(spot.x, spot.z) + 0.2);

    seat = null;
    g.player.pos = spot;
    g.prev_pos = spot;
    g.player.vel = if (c.grounded) .{} else c.vel.scale(0.3);
    g.player.grounded = c.grounded;
}

pub fn update(g: *Game, dt: f32, c: Controls) bool {
    var used = false;

    for (&crafts, 0..) |*a, i| {
        if (!a.active) continue;

        if (a.hp <= 0) {
            a.wreck = @max(0, a.wreck - dt);
            a.respawn -= dt;

            if (a.wreck > wreck_time - 2 and g.rand() < dt * 8) g.explosions.spawn(.{ .pos = a.center().add(.{ .x = (g.rand() - 0.5) * a.spec().radius, .y = g.rand() * 2, .z = (g.rand() - 0.5) * a.spec().radius }), .radius = 2 + g.rand() * 2, .life = 0.7, .total = 0.7, .fire = true });

            if (a.respawn <= 0) place(i, a.kind, a.home, a.home_yaw);

            continue;
        }

        a.since_hurt += dt;
        a.rotor += dt * (if (a.spec().kind == .heli) 4 + a.lift * 26 else 0);
        a.gun_cd = @max(0, a.gun_cd - dt);
        a.missile_cd = @max(0, a.missile_cd - dt);
        a.rocket_cd = @max(0, a.rocket_cd - dt);

        if (a.since_hurt > 6) a.hp = @min(a.spec().hp, a.hp + a.spec().hp * 0.04 * dt);
    }

    if (c.enter and g.dead <= 0) {
        if (seat != null) {
            exit(g);
            used = true;
        } else if (nearest(g)) |i| {
            enter(g, i);
            used = true;
        }
    }

    if (seat) |i| {
        var wc = c;

        if (autofire) {
            wc.fire_down = true;
            wc.aim = @mod(g.time, 1.0) < 0.5;
        }

        weapons(g, i, wc, dt);
        updateLock(g, i, dt);
    }

    updateMissiles(g, dt);

    return used;
}

pub fn nearest(g: *Game) ?usize {
    const at = g.player.center();
    var best: ?usize = null;
    var best_d: f32 = 1e9;

    for (crafts, 0..) |a, i| {
        if (!a.alive() or a.remote) continue;

        const d = at.distance(a.center());

        if (d < a.spec().radius * 0.7 + 3 and d < best_d) {
            best = i;
            best_d = d;
        }
    }

    return best;
}

pub fn tick(g: *Game, c: Controls) void {
    const dt = movement.dt;

    for (&crafts, 0..) |*a, i| {
        if (!a.alive() or a.remote) continue;

        a.prev = a.pos;

        const mine = seat == i;
        const s = a.spec();

        if (s.kind == .jet) jetStep(g, a, if (mine) c else .{}, mine, dt) else heliStep(g, a, if (mine) c else .{}, mine, dt);

        if (a.alive()) collideWorld(g, a, i);
    }

    if (seat) |i| {
        const a = crafts[i];

        g.player.pos = a.center().sub(.{ .y = 0.9 });
        g.player.vel = a.vel;
        g.player.grounded = true;
    }
}

fn jetStep(g: *Game, a: *Craft, c: Controls, mine: bool, dt: f32) void {
    const s = a.spec();
    const auto: f32 = if (mine and autofly) 1 else 0;
    const push = std.math.clamp(c.forward + c.gas - c.brake_pedal + auto * 0.6, -1, 1);

    a.throttle = std.math.clamp(a.throttle + push * dt * 0.6, 0, 1);

    const boost: f32 = if (mine and c.boost) 1.25 else 1;
    const target = s.top * (0.25 + 0.75 * a.throttle) * boost;

    if (a.grounded) {
        a.speed = math.approach(a.speed, if (a.throttle > 0.05) target else 0, dt * (if (a.throttle > 0.05) @as(f32, 14) else 10));
    } else {
        a.speed = math.approach(a.speed, target, dt * 16);
        a.speed -= @sin(a.pitch) * 12 * dt;
    }

    if (mine) {
        var want_yaw = g.yaw;
        var want_pitch = std.math.clamp(g.pitch + 0.1, -1.3, 1.3);

        if (a.grounded and a.speed > s.stall * 1.05 and a.throttle > 0.4) want_pitch = @max(want_pitch, 0.16);

        if (!a.grounded and a.pos.y - groundAt(a.pos.x, a.pos.z) < 35 and g.pitch > -0.3 and a.throttle > 0.3) want_pitch = @max(want_pitch, 0.2);

        if (autofly) {
            want_yaw = std.math.atan2(-a.pos.x, -a.pos.z) + 0.5;
            want_pitch = if (a.pos.y - groundAt(a.pos.x, a.pos.z) < 90) 0.25 else 0.0;
        }

        if (!a.grounded) {
            want_yaw = homeward(a.pos, want_yaw);

            const pull = math.clamp01((outside(a.pos) + 90) / 130);

            if (pull > 0) g.yaw += std.math.atan2(@sin(a.yaw - g.yaw), @cos(a.yaw - g.yaw)) * @min(1, dt * 2.5 * pull);

            if (g.pitch > -0.45 and a.throttle > 0.35 and blocked(a.*)) want_pitch = @max(want_pitch, 0.7);
        }

        const dyaw = std.math.atan2(@sin(want_yaw - a.yaw), @cos(want_yaw - a.yaw));
        const rate = s.agility * (0.4 + 0.6 * math.clamp01(a.speed / s.top));
        const roll_in = std.math.clamp(c.right, -1, 1);

        if (!a.grounded or a.speed > s.stall) {
            a.pitch += std.math.clamp(want_pitch - a.pitch, -1.2 * rate * dt, 1.2 * rate * dt);
            a.yaw += std.math.clamp(dyaw, -0.9 * rate * dt, 0.9 * rate * dt) - roll_in * 0.35 * rate * dt;
        } else {
            a.yaw += std.math.clamp(dyaw, -0.5 * dt, 0.5 * dt);
        }

        const want_roll = std.math.clamp(-dyaw * 1.6, -0.85, 0.85) + roll_in * 0.6;

        a.roll += (want_roll - a.roll) * @min(1, dt * 4);
    } else if (!a.grounded) {
        a.pitch = math.approach(a.pitch, -0.6, dt * 0.4);
        a.roll += dt * 0.8;
    }

    if (a.grounded) {
        if (a.speed > s.stall and a.pitch > 0.05) {
            a.grounded = false;
            a.pos.y += 0.35;
        }

        if (a.grounded) {
            a.pitch = @max(a.pitch, 0);
            a.roll = math.approach(a.roll, 0, dt * 3);
        }
    }

    const fwd = a.forward();
    var vel = fwd.scale(a.speed);

    if (!a.grounded and a.speed < s.stall) {
        a.lift = math.approach(a.lift, -18 * (1 - a.speed / s.stall), dt * 10);
        a.pitch = math.approach(a.pitch, -0.5, dt * 0.6);
    } else {
        a.lift = math.approach(a.lift, 0, dt * 10);
    }

    vel.y += a.lift;
    a.vel = vel;
    a.pos = a.pos.add(vel.scale(dt));

    if (a.grounded) a.pos.y = rest(a.kind, a.pos.x, a.pos.z, a.yaw);
}

fn heliStep(g: *Game, a: *Craft, c: Controls, mine: bool, dt: f32) void {
    const s = a.spec();
    const b0 = orient(a.yaw, 0, 0);
    var climb: f32 = 0;
    var fwd_in: f32 = 0;
    var side_in: f32 = 0;

    if (mine) {
        climb = (if (c.jump) @as(f32, 1) else 0) - (if (c.boost) @as(f32, 1) else 0) + c.gas - c.brake_pedal;
        fwd_in = c.forward;
        side_in = c.right;

        var want_yaw = homeward(a.pos, g.yaw);

        if (autofly) {
            const alt = a.pos.y - groundAt(a.pos.x, a.pos.z);

            climb = if (alt < 110) 1 else 0;
            fwd_in = if (alt > 70) 0.8 else 0;
            want_yaw = std.math.atan2(-a.pos.x, -a.pos.z) + 0.4;
        }

        const dyaw = std.math.atan2(@sin(want_yaw - a.yaw), @cos(want_yaw - a.yaw));

        a.yaw += std.math.clamp(dyaw, -1.6 * s.agility * dt, 1.6 * s.agility * dt);
        a.lift = math.approach(a.lift, 1, dt * 0.8);
    } else {
        a.lift = math.approach(a.lift, if (a.grounded) 0 else 0.2, dt * 0.3);
    }

    climb = std.math.clamp(climb, -1, 1);

    const powered = a.lift > 0.6;
    const want = b0.z.scale(fwd_in * s.top).add(b0.x.scale(-side_in * s.top * 0.6)).add(.{ .y = if (powered) climb * 14 else -12 });
    const k = @min(1, dt * 1.2 * s.agility);

    a.vel = a.vel.add(want.sub(a.vel).scale(k));

    if (!powered) a.vel.y -= 9 * dt;

    a.pos = a.pos.add(a.vel.scale(dt));

    const local_fwd = a.vel.dot(b0.z) / s.top;
    const local_side = a.vel.dot(b0.x) / s.top;

    a.pitch = math.approach(a.pitch, -local_fwd * 0.35, dt * 1.5);
    a.roll = math.approach(a.roll, std.math.clamp(local_side * 0.5, -0.32, 0.32), dt * 1.5);
    a.speed = a.vel.length();

    const floor = groundAt(a.pos.x, a.pos.z);

    if (a.pos.y <= floor) {
        a.pos.y = floor;
        a.vel = .{ .x = a.vel.x * 0.5, .z = a.vel.z * 0.5 };
        a.grounded = true;
    } else if (a.pos.y > floor + 0.3) {
        a.grounded = false;
    }
}

fn collideWorld(g: *Game, a: *Craft, i: usize) void {
    const s = a.spec();
    const floor = groundAt(a.pos.x, a.pos.z);

    if (s.kind == .jet and !a.grounded and a.vel.y <= 0.5 and a.pos.y <= floor + 0.2) {
        const gentle = a.pitch > -0.3 and @abs(a.roll) < 0.5 and a.vel.y > -10;

        if (gentle) {
            a.grounded = true;
            a.pos.y = floor;
            a.pitch = 0;
            a.roll = 0;
        } else {
            destroy(g, i);

            return;
        }
    }

    if (s.kind == .jet and !a.grounded and a.pos.y < floor - 0.6) {
        destroy(g, i);

        return;
    }

    if (s.kind == .heli and a.vel.y < -14 and a.pos.y <= floor + 0.3) {
        destroy(g, i);

        return;
    }

    const step = a.pos.sub(a.prev);
    const len = step.length();

    if (len > 0.01) {
        if (hitsWorld(a.prev.add(.{ .y = s.height * 0.5 }), step.scale(1 / len), len + s.radius * 0.3)) {
            if (a.speed > (if (s.kind == .heli) @as(f32, 20) else 12)) {
                destroy(g, i);

                return;
            }

            a.pos = a.prev;
            a.vel = .{};
            a.speed = 0;
        }
    }

    const bound = terrain.play + airspace;

    if (@abs(a.pos.x) > bound or @abs(a.pos.z) > bound) {
        a.pos.x = std.math.clamp(a.pos.x, -bound, bound);
        a.pos.z = std.math.clamp(a.pos.z, -bound, bound);
        a.yaw = std.math.atan2(-a.pos.x, -a.pos.z);
    }

    if (a.pos.y > floor + 600) a.pos.y = floor + 600;
}

pub fn damage(g: *Game, i: usize, amount: f32) void {
    const a = &crafts[i];

    if (!a.alive() or a.remote) return;

    a.hp -= amount;
    a.since_hurt = 0;

    if (a.hp <= 0) destroy(g, i);
}

fn destroy(g: *Game, i: usize) void {
    const a = &crafts[i];

    if (!a.alive()) return;

    a.hp = 0;
    a.wreck = wreck_time;
    a.respawn = respawn_time;

    const at = a.center();

    g.explode(at, 7, 0, 18);
    g.explosions.spawn(.{ .pos = at, .radius = a.spec().radius * 0.8, .life = 2.2, .total = 2.2, .fire = true });

    if (seat == i) exit(g);

    a.pos.y = groundAt(a.pos.x, a.pos.z);
    a.vel = .{};
    a.speed = 0;
    a.lift = 0;
}

pub fn wreckRemote(g: *Game, i: usize) void {
    const a = &crafts[i];

    if (!a.alive()) return;

    a.remote = false;
    a.hp = 0;
    a.wreck = wreck_time;
    a.respawn = respawn_time;
    g.explosions.spawn(.{ .pos = a.center(), .radius = a.spec().radius * 0.8, .life = 2.2, .total = 2.2, .fire = true });
    a.pos.y = groundAt(a.pos.x, a.pos.z);
    a.vel = .{};
    a.speed = 0;
    a.lift = 0;
}

pub fn splash(g: *Game, at: Vec3, radius: f32, amount: f32) void {
    for (crafts, 0..) |a, i| {
        if (!a.alive()) continue;

        const d = a.center().distance(at);
        const reach = radius + a.spec().radius * 0.5;

        if (d > reach) continue;

        damage(g, i, amount * 1.6 * (1 - d / reach) + 20);
    }
}

fn muzzle(a: Craft) Vec3 {
    const b = a.basis();

    return a.center().add(b.z.scale(a.spec().radius * 0.7));
}

fn aimDir(g: *Game, a: Craft) Vec3 {
    if (a.spec().kind == .jet) return a.forward();

    return math.lookDir(g.yaw, g.pitch);
}

fn weapons(g: *Game, i: usize, c: Controls, dt: f32) void {
    _ = dt;

    const a = &crafts[i];
    const s = a.spec();

    if (c.fire_down and a.gun_cd <= 0) {
        a.gun_cd = s.gun;
        cannon(g, i);
    }

    const alt = c.aim;

    if (alt and !last_aim) {
        if (a.missiles > 0 and locked() and a.missile_cd <= 0) {
            launchMissile(g, a.*, lock.?);
            a.missiles -= 1;
            a.missile_cd = 0.6;
        } else if (a.rockets > 0 and a.rocket_cd <= 0) {
            rocketSalvo(g, a);
        }
    } else if (alt and a.rockets > 0 and a.rocket_cd <= 0 and lock == null) {
        rocketSalvo(g, a);
    }

    last_aim = alt;

    if (a.missiles < s.missiles or a.rockets < s.rockets) {
        a.reload += movement.dt;

        if (a.reload > 8) {
            a.reload = 0;
            a.missiles = s.missiles;
            a.rockets = s.rockets;
        }
    }
}

fn rocketSalvo(g: *Game, a: *Craft) void {
    const dir = aimDir(g, a.*);
    const b = a.basis();
    const side: f32 = if (a.rockets % 2 == 0) 1 else -1;
    const from = muzzle(a.*).add(b.x.scale(side * 1.4)).sub(b.y.scale(0.4));

    g.launch(.{
        .kind = .rocket,
        .pos = from,
        .vel = dir.scale(140).add(a.vel),
        .life = 5,
        .damage = 150,
        .splash = 5,
        .knockback = 10,
        .heading = dir,
    });

    a.rockets -= 1;
    a.rocket_cd = 0.14;
}

fn cannon(g: *Game, i: usize) void {
    const a = crafts[i];
    const dir = aimDir(g, a).add(.{ .x = (g.rand() - 0.5) * 0.012, .y = (g.rand() - 0.5) * 0.012, .z = (g.rand() - 0.5) * 0.012 }).normalize();
    const from = muzzle(a);
    const range: f32 = 600;
    var t = range;

    if (movement.raycast(world.pieces, from, dir, range)) |h| t = h.t;

    var bot: ?usize = null;

    for (g.bots.items, 0..) |b, k| {
        if (!b.alive()) continue;

        const hit = geom.raySphere(from, dir, t, b.body.pos.add(.{ .y = 1 }), 0.9) orelse continue;

        t = hit;
        bot = k;
    }

    var car: ?usize = null;

    if (driving.hitVehicle(g, from, dir, t)) |h| {
        t = h.t;
        car = h.index;
        bot = null;
    }

    var other: ?usize = null;

    for (crafts, 0..) |o, k| {
        if (k == i or !o.alive()) continue;

        const hit = geom.raySphere(from, dir, t, o.center(), o.spec().radius * 0.45) orelse continue;

        t = hit;
        other = k;
        bot = null;
        car = null;
    }

    const end = from.add(dir.scale(t));

    g.tracers.spawn(.{ .from = from, .to = end, .life = 0.09 });

    if (bot) |k| {
        g.damageBot(k, 34, end, false);
    } else if (car) |k| {
        driving.damage(g, k, 40, end);
    } else if (other) |k| {
        damage(g, k, 30);
        g.hit_marker = 0.12;
    } else if (t < range) {
        g.impacts.spawn(.{ .pos = end, .life = 1.6, .seed = g.rand() });
    }
}

fn targetPos(g: *Game, t: Target) ?Vec3 {
    return switch (t) {
        .vehicle => |k| if (k < g.vehicles.len and g.vehicles[k].alive()) g.vehicles[k].center() else null,
        .craft => |k| if (crafts[k].alive()) crafts[k].center() else null,
    };
}

fn updateLock(g: *Game, i: usize, dt: f32) void {
    const a = crafts[i];

    if (a.spec().missiles == 0) {
        lock = null;

        return;
    }

    const fwd = aimDir(g, a);
    const from = a.center();
    var best: ?Target = null;
    var best_score: f32 = 0;

    for (g.vehicles, 0..) |v, k| {
        if (!v.alive()) continue;

        const to = v.center().sub(from);
        const d = to.length();

        if (d > 700 or d < 8) continue;

        const cosv = to.scale(1 / d).dot(fwd);

        if (cosv > 0.92 and cosv > best_score) {
            best_score = cosv;
            best = .{ .vehicle = k };
        }
    }

    for (crafts, 0..) |o, k| {
        if (k == i or !o.alive()) continue;

        const to = o.center().sub(from);
        const d = to.length();

        if (d > 900 or d < 8) continue;

        const cosv = to.scale(1 / d).dot(fwd);

        if (cosv > 0.92 and cosv > best_score) {
            best_score = cosv;
            best = .{ .craft = k };
        }
    }

    if (best) |b| {
        const same = if (lock) |l| std.meta.eql(l, b) else false;

        if (same) lock_time += dt else {
            lock = b;
            lock_time = 0;
        }
    } else {
        lock = null;
        lock_time = 0;
    }
}

pub fn locked() bool {
    return lock != null and lock_time > 0.8;
}

fn launchMissile(g: *Game, a: Craft, t: Target) void {
    if (lock_time < 0.8) return;

    for (&missiles) |*m| {
        if (m.active) continue;

        const b = a.basis();

        m.* = .{ .active = true, .pos = a.center().sub(b.y.scale(0.8)), .vel = a.vel.add(b.z.scale(40)), .life = 8, .target = t };

        _ = g;

        return;
    }
}

fn updateMissiles(g: *Game, dt: f32) void {
    for (&missiles) |*m| {
        if (!m.active) continue;

        m.life -= dt;

        var dir = m.vel.normalize();

        if (m.target) |t| {
            if (targetPos(g, t)) |p| {
                const want = p.sub(m.pos).normalize();

                dir = dir.add(want.sub(dir).scale(@min(1, dt * 4))).normalize();

                if (p.distance(m.pos) < 4) {
                    hitTarget(g, m, t);

                    continue;
                }
            }
        }

        const speed = @min(m.vel.length() + 160 * dt, 260);

        m.vel = dir.scale(speed);
        m.pos = m.pos.add(m.vel.scale(dt));

        if (g.rand() < 0.7) g.explosions.spawn(.{ .pos = m.pos.sub(dir.scale(1.2)), .radius = 0.35, .life = 0.35, .total = 0.35 });

        if (m.life <= 0 or m.pos.y <= groundAt(m.pos.x, m.pos.z)) {
            g.explode(m.pos, 6, 200, 12);
            m.active = false;
        }
    }
}

fn hitTarget(g: *Game, m: *Missile, t: Target) void {
    switch (t) {
        .vehicle => |k| driving.damage(g, k, 700, m.pos),
        .craft => |k| damage(g, k, 650),
    }

    g.explode(m.pos, 6, 200, 12);
    m.active = false;
}

pub fn view(g: Game) ?View {
    const i = seat orelse return null;
    const a = crafts[i];
    const s = a.spec();
    const alpha = g.accumulator / movement.dt;
    const pos = a.prev.lerp(a.pos, alpha).add(.{ .y = s.height * 0.5 });
    const dir = math.lookDir(g.yaw, std.math.clamp(g.pitch, -1.4, 1.4));
    const dist = s.radius * 2.1 + 8;
    var eye = pos.sub(dir.scale(dist)).add(.{ .y = s.height * 0.6 + 2 });

    eye.y = @max(eye.y, terrain.height(eye.x, eye.z) + 1);
    cam_focus = pos;

    const right = dir.cross(math.up).normalize();

    return .{
        .eye = eye,
        .forward = dir,
        .right = right,
        .up = right.cross(dir),
        .muzzle = muzzle(a),
    };
}

pub fn smooth(raw: View, dt: f32) View {
    const offset = raw.eye.sub(cam_focus);

    if (!cam_ready) {
        cam_pos = offset;
        cam_ready = true;
    }

    cam_pos = cam_pos.lerp(offset, @min(1, dt * 8));

    var out = raw;

    out.eye = cam_focus.add(cam_pos);
    out.eye.y = @max(out.eye.y, terrain.height(out.eye.x, out.eye.z) + 1);

    return out;
}

pub fn draw(r: *gfx.Renderer, models: *const models_mod.Models, alpha: f32) void {
    for (crafts) |a| {
        if (!a.active) continue;

        if (a.wreck <= 0 and a.hp <= 0) continue;

        const ar = art[a.kind] orelse continue;
        const pos = a.prev.lerp(a.pos, alpha);
        var b = a.basis();

        if (a.wreck > 0) b = orient(a.yaw, -0.15, 0.6);

        r.drawModelLit(ar.body, mesh.transform(pos, b, 1));

        if (ar.rotor) |m| {
            const hub = pos.add(local(a, b, a.spec().rotor));

            r.drawModelLit(m, mesh.transform(hub, spin(b, b.y, a.rotor), 1));
        }

        if (ar.tail) |m| {
            const hub = pos.add(local(a, b, a.spec().tail.?));

            r.drawModelLit(m, mesh.transform(hub, spin(b, b.x, a.rotor * 2.5), 1));
        }
    }

    for (missiles) |m| {
        if (!m.active) continue;

        r.draw(models.rocket, mesh.transform(m.pos, Basis.facing(m.vel.normalize()), 1.4), false);
    }
}

pub fn engineLevel() f32 {
    const a = current() orelse return 0;

    return math.clamp01(a.speed / a.spec().top);
}

pub fn isHeli() bool {
    const a = current() orelse return false;

    return a.spec().kind == .heli;
}

pub fn prompt(g: Game) ?[:0]const u8 {
    if (seat != null) return null;

    const at = g.player.center();

    for (crafts) |a| {
        if (!a.alive()) continue;

        if (at.distance(a.center()) < a.spec().radius * 0.7 + 3) return a.spec().name;
    }

    return null;
}

pub fn hud(g: Game, font: rl.Font, cam: rl.Camera3D) void {
    const w: f32 = @floatFromInt(rl.GetScreenWidth());
    const h: f32 = @floatFromInt(rl.GetScreenHeight());
    const u = @min(h / 900, w / 1500);
    var buf: [96]u8 = undefined;

    if (prompt(g)) |name| {
        const msg = std.fmt.bufPrintSentinel(&buf, "F / Y  Fly {s}", .{name}, 0) catch return;
        const size = 22 * u;

        ui.text(font, msg, (w - ui.width(font, msg, size)) / 2, h * 0.62, size, ui.white);
    }

    const a = current() orelse return;
    const s = a.spec();
    const x = 40 * u;
    const base = h - 150 * u;
    const kmh = std.fmt.bufPrintSentinel(&buf, "{d}", .{@as(u32, @intFromFloat(a.speed * 3.6))}, 0) catch return;
    const size = 40 * u;

    ui.text(font, kmh, x, base - size, size, ui.white);
    ui.text(font, "KM/H", x, base + 2 * u, 13 * u, ui.fade(ui.white, 0.6));

    var abuf: [32]u8 = undefined;
    const alt = std.fmt.bufPrintSentinel(&abuf, "ALT {d} M", .{@as(i32, @intFromFloat(a.pos.y - terrain.height(a.pos.x, a.pos.z)))}, 0) catch return;

    ui.text(font, alt, x + 150 * u, base - 28 * u, 22 * u, ui.white);
    ui.text(font, s.name, x + 150 * u, base - 52 * u, 15 * u, ui.fade(ui.white, 0.6));

    const bar_w = 220 * u;

    ui.bar(x, base + 22 * u, bar_w, 8 * u, math01(a.hp / s.hp), if (a.hp / s.hp < 0.3) ui.red else ui.rgba(255, 196, 90, 255));

    if (s.kind == .jet) {
        ui.text(font, "THROTTLE", x, base + 36 * u, 12 * u, ui.fade(ui.white, 0.6));
        ui.bar(x + 80 * u, base + 38 * u, bar_w - 80 * u, 6 * u, a.throttle, ui.blue);

        if (!a.grounded and a.speed < s.stall * 1.1) {
            const warn: [:0]const u8 = "STALL";
            const ws = 30 * u;

            ui.text(font, warn, (w - ui.width(font, warn, ws)) / 2, h * 0.3, ws, ui.red);
        }
    }

    if (outside(a.pos) > 0) {
        const warn: [:0]const u8 = "Turning back to the map";
        const ws = 24 * u;

        ui.text(font, warn, (w - ui.width(font, warn, ws)) / 2, h * 0.24, ws, ui.rgba(255, 196, 90, 255));
    }

    var wbuf: [64]u8 = undefined;
    const arms = std.fmt.bufPrintSentinel(&wbuf, "GUN   MSL {d}   RKT {d}", .{ a.missiles, a.rockets }, 0) catch return;

    ui.text(font, arms, w - 40 * u - ui.width(font, arms, 20 * u), h - 150 * u, 20 * u, ui.white);

    const fwd = if (s.kind == .jet) a.forward() else math.lookDir(g.yaw, g.pitch);
    const aim = rl.GetWorldToScreen(.{ .x = a.center().x + fwd.x * 300, .y = a.center().y + fwd.y * 300, .z = a.center().z + fwd.z * 300 }, cam);

    rl.DrawCircleLinesV(aim, 14 * u, ui.fade(ui.white, 0.85));
    rl.DrawCircleV(aim, 2.5 * u, ui.white);

    if (lock) |t| {
        const p = targetPos(@constCast(&g), t) orelse return;
        const sp = rl.GetWorldToScreen(.{ .x = p.x, .y = p.y, .z = p.z }, cam);
        const full = lock_time > 0.8;
        const box = (if (full) @as(f32, 26) else 40 - lock_time * 17) * u;
        const col = if (full) ui.red else ui.rgba(255, 196, 90, 255);

        rl.DrawRectangleLinesEx(.{ .x = sp.x - box, .y = sp.y - box, .width = box * 2, .height = box * 2 }, 2.5 * u, col);

        if (full) ui.text(font, "LOCK", sp.x - box, sp.y + box + 4 * u, 16 * u, col);
    }
}

fn math01(v: f32) f32 {
    return std.math.clamp(v, 0, 1);
}
