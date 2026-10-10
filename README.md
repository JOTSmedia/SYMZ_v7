# SYMZ CUSTOMZ: website v7

The umbrella site for **Symz Customz**: custom 3D printing (custom and pre-built), event merch (gender reveals, graduations, birthdays, baby announcements), SYMZ merch, gaming accessories and cosplay.

Built by JOTS.MEDIA. See `CHANGELOG.md` for what changed in each version.

## What's on the page

- **Loading screen:** a photoreal 3D printer, rendered in Blender (Cycles), prints the SYMZ CUSTOMZ logo in step with the real load progress, with a percentage. The logo hovers halfway between the bed and the top of the frame. Every refresh starts here, then the hero.
- **Hero + Symz:** headline on the left. On the right, Symz as a 3D figure with the full-definition avatar art on both sides (the same image front and back), standing on a SYMZ hex base, spinning, with a see-through thought cloud.
  - Closing the thought (✕), tapping anywhere else, or scrolling sends him to the bottom-right corner. There he acts as the site assistant: a short thought at each section, and tapping him opens the chat.
  - He flies back up to his hero spot any time you scroll back up into the hero.
  - Phones: headline, then Symz (thought to his right), then the intro and buttons.
- **Thought clouds:** small and see-through. In the corner, each thought is placed in whichever spot around Symz covers the least page content. Clicks go through the cloud (only its buttons take them), and corner thoughts fade once they have been read.
- **Autoscroll tour:** after about 4 seconds without input, the page drifts down at 33% speed and stops at each new section for Symz's thought. Any wheel, touch, click or key stops it.
- **Exploded View:** photoreal Blender renders of a sword, a name plaque and a controller dock, in one console sized to fit the screen: model picker on top, the render in the middle, and the Explode button, slider and readout along the bottom. Each model prints itself up from the build plate, then pulls apart into its labelled printed parts. You can also drag across the picture.
- **What Symz makes**
- **Photo → Figure:** an animation using the real job. The customer's photo loses its background and gets 3D scanned into a wireframe. The wireframe then adjusts into the print version (pose and proportions) and becomes a solid print-ready model, which prints layer by layer into the finished painted figure.
- **The Shelf:** a filterable gallery with a full-screen viewer.
- **Merch:** the SYMZ merch lineup photo (the map) with all 32 items clickable; hovering an item outlines it in white. On desktop the item pictures sit in a 2-column scrolling list to the right of the map: hovering a piece on the map scrolls the list to it, and hovering a picture outlines it on the map. On phones the pictures run in one swipeable row under the map: tapping a piece on the map scrolls the row to it (tap again to open), and the picture in the middle of the row lights up on the map. Every item opens a viewer whose "Order this" button fills in the order form.
- **Process**, **FAQ**, **order form** and footer.
- Type is all caps / small caps throughout. The nav stays on top. Phones get a ☰ menu.

## Files

```
index.html          the whole site (HTML, CSS, JS in one file)
img/                gallery photos (full size, for the viewer), logo, avatar art, share image
img/t/              light WebP versions of the gallery photos used in the grids
img/merch/          merch lineup photo, item close-ups, t/ = grid thumbnails
img/p2f/            Photo → Figure animation layers (cut-out, scan mesh, grey model, printed figure)
assets/loader/      loading-screen printer frames (Blender renders)
assets/symz-textures.js  Symz figure art, inlined so the figure works offline (avatar-*.webp = same art as files)
assets/lab/         Exploded View frames per model + bare build plate (Blender renders)
audio/              drop Symz voice recordings here (see audio/README.md)
tools/              the scripts that make all of the above (see "Re-rendering")
.nojekyll           tells GitHub Pages to serve files as-is
```

No build step. The loader and Exploded View are pre-rendered in Blender; Symz is drawn live with three.js r128 (from a CDN, like Google Fonts).

## Preview locally

Serve the folder (double-clicking `index.html` also works in most browsers):

```
python3 -m http.server 8000
# open http://localhost:8000
```

## Put it on GitHub Pages

1. Create a new repository (for example `symz-customz`) on GitHub.
2. Upload the **contents** of this folder to the repository root (drag-and-drop in the GitHub web UI works; include `.nojekyll`), or:
   ```
   git init && git add . && git commit -m "SYMZ v4"
   git branch -M main
   git remote add origin https://github.com/<you>/symz-customz.git
   git push -u origin main
   ```
3. In the repo: **Settings → Pages → Build and deployment → Deploy from a branch → `main` / root**.
4. The site goes live at `https://<you>.github.io/symz-customz/`. To use `symzcustomz84.com`, add it under Settings → Pages → Custom domain and point the domain's DNS at GitHub Pages.

Updating from an earlier version: replace everything in the repo with the contents of this folder. Files from older versions that aren't in this folder (`img/symz3d/`, `img/avatar.png`, `models/`, `assets/avatar-back.webp`, `assets/logo-*.png`, `tools/build_textures.py`) are no longer used and can be deleted.

## Link previews

Sharing the link (iMessage, Facebook, X, WhatsApp, Slack) shows `img/og-symz.jpg`: the SYMZ 3D CUSTOMZ badge with Symz (1200×1200, under 300 KB so every app accepts it). The preview tags point at `https://symzcustomz84.com/`. If the site lives somewhere else, replace that address in the `og:url`, `og:image`, `og:image:secure_url` and `twitter:image` tags near the top of `index.html`. Link previews only work once the site is live at that address. Apps cache previews, so a link that was already shared before may keep its old picture for a while; Facebook's Sharing Debugger can refresh it.

## Editing

| What | Where in `index.html` |
|---|---|
| Gallery photos, titles, categories | `const WORK=[` (add the image to `img/`) |
| Merch items (names, blurbs, categories, hotspot positions) | `const MERCH=[`; outlines in `const MSHAPE=` |
| Symz's thoughts and buttons | `const LINES={` |
| Assistant quick answers | `const A={` and `const QUICK=` |
| Thought-cloud placement | `function placeDocked` and `function placeUI` |
| Autoscroll speed and wait | `AUTO_SPEED` (0.33 = 33%) and `AUTO_IDLE` (ms) |
| Brand colors and fonts | `:root{` at the top of the `<style>` |
| Photo → Figure timing and captions | `const PH=[` in the PHOTO → FIGURE script |

## Re-rendering (Blender)

All renders come from scripts in `tools/`. They use Blender as a Python module (`pip install bpy`, Blender 4.2+/5.x) and Cycles on the CPU.

| Output | Script | Notes |
|---|---|---|
| `assets/loader/p00..p12` | `tools/blender/loader_printer.py` | `PROGRESS` = print amount per frame, `NX` = nozzle position; the logo outline comes from `trace_logo.py` |
| `assets/lab/<model>-NN`, `-plate` | `tools/blender/lab_models.py` | `MODEL=blade|plaque|dock`, 9 explode steps; also writes the tag positions that go into `const LAB=` |
| `img/p2f/*` | `tools/build_p2f.py` | from background-removed cut-outs of the two photos (rembg) |
| adjust-for-print wireframe (`D.m` in the page) | `tools/build_p2f_morph.py` | start points in the scanned person, end points on the figure |
| merch outlines | `tools/merch_segment.py` | SAM (vit-b) masks per item, then traced into `MSHAPE` |

Render PNGs are converted to WebP (quality ~80) before going into the site.

## Before launch

- **Order form:** it currently builds the request text for the visitor to copy into an Instagram DM. To receive submissions directly, connect a form service (Formspree, Netlify Forms, Basin) and post the form there.
- **Merch:** no prices are shown; every merch order goes through the order form. Add prices to the item viewer if the client wants them.
- **Copy:** a few lines are drafts to confirm with the client (shop story, FAQ answers, turnaround wording).
- **Instagram:** links point to `@symzcustomz84`.
