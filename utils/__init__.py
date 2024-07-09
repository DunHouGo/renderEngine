#!c4dpy
# -*- coding: utf-8 -*-

"""Provides classes that expose commonly used constants as immutable objects.
"""
import c4d
from typing import Union, Optional
import Renderer
from Renderer.utils.node_helper import NodeGraghHelper, EasyTransaction
from Renderer.utils.texture_helper import TextureHelper