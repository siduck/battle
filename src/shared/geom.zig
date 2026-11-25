const math = @import("math.zig");

const Vec3 = math.Vec3;

pub const Rise = enum { pos_x, neg_x, pos_z, neg_z };

pub const Aabb = struct {
    min: Vec3,
    max: Vec3,
};

pub const Ramp = struct {
    min: Vec3,
    max: Vec3,
    rise: Rise,

    pub fn heightAt(r: Ramp, x: f32, z: f32) f32 {
        const t = switch (r.rise) {
            .pos_x => (x - r.min.x) / (r.max.x - r.min.x),
            .neg_x => (r.max.x - x) / (r.max.x - r.min.x),
            .pos_z => (z - r.min.z) / (r.max.z - r.min.z),
            .neg_z => (r.max.z - z) / (r.max.z - r.min.z),
        };

        return r.min.y + math.clamp01(t) * (r.max.y - r.min.y);
    }
};

pub const Cylinder = struct {
    base: Vec3,
    radius: f32,
    height: f32,
};

pub const Shape = union(enum) {
    box: Aabb,
    ramp: Ramp,
    cylinder: Cylinder,

    pub fn bounds(s: Shape) Aabb {
        return switch (s) {
            .box => |b| b,
            .ramp => |r| .{ .min = r.min, .max = r.max },
            .cylinder => |c| .{
                .min = .{ .x = c.base.x - c.radius, .y = c.base.y, .z = c.base.z - c.radius },
                .max = .{ .x = c.base.x + c.radius, .y = c.base.y + c.height, .z = c.base.z + c.radius },
            },
        };
    }

    pub fn bottom(s: Shape) f32 {
        return s.bounds().min.y;
    }

    pub fn topOver(s: Shape, f: Rect) ?f32 {
        switch (s) {
            .box => |b| {
                if (!f.overlapsXZ(b.min, b.max)) return null;

                return b.max.y;
            },
            .ramp => |r| {
                if (!f.overlapsXZ(r.min, r.max)) return null;

                const x0 = @max(f.min_x, r.min.x);
                const x1 = @min(f.max_x, r.max.x);
                const z0 = @max(f.min_z, r.min.z);
                const z1 = @min(f.max_z, r.max.z);

                return @max(
                    @max(r.heightAt(x0, z0), r.heightAt(x1, z0)),
                    @max(r.heightAt(x0, z1), r.heightAt(x1, z1)),
                );
            },
            .cylinder => |c| {
                const cx = math.clamp01((c.base.x - f.min_x) / (f.max_x - f.min_x)) * (f.max_x - f.min_x) + f.min_x;
                const cz = math.clamp01((c.base.z - f.min_z) / (f.max_z - f.min_z)) * (f.max_z - f.min_z) + f.min_z;
                const dx = c.base.x - cx;
                const dz = c.base.z - cz;

                if (dx * dx + dz * dz >= c.radius * c.radius) return null;

                return c.base.y + c.height;
            },
        }
    }

    pub fn raycast(s: Shape, origin: Vec3, dir: Vec3, max_t: f32) ?Hit {
        return switch (s) {
            .box => |b| rayConvex(origin, dir, max_t, &boxPlanes(b.min, b.max)),
            .ramp => |r| rayConvex(origin, dir, max_t, &rampPlanes(r)),
            .cylinder => |c| rayCylinder(origin, dir, max_t, c),
        };
    }
};

pub const Rect = struct {
    min_x: f32,
    max_x: f32,
    min_z: f32,
    max_z: f32,

    pub fn around(p: Vec3, r: f32) Rect {
        return .{ .min_x = p.x - r, .max_x = p.x + r, .min_z = p.z - r, .max_z = p.z + r };
    }

    pub fn overlapsXZ(f: Rect, min: Vec3, max: Vec3) bool {
        return f.min_x < max.x and f.max_x > min.x and f.min_z < max.z and f.max_z > min.z;
    }
};

pub const Hit = struct {
    t: f32,
    normal: Vec3,
};

const Plane = struct {
    n: Vec3,
    d: f32,
};

fn boxPlanes(min: Vec3, max: Vec3) [6]Plane {
    return .{
        .{ .n = .{ .x = 1 }, .d = max.x },
        .{ .n = .{ .x = -1 }, .d = -min.x },
        .{ .n = .{ .y = 1 }, .d = max.y },
        .{ .n = .{ .y = -1 }, .d = -min.y },
        .{ .n = .{ .z = 1 }, .d = max.z },
        .{ .n = .{ .z = -1 }, .d = -min.z },
    };
}

fn rampPlanes(r: Ramp) [6]Plane {
    const box = boxPlanes(r.min, r.max);
    const rise = r.max.y - r.min.y;
    const slope: Plane = switch (r.rise) {
        .pos_x => slopePlane(.{ .x = -rise / (r.max.x - r.min.x), .y = 1 }, r.min.y - rise / (r.max.x - r.min.x) * r.min.x),
        .neg_x => slopePlane(.{ .x = rise / (r.max.x - r.min.x), .y = 1 }, r.min.y + rise / (r.max.x - r.min.x) * r.max.x),
        .pos_z => slopePlane(.{ .z = -rise / (r.max.z - r.min.z), .y = 1 }, r.min.y - rise / (r.max.z - r.min.z) * r.min.z),
        .neg_z => slopePlane(.{ .z = rise / (r.max.z - r.min.z), .y = 1 }, r.min.y + rise / (r.max.z - r.min.z) * r.max.z),
    };

    return .{ box[0], box[1], slope, box[3], box[4], box[5] };
}

fn slopePlane(n: Vec3, d: f32) Plane {
    const len = n.length();

    return .{ .n = n.scale(1 / len), .d = d / len };
}

fn rayConvex(origin: Vec3, dir: Vec3, max_t: f32, planes: []const Plane) ?Hit {
    var t_enter: f32 = 0;
    var t_exit: f32 = max_t;
    var normal: Vec3 = dir.neg();

    for (planes) |p| {
        const denom = p.n.dot(dir);
        const dist = p.n.dot(origin) - p.d;

        if (@abs(denom) < 1e-8) {
            if (dist > 0) return null;

            continue;
        }

        const t = -dist / denom;

        if (denom < 0) {
            if (t > t_enter) {
                t_enter = t;
                normal = p.n;
            }
        } else if (t < t_exit) {
            t_exit = t;
        }

        if (t_enter > t_exit) return null;
    }

    return .{ .t = t_enter, .normal = normal };
}

fn rayCylinder(origin: Vec3, dir: Vec3, max_t: f32, c: Cylinder) ?Hit {
    const top = c.base.y + c.height;
    const ox = origin.x - c.base.x;
    const oz = origin.z - c.base.z;
    const r2 = c.radius * c.radius;
    var best: ?Hit = null;

    if (ox * ox + oz * oz <= r2 and origin.y >= c.base.y and origin.y <= top) {
        return .{ .t = 0, .normal = dir.neg() };
    }

    const a = dir.x * dir.x + dir.z * dir.z;

    if (a > 1e-8) {
        const b = 2 * (ox * dir.x + oz * dir.z);
        const cc = ox * ox + oz * oz - r2;
        const disc = b * b - 4 * a * cc;

        if (disc >= 0) {
            const t = (-b - @sqrt(disc)) / (2 * a);
            const y = origin.y + dir.y * t;

            if (t >= 0 and t <= max_t and y >= c.base.y and y <= top) {
                const hx = ox + dir.x * t;
                const hz = oz + dir.z * t;

                best = .{ .t = t, .normal = (Vec3{ .x = hx, .z = hz }).normalize() };
            }
        }
    }

    if (@abs(dir.y) > 1e-8) {
        const cap_y = if (dir.y < 0) top else c.base.y;
        const t = (cap_y - origin.y) / dir.y;
        const hx = ox + dir.x * t;
        const hz = oz + dir.z * t;

        if (t >= 0 and t <= max_t and hx * hx + hz * hz <= r2) {
            if (best == null or t < best.?.t) {
                best = .{ .t = t, .normal = .{ .y = if (dir.y < 0) 1 else -1 } };
            }
        }
    }

    return best;
}

pub fn raySphere(origin: Vec3, dir: Vec3, max_t: f32, center: Vec3, radius: f32) ?f32 {
    const oc = origin.sub(center);
    const b = oc.dot(dir);
    const c = oc.dot(oc) - radius * radius;

    if (c <= 0) return 0;

    const disc = b * b - c;

    if (disc < 0) return null;

    const t = -b - @sqrt(disc);

    if (t < 0 or t > max_t) return null;

    return t;
}
