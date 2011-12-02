# ocaml_detect_recursion.py - GDB command to help debug OCaml stack overflows
#
# Copyright (C) 2011  Incubaid BVBA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
GDB command to (attempt to) pin down a recursion pattern on stack overflow
'''

import re
import struct

COMMAND = 'ocaml-detect-recursion'
DEFAULT_ARG = '$rsp'

ADDR_SIZE = 8 # 64 bit
ADDR_UNPACK = 'Q' # struct type for addresses
STACK_SAMPLE_LENGTH = 1024

try:
    gdb
except NameError:
    try:
        import gdb
    except ImportError:
        import sys

        sys.stderr.write('Not running inside GDB?\n')
        sys.stderr.flush()

        sys.exit(1)

VOID_P_TYPE = gdb.lookup_type('void').pointer()

def list_ngrams(xs, n):
    '''Generate all n-grams for given n in xs'''

    cnt, _ = divmod(len(xs), n)

    for i in xrange(cnt):
        yield xs[i * n:(i + 1) * n]

def all_equal(xs):
    '''Check whether all values in xs are equal'''

    fst = sentinel = object()

    for x in xs:
        if fst == sentinel:
            fst = x
            continue
        else:
            if x != fst:
                return False

    return True


def find_shortest(xs):
    '''Find the shorted repeated sequence in xs

    This function finds the shortest repeated sequence found in the given
    sequence, as well as the index of the first occurrence, if any.

    If no recurring sequence is found, (-1, None) is returned.

    Example:

        >>> find_shortest([1, 2 ,3, 4, 5, 3, 4, 5, 3, 4, 5, 3, 4])
        (2, [3, 4, 5])
    '''

    if not xs:
        return -1, None

    if len(xs) == 1:
        return 0, (xs[0], )

    xs_ = xs
    idx = 0
    while xs_[0] not in xs_[1:]:
        xs_ = xs_[1:]
        idx += 1

    if not xs_:
        return -1, None

    cnt, _ = divmod(len(xs_), 2)
    for l in xrange(1, cnt):
        ngrams = list_ngrams(xs_, l)
        if all_equal(ngrams):
            return idx, xs_[0:l]

    return -1, None


class DetectOCamlRecursion(gdb.Command):
    '''Attempt to reconstruct a minimal recursion pattern on stack

    Usage: ocaml-detect-recursion [address]

    If no starting address is provided, $rsp is used. The address can be any
    valid GDB expression (e.g. "$rsp + 0x28").
    '''

    def __init__(self):
        super(DetectOCamlRecursion, self).__init__(
            COMMAND, gdb.COMMAND_STACK)

    def invoke(self, arg, _):
        if not arg:
            arg = DEFAULT_ARG

        addr = gdb.parse_and_eval(arg)

        if addr.type != VOID_P_TYPE:
            gdb.write('Invalid argument: not an address\n', gdb.STDERR)
            return

        infs = gdb.inferiors()

        assert len(infs) == 1

        mem = infs[0].read_memory(addr, STACK_SAMPLE_LENGTH)

        procs = []
        funs = {}

        addr = struct.Struct(ADDR_UNPACK)

        for i in xrange(STACK_SAMPLE_LENGTH / ADDR_SIZE):
            p = addr.unpack(mem[i * ADDR_SIZE:(i + 1) * ADDR_SIZE])[0]

            if p not in funs:
                s = gdb.execute('info symbol %d' % p, to_string=True)
                s = s.strip()

                m = re.match(r'(\w*) \+ \d+ in section', s)
                if m:
                    procs.append(p)
                    funs[p] = m.groups()[0]
            else:
                procs.append(p)

        idx, seq = find_shortest(procs)

        if not seq:
            gdb.write('Unable to find recurring call pattern', gdb.STDERR)
            gdb.flush(gdb.STDERR)
            return

        title = 'Recurring call pattern starting at frame %d' % idx
        gdb.write(title)
        gdb.write('\n')
        gdb.write('=' * len(title))
        gdb.write('\n')
        for c in seq:
            gdb.write('%s @ 0x%x\n' % (funs[c], c))
        gdb.flush(gdb.STDOUT)

DetectOCamlRecursion()
