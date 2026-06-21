# Mirror sync setup

Track 35 keeps GitHub as the canonical repository and mirrors code to secondary
Git hosts only after explicit maintainer configuration. Mirror setup is
independent of the full corpus download.

## Required GitHub secrets

Configure these repository secrets on `edithatogo/corpus-legislation-nz`:

- `GIT_MIRROR_URLS`: newline-separated SSH remotes, for example GitLab and
  Codeberg remotes in `git@host:owner/repo.git` form.
- `GIT_MIRROR_SSH_PRIVATE_KEY`: private key accepted by each secondary Git
  remote.

`GIT_MIRROR_URL` remains supported for one legacy mirror remote, but
`GIT_MIRROR_URLS` is preferred for Track 35.

Do not commit mirror private keys, deploy keys, or generated known-host files to
the repository.

## CLI setup

From an authenticated GitHub CLI session:

```powershell
gh secret set GIT_MIRROR_URLS --repo edithatogo/corpus-legislation-nz
gh secret set GIT_MIRROR_SSH_PRIVATE_KEY --repo edithatogo/corpus-legislation-nz
```

Paste secret values only into the GitHub CLI prompt. Do not write them to a
tracked file.

## Live verification

After `.github/workflows/mirror_sync.yml` is present on the default branch,
dispatch the workflow manually:

```powershell
gh workflow run mirror_sync.yml --repo edithatogo/corpus-legislation-nz --ref main
```

Then inspect the run:

```powershell
gh run list --repo edithatogo/corpus-legislation-nz --workflow mirror_sync.yml --limit 1
gh run view <run-id> --repo edithatogo/corpus-legislation-nz --log-failed
```

Track 35 can record the mirror gate as verified only when the workflow run
succeeds and each configured secondary remote contains the expected mirrored
branch.
