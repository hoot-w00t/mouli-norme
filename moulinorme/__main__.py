
"""
MIT License

Copyright (c) 2019-2020 akrocynova

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import sys
import pathlib
import re
from argparse import ArgumentParser
import moulinorme
from moulinorme.types import TermStyle

def explore_path(target: pathlib.Path, recursive=False):
    """Explore paths add return a list of files found"""
    targets = list()

    if target.is_dir():
        for sub in target.iterdir():
            if sub.name.startswith("."):
                continue

            if sub.is_dir():
                if recursive:
                    targets += explore_path(sub, recursive)
            else:
                targets.append(sub)

    else:
        targets.append(target)

    return targets

def main():
    arg_parser = ArgumentParser(description=f"Moulinorme {moulinorme.__version__}")
    arg_parser.add_argument("-V", "--version", dest="version", action="store_true", help="Display Moulinorme version")
    arg_parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Increase verbosity")
    arg_parser.add_argument("-n", "--no-color", dest="no_color", action="store_true", help="Don't colorize output")
    arg_parser.add_argument("-u", "--unnecessary", dest="unnecessary", action="store_true", help="Handle unnecessary files")
    arg_parser.add_argument("-r", "--recursive", dest="recursive", action="store_true", help="Recursively list subdirectories")
    arg_parser.add_argument("-d", "--delivery", dest="delivery", action="store_true", help="Delivery check, equivalent to -ur")
    arg_parser.add_argument(dest="files", nargs="*", default=list(), help="Files/folders to check")
    args = arg_parser.parse_args()

    if args.delivery:
        args.unnecessary = True
        args.recursive = True

    if sys.stdout.isatty() and sys.stderr.isatty() and not args.no_color:
        colorize = True
    else:
        colorize = False

    if args.version:
        print(f"Moulinorme version {moulinorme.__version__}")
        return 0

    targets = list()
    for filename in args.files:
        target = pathlib.Path(filename).expanduser().resolve()
        targets += explore_path(target, args.recursive)

    if len(targets) == 0:
        print("No input files", file=sys.stderr)
        return 1

    norm_ok = True
    for target in targets:
        src_file = None
        if re.match(r"^Makefile$", target.name):
            src_file = moulinorme.Makefile(target)
        elif re.match("^.*\.h$", target.name):
            src_file = moulinorme.HFile(target)
        elif re.match("^.*\.c$", target.name):
            src_file = moulinorme.CFile(target)

        if isinstance(src_file, moulinorme.SourceFile):
            src_file.check_file()
            src_file.print_messages(colorize=colorize)
            if not src_file.norm_ok():
                norm_ok = False
        elif args.unnecessary:
            norm_ok = False
            o1 = moulinorme.types.NormMessage(str(target), 0, "O1, is this file required for compilation?", moulinorme.types.SeverityMajor())
            if colorize:
                print(o1.colorized())
            else:
                print(str(o1))
        elif args.verbose:
            print(f"Skipping unhandled file: {str(target)}")

    if norm_ok:
        if colorize:
            print(f"{TermStyle.GREEN}No norm violations!{TermStyle.RESET}")
        else:
            print(f"No norm violations!")

    return 0 if norm_ok else 1

if __name__ == "__main__":
    exit(main())