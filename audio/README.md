# Symz voice lines

Drop recordings here (mp3 or m4a), then put each file name in the matching `voice` field of the `LINES` list in `index.html` (search for `const LINES`).

| Line key   | When it plays                                   | Text |
|------------|-------------------------------------------------|------|
| hero       | Welcome bubble in the hero                      | Hey! I'm Symz. Want the quick tour? |
| heroBack   | Visitor scrolls back up to the hero             | Need anything? Tap me any time. |
| lab        | Exploded View section                           | Big props print in pieces. Hit Explode! |
| divisions  | What Symz makes                                 | Four lanes: prints, merch, gaming, cosplay. |
| p2f        | Photo → Figure                                  | Send a photo, get a figure. |
| shelf      | The Shelf (gallery)                             | Real pieces off my printers. |
| merch      | SYMZ merch                                      | Rep the drip. Tap any piece. |
| process    | Process                                         | Nothing prints till you say yes. |
| meet       | The face on the hoodie                          | That's my logo on the hoodie. |
| faq        | FAQ                                             | Questions? Tap me and ask. |
| order      | Order form                                      | Got an idea? Drop it here. |

Example: `hero:{text:"Hey! I'm Symz. Want the quick tour?", voice:"audio/hero.mp3", …}`

Browsers only play sound after the visitor has interacted with the page, so the very first welcome line may be silent until they click or tap. There's a Sound on/off toggle in Symz's chat panel.
