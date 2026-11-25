import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import apksign

ASSET_DIRS = ["guns", "sky", "props", "cars", "characters"]


def main():
    sdk, manifest, lib, assets, out = sys.argv[1:6]
    tools = os.path.join(sdk, "build-tools")
    android_jar = os.path.join(sdk, "platform", "android.jar")
    key = os.path.join(sdk, "debug-key.pem")
    cert = os.path.join(sdk, "debug-cert.der")

    with tempfile.TemporaryDirectory() as tmp:
        staged = os.path.join(tmp, "assets")

        for name in ASSET_DIRS:
            source = os.path.join(assets, name)

            if os.path.isdir(source):
                shutil.copytree(source, os.path.join(staged, name))

        base = os.path.join(tmp, "base.apk")
        aligned = os.path.join(tmp, "aligned.apk")

        subprocess.run([os.path.join(tools, "aapt2"), "link", "-o", base, "--manifest", manifest, "-I", android_jar, "-A", staged], check=True)

        with zipfile.ZipFile(base, "a", zipfile.ZIP_DEFLATED) as apk:
            apk.write(lib, "lib/arm64-v8a/libmain.so")

        subprocess.run([os.path.join(tools, "zipalign"), "-f", "-p", "4", base, aligned], check=True)
        apksign.sign(aligned, out, key, cert)


if __name__ == "__main__":
    main()
