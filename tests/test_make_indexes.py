import os
import pytest
from pathlib import Path
from sphinx_autotoc import make_indexes, trim_leading_numbers
from sphinx.config import Config
from sphinx.errors import ConfigError

MAKE_INDEXES_TEST_PROJECTS_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "make_indexes_test_projects"
)
NESTING_PROJECT_PATH = Path(MAKE_INDEXES_TEST_PROJECTS_DIR) / "3_levels_of_nesting"

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
        cfg = activate_cfg(NESTING_PROJECT_PATH)

        make_indexes(NESTING_PROJECT_PATH, cfg)
        assert os.path.isfile(NESTING_PROJECT_PATH / "autotoc.rst")
        with open(NESTING_PROJECT_PATH / "autotoc.rst", "r", encoding="utf8") as f:
            assert f.read() == """3 levels of nesting Test Project
====================================================
.. toctree::
   :maxdepth: 2
   :caption: Содержание

   src/1. level1/autotoc.1. level1.rst
   
"""

    def test_make_indexes_sf(self) -> None:
        cfg = activate_cfg(NESTING_PROJECT_PATH)

        cfg.sphinx_autotoc_get_headers_from_subfolder = True

        make_indexes(NESTING_PROJECT_PATH, cfg)
        assert os.path.isfile(NESTING_PROJECT_PATH / "autotoc.rst")
        with open(NESTING_PROJECT_PATH / "autotoc.rst", "r", encoding="utf8") as f:
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
        cfg = activate_cfg(NESTING_PROJECT_PATH)

        cfg.sphinx_autotoc_trim_folder_numbers = True

        make_indexes(NESTING_PROJECT_PATH, cfg)
        rst = NESTING_PROJECT_PATH / "src" / "1. level1" / "autotoc.1. level1.rst"
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
        cfg = activate_cfg(NESTING_PROJECT_PATH)

        cfg.sphinx_autotoc_get_headers_from_subfolder = True
        cfg.sphinx_autotoc_trim_folder_numbers = True

        make_indexes(NESTING_PROJECT_PATH, cfg)
        assert os.path.isfile(NESTING_PROJECT_PATH / "autotoc.rst")
        with open(NESTING_PROJECT_PATH / "autotoc.rst", "r", encoding="utf8") as f:
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
        cfg = activate_cfg(NESTING_PROJECT_PATH)

        cfg.sphinx_autotoc_header = "custom header"
        make_indexes(NESTING_PROJECT_PATH, cfg)
        assert os.path.isfile(NESTING_PROJECT_PATH / "autotoc.rst")
        with open(NESTING_PROJECT_PATH / "autotoc.rst", "r", encoding="utf8") as f:
            assert f.read() == """3 levels of nesting Test Project
====================================================
.. toctree::
   :maxdepth: 2
   :caption: custom header

   src/1. level1/autotoc.1. level1.rst
   
"""