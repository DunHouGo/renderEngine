#!c4dpy
# -*- coding: utf-8 -*-

"""Provides classes that expose commonly used constants as immutable objects.
"""
import Renderer
from Renderer.constants.corona_id import *
from Renderer.Corona.corona_helper import MaterialHelper as Material

# 获取渲染器
def GetRenderEngine(document: c4d.documents.BaseDocument = None) -> int :
    """
    Return current render engine ID.
    """
    if not document:
        document = c4d.documents.GetActiveDocument()
    return document.GetActiveRenderData()[c4d.RDATA_RENDERENGINE]


# 打开IPR
def OpenIPR() -> None:
    """
    Open Live Viewer.
    """
    c4d.CallCommand(1035192) # Corona VFB...
# 打开材质编辑器
def OpenNodeEditor(actmat: c4d.BaseMaterial = None) -> None:
    """
    Open Node Editor for given material.
    """
    if not actmat:
        doc = c4d.documents.GetActiveDocument()
        actmat = doc.GetActiveMaterial()

    elif isinstance(actmat, Material):
        actmat = actmat.material

    else:
        doc = actmat.GetDocument()

    doc.AddUndo(c4d.UNDOTYPE_BITS,actmat)
    actmat.SetBit(c4d.BIT_ACTIVE)
    
    if not actmat:
        raise ValueError("Failed to retrieve a Material.")


    c4d.CallCommand(1040908) # Node material editor...
    # Only scroll to the material if material manager is opened
    if c4d.IsCommandChecked(Renderer.ID_MATERIAL_MANAGER):
        c4d.CallCommand(16297) # Scroll To Selection

# 打开aov管理器
def AovManager() -> None:
    """
    Open aov Manager.
    """
    c4d.CallCommand(1038015) # Multi-Pass...

# 打开贴图管理器
def TextureManager() -> None:
    """
    Open Octane Texture Manager.
    """
    c4d.CallCommand(1029486) # Project Asset Inspector
