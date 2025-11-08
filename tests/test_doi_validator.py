#!/usr/bin/env python3
"""
Unit tests for DOI Validator
Tests cache functionality and DOI validation

Copyright (c) 2025 - Ilja Heitlager
SPDX-License-Identifier: Apache-2.0
"""

import json
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
import tempfile
import shutil

# Add parent scripts directory to path to import doi_validator
sys.path.insert(0, str(Path(__file__).parent.parent))

from doi_validator import DOICache, DOIValidator


class TestDOICache(unittest.TestCase):
    """Test suite for DOICache class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for test cache
        self.test_dir = tempfile.mkdtemp()
        self.test_cache_file = Path(self.test_dir) / '.bib_validator_test'
        
        # Patch the cache file location
        self.cache_patcher = patch.object(DOICache, 'CACHE_FILE', self.test_cache_file)
        self.cache_patcher.start()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.cache_patcher.stop()
        # Explicitly remove test cache file if it exists
        if self.test_cache_file.exists():
            self.test_cache_file.unlink()
        shutil.rmtree(self.test_dir)
    
    def test_cache_initialization_empty(self):
        """Test cache initializes with empty dict when no file exists"""
        cache = DOICache()
        self.assertEqual(cache.cache, {})
        self.assertFalse(self.test_cache_file.exists())
    
    def test_cache_set_and_get(self):
        """Test setting and getting a cached DOI result"""
        cache = DOICache()
        doi = "10.1234/example.doi"
        
        cache.set(doi, True)
        result = cache.get(doi)
        
        self.assertTrue(result)
        self.assertTrue(self.test_cache_file.exists())
    
    def test_cache_set_and_get_status(self):
        """Test setting and getting a cached DOI status"""
        cache = DOICache()
        doi = "10.1234/example.doi"
        
        cache.set_status(doi, "Validated")
        status = cache.get_status(doi)
        
        self.assertEqual(status, "Validated")
        self.assertTrue(self.test_cache_file.exists())
    
    def test_cache_get_nonexistent_doi(self):
        """Test getting a DOI that doesn't exist in cache"""
        cache = DOICache()
        result = cache.get("10.9999/nonexistent.doi")
        
        self.assertIsNone(result)
    
    def test_cache_get_nonexistent_status(self):
        """Test getting a status for a DOI that doesn't exist in cache"""
        cache = DOICache()
        status = cache.get_status("10.9999/nonexistent.doi")
        
        self.assertIsNone(status)
    
    def test_cache_persistence(self):
        """Test that cache persists across instances"""
        doi = "10.1234/example.doi"
        
        # Create first cache instance and store a value
        cache1 = DOICache()
        cache1.set(doi, True)
        
        # Create second cache instance and retrieve the value
        cache2 = DOICache()
        result = cache2.get(doi)
        
        self.assertTrue(result)
    
    def test_cache_status_persistence(self):
        """Test that cache status persists across instances"""
        doi = "10.1234/validated.doi"
        
        # Create first cache instance and store a status
        cache1 = DOICache()
        cache1.set_status(doi, "Validated")
        
        # Create second cache instance and retrieve the status
        cache2 = DOICache()
        status = cache2.get_status(doi)
        
        self.assertEqual(status, "Validated")
    
    def test_cache_is_valid_fresh(self):
        """Test that fresh cache entry is valid"""
        cache = DOICache()
        doi = "10.1234/fresh.doi"
        
        cache.set(doi, True)
        is_valid = cache.is_valid(doi)
        
        self.assertTrue(is_valid)
    
    def test_cache_is_valid_expired(self):
        """Test that expired cache entry is invalid"""
        cache = DOICache()
        doi = "10.1234/expired.doi"
        
        # Set cache entry with old timestamp
        old_timestamp = (datetime.now() - timedelta(days=31)).isoformat()
        cache.cache[doi] = {
            'is_valid': True,
            'timestamp': old_timestamp
        }
        cache._save_cache()
        
        is_valid = cache.is_valid(doi)
        
        self.assertFalse(is_valid)
    
    def test_cache_is_valid_almost_expired(self):
        """Test that cache entry just before expiration is valid"""
        cache = DOICache()
        doi = "10.1234/almost_expired.doi"
        
        # Set cache entry with timestamp 29 days ago
        old_timestamp = (datetime.now() - timedelta(days=29)).isoformat()
        cache.cache[doi] = {
            'is_valid': True,
            'timestamp': old_timestamp
        }
        cache._save_cache()
        
        is_valid = cache.is_valid(doi)
        
        self.assertTrue(is_valid)
    
    def test_cache_is_valid_missing_timestamp(self):
        """Test that cache entry without timestamp is invalid"""
        cache = DOICache()
        doi = "10.1234/no_timestamp.doi"
        
        # Manually add cache entry without timestamp
        cache.cache[doi] = {'is_valid': True}
        cache._save_cache()
        
        is_valid = cache.is_valid(doi)
        
        self.assertFalse(is_valid)
    
    def test_cache_clear(self):
        """Test clearing the cache"""
        cache = DOICache()
        doi = "10.1234/example.doi"
        
        # Add entry to cache
        cache.set(doi, True)
        self.assertTrue(self.test_cache_file.exists())
        
        # Clear cache
        cache.clear()
        self.assertFalse(self.test_cache_file.exists())
        self.assertEqual(cache.cache, {})
    
    def test_cache_store_validated_status(self):
        """Test caching DOI with Validated status"""
        cache = DOICache()
        doi = "10.1111/validated.doi"
        
        cache.set_status(doi, "Validated")
        status = cache.get_status(doi)
        
        self.assertEqual(status, "Validated")
        self.assertTrue(cache.is_doi_valid(doi))
        self.assertTrue(cache.is_valid(doi))
    
    def test_cache_store_exists_status(self):
        """Test caching DOI with Exists status"""
        cache = DOICache()
        doi = "10.1111/exists.doi"
        
        cache.set_status(doi, "Exists")
        status = cache.get_status(doi)
        
        self.assertEqual(status, "Exists")
        self.assertTrue(cache.is_doi_valid(doi))
        self.assertTrue(cache.is_valid(doi))
    
    def test_cache_store_nonexists_status(self):
        """Test caching DOI with NonExists status"""
        cache = DOICache()
        doi = "10.1111/nonexists.doi"
        
        cache.set_status(doi, "NonExists")
        status = cache.get_status(doi)
        
        self.assertEqual(status, "NonExists")
        self.assertFalse(cache.is_doi_valid(doi))
        self.assertTrue(cache.is_valid(doi))
    
    def test_cache_multiple_entries(self):
        """Test cache with multiple entries"""
        cache = DOICache()
        dois = {
            "10.1234/first.doi": True,
            "10.5678/second.doi": False,
            "10.9012/third.doi": True,
        }
        
        # Add multiple entries
        for doi, is_valid in dois.items():
            cache.set(doi, is_valid)
        
        # Verify all entries
        for doi, expected_valid in dois.items():
            result = cache.get(doi)
            self.assertEqual(result, expected_valid)
            self.assertTrue(cache.is_valid(doi))
    
    def test_cache_file_format(self):
        """Test that cache file is valid JSON"""
        cache = DOICache()
        cache.set("10.1234/test.doi", True)
        
        # Read cache file directly
        with open(self.test_cache_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn("10.1234/test.doi", data)
        self.assertIn("is_valid", data["10.1234/test.doi"])
        self.assertIn("timestamp", data["10.1234/test.doi"])
    
    def test_cache_load_invalid_json(self):
        """Test cache handles invalid JSON gracefully"""
        # Write invalid JSON to cache file
        with open(self.test_cache_file, 'w') as f:
            f.write("invalid json {")
        
        # Should not raise exception, returns empty cache
        cache = DOICache()
        self.assertEqual(cache.cache, {})
    
    def test_cache_verbose_mode(self):
        """Test cache in verbose mode"""
        cache = DOICache(verbose=True)
        cache.set("10.1234/test.doi", True)
        
        # Verify cache works the same in verbose mode
        self.assertTrue(cache.is_valid("10.1234/test.doi"))
        self.assertTrue(cache.get("10.1234/test.doi"))


class TestBibTeXParsing(unittest.TestCase):
    """Test suite for BibTeX parsing functionality"""
    
    def test_parse_simple_entry_with_doi(self):
        """Test parsing a simple article entry with DOI"""
        bib_content = """@article{Hodkinson2005,
    title = {{'Insider research' in the study of youth cultures}},
    year = {2005},
    journal = {Journal of Youth Studies},
    author = {Hodkinson, Paul},
    number = {2},
    pages = {131--149},
    volume = {8},
    doi = {10.1080/13676260500149238},
    issn = {13676261}
}"""
        validator = DOIValidator.__new__(DOIValidator)
        validator.entries = {}
        validator._parse_bib_entries(bib_content)
        
        # Verify entry was parsed
        self.assertIn('Hodkinson2005', validator.entries)
        self.assertEqual(
            validator.entries['Hodkinson2005']['doi'],
            '10.1080/13676260500149238'
        )
        self.assertEqual(
            validator.entries['Hodkinson2005']['entry_type'],
            'article'
        )
    
    def test_parse_entry_without_doi(self):
        """Test parsing an entry without DOI is skipped"""
        bib_content = """@article{Arno,
    title = {{50 gouden regels en tips voor een proefschriftonderzoek}},
    author = {Arno, Prof A and Korsten, F A and Albert, A}
}"""
        validator = DOIValidator.__new__(DOIValidator)
        validator.entries = {}
        validator._parse_bib_entries(bib_content)
        
        # Entry without DOI should not be in entries
        self.assertNotIn('Arno', validator.entries)
    
    def test_parse_multiple_entries(self):
        """Test parsing multiple entries with and without DOIs"""
        bib_content = """@article{Wirth2008,
    title = {{A Brief History of Software Engineering}},
    year = {2008},
    journal = {IEEE Annals of the History of Computing},
    author = {Wirth, Niklaus},
    doi = {10.1109/MAHC.2008.33}
}

@article{Simon1955,
    title = {{A behavioral model of rational choice}},
    year = {1955},
    journal = {The Quarterly Journal of Economics},
    author = {Simon, H. A.},
    number = {1},
    pages = {99--118},
    volume = {69}
}

@article{VanOorschot2015,
    title = {{A Bibliometric Review of the Innovation Adoption Literature}},
    year = {2015},
    journal = {Academy of Management Proceedings},
    author = {van Oorschot, J. and Hofman, E. and Halman, J.},
    doi = {10.5465/ambpp.2015.16847abstract}
}"""
        validator = DOIValidator.__new__(DOIValidator)
        validator.entries = {}
        validator._parse_bib_entries(bib_content)
        
        # Should parse 2 entries with DOI
        self.assertEqual(len(validator.entries), 2)
        self.assertIn('Wirth2008', validator.entries)
        self.assertIn('VanOorschot2015', validator.entries)
        self.assertNotIn('Simon1955', validator.entries)
    
    def test_doi_cleanup_with_special_characters(self):
        """Test that DOI cleanup handles escaped underscores"""
        bib_content = """@book{TestBook,
    title = {Test},
    author = {Author},
    doi = {10.1057/978-1-349-94848-2{\\_}390-1}
}"""
        validator = DOIValidator.__new__(DOIValidator)
        validator.entries = {}
        validator._parse_bib_entries(bib_content)
        
        # Verify escaped underscore is cleaned
        self.assertEqual(
            validator.entries['TestBook']['doi'],
            '10.1057/978-1-349-94848-2_390-1'
        )
    
    def test_doi_cleanup_with_alternative_escaping(self):
        """Test DOI cleanup with {_} pattern"""
        bib_content = """@book{TestBook2,
    title = {Test},
    author = {Author},
    doi = {10.1234/{_}test}
}"""
        validator = DOIValidator.__new__(DOIValidator)
        validator.entries = {}
        validator._parse_bib_entries(bib_content)
        
        # Verify {_} is cleaned
        self.assertEqual(
            validator.entries['TestBook2']['doi'],
            '10.1234/_test'
        )
    
    def test_doi_cleanup_removes_remaining_braces(self):
        """Test that remaining braces are removed from DOI"""
        bib_content = """@book{TestBook3,
    title = {Test},
    author = {Author},
    doi = {10.1234/test{code}123}
}"""
        validator = DOIValidator.__new__(DOIValidator)
        validator.entries = {}
        validator._parse_bib_entries(bib_content)
        
        # Verify braces are removed
        self.assertEqual(
            validator.entries['TestBook3']['doi'],
            '10.1234/testcode123'
        )
    
    def test_parse_inproceedings_entry(self):
        """Test parsing @inproceedings entry type"""
        bib_content = """@inproceedings{Venable2012,
    title = {{A Comprehensive Framework for Evaluation in Design Science Research}},
    year = {2012},
    booktitle = {Proceedings of the 7th international conference},
    author = {Venable, John Robert},
    doi = {10.1007/978-3-642-29863-9}
}"""
        validator = DOIValidator.__new__(DOIValidator)
        validator.entries = {}
        validator._parse_bib_entries(bib_content)
        
        # Verify inproceedings entry is parsed
        self.assertIn('Venable2012', validator.entries)
        self.assertEqual(
            validator.entries['Venable2012']['entry_type'],
            'inproceedings'
        )
        self.assertEqual(
            validator.entries['Venable2012']['doi'],
            '10.1007/978-3-642-29863-9'
        )
    
    def test_parse_phdthesis_entry(self):
        """Test parsing @phdthesis entry type"""
        bib_content = """@phdthesis{Valdez1989,
    title = {{A Gift From Pandora's Box: The Software Crisis}},
    year = {1989},
    author = {Valdez, Maria Eloina Pelaez},
    school = {Edinburgh},
    doi = {10.1234/phd.thesis}
}"""
        validator = DOIValidator.__new__(DOIValidator)
        validator.entries = {}
        validator._parse_bib_entries(bib_content)
        
        # Verify phdthesis entry is parsed
        self.assertIn('Valdez1989', validator.entries)
        self.assertEqual(
            validator.entries['Valdez1989']['entry_type'],
            'phdthesis'
        )
    
    def test_doi_field_case_insensitive(self):
        """Test that DOI field detection is case-insensitive"""
        bib_content = """@article{TestDOI,
    title = {Test},
    author = {Author},
    DOI = {10.1234/test.case}
}"""
        validator = DOIValidator.__new__(DOIValidator)
        validator.entries = {}
        validator._parse_bib_entries(bib_content)
        
        # Should find DOI even if in uppercase
        self.assertIn('TestDOI', validator.entries)
        self.assertEqual(
            validator.entries['TestDOI']['doi'],
            '10.1234/test.case'
        )
    
    def test_parse_complex_doi_format(self):
        """Test parsing complex DOI with multiple dots and slashes"""
        bib_content = """@article{Complex2023,
    title = {Complex DOI},
    author = {Author},
    doi = {10.1093/oxfordhb/9780199763986.013.0003}
}"""
        validator = DOIValidator.__new__(DOIValidator)
        validator.entries = {}
        validator._parse_bib_entries(bib_content)
        
        # Verify complex DOI is preserved
        self.assertEqual(
            validator.entries['Complex2023']['doi'],
            '10.1093/oxfordhb/9780199763986.013.0003'
        )


if __name__ == '__main__':
    unittest.main()
