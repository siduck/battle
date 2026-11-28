const std = @import("std");
const rl = @import("raylib");
const rlgl = @import("rlgl");
const shared = @import("shared");
const gfx = @import("gfx.zig");
const game_mod = @import("game.zig");
const vehicleart = @import("vehicleart.zig");

const Vec3 = shared.math.Vec3;

pub const View = struct {
    right: Vec3,
    up: Vec3,
    eye: Vec3 = .{},
    forward: Vec3 = .{},
    muzzle: Vec3 = .{},
};

pub const Fx = struct {
    soft: rl.Texture2D,

    pub fn init() Fx {
        const n = 64;
        var img = rl.GenImageColor(n, n, .{ .r = 255, .g = 255, .b = 255, .a = 0 });
        var y: c_int = 0;

        while (y < n) : (y += 1) {
            var x: c_int = 0;

            while (x < n) : (x += 1) {
                const dx = (@as(f32, @floatFromInt(x)) + 0.5) / n * 2 - 1;
                const dy = (@as(f32, @floatFromInt(y)) + 0.5) / n * 2 - 1;
                const d = @sqrt(dx * dx + dy * dy);
                const wob = 0.86 + 0.14 * @sin(std.math.atan2(dy, dx) * 5 + d * 9);
                const a = std.math.clamp(1 - d / wob, 0, 1);

                rl.ImageDrawPixel(&img, x, y, .{ .r = 255, .g = 255, .b = 255, .a = @intFromFloat(a * a * (3 - 2 * a) * 255) });
            }
        }

        const tex = rl.LoadTextureFromImage(img);

        rl.UnloadImage(img);
        rl.SetTextureFilter(tex, rl.TEXTURE_FILTER_BILINEAR);

        return .{ .soft = tex };
    }

    pub fn flash(fx: Fx, v: View, g: game_mod.Game) void {
        flashAt(fx, v, g);
    }

    pub fn draw(fx: Fx, r: *gfx.Renderer, g: game_mod.Game, v: View) void {
        if (r.phase == .shadow) return;

        rlgl.rlDrawRenderBatchActive();
        rlgl.rlDisableDepthMask();
        rlgl.rlDisableBackfaceCulling();

        rl.BeginBlendMode(rl.BLEND_ALPHA);

        for (g.explosions.items) |e| {
            if (!e.active or e.radius < 0.6) continue;

            smoke(fx, v, e);
        }

        dust(fx, v, g);

        if (shared.terrain.current == .desert) motes(fx, v, g.time);

        rl.EndBlendMode();
        rl.BeginBlendMode(rl.BLEND_ADDITIVE);

        for (g.explosions.items) |e| {
            if (!e.active) continue;

            if (e.radius < 0.6) {
                puff(fx, v, e);

                continue;
            }

            fire(fx, v, e);
        }

        for (g.vehicles) |car| {
            if (car.alive() and (car.boosting or car.boost_start > 0)) nitro(fx, v, g, car);
        }

        for (g.tracers.items) |t| {
            if (!t.active) continue;

            tracer(fx, v, t);
        }

        for (g.impacts.items) |im| {
            if (!im.active) continue;

            hit(fx, v, im);
        }

        for (g.shards.items) |sh| {
            if (!sh.active) continue;

            shatter(fx, v, sh);
        }

        for (g.projectiles.items) |p| {
            if (!p.active or p.kind != .fireball) continue;

            const flick = 1 + @sin(p.spin * 3.1) * 0.12;

            sprite(fx, v, p.pos, 0.9 * flick, .{ 255, 236, 170 }, 1);
            sprite(fx, v, p.pos, 1.5 * flick, .{ 255, 130, 30 }, 0.8);

            for (0..6) |k| {
                const fk: f32 = @floatFromInt(k + 1);
                const back = p.pos.sub(p.heading.scale(0.28 * fk)).add(.{ .y = 0.06 * fk + @sin(p.spin + fk) * 0.05 });
                const t = fk / 6;

                sprite(fx, v, back, (1.2 - t * 0.7) * flick, mix3(.{ 255, 170, 60 }, .{ 200, 40, 10 }, t), 0.7 * (1 - t));
            }
        }

        rl.EndBlendMode();
        rlgl.rlDrawRenderBatchActive();
        rlgl.rlEnableDepthMask();
        rlgl.rlEnableBackfaceCulling();
    }
};

fn nitro(fx: Fx, v: View, g: game_mod.Game, car: shared.vehicle.Vehicle) void {
    const s = car.spec();
    const basis = vehicleart.bodyBasis(car);
    const alpha = g.accumulator / shared.movement.dt;
    const pos = car.prev.lerp(car.pos, alpha);
    const back = basis.z.neg();
    const pipes = [_]f32{ -0.22, 0.22 };
    const y = s.height * 0.3;
    const speed = @abs(car.speed);
    const stretch = 0.8 + @min(1.6, speed / 25);
    const t = g.time;

    for (pipes, 0..) |side, pi| {
        const fp: f32 = @floatFromInt(pi);
        const tip = pos.add(basis.x.scale(side * s.width * 0.5)).add(basis.y.scale(y)).add(back.scale(s.length * 0.5));

        if (car.boosting) {
            for (0..9) |k| {
                const fk: f32 = @floatFromInt(k);
                const u = fk / 9;
                const flick = 0.82 + 0.18 * @sin(t * 57 + fk * 1.9 + fp * 3);
                const at = tip.add(back.scale(u * 1.1 * stretch)).add(basis.y.scale(@sin(t * 31 + fk) * 0.02));
                const size = (0.42 - u * 0.3) * flick;
                const core = 1 - u;

                sprite(fx, v, at, size * 1.7, mix3(.{ 70, 140, 255 }, .{ 30, 60, 200 }, u), 0.55 * core);
                sprite(fx, v, at, size, mix3(.{ 235, 245, 255 }, .{ 120, 190, 255 }, @min(1, u * 1.6)), 0.95 * core);
            }

            sprite(fx, v, tip.add(back.scale(0.2)), 1.6, .{ 80, 150, 255 }, 0.28);
        }

        if (car.boost_start > 0) {
            const b = car.boost_start / 0.35;

            sprite(fx, v, tip.add(back.scale(0.3)), (1 - b) * 2.6 + 0.6, .{ 120, 190, 255 }, b * 0.8);
            sprite(fx, v, tip, (1 - b) * 1.2 + 0.4, .{ 240, 248, 255 }, b);
        }
    }
}

fn hash(seed: f32, i: f32) f32 {
    const s = @sin(seed * 12.9898 + i * 78.233) * 43758.5453;

    return s - @floor(s);
}

fn dir(seed: f32, i: f32) Vec3 {
    const a = hash(seed, i) * std.math.tau;
    const y = hash(seed, i + 17.3) * 1.4 - 0.25;
    const c = @sqrt(@max(0, 1 - @min(y * y, 1)));

    return .{ .x = @cos(a) * c, .y = y, .z = @sin(a) * c };
}

fn mix3(a: [3]f32, b: [3]f32, t: f32) [3]f32 {
    return .{ a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t };
}

fn ramp(t: f32) [3]f32 {
    if (t < 0.15) return mix3(.{ 255, 250, 225 }, .{ 255, 210, 110 }, t / 0.15);

    if (t < 0.45) return mix3(.{ 255, 210, 110 }, .{ 250, 120, 30 }, (t - 0.15) / 0.3);

    return mix3(.{ 250, 120, 30 }, .{ 120, 24, 8 }, @min(1, (t - 0.45) / 0.55));
}

fn sprite(fx: Fx, v: View, at: Vec3, size: f32, col: [3]f32, alpha: f32) void {
    if (alpha <= 0.003 or size <= 0) return;

    const rx = v.right.scale(size * 0.5);
    const uy = v.up.scale(size * 0.5);
    const a = at.sub(rx).sub(uy);
    const b = at.add(rx).sub(uy);
    const c = at.add(rx).add(uy);
    const d = at.sub(rx).add(uy);

    rlgl.rlSetTexture(fx.soft.id);
    rlgl.rlBegin(rlgl.RL_QUADS);
    rlgl.rlColor4ub(@intFromFloat(@min(255, col[0])), @intFromFloat(@min(255, col[1])), @intFromFloat(@min(255, col[2])), @intFromFloat(std.math.clamp(alpha, 0, 1) * 255));
    rlgl.rlTexCoord2f(0, 1);
    rlgl.rlVertex3f(a.x, a.y, a.z);
    rlgl.rlTexCoord2f(1, 1);
    rlgl.rlVertex3f(b.x, b.y, b.z);
    rlgl.rlTexCoord2f(1, 0);
    rlgl.rlVertex3f(c.x, c.y, c.z);
    rlgl.rlTexCoord2f(0, 0);
    rlgl.rlVertex3f(d.x, d.y, d.z);
    rlgl.rlEnd();
    rlgl.rlSetTexture(0);
}

fn fire(fx: Fx, v: View, e: game_mod.Explosion) void {
    const t = 1 - e.life / e.total;
    const seed = e.pos.x * 0.37 + e.pos.z * 0.61;
    const r = e.radius;
    const burn = @min(1, t / 0.55);

    if (t < 0.12) sprite(fx, v, e.pos.add(.{ .y = r * 0.2 }), r * (2.2 + t * 10), .{ 255, 244, 210 }, (1 - t / 0.12) * 0.9);

    if (burn < 1) {
        for (0..18) |k| {
            const fk: f32 = @floatFromInt(k);
            const d = dir(seed, fk);
            const speed = 0.55 + hash(seed, fk + 5.1) * 0.6;
            const out = r * speed * (1 - (1 - burn) * (1 - burn) * (1 - burn));
            const at = e.pos.add(d.scale(out)).add(.{ .y = r * burn * burn * 0.9 });
            const life = 0.7 + hash(seed, fk + 9.7) * 0.3;
            const lt = @min(1, burn / life);
            const size = r * (0.55 + hash(seed, fk + 3.3) * 0.5) * (0.6 + lt * 0.9) * (1 - lt * lt * 0.7);

            sprite(fx, v, at, size, ramp(lt), (1 - lt) * 0.95);
        }
    }

    if (t < 0.6) {
        for (0..14) |k| {
            const fk: f32 = @floatFromInt(k + 40);
            const d = dir(seed, fk);
            const st = t / 0.6;
            const speed = r * (2.2 + hash(seed, fk) * 1.6);
            const at = e.pos.add(d.scale(speed * st)).add(.{ .y = -6 * st * st * 0.6 });

            sprite(fx, v, at, 0.09 + r * 0.03, .{ 255, 200, 120 }, (1 - st) * 1.2);
        }
    }

    if (e.fire) {
        for (0..8) |k| {
            const fk: f32 = @floatFromInt(k + 80);
            const d = dir(seed, fk);
            const lt = @min(1, t / (0.6 + hash(seed, fk) * 0.4));
            const at = e.pos.add(.{ .x = d.x * r * 0.5, .y = r * (0.2 + lt * 1.8), .z = d.z * r * 0.5 });

            sprite(fx, v, at, r * 0.35 * (1 - lt), ramp(0.2 + lt * 0.7), (1 - lt) * 0.9);
        }
    }
}

fn smoke(fx: Fx, v: View, e: game_mod.Explosion) void {
    const t = 1 - e.life / e.total;
    const seed = e.pos.x * 0.71 + e.pos.z * 0.29 + 3;
    const r = e.radius;

    if (t < 0.12) return;

    const st = (t - 0.12) / 0.88;

    for (0..12) |k| {
        const fk: f32 = @floatFromInt(k);
        const d = dir(seed, fk);
        const rise = r * (0.6 + hash(seed, fk + 2.2) * 0.8) * (1 - (1 - st) * (1 - st)) * 1.6;
        const out = r * (0.4 + hash(seed, fk + 7.7) * 0.5) * (0.6 + st * 0.6);
        const at = e.pos.add(.{ .x = d.x * out, .y = rise + r * 0.3, .z = d.z * out });
        const size = r * (0.9 + st * 1.8) * (0.8 + hash(seed, fk + 1.1) * 0.4);
        const shade = 38 + hash(seed, fk + 4.4) * 30;

        sprite(fx, v, at, size, .{ shade, shade * 0.95, shade * 0.9 }, (1 - st) * (1 - st) * 0.62 * @min(1, st * 6));
    }

    if (st < 0.6) {
        for (0..14) |k| {
            const fk: f32 = @floatFromInt(k);
            const a = fk / 14 * std.math.tau + seed;
            const rr = r * (0.6 + st * 2.4);
            const at = e.pos.add(.{ .x = @cos(a) * rr, .y = 0.25, .z = @sin(a) * rr });
            const k2 = st / 0.6;

            sprite(fx, v, at, r * 0.7 * (0.6 + k2), .{ 196, 168, 128 }, (1 - k2) * 0.45);
        }
    }
}

fn puff(fx: Fx, v: View, e: game_mod.Explosion) void {
    const t = 1 - e.life / e.total;

    sprite(fx, v, e.pos, e.radius * (1 + t * 2), .{ 255, 200, 120 }, (1 - t) * 0.8);
}

fn streak(fx: Fx, v: View, a: Vec3, b: Vec3, width: f32, col: [3]f32, alpha: f32) void {
    const d = b.sub(a);
    const len = d.length();

    if (len < 0.001 or alpha <= 0.003) return;

    const along = d.scale(1 / len);
    var side = along.cross(v.eye.sub(a)).normalize();

    side = side.scale(width * 0.5);

    const p0 = a.sub(side);
    const p1 = a.add(side);
    const p2 = b.add(side);
    const p3 = b.sub(side);

    rlgl.rlSetTexture(fx.soft.id);
    rlgl.rlBegin(rlgl.RL_QUADS);
    rlgl.rlColor4ub(@intFromFloat(@min(255, col[0])), @intFromFloat(@min(255, col[1])), @intFromFloat(@min(255, col[2])), @intFromFloat(std.math.clamp(alpha, 0, 1) * 255));
    rlgl.rlTexCoord2f(0.5, 0);
    rlgl.rlVertex3f(p0.x, p0.y, p0.z);
    rlgl.rlTexCoord2f(0.5, 1);
    rlgl.rlVertex3f(p1.x, p1.y, p1.z);
    rlgl.rlTexCoord2f(0.5, 1);
    rlgl.rlVertex3f(p2.x, p2.y, p2.z);
    rlgl.rlTexCoord2f(0.5, 0);
    rlgl.rlVertex3f(p3.x, p3.y, p3.z);
    rlgl.rlEnd();
    rlgl.rlSetTexture(0);
}

fn tracer(fx: Fx, v: View, t: game_mod.Tracer) void {
    const total: f32 = if (t.flame) 0.12 else 0.07;
    const k = 1 - std.math.clamp(t.life / total, 0, 1);
    const d = t.to.sub(t.from);
    const len = d.length();

    if (len < 0.01) return;

    const way = d.scale(1 / len);

    if (t.flame) {
        for (0..6) |i| {
            const fi: f32 = @floatFromInt(i);
            const at = t.from.add(way.scale(len * (0.1 + fi * 0.15) * (0.4 + k)));

            sprite(fx, v, at, 0.5 + fi * 0.18, ramp(0.15 + fi * 0.12), (1 - k) * 0.8);
        }

        return;
    }

    const head = @min(len, len * (k * 1.6 + 0.05));
    const tail = @max(0, head - @min(3.5, len * 0.5));
    const a = t.from.add(way.scale(tail));
    const b = t.from.add(way.scale(head));

    streak(fx, v, a, b, 0.05, .{ 255, 200, 110 }, 0.55);
    streak(fx, v, a.add(way.scale((head - tail) * 0.5)), b, 0.022, .{ 255, 250, 230 }, 0.95);
    streak(fx, v, t.from, b, 0.03, .{ 200, 200, 200 }, (1 - k) * 0.12);
}

fn shatter(fx: Fx, v: View, sh: game_mod.Impact) void {
    const t = std.math.clamp(1 - sh.life / 1.4, 0, 1);
    const secs = t * 1.4;
    const seed = sh.seed * 71.0;

    for (0..22) |i| {
        const fi: f32 = @floatFromInt(i);
        const d = dir(seed, fi);
        const spread = Vec3{ .x = d.x * 2.2, .y = 0, .z = d.z * 2.2 };
        const start = Vec3{ .x = (hash(seed, fi + 3.1) - 0.5) * 3.6, .y = hash(seed, fi + 5.7) * 2.2 - 1.0, .z = (hash(seed, fi + 8.3) - 0.5) * 0.4 };
        const at = sh.pos.add(start).add(spread.scale(secs)).add(.{ .y = d.y * 1.5 * secs - 4.9 * secs * secs });
        const glint = 0.6 + 0.4 * @sin(secs * 18 + fi);

        sprite(fx, v, at, 0.07 + hash(seed, fi + 1.9) * 0.12, .{ 210, 250, 248 }, (1 - t) * glint);
    }

    sprite(fx, v, sh.pos, 1.6 + t * 2.4, .{ 150, 230, 230 }, (1 - t) * (1 - t) * 0.35);
}

fn hit(fx: Fx, v: View, im: game_mod.Impact) void {
    const age = std.math.clamp(1 - im.life / 1.6, 0, 1);
    const seed = im.seed * 97.0;

    if (age < 0.2) {
        const k = age / 0.2;

        sprite(fx, v, im.pos, 0.25 + k * 0.15, .{ 255, 220, 150 }, (1 - k) * 0.9);

        for (0..6) |i| {
            const fi: f32 = @floatFromInt(i);
            const d = dir(seed, fi);
            const at = im.pos.add(d.scale(k * (0.4 + hash(seed, fi + 3) * 0.6))).add(.{ .y = -k * k * 0.3 });

            sprite(fx, v, at, 0.05, .{ 255, 200, 120 }, (1 - k) * 1.2);
        }
    }
}

fn motes(fx: Fx, v: View, time: f32) void {
    const box: f32 = 26;
    const wind = Vec3{ .x = 1.3, .y = 0.08, .z = 0.5 };

    for (0..64) |i| {
        const fi: f32 = @floatFromInt(i);
        const base = Vec3{ .x = hash(fi, 1) * box, .y = hash(fi, 2) * 6, .z = hash(fi, 3) * box };
        const drift = wind.scale(time * (0.6 + hash(fi, 4) * 0.8));
        const sway = @sin(time * (0.7 + hash(fi, 5)) + fi) * 0.4;
        const px = @mod(base.x + drift.x + sway - v.eye.x, box) + v.eye.x - box / 2;
        const pz = @mod(base.z + drift.z - v.eye.z, box) + v.eye.z - box / 2;
        const py = v.eye.y - 1.4 + @mod(base.y + drift.y, 6);
        const at = Vec3{ .x = px, .y = py, .z = pz };
        const d = at.sub(v.eye).length();
        const fade = std.math.clamp(1 - d / (box * 0.5), 0, 1) * std.math.clamp((d - 0.8) / 1.5, 0, 1);

        sprite(fx, v, at, 0.035 + hash(fi, 6) * 0.04, .{ 236, 218, 180 }, fade * 0.45);
    }
}

pub fn dust(fx: Fx, v: View, g: game_mod.Game) void {
    for (g.impacts.items) |im| {
        if (!im.active) continue;

        const age = std.math.clamp(1 - im.life / 1.6, 0, 1);
        const seed = im.seed * 53.0;

        for (0..4) |i| {
            const fi: f32 = @floatFromInt(i);
            const d = dir(seed, fi);
            const at = im.pos.add(d.scale(0.12 + age * 0.35)).add(.{ .y = age * 0.4 });

            sprite(fx, v, at, 0.22 + age * 0.55, .{ 196, 176, 146 }, (1 - age) * (1 - age) * 0.5);
        }

        sprite(fx, v, im.pos, 0.16, .{ 28, 26, 24 }, (1 - age * age) * 0.85);
    }
}

pub fn flashAt(fx: Fx, v: View, g: game_mod.Game) void {
    if (g.arsenal.flash <= 0 or g.scoped()) return;

    rlgl.rlDrawRenderBatchActive();
    rlgl.rlDisableDepthTest();
    rlgl.rlDisableDepthMask();
    rlgl.rlDisableBackfaceCulling();
    rl.BeginBlendMode(rl.BLEND_ADDITIVE);

    const seed = g.time * 13.0;
    const m = v.muzzle;
    const f = v.forward;
    const s = 0.8 + hash(seed, 1) * 0.5;

    sprite(fx, v, m.add(f.scale(0.04)), 0.16 * s, .{ 255, 248, 220 }, 1);
    sprite(fx, v, m.add(f.scale(0.06)), 0.32 * s, .{ 255, 170, 60 }, 0.75);
    streak(fx, v, m, m.add(f.scale(0.3 * s)), 0.11 * s, .{ 255, 190, 80 }, 0.9);

    for (0..4) |i| {
        const fi: f32 = @floatFromInt(i);
        const ang = fi * 1.5708 + hash(seed, fi) * 0.6;
        const out = v.right.scale(@cos(ang)).add(v.up.scale(@sin(ang)));

        streak(fx, v, m.add(f.scale(0.03)), m.add(f.scale(0.05)).add(out.scale(0.1 * s)), 0.04, .{ 255, 200, 110 }, 0.7);
    }

    rl.EndBlendMode();
    rlgl.rlDrawRenderBatchActive();
    rlgl.rlEnableDepthMask();
    rlgl.rlEnableDepthTest();
    rlgl.rlEnableBackfaceCulling();
}
