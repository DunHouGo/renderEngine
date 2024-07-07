#!c4dpy
# -*- coding: utf-8 -*-

"""Provides classes that expose commonly used constants as immutable objects.
"""
import Renderer
from ..constants.redshift_id import *
from ..Redshift.redshift_helper import AOVHelper as AOV, MaterialHelper as Material, SceneHelper as Scene
REDSHIFT_SHADER_NETWORK = 1036224

def GetPreference() -> c4d.BaseList2D:
    """
    Get the Redshift preferenc.
    """
    prefs = c4d.plugins.FindPlugin(ID_PREFERENCES_NODE)
    
    if not isinstance(prefs, c4d.BaseList2D):
        raise RuntimeError("Could not access preferences node.")
      
    descIdSettings = c4d.DescID(
    c4d.DescLevel(1036220, 1, 465001632), # pref ID Redshift
    c4d.DescLevel(888, 133, 465001632)
    )
    # Redshift
    return prefs[descIdSettings]

def IsRedshiftMaterial(material: c4d.BaseMaterial) -> bool:
    if material is None:
        return False
    return material.CheckType(REDSHIFT_SHADER_NETWORK) or material.GetNodeMaterialReference().HasSpace(Renderer.RS_NODESPACE)


# 首选项设置为Node材质
def IsNodeBased():
    """
    Check if in Redshift and use node material mode.
    """
    return GetPreference()[c4d.PREFS_REDSHIFT_USE_NODE_MATERIALS]

def SetMaterialPreview(preview_mode: int = 1):
    """
    Set material preview mode, default to 'when render is idle'.

    """    
    prefs = c4d.plugins.FindPlugin(ID_PREFERENCES_NODE)
    
    if not isinstance(prefs, c4d.BaseList2D):
        raise RuntimeError("Could not access preferences node.")

      
    descIdSettings = c4d.DescID(
    c4d.DescLevel(1036220, 1, 465001632), # pref ID Redshift
    c4d.DescLevel(888, 133, 465001632)
    )
    # Set
    prefsset = prefs[descIdSettings]

    prefsset[c4d.PREFS_REDSHIFT_MATPREVIEW_MODE] = preview_mode

# 获取渲染器版本
def GetVersion() -> str :
    """
    Get the version number of Redshift.

    Returns:
        str: The version number
    """
    try:
        import redshift
        return redshift.GetCoreVersion()
    except:
        return str(0)

def OpenIPR():
    try:
        c4d.CallCommand(1038666) # RS RenderView
    except:
        c4d.CallCommand(1038666, 1038666) # Redshift RenderView

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
        
    if Renderer.GetRenderEngine() == ID_REDSHIFT_VIDEO_POST:
        if IsNodeBased():
            if not c4d.IsCommandChecked(Renderer.CID_NODE_EDITOR):
                c4d.CallCommand(Renderer.CID_NODE_EDITOR) # Node Editor...
                c4d.CallCommand(465002360) # Material

        else:
            c4d.CallCommand(1036229) # Redshift Shader Graph Editor
            # Only scroll to the material if material manager is opened
            
        if c4d.IsCommandChecked(Renderer.ID_MATERIAL_MANAGER):  
            c4d.CallCommand(16297) # Scroll To Selection

# 打开aov管理器
def AovManager() -> None:
    """
    Open aov Manager.
    """
    c4d.CallCommand(1038693) # Redshift AOV Manager

# 打开贴图管理器
def TextureManager() -> None:
    """
    Open Redshift Texture Manager.
    """
    c4d.CallCommand(1038683) # Redshift Asset Manager
