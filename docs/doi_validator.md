# DOI Validator

Validates DOIs in BibTeX files for existence and accessibility.

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