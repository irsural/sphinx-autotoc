import os
from pathlib import Path
from textwrap import dedent

import pytest
from sphinx.config import Config
from sphinx.errors import ConfigError

from sphinx_autotoc import _list_files, make_indexes, trim_leading_numbers

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


def setup_list_files_dir(tmp_path: Path, folders: list[str], files: list[str]) -> None:
    root = tmp_path / 'src'
    root.mkdir()
    for folder in folders:
        (root / folder).mkdir(parents=True)
    for file in files:
        (root / file).touch()


class TestListFiles:
    def test_list_files_ok(self, tmp_path: Path) -> None:
        setup_list_files_dir(
            tmp_path,
            ['folder1/folder11', 'folder1/folder12'],
            [
                'folder1/1.rst',
                'folder1/folder11/11.rst',
                'folder1/folder12/12.rst',
            ],
        )
        set = _list_files(tmp_path, [])
        expected = {
            Path(item)
            for item in [
                'src',
                'src/folder1',
                'src/folder1/1.rst',
                'src/folder1/folder11',
                'src/folder1/folder11/11.rst',
                'src/folder1/folder12',
                'src/folder1/folder12/12.rst',
            ]
        }
        assert set == expected

    def test_list_files_empty_directory(self, tmp_path: Path) -> None:
        setup_list_files_dir(tmp_path, ['folder1/folder12'], ['folder1/1.rst'])
        set = _list_files(tmp_path, [])
        assert Path('src/folder1/folder12') not in set

    def test_list_files_empty_directory_with_rst_in_subdirectory(self, tmp_path: Path) -> None:
        setup_list_files_dir(tmp_path, ['folder1/folder12'], ['folder1/folder12/12.rst'])
        set = _list_files(tmp_path, [])
        assert Path('src/folder1') in set

    def test_list_files_non_rst_files(self, tmp_path: Path) -> None:
        setup_list_files_dir(tmp_path, [], ['1.txt', '2.py'])
        assert _list_files(tmp_path, []) == set()

    def test_list_files_mixed_files(self, tmp_path: Path) -> None:
        setup_list_files_dir(
            tmp_path, ['folder1'], ['folder1/1.rst', 'folder1/2.py', 'folder1/3.txt']
        )
        expected = {Path(item) for item in ['src', 'src/folder1/1.rst', 'src/folder1']}
        assert _list_files(tmp_path, []) == expected

    def test_list_files_underscored_subdirs(self, tmp_path: Path) -> None:
        setup_list_files_dir(tmp_path, ['folder1', '_folder2'], ['folder1/1.rst', '_folder2/2.rst'])
        expected = {Path(item) for item in ['src', 'src/folder1', 'src/folder1/1.rst']}
        assert _list_files(tmp_path, []) == expected

    @pytest.mark.parametrize(
        'folders, files, exclude_patterns, expected',
        [
            (
                # в корневой папке
                [],
                ['1.rst', '2.rst', 'excluded_file.rst'],
                ['**excluded_file.rst'],
                {'', '1.rst', '2.rst'},
            ),
            (
                # файл в подпапке, но не в корне
                ['a'],
                ['excluded_file.rst', 'a/1.rst', 'a/2.rst', 'a/excluded_file.rst'],
                ['**a/excluded_file.rst'],
                {'', 'a', 'a/1.rst', 'a/2.rst', 'excluded_file.rst'},
            ),
            (
                # файл и в подпапке, и в корне
                ['b'],
                ['excluded_file.rst', 'b/1.rst', 'b/2.rst', 'b/excluded_file.rst'],
                ['**excluded_file.rst'],
                {'', 'b', 'b/1.rst', 'b/2.rst'},
            ),
            (
                # файл в корне, но не в подпапке
                ['c'],
                ['1.rst', 'excluded_file.rst', 'c/2.rst', 'c/excluded_file.rst'],
                ['*/excluded_file.rst'],
                {'', '1.rst', 'c', 'c/2.rst', 'c/excluded_file.rst'},
            ),
            (
                # все файлы с одинаковым началом/концом
                [],
                ['bad_file.rst', 'bad_table.rst', 'bad_images.rst', 'good_file.rst'],
                ['**bad*'],
                {'', 'good_file.rst'},
            ),
            (
                # все файлы c 1-значным номером
                [],
                ['good_1.rst', 'good_2.rst', 'good_11.rst'],
                ['**good_?.rst'],
                {'', 'good_11.rst'},
            ),
            (
                # папки
                ['d1', 'd2', 'excluded_folder'],
                ['d1/1.rst', 'd2/2.rst', 'excluded_folder/other.rst'],
                ['**excluded_folder**'],
                {'', 'd1', 'd1/1.rst', 'd2', 'd2/2.rst'}
            )
        ],
    )
    def test_list_files_exclude_patterns_files(
        self,
        tmp_path: Path,
        folders: list[str],
        files: list[str],
        exclude_patterns: list[str],
        expected: list[str],
    ) -> None:
        setup_list_files_dir(tmp_path, folders, files)
        expected_paths = {Path('src', item) for item in expected}
        assert _list_files(tmp_path, exclude_patterns) == expected_paths
