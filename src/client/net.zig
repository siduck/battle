const std = @import("std");
const rl = @import("raylib");
const shared = @import("shared");
const game_mod = @import("game.zig");
const ui = @import("ui.zig");
const assets = @import("assets.zig");

const c = std.c;
const net = shared.net;
const math = shared.math;
const Vec3 = math.Vec3;
const Game = game_mod.Game;
const Addr = c.sockaddr.in;

extern "c" fn recv(fd: c_int, buf: [*]u8, len: usize, flags: c_int) isize;
extern "c" fn inet_addr(cp: [*:0]const u8) u32;

pub const default_server = "144.24.200.37";
const interp_ms: f64 = 110;
const send_every: f64 = 1.0 / 30.0;
const resend_every: f64 = 0.3;
const give_up: f64 = 6;
const lost_after: f64 = 4;
const ring = 32;

pub const Status = enum { idle, waiting, joined, rejected, timeout };

const Ask = enum { create, join };

const Claim = struct {
    hit: net.Hit,
    sent: u8 = 0,
};

const Kill = struct {
    killer: [net.name_len]u8,
    victim: [net.name_len]u8,
    mine: bool,
    life: f32,
};

pub var active = false;
pub var status: Status = .idle;
pub var reason: net.Reason = .no_room;
pub var code: u16 = 0;
pub var map: u8 = 0;
pub var slot: u8 = 0;
pub var ping_ms: f32 = 0;
pub var lost = false;

var token: u32 = 0;
var fd: c_int = -1;
var server: Addr = undefined;
var nonce: u32 = 0;
var ask: Ask = .create;
var ask_map: u8 = 0;
var asked_at: f64 = 0;
var first_ask: f64 = 0;
var my_name: [net.name_len]u8 = @splat(0);
var epoch: f64 = 0;
var last_recv: f64 = 0;
var send_at: f64 = 0;
var keep_at: f64 = 0;
var offset: f64 = 0;
var have_offset = false;
var snaps: [ring]net.Snapshot = undefined;
var snap_count: usize = 0;
var snap_head: usize = 0;
var claims: [32]Claim = undefined;
var claim_count: usize = 0;
var next_hit: u16 = 1;
var names: [net.max_slots][net.name_len]u8 = @splat(@splat(0));
var is_bot: [net.max_slots]bool = @splat(false);
var seen_shots: [net.max_slots]u8 = @splat(0);
var seen_deaths: [net.max_slots]u8 = @splat(0);
var known: [net.max_slots]bool = @splat(false);
var my_deaths: u8 = 0;
var my_warp: u8 = 0;
var my_known = false;
var kills: [5]Kill = undefined;
var kill_count: usize = 0;
var prng = std.Random.DefaultPrng.init(0x5eed);
var rejoin_at: f64 = 0;
var in_match = false;

fn now() f64 {
    var ts: c.timespec = undefined;

    _ = c.clock_gettime(c.CLOCK.MONOTONIC, &ts);

    return @as(f64, @floatFromInt(ts.sec)) + @as(f64, @floatFromInt(ts.nsec)) / 1e9;
}

fn ms() u32 {
    return @intFromFloat((now() - epoch) * 1000);
}

fn resolve() void {
    var host_buf: [64:0]u8 = @splat(0);
    var port: u16 = net.port;
    var host: []const u8 = default_server;

    if (c.getenv("DF_SERVER")) |env| {
        const text = std.mem.sliceTo(env, 0);
        var it = std.mem.splitScalar(u8, text, ':');

        host = it.next() orelse default_server;

        if (it.next()) |p| port = std.fmt.parseInt(u16, p, 10) catch port;
    }

    @memcpy(host_buf[0..@min(host.len, 63)], host[0..@min(host.len, 63)]);
    server = .{ .port = std.mem.nativeToBig(u16, port), .addr = inet_addr(&host_buf) };
}

fn pickName() void {
    if (c.getenv("DF_NAME")) |n| {
        my_name = net.nameOf(std.mem.sliceTo(n, 0));

        return;
    }

    if (!assets.mobile) {
        if (c.getenv("USER")) |n| {
            my_name = net.nameOf(std.mem.sliceTo(n, 0));

            if (my_name[0] >= 'a' and my_name[0] <= 'z') my_name[0] -= 32;

            return;
        }
    }

    my_name = net.nameOf("Player");
}

pub fn open() bool {
    if (fd >= 0) return true;

    fd = c.socket(c.AF.INET, c.SOCK.DGRAM, 0);

    if (fd < 0) return false;

    epoch = now() - 1;
    prng = std.Random.DefaultPrng.init(@intFromFloat(now() * 1e6));
    resolve();
    pickName();

    return true;
}

fn sendBytes(data: []const u8) void {
    if (fd < 0) return;

    _ = c.sendto(fd, data.ptr, data.len, 0, @ptrCast(&server), @sizeOf(Addr));
}

fn sendAsk() void {
    var w: net.Writer = .{};

    asked_at = now();

    switch (ask) {
        .create => {
            w.start(.{ .kind = .create });
            w.u8v(ask_map);
            w.u32v(nonce);
            w.name(my_name);
        },
        .join => {
            w.start(.{ .kind = .join, .code = code });
            w.name(my_name);
            w.u32v(nonce);
        },
    }

    sendBytes(w.bytes());
}

fn begin(kind: Ask) void {
    if (!open()) {
        status = .timeout;

        return;
    }

    ask = kind;
    nonce = prng.random().int(u32) | 1;
    status = .waiting;
    first_ask = now();
    sendAsk();
}

pub fn create(m: u8) void {
    ask_map = m;
    begin(.create);
}

pub fn join(room: u16) void {
    code = room;
    begin(.join);
}

pub fn cancel() void {
    if (status == .joined) leave();

    status = .idle;
}

pub fn leave() void {
    if (fd < 0 or token == 0) return;

    var w: net.Writer = .{};

    w.start(.{ .kind = .leave, .code = code, .token = token });

    for (0..3) |_| sendBytes(w.bytes());

    token = 0;
}

fn resetMatch() void {
    snap_count = 0;
    snap_head = 0;
    have_offset = false;
    claim_count = 0;
    my_known = false;
    known = @splat(false);
}

fn onJoined(r: *net.Reader, h: net.Header) void {
    const s = r.u8v();
    const m = r.u8v();
    const n = r.u32v();

    if (!r.ok or status != .waiting or n != nonce) return;

    code = h.code;
    token = h.token;
    slot = s;
    map = m;
    status = .joined;
    last_recv = now();
    lost = false;
    resetMatch();
}

fn onReject(r: *net.Reader) void {
    const why: net.Reason = @fromBackingInt(@intCast(r.u8v()));
    const n = r.u32v();

    if (status == .waiting and (n == nonce or n == 0)) {
        status = .rejected;
        reason = why;

        return;
    }

    if (status == .joined and why == .no_room and n == 0) {
        lost = true;
        last_recv = 0;
    }
}

fn store(s: net.Snapshot) void {
    if (snap_count > 0) {
        const last = snaps[(snap_head + ring - 1) % ring];

        if (s.time <= last.time) return;
    }

    snaps[snap_head] = s;
    snap_head = (snap_head + 1) % ring;
    snap_count = @min(snap_count + 1, ring);

    const sample = @as(f64, @floatFromInt(s.time)) - (now() - epoch) * 1000;

    if (!have_offset or @abs(sample - offset) > 400) {
        offset = sample;
        have_offset = true;
    } else {
        offset += (sample - offset) * 0.08;
    }
}

fn onSnapshot(r: *net.Reader, h: net.Header) void {
    if (h.token != token or status != .joined) return;

    const s = net.Snapshot.read(r);

    if (!r.ok) return;

    last_recv = now();
    lost = false;

    if (s.echo != 0) {
        const rtt = @as(f32, @floatFromInt(ms() -% s.echo)) - @as(f32, @floatFromInt(s.held));

        if (rtt >= 0 and rtt < 5000) ping_ms = if (ping_ms == 0) rtt else ping_ms + (rtt - ping_ms) * 0.2;
    }

    var keep: usize = 0;

    for (claims[0..claim_count]) |cl| {
        if (net.newer(cl.hit.id, s.hit_ack)) {
            claims[keep] = cl;
            keep += 1;
        }
    }

    claim_count = keep;
    store(s);
}

fn onRoster(r: *net.Reader, h: net.Header) void {
    if (h.token != token) return;

    const count = @min(r.u8v(), net.max_slots);

    for (0..count) |_| {
        const s = r.u8v();
        const bot = r.u8v() != 0;
        const n = r.name();

        if (!r.ok or s >= net.max_slots) return;

        names[s] = n;
        is_bot[s] = bot;
    }
}

pub fn pump() void {
    if (fd < 0) return;

    var count: u32 = 0;

    while (count < 256) : (count += 1) {
        var buf: [net.max_packet]u8 = undefined;
        const n = recv(fd, &buf, buf.len, c.MSG.DONTWAIT);

        if (n <= 0) break;

        var r: net.Reader = .{ .data = buf[0..@intCast(n)] };
        const h = r.header() orelse continue;

        switch (h.kind) {
            .joined => onJoined(&r, h),
            .reject => onReject(&r),
            .snapshot => onSnapshot(&r, h),
            .roster => onRoster(&r, h),
            else => {},
        }
    }

    const t = now();

    if (status == .waiting) {
        if (t - first_ask > give_up) {
            status = .timeout;
        } else if (t - asked_at > resend_every) {
            sendAsk();
        }
    }

    if (status == .joined and !in_match and t - keep_at > 0.5) {
        keep_at = t;
        sendInput(.{ .time = ms(), .flags = net.InFlag.loading });
    }
}

fn sendInput(in: net.Input) void {
    var w: net.Writer = .{};

    w.start(.{ .kind = .input, .code = code, .token = token });
    in.write(&w);
    sendBytes(w.bytes());
}

fn serverNow() f64 {
    return (now() - epoch) * 1000 + offset;
}

fn renderTime() u32 {
    return @intFromFloat(@max(0, serverNow() - interp_ms));
}

pub fn hit(index: usize, amount: f32, at: Vec3, head: bool, splash: bool) void {
    if (index >= net.max_slots or amount <= 0) return;

    const target: u8 = @intCast(index);

    if (claim_count > 0) {
        const last = &claims[claim_count - 1];

        if (last.sent == 0 and last.hit.target == target and last.hit.splash == splash) {
            last.hit.amount += amount;
            last.hit.head = last.hit.head or head;

            return;
        }
    }

    if (claim_count == claims.len) {
        std.mem.copyForwards(Claim, claims[0 .. claims.len - 1], claims[1..]);
        claim_count -= 1;
    }

    claims[claim_count] = .{ .hit = .{ .id = next_hit, .target = target, .amount = amount, .at = at, .head = head, .splash = splash, .view = renderTime() } };
    claim_count += 1;
    next_hit +%= 1;
}

fn findEnt(s: *const net.Snapshot, which: u8) ?net.Ent {
    for (s.ents[0..s.count]) |e| {
        if (e.slot == which) return e;
    }

    return null;
}

fn newest() ?*const net.Snapshot {
    if (snap_count == 0) return null;

    return &snaps[(snap_head + ring - 1) % ring];
}

fn bracket(t: f64) struct { a: *const net.Snapshot, b: *const net.Snapshot, k: f32 } {
    const last = newest().?;
    var i: usize = 0;

    while (i + 1 < snap_count) : (i += 1) {
        const older = &snaps[(snap_head + ring * 2 - 2 - i) % ring];
        const newer_s = &snaps[(snap_head + ring * 2 - 1 - i) % ring];
        const ta: f64 = @floatFromInt(older.time);
        const tb: f64 = @floatFromInt(newer_s.time);

        if (ta <= t and t <= tb) return .{ .a = older, .b = newer_s, .k = @floatCast((t - ta) / @max(1, tb - ta)) };
    }

    return .{ .a = last, .b = last, .k = 0 };
}

fn lerpAngle(a: f32, b: f32, k: f32) f32 {
    const tau = std.math.pi * 2;
    const d = @mod(b - a + std.math.pi, tau) - std.math.pi;

    return a + d * k;
}

fn feedKill(killer: u8, victim: u8) void {
    var k: Kill = .{ .killer = @splat(0), .victim = names[victim], .mine = killer == slot or victim == slot, .life = 5 };

    if (killer < net.max_slots and killer != victim) k.killer = names[killer];

    if (kill_count == kills.len) {
        std.mem.copyForwards(Kill, kills[0 .. kills.len - 1], kills[1..]);
        kill_count -= 1;
    }

    kills[kill_count] = k;
    kill_count += 1;
}

fn applySelf(g: *Game, me: net.Ent, latest: *const net.Snapshot) void {
    if (!my_known) {
        my_known = true;
        my_deaths = me.deaths;
        my_warp = me.warp;
    }

    if (me.warp != my_warp) {
        my_warp = me.warp;
        g.player.pos = me.pos;
        g.prev_pos = me.pos;
        g.player.vel = .{};
    }

    g.kills = me.kills;

    if (me.deaths != my_deaths) {
        my_deaths = me.deaths;

        if (g.dead <= 0) {
            g.hp = 0;
            g.dead = net.respawn_s;
            g.banner = net.respawn_s;
            g.banner_kind = .erased;
            g.buzz.add(1, 0.6, 0.35);
        }

        return;
    }

    if (me.flags & net.EntFlag.alive == 0 or g.dead > 0) return;

    const hp: f32 = @floatFromInt(me.hp);

    if (hp < g.hp - 0.5) {
        var from = g.player.center().add(math.flatDir(g.yaw).scale(5));

        if (me.attacker < net.max_slots) {
            if (findEnt(latest, me.attacker)) |a| from = a.pos.add(.{ .y = 1.4 });
        }

        const to = from.sub(g.player.center());
        const amount = g.hp - hp;

        g.since_hurt = 0;
        g.hurt_flash = 0.45;
        g.hurt_dir = std.math.atan2(to.x, to.z) - g.yaw;
        g.buzz.add(@min(1, 0.3 + amount / 30), 0.4, 0.22);
    }

    g.hp = hp;
}

fn applyOthers(g: *Game, dt: f32) void {
    const latest = newest() orelse return;
    const span = bracket(@as(f64, @floatFromInt(renderTime())));

    for (&g.bots.items, 0..) |*b, i| {
        const s: u8 = @intCast(i);

        if (s == slot or s >= net.max_slots) {
            b.active = false;

            continue;
        }

        const now_e = findEnt(latest, s) orelse {
            b.active = false;
            known[i] = false;

            continue;
        };
        const a = findEnt(span.a, s) orelse now_e;
        const z = findEnt(span.b, s) orelse a;
        const pos = a.pos.lerp(z.pos, span.k);

        if (!known[i]) {
            known[i] = true;
            seen_shots[i] = now_e.shots;
            seen_deaths[i] = now_e.deaths;
            b.* = .{ .remote = true, .active = true, .anim = @floatFromInt(i) };
        }

        if (now_e.deaths != seen_deaths[i]) {
            seen_deaths[i] = now_e.deaths;
            feedKill(now_e.attacker, s);
        }

        b.active = true;
        b.remote = true;
        b.body.pos = pos;
        b.prev = pos;
        b.body.vel = .{ .x = a.vel.x + (z.vel.x - a.vel.x) * span.k, .z = a.vel.z + (z.vel.z - a.vel.z) * span.k };
        b.body.grounded = a.flags & net.EntFlag.grounded != 0;
        b.yaw = lerpAngle(a.yaw, z.yaw, span.k);
        b.pitch = a.pitch + (z.pitch - a.pitch) * span.k;
        b.weapon = if (a.weapon < shared.weapons.specs.len) a.weapon else 0;
        b.hp = @floatFromInt(a.hp);
        b.max_hp = 100;
        b.anim += dt;
        b.flash = @max(0, b.flash - dt);
        b.shot = @max(0, b.shot - dt);

        if (a.flags & net.EntFlag.alive == 0) {
            b.dead = if (b.dead < 0) 0 else @min(3.5, b.dead + dt);
        } else {
            if (b.dead >= 0) b.anim = 0;

            b.dead = -1;
        }

        if (a.shots != seen_shots[i]) {
            seen_shots[i] = a.shots;

            if (b.dead < 0) {
                const aim = math.lookDir(b.yaw, b.pitch);
                const eye = pos.add(.{ .y = shared.movement.eye_height });
                const muzzle = eye.add(aim.scale(0.6)).add(.{ .y = -0.15 });
                const wall = shared.movement.raycast(shared.world.pieces, muzzle, aim, 120);
                const reach = if (wall) |w| w.t else 120;

                b.shot = 0.12;
                g.tracers.spawn(.{ .from = muzzle, .to = muzzle.add(aim.scale(reach)), .life = 0.07 });
            }
        }
    }
}

pub fn frame(g: *Game, dt: f32) void {
    if (!active) return;

    in_match = true;
    pump();

    const t = now();

    for (kills[0..kill_count]) |*k| k.life -= dt;

    while (kill_count > 0 and kills[0].life <= 0) {
        std.mem.copyForwards(Kill, kills[0 .. kill_count - 1], kills[1..kill_count]);
        kill_count -= 1;
    }

    if (status == .joined and t - last_recv > lost_after) lost = true;

    if (lost) {
        reconnect(t);

        for (&g.bots.items) |*b| {
            if (b.remote) b.active = false;
        }

        return;
    }

    if (status != .joined) return;

    if (newest()) |latest| {
        if (findEnt(latest, slot)) |me| applySelf(g, me, latest);
    }

    applyOthers(g, dt);

    if (t - send_at < send_every) return;

    send_at = t;

    var in: net.Input = .{
        .time = ms(),
        .view = renderTime(),
        .pos = g.player.pos,
        .vel = g.player.vel,
        .yaw = g.yaw,
        .pitch = g.pitch,
        .weapon = g.arsenal.current().weapon,
        .shots = g.shots,
    };

    if (g.dead <= 0) in.flags |= net.InFlag.alive;
    if (g.ads > 0.5) in.flags |= net.InFlag.aiming;
    if (g.player.grounded) in.flags |= net.InFlag.grounded;

    for (claims[0..claim_count]) |*cl| {
        if (in.hit_count >= net.max_hits) break;

        in.hits[in.hit_count] = cl.hit;
        in.hit_count += 1;
        cl.sent +|= 1;
    }

    sendInput(in);
}

fn reconnect(t: f64) void {
    if (status == .waiting) return;

    if (t < rejoin_at) return;

    rejoin_at = t + 1;

    if (status == .rejected and reason == .no_room) {
        create(map);

        return;
    }

    join(code);
}

const Drive = enum { unset, off, shoot, walk };

var drive_mode: Drive = .unset;
var drive_t: f32 = 0;

pub fn drive(g: *Game, controls: *game_mod.Controls) void {
    if (drive_mode == .unset) {
        const env = std.mem.sliceTo(c.getenv("DF_NETTEST") orelse "off", 0);

        drive_mode = std.meta.stringToEnum(Drive, env) orelse .off;
    }

    if (drive_mode == .off or !active or g.dead > 0) return;

    drive_t += rl.GetFrameTime();

    if (drive_mode == .walk) {
        controls.forward = if (@mod(drive_t, 6) < 3) 1 else -1;
        controls.right = @sin(drive_t * 1.3);

        return;
    }

    const eye = g.player.eye();
    var best: ?Vec3 = null;
    var best_d: f32 = 1e9;

    for (g.bots.items) |b| {
        if (!b.remote or !b.alive()) continue;

        const d = b.chest().distance(eye);

        if (d < best_d) {
            best_d = d;
            best = b.chest();
        }
    }

    const target = best orelse return;
    const to = target.sub(eye).normalize();

    g.yaw = std.math.atan2(to.x, to.z);
    g.pitch = std.math.asin(std.math.clamp(to.y, -1, 1));
    controls.fire_down = true;
    controls.fire_pressed = @mod(drive_t, 0.2) < 0.1;
}

fn print(buf: []u8, comptime fmt: []const u8, args: anytype) [:0]const u8 {
    return std.fmt.bufPrintSentinel(buf, fmt, args, 0) catch "";
}

fn pingColor() rl.Color {
    if (ping_ms < 90) return ui.green;

    if (ping_ms < 170) return ui.yellow;

    return ui.red;
}

pub fn scoreboardHeld(pad: ?c_int) bool {
    if (rl.IsKeyDown(rl.KEY_TAB)) return true;

    if (pad) |id| return rl.IsGamepadButtonDown(id, rl.GAMEPAD_BUTTON_MIDDLE_LEFT);

    return false;
}

pub fn draw(g: Game, font: rl.Font, pad: ?c_int) void {
    if (!active) return;

    const w: f32 = @floatFromInt(rl.GetScreenWidth());
    const h: f32 = @floatFromInt(rl.GetScreenHeight());
    const u = @min(h / 900, w / 1500);
    var buf: [96]u8 = undefined;
    const size = 15 * u;
    const y = 22 * u;
    const room = print(buf[0..24], "ROOM {d:0>3}", .{code});
    const ping = print(buf[24..48], "{d} MS", .{@as(u32, @intFromFloat(@round(ping_ms)))});
    const score = print(buf[48..96], "{d} K   {d} D", .{ g.kills, my_deaths });
    const rw = ui.capsWidth(font, room, size);
    const pw = ui.capsWidth(font, ping, size);
    const sw = ui.capsWidth(font, score, size);
    const gap = 26 * u;
    const dot = 12 * u;
    const total = rw + pw + dot + sw + gap * 2 + 40 * u;
    var x = w / 2 - total / 2;

    ui.card(x, y, total, 34 * u, 0.9);
    x += 20 * u;
    ui.caps(font, room, x, y + 9 * u, size, ui.accent);
    x += rw + gap;
    rl.DrawRectangleRec(.{ .x = x - gap / 2, .y = y + 10 * u, .width = 1, .height = 14 * u }, ui.fade(ui.white, 0.25));
    rl.DrawCircleV(.{ .x = x + 3.5 * u, .y = y + 17 * u }, 3.5 * u, pingColor());
    x += dot;
    ui.caps(font, ping, x, y + 9 * u, size, ui.white);
    x += pw + gap;
    rl.DrawRectangleRec(.{ .x = x - gap / 2, .y = y + 10 * u, .width = 1, .height = 14 * u }, ui.fade(ui.white, 0.25));
    ui.caps(font, score, x, y + 9 * u, size, ui.fade(ui.white, 0.75));

    drawKills(font, u);

    if (scoreboardHeld(pad)) drawBoard(font, u, w, h);

    if (lost) drawLost(font, u, w, h);
}

fn drawKills(font: rl.Font, u: f32) void {
    var row: f32 = 0;
    var buf: [64]u8 = undefined;

    for (kills[0..kill_count]) |k| {
        const size = 15 * u;
        const line = if (k.killer[0] == 0)
            print(&buf, "{s} fell", .{net.nameSlice(&k.victim)})
        else
            print(&buf, "{s}  >  {s}", .{ net.nameSlice(&k.killer), net.nameSlice(&k.victim) });
        const tw = ui.width(font, line, size);
        const alpha = @min(1, k.life * 2);
        const x = 36 * u;
        const yy = 76 * u + row * 34 * u;
        const color = if (k.mine) ui.accent else ui.red;

        ui.card(x, yy, tw + 30 * u, 28 * u, alpha);
        rl.DrawRectangleRec(.{ .x = x, .y = yy + 6 * u, .width = 2 * u, .height = 16 * u }, ui.fade(color, alpha));
        ui.text(font, line, x + 16 * u, yy + 6 * u, size, ui.fade(ui.white, alpha * 0.92));
        row += 1;
    }
}

fn drawBoard(font: rl.Font, u: f32, w: f32, h: f32) void {
    const latest = newest() orelse return;
    var order: [net.max_slots]net.Ent = undefined;
    var n: usize = 0;

    for (latest.ents[0..latest.count]) |e| {
        order[n] = e;
        n += 1;
    }

    std.mem.sort(net.Ent, order[0..n], {}, struct {
        fn more(_: void, a: net.Ent, b: net.Ent) bool {
            return a.kills > b.kills or (a.kills == b.kills and a.deaths < b.deaths);
        }
    }.more);

    const row_h = 34 * u;
    const pw = 460 * u;
    const ph = 70 * u + row_h * @as(f32, @floatFromInt(n));
    const x = (w - pw) / 2;
    const y = (h - ph) / 2;
    var buf: [48]u8 = undefined;

    ui.card(x, y, pw, ph, 0.95);
    ui.caps(font, "SCOREBOARD", x + 24 * u, y + 20 * u, 13 * u, ui.accent);
    ui.caps(font, "K", x + pw - 110 * u, y + 20 * u, 13 * u, ui.fade(ui.white, 0.5));
    ui.caps(font, "D", x + pw - 56 * u, y + 20 * u, 13 * u, ui.fade(ui.white, 0.5));

    for (order[0..n], 0..) |e, i| {
        const ry = y + 52 * u + row_h * @as(f32, @floatFromInt(i));
        const name = print(buf[0..24], "{s}", .{net.nameSlice(&names[e.slot])});
        const tint = if (e.slot == slot) ui.accent else if (e.flags & net.EntFlag.bot != 0) ui.fade(ui.white, 0.55) else ui.white;

        if (e.slot == slot) rl.DrawRectangleRec(.{ .x = x + 12 * u, .y = ry - 4 * u, .width = pw - 24 * u, .height = row_h - 4 * u }, ui.fade(ui.white, 0.06));

        ui.text(font, name, x + 24 * u, ry, 17 * u, tint);

        if (e.flags & net.EntFlag.bot != 0) ui.caps(font, "BOT", x + 24 * u + ui.width(font, name, 17 * u) + 12 * u, ry + 3 * u, 11 * u, ui.fade(ui.white, 0.4));

        ui.text(font, print(buf[24..36], "{d}", .{e.kills}), x + pw - 110 * u, ry, 17 * u, ui.white);
        ui.text(font, print(buf[36..48], "{d}", .{e.deaths}), x + pw - 56 * u, ry, 17 * u, ui.fade(ui.white, 0.7));
    }
}

fn drawLost(font: rl.Font, u: f32, w: f32, h: f32) void {
    const title: [:0]const u8 = "CONNECTION LOST";
    const sub: [:0]const u8 = if (status == .rejected and reason == .no_room) "Room closed, opening a new one" else "Reconnecting to the server";
    const ts = 34 * u;
    const ss = 16 * u;
    const pw = @max(ui.capsWidth(font, title, ts), ui.width(font, sub, ss)) + 80 * u;
    const ph = 120 * u;
    const x = (w - pw) / 2;
    const y = h * 0.3;
    const t: f32 = @floatCast(rl.GetTime());
    const head = @mod(t * 320, 360);

    rl.DrawRectangle(0, 0, @intFromFloat(w), @intFromFloat(h), ui.fade(ui.ink, 0.45));
    ui.card(x, y, pw, ph, 0.95);
    ui.caps(font, title, x + 40 * u, y + 24 * u, ts, ui.red);
    ui.text(font, sub, x + 40 * u, y + 24 * u + ts + 14 * u, ss, ui.fade(ui.white, 0.6));
    rl.DrawRing(.{ .x = x + pw - 34 * u, .y = y + 24 * u + ts / 2 }, 8 * u, 10 * u, head, head + 100, 24, ui.accent);
}
