Star Fighter 3000 3.21 (Fednet Software, 1994; Chris Bazley, 2020) - static recompilation
==========================================================================================

A recipe: this repository holds no game data. It rebuilds the game from
your own copies, recognised by content (recipe.json):

    ./build.sh 'Star Fighter 3000 3.21 (2020)(Fednet + Chris Bazley).zip' uniboot.zip system.zip
    cd recomp && ./sf3000

The game is release 3.21, Chris Bazley's 32-bit-clean desktop version (C
and assembler, a Toolbox application on the Shared C Library), not the
1994 Fednet disc. Its Toolbox modules aren't reimplemented: they run as
they are, from a RISC OS 3.1 !System of your own - Acorn's Universal
!Boot (uniboot.zip: FilterManager, the Toolbox modules, ThreeTen and its
sprites) with a later !System's Toolbox 1.43 and Window 1.54 over it
(system.zip; the Universal !Boot's Window 1.47 is too old for the game's
windows). libroger provides what's beneath them: the Wimp, the Shared C
Library (including modules' LibInitModule), MessageTrans, ResourceFS,
ColourTrans, the Buffer Manager, dynamic areas and the sound system.

build.sh runs recipe.json's steps with SuperSpider's tools/weave.py
(~/stuff/superspider, or $SUPERSPIDER): it extracts the three zips,
merging the two !Systems by RISC OS name (later wins), to game/
(libroger's appdir), then `make regen` (tools/images.py: unsqueezes
!RunImage and the squeezed modules with the game's own unsqueeze code,
analyses and translates each) and `make`. Needs python3, OCaml/dune, gcc
and SDL3.

    tools/unpack.py     AIF and module unsqueezing, run under SuperSpider's ARM emulator
    tools/images.py     the images (!RunImage, !Run's modules in its order, at fixed
                        RMA addresses) through unpack, analyse, roots and gen
    analysis/*.roots    entry points the analysis missed (make roots, from --trace-gaps runs)
    recomp/game.c       the roger_config and the stand-in for the user

Running
-------

    cd recomp && ./sf3000 [--desktop] [--no-sound] [--scale=N] [--fullscreen]
    ./sf3000              the game full screen (game.c clicks the icon bar icon and
                          chooses Full screen from the game window's menu)
    ./sf3000 --desktop    libroger's desktop: the icon bar icon starts it in a window,
                          as on RISC OS; Menu on the window has Full screen, Suspend, Scale...
    ./sf3000 --trace-gaps interpret untranslated code instead of stopping, logging it
    ./sf3000 --limit=N    headless, deterministic: Space, Space, Return, Return - the
                          main menu, mission select and the first mission's map (N=1.6e8)

The runtime's own keys are Ctrl+F10 (shaders), Ctrl+F11 (fullscreen) and
Ctrl+F12 (screenshot): the game uses F1-F12 itself.

Keys (the manual, !Star3000.Resources.UK.Manual): menus - cursor keys,
Return; the title and attract flight - Space. Flight - Z/X roll, ' and /
dive and climb, Right Alt thrust, Return fire; F1-F4 weapons, F5/F6 and
F9-F11 cameras, S status, M map, P pause, Escape back to the main menu,
F12 back to the desktop (without --desktop there's none to go back to,
and the run ends). The mouse works the map and shop screens: PLAY GAME
on the map starts the mission (the manual's mouse flying controls are
untested here).

Headless scripts (--script) give positions in OS units: full screen is a
320x480 mode with eigen factors 2 (1280x1920 units), so PLAY GAME is at
1152,416; on the desktop the window's map has it at 1150,224, after a
`move` into the window. The game reads its mouse once a frame, and a
headless frame is about half an emulated second (libroger's fixed 2
MIPS), so presses must be held for a while and come once the briefing has
been typed out ("Awaiting command").

What runs
---------

All of it, as far as played: the title, the attract flight, the menus,
mission select, the ship shop, the map and its briefing, flying missions
(full screen and in the window), music and effects (SFX_Handler's voice
generator through libroger's sound system), the window's menu (Full
screen), the Choices dialogue box (Adjust on the icon bar icon: all seven
panes, with the key names from Keyboards.1). Not tried yet: the in-game
Configure screens, the window's other menu entries and dialogue boxes,
later missions. The game generates its plotters at run time in its heap
and SFX_Handler copies code into the RMA: those ranges are interpreted
(game.c).

Not supported
-------------

- Joystick_Read isn't there (the game carries on without a joystick).
- The game's own error path (OS_PrettyPrint, OS_Confirm, _kernel_unwind)
  isn't provided: an error it reports that way stops the run.
- The desktop is libroger's: there's no Task Manager or other tasks.
