const std = @import("std");
const shared = @import("shared");
const game_mod = @import("game.zig");
const vehicleart = @import("vehicleart.zig");

const vehicle = shared.vehicle;
const movement = shared.movement;
const math = shared.math;
const terrain = shared.terrain;
const world = shared.world;
const props = shared.props;
const weapons = shared.weapons;
const Vec3 = math.Vec3;
const Game = game_mod.Game;
const Controls = game_mod.Controls;
const View = game_mod.View;

pub var seat: ?usize = null;

var steer_smooth: f32 = 0;
pub var autodrive = false;
pub var vtest = false;
var vclock: f32 = 0;
var vlast_yaw: f32 = 0;
var vprint: f32 = 0;
pub var autoboost = false;
pub var blast_test: ?usize = null;
var blast_clock: f32 = 0;

var cam_pos: Vec3 = .{};
var cam_ready = false;
var cam_reach: f32 = 8;
var last_yaw: f32 = 0;
var look_idle: f32 = 0;
var run_cd: [vehicle.count]f32 = @splat(0);

pub const Hit = struct {
    index: usize,
    t: f32,
};

pub fn driving() bool {
    return seat != null;
}

pub fn current(g: *const Game) ?vehicle.Vehicle {
    const i = seat orelse return null;

    return g.vehicles[i];
}

pub fn tick(g: *Game, c: Controls) void {
    const dt = movement.dt;

    for (&g.vehicles, 0..) |*v, i| {
        if (!v.alive()) continue;

        if (seat == i) {
            const s = v.spec();
            const pedal: f32 = if (s.class == .cycle) 0.85 + 0.15 * @sin(g.time * 6) else 1;

            const auto: f32 = if (autodrive) 0.7 else 0;

            var cc = c;

            if (vtest) {
                vclock += dt;
                cc = scripted(vclock, c);

                if (cc.reset) vehicle.reset(v);
                trace(v.*, dt);
            }

            const analog = cc.gas - cc.brake_pedal;
            const push = std.math.clamp(cc.forward + analog, -1, 1);

            const raw = std.math.clamp(cc.right, -1, 1);
            const curved = std.math.sign(raw) * (0.35 * @abs(raw) + 0.65 * raw * raw);
            const centering = @abs(curved) < @abs(steer_smooth) or curved * steer_smooth < 0;

            steer_smooth = math.approach(steer_smooth, curved, dt * (if (centering) @as(f32, 9) else 4.5));

            vehicle.step(v, .{ .throttle = (push + auto) * pedal, .steer = steer_smooth + auto * 0.4, .brake = cc.jump, .boost = cc.boost or autoboost }, world.pieces, dt);

            boost_view = v.boosting;
            speed_fov = math.clamp01(@abs(v.speed) / @max(s.top_speed, 1)) * 8;
            cam_shake = @max(cam_shake * @exp(-dt * 7), @max(v.impact * 0.6, if (v.boosting) 0.05 + v.boost_start * 0.35 else 0));
        } else if (@abs(v.speed) > 0.4 or @abs(v.side) > 0.4 or v.vy < -0.8 or v.vy > 0.8 or v.righting > 0) {
            vehicle.step(v, .{}, world.pieces, dt);
        }
    }

    collide(g);
    runOver(g);

    if (seat) |i| {
        const v = g.vehicles[i];

        g.player.pos = v.seat().sub(.{ .y = 0.9 });
        g.player.vel = v.forward().scale(v.speed);
        g.player.grounded = true;
    }
}

fn scripted(t: f32, base: Controls) Controls {
    var c = base;

    c.forward = 0;
    c.right = 0;
    c.jump = false;
    c.gas = 0;
    c.brake_pedal = 0;

    if (t < 3) {
        c.forward = 1;
    } else if (t < 5) {
        c.forward = 1;
        c.right = 1;
    } else if (t < 6.5) {
        c.forward = 1;
        c.right = -1;
    } else if (t < 8) {
        c.forward = 0.6;
        c.right = 1;
        c.jump = true;
    } else if (t < 9) {
        c.forward = 0.8;
        c.right = -0.6;
    } else if (t < 12) {
        c.forward = 1;
    } else if (t < 14) {
        c.forward = -1;
    }

    c.reset = t >= 14.5 and t < 14.52;

    return c;
}

fn trace(v: vehicle.Vehicle, dt: f32) void {
    vprint += dt;

    if (vprint < 0.25) return;

    const rate = std.math.atan2(@sin(v.yaw - vlast_yaw), @cos(v.yaw - vlast_yaw)) / vprint;
    const ground = terrain.height(v.pos.x, v.pos.z);

    std.debug.print("VT t={d:.2} spd={d:.2} side={d:.2} yawr={d:.2} pitch={d:.3} roll={d:.3} lean={d:.2} y-terr={d:.2} vy={d:.2} gnd={} pos={d:.1},{d:.1}\n", .{ vclock, v.speed, v.side, rate, v.pitch, v.roll, v.lean, v.pos.y - ground, v.vy, v.grounded, v.pos.x, v.pos.z });
    vlast_yaw = v.yaw;
    vprint = 0;
}

fn extent(v: vehicle.Vehicle, n: Vec3) f32 {
    const s = v.spec();

    return @abs(n.dot(v.forward())) * s.length * 0.46 + @abs(n.dot(v.right())) * s.width * 0.48;
}

fn velocityOf(v: vehicle.Vehicle) Vec3 {
    return v.forward().scale(v.speed).add(v.right().scale(v.side));
}

fn setVelocity(v: *vehicle.Vehicle, vel: Vec3) void {
    v.speed = vel.dot(v.forward());
    v.side = vel.dot(v.right());
}

fn collide(g: *Game) void {
    for (&g.vehicles, 0..) |*a, i| {
        if (!a.alive()) continue;

        for (g.vehicles[i + 1 ..], i + 1..) |*b, j| {
            if (!b.alive()) continue;

            const d = b.pos.sub(a.pos);
            const flat = Vec3{ .x = d.x, .z = d.z };
            const dist = flat.length();
            const reach = (a.spec().length + b.spec().length) * 0.5;

            if (dist >= reach or dist < 0.001 or @abs(d.y) > 2) continue;

            const n = flat.scale(1 / dist);
            const overlap = extent(a.*, n) + extent(b.*, n) - dist;

            if (overlap <= 0) continue;

            const ma = vehicle.massOf(a.*);
            const mb = vehicle.massOf(b.*);
            const wa = mb / (ma + mb);
            const wb = ma / (ma + mb);

            a.pos = a.pos.sub(n.scale(overlap * wa));
            b.pos = b.pos.add(n.scale(overlap * wb));

            const va = velocityOf(a.*);
            const vb = velocityOf(b.*);
            const closing = va.sub(vb).dot(n);

            if (closing <= 0) continue;

            const impulse = closing * 1.2;

            setVelocity(a, va.sub(n.scale(impulse * wa)));
            setVelocity(b, vb.add(n.scale(impulse * wb)));

            if (closing > 2.5) {
                vehicle.hit(a, closing * wa * 2, b.forward().dot(a.right()) * closing);
                vehicle.hit(b, -closing * wb * 2, a.forward().dot(b.right()) * closing);
            }

            if (closing > 6) {
                damage(g, i, closing * 6 * wa * 2, a.pos.add(n.scale(extent(a.*, n))));
                damage(g, j, closing * 6 * wb * 2, b.pos.sub(n.scale(extent(b.*, n))));
            }
        }
    }
}

fn runOver(g: *Game) void {
    for (g.vehicles, 0..) |v, i| {
        run_cd[i] = @max(0, run_cd[i] - movement.dt);

        if (!v.alive() or @abs(v.speed) < 4 or run_cd[i] > 0) continue;

        const fwd = v.forward();
        const half = v.spec().length * 0.5;
        const wide = v.spec().width * 0.5 + 0.35;

        for (g.bots.items, 0..) |b, k| {
            if (!b.alive()) continue;

            const rel = b.body.pos.sub(v.pos);
            const along = rel.dot(fwd);
            const across = @abs(rel.dot(v.right()));

            if (@abs(along) > half + 0.3 or across > wide or @abs(rel.y) > 1.5) continue;

            g.damageBot(k, @abs(v.speed) * 9, b.chest(), false);
            movement.launch(&g.bots.items[k].body, fwd.scale(v.speed * 0.6).add(.{ .y = 5 }));
            run_cd[i] = 0.15;
        }
    }
}

fn shove(walker: *movement.Player, v: vehicle.Vehicle) void {
    const s = v.spec();
    const f = v.forward();
    const r = v.right();
    const rel = walker.pos.sub(v.pos);
    const top = v.pos.y + s.height * 0.8;
    const along = rel.dot(f);
    const across = rel.dot(r);
    const half_l = s.length * 0.46 + movement.radius;
    const half_w = s.width * 0.46 + movement.radius;

    if (@abs(along) >= half_l or @abs(across) >= half_w) return;

    if (walker.pos.y > top - 0.35) {
        if (walker.vel.y <= 0 and walker.pos.y < top + 0.2) {
            walker.pos.y = top;
            walker.vel.y = 0;
            walker.grounded = true;
        }

        return;
    }

    if (walker.pos.y + 1.6 < v.pos.y) return;

    const dl = half_l - @abs(along);
    const dw = half_w - @abs(across);

    if (dw < dl) {
        walker.pos = walker.pos.add(r.scale(dw * std.math.sign(across + 0.0001)));
        walker.vel = walker.vel.sub(r.scale(walker.vel.dot(r)));
    } else {
        walker.pos = walker.pos.add(f.scale(dl * std.math.sign(along + 0.0001)));
        walker.vel = walker.vel.sub(f.scale(walker.vel.dot(f)));
    }
}

pub fn solid(g: *Game) void {
    for (g.vehicles, 0..) |v, i| {
        if (!v.alive()) continue;

        if (seat != i and g.dead <= 0) shove(&g.player, v);

        for (&g.bots.items) |*b| {
            if (b.alive()) shove(&b.body, v);
        }
    }
}

pub fn update(g: *Game, dt: f32, c: Controls) void {
    for (&g.vehicles, 0..) |*v, i| {
        if (!v.alive()) {
            const before = v.wreck;

            v.wreck -= dt;

            if (v.wreck > vehicle.wreck_time - 1.6 and @floor(before * 5) != @floor(v.wreck * 5)) {
                const jitter = Vec3{ .x = (g.rand() - 0.5) * v.spec().width, .y = g.rand() * v.spec().height, .z = (g.rand() - 0.5) * v.spec().length * 0.8 };

                g.explosions.spawn(.{ .pos = v.center().add(jitter), .radius = 1.6 + g.rand() * 1.4, .life = 0.6, .total = 0.6, .fire = true });
            }

            if (v.wreck <= 0) {
                v.* = vehicle.spawn(v.kind, v.home, v.home_yaw);
                vehicle.settle(v, world.pieces);
            }

            continue;
        }

        v.since_hurt += dt;

        if (v.since_hurt > vehicle.regen_delay) v.hp = @min(v.spec().hp, v.hp + v.spec().hp * vehicle.regen_rate * dt);

        _ = i;
    }

    if (blast_test) |k| {
        blast_clock += dt;

        if (blast_clock > 3 and k < g.vehicles.len) {
            damage(g, k, 1e6, g.vehicles[k].pos);
            blast_test = null;
        }
    }

    if (c.enter and g.dead <= 0) {
        if (seat != null) exit(g) else enter(g);
    }

    const i = seat orelse {
        lean = 0;
        lean_hold = 0;

        return;
    };

    if (c.reset or (c.reload and lean < 0.3)) vehicle.reset(&g.vehicles[i]);

    if (g.vehicles[i].spec().class == .tank) aimTurret(g, &g.vehicles[i], dt);

    const shooting = lean_test or g.ads > 0.3 or g.arsenal.flash > 0 or c.fire_down;

    lean_hold = if (shooting) 1 else @max(0, lean_hold - dt);
    lean += ((if (lean_hold > 0) @as(f32, 1) else 0) - lean) * @min(1, dt * (if (lean_hold > 0) @as(f32, 9) else 5));

    const v = g.vehicles[i];
    const turned = @abs(g.yaw - last_yaw) > 0.0005;

    look_idle = if (turned) 0 else look_idle + dt;

    if (look_idle > 1.2 and @abs(v.speed) > 3) {
        const diff = std.math.atan2(@sin(v.yaw - g.yaw), @cos(v.yaw - g.yaw));
        const back: f32 = if (v.speed < 0) std.math.pi else 0;

        g.yaw += (diff + back) * @min(1, dt * 2.5);
        g.pitch += (-0.12 - g.pitch) * @min(1, dt * 2);
    }

    last_yaw = g.yaw;
}

fn enter(g: *Game) void {
    const at = g.player.center();
    var best: ?usize = null;
    var best_d: f32 = 1e9;

    for (g.vehicles, 0..) |v, i| {
        if (!v.alive() or !vehicle.usableBy(at, v)) continue;

        const d = at.distance(v.pos);

        if (d < best_d) {
            best_d = d;
            best = i;
        }
    }

    const i = best orelse return;

    seat = i;
    g.vehicles[i].occupied = true;
    cam_ready = false;
    last_yaw = g.yaw;
    look_idle = 0;
}

pub fn exit(g: *Game) void {
    const i = seat orelse return;
    const v = &g.vehicles[i];
    const side = v.right().scale(v.spec().width * 0.5 + 0.9);
    const options = [_]Vec3{ v.pos.sub(side), v.pos.add(side), v.pos.sub(v.forward().scale(v.spec().length * 0.5 + 1)), v.pos.add(.{ .y = v.spec().height + 0.3 }) };
    var spot = options[options.len - 1];

    for (options[0 .. options.len - 1]) |o| {
        const p = Vec3{ .x = o.x, .y = @max(o.y, terrain.height(o.x, o.z)) + 0.1, .z = o.z };

        if (!movement.solidAt(world.pieces, p)) {
            spot = p;
            break;
        }
    }

    v.occupied = false;
    seat = null;
    boost_view = false;
    speed_fov = 0;
    fov_extra = 0;
    g.player.pos = spot;
    g.prev_pos = spot;
    g.player.vel = v.forward().scale(v.speed * 0.5);
}

pub fn view(g: Game) ?View {
    const i = seat orelse return null;
    const v = g.vehicles[i];
    const s = v.spec();
    const alpha = g.accumulator / movement.dt;
    const pos = v.prev.lerp(v.pos, alpha);
    const pitch = std.math.clamp(g.pitch + g.recoil, -0.7, 0.6);
    const dir = math.lookDir(g.yaw + g.recoil_yaw, pitch);
    const target = pos.add(.{ .y = s.height * 0.6 + 0.35 });
    const pace = math.clamp01(@abs(v.speed) / @max(s.top_speed, 1));
    const dist: f32 = switch (s.class) {
        .car => 5.6 + s.length * 0.25 + pace * 1.4,
        .tank => 9.5,
        else => 3.6 + s.length * 0.3 + pace * 0.9,
    };
    const orbit = math.lookDir(g.yaw, pitch - 0.1);
    var reach = dist;

    if (movement.raycast(world.pieces, target, orbit.scale(-1), dist)) |hit| reach = @max(1.2, hit.t - 0.3);

    if (propHit(target, orbit.scale(-1), reach)) |t| reach = @max(1.2, t - 0.4);

    var tries: usize = 0;

    while (tries < 16 and reach > 1.2 and insideProp(target.sub(orbit.scale(reach)), 0.9)) : (tries += 1) reach = @max(1.2, reach - 0.45);

    if (reach < cam_reach) cam_reach = reach else cam_reach += (reach - cam_reach) * 0.06;

    reach = @min(reach, cam_reach);

    var eye = target.sub(orbit.scale(reach));

    const edge = terrain.play - 1;

    eye.x = std.math.clamp(eye.x, -edge, edge);
    eye.z = std.math.clamp(eye.z, -edge, edge);
    eye.y = @max(eye.y, terrain.height(eye.x, eye.z) + 0.5);

    const right = dir.cross(math.up).normalize();
    const up = right.cross(dir);

    return .{
        .eye = eye,
        .forward = dir,
        .right = right,
        .up = up,
        .muzzle = v.seat().add(.{ .y = 0.55 }).add(dir.scale(0.6)),
    };
}

var cam_time: f32 = 0;
pub var cam_shake: f32 = 0;
pub var fov_extra: f32 = 0;
pub var boost_view = false;
var speed_fov: f32 = 0;
pub var lean: f32 = 0;
pub var lean_test = false;
var lean_hold: f32 = 0;

fn propHit(origin: Vec3, dir: Vec3, limit: f32) ?f32 {
    var best: ?f32 = null;
    var reach = limit;

    for (world.placements) |pl| {
        const info = props.info(pl.kind);

        switch (info.group) {
            .bush, .ground, .road, .street, .car => continue,
            else => {},
        }

        if (info.foliage) continue;

        const s = pl.scale;
        const lo_y = pl.pos.y + info.min[1] * s;
        const hi_y = pl.pos.y + info.max[1] * s;

        if (hi_y - lo_y < 1.4) continue;

        const ex = @max(@abs(info.min[0]), @abs(info.max[0])) * s;
        const ez = @max(@abs(info.min[2]), @abs(info.max[2])) * s;
        const r = @sqrt(ex * ex + ez * ez);
        const dx = pl.pos.x - origin.x;
        const dz = pl.pos.z - origin.z;
        const far = reach + r;

        if (dx * dx + dz * dz > far * far) continue;

        const lo = [3]f32{ info.min[0] * s, lo_y, info.min[2] * s };
        const hi = [3]f32{ info.max[0] * s, hi_y, info.max[2] * s };
        var hit_t: ?f32 = null;

        for ([_]f32{ 1, -1 }) |sign| {
            const c = @cos(pl.yaw * sign);
            const sn = @sin(pl.yaw * sign);
            const ox = origin.x - pl.pos.x;
            const oz = origin.z - pl.pos.z;
            const o = [3]f32{ ox * c - oz * sn, origin.y, ox * sn + oz * c };
            const d = [3]f32{ dir.x * c - dir.z * sn, dir.y, dir.x * sn + dir.z * c };

            if (slab(o, d, lo, hi, reach)) |t| hit_t = if (hit_t) |h| @min(h, t) else t;
        }

        const t = hit_t orelse continue;

        if (t < reach) {
            reach = t;
            best = t;
        }
    }

    return best;
}

fn insideProp(p: Vec3, margin: f32) bool {
    for (world.placements) |pl| {
        const info = props.info(pl.kind);

        switch (info.group) {
            .bush, .ground, .road, .street, .car => continue,
            else => {},
        }

        if (info.foliage) continue;

        const s = pl.scale;
        const lo_y = pl.pos.y + info.min[1] * s - margin;
        const hi_y = pl.pos.y + info.max[1] * s + margin;

        if (hi_y - lo_y < 1.4 + margin * 2 or p.y < lo_y or p.y > hi_y) continue;

        const ex = @max(@abs(info.min[0]), @abs(info.max[0])) * s + margin;
        const ez = @max(@abs(info.min[2]), @abs(info.max[2])) * s + margin;
        const dx = p.x - pl.pos.x;
        const dz = p.z - pl.pos.z;

        if (dx * dx + dz * dz > ex * ex + ez * ez) continue;

        for ([_]f32{ 1, -1 }) |sign| {
            const c = @cos(pl.yaw * sign);
            const sn = @sin(pl.yaw * sign);
            const lx = dx * c - dz * sn;
            const lz = dx * sn + dz * c;

            if (lx > info.min[0] * s - margin and lx < info.max[0] * s + margin and lz > info.min[2] * s - margin and lz < info.max[2] * s + margin) return true;
        }
    }

    return false;
}

fn slab(o: [3]f32, d: [3]f32, lo: [3]f32, hi: [3]f32, limit: f32) ?f32 {
    var t0: f32 = 0;
    var t1: f32 = limit;

    for (0..3) |k| {
        if (@abs(d[k]) < 1e-6) {
            if (o[k] < lo[k] or o[k] > hi[k]) return null;

            continue;
        }

        const inv = 1 / d[k];
        var a = (lo[k] - o[k]) * inv;
        var b = (hi[k] - o[k]) * inv;

        if (a > b) {
            const tmp = a;

            a = b;
            b = tmp;
        }

        t0 = @max(t0, a);
        t1 = @min(t1, b);

        if (t0 > t1) return null;
    }

    if (t0 <= 0) return null;

    return t0;
}

pub fn smooth(raw: View, dt: f32) View {
    if (!cam_ready) {
        cam_pos = raw.eye;
        cam_ready = true;
    }

    const gap = raw.eye.sub(cam_pos).length();

    cam_pos = if (gap > 6) raw.eye else cam_pos.lerp(raw.eye, @min(1, dt * 16));
    cam_time += dt;
    const want_fov = (if (boost_view) @as(f32, 16) else 0) + speed_fov;

    fov_extra += (want_fov - fov_extra) * @min(1, dt * (if (boost_view) @as(f32, 5) else 3));

    var out = raw;

    out.eye = cam_pos.add(.{ .x = @sin(cam_time * 47) * cam_shake * 0.35, .y = @sin(cam_time * 61 + 1.1) * cam_shake * 0.25, .z = @sin(cam_time * 53 + 2.3) * cam_shake * 0.35 });

    return out;
}

pub fn hitVehicle(g: *const Game, origin: Vec3, dir: Vec3, limit: f32) ?Hit {
    var best: ?Hit = null;
    var reach = limit;

    for (g.vehicles, 0..) |v, i| {
        if (!v.alive() or seat == i) continue;

        const s = v.spec();
        const f = v.forward();
        const r = v.right();
        const rel = origin.sub(v.pos);
        const o = [3]f32{ rel.dot(r), rel.y, rel.dot(f) };
        const d = [3]f32{ dir.dot(r), dir.y, dir.dot(f) };
        const lo = [3]f32{ -s.width * 0.5, 0.1, -s.length * 0.5 };
        const hi = [3]f32{ s.width * 0.5, s.height, s.length * 0.5 };
        var t0: f32 = 0;
        var t1: f32 = reach;
        var miss = false;

        for (0..3) |k| {
            if (@abs(d[k]) < 1e-6) {
                if (o[k] < lo[k] or o[k] > hi[k]) miss = true;

                continue;
            }

            var a = (lo[k] - o[k]) / d[k];
            var b = (hi[k] - o[k]) / d[k];

            if (a > b) std.mem.swap(f32, &a, &b);

            t0 = @max(t0, a);
            t1 = @min(t1, b);
        }

        if (miss or t0 > t1) continue;

        reach = t0;
        best = .{ .index = i, .t = t0 };
    }

    return best;
}

pub fn damage(g: *Game, i: usize, amount: f32, at: Vec3) void {
    const v = &g.vehicles[i];

    if (!v.alive()) return;

    if (seat != i) return;

    v.hp -= amount;
    v.since_hurt = 0;

    if (v.hp > 0) return;

    v.hp = 0;
    v.wreck = vehicle.wreck_time;

    const blast = v.center();

    if (seat == i) {
        exit(g);
        movement.launch(&g.player, v.right().scale(-4).add(.{ .y = 7 }));
    }

    v.speed = 0;
    g.explode(blast, if (v.spec().class == .car) 6 else 4, if (v.spec().class == .car) 90 else 50, 12);
    _ = at;
}

pub fn splash(g: *Game, at: Vec3, radius: f32, amount: f32) void {
    for (g.vehicles, 0..) |v, i| {
        if (!v.alive()) continue;

        const f = weapons.splashFalloff(v.center().distance(at), radius + v.spec().length * 0.3);

        if (f <= 0) continue;

        g.vehicles[i].vy += 3 * f;
        damage(g, i, amount * f * 1.4, at);
    }
}

pub fn absorb(g: *Game, amount: f32, from: Vec3) bool {
    const i = seat orelse return false;

    damage(g, i, amount, from);

    return g.vehicles[i].spec().class == .car and seat != null;
}

pub fn inTank(g: *const Game) bool {
    const i = seat orelse return false;

    return g.vehicles[i].spec().class == .tank;
}

fn aimTurret(g: *Game, v: *vehicle.Vehicle, dt: f32) void {
    const want = std.math.atan2(@sin(g.yaw - v.yaw), @cos(g.yaw - v.yaw));
    const diff = std.math.atan2(@sin(want - v.turret), @cos(want - v.turret));
    const pitch = std.math.clamp(g.pitch + 0.08, -0.12, 0.32);

    v.turret += std.math.clamp(diff, -1.3 * dt, 1.3 * dt);
    v.gun = math.approach(v.gun, pitch, 0.7 * dt);
    v.reload = @max(0, v.reload - dt);
}

pub fn tankFire(g: *Game, c: Controls) void {
    const i = seat orelse return;
    const v = &g.vehicles[i];

    if (!c.fire_down or v.reload > 0) return;

    const m = vehicleart.muzzle(v.*) orelse return;

    v.reload = 3;
    g.projectiles.spawn(.{ .kind = .rocket, .pos = m.pos, .vel = m.dir.scale(95), .life = 3, .damage = 240, .splash = 7, .knockback = 16, .gravity = 4, .heading = m.dir });
    g.explosions.spawn(.{ .pos = m.pos, .radius = 1.4, .life = 0.25, .total = 0.25, .fire = true });
    v.speed -= 1.5;
}

pub fn start(g: *Game, index: usize) void {
    if (index >= g.vehicles.len) return;

    const v = g.vehicles[index];

    g.player.pos = v.pos.sub(v.right().scale(v.spec().width * 0.5 + 0.6));
    g.prev_pos = g.player.pos;
    g.yaw = v.yaw;
    g.pitch = -0.12;
    g.wave_break = 1e9;

    if (vtest and std.c.getenv("DF_VYAW") != null) {
        const v2 = &g.vehicles[index];
        const off = std.fmt.parseFloat(f32, std.mem.sliceTo(std.c.getenv("DF_VYAW").?, 0)) catch 0;

        v2.yaw += off;
        vehicle.settle(v2, world.pieces);
        g.yaw = v2.yaw;
    } else if (vtest) {
        const r = terrain.runway;
        const v2 = &g.vehicles[index];

        v2.pos = .{ .x = r[0] - r[2] + 12, .y = terrain.height(r[0] - r[2] + 12, r[1]), .z = r[1] };
        v2.yaw = std.math.pi * 0.5;
        vehicle.settle(v2, world.pieces);
        g.player.pos = v2.pos.sub(v2.right().scale(2));
        g.prev_pos = g.player.pos;
        g.yaw = v2.yaw;
    }

    enter(g);
}

const plain_names = [_][]const u8{ "Ranger Jeep", "Conquer Pickup", "Utility Truck", "Box Truck", "Armored Car", "Ace Hatchback", "Kiri Sedan", "Traveller Van", "Enforcer SUV", "Taxi", "Lifted Truck", "Fire Wagon", "El Alamo", "Urus" };

fn plain(name: []const u8) bool {
    for (plain_names) |p| {
        if (std.mem.eql(u8, p, name)) return true;
    }

    return false;
}

pub fn park(g: *Game) void {
    const spots = world.vehicle_spots;
    const tank_map = terrain.current == .desert or terrain.current == .valley or terrain.current == .conquest or terrain.current == .facility;
    var used: [256]bool = @splat(false);
    var order: [vehicle.count]usize = undefined;
    var n: usize = 0;
    var placed: [4]f32 = @splat(0);
    var totals: [4]f32 = @splat(0);
    var taken: [vehicle.count]bool = @splat(false);

    for (&g.vehicles, 0..) |*v, i| {
        v.* = vehicle.spawn(@intCast(i), .{ .y = -100 }, 0);
        v.wreck = 1e9;

        if (plain(vehicle.specs[i].name)) {
            taken[i] = true;

            continue;
        }

        const c = classSlot(vehicle.specs[i].class);

        if (c < 3) totals[c] += 1;
    }

    var by_speed: [vehicle.count]usize = undefined;

    for (&by_speed, 0..) |*o, i| o.* = i;

    std.mem.sort(usize, &by_speed, {}, struct {
        fn lt(_: void, a: usize, b: usize) bool {
            return vehicle.specs[a].top_speed > vehicle.specs[b].top_speed;
        }
    }.lt);

    var mixed: [vehicle.count]usize = undefined;
    var lo: usize = 0;
    var hi: usize = vehicle.count;

    for (&mixed, 0..) |*m, k| {
        if (k % 2 == 0) {
            m.* = by_speed[lo];
            lo += 1;
        } else {
            hi -= 1;
            m.* = by_speed[hi];
        }
    }

    while (n < vehicle.count) {
        var best: ?usize = null;
        var best_ratio: f32 = 9;

        for (0..3) |c| {
            if (placed[c] >= totals[c]) continue;

            const r = placed[c] / totals[c];

            if (r < best_ratio) {
                best_ratio = r;
                best = c;
            }
        }

        const c = best orelse break;

        for (mixed) |i| {
            if (taken[i] or classSlot(vehicle.specs[i].class) != c) continue;

            taken[i] = true;
            order[n] = i;
            n += 1;
            placed[c] += 1;

            break;
        }
    }

    var s: usize = 0;
    const reserve: usize = if (tank_map and world.tank_spot == null and spots.len > 0) 1 else 0;
    const limit = @min(spots.len - reserve, used.len);

    for (order[0..n]) |i| {
        while (s < limit) : (s += 1) {
            const v = &g.vehicles[i];

            v.* = vehicle.spawn(@intCast(i), spots[s].pos, spots[s].yaw);
            vehicle.settle(v, world.pieces);

            if (clearOfProps(v.*) and free(v.*)) {
                used[s] = true;
                v.home = v.pos;
                s += 1;

                break;
            }

            v.* = vehicle.spawn(@intCast(i), .{ .y = -100 }, 0);
            v.wreck = 1e9;
        }
    }

    for (&g.vehicles, 0..) |*v, i| {
        if (vehicle.specs[i].class != .tank or !tank_map) continue;

        const spot = world.tank_spot orelse if (spots.len > 0) spots[spots.len - 1] else null;

        if (spot) |sp| {
            v.* = vehicle.spawn(@intCast(i), sp.pos, sp.yaw);
            vehicle.settle(v, world.pieces);
            v.home = v.pos;
        }
    }

    if (std.c.getenv("DF_PARKLOG") != null) {
        var cnt: [4]usize = @splat(0);

        for (g.vehicles, 0..) |v, i| {
            if (v.wreck < 1e8) cnt[classSlot(vehicle.specs[i].class)] += 1;
        }

        std.debug.print("park spots={d} cars={d} bikes={d} cycles={d} tank={d}\n", .{ spots.len, cnt[0], cnt[1], cnt[2], cnt[3] });
    }

    seat = null;
}

fn classSlot(c: vehicle.Class) usize {
    return switch (c) {
        .car => 0,
        .bike, .scooter => 1,
        .cycle => 2,
        else => 3,
    };
}

fn clearOfProps(v: vehicle.Vehicle) bool {
    const s = v.spec();
    const reach = s.length * 0.5 + 0.4;

    for (world.placements) |p| {
        const info = shared.props.infos[@intFromEnum(p.kind)];

        if (info.group == .ground or info.group == .road) continue;

        if (info.max[1] * p.scale < 0.35) continue;

        const dx = p.pos.x - v.pos.x;
        const dz = p.pos.z - v.pos.z;
        const near = if (info.group == .tree) 0.8 else @max(@max(@abs(info.min[0]), info.max[0]), @max(@abs(info.min[2]), info.max[2])) * p.scale * 0.8;
        const lim = reach + near;

        if (dx * dx + dz * dz > lim * lim) continue;

        const fx = @sin(v.yaw);
        const fz = @cos(v.yaw);
        const along = dx * fx + dz * fz;
        const across = -dx * fz + dz * fx;

        if (@abs(along) < s.length * 0.5 + 0.3 + near and @abs(across) < s.width * 0.5 + 0.3 + near) return false;
    }

    return true;
}

fn free(parked: vehicle.Vehicle) bool {
    for ([_]f32{ 1, -1 }) |dir| {
        var v = parked;
        var t: usize = 0;

        while (t < 60) : (t += 1) vehicle.step(&v, .{ .throttle = dir }, world.pieces, movement.dt);

        if (v.pos.sub(parked.pos).flatLength() > 1.2) return true;
    }

    return false;
}
