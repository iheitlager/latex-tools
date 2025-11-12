#!/usr/bin/env python3
"""
LaTeX Diff Parser
Compares two LaTeX files and creates a color-coded diff document.
Red: removed content from first file
Blue: added content in second file
"""

import difflib
from pathlib import Path
from typing import List


def tokenize_latex(text: str) -> List[str]:
    """Split LaTeX into meaningful tokens.
    
    Token types:
    - LaTeX commands with all arguments: \textbf{...}, \def\cmd{...}
    - Single braces/brackets: { } [ ]
    - Words (alphanumeric sequences)
    - Whitespace (preserved)
    - Punctuation and special characters
    """
    import re
    # Order matters! Try to match longer patterns first
    pattern = r'''
        \\[a-zA-Z]+\*?                    # LaTeX command (e.g., \textbf, \section*)
        |\\[^a-zA-Z]                       # Single-char commands (e.g., \\, \&, \{)
        |[\{\}\[\]]                        # Braces and brackets (separate tokens)
        |\w+                               # Words (letters, digits, underscore)
        |[ \t]+                            # Horizontal whitespace (keep together)
        |%[^\n]*\n                         # Comments (% to end of line)
        |\n                                # Newlines (separate token)
        |[^\w\s\\{}\[\]%]+                 # Punctuation/special chars
        '''
    return re.findall(pattern, text, re.VERBOSE)


def is_specific(segment: List[str]) -> bool:
    if len(segment) == 0:
        return False
    elif segment[0][0] == "%":
        return True
    elif segment[0].startswith("\\label"):
        return True
    elif segment[0].startswith("\\ref"):
        return True
    else:
        return False

def group_latex_commands(tokens: List[str]) -> List[str]:
    """
    Group ONLY formatting LaTeX commands with their arguments into single tokens.
    E.g., ['\\textbf', '{', 'text', '}'] becomes ['\\textbf{text}']
    
    This helps the matcher see '\textbf{asset-intensive industries}' as a unit
    rather than separate tokens, which causes it to be recognized as a REPLACEMENT
    of plain text with formatted text.
    
    Only groups these formatting commands:
    - Text formatting: textbf, textit, texttt, textsc, emph, underline, etc.
    - Font commands: bf, it, tt, sc, rm, sf
    - Size commands: tiny, small, large, Large, LARGE, huge, Huge
    """
    # Commands that should be grouped with their arguments
    FORMATTING_COMMANDS = {
        'textbf', 'textit', 'texttt', 'textsc', 'textrm', 'textsf',
        'emph', 'underline', 'textsl', 'textmd', 'textup',
        'bf', 'it', 'tt', 'sc', 'rm', 'sf', 'sl', 'md', 'up',
        'tiny', 'scriptsize', 'footnotesize', 'small', 'normalsize',
        'large', 'Large', 'LARGE', 'huge', 'Huge',
        'textcolor', 'color', 'colorbox',
        'label', 'ref'
        'cite', 'citep', 'citet'
    }
    
    result = []
    i = 0
    
    while i < len(tokens):
        token = tokens[i]
        
        # Check if this is a formatting command followed by braces
        if token.startswith('\\') and len(token) > 1:
            cmd_name = token[1:]  # Remove the backslash
            
            # Only group if it's a formatting command
            if cmd_name in FORMATTING_COMMANDS and i + 1 < len(tokens) and tokens[i + 1] == '{':
                # Find matching closing brace
                brace_count = 0
                group = [token]
                j = i + 1
                
                while j < len(tokens):
                    group.append(tokens[j])
                    if tokens[j] == '{':
                        brace_count += 1
                    elif tokens[j] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # Found complete command with arguments
                            result.append(''.join(group))
                            i = j + 1
                            break
                    j += 1
                else:
                    # No matching brace found, just add the command
                    result.append(token)
                    i += 1
            else:
                # Not a formatting command, or no braces - add as-is
                result.append(token)
                i += 1
        else:
            # Not a command, add as-is
            result.append(token)
            i += 1
    
    return result

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

    
    def diff_lines(self, old_line: str, new_line: str) -> str:
        """Generate inline diff for two lines."""

        old_tokens_raw = tokenize_latex(old_line)
        new_tokens_raw = tokenize_latex(new_line)

        old_tokens_grouped = group_latex_commands(old_tokens_raw)
        new_tokens_grouped = group_latex_commands(new_tokens_raw)
    
    
        matcher = difflib.SequenceMatcher(None, old_tokens_grouped, new_tokens_grouped)
        output_tokens = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            old_segment = old_tokens_grouped[i1:i2]
            new_segment = new_tokens_grouped[j1:j2]
            
            if tag == 'equal':
                output_tokens.extend(old_segment)
            elif is_specific(old_segment):
                if tag == 'replace' or tag == 'insert':
                    output_tokens.extend(new_segment)
            elif tag == 'delete':
                output_tokens.append('\\odiff{' + ''.join(old_segment) + '}')
            elif tag == 'replace':
                if new_segment[0] == " ":
                    output_tokens.append('\\odiff{' + ''.join(old_segment) + '} \\ndiff{' + ''.join(new_segment[1:]) + '}')
                else:
                    output_tokens.append('\\odiff{' + ''.join(old_segment) + '}\\ndiff{' + ''.join(new_segment) + '}')
            elif tag == 'insert':
                if new_segment[0] == " ":
                    output_tokens.append(' \\ndiff{' + ''.join(new_segment[1:]) + '}')
                else:
                    output_tokens.append('\\ndiff{' + ''.join(new_segment) + '}')
        
        return ''.join(output_tokens)
        
    def create_diff_document(self):
        """Create inline diff document."""
        text_old = self.read_file(self.file1_path)
        text_new = self.read_file(self.file2_path)
        
        old_lines = text_old.splitlines(keepends=False)
        new_lines = text_new.splitlines(keepends=False)  
       
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

        # Now compare with grouped tokens
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)    
        # Generate output
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            old_segment = old_lines[i1:i2]
            new_segment = new_lines[j1:j2]
            
            if tag == 'equal':
                output_lines.extend([line + '\n' for line in old_segment ])
                line_count += len(old_segment)
            elif tag == 'delete':
                output_lines.append('\\old{' + ''.join([line + '\n' for line in old_segment ]) + '}\n')
                line_count += len(old_segment)
            elif tag == 'replace':
                # Process each line pair for inline diffs
                max_lines = max(len(old_segment), len(new_segment))
                for k in range(max_lines):
                    old_line = old_segment[k] if k < len(old_segment) else ""
                    new_line = new_segment[k] if k < len(new_segment) else ""
                    diffed_line = self.diff_lines(old_line, new_line)
                    output_lines.append(diffed_line + '\n')
                    line_count += 1
            elif tag == 'insert':
                output_lines.append('\\new{' + ''.join([line + '\n' for line in new_segment ]) + '}\n')
                line_count += len(new_segment)
        
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
