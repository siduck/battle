const std = @import("std");
const shared = @import("shared");

const terrain = shared.terrain;
const world = shared.world;
const props = shared.props;
const maps = shared.maps;
const movement = shared.movement;
const Vec3 = shared.math.Vec3;

const cell: f32 = 0.5;
const eye: f32 = movement.eye_height;
const step: f32 = movement.step_height;
const head: f32 = movement.height;
const samples: usize = 700;
const rays_per: usize = 8;

const Grid = struct {
    n: usize,
    org: f32,
    ground: []f32,
    lo: []f32,
    hi: []f32,
    block: []u8,
    walk: []u8,
    top: []f32,

    fn idx(g: *const Grid, i: usize, j: usize) usize {
        return j * g.n + i;
    }

    fn cx(g: *const Grid, i: usize) f32 {
        return g.org + (@as(f32, @floatFromInt(i)) + 0.5) * cell;
    }

    fn at(g: *const Grid, x: f32, z: f32) ?usize {
        const fi = (x - g.org) / cell;
        const fj = (z - g.org) / cell;

        if (fi < 0 or fj < 0) return null;

        const i: usize = @intFromFloat(fi);
        const j: usize = @intFromFloat(fj);

        if (i >= g.n or j >= g.n) return null;

        return g.idx(i, j);
    }
};

const Rng = struct {
    s: u64,

    fn next(r: *Rng) f32 {
        r.s = r.s *% 6364136223846793005 +% 1442695040888963407;

        return @as(f32, @floatFromInt(r.s >> 40)) / 16777216.0;
    }
};

fn edt1(f: []const f32, d: []f32, v: []usize, z: []f32, n: usize) void {
    var k: usize = 0;

    v[0] = 0;
    z[0] = -std.math.inf(f32);
    z[1] = std.math.inf(f32);

    var q: usize = 1;

    while (q < n) : (q += 1) {
        while (true) {
            const vq: f32 = @floatFromInt(q);
            const vk: f32 = @floatFromInt(v[k]);
            const s = ((f[q] + vq * vq) - (f[v[k]] + vk * vk)) / (2 * vq - 2 * vk);

            if (s <= z[k]) {
                if (k == 0) {
                    v[0] = q;
                    z[0] = -std.math.inf(f32);
                    z[1] = std.math.inf(f32);

                    break;
                }

                k -= 1;

                continue;
            }

            k += 1;
            v[k] = q;
            z[k] = s;
            z[k + 1] = std.math.inf(f32);

            break;
        }
    }

    k = 0;
    q = 0;

    while (q < n) : (q += 1) {
        const fq: f32 = @floatFromInt(q);

        while (z[k + 1] < fq) k += 1;

        const dv = fq - @as(f32, @floatFromInt(v[k]));

        d[q] = dv * dv + f[v[k]];
    }
}

fn edt(gpa: std.mem.Allocator, src: []const u8, n: usize) ![]f32 {
    const big: f32 = 1e12;
    const out = try gpa.alloc(f32, n * n);
    const f = try gpa.alloc(f32, n);
    const d = try gpa.alloc(f32, n);
    const v = try gpa.alloc(usize, n);
    const z = try gpa.alloc(f32, n + 1);

    for (out, src) |*o, s| o.* = if (s != 0) 0 else big;

    var i: usize = 0;

    while (i < n) : (i += 1) {
        var j: usize = 0;

        while (j < n) : (j += 1) f[j] = out[j * n + i];

        edt1(f, d, v, z, n);
        j = 0;

        while (j < n) : (j += 1) out[j * n + i] = d[j];
    }

    var j: usize = 0;

    while (j < n) : (j += 1) {
        @memcpy(f, out[j * n .. j * n + n]);
        edt1(f, d, v, z, n);

        for (0..n) |q| out[j * n + q] = @sqrt(d[q]) * cell;
    }

    return out;
}

fn label(gpa: std.mem.Allocator, mask: []const u8, n: usize, diag: bool) !struct { ids: []i32, count: usize, sizes: []u32 } {
    const ids = try gpa.alloc(i32, n * n);
    var sizes: std.ArrayList(u32) = .empty;
    var stack: std.ArrayList(usize) = .empty;

    @memset(ids, -1);

    for (0..n * n) |s| {
        if (mask[s] == 0 or ids[s] >= 0) continue;

        const id: i32 = @intCast(sizes.items.len);
        var size: u32 = 0;

        ids[s] = id;
        try stack.append(gpa, s);

        while (stack.pop()) |c| {
            size += 1;

            const ci = c % n;
            const cj = c / n;
            var dj: i32 = -1;

            while (dj <= 1) : (dj += 1) {
                var di: i32 = -1;

                while (di <= 1) : (di += 1) {
                    if (di == 0 and dj == 0) continue;

                    if (!diag and di != 0 and dj != 0) continue;

                    const ni = @as(i32, @intCast(ci)) + di;
                    const nj = @as(i32, @intCast(cj)) + dj;

                    if (ni < 0 or nj < 0 or ni >= n or nj >= n) continue;

                    const nc = @as(usize, @intCast(nj)) * n + @as(usize, @intCast(ni));

                    if (mask[nc] == 0 or ids[nc] >= 0) continue;

                    ids[nc] = id;
                    try stack.append(gpa, nc);
                }
            }
        }

        try sizes.append(gpa, size);
    }

    return .{ .ids = ids, .count = sizes.items.len, .sizes = sizes.items };
}

fn opening(gpa: std.mem.Allocator, dt: []const f32, n: usize, r: f32) ![]u8 {
    const seed = try gpa.alloc(u8, n * n);

    for (seed, dt) |*s, d| s.* = if (d >= r) 1 else 0;

    const back = try edt(gpa, seed, n);
    const out = try gpa.alloc(u8, n * n);

    for (out, back, dt) |*o, b, d| o.* = if (d > 0 and b <= r + 0.01) 1 else 0;

    return out;
}

fn pct(xs: []f32, p: f32) f32 {
    if (xs.len == 0) return 0;

    const i: usize = @intFromFloat(@min(@as(f32, @floatFromInt(xs.len - 1)), p * @as(f32, @floatFromInt(xs.len - 1))));

    return xs[i];
}

fn lessF(_: void, a: f32, b: f32) bool {
    return a < b;
}

fn groupName(g: props.Group) []const u8 {
    return @tagName(g);
}

pub fn main(init: std.process.Init.Minimal) void {
    var args = init.args.iterate();

    _ = args.next();

    const name = args.next() orelse {
        std.debug.print("usage: mapaudit <map>\n", .{});

        return;
    };

    var raster = false;
    var window: f32 = 0;

    while (args.next()) |a| {
        if (std.mem.eql(u8, a, "--raster")) raster = true;

        if (std.mem.eql(u8, a, "--kinds")) list_kinds = true;

        if (std.mem.startsWith(u8, a, "--half=")) window = std.fmt.parseFloat(f32, a[7..]) catch 0;
    }

    run(name, raster, window) catch |e| std.debug.print("error {s}\n", .{@errorName(e)});
}

var list_kinds = false;

fn run(name: []const u8, raster: bool, window: f32) !void {
    const gpa = std.heap.page_allocator;
    const m = std.meta.stringToEnum(terrain.Map, name) orelse return error.UnknownMap;

    terrain.current = m;
    terrain.configure();
    world.build(gpa);

    if (list_kinds) {
        var seen = std.AutoHashMap(u16, void).init(gpa);

        for (world.placements) |pl| {
            const e = try seen.getOrPut(@intFromEnum(pl.kind));

            if (!e.found_existing) std.debug.print("KIND {s}\n", .{props.info(pl.kind).file});
        }

        return;
    }

    const def = maps.current() orelse return error.NoDef;
    const play = if (window > 0) window else terrain.play;
    const n: usize = @intFromFloat(@ceil(2 * play / cell));
    const total = n * n;
    var g: Grid = .{
        .n = n,
        .org = -play,
        .ground = try gpa.alloc(f32, total),
        .lo = try gpa.alloc(f32, total),
        .hi = try gpa.alloc(f32, total),
        .block = try gpa.alloc(u8, total),
        .walk = try gpa.alloc(u8, total),
        .top = try gpa.alloc(f32, total),
    };

    @memset(g.lo, std.math.inf(f32));
    @memset(g.hi, -std.math.inf(f32));
    @memset(g.block, 0);
    @memset(g.top, 0);

    for (0..n) |j| {
        for (0..n) |i| g.ground[g.idx(i, j)] = terrain.height(g.cx(i), g.cx(j));
    }

    for (world.pieces) |pc| {
        const bb = pc.shape.bounds();

        if (bb.max.x < -play or bb.min.x > play or bb.max.z < -play or bb.min.z > play) continue;

        const is_ramp = pc.shape == .ramp;
        const ri0: usize = @intFromFloat(@max(0, @floor((bb.min.x + play) / cell)));
        const rj0: usize = @intFromFloat(@max(0, @floor((bb.min.z + play) / cell)));
        const ri1: usize = @min(n - 1, @as(usize, @intFromFloat(@max(0, @floor((bb.max.x + play) / cell)))));
        const rj1: usize = @min(n - 1, @as(usize, @intFromFloat(@max(0, @floor((bb.max.z + play) / cell)))));

        var j = rj0;

        while (j <= rj1) : (j += 1) {
            var i = ri0;

            while (i <= ri1) : (i += 1) {
                const x = g.cx(i);
                const z = g.cx(j);

                switch (pc.shape) {
                    .cylinder => |c| {
                        const dx = x - c.base.x;
                        const dz = z - c.base.z;
                        const rr = @max(c.radius, cell * 0.5);

                        if (dx * dx + dz * dz > rr * rr) continue;
                    },
                    else => {
                        if (x < bb.min.x or x > bb.max.x or z < bb.min.z or z > bb.max.z) {
                            if (bb.max.x - bb.min.x >= cell and bb.max.z - bb.min.z >= cell) continue;
                        }
                    },
                }

                const c = g.idx(i, j);

                if (is_ramp) continue;

                g.lo[c] = @min(g.lo[c], bb.min.y);
                g.hi[c] = @max(g.hi[c], bb.max.y);

                const gy = g.ground[c];

                if (bb.max.y > gy + step and bb.min.y < gy + head) {
                    g.block[c] = 1;
                    g.top[c] = @max(g.top[c], bb.max.y - gy);
                }
            }
        }
    }

    const water_y = def.floor_y;
    var n_walk: usize = 0;
    var n_block: usize = 0;
    var n_water: usize = 0;
    var n_steep: usize = 0;

    for (0..n) |j| {
        for (0..n) |i| {
            const c = g.idx(i, j);
            const gy = g.ground[c];
            const x = g.cx(i);
            const z = g.cx(j);
            const nrm = terrain.normal(x, z);
            const wet = gy < water_y - 0.3 or gy < -20;
            const steep = 1 - nrm.y > 0.3;

            g.walk[c] = 0;

            if (wet) {
                n_water += 1;

                continue;
            }

            if (g.block[c] != 0) {
                n_block += 1;

                continue;
            }

            if (steep) {
                n_steep += 1;

                continue;
            }

            g.walk[c] = 1;
            n_walk += 1;
        }
    }

    const nonwalk = try gpa.alloc(u8, total);

    for (nonwalk, g.walk) |*o, w| o.* = if (w == 0) 1 else 0;

    for (0..n) |q| {
        nonwalk[q] = 1;
        nonwalk[(n - 1) * n + q] = 1;
        nonwalk[q * n] = 1;
        nonwalk[q * n + n - 1] = 1;
    }

    const dt = try edt(gpa, nonwalk, n);
    var widths: std.ArrayList(f32) = .empty;

    for (dt, g.walk) |d, w| {
        if (w != 0) try widths.append(gpa, 2 * d);
    }

    std.mem.sort(f32, widths.items, {}, lessF);

    const open6 = try opening(gpa, dt, n, 6);
    const open3 = try opening(gpa, dt, n, 3);
    const open1 = try opening(gpa, dt, n, 1);
    var c_open6: usize = 0;
    var c_open3: usize = 0;

    for (open6, open3, g.walk) |a, b, w| {
        if (w == 0) continue;

        if (a != 0) c_open6 += 1;

        if (b != 0) c_open3 += 1;
    }

    const clear_mask = try gpa.alloc(u8, total);

    for (clear_mask, dt) |*o, d| o.* = if (d >= 6) 1 else 0;

    const clears = try label(gpa, clear_mask, n, true);
    var clear_count: usize = 0;
    var clear_big: usize = 0;

    for (clears.sizes) |s| {
        if (s >= 8) clear_count += 1;

        clear_big = @max(clear_big, s);
    }

    const narrow = try gpa.alloc(u8, total);

    for (narrow, dt, open1, g.walk) |*o, d, op, w| o.* = if (w != 0 and d >= movement.radius and op == 0) 1 else 0;

    const nl = try label(gpa, narrow, n, true);
    const mouth = try gpa.alloc(i32, total);
    var dead_ends: usize = 0;
    var through: usize = 0;
    var pockets: usize = 0;
    var adj: std.ArrayList(usize) = .empty;
    var stk: std.ArrayList(usize) = .empty;

    @memset(mouth, -1);

    {
        var lists = try gpa.alloc(std.ArrayList(usize), nl.count);

        for (lists) |*l| l.* = .empty;

        for (0..total) |c| {
            if (nl.ids[c] < 0) continue;

            const ci = c % n;
            const cj = c / n;
            const nb = [_][2]i32{ .{ 1, 0 }, .{ -1, 0 }, .{ 0, 1 }, .{ 0, -1 } };

            for (nb) |o| {
                const ni = @as(i32, @intCast(ci)) + o[0];
                const nj = @as(i32, @intCast(cj)) + o[1];

                if (ni < 0 or nj < 0 or ni >= n or nj >= n) continue;

                const nc = @as(usize, @intCast(nj)) * n + @as(usize, @intCast(ni));

                if (open1[nc] != 0 and g.walk[nc] != 0) try lists[@intCast(nl.ids[c])].append(gpa, nc);
            }
        }

        for (lists, 0..) |l, id| {
            if (nl.sizes[id] < 4) continue;

            adj.clearRetainingCapacity();

            for (l.items) |c| {
                if (mouth[c] == @as(i32, @intCast(id))) continue;

                mouth[c] = @intCast(id);
                try adj.append(gpa, c);
            }

            var groups: usize = 0;
            const tag: i32 = -2 - @as(i32, @intCast(id));

            for (adj.items) |s| {
                if (mouth[s] == tag) continue;

                groups += 1;
                mouth[s] = tag;
                try stk.append(gpa, s);

                while (stk.pop()) |c| {
                    const ci = c % n;
                    const cj = c / n;
                    var dj: i32 = -2;

                    while (dj <= 2) : (dj += 1) {
                        var di: i32 = -2;

                        while (di <= 2) : (di += 1) {
                            const ni = @as(i32, @intCast(ci)) + di;
                            const nj = @as(i32, @intCast(cj)) + dj;

                            if (ni < 0 or nj < 0 or ni >= n or nj >= n) continue;

                            const nc = @as(usize, @intCast(nj)) * n + @as(usize, @intCast(ni));

                            if (mouth[nc] != @as(i32, @intCast(id))) continue;

                            mouth[nc] = tag;
                            try stk.append(gpa, nc);
                        }
                    }
                }
            }

            if (groups == 0) pockets += 1 else if (groups == 1) dead_ends += 1 else through += 1;
        }
    }

    if (raster) {
        const row = try gpa.alloc(u8, n);

        std.debug.print("RASTER {d}\n", .{n});

        for (0..n) |j| {
            for (0..n) |i| {
                const c = g.idx(i, j);
                const gy = g.ground[c];

                row[i] = if (gy < water_y - 0.3 or gy < -20) '~' else if (g.block[c] != 0) '#' else if (g.walk[c] == 0) '^' else if (narrow[c] != 0) ',' else if (open6[c] != 0) ' ' else '.';
            }

            std.debug.print("R{s}\n", .{row});
        }
    }

    const drive_mask = try gpa.alloc(u8, total);

    for (drive_mask, dt) |*o, d| o.* = if (d >= 1.75) 1 else 0;

    const drive = try label(gpa, drive_mask, n, false);
    var drive_big: usize = 0;

    for (drive.sizes) |s| drive_big = @max(drive_big, s);

    const cover_mask = try gpa.alloc(u8, total);

    for (cover_mask, g.block, g.top) |*o, b, tp| o.* = if (b != 0 and tp >= 0.9) 1 else 0;

    const cov = try label(gpa, cover_mask, n, true);
    const stamp = try gpa.alloc(u32, @max(cov.count, 1));

    @memset(stamp, 0);

    var rng: Rng = .{ .s = 0xd00d };
    var pts: std.ArrayList([2]usize) = .empty;
    var guard: usize = 0;

    while (pts.items.len < samples and guard < 400000) : (guard += 1) {
        const i: usize = @intFromFloat(rng.next() * @as(f32, @floatFromInt(n - 1)));
        const j: usize = @intFromFloat(rng.next() * @as(f32, @floatFromInt(n - 1)));

        if (g.walk[g.idx(i, j)] != 0 and dt[g.idx(i, j)] >= movement.radius) try pts.append(gpa, .{ i, j });
    }

    var cov15: f32 = 0;
    var cov30: f32 = 0;
    var blk15: f32 = 0;
    var low15: f32 = 0;
    var nearest: std.ArrayList(f32) = .empty;
    var tag: u32 = 0;

    for (pts.items) |p| {
        for ([_]f32{ 15, 30 }) |rad| {
            tag += 1;

            const rc: i32 = @intFromFloat(rad / cell);
            var cnt: f32 = 0;
            var lowc: f32 = 0;
            var blocked: f32 = 0;
            var cells: f32 = 0;
            var near_d: f32 = 1e9;
            var dj: i32 = -rc;

            while (dj <= rc) : (dj += 1) {
                var di: i32 = -rc;

                while (di <= rc) : (di += 1) {
                    if (di * di + dj * dj > rc * rc) continue;

                    const ni = @as(i32, @intCast(p[0])) + di;
                    const nj = @as(i32, @intCast(p[1])) + dj;

                    if (ni < 0 or nj < 0 or ni >= n or nj >= n) continue;

                    const c = @as(usize, @intCast(nj)) * n + @as(usize, @intCast(ni));

                    cells += 1;

                    if (g.block[c] != 0) blocked += 1;

                    const id = cov.ids[c];

                    if (id < 0) continue;

                    const dd = @sqrt(@as(f32, @floatFromInt(di * di + dj * dj))) * cell;

                    near_d = @min(near_d, dd);

                    if (stamp[@intCast(id)] == tag) continue;

                    stamp[@intCast(id)] = tag;
                    cnt += 1;

                    if (g.top[c] < 1.6) lowc += 1;
                }
            }

            if (rad == 15) {
                cov15 += cnt;
                low15 += lowc;
                blk15 += if (cells > 0) blocked / cells else 0;
                try nearest.append(gpa, near_d);
            } else cov30 += cnt;
        }
    }

    const np: f32 = @floatFromInt(@max(pts.items.len, 1));

    std.mem.sort(f32, nearest.items, {}, lessF);

    var sights: std.ArrayList(f32) = .empty;

    for (pts.items) |p| {
        var r: usize = 0;

        while (r < rays_per) : (r += 1) {
            const a = (@as(f32, @floatFromInt(r)) + rng.next()) / @as(f32, @floatFromInt(rays_per)) * std.math.tau;
            const dx = @cos(a);
            const dz = @sin(a);
            const ox = g.cx(p[0]);
            const oz = g.cx(p[1]);
            const oy = g.ground[g.idx(p[0], p[1])] + eye;
            var s: f32 = 0.5;
            var hit: f32 = 400;

            while (s < 400) : (s += 0.25) {
                const x = ox + dx * s;
                const z = oz + dz * s;
                const c = g.at(x, z) orelse {
                    hit = s;

                    break;
                };

                if (g.ground[c] > oy or (oy >= g.lo[c] and oy <= g.hi[c])) {
                    hit = s;

                    break;
                }
            }

            try sights.append(gpa, hit);
        }
    }

    std.mem.sort(f32, sights.items, {}, lessF);

    var over50: f32 = 0;
    var over100: f32 = 0;
    var under10: f32 = 0;
    var b10_40: f32 = 0;
    var b40_70: f32 = 0;
    var b70_120: f32 = 0;

    for (sights.items) |s| {
        if (s > 50) over50 += 1;

        if (s > 100) over100 += 1;

        if (s < 10) under10 += 1 else if (s < 40) b10_40 += 1 else if (s < 70) b40_70 += 1 else if (s < 120) b70_120 += 1;
    }

    const ns: f32 = @floatFromInt(@max(sights.items.len, 1));
    const max_groups = 8;
    var gcount: [max_groups]usize = @splat(0);
    var gsolid: [max_groups]usize = @splat(0);
    var kinds = std.AutoHashMap(u16, usize).init(gpa);
    var in_play: usize = 0;
    var solid_props: usize = 0;

    for (world.placements) |pl| {
        if (@abs(pl.pos.x) > play or @abs(pl.pos.z) > play) continue;

        const inf = props.info(pl.kind);
        const gi = @intFromEnum(inf.group);

        gcount[gi] += 1;
        in_play += 1;

        if (inf.collide != .none) {
            gsolid[gi] += 1;
            solid_props += 1;
        }

        const e = try kinds.getOrPut(@intFromEnum(pl.kind));

        if (!e.found_existing) e.value_ptr.* = 0;

        e.value_ptr.* += 1;
    }

    var marks: std.ArrayList([2]f32) = .empty;

    for (world.placements) |pl| {
        if (@abs(pl.pos.x) > play or @abs(pl.pos.z) > play) continue;

        const inf = props.info(pl.kind);
        const h = (inf.max[1] - inf.min[1]) * pl.scale;
        const uses = kinds.get(@intFromEnum(pl.kind)) orelse 0;
        const tall = h >= 18 or (uses <= 2 and h >= 7);

        if (!tall) continue;

        var merged = false;

        for (marks.items) |mk| {
            const ddx = mk[0] - pl.pos.x;
            const ddz = mk[1] - pl.pos.z;

            if (ddx * ddx + ddz * ddz < 25 * 25) merged = true;
        }

        if (!merged) try marks.append(gpa, .{ pl.pos.x, pl.pos.z });
    }

    var nn_sum: f32 = 0;

    for (marks.items, 0..) |a, ai| {
        var best: f32 = 1e9;

        for (marks.items, 0..) |b, bi| {
            if (ai == bi) continue;

            const ddx = a[0] - b[0];
            const ddz = a[1] - b[1];

            best = @min(best, @sqrt(ddx * ddx + ddz * ddz));
        }

        if (best < 1e8) nn_sum += best;
    }

    const ha = (2 * play) * (2 * play) / 10000;
    const land: f32 = @floatFromInt(total - n_water);
    const cellA = cell * cell;
    const nw: f32 = @floatFromInt(@max(n_walk, 1));

    std.debug.print("{{\"map\":\"{s}\",\"name\":\"{s}\",\"play\":{d:.0},\"ha\":{d:.2},\"land_ha\":{d:.2},", .{ name, def.name, play, ha, land * cellA / 10000 });
    var out_play: usize = 0;

    for (world.placements) |pl| {
        if (@max(@abs(pl.pos.x), @abs(pl.pos.z)) > terrain.play + 1) out_play += 1;

    }

    std.debug.print("\"all_props\":{d},\"out_play\":{d},\"terrain_half\":{d:.0},\"terrain_play\":{d:.0},", .{ world.placements.len, out_play, terrain.half, terrain.play });
    std.debug.print("\"props\":{d},\"props_ha\":{d:.1},\"solid_props_ha\":{d:.1},\"pieces\":{d},\"kinds\":{d},", .{ in_play, @as(f32, @floatFromInt(in_play)) / ha, @as(f32, @floatFromInt(solid_props)) / ha, world.pieces.len, kinds.count() });
    std.debug.print("\"groups\":{{", .{});

    for (0..max_groups) |gi| {
        const gname = groupName(@enumFromInt(gi));

        std.debug.print("\"{s}\":[{d:.1},{d:.1}]{s}", .{ gname, @as(f32, @floatFromInt(gcount[gi])) / ha, @as(f32, @floatFromInt(gsolid[gi])) / ha, if (gi + 1 < max_groups) "," else "" });
    }

    std.debug.print("}},\"blocked_pct\":{d:.1},\"water_pct\":{d:.1},\"steep_pct\":{d:.1},\"walk_pct\":{d:.1},", .{ @as(f32, @floatFromInt(n_block)) / land * 100, @as(f32, @floatFromInt(n_water)) / @as(f32, @floatFromInt(total)) * 100, @as(f32, @floatFromInt(n_steep)) / land * 100, @as(f32, @floatFromInt(n_walk)) / land * 100 });
    var under2: f32 = 0;
    var under4: f32 = 0;

    for (widths.items) |wv| {
        if (wv < 2) under2 += 1;

        if (wv < 4) under4 += 1;
    }

    std.debug.print("\"width_under2_pct\":{d:.1},\"width_under4_pct\":{d:.1},", .{ under2 / nw * 100, under4 / nw * 100 });
    std.debug.print("\"width_p10\":{d:.1},\"width_p50\":{d:.1},\"width_p90\":{d:.1},", .{ pct(widths.items, 0.1), pct(widths.items, 0.5), pct(widths.items, 0.9) });
    std.debug.print("\"open12_pct\":{d:.1},\"open6_pct\":{d:.1},\"clearings\":{d},\"clearing_max_m2\":{d:.0},", .{ @as(f32, @floatFromInt(c_open6)) / nw * 100, @as(f32, @floatFromInt(c_open3)) / nw * 100, clear_count, @as(f32, @floatFromInt(clear_big)) * cellA });
    std.debug.print("\"drive_pct\":{d:.1},\"dead_ends\":{d},\"through_gaps\":{d},\"pockets\":{d},\"dead_ends_ha\":{d:.2},", .{ @as(f32, @floatFromInt(drive_big)) / nw * 100, dead_ends, through, pockets, @as(f32, @floatFromInt(dead_ends)) / ha });
    std.debug.print("\"cover15\":{d:.1},\"cover30\":{d:.1},\"low_cover15\":{d:.1},\"blocked15_pct\":{d:.1},\"nearest_cover_p50\":{d:.1},\"nearest_cover_p90\":{d:.1},", .{ cov15 / np, cov30 / np, low15 / np, blk15 / np * 100, pct(nearest.items, 0.5), pct(nearest.items, 0.9) });
    std.debug.print("\"sight_p25\":{d:.1},\"sight_p50\":{d:.1},\"sight_p75\":{d:.1},\"sight_p90\":{d:.1},\"sight_over50_pct\":{d:.1},\"sight_over100_pct\":{d:.1},", .{ pct(sights.items, 0.25), pct(sights.items, 0.5), pct(sights.items, 0.75), pct(sights.items, 0.9), over50 / ns * 100, over100 / ns * 100 });
    std.debug.print("\"sight_bands\":[{d:.1},{d:.1},{d:.1},{d:.1},{d:.1}],", .{ under10 / ns * 100, b10_40 / ns * 100, b40_70 / ns * 100, b70_120 / ns * 100, (ns - under10 - b10_40 - b40_70 - b70_120) / ns * 100 });
    std.debug.print("\"landmarks\":{d},\"landmark_nn\":{d:.0},\"heat\":[", .{ marks.items.len, if (marks.items.len > 1) nn_sum / @as(f32, @floatFromInt(marks.items.len)) else 0 });

    const tiles: usize = 10;
    const per = n / tiles;

    for (0..tiles) |tj| {
        std.debug.print("\"", .{});

        for (0..tiles) |ti| {
            var bl: f32 = 0;
            var lc: f32 = 0;

            for (tj * per..(tj + 1) * per) |j| {
                for (ti * per..(ti + 1) * per) |i| {
                    const c = g.idx(i, j);
                    const gy = g.ground[c];

                    if (gy < water_y - 0.3 or gy < -20) continue;

                    lc += 1;

                    if (g.block[c] != 0) bl += 1;
                }
            }

            if (lc < 1) {
                std.debug.print("~", .{});

                continue;
            }

            const v: usize = @intFromFloat(@min(9, @floor(bl / lc * 10)));

            std.debug.print("{d}", .{v});
        }

        std.debug.print("\"{s}", .{if (tj + 1 < tiles) "," else ""});
    }

    std.debug.print("],\"propheat\":[", .{});

    const tile_ha = (2 * play / @as(f32, @floatFromInt(tiles))) * (2 * play / @as(f32, @floatFromInt(tiles))) / 10000;
    var ph = try gpa.alloc(f32, tiles * tiles);

    @memset(ph, 0);

    for (world.placements) |pl| {
        if (@abs(pl.pos.x) >= play or @abs(pl.pos.z) >= play) continue;

        const inf = props.info(pl.kind);

        if (inf.group == .building or inf.group == .road or inf.group == .ground) continue;

        const ti: usize = @min(tiles - 1, @as(usize, @intFromFloat((pl.pos.x + play) / (2 * play) * @as(f32, @floatFromInt(tiles)))));
        const tj: usize = @min(tiles - 1, @as(usize, @intFromFloat((pl.pos.z + play) / (2 * play) * @as(f32, @floatFromInt(tiles)))));

        ph[tj * tiles + ti] += 1;
    }

    for (0..tiles) |tj| {
        std.debug.print("[", .{});

        for (0..tiles) |ti| std.debug.print("{d:.0}{s}", .{ ph[tj * tiles + ti] / tile_ha, if (ti + 1 < tiles) "," else "" });

        std.debug.print("]{s}", .{if (tj + 1 < tiles) "," else ""});
    }

    std.debug.print("],\"top_kinds\":{{", .{});

    const KC = struct { k: u16, c: usize };
    var kc: std.ArrayList(KC) = .empty;
    var it = kinds.iterator();

    while (it.next()) |e| try kc.append(gpa, .{ .k = e.key_ptr.*, .c = e.value_ptr.* });

    std.mem.sort(KC, kc.items, {}, struct {
        fn more(_: void, a: KC, b: KC) bool {
            return a.c > b.c;
        }
    }.more);

    const shown = @min(kc.items.len, 20);

    for (kc.items[0..shown], 0..) |e, ei| {
        const kname = std.fs.path.stem(props.name(@enumFromInt(e.k)));

        std.debug.print("\"{s}\":{d:.1}{s}", .{ kname, @as(f32, @floatFromInt(e.c)) / ha, if (ei + 1 < shown) "," else "" });
    }

    std.debug.print("}}}}\n", .{});
}
