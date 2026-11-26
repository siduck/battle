const std = @import("std");

const Io = std.Io;
const Allocator = std.mem.Allocator;
const Sha256 = std.crypto.hash.sha2.Sha256;

const magic = "APK Sig Block 42";
const v2_id: u32 = 0x7109871A;
const rsa_sha256: u32 = 0x0103;
const chunk_size: usize = 1 << 20;
const lib_name = "lib/arm64-v8a/libmain.so";

const Ctx = struct {
    gpa: Allocator,
    io: Io,
    tmp: []const u8,
};

const Eocd = struct {
    pos: usize,
    cd_off: usize,
    cd_size: usize,
};

pub fn main(init: std.process.Init) !void {
    const arena = init.arena.allocator();
    const args = try init.minimal.args.toSlice(arena);

    if (args.len < 7) std.process.fatal("usage: apk <sdk> <manifest> <lib> <assets> <res> <out>", .{});

    const sdk = args[1];
    const manifest = args[2];
    const lib = args[3];
    const assets = args[4];
    const res = args[5];
    const out = args[6];
    const tmp = try std.fmt.allocPrint(arena, "{s}.tmp", .{out});
    const ctx: Ctx = .{ .gpa = arena, .io = init.io, .tmp = tmp };
    const cwd = Io.Dir.cwd();

    cwd.deleteTree(ctx.io, tmp) catch {};
    try cwd.createDirPath(ctx.io, tmp);
    defer cwd.deleteTree(ctx.io, tmp) catch {};

    const tools = try std.fs.path.join(arena, &.{ sdk, "build-tools" });
    const android_jar = try std.fs.path.join(arena, &.{ sdk, "platform", "android.jar" });
    const key = try std.fs.path.join(arena, &.{ sdk, "debug-key.pem" });
    const cert = try std.fs.path.join(arena, &.{ sdk, "debug-cert.der" });
    const base = try std.fs.path.join(arena, &.{ tmp, "base.apk" });
    const aligned = try std.fs.path.join(arena, &.{ tmp, "aligned.apk" });
    const res_zip = try std.fs.path.join(arena, &.{ tmp, "res.zip" });
    const aapt2 = try std.fs.path.join(arena, &.{ tools, "aapt2" });
    const zipalign = try std.fs.path.join(arena, &.{ tools, "zipalign" });

    _ = try exec(ctx, &.{ aapt2, "compile", "--dir", res, "-o", res_zip });
    _ = try exec(ctx, &.{ aapt2, "link", "-o", base, "--manifest", manifest, "-I", android_jar, "-A", assets, res_zip });
    try appendStored(ctx, base, lib, lib_name);
    _ = try exec(ctx, &.{ zipalign, "-f", "-p", "4", base, aligned });
    try sign(ctx, aligned, out, key, cert);
}

fn exec(ctx: Ctx, argv: []const []const u8) ![]u8 {
    const result = try std.process.run(ctx.gpa, ctx.io, .{ .argv = argv });

    if (!result.term.success()) std.process.fatal("{s} failed: {s}", .{ argv[0], result.stderr });

    return result.stdout;
}

fn execOk(ctx: Ctx, argv: []const []const u8) !bool {
    const result = try std.process.run(ctx.gpa, ctx.io, .{ .argv = argv });

    return result.term.success();
}

fn readAll(ctx: Ctx, path: []const u8) ![]u8 {
    return Io.Dir.cwd().readFileAlloc(ctx.io, path, ctx.gpa, .unlimited);
}

fn writeAll(ctx: Ctx, path: []const u8, data: []const u8) !void {
    try Io.Dir.cwd().writeFile(ctx.io, .{ .sub_path = path, .data = data });
}

fn exists(ctx: Ctx, path: []const u8) bool {
    Io.Dir.cwd().access(ctx.io, path, .{}) catch return false;

    return true;
}

fn tmpPath(ctx: Ctx, name: []const u8) ![]const u8 {
    return std.fs.path.join(ctx.gpa, &.{ ctx.tmp, name });
}

fn u16At(buf: []const u8, pos: usize) u16 {
    return std.mem.readInt(u16, buf[pos..][0..2], .little);
}

fn u32At(buf: []const u8, pos: usize) u32 {
    return std.mem.readInt(u32, buf[pos..][0..4], .little);
}

fn u64At(buf: []const u8, pos: usize) u64 {
    return std.mem.readInt(u64, buf[pos..][0..8], .little);
}

fn put16(list: *std.ArrayList(u8), gpa: Allocator, v: u16) !void {
    var b: [2]u8 = undefined;

    std.mem.writeInt(u16, &b, v, .little);
    try list.appendSlice(gpa, &b);
}

fn put32(list: *std.ArrayList(u8), gpa: Allocator, v: u32) !void {
    var b: [4]u8 = undefined;

    std.mem.writeInt(u32, &b, v, .little);
    try list.appendSlice(gpa, &b);
}

fn put64(list: *std.ArrayList(u8), gpa: Allocator, v: u64) !void {
    var b: [8]u8 = undefined;

    std.mem.writeInt(u64, &b, v, .little);
    try list.appendSlice(gpa, &b);
}

fn lp(gpa: Allocator, parts: []const []const u8) ![]u8 {
    var list: std.ArrayList(u8) = .empty;
    var n: usize = 0;

    for (parts) |p| n += p.len;

    try put32(&list, gpa, @intCast(n));

    for (parts) |p| try list.appendSlice(gpa, p);

    return list.toOwnedSlice(gpa);
}

fn le32(v: u32) [4]u8 {
    var b: [4]u8 = undefined;

    std.mem.writeInt(u32, &b, v, .little);

    return b;
}

fn findEocd(apk: []const u8) Eocd {
    const pos = std.mem.lastIndexOf(u8, apk, "PK\x05\x06") orelse std.process.fatal("apksign: no end of central directory", .{});

    return .{ .pos = pos, .cd_size = u32At(apk, pos + 12), .cd_off = u32At(apk, pos + 16) };
}

fn appendStored(ctx: Ctx, apk_path: []const u8, file_path: []const u8, name: []const u8) !void {
    const gpa = ctx.gpa;
    const apk = try readAll(ctx, apk_path);
    const data = try readAll(ctx, file_path);
    const eocd = findEocd(apk);
    const crc = std.hash.Crc32.hash(data);
    const size: u32 = @intCast(data.len);
    var out: std.ArrayList(u8) = .empty;

    try out.appendSlice(gpa, apk[0..eocd.cd_off]);

    const local_off: u32 = @intCast(out.items.len);

    try put32(&out, gpa, 0x04034b50);
    try put16(&out, gpa, 10);
    try put16(&out, gpa, 0);
    try put16(&out, gpa, 0);
    try put16(&out, gpa, 0);
    try put16(&out, gpa, 0x21);
    try put32(&out, gpa, crc);
    try put32(&out, gpa, size);
    try put32(&out, gpa, size);
    try put16(&out, gpa, @intCast(name.len));
    try put16(&out, gpa, 0);
    try out.appendSlice(gpa, name);
    try out.appendSlice(gpa, data);

    const cd_off: u32 = @intCast(out.items.len);

    try out.appendSlice(gpa, apk[eocd.cd_off .. eocd.cd_off + eocd.cd_size]);
    try put32(&out, gpa, 0x02014b50);
    try put16(&out, gpa, 0x0314);
    try put16(&out, gpa, 10);
    try put16(&out, gpa, 0);
    try put16(&out, gpa, 0);
    try put16(&out, gpa, 0);
    try put16(&out, gpa, 0x21);
    try put32(&out, gpa, crc);
    try put32(&out, gpa, size);
    try put32(&out, gpa, size);
    try put16(&out, gpa, @intCast(name.len));
    try put16(&out, gpa, 0);
    try put16(&out, gpa, 0);
    try put16(&out, gpa, 0);
    try put16(&out, gpa, 0);
    try put32(&out, gpa, 0o100644 << 16);
    try put32(&out, gpa, local_off);
    try out.appendSlice(gpa, name);

    const cd_size: u32 = @intCast(out.items.len - cd_off);
    const entries = u16At(apk, eocd.pos + 10) + 1;
    const tail = apk[eocd.pos..];

    try put32(&out, gpa, 0x06054b50);
    try put16(&out, gpa, 0);
    try put16(&out, gpa, 0);
    try put16(&out, gpa, entries);
    try put16(&out, gpa, entries);
    try put32(&out, gpa, cd_size);
    try put32(&out, gpa, cd_off);
    try out.appendSlice(gpa, tail[20..]);
    try writeAll(ctx, apk_path, out.items);
}

fn sectionDigests(list: *std.ArrayList([32]u8), gpa: Allocator, section: []const u8) !void {
    var start: usize = 0;

    while (start < section.len) : (start += chunk_size) {
        const chunk = section[start..@min(section.len, start + chunk_size)];
        var h = Sha256.init(.{});
        var digest: [32]u8 = undefined;

        h.update(&.{0xa5});
        h.update(&le32(@intCast(chunk.len)));
        h.update(chunk);
        h.final(&digest);
        try list.append(gpa, digest);
    }
}

fn contentDigest(gpa: Allocator, apk: []const u8, entries_end: usize, cd_start: usize, eocd_pos: usize) ![32]u8 {
    const eocd = try gpa.dupe(u8, apk[eocd_pos..]);
    var chunks: std.ArrayList([32]u8) = .empty;
    var h = Sha256.init(.{});
    var digest: [32]u8 = undefined;

    std.mem.writeInt(u32, eocd[16..20], @intCast(entries_end), .little);
    try sectionDigests(&chunks, gpa, apk[0..entries_end]);
    try sectionDigests(&chunks, gpa, apk[cd_start..eocd_pos]);
    try sectionDigests(&chunks, gpa, eocd);
    h.update(&.{0x5a});
    h.update(&le32(@intCast(chunks.items.len)));

    for (chunks.items) |c| h.update(&c);

    h.final(&digest);

    return digest;
}

fn ensureKey(ctx: Ctx, key: []const u8, cert: []const u8) !void {
    if (exists(ctx, key) and exists(ctx, cert)) return;

    _ = try exec(ctx, &.{ "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", cert, "-days", "10000", "-subj", "/CN=dronefire debug", "-outform", "DER" });
}

fn sign(ctx: Ctx, src: []const u8, dst: []const u8, key: []const u8, cert: []const u8) !void {
    const gpa = ctx.gpa;

    try ensureKey(ctx, key, cert);

    const apk = try readAll(ctx, src);
    const eocd = findEocd(apk);

    if (eocd.cd_off >= 16 and std.mem.eql(u8, apk[eocd.cd_off - 16 .. eocd.cd_off], magic)) std.process.fatal("apksign: already signed", .{});

    const digest = try contentDigest(gpa, apk, eocd.cd_off, eocd.cd_off, eocd.pos);
    const cert_der = try readAll(ctx, cert);
    const public_pem = try exec(ctx, &.{ "openssl", "x509", "-inform", "DER", "-in", cert, "-noout", "-pubkey" });
    const pem_path = try tmpPath(ctx, "pub.pem");

    try writeAll(ctx, pem_path, public_pem);

    const public_der = try exec(ctx, &.{ "openssl", "pkey", "-pubin", "-in", pem_path, "-outform", "DER" });
    const digest_entry = try std.mem.concat(gpa, u8, &.{ &le32(rsa_sha256), try lp(gpa, &.{&digest}) });
    const digests = try lp(gpa, &.{try lp(gpa, &.{digest_entry})});
    const certs = try lp(gpa, &.{try lp(gpa, &.{cert_der})});
    const attrs = try lp(gpa, &.{});
    const signed_data = try std.mem.concat(gpa, u8, &.{ digests, certs, attrs });
    const data_path = try tmpPath(ctx, "signed.bin");

    try writeAll(ctx, data_path, signed_data);

    const signature = try exec(ctx, &.{ "openssl", "dgst", "-sha256", "-sign", key, data_path });
    const sig_entry = try std.mem.concat(gpa, u8, &.{ &le32(rsa_sha256), try lp(gpa, &.{signature}) });
    const signer = try std.mem.concat(gpa, u8, &.{ try lp(gpa, &.{signed_data}), try lp(gpa, &.{try lp(gpa, &.{sig_entry})}), try lp(gpa, &.{public_der}) });
    const value = try lp(gpa, &.{try lp(gpa, &.{signer})});
    var pair: std.ArrayList(u8) = .empty;

    try put64(&pair, gpa, value.len + 4);
    try put32(&pair, gpa, v2_id);
    try pair.appendSlice(gpa, value);

    const size: u64 = pair.items.len + 8 + magic.len;
    var block: std.ArrayList(u8) = .empty;

    try put64(&block, gpa, size);
    try block.appendSlice(gpa, pair.items);
    try put64(&block, gpa, size);
    try block.appendSlice(gpa, magic);

    const tail = try gpa.dupe(u8, apk[eocd.pos..]);

    std.mem.writeInt(u32, tail[16..20], @intCast(eocd.cd_off + block.items.len), .little);

    const out = try std.mem.concat(gpa, u8, &.{ apk[0..eocd.cd_off], block.items, apk[eocd.cd_off..eocd.pos], tail });

    try writeAll(ctx, dst, out);
    try verify(ctx, dst);
}

fn take(buf: []const u8, pos: usize) struct { []const u8, usize } {
    const n = u32At(buf, pos);

    return .{ buf[pos + 4 .. pos + 4 + n], pos + 4 + n };
}

fn verify(ctx: Ctx, path: []const u8) !void {
    const apk = try readAll(ctx, path);
    const eocd = findEocd(apk);

    if (!std.mem.eql(u8, apk[eocd.cd_off - 16 .. eocd.cd_off], magic)) std.process.fatal("apksign verify: no signing block", .{});

    const size: usize = @intCast(u64At(apk, eocd.cd_off - 24));
    const block_start = eocd.cd_off - size - 8;
    const pairs = apk[block_start + 8 .. eocd.cd_off - 24];
    var pos: usize = 0;
    var value: ?[]const u8 = null;

    while (pos < pairs.len) {
        const n: usize = @intCast(u64At(pairs, pos));
        const kind = u32At(pairs, pos + 8);

        if (kind == v2_id) value = pairs[pos + 12 .. pos + 8 + n];

        pos += 8 + n;
    }

    const v = value orelse std.process.fatal("apksign verify: no v2 block", .{});
    const signers, _ = take(v, 0);
    const signer, _ = take(signers, 0);
    const signed_data, const p1 = take(signer, 0);
    const signatures, const p2 = take(signer, p1);
    const public_der, _ = take(signer, p2);
    const sig_entry, _ = take(signatures, 0);
    const algo = u32At(sig_entry, 0);
    const signature, _ = take(sig_entry, 4);
    const digests, _ = take(signed_data, 0);
    const digest_entry, _ = take(digests, 0);
    const stored, _ = take(digest_entry, 4);
    const actual = try contentDigest(ctx.gpa, apk, block_start, eocd.cd_off, eocd.pos);

    if (algo != rsa_sha256 or !std.mem.eql(u8, stored, &actual)) std.process.fatal("apksign verify: digest mismatch", .{});

    const data_path = try tmpPath(ctx, "verify.data");
    const sig_path = try tmpPath(ctx, "verify.sig");
    const key_path = try tmpPath(ctx, "verify.der");

    try writeAll(ctx, data_path, signed_data);
    try writeAll(ctx, sig_path, signature);
    try writeAll(ctx, key_path, public_der);

    if (!try execOk(ctx, &.{ "openssl", "dgst", "-sha256", "-verify", key_path, "-keyform", "DER", "-signature", sig_path, data_path })) std.process.fatal("apksign verify: bad signature", .{});
}
