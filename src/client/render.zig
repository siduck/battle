const std = @import("std");
const pvs = @import("pvs.zig");
const rl = @import("raylib");
const shared = @import("shared");
const gfx = @import("gfx.zig");
const mesh = @import("mesh.zig");
const ui = @import("ui.zig");
const game_mod = @import("game.zig");
const models_mod = @import("models.zig");
const gunart = @import("gunart.zig");
const propart = @import("propart.zig");
const cover = @import("cover.zig");
const soldier = @import("soldier.zig");
const fx_mod = @import("fx.zig");
const assets = @import("assets.zig");

var fx_state: ?fx_mod.Fx = null;
const vehicleart = @import("vehicleart.zig");
const driving = @import("driving.zig");
const air = @import("air.zig");

const math = shared.math;
const map = shared.map;
const movement = shared.movement;
const weapons = shared.weapons;
const Vec3 = math.Vec3;
const Basis = mesh.Basis;
const Game = game_mod.Game;
const View = game_mod.View;
const Models = models_mod.Models;

pub var base_fov: f32 = 74;

pub fn camera(g: Game, v: View) rl.Camera3D {
    return .{
        .position = v3(v.eye),
        .target = v3(v.eye.add(v.forward)),
        .up = v3(v.up),
        .fovy = (base_fov + driving.fov_extra) / g.zoom(),
        .projection = rl.CAMERA_PERSPECTIVE,
    };
}

fn v3(a: Vec3) rl.Vector3 {
    return .{ .x = a.x, .y = a.y, .z = a.z };
}

fn rotate(v: Vec3, axis: Vec3, angle: f32) Vec3 {
    const c = @cos(angle);
    const s = @sin(angle);

    return v.scale(c).add(axis.cross(v).scale(s)).add(axis.scale(axis.dot(v) * (1 - c)));
}

fn rotateBasis(b: Basis, axis: Vec3, angle: f32) Basis {
    return .{ .x = rotate(b.x, axis, angle), .y = rotate(b.y, axis, angle), .z = rotate(b.z, axis, angle) };
}

const Pose = struct {
    origin: Vec3,
    basis: Basis,
};

fn sightHeight(spec: weapons.Spec) f32 {
    return switch (spec.look.optic) {
        .iron => 0.012,
        .dot, .holo => 0.05,
        .scope2 => 0.06,
        .scope4, .scope8 => 0.07,
    };
}

fn adsDrop(spec: weapons.Spec, top: ?f32) f32 {
    if (spec.class == .bow) return -0.02;

    const sight = sightHeight(spec);

    if (top) |t| return -(t + sight) + ads_lift;

    return -(0.035 + sight);
}

const SwordPose = struct {
    yaw: f32,
    pitch: f32,
    roll: f32,
    x: f32,
    y: f32,
};

const sword_idle: SwordPose = .{ .yaw = 0.12, .pitch = 0.95, .roll = -0.2, .x = 0.2, .y = -0.155 };
const sword_block: SwordPose = .{ .yaw = 0.05, .pitch = 0.3, .roll = -1.45, .x = 0.06, .y = -0.17 };
const sword_staggered: SwordPose = .{ .yaw = 0.6, .pitch = 1.6, .roll = 0.3, .x = 0.3, .y = -0.1 };

const sword_arcs = [4][2]SwordPose{
    .{ .{ .yaw = 1.1, .pitch = 0.15, .roll = -1.45, .x = 0.28, .y = -0.14 }, .{ .yaw = -1.15, .pitch = 0.05, .roll = -1.5, .x = -0.16, .y = -0.2 } },
    .{ .{ .yaw = -0.85, .pitch = 0.7, .roll = 0.9, .x = -0.08, .y = -0.05 }, .{ .yaw = 0.95, .pitch = -0.35, .roll = 1.2, .x = 0.26, .y = -0.33 } },
    .{ .{ .yaw = 0.05, .pitch = 2.1, .roll = -0.1, .x = 0.12, .y = 0.02 }, .{ .yaw = -0.05, .pitch = -0.7, .roll = -0.1, .x = 0.05, .y = -0.38 } },
    .{ .{ .yaw = 0.7, .pitch = 1.9, .roll = -0.6, .x = 0.3, .y = 0.0 }, .{ .yaw = -1.1, .pitch = -0.6, .roll = -0.9, .x = -0.2, .y = -0.36 } },
};

fn easeInOut(t: f32) f32 {
    const k = math.clamp01(t);

    return k * k * (3 - 2 * k);
}

fn mixPose(a: SwordPose, b: SwordPose, t: f32) SwordPose {
    return .{
        .yaw = a.yaw + (b.yaw - a.yaw) * t,
        .pitch = a.pitch + (b.pitch - a.pitch) * t,
        .roll = a.roll + (b.roll - a.roll) * t,
        .x = a.x + (b.x - a.x) * t,
        .y = a.y + (b.y - a.y) * t,
    };
}

fn swordPose(g: Game, v: View) Pose {
    const m = g.melee_state;
    const moving = math.clamp01(g.player.vel.flatLength() / 7);
    var p = sword_idle;
    var reach: f32 = 0.42;

    if (m.kind != .none) {
        const arc = sword_arcs[@min(m.arc, 3)];
        const t = m.progress();

        if (t < 0.3) {
            p = mixPose(sword_idle, arc[0], easeInOut(t / 0.3));
        } else if (t < 0.47) {
            const k = easeInOut((t - 0.3) / 0.17);

            p = mixPose(arc[0], arc[1], k);
            reach += @sin(k * std.math.pi) * 0.12;
        } else {
            p = mixPose(arc[1], sword_idle, easeInOut((t - 0.47) / 0.53));
        }
    } else if (m.stagger > 0) {
        p = mixPose(sword_idle, sword_staggered, math.clamp01(m.stagger / 0.3));
    } else if (m.block >= 0) {
        p = mixPose(sword_idle, sword_block, easeInOut(m.block / 0.09));
    } else if (m.holding) {
        const c = m.charging();

        p = mixPose(sword_idle, sword_arcs[3][0], easeInOut(math.clamp01(m.hold / 0.25)) * (0.55 + 0.45 * c));

        if (c >= 1) p.x += @sin(g.time * 70) * 0.004;
    }

    p.x += @sin(g.bob) * 0.01 * moving;
    p.y += @abs(@cos(g.bob)) * 0.01 * moving;

    if (g.arsenal.switching > 0) p.y -= g.arsenal.switching * 0.8;

    var basis: Basis = .{ .x = v.right, .y = v.up, .z = v.forward.neg() };

    basis = rotateBasis(basis, v.up, p.yaw);
    basis = rotateBasis(basis, basis.x, p.pitch);
    basis = rotateBasis(basis, basis.z, p.roll);

    return .{
        .origin = v.eye.add(v.right.scale(p.x)).add(v.up.scale(p.y)).add(v.forward.scale(reach)),
        .basis = basis,
    };
}

fn gunPose(g: Game, v: View, top: ?f32) ?Pose {
    if (g.scoped() or g.dead > 0) return null;

    if (g.arsenal.spec().class == .melee) return swordPose(g, v);

    const a = g.arsenal;
    const spec = a.spec();
    const ads = g.ads;
    const moving = math.clamp01(g.player.vel.flatLength() / 7) * (1 - ads);
    const bob_x = @sin(g.bob) * 0.008 * moving;
    const bob_y = @abs(@cos(g.bob)) * 0.008 * moving;
    var down = -0.165 + (0.165 + adsDrop(spec, top)) * ads + bob_y;
    var tilt = a.kick * 0.05;
    var reach: f32 = 0.27 - a.kick * 0.03;

    if (scope_eyepiece) |ez| reach += (scope_relief + ez - reach) * ads;

    if (spec.class != .pistol) reach += vm_reach * (1 - ads);
    if (spec.class != .pistol) down -= vm_down * (1 - ads);

    if (spec.class == .pistol) {
        reach += pistol_reach * (1 - ads);
        down += pistol_down * (1 - ads);
    }

    if (a.reloading > 0) {
        const phase = math.clamp01(1 - a.reloading / @max(0.01, spec.reload));
        const s = @sin(phase * std.math.pi);

        down -= 0.07 * s;
        tilt -= 0.6 * s;
    }

    if (a.switching > 0) down -= a.switching * 0.8;

    var basis: Basis = .{ .x = v.right, .y = v.up, .z = v.forward.neg() };
    var bow_draw: f32 = ads;

    basis = rotateBasis(basis, v.right, tilt);

    if (spec.class != .bow and spec.class != .melee) {
        basis = rotateBasis(basis, v.up, yaw_side * (1 - ads));
        basis = rotateBasis(basis, v.forward, roll_side * (1 - ads));
    }

    if (spec.class == .bow) {
        bow_draw = if (a.charge > 0) math.clamp01(a.charge / @max(0.01, spec.charge)) else ads;
        basis = rotateBasis(basis, v.up, 0.2 * bow_draw);
        basis = rotateBasis(basis, v.forward, 0.35 - 0.12 * bow_draw);
        reach += 0.28;
        down -= 0.035 * (1 - bow_draw);
    }

    if (spec.class == .crossbow) {
        reach += 0.16 * (1 - ads);
        down -= 0.025 * (1 - ads);
        basis = rotateBasis(basis, v.up, 0.04 * (1 - ads));
    }

    if (a.swing > 0) {
        const t = a.swing / 0.28;
        const s = @sin(t * std.math.pi);

        basis = rotateBasis(basis, v.up, s * 0.9);
        basis = rotateBasis(basis, v.right, -s * 0.4);
        reach += s * 0.1;
    }

    const side_rest: f32 = switch (spec.class) {
        .crossbow => 0.24,
        .bow => -0.07,
        else => 0.19,
    };
    const side = if (spec.class == .bow) -0.07 - 0.03 * bow_draw + bob_x else side_rest * (1 - ads) + bob_x;

    return .{
        .origin = v.eye.add(v.right.scale(side)).add(v.up.scale(down)).add(v.forward.scale(reach)),
        .basis = basis,
    };
}

pub fn drawGunBare(r: *gfx.Renderer, models: *const Models, arts: *const [weapons.count]gunart.Art, weapon: u8, origin: Vec3, basis: Basis, s: f32) void {
    const art = arts[weapon];

    if (art.body) |body| r.drawModel(body, mesh.transform(origin, basis, s)) else r.draw(models.guns[weapon], mesh.transform(origin, basis, s), true);

    drawOptic(r, art, origin, basis, s);
}

pub var skin: weapons.Rarity = .common;
pub var yaw_side: f32 = 0.2;
pub var show_hands = true;
pub var blocky_hands = true;
pub var arm_scale: f32 = 0.85;
pub var r_off: Vec3 = .{};
pub var l_off: Vec3 = .{};
pub var vm_reach: f32 = 0;
pub var scope_eyepiece: ?f32 = null;
var optic_see_through = false;
pub var scope_relief: f32 = 0.1;
pub var vm_down: f32 = 0;
pub var l_roll: f32 = 0;
pub var melee_tilt: f32 = -1.57;
pub var l_roll_far: f32 = 0;
pub var pistol_reach: f32 = 0.06;
pub var pistol_down: f32 = 0.03;
pub var roll_side: f32 = -0.05;
pub var ads_lift: f32 = 0;

const skin_colors = [_][3]rl.Color{
    .{ .{ .r = 232, .g = 234, .b = 236, .a = 255 }, .{ .r = 52, .g = 58, .b = 66, .a = 255 }, .{ .r = 255, .g = 40, .b = 170, .a = 255 } },
    .{ .{ .r = 236, .g = 232, .b = 224, .a = 255 }, .{ .r = 48, .g = 52, .b = 58, .a = 255 }, .{ .r = 255, .g = 120, .b = 20, .a = 255 } },
    .{ .{ .r = 225, .g = 232, .b = 238, .a = 255 }, .{ .r = 30, .g = 62, .b = 120, .a = 255 }, .{ .r = 40, .g = 220, .b = 255, .a = 255 } },
    .{ .{ .r = 70, .g = 62, .b = 160, .a = 255 }, .{ .r = 40, .g = 42, .b = 50, .a = 255 }, .{ .r = 150, .g = 255, .b = 40, .a = 255 } },
    .{ .{ .r = 60, .g = 150, .b = 160, .a = 255 }, .{ .r = 44, .g = 48, .b = 54, .a = 255 }, .{ .r = 255, .g = 90, .b = 40, .a = 255 } },
};

fn drawSkinned(r: *gfx.Renderer, model: rl.Model, transform: rl.Matrix, weapon: u8) void {
    const tier = @intFromEnum(skin);

    if (tier < 9 or r.phase != .main) return r.drawModel(model, transform);

    for (model.materials[0..@intCast(model.materialCount)]) |m| {
        if (m.maps[0].texture.id > 1) return r.drawModel(model, transform);
    }

    const set = skin_colors[(@as(usize, weapon) + tier) % skin_colors.len];
    const mats = model.materials[0..@intCast(model.materialCount)];
    var saved: [24]rl.Color = undefined;
    const n = @min(mats.len, saved.len);

    for (mats[0..n], 0..) |*m, i| {
        saved[i] = m.maps[0].color;

        m.maps[0].color = switch (i % 3) {
            0 => set[0],
            1 => set[1],
            else => set[2],
        };
    }

    r.drawModel(model, transform);

    for (mats[0..n], 0..) |*m, i| m.maps[0].color = saved[i];
}

pub fn drawGun(r: *gfx.Renderer, models: *const Models, arts: *const [weapons.count]gunart.Art, weapon: u8, origin: Vec3, basis: Basis, s: f32) void {
    const art = arts[weapon];
    const body = art.body orelse {
        r.draw(models.guns[weapon], mesh.transform(origin, basis, s), true);

        return;
    };

    drawSkinned(r, body, mesh.transform(origin, basis, s), weapon);

    if (art.extra) |extra| {
        const at = origin.add(basis.x.scale(extra.offset.x * s)).add(basis.y.scale(extra.offset.y * s)).add(basis.z.scale(extra.offset.z * s));

        r.drawModel(extra.model, mesh.transform(at, basis, s));
    }
    drawOptic(r, art, origin, basis, s);
}

fn adsGloves(r: *gfx.Renderer, models: *const Models, v: View, pose: Pose, pistol: bool) void {
    const down = v.up.neg();
    const gr = if (pistol)
        v.eye.add(v.forward.scale(ads_r[0])).add(down.scale(ads_r[1] + 0.01)).add(v.right.scale(0.0))
    else
        v.eye.add(v.forward.scale(ads_r[0])).add(down.scale(ads_r[1])).add(v.right.scale(ads_r[2]));
    const er = gr.add(down.scale(0.3)).add(v.forward.scale(-0.12)).add(v.right.scale(0.12));

    limb(r, models.block_sleeve, gr.add(er.sub(gr).normalize().scale(0.03)), er, 0.04);
    r.draw(models.block_glove, mesh.transform(gr, pose.basis, ads_r[3]), false);

    if (pistol) return;

    const gl = v.eye.add(v.forward.scale(ads_l[0])).add(down.scale(ads_l[1])).add(v.right.scale(ads_l[2]));
    const el = gl.add(down.scale(0.4)).add(v.forward.scale(-0.1)).add(v.right.scale(-0.14));

    limb(r, models.block_sleeve, gl.add(el.sub(gl).normalize().scale(0.03)), el, 0.042);
    r.draw(models.block_glove, mesh.transform(gl, pose.basis, ads_l[3]), false);
}

pub var ads_r = [4]f32{ 0.22, 0.1, 0.04, 0.8 };
pub var ads_l = [4]f32{ 0.32, 0.12, -0.085, 0.85 };

fn scopeSetup(art: gunart.Art) void {
    scope_eyepiece = null;

    const o = art.optic orelse return;

    if (o.kind == gunart.none) return;

    scope_eyepiece = gunart.eyepiece(o);
    scope_relief = gunart.relief(o);
}

fn drawOptic(r: *gfx.Renderer, art: gunart.Art, origin: Vec3, basis: Basis, s: f32) void {
    const o = art.optic orelse return;

    if (o.kind == gunart.none) return;

    const model = (if (optic_see_through) gunart.optic_open[o.kind] else gunart.optic_models[o.kind]) orelse return;
    const at = origin.add(basis.y.scale(o.y * s)).add(basis.z.scale(o.z * s));
    const turned: Basis = .{ .x = basis.x.neg(), .y = basis.y, .z = basis.z.neg() };

    r.drawModel(model, mesh.transform(at, turned, o.scale * s));
}

fn limb(r: *gfx.Renderer, m: rl.Mesh, a: Vec3, b: Vec3, radius: f32) void {
    const d = b.sub(a);
    const len = d.length();

    if (len < 1e-4) return;

    const y = d.scale(1 / len);
    const ref: Vec3 = if (@abs(y.y) > 0.9) .{ .x = 1 } else .{ .y = 1 };
    const x = ref.cross(y).normalize();
    const z = x.cross(y);
    const t: rl.Matrix = .{
        .m0 = x.x * radius,
        .m1 = x.y * radius,
        .m2 = x.z * radius,
        .m4 = d.x,
        .m5 = d.y,
        .m6 = d.z,
        .m8 = z.x * radius,
        .m9 = z.y * radius,
        .m10 = z.z * radius,
        .m12 = a.x,
        .m13 = a.y,
        .m14 = a.z,
        .m15 = 1,
    };

    r.draw(m, t, false);
}

var hand_models: ?[2]rl.Model = null;
var arm_models: ?[2]rl.Model = null;
var arm_tried = false;

fn armModels() ?[2]rl.Model {
    if (arm_models) |h| return h;

    if (arm_tried) return null;

    arm_tried = true;

    var a: [512]u8 = undefined;
    var b: [512]u8 = undefined;
    const right = rl.LoadModel(assets.file(&a, "characters/arm_r.glb").ptr);
    const left = rl.LoadModel(assets.file(&b, "characters/arm_l.glb").ptr);

    if (right.meshCount == 0 or left.meshCount == 0) return null;

    arm_models = .{ right, left };

    return arm_models;
}

fn handModels() ?[2]rl.Model {
    if (hand_models) |h| return h;

    var a: [512]u8 = undefined;
    var b: [512]u8 = undefined;
    const right = rl.LoadModel(assets.file(&a, "characters/hand_r.glb").ptr);
    const left = rl.LoadModel(assets.file(&b, "characters/hand_l.glb").ptr);

    if (right.meshCount == 0 or left.meshCount == 0) return null;

    hand_models = .{ right, left };

    return hand_models;
}

fn arm(r: *gfx.Renderer, models: *const Models, shoulder: Vec3, hand: Vec3, out: Vec3, down: Vec3, glove_basis: Basis) void {
    _ = shoulder;
    _ = out;
    _ = down;
    r.draw(models.glove, mesh.transform(hand, glove_basis, 0.85), false);
}

fn bowNock(art: gunart.Art, charge: f32, full: f32) f32 {
    const base: f32 = if (art.tips) |t| t[1] else 0.07;

    return base + 0.2 * math.clamp01(charge / @max(0.01, full));
}

fn arms(r: *gfx.Renderer, models: *const Models, arts: *const [weapons.count]gunart.Art, g: Game, v: View, pose: Pose) void {
    const held = g.arsenal.current();
    const spec = held.spec();
    const art = arts[held.weapon];
    const down = v.up.neg();
    const box: rl.BoundingBox = art.box orelse .{ .min = .{ .x = -0.02, .y = art.bottom, .z = -spec.reach() }, .max = .{ .x = 0.02, .y = art.top, .z = 0.05 } };
    const len = box.max.z - box.min.z;
    const low = box.min.y;
    const grip_local: Vec3 = switch (spec.class) {
        .pistol => .{ .x = -0.008, .y = low * 0.4, .z = box.max.z - len * 0.25 },
        .melee => .{ .y = -0.01, .z = @min(0.06, box.max.z * 0.5) },
        .bow => .{ .y = -0.01, .z = -0.01 },
        else => .{ .x = -0.012, .y = low * 0.28, .z = box.max.z - len * 0.3 },
    };
    const fore_local: Vec3 = switch (spec.class) {
        .pistol => .{ .x = -0.025, .y = low * 0.55, .z = box.max.z - len * 0.32 },
        .bow => .{ .x = 0.0, .y = 0.0, .z = 0.3 },
        else => .{ .x = -0.01, .y = low * 0.04, .z = box.min.z + len * 0.3 },
    };
    const at = struct {
        fn p(o: Vec3, b: Basis, l: Vec3) Vec3 {
            return o.add(b.x.scale(l.x)).add(b.y.scale(l.y)).add(b.z.scale(l.z));
        }
    }.p;
    const right_hand = at(pose.origin, pose.basis, grip_local);
    const left_hand = at(pose.origin, pose.basis, fore_local);
    const right_shoulder = v.eye.add(v.right.scale(0.26)).add(down.scale(0.4)).add(v.forward.scale(-0.04));
    const left_shoulder = v.eye.add(v.right.scale(-0.2)).add(down.scale(0.4)).add(v.forward.scale(0.02));
    const glove_r: Basis = .{ .x = pose.basis.x, .y = pose.basis.y, .z = pose.basis.z };
    const glove_l = Basis{ .x = pose.basis.y.neg(), .y = pose.basis.x, .z = pose.basis.z };

    if (spec.class == .bow) {
        if (handModels()) |hands| {
            const a = g.arsenal;
            const tips = art.tips orelse [2]f32{ 0.36, 0.05 };
            const loaded = held.mag > 0 and a.reloading <= 0;
            const nock_z = if (loaded) bowNock(art, a.charge, spec.charge) else tips[1];
            const grip = at(pose.origin, pose.basis, .{ .y = -0.012, .z = 0.004 });
            const nock = at(pose.origin, pose.basis, .{ .z = nock_z });
            const draw_hand = at(pose.origin, pose.basis, .{ .x = 0.006, .y = -0.028, .z = nock_z + 0.035 });

            r.setSurface(.{ .roughness = 0.9 });
            r.drawModel(hands[1], mesh.transform(grip, pose.basis, 1.05));
            r.drawModel(hands[0], mesh.transform(draw_hand, pose.basis, 0.9));

            if (gunart.string) |sm| {
                const top = at(pose.origin, pose.basis, .{ .y = tips[0], .z = tips[1] });
                const bottom = at(pose.origin, pose.basis, .{ .y = -tips[0], .z = tips[1] });

                r.setSurface(.{ .roughness = 0.8 });
                r.drawModel(sm, mesh.segment(top, nock, 0.0016));
                r.drawModel(sm, mesh.segment(nock, bottom, 0.0016));
            }

            return;
        }
    }

    if (blocky_hands and spec.class != .bow) {
        const kb: f32 = if (spec.class == .pistol) 0.85 else 1;
        const gr = at(right_hand, pose.basis, .{ .y = -0.015, .z = 0.015 }).add(down.scale(0.03 * g.ads));
        const er = gr.add(down.scale(0.4)).add(pose.basis.z.scale(0.35)).add(v.right.scale(0.3));

        r.setSurface(.{ .roughness = 0.9 });

        if (g.ads > 0.3 and spec.class != .melee and spec.class != .crossbow) {
            adsGloves(r, models, v, pose, spec.class == .pistol);

            return;
        }

        limb(r, models.block_sleeve, gr.add(er.sub(gr).normalize().scale(0.05)), er, 0.06);
        r.draw(models.block_glove, mesh.transform(gr, pose.basis, kb * 1.2), false);

        return;
    }

    if (armModels()) |am| {
        r.setSurface(.{ .roughness = 0.9 });
        const ro: Vec3 = switch (spec.class) {
            .pistol => .{ .y = 0.05 - 0.03 * g.ads, .z = 0.04 },
            .melee => .{ .y = -0.02, .z = -0.03 - 0.07 * math.clamp01((len - 0.35) / 0.6) },
            else => .{ .y = 0.018, .z = 0.058 },
        };
        const lo: Vec3 = .{ .y = 0.005 - 0.035 * g.ads, .z = -0.02 * g.ads };

        const rs: f32 = if (spec.class == .pistol) arm_scale * (0.92 - 0.12 * g.ads) else arm_scale;

        const rb = if (spec.class == .melee) rotateBasis(pose.basis, pose.basis.x, melee_tilt) else pose.basis;

        r.drawModel(am[0], mesh.transform(at(right_hand, pose.basis, ro.add(r_off)), rb, rs));

        if (spec.class != .melee and spec.class != .pistol) {
            const reach_fwd = math.clamp01((-fore_local.z - 0.25) / 0.35);
            const lb = rotateBasis(pose.basis, pose.basis.z, (l_roll + l_roll_far * reach_fwd) * (1 - g.ads));

            r.drawModel(am[1], mesh.transform(at(left_hand, pose.basis, lo.add(l_off)), lb, arm_scale));
        }

        return;
    }

    if (handModels()) |hands| {
        const k: f32 = if (spec.class == .pistol) 0.9 else std.math.clamp((box.max.y - box.min.y) / 0.19, 0.7, 1.0) * 1.05;

        const cuff_r = at(right_hand, pose.basis, .{ .x = 0.004 * k, .y = -0.062 * k, .z = 0.05 * k });
        const end_r = cuff_r.add(down.scale(0.5)).add(pose.basis.z.scale(0.22)).add(v.right.scale(0.06));

        const sleeves = spec.class != .melee and g.ads < 0.3;

        r.setSurface(.{ .roughness = 0.9 });

        if (sleeves) limb(r, models.sleeve, cuff_r, end_r, 0.045);

        r.drawModel(hands[0], mesh.transform(right_hand, pose.basis, k));

        if (spec.class != .melee and spec.class != .pistol) {
            const cuff_l = at(left_hand, pose.basis, .{ .x = -0.015 * k, .y = -0.075 * k, .z = 0.065 * k });
            const end_l = cuff_l.add(down.scale(0.6)).add(pose.basis.z.scale(0.18)).add(v.right.scale(-0.05));

            r.setSurface(.{ .roughness = 0.9 });

            if (sleeves) limb(r, models.sleeve, cuff_l, end_l, 0.043);

            r.drawModel(hands[1], mesh.transform(left_hand, pose.basis, k));
        }

        return;
    }

    arm(r, models, right_shoulder, right_hand, v.right, down, glove_r);

    if (spec.class != .melee) arm(r, models, left_shoulder, left_hand, v.right.neg(), down, glove_l);
}

fn drawChunks(r: *gfx.Renderer, v: View) void {
    const fwd = Vec3{ .x = v.forward.x, .z = v.forward.z };
    const flen = fwd.length();
    const f = if (flen > 0.01) fwd.scale(1 / flen) else Vec3{ .z = 1 };
    const shadow = r.phase == .shadow;

    for (models_mod.chunks) |*c| {
        const d = Vec3{ .x = c.cx - v.eye.x, .z = c.cz - v.eye.z };
        const dist = d.length();

        if (shadow and dist > 200 + c.r) continue;

        if (dist > c.r * 1.2 and d.scale(1 / dist).dot(f) < -0.35 and !shadow) continue;

        if (dist > 760) continue;

        if (!shadow and !gfx.sphereVisible(.{ .x = c.cx, .y = 20, .z = c.cz }, c.r + 45)) continue;

        if (!shadow and !pvs.visible(v.eye, .{ .x = c.cx, .z = c.cz }, c.r)) continue;

        const near = dist < 230 + c.r;

        r.setSurface(.{ .roughness = 1, .metallic = 0 });
        r.setDetailMode(1);
        r.draw(if (near) c.hi else c.lo, mesh.identity, near);
        r.setDetailMode(0);

        if (dist < 480 + c.r) {
            r.setSurface(.{ .roughness = 0.75, .metallic = 0.05 });

            for (c.things[0..c.things_n]) |m| r.draw(m, mesh.identity, dist < 220 + c.r);
        }
    }
}

fn dust(eye: Vec3, t: f32) void {
    const cur = shared.terrain.current;

    if (cur != .facility and cur != .conquest) return;

    const inside = indoors(eye);
    const span: f32 = if (inside) 18 else 26;
    const col: rl.Color = if (inside) .{ .r = 236, .g = 228, .b = 204, .a = 150 } else .{ .r = 214, .g = 198, .b = 160, .a = 130 };

    for (0..70) |i| {
        const f: f32 = @floatFromInt(i);
        const hx = @abs(@mod(@sin(f * 12.9898) * 43758.5453, 1.0));
        const hz = @abs(@mod(@sin(f * 78.233) * 24634.634, 1.0));
        const hy = @abs(@mod(@sin(f * 39.425) * 14325.159, 1.0));
        const x = eye.x - span / 2 + @mod(hx * span + t * (0.35 + hy * 0.4) - eye.x, span);
        const z = eye.z - span / 2 + @mod(hz * span + t * 0.15 - eye.z, span);
        const y = eye.y - 1.2 + @mod(hy * 5 + @sin(t * 0.6 + f) * 0.3, 5);
        const sz: f32 = 0.025 + hy * 0.02;

        rl.DrawCubeV(.{ .x = x, .y = y, .z = z }, .{ .x = sz, .y = sz, .z = sz }, col);
    }
}

fn indoors(eye: Vec3) bool {
    for (shared.world.hangar_zones[0..shared.world.hangar_count]) |h| {
        if (@abs(eye.x - h[0]) < 13.6 and @abs(eye.z - h[1]) < 9.4 and eye.y < h[2] + 9.5) return true;
    }

    return shared.terrain.current == .facility and @abs(eye.x) < 56 and @abs(eye.z) < 44 and eye.y < 17;
}

pub var clean_shot = false;

pub var part_ms: [7]f32 = @splat(0);
var part_t: f64 = 0;

fn mark(i: usize) void {
    const now = rl.GetTime();

    if (i > 0) part_ms[i - 1] += @floatCast(now - part_t);
    part_t = now;
}

pub fn scene(r: *gfx.Renderer, models: *const Models, arts: *const [weapons.count]gunart.Art, scenery: *propart.Props, rig: *soldier.Rig, kit: soldier.Kit, cars: *const vehicleart.Art, g: Game, v: View, dt: f32) void {
    mark(0);
    r.ambientBoost(if (indoors(v.eye)) 1.8 else 1);
    r.setSurface(.{ .roughness = 1, .metallic = 0 });
    r.draw(models.backdrop, mesh.identity, false);
    r.setDetailMode(0);
    r.draw(models.world, mesh.identity, true);

    for (models_mod.extraMeshes()) |em| r.draw(em, mesh.identity, true);

    if (shared.terrain.current != .courtyard) drawChunks(r, v);
    mark(1);
    r.setDetailMode(0);
    r.setSurface(.{ .roughness = 0.9, .metallic = 0 });
    r.setPropDetail(true);
    scenery.draw(r, v.eye, v.forward);
    mark(2);
    cover.draw(r, v.eye);
    mark(3);
    r.setPropDetail(false);
    r.setSurface(.{ .roughness = 0.5 });

    for (g.drops.items) |d| {
        if (!d.active) continue;

        const gap = d.pos.sub(v.eye).length();

        if (gap > 90 or (gap > 3 and (!gfx.sphereVisible(d.pos, 1.5) or !pvs.visible(v.eye, d.pos, 1)))) continue;

        const bob: Vec3 = .{ .y = @sin(d.phase * 1.3) * 0.08 };

        const near = gap < 40;

        skin = if (near) d.held.rarity else .common;
        drawGun(r, models, arts, d.held.weapon, d.pos.add(bob), Basis.yawed(d.phase), 1.6);
        skin = .common;

        if (near) r.draw(models.beams[@intFromEnum(d.held.rarity)], mesh.transform(d.pos, Basis.world, 1), false);
    }

    for (g.pickups.items) |p| {
        if (!p.active) continue;

        const gap = p.pos.sub(v.eye).length();

        if (gap > 90 or (gap > 3 and (!gfx.sphereVisible(p.pos, 1) or !pvs.visible(v.eye, p.pos, 1)))) continue;

        const m = if (p.kind == .ammo) models.pickup else models.medkit;
        const at = p.pos.add(.{ .y = @sin(p.phase) * 0.12 });

        r.draw(m, mesh.transform(at, Basis.yawed(p.phase * 0.6), 1), true);
    }

    r.setSheen(0.75);

    vehicleart.eye = v.eye;

    for (g.vehicles) |car| {
        const to = car.pos.sub(v.eye);
        const dist = to.length();
        const limit: f32 = if (r.phase == .shadow) 45 else 220;

        if (dist > limit) continue;

        if (dist > 6 and r.phase != .shadow and (!gfx.sphereVisible(car.pos, 6) or !pvs.visible(v.eye, car.pos, 4))) continue;

        vehicleart.draw(r, cars, car, g.accumulator / movement.dt);
    }

    air.draw(r, models, g.accumulator / movement.dt);
    r.setSheen(0);

    if (driving.current(&g)) |car| {
        if (car.spec().class != .tank) {
            const alpha = g.accumulator / movement.dt;
            const basis = vehicleart.bodyBasis(car);
            const aiming = g.ads > 0.3 or g.arsenal.flash > 0 or driving.lean > 0.3;
            const s = car.spec();
            const drop: f32 = if (s.class == .car) 0.82 else 0.5;
            var seat_at = vehicleart.seatPoint(car, alpha);
            var body = basis;

            if (s.class == .car and driving.lean > 0.01) {
                const k = driving.lean;
                const k2 = k * k * (3 - 2 * k);
                const side: f32 = if (v.forward.dot(basis.x) < -0.15) -1 else 1;
                const out = side * (s.width * 0.5 + 0.05) - 0.36;
                const flat = Vec3{ .x = v.forward.x, .z = v.forward.z };
                const turn = std.math.atan2(flat.dot(basis.x), flat.dot(basis.z));

                seat_at = seat_at.add(basis.x.scale(out * k2)).add(basis.y.scale(0.42 * k2));
                body = rotateBasis(body, basis.z, -side * 0.55 * k2);
                body = rotateBasis(body, basis.y, -turn * 0.7 * k2);
            }

            soldier.drawRider(r, rig, kit, models, arts, seat_at, body, drop, g.arsenal.current().weapon, if (aiming) v.forward else null, g.arsenal.flash / 0.05, dt);
        }
    }

    for (g.bots.items) |b| {
        if (!b.active or !b.riding) continue;

        const k = b.seat orelse continue;

        if (k >= g.vehicles.len) continue;

        const car = g.vehicles[k];
        const s = car.spec();

        if (s.class == .tank) continue;

        const drop: f32 = if (s.class == .car) 0.82 else 0.5;

        soldier.drawRider(r, rig, kit, models, arts, vehicleart.seatPoint(car, 1), vehicleart.bodyBasis(car), drop, b.weapon, null, 0, 0);
    }

    r.setSurface(.{ .roughness = 0.7 });
    mark(4);
    soldier.draw(r, rig, kit, models, arts, g, g.accumulator / movement.dt, dt);
    mark(5);
    r.setSurface(.{ .roughness = 0.5 });

    for (g.projectiles.items) |p| {
        if (!p.active) continue;

        switch (p.kind) {
            .rocket => r.draw(models.rocket, mesh.transform(p.pos, Basis.facing(p.heading), 1), true),
            .grenade => r.draw(models.grenade, mesh.transform(p.pos, Basis.yawed(p.spin), 1), true),
            .orb => r.draw(models.orb, mesh.transform(p.pos, Basis.world, 1), true),
            .fireball => {},
            .arrow => if (gunart.arrow) |m| r.drawModel(m, mesh.transform(p.pos, Basis.facing(p.heading), 1)) else r.draw(models.arrow, mesh.transform(p.pos, Basis.facing(p.heading), 1), true),
            .gun => if (p.item) |item| drawGun(r, models, arts, item.weapon, p.pos, rotateBasis(Basis.facing(p.heading), Basis.facing(p.heading).x, p.spin * 1.5), 1.4),
        }
    }

    scenery.drawGlass(r, v.eye, v.forward);

    if (fx_state == null) fx_state = fx_mod.Fx.init();

    fx_state.?.draw(r, g, .{ .right = v.right, .up = v.up, .eye = v.eye, .forward = v.forward, .muzzle = v.muzzle });

    if (r.phase != .shadow) dust(v.eye, g.time);
    mark(6);

    if (driving.driving() or air.flying() or clean_shot) return;

    r.clearDepth();
    r.viewmodelProjection();
    r.ambientBoost(if (indoors(v.eye)) 2.1 else 1.35);
    r.setSurface(.{ .roughness = 0.5, .metallic = 0.08 });

    const held_art = arts[g.arsenal.current().weapon];
    const sight_top: ?f32 = if (held_art.optic) |o| o.eye - sightHeight(g.arsenal.spec()) else if (held_art.body != null) held_art.top else null;

    scopeSetup(held_art);
    gfx.vm_near = if (scope_eyepiece != null) 0.02 + @max(0, scope_relief - 0.05) * math.clamp01((g.ads - 0.4) / 0.4) else 0.02;
    r.viewmodelProjection();

    if (gunPose(g, v, sight_top)) |pose| {
        const a = g.arsenal;
        const held = a.current();
        const spec = held.spec();

        skin = held.rarity;
        r.setSheen(1);
        optic_see_through = g.ads > 0.5;
        drawGun(r, models, arts, held.weapon, pose.origin, pose.basis, 1);
        optic_see_through = false;
        skin = .common;
        r.setSurface(.{ .roughness = 0.85 });
        r.setSheen(0.45);
        if (show_hands) arms(r, models, arts, g, v, pose);
        r.setSheen(0);

        if (r.phase == .main) fx_state.?.flash(.{ .right = v.right, .up = v.up, .eye = v.eye, .forward = v.forward, .muzzle = v.muzzle }, g);
        r.setSurface(.{ .roughness = 0.5, .metallic = 0.08 });

        if (spec.class != .melee and arts[held.weapon].body == null) {
            const band_at = pose.origin.add(pose.basis.x.scale(0.022)).add(pose.basis.y.scale(-0.004));

            r.draw(models.bands[@intFromEnum(held.rarity)], mesh.transform(band_at, pose.basis, 1), false);
        }

        if ((spec.class == .bow or spec.class == .crossbow) and held.mag > 0 and a.reloading <= 0) {
            const real = arts[held.weapon].body != null;
            const pull: f32 = if (spec.class == .bow) bowNock(arts[held.weapon], a.charge, spec.charge) else if (real) 0.04 - 0.18 + 0.3 else 0.08 - spec.look.body;
            const lift: f32 = if (spec.class == .bow) 0 else if (real) 0.028 else 0.03;
            const at = pose.origin.add(pose.basis.z.scale(pull - 0.3)).add(pose.basis.y.scale(lift));

            if (spec.class == .crossbow and real and gunart.bolt != null) {
                r.drawModel(gunart.bolt.?, mesh.transform(at, pose.basis, 1));
            } else if (gunart.arrow) |m| {
                r.drawModel(m, mesh.transform(at, pose.basis, 1));
            } else {
                r.draw(models.arrow, mesh.transform(at, pose.basis, 1), true);
            }
        }
    }
}

const Projector = struct {
    cam: rl.Camera3D,
    eye: Vec3,
    forward: Vec3,
    focal: f32,

    fn init(cam: rl.Camera3D, v: View) Projector {
        const h: f32 = @floatFromInt(rl.GetScreenHeight());

        return .{
            .cam = cam,
            .eye = v.eye,
            .forward = v.forward,
            .focal = h * 0.5 / @tan(cam.fovy * 0.5 * std.math.pi / 180),
        };
    }

    fn depth(p: Projector, at: Vec3) f32 {
        return at.sub(p.eye).dot(p.forward);
    }

    fn point(p: Projector, at: Vec3) ?rl.Vector2 {
        if (p.depth(at) < 0.1) return null;

        return rl.GetWorldToScreen(v3(at), p.cam);
    }

    fn visible(p: Projector, at: Vec3) ?rl.Vector2 {
        const screen = p.point(at) orelse return null;
        const to = at.sub(p.eye);
        const dist = to.length();

        if (dist > 0.4) {
            if (movement.raycast(shared.world.pieces, p.eye, to.scale(1 / dist), dist - 0.35) != null) return null;
        }

        return screen;
    }

    fn pixels(p: Projector, at: Vec3, size: f32) f32 {
        return size * p.focal / @max(0.1, p.depth(at));
    }
};

pub fn overlay(g: Game, v: View, cam: rl.Camera3D, font: rl.Font) void {
    const pr = Projector.init(cam, v);
    const u: f32 = @as(f32, @floatFromInt(rl.GetScreenHeight())) / 900;

    for (g.bots.items) |d| {
        if (!d.alive() or d.hp >= d.max_hp) continue;

        const p = pr.visible(d.body.pos.add(.{ .y = 2.15 })) orelse continue;
        const w = 64 * u;

        ui.bar(p.x - w / 2, p.y, w, 8 * u, math.clamp01(d.hp / d.max_hp), ui.red);
    }

    for (g.vehicles, 0..) |car, i| {
        if (!car.alive() or car.hp >= car.spec().hp or driving.seat == i) continue;

        const p = pr.visible(car.pos.add(.{ .y = car.spec().height + 0.6 })) orelse continue;
        const w = 80 * u;

        ui.bar(p.x - w / 2, p.y, w, 8 * u, math.clamp01(car.hp / car.spec().hp), ui.rgba(255, 196, 90, 255));
    }

    var buf: [16]u8 = undefined;

    for (g.popups.items) |pop| {
        if (!pop.active) continue;

        const p = pr.visible(pop.pos) orelse continue;
        const str = std.mem.printSentinel(&buf, "{d}", .{pop.value}, 0) catch continue;
        const size = 30 * u;

        ui.outlined(font, str, p.x - ui.width(font, str, size) / 2, p.y, size, ui.fade(ui.white, pop.life * 2));
    }
}
