# Redshift
This is a custom api for Redshift Render in Cinema 4D, which is also wiil contains in 'boghma' library. This is a free lib for our boghma plugins with c4d.

To use this library, you need to download the source or download Boghma Plugin Manager and install the latest version. Downlad from: https://www.boghma.com (not done yet) and install any plugin, the boghma lib will auto installed.

# Limit
- AddChild() and AddTextureTree() will return a not auto-layout node network now.
- GetID() is broken, wait Maxon fix it, GetParamDataTypeID() can not get vector id

# Class Presentation

## Redshift_id
#### This Class contains unique ids for Redshift object, and name map of aovs.

## Redshift_helper
#### This Class contains the functions for the library. And it has some children Classes.
- __Functions(functions)__
- __VideoPostHelper__
- __RedshiftAOVData__
- __AOVHelper__
- __MaterialHelper__
- __RSMaterialTransaction__
- __SceneHelper__

### Redshift Class/method highlighted:
#### This Class contains methods for the library. It has the following methods:
  - __GetRedshiftPreference__ : Get the Redshift preference.
  - __RedshiftNodeBased__ : Check if in Redshift and use node material mode.
  - __SetMaterialPreview__ : Set material preview mode, default to 'when render is idle'.
  - __GetRenderEngine__ : Return current render engine ID.
  - __GetVersion__ : Get the version number of Redshift.
  - __OpenIPR__ : Open Render View.
  - __OpenNodeEditor__ : Open Node Editor for given material.
  - __AovManager__ : Open aov Manager.
  - __TextureManager__ : Open Redshift Texture Manager.
  - __RedshiftNodeBased__ : Check if in Redshift and use node material mode.


### AOVData:
    
#### Redshift AOV dataclass structure

- __aov_shader__: c4d.BaseShader
- __aov_enabled__: bool
- __aov_name__: str
- __aov_type__: c4d.BaseList2D
- __aov_muti_enabled__: bool
- __aov_bit_depth__: int
- __aov_dir_output__: bool
- __aov_dir_outpath__: str
- __aov_subdata__: any
- __light_group_data__: any


### AOVHelper Class/method highlighted:
  - __get_type_name__ : Get the name string of given aov type.
  - __get_name__ : Get the name of given aov.
  - __set_name__ : Set the name of given aov.
  - __get_all_aovs__ : Get all Redshift aovs in a list.
  - __get_aovs__ : Get all the aovs of given type in a list.
  - __get_aov__ : Get the aov of given type.
  - __read_aov__ : Get aov data in a list of AOVData Class.
  - __print_aov__ : Print main info of existed aov in python console.
  - __create_aov_shader__ : Create a shader of Redshift aov.
  - __set_aov__ : Set the Redshift aov (**call before add aovs**).
  - __add_aov__ : Add the Redshift aov shader to Redshift Render.
  - __remove_last_aov__ : Remove the last aov shader.
  - __update_aov__ : Update atribute of given aov.
  - __remove_all_aov__ : Remove all the aov shaders.
  - __remove_aov_type__ : Remove aovs of the given aov type.
  - __set_light_group__ : Set a light group to given aov.
  - __active_light_group__ : Active a light group to given aov.
  - __set_puzzle_matte__ : Add a white aov shader of given id.


### MaterialHelper Class/method highlighted:

  - __Create__ : Create an Redshift Basic(classic) material of given name.
  - __CreateStandardSurface__ : Create an Redshift Standard Surface material of given name.
  - __CreateRSMaterial__ : Creates a new Redshift Material with a NAME.
  - __ExposeUsefulPorts__ : Expose some useful port on material.
  - __InsertMaterial__ : Insert the material to the document.
  - __Refresh__ : Refresh thumbnail.
  - __SetActive__ : Set the material active in the document.
  - __SetupTextures__ : Setup a pbr material with given or selected texture.
  - __FastPreview__ : Set material preview to 64x64 or default.
 
  - __AddShader__ : Add a shader to the material of the given type and slot.

  - __AddStandardMaterial__ : Adds a new Standard Material shader to the graph.
  - __AddRSMaterial__ : Adds a new RSMaterial shader to the graph.
  - __AddMaterialBlender__ : Adds a new Material Blender shader to the graph.
  - __AddMaterialLayer__ : Adds a new Material Layer shader to the graph.
  - __AddIncandescent__ : Adds a new Incandescent Material shader to the graph.
  - __AddSprite__ : Adds a new Sprite Material shader to the graph.

  - __AddColorConstant__ : Adds a new Color Constant shader to the graph.
  - __AddColorSplitter__ : Adds a new Color Splitter shader to the graph.
  - __AddColorComposite__ : Adds a new Color Composite shader to the graph.
  - __AddColorLayer__ : Adds a new Color Layer shader to the graph.
  - __AddColorChangeRange__ : Adds a new Color Change Range shader to the graph.
  - __AddColorCorrect__ : Adds a new color correct shader to the graph.

  - __AddMathMix__ : Adds a new Math Mix shader to the graph.
  - __AddVectorMix__ : Adds a new Vector Mix shader to the graph.
  - __AddColorMix__ : Adds a new Color Mix shader to the graph.
  - __AddMathAdd__ : Adds a new Math Add shader to the graph.
  - __AddVectorAdd__ : Adds a new Vector Add shader to the graph.
  - __AddMathSub__ : Adds a new Math Sub shader to the graph.
  - __AddVectorSub__ : Adds a new Vector Sub shader to the graph.
  - __AddColorSub__ : Adds a new Color Sub shader to the graph.
  - __AddMathMul__ : Adds a new Math Mul shader to the graph.
  - __AddVectorMul__ : Adds a new Vector Mul shader to the graph.
  - __AddMathDiv__ : Adds a new Math Div shader to the graph.
  - __AddVectorDiv__ : Adds a new Vector Div shader to the graph.


  - __AddBump__ : Adds a new Bump shader to the graph.
  - __AddBumpBlender__ : Adds a new bump blender shader to the graph.
  - __AddDisplacement__ : Adds a new displacement shader to the graph.
  - __AddDisplacementBlender__ : Adds a new displacement blender shader to the graph.
  - __AddRoundCorner__ : Adds a new Round Corners shader to the graph.

  - __AddFresnel__ : Adds a new Fresnel shader to the graph.
  - __AddAO__ : Adds a new AO shader to the graph.
  - __AddCurvature__ : Adds a new Curvature shader to the graph.
  - __AddFlakes__ : Adds a new Flakes shader to the graph.
  - __AddPointAttribute__ : Adds a new Point Attribute shader to the graph.
  - __AddVertexAttribute__ : Adds a new Vertex Attribute shader to the graph.

  - __AddRamp__ : Adds a new ramp shader to the graph.
  - __AddScalarRamp__ : Adds a new scalar ramp shader to the graph.
  - __AddTriPlanar__ : Adds a new TriPlanar shader to the graph.
  - __AddMaxonNoise__ : Adds a new maxonnoise shader to the graph.
  - __AddTexture__ : Adds a new texture shader to the graph.


  - __AddtoOutput__ : Add a Displacement shader to the given slot(option).
  - __AddtoDisplacement__ : Add a Displacement shader to the given slot(option).

  - __AddTextureTree__ : Adds a texture tree (tex + color correction + ramp) to the graph.
  - __AddDisplacementTree__ : Adds a displacement tree (tex + displacement) to the graph.
  - __AddBumpTree__ :Adds a bump tree (tex + bump) to the graph.

### SceneHelper Class/method highlighted:

  - __add_hdr_dome__ : Add a texture (hdr) dome light to the scene.
  - __add_rgb_dome__ : Add a rgb dome light to the scene.
  - __add_dome_rig__ : Add a HDR and visible dome light folder.
  - __add_light__ : Add an Redshift light to the secne.
  - __add_light_texture__ : Add textures to given Redshift light tag.
  - __add_ies__ : Add an Redshift ies light to the secne.
  - __add_gobo__ : Add an Redshift gobo light to the secne.
  - __add_sun_rig__ : Add an Redshift sun&sky light to the secne.
  - __add_light_modifier__ : Add some modify tagsto given Redshift light tag.

  - __add_object_tag__ : Add an object tag to the given object.
  - __add_object_id__ : Add object tags to the given object(with id).

  - __add_scatter__ : Add a scatter object of given generator_node and scatter_nodes[vertex optional].
  - __add_env__ : Add an RS enviroment object.
  - __add_vdb__ : Add an RS volume object.
  - __add_proxy__ : Add an RS proxy object.
  - __auto_proxy__ : Export objects and replace with proxy (center axis).
  - __add_bakeset__ : Add given objects to a new bakeset object.

# Eaxmple
1. __VideoPostHelper__ : Get the renderer id and version, set the render settings.
2. __AOVHelper__ : Add/Remove/Set/Get aovs, and print aov info.
3. __MaterialHelper__ : Create an Redshift material with nodes and pbr material setup.
4. __SceneHelper__ : Create lights/tags/objects.
5. __PrintID__ : Print some ID with helper class (R2023 above just copy 'id' form node editor is easy)



