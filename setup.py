from setuptools import setup, find_packages

setup(
    name="coalesce",
    version="0.1.2",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "urllib3",
        "requests",
        "tabulate",
        "plotext",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "coalesce=coalesce.cli:main",
        ],
    },
    author="welcome-to-the-sunny-side",
    description="Track and analyze your Codeforces problem-solving data",
    keywords="codeforces, problems, analysis, plot",
    python_requires=">=3.6",
)
