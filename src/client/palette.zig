const shared = @import("shared");

const Paint = shared.map.Paint;

pub const Rgb = [3]u8;

pub fn of(p: Paint) Rgb {
    return switch (p) {
        .floor => .{ 232, 220, 196 },
        .floor_alt => .{ 220, 206, 180 },
        .wall => .{ 118, 156, 224 },
        .coral => .{ 246, 126, 100 },
        .coral_dark => .{ 206, 88, 78 },
        .teal => .{ 58, 190, 172 },
        .teal_dark => .{ 36, 140, 136 },
        .cream => .{ 250, 236, 206 },
        .sunny => .{ 252, 196, 60 },
        .wood => .{ 226, 156, 84 },
        .red => .{ 236, 74, 70 },
        .blue => .{ 58, 120, 234 },
        .orange => .{ 248, 140, 48 },
        .mint => .{ 120, 216, 156 },
        .lavender => .{ 170, 138, 236 },
        .steel => .{ 150, 162, 186 },
        .yellow => .{ 255, 214, 64 },
        .white => .{ 244, 244, 250 },
        .purple => .{ 146, 92, 230 },
        .green => .{ 92, 196, 104 },
        .dark => .{ 58, 62, 80 },
        .grass => .{ 120, 196, 110 },
        .olive => .{ 92, 102, 70 },
        .tan => .{ 168, 146, 108 },
        .glove => .{ 46, 48, 52 },
    };
}

pub const rarity_paint = [_]Paint{ .steel, .green, .blue, .purple, .yellow };
