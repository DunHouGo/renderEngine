#!c4dpy
# -*- coding: utf-8 -*-

"""Provides classes that expose commonly used constants as immutable objects.
"""
import c4d
import maxon
from typing import Iterator, Optional, Union

import random
from .node_helper import NodeGraghHelper
from .texture_helper import TextureHelper, g_texture_helper
from .converter_ports import ConverterPorts
from ..constants import *
import os

# Custom Transaction with auto Commit
class EasyTransaction:
    """
    A class used to simplify a transaction for node gragh.

    You can use this without the ``Commit()`` function. it will call commit when we out context.

    EasyTransaction用法类似于maxon.GraphTransaction, 是一个maxon.GraphTransaction的自定义包装

    不需要手动执行Commit(), 会在with退出后自执行

    需要一个材质#material执行初始化 如果#material是c4d.BaseMaterial, 则自动使用文档对应的节点空间将材质转换为对象的MaterialHerlper实例

    __enter__方法返回值为MaterialHerlper实例, 如下

    Example:

        with EasyTransaction(material) as tr:
            ... # do something like change name

        ... auto call ``Commit()`` to end the changes as we quit the block.

    .. code-block:: python

        import c4d
        import Renderer
        from Renderer import Arnold, NodeGraghHelper

        def main() -> None:

            # 1.选择的material为材质实例
            material: c4d.BaseMaterial = c4d.documents.GetActiveDocument().GetActiveMaterial()

            # 2.或者直接创建材质示例
            material: c4d.BaseMaterial = Arnold.Material.CreateStandardSurface()

            # 自定义EasyTransaction
            with EasyTransaction(material) as tr:

                # tr是转换后的EasyTransaction下的Arnold MaterialHelper, 继承了NodeGraghHelper
                # tr: EasyTransaction(material).material
                # 使用MaterialHelper中的方法
                tr.AddMaxonNoise()

                # 使用NodeGraghHelper中的方法
                output = tr.GetOutput()

                # 导入材质(来自Arnold MaterialHelper)
                tr.InsertMaterial()

            # 退出with后, 自动执行Commit()

            # ...执行其他操作
            c4d.EventAdd()

    """

    # Enable this to merge all the change within the Transaction
    MERGE_UNDO: bool = True

    def __init__(self, material: c4d.BaseMaterial):
        """
        Creates a new EasyTransaction class with a material.

        Args:
            material (c4d.BaseMaterial): the host material
        """

        # if the matreial is not a NodeGraghHelper instance, we get the gragh of it
        if isinstance(material, c4d.BaseMaterial):

            self.nodeMaterial: c4d.NodeMaterial = material.GetNodeMaterialReference()
            # node
            self.nodespaceId: maxon.Id = c4d.GetActiveNodeSpaceId()
            if self.nodespaceId is None:
                raise ValueError("Cannot retrieve the NodeSpace.")
            self.nimbusRef: maxon.NimbusBaseRef = material.GetNimbusRef(self.nodespaceId)
            if self.nimbusRef is None:
                raise ValueError("Cannot retrieve the nimbus reference for that NodeSpace.")

            if self.nodespaceId == RS_NODESPACE:
                from .. import Redshift
                self.helper = Redshift.Material(material)
                self.graph: maxon.GraphModelInterface = self.helper.graph

            elif self.nodespaceId == AR_NODESPACE:
                from .. import Arnold
                self.helper = Arnold.Material(material)
                self.graph: maxon.GraphModelInterface = self.helper.graph

            elif self.nodespaceId == VR_NODESPACE:
                from .. import Vray
                self.helper = Vray.Material(material)
                self.graph: maxon.GraphModelInterface = self.helper.graph

            elif self.nodespaceId == CL_NODESPACE:
                from .. import CentiLeo
                self.helper = CentiLeo.Material(material)
                self.graph: maxon.GraphModelInterface = self.helper.graph

            if self.graph.IsNullValue():
                raise ValueError("Cannot retrieve the graph of this nimbus NodeSpace.")

        # if the #material is already a NodeGraghHelper instance, we inherit the gragh of the instance
        else:
            if isinstance(material, NodeGraghHelper):
                self.helper = material
                self.graph = material.graph
                self.nodespaceId = material.nodespaceId
                self.nimbusRef = material.nimbusRef
            else:
                try:
                    self.helper = material.material
                    if material is None:
                        raise ValueError(f"Cannot retrieve the material of {material} object.")
                    self.graph = material.graph
                    self.nodespaceId = material.nodespaceId
                    self.nimbusRef = material.nimbusRef

                except Exception as error:
                    raise RuntimeError(f"{__class__.__name__} can not handle the {material}, {error}") from error

        # transaction attribute
        self.transaction: maxon.GraphTransaction = None

        # no undo steps
        settings: maxon.DataDictionaryInterface = maxon.DataDictionary()
        if self.MERGE_UNDO:
            settings.Set(maxon.nodes.UndoMode, maxon.nodes.UNDO_MODE.NONE)
        self.setting = settings

    def __enter__(self):
        if self.helper is not None and self.graph is not None:
            self.transaction: maxon.GraphTransaction = self.graph.BeginTransaction(self.setting)
        return self.helper

    # auto commit
    def __exit__(self, type, value, traceback) -> None:
        if self.transaction is not None:
            self.transaction.Commit(self.setting)

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
def AddVideoPost(document: c4d.documents.BaseDocument = None, videopost: int = ID_REDSHIFT) -> Optional[c4d.documents.BaseVideoPost]:
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
            return vpost

        vpost = vpost.GetNext()

    vpost = c4d.documents.BaseVideoPost(videopost)
    if vpost is None:
        return None

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

    rdata: c4d.documents.RenderData = document.GetActiveRenderData()
    rdata[c4d.RDATA_RENDERENGINE] = videopost

    # 参考 Maxon 官方示例，先收集再移除，避免遍历 VideoPost 链表时原地删除节点。
    remove_vps: list[c4d.documents.BaseVideoPost] = []
    current_vp: c4d.documents.BaseVideoPost = rdata.GetFirstVideoPost()
    while current_vp:
        if current_vp.GetType() != int(videopost) and not current_vp.RenderEngineCheck(videopost):
            remove_vps.append(current_vp)
        current_vp = current_vp.GetNext()

    for current_vp in remove_vps:
        current_vp.Remove()

    return AddVideoPost(document, videopost)

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



def GetPreferenceDescID(pname: str) -> None:
    prefs = c4d.plugins.FindPlugin(ID_PREFERENCES_NODE)
    if not isinstance(prefs, c4d.BaseList2D):
        raise RuntimeError("Could not access preferences node.")

    for bc, descid, _ in prefs.GetDescription(0):
        name = bc[c4d.DESC_NAME]
        if pname in name:
            print(name)
            print(descid)



#=============================================
# Util
#=============================================


def iterate(node: c4d.BaseList2D) -> Iterator[c4d.BaseList2D]:
    while isinstance(node, c4d.BaseList2D):
        yield node
        for child in iterate(node.GetDown()):
            yield child
        node = node.GetNext()

# 获取所有对象
def get_all_nodes(doc: c4d.documents.BaseDocument) -> list[c4d.BaseObject] :
    """
    Return the list of all nodes in Object Manager.

    Args:
        doc (c4d.documents.BaseDocument): c4d.documents.BaseDocument
    Returns:
        list[c4d.BaseObject]: A List of all objects
    """
    def iterate(node: c4d.BaseObject) -> Iterator[c4d.BaseObject]:
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
    def iterate(node: c4d.BaseObject) -> Iterator[c4d.BaseObject]:
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
    if isinstance(TRACKED_TYPES, int):
        TRACKED_TYPES = [TRACKED_TYPES]
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
