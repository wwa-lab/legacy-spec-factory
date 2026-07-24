# Critical Review Of The English Draft

## Accuracy

- **Dify status wording:** In the current-capability table, “current internal
  implementation approach” is weaker than the source. Replace it with “current
  internal implementation” while keeping the Pilot Control caveats.
- **Lifecycle wording:** “Legacy reverse discovery” is understandable but
  unnatural. Use “Legacy reverse engineering and discovery” without implying
  downstream modernization delivery.
- **Status boundaries:** COBOL, other platforms, BRD approval, downstream
  Build/Testing/Deployment, and Pilot metrics are otherwise preserved
  correctly.
- **Facts and numbers:** The 95%, 5%, 10K+, two-round, and 5-10-program targets
  match the source and remain framed as proposed acceptance targets.
- **Intermediate links:** Links are correct for the translation work
  subdirectory. They must be rewritten when the final English file is
  published in `docs/`.

## Native Voice

- **Title:** “Project Details” sounds generic. Use the document name expected
  by the repository: “Project Detail: Atlas Phoenix Lens.”
- **Capitalization:** Generic concepts such as modernization knowledge,
  program behavior, calculations, validations, files, and paths are
  over-capitalized in several sections. Retain capitals only for product names,
  formal status names, and artifact types.
- **Section 3 table:** “Actual boundary” is literal and slightly awkward. Use
  “Governance or implementation boundary.”
- **Section 4.4:** “Move a BRD draft beyond its authority” is unnatural. Use
  “promote a BRD draft directly into Build, Testing, or SDD.”
- **Section 8 heading:** “Significance and Business Value for the Company” is
  less direct than the source intent. Use “Company Impact and Commercial
  Value.”
- **Business-value bullets:** Normalize label capitalization and replace
  “duplicated project setup” with “rebuilding the same discovery solution.”
- **Closing line:** Lowercase generic “modernize legacy systems” for native
  English while preserving the slogan.

## Notes And Adaptation

- No translator notes are needed; the intended audience understands the
  technical terms.
- Add the English README and English roadshow script to the final Related
  Materials section. Keep a link to the Chinese source for bilingual review.
- The two embedded diagrams already use English labels, so no image-text
  localization is required.

## Summary

No critical factual omissions were found. The revision should address one
material status-wording issue, final-link paths, and several native-voice and
capitalization improvements before publication.
