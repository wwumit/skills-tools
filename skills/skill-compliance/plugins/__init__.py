#!/usr/bin/env python3
"""
Plugin Discovery — 合规检查插件发现与加载

自动扫描 plugins/ 目录，加载所有 CompliancePlugin 子类。
"""

import os
import sys

from .base import CompliancePlugin


def discover_plugins() -> list:
    """
    发现并加载所有合规检查插件。

    扫描 plugins/ 目录下的 .py 文件（排除 base.py 和 __init__.py），
    加载其中继承 CompliancePlugin 的类并实例化。

    Returns:
        已实例化的插件列表
    """
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    plugins = []

    for f in sorted(os.listdir(plugin_dir)):
        if not f.endswith(".py"):
            continue
        if f.startswith("_") or f == "base.py":
            continue

        module_name = f[:-3]
        module_path = os.path.join(plugin_dir, f)

        try:
            # 动态加载 .py 文件作为模块
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                module_name, module_path
            )
            mod = importlib.util.module_from_spec(spec)
            # 让模块能 import plugins.base
            mod.__package__ = "plugins"
            sys.modules[module_name] = mod
            spec.loader.exec_module(mod)

            # 查找 CompliancePlugin 子类
            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if (isinstance(attr, type)
                        and issubclass(attr, CompliancePlugin)
                        and attr is not CompliancePlugin):
                    instance = attr()
                    plugins.append(instance)
        except Exception as e:
            print(f"[WARN] 插件加载失败: {module_name} -> {e}")

    return plugins
