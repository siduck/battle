const std = @import("std");
const shared = @import("shared");
const server = @import("main.zig");

const c = std.c;
const net = shared.net;
const math = shared.math;
const movement = shared.movement;
const weapons = shared.weapons;
const world = shared.world;
const terrain = shared.terrain;
const geom = shared.geom;
const Vec3 = math.Vec3;
const Addr = server.Addr;

extern "c" fn recv(fd: c_int, buf: [*]u8, len: usize, flags: c_int) isize;
extern "c" fn send(fd: c_int, buf: [*]const u8, len: usize, flags: c_int) isize;

const max_hp: f32 = 100;
const regen_delay: f32 = 5;
const regen_rate: f32 = 14;
const human_timeout: f64 = 20;
const room_idle: f64 = 45;
const history = 64;
const bot_reaction: f32 = 0.45;

const Sample = struct {
    time: u32 = 0,
    pos: Vec3 = .{},
};

const Ent = struct {
    used: bool = false,
    bot: bool = false,
    spawned: bool = false,
    name: [net.name_len]u8 = @splat(0),
    addr: Addr = undefined,
    token: u32 = 0,
    nonce: u32 = 0,
    pos: Vec3 = .{},
    vel: Vec3 = .{},
    yaw: f32 = 0,
    pitch: f32 = 0,
    grounded: bool = true,
    aiming: bool = false,
    weapon: u8 = 0,
    shots: u8 = 0,
    hp: f32 = max_hp,
    alive: bool = true,
    dead_t: f32 = 0,
    since_hurt: f32 = 10,
    kills: u8 = 0,
    deaths: u8 = 0,
    attacker: u8 = net.none,
    warp: u8 = 0,
    seen_at: f64 = 0,
    input_at: f64 = 0,
    echo: u32 = 0,
    echo_at: f64 = 0,
    hit_ack: u16 = 0,
    grace: f32 = 0,
    hist: [history]Sample = @splat(.{}),
    body: movement.Player = .{ .pos = .{} },
    goal: Vec3 = .{},
    retarget: f32 = 0,
    strafe: f32 = 1,
    strafe_t: f32 = 0,
    fire_cd: f32 = 1,
    seen: f32 = 0,
    stuck: f32 = 0,
    mag: u16 = 0,
    reload: f32 = 0,

    fn center(e: Ent) Vec3 {
        return e.pos.add(.{ .y = movement.height / 2 });
    }

    fn eye(e: Ent) Vec3 {
        return e.pos.add(.{ .y = movement.eye_height });
    }
};

const Room = struct {
    code: u16,
    ents: [net.max_slots]Ent = @splat(.{}),
    tick: u64 = 0,
    empty_since: f64,
    prng: std.Random.DefaultPrng,
    fill: u8,
    hits_ok: u32 = 0,
    hits_bad: u32 = 0,

    fn rand(r: *Room) f32 {
        return r.prng.random().float(f32);
    }

    fn time(r: Room) u32 {
        return @intFromFloat(@as(f64, @floatFromInt(r.tick)) * net.tick_ms);
    }

    fn humans(r: Room) u8 {
        var n: u8 = 0;

        for (r.ents) |e| {
            if (e.used and !e.bot) n += 1;
        }

        return n;
    }

    fn bots(r: Room) u8 {
        var n: u8 = 0;

        for (r.ents) |e| {
            if (e.used and e.bot) n += 1;
        }

        return n;
    }

    fn free(r: *Room) ?u8 {
        for (r.ents, 0..) |e, i| {
            if (!e.used) return @intCast(i);
        }

        return null;
    }

    fn spawnPoint(r: *Room, avoid_bots: bool) Vec3 {
        if (world.spawns.len == 0) return .{ .y = 2 };

        var best: usize = 0;
        var best_score: f32 = -1;

        for (world.spawns, 0..) |s, i| {
            var nearest: f32 = 1e9;

            for (r.ents) |e| {
                if (!e.used or !e.alive or !e.spawned or (e.bot and !avoid_bots)) continue;

                nearest = @min(nearest, e.pos.distance(s));
            }

            const score = nearest + r.rand() * 12;

            if (score > best_score) {
                best_score = score;
                best = i;
            }
        }

        return world.spawns[best];
    }

    fn addBot(r: *Room) void {
        const slot = r.free() orelse return;
        const at = r.spawnPoint(true);
        const weapon = botWeapon(r);
        var e: Ent = .{ .used = true, .bot = true, .spawned = true, .pos = at, .weapon = weapon };
        var buf: [net.name_len]u8 = undefined;
        const label = std.fmt.bufPrint(&buf, "Bot {d}", .{slot + 1}) catch "Bot";

        e.name = net.nameOf(label);
        e.body = movement.Player.spawn(at);
        e.mag = weapons.specs[weapon].mag;
        e.goal = at;
        e.yaw = r.rand() * std.math.pi * 2;
        r.ents[slot] = e;
        r.resetHistory(slot);
    }

    fn removeBot(r: *Room) void {
        var i: usize = r.ents.len;

        while (i > 0) {
            i -= 1;

            if (r.ents[i].used and r.ents[i].bot) {
                r.ents[i] = .{};

                return;
            }
        }
    }

    fn balance(r: *Room) void {
        const h = r.humans();
        const want: u8 = if (h == 0) 0 else if (h >= r.fill) 0 else r.fill - h;
        var b = r.bots();

        while (b > want) : (b -= 1) r.removeBot();

        while (b < want and r.free() != null) : (b += 1) r.addBot();
    }

    fn resetHistory(r: *Room, slot: usize) void {
        const e = &r.ents[slot];

        for (&e.hist) |*s| s.* = .{ .time = r.time(), .pos = e.pos };
    }

    fn rewind(r: Room, slot: usize, at: u32) Vec3 {
        const e = r.ents[slot];
        const now_ms = r.time();
        const t = std.math.clamp(at, now_ms -| 600, now_ms);
        var before: ?Sample = null;
        var after: ?Sample = null;

        for (e.hist) |s| {
            if (s.time <= t and (before == null or s.time > before.?.time)) before = s;
            if (s.time >= t and (after == null or s.time < after.?.time)) after = s;
        }

        const a = before orelse return (after orelse return e.pos).pos;
        const b = after orelse return a.pos;

        if (b.time == a.time) return a.pos;

        const k = @as(f32, @floatFromInt(t - a.time)) / @as(f32, @floatFromInt(b.time - a.time));

        return a.pos.lerp(b.pos, k);
    }

    fn damage(r: *Room, slot: usize, amount: f32, from: u8) void {
        const e = &r.ents[slot];

        if (!e.used or !e.alive or !e.spawned) return;

        e.hp -= amount;
        e.since_hurt = 0;
        e.attacker = from;

        if (e.bot) e.seen = @max(e.seen, bot_reaction);

        if (e.hp > 0) return;

        e.hp = 0;
        e.alive = false;
        e.dead_t = if (e.bot) 4 else net.respawn_s;
        e.deaths +%= 1;

        if (from < r.ents.len and from != slot and r.ents[from].used) r.ents[from].kills +%= 1;

        var a: [net.name_len]u8 = @splat(0);

        if (from < r.ents.len) a = r.ents[from].name;

        server.log("room {d}: {s} downed {s}", .{ r.code, net.nameSlice(&a), net.nameSlice(&e.name) });
    }

    fn validHit(r: *Room, shooter: usize, h: net.Hit) bool {
        if (h.target >= r.ents.len or h.target == shooter) return false;

        const s = r.ents[shooter];
        const t = r.ents[h.target];

        if (!s.alive or !t.used or !t.alive or !t.spawned) return false;

        if (h.amount <= 0 or h.amount > 400) return false;

        const then = r.rewind(h.target, h.view);
        const now_pos = t.pos;
        const reach: f32 = if (h.splash) 3.5 else 2.4;
        const near_then = h.at.distance(then.add(.{ .y = 1 })) < reach;
        const near_now = h.at.distance(now_pos.add(.{ .y = 1 })) < reach;

        if (!near_then and !near_now) return false;

        if (h.splash) return h.at.distance(s.eye()) < 400;

        const eye = s.eye();
        const to = h.at.sub(eye);
        const dist = to.length();

        if (dist > 450) return false;

        if (dist < 1.5) return true;

        const dir = to.scale(1 / dist);
        const wall = movement.raycast(world.pieces, eye, dir, dist);

        if (wall) |w| return w.t > dist - 1.2;

        return true;
    }

    fn onInput(r: *Room, slot: usize, addr: Addr, in: net.Input, now: f64) void {
        const e = &r.ents[slot];

        e.addr = addr;
        e.seen_at = now;
        e.echo = in.time;
        e.echo_at = now;

        for (in.hits[0..in.hit_count]) |h| {
            if (!net.newer(h.id, e.hit_ack)) continue;

            e.hit_ack = h.id;

            if (r.validHit(slot, h)) {
                r.hits_ok += 1;
                r.damage(h.target, h.amount, @intCast(slot));
            } else {
                r.hits_bad += 1;
            }
        }

        if (in.flags & net.InFlag.loading != 0) return;

        if (!e.spawned) {
            e.spawned = true;
            e.grace = 2;
            e.pos = in.pos;
            r.resetHistory(slot);
        }

        const dt: f32 = @floatCast(@max(0.016, @min(1, now - e.input_at)));

        e.input_at = now;

        const bound = terrain.half + 20;
        const inside = @abs(in.pos.x) < bound and @abs(in.pos.z) < bound and in.pos.y > -60 and in.pos.y < 1500;
        const moved = in.pos.distance(e.pos);
        var at_spawn = false;

        for (world.spawns) |s| {
            if (s.distance(in.pos) < 2.5) at_spawn = true;
        }

        if (inside and (e.grace > 0 or at_spawn or moved < 150 * dt + 4)) {
            e.pos = in.pos;
        } else if (e.alive) {
            e.warp +%= 1;
        }

        e.vel = in.vel;
        e.yaw = in.yaw;
        e.pitch = in.pitch;
        e.weapon = if (in.weapon < weapons.specs.len) in.weapon else 0;
        e.aiming = in.flags & net.InFlag.aiming != 0;
        e.grounded = in.flags & net.InFlag.grounded != 0;
        e.shots = in.shots;
    }

    fn join(r: *Room, addr: Addr, name: [net.name_len]u8, nonce: u32, now: f64) ?usize {
        for (r.ents, 0..) |e, i| {
            if (e.used and !e.bot and e.nonce == nonce and e.addr.addr == addr.addr and e.addr.port == addr.port) return i;
        }

        if (r.humans() >= net.max_humans) return null;

        if (r.free() == null) r.removeBot();

        const slot = r.free() orelse return null;
        var e: Ent = .{ .used = true, .addr = addr, .nonce = nonce, .seen_at = now, .input_at = now, .name = name, .token = r.prng.random().int(u32) | 1 };

        if (e.name[0] == 0) e.name = net.nameOf("Player");

        for (r.ents, 0..) |o, i| {
            if (i != slot and o.used and std.mem.eql(u8, &o.name, &e.name)) {
                var buf: [net.name_len]u8 = undefined;
                const base = net.nameSlice(&e.name);
                const label = std.fmt.bufPrint(&buf, "{s} {d}", .{ base[0..@min(base.len, net.name_len - 3)], slot + 1 }) catch base;

                e.name = net.nameOf(label);

                break;
            }
        }

        e.pos = r.spawnPoint(false);
        r.ents[slot] = e;
        r.resetHistory(slot);
        r.balance();

        var text: [32]u8 = undefined;

        server.log("room {d}: {s} joined slot {d} from {s}", .{ r.code, net.nameSlice(&e.name), slot, server.addrText(addr, &text) });

        return slot;
    }

    fn step(r: *Room, now: f64) void {
        const dt = movement.dt;

        r.tick += 1;

        for (&r.ents, 0..) |*e, i| {
            if (!e.used) continue;

            if (!e.bot and now - e.seen_at > human_timeout) {
                server.log("room {d}: {s} timed out", .{ r.code, net.nameSlice(&e.name) });
                e.* = .{};
                r.balance();

                continue;
            }

            e.grace = @max(0, e.grace - dt);
            e.since_hurt += dt;

            if (!e.alive) {
                e.dead_t -= dt;

                if (e.dead_t <= 0) r.revive(i);

                continue;
            }

            if (e.since_hurt > regen_delay) e.hp = @min(max_hp, e.hp + regen_rate * dt);

            if (e.bot) r.thinkBot(i, dt);
        }

        const t = r.time();

        if (r.tick % (net.tick_hz * 10) == 0 and r.hits_ok + r.hits_bad > 0) {
            server.log("room {d}: hits accepted {d}, rejected {d}", .{ r.code, r.hits_ok, r.hits_bad });
            r.hits_ok = 0;
            r.hits_bad = 0;
        }

        for (&r.ents) |*e| {
            if (e.used) e.hist[r.tick % history] = .{ .time = t, .pos = e.pos };
        }
    }

    fn revive(r: *Room, slot: usize) void {
        const e = &r.ents[slot];

        e.alive = true;
        e.hp = max_hp;
        e.since_hurt = 10;
        e.grace = 1.5;

        if (!e.bot) return;

        e.pos = r.spawnPoint(true);
        e.body = movement.Player.spawn(e.pos);
        e.weapon = botWeapon(r);
        e.mag = weapons.specs[e.weapon].mag;
        e.seen = 0;
        e.goal = e.pos;
        r.resetHistory(slot);
    }

    fn thinkBot(r: *Room, slot: usize, dt: f32) void {
        const b = &r.ents[slot];
        const eye = b.eye();
        var target: ?usize = null;
        var best: f32 = 70;

        for (r.ents, 0..) |o, i| {
            if (i == slot or !o.used or o.bot or !o.alive or !o.spawned) continue;

            const d = o.center().distance(eye);

            if (d < best) {
                best = d;
                target = i;
            }
        }

        var los = false;
        var dir: Vec3 = .{ .z = 1 };
        var dist: f32 = 1e9;

        if (target) |t| {
            const to = r.ents[t].center().sub(eye);

            dist = @max(to.length(), 0.01);
            dir = to.scale(1 / dist);
            los = movement.raycast(world.pieces, eye, dir, dist - 0.5) == null;
        }

        b.seen = if (los) b.seen + dt else @max(0, b.seen - dt * 0.5);
        b.retarget -= dt;
        b.strafe_t -= dt;

        if (b.strafe_t <= 0) {
            b.strafe = if (r.rand() < 0.5) -1 else 1;
            b.strafe_t = 0.9 + r.rand() * 1.6;
        }

        var input: movement.Input = .{};

        if (los) {
            b.yaw = turnToward(b.yaw, std.math.atan2(dir.x, dir.z), dt * 6);
            b.pitch = std.math.asin(std.math.clamp(dir.y, -1, 1));
            input.forward = if (dist > 24) 1 else if (dist < 9) -0.7 else 0;
            input.right = b.strafe * 0.85;
        } else {
            if (b.retarget <= 0 or b.pos.distance(b.goal) < 2) {
                b.goal = if (target) |t| r.ents[t].pos else if (world.spawns.len > 0) world.spawns[r.prng.random().uintLessThan(usize, world.spawns.len)] else b.pos;
                b.retarget = 2.5 + r.rand() * 2;
            }

            const go = b.goal.sub(b.pos);

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
        movement.step(&b.body, input, world.pieces);
        b.pos = b.body.pos;
        b.vel = b.body.vel;
        b.grounded = b.body.grounded;

        if (b.pos.y < movement.kill_y) {
            r.damage(slot, 1e6, @intCast(slot));

            return;
        }

        b.fire_cd -= dt;

        if (b.reload > 0) {
            b.reload -= dt;

            if (b.reload <= 0) b.mag = weapons.specs[b.weapon].mag;

            return;
        }

        const t = target orelse return;

        if (!los or b.seen < bot_reaction or b.fire_cd > 0) return;

        const spec = weapons.specs[b.weapon];

        if (b.mag == 0) {
            b.reload = spec.reload * 1.2;

            return;
        }

        b.mag -= 1;
        b.fire_cd = @max(spec.interval, 0.09) * (1.6 + r.rand() * 0.8);
        b.shots +%= 1;

        const victim = r.ents[t];
        const aim_at = victim.center();
        const spread = 0.5 + dist * 0.05 + victim.vel.flatLength() * 0.07;
        var pellet: u8 = 0;

        while (pellet < spec.pellets) : (pellet += 1) {
            const miss: Vec3 = .{ .x = (r.rand() - 0.5) * 2 * spread, .y = (r.rand() - 0.5) * 2 * spread, .z = (r.rand() - 0.5) * 2 * spread };
            const aim = aim_at.add(miss).sub(eye);
            const len = aim.length();
            const shot_dir = aim.scale(1 / len);
            const wall = movement.raycast(world.pieces, eye, shot_dir, len + 30);
            const reach = if (wall) |h| h.t else len + 30;
            const along = std.math.clamp(aim_at.sub(eye).dot(shot_dir), 0, reach);
            const closest = eye.add(shot_dir.scale(along));

            if (closest.distance(aim_at) < 0.5 and along < reach) r.damage(t, spec.damage * 0.3, @intCast(slot));
        }
    }

    fn snapshot(r: *Room, udp: c_int, now: f64) void {
        var s: net.Snapshot = .{ .time = r.time() };

        for (r.ents, 0..) |e, i| {
            if (!e.used or !e.spawned) continue;

            var flags: u8 = 0;

            if (e.alive) flags |= net.EntFlag.alive;
            if (e.bot) flags |= net.EntFlag.bot;
            if (e.aiming) flags |= net.EntFlag.aiming;
            if (e.grounded) flags |= net.EntFlag.grounded;

            s.ents[s.count] = .{
                .slot = @intCast(i),
                .flags = flags,
                .pos = e.pos,
                .vel = e.vel,
                .yaw = e.yaw,
                .pitch = e.pitch,
                .hp = @intFromFloat(@ceil(std.math.clamp(e.hp, 0, 255))),
                .weapon = e.weapon,
                .shots = e.shots,
                .kills = e.kills,
                .deaths = e.deaths,
                .attacker = e.attacker,
                .warp = e.warp,
            };
            s.count += 1;
        }

        const roster = r.tick % (net.tick_hz / 2) == 0;

        for (r.ents, 0..) |e, i| {
            if (!e.used or e.bot) continue;

            s.you = @intCast(i);
            s.echo = e.echo;
            s.held = @intFromFloat(std.math.clamp((now - e.echo_at) * 1000, 0, 65535));
            s.hit_ack = e.hit_ack;

            var w: net.Writer = .{};

            w.start(.{ .kind = .snapshot, .code = r.code, .token = e.token });

            s.write(&w);
            server.sendTo(udp, e.addr, w.bytes());

            if (roster) r.sendRoster(udp, e);
        }
    }

    fn sendRoster(r: *Room, udp: c_int, to: Ent) void {
        var w: net.Writer = .{};

        w.start(.{ .kind = .roster, .code = r.code, .token = to.token });
        var count: u8 = 0;

        for (r.ents) |e| {
            if (e.used) count += 1;
        }

        w.u8v(count);

        for (r.ents, 0..) |e, i| {
            if (!e.used) continue;

            w.u8v(@intCast(i));
            w.u8v(@intFromBool(e.bot));
            w.name(e.name);
        }

        server.sendTo(udp, to.addr, w.bytes());
    }
};

fn turnToward(current: f32, target: f32, max_step: f32) f32 {
    const tau = std.math.pi * 2;
    const diff = @mod(target - current + std.math.pi, tau) - std.math.pi;

    return current + std.math.clamp(diff, -max_step, max_step);
}

fn botWeapon(r: *Room) u8 {
    var tries: u32 = 0;

    while (tries < 40) : (tries += 1) {
        const i = r.prng.random().uintLessThan(u8, @intCast(weapons.specs.len));
        const s = weapons.specs[i];

        if (s.fire == .hitscan and !s.flame and !weapons.isMelee(s) and s.charge == 0 and s.spinup == 0) return i;
    }

    return 0;
}

var rooms: [1000]?*Room = @splat(null);
var udp_fd: c_int = -1;
var master_fd: c_int = -1;
var fill_to: u8 = 6;
var seed_rng: std.Random.DefaultPrng = undefined;

fn joined(addr: Addr, r: *Room, slot: usize, nonce: u32) void {
    var w: net.Writer = .{};

    w.start(.{ .kind = .joined, .code = r.code, .token = r.ents[slot].token });

    w.u8v(@intCast(slot));
    w.u8v(@backingInt(terrain.current));
    w.u32v(nonce);
    server.sendTo(udp_fd, addr, w.bytes());
}

fn refuse(addr: Addr, code: u16, reason: net.Reason, nonce: u32) void {
    var w: net.Writer = .{};

    w.start(.{ .kind = .reject, .code = code });

    w.u8v(@backingInt(reason));
    w.u32v(nonce);
    server.sendTo(udp_fd, addr, w.bytes());
}

fn closeRoom(code: u16) void {
    const r = rooms[code] orelse return;

    std.heap.page_allocator.destroy(r);
    rooms[code] = null;

    const msg = [3]u8{ 'x', @truncate(code), @truncate(code >> 8) };

    _ = send(master_fd, &msg, msg.len, c.MSG.DONTWAIT);
    server.log("room {d} expired", .{code});
}

fn findByToken(r: *Room, token: u32) ?usize {
    for (r.ents, 0..) |e, i| {
        if (e.used and !e.bot and e.token == token) return i;
    }

    return null;
}

fn onPacket(addr: Addr, data: []const u8, now: f64) void {
    var rd: net.Reader = .{ .data = data };
    const h = rd.header() orelse return;

    if (h.code >= rooms.len) return;

    switch (h.kind) {
        .create => {
            _ = rd.u8v();

            const nonce = rd.u32v();
            const name = rd.name();

            if (rooms[h.code] == null) {
                const r = std.heap.page_allocator.create(Room) catch return refuse(addr, 0, .busy, nonce);

                r.* = .{ .code = h.code, .empty_since = now, .prng = std.Random.DefaultPrng.init(seed_rng.random().int(u64)), .fill = fill_to };
                rooms[h.code] = r;
            }

            const r = rooms[h.code].?;
            const slot = r.join(addr, name, nonce, now) orelse return refuse(addr, h.code, .full, nonce);

            joined(addr, r, slot, nonce);
        },
        .join => {
            const name = rd.name();
            const nonce = rd.u32v();
            const r = rooms[h.code] orelse return refuse(addr, h.code, .no_room, nonce);
            const slot = r.join(addr, name, nonce, now) orelse return refuse(addr, h.code, .full, nonce);

            joined(addr, r, slot, nonce);
        },
        .input => {
            const r = rooms[h.code] orelse return refuse(addr, h.code, .no_room, 0);
            const slot = findByToken(r, h.token) orelse return refuse(addr, h.code, .no_room, 0);
            const in = net.Input.read(&rd);

            if (!rd.ok) return;

            r.onInput(slot, addr, in, now);
        },
        .leave => {
            const r = rooms[h.code] orelse return;
            const slot = findByToken(r, h.token) orelse return;

            server.log("room {d}: {s} left", .{ r.code, net.nameSlice(&r.ents[slot].name) });
            r.ents[slot] = .{};
            r.balance();
        },
        else => {},
    }
}

pub fn worker(map: terrain.Map, udp: c_int, fd: c_int, fill: u8) void {
    udp_fd = udp;
    master_fd = fd;
    fill_to = fill;
    seed_rng = std.Random.DefaultPrng.init(@intFromFloat(server.now() * 1e6));
    terrain.current = map;
    terrain.configure();
    world.build(std.heap.page_allocator);
    server.log("world {s} ready: {d} pieces, {d} spawns", .{ @tagName(map), world.pieces.len, world.spawns.len });

    const tick: f64 = 1.0 / @as(f64, net.tick_hz);
    var next = server.now();

    while (true) {
        const now = server.now();
        const wait: c_int = @intFromFloat(@max(0, (next - now) * 1000));
        var fds = [_]c.pollfd{.{ .fd = fd, .events = c.POLL.IN, .revents = 0 }};

        if (c.poll(&fds, 1, wait) > 0) {
            if (fds[0].revents & (c.POLL.HUP | c.POLL.ERR) != 0) c._exit(0);

            var count: u32 = 0;

            while (count < 512) : (count += 1) {
                var buf: [net.max_packet + @sizeOf(Addr)]u8 = undefined;
                const n = recv(fd, &buf, buf.len, c.MSG.DONTWAIT);

                if (n == 0) c._exit(0);

                if (n < @as(isize, @sizeOf(Addr))) break;

                var addr: Addr = undefined;

                @memcpy(std.mem.asBytes(&addr), buf[0..@sizeOf(Addr)]);
                onPacket(addr, buf[@sizeOf(Addr)..@intCast(n)], server.now());
            }
        }

        var steps: u32 = 0;

        while (server.now() >= next and steps < 10) : (steps += 1) {
            next += tick;

            const t = server.now();

            for (&rooms, 0..) |*slot, code| {
                const r = slot.* orelse continue;

                r.step(t);

                if (r.tick % net.snapshot_every == 0) r.snapshot(udp, t);

                if (r.humans() > 0) r.empty_since = t else if (t - r.empty_since > room_idle) closeRoom(@intCast(code));
            }
        }

        if (server.now() > next + 1) next = server.now();
    }
}

test "rewind" {
    var r: Room = .{ .code = 1, .empty_since = 0, .prng = std.Random.DefaultPrng.init(1), .fill = 0 };

    r.ents[0].used = true;

    var i: u64 = 0;

    while (i < 30) : (i += 1) {
        r.tick = i;
        r.ents[0].hist[i % history] = .{ .time = r.time(), .pos = .{ .x = @floatFromInt(i) } };
    }

    r.ents[0].pos = .{ .x = 29 };

    const p = r.rewind(0, r.time() - 100);

    try std.testing.expect(@abs(p.x - 23) < 0.2);
}
