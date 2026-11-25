const std = @import("std");
const rl = @import("raylib");
const rlgl = @import("rlgl");
const shared = @import("shared");
const gunart = @import("gunart.zig");
const models_mod = @import("models.zig");
const mesh = @import("mesh.zig");
const assets = @import("assets.zig");

const weapons = shared.weapons;
const Vec3 = shared.math.Vec3;

pub const icon_w: c_int = 384;
pub const icon_h: c_int = 192;
pub const live_w: c_int = 960;
pub const live_h: c_int = 480;

const vs_src =
    \\#version 330
    \\in vec3 vertexPosition;
    \\in vec2 vertexTexCoord;
    \\in vec3 vertexNormal;
    \\in vec4 vertexColor;
    \\uniform mat4 mvp;
    \\uniform mat4 matNormal;
    \\out vec2 uv;
    \\out vec3 nrm;
    \\out vec4 tint;
    \\void main() {
    \\    uv = vertexTexCoord;
    \\    nrm = normalize(vec3(matNormal * vec4(vertexNormal, 0.0)));
    \\    tint = vertexColor;
    \\    gl_Position = mvp * vec4(vertexPosition, 1.0);
    \\}
;

const fs_src =
    \\#version 330
    \\in vec2 uv;
    \\in vec3 nrm;
    \\in vec4 tint;
    \\uniform sampler2D texture0;
    \\uniform vec4 colDiffuse;
    \\uniform vec3 viewDir;
    \\uniform vec3 rimColor;
    \\out vec4 finalColor;
    \\void main() {
    \\    vec4 tex = texture(texture0, uv);
    \\    if (tex.a * colDiffuse.a < 0.3) discard;
    \\    vec3 base = tex.rgb * colDiffuse.rgb * tint.rgb;
    \\    vec3 n = normalize(nrm);
    \\    if (dot(n, viewDir) > 0.0) n = -n;
    \\    vec3 key = normalize(vec3(0.45, 0.8, 0.4));
    \\    vec3 fill = normalize(vec3(-0.6, 0.2, -0.5));
    \\    float k = max(dot(n, key), 0.0);
    \\    float f = max(dot(n, fill), 0.0);
    \\    float sky = n.y * 0.5 + 0.5;
    \\    vec3 h = normalize(key - viewDir);
    \\    float spec = pow(max(dot(n, h), 0.0), 28.0) * 0.35;
    \\    float rim = pow(1.0 - max(dot(n, -viewDir), 0.0), 3.0);
    \\    vec3 lift = max(base, vec3(0.06));
    \\    vec3 col = lift * (0.38 + 0.22 * sky + 0.95 * k + 0.28 * f) + spec + rimColor * rim * 0.75;
    \\    col = col / (col + vec3(0.85)) * 1.75;
    \\    finalColor = vec4(pow(clamp(col, 0.0, 1.0), vec3(0.92)), 1.0);
    \\}
;

fn esSource(comptime src: [:0]const u8) [:0]const u8 {
    const head = "#version 330";

    return "#version 300 es\nprecision highp float;\nprecision highp sampler2D;" ++ src[head.len..];
}

pub const Icons = struct {
    tex: [weapons.count]rl.RenderTexture2D,
    live: rl.RenderTexture2D,
    shader: rl.Shader,
    view_loc: c_int,
    rim_loc: c_int,
    arts: *const [weapons.count]gunart.Art,
    models: *const models_mod.Models,

    pub fn build(arts: *const [weapons.count]gunart.Art, models: *const models_mod.Models) Icons {
        const sh = if (assets.mobile) rl.LoadShaderFromMemory(comptime esSource(vs_src), comptime esSource(fs_src)) else rl.LoadShaderFromMemory(vs_src, fs_src);
        var icons: Icons = .{
            .tex = undefined,
            .live = rl.LoadRenderTexture(live_w, live_h),
            .shader = sh,
            .view_loc = rl.GetShaderLocation(sh, "viewDir"),
            .rim_loc = rl.GetShaderLocation(sh, "rimColor"),
            .arts = arts,
            .models = models,
        };

        rl.SetTextureFilter(icons.live.texture, rl.TEXTURE_FILTER_BILINEAR);

        for (&icons.tex, 0..) |*t, i| {
            t.* = rl.LoadRenderTexture(icon_w, icon_h);
            rl.SetTextureFilter(t.texture, rl.TEXTURE_FILTER_BILINEAR);
            icons.render(t.*, @intCast(i), 0.42, 0.18, .{ 0.75, 0.8, 0.9 });
        }

        return icons;
    }

    pub fn renderLive(icons: *const Icons, weapon: u8, yaw: f32, rim: [3]f32) void {
        icons.render(icons.live, weapon, yaw, 0.2, rim);
    }

    fn render(icons: *const Icons, target: rl.RenderTexture2D, weapon: u8, yaw: f32, pitch: f32, rim: [3]f32) void {
        const art = icons.arts[weapon];
        const forward = Vec3{ .x = -@cos(yaw) * @cos(pitch), .y = -@sin(pitch), .z = @sin(yaw) * @cos(pitch) };
        const right = forward.cross(Vec3{ .y = 1 }).normalize();
        const up = right.cross(forward).normalize();
        var lo = [2]f32{ 1e9, 1e9 };
        var hi = [2]f32{ -1e9, -1e9 };
        var center = Vec3{};

        if (art.box) |box| {

            center = .{ .x = (box.min.x + box.max.x) / 2, .y = (box.min.y + box.max.y) / 2, .z = (box.min.z + box.max.z) / 2 };

            for (0..8) |c| {
                const p = Vec3{ .x = if (c & 1 != 0) box.max.x else box.min.x, .y = if (c & 2 != 0) box.max.y else box.min.y, .z = if (c & 4 != 0) box.max.z else box.min.z };
                const d = p.sub(center);
                const px = d.dot(right);
                const py = d.dot(up);

                lo = .{ @min(lo[0], px), @min(lo[1], py) };
                hi = .{ @max(hi[0], px), @max(hi[1], py) };
            }
        } else {
            const s = weapons.specs[weapon];
            const reach = @max(0.25, s.reach() + s.look.stock + 0.1);

            center = .{ .z = -s.look.barrel * 0.5 };
            lo = .{ -reach * 0.55, -reach * 0.2 };
            hi = .{ reach * 0.55, reach * 0.2 };
        }

        const aspect = @as(f32, @floatFromInt(target.texture.width)) / @as(f32, @floatFromInt(target.texture.height));
        const span = @max(hi[1] - lo[1], (hi[0] - lo[0]) / aspect) * 1.12;
        const aim = center.add(right.scale((lo[0] + hi[0]) / 2)).add(up.scale((lo[1] + hi[1]) / 2));
        const eye = aim.sub(forward.scale(6));
        const cam: rl.Camera3D = .{
            .position = .{ .x = eye.x, .y = eye.y, .z = eye.z },
            .target = .{ .x = aim.x, .y = aim.y, .z = aim.z },
            .up = .{ .x = up.x, .y = up.y, .z = up.z },
            .fovy = span,
            .projection = rl.CAMERA_ORTHOGRAPHIC,
        };
        const vd = [3]f32{ forward.x, forward.y, forward.z };

        rl.SetShaderValue(icons.shader, icons.view_loc, &vd, rl.SHADER_UNIFORM_VEC3);
        rl.SetShaderValue(icons.shader, icons.rim_loc, &rim, rl.SHADER_UNIFORM_VEC3);
        rl.BeginTextureMode(target);
        rl.ClearBackground(.{ .r = 0, .g = 0, .b = 0, .a = 0 });
        rl.BeginMode3D(cam);
        rlgl.rlEnableDepthTest();
        rlgl.rlDisableBackfaceCulling();

        if (art.body) |body| {
            icons.drawLit(body, mesh.identity);

            if (art.extra) |extra| icons.drawLit(extra.model, mesh.transform(extra.offset, mesh.Basis.world, 1));

            if (art.tips) |t| {
                if (gunart.string) |sm| icons.drawLit(sm, mesh.segment(.{ .y = t[0], .z = t[1] }, .{ .y = -t[0], .z = t[1] }, 0.0022));
            }
        } else {
            var m = rl.LoadMaterialDefault();

            m.shader = icons.shader;
            m.maps[0].color = .{ .r = 90, .g = 96, .b = 104, .a = 255 };
            rl.DrawMesh(icons.models.guns[weapon], m, mesh.identity);
        }

        rlgl.rlDrawRenderBatchActive();
        rlgl.rlEnableBackfaceCulling();
        rl.EndMode3D();
        rl.EndTextureMode();
    }

    fn drawLit(icons: *const Icons, model: rl.Model, transform: rl.Matrix) void {
        var k: usize = 0;

        while (k < @as(usize, @intCast(model.meshCount))) : (k += 1) {
            var m = model.materials[@intCast(model.meshMaterial[k])];

            m.shader = icons.shader;
            rl.DrawMesh(model.meshes[k], m, transform);
        }
    }
};

pub fn power(s: weapons.Spec, rarity: u8) u32 {
    const dmg = s.damage * @as(f32, @floatFromInt(@max(s.pellets, 1))) * weapons.rarity_damage[rarity];
    const rate = 1 / @max(s.interval, 0.01);
    const v = dmg * @sqrt(@min(rate, 25)) * 12;

    return @intFromFloat(std.math.clamp(v, 60, 1999));
}
