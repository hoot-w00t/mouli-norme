
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

from moulinorme.types import Severity, SeverityOk, SeverityInfo, SeverityMinor, SeverityMajor, NormMessage
import pathlib
import typing
import re
import os

class SourceFile:
    def __init__(self, filename: [typing.Union[str, pathlib.Path]]):
        self._header_start = "/*"
        self._header_mid = "**"
        self._header_end = "*/"

        self._tabsize = 1
        self._indent_size = 4
        self._max_columns = 80

        if isinstance(filename, pathlib.Path):
            self._filename = filename
        else:
            self._filename = pathlib.Path(filename).expanduser().resolve()

        self._readlines()
        self.messages = list()

    def _readlines(self):
        with self._filename.open("r") as h:
            self.raw_lines = h.readlines()

        self.lines = [line.replace("\n", "").expandtabs(tabsize=self._tabsize) for line in self.raw_lines]

    def append_message(self, line: int, message: str, severity: Severity):
        self.messages.append(NormMessage(
            str(self._filename),
            line,
            message,
            severity
        ))

    def print_messages(self, colorize=False, include_ok=False, sort_by_line=True):
        """Print norm messages to stdout"""

        if sort_by_line:
            self.messages.sort(key=lambda x: x.line)

        for message in self.messages:
            if not message.is_ok() or include_ok:
                if colorize:
                    print(message.colorized())
                else:
                    print(str(message))

    def norm_ok(self) -> bool:
        """Returns True if no norm violations are reported in self.messages"""

        for message in self.messages:
            if not message.is_ok():
                return False

        return True

    def check_header(self):
        """Check if source file header is valid"""

        if len(self.lines) < 6:
            self.append_message(0, "G1, missing header", SeverityMajor())
            return

        invalid = list()
        if self.lines[0] != self._header_start:
            invalid.append(1)
        if not re.match(f"^{re.escape(self._header_mid)} EPITECH PROJECT, \\d\\d\\d\\d$", self.lines[1]):
            invalid.append(2)
        if len(self.lines[2].rstrip()) < len(self.lines[2]) or not self.lines[2].startswith(self._header_mid):
            invalid.append(3)
        if self.lines[3] != f"{self._header_mid} File description:":
            invalid.append(4)
        if len(self.lines[4].rstrip()) < len(self.lines[4]) or not self.lines[4].startswith(self._header_mid):
            invalid.append(5)
        if self.lines[5] != self._header_end:
            invalid.append(6)

        if len(invalid) >= 6:
            self.append_message(0, "G1, missing header", SeverityMajor())
        else:
            for line_nb in invalid:
                self.append_message(line_nb, "G1, invalid header", SeverityMajor())

    def check_columns(self):
        """Check if any line exceeds _max_columns width (tabs expanded to _tabsize spaces)"""

        line_nb = 1
        for line in self.lines:
            line_len = len(line) + 1
            if line_len > self._max_columns:
                self.append_message(line_nb, f"F3, too long line ({line_len} columns)", SeverityMajor())

            line_nb += 1

    def check_file(self):
        """Perform all norm checks"""

        self.check_header()
        self.check_columns()

    def snake_case(self, name: str) -> bool:
        return True if re.match("^([a-z0-9_]*)$", name) else False

class Makefile(SourceFile):
    def __init__(self, filename: [typing.Union[str, pathlib.Path]]):
        super().__init__(filename)

        self._header_start = "##"
        self._header_mid = "##"
        self._header_end = "##"

class CFileDefs(SourceFile):
    def __init__(self, filename: [typing.Union[str, pathlib.Path]]):
        super().__init__(filename)

        self._max_funcs = 5
        self._max_func_lines = 20
        self._max_func_args = 4

    def check_filename(self):
        if not self.snake_case(os.path.splitext(self._filename.name)[0]):
            self.append_message(0, "O4, file name does not respect snake case convention", SeverityMajor())

    def check_indent(self):
        """Check if indentation is valid (indent dividable by _indent_size)"""

        line_nb = 1
        for line in self.lines:
            line_indent = len(line.rstrip()) - len(line.strip())
            if line_indent % self._indent_size != 0:
                self.append_message(line_nb, "L2, invalid indentation", SeverityMinor())

            line_nb += 1

    def check_trailing_whitespace(self):
        """Check if lines have trailing whitespace"""

        line_nb = 1
        for line in self.lines:
            if len(line.rstrip()) < len(line):
                self.append_message(line_nb, "L2, trailing whitespace", SeverityMinor())

            line_nb += 1

    def extract_prototype_name(self, prototype: str):
        """Extract function name from its prototype"""

        start = prototype.find(" ") + 1
        end = prototype.find("(", start)

        return prototype[start:end].replace("*", "").strip()

    def extract_prototype_args(self, prototype: str):
        """Extract function arguments from its prototype"""

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

    def extract_functions(self):
        self.functions = list()

        line_range = iter(range(0, len(self.lines)))
        for i in line_range:
            line_nb = i + 1
            line = self.lines[i]
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
                while not self.lines[i].startswith("{"):
                    prototype += f" {self.lines[i].strip()}"
                    i = next(line_range)

                function = {
                    "prototype": prototype,
                    "prototype_line_nb": line_nb,
                    "first_line_nb": i + 2,
                    "lines": []
                }
                i = next(line_range)

            if function is not None:
                function["name"] = self.extract_prototype_name(function["prototype"])
                function["args"] = self.extract_prototype_args(function["prototype"])

                while not self.lines[i].startswith("}"):
                    function["lines"].append(self.lines[i])
                    i = next(line_range)

                self.functions.append(function)

    def check_function(self, function):
        if not self.snake_case(function["name"]):
            self.append_message(function["prototype_line_nb"], "F2, function name does not respect snake case convention", SeverityMajor())

        args_count = 0 if function["args"] is None else len(function["args"])
        if function["args"] is None:
            self.append_message(function["prototype_line_nb"], "F5, a function with no parameters should take (void)", SeverityMajor())
        elif args_count > self._max_func_args:
            self.append_message(function["prototype_line_nb"], f"F5, function takes too many parameters ({args_count}/{self._max_func_args})", SeverityMajor())

        lines_count = len(function["lines"])
        if lines_count > self._max_func_lines:
            self.append_message(function["prototype_line_nb"], f"F4, too long function ({lines_count}/{self._max_func_lines} lines)", SeverityMajor())

        for i in range(0, len(function["lines"])):
            line_nb = function["first_line_nb"] + i
            line = function["lines"][i].strip()

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
                    self.append_message(line_nb, "F6, comment inside function", SeverityMinor())

            for keyword in ["if", "for", "while", "return", "switch", "do"]:
                for trail in ["(", "{"]:
                    kp = line.find("{}{}".format(keyword, trail))
                    if kp != -1:
                        self.append_message(line_nb, f"L3, missing space after '{keyword}'", SeverityMinor())

class HFile(CFileDefs):
    def check_file(self):
        """Perform all norm checks"""

        super().check_file()
        self.check_filename()
        self.check_indent()
        self.check_trailing_whitespace()

class CFile(CFileDefs):
    def check_file(self):
        """Perform all norm checks"""

        self.extract_functions()
        super().check_file()
        self.check_filename()
        self.check_indent()
        self.check_trailing_whitespace()

        funcs_nb = len(self.functions)
        if funcs_nb > self._max_funcs:
            self.append_message(0, f"O3, too many functions ({funcs_nb}/{self._max_funcs})", SeverityMajor())

        for function in self.functions:
            self.check_function(function)
