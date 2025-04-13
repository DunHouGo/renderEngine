from warnings import warn
import c4d
import maxon
import os
import random
from typing import Union,Optional

import Renderer
from Renderer.constants.centileo_id import *
from Renderer.utils.node_helper import NodeGraghHelper, EasyTransaction

# todo : not finished yet, wait for CentiLeoupdate their aov system.
class AOVHelper:

    """
    Custom helper to modify CentiLeo AOV.
    """

    def __init__(self, vp: c4d.documents.BaseVideoPost = None):
        
        if isinstance(vp, c4d.documents.BaseVideoPost):
            if vp.GetType() == int(Renderer.ID_CENTILEO):
                self.doc = vp.GetDocument()
                self.vp: c4d.documents.BaseVideoPost = vp
                self.vpname: str = self.vp.GetName()

        elif vp is None:
            self.doc: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
            self.vp: c4d.documents.BaseVideoPost = Renderer.GetVideoPost(self.doc, Renderer.ID_CENTILEO)
            self.vpname: str = self.vp.GetName()

        warn("This class is still in development, wait for CentiLeoupdate their aov system.")

    def __str__(self) -> str:
        return (f'<Class> {__class__.__name__} with videopost named {self.vpname}')


class MaterialHelper(NodeGraghHelper):

    # 初始化 ==> OK
    def __init__(self, material: Union[c4d.BaseMaterial, str] = None):

        # If we filled a str, we create a material with the name of the string
        if isinstance(material, str):
            self.material = self.CreateStandardSurface(material)

        # No argument filled, we create a material with default name
        elif material is None:
            self.material = self.CreateStandardSurface()

        else:
            self.material = material

        # Acess data
        self.graph = None
        self.nimbusRef = self.material.GetNimbusRef(Renderer.CL_NODESPACE)

        if isinstance(self.material, c4d.Material):
            nodeMaterial = self.material.GetNodeMaterialReference()
            self.graph: maxon.GraphModelInterface = nodeMaterial.GetGraph(Renderer.CL_NODESPACE)

        # Super the NodeGraghHelper
        super().__init__(self.material)

        # A final check
        if self.graph.IsNullValue():
            raise RuntimeError("Empty graph associated with CentiLeo node space.")
    
    def __str__(self):
        return (f"A CentiLeo {self.__class__.__name__} Instance with Material : {self.material.GetName()}")
    
    # =====  Material  ===== #

    # 创建材质 ==> OK
    #@staticmethod
    def Create(self, name: str = 'CentiLeo Material') -> c4d.BaseMaterial:
        """
        Creates a new CentiLeo Node Material with a NAME.

        Parameters
        ----------
        name : str
            The Material entry name.

        """
        material = c4d.BaseMaterial(c4d.Mmaterial)         
        material.SetName(name)

        # add graph
        nodeMaterial = material.GetNodeMaterialReference()
        nodeMaterial.CreateDefaultGraph(CL_NODESPACE)

        return material

    # 创建Cryptomatte
    @staticmethod                                               
    def CreateCryptomatte() -> c4d.BaseMaterial:
        pass
    
    # 创建Standard Surface
    # @staticmethod
    def CreateStandardSurface(self, name: str = 'Standard Surface'):
        """
        Creates a new Redshift Starndard Surface Material with a NAME.

        Args:
            name (str): Name of the Material

        Returns:
            Material: Redshift Material instance
        """    
        CentiLeoMaterial = self.Create(name)
        hide_ports = ['diffuse_weight', 'diffuse_rough',
                    'refl1_weight','refl1_color','refl1_ior','refl1_aniso','refl1_rotation','refl2_rough',
                    'refl2_weight','refl2_color','refl2_ior','refl2_aniso','refl2_rotation','refl2_color',
                    'sss1_weight','sss1_radius','sss2_weight','sss2_radius','sss3_weight','sss3_radius',
                    'transmission_ior','absorb_color','absorb_radius'
                    ]
        hide_param = ["enabled_bump"]

        with EasyTransaction(CentiLeoMaterial) as ts:
            # standard_surface = ts.AddShader("com.centileo.node.material")
            standard_surface = ts.GetRootBRDF()
            surface_out = ts.GetPort(standard_surface,'result')
            end_node = ts.GetOutput()
            end_shader_in = ts.GetPort(end_node,'surface_material')
            surface_out.Connect(end_shader_in)

            # specular color white
            # NOTE color is in linear sRGB space
            ts.SetShaderValue(standard_surface, "diffuse_color", maxon.Color(0.7, 0.7, 0.7))
            ts.SetShaderValue(standard_surface, "refl1_rough", 0.2)

            for port in hide_ports:
                ts.RemovePort(standard_surface, port)

            for param in hide_param:
                ts.SetShaderValue(standard_surface, param, True)

        return ts.material

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

    # 创建PBR材质 ==> ok
    #todo
    def SetupTextures(self, tex_data: dict = None, mat_name: Optional[str] = None):
        """
        Setup a pbr material with given or selected texture.
        """
        
        isSpecularWorkflow = False
        if 'Specular' in list(tex_data.keys()):
            isSpecularWorkflow = True            
 
        # modification has to be done within a transaction
        with EasyTransaction(self):

            # Find brdf node (in this case : standard surface)
            # 查找Standard Surface节点
            standard_surface = self.GetRootBRDF()
            output_node = self.GetOutput()

            # Change a shader name
            # 更改Standard Surface节点名称
            self.SetName(standard_surface,f'{mat_name} Shader')

            # get ports
            albedoPort = self.GetPort(standard_surface,'base_color')
            specularPort = self.GetPort(standard_surface,'specular_color')
            roughnessPort = self.GetPort(standard_surface,'specular_roughness')
            metalnessPort = self.GetPort(standard_surface,'metalness')
            opacityPort = self.GetPort(standard_surface,'opacity')
            reflectionPort = self.GetPort(standard_surface,'transmission_color')

            try:
                # Base Color            
                if "AO" in tex_data:
                    aoNode = self.AddTexture(filepath=tex_data['AO'], shadername="AO")
                    if "Diffuse" in tex_data:
                        albedoNode = self.AddTextureTree(filepath=tex_data['Diffuse'], shadername="Albedo", raw=False, color_mode=True, color_mutiplier=aoNode, target_port=albedoPort)
                else:
                    albedoNode = self.AddTextureTree(filepath=tex_data['Diffuse'], shadername="Albedo", raw=False, target_port=albedoPort)

                
                if isSpecularWorkflow:
                    if "Specular" in tex_data:
                        self.AddTextureTree(filepath=tex_data['Specular'], shadername="Specular", raw=False, color_mode=True, target_port=specularPort)
                    
                    if "Glossiness" in tex_data:
                        self.AddTextureTree(filepath=tex_data['Glossiness'], shadername="Glossiness", target_port=roughnessPort)
                        isglossinessPort = self.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refl_isglossiness')
                        self.SetPortData(isglossinessPort, True)

                    elif "Roughness" in tex_data:
                        roughnessNode = self.AddTextureTree(filepath=tex_data['Roughness'], shadername="Roughness", target_port=roughnessPort)

                else:
                    if "Metalness" in tex_data:
                        aoNode = self.AddTexture(filepath=tex_data['Metalness'], shadername="Metalness",target_port=metalnessPort)

                    if "Roughness" in tex_data:
                        roughnessNode = self.AddTextureTree(filepath=tex_data['Roughness'], shadername="Roughness", target_port=roughnessPort)

                    elif "Glossiness" in tex_data:
                        self.AddTextureTree(filepath=tex_data['Glossiness'], shadername="Glossiness", target_port=roughnessPort)
                        isglossinessPort = self.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refl_isglossiness')
                        self.SetPortData(isglossinessPort, True)

                if "Normal" in tex_data:
                    self.AddBumpTree(filepath=tex_data['Normal'], shadername="Normal")
                
                if "Bump" in tex_data and "Normal" not in tex_data:  
                    self.AddBumpTree(filepath=tex_data['Bump'], shadername="Bump")
                
                if "Displacement" in tex_data:
                    self.AddDisplacementTree(filepath=tex_data['Displacement'], shadername="Displacement")

                if "Alpha" in tex_data:
                    self.AddTexture(filepath=tex_data['Alpha'], shadername="Alpha",target_port=opacityPort)

                if "Translucency" in tex_data:
                    self.AddTexture(filepath=tex_data['Translucency'], shadername="Translucency", raw=False, target_port=reflectionPort)

                elif "Transmission" in tex_data:
                    self.AddTexture(filepath=tex_data['Transmission'], shadername="Transmission", raw=True, target_port=reflectionPort)

                self.material.SetName(mat_name)
                
            except Exception as e:
                raise RuntimeError (f"Unable to setup texture with {e}")
            
        # 将Standard Surface材质引入当前Document
        self.InsertMaterial()
        # 将Standard Surface材质设置为激活材质
        self.SetActive()
        
        return self.material

    def AddNode(self, nodeId:str):
        """
        Adds a new shader to the graph.

        Parameters
        ----------
        nodeId : str
            The CentiLeo node entry name.
        """
        if self.graph is None:
            return None

        shader = self.graph.AddChild("", "com.centileo.node." + nodeId, maxon.DataDictionary())


        return shader

    def GetRootBRDF(self, filter: Union[str,int] = 0) -> maxon.GraphNode:
        """
        Returns the very first brdf shader connect to output

        Args:
            filter (Union[str,int], optional): filter to get the object, fill ``str`` to filter by name, fill ``int`` to filter by index. Defaults to 0.

        Returns:
            maxon.GraphNode: the BRDF node
        """

        standard_mat: str = "com.centileo.node.material"

        endNode = self.GetOutput()
        if not endNode: return None

        # only one direct brdf
        predecessor = list()
        maxon.GraphModelHelper.GetDirectPredecessors(endNode, maxon.NODE_KIND.NODE, predecessor)
        rootshader = [i for i in predecessor if self.GetAssetId(i) == standard_mat]
        if rootshader:
            return rootshader[0]
        
        # find brdf by filter
        else:
            nodes = self.GetNodes(standard_mat)
            # By Name
            if isinstance(filter, str):
                for node in nodes:
                    if self.GetName(node) == filter:
                        return node
            elif isinstance(filter, int):
                return nodes[filter]

    ### Color ###

    # 创建color correct ==> OK
    def AddColorCorrect(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new color correct shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.centileo.node.colorcorrect",
            input_ports = ['input_map'],
            connect_inNodes = inputs,
            output_ports=['result'], 
            connect_outNodes = target
            )
    
    ### Operator ###
   
    # 创建Math(Float64) ==> OK
    def AddMath(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Math shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.centileo.node.math",
            input_ports = ['math_a','math_b'],
            connect_inNodes = inputs,
            output_ports=['result'], 
            connect_outNodes = target
            )

    # 创建displacement ==> OK
    def AddDisplacement(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new displacement shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.centileo.node.displacement",
            input_ports = ['displacement_map'],
            connect_inNodes = inputs,
            output_ports=['result'], 
            connect_outNodes = target
            )

    # 创建Layer Rgba ==> OK
    def AddLayer(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Layer Rgba shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.centileo.node.layer",
            input_ports = ['color1','color2',"color3", "color4", "color5", "color6", "color7"],
            connect_inNodes = inputs,
            output_ports=['result'], 
            connect_outNodes = target
            )

    ### State ###

    # 创建Curvature ==> OK
    def AddCurvature(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Curvature shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.centileo.node.curvature",
            input_ports = ['distance_map'],
            connect_inNodes = None,
            output_ports=['result'], 
            connect_outNodes = target
            )
    
    # 创建Flakes ==> OK
    def AddFlakes(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Flakes shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.centileo.node.flakes",
            input_ports = ['uvw_map'],
            connect_inNodes = None,
            output_ports=['result'], 
            connect_outNodes = target
            )
    
    ### Texture ###
    
    # 创建ramp ==> OK
    def AddRamp(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new ramp shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.centileo.node.gradientnode",
            input_ports = ['input_map'],
            connect_inNodes = inputs,
            output_ports=['result'], 
            connect_outNodes = target
            )
    

    # 创建TriPlanar ==> OK
    def AddTriPlanar(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new TriPlanar shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.centileo.node.triplanar",
            input_ports = ['map_yz', 'map_zx', 'map_xy'],
            connect_inNodes = inputs,
            output_ports=['result'], 
            connect_outNodes = target
            )
    
    # 创建noise ==> OK
    def AddNoise(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new maxonnoise shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.centileo.node.noise",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['result'], 
            connect_outNodes = target
            )   
    
    # 创建Texture ==> OK
    def AddTexture(self, shadername :str = 'Texture', filepath: str = None, raw: bool = True, target_port: maxon.GraphNode = None) -> maxon.GraphNode :
        """
        Adds a new texture shader to the graph.
        """
        if self.graph is None:
            return None

        shader: maxon.GraphNode = self.graph.AddChild("", "com.centileo.node.bitmap", maxon.DataDictionary())
        self.SetName(shader,shadername)
        
        texPort: maxon.GraphNode = self.GetPort(shader,"filename")
        gammaPort: maxon.GraphNode = self.GetPort(shader,"gamma")

        # colorspacePort: maxon.GraphNode = self.GetPort(shader,"color_space")

        # tex path
        if filepath is not None:
            self.SetPortData(texPort,filepath)
        
        # color space
        if raw:
            self.SetPortData(gammaPort, 1)
        else:
            self.SetPortData(gammaPort, 2.2)
        
        # target connect
        if target_port:
            if isinstance(target_port, maxon.GraphNode):
                outPort: maxon.GraphNode = self.GetPort(shader,'output')
                outPort.Connect(target_port)

        return shader

    # 创建Normal ==> OK
    def AddNormal(self, shadername :str = 'Texture', filepath: str = None, target: Union[str,maxon.GraphNode] = None) -> maxon.GraphNode :
        """
        Adds a new Normal shader to the graph.

        """
        shader = self.AddTexture(shadername,filepath,True,target)
        normalPort: maxon.GraphNode = self.GetPort(shader,"normal_map_enabled")
        self.SetShaderValue(shader,normalPort,True)
        return shader

    ### Tree ###

    # NEW
    def AddTextureTree(self, shadername :str = 'Texture', filepath: str = None, raw: bool = True, triplaner_node: bool = False, target_port: maxon.GraphNode = None) -> list[maxon.GraphNode] :
        """
        Adds a texture tree (tex + color correction + ramp) to the graph.
        """
        if self.graph is None:
            return None
        
        # add
        tex_node = self.AddTexture(shadername, filepath, raw)
        cc_node = self.AddColorCorrect(target=target_port)

        if triplaner_node:
            triplaner_node = self.AddTriPlanar(self.GetPort(tex_node,"result"), self.GetPort(cc_node,"input_map"))
        else:
            self.AddConnection(tex_node, "result", cc_node, "input_map")

        return tex_node

    # NEW
    def AddDisplacementTree(self, shadername :str = 'Displacement', filepath: str = None, triplaner_node: bool = False) -> list[maxon.GraphNode] :
        """
        Adds a displacement tree (tex + displacement) to the graph.
        """
        if self.graph is None:
            return None
        
        # add        
        tex_node = self.AddTexture(shadername, filepath, True)
        tex_out = self.GetPort(tex_node, "result")
        endNode = self.GetOutput()
        disp_port = self.GetPort(endNode,'displacement_map')
        if triplaner_node:
            triplaner_node = self.AddTriPlanar(tex_out)
            tex_out = self.GetPort(triplaner_node, self.GetConvertOutput(triplaner_node))
        self.AddDisplacement(tex_out,disp_port)

    # 连接到Output Surface接口
    def AddtoOutput(self, soure_node, outPort):
        """
        Connects the given shader to RS Output Surface port.

        Parameters
        ----------
        soure_node : maxon.frameworks.graph.GraphNode
            The source shader node.
        outPort : str
            Output port id of the source shader node.
        """
        endNode = self.GetOutput()
        endNodePort = self.GetPort(endNode, "surface_material")
        return self.AddConnection(soure_node, outPort, endNode, endNodePort) is not None

    # 连接到Output置换接口
    def AddtoDisplacement(self, soure_node, outPort):
        """
        Connects the given shader to AR Output Displacement port.

        Parameters
        ----------
        soure_node : maxon.frameworks.graph.GraphNode
            The source shader node.
        outPort : str
            Output port id of the source shader node.
        """
        rsoutput = self.GetOutput()
        rsoutputPort = self.GetPort(rsoutput, "displacement_map")
        return self.AddConnection(soure_node, outPort, rsoutput, rsoutputPort) is not None


# todo
# coding more...