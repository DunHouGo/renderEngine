#!c4dpy
# -*- coding: utf-8 -*-

"""Provides classes that expose commonly used constants as immutable objects.
"""
import c4d
from typing import Union, Optional
import Renderer
from Renderer.utils.node_helper import NodeGraghHelper, EasyTransaction
from Renderer.utils.texture_helper import TextureHelper

ID_PREFERENCES_NODE = 465001632 # prefs ID

def GetPreferenceDescID(pname: str) -> None:
    prefs = c4d.plugins.FindPlugin(ID_PREFERENCES_NODE)
    if not isinstance(prefs, c4d.BaseList2D):
        raise RuntimeError("Could not access preferences node.")

    for bc, descid, _ in prefs.GetDescription(0):
        name = bc[c4d.DESC_NAME]
        if pname in name:
            print(name)
            print(descid)