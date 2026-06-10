#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pre-commit==4.2.0",
#     "pytz==2025.2",
#     "requests==2.32.3",
#     "requests-cache==1.2.1",
# ]
# ///

from svg_wheel import generate_fraction_circle, generate_svg_wheel
from utils import (
    WORKS_IN_PYODIDE,
    annotate_wheels,
    get_pyodide_recipe_packages,
    get_top_packages,
    remove_irrelevant_packages,
    save_to_file,
)

TO_CHART = 360


def main(to_chart: int = TO_CHART) -> None:
    packages = remove_irrelevant_packages(get_top_packages(), to_chart)
    recipe_packages, patched_packages = get_pyodide_recipe_packages()
    annotate_wheels(packages, recipe_packages, patched_packages)
    save_to_file(packages, "results.json")

    pep783_count = sum(package["wheel"] for package in packages)
    pyodide_count = sum(
        package["css_class"] in WORKS_IN_PYODIDE for package in packages
    )

    generate_svg_wheel(packages, to_chart, pep783_count)
    generate_fraction_circle(pyodide_count, to_chart, "wheel-pyodide.svg")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-n", "--number", type=int, default=TO_CHART, help="number of packages to chart"
    )
    args = parser.parse_args()

    main(args.number)
