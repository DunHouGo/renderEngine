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
from renderEngine.arnold import arnold_helper as ar
reload(ar)
from pprint import pprint
try:
    from arnold_id import *
except:
    from renderEngine.arnold.arnold_id import *
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
    print(f'Current render engine ID : {ar.GetRenderEngine(doc)}.')
    # Get the current render version.
    print(f'Current render engine version : {ar.GetVersion()}.')
    # Get the arnold core version.
    print(f'Current arnold core version : {ar.GetCoreVersion()}.')
    # Set the VideoPostHelper instance
    print(f'This is a VideoPostHelper instance of : {ar.VideoPostHelper(doc)}.')

#---------------------------------------------------------
# Example 02
# AOVHelper
#---------------------------------------------------------
def example_02_aovs():
    # Get arnold videopost
    videopost: c4d.documents.BaseVideoPost = ar.VideoPostHelper(doc).videopost
    # Set arnold AOVHelper instance
    aov_helper: ar.AOVHelper = ar.AOVHelper(videopost)
    
    # Start record undo
    aov_helper.doc.StartUndo()
    
    # Create a arnold Driver item
    exr_driver: c4d.BaseObject = aov_helper.create_aov_driver(isDisplay=False,driver_type=C4DAIN_DRIVER_EXR,denoise=True,sRGB=False)
    display_driver: c4d.BaseObject = aov_helper.create_aov_driver(isDisplay=True)
    
    # Create a arnold aov item(aov type must as same as the aov manager aov)
    # If #name is None, defulat to #beauty.
    diff_aov: c4d.BaseObject = aov_helper.create_aov_shader(aov_name='diffuse')
    # Add the DIFFUSE aov just created to the arnold aov system
    aov_helper.add_aov(driver=exr_driver,aov=diff_aov)
    
    # Add some aovs to exr_driver
    aov_helper.add_aov(exr_driver,aov_helper.create_aov_shader("N"))
    aov_helper.add_aov(exr_driver,aov_helper.create_aov_shader("Z"))
    aov_helper.add_aov(exr_driver,aov_helper.create_aov_shader("sheen"))
    aov_helper.add_aov(exr_driver,aov_helper.create_aov_shader("specular"))
    aov_helper.add_aov(exr_driver,aov_helper.create_aov_shader("transmission"))
    aov_helper.add_aov(exr_driver,aov_helper.create_aov_shader("emission"))
    aov_helper.add_aov(exr_driver,aov_helper.create_aov_shader("coat"))
    last_aov: c4d.BaseObject = aov_helper.add_aov(exr_driver,aov_helper.create_aov_shader("sss"))
    last_name: str = last_aov.GetName()
    
    # Add some aovs to display_driver
    aov_helper.add_aov(display_driver,aov_helper.create_aov_shader("N"))
    aov_helper.add_aov(display_driver,aov_helper.create_aov_shader("Z"))
    
    # Find driver
    print(f"We have an exr driver called{aov_helper.get_driver('EXR').GetName()}")
    print(f"We also have a dispaly driver called{aov_helper.get_dispaly_driver().GetName()}")

    # Set exr_driver render path
    aov_helper.set_driver_path(exr_driver,r"C:\Users\DunHou\Desktop\DelMe")

    # Get all aovs of exr_driver
    pprint(aov_helper.get_aovs(exr_driver))    
    
    # Remove last aov: sss
    aov_helper.remove_last_aov(exr_driver)
    print(f'We remove the last AOV named: {last_name}')
    
    # Remove specified aov: N of display_driver
    aov_helper.remove_aov_type(display_driver,'N')
    print('We remove the AOV type: N of the display_driver')
    
    # Get the #emission aov and his #name
    emission = aov_helper.get_aov(exr_driver,'emission')
    if emission:
        print(f'We find a AOV with Named {emission.GetName()}')
    
    # Print current aov info
    aov_helper.print_aov()
    
    # End record undo
    aov_helper.doc.EndUndo()
#---------------------------------------------------------
# Example 03
# MaterialHelper
#---------------------------------------------------------
if ar.IsNodeBased():
    
    #---------------------------------------------------------
    # Example 01
    # 创建材质
    # Standard Surface
    #---------------------------------------------------------
    def CreateStandard(name):
        # 创建Standard Surface材质
        arnoldMaterial = ar.MaterialHelper.CreateStandardSurface(name)
        # 将Standard Surface材质引入当前Document
        arnoldMaterial.InsertMaterial()
        # 将Standard Surface材质设置为激活材质
        arnoldMaterial.SetActive()
        
        return arnoldMaterial.material


    #---------------------------------------------------------
    # Example 02
    # 新建节点 修改属性
    # Add and Modify Standard Surface
    #---------------------------------------------------------
    def AddandModify(name):
        arnoldMaterial =  ar.MaterialHelper.CreateStandardSurface(name)

        # modification has to be done within a transaction
        with ar.ARMaterialTransaction(arnoldMaterial) as transaction:

            # Find brdf node (in this case : standard surface)
            standard_surface = arnoldMaterial.helper.GetRootBRDF()
            

            # Change a shader name
            arnoldMaterial.helper.SetName(standard_surface,'My BRDF Shader')
            
            # Create two noise and get their out port
            noise1 = arnoldMaterial.helper.add_shader('com.autodesk.arnold.shader.c4d_noise')
            n1_port =  arnoldMaterial.helper.GetPort(noise1,'output')
            noise2 = arnoldMaterial.AddMaxonNoise()
            n2_port =  arnoldMaterial.helper.GetPort(noise2,'output')
            
            # Get the specular_roughness port on the #standard_surface
            spc_rough = arnoldMaterial.helper.GetPort(standard_surface,'specular_roughness')

            # Add a #math add node and connect it between two noise shader output and specular_roughness
            arnoldMaterial.AddMathAdd([n1_port,n2_port], spc_rough)
            
            # # TexPath   
            url: maxon.Url = node_helper.get_asset_url(maxon.Id("file_5b6a5fe03176444c"))
            base_color = arnoldMaterial.helper.GetPort(standard_surface,'base_color')
            spc_color = arnoldMaterial.helper.GetPort(standard_surface,'specular_color')
            
            # Add a Texture node and set a tex to it , change color space to RAW
            # 添加一个Texture shader , 设置贴图路径,并将色彩空间设置为RAW
            tex_node = arnoldMaterial.AddTexture(shadername = 'YourTex', filepath = node_helper.get_asset_url(maxon.Id("file_2e316c303b15a330")), raw = True,target_port = spc_color)
            arnoldMaterial.helper.SetName(tex_node,'Specular')
            
            # Add a texture tree to base color
            # 将纹理节点树到 base color 节点中
            arnoldMaterial.AddTextureTree(shadername = 'YourTex',filepath = url, raw=False,target_port = base_color)
            # Add a Displace tree
            # 将置换节点树 
            arnoldMaterial.AddDisplacementTree(shadername = 'My Disp Tex',filepath=node_helper.get_asset_url(maxon.Id("file_6b69a957ef516e44")))

            # Add a Bump tree
            # 将凹凸节点树
            arnoldMaterial.AddNormalTree(filepath=node_helper.get_asset_url(maxon.Id("file_2ceb1d8bb35c56ba")))

        # 将Standard Surface材质引入当前Document
        arnoldMaterial.InsertMaterial()
        # 将Standard Surface材质设置为激活材质
        arnoldMaterial.SetActive()
        
        return arnoldMaterial.material

    #---------------------------------------------------------
    # Example 03
    # 修改已有材质
    # Modify Material
    #---------------------------------------------------------
    def ModifyMaterial(material: ar.MaterialHelper):
        """
        This function try to modify an exsit arnold material.
        """
        if material is None:
            return
        
        # for our example, the #material should be a instance of ar.MaterialHelper
        # then we can use our ARMaterialTransaction to modify
        if isinstance(material, ar.MaterialHelper):
            # modification has to be done within a transaction
            with ar.ARMaterialTransaction(material) as transaction:
                noise = material.AddMaxonNoise()

                output = material.helper.GetRootBRDF()                
                material.helper.AddConnection(noise,'output', output, 'base_color')
                
        # for suitable for most cases, the #material can be a c4d.BaseMaterial
        # we can transfer it to a instance of rs.MaterialHelper
        # then we can use our RSMaterialTransaction to modify                   
        if isinstance(material, c4d.BaseMaterial):
            material = ar.MaterialHelper(material)
            # modification has to be done within a transaction
            with ar.ARMaterialTransaction(material) as transaction:
                noise = material.AddMaxonNoise()
                output = material.helper.GetRootBRDF()                
                material.helper.AddConnection(noise,'output', output, 'base_color')
                
        return material.material
            
    #---------------------------------------------------------
    # Example 04
    # 创建pbr材质
    # Create PBR Material
    #---------------------------------------------------------
    def PBRMaterial():
        arnoldMaterial =  ar.MaterialHelper.CreateStandardSurface("PBR Example")
        arnoldMaterial.SetupTextures()
        # 将Standard Surface材质引入当前Document
        arnoldMaterial.InsertMaterial()
        # 将Standard Surface材质设置为激活材质
        arnoldMaterial.SetActive()
        arnoldMaterial.FastPreview()
        ar.OpenNodeEditor(arnoldMaterial.material)
        return arnoldMaterial.material


#---------------------------------------------------------
# Example 04
# SceneHelper
#---------------------------------------------------------
def example_04_scenes():
    # Set arnold SceneHelper instance
    scene_helper = ar.SceneHelper(doc)
    
    ### == Light == ###
    # Add a rig of hdr and rgb backdrop
    hdr_url: str =  node_helper.get_asset_str(maxon.Id("file_d21cf4cfdec8c636"))
    scene_helper.add_dome_rig(texture_path = hdr_url, rgb = c4d.Vector(0,0,0))
    
    # Add a light object and and some modify tags
    gobo_url: maxon.Url = node_helper.get_asset_url(maxon.Id("file_66b116a34a150e7e"))    
    gobo_light = scene_helper.add_gobo(texture_path = str(gobo_url), intensity=2, exposure=0)
    scene_helper.add_light_modifier(light = gobo_light, gsg_link = True, rand_color = True)
    
    # Add a IES light
    ies_url: str = node_helper.get_asset_str("file_6f300f2ba077da4a")
    ies = scene_helper.add_ies(texture_path = ies_url, intensity=1, exposure=0)
    
    ### == Tag == ###
    # Add a Cude object and an arnold tag with mask_name
    cube = c4d.BaseObject(c4d.Ocube)
    scene_helper.add_mask_tag(node=cube, mask_name='My Mask 01')
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
    example3 = ModifyMaterial(ar.MaterialHelper(example1))
    example3.SetName("3.Modify Material")
    example4 = PBRMaterial()
    # --- 4 --- #
    example_04_scenes()

    # Put Refresh
    c4d.EventAdd()