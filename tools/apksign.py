import hashlib
import os
import struct
import subprocess
import sys
import tempfile

MAGIC = b"APK Sig Block 42"
V2_ID = 0x7109871A
RSA_SHA256 = 0x0103
CHUNK = 1 << 20


def lp(data):
    return struct.pack("<I", len(data)) + data


def find_eocd(apk):
    pos = apk.rfind(b"PK\x05\x06")

    if pos < 0:
        sys.exit("apksign: no end of central directory")

    cd_size, cd_off = struct.unpack("<II", apk[pos + 12 : pos + 20])

    return pos, cd_off, cd_size


def section_digest(section):
    digests = []

    for start in range(0, len(section), CHUNK):
        chunk = section[start : start + CHUNK]
        digests.append(hashlib.sha256(b"\xa5" + struct.pack("<I", len(chunk)) + chunk).digest())

    return digests


def content_digest(apk, entries_end, cd_start, eocd_pos):
    eocd = bytearray(apk[eocd_pos:])
    eocd[16:20] = struct.pack("<I", entries_end)
    chunks = section_digest(apk[:entries_end]) + section_digest(apk[cd_start:eocd_pos]) + section_digest(bytes(eocd))

    return hashlib.sha256(b"\x5a" + struct.pack("<I", len(chunks)) + b"".join(chunks)).digest()


def openssl(*args, data=None):
    return subprocess.run(["openssl", *args], input=data, capture_output=True, check=True).stdout


def ensure_key(key, cert):
    if os.path.exists(key) and os.path.exists(cert):
        return

    openssl("req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", cert, "-days", "10000", "-subj", "/CN=dronefire debug", "-outform", "DER")


def sign(src, dst, key, cert):
    ensure_key(key, cert)

    apk = open(src, "rb").read()
    eocd_pos, cd_off, cd_size = find_eocd(apk)

    if apk[cd_off - 16 : cd_off] == MAGIC:
        sys.exit("apksign: already signed")

    digest = content_digest(apk, cd_off, cd_off, eocd_pos)
    cert_der = open(cert, "rb").read()
    public_key = openssl("x509", "-inform", "DER", "-in", cert, "-noout", "-pubkey")
    public_der = openssl("pkey", "-pubin", "-outform", "DER", data=public_key)
    digests = lp(lp(struct.pack("<I", RSA_SHA256) + lp(digest)))
    signed_data = digests + lp(lp(cert_der)) + lp(b"")

    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(signed_data)
        tmp.flush()
        signature = openssl("dgst", "-sha256", "-sign", key, tmp.name)

    signer = lp(signed_data) + lp(lp(struct.pack("<I", RSA_SHA256) + lp(signature))) + lp(public_der)
    value = lp(lp(signer))
    pair = struct.pack("<QI", len(value) + 4, V2_ID) + value
    size = len(pair) + 8 + len(MAGIC)
    block = struct.pack("<Q", size) + pair + struct.pack("<Q", size) + MAGIC
    eocd = bytearray(apk[eocd_pos:])
    eocd[16:20] = struct.pack("<I", cd_off + len(block))
    out = apk[:cd_off] + block + apk[cd_off:eocd_pos] + bytes(eocd)

    open(dst, "wb").write(out)
    verify(dst)


def take(buf, pos):
    n = struct.unpack("<I", buf[pos : pos + 4])[0]

    return buf[pos + 4 : pos + 4 + n], pos + 4 + n


def verify(path):
    apk = open(path, "rb").read()
    eocd_pos, cd_off, cd_size = find_eocd(apk)

    if apk[cd_off - 16 : cd_off] != MAGIC:
        sys.exit("apksign verify: no signing block")

    size = struct.unpack("<Q", apk[cd_off - 24 : cd_off - 16])[0]
    block_start = cd_off - size - 8
    pairs = apk[block_start + 8 : cd_off - 24]
    pos = 0
    value = None

    while pos < len(pairs):
        n, kind = struct.unpack("<QI", pairs[pos : pos + 12])

        if kind == V2_ID:
            value = pairs[pos + 12 : pos + 8 + n]

        pos += 8 + n

    if value is None:
        sys.exit("apksign verify: no v2 block")

    signers, _ = take(value, 0)
    signer, _ = take(signers, 0)
    signed_data, p = take(signer, 0)
    signatures, p = take(signer, p)
    public_der, _ = take(signer, p)
    sig_entry, _ = take(signatures, 0)
    algo = struct.unpack("<I", sig_entry[:4])[0]
    signature, _ = take(sig_entry, 4)
    digests, _ = take(signed_data, 0)
    digest_entry, _ = take(digests, 0)
    stored, _ = take(digest_entry, 4)
    actual = content_digest(apk, block_start, cd_off, eocd_pos)

    if algo != RSA_SHA256 or stored != actual:
        sys.exit("apksign verify: digest mismatch")

    with tempfile.TemporaryDirectory() as tmp:
        data = os.path.join(tmp, "data")
        sig = os.path.join(tmp, "sig")
        key = os.path.join(tmp, "key.der")

        open(data, "wb").write(signed_data)
        open(sig, "wb").write(signature)
        open(key, "wb").write(public_der)
        result = subprocess.run(["openssl", "dgst", "-sha256", "-verify", key, "-keyform", "DER", "-signature", sig, data], capture_output=True)

    if result.returncode != 0:
        sys.exit("apksign verify: bad signature")

    print("apksign: v2 signature verified")


if __name__ == "__main__":
    if sys.argv[1] == "verify":
        verify(sys.argv[2])
    else:
        sign(*sys.argv[1:5])
