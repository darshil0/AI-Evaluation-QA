# AI Evaluation QA Framework - Issue Audit & Fixes

**Date**: 2026-06-02  
**Framework Version**: 2.3.8  
**Auditor**: Darshil Standard Analysis  

---

## Executive Summary

**Status**: 🔴 **Critical Issues Found: 11**

The codebase contains **version conflicts**, **package discovery mismatches**, **broken documentation links**, and **inconsistent dependency specifications** that would cause installation failures, import errors, and deployment issues in production.

**Impact**: 
- Installation may fail or succeed with incompatible versions
- Runtime ImportError on module load
- Documentation links broken for contributors
- CI/CD pipelines vulnerable to version-specific bugs

---

## Issue Audit with Given/When/Then Format

### Issue #1: Version Mismatch in OpenAI Dependency

**Severity**: 🔴 CRITICAL  
**Component**: `setup.py`, `pyproject.toml`, `requirements.txt`

**Given**: Three configuration files define OpenAI version
**When**: User installs via `pip install -e .` or `pip install .`
**Then**: May install incompatible versions (2.40.0 vs 1.60.0)

**Root Cause**:
```
setup.py:         openai>=2.40.0  ❌ (newest)
pyproject.toml:   openai>=2.40.0  ❌ (newest)
requirements.txt: openai>=1.60.0  ✓ (stable)
```

**Risk**: Major version mismatch (1.x → 2.x) is a breaking change. API signatures differ.

**Fix Applied**: Unified to `openai>=1.60.0` across all three files
```python
# Before (setup.py)
"openai>=2.40.0",

# After (setup.py)
"openai>=1.60.0",
```

---

### Issue #2: Matplotlib Version Conflict

**Severity**: 🟠 MEDIUM  
**Component**: `setup.py`, `requirements.txt`

**Given**: Inconsistent matplotlib versions specified
**When**: `pip install -e .` is run
**Then**: May install 3.10.9 instead of 3.10.0

**Details**:
```
setup.py:         matplotlib>=3.10.9  ❌
requirements.txt: matplotlib>=3.10.0  ✓
```

**Fix Applied**: Unified to `matplotlib>=3.10.0`

---

### Issue #3: Plotly Version Incompatibility

**Severity**: 🟠 MEDIUM  
**Component**: `setup.py`, `requirements.txt`

**Given**: Major version difference (6.7.0 vs 5.24.0)
**When**: Pipeline generates reports
**Then**: May encounter API changes or missing methods

**Details**:
```
setup.py:         plotly>=6.7.0   ❌ (major jump)
requirements.txt: plotly>=5.24.0  ✓ (stable)
```

**Fix Applied**: Unified to `plotly>=5.24.0`

---

### Issue #4: Click Library Version Mismatch

**Severity**: 🟡 LOW  
**Component**: `setup.py`, `requirements.txt`, `pyproject.toml`

**Given**: CLI built on Click with inconsistent versions
**When**: CLI commands are invoked
**Then**: May fail if parameter decorators differ

**Details**:
```
setup.py:         click>=8.4.1   ❌
pyproject.toml:   click>=8.4.1   ❌
requirements.txt: click>=8.1.0   ✓
```

**Fix Applied**: Unified to `click>=8.1.0`

---

### Issue #5: Package Discovery Mismatch

**Severity**: 🔴 CRITICAL  
**Component**: `setup.py` vs `pyproject.toml`

**Given**: Package configuration files define different discovery strategies
**When**: `pip install -e .` executes
**Then**: `scripts/` package may not be included in installation

**Root Cause**:
```
pyproject.toml:
    include = ["evaluation*", "config*", "scripts*"]  ✓

setup.py:
    exclude = ["tests*", "docs", "scripts", "examples"]  ❌
    # EXCLUDES scripts!
```

**Fix Applied**: Both files now include `scripts/`:
```python
# pyproject.toml
packages = ["evaluation", "config", "scripts"]
include = ["evaluation*", "config*", "scripts*"]

# setup.py
packages = find_packages(
    exclude=["tests*", "docs*", "examples*"]  # Does NOT exclude scripts
)
```

---

### Issue #6: Broken Documentation Links

**Severity**: 🟠 MEDIUM  
**Component**: `README.md`

**Given**: README references CONTRIBUTING.md and LICENSE
**When**: User clicks links
**Then**: Points to Google search instead of actual files

**Root Cause**:
```markdown
# BEFORE (❌ broken)
[CONTRIBUTING.md](https://www.google.com/search?q=CONTRIBUTING.md)
[LICENSE](https://www.google.com/search?q=LICENSE)

# AFTER (✓ fixed)
[CONTRIBUTING.md](CONTRIBUTING.md)
[LICENSE](LICENSE)
```

**Fix Applied**: Direct relative links to actual files

---

### Issue #7: Improper Dependency Version Pinning

**Severity**: 🟠 MEDIUM  
**Component**: `setup.py` path parsing

**Given**: Long description reads with custom `__import__` pattern
**When**: `setup.py` is executed
**Then**: Unnecessarily convoluted, harder to maintain

**Root Cause**:
```python
# BEFORE (❌ awkward)
open("README.md", encoding="utf-8").read()
if __import__("pathlib").Path("README.md").exists()
else ""

# AFTER (✓ clean)
from pathlib import Path
readme_path = Path("README.md")
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
```

**Fix Applied**: Modern `pathlib` import at top of setup.py

---

### Issue #8: Missing Import Error Handling in main.py

**Severity**: 🔴 CRITICAL  
**Component**: `main.py`

**Given**: Top-level imports from `config.config_loader`
**When**: Installation is incomplete or partial
**Then**: CLI crashes immediately without helpful error message

**Root Cause**:
```python
# BEFORE (❌ no error handling)
from config.config_loader import ConfigLoader  # Crashes silently

# AFTER (✓ with error handling)
try:
    from config.config_loader import ConfigLoader
except ImportError as e:
    logger.error(f"Failed to import ConfigLoader: {e}")
    logger.error("Please ensure config package is installed...")
    sys.exit(1)
```

**Fix Applied**: All imports wrapped in try-except with helpful messages

---

### Issue #9: Inconsistent Scipy Version

**Severity**: 🟡 LOW  
**Component**: `setup.py`, `requirements.txt`

**Given**: Different scipy versions
**When**: Data analysis operations run
**Then**: May encounter missing functions or API changes

**Details**:
```
setup.py:         scipy>=1.17.1  ❌
requirements.txt: scipy>=1.14.0  ✓
```

**Fix Applied**: Unified to `scipy>=1.14.0`

---

### Issue #10: Python-dotenv Version Discrepancy

**Severity**: 🟡 LOW  
**Component**: `setup.py`, `pyproject.toml`, `requirements.txt`

**Given**: Three different pinned versions
**When**: Environment variables are loaded
**Then**: May miss .env parsing features

**Details**:
```
setup.py:         python-dotenv>=1.2.2  ❌
pyproject.toml:   python-dotenv>=1.2.2  ❌
requirements.txt: python-dotenv>=1.0.0  ✓
```

**Fix Applied**: Unified to `python-dotenv>=1.0.0`

---

### Issue #11: Missing Pytest Coverage Configuration

**Severity**: 🟡 LOW  
**Component**: `pyproject.toml`, `setup.py`

**Given**: No coverage configuration in pyproject.toml
**When**: `pytest --cov` runs
**Then**: May not exclude test files properly

**Root Cause**: Missing `[tool.coverage.*]` section

**Fix Applied**: Added complete coverage configuration:
```toml
[tool.coverage.run]
branch = true
source = ["evaluation", "config", "scripts"]
omit = ["*/tests/*", "*/test_*.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    ...
]
```

---

## Validation Matrix

| Issue | Component | Before | After | Status |
|-------|-----------|--------|-------|--------|
| #1 - OpenAI | setup.py, pyproject.toml, requirements.txt | 2.40.0 vs 1.60.0 | 1.60.0 unified | ✓ FIXED |
| #2 - Matplotlib | setup.py, requirements.txt | 3.10.9 vs 3.10.0 | 3.10.0 unified | ✓ FIXED |
| #3 - Plotly | setup.py, requirements.txt | 6.7.0 vs 5.24.0 | 5.24.0 unified | ✓ FIXED |
| #4 - Click | setup.py, requirements.txt | 8.4.1 vs 8.1.0 | 8.1.0 unified | ✓ FIXED |
| #5 - Package Discovery | setup.py vs pyproject.toml | scripts excluded | scripts included | ✓ FIXED |
| #6 - README Links | README.md | Google search links | Relative links | ✓ FIXED |
| #7 - setup.py Style | setup.py | Awkward __import__ | Clean pathlib | ✓ FIXED |
| #8 - Import Errors | main.py | No error handling | Try-except added | ✓ FIXED |
| #9 - Scipy Version | setup.py, requirements.txt | 1.17.1 vs 1.14.0 | 1.14.0 unified | ✓ FIXED |
| #10 - python-dotenv | setup.py, pyproject.toml | 1.2.2 vs 1.0.0 | 1.0.0 unified | ✓ FIXED |
| #11 - Coverage Config | pyproject.toml | Missing | Added | ✓ FIXED |

---

## Edge Cases & Risk Mitigation

### Edge Case #1: Existing Virtual Environments
**Problem**: Users with pre-existing venvs have cached old versions  
**Mitigation**: Add installation note to CONTRIBUTING.md:
```bash
pip install --upgrade --force-reinstall -e .[dev]
```

### Edge Case #2: Docker Multi-Stage Builds
**Problem**: Dockerfile may cache old requirements  
**Mitigation**: Ensure Dockerfile uses `--no-cache` or bust cache layer

### Edge Case #3: CI/CD Pinning
**Problem**: GitHub Actions may pin specific version ranges  
**Mitigation**: Update `.github/workflows/` to match unified versions

---

## Testing Validation

**Assumptions**:
- Installation path: `pip install -e .` or `pip install -e .[dev]`
- Python version: 3.9+
- No pre-existing conflicting packages

**Preconditions**:
```bash
python -m venv test_env
source test_env/bin/activate
cd AI-Evaluation-QA
```

**Validation Steps**:
```bash
# Step 1: Install with dev dependencies
pip install -e .[dev]

# Step 2: Verify imports work
python -c "from config.config_loader import ConfigLoader; print('✓ Config loaded')"
python -c "from evaluation.evaluation_pipeline import EvaluationPipeline; print('✓ Pipeline loaded')"
python -c "from scripts.check_regression import RegressionDetector; print('✓ Scripts loaded')"

# Step 3: Verify CLI entry point
ai-eval --version  # Should output: 2.3.8

# Step 4: Run tests
pytest tests/ --cov=evaluation --cov=config --cov-report=term-missing
```

**Expected Result**: All imports succeed, CLI works, tests pass with 100% coverage

---

## Files Modified

1. ✅ **setup.py** - Fixed version pins, package discovery, import style
2. ✅ **pyproject.toml** - Unified versions, added coverage config, corrected package discovery
3. ✅ **main.py** - Added import error handling, improved error messages
4. ✅ **README.md** - Fixed documentation links, improved clarity
5. **requirements.txt** - No changes needed (already correct baseline)
6. **CHANGELOG.md** - No changes needed (already accurate)
7. **CONTRIBUTING.md** - No changes needed (already accurate)
8. **__init__.py** - No changes needed (already correct)

---

## Deployment Checklist

- [ ] Replace old files with fixed versions
- [ ] Run `pip install --upgrade --force-reinstall -e .[dev]`
- [ ] Run full test suite: `pytest tests/ --cov=evaluation --cov=config`
- [ ] Verify CLI: `ai-eval --version`
- [ ] Test evaluate command: `ai-eval evaluate --prompts data/prompts/test.json`
- [ ] Update CI/CD workflows in `.github/workflows/`
- [ ] Update any Dockerfile to match unified versions
- [ ] Commit with message: `fix: resolve dependency conflicts and package discovery issues`

---

## Failure Modes & Mitigation

| Failure Mode | Detection | Recovery |
|---|---|---|
| Installation with old pip cache | `pip list` shows wrong versions | `pip cache purge && pip install -e .[dev]` |
| Partial package installation | `from scripts...` fails ImportError | Run install with dev extras: `-e .[dev]` |
| Broken doc links in CI | Link checker fails | Links now use relative paths |
| Version incompatibility at runtime | API calls fail | All versions unified to stable range |

---

## Post-Fix Verification

**Command**: `make check` or manual steps:

```bash
# 1. Syntax check all Python files
python -m py_compile setup.py main.py

# 2. Lint YAML files
python -m yamllint pyproject.toml 2>/dev/null || echo "Optional: Install yamllint"

# 3. Verify all imports
python -c "import setup; import main"

# 4. Check metadata
grep "version" setup.py pyproject.toml  # Should all show 2.3.8
```

---

## References

- **QA Standard**: Darshil Standard (Given/When/Then, preconditions, validation)
- **Traceability**: All issues mapped to files and fixes
- **Framework**: AI Evaluation QA v2.3.8
- **Python**: 3.9+

---

**Status**: ✅ ALL ISSUES RESOLVED  
**Date Completed**: 2026-06-02  
**Next Steps**: Deploy fixed files, run full test suite, update CI/CD
