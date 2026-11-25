const std = @import("std");
const rl = @import("raylib");
const shared = @import("shared");
const palette = @import("palette.zig");

const Vec3 = shared.math.Vec3;
const geom = shared.geom;

pub const Style = struct {
    color: palette.Rgb = .{ 240, 240, 240 },
    glow: u8 = 0,
};

pub const Basis = struct {
    x: Vec3,
    y: Vec3,
    z: Vec3,

    pub const world: Basis = .{
        .x = .{ .x = 1 },
        .y = .{ .y = 1 },
        .z = .{ .z = 1 },
    };

    pub fn yawed(yaw: f32) Basis {
        const c = @cos(yaw);
        const s = @sin(yaw);

        return .{
            .x = .{ .x = c, .z = -s },
            .y = .{ .y = 1 },
            .z = .{ .x = s, .z = c },
        };
    }

    pub fn facing(forward: Vec3) Basis {
        const back = forward.normalize().neg();
        const ref: Vec3 = if (@abs(back.y) > 0.95) .{ .x = 1 } else .{ .y = 1 };
        const x = ref.cross(back).normalize();

        return .{ .x = x, .y = back.cross(x), .z = back };
    }
};

pub fn transform(origin: Vec3, basis: Basis, s: f32) rl.Matrix {
    return .{
        .m0 = basis.x.x * s,
        .m1 = basis.x.y * s,
        .m2 = basis.x.z * s,
        .m4 = basis.y.x * s,
        .m5 = basis.y.y * s,
        .m6 = basis.y.z * s,
        .m8 = basis.z.x * s,
        .m9 = basis.z.y * s,
        .m10 = basis.z.z * s,
        .m12 = origin.x,
        .m13 = origin.y,
        .m14 = origin.z,
        .m15 = 1,
    };
}

pub const identity = transform(.{}, Basis.world, 1);

pub fn segment(a: Vec3, b: Vec3, radius: f32) rl.Matrix {
    const d = b.sub(a);
    const len = @max(d.length(), 1e-5);
    const y = d.scale(1 / len);
    const ref: Vec3 = if (@abs(y.y) > 0.9) .{ .x = 1 } else .{ .y = 1 };
    const x = ref.cross(y).normalize();
    const z = x.cross(y);

    return .{
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
}

const max_vertices = 180_000;

var positions: []f32 = &.{};
var normals: []f32 = &.{};
var colors: []u8 = &.{};
var outlines: []f32 = &.{};

fn reserve() bool {
    if (positions.len != 0) return true;

    const a = std.heap.page_allocator;

    positions = a.alloc(f32, max_vertices * 3) catch return false;
    normals = a.alloc(f32, max_vertices * 3) catch return false;
    colors = a.alloc(u8, max_vertices * 4) catch return false;
    outlines = a.alloc(f32, max_vertices * 4) catch return false;

    return true;
}

pub fn releaseScratch() void {
    const a = std.heap.page_allocator;

    if (positions.len != 0) a.free(positions);
    if (normals.len != 0) a.free(normals);
    if (colors.len != 0) a.free(colors);
    if (outlines.len != 0) a.free(outlines);

    positions = &.{};
    normals = &.{};
    colors = &.{};
    outlines = &.{};
}

pub fn smoothModel(model: rl.Model, max_angle_deg: f32) void {
    var i: usize = 0;

    while (i < @as(usize, @intCast(model.meshCount))) : (i += 1) smoothMesh(@ptrCast(&model.meshes[i]), max_angle_deg);
}

const Key = struct { x: i32, y: i32, z: i32 };

fn smoothMesh(m: *rl.Mesh, max_angle_deg: f32) void {
    if (m.vertices == null or m.normals == null or m.animVertices != null) return;

    const n: usize = @intCast(m.vertexCount);

    if (n == 0 or n > 400_000) return;

    const gpa = std.heap.page_allocator;
    const out = gpa.alloc(f32, n * 3) catch return;
    defer gpa.free(out);

    var groups = std.AutoHashMap(Key, std.ArrayList(u32)).init(gpa);
    defer {
        var it = groups.valueIterator();

        while (it.next()) |l| l.deinit(gpa);
        groups.deinit();
    }

    const pos = m.vertices[0 .. n * 3];
    const nor = m.normals[0 .. n * 3];
    const limit = @cos(max_angle_deg * std.math.pi / 180.0);
    var v: usize = 0;

    while (v < n) : (v += 1) {
        const key: Key = .{ .x = @intFromFloat(@round(pos[v * 3] * 2000)), .y = @intFromFloat(@round(pos[v * 3 + 1] * 2000)), .z = @intFromFloat(@round(pos[v * 3 + 2] * 2000)) };
        const entry = groups.getOrPut(key) catch return;

        if (!entry.found_existing) entry.value_ptr.* = .empty;

        entry.value_ptr.append(gpa, @intCast(v)) catch return;
    }

    var it = groups.valueIterator();

    while (it.next()) |list| {
        for (list.items) |a| {
            var sx: f32 = 0;
            var sy: f32 = 0;
            var sz: f32 = 0;

            for (list.items) |b| {
                const d = nor[a * 3] * nor[b * 3] + nor[a * 3 + 1] * nor[b * 3 + 1] + nor[a * 3 + 2] * nor[b * 3 + 2];

                if (d < limit) continue;

                sx += nor[b * 3];
                sy += nor[b * 3 + 1];
                sz += nor[b * 3 + 2];
            }

            const len = @sqrt(sx * sx + sy * sy + sz * sz);

            if (len < 1e-6) {
                out[a * 3] = nor[a * 3];
                out[a * 3 + 1] = nor[a * 3 + 1];
                out[a * 3 + 2] = nor[a * 3 + 2];
            } else {
                out[a * 3] = sx / len;
                out[a * 3 + 1] = sy / len;
                out[a * 3 + 2] = sz / len;
            }
        }
    }

    @memcpy(nor, out);

    if (m.vboId != null) rl.UpdateMeshBuffer(m.*, 2, m.normals, @intCast(n * 3 * @sizeOf(f32)), 0);
}

pub fn dropCpu(model: rl.Model) void {
    var i: usize = 0;

    while (i < @as(usize, @intCast(model.meshCount))) : (i += 1) {
        const m = &model.meshes[i];

        if (m.animVertices != null or m.vboId == null) continue;

        rl.MemFree(m.vertices);
        rl.MemFree(m.texcoords);
        rl.MemFree(m.texcoords2);
        rl.MemFree(m.normals);
        rl.MemFree(m.tangents);
        rl.MemFree(m.colors);
        rl.MemFree(m.boneIndices);
        rl.MemFree(m.boneWeights);
        m.vertices = null;
        m.texcoords = null;
        m.texcoords2 = null;
        m.normals = null;
        m.tangents = null;
        m.colors = null;
        m.boneIndices = null;
        m.boneWeights = null;
    }
}

pub const Grime = struct {
    ceiling: f32 = 1e9,
    floor: f32 = 0,
    dark: f32 = 0.42,
    span: f32 = 0,
};

fn grimeK(g: Grime, p: Vec3, n: Vec3) f32 {
    const low = std.math.clamp((p.y - g.floor) / 1.8, 0, 1);
    const floor_k = (1 - g.dark) + g.dark * low * low * (3 - 2 * low);
    const top = std.math.clamp((p.y - (g.ceiling - 4)) / 4, 0, 1);
    const under: f32 = if (n.y < -0.5) 0.72 else 1;
    const rise = if (g.span > 0) 0.9 + 0.2 * std.math.clamp((p.y - g.floor) / g.span, 0, 1) else 1;
    const up: f32 = if (g.span > 0 and n.y > 0.5) 1.06 else 1;

    return @min(1.25, floor_k * (1 - 0.32 * top) * under * rise * up);
}

pub const Builder = struct {
    count: usize = 0,
    style: Style = .{},
    grime: ?Grime = null,

    fn vertex(b: *Builder, p: Vec3, n: Vec3) void {
        if (!reserve()) return;

        const i = b.count;
        var c = b.style.color;

        if (b.grime) |g| {
            const k = grimeK(g, p, n);

            c = .{ @intFromFloat(@min(255, @as(f32, @floatFromInt(c[0])) * k)), @intFromFloat(@min(255, @as(f32, @floatFromInt(c[1])) * k)), @intFromFloat(@min(255, @as(f32, @floatFromInt(c[2])) * k)) };
        }

        positions[i * 3 ..][0..3].* = .{ p.x, p.y, p.z };
        normals[i * 3 ..][0..3].* = .{ n.x, n.y, n.z };
        colors[i * 4 ..][0..4].* = .{ c[0], c[1], c[2], 255 - b.style.glow };
        b.count += 1;
    }

    pub fn full(b: *Builder) bool {
        return b.count + 2000 > max_vertices;
    }

    pub fn bevelBox(b: *Builder, lo: Vec3, hi: Vec3, bevel_in: f32) void {
        const h = [3]f32{ (hi.x - lo.x) / 2, (hi.y - lo.y) / 2, (hi.z - lo.z) / 2 };
        const c = [3]f32{ (hi.x + lo.x) / 2, (hi.y + lo.y) / 2, (hi.z + lo.z) / 2 };
        const bevel = @min(bevel_in, @min(h[0], @min(h[1], h[2])) * 0.45);
        const e = [3]f32{ h[0] - bevel, h[1] - bevel, h[2] - bevel };
        const P = struct {
            fn v(cc: [3]f32, a: [3]f32) Vec3 {
                return .{ .x = cc[0] + a[0], .y = cc[1] + a[1], .z = cc[2] + a[2] };
            }
        };
        var ys: [6]f32 = undefined;
        var ny: usize = 0;

        ys[ny] = -e[1];
        ny += 1;

        for ([_]f32{ 0.35, 1.0, 2.2 }) |abs_y| {
            const local = lo.y + abs_y - c[1];

            if (local > ys[ny - 1] + 0.05 and local < e[1] - 0.05) {
                ys[ny] = local;
                ny += 1;
            }
        }

        ys[ny] = e[1];
        ny += 1;

        for (0..3) |a| {
            const u = (a + 1) % 3;
            const w = (a + 2) % 3;

            for ([_]f32{ -1, 1 }) |sg| {
                var nrm = [3]f32{ 0, 0, 0 };

                nrm[a] = sg;

                const n = Vec3{ .x = nrm[0], .y = nrm[1], .z = nrm[2] };

                if (a == 1) {
                    var q: [4]Vec3 = undefined;

                    for ([_][2]f32{ .{ -1, -1 }, .{ 1, -1 }, .{ 1, 1 }, .{ -1, 1 } }, 0..) |uv, k| {
                        var o = [3]f32{ 0, 0, 0 };

                        o[a] = sg * h[a];
                        o[u] = uv[0] * e[u];
                        o[w] = uv[1] * e[w];
                        q[k] = P.v(c, o);
                    }

                    b.tri(q[0], q[1], q[2], n, n, n, n);
                    b.tri(q[0], q[2], q[3], n, n, n, n);

                    continue;
                }

                const other: usize = if (u == 1) w else u;

                for (0..ny - 1) |k| {
                    var q: [4]Vec3 = undefined;

                    for ([_][2]f32{ .{ -1, 0 }, .{ 1, 0 }, .{ 1, 1 }, .{ -1, 1 } }, 0..) |uv, m| {
                        var o = [3]f32{ 0, 0, 0 };

                        o[a] = sg * h[a];
                        o[other] = uv[0] * e[other];
                        o[1] = ys[k + @as(usize, @intFromFloat(uv[1]))];
                        q[m] = P.v(c, o);
                    }

                    b.tri(q[0], q[1], q[2], n, n, n, n);
                    b.tri(q[0], q[2], q[3], n, n, n, n);
                }
            }
        }

        for (0..3) |a| {
            const u = (a + 1) % 3;
            const w = (a + 2) % 3;

            for ([_]f32{ -1, 1 }) |su| {
                for ([_]f32{ -1, 1 }) |sw| {
                    var nv = [3]f32{ 0, 0, 0 };

                    nv[u] = su;
                    nv[w] = sw;

                    const n = (Vec3{ .x = nv[0], .y = nv[1], .z = nv[2] }).normalize();
                    var o0 = [3]f32{ 0, 0, 0 };
                    var o1 = [3]f32{ 0, 0, 0 };
                    var o2 = [3]f32{ 0, 0, 0 };
                    var o3 = [3]f32{ 0, 0, 0 };

                    o0[a] = -e[a];
                    o0[u] = su * h[u];
                    o0[w] = sw * e[w];
                    o1 = o0;
                    o1[a] = e[a];
                    o2[a] = e[a];
                    o2[u] = su * e[u];
                    o2[w] = sw * h[w];
                    o3 = o2;
                    o3[a] = -e[a];

                    const q0 = P.v(c, o0);
                    const q1 = P.v(c, o1);
                    const q2 = P.v(c, o2);
                    const q3 = P.v(c, o3);

                    b.tri(q0, q1, q2, n, n, n, n);
                    b.tri(q0, q2, q3, n, n, n, n);
                }
            }
        }

        for ([_]f32{ -1, 1 }) |sx| {
            for ([_]f32{ -1, 1 }) |sy| {
                for ([_]f32{ -1, 1 }) |sz| {
                    const n = (Vec3{ .x = sx, .y = sy, .z = sz }).normalize();
                    const a0 = P.v(c, .{ sx * h[0], sy * e[1], sz * e[2] });
                    const a1 = P.v(c, .{ sx * e[0], sy * h[1], sz * e[2] });
                    const a2 = P.v(c, .{ sx * e[0], sy * e[1], sz * h[2] });

                    b.tri(a0, a1, a2, n, n, n, n);
                }
            }
        }
    }

    pub fn tri(b: *Builder, p0: Vec3, p1: Vec3, p2: Vec3, n0: Vec3, n1: Vec3, n2: Vec3, outward: Vec3) void {
        if (b.count + 3 > max_vertices) return;

        const face = p1.sub(p0).cross(p2.sub(p0));

        b.vertex(p0, n0);

        if (face.dot(outward) >= 0) {
            b.vertex(p1, n1);
            b.vertex(p2, n2);
        } else {
            b.vertex(p2, n2);
            b.vertex(p1, n1);
        }
    }

    pub fn flat(b: *Builder, p0: Vec3, p1: Vec3, p2: Vec3, hint: Vec3) void {
        var n = p1.sub(p0).cross(p2.sub(p0)).normalize();

        if (n.dot(hint) < 0) n = n.neg();

        b.tri(p0, p1, p2, n, n, n, n);
    }

    pub fn flatBlend(b: *Builder, p: [3]Vec3, c: [3]palette.Rgb, hint: Vec3) void {
        if (b.count + 3 > max_vertices) return;

        var n = p[1].sub(p[0]).cross(p[2].sub(p[0])).normalize();

        if (n.dot(hint) < 0) n = n.neg();

        const order: [3]usize = if (p[1].sub(p[0]).cross(p[2].sub(p[0])).dot(n) >= 0) .{ 0, 1, 2 } else .{ 0, 2, 1 };

        for (order) |k| {
            b.style.color = c[k];
            b.vertex(p[k], n);
        }
    }

    pub fn quad(b: *Builder, p0: Vec3, p1: Vec3, p2: Vec3, p3: Vec3, hint: Vec3) void {
        b.flat(p0, p1, p2, hint);
        b.flat(p0, p2, p3, hint);
    }

    pub fn box(b: *Builder, center: Vec3, basis: Basis, half: Vec3) void {
        const ax = basis.x.scale(half.x);
        const ay = basis.y.scale(half.y);
        const az = basis.z.scale(half.z);
        var p: [8]Vec3 = undefined;

        for (&p, 0..) |*corner, i| {
            const sx: f32 = if (i & 1 != 0) 1 else -1;
            const sy: f32 = if (i & 2 != 0) 1 else -1;
            const sz: f32 = if (i & 4 != 0) 1 else -1;

            corner.* = center.add(ax.scale(sx)).add(ay.scale(sy)).add(az.scale(sz));
        }

        b.quad(p[1], p[3], p[7], p[5], basis.x);
        b.quad(p[0], p[4], p[6], p[2], basis.x.neg());
        b.quad(p[2], p[6], p[7], p[3], basis.y);
        b.quad(p[0], p[1], p[5], p[4], basis.y.neg());
        b.quad(p[4], p[5], p[7], p[6], basis.z);
        b.quad(p[0], p[2], p[3], p[1], basis.z.neg());
    }

    pub fn aabb(b: *Builder, min: Vec3, max: Vec3) void {
        b.box(min.add(max).scale(0.5), Basis.world, max.sub(min).scale(0.5));
    }

    pub fn ramp(b: *Builder, r: geom.Ramp) void {
        const size = r.max.sub(r.min);
        const rise_dir: Vec3 = switch (r.rise) {
            .pos_x => .{ .x = 1 },
            .neg_x => .{ .x = -1 },
            .pos_z => .{ .z = 1 },
            .neg_z => .{ .z = -1 },
        };
        const across: Vec3 = switch (r.rise) {
            .pos_x, .neg_x => .{ .z = 1 },
            .pos_z, .neg_z => .{ .x = 1 },
        };
        const P = struct {
            fn at(rr: geom.Ramp, sz: Vec3, u: f32, w: f32, h: f32) Vec3 {
                const y = rr.min.y + h * sz.y;

                return switch (rr.rise) {
                    .pos_x => .{ .x = rr.min.x + u * sz.x, .y = y, .z = rr.min.z + w * sz.z },
                    .neg_x => .{ .x = rr.max.x - u * sz.x, .y = y, .z = rr.min.z + w * sz.z },
                    .pos_z => .{ .x = rr.min.x + w * sz.x, .y = y, .z = rr.min.z + u * sz.z },
                    .neg_z => .{ .x = rr.min.x + w * sz.x, .y = y, .z = rr.max.z - u * sz.z },
                };
            }
        };

        const l0 = P.at(r, size, 0, 0, 0);
        const l1 = P.at(r, size, 0, 1, 0);
        const h0 = P.at(r, size, 1, 0, 0);
        const h1 = P.at(r, size, 1, 1, 0);
        const t0 = P.at(r, size, 1, 0, 1);
        const t1 = P.at(r, size, 1, 1, 1);

        b.quad(l0, h0, h1, l1, .{ .y = -1 });
        b.quad(l0, t0, t1, l1, .{ .y = 1 });
        b.quad(h0, t0, t1, h1, rise_dir);
        b.flat(l0, h0, t0, across.neg());
        b.flat(l1, h1, t1, across);
    }

    pub fn slab(b: *Builder, x: f32, pts: []const [2]f32, half: f32, bevel: f32) void {
        var c: [2]f32 = .{ 0, 0 };

        for (pts) |p| {
            c[0] += p[0];
            c[1] += p[1];
        }

        const n: f32 = @floatFromInt(pts.len);

        c = .{ c[0] / n, c[1] / n };

        var inset: [16][2]f32 = undefined;

        for (pts, 0..) |p, i| {
            const dz = c[0] - p[0];
            const dy = c[1] - p[1];
            const len = @max(1e-6, @sqrt(dz * dz + dy * dy));
            const k = @min(bevel, len * 0.5) / len;

            inset[i] = .{ p[0] + dz * k, p[1] + dy * k };
        }

        const at = struct {
            fn v(px: f32, p: [2]f32) Vec3 {
                return .{ .x = px, .y = p[1], .z = p[0] };
            }
        }.v;
        const outer = half - bevel;
        const center_l = at(x - half, c);
        const center_r = at(x + half, c);

        for (pts, 0..) |p, i| {
            const j = (i + 1) % pts.len;
            const q = pts[j];
            const ez = q[0] - p[0];
            const ey = q[1] - p[1];
            var side: Vec3 = .{ .y = -ez, .z = ey };

            if (side.dot(at(0, .{ (p[0] + q[0]) / 2 - c[0], (p[1] + q[1]) / 2 - c[1] })) < 0) side = side.neg();

            side = side.normalize();

            b.flat(center_r, at(x + half, inset[i]), at(x + half, inset[j]), .{ .x = 1 });
            b.flat(center_l, at(x - half, inset[i]), at(x - half, inset[j]), .{ .x = -1 });
            b.quad(at(x + outer, p), at(x + outer, q), at(x - outer, q), at(x - outer, p), side);
            b.quad(at(x + half, inset[i]), at(x + half, inset[j]), at(x + outer, q), at(x + outer, p), side.add(.{ .x = 1 }));
            b.quad(at(x - half, inset[i]), at(x - half, inset[j]), at(x - outer, q), at(x - outer, p), side.add(.{ .x = -1 }));
        }
    }

    pub fn cylinder(b: *Builder, base: Vec3, top: Vec3, radius: f32, segments: u32, caps: bool) void {
        const axis = top.sub(base).normalize();
        const ref: Vec3 = if (@abs(axis.y) > 0.95) .{ .x = 1 } else .{ .y = 1 };
        const u = axis.cross(ref).normalize();
        const v = axis.cross(u);
        const step = 2 * std_pi / @as(f32, @floatFromInt(segments));
        var i: u32 = 0;

        while (i < segments) : (i += 1) {
            const a0 = step * @as(f32, @floatFromInt(i));
            const a1 = a0 + step;
            const d0 = u.scale(@cos(a0)).add(v.scale(@sin(a0)));
            const d1 = u.scale(@cos(a1)).add(v.scale(@sin(a1)));
            const out = d0.add(d1);
            const b0 = base.add(d0.scale(radius));
            const b1 = base.add(d1.scale(radius));
            const t0 = top.add(d0.scale(radius));
            const t1 = top.add(d1.scale(radius));

            b.tri(b0, b1, t1, d0, d1, d1, out);
            b.tri(b0, t1, t0, d0, d1, d0, out);

            if (caps) {
                b.flat(base, b0, b1, axis.neg());
                b.flat(top, t0, t1, axis);
            }
        }
    }

    pub fn cone(b: *Builder, base: Vec3, tip: Vec3, radius: f32, segments: u32) void {
        const axis = tip.sub(base).normalize();
        const ref: Vec3 = if (@abs(axis.y) > 0.95) .{ .x = 1 } else .{ .y = 1 };
        const u = axis.cross(ref).normalize();
        const v = axis.cross(u);
        const step = 2 * std_pi / @as(f32, @floatFromInt(segments));
        var i: u32 = 0;

        while (i < segments) : (i += 1) {
            const a0 = step * @as(f32, @floatFromInt(i));
            const a1 = a0 + step;
            const d0 = u.scale(@cos(a0)).add(v.scale(@sin(a0)));
            const d1 = u.scale(@cos(a1)).add(v.scale(@sin(a1)));
            const b0 = base.add(d0.scale(radius));
            const b1 = base.add(d1.scale(radius));

            b.flat(b0, b1, tip, d0.add(d1));
            b.flat(base, b0, b1, axis.neg());
        }
    }

    pub fn sphere(b: *Builder, center: Vec3, radius: f32, rings: u32, slices: u32) void {
        var j: u32 = 0;

        while (j < rings) : (j += 1) {
            const th0 = std_pi * @as(f32, @floatFromInt(j)) / @as(f32, @floatFromInt(rings));
            const th1 = std_pi * @as(f32, @floatFromInt(j + 1)) / @as(f32, @floatFromInt(rings));
            var i: u32 = 0;

            while (i < slices) : (i += 1) {
                const ph0 = 2 * std_pi * @as(f32, @floatFromInt(i)) / @as(f32, @floatFromInt(slices));
                const ph1 = 2 * std_pi * @as(f32, @floatFromInt(i + 1)) / @as(f32, @floatFromInt(slices));
                const n00 = polar(th0, ph0);
                const n01 = polar(th0, ph1);
                const n10 = polar(th1, ph0);
                const n11 = polar(th1, ph1);
                const out = n00.add(n01).add(n10).add(n11);
                const p00 = center.add(n00.scale(radius));
                const p01 = center.add(n01.scale(radius));
                const p10 = center.add(n10.scale(radius));
                const p11 = center.add(n11.scale(radius));

                if (j != 0) b.tri(p00, p01, p11, n00, n01, n11, out);
                if (j != rings - 1) b.tri(p00, p11, p10, n00, n11, n10, out);
            }
        }
    }

    pub fn paint(b: *Builder, p: shared.map.Paint) void {
        b.style = .{ .color = palette.of(p) };
    }

    pub fn glowing(b: *Builder, p: shared.map.Paint, glow: u8) void {
        b.style = .{ .color = palette.of(p), .glow = glow };
    }

    fn smoothOutlines(n: usize) void {
        var map: std.AutoHashMapUnmanaged([3]i32, [3]f32) = .empty;
        const gpa = std.heap.c_allocator;

        defer map.deinit(gpa);

        var i: usize = 0;

        while (i < n) : (i += 1) {
            const key = quantize(i);
            const entry = map.getOrPut(gpa, key) catch return;

            if (!entry.found_existing) entry.value_ptr.* = .{ 0, 0, 0 };

            entry.value_ptr.*[0] += normals[i * 3];
            entry.value_ptr.*[1] += normals[i * 3 + 1];
            entry.value_ptr.*[2] += normals[i * 3 + 2];
        }

        i = 0;

        while (i < n) : (i += 1) {
            const sum = map.get(quantize(i)) orelse .{ 0, 1, 0 };
            const v = (Vec3{ .x = sum[0], .y = sum[1], .z = sum[2] }).normalize();

            outlines[i * 4 ..][0..4].* = .{ v.x, v.y, v.z, 0 };
        }
    }

    fn quantize(i: usize) [3]i32 {
        return .{
            @intFromFloat(@round(positions[i * 3] * 1000)),
            @intFromFloat(@round(positions[i * 3 + 1] * 1000)),
            @intFromFloat(@round(positions[i * 3 + 2] * 1000)),
        };
    }

    pub fn finish(b: *Builder) rl.Mesh {
        const n = b.count;

        smoothOutlines(n);

        const verts: [*]f32 = @ptrCast(@alignCast(rl.MemAlloc(@intCast(n * 3 * @sizeOf(f32))).?));
        const norms: [*]f32 = @ptrCast(@alignCast(rl.MemAlloc(@intCast(n * 3 * @sizeOf(f32))).?));
        const cols: [*]u8 = @ptrCast(rl.MemAlloc(@intCast(n * 4)).?);
        const outs: [*]f32 = @ptrCast(@alignCast(rl.MemAlloc(@intCast(n * 4 * @sizeOf(f32))).?));
        const uvs: [*]f32 = @ptrCast(@alignCast(rl.MemAlloc(@intCast(n * 2 * @sizeOf(f32))).?));

        @memcpy(verts[0 .. n * 3], positions[0 .. n * 3]);
        @memcpy(norms[0 .. n * 3], normals[0 .. n * 3]);
        @memcpy(cols[0 .. n * 4], colors[0 .. n * 4]);
        @memcpy(outs[0 .. n * 4], outlines[0 .. n * 4]);
        @memset(uvs[0 .. n * 2], 0);

        var mesh: rl.Mesh = .{
            .vertexCount = @intCast(n),
            .triangleCount = @intCast(n / 3),
            .vertices = verts,
            .normals = norms,
            .colors = cols,
            .tangents = outs,
            .texcoords = uvs,
        };

        rl.UploadMesh(&mesh, false);
        rl.MemFree(mesh.vertices);
        rl.MemFree(mesh.normals);
        rl.MemFree(mesh.colors);
        rl.MemFree(mesh.tangents);
        rl.MemFree(mesh.texcoords);
        mesh.vertices = null;
        mesh.normals = null;
        mesh.colors = null;
        mesh.tangents = null;
        mesh.texcoords = null;
        b.count = 0;

        return mesh;
    }
};

const std_pi: f32 = 3.14159265358979;

fn polar(theta: f32, phi: f32) Vec3 {
    return .{
        .x = @sin(theta) * @cos(phi),
        .y = @cos(theta),
        .z = @sin(theta) * @sin(phi),
    };
}
