#!/usr/bin/env python3
"""
LaTeX Diff Parser
Compares two LaTeX files and creates a color-coded diff document.
Red: removed content from first file
Blue: added content in second file
"""

import difflib
import re
from pathlib import Path
from typing import List, Tuple


class LatexDiffParser:
    """Parser for comparing two LaTeX documents and generating colored diff."""
    
    def __init__(self, file1_path: str, file2_path: str, output_path: str):
        self.file1_path = Path(file1_path)
        self.file2_path = Path(file2_path)
        self.output_path = Path(output_path)
        
    def read_file(self, filepath: Path) -> List[str]:
        """Read a file and return its lines."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.readlines()
    
    def escape_latex_special_chars(self, text: str) -> str:
        """Escape special LaTeX characters for safe inclusion in output."""
        # Don't escape if it's already a command
        if text.startswith('\\'):
            return text
        # Basic escaping for text content
        replacements = {
            '\\': r'\textbackslash{}',
            '{': r'\{',
            '}': r'\}',
            '$': r'\$',
            '&': r'\&',
            '%': r'\%',
            '#': r'\#',
            '_': r'\_',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    
    def wrap_with_color(self, text: str, color: str) -> str:
        """Wrap text with LaTeX color command."""
        if not text.strip():
            return text
        return f"\\textcolor{{{color}}}{{{text}}}"
    
    def generate_diff(self) -> List[str]:
        """Generate diff between two files."""
        lines1 = self.read_file(self.file1_path)
        lines2 = self.read_file(self.file2_path)
        
        # Use difflib to compute differences
        differ = difflib.Differ()
        diff = list(differ.compare(lines1, lines2))
        
        output_lines = []
        
        for line in diff:
            if line.startswith('  '):  # Unchanged line
                output_lines.append(line[2:])
            elif line.startswith('- '):  # Removed line (red)
                content = line[2:].rstrip('\n')
                if content.strip():  # Only add if not empty
                    colored_line = self.wrap_with_color(content, 'red')
                    output_lines.append(colored_line + '\n')
            elif line.startswith('+ '):  # Added line (blue)
                content = line[2:].rstrip('\n')
                if content.strip():  # Only add if not empty
                    colored_line = self.wrap_with_color(content, 'blue')
                    output_lines.append(colored_line + '\n')
            elif line.startswith('? '):  # Hint line (ignore)
                continue
                
        return output_lines
    
    def create_diff_document(self):
        """Create the complete diff LaTeX document."""
        diff_lines = self.generate_diff()
        
        # Create a complete LaTeX document with color package
        header = [
            "\\documentclass{article}\n",
            "\\usepackage[utf8]{inputenc}\n",
            "\\usepackage{xcolor}\n",
            "\\usepackage[margin=1in]{geometry}\n",
            "\\usepackage{listings}\n",
            "\\lstset{basicstyle=\\ttfamily\\small, breaklines=true}\n",
            "\n",
            "\\title{LaTeX Diff: single\\_file.tex vs onefile.tex}\n",
            "\\author{Diff Parser}\n",
            "\\date{\\today}\n",
            "\n",
            "\\begin{document}\n",
            "\\maketitle\n",
            "\n",
            "\\section*{Color Legend}\n",
            "\\textcolor{red}{Red text indicates content removed from single\\_file.tex}\n",
            "\\\\\n",
            "\\textcolor{blue}{Blue text indicates content added in onefile.tex}\n",
            "\\\\\n",
            "Black text indicates unchanged content\n",
            "\n",
            "\\section*{Differences}\n",
            "\\begin{lstlisting}[escapechar=@]\n"
        ]
        
        footer = [
            "\\end{lstlisting}\n",
            "\\end{document}\n"
        ]
        
        # Write output
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.writelines(header)
            
            # Write diff content with proper escaping for lstlisting
            for line in diff_lines:
                # If line contains color commands, escape them for lstlisting
                if '\\textcolor' in line:
                    # Use escape character @ to embed LaTeX commands
                    line = line.replace('\\textcolor', '@\\textcolor')
                    line = line.replace('}}\n', '}}@\n')
                    line = line.replace('}}', '}}@')
                f.write(line)
            
            f.writelines(footer)
        
        print(f"Diff document created: {self.output_path}")
        print(f"\nTo compile:")
        print(f"  pdflatex {self.output_path}")


class LatexInlineDiffParser:
    """Parser that creates inline diffs showing changes within lines."""
    
    def __init__(self, file1_path: str, file2_path: str, output_path: str):
        self.file1_path = Path(file1_path)
        self.file2_path = Path(file2_path)
        self.output_path = Path(output_path)
        
    def read_file(self, filepath: Path) -> str:
        """Read entire file as string."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def compare_words_inline(self, line1: str, line2: str) -> str:
        """Compare two similar lines word-by-word and create TRUE inline diff with grouped macros."""
        words1 = line1.split()
        words2 = line2.split()
        
        matcher = difflib.SequenceMatcher(None, words1, words2)
        result = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Unchanged words - add as-is (no wrapper)
                result.extend(words1[i1:i2])
            elif tag == 'delete':
                # Group all removed words into single \odiff
                deleted_text = ' '.join(words1[i1:i2])
                result.append(f'\\odiff{{{deleted_text}}}')
            elif tag == 'insert':
                # Group all added words into single \ndiff
                inserted_text = ' '.join(words2[j1:j2])
                result.append(f'\\ndiff{{{inserted_text}}}')
            elif tag == 'replace':
                # Group old words in one \odiff, new words in one \ndiff
                deleted_text = ' '.join(words1[i1:i2])
                inserted_text = ' '.join(words2[j1:j2])
                result.append(f'\\odiff{{{deleted_text}}}')
                result.append(f'\\ndiff{{{inserted_text}}}')
        
        return ' '.join(result)
    
    def lines_are_similar(self, line1: str, line2: str, threshold=0.5) -> bool:
        """Check if two lines are similar enough to do inline diff."""
        matcher = difflib.SequenceMatcher(None, line1, line2)
        return matcher.ratio() > threshold
    
    def create_diff_document(self):
        """Create inline diff document."""
        text1 = self.read_file(self.file1_path)
        text2 = self.read_file(self.file2_path)
        
        lines1 = text1.splitlines(keepends=False)
        lines2 = text2.splitlines(keepends=False)
        
        # Use SequenceMatcher for line-level comparison
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        
        # Start with just the macro definitions - no document wrapper
        output_lines = [
            "% LaTeX Diff Macros - Add these at the top of your document\n",
            "% \\usepackage{xcolor}\n",
            "% \\usepackage{soul}\n",
            "% \\usepackage{ulem}\n",
            "\\newcommand{\\odiff}[1]{\\textcolor{red}{\\sout{#1}}} % Old text: red + strikethrough\n",
            "\\newcommand{\\ndiff}[1]{\\textcolor{green!60!black}{#1}} % New text: green\n",
            "\n",
        ]
        
        line_count = 0
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Unchanged lines - always output them
                for line in lines1[i1:i2]:
                    if line.strip():
                        output_lines.append(line + "\n")
                line_count += (i2 - i1)
                        
            elif tag == 'delete':
                # Completely removed lines - group entire line in one macro
                for line in lines1[i1:i2]:
                    if line.strip():
                        output_lines.append(f'\\odiff{{{line}}}\n')
                line_count += (i2 - i1)
                        
            elif tag == 'insert':
                # Completely new lines - group entire line in one macro
                for line in lines2[j1:j2]:
                    if line.strip():
                        output_lines.append(f'\\ndiff{{{line}}}\n')
                line_count += (j2 - j1)
                        
            elif tag == 'replace':
                # Lines that changed - ALWAYS try inline diff for single line changes
                if i2 - i1 == 1 and j2 - j1 == 1:
                    # Single line to single line - do inline word-level diff
                    inline_diff = self.compare_words_inline(lines1[i1], lines2[j1])
                    output_lines.append(inline_diff + "\n")
                else:
                    # Multiple lines changed - pair them up and do inline diff where possible
                    # First process common length
                    common_len = min(i2 - i1, j2 - j1)
                    for idx in range(common_len):
                        if self.lines_are_similar(lines1[i1 + idx], lines2[j1 + idx]):
                            inline_diff = self.compare_words_inline(lines1[i1 + idx], lines2[j1 + idx])
                            output_lines.append(inline_diff + "\n")
                        else:
                            # Lines too different - show separately with entire line in one macro
                            line1 = lines1[i1 + idx]
                            line2 = lines2[j1 + idx]
                            if line1.strip():
                                output_lines.append(f'\\odiff{{{line1}}}\n')
                            if line2.strip():
                                output_lines.append(f'\\ndiff{{{line2}}}\n')
                    
                    # Handle any extra lines from file 1
                    for idx in range(common_len, i2 - i1):
                        line = lines1[i1 + idx]
                        if line.strip():
                            output_lines.append(f'\\odiff{{{line}}}\n')
                    
                    # Handle any extra lines from file 2
                    for idx in range(common_len, j2 - j1):
                        line = lines2[j1 + idx]
                        if line.strip():
                            output_lines.append(f'\\ndiff{{{line}}}\n')
                
                line_count += max(i2 - i1, j2 - j1)
        
        # Write output - no closing document tag
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.writelines(output_lines)
        
        print(f"Inline diff document created: {self.output_path}")
        print(f"Total lines processed: {line_count}")
        print(f"\nMacros defined:")
        print(f"  \\odiff{{text}} - Red strikethrough for removed text")
        print(f"  \\ndiff{{text}} - Green for added text")
        print(f"\nTo compile:")
        print(f"  pdflatex {self.output_path}")


def main():
    """Main function to run the diff parser."""
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python latex_diff_parser.py <file1> <file2> <output>")
        print("\nExample:")
        print("  python latex_diff_parser.py single_file.tex onefile.tex diff_output.tex")
        sys.exit(1)
    
    file1 = sys.argv[1]
    file2 = sys.argv[2]
    output = sys.argv[3]
    
    print(f"Comparing:")
    print(f"  File 1: {file1}")
    print(f"  File 2: {file2}")
    print(f"  Output: {output}")
    print()
    
    # Use the inline diff parser
    parser = LatexInlineDiffParser(file1, file2, output)
    parser.create_diff_document()
    
    print("\nDone! You can now compile the diff document with pdflatex.")


if __name__ == "__main__":
    main()
