# -*- coding: utf-8 -*-  

# Develop for Maxon Cinema 4D version 2023.2.0
#   ++> Corona Render version 2022.1.1

###  ==========  Copyrights  ==========  ###

"""
    Copyright [2023] [DunHouGo]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

###  ==========  Author INFO  ==========  ###

__author__ = "DunHouGo"
__copyright__ = "Copyright (C) 2023 Boghma"
__website__ = "https://www.boghma.com/"
__license__ = "Apache-2.0 License"
__version__ = "2023.2.1"

###  ==========  Import from boghma  ==========  ###
import c4d
from typing import Optional,Union, Any, Generator
import os
import sys
import Renderer
from Renderer.constants.corona_id import *

def iterate(node):
    while isinstance(node, c4d.BaseList2D):
        yield node

        for child in iterate(node.GetDown()):
            yield child

        node = node.GetNext()


class AOVHelper:

    """
    Custom helper to modify corona AOVs. corona aovs store in render element scene hook with c4d.BaseObject.
    """

    def __init__(self, vp: c4d.documents.BaseVideoPost = None):
        
        if isinstance(vp, c4d.documents.BaseVideoPost):
            if vp.GetType() == int(Renderer.ID_CORONA):
                self.doc = vp.GetDocument()
                self.vp: c4d.documents.BaseVideoPost = vp
                self.vpname: str = self.vp.GetName()
                self.head: c4d.GeListHead = self.get_master_head()

        elif vp is None:
            self.doc: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
            self.vp: c4d.documents.BaseVideoPost = Renderer.GetVideoPost(self.doc, Renderer.ID_CORONA)
            self.vpname: str = self.vp.GetName()
            self.head: c4d.GeListHead = self.get_master_head()

        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        if self.head is None:
            raise RuntimeError(f"Can't get the Render Element for {self.vpname}")

    # 名称对照字典 DEV
    def _convert_namedata(self) -> None:
        """
        A help function to convert list, you should no need use this, just for dev.
        """
        for node in self.get_all_aovs():
            name = f"CORONA_AOV_{node.GetName()}"
            print( name.upper().replace(" ", "_"), "=", [node.GetType(), node.GetParameter(VRAY_RENDER_ELEMENT_CREATE_NODE_TYPE, c4d.DESCFLAGS_GET_NONE), name] )

    # aov data
    def get_aov_data(self) -> Optional[dict[str,int]]:
        """
        Get all aov data in a list of BaseContainer.
        
        Parameters
        ----------        
        :return: the data list
        :rtype: Optional[dict[str,int]]
        """
        pass

    def iterater(self, node: c4d.BaseObject) -> Generator[None, None, c4d.BaseObject]:
        """
        Iterate the aov nodes.

        Args:
            node (c4d.BaseObject): the node we start from.
        """
        while isinstance(node, c4d.BaseObject):
            yield node

            for child in self.iterater(node.GetDown()):
                yield child

            node = node.GetNext()

    # 获取Render Elemnt的GeListHead
    def get_master_head(self) -> Optional[c4d.GeListHead]:
        """Get the master head of the render element.
        """
        sceneHook: c4d.BaseList2D = self.doc.FindSceneHook(CORONA_STR_MULTIPASSHOOK)
        if sceneHook is None:
            return None
        info = sceneHook.GetBranchInfo(c4d.GETBRANCHINFO_NONE)
        if info is None:
            return None
        head = info[0]["head"]
        if head is None:
            return None
        return head

    def enable_mutipass(self, enable: bool = True) -> None:
        """Enable or disable the multipass render element.
        """
        sceneHook: c4d.BaseList2D = self.doc.FindSceneHook(CORONA_STR_MULTIPASSHOOK)
        if sceneHook is None:
            raise RuntimeError(f"Can't get the {self.vpname} Render Element hook")
        sceneHook[c4d.CORONA_MULTIPASS_ENABLE] = enable
        return True

    def get_type(self, node: c4d.BaseObject) -> int:
        """Get the type of the given node."""
        return node.GetParameter(CORONA_MULTIPASS_BASE_TYPE, c4d.DESCFLAGS_GET_NONE)

    def get_type_name(self, node: c4d.BaseObject) -> int:
        """Get the type of the given node."""
        return node.GetParameter(CORONA_MULTIPASS_BASE_TYPE_NAME, c4d.DESCFLAGS_GET_NONE)

    def get_name(self, node: c4d.BaseObject) -> str:
        """Get the name of the given node."""
        return node.GetParameter(CORONA_MULTIPASS_BASE_NAME, c4d.DESCFLAGS_GET_NONE)

    def get_enable(self, node: c4d.BaseObject) -> bool:
        """Get the enable check of the given node."""
        return node.GetParameter(CORONA_MULTIPASS_BASE_ENABLE, c4d.DESCFLAGS_GET_NONE)

    def get_aa(self, node: c4d.BaseObject) -> bool:
        """Get the anti-alias check of the given node."""
        return node.GetParameter(CORONA_MULTIPASS_BASE_ANTIALIASED, c4d.DESCFLAGS_GET_NONE)

    def set_type(self, node: c4d.BaseObject, arg: int) -> bool:
        """Set the type of the given node."""
        return node.SetParameter(CORONA_MULTIPASS_BASE_TYPE, arg, c4d.DESCFLAGS_SET_NONE)

    def set_type_name(self, node: c4d.BaseObject, arg: int) -> bool:
        """Set the type of the given node."""
        return node.SetParameter(CORONA_MULTIPASS_BASE_TYPE_NAME, arg, c4d.DESCFLAGS_SET_NONE)

    def set_name(self, node: c4d.BaseObject, arg: str) -> str:
        """Set the name of the given node."""
        return node.SetParameter(CORONA_MULTIPASS_BASE_NAME, arg, c4d.DESCFLAGS_SET_NONE)

    def set_enable(self, node: c4d.BaseObject, arg: int) -> bool:
        """Set the enable check of the given node."""
        return node.SetParameter(CORONA_MULTIPASS_BASE_ENABLE, arg, c4d.DESCFLAGS_SET_NONE)

    def set_aa(self, node: c4d.BaseObject, arg: int) -> bool:
        """Set the denoise check of the given node."""
        return node.SetParameter(CORONA_MULTIPASS_BASE_ANTIALIASED, arg, c4d.DESCFLAGS_SET_NONE)

    # 获取所有aov shader ==> ok
    def get_all_aovs(self) -> list[c4d.BaseObject] :
        """
        Get all corona aovs in a list.

        Returns:
            list[c4d.BaseObject]: A List of all find nodes

        """
        
        """Get all render elements in the scene."""
        res = []
        for node in self.iterater(self.get_master_head().GetFirst()):
            res.append(node)
        return res

    # 获取指定类型的aov shader ==> ok
    def get_aov(self, aov_type: int) -> list[c4d.BaseObject]:
        """
        Get all the aovs of given type in a list.
        
        Args:
            aov_type (Union[int, c4d.BaseShader]): Shader to iterate.
            
        Returns:
            list[int]: A List of all find aovs

        """

        # The list.
        result: list = []

        start_shader = self.get_master_head().GetFirst()
        if not start_shader:
            return result
        for obj in self.iterater(start_shader):
            if self.get_type(obj) != aov_type:
                continue
            result.append(obj)

        return result

    # 打印aov ==> ok
    def print_aov(self):
        """
        Print main info of existed aov in python console.

        """
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        
        aovs = self.get_all_aovs()
        aovCnt = len(aovs)
        # color_space = self.vp[c4d.SETTINGSUNITSINFO_RGB_COLOR_SPACE]
        # if color_space == 1:
        #     color_str = "sRGB"
        # elif color_space == 2:
        #     color_str = "ACEScg"
                      
        print ("--- CORONA RENDER ---")
        print ("Name:", self.vp.GetName())
        # print ("Color space:", color_str)
        print ("AOV count:", aovCnt)
        
        if aovCnt == 0:
            print("No AOV data in this scene.")
        else:
            for aov in aovs:
                if aov is not None:
                    aov_enabled = self.get_enable(aov)
                    aov_name = self.get_name(aov)
                    aov_type = self.get_type(aov)

                    print("--"*10)
                    print("Name                  :%s" % aov_name)
                    print("Type                  :%s" % str(aov_type))
                    print("Enabled               :%s" % ("Yes" if aov_enabled else "No"))                            
                    # # Z-Depth
                    # if aov_type == 12:
                    #     print ("Subdata: Z-depth black:",aov[c4d.RENDERCHANNELZDEPTH_DEPTH_BLACK],
                    #            "Z-depth white:",aov[c4d.RENDERCHANNELZDEPTH_DEPTH_WHITE],
                    #            "Invert:",aov[c4d.RENDERCHANNELZDEPTH_DEPTH_INVERT])

                    # # Cryptomatte
                    # if aov_type == 34:
                    #     print ("Subdata: Cryptomatte type:", aov[c4d.RENDERCHANNELCRYPTOMATTE_ID_TYPE])
                
        print ("--- CORONA RENDER ---")

    # 创建aov ==> ok
    def create_aov_shader(self, aov_type: int, aov_name: str = None) -> c4d.BaseObject :
        """
        Create a shader of corona aov.

        :param aov_tye: the aov int type, this is a list of main id and sub type of the aov, find it in corona_id.py
        :type aov_tye: int, optional
        :param aov_name: the aov name, defaults to ""
        :type aov_name: str, optional 
        :return: the aov shader
        :rtype: c4d.BaseObject
        """
        
        aov = c4d.BaseObject(CORONA_MULTIPASS_AOV)
        self.set_type(aov, aov_type)

        if aov_name:
            self.set_name(aov, aov_name)
        else:
            self.set_name(aov, AOV_NAME_MAP[aov_type])

        return aov
    
    # 将aov添加到vp ==> ok
    def add_aov(self, aov_shader: c4d.BaseObject) -> c4d.BaseObject:
        """
        Add the corona aov shader to Octane Render.

        :param aov_shader: the corona aov shader
        :type aov_shader: c4d.BaseObject
        :return: the corona aov shader
        :rtype: c4d.BaseObject
        """
        if not isinstance(aov_shader, c4d.BaseObject):
            raise ValueError("corona AOV must be a c4d.BaseObject")
        
        # insert octane_aov to new port
        try:
            self.head.InsertFirst(aov_shader)
            self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,aov_shader)
        except:
            pass        
        return aov_shader

    # 为aov添加属性 ==> ok
    def set_aov(self, aov_shader: c4d.BaseObject , aov_id : int, aov_attrib)-> c4d.BaseObject :
        """
        A helper fucnction to set aov data.

        """
        if not isinstance(aov_shader,c4d.BaseObject):
            raise ValueError(f"Aov must be the {self.vpname} aov shader which is a BaseObject")    
        if aov_shader[aov_id] is not None:
            aov_shader[aov_id] = aov_attrib
        return aov_shader
        
    # 删除最新的aov ==> ok
    def remove_last_aov(self):
        """
        Remove the last aov shader.

        """
        self.get_all_aovs()[0].Remove()

    # 删除全部aov ==> ok
    def remove_all_aov(self):
        """
        Remove all the aov shaders.

        """
        for aov in self.get_all_aovs():
            if isinstance(aov, c4d.BaseObject):
                aov.Remove()  

    # 按照Type删除aov ==> ok
    def remove_aov_type(self, aov_type: int, filter_type: int = None):
        """
        Remove aovs of the given aov type.

        :param aov_type: the aov type to remove
        :type aov_type: int
        """
        for aov in self.get_all_aovs():
            if aov.CheckType(aov_type):
                if filter_type is not None:
                    if self.get_type(aov) == filter_type:
                        aov.Remove()  
                else:
                    aov.Remove() 


class MaterialHelper:

    #=============================================
    # Basic
    #=============================================

    def __init__(self, material: c4d.BaseMaterial = None):
        
        self.materialType: str = "Corona Material"

        # First we want to modify exsited material
        if isinstance(material, c4d.BaseMaterial):
            if not self.IsCoronaMaterial(material):
                raise ValueError("This is not an Corona Material")
            self.material: c4d.BaseMaterial = material

        else:
            self.material: c4d.BaseMaterial = self.CreateBasicMaterial()

        self.doc = self.SetDocument()

    def __str__(self):
        return (f"A Corona {self.__class__.__name__} Instance with Material : {self.material.GetName()}")

    #=============================================
    # Util
    #=============================================
    
    # 判断是否为Corona材质 ==> ok
    def IsCoronaMaterial(self, material: c4d.BaseMaterial) -> bool:
        """
        Check if the host material is an Corona Material.

        Returns:
            bool: True if the host material is an Corona Material, False otherwise.
        """
        if isinstance(material, c4d.BaseMaterial):
            if material.GetType() in ID_VALID_MATERIALS:
                return True
        return False

    # 创建基础材质 ==> ok
    def CreateBasicMaterial(self, matName: str = None) -> c4d.BaseMaterial:
        """
        Create an Corona Basic(classic) material of given type and name.
        """

        # Basic Corona Mat Type 
        material = c4d.BaseMaterial(CORONA_STR_MATERIAL_PHYSICAL)
        if material is None:
            raise ValueError("Cannot create a BaseMaterial")

        if matName:
            material.SetName(matName)
       
        material.Update(True, True)
        return material

    # 设置材质 ==> ok
    def SetMaterial(self, material: c4d.BaseMaterial) -> c4d.BaseMaterial:
        """
        Set the host material of the helper class.

        Args:
            material (c4d.BaseMaterial): the host material.

        Returns:
            c4d.BaseMaterial: #material attribute of the class
        """

        if isinstance(material, c4d.BaseMaterial):
            if not self.IsCoronaMaterial():
                raise ValueError("This is not an Corona Material")
        self.material: c4d.BaseMaterial = material
        return self.material
    
    # 获取材质 ==> ok
    def GetMaterial(self) -> c4d.BaseMaterial:
        """
        Get the host material of the helper class.

        Returns:
            c4d.BaseMaterial: #material attribute of the class
        """
        return self.material

    # 设置文档 ==> ok
    def SetDocument(self, doc: c4d.documents.BaseDocument = None) -> c4d.documents.BaseDocument:
        """
        Set the document of the helper class.

        Args:
            doc (c4d.documents.BaseDocument): the document.

        Returns:
            c4d.documents.BaseDocument: #doc attribute of the class
        """
        if not doc:
            # We try to get the document
            if isinstance(self.material, c4d.BaseMaterial):
                self.doc: c4d.documents.BaseDocument = self.material.GetDocument()

            if self.doc is None:
                self.doc: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
        else:
            if not isinstance(doc, c4d.documents.BaseDocument):
                raise TypeError("The document must be of type c4d.documents.BaseDocument")
            self.doc = doc
        return self.doc

    # 获取文档 ==> ok
    def GetDocument(self) -> c4d.documents.BaseDocument:
        """
        Get the document of the helper class.

        Returns:
            c4d.documents.BaseDocument: #doc attribute of the class
        """
        return self.doc

    # 插入 ==> ok
    def InsertMaterial(self, doc: c4d.documents.BaseDocument = None) -> c4d.BaseMaterial:
        """
        Insert the material to the document.
        """
        if self.material is None: return False
        #self.material.Update(True, True)

        if not doc:
            doc = self.material.GetDocument()
            if doc is None:
                doc = c4d.documents.GetActiveDocument()

        doc.InsertMaterial(self.material)
        doc.AddUndo(c4d.UNDOTYPE_NEW, self.material)
        return self.material

    # 刷新材质 ==> ok
    def Refresh(self):
        """
        Refresh thumbnail.
        """
        self.material.Update(True, True)

    # 设置激活 ==> ok
    def SetActive(self, doc: c4d.documents.BaseDocument = None):
        """
        Set the material active in the document.
        """
        if self.material is not None:
            if not doc:
                doc = self.material.GetDocument()
                if doc is None:
                    doc = c4d.documents.GetActiveDocument()
            doc.SetActiveMaterial(self.material)
            doc.AddUndo(c4d.UNDOTYPE_BITS, self.material)

    # 获取节点名 ==> ok
    def GetName(self, node: c4d.BaseShader) -> str:
        """
        Retrieve the displayed name of a node. 
        This is a function to maintain consistency, and it is generally recommended to use BaseList2D.GetName()

        Args:
            node (maxon.GraphNode): the node

        Returns:
            Optional[str]: the name of the ndoe
        """
        if not isinstance(node, c4d.BaseShader):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a BaseShader, got {type(node)}')
            
        return node.GetName()

    # 设置节点名
    def SetName(self, node: c4d.BaseShader, name: str) -> bool:
        """
        Set the name of a node.
        This is a function to maintain consistency, and it is generally recommended to use BaseList2D.SetName()

        Args:
            node (c4d.BaseShader): the node
            name (str): the name of the node

        Returns:
            bool: True if the name has been changed.
        """
        if not isinstance(node, c4d.BaseShader):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a BaseShader, got {type(node)}')
        
        if not isinstance(name, str):
            raise ValueError('Expected a String, got {}'.format(type(name)))
        
        node.SetName(name)
        return True

    # 获取所有shader ==> ok
    def GetAllShaders(self) -> list[c4d.BaseList2D] :
        """
        Get all nodes of the material in a list.

        Returns:
            list[c4d.BaseList2D]: A List of all find nodes

        """

        # The list.
        result: list = []

        start_shader = self.material.GetFirstShader()
        if not start_shader:
            raise RuntimeError("No shader found")
        
        for obj in iterate(start_shader):

            result.append(obj)

        # Return the object List.
        return result

    # 添加Nodes ==> ok
    def AddShader(self, shaderID: int = None, parentNode: c4d.BaseList2D = None) -> c4d.BaseShader:
        """
        Add a shader to the material of the given type and slot.

        """
        theNode = c4d.BaseList2D(shaderID)
        if parentNode:
            self.material[parentNode] = theNode                                     
        self.material.InsertShader(theNode)
        if self.doc is not None:
            self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, self.material)
        return theNode

    # todo
    def AddConnectShader(self):
        pass

    # todo
    def InsertShader(self):
        pass

    # todo
    def RemoveShader(self, shader: c4d.BaseShader) -> None:
        return shader.Remove()

    # 是否是shader ==> ok
    def IsNode(self, node: c4d.BaseShader) -> bool:
        """
        Check if a true node is a valid node.

        Args:
            node (c4d.BaseShader): the node to check

        Returns:
            bool: True if node is a valid True node
        """
        return isinstance(node, c4d.BaseShader)

    # 获取特定shader ==> ok
    def GetNodes(self, node_type: c4d.BaseList2D) -> Union[list[c4d.BaseList2D],c4d.BaseList2D]:

        """
        Get all nodes of given type of the material in a list.

        Returns:
            list[c4d.BaseList2D]: A List of all find nodes

        """

        # The list.
        result: list = []

        start_shader = self.material.GetFirstShader()
        if not start_shader:
            raise RuntimeError("No shader found")
        
        for obj in iterate(start_shader):
            if obj.CheckType(node_type):
                result.append(obj)
            
        return result

    # 获取属性 ==> ok
    def GetShaderValue(self, node: c4d.BaseShader, paramId: Any = None) -> Any:
        """
        Returns the value stored in the given shader parameter.

        Args:
            node (c4d.BaseShader): the node
            paramId (Any): the port id. Defaults to None.

        Returns:
            maxon.Data: the value assigned to this port
        """
        # standard data type
        
        if not isinstance(node, c4d.BaseShader):
            raise TypeError("The given node is not a shader")
        if paramId is None:
            raise ValueError("The given paramId is None")
        try:
            return node[paramId]
        except Exception:
            return None

    # 设置属性 ==> ok
    def SetShaderValue(self, node: c4d.BaseShader, paramId: Any = None, value: Any = None) -> bool:
        """
        Sets the value stored in the given shader parameter.

        Args:
            node (c4d.BaseShader): the node
            paramId (Any): the port id. Defaults to None.
            value (Any): the value to set. Defaults to None.

        Returns:
            bool: True if the value has been changed.
        """

        if not isinstance(node, c4d.BaseShader):
            raise TypeError("The given node is not a shader")
        if paramId is None:
            raise ValueError("The given paramId is None")
    
        try:
            node[paramId] = value
            return True
        except Exception:
            return False

    # New 获取前方节点(只包含子节点)  ==> ok
    def GetPreNode(self, node: c4d.BaseShader) -> list[c4d.BaseShader]:
        """
        Return the nodes directly connected before the node.

        Args:
            node (c4d.BaseShader): the node

        Returns:
            list[c4d.BaseShader]: Return the nodes directly connected before the node.
        """
        result = list()
        for _ ,shader in self.GetConnections(node):
            result.append(shader)
        return result

    # New 获取后方节点(只包含子节点)  ==> ok
    def GetNextNode(self, node: c4d.BaseShader) -> list[c4d.BaseShader]:
        """
        Return the nodes directly connected after the node.

        Args:
            node (c4d.BaseShader): the node

        Returns:
            list[c4d.BaseShader]: Return the nodes directly connected after the node.
        """
        # Bail when the passed node is not a true node.
        if not isinstance(node, c4d.BaseShader):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a BaseShader, got {type(node)}')
        # The list.
        result: list = []
        for shader in self.GetAllShaders():
            for i in self.GetConnections(shader):
                if i[1] == node:                
                    result.append(shader)
        return result
    
    # New 获取前方节点树(包含节点树)  ==> ok
    def GetPreNodes(self, node: c4d.BaseShader, filter_asset: str = None) -> list:
        """
        Return the nodes connected before the node, include all the node chain.

        Args:
            node (c4d.BaseShader): the node
            filter_asset (str): the shader id we will keep, fill none to disable.

        Returns:
            list[c4d.BaseShader]: Return the nodes connected before the node, include all the node chain.
        """
        # Bail when the passed node is not a true node.
        if not isinstance(node, c4d.BaseShader):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a BaseShader, got {type(node)}')
        
        # The list.
        result: list = []

        for shader in iterate(node):
            if filter_asset is not None:
                if shader.GetType() == filter_asset and shader not in result:
                    result.append(shader)
            else:
                if shader not in result:
                    result.append(shader)

        # remove the node self
        result.remove(node)

        return result
    
    # New 获取后方节点树(包含节点树)  ==> ok
    def GetNextNodes(self, node: c4d.BaseShader, filter_asset: str = None) -> list:
        """
        Return the nodes connected after the node, include all the node chain.

        Args:
            node (c4d.BaseShader): the node

            filter_asset (str): the asset id we will keep, fill none to disable.

        Returns:
            list[c4d.BaseShader]: Return the nodes connected after the node, include all the node chain.
        """
        # Bail when the passed node is not a true node.
        if not isinstance(node, c4d.BaseShader):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a BaseShader, got {type(node)}')
        # The list.
        result: list = []

        for shader in self.GetAllShaders():
            if node in self.GetPreNodes(shader):
                result.append(shader)

        return result

    # 获取材质上被连接的端口列表 ==> ok
    def GetRootConnectedNodes(self) -> list[c4d.BaseShader]:
        """
        Get all root connected ports of given node of the shader in a list.

        Returns:
            list[c4d.BaseShader]: A List of all find nodes

        """
        # The list.
        result: list = []

        bc = self.material.GetDataInstance()
        if bc is None:
            raise RuntimeError("Failed to retrieve bc")
        for key in range(len(bc)):           
            key = bc.GetIndexId(key)
            try:
                if isinstance(bc[key], c4d.BaseShader):
                    result.append((key, bc[key]))
            except Exception :
                pass
        return result

    # Shader是否直连材质 ==> ok
    def IsRootShader(self, node: c4d.BaseShader) -> bool:
        """
        Check if the given node is dirctly connect to material.

        Returns:
            bool: True if connect to material, False if not.

        """
        for _, shader in self.GetRootConnectedNodes(node):
            if shader == node:
                return True
        return False
    
    # 获取shader上被连接的端口列表 ==> ok
    def GetConnections(self, node: c4d.BaseShader) -> list[tuple[int, c4d.BaseShader]]:
        """
        Get all connections of given node of the shader in a list.

        Returns:
            list[tuple[int, c4d.BaseShader]]: A list of all find nodes

        """
        # The list.
        result: list = []

        bc = node.GetDataInstance()
        if bc is None:
            raise RuntimeError("Failed to retrieve bc")

        for key in range(len(bc)):           
            key = bc.GetIndexId(key)
            if isinstance(bc[key], c4d.BaseShader):
                result.append((key, bc[key]))        
        return result

    # Shader是否独立
    def IsConnected(self, node: c4d.BaseShader) -> bool:
        """
        Check if the given node is isolated.

        Returns:
            bool: True if isolated, False if not.

        """
        if self.GetPreNode(node) or self.GetNextNode(node) or self.IsRootShader(node):
            return True
        return False

    # 寻找shader在材质上的插槽
    def GetMaterialPort(self, node: c4d.BaseShader) -> int:
        bc = self.material.GetDataInstance()
        #print(img.GetDown().GetMain())
        if bc is None:
            raise RuntimeError("Failed to retrieve bc")

        # Iterates over the content of the BaseContainer using a for loop
        for key in range(len(bc)):
            # Check if the data retrieved can be printed in python (some DataType are not supported in Python)
            key = bc.GetIndexId(key)
            try:
                if bc[key] == node:
                    # print(key, bc[key])
                    return key
            except Exception :
                pass
    
    # New 端口是否连接  ==> ok
    def IsPortConnected(self, node: c4d.BaseShader, port: int) -> bool:
        """
        Check if the port is connected.

        Args:
            port (c4d.BaseShader): The port to check.

        Returns:
            bool: True if the port is connected, False otherwise.
        """

        if not self.IsNode(port):
            raise RuntimeError("The port is not a node")
        if not port:
            raise RuntimeError("The port is empty")
        try:
            return self.IsNode(node[port])
        except Exception:
            return False

    # 查询shader连接的端口
    def GetConnectedPortAfter(self, node: c4d.BaseShader) -> int:
        """
        Add a Transform node to all the Image nodes.
        """
        for _, shader in self.GetRootConnectedNodes(node):
            if shader == node:
                return self.GetMaterialPort(node)
        
        # Get the next node.
        after_node: c4d.BaseShader = node.GetUp()

        bc = after_node.GetDataInstance()
        if bc is None:
            raise RuntimeError("Failed to retrieve bc")

        # Iterates over the content of the BaseContainer using a for loop
        for key in range(len(bc)):
            # Check if the data retrieved can be printed in python (some DataType are not supported in Python)
            key = bc.GetIndexId(key)
            try:
                if bc[key] == node:
                    return key
            except Exception :
                pass
        return False

    def AddTexture(self, texturePath: str = None, nodeName: str = None, color_space: int = CR_COLORSPACE_LINEAR,
                           parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Texture shader tree to the given slot(option).

        """
        
        theNode = self.AddShader(CORONA_STR_CORONABITMAPSHADER, parentNode)

        if texturePath:                
            theNode[c4d.CORONA_BITMAP_FILENAME] = texturePath
            
        theNode[c4d.CORONA_BITMAP_COLORPROFILE] = color_space

        if nodeName:
            theNode.SetName(nodeName)
            theNode[c4d.ID_BASELIST_NAME] = nodeName

        
        return theNode

