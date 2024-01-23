# Sphinx-Autotoc

Sphinx-Autotoc - это расширение Python для Sphinx, которое позволяет автоматически создавать оглавления (TOC).

Для корректного использования расширения файлы документации должны находиться в папке `src` в корне документации.

## Установка

Для установки Sphinx-Autotoc используется pip:

```bash
pip install sphinx-autotoc
``` 

## Использование

Для использования Sphinx-Autotoc необходимо добавить его в конфигурационный файл Sphinx (conf.py):

```python
extensions = [
    ...
    'sphinx_autotoc',
    ...
]
```

У расширения есть два параметра, которые также можно задать в conf.py

* `sphinx_autotoc_get_headers_from_subfolder` - формат заголовков первого уровня, бинарное значение (True или False).  
   * При `False` (по умолчанию) создаётся один заголовок с текстом из параметра `sphinx_autotoc_header`  
   * При `True` создаётся по одному заголовку для каждой папки в `src`, с текстом - названием папки
     ВНИМАНИЕ! При использовании `sphinx_autotoc_get_headers_from_subfolder = True` файлы документации из `src` в содержании указываться не будут!
* `sphinx_autotoc_header` - текст заголовка при отключенном `sphinx_autotoc_get_headers_from_subfolder`, текстовое значение  
   * По умолчанию - "Содержание".


Для проекта с структурой файлов
```bash
project
├── conf.py
├── index.rst
├── requirements.txt
├── src
│   ├── root.md
│   ├── data
│   │   ├── data1.rst
│   │   └── data2.rst
│   ├── another
│   │   ├── instruction.rst
│   │   └── website.rst
│   └── hasinner
│       ├── somefile.md
│       └── inner
│           └── needed_data.rst
└── _static_local
    └── css
        └── custom.css
```
содержание без sphinx_autotoc_get_headers_from_subfolder будет следующим:


![Содержание при sphinx_autotoc_get_headers_from_subfolder = False](https://imgur.com/xKokPBB.png)

С включенным sphinx_autotoc_get_headers_from_subfolder содержание будет таким:


![Содержание при sphinx_autotoc_get_headers_from_subfolder = True](https://imgur.com/QLYnsIC.png)