# coding=utf-8

"""Provides classes that expose commonly used constants as immutable objects.
"""
from ast import Set
from typing import Union, Optional
import c4d
import maxon
from .. import constants
from ..constants.arnold_id import *
from .scene import SceneHelper as Scene
from .material import MaterialHelper as Material
from .aov import AOVHelper as AOV


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

def IsArnoldMaterial(material: c4d.BaseMaterial) -> bool:
    if material is None:
        return False
    return material.CheckType(ARNOLD_SHADER_NETWORK) or material.GetNodeMaterialReference().HasSpace(AR_NODESPACE)

# 首选项设置为Node材质
def IsNodeBased() -> bool:
    """
    Check if Arnold use node material mode.
    """
    try:
        return not GetPreference()[c4d.PARNOLD_MATERIAL_SYSTEM]
    except:
        return True

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
    
    if IsNodeBased():
        if not c4d.IsCommandChecked(constants.CID_NODE_EDITOR):
            c4d.CallCommand(constants.CID_NODE_EDITOR) # Node Editor...
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
    from .. import GetVideoPost, get_nodes
    
    if not document:
        document = c4d.documents.GetActiveDocument()
    if isinstance(driverType,c4d.BaseObject):
        the_driver = driverType
    if isinstance(driverType, str):
        aov_helper = AOV(GetVideoPost(document, constants.ID_ARNOLD))
        the_driver = aov_helper.get_driver(driverType)

    if driverType is None:
        aov_helper = AOV(GetVideoPost(document, constants.ID_ARNOLD))
        drivers = get_nodes(document,[ARNOLD_DRIVER])
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


#=============================================
# Copyright @Arnold Node Material
#=============================================

# Link
class ArnoldShaderLinkCustomData:
    """
    A class used to represent data stored in the Arnold Shader Link custom gui.
    """

    TYPE_CONSTANT = 1
    TYPE_TEXTURE = 2
    TYPE_MATERIAL = 3
 
    def __init__(self, guiType = TYPE_CONSTANT, value = c4d.Vector(), texture = None, material = None):
        self.type = guiType
        self.value = value
        self.texture = texture
        self.texture_color_space = "sRGB"
        self.material = material

    def __repr__(self):
        if self.type == ArnoldShaderLinkCustomData.TYPE_CONSTANT:
            if self.value is not None:
                return "%f %f %f (constant)" % (self.value.x, self.value.y, self.value.z)
            else:
                return "0 0 0 (constant)"
        elif self.type == ArnoldShaderLinkCustomData.TYPE_TEXTURE:
            return "%s [%s] (texture)" % (self.texture, self.texture_color_space)
        elif self.type == ArnoldShaderLinkCustomData.TYPE_MATERIAL:
            return "%s (material)" % (self.material.GetName() if self.material is not None else "<none>")
        return ""

def GetShaderLink(node, paramId):
    """
    Returns the value defined in the given node parameter.

    Parameters
    ----------
    node : c4d.BaseList2D
        Scene node (e.g. Arnold Light object).
    paramId : Int32
        Id of the parameter.
    """
    if node is None:
        return None

    # get the container which stores the shader link attributes
    shaderLinkMainContainer = node[C4DAI_SHADERLINK_CONTAINER]
    if shaderLinkMainContainer is None:
        return None
    shaderLinkContainer = shaderLinkMainContainer.GetContainer(paramId)
    if shaderLinkContainer is None:
        return None

    # read the shader link attributes
    shaderLinkData = ArnoldShaderLinkCustomData()
    shaderLinkData.type = shaderLinkContainer.GetInt32(C4DAI_SHADERLINK_TYPE,  ArnoldShaderLinkCustomData.TYPE_CONSTANT)
    shaderLinkData.value = node[paramId]
    shader = shaderLinkContainer.GetLink(C4DAI_SHADERLINK_TEXTURE)
    if shader is not None and shader.GetType() == c4d.Xbitmap:
        shaderLinkData.texture = shader[c4d.BITMAPSHADER_FILENAME]
        shaderLinkData.texture_color_space = shader[C4DAI_GVC4DSHADER_BITMAP_COLOR_SPACE]
    else:
        shaderLinkData.texture = None
        shaderLinkData.texture_color_space = ""
    shaderLinkData.material = shaderLinkContainer.GetLink(C4DAI_SHADERLINK_MATERIAL)

    return shaderLinkData
 
def SetShaderLink(node, paramId, value):
    """
    Sets the value of the given node parameter.

    Parameters
    ----------
    node : c4d.BaseList2D
        Scene node (e.g. Arnold Light object).
    paramId : int
        Id of the parameter.
    value : ArnoldShaderLinkCustomData, c4d.Vector, maxon.Color, str, c4d.BaseMaterial
        Value of the parameter to set.
    """
    if node is None:
        return None

    # check the data type of the value
    # accept ArnoldShaderLinkCustomData, Vector, Color, str and BaseMaterial
    if isinstance(value, ArnoldShaderLinkCustomData):
        shaderLinkData = value
    elif isinstance(value, c4d.Vector) or isinstance(value, maxon.Vector):
        shaderLinkData = ArnoldShaderLinkCustomData(ArnoldShaderLinkCustomData.TYPE_CONSTANT, value)
    elif isinstance(value, maxon.Color):
        shaderLinkData = ArnoldShaderLinkCustomData(ArnoldShaderLinkCustomData.TYPE_CONSTANT, c4d.Vector(value.r, value.g, value.b))
    elif isinstance(value, str):
        shaderLinkData = ArnoldShaderLinkCustomData(ArnoldShaderLinkCustomData.TYPE_TEXTURE, texture=value)
    elif isinstance(value, c4d.BaseMaterial):
        shaderLinkData = ArnoldShaderLinkCustomData(ArnoldShaderLinkCustomData.TYPE_MATERIAL, material=value)
    elif value is None:
        shaderLinkData = ArnoldShaderLinkCustomData()
    else:
        print("[WARNING] %s.%s: invalid shader link value, only ArnoldShaderLinkCustomData, Vector, Color, Filename, str or BaseMaterial is accepted" % (node.GetId(), paramId))
        return None

    # create a container to store the shader link attributes
    shaderLinkMainContainer = node[C4DAI_SHADERLINK_CONTAINER]
    if shaderLinkMainContainer is None:
        shaderLinkMainContainer = c4d.BaseContainer()

    shaderLinkContainer = shaderLinkMainContainer.GetContainer(paramId)
    if shaderLinkContainer is None:
        shaderLinkContainer = c4d.BaseContainer()

    # set the type
    shaderLinkContainer[C4DAI_SHADERLINK_TYPE] = shaderLinkData.type

    # set the color value
    if shaderLinkData.type == ArnoldShaderLinkCustomData.TYPE_CONSTANT:
        node[paramId] = shaderLinkData.value
        shaderLinkContainer[C4DAI_SHADERLINK_VALUE] = shaderLinkData.value
    # set the texture (Bitmap shader)
    elif shaderLinkData.type == ArnoldShaderLinkCustomData.TYPE_TEXTURE:
        shader = shaderLinkContainer.GetLink(C4DAI_SHADERLINK_TEXTURE)
        if shader is not None:
            shader.Remove()
        shader = c4d.BaseShader(c4d.Xbitmap)
        shader[c4d.BITMAPSHADER_FILENAME] = shaderLinkData.texture
        shader[C4DAI_GVC4DSHADER_BITMAP_COLOR_SPACE] = shaderLinkData.texture_color_space
        node.InsertShader(shader)
        shaderLinkContainer[C4DAI_SHADERLINK_TEXTURE] = shader
    # set the material link
    elif shaderLinkData.type == ArnoldShaderLinkCustomData.TYPE_MATERIAL:
        shaderLinkContainer[C4DAI_SHADERLINK_MATERIAL] = shaderLinkData.material

    # set the shader link to the node
    shaderLinkMainContainer.SetContainer(paramId, shaderLinkContainer)
    node[C4DAI_SHADERLINK_CONTAINER] = shaderLinkMainContainer


# Color
class ArnoldVColorCustomData:
    """
    A class used to represent data stored in the Arnold Vector/Color custom gui.
    """

    TYPE_COLOR = 1
    TYPE_VECTOR = 2
 
    def __init__(self, value = c4d.Vector(), guiType = TYPE_COLOR):
        self.value = value
        self.type = guiType

    def __repr__(self):
        return "%f %f %f (%s)" % (self.value.x, self.value.y, self.value.z, 
            "color" if self.type == ArnoldVColorCustomData.TYPE_COLOR else "vector")

def GetVColor(node, paramId):
    """
    Returns the value defined in the given node parameter.

    Parameters
    ----------
    node : c4d.BaseList2D or maxon.frameworks.graph.GraphNode
        Scene node (e.g. object).
    paramId : Int32
        Id of the parameter.
    """
    if node is None:
        return None

    vcolorData = ArnoldVColorCustomData()

    if isinstance(node, maxon.GraphNode):
        material = c4d.NodeMaterial.GetMaterial(maxon.Cast(maxon.NodesGraphModelRef, node.GetGraph()))
        if material is None:
            return None

        # send a custom message to the Arnold Scene hook class to get the data
        msg = c4d.BaseContainer()
        msg.SetInt32(C4DTOA_MSG_TYPE, C4DTOA_MSG_GET_NODEMATERIAL_CUSTOMDATA)
        msg.SetLink(C4DTOA_MSG_PARAM1, material)
        msg.SetString(C4DTOA_MSG_PARAM2, node.GetPath())
        msg.SetString(C4DTOA_MSG_PARAM3, paramId)

        doc = c4d.documents.GetActiveDocument()
        arnoldSceneHook = doc.FindSceneHook(ARNOLD_SCENE_HOOK)
        if arnoldSceneHook is None:
            return None
        arnoldSceneHook.Message(c4d.MSG_BASECONTAINER, msg)

        vcolorData.value = msg.GetVector(C4DTOA_MSG_RESP1)
        vcolorData.type = msg.GetInt32(C4DTOA_MSG_RESP2)

    else:
        valueId = c4d.DescID(c4d.DescLevel(paramId), c4d.DescLevel(1))
        vcolorData.value = node.GetParameter(valueId, c4d.DESCFLAGS_GET_0)
        guiTypeId = c4d.DescID(c4d.DescLevel(paramId), c4d.DescLevel(2))
        vcolorData.type = node.GetParameter(guiTypeId, c4d.DESCFLAGS_GET_0)

    return vcolorData
 
def SetVColor(node, paramId, value):
    """
    Sets the value of the given node parameter.

    Parameters
    ----------
    node : c4d.BaseList2D or maxon.frameworks.graph.GraphNode
        Scene node (e.g. object).
    paramId : int
        Id of the parameter.
    value : ArnoldVColorCustomData, c4d.Vector, maxon.Color
        Value of the parameter to set.
    """
    if node is None:
        return None

    # check the data type of the value
    # accept ArnoldVColorCustomData, Vector and Color
    if isinstance(value, ArnoldVColorCustomData):
        vcolorData = value
    elif isinstance(value, c4d.Vector) or isinstance(value, maxon.Vector):
        vcolorData = ArnoldVColorCustomData(value, ArnoldVColorCustomData.TYPE_VECTOR)
    elif isinstance(value, maxon.Color):
        vcolorData = ArnoldVColorCustomData(c4d.Vector(value.r, value.g, value.b), ArnoldVColorCustomData.TYPE_COLOR)
    elif value is None:
        vcolorData = ArnoldVColorCustomData()
    else:
        print("[WARNING] %s.%s: invalid vcolor value, only ArnoldVColorCustomData, Vector or Color is accepted" % (node.GetId(), paramId))
        return None

    if  isinstance(node, maxon.GraphNode):
        material = c4d.NodeMaterial.GetMaterial(maxon.Cast(maxon.NodesGraphModelRef, node.GetGraph()))
        if material is None:
            return None

        # send a custom message to the Arnold Scene hook class to set the data
        msg = c4d.BaseContainer()
        msg.SetInt32(C4DTOA_MSG_TYPE, C4DTOA_MSG_SET_NODEMATERIAL_CUSTOMDATA)
        msg.SetLink(C4DTOA_MSG_PARAM1, material)
        msg.SetString(C4DTOA_MSG_PARAM2, node.GetPath())
        msg.SetString(C4DTOA_MSG_PARAM3, paramId)
        msg.SetVector(C4DTOA_MSG_PARAM4, vcolorData.value)
        msg.SetInt32(C4DTOA_MSG_PARAM5, vcolorData.type)

        doc = c4d.documents.GetActiveDocument()
        arnoldSceneHook = doc.FindSceneHook(ARNOLD_SCENE_HOOK)
        if arnoldSceneHook is None:
            return None
        arnoldSceneHook.Message(c4d.MSG_BASECONTAINER, msg)

    else:     
        valueId = c4d.DescID(c4d.DescLevel(paramId), c4d.DescLevel(1))
        node.SetParameter(valueId, vcolorData.value, c4d.DESCFLAGS_SET_0)
        guiTypeId = c4d.DescID(c4d.DescLevel(paramId), c4d.DescLevel(2))
        node.SetParameter(guiTypeId, vcolorData.type, c4d.DESCFLAGS_SET_0)


__all__ = [
    Scene,
    Material,
    AOV,
    GetPreference,
    IsArnoldMaterial,
    IsNodeBased,
    GetVersion,
    GetCoreVersion,
    OpenIPR,
    OpenNodeEditor,
    AovManager,
    TextureManager,
    LightManager,
    ArnoldShaderLinkCustomData,
    GetShaderLink,
    SetShaderLink,
    ArnoldVColorCustomData,
    GetVColor,
    SetVColor
]
