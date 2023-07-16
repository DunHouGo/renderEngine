# -*- coding: utf-8 -*-  

# Maxon Cinema 4D version 2023.2.1

###  ==========  Copyrights  ==========  ###

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
__license__ = "Apache-2.0 License"
__version__ = "2023.2.1"
###  ==========  Import Libs  ==========  ###
from typing import Optional
import c4d,maxon
from importlib import reload
from renderEngine.redshift import redshift_helper as rs
reload(rs)
from pprint import pprint
try:
    from redshift_id import *
except:
    from renderEngine.redshift.redshift_id import *
from renderEngine import node_helper
reload(node_helper)


#=============================================
#                  Examples
#=============================================

       
#---------------------------------------------------------
# Example 01
# VideoPostHelper
#---------------------------------------------------------
def example_01_videopost():
    # Get the RenderEngine id.
    render_engine: int = rs.GetRenderEngine(doc)
    print(f'Current render engine ID : {render_engine}.')
    # Get the current render version.
    render_version: str = rs.GetVersion()
    print(f'Current render engine version : {render_version}.')
    # Set the VideoPostHelper instance
    videopost_helper = rs.VideoPostHelper(doc)
    # Set render setting
    videopost_helper.denoise_on(mode=4)
    print('We set redshift render with OIDN denoiser')

#---------------------------------------------------------
# Example 02
# AOVHelper
#---------------------------------------------------------
def example_02_aovs():
    # Get redshift videopost
    videopost: c4d.documents.BaseVideoPost = rs.VideoPostHelper(doc).videopost
    # Set redshift AOVHelper instance
    aov_helper = rs.AOVHelper(videopost)
    
    # Create a redshift aov item id can find from redshift_id.py
    # If #name is None, defulat to type name.
    diff_aov = aov_helper.create_aov_shader(aov_type = REDSHIFT_AOV_TYPE_BEAUTY)
    # Add the DIFFUSE aov just created to the redshift aov system
    aov_helper.add_aov(diff_aov)
    
    # Add some aovs
    aov_helper.add_aov(aov_helper.create_aov_shader(aov_type = REDSHIFT_AOV_TYPE_SHADOWS, aov_name = 'My Shadow'))
    aov_helper.add_aov(aov_helper.create_aov_shader(REDSHIFT_AOV_TYPE_NORMALS))
    aov_helper.add_aov(aov_helper.create_aov_shader(REDSHIFT_AOV_TYPE_REFLECTIONS))
    aov_helper.add_aov(aov_helper.create_aov_shader(REDSHIFT_AOV_TYPE_REFRACTIONS))
    aov_helper.add_aov(aov_helper.create_aov_shader(REDSHIFT_AOV_TYPE_DEPTH))
    aov_helper.add_aov(aov_helper.create_aov_shader(REDSHIFT_AOV_TYPE_EMISSION))
    aov_helper.add_aov(aov_helper.create_aov_shader(REDSHIFT_AOV_TYPE_CRYPTOMATTE))
    last_aov = aov_helper.add_aov(aov_helper.create_aov_shader(REDSHIFT_AOV_TYPE_OBJECT_ID))
    last_aov_name = aov_helper.get_name(last_aov)
    
    # Remove last aov: object id
    aov_helper.remove_last_aov()
    print(f'We remove the last AOV named: {last_aov_name}')
    
    # Remove specified aov: emission
    aov_helper.remove_aov_type(aov_type = REDSHIFT_AOV_TYPE_EMISSION)
    print(f'We remove the AOV type: EMISSION @{REDSHIFT_AOV_TYPE_EMISSION}')
    
    # update the depth aov "Use Camera Near/Far" to Flase
    aov_helper.update_aov(aov_type=REDSHIFT_AOV_TYPE_DEPTH, aov_id=c4d.REDSHIFT_AOV_DEPTH_USE_CAMERA_NEAR_FAR ,aov_attrib=False)
    print(f'We update the Depth AOV with attribute "Use Camera Near/Far" to False')
    
    # Set the #REFRACTION aov #name
    aov_helper.set_name(REDSHIFT_AOV_TYPE_REFRACTIONS, "new refraction name")
    
    # Get the #SHADOW aov and his #name
    shadow = aov_helper.get_aovs(REDSHIFT_AOV_TYPE_SHADOWS)
    if shadow:
        print(f'We find a AOV with Named {aov_helper.get_name(shadow)}')
               
    # Set the #REFRACTION aov #light group
    aov_helper.set_light_group(REDSHIFT_AOV_TYPE_REFRACTIONS, "new group")
    print(f'We add a light group the REFRACTION AOV Named: new group')
    
    # Add a puzzle matte with same id(r=g=b), aka a white mask with given id
    aov_helper.set_puzzle_matte(puzzle_id = 2 ,aov_name = "My Puzzle 2")
    print(f'We add a white puzzle matte with ID = 2 , Name = "My Puzzle 2"')
    
    # Print current aov info
    aov_helper.print_aov()

#---------------------------------------------------------
# Example 03
# MaterialHelper
#---------------------------------------------------------
if rs.IsNodeBased():
    
    #---------------------------------------------------------
    # Example 01
    # 创建材质
    # Standard Surface
    #---------------------------------------------------------
    def CreateStandard(name):
        # 创建Standard Surface材质
        redshiftMaterial = rs.MaterialHelper.CreateStandardSurface(name)
        # 将Standard Surface材质引入当前Document
        redshiftMaterial.InsertMaterial()
        # 将Standard Surface材质设置为激活材质
        redshiftMaterial.SetActive()
        
        return redshiftMaterial.material


    #---------------------------------------------------------
    # Example 02
    # 新建节点 修改属性
    # Add and Modify Standard Surface
    #---------------------------------------------------------
    def AddandModify(name):
        redshiftMaterial =  rs.MaterialHelper.CreateStandardSurface(name)

        # modification has to be done within a transaction
        with rs.RSMaterialTransaction(redshiftMaterial) as transaction:

            # Find brdf node (in this case : standard surface)
            # 查找Standard Surface节点
            standard_surface = redshiftMaterial.helper.GetRootBRDF()

            # Change a shader name
            # 更改Standard Surface节点名称
            redshiftMaterial.helper.SetName(standard_surface,'My BRDF Shader')


            # TexPath
            # 贴图路径
            url: maxon.Url = GetFileAssetUrl(maxon.Id("file_5b6a5fe03176444c"))
            tar = redshiftMaterial.helper.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.base_color')
            
            # Add a Texture node and set a tex to it , change color space to RAW
            # 添加一个Texture shader , 设置贴图路径,并将色彩空间设置为RAW
            # tex_node = redshiftMaterial.AddTexture(shadername = 'YourTex', filepath = url, raw = True)


            # Add a texture tree to base color
            # 将纹理节点树（triplaner）到 base color 节点中
            redshiftMaterial.AddTextureTree(shadername = 'tree', filepath = url, raw = True, triplaner_node = True, scaleramp = False, target_port = tar)
            
            # Add a Displace tree
            # 将置换节点树
            redshiftMaterial.AddDisplacementTree()
            
            # Add a Bump tree
            # 将凹凸节点树
            redshiftMaterial.AddBumpTree()

        # 将Standard Surface材质引入当前Document
        redshiftMaterial.InsertMaterial()
        # 将Standard Surface材质设置为激活材质
        redshiftMaterial.SetActive()
        
        return redshiftMaterial.material

    #---------------------------------------------------------
    # Example 03
    # 修改已有材质
    # Modify Material
    #---------------------------------------------------------
    def ModifyMaterial(material: rs.MaterialHelper):
        """
        This function try to modify an exsit redshift material.
        """
        if material is None:
            return
        
        # for our example, the #material should be a instance of rs.MaterialHelper
        # then we can use our RSMaterialTransaction to modify
        if isinstance(material, rs.MaterialHelper):
            # modification has to be done within a transaction
            with rs.RSMaterialTransaction(material) as transaction:

                # add a new STD shader
                noise = material.AddMaxonNoise()
                noise_out = material.helper.GetPort(noise, 'com.redshift3d.redshift4c4d.nodes.core.maxonnoise.outcolor')
                output = material.helper.GetRootBRDF()
                
                material.helper.AddConnection(noise,noise_out, output, rs.PortStr.base_color)
                
        # for suitable for most cases, the #material can be a c4d.BaseMaterial
        # we can transfer it to a instance of rs.MaterialHelper
        # then we can use our RSMaterialTransaction to modify                   
        if isinstance(material, c4d.BaseMaterial):
            material = rs.MaterialHelper(material)
            # modification has to be done within a transaction
            with rs.RSMaterialTransaction(material) as transaction:

                # add a new STD shader
                noise = material.AddMaxonNoise()
                noise_out = material.helper.GetPort(noise, 'com.redshift3d.redshift4c4d.nodes.core.maxonnoise.outcolor')
                output = material.helper.GetRootBRDF()
                
                material.helper.AddConnection(noise,noise_out, output, rs.PortStr.base_color)
        return material.material
            
    #---------------------------------------------------------
    # Example 04
    # 创建pbr材质
    # Create PBR Material
    #---------------------------------------------------------
    def PBRMaterial():
        redshiftMaterial =  rs.MaterialHelper.CreateStandardSurface("PBR Example")
        redshiftMaterial.SetupTextures()
        # 将Standard Surface材质引入当前Document
        redshiftMaterial.InsertMaterial()
        # 将Standard Surface材质设置为激活材质
        redshiftMaterial.SetActive()
        redshiftMaterial.FastPreview()
        rs.OpenNodeEditor(redshiftMaterial.material)
        return redshiftMaterial.material
    #---------------------------------------------------------
    # Example 05
    # 自定义生成ID
    # custom functions for IDs
    #---------------------------------------------------------
    def PrintID():
        # Mostly the string show in the node gui,then them can gennerate maxon id
        # 2023.2.1 Copy Id will not shipping useless str . it is easy to just copy
        # 输入界面显示的字符串就可以生成ID
        # 2023.2.1 复制ID不会附带多余字符串 可以直接复制id使用更方便
        StandardSurfaceShader = rs.ShaderID.StandardMaterial
        StandardOutputPortString = rs.PortStr.standard_outcolor
        StandardOutputPortID = rs.PortID.standard_outcolor
        curvature_out = rs.StrPortID("curvature", "out")    
        print("Name: " + str(StandardSurfaceShader), "Type: " , type(StandardSurfaceShader) )
        print("Name: " + str(StandardOutputPortString), "Type: " , type(StandardOutputPortString) )
        print("Name: " + str(StandardOutputPortID), "Type: " , type(StandardOutputPortID) )
        print("Name: " + str(curvature_out), "Type: " , type(curvature_out) )


#---------------------------------------------------------
# Example 04
# SceneHelper
#---------------------------------------------------------
def example_04_scenes():
    # Set Redshift SceneHelper instance
    scene_helper = rs.SceneHelper(doc)
    
    ### == Light == ###
    # Add a rig of hdr and rgb backdrop
    hdr_url: str =  node_helper.get_asset_str(maxon.Id("file_d21cf4cfdec8c636"))
    scene_helper.add_dome_rig(texture_path = hdr_url, rgb = c4d.Vector(0,0,0))
    
    # Add a light object and and some modify tags
    gobo_url: maxon.Url = node_helper.get_asset_str(maxon.Id("file_66b116a34a150e7e"))    
    mylight = scene_helper.add_light(light_name = 'My Light', texture_path = gobo_url, intensity=2, exposure=0)
    scene_helper.add_light_modifier(light = mylight, target = True, gsg_link = True, rand_color = True)
    # Add a IES light
    ies_url: str = node_helper.get_asset_str("file_6f300f2ba077da4a")
    ies = scene_helper.add_ies(light_name = 'My IES', texture_path = ies_url, intensity=1, exposure=0)
    
    ### == Tag == ###
    # Add a Cude object and an Redshift tag with maskID 2
    cube = c4d.BaseObject(c4d.Ocube)
    scene_helper.add_object_id(node=cube, maskID=2)
    doc.InsertObject(cube)
        
    ### == Object == ###
    # Add a scatter obejct with some children and count 12345
    generate_object = c4d.BaseObject(c4d.Oplane)
    doc.InsertObject(generate_object)
    scatter_A = c4d.BaseObject(c4d.Oplatonic)
    scatter_B = c4d.BaseObject(c4d.Ooiltank)
    doc.InsertObject(scatter_A)
    doc.InsertObject(scatter_B)
    scatters: list[c4d.BaseObject] = [scatter_A, scatter_B]
    scene_helper.add_scatter(generator_node=generate_object, scatter_nodes=scatters, count=12345)
    
    # Add a object and set auto proxy
    the_object = c4d.BaseObject(c4d.Oplane)
    doc.InsertObject(the_object)
    the_object.SetName("Original Object")
    scene_helper.auto_proxy(node=the_object,remove_objects=False)
    
if __name__ == '__main__':
    # --- 1 --- #    
    example_01_videopost()
    # --- 2 --- #    
    example_02_aovs()
    # --- 3 --- #
    example1 = CreateStandard("1.Standard Surface")
    example2 = AddandModify("2.Add and Modify Material")
    example3 = ModifyMaterial(rs.MaterialHelper(example1))
    example3.SetName("3.Modify Material")
    example4 = PBRMaterial()
    # --- 4 --- #
    example_04_scenes()
    # --- 5 --- #
    PrintID()

    # Put Refresh
    c4d.EventAdd()