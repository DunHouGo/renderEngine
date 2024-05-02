###  ==========  Author INFO  ==========  ###

__author__ = "DunHouGo"
__copyright__ = "Copyright (C) 2023 Boghma"
__website__ = "https://www.boghma.com/"
__license__ = "Apache-2.0 License"
__version__ = "2023.2.1"

###  ==========  Import Libs  ==========  ###
import c4d
import maxon
import Renderer
import os
import random
from typing import Union,Optional
from Renderer.constants.vray_id import *
from Renderer.utils.node_helper import NodeGraghHelper, EasyTransaction

class MaterialHelper(NodeGraghHelper):

    # 初始化 ==> OK
    def __init__(self, material: Union[c4d.BaseMaterial, str] = None):
        
        # If we filled a str, we create a material with the name of the string
        if isinstance(material, str):
            self.material = self.Create(material)

        # No argument filled, we create a material with default name
        elif material is None:
            self.material = self.Create()

        else:
            self.material = material

        # Acess data
        self.graph = None
        self.nimbusRef = self.material.GetNimbusRef(Renderer.RS_NODESPACE)

        if isinstance(self.material, c4d.Material):
            nodeMaterial = self.material.GetNodeMaterialReference()
            self.graph: maxon.GraphModelInterface = nodeMaterial.GetGraph(Renderer.RS_NODESPACE)

        # Super the NodeGraghHelper
        super().__init__(self.material)

        # A final check
        if self.graph.IsNullValue():
            raise RuntimeError("Empty graph associated with Redshift node space.")

    def __str__(self):
        return (f"A Vray {self.__class__.__name__} Instance with Material : {self.material.GetName()}")
    
    # =====  Material  ===== #

    # 创建材质(Standard Surface) ==> OK
    def Create(self, name: str = "Standard Surface") -> c4d.BaseMaterial:
        """
        Creates a new Vray Node Material with a NAME.

        Parameters
        ----------
        name : str
            The Material entry name.

        """
        material = c4d.BaseMaterial(c4d.Mmaterial)
        if material is None:
            raise ValueError("Cannot create a BaseMaterial")
                 
        material.SetName(name)

        nodeMaterial = material.GetNodeMaterialReference()
        if nodeMaterial is None:
            raise ValueError("Cannot retrieve nodeMaterial reference")
        # Add a graph for the redshift node space
        nodeMaterial.CreateDefaultGraph(Renderer.VR_NODESPACE)  

        with EasyTransaction(material) as tr:
            # ports
            brdf: maxon.GraphNode = tr.GetRootBRDF()
            tr.SetName(brdf,'V-Ray Material')
        return material

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

    def FastPreview(self, on: bool = True):
        if self.material is not None:
            if on:
                self.material[c4d.MATERIAL_PREVIEWSIZE] = 6 # 64x64
            else:
                self.material[c4d.MATERIAL_PREVIEWSIZE] = 0 # default

    # 创建Shader ==> OK 
    def AddNode(self, nodeId: str , outport_id: str = None, targret_shader = None, target_port= None) -> maxon.GraphNode :
        """
        Adds a new shader to the graph.

        Parameters
        ----------
        nodeId : str
            The Redshift node entry name.
        useStr : bool
            True : only inpput node name
            False: inpput full node id 
        """
        if self.graph is None:
            return None        

        shader = self.AddShader(nodeId)

        if outport_id is not None:
            if isinstance(target_port, maxon.GraphNode):
                out = self.GetPort(shader, outport_id)
                out.Connect(target_port)
        else:
            self.AddConnection(shader, outport_id, targret_shader, target_port)
        return shader

    def GetRootBRDF(self, filter: Union[str,int] = 0) -> maxon.GraphNode:
        """
        Returns the very first brdf shader connect to output

        Args:
            filter (Union[str,int], optional): filter to get the object, fill ``str`` to filter by name, fill ``int`` to filter by index. Defaults to 0.

        Returns:
            maxon.GraphNode: the BRDF node
        """

        vr_mat = "com.chaos.vray_node.brdfvraymtl"
        valid_mat = [vr_mat]

        endNode = self.GetOutput()
        if not endNode: return None

        # only one direct brdf
        predecessor = list()
        maxon.GraphModelHelper.GetDirectPredecessors(endNode, maxon.NODE_KIND.NODE, predecessor)
        rootshader = [i for i in predecessor if self.GetAssetId(i) in valid_mat]
        if rootshader:
            return rootshader[0]

        # find brdf by filter
        else:
            nodes = []
            for i in valid_mat:
                nodes += self.GetNodes(i)
            # By Name
            if isinstance(filter, str):
                for node in nodes:
                    if self.GetName(node) == filter:
                        return node
            elif isinstance(filter, int):
                return nodes[filter]

    ### Material ###
    
    def AddStandardMaterial(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Standard Material shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.chaos.vray_node.brdfvraymtl",
            input_ports = ['com.chaos.vray_node.brdfvraymtl.diffuse'],
            connect_inNodes = inputs,
            output_ports=['com.chaos.vray_node.brdfvraymtl.output.default'], 
            connect_outNodes = target
            )
    
    ### Color ###

    # 创建Invert ==> OK
    def AddInvert(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new invert shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.chaos.vray_node.texinvert",
            input_ports = ['com.chaos.vray_node.texinvert.texture'],
            connect_inNodes = inputs,
            output_ports=['com.chaos.vray_node.texinvert.output.default'], 
            connect_outNodes = target
            )
    
    # 创建color correct ==> OK
    def AddColorCorrect(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new color correct shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.chaos.vray_node.colorcorrection",
            input_ports = ['com.chaos.vray_node.colorcorrection.texture_map'],
            connect_inNodes = inputs,
            output_ports=['com.chaos.vray_node.colorcorrection.output.default'], 
            connect_outNodes = target
            )

    ### Bump ###

    # 创建Bump ==> # todo
    def AddBump(self, input_port: maxon.GraphNode = None, target_port: maxon.GraphNode = None, bump_mode: int = 0) -> maxon.GraphNode :
        """
        Adds a new Bump shader to the graph.

        """
        if self.graph is None:
            return None
        shader: maxon.GraphNode = self.graph.AddChild("", "com.chaos.vray_node.brdfbump", maxon.DataDictionary())
        type_port = self.GetPort(shader, 'com.chaos.vray_node.brdfbump.map_type')
        type_port.SetDefaultValue(bump_mode)

        if input_port:
            if isinstance(input_port, maxon.GraphNode):
                input: maxon.GraphNode = self.GetPort(shader,'com.redshift3d.redshift4c4d.nodes.core.bumpmap.input')
                input_port.Connect(input)

                
        output: maxon.GraphNode = self.GetPort(shader,'com.redshift3d.redshift4c4d.nodes.core.bumpmap.out')
        
        if target_port is not None:
            if isinstance(target_port, maxon.GraphNode):
                output.Connect(target_port)

        else:
            material = self.GetRootBRDF()
            bump_port = self.GetPort(material,"com.redshift3d.redshift4c4d.nodes.core.standardmaterial.bump_input")
            output.Connect(bump_port)
        return shader

    # 创建Normal ==> OK
    def AddNormal(self, input_port: maxon.GraphNode = None, target_port: maxon.GraphNode = None, bump_mode: int = 1) -> maxon.GraphNode :
        """
        Adds a new Normal shader to the graph.

        """
        if self.graph is None:
            return None

        shader: maxon.GraphNode = self.graph.AddChild("", "com.chaos.vray_node.texnormalbump", maxon.DataDictionary())
        type_port = self.GetPort(shader, 'com.chaos.vray_node.texnormalbump.map_type')
        type_port.SetDefaultValue(bump_mode)

        if input_port:
            if isinstance(input_port, maxon.GraphNode):
                input: maxon.GraphNode = self.GetPort(shader,'com.chaos.vray_node.texnormalbump.bump_tex_color')
                try:
                    input_port.Connect(input)
                except:
                    pass
                
        output: maxon.GraphNode = self.GetPort(shader,'com.chaos.vray_node.texnormalbump.output.default')
        
        if target_port is not None:
            if isinstance(target_port, maxon.GraphNode):                
                try:
                    output.Connect(target_port)
                except:
                    pass

        return shader
    ### State ###

    ### Texture ###
    
    # 创建Remap ==> OK
    def AddRemap(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Remap shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.chaos.vray_node.texremap",
            input_ports = ['com.chaos.vray_node.texremap.input_color'],
            connect_inNodes = inputs,
            output_ports=['com.chaos.vray_node.texremap.output.default'], 
            connect_outNodes = target
            )

    # 创建maxon noise ==> OK
    def AddMaxonNoise(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new maxonnoise shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.chaos.vray_node.maxon_noise",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['com.chaos.vray_node.maxon_noise.output.default'], 
            connect_outNodes = target
            )

    # 创建Texture ==> OK
    def AddTexture(self, shadername :str = 'Texture', filepath: str = None, raw: bool = True, target_port: maxon.GraphNode = None) -> maxon.GraphNode :
        """
        Adds a new texture shader to the graph.
        """
        if self.graph is None:
            return None

        shader: maxon.GraphNode = self.graph.AddChild("", "com.chaos.vray_node.texbitmap", maxon.DataDictionary())
        self.SetName(shader,shadername)
        
        texPort: maxon.GraphNode = self.GetPort(shader,"com.chaos.vray_node.texbitmap.file")

        colorspacePort: maxon.GraphNode = self.GetPort(shader,"com.chaos.vray_node.texbitmap.rgb_primaries")

        # tex path
        if filepath is not None:
            texPort.SetDefaultValue(filepath)
        
        # color space
        if raw:
            colorspacePort.SetDefaultValue(0)
        else:
            colorspacePort.SetDefaultValue(1)
        
        # target connect
        if target_port:
            if isinstance(target_port, maxon.GraphNode):
                outPort: maxon.GraphNode = self.GetPort(shader,'com.chaos.vray_node.texbitmap.output.default')
                try:
                    outPort.Connect(target_port)
                except:
                    pass

        return shader

    def AddLayer(self, inputA: Union[str,maxon.GraphNode] = None, inputB: Union[str,maxon.GraphNode] = None, target: Union[str,maxon.GraphNode] = None, blend: int = 5) -> maxon.GraphNode :
        """
        Adds a new color correct shader to the graph.

        """
        layerNode = self.AddShader("com.chaos.vray_node.texlayeredmax")
        output:maxon.GraphNode = layerNode.GetOutputs().FindChild('com.chaos.vray_node.texlayeredmax.output.default')
        input1 = layerNode.GetInputs().FindChild('com.chaos.vray_node.texlayeredmax.texture_layers').FindChild("_0").FindChild("com.chaos.vray.portbundle.texture_layer.texture")
        input2 = layerNode.GetInputs().FindChild('com.chaos.vray_node.texlayeredmax.texture_layers').FindChild("_1").FindChild("com.chaos.vray.portbundle.texture_layer.texture")
        blendNode:maxon.GraphNode = layerNode.GetInputs().FindChild('com.chaos.vray_node.texlayeredmax.texture_layers').FindChild("_1").FindChild("com.chaos.vray.portbundle.texture_layer.blend_mode")
        blendNode.SetDefaultValue(blend)

        if inputA is not None:
            inputA.Connect(input1)
        if inputB is not None:
            inputB.Connect(input2)
        if target is not None:
            output.Connect(target)
        return layerNode
    
    ### Tree ###

    def AddBumpTree(self, shadername :str = 'Bump', filepath: str = None, bump_mode: int = 1, target_port: maxon.GraphNode = None) -> list[maxon.GraphNode] :
        """
        Adds a bump tree (tex + bump) to the graph.
        """
        if self.graph is None:
            return None
        
        # add        
        tex_node = self.AddTexture(shadername, filepath, True)
        tex_out = self.GetPort(tex_node, "com.chaos.vray_node.texbitmap.output.default")
        #tex_out = self.GetPort(tex_node, "com.redshift3d.redshift4c4d.nodes.core.texturesampler.outcolor")
        self.AddNormal(input_port=tex_out, target_port=target_port, bump_mode=bump_mode)


# todo
# coding more...