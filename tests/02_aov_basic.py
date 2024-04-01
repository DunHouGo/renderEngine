import c4d
import maxon
import Renderer
from Renderer import Redshift, Arnold, Octane
from pprint import pprint


# How to create and modify redshift aovs
def modify_redshift_aov():

    # Get the videopost host the aovs
    doc: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
    vp: c4d.documents.BaseVideoPost = Renderer.GetVideoPost(doc, Renderer.ID_REDSHIFT)
    # Set redshift AOVHelper instance
    aov_helper = Redshift.AOV(vp)
    
    # Create a redshift aov item
    # the id can find from Renderer.constants.redshift,or Redshift.theid
    # If #name is None, defulat to type name of the aov.
    diff_aov = aov_helper.create_aov_shader(aov_type = Redshift.REDSHIFT_AOV_TYPE_BEAUTY)
    # Add the DIFFUSE aov just created to the redshift aov system
    aov_helper.add_aov(diff_aov)
    
    # Add some aovs
    aov_helper.add_aov(aov_helper.create_aov_shader(aov_type = Redshift.REDSHIFT_AOV_TYPE_SHADOWS, aov_name = 'My Shadow'))
    aov_helper.add_aov(aov_helper.create_aov_shader(Redshift.REDSHIFT_AOV_TYPE_NORMALS))
    aov_helper.add_aov(aov_helper.create_aov_shader(Redshift.REDSHIFT_AOV_TYPE_REFLECTIONS))
    aov_helper.add_aov(aov_helper.create_aov_shader(Redshift.REDSHIFT_AOV_TYPE_REFRACTIONS))
    aov_helper.add_aov(aov_helper.create_aov_shader(Redshift.REDSHIFT_AOV_TYPE_DEPTH))
    aov_helper.add_aov(aov_helper.create_aov_shader(Redshift.REDSHIFT_AOV_TYPE_EMISSION))
    aov_helper.add_aov(aov_helper.create_aov_shader(Redshift.REDSHIFT_AOV_TYPE_CRYPTOMATTE))
    last_aov = aov_helper.add_aov(aov_helper.create_aov_shader(Redshift.REDSHIFT_AOV_TYPE_OBJECT_ID))
    last_aov_name = aov_helper.get_name(last_aov)
    
    # Remove last aov: object id
    aov_helper.remove_last_aov()
    print(f'We remove the last AOV named: {last_aov_name}')
    
    # Remove specified aov: emission
    aov_helper.remove_aov_type(aov_type = Redshift.REDSHIFT_AOV_TYPE_EMISSION)
    print(f'We remove the AOV type: EMISSION @{Redshift.REDSHIFT_AOV_TYPE_EMISSION}')
    
    # update the depth aov "Use Camera Near/Far" to Flase
    aov_helper.update_aov(aov_type=Redshift.REDSHIFT_AOV_TYPE_DEPTH, aov_id=c4d.REDSHIFT_AOV_DEPTH_USE_CAMERA_NEAR_FAR, aov_attrib=False)
    print(f'We update the Depth AOV with attribute "Use Camera Near/Far" to False')
    
    # Set the #REFRACTION aov #name
    aov_helper.set_name(Redshift.REDSHIFT_AOV_TYPE_REFRACTIONS, "new refraction name")
    
    # Get the #SHADOW aov and his #name
    shadow = aov_helper.get_aovs(Redshift.REDSHIFT_AOV_TYPE_SHADOWS)
    if shadow:
        print(f'We find a AOV with Named {aov_helper.get_name(shadow)}')
               
    # Set the #REFRACTION aov #light group
    aov_helper.set_light_group(Redshift.REDSHIFT_AOV_TYPE_REFRACTIONS, "new group")
    print(f'We add a light group the REFRACTION AOV Named: new group')
    
    # Add a puzzle matte with same id(r=g=b), aka a white mask with given id
    aov_helper.set_puzzle_matte(puzzle_id = 2 ,aov_name = "My Puzzle 2")
    print(f'We add a white puzzle matte with ID = 2 , Name = "My Puzzle 2"')
    
    # Print current aov info
    aov_helper.print_aov()

# How to create and modify octane aovs
def modify_octane_aov():

    # Get the videopost host the aovs
    doc: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
    vp: c4d.documents.BaseVideoPost = Renderer.GetVideoPost(doc, Renderer.ID_OCTANE)
    # Set Octane AOVHelper instance
    aov_helper = Octane.AOV(vp)
    
    # Create a Octane aov item
    # the id can find from Renderer.constants.octane, or Octane.theid
    # If #name is None, defulat to type.
    diff_aov = aov_helper.create_aov_shader(aov_type = Octane.RNDAOV_DIFFUSE)
    # Add the DIFFUSE aov just created to the Octane aov system
    aov_helper.add_aov(diff_aov)
    
    # Add some aovs
    aov_helper.add_aov(aov_helper.create_aov_shader(aov_type = Octane.RNDAOV_POST,aov_name = 'POST'))
    aov_helper.add_aov(aov_helper.create_aov_shader(Octane.RNDAOV_DIF_D))
    aov_helper.add_aov(aov_helper.create_aov_shader(Octane.RNDAOV_DIF_I))
    aov_helper.add_aov(aov_helper.create_aov_shader(Octane.RNDAOV_REFL_D))
    aov_helper.add_aov(aov_helper.create_aov_shader(Octane.RNDAOV_REFL_I))
    aov_helper.add_aov(aov_helper.create_aov_shader(Octane.RNDAOV_WIRE))
    aov_helper.add_aov(aov_helper.create_aov_shader(Octane.RNDAOV_OBJECT_LAYER_COLOR))
    aov_helper.add_aov(aov_helper.create_aov_shader(Octane.RNDAOV_VOLUME))
    
    # Remove last aov: volume
    aov_helper.remove_last_aov()
    
    # Remove specified aov: wire
    aov_helper.remove_aov_type(aov_type = Octane.RNDAOV_WIRE)
    
    # Add 2 custom aovs with id 1 and 2
    aov_helper.add_custom_aov(customID = 1)
    aov_helper.add_custom_aov(customID = 2)
    
    # Get the custom aov with id 2
    custom2 = aov_helper.get_custom_aov(customID = 2)
    if custom2:
        print(f'We find a Custom AOV with id 2 Named{custom2.GetName()}')
        
    # Print current aov info
    aov_helper.print_aov()

# How to create and modify arnold aovs
def modify_arnold_aov():

    # Get the videopost host the aovs
    doc: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
    vp: c4d.documents.BaseVideoPost = Renderer.GetVideoPost(doc, Renderer.ID_ARNOLD)
    # Set Arnold AOVHelper instance
    aov_helper = Arnold.AOV(vp)

    # Start record undo
    aov_helper.doc.StartUndo()
    
    # Create a arnold Driver item
    exr_driver: c4d.BaseObject = aov_helper.create_aov_driver(isDisplay=False, driver_type=Arnold.C4DAIN_DRIVER_EXR, denoise=True, sRGB=False)
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

if __name__ == '__main__':
    Renderer.ClearConsole()
    modify_redshift_aov()
    # modify_octane_aov()
    # modify_arnold_aov()