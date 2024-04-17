import os
from pathlib import Path
from textwrap import dedent

from sphinx_autotoc import _list_files
import pytest
from sphinx.config import Config
from sphinx.errors import ConfigError

from sphinx_autotoc import make_indexes, trim_leading_numbers

MAKE_INDEXES_TEST_PROJECTS_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "make_indexes_test_projects"
)


def activate_cfg(path: Path) -> Config:
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

    @pytest.mark.parametrize("original,modified", [
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
    ])
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

    @pytest.mark.parametrize("test_file_path, test_file_line", [
        (project_path / "autotoc.rst",
         "   L1header <src/1. level1/_autosummary/Level1>\n"),
        (project_path / "src/1. level1/autotoc.1. level1.rst",
         "   L1header <_autosummary/Level1>\n"),
        (project_path / "src/1. level1/2. level2/autotoc.2. level2.rst",
         "   l2header <_autosummary/Level2>\n"),
        (project_path / "src/1. level1/2. level2/3. level3/autotoc.3. level3.rst",
         "   l3 <_autosummary/Level3>\n"),
    ])
    def test_autosummary_in_several_levels(self, test_file_path: Path, test_file_line: str) -> None:
        cfg = activate_cfg(self.project_path)
        cfg.add('autosummary_generate', True, 'html', bool)
        cfg["sphinx_autotoc_get_headers_from_subfolder"] = True
        cfg.post_init_values()
        make_indexes(self.project_path, cfg)
        assert os.path.isfile(test_file_path)
        with open(test_file_path) as f:
            lines = f.readlines()
            assert test_file_line in lines


class TestListFiles:

    @pytest.mark.parametrize(["dir_structure", "expected_paths", "excluded_patterns"], [
        (["root_file.rst",
          "dir1/file1.rst",
          "dir2/file3.rst"], {Path(item) for item in [
                              ".",
                              "root_file.rst",
                              "dir1",
                              "dir1/file1.rst",
                              "dir2",
                              "dir2/file3.rst"]}, []),
        (["dir1/file1.rst",
          "empty_directory"], {Path(item) for item in [
                               "dir1",
                               "dir1/file1.rst"]}, ""),
        (["dir1/file1.rst",
          "_dir2/file2.rst",
          "dir1/_hidden_subdir/subfile.rst"], {Path(item) for item in [
                                               "dir1/file1.rst",
                                               "dir1"]}, []),
        (["_root_file.rst",
          "dir1/file1.rst",
          "dir2/_file2.rst"], {Path(item) for item in [
                               ".",
                               "_root_file.rst",
                               "dir1",
                               "dir1/file1.rst",
                               "dir2",
                               "dir2/_file2.rst",]}, []),
        (["shown_folder/visible_file.rst",
          "hidden_folder/file.rst",
          "mixed_folder/hidden_file.rst",
          "mixed_folder/visible_file.rst"], {Path(item) for item in [
                                             "mixed_folder",
                                             "shown_folder",
                                             "shown_folder/visible_file.rst",
                                             "mixed_folder/visible_file.rst"]}, ["*hidden*"]),
        (["rst/rst-file.rst",
          "txt/txt-file.txt"], {Path(item) for item in [
                                "rst",
                                "rst/rst-file.rst"]}, [])
    ])
    def test_list_files(self, dir_structure: list[Path], expected_paths, tmp_path, excluded_patterns):
        for item in dir_structure:
            item = tmp_path / item
            if item.suffix == '':
                item.mkdir(parents=True, exist_ok=True)
            else:
                item.parent.mkdir(parents=True, exist_ok=True)
                item.touch()

        result = _list_files(tmp_path, excluded_patterns)
        assert result == expected_paths
