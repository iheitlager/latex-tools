#!/usr/bin/env python3
"""
LaTeX File Processor

Comprehensive LaTeX document processor that handles:

1. File Inclusion
   - Recursively inlines all \\input and \\include commands
   - Prevents circular inclusions
   - Handles relative and absolute paths

2. Bibliography Processing
   - Extracts citation keys from \\cite, \\citep, \\citet commands
   - Parses BibTeX (.bib) files
   - Filters to only cited references
   - Converts to inline \\bibitem format with APA-style formatting
   - Maintains citation order

3. Label and Reference Tracking
   - Detects labels in figures, tables, sections, subsections, equations, listings
   - Tracks references (\\ref, \\eqref, \\autoref, \\cref, \\Cref)
   - Validates all references are defined
   - Identifies unused labels
   - Provides detailed reporting and programmatic access

4. Reporting
   - File processing statistics
   - Citation counts
   - Label and reference summary by type
   - Validation warnings for undefined references and unused labels

Usage:
    Command line: python3 latex_processor.py main.tex -o onefile.tex
    Programmatic: processor = LaTeXProcessor('main.tex', 'output.tex')
                  processor.process()
                  stats = processor.get_label_stats()

Copyright (c) 2025 - Ilja Heitlager
SPDX-License-Identifier: Apache-2.0
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any


class LaTeXProcessor:
    def __init__(self, main_file: str, output_file: str = "onefile.tex"):
        self.main_file = Path(main_file)
        self.output_file = Path(output_file)
        self.base_dir = self.main_file.parent
        self.processed_files: Set[Path] = set()
        self.cited_keys: List[str] = []
        self.bib_file: Path = None
        
        # Label and reference tracking
        self.labels: Dict[str, Dict[str, Any]] = {}  # label -> {type, context, file, position}
        self.references: List[Dict[str, Any]] = []  # [{ref, type, file, position}]
        self.label_contexts: Dict[str, str] = {}  # label -> surrounding context
        
    def process(self) -> None:
        """Main processing function"""
        print(f"Processing {self.main_file} -> {self.output_file}")
        
        # Pass 1: Process includes/inputs recursively
        content = self._process_includes(self.main_file)
        
        # Pass 2: Extract labels and references
        self._extract_labels_and_refs(content)
        
        # Pass 3: Process bibliography
        content = self._process_bibliography(content)
        
        # Write output
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"Successfully created {self.output_file}")
        print(f"Processed {len(self.processed_files)} files")
        print(f"Found {len(self.cited_keys)} citations")
        print(f"Found {len(self.labels)} labels")
        print(f"Found {len(self.references)} references")
        
        # Report on labels and references
        self._report_labels_and_refs()
    
    def _process_includes(self, file_path: Path, depth: int = 0) -> str:
        """Recursively process \\input and \\include commands"""
        if depth > 50:  # Prevent infinite recursion
            raise RecursionError(f"Maximum inclusion depth exceeded for {file_path}")
            
        if file_path in self.processed_files:
            print(f"Warning: Circular inclusion detected for {file_path}")
            return f"% Circular inclusion: {file_path}\n"
            
        self.processed_files.add(file_path)
        
        if not file_path.exists():
            print(f"Warning: File not found: {file_path}")
            return f"% File not found: {file_path}\n"
            
        print("  " * depth + f"Processing: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                return f"% Error reading file: {file_path}\n"
        
        # Process \input{file} and \include{file}
        def replace_include(match):
            command = match.group(1)  # 'input' or 'include'
            filename = match.group(2).strip()
            
            # Add .tex extension if not present
            if not filename.endswith('.tex'):
                tex_file = self.base_dir / f"{filename}.tex"
            else:
                tex_file = self.base_dir / filename
                
            # Try relative to current file if not found
            if not tex_file.exists():
                current_dir = file_path.parent
                if not filename.endswith('.tex'):
                    tex_file = current_dir / f"{filename}.tex"
                else:
                    tex_file = current_dir / filename
            
            if tex_file.exists():
                included_content = self._process_includes(tex_file, depth + 1)
                return f"\n% Begin included file: {tex_file.name}\n{included_content}\n% End included file: {tex_file.name}\n"
            else:
                print(f"Warning: Included file not found: {filename}")
                return f"% File not found: {filename}\n"
        
        # Match \input{...} and \include{...}
        include_pattern = r'\\(input|include)\s*\{([^}]+)\}'
        content = re.sub(include_pattern, replace_include, content)
        
        return content
    
    def _extract_labels_and_refs(self, content: str) -> None:
        """Extract all labels and references from the content"""
        # Extract labels with context
        self._extract_labels(content)
        
        # Extract references
        self._extract_references(content)
    
    def _extract_labels(self, content: str) -> None:
        r"""Extract all \label{} commands and their context"""
        # Pattern to match \label{labelname}
        label_pattern = r'\\label\{([^}]+)\}'
        
        # Find all labels with their positions
        for match in re.finditer(label_pattern, content):
            label_name = match.group(1)
            position = match.start()
            
            # Extract context around the label
            context_start = max(0, position - 200)
            context_end = min(len(content), position + 200)
            context = content[context_start:context_end].strip()
            
            # Determine label type based on surrounding context
            label_type = self._determine_label_type(content, position)
            
            # Store label information
            self.labels[label_name] = {
                'type': label_type,
                'context': context,
                'position': position
            }
            self.label_contexts[label_name] = context
    
    def _determine_label_type(self, content: str, position: int) -> str:
        """Determine the type of label based on surrounding context"""
        # Look backwards from the label position to find the environment or command
        context_start = max(0, position - 500)
        preceding_text = content[context_start:position]
        
        # Find all environment beginnings and their positions
        environments = []
        
        for match in re.finditer(r'\\begin\{(figure|table|longtable|supertabular|equation|align|gather|multline|listing|lstlisting)\*?\}', preceding_text):
            env_type = match.group(1)
            env_pos = match.start()
            environments.append((env_pos, env_type))
        
        # Find section commands
        for match in re.finditer(r'\\(subsubsection|subsection|section)\{', preceding_text):
            section_type = match.group(1)
            section_pos = match.start()
            environments.append((section_pos, section_type))
        
        # Get the closest environment/command
        if environments:
            # Sort by position (descending) and take the closest one
            environments.sort(reverse=True)
            closest_env = environments[0][1]
            
            # Map environment names to label types
            env_map = {
                'figure': 'figure',
                'table': 'table',
                'longtable': 'table',
                'supertabular': 'table',
                'equation': 'equation',
                'align': 'equation',
                'gather': 'equation',
                'multline': 'equation',
                'listing': 'listing',
                'lstlisting': 'listing',
                'section': 'section',
                'subsection': 'subsection',
                'subsubsection': 'subsubsection'
            }
            
            if closest_env in env_map:
                return env_map[closest_env]
        
        # Check label prefix as a fallback
        following_text = content[position:min(len(content), position + 100)]
        label_match = re.search(r'\\label\{([^}]+)\}', following_text)
        if label_match:
            label_name = label_match.group(1)
            if label_name.startswith('fig:'):
                return 'figure'
            elif label_name.startswith('tab:'):
                return 'table'
            elif label_name.startswith('sec:'):
                return 'section'
            elif label_name.startswith('eq:'):
                return 'equation'
            elif label_name.startswith('lst:'):
                return 'listing'
        
        # Default to unknown
        return 'unknown'
    
    def _extract_references(self, content: str) -> None:
        r"""Extract all \ref{} and \eqref{} commands"""
        # Pattern to match \ref{}, \eqref{}, \autoref{}, \cref{}, etc.
        ref_pattern = r'\\(eq)?ref\{([^}]+)\}'
        
        for match in re.finditer(ref_pattern, content):
            ref_type = 'eqref' if match.group(1) else 'ref'
            ref_name = match.group(2)
            
            self.references.append({
                'ref': ref_name,
                'type': ref_type,
                'position': match.start()
            })
        
        # Also match \autoref{} and \cref{} variants
        autoref_pattern = r'\\(autoref|cref|Cref)\{([^}]+)\}'
        
        for match in re.finditer(autoref_pattern, content):
            ref_type = match.group(1)
            ref_name = match.group(2)
            
            self.references.append({
                'ref': ref_name,
                'type': ref_type,
                'position': match.start()
            })
    
    def _report_labels_and_refs(self) -> None:
        """Report on labels and references found"""
        print("\n" + "="*60)
        print("LABEL AND REFERENCE SUMMARY")
        print("="*60)
        
        # Group labels by type
        labels_by_type = {}
        for label, info in self.labels.items():
            label_type = info['type']
            if label_type not in labels_by_type:
                labels_by_type[label_type] = []
            labels_by_type[label_type].append(label)
        
        # Print labels by type
        print("\nLabels found:")
        for label_type in sorted(labels_by_type.keys()):
            labels = labels_by_type[label_type]
            print(f"  {label_type}: {len(labels)}")
            for label in sorted(labels):
                print(f"    - {label}")
        
        # Check for undefined references
        print("\nReference validation:")
        undefined_refs = []
        for ref_info in self.references:
            ref_name = ref_info['ref']
            if ref_name not in self.labels:
                undefined_refs.append(ref_info)
        
        if undefined_refs:
            print(f"  WARNING: {len(undefined_refs)} undefined reference(s):")
            for ref_info in undefined_refs:
                print(f"    - \\{ref_info['type']}{{{ref_info['ref']}}}")
        else:
            print(f"  All {len(self.references)} references are defined ✓")
        
        # Check for unused labels
        referenced_labels = set(ref_info['ref'] for ref_info in self.references)
        unused_labels = set(self.labels.keys()) - referenced_labels
        
        if unused_labels:
            print(f"\n  WARNING: {len(unused_labels)} unused label(s):")
            for label in sorted(unused_labels):
                label_type = self.labels[label]['type']
                print(f"    - {label} ({label_type})")
        else:
            print(f"\n  All {len(self.labels)} labels are referenced ✓")
        
        print("="*60 + "\n")
    
    def get_label_stats(self) -> Dict[str, Any]:
        """Get statistics about labels and references"""
        # Group labels by type
        labels_by_type = {}
        for label, info in self.labels.items():
            label_type = info['type']
            if label_type not in labels_by_type:
                labels_by_type[label_type] = []
            labels_by_type[label_type].append(label)
        
        # Find undefined references
        undefined_refs = []
        for ref_info in self.references:
            ref_name = ref_info['ref']
            if ref_name not in self.labels:
                undefined_refs.append(ref_info)
        
        # Find unused labels
        referenced_labels = set(ref_info['ref'] for ref_info in self.references)
        unused_labels = set(self.labels.keys()) - referenced_labels
        
        return {
            'total_labels': len(self.labels),
            'total_references': len(self.references),
            'labels_by_type': labels_by_type,
            'undefined_references': undefined_refs,
            'unused_labels': list(unused_labels),
            'all_labels': self.labels,
            'all_references': self.references
        }
    
    def _process_bibliography(self, content: str) -> str:
        """Process bibliography: extract citations and inline bibliography"""
        # Find bibliography file
        bib_match = re.search(r'\\bibliography\s*\{([^}]+)\}', content)
        if not bib_match:
            print("No \\bibliography command found")
            return content
            
        bib_filename = bib_match.group(1)
        if not bib_filename.endswith('.bib'):
            bib_filename += '.bib'
            
        self.bib_file = self.base_dir / bib_filename
        if not self.bib_file.exists():
            print(f"Warning: Bibliography file not found: {self.bib_file}")
            return content
        
        # Extract all citation keys
        self._extract_citation_keys(content)
        
        # Parse bibliography
        bib_entries = self._parse_bib_file()
        
        # Filter and convert to \bibitem
        bibitem_content = self._create_bibitem_content(bib_entries)
        
        # Replace \bibliography with \begin{thebibliography}
        bibliography_replacement = f"""\\begin{{thebibliography}}{{99}}
{bibitem_content}
\\end{{thebibliography}}"""
        
        # Remove \bibliographystyle if present
        content = re.sub(r'\\bibliographystyle\s*\{[^}]+\}\s*', '', content)
        
        # Replace \bibliography - escape backslashes for regex replacement
        escaped_replacement = bibliography_replacement.replace('\\', r'\\')
        content = re.sub(r'\\bibliography\s*\{[^}]+\}', escaped_replacement, content)
        
        return content
    
    def _extract_citation_keys(self, content: str) -> None:
        """Extract all citation keys from the content in order of appearance"""
        # Clear existing keys but preserve order
        self.cited_keys = []  # Change to list to preserve order
        seen_keys = set()     # Track what we've seen to avoid duplicates
        
        # Match various citation commands: \cite{}, \citep{}, \citet{}, etc.
        cite_pattern = r'\\cite[pt]?\*?\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}'
        
        for match in re.finditer(cite_pattern, content):
            keys = match.group(1)
            # Split by comma and clean up
            for key in keys.split(','):
                key = key.strip()
                if key and key not in seen_keys:
                    self.cited_keys.append(key)
                    seen_keys.add(key)
    
    def _parse_bib_file(self) -> Dict[str, Dict[str, str]]:
        """Parse the .bib file and return entries as dictionaries"""
        try:
            with open(self.bib_file, 'r', encoding='utf-8') as f:
                bib_content = f.read()
        except UnicodeDecodeError:
            with open(self.bib_file, 'r', encoding='latin-1') as f:
                bib_content = f.read()
        return self._parse_bib_entries(bib_content)

    def _parse_bib_entries(self, bib_content: str) -> Dict[str, Dict[str, str]]:        
        entries = {}
        
        # Pattern to match BibTeX entries
        entry_pattern = r'@(\w+)\s*\{\s*([^,\s]+)\s*,\s*(.*?)\n\s*\}'
        
        for match in re.finditer(entry_pattern, bib_content, re.DOTALL):
            entry_type = match.group(1).lower()
            key = match.group(2)
            fields_str = match.group(3)
            
            # Parse fields
            fields = {'entry_type': entry_type}
            
            # Parse fields using a proper brace-counting approach
            i = 0
            while i < len(fields_str):
                # Skip whitespace and commas
                while i < len(fields_str) and fields_str[i] in ' \t\n,':
                    i += 1
                if i >= len(fields_str):
                    break
                
                # Find field name
                field_start = i
                while i < len(fields_str) and fields_str[i] not in '=':
                    i += 1
                if i >= len(fields_str):
                    break
                
                field_name = fields_str[field_start:i].strip().lower()
                
                # Skip '=' and whitespace
                while i < len(fields_str) and fields_str[i] in '= \t\n':
                    i += 1
                if i >= len(fields_str) or fields_str[i] != '{':
                    continue
                
                # Parse field value with proper brace counting
                i += 1  # Skip opening brace
                value_start = i
                brace_count = 1
                
                while i < len(fields_str) and brace_count > 0:
                    if fields_str[i] == '{':
                        brace_count += 1
                    elif fields_str[i] == '}':
                        brace_count -= 1
                    i += 1
                
                if brace_count == 0:
                    field_value = fields_str[value_start:i-1].strip()
                    # Clean up field value
                    field_value = re.sub(r'\s+', ' ', field_value)
                    fields[field_name] = field_value
            
            entries[key] = fields
        
        return entries
    
    def _create_bibitem_content(self, bib_entries: Dict[str, Dict[str, str]]) -> str:
        """Convert filtered bibliography entries to \bibitem format in APA style"""
        bibitem_lines = []
        
        # for key in sorted(self.cited_keys):
        for key in self.cited_keys:
            if key in bib_entries:
                entry = bib_entries[key]
                bibitem_line = self._format_apa_bibitem(key, entry)
                bibitem_lines.append(bibitem_line)
            else:
                print(f"Warning: Citation key '{key}' not found in bibliography")
                bibitem_lines.append(f"\\bibitem{{{key}}} % Citation not found: {key}")
        
        return '\n\n'.join(bibitem_lines)

    def _format_authors_short(self, author, year): 
        """Format author names in short format with year.

        1 name: lastname
        2 names: lastname1 and lastname2
        3+ names: lastname et. al.
        """

        if not author:
            return ""
        
        # Split authors by ' and '
        authors = [a.strip() for a in author.split(' and ')]
        
        # Extract last names from author names
        last_names = []
        for auth in authors:
            # Handle "Lastname, Firstname" format
            if ',' in auth:
                last_name = auth.split(',')[0].strip()
            else:
                # Handle "Firstname Lastname" format
                parts = auth.split()
                last_name = parts[-1] if parts else ""
            last_names.append(last_name)
        
        # Format based on number of authors
        if len(last_names) == 1:
            short_author = f"{last_names[0]}({year})"
        elif len(last_names) == 2:
            short_author = f"{last_names[0]} and {last_names[1]}({year})"
        else:  # 3 or more
            short_author = f"{last_names[0]} et. al.({year})"
        
        return short_author


    def _format_apa_bibitem(self, key: str, entry: Dict[str, str]) -> str:
        """Format a single bibliography entry in APA style"""
        entry_type = entry.get('entry_type', '')
        
        # Extract common fields
        author = entry.get('author', '')
        title = entry.get('title', '')
        year = entry.get('year', '')
        doi = entry.get('doi', '')

        # Clean up author names - convert "Last, First and Last2, First2" to "Last, F. & Last2, F."
        if author:
            short_author = self._format_authors_short(author, year)
            author = self._format_authors_apa(author)
        
        # Clean up title - remove extra braces
        if title:
            title = re.sub(r'\{([^{}]*)\}', r'\1', title)
    
        # Start building the \bibitem entry, generics first
        if author:
            result = f"\\bibitem[{short_author}]{{{key}}} {author} "
        else:
            result = f"\\bibitem{{{key}}}"
        if year:
            result += f"({year}). "

        if entry_type == 'article':
            journal = entry.get('journal', '')
            volume = entry.get('volume', '')
            number = entry.get('number', '')
            pages = entry.get('pages', '')
            
            # Format: Author (Year). Title. Journal, Volume(Number), pages.
            if title:
                result += f"{title}. "
            if journal:
                result += f" \\textit{{{journal}}}"
                if volume:
                    result += f", {volume}"
                    if number:
                        result += f"({number})"
                if pages:
                    result += f", {pages}"
                result += "."

        elif entry_type == 'book':
            publisher = entry.get('publisher', '')
            address = entry.get('address', '')
            
            # Format: Author (Year). Title. Publisher.
            if title:
                result += f"\\textit{{{title}}}. "            
            if publisher:
                result += f" {publisher}"
                if address:
                    result += f": {address}"
                result += "."
                
        elif entry_type == 'inproceedings' or entry_type == 'conference' or entry_type == 'incollection':
            booktitle = entry.get('booktitle', '')
            pages = entry.get('pages', '')
            
            if title:
                result += f"{title}. "            
            if booktitle:
                result += f"In \\textit{{{booktitle}}}"
                if pages:
                    result += f" (pp. {pages})"
                result += "."
                
        elif entry_type == 'techreport':
            # Format: Author (Year). Title. Institution.
            if title:
                result += f"{title}."
            result += " Technical Report"
            institution = entry.get('institution', '')
            if institution:
                result += f", {institution}"
            result += "."

        if doi:
            # Clean up DOI - unescape underscores that might be escaped in BibTeX
            doi_cleaned = doi.replace(r'{\_}', '_').replace(r'{\\_}', '_')
            result += f" \\url{{https://doi.org/{doi_cleaned}}}."   

        return result
    
    def _format_authors_apa(self, author_str: str) -> str:
        """Format author names in APA style"""
        # Split by 'and'
        authors = re.split(r'\s+and\s+', author_str)
        formatted_authors = []
        
        for author in authors:
            author = author.strip()
            if ',' in author:
                # Format: "Last, First Middle" -> "Last, F. M."
                parts = author.split(',', 1)
                last_name = parts[0].strip()
                first_names = parts[1].strip() if len(parts) > 1 else ''
                
                if first_names:
                    # Extract initials
                    initials = []
                    for name in first_names.split():
                        if name and name[0].isalpha():
                            initials.append(f"{name[0].upper()}.")
                    
                    if initials:
                        formatted_authors.append(f"{last_name}, {' '.join(initials)}")
                    else:
                        formatted_authors.append(last_name)
                else:
                    formatted_authors.append(last_name)
            else:
                # Assume "First Last" format
                names = author.split()
                if len(names) >= 2:
                    last_name = names[-1]
                    first_names = names[:-1]
                    initials = [f"{name[0].upper()}." for name in first_names if name and name[0].isalpha()]
                    if initials:
                        formatted_authors.append(f"{last_name}, {' '.join(initials)}")
                    else:
                        formatted_authors.append(last_name)
                else:
                    formatted_authors.append(author)
        
        # Join with & for APA style
        if len(formatted_authors) == 1:
            return formatted_authors[0]
        elif len(formatted_authors) == 2:
            return f"{formatted_authors[0]} \\& {formatted_authors[1]}"
        else:
            return ', '.join(formatted_authors[:-1]) + f", \\& {formatted_authors[-1]}"


def main():
    parser = argparse.ArgumentParser(description='Process LaTeX files by inlining includes and bibliography')
    parser.add_argument('input_file', nargs='?', default='main.tex', help='Main LaTeX file to process (default: main.tex)')
    parser.add_argument('-o', '--output', default='onefile.tex', help='Output file (default: onefile.tex)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found")
        sys.exit(1)
    
    try:
        processor = LaTeXProcessor(args.input_file, args.output)
        processor.process()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()