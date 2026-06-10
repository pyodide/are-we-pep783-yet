import datetime
import json
import re

import pytz
import requests_cache

BASE_URL = "https://pypi.org"

# The PEP 783 platform tag for Pyodide/Emscripten wheels
PYEMSCRIPTEN_TAG_RE = re.compile(r"pyemscripten_\d+_\d+_wasm32")

# css_class values for packages that work in Pyodide today, either via a
# PEP 783 wheel on PyPI or via a pyodide-recipes build.
WORKS_IN_PYODIDE = {"success", "recipe", "recipe-pure-py"}

DEPRECATED_PACKAGES = {
    "BeautifulSoup",
    "bs4",
    "distribute",
    "django-social-auth",
    "nose",
    "pep8",
    "pycrypto",
    "pypular",
    "sklearn",
}

# Keep responses for one hour
SESSION = requests_cache.CachedSession("requests-cache", expire_after=60 * 60)


def get_json_url(package_name):
    return f"{BASE_URL}/pypi/{package_name}/json"


def normalize(name):
    # PEP 503 normalization.
    return re.sub(r"[-_.]+", "-", name).lower()


def get_pyodide_recipe_packages():
    print("Getting pyodide-recipes package list...")
    with open("pyodide-recipes-packages.json") as f:
        data = json.load(f)
    return set(data["packages"]), set(data["patched_packages"])


def annotate_wheels(packages, recipe_packages, patched_packages):
    print("Getting wheel data...")
    num_packages = len(packages)
    for index, package in enumerate(packages):
        print(index + 1, num_packages, package["name"])

        response = SESSION.get(get_json_url(package["name"]))
        if response.status_code != 200:
            print(" ! Skipping " + package["name"])
            continue
        data = response.json()
        info = data["info"]

        has_pep783_wheel = False
        has_pure_python_wheel = False
        # info["version"] is what PyPI considers the latest stable release.
        for f in data["releases"].get(info["version"], []):
            if f["packagetype"] != "bdist_wheel":
                continue
            # The wheel filename is:
            # {distribution}-{version}(-{build tag})?-{python tag}-{abi tag}-{platform tag}.whl
            # https://packaging.python.org/en/latest/specifications/binary-distribution-format/#file-name-convention
            tags = f["filename"].removesuffix(".whl").split("-")
            abi_tag, platform_tag = tags[-2], tags[-1]
            if PYEMSCRIPTEN_TAG_RE.search(platform_tag):
                has_pep783_wheel = True
            if abi_tag == "none":
                has_pure_python_wheel = True

        has_recipe = normalize(package["name"]) in recipe_packages
        has_patch = normalize(package["name"]) in patched_packages

        package["wheel"] = has_pep783_wheel
        if has_pep783_wheel:
            package["css_class"] = "success"
            package["icon"] = "🟢"
            package["title"] = "Ships a PEP 783 pyemscripten wheel on PyPI."
        elif has_pure_python_wheel and has_patch:
            package["css_class"] = "recipe-pure-py"
            package["icon"] = "🩹"
            package["title"] = (
                "Pure Python on PyPI, but needed a pyodide-recipes patch to work on Pyodide."
            )
        elif has_recipe and not has_pure_python_wheel:
            package["css_class"] = "recipe"
            package["icon"] = "🔧"
            package["title"] = "Built from source via a pyodide-recipes recipe."
        elif has_pure_python_wheel:
            package["css_class"] = "pure-py"
            package["icon"] = "🐍"
            package["title"] = "Pure Python wheel. Likely works on Pyodide as-is."
        else:
            # is there any left, based on pythonwheels.com?
            package["css_class"] = "todo"
            package["icon"] = "❌"
            package["title"] = "No PEP 783 wheel, recipe, or pure Python wheel yet."


def get_top_packages():
    print("Getting packages...")

    with open("top-pypi-packages.json") as data_file:
        packages = json.load(data_file)["rows"]

    # Rename keys
    for package in packages:
        package["downloads"] = package.pop("download_count")
        package["name"] = package.pop("project")

    return packages


def not_deprecated(package):
    return package["name"] not in DEPRECATED_PACKAGES


def remove_irrelevant_packages(packages, limit):
    print("Removing cruft...")
    active_packages = list(filter(not_deprecated, packages))
    return active_packages[:limit]


def save_to_file(packages, file_name):
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    with open(file_name, "w") as f:
        f.write(
            json.dumps(
                {
                    "data": packages,
                    "last_update": now.strftime("%A, %d %B %Y, %X %Z"),
                },
                indent=1,
            )
        )
