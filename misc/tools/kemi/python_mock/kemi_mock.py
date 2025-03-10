#!/usr/bin/python3

#parses the output of /usr/sbin/kamctl rpc app_python.api_list
#
#usage ./kemi_mock.py api.json > KSR.py
#or for python 3.2
#./kemi_mock.py api.json --no-union > KSR.py

import json
import sys

from collections import defaultdict

#python 3.2 doesnt support types.Union
noUnion = False

reserved_keywords = {"async"}


def printMocReturn(module_name, func, indent):
    param_names = []
    param_list = []
    param_signature = ""
    if func['params'] is not None and func['params'] != 'none':
        param_list = func['params'].split(", ")
    i = 0

    for _ in param_list:
        param_names.append("param"+str(i))
        i = i + 1

    param_signature = ", ".join(param_names)

    prefix = ""
    for i in range(indent):
        prefix = prefix+"\t"

    print(prefix + "if \""+func['name']+"\" not in _mock_data['"+module_name+"']:")
    printDefaultReturn(func, indent+1)

    print(prefix + "node = _mock_data['"+module_name+"']['"+func['name']+"']")

    print(prefix + "if isinstance(node, types.FunctionType):")
    print(prefix + "\treturn node("+param_signature+")")

    for param in param_names:
        print(prefix + "if not isinstance(node, dict):")
        print(prefix + "\treturn node")
        print(prefix + "if str(" + param + ") in node:")
        print(prefix + "\tnode = node[str("+param+")]")
        print(prefix + "else:")
        printDefaultReturn(func, indent+1)

    print(prefix + "return node")


def printDefaultReturn(func, indent):
    prefix = ""
    for i in range(indent):
        prefix = prefix+"\t"

    if func['ret'] == "bool":
        print(prefix + "return True")
    elif func['ret'] == "int":
        print(prefix + "return 1")
    elif func['ret'] == "str":
        print(prefix + "return \"\"")
    elif func['ret'] == "xval":
        print(prefix + "return None")
    else:
        print(prefix + "return")


def printFunction(module_name, func, indent):
    params = ""
    log_params = ""
    if module_name == "":
        log_params = "\"" + func['name'] + "\""
    else:
        log_params = "\"" + module_name + "." + func['name'] + "\""

    log_format_params = "%s"

    param_list = []
    if func['params'] is not None and func['params'] != "none":
        param_list = func['params'].split(", ")
        i = 0
        for _ in param_list:
            if params != "":
                 params = params + ", "
            params = params + "param" + str(i) + ": " + param_list[i]
            log_params = log_params + ", param" + str(i)
            log_format_params = log_format_params + ", %s"
            i = i+1
    if len(param_list) > 0:
        log_params = "(" + log_params + ")"
    prefix = ""
    for i in range(indent):
        prefix = prefix+"\t"
    if indent > 0:
        print(prefix + "@staticmethod")
    if func['ret'] == "bool":
        print(prefix + "def " + func['name'] +"("+params+") -> bool:")
    elif func['ret'] == "int":
        print(prefix + "def " + func['name'] +"("+params+") -> int:")
    elif func['ret'] == "str":
        print(prefix + "def " + func['name'] + "(" + params + ") -> int:")
    elif func['ret'] == "xval":
        if noUnion:
            print(prefix + "def " + func['name'] + "(" + params + "):")
        else:
            print(prefix + "def " + func['name'] +"("+params+") -> Union[int, str, None]:")
    else:
        print(prefix + "def " + func['name'] +"("+params+"):")

    generate_function_doc(module_name, func, prefix)

    print(prefix + "\tprint(\"Calling " + log_format_params + "\" % "+log_params+")")
    printMocReturn(module_name, func, indent+1)
    print("")


def generate_function_doc(module_name, func, prefix):
    if documentation is not None and module_name in documentation:
        function_parts = func['name'].split("_")
        for i in range(len(function_parts), 0, -1):
            function_prefix = "_".join(function_parts[:i])
            if function_prefix in documentation[module_name]["functions"]:
                print(prefix + "\t\"\"\"")
                documentation_lines = documentation[module_name]["functions"][function_prefix].split("\n")
                for line in documentation_lines:
                    print(prefix + "\t" + line)
                print(prefix + "\t\"\"\"")
                break


classes = defaultdict(list)

if len(sys.argv) < 2:
    print("Please specify the json file to parse")
    sys.exit(-1)

documentation = None
if len(sys.argv) > 2:
    for i in range(2,len(sys.argv)):
        if sys.argv[i] == "--no-union":
            noUnion = True
        else:
            with open(sys.argv[i]) as f:
                documentation = json.load(f)

if not noUnion:
    print("from typing import Union")

print("import sys")
print("import types")
print("_mock_data = {}")
print("")

with open(sys.argv[1]) as f:
    data = json.load(f)

for method in data['result']['methods']:
    classes[method['func']['module']].append(method['func'])

if "pv" not in classes:
    classes['pv'].append({'params': 'str',
                          'ret': 'xval',
                          'name': 'get'}
                         )
    classes['pv'].append({'params': 'str',
                          'ret': 'xval',
                          'name': 'gete'}
                         )
    classes['pv'].append({'params': 'str, int',
                          'ret': 'xval',
                          'name': 'getvn'}
                         )
    classes['pv'].append({'params': 'str, str',
                          'ret': 'xval',
                          'name': 'getvs'}
                         )
    classes['pv'].append({'params': 'str',
                          'ret': 'xval',
                          'name': 'getw'}
                         )
    classes['pv'].append({'params': 'str, int',
                          'ret': 'none',
                          'name': 'seti'}
                         )
    classes['pv'].append({'params': 'str, str',
                          'ret': 'none',
                          'name': 'sets'}
                         )
    classes['pv'].append({'params': 'str',
                          'ret': 'none',
                          'name': 'unset'}
                         )
    classes['pv'].append({'params': 'str',
                          'ret': 'none',
                          'name': 'is_null'}
                         )

for module_name, module in classes.items():
    if module_name != "":
        print("")
        print("class " + module_name.capitalize() + ":")

        for func in module:
            printFunction(module_name, func, 1)

for func in classes['']:
    print("")
    printFunction('', func, 0)


def document_module(module_name):
    if documentation is not None and module_name in documentation:
        print("\"\"\"")
        documentation_lines = documentation[module_name]["overview"].split("\n")
        for line in documentation_lines:
            print("" + line)
        print("\"\"\"")


for module_name in classes.keys():
    if module_name != "":
        if module_name in reserved_keywords:
            print("setattr(sys.modules[__name__], '" + module_name + "', " + module_name.capitalize() + "())")
        else:
            print(module_name + " = "+module_name.capitalize()+"()")
        document_module(module_name)

print("")

for module_name in classes.keys():
    print("_mock_data['" + module_name + "'] = {}")

