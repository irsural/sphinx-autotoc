import os
from pathlib import Path
from collections import defaultdict
from typing import Iterator
import glob

from sphinx.util import logging
from sphinx.config import Config
from sphinx.application import Sphinx
from time import sleep

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
    logger.info('Running make_indexes...')
    app.config["root_doc"] = "service.index"
    make_indexes(Path(app.srcdir), app.config)


def setup(app: Sphinx) -> None:
    app.add_config_value("sphinx_autotoc_trim_folder_numbers", False, "html", bool)
    app.add_config_value("sphinx_autotoc_get_headers_from_subfolder", False, "html", bool)
    app.add_config_value("sphinx_autotoc_header", "Содержание", "html", str)
    app.connect('builder-inited', run_make_indexes, 250)


def make_indexes(docs_directory: Path, cfg: Config) -> None:
    """
    :param docs_directory: Путь к папке с документацией.
    :param cfg: Конфигурация Sphinx.
    """
    module_name = file_path = None
    if "sphinx.ext.autosummary" in cfg.extensions:
        logger.info("autosummary found!")
        module_name, file_path = parse_autosummary(docs_directory)
        logger.info(f"module_name: {module_name}, file_path: {file_path}")
    main_page = MAIN_PAGE
    index = docs_directory / SPHINX_INDEX_FILE_NAME
    index_md = (docs_directory / SPHINX_INDEX_FILE_NAME).with_suffix(".md")
    get_headers_from_subfolder = cfg["sphinx_autotoc_get_headers_from_subfolder"]
    header_text = cfg["sphinx_autotoc_header"]
    trim_folder_numbers = cfg["sphinx_autotoc_trim_folder_numbers"]

    if index_md.exists():
        os.remove(index_md)
    all_main_page_dirs = {}
    for root, sub_dict in _iter_dirs(docs_directory, cfg):
        main_page_dirs = []
        for sub, docs in sub_dict.items():
            if sub.name == "_autosummary":
                continue
            if sub != root:
                # Если sub == root то, директория не содержит вложенных директорий
                # В содержании данная директория показа как группа, но не
                # является таковой.
                _add_to_nav(sub, docs, trim_folder_numbers)
                main_page_dirs.append(sub)
            else:
                main_page_dirs.extend(docs)
        if get_headers_from_subfolder:
            main_page = _add_to_main_page(root, main_page_dirs, main_page, trim_folder_numbers)
        else:
            all_main_page_dirs.update({root: main_page_dirs})
    if not get_headers_from_subfolder:
        paths = ""
        for dir_path, dirs in all_main_page_dirs.items():
            paths += _make_search_paths(dir_path, dirs, True, False)
        main_page += TOCTREE.format(group_name=header_text, group_dirs=paths).replace("\f", "\n   ")

    with open(index, "w", encoding="utf8") as f:
        f.write(main_page.format(project=cfg.project, dop="=" * len(cfg.project)))

    if module_name and file_path:
        logger.info("Working on autosummary reference...")
        autosummary_index = _get_dir_index(file_path.parent)
        if autosummary_index.parent == docs_directory:
            autosummary_index = index
        with open(autosummary_index, 'r+', encoding="utf8") as f:
            f.seek(0)
            lines = f.readlines()
            for i, line in enumerate(lines):
                if file_path.name in line:
                    lines[i] = f"   API reference <_autosummary/{module_name}>\n"
            f.seek(0)
            f.writelines(lines)
            f.truncate()
        sleep(2)


def parse_autosummary(root: Path) -> tuple[str, Path] | tuple[None, None]:
    """
    Парсит файлы .rst в поисках автосаммари.

    :param root: Путь к папке с сайтом.
    :return: Имя модуля и путь к файлу с автосаммари.
    """
    files = [Path(file) for file in glob.glob(f"{root}/**/*.rst", recursive=True)]
    for file in files:
        with open(file, 'r') as f:
            lines = f.readlines()
            found_autosummary = False
            for i in range(len(lines)):
                if '.. autosummary::' in lines[i]:
                    found_autosummary = True
                elif found_autosummary and ':recursive:' in lines[i]:
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()
                        if len(next_line) > 1 and not next_line.startswith(':'):
                            return next_line, file
    return None, None


def _add_to_main_page(
    dir_path: Path,
    dirs: list[Path],
    main_page: str,
    trim_folder_numbers: bool
) -> str:
    """
    Добавляет дерево содержания папки в индексную страницу проекта.

    :param dir_path: Путь к папке.
    :param dirs: Список вложенных папок.
    :param main_page: Содержимое индексной страницы.
    :param trim_folder_numbers: Удалять ли номера папок.
    :return main_page: Изменённое содержимое индексной страницы.
    """
    search_paths = _make_search_paths(dir_path, dirs, True, True)
    dirname = trim_leading_numbers(dir_path.name) if trim_folder_numbers else dir_path.name
    main_page += TOCTREE.format(
        group_name=dirname, group_dirs=search_paths
    ).replace("\f", "\n   ")
    return main_page


def _add_to_nav(path: Path, docs: list[Path], trim_folder_numbers: bool) -> None:
    """
    Добавляет рядом с папкой её сервисный файл.

    В сервисном файле находится дерево содержания папки (toctree) и, если есть,
    содержимое файла README из этой папки

    :param path: Путь до папки.
    :param docs: Список файлов в папке.
    :param trim_folder_numbers: Удалять ли номера папок.
    """
    content = ""
    include_file = path / "README.md"
    if include_file.exists():
        with open(include_file.as_posix(), encoding="utf8") as f:
            content = f.read()

    index_path = _get_dir_index(path)
    dirname = trim_leading_numbers(path.name) if trim_folder_numbers else path.name
    search_paths = _make_search_paths(path, docs, False, True)
    with open(index_path.as_posix(), "w", encoding="utf-8") as f:
        f.write(
            NAV_PATTERN.format(
                dirname=dirname,
                search_paths=search_paths,
                includes=content,
            ).replace("\f", "\n   ")
        )


def trim_leading_numbers(input: str) -> str:
    """
    Убирает из начала строки номер

    1. Текст -> Текст

    :param input: Строка с номером
    :return: Строка без номера, если совпадает с шаблоном "123. строка"
    """
    split_path = input.split(".", maxsplit=1)
    if len(split_path) == 2:
        number, name = split_path
        if len(name) > 1:
            if number.isdigit() and name[0] == " ":
                name = name.lstrip()
                if name:
                    return name
    return input


def _get_dir_index(path: Path) -> Path:
    """
    Возвращает путь до сервисного файла папки.

    :param path: Путь до папки.
    :return: Путь до сервисного файла папки.
    """
    return path / f"{SPHINX_SERVICE_FILE_PREFIX}.{path.name}.rst"


def _make_search_paths(root: Path, f: list[Path], index: bool, get_headers_from_subfolder: bool) -> str:
    """
    Создает пути к содержимому в папке.

    Если содержимое - файл, добавляется путь к файлу (root/file.txt)
    Если содержимое - папка, добавляется путь к сервисному файлу этой папки (root/service.dir.rst)

    :param root: Корневая папка.
    :param f: Список содержимого корневой папки.
    :param index: Добавлять ли в путь к файлу корневую папку.
    :param get_headers_from_subfolder: Брать ли заголовки из подпапок.
    :return: Строка путей, разделённая символом \f.
    """
    search_paths = []
    for file in f:
        p = Path(root.name)
        tmp = "src" if get_headers_from_subfolder else ""
        if file.is_dir() and file.parent == root:
            p = tmp / p / file.name / _get_dir_index(file).name if index else Path(file.name) / _get_dir_index(file).name
        elif not file.is_dir():
            p = tmp / p / file.name if index else Path(file.name)
        else:
            continue

        if p.name.startswith("service.") and p.name.split(".")[1] == root.name:
            continue
        if p.as_posix() not in search_paths:
            search_paths.append(p.as_posix())
    search_paths.sort(key=lambda x: Path(x).stem.replace("service.", ""))
    return "\f".join(search_paths) + "\f"


def _iter_dirs(docs_directory: Path, cfg: Config) -> Iterator[tuple[Path, dict[Path, list[Path]]]]:
    """
    Итерируется по папке.
    Содержимое папки маршрутизируется и сортируется.

    :param docs_directory: Папка с документацией.
    :return: Кортеж из пути до папки и отсортированного содержимого этой папки.
    """
    if cfg["sphinx_autotoc_get_headers_from_subfolder"]:
        src_directory = docs_directory / 'src'
        if src_directory.exists() and src_directory.is_dir():
            docs_directory = src_directory

    mp = _flatmap(docs_directory, cfg)
    skeys = sorted(mp.keys())
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
        return any(part in IGNORE_LIST for part in p.parts)

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
