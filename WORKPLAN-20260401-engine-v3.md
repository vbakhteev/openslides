# WORKPLAN: OpenSlides Engine v3 - Gemini Renderer Quality

**Created:** 2026-04-01
**Status:** PLANNING
**Approach:** Validate each change with experiments before building into production engine.
**Baseline:** Current Gemini renderer produces 8/10 single slides, but all decks look similar (same template reference).

## The 6 Engine Changes

### 1. Template Library Expansion (Biggest lever)

**Hypothesis:** More diverse reference templates = more diverse output.

**What to do:**
- Curate 30+ reference slides across 5 styles (warm-tech, consulting, consumer, minimal, classic)
- Each style needs: title, problem, solution, market, competition, traction, funds, team (8 types x 5 styles = 40 templates)
- Sources: floom deck (have), old openslides (have), hand-craft new ones, or use Gemini to generate reference templates from the best experiment outputs

**Validation test:**
- Pick 3 test prompts (tech, consulting, consumer)
- Run each with warm-tech templates (current)
- Run each with style-matched templates (consulting templates for consulting brief, etc.)
- Screenshot and compare: does style-matching produce better, more varied results?

**Effort:** 1-2 sessions (curating + organizing templates)

### 2. Multi-Turn Per-Slide Generation (Second biggest lever)

**Hypothesis:** Generating each slide individually with a dedicated reference template produces higher quality than generating all 8 slides in one prompt.

**What to do:**
- Step 1: Generate deck outline (slide types + one-line key messages) in one Gemini call
- Step 2: For each slide, make a separate Gemini call with:
  - The specific reference template for that slide type
  - The full company context
  - The key message for this slide from the outline
  - Theme tokens

**Validation test:**
- Take 1 test prompt (e.g., healthcare)
- Generate with current approach (1 prompt, all 8 slides)
- Generate with multi-turn (1 outline + 8 individual slides)
- Screenshot and compare: better quality? More variety between slides?
- Measure: time difference (expect ~2x slower but higher quality)

**Effort:** 0.5 session to test, 1 session to build into engine

### 3. Style Routing

**Hypothesis:** Automatically matching company/industry to visual style produces better results than one-size-fits-all.

**What to do:**
- Add industry detection (from company URL scrape or brief keywords)
- Map industries to styles:
  - SaaS/devtools -> warm-tech or minimal
  - Consulting/B2B services -> consulting
  - Consumer/DTC -> consumer
  - Fintech -> minimal
  - Healthcare -> clean/professional
  - Marketplace -> warm or consumer
  - Climate/impact -> earthy/warm
  - Agency -> bold/minimal
- Override: user can specify style explicitly

**Validation test:**
- Generate the consulting_b2b prompt with consulting templates
- Generate the consumer_app prompt with consumer templates
- Compare to current (all using warm-tech templates)
- Does auto-routing produce more appropriate designs?

**Effort:** 0.5 session to test, 0.5 session to build

### 4. Tools in the Loop

**Hypothesis:** Feeding resolved logos, scraped brand info, and product screenshots INTO the Gemini prompt produces richer slides.

**What to do:**
- Before calling Gemini, pre-resolve:
  - Company logo (SimpleIcons SVG or favicon URL)
  - Competitor logos (for comparison slide)
  - Brand colors from URL scrape
  - Product screenshot (base64 or description)
- Inject these into the per-slide Gemini prompt:
  - "The company logo is: [SVG inline or URL]"
  - "Competitors: Replit (logo: [URL]), Railway (logo: [URL])"
  - "Product screenshot shows: [description from scrape]"

**Validation test:**
- Generate the tech_saas deck with tools (logo + screenshot URL for floom.dev)
- Generate without tools (current)
- Compare: does the title slide include a real product visual? Does competition include logos?

**Effort:** 0.5 session to test, 1 session to build

### 5. Per-Slide Reference Selection

**Hypothesis:** Picking the BEST reference template for each slide type produces better results than using 3 generic references for the whole deck.

**What to do:**
- When generating each slide (in multi-turn mode), include ONLY the reference template that matches that slide type
- Problem slide gets the best problem template
- Market slide gets the best market template
- Each reference is the full HTML (not truncated)

**Validation test:**
- This is tested implicitly with experiment #2 (multi-turn). If multi-turn works, per-slide reference is part of it.

**Effort:** Built into #2

### 6. Quality Gate (Auditor Loop)

**Hypothesis:** Auto-regenerating low-scoring slides improves the deck without manual intervention.

**What to do:**
- After generating all slides, screenshot each on AX41 (Playwright)
- Send screenshots to Gemini auditor with scoring rubric
- If any slide < 7/10, regenerate with the auditor's feedback as additional context
- Max 1 retry per slide

**Validation test:**
- Generate a full deck
- Run auditor
- Take the lowest-scoring slide, regenerate with feedback
- Compare before/after

**Effort:** 1 session (auditor exists, need to wire the retry loop)

## Validation Plan

Run experiments in parallel where possible. Each experiment produces a concrete artifact (screenshot) and a go/no-go decision.

| # | Experiment | Hypothesis | How to Test | Effort |
|---|-----------|-----------|-------------|--------|
| A | Style-matched templates | Matching style to industry improves quality | 3 prompts x 2 approaches, compare screenshots | 30 min |
| B | Multi-turn per-slide | Individual slide generation > batch | 1 prompt x 2 approaches, compare screenshots | 30 min |
| C | Tools injection | Logos + screenshots in prompt improve richness | 1 prompt x 2 approaches, compare | 30 min |
| D | Auditor retry | Regenerating low slides improves deck | 1 deck, auditor, 1 retry | 30 min |

All 4 experiments can run as parallel agents. Total validation time: ~30 min.

## Build Order (after validation)

Only build what the experiments validate. If an experiment shows no improvement, skip it.

| Priority | Change | Depends on | Effort |
|----------|--------|-----------|--------|
| 1 | Template library expansion (curate 30+ slides) | Nothing | 1-2 sessions |
| 2 | Multi-turn per-slide generation | Templates | 1 session |
| 3 | Style routing | Templates | 0.5 session |
| 4 | Tools injection (logos, screenshots) | Multi-turn | 1 session |
| 5 | Per-slide reference selection | Multi-turn | Built into #2 |
| 6 | Quality gate (auditor retry) | All above | 1 session |

Total: ~5-6 sessions after validation.

## What NOT to Change

- The Gemini-as-renderer approach (validated, works)
- The theme system (works)
- The few-shot prompt structure (works)
- The test harness (10 prompts, works)
- The tooling layer (logos, scraping, export, all work)

## Success Criteria

Run all 10 test decks. Every deck should:
1. Score 8+/10 from Gemini auditor
2. Look visually DIFFERENT from other decks (no two decks identical layout)
3. Match the company's industry/brand feel
4. Fill every slide (no dead space, no empty areas)
5. Include real data viz, icons, or mockups where appropriate
