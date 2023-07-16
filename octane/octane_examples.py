# Octane

###  ==========  Import Libs  ==========  ###
from typing import Optional
import c4d,maxon
from importlib import reload
from renderEngine.octane import octane_helper as oc
reload(oc)
from pprint import pprint
try:
    from octane_id import *
except:
    from renderEngine.octane.octane_id import *
from renderEngine import node_helper
reload(node_helper)

###  ==========  Author INFO  ==========  ###

__author__ = "DunHouGo"
__copyright__ = "Copyright (C) 2023 Boghma"
__website__ = "https://www.boghma.com/"
__license__ = "Apache-2.0 License"
__version__ = "2023.2.1"    

    
###  ==========  VideoPost  ==========  ###

doc: c4d.documents.BaseDocument  # The active document
op: Optional[c4d.BaseObject]  # The active object, None if unselected
render_path: str = r'Render/example/test.png'

#---------------------------------------------------------
# Example 01
# VideoPostHelper
#---------------------------------------------------------
def example_01_videopost():
    # Get the RenderEngine id.
    print(f'Current render engine ID : {oc.GetRenderEngine(doc)}.')
    # Get the current render version.
    print(f'Current render engine version : {oc.GetVersion()}.')
    # Set the VideoPostHelper instance
    videopost_helper = oc.VideoPostHelper(doc)
    # Set render setting
    videopost_helper.set_render_settings(file_path = render_path, use_exr = True, no_filters = False)
    print('We set octane render with custom (path/format/zip/filter)')

#---------------------------------------------------------
# Example 02
# AOVHelper
#---------------------------------------------------------
def example_02_aovs():
    # Get Octane videopost
    videopost: c4d.documents.BaseVideoPost = oc.VideoPostHelper(doc).videopost
    # Set Octane AOVHelper instance
    aov_helper = oc.AOVHelper(videopost)
    
    # Create a Octane aov item id can find from octane_id.py
    # If #name is None, defulat to type.
    diff_aov = aov_helper.create_aov_shader(aov_type = RNDAOV_DIFFUSE)
    # Add the DIFFUSE aov just created to the Octane aov system
    aov_helper.add_aov(diff_aov)
    
    # Add some aovs
    aov_helper.add_aov(aov_helper.create_aov_shader(aov_type = RNDAOV_POST,aov_name = 'POST'))
    aov_helper.add_aov(aov_helper.create_aov_shader(RNDAOV_DIF_D))
    aov_helper.add_aov(aov_helper.create_aov_shader(RNDAOV_DIF_I))
    aov_helper.add_aov(aov_helper.create_aov_shader(RNDAOV_REFL_D))
    aov_helper.add_aov(aov_helper.create_aov_shader(RNDAOV_REFL_I))
    aov_helper.add_aov(aov_helper.create_aov_shader(RNDAOV_WIRE))
    aov_helper.add_aov(aov_helper.create_aov_shader(RNDAOV_OBJECT_LAYER_COLOR))
    aov_helper.add_aov(aov_helper.create_aov_shader(RNDAOV_VOLUME))
    
    # Remove last aov: volume
    aov_helper.remove_last_aov()
    
    # Remove specified aov: wire
    aov_helper.remove_aov_type(aov_type = RNDAOV_WIRE)
    
    # Add 2 custom aovs with id 1 and 2
    aov_helper.add_custom_aov(customID = 1)
    aov_helper.add_custom_aov(customID = 2)
    
    # Get the custom aov with id 2
    custom2 = aov_helper.get_custom_aov(customID = 2)
    if custom2:
        print(f'We find a Custom AOV with id 2 Named{custom2.GetName()}')
        
    # Print current aov info
    aov_helper.print_aov()

#---------------------------------------------------------
# Example 03 A
# MaterialHelper
#---------------------------------------------------------
def example_03_materials_A():
    # Set Octane MaterialHelper instance
    MyMaterial = oc.MaterialHelper(doc)
    # Create a univeral material named 'MyMaterial'
    MyMaterial.CreateBasicMaterial(isMetal=False, matType=MAT_TYPE_UNIVERSAL, matName = "MyMaterial")
    # Add a float texture to roughness port
    MyMaterial.AddFloat(parentNode = c4d.OCT_MATERIAL_ROUGHNESS_LINK)
    # Add a node tree to Albedo port, and set path and props
    url: maxon.Url = node_helper.get_asset_str(maxon.Id("file_ed38c13fd1ae85ae"))    
    MyMaterial.AddTextureTree(texturePath = url, nodeName = 'Albedo', isFloat = False, gamma = 2.2,
                           invert = False, parentNode = c4d.OCT_MATERIAL_DIFFUSE_LINK)
    # Insert the material
    MyMaterial.InsertMaterial()
    # Set the material active
    MyMaterial.SetActive()
    # Open the Node Editor
    oc.OpenNodeEditor()
    # Get all shader in the material
    node_list = MyMaterial.GetAllNodes()
    # Print the info
    print(f'We create an Octane Material with name {MyMaterial.material.GetName()}')
    print('#-----Shader-----#')
    pprint(node_list)
    print('#----- End -----#')

#---------------------------------------------------------
# Example 03 B
# MaterialHelper
#---------------------------------------------------------
def example_03_materials_B():
    # Set Octane MaterialHelper instance
    MyMaterial = oc.MaterialHelper(doc)
    # Create a univeral material named 'MyMaterial'
    MyMaterial.CreateBasicMaterial(isMetal=False, matType=MAT_TYPE_UNIVERSAL, matName = "MyMaterial")
    # Setup a pbr material with given or selected texture.
    # We select a albedo texture of Megascans texture package here
    # But you can select almost any texture package here
    MyMaterial.SetupTextures()
    # Add a Transform node to all the Image nodes.
    MyMaterial.UniTransform()
    # Insert the material
    MyMaterial.InsertMaterial()
    # Set the material active
    MyMaterial.SetActive()
    # Open the Node Editor
    oc.OpenNodeEditor()
    # Get all shader in the material
    node_list = MyMaterial.GetAllNodes()
    # Print the info
    print(f'We create an Octane PBR Material with name {MyMaterial.material.GetName()}')
    print('#-----Shader-----#')
    pprint(node_list)
    print('#----- End -----#')

#---------------------------------------------------------
# Example 04
# SceneHelper
#---------------------------------------------------------
def example_04_scenes():
    # Set Octane SceneHelper instance
    scene_helper = oc.SceneHelper(doc)
    
    ### == Light == ###
    # Add a rig of hdr and rgb backdrop
    hdr_url: maxon.Url = node_helper.get_asset_str(maxon.Id("file_d21cf4cfdec8c636"))
    scene_helper.add_dome_rig(texture_path = hdr_url, rgb = c4d.Vector(0,0,0))
    # Add a light object and and some modify tags
    gobo_url: maxon.Url = node_helper.get_asset_str(maxon.Id("file_66b116a34a150e7e"))    
    mylight = scene_helper.add_light(power = 5, light_name = 'My Light', texture_path = gobo_url, distribution_path = None, visibility= False)
    scene_helper.add_light_modifier(light = mylight, target = True, gsg_link = True, rand_color = True)
    
    ### == Tag == ###
    # Add a Cude object and an Octane tag with layerID 2
    cube = c4d.BaseObject(c4d.Ocube)
    scene_helper.add_object_tag(node=cube, layerID=2)
    doc.InsertObject(cube)
    # Add a Sphere object and an Octane tag with custom aov id 2
    sphere = c4d.BaseObject(c4d.Osphere)
    scene_helper.add_custom_aov_tag(node=sphere, aovID=2)
    doc.InsertObject(sphere)
    # Add a Camera object and an Octane cam tag, then copy render setting data to it
    cam = c4d.BaseObject(c4d.Ocamera)
    doc.InsertObject(cam)
    camtag = scene_helper.add_camera_tag(node=cam)    
    videopost_helper = oc.VideoPostHelper(doc)
    videopost_helper.videopost_to_camera(camtag)
    
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
    
if __name__ == '__main__':
    # --- 1 --- #
    example_01_videopost()
    # --- 2 --- #
    example_02_aovs()
    # --- 3 --- #
    example_03_materials_A()
    example_03_materials_B()
    # --- 4 --- #
    example_04_scenes()
    
    # Put Refresh
    c4d.EventAdd()