# coding=utf-8
import c4d
import maxon
from typing import Union,Optional

from ..constants import *
from ..utils.node_helper import NodeGraghHelper
from ..utils import EasyTransaction

def IsArnoldMaterial(material: c4d.BaseMaterial) -> bool:
    if material is None:
        return False
    return material.CheckType(ARNOLD_SHADER_NETWORK) or material.GetNodeMaterialReference().HasSpace(AR_NODESPACE)

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
        self.nimbusRef = self.material.GetNimbusRef(AR_NODESPACE)

        if isinstance(self.material, c4d.Material):
            nodeMaterial = self.material.GetNodeMaterialReference()
            self.graph: maxon.GraphModelInterface = nodeMaterial.GetGraph(AR_NODESPACE)

        # Super the NodeGraghHelper
        super().__init__(self.material)

        # A final check
        if self.graph.IsNullValue():
            raise RuntimeError("Empty graph associated with Arnold node space.")
    
    def __str__(self):
        return (f"A Arnold {self.__class__.__name__} Instance with Material : {self.material.GetName()}")
    
    # =====  Material  ===== #

    # 创建材质 ==> OK
    #@staticmethod
    def Create(self, name: str = 'Arnold Material') -> c4d.BaseMaterial:
        """
        Creates a new Arnold Node Material with a NAME.

        Parameters
        ----------
        name : str
            The Material entry name.

        """
        material = c4d.BaseMaterial(c4d.Mmaterial)         
        material.SetName(name)

        # add graph
        nodeMaterial = material.GetNodeMaterialReference()
        nodeMaterial.CreateDefaultGraph(AR_NODESPACE)

        return material

    # 创建Cryptomatte
    @staticmethod                                               
    def CreateCryptomatte() -> c4d.BaseMaterial:
        arnoldMaterial = MaterialHelper.Create('Cryptomatte')

        with EasyTransaction(arnoldMaterial) as ts:
            crypto = ts.AddShader("com.autodesk.arnold.shader.cryptomatte")
            crypto_out = ts.GetPort(crypto)
            end_node = ts.GetOutput()
            end_shader_in = ts.GetPort(end_node,'shader')
            crypto_out.Connect(end_shader_in)

        return ts.material
    
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
        arnoldMaterial = self.Create(name)
        exp_ports = ['metalness',
                    'specular_color','specular_roughness',
                    'transmission','transmission_color',
                    'emission','emission_color',
                    'normal', 'opacity'
                    ]

        with EasyTransaction(arnoldMaterial) as ts:
            standard_surface = ts.AddShader("com.autodesk.arnold.shader.standard_surface")
            surface_out = ts.GetPort(standard_surface,'output')
            end_node = ts.GetOutput()
            end_shader_in = ts.GetPort(end_node,'shader')
            surface_out.Connect(end_shader_in)

            # specular color white
            # NOTE color is in linear sRGB space
            ts.SetShaderValue(standard_surface, "base_color", maxon.Color(0.7, 0.7, 0.7))
            ts.SetShaderValue(standard_surface, "specular_roughness", 0.2)

            for port in exp_ports:
                ts.AddPort(standard_surface, port)

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
            The Arnold node entry name.
        """
        if self.graph is None:
            return None

        shader = self.graph.AddChild("", "com.autodesk.arnold.shader." + nodeId, maxon.DataDictionary())


        return shader

    def GetRootBRDF(self, filter: Union[str,int] = 0) -> maxon.GraphNode:
        """
        Returns the very first brdf shader connect to output

        Args:
            filter (Union[str,int], optional): filter to get the object, fill ``str`` to filter by name, fill ``int`` to filter by index. Defaults to 0.

        Returns:
            maxon.GraphNode: the BRDF node
        """

        standard_mat: str = "com.autodesk.arnold.shader.standard_surface"

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

    # 创建Color jitter ==> OK
    def AddColorJitter(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Color jitter shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.color_jitter",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )

    # 创建shuffle ==> OK
    def AddShuffle(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new shuffle shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.shuffle",
            input_ports = ['color'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建Color convert ==> OK
    def AddColorConvert(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Color Convert shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.color_convert",
            input_ports = ['color'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )

    # 创建color correct ==> OK
    def AddColorCorrect(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new color correct shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.color_correct",
            input_ports = ['color'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    ### Operator ###
   
    # 创建Math Add(Float64) ==> OK
    def AddMathAdd(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Math Add shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.add",
            input_ports = ['input1','input2'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
     
    # 创建Math Sub(Float64) ==> OK
    def AddMathSub(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Math Sub shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.subtract",
            input_ports = ['input1','input2'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )

    # 创建Math Mul(Float64) ==> OK
    def AddMathMul(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Math Mul shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.multiply",
            input_ports = ['input1','input2'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )

    # 创建Math Div(Float64) ==> OK
    def AddMathDiv(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Math Div shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.divide",
            input_ports = ['input1','input2'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建Math Negate ==> OK
    def AddMathNegate(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Negate shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.negate",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )

    # 创建Math Range ==> OK
    def AddMathRange(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Range shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.range",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建Math normalize ==> OK
    def AddMathNormalize(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new normalize shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.normalize",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建Math value ==> OK
    def AddMathvalue(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new value shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.value",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
        
    # 创建Math compare ==> OK
    def AddMathCompare(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new compare shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.compare",
            input_ports = ['input1','input2'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )        
        
    # 创建Math abs ==> OK
    def AddMathAbs(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new abs shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.abs",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )        
        
    # 创建Math Min ==> OK
    def AddMathMin(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Min shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.min",
            input_ports = ['input1','input2','input3','input4','input5','input6','input7','input8'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
        
    # 创建Math Max ==> OK
    def AddMathMax(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Max shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.max",
            input_ports = ['input1','input2'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
        
    ### Bump ###
    # 创建Normal ==> OK
    def AddNormal(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Normal shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.normal_map",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
        
    # 创建Bump ==> OK
    def AddBump2d(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Bump shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.bump2d",
            input_ports = ['bump_map'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
        
    def AddBump3d(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Bump shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.bump3d",
            input_ports = ['bump_map'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
         
    # 创建displacement ==> OK
    def AddDisplacement(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new displacement shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.displacement",
            input_ports = ['normal_displacement_input','vector_displacement_input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )

    # 创建Layer Rgba ==> OK
    def AddLayerRgba(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Layer Rgba shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.bump3d",
            input_ports = ['input1','input2'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
        
    # 创建Layer float ==> OK
    def AddLayerFloat(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Layer float shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.layer_float",
            input_ports = ['input1','input2'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
   
    # 创建Round Corners ==> OK
    def AddRoundCorner(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Round Corners shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.layer_float",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    ### State ###

    # 创建Fresnel ==> OK
    def AddFresnel(self,  target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Fresnel shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.facing_ratio",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建AO ==> OK
    def AddAO(self,  target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new AO shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.ambient_occlusion",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['output'], 
            connect_outNodes = target
            )
   
    # 创建Curvature ==> OK
    def AddCurvature(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Curvature shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.curvature",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建Flakes ==> OK
    def AddFlakes(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Flakes shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.flakes",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    ### Texture ###
    
    # 创建ramp ==> OK
    def AddRampRGB(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new ramp shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.ramp_rgb",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建scalar ramp ==> OK
    def AddRampFloat(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new scalar ramp shader to the graph.        

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.ramp_float",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建TriPlanar ==> OK
    def AddTriPlanar(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new TriPlanar shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.triplanar",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建maxon noise ==> OK
    def AddMaxonNoise(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new maxonnoise shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.c4d_noise",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['output'], 
            connect_outNodes = target
            )   
    
    # 创建Texture ==> OK
    def AddTexture(self, shadername :str = 'Texture', filepath: str = None, raw: bool = True, target_port: maxon.GraphNode = None) -> maxon.GraphNode :
        """
        Adds a new texture shader to the graph.
        """
        if self.graph is None:
            return None

        shader: maxon.GraphNode = self.graph.AddChild("", "com.autodesk.arnold.shader.image", maxon.DataDictionary())
        self.SetName(shader,shadername)
        
        texPort: maxon.GraphNode = self.GetPort(shader,"filename")

        colorspacePort: maxon.GraphNode = self.GetPort(shader,"color_space")

        # tex path
        if filepath is not None:
            self.SetPortData(texPort, filepath)
        
        # color space
        if raw:
            self.SetPortData(colorspacePort, "raw")
        else:
            self.SetPortData(colorspacePort, "sRGB")
        
        # target connect
        if target_port:
            if isinstance(target_port, maxon.GraphNode):
                outPort: maxon.GraphNode = self.GetPort(shader,'output')
                outPort.Connect(target_port)

        return shader

    def AddGobo(self,inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        return self.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.gobo",
            input_ports = ['slidemap'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    ### Tree ###

    # NEW
    def AddTextureTree(self, shadername :str = 'Texture', filepath: str = None, raw: bool = True, color_mode: bool = False,scaleramp: bool = False,color_mutiplier: maxon.GraphNode = None,triplaner_node: bool = False, target_port: maxon.GraphNode = None) -> list[maxon.GraphNode] :
        """
        Adds a texture tree (tex + color correction + ramp) to the graph.
        """
        if self.graph is None:
            return None
        
        # add
        tex_node = self.AddTexture(shadername, filepath, raw)
        color_mutiplier_port = self.GetPort(tex_node,"multiply")
        
        if color_mode:
            cc_node = self.AddColorCorrect(target=target_port)
        
        else:
            cc_node = self.AddColorCorrect()
            if scaleramp:
                ramp_node = self.AddRampFloat(target=target_port)
            else:
                ramp_node = self.AddRampRGB(target=target_port)

        if triplaner_node:
            triplaner_node = self.AddTriPlanar(self.GetPort(tex_node,"output"), self.GetPort(cc_node,"input"))
        else:
            self.AddConnection(tex_node, "output", cc_node, "input")
        
        if not color_mode:
            if scaleramp:
                self.AddConnection(cc_node, "output", ramp_node, "input")
            else:
                self.AddConnection(cc_node, "output", ramp_node, "input")
        
        if color_mutiplier:
            self.AddConnection(color_mutiplier, "output", tex_node, color_mutiplier_port)
        
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
        tex_out = self.GetPort(tex_node, "output")
        endNode = self.GetOutput()
        disp_port = self.GetPort(endNode,'displacement')
        if triplaner_node:
            triplaner_node = self.AddTriPlanar(tex_out)
            tex_out = self.GetPort(triplaner_node, self.GetConvertOutput(triplaner_node))
        self.AddDisplacement(tex_out,disp_port)

    # NEW
    def AddBumpTree(self, shadername :str = 'Bump', filepath: str = None, triplaner_node: bool = False) -> list[maxon.GraphNode] :
        """
        Adds a bump tree (tex + bump) to the graph.
        """
        if self.graph is None:
            return None
        
        tex_node = self.AddTexture(shadername, filepath, True)
        tex_out = self.GetPort(tex_node, "output")
        brdf = self.GetRootBRDF()
        disp_port = self.GetPort(brdf,'normal')
        if triplaner_node:
            triplaner_node = self.AddTriPlanar(tex_out)
            tex_out = self.GetPort(triplaner_node, self.GetConvertOutput(triplaner_node))
        self.AddBump2d(tex_out,disp_port)
        
    # NEW
    def AddNormalTree(self, shadername :str = 'Normal', filepath: str = None,triplaner_node: bool = False) -> list[maxon.GraphNode] :
        """
        Adds a Normal tree (tex + Normal) to the graph.
        """
        if self.graph is None:
            return None
        
        tex_node = self.AddTexture(shadername, filepath, True)
        tex_out = self.GetPort(tex_node, "output")
        brdf = self.GetRootBRDF()
        disp_port = self.GetPort(brdf,'normal')
        if triplaner_node:
            triplaner_node = self.AddTriPlanar(tex_out)
            tex_out = self.GetPort(triplaner_node, self.GetConvertOutput(triplaner_node))
        self.AddNormal(tex_out,disp_port)
        
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
        endNodePort = self.GetPort(endNode, "shader")
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
        rsoutputPort = self.GetPort(rsoutput, "displacement")
        return self.AddConnection(soure_node, outPort, rsoutput, rsoutputPort) is not None

__all__ = [
    "MaterialHelper", 
    "IsArnoldMaterial",
]
