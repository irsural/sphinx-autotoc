# sphinx-autotoc

**sphinx-autotoc** - это расширение [Sphinx](https://www.sphinx-doc.org/en/master/)
для автоматической генерации содержания сайта 
([toctree](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#table-of-contents)).

Для корректной работы расширения, исходные файлы документации должны находиться в папке `src`, в корне документации.

## Использование

### Установка

```bash
pip install sphinx-autotoc
``` 

Расширение добавляется в файл конфигурации sphinx (**conf.py**), так же как и другие расширения sphinx:

```python
extensions = [
    ...
    'sphinx_autotoc',
    ...
]
```

### Настройка

У расширения есть 3 параметра, которые задаются переменными в **conf.py**.

#### ``sphinx_autotoc_get_headers_from_subfolder``

Определяет способ генерации заголовков в содержании.

Заголовок содержания - это некликабельный текст, с помощью которого можно 
разделить содержание на логические части.

Возможные значения:

- ``False``

  В содержании будет один заголовок, текст для которого указывается в ``sphinx_autotoc_header`` (см. ниже),

  Каждая папка внутри **src** станет кликабельным элементом содержания.

  Отдельные документы (.rst, .md) внутри папки **src** также будут отображаться в содержании.
  
- ``True``

  Количество заголовков в содержании будет равно количеству папок в папке **src**. Текст заголовков будет
  взят из названий этих папок.

  Папки второго уровня (например, **src/header_folder/content_folder**) станут кликабельными элементами
  содержания.
  
  Отдельные документы внутри папки **src** не будут отображаться в содержании.

Значение по умолчанию - ``False``.

#### ``sphinx_autotoc_header`` 

Используется только при ``sphinx_autotoc_get_headers_from_subfolder = False``.

Задает текст заголовка. Значение по умолчанию - **Содержание**.

#### ``sphinx_autotoc_trim_folder_numbers``

По умолчанию сортировка папок в содержании происходит по алфавиту.

Для того чтобы папки в содержании располагались в нужном порядке, можно добавить числа в начало названий папок.

Данный флаг определяет, нужно ли удалять числа из названий папок в содержании.

Возможные значения: 

- ``False``

  В содержание сайта выводится полное название папки

- ``True``

  В содержании сайта выводится название папки без числа в начале

  Папки должны быть пронумерованы следующим образом:
  
  ``<folder_order>. <folder_name>``
  
  , где:
  
    * **<folder_order>** - число, определяющее порядок папки в содержании сайта

    * **<folder_name>** - название папки

Значение по умолчанию - ``False``

Для того, чтобы папка не попала в содержание, её название должно начинаться с `_`

## Пример

Рассмотрим проект со следующей структурой:

```bash
project
├── conf.py
├── ...
└── src
    ├── _hidden_folder
    ├── root.md
    ├── 1. data
    │   ├── data1.rst
    │   └── data2.rst
    ├── 2. another
    │   ├── instruction.rst
    │   └── website.rst
    └── hasinner
        ├── 1. somefile.md
        └── 2. inner
            └── needed_data.rst
```

### Один заголовок

Содержимое **conf.py**:

```python
sphinx_autotoc_get_headers_from_subfolder = False
sphinx_autotoc_header = "Содержание"
```

Вид сгенерированного содержания:

![no subfolders, no trimming numbers](docs/images/no_sf_no_trim.png)

### Несколько заголовков

Содержимое **conf.py**:

```python
sphinx_autotoc_get_headers_from_subfolder = False
```

Вид сгенерированного содержания:

![subfolders, no trimming numbers](docs/images/sf_no_trim.png)

### Один заголовок, отключены числа в содержании

Содержимое **conf.py**:

```python
sphinx_autotoc_trim_folder_numbers = True
sphinx_autotoc_get_headers_from_subfolder = False
sphinx_autotoc_header = "Содержание"
```

Вид сгенерированного содержания:

![no subfolders, trim numbers](docs/images/no_sf_trim.png)

### Несколько заголовков, отключены числа в содержании

Содержимое **conf.py**:

```python
sphinx_autotoc_trim_folder_numbers = True
sphinx_autotoc_get_headers_from_subfolder = True
```

Вид сгенерированного содержания:

![subfolders, trim numbers](docs/images/sf_trim.png)


sphinx-autotoc взаимодействует с содержанием сайта, поэтому возможны конфликты с другими расширениями.


### Автоматическая генерация документации по коду

При использовании расширения 
[sphinx.ext.autosummary](https://www.sphinx-doc.org/en/master/usage/extensions/autosummary.html)
необходимо назвать файл, в котором указываются директивы autosummary
**autotoc.autosummary.rst**.

Особая обработка autosummary будет запущена только если выполняются **все** 
нижеперечисленные условия:

1. Включено расширение **sphinx.ext.autosummary**
2. Включено расширение **sphinx_autotoc**
3. Включен флаг **autosummary_generate** в **conf.py** (включен по умолчанию)
4. Файл с директивами autosummary назван **autotoc.autosummary.rst**
5. Первая строка файла с директивами - заголовок ссылки для этого файла
6. В файле с директивами указан документируемый модуль, класс или функция.
7. Документируемый модуль: 
   * либо добавлен в **sys.path** в **conf.py** (`sys.path.insert(0, os.path('path_to_module'))`)
   * либо установлен в том окружении, из которого запускается Sphinx

В противном случае, ссылка будет отображаться и вести себя неправильно.

Пример **conf.py**:

```python
extensions = [
    ...,
    'sphinx.ext.autosummary',
    ...
]
autosummary_generate = True
```

Пример файла **autotoc.autosummary.rst**:

```rst
.. autosummary::
   :toctree: _autosummary
   :recursive:
   
   module
```
`module` - название документируемого модуля.