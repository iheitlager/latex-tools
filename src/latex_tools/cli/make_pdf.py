#!/usr/bin/env python3
"""
A LaTeX PDF compilation wrapper in Python that mimics the shell script make-pdf.
Handles pdflatex, bibliography generation, cleanup, multiple passes, error reporting, and PDF opening.

Copyright (c) 2025 - Ilja Heitlager
SPDX-License-Identifier: Apache-2.0
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

from latex_tools import __version__


def check_command(cmd: str):
    import shutil

    if shutil.which(cmd) is None:
        print(f"❌ Error: {cmd} not found")
        sys.exit(1)


def show_latex_errors(logfile: str):
    if not Path(logfile).is_file():
        print(f"❌ No log file found at: {logfile}")
        return
    print("\n📋 LaTeX Error Details:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    with open(logfile, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    error_lines = [i for i, line in enumerate(lines) if line.startswith("!")]
    if error_lines:
        for idx in error_lines[:3]:
            print("".join(lines[max(0, idx - 1) : idx + 4]))
    else:
        print("".join(lines[-20:]))
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"💡 Full log file: {logfile}")


from typing import List


def run_command(cmd: List[str], verbose: bool) -> int:
    if verbose:
        return subprocess.call(cmd)
    else:
        return subprocess.call(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )


def run_bibliography(bibengine: str, bibfile: str, verbose: bool) -> bool:
    print(f"🔄 Running {bibengine} for bibliography...")
    result = run_command([bibengine, bibfile], verbose)
    if result == 0:
        print(f"✅ {bibengine} completed")
        return True
    else:
        print(f"❌ {bibengine} failed")
        return False


def open_pdf(pdffile: str):
    if not Path(pdffile).is_file():
        print("⚠️  Warning: PDF file not found")
        return
    print(f"📁 PDF file size: {os.path.getsize(pdffile) // 1024} KB")
    if sys.platform == "darwin":
        subprocess.call(["open", pdffile])
    elif sys.platform.startswith("linux"):
        subprocess.call(["xdg-open", pdffile])
    else:
        print("⚠️  Could not detect PDF viewer to open file")


def cleanup_files(basename: str, outdir: str, keeplog: bool):
    print("🧹 Cleaning up auxiliary files...")
    exts = [
        "aux",
        "bbl",
        "bcf",
        "run.xml",
        "blg",
        "out",
        "toc",
        "lof",
        "lot",
        "fls",
        "fdb_latexmk",
        "synctex.gz",
    ]
    if not keeplog:
        exts.append("log")
    for ext in exts:
        f = Path(outdir) / f"{basename}.{ext}" if outdir else Path(f"{basename}.{ext}")
        if f.exists():
            f.unlink()
    print("✅ Cleanup completed" + (" (log files preserved)" if keeplog else ""))


def main():
    parser = argparse.ArgumentParser(
        description="Compile LaTeX to PDF with bibliography and cleanup.",
        usage="make-pdf [--version] [-crvbxl] [-o DIR] [-p N] [--keeplog] filename ...",
    )
    parser.add_argument("filename", nargs="?", help="LaTeX source file (.tex)")
    parser.add_argument(
        "-c",
        "--continue_on_error",
        action="store_true",
        help="Continue compilation even if bibliography has errors",
    )
    parser.add_argument(
        "-r",
        "--clean",
        action="store_true",
        help="Clean auxiliary files after compilation",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show stderr output (for debugging)",
    )
    parser.add_argument(
        "-o", "--outdir", default="", help="Output directory for PDF and aux files"
    )
    parser.add_argument(
        "-b", "--bibtex", action="store_true", help="Use bibtex instead of biber"
    )
    parser.add_argument(
        "-p",
        "--passes",
        type=int,
        default=3,
        help="Number of pdflatex passes (default: 3)",
    )
    parser.add_argument(
        "-x",
        "--open",
        action="store_true",
        help="Open PDF after successful compilation",
    )
    parser.add_argument(
        "-l",
        "--showlog",
        action="store_true",
        help="Show last 20 lines of .log file on error",
    )
    parser.add_argument(
        "--keeplog", action="store_true", help="Don't delete .log files during cleanup"
    )
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    args = parser.parse_args()

    if args.version:
        print(f"latex-tools version: {__version__}")
        sys.exit(0)

    filename = args.filename
    if not filename:
        parser.print_usage()
        sys.exit(2)

    basename = Path(filename).stem
    outdir = args.outdir
    bibengine = "bibtex" if args.bibtex else "biber"
    passes = args.passes
    verbose = args.verbose
    keeplog = args.keeplog

    if not Path(filename).is_file():
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    check_command("pdflatex")
    check_command(bibengine)

    if outdir:
        Path(outdir).mkdir(parents=True, exist_ok=True)
        outdir_arg = f"-output-directory={outdir}"
    else:
        outdir_arg = ""

    print(f"📄 Compiling LaTeX document: {filename}")
    if outdir:
        print(f"📁 Output directory: {outdir}")
    print(f"🔧 Bibliography engine: {bibengine}")
    print(f"🔄 Number of passes: {passes}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # First pdflatex run
    if (
        run_command(
            ["pdflatex", outdir_arg, filename]
            if outdir_arg
            else ["pdflatex", filename],
            verbose,
        )
        != 0
    ):
        if args.showlog:
            logf = Path(outdir) / f"{basename}.log" if outdir else f"{basename}.log"
            show_latex_errors(str(logf))
        sys.exit(1)
    # Bibliography
    bibfile = Path(outdir) / basename if outdir else basename
    if (
        not run_bibliography(bibengine, str(bibfile), verbose)
        and not args.continue_on_error
    ):
        sys.exit(1)
    # Additional pdflatex runs
    for i in range(2, passes + 1):
        if (
            run_command(
                ["pdflatex", outdir_arg, filename]
                if outdir_arg
                else ["pdflatex", filename],
                verbose,
            )
            != 0
        ):
            if args.showlog:
                logf = Path(outdir) / f"{basename}.log" if outdir else f"{basename}.log"
                show_latex_errors(str(logf))
            sys.exit(1)
    pdffile = Path(outdir) / f"{basename}.pdf" if outdir else f"{basename}.pdf"
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🎉 Compilation complete! Output: {pdffile}")
    if args.open:
        open_pdf(str(pdffile))
    if args.clean:
        cleanup_files(basename, outdir, keeplog)
    print("🏁 Done!")


if __name__ == "__main__":
    main()
