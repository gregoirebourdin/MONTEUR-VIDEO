# ManySetter promo for the sales page (Charon voice)

| File | Use |
|---|---|
| `manysetter.mp4` | H.264 1080p60, plays everywhere (Safari, iPhone, Android, every browser), starts streaming at once |
| `manysetter.webm` | VP9 1080p60, lighter, served first to Chrome, Firefox and Edge |
| `poster.jpg` | the frame shown before play (end card: logo + tagline) |
| `poster-alt.jpg` | alternative poster ("126 DMs!") |

## Embed

Upload the files next to your page (or to your CDN), then:

```html
<video controls playsinline preload="metadata" poster="poster.jpg" style="width:100%;height:auto;border-radius:16px">
  <source src="manysetter.webm" type="video/webm" />
  <source src="manysetter.mp4" type="video/mp4" />
</video>
```

- The voice carries the pitch, so leave it click-to-play with sound. Browsers only autoplay muted video.
- If your site builder (Framer, Webflow, Systeme.io…) only accepts one file, upload `manysetter.mp4`.
- For YouTube or Vimeo, upload the master `../film_v2/manysetter_v2_1080p60.mp4` instead.
