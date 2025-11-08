#!/usr/bin/env python3
"""
DOI Validator for BibTeX Files
Validates whether DOIs mentioned in a BibTeX file actually exist.

VALIDATION STATUS MEANINGS:
    ✔️ Exists       - DOI resolves but target is inaccessible (404 or unreachable)
    🔗 Validated    - DOI resolves with access restriction (HTTP 401/403)
    ✅ Confirmed    - DOI fully validated with accessible target (HTTP 200)
    💾 Cached       - Result loaded from cache (within 30 days)
    ❌ NonExists    - DOI does not exist (HTTP 404 at resolver)
    ⚠️ Error        - Connection or validation error occurred

Copyright (c) 2025 - Ilja Heitlager
SPDX-License-Identifier: Apache-2.0
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Tuple
import urllib.request
import urllib.error


class DOIStatus(Enum):
    """Enum for DOI validation status"""
    Exists = "Exists"
    Validated = "Validated"  # DOI resolves, target accessible (401/403 - access restricted)
    Confirmed = "Confirmed"  # DOI resolves, target fully accessible (200)
    Cached = "Cached"
    NonExists = "NonExists"
    Internal_Error = "Internal_Error"


class DOICache:
    """Manages caching of DOI validation results"""
    
    CACHE_FILE = Path.home() / '.bib_validator'
    CACHE_VALIDITY_DAYS = 30
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.cache: Dict = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cache from file"""
        if self.CACHE_FILE.exists():
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                if self.verbose:
                    print(f"Warning: Could not load cache: {e}")
                return {}
        return {}
    
    def _save_cache(self) -> None:
        """Save cache to file"""
        try:
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")
    
    def is_valid(self, doi: str) -> bool:
        """Check if cached DOI result is still valid (within 30 days)"""
        if doi not in self.cache:
            return False
        
        cached_entry = self.cache[doi]
        if 'timestamp' not in cached_entry:
            return False
        
        try:
            cached_date = datetime.fromisoformat(cached_entry['timestamp'])
            if datetime.now() - cached_date < timedelta(days=self.CACHE_VALIDITY_DAYS):
                return True
        except Exception:
            pass
        
        return False
    
    def is_doi_valid(self, doi: str) -> Optional[bool]:
        """Check if a DOI is valid based on its cached status
        
        Returns:
            True if status is 'Validated' or 'Exists'
            False if status is 'NonExists'
            None if DOI not in cache or status unknown
        """
        status = self.get_status(doi)
        if status in ("Validated", "Exists"):
            return True
        elif status == "NonExists":
            return False
        return None
    
    def get(self, doi: str) -> Optional[bool]:
        """Get cached validation result for a DOI"""
        if doi in self.cache and 'is_valid' in self.cache[doi]:
            return self.cache[doi]['is_valid']
        return None
    
    def get_status(self, doi: str) -> Optional[str]:
        """Get cached validation status for a DOI (Exists, Validated, NonExists)"""
        if doi in self.cache and 'status' in self.cache[doi]:
            return self.cache[doi]['status']
        return None
    
    def set(self, doi: str, is_valid: bool) -> None:
        """Cache a validation result"""
        self.cache[doi] = {
            'is_valid': is_valid,
            'timestamp': datetime.now().isoformat()
        }
        self._save_cache()
    
    def set_status(self, doi: str, status: str) -> None:
        """Cache a validation status (Exists, Validated, NonExists)"""
        self.cache[doi] = {
            'is_valid': status != "NonExists",  # Maintain backward compatibility
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        self._save_cache()
    
    def clear(self) -> None:
        """Clear the cache"""
        if self.CACHE_FILE.exists():
            self.CACHE_FILE.unlink()
            self.cache = {}


class DOIValidator:
    def __init__(self, bib_file: str, timeout: int = 5, verbose: bool = False, user_agent: str = None, limit: int = None):
        self.bib_file = Path(bib_file)
        self.timeout = timeout
        self.verbose = verbose
        self.limit = limit  # Limit to first N uncached entries
        # Default to full Chrome browser user-agent
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.entries: Dict[str, Dict[str, str]] = {}
        self.doi_results: Dict[str, Tuple[str, DOIStatus]] = {}  # key -> (doi, status)
        self.cache = DOICache(verbose=verbose)
        
    def validate(self) -> None:
        """Main validation function"""
        if not self.bib_file.exists():
            print(f"Error: BibTeX file not found: {self.bib_file}")
            sys.exit(1)
        
        print(f"Loading BibTeX file: {self.bib_file}")
        self._parse_bib_file()
        
        total_entries = len(self._count_all_bib_entries())
        entries_with_doi = len(self.entries)
        print(f"Total references in bibliography: {total_entries}")
        print(f"References with DOI: {entries_with_doi}")
        
        print("Validating DOIs...")
        try:
            self._validate_dois()
            self._print_report()
        except KeyboardInterrupt:
            print("\n\n⏸️  Validation interrupted by user (CTRL-C)")
            if self.doi_results:
                print(f"Partial results: {len(self.doi_results)} entries checked before interruption")
                self._print_partial_report()
            sys.exit(0)
    
    def _parse_bib_file(self) -> None:
        """Parse the BibTeX file and extract entries with DOIs"""
        try:
            with open(self.bib_file, 'r', encoding='utf-8') as f:
                bib_content = f.read()
        except UnicodeDecodeError:
            with open(self.bib_file, 'r', encoding='latin-1') as f:
                bib_content = f.read()
    
        return self._parse_bib_entries(bib_content)

    def _parse_bib_entries(self, bib_content: str) -> None:
        """Parse BibTeX entries and extract DOIs"""
        # Pattern to match BibTeX entries
        entry_pattern = r'@(\w+)\s*\{\s*([^,\s]+)\s*,\s*(.*?)\n\s*\}'
        
        for match in re.finditer(entry_pattern, bib_content, re.DOTALL):
            entry_type = match.group(1).lower()
            key = match.group(2)
            fields_str = match.group(3)
            
            # Parse DOI field - use a more sophisticated pattern to handle nested braces
            # Match doi = { ... } handling nested braces
            doi_match = re.search(r'doi\s*=\s*\{((?:[^{}]|(?:\{[^}]*\}))*)\}', fields_str, re.IGNORECASE)
            if doi_match:
                doi = doi_match.group(1).strip()
                # Clean up DOI - remove escaped characters and braces
                # Handle patterns like {\_}, {\\_}, \_, and remove remaining braces
                doi = re.sub(r'\{\\_\}', '_', doi)  # {\_} -> _
                doi = re.sub(r'\{_\}', '_', doi)    # {_} -> _
                doi = re.sub(r'\\_', '_', doi)      # \_ -> _
                doi = re.sub(r'[{}]', '', doi)      # Remove any remaining braces
                self.entries[key] = {'doi': doi, 'entry_type': entry_type}
    
    def _count_all_bib_entries(self) -> Dict[str, str]:
        """Count all BibTeX entries in the file"""
        try:
            with open(self.bib_file, 'r', encoding='utf-8') as f:
                bib_content = f.read()
        except UnicodeDecodeError:
            with open(self.bib_file, 'r', encoding='latin-1') as f:
                bib_content = f.read()
        
        # Pattern to match BibTeX entries
        entry_pattern = r'@(\w+)\s*\{\s*([^,\s]+)\s*,\s*(.*?)\n\s*\}'
        entries = {}
        
        for match in re.finditer(entry_pattern, bib_content, re.DOTALL):
            key = match.group(2)
            entries[key] = match.group(1)
        
        return entries
    
    def _validate_dois(self) -> None:
        """Validate each DOI by checking if it resolves"""
        entries_with_doi = len(self.entries)
        
        print(f"Found {entries_with_doi} entries with DOI in bibliography")
        
        uncached_count = 0
        for i, (key, entry) in enumerate(self.entries.items(), 1):
            doi = entry['doi']
            
            # Check cache first - if valid, use it without external check
            if self.cache.is_valid(doi):
                cached_status = self.cache.get_status(doi)
                if self.verbose:
                    print(f"    [VERBOSE] Using cached result for {doi}: {cached_status}")
                status = DOIStatus.Cached
            # Check if we've reached the limit for uncached entries
            elif self.limit is not None:
                uncached_count += 1
                if uncached_count > self.limit:
                    # No cache available and limit reached, skip
                    if self.verbose:
                        print(f"  [{i}/{entries_with_doi}] ⏭️ {key} (limit reached, no cache)")
                    continue
                else:
                    status = self._check_doi(doi, key)
            else:
                status = self._check_doi(doi, key)
            
            self.doi_results[key] = (doi, status)
            
            # Map status to emoji
            status_emoji = {
                DOIStatus.Exists: "✔️",
                DOIStatus.Validated: "🔗",
                DOIStatus.Confirmed: "✅",
                DOIStatus.Cached: "💾",
                DOIStatus.NonExists: "❌",
                DOIStatus.Internal_Error: "⚠️"
            }
            
            # Print in multi-line format when verbose
            print(f"  [{i}/{entries_with_doi}] {status_emoji[status]} {key}")
            if self.verbose:
                print(f"      → https://doi.org/{doi}")
            
            # Add small delay to be respectful to DOI resolver (only for external checks)
            if status != DOIStatus.Cached and i < entries_with_doi:
                time.sleep(0.5)
    
    def _check_doi(self, doi: str, key: str) -> DOIStatus:
        """Check if a DOI resolves (assumes cache has already been checked)"""
        # Construct the DOI URL
        doi_url = f"https://doi.org/{doi}"
        
        try:
            # First, check if DOI exists WITHOUT following redirects
            redirect_url = self._check_redirect(doi_url)
            
            if redirect_url is None:
                # No redirect detected, DOI doesn't exist
                self.cache.set_status(doi, "NonExists")
                return DOIStatus.NonExists
            
            # DOI exists (we got a redirect)
            if self.verbose:
                print(f"    [VERBOSE] DOI redirects to: {redirect_url}")
            
            # Now validate the redirect target if it's not a placeholder
            if redirect_url != "access_restricted":
                validation_status = self._validate_redirect_target(redirect_url)
                if self.verbose:
                    print(f"    [VERBOSE] Redirect target validation: {validation_status}")
                if validation_status is not None:
                    # Redirect target is accessible
                    if validation_status == 200:
                        # Fully accessible (200) - mark as Confirmed
                        self.cache.set_status(doi, "Confirmed")
                        return DOIStatus.Confirmed
                    else:
                        # Access restricted (401/403) but exists - mark as Validated
                        self.cache.set_status(doi, "Validated")
                        return DOIStatus.Validated
                else:
                    # Redirect target is not accessible (404, error) - only mark as Exists
                    self.cache.set_status(doi, "Exists")
                    return DOIStatus.Exists
            else:
                # Access restricted placeholder - DOI exists but can't verify target
                self.cache.set_status(doi, "Exists")
                return DOIStatus.Exists
        
        except urllib.error.URLError:
            # Network error - can't validate
            print(f"    Warning: Connection error for {key}")
            return DOIStatus.Internal_Error
        except Exception as e:
            # Unexpected error
            print(f"    Warning: Unexpected error for {key}: {type(e).__name__}")
            return DOIStatus.Internal_Error
    
    def _check_redirect(self, doi_url: str) -> Optional[str]:
        """
        Check if DOI resolves by catching redirect before following it.
        Returns the redirect URL if DOI exists, None if it returns 404.
        """
        try:
            # Create a custom handler that doesn't follow redirects
            class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
                def http_error_301(self, req, fp, code, msg, hdrs):
                    return None  # Stop redirect processing
                
                def http_error_302(self, req, fp, code, msg, hdrs):
                    return None
                
                def http_error_303(self, req, fp, code, msg, hdrs):
                    return None
                
                def http_error_307(self, req, fp, code, msg, hdrs):
                    return None
            
            opener = urllib.request.build_opener(NoRedirectHandler)
            request = urllib.request.Request(
                doi_url,
                headers={'User-Agent': self.user_agent}
            )
            
            opener.open(request, timeout=self.timeout)
            # If we get here without exception, it's a 2xx response (unlikely but possible)
            return None
            
        except urllib.error.HTTPError as e:
            # 3xx redirects are what we expect
            if e.code in (301, 302, 303, 307, 308):
                # Get the Location header which tells us where it redirects to
                redirect_url = e.headers.get('Location')
                if self.verbose:
                    print(f"    [VERBOSE] HTTP {e.code} redirect to: {redirect_url}")
                return redirect_url
            # 404 means DOI doesn't exist
            elif e.code == 404:
                return None
            # 403/401 means access restricted but DOI exists
            elif e.code in (401, 403):
                if self.verbose:
                    print(f"    [VERBOSE] HTTP {e.code} (access restricted but DOI likely exists)")
                return "access_restricted"  # Placeholder to indicate it exists
            else:
                # Other errors (5xx, etc.)
                print(f"    Warning: HTTP {e.code} checking redirect")
                raise
                
        except (urllib.error.URLError, Exception) as e:
            # Network error
            print(f"    Warning: Connection error: {type(e).__name__}")
            raise
    
    def _validate_redirect_target(self, redirect_url: str) -> Optional[int]:
        """
        Validate the redirect target to ensure it's accessible.
        Returns HTTP status code if accessible (200, 401, 403), None if not accessible or error.
        """
        try:
            request = urllib.request.Request(
                redirect_url,
                headers={'User-Agent': self.user_agent}
            )
            
            with urllib.request.urlopen(request, timeout=self.timeout):
                # If we get here, it's a 2xx response
                return 200
                
        except urllib.error.HTTPError as e:
            # 401/403 means access restricted but content exists
            if e.code in (401, 403):
                if self.verbose:
                    print(f"    [VERBOSE] Redirect target returned HTTP {e.code} (access restricted)")
                return e.code
            # 404 means the redirect target doesn't exist
            elif e.code == 404:
                if self.verbose:
                    print("    [VERBOSE] Redirect target returned 404 (not found)")
                return None
            else:
                # Other errors, assume it exists
                return e.code
                
        except (urllib.error.URLError, Exception) as e:
            # Network error, can't validate
            if self.verbose:
                print(f"    [VERBOSE] Connection error validating redirect target: {type(e).__name__}")
            return None
    
    
    def _print_report(self) -> None:
        """Print a summary report"""
        total_checked = len(self.doi_results)
        exists_dois = sum(1 for _, status in self.doi_results.values() if status == DOIStatus.Exists)
        validated_dois = sum(1 for _, status in self.doi_results.values() if status == DOIStatus.Validated)
        confirmed_dois = sum(1 for _, status in self.doi_results.values() if status == DOIStatus.Confirmed)
        cached_dois = sum(1 for _, status in self.doi_results.values() if status == DOIStatus.Cached)
        nonexists_dois = sum(1 for _, status in self.doi_results.values() if status == DOIStatus.NonExists)
        error_dois = sum(1 for _, status in self.doi_results.values() if status == DOIStatus.Internal_Error)
        
        # Collect problematic entries
        nonexists_keys = [
            key for key, (doi, status) in self.doi_results.items()
            if status == DOIStatus.NonExists
        ]
        
        error_keys = [
            key for key, (doi, status) in self.doi_results.items()
            if status == DOIStatus.Internal_Error
        ]
        
        # Print invalid entries first
        if nonexists_keys:
            print("\n" + "="*70)
            print("NON-EXISTENT DOIs:")
            print("="*70)
            for key in sorted(nonexists_keys):
                doi, _ = self.doi_results[key]
                print(f"  ❌ {key}")
                if self.verbose:
                    print(f"      → https://doi.org/{doi}")
        
        # Print error entries
        if error_keys:
            print("\n" + "="*70)
            print("DOIs WITH ERRORS (connection issues):")
            print("="*70)
            for key in sorted(error_keys):
                doi, _ = self.doi_results[key]
                print(f"  ⚠️ {key}")
                if self.verbose:
                    print(f"      → https://doi.org/{doi}")
        
        # Print summary at the end
        print("\n" + "="*70)
        print("DOI VALIDATION SUMMARY")
        print("="*70)
        total_entries = len(self._count_all_bib_entries())
        print(f"Total references in bibliography: {total_entries}")
        print(f"References with DOI:             {total_checked}")
        print(f"Valid (Exists):                  {exists_dois}")
        print(f"Valid (Validated - 401/403):     {validated_dois}")
        print(f"Valid (Confirmed - 200):         {confirmed_dois}")
        print(f"Valid (Cached):                  {cached_dois}")
        print(f"Non-existent DOIs:               {nonexists_dois}")
        print(f"Errors:                          {error_dois}")
        print("="*70)
        
        if not nonexists_keys and not error_keys:
            print("\n✅ All DOIs validated successfully!")
        
        print("="*70)
    
    def _print_partial_report(self) -> None:
        """Print a partial report when validation is interrupted"""
        total_checked = len(self.doi_results)
        exists_dois = sum(1 for _, status in self.doi_results.values() if status == DOIStatus.Exists)
        validated_dois = sum(1 for _, status in self.doi_results.values() if status == DOIStatus.Validated)
        confirmed_dois = sum(1 for _, status in self.doi_results.values() if status == DOIStatus.Confirmed)
        cached_dois = sum(1 for _, status in self.doi_results.values() if status == DOIStatus.Cached)
        nonexists_dois = sum(1 for _, status in self.doi_results.values() if status == DOIStatus.NonExists)
        error_dois = sum(1 for _, status in self.doi_results.values() if status == DOIStatus.Internal_Error)
        
        # Collect problematic entries
        nonexists_keys = [
            key for key, (doi, status) in self.doi_results.items()
            if status == DOIStatus.NonExists
        ]
        
        error_keys = [
            key for key, (doi, status) in self.doi_results.items()
            if status == DOIStatus.Internal_Error
        ]
        
        # Print invalid entries first
        if nonexists_keys:
            print("\n" + "="*70)
            print("NON-EXISTENT DOIs (found so far):")
            print("="*70)
            for key in sorted(nonexists_keys):
                doi, _ = self.doi_results[key]
                print(f"  ❌ {key}")
                if self.verbose:
                    print(f"      → https://doi.org/{doi}")
        
        # Print error entries
        if error_keys:
            print("\n" + "="*70)
            print("DOIs WITH ERRORS (found so far):")
            print("="*70)
            for key in sorted(error_keys):
                doi, _ = self.doi_results[key]
                print(f"  ⚠️ {key}")
                if self.verbose:
                    print(f"      → https://doi.org/{doi}")
        
        # Print partial summary
        print("\n" + "="*70)
        print("PARTIAL DOI VALIDATION SUMMARY (interrupted)")
        print("="*70)
        total_entries = len(self._count_all_bib_entries())
        print(f"Total references in bibliography: {total_entries}")
        print(f"Checked so far:                  {total_checked}")
        print(f"Valid (Exists):                  {exists_dois}")
        print(f"Valid (Validated - 401/403):     {validated_dois}")
        print(f"Valid (Confirmed - 200):         {confirmed_dois}")
        print(f"Valid (Cached):                  {cached_dois}")
        print(f"Non-existent DOIs:               {nonexists_dois}")
        print(f"Errors:                          {error_dois}")
        print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description='Validate DOIs in a BibTeX file',
        epilog="""
VALIDATION STATUS MEANINGS:
    ✔️ Exists       - DOI resolves but target is inaccessible (404 or unreachable)
    🔗 Validated    - DOI resolves with access restriction (HTTP 401/403)
    ✅ Confirmed    - DOI fully validated with accessible target (HTTP 200)
    💾 Cached       - Result loaded from cache (within 30 days)
    ❌ NonExists    - DOI does not exist (HTTP 404 at resolver)
    ⚠️ Error        - Connection or validation error occurred
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'bib_file',
        nargs='?',
        default='references.bib',
        help='BibTeX file to validate (default: references.bib)'
    )
    parser.add_argument(
        '-t', '--timeout',
        type=int,
        default=5,
        help='Timeout for DOI resolution in seconds (default: 5)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print verbose output including DOI URLs being checked'
    )
    parser.add_argument(
        '-u', '--user-agent',
        type=str,
        default=None,
        help='Custom user-agent string (default: Chrome browser user-agent)'
    )
    parser.add_argument(
        '-l', '--limit',
        type=int,
        default=None,
        help='Limit to first N uncached DOIs to check (cached results always shown)'
    )
    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear the DOI validation cache'
    )
    
    args = parser.parse_args()
    
    # Handle cache clearing
    if args.clear_cache:
        cache = DOICache()
        cache.clear()
        print(f"Cache cleared: {DOICache.CACHE_FILE}")
        sys.exit(0)
    
    try:
        validator = DOIValidator(
            args.bib_file,
            timeout=args.timeout,
            verbose=args.verbose,
            user_agent=args.user_agent,
            limit=args.limit
        )
        validator.validate()
    except KeyboardInterrupt:
        print("\n\n⏸️  Script interrupted by user (CTRL-C)")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
