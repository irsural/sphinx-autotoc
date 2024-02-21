import os
import pytest
from pathlib import Path
from sphinx_autotoc import make_indexes, trim_leading_numbers
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

class TestMakeIndexes:
    def test_make_indexes_ok(self) -> None:
        path = Path(MAKE_INDEXES_TEST_PROJECTS_DIR) / "no_errors"
        cfg = activate_cfg(path)
        cfg.sphinx_autotoc_get_headers_from_subfolder = True
        make_indexes(path, cfg)
        assert os.path.isfile(path / "autotoc.rst")
        with open(path / "autotoc.rst", "r", encoding="utf8") as f:
            assert (
                    f.read()
                    == """No Errors Test Project
==========================================
.. toctree::
   :maxdepth: 2
   :caption: main

   main/index.rst
   
"""
            )

    def test_make_indexes_ignore_root(self) -> None:
        path = Path(MAKE_INDEXES_TEST_PROJECTS_DIR) / "no_root"

        cfg = Config.read(path)
        cfg.pre_init_values()
        cfg.init_values()

        make_indexes(path, cfg)
        assert os.path.isfile(path / "autotoc.rst")
        with open(path / "autotoc.rst", "r", encoding="utf8") as f:
            assert f.read() == """No Errors Test Project\n=========================================="""

    def test_make_indexes_show_hidden(self) -> None:
        path = Path(MAKE_INDEXES_TEST_PROJECTS_DIR) / "hidden_files"

        cfg = Config.read(path)
        cfg.pre_init_values()
        cfg.init_values()

        make_indexes(path, cfg)
        assert os.path.isfile(path / "autotoc.rst")
        with open(path / "autotoc.rst", "r", encoding="utf8") as f:
            assert (
                    f.read()
                    == """No Errors Test Project
==========================================
.. toctree::
   :maxdepth: 2
   :caption: .hiddendir

   .hiddendir/visible.rst
   

.. toctree::
   :maxdepth: 2
   :caption: main

   main/.hidden.rst
   main/index.rst
   
"""
            )

    def test_make_indexes_wrong_directory(self) -> None:
        path = Path(MAKE_INDEXES_TEST_PROJECTS_DIR) / "doesnotexist"
        with pytest.raises(ConfigError):
            cfg = Config.read(path)
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

    def test_make_indexes_default_flags(self):
        path = Path(MAKE_INDEXES_TEST_PROJECTS_DIR) / "3_levels_of_nesting"

        cfg = activate_cfg(path)

        make_indexes(path, cfg)
        assert os.path.isfile(path / "autotoc.rst")
        with open(path / "autotoc.rst", "r", encoding="utf8") as f:
            assert f.read() == """3 levels of nesting Test Project
====================================================
.. toctree::
   :maxdepth: 2
   :caption: Содержание

   src/1. level1/autotoc.1. level1.rst
   
"""

    def test_make_indexes_sf(self) -> None:
        path = Path(MAKE_INDEXES_TEST_PROJECTS_DIR) / "3_levels_of_nesting"

        cfg = activate_cfg(path)
        cfg.sphinx_autotoc_get_headers_from_subfolder = True

        make_indexes(path, cfg)
        assert os.path.isfile(path / "autotoc.rst")
        with open(path / "autotoc.rst", "r", encoding="utf8") as f:
            assert f.read() == """3 levels of nesting Test Project
====================================================
.. toctree::
   :maxdepth: 2
   :caption: 1. level1

   src/1. level1/2. level2/autotoc.2. level2.rst
   src/1. level1/l1.rst
   src/1. level1/l1.1.rst
   
"""

    def test_make_indexes_trim(self):
        path = Path(MAKE_INDEXES_TEST_PROJECTS_DIR) / "3_levels_of_nesting"

        cfg = activate_cfg(path)
        cfg.sphinx_autotoc_trim_folder_numbers = True
        make_indexes(path, cfg)
        rst = path / "src" / "1. level1" / "autotoc.1. level1.rst"

        assert rst.is_file()
        with open(rst, "r", encoding="utf8") as f:
            assert f.read() == """
level1
==========



.. toctree::
   :maxdepth: 2

   2. level2/autotoc.2. level2.rst
   l1.rst
   l1.1.rst
   
    """

    def test_make_indexes_sf_trim(self) -> None:
        path = Path(MAKE_INDEXES_TEST_PROJECTS_DIR) / "3_levels_of_nesting"

        cfg = activate_cfg(path)

        cfg.sphinx_autotoc_get_headers_from_subfolder = True
        cfg.sphinx_autotoc_trim_folder_numbers = True

        make_indexes(path, cfg)
        assert os.path.isfile(path / "autotoc.rst")
        with open(path / "autotoc.rst", "r", encoding="utf8") as f:
            assert f.read() == """3 levels of nesting Test Project
====================================================
.. toctree::
   :maxdepth: 2
   :caption: level1

   src/1. level1/2. level2/autotoc.2. level2.rst
   src/1. level1/l1.rst
   src/1. level1/l1.1.rst
   
"""

    def test_make_indexes_custom_header(self) -> None:
        path = Path(MAKE_INDEXES_TEST_PROJECTS_DIR) / "3_levels_of_nesting"

        cfg = activate_cfg(path)

        cfg.sphinx_autotoc_header = "custom header"
        make_indexes(path, cfg)
        assert os.path.isfile(path / "autotoc.rst")
        with open(path / "autotoc.rst", "r", encoding="utf8") as f:
            assert f.read() == """3 levels of nesting Test Project
====================================================
.. toctree::
   :maxdepth: 2
   :caption: custom header

   src/1. level1/autotoc.1. level1.rst
   
"""