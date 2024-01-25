import c4d
import maxon
import Renderer
from Renderer import Redshift, Arnold, Octane, TextureHelper
from pprint import pprint

# Create a TextureHelper instance
tex_helper: TextureHelper = TextureHelper()

# How to create and modify redshift scene
def modify_redshift_scene():

    # Get the doc host the scene, in this case th active doc
    doc: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
    # Set Redshift SceneHelper instance
    scene_helper = Redshift.Scene(doc)
    
    ### == Light == ###
    # Add a rig of hdr and rgb backdrop
    hdr_url: str =  tex_helper.GetAssetStr("file_d21cf4cfdec8c636")
    scene_helper.add_dome_rig(texture_path = hdr_url, rgb = c4d.Vector(0,0,0))
    
    # Add a light object and and some modify tags
    gobo_url: maxon.Url = tex_helper.GetAssetStr("file_66b116a34a150e7e")
    mylight = scene_helper.add_light(light_name = 'My Light', texture_path = gobo_url, intensity=2, exposure=0)
    scene_helper.add_light_modifier(light = mylight, target = True, gsg_link = True, rand_color = True)
    # Add a IES light
    ies_url: str = tex_helper.GetAssetStr("file_6f300f2ba077da4a")
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
    scene_helper.auto_proxy(nodes=the_object,remove_objects=False)

# How to create and modify octane scene
def modify_octane_scene():

    # Get the doc host the scene, in this case th active doc
    doc: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
    # Set Octane SceneHelper instance
    scene_helper = Octane.Scene(doc)
    
    ### == Light == ###
    # Add a rig of hdr and rgb backdrop
    hdr_url: maxon.Url = tex_helper.GetAssetStr("file_d21cf4cfdec8c636")
    scene_helper.add_dome_rig(texture_path = hdr_url, rgb = c4d.Vector(0,0,0))
    # Add a light object and and some modify tags
    gobo_url: maxon.Url = tex_helper.GetAssetStr("file_66b116a34a150e7e") 
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
    scene_helper.auto_proxy(nodes=the_object,remove_objects=False)

# How to create and modify arnold scene
def modify_arnold_scene():

    # Get the doc host the scene, in this case th active doc
    doc: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
    # Set arnold SceneHelper instance
    scene_helper = Arnold.Scene(doc)
    
    ### == Light == ###
    # Add a rig of hdr and rgb backdrop
    hdr_url: str =  tex_helper.GetAssetStr(maxon.Id("file_d21cf4cfdec8c636"))
    scene_helper.add_dome_rig(texture_path = hdr_url, rgb = c4d.Vector(0,0,0))
    
    # Add a light object and and some modify tags
    gobo_url: maxon.Url = tex_helper.GetAssetUrl("file_66b116a34a150e7e")
    gobo_light = scene_helper.add_gobo(texture_path = str(gobo_url), intensity=2, exposure=0)
    scene_helper.add_light_modifier(light = gobo_light, gsg_link = True, rand_color = True)
    
    # Add a IES light
    ies_url: str = tex_helper.GetAssetStr("file_6f300f2ba077da4a")
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
    scene_helper.auto_proxy(nodes=the_object,remove_objects=False)

if __name__ == '__main__':
    Renderer.ClearConsole()
    modify_redshift_scene()
    # modify_octane_scene()
    # modify_arnold_scene()
    c4d.EventAdd()