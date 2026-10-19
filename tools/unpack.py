#!/usr/bin/env python3
"""Unsqueeze the squeezed images, with the game's own unsqueeze code.

    unpack.py runimage RUNIMAGE OUT     the game: an Acorn-squeezed AIF image
    unpack.py module RUNIMAGE MODULE OUT
                                        a squeezed relocatable module (the
                                        Toolbox's Window: its initialisation
                                        offset has bit 31 set, and the kernel
                                        unsqueezes it when it is loaded)

Both run in SuperSpider's arm2.py. !RunImage's header branches to the
unsqueeze stub at its end, which expands the image in place and jumps back
to the header (&8004): what is then in memory, RO and RW, is the image.

A squeezed module carries no code of its own to do that. Its data is in
the same form as a squeezed AIF image's, though: the module header up to
its help string as it is, then the encoded data and the decoding tables,
ending with five words - decoded size, encoded size, tables size, and the
number of short and long codes - which are the first five of the six an
AIF's unsqueeze stub reads from just before itself. So the module's data is
laid out as a squeezed image would have it, followed by those words, a
sixth and the stub from !RunImage, and the stub is called from a header of
our own. The stub decodes downwards, ending 4 bytes below where the encoded
data started, and returns &7C below that (to an AIF header's second word);
the sixth word is how many bytes at the start of the encoded data it first
copies out of the way, so that what it writes can't overtake what it has
yet to read (none here: the output is given room instead). The decoded data is the whole module, its
header with the real initialisation offset.
"""
import os
import struct
import sys

SS = os.environ.get('SUPERSPIDER', os.path.expanduser('~/stuff/superspider'))
sys.path.insert(0, os.path.join(SS, 'tools'))
from arm2 import ARM, Stop   # noqa: E402

BASE = 0x8000
LIMIT = 0x800000                                # the RAM limit OS_GetEnv gives the stub
OS_GETENV, OS_SYNCHRONISECODEAREAS = 0x10, 0x6E


def run(data, entry, done):
    """data at BASE, run from entry until control reaches done; the machine"""
    m = ARM()
    end = BASE + len(data)
    m.mem[BASE:end] = data
    m.r[13] = LIMIT
    m.r[15] = entry

    def swi(m, n, pc):
        n &= ~0x20000
        if n == OS_GETENV:
            m.r[0], m.r[1], m.r[2] = 0, LIMIT, 0
        elif n != OS_SYNCHRONISECODEAREAS:
            raise Stop('SWI &%x at &%x' % (n, pc))
    m.swi_handler = swi
    while m.steps < 50_000_000:
        pc = m.r[15] & 0x3FFFFFC
        if pc == done and m.steps:
            return m
        nxt = m.rw(pc + 4)
        m.step()
        if (m.r[15] & 0x3FFFFFC) == pc + 4 and m.rw(pc + 4) != nxt:
            # an instruction stored over after it was fetched runs as it was (see
            # Elite's unpack.py)
            new = m.rw(pc + 4)
            m.ww(pc + 4, nxt)
            m.step()
            if m.rw(pc + 4) == nxt:
                m.ww(pc + 4, new)
    raise Stop('the unsqueeze did not finish')


def stub_of(runimage):
    """!RunImage's unsqueeze stub: the code its header's first word branches to"""
    w0 = struct.unpack_from('<I', runimage, 0)[0]
    assert w0 >> 24 == 0xEB, 'not a squeezed AIF image'
    at = ((w0 & 0xFFFFFF) << 2) + 8
    return runimage[at:]


def unpack_runimage(src, dst):
    data = open(src, 'rb').read()
    stub_of(data)
    m = run(data, BASE, BASE + 4)
    ro, rw = struct.unpack_from('<II', m.mem, BASE + 0x14)
    img = bytes(m.mem[BASE:BASE + ro + rw])
    assert struct.unpack_from('<I', img, 0)[0] == 0xE1A00000, 'header not restored'
    open(dst, 'wb').write(img)
    print('%s: %d bytes (RO &%x, RW &%x)' % (dst, len(img), ro, rw))


def unpack_module(runimage, src, dst):
    stub = stub_of(open(runimage, 'rb').read())
    data = open(src, 'rb').read()
    init = struct.unpack_from('<I', data, 4)[0]
    assert init & 0x80000000 and init & 0x7FFFFFFF == len(data), 'not a squeezed module'
    decoded, encoded, tables, nshorts, nlongs = struct.unpack_from('<5I', data, len(data) - 20)
    body = data[:len(data) - 20]
    start = len(body) - tables - encoded             # where the encoded data starts
    # our header (a branch to the stub, as an AIF's first word), the module
    # bytes from where the encoded data starts, the six words, the stub. The
    # output is put ROOM bytes higher than the stub would put it (the decoded
    # size it is given is that much larger), so it can't overtake the input
    hdr, room = 0x100, 0x10000
    image = bytearray(hdr) + body[start:] + struct.pack(
        '<6I', decoded + room, encoded, tables, nshorts, nlongs, 0) + stub
    stub_at = BASE + hdr + len(body) - start + 24
    out_at = BASE + hdr - 4 + room
    struct.pack_into('<I', image, 0, 0xEB000000 | ((stub_at - BASE - 8) >> 2))
    m = run(bytes(image), BASE, out_at - 0x7C)
    out = bytes(m.mem[out_at:out_at + decoded])
    title = struct.unpack_from('<I', out, 0x10)[0]
    assert out[title:title + 4] == data[0x2C:0x30], 'not the module (title)'
    open(dst, 'wb').write(out)
    print('%s: %d bytes, initialisation at &%x' % (dst, len(out), struct.unpack_from('<I', out, 4)[0]))


if __name__ == '__main__':
    try:
        if len(sys.argv) == 4 and sys.argv[1] == 'runimage':
            unpack_runimage(sys.argv[2], sys.argv[3])
        elif len(sys.argv) == 5 and sys.argv[1] == 'module':
            unpack_module(sys.argv[2], sys.argv[3], sys.argv[4])
        else:
            sys.exit(__doc__)
    except Stop as e:
        sys.exit('unpack: %s' % e)
