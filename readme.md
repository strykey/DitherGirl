<div align="center">
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0a0a0a,60:1a1208,100:c8a96e&height=200&section=header&text=Dither%20Girl&fontSize=60&fontColor=c8a96e&fontAlignY=55&animation=fadeIn" width="100%"/>

<br/>

<img src="<img width="459" height="501" alt="logo" src="https://github.com/user-attachments/assets/4af26dae-2bdc-4d40-b603-9d100d5c07b4" />

<br/>

[![Python](https://img.shields.io/badge/Python-3.9+-3572A5?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![pywebview](https://img.shields.io/badge/pywebview-4.x-c8a96e?style=for-the-badge&logo=python&logoColor=111111)](https://pywebview.flowrl.com)
[![NumPy](https://img.shields.io/badge/NumPy-powered-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org)
[![Platform](https://img.shields.io/badge/Platform-Win%20%7C%20Mac%20%7C%20Linux-555555?style=for-the-badge&logo=linux&logoColor=white)](https://github.com/strykey/DitherGirl)
[![License](https://img.shields.io/badge/License-Restrictive-c0392b?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](./LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-27ae60?style=for-the-badge&logo=semanticrelease&logoColor=white)](https://github.com/strykey/DitherGirl/releases)

<br/>

*For people who look at a perfectly good photo and think: "needs more grain and way fewer colors."*

<br/>

[Get Started](#installation) &nbsp;·&nbsp; [How it works](#how-it-works) &nbsp;·&nbsp; [Algorithms](#algorithms) &nbsp;·&nbsp; [Effects Pipeline](#effects-pipeline) &nbsp;·&nbsp; [Palettes](#palettes) &nbsp;·&nbsp; [Export](#export) &nbsp;·&nbsp; [License](#license)

</div>

<br/>

## What is this

Dither Girl is a desktop image dithering tool. You feed it a photo, pick one of 18 algorithms, tweak a handful of sliders, and it comes out the other side looking like it was printed in 1994 on a machine that was very tired. There is no cloud, no account, no subscription trying to upsell you on "Pro Dithering Tier." Every pixel gets processed on your machine, the math runs in NumPy, and the whole thing looks extremely good doing it.

The interface is dark, minimal, and accented in the kind of gold that makes you feel like the app respects your time. The mascot is a little robot with a screen for a torso. Her name is Dither Girl. She has seen things.

<br/>

## Table of Contents

[What is this](#what-is-this) &nbsp;&nbsp; [Features](#features) &nbsp;&nbsp; [Installation](#installation) &nbsp;&nbsp; [How it works](#how-it-works) &nbsp;&nbsp; [Algorithms](#algorithms) &nbsp;&nbsp; [Palettes](#palettes) &nbsp;&nbsp; [Effects Pipeline](#effects-pipeline) &nbsp;&nbsp; [Adjustments](#adjustments) &nbsp;&nbsp; [Export](#export) &nbsp;&nbsp; [Presets](#presets) &nbsp;&nbsp; [Coming Soon](#coming-soon)

<br/>

## Features

**18 dithering algorithms** organized into four families. Floyd-Steinberg is there because it has existed since 1975 and it earned its spot. But so is blue noise, halftone, FM dithering, glitch mode, and a handful of other methods that will make your images look like they escaped from a 90s demo scene ZIP file, in a good way.

**A full pre/post effects pipeline** that runs around the dither pass. Sharpen before to get crispier edges going in. Slap chromatic aberration and grain after to make the output look like it was photographed off a CRT with a disposable camera. Every effect has an intensity slider and you can drag-and-drop the whole chain to reorder it however you want.

**A serious palette system** that ships with built-in palettes, accepts imported JSON palette files, and can extract a palette directly from your loaded image using median cut quantization. You tell it how many colors you want, it reverse-engineers the vibe of your photo and gives you a palette that actually fits it.

**Live preview that actually stays live.** Every slider move triggers a redither. There is a debounce on it so it does not melt your CPU on every pixel of mouse travel, and the backend caches the last result so it only does real work when something actually changed. On slow algorithms it automatically switches to a lower-resolution preview copy so the UI never feels stuck.

**Before/After toggle** in the header so you can flip between the original and the result mid-session without losing your zoom level or pan position. Sounds small. Feels essential.

**Canvas navigation** works exactly how you expect. Scroll to zoom, drag to pan, buttons in the corner if you are a button person. Image renders with `image-rendering: pixelated` so every dither pixel reads crisp at any zoom level.

**Presets** save your entire session state : algorithm, palette, every slider value, every effect with its param and stack order, under a name you choose. Load it back in one click. The app ships with built-in presets too so you can get results immediately without knowing what a Jarvis-Judice-Ninke matrix is.

<br/>

## Installation

```bash
git clone https://github.com/strykey/DitherGirl.git
cd DitherGirl
pip install -r requirements.txt
python main.py
```

This is not a project with a 400-package `node_modules` folder and a webpack config that takes three minutes to understand. It is Python, NumPy, Pillow, and pywebview. The frontend is plain HTML, CSS, and vanilla JavaScript sitting directly in the repo. No build step, nothing to compile, nothing to transpile. You clone, you install, you run.

**Requirements**

```
pywebview >= 4.0
numpy
pillow
scipy        optional : used for better blue noise generation, falls back cleanly without it
```

Python 3.9 or higher. Two commands and a window opens on your screen.

<br/>

## How it works

The architecture is a clean two-part split between a Python backend and an HTML/JS frontend talking to each other through pywebview's JavaScript API bridge.

When you launch the app, `splash.html` runs first. It plays a fake loading animation with realistic-sounding steps like "Importing color engine..." while the real initialization happens behind the scenes. When everything is ready it redirects to `index.html`, where five JavaScript modules boot up and call into Python to fetch palettes, algorithms, effects metadata, and presets all at once.

From that point every image operation follows the same path. The JS frontend calls `API.applyDither(settings)` with a plain JSON object describing the current state of every control. That call crosses the pywebview bridge and lands in `DitherGirlAPI.apply_dither()` on the Python side. The backend does the actual math, encodes the result as a base64 PNG, and returns it. The frontend drops that string directly into an `<img>` tag. No files written to disk, no temp folders, no intermediate nonsense. Just bytes in memory and base64 across the bridge.

The backend is also smart about performance. When you first load an image it pre-computes two downscaled cached copies, one at 800px for fast algorithms and one at 300px for the slower error diffusion ones that scan every pixel individually. Live preview always uses the appropriate cached version. Full resolution only runs when you export. You never wait for a 4000px Floyd-Steinberg pass just because you moved the brightness slider.

<br/>

## Algorithms

<div align="center">

`Floyd-Steinberg` &nbsp; `Atkinson` &nbsp; `Jarvis-Judice-Ninke` &nbsp; `Stucki` &nbsp; `Burkes` &nbsp; `Sierra` &nbsp; `Sierra Two-Row` &nbsp; `Sierra Lite` &nbsp; `Bayer 2×2` &nbsp; `Bayer 4×4` &nbsp; `Bayer 8×8` &nbsp; `Bayer 16×16` &nbsp; `Cluster Dot` &nbsp; `Halftone` &nbsp; `Blue Noise` &nbsp; `Scanlines` &nbsp; `FM` &nbsp; `Glitch`

</div>

**Error Diffusion** is the classic family. These algorithms scan the image pixel by pixel, snap each one to the closest palette color, and distribute the leftover color error to the neighboring pixels using a weighted matrix. The error literally diffuses outward across the image, and from a normal viewing distance your brain blends it back into something that approximates the original. Floyd-Steinberg is the safe pick, balanced, works on everything. Atkinson is the Apple Macintosh original: it only diffuses 75% of the error instead of 100%, which means darker darks and lighter lights and that sharp high-contrast look you recognize from early Mac graphics. JJN and Stucki use wider matrices that spread the error across more neighbors, which produces smoother gradients at the cost of being slower. Burkes and Sierra are the middle ground. Sierra Lite is the fastest of the bunch and still looks great.

**Ordered / Bayer** takes the completely opposite approach. Instead of doing any error tracking at all, it tiles a threshold matrix across the image and uses it to decide which pixels get rounded up vs down. The result is a perfectly regular geometric pattern that looks mechanical and intentional. The Bayer matrices come in four sizes, 2×2 for maximum brutalism, 16×16 for something almost smooth. Cluster Dot produces a halftone newspaper look. Halftone 8×8 uses a circular dot pattern. Blue noise uses an irregular organic threshold map so you get all the crispness of ordered dithering without the visible grid structure.

**Modulation** ditchers work by overlaying a pattern onto a quantized image rather than computing per-pixel error. Scanlines slap a horizontal line pattern over everything and make it look like a CRT monitor at the wrong refresh rate. FM dithering uses a frequency-modulated dot grid where denser dots represent darker areas. Crosshatch draws a grid in the darkest palette color over the result. These are niche but they produce effects you cannot get any other way.

**Special** is the drawer for the stuff that does not fit anywhere else. Random threshold adds noise before quantization and produces a raw, almost TV-static texture. Glitch shifts random rows of the image horizontally before dithering it, producing a digital artifact aesthetic that looks like a corrupted file in the best possible sense.

<br/>

## Palettes

The palette is what actually determines how the output looks. The algorithm decides how the image gets broken down. The palette decides what colors are available to build it back up with.

The app ships with a set of built-in palettes covering the classics, Game Boy greens, CGA, EGA, one-bit black and white, and more. The palette selector shows a live swatch grid so you see the colors before you commit to them.

**Import** lets you bring in any `.json` palette file in the standard format: a `name` field and a `colors` array of hex strings. If you have palettes from Lospec or anywhere else you can drop them straight in.

**Extract** runs median cut quantization on your loaded image and generates a palette directly from its color content. You pick the number of colors (2 to 32) and the algorithm finds the most representative values in the image. Using an extracted palette almost always produces the most coherent-looking result because the colors are already drawn from what is actually in the photo.

<div align="center">

```json
{
  "name": "My Palette",
  "author": "you",
  "colors": ["#0a0a0a", "#c8a96e", "#e8e8e8", "#1c1c1c"]
}
```

</div>

<br/>

## Effects Pipeline

The pipeline wraps around the dither pass and splits into two phases.

**Pre-effects** run on the image before dithering. What happens here shapes what the algorithm receives, so it directly changes the character of the dither output. Sharpen adds edge contrast and makes the dither pattern crunch into hard lines. Blur softens everything and produces rounder, more painterly dithering. These two together give you a lot of control over how fine or coarse the output texture reads.

**Post-effects** run on the dithered image after the palette has been applied. Chromatic aberration shifts the red and blue channels horizontally by a pixel amount you control, the classic lens fringe that makes everything look like a lo-fi VHS rip. JPEG Glitch saves the image to a low-quality JPEG in memory and reads it back, introducing real compression artifacts directly into the dithered result. Grain adds Gaussian noise on top. Vignette darkens the edges. Glow blends a blurred copy of the image back over itself for a soft halo.

<div align="center">

| Effect | Phase | What it does |
|:---|:---:|:---|
| Sharpen | Pre | Adds edge contrast before the dither pass |
| Blur | Pre | Softens input for rounder dither patterns |
| Chromatic Aberration | Post | RGB channel shift, lens fringe effect |
| JPEG Glitch | Post | Real compression artifacts in-memory |
| Grain | Post | Gaussian noise over the dithered result |
| Vignette | Post | Edge darkening, draws focus inward |
| Glow | Post | Blurred overlay, soft halo effect |

</div>

Every effect has a parameter slider. Drag the handle icon on the left of any effect row to reorder the chain. Order matters, especially post-effects grain before vignette looks different from vignette before grain.

The current pipeline is just the foundation. A lot more effects are planned, see [Coming Soon](#coming-soon).

<br/>

## Adjustments

The right panel has six sliders that control the core of the dither pass.

**Depth** controls bit depth posterization. At 8 bits the input image is untouched. Lower values crush the color range before dithering, which produces harder banding and a more aggressive palette-reduced look. Think of it as how much of the original color information survives into the algorithm.

**Threshold** shifts the quantization cutoff globally. Above 128 the image biases toward the lighter palette colors, below 128 it biases toward darker ones. On Bayer and ordered algorithms this shifts the entire threshold matrix up or down, which changes how dense the dither pattern reads in the midtones.

**Brightness and Contrast** are standard image adjustments that run before everything else. They are there so you can optimize the input image for dithering without needing an external editor. Dithering high-contrast images usually produces better results than dithering flat ones.

**Scale** lets you dither at a different resolution than the display size. Values above 1 downsample the image before dithering and scale it back up, making each dither "pixel" physically larger. Values below 1 do the opposite. At ×2 you get chunky visible dither pixels. At ×0.25 the pattern is extremely fine-grained. This is one of the most impactful sliders in the whole app.

**Serpentine** toggles alternating scan direction for error diffusion algorithms. Instead of always scanning left to right, it scans right to left on even rows. This removes the subtle directional bias that regular scanning introduces and produces more balanced diffusion across the whole image.

**Invert** flips every pixel value before processing. Useful for producing negative-space dithering or for palettes where dark and light are swapped.

<br/>

## Export

The export section lives at the bottom of the right panel and runs a full-resolution dither pass when you trigger it, meaning none of the preview shortcuts apply, and the output is computed from the full-size original image.

<div align="center">

| Format | Notes |
|:---|:---|
| PNG | Lossless, recommended for dithered art |
| JPEG | Quality slider appears, use 90+ for clean results |
| BMP | Uncompressed, maximum compatibility |
| WebP | Modern format, good compression with quality control |

</div>

**Export Scale** multiplies the output dimensions before saving. ×1 saves at the dithered resolution. ×2 doubles it using nearest-neighbor scaling so every dither pixel becomes a 2×2 block without introducing any interpolation blur. ×4 does the same at four times the size. Use this when you want large crisp pixel art from a small source image.

<br/>

## Presets

A preset saves the complete state of the app: algorithm, palette, all six sliders, the serpentine and invert toggles, and every effect with its enabled state, param value, and position in the stack. Everything.

The app ships with built-in presets demonstrating different styles so you can see what the algorithms look like on a real image without spending time dialing things in. Your saved presets appear in the same list and can be deleted individually. Built-in presets are permanent.

To save a preset, load an image and configure everything how you want it. The "Save Current" button activates once an image is loaded. Name it, save it, find it in the list. Done.

<br/>

## Coming Soon

This is where Dither Girl is going. Some of this is almost done, some of it is a napkin sketch, all of it is happening.

**3D/2D export for Blender** is the big one. The idea is to export your dithered image as a flat plane mesh with a displacement map baked from the luminance of the result, so you can import it directly into Blender, drop a light above it, and watch the dither pattern cast actual shadows. Every dot becomes a micro-relief. You get physically accurate light bounce across a Floyd-Steinberg pass, which is a sentence nobody has ever said before and honestly that is reason enough to build it. Output will be an OBJ + PNG pair that imports in two clicks.

**Colored glow** because the current glow effect is monochrome and that is a crime. The plan is a per-channel glow with independent color pickers for shadows, midtones, and highlights so you can push a red halo into the darks and a cool blue into the lights simultaneously. This alone would make the effects pipeline twice as interesting.

**Animated dither export** for GIFs and sprite sheets. Feed it a video clip or an image sequence, it dithers every frame with the same settings and exports a looping GIF or a tiled sprite sheet. The obvious use case is pixel art animations but also just making anything look like a broken TV and exporting that as a loop.

**Palette builder** built into the app so you do not have to write JSON by hand. A small editor where you add, remove, reorder, and tweak colors with a picker, then export as a properly formatted palette file. Should have existed from day one.

**Dither masking** with a brush tool. Paint a mask directly on the canvas that tells the algorithm where to apply dithering and where to leave the original untouched. Useful for keeping a face clean while destroying the background, or vice versa.

**Reaction-diffusion texture generator** as a new algorithm family. These are the biological growth patterns spots, stripes, coral shapes that look stunning when used as threshold maps for ordered dithering. Think Turing patterns baked into a Bayer matrix.

**Custom algorithm editor** where you define your own error diffusion matrix by filling in a grid of weights. Build a matrix that has never existed before and see what it does to a photo. Nerd bait, yes. Worth it.

**A lot more effects in the pipeline** because seven is not enough. The list of what is coming includes pixel sorting (sort pixels by luminance or hue along rows or columns, that melting vertical streak effect), color channel swap (reroute R into G, G into B, or any combination, brutal palette destruction in one click), edge detection overlay (run a Sobel or Canny pass on top of the dithered result and draw the detected edges in a chosen palette color), halation (the red bloom around bright areas you get on film, baked as a post effect), color temperature shift (push the whole result warm or cold without touching the palette), stipple bloom (bright areas grow larger dither dots while dark areas shrink, mimics photographic exposure), posterize post (crush the dithered output to even fewer tones after the pass, stacks interestingly with depth posterization before it), and pixel offset/displacement (shift individual pixel rows by a noise map, creates a liquid warping effect on the dithered pattern without the hard glitch look).

<br/>

## License

This software is released under a custom restrictive license. Read [LICENSE](./LICENSE) for the full terms. The short version is: personal use is free and encouraged. You cannot redistribute this, sell it, fork it publicly, or use it in a commercial product without explicit written permission from Strykey. If you want to do any of those things, reach out.

<br/>

<div align="center">

made with love (and a lot of NumPy) by **Strykey**

<br/>

[![GitHub stars](https://img.shields.io/github/stars/strykey/DitherGirl?style=for-the-badge&color=c8a96e&labelColor=1a1a1a)](https://github.com/strykey/DitherGirl/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/strykey/DitherGirl?style=for-the-badge&color=c8a96e&labelColor=1a1a1a)](https://github.com/strykey/DitherGirl/network)

<br/>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:c8a96e,40:1a1208,100:0a0a0a&height=120&section=footer" width="100%"/>


</div>
