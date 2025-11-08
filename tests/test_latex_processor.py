#!/usr/bin/env python3
r"""
Unit tests for LaTeX File Processor
Processes LaTeX files by:
1. Recursively inlining all \input and \include commands
2. Filtering and inlining bibliography entries as \bibitem commands

Copyright (c) 2025 - Ilja Heitlager
SPDX-License-Identifier: Apache-2.0
"""

import unittest
import tempfile
from pathlib import Path
import shutil
import sys

# Add parent scripts directory to path to import latex_processor
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from latex_processor import LaTeXProcessor
except ImportError:
    print("Error: Could not import latex_processor module.")
    print("Make sure latex_processor.py is in the scripts directory.")
    sys.exit(1)


class TestLaTeXProcessor(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment with temporary directory"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.processor = None
    
    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def create_test_file(self, filename: str, content: str) -> Path:
        """Helper to create test files"""
        file_path = self.test_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_simple_include_processing(self):
        r"""Test basic \input and \include processing"""
        # Create main file
        main_content = r"""
\documentclass{article}
\begin{document}
Main content here.
\input{chapter1}
More main content.
\include{chapter2}
End of main.
\end{document}
"""
        
        # Create included files
        chapter1_content = "This is chapter 1 content."
        chapter2_content = "This is chapter 2 content."
        
        main_file = self.create_test_file("main.tex", main_content)
        self.create_test_file("chapter1.tex", chapter1_content)
        self.create_test_file("chapter2.tex", chapter2_content)
        
        # Process
        output_file = self.test_dir / "output.tex"
        processor = LaTeXProcessor(str(main_file), str(output_file))
        processor.process()
        
        # Verify output
        with open(output_file, 'r', encoding='utf-8') as f:
            result = f.read()
        
        self.assertIn("This is chapter 1 content.", result)
        self.assertIn("This is chapter 2 content.", result)
        self.assertIn("Main content here.", result)
        self.assertNotIn(r"\input{chapter1}", result)
        self.assertNotIn(r"\include{chapter2}", result)
    
    def test_recursive_includes(self):
        """Test recursive inclusion of files"""
        main_content = r"""
\documentclass{article}
\begin{document}
\input{level1}
\end{document}
"""
        
        level1_content = r"""
Level 1 content.
\input{level2}
More level 1.
"""
        
        level2_content = "Level 2 content."
        
        main_file = self.create_test_file("main.tex", main_content)
        self.create_test_file("level1.tex", level1_content)
        self.create_test_file("level2.tex", level2_content)
        
        output_file = self.test_dir / "output.tex"
        processor = LaTeXProcessor(str(main_file), str(output_file))
        processor.process()
        
        with open(output_file, 'r', encoding='utf-8') as f:
            result = f.read()
        
        self.assertIn("Level 1 content.", result)
        self.assertIn("Level 2 content.", result)
        self.assertIn("More level 1.", result)
    
    def test_citation_extraction(self):
        r"""Test extraction of citation keys"""
        content = r"""
Some text with \cite{Smith2020} and \citep{Jones2019}.
Also \citet{Brown2021} and multiple \cite{Davis2018,Wilson2022}.
"""
        
        processor = LaTeXProcessor("dummy.tex")
        processor._extract_citation_keys(content)
        
        expected_keys = ['Smith2020', 'Jones2019', 'Brown2021', 'Davis2018', 'Wilson2022']
        self.assertEqual(processor.cited_keys, expected_keys)
    
    def test_bibtex_parsing(self):
        """Test parsing of BibTeX entries"""
        bib_content = r"""
@article{Smith2020,
  title={A Great Paper},
  author={Smith, John and Doe, Jane},
  journal={Journal of Science},
  volume={10},
  number={2},
  pages={123--145},
  year={2020}
}

@book{Jones2019,
  title={The Complete Guide},
  author={Jones, Bob},
  publisher={Academic Press},
  year={2019}
}
"""
        
        bib_file = self.create_test_file("refs.bib", bib_content)
        
        processor = LaTeXProcessor("dummy.tex")
        processor.bib_file = bib_file
        entries = processor._parse_bib_file()
        
        self.assertIn("Smith2020", entries)
        self.assertIn("Jones2019", entries)
        
        smith_entry = entries["Smith2020"]
        self.assertEqual(smith_entry["title"], "A Great Paper")
        self.assertEqual(smith_entry["author"], "Smith, John and Doe, Jane")
        self.assertEqual(smith_entry["year"], "2020")
    
    def test_bibtex_parsing_author(self):
        """Test parsing of BibTeX entries"""
        bib_content = r"""
@article{GarciaMartin2024,
    title = {{Managing start-up–incumbent digital solution co-creation: a four-phase process for intermediation in innovative contexts}},
    year = {2024},
    journal = {Industry and Innovation},
    author = {Garcia Martin, Patricia Carolina and Sj{\"{o}}din, David and Nair, Sujith and Parida, Vinit},
    number = {5},
    pages = {579--605},
    volume = {31},
    publisher = {Routledge},
    doi = {10.1080/13662716.2023.2189091},
    issn = {14698390},
    keywords = {Tension mitigation, asymmetric collaboration, digitalisation, innovation orchestration, value co-creation}
}
"""
        
        bib_file = self.create_test_file("refs.bib", bib_content)
        
        processor = LaTeXProcessor("dummy.tex")
        processor.bib_file = bib_file
        entries = processor._parse_bib_file()
        
        self.assertIn("GarciaMartin2024", entries)

        garcia_entry = entries["GarciaMartin2024"]
        self.assertEqual(garcia_entry["title"], "{Managing start-up–incumbent digital solution co-creation: a four-phase process for intermediation in innovative contexts}")
        self.assertEqual(garcia_entry["author"], 'Garcia Martin, Patricia Carolina and Sj{\\"{o}}din, David and Nair, Sujith and Parida, Vinit')
        self.assertEqual(garcia_entry["year"], "2024")


    def test_apa_author_formatting(self):
        """Test APA style author formatting"""
        processor = LaTeXProcessor("dummy.tex")
        
        # Single author
        result = processor._format_authors_apa("Smith, John")
        self.assertEqual(result, "Smith, J.")
        
        # Two authors
        result = processor._format_authors_apa("Smith, John and Doe, Jane")
        self.assertEqual(result, "Smith, J. \\& Doe, J.")
        
        # Multiple authors
        result = processor._format_authors_apa("Smith, John and Doe, Jane and Brown, Bob")
        self.assertEqual(result, "Smith, J., Doe, J., \\& Brown, B.")
    
    def test_full_bibliography_processing(self):
        """Test complete bibliography processing"""
        main_content = r"""
\documentclass{article}
\begin{document}
This cites \cite{Smith2020} and \cite{Jones2019}.
\bibliographystyle{apa}
\bibliography{refs}
\end{document}
"""
        
        bib_content = r"""
@article{Smith2020,
  title={A Great Paper},
  author={Smith, John},
  journal={Nature},
  volume={580},
  pages={123--125},
  year={2020}
}

@book{Jones2019,
  title={The Book},
  author={Jones, Jane},
  publisher={Academic Press},
  year={2019}
}

@article{Unused2021,
  title={Unused Paper},
  author={Nobody, Someone},
  journal={Nowhere},
  year={2021}
}
"""
        
        main_file = self.create_test_file("main.tex", main_content)
        self.create_test_file("refs.bib", bib_content)
        
        output_file = self.test_dir / "output.tex"
        processor = LaTeXProcessor(str(main_file), str(output_file))
        processor.process()
        
        with open(output_file, 'r', encoding='utf-8') as f:
            result = f.read()
        
        # Should contain bibliography
        self.assertIn(r"\begin{thebibliography}", result)
        self.assertIn(r"\bibitem[Smith(2020)]{Smith2020}", result)
        self.assertIn(r"\bibitem[Jones(2019)]{Jones2019}", result)
        self.assertIn("Smith, J. (2020)", result)
        self.assertIn("Nature", result)
        
        # Should not contain unused citation
        self.assertNotIn("Unused2021", result)
        self.assertNotIn("Nobody", result)
        
        # Should not contain original bibliography commands
        self.assertNotIn(r"\bibliography{refs}", result)
        self.assertNotIn(r"\bibliographystyle{apa}", result)
    
    def test_missing_files_handling(self):
        """Test handling of missing files"""
        main_content = r"""
\documentclass{article}
\begin{document}
\input{missing_file}
\end{document}
"""
        
        main_file = self.create_test_file("main.tex", main_content)
        output_file = self.test_dir / "output.tex"
        
        processor = LaTeXProcessor(str(main_file), str(output_file))
        processor.process()
        
        with open(output_file, 'r', encoding='utf-8') as f:
            result = f.read()
        
        self.assertIn("% File not found: missing_file", result)
    
    def test_circular_inclusion_detection(self):
        """Test detection of circular inclusions"""
        main_content = r"""
\documentclass{article}
\begin{document}
\input{file1}
\end{document}
"""
        
        file1_content = r"\input{file2}"
        file2_content = r"\input{file1}"  # Circular reference
        
        main_file = self.create_test_file("main.tex", main_content)
        self.create_test_file("file1.tex", file1_content)
        self.create_test_file("file2.tex", file2_content)
        
        output_file = self.test_dir / "output.tex"
        processor = LaTeXProcessor(str(main_file), str(output_file))
        processor.process()
        
        with open(output_file, 'r', encoding='utf-8') as f:
            result = f.read()
        
        self.assertIn("% Circular inclusion:", result)
    
    def test_file_extension_handling(self):
        """Test handling of files with and without .tex extension"""
        main_content = r"""
\documentclass{article}
\begin{document}
\input{chapter1}
\input{chapter2.tex}
\end{document}
"""
        
        chapter1_content = "Chapter 1 without extension"
        chapter2_content = "Chapter 2 with extension"
        
        main_file = self.create_test_file("main.tex", main_content)
        self.create_test_file("chapter1.tex", chapter1_content)
        self.create_test_file("chapter2.tex", chapter2_content)
        
        output_file = self.test_dir / "output.tex"
        processor = LaTeXProcessor(str(main_file), str(output_file))
        processor.process()
        
        with open(output_file, 'r', encoding='utf-8') as f:
            result = f.read()
        
        self.assertIn("Chapter 1 without extension", result)
        self.assertIn("Chapter 2 with extension", result)


class TestBibItemFormatting(unittest.TestCase):
    """Test specific bibliography formatting functionality"""
    
    def setUp(self):
        self.processor = LaTeXProcessor("dummy.tex")

    def test_article_formatting(self):
        """Test APA formatting for journal articles"""
        entry = {
            'entry_type': 'article',
            'author': 'Smith, John and Doe, Jane',
            'title': 'A Revolutionary Study',
            'journal': 'Journal of Important Research',
            'volume': '42',
            'number': '3',
            'pages': '123--145',
            'year': '2020',
            'doi': '10.1234/example.doi'
        }
        
        result = self.processor._format_apa_bibitem('test_key', entry)
        
        self.assertIn(r'\bibitem[Smith and Doe(2020)]{test_key}', result)
        self.assertIn('Smith, J. \\& Doe, J. (2020)', result)
        self.assertIn('A Revolutionary Study', result)
        self.assertIn(r'\textit{Journal of Important Research}', result)
        self.assertIn('42(3), 123--145', result)
        self.assertIn('https://doi.org/10.1234/example.doi', result)
        
    def test_book_formatting(self):
        """Test APA formatting for books"""
        entry = {
            'entry_type': 'book',
            'author': 'Author, First',
            'title': 'The Great Book',
            'publisher': 'Academic Publishers',
            'year': '2019',
            'doi': '10.1234/book.doi'
        }
        
        result = self.processor._format_apa_bibitem('book_key', entry)
        
        self.assertIn('Author, F. (2019)', result)
        self.assertIn(r'\textit{The Great Book}', result)
        self.assertIn('Academic Publishers', result)
        self.assertIn('https://doi.org/10.1234/book.doi', result)

    def test_article_without_doi(self):
        """Test APA formatting for articles without DOI"""
        entry = {
            'entry_type': 'article',
            'author': 'Smith, John',
            'title': 'Old Paper Without DOI',
            'journal': 'Historical Journal',
            'volume': '15',
            'pages': '45--67',
            'year': '1995'
        }
        
        result = self.processor._format_apa_bibitem('old_key', entry)
        
        self.assertIn(r'\bibitem[Smith(1995)]{old_key}', result)
        self.assertIn('Smith, J. (1995)', result)
        self.assertIn('Old Paper Without DOI', result)
        self.assertNotIn(r'\url{', result)  # Should not contain any URL


class BibtItemParsing(unittest.TestCase):
    """Test cases in BibTeX parsing and formatting"""
    
    def setUp(self):
        self.processor = LaTeXProcessor("dummy.tex")


    def test_short_author_names(self):
        """Test APA formatting for short author names"""
        authors = [
            ("Doe, John", 2020, "Doe(2020)"),
            ("Li, Wei and Kim, Soo and O'Neil, Tim", 2021, "Li et. al.(2021)"),
            ("Warner, Karl S.R. and Waeger, Maximilian", 2019, "Warner and Waeger(2019)"),
        ]
        for author, year, expected in authors:
            formatted = self.processor._format_authors_short(author, year)
            self.assertIn(expected, formatted)

            

    def test_apa_formating_warner(self):
        """Test APA formatting for complex author names"""
        text = """@article{Warner2019,
            title = {{Building dynamic capabilities for digital transformation: An ongoing process of strategic renewal}},
            year = {2019},
            journal = {Long Range Planning},
            author = {Warner, Karl S.R. and Waeger, Maximilian},
            number = {3},
            pages = {326--349},
            volume = {52},
            publisher = {Elsevier Ltd},
            url = {https://linkinghub.elsevier.com/retrieve/pii/S0024630117303710},
            doi = {10.1016/j.lrp.2018.12.001},
            issn = {00246301},
            keywords = {Digital transformation, Digitalization, Dynamic capabilities, Microfoundations, Qualitative interpretive research, Strategic agility, Strategic renewal, Technology and innovation management}
        }"""

        entries = self.processor._parse_bib_entries(text)
        warner_entry = entries["Warner2019"]
        self.assertTrue(warner_entry["author"] == "Warner, Karl S.R. and Waeger, Maximilian")
        result = self.processor._format_apa_bibitem('Warner2019', warner_entry)
        self.assertIn('Warner, K. S. \\& Waeger, M.', result)
        self.assertIn('[Warner and Waeger(2019)]', result)


if __name__ == '__main__':
    unittest.main()
