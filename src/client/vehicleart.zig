const std = @import("std");

pub var tick: ?*const fn () void = null;
const rl = @import("raylib");
const shared = @import("shared");
const mesh = @import("mesh.zig");
const gfx = @import("gfx.zig");
const fleet = @import("fleet.zig");
const assets = @import("assets.zig");

const vehicle = shared.vehicle;
const Vec3 = shared.math.Vec3;
const vec = shared.math.vec;
const Basis = mesh.Basis;

pub const Hero = fleet.Hero;
pub const heroes = fleet.heroes;

const HeroArt = struct {
    body: rl.Model,
    wheel: ?rl.Model = null,
    rear: ?rl.Model = null,
    caliper: ?rl.Model = null,
    turret: ?rl.Model = null,
    barrel: ?rl.Model = null,
};

pub const Art = struct {
    models: [vehicle.count]?HeroArt = @splat(null),

    pub fn build(cars_dir: []const u8) Art {
        var a: Art = .{};

        for (heroes) |h| {
            if (tick) |t| t();

            const body = load(cars_dir, h.dir, "body") orelse continue;
            var art: HeroArt = .{ .body = body };

            if (h.split and h.two) {
                art.wheel = load(cars_dir, h.dir, "wheelF");
                art.rear = load(cars_dir, h.dir, "wheelR");
            } else if (h.split) {
                art.wheel = load(cars_dir, h.dir, "wheel");
                art.caliper = load(cars_dir, h.dir, "caliper");
            }

            if (h.turret != null) {
                art.turret = load(cars_dir, h.dir, "turret");
                art.barrel = load(cars_dir, h.dir, "barrel");
            }

            a.models[h.kind] = art;
        }

        return a;
    }
};

fn load(dir: []const u8, name: []const u8, part: []const u8) ?rl.Model {
    var buf: [512]u8 = undefined;
    const path = std.fmt.bufPrintSentinel(&buf, "{s}/{s}/{s}.glb", .{ dir, name, part }, 0) catch return null;

    if (!assets.exists(path)) return null;

    const model = rl.LoadModel(path.ptr);

    if (model.meshCount == 0) return null;

    applyShared(dir, name, part, model);

    const merged = mesh.mergeFlat(model);

    mesh.dropCpu(merged);

    return merged;
}

const SharedTexture = struct {
    name: [24]u8 = undefined,
    len: usize = 0,
    texture: rl.Texture2D = undefined,
};

var shared_textures: [192]SharedTexture = @splat(.{});
var shared_count: usize = 0;

fn sharedTexture(dir: []const u8, file: []const u8) ?rl.Texture2D {
    for (shared_textures[0..shared_count]) |*s| {
        if (std.mem.eql(u8, s.name[0..s.len], file)) return s.texture;
    }

    if (shared_count == shared_textures.len or file.len > 24) return null;

    var buf: [512]u8 = undefined;
    const path = std.fmt.bufPrintSentinel(&buf, "{s}/tex/{s}", .{ dir, file }, 0) catch return null;
    var texture = rl.LoadTexture(path.ptr);

    if (texture.id == 0) return null;

    rl.GenTextureMipmaps(&texture);
    rl.SetTextureFilter(texture, rl.TEXTURE_FILTER_TRILINEAR);

    const slot = &shared_textures[shared_count];

    @memcpy(slot.name[0..file.len], file);
    slot.len = file.len;
    slot.texture = texture;
    shared_count += 1;

    return texture;
}

fn applyShared(dir: []const u8, name: []const u8, part: []const u8, model: rl.Model) void {
    var buf: [512]u8 = undefined;
    const path = std.fmt.bufPrintSentinel(&buf, "{s}/{s}/{s}.tex", .{ dir, name, part }, 0) catch return;

    if (!assets.exists(path)) return;

    const text = rl.LoadFileText(path.ptr);

    if (text == null) return;

    defer rl.UnloadFileText(text);

    var lines = std.mem.tokenizeAny(u8, std.mem.span(text), "\r\n");

    while (lines.next()) |line| {
        var parts = std.mem.tokenizeScalar(u8, line, ' ');
        const index = std.fmt.parseInt(usize, parts.next() orelse continue, 10) catch continue;
        const file = parts.next() orelse continue;

        if (index >= @as(usize, @intCast(model.materialCount))) continue;

        const texture = sharedTexture(dir, file) orelse continue;

        model.materials[index].maps[rl.MATERIAL_MAP_ALBEDO].texture = texture;
    }
}

fn rotate(v: Vec3, axis: Vec3, angle: f32) Vec3 {
    const c = @cos(angle);
    const s = @sin(angle);

    return v.scale(c).add(axis.cross(v).scale(s)).add(axis.scale(axis.dot(v) * (1 - c)));
}

pub fn rotateBasis(b: Basis, axis: Vec3, angle: f32) Basis {
    return .{ .x = rotate(b.x, axis, angle), .y = rotate(b.y, axis, angle), .z = rotate(b.z, axis, angle) };
}

pub fn bodyBasis(v: vehicle.Vehicle) Basis {
    var b = Basis.yawed(v.yaw);

    b = rotateBasis(b, b.x, -v.pitch);
    b = rotateBasis(b, b.z, v.roll + v.lean);

    return b;
}

var tyre_mesh: ?rl.Mesh = null;

fn tyre() rl.Mesh {
    if (tyre_mesh) |m| return m;

    const profile = [_][2]f32{ .{ -1, 0.7 }, .{ -1, 0.88 }, .{ -0.88, 0.975 }, .{ -0.55, 1.0 }, .{ 0.55, 1.0 }, .{ 0.88, 0.975 }, .{ 1, 0.88 }, .{ 1, 0.7 } };
    var normals: [profile.len][2]f32 = undefined;
    const segs = 48;
    var b: mesh.Builder = .{};

    for (profile, 0..) |_, k| {
        var nx: f32 = 0;
        var nr: f32 = 0;

        if (k > 0) {
            nx += profile[k][1] - profile[k - 1][1];
            nr += -(profile[k][0] - profile[k - 1][0]);
        }

        if (k + 1 < profile.len) {
            nx += profile[k + 1][1] - profile[k][1];
            nr += -(profile[k + 1][0] - profile[k][0]);
        }

        const l = @max(1e-5, @sqrt(nx * nx + nr * nr));

        normals[k] = .{ -nx / l, -nr / l };
    }

    b.style = .{ .color = .{ 30, 30, 33 } };

    for (0..segs) |i| {
        const a0 = @as(f32, @floatFromInt(i)) / segs * std.math.tau;
        const a1 = @as(f32, @floatFromInt(i + 1)) / segs * std.math.tau;

        for (0..profile.len - 1) |k| {
            const pt = struct {
                fn f(q: [2]f32, ang: f32) Vec3 {
                    return vec(q[0], @cos(ang) * q[1], @sin(ang) * q[1]);
                }

                fn n(q: [2]f32, ang: f32) Vec3 {
                    return vec(q[0], @cos(ang) * q[1], @sin(ang) * q[1]);
                }
            };
            const p00 = pt.f(profile[k], a0);
            const p01 = pt.f(profile[k + 1], a0);
            const p10 = pt.f(profile[k], a1);
            const p11 = pt.f(profile[k + 1], a1);
            const n00 = pt.n(normals[k], a0);
            const n01 = pt.n(normals[k + 1], a0);
            const n10 = pt.n(normals[k], a1);
            const n11 = pt.n(normals[k + 1], a1);
            const out = n00.add(n11);

            b.tri(p00, p01, p11, n00, n01, n11, out);
            b.tri(p00, p11, p10, n00, n11, n10, out);
        }
    }

    tyre_mesh = b.finish();

    return tyre_mesh.?;
}

fn tyreAt(r: *gfx.Renderer, spot: Vec3, basis: Basis, s: vehicle.Spec) void {
    const radius = s.wheel * 1.03;
    const half: f32 = switch (s.class) {
        .car => s.wheel * 0.46,
        .cycle => s.wheel * 0.09,
        else => s.wheel * 0.3,
    };
    const m: rl.Matrix = .{
        .m0 = basis.x.x * half,
        .m1 = basis.x.y * half,
        .m2 = basis.x.z * half,
        .m4 = basis.y.x * radius,
        .m5 = basis.y.y * radius,
        .m6 = basis.y.z * radius,
        .m8 = basis.z.x * radius,
        .m9 = basis.z.y * radius,
        .m10 = basis.z.z * radius,
        .m12 = spot.x,
        .m13 = spot.y,
        .m14 = spot.z,
        .m15 = 1,
    };

    r.setSurface(.{ .roughness = 0.92, .metallic = 0 });
    r.draw(tyre(), m, true);
}

fn at(pos: Vec3, basis: Basis, local: Vec3) Vec3 {
    return pos.add(basis.x.scale(local.x)).add(basis.y.scale(local.y)).add(basis.z.scale(local.z));
}

pub fn draw(r: *gfx.Renderer, art: *const Art, v: vehicle.Vehicle, alpha: f32) void {
    const ha = art.models[v.kind] orelse return;
    const h = heroes[v.kind];
    const basis = bodyBasis(v);
    const age = vehicle.wreck_time - v.wreck;

    if (!v.alive()) {
        if (age > 10 or v.wreck > vehicle.wreck_time) return;

        const sink = @max(0, age - 8) * 0.6;

        charred(r, ha.body, mesh.transform(v.pos.add(basis.y.scale(-h.ground - sink)), basis, h.scale));

        return;
    }

    const pos = v.prev.lerp(v.pos, alpha).add(basis.y.scale(-h.ground));
    const far2 = pos.sub(eye).dot(pos.sub(eye));

    r.drawModelLit(ha.body, mesh.transform(pos, basis, h.scale));

    if (far2 > 90 * 90 and h.turret == null) return;

    if (h.turret) |pivot| {
        const turret_basis = rotateBasis(basis, basis.y, v.turret);
        const turret_at = at(pos, basis, pivot.scale(h.scale));

        if (ha.turret) |t| r.drawModelLit(t, mesh.transform(turret_at, turret_basis, h.scale));

        const gun_basis = rotateBasis(turret_basis, turret_basis.x, -v.gun);
        const gun_at = at(turret_at, turret_basis, h.barrel.sub(pivot).scale(h.scale));

        if (ha.barrel) |b| r.drawModelLit(b, mesh.transform(gun_at, gun_basis, h.scale));
    }

    if (h.two) {
        const steered = rotateBasis(basis, basis.y, -v.steer);

        if (ha.wheel) |w| {
            r.drawModelLit(w, mesh.transform(at(pos, basis, h.front), rotateBasis(steered, steered.x, v.spin), h.scale));
        }

        if (ha.rear) |w| {
            r.drawModelLit(w, mesh.transform(at(pos, basis, h.rear), rotateBasis(basis, basis.x, v.spin), h.scale));
        }
    } else if (ha.wheel) |w| {
        for ([_]Vec3{ h.front, h.rear }, 0..) |base, axle| {
            for ([_]f32{ 1, -1 }) |side| {
                var fixed = basis;

                if (side < 0) fixed = rotateBasis(fixed, basis.y, std.math.pi);

                if (axle == 0) fixed = rotateBasis(fixed, basis.y, -v.steer);

                const spot = at(pos, basis, vec(base.x * side, base.y, base.z));

                r.drawModelLit(w, mesh.transform(spot, rotateBasis(fixed, basis.x, v.spin), h.scale));

                if (far2 < 25 * 25) {
                    if (ha.caliper) |c| r.drawModelLit(c, mesh.transform(spot, fixed, h.scale));
                }
            }
        }
    }

    r.setSurface(.{ .roughness = 0.5 });
}

pub var eye: Vec3 = .{};

fn charred(r: *gfx.Renderer, model: rl.Model, transform: rl.Matrix) void {
    var saved: [64]rl.Color = undefined;
    const n: usize = @min(64, @as(usize, @intCast(model.materialCount)));

    for (0..n) |i| {
        saved[i] = model.materials[i].maps[0].color;
        model.materials[i].maps[0].color = .{ .r = 38, .g = 34, .b = 32, .a = saved[i].a };
    }

    r.drawModelLit(model, transform);

    for (0..n) |i| model.materials[i].maps[0].color = saved[i];
}

pub fn seatPoint(v: vehicle.Vehicle, alpha: f32) Vec3 {
    const s = v.spec();
    const basis = bodyBasis(v);
    const car = s.class == .car;
    const local = vec(if (car) 0.36 else 0, s.seat, if (car) -s.length * 0.06 else -s.length * 0.1);

    return at(v.prev.lerp(v.pos, alpha), basis, local);
}

pub fn muzzle(v: vehicle.Vehicle) ?struct { pos: Vec3, dir: Vec3 } {
    const h = heroes[v.kind];
    const pivot = h.turret orelse return null;
    const basis = bodyBasis(v);
    const pos = v.pos.add(basis.y.scale(-h.ground));
    const turret_basis = rotateBasis(basis, basis.y, v.turret);
    const turret_at = at(pos, basis, pivot.scale(h.scale));
    const gun_basis = rotateBasis(turret_basis, turret_basis.x, -v.gun);
    const gun_at = at(turret_at, turret_basis, h.barrel.sub(pivot).scale(h.scale));

    return .{ .pos = gun_at.add(gun_basis.z.scale(h.tip * h.scale)), .dir = gun_basis.z };
}
