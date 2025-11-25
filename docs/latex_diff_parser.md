# LaTeX Diff Parser

Compares two LaTeX files and generates a color-coded diff document.

**Key Features:**

- **Visual Diff Generation**: Creates a LaTeX document highlighting differences
- **Color-Coded Output**:
  - 🔴 **Red**: Content removed from first file
  - 🔵 **Blue**: Content added in second file
  - ⚫ **Black**: Unchanged content
- **Two Diff Modes**:
  - **Line-level diff**: Shows entire lines as added/removed
  - **Inline diff**: Shows word-level changes within similar lines
- **LaTeX-Aware**: Uses `lstlisting` environment to preserve LaTeX formatting
- **Compilable Output**: Generates valid LaTeX document ready to compile

**Usage:**

```python
from latex_diff_parser import LatexDiffParser

# Create line-level diff
parser = LatexDiffParser('old_version.tex', 'new_version.tex', 'diff_output.tex')
parser.create_diff_document()

# Create inline word-level diff
from latex_diff_parser import LatexInlineDiffParser
inline_parser = LatexInlineDiffParser('old.tex', 'new.tex', 'inline_diff.tex')
inline_parser.create_diff_document()

# Compile the diff document
# pdflatex diff_output.tex
```

**Diff Modes:**

1. **LatexDiffParser**: Line-by-line comparison
   - Shows complete lines as added or removed
   - Uses `\textcolor{red}` and `\textcolor{blue}` for changes
   - Best for significant structural changes

2. **LatexInlineDiffParser**: Word-level comparison
   - Shows changes within lines
   - Uses `\odiff{}` (red strikethrough) for deletions
   - Uses `\ndiff{}` (green) for additions
   - Better for minor edits and fine-grained changes

**Output:**

- Generates a standalone LaTeX document with:
  - Required packages (`xcolor`, `listings`, `soul`, `ulem`)
  - Color legend explaining the diff markers
  - Formatted diff content
  - Compilation instructions

---

## Installation

### Recommended: Install with pipx

```bash
# Install with pipx (isolated environment, system-wide commands)
pipx install git+https://github.com/iheitlager/latex-tools.git

# The commands are now available globally
latex-processor --help
doi-validator --help
latex-diff --help
```

### Alternative: Install with pip

```bash
# Install directly from GitHub (latest version)
python3 -m pip install git+https://github.com/iheitlager/latex-tools.git

# Or install from a specific release
python3 -m pip install https://github.com/iheitlager/latex-tools/releases/latest/download/latex_tools-0.2.0-py3-none-any.whl
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/iheitlager/latex-tools.git
cd latex-tools

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Or using uv (recommended)
uv sync
```

For more installation options, see [INSTALL.md](INSTALL.md)

## Requirements

- Python 3.11+
- Standard library only (no external dependencies required)

## License

Copyright (c) 2025 - Ilja Heitlager  
SPDX-License-Identifier: Apache-2.0

---

## Common Workflows

### Consolidate a multi-file LaTeX project

```bash
python latex_processor.py thesis.tex -o thesis_single.tex --verbose
```

### Validate DOIs in your bibliography

```bash
python doi_validator.py references.bib --verbose
```

### Create a clean BibTeX file with only cited references

```bash
python latex_processor.py paper.tex --bibtex -o paper_refs.bib
```

### Compare two versions of a document

```python
from latex_diff_parser import LatexInlineDiffParser
parser = LatexInlineDiffParser('draft_v1.tex', 'draft_v2.tex', 'changes.tex')
parser.create_diff_document()
```

### Find problematic labels and references

```bash
python latex_processor.py document.tex -o output.tex --verbose
# Check output for warnings about:
# - Duplicate labels
# - Undefined references
# - Unused labels
# - Missing captions
```