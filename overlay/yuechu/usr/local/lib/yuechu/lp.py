"""Read logical partition extents from an Android super partition (LP v10)."""
import struct


def extents(dev, name):
    """Return [(offset_bytes, size_bytes), ...] of logical partition `name`."""
    with open(dev, "rb") as f:
        f.seek(4096)
        geometry = f.read(4096)
        magic, = struct.unpack_from("<I", geometry, 0)
        if magic != 0x616C4467:
            raise ValueError("no LP geometry on %s" % dev)
        meta_max, = struct.unpack_from("<I", geometry, 40)
        f.seek(4096 + 4096 * 2)              # primary metadata, slot 0
        h = f.read(meta_max)
    magic, _major, _minor, header_size = struct.unpack_from("<IHHI", h, 0)
    if magic != 0x414C5030:
        raise ValueError("no LP metadata header on %s" % dev)

    def table(off):
        return struct.unpack_from("<III", h, off)     # offset, count, entry size

    parts, exts = table(80), table(92)
    all_exts = []
    for i in range(exts[1]):
        o = header_size + exts[0] + i * exts[2]
        sectors, target_type, target_data, _source = struct.unpack_from("<QIQI", h, o)
        all_exts.append((target_type, target_data * 512, sectors * 512))
    for i in range(parts[1]):
        o = header_size + parts[0] + i * parts[2]
        if h[o:o + 36].rstrip(b"\0").decode() != name:
            continue
        _attr, first, num, _group = struct.unpack_from("<IIII", h, o + 36)
        chosen = all_exts[first:first + num]
        if any(t != 0 for t, _, _ in chosen):
            raise ValueError("%s has non-linear extents" % name)
        return [(off, size) for _, off, size in chosen]
    raise KeyError(name)
