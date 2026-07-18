# Gale documentation site

Sphinx site for https://r3mmurd.github.io/Gale/, built with
`sphinx_rtd_theme`. Guide pages under `source/examples/` and the API
reference under `source/api/` are generated (not committed) from this
repo's `docs/examples/*.rst` guides and the `gale` package's
docstrings, so they always match the checked-out commit — see the
`prepare` target in `Makefile`.

## Building locally

From the repo root:

```bash
pip install -e .
pip install -r docs/sphinx/requirements.txt
make -C docs/sphinx html
```

Open `docs/sphinx/build/html/index.html` in a browser.

## Deployment

`.github/workflows/docs.yml` builds this site and deploys it to
GitHub Pages every time a release is published (the same trigger that
publishes to PyPI, so the docs always match what's on PyPI). Enable it
once via Settings -> Pages -> Source -> "GitHub Actions".
