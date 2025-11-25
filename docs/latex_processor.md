# LaTeX Processor

A comprehensive tool for consolidating, validating, and exporting LaTeX documents.

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
