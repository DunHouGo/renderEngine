#!c4dpy
# -*- coding: utf-8 -*-

###  ==========  INFO  ==========  ###

__author__ = "DunHou"
__version__ = "0.3.0"
__website__ = "https://www.boghma.com/"
__license__ = "MIT license"

# Released under the MIT license
# https://opensource.org/licenses/mit-license.php

###  ==========  Import Libs  ==========  ###
"""Provides functions and constants that are commonly used in all modules. Also exposes the sub-modules.
"""

import c4d
import os
import typing
from typing import Union, Optional, Callable
import functools
import time
import random
import math
import colorsys

try:
    import maxon
except Exception as error:
    print("import maxon error: ", error)

# if c4d.GetC4DVersion() <= 2023000:
#     print("This module better compatible with Cinema 4D R2023 and above.")

# import Renderer package
from Renderer import constants, utils
from Renderer.constants.common_id import *
from Renderer.utils.node_helper import NodeGraghHelper, EasyTransaction
from Renderer.utils.texture_helper import TextureHelper
from Renderer.utils import material_maker as MaterialMaker
from Renderer.utils.material_maker import PBRPackage
from Renderer.utils.material_maker import ArnoldPbrMaterial, RedshiftPbrMaterial, VrayPbrMaterial, OctanePbrMaterial, CoronaPbrMaterial, C4DPbrMaterial
from Renderer.utils.image_helper import ImageSequence

# import moudule if plugin installed
if c4d.plugins.FindPlugin(ID_REDSHIFT, type=c4d.PLUGINTYPE_ANY) is not None:
    from Renderer import Redshift
if c4d.plugins.FindPlugin(ID_ARNOLD, type=c4d.PLUGINTYPE_ANY) is not None:
    from Renderer import Arnold
if c4d.plugins.FindPlugin(ID_OCTANE, type=c4d.PLUGINTYPE_ANY) is not None:
    from Renderer import Octane
if c4d.plugins.FindPlugin(ID_VRAY, type=c4d.PLUGINTYPE_ANY) is not None:
    from Renderer import Vray
if c4d.plugins.FindPlugin(ID_CORONA, type=c4d.PLUGINTYPE_ANY) is not None:
    from Renderer import Corona
if c4d.plugins.FindPlugin(ID_CENTILEO, type=c4d.PLUGINTYPE_ANY) is not None:
    from Renderer import CentiLeo

SUPPORT_RENDERER: list[int] = [ID_REDSHIFT, ID_ARNOLD, ID_OCTANE, ID_CORONA, ID_VRAY]
IMAGE_EXTENSIONS: tuple[str] = ('.png', '.jpg', '.jpeg', '.tga', '.bmp', ".exr", ".hdr", ".tif", ".tiff","iff", ".psd", ".tx",  ".b3d", ".dds", ".dpx", ".psb", ".rla", ".rpf", ".pict")

###  ==========  Decorators  ==========  ###

# decorator 装饰器 状态栏信息
def Statusbar(msg: str) -> None:
    """A decorator for indicating a computationally expensive process in the *Cinema4D* status bar. 

    Will set the status bar text to the argument ``msg`` and start the spinning gadget in the status bar before the function/method is being called and then clear out the status bar after the scope of the function/method has been left.

    Note:
        This decorator performs *GUI* operations and therefor is bound by the threading limitations of *Cinema4D*. It should not be used on objects that are called in a threaded context.

    Args:
        msg (``any``): The message to be displayed in the status bar while the decorated function/method is running. Will be cast into a string with ``str()``.

    Returns:
        ``any``: The return value of the decorated function/method.

    **Example**
        Indicating the execution of an expensive method. Using `statusbar` as a class decorator will work analogously.

        .. code-block:: python
            
            @Statusbar("This might take a while ...")
            def some_expensive_method(self, *args, **kwargs):
                pass
    """
    def decorator(f):
        """
        """
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            """
            """
            if c4d.GetC4DVersion() >= 2025000:
                c4d.gui.StatusSetText(str(msg))
                c4d.gui.StatusSetSpin()
            else:
                c4d.StatusSetText(str(msg))
                c4d.StatusSetSpin()
            result = f(*args, **kwargs)
            if c4d.GetC4DVersion() >= 2025000:
                c4d.gui.StatusClear()
            else:
                c4d.StatusClear()
            return result
        return wrapper
    return decorator

# decorator 装饰器 打印函数名称和返回值
def PirntMe(func) -> None:
    """
    decorator to print the function name and the return value.

    **Example**

    .. code-block:: python

        @PirntMe
        def GetAssetId(self, *args, **kwargs):
            pass

    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        print(f"Function {func.__name__} return : {result = }")
        return result
    return wrapper

 # - Functions --------------------------------------------------------------

# decorator 装饰器 计时器
def TimeIt(func) -> None:
    """Provides a makeshift decorator for timing functions executions.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """Wraps and measures the execution time of the wrapped function.
        """
        t0: int = time.perf_counter()
        result: typing.Any = func(*args, **kwargs)
        print(f"Executing {func.__name__}() took {(time.perf_counter() - t0):.4f} seconds.")
        return result
    return wrapper

# decorator 装饰器 检查某个参数的类型
# @CheckArgType("arg_name", (type, tuple))
def CheckArgType(arg_name: str, expected_type: Union[type, tuple]) -> callable:  
    def decorator(func):  
        @functools.wraps(func)  
        def wrapper(*args, **kwargs):  
            # 获取参数位置  
            arg_positions = [i for i, param in enumerate(func.__code__.co_varnames) if param == arg_name]  
              
            # 检查位置参数  
            for pos in arg_positions:  
                if pos < len(args):  
                    arg_value = args[pos]  
                    break  
            else:  
                # 检查关键字参数  
                arg_value = kwargs.get(arg_name)  
                if arg_value is None:  
                    raise TypeError(f"Missing required argument '{arg_name}'")  
  
            # 检查参数类型  
            if not isinstance(arg_value, expected_type):  
                raise TypeError(f"Argument '{arg_name}' should be of type {expected_type}, got {type(arg_value)}")  
              
            return func(*args, **kwargs)  
          
        return wrapper  
      
    return decorator 


# decorator 装饰器 检查某个参数是否符合指定条件
# @CheckArgCallback("node", lambda node: isinstance(node, maxon.GraphNode) and node.GetKind() != maxon.NODE_KIND.NODE)
def CheckArgCallback(arg_name: str, callback: Callable):

    def decorator(func):
        @functools.wraps(func)  
        def wrapper(*args, **kwargs):
            # 检查参数是否存在
            if arg_name in kwargs:
                # 获取参数值
                param_value = kwargs[arg_name]
                # 使用回调函数判断参数是否符合条件
                if callback(param_value):
                    # 如果符合条件，则调用原始函数
                    return func(*args, **kwargs)
                else:
                    # 如果不符合条件，则抛出异常
                    raise ValueError(f"Invalid type for parameter '{param_value}' with {type(param_value)} for parameter '{arg_name}'")
            else:
                # 如果参数不存在，则抛出异常
                raise ValueError(f"Parameter '{arg_name}' is missing")
        return wrapper
    return decorator

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
    def iterate(node: c4d.BaseObject):
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
    def iterate(node: c4d.BaseObject):
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
    if not isinstance(TRACKED_TYPES, list):
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

### Colors ###
def hex_to_rgb(hex_color: str) -> c4d.Vector:
    if isinstance(hex_color, str):
        # 移除十六进制颜色代码中的'#'符号
        if hex_color.startswith('#'):
            hex_color = hex_color.lstrip('#')
        
        # 将十六进制颜色转换为RGB
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        
        # 将RGB转换为HSV
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        return c4d.utils.HSVToRGB(c4d.Vector(h,s,v))

def rgb_to_hex(rgb_color: c4d.Vector) -> str:
    rgb_color = c4d.utils.RGBToHSV(rgb_color)
    # 将HSV转换为RGB
    r, g, b = colorsys.hsv_to_rgb(rgb_color.x, rgb_color.y, rgb_color.z)
    
    # 将RGB转换为十六进制
    r = int(r * 255)
    g = int(g * 255)
    b = int(b * 255)
    
    # 格式化为两位十六进制数
    r = format(r, '02x')
    g = format(g, '02x')
    b = format(b, '02x')
    
    # 返回十六进制颜色代码
    return f"{r}{g}{b}".upper()

def cmyk_to_rgb(c, m, y, k):
    """
    将CMYK颜色转换为RGB颜色。

    参数:
    c (float): 青色 (0-100)
    m (float): 品红色 (0-100)
    y (float): 黄色 (0-100)
    k (float): 黑色 (0-100)

    返回:
    tuple: RGB颜色值 (0-255)
    """
    c, m, y, k = map(lambda x: x / 100.0, (c, m, y, k))
    r = round(255 * (1 - c) * (1 - k))
    g = round(255 * (1 - m) * (1 - k))
    b = round(255 * (1 - y) * (1 - k))
    return (r, g, b)

def lab_to_xyz(l, a, b):
    """
    将Lab颜色转换为XYZ颜色。

    参数:
    l (float): 亮度 (0-100)
    a (float): 绿色到红色 (通常范围是-128到128)
    b (float): 蓝色到黄色 (通常范围是-128到128)

    返回:
    tuple: XYZ颜色值
    """
    # 参考白点D65
    ref_x = 95.047
    ref_y = 100.000
    ref_z = 108.883

    # 将L值转换为f值
    fy = (l + 16) / 116
    fx = a / 500 + fy
    fz = fy - b / 200

    # 计算XYZ值
    x = ref_x * (fx ** 3) if fx ** 3 > 0.008856 else (fx - 16 / 116) * 3 * (0.008856 ** 2) * ref_x
    y = ref_y * (fy ** 3) if fy ** 3 > 0.008856 else (fy - 16 / 116) * 3 * (0.008856 ** 2) * ref_y
    z = ref_z * (fz ** 3) if fz ** 3 > 0.008856 else (fz - 16 / 116) * 3 * (0.008856 ** 2) * ref_z

    return (x, y, z)

def xyz_to_rgb(x, y, z):
    """
    将XYZ颜色转换为RGB颜色。

    参数:
    x (float): X值
    y (float): Y值
    z (float): Z值

    返回:
    tuple: RGB颜色值 (0-255)
    """
    # 转换矩阵
    matrix = [
        [3.2404542, -1.5371385, -0.4985314],
        [-0.9692660, 1.8760108, 0.0415560],
        [0.0556434, -0.2040259, 1.0572252]
    ]

    # 计算RGB值
    r = matrix[0][0] * x + matrix[0][1] * y + matrix[0][2] * z
    g = matrix[1][0] * x + matrix[1][1] * y + matrix[1][2] * z
    b = matrix[2][0] * x + matrix[2][1] * y + matrix[2][2] * z

    # 将RGB值限制在0-1范围内
    r = 12.92 * r if r <= 0.0031308 else 1.055 * (r ** (1 / 2.4)) - 0.055
    g = 12.92 * g if g <= 0.0031308 else 1.055 * (g ** (1 / 2.4)) - 0.055
    b = 12.92 * b if b <= 0.0031308 else 1.055 * (b ** (1 / 2.4)) - 0.055

    # 将RGB值转换为0-255范围并四舍五入
    r = round(max(0, min(255, r * 255)))
    g = round(max(0, min(255, g * 255)))
    b = round(max(0, min(255, b * 255)))

    return (r, g, b)

def lab_to_rgb(l, a, b):
    """
    将Lab颜色转换为RGB颜色。

    参数:
    l (float): 亮度 (0-100)
    a (float): 绿色到红色 (通常范围是-128到128)
    b (float): 蓝色到黄色 (通常范围是-128到128)

    返回:
    tuple: RGB颜色值 (0-255)
    """
    x, y, z = lab_to_xyz(l, a, b)
    return xyz_to_rgb(x, y, z)

def GetColorAs8Hex(color: c4d.Vector) -> str:
    """Returns an eight bit hex string representation of the given #color.
    """
    FLOAT_TO_INT: callable = lambda v: round(v * 255)
    return "#{0:02X}{1:02X}{2:02X}".format(
        FLOAT_TO_INT(color.x),
        FLOAT_TO_INT(color.y),
        FLOAT_TO_INT(color.z)
    )

def find_similar_colors(rgb_color: c4d.Vector, step=0.05, count: int = 2) -> list[c4d.Vector]:
    r, g, b = rgb_color.x, rgb_color.y, rgb_color.z
    h, s, v = colorsys.rgb_to_hsv(r, g, b)  
    similar_colors = []  
    for i in range(1, count+1):  
        new_h = (h + i * step) % 1
        color = colorsys.hsv_to_rgb(new_h, s, v)
        similar_colors.append(c4d.Vector(color[0], color[1], color[2]))  
    return similar_colors
  
def find_contrasting_color(rgb_color: c4d.Vector) -> c4d.Vector:  
    r, g, b = rgb_color.x, rgb_color.y, rgb_color.z
    h, s, v = colorsys.rgb_to_hsv(r, g, b)  
    contrast_h = (h + 0.5) % 1  # 约等于180度变化  
    color = colorsys.hsv_to_rgb(contrast_h, s, v)  # 可以调整饱和度和亮度以获得更好的对比效果  
    return c4d.Vector(color[0], color[1], color[2])

def rgb_to_hsv(rgb_color: c4d.Vector) -> tuple:
    r, g, b = rgb_color.x, rgb_color.y, rgb_color.z
    r, g, b = r/255.0, g/255.0, b/255.0  
    h, s, v = colorsys.rgb_to_hsv(r, g, b)  
    return h, s, v  
  
def compare_colors_hsv(color1: c4d.Vector, color2: c4d.Vector, threshold: float=0.1) -> bool:  

    h1, s1, v1 = rgb_to_hsv(color1)  
    h2, s2, v2 = rgb_to_hsv(color2)
  
    h_diff = min(abs(h1 - h2), 1 - abs(h1 - h2))  
      
    s_diff = abs(s1 - s2)  
    v_diff = abs(v1 - v2)

    distance = math.sqrt(h_diff**2 + s_diff**2 + v_diff**2)  

    return distance < threshold  

# ACEScg conversion matrix
M_SRGB_TO_ACESCG = [
    [0.6134, 0.3395, 0.0470],
    [0.0701, 0.9163, 0.0136],
    [0.0203, 0.1096, 0.8691]
]

# def srgb_to_linear(value: float) -> float:
#     """
#     Convert a single sRGB channel to linear RGB.
#     """
#     if value <= 0.04045:
#         return value / 12.92
#     else:
#         return ((value + 0.055) / 1.055) ** 2.4

def linear_to_acescg(linear_rgb: c4d.Vector) -> c4d.Vector:
    """
    Convert a linear RGB color to ACEScg using the conversion matrix.
    """
    r = linear_rgb.x * M_SRGB_TO_ACESCG[0][0] + linear_rgb.y * M_SRGB_TO_ACESCG[0][1] + linear_rgb.z * M_SRGB_TO_ACESCG[0][2]
    g = linear_rgb.x * M_SRGB_TO_ACESCG[1][0] + linear_rgb.y * M_SRGB_TO_ACESCG[1][1] + linear_rgb.z * M_SRGB_TO_ACESCG[1][2]
    b = linear_rgb.x * M_SRGB_TO_ACESCG[2][0] + linear_rgb.y * M_SRGB_TO_ACESCG[2][1] + linear_rgb.z * M_SRGB_TO_ACESCG[2][2]

    return c4d.Vector(r, g, b)


def hex_to_acescg_vector(hex_value: str) -> c4d.Vector:
    """
    Convert a HEX color to an ACEScg vector.
    """
    r_srgb = int(hex_value[0:2], 16) / 255.0
    g_srgb = int(hex_value[2:4], 16) / 255.0
    b_srgb = int(hex_value[4:6], 16) / 255.0

    # Convert sRGB to linear RGB
    r_linear = srgb_to_linear(r_srgb)
    g_linear = srgb_to_linear(g_srgb)
    b_linear = srgb_to_linear(b_srgb)
    linear_rgb = c4d.Vector(r_linear, g_linear, b_linear)

    # Convert linear RGB to ACEScg
    return linear_to_acescg(linear_rgb)


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

# 颜色空间转换
def srgb_to_linear(color: c4d.Vector) -> c4d.Vector:
    return c4d.utils.TransformColor(color, c4d.COLORSPACETRANSFORMATION_LINEAR_TO_SRGB)

def linear_to_srgb(color: c4d.Vector) -> c4d.Vector:
    return c4d.utils.TransformColor(color, c4d.COLORSPACETRANSFORMATION_SRGB_TO_LINEAR)

# todo