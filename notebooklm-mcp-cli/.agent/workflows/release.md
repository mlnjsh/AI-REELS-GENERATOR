---
description: How to create a new release of notebooklm-mcp-cli
---

# Release Process

// turbo-all

## Steps

1. Ensure you're on the release branch (e.g., `dev/0.2.18`)

2. Bump version in both files:
   - `pyproject.toml` → `version = "X.Y.Z"`
   - `src/notebooklm_tools/__init__.py` → `__version__ = "X.Y.Z"`
   - `src/notebooklm_tools/data/SKILL.md` (frontmatter) → `version: "X.Y.Z"`
   - `src/notebooklm_tools/data/AGENTS_SECTION.md` (comment) → `<!-- nlm-version: X.Y.Z -->`

3. Update `CHANGELOG.md` with the new version entry

4. **Review and update documentation** for any CLI changes:
   - `README.md` — authentication, feature docs
   - `docs/CLI_GUIDE.md` — user-facing command guide
   - `src/notebooklm_tools/cli/ai_docs.py` — AI-friendly docs (`nlm --ai`)
   - `src/notebooklm_tools/data/SKILL.md` — AI skill file
   - `src/notebooklm_tools/data/references/command_reference.md` — full command reference

5. Reinstall locally and test:
```bash
uv cache clean && uv tool install --force .
```

6. Run tests:
```bash
uv run python -m pytest
```

7. Commit all changes:
```bash
git add -A && git commit -m "release: vX.Y.Z"
```

8. Push and tag:
```bash
git tag vX.Y.Z && git push origin main --tags
```

9. Create a GitHub release to trigger PyPI publish:
```bash
gh release create vX.Y.Z --title "vX.Y.Z" --generate-notes
```

## Checklist

- [ ] Version bumped in `pyproject.toml`, `__init__.py`, `SKILL.md`, and `AGENTS_SECTION.md`
- [ ] CHANGELOG updated
- [ ] Docs reviewed and updated (README, CLI Guide, ai_docs.py, SKILL.md, command_reference.md)
- [ ] Tests pass (`uv run python -m pytest`)
- [ ] Committed and pushed
- [ ] Tagged
- [ ] GitHub release created (triggers PyPI publish)
