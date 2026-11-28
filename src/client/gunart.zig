const std = @import("std");

pub var tick: ?*const fn () void = null;
const rl = @import("raylib");
const mesh = @import("mesh.zig");
const shared = @import("shared");
const assets = @import("assets.zig");
const etc = @import("etc.zig");

const weapons = shared.weapons;
const Vec3 = shared.math.Vec3;

pub const Part = struct {
    model: rl.Model,
    offset: Vec3 = .{},
};

pub const Art = struct {
    body: ?rl.Model = null,
    extra: ?Part = null,
    top: f32 = 0.03,
    bottom: f32 = -0.03,
    blade: bool = false,
    box: ?rl.BoundingBox = null,
    tips: ?[2]f32 = null,
    optic: ?Mount = null,
};

pub const Mount = struct {
    kind: usize,
    y: f32,
    z: f32,
    scale: f32,
    eye: f32,
    risers: [4]f32 = @splat(0),
};

const OpticInfo = struct {
    file: []const u8,
    length: f32,
    eye: f32,
};

const optic_info = [_]OpticInfo{
    .{ .file = "Optic_Dot", .length = 0.026, .eye = 0.034 },
    .{ .file = "Optic_Holo", .length = 0.06, .eye = 0.04 },
    .{ .file = "Optic_Scope2", .length = 0.12, .eye = 0.034 },
    .{ .file = "Optic_Scope4", .length = 0.18, .eye = 0.036 },
    .{ .file = "Optic_Scope8", .length = 0.25, .eye = 0.0384 },
    .{ .file = "Sight_X2", .length = 0.04, .eye = 0.028 },
    .{ .file = "Sight_X4", .length = 0.046, .eye = 0.041 },
    .{ .file = "Sight_X8", .length = 0.056, .eye = 0.054 },
};

pub var optic_models: [optic_info.len]?rl.Model = @splat(null);
pub var optic_open: [optic_info.len]?rl.Model = @splat(null);
var open_meshes: [optic_info.len][48]rl.Mesh = undefined;
var open_mats: [optic_info.len][48]c_int = undefined;

fn lensFree(i: usize, m: rl.Model) rl.Model {
    var out = m;
    var n: usize = 0;

    for (0..@intCast(m.meshCount)) |k| {
        const mi: usize = @intCast(m.meshMaterial[k]);
        const c = m.materials[mi].maps[0].color;
        const lens = @as(i32, c.b) > @as(i32, c.r) + 40 and @as(i32, c.g) > @as(i32, c.r) + 30;

        if (lens or n >= 48) continue;

        open_meshes[i][n] = m.meshes[k];
        open_mats[i][n] = m.meshMaterial[k];
        n += 1;
    }

    out.meshes = &open_meshes[i];
    out.meshMaterial = &open_mats[i];
    out.meshCount = @intCast(n);

    return out;
}

const reliefs = [_]f32{ 0.15, 0.16, 0.11, 0.095, 0.085, 0.12, 0.11, 0.1 };
const lenses = [_]f32{ 0.127, 0.176, 0.262, 0.09 };
const first_sight = 5;

pub fn aimed(o: Mount, zoom: f32, magnified: bool) Mount {
    const step: usize = if (!magnified) 3 else if (zoom < 3) 0 else if (zoom < 5) 1 else 2;
    const y = o.y + o.risers[step];
    const kind = if (magnified) first_sight + step else o.kind;

    return .{ .kind = kind, .y = y, .z = o.z, .scale = o.scale, .eye = y + optic_info[kind].eye * o.scale };
}

fn riser(body: rl.Model, o: Mount, step: usize) f32 {
    const kind = if (step == 3) o.kind else first_sight + step;
    const eye = o.y + optic_info[kind].eye * o.scale;
    const near = (reliefs[kind] + optic_info[kind].length / 2) * o.scale;
    var lift: f32 = 0;

    for (body.meshes[0..@intCast(body.meshCount)]) |m| {
        if (m.vertices == null) continue;

        const v = m.vertices[0..@intCast(m.vertexCount * 3)];
        var i: usize = 0;

        while (i < v.len) : (i += 3) {
            const d = near + o.z - v[i + 2];

            if (d < 0.03) continue;

            const open = lenses[step] * d;

            if (@abs(v[i]) > open * 0.7) continue;

            lift = @max(lift, v[i + 1] + open * 0.45 - eye);
        }
    }

    return @min(lift, 0.075);
}

pub fn eyepiece(o: Mount) f32 {
    return o.z + optic_info[o.kind].length * o.scale / 2;
}

pub fn relief(o: Mount) f32 {
    return reliefs[o.kind] * o.scale;
}


pub const none: usize = 255;

fn opticKind(o: weapons.Optic) usize {
    return switch (o) {
        .iron, .dot => 0,
        .holo => 1,
        .scope2 => 2,
        .scope4 => 3,
        .scope8 => 4,
    };
}

fn fitOptic(body: rl.Model, box: rl.BoundingBox, spec: weapons.Spec) ?Mount {
    const slices = 32;
    const len = box.max.z - box.min.z;

    if (len < 0.05) return null;

    var tops: [slices]f32 = @splat(-1e9);

    for (body.meshes[0..@intCast(body.meshCount)]) |m| {
        if (m.vertices == null) return null;

        const v = m.vertices[0..@intCast(m.vertexCount * 3)];
        var i: usize = 0;

        while (i < v.len) : (i += 3) {
            if (@abs(v[i]) > 0.012) continue;

            const t = (v[i + 2] - box.min.z) / len;
            const k: usize = @intFromFloat(std.math.clamp(t * slices, 0, slices - 1));

            tops[k] = @max(tops[k], v[i + 1]);
        }
    }

    const pistol = spec.class == .pistol;
    const lo: usize = if (pistol) slices * 3 / 10 else slices * 35 / 100;
    const hi: usize = if (pistol) slices * 9 / 10 else slices * 8 / 10;
    var sorted: [slices]f32 = undefined;
    var n: usize = 0;
    var peak: f32 = -1e9;

    for (tops[lo..hi]) |t| {
        if (t < -1e8) continue;

        sorted[n] = t;
        n += 1;
    }

    for (tops[lo .. slices * 19 / 20]) |t| peak = @max(peak, t);

    if (n < 3) return null;

    std.mem.sort(f32, sorted[0..n], {}, std.sort.asc(f32));

    const rail = sorted[n * 3 / 10];
    _ = &peak;

    const kind = opticKind(spec.look.optic);
    const info = optic_info[kind];
    const scale: f32 = if (pistol) 0.6 else std.math.clamp(len / 0.72, 0.55, 1.15);
    const half = info.length * scale / 2;
    var best: usize = lo;
    var run: usize = 0;
    var best_run: usize = 0;

    for (lo..hi) |k| {
        if (tops[k] < rail + 0.008 and tops[k] > -1e8) {
            run += 1;

            if (run > best_run) {
                best_run = run;
                best = k;
            }
        } else run = 0;
    }

    const mid_slice = @as(f32, @floatFromInt(best)) + 0.5 - @as(f32, @floatFromInt(best_run)) / 2;
    var z = box.min.z + mid_slice / slices * len;

    z = std.math.clamp(z, box.min.z + half + len * 0.15, box.max.z - half);

    var base: f32 = rail;

    for (0..slices) |k| {
        const zc = box.min.z + (@as(f32, @floatFromInt(k)) + 0.5) / slices * len;

        if (@abs(zc - z) < half and tops[k] > -1e8) base = @max(base, tops[k]);
    }

    return .{ .kind = kind, .y = base - 0.002, .z = z, .scale = scale, .eye = base - 0.002 + info.eye * scale };
}

fn fallbackOptic(box: rl.BoundingBox, spec: weapons.Spec) Mount {
    const len = box.max.z - box.min.z;
    const kind = opticKind(spec.look.optic);
    const scale: f32 = std.math.clamp(len / 0.72, 0.55, 1.15);
    const y = box.max.y - (box.max.y - box.min.y) * 0.08;

    return .{ .kind = kind, .y = y, .z = box.min.z + len * 0.55, .scale = scale, .eye = y + optic_info[kind].eye * scale };
}

const Plan = struct {
    weapon: []const u8,
    file: []const u8,
    extra: ?[]const u8 = null,
    flip: bool = false,
    exact: bool = false,
    tips: ?[2]f32 = null,
};

pub var arrow: ?rl.Model = null;
pub var bolt: ?rl.Model = null;
pub var string: ?rl.Model = null;

const plans = [_]Plan{
    .{ .weapon = "Pocket", .file = "Mid_Pocket" },
    .{ .weapon = "Nine", .file = "Mid_Nine" },
    .{ .weapon = "Torch", .file = "Mid_Torch" },
    .{ .weapon = "Recurve", .file = "Bow_Recurve", .exact = true, .tips = .{ 0.36, 0.05 } },
    .{ .weapon = "Longbow", .file = "Bow_Longbow", .exact = true, .tips = .{ 0.44, 0.073 } },
    .{ .weapon = "Crossbow", .file = "Bow_Crossbow", .exact = true },
    .{ .weapon = "Rapid Bolt", .file = "Bow_Rapid", .exact = true },
    .{ .weapon = "Hand Cannon", .file = "Mid_HandCannon" },
    .{ .weapon = "Twin Tap", .file = "Mid_TwinTap" },
    .{ .weapon = "Buzzer", .file = "Mid_Buzzer" },
    .{ .weapon = "Six Shooter", .file = "Mid_SixShooter" },
    .{ .weapon = "Buzz", .file = "Mid_Buzz", .flip = true },
    .{ .weapon = "Hornet", .file = "Mid_Hornet" },
    .{ .weapon = "Whip", .file = "Mid_Whip" },
    .{ .weapon = "Stinger", .file = "Mid_Stinger" },
    .{ .weapon = "Drum Kid", .file = "Mid_DrumKid" },
    .{ .weapon = "Burst Box", .file = "Mid_BurstBox" },
    .{ .weapon = "Liner", .file = "Mid_Liner" },
    .{ .weapon = "Ranger", .file = "Mid_Ranger" },
    .{ .weapon = "Brick", .file = "Mid_Brick" },
    .{ .weapon = "Tri-Shot", .file = "Mid_TriShot" },
    .{ .weapon = "Bullpup", .file = "Mid_Bullpup", .flip = true },
    .{ .weapon = "Scout Carbine", .file = "Mid_ScoutCarbine" },
    .{ .weapon = "Thunder", .file = "Mid_Thunder" },
    .{ .weapon = "Bruiser", .file = "Mid_Bruiser" },
    .{ .weapon = "Marksman", .file = "Mid_Marksman" },
    .{ .weapon = "Tapper", .file = "Mid_Tapper" },
    .{ .weapon = "Pierce", .file = "Mid_Pierce" },
    .{ .weapon = "Hunter", .file = "Mid_Hunter" },
    .{ .weapon = "Needle", .file = "Mid_Needle" },
    .{ .weapon = "Longshot", .file = "Mid_Longshot" },
    .{ .weapon = "Whisper", .file = "Mid_Whisper" },
    .{ .weapon = "Elephant", .file = "Mid_Elephant" },
    .{ .weapon = "Hailstone", .file = "Mid_Hailstone" },
    .{ .weapon = "Scatter", .file = "Mid_Scatter" },
    .{ .weapon = "Twins", .file = "Mid_Twins" },
    .{ .weapon = "Rattler", .file = "Mid_Rattler" },
    .{ .weapon = "Thumper", .file = "Mid_Thumper" },
    .{ .weapon = "Barrel Roll", .file = "Mid_BarrelRoll" },
    .{ .weapon = "Chatter", .file = "Mid_Chatter" },
    .{ .weapon = "Drum Line", .file = "Mid_DrumLine" },
    .{ .weapon = "Anchor", .file = "Mid_Anchor" },
    .{ .weapon = "Spinner", .file = "Mid_Spinner" },
    .{ .weapon = "Boomer", .file = "Mid_Boomer" },
    .{ .weapon = "Lobber", .file = "Mid_Lobber" },
    .{ .weapon = "Rail", .file = "Mid_Rail" },
    .{ .weapon = "Edge", .file = "Bayonet" },
};

const blades = [_]Plan{
    .{ .weapon = "Katana", .file = "Blade_Katana" },
    .{ .weapon = "Longsword", .file = "Blade_Longsword" },
    .{ .weapon = "Scimitar", .file = "Blade_Scimitar" },
    .{ .weapon = "Machete", .file = "Blade_Machete" },
    .{ .weapon = "Vampire Blade", .file = "Blade_Vampire" },
};

fn targetLength(class: weapons.Class) f32 {
    return switch (class) {
        .pistol => 0.24,
        .smg => 0.46,
        .rifle => 0.72,
        .dmr => 0.8,
        .sniper => 0.98,
        .shotgun => 0.78,
        .lmg => 0.82,
        .melee => 0.3,
        else => 0.7,
    };
}

fn toDisplay(c: u8) u8 {
    const linear = @as(f32, @floatFromInt(c)) / 255;
    const gamma = std.math.pow(f32, linear, 1.0 / 2.2);

    return @intFromFloat(@min(255, gamma * 255 * 1.1));
}

const Shape = struct {
    top: f32,
    bottom: f32,
};

fn normalize(model: *rl.Model, length: f32, forward_shift: f32) Shape {
    return normalizeEx(model, length, forward_shift, true, null);
}

fn normalizeEx(model: *rl.Model, length: f32, forward_shift: f32, regamma: bool, force_sign: ?f32) Shape {
    var min: Vec3 = .{ .x = 1e9, .y = 1e9, .z = 1e9 };
    var max: Vec3 = .{ .x = -1e9, .y = -1e9, .z = -1e9 };
    const meshes = model.meshes[0..@intCast(model.meshCount)];

    for (meshes) |m| {
        const v = m.vertices[0..@intCast(m.vertexCount * 3)];
        var i: usize = 0;

        while (i < v.len) : (i += 3) {
            min = .{ .x = @min(min.x, v[i]), .y = @min(min.y, v[i + 1]), .z = @min(min.z, v[i + 2]) };
            max = .{ .x = @max(max.x, v[i]), .y = @max(max.y, v[i + 1]), .z = @max(max.z, v[i + 2]) };
        }
    }

    const span = max.x - min.x;
    const slice = span * 0.12;
    var lo_min: f32 = 1e9;
    var lo_max: f32 = -1e9;
    var hi_min: f32 = 1e9;
    var hi_max: f32 = -1e9;

    for (meshes) |m| {
        const v = m.vertices[0..@intCast(m.vertexCount * 3)];
        var i: usize = 0;

        while (i < v.len) : (i += 3) {
            if (v[i] < min.x + slice) {
                lo_min = @min(lo_min, v[i + 1]);
                lo_max = @max(lo_max, v[i + 1]);
            }

            if (v[i] > max.x - slice) {
                hi_min = @min(hi_min, v[i + 1]);
                hi_max = @max(hi_max, v[i + 1]);
            }
        }
    }

    const muzzle_high = (hi_max - hi_min) < (lo_max - lo_min);
    const sign: f32 = force_sign orelse if (muzzle_high) 1 else -1;
    const center = min.add(max).scale(0.5);
    const s = length / @max(span, 1e-4);

    for (meshes) |*m| {
        const count: usize = @intCast(m.vertexCount);
        const v = m.vertices[0 .. count * 3];
        var i: usize = 0;

        while (i < v.len) : (i += 3) {
            const dx = v[i] - center.x;
            const dy = v[i + 1] - center.y;
            const dz = v[i + 2] - center.z;

            v[i] = dz * sign * s;
            v[i + 1] = dy * s;
            v[i + 2] = -dx * sign * s - forward_shift;
        }

        rl.UpdateMeshBuffer(m.*, 0, m.vertices, @intCast(count * 3 * @sizeOf(f32)), 0);

        if (m.normals != null) {
            const n = m.normals[0 .. count * 3];
            var j: usize = 0;

            while (j < n.len) : (j += 3) {
                const nx = n[j];
                const nz = n[j + 2];

                n[j] = nz * sign;
                n[j + 2] = -nx * sign;
            }

            rl.UpdateMeshBuffer(m.*, 2, m.normals, @intCast(count * 3 * @sizeOf(f32)), 0);
        }
    }

    if (regamma) {
        for (model.materials[0..@intCast(model.materialCount)]) |*mat| {
            const c = mat.maps[0].color;

            mat.maps[0].color = .{ .r = toDisplay(c.r), .g = toDisplay(c.g), .b = toDisplay(c.b), .a = 255 };
        }
    }

    return .{ .top = (max.y - center.y) * s, .bottom = (min.y - center.y) * s };
}

fn load(dir: []const u8, file: []const u8) ?rl.Model {
    var buf: [512]u8 = undefined;
    const path = std.fmt.bufPrintSentinel(&buf, "{s}/{s}.glb", .{ dir, file }, 0) catch return null;
    const model = rl.LoadModel(path.ptr);

    if (model.meshCount == 0) return null;

    etc.apply(model, path);

    return model;
}

fn loadGlb(dir: []const u8, file: []const u8) ?rl.Model {
    var buf: [512]u8 = undefined;
    const path = std.fmt.bufPrintSentinel(&buf, "{s}/{s}.glb", .{ dir, file }, 0) catch return null;

    if (!assets.exists(path)) return null;

    const model = rl.LoadModel(path.ptr);

    if (model.meshCount == 0) return null;

    etc.apply(model, path);

    return model;
}

pub fn loadAll(dir: []const u8) [weapons.count]Art {
    var arts: [weapons.count]Art = @splat(.{});

    for (plans) |plan| {
        if (tick) |t| t();

        const index = indexOf(plan.weapon) orelse continue;
        const spec = weapons.specs[index];
        var model = load(dir, plan.file) orelse continue;

        if (plan.exact) {
            const b = rl.GetModelBoundingBox(model);

            arts[index] = .{ .body = model, .top = b.max.y, .bottom = b.min.y, .tips = plan.tips };

            continue;
        }

        const length = targetLength(spec.class);
        const mid = std.mem.startsWith(u8, plan.file, "Mid_");
        const shape = if (mid) normalizeEx(&model, length * 0.85, length * 0.42, false, if (plan.flip) -1 else 1) else normalize(&model, length * 0.85, length * 0.42);

        arts[index] = .{ .body = model, .top = shape.top, .bottom = shape.bottom };

        const extra_file = plan.extra orelse continue;
        var extra = load(dir, extra_file) orelse continue;
        const is_bipod = std.mem.eql(u8, extra_file, "Bipod");
        const extra_len: f32 = if (is_bipod) 0.16 else length * 0.32;

        _ = normalize(&extra, extra_len, 0);

        arts[index].extra = .{
            .model = extra,
            .offset = if (is_bipod) .{ .y = shape.bottom * 0.4, .z = -length * 0.38 } else .{ .y = shape.top + 0.02, .z = -length * 0.08 },
        };
    }

    for (blades) |plan| {
        const index = indexOf(plan.weapon) orelse continue;

        if (loadGlb(dir, plan.file)) |model| {
            arts[index] = .{ .body = model, .top = 0.03, .bottom = -0.03, .blade = true };

            continue;
        }

        const model = load(dir, plan.file) orelse continue;

        arts[index] = .{ .body = model, .top = 0.03, .bottom = -0.03, .blade = true };

        for (model.materials[0..@intCast(model.materialCount)]) |*mat| {
            const c = mat.maps[0].color;

            mat.maps[0].color = .{ .r = toDisplay(c.r), .g = toDisplay(c.g), .b = toDisplay(c.b), .a = 255 };
        }
    }

    arrow = load(dir, "Bow_Arrow");
    bolt = load(dir, "Bow_Bolt");
    string = load(dir, "Bow_String");

    for ([_]?rl.Model{ arrow, bolt, string }) |extra| {
        const m = extra orelse continue;

        mesh.smoothModel(m, 38);
        mesh.dropCpu(m);
    }

    for (optic_info, 0..) |info, i| {
        if (load(dir, info.file)) |m| {
            mesh.dropCpu(m);
            optic_models[i] = m;
            optic_open[i] = lensFree(i, m);
        }
    }

    for (&arts, 0..) |*art, wi| {
        if (art.body) |body| {
            art.box = rl.GetModelBoundingBox(body);

            const spec = weapons.specs[wi];
            const skip = art.blade or art.tips != null or spec.class == .bow or spec.class == .crossbow or spec.class == .melee or spec.flame;

            if (!skip and art.box != null) art.optic = fitOptic(body, art.box.?, spec) orelse fallbackOptic(art.box.?, spec);

            if (art.optic) |*o| {
                for (&o.risers, 0..) |*lift, step| lift.* = riser(body, o.*, step);
            }

            mesh.smoothModel(body, 38);
            mesh.dropCpu(body);
        }

        if (art.extra) |extra| mesh.dropCpu(extra.model);
    }

    return arts;
}

fn indexOf(name: []const u8) ?usize {
    for (weapons.specs, 0..) |s, i| {
        if (std.mem.eql(u8, s.name, name)) return i;
    }

    return null;
}
