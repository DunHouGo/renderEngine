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
from typing import Generator, Union,Optional
from Renderer.constants.vray_id import *
from Renderer.utils.node_helper import NodeGraghHelper, EasyTransaction


class AOVHelper:

    """
    Custom helper to modify Vray AOVs. vray aovs store in render element scene hook with c4d.BaseObject.
    """

    def __init__(self, vp: c4d.documents.BaseVideoPost = None):
        
        if isinstance(vp, c4d.documents.BaseVideoPost):
            if vp.GetType() == int(Renderer.ID_VRAY):
                self.doc = vp.GetDocument()
                self.vp: c4d.documents.BaseVideoPost = vp
                self.vpname: str = self.vp.GetName()
                self.head: c4d.GeListHead = self.get_master_head()

        elif vp is None:
            self.doc: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
            self.vp: c4d.documents.BaseVideoPost = Renderer.GetVideoPost(self.doc, Renderer.ID_VRAY)
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
            name = f"VRAY_AOV_{node.GetName()}"
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
        sceneHook: c4d.BaseList2D = self.doc.FindSceneHook(ID_VRAY_RENDER_ELEMENTS_SCENE_HOOK)
        if sceneHook is None:
            return None
        info = sceneHook.GetBranchInfo(c4d.GETBRANCHINFO_NONE)
        if info is None:
            return None
        head = info[0]["head"]
        if head is None:
            return None
        return head

    def get_type(self, node: c4d.BaseObject) -> int:
        """Get the type of the given node."""
        return node.GetParameter(VRAY_RENDER_ELEMENT_CREATE_NODE_TYPE, c4d.DESCFLAGS_GET_NONE)

    def get_name(self, node: c4d.BaseObject) -> str:
        """Get the name of the given node."""
        return node.GetName()

    def get_enable(self, node: c4d.BaseObject) -> bool:
        """Get the enable check of the given node."""
        return node.GetParameter(VRAY_RENDER_ELEMENT_ENABLED, c4d.DESCFLAGS_GET_NONE)

    def get_filter(self, node: c4d.BaseObject) -> bool:
        """Get the filter check of the given node."""
        return node.GetParameter(VRAY_RENDER_ELEMENT_FILTER_PARAMETER_ID, c4d.DESCFLAGS_GET_NONE)

    def get_denoise(self, node: c4d.BaseObject) -> bool:
        """Get the denoise check of the given node."""
        return node.GetParameter(VRAY_RENDER_ELEMENT_DENOISE_PARAMETER_ID, c4d.DESCFLAGS_GET_NONE)

    def set_type(self, node: c4d.BaseObject, arg: int) -> bool:
        """Set the type of the given node."""
        return node.SetParameter(VRAY_RENDER_ELEMENT_CREATE_NODE_TYPE, arg, c4d.DESCFLAGS_SET_NONE)

    def set_name(self, node: c4d.BaseObject, arg: str) -> str:
        """Set the name of the given node."""
        return node.SetName(arg)

    def set_enable(self, node: c4d.BaseObject, arg: int) -> bool:
        """Set the enable check of the given node."""
        return node.SetParameter(VRAY_RENDER_ELEMENT_ENABLED, arg, c4d.DESCFLAGS_GET_NONE)

    def set_filter(self, node: c4d.BaseObject, arg: int) -> bool:
        """Set the filter check of the given node."""
        return node.SetParameter(VRAY_RENDER_ELEMENT_FILTER_PARAMETER_ID, arg, c4d.DESCFLAGS_GET_NONE)

    def set_denoise(self, node: c4d.BaseObject, arg: int) -> bool:
        """Set the denoise check of the given node."""
        return node.SetParameter(VRAY_RENDER_ELEMENT_DENOISE_PARAMETER_ID, arg, c4d.DESCFLAGS_GET_NONE)

    # 获取所有aov shader ==> ok
    def get_all_aovs(self) -> list[c4d.BaseShader] :
        """
        Get all vray aovs in a list.

        Returns:
            list[c4d.BaseShader]: A List of all find nodes

        """
        
        """Get all render elements in the scene."""
        res = []
        for node in self.iterater(self.get_master_head().GetFirst()):
            res.append(node)
        return res

    # 获取指定类型的aov shader ==> ok
    def get_aov(self, aov_type: c4d.BaseObject) -> list[c4d.BaseObject]:
        """
        Get all the aovs of given type in a list.
        
        Args:
            aov_type (Union[c4d.BaseObject, c4d.BaseShader]): Shader to iterate.
            
        Returns:
            list[c4d.BaseObject]: A List of all find aovs

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
        color_space = self.vp[c4d.SETTINGSUNITSINFO_RGB_COLOR_SPACE]
        if color_space == 1:
            color_str = "sRGB"
        elif color_space == 2:
            color_str = "ACEScg"
                      
        print ("--- VRAY RENDER ---")
        print ("Name:", self.vp.GetName())
        print ("Color space:", color_str)
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

                    
                    #print(SET_RENDERAOV_INPUT_0)
                    # print('aov1',self.vp[SET_RENDERAOV_INPUT_0])
                    #print(SET_RENDERAOV_INPUT_0+1)
                            
                    # Z-Depth
                    if aov_type == 117:
                        print ("Subdata: Z-depth black:",aov[c4d.RENDERCHANNELZDEPTH_DEPTH_BLACK],
                               "Z-depth white:",aov[c4d.RENDERCHANNELZDEPTH_DEPTH_WHITE],
                               "Invert:",aov[c4d.RENDERCHANNELZDEPTH_DEPTH_INVERT])

                    # Cryptomatte
                    if aov_type == 158:
                        print ("Subdata: Cryptomatte type:", aov[c4d.RENDERCHANNELCRYPTOMATTE_ID_TYPE])
                
        print ("--- VRAY RENDER ---")

    # 创建aov ==> ok
    def create_aov_shader(self, aov_type: list[int], aov_name: str = None) -> c4d.BaseShader :
        """
        Create a shader of vray aov.

        :param aov_tye: the aov int type, this is a list of main id and sub type of the aov, find it in vray_id.py
        :type aov_tye: int, optional
        :param aov_name: the aov name, defaults to ""
        :type aov_name: str, optional 
        :return: the aov shader
        :rtype: c4d.BaseShader
        """
        if not isinstance(aov_type, list):
            raise ValueError("We should use a custom list data here: [the object type, the sub type, aov nae(optional)]")

        aov = c4d.BaseObject(aov_type[0])
        self.set_type(aov, aov_type[1])

        if aov_name:
            self.set_name(aov, aov_name)
        else:
            self.set_name(aov, aov_type[2])

        return aov
    
    # 将aov添加到vp ==> ok
    def add_aov(self, aov_shader: c4d.BaseObject) -> c4d.BaseObject:
        """
        Add the vray aov shader to Octane Render.

        :param aov_shader: the vray aov shader
        :type aov_shader: c4d.BaseObject
        :return: the vray aov shader
        :rtype: c4d.BaseList2D
        """
        if not isinstance(aov_shader, c4d.BaseObject):
            raise ValueError("Vray AOV must be a c4d.BaseObject")
        
        # insert octane_aov to new port
        try:
            self.head.InsertFirst(aov_shader)
            self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,aov_shader)
        except:
            pass        
        return aov_shader

    # 为aov添加属性 ==> ok
    def set_aov(self, aov_shader: c4d.BaseList2D , aov_id : int, aov_attrib)-> c4d.BaseShader :
        """
        A helper fucnction to set aov data.

        """
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        if not isinstance(aov_shader,c4d.BaseList2D):
            raise ValueError(f"Aov must be the {self.vpname} aov shader which is a BaseList2D")    
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
        self.nimbusRef = self.material.GetNimbusRef(Renderer.VR_NODESPACE)

        if isinstance(self.material, c4d.Material):
            nodeMaterial = self.material.GetNodeMaterialReference()
            self.graph: maxon.GraphModelInterface = nodeMaterial.GetGraph(Renderer.VR_NODESPACE)

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


    def AddMix(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new math multiply shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.chaos.vray_node.texmix",
            input_ports = ['com.chaos.vray_node.texmix.color1', 'com.chaos.vray_node.texmix.color2', 'com.chaos.vray_node.texmix.mix_map'],
            connect_inNodes = inputs,
            output_ports=['com.chaos.vray_node.texmix.output.default'], 
            connect_outNodes = target
            )

    ### Bump ###

    # 创建Bump ==> # todo
    def AddRootBump(self, input_port: maxon.GraphNode = None) -> maxon.GraphNode :
        """
        Adds a new displacement shader to the graph.

        """
        if self.graph is None:
            return None
        nodeId = "com.chaos.vray_node.brdfbump"
        # shader: maxon.GraphNode = self.graph.AddChild("", nodeId, maxon.DataDictionary())
        brdf = self.GetRootBRDF()
        wiredata = brdf.GetWires(self.GetOutput())
        # brdf_out = self.GetPort(brdf, "com.chaos.vray_node.brdfvraymtl.output.default")

        displacement = self.InsertShader(nodeId, wiredata, "com.chaos.vray_node.brdfbump.base_brdf","com.chaos.vray_node.brdfbump.output.default")

        if input_port:
            if isinstance(input_port, maxon.GraphNode):
                input: maxon.GraphNode = self.GetPort(displacement,'com.chaos.vray_node.brdfbump.bump_tex_color')
                try:
                    input_port.Connect(input)
                except:
                    pass
                
        # output: maxon.GraphNode = self.GetPort(shader,'com.chaos.vray_node.brdfbump.output.default')
        
        # if target_port is not None:
        #     if isinstance(target_port, maxon.GraphNode):                
        #         try:
        #             output.Connect(target_port)
        #         except:
        #             pass

        # else:
        #     output = self.GetOutput()
        #     dis_port = self.GetPort(output,"com.chaos.vray_node.mtlsinglebrdf.brdf")
        #     output.Connect(dis_port)
        return displacement
    
    # 创建Normal ==> OK
    def AddNormal(self, input_port: maxon.GraphNode = None, target_port: maxon.GraphNode = None, bump_mode: int = 1) -> maxon.GraphNode :
        """
        Adds a new Normal shader to the graph.

        """
        if self.graph is None:
            return None

        shader: maxon.GraphNode = self.graph.AddChild("", "com.chaos.vray_node.texnormalbump", maxon.DataDictionary())
        type_port = self.GetPort(shader, 'com.chaos.vray_node.texnormalbump.map_type')
        self.SetPortData(type_port, bump_mode)

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
            self.SetPortData(texPort, filepath)
        
        # color space
        if raw:
            self.SetPortData(colorspacePort, 0)
        else:
            self.SetPortData(colorspacePort, 1)
        
        # target connect
        if target_port:
            if isinstance(target_port, maxon.GraphNode):
                outPort: maxon.GraphNode = self.GetPort(shader,'com.chaos.vray_node.texbitmap.output.default')
                # print(outPort)
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
        self.SetPortData(blendNode,blend)

        if inputA is not None:
            self.RemoveConnection(inputA)
            inputA.Connect(input1)
        if inputB is not None:
            inputB.Connect(input2)
        if target is not None:
            output.Connect(target)
        return layerNode

    # 创建TriPlanar ==> OK
    def AddTriPlanar(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new TriPlanar shader to the graph.

        """
        return self.AddConnectShader(
            nodeID ="com.chaos.vray_node.textriplanar",
            input_ports = ['com.chaos.vray_node.textriplanar.texture_x'],
            connect_inNodes = inputs,
            output_ports=['com.chaos.vray_node.textriplanar.output.default'], 
            connect_outNodes = target
            )


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
        color_mutiplier_port = self.GetPort(tex_node,"com.chaos.vray_node.texbitmap.color_mult")
        
        if color_mode:
            cc_node = self.AddColorCorrect(target=target_port)
        
        else:
            cc_node = self.AddColorCorrect()
            if scaleramp:
                ramp_node = self.AddRemap(target=target_port)
        
        if triplaner_node:
            triplaner_node = self.AddTriPlanar(self.GetPort(tex_node,"com.chaos.vray_node.textriplanar.texture_x"), 
                                               self.GetPort(cc_node,"com.chaos.vray_node.textriplanar.output.default"))

        else:
            self.AddConnection(tex_node, "com.chaos.vray_node.texbitmap.output.default", 
                               cc_node, "com.chaos.vray_node.colorcorrection.texture_map")
        
        if not color_mode:
            if scaleramp:
                self.AddConnection(cc_node, "com.chaos.vray_node.colorcorrection.output.default",
                                   ramp_node, "com.chaos.vray_node.texremap.input_color")
            else:
                self.AddConnection(cc_node, "com.chaos.vray_node.colorcorrection.output.default",
                                   ramp_node, "com.redshift3d.redshift4c4d.nodes.core.rsramp.input")
        
        if color_mutiplier:
            self.AddConnection(color_mutiplier, "com.chaos.vray_node.texbitmap.color_mult", tex_node, color_mutiplier_port)
        
        return tex_node

    # todo
    def AddDisplacementTree(self, shadername :str = 'Displacement', filepath: str = None, triplaner_node: bool = False) -> list[maxon.GraphNode] :
        """
        Adds a displacement tree (tex + displacement) to the graph.
        """
        if self.graph is None:
            return None
        # add        
        tex_node = self.AddTexture(shadername, filepath, True)
        # tex_in = self.GetPort(tex_node, "com.redshift3d.redshift4c4d.nodes.core.texturesampler.tex0")
        tex_out = self.GetPort(tex_node, "com.chaos.vray_node.texbitmap.output.default")

        if triplaner_node:
            triplaner_node = self.AddTriPlanar(tex_out)
            tex_out = self.GetPort(triplaner_node, self.GetConvertOutput(triplaner_node))

        self.AddRootBump(input_port=tex_out)


    def AddBumpTree(self, shadername :str = 'Bump', filepath: str = None, bump_mode: int = 1, target_port: maxon.GraphNode = None, triplaner_node: bool = False) -> list[maxon.GraphNode] :
        """
        Adds a bump tree (tex + bump) to the graph.
        """
        if self.graph is None:
            return None

        # add        
        tex_node = self.AddTexture(shadername, filepath, True)
        tex_out = self.GetPort(tex_node, "com.chaos.vray_node.texbitmap.output.default")
        if triplaner_node:
            triplaner_node = self.AddTriPlanar(tex_out)
            tex_out = self.GetPort(triplaner_node, self.GetConvertOutput(triplaner_node))
        #tex_out = self.GetPort(tex_node, "com.redshift3d.redshift4c4d.nodes.core.texturesampler.outcolor")
        self.AddNormal(input_port=tex_out, target_port=target_port, bump_mode=bump_mode)

# todo
# coding more...