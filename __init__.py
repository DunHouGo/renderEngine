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
import typing
from typing import Generator, Union, Optional
import random

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


# todo