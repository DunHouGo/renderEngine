# Octane
This is a custom api for Octane Render in Cinema 4D, which is also wiil contains in 'boghma' library.
```
All the boghma plugins and boghma library is FREE.
```
## Installation
To use this library, you have two options:
1. Download the source and import it to your Cinema 4D
2. (**Not Ready Now**) You can also download [Boghma Plugin Manager](https://www.boghma.com/) and install any plugin, the boghma lib will auto installed.


# Limit
Due to otoy use a custom userarea for the node editor, and don't support python. We can not get the selection of the node edtor, so it is not possible to interact with node editor. 

# Class Presentation

## octane_id
#### This Class contains unique ids for octane object, and name map of aovs.

## octane_helper
#### This Class contains the functions for the library. And it has some children Classes.
- __Functions(functions)__
- __VideoPostHelper__
- __AOVData__
- __AOVHelper__
- __MaterialHelper__
- __SceneHelper__

### octane Class/method highlighted:
#### This Class contains methods for the library. It has the following methods:

  - __GetRenderEngine__ : Return current render engine ID.
  - __GetVersion__ : Get the version number of Octane.
  - __OpenIPR__ : Open Live Viewer.
  - __OpenNodeEditor__ : Open Node Editor for given material.
  - __AovManager__ : Open aov Manager.
  - __TextureManager__ : Open Octane Texture Manager.


### AOVData:
    
#### Octane AOV dataclass structure

- __aov_shader__: c4d.BaseShader
- __aov_enabled__: bool
- __aov_name__: str
- __aov_type__: c4d.BaseList2D
- __aov_subdata__: list

### AOVHelper Class/method highlighted:

  - __get_aov_data__ : Get all aov data in a list of BaseContainer.
  - __get_all_aovs__ : Get all octane aovs in a list.
  - __get_aov__ : Get all the aovs of given type in a list.
  - __read_aov__ : Get aov data in a list of AOVData Class.
  - __print_aov__ : Print main info of existed aov in python console.
  - __create_aov_shader__ : Create a shader of octane aov.
  - __add_aov__ : Add the octane aov shader to Octane Render.
  - __remove_last_aov__ : Remove the last aov shader.
  - __remove_empty_aov__ : Romove all the empty aov shaders.
  - __remove_all_aov__ : Remove all the aov shaders.
  - __remove_aov_type__ : Remove aovs of the given aov type.
  - __get_custom_aov__ : Get the custom aov shader of given id.
  - __add_custom_aov__ : Add the custom aov shader of given id if it not existed.
  - __get_light_aov__ : Get the light aov shader of given id.
  - __add_light_aov__ : Add the light aov shader of given id if it not existed.

### NodeHelper Class/method highlighted:

  - __GetAllNodes__ : Get all nodes of the material in a list.
  - __GetNodes__ : Get all nodes of given type of the material in a list.
  - __RefreshTextures__ : Refresh all the Texture shader.
  - __ResetCompression__ : Reset all the texture shader compression.
  - __AddShader__ : Add a shader to the material of the given type and slot.
  - __AddTransform__ : Add a Transform shader to the given slot(option).
  - __Addrojection__ : Add a Projection shader to the given slot(option).
  - __AddMultiply__ : Add a Multiply shader to the given slot(option).
  - __AddSubtract__ : Add a Subtract shader to the given slot(option).
  - __AddMathAdd__ : Add a MathAdd shader to the given slot(option).
  - __AddMix__ : Add a Mix shader to the given slot(option).
  - __AddInvert__ : Add a Invert shader to the given slot(option).
  - __AddFloat__ :Add a Float shader to the given slot(option).
  - __AddRGB__ : Add a RGB shader to the given slot(option).
  - __AddImageTexture__ : Add a ImageTexture shader to the given slot(option).
  - __AddCC__ : Add a Color Correction shader to the given slot(option).
  - __AddGradient__ : Add a Gradient shader to the given slot(option).
  - __AddFalloff__ : Add a Falloff shader to the given slot(option).
  - __AddDirt__ : Add a Dirt shader to the given slot(option).
  - __AddCurvature__ : Add a Curvature shader to the given slot(option).
  - __AddNoise4D__ : Add a Maxon Noise shader to the given slot(option).
  - __AddNoise__ : Add a Octane Noise shader to the given slot(option).
  - __AddTriplanar__ : Add a Triplanar shader to the given slot(option).
  - __AddDisplacement__ : Add a Displacement shader to the given slot(option).
  - __AddBlackbodyEmission__ : Add a Blackbody Emission shader to the given slot(option).
  - __AddTextureEmission__ : Add a Texture Emission shader to the given slot(option).
  - __AddTextureTree__ : Add a Texture + Color Correction + Gradient shader tree to the given slot(option).

### MaterialHelper Class/method highlighted:

  - __CreateBasicMaterial__ : Create an Octane Basic(classic) material of given type and name.
  - __CreateComposite__ : Create an Octane Composite material of given type and name.
  - __CreateStandardMaterial__ : Create an Octane Standard Surface material of given type and name.
  - __InsertMaterial__ : Insert the material to the document.
  - __Refresh__ : Refresh thumbnail.
  - __SetActive__ : Set the material active in the document.
  - __SetupTextures__ : Setup a pbr material with given or selected texture.
  - __UniTransform__ : Add a Transform node to all the Image nodes.

### SceneHelper Class/method highlighted:

  - __add_hdr_dome__ : Add a texture (hdr) dome light to the scene.
  - __add_rgb_dome__ : Add a rgb dome light to the scene.
  - __add_dome_rig__ : Add a HDR and visible dome light folder.
  - __add_light__ : Add an Octane light to the secne.
  - __add_light_texture__ : Add textures to given Octane light tag.
  - __add_ies__ : Add an Octane ies light to the secne.
  - __add_gobo__ : Add an Octane gobo light to the secne.
  - __add_sun__ : Add an Octane sun light to the secne.
  - __add_light_modifier__ : Add some modify tagsto given Octane light tag.
  - __add_object_tag__ : Add an object tag to the given object.
  - __add_objects_tag__ : Add object tags to the given objects(enumerate id).
  - __add_custom_aov_tag__ : Add an object tag of given custom aov id to the given object.
  - __add_camera_tag__ :Add an camera tag to the given camera.
  - __add_scatter__ : Add a scatter object of given generator_node and scatter_nodes.
  - __add_vdb__ : Add a vdb loader object with the given path to the scene.

# Eaxmple
1. __VideoPostHelper__ : Get the renderer id and version, set the render settings.
2. __AOVHelper__ : Add/Remove/Set/Get aovs, and print aov info.
3. __MaterialHelper__ : Create an Octane material with nodes and print shader info.
4. __SceneHelper__ : Create lights/tags/objects.



