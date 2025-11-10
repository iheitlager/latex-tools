# latex-tools

A collection of Python tools for processing, validating, and comparing LaTeX documents. These tools help with common LaTeX workflows including file consolidation, bibliography management, DOI validation, and document comparison.

## Tools Overview

### 1. LaTeX Processor (`latex_processor.py`)

A comprehensive LaTeX document processor that consolidates multi-file projects into a single file, processes bibliographies, and validates labels and references.

**Key Features:**

- **File Inclusion**: Recursively inlines all `\input` and `\include` commands
  - Prevents circular inclusions
  - Handles relative and absolute paths
  - Supports arbitrary nesting depth

- **Bibliography Processing**: 
  - Extracts citation keys from `\cite`, `\citep`, `\citet` commands
  - Parses BibTeX (.bib) files
  - Filters to only cited references
  - Converts to inline `\bibitem` format with APA-style formatting
  - Maintains citation order

- **Label and Reference Tracking**:
  - Detects labels in figures, tables, sections, equations, listings
  - Tracks references (`\ref`, `\eqref`, `\autoref`, `\cref`, `\Cref`)
  - Validates all references are defined
  - Identifies unused labels
  - Detects duplicate labels

- **Caption Analysis**:
  - Associates captions with their labels
  - Detects missing captions in figures and tables
  - Reports caption-label mismatches

- **Dual Output Modes**:
  - **Summary mode** (default): Concise overview with statistics and warnings
  - **Verbose mode**: Detailed reports on labels, references, and validation issues

- **BibTeX Export Mode**:
  - Extract only referenced BibTeX entries from source
  - Automatically outputs to `.bib` file
  - Preserves original BibTeX formatting

**Usage:**

```bash
# Process a LaTeX document (combines all includes, processes bibliography)
python latex_processor.py main.tex -o onefile.tex

# Show detailed verbose output
python latex_processor.py main.tex -o output.tex --verbose

# Extract only cited BibTeX entries
python latex_processor.py main.tex --bibtex -o references.bib

# Alternative using mode flag
python latex_processor.py main.tex --mode bibtex -o references
```

**Command-line Options:**

- `input_file`: Main LaTeX file to process (default: `main.tex`)
- `-o, --output`: Output file path (default: `onefile.tex`)
- `-v, --verbose`: Show detailed reports including all labels, references, and validation
- `-m, --mode`: Processing mode: `all` (default) or `bibtex`
- `-b, --bibtex`: Shortcut for `--mode bibtex` (extract only referenced BibTeX entries)

**Output Summary:**

The processor provides clear feedback on:
- Number of files processed
- Citation count
- Label and reference statistics
- ⚠️ Warnings for:
  - Duplicate labels
  - Undefined references
  - Unused labels
  - Missing captions

---

### 2. DOI Validator (`doi_validator.py`)

Validates whether DOIs mentioned in BibTeX files actually exist and are accessible. Uses intelligent caching to avoid redundant checks and rate limiting.

**Key Features:**

- **DOI Validation**: Checks if DOIs resolve using the official doi.org resolver
- **Smart Caching**: Stores validation results for 30 days to avoid redundant checks
- **Status Granularity**:
  - ✅ **Confirmed**: DOI fully accessible (HTTP 200)
  - 🔗 **Validated**: DOI resolves with access restriction (HTTP 401/403)
  - ✔️ **Exists**: DOI resolves but target inaccessible (404 or unreachable)
  - 💾 **Cached**: Result loaded from cache
  - ❌ **NonExists**: DOI does not exist (HTTP 404 at resolver)
  - ⚠️ **Error**: Connection or validation error
- **Rate Limiting**: Optional limit on uncached entries to check (respects API usage)
- **Flexible Parsing**: Handles escaped characters, nested braces, and various BibTeX formats
- **Cache Management**: Clear cache on demand or let it auto-expire

**Usage:**

```bash
# Validate all DOIs in a BibTeX file
python doi_validator.py references.bib

# Verbose output with detailed status for each DOI
python doi_validator.py references.bib --verbose

# Limit checking to first 10 uncached entries
python doi_validator.py references.bib --limit 10

# Clear the cache before validating
python doi_validator.py references.bib --clear-cache

# Use custom timeout (default: 5 seconds)
python doi_validator.py references.bib --timeout 10

# Use custom user agent
python doi_validator.py references.bib --user-agent "MyApp/1.0"
```

**Command-line Options:**

- `bib_file`: Path to the BibTeX file to validate
- `-t, --timeout`: HTTP request timeout in seconds (default: 5)
- `-v, --verbose`: Show detailed validation information for each DOI
- `-u, --user-agent`: Custom user agent string for HTTP requests
- `-l, --limit`: Limit validation to first N uncached entries
- `--clear-cache`: Clear the validation cache before running

**Output:**

The validator provides:
- Count of entries with DOIs
- Validation status for each DOI with visual indicators
- Summary statistics of validation results
- Cache file location (`~/.bib_validator`)

**Cache Behavior:**

- Cached results are valid for 30 days
- Cache persists at `~/.bib_validator` in your home directory
- Prevents redundant network requests for previously validated DOIs
- Can be cleared manually with `--clear-cache` flag

---

### 3. LaTeX Diff Parser (`latex_diff_parser.py`)

Compares two LaTeX files and creates a color-coded diff document showing changes between versions.

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

```bash
# Clone the repository
git clone https://github.com/iheitlager/latex-tools.git
cd latex-tools

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (if any)
pip install -r requirements.txt  # if requirements file exists
```

## Requirements

- Python 3.8+
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
