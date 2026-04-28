# AGENTS.md — schemaorg-arc-builder

> Guidance for AI coding agents (Claude Code, Codex, Cursor, etc.) working on this repository.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture & Pipeline](#architecture--pipeline)
3. [Directory Map](#directory-map)
4. [Environment Setup](#environment-setup)
5. [Running the Project](#running-the-project)
6. [Code Standards](#code-standards)
7. [Testing](#testing)
8. [Branch Naming & Workflows](#branch-naming--workflows)
9. [Feature Workflows](#feature-workflows)
10. [Known Issues & Technical Debt](#known-issues--technical-debt)
11. [Design Patterns to Follow](#design-patterns-to-follow)
12. [Extending the Parser](#extending-the-parser)
13. [Out-of-Scope for Agents](#out-of-scope-for-agents)

---

## Project Overview

`schemaorg-arc-builder` converts **Schema.org JSON-LD** metadata into **ISA RO-Crate** structures and optionally submits them to **GitLab as ARCs** (Annotated Research Contexts).

The domain is scientific research data management. The three main standards in play are:

| Standard | Role | Key Spec |
|---|---|---|
| Schema.org JSON-LD | Input format — metadata from institutional repositories | https://schema.org |
| RO-Crate | Intermediate/output format — research objects | https://www.researchobject.org/ro-crate/ |
| ISA (Investigation/Study/Assay) | Structural model mapped into the RO-Crate | https://isa-specs.readthedocs.io |
| ARC (Annotated Research Context) | GitLab-compatible output using ARCtrl | https://arc-rdm.org |

**Input repositories supported** (see `examples/`): BonaRes, e!DAL, OpenAgrar, PlabiPD, Publisso.

---

## Architecture & Pipeline

```
JSON-LD file
     │
     ▼
[SchemaOrgParser]          schemaorg_arc_builder/parser.py
  • Normalizes @graph, single entity, and array forms
  • Classifies entities: datasets / persons / organizations / publications / other
  • Resolves PropertyValue identifiers, dates, PostalAddress, ContactPoint
     │
     ▼  parsed_data dict (datasets, persons, organizations, publications, other)
     │
     ▼
[ISAROCrateBuilder]        schemaorg_arc_builder/rocrate_builder.py
  • Builds an RO-Crate (via `rocrate` library)
  • Maps Dataset → Investigation + Study (+ optional Assay)
  • Maps Person / Organization → rocrate entities
  • Deduplicates entities via added_entities registry
     │
     ▼  ro-crate-metadata.json  (output_crates/<name>/ro-crate-metadata.json)
     │
     ▼
[ARCCreator]               scripts/arc_creator.py
  • Reads ro-crate-metadata.json
  • Uses ARCtrl Python bindings to build ARC structure
  • Outputs isa.investigation.xlsx, studies/, assays/
     │
     ▼
[GitLabSubmitter]          scripts/gitlab_submitter.py
  • Pushes ARC directory to a GitLab instance
  • Reads credentials from .env
```

**Critical constraint**: The pipeline is strictly one-directional. Each layer must not import from the layer above it. `parser.py` must never import from `rocrate_builder.py`.

---

## Directory Map

```
schemaorg_arc_builder/
├── schemaorg_arc_builder/
│   ├── __init__.py              # Public API: SchemaOrgParser, ISAROCrateBuilder
│   ├── __main__.py              # CLI entry point (python -m or schemaorg-rocrate-parser)
│   ├── parser.py                # Layer 1 — JSON-LD → normalized dict
│   └── rocrate_builder.py       # Layer 2 — dict → RO-Crate
├── scripts/
│   ├── arc_creator.py           # Layer 3 — RO-Crate → ARC (ARCtrl)
│   ├── gitlab_submitter.py      # Layer 4 — ARC → GitLab push
│   └── gitlab_submit.py        # CLI wrapper for gitlab_submitter
├── examples/                    # Real-world JSON-LD input examples
├── output_crates/               # Committed example outputs (DO NOT delete)
├── tests/                       # pytest suite: test_*.py, conftest.py
├── assets/                      # Images for README
└── pyproject.toml
```

---

## Environment Setup

```bash
# Install dependencies (preferred)
uv sync

# Or with pip
pip install -e .

# Copy and fill in credentials for GitLab submission
cp .env.example .env
# Edit .env: GITLAB_URL, GITLAB_PRIVATE_TOKEN, GITLAB_NAMESPACE_ID, GITLAB_GROUP_ID
```

**Python version**: >= 3.13 (enforced in pyproject.toml).

**Never commit `.env`** — it contains private tokens.

---

## Running the Project

```bash
# Parse a JSON-LD file → write RO-Crate to disk
python main.py examples/example_edal.json -o output_crates/edal_arc

# Parse → print JSON-LD to stdout (for inspection)
python main.py examples/example_bonares.json --json

# Generate ARC from existing RO-Crate
python scripts/arc_creator.py output_crates/edal_arc/ro-crate-metadata.json

# Submit ARC to GitLab
python scripts/gitlab_submit.py output_crates/edal_arc/arc --name my-arc --overwrite
```

---

## Code Standards

### Python Style

- Follow **PEP 8** with 4-space indentation.
- Use **type hints** on all public methods and function signatures.
- Keep docstrings in **Google style** (Args / Returns / Raises), matching the existing pattern.
- **All imports must be at the top of the file** — never inside methods or functions. This is a known tech debt violation in `rocrate_builder.py` (`import re` inside `_sanitize_identifier`, `from rocrate...` imports inside several methods). When touching those methods, move the imports to the top.
- Prefer `pathlib.Path` over raw string paths everywhere.
- Use `Union[X, Y]` or `X | Y` (Python 3.10+) for type unions.

### Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Classes | PascalCase | `SchemaOrgParser` |
| Methods / functions | snake_case | `_parse_entity` |
| Private helpers | leading underscore | `_normalize_date` |
| Module-level constants | UPPER_SNAKE | `IDENTIFIER_PATTERNS` |
| Branch names | `type/short-description` | `feat/grant-entity-support` |

### Error Handling

- Raise specific exceptions, not bare `Exception`.
- In `parser.py`, raise `ValueError` for malformed JSON-LD input.
- In `rocrate_builder.py`, raise `RuntimeError` for unrecoverable build errors.
- CLI entry points (`main.py`, scripts) catch exceptions and print to `stderr` then `sys.exit(1)`.
- Replace bare `print()` debug statements with Python `logging` (see tech debt section).

---

## Testing

### Current State

`tests/` contains manual debug scripts (`check_xlsx.py`, `inspect_investigation.py`, `list_projects.py`). There is **no pytest suite yet**. This is tracked as tech debt.

### Running Existing Debug Scripts

```bash
uv run python tests/check_xlsx.py path/to/file.xlsx
uv run python tests/inspect_investigation.py path/to/isa.investigation.xlsx
```

### Adding New Tests

When creating or modifying any feature, **always add a pytest test** in `tests/`. Create the file if it doesn't exist:

```
tests/
├── conftest.py              # shared fixtures (create this)
├── test_parser.py           # unit tests for SchemaOrgParser
├── test_rocrate_builder.py  # unit tests for ISAROCrateBuilder
└── test_integration.py      # end-to-end using examples/ inputs
```

**Minimum test requirements per PR/branch**:
- Parser: one test per new entity type or parsing path added.
- Builder: one test per new property mapping.
- Integration: at least run all 5 examples/ inputs and assert the output ro-crate-metadata.json is valid JSON and contains the expected `@id: "./"` root entity.

**Fixture pattern to use** (add to `tests/conftest.py`):

```python
import pytest
from pathlib import Path

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

@pytest.fixture
def edal_json(tmp_path):
    return EXAMPLES_DIR / "example_edal.json"

@pytest.fixture
def bonares_json():
    return EXAMPLES_DIR / "example_bonares.json"
```

**Run tests**:

```bash
uv run pytest tests/ -v
```

---

## Branch Naming & Workflows

### Branch Types

| Prefix | When to use | Example |
|---|---|---|
| `feat/` | Adding new functionality | `feat/grant-entity-support` |
| `fix/` | Fixing a bug or incorrect behavior | `fix/duplicate-person-dedup` |
| `refactor/` | Restructuring without changing behavior | `refactor/move-imports-to-top` |
| `improve/` | Non-breaking enhancements (perf, UX, DX) | `improve/add-logging-framework` |
| `test/` | Adding or fixing tests only | `test/parser-unit-suite` |
| `docs/` | Documentation only | `docs/update-readme-examples` |
| `chore/` | Tooling, CI, config, dependencies | `chore/add-github-actions-ci` |

### Commit Message Format

```
<type>(<scope>): <short summary>

<optional body>

<optional footer: "Fixes #N" or "Closes #N">
```

Types: `feat`, `fix`, `refactor`, `improve`, `test`, `docs`, `chore`.  
Scopes: `parser`, `builder`, `arc`, `gitlab`, `cli`, `tests`, `ci`.

Example:
```
feat(parser): add Grant entity support for funding field

Parses schema:Grant objects from 'funding' property and emits them
as normalized dicts in a new 'grants' key in the parsed_data output.

Closes #12
```

---

## Feature Workflows

### Adding a New Entity Type

Goal: e.g. support `schema:Grant`, `schema:Event`, `schema:SoftwareApplication`.

1. **Branch**: `feat/<entity-name>-support`
2. **Parser** (`parser.py`):
   - Add a new key to the `entities` dict in `_parse_graph` (e.g. `'grants': []`).
   - Add a type-check branch in `_parse_graph` routing to the new key.
   - Add a `_parse_<entity>(self, entity: Dict) -> Dict` private method following the `_parse_person` / `_parse_organization` pattern.
3. **Builder** (`rocrate_builder.py`):
   - Add an `_add_<entity>(self, data: Dict) -> Optional[Dict]` method.
   - Call it from `build_from_parsed_data` for the new key.
4. **Tests**: add `test_parser.py::test_parse_<entity>` and `test_rocrate_builder.py::test_add_<entity>`.
5. **Example**: add an `examples/example_with_<entity>.json` if a real-world example exists.

### Fixing an Issue / Bug

1. **Branch**: `fix/<short-description>` — be specific, e.g. `fix/person-id-collision-on-same-name`
2. Write a **failing test first** that reproduces the bug.
3. Implement the fix.
4. Confirm the test passes; confirm all other tests still pass.
5. Document the root cause briefly in the commit body.

### Refactoring

1. **Branch**: `refactor/<scope>`
2. **No behavior changes** — verify with the existing examples: run all 5 examples before and after and diff the output `ro-crate-metadata.json` files. They should be identical.
3. The most urgent refactors (see tech debt) are:
   - `refactor/move-imports-to-top` — move all inline imports in `rocrate_builder.py` to module level.
   - `refactor/logging-replace-print` — replace all `print()` calls with `logging`.
   - `refactor/entity-resolver` — implement `@id` reference resolution in `_parse_graph`.
4. Add or update docstrings if the refactor touches public API.

### Improving the Project

1. **Branch**: `improve/<scope>`
2. Examples of improvements:
   - `improve/cli-entry-point` — add `[project.scripts]` to `pyproject.toml` so `schemaorg-rocrate-parser` works as a shell command.
   - `improve/validation-layer` — add JSON-LD schema validation before parsing.
   - `improve/batch-processing` — support a directory or glob of JSON-LD files as input.

---

## Known Issues & Technical Debt

These are real problems identified in the current codebase. Any agent may address them, each as its own focused branch.

### TD-3: Duplicate person detection (`fix/duplicate-person-dedup`)

**File**: `parser.py`.  
**Problem**: `example_edal.json` contains the same person twice (same name, different address format). The parser creates two separate Person entities with slightly different synthetic IDs.  
**Fix**: Add deduplication logic in `_parse_person` — before generating a synthetic ID, check `self.all_persons` for an existing entry with the same `givenName` + `familyName` combination and merge rather than duplicate.

---

## Design Patterns to Follow

### Entity Registry Pattern (already in place — extend it)

Both `SchemaOrgParser` (`self.all_persons`, `self.all_organizations`) and `ISAROCrateBuilder` (`self.added_entities`) maintain in-memory registries keyed by `@id`. When adding support for a new entity type (e.g. Grant), follow this pattern:

```python
# In __init__:
self.all_grants: Dict[str, Dict] = {}

# In _parse_grant:
self.all_grants[grant_id] = parsed
return parsed
```

### Normalize Then Build (two-phase pattern)

The `SchemaOrgParser` normalizes messy real-world JSON-LD into a clean, predictable dict structure. The `ISAROCrateBuilder` then consumes that clean structure. **Never parse raw JSON-LD in the builder**. If the builder needs something the parser doesn't currently produce, add it to the parser first.

### Defensive `_extract_first_value`

The builder's `_extract_first_value` handles the common case where a property can be a single value or a list. Apply it consistently for any property that Schema.org allows to be multi-valued (name, description, identifier, etc.).

### `_sanitize_identifier` for ARCtrl

ARCtrl identifiers allow only `[a-zA-Z0-9_\- ]`. Always pass identifiers through `_sanitize_identifier` before using them as ARC study/assay IDs. Do not inline this logic elsewhere.

---

## Extending the Parser

### Adding a New Schema.org Type

Checklist for adding, e.g., `schema:Event`:

- [ ] Add `'events': []` to the `entities` dict in `_parse_graph`.
- [ ] Add `elif 'Event' in entity_type: entities['events'].append(parsed)` in the routing block.
- [ ] Add `_parse_event(self, entity: Dict) -> Dict` following the established method pattern.
- [ ] Export the new key from `__init__.py` if needed.
- [ ] Add `_add_event` in `rocrate_builder.py` and call it from `build_from_parsed_data`.
- [ ] Add `examples/example_with_event.json` (real or synthetic).
- [ ] Add tests.

### Adding a New Source Repository

When the tool needs to support a new institutional repository (e.g. Zenodo, DataCite):

1. Add a representative example JSON-LD to `examples/example_<source>.json`.
2. Run the parser against it and inspect the output.
3. If new Schema.org properties appear that aren't handled, add them following the existing patterns (date normalization, identifier normalization, etc.).
4. Add an output to `output_crates/<source>_arc/` by running the full pipeline.
5. Add integration tests for the new source.

---

## Out-of-Scope for Agents

Do not do these unless explicitly requested by the human:

- **Do not change the `examples/` JSON-LD files** — they are real-world samples from production repositories.
- **Do not delete or overwrite `output_crates/`** — these committed outputs serve as regression baselines.
- **Do not add dependencies** without checking they are compatible with Python >= 3.13 and discussing the addition.
- **Do not change the public API** of `SchemaOrgParser` or `ISAROCrateBuilder` (`parse`, `parse_file`, `build_from_parsed_data`, `save`, `to_json`) without versioning the change in `pyproject.toml`.
- **Do not hardcode GitLab URLs or tokens** anywhere in the source — always read from environment variables via `python-dotenv`.