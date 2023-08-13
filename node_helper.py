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

###  ==========  Import Libs  ==========  ###
import c4d
import maxon
from typing import Union
from typing import Optional
import os
import random

# redshift
RS_NODESPACE = "com.redshift3d.redshift4c4d.class.nodespace"
RS_SHADER_PREFIX = "com.redshift3d.redshift4c4d.nodes.core."
# arnold
AR_NODESPACE = "com.autodesk.arnold.nodespace" 
AR_SHADER_PREFIX = "com.autodesk.arnold.shader."

###  Notes  ###
"""
# Example Node Tree

maxon.GraphModelInterface
    maxon.GraphModelRef
    maxon.NodesGraphModelInterface


maxon.GraphModelInterface 存在一个root node (maxon.GraphModelInterface.GetRoot()).
Root node可以有任意数量的子节点
一个node可以有任意数量的输入输出端口 可以嵌套

所有的node都是maxon.GraphNode(节点/端口) 用maxon.GraphNode.GetKind()区分
    maxon.NODE_KIND.NODE 代表常规意义上的节点
    maxon.NODE_KIND.INPUTS /maxon.NODE_KIND.OUTPUTS 代表节点最顶层的输入输出端口列表
    maxon.NODE_KIND.INPORT / maxon.NODE_KIND.OUTPORT 代表单个端口

Root (maxon.NODE_KIND.NODE)
    N1 (maxon.NODE_KIND.NODE)
        N2 (maxon.NODE_KIND.NODE)
            Inputs (maxon.NODE_KIND.INPUTS)
                PortA (maxon.NODE_KIND.INPORT)
            PortB (maxon.NODE_KIND.INPORT)

                PortC (maxon.NODE_KIND.INPORT)

            Outputs (maxon.NODE_KIND.OUTPUTS)
                PortD (maxon.NODE_KIND.OUTPORT)

        Inputs (maxon.NODE_KIND.INPUTS)
            PortE (maxon.NODE_KIND.INPORT)g

        Outputs (maxon.NODE_KIND.OUTPUTS)
            PortF (maxon.NODE_KIND.OUTPORT)
                PortG (maxon.NODE_KIND.OUTPORT)

    N3 (maxon.NODE_KIND.NODE)
        Inputs (maxon.NODE_KIND.INPUTS)
            PortH (maxon.NODE_KIND.INPORT)

        Outputs (maxon.NODE_KIND.OUTPUTS)
            PortI (maxon.NODE_KIND.OUTPORT)
"""


class NodeGraghHelper(object):
    
    def __init__(self, material: c4d.BaseMaterial):
        """
        A Custom NodeHelper for Node Material. 
        
        ----------
        
        :param material: the BaseMaterial instance from the C4D document.
        :type material: c4d.BaseMaterial
        """
        self.material: c4d.BaseMaterial = material

        if self.material is not None:
            if isinstance(self.material, c4d.Material):
            
                self.nodeMaterial: c4d.NodeMaterial = self.material.GetNodeMaterialReference()
                # node
                self.nodespaceId: maxon.Id = c4d.GetActiveNodeSpaceId()
                if self.nodespaceId is None:
                    raise ValueError("Cannot retrieve the NodeSpace.")
                
                self.nimbusRef: maxon.NimbusBaseRef = self.material.GetNimbusRef(self.nodespaceId)
                if self.nimbusRef is None:
                    raise ValueError("Cannot retrieve the nimbus reference for that NodeSpace.")
                
                self.graph: maxon.GraphModelInterface = self.nodeMaterial.GetGraph(self.nodespaceId)
                if self.graph is None:
                    raise ValueError("Cannot retrieve the graph of this nimbus NodeSpace.")
                
                self.root: maxon.GraphNode = self.graph.GetRoot()

                
            if isinstance(self.material, c4d.NodeMaterial):
                # node
                self.nodespaceId: maxon.Id = c4d.GetActiveNodeSpaceId()
                
                self.nimbusRef: maxon.NimbusBaseRef = self.material.GetNimbusRef(self.nodespaceId)
                if self.nimbusRef is None:
                    raise ValueError("Cannot retrieve the nimbus reference for that NodeSpace.")
                
                self.graph: maxon.GraphModelInterface = self.material.GetGraph(self.nodespaceId)
                if self.graph is None:
                    raise ValueError("Cannot retrieve the graph of this nimbus NodeSpace.")
                
                self.root: maxon.GraphNode = self.graph.GetRoot()
                
    def __str__(self):
        return (f"{self.__class__.__name__}:(Material Name:{self.material.GetName()}) @nodespaceId: {self.nodespaceId}")

    #=============================================
    # Util
    #=============================================

    # 获取资产ID 只有node有asset id ==> ok
    def GetAssetId(self, node: maxon.GraphNode) -> maxon.Id:
        """
        Returns the asset id of the given node.

        :param node: the shader node
        :type node: maxon.GraphNode
        :return: maxon Id
        :rtype: maxon.Id
        """
        res = node.GetValue("net.maxon.node.attribute.assetid")        
        assetId = ("%r"%res)[1:].split(",")[0]
                    
        return assetId  

    # 获取ShaderID ==> ok
    def GetShaderId(self, node: maxon.GraphNode) -> maxon.Id:
        """
        Returns the node id(No prefix) of the given node.

        :param node: the shader node
        :type node: maxon.GraphNode
        :return: maxon Id
        :rtype:  maxon.Id
        """
        if node is None:
            return None
        
        assetId: str = self.GetAssetId(node)
        
        if self.nodespaceId == RS_NODESPACE:
            if assetId.startswith(RS_SHADER_PREFIX):
                return assetId[len(RS_SHADER_PREFIX):]
        elif self.nodespaceId == AR_NODESPACE:
            if assetId.startswith(AR_SHADER_PREFIX):
                return assetId[len(AR_SHADER_PREFIX):]
        return None

    # 获取节点名 ==> ok
    def GetName(self, node: maxon.GraphNode) -> Optional[str]:
        """
        Retrieve the displayed name of a node.

        :param node: The node to retrieve the name from.
        :type node: maxon.GraphNode
        :return: The node name, or None if the Node name can't be retrieved.
        :rtype: Optional[str]
        """
        if node is None:
            return None

        nodeName = node.GetValue(maxon.NODE.BASE.NAME)

        if nodeName is None:
            nodeName = node.GetValue(maxon.EffectiveName)

        if nodeName is None:
            nodeName = str(node)
            
        return nodeName

    # 设置节点名 ==> ok
    def SetName(self, node: maxon.GraphNode, name: str) -> None:
        """
        Set the name of the shader.

        :param node: The shader node.
        :type node: maxon.GraphNode
        :param name: name str
        :type name: str
        :return: True if suceess, False otherwise.
        :rtype: bool
        """
        if node is None:
            return None
        
        shadername = maxon.String(name)
        node.SetValue(maxon.NODE.BASE.NAME, shadername)
        node.SetValue(maxon.EffectiveName, shadername)

    # 选择 ==> ok
    def Select(self, node: maxon.GraphNode) -> maxon.GraphNode:
        """
        Select a port or node.

        :param node: the node to be select.
        :type node: maxon.GraphNode

        :return: the origin node
        :rtype: maxon.GraphNode
        """
        if not isinstance(node, maxon.GraphNode):
            raise ValueError('Expected a maxon.GraphNode, got {}'.format(type(node)))
        
        maxon.GraphModelHelper.SelectNode(node)
        return node

    # 取消选择 ==> ok
    def Deselect(self,node: maxon.GraphNode) -> maxon.GraphNode:
        """
        Deselect a port or node.

        :param node: the node to be deselect.
        :type node: maxon.GraphNode

        :return: the origin node
        :rtype: maxon.GraphNode
        """
        if not isinstance(node, maxon.GraphNode):
            raise ValueError('Expected a maxon.GraphNode, got {}'.format(type(node)))

        maxon.GraphModelHelper.DeselectNode(node)
        return node

    # 获取Output Node ==> ok
    def GetOutput(self):
        """
        Returns the Output node.
        """
        if self.graph is None:
            return None
        if self.nodespaceId == RS_NODESPACE:
            output_id = 'com.redshift3d.redshift4c4d.node.output'
        if self.nodespaceId == AR_NODESPACE:
            output_id = 'com.autodesk.arnold.material'
            
        # Attempt to find the BSDF node contained in the default graph setup.
        result: list[maxon.GraphNode] = []
        maxon.GraphModelHelper.FindNodesByAssetId(
            self.graph, output_id, True, result)
        if len(result) < 1:
            raise RuntimeError("Could not find BSDF node in material.")
        bsdfNode: maxon.GraphNode = result[0]
        
        return bsdfNode
    
    # 获取 BRDF (Material) Node ==> ok
    def GetRootBRDF(self):
        """
        Returns the shader connect to redshift output (maxon.frameworks.graph.GraphNode)
        """
        if self.graph is None:
            return None

        endNode = self.GetOutput()
        if endNode is None:
            print("[Error] End node is not found in Node Material: %s" % self.material.GetName())
            return None
        
        predecessor = list()
        maxon.GraphModelHelper.GetDirectPredecessors(endNode, maxon.NODE_KIND.NODE, predecessor)
        rootshader = predecessor[-1] 
        if rootshader is None and not rootshader.IsValid() :
            raise ValueError("Cannot retrieve the inputs list of the bsdfNode node")
        #print(predecessor)
        return rootshader  

    # 切换预览
    def FoldPreview(self, nodes: list[maxon.GraphNode] ,state: bool = False):

        if self.graph is None:
            return 
        for graph_node in nodes:
            graph_node.SetValue(maxon.NODE.BASE.DISPLAYPREVIEW  , maxon.Bool(state))

    
    # 获取属性 ==> ok
    def GetShaderValue(self, node: maxon.GraphNode, paramId: Union[maxon.Id,str]) -> maxon.Data:
        """
        Returns the value stored in the given shader parameter.

        :param node: the shader node
        :type node: maxon.GraphNode
        :param paramId: the param id
        :type paramId: maxon.Id
        :return: the data
        :rtype: maxon.Data
        """
        if node is None or paramId is None:
            return None
        # standard data type
        port: maxon.GraphNode = node.GetInputs().FindChild(paramId)
        if not self.IsPortValid(port):
            print("[Error] Input port '%s' is not found on shader '%r'" % (paramId, node))
            return None

        return port.GetDefaultValue()
    
    # 设置属性 ==> ok
    def SetShaderValue(self, node: maxon.GraphNode, paramId: Union[maxon.Id,str], value) -> None:
        """
        Sets the value stored in the given shader parameter.

        :param node: the shader ndoe
        :type node: maxon.GraphNode
        :param paramId: the param id
        :type paramId: maxon.Id
        :param value: the value
        :type value: Any
        :return: None
        :rtype: None
        """
        if node is None or paramId is None:
            return None
        # standard data type
        port: maxon.GraphNode = node.GetInputs().FindChild(paramId)
        if not self.IsPortValid(port):
            print("[WARNING] Input port '%s' is not found on shader '%r'" % (paramId, node))
            return None
    
        port.SetDefaultValue(value)

    # 获取所有Shader ==> ok
    def GetAllShaders(self) -> list[maxon.GraphNode]:
        """

        Get all shaders from the graph.

        :return: the list of all shader node in the material
        :rtype: list[maxon.GraphNode]
        """
        if self.graph is None:
            return []

        shaders_list: list = []
        
        # 创建shader list
        def _IterGraghNode(node, shaders_list: list):

            if node.GetKind() != maxon.NODE_KIND.NODE:
                return

            if self.GetAssetId(node) == "net.maxon.node.group":
                for node in self.root.GetChildren():
                    _IterGraghNode(node, shaders_list)
                return

            shaders_list.append(node)
            
        root = self.graph.GetRoot()
        
        for node in root.GetChildren():   
            _IterGraghNode(node, shaders_list) 
            
        return shaders_list

    # New ==> ok
    def IsConnected(self, NodeorPort: maxon.GraphNode = None, port: Union[maxon.GraphNode,str] = None) -> bool:
        """
        Get a port is connected to another port.

        :param port: the port to check
        :type port: maxon.GraphNode
        :return: True if is connected
        :rtype: bool
        """
        if self.graph is None:
            return None

        if NodeorPort is None or port is None:
            return False
        if not isinstance(NodeorPort,maxon.GraphNode) and not isinstance(port,maxon.GraphNode):
            return False

        # node 1 is port
        if isinstance(NodeorPort,maxon.GraphNode) and self.IsPort(NodeorPort):
        
            return maxon.GraphModelHelper.IsConnected(NodeorPort,port)
    
    #=============================================
    # Node
    #=============================================

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
    def GetActiveNodes(self, callback: callable = None) -> Union[list[maxon.GraphNode], maxon.GraphNode, None]:
        """Gets the active node list (with callback) ."""
 
        with self.graph.BeginTransaction() as transaction:
            result = maxon.GraphModelHelper.GetSelectedNodes(self.graph, maxon.NODE_KIND.NODE, callback)
            transaction.Commit()
            
        if len(result) == 0:
            return None
        
        if len(result) == 1:
            return result[0]
        
        return result
   
    # 创建Shader ==> ok
    def AddShader(self, nodeId: Union[str, maxon.Id]) -> maxon.GraphNode:
        """
        Adds a new shader to the graph.
        
        ----------

        :param nodeId: The node entry name.
        :type nodeId: Union[str, maxon.Id]
        :return: the shader node.
        :rtype: maxon.GraphNode
        """
        if self.graph is None:
            return None

        shader: maxon.GraphNode = self.graph.AddChild(childId=maxon.Id(), nodeId=nodeId, args=maxon.DataDictionary())

        return shader 
    
    # 创建Shader 可以提供链接 ==> ok
    def AddConnectShader(self, nodeID: str=None, 
                input_ports: list[Union[str,maxon.GraphNode]]=None, connect_inNodes: list[maxon.GraphNode]=None,
                output_ports: list[Union[str,maxon.GraphNode]]=None, connect_outNodes: list[maxon.GraphNode]=None
                ) -> Union[maxon.GraphNode,None] :
        """
        Add shader and connect with given ports and nodes.

        :param nodeID: the shader id, defaults to None
        :type nodeID: str, optional
        :param input_ports: the input port list, defaults to None
        :type input_ports: list[str | maxon.GraphNode], optional
        :param connect_inNodes: the node list connect to inputs, defaults to None
        :type connect_inNodes: list[maxon.GraphNode], optional
        :param output_ports: the output port list, defaults to None
        :type output_ports: list[str | maxon.GraphNode], optional
        :param connect_outNodes: the node list connect to outputs, defaults to None
        :type connect_outNodes: list[maxon.GraphNode], optional
        :return: the shader.
        :rtype: maxon.GraphNode|None
        """
        if self.graph is None:
            return None
        
        shader: maxon.GraphNode = self.graph.AddChild("", nodeID , maxon.DataDictionary())
        if not shader:
            return None
        
        if (isinstance(input_ports,maxon.GraphNode) or isinstance(input_ports,str)) and not isinstance(input_ports,list):
            input_ports = [input_ports]
        
        if (isinstance(output_ports,maxon.GraphNode) or isinstance(output_ports,str)) and not isinstance(output_ports,list):
            output_ports = [output_ports]
            
        if isinstance(connect_inNodes,maxon.GraphNode) and not isinstance(connect_inNodes,list):
            connect_inNodes = [connect_inNodes]
        
        if isinstance(connect_outNodes,maxon.GraphNode) and not isinstance(connect_outNodes,list):
            connect_outNodes = [connect_outNodes]
        
        if input_ports is not None:
            if connect_inNodes is not None:
                if len(connect_inNodes) > len(input_ports):
                    raise ValueError('Port nodes can not bigger than input port.')
                if len(input_ports) > len(connect_inNodes):
                    input_ports = input_ports[:len(connect_inNodes)]
                for i, input_port in enumerate(input_ports):
                    input: maxon.GraphNode = self.GetPort(shader,input_port)
                    connect_inNodes[i].Connect(input)
        
        if output_ports is not None:
            if connect_outNodes is not None:
                if len(connect_outNodes) > len(output_ports):
                    raise ValueError('Port nodes can not bigger than output port.')
                if len(output_ports) > len(connect_outNodes):
                    output_ports = output_ports[:len(connect_outNodes)]
                for i, output_port in enumerate(output_ports):
                    output: maxon.GraphNode = self.GetPort(shader,output_port)
                    print(output , connect_outNodes[i])
                    output.Connect(connect_outNodes[i])

        return shader

    # 在Wire中插入Shader （New） ==> ok
    def InsertShader(self, nodeID: Union[str,maxon.Id], wire: maxon.Wires, 
                     input_port: list[Union[str,maxon.GraphNode]],
                     output_port: list[Union[str,maxon.GraphNode]]) -> maxon.GraphNode:
        """
        Insert a shder into a wire, and keep connect.

        :param nodeID: the node id
        :type nodeID: str | maxon.Id
        :param wire: the wire to insert the shader
        :type wire: maxon.Wires
        :param input_port: the input port of the insert node
        :type input_port: list[str | maxon.GraphNode]
        :param output_port: the output port of the insert node
        :type output_port: list[str | maxon.GraphNode]
        :return: the node
        :rtype: maxon.GraphNode
        """
        if not wire:
            wire: maxon.Wires = self.GetActiveWires() # last select wire
        pre_port: maxon.GraphNode = wire[0]
        #pre_node: maxon.GraphNode = self.GetTrueNode(pre_port)
        next_port: maxon.GraphNode = wire[1]
        #next_node: maxon.GraphNode = self.GetTrueNode(next_port)
        
        # Remove old wire
        self.RemoveConnection(next_port,pre_port)
        # add our new shader and wires
        #print(input_port,pre_port,output_port,next_port)
        return self.AddConnectShader(nodeID,input_port,pre_port,output_port,next_port)

    # 删除Shader ==> ok
    def RemoveShader(self, shader: maxon.GraphNode):
        """
        Removes the given shader from the graph.

        ----------
        :param shader: The node to be remove.
        :type shader: maxon.GraphNode
        shader : maxon.frameworks.graph.GraphNode
            The shader node.
        """
        if self.graph is None:
            return

        if shader is None or not isinstance(shader, maxon.GraphNode):
            return

        shader.Remove()

    # 是否是shader ==> ok
    def IsNode(self, node: maxon.GraphNode) -> bool:
        """
        Check if a node is a node.

        :param node: the GraghNode to check
        :type node: maxon.GraphNode
        :return: True if is node
        :rtype: bool
        """
        if self.graph is None:
            return None
        if not isinstance(node,maxon.GraphNode) :
            return False
        if node.GetKind() == maxon.NODE_KIND.NODE and node.IsValid():
            return True
        return False

    # 获取节点  ==> ok
    def GetNodes(self, shader: Union[maxon.GraphNode, str]) -> list[maxon.GraphNode]:
        """
        Get all Nodes of given shader.

        Parameters
        ----------
        :param shader: the shader
        :type shader: maxon.GraphNode | str
        :return: the return nodes
        :rtype: list[maxon.GraphNode]
        """
        if self.graph is None:
            return None
        if not shader:
            return None
        
        result: list[maxon.GraphNode] = []
        
        if isinstance(shader, maxon.GraphNode):
            asset_id = self.GetAssetId(shader)
            
        if isinstance(shader, str):
            asset_id = shader
        maxon.GraphModelHelper.FindNodesByAssetId(
            self.graph, asset_id, True, result)
        return result

    # New ==> ok
    def GetPreNode(self, node: maxon.GraphNode) -> list[maxon.GraphNode]:
        """
        Returns True if the given shader is connected to the pre shader.

        :param node: the shader to check
        :type node: maxon.GraphNode
        
        :return: Return the true node list which is direct connect before to the node.
        :rtype: list[maxon.GraphNode]
        """
        result = list()
        maxon.GraphModelHelper.GetDirectPredecessors(node, maxon.NODE_KIND.NODE, result)
        return result

    # New ==> ok
    def GetNextNode(self, node: maxon.GraphNode) -> list[maxon.GraphNode]:
        """
        Returns True if the given shader is connected to the next shader.

        :param node: the shader to check
        :type node: maxon.GraphNode

        :return: Return the true node list which is direct connect after to the node.
        :rtype: list[maxon.GraphNode]
        """
        result = list()
        maxon.GraphModelHelper.GetDirectSuccessors(node, maxon.NODE_KIND.NODE, result)
        return result

    # New ==> ok
    def GetPreNodes(self, node: maxon.GraphNode, result) -> list:
        """Get all connected node for #node(before).
        """
        # Bail when the passed node is not a true node.
        if node.GetKind() != maxon.NODE_KIND.NODE:
            return
        
        for inPort in node.GetInputs().GetChildren():
            # Get the connected output ports and their wires.
            for outPort, wires in inPort.GetConnections(maxon.PORT_DIR.INPUT, None, maxon.Wires.All(), maxon.WIRE_MODE.ALL):
                pre_node: maxon.GraphNode = self.GetTrueNode(outPort)
                if pre_node not in result:
                    result.append(pre_node)
                self.GetPreNodes(pre_node,result)
        
    # New ==> ok
    def GetNextNodes(self, node: maxon.GraphNode, result) -> list:
        """Get all connected node for #node(before).
        """
        # Bail when the passed node is not a true node.
        if node.GetKind() != maxon.NODE_KIND.NODE:
            return
        
        for outPort in node.GetOutputs().GetChildren():
            # Get the connected output ports and their wires.
            for outPort, wires in outPort.GetConnections(maxon.PORT_DIR.OUTPUT, None, maxon.Wires.All(), maxon.WIRE_MODE.ALL):
                pre_node: maxon.GraphNode = self.GetTrueNode(outPort)
                if pre_node not in result:
                    result.append(pre_node)
                self.GetNextNodes(pre_node,result)

    # New ==> ok
    def IsNodeConnected(self, node: maxon.GraphNode) -> bool:
        """
        Check if the node is connect to another port.

        :param port: the node to check
        :type node: maxon.GraphNode
        :return: True if is connected.
        :rtype: bool
        """
        if self.graph is None:
            return None
        if not self.IsNode(node):
            return None
        
        all_ports = self.GetAllConnectedPorts(node)

        for the_port in all_ports:
            if maxon.GraphModelHelper.IsConnected(node, the_port):
                return True
        return False
  

    #=============================================
    # Port
    #=============================================

    # 选择的端口 ==> ok
    def GetActivePorts(self, callback: callable = None) -> Union[list[maxon.GraphNode], maxon.GraphNode, None]:
        """Gets the active port list (with callback) ."""
 
        with self.graph.BeginTransaction() as transaction:
            result = maxon.GraphModelHelper.GetSelectedNodes(self.graph, maxon.NODE_KIND.PORT_MASK, callback)
            transaction.Commit()
            
        if len(result) == 0:
            return None
        
        if len(result) == 1:
            return result[0]
        
        return result
    
    # NEW 新建（暴露端口） ==> ok
    def AddPort(self, node: maxon.GraphNode, port :Union[str, maxon.GraphNode]) -> maxon.GraphNode:
        """
        Add a 'true' port in the gragh ui.

        :param node: the node
        :type node: maxon.GraphNode
        :param port: the port or the port id
        :type port: Union[str, maxon.GraphNode]
        :return: the port.
        :rtype: maxon.GraphNode
        """
        if self.graph is None:
            return
        if node is None:
            return
        if port is None:
            return
        if not isinstance(node, maxon.GraphNode):
            raise ValueError("Node is not a True Node")
        
        if isinstance(port, str):
            true_port = self.GetPort(node, port)
        if isinstance(port, maxon.GraphNode):
            true_port = port
        
        true_port.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(False))
        return true_port

    # NEW 删除（隐藏端口） ==> ok
    def RemovePort(self, node: maxon.GraphNode, port :Union[str, maxon.GraphNode]) -> maxon.GraphNode:
        """
        Hide a 'true' port in the gragh ui.
        
        Parameters
        ----------
        :param node: the node
        :type node: maxon.GraphNode
        :param port: the port or the port id
        :type port: Union[str, maxon.GraphNode]
        :return: the port.
        :rtype: maxon.GraphNode
        """
        if self.graph is None:
            return
        if node is None:
            return
        if port is None:
            return
        if not isinstance(node, maxon.GraphNode):
            raise ValueError("Node is not a True Node")
        
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

        Parameters
        ----------
        :param shader: the shader
        :type shader: maxon.GraphNode
        :param port_id: the shader port id (copy from C4D)
        :type port_id: str
        :return: the return port
        :rtype: maxon.GraphNode
        """
        if self.graph is None:
            return None
        if not shader:
            return None
        
        if self.nodespaceId == RS_NODESPACE:
            if port_id == None:
                out_ids = ['outcolor','output','out']
                for out in out_ids:
                    port_id = self.GetAssetId(shader) + out                
                    port: maxon.GraphNode = shader.GetInputs().FindChild(port_id)
                    if port.IsNullValue():
                        port = shader.GetOutputs().FindChild(port_id)
                    if not port.IsNullValue():
                        return port
            else:
                port: maxon.GraphNode = shader.GetInputs().FindChild(port_id)
                if port.IsNullValue():
                    port = shader.GetOutputs().FindChild(port_id)
            return port
        
        if self.nodespaceId == AR_NODESPACE:
            if port_id == None:
                out_ids = ['outcolor','output','out']
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
            return port

    # 获取端口所在节点 ==> ok
    def GetTrueNode(self, port: maxon.GraphNode) -> maxon.GraphNode:
        """
        Get the actually node host the given port.
        
        Parameters
        ----------
        :param port: the port
        :type port: maxon.GraphNode
        :return: the true node
        :rtype: maxon.GraphNode
        """
        if self.graph is None:
            return None
        if not port:
            return None

        trueNode = port.GetAncestor(maxon.NODE_KIND.NODE)

        return trueNode
    
    # 端口合法 ==> ok
    def IsPortValid(self, port: maxon.GraphNode) -> bool:
        """
        Checks if the port is valid.

        :param port: the shader port
        :type port: maxon.GraphNode
        :return: True if is valid, False otherwise
        :rtype: bool
        """
        try:
            return port.IsValid()
        except Exception as e:
            return False

    # New ==> ok
    def IsPort(self, port: maxon.GraphNode) -> bool:
        """
        Check if a node is a port.

        :param port: the GraghNode to check
        :type port: maxon.GraphNode
        :return: True if is port
        :rtype: bool
        """
        if self.graph is None:
            return None
        if not isinstance(port,maxon.GraphNode) :
            return False
        if (port.GetKind() == maxon.NODE_KIND.INPORT or port.GetKind() == maxon.NODE_KIND.OUTPORT) and port.IsValid():
            return True
        return False
    
    # New ==> ok
    def OnSameNode(self, port_1: maxon.GraphNode ,port_2: maxon.GraphNode) -> bool:
        if self.graph is None:
            return None
        if not self.IsPort(port_1) or not self.IsPort(port_2):
            return False
        if self.GetTrueNode(port_1) == self.GetTrueNode(port_2):
            return True
        return False
    
    # New ==> ok
    def GetAllConnectedPorts(self, except_node: maxon.GraphNode = None) -> list[maxon.GraphNode]:
        """
        Get all ports with something connected, if except_node is passed,
        the port on the except_node will be except.

        :param except_node: except_node, defaults to None
        :type except_node: maxon.GraphNode, optional
        :return: list of the ports
        :rtype: list
        """
        if self.graph is None:
            return None
        all_ports = []
        wirs = self.GetAllConnections()
        for wir in wirs:
            if except_node:
                if not self.GetTrueNode(wir[1]) == except_node:
                    all_ports.append(wir[1])
                if not self.GetTrueNode(wir[-1]) == except_node:
                    all_ports.append(wir[-1])
            else:
                all_ports.append(wir[1])
                all_ports.append(wir[-1])
        return all_ports
    
    # New ==> ok
    def IsPortConnected(self, port: maxon.GraphNode) -> bool:
        """
        Check if the port is connect to another port.

        :param port: the port to check
        :type port: maxon.GraphNode
        :return: True if is connected.
        :rtype: bool
        """
        if self.graph is None:
            return None
        if not self.IsPort(port):
            return None
        
        all_ports = []
        wirs = self.GetAllConnections()
        for wir in wirs:
            if not self.OnSameNode(port, wir[1]):
                all_ports.append(wir[1])
            if not self.OnSameNode(port, wir[-1]):
                all_ports.append(wir[-1])

        for the_port in all_ports:
            if maxon.GraphModelHelper.IsConnected(port, the_port):
                return True
        return False

    # New ==> ok        
    def GetPreNodePorts(self, node: maxon.GraphNode, result) -> list:
        """Get all connected node's port for #node(before).
        """
        # Bail when the passed node is not a true node.
        if node.GetKind() != maxon.NODE_KIND.NODE:
            return
        
        for inPort in node.GetInputs().GetChildren():
            # Get the connected output ports and their wires.
            for outPort, wires in inPort.GetConnections(maxon.PORT_DIR.INPUT, None, maxon.Wires.All(), maxon.WIRE_MODE.ALL):
                otherNode: maxon.GraphNode = self.GetTrueNode(outPort)
                result.append((outPort, inPort))
                self.GetPreNodePorts(otherNode,result)

    # New ==> ok
    def GetNextNodePorts(self, node: maxon.GraphNode, result) -> list:
        """Get all connected node's port for #node(before).
        """
        # Bail when the passed node is not a true node.
        if node.GetKind() != maxon.NODE_KIND.NODE:
            return
        
        for inPort in node.GetOutputs().GetChildren():
            # Get the connected output ports and their wires.
            for outPort, wires in inPort.GetConnections(maxon.PORT_DIR.OUTPUT, None, maxon.Wires.All(), maxon.WIRE_MODE.ALL):
                otherNode: maxon.GraphNode = self.GetTrueNode(outPort)
                result.append((inPort, outPort))
                self.GetNextNodePorts(otherNode,result)

    #=============================================
    # Wire
    #=============================================

    # 选择的线 ==> ok
    def GetActiveWires(self, callback: callable = None) -> Union[list[maxon.Wires], maxon.Wires, None]:        
        """Gets the active wires list (with callback) ."""
        
        with self.graph.BeginTransaction() as transaction:
            result = maxon.GraphModelHelper.GetSelectedConnections(self.graph, callback)
            transaction.Commit()
            
        if len(result) == 0:
            return None
        
        if len(result) == 1:
            return result[0]
          
        return result
        
    # 获取所有连接线 ==> ok
    def GetAllConnections(self) -> list[list[maxon.GraphNode]]:
        """
        Returns the list of connections within this shader graph.
        A connection is a tuple of:
            source shader node : maxon.GraphNode
            source shader output port id : str
            target shader node : maxon.GraphNode
            target shader input port id : str
        """
        if self.graph is None:
            return []

        connections = []

        for shader in self.GetAllShaders():
            for inPort in shader.GetInputs().GetChildren():
                for c in inPort.GetConnections(maxon.PORT_DIR.INPUT):
                    outPort = c[0]
                    src = outPort.GetAncestor(maxon.NODE_KIND.NODE)
                    connections.append((src, outPort, shader, inPort))

        return connections
    
    # 添加连接线 ==> ok
    def AddConnection(self, soure_node: maxon.GraphNode, outPort: Union[maxon.GraphNode,str], target_node: maxon.GraphNode, inPort: maxon.GraphNode|str) -> list[maxon.GraphNode,maxon.Id]:
        """
        Connects the given shaders with given port.

        ----------
        :param soure_node : The source shader node.
        :type soure_node: maxon.GraphNode
        :param outPort : The out Port of soure_node shader node.
        :type outPort: maxon.GraphNode
        :param target_node : The target shader node.
        :type target_node: maxon.GraphNode
        :param inPort : Input port id of the target shader node..
        :type inPort: maxon.GraphNode
        :return: a list of all inputs
        :rtype: list[maxon.GraphNode,maxon.Id]
        
        """

        if self.graph is None:
            return None

        if isinstance(outPort,maxon.GraphNode) and isinstance(inPort,maxon.GraphNode):
            return outPort.Connect(inPort)            
        
        if soure_node is not None and target_node is not None:

            if outPort is None or outPort == "":
                outPort = "output"

            if isinstance(outPort, str):
                outPort_name = outPort
                outPort = soure_node.GetOutputs().FindChild(outPort_name)
                if not self.IsPortValid(outPort):
                    print("[WARNING] Output port '%s' is not found on shader '%r'" % (outPort_name, soure_node))
                    outPort = None

            if isinstance(inPort, str):
                inPort_name = inPort
                inPort = target_node.GetInputs().FindChild(inPort_name)
                if not self.IsPortValid(inPort):
                    print("[WARNING] Input port '%s' is not found on shader '%r'" % (inPort_name, target_node))
                    inPort = None

            if outPort is None or inPort is None:
                return None

            outPort.Connect(inPort)
            return [soure_node, outPort, target_node, inPort]

    # 删除连接线 ==> ok
    def RemoveConnection(self, port: maxon.GraphNode, another_port: Optional[Union[maxon.GraphNode,str]] = None):
        """

        Disconnects the given shader input.

        ----------

        :param target_node: The target shader node.
        :type target_node: maxon.GraphNode
        :param inPort: Input port id of the target shader node.
        :type inPort: maxon.GraphNode
        """
        if self.graph is None:
            return None

        if port is None:
            return None
        
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
  
    #=============================================
    # to be Fix
    #=============================================
    # port.GetDefaultValue() can't get the vector value

    # FIXME 获取port数据类型
    def GetParamDataTypeID(self, node: maxon.GraphNode, paramId: Union[maxon.Id,str]) -> maxon.DataType:
        """
        Returns the data type id of the given port.

        :param node: the shader node
        :type node: maxon.GraphNode
        :param paramId: the param id
        :type paramId: maxon.Id
        :return: the data type
        :rtype: maxon.DataType
        """
        if node is None or paramId is None:
            return None

        if isinstance(paramId, str):
            port: maxon.GraphNode = node.GetInputs().FindChild(paramId)
        if isinstance(paramId, maxon.GraphNode):
            port = paramId
            
        if not self.IsPortValid(port):
            return None

        return port.GetDefaultValue().GetType().GetId()
    
    # FIXME 获取port数据类型
    def GetParamDataType(self, node: maxon.GraphNode, paramId: Union[maxon.Id,str]) -> maxon.DataType:
        """
        Returns the data type id of the given port.

        :param node: the shader node
        :type node: maxon.GraphNode
        :param paramId: the param id
        :type paramId: maxon.Id
        :return: the data type
        :rtype: maxon.DataType
        """
        if node is None or paramId is None:
            return None

        if isinstance(paramId, str):
            port: maxon.GraphNode = node.GetInputs().FindChild(paramId)
        if isinstance(paramId, maxon.GraphNode):
            port = paramId
            
        if not self.IsPortValid(port):
            return None

        return port.GetDefaultValue().GetType()
    

    # todo


###  ==========  Func  ==========  ###

# data json
keys_json: dict = {
    "AO": [
        "AO",
        "occlusion",
        "ambient_occlusion"
    ],
    "Alpha": [
        "Opacity",
        "Alpha"
    ],
    "Bump": [
        "Bump",
        "BUMP"
    ],
    "Diffuse": [
        "Base_Color",
        "Albedo",
        "COLOR",
        "COL",
        "Color"
    ],
    "Displacement": [
        "DISP",
        "DEPTH",
        "Depth",
        "Height",
        "Displacement"
    ],
    "Glossiness": [
        "Gloss",
        "GLOSS",
        "Glossiness"
    ],
    "Metalness": [
        "Metalness"
    ],
    "Normal": [
        "Normal",
        "NRM",
        "NORMAL",
        "Normaldx"
    ],
    "Roughness": [
        "ROUGHNESS",
        "Roughness"
    ],
    "Translucency": [
        "Translucency"
    ],
    "Transmission": [
        "Transmission",
        "transmission",
        "Trans"
    ],
    "Specular": [
        "Specular",
        "Spec"
    ]
    }

class TexPack:
    """
    Thanks for Gheyret@Boghma
    """
    def get_all_keys(self):
        """
        获取关键词数据和原始数据
        :return: 关键词列表，原始数据
        """

        # 所有关键词去重保存
        # sum：拆分嵌套列表合并成一个列表
        # set：列表去重
        keys = list(set(sum(keys_json.values(), [])))
        return keys, keys_json

    def get_texture_data(self, texture: str = None):
        
        if texture is None:
            # 用户任意选择一张贴图
            file = c4d.storage.LoadDialog(type=c4d.FILESELECTTYPE_IMAGES, title='Select a texture',
                                        flags=c4d.FILESELECT_LOAD)
            if not file:
                return
        if file:
            # 关键词列表， 原始数据
            all_keys, key_data = self.get_all_keys()

            # 用户选择的贴图文件的 路径 和 文件名
            fp, fn = os.path.split(file)

            # 文件名 和 后缀
            fn, ext = os.path.splitext(fn)

            # 支持的贴图后缀
            # 某些贴图包中的贴图格式并不相同，比如；Albedo.jpg，Normal.png
            # 这种情况下用户选择的贴图的后缀和当前贴图包中的其他贴图的后缀不一样会导致插件找不到其他贴图
            ext_list = [".jpg", ".png", ".exr", ".tif", ".tiff", ".tga"]

            channels = []  # 贴图通道
            textures = []  # 贴图

            name = ""
            # 遍历关键词列表，k = 关键词
            for k in all_keys:
                if k:
                    if k in fn:
                        # 如果贴图文件名中有某个关键词
                        # 以关键词对文件名拆分，例如：ground_albedo_2k ---> ['ground_', '_2k']
                        # ['asdasd_4k_', ""]
                        words = fn.split(k)

                        for k in all_keys:
                            if k:
                                # 遍历通道，key = 通道名（原始数据字典中的key）
                                for key in key_data:
                                    # 用户的 关键词 在原始数据中的哪个列表里
                                    if k in key_data[key]:
                                        for e in ext_list:
                                            # 组合贴图完整路径和名称，开始找贴图
                                            tex = os.path.join(fp, f"{words[0]}{k}{words[1]}{e}")
                                            # 如果贴图存在
                                            if os.path.exists(tex):
                                                # 在通道列表里加入 通道key，贴图列表里加入 贴图tex
                                                channels.append(key)
                                                textures.append(tex)
                                                name = words[0]
                                                # 得到了 贴图属于哪个通道 和 贴图路径
            # 将两个列表组合成一个字典：
            # {"Diffuse": "D:\Texture\ground_albedo_2k.jpg"} ...
            tex_data = dict(zip(channels, textures))

            if name[-1] == "_" or name[-1] == "-" or name[-1] == " ":
                name = name[:-1]
            elif name == "":
                name = "MyMaterial"
            return tex_data, name
        else:
            return None

# 获取所有对象
def get_all_nodes(doc: c4d.documents.BaseDocument) -> list[c4d.BaseObject] :
    """
    Return the list of all nodes in Object Manager.

    Args:
        doc (c4d.documents.BaseDocument): c4d.documents.BaseDocument
    Returns:
        list[c4d.BaseObject]: A List of all objects
    """
    def iterate(node: c4d.BaseObject) -> c4d.BaseObject:
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
    def iterate(node: c4d.BaseObject) -> c4d.BaseObject:
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
def get_tags(doc: c4d.documents.BaseDocument, TRACKED_TYPES : list[int]) -> list[c4d.BaseTag] :
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
            if tag.GetType() in TRACKED_TYPES:
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
def get_texture_tag(selectionTag : c4d.SelectionTag) -> c4d.TextureTag :
    """
    Check if the selection tag has a material.
    Args:
        avtag (c4d.BaseTag, optional): The tag to check with. Defaults to doc.GetActiveTag().
    Returns:
        c4d.TextureTag: The texture tag assign with the selection tag.
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
def select_all_materials(doc=None):
    # Deselect All Mats
    if not doc:
        doc = c4d.documents.GetActiveDocument()
    for m in doc.GetActiveMaterials() :
        doc.AddUndo(c4d.UNDOTYPE_BITS, m)
        m.SetBit(c4d.BIT_ACTIVE)

# 取消选择所有材质
def deselect_all_materials(doc=None):
    # Deselect All Mats
    if not doc:
        doc = c4d.documents.GetActiveDocument()
    for m in doc.GetActiveMaterials() :
        doc.AddUndo(c4d.UNDOTYPE_BITS, m)
        m.DelBit(c4d.BIT_ACTIVE)

# 获取资产url
def get_asset_url(aid: Union[maxon.Id,str]) -> maxon.Url:
    """Returns the asset URL for the given file asset ID.
    """
    # Bail when the asset ID is invalid.
    if not isinstance(aid, maxon.Id) or aid.IsEmpty():        
        aid = maxon.Id(aid)
        
    if aid.IsEmpty():
        raise RuntimeError("Could not find the maxon id")

    # Get the user repository, a repository which contains almost all assets, and try to find the
    # asset description, a bundle of asset metadata, for the given asset ID in it.
    repo: maxon.AssetRepositoryRef = maxon.AssetInterface.GetUserPrefsRepository()
    if repo.IsNullValue():
        raise RuntimeError("Could not access the user repository.")
    
    asset: maxon.AssetDescription = repo.FindLatestAsset(
        maxon.AssetTypes.File(), aid, maxon.Id(), maxon.ASSET_FIND_MODE.LATEST)
    if asset.IsNullValue():
        raise RuntimeError(f"Could not find file asset for {aid}.")

    # When an asset description has been found, return the URL of that asset in the "asset:///"
    # scheme for the latest version of that asset.
    return maxon.AssetInterface.GetAssetUrl(asset, True)

# 获取资产str
def get_asset_str(aid: Union[maxon.Id,str]) -> str:
    """Returns the asset str for the given file asset ID.
    """
    return str(get_asset_url(aid))

# 迭代对象
def iter_node(node, include_node=False, include_siblings=False) -> list[c4d.GeListNode]:
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
def generate_random_color(pastel_factor = 0.5):
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
    return best_color

# NEW
def get_tex_folder(doc: c4d.documents.BaseDocument = None) -> str :
    """
    Get the local tex folder in the expolorer.

    Returns:
        string : tex folder path
    """
    if doc is None:
        doc = c4d.documents.GetActiveDocument()
    tex_folder = os.path.join(doc.GetDocumentPath(),"tex") # Tex Folder
    if not os.path.exists(tex_folder):
        os.makedirs(tex_folder)
    return tex_folder

def get_texture_path(doc: c4d.documents.BaseDocument = None, file_name: str = None) -> Union[str,bool]:
    """
    Get the tex path.

    Returns:
        string : tex path | Flase
    """
    if doc is None:
        doc = c4d.documents.GetActiveDocument()        
    if file_name is None:
        return False
    if file_name == '':
        return False
    if os.path.exists(file_name):
        return file_name
    if os.path.exists(os.path.join(get_tex_folder(doc),file_name)):
        return os.path.join(get_tex_folder(doc),file_name)
    else:
        # Gets global texture paths
        paths = c4d.GetGlobalTexturePaths()
        for path, enabled in paths:
            if os.path.exists(os.path.join(path,file_name)):
                return os.path.join(path,file_name)
    return False

# todo