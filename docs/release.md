# Release procedure

We use [trusted publishing with PyPI](https://docs.astral.sh/uv/guides/integration/github/#publishing-to-pypi) for our release.
Check the `.github/workflows/release.yaml` workflow.

## Steps to release

1. Edit the version on `pyproject.toml`
2. Run `uv lock` to update `uv.lock` file
3. Commit changes: `git add pyproject.toml uv.lock && git commit -m "Bump version to 0.X.Y"`
4. Create release tag: `git tag -a v0.X.Y -m "Release v0.X.Y"`
5. Push tag: `git push origin v0.X.Y`

Check the github action for the tag was successful, validate the wheel and source distribution is on PyPI.

Create new release manually on GitHub selecting the tag and adding the title as v0.X.Y.

Click Generate Release notes from previous tag.

## Testing locally before release (optional)

```bash
# Clean old builds
rm -rf dist/

# Build
uv build

# Smoke test wheel
uv run --isolated --no-project --with dist/*.whl datanomy --help

# Smoke test source distribution
uv run --isolated --no-project --with dist/*.tar.gz datanomy --help
```
