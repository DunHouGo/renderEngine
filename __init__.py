# -*- coding: utf-8 -*-
"""This is a custom module for render engines in Maxon Cinema 4D.

It contains sub-modules named as render engines, and each sub-modules has classes in them,
at least two: 

    AOV: uesd for create and modify aovs
    Material: uesd for create and modify materials

and an optional class:

    Scene: uesd for create and modify scenes objects/tags/and etcs.


Note: Material class more focus on #maxon.GraphNode, aka the new node editor material, but not the old legacy
and not on active devlopment expresso material graph.



"""
###  ==========  INFO  ==========  ###

__author__ = "DunHou"
__version__ = "1.1.0"
__website__ = "https://www.boghma.com/"
__license__ = "MIT license"

# Released under the MIT license
# https://opensource.org/licenses/mit-license.php

###  ==========  Import Libs  ==========  ###
"""Provides functions and constants that are commonly used in all modules. Also exposes the sub-modules.
"""

import c4d
C4D_VERSION: int = c4d.GetC4DVersion()

if C4D_VERSION <= 2023200:
    print("NOTE: This module better compatible with Cinema 4D R2024 and above.")
    
import os
import importlib
import sys
import typing
from typing import Generator, Union, Optional
import random


def _reload_loaded_submodules(
    package_name: str,
    skip_modules: Optional[set[str]] = None,
) -> list[str]:
    """Reload loaded submodules of the current package.

    Args:
        package_name (str): The package name that owns the submodules.
        skip_modules (Optional[set[str]]): Module names to skip. Defaults to None.

    Returns:
        list[str]: The reloaded module names in execution order.

    Example:
        .. code-block:: python

            import Renderer
            from importlib import reload

            reload(Renderer)
    """
    if skip_modules is None:
        skip_modules = set()

    prefix: str = f"{package_name}."
    module_names: list[str] = [
        module_name
        for module_name in sys.modules
        if module_name.startswith(prefix) and module_name not in skip_modules
    ]

    # 先重载更深层的模块，避免父模块过早绑定旧对象。
    module_names.sort(key=lambda module_name: module_name.count("."), reverse=True)

    reloaded_module_names: list[str] = []
    for module_name in module_names:
        module = sys.modules.get(module_name)
        if module is None:
            continue
        importlib.reload(module)
        reloaded_module_names.append(module_name)

    return reloaded_module_names


# 在包被 reload(Renderer) 时，先深度重载已加载的 Renderer 子模块。
if globals().get("_RENDERER_PACKAGE_INITIALIZED", False):
    _RELOADED_SUBMODULES: list[str] = _reload_loaded_submodules(
        __name__,
        skip_modules={__name__},
    )
else:
    _RELOADED_SUBMODULES = []

# import Renderer package
from . import constants, utils
from .constants.common_id import *
from .utils import NodeGraghHelper, EasyTransaction
from .utils.texture_helper import TextureHelper, g_texture_helper

from .utils import material_maker as MaterialMaker
from .utils.material_maker import PBRPackage, DescriptionMaterialMaker
from .utils import decorators

# New unified PBR pipeline (preferred for new code)

from .utils import (GetVideoPost,
                    GetRenderEngine,
                    ArrangeAll,
                    ArrangeSelected,
                    ClearConsole,
                    )


# import moudule if plugin installed
if c4d.plugins.FindPlugin(ID_REDSHIFT, type=c4d.PLUGINTYPE_ANY) is not None:
    from . import Redshift
if c4d.plugins.FindPlugin(ID_ARNOLD, type=c4d.PLUGINTYPE_ANY) is not None:
    from . import Arnold
if c4d.plugins.FindPlugin(ID_OCTANE, type=c4d.PLUGINTYPE_ANY) is not None:
    from . import Octane
if c4d.plugins.FindPlugin(ID_VRAY, type=c4d.PLUGINTYPE_ANY) is not None:
    from . import Vray
if c4d.plugins.FindPlugin(ID_CORONA, type=c4d.PLUGINTYPE_ANY) is not None:
    from . import Corona
if c4d.plugins.FindPlugin(ID_CENTILEO, type=c4d.PLUGINTYPE_ANY) is not None:
    from . import CentiLeo

SUPPORT_RENDERER: list[int] = [ID_REDSHIFT, ID_ARNOLD, ID_OCTANE, ID_CORONA, ID_VRAY, ID_CENTILEO]

_RENDERER_PACKAGE_INITIALIZED = True


# todo
