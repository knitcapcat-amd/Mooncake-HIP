import os
import re
from glob import glob

from setuptools import setup
import torch
from torch.utils.cpp_extension import BuildExtension, CUDAExtension


torch_version = re.match(r"\d+(?:\.\d+)*", torch.__version__).group()
version_suffix = "_" + torch_version.replace(".", "_")
module_name = "mooncake.ep" + version_suffix

abi_flag = int(torch._C._GLIBCXX_USE_CXX11_ABI)
current_dir = os.path.abspath(os.path.dirname(__file__))


def resolve_engine_extension() -> str:
    candidates = sorted(
        glob(os.path.join(current_dir, "../mooncake-wheel/mooncake/engine*.so")),
        key=lambda path: (os.path.basename(path) == "engine.so", path),
    )
    if not candidates:
        raise FileNotFoundError(
            "Mooncake engine extension not found under mooncake-wheel/mooncake"
        )
    return candidates[0]


setup(
    name=module_name,
    ext_modules=[
        CUDAExtension(
            name=module_name,
            include_dirs=[
                os.path.join(current_dir, "include"),
                os.path.join(current_dir, "../mooncake-transfer-engine/include"),
            ],
            sources=[
                "../mooncake-integration/ep/ep_py.cpp",
                "src/mooncake_ep_buffer.cpp",
                "src/mooncake_ep_kernel.cu",
                "src/mooncake_ibgda/mlx5gda.cpp",
            ],
            extra_compile_args={
                "cxx": [
                    f"-D_GLIBCXX_USE_CXX11_ABI={abi_flag}",
                    "-std=c++20",
                    "-O3",
                    "-g0",
                ],
                "nvcc": [
                    f"-D_GLIBCXX_USE_CXX11_ABI={abi_flag}",
                    "-std=c++20",
                    "-Xcompiler",
                    "-O3",
                    "-Xcompiler",
                    "-g0",
                ],
            },
            libraries=["ibverbs", "mlx5"],
            extra_objects=[
                resolve_engine_extension(),
            ],
        )
    ],
    cmdclass={"build_ext": BuildExtension},
)
