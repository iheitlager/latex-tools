import subprocess
import sys


def test_make_pdf_help():
    # Should print usage and exit 0
    result = subprocess.run(
        [sys.executable, "-m", "latex_tools.cli.make_pdf", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Compile LaTeX to PDF" in result.stdout
    assert "LaTeX source file" in result.stdout


def test_make_pdf_missing_file():
    # Should print error and exit 1
    result = subprocess.run(
        [sys.executable, "-m", "latex_tools.cli.make_pdf", "nonexistent_file.tex"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert (
        "Error: File 'nonexistent_file.tex' not found" in result.stdout or result.stderr
    )
