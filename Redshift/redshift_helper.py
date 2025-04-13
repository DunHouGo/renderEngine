###  ==========  Import Libs  ==========  ###
import c4d
import maxon
import Renderer
if c4d.plugins.FindPlugin(Renderer.ID_REDSHIFT, type=c4d.PLUGINTYPE_ANY) is not None:
    import redshift
else:
    raise ImportError("Redshift plugin is not found.")
import os
import random
from typing import Union,Optional
from Renderer.constants.redshift_id import *
from Renderer.utils.node_helper import NodeGraghHelper, EasyTransaction

if c4d.plugins.FindPlugin(Renderer.ID_REDSHIFT, type=c4d.PLUGINTYPE_ANY) is None:
    class AOVHelper:
        """
        Custom helper to easier modify AOV.
        """

        def __init__(self, vp: c4d.documents.BaseVideoPost = None):

            if isinstance(vp, c4d.documents.BaseVideoPost):
                if vp.GetType() == int(Renderer.ID_REDSHIFT):
                    self.doc = vp.GetDocument()
                    self.vp: c4d.documents.BaseVideoPost = vp
                    self.vpname: str = self.vp.GetName()

            elif vp is None:
                self.doc: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
                self.vp: c4d.documents.BaseVideoPost = Renderer.GetVideoPost(self.doc, Renderer.ID_REDSHIFT)
                self.vpname: str = self.vp.GetName()

        def __str__(self) -> str:
            return (f'<Redshift> {__class__.__name__} with videopost named {self.vpname}')

        # 获取aov默认名称 ==> ok
        def get_type_name(self, aov_type: c4d.BaseList2D) -> str:
            """
            Get the name string of given aov type.
            """
            for i in REDSHIFT_AOVS:
                if i == aov_type:
                    return REDSHIFT_AOVS_NAME[REDSHIFT_AOVS.index(i)]

        # 获取aov名称 ==> ok
        def get_name(self, aov: Union[int,c4d.redshift.RSAOV] = None) -> str:
            """
            Get the name of given aov.
            """
            
            if aov is None:
                return
            
            if isinstance(aov, c4d.redshift.RSAOV):
                return aov.GetParameter(c4d.REDSHIFT_AOV_NAME)

            if isinstance(aov, int):
                return self.get_aov(aov).GetParameter(c4d.REDSHIFT_AOV_NAME)

        # 设置aov名称 ==> ok
        def set_name(self, aov: Union[int,c4d.redshift.RSAOV] = None, name: str = None) -> str:
            """
            Set the name of given aov.
            """
            if aov is None:
                return
            
            return self.update_aov(aov, c4d.REDSHIFT_AOV_NAME, aov_attrib = name)

        # 获取所有aov shader ==> ok
        def get_all_aovs(self) -> list[c4d.redshift.RSAOV] :
            """
            Get all aovs in a list.

            Returns:
                list[c4d.BaseShader]: A List of all find aovs
            """

            return redshift.RendererGetAOVs(self.vp)

        # 获取指定类型的aov列表 ==> ok
        def get_aovs(self, aov_type: c4d.BaseList2D) -> list[c4d.redshift.RSAOV]:
            """
            Get all the aovs of given type in a list.

            """
            if self.vp is None:
                raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
            
            aov_list: list = []
            
            # keep original aovs
            current_aovs = redshift.RendererGetAOVs(self.vp)
            for aov in current_aovs:
                if aov.GetParameter(c4d.REDSHIFT_AOV_TYPE) == aov_type:
                    aov_list.append(aov)

            return aov_list
        
        # 获取指定类型的aov shader ==> ok
        def get_aov(self, aov_type: c4d.BaseList2D) -> Union[c4d.redshift.RSAOV , None]:
            """
            Get the aov of given type.

            """
            if self.vp is None:
                raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
                    
            # keep original aovs
            current_aovs = redshift.RendererGetAOVs(self.vp)
            for aov in current_aovs:
                if aov.GetParameter(c4d.REDSHIFT_AOV_TYPE) == aov_type:
                    return aov

            return None
        
        # 打印aov ==> ok
        def print_aov(self):
            if self.vp is None:
                raise RuntimeError(f"Can't get the {self.vpname} VideoPost")

            aovs = redshift.RendererGetAOVs(self.vp)
            aovCnt = len(aovs)
            
            print ("--- REDSHIFTRENDER ---")
            
            print ("Name:", self.vp.GetName())
            print ("Color space:", self.vp[c4d.REDSHIFT_RENDERER_COLOR_MANAGEMENT_OCIO_RENDERING_COLORSPACE])
            print ("AOV count:", aovCnt)        
            
            for aov in aovs:
                aov_name = aov.GetParameter(c4d.REDSHIFT_AOV_NAME)
                aov_type = aov.GetParameter(c4d.REDSHIFT_AOV_TYPE)
                if aov_name == '':
                    aov_name = REDSHIFT_AOVS_NAME[aov_type]
                
                print("-----------------------------------------------------------")
                print("Name                  :%s" % aov_name)
                print("Type                  :%s" % str(REDSHIFT_AOVS[aov_type]))
                print("Enabled               :%s" % ("Yes" if aov.GetParameter(c4d.REDSHIFT_AOV_ENABLED) else "No"))
                print("Multi-Pass            :%s" % ("Yes" if aov.GetParameter(c4d.REDSHIFT_AOV_MULTIPASS_ENABLED) else "No"))
                print("Direct                :%s" % ("Yes" if aov.GetParameter(c4d.REDSHIFT_AOV_FILE_ENABLED) else "No"))
                print("Direct Path           :%s" % aov.GetParameter(c4d.REDSHIFT_AOV_FILE_PATH))
                print("Direct Effective Path :%s" % aov.GetParameter(c4d.REDSHIFT_AOV_FILE_EFFECTIVE_PATH)) # Available from 2.6.44/3.0.05
            
            print ("--- REDSHIFTRENDER ---")
        
        # 创建aov ==> ok
        def create_aov_shader(self, aov_type: c4d.BaseList2D, aov_enabled: bool = True, aov_name: str = None, muti_enabled: bool = True, muti_bit: int = 16) -> c4d.redshift.RSAOV:
                    
            if self.vp is None:
                raise RuntimeError(f"Can't get the {self.vpname} VideoPost")

            aov: c4d.redshift.RSAOV = redshift.RSAOV()
            aov.SetParameter(c4d.REDSHIFT_AOV_TYPE, aov_type)
            aov.SetParameter(c4d.REDSHIFT_AOV_ENABLED, aov_enabled)
            if aov_name is not None:
                aov.SetParameter(c4d.REDSHIFT_AOV_NAME, aov_name)
            else:
                aov.SetParameter(c4d.REDSHIFT_AOV_NAME, self.get_type_name(aov_type))
            aov.SetParameter(c4d.REDSHIFT_AOV_MULTIPASS_ENABLED, muti_enabled)
            
            # zip
            if muti_bit == 16: 
                bit = c4d.REDSHIFT_AOV_MULTIPASS_BIT_DEPTH_16
            elif muti_bit == 8:
                bit = c4d.REDSHIFT_AOV_MULTIPASS_BIT_DEPTH_8
            elif muti_bit == 32:
                bit = c4d.REDSHIFT_AOV_MULTIPASS_BIT_DEPTH_32
            else:
                bit = c4d.REDSHIFT_AOV_MULTIPASS_BIT_DEPTH_16
            aov.SetParameter(c4d.REDSHIFT_AOV_MULTIPASS_BIT_DEPTH, bit)
            
            # denoise
            try:
                aov.SetParameter(c4d.REDSHIFT_AOV_DENOISE_ENABLED, True)
            except:
                pass        

            return aov
        
        # 为aov添加属性,在添加到vp之前 ==> ok
        def set_aov(self, aov_shader: c4d.BaseList2D , aov_id : int, aov_attrib):
                    
            if self.vp is None:
                raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
            if not isinstance(aov_shader,c4d.redshift.RSAOV):
                raise ValueError(f"Aov must be the {self.vpname} aov")

            aov_shader.SetParameter(aov_id, aov_attrib)
        
        # 更新aov属性 ==> ok
        # todo新建的AOV会丢失属性
        def update_aov_old(self, aov_type: Union[int, c4d.redshift.RSAOV], aov_id : int, aov_attrib) -> c4d.redshift.RSAOV:
            if self.vp is None:
                raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
            
            if isinstance(aov_type, c4d.redshift.RSAOV):
                aovshader = aov_type
            if isinstance(aov_type, int):
                aovshader = self.get_aov(aov_type) 
                
            aovshader = self.get_aov(aov_type)
            if aovshader is None:
                return
            
            aov_list: list = []
            # keep original aovs
            current_aovs = redshift.RendererGetAOVs(self.vp)
            self.remove_aov_type(aov_type)
            for aov in current_aovs:
                if aov.GetParameter(c4d.REDSHIFT_AOV_TYPE) == aov_type:
                    aov_list.append(aovshader)
                else:
                    aov_list.append(aov)
            
            self.set_aov(aovshader,aov_id, aov_attrib)
            # set aovs
            redshift.RendererSetAOVs(self.vp, aov_list)
            return aovshader

        def update_aov(self, aov_type: Union[int, c4d.redshift.RSAOV], aov_id: int, aov_attrib):
            allaovs = self.get_all_aovs()
            aov_update_list = []
            for aov in allaovs:
                if aov.GetParameter(c4d.REDSHIFT_AOV_TYPE) == aov_type:
                    aov_update_list.append(aov)
            aovs_temp = [allaovs.remove(aov_update) for aov_update in aov_update_list]
            [self.set_aov(aov_update, aov_id, aov_attrib) for aov_update in aov_update_list]
            aovs_temp.extend(aov_update_list)
            return redshift.RendererSetAOVs(self.vp, aovs_temp)

        # 将aov添加到vp ==> ok
        def add_aov(self, aov_shader: Union[c4d.redshift.RSAOV,list[c4d.redshift.RSAOV]]):
            
            if self.vp is None:
                raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
            if not isinstance(aov_shader,c4d.redshift.RSAOV):
                raise ValueError(f"Aov must be the {self.vpname} aov")
            
            aov_list: list = []

            # aov
            if isinstance(aov_shader, c4d.redshift.RSAOV):
                
                # keep original aovs
                current_aovs = redshift.RendererGetAOVs(self.vp)
                for aov in current_aovs:
                    aov_list.append(aov)
                # add our new aov  
                aov_list.append(aov_shader)
                # set aovs
                redshift.RendererSetAOVs(self.vp, aov_list)

            # aovs
            if isinstance(aov_shader, list):
                
                # keep original aovs
                current_aovs = redshift.RendererGetAOVs(self.vp)
                # merge aovs
                aov_list = current_aovs + aov_shader
                # set aovs
                redshift.RendererSetAOVs(self.vp, aov_list)
            return aov_shader

        # 删除最新的aov ==> ok
        def remove_last_aov(self):
            """
            Remove the last aov shader.

            """
            # index: Union[int,c4d.BaseList2D]
            
            if self.vp is None:
                raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
            
            aovs = redshift.RendererGetAOVs(self.vp)
            del(aovs[-1])
            redshift.RendererSetAOVs(self.vp, aovs)

        # 删除全部aov ==> ok
        def remove_all_aov(self):
            """
            Remove all the aov shaders.

            """
            
            if self.vp is None:
                raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
            aovs = []
            redshift.RendererSetAOVs(self.vp, aovs)  
                        
        # 按照Type删除aov ==> ok
        def remove_aov_type(self, aov_type: int):
            """
            Remove aovs of the given aov type.

            :param aov_type: the aov type to remove
            :type aov_type: int
            """
            if self.vp is None:
                raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
            
            aov_list: list = []
            
            # keep original aovs
            current_aovs = redshift.RendererGetAOVs(self.vp)
            for aov in current_aovs:
                if aov.GetParameter(c4d.REDSHIFT_AOV_TYPE) == aov_type:
                    continue
                aov_list.append(aov)
            # set aovs
            redshift.RendererSetAOVs(self.vp, aov_list)

        # 添加灯光组 ==> ok
        def set_light_group(self, aov: c4d.redshift.RSAOV, group_name: str = None):
            if aov is None:
                return
            if group_name is None:
                return
            
            if isinstance(aov, c4d.redshift.RSAOV):
                aovtype = 	aov.GetParameter(c4d.REDSHIFT_AOV_TYPE)
                aovshader = aov
            if isinstance(aov, int):
                aovtype = aov
                aovshader = self.get_aov(aov)
            or_str = aovshader.GetParameter(c4d.REDSHIFT_AOV_LIGHTGROUP_NAMES)
            if or_str == "":
                group_str = group_name + "\n"
            else:
                group_str = or_str + "\n" + group_name + "\n"
            self.update_aov(aov_type=aovtype, aov_id=c4d.REDSHIFT_AOV_LIGHTGROUP_NAMES, aov_attrib=group_str)

        # 添加灯光组 ==> ok   
        def active_light_group(self, aov: c4d.redshift.RSAOV, group_name: str = None):
            if aov is None:
                return
            if group_name is None:
                return
            or_group = aov.GetParameter(c4d.REDSHIFT_AOV_LIGHTGROUP_NAMES)
            
            if group_name not in or_group:
                group_str = or_group + "\n" + group_name.strip() + "\n"
                self.set_light_group(aov,group_str)
                
        # 添加纯白puzzle matte ==> ok
        def set_puzzle_matte(self, puzzle_id: int = 1, aov_enabled: bool = True, aov_name: str = None, muti_enabled: bool = True, muti_bit: int = 16):
            if self.vp is None:
                raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
            if aov_name is not None:
                aov_name = aov_name
            else:
                aov_name =  "Puzzle " + str(puzzle_id)
            
            aov = self.create_aov_shader(REDSHIFT_AOV_TYPE_PUZZLE_MATTE, aov_enabled, aov_name, muti_enabled, muti_bit)
            
            # object mode
            aov.SetParameter(c4d.REDSHIFT_AOV_PUZZLE_MATTE_MODE, REDSHIFT_AOV_PUZZLE_MATTE_MODE_OBJECT_ID)        
            # set a white puzzle
            aov.SetParameter(c4d.REDSHIFT_AOV_PUZZLE_MATTE_RED_ID, puzzle_id)
            aov.SetParameter(c4d.REDSHIFT_AOV_PUZZLE_MATTE_GREEN_ID, puzzle_id)
            aov.SetParameter(c4d.REDSHIFT_AOV_PUZZLE_MATTE_BLUE_ID, puzzle_id)
            aov.SetParameter(c4d.REDSHIFT_AOV_PUZZLE_MATTE_REFLECTION_REFRACTION, False)
            self.add_aov(aov)
            return aov
else:
    class AOVHelper:
        def __init__(self):
            print("Redshift is not installed on this machine.")

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
        nodeMaterial.CreateDefaultGraph(Renderer.RS_NODESPACE)  

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
    def SetupTextures(self, tex_data: dict = None, mat_name: Optional[str] = None):
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

    def GetRootBRDF(self, filter: Union[str,int] = 0) -> maxon.GraphNode:
        """
        Returns the very first brdf shader connect to output

        Args:
            filter (Union[str,int], optional): filter to get the object, fill ``str`` to filter by name, fill ``int`` to filter by index. Defaults to 0.

        Returns:
            maxon.GraphNode: the BRDF node
        """

        standard_mat = "com.redshift3d.redshift4c4d.nodes.core.standardmaterial"
        rs_mat = "com.redshift3d.redshift4c4d.nodes.core.material"
        valid_mat = [standard_mat, rs_mat]

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
            nodeID ="com.redshift3d.redshift4c4d.nodes.core.standardmaterial",
            input_ports = ['com.redshift3d.redshift4c4d.nodes.core.standardmaterial.base_color'],
            connect_inNodes = inputs,
            output_ports=['com.redshift3d.redshift4c4d.nodes.core.standardmaterial.outcolor'], 
            connect_outNodes = target
            )
    
    def AddRSMaterial(self,  inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    
    def AddMaterialBlender(self,  inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    
    def AddMaterialLayer(self,  inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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

    def AddIncandescent(self,  inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    
    def AddSprite(self,  inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddInvert(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddColorConstant(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddColorSplitter(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddColorComposite(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddColorLayer(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddColorChangeRange(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddColorCorrect(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddValue(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None, mode: Union[str,maxon.Id] = maxon.Id("float")) -> maxon.GraphNode :
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
    def AddMathMix(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddVectorMix(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddColorMix(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddMathAdd(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddVectorAdd(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddMathSub(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddVectorSub(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddColorSub(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddMathMul(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddVectorMul(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddMathDiv(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddVectorDiv(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
            bump_port = self.GetPort(material,"com.redshift3d.redshift4c4d.nodes.core.standardmaterial.bump_input")
            output.Connect(bump_port)
        return shader
    
    # 创建Bump Blender ==> OK
    def AddBumpBlender(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddDisplacementBlender(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddRoundCorner(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddFresnel(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddAO(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddCurvature(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddFlakes(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddPointAttribute(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddVertexAttribute(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddRamp(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddScalarRamp(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddTriPlanar(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddMaxonNoise(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
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
    def AddUniTransform(self, tex_shader: maxon.GraphNode) -> Optional[maxon.GraphNode]:
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
    def AddUniTransforms(self, tex_shaders: list[maxon.GraphNode]) -> Optional[maxon.GraphNode]:
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


class SceneHelper:

    """
    Class for Secne Objects, Tags, Lights, Proxy and so on.
    """

    def __init__(self, document: c4d.documents.BaseDocument = None):
        if document is None:
            document: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
        self.doc: c4d.documents.BaseDocument = document

    def _add_unseltag(self, node: c4d.BaseObject):
        if not isinstance(node,c4d.BaseObject):
            raise ValueError("Must be a BaseObject")
        unseltag = c4d.BaseTag(440000164) # Interaction Tag
        unseltag[c4d.INTERACTIONTAG_SELECT] = True # INTERACTIONTAG_SELECT
        node.InsertTag(unseltag) # insert tag 

    ### Light ###        

    def add_hdr_dome(self, color_space: str = '', texture_path: str = None, intensity: float = 1.0, exposure: float = 0.0, seen_by_cam: bool = True) -> c4d.BaseObject :
        """
        Add a texture (hdr) dome light to the scene.

        :param texture_path: HDR image path
        :type texture_path: str
        :param unselect: True if the dome can not be select, defaults to True
        :type unselect: bool, optional
        :param mode: True to primray mode,othervise to visible, defaults to True
        :type mode: bool, optional
        :return: the image texture node and the sky object
        :rtype: list[c4d.BaseTag, c4d.BaseObject]
        """

        light = c4d.BaseObject(ID_REDSHIFT_LIGHT)
        light[c4d.REDSHIFT_LIGHT_TYPE] = 4
        self.doc.InsertObject(light)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,light)
        light.SetName("RS HDR Dome")
        light[c4d.REDSHIFT_LIGHT_DOME_MULTIPLIER] = intensity
        light[c4d.REDSHIFT_LIGHT_DOME_EXPOSURE0] = exposure
        if texture_path:
            light[c4d.REDSHIFT_LIGHT_DOME_TEX0,c4d.REDSHIFT_FILE_PATH] = texture_path
        light[c4d.REDSHIFT_LIGHT_DOME_TEX0,c4d.REDSHIFT_FILE_COLORSPACE] = color_space
        light[c4d.REDSHIFT_LIGHT_DOME_BACKGROUND_ENABLE] = seen_by_cam
        
        return light

    def add_rgb_dome(self, rgb: c4d.Vector = c4d.Vector(0,0,0),intensity: float = 1.0, exposure: float = 0.0, seen_by_cam: bool = True) -> list[c4d.BaseTag, c4d.BaseObject]:
        """
        Add a rgb dome light to the scene.

        :param rgb: rgb color value
        :type rgb: c4d.Vector
        :param unselect: True if the dome can not be select, defaults to True
        :type unselect: bool, optional
        :param mode: True to primray mode,othervise to visible, defaults to True
        :type mode: bool, optional
        :return: the rgb node and the sky object
        :rtype: list[c4d.BaseTag, c4d.BaseObject]
        """
        light = c4d.BaseObject(ID_REDSHIFT_LIGHT)
        light[c4d.REDSHIFT_LIGHT_TYPE] = 4
        self.doc.InsertObject(light)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,light)
        light.SetName("RS RGB Dome")
        light[c4d.REDSHIFT_LIGHT_DOME_COLOR] = rgb
        light[c4d.REDSHIFT_LIGHT_DOME_MULTIPLIER] = intensity
        light[c4d.REDSHIFT_LIGHT_DOME_EXPOSURE0] = exposure
        light[c4d.REDSHIFT_LIGHT_DOME_BACKGROUND_ENABLE] = seen_by_cam 
        
        return light
    
    def add_dome_rig(self, texture_path: str, rgb: c4d.Vector = c4d.Vector(0,0,0)):
        """
        Add a HDR and visible dome light folder.

        :param texture_path: hdr image path
        :type texture_path: str
        :param unselect: True if the dome can not be select, defaults to True
        :type unselect: bool, optional
        """
        hdr_dome: c4d.BaseObject = self.add_hdr_dome(texture_path=texture_path, seen_by_cam = False)
        black_dome: c4d.BaseObject = self.add_rgb_dome(rgb=rgb)
        null = c4d.BaseObject(c4d.Onull)
        null.SetName("Environment")
        null[c4d.ID_BASELIST_ICON_FILE] = '1052837'
        null[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 1
        null[c4d.ID_BASELIST_ICON_COLOR] = c4d.Vector(0.008, 0.659, 0.902)
        self.doc.InsertObject(null)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,null)
        hdr_dome.InsertUnder(null)
        black_dome.InsertUnder(null)
        hdr_dome.DelBit(c4d.BIT_ACTIVE)
        black_dome.DelBit(c4d.BIT_ACTIVE)
        null.SetBit(c4d.BIT_ACTIVE)
        # Unfold the null if it is fold
        if null.GetNBit(c4d.NBIT_OM1_FOLD) == False:
            null.ChangeNBit(c4d.NBIT_OM1_FOLD, c4d.NBITCONTROL_TOGGLE)
        return hdr_dome
        
    def add_light(self, light_name: str = None, texture_path: str = None, intensity: float = 1.0, exposure: float = 0.0) -> c4d.BaseObject :        
        
        light = c4d.BaseObject(ID_REDSHIFT_LIGHT)
        self.doc.InsertObject(light)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,light)
        # 定义灯光属性
        light[c4d.REDSHIFT_LIGHT_PHYSICAL_AREA_GEOMETRY] = 0
        if light_name:
            light.SetName(light_name)
        else:
            light.SetName('Redshift Light')
        light[c4d.REDSHIFT_LIGHT_PHYSICAL_INTENSITY] = intensity
        light[c4d.REDSHIFT_LIGHT_PHYSICAL_EXPOSURE] = exposure
        
        if texture_path:
            light[c4d.REDSHIFT_LIGHT_PHYSICAL_TEXTURE,c4d.REDSHIFT_FILE_PATH] = texture_path
         
        return light

    def add_light_texture(self, light: c4d.BaseObject = None,  texture_path: str = None, opacity_texture: bool = True) -> c4d.BaseObject :
        """
        Add textures to given light.

        """
        if not light.CheckType(ID_REDSHIFT_LIGHT):
            raise ValueError("This is not a Redshift light")
        
        # Texture
        if texture_path:
            try:
                light[c4d.REDSHIFT_LIGHT_PHYSICAL_TEXTURE,c4d.REDSHIFT_FILE_PATH] = texture_path
            except:
                light[c4d.REDSHIFT_LIGHT_IES_PROFILE,c4d.REDSHIFT_FILE_PATH] = texture_path                
        return light
        
    def add_ies(self, light_name: str = None, intensity: float = 1.0, exposure: float = 0.0, texture_path: str = None) -> c4d.BaseObject :
        light = c4d.BaseObject(ID_REDSHIFT_LIGHT)
        self.doc.InsertObject(light)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,light)
        # 定义灯光属性
        light[c4d.REDSHIFT_LIGHT_TYPE] = 5 # ies
        if light_name:
            light.SetName(light_name)
        else:
            light.SetName('Redshift IES')
        light[c4d.REDSHIFT_LIGHT_IES_MULTIPLIER] = intensity
        light[c4d.REDSHIFT_LIGHT_IES_EXPOSURE] = exposure
        light[c4d.REDSHIFT_LIGHT_PREVIEW] = False
        
        if texture_path:
            light[c4d.REDSHIFT_LIGHT_IES_PROFILE,c4d.REDSHIFT_FILE_PATH] = texture_path
         
        return light
    
    def add_gobo(self,light_name: str = None, intensity: float = 250000.0, exposure: float = -3.0, texture_path: str = None) -> c4d.BaseObject :
        light = c4d.BaseObject(ID_REDSHIFT_LIGHT)
        self.doc.InsertObject(light)
        
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,light)
        # 定义灯光属性
        light[c4d.REDSHIFT_LIGHT_PHYSICAL_AREA_GEOMETRY] = 2 # spot
        if light_name:
            light.SetName(light_name)
        else:
            light.SetName('Redshift Gobo')
        light[c4d.REDSHIFT_LIGHT_IES_MULTIPLIER] = int(intensity)
        light[c4d.REDSHIFT_LIGHT_IES_EXPOSURE] = int(exposure)
        light[c4d.REDSHIFT_LIGHT_PREVIEW] = False
        
        if texture_path:
            light[c4d.REDSHIFT_LIGHT_PHYSICAL_TEXTURE,c4d.REDSHIFT_FILE_PATH] = texture_path
         
        return light
    
    def add_sun_rig(self, sky_intensity: int = 1, sun_intensity: int =1):
        sky = c4d.BaseObject(ID_REDSHIFT_RSSKY)
        sky.SetName( "Redshift Sky")
        sun = c4d.BaseObject(ID_REDSHIFT_LIGHT)
        sky.SetName( "Redshift Sun")
        sun[c4d.REDSHIFT_LIGHT_PHYSICAL_AREA_GEOMETRY] = 7 # sun
        self.doc.InsertObject(sky)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,sky)
        self.doc.InsertObject(sun)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,sun)
        sky[c4d.REDSHIFT_SKY_PHYSICALSKY_SUN] = sun
        
        sky[c4d.REDSHIFT_SKY_PHYSICALSKY_MULTIPLIER] = int(sky_intensity)
        sky[c4d.REDSHIFT_SKY_PHYSICALSKY_SUN_DISK_INTENSITY] = int(sun_intensity)
         
        return sky

    def add_light_modifier(self, light: c4d.BaseObject, target: c4d.BaseObject = None, gsg_link: bool = False, rand_color: bool = False, seed: int = 0):
        
        # 新建目标标签
        if target is not None:        
            mbtag = c4d.BaseTag(5676) # target
            self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, mbtag)
            if isinstance(target, c4d.BaseObject):
                mbtag[c4d.TARGETEXPRESSIONTAG_LINK] = target
            light.InsertTag(mbtag)
        
        # GSG HDR LINK
        if gsg_link:
            try:            
                gsglink = c4d.plugins.FindPlugin(1037662, type=c4d.PLUGINTYPE_TAG)
                if gsglink:
                    linktag = c4d.BaseTag(1037662)
                    light.InsertTag(linktag)
                    linktag[2001] = ''
            except:
                pass
        
        # 随机颜色
        if rand_color:
            light[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 1
            
            if seed == 0:
                randcolor = c4d.Vector(*Renderer.generate_random_color(1))
            else:
                random.seed(seed)
                randcolor = NodeGraghHelper.generate_random_color(1)
            light[c4d.ID_BASELIST_ICON_COLOR] = randcolor

    ### Tag ###
    
    def add_object_id(self, node : c4d.BaseObject, maskID: int = 2) -> c4d.BaseTag:
        mask_tag = c4d.BaseTag(ID_REDSHIFT_TAG)
        node.InsertTag(mask_tag)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,mask_tag)
        if maskID:
            mask_tag[c4d.REDSHIFT_OBJECT_OBJECTID_OVERRIDE] = True
            mask_tag[c4d.REDSHIFT_OBJECT_OBJECTID_ID] = int(maskID)
        return mask_tag    
        
    def add_object_tag(self, node : c4d.BaseObject) -> c4d.BaseTag:
        object_tag = c4d.BaseTag(ID_REDSHIFT_TAG)
        node.InsertTag(object_tag)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,object_tag)        
        return object_tag
    
    ### Object ### 
                  
    def add_scatter(self, generator_node: c4d.BaseObject, scatter_nodes: list[c4d.BaseObject], selectedtag: c4d.SelectionTag = None, count: int = None) -> c4d.BaseObject :
        """ 
        Add a scatter object of given generator_node and scatter_nodes[vertex optional].
        """
        # __init pram__
        ModifierID = 1018545 # c4d.Omgmatrix # R2023
        ModifierName = 'RS Scatter : '
        objName = generator_node.GetName()
        if count is None:
            count = random.randint(0,1234567)
        # Modifier config
        Modifier = c4d.BaseObject(ModifierID) #  ID
        #  Config settings
        Modifier[c4d.ID_MG_MOTIONGENERATOR_MODE] = 0
        Modifier[c4d.MG_OBJECT_LINK] = generator_node
        Modifier[c4d.MG_POLYSURFACE_SEED] = count
        Modifier[c4d.MG_POLY_MODE_] = 3 # surface
        Modifier.SetName(ModifierName + objName)
        if selectedtag :
            Modifier[c4d.MG_POLY_SELECTION] = selectedtag.GetName()
            
        rs_tag = c4d.BaseTag(ID_REDSHIFT_TAG)
        Modifier.InsertTag(rs_tag)
        
        if scatter_nodes:
            data = c4d.InExcludeData()
            for node in scatter_nodes :
                data.InsertObject(node,1)                
            rs_tag[c4d.REDSHIFT_OBJECT_PARTICLE_MODE] = 4 # object mode
            rs_tag[c4d.REDSHIFT_OBJECT_PARTICLE_CUSTOM_OBJECTS] = data

        self.doc.InsertObject(Modifier)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,Modifier) # Undo
    
        return Modifier

    def add_env(self, emisson: c4d.Vector = c4d.Vector(0,0,0), seen_by_camera: bool = True) -> c4d.BaseObject :
        env = c4d.BaseObject(ID_REDSHIFT_ENVIROMENT)
        self.doc.InsertObject(env)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,env)
        env[c4d.REDSHIFT_ENVIRONMENT_VOLUMESCATTERING_FOG_AMBIENT] = emisson
        if not seen_by_camera:
            env[c4d.REDSHIFT_ENVIRONMENT_VOLUMESCATTERING_FOG_AMBIENT] = 0
        return env
        
    def add_vdb(self, name: str = None, vdb_path: str = None) -> c4d.BaseObject :
        vdb = c4d.BaseObject(ID_REDSHIFT_VOLUME) # Create the object.
        if name:
            vdb.SetName(name)
        else:            
            vdb.SetName('Redshift Volume')
        
        if vdb_path:
            vdb[c4d.REDSHIFT_VOLUME_FILE,c4d.REDSHIFT_FILE_PATH] = vdb_path
            
            try:
                vdb[c4d.REDSHIFT_VOLUME_VELOCITY_GRID_X] = 'velocity'
                vdb[c4d.REDSHIFT_VOLUME_VELOCITY_GRID_Y] = 'velocity'
                vdb[c4d.REDSHIFT_VOLUME_VELOCITY_GRID_Z] = 'velocity'
                vdb[c4d.REDSHIFT_VOLUME_CHANNELS] = 'density\ntemperature\nvelocity\n'
            except:
                pass
        vdb_obj = self.doc.InsertObject(vdb)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,vdb)
        return vdb_obj

    def add_proxy(self, name: str = None, proxy_path: str = None, mesh: bool = True, mode: int = None) -> c4d.BaseObject :
        proxy = c4d.BaseObject(ID_REDSHIFT_PROXY)
        self.doc.InsertObject(proxy)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,proxy)
        if name:
            proxy.SetName(name)
        else:
            proxy.SetName('Redshift Proxy')
        
        if proxy_path:
            if os.path.isfile(str(proxy_path)):
                proxy[c4d.REDSHIFT_PROXY_FILE,c4d.REDSHIFT_FILE_PATH] = proxy_path
                
        if mesh:
            proxy[c4d.REDSHIFT_PROXY_DISPLAY_MODE] = REDSHIFT_PROXY_DISPLAY_MODE_MESH
            
        if mode:
            proxy[c4d.REDSHIFT_PROXY_MATERIAL_MODE] = mode
        return proxy

    def auto_proxy(self, node : c4d.BaseObject , filepath: str = None, remove_objects: bool = False):
        if not isinstance(node,c4d.BaseObject):
            raise ValueError("must be a BaseObject.")
        
        # Find the Redshift Proxy Export plugin
        plug = c4d.plugins.FindPlugin(redshift.Frsproxyexport, c4d.PLUGINTYPE_SCENESAVER)
        if plug is None:
            raise RuntimeError("Pluging not found")

        # Send MSG_RETRIEVEPRIVATEDATA to the plugin to retrieve the state
        op = {}
        if not plug.Message(c4d.MSG_RETRIEVEPRIVATEDATA, op):
            return False

        # BaseList2D object stored in "imexporter" key holds the settings
        if "imexporter" not in op:
            return False
        imexporter = op["imexporter"]
        
        # Single frame export
        imexporter[c4d.REDSHIFT_PROXYEXPORT_ANIMATION_RANGE] = c4d.REDSHIFT_PROXYEXPORT_ANIMATION_RANGE_CURRENT_FRAME

        # Keep the default beauty config in the proxy. Used primarily when exporting entire scenes for rendering with the redshiftCmdLine tool
        imexporter[c4d.REDSHIFT_PROXYEXPORT_AOV_DEFAULT_BEAUTY]	= False

        # Don't need lights in our proxies
        imexporter[c4d.REDSHIFT_PROXYEXPORT_EXPORT_LIGHTS] = False

        # Automatic object replacement with proxies
        # Proxy contents will be offset around the selection cetner
        imexporter[c4d.REDSHIFT_PROXYEXPORT_OBJECTS] = c4d.REDSHIFT_PROXYEXPORT_OBJECTS_SELECTION
        imexporter[c4d.REDSHIFT_PROXYEXPORT_ORIGIN] = c4d.REDSHIFT_PROXYEXPORT_ORIGIN_WORLD #REDSHIFT_PROXYEXPORT_ORIGIN_OBJECTS for Boundingbox

        imexporter[c4d.REDSHIFT_PROXYEXPORT_AUTOPROXY_CREATE] = True
        imexporter[c4d.REDSHIFT_PROXYEXPORT_REMOVE_OBJECTS] = False
                
        # 对象实例
        ex_node: c4d.BaseObject = node.GetClone()
        mg = c4d.Matrix()
        ex_node.SetMg(mg)
        self.doc.InsertObject(ex_node) # 0,0,0
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, ex_node) 
        
        
        # 执行导出
        for obj in self.doc.GetActiveObjects(1) :
            self.doc.AddUndo(c4d.UNDOTYPE_BITS, obj)
            obj.DelBit(c4d.BIT_ACTIVE)
        
        if filepath is None:
            proxy_path = os.path.join(self.doc.GetDocumentPath(),"_Proxy") # Proxy Temp Folder
            if not os.path.exists(proxy_path):
                os.makedirs(proxy_path)
            filepath = os.path.join(self.doc.GetDocumentPath(), "_Proxy", node.GetName())
        self.doc.SetSelection(ex_node)

        c4d.documents.SaveDocument(self.doc, filepath, c4d.SAVEDOCUMENTFLAGS_DONTADDTORECENTLIST, redshift.Frsproxyexport) 
        self.doc.AddUndo(c4d.UNDOTYPE_DELETEOBJ, ex_node)   
        ex_node.Remove()
        
        # 程序对象
        proxy = self.doc.GetFirstObject()
        if not (isinstance(proxy, c4d.BaseObject) and
                proxy.CheckType(1038649)):
            raise TypeError("Can not find the proxy.")
        self.doc.AddUndo(c4d.UNDOTYPE_CHANGE, proxy)    
        # 重置坐标
        proxy.SetMg(node.GetMg())
        proxy_clone: c4d.BaseObject  = proxy.GetClone()
        self.doc.AddUndo(c4d.UNDOTYPE_DELETEOBJ, node)
        proxy.Remove()
        self.doc.InsertObject(proxy_clone, pred=node, checknames=True)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, proxy)   
        proxy_clone.SetName(node.GetName() + "_Proxy")
        proxy_clone.SetMg(node.GetMg())
        
        if remove_objects == True:
            self.doc.AddUndo(c4d.UNDOTYPE_DELETEOBJ, node)
            node.Remove()   

        return proxy

    def get_bakeable_nodes(self, select_nodes:list[c4d.BaseObject]) -> list :
        nodes = []
        for node in select_nodes :  
                            
            self.doc.AddUndo(c4d.UNDOTYPE_BITS,node)
            node.DelBit(c4d.BIT_ACTIVE)
            
            if isinstance(node, c4d.PointObject):
                if node.GetTag(c4d.Tuvw) is not None :
                    nodes.append(node)
        return nodes

    def add_bakeset(self, nodes : list[c4d.BaseObject], resolution: int = 2048) -> c4d.BaseObject :
        if isinstance(nodes, c4d.BaseObject):
            nodes = [nodes]
        if isinstance(nodes, list):
            nodes = nodes

        data = c4d.InExcludeData()
        nodes = self.get_bakeable_nodes(nodes)
        for node in nodes :
            data.InsertObject(node,1)
            self.doc.AddUndo(c4d.UNDOTYPE_BITS,node)
            node.DelBit(c4d.BIT_ACTIVE)
        bakeset = c4d.BaseObject(ID_REDSHIFT_BAKESET)
        bakeset[c4d.REDSHIFT_BAKESET_WIDTH] = resolution
        bakeset[c4d.REDSHIFT_BAKESET_HEIGHT] = resolution
        bakeset[c4d.REDSHIFT_BAKESET_OBJECTS] = data
        self.doc.InsertObject(bakeset)
        self.doc.AddUndo(c4d.UNDOTYPE_BITS,bakeset)
        bakeset.SetBit(c4d.BIT_ACTIVE)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,bakeset)

# todo
# coding more...