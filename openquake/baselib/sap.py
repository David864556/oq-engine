# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2020 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
"""
``openquake.baselib.sap`` is a Simple Argument Parser based on argparse
which is extremely powerful. Its features are

1. zero boilerplate (no decorators)
2. supports arbitrarily nested subcommands with an easy sintax
3. automatically generates a simple parser from a Python module and
   a hierarchic parser from a Python package.

Here is a minimal example of usage:
￼
.. code-block:: python

 >>> def convert_archive(input_, output=None, inplace=False, *, out='/tmp'):
 ...    "Example"
 ...    print(input_, output, inplace, out)
 >>> convert_archive.input_ = 'input file or archive'
 >>> convert_archive.inplace = 'convert inplace'
 >>> convert_archive.output = 'output archive'
 >>> convert_archive.out = 'output directory'
 >>> parser(convert_archive, 'app').print_help()
 usage: app [-h] [-i] [-o /tmp] input [output]
 <BLANKLINE>
 Example
 <BLANKLINE>
 positional arguments:
   input                input file or archive
   output               output archive
 <BLANKLINE>
 optional arguments:
   -h, --help           show this help message and exit
   -i, --inplace        convert inplace
   -o /tmp, --out /tmp  output directory
 >>> run(convert_archive, argv=['a.zip', 'b.zip'])
 a.zip b.zip False /tmp
 >>> run(convert_archive, argv=['a.zip', '-i', '-o', '/tmp/x'])
 a.zip None True /tmp/x
"""

import os
import inspect
import argparse
import importlib

NODEFAULT = object()


def _choices(choices):
    # returns {choice1, ..., choiceN} or the empty string
    if choices:
        return '{%s}' % ', '.join(map(str, choices))
    return ''


def _populate(parser, func):
    # populate the parser
    # args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, anns
    argspec = inspect.getfullargspec(func)
    if argspec.varargs:
        raise TypeError('varargs in the signature of %s are not supported'
                        % func)
    defaults = argspec.defaults or ()
    nodefaults = len(argspec.args) - len(defaults)
    alldefaults = (NODEFAULT,) * nodefaults + defaults
    argdef = dict(zip(argspec.args, alldefaults))
    argdef.update(argspec.kwonlydefaults or {})
    parser.description = func.__doc__
    parser.set_defaults(_func=func)
    parser.aliases = {}
    argdescr = []  # list of pairs (argname, argkind)
    for arg in argspec.args:
        if argdef[arg] is False:
            argdescr.append((arg, 'flg'))
        else:
            argdescr.append((arg, 'pos'))
    for arg in argspec.kwonlyargs:
        argdescr.append((arg, 'opt'))
    abbrevs = {'-h'}  # already taken abbreviations
    for name, kind in argdescr:
        if name.endswith('_'):
            # make it possible use bultins/keywords as argument names
            stripped = name.rstrip('_')
            parser.aliases[stripped] = name
        else:
            stripped = name
        descr = getattr(func, name, '')
        if isinstance(descr, str):
            kw = dict(help=descr)
        else:  # assume a dictionary
            kw = descr.copy()
        if kw.get('type') is None and type in func.__annotations__:
            kw.setdefault('type', func.__annotations__['type'])
        abbrev = kw.get('abbrev')
        choices = kw.get('choices')
        default = argdef[name]
        if kind == 'pos':
            if default is not NODEFAULT:
                kw['default'] = default
                kw.setdefault('nargs', '?')
                if default is not None:
                    kw['help'] += ' [default: %s]' % repr(default)
        elif kind == 'flg':
            kw.setdefault('abbrev', abbrev or '-' + name[0])
            kw['action'] = 'store_true'
        elif kind == 'opt':
            kw.setdefault('abbrev', abbrev or '-' + name[0])
            if default not in (None, NODEFAULT):
                kw['default'] = default
                kw.setdefault('metavar', _choices(choices) or str(default))
        abbrev = kw.pop('abbrev', None)
        longname = '--' + stripped.replace('_', '-')
        if abbrev and abbrev in abbrevs:
            # avoid conflicts with previously defined abbreviations
            args = longname,
        elif abbrev:
            if len(abbrev) > 2:  # no single-letter abbrev
                args = longname, abbrev
            else:  # single-letter abbrev
                args = abbrev, longname
            abbrevs.add(abbrev)
        else:
            # no abbrev
            args = stripped,
        parser.add_argument(*args, **kw)


def _rec_populate(parser, funcdict):
    subparsers = parser.add_subparsers(
        help='available subcommands; use %s <subcmd> --help' % parser.prog)
    for name, func in funcdict.items():
        subp = subparsers.add_parser(name, prog=parser.prog + ' ' + name)
        if isinstance(func, dict):  # nested subcommand
            _rec_populate(subp, func)
        else:  # terminal subcommand
            _populate(subp, func)


def find_main(pkgname):
    """
    :param pkgname: name of a packake (i.e. myapp.plot) with "main" functions
    :returns: a dictionary name -> func_or_subdic

    If pkgname actually refers to a module, the main function of the module
    is returned (or an AttributeError is raised, if missing)
    """
    pkg = importlib.import_module(pkgname)
    if not hasattr(pkg, '__path__'):  # is a module, not a package
        return pkg.main
    dic = {}
    for path in pkg.__path__:
        for name in os.listdir(path):
            fname = os.path.join(path, name)
            dotname = pkgname + '.' + name
            if os.path.isdir(fname) and '__init__.py' in os.listdir(fname):
                subdic = find_main(dotname)
                if subdic:
                    dic[name] = subdic
            elif name.endswith('.py') and name != '__init__.py':
                mod = importlib.import_module(dotname[:-3])
                if hasattr(mod, 'main'):
                    dic[name[:-3]] = mod.main
    return dic


def parser(funcdict, prog=None, description=None, version=None):
    """
    :param funcdict: a function or a nested dictionary of functions
    :param prog: the name of the associated command line application
    :param description: description of the application
    :param version: version of the application printed with --version
    :returns: an ArgumentParser instance
    """
    parser = argparse.ArgumentParser(prog, description=description)
    if version:
        parser.add_argument(
            '-v', '--version', action='version', version=version)
    if isinstance(funcdict, str):  # passed a package name
        funcdict = find_main(funcdict)
    if callable(funcdict):
        _populate(parser, funcdict)
    else:
        _rec_populate(parser, funcdict)
    return parser


def _run(parser, argv):
    namespace = parser.parse_args(argv)
    try:
        func = namespace.__dict__.pop('_func')
    except KeyError:
        parser.print_usage()
        return
    if hasattr(parser, 'aliases'):
        # go back from stripped to unstripped names
        dic = {parser.aliases.get(name, name): value
               for name, value in vars(namespace).items()}
    else:
        dic = vars(namespace)
    return func(**dic)


def run(funcdict, prog=None, description=None, version=None, argv=None):
    """
    :param funcdict: a function or a nested dictionary of functions
    :param prog: the name of the associated command line application
    :param description: description of the application
    :param version: version of the application printed with --version
    :param argv: a list of command-line arguments (if None, use sys.argv[1:])
    """
    _run(parser(funcdict, prog, description, version), argv)
