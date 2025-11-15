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


class TestReferenceHandling(unittest.TestCase):

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
    
    def test_label_extraction_figures(self):
        r"""Test extraction of labels from figures"""
        content = r"""
\documentclass{article}
\begin{document}

\begin{figure}
  \includegraphics{image.png}
  \caption{A nice figure}
  \label{fig:nice}
\end{figure}

\begin{figure}
  \includegraphics{another.png}
  \caption{Another figure}
  \label{fig:another}
\end{figure}

\end{document}
"""
        main_file = self.create_test_file("main.tex", content)
        processor = LaTeXProcessor(str(main_file))
        processor._extract_labels_and_refs(content)
        
        self.assertIn("fig:nice", processor.labels)
        self.assertIn("fig:another", processor.labels)
        self.assertEqual(processor.labels["fig:nice"]["type"], "figure")
        self.assertEqual(processor.labels["fig:another"]["type"], "figure")
    
    def test_label_extraction_tables(self):
        r"""Test extraction of labels from tables"""
        content = r"""
\documentclass{article}
\begin{document}

\begin{table}
  \begin{tabular}{cc}
    A & B \\
    C & D
  \end{tabular}
  \caption{Data table}
  \label{tab:data}
\end{table}

\end{document}
"""
        main_file = self.create_test_file("main.tex", content)
        processor = LaTeXProcessor(str(main_file))
        processor._extract_labels_and_refs(content)
        
        self.assertIn("tab:data", processor.labels)
        self.assertEqual(processor.labels["tab:data"]["type"], "table")
    
    def test_label_extraction_sections(self):
        r"""Test extraction of labels from sections"""
        content = r"""
\documentclass{article}
\begin{document}

\section{Introduction}
\label{sec:intro}

\subsection{Background}
\label{sec:background}

\subsubsection{History}
\label{sec:history}

\end{document}
"""
        main_file = self.create_test_file("main.tex", content)
        processor = LaTeXProcessor(str(main_file))
        processor._extract_labels_and_refs(content)
        
        self.assertIn("sec:intro", processor.labels)
        self.assertIn("sec:background", processor.labels)
        self.assertIn("sec:history", processor.labels)
        self.assertEqual(processor.labels["sec:intro"]["type"], "section")
        self.assertEqual(processor.labels["sec:background"]["type"], "subsection")
        self.assertEqual(processor.labels["sec:history"]["type"], "subsubsection")
    
    def test_reference_extraction(self):
        r"""Test extraction of references"""
        content = r"""
\documentclass{article}
\begin{document}

See Figure \ref{fig:nice} and Table \ref{tab:data}.
Also see Section \ref{sec:intro}.
For equations, use \eqref{eq:einstein}.

\end{document}
"""
        main_file = self.create_test_file("main.tex", content)
        processor = LaTeXProcessor(str(main_file))
        processor._extract_labels_and_refs(content)
        
        self.assertEqual(len(processor.references), 4)
        
        ref_names = [ref['ref'] for ref in processor.references]
        self.assertIn("fig:nice", ref_names)
        self.assertIn("tab:data", ref_names)
        self.assertIn("sec:intro", ref_names)
        self.assertIn("eq:einstein", ref_names)
    
    def test_undefined_references(self):
        r"""Test detection of undefined references"""
        content = r"""
\documentclass{article}
\begin{document}

\section{Test}
\label{sec:test}

This references \ref{sec:test} which exists.
This references \ref{sec:missing} which does not exist.

\end{document}
"""
        main_file = self.create_test_file("main.tex", content)
        processor = LaTeXProcessor(str(main_file))
        processor._extract_labels_and_refs(content)
        
        # Check that sec:test is defined
        self.assertIn("sec:test", processor.labels)
        
        # Check that we have 2 references
        self.assertEqual(len(processor.references), 2)
        
        # Check for undefined reference
        referenced_labels = set(ref['ref'] for ref in processor.references)
        undefined = referenced_labels - set(processor.labels.keys())
        self.assertIn("sec:missing", undefined)
    
    def test_unused_labels(self):
        r"""Test detection of unused labels"""
        content = r"""
\documentclass{article}
\begin{document}

\section{Used Section}
\label{sec:used}

\section{Unused Section}
\label{sec:unused}

See Section \ref{sec:used}.

\end{document}
"""
        main_file = self.create_test_file("main.tex", content)
        processor = LaTeXProcessor(str(main_file))
        processor._extract_labels_and_refs(content)
        
        # Both labels should be defined
        self.assertIn("sec:used", processor.labels)
        self.assertIn("sec:unused", processor.labels)
        
        # Check for unused label
        referenced_labels = set(ref['ref'] for ref in processor.references)
        unused = set(processor.labels.keys()) - referenced_labels
        self.assertIn("sec:unused", unused)
        self.assertNotIn("sec:used", unused)



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


class TestDuplicateDetectionAndCaptions(unittest.TestCase):
    """Tests for duplicate label detection and caption extraction"""
    
    def setUp(self):
        """Set up test environment with temporary directory"""
        self.test_dir = Path(tempfile.mkdtemp())
    
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

    def test_duplicate_label_detection(self):
        """Test detection of duplicate labels"""
        main_content = r"""
\documentclass{article}
\begin{document}

\section{Introduction}\label{sec:intro}
Some text here.

\begin{figure}
\caption{First figure}
\label{fig:test}
\end{figure}

More text.

\begin{figure}
\caption{Second figure}
\label{fig:test}
\end{figure}

Another section.
\section{Methods}\label{sec:methods}

\begin{table}
\caption{A table}
\label{tab:data}
\end{table}

\begin{table}
\caption{Another table}
\label{tab:data}
\end{table}

\end{document}
"""
        
        main_file = self.create_test_file("main.tex", main_content)
        output_file = self.test_dir / "output.tex"
        processor = LaTeXProcessor(str(main_file), str(output_file))
        processor.process()
        
        # Check for duplicates
        duplicates = processor.detect_duplicate_labels()
        
        self.assertEqual(len(duplicates), 2)  # fig:test and tab:data
        self.assertIn('fig:test', duplicates)
        self.assertIn('tab:data', duplicates)
        self.assertEqual(len(duplicates['fig:test']), 2)
        self.assertEqual(len(duplicates['tab:data']), 2)
        
    def test_no_duplicate_labels(self):
        """Test when there are no duplicate labels"""
        main_content = r"""
\documentclass{article}
\begin{document}

\section{Introduction}\label{sec:intro}

\begin{figure}
\caption{A figure}
\label{fig:one}
\end{figure}

\begin{figure}
\caption{Another figure}
\label{fig:two}
\end{figure}

\end{document}
"""
        
        main_file = self.create_test_file("main.tex", main_content)
        output_file = self.test_dir / "output.tex"
        processor = LaTeXProcessor(str(main_file), str(output_file))
        processor.process()
        
        duplicates = processor.detect_duplicate_labels()
        self.assertEqual(len(duplicates), 0)
        
    def test_caption_extraction_with_labels(self):
        """Test extraction of captions and their association with labels"""
        main_content = r"""
\documentclass{article}
\begin{document}

\begin{figure}
\centering
\includegraphics{image.pdf}
\caption{This is a figure caption}
\label{fig:example}
\end{figure}

\begin{table}
\centering
\begin{tabular}{cc}
A & B \\
\end{tabular}
\caption{This is a table caption}
\label{tab:results}
\end{table}

\end{document}
"""
        
        main_file = self.create_test_file("main.tex", main_content)
        output_file = self.test_dir / "output.tex"
        processor = LaTeXProcessor(str(main_file), str(output_file))
        processor.process()
        
        # Extract captions
        captions = processor.extract_captions(processor.processed_content)
        
        self.assertIn('fig:example', captions)
        self.assertIn('tab:results', captions)
        
        self.assertEqual(captions['fig:example']['caption'], 'This is a figure caption')
        self.assertEqual(captions['fig:example']['type'], 'figure')
        self.assertTrue(captions['fig:example']['has_caption'])
        
        self.assertEqual(captions['tab:results']['caption'], 'This is a table caption')
        self.assertEqual(captions['tab:results']['type'], 'table')
        self.assertTrue(captions['tab:results']['has_caption'])
        
    def test_caption_missing(self):
        """Test detection of labels without captions"""
        main_content = r"""
\documentclass{article}
\begin{document}

\begin{figure}
\centering
\includegraphics{image.pdf}
\label{fig:no_caption}
\end{figure}

\begin{figure}
\centering
\includegraphics{image2.pdf}
\caption{This one has a caption}
\label{fig:with_caption}
\end{figure}

\end{document}
"""
        
        main_file = self.create_test_file("main.tex", main_content)
        output_file = self.test_dir / "output.tex"
        processor = LaTeXProcessor(str(main_file), str(output_file))
        processor.process()
        
        captions = processor.extract_captions(processor.processed_content)
        
        # Check the label without caption
        self.assertIn('fig:no_caption', captions)
        self.assertFalse(captions['fig:no_caption']['has_caption'])
        self.assertIsNone(captions['fig:no_caption']['caption'])
        
        # Check the label with caption
        self.assertIn('fig:with_caption', captions)
        self.assertTrue(captions['fig:with_caption']['has_caption'])
        self.assertEqual(captions['fig:with_caption']['caption'], 'This one has a caption')
        
    def test_caption_with_nested_braces(self):
        """Test caption extraction with nested braces"""
        main_content = r"""
\documentclass{article}
\begin{document}

\begin{figure}
\caption{Caption with \textbf{bold text} and $\alpha = \beta$}
\label{fig:complex}
\end{figure}

\end{document}
"""
        
        main_file = self.create_test_file("main.tex", main_content)
        output_file = self.test_dir / "output.tex"
        processor = LaTeXProcessor(str(main_file), str(output_file))
        processor.process()
        
        captions = processor.extract_captions(processor.processed_content)
        
        self.assertIn('fig:complex', captions)
        # Check that caption contains the formatting commands
        self.assertIn('textbf', captions['fig:complex']['caption'])
        self.assertIn('alpha', captions['fig:complex']['caption'])

    def test_bibtex_export_mode(self):
        """Test bibtex export mode extracts only referenced entries"""
        main_content = r"""
\documentclass{article}
\begin{document}

Some text citing \cite{Smith2020} and \cite{Jones2019}.

\bibliographystyle{plain}
\bibliography{refs}

\end{document}
"""
        
        bib_content = r"""
@article{Smith2020,
    author = {Smith, John},
    title = {A Paper},
    journal = {Journal},
    year = {2020}
}

@article{Jones2019,
    author = {Jones, Jane},
    title = {Another Paper},
    journal = {Journal},
    year = {2019}
}

@article{Brown2021,
    author = {Brown, Bob},
    title = {Uncited Paper},
    journal = {Journal},
    year = {2021}
}
"""
        
        main_file = self.create_test_file("main.tex", main_content)
        self.create_test_file("refs.bib", bib_content)
        output_file = self.test_dir / "output.bib"
        
        processor = LaTeXProcessor(str(main_file), str(output_file), mode='bibtex')
        processor.process()
        
        # Read output
        with open(output_file, 'r', encoding='utf-8') as f:
            result = f.read()
        
        # Should contain cited entries
        self.assertIn('Smith2020', result)
        self.assertIn('Jones2019', result)
        
        # Should NOT contain uncited entry
        self.assertNotIn('Brown2021', result)


class TestBibLaTeXProcessing(unittest.TestCase):
    """Test BibLaTeX-style bibliography processing"""
    
    def setUp(self):
        """Set up test environment with temporary directory"""
        self.test_dir = Path(tempfile.mkdtemp())
    
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
    
    def test_biblatex_style_processing(self):
        """Test BibLaTeX-style bibliography with \\addbibresource and \\printbibliography"""
        main_content = r"""
\documentclass{article}
\usepackage[backend=biber]{biblatex}
\addbibresource{refs.bib}

\begin{document}
This cites \cite{Smith2020} and \cite{Jones2019}.

\printbibliography[title=References]

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
        
        # Should contain bibliography with \reftitle
        self.assertIn(r"\reftitle{References}", result)
        self.assertIn(r"\begin{thebibliography}{99}", result)
        self.assertIn(r"\bibitem[Smith(2020)]{Smith2020}", result)
        self.assertIn(r"\bibitem[Jones(2019)]{Jones2019}", result)
        self.assertIn("Smith, J. (2020)", result)
        self.assertIn("Nature", result)
        
        # Should not contain unused citation
        self.assertNotIn("Unused2021", result)
        self.assertNotIn("Nobody", result)
        
        # Should not contain original bibliography commands
        self.assertNotIn(r"\addbibresource{refs.bib}", result)
        self.assertNotIn(r"\printbibliography", result)
    
    def test_biblatex_default_title(self):
        """Test BibLaTeX-style bibliography without explicit title"""
        main_content = r"""
\documentclass{article}
\usepackage{biblatex}
\addbibresource{refs.bib}

\begin{document}
This cites \cite{Author2020}.

\printbibliography

\end{document}
"""
        
        bib_content = r"""
@article{Author2020,
  title={Test Article},
  author={Author, Test},
  journal={Test Journal},
  year={2020}
}
"""
        
        main_file = self.create_test_file("main.tex", main_content)
        self.create_test_file("refs.bib", bib_content)
        
        output_file = self.test_dir / "output.tex"
        processor = LaTeXProcessor(str(main_file), str(output_file))
        processor.process()
        
        with open(output_file, 'r', encoding='utf-8') as f:
            result = f.read()
        
        # Should use default title "References"
        self.assertIn(r"\reftitle{References}", result)
        self.assertIn(r"\begin{thebibliography}{99}", result)
    
    def test_biblatex_custom_title(self):
        """Test BibLaTeX-style bibliography with custom title"""
        main_content = r"""
\documentclass{article}
\usepackage{biblatex}
\addbibresource{refs.bib}

\begin{document}
This cites \cite{Author2020}.

\printbibliography[title=Bibliography]

\end{document}
"""
        
        bib_content = r"""
@article{Author2020,
  title={Test Article},
  author={Author, Test},
  journal={Test Journal},
  year={2020}
}
"""
        
        main_file = self.create_test_file("main.tex", main_content)
        self.create_test_file("refs.bib", bib_content)
        
        output_file = self.test_dir / "output.tex"
        processor = LaTeXProcessor(str(main_file), str(output_file))
        processor.process()
        
        with open(output_file, 'r', encoding='utf-8') as f:
            result = f.read()
        
        # Should use custom title "Bibliography"
        self.assertIn(r"\reftitle{Bibliography}", result)
        self.assertIn(r"\begin{thebibliography}{99}", result)
    
    def test_traditional_vs_biblatex(self):
        """Test that traditional and BibLaTeX styles are distinguished correctly"""
        # Traditional style
        traditional_content = r"""
\documentclass{article}
\begin{document}
This cites \cite{Smith2020}.
\bibliography{refs}
\end{document}
"""
        
        # BibLaTeX style
        biblatex_content = r"""
\documentclass{article}
\addbibresource{refs.bib}
\begin{document}
This cites \cite{Smith2020}.
\printbibliography
\end{document}
"""
        
        bib_content = r"""
@article{Smith2020,
  title={Test},
  author={Smith, John},
  journal={Journal},
  year={2020}
}
"""
        
        # Test traditional
        trad_file = self.create_test_file("traditional.tex", traditional_content)
        self.create_test_file("refs.bib", bib_content)
        trad_output = self.test_dir / "trad_output.tex"
        processor = LaTeXProcessor(str(trad_file), str(trad_output))
        processor.process()
        
        with open(trad_output, 'r', encoding='utf-8') as f:
            trad_result = f.read()
        
        # Traditional should NOT have \reftitle
        self.assertNotIn(r"\reftitle", trad_result)
        self.assertIn(r"\begin{thebibliography}{99}", trad_result)
        
        # Test BibLaTeX
        biblatex_file = self.create_test_file("biblatex.tex", biblatex_content)
        biblatex_output = self.test_dir / "biblatex_output.tex"
        processor = LaTeXProcessor(str(biblatex_file), str(biblatex_output))
        processor.process()
        
        with open(biblatex_output, 'r', encoding='utf-8') as f:
            biblatex_result = f.read()
        
        # BibLaTeX should have \reftitle
        self.assertIn(r"\reftitle{References}", biblatex_result)
        self.assertIn(r"\begin{thebibliography}{99}", biblatex_result)
    
    def test_biblatex_multiple_citations(self):
        """Test BibLaTeX with multiple citations in order"""
        main_content = r"""
\documentclass{article}
\addbibresource{refs.bib}
\begin{document}
First \cite{Zebra2020}, then \cite{Alpha2019}, and \cite{Beta2021}.
\printbibliography[title=References]
\end{document}
"""
        
        bib_content = r"""
@article{Zebra2020,
  title={Zebra Paper},
  author={Zebra, Z.},
  journal={Journal Z},
  year={2020}
}

@article{Alpha2019,
  title={Alpha Paper},
  author={Alpha, A.},
  journal={Journal A},
  year={2019}
}

@article{Beta2021,
  title={Beta Paper},
  author={Beta, B.},
  journal={Journal B},
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
        
        # All citations should be present
        self.assertIn("Zebra2020", result)
        self.assertIn("Alpha2019", result)
        self.assertIn("Beta2021", result)
        
        # Should be in citation order (not alphabetical)
        zebra_pos = result.find("Zebra2020")
        alpha_pos = result.find("Alpha2019")
        beta_pos = result.find("Beta2021")
        
        self.assertLess(zebra_pos, alpha_pos)
        self.assertLess(alpha_pos, beta_pos)


if __name__ == '__main__':
    unittest.main()
