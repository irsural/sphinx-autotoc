import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Iterator
from sphinx.util import logging
from sphinx.config import Config
from sphinx.application import Sphinx

logger = logging.getLogger(__name__)
SPHINX_SERVICE_FILE_PREFIX = "service"
SPHINX_INDEX_FILE_NAME = f"{SPHINX_SERVICE_FILE_PREFIX}.index.rst"
IGNORE_LIST = {".git", ".idea", "logs", ".venv", ".vscode"}
NAV_PATTERN = """
{dirname}
==========

{includes}

.. toctree::
   :maxdepth: 2

   {search_paths}
    """

MAIN_PAGE = """{project}
==================={dop}="""

TOCTREE = """
.. toctree::
   :maxdepth: 2
   :caption: {group_name}

   {group_dirs}
"""


def run_make_indexes(app: Sphinx) -> None:
    app.config["root_doc"] = "service.index"
    app.config["exclude_patterns"].extend(IGNORE_LIST)
    make_indexes(Path(app.srcdir), app.config)


def setup(app: Sphinx) -> None:
    logger.info('Running make_indexes...')
    app.connect('builder-inited', run_make_indexes)


def make_indexes(docs_directory: Path, cfg: Config) -> None:
    """
    :param docs_directory: Путь к папке с документацией.
    :param cfg: Конфигурация Sphinx.
    """
    main_page = MAIN_PAGE
    index = docs_directory / SPHINX_INDEX_FILE_NAME
    index_md = (docs_directory / SPHINX_INDEX_FILE_NAME).with_suffix(".md")
    if index_md.exists():
        os.remove(index_md)
    for root, sub_dict in _iter_dirs(docs_directory, cfg):
        main_page_dirs = []
        for sub, docs in sub_dict.items():
            if sub != root:
                # Если sub == root то, директория не содержит вложенных директорий
                # В содержании данная директория показа как группа, но не
                # является таковой.
                _add_to_nav(sub, docs)
                main_page_dirs.append(sub)
            else:
                main_page_dirs.extend(docs)
        main_page = _add_to_main_page(root, main_page_dirs, main_page)

    with open(index, "w", encoding="utf8") as f:
        f.write(main_page.format(project=cfg.project, dop="=" * len(cfg.project)))


def _add_to_main_page(
    dir_path: Path,
    dirs: list[Path],
    main_page: str,
) -> str:
    """
    Добавляет дерево содержания папки в индексную страницу проекта.

    :param dir_path: Путь к папке.
    :param dirs: Список вложенных папок.
    :param main_page: Содержимое индексной страницы.
    :return main_page: Изменённое содержимое индексной страницы.
    """
    search_paths = _make_search_paths(dir_path, dirs)
    main_page += TOCTREE.format(
        group_name=dir_path.stem, group_dirs=search_paths
    ).replace("\f", "\n   ")
    return main_page


def _add_to_nav(path: Path, docs: list[Path]) -> None:
    """
    Добавляет рядом с папкой её сервисный файл.

    В сервисном файле находится дерево содержания папки (toctree) и, если есть,
    содержимое файла README из этой папки

    :param path: Путь до папки.
    :param docs: Список файлов в папке.
    """
    content = ""
    include_file = path / "README.md"
    if include_file.exists():
        with open(include_file.as_posix(), encoding="utf8") as f:
            content = f.read()

    index_path = _get_dir_index(path)

    pat = re.search(r"(\d\.\s)?(.*)", path.stem)  # 1. Text
    if pat:
        dirname_with_no_heading_nums = pat.group(2)
    else:
        return
    search_paths = _make_search_paths(path, docs)
    with open(index_path.as_posix(), "w", encoding="utf-8") as f:
        f.write(
            NAV_PATTERN.format(
                dirname=dirname_with_no_heading_nums,
                search_paths=search_paths,
                includes=content,
            ).replace("\f", "\n   ")
        )


def _get_dir_index(path: Path) -> Path:
    """
    Возвращает путь до сервисного файла папки.

    :param path: Путь до папки.
    :return: Путь до сервисного файла папки.
    """
    return path.parent / f"{SPHINX_SERVICE_FILE_PREFIX}.{path.name}.rst"


def _make_search_paths(root: Path, f: list[Path]) -> str:
    """
    Создает пути к содержимому в папке.

    Если содержимое - файл, добавляется путь к файлу (root/file.txt)
    Если содержимое - папка, добавляется путь к сервисному файлу этой папки (root/service.dir.rst)

    :param root: Корневая папка.
    :param f: Список содержимого корневой папки.
    :return: Строка путей, разделённая символом \f.
    """
    search_paths = []
    for file in sorted(f, key=lambda x: x.stem.replace("service.", "")):
        p = Path(root.name)
        if file.is_dir() and file.parent == root:
            p /= _get_dir_index(file).name
        elif not file.is_dir():
            p /= file.name
        else:
            continue
        if p.as_posix() not in search_paths:
            search_paths.append(p.as_posix())

    return "\f".join(search_paths) + "\f"


def _iter_dirs(docs_directory: Path, cfg: Config) -> Iterator[tuple[Path, dict[Path, list[Path]]]]:
    """
    Итерируется по папке.
    Содержимое папки маршрутизируется и сортируется.

    :param docs_directory: Папка с документацией.
    :return: Кортеж из пути до папки и отсортированного содержимого этой папки.
    """
    mp = _flatmap(docs_directory, cfg)
    skeys = sorted(mp.keys(), key=lambda k: (len(k.parts), k.stem))
    for root in skeys:
        sub = mp[root]
        docs = {}
        for k, v in sub.items():
            docs[k] = sorted(v)
        yield root, docs


def _flatmap(docs_directory: Path, cfg: Config) -> dict[Path, dict[Path, set[Path]]]:
    """
        Составляет маршруты файлов с искомыми суффиксами.
    Суффиксы файлов берутся из конфигурационного файла изначальной папки.
    Для проекта project со структурой
    ::
        project
        ├── main
        │   ├── index.rst
        │   └── second.rst
        ├── data
        │   ├── inner_dir
        │   │   └── data.rst
        │   └── table.rst
        └── root.rst

    маршруты будут:
    ::
        {project/main:
            {project/main:
                (project/main/index.rst, project/main/second.rst)
                },
        {project/data:
            {project/data:
                (project/data/table.rst)
            },
            {project/data/inner_dir:
                (project/data/inner_dir/data.rst)
            }
        }

    :param docs_directory: Папка с документацией.
    :return: Маршруты файлов в папке
    """
    roots: dict[Path, dict[Path, set[Path]]] = {}
    for file in _list_files(docs_directory):
        if file.parent.name and file.suffix in cfg.source_suffix.keys():
            parents = list(reversed(file.parents))
            relative_group = parents[1]
            abs_group = docs_directory / relative_group
            if roots.get(abs_group) is None:
                roots[abs_group] = defaultdict(set)
            parts = [file, *file.parents]
            # Если i - путь до директории, то i-1, его файл или каталог
            # -2, так как "." и group не нужны
            if len(parts) == 3:
                roots[abs_group][abs_group].add(docs_directory / file)
            else:
                for i, p in enumerate(parts[1:-2]):
                    roots[abs_group][docs_directory / p].add(docs_directory / parts[i])
    return roots


def _list_files(docs_directory: Path) -> set[Path]:
    """
    Составляет список файлов в папках. Игнорирует файлы и папки, указанные в IGNORE_LIST

    :param docs_directory: Папка с документацией.
    :return: Пути к файлам.
    """
    result = set()

    def _should_ignore(p: Path) -> bool:
        return any(ignored in str(p) for ignored in IGNORE_LIST)

    for root, dirs, files in os.walk(docs_directory):
        if _should_ignore(Path(root)):
            continue

        # Filter out ignored directories and their contents
        dirs[:] = [d for d in dirs if not _should_ignore(Path(os.path.join(root, d)))]

        for file in files:
            if _should_ignore(Path(os.path.join(root, file))):
                continue
            result.add(
                Path(os.path.relpath(os.path.join(root, file), start=docs_directory))
            )

        for directory in dirs:
            result.add(
                Path(
                    os.path.relpath(os.path.join(root, directory), start=docs_directory)
                )
            )

    return result
