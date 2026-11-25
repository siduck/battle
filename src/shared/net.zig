const std = @import("std");
const math = @import("math.zig");

const Vec3 = math.Vec3;

pub const port: u16 = 27015;
pub const magic: u16 = 0xDF1E;
pub const version: u8 = 1;
pub const max_slots = 16;
pub const max_humans = 12;
pub const max_packet = 1200;
pub const name_len = 12;
pub const tick_hz = 60;
pub const snapshot_every = 2;
pub const tick_ms: f64 = 1000.0 / @as(f64, tick_hz);
pub const max_hits = 6;
pub const respawn_s: f32 = 3;
pub const none: u8 = 255;

pub const Kind = enum(u8) { create, join, input, leave, joined, reject, snapshot, roster, probe, probe_reply, _ };

pub const Reason = enum(u8) { no_room, full, bad_version, bad_map, busy, _ };

pub const Header = struct {
    kind: Kind,
    code: u16 = 0,
    token: u32 = 0,
};

pub const header_len = 10;

pub const Writer = struct {
    buf: [max_packet]u8 = undefined,
    len: usize = 0,

    pub fn start(w: *Writer, h: Header) void {
        w.len = 0;
        w.u16v(magic);
        w.u8v(version);
        w.u8v(@backingInt(h.kind));
        w.u16v(h.code);
        w.u32v(h.token);
    }

    pub fn bytes(w: *const Writer) []const u8 {
        return w.buf[0..w.len];
    }

    pub fn u8v(w: *Writer, v: u8) void {
        if (w.len + 1 > w.buf.len) return;

        w.buf[w.len] = v;
        w.len += 1;
    }

    pub fn i8v(w: *Writer, v: i8) void {
        w.u8v(@bitCast(v));
    }

    pub fn u16v(w: *Writer, v: u16) void {
        w.u8v(@truncate(v));
        w.u8v(@truncate(v >> 8));
    }

    pub fn i16v(w: *Writer, v: i16) void {
        w.u16v(@bitCast(v));
    }

    pub fn u32v(w: *Writer, v: u32) void {
        w.u16v(@truncate(v));
        w.u16v(@truncate(v >> 16));
    }

    pub fn f32v(w: *Writer, v: f32) void {
        w.u32v(@bitCast(v));
    }

    pub fn vec(w: *Writer, v: Vec3) void {
        w.f32v(v.x);
        w.f32v(v.y);
        w.f32v(v.z);
    }

    pub fn name(w: *Writer, n: [name_len]u8) void {
        for (n) |ch| w.u8v(ch);
    }
};

pub const Reader = struct {
    data: []const u8,
    at: usize = 0,
    ok: bool = true,

    pub fn header(r: *Reader) ?Header {
        if (r.u16v() != magic) return null;

        const ver = r.u8v();
        const kind: Kind = @fromBackingInt(@intCast(r.u8v()));
        const code = r.u16v();
        const token = r.u32v();

        if (!r.ok) return null;

        if (ver != version) return .{ .kind = .reject, .code = code, .token = 0xFFFF_FFFF };

        return .{ .kind = kind, .code = code, .token = token };
    }

    pub fn u8v(r: *Reader) u8 {
        if (r.at + 1 > r.data.len) {
            r.ok = false;

            return 0;
        }

        r.at += 1;

        return r.data[r.at - 1];
    }

    pub fn i8v(r: *Reader) i8 {
        return @bitCast(r.u8v());
    }

    pub fn u16v(r: *Reader) u16 {
        const lo: u16 = r.u8v();
        const hi: u16 = r.u8v();

        return lo | hi << 8;
    }

    pub fn i16v(r: *Reader) i16 {
        return @bitCast(r.u16v());
    }

    pub fn u32v(r: *Reader) u32 {
        const lo: u32 = r.u16v();
        const hi: u32 = r.u16v();

        return lo | hi << 16;
    }

    pub fn f32v(r: *Reader) f32 {
        const v: f32 = @bitCast(r.u32v());

        return if (std.math.isFinite(v)) v else 0;
    }

    pub fn vec(r: *Reader) Vec3 {
        return .{ .x = r.f32v(), .y = r.f32v(), .z = r.f32v() };
    }

    pub fn name(r: *Reader) [name_len]u8 {
        var n: [name_len]u8 = @splat(0);

        for (&n) |*ch| {
            const v = r.u8v();

            ch.* = if (v >= 32 and v < 127) v else 0;
        }

        return n;
    }
};

pub fn qx(v: f32) i16 {
    return @intFromFloat(std.math.clamp(@round(v * 32), -32767, 32767));
}

pub fn qy(v: f32) i16 {
    return @intFromFloat(std.math.clamp(@round(v * 64), -32767, 32767));
}

pub fn dx(v: i16) f32 {
    return @as(f32, @floatFromInt(v)) / 32;
}

pub fn dy(v: i16) f32 {
    return @as(f32, @floatFromInt(v)) / 64;
}

pub fn qyaw(yaw: f32) u16 {
    const tau = std.math.pi * 2;
    const turns = @mod(yaw, tau) / tau;

    return @intFromFloat(@mod(@round(turns * 65536), 65536));
}

pub fn dyaw(v: u16) f32 {
    return @as(f32, @floatFromInt(v)) / 65536 * std.math.pi * 2;
}

pub fn qpitch(p: f32) i8 {
    return @intFromFloat(std.math.clamp(@round(p / 1.6 * 127), -127, 127));
}

pub fn dpitch(v: i8) f32 {
    return @as(f32, @floatFromInt(v)) / 127 * 1.6;
}

pub fn qvel(v: f32) i8 {
    return @intFromFloat(std.math.clamp(@round(v * 4), -127, 127));
}

pub fn dvel(v: i8) f32 {
    return @as(f32, @floatFromInt(v)) / 4;
}

pub const Hit = struct {
    id: u16,
    target: u8,
    amount: f32,
    at: Vec3,
    head: bool,
    splash: bool,
    view: u32,

    pub fn write(h: Hit, w: *Writer) void {
        w.u16v(h.id);
        w.u8v(h.target);
        w.u16v(@intFromFloat(std.math.clamp(h.amount * 10, 0, 65535)));
        w.vec(h.at);
        w.u8v(@as(u8, @intFromBool(h.head)) | @as(u8, @intFromBool(h.splash)) << 1);
        w.u32v(h.view);
    }

    pub fn read(r: *Reader) Hit {
        const id = r.u16v();
        const target = r.u8v();
        const amount = @as(f32, @floatFromInt(r.u16v())) / 10;
        const at = r.vec();
        const flags = r.u8v();
        const view = r.u32v();

        return .{ .id = id, .target = target, .amount = amount, .at = at, .head = flags & 1 != 0, .splash = flags & 2 != 0, .view = view };
    }
};

pub const InFlag = struct {
    pub const alive: u8 = 1;
    pub const aiming: u8 = 2;
    pub const grounded: u8 = 4;
    pub const loading: u8 = 8;
};

pub const Input = struct {
    time: u32 = 0,
    view: u32 = 0,
    pos: Vec3 = .{},
    vel: Vec3 = .{},
    yaw: f32 = 0,
    pitch: f32 = 0,
    flags: u8 = 0,
    weapon: u8 = 0,
    shots: u8 = 0,
    hits: [max_hits]Hit = undefined,
    hit_count: u8 = 0,

    pub fn write(in: Input, w: *Writer) void {
        w.u32v(in.time);
        w.u32v(in.view);
        w.vec(in.pos);
        w.i16v(qx(in.vel.x));
        w.i16v(qx(in.vel.y));
        w.i16v(qx(in.vel.z));
        w.u16v(qyaw(in.yaw));
        w.i8v(qpitch(in.pitch));
        w.u8v(in.flags);
        w.u8v(in.weapon);
        w.u8v(in.shots);
        w.u8v(in.hit_count);

        for (in.hits[0..in.hit_count]) |h| h.write(w);
    }

    pub fn read(r: *Reader) Input {
        var in: Input = .{};

        in.time = r.u32v();
        in.view = r.u32v();
        in.pos = r.vec();
        in.vel = .{ .x = dx(r.i16v()), .y = dx(r.i16v()), .z = dx(r.i16v()) };
        in.yaw = dyaw(r.u16v());
        in.pitch = dpitch(r.i8v());
        in.flags = r.u8v();
        in.weapon = r.u8v();
        in.shots = r.u8v();
        in.hit_count = @min(r.u8v(), max_hits);

        for (in.hits[0..in.hit_count]) |*h| h.* = Hit.read(r);

        return in;
    }
};

pub const EntFlag = struct {
    pub const alive: u8 = 1;
    pub const bot: u8 = 2;
    pub const aiming: u8 = 4;
    pub const grounded: u8 = 8;
};

pub const Ent = struct {
    slot: u8 = 0,
    flags: u8 = 0,
    pos: Vec3 = .{},
    vel: Vec3 = .{},
    yaw: f32 = 0,
    pitch: f32 = 0,
    hp: u8 = 0,
    weapon: u8 = 0,
    shots: u8 = 0,
    kills: u8 = 0,
    deaths: u8 = 0,
    attacker: u8 = none,
    warp: u8 = 0,

    pub fn write(e: Ent, w: *Writer) void {
        w.u8v(e.slot);
        w.u8v(e.flags);
        w.i16v(qx(e.pos.x));
        w.i16v(qy(e.pos.y));
        w.i16v(qx(e.pos.z));
        w.i8v(qvel(e.vel.x));
        w.i8v(qvel(e.vel.z));
        w.u16v(qyaw(e.yaw));
        w.i8v(qpitch(e.pitch));
        w.u8v(e.hp);
        w.u8v(e.weapon);
        w.u8v(e.shots);
        w.u8v(e.kills);
        w.u8v(e.deaths);
        w.u8v(e.attacker);
        w.u8v(e.warp);
    }

    pub fn read(r: *Reader) Ent {
        var e: Ent = .{};

        e.slot = r.u8v();
        e.flags = r.u8v();
        e.pos.x = dx(r.i16v());
        e.pos.y = dy(r.i16v());
        e.pos.z = dx(r.i16v());
        e.vel.x = dvel(r.i8v());
        e.vel.z = dvel(r.i8v());
        e.yaw = dyaw(r.u16v());
        e.pitch = dpitch(r.i8v());
        e.hp = r.u8v();
        e.weapon = r.u8v();
        e.shots = r.u8v();
        e.kills = r.u8v();
        e.deaths = r.u8v();
        e.attacker = r.u8v();
        e.warp = r.u8v();

        return e;
    }
};

pub const Snapshot = struct {
    time: u32 = 0,
    echo: u32 = 0,
    held: u16 = 0,
    hit_ack: u16 = 0,
    you: u8 = 0,
    count: u8 = 0,
    ents: [max_slots]Ent = undefined,

    pub fn write(s: Snapshot, w: *Writer) void {
        w.u32v(s.time);
        w.u32v(s.echo);
        w.u16v(s.held);
        w.u16v(s.hit_ack);
        w.u8v(s.you);
        w.u8v(s.count);

        for (s.ents[0..s.count]) |e| e.write(w);
    }

    pub fn read(r: *Reader) Snapshot {
        var s: Snapshot = .{};

        s.time = r.u32v();
        s.echo = r.u32v();
        s.held = r.u16v();
        s.hit_ack = r.u16v();
        s.you = r.u8v();
        s.count = @min(r.u8v(), max_slots);

        for (s.ents[0..s.count]) |*e| e.* = Ent.read(r);

        return s;
    }
};

pub fn newer(a: u16, b: u16) bool {
    return @as(i16, @bitCast(a -% b)) > 0;
}

pub fn nameOf(text: []const u8) [name_len]u8 {
    var n: [name_len]u8 = @splat(0);
    var i: usize = 0;

    for (text) |ch| {
        if (i >= name_len) break;

        if (ch < 32 or ch >= 127) continue;

        n[i] = ch;
        i += 1;
    }

    return n;
}

pub fn nameSlice(n: *const [name_len]u8) []const u8 {
    return std.mem.sliceTo(n, 0);
}

test "roundtrip" {
    var in: Input = .{ .time = 5, .pos = .{ .x = 1, .y = 2, .z = 3 }, .yaw = 1.2, .pitch = -0.4, .hit_count = 1 };

    in.hits[0] = .{ .id = 7, .target = 3, .amount = 12.5, .at = .{ .x = 4 }, .head = true, .splash = false, .view = 99 };

    var w: Writer = .{};

    w.start(.{ .kind = .input, .code = 427, .token = 1234 });

    in.write(&w);

    var r: Reader = .{ .data = w.bytes() };
    const h = r.header().?;
    const out = Input.read(&r);

    try std.testing.expect(r.ok);
    try std.testing.expectEqual(@as(u16, 427), h.code);
    try std.testing.expectEqual(@as(u16, 7), out.hits[0].id);
    try std.testing.expect(@abs(out.yaw - 1.2) < 0.001);
    try std.testing.expect(newer(2, 65535));
}
