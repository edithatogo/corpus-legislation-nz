# Corpus Family Alignment Design

## Design Principle

`corpus-nz-legislation` and `corpus-nz-hansard` should operate as sibling projects in a systematic New Zealand public-text corpus family. They may have different source systems and schemas, but they should share naming conventions, publication-surface rules, validation gates, and release evidence patterns.

## Preferred Names

| Corpus | Preferred project label | Current/local or published names observed | Naming action |
| --- | --- | --- | --- |
| Legislation | `corpus-nz-legislation` | local `corpus-law-nz`; GitHub `corpus-legislation-nz`; package `corpus-legislation-nz` | Track migration/reservation without breaking citations. |
| Hansard | `corpus-nz-hansard` | local/GitHub `corpus-nz-hansard`; HF `nz-hansard-corpus` | Keep, and align metadata references. |

## Publication Surface Model

```mermaid
flowchart LR
  subgraph Family["NZ corpus family"]
    L["corpus-nz-legislation"]
    H["corpus-nz-hansard"]
  end
  subgraph GitHub["GitHub: code and automation"]
    LGH["legislation repo / workflows / releases"]
    HGH["hansard repo / workflows / releases"]
  end
  subgraph HF["Hugging Face: operational datasets"]
    LHF["edithatogo/corpus-legislation-nz"]
    HHF["edithatogo/nz-hansard-corpus"]
  end
  subgraph Zenodo["Zenodo: fixed DOI archives"]
    LZ["10.5281/zenodo.20592540"]
    HZ["10.5281/zenodo.20595194"]
  end
  subgraph Optional["Optional mirrors and metadata"]
    OSF["OSF review/mirror bundles"]
    META["Croissant / RO-Crate / Frictionless / DCAT / PROV-O"]
  end
  L --> LGH --> LHF --> LZ
  H --> HGH --> HHF --> HZ
  LGH -.cross-reference.-> HGH
  LHF -.dataset family links.-> HHF
  LZ -.related identifiers.-> HZ
  LGH --> OSF
  HGH --> OSF
  LHF --> META
  HHF --> META
```

## Environment Alignment Matrix

| Environment | Shared role | Legislation requirement | Hansard requirement |
| --- | --- | --- | --- |
| GitHub | Code, tests, CI, releases, docs, lightweight packages | Prefer future label `corpus-nz-legislation`; keep current published repo stable until migration plan. | Continue `corpus-nz-hansard`; add engineering alignment with legislation baseline. |
| Hugging Face | Dataset hosting, Parquet, cards, Xet storage | Keep `edithatogo/corpus-legislation-nz`; verify access/gating and viewer layout. | Keep `edithatogo/nz-hansard-corpus`; fix viewer split/layout issue and verify ungated access. |
| Zenodo | Fixed DOI archives | Keep published DOI; align related identifiers to GitHub and HF; license must not overclaim source rights. | Keep latest DOI; mark older review DOI as superseded; align license/source-rights wording. |
| OSF | Optional review or mirror | Do not require until file-size/splitting and citation policy are documented. | Same; use only for review bundles or mirrors if explicitly approved. |
| Future metadata registries | SOTA discovery and interoperability | Add Croissant/RO-Crate/Frictionless/DCAT/PROV-O as generated metadata artifacts. | Same; can use Hansard interoperability tracks as baseline. |

## Release Gate Diagram

```mermaid
flowchart TD
  A["Prepare release candidate"] --> B["GitHub metadata and CI audit"]
  B --> C["Hugging Face dataset card, files, access, viewer audit"]
  C --> D["Zenodo draft metadata, files, related identifiers audit"]
  D --> E["Optional OSF/mirror decision"]
  E --> F["Cross-corpus naming and sibling-link audit"]
  F --> G{"All public claims aligned?"}
  G -- No --> H["Fix docs/cards/metadata before release"]
  H --> B
  G -- Yes --> I["Approve publish or tag"]
  I --> J["Record evidence in Conductor track"]
```

## Design Notes

- GitHub is the automation and documentation controller, not the large-data host.
- Hugging Face is the browsable/operational dataset host and should remain ungated unless a deliberate access policy says otherwise.
- Zenodo records should be immutable citation snapshots and should link both GitHub and Hugging Face where possible.
- OSF is useful only if it adds review, institutional, or redundancy value without creating another unsynchronised source of truth.
- Every public surface should expose the same preferred naming family and sibling-corpus links.

## Recommended Additional Tracks

```mermaid
flowchart TD
  A["Corpus-family publication alignment"] --> B["Public-surface audit evidence"]
  A --> C["Zenodo rights metadata harmonisation"]
  C --> ZD["Zenodraft-based draft workflow"]
  A --> D["Shared NZ corpus core schema"]
  A --> E["SOTA metadata packages"]
  A --> F["OSF optional mirror policy"]
  A --> G["Dataset viewer and machine-consumability gates"]
  B --> H["Release evidence ledger"]
  D --> H
  E --> H
  G --> H
```

### Zenodraft integration design

Future Zenodo automation should prefer `zenodraft` (`https://github.com/zenodraft/zenodraft`) for draft deposition operations. The design target is:

1. Generate archive files and `.zenodo.json` metadata locally.
2. Run `zenodraft metadata validate .zenodo.json` before upload.
3. Use `zenodraft deposition create concept` or `zenodraft deposition create version <concept_id>` for draft creation.
4. Use `zenodraft file add` and `zenodraft metadata update` for draft contents.
5. Use `zenodraft deposition show prereserved` and `show details` to capture evidence.
6. Keep `zenodraft deposition publish` in a separate protected approval step.

CI must map repository secrets to `ZENODO_ACCESS_TOKEN` or `ZENODO_SANDBOX_ACCESS_TOKEN` only for the step that needs them.
