"""Minimal MIPC client for the MT6895 CCCI MIPC ports (/dev/ttyCMIPCn).

Frame: 16-byte header (magic 0x24541984, ps = SIM slot or 0xff, message id,
transaction id, payload length) followed by 8-byte aligned TLVs.  Message ids
were recovered from the stock libmipc.so (mipcIdToString jump tables).
"""
import errno, os, select, struct, time

MAGIC = 0x24541984
SYS_AT_REQ = 0x0003
DATA_ACT_CALL_REQ = 0x0201
INTERNAL_OPEN_REQ = 0x0301
INTERNAL_TEST_REQ = 0x0305
NW_GET_REGISTER_STATE_REQ = 0x0407
NW_GET_RAT_REQ = 0x042b
NW_GET_CS_REQ = 0x042f
SIM_STATUS_REQ = 0x050f
IMS_SET_CONFIG_REQ = 0x0a00
IMS_GET_CONFIG_REQ = 0x0a02


def tlv(kind, val):
    b = struct.pack("<HH", kind, len(val)) + val
    return b + b"\0" * ((-len(b)) % 8)


def u8(v):
    return bytes([v])


def u32(v):
    return struct.pack("<I", v)


def tlvs(p):
    out, i = {}, 0
    while i + 4 <= len(p):
        k, l = struct.unpack_from("<HH", p, i)
        out[k] = p[i + 4:i + 4 + l]
        i += (4 + l + 7) & ~7
    return out


def text(b):
    return b.split(b"\0")[0].decode(errors="replace").strip() if b else ""


def result(r):
    v = r.get(0x0000)
    return struct.unpack("<I", v)[0] if v and len(v) == 4 else None


class Mipc:
    def __init__(self, dev, tries=10):
        for i in range(tries):
            try:
                self.fd = os.open(dev, os.O_RDWR | os.O_NOCTTY)
                break
            except OSError as e:
                if e.errno != errno.EBUSY or i == tries - 1:
                    raise
                time.sleep(0.5)
        self.dev, self.buf, self.tx = dev, b"", 0x200 + (os.getpid() & 0xff) * 0x40
        self.req(INTERNAL_TEST_REQ, 0xff)
        self.req(INTERNAL_OPEN_REQ, 0xff, tlv(0x100, u32(2)) + tlv(0x101, dev.encode() + b"\0") + tlv(0x102, u8(1)))

    def close(self):
        os.close(self.fd)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def _recv(self, timeout):
        end = time.time() + timeout
        while time.time() < end:
            if len(self.buf) >= 16:
                ln = struct.unpack_from("<H", self.buf, 14)[0]
                if len(self.buf) >= 16 + ln:
                    f, self.buf = self.buf[:16 + ln], self.buf[16 + ln:]
                    return struct.unpack_from("<HH", f, 10), f[16:]
            r, _, _ = select.select([self.fd], [], [], 0.2)
            if r:
                self.buf += os.read(self.fd, 65536)
        return None

    def req(self, mid, ps, payload=b"", timeout=5):
        self.tx = (self.tx + 1) & 0xffff
        hdr = struct.pack("<I", MAGIC) + b"\0" * 4 + bytes([ps, 0])
        os.write(self.fd, hdr + struct.pack("<HHH", mid, self.tx, len(payload)) + payload)
        end = time.time() + timeout
        while time.time() < end:
            f = self._recv(end - time.time())
            if not f:
                break
            (fmid, ftx), fp = f
            if fmid == mid + 1 and ftx == self.tx:
                return tlvs(fp)
        return {}

    def at(self, ps, cmd, timeout=8):
        return text(self.req(SYS_AT_REQ, ps, tlv(0x8100, cmd.encode() + b"\0"), timeout).get(0x8100))
