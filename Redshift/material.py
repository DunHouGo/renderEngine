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

    # Public port table for the supported Redshift material models.
    PBR_PORTS: dict[str, dict[str, str]] = {
        standard_mat: {
            "diffuse": f"{standard_mat}.base_color",
            "specular": f"{standard_mat}.refl_color",
            "roughness": f"{standard_mat}.refl_roughness",
            "metalness": f"{standard_mat}.metalness",
            "opacity": f"{standard_mat}.opacity_color",
            "transmission": f"{standard_mat}.refr_color",
            "emission": f"{standard_mat}.emission_color",
            "normal": f"{standard_mat}.bump_input",
            "coat_normal": f"{standard_mat}.coat_bump_input",
            "glossiness": f"{standard_mat}.refl_isglossiness",
            "sheen": f"{standard_mat}.sheen_color",
            "anisotropy": f"{standard_mat}.refl_aniso",
        },
        redshift_mat: {
            "diffuse": f"{redshift_mat}.diffuse_color",
            "specular": f"{redshift_mat}.refl_color",
            "roughness": f"{redshift_mat}.refl_roughness",
            "metalness": f"{redshift_mat}.metalness",
            "opacity": f"{redshift_mat}.opacity_color",
            "transmission": f"{redshift_mat}.refr_color",
            "emission": f"{redshift_mat}.emission_color",
            "normal": f"{redshift_mat}.bump_input",
            "coat_normal": f"{redshift_mat}.coat_bump_input",
            "sheen": f"{redshift_mat}.sheen_color",
            "anisotropy": f"{redshift_mat}.refl_aniso",
        },
        openpbr_mat: {
            "base_weight": f"{openpbr_mat}.base_weight",
            "diffuse": f"{openpbr_mat}.base_color",
            "base_color": f"{openpbr_mat}.base_color",
            "diffuse_roughness": f"{openpbr_mat}.base_diffuse_roughness",
            "base_diffuse_roughness": f"{openpbr_mat}.base_diffuse_roughness",
            "metalness": f"{openpbr_mat}.base_metalness",
            "base_metalness": f"{openpbr_mat}.base_metalness",
            "specular": f"{openpbr_mat}.specular_color",
            "specular_color": f"{openpbr_mat}.specular_color",
            "specular_weight": f"{openpbr_mat}.specular_weight",
            "specular_ior": f"{openpbr_mat}.specular_ior",
            "roughness": f"{openpbr_mat}.specular_roughness",
            "specular_roughness": f"{openpbr_mat}.specular_roughness",
            "anisotropy": f"{openpbr_mat}.specular_roughness_anisotropy",
            "specular_roughness_anisotropy": f"{openpbr_mat}.specular_roughness_anisotropy",
            "transmission": f"{openpbr_mat}.transmission_color",
            "transmission_color": f"{openpbr_mat}.transmission_color",
            "transmission_weight": f"{openpbr_mat}.transmission_weight",
            "transmission_depth": f"{openpbr_mat}.transmission_depth",
            "transmission_scatter": f"{openpbr_mat}.transmission_scatter",
            "transmission_scatter_anisotropy": f"{openpbr_mat}.transmission_scatter_anisotropy",
            "transmission_dispersion_scale": f"{openpbr_mat}.transmission_dispersion_scale",
            "transmission_dispersion_abbe_number": f"{openpbr_mat}.transmission_dispersion_abbe_number",
            "subsurface": f"{openpbr_mat}.subsurface_weight",
            "subsurface_weight": f"{openpbr_mat}.subsurface_weight",
            "subsurface_color": f"{openpbr_mat}.subsurface_color",
            "subsurface_radius": f"{openpbr_mat}.subsurface_radius",
            "subsurface_radius_scale": f"{openpbr_mat}.subsurface_radius_scale",
            "subsurface_scatter_anisotropy": f"{openpbr_mat}.subsurface_scatter_anisotropy",
            "emission": f"{openpbr_mat}.emission_color",
            "emission_color": f"{openpbr_mat}.emission_color",
            "emission_luminance": f"{openpbr_mat}.emission_luminance",
            "opacity": f"{openpbr_mat}.geometry_opacity",
            "geometry_opacity": f"{openpbr_mat}.geometry_opacity",
            "normal": f"{openpbr_mat}.geometry_normal",
            "geometry_normal": f"{openpbr_mat}.geometry_normal",
            "coat_normal": f"{openpbr_mat}.geometry_coat_normal",
            "geometry_coat_normal": f"{openpbr_mat}.geometry_coat_normal",
            "coat_color": f"{openpbr_mat}.coat_color",
            "coat_weight": f"{openpbr_mat}.coat_weight",
            "coat_darkening": f"{openpbr_mat}.coat_darkening",
            "coat_ior": f"{openpbr_mat}.coat_ior",
            "coat_roughness": f"{openpbr_mat}.coat_roughness",
            "coat_roughness_anisotropy": f"{openpbr_mat}.coat_roughness_anisotropy",
            "sheen": f"{openpbr_mat}.fuzz_color",
            "sheen_weight": f"{openpbr_mat}.fuzz_weight",
            "sheen_roughness": f"{openpbr_mat}.fuzz_roughness",
            "tangent": f"{openpbr_mat}.geometry_tangent",
            "coat_tangent": f"{openpbr_mat}.geometry_coat_tangent",
            "thin_film_weight": f"{openpbr_mat}.thin_film_weight",
            "thin_film_thickness": f"{openpbr_mat}.thin_film_thickness",
            "thin_film_ior": f"{openpbr_mat}.thin_film_ior",
            "thin_walled": f"{openpbr_mat}.geometry_thin_walled",
            "output": f"{openpbr_mat}.outcolor",
        },
    }

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
        # NodeGraghHelper defaults to the active NodeSpace, which is unsafe when
        # the material editor is showing another renderer. Initialize the common
        # fields locally and bind this helper only to the material's RS graph.
        if not isinstance(self.material, c4d.BaseMaterial):
            raise ValueError(f"Expected a BaseMaterial, got {type(self.material)}")
        self.nodeMaterial = self.material.GetNodeMaterialReference()
        if self.nodeMaterial is None:
            raise ValueError("Cannot retrieve nodeMaterial reference")
        self._support_renderers = [
            "net.maxon.nodespace.standard",
            "com.autodesk.arnold.nodespace",
            RS_NODESPACE,
            "com.chaos.class.vray_node_renderer_nodespace",
            "com.centileo.class.nodespace",
        ]
        self.nodespaceId = RS_NODESPACE
        self.nimbusRef = self.material.GetNimbusRef(RS_NODESPACE)
        self.graph = self.nodeMaterial.GetGraph(RS_NODESPACE)
        if self.graph.IsNullValue():
            raise RuntimeError("Empty graph associated with Redshift node space.")
        if c4d.GetC4DVersion() < 2025000:
            self.root = self.graph.GetRoot()
        else:
            self.root = self.graph.GetViewRoot()

    def __str__(self):
        return (f"A Redshift {self.__class__.__name__} Instance with Material : {self.material.GetName()}")
    
    # =====  Material  ===== #

    @staticmethod
    def _getversion() -> str :
        """
        Get the version number of Redshift.

        Returns:
            str: The version number
        """
        try:
            import redshift
            return redshift.GetCoreVersion()
        except Exception:
            return str(0)

    def GetPBRPortId(self, material_node: maxon.GraphNode, channel: str) -> str | None:
        """Return the full Redshift port ID for a material channel.

        :param material_node: The Redshift material node to inspect.
        :param channel: A normalized channel name such as ``diffuse`` or ``roughness``.
        :return: The full port ID, or ``None`` when the material model has no such channel.
        :rtype: str | None
        """
        if not isinstance(material_node, maxon.GraphNode):
            return None
        asset_id = self.GetAssetId(material_node)
        return self.PBR_PORTS.get(asset_id, {}).get(channel)

    def GetPBRPort(self, material_node: maxon.GraphNode, channel: str) -> maxon.GraphNode | None:
        """Return a validated material port for a normalized PBR channel.

        :param material_node: The Redshift material node to inspect.
        :param channel: A normalized PBR channel name.
        :return: The matching valid graph port, or ``None`` when unavailable.
        :rtype: maxon.GraphNode | None
        """
        port_id = self.GetPBRPortId(material_node, channel)
        if not port_id:
            return None
        port = self.GetPort(material_node, port_id)
        return port if self.IsPortValid(port) else None

    def IsOpenPBR(self, material_node: maxon.GraphNode | None = None) -> bool:
        """Return whether the given or current root material is an OpenPBR node.

        :param material_node: An optional Redshift material node; the root BRDF is used by default.
        :return: ``True`` when the node asset is Redshift OpenPBR.
        :rtype: bool
        """
        node = material_node if material_node is not None else self.GetRootBRDF()
        return isinstance(node, maxon.GraphNode) and self.GetAssetId(node) == self.openpbr_mat

    def _ExposePortIfValid(self, node: maxon.GraphNode, port_id: str) -> maxon.GraphNode | None:
        """Expose a material port only when it exists in the installed Redshift node definition."""
        port = self.GetPort(node, port_id)
        if not self.IsPortValid(port):
            return None
        port.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(False))
        return port


    # 创建材质(Standard Surface) ==> OK
    def Create(self, name: str = "") -> c4d.BaseMaterial:
        """
        Creates a new Redshift Node Material with a NAME.

        Parameters
        ----------
        name : str
            The Material entry name.

        """
        # OpenPBR is the preferred Redshift model. Older Redshift builds simply
        # fail to instantiate it and use Standard Material as a compatibility path.
        try:
            return self.CreateOpenPBR(name)
        except Exception:
            return self.CreateDefault(name)

    @staticmethod
    def CreateDefault(name: str = "") -> c4d.BaseMaterial:
        material = c4d.BaseMaterial(c4d.Mmaterial)
        if material is None:
            raise ValueError("Cannot create a BaseMaterial")
        name = name if name else "Standard Surface"
        material.SetName(name)

        nodeMaterial = material.GetNodeMaterialReference()
        if nodeMaterial is None:
            raise ValueError("Cannot retrieve nodeMaterial reference")
        # Add a graph for the redshift node space
        nodeMaterial.CreateDefaultGraph(RS_NODESPACE)  

        helper = MaterialHelper(material)
        with helper.graph.BeginTransaction() as transaction:
            brdf: maxon.GraphNode = helper.GetRootBRDF()
            helper.SetName(brdf, 'Standard Surface')
            helper._ExposePortIfValid(brdf, f"{MaterialHelper.standard_mat}.refr_color")
            helper._ExposePortIfValid(brdf, f"{MaterialHelper.standard_mat}.refr_weight")
            helper._ExposePortIfValid(brdf, f"{MaterialHelper.standard_mat}.emission_weight")
            helper._ExposePortIfValid(brdf, f"{MaterialHelper.standard_mat}.emission_color")
            helper._ExposePortIfValid(brdf, f"{MaterialHelper.standard_mat}.refl_color")
            transaction.Commit()

        return material
    
    # 创建RS Material
    @staticmethod
    def CreateRSMaterial(name: str = "") -> c4d.BaseMaterial:
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
        name = name if name else "Redshift Material"
        helper = MaterialHelper(standardMaterial)
        with helper.graph.BeginTransaction() as transaction:
            oldrs = helper.GetRootBRDF()
            output_inport = helper.GetPort(helper.GetOutput(), "com.redshift3d.redshift4c4d.node.output.surface")
            helper.RemoveShader(oldrs)
            rsMaterial = helper.AddRSMaterial(target=output_inport)
            helper.SetName(rsMaterial, 'RS Material')
            helper.SetShaderValue(rsMaterial, f"{MaterialHelper.redshift_mat}.refl_roughness", 0.2)
            helper._ExposePortIfValid(helper.GetRootBRDF(), f"{MaterialHelper.redshift_mat}.transl_color")
            helper._ExposePortIfValid(helper.GetRootBRDF(), f"{MaterialHelper.redshift_mat}.transl_weight")
            transaction.Commit()
        return standardMaterial

    @staticmethod
    def CreateOpenPBR(name: str = "") -> c4d.BaseMaterial:
        """
        Creates a MaterialHelper instance for OpenPBRMaterial.

        Parameters
        ----------
        name : str
            The Material entry name.
        """
        material: c4d.BaseMaterial = c4d.BaseMaterial(c4d.Mmaterial)
        if material is None:
            raise ValueError("Cannot create a BaseMaterial")
        name = name if name else "OpenPBR Material"
        material.SetName(name)
        nodeMaterial = material.GetNodeMaterialReference()
        if nodeMaterial is None:
            raise ValueError("Cannot retrieve nodeMaterial reference")
        nodeMaterial.CreateDefaultGraph(RS_NODESPACE)
        helper = MaterialHelper(material)
        with helper.graph.BeginTransaction() as transaction:
            old_brdf = helper.GetRootBRDF()
            output_port = helper.GetPort(helper.GetOutput(), "com.redshift3d.redshift4c4d.node.output.surface")
            if not helper.IsPortValid(output_port):
                raise RuntimeError("Redshift output surface port is unavailable")
            if helper.IsNode(old_brdf):
                helper.RemoveShader(old_brdf, keep_wire=False)
            brdf = helper.AddOpenPBRMaterial(target=output_port)
            if not helper.IsNode(brdf):
                raise RuntimeError("Redshift OpenPBR node could not be created")
            helper.SetName(brdf, name)
            for port_id in (
                "diffuse",
                "diffuse_roughness",
                "metalness",
                "specular",
                "specular_weight",
                "roughness",
                "anisotropy",
                "transmission",
                "transmission_weight",
                "emission",
                "emission_luminance",
                "opacity",
                "normal",
                "coat_normal",
                "coat_color",
                "coat_weight",
                "coat_roughness",
                "sheen",
                "sheen_weight",
                "sheen_roughness",
                "tangent",
                "coat_tangent",
            ):
                port_id = helper.GetPBRPortId(brdf, port_id)
                if port_id:
                    helper._ExposePortIfValid(brdf, port_id)
            transaction.Commit()

        return material
    
    # 暴露常用接口
    def ExposeUsefulPorts(self):
        if self.graph is None:
            raise ValueError("can't retrieve the graph of this nimbus ref")

        def expose_ports(node: maxon.GraphNode) -> bool:
            """Expose the common PBR ports on one Redshift material node."""
            asset_id = self.GetAssetId(node)
            with self.graph.BeginTransaction() as transaction:
                for channel in self.PBR_PORTS.get(asset_id, {}):
                    port_id = self.GetPBRPortId(node, channel)
                    if port_id:
                        self._ExposePortIfValid(node, port_id)
                transaction.Commit()
            return True

        for asset_id in self.valid_mat:
            maxon.GraphModelHelper.FindNodesByAssetId(self.graph, asset_id, False, expose_ports)

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

            # Resolve the ports from the actual material model, including OpenPBR.
            albedoPort = redshiftMaterial.GetPBRPort(standard_surface, "diffuse")
            specularPort = redshiftMaterial.GetPBRPort(standard_surface, "specular")
            roughnessPort = redshiftMaterial.GetPBRPort(standard_surface, "roughness")
            metalnessPort = redshiftMaterial.GetPBRPort(standard_surface, "metalness")
            opacityPort = redshiftMaterial.GetPBRPort(standard_surface, "opacity")
            reflectionPort = redshiftMaterial.GetPBRPort(standard_surface, "transmission")
            glossinessPort = redshiftMaterial.GetPBRPort(standard_surface, "glossiness")

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
                        if redshiftMaterial.IsPortValid(glossinessPort):
                            tr.SetPortData(glossinessPort, True)

                    elif "Roughness" in tex_data:
                        roughnessNode = self.AddTextureTree(filepath=tex_data['Roughness'], shadername="Roughness", scaleramp=True, target_port=roughnessPort)

                else:
                    if "Metalness" in tex_data:
                        aoNode = self.AddTexture(filepath=tex_data['Metalness'], shadername="Metalness",target_port=metalnessPort)

                    if "Roughness" in tex_data:
                        roughnessNode = self.AddTextureTree(filepath=tex_data['Roughness'], shadername="Roughness", scaleramp=True, target_port=roughnessPort)

                    elif "Glossiness" in tex_data:
                        self.AddTextureTree(filepath=tex_data['Glossiness'], shadername="Glossiness", scaleramp=True, target_port=roughnessPort)
                        if redshiftMaterial.IsPortValid(glossinessPort):
                            tr.SetPortData(glossinessPort, True)

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

    def AddOpenPBRMaterial(
        self,
        inputs: list[NodeInput] | NodeInput = None,
        target: list[NodeInput] | NodeInput = None,
    ) -> maxon.GraphNode:
        """Add an OpenPBR material node and optionally connect it to graph ports.

        :param inputs: Optional source ports connected to the OpenPBR base color.
        :param target: Optional target ports connected from the OpenPBR output.
        :return: The newly created OpenPBR graph node.
        :rtype: maxon.GraphNode
        """
        return self.AddConnectShader(
            nodeID=self.openpbr_mat,
            input_ports=[self.PBR_PORTS[self.openpbr_mat]["diffuse"]],
            connect_inNodes=inputs,
            output_ports=[f"{self.openpbr_mat}.outcolor"],
            connect_outNodes=target,
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
        # 部分 Redshift 版本没有 inputtype 端口，不能将 None 传给 SetPortData。
        if self.IsPortValid(type_port):
            self.SetPortData(type_port, bump_mode)

        if input_port:
            if isinstance(input_port, maxon.GraphNode):
                input: maxon.GraphNode = self.GetPort(shader,'com.redshift3d.redshift4c4d.nodes.core.bumpmap.input')
                if self.IsPortValid(input):
                    input_port.Connect(input)

                
        output: maxon.GraphNode = self.GetPort(shader,'com.redshift3d.redshift4c4d.nodes.core.bumpmap.out')
        if not self.IsPortValid(output):
            shader.Remove()
            return None
        
        if target_port is not None:
            if isinstance(target_port, maxon.GraphNode):
                output.Connect(target_port)

        else:
            material = self.GetRootBRDF()
            if self.GetAssetId(material) == self.standard_mat:
                bump_port = self.GetPort(material,"com.redshift3d.redshift4c4d.nodes.core.standardmaterial.bump_input")
                if self.IsPortValid(bump_port):
                    output.Connect(bump_port)
            elif self.GetAssetId(material) == self.redshift_mat:
                bump_port = self.GetPort(material,"com.redshift3d.redshift4c4d.nodes.core.material.bump_input")
                if self.IsPortValid(bump_port):
                    output.Connect(bump_port)
            elif self.GetAssetId(material) == self.openpbr_mat:
                bump_port = self.GetPort(material,"com.redshift3d.redshift4c4d.nodes.core.openpbrmaterial.geometry_normal")
                if self.IsPortValid(bump_port):
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
                except Exception:
                    pass
                
        output: maxon.GraphNode = self.GetPort(shader,'com.redshift3d.redshift4c4d.nodes.core.displacement.out')
        
        if target_port is not None:
            if isinstance(target_port, maxon.GraphNode):                
                try:
                    output.Connect(target_port)
                except Exception:
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
        if not self.IsNode(shader):
            return None
        self.SetName(shader,shadername)
        
        texPort: maxon.GraphNode = self.GetPort(shader,"com.redshift3d.redshift4c4d.nodes.core.texturesampler.tex0")
        if not self.IsPortValid(texPort):
            shader.Remove()
            return None
        texFilenamePort: maxon.GraphNode = texPort.FindChild('path')
        colorspacePort: maxon.GraphNode = texPort.FindChild("colorspace")
        gammaPort: maxon.GraphNode = self.GetPort(shader,"com.redshift3d.redshift4c4d.nodes.core.texturesampler.tex0_gamma")
        if self.IsPortValid(gammaPort):
            self.SetPortData(gammaPort, gamma)
        # tex path
        if filepath is not None:
            if self.IsPortValid(texFilenamePort):
                self.SetPortData(texFilenamePort, filepath)
        
        # color space
        if raw:
            if self.IsPortValid(colorspacePort):
                self.SetPortData(colorspacePort, "RS_INPUT_COLORSPACE_RAW")
        else:
            if self.IsPortValid(colorspacePort):
                self.SetPortData(colorspacePort, "RS_INPUT_COLORSPACE_SRGB")
        
        # target connect
        if self.IsPortValid(target_port):
            if isinstance(target_port, maxon.GraphNode):
                outPort: maxon.GraphNode = self.GetPort(shader,'com.redshift3d.redshift4c4d.nodes.core.texturesampler.outcolor')
                try:
                    if self.IsPortValid(outPort):
                        outPort.Connect(target_port)
                except Exception:
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
        if not self.IsNode(tex_node):
            return None
        color_mutiplier_port = self.GetPort(tex_node,"com.redshift3d.redshift4c4d.nodes.core.texturesampler.color_multiplier")
        tex_output = self.GetPort(tex_node, "com.redshift3d.redshift4c4d.nodes.core.texturesampler.outcolor")
        if not self.IsPortValid(tex_output):
            tex_node.Remove()
            return None
        
        if color_mode:
            cc_node = self.AddColorCorrect(target=target_port)
            if not self.IsNode(cc_node):
                tex_node.Remove()
                return None
            self.AddConnection(
                tex_node,
                "com.redshift3d.redshift4c4d.nodes.core.texturesampler.outcolor",
                cc_node,
                "com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection.input",
            )
        
        else:
            cc_node = self.AddColorCorrect()
            if scaleramp:
                ramp_node = self.AddScalarRamp(target=target_port)
            else:
                ramp_node = self.AddRamp(target=target_port)
        
        if triplaner_node:
            triplaner_node = self.AddTriPlanar(tex_output, self.GetPort(cc_node,"com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection.input"))

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
    "MaterialHelper"
]
