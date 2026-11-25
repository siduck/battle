const terrain = @import("../terrain.zig");
const props = @import("../props.zig");
const api = @import("api.zig");

pub const Def = api.Def;

const all = struct {
    pub const desert = @import("desert.zig");
    pub const islands = @import("islands.zig");
    pub const airport = @import("airport.zig");
    pub const alpine = @import("alpine.zig");
    pub const coast = @import("coast.zig");
    pub const construction = @import("construction.zig");
    pub const japan = @import("japan.zig");
    pub const forest = @import("forest.zig");
    pub const nyc = @import("nyc.zig");
    pub const pirate = @import("pirate.zig");
    pub const prehistoric = @import("prehistoric.zig");
    pub const racing = @import("racing.zig");
    pub const lab = @import("lab.zig");
    pub const salvage = @import("salvage.zig");
    pub const stadium = @import("stadium.zig");
    pub const warehouse = @import("warehouse.zig");
};

pub fn get(m: terrain.Map) ?*const Def {
    switch (m) {
        inline else => |t| {
            const name = @tagName(t);

            if (@hasDecl(all, name)) return &@field(all, name).def;

            return null;
        },
    }
}

pub fn current() ?*const Def {
    return get(terrain.current);
}

pub fn activate() void {
    const d = current() orelse {
        props.local = &.{};

        return;
    };

    props.local = d.props;
}
