
import c4d

ID_PREFERENCES_NODE = 465001632 # Prefs ID
ID_VRAY = 1053272

VR_NODESPACE: str = "com.chaos.class.vray_node_renderer_nodespace"

ID_CHAOSGROUP=1053267 ## Reserved but not yet used.
ID_CHAOSGROUP_VRAY=1053268 ## Reserved but not yet used.
ID_VRAY_HELP_PLUGIN_DELEGATE=1055827 ## Used for registering the global plugin help delegate.

ID_VRAY_INSTANCE_OBJECT=1053298 ## ID used as basic ID of V-Ray related custom objects
ID_VRAY_INSTANCE_LIGHT=1053299 ## ID used as basic ID of V-Ray light objects
ID_VRAY_INSTANCE_MATERIAL=1053300 ## ID used as basic ID of V-Ray materials
ID_VRAY_INSTANCE_RENDER_ELEMENT=1054052 ## ID used as a basic ID of V-Ray render elements
ID_VRAY_INSTANCE_SHADER=1054352 ## ID used as a basic ID of V-Ray shaders (textures)

ID_VRAY_PLUGIN=1053271 ## Main value for our plugin to be used as a base.
ID_VRAY_VIDEO_POST=1053272 ## ID for our VideoPost derivative plugin used for production rendering in Cinema 4D.
ID_VRAY_PREFERENCES=1053273 ## ID for our Preferences derivative plugin to store and use global preferences.
ID_VRAY_COMMAND_SHOW_VFB=1054856 ## ID for the Show VFB command
ID_VRAY_COMMAND_INTERACTIVE_RENDER=1053274 ## ID for the Interactive Render command
ID_VRAY_COMMAND_PRODUCTION_RENDER=1055123 ## ID for the Production Render command
ID_VRAY_VFB_CORE_MESSAGE=1054857 ## ID for the VFB core messages (command from VRayVFBDialog).
ID_VRAY_SETTINGS_MATERIAL_PREVIEW=1053389 ## ID for the material preview common description.
ID_VRAY_COMMAND_RENDER_ELEMENTS=1054051 ## ID for the Render Elements command
ID_VRAY_SETTINGS_LIGHT_LINKER=1055646 ## ID for the settings light linker common description.
ID_VRAY_COMMAND_CLOUD_SUBMIT=1056144 ## ID for exporting a scene for cloud rendering

ID_VRAY_COMMAND_MATERIAL_CONVERT_DIALOG=1059205 ## ID for opening the material conversion dialog.

ID_VRAY_PLUGIN_HOOK=1061708 ## ID for the V-Ray Plugin Hook.
ID_VRAY_PLUGIN_DOCUMENT_INFO=1061710 ## ID for the V-Ray document info.

## Help menu
ID_VRAY_COMMAND_ABOUT_DIALOG=1056085 ## ID for opening the About V-Ray dialog
ID_VRAY_COMMAND_ONLINE_DOCUMENTATION=1055823 ## ID for our on-line documentation command implementation from the menu
ID_VRAY_COMMAND_ONLINE_HELP_CENTER=1056084 ## ID for opening the on-line page for writing a support ticket
ID_VRAY_COMMAND_CHECK_FOR_UPDATE=1056122 ## ID for direct check online for an available update
ID_VRAY_COMMAND_EULA_DIALOG=1060397 ## ID for opening the V-Ray EULA dialog

ID_VRAY_MESSAGE_PLUGIN=1055901 ## ID for the message handling plugin used in V-Ray for global message communication.
ID_VRAY_CORE_MESSAGE=1055902 ## ID for a core message to be handled by the message plugin.

ID_VRAY_CUSTOMGUI_STRING_PRESETS=1056038 ## ID for the CUSTOMGUI implementation of a string edit with presets pop-up.

ID_VRAY_HOOK_LEGACY_SCENE_CONVERSION=1055343 ## ID for the legacy scene conversion hook
ID_VRAY_COMMAND_LEGACY_SCENE_CONVERSION=1056295 ## ID for on demand legacy scene conversion
ID_LEGACY_VRAYBRIDGE=1019782 ## ID of the legacy V-Ray VideoPost plugin

ID_VRAY_VFB_HOOK=1055633 ## ID for hook handling VFB parameters and additional operations for saving and loading documents.

ID_INTERACTIVE_HOOK=1058583 ## ID for the scene hook plugin
ID_INTERACTIVE_MESSAGE_PLUGIN=1058582 ## ID for the message plugin that will handle and make updates to Vantage and Viewport Interactive.
ID_INTERACTIVE_MESSAGE=1056046 ## ID for a message to be handled by the interactive message plugin.

## Vantage
ID_VANTAGE_COMMAND_LIVE_LINK=1058594 ## ID for directly starting the Vantage live link render
ID_VANTAGE_COMMAND_ANIMATION=1061986 ## ID for starting an animation export for Vantage render
ID_VANTAGE_COMMAND_SETTINGS=1061987 ## ID for opening the Vantage settings dialog

## Viewport Interactive Renderer
ID_VIEWPORT_INTERACTIVE_COMMAND=1060305 ## ID for the command used to start viewport interactive rendering.
ID_VIEWPORT_INTERACTIVE_RESOLUTION_COMMAND=1061066 ## ID for the command used to change the resolution multiplier in viewport interactive rendering.


## Lights
ID_VRAY_LIGHT_AMBIENT=1053275 ## ID for LightAmbient object
ID_VRAY_LIGHT_DIRECT=1053276 ## ID for LightDirect object
ID_VRAY_LIGHT_DOME=1053277 ## ID for LightDome object
ID_VRAY_LIGHT_IES=1053278 ## ID for LightIES object
ID_VRAY_LIGHT_MESH=1059898 ## ID for LightMesh object
ID_VRAY_LIGHT_OMNI=1053279 ## ID for LightOmni object
ID_VRAY_LIGHT_RECTANGLE=1053280 ## ID for LightRectangle object
ID_VRAY_LIGHT_SPHERE=1053281 ## ID for LightSphere object
ID_VRAY_LIGHT_SPOT=1053282 ## ID for LightSpot object
ID_VRAY_LIGHT_SUN=1053287 ## ID for LightSun object
ID_VRAY_CREATE_LIGHT_SUN_COMMAND=1055140 ## ID for CreateLightSunCommand
ID_VRAY_CREATE_SUN_SKY_COMMAND=1055238 ## ID for CreateVRaySunSkyCommand
ID_VRAY_CREATE_LIGHT_IES_COMMAND=1055553 ## ID for CreateVRayLigthIESCommand

## Tags
ID_VRAY_PHYSICAL_CAMERA=1053283 ## ID for PhysicalCamera tag
ID_VRAY_DOME_CAMERA=1053284 ## ID for DomeCamera tag
ID_VRAY_OBJECT_PROPERTIES=1055070 ## ID for VRayObjectProperties tag
ID_VRAY_TAG_GEOMETRY=1055219 ## ID for Geometry tag
ID_VRAY_TAG_RENDERABLE_SPLINE=1058901 ## ID for Spline tag
ID_VRAY_COMMAND_MAKE_SHADOW_CATCHER=1059839 ## ID for the command for creating a shadow catcher tag

## Camera create menu commands
ID_VRAY_MENU_PHYSICAL_CAMERA=1054777 ## ID for the command for creating physical camera
ID_VRAY_MENU_DOME_CAMERA=1054778 ## ID for the command for creating dome camera

## Materials
ID_VRAY_MATERIAL_DISPLACEMENT_OPTIONS=1055342 ## ID for the material displacement options
ID_VRAY_MATERIAL_EXTRA_OPTIONS=1055647 ## ID for the material id options
ID_VRAY_MATERIAL_VRAYMTL=1053286 ## ID for the VRayMtl material
ID_VRAY_MATERIAL_ALSURFACE=1054171 ## ID for the AlSurface material
ID_VRAY_MATERIAL_BLEND=1055197 ## ID for the Blend material
ID_VRAY_MATERIAL_BUMP=1054172 ## ID for the Bump material
ID_VRAY_MATERIAL_OSL=1060098 ## ID for the OSL material
ID_VRAY_MATERIAL_CAR_PAINT_2=1054173 ## ID for the Car Paint 2 material
ID_VRAY_MATERIAL_FAST_SSS=1054174 ## ID for the Fast SSS2 material
ID_VRAY_MATERIAL_FLAKES=1054175 ## ID for the Flakes material (unused)
ID_VRAY_MATERIAL_HAIR_NEXT=1054176 ## ID for the Hair Next material
ID_VRAY_MATERIAL_HAIR_3=1054177 ## ID for the Hair 3 material (unused)
ID_VRAY_MATERIAL_LIGHT=1054294 ## ID for the Light material
ID_VRAY_MATERIAL_SCANNED=1056284 ## ID for Scanned Material (VRScan)
ID_VRAY_MATERIAL_SCANNED_LOADER_DATA=1060076 ## ID for Scanned Material loader
ID_VRAY_MATERIAL_STOCHASTIC_FLAKES=1054178 ## ID for the Stochastic Flakes material
ID_VRAY_MATERIAL_TOON=1054179 ## ID for the Toon material
ID_VRAY_MATERIAL_2SIDED=1055208 ## ID for the 2Sided material
ID_VRAY_MATERIAL_OVERRIDE=1059116 ## ID for the Override material
ID_VRAY_MATERIAL_SWITCH=1061339 ## ID for the Switch material
ID_VRAY_MATERIAL_VRMAT=1061834 ## ID for the VRmat material
ID_VRAY_MATERIAL_VRAY_SCENE_ASSET=1061761 ## ID for the VRay Scene Asset material.

ID_LAYER_TYPE_MATERIAL = [
    ID_VRAY_MATERIAL_VRAYMTL,
    ID_VRAY_MATERIAL_ALSURFACE,
    ID_VRAY_MATERIAL_BLEND,
    ID_VRAY_MATERIAL_BUMP,
    ID_VRAY_MATERIAL_OSL,
    ID_VRAY_MATERIAL_CAR_PAINT_2,
    ID_VRAY_MATERIAL_FAST_SSS,
    ID_VRAY_MATERIAL_FLAKES,
    ID_VRAY_MATERIAL_HAIR_NEXT,
    ID_VRAY_MATERIAL_LIGHT,
    ID_VRAY_MATERIAL_SCANNED,
    ID_VRAY_MATERIAL_STOCHASTIC_FLAKES,
    ID_VRAY_MATERIAL_TOON,
    ID_VRAY_MATERIAL_2SIDED,
    ID_VRAY_MATERIAL_OVERRIDE,
    ID_VRAY_MATERIAL_SWITCH,
    ID_VRAY_MATERIAL_VRMAT,
    ID_VRAY_MATERIAL_VRAY_SCENE_ASSET
]

## Material create menu commands
ID_VRAY_MENU_MATERIAL_VRAYMTL=1054644 ## ID for menu entry for creating VRayMtl material
ID_VRAY_MENU_MATERIAL_ALSURFACE=1054645 ## ID for menu entry for creating AlSurface material
ID_VRAY_MENU_MATERIAL_BLEND=1055198 ## ID for menu entry for creating Blend material
ID_VRAY_MENU_MATERIAL_BUMP=1054646 ## ID for menu entry for creating Bump material
ID_VRAY_MENU_MATERIAL_CAR_PAINT_2=1054647 ## ID for menu entry for creating Car Paint 2 material
ID_VRAY_MENU_MATERIAL_FAST_SSS=1054648 ## ID for menu entry for creating SSS2 material
ID_VRAY_MENU_MATERIAL_FLAKES=1054649 ## ID for menu entry for creating Flakes material
ID_VRAY_MENU_MATERIAL_HAIR_NEXT=1054650 ## ID for menu entry for creating Hair Next material
ID_VRAY_MENU_MATERIAL_HAIR_3=1054651 ## ID for menu entry for creating Hair 3 material
ID_VRAY_MENU_MATERIAL_LIGHT=1054643 ## ID for menu entry for creating Light material
ID_VRAY_MENU_MATERIAL_OSL=1060099 ## ID for menu entry for creating OSL material
ID_VRAY_MENU_MATERIAL_SCANNED=1056285 ## ID for menu entry for creating Scanned material
ID_VRAY_MENU_MATERIAL_STOCHASTIC_FLAKES=1054652 ## ID for menu entry for creating Stochastic Flakes material
ID_VRAY_MENU_MATERIAL_TOON=1054653 ## ID for menu entry for creating Toon material
ID_VRAY_MENU_MATERIAL_2SIDED=1055209 ## ID for menu entry for creating 2Sided material
ID_VRAY_MENU_MATERIAL_OVERRIDE=1059117 ## ID for menu entry for creating Override material
ID_VRAY_MENU_MATERIAL_SWITCH=1061340 ## ID for menu entry for creating Switch material
ID_VRAY_MENU_MATERIAL_VRMAT=1061835 ## ID for menu entry for creating VRmat material

## Node material presets
ID_VRAY_MENU_NODE_MATERIAL_VRAYMTL=1058751 ## ID for menu entry for creating a Node material with VRayMtl BRDF
ID_VRAY_MENU_NODE_MATERIAL_ALSURFACE=1058747 ## ID for menu entry for creating a Node material with AlSurface BRDF
ID_VRAY_MENU_NODE_MATERIAL_HAIR_NEXT=1058752 ## ID for menu entry for creating a Node material with Hair Next BRDF
ID_VRAY_MENU_NODE_MATERIAL_LIGHT=1058753 ## ID for menu entry for creating a Node material with Light BRDF
ID_VRAY_MENU_NODE_MATERIAL_FAST_SSS=1058754 ## ID for menu entry for creating a Node material with Fast SSS BRDF
ID_VRAY_MENU_NODE_MATERIAL_BUMP=1058755 ## ID for menu entry for creating a Node material with Bump BRDF
ID_VRAY_MENU_NODE_MATERIAL_BLEND=1058756 ## ID for menu entry for creating a Node material with Blend BRDF
ID_VRAY_MENU_NODE_MATERIAL_2SIDED=1058757 ## ID for menu entry for creating a Node material with 2Sided Material
ID_VRAY_MENU_NODE_MATERIAL_CAR_PAINT_2=1058758 ## ID for menu entry for creating a Node material with Car Paint 2 BRDF
ID_VRAY_MENU_NODE_MATERIAL_STOCHASTIC_FLAKES=1061625 ## ID for menu entry for creating a Node material with Stochastic Flakes BRDF
ID_VRAY_MENU_NODE_MATERIAL_TOON=1060580 ## ID for menu entry for creating a Node material with Toon BRDF
ID_VRAY_MENU_NODE_MATERIAL_OSL=1061097 ## ID for menu entry for creating a Node material with MtlOSL
ID_VRAY_MENU_NODE_MATERIAL_OVERRIDE=1059122 ## ID for menu entry for creating a Node material with Override material
ID_VRAY_MENU_NODE_MATERIAL_SWITCH=1061370 ## ID for menu entry for creating a Node material with Switch BRDF
ID_VRAY_MENU_NODE_MATERIAL_VRMAT=1061836 ## ID for menu entry for creating a Node material with VRmat BRDF

## Shaders (Textures)
ID_VRAY_TEXTURE_FRESNEL=1054124 ## ID for the Fresnel V-Ray texture.
ID_VRAY_TEXTURE_HAIR_SAMPLER=1059829 ## ID for TexHairSampler
ID_VRAY_TEXTURE_LAYERED=1055052 ## ID for the Layered V-Ray texture.
ID_VRAY_TEXTURE_SKY=1055174 ## ID for the Sky V-Ray texture.
ID_VRAY_TEXTURE_DIRT=1055400 ## ID for the Dirt V-Ray texture.
ID_VRAY_TEXTURE_DISTANCE=1055401 ## ID for Distance V-Ray texture
ID_VRAY_TEXTURE_FALLOFF=1055604 ## ID for Falloff V-Ray texture
ID_VRAY_TEXTURE_BAKE=1055613 ## ID for the Bake V-Ray texture.
ID_VRAY_TEXTURE_BITMAP=1055619 ## ID for Bitmap V-Ray texture
ID_VRAY_TEXTURE_TRIPLANAR=1055660 ## ID for Triplanar V-Ray texture
ID_VRAY_TEXTURE_CURVATURE=1055682 ## ID for Curvature V-Ray texture
ID_VRAY_TEXTURE_MULTI=1056176 ## ID for the MultiSubTex V-Ray texture
ID_VRAY_TEXTURE_RAMP=1056347 ## ID for the Ramp V-Ray texture
ID_VRAY_TEXTURE_COMBINE_COLOR=1057878 ## ID for the TexCombineColor V-Ray texture
ID_VRAY_TEXTURE_COMBINE_FLOAT=1057879 ## ID for the TexCombineFloat V-Ray texture
ID_VRAY_TEXTURE_MIX=1057880 ## ID for the TexMix V-Ray texture
ID_VRAY_TEXTURE_NORMAL_BUMP=1057881 ## ID for the TexNormalBump V-Ray texture
ID_VRAY_TEXTURE_NORMAL_MAP_FLIP=1057882 ## (removed) ID for the TexNormalMapFlip V-Ray texture
ID_VRAY_TEXTURE_BEZIER_CURVE_COLOR=1057883 ## ID for the TexBezierCurveColor V-Ray texture
ID_VRAY_TEXTURE_OCIO=1059904 ## ID for the TexOCIO V-Ray texture
ID_VRAY_TEXTURE_OUTPUT=1057884 ## ID for the TexOutput V-Ray texture
ID_VRAY_TEXTURE_FLOAT_TO_COLOR=1057885 ## ID for the TexFloatToColor V-Ray texture
ID_VRAY_TEXTURE_MAX_GAMMA=1057886 ## ID for the TexMaxGamma V-Ray texture
ID_VRAY_TEXTURE_COLOR_CORRECTION=1057887 ## ID for the ColorCorrection V-Ray texture
ID_VRAY_TEXTURE_ACOLOR_OPERATION=1057888 ## ID for the AColorOp V-Ray texture
ID_VRAY_TEXTURE_UVW=1057889 ## ID for the TexUVW V-Ray texture
ID_VRAY_TEXTURE_SAMPLER_INFO=1059922 ## ID for TexSamplerInfo V-Ray texture
ID_VRAY_TEXTURE_SOFTBOX=1059206 ## ID for the Softbox V-Ray texture
ID_VRAY_TEXTURE_EDGES=1059289 ## ID for the Edges V-Ray texture
ID_VRAY_TEXTURE_PARTICLES=1059321 ## ID for PhxShaderParticleTex.
ID_VRAY_TEXTURE_PARTICLE_SAMPLER=1059320 ## ID for TexParticleSampler
ID_VRAY_TEXTURE_USER_COLOR=1060191 ## ID for the TexUserColor
ID_VRAY_TEXTURE_USER_INTEGER=1060192 ## ID for the TexUserInteger
ID_VRAY_TEXTURE_USER_SCALAR=1060193 ## ID for the TexUserScalar
ID_VRAY_TEXTURE_CELLULAR=1060284 ## ID for the TexCellular
ID_VRAY_TEXTURE_NOISE_MAX=1060286 ## ID for the TexNoiseMax
ID_VRAY_TEXTURE_SMOKE=1060290 ## ID for the TexSmoke
ID_VRAY_TEXTURE_SPLAT=1060291 ## ID for the TexSplat
ID_VRAY_TEXTURE_STUCCO=1060299 ## ID for the TexStucco
ID_VRAY_TEXTURE_TILES=1060300 ## ID for the TexTiles
ID_VRAY_TEXTURE_OSL=1060100 ## ID for V-Ray TexOSL
ID_VRAY_TEXTURE_REMAP=1061626 ## ID for V-Ray TexRemap
ID_VRAY_TEXTURE_RGB_TO_HSV=1061627 ## ID for V-Ray TexRGBToHSV
ID_VRAY_TEXTURE_FLOAT_OPERATION=1061628 ## ID for V-Ray TexFloatOp
ID_VRAY_TEXTURE_VECTOR_PRODUCT=1061629 ## ID for V-Ray TexVectorProduct
ID_VRAY_TEXTURE_COMPOSE_COLOR=1061630 ## ID for V-Ray Float3AToColor
ID_VRAY_TEXTURE_COLOR_RANGE=1061631 ## ID for V-Ray TexSetRange
ID_VRAY_TEXTURE_BUMP_TO_GLOSSINESS=1061632 ## ID for V-Ray TexBump2Glossiness
ID_VRAY_TEXTURE_VRAY_SCENE_ASSET=1061765 ## ID for V-Ray Scene Asset texture
ID_VRAY_TEXTURE_CLAMP=1061953 ## ID for TexClamp

## Shaders (UVWGen)
ID_VRAY_UVWGEN_CHANNEL=1057890 ## ID for the UVWGenChannel V-Ray UVW generator
ID_VRAY_UVWGEN_RANDOMIZER=1058129 ## ID for the UVWGenRandomizer V-Ray UVW generator
ID_VRAY_UVWGEN_EXPLICIT=1061730 ## ID for the UVWGenExplicit V-Ray UVW generator
ID_VRAY_UVWGEN_PROJECTION=1061731 ## ID for the UVWGenProjection V-Ray UVW generator
ID_VRAY_UVWGEN_OBJECT=1061732 ## ID for the UVWGenObject V-Ray UVW generator
ID_VRAY_UVWGEN_TRANSFORM=1061733 ## ID for the UVWGenSelect V-Ray UVW generator
ID_VRAY_UVWGEN_PLACE2D=1061981 ## ID for the UVWGenMayaPlace2dTexture V-Ray UVW generator

## Render Elements
ID_VRAY_RENDER_ELEMENTS_SCENE_HOOK=1054363 ## ID for RenderElementsHook
ID_VRAY_RENDER_ELEMENT_BASE=1054148 ## ID for the common description
ID_VRAY_RENDER_ELEMENT_ROOT=1054149 ## ID for the render elements branch head
ID_VRAY_RENDER_ELEMENT_FOLDER=1054150 ## ID for RenderElementFolder
ID_VRAY_RENDER_ELEMENT_COLOR=1054151 ## ID for RenderElementColor
ID_VRAY_RENDER_ELEMENT_COLOR_NO_DENOISE=1054152 ## ID for RenderElementColorNoDenoise
ID_VRAY_RENDER_ELEMENT_NORMALS=1054153 ## ID for RenderElementNormals
ID_VRAY_RENDER_ELEMENT_GLOSSINESS=1054154 ## ID for RenderElementGlossiness
ID_VRAY_RENDER_ELEMENT_ZDEPTH=1054155 ## ID for RenderElementZDepth
ID_VRAY_RENDER_ELEMENT_BUMP_NORMALS=1054156 ## ID for RenderElementBumpNormals
ID_VRAY_RENDER_ELEMENT_NODE_ID=1054157 ## ID for RenderElementNodeID
ID_VRAY_RENDER_ELEMENT_VELOCITY=1054158 ## ID for RenderElementVelocity
ID_VRAY_RENDER_ELEMENT_RENDER_ID=1054159 ## ID for RenderElementRenderID
ID_VRAY_RENDER_ELEMENT_COVERAGE=1054160 ## ID for RenderElementCoverage
ID_VRAY_RENDER_ELEMENT_LIGHT_SELECT=1054224 ## ID for RenderElementLightSelect
ID_VRAY_RENDER_ELEMENT_CRYPTOMATTE=1054317 ## ID for RenderElementCryptomatte
ID_VRAY_RENDER_ELEMENT_LIGHT_MIX=1055656 ## ID for RenderElementLightMix
ID_VRAY_RENDER_ELEMENT_EXTRA_TEX=1055728 ## ID for RenderElementExtraTex
ID_VRAY_RENDER_ELEMENT_COAT=1055759 ## ID for RenderElementCoat
ID_VRAY_RENDER_ELEMENT_COAT_REFLECTION=1055760 ## ID for RenderElementCoatReflection
ID_VRAY_RENDER_ELEMENT_SHEEN=1055761 ## ID for RenderElementSheen
ID_VRAY_RENDER_ELEMENT_SHEEN_REFLECTION=1055762 ## ID for RenderElementSheenReflection
ID_VRAY_RENDER_ELEMENT_OBJECT_SELECT=1056127 ## ID for RenderElementObjectSelect
ID_VRAY_RENDER_ELEMENT_MATERIAL_SELECT=1060059 ## ID for RenderElementMaterialSelect
ID_VRAY_RENDER_ELEMENT_MULTI_MATTE=1056238 ## ID for RenderElementMultiMatte
ID_VRAY_RENDER_ELEMENT_MULTI_MATTE_ID=1056239 ## ID for RenderElementMultiMatteID
ID_VRAY_RENDER_ELEMENT_TOON=1060306 ## ID for RenderElementToon
ID_VRAY_RENDER_ELEMENT_SAMPLER_INFO=1061231 ## ID for RenderElementSamplerInfo
ID_VRAY_RENDER_ELEMENT_DR_BUCKET=1061337 ## ID for RenderElementDRBucket

ID_VRAY_PARTICLES=1059505 ## ID for VRayParticles object

ID_VRAY_PROXY=1054728 ## ID for VRayProxy
ID_VRAY_COMMAND_PROXY_DIALOG=1055046 ## ID for CommandProxyDialog
ID_VRAY_MESSAGE_PROXY_DIALOG_FROM_OBJECT=1055047 ## ID for a message sent to CommandProxyDialog to open the Proxy Dialog
ID_VRAY_PROXY_HELPER=1055048 ## ID for VRayProxyHelper
ID_VRAY_PROXY_ROOT=1055049 ## ID for VRayProxyRoot
ID_VRAY_PROXY_SCENE_HOOK=1055050 ## ID for VRayProxyHook
ID_VRAY_PROXY_SAVER_DATA=1055794 ## ID for VRayProxySaver
ID_VRAY_PROXY_LOADER_DATA=1055844 ## ID for VRayProxyLoader

ID_VRAY_SCENE_OBJECT=1058532 ## ID for VRayScene
ID_VRAY_SCENE_SAVER_DATA=1058655 ## ID for VRaySceneSaver
ID_VRAY_SCENE_LOADER_DATA=1058654 ## ID for VRaySceneLoader

ID_VRAY_SCENE_ASSET_OBJECT=1061766 ## ID for VRaySceneAsset
ID_VRAY_SCENE_ASSET_BASE_DESCRIPTION=1061880 ## ID for V-Ray Scene Asset Base description

ID_VRAY_ENVIRONMENT_FOG=1055729 ## ID for VRayEnvironmentFog
ID_VRAY_TOON=1060307 ## ID for VRayToon

ID_VRAY_VOLUME_GRID=1056014 ## ID for VRayVolumeGrid
ID_VRAY_CREATE_VOLUME_GRID_COMMAND=1056305 ## ID for the command for creating a VRayVolumeGrid object
ID_VRAY_VOLUME_GRID_PREVIEW_PROPERTIES = 1056275 ## ID for VRayVolumeGridPreviewProperties object
ID_VRAY_VOLUME_GRID_PREVIEW_SCENE_HOOK = 1056274 ## ID for VRayVolumeGridPreviewHook object
ID_VRAY_VOLUME_GRID_PREVIEW_HELPER = 1056501 ## ID for VRayVolumeGridHelper object

ID_VRAY_COSMOS_BASE_DESCRIPTION=1060055 ## ID for the base description included in V-Ray objects that may have been created by a cosmos asset.
ID_VRAY_COSMOS_ASSET=1057269 ## ID for VRayCosmosAsset.
ID_VRAY_COMMAND_OPEN_COSMOS_BROWSER=1057439 ## ID for OpenBrowserCommand.
ID_VRAY_COSMOS_HOOK=1058570 ## ID for the Cosmos hook plugin.
ID_VRAY_COMMAND_DOWNLOAD_COSMOS_ASSETS=1060164 ## ID for DownloadVRayCosmosAssetsCommand
ID_VRAY_COSMOS_ASSETS_CHECK_INTEGRITY_MESSAGE=1060188 ## ID used a message for all cosmos assets in the scene.

ID_VRAY_COMMAND_OPEN_CHAOS_COLLABORATION=1060643 ## ID for the command plugin that opens the collaboration dialog.

ID_VRAY_FUR=1057380 ## ID for VRayFur object
ID_VRAY_CLIPPER=1057445 ## ID for VRayClipper object
ID_VRAY_DECAL=1059061 ## ID for VRayDecal object
ID_VRAY_ENMESH=1059492 ## ID for VRayEnmesh object
ID_VRAY_CREATE_FUR_COMMAND=1059883 ## ID for CreateVRayFurCommand.
ID_VRAY_CREATE_ENMESH_COMMAND=1059899 ## ID for CreateVRayEnmeshCommand.
ID_VRAY_CREATE_CHAOS_SCATTER_COMMAND=1060907 ## ID for the CreateChaosScatterCommand.
ID_VRAY_ENVIRONMENT_OBJECT=1061436 ## ID for the VRayEnvironmentObject.

ID_VRAY_BAKE_OBJECT=1059602 ## ID for VRay Texture Baking object.

ID_VRAY_COMMAND_LIGHT_LISTER=1057923 ## ID for the Light Lister dialog
DIALOG_VRAY_COLOR_PICKER=1058235 ## ID for the color picker dialog
ID_VRAY_COMMAND_DISTRIBUTED_RENDER=1055635 ## ID for the DistributedRender dialog open command.
DIALOG_VRAY_DISTRIBUTED_RENDER_EDIT_ENTRY=1058236 ## ID for the EditEntry sub-dialog in the DistributedRender dialog.
ID_VRAY_COMMAND_TOOLBAR=1060033 ## ID for creating a V-Ray Toolbar.
ID_VRAY_COMMAND_OPEN_PROFILER_DIALOG=1060818 ## ID for the command for opening the V-Ray Profiler dialog.