import os
import pytest
from pathlib import Path
from sphinx_autotoc import make_indexes, trim_leading_numbers
from sphinx.config import Config
from sphinx.errors import ConfigError

MAKE_INDEXES_TEST_PROJECTS_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "make_indexes_test_projects"
)


class TestMakeIndexes:
    def test_make_indexes_ok(self) -> None:
        path = Path(MAKE_INDEXES_TEST_PROJECTS_DIR) / "no_errors"

        cfg = Config.read(path)
        cfg.pre_init_values()
        cfg.init_values()

        make_indexes(path, cfg)
        assert os.path.isfile(path / "service.index.rst")
        with open(path / "service.index.rst", "r", encoding="utf8") as f:
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
        assert os.path.isfile(path / "service.index.rst")
        with open(path / "service.index.rst", "r", encoding="utf8") as f:
            assert f.read() == """No Errors Test Project\n=========================================="""

    def test_make_indexes_show_hidden(self) -> None:
        path = Path(MAKE_INDEXES_TEST_PROJECTS_DIR) / "hidden_files"

        cfg = Config.read(path)
        cfg.pre_init_values()
        cfg.init_values()

        make_indexes(path, cfg)
        assert os.path.isfile(path / "service.index.rst")
        with open(path / "service.index.rst", "r", encoding="utf8") as f:
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
        ("5678.foo", "5678.foo"),
        ("1234. text with 5678 number", "text with 5678 number"),
        ("1234. 5678. double number dot", "5678. double number dot"),
        ("5678.\nnew line", "5678.\nnew line"),
    ])
    def test_trim_leading_numbers(self, original: str, modified: str) -> None:
        assert trim_leading_numbers(original) == modified
