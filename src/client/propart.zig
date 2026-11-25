const std = @import("std");
const rl = @import("raylib");
const shared = @import("shared");
const gfx = @import("gfx.zig");
const settings = @import("settings.zig");
const mesh = @import("mesh.zig");

const props = shared.props;
const world = shared.world;
const Vec3 = shared.math.Vec3;

const kind_count = @typeInfo(props.Kind).@"enum".field_names.len;

const Slot = struct {
    model: ?rl.Model = null,
    all: []rl.Matrix = &.{},
    spots: []Vec3 = &.{},
    visible: []rl.Matrix = &.{},
    count: usize = 0,
};

pub const Props = struct {
    slots: [kind_count]Slot = @splat(.{}),

    pub fn load(gpa: std.mem.Allocator, dir: []const u8) Props {
        var p: Props = .{};
        var counts: [kind_count]usize = @splat(0);

        for (world.placements) |pl| counts[@intFromEnum(pl.kind)] += 1;

        for (&p.slots, 0..) |*slot, i| {
            if (counts[i] == 0) continue;

            var buf: [512]u8 = undefined;
            const path = std.fmt.bufPrintSentinel(&buf, "{s}/{s}", .{ dir, props.infos[i].file }, 0) catch continue;
            const model = rl.LoadModel(path.ptr);

            if (model.meshCount == 0) continue;

            tint(model, std.mem.sliceTo(props.infos[i].file, 0));
            mesh.dropCpu(model);
            slot.model = model;
            slot.all = gpa.alloc(rl.Matrix, counts[i]) catch continue;
            slot.spots = gpa.alloc(Vec3, counts[i]) catch continue;
            slot.visible = gpa.alloc(rl.Matrix, counts[i]) catch continue;
            slot.count = 0;
        }

        for (world.placements) |pl| {
            const slot = &p.slots[@intFromEnum(pl.kind)];

            if (slot.model == null or slot.count >= slot.all.len) continue;

            slot.all[slot.count] = mesh.transform(pl.pos, mesh.Basis.yawed(pl.yaw), pl.scale);
            slot.spots[slot.count] = pl.pos;
            slot.count += 1;
        }

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
        return std.mem.startsWith(u8, props.infos[i].file, "prism/glass_pane");
    }

    pub fn drawGlass(p: *Props, r: *gfx.Renderer, eye: Vec3, forward: Vec3) void {
        if (r.phase == .shadow) return;

        r.setGlass(0.22);
        p.drawWhere(r, eye, forward, true);
        r.setGlass(0);
    }

    pub fn draw(p: *Props, r: *gfx.Renderer, eye: Vec3, forward: Vec3) void {
        p.drawWhere(r, eye, forward, false);
    }

    fn drawWhere(p: *Props, r: *gfx.Renderer, eye: Vec3, forward: Vec3, glass: bool) void {
        const shadow = r.phase == .shadow;

        for (&p.slots, 0..) |*slot, i| {
            const model = slot.model orelse continue;
            const info = props.infos[i];

            if (glassy(i) != glass) continue;
            const limit = reach(info.group, shadow) * (if (shadow) @min(settings.view_dist, 1) else settings.view_dist);
            const limit2 = limit * limit;
            var n: usize = 0;

            if (shadow and (info.group == .road or info.group == .ground)) continue;

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
    const name = @tagName(@as(props.Kind, @enumFromInt(i)));

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
