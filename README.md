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

У расширения есть два параметра, которые задаются переменными в **conf.py**.

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

## Пример

Рассмотрим проект со следующей структурой:

```bash
project
├── conf.py
├── ...
└── src
    ├── root.md
    ├── data
    │   ├── data1.rst
    │   └── data2.rst
    ├── another
    │   ├── instruction.rst
    │   └── website.rst
    └── hasinner
        ├── somefile.md
        └── inner
            └── needed_data.rst
```

### Один заголовок

Содержимое **conf.py**:

```python
sphinx_autotoc_get_headers_from_subfolder = False
sphinx_autotoc_header = "Содержание"
```

Вид сгенерированного содержания:

![sphinx_autotoc_get_headers_from_subfolder = False](https://imgur.com/xKokPBB.png)

### Несколько заголовков

Содержимое **conf.py**:

```python
sphinx_autotoc_get_headers_from_subfolder = True
```

Вид сгенерированного содержания:

![get_headers_from_subfolder = True](https://imgur.com/QLYnsIC.png)
