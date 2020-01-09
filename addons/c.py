"""
    C Handler for Moulinorme
    Copyright (C) 2019  akrocynova

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

import re

class MoulinetteAddon:
    _name = "C Source"
    _author = "https://github.com/hoot-w00t"
    _description = "Norm checks for C source files"
    _handlers = {
        "extensions": [".c"],
        "filenames": [],
    }

    c_norm = {
        "max_func_args": 4,
        "max_func_lines": 20,
        "max_funcs_per_file": 5,
        "max_params_per_func": 4,
    }

    def __init__(self, moulinette, verbose=False):
        self.verbose = verbose
        self.moulinette = moulinette

    def split_functions(self, filepath, lines):
        line_nb = 1
        funcs = []
        c_func = []
        is_func = False

        for line in lines:
            if line .startswith('}') and is_func:
                is_func = False
                funcs.append(c_func)
                c_func = []
            if is_func : c_func.append(line)
            if line == '{':
                c_func.append(line_nb - 1)
                is_func = True

            if line_nb > 6:
                comments = [line.find(comment) for comment in ["//", "/*", "*/"]]
                dquotes = [i for i, s in enumerate(line) if s == '"']

                for comment in comments:
                    if comment == -1 : continue
                    lower = False
                    higher = False
                    for dquote in dquotes:
                        if dquote < comment : lower = True
                        if dquote > comment : higher = True

                    if not (lower and higher):
                        self.moulinette.add_norm_violation(f"F6, comment", filepath, line=line_nb, severity=1)

            line_nb += 1

        return funcs

    def is_variable_decl(self, filepath, line_nb, line):
        w_a = re.match("^([a-zA-Z0-9_\\* ]*) ([a-zA-Z0-9_\*\\[\\]\\-+ ]*) = (.*);", line)
        wo_a = re.match("^([a-zA-Z0-9_\\* ]*) ([a-zA-Z0-9_\*\\[\\]\\-+ ]*);", line)
        w_ma = re.match("^([a-zA-Z0-9_\\* ]*) ([a-zA-Z0-9_\*,\\[\\]\\-+ ]*) = (.*);", line)
        wo_ma = re.match("^([a-zA-Z0-9_\\* ]*) ([a-zA-Z0-9_\*,\\[\\]\\-+ ]*);", line)

        if (w_ma or wo_ma) and not (w_a or wo_a):
            self.moulinette.add_norm_violation(f"L5, multiple declarations on the same line", filepath, line=line_nb, severity=1)
            return True

        if w_a or wo_a:
            return True
        return False

    def c_functions(self, filepath, lines):
        funcs = self.split_functions(filepath, lines)

        for func in funcs:
            func_size = len(func) - 1
            func_line = func[0]

            func_decl = lines[func_line - 1]
            decl_params = func_decl[func_decl.find("(") + 1:func_decl.find(")")]
            param_count = len(decl_params.split(','))
            if len(decl_params) == 0:
                self.moulinette.add_norm_violation(f"F5, a function with no parameters should take (void)", filepath, line=func_line, severity=2)
            elif param_count > self.c_norm["max_params_per_func"]:
                self.moulinette.add_norm_violation(f"F5, function takes too many parameters ({param_count})", filepath, line=func_line, severity=2)

            for i in range(1, func_size + 1):
                line = func[i].strip()
                line_nb = func_line + i + 1
                is_var_decl = self.is_variable_decl(filepath, line_nb, line)
                if i == 1:
                    variable_decl = is_var_decl

                if len(line) == 0 and not variable_decl:
                    self.moulinette.add_norm_violation("L6, only one line break should be found after the variable declarations", filepath, line=line_nb, severity=1)

                if not is_var_decl:
                    if len(line) > 0 and variable_decl:
                        self.moulinette.add_norm_violation("L6, a line break should separate the variable declarations from the remainder of the function", filepath, line=line_nb, severity=1)
                    variable_decl = False

                if is_var_decl and not variable_decl:
                    self.moulinette.add_norm_violation("L5, variables should be declared at the beginning of the scope of the function", filepath, line=line_nb, severity=1)

                dquotes = [i for i, s in enumerate(line) if s == '"']
                for keyword in ["if", "while", "for", "return", "switch", "do"]:
                    kp = line.find(f"{keyword}(")
                    if kp != -1:
                        self.moulinette.add_norm_violation(f"L3, missing space after '{keyword}'", filepath, line=line_nb, severity=1)

            if func_size > self.c_norm["max_func_lines"]:
                self.moulinette.add_norm_violation(f"F4, too long function ({func_size} lines)", filepath, line=func_line, severity=2)

            func_line_end = func_line + func_size + 3
            if func_line_end + 1 <= len(lines):
                if len(lines[func_line_end - 1]) == 0 and len(lines[func_line_end]) == 0:
                    self.moulinette.add_norm_violation("G2, wrong function spacing", filepath, line=func_line_end, severity=1)

        func_nb = len(funcs)
        if func_nb > self.c_norm["max_funcs_per_file"]:
            self.moulinette.add_norm_violation(f"O3, too many functions ({func_nb}>{self.c_norm['max_funcs_per_file']})", filepath, line=0, severity=2)

    def process_file(self, filepath):
        lines = self.moulinette.lines_to_list(filepath)

        self.moulinette.check_header(
            filepath=filepath,
            lines=lines,
            comment_separator=["/*", "**", "*/"]
            )

        self.moulinette.check_columns(
            filepath=filepath,
            lines=lines
        )

        self.moulinette.check_indent(filepath, lines)
        self.c_functions(filepath, lines)

        lines.clear()