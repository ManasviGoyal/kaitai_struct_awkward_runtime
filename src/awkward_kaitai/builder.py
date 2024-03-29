from __future__ import annotations

import argparse
import contextlib
import importlib.metadata
import os
import pathlib
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from typing import ContextManager, cast

import importlib_resources

import awkward_kaitai.data


def find_package_record_path() -> pathlib.Path:
    """Find the path to the RECORD for awkward_kaitai"""
    files = importlib.metadata.files("awkward_kaitai")
    if files is None:
        msg = "couldn't find RECORD for awkward_kaitai"
        raise FileNotFoundError(msg)

    record_path = next(p for p in files if p.name == "RECORD").locate()
    return pathlib.Path(os.fsdecode(record_path))


def find_cmake() -> Iterator[pathlib.Path]:
    """Find the paths of available CMake binaries"""
    with contextlib.suppress(ImportError):
        from cmake import CMAKE_BIN_DIR  # pylint: disable=import-outside-toplevel

        yield pathlib.Path(CMAKE_BIN_DIR) / "cmake"

    for candidate in "cmake3", "cmake":
        cmake_path = shutil.which(candidate)
        if cmake_path is not None:
            yield pathlib.Path(cmake_path)


def copy_file_with_stat(
    src: pathlib.Path, dst: pathlib.Path, stat_src: pathlib.Path
) -> None:
    """Copy a file to a destination, using another file's stat attributes"""
    shutil.copy(src, dst)
    shutil.copystat(stat_src, dst)


def get_awkward_version() -> str:
    """Get the version of Awkward Array"""
    return f"v{importlib.metadata.version('awkward')}"


def build_with_cmake(
    main_path: pathlib.Path,
    dest_path: pathlib.Path,
    configure_path: pathlib.Path | None,
    debug: bool,
) -> None:
    """Build an awkward-kaitai shared-object from the given paths"""
    try:
        cmake_path = next(find_cmake())
    except StopIteration:
        msg = "Could not find CMake binary. CMake can be found on PyPI and installed using `pip install cmake`"
        raise RuntimeError(msg) from None

    # Copy various CMake files into correct positions
    build_context: ContextManager[str | pathlib.Path]
    if configure_path is None:
        build_context = cast(
            ContextManager[str],
            tempfile.TemporaryDirectory(),  # pylint: disable=consider-using-with
        )
    else:
        build_context = contextlib.nullcontext(configure_path)

    with build_context as _temp_path:
        temp_path = pathlib.Path(_temp_path)
        temp_path.mkdir(exist_ok=True)

        files_path = importlib_resources.files(awkward_kaitai.data)
        record_path = find_package_record_path()

        # Load resources from the Python package
        with importlib_resources.as_file(
            files_path / "CMakeLists.txt"
        ) as cmakelists_path, importlib_resources.as_file(
            files_path / "kaitai_struct_cpp_stl_runtime-CMakeLists.txt"
        ) as kaitai_struct_cmakelists_path:
            # Copy resources to new temporary directory
            copy_file_with_stat(
                cmakelists_path, temp_path / "CMakeLists.txt", record_path
            )

            # Copy Katai Struct's CMakeLists.txt
            kaitai_struct_path = temp_path / "kaitai_struct_cpp_stl_runtime"
            kaitai_struct_path.mkdir(exist_ok=True)
            copy_file_with_stat(
                kaitai_struct_cmakelists_path,
                kaitai_struct_path / "CMakeLists.txt",
                record_path,
            )

        # Prepare build
        build_path = temp_path / "build"

        command = [
            cmake_path,
            "-S",
            str(temp_path),
            "-B",
            str(build_path),
            f"-DKAITAI_MAIN_FILE={main_path.resolve()}",
            f"-DCMAKE_INSTALL_PREFIX={dest_path.resolve()}",
            f"-DAWKWARD_VERSION={get_awkward_version()}",
        ]

        if debug:
            command += [
                "-DCMAKE_BUILD_TYPE=Debug",
                "-DCMAKE_CXX_FLAGS='-ggdb'",
            ]
        # Configure CMake
        subprocess.run(
            command,
            check=True,
        )

        # Run build
        subprocess.run(
            [cmake_path, "--build", str(build_path)],
            check=True,
        )

        # Install!
        subprocess.run(
            [cmake_path, "--install", str(build_path)],
            check=True,
        )


def main(argv: list[str] | None = None) -> None:
    """A CLI for building shared libraries that can read Awkward Array"""
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="main `.cpp` file to build", type=pathlib.Path)
    parser.add_argument(
        "-d",
        "--dest",
        type=pathlib.Path,
        help="explicitly specify a destination for the build shared library",
    )
    parser.add_argument(
        "-b", "--build", type=pathlib.Path, help="explicitly specify a build location"
    )
    parser.add_argument(
        "--debug",
        action=argparse.BooleanOptionalAction,
        help="build with debug symbols",
    )

    args = parser.parse_args(argv)

    dest = args.file.parent if args.dest is None else args.dest

    build_with_cmake(args.file, dest, args.build, args.debug)


if __name__ == "__main__":
    main()
