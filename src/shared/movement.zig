const math = @import("math.zig");
const geom = @import("geom.zig");
const map = @import("map.zig");
const terrain = @import("terrain.zig");
const grid = @import("grid.zig");

const Vec3 = math.Vec3;

pub const tick_rate: f32 = 60;
pub const dt: f32 = 1 / tick_rate;

pub const radius: f32 = 0.35;
pub const height: f32 = 1.7;
pub const eye_height: f32 = 1.55;
pub const step_height: f32 = 0.55;

const walk_speed: f32 = 7;
const ads_speed: f32 = 4.2;
const ground_accel: f32 = 75;
const air_accel: f32 = 28;
const air_drag: f32 = 0.35;
const gravity: f32 = 22;
const jump_speed: f32 = 8.2;
const max_fall: f32 = 45;
const snap_distance: f32 = 0.4;
const skin: f32 = 0.002;
pub const kill_y: f32 = -20;

pub const Input = struct {
    forward: f32 = 0,
    right: f32 = 0,
    jump: bool = false,
    aiming: bool = false,
    yaw: f32 = 0,
    pitch: f32 = 0,
};

pub const Player = struct {
    pos: Vec3,
    vel: Vec3 = .{},
    grounded: bool = false,

    pub fn spawn(at: Vec3) Player {
        return .{ .pos = at };
    }

    pub fn eye(p: Player) Vec3 {
        return p.pos.add(.{ .y = eye_height });
    }

    pub fn center(p: Player) Vec3 {
        return p.pos.add(.{ .y = height / 2 });
    }
};

fn footprint(pos: Vec3) geom.Rect {
    return geom.Rect.around(pos, radius);
}

fn blocks(piece: map.Piece, pos: Vec3) bool {
    const top = piece.shape.topOver(footprint(pos)) orelse return false;

    if (top <= pos.y + step_height) return false;

    return pos.y + height > piece.shape.bottom() and pos.y < top;
}

pub fn solidAt(pieces: []const map.Piece, pos: Vec3) bool {
    var near = grid.rect(pieces, footprint(pos));

    while (near.next()) |piece_ref| {
        const piece = piece_ref.*;
        const top = piece.shape.topOver(footprint(pos)) orelse continue;

        if (pos.y + height > piece.shape.bottom() and pos.y < top - skin) return true;
    }

    return false;
}

fn groundUnder(pieces: []const map.Piece, pos: Vec3, max_top: f32) f32 {
    var best = terrain.height(pos.x, pos.z);

    var near = grid.rect(pieces, footprint(pos));

    while (near.next()) |piece_ref| {
        const piece = piece_ref.*;
        const top = piece.shape.topOver(footprint(pos)) orelse continue;

        if (top <= max_top and top > best) best = top;
    }

    return best;
}

fn ceilingAbove(pieces: []const map.Piece, pos: Vec3) f32 {
    var lowest: f32 = 1e9;
    const head = pos.y + height;

    var near = grid.rect(pieces, footprint(pos));

    while (near.next()) |piece_ref| {
        const piece = piece_ref.*;
        if (piece.shape.topOver(footprint(pos)) == null) continue;

        const bottom = piece.shape.bottom();

        if (bottom >= head - skin and bottom < lowest) lowest = bottom;
    }

    return lowest;
}

fn pushOut(p: *Player, piece: map.Piece, along_x: bool, delta: f32) void {
    switch (piece.shape) {
        .cylinder => |c| {
            const dx = p.pos.x - c.base.x;
            const dz = p.pos.z - c.base.z;
            const dist = @sqrt(dx * dx + dz * dz);
            const need = c.radius + radius + skin;

            if (dist < 1e-4) {
                if (along_x) p.pos.x = c.base.x - need * @as(f32, if (delta > 0) 1 else -1) else p.pos.z = c.base.z - need * @as(f32, if (delta > 0) 1 else -1);

                return;
            }

            p.pos.x = c.base.x + dx / dist * need;
            p.pos.z = c.base.z + dz / dist * need;
        },
        else => {
            const b = piece.shape.bounds();

            if (along_x) {
                p.pos.x = if (delta > 0) b.min.x - radius - skin else b.max.x + radius + skin;
                p.vel.x = 0;
            } else {
                p.pos.z = if (delta > 0) b.min.z - radius - skin else b.max.z + radius + skin;
                p.vel.z = 0;
            }
        },
    }
}

fn moveHorizontal(p: *Player, pieces: []const map.Piece, along_x: bool, delta: f32) void {
    if (delta == 0) return;

    if (along_x) p.pos.x += delta else p.pos.z += delta;

    var near = grid.rect(pieces, geom.Rect.around(p.pos, radius + 1));

    while (near.next()) |piece_ref| {
        const piece = piece_ref.*;
        if (!blocks(piece, p.pos)) continue;

        pushOut(p, piece, along_x, delta);
    }
}

pub fn step(p: *Player, input: Input, pieces: []const map.Piece) void {
    const forward = math.flatDir(input.yaw);
    const right = forward.cross(math.up);
    var wish = forward.scale(input.forward).add(right.scale(input.right));

    if (wish.length() > 1) wish = wish.normalize();

    const speed = if (input.aiming) ads_speed else walk_speed;
    const target = wish.scale(speed);
    const accel = if (p.grounded) ground_accel else air_accel;
    const was_grounded = p.grounded;

    if (p.grounded or p.vel.flatLength() <= speed) {
        p.vel.x = math.approach(p.vel.x, target.x, accel * dt);
        p.vel.z = math.approach(p.vel.z, target.z, accel * dt);
    } else {
        const before = p.vel.flatLength();
        const pushed: Vec3 = .{ .x = p.vel.x + wish.x * air_accel * dt, .z = p.vel.z + wish.z * air_accel * dt };
        const keep = before * (1 - air_drag * dt) / @max(pushed.flatLength(), 0.001);

        p.vel.x = pushed.x * @min(1, keep);
        p.vel.z = pushed.z * @min(1, keep);
    }

    if (input.jump and p.grounded) p.vel.y = jump_speed;

    p.vel.y = @max(p.vel.y - gravity * dt, -max_fall);
    p.grounded = false;

    moveHorizontal(p, pieces, true, p.vel.x * dt);
    moveHorizontal(p, pieces, false, p.vel.z * dt);

    const stand = groundUnder(pieces, p.pos, p.pos.y + step_height);

    if (stand > p.pos.y) {
        const lifted: Vec3 = .{ .x = p.pos.x, .y = stand, .z = p.pos.z };

        if (!solidAt(pieces, lifted)) {
            p.pos.y = stand;
            p.vel.y = @max(p.vel.y, 0);
            p.grounded = true;
        }
    }

    const dy = p.vel.y * dt;

    if (dy > 0) {
        const ceiling = ceilingAbove(pieces, p.pos);

        p.pos.y += dy;

        if (p.pos.y + height > ceiling) {
            p.pos.y = ceiling - height - skin;
            p.vel.y = 0;
        }
    } else {
        const ground = groundUnder(pieces, p.pos, p.pos.y + skin);
        const next = p.pos.y + dy;

        if (next <= ground) {
            p.pos.y = ground;
            p.vel.y = 0;
            p.grounded = true;
        } else if (was_grounded and !input.jump and p.pos.y - ground <= snap_distance) {
            p.pos.y = ground;
            p.vel.y = 0;
            p.grounded = true;
        } else {
            p.pos.y = next;
        }
    }
}

pub fn launch(p: *Player, impulse: Vec3) void {
    p.vel = p.vel.add(impulse);

    if (impulse.y > 0) p.grounded = false;
}

pub fn raycast(pieces: []const map.Piece, origin: Vec3, dir: Vec3, max_t: f32) ?geom.Hit {
    var best: ?geom.Hit = null;
    var limit = max_t;

    if (terrain.raycast(origin, dir, max_t)) |t| {
        const p = origin.add(dir.scale(t));

        limit = t;
        best = .{ .t = t, .normal = terrain.normal(p.x, p.z) };
    }

    var near = grid.ray(pieces, origin, dir, limit);

    while (near.next()) |piece| {
        const hit = piece.shape.raycast(origin, dir, limit) orelse continue;

        limit = hit.t;
        best = hit;
    }

    return best;
}
