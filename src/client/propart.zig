const std = @import("std");
const rl = @import("raylib");
const rlgl = @import("rlgl");
const shared = @import("shared");
const gfx = @import("gfx.zig");
const settings = @import("settings.zig");
const mesh = @import("mesh.zig");

const props = shared.props;
const world = shared.world;
const Vec3 = shared.math.Vec3;
const pvs = @import("pvs.zig");
const assets = @import("assets.zig");

const kind_count = props.kind_capacity;

const Slot = struct {
    model: ?rl.Model = null,
    lod: ?rl.Model = null,
    steps: [2]u16 = .{ 0, 0 },
    step_err: [2]f32 = .{ 0, 0 },
    all: []rl.Matrix = &.{},
    spots: []Vec3 = &.{},
    visible: []rl.Matrix = &.{},
    count: usize = 0,
    vbo: c_uint = 0,
    cells: []Cell = &.{},
    size: f32 = 0,
    extent: f32 = 0,
};

const Cell = struct {
    start: u32,
    count: u32,
    center: Vec3,
    radius: f32,
    bound: Vec3,
    bound_radius: f32,
};

const cell_size: f32 = 32;
const min_pixels: f32 = 5;
pub var lod_pixels: f32 = 100;
pub var lod_tolerance: f32 = 1;

var step_pool: [kind_count * 2]rl.Model = undefined;
var step_used: usize = 0;

pub var tri_count: [kind_count]u64 = @splat(0);

fn modelTris(m: rl.Model) u64 {
    var t: u64 = 0;

    for (m.meshes[0..@intCast(m.meshCount)]) |me| t += @intCast(me.triangleCount);

    return t;
}

pub fn dumpTris() void {
    var order: [kind_count]usize = undefined;

    for (&order, 0..) |*o, i| o.* = i;

    std.mem.sort(usize, &order, {}, struct {
        fn less(_: void, a: usize, b: usize) bool {
            return tri_count[a] > tri_count[b];
        }
    }.less);

    var total: u64 = 0;

    for (tri_count) |t| total += t;

    std.debug.print("props tris total {d}\n", .{total});

    for (order[0..12]) |k| std.debug.print("  {s} {d}\n", .{ props.info(@fromBackingInt(@intCast(k))).file, tri_count[k] });
}

fn cellKey(p: Vec3) i64 {
    const cx: i64 = @intFromFloat(@floor(p.x / cell_size));
    const cz: i64 = @intFromFloat(@floor(p.z / cell_size));

    return (cz + 4096) * 8192 + (cx + 4096);
}

fn buildCells(gpa: std.mem.Allocator, slot: *Slot, scales: []const f32) void {
    const n = slot.count;

    if (n == 0) return;

    const order = gpa.alloc(u32, n) catch return;

    defer gpa.free(order);

    for (order, 0..) |*o, i| o.* = @intCast(i);

    const Ctx = struct {
        spots: []const Vec3,

        fn less(ctx: @This(), a: u32, b: u32) bool {
            return cellKey(ctx.spots[a]) < cellKey(ctx.spots[b]);
        }
    };

    std.mem.sort(u32, order, Ctx{ .spots = slot.spots[0..n] }, Ctx.less);

    const all = gpa.dupe(rl.Matrix, slot.all[0..n]) catch return;
    const spots = gpa.dupe(Vec3, slot.spots[0..n]) catch return;

    defer gpa.free(all);
    defer gpa.free(spots);

    var max_scale: f32 = 0;

    for (order, 0..) |o, i| {
        slot.all[i] = all[o];
        slot.spots[i] = spots[o];
        max_scale = @max(max_scale, scales[o]);
    }

    const margin = slot.extent * max_scale;

    slot.size = margin;
    var cells: std.ArrayList(Cell) = .empty;
    var i: usize = 0;

    while (i < n) {
        const key = cellKey(slot.spots[i]);
        var j = i;
        var lo_y: f32 = 1e9;
        var hi_y: f32 = -1e9;
        var lo_x: f32 = 1e9;
        var hi_x: f32 = -1e9;
        var lo_z: f32 = 1e9;
        var hi_z: f32 = -1e9;

        while (j < n and cellKey(slot.spots[j]) == key) : (j += 1) {
            lo_x = @min(lo_x, slot.spots[j].x);
            hi_x = @max(hi_x, slot.spots[j].x);
            lo_y = @min(lo_y, slot.spots[j].y);
            hi_y = @max(hi_y, slot.spots[j].y);
            lo_z = @min(lo_z, slot.spots[j].z);
            hi_z = @max(hi_z, slot.spots[j].z);
        }

        const cx = (@floor(slot.spots[i].x / cell_size) + 0.5) * cell_size;
        const cz = (@floor(slot.spots[i].z / cell_size) + 0.5) * cell_size;
        const half_y = (hi_y - lo_y) / 2;
        const half_x = (hi_x - lo_x) / 2;
        const half_z = (hi_z - lo_z) / 2;
        const center: Vec3 = .{ .x = cx, .y = (lo_y + hi_y) / 2, .z = cz };
        const radius = @sqrt(cell_size * cell_size / 2 + half_y * half_y) + margin;
        const bound: Vec3 = .{ .x = (lo_x + hi_x) / 2, .y = center.y, .z = (lo_z + hi_z) / 2 };
        const bound_radius = @sqrt(half_x * half_x + half_y * half_y + half_z * half_z) + margin;

        cells.append(gpa, .{
            .start = @intCast(i),
            .count = @intCast(j - i),
            .center = center,
            .radius = radius,
            .bound = bound,
            .bound_radius = bound_radius,
        }) catch return;
        i = j;
    }

    slot.cells = cells.toOwnedSlice(gpa) catch &.{};
}

fn loadSteps(slot: *Slot, dir: []const u8, stem: []const u8, file: []const u8) void {
    var buf: [512]u8 = undefined;
    const errs_path = std.fmt.bufPrintSentinel(&buf, "{s}/{s}.lods", .{ dir, stem }, 0) catch return;

    if (!assets.exists(errs_path)) return;

    const text = rl.LoadFileText(errs_path.ptr);

    if (text == null) return;

    defer rl.UnloadFileText(text);

    var it = std.mem.tokenizeAny(u8, std.mem.sliceTo(text, 0), " \n");
    var k: usize = 0;

    while (it.next()) |tok| : (k += 1) {
        if (k >= slot.steps.len) break;

        const err = std.fmt.parseFloat(f32, tok) catch break;
        var path_buf: [512]u8 = undefined;
        const path = std.fmt.bufPrintSentinel(&path_buf, "{s}/{s}.lod{d}.glb", .{ dir, stem, k + 1 }, 0) catch break;

        if (!assets.exists(path)) break;

        const model = rl.LoadModel(path.ptr);

        if (model.meshCount == 0) break;

        if (step_used == step_pool.len) break;

        tint(model, file);
        mesh.dropCpu(model);
        step_pool[step_used] = model;
        step_used += 1;
        slot.steps[k] = @intCast(step_used);
        slot.step_err[k] = err;
    }
}

fn pickLevel(slot: *const Slot, flat: f32, lod_from: f32) usize {
    if (flat >= lod_from) return 3;

    const scale = slot.size / @max(slot.extent, 0.001);
    const allowed = @max(flat, 0) * gfx.pixelAngle() * lod_tolerance;
    var level: usize = 0;

    for (slot.steps, slot.step_err, 0..) |step, err, k| {
        if (step != 0 and err * scale <= allowed) level = k + 1;
    }

    return level;
}

fn levelModel(slot: *const Slot, model: rl.Model, level: usize) ?rl.Model {
    return switch (level) {
        0 => model,
        1, 2 => if (slot.steps[level - 1] == 0) null else step_pool[slot.steps[level - 1] - 1],
        else => slot.lod,
    };
}

const deep_footing: f32 = -10;

fn drawnLate(i: usize) bool {
    return props.info(@fromBackingInt(@intCast(i))).min[1] < deep_footing;
}

fn dropModel(model: rl.Model) void {
    for (model.materials[0..@intCast(model.materialCount)]) |m| {
        for (m.maps[0..11]) |map| {
            if (map.texture.id > 0 and map.texture.id != rlgl.rlGetTextureIdDefault()) rl.UnloadTexture(map.texture);
        }
    }

    rl.UnloadModel(model);
}

pub const Props = struct {
    slots: [kind_count]Slot = @splat(.{}),

    pub fn unload(p: *Props, gpa: std.mem.Allocator) void {
        for (&p.slots) |*slot| {
            if (slot.model) |m| dropModel(m);

            if (slot.lod) |m| dropModel(m);

            if (slot.vbo != 0) rlgl.rlUnloadVertexBuffer(slot.vbo);

            gpa.free(slot.all);
            gpa.free(slot.spots);
            gpa.free(slot.visible);
            gpa.free(slot.cells);
            slot.* = .{};
        }

        for (step_pool[0..step_used]) |m| dropModel(m);

        step_used = 0;
    }

    pub fn load(gpa: std.mem.Allocator, dir: []const u8) Props {
        step_used = 0;

        var p: Props = .{};
        var counts: [kind_count]usize = @splat(0);

        for (world.placements) |pl| counts[@backingInt(pl.kind)] += 1;

        for (&p.slots, 0..) |*slot, i| {
            if (counts[i] == 0) continue;

            var buf: [512]u8 = undefined;
            const path = std.fmt.bufPrintSentinel(&buf, "{s}/{s}", .{ dir, props.info(@fromBackingInt(@intCast(i))).file }, 0) catch continue;
            const model = rl.LoadModel(path.ptr);

            if (model.meshCount == 0) continue;

            const file = props.info(@fromBackingInt(@intCast(i))).file;

            if (std.mem.endsWith(u8, std.mem.sliceTo(file, 0), ".glb")) {
                var lod_buf: [512]u8 = undefined;
                const name = std.mem.sliceTo(file, 0);
                const lod_path = std.fmt.bufPrintSentinel(&lod_buf, "{s}/{s}.lod.glb", .{ dir, name[0 .. name.len - 4] }, 0) catch "";

                loadSteps(slot, dir, name[0 .. name.len - 4], std.mem.sliceTo(file, 0));

                if (lod_path.len > 0 and assets.exists(lod_path)) {
                    const lod = rl.LoadModel(lod_path.ptr);

                    if (lod.meshCount > 0) {
                        tint(lod, std.mem.sliceTo(file, 0));
                        mesh.dropCpu(lod);
                        slot.lod = lod;
                    }
                }
            }

            tint(model, std.mem.sliceTo(props.info(@fromBackingInt(@intCast(i))).file, 0));

            const box = rl.GetModelBoundingBox(model);

            slot.extent = (Vec3{ .x = @max(@abs(box.min.x), @abs(box.max.x)), .y = @max(@abs(box.min.y), @abs(box.max.y)), .z = @max(@abs(box.min.z), @abs(box.max.z)) }).length();
            mesh.dropCpu(model);
            slot.model = model;
            slot.all = gpa.alloc(rl.Matrix, counts[i]) catch continue;
            slot.spots = gpa.alloc(Vec3, counts[i]) catch continue;
            slot.visible = gpa.alloc(rl.Matrix, counts[i]) catch continue;
            slot.count = 0;
        }

        var scales: [kind_count][]f32 = @splat(&.{});

        for (&p.slots, 0..) |*slot, i| {
            if (slot.model != null) scales[i] = gpa.alloc(f32, slot.all.len) catch &.{};
        }

        for (world.placements) |pl| {
            const k = @backingInt(pl.kind);
            const slot = &p.slots[k];

            if (slot.model == null or slot.count >= slot.all.len) continue;

            slot.all[slot.count] = mesh.transform(pl.pos, mesh.Basis.yawed(pl.yaw), pl.scale);
            slot.spots[slot.count] = pl.pos;

            if (slot.count < scales[k].len) scales[k][slot.count] = pl.scale;

            slot.count += 1;
        }

        for (&p.slots, 0..) |*slot, i| {
            if (slot.model == null or glassy(i)) continue;

            buildCells(gpa, slot, scales[i]);
        }

        for (scales) |sc| gpa.free(sc);

        return p;
    }

    fn reach(group: props.Group, shadow: bool) f32 {
        const base: f32 = switch (group) {
            .ground => 55,
            .bush => 90,
            .rock => 220,
            .street => 160,
            else => 1000,
        };

        return if (shadow) @min(base, if (group == .bush) @as(f32, 30) else @as(f32, 75)) else base;
    }

    fn glassy(i: usize) bool {
        return std.mem.startsWith(u8, props.info(@fromBackingInt(@intCast(i))).file, "prism/glass_pane");
    }

    pub fn drawGlass(p: *Props, r: *gfx.Renderer, eye: Vec3, forward: Vec3) void {
        if (r.phase == .shadow) return;

        r.setGlass(0.22);
        p.drawWhere(r, eye, forward, true, false);
        r.setGlass(0);
    }

    pub fn draw(p: *Props, r: *gfx.Renderer, eye: Vec3, forward: Vec3) void {
        p.drawWhere(r, eye, forward, false, false);
    }

    pub fn drawFootings(p: *Props, r: *gfx.Renderer, eye: Vec3, forward: Vec3) void {
        p.drawWhere(r, eye, forward, false, true);
    }

    fn drawWhere(p: *Props, r: *gfx.Renderer, eye: Vec3, forward: Vec3, glass: bool, late: bool) void {
        const shadow = r.phase == .shadow;

        for (&p.slots, 0..) |*slot, i| {
            const model = slot.model orelse continue;
            const info = props.info(@fromBackingInt(@intCast(i)));

            if (glassy(i) != glass or (!glass and drawnLate(i) != late)) continue;
            const limit = reach(info.group, shadow) * (if (shadow) @min(settings.view_dist, 1) else settings.view_dist);
            const limit2 = limit * limit;
            var n: usize = 0;

            if (shadow and (info.group == .road or info.group == .ground)) continue;

            if (!glass and !shadow) {
                if (slot.vbo == 0) slot.vbo = gfx.uploadStatic(slot.all[0..slot.count]);

                r.setSway(switch (info.group) {
                    .tree => 1.0,
                    .bush => 0.8,
                    .ground => 0.6,
                    else => 0,
                });
                r.setMatId(kitMaterial(i));

                const pixel_limit = gfx.pixelAngle() * min_pixels;
                const lod_from = if (slot.lod != null) slot.size / (gfx.pixelAngle() * lod_pixels) else 1e9;

                var levels: [512]u8 = undefined;
                const cells = slot.cells[0..@min(slot.cells.len, levels.len)];

                tri_count[i] = 0;

                for (cells, 0..) |c, ci| {
                    const d = c.center.sub(eye);
                    const flat = @sqrt(d.x * d.x + d.z * d.z) - c.radius;

                    levels[ci] = 255;

                    if (flat < limit and slot.size > pixel_limit * @max(flat, 1) and gfx.sphereVisible(c.bound, c.bound_radius) and pvs.visible(eye, c.bound, c.bound_radius)) {
                        const level = pickLevel(slot, flat, lod_from);

                        levels[ci] = @intCast(level);
                        tri_count[i] += c.count * modelTris(levelModel(slot, model, level) orelse model);
                    }
                }

                for (0..4) |level| {
                    const m = levelModel(slot, model, level) orelse continue;
                    var run_start: usize = 0;
                    var run_len: usize = 0;

                    for (cells, 0..) |c, ci| {
                        if (levels[ci] != level) continue;

                        if (run_len > 0 and run_start + run_len == c.start) {
                            run_len += c.count;
                        } else {
                            r.drawStaticRange(m, slot.vbo, run_start, run_len, info.foliage);
                            run_start = c.start;
                            run_len = c.count;
                        }
                    }

                    r.drawStaticRange(m, slot.vbo, run_start, run_len, info.foliage);
                }

                r.setMatId(-1);

                continue;
            }

            for (slot.spots[0..slot.count], 0..) |spot, k| {
                if (glass and world.paneBroken(spot)) continue;

                const d = spot.sub(eye);
                const flat2 = d.x * d.x + d.z * d.z;

                if (flat2 > limit2) continue;

                if (!shadow and flat2 > 400) {
                    const len = @sqrt(flat2 + d.y * d.y);

                    if (d.dot(forward) < -len * 0.35 - 12) continue;
                }

                slot.visible[n] = slot.all[k];
                n += 1;
            }

            r.setSway(switch (info.group) {
                .tree => 1.0,
                .bush => 0.8,
                .ground => 0.6,
                else => 0,
            });
            r.setMatId(kitMaterial(i));
            r.drawInstanced(model, slot.visible[0..n], info.foliage or glass);
            r.setMatId(-1);
        }
    }
};

const KitMat = struct { prefix: []const u8, side: u8, top: u8 };

const kit_mats = [_]KitMat{
    .{ .prefix = "iv_hut", .side = 8, .top = 19 },
    .{ .prefix = "iv_hay", .side = 19, .top = 19 },
    .{ .prefix = "iv_compound", .side = 2, .top = 2 },
    .{ .prefix = "vl_house", .side = 4, .top = 7 },
    .{ .prefix = "iv_dock", .side = 8, .top = 8 },
    .{ .prefix = "iv_boardwalk", .side = 8, .top = 8 },
    .{ .prefix = "mil_barracks", .side = 11, .top = 11 },
    .{ .prefix = "mil_comms", .side = 10, .top = 12 },
    .{ .prefix = "mil_hangar_doors", .side = 11, .top = 11 },
    .{ .prefix = "sv_shop", .side = 0, .top = 12 },
    .{ .prefix = "sv_shed", .side = 11, .top = 11 },
    .{ .prefix = "sv_watertower", .side = 10, .top = 10 },
    .{ .prefix = "sv_fuel", .side = 12, .top = 12 },
    .{ .prefix = "fc_office", .side = 12, .top = 12 },
    .{ .prefix = "fc_workshop", .side = 11, .top = 11 },
    .{ .prefix = "fc_pipebridge", .side = 10, .top = 10 },
    .{ .prefix = "vl_paving", .side = 6, .top = 6 },
    .{ .prefix = "vl_fountain", .side = 4, .top = 4 },
    .{ .prefix = "iv_tower", .side = 2, .top = 2 },
    .{ .prefix = "iv_gate", .side = 2, .top = 2 },
    .{ .prefix = "iv_landmark", .side = 2, .top = 7 },
    .{ .prefix = "iv_bridge", .side = 8, .top = 8 },
    .{ .prefix = "iv_platform", .side = 8, .top = 8 },
    .{ .prefix = "iv_stall", .side = 8, .top = 8 },
    .{ .prefix = "iv_cart", .side = 8, .top = 8 },
    .{ .prefix = "iv_fence", .side = 8, .top = 8 },
    .{ .prefix = "iv_logs", .side = 8, .top = 8 },
    .{ .prefix = "iv_ruin", .side = 4, .top = 4 },
    .{ .prefix = "iv_terrace", .side = 4, .top = 16 },
    .{ .prefix = "iv_cliff", .side = 17, .top = 17 },
    .{ .prefix = "iv_ridge", .side = 17, .top = 17 },
    .{ .prefix = "iv_range", .side = 17, .top = 18 },
    .{ .prefix = "iv_rock", .side = 17, .top = 17 },
    .{ .prefix = "iv_under", .side = 17, .top = 15 },
    .{ .prefix = "mil_container", .side = 11, .top = 11 },
    .{ .prefix = "mil_hesco", .side = 11, .top = 16 },
    .{ .prefix = "mil_bunker", .side = 12, .top = 12 },
    .{ .prefix = "mil_trench", .side = 12, .top = 16 },
    .{ .prefix = "mil_checkpoint", .side = 12, .top = 12 },
    .{ .prefix = "mil_kerb", .side = 12, .top = 12 },
    .{ .prefix = "mil_barrier", .side = 12, .top = 12 },
    .{ .prefix = "mil_office", .side = 12, .top = 12 },
    .{ .prefix = "mil_warehouse", .side = 11, .top = 11 },
    .{ .prefix = "mil_quonset", .side = 11, .top = 11 },
    .{ .prefix = "mil_workshop", .side = 11, .top = 11 },
    .{ .prefix = "hangar_", .side = 11, .top = 11 },
    .{ .prefix = "mil_watchtower", .side = 8, .top = 11 },
    .{ .prefix = "mil_pallets", .side = 8, .top = 8 },
    .{ .prefix = "mil_powerpole", .side = 8, .top = 8 },
    .{ .prefix = "mil_fueltank", .side = 10, .top = 10 },
    .{ .prefix = "mil_pipe_rack", .side = 10, .top = 10 },
    .{ .prefix = "mil_generator", .side = 10, .top = 10 },
    .{ .prefix = "mil_forklift", .side = 10, .top = 10 },
    .{ .prefix = "mil_drums", .side = 10, .top = 10 },
    .{ .prefix = "mil_cable_drum", .side = 8, .top = 8 },
    .{ .prefix = "mil_light_tower", .side = 10, .top = 10 },
    .{ .prefix = "mil_mast", .side = 10, .top = 10 },
    .{ .prefix = "mil_rock", .side = 17, .top = 17 },
    .{ .prefix = "mil_outcrop", .side = 17, .top = 17 },
};

fn kitMaterial(i: usize) f32 {
    if (i >= props.named_kinds) return -1;

    const name = @tagName(@as(props.Kind, @fromBackingInt(@intCast(i))));

    for (kit_mats) |k| {
        if (std.mem.startsWith(u8, name, k.prefix)) return @floatFromInt(@as(u32, k.side) * 32 + k.top);
    }

    return -1;
}

fn tint(model: rl.Model, file: []const u8) void {
    const leaf: ?rl.Color = if (std.mem.indexOf(u8, file, "Pine") != null)
        .{ .r = 150, .g = 178, .b = 128, .a = 255 }
    else if (std.mem.indexOf(u8, file, "CommonTree") != null)
        .{ .r = 170, .g = 190, .b = 140, .a = 255 }
    else
        null;
    const plant: ?rl.Color = if (std.mem.indexOf(u8, file, "Grass") != null)
        .{ .r = 125, .g = 172, .b = 72, .a = 255 }
    else if (std.mem.indexOf(u8, file, "Fern") != null or std.mem.indexOf(u8, file, "Plant") != null)
        .{ .r = 120, .g = 160, .b = 80, .a = 255 }
    else
        null;
    const mats = model.materials[0..@intCast(model.materialCount)];

    if (shared.terrain.current == .desert and std.mem.indexOf(u8, file, "Rock") != null) {
        for (mats) |*m| m.maps[0].color = .{ .r = 222, .g = 188, .b = 146, .a = 255 };
    }

    if (std.mem.indexOf(u8, file, "Desertjar") != null) {
        for (mats, 0..) |*m, i| m.maps[0].color = if (i % 2 == 0) .{ .r = 196, .g = 112, .b = 70, .a = 255 } else .{ .r = 150, .g = 82, .b = 52, .a = 255 };
    }

    if (std.mem.indexOf(u8, file, "Cactus") != null) {
        for (mats) |*m| m.maps[0].color = .{ .r = 176, .g = 196, .b = 150, .a = 255 };
    }

    if (std.mem.indexOf(u8, file, "Brickwall") != null or std.mem.indexOf(u8, file, "Monument") != null) {
        for (mats) |*m| m.maps[0].color = .{ .r = 255, .g = 214, .b = 170, .a = 255 };
    }

    if (leaf) |c| {
        if (mats.len > 2) mats[2].maps[0].color = c;
    }

    if (plant) |c| {
        for (mats[1..]) |*m| m.maps[0].color = c;
    }
}
