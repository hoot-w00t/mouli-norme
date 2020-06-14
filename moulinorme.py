#!/usr/bin/python3

"""
    Moulinorme
    Copyright (C) 2019-2020  akrocynova

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import pathlib
import typing
import math
import re

VERSION = "1.0"

class TermStyle:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    RESET  = '\033[0m'
    BOLD   = '\033[1m'

class NormViolation:
    MAJOR = 0
    MINOR = 1
    INFO  = 2

    def __init__(self,
                 severity: int,
                 message:  str,
                 line:     int):
        self.severity = severity
        self.message = message
        self.line = line

class Moulinorme:
    def __init__(self,
                 indent_spaces: int = 4,
                 max_columns:   int = 80):
        self.rules = {
            "indent_spaces": indent_spaces,
            "max_columns": max_columns,
            "c_max_funcs_per_file": 5,
            "c_max_lines_per_func": 20,
            "c_max_args_per_func": 4
        }

        self.file_types = {
            "makefile": {
                "comment": "Makefile",
                "regexps": ["^Makefile$"],
                "handler": self.check_makefile
            },
            "c_source": {
                "comment": "C Source File",
                "regexps": ["^.*\.c"],
                "handler": self.check_c_source
            },
            "c_header": {
                "comment": "C Header File",
                "regexps": ["^.*\.h"],
                "handler": self.check_c_header
            }
        }

    def extract_c_prototype_name(self, prototype: str):
        """Extract C function name from its prototype"""

        start = prototype.find(" ") + 1
        end = prototype.find("(", start)

        return prototype[start:end].replace("*", "").strip()

    def extract_c_prototype_args(self, prototype: str):
        """Extract C function arguments from its prototype"""

        start = prototype.find("(") + 1
        end = prototype.find(")", start)
        argw = prototype[start:end].strip()

        if len(argw) == 0:
            return None

        if argw == "void":
            return list()

        args = []
        for arg in argw.split(","):
            args.append(arg.strip())

        return args

    def extract_c_functions(self, lines: list):
        functions = list()

        line_range = iter(range(0, len(lines)))
        for i in line_range:
            line_nb = i + 1
            line = lines[i]
            function = None

            if re.match("^([a-zA-Z0-9_\\*]*) ([a-zA-Z0-9_\*]*)\((.*)\)$", line):
                function = {
                    "prototype": line,
                    "prototype_line_nb": line_nb,
                    "first_line_nb": line_nb + 2,
                    "lines": []
                }
                i = next(line_range)
                i = next(line_range)

            elif re.match("^([a-zA-Z0-9_\\*]*) ([a-zA-Z0-9_\*]*)\((.*),$", line):
                prototype = line

                i = next(line_range)
                while not lines[i].startswith("{"):
                    prototype += " " + lines[i].strip()
                    i = next(line_range)

                function = {
                    "prototype": prototype,
                    "prototype_line_nb": line_nb,
                    "first_line_nb": i + 2,
                    "lines": []
                }
                i = next(line_range)

            if function != None:
                function["name"] = self.extract_c_prototype_name(function["prototype"])
                function["args"] = self.extract_c_prototype_args(function["prototype"])

                while not lines[i].startswith("}"):
                    function["lines"].append(lines[i])
                    i = next(line_range)

                functions.append(function)

        return functions

    def is_c_variable_declaration(self, line: str, line_nb: int):
        w_a = re.match("^([a-zA-Z0-9_\\* ]*) ([a-zA-Z0-9_\*\\[\\]\\-+ ]*) = (.*);", line)
        wo_a = re.match("^([a-zA-Z0-9_\\* ]*) ([a-zA-Z0-9_\*\\[\\]\\-+ ]*);", line)
        w_ma = re.match("^([a-zA-Z0-9_\\* ]*) ([a-zA-Z0-9_\*,\\[\\]\\-+ ]*) = (.*);", line)
        wo_ma = re.match("^([a-zA-Z0-9_\\* ]*) ([a-zA-Z0-9_\*,\\[\\]\\-+ ]*);", line)

        if (w_ma or wo_ma) and not (w_a or wo_a):
            return NormViolation(
                NormViolation.MINOR,
                "L5, multiple declarations on the same line",
                line_nb
            )

        if (w_a or wo_a) and not line.startswith("return"):
            return True

        return False

    def check_c_functions(self, lines: list):
        functions = self.extract_c_functions(lines)
        violations = list()

        if len(functions) > self.rules["c_max_funcs_per_file"]:
            violations.append(NormViolation(
                NormViolation.MAJOR,
                "O3, too many functions ({}/{})".format(
                    len(functions),
                    self.rules["c_max_funcs_per_file"]
                ),
                0
            ))

        for function in functions:
            if not re.match("^([a-z0-9_]*)$", function["name"]):
                violations.append(NormViolation(
                    NormViolation.MAJOR,
                    "F2, function name does not respect snake case convention",
                    function["prototype_line_nb"]
                ))

            if function["args"] == None:
                violations.append(NormViolation(
                    NormViolation.MAJOR,
                    "F5, a function with no parameters should take (void)",
                    function["prototype_line_nb"]
                ))
            elif len(function["args"]) > self.rules["c_max_args_per_func"]:
                violations.append(NormViolation(
                    NormViolation.MAJOR,
                    "F5, function takes too many parameters ({}/{})".format(
                        len(function["args"]),
                        self.rules["c_max_args_per_func"]
                    ),
                    function["prototype_line_nb"]
                ))

            if len(function["lines"]) > self.rules["c_max_lines_per_func"]:
                violations.append(NormViolation(
                    NormViolation.MAJOR,
                    "F4, too long function ({}/{} lines)".format(
                        len(function["lines"]),
                        self.rules["c_max_lines_per_func"]
                    ),
                    function["prototype_line_nb"]
                ))

            declare_vars = True
            for i in range(0, len(function["lines"])):
                line_nb = function["first_line_nb"] + i
                line = function["lines"][i].strip()

                var_decl = self.is_c_variable_declaration(line, line_nb)
                if isinstance(var_decl, NormViolation):
                    violations.append(var_decl)

                if len(line) == 0 and (not declare_vars or i == 0):
                    violations.append(NormViolation(
                        NormViolation.MINOR,
                        "L6, only one line break should be found after the variable declarations",
                        line_nb
                    ))

                if not var_decl:
                    if len(line) > 0 and declare_vars and i > 0:
                        violations.append(NormViolation(
                            NormViolation.MINOR,
                            "L6, a line break should separate the variable declarations from the remainder of the function",
                            line_nb
                        ))

                    declare_vars = False

                if not declare_vars and var_decl:
                    violations.append(NormViolation(
                        NormViolation.MINOR,
                        "L5, variables should be declared at the beginning of the scope of the function",
                        line_nb
                    ))

                comments = [line.find(comment) for comment in ["//", "/*", "*/"]]
                dquotes = [j for j, s in enumerate(line) if s == '"']
                for comment in comments:
                    if comment == -1 : continue
                    lower = False
                    higher = False
                    for dquote in dquotes:
                        if dquote < comment : lower = True
                        if dquote > comment : higher = True

                    if not (lower and higher):
                        violations.append(NormViolation(
                            NormViolation.MINOR,
                            "F6, comment inside function",
                            line_nb
                        ))

                for keyword in ["if", "for", "while", "return", "switch", "do"]:
                    for trail in ["(", "{"]:
                        kp = line.find("{}{}".format(keyword, trail))
                        if kp != -1:
                            violations.append(NormViolation(
                                NormViolation.MINOR,
                                "L3, missing space after '{}'".format(keyword),
                                line_nb
                            ))

        return violations

    def line_indent(self, line: str, space_count: bool = False):
        """Return the number of indentations (only counts complete indent)
        If space_count is True, return the number of indent spaces"""

        spaces = len(line.rstrip()) - len(line.strip())

        if space_count:
            return spaces
        else:
            return math.trunc(spaces / self.rules.get("indent_spaces"))

    def check_indent(self, lines: list):
        """Check if indentation is valid (indent_spaces per indent)"""

        violations = list()

        line_nb = 1
        for line in lines:
            if self.line_indent(line, True) % self.rules.get("indent_spaces") != 0:
                violations.append(NormViolation(
                    NormViolation.MINOR,
                    "L2, invalid indentation",
                    line_nb
                ))
            elif len(line.rstrip()) < len(line):
                violations.append(NormViolation(
                    NormViolation.MINOR,
                    "L2, trailing whitespaces",
                    line_nb
                ))

            line_nb += 1

        return violations

    def check_columns(self, lines: list):
        """Check if all lines are <= 80 columns in size"""

        violations = []

        line_nb = 1
        for line in lines:
            line_len = len(line) + 1
            if line_len > self.rules.get("max_columns"):
                violations.append(NormViolation(
                    NormViolation.MAJOR,
                    "F3, too long line ({} columns)".format(line_len),
                    line_nb
                ))

            line_nb += 1

        return violations

    def check_header(self, lines: list, comments: list = ["##", "##", "##"]):
        """Check if header is valid"""

        violations = []
        invalid_lines = []

        if len(lines) < 6:
            violations.append(NormViolation(
                NormViolation.MAJOR,
                "G1, missing header",
                0
            ))
        else:
            if lines[0] != comments[0]:
                invalid_lines.append(1)
            if not re.match("^{} EPITECH PROJECT, \\d\\d\\d\\d$".format(re.escape(comments[1])), lines[1]):
                invalid_lines.append(2)
            if len(lines[2].rstrip()) < len(lines[2]) or not lines[2].startswith(comments[1]):
                invalid_lines.append(3)
            if lines[3] != "{} File description:".format(comments[1]):
                invalid_lines.append(4)
            if len(lines[4].rstrip()) < len(lines[4]) or not lines[4].startswith(comments[1]):
                invalid_lines.append(5)
            if lines[5] != comments[2]:
                invalid_lines.append(6)

            if len(invalid_lines) == 6:
                violations.append(NormViolation(
                    NormViolation.MAJOR,
                    "G1, missing header",
                    0
                ))
            else:
                for invalid_line in invalid_lines:
                    violations.append(NormViolation(
                        NormViolation.MAJOR,
                        "G1, invalid header",
                        invalid_line
                    ))

        return violations

    def open_file(self, filepath: pathlib.Path):
        """Open filepath and return a list of its lines"""

        lines = []

        with filepath.open("r") as file:
            for line in file.readlines():
                lines.append(line.replace("\n", "").expandtabs(
                        tabsize=self.rules.get("indent_spaces")))

        return lines

    def print_violations(self,
                         filepath: pathlib.Path,
                         violations: typing.Union[NormViolation, list],
                         display_valid_files: bool = False):
        """Print norm violations to stdout"""

        if isinstance(violations, NormViolation):
            violations = [violations]

        if len(violations) == 0:
            if display_valid_files:
                print("{}: {}no violations{}".format(
                    str(filepath),
                    TermStyle.GREEN,
                    TermStyle.RESET
                ))

            return

        print("{}: {}{}{} {}:".format(
                str(filepath),
                TermStyle.BLUE, len(violations), TermStyle.RESET,
                "violation" if len(violations) == 1 else "violations"
            ))

        for violation in violations:
            if violation.severity == NormViolation.MAJOR:
                severity_text = "{}{}{}".format(
                    TermStyle.RED,
                    "Major",
                    TermStyle.RESET
                    )
            elif violation.severity == NormViolation.MINOR:
                severity_text = "{}{}{}".format(
                    TermStyle.YELLOW,
                    "Minor",
                    TermStyle.RESET
                    )
            else:
                severity_text = "{}{}{}".format(
                    TermStyle.GREEN,
                    "Info",
                    TermStyle.RESET
                    )

            print("    {}{}{}: {}: {}".format(
                TermStyle.BLUE, violation.line, TermStyle.RESET,
                severity_text,
                violation.message
            ))

    def check_makefile(self, lines: list):
        """Return a list of norm violations for Makefiles"""

        violations = []

        violations += self.check_header(lines)
        violations += self.check_columns(lines)

        return violations

    def check_c_source(self, lines: list):
        """Return a list of norm violations for C source files"""

        violations = []

        violations += self.check_header(lines, comments=["/*", "**", "*/"])
        violations += self.check_columns(lines)
        violations += self.check_indent(lines)
        violations += self.check_c_functions(lines)

        return violations

    def check_c_header(self, lines: list):
        """Return a list of norm violations for C header files"""

        violations = []

        violations += self.check_header(lines, comments=["/*", "**", "*/"])
        violations += self.check_columns(lines)
        violations += self.check_indent(lines)

        return violations


    def check_file(self, filepath: pathlib.Path):
        """Return a list of norm violations, None if there are no violations"""

        for file_type in self.file_types:
            for regexp in self.file_types[file_type]["regexps"]:
                if re.match(regexp, filepath.name):
                    lines = self.open_file(filepath)

                    return self.file_types[file_type]["handler"](lines)

        return None

def explore_path(target: pathlib.Path, recursively: bool = True):
    """Explore paths add return a list of files found"""
    targets = []

    if target.is_dir():
        for sub in target.iterdir():
            if sub.is_dir():
                if recursively:
                    targets += explore_path(sub)
            else:
                targets.append(sub)

    else:
        targets.append(target)

    return targets

if __name__ == "__main__":
    from sys import stdout, stderr
    from argparse import ArgumentParser

    arg_parser = ArgumentParser(description="Moulinorme")
    arg_parser.add_argument("-a", "--all", dest="display_all", action="store_true",
                            help="display files that do not have any violations")
    arg_parser.add_argument("-v", "--version", dest="version", action="store_true",
                            help="display Moulinorme version")
    arg_parser.add_argument("--no-color", dest="no_color", action="store_true",
                            help="do not colorize output")
    arg_parser.add_argument("--supported", dest="supported", action="store_true",
                            help="display the list of supported file types")
    arg_parser.add_argument(dest="files", nargs='*', default=[],
                            help="files/folders to check")
    args = arg_parser.parse_args()

    if args.version:
        print("Moulinorme version {}".format(VERSION))
        exit(0)

    moulinorme = Moulinorme()

    if args.supported:
        for file_type in moulinorme.file_types:
            print("{} ({})".format(
                moulinorme.file_types[file_type]["comment"],
                ", ".join(moulinorme.file_types[file_type]["regexps"])
            ))
        exit(0)

    if args.no_color or not stdout.isatty():
        TermStyle.BLUE = ""
        TermStyle.GREEN = ""
        TermStyle.YELLOW = ""
        TermStyle.RED = ""
        TermStyle.RESET = ""
        TermStyle.BOLD = ""

    if len(args.files) == 0:
        arg_parser.print_usage()
        print("\nNo files/folders given", file=stderr)
        exit(1)

    targets = []
    for file in args.files:
        target = pathlib.Path(file).expanduser().resolve()
        targets += explore_path(target)

    violates_norm = False
    for target in targets:
        try:
            violations = moulinorme.check_file(target)

        except Exception as e:
            print("{}: {}".format(str(target), e), file=stderr)
            continue

        if violations == None:
            if args.display_all:
                print("{}: unhandled file".format(str(target)))
            continue

        if len(violations) > 0:
            violates_norm = True

        moulinorme.print_violations(target,
                                    violations,
                                    args.display_all)

    if not violates_norm and not args.display_all:
        print("{}No norm violations!{}".format(
            TermStyle.GREEN,
            TermStyle.RESET
        ))

    exit(1 if violates_norm else 0)