#!c4dpy
# -*- coding: utf-8 -*-

"""Provides classes that expose commonly used constants as immutable objects.
"""
import c4d
import Renderer
from ..constants.vray_id import *
from ..Vray.vray_helper import MaterialHelper as Material


# 首选项设置为Node材质
def IsNodeBased(material: c4d.BaseMaterial) -> bool:
    """
    Check if is node material.
    """
    nodeMaterial: c4d.NodeMaterial = material.GetNodeMaterialReference()
    if nodeMaterial.HasSpace(VR_NODESPACE):
        return True
    return False

def OpenIPR():
    c4d.CallCommand(1054856) # V-Ray VFB

# 打开材质编辑器
def OpenNodeEditor(actmat: c4d.BaseMaterial = None) -> None:
    """
    Open Node Editor for given material.
    """
    if not actmat:
        doc = c4d.documents.GetActiveDocument()
        actmat = doc.GetActiveMaterial()
    else:
        doc = actmat.GetDocument()
    doc.AddUndo(c4d.UNDOTYPE_BITS,actmat)
    actmat.SetBit(c4d.BIT_ACTIVE)
    if not actmat:
        raise ValueError("Failed to retrieve a Material.")
        
    if Renderer.GetRenderEngine() == ID_VRAY:
        if IsNodeBased(actmat):
            if not c4d.IsCommandChecked(Renderer.CID_NODE_EDITOR):
                c4d.CallCommand(Renderer.CID_NODE_EDITOR) # Node Editor...
                c4d.CallCommand(465002360) # Material
            
        if c4d.IsCommandChecked(Renderer.ID_MATERIAL_MANAGER):  
            c4d.CallCommand(16297) # Scroll To Selection

# 打开aov管理器
def AovManager() -> None:
    """
    Open aov Manager.
    """
    c4d.CallCommand(1054051) # Render Elements
