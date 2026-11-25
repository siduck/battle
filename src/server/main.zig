const std = @import("std");
const shared = @import("shared");
const room_mod = @import("room.zig");

const c = std.c;
const net = shared.net;
const Map = shared.terrain.Map;
const map_count = std.enums.values(Map).len;

extern "c" fn signal(sig: c_int, handler: ?*const anyopaque) ?*const anyopaque;
extern "c" fn recv(fd: c_int, buf: [*]u8, len: usize, flags: c_int) isize;
extern "c" fn send(fd: c_int, buf: [*]const u8, len: usize, flags: c_int) isize;
extern "c" fn inet_addr(cp: [*:0]const u8) u32;

pub const Addr = c.sockaddr.in;

pub fn now() f64 {
    var ts: c.timespec = undefined;

    _ = c.clock_gettime(c.CLOCK.MONOTONIC, &ts);

    return @as(f64, @floatFromInt(ts.sec)) + @as(f64, @floatFromInt(ts.nsec)) / 1e9;
}

pub fn log(comptime fmt: []const u8, args: anytype) void {
    var buf: [512]u8 = undefined;
    const line = std.fmt.bufPrint(&buf, fmt ++ "\n", args) catch return;

    _ = c.write(1, line.ptr, line.len);
}

pub fn sendTo(fd: c_int, addr: Addr, data: []const u8) void {
    _ = c.sendto(fd, data.ptr, data.len, 0, @ptrCast(&addr), @sizeOf(Addr));
}

pub fn addrText(addr: Addr, buf: []u8) []const u8 {
    const ip: [4]u8 = @bitCast(addr.addr);

    return std.fmt.bufPrint(buf, "{d}.{d}.{d}.{d}:{d}", .{ ip[0], ip[1], ip[2], ip[3], std.mem.bigToNative(u16, addr.port) }) catch "?";
}

const Route = struct {
    map: ?u8 = null,
    nonce: u32 = 0,
    addr: u32 = 0,
    port: u16 = 0,
};

const Worker = struct {
    pid: c.pid_t,
    fd: c_int,
};

var routes: [1000]Route = @splat(.{});
var workers: [map_count]?Worker = @splat(null);
var udp: c_int = -1;
var fill: u8 = 6;
var prng: std.Random.DefaultPrng = undefined;

fn reject(addr: Addr, code: u16, reason: net.Reason, nonce: u32) void {
    var w: net.Writer = .{};

    w.start(.{ .kind = .reject, .code = code });

    w.u8v(@backingInt(reason));
    w.u32v(nonce);
    sendTo(udp, addr, w.bytes());
}

fn spawnWorker(map: u8) ?Worker {
    var pair: [2]c.fd_t = undefined;

    if (c.socketpair(c.AF.UNIX, c.SOCK.DGRAM, 0, &pair) != 0) return null;

    const pid = c.fork();

    if (pid < 0) {
        _ = c.close(pair[0]);
        _ = c.close(pair[1]);

        return null;
    }

    if (pid == 0) {
        _ = c.close(pair[0]);
        _ = c.prctl(1, @as(c_ulong, 15));

        for (workers) |maybe| {
            if (maybe) |w| _ = c.close(w.fd);
        }

        room_mod.worker(@fromBackingInt(@intCast(map)), udp, pair[1], fill);
        c._exit(0);
    }

    _ = c.close(pair[1]);
    log("worker {s} pid {d}", .{ @tagName(@as(Map, @fromBackingInt(@intCast(map)))), pid });

    return .{ .pid = pid, .fd = pair[0] };
}

fn forward(map: u8, addr: Addr, data: []const u8) bool {
    if (workers[map] == null) workers[map] = spawnWorker(map);

    const w = workers[map] orelse return false;
    var buf: [net.max_packet + @sizeOf(Addr)]u8 = undefined;

    @memcpy(buf[0..@sizeOf(Addr)], std.mem.asBytes(&addr));
    @memcpy(buf[@sizeOf(Addr)..][0..data.len], data);

    return send(w.fd, &buf, @sizeOf(Addr) + data.len, c.MSG.DONTWAIT) > 0;
}

fn freeCode() ?u16 {
    var tries: u32 = 0;

    while (tries < 400) : (tries += 1) {
        const code = prng.random().intRangeAtMost(u16, 100, 999);

        if (routes[code].map == null) return code;
    }

    for (100..1000) |code| {
        if (routes[code].map == null) return @intCast(code);
    }

    return null;
}

fn handle(addr: Addr, data: []u8) void {
    var r: net.Reader = .{ .data = data };
    const h = r.header() orelse return;

    if (h.kind == .reject and h.token == 0xFFFF_FFFF) return reject(addr, h.code, .bad_version, 0);

    switch (h.kind) {
        .probe => {
            var w: net.Writer = .{};

            w.start(.{ .kind = .probe_reply });

            w.u32v(r.u32v());
            sendTo(udp, addr, w.bytes());
        },
        .create => {
            const map = r.u8v();
            const nonce = r.u32v();

            if (!r.ok) return;

            if (map >= map_count) return reject(addr, 0, .bad_map, nonce);

            var code: ?u16 = null;

            for (routes, 0..) |route, i| {
                if (route.map != null and route.nonce == nonce and route.addr == addr.addr and route.port == addr.port) code = @intCast(i);
            }

            if (code == null) {
                code = freeCode() orelse return reject(addr, 0, .busy, nonce);
                routes[code.?] = .{ .map = map, .nonce = nonce, .addr = addr.addr, .port = addr.port };

                var text: [32]u8 = undefined;

                log("room {d} created on {s} by {s}", .{ code.?, @tagName(@as(Map, @fromBackingInt(@intCast(map)))), addrText(addr, &text) });
            }

            std.mem.writeInt(u16, data[4..6], code.?, .little);

            if (!forward(map, addr, data)) {
                routes[code.?] = .{};
                reject(addr, 0, .busy, nonce);
            }
        },
        else => {
            if (h.code >= routes.len) return;

            const map = routes[h.code].map orelse {
                if (h.kind == .join or h.kind == .input) {
                    const nonce = if (h.kind == .join) blk: {
                        _ = r.name();

                        break :blk r.u32v();
                    } else 0;

                    reject(addr, h.code, .no_room, nonce);
                }

                return;
            };

            if (!forward(map, addr, data)) reject(addr, h.code, .busy, 0);
        },
    }
}

fn workerMessage(map: u8) void {
    const w = workers[map] orelse return;
    var buf: [64]u8 = undefined;

    while (true) {
        const n = recv(w.fd, &buf, buf.len, c.MSG.DONTWAIT);

        if (n == 0 or (n < 0 and c.errno(n) != .AGAIN)) {
            log("worker {s} gone", .{@tagName(@as(Map, @fromBackingInt(@intCast(map))))});
            _ = c.close(w.fd);
            workers[map] = null;

            for (&routes) |*route| {
                if (route.map == map) route.* = .{};
            }

            return;
        }

        if (n < 0) return;

        if (n >= 3 and buf[0] == 'x') {
            const code = std.mem.readInt(u16, buf[1..3], .little);

            if (code < routes.len and routes[code].map == map) {
                routes[code] = .{};
                log("room {d} closed", .{code});
            }
        }
    }
}

fn probe(host: [:0]const u8, port: u16) void {
    const fd = c.socket(c.AF.INET, c.SOCK.DGRAM, 0);
    const addr: Addr = .{ .port = std.mem.nativeToBig(u16, port), .addr = inet_addr(host.ptr) };
    var got: u32 = 0;
    var best: f64 = 1e9;
    var sum: f64 = 0;
    var i: u32 = 0;

    while (i < 10) : (i += 1) {
        const start = now();
        var w: net.Writer = .{};

        w.start(.{ .kind = .probe });

        w.u32v(i);
        sendTo(fd, addr, w.bytes());

        var fds = [_]c.pollfd{.{ .fd = fd, .events = c.POLL.IN, .revents = 0 }};

        while (now() - start < 1) {
            const left: c_int = @intFromFloat((1 - (now() - start)) * 1000);

            if (c.poll(&fds, 1, @max(1, left)) <= 0) continue;

            var buf: [64]u8 = undefined;
            const n = recv(fd, &buf, buf.len, 0);

            if (n <= 0) continue;

            var r: net.Reader = .{ .data = buf[0..@intCast(n)] };
            const h = r.header() orelse continue;

            if (h.kind != .probe_reply or r.u32v() != i) continue;

            const rtt = (now() - start) * 1000;

            got += 1;
            sum += rtt;
            best = @min(best, rtt);
            log("reply {d}: {d:.1} ms", .{ i, rtt });

            break;
        }
    }

    if (got == 0) {
        log("no reply from {s}:{d}", .{ host, port });
        c._exit(1);
    }

    log("{d}/10 replies, min {d:.1} ms, avg {d:.1} ms", .{ got, best, sum / @as(f64, @floatFromInt(got)) });
}

pub fn main(init: std.process.Init.Minimal) void {
    var port: u16 = net.port;
    var args = init.args.iterate();

    _ = args.next();

    while (args.next()) |arg| {
        if (std.mem.eql(u8, arg, "--port")) port = std.fmt.parseInt(u16, args.next() orelse "", 10) catch port;

        if (std.mem.eql(u8, arg, "--fill")) fill = std.fmt.parseInt(u8, args.next() orelse "", 10) catch fill;

        if (std.mem.eql(u8, arg, "--probe")) return probe(args.next() orelse "127.0.0.1", port);
    }

    prng = std.Random.DefaultPrng.init(@intFromFloat(now() * 1e6));
    _ = signal(17, @ptrFromInt(1));
    _ = signal(13, @ptrFromInt(1));

    udp = c.socket(c.AF.INET, c.SOCK.DGRAM, 0);

    const bind_addr: Addr = .{ .port = std.mem.nativeToBig(u16, port), .addr = 0 };

    if (c.bind(udp, @ptrCast(&bind_addr), @sizeOf(Addr)) != 0) {
        log("bind udp {d} failed", .{port});
        c._exit(1);
    }

    log("battle-server listening on udp {d}, bot fill {d}", .{ port, fill });

    while (true) {
        var fds: [1 + map_count]c.pollfd = undefined;
        var owners: [1 + map_count]usize = undefined;
        var n: usize = 1;

        fds[0] = .{ .fd = udp, .events = c.POLL.IN, .revents = 0 };

        for (workers, 0..) |maybe, m| {
            const w = maybe orelse continue;

            fds[n] = .{ .fd = w.fd, .events = c.POLL.IN, .revents = 0 };
            owners[n] = m;
            n += 1;
        }

        if (c.poll(&fds, @intCast(n), 1000) <= 0) continue;

        if (fds[0].revents != 0) {
            var count: u32 = 0;

            while (count < 512) : (count += 1) {
                var buf: [net.max_packet]u8 = undefined;
                var from: Addr = undefined;
                var len: c.socklen_t = @sizeOf(Addr);
                const got = c.recvfrom(udp, &buf, buf.len, c.MSG.DONTWAIT, @ptrCast(&from), &len);

                if (got <= 0) break;

                handle(from, buf[0..@intCast(got)]);
            }
        }

        for (fds[1..n], owners[1..n]) |f, m| {
            if (f.revents != 0) workerMessage(@intCast(m));
        }
    }
}
