#!c4dpy
# -*- coding: utf-8 -*-

"""Provides classes that expose commonly used constants as immutable objects.
"""
from typing import Union, Optional
import c4d
import Renderer
from Renderer.constants.centileo_id import *
from Renderer.CentiLeo.centileo_helper import AOVHelper as AOV, MaterialHelper as Material

ID_PREFERENCES_NODE = 465001632 # Prefs ID
ID_MATERIAL_MANAGER: int = 12159 # Material Manager

def GetPreference() -> c4d.BaseList2D:
    prefs = c4d.plugins.FindPlugin(ID_PREFERENCES_NODE)
    if not isinstance(prefs, c4d.BaseList2D):
        raise RuntimeError("Could not access preferences node.")
    descIdSettings = c4d.DescID(    
    c4d.DescLevel(1057305, 1, 465001632), # pref ID CentiLeo
    c4d.DescLevel(888, 133, 465001632)
    )
    # Set 
    return prefs[descIdSettings]

def IsCentiLeoMaterial(material: c4d.BaseMaterial) -> bool:
    if material is None:
        return False
    return material.GetNodeMaterialReference().HasSpace(CL_NODESPACE)

# 首选项设置为Node材质
def IsNodeBased() -> bool:
    """
    Check if CentiLeo use node material mode.
    """
    return True

# 获取渲染器版本
def GetVersion(document: c4d.documents.BaseDocument = None) -> str :
    """
    Get the version number of CentiLeo.

    Returns:
        str: The version number
    """
    pass

# 获取渲染器核心版本
def GetCoreVersion(document: c4d.documents.BaseDocument = None) -> str :
    """
    Get the core version of CentiLeo.

    Returns:
        str: The version number
    """
    pass

def OpenIPR():
    c4d.CallCommand(1061490) # CentiLeo IPR Window 

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
        
    if Renderer.GetRenderEngine() == ID_CENTILEO:
        if IsNodeBased():
            if not c4d.IsCommandChecked(Renderer.CID_NODE_EDITOR):
                c4d.CallCommand(Renderer.CID_NODE_EDITOR) # Node Editor...
                c4d.CallCommand(465002360) # Material
        else:
            c4d.CallCommand(1033989) # CentiLeo Shader Graph Editor
            # Only scroll to the material if material manager is opened
            
        if c4d.IsCommandChecked(ID_MATERIAL_MANAGER):  
            c4d.CallCommand(16297) # Scroll To Selection

# 打开材质编辑器
def AovManager(document: c4d.documents.BaseDocument = None, driverType: Union[str,c4d.BaseObject,None] = None) -> None:
    """
    Open aov Manager.
    """
    pass

# 打开贴图管理器
def TextureManager() -> None:
    """
    Open Texture Manager.
    """
    c4d.CallCommand(1029486)

# 打开灯光管理器
def LightManager():
    pass
