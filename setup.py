"""
Setup script for LexAudit package.
"""

from setuptools import find_packages, setup

setup(
    name="lexaudit",
    version="0.1.0",
    description="LexAudit - Legal citation extraction, retrieval and resolution pipeline",
    author="LexAudit Team",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        # Add dependencies as needed
    ],
    entry_points={
        "console_scripts": [
            "lexaudit=lexaudit.main:main",
        ],
    },
)
