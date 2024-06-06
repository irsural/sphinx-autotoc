import os
from collections import defaultdict
from pathlib import Path
from typing import Iterator

from natsort import natsorted
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.errors import ExtensionError
from sphinx.util import logging
from sphinx.util.matching import Matcher

logger = logging.getLogger(__name__)
SPHINX_SERVICE_FILE_PREFIX = 'autotoc'
SPHINX_INDEX_FILE_NAME = 'autotoc.rst'
NAV_PATTERN = """
{dirname}
==========
{includes}

.. toctree::
   :maxdepth: 2

   {search_paths}
"""

MAIN_PAGE = """
{project}
==================={dop}="""

TOCTREE = """
.. toctree::
   :maxdepth: 2
   :caption: {group_name}

   {group_dirs}
"""


def run_make_indexes(app: Sphinx) -> None:
    logger.info('Running make_indexes...')
    app.config['root_doc'] = 'autotoc'
    make_indexes(Path(app.srcdir), app.config)


def setup(app: Sphinx) -> None:
    app.add_config_value('sphinx_autotoc_trim_folder_numbers', False, 'html', bool)
    app.add_config_value('sphinx_autotoc_get_headers_from_subfolder', False, 'html', bool)
    app.add_config_value('sphinx_autotoc_header', 'Содержание', 'html', str)
    app.connect('builder-inited', run_make_indexes, 250)


def make_indexes(docs_directory: Path, cfg: Config) -> None:
    """
    :param docs_directory: Путь к папке с документацией.
    :param cfg: Конфигурация Sphinx.
    """
    main_page = MAIN_PAGE
    index = docs_directory / SPHINX_INDEX_FILE_NAME
    get_headers_from_subfolder = cfg['sphinx_autotoc_get_headers_from_subfolder']
    header_text = cfg['sphinx_autotoc_header']
    trim_folder_numbers = cfg['sphinx_autotoc_trim_folder_numbers']
    src_path = docs_directory / 'src'
    _check_folder_existence(src_path)
    autosummary_flag = _check_autosummary_flag(cfg)
    autosummary_dict: dict[Path, tuple[str, str]] = {}

    main_page_dirs: dict[Path, list[Path]] = {}  # toctree header: toctree links

    if not get_headers_from_subfolder:
        main_page_dirs = {src_path: []}

    for current_dir, current_dir_files in _iter_dirs(docs_directory, cfg):
        _process_dir_and_files(
            src_path,
            current_dir,
            current_dir_files,
            autosummary_flag,
            autosummary_dict,
            get_headers_from_subfolder,
            main_page_dirs,
            trim_folder_numbers,
        )

    main_page = _add_to_main_page(
        main_page_dirs, main_page, trim_folder_numbers, get_headers_from_subfolder, header_text
    )

    with open(index, 'w', encoding='utf8') as f:
        f.write(main_page.format(project=cfg.project, dop='=' * len(cfg.project)))

    if autosummary_flag:
        _replace_autosummary(autosummary_dict, docs_directory, index)


def _check_autosummary_flag(cfg: Config) -> bool:
    if 'sphinx.ext.autosummary' in cfg.extensions and cfg.autosummary_generate:
        logger.info('autosummary found!')
        return True
    return False


def _process_dir_and_files(
    src_path: Path,
    current_dir: Path,
    current_dir_files: list[Path],
    autosummary_flag: bool,
    autosummary_dict: dict[Path, tuple[str, str]],
    get_headers_from_subfolder: bool,
    main_page_dirs: dict[Path, list[Path]],
    trim_folder_numbers: bool,
) -> None:
    if autosummary_flag:
        for file in current_dir_files:
            if file.name == 'autotoc.autosummary.rst':
                autosummary_info = _parse_autosummary(current_dir / file)
                if autosummary_info:
                    autosummary_dict[current_dir / file] = autosummary_info

    if current_dir.name == '_autosummary':
        return

    if current_dir != src_path:
        _add_to_nav(current_dir, current_dir_files, trim_folder_numbers)

    _update_main_page_dirs(
        main_page_dirs, get_headers_from_subfolder, current_dir, src_path, current_dir_files
    )


def _update_main_page_dirs(
    main_page_dirs: dict[Path, list[Path]],
    get_headers_from_subfolder: bool,
    current_dir: Path,
    src_path: Path,
    current_dir_files: list[Path],
) -> None:
    if get_headers_from_subfolder:
        if current_dir.parent == src_path:
            main_page_dirs.update({current_dir: current_dir_files})
    else:
        if current_dir == src_path:
            main_page_dirs[src_path].extend(current_dir_files)
        elif current_dir.parent == src_path:
            main_page_dirs[src_path].append(Path(current_dir.name))


def _check_folder_existence(folder: Path) -> None:
    if not folder.exists() or not any(folder.iterdir()):
        errormsg = f'Папка {folder} не существует или пуста.'
        raise ExtensionError(errormsg)


def _replace_autosummary(
    autosummary_dict: dict[Path, tuple[str, str]], docs_directory: Path, index: Path
) -> None:
    """
    Меняет заголовок ссылки на autosummary на заголовок файла с директивой autosummary.

    :param autosummary_dict: Словарь с путями к файлам с директивой autosummary.
    :param docs_directory: Путь к папке с документацией.
    :param index: Путь к индексной странице.
    """
    for file_path, (file_header, module_name) in autosummary_dict.items():
        if any((file_header, module_name, file_path)) is None:
            continue
        logger.debug('module name: %s, file path:%s', module_name, file_path)
        logger.info('Working on autosummary reference...')
        autosummary_index = _get_dir_index(file_path.parent)
        if autosummary_index.parent == docs_directory:
            autosummary_index = index
        elif autosummary_index.parent.parent == docs_directory / 'src':
            _replace_autosummary_with_api_reference(index, file_path, module_name, file_header)
        _replace_autosummary_with_api_reference(
            autosummary_index, file_path, module_name, file_header
        )


def _replace_autosummary_with_api_reference(
    index: Path, file_path: Path, module_name: str, autosummary_header: str
) -> None:
    """
    Заменяет ссылку на autosummary в индексной странице на ссылку на API reference.

    :param index: Путь к индексной странице.
    :param file_path: Путь к файлу с autosummary.
    :param module_name: Имя модуля autosummary.
    :param autosummary_header: Заголовок для autosummary.
    """
    with open(index, 'r+', encoding='utf8') as f:
        f.seek(0)
        lines = f.readlines()
        for i, line in enumerate(lines):
            if file_path.name in line:
                lines[i] = (
                    f"   {autosummary_header} <"
                    f"{Path(line.strip()).parent / '_autosummary' / module_name}>\n"
                )
        f.seek(0)
        f.writelines(lines)
        f.truncate()


def _parse_autosummary(file: Path) -> tuple[str, str] | None:
    """
    Парсит файл с директивой autosummary.

    :param file: Путь к файлу с директивой
    :return: Заголовок файла и имя модуля.
    """
    with open(file) as f:
        lines = f.readlines()
        for i in range(len(lines)):
            if lines[i].strip() == '.. autosummary::':
                break
        for j in range(i + 1, len(lines)):
            next_line = lines[j].strip()
            if len(next_line) > 1 and not next_line.startswith(':'):
                return lines[0].strip(), next_line
    return None


def _add_to_main_page(
    dirs: dict[Path, list[Path]],
    main_page: str,
    trim_folder_numbers: bool,
    get_headers_from_subfolder: bool,
    header_text: str,
) -> str:
    """
    Добавляет дерево содержания папок в индексную страницу проекта.

    :param dirs: Словарь с содержанием папок
    :param main_page: Содержимое индексной страницы.
    :param trim_folder_numbers: Удалять ли номера папок.
    :return main_page: Изменённое содержимое индексной страницы.
    """
    for path, docs in dirs.items():
        search_paths = _make_search_paths(path, docs)
        dirname = trim_leading_numbers(path.name) if trim_folder_numbers else path.name
        str_search_paths: list[str] = []
        if get_headers_from_subfolder:
            for item in search_paths:
                str_search_paths.append(f'src/{path.name}/{item}')
        else:
            for item in search_paths:
                str_search_paths.append(f'{path.name}/{item}')
        main_page += TOCTREE.format(
            group_name=dirname if get_headers_from_subfolder else header_text,
            group_dirs='\n   '.join(str_search_paths),
        )
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
    content = ''
    include_file = path / 'README.md'
    if include_file.exists():
        with open(include_file.as_posix(), encoding='utf8') as f:
            content = f.read()

    index_path = _get_dir_index(path)
    dirname = trim_leading_numbers(path.name) if trim_folder_numbers else path.name
    search_paths = _make_search_paths(path, docs)
    with open(index_path.as_posix(), 'w', encoding='utf-8') as f:
        f.write(
            NAV_PATTERN.format(
                dirname=dirname,
                search_paths='\n   '.join(map(str, search_paths)),
                includes=content,
            )
        )


def trim_leading_numbers(input: str) -> str:
    """
    Убирает из начала строки номер

    >>> trim_leading_numbers("1. Текст")
    'Текст'

    :param input: Строка с номером
    :return: Строка без номера, если совпадает с шаблоном "123. строка"
    """
    split_path = input.split('.', maxsplit=1)
    if len(split_path) == 2:
        number, name = split_path
        name = name.lstrip()
        if number.isdigit() and name:
            return name
    return input


def _get_dir_index(path: Path) -> Path:
    """
    Возвращает путь до сервисного файла папки.

    :param path: Путь до папки.
    :return: Путь до сервисного файла папки.
    """
    return path / f'{SPHINX_SERVICE_FILE_PREFIX}.{path.name}.rst'


def _make_search_paths(root: Path, f: list[Path]) -> list[Path]:
    """
    Создает пути к содержимому в папке.

    Если содержимое - файл, добавляется путь к файлу (root/file.txt)

    Если содержимое - папка, добавляется путь к файлу содержания этой папки
    (root/dir/autotoc.dir.rst)

    Итоговый список содержит пути к папкам и файлам, отсортированные по типу: сначала идут
    папки, отсортированные по алфавиту, затем - файлы, также отсортированные по алфавиту.

    :param root: Корневая папка.
    :param f: Список содержимого корневой папки.
    :return: Список путей к содержимому в папке.
    """
    file_paths = set()
    folder_paths = set()
    for file in f:
        if (root / file).is_dir():
            file /= _get_dir_index(file).name
            folder_paths.add(file)
        else:
            # Если смотрим файл содержания текущей папки
            if file.stem == f'{SPHINX_SERVICE_FILE_PREFIX}.{root.name}':
                continue

            file_paths.add(file)

    file_paths_list = natsorted(file_paths, key=lambda x: Path(x).stem)
    folder_paths_list = natsorted(
        folder_paths,
        key=lambda x: Path(x).stem.replace(f'{SPHINX_SERVICE_FILE_PREFIX}.', ''),
    )
    return folder_paths_list + file_paths_list


def _iter_dirs(docs_directory: Path, cfg: Config) -> Iterator[tuple[Path, list[Path]]]:
    """
    Итерируется по папке.
    Содержимое папки маршрутизируется и сортируется.

    :param docs_directory: Папка с документацией.
    :return: Кортеж из пути до папки и отсортированного содержимого этой папки.
    """
    mp = _flatmap(docs_directory, cfg)
    skeys = natsorted(mp.keys())
    for root in skeys:
        sub = natsorted(mp[root])
        yield root, sub


def _flatmap(docs_directory: Path, cfg: Config) -> dict[Path, set[Path]]:
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
            (project/main/index.rst, project/main/second.rst)
        },
        {project/data:
            (project/data/table.rst)
        },
        {project/data/inner_dir:
            (project/data/inner_dir/data.rst)
        }

    :param docs_directory: Папка с документацией.
    :return: Маршруты файлов в папке
    """
    roots: dict[Path, set[Path]] = defaultdict(set)
    for file in _list_files(docs_directory, cfg['exclude_patterns'], cfg['source_suffix']):
        if file.parent.name and (
            file.suffix in cfg.source_suffix or (docs_directory / file).is_dir()
        ):
            roots[docs_directory / file.parent].add(Path(file.name))
    return roots


def _list_files(
    docs_directory: Path, exclude_patterns: list[str], source_suffixes: list[str] | dict[str, str]
) -> set[Path]:
    """
    Составляет список файлов в папках. Игнорирует файлы и папки, указанные в параметре
    exclude_patterns в конфигурации.

    :param docs_directory: Папка с документацией.
    :return: Пути к файлам.
    """
    result = set()
    matcher = Matcher(exclude_patterns)
    if type(source_suffixes) is dict:
        source_suffixes = source_suffixes.keys()  # type: ignore[assignment]
    for root, _, files in os.walk(docs_directory):
        root_path = Path(root)
        relative_root = root_path.relative_to(docs_directory)

        if matcher(root):
            continue

        for file in files:
            file_path = relative_root / file

            underscored = relative_root.name.startswith('_')
            excluded = matcher(str(file_path))
            not_an_rst = file_path.suffix not in source_suffixes

            if underscored or excluded or not_an_rst:
                continue

            result.add(file_path)
            # [:-1] в родителях файла исключает '.'
            parent_dirs = list(file_path.parents)[:-1]
            for parent_dir in parent_dirs:
                result.add(parent_dir)

    return result
