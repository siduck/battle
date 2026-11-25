const std = @import("std");
const math = @import("math.zig");
const map = @import("map.zig");
const terrain = @import("terrain.zig");

const Vec3 = math.Vec3;

pub const Class = enum { car, bike, scooter, cycle, tank };

pub const Spec = struct {
    name: [:0]const u8,
    class: Class,
    length: f32,
    width: f32,
    height: f32,
    seat: f32,
    wheel: f32,
    top_speed: f32,
    accel: f32,
    steer: f32 = 0.55,
    grip: f32 = 8,
    hp: f32,
};

pub const specs = [_]Spec{
    .{ .name = "Ranger Jeep", .class = .car, .length = 3.98, .width = 1.73, .height = 1.60, .seat = 0.55, .wheel = 0.339, .top_speed = 38.0, .accel = 11.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Conquer Pickup", .class = .car, .length = 5.22, .width = 2.10, .height = 1.60, .seat = 0.55, .wheel = 0.351, .top_speed = 36.0, .accel = 10.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Utility Truck", .class = .car, .length = 5.37, .width = 2.00, .height = 1.60, .seat = 0.55, .wheel = 0.356, .top_speed = 30.0, .accel = 7.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Box Truck", .class = .car, .length = 4.60, .width = 2.00, .height = 1.60, .seat = 0.55, .wheel = 0.273, .top_speed = 28.0, .accel = 6.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Armored Car", .class = .car, .length = 4.60, .width = 1.95, .height = 1.60, .seat = 0.55, .wheel = 0.349, .top_speed = 32.0, .accel = 8.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Ace Hatchback", .class = .car, .length = 3.84, .width = 1.83, .height = 1.45, .seat = 0.55, .wheel = 0.298, .top_speed = 36.0, .accel = 10.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Kiri Sedan", .class = .car, .length = 4.54, .width = 1.80, .height = 1.42, .seat = 0.55, .wheel = 0.298, .top_speed = 40.0, .accel = 11.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Traveller Van", .class = .car, .length = 5.18, .width = 2.10, .height = 1.60, .seat = 0.55, .wheel = 0.350, .top_speed = 32.0, .accel = 8.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Enforcer SUV", .class = .car, .length = 4.36, .width = 1.88, .height = 1.60, .seat = 0.55, .wheel = 0.348, .top_speed = 42.0, .accel = 12.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Taxi", .class = .car, .length = 5.27, .width = 2.09, .height = 1.60, .seat = 0.55, .wheel = 0.322, .top_speed = 38.0, .accel = 10.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "JDM Sport", .class = .car, .length = 4.68, .width = 1.97, .height = 1.35, .seat = 0.55, .wheel = 0.325, .top_speed = 52.0, .accel = 15.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "NFR Coupe", .class = .car, .length = 4.44, .width = 1.97, .height = 1.15, .seat = 0.55, .wheel = 0.303, .top_speed = 54.0, .accel = 16.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Cheetah", .class = .car, .length = 4.56, .width = 1.94, .height = 1.18, .seat = 0.55, .wheel = 0.306, .top_speed = 56.0, .accel = 16.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Interceptor", .class = .car, .length = 4.56, .width = 2.10, .height = 1.53, .seat = 0.55, .wheel = 0.325, .top_speed = 58.0, .accel = 17.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Lifted Truck", .class = .car, .length = 4.93, .width = 2.10, .height = 1.60, .seat = 0.55, .wheel = 0.349, .top_speed = 34.0, .accel = 10.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Phoenix Muscle", .class = .car, .length = 4.89, .width = 2.09, .height = 1.33, .seat = 0.55, .wheel = 0.322, .top_speed = 46.0, .accel = 13.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Stinger GT", .class = .car, .length = 4.17, .width = 1.95, .height = 1.23, .seat = 0.55, .wheel = 0.314, .top_speed = 48.0, .accel = 14.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Roadster", .class = .car, .length = 3.74, .width = 1.82, .height = 1.09, .seat = 0.55, .wheel = 0.301, .top_speed = 44.0, .accel = 13.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Fire Wagon", .class = .car, .length = 5.07, .width = 1.83, .height = 1.49, .seat = 0.55, .wheel = 0.303, .top_speed = 36.0, .accel = 10.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Hazer Turbo", .class = .car, .length = 4.23, .width = 1.97, .height = 1.13, .seat = 0.55, .wheel = 0.282, .top_speed = 46.0, .accel = 14.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Asti Stradale", .class = .car, .length = 3.90, .width = 1.84, .height = 1.39, .seat = 0.55, .wheel = 0.299, .top_speed = 50.0, .accel = 15.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "El Alamo", .class = .car, .length = 5.13, .width = 1.91, .height = 1.38, .seat = 0.55, .wheel = 0.319, .top_speed = 38.0, .accel = 11.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Street Bike", .class = .bike, .length = 2.02, .width = 0.76, .height = 1.26, .seat = 0.95, .wheel = 0.290, .top_speed = 48.0, .accel = 15.0, .steer = 0.5, .grip = 9, .hp = 260 },
    .{ .name = "Scrambler", .class = .bike, .length = 2.02, .width = 0.76, .height = 1.26, .seat = 0.95, .wheel = 0.291, .top_speed = 44.0, .accel = 14.0, .steer = 0.5, .grip = 9, .hp = 260 },
    .{ .name = "Sport Bike", .class = .bike, .length = 2.07, .width = 0.67, .height = 1.06, .seat = 0.95, .wheel = 0.284, .top_speed = 56.0, .accel = 18.0, .steer = 0.5, .grip = 9, .hp = 260 },
    .{ .name = "Police Bike", .class = .bike, .length = 2.07, .width = 0.67, .height = 1.06, .seat = 0.95, .wheel = 0.284, .top_speed = 54.0, .accel = 17.0, .steer = 0.5, .grip = 9, .hp = 260 },
    .{ .name = "Dirt Bike", .class = .bike, .length = 2.02, .width = 0.61, .height = 1.03, .seat = 0.95, .wheel = 0.285, .top_speed = 42.0, .accel = 16.0, .steer = 0.5, .grip = 9, .hp = 260 },
    .{ .name = "Chopper", .class = .bike, .length = 2.19, .width = 0.52, .height = 1.21, .seat = 0.95, .wheel = 0.306, .top_speed = 40.0, .accel = 12.0, .steer = 0.5, .grip = 9, .hp = 260 },
    .{ .name = "Enduro", .class = .bike, .length = 2.07, .width = 0.88, .height = 1.21, .seat = 0.95, .wheel = 0.309, .top_speed = 44.0, .accel = 16.0, .steer = 0.5, .grip = 9, .hp = 260 },
    .{ .name = "Scooter", .class = .bike, .length = 1.90, .width = 0.85, .height = 1.30, .seat = 0.95, .wheel = 0.209, .top_speed = 30.0, .accel = 9.0, .steer = 0.5, .grip = 9, .hp = 260 },
    .{ .name = "Moped", .class = .bike, .length = 1.90, .width = 0.90, .height = 1.29, .seat = 0.95, .wheel = 0.309, .top_speed = 28.0, .accel = 9.0, .steer = 0.5, .grip = 9, .hp = 260 },
    .{ .name = "Cruiser", .class = .bike, .length = 2.41, .width = 0.90, .height = 1.40, .seat = 0.95, .wheel = 0.346, .top_speed = 46.0, .accel = 13.0, .steer = 0.5, .grip = 9, .hp = 260 },
    .{ .name = "Mountain Bike", .class = .cycle, .length = 1.35, .width = 0.59, .height = 0.72, .seat = 1.00, .wheel = 0.213, .top_speed = 12.0, .accel = 4.0, .steer = 0.55, .grip = 10, .hp = 120 },
    .{ .name = "City Bike", .class = .cycle, .length = 1.90, .width = 0.50, .height = 1.09, .seat = 1.00, .wheel = 0.294, .top_speed = 12.0, .accel = 4.0, .steer = 0.55, .grip = 10, .hp = 120 },
    .{ .name = "Road Bike", .class = .cycle, .length = 1.90, .width = 0.50, .height = 1.09, .seat = 1.00, .wheel = 0.294, .top_speed = 14.0, .accel = 4.5, .steer = 0.55, .grip = 10, .hp = 120 },
    .{ .name = "Aventador", .class = .car, .length = 4.96, .width = 2.10, .height = 1.14, .seat = 0.55, .wheel = 0.320, .top_speed = 46.0, .accel = 16.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "720S", .class = .car, .length = 4.60, .width = 2.10, .height = 1.21, .seat = 0.55, .wheel = 0.341, .top_speed = 45.0, .accel = 17.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "993 Carrera", .class = .car, .length = 4.49, .width = 2.01, .height = 1.36, .seat = 0.55, .wheel = 0.334, .top_speed = 40.0, .accel = 15.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Venom F5", .class = .car, .length = 4.12, .width = 1.84, .height = 1.03, .seat = 0.55, .wheel = 0.252, .top_speed = 51.0, .accel = 18.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Urus", .class = .car, .length = 5.09, .width = 2.10, .height = 1.60, .seat = 0.55, .wheel = 0.357, .top_speed = 40.0, .accel = 14.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Huayra", .class = .car, .length = 4.98, .width = 2.10, .height = 1.30, .seat = 0.55, .wheel = 0.386, .top_speed = 45.0, .accel = 16.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Aventador SVJ", .class = .car, .length = 4.87, .width = 2.09, .height = 1.21, .seat = 0.55, .wheel = 0.333, .top_speed = 47.0, .accel = 17.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Centenario", .class = .car, .length = 4.98, .width = 2.10, .height = 1.16, .seat = 0.55, .wheel = 0.324, .top_speed = 49.0, .accel = 17.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "Terzo", .class = .car, .length = 4.60, .width = 2.10, .height = 0.99, .seat = 0.55, .wheel = 0.282, .top_speed = 50.0, .accel = 18.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "P72", .class = .car, .length = 4.60, .width = 2.01, .height = 1.08, .seat = 0.55, .wheel = 0.309, .top_speed = 42.0, .accel = 15.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "SF90", .class = .car, .length = 4.84, .width = 2.10, .height = 1.22, .seat = 0.55, .wheel = 0.340, .top_speed = 49.0, .accel = 18.0, .steer = 0.55, .grip = 8, .hp = 600 },
    .{ .name = "T-62", .class = .tank, .length = 9.30, .width = 3.79, .height = 2.40, .seat = 1.60, .wheel = 0.330, .top_speed = 9, .accel = 3, .steer = 1.0, .grip = 12, .hp = 3000 },
};

pub const regen_delay: f32 = 5;
pub const regen_rate: f32 = 0.08;
pub const wreck_time: f32 = 14;

pub const count = specs.len;

pub const Input = struct {
    throttle: f32 = 0,
    steer: f32 = 0,
    brake: bool = false,
    boost: bool = false,
};

pub const nitro_burn: f32 = 3.2;
pub const nitro_refill: f32 = 8;
pub const nitro_delay: f32 = 1.2;

pub const Vehicle = struct {
    kind: u8,
    pos: Vec3,
    prev: Vec3,
    yaw: f32,
    speed: f32 = 0,
    side: f32 = 0,
    vy: f32 = 0,
    steer: f32 = 0,
    lean: f32 = 0,
    pitch: f32 = 0,
    roll: f32 = 0,
    spin: f32 = 0,
    grounded: bool = true,
    occupied: bool = false,
    hp: f32 = 0,
    since_hurt: f32 = 99,
    wreck: f32 = 0,
    home: Vec3 = .{},
    home_yaw: f32 = 0,
    turret: f32 = 0,
    gun: f32 = 0,
    reload: f32 = 0,
    yaw_kick: f32 = 0,
    jolt: f32 = 0,
    jolt_roll: f32 = 0,
    impact: f32 = 0,
    nitro: f32 = 1,
    nitro_idle: f32 = 0,
    boosting: bool = false,
    boost_start: f32 = 0,
    yaw_rate: f32 = 0,
    ground_pitch: f32 = 0,
    ground_roll: f32 = 0,
    body_pitch: f32 = 0,
    body_pitch_v: f32 = 0,
    body_roll: f32 = 0,
    body_roll_v: f32 = 0,
    paved: bool = true,

    pub fn hasNitro(v: Vehicle) bool {
        return v.spec().class != .cycle and v.spec().class != .tank;
    }

    pub fn alive(v: Vehicle) bool {
        return v.wreck <= 0;
    }

    pub fn twoWheeled(v: Vehicle) bool {
        return v.spec().class != .car;
    }

    pub fn spec(v: Vehicle) Spec {
        return specs[v.kind];
    }

    pub fn forward(v: Vehicle) Vec3 {
        return math.flatDir(v.yaw);
    }

    pub fn right(v: Vehicle) Vec3 {
        return v.forward().cross(math.up);
    }

    pub fn radius(v: Vehicle) f32 {
        return @max(v.spec().width * 0.45, 0.35);
    }

    pub fn reach(v: Vehicle) f32 {
        return v.spec().length * 0.5;
    }

    pub fn center(v: Vehicle) Vec3 {
        return v.pos.add(.{ .y = v.spec().height * 0.45 });
    }

    pub fn seat(v: Vehicle) Vec3 {
        const s = v.spec();
        const back: f32 = if (s.class == .car) -s.length * 0.06 else -s.length * 0.1;

        return v.pos.add(v.forward().scale(back)).add(.{ .y = s.seat });
    }
};

const gravity: f32 = 22;

fn climbLimit(s: Spec) f32 {
    return switch (s.class) {
        .tank => 0.9,
        .car => @max(0.32, s.wheel * 1.15),
        else => @max(0.26, s.wheel),
    };
}

const Ground = struct {
    y: f32,
    piece: bool,
};

fn groundAt(pieces: []const map.Piece, p: Vec3, r: f32, climb: f32) Ground {
    var best = terrain.height(p.x, p.z);
    var piece = false;
    const box: @import("geom.zig").Rect = .{ .min_x = p.x - r, .max_x = p.x + r, .min_z = p.z - r, .max_z = p.z + r };

    for (pieces) |pc| {
        const top = pc.shape.topOver(box) orelse continue;

        if (top <= p.y + climb and top > best) {
            best = top;
            piece = true;
        }
    }

    return .{ .y = best, .piece = piece };
}

fn blocked(pieces: []const map.Piece, p: Vec3, r: f32, climb: f32, height: f32) bool {
    const box: @import("geom.zig").Rect = .{ .min_x = p.x - r, .max_x = p.x + r, .min_z = p.z - r, .max_z = p.z + r };

    for (pieces) |pc| {
        const top = pc.shape.topOver(box) orelse continue;

        if (top > p.y + climb and pc.shape.bottom() < p.y + height) return true;
    }

    return false;
}

const Contact = struct {
    y: f32,
    pitch: f32,
    roll: f32,
    paved: bool,
};

fn contact(pieces: []const map.Piece, v: Vehicle, base: Vec3) Contact {
    const s = v.spec();
    const climb = climbLimit(s);
    const two = s.class != .car and s.class != .tank;
    const half_l = s.length * 0.34;
    const half_w: f32 = if (two) 0 else s.width * 0.4;
    const f = v.forward().scale(half_l);
    const r = v.right().scale(half_w);
    const pr: f32 = if (two) 0.12 else 0.18;
    const fl = groundAt(pieces, base.add(f).sub(r), pr, climb);
    const fr = groundAt(pieces, base.add(f).add(r), pr, climb);
    const bl = groundAt(pieces, base.sub(f).sub(r), pr, climb);
    const br = groundAt(pieces, base.sub(f).add(r), pr, climb);
    const front = (fl.y + fr.y) * 0.5;
    const back = (bl.y + br.y) * 0.5;
    const left = (fl.y + bl.y) * 0.5;
    const right_y = (fr.y + br.y) * 0.5;
    const mean = (front + back) * 0.5;
    const high = @max(@max(fl.y, fr.y), @max(bl.y, br.y));
    const pitch = std.math.clamp(std.math.atan2(front - back, half_l * 2), -0.6, 0.6);
    const roll = if (two) 0 else std.math.clamp(std.math.atan2(right_y - left, @max(half_w * 2, 0.5)), -0.5, 0.5);
    const road = terrain.roadDistance(base.x, base.z) < terrain.road_half + 1;

    return .{
        .y = @max(mean, high - 0.12),
        .pitch = pitch,
        .roll = roll,
        .paved = fl.piece or br.piece or road or terrain.current == .facility or terrain.current == .prism,
    };
}

fn surfaceGrip(paved: bool) f32 {
    if (paved) return 1;

    return switch (terrain.current) {
        .desert => 0.72,
        .valley, .islands, .conquest => 0.84,
        else => 0.95,
    };
}

fn mass(s: Spec) f32 {
    return switch (s.class) {
        .tank => 10,
        .car => 1.5,
        .bike, .scooter => 0.45,
        .cycle => 0.25,
    };
}

pub fn massOf(v: Vehicle) f32 {
    return mass(v.spec());
}

fn hull(pieces: []const map.Piece, v: Vehicle, at: Vec3, dir_sign: f32) bool {
    const s = v.spec();
    const climb = climbLimit(s);
    const h = @max(1.0, s.height * 0.9);
    const fwd = v.forward();
    const side = v.right();
    const r = @max(s.width * 0.42, 0.3);
    const half = @max(s.length * 0.5 - r, 0);

    if (blocked(pieces, at, r, climb, h)) return true;

    const lead = at.add(fwd.scale(half * dir_sign));

    if (blocked(pieces, lead, r, climb, h)) return true;

    if (s.class == .car or s.class == .tank) {
        const w = side.scale(s.width * 0.28);

        if (blocked(pieces, lead.add(w), r * 0.6, climb, h) or blocked(pieces, lead.sub(w), r * 0.6, climb, h)) return true;
    }

    return false;
}

pub fn step(v: *Vehicle, input: Input, pieces: []const map.Piece, dt: f32) void {
    const s = v.spec();
    const two = s.class != .car and s.class != .tank;
    const tank = s.class == .tank;
    const throttle = std.math.clamp(input.throttle, -1, 1);

    v.prev = v.pos;

    const was = v.boosting;

    v.boosting = input.boost and v.hasNitro() and v.nitro > 0.02 and v.speed > -0.5;

    if (v.boosting) {
        v.nitro = @max(0, v.nitro - dt / nitro_burn);
        v.nitro_idle = 0;
    } else {
        v.nitro_idle += dt;

        if (v.nitro_idle > nitro_delay) v.nitro = @min(1, v.nitro + dt / nitro_refill);
    }

    if (v.boosting and !was) v.boost_start = 0.35;

    v.boost_start = @max(0, v.boost_start - dt);

    const mu = surfaceGrip(v.paved);
    const soft = 1 - mu;
    const top = (if (v.boosting) s.top_speed * 1.35 else s.top_speed) * (1 - soft * 0.5);
    const before = v.speed;
    var long_accel: f32 = 0;

    if (v.grounded) {
        const ratio = math.clamp01(v.speed / top);
        const curve = std.math.pow(f32, 1 - ratio, 0.7);

        if (v.boosting) v.speed += s.accel * 1.6 * dt * curve;

        if (throttle > 0) {
            if (v.speed < -0.5) {
                v.speed = math.approach(v.speed, 0, brakeDecel(s) * throttle * dt);
            } else {
                v.speed += throttle * s.accel * dt * curve;
            }
        } else if (throttle < 0) {
            if (v.speed > 0.5) {
                v.speed = math.approach(v.speed, 0, brakeDecel(s) * -throttle * dt);
            } else {
                const reverse_top = s.top_speed * (if (tank) @as(f32, 0.6) else 0.28);

                v.speed = @max(v.speed + throttle * s.accel * 0.55 * dt, -reverse_top);
            }
        } else {
            v.speed = math.approach(v.speed, 0, (2.2 + soft * 4) * dt);
        }

        if (input.brake and !tank) v.speed = math.approach(v.speed, 0, (if (two) brakeDecel(s) else 3.5) * dt);

        v.speed = math.approach(v.speed, 0, (soft * 1.5 + v.speed * v.speed * 0.0004) * dt);

        if (v.speed > top) v.speed = math.approach(v.speed, top, s.accel * 0.6 * dt);

    }

    const steer_limit = s.steer / (1 + @abs(v.speed) / 16);
    const steer_target = std.math.clamp(input.steer, -1, 1) * @max(steer_limit, s.steer * 0.18);
    const toward_center = @abs(steer_target) < @abs(v.steer);

    v.steer = math.approach(v.steer, steer_target, dt * (if (toward_center) @as(f32, 6) else 3.5));

    const wheelbase = @max(s.length * 0.6, 0.9);
    const handbrake = input.brake and !two and !tank and @abs(v.speed) > 4;
    const lat_max = mu * gravity * (if (two) @as(f32, 0.95) else 1.05);
    var target_rate: f32 = 0;

    if (tank) {
        target_rate = input.steer * 0.85 * (if (v.speed < -0.3) @as(f32, -1) else 1);
    } else if (v.grounded) {
        target_rate = v.speed * @tan(v.steer) / wheelbase;

        const cap = lat_max * 1.25 / @max(@abs(v.speed), 1);

        target_rate = std.math.clamp(target_rate, -cap, cap);

        if (handbrake) target_rate *= 1.7;
    }

    const yaw_response: f32 = if (!v.grounded) 0.5 else if (handbrake) 3 else if (two) 7 else 9;

    v.yaw_rate += (target_rate - v.yaw_rate) * @min(1, dt * yaw_response);

    const fwd0 = v.forward();
    const right0 = v.right();
    const world_vel = fwd0.scale(v.speed).add(right0.scale(v.side));

    v.yaw -= v.yaw_rate * dt + v.yaw_kick * dt;
    v.yaw_kick = math.approach(v.yaw_kick, 0, dt * (3 + @abs(v.yaw_kick) * 2));

    const fwd = v.forward();
    const right = v.right();

    v.speed = world_vel.dot(fwd);
    v.side = world_vel.dot(right);

    if (v.grounded) {
        const counter = v.side * v.steer < 0;
        const lat_grip: f32 = if (tank) 60 else if (handbrake) lat_max * 0.22 else if (counter) lat_max * 1.3 else lat_max;
        const slide = @abs(v.side);

        v.side = math.approach(v.side, 0, lat_grip * dt);

        if (slide > 1) v.speed = math.approach(v.speed, 0, slide * 0.35 * dt);
    }

    const travel = fwd.scale(v.speed * dt).add(right.scale(v.side * dt));
    const dist = @sqrt(travel.x * travel.x + travel.z * travel.z);
    const steps: usize = @intFromFloat(@min(8, @ceil(dist / 0.35) + 1));
    const part = travel.scale(1 / @as(f32, @floatFromInt(steps)));
    const dir_sign: f32 = if (v.speed < -0.2) -1 else 1;
    var stopped = false;
    var normal_speed: f32 = 0;

    for (0..steps) |_| {
        const full = Vec3{ .x = v.pos.x + part.x, .y = v.pos.y, .z = v.pos.z + part.z };

        if (!hull(pieces, v.*, full, dir_sign)) {
            v.pos.x = full.x;
            v.pos.z = full.z;
            continue;
        }

        const only_x = Vec3{ .x = v.pos.x + part.x, .y = v.pos.y, .z = v.pos.z };
        const only_z = Vec3{ .x = v.pos.x, .y = v.pos.y, .z = v.pos.z + part.z };
        const vel = fwd.scale(v.speed).add(right.scale(v.side));

        if (@abs(part.x) > 1e-5 and !hull(pieces, v.*, only_x, dir_sign)) {
            v.pos.x = only_x.x;
            normal_speed = @max(normal_speed, @abs(vel.z));
            slideAlong(v, .{ .x = vel.x }, fwd, right);
        } else if (@abs(part.z) > 1e-5 and !hull(pieces, v.*, only_z, dir_sign)) {
            v.pos.z = only_z.z;
            normal_speed = @max(normal_speed, @abs(vel.x));
            slideAlong(v, .{ .z = vel.z }, fwd, right);
        } else {
            normal_speed = @max(normal_speed, vel.length());
            stopped = true;
        }

        break;
    }

    if (stopped) {
        hit(v, if (normal_speed > 0) normal_speed * dir_sign else 0, v.side);
        v.speed *= -0.15;
        v.side *= -0.15;
        v.yaw_rate *= 0.3;
    } else if (normal_speed > 3) {
        hit(v, normal_speed * dir_sign * 0.6, v.side);
    }

    if (v.grounded) long_accel = (v.speed - before) / dt;

    const lat_accel = v.speed * v.yaw_rate;
    const bound = terrain.play - 2;

    v.pos.x = std.math.clamp(v.pos.x, -bound, bound);
    v.pos.z = std.math.clamp(v.pos.z, -bound, bound);

    const touch = contact(pieces, v.*, v.pos);
    const ground = touch.y;

    v.paved = touch.paved;

    if (v.grounded) {
        if (ground >= v.pos.y - 0.02) {
            const rise = ground - v.pos.y;

            v.pos.y = ground;
            v.vy = 0;

            if (rise > 0.05) v.body_pitch_v += rise * 1.5 * std.math.sign(v.speed);
        } else if (v.pos.y - ground < 0.08 + @abs(v.speed) * 0.006) {
            v.pos.y = ground;
            v.vy = 0;
        } else {
            v.grounded = false;
            v.vy = @min(v.vy, 0);
        }
    }

    if (!v.grounded) {
        v.vy -= gravity * dt;
        v.pos.y += v.vy * dt;

        if (v.pos.y <= ground) {
            const landing = -v.vy;

            v.pos.y = ground;
            v.grounded = true;
            v.vy = 0;

            if (landing > 3) {
                v.body_pitch_v -= landing * 0.05;
                v.speed *= 1 - @min(0.25, landing * 0.015);
                v.impact = @max(v.impact, @min(1, landing / 14));
            }
        }
    }

    if (v.grounded) {
        v.ground_pitch += (touch.pitch - v.ground_pitch) * @min(1, dt * 12);
        v.ground_roll += (touch.roll - v.ground_roll) * @min(1, dt * 12);
    } else {
        const glide = std.math.clamp(std.math.atan2(v.vy, @max(@abs(v.speed), 4)) * 0.6, -0.5, 0.4);

        v.ground_pitch += (glide - v.ground_pitch) * @min(1, dt * 1.5);
        v.ground_roll += (0 - v.ground_roll) * @min(1, dt * 1.5);
    }

    const soft_body: f32 = if (tank) 0.004 else if (two) 0.006 else 0.012;
    const pitch_target = if (v.grounded) std.math.clamp(long_accel * soft_body, -0.09, 0.07) else 0;
    const roll_target = if (v.grounded and !two) std.math.clamp(lat_accel * soft_body * 0.55, -0.08, 0.08) else 0;
    const k: f32 = 90;
    const c: f32 = 13;

    v.body_pitch_v += ((pitch_target - v.body_pitch) * k - v.body_pitch_v * c) * dt;
    v.body_pitch += v.body_pitch_v * dt;
    v.body_roll_v += ((roll_target - v.body_roll) * k - v.body_roll_v * c) * dt;
    v.body_roll += v.body_roll_v * dt;

    const target_lean = if (two) std.math.clamp(-std.math.atan2(lat_accel, gravity), -0.75, 0.75) else 0;

    v.jolt = math.approach(v.jolt, 0, dt * 2.2) * (1 - @min(1, dt * 3));
    v.jolt_roll = math.approach(v.jolt_roll, 0, dt * 2.2) * (1 - @min(1, dt * 3));
    v.impact = @max(0, v.impact - dt * 2.5);

    const wobble = @sin(v.impact * 38) * v.impact * 0.5;

    v.pitch = v.ground_pitch + v.body_pitch + v.jolt * (1 + wobble);
    v.roll = v.ground_roll + v.body_roll + v.jolt_roll * (1 - wobble);
    v.lean += (target_lean - v.lean) * @min(1, dt * 7);
    v.spin += v.speed * dt / @max(s.wheel, 0.1);
}

fn brakeDecel(s: Spec) f32 {
    return switch (s.class) {
        .tank => 7,
        .car => 15,
        .bike, .scooter => 13,
        .cycle => 7,
    };
}

fn slideAlong(v: *Vehicle, kept: Vec3, fwd: Vec3, right: Vec3) void {
    const scrub: f32 = 0.85;

    v.speed = kept.dot(fwd) * scrub;
    v.side = kept.dot(right) * scrub;
    v.yaw_rate *= 0.6;
}

pub fn hit(v: *Vehicle, speed: f32, side: f32) void {
    const force = @abs(speed);

    if (force < 2.5) return;

    const k = @min(1, force / 30);
    const glance = std.math.clamp(side / @max(force, 1) + @sin(v.pos.x * 3.1 + v.pos.z * 1.7) * 0.35, -1, 1);
    const two = v.spec().class != .car and v.spec().class != .tank;

    v.jolt = -std.math.sign(speed) * k * (if (two) @as(f32, 0.3) else 0.16);
    v.jolt_roll = glance * k * (if (two) @as(f32, 0.6) else 0.2);
    v.yaw_kick += glance * k * 2.5;
    v.impact = @max(v.impact, k);

    if (force > 16 and v.grounded) v.vy = 0.6 + k * 1.6;
}

pub fn settle(v: *Vehicle, pieces: []const map.Piece) void {
    v.pos.y = terrain.height(v.pos.x, v.pos.z);

    const touch = contact(pieces, v.*, v.pos);

    v.pos.y = touch.y;
    v.ground_pitch = touch.pitch;
    v.ground_roll = touch.roll;
    v.pitch = touch.pitch;
    v.roll = touch.roll;
    v.body_pitch = 0;
    v.body_roll = 0;
    v.body_pitch_v = 0;
    v.body_roll_v = 0;
    v.yaw_rate = 0;
    v.paved = touch.paved;
    v.grounded = true;
    v.vy = 0;
    v.prev = v.pos;
}

pub fn spawn(kind: u8, pos: Vec3, yaw: f32) Vehicle {
    return .{ .kind = kind, .pos = pos, .prev = pos, .yaw = yaw, .hp = specs[kind].hp, .home = pos, .home_yaw = yaw };
}

pub fn usableBy(pos: Vec3, v: Vehicle) bool {
    return pos.distance(v.pos) < v.spec().length * 0.5 + 1.8;
}

