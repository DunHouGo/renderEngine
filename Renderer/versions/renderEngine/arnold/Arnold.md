# Arnold
This is a custom api for Arnold Render in Cinema 4D, which is also wiil contains in 'boghma' library. This is a free lib for our boghma plugins with c4d.

To use this library, you need to download the source or download Boghma Plugin Manager and install the latest version. Downlad from: https://www.boghma.com (not done yet) and install any plugin, the boghma lib will auto installed.

# Limit
- AddChild() and AddTextureTree() will return a not auto-layout node network now.
- GetID() is broken, wait Maxon fix it, GetParamDataTypeID() can not get vector id

# Class Presentation

## Arnold_id
#### This Class contains unique ids for Arnold object, and name map of aovs.

## Arnold_helper
#### This Class contains the functions for the library. And it has some children Classes.
- __Functions(functions)__
- __VideoPostHelper__
- __AOVHelper__
- __ArnoldShaderLinkCustomData(same as offical)__
- __ArnoldVColorCustomData(same as offical)__
- __MaterialHelper__
- __ARMaterialTransaction__
- __SceneHelper__

### Arnold Class/method highlighted:

#### This Class contains methods for the library. It has the following methods:
  - __GetPreference__ : Get the Arnold preference.
  - __IsNodeBased__ : Check if in Arnold and use node material mode.
  - __SetMaterialPreview__ : Set material preview mode, default to 'when render is idle'.
  - __GetRenderEngine__ : Return current render engine ID.
  - __GetVersion__ : Get the version number of Arnold.
  - __GetCoreVersion__ : Get the core version number of Arnold.
  - __OpenIPR__ : Open Render View.
  - __OpenNodeEditor__ : Open Node Editor for given material.
  - __AovManager__ : Open aov Manager of given driver of driver type.
  - __TextureManager__ : Open Arnold Texture Manager.
  - __LightManager__ : Check if in Arnold and use node material mode.


### AOVHelper Class/method highlighted:
  - __get_driver__ : Get the top arnold driver of given driver type.
  - __get_dispaly_driver__ : Get dispaly arnold drivers in the scene.
  - __set_driver_path__ : Set driver render path.
  - __create_aov_driver__ : Create a Driver of Arnold aov.
  - __create_aov_shader__ : Create a shader of Arnold aov.
  - __add_aov__ : Add the Arnold aov shader to Arnold Driver.
  - __get_aovs__ : Get all the aovs of given driver in a list.
  - __get_aov__ : Get the aov of given name of the driver.
  - __print_aov__ : Print main info of existed aov in python console.
  - __set_driver_mode__ : Set the driver render mode.
  - __remove_last_aov__ : Remove the last aov shader.
  - __remove_all_aov__ : Remove all the aov shaders.
  - __remove_aov_type__ : Remove aovs of the given aov type.


### MaterialHelper Class/method highlighted:

  - __Create__ : Create an Arnold material(output) of given name.
  - __CreateStandardSurface__ : Create an Arnold Standard Surface material of given name.
  - __InsertMaterial__ : Insert the material to the document.
  - __Refresh__ : Refresh thumbnail.
  - __SetActive__ : Set the material active in the document.
  - __SetupTextures__ : Setup a pbr material with given or selected texture.
  - __FastPreview__ : Set material preview to 64x64 or default.
 
  - __AddShader__ : Add a shader to the material of the given id.

  - __AddColorJitter__ : Adds a new color jitter shader to the graph.
  - __AddAddShuffle__ : Adds a new shuffle shader to the graph.
  - __AddColorConvert__ : Adds a new Color Convert shader to the graph.
  - __AddColorCorrect__ : Adds a new Color Correct shader to the graph.


  - __AddMathAdd__ : Adds a new Math Add shader to the graph.
  - __AddMathSub__ : Adds a new Math Sub shader to the graph.
  - __AddMathMul__ : Adds a new Math Mul shader to the graph.
  - __AddMathDiv__ : Adds a new Math Div shader to the graph.
  - __AddMathNegate__ : Adds a new Math Negate shader to the graph.
  - __AddMathRange__ : Adds a new Math Range shader to the graph.
  - __AddMathNormalize__ : Adds a new Math Normalize shader to the graph.
  - __AddMathvalue__ : Adds a new Math value shader to the graph.
  - __AddMathCompare__ : Adds a new Math Compare shader to the graph.
  - __AddMathAbs__ : Adds a new Math Abs shader to the graph.
  - __AddMathMin__ : Adds a new Math Min shader to the graph.
  - __AddMathMax__ : Adds a new Math Max shader to the graph.

  - __AddNormal__ : Adds a new normal shader to the graph.
  - __AddBump2d__ : Adds a new Bump2d shader to the graph.
  - __AddBump3d__ : Adds a new Bump3d shader to the graph.
  - __AddDisplacement__ : Adds a new displacement shader to the graph.

  - __AddLayerRgba__ : Adds a new LayerRgba shader to the graph.
  - __AddLayerFloat__ : Adds a new LayerFloat shader to the graph.  
  - __AddRoundCorner__ : Adds a new Round Corner shader to the graph.

  - __AddFresnel__ : Adds a new Fresnel shader to the graph.
  - __AddAO__ : Adds a new AO shader to the graph.
  - __AddCurvature__ : Adds a new Curvature shader to the graph.
  - __AddFlakes__ : Adds a new Flakes shader to the graph.
  - __AddPointAttribute__ : Adds a new Point Attribute shader to the graph.
  - __AddVertexAttribute__ : Adds a new Vertex Attribute shader to the graph.

  - __AddRampRGB__ : Adds a new RampRGB shader to the graph.
  - __AddRampFloat__ : Adds a new RampFloat shader to the graph.
  - __AddTriPlanar__ : Adds a new TriPlanar shader to the graph.
  - __AddMaxonNoise__ : Adds a new maxonnoise shader to the graph.
  - __AddTexture__ : Adds a new texture shader to the graph.


  - __AddtoOutput__ : Add a Displacement shader to the given slot(option).
  - __AddtoDisplacement__ : Add a Displacement shader to the given slot(option).

  - __AddTextureTree__ : Adds a texture tree (tex + color correction + ramp) to the graph.
  - __AddDisplacementTree__ : Adds a displacement tree (tex + displacement) to the graph.
  - __AddBumpTree__ :Adds a bump tree (tex + bump) to the graph.
  - __AddNoramlTree__ :Adds a normal tree (tex + normal) to the graph.

### SceneHelper Class/method highlighted:

  - __set_link__ : Set links to given hdr or light.
  - __add_hdr_dome__ : Add a texture (hdr) dome light to the scene.
  - __add_rgb_dome__ : Add a rgb dome light to the scene.
  - __add_dome_rig__ : Add a HDR and visible dome light folder.
  - __add_light__ : Add an Arnold light to the secne.
  - __add_light_texture__ : Add textures to given Arnold light tag.
  - __add_ies__ : Add an Arnold ies light to the secne.
  - __add_gobo__ : Add an Arnold gobo light to the secne.
  - __add_sun__ : Add an Arnold sun light to the secne.
  - __add_light_modifier__ : Add some modify tagsto given Arnold light tag.

  - __add_object_tag__ : Add an object tag to the given object.
  - __add_mask_tag__ : Add object mask tags to the given object(with name).
  - __add_camera_tag__ : Add camera tag to the given camera.

  - __add_scatter__ : Add a scatter object of given generator_node and scatter_nodes[selection optional].
  - __add_vdb__ : Add an arnold volume object.
  - __add_proxy__ : Add an arnold proxy object.
  - __auto_proxy__ : Export objects and replace with proxy (center axis).

# Eaxmple
1. __VideoPostHelper__ : Get the renderer id and version, set the render settings.
2. __AOVHelper__ : Add/Remove/Set/Get aovs, and print aov info.
3. __MaterialHelper__ : Create an Arnold material with nodes and pbr material setup.
4. __SceneHelper__ : Create lights/tags/objects.
5. __PrintID__ : Print some ID with helper class (R2023 above just copy 'id' form node editor is easy)



