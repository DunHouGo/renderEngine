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
from .utils.node_helper import NodeGraghHelper, EasyTransaction
from .utils.texture_helper import TextureHelper
from .utils import material_maker as MaterialMaker
from .utils.description_material import DescriptionMaterialMaker
from .utils.description_material import PackageData
from .utils.material_maker import PBRPackage
from .utils import decorators

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

SUPPORT_RENDERER: list[int] = [ID_REDSHIFT, ID_ARNOLD, ID_OCTANE, ID_CORONA, ID_VRAY]
IMAGE_EXTENSIONS: tuple[str] = ('.png', '.jpg', '.jpeg', '.tga', '.bmp', ".exr", ".hdr", ".tif", ".tiff","iff", ".psd", ".tx",  ".b3d", ".dds", ".dpx", ".psb", ".rla", ".rpf", ".pict")

###  ==========  Functions  ==========  ###

# Arrange All Nodes
def ArrangeAll() -> None:
    """Arrange All Nodes command in *Cinema 4D*.
    """
    c4d.CallCommand(ALIGNALLNODES)

# Arrange Selected Nodes
def ArrangeSelected() -> None:
    """Arrange Selected Nodes command in *Cinema 4D*.
    """
    c4d.CallCommand(ALIGNNODES)

# 清空控制台
def ClearConsole():
    """Clears the console window of *Cinema 4D*.
    """
    c4d.CallCommand(13957)

# 获取渲染器
def GetRenderEngine(document: c4d.documents.BaseDocument = None) -> int :
    """
    Return current render engine ID.

    Args:
        document (c4d.documents.BaseDocument, optional): Fill None to check active documents. Defaults to None.

    Returns:
        int: The Id of the document renderer.
    """
    if not document:
        document = c4d.documents.GetActiveDocument()
    return document.GetActiveRenderData()[c4d.RDATA_RENDERENGINE]

# 获取渲染器VideoPost
def GetVideoPost(document: c4d.documents.BaseDocument = None, videopost: int = ID_REDSHIFT) -> Optional[c4d.documents.BaseVideoPost]:
    """
    Get the videopost of given render engine of filled document.

    Args:
        document (c4d.documents.BaseDocument, optional): Fill None to check active documents. Defaults to None.
        videopost (int, optional): The id of the videopost. Defaults to ID_REDSHIFT.

    Returns:
        Optional[c4d.documents.BaseVideoPost]: The videopost we get.
    """
    if not document:
        document = c4d.documents.GetActiveDocument()

    rdata: c4d.documents.RenderData = document.GetActiveRenderData()
    vpost: c4d.documents.BaseVideoPost = rdata.GetFirstVideoPost()
    theVp: c4d.documents.BaseVideoPost = None

    while vpost:
        if vpost.GetType() == int(videopost):
            theVp = vpost
        vpost = vpost.GetNext()
    return theVp

# 添加渲染器VideoPost
def AddVideoPost(document: c4d.documents.BaseDocument = None, videopost: int = ID_REDSHIFT) -> None:
    """
    Add the videopost of given render engine of filled document.

    Args:
        document (c4d.documents.BaseDocument, optional): Fill None to check active documents. Defaults to None.
        videopost (int, optional): The id of the videopost. Defaults to ID_REDSHIFT.
    """
    if not document:
        document = c4d.documents.GetActiveDocument()

    rdata: c4d.documents.RenderData = document.GetActiveRenderData()
    vpost: c4d.documents.BaseVideoPost = rdata.GetFirstVideoPost()

    while vpost:
        if vpost.GetType() == int(videopost):
            vpost.Remove()

        vpost = vpost.GetNext()

    if not vpost:
        vpost = c4d.documents.BaseVideoPost(videopost)
        rdata.InsertVideoPostLast(vpost)
    return vpost

# 切换渲染器VideoPost
def ChangeRenderer(document: c4d.documents.BaseDocument = None, videopost: int = ID_REDSHIFT) -> Optional[c4d.documents.BaseVideoPost]:
    """
    Change the videopost of given render engine of filled document.

    Args:
        document (c4d.documents.BaseDocument, optional): Fill None to check active documents. Defaults to None.
        videopost (int, optional): The id of the videopost. Defaults to ID_REDSHIFT.
    """
    if not document:
        document = c4d.documents.GetActiveDocument()

    # If the document already set to the renderer we want, return the videopost of the renderer
    if GetRenderEngine(document) == videopost and (new_vp := GetVideoPost(document, videopost)) is not None:
        return new_vp

    if not document:
        document = c4d.documents.GetActiveDocument()

    rdata: c4d.documents.RenderData = document.GetActiveRenderData()
    rdata[c4d.RDATA_RENDERENGINE] = videopost
    AddVideoPost(document, videopost)

# Check if the file is an image
def IsImageFile(file: str) -> bool:
    """Check if the file is an image"""
    if not file:
        return False
    if not os.path.exists(file):
        return False
    if not os.path.isfile(file):
        return False
    return file.lower().endswith(IMAGE_EXTENSIONS)

#=============================================
# Util
#=============================================

# 获取所有对象
def get_all_nodes(doc: c4d.documents.BaseDocument) -> list[c4d.BaseObject] :
    """
    Return the list of all nodes in Object Manager.

    Args:
        doc (c4d.documents.BaseDocument): c4d.documents.BaseDocument
    Returns:
        list[c4d.BaseObject]: A List of all objects
    """
    def iterate(node: c4d.BaseObject) -> Generator[c4d.BaseObject, None, None]:
        while isinstance(node, c4d.BaseObject):
            yield node

            for child in iterate(node.GetDown()):
                yield child

            node = node.GetNext()

    result: list = []

    for node in iterate(doc.GetFirstObject()):

        if not isinstance(node, c4d.BaseObject):
            raise ValueError("Failed to retrieve node.")
            continue
        result.append(node)

    return result

# 根据[类型]获取对象
def get_nodes(doc: c4d.documents.BaseDocument, TRACKED_TYPES : list[int]) -> Union[list[c4d.BaseObject], bool] :
    """
    Walks an object tree and yields all nodes that are of a type which is contained in TRACKED_TYPES.
    Args:
        TRACKED_TYPES (list): All types to tracked
    Returns:
        list[c4d.BaseObject]: A List of all find objects
    """
    def iterate(node: c4d.BaseObject) -> Generator[c4d.BaseObject, None, None]:
        # Iterate over all nodes
        while isinstance(node, c4d.BaseObject):
            if node.GetType() in TRACKED_TYPES:
                yield node

            for child in iterate(node.GetDown()):
                yield child

            node = node.GetNext()

    # The list.
    result: list = []

    # For all tracked type objects in the passed document.
    for obj in iterate(doc.GetFirstObject()):

        if not isinstance(obj, c4d.BaseObject):
            raise ValueError("Failed to retrieve obj.")
            continue
        result.append(obj)

    if len(result) == 0:
        return False
    else: 
        # Return the object List.
        return result
    
# 根据[类型]获取标签
def get_tags(doc: c4d.documents.BaseDocument, TRACKED_TYPES : Union[list[int],int]) -> list[c4d.BaseTag] :
    """
    Return a list of all tags that are of a type which is contained in TRACKED_TYPES.

    Args:
        TRACKED_TYPES (list): All types to tracked
    Returns:
        list[c4d.BaseObject]: A List of all find objects
    """
    all_nodes = get_all_nodes(doc)
    result: list = []

    for node in all_nodes:
        tags = node.GetTags()
        for tag in tags:
            if tag.GetType() in TRACKED_TYPES or tag.GetType() == TRACKED_TYPES:
                result.append(tag)

    # Return the object List.
    return result

# 获取纹理标签对应的选集标签
def get_selection_tag(textureTag : c4d.TextureTag) -> c4d.SelectionTag :
    """
    Get the selection tag from the active texture tag.
    Args:
        textureTag (c4d.TextureTag): textureTag

    Returns:
        c4d.SelectionTag: The selection tag assign to the texture tag.
    """
    if not isinstance(textureTag, c4d.TextureTag):
        return   

    mattags: list[c4d.TextureTag] = [tag for tag in textureTag.GetObject().GetTags() if tag.GetType() == c4d.Tpolygonselection] # selection tag

    for selectionTag in mattags:
        if selectionTag.GetName() == textureTag[c4d.TEXTURETAG_RESTRICTION]:
            return selectionTag
    return False

# 获取选集标签对应材质
def get_material(selectionTag : c4d.SelectionTag) -> c4d.BaseMaterial :
    """
    Get the material from the selection tag.
    Args:
        avtag (c4d.SelectionTag): Active tags.
    Returns:
        c4d.BaseMaterial: The material reference to the selection tag.
    """
    if not isinstance(selectionTag, c4d.SelectionTag):
        return
        
    # get obj form tag
    obj : c4d.BaseObject = selectionTag.GetObject() 
    # get all tags
    tagnum = obj.GetTags() 
    if tagnum is None:
        raise RuntimeError("Failed to retrieve tags.")
    # mattag lsit
    matlist:list[c4d.BaseMaterial] = [] 
    # add mat tag to mattag list
    for tag in tagnum:
        if tag.GetRealType() == c4d.Ttexture: # c4d.Ttexture Tag 5616
            matlist.append(tag)
                
    for mat in matlist:
        # mat tag selection name = active tag
        if mat[c4d.TEXTURETAG_RESTRICTION]==selectionTag.GetName(): 
            return mat

# 获取选集标签对应纹理标签
def get_texture_tag(selectionTag : c4d.SelectionTag) -> Union[c4d.TextureTag, bool] :
    """
    Check if the selection tag has a material.
    Args:
        avtag (c4d.BaseTag, optional): The tag to check with. Defaults to doc.GetActiveTag().
    Returns:
        Union[c4d.TextureTag, bool]: The texture tag assign with the selection tag. Or False if None
    """
    if not isinstance(selectionTag, c4d.SelectionTag):
        return   
    # get obj form tag
    obj:c4d.BaseObject = selectionTag.GetObject()
    # get all tex tags
    textags = [t for t in obj.GetTags() if t.GetType()==5616]
    if textags is None:
        raise RuntimeError("Failed to retrieve texture tags.")
    for textag in textags:
        if textag[c4d.TEXTURETAG_RESTRICTION] == selectionTag.GetName():
            return textag
    return False

# 选择所有材质
def select_all_materials(doc: c4d.documents.BaseDocument = None):
    # Deselect All Mats
    if not doc:
        doc = c4d.documents.GetActiveDocument()
    for m in doc.GetActiveMaterials() :
        doc.AddUndo(c4d.UNDOTYPE_BITS, m)
        m.SetBit(c4d.BIT_ACTIVE)

# 取消选择所有材质
def deselect_all_materials(doc: c4d.documents.BaseDocument = None):
    # Deselect All Mats
    if not doc:
        doc = c4d.documents.GetActiveDocument()
    for m in doc.GetActiveMaterials() :
        doc.AddUndo(c4d.UNDOTYPE_BITS, m)
        m.DelBit(c4d.BIT_ACTIVE)

# 迭代对象
def iter_node(node, include_node=False, include_siblings=False):
    """Provides a non-recursive iterator for all descendants of a node.

    Args:
        node (c4d.GeListNode): The node to iterate over.
        include_node (bool, optional): If node itself should be included in
         the generator. Defaults to False. 
        include_siblings (bool, optional): If the siblings (and their
         descendants) of node should be included. Will implicitly include
         node (i.e. set include_node to True). Defaults to False. 

    Yields:
        c4d.GeListNode: A descendant of node.

    Example:
        For the following graph with object.2 as the input node.

        object.0
            object.1
            object.2
                object.3
                object.4
                    object.5
            object.6
                object.7
                object.8

        >> for node in iter_node(object_2, False, False):
        >>     print node.GetName()
        object.3
        object.4
        object.5
        >> for node in iter_node(object_2, True, False):
        >>     print node.GetName()
        object.2
        object.3
        object.4
        object.5
        >> for node in iter_node(object_2, True, True):
        >>     print node.GetName()
        object.1
        object.2
        object.3
        object.4
        object.5
        object.6
        object.7
        object.8
    """
    if not isinstance(node, c4d.GeListNode):
        msg = "The argument node has to be a c4d.GeListNode. Received: {}."
        raise TypeError(msg.format(type(node)))

    # Lookup lists
    input_node = node
    yielded_nodes = []
    top_nodes = []

    # Set top nodes (and set node to first sibling if siblings are included)
    if include_siblings:
        while node.GetNext():
            node = node.GetNext()
        top_nodes = [node]
        while node.GetPred():
            node = node.GetPred()
            top_nodes.append(node)
    else:
        top_nodes = [node]

    # Start of iterator
    while node:
        # Yield the current node if it has not been yielded yet
        if node not in yielded_nodes:
            yielded_nodes.append(node)
            if node is input_node and include_node:
                yield node
            elif node is not input_node:
                yield node

        # Get adjacent nodes
        is_top_node = node in top_nodes
        node_down = node.GetDown()
        node_next = node.GetNext()
        node_up = node.GetUp()

        if is_top_node:
            node_up = None
        if is_top_node and not include_siblings:
            node_next = None

        # Get the next node in the graph in a depth first fashion
        if node_down and node_down not in yielded_nodes:
            node = node_down
        elif node_next and node_next not in yielded_nodes:
            node = node_next
        elif node_up:
            node = node_up
        else:
            node = None

# 生成随机颜色
def generate_random_color(pastel_factor = 0.5) -> c4d.Vector:
    """
    Generate a random color with factor. 
    """
    def _color_distance(c1,c2):
        return sum([abs(x[0]-x[1]) for x in zip(c1,c2)])
    #_ 在指定饱和度生成随机颜色 v1.0
    def _get_random_color(pastel_factor):
        return [(x+pastel_factor)/(1.0+pastel_factor) for x in [random.uniform(0,1.0) for i in [1,2,3]]]
    existing_colors = []
    max_distance = None
    best_color = None
    for i in range(0,100):
        color = _get_random_color(pastel_factor = pastel_factor)
        if not existing_colors:
            return color
        best_distance = min([_color_distance(color,c) for c in existing_colors])
        if not max_distance or best_distance > max_distance:
            max_distance = best_distance
            best_color = color
    return c4d.Vector(*best_color)

# 辅助：打印vp信息
def list_vpdata(videopost: c4d.documents.BaseVideoPost):

    if  videopost is None:
        raise RuntimeError(f"Can't get the VideoPost")
    
    bc: c4d.BaseContainer = videopost.GetDataInstance()

    for key in range(len(bc)):
        key = bc.GetIndexId(key)
        try:
            print(f"Key: {key}, Value: {bc[key]}, DataType{bc.GetType(key)}")
        except AttributeError:
            print("Entry:{0} is DataType {1} and can't be printed in Python".format(key, bc.GetType(key)))

def srgb_to_linear(color: c4d.Vector) -> c4d.Vector:
    # r = (rgb[0] / 1.0)  ** (1 / gamma)
    # g = (rgb[1] / 1.0)  ** (1 / gamma)
    # b = (rgb[2] / 1.0)  ** (1 / gamma)
    # return c4d.Vector(r,g,b)
    
    if c4d.GetC4DVersion() >= 2025200:
        doc = c4d.documents.BaseDocument()
        converter: c4d.modules.render.OcioConverter = doc.GetColorConverter()
        return converter.TransformColor(color, c4d.COLORSPACETRANSFORMATION_OCIO_SRGB_TO_RENDERING)
    else:
        return c4d.utils.TransformColor(color, c4d.COLORSPACETRANSFORMATION_SRGB_TO_LINEAR)

def linear_to_srgb(color: c4d.Vector) -> c4d.Vector:
    if c4d.GetC4DVersion() >= 2025200:
        doc = c4d.documents.BaseDocument()
        converter: c4d.modules.render.OcioConverter = doc.GetColorConverter()
        return converter.TransformColor(color, c4d.COLORSPACETRANSFORMATION_OCIO_RENDERING_TO_SRGB)
    else:
        return c4d.utils.TransformColor(color, c4d.COLORSPACETRANSFORMATION_LINEAR_TO_SRGB)


# todo