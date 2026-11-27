#!/usr/bin/env python3
"""Repack a yuechu v4 boot.img with a new kernel, keeping header and ramdisk.

Usage: yuechu-repack-boot.py OLD_BOOT.img Image.gz OUT.img

The yuechu LK only boots a gzip kernel and rejects a boot partition without an
AVB footer, so finish with:
  avbtool add_hash_footer --image OUT.img --partition_name boot \
      --partition_size 67108864 --algorithm NONE
"""
import struct, sys
old, kern, out = sys.argv[1:4]
PAGE = 4096
b = open(old, "rb").read()
assert b[:8] == b"ANDROID!"
ksz, rsz, osv, hsz = struct.unpack_from("<4I", b, 8)
assert struct.unpack_from("<I", b, 40)[0] == 4
up = lambda n: (n + PAGE - 1) // PAGE * PAGE
r = b[PAGE + up(ksz): PAGE + up(ksz) + rsz]
k = open(kern, "rb").read()
assert k[:2] == b"\x1f\x8b"
hdr = bytearray(b[:hsz])
struct.pack_into("<2I", hdr, 8, len(k), len(r))
pad = lambda x: x + b"\0" * ((-len(x)) % PAGE)
open(out, "wb").write(pad(bytes(hdr)) + pad(k) + pad(r))
print("kernel=%d ramdisk=%d ramdisk_magic=%s" % (len(k), len(r), r[:4].hex()))
