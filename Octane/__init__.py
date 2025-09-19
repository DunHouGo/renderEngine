#!c4dpy
# -*- coding: utf-8 -*-

"""Provides classes that expose commonly used constants as immutable objects.
"""
import Renderer
from Renderer.constants.octane_id import *
from Renderer.Octane.octane_helper import AOVHelper as AOV, MaterialHelper as Material, SceneHelper as Scene

# 获取渲染器
def GetRenderEngine(document: c4d.documents.BaseDocument = None) -> int :
    """
    Return current render engine ID.
    """
    if not document:
        document = c4d.documents.GetActiveDocument()
    return document.GetActiveRenderData()[c4d.RDATA_RENDERENGINE]

def IsOctaneMaterial(material: c4d.BaseMaterial) -> bool:
    if isinstance(material, c4d.BaseMaterial):
        if material.GetType() in Renderer.constants.OCTANE_MATERIALS:
            return True
    return False

# 获取渲染器版本
def GetVersion() -> str :
    """
    Get the version number of Octane.

    Returns:
        str: The version number
    """
    doc = c4d.documents.GetActiveDocument()
    OctaneDialogOpened = False
    
    def GetOctaneDialogOpened():
        return OctaneDialogOpened
    
    def SetOctaneDialogOpened( value = True ):
        OctaneDialogOpened = value
    
    if GetRenderEngine() == ID_OCTANE_VIDEO_POST:
        try:
            bc = doc[ID_OCTANE_LIVEPLUGIN]
            renderer_version = bc[c4d.SET_OCTANE_VERSION]
            SetOctaneDialogOpened()
            return renderer_version
        except Exception as e:
            try:
                if GetOctaneDialogOpened() == False:
                    SetOctaneDialogOpened()
                    c4d.CallCommand(1031193) # Octane Dialog
                bc = doc[ID_OCTANE_LIVEPLUGIN]
                renderer_version = bc[c4d.SET_OCTANE_VERSION]
            except:
                renderer_version = 0
    else: renderer_version = 0
    return renderer_version

# 打开IPR
def OpenIPR() -> None:
    """
    Open Live Viewer.
    """
    c4d.CallCommand(ID_OCTANE_LIVEPLUGIN)  # Octane Live Viewer Window

# 打开材质编辑器
def OpenNodeEditor(actmat = None) -> None:
    """
    Open Node Editor for given material.
    """
    if not actmat:
        doc = c4d.documents.GetActiveDocument()
        actmat = doc.GetActiveMaterial()
    else:
        cid = 0
        # if isinstance(actmat, Material):
        #     actmat = actmat.material
        if isinstance(actmat, c4d.BaseMaterial):
            if not actmat:
                raise ValueError("Failed to retrieve a octane item.")

        elif isinstance(actmat, c4d.BaseTag):
            
            if actmat.GetType() == 1029603:
                cid = 1527
            elif actmat.GetType() == 1029643:
                cid = 1329
            elif actmat.GetType() == 1029754:
                cid = 1325
            elif actmat.GetType() == 1029526:
                cid = 1207
            elif actmat.GetType() == 1029524:
                cid = 1742
            if cid:
                c4d.CallButton(actmat, cid)
                return
        elif isinstance(actmat, c4d.BaseObject):
            if actmat.GetType() == 1035961:
                cid = 12013
            elif actmat.GetType() == 1065204:
                cid = 10281                
            elif actmat.GetType() == 1035792:
                cid = 23               
            elif actmat.GetType() == 1050417:
                cid = 4130
            elif actmat.GetType() == 1065727:
                cid = 10281
            if cid:
                c4d.CallButton(actmat, cid)
                return   

        doc = actmat.GetDocument()
        doc.AddUndo(c4d.UNDOTYPE_BITS,actmat)
        actmat.SetBit(c4d.BIT_ACTIVE)
        c4d.CallCommand(1033872) # Octane Node Editor
        # Only scroll to the material if material manager is opened
        if c4d.IsCommandChecked(12159):
            c4d.CallCommand(16297) # Scroll To Selection
    c4d.EventAdd()

# 打开aov管理器
def AovManager() -> None:
    """
    Open aov Manager.
    """
    c4d.CallCommand(1058335) # aov Manager...

# 打开贴图管理器
def TextureManager() -> None:
    """
    Open Octane Texture Manager.
    """
    c4d.CallCommand(1035275) # Octane Texture Manager
