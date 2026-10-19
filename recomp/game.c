/* Star Fighter 3000 release 3.21 (Fednet Software, 1994; Chris Bazley,
 * 2020): what libroger needs to know about the game.
 *
 * !Run: Obey !Boot (Set Star3000$Dir <Obey$Dir>; IconSprites; Run
 * Resources.ResFind Star3000, a BASIC program setting Star3000Res$Path to
 * the territory's resources, Resources.UK; Obey Star3000Res:SysVars);
 * RMEnsure the FilterManager and the Toolbox modules, RMLoading them from
 * System:Modules; RMLoad Code.FDComp and Code.SFX_Handle; set
 * Star3000Choices$Path and Star3000Levels$Path; WimpSlot 1444K; Run
 * !RunImage. The program is C and assembler on the Shared C Library (which
 * libroger provides), a Toolbox application: the Toolbox modules run as
 * they are, from the user's !System (../recipe.json). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <roger.h>

extern const struct roger_image recomp_image;      /* gen/runimage/entries.c */
#include "gen/modules.inc"                         /* !Run's modules, in its order */

static const char *const prefixes[] = {"<Obey$Dir>.", NULL};
static const char *const variables[] = {
    "Star3000$Dir", "!Star3000", "System$Path", "!System.310.,!System.",
    "Wimp$ScrapDir", "Scrap",            /* (as !Scrap sets it: written to the save directory) */
    "Star3000Res$Dir", "!Star3000.Resources.UK", "Star3000Res$Path", "<Star3000Res$Dir>.",
    "Star3000Choices$Path", "<Star3000$Dir>.Choices.,<Star3000$Dir>.Defaults.",
    "Star3000Levels$Path", "<Star3000$Dir>.LandScapes.",
    "Star3000$Help", "<Star3000Res$Dir>.Manual.index/html",
    /* Resources.UK.SysVars */
    "Star3000$Version", "3.20", "Star3000$Web", "http://starfighter.acornarcade.com",
    "Star3000$Title", "Star Fighter 3000", "Star3000$Publisher", "Fednet Software",
    "Star3000$Description", "Futuristic aerial combat game",
    NULL,
};

static void game_init(void)
{
    /* the Wimp's sprites the Toolbox gadgets use (radio and option buttons,
     * adjuster arrows): on RISC OS 3.1 they're !System's, as ThreeTen
     * loads them (icons22 is for square-pixel modes; mode 15's aren't) */
    roger_cli("IconSprites System:Modules.310Support.icons");
    roger_cli("IconSprites <Star3000$Dir>.!Sprites");
}

/* Without the desktop (--desktop), game.c stands in for the user when
 * Wimp_Poll has nothing to return: Select on the icon bar icon (which
 * opens the game window), Menu on that window, then its menu's first item,
 * Full screen - the game takes over the screen until F12. Back at the
 * desktop, which isn't there to show, Message_Quit. */
static void wimp_idle(void)
{
    static int step;
    int32_t w = roger_wimp_top_window();
    switch (step) {
    case 0: roger_wimp_click(-2, 0, 4); step++; break;
    case 1: if (w) { roger_wimp_click(w, -1, 2); step++; } break;
    case 2: roger_wimp_menu((const int[]){0, -1}); step++; break;
    default: roger_wimp_quit(); break;
    }
}

/* Code made at run time: the game assembles its plotters into buffers in
 * its zero-initialised data and heap (above the image's RO and RW, which
 * end at &4F018), and SFX_Handler copies its interrupt routines into RMA
 * blocks it claims, above the modules' slots (../tools/images.py) */
static const uint32_t interpreted[] = {0x0004F018, 0x01000000, 0x01930000, 0x01E00000, 0, 0};

/* Headless runs (--limit): Space on the title (to the attract flight,
 * with the menu over it from about 31s, "Press Start"), Space (the main
 * menu), Return (Start Game: mission select), Return held after the
 * mission select's animation (the mission's map, its briefing typed out;
 * PLAY GAME there needs the mouse: see README.md). Times in emulated ms,
 * 20000 instructions a centisecond; a frame takes about half a second
 * here, so keys are held for several. */
#define MS(t) ((uint64_t)(t) * 2000)
static const struct roger_key keys[] = {
    {99, MS(15000), MS(15300)},         /* Space */
    {99, MS(35000), MS(35600)},         /* Space */
    {74, MS(40000), MS(40600)},         /* Return */
    {74, MS(65000), MS(67000)},         /* Return */
};

static struct roger_config config = {
    .title = "Star Fighter 3000 (recompiled)",
    .image_path = "../unpacked/RunImage",
    .image = &recomp_image,
    .modules = modules,
    .appdir = "../game",
    .dir_prefixes = prefixes,
    .variables = variables,
    .command_line = "!Star3000.!RunImage",
    .initial_mode = 15,                 /* a 256-colour desktop mode */
    .wimpslot = 1444 * 1024,
    .screen_size = 320 * 1024,          /* the 256-colour desktop and the game's two screen banks */
    .vidc20 = 1,
    .ctrl_meta_keys = 1,                /* the game uses F10-F12 (views; F12 the desktop) */
    .wimp_version = 398,                /* !Run: RMEnsure WindowManager 3.80 (RISC OS 3.1 loads 3.98) */
    .init = game_init,
    .wimp_idle = wimp_idle,
    .interpreted = interpreted,
    .keys = keys,
    .nkeys = sizeof keys / sizeof keys[0],
};

int main(int argc, char **argv) { roger_main(argc, argv, &config); }
