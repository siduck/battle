pub const Vec3 = struct {
    x: f32 = 0,
    y: f32 = 0,
    z: f32 = 0,

    pub fn add(a: Vec3, b: Vec3) Vec3 {
        return .{ .x = a.x + b.x, .y = a.y + b.y, .z = a.z + b.z };
    }

    pub fn sub(a: Vec3, b: Vec3) Vec3 {
        return .{ .x = a.x - b.x, .y = a.y - b.y, .z = a.z - b.z };
    }

    pub fn scale(a: Vec3, s: f32) Vec3 {
        return .{ .x = a.x * s, .y = a.y * s, .z = a.z * s };
    }

    pub fn mul(a: Vec3, b: Vec3) Vec3 {
        return .{ .x = a.x * b.x, .y = a.y * b.y, .z = a.z * b.z };
    }

    pub fn neg(a: Vec3) Vec3 {
        return .{ .x = -a.x, .y = -a.y, .z = -a.z };
    }

    pub fn dot(a: Vec3, b: Vec3) f32 {
        return a.x * b.x + a.y * b.y + a.z * b.z;
    }

    pub fn cross(a: Vec3, b: Vec3) Vec3 {
        return .{
            .x = a.y * b.z - a.z * b.y,
            .y = a.z * b.x - a.x * b.z,
            .z = a.x * b.y - a.y * b.x,
        };
    }

    pub fn length(a: Vec3) f32 {
        return @sqrt(a.dot(a));
    }

    pub fn flatLength(a: Vec3) f32 {
        return @sqrt(a.x * a.x + a.z * a.z);
    }

    pub fn distance(a: Vec3, b: Vec3) f32 {
        return a.sub(b).length();
    }

    pub fn normalize(a: Vec3) Vec3 {
        const len = a.length();

        if (len < 1e-6) return .{};

        return a.scale(1 / len);
    }

    pub fn lerp(a: Vec3, b: Vec3, t: f32) Vec3 {
        return a.add(b.sub(a).scale(t));
    }
};

pub fn vec(x: f32, y: f32, z: f32) Vec3 {
    return .{ .x = x, .y = y, .z = z };
}

pub const up: Vec3 = .{ .y = 1 };

pub fn lookDir(yaw: f32, pitch: f32) Vec3 {
    const cp = @cos(pitch);

    return .{ .x = cp * @sin(yaw), .y = @sin(pitch), .z = cp * @cos(yaw) };
}

pub fn flatDir(yaw: f32) Vec3 {
    return .{ .x = @sin(yaw), .z = @cos(yaw) };
}

pub fn clamp01(v: f32) f32 {
    return @min(1, @max(0, v));
}

pub fn approach(current: f32, target: f32, max_delta: f32) f32 {
    if (current < target) return @min(current + max_delta, target);

    return @max(current - max_delta, target);
}
