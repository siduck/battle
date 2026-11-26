const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{ .preferred_optimize_mode = .ReleaseFast });

    addServer(b, if (optimize == .debug) .debug else .safe);

    if (b.option(bool, "android", "Build a signed arm64 Android APK into zig-out/dronefire.apk") orelse false) {
        buildAndroid(b, optimize);

        return;
    }

    const shared = b.createModule(.{
        .root_source_file = b.path("src/shared/root.zig"),
        .target = target,
        .optimize = optimize,
    });

    const raylib_dep = b.dependency("raylib", .{
        .target = target,
        .optimize = optimize,
        .config = @as([]const u8, "-DSUPPORT_FILEFORMAT_HDR=1"),
    });

    const client = b.createModule(.{
        .root_source_file = b.path("src/client/main.zig"),
        .target = target,
        .optimize = optimize,
        .strip = optimize != .debug,
        .link_libc = true,
        .imports = &.{
            .{ .name = "shared", .module = shared },
            .{ .name = "raylib", .module = raylib_dep.module("raylib") },
            .{ .name = "rlgl", .module = raylib_dep.module("rlgl") },
            .{ .name = "raymath", .module = raylib_dep.module("raymath") },
        },
    });

    const exe = b.addExecutable(.{
        .name = "dronefire",
        .root_module = client,
    });

    b.installArtifact(exe);
    b.installDirectory(.{
        .source_dir = b.path("src/client/assets/ui"),
        .install_dir = .prefix,
        .install_subdir = "share/dronefire/ui",
    });
    b.installDirectory(.{
        .source_dir = b.path("src/client/assets/guns"),
        .install_dir = .prefix,
        .install_subdir = "share/dronefire/guns",
    });
    b.installDirectory(.{
        .source_dir = b.path("src/client/assets/sky"),
        .install_dir = .prefix,
        .install_subdir = "share/dronefire/sky",
    });
    b.installDirectory(.{
        .source_dir = b.path("src/client/assets/props"),
        .install_dir = .prefix,
        .install_subdir = "share/dronefire/props",
    });
    b.installDirectory(.{
        .source_dir = b.path("src/client/assets/air"),
        .install_dir = .prefix,
        .install_subdir = "share/dronefire/air",
    });
    b.installDirectory(.{
        .source_dir = b.path("src/client/assets/cars"),
        .install_dir = .prefix,
        .install_subdir = "share/dronefire/cars",
    });
    b.installDirectory(.{
        .source_dir = b.path("src/client/assets/sounds"),
        .install_dir = .prefix,
        .install_subdir = "share/dronefire/sounds",
    });
    b.installDirectory(.{
        .source_dir = b.path("src/client/assets/characters"),
        .install_dir = .prefix,
        .install_subdir = "share/dronefire/characters",
    });
    b.installDirectory(.{
        .source_dir = b.path("src/client/assets/textures"),
        .install_dir = .prefix,
        .install_subdir = "share/dronefire/textures",
    });

    const run = b.addRunArtifact(exe);

    run.step.dependOn(b.getInstallStep());
    b.step("run", "Run the game").dependOn(&run.step);
}

fn serverExe(b: *std.Build, target: std.Build.ResolvedTarget, optimize: std.builtin.OptimizeMode) *std.Build.Step.Compile {
    const shared = b.createModule(.{
        .root_source_file = b.path("src/shared/root.zig"),
        .target = target,
        .optimize = optimize,
    });

    return b.addExecutable(.{
        .name = "battle-server",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/server/main.zig"),
            .target = target,
            .optimize = optimize,
            .strip = optimize != .debug,
            .link_libc = true,
            .imports = &.{.{ .name = "shared", .module = shared }},
        }),
        .linkage = .static,
    });
}

fn addServer(b: *std.Build, optimize: std.builtin.OptimizeMode) void {
    const arm = serverExe(b, b.resolveTargetQuery(.{ .cpu_arch = .aarch64, .os_tag = .linux, .abi = .musl }), optimize);
    const local = serverExe(b, b.resolveTargetQuery(.{ .abi = .musl }), optimize);

    b.step("server", "Build the static aarch64 battle-server into zig-out/server/").dependOn(&b.addInstallArtifact(arm, .{ .dest_dir = .{ .override = .{ .custom = "server" } } }).step);
    b.step("server-local", "Build battle-server for this machine into zig-out/bin/").dependOn(&b.addInstallArtifact(local, .{}).step);

    const shared_tests = b.addTest(.{ .root_module = b.createModule(.{
        .root_source_file = b.path("src/shared/net.zig"),
        .target = b.graph.host,
        .optimize = .debug,
    }) });

    b.step("test-net", "Run netcode tests").dependOn(&b.addRunArtifact(shared_tests).step);
}

const manifest_xml =
    \\<?xml version="1.0" encoding="utf-8"?>
    \\<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.dronefire.game" android:versionCode="1" android:versionName="0.1">
    \\    <uses-sdk android:minSdkVersion="24" android:targetSdkVersion="35"/>
    \\    <uses-permission android:name="android.permission.INTERNET"/>
    \\    <uses-feature android:glEsVersion="0x00030000" android:required="true"/>
    \\    <uses-feature android:name="android.hardware.touchscreen" android:required="false"/>
    \\    <uses-feature android:name="android.hardware.gamepad" android:required="false"/>
    \\    <application android:label="Dronefire" android:hasCode="false" android:extractNativeLibs="true" android:isGame="true" android:appCategory="game">
    \\        <activity android:name="android.app.NativeActivity" android:exported="true" android:launchMode="singleTask" android:screenOrientation="sensorLandscape" android:resizeableActivity="false" android:theme="@android:style/Theme.NoTitleBar.Fullscreen" android:configChanges="orientation|keyboardHidden|keyboard|screenSize|screenLayout|smallestScreenSize|navigation|uiMode|density">
    \\            <meta-data android:name="android.app.lib_name" android:value="main"/>
    \\            <intent-filter>
    \\                <action android:name="android.intent.action.MAIN"/>
    \\                <category android:name="android.intent.category.LAUNCHER"/>
    \\            </intent-filter>
    \\        </activity>
    \\    </application>
    \\</manifest>
    \\
;

fn buildAndroid(b: *std.Build, optimize: std.builtin.OptimizeMode) void {
    const home = b.graph.environ_map.get("HOME") orelse "";
    const sdk = b.option([]const u8, "android_sdk", "Folder with ndk/, build-tools/ and platform/") orelse b.fmt("{s}/.local/opt/android", .{home});
    const ndk = b.fmt("{s}/ndk", .{sdk});
    const sysroot = b.fmt("{s}/toolchains/llvm/prebuilt/linux-x86_64/sysroot", .{ndk});
    const libs = b.fmt("{s}/usr/lib/aarch64-linux-android/24", .{sysroot});
    const glue = b.fmt("{s}/sources/android/native_app_glue", .{ndk});
    const target = b.resolveTargetQuery(.{ .cpu_arch = .aarch64, .os_tag = .linux, .abi = .android, .android_api_level = 24 });

    const shared = b.createModule(.{
        .root_source_file = b.path("src/shared/root.zig"),
        .target = target,
        .optimize = optimize,
    });

    const raylib_dep = b.dependency("raylib", .{
        .target = target,
        .optimize = optimize,
        .platform = .android,
        .android_ndk = ndk,
        .android_api_version = @as([]const u8, "24"),
        .config = @as([]const u8, "-DSUPPORT_FILEFORMAT_HDR=1 -DGRAPHICS_API_OPENGL_ES3"),
    });

    const headers = [_][]const u8{ "raylib", "rlgl", "raymath" };
    var bindings: [headers.len]*std.Build.Module = undefined;

    for (headers, 0..) |name, i| {
        const translate = b.addTranslateC(.{
            .root_source_file = raylib_dep.path(b.fmt("src/{s}.h", .{name})),
            .target = target,
            .optimize = optimize,
            .link_libc = false,
        });

        translate.addSystemIncludePath(.{ .cwd_relative = b.fmt("{s}/usr/include", .{sysroot}) });
        translate.addSystemIncludePath(.{ .cwd_relative = b.fmt("{s}/usr/include/aarch64-linux-android", .{sysroot}) });
        bindings[i] = translate.createModule();
        bindings[i].linkLibrary(raylib_dep.artifact("raylib"));
    }

    const client = b.createModule(.{
        .root_source_file = b.path("src/client/android_main.zig"),
        .target = target,
        .optimize = optimize,
        .link_libc = true,
        .strip = true,
        .imports = &.{
            .{ .name = "shared", .module = shared },
            .{ .name = "raylib", .module = bindings[0] },
            .{ .name = "rlgl", .module = bindings[1] },
            .{ .name = "raymath", .module = bindings[2] },
        },
    });

    client.addSystemIncludePath(.{ .cwd_relative = b.fmt("{s}/usr/include", .{sysroot}) });
    client.addSystemIncludePath(.{ .cwd_relative = b.fmt("{s}/usr/include/aarch64-linux-android", .{sysroot}) });
    client.addSystemIncludePath(.{ .cwd_relative = glue });
    client.addCSourceFile(.{ .file = .{ .cwd_relative = b.fmt("{s}/android_native_app_glue.c", .{glue}) } });
    client.addLibraryPath(.{ .cwd_relative = libs });

    for ([_][]const u8{ "android", "log", "EGL", "GLESv3", "m", "dl" }) |name| client.linkSystemLibrary(name, .{});

    const lib = b.addLibrary(.{
        .name = "main",
        .linkage = .dynamic,
        .root_module = client,
    });

    const libc_txt = b.addWriteFiles().add("android-libc.txt", b.fmt(
        \\include_dir={0s}/usr/include
        \\sys_include_dir={0s}/usr/include/aarch64-linux-android
        \\cc_dir={1s}
        \\crt_dir={1s}
        \\msvc_lib_dir=
        \\kernel32_lib_dir=
        \\darwin_sdk_dir=
        \\
    , .{ sysroot, libs }));

    lib.setLibCFile(libc_txt);
    raylib_dep.artifact("raylib").setLibCFile(libc_txt);

    const manifest = b.addWriteFiles().add("AndroidManifest.xml", manifest_xml);
    const staged = b.addWriteFiles();

    for ([_][]const u8{ "guns", "sky", "props", "cars", "characters", "sounds", "ui", "textures", "air" }) |name| {
        _ = staged.addCopyDirectory(b.path(b.fmt("src/client/assets/{s}", .{name})), b.fmt("assets/{s}", .{name}), .{});
    }

    const tool = b.addExecutable(.{
        .name = "apk",
        .root_module = b.createModule(.{
            .root_source_file = b.path("tools/apk.zig"),
            .target = b.graph.host,
            .optimize = .ReleaseSafe,
        }),
    });
    const pack = b.addRunArtifact(tool);

    pack.addArg(sdk);
    pack.addFileArg(manifest);
    pack.addArtifactArg(lib);
    pack.addDirectoryArg(staged.getDirectory().path(b, "assets"));

    const apk = pack.addOutputFileArg("dronefire.apk");

    b.getInstallStep().dependOn(&b.addInstallFile(apk, "dronefire.apk").step);
}
