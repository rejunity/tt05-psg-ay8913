![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg)

# AY-3-8913 PSG in Verilog for Tiny Tapeout 5 (WIP)

Info
* https://en.wikipedia.org/wiki/General_Instrument_AY-3-8910
* https://www.vgmpf.com/Wiki/index.php/AY-3-8910
* https://github.com/lvd2/ay-3-8910_reverse_engineered/blob/master/pdf/generalinstrument_ay-3-8910.pdf
* https://github.com/simondotm/ym2149f/blob/master/doc/Resources.md
* https://www.polynominal.com/atari-st/atari-st-ym2149f-yamaha.html
* https://www.atari-shrine.co.uk/hardware/articles/Yamaha%20YM2149.html
* http://wiki.intellivision.us/index.php?title=PSG
* https://www.atarimagazines.com/v4n7/stsound.html
* http://clarets.org/steve/projects/2021_ym2149_sync_square.html

Compatible chips:
* YMZ294, YMZ284, YMZ285
* AY-3-8910, AY-3-8912, AY-3-8930
* YM2149
* YM3439
* T7766A
* WF19054, JFC 95101 and KC89C72
* https://maidavale.org/blog/ay-ym-differences/

Computers that used AY-3-819x / YM2149
* Atari ST, Intellivsion, Amstrad CPC, Oric-1, Colour Genie, MSX, ZX Spectrum 128

Reverse Engineering and chip decap images
* https://github.com/lvd2/ay-3-8910_reverse_engineered
* http://privatfrickler.de/blick-auf-den-chip-soundchip-general-instruments-ay-3-8910/
* https://siliconpr0n.org/map/gi/ay-3-8910/
* https://siliconpr0n.org/map/gi/ay-3-8914
* AY-3-8910 die size: 4.16 mm x 3.80 mm

Implementations
* https://github.com/jotego/jt49 (Verilog)
* https://github.com/dnotq/ym2149_audio/ (VHDL)
* https://opencores.org/projects/sqmusic
* https://github.com/mamedev/mame/blob/master/src/devices/sound/ay8910.cpp
* https://github.com/arnaud-carre/sndh-player/blob/main/AtariAudio/ym2149c.cpp
* https://github.com/mengstr/Discrete-AY-3-8910 - using only discreet 74-series logic ICs!

Music playback!
* http://antarctica.no/stuff/atari/YM2/Misc.Games/ Music from several Atari ST games in YM format
* https://www.cpc-power.com/index.php?page=database Music from many Amstract CPC games in YM format
* https://vgmrips.net/packs/system/atari/st Music from AtariST games in VGM format
* https://vgmrips.net/packs/system/sinclair/zx-spectrum-128 Music from ZX Spectrum 128 games in VGM format
* https://vgmrips.net/packs/system/ascii/msx Music from MSX games in VGM format


## What is Tiny Tapeout?

TinyTapeout is an educational project that aims to make it easier and cheaper than ever to get your digital designs manufactured on a real chip.

To learn more and get started, visit https://tinytapeout.com.

### Verilog Projects

Edit the [info.yaml](info.yaml) and uncomment the `source_files` and `top_module` properties, and change the value of `language` to "Verilog". Add your Verilog files to the `src` folder, and list them in the `source_files` property.

The GitHub action will automatically build the ASIC files using [OpenLane](https://www.zerotoasiccourse.com/terminology/openlane/).

### How to enable the GitHub actions to build the ASIC files

Please see the instructions for:

- [Enabling GitHub Actions](https://tinytapeout.com/faq/#when-i-commit-my-change-the-gds-action-isnt-running)
- [Enabling GitHub Pages](https://tinytapeout.com/faq/#my-github-action-is-failing-on-the-pages-part)

### Resources

- [FAQ](https://tinytapeout.com/faq/)
- [Digital design lessons](https://tinytapeout.com/digital_design/)
- [Learn how semiconductors work](https://tinytapeout.com/siliwiz/)
- [Join the community](https://discord.gg/rPK2nSjxy8)

### What next?

- Submit your design to the next shuttle [on the website](https://tinytapeout.com/#submit-your-design). The closing date is **November 4th**.
- Edit this [README](README.md) and explain your design, how it works, and how to test it.
- Share your GDS on your social network of choice, tagging it #tinytapeout and linking Matt's profile:
  - LinkedIn [#tinytapeout](https://www.linkedin.com/search/results/content/?keywords=%23tinytapeout) [matt-venn](https://www.linkedin.com/in/matt-venn/)
  - Mastodon [#tinytapeout](https://chaos.social/tags/tinytapeout) [@matthewvenn](https://chaos.social/@matthewvenn)
  - Twitter [#tinytapeout](https://twitter.com/hashtag/tinytapeout?src=hashtag_click) [@matthewvenn](https://twitter.com/matthewvenn)
