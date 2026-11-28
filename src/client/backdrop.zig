const std = @import("std");
const rl = @import("raylib");
const shared = @import("shared");
const gfx = @import("gfx.zig");
const models = @import("models.zig");
const propart = @import("propart.zig");
const render = @import("render.zig");
const assets = @import("assets.zig");
const theme = @import("theme.zig");
const mesh = @import("mesh.zig");
const game = @import("main.zig");

const Map = shared.terrain.Map;
const Vec3 = shared.math.Vec3;

const map: Map = .coast;
const haze: rl.Color = .{ .r = 150, .g = 196, .b = 218, .a = 255 };
const focus: Vec3 = .{ .x = -4, .y = 4, .z = -8 };

const Stage = enum { idle, world, scenery, renderer, props, ready };

var stage: Stage = .idle;
var thread: ?std.Thread = null;
var built = std.atomic.Value(bool).init(false);
var set: models.Scenery = undefined;
var renderer: gfx.Renderer = undefined;
var pristine: gfx.Renderer = undefined;
var props: propart.Props = .{};
var previous: Map = .facility;
var facet: f32 = 0;
var clock: f32 = 0;
var wait: f32 = 0;
var shown: f32 = 0;

fn worker() void {
    shared.world.build(std.heap.page_allocator);
    built.store(true, .release);
}

pub fn name() [:0]const u8 {
    return if (shared.maps.get(map)) |d| d.name else "";
}

pub fn begin() void {
    if (stage != .idle or std.c.getenv("DF_NOBACKDROP") != null) return;

    previous = shared.terrain.current;
    facet = shared.terrain.facet;
    shared.terrain.current = map;
    shared.terrain.configure();
    built.store(false, .release);
    thread = std.Thread.spawn(.{}, worker, .{}) catch null;

    if (thread == null) worker();

    stage = .world;
    wait = 0.7;
    shown = 0;
}

pub fn step() void {
    if (wait > 0) return;

    switch (stage) {
        .idle, .ready => {},
        .world => {
            if (!built.load(.acquire)) return;

            join();
            stage = .scenery;
        },
        .scenery => {
            set = models.buildScenery();
            models.buildGroundMap();
            stage = .renderer;
        },
        .renderer => {
            var sky: [1024]u8 = undefined;
            var ground: [1024]u8 = undefined;

            renderer = gfx.Renderer.init(assets.file(&sky, "sky/sky.hdr"), set.sky);
            renderer.loadGround(assets.dir(&ground, "textures"));
            pristine = renderer;
            renderer.setGroundMap(models.ground_map, models.ground_extent);

            if (shared.maps.current()) |d| renderer.applyPalette(d.palette);

            renderer.shadows_on = false;
            renderer.post = false;

            for (0..renderer.cascades) |cascade| {
                renderer.beginShadow(focus, cascade);
                renderer.endShadow();
            }

            stage = .props;
        },
        .props => {
            var dir: [1024]u8 = undefined;

            props = propart.Props.load(std.heap.page_allocator, assets.dir(&dir, "props"));
            mesh.releaseScratch();
            stage = .ready;
        },
    }

    wait = 0.02;
}

fn view() render.Panorama {
    const t = if (std.c.getenv("DF_MENUTIME")) |v| std.fmt.parseFloat(f32, std.mem.sliceTo(v, 0)) catch clock else clock;
    const angle = 0.5 + 0.17 * @sin(t * std.math.tau / 76);
    const reach = 65 + 4 * @sin(t * std.math.tau / 54);
    const rise = 12.5 + 1.4 * @sin(t * std.math.tau / 43 + 1);
    const eye: Vec3 = .{ .x = focus.x - @sin(angle) * reach, .y = rise, .z = focus.z - @cos(angle) * reach };
    const yaw = angle + 0.17;
    const pitch: f32 = -0.085;
    const forward: Vec3 = .{ .x = @sin(yaw) * @cos(pitch), .y = @sin(pitch), .z = @cos(yaw) * @cos(pitch) };
    const right = forward.cross(shared.math.up).normalize();

    return .{ .eye = eye, .forward = forward, .right = right, .up = right.cross(forward), .muzzle = eye };
}

pub fn draw(dt: f32) void {
    wait -= dt;
    rl.ClearBackground(haze);

    if (stage != .ready) return;

    clock += @min(dt, 0.05);
    shown += @min(dt, 0.05);

    const v = view();
    const w: f32 = @floatFromInt(rl.GetScreenWidth());
    const h: f32 = @floatFromInt(rl.GetScreenHeight());
    const wide = std.math.degreesToRadians(@as(f32, 74));
    const fovy = std.math.radiansToDegrees(2 * std.math.atan(@tan(wide / 2) / @max(w / h, 1.55)));
    const at = v.eye.add(v.forward);
    const camera: rl.Camera3D = .{
        .position = .{ .x = v.eye.x, .y = v.eye.y, .z = v.eye.z },
        .target = .{ .x = at.x, .y = at.y, .z = at.z },
        .up = .{ .x = 0, .y = 1, .z = 0 },
        .fovy = fovy,
        .projection = rl.CAMERA_PERSPECTIVE,
    };

    renderer.begin(camera, clock);
    render.panorama(&renderer, set, &props, v);
    renderer.end();

    if (shown < 0.8) {
        const left = 1 - shown / 0.8;

        rl.DrawRectangle(0, 0, rl.GetScreenWidth(), rl.GetScreenHeight(), theme.fade(haze, left * left));
    }
}

var opened: f64 = 0;

pub fn open(dt: f32) void {
    opened = rl.GetTime();
    theme.begin(dt);
    rl.BeginDrawing();
    draw(dt);
}

pub fn close(dt: f32) void {
    const drawn = rl.GetTime();

    game.dropDepth(true);
    rl.EndDrawing();
    game.frameStats(dt, @floatCast(drawn - opened), @floatCast(rl.GetTime() - drawn));
    step();
}

fn join() void {
    if (thread) |t| t.join();

    thread = null;
}

pub fn finish() ?gfx.Renderer {
    if (stage == .idle) return null;

    const reached = @backingInt(stage);
    const gpa = std.heap.page_allocator;
    var out: ?gfx.Renderer = null;

    join();

    if (reached >= @backingInt(Stage.ready)) props.unload(gpa);

    if (reached >= @backingInt(Stage.props)) {
        out = pristine;
    }

    if (reached >= @backingInt(Stage.renderer)) models.dropScenery(set);

    mesh.releaseScratch();
    shared.world.reset(gpa);
    shared.terrain.current = previous;
    shared.terrain.facet = facet;
    stage = .idle;

    return out;
}
