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
            if line == '}' and is_func:
                is_func = False
                funcs.append(c_func)
                c_func = []
            if is_func : c_func.append(line)
            if line == '{':
                c_func.append(line_nb - 1)
                is_func = True

            is_comment = [line.find(comment) >= 0 and  line_nb > 6 for comment in ["// ", "/* ", "*/ "]]
            if any(is_comment):
                print(f"[MINOR] {filepath}: F6, comment at line {line_nb}")

            line_nb += 1

        return funcs

    def is_variable_decl(self, filepath, line_nb, line):
        w_a = re.match("^([a-zA-Z0-9_\\* ]*) ([a-zA-Z0-9_\*\\[\\]\\-+ ]*) = (.*);", line)
        wo_a = re.match("^([a-zA-Z0-9_\\* ]*) ([a-zA-Z0-9_\*\\[\\]\\-+ ]*);", line)
        w_ma = re.match("^([a-zA-Z0-9_\\* ]*) ([a-zA-Z0-9_\*,\\[\\]\\-+ ]*) = (.*);", line)
        wo_ma = re.match("^([a-zA-Z0-9_\\* ]*) ([a-zA-Z0-9_\*,\\[\\]\\-+ ]*);", line)

        if (w_ma or wo_ma) and not (w_a or wo_a):
            print(f"[MINOR] {filepath}: L5, multiple declarations on the same line (line {line_nb})")
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
                print(f"[MAJOR] {filepath}: F5, a function with no parameters should take (void), at line {func_line}")
            elif param_count > self.c_norm["max_params_per_func"]:
                print(f"[MAJOR] {filepath}: F5, function takes too many parameters ({param_count}) at line {func_line}")

            for i in range(1, func_size + 1):
                line = func[i].strip()
                line_nb = func_line + i + 1
                is_var_decl = self.is_variable_decl(filepath, line_nb, line)
                if i == 1:
                    variable_decl = is_var_decl

                if len(line) == 0 and not variable_decl:
                    print(f"[MINOR] {filepath}: L6, only one line break should be found after the variable declarations (line {line_nb})")

                if not is_var_decl:
                    if len(line) > 0 and variable_decl:
                        print(f"[MINOR] {filepath}: L6, a line break should separate the variable declarations from the remainder of the function (line {line_nb})")
                    variable_decl = False

                if is_var_decl and not variable_decl:
                    print(f"[MINOR] {filepath}: L5, variables should be declared at the beginning of the scope of the function (line {line_nb})")


            if func_size > self.c_norm["max_func_lines"]:
                print(f"[MAJOR] {filepath}: F4, too long function at line {func_line} ({func_size} lines)")

            func_line_end = func_line + func_size + 3
            if func_line_end + 1 <= len(lines):
                if len(lines[func_line_end - 1]) == 0 and len(lines[func_line_end]) == 0:
                    print(f"[MINOR] {filepath}: G2, wrong function spacing line {func_line_end}")

        func_nb = len(funcs)
        if func_nb > self.c_norm["max_funcs_per_file"]:
            print(f"[MAJOR] {filepath}: O3, too many functions ({func_nb}>{self.c_norm['max_funcs_per_file']})")


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