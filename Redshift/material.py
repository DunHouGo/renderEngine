import c4d
import maxon
from ..constants import *
from ..utils.node_helper import NodeGraghHelper
from ..utils import EasyTransaction

from typing import Union, TypeAlias 
NodeInput: TypeAlias = Union[str, maxon.GraphNode]

def IsRedshiftMaterial(material: c4d.BaseMaterial) -> bool:
    if material is None:
        return False
    return material.CheckType(REDSHIFT_SHADER_NETWORK) or material.GetNodeMaterialReference().HasSpace(RS_NODESPACE)


class MaterialHelper(NodeGraghHelper):
    """
    Custom helper to easier modify Redshift Material.
    """

    standard_mat = "com.redshift3d.redshift4c4d.nodes.core.standardmaterial"
    redshift_mat = "com.redshift3d.redshift4c4d.nodes.core.material"
    openpbr_mat = "com.redshift3d.redshift4c4d.nodes.core.openpbrmaterial"
    valid_mat = [standard_mat, redshift_mat, openpbr_mat]

    # 初始化 ==> OK
    def __init__(self, material: c4d.BaseMaterial|str = None):
        
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
        self.nimbusRef = self.material.GetNimbusRef(RS_NODESPACE)

        if isinstance(self.material, c4d.Material):
            nodeMaterial = self.material.GetNodeMaterialReference()
            self.graph: maxon.GraphModelInterface = nodeMaterial.GetGraph(RS_NODESPACE)

        # Super the NodeGraghHelper
        super().__init__(self.material)

        # A final check
        if self.graph.IsNullValue():
            raise RuntimeError("Empty graph associated with Redshift node space.")

    def __str__(self):
        return (f"A Redshift {self.__class__.__name__} Instance with Material : {self.material.GetName()}")
    
    # =====  Material  ===== #

    # 创建材质(Standard Surface) ==> OK
    def Create(self, name: str = "Standard Surface") -> c4d.BaseMaterial:
        """
        Creates a new Redshift Node Material with a NAME.

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
        nodeMaterial.CreateDefaultGraph(RS_NODESPACE)  

        with EasyTransaction(material) as tr:

            # ports
            brdf: maxon.GraphNode = tr.GetRootBRDF()
            tr.SetName(brdf,'Standard Surface')
            tr.AddPort(brdf,"com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refr_color")
            tr.AddPort(brdf,"com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refr_weight")
            tr.AddPort(brdf,"com.redshift3d.redshift4c4d.nodes.core.standardmaterial.emission_weight")
            tr.AddPort(brdf,"com.redshift3d.redshift4c4d.nodes.core.standardmaterial.emission_color")
            tr.AddPort(brdf,"com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refl_color")

        return material

    # 创建RS Material
    @staticmethod
    def CreateRSMaterial(name):
        """
        Creates a new Redshift Material with a NAME.

        Args:
            name (str): Name of the Material

        Returns:
            Material: Redshift Material instance
        """    
        standardMaterial = MaterialHelper.Create(name)
        if standardMaterial is None or standardMaterial is None:
            raise Exception("Failed to create Redshift Standard Surface Material")

        with EasyTransaction(standardMaterial) as tr:
            oldrs = tr.GetRootBRDF()

            output_inport = tr.GetPort(tr.GetOutput(), "com.redshift3d.redshift4c4d.node.output.surface")
            tr.RemoveShader(oldrs)
            rsMaterial = tr.AddRSMaterial(target=output_inport)
            tr.SetName(rsMaterial,'RS Material')
            tr.SetShaderValue(rsMaterial,'com.redshift3d.redshift4c4d.nodes.core.material.refl_roughness',0.2)

            # ports
            #standardMaterial.ExposeUsefulPorts()
            tr.AddPort(tr.GetRootBRDF(),'com.redshift3d.redshift4c4d.nodes.core.material.transl_color')
            tr.AddPort(tr.GetRootBRDF(),'com.redshift3d.redshift4c4d.nodes.core.material.transl_weight')
        return standardMaterial

    # 暴露常用接口
    def ExposeUsefulPorts(self):
        if self.graph is None:
            raise ValueError("can't retrieve the graph of this nimbus ref")
        
        # expose port callback
        def ExposeHidePorts(node):
            transmission_color = node.GetInputs().FindChild("com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refr_color")
            transmission = node.GetInputs().FindChild("com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refr_weight")
            emission = node.GetInputs().FindChild("com.redshift3d.redshift4c4d.nodes.core.standardmaterial.emission_weight")
            emission_color = node.GetInputs().FindChild("com.redshift3d.redshift4c4d.nodes.core.standardmaterial.emission_color")
            refl_color = node.GetInputs().FindChild("com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refl_color")
            # Display the port in the node editor
            with self.graph.BeginTransaction() as transaction:
                refl_color.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(False))
                transmission.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(False))
                transmission_color.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(False))
                emission.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(False))
                emission_color.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(False))
                transaction.Commit()
            return True
        
        # Do Expose defined ports on standard_surface
        maxon.GraphModelHelper.FindNodesByAssetId(self.graph, "com.redshift3d.redshift4c4d.nodes.core.standardmaterial", False, ExposeHidePorts)

        return self.material

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
    # todo fix with new version
    def SetupTextures(self, tex_data: dict = None, mat_name: str = None):
        """
        Setup a pbr material with given or selected texture.
        """
        
        isSpecularWorkflow = False
        if 'Specular' in list(tex_data.keys()):
            isSpecularWorkflow = True            

        redshiftMaterial = self
        # modification has to be done within a transaction
        with EasyTransaction(redshiftMaterial) as tr:

            # Find brdf node (in this case : standard surface)
            # 查找Standard Surface节点
            standard_surface = redshiftMaterial.GetRootBRDF()
            output_node = redshiftMaterial.GetOutput()

            # Change a shader name
            # 更改Standard Surface节点名称
            redshiftMaterial.SetName(standard_surface, f'{mat_name} Shader')

            # get ports
            albedoPort = redshiftMaterial.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.base_color')
            specularPort = redshiftMaterial.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refl_color')
            roughnessPort = redshiftMaterial.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refl_roughness')
            metalnessPort = redshiftMaterial.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.metalness')
            opacityPort = redshiftMaterial.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.opacity_color')
            reflectionPort = redshiftMaterial.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refr_color')

            try:
                # Base Color            
                if "AO" in tex_data:
                    aoNode = self.AddTexture(filepath=tex_data['AO'], shadername="AO")
                    if "Diffuse" in tex_data:
                        albedoNode = self.AddTextureTree(filepath=tex_data['Diffuse'], shadername="Albedo", raw=False, color_mode=True, color_mutiplier=aoNode, target_port=albedoPort)
                else:
                    albedoNode = self.AddTextureTree(filepath=tex_data['Diffuse'], shadername="Albedo", raw=False, color_mode=True, target_port=albedoPort)

                
                if isSpecularWorkflow:
                    if "Specular" in tex_data:
                        self.AddTextureTree(filepath=tex_data['Specular'], shadername="Specular", raw=False, color_mode=True, target_port=specularPort)
                    
                    if "Glossiness" in tex_data:
                        self.AddTextureTree(filepath=tex_data['Glossiness'], shadername="Glossiness", target_port=roughnessPort)
                        isglossinessPort = redshiftMaterial.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refl_isglossiness')

                        tr.SetPortData(isglossinessPort, True)

                    elif "Roughness" in tex_data:
                        roughnessNode = self.AddTextureTree(filepath=tex_data['Roughness'], shadername="Roughness", scaleramp=True, target_port=roughnessPort)

                else:
                    if "Metalness" in tex_data:
                        aoNode = self.AddTexture(filepath=tex_data['Metalness'], shadername="Metalness",target_port=metalnessPort)

                    if "Roughness" in tex_data:
                        roughnessNode = self.AddTextureTree(filepath=tex_data['Roughness'], shadername="Roughness", scaleramp=True, target_port=roughnessPort)

                    elif "Glossiness" in tex_data:
                        self.AddTextureTree(filepath=tex_data['Glossiness'], shadername="Glossiness", scaleramp=True, target_port=roughnessPort)
                        isglossinessPort = redshiftMaterial.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refl_isglossiness')
 
                        tr.SetPortData(isglossinessPort, True)                  

                if "Normal" in tex_data:
                    self.AddBumpTree(filepath=tex_data['Normal'], shadername="Normal")
                
                if "Bump" in tex_data and "Normal" not in tex_data:  
                    self.AddBumpTree(filepath=tex_data['Bump'], shadername="Bump",bump_mode=0)
                
                if "Displacement" in tex_data:
                    self.AddDisplacementTree(filepath=tex_data['Displacement'], shadername="Displacement")

                if "Alpha" in tex_data:
                    self.AddTexture(filepath=tex_data['Alpha'], shadername="Alpha",target_port=opacityPort)

                if "Translucency" in tex_data:
                    self.AddTexture(filepath=tex_data['Translucency'], shadername="Translucency", raw=False, target_port=reflectionPort)

                elif "Transmission" in tex_data:
                    self.AddTexture(filepath=tex_data['Transmission'], shadername="Transmission", raw=True, target_port=reflectionPort)

            except Exception as e:
                raise RuntimeError (f"Unable to setup texture with {e}")
            
            self.material.SetName(mat_name)
            
        # 将Standard Surface材质引入当前Document
        redshiftMaterial.InsertMaterial()
        # 将Standard Surface材质设置为激活材质
        redshiftMaterial.SetActive()
        
        return redshiftMaterial.material
    
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

    def GetRootBRDF(self, filter: str|int = 0) -> maxon.GraphNode:
        """
        Returns the very first brdf shader connect to output

        Args:
            filter (Union[str,int], optional): filter to get the object, fill ``str`` to filter by name, fill ``int`` to filter by index. Defaults to 0.

        Returns:
            maxon.GraphNode: the BRDF node
        """

        endNode = self.GetOutput()
        if not endNode: return None

        # only one direct brdf
        predecessor = list()
        maxon.GraphModelHelper.GetDirectPredecessors(endNode, maxon.NODE_KIND.NODE, predecessor)
        rootshader = [i for i in predecessor if self.GetAssetId(i) in self.valid_mat]
        if rootshader:
            return rootshader[0]

        # find brdf by filter
        else:
            nodes = []
            for i in self.valid_mat:
                nodes += self.GetNodes(i)
            # By Name
            if isinstance(filter, str):
                for node in nodes:
                    if self.GetName(node) == filter:
                        return node
            elif isinstance(filter, int):
                return nodes[filter]

    ### Material ###
    
    def AddStandardMaterial(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Standard Material shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.standardmaterial",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.standardmaterial.base_color'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.standardmaterial.outcolor'], 
            connect_outNodes = target
            )
    
    def AddRSMaterial(self,  inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new RSMaterial shader to the graph.

        """

        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.material",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.material.diffuse_color'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.material.outcolor'], 
            connect_outNodes = target
            )
    
    def AddMaterialBlender(self,  inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Material Blender shader to the graph.

        """

        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.materialblender",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.materialblender.basecolor',
                           'com.redshift3d.redshift4c4d.nodes.core.materialblender.layercolor1',
                           'com.redshift3d.redshift4c4d.nodes.core.materialblender.blendcolor1'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.materialblender.out'], 
            connect_outNodes = target
            )
    
    def AddMaterialLayer(self,  inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Material Layer shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.materiallayer",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.materiallayer.basecolor',
                           'com.redshift3d.redshift4c4d.nodes.core.materiallayer.layercolor',
                           'com.redshift3d.redshift4c4d.nodes.core.materiallayer.layermask',
                           'com.redshift3d.redshift4c4d.nodes.core.materiallayer.layerblendtype'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.materiallayer.out'], 
            connect_outNodes = target
            )

    def AddIncandescent(self,  inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Incandescent Material shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.incandescent",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.incandescent.color'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.incandescent.outcolor'], 
            connect_outNodes = target
            )
    
    def AddSprite(self,  inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Sprite Material shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.sprite",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.sprite.input'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.sprite.outcolor'], 
            connect_outNodes = target
            )
    
    ### Color ###

    # 创建Invert ==> OK
    def AddInvert(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new invert shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rsmathinv",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rsmathinv.input'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rsmathinv.out'], 
            connect_outNodes = target
            )

    # 创建Color Constant ==> OK
    def AddColorConstant(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Color Constant shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rscolorconstant",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rscolorconstant.color'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rscolorconstant.outcolor'], 
            connect_outNodes = target
            )
    
    # 创建Color Splitter ==> OK
    def AddColorSplitter(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Color Splitter shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rscolorsplitter",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rscolorsplitter.input'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rscolorsplitter.outr',
                          'com.redshift3d.redshift4c4d.nodes.core.rscolorsplitter.outg',
                          'com.redshift3d.redshift4c4d.nodes.core.rscolorsplitter.outb',
                          'com.redshift3d.redshift4c4d.nodes.core.rscolorsplitter.outa'
                          ], 
            connect_outNodes = target
            )
  
    # 创建Color Composite ==> OK
    def AddColorComposite(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Color Composite shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rscolorcomposite",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rscolorcomposite.base_color','com.redshift3d.redshift4c4d.nodes.core.rscolorcomposite.blend_color'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rscolorcomposite.outcolor'], 
            connect_outNodes = target
            )
    
    # 创建Color Layer ==> OK
    def AddColorLayer(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Color Layer shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rscolorlayer",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rscolorlayer.base_color',
                           'com.redshift3d.redshift4c4d.nodes.core.rscolorlayer.layer1_color',
                           'com.redshift3d.redshift4c4d.nodes.core.rscolorlayer.layer1_mask'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rscolorlayer.outcolor'], 
            connect_outNodes = target
            )
     
    # 创建Color Change Range ==> OK
    def AddColorChangeRange(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Color Change Range shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rscolorrange",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rscolorrange.input'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rscolorrange.outcolor'], 
            connect_outNodes = target
            )
    
    # 创建color correct ==> OK
    def AddColorCorrect(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new color correct shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection.input'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection.outcolor'], 
            connect_outNodes = target
            )

    ### Operator ###

    # 创建Math Mix(Float64) ==> OK
    def AddValue(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None, mode: Union[str,maxon.Id] = maxon.Id("float")) -> maxon.GraphNode :
        """
        Adds a new Value shader to the graph.

        """
        node = self.AddConnectShader(
            nodeID ="net.maxon.node.type",
            input_ports = ['in'],
            connect_inNodes = inputs,
            output_ports=['out'], 
            connect_outNodes = target
            )
        if isinstance(mode, str):
            mode = maxon.Id(mode)
        if isinstance(mode, maxon.Id):            
            self.SetShaderValue(node, "datatype", mode)
        return node

    # 创建Math Mix(Float64) ==> OK
    def AddMathMix(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Math Mix shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rsmathmix",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rsmathmix.input1',
                           'com.redshift3d.redshift4c4d.nodes.core.rsmathmix.input2',
                           'com.redshift3d.redshift4c4d.nodes.core.rsmathmix.mixamount'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rsmathmix.out'], 
            connect_outNodes = target
            )
    
    # 创建Vector Mix(Vector64) ==> OK
    def AddVectorMix(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Vector Mix shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rsmathmixvector",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rsmathmixvector.input1',
                           'com.redshift3d.redshift4c4d.nodes.core.rsmathmixvector.input2',
                           'com.redshift3d.redshift4c4d.nodes.core.rsmathmixvector.mixamount'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rsmathmixvector.out'], 
            connect_outNodes = target
            )
   
    # 创建Color Mix(ColorAlpha64) ==> OK
    def AddColorMix(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Color Mix shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rscolormix",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rscolormix.input1',
                           'com.redshift3d.redshift4c4d.nodes.core.rscolormix.input2',
                           'com.redshift3d.redshift4c4d.nodes.core.rscolormix.mixamount'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rscolormix.out'], 
            connect_outNodes = target
            )
   
    # 创建Math Add(Float64) ==> OK
    def AddMathAdd(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Math Add shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rsmathadd",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rsmathadd.input1',
                           'com.redshift3d.redshift4c4d.nodes.core.rsmathadd.input2'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rsmathadd.out'], 
            connect_outNodes = target
            )
    
    # 创建Vector Add(Vector64) ==> OK
    def AddVectorAdd(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Vector Add shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rsmathaddvector",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rsmathaddvector.input1',
                           'com.redshift3d.redshift4c4d.nodes.core.rsmathaddvector.input2'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rsmathaddvector.out'], 
            connect_outNodes = target
            )

    # 创建Math Sub(Float64) ==> OK
    def AddMathSub(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Math Sub shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rsmathsub",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rsmathsub.input1',
                           'com.redshift3d.redshift4c4d.nodes.core.rsmathsub.input2'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rsmathsub.out'], 
            connect_outNodes = target
            )

    # 创建Vector Sub(Vector64) ==> OK
    def AddVectorSub(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Vector Sub shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rsmathsubvector",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rsmathsubvector.input1',
                           'com.redshift3d.redshift4c4d.nodes.core.rsmathsubvector.input2'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rsmathsubvector.out'], 
            connect_outNodes = target
            )

    # 创建Color Sub(ColorAlpha64) ==> OK
    def AddColorSub(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Color Sub shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rsmathsubcolor",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rsmathsubcolor.input1',
                           'com.redshift3d.redshift4c4d.nodes.core.rsmathsubcolor.input2'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rsmathsubcolor.out'], 
            connect_outNodes = target
            )

    # 创建Math Mul(Float64) ==> OK
    def AddMathMul(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Math Mul shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rsmathmul",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rsmathmul.input1',
                           'com.redshift3d.redshift4c4d.nodes.core.rsmathmul.input2'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rsmathmul.out'], 
            connect_outNodes = target
            )
    
    # 创建Vector Mul(Vector64) ==> OK
    def AddVectorMul(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Vector Mul shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rsmathmulvector",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rsmathmulvector.input1',
                           'com.redshift3d.redshift4c4d.nodes.core.rsmathmulvector.input2'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rsmathmulvector.out'], 
            connect_outNodes = target
            )

    # 创建Math Div(Float64) ==> OK
    def AddMathDiv(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Math Div shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rsmathdiv",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rsmathdiv.input1',
                           'com.redshift3d.redshift4c4d.nodes.core.rsmathdiv.input2'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rsmathdiv.out'], 
            connect_outNodes = target
            )

    # 创建Vector Div(Vector64) ==> OK
    def AddVectorDiv(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Vector Div shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rsmathdivvector",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rsmathdivvector.input1',
                           'com.redshift3d.redshift4c4d.nodes.core.rsmathdivvector.input2'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rsmathdivvector.out'], 
            connect_outNodes = target
            )

    ### Bump ###

    # 创建Bump ==> OK
    def AddBump(self, input_port: maxon.GraphNode = None, target_port: maxon.GraphNode = None, bump_mode: int = 1) -> maxon.GraphNode :
        """
        Adds a new Bump shader to the graph.

        """
        if self.graph is None:
            return None
        nodeId = "bumpmap"
        shader: maxon.GraphNode = self.graph.AddChild("", "com.redshift3d.redshift4c4d.nodes.core." + nodeId, maxon.DataDictionary())
        type_port = self.GetPort(shader, 'com.redshift3d.redshift4c4d.nodes.core.bumpmap.inputtype')
        self.SetPortData(type_port,bump_mode)

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
            if self.GetAssetId(material) == self.standard_mat:
                bump_port = self.GetPort(material,"com.redshift3d.redshift4c4d.nodes.core.standardmaterial.bump_input")
                output.Connect(bump_port)
            elif self.GetAssetId(material) == self.redshift_mat:
                bump_port = self.GetPort(material,"com.redshift3d.redshift4c4d.nodes.core.material.bump_input")
                output.Connect(bump_port)
            elif self.GetAssetId(material) == self.openpbr_mat:
                bump_port = self.GetPort(material,"com.redshift3d.redshift4c4d.nodes.core.openpbrmaterial.geometry_normal")
                output.Connect(bump_port)
        return shader
    
    # 创建Bump Blender ==> OK
    def AddBumpBlender(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new bump blender shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.bumpblender",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.bumpblender.baseinput',
                           'com.redshift3d.redshift4c4d.nodes.core.bumpblender.bumpinput0',
                           'com.redshift3d.redshift4c4d.nodes.core.bumpblender.bumpweight0',
                           'com.redshift3d.redshift4c4d.nodes.core.bumpblender.bumpinput1',
                           'com.redshift3d.redshift4c4d.nodes.core.bumpblender.bumpweight1',
                           'com.redshift3d.redshift4c4d.nodes.core.bumpblender.bumpinput2',
                           'com.redshift3d.redshift4c4d.nodes.core.bumpblender.bumpweight2'                           
                           ],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.bumpblender.outdisplacementvector'], 
            connect_outNodes = target
            )
    
    # 创建displacement ==> OK
    def AddDisplacement(self, input_port: maxon.GraphNode = None, target_port: maxon.GraphNode = None) -> maxon.GraphNode :
        """
        Adds a new displacement shader to the graph.

        """
        if self.graph is None:
            return None
        nodeId = "displacement"
        shader: maxon.GraphNode = self.graph.AddChild("", "com.redshift3d.redshift4c4d.nodes.core." + nodeId, maxon.DataDictionary())

        if input_port:
            if isinstance(input_port, maxon.GraphNode):
                input: maxon.GraphNode = self.GetPort(shader,'com.redshift3d.redshift4c4d.nodes.core.displacement.texmap')
                try:
                    input_port.Connect(input)
                except:
                    pass
                
        output: maxon.GraphNode = self.GetPort(shader,'com.redshift3d.redshift4c4d.nodes.core.displacement.out')
        
        if target_port is not None:
            if isinstance(target_port, maxon.GraphNode):                
                try:
                    output.Connect(target_port)
                except:
                    pass

        else:
            rsoutput = self.GetOutput()

            dis_port = self.GetPort(rsoutput,"com.redshift3d.redshift4c4d.node.output.displacement")
            output.Connect(dis_port)
        return shader

    # 创建displacement Blender ==> OK
    def AddDisplacementBlender(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new displacement blender shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.displacementblender",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.displacementblender.baseinput',
                           'com.redshift3d.redshift4c4d.nodes.core.displacementblender.displaceinput0',
                           'com.redshift3d.redshift4c4d.nodes.core.displacementblender.displaceweight0',
                           'com.redshift3d.redshift4c4d.nodes.core.displacementblender.displaceinput1',
                           'com.redshift3d.redshift4c4d.nodes.core.displacementblender.displaceweight1',
                           'com.redshift3d.redshift4c4d.nodes.core.displacementblender.displaceinput2',
                           'com.redshift3d.redshift4c4d.nodes.core.displacementblender.displaceweight2'                           
                           ],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.displacementblender.out'], 
            connect_outNodes = target
            )

    # 创建Round Corners ==> OK
    def AddRoundCorner(self, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Round Corners shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.roundcorners",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.roundcorners.out'], 
            connect_outNodes = target
            )
    
    ### State ###

    # 创建Fresnel ==> OK
    def AddFresnel(self, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Fresnel shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rscolorconstant",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rscolorconstant.outcolor'], 
            connect_outNodes = target
            )

    # 创建AO ==> OK
    def AddAO(self, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new AO shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.ambientocclusion",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.ambientocclusion.out'], 
            connect_outNodes = target
            )

    # 创建Curvature ==> OK
    def AddCurvature(self, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Curvature shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.curvature",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.curvature.out'], 
            connect_outNodes = target
            )

    # 创建Flakes ==> OK
    def AddFlakes(self, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Flakes shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.flakes",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.flakes.outnormal'], 
            connect_outNodes = target
            )

    # 创建Point Attribute ==> OK
    def AddPointAttribute(self, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Point Attribute shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.particleattributelookup",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.particleattributelookup.outscalar',
                          'com.redshift3d.redshift4c4d.nodes.core.particleattributelookup.outcolor'], 
            connect_outNodes = target
            )

    # 创建Vertex Attribute ==> OK
    def AddVertexAttribute(self, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new Vertex Attribute shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.vertexattributelookup",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.vertexattributelookup.outscalar',
                          'com.redshift3d.redshift4c4d.nodes.core.vertexattributelookup.outcolor'], 
            connect_outNodes = target
            )

    ### Texture ###
    
    # 创建ramp ==> OK
    def AddRamp(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new ramp shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rsramp",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rsramp.input'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rsramp.outcolor'], 
            connect_outNodes = target
            )

    # 创建scalar ramp ==> OK
    def AddScalarRamp(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new scalar ramp shader to the graph.        

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.rsscalarramp",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.rsscalarramp.input'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.rsscalarramp.out'], 
            connect_outNodes = target
            )

    # 创建TriPlanar ==> OK
    def AddTriPlanar(self, inputs: list[NodeInput] = None, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new TriPlanar shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.triplanar",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.triplanar.imagex'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.triplanar.outcolor'], 
            connect_outNodes = target
            )

    # 创建maxon noise ==> OK
    def AddMaxonNoise(self, target: list[NodeInput] = None) -> maxon.GraphNode :
        """
        Adds a new maxonnoise shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.maxonnoise",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.maxonnoise.outcolor'], 
            connect_outNodes = target
            )

    # 创建Texture ==> OK
    def AddTexture(self, shadername :str = 'Texture', filepath: str = None, raw: bool = True, gamma: int = 1, target_port: maxon.GraphNode = None) -> maxon.GraphNode :
        """
        Adds a new texture shader to the graph.
        """
        if self.graph is None:
            return None
        
        nodeId = "texturesampler"
        shader: maxon.GraphNode = self.graph.AddChild("", "com.redshift3d.redshift4c4d.nodes.core." + nodeId, maxon.DataDictionary())
        self.SetName(shader,shadername)
        
        texPort: maxon.GraphNode = self.GetPort(shader,"com.redshift3d.redshift4c4d.nodes.core.texturesampler.tex0")
        texFilenamePort: maxon.GraphNode = texPort.FindChild('path')
        colorspacePort: maxon.GraphNode = texPort.FindChild("colorspace")
        gammaPort: maxon.GraphNode = self.GetPort(shader,"com.redshift3d.redshift4c4d.nodes.core.texturesampler.tex0_gamma")
        self.SetPortData(gammaPort, gamma)
        # tex path
        if filepath is not None:
            self.SetPortData(texFilenamePort, filepath)
        
        # color space
        if raw:
            self.SetPortData(colorspacePort, "RS_INPUT_COLORSPACE_RAW")
        else:
            self.SetPortData(colorspacePort, "RS_INPUT_COLORSPACE_SRGB")
        
        # target connect
        if target_port:
            if isinstance(target_port, maxon.GraphNode):
                outPort: maxon.GraphNode = self.GetPort(shader,'com.redshift3d.redshift4c4d.nodes.core.texturesampler.outcolor')
                try:
                    outPort.Connect(target_port)
                except:
                    pass

        return shader

    ### Tree ###
    # todo
    # NEW
    def AddTextureTree(self, shadername :str = 'Texture', filepath: str = None, raw: bool = True, gamma: int = 1.0, triplaner_node: bool = False, color_mode: bool = False,scaleramp: bool = True,color_mutiplier: maxon.GraphNode = None, target_port: maxon.GraphNode = None) -> list[maxon.GraphNode] :
        """
        Adds a texture tree (tex + color correction + ramp) to the graph.
        """
        if self.graph is None:
            return None
        
        # add
        tex_node = self.AddTexture(shadername, filepath, raw, gamma)
        color_mutiplier_port = self.GetPort(tex_node,"com.redshift3d.redshift4c4d.nodes.core.texturesampler.color_multiplier")
        
        if color_mode:
            cc_node = self.AddColorCorrect(target=target_port)
        
        else:
            cc_node = self.AddColorCorrect()
            if scaleramp:
                ramp_node = self.AddScalarRamp(target=target_port)
            else:
                ramp_node = self.AddRamp(target=target_port)
        
        if triplaner_node:
            triplaner_node = self.AddTriPlanar(self.GetPort(tex_node,"com.redshift3d.redshift4c4d.nodes.core.texturesampler.outcolor"), self.GetPort(cc_node,"com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection.input"))

        else:
            self.AddConnection(tex_node, "com.redshift3d.redshift4c4d.nodes.core.texturesampler.outcolor", cc_node, "com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection.input")
        
        
        if not color_mode:
            if scaleramp:
                self.AddConnection(cc_node, "com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection.outcolor", ramp_node, "com.redshift3d.redshift4c4d.nodes.core.rsscalarramp.input")
            else:
                self.AddConnection(cc_node, "com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection.outcolor", ramp_node, "com.redshift3d.redshift4c4d.nodes.core.rsramp.input")
        
        if color_mutiplier:
            self.AddConnection(color_mutiplier, "com.redshift3d.redshift4c4d.nodes.core.texturesampler.outcolor", tex_node, color_mutiplier_port)
        
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
        # tex_in = self.GetPort(tex_node, "com.redshift3d.redshift4c4d.nodes.core.texturesampler.tex0")
        tex_out = self.GetPort(tex_node, "com.redshift3d.redshift4c4d.nodes.core.texturesampler.outcolor")

        if triplaner_node:
            triplaner_node = self.AddTriPlanar(tex_out)
            tex_out = self.GetPort(triplaner_node, self.GetConvertOutput(triplaner_node))

        self.AddDisplacement(input_port=tex_out)

    # NEW
    def AddBumpTree(self, shadername :str = 'Bump', filepath: str = None, bump_mode: int = 1, target_port: maxon.GraphNode = None, triplaner_node: bool = False) -> list[maxon.GraphNode] :
        """
        Adds a bump tree (tex + bump) to the graph.
        """
        if self.graph is None:
            return None
        
        # add        
        tex_node = self.AddTexture(shadername, filepath, True)
        tex_out = self.GetPort(tex_node, "com.redshift3d.redshift4c4d.nodes.core.texturesampler.outcolor")
        #tex_out = self.GetPort(tex_node, "com.redshift3d.redshift4c4d.nodes.core.texturesampler.outcolor")
        if triplaner_node:
            triplaner_node = self.AddTriPlanar(tex_out)
            tex_out = self.GetPort(triplaner_node, self.GetConvertOutput(triplaner_node))
        self.AddBump(input_port=tex_out, target_port=target_port, bump_mode=bump_mode)

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
        endNodePort = self.GetPort(endNode, "com.redshift3d.redshift4c4d.node.output.surface")
        return self.AddConnection(soure_node, outPort, endNode, endNodePort) is not None
    
    # 连接到Output置换接口
    def AddtoDisplacement(self, soure_node, outPort):
        """
        Connects the given shader to RS Output Displacement port.

        Parameters
        ----------
        soure_node : maxon.frameworks.graph.GraphNode
            The source shader node.
        outPort : str
            Output port id of the source shader node.
        """
        rsoutput = self.GetOutput()
        rsoutputPort = self.GetPort(rsoutput, "com.redshift3d.com.redshift3d.redshift4c4d.node.output.displacement.node.output.surface")
        return self.AddConnection(soure_node, outPort, rsoutput, rsoutputPort) is not None

    # 添加统一缩放（类似Octane的transform）
    def AddUniTransform(self, tex_shader: maxon.GraphNode) -> maxon.GraphNode:
        """
        Connects a UniTransform node to the given texture shader.

        Parameters
        ----------
        tex_shader : maxon.frameworks.graph.GraphNode
            The target shader node.
        """
        if not tex_shader:
            return None
        if self.GetShaderId(tex_shader) != "texturesampler":
            raise ValueError("The given node is not a texture shader.")
        
        # The tex value port
        tex_scale = self.GetPort(tex_shader, "com.redshift3d.redshift4c4d.nodes.core.texturesampler.scale")
        tex_offset = self.GetPort(tex_shader, "com.redshift3d.redshift4c4d.nodes.core.texturesampler.offset")
        tex_rotate = self.GetPort(tex_shader, "com.redshift3d.redshift4c4d.nodes.core.texturesampler.rotate")

        # create inner node
        uni_scale_node = self.AddValue()
        self.SetName(uni_scale_node, "UniScale")
        #uni_scale_in = self.GetPort(uni_scale_node, "in")
        uni_scale_out = self.GetPort(uni_scale_node, "out")
        
        scale_node = self.AddVectorMul(inputs=[uni_scale_out])
        scale2d_node = self.AddValue(mode=maxon.Id("net.maxon.parametrictype.vec<2,float>"))
        offset_node = self.AddValue(mode=maxon.Id("net.maxon.parametrictype.vec<2,float>"))
        rotate_node = self.AddValue()
        self.SetName(scale_node, "Scale")
        self.SetName(scale2d_node, "Scale2D")
        self.SetName(offset_node, "Offset")
        self.SetName(rotate_node, "Rotation")

        # Move to group straight away
        groupRoot: maxon.GraphNode = self.graph.MoveToGroup(maxon.GraphNode(), maxon.Id(f"UniTransform@{str(maxon.UuidInterface.Alloc()).replace('-','')}"), 
                                                            [uni_scale_node, scale_node, offset_node, rotate_node, scale2d_node])
        self.SetName(groupRoot, "UniTransform")

        # Create group ports
        # in
        groupPortIn_scale: maxon.GraphNode =  maxon.GraphModelHelper.CreateInputPort(groupRoot, "group_scale_id", "Scale")
        groupPortIn_unify: maxon.GraphNode =  maxon.GraphModelHelper.CreateInputPort(groupRoot, "group_uni_scale_id", "UniScale")
        groupPortIn_offset: maxon.GraphNode =  maxon.GraphModelHelper.CreateInputPort(groupRoot, "group_offset_id", "Offset")
        groupPortIn_rotate: maxon.GraphNode =  maxon.GraphModelHelper.CreateInputPort(groupRoot, "group_rotate_id", "Rotation")
        # out
        groupPortOut_scale: maxon.GraphNode =  maxon.GraphModelHelper.CreateOutputPort(groupRoot, "group_output_scale_id", "Scale")
        groupPortOut_offset: maxon.GraphNode =  maxon.GraphModelHelper.CreateOutputPort(groupRoot, "group_output_offset_id", "Offset")
        groupPortOut_rotate: maxon.GraphNode =  maxon.GraphModelHelper.CreateOutputPort(groupRoot, "group_output_rotate_id", "Rotation")

        # Connect group to the outside nodes
        groupPortOut_scale.Connect(tex_scale)
        groupPortOut_offset.Connect(tex_offset)
        groupPortOut_rotate.Connect(tex_rotate)

        # Find innder node
        innerNodes: list[maxon.GraphNode] = []
        groupRoot.GetInnerNodes(maxon.NODE_KIND.NODE, False, innerNodes)
        # maxon.GraphModelHelper.FindNodesByAssetId(self.graph, maxon.Id(rsID.StrNodeID("rsmathabs")), True, innerNodes)
        for node in innerNodes:
            if self.GetName(node) == "Scale":
                NodeInner_scale: maxon.GraphNode = node
            if self.GetName(node) == "Offset":
                NodeInner_offset: maxon.GraphNode = node
            if self.GetName(node) == "Rotation":
                NodeInner_rotate: maxon.GraphNode = node
            if self.GetName(node) == "UniScale":
                NodeInner_uniScale: maxon.GraphNode = node
            if self.GetName(node) == "Scale2D":
                NodeInner_Scale2D: maxon.GraphNode = node

        # Find inner node ports
        NodeInnerInput_uni_scale_in = self.GetPort(NodeInner_uniScale, "in")
        NodeInnerInput_offset_in = self.GetPort(NodeInner_offset, "in")
        NodeInnerInput_rotate_in = self.GetPort(NodeInner_rotate, "in")
        NodeInnerInput_scale_in = self.GetPort(NodeInner_scale, "com.redshift3d.redshift4c4d.nodes.core.rsmathmulvector.input2")
        NodeInnerInput_scale2D_in = self.GetPort(NodeInner_Scale2D, "in")
        # Find outer node ports
        NodeInnerOutput_scale_out = self.GetPort(NodeInner_scale, "com.redshift3d.redshift4c4d.nodes.core.rsmathmulvector.out")
        NodeInnerOutput_offset_out = self.GetPort(NodeInner_offset, "out")
        NodeInnerOutput_rotate_out = self.GetPort(NodeInner_rotate, "out")

        # Connect scale
        self.GetPort(NodeInner_Scale2D, "out").Connect(NodeInnerInput_scale_in)

        # Connect inner node ports to group ports
        groupPortIn_scale.Connect(NodeInnerInput_scale2D_in)
        groupPortIn_unify.Connect(NodeInnerInput_uni_scale_in)
        groupPortIn_offset.Connect(NodeInnerInput_offset_in)
        groupPortIn_rotate.Connect(NodeInnerInput_rotate_in)

        NodeInnerOutput_scale_out.Connect(groupPortOut_scale)
        NodeInnerOutput_offset_out.Connect(groupPortOut_offset)
        NodeInnerOutput_rotate_out.Connect(groupPortOut_rotate)

        # Set default value
        self.SetPortData(NodeInnerInput_uni_scale_in, 1)
        self.SetPortData(NodeInnerInput_scale2D_in, 1)

        # Hide input ports
        self.RemovePort(groupRoot, groupPortIn_scale)
        self.RemovePort(groupRoot, groupPortIn_unify)
        self.RemovePort(groupRoot, groupPortIn_offset)
        self.RemovePort(groupRoot, groupPortIn_rotate)

        self.FoldPreview(groupRoot)
        groupRoot.SetValue(maxon.NODE.BASE.COLOR, maxon.Color(0, 0.424, 0)) 

        return groupRoot


    # TEST
    # 添加统一缩放（类似Octane的transform）
    def AddUniTransforms(self, tex_shaders: list[maxon.GraphNode]) -> maxon.GraphNode:
        """
        Connects a UniTransform node to the given texture shader.

        Parameters
        ----------
        tex_shader : maxon.frameworks.graph.GraphNode
            The target shader node.
        """
        if not tex_shaders:
            return None

        # create inner node
        uni_scale_node = self.AddValue()
        self.SetName(uni_scale_node, "UniScale")
        #uni_scale_in = self.GetPort(uni_scale_node, "in")
        uni_scale_out = self.GetPort(uni_scale_node, "out")
        
        scale_node = self.AddVectorMul(inputs=[uni_scale_out])
        scale2d_node = self.AddValue(mode=maxon.Id("net.maxon.parametrictype.vec<2,float>"))
        offset_node = self.AddValue(mode=maxon.Id("net.maxon.parametrictype.vec<2,float>"))
        rotate_node = self.AddValue()
        self.SetName(scale_node, "Scale")
        self.SetName(scale2d_node, "Scale2D")
        self.SetName(offset_node, "Offset")
        self.SetName(rotate_node, "Rotation")

        # Move to group straight away
        groupRoot: maxon.GraphNode = self.graph.MoveToGroup(maxon.GraphNode(), maxon.Id(f"UniTransform@{str(maxon.UuidInterface.Alloc()).replace('-','')}"), 
                                                            [uni_scale_node, scale_node, offset_node, rotate_node, scale2d_node])
        self.SetName(groupRoot, "UniTransform")

        # Create group ports
        # in
        groupPortIn_scale: maxon.GraphNode =  maxon.GraphModelHelper.CreateInputPort(groupRoot, "group_scale_id", "Scale")
        groupPortIn_unify: maxon.GraphNode =  maxon.GraphModelHelper.CreateInputPort(groupRoot, "group_uni_scale_id", "UniScale")
        groupPortIn_offset: maxon.GraphNode =  maxon.GraphModelHelper.CreateInputPort(groupRoot, "group_offset_id", "Offset")
        groupPortIn_rotate: maxon.GraphNode =  maxon.GraphModelHelper.CreateInputPort(groupRoot, "group_rotate_id", "Rotation")
        # out
        groupPortOut_scale: maxon.GraphNode =  maxon.GraphModelHelper.CreateOutputPort(groupRoot, "group_output_scale_id", "Scale")
        groupPortOut_offset: maxon.GraphNode =  maxon.GraphModelHelper.CreateOutputPort(groupRoot, "group_output_offset_id", "Offset")
        groupPortOut_rotate: maxon.GraphNode =  maxon.GraphModelHelper.CreateOutputPort(groupRoot, "group_output_rotate_id", "Rotation")

        # Find innder node
        innerNodes: list[maxon.GraphNode] = []
        groupRoot.GetInnerNodes(maxon.NODE_KIND.NODE, False, innerNodes)
        # maxon.GraphModelHelper.FindNodesByAssetId(self.graph, maxon.Id(rsID.StrNodeID("rsmathabs")), True, innerNodes)
        for node in innerNodes:
            if self.GetName(node) == "Scale":
                NodeInner_scale: maxon.GraphNode = node
            if self.GetName(node) == "Offset":
                NodeInner_offset: maxon.GraphNode = node
            if self.GetName(node) == "Rotation":
                NodeInner_rotate: maxon.GraphNode = node
            if self.GetName(node) == "UniScale":
                NodeInner_uniScale: maxon.GraphNode = node
            if self.GetName(node) == "Scale2D":
                NodeInner_Scale2D: maxon.GraphNode = node

        # Find inner node ports
        NodeInnerInput_uni_scale_in = self.GetPort(NodeInner_uniScale, "in")
        NodeInnerInput_offset_in = self.GetPort(NodeInner_offset, "in")
        NodeInnerInput_rotate_in = self.GetPort(NodeInner_rotate, "in")
        NodeInnerInput_scale_in = self.GetPort(NodeInner_scale, "com.redshift3d.redshift4c4d.nodes.core.rsmathmulvector.input2")
        NodeInnerInput_scale2D_in = self.GetPort(NodeInner_Scale2D, "in")
        # Find outer node ports
        NodeInnerOutput_scale_out = self.GetPort(NodeInner_scale, "com.redshift3d.redshift4c4d.nodes.core.rsmathmulvector.out")
        NodeInnerOutput_offset_out = self.GetPort(NodeInner_offset, "out")
        NodeInnerOutput_rotate_out = self.GetPort(NodeInner_rotate, "out")

        # Connect scale
        self.GetPort(NodeInner_Scale2D, "out").Connect(NodeInnerInput_scale_in)

        # Connect inner node ports to group ports
        groupPortIn_scale.Connect(NodeInnerInput_scale2D_in)
        groupPortIn_unify.Connect(NodeInnerInput_uni_scale_in)
        groupPortIn_offset.Connect(NodeInnerInput_offset_in)
        groupPortIn_rotate.Connect(NodeInnerInput_rotate_in)

        NodeInnerOutput_scale_out.Connect(groupPortOut_scale)
        NodeInnerOutput_offset_out.Connect(groupPortOut_offset)
        NodeInnerOutput_rotate_out.Connect(groupPortOut_rotate)

        # Set default value
        self.SetPortData(NodeInnerInput_uni_scale_in, 1)
        self.SetPortData(NodeInnerInput_scale2D_in, 1)

        # Hide input ports
        self.RemovePort(groupRoot, groupPortIn_scale)
        self.RemovePort(groupRoot, groupPortIn_unify)
        self.RemovePort(groupRoot, groupPortIn_offset)
        self.RemovePort(groupRoot, groupPortIn_rotate)

        self.FoldPreview(groupRoot)
        groupRoot.SetValue(maxon.NODE.BASE.COLOR, maxon.Color(0, 0.424, 0)) 

        for tex_shader in tex_shaders:		
            if self.GetShaderId(tex_shader) == "texturesampler":
                # The tex value port
                tex_scale = self.GetPort(tex_shader, "com.redshift3d.redshift4c4d.nodes.core.texturesampler.scale")
                tex_offset = self.GetPort(tex_shader, "com.redshift3d.redshift4c4d.nodes.core.texturesampler.offset")
                tex_rotate = self.GetPort(tex_shader, "com.redshift3d.redshift4c4d.nodes.core.texturesampler.rotate")
                # Connect group to the outside nodes
                groupPortOut_scale.Connect(tex_scale)
                groupPortOut_offset.Connect(tex_offset)
                groupPortOut_rotate.Connect(tex_rotate)

        return groupRoot

__all__ = [
    "MaterialHelper",
    "IsCoronaMaterial",
]
