# Moulinorme
![License](https://img.shields.io/github/license/hoot-w00t/mouli-norme?style=flat-square) ![Python Version](https://img.shields.io/pypi/pyversions/moulinorme?style=flat-square) [![PyPI](https://img.shields.io/pypi/v/moulinorme?style=flat-square)](https://pypi.org/project/moulinorme/)

## What it does
This program checks for Epitech norm violations in your code.

**Note**: This is done on my free-time and given as-is, there is no guarantee of reliability.

## Installation
You need [Python 3.6+](https://docs.python.org/3.6/tutorial/index.html) to run it.

You can install or update it using PyPI
```sh
python3 -m pip install -U moulinorme
```

## Norm checks
The following rules are checked:
| Rule | Description                                                        |
|:----:|--------------------------------------------------------------------|
| G1   | File header                                                        |
| L2   | Indentation (only checks for a valid indentation level, see below) |
| L3   | Spaces                                                             |
| F2   | Naming functions                                                   |
| F3   | Number of columns                                                  |
| F4   | Number of lines                                                    |
| F5   | Arguments                                                          |
| F6   | Comments inside a function                                         |
| O1   | Contents of the delivery folder                                    |
| O3   | File coherence                                                     |
| O4   | Naming files and folders (only checks source files)                |

---

### L2: Indentation

The program will only check for a valid indentation level (`indent_spaces % 4 == 0`).

In the example below both `printf` are an L2 violation, but the program will only catch the first one.
```c
int main(void)
{
    if (condition)
      printf("Hello"); /* Indented with 6 spaces, will be caught */

    if (condition)
            printf("world!\n"); /* Indented with 12 spaces, will not be caught */
}
```