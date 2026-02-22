# coding=utf-8

import c4d
from typing import Any
from ..constants import *
from ..utils import iterate

def IsOctaneMaterial(material: c4d.BaseMaterial) -> bool:
    if isinstance(material, c4d.BaseMaterial):
        if material.GetType() in OCTANE_MATERIALS:
            return True
    return False

class MaterialHelper:
    """
    material_types:
        ID_OCTANE_STANDARD_SURFACE,
        ID_OCTANE_BASE_MATERIAL,
        ID_OCTANE_COMPOSITE_MATERIAL
    """

    #=============================================
    # Basic
    #=============================================

    def __init__(self, material: c4d.BaseMaterial = None, create_standard: bool = False):
        
        self.materialType: str = "Octane"

        # First we want to modify exsited material
        if isinstance(material, c4d.BaseMaterial):
            if not self.IsOctaneMaterial(material):
                raise ValueError("This is not an Octane Material")
            self.material: c4d.BaseMaterial = material

        else:
            if create_standard:
                self.material: c4d.BaseMaterial = self.CreateStandardMaterial()
            else:
                self.material: c4d.BaseMaterial = self.CreateBasicMaterial(matType = MAT_TYPE_UNIVERSAL)

        # if self.material is None:
        #     raise ValueError(f"Cann't create Octane NodeHelper with {material}")
        
        self.doc = self.SetDocument()

    def __str__(self):
        return (f"A Octane {self.__class__.__name__} Instance with Material : {self.material.GetName()}")

    #=============================================
    # Util
    #=============================================
    
    # 判断是否为Octane材质 ==> ok
    def IsOctaneMaterial(self, material: c4d.BaseMaterial) -> bool:
        """
        Check if the host material is an Octane Material.

        Returns:
            bool: True if the host material is an Octane Material, False otherwise.
        """
        if isinstance(material, c4d.BaseMaterial):
            if material.GetType() in OCTANE_MATERIALS:
                return True
        return False

    # 创建Standard Surface材质 ==> ok
    def CreateStandardMaterial(self, matName: str = None, isMetal: bool = False) -> c4d.BaseMaterial:
        """
        Create an Octane Standard Surface material of given type and name.
        """
        try:
            # Basic Octane Mat Type 
            material = c4d.BaseMaterial(ID_OCTANE_STANDARD_SURFACE)            
            if material is None:
                raise ValueError("Cannot create a BaseMaterial") 
            
            material[c4d.STDMAT_BASELAYER_WEIGHT_FLOAT] = 1.0 # albedo
            material[c4d.STDMAT_BASELAYER_DIFROUGH_VAL] = 0.0 # albedo roughness
            material[c4d.STDMAT_SPECULARLAYER_ROUGH_VAL] = 0.2 # specular roughness
            
            if isMetal:
                material[c4d.STDMAT_BASELAYER_METALNESS_VAL] = 1.0
            else:
                material[c4d.STDMAT_BASELAYER_METALNESS_VAL] = 0.0
            
            if not matName:
                material.SetName(MAT_NAME_SYMBOLS.get(ID_OCTANE_STANDARD_SURFACE))
            else:
                material.SetName(matName)
                
            # Update material
            material.Update(True, True)
            return material
        
        except :
            ValueError("Cannot create Octane Material.")

    # 创建基础材质 ==> ok
    def CreateBasicMaterial(self, isMetal: bool = False, matType: int = MAT_TYPE_UNIVERSAL, matName: str = None) -> c4d.BaseMaterial:
        """
        Create an Octane Basic(classic) material of given type and name.
        """

        # Basic Octane Mat Type 
        material = c4d.BaseMaterial(ID_OCTANE_BASE_MATERIAL)
        if material is None:
            raise ValueError("Cannot create a BaseMaterial")

        material[c4d.OCT_MATERIAL_DIFFUSE_COLOR] = c4d.Vector(0.7,0.7,0.7) # albedo

        if matType == MAT_TYPE_SPECULAR:
            material[c4d.OCT_MATERIAL_FAKESHADOW] = True # fake shadow

        if isMetal:
            material[c4d.OCT_MATERIAL_TYPE] = MAT_TYPE_UNIVERSAL
            material.SetName(MAT_NAME_SYMBOLS.get(MAT_TYPE_UNIVERSAL))
            material[c4d.OCT_MAT_BRDF_MODEL] = 6 # ggx energy preserving, for annistropy
            material[c4d.OCT_MAT_USE_COLOR] = c4d.Vector(0,0,0) # albedo black

        else:
            try:
                material[c4d.OCT_MATERIAL_TYPE] = matType
            except:
                material[c4d.OCT_MATERIAL_TYPE] = MAT_TYPE_UNIVERSAL                    

            material[c4d.OCT_MAT_BRDF_MODEL] = 6 # ggx energy preserving
            material[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.2
            material[c4d.OCT_MAT_USE_MATERIAL_LAYER] = True

            # Name
            if not matName:
                for name in MAT_NAME_SYMBOLS.keys():
                    matName = MAT_NAME_SYMBOLS.get(name)
                    if matName == material[c4d.OCT_MATERIAL_TYPE]:
                        material.SetName(DiffuseName)

            else:
                material.SetName(matName)
       
        material.Update(True, True)
        return material

    # 创建合成材质 ==> ok
    def CreateComposite(self, matName: str = None, compNum: int = 2) -> c4d.BaseMaterial:
        """
        Create an Octane Composite material of given type and name.
        """
        
        try:
            material = c4d.BaseMaterial(ID_OCTANE_COMPOSITE_MATERIAL)
            if material is None:
                raise ValueError("Cannot create a BaseMaterial")
            
            if matName:
                material.SetName(matName)
            else:
                material.SetName(MAT_NAME_SYMBOLS.get(ID_OCTANE_COMPOSITE_MATERIAL))
                
            material[c4d.BLENDMAT_NUM_OF_MATERIALS] = compNum
            
            for i ,subnode in enumerate(compNum): 
                subnode = c4d.BaseList2D(SUBMaterialNodeID)
                material.InsertShader(subnode)
                material[1300 + i] = subnode
            
            # Update material
            material.Update(True, True)
            return material
            
        except :
            ValueError("Cannot create Octane Material.")

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
            if not self.IsOctaneMaterial():
                raise ValueError("This is not an Octane Material")
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

    # 在shader后插入shader ==> ok
    def AddConnectShader(self, shader: c4d.BaseShader, newShader: c4d.BaseShader, inputSlot: int) -> c4d.BaseShader:
        parrent = self.GetNextNode(shader)
        # shader
        if len(parrent):
            parrent = parrent[0]
            slot = self.GetConnectedPortAfter(shader)
        # root
        else:
            parrent = shader.GetMain()
            slot = self.GetMaterialPort(shader)
        newShader[inputSlot] = shader
        parrent[slot] = newShader
        return newShader

    # todo
    def InsertShader(self):
        pass

    def RemoveShader(self, shader: c4d.BaseShader) -> None:
        return shader.Remove()

    # 比较shader是否为相同的shader
    def IsUnique(self, shader: c4d.BaseShader, anotherShader: c4d.BaseShader) -> bool:
        """
        Return True if the two shaders is a same shader
        """
        if not isinstance(shader, c4d.BaseShader) or not isinstance(anotherShader, c4d.BaseShader):
            return False

        if shader.GetType() != anotherShader.GetType():
            return False

        if bytes(shader.FindUniqueID(c4d.MAXON_CREATOR_ID)) != bytes(anotherShader.FindUniqueID(c4d.MAXON_CREATOR_ID)):
            return False
        return True

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
    def GetNodes(self, node_type: c4d.BaseList2D) -> list[c4d.BaseList2D]:

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
    def GetNextNode(self, node: c4d.BaseShader) -> list[c4d.BaseShader,c4d.BaseMaterial]:
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
        for _, shader in self.GetRootConnectedNodes():
            if shader == node:
                return self.GetMaterialPort(node)
        
        # Get the next node.
        after_node: c4d.BaseShader = self.GetNextNode(node)[0]#node.GetUp()
        if after_node is None:
            return False
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

    # 刷新贴图 ==> ok
    def RefreshTextures(self):
        """
        Reload all the texture shader.

        """
        nodes: list[c4d.BaseShader] = self.GetNodes(ID_OCTANE_IMAGE_TEXTURE)
        for node in nodes:
            node[c4d.IMAGETEXTURE_FORCE_RELOAD] = 1
            node.SetDirty(c4d.DIRTYFLAGS_ALL)
        #c4d.EventAdd()
    
    # 重置压缩 ==> ok
    def ResetCompression(self):
        """
        Reset all the texture shader compression.

        """
        nodes: list[c4d.BaseShader] = self.GetNodes(ID_OCTANE_IMAGE_TEXTURE)
        for node in nodes:
            node[c4d.IMAGETEX_COMPR_FORMAT] = 0  # reset the compression
        c4d.EventAdd()

    #=============================================
    # Presets
    #=============================================

    def AddTransform(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Transform shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_TRANSFORM, parentNode)
    
    def AddProjection(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Projection shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_TEXTURE_PROJECTION, parentNode)

    def AddMultiply(self, nodeA: c4d.BaseList2D, nodeB: c4d.BaseList2D, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Multiply shader to the given slot(option).

        """
        theNode = self.AddShader(ID_OCTANE_MULTIPLY_TEXTURE, parentNode)
        if nodeA:
            theNode[c4d.MULTIPLY_TEXTURE1] = nodeA
        if nodeB:
            theNode[c4d.MULTIPLY_TEXTURE2] = nodeB
        return theNode
    
    def AddSubtract(self, nodeA: c4d.BaseList2D, nodeB: c4d.BaseList2D, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Subtract shader to the given slot(option).

        """
        theNode = self.AddShader(ID_OCTANE_SUBTRACT_TEXTURE, parentNode)
        if nodeA:
            theNode[c4d.MULTIPLY_TEXTURE1] = nodeA
        if nodeB:
            theNode[c4d.MULTIPLY_TEXTURE2] = nodeB
        return theNode

    def AddMathAdd(self, nodeA: c4d.BaseList2D, nodeB: c4d.BaseList2D, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a MathAdd shader to the given slot(option).

        """
        theNode = self.AddShader(ID_OCTANE_ADD_TEXTURE, parentNode)
        if nodeA:
            theNode[c4d.MULTIPLY_TEXTURE1] = nodeA
        if nodeB:
            theNode[c4d.MULTIPLY_TEXTURE2] = nodeB
        return theNode

    def AddMix(self, mix_amount: float, nodeA: c4d.BaseList2D, nodeB: c4d.BaseList2D, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Mix shader to the given slot(option).

        """
        theNode = self.AddShader(ID_OCTANE_MIXTEXTURE, parentNode)        
        if mix_amount:
            theNode[c4d.MIXTEX_AMOUNT_FLOAT] = mix_amount
        if nodeA:
            theNode[c4d.MULTIPLY_TEXTURE1] = nodeA
        if nodeB:
            theNode[c4d.MULTIPLY_TEXTURE2] = nodeB
        return theNode

    def AddInvert(self, imageTexture: c4d.BaseList2D, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Invert shader to the given slot(option).

        """
        theNode = self.AddShader(ID_OCTANE_INVERT_TEXTURE, parentNode)
        if imageTexture:
            theNode[c4d.INVERT_TEXTURE] = imageTexture       
        return theNode

    def AddFloat(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Float shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_FLOAT_TEXTURE, parentNode)

    def AddRGB(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a RGB shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_RGBSPECTRUM, parentNode)

    def AddImageTexture(self, texturePath: str = "", nodeName: str = None, isFloat: bool = True, gamma: int = 1,
                           invert: bool = False, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a ImageTexture shader to the given slot(option).

        """
        
        theNode = self.AddShader(ID_OCTANE_IMAGE_TEXTURE, parentNode)

        if texturePath:                
            theNode[c4d.IMAGETEXTURE_FILE] = texturePath

        theNode[c4d.IMAGETEXTURE_INVERT] = invert
        theNode[c4d.IMAGETEXTURE_GAMMA] = gamma
        
        if isFloat:
            theNode[c4d.IMAGETEXTURE_MODE] = 1 # 1 = Float and 0 is Normal (Color)
        else:
            theNode[c4d.IMAGETEXTURE_MODE] = 0
        
        if nodeName:
            theNode.SetName(nodeName)
        return theNode

    def AddCC(self, imageTexture: c4d.BaseList2D = None, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Color Correction shader to the given slot(option).

        """
        theNode = self.AddShader(ID_OCTANE_COLORCORRECTION, parentNode)
        if imageTexture:
            theNode[c4d.COLORCOR_TEXTURE_LNK] = imageTexture       
        return theNode

    def AddGradient(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Gradient shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_GRADIENT_TEXTURE, parentNode)

    def AddFalloff(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Falloff shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_FALLOFFMAP, parentNode)

    def AddDirt(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Dirt shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_DIRT_TEXTURE, parentNode)

    def AddCurvature(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Curvature shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_CURVATURE_TEX, parentNode)

    def AddNoise4D(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Maxon Noise shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_C4DNOISE_TEX, parentNode)

    def AddNoise(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Octane Noise shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_NOISE_TEXTURE, parentNode)

    def AddTriplanar(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Triplanar shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_TRIPLANAR, parentNode)

    def AddDisplacement(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Displacement shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_DISPLACEMENT, parentNode)

    def AddBlackbodyEmission(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Blackbody Emission shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_BLACKBODY_EMISSION, parentNode)

    def AddTextureEmission(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Texture Emission shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_TEXTURE_EMISSION, parentNode)

    def AddTextureTree(self, texturePath: str = None, nodeName: str = None, isFloat: bool = True, gamma: int = 1,
                           invert: bool = False, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Texture + Color Correction + Gradient shader tree to the given slot(option).

        """
        
        theNode = self.AddShader(ID_OCTANE_IMAGE_TEXTURE, parentNode)

        if texturePath:                
            theNode[c4d.IMAGETEXTURE_FILE] = texturePath
            
        theNode[c4d.IMAGETEXTURE_INVERT] = invert
        theNode[c4d.IMAGETEXTURE_GAMMA] = gamma
        
        if isFloat:
            theNode[c4d.IMAGETEXTURE_MODE] = 1 # 1 = Float and 0 is Normal (Color)
        else:
            theNode[c4d.IMAGETEXTURE_MODE] = 0
        
        if nodeName:
            theNode.SetName(nodeName)
            
        gradientNode = self.AddGradient(parentNode)
        ccNode = self.AddCC(theNode)
        gradientNode[c4d.GRADIENT_TEXTURE_LNK] = ccNode
        ccNode[c4d.COLORCOR_TEXTURE_LNK] = theNode
        
        return theNode

    # 创建材质 ==> ok
    def SetupTextures(self, tex_data: dict = None, mat_name: str = None):
        """
        Setup a pbr material with given or selected texture.
        """        
        isSpecularWorkflow = False
        if 'Specular' in list(tex_data.keys()):
            isSpecularWorkflow = True            
        
        try:
            # 
            if "Diffuse" in tex_data:
                albedoNode = self.AddImageTexture(texturePath=tex_data['Diffuse'], nodeName="Albedo", isFloat=False, gamma=2.2)
                if albedoNode:
                    ccAlbedoNode = self.AddCC(albedoNode)
                    if "AO" in tex_data:
                        aoNode = self.AddImageTexture(texturePath=tex_data['AO'], nodeName="AO")
                        if aoNode:
                            self.AddMultiply(ccAlbedoNode, aoNode, c4d.OCT_MATERIAL_DIFFUSE_LINK)
                    else:
                        self.material[c4d.OCT_MATERIAL_DIFFUSE_LINK] = ccAlbedoNode
            
            if isSpecularWorkflow:
                if "Specular" in tex_data:
                    self.AddImageTexture(texturePath=tex_data['Specular'], nodeName="Specular",
                                         isFloat=False, gamma=2.2, parentNode=c4d.OCT_MATERIAL_SPECULAR_LINK)
                
                if "Glossiness" in tex_data:
                    glossNode = self.AddImageTexture(texturePath=tex_data['Glossiness'], nodeName="Gloss")
                    if glossNode:
                        ccGlossNode = self.AddCC(glossNode, parentNode=c4d.OCT_MATERIAL_ROUGHNESS_LINK)
                elif "Roughness" in tex_data:
                    roughnessNode = self.AddImageTexture(texturePath=tex_data['Roughness'], nodeName="Roughness")
                    if roughnessNode:
                        ccRoughnessNode = self.AddCC(roughnessNode, parentNode=c4d.OCT_MATERIAL_ROUGHNESS_LINK)
                        #ccRoughnessNode[c4d.COLORCOR_TEXTURE_LNK] = roughnessNode

            else:
                if "Metalness" in tex_data:
                    self.AddImageTexture(texturePath=tex_data['Metalness'], nodeName="Metalness", parentNode=c4d.OCT_MAT_SPECULAR_MAP_LINK)
                if "Roughness" in tex_data:
                    roughnessNode = self.AddImageTexture(texturePath=tex_data['Roughness'], nodeName="Roughness")
                    if roughnessNode:
                        ccRoughnessNode = self.AddCC(roughnessNode,parentNode=c4d.OCT_MATERIAL_ROUGHNESS_LINK)

                elif "Glossiness" in tex_data:
                    glossNode = self.AddImageTexture(texturePath=tex_data['Glossiness'], nodeName="Gloss")
                    if glossNode:
                        ccGlossNode = self.AddCC(glossNode,parentNode=c4d.OCT_MATERIAL_ROUGHNESS_LINK)
                        # self.material[c4d.OCT_MATERIAL_ROUGHNESS_LINK] = ccGlossNode
                
            if "Bump" in tex_data:  
                self.AddImageTexture(texturePath=tex_data['Bump'], nodeName="Bump",parentNode=c4d.OCT_MATERIAL_BUMP_LINK)

            if "Normal" in tex_data:  
                self.AddImageTexture(texturePath=tex_data['Normal'], nodeName="Normal", isFloat=False, gamma=1, parentNode=c4d.OCT_MATERIAL_NORMAL_LINK)
            
            if "Displacement" in tex_data:
                displacementNode = self.AddDisplacement(c4d.OCT_MATERIAL_DISPLACEMENT_LINK)
                if displacementNode:
                    displacementNode[c4d.DISPLACEMENT_LEVELOFDETAIL] = 11 # 2k
                    displacementSlotName = c4d.DISPLACEMENT_TEXTURE
                    displacementNode[displacementSlotName] = self.AddImageTexture(texturePath=tex_data['Displacement'], nodeName="Displacement")

            if "Alpha" in tex_data:  
                self.AddImageTexture(texturePath=tex_data['Alpha'], nodeName="Alpha", parentNode=c4d.OCT_MATERIAL_OPACITY_LINK)

            if "Translucency" in tex_data:  
                self.AddImageTexture(texturePath=tex_data['Translucency'], nodeName="Translucency", gamma=2.2, parentNode=c4d.OCT_MATERIAL_TRANSMISSION_LINK)
                self.material[c4d.UNIVMAT_TRANSMISSION_TYPE] = 1
            elif "Transmission" in tex_data:  
                self.AddImageTexture(texturePath=tex_data['Transmission'], nodeName="Transmission", gamma=1, parentNode=c4d.OCT_MATERIAL_TRANSMISSION_LINK)
                self.material[c4d.UNIVMAT_TRANSMISSION_TYPE] = 1
            self.material.SetName(mat_name)
            
        except Exception as e:
            raise RuntimeError ("Unable to setup texture")    

    # 统一缩放 ==> ok
    def UniTransform(self):
        """
        Add a Transform node to all the Image nodes.
        """
        images = self.GetNodes(ID_OCTANE_IMAGE_TEXTURE)
        trans_node = self.AddTransform()
        for image in images:
            image[c4d.IMAGETEXTURE_TRANSFORM_LINK] = trans_node

    def UniProjection(self, effectiveShaders: list[c4d.BaseShader]=None, projectionType: int = 6):
        """
        Add a Projection node to all the Image nodes.
        """
        if effectiveShaders is None:
            effectiveShaders = self.GetNodes(ID_OCTANE_IMAGE_TEXTURE)
        proj_node = self.AddProjection()
        proj_node[1360] = projectionType
        for image in effectiveShaders:
            image[c4d.IMAGETEXTURE_PROJECTION_LINK] = proj_node

    def AddTriplanars(self, effectiveShaders: list[c4d.BaseShader]=None):
        """
        Add Triplanar nodes to all the Image nodes.
        """
        if effectiveShaders is None:
            effectiveShaders = self.GetNodes(ID_OCTANE_IMAGE_TEXTURE)
        for shader in effectiveShaders:
            mysha = self.AddShader(ID_OCTANE_TRIPLANAR)
            self.AddConnectShader(shader, mysha, c4d.TRIPTEX_TEXTURE1)
        self.UniProjection(effectiveShaders, 6)

__all__ = [
    "MaterialHelper",
    "IsCoronaMaterial",
]