# Generating a Client IMA from the Cobalt Template

## What this repo is

`cobalt-ima-template` is the **template of record** for every client IMA HTML. Every
client-specific slot carries a `[bracketed placeholder]` describing what belongs there, and
both tracks plus all six priority cards are present as structure to delete from. It mirrors
what `COBALT_IMA_TEMPLATE` does on the Word side.

Clone this. Do not clone a client repo — `bfc-ima`, `xsel-labs-ima`, `snorkl-ima`,
`journify_ima`, `paper-ima` and `lando-ima` are delivered deliverables, and starting from one means inheriting their
content and their embedded PDF.

**Read a finished report alongside this one.** Placeholders tell you what goes in a slot;
they cannot show you how long a priority body actually runs, what a good evidence row looks
like, or how the theory-of-change drawers read. Open **`lando-ima`** for that — it is
single-track, four priorities, uses the ToC figure, and carries every current section. Read
it; never clone it. (`xsel-labs-ima` predates the ToC figure; read it for prose only.)

If the chrome needs a fix, fix it **here** and re-push, then propagate to whichever client
files are still live.

---


There is no build step. The markup, JS, and SVG live in `index.html`; all CSS lives alongside
it in `styles.css` (linked from the `<head>`). Keep these two files together — `index.html`
references `styles.css` by relative path, so they must travel as a pair. The fonts load from
Typekit/Google CDNs; everything else is local.

To make a new client report, clone this repo and **fill the content regions** while leaving
the **chrome** untouched. Every region that needs client copy is marked with `[bracketed
text]` telling you what belongs there and roughly how long it should run.

> **Anchors, not line numbers.** This guide deliberately locates things by *search string*
> rather than line number. Line numbers drift the moment anyone edits the file, and stale
> pointers were the main way an earlier version of this guide went wrong.

---

## Files in this repo

| File | Role |
|---|---|
| `index.html` | The report. Markup + JS + SVG. **Canonical template.** |
| `styles.css` | All CSS. Chrome — do not edit per client. |
| *(no PDF file)* | The Doc's PDF is embedded **inside** `index.html` as base64 — not a separate repo file. |
| `evidence.html` | The evidence review appendix page. Shares `styles.css`. |
| `toc_figure.py` | Builds the theory-of-change figure from the client's ToC slide. See region 5. |
| `check_deliverable.py` | Pre-delivery check: stale "Roadmap", unfilled placeholders, prior-client names. |
| `bundle.py` | Inlines CSS into a single portable HTML in `dist/` (for email). |
| `GENERATION.md` | This guide. |
| `.gitignore` | Ignores `dist/`. |

---

## Order of operations (the real workflow)

The HTML is **not** the first artifact, and the downloadable PDF is **not** a render of the
HTML. The sequence is:

1. **Draft the Google Doc version** of the report (the Word/GDoc deliverable).
2. **Clark reviews and edits** the Doc until it is final.
3. **Generate the HTML report** from the finalized Doc's content (this guide).
4. **Export the final Google Doc to PDF**, base64-encode it, and embed it in `index.html`
   as `PDF_B64` (see "The Download PDF button"). This is a scripted step, not a manual one.
5. Update `PDF_NAME` to the filename the client should receive on download.
6. Post to GitHub; share the Word/PDF plus the GitHub Pages link.

Because the HTML and the PDF are two independent renderings of the same report, **build the
HTML only after the Doc is genuinely final.** If the Doc changes later, re-export the PDF and
re-commit it — the HTML will not update itself, and vice versa.

---

## How to generate a new report

1. Get the template with `git clone https://github.com/clark244/cobalt-ima-template.git` — **not** a raw
   URL fetch, which truncates around 80KB and silently loses the `<script>` block. Copy
   `index.html` → `dist/<client>.html` and `styles.css` alongside it (keep the originals as the
   template). The copied HTML still links `styles.css` by relative path.
2. Feed an LLM: (a) the source material for the new client — discovery notes, questionnaire,
   public info; (b) this guide; (c) a finished client report — `lando-ima` — read as an example.
3. Instruct it to rewrite **only** the content regions listed below, preserving the chrome
   and all the coupling rules.
4. Run the **post-generation checklist** at the bottom before sending.

The model is *clone + rewrite-in-place*, not *regenerate from scratch*. The chrome (layout,
CSS, JS logic, SVG geometry) is hard-won and identical for every client — never rebuild it.

### Exporting a portable single file (for email)

The working copy links `styles.css`, so the two files must stay together. To produce **one
self-contained `.html`** (CSS inlined, no local dependencies):

```
python3 bundle.py                      # -> dist/bfc-bundled.html
python3 bundle.py dist/<client>.html   # custom output path
```

`bundle.py` needs only system Python 3. It reads `index.html` + `styles.css`, inlines the CSS
into a `<style>` block, and writes the bundle to `dist/` (gitignored). It never modifies the
source files. Because the PDF is embedded in `index.html` rather than sitting beside it, the
bundled file keeps a working Download PDF button — nothing extra to attach.

---

## Structure of the report

Sections, in document order. **"About This Report" is a modal, not a section** — it opens from
the cover buttons via `openAboutModal()`.

| Section id | Title | Notes |
|---|---|---|
| `#keyfindings` | Key Findings | Full-bleed tinted band, 2×2 card grid. Unnumbered. |
| `#model` | Theory of Change | The client's ToC slide as an interactive figure + print-only description table. |
| `#evidence` | Evidence Landscape | Table with inline source tooltips. |
| `#opportunities` | Measurement Opportunities | Framing prose + dot legend. |
| `#track1` | Track 1 — *(client-specific title)* | Priority accordion. |
| `#track2` | Track 2 — *(client-specific title)* | Priority accordion. |
| `#nextsteps` | Recommended Next Steps | Numbered list. |

**One track vs. two.** The template ships two tracks (`#track1` + `#track2`). Most clients have a
single track. To go single-track: delete the `#track2` section, remove its nav sub-item,
remove its `navMap` entry, and renumber the priorities (e.g. `1a…1d` → `1…4`). Keep one
`.priority-matrix-key` at the top of whichever track sections remain.

---

## Content regions to rewrite (per client)

**Word counts are targets, not hard limits.** They come from the filled file, which is tuned
to the layout's rhythm — cards, matrix cells, and diagram boxes are sized for copy in these
ranges. Land inside the range and the report keeps its density. Run long and cards grow
uneven, prose blows past the `--measure` width, or diagram labels overflow their boxes. When
in doubt, cut toward the low end — this is an executive brief.

| # | Region | Where (search for) | Words (target) | Notes |
|---|--------|--------------------|----------------|-------|
| 1 | Cover + meta | `cover-label`, `cover-client`, `cover-meta-value` | labels only | Client name, doc type, "prepared for" contacts, date. **"Cobalt Collective" is the report author — constant, do not change.** |
| 2 | Key Findings (4 cards) | `class="kf-card"` | title **8–14**, desc **20–28** (≈**100** total desc) | The executive summary. Keep the four descriptions balanced so the cards align. |
| 3 | About modal | `id="about-modal"` | intro **60–90** | Mostly boilerplate; swap client name, source dates, discovery-conversation reference, and the `.about-sources` list. |
| 3b | **About-the-client section** | `id="about-client"` | **60–90** | A short unnumbered section between Key Findings and the model. See "The About-the-client section" below. |
| 4 | Theory of Change intro | `id="model"` intro `<p>` | **55–85** | Copied from the finalized Doc. |
| 5 | **The ToC figure** | `id="model-svg"` + the `nodes` object + the print-only table | `know` = the Doc row verbatim; `gaps` **30–60** | **Built by `toc_figure.py`, never by hand. See "The theory-of-change figure" below.** |
| 6 | Evidence Landscape | `id="evidence-table"` + closing `<p>` | **6 rows**; closing para **80–110** | Rows = the client's existing evidence assets. Keep cell copy terse. |
| 7 | Opportunities framing | `id="opportunities"` intro `<p>`s | **3 paras, ≈200 total** (buyer-reality para **80–90**) | Includes the two-track framing. |
| 8 | Matrix column labels | `priority-matrix-key` | labels only | The four audience/buyer columns. Must match the `.pm-dots` order in every card. |
| 9 | Priority cards | `class="priority-card"` | body **170–230** (intro **90–140** + a 4-item list + one italic note **25–40**) | The detailed payload. The template ships 6 (1a–1d, 2a–2b) as structure to delete from — **the count for a client must fall out of the evidence, not the template.** |
| 9b | **What Changes If You Do This** | `id="whatchanges"` | **90–130** | One paragraph, after the priorities, before Next Steps. See the section below. |
| 10 | Next Steps | `next-steps-list` | **6–7 steps, 25–45 each** | |
| 11 | Nav labels | `<nav>` in `id="sidebar"` | labels only | Must **mirror** the section titles and track titles. |
| 12 | Embedded PDF | `const PDF_B64` + `const PDF_NAME` | scripted | Regenerate from the final Doc. See below. |

---

## The About-the-client section (region 3b)

A short unnumbered section titled "About [Client]", sitting between Key Findings and the
Theory of Change. One paragraph, no subheadings. It carries a section header, a section
rule, a sidebar nav entry and a `navMap` entry like any other section — it is simply much
shorter than the rest.

```html
<section class="section" id="about-client">
  <div class="section-header"><h2 class="section-title">About [Client]</h2></div>
  <div class="section-rule"></div>
  <p class="scope-note">…</p>
</section>
```

It mirrors the Word report, where this is a Heading 1 section in the same position, before
"About This Report". Keep the two in step: About the *client* comes before About the
*report*, because the reader should know what is being assessed before how it was assessed.

**Its job is an accuracy check, not context.** The client reads it in five seconds and
confirms the report describes what they actually built. A founder who has to correct it has
found the error on page one instead of page six, which is the point. Write it so it is easy
to disagree with.

**What it contains:** what the organization offers, who uses it, who buys it, and the
boundary — what this assessment covers and what it treats as out of scope. Acquisitions,
adjacent product lines and discontinued products belong in that last clause when they exist,
because a reader who knows the company will otherwise wonder whether they were missed.

**What it does not contain:**

- **Anything already in the ToC's context band.** Credits, price, duration,
  accreditation, delivery mode, administration time — the band carries those. Restating them
  spends the paragraph's whole budget on nothing. Check the band before writing.
- **Analysis.** It states what the thing is. Key Findings said what we concluded, and the
  model does the causal work. This section makes no claim beyond description and scope.
- **Marketing language.** If it reads like the client's homepage, it is doing their writing
  rather than Cobalt's.

**The test:** could this have been written from the client's website alone? If yes, it is
either mis-scoped, or the discovery conversation never reached what the product actually is —
and the second case is worth knowing before the model is drawn.

---

## "What Changes If You Do This" (region 9b)

An unnumbered section of a single paragraph, placed after the last track of priorities and
before Recommended Next Steps. Structured like any other section — header, rule, nav entry,
`navMap` entry — with no new CSS.

```html
<section class="section" id="whatchanges">
  <div class="section-header"><h2 class="section-title">What Changes If You Do This</h2></div>
  <div class="section-rule"></div>
  <p>…</p>
</section>
```

**What it is.** The payoff: what these priorities, taken together, let this client do that they
cannot do today. It is a synthesis across the whole set, which is the one thing the individual
priority cards structurally cannot say.

**What it is not.** It is not a paragraph about the value of impact measurement. A sentence
that would read the same for every client is marketing, and it belongs in a Cobalt deck, not
in a client's report. If you could paste it into the next IMA by swapping the company name, it
has failed.

**Do not hedge here.** Design cautions, instrument limitations and threats to validity live in
the priority cards, next to the design decisions that address them. Repeating them in this
section makes the payoff hedge its own payoff, which is the fastest way to have a client
discount the whole document. Say what becomes possible; the cards have already said at what
cost.

**Position matters.** After the priorities, not before. Before them, the reader does not yet
know what is being proposed, so any claim about consequences is unanchored. After them, it
reads as the conclusion and hands off cleanly into Next Steps.

### The check this section replaces

An earlier design attached a "what it lets you decide" line to every priority card. That was
dropped because it made the cards long, but it was doing a second job worth keeping: a
priority whose decision line comes out vague is usually a priority that has not earned its
slot. **Apply that test while drafting, card by card, even though it no longer appears in the
document.** For each priority, name the branch the client currently cannot resolve and the
options on either side of it. If you cannot, reconsider whether the priority is real or
whether it is a sub-step promoted to fill out a list. The IMA rule that priority count falls
out of the evidence has no other enforcement mechanism now.

---

## The Download PDF button

The button does **not** print the HTML. It serves the PDF export of the **final Google Doc**,
embedded directly in `index.html` as base64. This is the standard for all IMA HTML
deliverables — the file is self-contained and has no external dependency.

```js
const PDF_NAME = '[Client]_Impact_Measurement_Assessment_[Month][Year].pdf';
const PDF_B64  = "JVBERi0xLjQ...";   // the whole PDF, one line
```

`downloadPDF()` decodes `PDF_B64` with `atob`, builds a `Uint8Array` → `Blob`, and triggers an
`<a download>` click.

**Regenerating it per client** (scripted — never paste base64 by hand):

1. Export the final Doc: Drive `download_file_content` with `exportMimeType: application/pdf`.
   The response is base64 already. Large responses are written to a tool-results file that the
   sandbox can read directly at `.claude/projects/.../tool-results/` — decode from there so the
   base64 never has to pass through a model context.
2. `base64.b64encode(pdf_bytes)` → splice in as the `PDF_B64` literal, replacing the old one.
3. Update `PDF_NAME`.

**Always verify the round-trip.** Extract `PDF_B64` back out of the written file, decode it, and
assert the bytes are identical to the source PDF (compare SHA-256) and that it still parses at
the expected page count. A corrupted embed produces a button that downloads a broken file — it
will not announce itself.

**Expected size.** The embed adds roughly 4/3 the PDF's size, so `index.html` lands in the
hundreds of KB to low MB (xSEL Labs: 721KB for a 356KB, 8-page PDF). That is normal, not a mistake.
This template ships with `PDF_B64` empty — filling it is a per-client step, not a template edit.

**The embed is a snapshot.** If the Doc changes, re-export and re-embed — the HTML will not
update itself.

---

## The theory-of-change figure (region 5)

The model figure is the client's **completed theory of change**: the one-slide figure made
with the toc-synthesizer skill, finalized in the client's Drive folder. It replaced the old
seven-box impact process model in October 2026 (Paper and Lando were the first two). The
section is titled **Theory of Change**. The same slide appears in three places, and all three
must come from the same version of it:

1. **The Doc figure**, inserted as an image (468 pt wide, centered) under the section intro.
2. **The Doc's Model Description table**: one row for the context band, one per ToC column in
   slide order, and one for the lower band (a loop or causal chain) if the ToC has one.
   Row labels are the slide's own headings.
3. **The HTML figure**, built by `toc_figure.py`.

If the client edits the slide after the Doc is drafted, update all three.

### Building the HTML figure

The figure is never drawn by hand. `toc_figure.py` turns the slide into an inline vector
drawing (sharp at any zoom, about 0.8 MB) and lays the interactive parts over it.

1. **Read the slide's geometry.** Slides `read_presentation` with the field mask in the
   script's docstring, then:
   `python3 toc_figure.py regions <tool-results file> > figure.json`
   This finds the context band, one region per column (header pill down to the last box in
   the column) and each lower-band box, named `context`, `col1…colN`, `band1…bandN`.
2. **Edit `figure.json`.** Rename the ids to short words that fit the client (`teachers`,
   `app`, `students`…). Delete regions that should not be clickable, such as a "Where data
   come from" note. Add one entry per priority: `id` (the `priorityData` key), `label`
   (`P1`, `P2`… so the badges do not clash with the ToC's own numbered question markers),
   `color` (closed set below) and `nodes` (the regions that priority measures).
3. **Export the slide**: Drive `download_file_content` on the Slides file with
   `exportMimeType: application/pdf`, decoded from the tool-results file.
4. **Write the `nodes` object and `priorityData` with the same ids**, then run
   `python3 toc_figure.py build index.html --pdf toc.pdf --spec figure.json`.
   It replaces the whole `<svg id="model-svg">` element (re-running is safe) and refuses to
   build if a region has no `nodes` entry, a `nodes` key has no region, or a priority id or
   node is unknown.

### What goes where

- **Clickable regions**: one per Model Description row, and nothing else. A click opens the
  drawer for the `nodes` entry with the same id.
- **`nodes` entries**: `know` is the Doc's Model Description row **word for word**, so the
  drawer and the print table cannot disagree. `gaps` quotes the ToC's open question(s) for
  that element by number and names the priority that answers each. `badge` follows the
  slide's legend: `ok` (all boxes solid, "Observed"), `par` (mixed, "Partly observed"),
  `gap` (all dashed, "Described, not yet verified").
- **Priority badges** sit in a strip just right of the slide, not on it: the ToC carries its
  own numbered markers, and a badge placed on a box hides content. Hovering a badge draws
  connector lines to its regions and dims the rest; clicking opens the priority drawer.
  Colours are the closed set `#1a6fff`, `#059669`, `#d97706`, `#718096`.
- **The print-only Model Description table** mirrors the Doc table row for row.

### Traps

- **Do not round the SVG's coordinates to save space.** It broke the render. The script
  only collapses whitespace between tags.
- **Do not embed the slide as a base64 `<image>`.** It works, but adds a third to the size
  (Lando went from 1.9 MB to 2.2 MB). The script inlines it.
- **Do not use a screenshot.** A raster blurs in full-screen mode and the text is not
  selectable.
- **Inserting the slide into the Doc without a public URL**: Docs `insertInlineImage` with
  the `contentUrl` from Slides `read_slide_page_thumbnail` (large size). The URL is
  short-lived, so insert it straight away.

---

## Do NOT touch (chrome — identical for every client)

**The cover banner is chrome.** `#cover` in `styles.css` carries the standard Cobalt
artwork as a base64 JPEG data URI, layered under a dark scrim gradient. It is identical
for every client — there is no per-client image slot, and no third file to upload.

- Do not swap the image, and do not lighten the scrim's first two stops. The scrim is what
  keeps the left side dark enough for the white client name and meta grid; the artwork is
  light on its right side and the cover type will fail against it without the scrim.
- `background-color: var(--ink)` above it is the fallback. Leave it — if the data URI is
  ever corrupted the cover degrades to dark navy with legible type instead of white on white.
- It prints. `-webkit-print-color-adjust: exact` is already set on `#cover`.
- It survives `bundle.py`, because it lives in the CSS the bundler inlines.

- The entire `styles.css` file (all CSS, including `--measure` and the layout variables).
  If a client genuinely needs a new component, add a rule to `styles.css` and treat it as a
  template improvement — don't inline styles into one client's HTML.
- All JS **functions/logic**: `show()`, `toggleCard()`, `toggleBadges()`, `openPriorityCard()`,
  `hidePriorityPopup()`, `toggleFullscreen()`, `openAboutModal()` (+ its close handler),
  `downloadPDF()`, the scroll-spy `IntersectionObserver` + `navMap`, and the sticky-TOC
  `--toc-pin` logic. You edit the JS **data** — `nodes`, `priorityData`, `navMap` keys, and
  the `PDF_B64` / `PDF_NAME` values — never the function bodies.
- The `#model-svg` figure: generated by `toc_figure.py`. Change the slide or `figure.json`
  and re-run the script; never edit the generated SVG.
- The cover topbar, the Cobalt Collective logo SVG, the footer brand, and the
  `cobaltcollective.org` author identity.
- The `.print-only` Model Description block — hidden on screen, restored in print.

---

## Coupling to keep in sync

- **Nav ↔ sections ↔ navMap:** every section `id` needs a nav `<a href="#x">` *and* a `navMap`
  entry, or scroll-spy highlighting breaks. Track sub-items use `.nav-item.sub` with a
  `.nav-badge` count that must equal the number of priority cards in that track.
- **Matrix ↔ priorities:** the `.pm-dots` in each card header must have the same number and
  order of columns as the `.priority-matrix-key` above it. Each track section carries its own
  copy of the key row as the first child of its `.priority-cards.priority-matrix` container.
- **Badges ↔ cards ↔ priorityData:** the badge `data-priority`, the card `id="card-<x>"`, and
  the `priorityData` key are the same identifier. All three must agree.
- **Legend ↔ key row:** the `.matrix-legend` line explaining ●/○/– belongs immediately
  after the `.priority-matrix-key` block, inside the same `.priority-cards.priority-matrix`
  container — one per track. It does **not** belong at the end of the Measurement
  Opportunities section; that is where it lands if you carry the Word report's structure
  over verbatim, because there it sits under the at-a-glance table, which the HTML has no
  equivalent of.
- **Track counts:** nav badge number = cards in that track = badges in the figure for that
  track.

---

## Post-generation checklist

- [ ] **No `[bracketed]` placeholder text survives anywhere** — this is the failure mode a
      neutral template creates, and it is the one that embarrasses. Run the pre-delivery
      check, which scans for it in the body, the `<head>`, and the JS constants.
- [ ] No text inherited from another client. This template carries none, but copying a
      section across from a completed client file will.
- [ ] "Cobalt Collective" author identity intact (cover topbar logo, About modal, footer).
- [ ] `PDF_B64` regenerated from **this client's** final Doc, and `PDF_NAME` updated.
      Verified by round-trip: extracted, decoded, SHA-256 matches the source PDF.
      Then click the button in a browser and confirm the downloaded file opens correctly.
- [ ] The ToC figure, the Doc's figure and the Model Description rows all come from the same
      version of the slide, and each `know` matches its Doc row word for word.
- [ ] Open in a browser: every ToC region click opens a drawer with matching content.
- [ ] Toggle "Show measurement priorities": badges appear; hovering a badge highlights its
      connector lines and dims the other nodes; clicking opens the right priority drawer.
- [ ] Full-screen button on the figure expands and collapses.
- [ ] All priority cards expand/collapse; the dot columns line up under the key row.
- [ ] The ●/○/– legend sits directly under each track's key row, not at the end of the
      previous section.
- [ ] Scroll top→bottom: the sticky TOC active state tracks the visible section, including
      the track sub-items.
- [ ] About modal opens and closes from both cover buttons (topbar and the narrow-screen one).
- [ ] Print/PDF preview looks right (the print-only Model Description renders; TOC and topbar
      are hidden; priority card bodies are expanded).
- [ ] The About-the-client section names the client, the user, the buyer and the scope
      boundary, repeats nothing from the ToC's context band, and has both
      a nav link and a `navMap` entry.
- [ ] "What Changes If You Do This" is specific to this client — swapping the company name
      into the next report would produce nonsense, not a usable paragraph — carries no hedges,
      and has a nav link and a `navMap` entry.
- [ ] Prose still respects the `--measure` width — no paragraph runs the full page width.
- [ ] Responsive: below ~860px the TOC hides and the About button moves under the cover meta.
