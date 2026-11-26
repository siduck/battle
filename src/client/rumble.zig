const std = @import("std");
const builtin = @import("builtin");

const c = std.c;
const supported = builtin.os.tag == .linux and !builtin.abi.isAndroid();

const FfReplay = extern struct {
    length: u16,
    delay: u16,
};

const FfTrigger = extern struct {
    button: u16,
    interval: u16,
};

const FfRumble = extern struct {
    strong: u16,
    weak: u16,
};

const FfEffect = extern struct {
    kind: u16,
    id: i16,
    direction: u16,
    trigger: FfTrigger,
    replay: FfReplay,
    pad: u16 = 0,
    rumble: FfRumble,
    rest: [28]u8 = @splat(0),
};

const InputEvent = extern struct {
    sec: isize = 0,
    usec: isize = 0,
    kind: u16,
    code: u16,
    value: i32,
};

const ff_rumble: u16 = 0x50;
const ev_ff: u16 = 0x15;
const eviocsff: c_int = 0x40000000 | (@sizeOf(FfEffect) << 16) | (0x45 << 8) | 0x80;

pub const Rumble = struct {
    fd: c_int = -1,
    effect: i16 = -1,
    name: [128]u8 = @splat(0),
    name_len: usize = 0,
    strong: f32 = 0,
    weak: f32 = 0,
    left: f32 = 0,
    sent: f32 = 0,

    pub fn attach(r: *Rumble, gamepad_name: []const u8) void {
        if (!supported) return;

        if (r.fd >= 0 and std.mem.eql(u8, r.name[0..r.name_len], gamepad_name)) return;

        r.detach();

        const len = @min(gamepad_name.len, r.name.len);

        @memcpy(r.name[0..len], gamepad_name[0..len]);
        r.name_len = len;

        var i: u32 = 0;

        while (i < 64) : (i += 1) {
            var path_buf: [96]u8 = undefined;
            const name_path = std.fmt.bufPrintSentinel(&path_buf, "/sys/class/input/event{d}/device/name", .{i}, 0) catch continue;
            var name_buf: [160]u8 = undefined;
            const name = readSmall(name_path, &name_buf) orelse continue;

            if (!std.mem.eql(u8, std.mem.trimEnd(u8, name, "\n "), gamepad_name)) continue;

            var dev_buf: [64]u8 = undefined;
            const dev = std.fmt.bufPrintSentinel(&dev_buf, "/dev/input/event{d}", .{i}, 0) catch continue;
            const fd = c.open(dev.ptr, .{ .ACCMODE = .RDWR, .NONBLOCK = true, .CLOEXEC = true });

            if (fd < 0) continue;

            var effect: FfEffect = .{
                .kind = ff_rumble,
                .id = -1,
                .direction = 0,
                .trigger = .{ .button = 0, .interval = 0 },
                .replay = .{ .length = 100, .delay = 0 },
                .rumble = .{ .strong = 0, .weak = 0 },
            };

            if (c.ioctl(fd, eviocsff, &effect) < 0) {
                _ = c.close(fd);

                continue;
            }

            r.fd = fd;
            r.effect = effect.id;

            return;
        }
    }

    pub fn detach(r: *Rumble) void {
        if (!supported) return;

        if (r.fd >= 0) _ = c.close(r.fd);

        r.fd = -1;
        r.effect = -1;
        r.name_len = 0;
    }

    pub fn pulse(r: *Rumble, strong: f32, weak: f32, seconds: f32) void {
        r.strong = @max(r.strong, strong);
        r.weak = @max(r.weak, weak);
        r.left = @max(r.left, seconds);
    }

    pub fn update(r: *Rumble, dt: f32) void {
        r.sent -= dt;

        if (r.left <= 0) {
            r.strong = 0;
            r.weak = 0;

            return;
        }

        r.left -= dt;

        if (!supported) return;

        if (r.fd < 0 or r.sent > 0) return;

        const length: u16 = @intFromFloat(@min(1000, @max(20, r.left * 1000)));
        var effect: FfEffect = .{
            .kind = ff_rumble,
            .id = r.effect,
            .direction = 0,
            .trigger = .{ .button = 0, .interval = 0 },
            .replay = .{ .length = length, .delay = 0 },
            .rumble = .{ .strong = scale(r.strong), .weak = scale(r.weak) },
        };

        if (c.ioctl(r.fd, eviocsff, &effect) < 0) return;

        const play: InputEvent = .{ .kind = ev_ff, .code = @bitCast(r.effect), .value = 1 };

        _ = c.write(r.fd, @ptrCast(&play), @sizeOf(InputEvent));
        r.sent = 0.05;
        r.strong *= 0.6;
        r.weak *= 0.6;
    }
};

fn scale(v: f32) u16 {
    return @intFromFloat(@min(1, @max(0, v)) * 65535);
}

fn readSmall(path: [:0]const u8, buf: []u8) ?[]const u8 {
    const fd = c.open(path.ptr, .{ .ACCMODE = .RDONLY, .CLOEXEC = true });

    if (fd < 0) return null;

    defer _ = c.close(fd);

    const n = c.read(fd, buf.ptr, buf.len);

    if (n <= 0) return null;

    return buf[0..@intCast(n)];
}
