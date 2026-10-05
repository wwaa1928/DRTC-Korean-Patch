# Third-party notices

## Included

- **Galmuri11 BDF and Hangul-only atlas overlay**: https://github.com/quiple/galmuri — SIL Open Font License 1.1. The unmodified notice is in `licenses/Galmuri-OFL.txt`. The overlay derives only from Galmuri glyphs and does not contain the externally downloaded Japanese atlas.
- **pefile and ordlookup**: https://github.com/erocarrera/pefile — MIT. The unmodified notice is in `vendor/pefile-LICENSE.txt`. Public author details in the source and license are retained.
- **Korean PO translations and local build/install tools**: DRTC Korean Patch contributors. English `msgid` values identify the corresponding text in the user's game; ownership of game text remains with the game rights holders.

## Referenced; obtained separately

- **sevenshape dr2c-mod-loader**: https://github.com/sevenshape/dr2c-mod-loader — ISC source license, preserved verbatim in `licenses/sevenshape-ISC.txt`. No compiled loader distribution is included here.
- **HAM V202.0 Japanese Mod distribution**: https://arkwright1.blog.fc2.com/blog-entry-1576.html — the distribution page prohibits redistribution of its package. Obtain it upstream and supply its unmodified loader folder with `--loader-root`. No Japanese game-script translations are included.
- **Frida**: https://frida.re/ and https://github.com/frida/frida — used by the separately obtained loader. Consult the upstream `COPYING` and other component notices. No Frida binary is included here.
- **polib and Pillow**: installed by the user from `requirements.txt`; their source and licenses are available at https://github.com/izimobil/polib and https://github.com/python-pillow/Pillow. They are not vendored here.

Original game files, generated full `.df` files, executable patch utilities, installed-state manifests and personal diagnostic reports are excluded from this repository.
