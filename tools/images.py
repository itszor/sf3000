#!/usr/bin/env python3
"""The translated images of Star Fighter 3000 3.21 and the steps that build them.

    images.py unpack    the squeezed images -> unpacked/: !RunImage (an
                        Acorn-squeezed AIF image) and the Toolbox's Window
                        module (a squeezed module), with tools/unpack.py
    images.py analyse   SuperSpider (superspider analyse --full) on every image:
                        analysis/<name>.json; analysis/<name>.roots, if there,
                        adds entry points
    images.py roots LOG...
                        merges the gap entries of --trace-gaps runs (libroger's
                        untranslated.log) into analysis/<name>.roots
    images.py gen       superspider gen for every image -> recomp/gen/<name>/,
                        plus recomp/gen/modules.inc (game.c's module list)

Images (game/: !Star3000 from the game's zip, !System from the Universal
!Boot's; see ../recipe.json):
  runimage   !Star3000.!RunImage, unsqueezed: the game, an AIF image (C and
             assembler, on the Shared C Library) at &8000.
  the modules !Run loads, in its order: the FilterManager and the Toolbox
             modules from !System (C, on the Shared C Library), the game's
             FDComp (decompression) and SFX_Handler (sound and music).
Modules are translated at fixed RMA addresses, a 64K slot each from &1840000
(below that, libroger's OS_Module claims).
Not translated: the Shared C Library (libroger provides it, on the host's),
Resources.ResFind (BASIC: game.c sets the variables it would).
"""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
GAME = os.path.join(TOP, 'game')
UNPACKED = os.path.join(TOP, 'unpacked')
SS = os.environ.get('SUPERSPIDER', os.path.expanduser('~/stuff/superspider'))
SSBIN = os.path.join(SS, '_build/default/bin/main.exe')

SYSMOD = '!System/310/Modules/'
RUNIMAGE = '!Star3000/!RunImage'
# (name, file: in game/, or unpacked/ for the unsqueezed ones). The last
# ones are loaded when another asks for them (*RMEnsure ... RMLoad): the
# Toolbox needs DragAnObject and, on RISC OS 3.1, ThreeTen (which needs
# DragASprite and BorderUtils)
MODULES = [('filtermgr', SYSMOD + 'FilterMgr'),
           ('toolbox', SYSMOD + 'Toolbox/Toolbox'),
           ('window', 'unpacked/Window'),
           ('menu', SYSMOD + 'Toolbox/Menu'),
           ('iconbar', SYSMOD + 'Toolbox/IconBar'),
           ('proginfo', SYSMOD + 'Toolbox/ProgInfo'),
           ('saveas', SYSMOD + 'Toolbox/SaveAs'),
           ('scale', SYSMOD + 'Toolbox/Scale'),
           ('dcs', SYSMOD + 'Toolbox/DCS_Quit'),
           ('fdcomp', '!Star3000/Code/FDComp'),
           ('sfx', '!Star3000/Code/SFX_Handle'),
           ('draganobj', SYSMOD + 'DragAnObj'),
           ('threeten', SYSMOD + '310Support/ThreeTen'),
           ('dragasprit', SYSMOD + 'DragASprit'),
           ('borderutil', SYSMOD + 'BorderUtil')]
ON_DEMAND = {'draganobj', 'threeten', 'dragasprit', 'borderutil'}
RMA_SLOTS = 0x1840000


def game_file(rel):
    """a file in game/, whatever its ,load-exec suffix (or unpacked/'s)"""
    if rel.startswith('unpacked/'):
        return os.path.join(TOP, rel)
    p = os.path.join(GAME, rel)
    if os.path.exists(p):
        return p
    m = glob.glob(glob.escape(p) + ',*')
    if len(m) != 1:
        sys.exit('images.py: %s not found in game/ (run the recipe\'s extract step)' % rel)
    return m[0]


def images():
    """(name, path, base, is module)"""
    return [('runimage', 'unpacked/RunImage', 0x8000, False)] + [
        (name, path, RMA_SLOTS + k * 0x10000, True) for k, (name, path) in enumerate(MODULES)]


def run(cmd):
    print('+', ' '.join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def unpack():
    os.makedirs(UNPACKED, exist_ok=True)
    ri = game_file(RUNIMAGE)
    run([sys.executable, '-I', os.path.join(HERE, 'unpack.py'), 'runimage', ri,
         os.path.join(UNPACKED, 'RunImage')])
    run([sys.executable, '-I', os.path.join(HERE, 'unpack.py'), 'module', ri,
         game_file(SYSMOD + 'Toolbox/Window'), os.path.join(UNPACKED, 'Window')])


def analyse():
    subprocess.run(['dune', 'build'], cwd=SS, check=True)
    an = os.path.join(TOP, 'analysis')
    os.makedirs(an, exist_ok=True)
    for name, path, base, module in images():
        cmd = [SSBIN, 'analyse', game_file(path), '%x' % base, '--full',
               '-o', os.path.join(an, name + '.json')]
        rf = os.path.join(an, name + '.roots')
        if os.path.exists(rf):
            cmd += ['--roots', rf]
        if module:
            cmd += ['--module']
        run(cmd)


def roots(logs):
    for name, path, base, _ in images():
        run([sys.executable, os.path.join(SS, 'tools/gap_roots.py'), game_file(path), '%x' % base,
             os.path.join(TOP, 'analysis', name + '.roots')] + logs)


def gen():
    rc = os.path.join(TOP, 'recomp')
    for k, (name, path, base, module) in enumerate(images()):
        extra = [] if not module else ['--prefix', 'M%d' % k, '--tabprefix', 'recomp_' + name,
                                       '--covtag', chr(ord('a') + k)]
        run([SSBIN, 'gen', game_file(path), '%x' % base, os.path.join(TOP, 'analysis', name + '.json'),
             '--c', os.path.join(rc, 'gen', name)] + extra)
    with open(os.path.join(rc, 'gen', 'modules.inc'), 'w') as f:
        f.write('/* generated by ../tools/images.py - the modules, for game.c */\n')
        for name, _, _, module in images():
            if module:
                f.write('extern const struct roger_image recomp_%s_image;\n' % name)
        f.write('static const struct roger_module modules[] = {\n')
        for name, path, _, module in images():
            if module:
                f.write('    {"%s", &recomp_%s_image, %d},\n' % (os.path.relpath(game_file(path), rc), name,
                                                              name in ON_DEMAND))
        f.write('    {NULL, NULL, 0}};\n')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == 'roots':
        roots(sys.argv[2:])
    else:
        for step in sys.argv[1:]:
            {'unpack': unpack, 'analyse': analyse, 'gen': gen}[step]()
