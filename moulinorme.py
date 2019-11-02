#!/usr/bin/python3

"""
    Moulinorme
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

from argparse import ArgumentParser
from os.path import join, isdir, basename, splitext
from os import listdir, getenv
from importlib import machinery
import types
import re

class Moulinette:
    global_norm = {
        "indent_space": 4,
        "max_columns": 80,
    }

    def escape_separator(self, separator):
        new_separator = ""
        for c in separator:
            new_separator += f"\\{c}"
        return (new_separator)

    def check_header(self, filepath, lines, comment_separator=["/*", "**", "*/"]):
        if len(lines) < 6:
            print(f"[MAJOR] {filepath}: G1, missing header")
            return
        wrong_lines = []
        if lines[0] != comment_separator[0]:
            wrong_lines.append("1")
        if not re.match(f"^{self.escape_separator(comment_separator[1])} EPITECH PROJECT, \\d\\d\\d\\d$", lines[1]):
            wrong_lines.append("2")
        if len(lines[2].rstrip()) < len (lines[2]) or not lines[2].startswith(comment_separator[1]):
            wrong_lines.append("3")
        if lines[3] != f"{comment_separator[1]} File description:":
            wrong_lines.append("4")
        if len(lines[4].rstrip()) < len (lines[4]) or not lines[4].startswith(comment_separator[1]):
            wrong_lines.append("5")
        if lines[5] != comment_separator[2]:
            wrong_lines.append("6")
        if len(wrong_lines) == 6:
            print(f"[MAJOR] {filepath}: G1, missing header")
        elif len(wrong_lines) > 0:
            print(f"[MAJOR] {filepath}: G1, wrong header, lines {', '.join(wrong_lines)}")

    def check_columns(self, filepath, lines):
        line_nb = 1
        for line in lines:
            line_len = len(line) + 1
            if line_len > self.global_norm["max_columns"]:
                print(f"[MAJOR] {filepath}: F3, too long line ({line_len} columns, line {line_nb})")
            line_nb += 1

    def lines_to_list(self, filepath):
        lines = []
        with open(filepath, 'r') as h:
            for line in h.readlines():
                lines.append(line.replace('\n', '').expandtabs(tabsize=self.global_norm["indent_space"]))
        return lines

if __name__ == "__main__":
    handlers = {
        "extensions": {},
        "filenames": {},
    }

    addons_files = []
    addons = {}

    arg_parser = ArgumentParser(description="Mouli-norme")
    arg_parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Display additionnal (debug) information.")
    arg_parser.add_argument("-d", "--display", dest="display_files", action="store_true", help="Show each file that is being processed.")
    arg_parser.add_argument("--addons", dest="addons_folder", nargs="?", default="./addons", help="Path to the addons folder (default=./addons)")
    arg_parser.add_argument("--addons-list", dest="display_addons", action="store_true", help="Display information about each addon loaded.")
    arg_parser.add_argument("--supported", dest="display_handlers", action="store_true", help="Display which files the program can handle.")
    arg_parser.add_argument(dest="files", nargs='*', default=[], help="Files to process.")
    args = arg_parser.parse_args()

    addons_env = join(getenv("HOME", "."), ".config/moulinorme/addons")
    if isdir(addons_env) and args.addons_folder == "./addons":
        if args.verbose : print(f"Using addons folder from environment")
        args.addons_folder = addons_env

    if not isdir(args.addons_folder):
        print(f"Addons folder: {args.addons_folder}: doesn't exist")
        exit(1)
    
    if args.verbose : print(f"Using addons folder: {args.addons_folder}")

    try:
        for filename in listdir(args.addons_folder):
            if filename.endswith('.py'):
                addons_files.append(join(args.addons_folder, filename))

        moulinette = Moulinette()

        for addon in addons_files:
            if args.verbose : print(f"Loading addon: {addon}")

            loader = machinery.SourceFileLoader('MoulinetteAddon', addon)
            module = types.ModuleType(loader.name)
            loader.exec_module(module)
            ha = module.MoulinetteAddon(moulinette)
            addons[addon] = ha

            for handler in module.MoulinetteAddon._handlers["extensions"]:
                if handler in handlers["extensions"]:
                    print(f"Handler conflict: '{handler}' from plugin '{module.MoulinetteAddon._name}'. This one will not be loaded.")
                else:
                    handlers["extensions"][handler] = ha

            for handler in module.MoulinetteAddon._handlers["filenames"]:
                if handler in handlers["filenames"]:
                    print(f"Handler conflict: '{handler}' from plugin '{module.MoulinetteAddon._name}'. This one will not be loaded.")
                else:
                    handlers["filenames"][handler] = ha

    except Exception as e:
        print(f"Error while loading addons: {e}")
        exit(1)

    if args.display_addons:
        print("Loaded addons:")
        for addon in addons:
            print(f"{addon}: {addons[addon]._name} by {addons[addon]._author}: {addons[addon]._description}")

    if args.display_handlers:
        handler_list = []
        for h in handlers["filenames"]:
            handler_list.append(h)
        for h in handlers["extensions"]:
            handler_list.append(f'*{h}')
        print(f"Files handled: {', '.join(handler_list)}")

    if args.display_addons or args.display_handlers:
        exit(0)

    if len(args.files) == 0:
        arg_parser.print_usage()
        exit(1)

    for _file in args.files:
        if isdir(_file):
            if args.verbose : print(f"Exploring directory: {_file}")
            for sub_file in listdir(_file):
                if not sub_file.startswith('.'):
                    if args.verbose : print(f"Adding file to list: {sub_file}")
                    args.files.append(join(_file, sub_file))
            continue

        if args.display_files or args.verbose:
            print(f"Processing: {_file}")

        file_name = basename(_file)
        name, ext = splitext(file_name)

        if ext in handlers["extensions"]:
            func = getattr(handlers["extensions"][ext], "process_file")
            func(_file)
        elif name in handlers["filenames"]:
            func = getattr(handlers["filenames"][name], "process_file")
            func(_file)