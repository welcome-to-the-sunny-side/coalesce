from setuptools import setup, find_packages

setup(
    name="coalesce",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "urllib3>=1.26.0",
        "requests",
        "tabulate",
    ],
    entry_points={
        "console_scripts": [
            "coalesce=coalesce.cli:main",
        ],
    },
    author="welcome-to-the-sunny-side",
    description="Track and analyze your Codeforces problem-solving data",
    keywords="codeforces, problems, analysis",
    python_requires=">=3.6",
)
