pub const Class = enum { pistol, smg, rifle, dmr, sniper, shotgun, lmg, launcher, bow, crossbow, special, melee };

pub const Fire = enum { hitscan, rocket, grenade, arrow, bolt, melee };

pub const Mag = enum { none, box, curved, drum, tube, belt };

pub const Optic = enum { iron, dot, holo, scope2, scope4, scope8 };

pub const Look = struct {
    body: f32,
    height: f32 = 0.03,
    barrel: f32,
    stock: f32 = 0,
    mag: Mag = .box,
    optic: Optic = .iron,
    guard: bool = false,
};

pub const Spec = struct {
    name: [:0]const u8,
    class: Class,
    fire: Fire = .hitscan,
    auto: bool = false,
    burst: u8 = 1,
    damage: f32,
    pellets: u8 = 1,
    interval: f32,
    mag: u16,
    reserve: u16,
    reload: f32,
    spread: f32,
    ads_spread: f32,
    ads_zoom: f32 = 2,
    range: f32 = 250,
    recoil: f32,
    splash: f32 = 0,
    speed: f32 = 0,
    gravity: f32 = 0,
    knockback: f32 = 0,
    spinup: f32 = 0,
    charge: f32 = 0,
    pierce: bool = false,
    flame: bool = false,
    lifesteal: f32 = 0,
    look: Look,

    pub fn reach(s: Spec) f32 {
        return s.look.body + s.look.barrel;
    }
};

pub const Rarity = enum(u8) { common, uncommon, rare, epic, legendary };

pub const rarity_names = [_][:0]const u8{ "Common", "Uncommon", "Rare", "Epic", "Legendary" };
pub const rarity_accent = [_]u8{ 0, 2, 3, 6, 5 };
pub const rarity_damage = [_]f32{ 1, 1.08, 1.16, 1.25, 1.35 };
pub const rarity_reload = [_]f32{ 1, 0.95, 0.9, 0.85, 0.8 };

fn blade(name: [:0]const u8, damage: f32, interval: f32, range: f32, knockback: f32, lifesteal: f32, length: f32) Spec {
    return .{ .name = name, .class = .melee, .fire = .melee, .damage = damage, .interval = interval, .mag = 0, .reserve = 0, .reload = 0, .spread = 0, .ads_spread = 0, .ads_zoom = 1, .range = range, .recoil = 0, .knockback = knockback, .lifesteal = lifesteal, .look = .{ .body = 0.1, .barrel = length - 0.1, .mag = .none } };
}

pub fn isMelee(s: Spec) bool {
    return s.fire == .melee;
}

fn hand(name: [:0]const u8, damage: f32, interval: f32, mag: u16, reload: f32, spread: f32, recoil: f32, look: Look) Spec {
    return .{ .name = name, .class = .pistol, .damage = damage, .interval = interval, .mag = mag, .reserve = mag * 6, .reload = reload, .spread = spread, .ads_spread = spread * 0.2, .recoil = recoil, .range = 120, .look = look };
}

fn smg(name: [:0]const u8, damage: f32, interval: f32, mag: u16, spread: f32, recoil: f32, look: Look) Spec {
    return .{ .name = name, .class = .smg, .auto = true, .damage = damage, .interval = interval, .mag = mag, .reserve = mag * 5, .reload = 1.6, .spread = spread, .ads_spread = spread * 0.45, .recoil = recoil, .range = 70, .look = look };
}

fn rifle(name: [:0]const u8, damage: f32, interval: f32, mag: u16, spread: f32, recoil: f32, look: Look) Spec {
    return .{ .name = name, .class = .rifle, .auto = true, .damage = damage, .interval = interval, .mag = mag, .reserve = mag * 5, .reload = 1.9, .spread = spread, .ads_spread = spread * 0.15, .ads_zoom = zoomFor(look.optic), .recoil = recoil, .look = look };
}

fn dmr(name: [:0]const u8, damage: f32, interval: f32, mag: u16, recoil: f32, look: Look) Spec {
    return .{ .name = name, .class = .dmr, .damage = damage, .interval = interval, .mag = mag, .reserve = mag * 4, .reload = 2.3, .spread = 0.03, .ads_spread = 0.001, .ads_zoom = zoomFor(look.optic), .recoil = recoil, .range = 400, .look = look };
}

fn sniper(name: [:0]const u8, damage: f32, interval: f32, mag: u16, reload: f32, recoil: f32, look: Look) Spec {
    return .{ .name = name, .class = .sniper, .damage = damage, .interval = interval, .mag = mag, .reserve = mag * 5, .reload = reload, .spread = 0.06, .ads_spread = 0, .ads_zoom = zoomFor(look.optic), .recoil = recoil, .range = 700, .look = look };
}

fn shotgun(name: [:0]const u8, pellets: u8, damage: f32, interval: f32, mag: u16, reload: f32, spread: f32, look: Look) Spec {
    return .{ .name = name, .class = .shotgun, .damage = damage, .pellets = pellets, .interval = interval, .mag = mag, .reserve = mag * 5, .reload = reload, .spread = spread, .ads_spread = spread * 0.7, .recoil = 0.045, .range = 40, .look = look };
}

fn lmg(name: [:0]const u8, damage: f32, interval: f32, mag: u16, reload: f32, spread: f32, look: Look) Spec {
    return .{ .name = name, .class = .lmg, .auto = true, .damage = damage, .interval = interval, .mag = mag, .reserve = mag * 3, .reload = reload, .spread = spread, .ads_spread = spread * 0.3, .ads_zoom = zoomFor(look.optic), .recoil = 0.006, .look = look };
}

fn zoomFor(optic: Optic) f32 {
    return switch (optic) {
        .iron => 2,
        .dot => 2,
        .holo => 2,
        .scope2 => 2,
        .scope4 => 4,
        .scope8 => 7,
    };
}

fn burst(s: Spec, shots: u8) Spec {
    var out = s;

    out.burst = shots;
    out.auto = false;

    return out;
}

pub const specs = outfit(&raw_specs);

const raw_specs = [_]Spec{
    hand("Pocket", 24, 0.16, 12, 1.1, 0.012, 0.012, .{ .body = 0.09, .barrel = 0.03, .mag = .none }),
    hand("Nine", 20, 0.12, 17, 1.2, 0.014, 0.01, .{ .body = 0.1, .barrel = 0.03, .mag = .none, .optic = .dot }),
    hand("Hand Cannon", 55, 0.38, 7, 1.6, 0.016, 0.055, .{ .body = 0.12, .height = 0.034, .barrel = 0.06, .mag = .none }),
    burst(hand("Twin Tap", 18, 0.24, 16, 1.2, 0.012, 0.012, .{ .body = 0.1, .barrel = 0.04, .mag = .none }), 2),
    blk: {
        var s = hand("Buzzer", 14, 0.07, 20, 1.3, 0.035, 0.008, .{ .body = 0.1, .barrel = 0.03, .mag = .box });

        s.auto = true;

        break :blk s;
    },
    hand("Six Shooter", 45, 0.3, 6, 2.2, 0.01, 0.045, .{ .body = 0.11, .height = 0.032, .barrel = 0.08, .mag = .drum }),

    smg("Buzz", 13, 0.06, 36, 0.03, 0.005, .{ .body = 0.12, .barrel = 0.08, .stock = 0.06 }),
    smg("Hornet", 11, 0.05, 40, 0.04, 0.004, .{ .body = 0.11, .barrel = 0.06, .stock = 0.05, .mag = .curved }),
    smg("Whip", 12, 0.045, 33, 0.036, 0.0045, .{ .body = 0.1, .barrel = 0.05, .stock = 0.07, .optic = .dot }),
    smg("Stinger", 16, 0.085, 30, 0.02, 0.006, .{ .body = 0.13, .barrel = 0.1, .stock = 0.08, .optic = .holo }),
    smg("Drum Kid", 12, 0.065, 50, 0.034, 0.005, .{ .body = 0.13, .barrel = 0.07, .stock = 0.06, .mag = .drum }),
    burst(smg("Burst Box", 17, 0.2, 30, 0.022, 0.006, .{ .body = 0.12, .barrel = 0.08, .stock = 0.07, .optic = .dot }), 3),

    rifle("Liner", 19, 0.095, 30, 0.018, 0.007, .{ .body = 0.16, .barrel = 0.18, .stock = 0.12, .guard = true }),
    rifle("Ranger", 21, 0.105, 30, 0.014, 0.0065, .{ .body = 0.17, .barrel = 0.2, .stock = 0.13, .guard = true, .optic = .scope2 }),
    rifle("Brick", 25, 0.12, 30, 0.022, 0.011, .{ .body = 0.17, .height = 0.034, .barrel = 0.17, .stock = 0.14, .mag = .curved }),
    burst(rifle("Tri-Shot", 22, 0.3, 30, 0.014, 0.008, .{ .body = 0.16, .barrel = 0.2, .stock = 0.12, .guard = true, .optic = .dot }), 3),
    rifle("Bullpup", 18, 0.085, 30, 0.016, 0.006, .{ .body = 0.2, .barrel = 0.1, .stock = 0, .optic = .holo }),
    rifle("Scout Carbine", 20, 0.09, 30, 0.017, 0.0065, .{ .body = 0.14, .barrel = 0.14, .stock = 0.1, .optic = .holo }),
    rifle("Thunder", 23, 0.08, 30, 0.024, 0.009, .{ .body = 0.18, .barrel = 0.12, .stock = 0.0, .mag = .curved, .optic = .dot }),
    rifle("Bruiser", 31, 0.14, 20, 0.016, 0.012, .{ .body = 0.18, .height = 0.036, .barrel = 0.22, .stock = 0.14, .guard = true, .optic = .scope2 }),

    dmr("Marksman", 45, 0.25, 10, 0.022, .{ .body = 0.18, .barrel = 0.26, .stock = 0.14, .optic = .scope4, .guard = true }),
    dmr("Tapper", 38, 0.2, 20, 0.018, .{ .body = 0.17, .barrel = 0.22, .stock = 0.13, .optic = .scope2 }),
    dmr("Pierce", 52, 0.3, 10, 0.026, .{ .body = 0.19, .barrel = 0.28, .stock = 0.15, .optic = .scope4, .mag = .curved }),
    dmr("Hunter", 62, 0.4, 5, 0.03, .{ .body = 0.19, .barrel = 0.3, .stock = 0.16, .optic = .scope4, .mag = .none }),
    dmr("Needle", 34, 0.17, 20, 0.016, .{ .body = 0.16, .barrel = 0.24, .stock = 0.12, .optic = .dot, .guard = true }),

    sniper("Longshot", 115, 1.2, 5, 2.5, 0.06, .{ .body = 0.2, .barrel = 0.4, .stock = 0.18, .optic = .scope8 }),
    sniper("Whisper", 92, 1.0, 5, 2.3, 0.045, .{ .body = 0.2, .barrel = 0.42, .stock = 0.17, .optic = .scope4 }),
    sniper("Elephant", 160, 1.7, 3, 3.0, 0.09, .{ .body = 0.22, .height = 0.04, .barrel = 0.46, .stock = 0.19, .optic = .scope8, .mag = .none }),
    sniper("Hailstone", 72, 0.45, 10, 2.6, 0.04, .{ .body = 0.21, .barrel = 0.36, .stock = 0.17, .optic = .scope4, .mag = .curved }),

    shotgun("Scatter", 9, 11, 0.75, 6, 2.2, 0.085, .{ .body = 0.13, .barrel = 0.3, .stock = 0.12, .mag = .tube }),
    shotgun("Twins", 10, 12, 0.22, 2, 2.4, 0.1, .{ .body = 0.12, .height = 0.034, .barrel = 0.32, .stock = 0.13, .mag = .none }),
    blk: {
        var s = shotgun("Rattler", 8, 8, 0.24, 8, 2.4, 0.09, .{ .body = 0.15, .barrel = 0.22, .stock = 0.11, .mag = .box });

        s.auto = true;

        break :blk s;
    },
    shotgun("Thumper", 1, 85, 0.8, 6, 2.2, 0.01, .{ .body = 0.14, .barrel = 0.34, .stock = 0.12, .mag = .tube, .optic = .dot }),
    blk: {
        var s = shotgun("Barrel Roll", 6, 9, 0.3, 20, 3.0, 0.09, .{ .body = 0.16, .barrel = 0.2, .stock = 0.1, .mag = .drum });

        s.auto = true;

        break :blk s;
    },

    lmg("Chatter", 20, 0.085, 100, 4.2, 0.03, .{ .body = 0.22, .height = 0.04, .barrel = 0.24, .stock = 0.14, .mag = .belt }),
    lmg("Drum Line", 22, 0.1, 75, 3.6, 0.028, .{ .body = 0.2, .height = 0.038, .barrel = 0.22, .stock = 0.14, .mag = .drum, .optic = .holo }),
    blk: {
        var s = lmg("Spinner", 14, 0.04, 200, 5, 0.04, .{ .body = 0.2, .height = 0.05, .barrel = 0.3, .mag = .belt });

        s.spinup = 0.7;
        s.class = .special;

        break :blk s;
    },
    lmg("Anchor", 27, 0.12, 60, 3.4, 0.024, .{ .body = 0.22, .height = 0.04, .barrel = 0.26, .stock = 0.15, .mag = .box, .optic = .scope2, .guard = true }),

    .{ .name = "Boomer", .class = .launcher, .fire = .rocket, .damage = 120, .interval = 0.9, .mag = 1, .reserve = 12, .reload = 1.3, .spread = 0, .ads_spread = 0, .recoil = 0.04, .splash = 4, .speed = 32, .knockback = 13, .look = .{ .body = 0.36, .barrel = 0.06, .mag = .none } },
    .{ .name = "Lobber", .class = .launcher, .fire = .grenade, .damage = 100, .interval = 0.6, .mag = 4, .reserve = 24, .reload = 2, .spread = 0, .ads_spread = 0, .recoil = 0.03, .splash = 4.5, .speed = 20, .gravity = 18, .knockback = 10, .look = .{ .body = 0.16, .barrel = 0.12, .mag = .drum } },
    .{ .name = "Rail", .class = .special, .damage = 140, .interval = 1.1, .mag = 4, .reserve = 20, .reload = 2.6, .spread = 0.004, .ads_spread = 0, .ads_zoom = 2.5, .recoil = 0.05, .range = 900, .charge = 0.7, .pierce = true, .look = .{ .body = 0.2, .height = 0.038, .barrel = 0.34, .stock = 0.14, .optic = .scope2 } },
    .{ .name = "Torch", .class = .special, .auto = true, .damage = 5, .pellets = 5, .interval = 0.05, .mag = 80, .reserve = 240, .reload = 2.8, .spread = 0.12, .ads_spread = 0.1, .ads_zoom = 1.1, .range = 10, .recoil = 0.001, .flame = true, .look = .{ .body = 0.16, .height = 0.04, .barrel = 0.2, .mag = .drum } },

    .{ .name = "Recurve", .class = .bow, .fire = .arrow, .damage = 95, .interval = 0.2, .mag = 1, .reserve = 30, .reload = 0.45, .spread = 0.01, .ads_spread = 0, .ads_zoom = 2, .recoil = 0.01, .speed = 55, .gravity = 9, .charge = 0.8, .look = .{ .body = 0.05, .barrel = 0.3, .mag = .none } },
    .{ .name = "Longbow", .class = .bow, .fire = .arrow, .damage = 135, .interval = 0.25, .mag = 1, .reserve = 24, .reload = 0.55, .spread = 0.01, .ads_spread = 0, .ads_zoom = 2.2, .recoil = 0.012, .speed = 70, .gravity = 7, .charge = 1.15, .look = .{ .body = 0.05, .barrel = 0.36, .mag = .none } },
    .{ .name = "Crossbow", .class = .crossbow, .fire = .bolt, .damage = 120, .interval = 0.3, .mag = 1, .reserve = 20, .reload = 1.6, .spread = 0.008, .ads_spread = 0, .ads_zoom = 2.5, .recoil = 0.02, .speed = 90, .gravity = 4, .look = .{ .body = 0.18, .barrel = 0.08, .stock = 0.12, .mag = .none, .optic = .scope2 } },
    .{ .name = "Rapid Bolt", .class = .crossbow, .fire = .bolt, .damage = 55, .interval = 0.35, .mag = 6, .reserve = 36, .reload = 2.2, .spread = 0.012, .ads_spread = 0.002, .ads_zoom = 2, .recoil = 0.015, .speed = 80, .gravity = 5, .look = .{ .body = 0.16, .barrel = 0.08, .stock = 0.1, .mag = .box, .optic = .dot } },

    blade("Katana", 46, 0.42, 2.7, 4, 0, 1.02),
    blade("Longsword", 62, 0.6, 3.0, 7, 0, 1.12),
    blade("Scimitar", 52, 0.5, 2.8, 5, 0, 0.95),
    blade("Machete", 38, 0.34, 2.3, 3, 0, 0.66),
    blade("Vampire Blade", 54, 0.5, 2.9, 5, 0.3, 1.08),

    .{ .name = "Edge", .class = .melee, .fire = .melee, .auto = true, .damage = 34, .interval = 0.3, .knockback = 2, .mag = 0, .reserve = 0, .reload = 0, .spread = 0, .ads_spread = 0, .ads_zoom = 1, .range = 2.4, .recoil = 0, .look = .{ .body = 0.1, .barrel = 0.15, .mag = .none } },
};

pub const count = specs.len;

fn rank(o: Optic) u8 {
    return @intFromEnum(o);
}

pub fn magnified(o: Optic) bool {
    return rank(o) >= rank(.scope2);
}

pub fn spreadFor(s: Spec, ads: f32, moving: f32, grounded: bool) f32 {
    const airborne: f32 = if (grounded) 0 else 0.02;

    return s.spread + (s.ads_spread - s.spread) * ads + (moving * 0.015 + airborne) * (1 - ads);
}

const hitch: f32 = 0.05;

pub fn cool(left: f32, dt: f32) f32 {
    if (left <= 0) return 0;

    const next = left - dt;

    return if (next < 0 and dt > hitch) 0 else next;
}

pub fn rearm(left: f32, interval: f32) f32 {
    return interval + @min(left, 0);
}

const sight_zoom: f32 = 1.31;

fn defaultOptic(s: Spec) ?Optic {
    if (s.flame) return null;

    const o = s.look.optic;

    return switch (s.class) {
        .pistol => if (o == .iron) .dot else null,
        .smg => if (o == .iron) .holo else null,
        .rifle => if (o == .iron) .scope2 else null,
        .dmr => if (rank(o) < rank(.scope4)) .scope4 else null,
        .sniper => if (o != .scope8) .scope8 else null,
        .shotgun => if (o == .iron or o == .dot) .holo else null,
        .lmg => if (rank(o) < rank(.scope2)) .scope2 else null,
        .launcher, .special => if (o == .iron) .holo else null,
        else => null,
    };
}

fn outfit(comptime raw: []const Spec) [raw.len]Spec {
    var out: [raw.len]Spec = raw[0..raw.len].*;

    for (&out) |*s| {
        if (defaultOptic(s.*)) |o| {
            s.look.optic = o;
            s.ads_zoom = @max(s.ads_zoom, zoomFor(o));
        }

        if (!magnified(s.look.optic) and s.ads_zoom >= 2) s.ads_zoom *= sight_zoom / 2.0;
    }

    return out;
}

pub fn indexOf(comptime name: []const u8) u8 {
    for (specs, 0..) |s, i| {
        if (std_eql(s.name, name)) return @intCast(i);
    }

    @compileError("unknown weapon " ++ name);
}

fn std_eql(a: []const u8, b: []const u8) bool {
    if (a.len != b.len) return false;

    for (a, b) |x, y| {
        if (x != y) return false;
    }

    return true;
}

pub const knife = indexOf("Edge");

pub const swords = [_]u8{ indexOf("Katana"), indexOf("Longsword"), indexOf("Scimitar"), indexOf("Machete") };

pub const grenade = Spec{
    .name = "Grenade",
    .class = .launcher,
    .fire = .grenade,
    .damage = 110,
    .interval = 0.8,
    .mag = 3,
    .reserve = 0,
    .reload = 0,
    .spread = 0,
    .ads_spread = 0,
    .recoil = 0,
    .splash = 5,
    .speed = 16,
    .gravity = 18,
    .knockback = 11,
    .look = .{ .body = 0, .barrel = 0 },
};

pub fn splashFalloff(distance: f32, radius: f32) f32 {
    if (distance >= radius) return 0;

    return 1 - (distance / radius) * 0.7;
}
