from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="concore",
    version="1.0.0",
    author="ControlCore Project",
    description="A command-line interface for concore neuromodulation workflows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ControlCore-Project/concore",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "beautifulsoup4",
        "lxml",
        "numpy",
        "scipy",
        "matplotlib",
        "click>=8.0.0",
        "rich>=10.0.0",
        "psutil>=5.8.0",
    ],
    entry_points={
        "console_scripts": [
            "concore=concore_cli.cli:cli",
        ],
    },
)
