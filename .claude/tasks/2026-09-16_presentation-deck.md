# Presentation deck (PowerPoint) for the course-project defense

Goal: a designed .pptx deck built from the outline `reports/slides/slides.md`
(user-edited, uncommitted: member list added, "Phân công" slide removed on purpose;
do NOT re-add it, do NOT commit the user's own edits to slides.md / xlsx).

## Decisions
- Tool: PowerPoint via pptxgenjs, not Gamma. Reasons: submission needs a .pptx
  (`scripts/assemble-submission.py` expects `reports/slides/slides.pptx`), real
  figures/screenshots must be embedded, and every number must match
  `reports/tables/*.md` exactly (Gamma rewrites content and cannot take local images).
- Output: NEW file `reports/slides/slide-thuyet-trinh.pptx`. Do not overwrite
  `reports/slides/slides.pptx` (pandoc build artifact; `make slides` regenerates it).
  Ask the user before repointing the submission script.
- Generator: `reports/slides/deck/build-deck.js` (node + pptxgenjs); numbers copied
  from `reports/tables/*.md`, verified after build.
- Pipeline figure `reports/figures/01-pipeline-tong-the.png` is stale (mentions
  Batdongsan, "Hạn: buổi 10", contains an em dash) -> redraw pipeline natively.
- Slide text in Vietnamese, zero em dashes, speaker notes on every slide.

## Checklist
- [x] Read outline, included tables, figures, README
- [x] Check tooling: node 22 ok; pptxgenjs/react-icons/sharp installed in
      scratchpad `deckenv/`; markitdown+validate deps in scratchpad `pyenv/`.
      No LibreOffice. PowerPoint AppleScript "save as PDF" to /private/tmp hangs
      (sandbox file-access). Assistive access denied, cannot see dialogs.
- [x] Read result tables for E1/E2/E3/extraction/funnel/learning curve
- [x] Pick palette (ink 13303A + terracotta C8553A) + motif (numbered chip,
      roof over the 4-tier model "building"), write generator

## Accuracy fixes vs outline (report these to the user)
- slide-e1.md says "LightGBM và XGBoost hơn baseline 6,66": JSON gives LGBM 6,66,
  XGB 6,53, CatBoost 6,32 -> deck uses "6,32–6,66" (README wording) + CatBoost row.
- E2 outline says drift is "thuần tuý": e2-results.md says train/test also differ by
  platform -> deck keeps "không lẫn giá rao/giao dịch" but adds the platform caveat.
- Demo "khoảng tin cậy" -> "khoảng tham khảo" (the app's own label; not a CI).
- Pipeline PNG stale -> redrawn natively with data-funnel numbers.
- Outline only flags số tầng below F1 0,9, but phòng ngủ 0,887 is also under the
  target (runbook target covers diện tích, phòng ngủ, số tầng) -> speaker notes.
- ablation.md prose says "cải thiện lớn nhất 0,86" but table max is 0,89 -> deck uses table.
- [x] Build deck (18 slides, speaker notes on every slide)
- [x] validate PASSED + markitdown content QA (numbers vs tables, 0 em dash)
- [x] Render round 1 via PowerPoint (use `with timeout of 900 seconds`, ~4 min),
      visual QA of all 18 slides, fixes applied (s3 dataset name wrap, s8 spacing,
      s9 bullet wraps, s11/s12 captions, s13/s15 hyphen breaks, image altText)
- [x] Render round 2, re-check slides 3, 8, 9, 11, 12, 13, 15: all clean
      (validate PASSED, 0 em dash, no local paths in alt text)
- [x] Speaker notes audit (avoid-ai-writing-vi detect): no P0/P1; fixed
      "Tóm lại" opener and "CatBoost bền nhất" overclaim
- [x] Commit deck + generator + this checklist (only my files; not pushed)
- [ ] Report to user; offer to repoint submission to the new deck
