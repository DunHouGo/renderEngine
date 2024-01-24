#!c4dpy
# -*- coding: utf-8 -*-

"""Provides classes that expose commonly used constants as immutable objects.
"""
from typing import Union, Optional
import c4d
import Renderer
from Renderer.constants.arnold_id import *
from Renderer.Arnold.arnold_helper import AOVHelper as AOV, MaterialHelper as Material, SceneHelper as Scene

def GetPreference() -> c4d.BaseList2D:
    prefs = c4d.plugins.FindPlugin(ID_PREFERENCES_NODE)
    if not isinstance(prefs, c4d.BaseList2D):
        raise RuntimeError("Could not access preferences node.")
    descIdSettings = c4d.DescID(    
    c4d.DescLevel(1036062, 1, 465001632), # pref ID Arnold
    c4d.DescLevel(888, 133, 465001632)
    )
    # Set 
    return prefs[descIdSettings]

# 首选项设置为Node材质
def IsNodeBased() -> bool:
    """
    Check if Arnold use node material mode.
    """
    return not GetPreference()[c4d.PARNOLD_MATERIAL_SYSTEM]

# 获取渲染器版本
def GetVersion(document: c4d.documents.BaseDocument = None) -> str :
    """
    Get the version number of Arnold.

    Returns:
        str: The version number
    """
    if not document:
        document = c4d.documents.GetActiveDocument()
    arnoldSceneHook = document.FindSceneHook(ARNOLD_SCENE_HOOK)
    if arnoldSceneHook is None:
        return ""

    msg = c4d.BaseContainer()
    msg.SetInt32(C4DTOA_MSG_TYPE, C4DTOA_MSG_GET_VERSION)
    arnoldSceneHook.Message(c4d.MSG_BASECONTAINER, msg)

    return msg.GetString(C4DTOA_MSG_RESP1)

# 获取渲染器核心版本
def GetCoreVersion(document: c4d.documents.BaseDocument = None) -> str :
    """
    Get the core version of Arnold.

    Returns:
        str: The version number
    """
    if not document:
        document = c4d.documents.GetActiveDocument()
    arnoldSceneHook = document.FindSceneHook(ARNOLD_SCENE_HOOK)
    if arnoldSceneHook is None:
        return ""

    msg = c4d.BaseContainer()
    msg.SetInt32(C4DTOA_MSG_TYPE, C4DTOA_MSG_GET_VERSION)
    arnoldSceneHook.Message(c4d.MSG_BASECONTAINER, msg)

    return msg.GetString(C4DTOA_MSG_RESP2)

def OpenIPR():
    c4d.CallCommand(1032195) # Arnold IPR Window 

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
        
    if Renderer.GetRenderEngine() == ARNOLD_RENDERER:
        if IsNodeBased():
            if not c4d.IsCommandChecked(Renderer.CID_NODE_EDITOR):
                c4d.CallCommand(Renderer.CID_NODE_EDITOR) # Node Editor...
                c4d.CallCommand(465002360) # Material
        else:
            c4d.CallCommand(1033989) # Arnold Shader Graph Editor
            # Only scroll to the material if material manager is opened
            
        if c4d.IsCommandChecked(ID_MATERIAL_MANAGER):  
            c4d.CallCommand(16297) # Scroll To Selection

# 打开材质编辑器
def AovManager(document: c4d.documents.BaseDocument = None, driverType: Union[str,c4d.BaseObject,None] = None) -> None:
    """
    Open aov Manager.
    """
    if not document:
        document = c4d.documents.GetActiveDocument()
    if isinstance(driverType,c4d.BaseObject):
        the_driver = driverType
    if isinstance(driverType, str):
        aov_helper = AOV(Renderer.GetVideoPost(document, Renderer.ID_ARNOLD))
        the_driver = aov_helper.get_driver(driverType)

    if driverType is None:
        aov_helper = AOV(Renderer.GetVideoPost(document, Renderer.ID_ARNOLD))
        drivers = Renderer.get_nodes(document,[ARNOLD_DRIVER])
        if not drivers:
            the_driver: c4d.BaseObject = aov_helper.create_aov_driver(isDisplay=True)
        # 只有一个driver
        if len(drivers) == 1:
            the_driver = drivers[0]
        # 有多个driver
        elif len(drivers) > 1:
            the_driver = aov_helper.get_dispaly_driver()
    c4d.CallButton(the_driver, C4DAI_DRIVER_SETUP_AOVS)

# 打开贴图管理器
def TextureManager() -> None:
    """
    Open Texture Manager.
    """
    c4d.CallCommand(1034460) # Asset/Tx Manager

# 打开灯光管理器
def LightManager():
    c4d.CallCommand(1039255) # light
