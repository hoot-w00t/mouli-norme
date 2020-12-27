import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="moulinorme",
    version="2.0.0",
    author="akrocynova",
    author_email="",
    description="Epitech norm checks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hoot-w00t/mouli-norme",
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": [
            "moulinorme=moulinorme.__main__:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)