
"""
MIT License

Copyright (c) 2019-2021 akrocynova

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

class TermStyle:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    RESET  = '\033[0m'
    BOLD   = '\033[1m'

class Severity:
    def __init__(self):
        self.color = None
        self.name = None
        raise Exception()

    def colorized(self) -> str:
        return f"{self.color}{self.name}{TermStyle.RESET}"

    def __str__(self) -> str:
        return self.name

class SeverityOk(Severity):
    def __init__(self):
        self.color = TermStyle.GREEN
        self.name = "Ok"

class SeverityInfo(Severity):
    def __init__(self):
        self.color = TermStyle.BLUE
        self.name = "Info"

class SeverityMinor(Severity):
    def __init__(self):
        self.color = TermStyle.YELLOW
        self.name = "Minor"

class SeverityMajor(Severity):
    def __init__(self):
        self.color = TermStyle.RED
        self.name = "Major"

class NormMessage:
    def __init__(self, filename: str, line: int, message: str, severity: Severity):
        if not isinstance(filename, str):
            raise TypeError("filename must be a string")
        if not isinstance(line, int):
            raise TypeError("line must be an integer")
        if not isinstance(message, str):
            raise TypeError("message must be a string")
        if not isinstance(severity, Severity):
            raise TypeError("severity must be a Severity object")

        self.filename = filename
        self.line = line
        self.message = message
        self.severity = severity

    def is_ok(self) -> bool:
        return isinstance(self.severity, SeverityOk)

    def colorized(self) -> str:
        return f"{self.severity.colorized()}: {self.filename}:{TermStyle.BLUE}{self.line}{TermStyle.RESET}: {self.message}"

    def __str__(self) -> str:
        return f"{str(self.severity)}: {self.filename}:{self.line}: {self.message}"