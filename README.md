# Mir Tuhin Billah · personal website

A static site: plain HTML, CSS and JS, with no build step and no cost.

## Files
- `index.html`: the page
- `assets/site.css`, `assets/site.js`: styles (tokens from DESIGN.md) and behaviour
- `assets/fonts/`: self-hosted Inter (SIL Open Font License)
- `assets/img/`: portrait in three sizes, social preview, favicon
- `DESIGN.md`: the Apple design system (VoltAgent/awesome-design-md), the visual source of truth
- `CLAUDE.md`: the build rules from the five-plugin pipeline
- `PRODUCT.md`: who the site is for and what it must do

## Put it online free with GitHub Pages
1. Create a free GitHub account, then a new **public** repository named `<your-username>.github.io`.
2. Upload everything in this folder: **Add file → Upload files**, drag the contents in, then **Commit**.
3. Go to **Settings → Pages**, choose **Deploy from a branch**, branch `main`, folder `/ (root)`, then **Save**.
4. After about a minute the site is live at `https://<your-username>.github.io`.

Optional: add a custom domain later under **Settings → Pages** (a domain costs about $10–12 a year; the site works without one).

## Updating
Edit the text in `index.html` (each section is labelled with a comment) and re-upload. Talks move from "Coming up" to "Earlier" automatically once their date passes.

## Adding photos later
Put photos in `assets/img/` and ask Claude to place them. The design is built to carry 4 or more real photos (lab, extruder, posters, badminton).
