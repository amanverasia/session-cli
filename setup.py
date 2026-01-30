from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="session-controller",
    version="1.3.0",
    description="Python CLI tool and library for programmatic control of Session Desktop",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/amanverasia/session-cli",
    author="Session Controller Contributors",
    author_email="",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Communications :: Chat",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    keywords="session messenger desktop cli cdp sqlcipher",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    python_requires=">=3.10",
    install_requires=[
        "sqlcipher3>=0.5.0",
        "pynacl>=1.5.0",
        "websocket-client>=1.0.0",
        "pyaes>=1.6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "session-cli=session_controller.cli:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/amanverasia/session-cli/issues",
        "Source": "https://github.com/amanverasia/session-cli",
        "Documentation": "https://github.com/amanverasia/session-cli#readme",
    },
)
