# Plan - Corpus Family Naming And Publication Alignment

## Phase 1 - Naming and sibling setup

- [ ] Record `corpus-nz-legislation` as the preferred systematic project label in Conductor product/setup docs.
- [ ] Cross-reference `corpus-nz-hansard` and its local path in Conductor setup.
- [ ] Create or update requirements and design docs with naming decision and Mermaid diagrams.
- [ ] Document current published names and migration risks.

## Phase 2 - GitHub environment

- [ ] Audit current GitHub repo metadata, topics, homepage, release tags, branch/ruleset posture, Actions, CodeQL, Scorecard, Renovate, license, and SECURITY files.
- [ ] Decide whether to reserve or migrate `corpus-nz-legislation` as a GitHub repository name.
- [ ] Add explicit cross-links to `corpus-nz-hansard` where appropriate.
- [ ] Ensure release notes and README keep partial/API-discovery caveats.

## Phase 3 - Hugging Face environment

- [ ] Audit `edithatogo/corpus-legislation-nz` card metadata, access/gating, files, viewer behaviour, Xet status, DOI links, and GitHub links.
- [ ] Ensure dataset card uses preferred family naming and links sibling Hansard corpus.
- [ ] Verify manifest files are visible without confusing dataset viewer splits.
- [ ] Record HF revision and manifest hash in evidence.

## Phase 4 - Zenodo environment

- [ ] Audit Zenodo DOI record metadata, creators, license, files, related identifiers, concept DOI, and links to GitHub/HF.
- [ ] Ensure license wording does not overclaim source legislation rights.
- [ ] Align related identifiers to both live HF dataset and GitHub source repository where possible.
- [ ] Keep production publish draft-first and reviewer-approved.

## Phase 5 - OSF and other environments

- [ ] Decide whether OSF is needed for review bundles, mirrors, or institutional archiving.
- [ ] If OSF is used, define file-size/splitting, citation, checksum, and update policy.
- [ ] Add optional SOTA metadata tasks for Croissant, RO-Crate, Frictionless, DCAT, and PROV-O.

## Verification

- [ ] Requirements/design docs include the naming preference and environment matrix.
- [ ] Mermaid diagrams render structurally.
- [ ] Conductor tracks.md registers this track.
- [ ] All environment tasks are present and cross-reference Hansard.
