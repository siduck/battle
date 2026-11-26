const std = @import("std");
const rl = @import("raylib");
const rlgl = @import("rlgl");
const rm = @import("raymath");
const shared = @import("shared");
const assets = @import("assets.zig");

const Vec3 = shared.math.Vec3;

pub const near_plane: f32 = 0.08;
pub var sharpen_amount: f32 = 0.22;
pub var vm_near: f32 = 0.02;
pub const far_plane: f32 = 800;

pub var shadow_res: c_int = if (assets.mobile) 1024 else 2048;
const shadow_slot: c_int = 13;
const shadow_slot_far: c_int = 12;
const env_slot: c_int = 14;
const cloud_slot: c_int = 11;
var cloud_tex: c_uint = 0;
var cloud_loc: c_int = -2;
const mat_slot: c_int = 7;
const ground_detail_slot: c_int = 5;
const ground_map_slot: c_int = 6;
const shadow_span: f32 = if (assets.mobile) 60 else 40;
const shadow_span_far: f32 = 160;

extern fn glClear(mask: c_uint) callconv(.c) void;
extern fn glGenFramebuffers(n: c_int, ids: *c_uint) callconv(.c) void;
extern fn glDeleteFramebuffers(n: c_int, ids: *const c_uint) callconv(.c) void;
extern fn glBindFramebuffer(target: c_uint, id: c_uint) callconv(.c) void;
extern fn glGenRenderbuffers(n: c_int, ids: *c_uint) callconv(.c) void;
extern fn glDeleteRenderbuffers(n: c_int, ids: *const c_uint) callconv(.c) void;
extern fn glBindRenderbuffer(target: c_uint, id: c_uint) callconv(.c) void;
extern fn glRenderbufferStorageMultisample(target: c_uint, samples: c_int, format: c_uint, w: c_int, h: c_int) callconv(.c) void;
extern fn glFramebufferRenderbuffer(target: c_uint, attachment: c_uint, rb_target: c_uint, rb: c_uint) callconv(.c) void;
extern fn glBlitFramebuffer(sx0: c_int, sy0: c_int, sx1: c_int, sy1: c_int, dx0: c_int, dy0: c_int, dx1: c_int, dy1: c_int, mask: c_uint, filt: c_uint) callconv(.c) void;
extern fn glCheckFramebufferStatus(target: c_uint) callconv(.c) c_uint;
extern fn glGetError() callconv(.c) c_uint;
extern fn glTexImage2D(target: c_uint, level: c_int, internal: c_int, w: c_int, h: c_int, border: c_int, format: c_uint, kind: c_uint, data: ?*const anyopaque) callconv(.c) void;
extern fn glGenTextures(n: c_int, ids: *c_uint) callconv(.c) void;
extern fn glBindTexture(target: c_uint, id: c_uint) callconv(.c) void;
extern fn glTexParameteri(target: c_uint, name: c_uint, v: c_int) callconv(.c) void;
extern fn glFramebufferTexture2D(target: c_uint, attachment: c_uint, tex_target: c_uint, tex: c_uint, level: c_int) callconv(.c) void;

const gl_framebuffer: c_uint = 0x8D40;
const gl_read_framebuffer: c_uint = 0x8CA8;
const gl_draw_framebuffer: c_uint = 0x8CA9;
const gl_renderbuffer: c_uint = 0x8D41;
const gl_color_attachment0: c_uint = 0x8CE0;
const gl_depth_attachment: c_uint = 0x8D00;
const gl_rgba16f: c_uint = 0x881A;
const gl_depth_component24: c_uint = 0x81A6;
const gl_color_buffer_bit: c_uint = 0x4000;
const gl_nearest: c_uint = 0x2600;
const gl_framebuffer_complete: c_uint = 0x8CD5;
const gl_texture_2d: c_uint = 0x0DE1;
const gl_depth_component: c_uint = 0x1902;
const gl_unsigned_int: c_uint = 0x1405;

const gl_depth_buffer_bit: c_uint = 0x00000100;

const lit_vs =
    \\#version 330
    \\in vec3 vertexPosition;
    \\in vec3 vertexNormal;
    \\in vec4 vertexColor;
    \\in vec2 vertexTexCoord;
    \\in vec4 vertexBoneIndices;
    \\in vec4 vertexBoneWeights;
    \\uniform mat4 mvp;
    \\uniform mat4 matModel;
    \\uniform mat4 matNormal;
    \\uniform mat4 boneMatrices[56];
    \\uniform float skinned;
    \\out vec3 worldPos;
    \\out vec3 worldNormal;
    \\out float localY;
    \\centroid out vec4 tint;
    \\centroid out vec2 uv;
    \\void main() {
    \\    vec4 p = vec4(vertexPosition, 1.0);
    \\    vec3 n = vertexNormal;
    \\    if (skinned > 0.5) {
    \\        mat4 s = boneMatrices[int(vertexBoneIndices.x)] * vertexBoneWeights.x
    \\            + boneMatrices[int(vertexBoneIndices.y)] * vertexBoneWeights.y
    \\            + boneMatrices[int(vertexBoneIndices.z)] * vertexBoneWeights.z
    \\            + boneMatrices[int(vertexBoneIndices.w)] * vertexBoneWeights.w;
    \\        p = s * p;
    \\        n = mat3(s) * n;
    \\    }
    \\    uv = vertexTexCoord;
    \\    localY = 10.0;
    \\    worldPos = (matModel * p).xyz;
    \\    worldNormal = normalize(mat3(matNormal) * n);
    \\    tint = vertexColor;
    \\    gl_Position = mvp * p;
    \\}
;

const lit_inst_vs =
    \\#version 330
    \\in vec3 vertexPosition;
    \\in vec3 vertexNormal;
    \\in vec4 vertexColor;
    \\in vec2 vertexTexCoord;
    \\in mat4 instanceTransform;
    \\uniform mat4 mvp;
    \\uniform float sway;
    \\uniform float swayTime;
    \\out vec3 worldPos;
    \\out vec3 worldNormal;
    \\out float localY;
    \\centroid out vec4 tint;
    \\centroid out vec2 uv;
    \\void main() {
    \\    uv = vertexTexCoord;
    \\    localY = vertexPosition.y * length(instanceTransform[1].xyz);
    \\    vec4 wp = instanceTransform * vec4(vertexPosition, 1.0);
    \\    float bend = sway * max(vertexPosition.y, 0.0) * 0.014;
    \\    wp.xz += vec2(sin(swayTime * 1.3 + wp.x * 0.21 + wp.z * 0.17), cos(swayTime * 1.1 + wp.z * 0.19 - wp.x * 0.07)) * bend;
    \\    worldPos = wp.xyz;
    \\    worldNormal = normalize(mat3(instanceTransform) * vertexNormal);
    \\    tint = vertexColor;
    \\    gl_Position = mvp * wp;
    \\}
;

const depth_vs =
    \\#version 330
    \\in vec3 vertexPosition;
    \\in vec2 vertexTexCoord;
    \\uniform mat4 mvp;
    \\out vec2 uv;
    \\void main() {
    \\    uv = vertexTexCoord;
    \\    gl_Position = mvp * vec4(vertexPosition, 1.0);
    \\}
;

const depth_inst_vs =
    \\#version 330
    \\in vec3 vertexPosition;
    \\in vec2 vertexTexCoord;
    \\in mat4 instanceTransform;
    \\uniform mat4 mvp;
    \\out vec2 uv;
    \\void main() {
    \\    uv = vertexTexCoord;
    \\    gl_Position = mvp * instanceTransform * vec4(vertexPosition, 1.0);
    \\}
;

const depth_fs =
    \\#version 330
    \\in vec2 uv;
    \\uniform sampler2D texture0;
    \\uniform vec4 colDiffuse;
    \\out vec4 finalColor;
    \\void main() {
    \\    if (texture(texture0, uv).a * colDiffuse.a < 0.45) discard;
    \\    finalColor = vec4(1.0);
    \\}
;

const common_fs =
    \\const float PI = 3.14159265;
    \\uniform sampler2D envMap;
    \\uniform float envScale;
    \\uniform float exposure;
    \\uniform vec3 gradeTint;
    \\uniform float gradeSat;
    \\uniform float postFx;
    \\uniform vec3 fogColor;
    \\float dhash(vec2 p) {
    \\    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
    \\}
    \\float dnoise(vec2 p) {
    \\    vec2 i = floor(p);
    \\    vec2 f = fract(p);
    \\    vec2 u = f * f * (3.0 - 2.0 * f);
    \\    return mix(mix(dhash(i), dhash(i + vec2(1.0, 0.0)), u.x), mix(dhash(i + vec2(0.0, 1.0)), dhash(i + vec2(1.0, 1.0)), u.x), u.y);
    \\}
    \\vec2 dirUV(vec3 d) {
    \\    return vec2(atan(d.z, d.x) / (2.0 * PI) + 0.5, acos(clamp(d.y, -1.0, 1.0)) / PI);
    \\}
    \\vec3 env(vec3 d, float lod) {
    \\    d = normalize(d);
    \\    vec3 sky = textureLod(envMap, dirUV(vec3(d.x, max(d.y, 0.02), d.z)), lod).rgb * envScale;
    \\    vec3 ground = vec3(0.42, 0.38, 0.30) * envScale * 0.5;
    \\    return mix(ground, sky, smoothstep(-0.12, 0.04, d.y));
    \\}
    \\vec3 grade(vec3 c) {
    \\    if (postFx > 0.5) return c;
    \\    c *= exposure;
    \\    c = clamp((c * (2.51 * c + 0.03)) / (c * (2.43 * c + 0.59) + 0.14), 0.0, 1.0);
    \\    float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
    \\    float chroma = max(c.r, max(c.g, c.b)) - min(c.r, min(c.g, c.b));
    \\    c = mix(vec3(l), c, gradeSat + (1.0 - chroma) * 0.12);
    \\    c *= mix(vec3(0.975, 0.99, 1.03), vec3(1.025, 1.0, 0.965), smoothstep(0.12, 0.7, l));
    \\    c = mix(c, c * c * (3.0 - 2.0 * c), 0.17);
    \\    c = max(c - 0.008, 0.0) * 1.008;
    \\    c *= gradeTint;
    \\    return pow(clamp(c, 0.0, 1.0), vec3(1.0 / 2.2));
    \\}
    \\
;

const lit_fs_head =
    \\#version 330
    \\in vec3 worldPos;
    \\in vec3 worldNormal;
    \\in float localY;
    \\centroid in vec4 tint;
    \\centroid in vec2 uv;
    \\uniform sampler2D texture0;
    \\uniform vec4 colDiffuse;
    \\uniform sampler2D shadowMap;
    \\uniform mat4 lightVP;
    \\uniform vec3 ambSky;
    \\uniform vec3 ambGround;
    \\uniform vec3 shadeTint;
    \\uniform sampler2D shadowMapFar;
    \\uniform mat4 lightVPFar;
    \\uniform float cascades;
    \\uniform float detail;
    \\uniform vec3 sunDir;
    \\uniform vec3 sunColor;
    \\uniform vec3 viewPos;
    \\uniform float roughness;
    \\uniform float metallic;
    \\uniform float fogDensity;
    \\uniform float shadowTexel;
    \\uniform float glassAlpha;
    \\uniform float sheen;
    \\uniform float prism;
    \\uniform float courtyard;
    \\uniform sampler2D mtex0;
    \\uniform sampler2D mtex1;
    \\uniform sampler2D mtex2;
    \\uniform sampler2D mtex3;
    \\uniform sampler2D mtex4;
    \\uniform float matOn;
    \\uniform float matId;
    \\uniform sampler2D groundMap;
    \\uniform sampler2D groundDetail;
    \\uniform vec3 groundXf;
    \\out vec4 finalColor;
    \\
;

const lit_fs_body =
    \\uniform vec3 fogColor;
    \\vec3 groundSurface(vec3 n, float dist) {
    \\    vec2 guv = (worldPos.xz + groundXf.x) * groundXf.y;
    \\    vec3 g = texture(groundMap, guv).rgb;
    \\    float mx = max(max(g.r, g.g), g.b);
    \\    float mn = min(min(g.r, g.g), g.b);
    \\    float sat = (mx - mn) / max(mx, 0.001);
    \\    float lum = dot(g, vec3(0.3, 0.59, 0.11));
    \\    float grassW = smoothstep(0.0, 0.035, g.g - max(g.r * 0.97, g.b * 1.12));
    \\    float snowW = smoothstep(0.66, 0.76, lum) * (1.0 - smoothstep(0.1, 0.18, sat));
    \\    float greyW = (1.0 - smoothstep(0.1, 0.2, sat)) * (1.0 - snowW) * (1.0 - grassW);
    \\    float warm = max(1.0 - grassW - snowW - greyW, 0.0);
    \\    float sandW = warm * smoothstep(0.46, 0.56, lum);
    \\    float dirtW = warm - sandW;
    \\    float steep = 1.0 - smoothstep(0.62, 0.8, n.y);
    \\    vec4 w = vec4(grassW, dirtW, sandW + snowW * 0.4, greyW);
    \\    w = mix(w, vec4(0.0, 0.0, 0.0, 1.0), steep * (1.0 - snowW));
    \\    vec2 duv = n.y > 0.7 ? worldPos.xz : (abs(n.x) > abs(n.z) ? worldPos.zy : worldPos.xy);
    \\    vec4 dt = texture(groundDetail, duv * 0.42);
    \\    float d = dot((dt - 0.5) * vec4(1.0, 0.9, 0.6, 0.8), w) / max(w.x + w.y + w.z + w.w, 0.001);
    \\    float near = 1.0 - smoothstep(14.0, 70.0, dist);
    \\    float amp = mix(0.32, 1.0, near) * mix(1.0, 0.55, snowW);
    \\    vec3 tip = mix(vec3(1.0), vec3(1.05, 1.07, 0.86), grassW * clamp(d * 2.0, 0.0, 1.0));
    \\    return g * tip * (1.0 + d * 0.95 * amp);
    \\}
    \\void main() {
    \\    vec4 texel = texture(texture0, uv);
    \\    if (texel.a * colDiffuse.a < 0.45) discard;
    \\    vec3 n = normalize(worldNormal);
    \\    if (!gl_FrontFacing) n = -n;
    \\    float dist = length(viewPos - worldPos);
    \\    vec3 base = tint.rgb * colDiffuse.rgb * texel.rgb;
    \\    if (detail > 0.5 && detail < 1.5 && groundXf.z > 0.5) base = groundSurface(n, dist);
    \\    float ndl = max(dot(n, normalize(sunDir)), 0.0);
    \\    vec3 fill = mix(vec3(0.56, 0.59, 0.66), vec3(0.7, 0.73, 0.8), n.y * 0.5 + 0.5);
    \\    vec3 light = fill + vec3(0.5, 0.48, 0.44) * ndl + 0.06 * max(n.y, 0.0);
    \\    vec3 col = base * min(light, vec3(1.12));
    \\    float fog = min(1.0 - exp(-max(dist - 60.0, 0.0) * fogDensity * 0.55), 0.85);
    \\    col = mix(col, fogColor, fog);
    \\    finalColor = vec4(col, glassAlpha > 0.0 ? glassAlpha : 1.0);
    \\}
;

const lit_fs = lit_fs_head ++ lit_fs_body;

const sky_vs =
    \\#version 330
    \\in vec3 vertexPosition;
    \\uniform mat4 mvp;
    \\out vec3 dir;
    \\void main() {
    \\    dir = vertexPosition;
    \\    gl_Position = mvp * vec4(vertexPosition, 1.0);
    \\}
;

const sky_fs = "#version 330\nin vec3 dir;\nout vec4 finalColor;\nuniform vec3 skyZenith;\nuniform vec3 sunDir;\nuniform float time;\nuniform float prism;\n" ++ common_fs ++
    \\uniform sampler2D cloudTex;
    \\float fbm(vec2 p) {
    \\    return texture(cloudTex, p * 0.125).r;
    \\}
    \\void main() {
    \\    vec3 d = normalize(dir);
    \\    float h = clamp(d.y, 0.0, 1.0);
    \\    if (prism > 0.5) {
    \\        vec3 pc = mix(fogColor * 1.22 + vec3(0.03), fogColor * 0.5, pow(h, 0.55));
    \\        float ps = max(dot(d, normalize(sunDir)), 0.0);
    \\        pc += vec3(1.0, 0.98, 0.92) * (pow(ps, 64.0) * 0.5 + pow(ps, 6.0) * 0.08);
    \\        if (d.y < 0.0) pc = fogColor * 1.22 + vec3(0.03);
    \\        finalColor = vec4(grade(pc), 1.0);
    \\        return;
    \\    }
    \\    vec3 zenith = skyZenith;
    \\    vec3 horizon = mix(fogColor, vec3(0.42, 0.62, 0.9), 0.18);
    \\    vec3 col = mix(horizon, zenith, pow(h, 0.42));
    \\    vec3 l = normalize(sunDir);
    \\    float s = max(dot(d, l), 0.0);
    \\    col += vec3(1.0, 0.92, 0.75) * (smoothstep(0.9985, 0.9992, s) * 6.0 + pow(s, 24.0) * 0.35 + pow(s, 4.0) * 0.08);
    \\    if (d.y > 0.0) {
    \\        vec2 p = d.xz / (d.y + 0.12) * 0.9 + vec2(time * 0.006, time * 0.002);
    \\        float n = fbm(p * 1.6);
    \\        float cover = smoothstep(0.56, 0.66, n) * smoothstep(0.0, 0.18, d.y);
    \\        float shade = smoothstep(0.52, 0.85, fbm(p * 1.6 + vec2(0.06, 0.04)));
    \\        vec3 cloud = mix(vec3(1.0, 1.0, 1.02), vec3(0.74, 0.80, 0.92), shade * 0.8);
    \\        cloud += vec3(1.0, 0.9, 0.7) * pow(s, 8.0) * 0.4;
    \\        col = mix(col, cloud, cover);
    \\    } else {
    \\        col = mix(horizon, vec3(0.42, 0.50, 0.44), smoothstep(0.0, -0.25, d.y));
    \\    }
    \\    finalColor = vec4(grade(col), 1.0);
    \\}
;

pub const Surface = struct {
    roughness: f32 = 0.78,
    metallic: f32 = 0,
};

const Locs = struct {
    shadow_map: c_int,
    amb_sky: c_int,
    amb_ground: c_int,
    shade_tint: c_int,
    env_map: c_int,
    light_vp: c_int,
    sun_dir: c_int,
    sun_color: c_int,
    view: c_int,
    roughness: c_int,
    metallic: c_int,
    fog: c_int,
    texel: c_int,
    env_scale: c_int,
    exposure: c_int,
    grade_tint: c_int,
    grade_sat: c_int,
    post: c_int,
    fog_color: c_int,
    shadow_map_far: c_int,
    light_vp_far: c_int,
    cascades: c_int,
    detail: c_int,
    prism: c_int,
    glass: c_int,
};

fn locsFor(sh: rl.Shader) Locs {
    return .{
        .shadow_map = rl.GetShaderLocation(sh, "shadowMap"),
        .amb_sky = rl.GetShaderLocation(sh, "ambSky"),
        .amb_ground = rl.GetShaderLocation(sh, "ambGround"),
        .shade_tint = rl.GetShaderLocation(sh, "shadeTint"),
        .env_map = rl.GetShaderLocation(sh, "envMap"),
        .light_vp = rl.GetShaderLocation(sh, "lightVP"),
        .sun_dir = rl.GetShaderLocation(sh, "sunDir"),
        .sun_color = rl.GetShaderLocation(sh, "sunColor"),
        .view = rl.GetShaderLocation(sh, "viewPos"),
        .roughness = rl.GetShaderLocation(sh, "roughness"),
        .metallic = rl.GetShaderLocation(sh, "metallic"),
        .fog = rl.GetShaderLocation(sh, "fogDensity"),
        .texel = rl.GetShaderLocation(sh, "shadowTexel"),
        .env_scale = rl.GetShaderLocation(sh, "envScale"),
        .exposure = rl.GetShaderLocation(sh, "exposure"),
        .grade_tint = rl.GetShaderLocation(sh, "gradeTint"),
        .grade_sat = rl.GetShaderLocation(sh, "gradeSat"),
        .post = rl.GetShaderLocation(sh, "postFx"),
        .fog_color = rl.GetShaderLocation(sh, "fogColor"),
        .shadow_map_far = rl.GetShaderLocation(sh, "shadowMapFar"),
        .light_vp_far = rl.GetShaderLocation(sh, "lightVPFar"),
        .cascades = rl.GetShaderLocation(sh, "cascades"),
        .detail = rl.GetShaderLocation(sh, "detail"),
        .prism = rl.GetShaderLocation(sh, "prism"),
        .glass = rl.GetShaderLocation(sh, "glassAlpha"),
    };
}

const SkyLocs = struct {
    env_map: c_int,
    env_scale: c_int,
    exposure: c_int,
    grade_tint: c_int,
    grade_sat: c_int,
    sun_dir: c_int,
    time: c_int,
    post: c_int,
    fog_color: c_int,
    prism: c_int,
    zenith: c_int,
};

pub const Phase = enum { shadow, main };

const inst_cap: usize = 16384;
var inst_stage: [inst_cap][16]f32 = undefined;
var inst_vbos: [3]c_uint = .{ 0, 0, 0 };
var inst_frame: usize = 0;
var inst_ring: usize = 0;
var sway_loc: c_int = -2;
var sway_time_loc: c_int = -1;
var mat_id_loc: c_int = -1;
var skinned_loc: c_int = -1;
var bones_loc: c_int = -1;

fn latticeHash(x: u32, y: u32) f32 {
    var h = x *% 374761393 +% y *% 668265263;

    h = (h ^ (h >> 13)) *% 1274126177;
    h ^= h >> 16;

    return @as(f32, @floatFromInt(h & 0xffff)) / 65535.0;
}

fn valueNoise(x: f32, y: f32, period: u32) f32 {
    const fx = @floor(x);
    const fy = @floor(y);
    const ix: u32 = @intFromFloat(fx);
    const iy: u32 = @intFromFloat(fy);
    const tx = x - fx;
    const ty = y - fy;
    const ux = tx * tx * (3 - 2 * tx);
    const uy = ty * ty * (3 - 2 * ty);
    const x0 = ix % period;
    const y0 = iy % period;
    const x1 = (ix + 1) % period;
    const y1 = (iy + 1) % period;
    const a = latticeHash(x0, y0);
    const b = latticeHash(x1, y0);
    const c = latticeHash(x0, y1);
    const d = latticeHash(x1, y1);

    return (a + (b - a) * ux) + ((c + (d - c) * ux) - (a + (b - a) * ux)) * uy;
}

fn makeClouds() c_uint {
    const size: usize = 512;
    const span: f32 = 8;
    const pixels = std.heap.page_allocator.alloc(u8, size * size) catch return 0;

    defer std.heap.page_allocator.free(pixels);

    for (0..size) |j| {
        for (0..size) |i| {
            const x = @as(f32, @floatFromInt(i)) / @as(f32, @floatFromInt(size)) * span;
            const y = @as(f32, @floatFromInt(j)) / @as(f32, @floatFromInt(size)) * span;
            var v: f32 = 0;
            var a: f32 = 0.5;
            var f: f32 = 1;
            var period: u32 = 8;

            for (0..5) |_| {
                v += a * valueNoise(x * f, y * f, period);
                f *= 2;
                period *= 2;
                a *= 0.5;
            }

            pixels[j * size + i] = @intFromFloat(std.math.clamp(v, 0, 1) * 255);
        }
    }

    const id = rlgl.rlLoadTexture(pixels.ptr, @intCast(size), @intCast(size), rl.PIXELFORMAT_UNCOMPRESSED_GRAYSCALE, 1);

    rlgl.rlTextureParameters(id, rlgl.RL_TEXTURE_WRAP_S, rlgl.RL_TEXTURE_WRAP_REPEAT);
    rlgl.rlTextureParameters(id, rlgl.RL_TEXTURE_WRAP_T, rlgl.RL_TEXTURE_WRAP_REPEAT);
    rlgl.rlTextureParameters(id, rlgl.RL_TEXTURE_MAG_FILTER, rlgl.RL_TEXTURE_FILTER_LINEAR);
    rlgl.rlTextureParameters(id, rlgl.RL_TEXTURE_MIN_FILTER, rlgl.RL_TEXTURE_FILTER_LINEAR);

    return id;
}

fn asMat(comptime T: type, m: anytype) T {
    return @as(*const T, @ptrCast(&m)).*;
}

fn flatMatrix(m: rl.Matrix) [16]f32 {
    return .{ m.m0, m.m1, m.m2, m.m3, m.m4, m.m5, m.m6, m.m7, m.m8, m.m9, m.m10, m.m11, m.m12, m.m13, m.m14, m.m15 };
}

pub fn uploadStatic(transforms: []const rl.Matrix) c_uint {
    if (transforms.len == 0) return 0;

    const flat = std.heap.page_allocator.alloc([16]f32, transforms.len) catch return 0;

    defer std.heap.page_allocator.free(flat);

    for (transforms, 0..) |t, i| flat[i] = flatMatrix(t);

    return rlgl.rlLoadVertexBuffer(flat.ptr, @intCast(transforms.len * 64), false);
}

fn drawMeshBatch(mesh: rl.Mesh, material: rl.Material, transforms: []const rl.Matrix) void {
    const sh = material.shader;
    const inst_loc = sh.locs[@intCast(rl.SHADER_LOC_VERTEX_INSTANCETRANSFORM)];

    if (inst_loc < 0 or transforms.len > inst_cap) return rl.DrawMeshInstanced(mesh, material, transforms.ptr, @intCast(transforms.len));

    const inst_vbo = &inst_vbos[inst_frame];

    if (inst_vbo.* == 0) inst_vbo.* = rlgl.rlLoadVertexBuffer(null, @intCast(inst_cap * 64), true);

    if (inst_ring + transforms.len > inst_cap) inst_ring = 0;

    for (transforms, 0..) |t, i| inst_stage[inst_ring + i] = flatMatrix(t);

    const base = inst_ring * 64;

    rlgl.rlUpdateVertexBuffer(inst_vbo.*, &inst_stage[inst_ring], @intCast(transforms.len * 64), @intCast(base));
    inst_ring += transforms.len;
    drawFromBuffer(mesh, material, inst_vbo.*, base, transforms.len);
}

fn drawFromBuffer(mesh: rl.Mesh, material: rl.Material, vbo: c_uint, base: usize, count: usize) void {
    const sh = material.shader;
    const inst_loc = sh.locs[@intCast(rl.SHADER_LOC_VERTEX_INSTANCETRANSFORM)];

    rlgl.rlEnableShader(sh.id);

    const diffuse = material.maps[@intCast(rl.MATERIAL_MAP_DIFFUSE)];
    const col_loc = sh.locs[@intCast(rl.SHADER_LOC_COLOR_DIFFUSE)];

    if (col_loc != -1) {
        const c = diffuse.color;
        const v = [4]f32{ @as(f32, @floatFromInt(c.r)) / 255, @as(f32, @floatFromInt(c.g)) / 255, @as(f32, @floatFromInt(c.b)) / 255, @as(f32, @floatFromInt(c.a)) / 255 };

        rlgl.rlSetUniform(col_loc, &v, rl.SHADER_UNIFORM_VEC4, 1);
    }

    const view = rlgl.rlGetMatrixModelview();
    const proj = rlgl.rlGetMatrixProjection();
    const view_loc = sh.locs[@intCast(rl.SHADER_LOC_MATRIX_VIEW)];
    const proj_loc = sh.locs[@intCast(rl.SHADER_LOC_MATRIX_PROJECTION)];
    const normal_loc = sh.locs[@intCast(rl.SHADER_LOC_MATRIX_NORMAL)];

    if (view_loc != -1) rlgl.rlSetUniformMatrix(view_loc, view);
    if (proj_loc != -1) rlgl.rlSetUniformMatrix(proj_loc, proj);
    if (normal_loc != -1) rlgl.rlSetUniformMatrix(normal_loc, asMat(rlgl.Matrix, rm.MatrixIdentity()));

    if (diffuse.texture.id > 0) {
        const slot: c_int = 0;

        rlgl.rlActiveTextureSlot(0);
        rlgl.rlEnableTexture(diffuse.texture.id);
        rlgl.rlSetUniform(sh.locs[@intCast(rl.SHADER_LOC_MAP_DIFFUSE)], &slot, rl.SHADER_UNIFORM_INT, 1);
    }

    _ = rlgl.rlEnableVertexArray(mesh.vaoId);
    rlgl.rlEnableVertexBuffer(vbo);

    for (0..4) |i| {
        const loc: c_uint = @intCast(inst_loc + @as(c_int, @intCast(i)));

        rlgl.rlEnableVertexAttribute(loc);
        rlgl.rlSetVertexAttribute(loc, 4, rlgl.RL_FLOAT, false, 64, @intCast(base + i * 16));
        rlgl.rlSetVertexAttributeDivisor(loc, 1);
    }

    rlgl.rlSetUniformMatrix(sh.locs[@intCast(rl.SHADER_LOC_MATRIX_MVP)], asMat(rlgl.Matrix, rm.MatrixMultiply(rm.MatrixMultiply(asMat(rm.Matrix, rlgl.rlGetMatrixTransform()), asMat(rm.Matrix, view)), asMat(rm.Matrix, proj))));

    if (mesh.indices != null) {
        rlgl.rlDrawVertexArrayElementsInstanced(0, mesh.triangleCount * 3, null, @intCast(count));
    } else {
        rlgl.rlDrawVertexArrayInstanced(0, mesh.vertexCount, @intCast(count));
    }

    if (diffuse.texture.id > 0) {
        rlgl.rlActiveTextureSlot(0);
        rlgl.rlDisableTexture();
    }

    rlgl.rlDisableVertexArray();
    rlgl.rlDisableVertexBuffer();
    rlgl.rlDisableShader();
}

pub const Renderer = struct {
    lit: rl.Shader,
    lit_inst: rl.Shader,
    depth: rl.Shader,
    depth_inst: rl.Shader,
    inst_locs: Locs,
    sky: rl.Shader,
    lit_material: rl.Material,
    depth_material: rl.Material,
    sky_material: rl.Material,
    sky_mesh: rl.Mesh,
    locs: Locs,
    sky_locs: SkyLocs,
    env: rl.Texture2D,
    mats: [5]rl.Texture2D = @splat(.{ .id = 0, .width = 0, .height = 0, .mipmaps = 0, .format = 0 }),
    mat_on: f32 = 0,
    ground_detail: rl.Texture2D = .{ .id = 0, .width = 0, .height = 0, .mipmaps = 0, .format = 0 },
    ground_map: rl.Texture2D = .{ .id = 0, .width = 0, .height = 0, .mipmaps = 0, .format = 0 },
    ground_xf: [3]f32 = .{ 0, 0, 0 },
    shadow_fbo: c_uint,
    shadow_depth: c_uint,
    shadow_fbo_far: c_uint = 0,
    shadow_depth_far: c_uint = 0,
    light_vp_far: rl.Matrix = .{},
    cascades: u8 = if (assets.mobile) 1 else 2,
    shadows_on: bool = true,
    fog_color: [3]f32 = .{ 0.62, 0.80, 0.96 },
    post: bool = false,
    ssao: bool = true,
    bloom: bool = true,
    fxaa: bool = true,
    render_scale: f32 = if (assets.mobile) 0.75 else 1,
    bloom_strength: f32 = 0.035,
    ao_strength: f32 = 0.85,
    fx: Post = .{},
    cam_fovy: f32 = 70,
    ao_done: bool = false,
    vm_pass: bool = false,
    in_post: bool = false,
    sun_dir: Vec3,
    sun_color: [3]f32,
    env_scale: f32,
    exposure: f32 = 0.85,
    amb_sky: [3]f32 = .{ 0.96, 1.06, 1.32 },
    amb_ground: [3]f32 = .{ 0.67, 0.56, 0.44 },
    shade_tint: [3]f32 = .{ 0.88, 0.92, 1.06 },
    zenith: [3]f32 = .{ 0.06, 0.22, 0.66 },
    grade_tint: [3]f32 = .{ 1.02, 1.0, 0.97 },
    grade_sat: f32 = 1.06,
    fog: f32 = 0.004,
    light_vp: rl.Matrix = .{},
    phase: Phase = .main,
    skip: bool = false,

    pub fn init(sky_path: [:0]const u8, sky_mesh: rl.Mesh) Renderer {
        const lit = shader(lit_vs, lit_fs);
        var lit_inst = shader(lit_inst_vs, lit_fs);
        const depth = shader(depth_vs, depth_fs);
        var depth_inst = shader(depth_inst_vs, depth_fs);

        lit_inst.locs[@intCast(rl.SHADER_LOC_VERTEX_INSTANCETRANSFORM)] = rl.GetShaderLocationAttrib(lit_inst, "instanceTransform");
        depth_inst.locs[@intCast(rl.SHADER_LOC_VERTEX_INSTANCETRANSFORM)] = rl.GetShaderLocationAttrib(depth_inst, "instanceTransform");

        const sky = shader(sky_vs, sky_fs);
        var lit_material = rl.LoadMaterialDefault();
        var sky_material = rl.LoadMaterialDefault();
        var image = rl.LoadImage(sky_path.ptr);
        const sun = findSun(image);
        const env_boost: f32 = if (assets.mobile) lowRange(&image) else 1;

        if (assets.mobile) rl.ImageMipmaps(&image);

        var env = rl.LoadTextureFromImage(image);

        rl.UnloadImage(image);

        if (!assets.mobile) rl.GenTextureMipmaps(&env);
        rl.SetTextureFilter(env, rl.TEXTURE_FILTER_TRILINEAR);
        rl.SetTextureWrap(env, rl.TEXTURE_WRAP_REPEAT);

        lit_material.shader = lit;
        sky_material.shader = sky;

        const fbo = rlgl.rlLoadFramebuffer();

        rlgl.rlEnableFramebuffer(fbo);

        const shadow_tex = rlgl.rlLoadTextureDepth(shadow_res, shadow_res, false);

        rlgl.rlFramebufferAttach(fbo, shadow_tex, rlgl.RL_ATTACHMENT_DEPTH, rlgl.RL_ATTACHMENT_TEXTURE2D, 0);
        _ = rlgl.rlFramebufferComplete(fbo);
        rlgl.rlDisableFramebuffer();

        var depth_material = rl.LoadMaterialDefault();

        depth_material.shader = depth;

        var far_fbo: c_uint = 0;
        var far_tex: c_uint = 0;

        if (!assets.mobile) {
            far_fbo = rlgl.rlLoadFramebuffer();
            rlgl.rlEnableFramebuffer(far_fbo);
            far_tex = rlgl.rlLoadTextureDepth(shadow_res, shadow_res, false);
            rlgl.rlFramebufferAttach(far_fbo, far_tex, rlgl.RL_ATTACHMENT_DEPTH, rlgl.RL_ATTACHMENT_TEXTURE2D, 0);
            _ = rlgl.rlFramebufferComplete(far_fbo);
            rlgl.rlDisableFramebuffer();
        }

        return .{
            .post = !assets.mobile and std.c.getenv("DF_POST") != null,
            .ssao = std.c.getenv("DF_NOAO") == null,
            .bloom = std.c.getenv("DF_NOBLOOM") == null,
            .fxaa = std.c.getenv("DF_NOFXAA") == null,
            .shadow_fbo_far = far_fbo,
            .shadow_depth_far = far_tex,
            .lit = lit,
            .lit_inst = lit_inst,
            .depth = depth,
            .depth_inst = depth_inst,
            .inst_locs = locsFor(lit_inst),
            .sky = sky,
            .lit_material = lit_material,
            .depth_material = depth_material,
            .sky_material = sky_material,
            .sky_mesh = sky_mesh,
            .locs = locsFor(lit),
            .sky_locs = .{
                .env_map = rl.GetShaderLocation(sky, "envMap"),
                .env_scale = rl.GetShaderLocation(sky, "envScale"),
                .exposure = rl.GetShaderLocation(sky, "exposure"),
                .grade_tint = rl.GetShaderLocation(sky, "gradeTint"),
                .grade_sat = rl.GetShaderLocation(sky, "gradeSat"),
                .sun_dir = rl.GetShaderLocation(sky, "sunDir"),
                .time = rl.GetShaderLocation(sky, "time"),
                .post = rl.GetShaderLocation(sky, "postFx"),
                .fog_color = rl.GetShaderLocation(sky, "fogColor"),
                .prism = rl.GetShaderLocation(sky, "prism"),
                .zenith = rl.GetShaderLocation(sky, "skyZenith"),
            },
            .env = env,
            .shadow_fbo = fbo,
            .shadow_depth = shadow_tex,
            .sun_dir = sun.dir,
            .sun_color = sun.color,
            .env_scale = sun.env_scale * env_boost,
        };
    }

    pub fn beginShadow(r: *Renderer, focus: Vec3, cascade: usize) void {
        const far = cascade > 0;
        const span: f32 = if (far) shadow_span_far else shadow_span;
        const snap: f32 = span * 2 / @as(f32, @floatFromInt(shadow_res));
        const look = r.sun_dir.neg();
        const ref: Vec3 = if (@abs(r.sun_dir.y) > 0.97) .{ .z = 1 } else .{ .y = 1 };
        const side = look.cross(ref).normalize();
        const lift = side.cross(look);
        const a = @round(focus.dot(side) / snap) * snap;
        const b = @round(focus.dot(lift) / snap) * snap;
        const center = side.scale(a).add(lift.scale(b)).add(look.scale(focus.dot(look)));
        const eye = center.add(r.sun_dir.scale(160));
        const light_cam: rl.Camera3D = .{
            .position = .{ .x = eye.x, .y = eye.y, .z = eye.z },
            .target = .{ .x = center.x, .y = center.y, .z = center.z },
            .up = if (@abs(r.sun_dir.y) > 0.97) .{ .z = 1 } else .{ .y = 1 },
            .fovy = span,
            .projection = rl.CAMERA_ORTHOGRAPHIC,
        };

        r.phase = .shadow;
        r.skip = false;
        rlgl.rlDrawRenderBatchActive();
        rlgl.rlSetClipPlanes(1, 400);
        rlgl.rlEnableFramebuffer(if (far) r.shadow_fbo_far else r.shadow_fbo);
        rlgl.rlViewport(0, 0, shadow_res, shadow_res);
        rlgl.rlClearScreenBuffers();
        rl.BeginMode3D(light_cam);

        const view = retype(rm.Matrix, rlgl.rlGetMatrixModelview());
        const proj = retype(rm.Matrix, rlgl.rlGetMatrixProjection());

        const vp = retype(rl.Matrix, rm.MatrixMultiply(view, proj));

        if (far) r.light_vp_far = vp else r.light_vp = vp;
    }

    pub fn endShadow(r: *Renderer) void {
        rl.EndMode3D();
        rlgl.rlDisableFramebuffer();
        rlgl.rlViewport(0, 0, rl.GetRenderWidth(), rl.GetRenderHeight());
        r.phase = .main;
        r.skip = false;
    }

    pub fn begin(r: *Renderer, cam: rl.Camera3D, time: f32) void {
        inst_frame = (inst_frame + 1) % inst_vbos.len;
        inst_ring = 0;

        const view = [3]f32{ cam.position.x, cam.position.y, cam.position.z };
        const sun = [3]f32{ r.sun_dir.x, r.sun_dir.y, r.sun_dir.z };
        const texel: f32 = 1.0 / @as(f32, @floatFromInt(shadow_res));
        const shadow_unit = shadow_slot;
        const env_unit = env_slot;
        const sky_at = retype(rl.Matrix, rm.MatrixTranslate(cam.position.x, cam.position.y, cam.position.z));

        r.cam_fovy = cam.fovy;
        r.ao_done = false;
        r.vm_pass = false;
        r.in_post = r.post and r.fx.ensure(r.render_scale);

        if (r.in_post) r.fx.bindScene();

        rl.ClearBackground(.{ .r = 0, .g = 0, .b = 0, .a = 255 });
        rlgl.rlSetClipPlanes(near_plane, far_plane);
        rl.BeginMode3D(cam);

        rlgl.rlActiveTextureSlot(env_slot);
        rlgl.rlEnableTexture(r.env.id);

        if (cloud_tex == 0) cloud_tex = makeClouds();

        if (cloud_loc == -2) cloud_loc = rl.GetShaderLocation(r.sky, "cloudTex");

        rlgl.rlActiveTextureSlot(cloud_slot);
        rlgl.rlEnableTexture(cloud_tex);
        rlgl.rlActiveTextureSlot(shadow_slot);
        rlgl.rlEnableTexture(r.shadow_depth);

        for (r.mats, 0..) |m, i| {
            if (m.id == 0) continue;

            rlgl.rlActiveTextureSlot(mat_slot + @as(c_int, @intCast(i)));
            rlgl.rlEnableTexture(m.id);
        }

        if (r.ground_detail.id != 0 and r.ground_map.id != 0) {
            rlgl.rlActiveTextureSlot(ground_detail_slot);
            rlgl.rlEnableTexture(r.ground_detail.id);
            rlgl.rlActiveTextureSlot(ground_map_slot);
            rlgl.rlEnableTexture(r.ground_map.id);
        }

        if (r.cascades > 1) {
            rlgl.rlActiveTextureSlot(shadow_slot_far);
            rlgl.rlEnableTexture(r.shadow_depth_far);
        }

        rlgl.rlActiveTextureSlot(0);

        rlgl.rlEnableShader(r.sky.id);
        rlgl.rlSetUniform(r.sky_locs.env_map, &env_unit, rl.SHADER_UNIFORM_INT, 1);
        rlgl.rlSetUniform(cloud_loc, &cloud_slot, rl.SHADER_UNIFORM_INT, 1);
        rl.SetShaderValue(r.sky, r.sky_locs.env_scale, &r.env_scale, rl.SHADER_UNIFORM_FLOAT);
        rl.SetShaderValue(r.sky, r.sky_locs.exposure, &r.exposure, rl.SHADER_UNIFORM_FLOAT);
        rl.SetShaderValue(r.sky, r.sky_locs.grade_tint, &r.grade_tint, rl.SHADER_UNIFORM_VEC3);
        rl.SetShaderValue(r.sky, r.sky_locs.grade_sat, &r.grade_sat, rl.SHADER_UNIFORM_FLOAT);
        rl.SetShaderValue(r.sky, r.sky_locs.sun_dir, &sun, rl.SHADER_UNIFORM_VEC3);
        rl.SetShaderValue(r.sky, r.sky_locs.time, &time, rl.SHADER_UNIFORM_FLOAT);

        const post_on: f32 = if (r.in_post) 1 else 0;

        rl.SetShaderValue(r.sky, r.sky_locs.post, &post_on, rl.SHADER_UNIFORM_FLOAT);
        rl.SetShaderValue(r.sky, r.sky_locs.fog_color, &r.fog_color, rl.SHADER_UNIFORM_VEC3);
        rl.SetShaderValue(r.sky, r.sky_locs.zenith, &r.zenith, rl.SHADER_UNIFORM_VEC3);

        const prism_on: f32 = if (shared.terrain.current == .prism) 1 else 0;

        rl.SetShaderValue(r.sky, r.sky_locs.prism, &prism_on, rl.SHADER_UNIFORM_FLOAT);

        r.setLit(r.lit, r.locs, view, sun, texel, env_unit, shadow_unit);
        r.setLit(r.lit_inst, r.inst_locs, view, sun, texel, env_unit, shadow_unit);
        r.setSurface(.{});

        rlgl.rlDisableBackfaceCulling();
        rlgl.rlDisableDepthMask();
        rl.DrawMesh(r.sky_mesh, r.sky_material, sky_at);
        rlgl.rlEnableDepthMask();
        rlgl.rlEnableBackfaceCulling();
    }

    fn setLit(r: *Renderer, sh: rl.Shader, l: Locs, view: [3]f32, sun: [3]f32, texel: f32, env_unit: c_int, shadow_unit: c_int) void {
        rlgl.rlEnableShader(sh.id);
        rlgl.rlSetUniform(l.env_map, &env_unit, rl.SHADER_UNIFORM_INT, 1);
        rlgl.rlSetUniform(l.shadow_map, &shadow_unit, rl.SHADER_UNIFORM_INT, 1);
        rl.SetShaderValueMatrix(sh, l.light_vp, r.light_vp);
        rl.SetShaderValue(sh, l.sun_dir, &sun, rl.SHADER_UNIFORM_VEC3);
        rl.SetShaderValue(sh, l.amb_sky, &r.amb_sky, rl.SHADER_UNIFORM_VEC3);
        rl.SetShaderValue(sh, l.amb_ground, &r.amb_ground, rl.SHADER_UNIFORM_VEC3);
        rl.SetShaderValue(sh, l.shade_tint, &r.shade_tint, rl.SHADER_UNIFORM_VEC3);
        rl.SetShaderValue(sh, l.sun_color, &r.sun_color, rl.SHADER_UNIFORM_VEC3);
        rl.SetShaderValue(sh, l.view, &view, rl.SHADER_UNIFORM_VEC3);
        rl.SetShaderValue(sh, l.fog, &r.fog, rl.SHADER_UNIFORM_FLOAT);
        rl.SetShaderValue(sh, l.texel, &texel, rl.SHADER_UNIFORM_FLOAT);
        rl.SetShaderValue(sh, l.env_scale, &r.env_scale, rl.SHADER_UNIFORM_FLOAT);
        rl.SetShaderValue(sh, l.exposure, &r.exposure, rl.SHADER_UNIFORM_FLOAT);
        rl.SetShaderValue(sh, l.grade_tint, &r.grade_tint, rl.SHADER_UNIFORM_VEC3);
        rl.SetShaderValue(sh, l.grade_sat, &r.grade_sat, rl.SHADER_UNIFORM_FLOAT);

        const post_on: f32 = if (r.in_post) 1 else 0;
        const far_unit = shadow_slot_far;
        const cascades: f32 = if (r.shadows_on) @floatFromInt(r.cascades) else 0;
        const no_detail: f32 = 0;

        rl.SetShaderValue(sh, l.post, &post_on, rl.SHADER_UNIFORM_FLOAT);
        rl.SetShaderValue(sh, l.fog_color, &r.fog_color, rl.SHADER_UNIFORM_VEC3);
        rlgl.rlSetUniform(l.shadow_map_far, &far_unit, rl.SHADER_UNIFORM_INT, 1);
        rl.SetShaderValueMatrix(sh, l.light_vp_far, r.light_vp_far);
        rl.SetShaderValue(sh, l.cascades, &cascades, rl.SHADER_UNIFORM_FLOAT);
        rl.SetShaderValue(sh, l.detail, &no_detail, rl.SHADER_UNIFORM_FLOAT);

        const prism_on: f32 = if (shared.terrain.current == .prism) 1 else 0;

        rl.SetShaderValue(sh, l.prism, &prism_on, rl.SHADER_UNIFORM_FLOAT);

        const courtyard_on: f32 = if (shared.terrain.current == .courtyard) 1 else 0;

        rl.SetShaderValue(sh, rl.GetShaderLocation(sh, "courtyard"), &courtyard_on, rl.SHADER_UNIFORM_FLOAT);

        const detail_unit = ground_detail_slot;
        const map_unit = ground_map_slot;
        const xf: [3]f32 = if (r.ground_detail.id != 0 and r.ground_map.id != 0) r.ground_xf else .{ 0, 0, 0 };

        rlgl.rlSetUniform(rl.GetShaderLocation(sh, "groundDetail"), &detail_unit, rl.SHADER_UNIFORM_INT, 1);
        rlgl.rlSetUniform(rl.GetShaderLocation(sh, "groundMap"), &map_unit, rl.SHADER_UNIFORM_INT, 1);
        rl.SetShaderValue(sh, rl.GetShaderLocation(sh, "groundXf"), &xf, rl.SHADER_UNIFORM_VEC3);

        const names = [_][:0]const u8{ "mtex0", "mtex1", "mtex2", "mtex3", "mtex4" };

        for (names, 0..) |name, i| {
            const unit: c_int = mat_slot + @as(c_int, @intCast(i));

            rlgl.rlSetUniform(rl.GetShaderLocation(sh, name.ptr), &unit, rl.SHADER_UNIFORM_INT, 1);
        }

        const on: f32 = if (prism_on > 0.5 or courtyard_on > 0.5) 0 else r.mat_on;
        const auto_id: f32 = -1;

        rl.SetShaderValue(sh, rl.GetShaderLocation(sh, "matOn"), &on, rl.SHADER_UNIFORM_FLOAT);
        rl.SetShaderValue(sh, rl.GetShaderLocation(sh, "matId"), &auto_id, rl.SHADER_UNIFORM_FLOAT);
    }

    pub fn loadGround(r: *Renderer, dir: []const u8) void {
        var buf: [512]u8 = undefined;
        const path = std.fmt.bufPrintSentinel(&buf, "{s}/ground.png", .{dir}, 0) catch return;
        var t = rl.LoadTexture(path.ptr);

        if (t.id == 0) return;

        rl.GenTextureMipmaps(&t);
        rl.SetTextureFilter(t, rl.TEXTURE_FILTER_TRILINEAR);
        rl.SetTextureWrap(t, rl.TEXTURE_WRAP_REPEAT);
        r.ground_detail = t;
    }

    pub fn setGroundMap(r: *Renderer, map: ?rl.Texture2D, extent: f32) void {
        const t = map orelse {
            r.ground_xf = .{ 0, 0, 0 };

            return;
        };

        r.ground_map = t;
        r.ground_xf = .{ extent, 1 / (2 * extent), 1 };
    }

    pub fn loadMaterials(r: *Renderer, dir: []const u8) void {
        for (&r.mats, 0..) |*m, i| {
            var buf: [512]u8 = undefined;
            const path = std.fmt.bufPrintSentinel(&buf, "{s}/mat{d}.png", .{ dir, i }, 0) catch return;
            var t = rl.LoadTexture(path.ptr);

            if (t.id == 0) return;

            rl.GenTextureMipmaps(&t);
            rl.SetTextureFilter(t, rl.TEXTURE_FILTER_TRILINEAR);
            rl.SetTextureWrap(t, rl.TEXTURE_WRAP_REPEAT);
            m.* = t;
        }

        r.mat_on = 1;
    }

    pub fn setMatId(r: *Renderer, id: f32) void {
        if (r.phase == .shadow) return;

        if (sway_loc == -2) {
            sway_loc = rl.GetShaderLocation(r.lit_inst, "sway");
            sway_time_loc = rl.GetShaderLocation(r.lit_inst, "swayTime");
            mat_id_loc = rl.GetShaderLocation(r.lit_inst, "matId");
        }

        rl.SetShaderValue(r.lit_inst, mat_id_loc, &id, rl.SHADER_UNIFORM_FLOAT);
    }

    pub fn setGlass(r: *Renderer, alpha: f32) void {
        if (r.phase == .shadow) return;

        rlgl.rlDrawRenderBatchActive();
        rl.SetShaderValue(r.lit_inst, r.inst_locs.glass, &alpha, rl.SHADER_UNIFORM_FLOAT);

        if (alpha > 0) rlgl.rlDisableDepthMask() else rlgl.rlEnableDepthMask();
    }

    pub fn setDetailMode(r: *Renderer, v: f32) void {
        if (r.phase == .shadow) return;

        rl.SetShaderValue(r.lit, r.locs.detail, &v, rl.SHADER_UNIFORM_FLOAT);
    }

    pub fn setPropDetail(r: *Renderer, on: bool) void {
        if (r.phase == .shadow) return;

        const v: f32 = if (on and shared.terrain.current != .prism and shared.terrain.current != .courtyard) 4 else 0;

        rl.SetShaderValue(r.lit_inst, rl.GetShaderLocation(r.lit_inst, "detail"), &v, rl.SHADER_UNIFORM_FLOAT);
    }

    pub fn setDetail(r: *Renderer, on: bool) void {
        if (r.phase == .shadow) return;

        const panel = shared.terrain.current == .facility;
        const v: f32 = if (!on or shared.terrain.current == .courtyard) 0 else if (shared.terrain.current == .prism) 3 else if (panel) 2 else 1;

        rl.SetShaderValue(r.lit, r.locs.detail, &v, rl.SHADER_UNIFORM_FLOAT);
    }

    pub fn setSurface(r: *Renderer, s: Surface) void {
        if (r.phase == .shadow) return;

        rl.SetShaderValue(r.lit, r.locs.roughness, &s.roughness, rl.SHADER_UNIFORM_FLOAT);
        rl.SetShaderValue(r.lit, r.locs.metallic, &s.metallic, rl.SHADER_UNIFORM_FLOAT);
        rl.SetShaderValue(r.lit_inst, r.inst_locs.roughness, &s.roughness, rl.SHADER_UNIFORM_FLOAT);
        rl.SetShaderValue(r.lit_inst, r.inst_locs.metallic, &s.metallic, rl.SHADER_UNIFORM_FLOAT);
    }

    pub fn setSway(r: *Renderer, amount: f32) void {
        const t: f32 = @floatCast(rl.GetTime());

        if (sway_loc == -2) {
            sway_loc = rl.GetShaderLocation(r.lit_inst, "sway");
            sway_time_loc = rl.GetShaderLocation(r.lit_inst, "swayTime");
            mat_id_loc = rl.GetShaderLocation(r.lit_inst, "matId");
        }

        rl.SetShaderValue(r.lit_inst, sway_loc, &amount, rl.SHADER_UNIFORM_FLOAT);
        rl.SetShaderValue(r.lit_inst, sway_time_loc, &t, rl.SHADER_UNIFORM_FLOAT);
    }

    pub fn drawInstanced(r: *Renderer, model: rl.Model, transforms: []const rl.Matrix, two_sided: bool) void {
        if (r.skip or transforms.len == 0) return;

        if (two_sided) rlgl.rlDisableBackfaceCulling();

        var i: usize = 0;

        while (i < @as(usize, @intCast(model.meshCount))) : (i += 1) {
            var material = model.materials[@intCast(model.meshMaterial[i])];

            material.shader = if (r.phase == .shadow) r.depth_inst else r.lit_inst;
            drawMeshBatch(model.meshes[i], material, transforms);
        }

        if (two_sided) rlgl.rlEnableBackfaceCulling();
    }

    pub fn drawStatic(r: *Renderer, model: rl.Model, vbo: c_uint, count: usize, two_sided: bool) void {
        if (r.skip or count == 0 or vbo == 0) return;

        if (two_sided) rlgl.rlDisableBackfaceCulling();

        var i: usize = 0;

        while (i < @as(usize, @intCast(model.meshCount))) : (i += 1) {
            var material = model.materials[@intCast(model.meshMaterial[i])];

            material.shader = if (r.phase == .shadow) r.depth_inst else r.lit_inst;
            drawFromBuffer(model.meshes[i], material, vbo, 0, count);
        }

        if (two_sided) rlgl.rlEnableBackfaceCulling();
    }

    pub fn draw(r: *Renderer, m: rl.Mesh, transform: rl.Matrix, cast: bool) void {
        if (r.skip) return;

        if (r.phase == .shadow) {
            if (cast) rl.DrawMesh(m, r.depth_material, transform);

            return;
        }

        rl.DrawMesh(m, r.lit_material, transform);
    }

    pub fn enableSkinning(r: *Renderer, model: *rl.Model) void {
        skinned_loc = rl.GetShaderLocation(r.lit, "skinned");
        bones_loc = rl.GetShaderLocation(r.lit, "boneMatrices");
        r.lit.locs[@intCast(rl.SHADER_LOC_VERTEX_BONEIDS)] = rl.GetShaderLocationAttrib(r.lit, "vertexBoneIndices");
        r.lit.locs[@intCast(rl.SHADER_LOC_VERTEX_BONEWEIGHTS)] = rl.GetShaderLocationAttrib(r.lit, "vertexBoneWeights");
        r.lit_material.shader = r.lit;

        for (model.materials[0..@intCast(model.materialCount)]) |*m| m.shader = r.lit;
    }

    pub fn drawModel(r: *Renderer, model: rl.Model, transform: rl.Matrix) void {
        if (r.skip) return;

        const skin = r.phase != .shadow and bones_loc >= 0 and model.boneMatrices != null and model.skeleton.boneCount > 0 and model.skeleton.boneCount <= 56;

        if (skin) {
            const on: f32 = 1;

            rlgl.rlEnableShader(r.lit.id);
            rlgl.rlSetUniformMatrices(bones_loc, @ptrCast(model.boneMatrices), @intCast(model.skeleton.boneCount));
            rl.SetShaderValue(r.lit, skinned_loc, &on, rl.SHADER_UNIFORM_FLOAT);
        }

        defer if (skin) {
            const off: f32 = 0;

            rl.SetShaderValue(r.lit, skinned_loc, &off, rl.SHADER_UNIFORM_FLOAT);
        };

        var i: usize = 0;

        while (i < @as(usize, @intCast(model.meshCount))) : (i += 1) {
            var material = model.materials[@intCast(model.meshMaterial[i])];

            material.shader = if (r.phase == .shadow) r.depth else r.lit;
            rl.DrawMesh(model.meshes[i], material, transform);
        }
    }

    pub fn drawModelLit(r: *Renderer, model: rl.Model, transform: rl.Matrix) void {
        if (r.skip) return;

        var i: usize = 0;

        while (i < @as(usize, @intCast(model.meshCount))) : (i += 1) {
            var material = model.materials[@intCast(model.meshMaterial[i])];

            if (material.maps[0].color.a < 250) continue;

            if (r.phase == .main) r.setSurface(.{ .roughness = material.maps[rl.MATERIAL_MAP_ROUGHNESS].value, .metallic = material.maps[rl.MATERIAL_MAP_METALNESS].value });

            const own = material.maps[0].texture;

            if (r.phase == .shadow) material.maps[0].texture = .{ .id = rlgl.rlGetTextureIdDefault(), .width = 1, .height = 1, .mipmaps = 1, .format = rl.PIXELFORMAT_UNCOMPRESSED_R8G8B8A8 };

            material.shader = if (r.phase == .shadow) r.depth else r.lit;
            rl.DrawMesh(model.meshes[i], material, transform);
            material.maps[0].texture = own;
        }

        if (r.phase == .shadow) return;

        const loc = rl.GetShaderLocation(r.lit, "glassAlpha");
        const solid: f32 = 0;

        rlgl.rlDrawRenderBatchActive();
        rlgl.rlDisableDepthMask();
        i = 0;

        while (i < @as(usize, @intCast(model.meshCount))) : (i += 1) {
            var material = model.materials[@intCast(model.meshMaterial[i])];
            const alpha = @as(f32, @floatFromInt(material.maps[0].color.a)) / 255;

            if (material.maps[0].color.a >= 250) continue;

            r.setSurface(.{ .roughness = material.maps[rl.MATERIAL_MAP_ROUGHNESS].value, .metallic = material.maps[rl.MATERIAL_MAP_METALNESS].value });
            rl.SetShaderValue(r.lit, loc, &alpha, rl.SHADER_UNIFORM_FLOAT);
            material.maps[0].color.a = 255;
            material.shader = r.lit;
            rl.DrawMesh(model.meshes[i], material, transform);
        }

        rlgl.rlDrawRenderBatchActive();
        rlgl.rlEnableDepthMask();
        rl.SetShaderValue(r.lit, loc, &solid, rl.SHADER_UNIFORM_FLOAT);
    }

    pub fn setSheen(r: *Renderer, k: f32) void {
        if (r.phase == .shadow) return;

        rlgl.rlDrawRenderBatchActive();
        rl.SetShaderValue(r.lit, rl.GetShaderLocation(r.lit, "sheen"), &k, rl.SHADER_UNIFORM_FLOAT);
    }

    pub fn ambientBoost(r: *Renderer, k: f32) void {
        if (r.phase == .shadow) return;

        rlgl.rlDrawRenderBatchActive();

        const v = r.env_scale * k;

        rl.SetShaderValue(r.lit, r.locs.env_scale, &v, rl.SHADER_UNIFORM_FLOAT);
    }

    pub fn viewmodelProjection(r: *Renderer) void {
        if (r.phase == .shadow) return;

        rlgl.rlDrawRenderBatchActive();

        const w: f64 = @floatFromInt(@max(1, rlgl.rlGetFramebufferWidth()));
        const h: f64 = @floatFromInt(@max(1, rlgl.rlGetFramebufferHeight()));
        const aspect = w / h;
        const base: f64 = std.math.degreesToRadians(54.0);
        const hfov = 2 * std.math.atan(@tan(base / 2) * (16.0 / 9.0));
        const fovy = if (aspect < 16.0 / 9.0) 2 * std.math.atan(@tan(hfov / 2) / aspect) else base;
        const near: f64 = @max(0.02, vm_near);
        const top = near * @tan(fovy / 2);
        const right = top * aspect;

        rlgl.rlMatrixMode(rlgl.RL_PROJECTION);
        rlgl.rlLoadIdentity();
        rlgl.rlFrustum(-right, right, -top, top, near, 50);
        rlgl.rlMatrixMode(rlgl.RL_MODELVIEW);
    }

    pub fn clearDepth(r: *Renderer) void {
        if (r.phase == .shadow) {
            r.skip = true;

            return;
        }

        rlgl.rlDrawRenderBatchActive();

        const flat: f32 = 0;

        rl.SetShaderValue(r.lit, r.locs.prism, &flat, rl.SHADER_UNIFORM_FLOAT);
        rl.SetShaderValue(r.lit_inst, r.inst_locs.prism, &flat, rl.SHADER_UNIFORM_FLOAT);
        rl.SetShaderValue(r.lit, rl.GetShaderLocation(r.lit, "courtyard"), &flat, rl.SHADER_UNIFORM_FLOAT);
        rl.SetShaderValue(r.lit_inst, rl.GetShaderLocation(r.lit_inst, "courtyard"), &flat, rl.SHADER_UNIFORM_FLOAT);

        if (r.in_post) {
            r.fx.resolve();

            if (r.ssao) {
                r.fx.ambientOcclusion(r.cam_fovy);
                r.ao_done = true;
            }

            r.vm_pass = true;
            r.fx.bindScene();
            rlgl.rlEnableDepthTest();
            rlgl.rlEnableDepthMask();
            rlgl.rlEnableBackfaceCulling();
        }

        glClear(gl_depth_buffer_bit);
    }

    pub fn end(r: *Renderer) void {
        if (r.phase == .shadow) return;

        rlgl.rlDrawRenderBatchActive();
        rlgl.rlActiveTextureSlot(shadow_slot);
        rlgl.rlDisableTexture();
        rlgl.rlActiveTextureSlot(shadow_slot_far);
        rlgl.rlDisableTexture();
        rlgl.rlActiveTextureSlot(env_slot);
        rlgl.rlDisableTexture();
        rlgl.rlActiveTextureSlot(0);
        rl.EndMode3D();

        if (!r.in_post) return;

        r.fx.resolve();
        rlgl.rlDisableFramebuffer();

        if (r.ssao and !r.ao_done) r.fx.ambientOcclusion(r.cam_fovy);

        r.fx.finish(.{
            .exposure = r.exposure,
            .tint = r.grade_tint,
            .sat = r.grade_sat,
            .bloom = if (r.bloom) r.bloom_strength else 0,
            .ao = if (r.ssao) r.ao_strength else 0,
            .vm_mask = r.vm_pass,
            .fxaa = r.fxaa,
        });
        r.in_post = false;
    }
};

fn retype(comptime T: type, value: anytype) T {
    const bytes = std.mem.toBytes(value);

    return std.mem.bytesToValue(T, &bytes);
}

const Sun = struct {
    dir: Vec3,
    color: [3]f32,
    env_scale: f32,
};

fn esSource(comptime src: [:0]const u8) [:0]const u8 {
    const head = "#version 330";

    if (comptime !std.mem.startsWith(u8, src, head)) @compileError("shader must start with #version 330");

    return "#version 300 es\nprecision highp float;\nprecision highp sampler2D;" ++ src[head.len..];
}

fn shader(comptime vs: [:0]const u8, comptime fs: [:0]const u8) rl.Shader {
    if (assets.mobile or std.c.getenv("DF_ES_SHADERS") != null) return rl.LoadShaderFromMemory(comptime esSource(vs), comptime esSource(fs));

    return rl.LoadShaderFromMemory(vs, fs);
}

fn lowRange(image: *rl.Image) f32 {
    const range: f32 = 4;

    if (image.format != rl.PIXELFORMAT_UNCOMPRESSED_R32G32B32 or image.data == null) return 1;

    const n: usize = @intCast(image.width * image.height * 3);
    const px: [*]f32 = @ptrCast(@alignCast(image.data));

    for (px[0..n]) |*v| v.* = @min(v.* / range, 1);

    rl.ImageFormat(image, rl.PIXELFORMAT_UNCOMPRESSED_R8G8B8A8);

    return range;
}

fn findSun(image: rl.Image) Sun {
    const fallback: Sun = .{ .dir = (Vec3{ .x = 0.45, .y = 0.8, .z = 0.35 }).normalize(), .color = .{ 3.2, 3.0, 2.7 }, .env_scale = 1 };

    if (image.format != rl.PIXELFORMAT_UNCOMPRESSED_R32G32B32 or image.data == null) return fallback;

    const w: usize = @intCast(image.width);
    const h: usize = @intCast(image.height);
    const px: [*]const f32 = @ptrCast(@alignCast(image.data));
    var best: f32 = 0;
    var best_x: usize = 0;
    var best_y: usize = 0;
    var total: f64 = 0;
    var count: f64 = 0;
    var y: usize = 0;

    while (y < h / 2) : (y += 1) {
        var x: usize = 0;

        while (x < w) : (x += 1) {
            const i = (y * w + x) * 3;
            const lum = px[i] * 0.2126 + px[i + 1] * 0.7152 + px[i + 2] * 0.0722;

            if (lum > best) {
                best = lum;
                best_x = x;
                best_y = y;
            }

            if (lum < 50) {
                total += lum;
                count += 1;
            }
        }
    }

    const u = (@as(f32, @floatFromInt(best_x)) + 0.5) / @as(f32, @floatFromInt(w));
    const v = (@as(f32, @floatFromInt(best_y)) + 0.5) / @as(f32, @floatFromInt(h));
    const theta = v * std.math.pi;
    const phi = (u - 0.5) * 2 * std.math.pi;
    var dir: Vec3 = .{ .x = @sin(theta) * @cos(phi), .y = @cos(theta), .z = @sin(theta) * @sin(phi) };

    if (dir.y < 0.25) dir = (Vec3{ .x = dir.x, .y = 0.25, .z = dir.z }).normalize();

    const i = (best_y * w + best_x) * 3;
    const peak = @max(px[i], @max(px[i + 1], px[i + 2]));
    const avg: f32 = if (count > 0) @floatCast(total / count) else 1;

    return .{
        .dir = dir.normalize(),
        .color = .{ px[i] / peak * 2.0, px[i + 1] / peak * 2.0, px[i + 2] / peak * 2.0 },
        .env_scale = 0.5 / @max(avg, 0.01),
    };
}

const post_vs =
    \\#version 330
    \\in vec3 vertexPosition;
    \\in vec2 vertexTexCoord;
    \\out vec2 uv;
    \\void main() {
    \\    uv = vertexTexCoord;
    \\    gl_Position = vec4(vertexPosition.xy, 0.0, 1.0);
    \\}
;

const post_lin =
    \\uniform vec2 clip;
    \\float lin(float d) {
    \\    float z = d * 2.0 - 1.0;
    \\    return 2.0 * clip.x * clip.y / (clip.y + clip.x - z * (clip.y - clip.x));
    \\}
    \\
;

const ssao_fs = "#version 330\nin vec2 uv;\nout vec4 finalColor;\nuniform sampler2D depthTex;\nuniform vec2 proj;\nuniform float radius;\n" ++ post_lin ++
    \\vec3 viewAt(vec2 p) {
    \\    float l = lin(texture(depthTex, p).r);
    \\    return vec3((p * 2.0 - 1.0) * proj * l, -l);
    \\}
    \\void main() {
    \\    float d = texture(depthTex, uv).r;
    \\    if (d >= 0.99999) {
    \\        finalColor = vec4(1.0);
    \\        return;
    \\    }
    \\    vec3 p = viewAt(uv);
    \\    vec3 cn = cross(dFdx(p), dFdy(p));
    \\    if (dot(cn, cn) < 1e-14) {
    \\        finalColor = vec4(1.0);
    \\        return;
    \\    }
    \\    vec3 n = normalize(cn);
    \\    if (dot(n, -p) < 0.0) n = -n;
    \\    float rot = fract(52.9829189 * fract(dot(gl_FragCoord.xy, vec2(0.06711056, 0.00583715)))) * 6.2831853;
    \\    vec3 rv = vec3(cos(rot), sin(rot), 0.0);
    \\    vec3 t = normalize(rv - n * dot(rv, n));
    \\    vec3 b = cross(n, t);
    \\    float rad = radius * clamp(-p.z * 0.08 + 0.6, 0.6, 2.0);
    \\    float occ = 0.0;
    \\    for (int i = 0; i < 14; i++) {
    \\        float fi = float(i);
    \\        float r = (fi + 0.5) / 14.0;
    \\        float a = fi * 2.39996;
    \\        vec3 dir = vec3(cos(a) * r, sin(a) * r, sqrt(max(1.0 - r * r, 0.0)));
    \\        float k = mix(0.12, 1.0, (fi / 14.0) * (fi / 14.0));
    \\        vec3 s = p + (t * dir.x + b * dir.y + n * dir.z) * rad * k;
    \\        vec2 q = (s.xy / -s.z) / proj * 0.5 + 0.5;
    \\        if (q.x < 0.0 || q.x > 1.0 || q.y < 0.0 || q.y > 1.0) continue;
    \\        float sz = -lin(texture(depthTex, q).r);
    \\        float range = smoothstep(0.0, 1.0, rad / max(abs(p.z - sz), 1e-3));
    \\        occ += (sz >= s.z + 0.025 * (-p.z * 0.02 + 1.0) ? 1.0 : 0.0) * range;
    \\    }
    \\    float ao = 1.0 - clamp(occ / 14.0 * 1.7, 0.0, 1.0);
    \\    ao = mix(ao, 1.0, smoothstep(70.0, 140.0, -p.z));
    \\    finalColor = vec4(vec3(pow(clamp(ao, 0.0, 1.0), 1.8)), 1.0);
    \\}
;

const blur_fs = "#version 330\nin vec2 uv;\nout vec4 finalColor;\nuniform sampler2D aoTex;\nuniform sampler2D depthTex;\nuniform vec2 dir;\n" ++ post_lin ++
    \\void main() {
    \\    float center = lin(texture(depthTex, uv).r);
    \\    float sum = 0.0;
    \\    float wsum = 0.0;
    \\    for (int i = -4; i <= 4; i++) {
    \\        vec2 o = uv + dir * float(i);
    \\        float dz = lin(texture(depthTex, o).r) - center;
    \\        float w = exp(-float(i * i) / 10.0) * exp(-dz * dz / (0.0015 * center * center + 0.004));
    \\        sum += texture(aoTex, o).r * w;
    \\        wsum += w;
    \\    }
    \\    float bl = sum / max(wsum, 1e-4);
    \\    if (isnan(bl) || isinf(bl)) bl = 1.0;
    \\    finalColor = vec4(vec3(bl), 1.0);
    \\}
;

const down_fs =
    \\#version 330
    \\in vec2 uv;
    \\out vec4 finalColor;
    \\uniform sampler2D src;
    \\uniform vec2 texel;
    \\uniform float prefilter;
    \\uniform float threshold;
    \\void main() {
    \\    vec3 s0 = texture(src, uv).rgb;
    \\    vec3 s1 = texture(src, uv + vec2(-1.0, -1.0) * texel).rgb;
    \\    vec3 s2 = texture(src, uv + vec2(1.0, -1.0) * texel).rgb;
    \\    vec3 s3 = texture(src, uv + vec2(-1.0, 1.0) * texel).rgb;
    \\    vec3 s4 = texture(src, uv + vec2(1.0, 1.0) * texel).rgb;
    \\    vec3 c;
    \\    if (prefilter > 0.5) {
    \\        vec3 lw = vec3(0.2126, 0.7152, 0.0722);
    \\        float w0 = 2.0 / (1.0 + dot(min(s0, vec3(24.0)), lw));
    \\        float w1 = 0.5 / (1.0 + dot(min(s1, vec3(24.0)), lw));
    \\        float w2 = 0.5 / (1.0 + dot(min(s2, vec3(24.0)), lw));
    \\        float w3 = 0.5 / (1.0 + dot(min(s3, vec3(24.0)), lw));
    \\        float w4 = 0.5 / (1.0 + dot(min(s4, vec3(24.0)), lw));
    \\        c = (s0 * w0 + s1 * w1 + s2 * w2 + s3 * w3 + s4 * w4) / (w0 + w1 + w2 + w3 + w4);
    \\    } else {
    \\        c = s0 * 0.5 + (s1 + s2 + s3 + s4) * 0.125;
    \\    }
    \\    if (any(isnan(c)) || any(isinf(c))) c = vec3(0.0);
    \\    if (prefilter > 0.5) {
    \\        c = clamp(c, vec3(0.0), vec3(24.0));
    \\        float br = max(c.r, max(c.g, c.b));
    \\        float knee = threshold * 0.5;
    \\        float soft = clamp(br - threshold + knee, 0.0, 2.0 * knee);
    \\        soft = soft * soft / (4.0 * knee + 1e-4);
    \\        c *= max(soft, br - threshold) / max(br, 1e-4);
    \\        c = min(c, vec3(40.0));
    \\    }
    \\    finalColor = vec4(c, 1.0);
    \\}
;

const up_fs =
    \\#version 330
    \\in vec2 uv;
    \\out vec4 finalColor;
    \\uniform sampler2D src;
    \\uniform vec2 texel;
    \\void main() {
    \\    vec3 c = texture(src, uv).rgb * 4.0;
    \\    c += texture(src, uv + vec2(-texel.x, 0.0)).rgb * 2.0;
    \\    c += texture(src, uv + vec2(texel.x, 0.0)).rgb * 2.0;
    \\    c += texture(src, uv + vec2(0.0, -texel.y)).rgb * 2.0;
    \\    c += texture(src, uv + vec2(0.0, texel.y)).rgb * 2.0;
    \\    c += texture(src, uv - texel).rgb;
    \\    c += texture(src, uv + texel).rgb;
    \\    c += texture(src, uv + vec2(texel.x, -texel.y)).rgb;
    \\    c += texture(src, uv + vec2(-texel.x, texel.y)).rgb;
    \\    finalColor = vec4(c / 16.0, 1.0);
    \\}
;

const composite_fs =
    \\#version 330
    \\in vec2 uv;
    \\out vec4 finalColor;
    \\uniform sampler2D texture0;
    \\uniform sampler2D depthTex;
    \\uniform sampler2D aoTex;
    \\uniform sampler2D bloomTex;
    \\uniform float exposure;
    \\uniform vec3 gradeTint;
    \\uniform float gradeSat;
    \\uniform float bloomStrength;
    \\uniform float aoStrength;
    \\uniform float vmMask;
    \\uniform float sharpen;
    \\uniform vec2 clip;
    \\float lin(float d) {
    \\    float z = d * 2.0 - 1.0;
    \\    return 2.0 * clip.x * clip.y / (clip.y + clip.x - z * (clip.y - clip.x));
    \\}
    \\float upAO() {
    \\    vec2 size = vec2(textureSize(aoTex, 0));
    \\    vec2 st = uv * size - 0.5;
    \\    vec2 base = floor(st);
    \\    vec2 f = st - base;
    \\    float dc = lin(texture(depthTex, uv).r);
    \\    float sum = 0.0;
    \\    float wsum = 0.0;
    \\    for (int i = 0; i < 4; i++) {
    \\        vec2 o = vec2(float(i % 2), float(i / 2));
    \\        vec2 q = (base + o + 0.5) / size;
    \\        float bw = (o.x > 0.5 ? f.x : 1.0 - f.x) * (o.y > 0.5 ? f.y : 1.0 - f.y);
    \\        float dq = lin(texture(depthTex, q).r);
    \\        float w = bw * (1.0 / (0.0005 + abs(dq - dc) / max(dc, 0.1)));
    \\        float a = texture(aoTex, q).r;
    \\        if (isnan(a) || isinf(a)) a = 1.0;
    \\        sum += a * w;
    \\        wsum += w;
    \\    }
    \\    return wsum > 0.0 ? sum / wsum : 1.0;
    \\}
    \\void main() {
    \\    vec3 c = texture(texture0, uv).rgb;
    \\    if (any(isnan(c)) || any(isinf(c))) c = vec3(0.0);
    \\    c = clamp(c, vec3(0.0), vec3(24.0));
    \\    if (sharpen > 0.0) {
    \\        vec2 px = 1.0 / vec2(textureSize(texture0, 0));
    \\        vec3 n = clamp(texture(texture0, uv + vec2(0.0, px.y)).rgb, 0.0, 24.0);
    \\        vec3 so = clamp(texture(texture0, uv - vec2(0.0, px.y)).rgb, 0.0, 24.0);
    \\        vec3 e = clamp(texture(texture0, uv + vec2(px.x, 0.0)).rgb, 0.0, 24.0);
    \\        vec3 w = clamp(texture(texture0, uv - vec2(px.x, 0.0)).rgb, 0.0, 24.0);
    \\        vec3 lo = min(c, min(min(n, so), min(e, w)));
    \\        vec3 hi = max(c, max(max(n, so), max(e, w)));
    \\        vec3 amp = clamp(min(lo, 2.0 - hi) / max(hi, 1e-4), 0.0, 1.0);
    \\        vec3 wgt = -sqrt(amp) * sharpen;
    \\        vec3 sh = (c + (n + so + e + w) * wgt) / (1.0 + 4.0 * wgt);
    \\        if (!any(isnan(sh))) c = clamp(sh, lo, hi);
    \\    }
    \\    if (aoStrength > 0.0) {
    \\        float a = clamp(upAO(), 0.0, 1.0);
    \\        if (vmMask > 0.5 && texture(depthTex, uv).r < 0.99999) a = 1.0;
    \\        float lum = dot(c, vec3(0.2126, 0.7152, 0.0722));
    \\        c *= mix(1.0, a, aoStrength * (1.0 - smoothstep(0.5, 1.8, lum) * 0.6));
    \\    }
    \\    if (bloomStrength > 0.0) c += texture(bloomTex, uv).rgb * bloomStrength;
    \\    c *= exposure;
    \\    c = clamp((c * (2.51 * c + 0.03)) / (c * (2.43 * c + 0.59) + 0.14), 0.0, 1.0);
    \\    float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
    \\    float chroma = max(c.r, max(c.g, c.b)) - min(c.r, min(c.g, c.b));
    \\    c = mix(vec3(l), c, gradeSat + (1.0 - chroma) * 0.12);
    \\    c *= mix(vec3(0.975, 0.99, 1.03), vec3(1.025, 1.0, 0.965), smoothstep(0.12, 0.7, l));
    \\    c = mix(c, c * c * (3.0 - 2.0 * c), 0.17);
    \\    c = max(c - 0.008, 0.0) * 1.008;
    \\    c *= gradeTint;
    \\    vec2 vd = uv - 0.5;
    \\    c *= mix(1.0, 0.9, smoothstep(0.35, 0.9, dot(vd, vd) * 2.6));
    \\    c = pow(clamp(c, 0.0, 1.0), vec3(1.0 / 2.2));
    \\    finalColor = vec4(c, 1.0);
    \\}
;

const fxaa_fs =
    \\#version 330
    \\in vec2 uv;
    \\out vec4 finalColor;
    \\uniform sampler2D src;
    \\uniform vec2 texel;
    \\void main() {
    \\    vec3 luma = vec3(0.299, 0.587, 0.114);
    \\    vec3 rgbM = texture(src, uv).rgb;
    \\    float lNW = dot(texture(src, uv + vec2(-1.0, -1.0) * texel).rgb, luma);
    \\    float lNE = dot(texture(src, uv + vec2(1.0, -1.0) * texel).rgb, luma);
    \\    float lSW = dot(texture(src, uv + vec2(-1.0, 1.0) * texel).rgb, luma);
    \\    float lSE = dot(texture(src, uv + vec2(1.0, 1.0) * texel).rgb, luma);
    \\    float lM = dot(rgbM, luma);
    \\    float lMin = min(lM, min(min(lNW, lNE), min(lSW, lSE)));
    \\    float lMax = max(lM, max(max(lNW, lNE), max(lSW, lSE)));
    \\    vec2 d = vec2(-((lNW + lNE) - (lSW + lSE)), (lNW + lSW) - (lNE + lSE));
    \\    float reduce = max((lNW + lNE + lSW + lSE) * 0.03125, 1.0 / 128.0);
    \\    float rcp = 1.0 / (min(abs(d.x), abs(d.y)) + reduce);
    \\    d = clamp(d * rcp, vec2(-8.0), vec2(8.0)) * texel;
    \\    vec3 a = 0.5 * (texture(src, uv + d * (1.0 / 3.0 - 0.5)).rgb + texture(src, uv + d * (2.0 / 3.0 - 0.5)).rgb);
    \\    vec3 b = a * 0.5 + 0.25 * (texture(src, uv - d * 0.5).rgb + texture(src, uv + d * 0.5).rgb);
    \\    float lB = dot(b, luma);
    \\    finalColor = vec4((lB < lMin || lB > lMax) ? a : b, 1.0);
    \\}
;

const Target = struct {
    fbo: c_uint = 0,
    tex: c_uint = 0,
    w: c_int = 0,
    h: c_int = 0,
};

pub const Finish = struct {
    exposure: f32,
    tint: [3]f32,
    sat: f32,
    bloom: f32,
    ao: f32,
    vm_mask: bool,
    fxaa: bool,
};

const bloom_levels = 5;

pub const Post = struct {
    loaded: bool = false,
    w: c_int = 0,
    h: c_int = 0,
    sw: c_int = 0,
    sh: c_int = 0,
    scale: f32 = 0,
    scene_fbo: c_uint = 0,
    scene_color: c_uint = 0,
    scene_depth: c_uint = 0,
    ms_fbo: c_uint = 0,
    ms_color: c_uint = 0,
    ms_depth: c_uint = 0,
    samples: c_int = 4,
    ao: [2]Target = .{ .{}, .{} },
    blooms: [bloom_levels]Target = @splat(.{}),
    ldr: Target = .{},
    ssao_sh: rl.Shader = undefined,
    blur_sh: rl.Shader = undefined,
    down_sh: rl.Shader = undefined,
    up_sh: rl.Shader = undefined,
    comp_sh: rl.Shader = undefined,
    fxaa_sh: rl.Shader = undefined,

    pub fn ensure(p: *Post, scale: f32) bool {
        const sw = rl.GetRenderWidth();
        const sh = rl.GetRenderHeight();

        if (sw < 8 or sh < 8) return false;

        if (!p.loaded) {
            p.ssao_sh = shader(post_vs, ssao_fs);
            p.blur_sh = shader(post_vs, blur_fs);
            p.down_sh = shader(post_vs, down_fs);
            p.up_sh = shader(post_vs, up_fs);
            p.comp_sh = shader(post_vs, composite_fs);
            p.fxaa_sh = shader(post_vs, fxaa_fs);
            p.loaded = true;
        }

        if (sw == p.sw and sh == p.sh and scale == p.scale and p.scene_fbo != 0) return true;

        p.release();
        p.sw = sw;
        p.sh = sh;
        p.scale = scale;
        p.w = @max(8, @as(c_int, @intFromFloat(@as(f32, @floatFromInt(sw)) * scale)));
        p.h = @max(8, @as(c_int, @intFromFloat(@as(f32, @floatFromInt(sh)) * scale)));

        const hdr = rl.PIXELFORMAT_UNCOMPRESSED_R16G16B16A16;

        p.scene_fbo = rlgl.rlLoadFramebuffer();
        rlgl.rlEnableFramebuffer(p.scene_fbo);
        p.scene_color = rlgl.rlLoadTexture(null, p.w, p.h, hdr, 1);
        filter(p.scene_color);
        glGenTextures(1, &p.scene_depth);
        glBindTexture(gl_texture_2d, p.scene_depth);
        glTexImage2D(gl_texture_2d, 0, @intCast(gl_depth_component24), p.w, p.h, 0, gl_depth_component, gl_unsigned_int, null);
        glTexParameteri(gl_texture_2d, 0x2801, @intCast(gl_nearest));
        glTexParameteri(gl_texture_2d, 0x2800, @intCast(gl_nearest));
        glTexParameteri(gl_texture_2d, 0x2802, 0x812F);
        glTexParameteri(gl_texture_2d, 0x2803, 0x812F);
        glBindTexture(gl_texture_2d, 0);
        rlgl.rlFramebufferAttach(p.scene_fbo, p.scene_color, rlgl.RL_ATTACHMENT_COLOR_CHANNEL0, rlgl.RL_ATTACHMENT_TEXTURE2D, 0);
        glBindFramebuffer(gl_framebuffer, p.scene_fbo);
        glFramebufferTexture2D(gl_framebuffer, gl_depth_attachment, gl_texture_2d, p.scene_depth, 0);
        _ = rlgl.rlFramebufferComplete(p.scene_fbo);
        rlgl.rlDisableFramebuffer();

        if (p.samples > 1) p.loadMultisample();

        for (&p.ao) |*t| t.* = target(@divTrunc(p.w, 2), @divTrunc(p.h, 2), rl.PIXELFORMAT_UNCOMPRESSED_R8G8B8A8);

        var bw = @divTrunc(p.w, 2);
        var bh = @divTrunc(p.h, 2);

        for (&p.blooms) |*t| {
            t.* = target(@max(bw, 2), @max(bh, 2), hdr);
            bw = @divTrunc(bw, 2);
            bh = @divTrunc(bh, 2);
        }

        p.ldr = target(sw, sh, rl.PIXELFORMAT_UNCOMPRESSED_R8G8B8A8);

        return true;
    }

    fn loadMultisample(p: *Post) void {
        glGenFramebuffers(1, &p.ms_fbo);
        glBindFramebuffer(gl_framebuffer, p.ms_fbo);
        glGenRenderbuffers(1, &p.ms_color);
        glBindRenderbuffer(gl_renderbuffer, p.ms_color);
        glRenderbufferStorageMultisample(gl_renderbuffer, p.samples, gl_rgba16f, p.w, p.h);
        glFramebufferRenderbuffer(gl_framebuffer, gl_color_attachment0, gl_renderbuffer, p.ms_color);
        glGenRenderbuffers(1, &p.ms_depth);
        glBindRenderbuffer(gl_renderbuffer, p.ms_depth);
        glRenderbufferStorageMultisample(gl_renderbuffer, p.samples, gl_depth_component24, p.w, p.h);
        glFramebufferRenderbuffer(gl_framebuffer, gl_depth_attachment, gl_renderbuffer, p.ms_depth);
        glBindRenderbuffer(gl_renderbuffer, 0);

        const ok = glCheckFramebufferStatus(gl_framebuffer) == gl_framebuffer_complete;

        glBindFramebuffer(gl_framebuffer, 0);

        if (!ok) p.dropMultisample();
    }

    fn dropMultisample(p: *Post) void {
        if (p.ms_fbo != 0) glDeleteFramebuffers(1, &p.ms_fbo);
        if (p.ms_color != 0) glDeleteRenderbuffers(1, &p.ms_color);
        if (p.ms_depth != 0) glDeleteRenderbuffers(1, &p.ms_depth);

        p.ms_fbo = 0;
        p.ms_color = 0;
        p.ms_depth = 0;
    }

    pub fn resolve(p: *Post) void {
        if (p.ms_fbo == 0) return;

        rlgl.rlDrawRenderBatchActive();
        glBindFramebuffer(gl_read_framebuffer, p.ms_fbo);
        glBindFramebuffer(gl_draw_framebuffer, p.scene_fbo);
        glBlitFramebuffer(0, 0, p.w, p.h, 0, 0, p.w, p.h, gl_color_buffer_bit | gl_depth_buffer_bit, gl_nearest);

        if (glGetError() != 0) {
            glBindFramebuffer(gl_framebuffer, 0);
            p.dropMultisample();

            return;
        }

        glBindFramebuffer(gl_framebuffer, 0);
    }

    fn release(p: *Post) void {
        if (p.scene_fbo == 0) return;

        p.dropMultisample();

        rlgl.rlUnloadFramebuffer(p.scene_fbo);
        rlgl.rlUnloadTexture(p.scene_color);
        rlgl.rlUnloadTexture(p.scene_depth);

        for (&p.ao) |*t| drop(t);

        for (&p.blooms) |*t| drop(t);

        drop(&p.ldr);
        p.scene_fbo = 0;
    }

    pub fn bindScene(p: *Post) void {
        rlgl.rlDrawRenderBatchActive();
        rlgl.rlEnableFramebuffer(if (p.ms_fbo != 0) p.ms_fbo else p.scene_fbo);
        rlgl.rlViewport(0, 0, p.w, p.h);
    }

    pub fn ambientOcclusion(p: *Post, fovy: f32) void {

        const tan_half = @tan(fovy * std.math.pi / 360);
        const aspect = @as(f32, @floatFromInt(p.w)) / @as(f32, @floatFromInt(p.h));
        const proj = [2]f32{ tan_half * aspect, tan_half };
        const clip = [2]f32{ near_plane, far_plane };
        const radius: f32 = 1.25;
        const a = p.ao[0];
        const b = p.ao[1];
        const tx = 1 / @as(f32, @floatFromInt(a.w));
        const ty = 1 / @as(f32, @floatFromInt(a.h));

        begin(p.ssao_sh, a);
        sampler(p.ssao_sh, "depthTex", p.scene_depth);
        vec2(p.ssao_sh, "proj", proj);
        vec2(p.ssao_sh, "clip", clip);
        float(p.ssao_sh, "radius", radius);
        quad();

        begin(p.blur_sh, b);
        sampler(p.blur_sh, "aoTex", a.tex);
        sampler(p.blur_sh, "depthTex", p.scene_depth);
        vec2(p.blur_sh, "dir", .{ tx, 0 });
        vec2(p.blur_sh, "clip", clip);
        quad();

        begin(p.blur_sh, a);
        sampler(p.blur_sh, "aoTex", b.tex);
        sampler(p.blur_sh, "depthTex", p.scene_depth);
        vec2(p.blur_sh, "dir", .{ 0, ty });
        vec2(p.blur_sh, "clip", clip);
        quad();
        done();
    }

    pub fn finish(p: *Post, f: Finish) void {
        if (f.bloom > 0) {
            var src_tex = p.scene_color;
            var src_w = p.w;
            var src_h = p.h;

            for (p.blooms, 0..) |t, i| {
                begin(p.down_sh, t);
                sampler(p.down_sh, "src", src_tex);
                vec2(p.down_sh, "texel", .{ 1 / @as(f32, @floatFromInt(src_w)), 1 / @as(f32, @floatFromInt(src_h)) });
                float(p.down_sh, "prefilter", if (i == 0) 1 else 0);
                float(p.down_sh, "threshold", 3.2);
                quad();
                src_tex = t.tex;
                src_w = t.w;
                src_h = t.h;
            }

            additive = true;
            rlgl.rlEnableColorBlend();
            rlgl.rlSetBlendMode(rlgl.RL_BLEND_ADDITIVE);

            var i: usize = bloom_levels - 1;

            while (i > 0) : (i -= 1) {
                const src = p.blooms[i];

                begin(p.up_sh, p.blooms[i - 1]);
                sampler(p.up_sh, "src", src.tex);
                vec2(p.up_sh, "texel", .{ 1 / @as(f32, @floatFromInt(src.w)), 1 / @as(f32, @floatFromInt(src.h)) });
                quad();
            }

            additive = false;
            rlgl.rlDisableColorBlend();
        }

        const out: Target = if (f.fxaa) p.ldr else .{ .w = p.sw, .h = p.sh };

        begin(p.comp_sh, out);
        main_tex = p.scene_color;
        sampler(p.comp_sh, "depthTex", p.scene_depth);
        sampler(p.comp_sh, "aoTex", p.ao[0].tex);
        sampler(p.comp_sh, "bloomTex", p.blooms[0].tex);
        float(p.comp_sh, "exposure", f.exposure);
        vec3(p.comp_sh, "gradeTint", f.tint);
        float(p.comp_sh, "gradeSat", f.sat);
        float(p.comp_sh, "bloomStrength", f.bloom);
        float(p.comp_sh, "aoStrength", f.ao);
        float(p.comp_sh, "vmMask", if (f.vm_mask) 1 else 0);
        float(p.comp_sh, "sharpen", sharpen_amount);
        vec2(p.comp_sh, "clip", .{ near_plane, far_plane });
        quad();

        if (f.fxaa) {
            begin(p.fxaa_sh, .{ .w = p.sw, .h = p.sh });
            sampler(p.fxaa_sh, "src", p.ldr.tex);
            vec2(p.fxaa_sh, "texel", .{ 1 / @as(f32, @floatFromInt(p.sw)), 1 / @as(f32, @floatFromInt(p.sh)) });
            quad();
        }

        done();
        rlgl.rlDisableFramebuffer();
        rlgl.rlViewport(0, 0, p.sw, p.sh);
    }
};

fn filter(tex: c_uint) void {
    rlgl.rlTextureParameters(tex, rlgl.RL_TEXTURE_MIN_FILTER, rlgl.RL_TEXTURE_FILTER_LINEAR);
    rlgl.rlTextureParameters(tex, rlgl.RL_TEXTURE_MAG_FILTER, rlgl.RL_TEXTURE_FILTER_LINEAR);
    rlgl.rlTextureParameters(tex, rlgl.RL_TEXTURE_WRAP_S, rlgl.RL_TEXTURE_WRAP_CLAMP);
    rlgl.rlTextureParameters(tex, rlgl.RL_TEXTURE_WRAP_T, rlgl.RL_TEXTURE_WRAP_CLAMP);
}

fn target(w: c_int, h: c_int, format: c_int) Target {
    const fbo = rlgl.rlLoadFramebuffer();

    rlgl.rlEnableFramebuffer(fbo);

    const tex = rlgl.rlLoadTexture(null, w, h, format, 1);

    filter(tex);
    rlgl.rlFramebufferAttach(fbo, tex, rlgl.RL_ATTACHMENT_COLOR_CHANNEL0, rlgl.RL_ATTACHMENT_TEXTURE2D, 0);
    _ = rlgl.rlFramebufferComplete(fbo);
    rlgl.rlDisableFramebuffer();

    return .{ .fbo = fbo, .tex = tex, .w = w, .h = h };
}

fn drop(t: *Target) void {
    if (t.fbo != 0) rlgl.rlUnloadFramebuffer(t.fbo);

    if (t.tex != 0) rlgl.rlUnloadTexture(t.tex);

    t.* = .{};
}

var additive = false;


fn begin(sh: rl.Shader, t: Target) void {
    rlgl.rlDrawRenderBatchActive();

    if (t.fbo != 0) rlgl.rlEnableFramebuffer(t.fbo) else rlgl.rlDisableFramebuffer();

    rlgl.rlViewport(0, 0, t.w, t.h);
    rlgl.rlDisableDepthTest();
    rlgl.rlDisableBackfaceCulling();

    if (!additive) rlgl.rlDisableColorBlend();

    rlgl.rlSetShader(sh.id, sh.locs);
    rlgl.rlEnableShader(sh.id);
}

fn sampler(sh: rl.Shader, name: [:0]const u8, tex: c_uint) void {
    rlgl.rlSetUniformSampler(rl.GetShaderLocation(sh, name.ptr), tex);
}

fn float(sh: rl.Shader, name: [:0]const u8, v: f32) void {
    rlgl.rlSetUniform(rl.GetShaderLocation(sh, name.ptr), &v, rl.SHADER_UNIFORM_FLOAT, 1);
}

fn vec2(sh: rl.Shader, name: [:0]const u8, v: [2]f32) void {
    rlgl.rlSetUniform(rl.GetShaderLocation(sh, name.ptr), &v, rl.SHADER_UNIFORM_VEC2, 1);
}

fn vec3(sh: rl.Shader, name: [:0]const u8, v: [3]f32) void {
    rlgl.rlSetUniform(rl.GetShaderLocation(sh, name.ptr), &v, rl.SHADER_UNIFORM_VEC3, 1);
}

var main_tex: c_uint = 0;

fn quad() void {
    rlgl.rlSetTexture(if (main_tex != 0) main_tex else rlgl.rlGetTextureIdDefault());
    main_tex = 0;
    rlgl.rlBegin(rlgl.RL_QUADS);
    rlgl.rlColor4ub(255, 255, 255, 255);
    rlgl.rlTexCoord2f(0, 0);
    rlgl.rlVertex2f(-1, -1);
    rlgl.rlTexCoord2f(1, 0);
    rlgl.rlVertex2f(1, -1);
    rlgl.rlTexCoord2f(1, 1);
    rlgl.rlVertex2f(1, 1);
    rlgl.rlTexCoord2f(0, 1);
    rlgl.rlVertex2f(-1, 1);
    rlgl.rlEnd();
    rlgl.rlDrawRenderBatchActive();
    rlgl.rlSetTexture(0);
}

fn done() void {
    rlgl.rlDrawRenderBatchActive();
    rlgl.rlSetShader(rlgl.rlGetShaderIdDefault(), rlgl.rlGetShaderLocsDefault());
    rlgl.rlEnableColorBlend();
    rlgl.rlSetBlendMode(rlgl.RL_BLEND_ALPHA);
    rlgl.rlEnableBackfaceCulling();
}

const glow_vs =
    \\#version 330
    \\in vec3 vertexPosition;
    \\in vec2 vertexTexCoord;
    \\in vec4 vertexColor;
    \\uniform mat4 mvp;
    \\out vec2 uv;
    \\void main() {
    \\    uv = vertexTexCoord;
    \\    gl_Position = mvp * vec4(vertexPosition, 1.0);
    \\}
;

const glow_bright_fs =
    \\#version 330
    \\in vec2 uv;
    \\uniform sampler2D texture0;
    \\uniform vec2 texel;
    \\out vec4 finalColor;
    \\void main() {
    \\    vec3 c = texture(texture0, uv).rgb * 0.25;
    \\    c += texture(texture0, uv + vec2(texel.x, 0.0)).rgb * 0.25;
    \\    c += texture(texture0, uv + vec2(0.0, texel.y)).rgb * 0.25;
    \\    c += texture(texture0, uv + texel).rgb * 0.25;
    \\    float l = max(max(c.r, c.g), c.b);
    \\    finalColor = vec4(c * smoothstep(0.84, 0.99, l), 1.0);
    \\}
;

const glow_blur_fs =
    \\#version 330
    \\in vec2 uv;
    \\uniform sampler2D texture0;
    \\uniform vec2 dirStep;
    \\out vec4 finalColor;
    \\void main() {
    \\    vec3 c = texture(texture0, uv).rgb * 0.227;
    \\    c += texture(texture0, uv + dirStep * 1.385).rgb * 0.316;
    \\    c += texture(texture0, uv - dirStep * 1.385).rgb * 0.316;
    \\    c += texture(texture0, uv + dirStep * 3.231).rgb * 0.07;
    \\    c += texture(texture0, uv - dirStep * 3.231).rgb * 0.07;
    \\    finalColor = vec4(c, 1.0);
    \\}
;

pub const Glow = struct {
    bright: ?rl.Shader = null,
    blur: rl.Shader = undefined,
    a: ?rl.RenderTexture2D = null,
    b: rl.RenderTexture2D = undefined,
    strength: f32 = 0.8,

    fn pass(sh: rl.Shader, src: rl.Texture2D, dst: rl.RenderTexture2D) void {
        const from: rl.Rectangle = .{ .x = 0, .y = 0, .width = @floatFromInt(src.width), .height = @floatFromInt(-src.height) };
        const to: rl.Rectangle = .{ .x = 0, .y = 0, .width = @floatFromInt(dst.texture.width), .height = @floatFromInt(dst.texture.height) };

        rl.BeginTextureMode(dst);
        rl.ClearBackground(.{ .r = 0, .g = 0, .b = 0, .a = 255 });
        rl.BeginShaderMode(sh);
        rl.DrawTexturePro(src, from, to, .{}, 0, rl.WHITE);
        rl.EndShaderMode();
        rl.EndTextureMode();
    }

    pub fn process(g: *Glow, scene: rl.Texture2D) void {
        if (g.bright == null) {
            g.bright = shader(glow_vs, glow_bright_fs);
            g.blur = shader(glow_vs, glow_blur_fs);
        }

        const w = @max(16, @divTrunc(scene.width, 4));
        const h = @max(16, @divTrunc(scene.height, 4));

        if (g.a) |t| {
            if (t.texture.width != w or t.texture.height != h) {
                rl.UnloadRenderTexture(t);
                rl.UnloadRenderTexture(g.b);
                g.a = null;
            }
        }

        if (g.a == null) {
            g.a = rl.LoadRenderTexture(w, h);
            g.b = rl.LoadRenderTexture(w, h);
            rl.SetTextureFilter(g.a.?.texture, rl.TEXTURE_FILTER_BILINEAR);
            rl.SetTextureFilter(g.b.texture, rl.TEXTURE_FILTER_BILINEAR);
        }

        const a = g.a.?;
        const bright = g.bright.?;
        const texel = [2]f32{ 1.0 / @as(f32, @floatFromInt(scene.width)), 1.0 / @as(f32, @floatFromInt(scene.height)) };
        const step_loc = rl.GetShaderLocation(g.blur, "dirStep");
        const tx = 1.0 / @as(f32, @floatFromInt(w));
        const ty = 1.0 / @as(f32, @floatFromInt(h));

        rl.SetShaderValue(bright, rl.GetShaderLocation(bright, "texel"), &texel, rl.SHADER_UNIFORM_VEC2);
        pass(bright, scene, a);

        for ([_]f32{ 1, 2.2 }) |k| {
            const hs = [2]f32{ tx * k, 0 };
            const vs = [2]f32{ 0, ty * k };

            rl.SetShaderValue(g.blur, step_loc, &hs, rl.SHADER_UNIFORM_VEC2);
            pass(g.blur, a.texture, g.b);
            rl.SetShaderValue(g.blur, step_loc, &vs, rl.SHADER_UNIFORM_VEC2);
            pass(g.blur, g.b.texture, a);
        }
    }

    pub fn composite(g: *Glow) void {
        const a = g.a orelse return;
        const from: rl.Rectangle = .{ .x = 0, .y = 0, .width = @floatFromInt(a.texture.width), .height = @floatFromInt(-a.texture.height) };
        const to: rl.Rectangle = .{ .x = 0, .y = 0, .width = @floatFromInt(rl.GetScreenWidth()), .height = @floatFromInt(rl.GetScreenHeight()) };
        const k: u8 = @intFromFloat(std.math.clamp(g.strength, 0, 1) * 255);

        rl.BeginBlendMode(rl.BLEND_ADDITIVE);
        rl.DrawTexturePro(a.texture, from, to, .{}, 0, .{ .r = k, .g = k, .b = k, .a = 255 });
        rl.EndBlendMode();
    }
};
