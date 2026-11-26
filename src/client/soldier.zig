const std = @import("std");
const rl = @import("raylib");
const shared = @import("shared");
const gfx = @import("gfx.zig");
const pvs = @import("pvs.zig");
const mesh = @import("mesh.zig");
const game_mod = @import("game.zig");
const render = @import("render.zig");
const models_mod = @import("models.zig");
const gunart = @import("gunart.zig");

const Vec3 = shared.math.Vec3;
const Basis = mesh.Basis;
const movement = shared.movement;

pub const Clip = enum(u8) { idle, run, aim, shoot, reload, death, drive };

const clip_names = [_][]const u8{ "Pistol_Idle_Loop", "Jog_Fwd_Loop", "Pistol_Aim_Neutral", "Pistol_Shoot", "Pistol_Reload", "Death01", "Driving_Loop" };
const fps: f32 = 60;
const blend_time: f32 = 0.18;
pub const scale: f32 = 0.95;

const Track = struct {
    clip: Clip = .idle,
    time: f32 = 0,
    prev: Clip = .idle,
    prev_time: f32 = 0,
    blend: f32 = 1,
};

pub const Bones = struct {
    head: usize = 0,
    chest: usize = 0,
    hand: usize = 0,
};

pub const Rig = struct {
    model: rl.Model,
    anims: [*c]rl.ModelAnimation,
    clips: [clip_names.len]usize,
    bones: Bones,
    tracks: [16]Track = @splat(.{}),
    gear: bool = false,
    rider: Track = .{ .clip = .drive, .prev = .drive },
    spine1: usize = 0,
    spine2: usize = 0,
    tier: []u8 = &.{},
    pose: []rl.Transform = &.{},
    aim_pose: []rl.Transform = &.{},
    pose_ptr: [1][*c]rl.Transform = .{null},
    aim_w: f32 = 0,
    aim_yaw: f32 = 0,
    aim_pitch: f32 = 0,
    ok: bool,

    pub fn load(path: [:0]const u8) Rig {
        var rig: Rig = .{ .model = rl.LoadModel(path.ptr), .anims = null, .clips = @splat(0), .bones = .{}, .ok = false };
        var count: c_int = 0;

        if (rig.model.meshCount == 0) return rig;

        rig.anims = rl.LoadModelAnimations(path.ptr, &count);

        if (rig.anims == null or count == 0) return rig;

        for (clip_names, 0..) |name, i| {
            var k: usize = 0;

            while (k < @as(usize, @intCast(count))) : (k += 1) {
                const clip = rig.anims[k];

                if (std.mem.eql(u8, std.mem.sliceTo(&clip.name, 0), name)) rig.clips[i] = k;
            }
        }

        const bones = rig.model.skeleton.bones[0..rig.model.skeleton.boneCount];
        var neck: ?usize = null;

        for (bones, 0..) |b, i| {
            const bone = b;
            const name = std.mem.sliceTo(&bone.name, 0);

            if (std.mem.eql(u8, name, "DEF-neck")) neck = i;
            if (std.mem.eql(u8, name, "DEF-head")) rig.bones.head = i;
            if (std.mem.eql(u8, name, "DEF-spine.003")) rig.bones.chest = i;
            if (std.mem.eql(u8, name, "DEF-spine.001")) rig.spine1 = i;
            if (std.mem.eql(u8, name, "DEF-spine.002")) rig.spine2 = i;
            if (std.mem.eql(u8, name, "DEF-hand.R")) rig.bones.hand = i;
        }

        rig.tier = std.heap.page_allocator.alloc(u8, bones.len) catch &.{};
        rig.pose = std.heap.page_allocator.alloc(rl.Transform, bones.len) catch &.{};
        rig.aim_pose = std.heap.page_allocator.alloc(rl.Transform, bones.len) catch &.{};

        for (rig.tier, 0..) |*t, i| {
            var b: c_int = @intCast(i);

            t.* = 0;

            while (b >= 0) : (b = bones[@intCast(b)].parent) {
                const at: usize = @intCast(b);

                if (at == rig.bones.chest) {
                    t.* = if (at == i) 3 else 4;
                    break;
                }

                if (at == rig.spine2) {
                    t.* = 2;
                    break;
                }

                if (at == rig.spine1) {
                    t.* = 1;
                    break;
                }
            }
        }

        inflate(&rig.model, 0.032);

        if (neck) |n| {
            const bind = rig.model.skeleton.bindPose;
            const low = bind[n].translation.y - 0.02;
            const high = bind[rig.bones.head].translation.y + 0.035;

            cutNeck(&rig.model, n, low, high);
        }

        rig.gear = rig.model.materialCount > 4;

        if (!rig.gear) {
            for (rig.model.materials[0..@intCast(rig.model.materialCount)], 0..) |*m, i| {
                m.maps[0].color = switch (i) {
                    1 => .{ .r = 128, .g = 122, .b = 86, .a = 255 },
                    else => .{ .r = 70, .g = 70, .b = 66, .a = 255 },
                };
            }
        }

        rig.ok = true;

        return rig;
    }

    fn frame(rig: Rig, clip: Clip, time: f32) f32 {
        const a = rig.anims[rig.clips[@intFromEnum(clip)]];
        const count: f32 = @floatFromInt(@max(a.keyframeCount, 1));
        const f = time * fps;

        if (clip == .death or clip == .shoot) return @min(f, count - 1);

        return @mod(f, count);
    }

    fn anim(rig: Rig, clip: Clip) rl.ModelAnimation {
        return rig.anims[rig.clips[@intFromEnum(clip)]];
    }

    fn posed(rig: Rig, track: Track, bone: usize) Vec3 {
        const from = rig.bonePos(track.prev, track.prev_time, bone);
        const to = rig.bonePos(track.clip, track.time, bone);

        return from.lerp(to, track.blend);
    }

    fn bonePos(rig: Rig, clip: Clip, time: f32, bone: usize) Vec3 {
        const a = rig.anim(clip);
        const last: usize = @intCast(@max(a.keyframeCount - 1, 0));
        const f = rig.frame(clip, time);
        const k0: usize = @min(@as(usize, @intFromFloat(@floor(f))), last);
        const k1: usize = if (clip == .death or clip == .shoot) @min(k0 + 1, last) else (k0 + 1) % (last + 1);
        const k = f - @floor(f);
        const p0 = a.keyframePoses[k0][bone].translation;
        const p1 = a.keyframePoses[k1][bone].translation;

        return .{ .x = p0.x + (p1.x - p0.x) * k, .y = p0.y + (p1.y - p0.y) * k, .z = p0.z + (p1.z - p0.z) * k };
    }
};

fn inflate(model: *rl.Model, amount: f32) void {
    for (model.meshes[0..@intCast(model.meshCount)]) |*m| {
        if (m.vertices == null or m.normals == null) continue;

        const n: usize = @intCast(m.vertexCount);
        var i: usize = 0;

        while (i < n) : (i += 1) {
            const y = m.vertices[i * 3 + 1];
            const k: f32 = if (y > 1.55) 0.3 else 1;

            m.vertices[i * 3] += m.normals[i * 3] * amount * k;
            m.vertices[i * 3 + 1] += m.normals[i * 3 + 1] * amount * k;
            m.vertices[i * 3 + 2] += m.normals[i * 3 + 2] * amount * k;
        }

        rl.UpdateMeshBuffer(m.*, 0, m.vertices, @intCast(n * 3 * @sizeOf(f32)), 0);
    }
}

fn cutNeck(model: *rl.Model, neck: usize, low: f32, high: f32) void {
    for (model.meshes[0..@intCast(model.meshCount)]) |*m| {
        if (m.indices == null or m.boneIndices == null or m.boneWeights == null) continue;

        const tris: usize = @intCast(m.triangleCount);
        const idx = m.indices[0 .. tris * 3];
        var t: usize = 0;

        while (t < tris) : (t += 1) {
            var hit = false;

            var in_band: u8 = 0;

            for (idx[t * 3 .. t * 3 + 3]) |v| {
                const y = m.vertices[@as(usize, v) * 3 + 1];
                const x = m.vertices[@as(usize, v) * 3];

                if (y > low and y < high and @abs(x) < 0.14) in_band += 1;
            }

            if (in_band == 3) hit = true;

            for (idx[t * 3 .. t * 3 + 3]) |v| {
                const base = @as(usize, v) * 4;
                var best: usize = 0;

                for (1..4) |k| {
                    if (m.boneWeights[base + k] > m.boneWeights[base + best]) best = k;
                }

                if (m.boneIndices[base + best] == neck) hit = true;
            }

            if (hit) {
                idx[t * 3 + 1] = idx[t * 3];
                idx[t * 3 + 2] = idx[t * 3];
            }
        }

        rl.UpdateMeshBuffer(m.*, 6, m.indices, @intCast(tris * 3 * @sizeOf(c_ushort)), 0);
    }
}

pub const Kit = struct {
    helmet: rl.Mesh,
    rig: rl.Mesh,
    pack: rl.Mesh,

    pub fn build() Kit {
        var h: mesh.Builder = .{};

        h.style = .{ .color = .{ 150, 144, 100 } };
        h.sphere(.{ .y = 0.1, .z = -0.01 }, 0.16, 7, 10);
        h.cylinder(.{ .y = 0.045, .z = -0.01 }, .{ .y = 0.065, .z = -0.01 }, 0.175, 10, true);
        h.style = .{ .color = .{ 44, 46, 50 } };
        h.slab(0, &.{ .{ 0.06, -0.07 }, .{ 0.15, -0.05 }, .{ 0.16, 0.03 }, .{ 0.1, 0.05 }, .{ 0.05, 0.0 } }, 0.105, 0.015);
        h.style = .{ .color = .{ 30, 32, 36 } };
        h.box(.{ .y = 0.035, .z = 0.15 }, Basis.world, .{ .x = 0.1, .y = 0.028, .z = 0.025 });
        h.style = .{ .color = .{ 70, 80, 90 } };
        h.box(.{ .x = 0.045, .y = 0.035, .z = 0.172 }, Basis.world, .{ .x = 0.035, .y = 0.02, .z = 0.006 });
        h.box(.{ .x = -0.045, .y = 0.035, .z = 0.172 }, Basis.world, .{ .x = 0.035, .y = 0.02, .z = 0.006 });

        const helmet = h.finish();
        var c: mesh.Builder = .{};

        c.style = .{ .color = .{ 58, 60, 62 } };
        c.slab(0, &.{ .{ -0.17, -0.26 }, .{ 0.17, -0.28 }, .{ 0.2, 0.1 }, .{ 0.13, 0.2 }, .{ -0.13, 0.2 }, .{ -0.2, 0.1 } }, 0.22, 0.04);
        c.style = .{ .color = .{ 48, 50, 52 } };
        c.box(.{ .x = -0.09, .y = -0.15, .z = 0.2 }, Basis.world, .{ .x = 0.055, .y = 0.075, .z = 0.04 });
        c.box(.{ .x = 0.0, .y = -0.15, .z = 0.2 }, Basis.world, .{ .x = 0.055, .y = 0.075, .z = 0.04 });
        c.box(.{ .x = 0.09, .y = -0.15, .z = 0.2 }, Basis.world, .{ .x = 0.055, .y = 0.075, .z = 0.04 });

        const vest = c.finish();
        var p: mesh.Builder = .{};

        p.style = .{ .color = .{ 62, 64, 58 } };
        p.slab(0, &.{ .{ -0.27, -0.2 }, .{ -0.17, -0.22 }, .{ -0.15, 0.12 }, .{ -0.27, 0.14 } }, 0.14, 0.03);

        return .{ .helmet = helmet, .rig = vest, .pack = p.finish() };
    }
};

fn turn(b: Basis, axis: Vec3, angle: f32) Basis {
    const c = @cos(angle);
    const s = @sin(angle);
    const spin = struct {
        fn by(v: Vec3, k: Vec3, cs: f32, sn: f32) Vec3 {
            return v.scale(cs).add(k.cross(v).scale(sn)).add(k.scale(k.dot(v) * (1 - cs)));
        }
    }.by;

    return .{ .x = spin(b.x, axis, c, s), .y = spin(b.y, axis, c, s), .z = spin(b.z, axis, c, s) };
}

fn swordBasis(b: game_mod.Bot, base: Basis) Basis {
    var pitch: f32 = 0.9;
    var roll: f32 = 0;

    if (b.stagger > 0) {
        pitch = 1.8;
        roll = 0.4;
    } else if (b.swing >= 0) {
        const wind: f32 = 0.33;
        const hit: f32 = 0.5;

        pitch = if (b.swing < wind)
            0.9 + (b.swing / wind) * 1.4
        else if (b.swing < hit)
            2.3 - ((b.swing - wind) / (hit - wind)) * 3.0
        else
            -0.7 + @min(1, (b.swing - hit) / 0.35) * 1.6;
    } else if (b.guard >= 0) {
        pitch = 0.25;
        roll = 1.45;
    }

    return turn(turn(base, base.x, pitch), base.z, roll);
}

fn pick(b: game_mod.Bot) Clip {
    if (b.dead >= 0) return .death;
    if (b.reload > 0) return .reload;
    if (b.shot > 0) return .shoot;
    if (b.body.vel.flatLength() > 1.2) return .run;
    if (b.seen > 0) return .aim;

    return .idle;
}

pub fn draw(r: *gfx.Renderer, rig: *Rig, kit: Kit, models: *const models_mod.Models, arts: *const [shared.weapons.count]gunart.Art, g: game_mod.Game, alpha: f32, dt: f32) void {
    if (!rig.ok) return;

    const eye = g.view().eye;

    for (g.bots.items, 0..) |b, i| {
        if (!b.active or b.riding) continue;

        if (r.phase == .main and b.body.pos.sub(eye).length() > 4) {
            const mid = b.body.pos.add(.{ .y = 1 });

            if (!gfx.sphereVisible(mid, 1.5) or !pvs.visible(eye, mid, 1)) continue;
        }

        const track = &rig.tracks[i % rig.tracks.len];

        if (r.phase == .main) {
            const want = pick(b);

            if (want != track.clip) {
                track.prev = track.clip;
                track.prev_time = track.time;
                track.clip = want;
                track.time = 0;
                track.blend = 0;
            }

            track.time += dt;
            track.prev_time += dt;
            track.blend = @min(1, track.blend + dt / blend_time);
        }

        const pos = b.prev.lerp(b.body.pos, alpha).add(.{ .y = if (b.dead > 4) -(b.dead - 4) * 0.6 else 0 });
        const basis = Basis.yawed(b.yaw);
        const world = mesh.transform(pos, basis, scale);

        rl.UpdateModelAnimationEx(rig.model, rig.anim(track.prev), rig.frame(track.prev, track.prev_time), rig.anim(track.clip), rig.frame(track.clip, track.time), track.blend);
        r.drawModel(rig.model, world);

        const place = struct {
            fn at(p: Vec3, bs: Basis, local: Vec3) Vec3 {
                return p.add(bs.x.scale(local.x * scale)).add(bs.y.scale(local.y * scale)).add(bs.z.scale(local.z * scale));
            }
        }.at;
        const head = place(pos, basis, rig.posed(track.*, rig.bones.head));
        const chest = place(pos, basis, rig.posed(track.*, rig.bones.chest));
        const hand = place(pos, basis, rig.posed(track.*, rig.bones.hand));

        if (!rig.gear) {
            r.draw(kit.helmet, mesh.transform(head.add(.{ .y = 0.06 }), basis, 1), true);
            r.draw(kit.rig, mesh.transform(chest.add(.{ .y = -0.05 }), basis, 1), true);
            r.draw(kit.pack, mesh.transform(chest.add(basis.z.scale(-0.04)).add(.{ .y = -0.02 }), basis, 1), true);
        }

        if (b.dead < 0) {
            const aim = shared.math.lookDir(b.yaw, b.pitch);
            const gun_basis = Basis.facing(aim);

            if (shared.weapons.isMelee(shared.weapons.specs[b.weapon])) {
                render.drawGunBare(r, models, arts, b.weapon, hand, swordBasis(b, Basis.facing(shared.math.flatDir(b.yaw))), 1);

                continue;
            }

            render.drawGunBare(r, models, arts, b.weapon, hand.add(aim.scale(0.12)), gun_basis, 1);
        }
    }
}

const Quat = rl.Quaternion;

fn qmul(a: Quat, b: Quat) Quat {
    return .{
        .x = a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
        .y = a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
        .z = a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w,
        .w = a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
    };
}

fn qaxis(x: f32, y: f32, z: f32, angle: f32) Quat {
    const s = @sin(angle * 0.5);

    return .{ .x = x * s, .y = y * s, .z = z * s, .w = @cos(angle * 0.5) };
}

fn qconj(q: Quat) Quat {
    return .{ .x = -q.x, .y = -q.y, .z = -q.z, .w = q.w };
}

fn qrot(q: Quat, v: rl.Vector3) rl.Vector3 {
    const p = qmul(qmul(q, .{ .x = v.x, .y = v.y, .z = v.z, .w = 0 }), qconj(q));

    return .{ .x = p.x, .y = p.y, .z = p.z };
}

fn qnlerp(a: Quat, b: Quat, t: f32) Quat {
    const d = a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
    const s: f32 = if (d < 0) -1 else 1;
    const q: Quat = .{ .x = a.x + (b.x * s - a.x) * t, .y = a.y + (b.y * s - a.y) * t, .z = a.z + (b.z * s - a.z) * t, .w = a.w + (b.w * s - a.w) * t };
    const n = @sqrt(q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w);

    return .{ .x = q.x / n, .y = q.y / n, .z = q.z / n, .w = q.w / n };
}

fn vlerp(a: rl.Vector3, b: rl.Vector3, t: f32) rl.Vector3 {
    return .{ .x = a.x + (b.x - a.x) * t, .y = a.y + (b.y - a.y) * t, .z = a.z + (b.z - a.z) * t };
}

fn vsub(a: rl.Vector3, b: rl.Vector3) rl.Vector3 {
    return .{ .x = a.x - b.x, .y = a.y - b.y, .z = a.z - b.z };
}

fn vadd(a: rl.Vector3, b: rl.Vector3) rl.Vector3 {
    return .{ .x = a.x + b.x, .y = a.y + b.y, .z = a.z + b.z };
}

fn sample(rig: *const Rig, clip: Clip, time: f32, out: []rl.Transform) void {
    const a = rig.anim(clip);
    const last: usize = @intCast(@max(a.keyframeCount - 1, 0));
    const f = rig.frame(clip, time);
    const k0: usize = @min(@as(usize, @intFromFloat(@floor(f))), last);
    const k1: usize = (k0 + 1) % (last + 1);
    const k = f - @floor(f);

    for (out, 0..) |*o, i| {
        const p0 = a.keyframePoses[k0][i];
        const p1 = a.keyframePoses[k1][i];

        o.translation = vlerp(p0.translation, p1.translation, k);
        o.rotation = qnlerp(p0.rotation, p1.rotation, k);
        o.scale = vlerp(p0.scale, p1.scale, k);
    }
}

fn twistStage(rig: *Rig, tier: u8, pivot_bone: usize, q: Quat) void {
    const pivot = rig.pose[pivot_bone].translation;

    for (rig.pose, rig.tier) |*p, t| {
        if (t < tier) continue;

        p.translation = vadd(pivot, qrot(q, vsub(p.translation, pivot)));
        p.rotation = qmul(q, p.rotation);
    }
}

const twist_yaw_limit: f32 = 2.09;
const twist_pitch_limit: f32 = 0.78;

pub fn drawRider(r: *gfx.Renderer, rig: *Rig, kit: Kit, models: *const models_mod.Models, arts: *const [shared.weapons.count]gunart.Art, seat: Vec3, basis: Basis, drop: f32, weapon: u8, aim: ?Vec3, kick: f32, dt: f32) void {
    if (!rig.ok) return;

    const track = &rig.rider;

    if (r.phase == .main) {
        track.time += dt;
        track.prev_time += dt;
    }

    const pos = seat.sub(basis.y.scale(drop));
    const world = mesh.transform(pos, basis, scale);
    const place = struct {
        fn at(p: Vec3, bs: Basis, local: Vec3) Vec3 {
            return p.add(bs.x.scale(local.x * scale)).add(bs.y.scale(local.y * scale)).add(bs.z.scale(local.z * scale));
        }
    }.at;
    const toWorld = struct {
        fn at(bs: Basis, v: rl.Vector3) Vec3 {
            return bs.x.scale(v.x).add(bs.y.scale(v.y)).add(bs.z.scale(v.z));
        }
    }.at;

    if (rig.pose.len == 0 or rig.pose.len != rig.tier.len) {
        rl.UpdateModelAnimationEx(rig.model, rig.anim(.drive), rig.frame(.drive, track.time), rig.anim(.drive), rig.frame(.drive, track.time), 1);
        r.drawModel(rig.model, world);

        return;
    }

    if (r.phase == .main) {
        const want: f32 = if (aim != null) 1 else 0;

        rig.aim_w += (want - rig.aim_w) * @min(1, dt * (if (aim != null) @as(f32, 10) else 5));

        if (aim) |d| {
            const lx = d.dot(basis.x);
            const ly = d.dot(basis.y);
            const lz = d.dot(basis.z);
            const yaw = std.math.clamp(std.math.atan2(lx, lz), -twist_yaw_limit, twist_yaw_limit);
            const pitch = std.math.clamp(std.math.asin(std.math.clamp(ly, -1, 1)), -twist_pitch_limit, twist_pitch_limit);
            const k = @min(1, dt * 16);

            rig.aim_yaw += (yaw - rig.aim_yaw) * k;
            rig.aim_pitch += (pitch - rig.aim_pitch) * k;
        }
    }

    sample(rig, .drive, track.time, rig.pose);

    const w = rig.aim_w;
    const chest_bone = rig.bones.chest;

    if (w > 0.001) {
        sample(rig, .aim, 0, rig.aim_pose);

        const cd = rig.pose[chest_bone];
        const ca = rig.aim_pose[chest_bone];
        const rel = qmul(cd.rotation, qconj(ca.rotation));

        for (rig.pose, rig.aim_pose, rig.tier) |*p, a, t| {
            if (t != 4) continue;

            const tr = vadd(cd.translation, qrot(rel, vsub(a.translation, ca.translation)));
            const rot = qmul(rel, a.rotation);

            p.translation = vlerp(p.translation, tr, w);
            p.rotation = qnlerp(p.rotation, rot, w);
        }

        const yaw = rig.aim_yaw * w;
        const pitch = rig.aim_pitch * w - std.math.clamp(kick, 0, 1) * 0.12;
        const stages = [_]struct { tier: u8, bone: usize, share: f32 }{
            .{ .tier = 1, .bone = rig.spine1, .share = 0.3 },
            .{ .tier = 2, .bone = rig.spine2, .share = 0.3 },
            .{ .tier = 3, .bone = chest_bone, .share = 0.4 },
        };

        for (stages) |s| twistStage(rig, s.tier, s.bone, qmul(qaxis(0, 1, 0, yaw * s.share), qaxis(1, 0, 0, -pitch * s.share)));
    }

    var tmp = rig.anim(.drive);

    rig.pose_ptr[0] = rig.pose.ptr;
    tmp.keyframeCount = 1;
    tmp.keyframePoses = @ptrCast(&rig.pose_ptr);
    rl.UpdateModelAnimationEx(rig.model, tmp, 0, tmp, 0, 0);
    r.drawModel(rig.model, world);

    const head = place(pos, basis, Vec3{ .x = rig.pose[rig.bones.head].translation.x, .y = rig.pose[rig.bones.head].translation.y, .z = rig.pose[rig.bones.head].translation.z });
    const chest = place(pos, basis, Vec3{ .x = rig.pose[chest_bone].translation.x, .y = rig.pose[chest_bone].translation.y, .z = rig.pose[chest_bone].translation.z });
    const hand = place(pos, basis, Vec3{ .x = rig.pose[rig.bones.hand].translation.x, .y = rig.pose[rig.bones.hand].translation.y, .z = rig.pose[rig.bones.hand].translation.z });
    const body_q = qaxis(0, 1, 0, rig.aim_yaw * w);
    const gear: Basis = .{
        .x = toWorld(basis, qrot(body_q, .{ .x = 1, .y = 0, .z = 0 })),
        .y = toWorld(basis, qrot(body_q, .{ .x = 0, .y = 1, .z = 0 })),
        .z = toWorld(basis, qrot(body_q, .{ .x = 0, .y = 0, .z = 1 })),
    };

    if (!rig.gear) {
        r.draw(kit.helmet, mesh.transform(head.add(gear.y.scale(0.06)), gear, 1), true);
        r.draw(kit.rig, mesh.transform(chest.sub(gear.y.scale(0.05)), gear, 1), true);
        r.draw(kit.pack, mesh.transform(chest.add(gear.z.scale(-0.04)).sub(gear.y.scale(0.02)), gear, 1), true);
    }

    if (w < 0.35) return;

    const point = toWorld(basis, qrot(qmul(qaxis(0, 1, 0, rig.aim_yaw), qaxis(1, 0, 0, -rig.aim_pitch)), .{ .x = 0, .y = 0, .z = 1 })).normalize();

    render.drawGunBare(r, models, arts, weapon, hand.add(point.scale(0.12)), Basis.facing(point), 1);
}
