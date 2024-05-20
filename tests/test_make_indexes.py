import os
import pytest
from textwrap import dedent
from pathlib import Path
from shutil import rmtree
from sphinx_autotoc import make_indexes, trim_leading_numbers, _make_search_paths
from sphinx.config import Config
from sphinx.errors import ConfigError

MAKE_INDEXES_TEST_PROJECTS_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "make_indexes_test_projects"
)


def activate_cfg(path: Path):
    cfg = Config.read(path)
    cfg.pre_init_values()
    cfg.init_values()
    cfg.add("sphinx_autotoc_trim_folder_numbers", False, "html", bool)
    cfg.add("sphinx_autotoc_get_headers_from_subfolder", False, "html", bool)
    cfg.add("sphinx_autotoc_header", "Содержание", "html", str)
    return cfg


def test_make_indexes_wrong_directory() -> None:
    path = Path(MAKE_INDEXES_TEST_PROJECTS_DIR) / "doesnotexist"
    with pytest.raises(ConfigError):
        cfg = activate_cfg(path)
        make_indexes(path, cfg)


class TestTrimLeadingNumbers:
    @pytest.mark.parametrize(
        "original,modified",
        [
            ("1425. faire46", "faire46"),
            ("No leading number", "No leading number"),
            ("", ""),
            ("   42. with spaces", "   42. with spaces"),
            ("1234. !@#$%^&*()", "!@#$%^&*()"),
            ("1234.", "1234."),
            ("5678.foo", "foo"),
            ("1234. text with 5678 number", "text with 5678 number"),
            ("1234. 5678. double number dot", "5678. double number dot"),
            ("5678.\nnew line", "new line"),
        ],
    )
    def test_trim_leading_numbers(self, original: str, modified: str) -> None:
        assert trim_leading_numbers(original) == modified


class TestMakeIndexesFlags:
    project_path = Path(MAKE_INDEXES_TEST_PROJECTS_DIR, "3_levels_of_nesting")

    def test_make_indexes_default_flags(self) -> None:
        cfg = activate_cfg(self.project_path)

        make_indexes(self.project_path, cfg)
        assert os.path.isfile(self.project_path / "autotoc.rst")
        with open(self.project_path / "autotoc.rst", encoding="utf8") as f:
            assert f.read() == dedent("""
            3 levels of nesting Test Project
            ====================================================
            .. toctree::
               :maxdepth: 2
               :caption: Содержание
            
               src/1. level1/autotoc.1. level1.rst
            """)

    def test_make_indexes_sf(self) -> None:
        cfg = activate_cfg(self.project_path)

        cfg["sphinx_autotoc_get_headers_from_subfolder"] = True

        make_indexes(self.project_path, cfg)
        assert os.path.isfile(self.project_path / "autotoc.rst")
        with open(self.project_path / "autotoc.rst", encoding="utf8") as f:
            assert f.read() == dedent("""
            3 levels of nesting Test Project
            ====================================================
            .. toctree::
               :maxdepth: 2
               :caption: 1. level1
            
               src/1. level1/2. level2/autotoc.2. level2.rst
               src/1. level1/l1.rst
               src/1. level1/l1.1.rst
            """)

    def test_make_indexes_trim(self) -> None:
        cfg = activate_cfg(self.project_path)

        cfg["sphinx_autotoc_trim_folder_numbers"] = True

        make_indexes(self.project_path, cfg)
        rst = self.project_path / "src" / "1. level1" / "autotoc.1. level1.rst"
        assert rst.is_file()
        with open(rst, encoding="utf8") as f:
            assert f.read() == dedent("""
            level1
            ==========
            
            
            .. toctree::
               :maxdepth: 2
            
               2. level2/autotoc.2. level2.rst
               l1.rst
               l1.1.rst
            """)

    def test_make_indexes_sf_trim(self) -> None:
        cfg = activate_cfg(self.project_path)

        cfg["sphinx_autotoc_get_headers_from_subfolder"] = True
        cfg["sphinx_autotoc_trim_folder_numbers"] = True

        make_indexes(self.project_path, cfg)
        assert os.path.isfile(self.project_path / "autotoc.rst")
        with open(self.project_path / "autotoc.rst", encoding="utf8") as f:
            assert f.read() == dedent("""
            3 levels of nesting Test Project
            ====================================================
            .. toctree::
               :maxdepth: 2
               :caption: level1
            
               src/1. level1/2. level2/autotoc.2. level2.rst
               src/1. level1/l1.rst
               src/1. level1/l1.1.rst
               """)

    def test_make_indexes_custom_header(self) -> None:
        cfg = activate_cfg(self.project_path)

        cfg["sphinx_autotoc_header"] = "custom header"
        make_indexes(self.project_path, cfg)
        assert os.path.isfile(self.project_path / "autotoc.rst")
        with open(self.project_path / "autotoc.rst", encoding="utf8") as f:
            assert f.read() == dedent("""
            3 levels of nesting Test Project
            ====================================================
            .. toctree::
               :maxdepth: 2
               :caption: custom header
            
               src/1. level1/autotoc.1. level1.rst
               """)


class TestAutosummaryCompatibility:
    project_path = Path(MAKE_INDEXES_TEST_PROJECTS_DIR, "autosummary_test")

    @pytest.mark.parametrize(
        "test_file_path, test_file_line",
        [  # type: ignore[misc]
            (
                project_path / "autotoc.rst",
                "   L1header <src/1. level1/_autosummary/Level1>\n",
            ),
            (
                project_path / "src/1. level1/autotoc.1. level1.rst",
                "   L1header <_autosummary/Level1>\n",
            ),
            (
                project_path / "src/1. level1/2. level2/autotoc.2. level2.rst",
                "   l2header <_autosummary/Level2>\n",
            ),
            (
                project_path
                / "src/1. level1/2. level2/3. level3/autotoc.3. level3.rst",
                "   l3 <_autosummary/Level3>\n",
            ),
        ],
    )
    def test_autosummary_in_several_levels(
        self, test_file_path: Path, test_file_line: str
    ) -> None:
        cfg = activate_cfg(self.project_path)
        cfg.add("autosummary_generate", True, "html", bool)
        cfg.sphinx_autotoc_get_headers_from_subfolder = True
        make_indexes(self.project_path, cfg)
        assert os.path.isfile(test_file_path)
        with open(test_file_path) as f:
            lines = f.readlines()
            assert test_file_line in lines


def prepare_search_paths(root: Path, file_list: list[str], folder_list: list[str]) -> list[Path]:
    for folder in folder_list:
        (root / folder).mkdir()

    for file in file_list:
        (root / file).touch()

    full_list = [Path(item) for item in file_list + folder_list]
    return _make_search_paths(root, full_list)


class TestMakeSearchPaths:

    def test_search_paths_add_files(self, tmp_path):
        search_paths = prepare_search_paths(
            tmp_path,
                ["file.rst"],
            []
        )
        assert search_paths == [Path("file.rst")]

    def test_search_paths_ignore_autotoc_of_current_folder(self, tmp_path) -> None:
        search_paths = prepare_search_paths(
            tmp_path,
            [f"autotoc.{tmp_path.name}.rst"],
            []
        )
        assert Path(f"autotoc.{tmp_path.name}.rst") not in search_paths

    def test_search_paths_add_folders(self, tmp_path):
        search_paths = prepare_search_paths(
            tmp_path,
            [],
            ["folder1"]
        )
        assert search_paths == [Path("folder1/autotoc.folder1.rst")]

    def test_search_paths_ignore_autotoc_of_current_folder(self, search_paths_list) -> None:
        assert Path("autotoc.src.rst") not in search_paths_list

    def test_search_paths_folders_before_files(self, tmp_path):
        search_paths = prepare_search_paths(
            tmp_path,
            ["file1.rst", "file2.rst",],
            ["folder1", "folder2"]
        )
        assert search_paths == [ Path(item) for item in [
            "folder1/autotoc.folder1.rst",
            "folder2/autotoc.folder2.rst",
            "file1.rst",
            "file2.rst"
        ]], "Папки должны идти в содержании раньше файлов"
