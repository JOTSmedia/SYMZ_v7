# Changelog

## v7
- Nav shows where you are: the link for the section on screen lights up with a red underline (in the phone menu, it turns red), and "Start an order" gets a ring on the order form. This works for normal scrolling and during the autoscroll tour.
- Photo → Figure only starts once the visitor is actually there, meaning the animation is in view and the page has stopped moving, so the whole sequence is seen from the photo onward. It restarts each time you come back. The autoscroll tour now stays on this section until one full run has played (Symz's thought fades once read), then moves on.
- Link previews (iMessage and everywhere else) now use the SYMZ 3D CUSTOMZ badge with Symz: `img/og-symz.jpg`, 1200×1200.

## v6
- Exploded View: everything is in one console that fits the screen, so no scrolling is needed. The Sword / Name plaque / Controller dock picker is on top, the render is in the middle, and the Explode button, Built-to-Apart slider and readout are along the bottom. On phones: the headline, then the console sized to the rest of the screen, then the intro; the controls leave room for Symz in the corner.
- Photo → Figure: a new "Adjust for print" step between the scan and the print. The scan wireframe reshapes from the customer's pose into the figure's (the horn swings up), then fills in as a solid print-ready model inside a print-volume box. That wireframe stays faintly visible above the print line while it prints.

## v5
- Merch: the item pictures moved to a 2-column scrolling list beside the map on desktop, and one swipeable row under the map on phones. The map and the list follow each other: hover (or tap) a piece on the map and the list scrolls to it; hover a picture, or swipe it to the middle of the row on phones, and it's outlined on the map. On phones, the first tap on the map picks a piece and the second opens it.
- Speed: first load is about a third lighter (about 3.1 MB down to 2.0 MB), and a full scroll is about 40% lighter (about 7 MB down to 4.4 MB).
  - Light WebP versions of the gallery photos are used in the grids; the full photos still open in the viewer.
  - Symz's art loads as WebP (101 KB instead of a 650 KB PNG), with a tiny face image for the chat header.
  - The unused Pacifico font is gone.
  - The loader's first frame is preloaded, and the CDN connection is opened early.
  - Leftover code is removed, including an old optional-model check that caused a 404.
- Autoscroll waits until the hero is actually on screen before its 4-second idle countdown, so the welcome thought always shows first. It used to start counting during the loading screen.
- Phones: bigger tap areas for the ORDER button, the thought-cloud buttons and ✕, and the footer links. The corner thought cloud is a little smaller and fades sooner once read.
- Checked at desktop (1440×900) and phone (390×844) sizes, section by section: no sideways scrolling, no broken images, no script errors.

## v4
- Photorealism pass: the loading screen and the Exploded View are now rendered in Blender (Cycles) and shipped as image sequences.
  - Loading screen: photoreal printer (V-slot frame, PEI bed, brass nozzle, red shroud, PTFE tube). The SYMZ CUSTOMZ logo is bigger, hovers halfway between the bed and the top of the frame (no stand), and prints in step with load progress.
  - Symz stays the 3D figure with the full-definition avatar art on both sides (a Blender-built version was tried and dropped in favour of this one).
  - Exploded View: the sword, name plaque and controller dock rebuilt part by part in Blender and rendered at 9 explode steps, plus a print-in from the build plate. Drag across the picture to pull it apart.
- Merch section (new, in the nav): the merch lineup photo (the map) with all 32 items clickable. Hovering an item outlines its shape in white, and hotspot dots show names. Under the map are the individual item pictures with category filters, plus an item viewer with "Order this" (adds a Merch line to the order form) and "Find in lineup".
- Photo → Figure: animated. Photo, background removed, laser 3D scan into a mesh, grey 3D model, layer-by-layer print, then the finished painted figure.
- Thought clouds: smaller. Corner thoughts are placed where they cover the least page content. The cloud lets clicks through (except its own buttons), and corner thoughts fade once read. The hero cloud stays inside Symz's column.
- Mobile ☰ menu, so every section, including Merch, is reachable from the nav on phones.
- Images reserve their space while loading, so jumping to a section lands in the right place.

## v3
- Autoscroll tour stops only when a new section's top reaches the top of the screen; Symz's thought shows at each stop for long enough to read.
- Phone hero: Symz centred between the headline and the intro, thought cloud to his right.
- Link previews: share image (logo + Symz) with Open Graph and Twitter card tags, plus a home-screen icon.

## v2
- Loading screen with a 3D printer printing the logo in step with load progress; every refresh starts at the loader.
- Photoreal two-sided Symz; thought cloud with ✕; corner assistant; autoscroll at 33% speed; Exploded View section; shorter nav that stays on top.

## v1
- First build: hero, divisions, photo → figure, gallery, process, FAQ, order form, Symz guide and assistant, all-caps / small-caps type.
