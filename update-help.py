#!/usr/bin/env python3

"""Update the ``help()`` outputs  in ``docs/api.rst``."""

import contextlib
import io
import pathlib
import re

import graphviz

ALL_CLASSES = [graphviz.Graph, graphviz.Digraph, graphviz.Source]

ARGS_LINE = re.compile(r'(?:class | \| {2})\w+\(')

WRAP_AFTER = 80

WRAP_SEARCH, WRAP_REPL = re.compile(r'(,)[ ](?!\*)'), r'\1\n{indent} '

INDENT = ' ' * 4

TARGET = pathlib.Path('docs/api.rst')

PATTERN = (r'''
           (
           \ {{4}}>>>\ help\(graphviz\.{cls_name}\).*\n)
           \ {{4}}Help\ on\ class\ {cls_name}
                  \ in\ module\ graphviz\.(?:graphs|sources):\n
           \ {{4}}<BLANKLINE>\n
           (?:.*\n)+?
           \ {{4}}<BLANKLINE>\n
           ''')

ENCODING = 'utf-8'


def get_help(obj) -> str:
    print(f'capture help() output for {obj}')
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        help(obj)
    buf.seek(0)
    return ''.join(iterlines(buf))


def iterlines(lines, *, wrap_after: int = WRAP_AFTER, line_indent: str = INDENT):
    for line in lines:
        line = line.rstrip() + '\n'
        line = line.replace("``'\\n'``", "``'\\\\n'``")

        if len(line) > wrap_after and ARGS_LINE.match(line):
            line, sep, rest = line.rpartition(' -> ')
            if sep:
                return_annotation = sep + rest
            else:
                line = rest
                return_annotation = ''

            indent = line_indent + ' ' * line.index('(')
            repl = WRAP_REPL.format(indent=indent)

            line, n_newlines = WRAP_SEARCH.subn(repl, line)
            print(len(line), 'character line wrapped into',
                  n_newlines + 1, 'lines')
            assert n_newlines, 'wrapped long argument line'

            line += return_annotation

        yield line_indent + line


help_docs = {cls.__name__: get_help(cls) for cls in ALL_CLASSES}

print('read', TARGET)
target = target_before = TARGET.read_text(encoding=ENCODING)

for cls_name, doc in help_docs.items():
    print('replace', cls_name, 'section')

    pattern = re.compile(PATTERN.format(cls_name=cls_name), flags=re.VERBOSE)

    target, found = pattern.subn(fr'\1{doc}', target, count=1)
    assert found, f'replaced {cls_name} section'

    target = target.replace(INDENT + '\n', INDENT + '<BLANKLINE>\n')

if target == target_before:
    print('unchanged')
else:
    print('write', TARGET)
    print(target_before.count('\n'), 'lines before')
    print(target.count('\n'), 'lines after')

    TARGET.write_text(target, encoding=ENCODING)