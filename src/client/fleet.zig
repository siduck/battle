const shared = @import("shared");

const Vec3 = shared.math.Vec3;
const vec = shared.math.vec;

pub const Hero = struct {
    kind: u8,
    dir: [:0]const u8,
    scale: f32,
    ground: f32,
    split: bool,
    flip: bool,
    front: Vec3,
    rear: Vec3,
    rear_spin: f32 = 1,
};

pub const heroes = [_]Hero{
    .{ .kind = 0, .dir = "rescue", .scale = 1, .ground = 0.0000, .split = true, .flip = false, .front = vec(-1.015, 0.505, 1.616), .rear = vec(-1.015, 0.505, -1.634) },
    .{ .kind = 1, .dir = "carrier", .scale = 1, .ground = 0.0000, .split = true, .flip = false, .front = vec(-1.015, 0.505, 1.707), .rear = vec(-1.015, 0.505, -1.722) },
    .{ .kind = 2, .dir = "tractor", .scale = 1, .ground = 0.0000, .split = true, .flip = false, .front = vec(-0.840, 0.414, 1.081), .rear = vec(-1.030, 0.790, -1.229), .rear_spin = 0.520 },
};
