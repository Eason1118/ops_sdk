#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 12:22
# @Author  : harilou
# @Describe: 脚本入参校验
import os
import json


class ParseError(Exception):
    """自定义解析异常"""
    def __init__(self, message):
        self.message = message


class Argument:
    """参数定义"""
    def __init__(self, name, default=None, handler=None, required=True, type=str, filter=None, help=None):
        self.name = name
        self.default = default
        self.type = type
        self.required = required
        self.filter = filter
        self.help = help
        self.handler = handler

        if not isinstance(name, str):
            raise TypeError('Argument name must be a string')
        if filter and not callable(filter):
            raise TypeError('Argument filter must be callable')

    def parse(self, has_key, value):
        if not has_key:
            if self.required and self.default is None:
                raise ParseError(f"Required Error: '{self.name}' is required.\nHelp: {self.help}")
            return self.default

        if value in [None, '', 'null']:
            if self.required:
                raise ParseError(f"Value Error: '{self.name}' cannot be null.\nHelp: {self.help}")
            return self.default

        try:
            if self.type:
                if self.type in (list, dict) and isinstance(value, str):
                    value = json.loads(value)
                    assert isinstance(value, self.type)
                elif self.type == bool and isinstance(value, str):
                    value = value.lower() == 'true'
                elif not isinstance(value, self.type):
                    value = self.type(value)
        except (ValueError, TypeError, AssertionError):
            raise ParseError(f"Type Error: '{self.name}' must be of type {self.type}.\nHelp: {self.help}")

        if self.filter and not self.filter(value):
            raise ParseError(f"Value Error: '{self.name}' failed validation.\nHelp: {self.help}")

        if self.handler:
            value = self.handler(value)

        return value


class EnvParser:
    """通过环境变量解析参数"""
    def __init__(self, *args):
        self.arguments = {arg.name: arg for arg in args}

    def parse(self):
        result = {}
        for name, argument in self.arguments.items():
            value = os.environ.get(name)
            has_key = name in os.environ
            try:
                result[name] = argument.parse(has_key, value)
            except ParseError as e:
                print(f"参数校验失败: {e.message}")
                exit(1)
        return result


# 参数解析器
class ScriptParser:
    def __init__(self, *args):
        self.arguments = {arg.name: arg for arg in args}

    def parse(self, argv):
        result = {}
        provided_args = {arg.split('=')[0].lstrip('-'): arg.split('=')[1] for arg in argv if '=' in arg}

        for name, argument in self.arguments.items():
            has_key = name in provided_args
            value = provided_args.get(name, None)
            try:
                result[name] = argument.parse(has_key, value)
            except ParseError as e:
                print(f"参数校验失败: {e.message}")
                exit(1)

        return
