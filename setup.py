from setuptools import find_namespace_packages, setup


def get_version():
    version = {}
    with open("tools/_version.py") as fp:
        exec(fp.read(), version)

    return version["__version__"]


setup(
    name="fivetran-connectors",
    version=get_version(),
    author="Mozilla Corporation",
    author_email="fx-data-dev@mozilla.org",
    description="Tooling for managing custom Fivetran connectors",
    url="https://github.com/mozilla/fivetran-connectors",
    packages=find_namespace_packages(include=["tools.*", "tools"]),
    package_data={
        "tools": [
            "templates/*",
        ]
    },
    include_package_data=True,
    install_requires=[
        "click",
        "pytest-black",
        "pytest-pydocstyle",
        "pytest-flake8",
        "pytest-mypy",
        "pytest",
        "Jinja2",
        "cattrs",
        "attrs",
        "typing",
    ],
    long_description="Tooling for building custom Fivetran connectors",
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    entry_points="""
        [console_scripts]
        fivetran=tools.cli:cli
    """,
)
