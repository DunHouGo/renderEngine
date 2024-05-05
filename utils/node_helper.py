# -*- coding: utf-8 -*-
import c4d
import maxon
import functools
import Renderer
from typing import Union, Optional, Any
from pprint import pprint
from Renderer.constants.common_id import *
import os, sys, json

# Custom Helper for get the "Converter Port" in trick.
class ConverterPorts:

    """
    data = {
        "Redshift.json" : {
            "com.redshift3d.redshift4c4d.nodes.core.texturesampler" : {
                "Name" : "Texture"
                "Input" : "None"
                "Output": "com.redshift3d.redshift4c4d.nodes.core.texturesampler.outcolor"
            }
            "com.redshift3d.redshift4c4d.nodes.core.texturesampler" : {
                "Name" : "Texture"
                "Input" : "com.redshift3d.redshift4c4d.nodes.core.triplanar.imagex"
                "Output": "com.redshift3d.redshift4c4d.nodes.core.triplanar.outcolor"
            }            
        }
    }
    """

    def __init__(self, nodespaceId: maxon.Id) -> None:

        self.nodespaceId: maxon.Id = nodespaceId

        FILEPATH, f = os.path.split(__file__)
        parent_dir = os.path.abspath(os.path.join(FILEPATH, os.pardir))

        if self.nodespaceId == RS_NODESPACE:
            self.dataPath = os.path.join(parent_dir, 'constants', "Redshift.json")
        if self.nodespaceId == AR_NODESPACE:
            self.dataPath = os.path.join(parent_dir, 'constants', "Arnold.json")

        if not os.path.exists(self.dataPath): 
            raise FileExistsError(f"the Convertor data is not exsit at {self.dataPath}")

    @staticmethod
    def InitRedshiftData() -> dict[dict[str]]:
        """
        Get the basic data, then save the date and modity it.
        This should be used if the data is missing or you want to customizd

        Returns:
            dict[dict[str]]: teh data we want
        """
        repo: maxon.AssetRepositoryRef = maxon.AssetInterface.GetUserPrefsRepository()
        if repo.IsNullValue():
            raise RuntimeError("Could not access the user preferences repository.")

        # latest version assets
        nodeTemplateDescriptions: list[maxon.AssetDescription] = repo.FindAssets(
            maxon.Id("net.maxon.node.assettype.nodetemplate"), maxon.Id(), maxon.Id(),
            maxon.ASSET_FIND_MODE.LATEST)

        allShaders: list[str] =  [
            str(item.GetId())  # asset ID.
            for item in nodeTemplateDescriptions
            if str(item.GetId()).startswith("com.redshift3d.redshift4c4d.")  # Only RS ones
        ]
            
        output = {}

        def _GetOutput(shader):
            out_ids = ['outcolor','output','out']

            for out in out_ids:
                port_id = f"{str(shader.GetValue('net.maxon.node.attribute.assetid'))[1:].split(',')[0]}.{out}"
                port: maxon.GraphNode = shader.GetOutputs().FindChild(port_id)
                if not port.IsNullValue():
                    return str(port.GetId())
            return ""

        def _GetInput(shader):
            out_ids = ['color','input','base_color', 
                       'tex0', 'albedo', 'texture',
                       'input1','x', 'default', 'attribute'
                       ]

            for out in out_ids:
                port_id = f"{str(shader.GetValue('net.maxon.node.attribute.assetid'))[1:].split(',')[0]}.{out}"
                port: maxon.GraphNode = shader.GetInputs().FindChild(port_id)
                if not port.IsNullValue():
                    return str(port.GetId())
            return ""

        rsNodeSpaceId: maxon.Id = maxon.Id(RS_NODESPACE)
        if c4d.GetActiveNodeSpaceId() != rsNodeSpaceId:
            raise RuntimeError("Make RS the active renderer and node space to run this script.")

        material: c4d.BaseMaterial = c4d.BaseMaterial(c4d.Mmaterial)
        if not material:
            raise MemoryError(f"{material = }")

        nodeMaterial: c4d.NodeMaterial = material.GetNodeMaterialReference()
        graph: maxon.NodesGraphModelInterface = nodeMaterial.CreateDefaultGraph(rsNodeSpaceId)

        with graph.BeginTransaction() as gt:
            for nodeId in allShaders:
                data = {}
                node = graph.AddChild(maxon.Id(), nodeId)
                data["input"] = str(_GetInput(node))
                data["output"] = str(_GetOutput(node))
                output[f"{str(node.GetValue('net.maxon.node.attribute.assetid'))[1:].split(',')[0]}"] = data

            gt.Commit()

        c4d.documents.GetActiveDocument().InsertMaterial(material)
        c4d.EventAdd()

        return output

    @staticmethod
    def InitArnoldData() -> dict[dict[str]]:
        """
        Get the basic data, then save the date and modity it.
        This should be used if the data is missing or you want to customizd
        
        Returns:
            dict[dict[str]]: teh data we want
        """
        repo: maxon.AssetRepositoryRef = maxon.AssetInterface.GetUserPrefsRepository()
        if repo.IsNullValue():
            raise RuntimeError("Could not access the user preferences repository.")

        # latest version assets
        nodeTemplateDescriptions: list[maxon.AssetDescription] = repo.FindAssets(
            maxon.Id("net.maxon.node.assettype.nodetemplate"), maxon.Id(), maxon.Id(),
            maxon.ASSET_FIND_MODE.LATEST)

        allShaders: list[str] =  [
            str(item.GetId())  # asset ID.
            for item in nodeTemplateDescriptions
            if str(item.GetId()).startswith("com.autodesk.arnold.")  # Only Arnold ones
        ]
        
        output = {}

        def _GetOutput(shader):
            out_ids = ['outcolor','output','out']

            for out in out_ids:
                port: maxon.GraphNode = shader.GetOutputs().FindChild(out)
                if not port.IsNullValue():
                    return str(port.GetId())
            return ""

        def _GetInput(shader):
            out_ids = ['color','input','base_color', 'filename',
                       'tex0', 'albedo', 'texture',
                       'input1','x', 'default', 'aov_name'
                       ]

            for out in out_ids:
                port: maxon.GraphNode = shader.GetInputs().FindChild(out)
                if not port.IsNullValue():
                    return str(port.GetId())
            return ""

        rsNodeSpaceId: maxon.Id = maxon.Id(AR_NODESPACE)
        if c4d.GetActiveNodeSpaceId() != rsNodeSpaceId:
            raise RuntimeError("Make RS the active renderer and node space to run this script.")

        material: c4d.BaseMaterial = c4d.BaseMaterial(c4d.Mmaterial)
        if not material:
            raise MemoryError(f"{material = }")

        nodeMaterial: c4d.NodeMaterial = material.GetNodeMaterialReference()
        graph: maxon.NodesGraphModelInterface = nodeMaterial.CreateDefaultGraph(rsNodeSpaceId)

        with graph.BeginTransaction() as gt:
            for nodeId in allShaders:
                data = {}
                node = graph.AddChild(maxon.Id(), nodeId)
                data["input"] = str(_GetInput(node))
                data["output"] = str(_GetOutput(node))
                output[f"{str(node.GetValue('net.maxon.node.attribute.assetid'))[1:].split(',')[0]}"] = data

            gt.Commit()

        c4d.documents.GetActiveDocument().InsertMaterial(material)
        c4d.EventAdd()

        return output

    ### Key methods ###

    def IsGeneratorNode(self, node: maxon.GraphNode) -> bool:
        """
        True if the node don't have a input data. so we call it generator.

        Args:
            node (maxon.GraphNode): the host node

        Returns:
            bool: True if the node don't have a input data.
        """
        if self.GetConvertInput(node) != "":
            return True
        return False

    def GetConvertInput(self, StrOrNode: Union[str, maxon.GraphNode]) -> str:
        """
        Get the default in port of the node.

        Args:
            StrOrNode (Union[str, maxon.GraphNode]): the node or it's string id.

        Returns:
            str: the string id of the default in port, else ""
        """
        if isinstance(StrOrNode, str):
            assetId = StrOrNode
        elif isinstance(StrOrNode, maxon.GraphNode):
            if StrOrNode.GetKind() == maxon.NODE_KIND.NODE:       
                assetId = str(StrOrNode.GetValue("net.maxon.node.attribute.assetid"))[1:].split(",")[0]

        with open(self.dataPath, 'r', encoding='UTF-8') as file:
            data: dict = json.loads(file.read())

        # data: dict = read_json(self.dataPath)
        item: dict =  data.get(assetId,"")
        return item.get("input","")
    
    def GetConvertOutput(self, StrOrNode: Union[str, maxon.GraphNode]) -> str:
        """
        Get the default out port of the node.

        Args:
            StrOrNode (Union[str, maxon.GraphNode]): the node or it's string id.

        Returns:
            str: the string id of the default out port, else ""
        """
        if isinstance(StrOrNode, str):
            assetId = StrOrNode
        elif isinstance(StrOrNode, maxon.GraphNode):
            if StrOrNode.GetKind() == maxon.NODE_KIND.NODE:       
                assetId = str(StrOrNode.GetValue("net.maxon.node.attribute.assetid"))[1:].split(",")[0]
        with open(self.dataPath, 'r', encoding='UTF-8') as file:
            data: dict = json.loads(file.read())
        #data: dict = read_json(self.dataPath)
        item: dict =  data.get(assetId,"")
        return item.get("output","")


# Custom Helper for New Node Materials Graph
class NodeGraghHelper:

    """
    Custom helper for NodeGragh Material in Cinema 4D Node Editor.
    Warp with maxon api and add some daliy functions.
    """

    #=============================================
    # Basic
    #=============================================

    def __init__(self, material: c4d.BaseMaterial):
        """
        A Custom NodeHelper for Node Material. Need a material to initalize the instance.

        Args:
            material (c4d.BaseMaterial): the BaseMaterial instance from the C4D document.

        """

        self._support_renderers: list = [
            "net.maxon.nodespace.standard",
            "com.autodesk.arnold.nodespace",
            "com.redshift3d.redshift4c4d.class.nodespace",
            "com.chaos.class.vray_node_renderer_nodespace"
        ]

        if not isinstance(material, c4d.BaseMaterial):
            raise ValueError("The material is not a valid BaseMaterial instance.")
        
        self.material: c4d.BaseMaterial = material

        if self.material:
            
            # get node material ref
            self.nodeMaterial: c4d.NodeMaterial = self.material.GetNodeMaterialReference()

            # check support node space
            for nid in self._support_renderers:
                if not self.nodeMaterial.HasSpace(nid):
                    continue
            # node
            self.nodespaceId: maxon.Id = c4d.GetActiveNodeSpaceId()
            if self.nodespaceId is None:
                raise ValueError("Cannot retrieve the NodeSpace.")
            
            self.nimbusRef: maxon.NimbusBaseRef = self.material.GetNimbusRef(self.nodespaceId)
            if self.nimbusRef is None:
                raise ValueError("Cannot retrieve the nimbus reference for that NodeSpace.")
            
            self.graph: maxon.GraphModelRef = self.nodeMaterial.GetGraph(self.nodespaceId)
            if self.graph.IsNullValue():
                raise ValueError("Cannot retrieve the graph of this nimbus NodeSpace.")
            
            self.root: maxon.GraphNode = self.graph.GetRoot()

    def __str__(self):
        return (f"A {self.__class__.__name__} Instance with Material : {self.material.GetName()}")

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
    
    #=============================================
    # Util
    #=============================================
    # 包装maxon数据转换，把数据强制转换为maxon数据类型
    def _ConvertData(self, data: Any) -> maxon.data:
        """
        Convert the data to maxon data type for safely.

        Args:
            data (Any): the data to convert

        Returns:
            maxon.data: the converted data
        """
        
        return maxon.MaxonConvert(data, maxon.CONVERSIONMODE.TOMAXON)

    # 获取资产ID 只有node有asset id ==> ok
    def GetAssetId(self, node: maxon.GraphNode) -> str:
        """
        Returns the asset id of the given node.

        Args:
            node (maxon.GraphNode): the shader node

        Returns:
            str: Asset id of the given node, only true node had asset id.

        Example:
            "com.redshift3d.redshift4c4d.nodes.core.standardmaterial"
        """
        if not isinstance(node, maxon.GraphNode) and node.GetKind() != maxon.NODE_KIND.NODE:
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a true node GraphNode, got {type(node)}')
        
        return str(node.GetValue("net.maxon.node.attribute.assetid"))[1:].split(",")[0]

    # 获取ShaderID ==> ok
    def GetShaderId(self, node: maxon.GraphNode) -> str:
        """
        Returns the node id(No prefix) of the given node.

        Args:
            node (maxon.GraphNode): the shader node

        Returns:
            str: the node id(No prefix) of the given node

        Example:
            "standardmaterial"
        """
        if not isinstance(node, maxon.GraphNode) and node.GetKind() != maxon.NODE_KIND.NODE:
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a true node GraphNode, got {type(node)}')
        
        # True node
        shaderId = self.GetAssetId(node).split('.')[-1]
        # Group node
        if not shaderId:
            shaderId = str(node.GetId()).split('@')[0]

        return shaderId

    # NOTE:获取节点名 ==> ok
    def GetName(self, node: maxon.GraphNode) -> Optional[str]:
        """
        Retrieve the displayed name of a node.

        Args:
            node (maxon.GraphNode): the node

        Returns:
            Optional[str]: the name of the ndoe
        """
        if not isinstance(node, maxon.GraphNode):#  or node.GetKind() != maxon.NODE_KIND.NODE:
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a node GraphNode, got {type(node)}')

        nodeName = node.GetValue(maxon.NODE.BASE.NAME)

        # 此函数在2024.4.0中可以返回正确的值
        # 在2024.2.0中返回None
        if nodeName is None:
            nodeName = node.GetValue(maxon.EffectiveName)

        if nodeName is None:
            nodeName = str(node)

        return nodeName

    # 设置节点名
    def SetName(self, node: maxon.GraphNode, name: str) -> bool:
        """
        Set the name of a node.

        Args:
            node (maxon.GraphNode): the node
            name (str): the name of the node

        Returns:
            bool: True if the name has been changed.
        """
        if not isinstance(node, maxon.GraphNode) and node.GetKind() != maxon.NODE_KIND.NODE:
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a true node GraphNode, got {type(node)}')

        # if not isinstance(name, str):
        #     raise ValueError('Expected a String, got {}'.format(type(name)))
        
        node.SetValue(maxon.NODE.BASE.NAME, self._ConvertData(str(name)))
        return True

    # 选择 ==> ok
    def Select(self, node: maxon.GraphNode) -> maxon.GraphNode:
        """
        Select a port or node.

        Args:
            node (maxon.GraphNode): the node to select

        Returns:
            maxon.GraphNode: the node self
        """
        if not isinstance(node, maxon.GraphNode):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a GraphNode, got {type(node)}')
        
        maxon.GraphModelHelper.SelectNode(node)
        return node

    # 取消选择 ==> ok
    def Deselect(self,node: maxon.GraphNode) -> maxon.GraphNode:
        """
        Deselect a port or node.

        Args:
            node (maxon.GraphNode): the node to deselect

        Returns:
            maxon.GraphNode: the node self
        """
        if not isinstance(node, maxon.GraphNode):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a GraphNode, got {type(node)}')

        maxon.GraphModelHelper.DeselectNode(node)
        return node

    # 获取Output Node ==> ok
    def GetOutput(self) -> maxon.GraphNode:
        """
        Returns the end node.

        Returns:
            maxon.GraphNode: the end node of this graph
        """
        # Retrieve the end node of this graph
        endNodePath = self.nimbusRef.GetPath(maxon.NIMBUS_PATH.MATERIALENDNODE)
        endNode = self.graph.GetNode(endNodePath)
        return endNode
    
    # 获取此节点空间默认纹理节点（节点数据） ==> ok
    def GetImageNodeID(self, include_portData: bool = False) -> Union[maxon.Id, tuple]:
        """
        Returns the image node id (and it's port data).
        Need to convert the NodePath to a string, this is a bug that is going to be fixed in 2024.2

        Returns:
            maxon.GraphNode: the image node id of this graph

        portData 
        .. code-block:: python
            portData = [
                outColorPortId = portData[0],      # The result port.
                inTexturePortId = portData[1],     # The URL of the input image.
                inStartFramePortId = portData[2],  # The index of the starting frame.
                inEndFramePortId = portData[3]     # The index of the ending frame.
                ]
        """
        # Retrieve the nodespace id from the graph
        spaceContext = self.root.GetValue(maxon.nodes.NODESPACE.NodeSpaceContext)
        nodeSpaceId = spaceContext.Get(maxon.nodes.NODESPACE.SPACEID)
        
        # Thanks Maxime!
        # Retrieve the nodespace data, and its default picture node with the associated port Id
        if c4d.GetC4DVersion() < 2024200:
            # --- Temporary add NodeSpaceHelpersInterface.GetNodeSpaceData() 
            # This is going to be added in 2024.2 as maxon.NodeSpaceHelpersInterface.GetNodeSpaceData() --------------------------
            @maxon.interface.MAXON_INTERFACE_NONVIRTUAL(maxon.consts.MAXON_REFERENCE_STATIC, "net.maxon.nodes.interface.nodespacehelpers")
            class NodeSpaceHelpersInterface:
                
                @staticmethod
                @maxon.interface.MAXON_STATICMETHOD("net.maxon.nodes.interface.nodespacehelpers.GetNodeSpaceData")
                def GetNodeSpaceData(spaceId):
                    pass
            # --- End of fix -----------------------------------------------------------------------------------
            
            spaceData = NodeSpaceHelpersInterface.GetNodeSpaceData(nodeSpaceId)

        else:
            spaceData = maxon.NodeSpaceHelpersInterface.GetNodeSpaceData(nodeSpaceId)

        assetId = spaceData.Get(maxon.nodes.NODESPACE.IMAGENODEASSETID)
        
        if include_portData:
            portData = spaceData.Get(maxon.nodes.NODESPACE.IMAGENODEPORTS)
            return (assetId, portData)
        return assetId

    # 切换预览 ==> ok
    def FoldPreview(self, nodes: list[maxon.GraphNode] ,state: bool = False) -> bool:
        """
        Toggle folding state of given nodes.

        Args:
            nodes (list[maxon.GraphNode]): the nodes list
            state (bool, optional): the folding state, False to hide preview. Defaults to False.

        Returns:
            bool: True if the state has been changed.
        """
        if isinstance(nodes, maxon.GraphNode):
            nodes = [nodes]
        for graph_node in nodes:
            graph_node.SetValue(maxon.NODE.BASE.DISPLAYPREVIEW  , maxon.Bool(state))
        return True

    # 获取属性 ==> ok
    def GetShaderValue(self, node: maxon.GraphNode, paramId: Union[maxon.Id,str]=None) -> maxon.Data:
        """
        Returns the value stored in the given shader parameter.

        Args:
            node (maxon.GraphNode): the node
            paramId (Union[maxon.Id,str], optional): the port id. Defaults to None.

        Returns:
            maxon.Data: the value assigned to this port
        """
        # standard data type
        port: maxon.GraphNode = self.GetPort(node,paramId)
        self.GetPortData(port)

    # 设置属性 ==> ok
    def SetShaderValue(self, node: maxon.GraphNode, paramId: Union[maxon.Id,str]=None, value=None) -> bool:
        """
        Sets the value stored in the given shader parameter.

        Args:
            node (maxon.GraphNode): the node
            paramId (Union[maxon.Id,str], optional): the port id. Defaults to None.
            value (_type_, optional): the value to set. Defaults to None.

        Returns:
            bool: True if the value has been changed.
        """

        port: maxon.GraphNode = self.GetPort(node,paramId)        
        return self.SetPortData(port, value)

    # 获取端口属性 ==> ok
    def GetPortData(self, port: maxon.GraphNode) -> any:
        """
        Gets the value to the given port.

        Args:
            node (maxon.GraphNode): the node

        Returns:
            bool: True if the value has been changed.
        """
        # standard data type
        if not self.IsPortValid(port):
            raise ValueError(f"Input {port} is not a valid port")

        if c4d.GetC4DVersion() >= 2024400:
            return port.GetPortValue()
            # "effectivename" is None when a wire filled into the port
        elif 2024000 <= c4d.GetC4DVersion() < 2024400:
            return port.GetValue("value")
        else:
            try:
                return port.GetValue("value")
            except:
                return port.GetDefaultValue()

    # 设置端口属性 ==> ok
    def SetPortData(self, port: maxon.GraphNode, value) -> bool:
        """
        Sets the value to the given port.

        Args:
            node (maxon.GraphNode): the node
            paramId (Union[maxon.Id,str], optional): the port id. Defaults to None.
            value (_type_, optional): the value to set. Defaults to None.

        Returns:
            bool: True if the value has been changed.
        """
        if not self.IsPortValid(port):
            raise ValueError(f"Input {port} is not a valid port")

        return port.SetValue("net.maxon.description.data.base.defaultvalue", self._ConvertData(value))

        # if c4d.GetC4DVersion() >= 2024400:
        #     return port.SetPortValue(maxon_value)
        
        # return port.SetDefaultValue(maxon_value)

    # 获取所有Shader ==> ok
    def GetAllShaders(self, mask: Union[str,maxon.Id] = None) -> list[maxon.GraphNode]:
        """
        Get all shaders from the graph. can filter by a mask.

        Args:
            mask (Union[str,maxon.Id], optional): String filter to get specific nodes. Defaults to None.

        Returns:
            list[maxon.GraphNode]: list of nodes
        """
        shaders_list: list = []
        
        # 创建shader list
        def _IterGraghNode(node, shaders_list: list):

            if node.GetKind() != maxon.NODE_KIND.NODE:
                return

            if self.GetAssetId(node) == "net.maxon.node.group":
                for node in self.root.GetChildren():
                    _IterGraghNode(node, shaders_list)
                return
            
            if mask:
                if self.GetAssetId(node) == mask or self.GetShaderId(node) == mask:
                    shaders_list.append(node)
            else:
                shaders_list.append(node)
            
        #root = self.graph.GetRoot()
        
        for node in self.root.GetChildren():   
            _IterGraghNode(node, shaders_list) 
            
        return shaders_list

    # New 节点或者端口是否被链接 ==> ok
    def IsConnected(self, NodeorPort: maxon.GraphNode, port: Union[maxon.GraphNode,str] = None) -> bool:
        """Check if a node or a port is connected.

        Args:
            NodeorPort (maxon.GraphNode, optional): Node or port to check. Defaults to None.
            port (Union[maxon.GraphNode,str], optional): Port to check. Defaults to None.

        Returns:
            bool: True if connected, False otherwise.
        """
        # only first #arg
        if isinstance(NodeorPort, maxon.GraphNode) and port is None:
            if self.IsNodeConnected(NodeorPort) or self.IsPortConnected(NodeorPort):
                return True
            return False
        
        # both #args filled
        else:            
            if isinstance(NodeorPort,maxon.GraphNode) and isinstance(port,maxon.GraphNode):
                # this will crash if port is None
                return maxon.GraphModelHelper.IsConnected(NodeorPort,port)
            return False
        return False

    # New 移除独立节点 ==> ok
    def RemoveIsolateNodes(self, filterId: str = None) -> None:
        """
        Remove all the isolate shaders(not connected to any ports or nodes),filled filter to only apply to specfic asset id.

        Args:
            filterId (str, optional): the asset id of the nodes to apply. Defaults to None.
        """
        for node in self.GetAllShaders():
            if not self.IsNodeConnected(node):
                if filterId:
                    if self.GetAssetId(node) == filterId and self.GetShaderId(node) != "scaffold":
                        node.Remove()
                else:
                    node.Remove()

    # New 备注节点 ==> ok
    def Scaffold(self, node_list: list[maxon.GraphNode], name: str = "Scaffold") -> maxon.GraphNode:
        """
        Create a scaffold node with the given nodes.

        Args:
            node_list (list[maxon.GraphNode]): the list of nodes to use as inputs.
            name (str, optional): the name of the scaffold node. Defaults to "Scaffold".

        Returns:
            maxon.GraphNode: the created scaffold node.
        """
        if not isinstance(node_list, list):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a list of true node GraphNodes, got {type(node)}')
        
        scaffold_node = self.AddShader("net.maxon.node.scaffold")
        self.SetName(scaffold_node, name)
        for node in node_list:
            node.SetValue("net.maxon.node.attribute.scaffoldid", scaffold_node.GetId())
        return scaffold_node

    # New 是否为组 ==> ok
    def IsGroup(self, node: maxon.GraphNode) -> bool:

        if not isinstance(node, maxon.GraphNode):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a true node GraphNodes, got {type(node)}')

        return node.GetValue("isgroup")
    
    # New 是不是生成类节点:没有默认的输入端
    def IsGeneratorNode(self, node: maxon.GraphNode) -> bool:
        """
        True if the node don't have a input data. so we call it generator.

        Args:
            node (maxon.GraphNode): the host node

        Returns:
            bool: True if the node don't have a input data.
        """
        return ConverterPorts(self.nodespaceId).IsGeneratorNode(node)
    
    # New 获取默认输入端口
    def GetConvertInput(self, node: maxon.GraphNode) -> Optional[str]:
        """
        Get the Convert port of a node, this is a custom solution in python, only used to get "defaut" port.

        Args:
            node (maxon.GraphNode): the host node.

        Returns:
            str: the id of the port, or None
        """
        res = ConverterPorts(self.nodespaceId).GetConvertInput(node)
        return res if res != "" else None
    
    # New 获取默认输出端口
    def GetConvertOutput(self, node: maxon.GraphNode) -> Optional[str]:
        """
        Get the Convert port of a node, this is a custom solution in python, only used to get "defaut" port.

        Args:
            node (maxon.GraphNode): the host node.

        Returns:
            str: the id of the port, or None
        """
        res = ConverterPorts(self.nodespaceId).GetConvertOutput(node)
        return res if res != "" else None

    #=============================================
    # Node
    #=============================================~~

    # 当前NodeSpace下所有可用的shader ==> ok
    
    def GetAvailableShaders(self) -> list[maxon.Id]:
        """
        Get all available node assets for active nodespace
        
        ----------

        :return: list of all available shader node.
        :rtype: maxon.GraphNode
        
        """
        repo: maxon.AssetRepositoryRef = maxon.AssetInterface.GetUserPrefsRepository()
        if repo.IsNullValue():
            raise RuntimeError("Could not access the user preferences repository.")

        # latest version assets
        nodeTemplateDescriptions: list[maxon.AssetDescription] = repo.FindAssets(
            maxon.Id("net.maxon.node.assettype.nodetemplate"), maxon.Id(), maxon.Id(),
            maxon.ASSET_FIND_MODE.LATEST)

        if self.nodespaceId == RS_NODESPACE:
            return [
                item.GetId()  # asset ID.
                for item in nodeTemplateDescriptions
                if str(item.GetId()).startswith("com.redshift3d.redshift4c4d.")  # Only RS ones
            ]
            
        elif self.nodespaceId == AR_NODESPACE:
            return [
                item.GetId()  # asset ID.
                for item in nodeTemplateDescriptions
                if str(item.GetId()).startswith("com.autodesk.arnold.")  # Only AR ones
            ]

    # 选择的节点 ==> ok
    def GetActiveNodes(self, single_mode: bool = True, callback: callable = None) -> Union[maxon.GraphNode, list[maxon.GraphNode]]:
        """
        Gets the selected nodes, return a list of them.

        Args:
            sigle_mode (bool): True to anble if only one node selected,return the node but not the list.
            callback (callable, optional): A callback, had a ``maxon.GraphNode`` argument. Defaults to None.

        Returns:
            Union[maxon.GraphNode, list[maxon.GraphNode]]: the list of selected nodes.
        """
        
        if callback:
            with self.graph.BeginTransaction() as transaction:
                result =  maxon.GraphModelHelper.GetSelectedNodes(self.graph, maxon.NODE_KIND.NODE, callback)
                transaction.Commit()            
        
        else:
            result = maxon.GraphModelHelper.GetSelectedNodes(self.graph, maxon.NODE_KIND.NODE)
        
        if single_mode:
            if len(result) == 1:
                return result[0]
        return result

    # 创建Shader ==> ok
    def AddShader(self, nodeId: Union[str, maxon.Id]) -> maxon.GraphNode:
        """
        Adds a new shader to the graph.

        Args:
            nodeId (Union[str, maxon.Id]): shader id

        Returns:
            maxon.GraphNode: the shader we added.
        """
        return self.graph.AddChild(childId=maxon.Id(), nodeId=nodeId, args=maxon.DataDictionary())
    
    # 创建Shader 可以提供链接 ==> ok
    def AddConnectShader(self, nodeID: Union[str, maxon.Id] = None, 
                input_ports: list[Union[str,maxon.GraphNode]] = None, connect_inNodes: list[maxon.GraphNode] = None,
                output_ports: list[Union[str,maxon.GraphNode]] = None, connect_outNodes: list[maxon.GraphNode] = None,
                remove_wires: bool = True
                ) -> Optional[maxon.GraphNode] :
        """
        Add shader and connect with given ports and nodes.

        Args:
            nodeID (Union[str, maxon.Id], optional): the shader id. Defaults to None.
            input_ports (list[Union[str,maxon.GraphNode]], optional): the input port list. Defaults to None.
            connect_inNodes (list[maxon.GraphNode], optional): the node list connect to inputs. Defaults to None.
            output_ports (list[Union[str,maxon.GraphNode]], optional): the output port list. Defaults to None.
            connect_outNodes (list[maxon.GraphNode], optional): the node list connect to outputs. Defaults to None.
            remove_wires (bool, optional): True to remove all original wires. Defaults to True.

        Returns:
            Optional[maxon.GraphNode]: the node we added.
        """
      
        shader: maxon.GraphNode = self.AddShader(nodeID)
        
        # progress the ports data        
        if (isinstance(input_ports,maxon.GraphNode) or isinstance(input_ports,str)) and not isinstance(input_ports,list):
            input_ports = [input_ports]
        elif input_ports is None:
            input_ports = []


        if (isinstance(output_ports,maxon.GraphNode) or isinstance(output_ports,str)) and not isinstance(output_ports,list):
            output_ports = [output_ports]
        elif output_ports is None:
            output_ports = []

        if isinstance(connect_inNodes,maxon.GraphNode) and not isinstance(connect_inNodes,list):
            connect_inNodes = [connect_inNodes]
        elif connect_inNodes is None:
            connect_inNodes = []


        if isinstance(connect_outNodes,maxon.GraphNode) and not isinstance(connect_outNodes,list):
            connect_outNodes = [connect_outNodes]
        elif connect_outNodes is None:
            connect_outNodes = []

        # remove original wires connected to the ports
        if remove_wires:
            try:
                # todo
                ports: list[maxon.GraphNode] = input_ports + output_ports + connect_inNodes + connect_outNodes
                for port in ports:
                    if port is not None:
                        self.RemoveConnection(port)
            # except Exception as error:
            #     print(f"AddConnectShader {error = }")
            finally:
                pass

        # connect with ports data
        if input_ports is not None:
            if connect_inNodes is not None:
                if len(connect_inNodes) > len(input_ports):
                    raise ValueError(f'{sys._getframe().f_code.co_name} Error: Port nodes can not bigger than input port.')
                if len(input_ports) > len(connect_inNodes):
                    input_ports = input_ports[:len(connect_inNodes)]
                for i, input_port in enumerate(input_ports):
                    input: maxon.GraphNode = self.GetPort(shader,input_port)
                    connect_inNodes[i].Connect(input)
        
        if output_ports is not None:
            if connect_outNodes is not None:
                if len(connect_outNodes) > len(output_ports):
                    raise ValueError(f'{sys._getframe().f_code.co_name} Error: Port nodes can not bigger than output port.')
                if len(output_ports) > len(connect_outNodes):
                    output_ports = output_ports[:len(connect_outNodes)]
                for i, output_port in enumerate(output_ports):
                    output: maxon.GraphNode = self.GetPort(shader,output_port)
                    output.Connect(connect_outNodes[i])

        return shader

    # 在Wire中插入Shader （New） ==> ok
    def InsertShader(self, nodeID: Union[str,maxon.Id], wireData: Union[maxon.Wires, list[maxon.GraphNode]], 
                     input_port: list[Union[str,maxon.GraphNode]],
                     output_port: list[Union[str,maxon.GraphNode]]) -> Optional[maxon.GraphNode]:
        """
        Insert a shder into a wire, and keep connect.

        Args:
            nodeID (Union[str,maxon.Id]): the node id
            wireData (list[maxon.GraphNode,maxon.Wires]): a wire or a data bundle with a list a ``in`` and ``out`` port
            input_port (list[Union[str,maxon.GraphNode]]): the input port of the insert node
            output_port (list[Union[str,maxon.GraphNode]]): the output port of the insert node

        Returns:
            Optional[maxon.GraphNode]: the node we added.
        """
        if not wireData:
            wireData: list[maxon.GraphNode,maxon.Wires] = self.GetActiveWires() # last select wire

        pre_port: maxon.GraphNode = wireData[0]
        if not self.IsPort(pre_port):
            raise ValueError(f'{sys._getframe().f_code.co_name} wireData Error: cannot get a out-port form wireData')
        next_port: maxon.GraphNode = wireData[1]
        if not self.IsPort(next_port):
            raise ValueError(f'{sys._getframe().f_code.co_name} wireData Error: cannot get a in-port form wireData')
        
        # remove wire
        if isinstance(pre_port, maxon.GraphNode) or isinstance(next_port, maxon.GraphNode):
            self.RemoveConnection(next_port,pre_port)

        # add our new shader and wires
        return self.AddConnectShader(nodeID,input_port,pre_port,output_port,next_port)

    # 删除Shader ==> ok
    def RemoveShader(self, shader: maxon.GraphNode, keep_wire: bool = True) -> bool:
        """
        Removes the given shader from the graph.

        Args:
            shader (maxon.GraphNode): the shader to remove
            keep_wire (bool, optional): True to keep the wire across this shader. Defaults to True.

        Returns:
            _type_: True to keep loop
        """
        if not isinstance(shader, maxon.GraphNode):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a true node GraphNode, got {type(shader)}')
        
        if not keep_wire:
            shader.Remove()
            return True
        
        else:
            before = []
            after = []
            self.GetNextNodePorts(shader, result=after, stop=True)
            self.GetPreNodePorts(shader, result=before, stop=True)
            if before:
                if len(before) != len(after):
                    input_port: maxon.GraphNode = before[0][0]
                    output_port: maxon.GraphNode = after[0][1]
                    shader.Remove()
                    input_port.Connect(output_port)
                    # print(f"The {shader} has a different number of input and output ports, only keep first wire")
                else:
                    for i in range(len(after)):
                        input_port: maxon.GraphNode = before[i][0]
                        output_port: maxon.GraphNode = after[i][1]
                        shader.Remove()
                        input_port.Connect(output_port)
            else:
                shader.Remove()

        return True

    # 是否是shader ==> ok
    def IsNode(self, node: maxon.GraphNode) -> bool:
        """
        Check if a true node is a valid node.

        Args:
            node (maxon.GraphNode): the node to check

        Returns:
            bool: True if node is a valid True node
        """
        if not isinstance(node,maxon.GraphNode) :
            return False
        if node.GetKind() == maxon.NODE_KIND.NODE and node.IsValid():
            return True
        return False

    # 获取节点  ==> ok
    def GetNodes(self, shader: Union[maxon.GraphNode, str]) -> list[maxon.GraphNode]:
        """
        Get all Nodes of given shader.

        Args:
            shader (Union[maxon.GraphNode, str]): the shaders id or the shader node,this will convert the node to id

        Returns:
            list[maxon.GraphNode]: the shader list we got.
        """

        if not shader:
            raise ValueError(f'Expected a maxon.GraphNode, got {type(shader)}')
        
        result: list[maxon.GraphNode] = []
        
        if isinstance(shader, maxon.GraphNode):
            asset_id = self.GetAssetId(shader)
            
        if isinstance(shader, str):
            asset_id = shader

        maxon.GraphModelHelper.FindNodesByAssetId(self.graph, asset_id, True, result)
        return result

    # New 获取前方节点(只包含子节点)  ==> ok
    def GetPreNode(self, node: maxon.GraphNode) -> list[maxon.GraphNode]:
        """
        Return the nodes directly connected before the node.

        Args:
            node (maxon.GraphNode): the node

        Returns:
            list[maxon.GraphNode]: Return the nodes directly connected before the node.
        """
        result = list()
        maxon.GraphModelHelper.GetDirectPredecessors(node, maxon.NODE_KIND.NODE, result)
        return result

    # New 获取后方节点(只包含子节点)  ==> ok
    def GetNextNode(self, node: maxon.GraphNode) -> list[maxon.GraphNode]:
        """
        Return the nodes directly connected after the node.

        Args:
            node (maxon.GraphNode): the node

        Returns:
            list[maxon.GraphNode]: Return the nodes directly connected after the node.
        """
        result = list()
        maxon.GraphModelHelper.GetDirectSuccessors(node, maxon.NODE_KIND.NODE, result)
        return result

    # New 获取前方节点树(包含节点树)  ==> ok
    def GetPreNodes(self, node: maxon.GraphNode, result: list, filter_asset: str = None) -> list:
        """
        Return the nodes connected before the node, include all the node chain.

        Args:
            node (maxon.GraphNode): the node
            result (list): the list we will add return nodes to
            filter_asset (str): the asset id we will keep, fill none to disable.

        Returns:
            list[maxon.GraphNode]: Return the nodes connected before the node, include all the node chain.
        """
        # Bail when the passed node is not a true node.
        if node.GetKind() != maxon.NODE_KIND.NODE:
            return
        
        for inPort in node.GetInputs().GetChildren():
            # Get the connected output ports and their wires.
            for outPort, wires in inPort.GetConnections(maxon.PORT_DIR.INPUT, None, maxon.Wires.All(), maxon.WIRE_MODE.ALL):
                pre_node: maxon.GraphNode = self.GetTrueNode(outPort)
                if filter_asset is not None:
                    if self.GetAssetId(pre_node) == filter_asset and pre_node not in result:
                        result.append(pre_node)
                else:
                    if pre_node not in result:
                        result.append(pre_node)

                self.GetPreNodes(pre_node,result,filter_asset)
        
    # New 获取后方节点树(包含节点树)  ==> ok
    def GetNextNodes(self, node: maxon.GraphNode, result: list, filter_asset: str = None) -> list:
        """
        Return the nodes connected after the node, include all the node chain.

        Args:
            node (maxon.GraphNode): the node
            result (list): the list we will add return nodes to
            filter_asset (str): the asset id we will keep, fill none to disable.

        Returns:
            list[maxon.GraphNode]: Return the nodes connected after the node, include all the node chain.
        """
        # Bail when the passed node is not a true node.
        if node.GetKind() != maxon.NODE_KIND.NODE:
            return
        
        for outPort in node.GetOutputs().GetChildren():
            # Get the connected output ports and their wires.
            for outPort, wires in outPort.GetConnections(maxon.PORT_DIR.OUTPUT, None, maxon.Wires.All(), maxon.WIRE_MODE.ALL):
                pre_node: maxon.GraphNode = self.GetTrueNode(outPort)
                if filter_asset is not None:
                    if self.GetAssetId(pre_node) == filter_asset and pre_node not in result:
                        result.append(pre_node)
                else:
                    if pre_node not in result:
                        result.append(pre_node)

                self.GetNextNodes(pre_node,result,filter_asset)

    # New 判断节点是否连接  ==> ok
    def IsNodeConnected(self, node: maxon.GraphNode) -> bool:
        """
        Check if the node is connect to another port.

        Args:
            node (maxon.GraphNode): the node to check

        Returns:
            bool: True if the node is connected.
        """
        if not self.IsNode(node):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a true node GraphNode, got {type(node)}')
        
        all_ports = self.GetAllConnectedPorts(node)

        for the_port in all_ports:
            if maxon.GraphModelHelper.IsConnected(node, the_port):
                return True
        return False
  

    #=============================================
    # Port
    #=============================================

    # New 获取端口名 ==> ok
    # NOTE: 2024.4.0 此函数返回了接口的真正名称（Maxon.String），也就是节点编辑器中的显示名称
    def GetPortName(self, port: maxon.GraphNode) -> Union[str, maxon.String]:
        """
        Get the name of the port

        Args:
            port (maxon.GraphNode): the port

        Returns:
            str: The name string of this port
        """
        if not self.IsPort(port):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a port, got {type(port)}')
        
        return self.GetName(port).split(".")[-1]
    
    # New 获取端口名称 ==> ok
    # NOTE: 此函数返回的是端口id的名称(最后一个分段)，用于比对更加准确
    def GetPortRealName(self, port: maxon.GraphNode) -> str:
        """
        Get the real name of the port.

        Args:
            port (maxon.GraphNode): the port

        Returns:
            str: The id string of this port
        """
        if not self.IsPort(port):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a port, got {type(port)}')
        
        return str(port.GetId()).split(".")[-1]

    # 选择的端口 ==> ok
    def GetActivePorts(self, single_mode: bool = True, callback: callable = None) -> Union[maxon.GraphNode, list[maxon.GraphNode]]:
        """
        Gets the selected ports, return a list of them.

        Args:
            sigle_mode (bool): True to anble if only one node selected,return the node but not the list.
            callback (callable, optional): A callback, had a ``maxon.GraphNode`` argument. Defaults to None.

        Returns:
            Union[maxon.GraphNode, list[maxon.GraphNode]]: the list of selected ports.
        """
        if callback:
            with self.graph.BeginTransaction() as transaction:
                result =  maxon.GraphModelHelper.GetSelectedNodes(self.graph, maxon.NODE_KIND.PORT_MASK, callback)
                transaction.Commit()
        else:        
            result = maxon.GraphModelHelper.GetSelectedNodes(self.graph, maxon.NODE_KIND.PORT_MASK, callback)

        if single_mode:
            if len(result) == 1:
                return result[0]
        return result
    
    # NEW 新建（暴露端口） ==> ok
    def AddPort(self, node: maxon.GraphNode, port :Union[str, maxon.GraphNode] = None) -> maxon.GraphNode:
        """
        Add a 'true' port in the gragh ui. Need under a transaction.

        Args:
            node (maxon.GraphNode): the node to add port on it
            port (Union[str, maxon.GraphNode]): the port id

        Returns:
            maxon.GraphNode: the port itself
        """
        if not isinstance(node, maxon.GraphNode) and node.GetKind() != maxon.NODE_KIND.NODE:
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a true node GraphNode, got {type(node)}')

        if isinstance(port, str):
            true_port = self.GetPort(node, port)
        if isinstance(port, maxon.GraphNode):
            true_port = port
        
        true_port.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(False))
        return true_port

    # NEW 新建组入端  ==> ok
    def AddGroupInPort(self, node: maxon.GraphNode, portName: str, portId :Union[str, maxon.GraphNode] = None) -> maxon.GraphNode:
        """
        Add input port to a group node, it can automaticlly add id from the node name and port name.

        Args:
            node (maxon.GraphNode): the group node
            portName (str): the input port name
            portId (Union[str, maxon.GraphNode], optional): the port id. Fill None to use auto id.

        Returns:
            maxon.GraphNode: the input port we added.
        """
        # 组
        if self.GetAssetId(node) == "group":
            if not portId:
                portId = f"{self.GetName(node)}]_input_{str(portName)}"
            true_port = maxon.GraphModelHelper.CreateInputPort(node, portId, portName)
        return true_port
    
    # NEW 新建组出端  ==> ok
    def AddGroupOutPort(self, node: maxon.GraphNode, portName: str, portId :Union[str, maxon.GraphNode] = None) -> maxon.GraphNode:
        """
        Add output port to a group node, it can automaticlly add id from the node name and port name.

        Args:
            node (maxon.GraphNode): the group node
            portName (str): the output port name
            portId (Union[str, maxon.GraphNode], optional): the port id. Fill None to use auto id.

        Returns:
            maxon.GraphNode: the output port we added.
        """
        # 组
        if self.GetAssetId(node) == "group":
            if not portId:
                portId = f"{self.GetName(node)}]_output_{str(portName)}"
            true_port = maxon.GraphModelHelper.CreateOutputPort(node, portId, portName)
        return true_port

    # NEW 删除（隐藏端口） ==> ok
    def RemovePort(self, node: maxon.GraphNode, port :Union[str, maxon.GraphNode], Hide: bool = True) -> maxon.GraphNode:
        """
        Hide or remove a 'true' port in the gragh ui. 

        Args:
            node (maxon.GraphNode): the node to add port on it
            port (Union[str, maxon.GraphNode]): the port id
            Hide (bool) : True to hide the port, Flase to remove it(only group)

        Returns:
            maxon.GraphNode: the port itself
        """
        if not isinstance(node, maxon.GraphNode):
            raise ValueError("Node is not a True Node")
        
        # 组
        if self.GetAssetId(node) == "group":
            # find port
            for port in node.GetOutputs().GetChildren():
                if str(port) == self.GetName(port):
                    true_port = port
                    break
            if Hide:
                true_port.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(True))
            else:
                true_port.Remove()
        # True Node
        else:
            if isinstance(port, str):
                true_port = self.GetPort(node, port)
            if isinstance(port, maxon.GraphNode):
                true_port = port

            true_port.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(True))

        return true_port
 
    # 获取节点上端口 ==> ok
    def GetPort(self, shader: maxon.GraphNode, port_id :str = None) -> Union[maxon.GraphNode,bool]:
        """
        Get a port from a Shader node.if port id is None,try to find out port.

        Args:
            shader (maxon.GraphNode): the host shader
            port_id (str, optional): the port id, fill none try to get the output port.

        Returns:
            Union[maxon.GraphNode,bool]: the port we get.
        """
        if not shader:
            raise ValueError(f'Expected a maxon.GraphNode, got {type(shader)}')
        
        out_ids = ['outcolor','output','out']
         
        if self.nodespaceId == RS_NODESPACE:
            if port_id == None:
                for out in out_ids:
                    port_id = f"{self.GetAssetId(shader)}.{out}"
                    port: maxon.GraphNode = shader.GetInputs().FindChild(port_id)
                    if port.IsNullValue():
                        port = shader.GetOutputs().FindChild(port_id)
                    if not port.IsNullValue():
                        return port
            else:
                port: maxon.GraphNode = shader.GetInputs().FindChild(port_id)
                if port.IsNullValue():
                    port = shader.GetOutputs().FindChild(port_id)
                    if port.IsNullValue():
                        return False
            return port
        
        if self.nodespaceId == AR_NODESPACE:
            if port_id == None:
                for out in out_ids:                               
                    port: maxon.GraphNode = shader.GetInputs().FindChild(out)
                    if port.IsNullValue():
                        port = shader.GetOutputs().FindChild(out)
                    if not port.IsNullValue():
                        return port
            else:
                port: maxon.GraphNode = shader.GetInputs().FindChild(port_id)
                if port.IsNullValue():
                    port = shader.GetOutputs().FindChild(port_id)
                    if port.IsNullValue():
                        return False
            return port
        else:
            port: maxon.GraphNode = shader.GetInputs().FindChild(port_id)
            if port.IsNullValue():
                port = shader.GetOutputs().FindChild(port_id)
                if port.IsNullValue():
                    return False
            return port


    # 获取端口所在节点 ==> ok
    def GetTrueNode(self, port: maxon.GraphNode) -> maxon.GraphNode:
        """
        Get the actually node host the given port.

        Args:
            port (maxon.GraphNode): the port to test

        Returns:
            maxon.GraphNode: the host true node.
        """

        if not self.IsPort(port):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a port, got {type(port)}')

        return port.GetAncestor(maxon.NODE_KIND.NODE)
    
    # 端口合法 ==> ok
    def IsPortValid(self, port: maxon.GraphNode) -> bool:
        """
        Checks if the port is valid.

        Args:
            port (maxon.GraphNode): the port to test.

        Returns:
            bool: True if the node is valid.
        """
        try:
            if self.IsPort(port):
                return port.IsValid()
            return False
        except Exception as e:
            return False

    # New 是否是端口 ==> ok
    def IsPort(self, port: maxon.GraphNode) -> bool:
        """
        Checks if the maxon.GraphNode is a port.

        Args:
            port (maxon.GraphNode): the port to test.

        Returns:
            bool: True if the maxon.GraphNode is port.
        """
        if not isinstance(port,maxon.GraphNode) :
            return False
        if (port.GetKind() == maxon.NODE_KIND.INPORT or port.GetKind() == maxon.NODE_KIND.OUTPORT) and port.IsValid():
            return True
        return False
    
    # NEW @ 2024.4.8 ==> ok
    def IsOutPort(self, port: maxon.GraphNode, only_port: bool = True) -> bool:
        """
        Check is a port is a out port or out(include out list)

        Args:
            port (maxon.GraphNode): the port the check
            only_port (bool, optional): if set True, only outport will return trye. Defaults to True.

        Returns:
            bool: True if the node is a output port or a output list
        """
        if not isinstance(port, maxon.GraphNode):
            raise TypeError("Kind should be a maxon.GraphNode")
        if only_port:
            condition = maxon.NODE_KIND.OUTPORT
        else:
            condition = maxon.NODE_KIND.OUT_MASK
        return port.GetKind() == condition

    # NEW @ 2024.4.8 ==> ok
    def IsInputPort(self, port: maxon.GraphNode, only_port: bool = True) -> bool:
        """
        Check is a port is a input port or out(include out list)

        Args:
            port (maxon.GraphNode): the port the check
            only_port (bool, optional): if set True, only input will return trye. Defaults to True.

        Returns:
            bool: True if the node is a input port or a input list
        """
        if not isinstance(port, maxon.GraphNode):
            raise TypeError("Kind should be a maxon.GraphNode")
        if only_port:
            condition = maxon.NODE_KIND.INPORT
        else:
            condition = maxon.NODE_KIND.IN_MASK
        return port.GetKind() == condition

    # New 端口是否在同一个节点  ==> ok
    def OnSameNode(self, port_1: maxon.GraphNode ,port_2: maxon.GraphNode) -> bool:
        """
        Checks if the two ports are on the same node.

        Args:
            port_1 (maxon.GraphNode): the first port.
            port_2 (maxon.GraphNode): the second port.

        Returns:
            bool: True if the two ports are on the same node.
        """
        if not self.IsPort(port_1) or not self.IsPort(port_2):
            return False
        if self.GetTrueNode(port_1) == self.GetTrueNode(port_2):
            return True
        return False

    # New 获取所有被连接的端口 ==> ok
    def GetAllConnectedPorts(self, except_node: maxon.GraphNode = None) -> list[maxon.GraphNode]:
        """
        Get all ports with something connected, if except_node is passed,
        the port on the except_node will be except.

        Args:
            except_node (maxon.GraphNode, optional): the bypass node. Defaults to None.

        Returns:
            list[maxon.GraphNode]: List of all connected ports.
        """
        all_ports = []
        wires = self.GetAllConnections()
        for wire in wires:
            if except_node:
                if not self.GetTrueNode(wire[1]) == except_node:
                    all_ports.append(wire[1])
                if not self.GetTrueNode(wire[-1]) == except_node:
                    all_ports.append(wire[-1])
            else:
                all_ports.append(wire[1])
                all_ports.append(wire[-1])
        return all_ports

    # New 端口是否连接  ==> ok
    def IsPortConnected(self, port: maxon.GraphNode) -> bool:
        """
        Check if the port is connected.

        Args:
            port (maxon.GraphNode): The port to check.

        Returns:
            bool: True if the port is connected, False otherwise.
        """

        if not self.IsPort(port):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a port, got {type(port)}')
        
        all_ports = []
        wirs = self.GetAllConnections()
        for wir in wirs:
            if not self.OnSameNode(port, wir[1]):
                all_ports.append(wir[1])
            if not self.OnSameNode(port, wir[-1]):
                all_ports.append(wir[-1])

        # check connect
        for the_port in all_ports:
            if maxon.GraphModelHelper.IsConnected(port, the_port):
                return True
        return False

    # New 获取前面节点（们）的端口  ==> ok
    def GetPreNodePorts(self, node: maxon.GraphNode, result: list, stop: bool = True) -> Union[list[maxon.GraphNode],None]:
        """
        Get all the ports of the previous node.

        Args:
            node (maxon.GraphNode): The node to get the ports from.
            result (list): The list to store the ports in.
            stop (bool, optional): If True, the function will stop at the first node. Defaults to True.

        Returns:
            Union[list[maxon.GraphNode],None]: The list of ports or None if the node is not connected.
        """
        # Bail when the passed node is not a true node.
        if node.GetKind() != maxon.NODE_KIND.NODE:
            return

        for inPort in node.GetInputs().GetChildren():
            # Get the connected output ports and their wires.
            for outPort, wires in inPort.GetConnections(maxon.PORT_DIR.INPUT, None, maxon.Wires.All(), maxon.WIRE_MODE.ALL):
                if not stop:
                    otherNode: maxon.GraphNode = self.GetTrueNode(outPort)
                result.append((outPort, inPort))
                if not stop:
                    self.GetPreNodePorts(otherNode,result,stop)

    # New 获取前方连接端口  ==> ok
    def GetConnectedPortsBefore(self, node: maxon.GraphNode) -> Union[list[maxon.GraphNode],None]:
        """
        Get the connected port of the previous node.

        Args:
            node (maxon.GraphNode): The node to get the ports from.

        Returns:
            Union[list[maxon.GraphNode],None]: The list of ports [out -> in]
        """
        # Bail when the passed node is not a true node.
        if node.GetKind() != maxon.NODE_KIND.NODE:
            raise ValueError(f'Expected a maxon.GraphNode, got {type(node)}')
        
        for inPort in node.GetInputs().GetChildren():
            # Get the connected output ports and their wires.
            for outPort, wires in inPort.GetConnections(maxon.PORT_DIR.INPUT, None, maxon.Wires.All(), maxon.WIRE_MODE.ALL):
                return [outPort, inPort]

    # New 获取后面节点（们）的端口  ==> ok
    def GetNextNodePorts(self, node: maxon.GraphNode, result: list, stop: bool = True) -> Union[list[maxon.GraphNode],None]:
        """
        Get all the ports of the next node.

        Args:
            node (maxon.GraphNode): The node to get the ports from.
            result (list): The list to store the ports in.
            stop (bool, optional): If True, the function will stop at the first node. Defaults to True.

        Returns:
            Union[list[maxon.GraphNode],None]: The list of ports or None if the node is not connected.
        """
        # Bail when the passed node is not a true node.
        if node.GetKind() != maxon.NODE_KIND.NODE:
            return

        for inPort in node.GetOutputs().GetChildren():
            # Get the connected output ports and their wires.
            for outPort, wires in inPort.GetConnections(maxon.PORT_DIR.OUTPUT, None, maxon.Wires.All(), maxon.WIRE_MODE.ALL):
                if not stop:
                    otherNode: maxon.GraphNode = self.GetTrueNode(outPort)
                result.append((inPort, outPort))
                if not stop:
                    self.GetNextNodePorts(otherNode,result, stop)

    # New 获取后方连接端口  ==> ok
    def GetConnectedPortsAfter(self, node: maxon.GraphNode) -> Union[list[maxon.GraphNode],None]:
        """
        Get the connected port of the next node.

        Args:
            node (maxon.GraphNode): The node to get the ports from.

        Returns:
            Union[list[maxon.GraphNode],None]: The list of ports [out -> in]
        """
        # Bail when the passed node is not a true node.
        if node.GetKind() != maxon.NODE_KIND.NODE:
            return
        for inPort in node.GetOutputs().GetChildren():
            # Get the connected output ports and their wires.
            for outPort, wires in inPort.GetConnections(maxon.PORT_DIR.OUTPUT, None, maxon.Wires.All(), maxon.WIRE_MODE.ALL):
                return [inPort, outPort]

    # NEW 获取连接的节点  ==> ok
    def GetConnectedPorts(self, port: maxon.GraphNode) -> Union[list[maxon.GraphNode],maxon.GraphNode,None]:
        """
        Get the connected port of the given port. if the port is input port. only one port returen, otherwise return a list.

        Args:
            port (maxon.GraphNode): The port to get the ports from.

        Returns:
            Union[list[maxon.GraphNode],maxon.GraphNode,None]: the port or the list of ports
        """
        # Bail when the passed node is not a true node.
        if port.GetKind() != maxon.NODE_KIND.INPORT or port.GetKind() != maxon.NODE_KIND.OUTPORT:
            return
        
        result = list()

        if port.GetKind() != maxon.NODE_KIND.INPORT:
            maxon.GraphModelHelper.GetDirectPredecessors(port, maxon.NODE_KIND.OUTPORT, result)
            return result[0]
        if port.GetKind() != maxon.NODE_KIND.OUTPORT:
            maxon.GraphModelHelper.GetAllSuccessors(port, maxon.NODE_KIND.INPORT, result)
            return result

    #=============================================
    # Wire
    #=============================================

    # 选择的线 ==> ok
    def GetActiveWires(self,  single_mode: bool = True, callback: callable = None) -> Union[maxon.Wires, list[maxon.Wires]]:
        """
        Get the active wires.

        Args:
            sigle_mode (bool): True to anble if only one node selected,return the node but not the list.
            callback (callable, optional): The callback to use. Defaults to None.

        Returns:
            Union[maxon.Wires, list[maxon.Wires]]: The list of wires.
        """
        if callback:
            with self.graph.BeginTransaction() as transaction:
                result = maxon.GraphModelHelper.GetSelectedConnections(self.graph, callback)
                transaction.Commit()
        else:
            result = maxon.GraphModelHelper.GetSelectedConnections(self.graph, callback)
            
        if single_mode:
            if len(result) == 1:
                return result[0]
        return result
        
    # 获取所有连接线 ==> ok
    def GetAllConnections(self) -> list[list[maxon.GraphNode]]:
        """
        Get all connections.

        Returns:
            list[tuple(maxon.GraphNode)]: The list of connections.
        """

        connections = []

        for shader in self.GetAllShaders():
            for inPort in shader.GetInputs().GetChildren():
                for c in inPort.GetConnections(maxon.PORT_DIR.INPUT):
                    outPort = c[0]
                    src = outPort.GetAncestor(maxon.NODE_KIND.NODE)
                    connections.append([src, outPort, shader, inPort])

        return connections
    
    # 添加连接线 ==> ok
    def AddConnection(self, soure_node: maxon.GraphNode, outPort: Union[maxon.GraphNode,str], target_node: maxon.GraphNode, inPort: Union[maxon.GraphNode,str]) -> list[maxon.GraphNode]:
        """
        Add a connection.

        Args:
            soure_node (maxon.GraphNode): The source node.
            outPort (Union[maxon.GraphNode,str]): The source port.
            target_node (maxon.GraphNode): The target node.
            inPort (Union[maxon.GraphNode,str]): The target port.

        Returns:
            list[maxon.GraphNode]: The list of nodes connected  [soure_node, outPort, target_node, inPort].
        """

        if isinstance(outPort,maxon.GraphNode) and isinstance(inPort,maxon.GraphNode):
            return outPort.Connect(inPort)
        
        if soure_node is not None and target_node is not None:

            if outPort is None or outPort == "":
                outPort = "output"

            if isinstance(outPort, str):
                outPort_name = outPort
                outPort = soure_node.GetOutputs().FindChild(outPort_name)
                if not self.IsPortValid(outPort):                    
                    outPort = None

            if isinstance(inPort, str):
                inPort_name = inPort
                inPort = target_node.GetInputs().FindChild(inPort_name)
                if not self.IsPortValid(inPort):
                    inPort = None

            if outPort is None or inPort is None:
                return None

            outPort.Connect(inPort)
            return [soure_node, outPort, target_node, inPort]

    # NEW 连接节点 ==> ok
    def ConnectPorts(self, portA: maxon.GraphNode, portB: maxon.GraphNode) -> bool:
        """
        Connects two ports.

        Args:
            portA (maxon.GraphNode): The first port.
            portB (maxon.GraphNode): The second port.

        Returns:
            bool[bool]: True if connected, False to break loop.
        """
        if isinstance(portA,maxon.GraphNode) and portA.GetKind() != maxon.NODE_KIND.INPORT:
            if isinstance(portB,maxon.GraphNode) and portB.GetKind() != maxon.NODE_KIND.OUTPORT:
                portA.Connect(portB)
                return True
        elif isinstance(portB,maxon.GraphNode) and portB.GetKind() != maxon.NODE_KIND.INPORT:
            if isinstance(portA,maxon.GraphNode) and portA.GetKind() != maxon.NODE_KIND.OUTPORT:
                portB.Connect(portA)
                return True
        return False

    # 删除连接线 ==> ok
    def RemoveConnection(self, port: maxon.GraphNode, another_port: Optional[Union[maxon.GraphNode,str]] = None):
        """
        Disconnects the given shader input.

        Args:
            port (maxon.GraphNode): the port we can remove connection. and we can only fill one port
            another_port (Optional[Union[maxon.GraphNode,str]], optional): the 2rd port. Defaults to None.
        """
        
        # 两个输入都是port 
        # {maxon.NODE_KIND.INPORT = 8 , maxon.NODE_KIND.OUTPORT = 16}
        if another_port is not None:
            if isinstance(another_port, maxon.GraphNode) and isinstance(port, maxon.GraphNode):
                if port.GetKind() == maxon.NODE_KIND.INPORT and another_port.GetKind() == maxon.NODE_KIND.OUTPORT:
                    maxon.GraphModelHelper.RemoveConnection(another_port, port)
                if port.GetKind() == maxon.NODE_KIND.OUTPORT and another_port.GetKind() == maxon.NODE_KIND.INPORT:
                    maxon.GraphModelHelper.RemoveConnection(port, another_port)
        else:
            mask = maxon.Wires(maxon.WIRE_MODE.NORMAL)
            if isinstance(port, maxon.GraphNode) and port.GetKind() == maxon.NODE_KIND.OUTPORT:
                port.RemoveConnections(maxon.PORT_DIR.OUTPUT, mask)                
            if isinstance(port, maxon.GraphNode) and port.GetKind() == maxon.NODE_KIND.INPORT:
                port.RemoveConnections(maxon.PORT_DIR.INPUT, mask)
  
    # 获取节点上端口数据类型ID
    def GetParamDataTypeID(self, node: maxon.GraphNode, paramId: Union[maxon.Id,str]) -> maxon.Id:
        """
        Returns the data type id of the given port.

        Args:
            node (maxon.GraphNode): the host node
            paramId (Union[maxon.Id,str]): the port id

        Returns:
            maxon.Id: the data type id of the port
        """


        port: maxon.GraphNode = self.GetPort(node, paramId)
        if not self.IsPortValid(port):
            return None

        if c4d.GetC4DVersion() >= 2023000:
            return port.GetValue("value").GetType().GetId()
        else:
            return port.GetDefaultValue().GetType().GetId()
    
    # 获取节点上端口数据类型
    def GetParamDataType(self, node: maxon.GraphNode, paramId: Union[maxon.Id,str]) -> maxon.DataType:
        """
        Returns the data type id of the given port.

        Args:
            node (maxon.GraphNode): the host node
            paramId (Union[maxon.Id,str]): the port id

        Returns:
            maxon.Id: the data type of the port
        """

        port: maxon.GraphNode = self.GetPort(node, paramId)
        if not self.IsPortValid(port):
            return None
        
        if c4d.GetC4DVersion() >= 2023000:
            return port.GetValue("value").GetType()
        else:
            return port.GetDefaultValue().GetType()

    # 获取port数据类型ID
    def GetPortDataTypeId(self, port: maxon.GraphNode) -> maxon.Id:
        if c4d.GetC4DVersion() >= 2023000:
            return port.GetValue("value").GetType().GetId()
        else:
            return port.GetDefaultValue().GetType().GetId()

    # 获取port数据类型
    def GetPortDataType(self, port: maxon.GraphNode) -> maxon.DataType:
        """
        Returns the data type id of the given port.

        Args:
            node (maxon.GraphNode): the host node
            paramId (Union[maxon.Id,str]): the port id

        Returns:
            maxon.Id: the data type of the port
        """
        
        if c4d.GetC4DVersion() >= 2023000:
            return port.GetValue("value").GetType()
        else:
            return port.GetDefaultValue().GetType()    


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
                self.helper = Renderer.Redshift.Material(material)
                self.graph: maxon.GraphModelInterface = self.helper.graph

            elif self.nodespaceId == AR_NODESPACE:
                self.helper= Renderer.Arnold.Material(material)
                self.graph: maxon.GraphModelInterface = self.helper.graph
            
            elif self.nodespaceId == VR_NODESPACE:
                self.helper= Renderer.Vray.Material(material)
                self.graph: maxon.GraphModelInterface = self.helper.graph
            if self.graph.IsNullValue():
                raise ValueError("Cannot retrieve the graph of this nimbus NodeSpace.")

        # if the #material is already a NodeGraghHelper instance, we inherit the gragh of the instance
        else:
            if isinstance(material, NodeGraghHelper):
                self.helper = material#.material
                self.graph = material.graph
                self.nodespaceId = material.nodespaceId
                self.nimbusRef = material.nimbusRef
            else:
                try:
                    self.helper = material.material
                    if material is None:
                        raise ValueError(f"Cannot retrieve the material of {material} object.")
                    self.graph = material#.graph
                    self.nodespaceId = material.nodespaceId
                    self.nimbusRef = material.nimbusRef
                    
                except Exception as error:
                    raise RuntimeError(f"{__class__.__name__} can not handle the {material}, {error}")

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


