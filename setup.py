import os

from copy import copy
from dataclasses import dataclass
from dataclasses import field
from setuptools import setup, find_packages

from typing import List, Set

setup_package = os.environ.get("SETUP_PACKAGE", None)
install_optional = os.environ.get("INSTALL_OPTIONAL", "TRUE")


@dataclass
class PyPackage:
    requires: List[str] = field(default_factory=list)
    optional: List[str] = field(default_factory=list)
    requires_packages: List[str] = field(default_factory=list)
    data: List[str] = field(default_factory=list)


all_refact_packages = {
    "code_contrast": PyPackage(
        requires=["cdifflib", "termcolor", "numpy", "dataclasses"]),
    "refact_known_models": PyPackage(),
    "refact_utils": PyPackage(),
    "refact_data_pipeline": PyPackage(
        requires=["numpy", "tokenizers>=0.15.0", "torch", "requests>=2.31.0", "cloudpickle", "blobfile",
                  "tqdm", "dataclasses_json", "termcolor", 'more_itertools', "cdifflib",
                  "ujson", "zstandard", "scipy", "einops", "matplotlib", "giturlparse",
                  "jsonlines", "binpacking", "filelock", "tables==3.8.0", "pygments", "kshingle"],
        requires_packages=["code_contrast", "self_hosting_machinery", "refact_utils"],
        data=["git_command.exp"],
    ),
    "refact_webgui": PyPackage(
        requires=["aiohttp", "aiofiles", "cryptography", "fastapi==0.100.0", "giturlparse", "pydantic>=2",
                  "starlette==0.27.0", "uvicorn", "uvloop", "termcolor", "python-multipart", "more_itertools",
                  "scyllapy==1.3.0", "pandas>=2.0.3",
                  # NOTE: litellm has bug with anthropic streaming, so we're staying on this version for now
                  "litellm==1.34.42",
                  ],
        requires_packages=["refact_known_models", "refact_utils"],
        data=["webgui/static/*", "webgui/static/components/modals/*",
              "webgui/static/dashboards/*", "webgui/static/assets/*", "webgui/static/utils/*",]),
    "self_hosting_machinery": PyPackage(
        requires=["python-multipart", "auto-gptq==0.7.1", "accelerate",
                  "termcolor", "torch", "transformers>=4.39.3",
                  "bitsandbytes", "safetensors", "peft", "triton",
                  "torchinfo", "mpi4py", "deepspeed==0.14.2",
                  "sentence-transformers", "huggingface-hub>=0.19.3",
                  "aiohttp", "setproctitle"],
        optional=["ninja", "flash-attn"],
        requires_packages=["refact_known_models", "refact_data_pipeline",
                           "refact_webgui", "refact_utils"],
        data=["watchdog/watchdog.d/*"]),
}


def find_required_packages(packages: Set[str]) -> Set[str]:
    updated_packages = copy(packages)
    for name in packages:
        assert name in all_refact_packages, f"Package {name} not found in repo"
        updated_packages.update(all_refact_packages[name].requires_packages)
    if updated_packages != packages:
        return find_required_packages(updated_packages)
    return packages


def get_install_requires(packages):
    install_requires = list({
        required_package
        for py_package in packages.values()
        for required_package in py_package.requires
    })
    if install_optional.upper() == "TRUE":
        install_requires.extend(list({
            required_package
            for py_package in packages.values()
            for required_package in py_package.optional
        }))
    return install_requires


if setup_package is not None:
    if setup_package not in all_refact_packages:
        raise ValueError(f"Package {setup_package} not found in repo")
    setup_packages = {
        name: py_package
        for name, py_package in all_refact_packages.items()
        if name in find_required_packages({setup_package})
    }
else:
    setup_packages = all_refact_packages

setup(
    name="refact-self-hosting",
    version="1.6.2",
    py_modules=list(setup_packages.keys()),
    package_data={
        name: py_package.data
        for name, py_package in setup_packages.items()
        if py_package.data
    },
    packages=find_packages(include=(
        f"{name}*" for name in setup_packages
    )),
    install_requires=get_install_requires(setup_packages),
)
