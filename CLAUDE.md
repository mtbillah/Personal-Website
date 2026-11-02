# Frontend Design Engineering Rules (Score 98/100 Pipeline)

Source: the five-plugin pipeline from Sharif Mohammad Nasrullah's reel (pinned comment), adapted to this site.

## 1. Design system grounding (Awesome DESIGN.md)
- Always read `./DESIGN.md` (Apple, from VoltAgent/awesome-design-md) before creating or modifying any UI.
- Strictly use its hex colors, type scale, spacing tokens, radii and the single product shadow. Every value lives as a CSS custom property in `assets/site.css :root`; components reference tokens only.
- Font: `system-ui, -apple-system` first (real SF Pro on Apple devices), then the self-hosted Inter / Inter Display, which is the substitute DESIGN.md names.

## 2. Anti-slop governance (Impeccable + Taste Skill)
- No gradient text or backgrounds. No purple or indigo. No emoji or icon tiles above headings; icons are inline SVG with one stroke weight.
- No eyebrows or kickers above headings. No 01/02/03 numbering. No tiny letter-spaced uppercase labels. No monospace outside code.
- No glass or backdrop blur. No shadows on cards, buttons or text; the one DESIGN.md shadow is reserved for the portrait.
- No icon-card grids or rows of identical cards. Neighbouring sections use different compositions.
- Headlines are two lines or fewer at every width. Every section opens with a heading; the page has a single `h1`.
- Surfaces are separated by tone steps (white ↔ parchment ↔ near-black tiles), not by lines.
- Run `/impeccable audit` and `/impeccable polish` after changes.

## 3. UX & accessibility (Vercel Web Interface Guidelines)
- Hit targets ≥24px, and ≥44px on touch. Never disable zoom.
- Visible `:focus-visible` rings, a skip link, hierarchical headings, `scroll-margin-top` on anchors.
- Honour `prefers-reduced-motion`; animate only `transform` and `opacity`; never use `transition: all`.
- Filter state is deep-linked in the URL. Result counts are announced with `aria-live="polite"`.
- Images have explicit width and height; below-the-fold images lazy-load.

## 4. Closed-loop browser QA (Playwright)
- After any change, render the page in a real browser at 1440, 768 and 390 px, click every control, take screenshots, and fix any overlap or overflow before calling the task done.
