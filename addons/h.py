"""
    C Header Handler for Moulinorme
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

class MoulinetteAddon:
    _name = "C Header"
    _author = "https://github.com/hoot-w00t"
    _description = "Norm checks for C header files"
    _handlers = {
        "extensions": [".h"],
        "filenames": [],
    }

    def __init__(self, moulinette, verbose=False):
        self.verbose = verbose
        self.moulinette = moulinette

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

        lines.clear()