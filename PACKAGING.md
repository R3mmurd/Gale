# Publishing to PyPI

Gale is published on PyPI as [`gale-engine`](https://pypi.org/project/gale-engine/)
(`gale` and several close variants were already taken; `import gale`
is unaffected). Publishing is fully automated through
[`.github/workflows/publish.yml`](.github/workflows/publish.yml)
using PyPI's [Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
(OIDC): there is no API token stored anywhere — GitHub mints a
short-lived identity token for the workflow run, and PyPI trusts it
based on the publisher configured on the project's own PyPI settings.

## One-time setup (already done for `gale-engine`, keep for reference)

1. Have a [PyPI](https://pypi.org/) account with 2FA enabled (PyPI
   requires it).
2. Go to https://pypi.org/manage/account/publishing/ and add a
   **pending publisher** (this works even before the project exists
   on PyPI at all — the first trusted-publisher-authenticated upload
   creates it):
   - PyPI project name: `gale-engine`
   - Owner: `R3mmurd`
   - Repository name: `Gale`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
3. In the GitHub repo, create an **environment** named `pypi`
   (Settings → Environments → New environment). Optional but
   recommended: add required reviewers so publishing needs a manual
   approval click, as a last line of defense against an accidental or
   compromised release.

Nothing else is needed — no secret, no token, nothing to rotate.

## How a release actually publishes

Publishing a [GitHub Release](https://github.com/R3mmurd/Gale/releases)
(`release: published`) triggers the workflow: it builds the sdist and
wheel with `python -m build`, then uploads both to PyPI via
[`pypa/gh-action-pypi-publish`](https://github.com/pypa/gh-action-pypi-publish).

Cutting a release, in order:

1. Bump the version in `pyproject.toml` (`[project].version`) and the
   `GithubCommits` badge in `README.rst`, in their own PR into
   `develop` (see past `chore/bump-version-*` PRs for the shape).
2. Open a PR from `develop` into `main` and merge it (`develop` is
   never deleted — see `README.rst`'s Git workflow section).
3. Create a GitHub Release on `main`, tagged `vX.Y.Z` matching the
   version just bumped. Publishing it fires the workflow above
   automatically.

## Building/checking a release locally

The same tools the workflow uses, for a dry run before tagging
anything:

```bash
pip install -r requirements/dev.txt   # includes build + twine
rm -rf dist build
python -m build
twine check dist/*
```

`twine check` catches most long_description/metadata problems (e.g. a
`README.rst` construct PyPI's renderer can't handle) before they ever
reach a real upload.
