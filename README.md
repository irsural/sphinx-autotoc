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

У расширения есть три параметра, которые задаются переменными в **conf.py**.

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

Определяет, нужно ли удалять числа из названий папок в содержании.

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

## Пример

Рассмотрим проект со следующей структурой:

```bash
project
├── conf.py
├── ...
└── src
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

![no subfolders, no numbers](https://i.imgur.com/rL5p5fI.png)

### Несколько заголовков

Содержимое **conf.py**:

```python
sphinx_autotoc_get_headers_from_subfolder = False
```

Вид сгенерированного содержания:

![subfolders, no numbers](https://i.imgur.com/6GoK1hj.png)

### Один заголовок, отключены числа в содержании

Содержимое **conf.py**:

```python
sphinx_autotoc_trim_folder_numbers = True
sphinx_autotoc_get_headers_from_subfolder = False
sphinx_autotoc_header = "Содержание"
```

Вид сгенерированного содержания:

![sphinx_autotoc_get_headers_from_subfolder = False](https://imgur.com/xKokPBB.png)

### Несколько заголовков, отключены числа в содержании

Содержимое **conf.py**:

```python
sphinx_autotoc_trim_folder_numbers = True
sphinx_autotoc_get_headers_from_subfolder = True
```

Вид сгенерированного содержания:

![get_headers_from_subfolder = True](https://imgur.com/QLYnsIC.png)
