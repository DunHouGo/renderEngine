import c4d


###  ==========  Redshift ID  ==========  ###
# Redshift ID
ID_REDSHIFT_VIDEO_POST = 1036219

REDSHIFT_AOV_TYPE_WORLD_POSITION  =  0
REDSHIFT_AOV_TYPE_DEPTH  =  1
REDSHIFT_AOV_TYPE_PUZZLE_MATTE  =  2
REDSHIFT_AOV_TYPE_MOTION_VECTORS = 3
REDSHIFT_AOV_TYPE_OBJECT_ID = 4
REDSHIFT_AOV_TYPE_DIFFUSE_LIGHTING = 5
REDSHIFT_AOV_TYPE_DIFFUSE_LIGHTING_RAW = 6
REDSHIFT_AOV_TYPE_DIFFUSE_FILTER  =  7
REDSHIFT_AOV_TYPE_SPECULAR_LIGHTING = 8
REDSHIFT_AOV_TYPE_SUB_SURFACE_SCATTER = 9
REDSHIFT_AOV_TYPE_SUB_SURFACE_SCATTER_RAW = 10
REDSHIFT_AOV_TYPE_REFLECTIONS = 11
REDSHIFT_AOV_TYPE_REFLECTIONS_RAW = 12
REDSHIFT_AOV_TYPE_REFLECTIONS_FILTER = 13
REDSHIFT_AOV_TYPE_REFRACTIONS = 14
REDSHIFT_AOV_TYPE_REFRACTIONS_RAW = 15
REDSHIFT_AOV_TYPE_REFRACTIONS_FILTER = 16
REDSHIFT_AOV_TYPE_EMISSION = 17
REDSHIFT_AOV_TYPE_GLOBAL_ILLUMINATION = 18
REDSHIFT_AOV_TYPE_GLOBAL_ILLUMINATION_RAW = 19
REDSHIFT_AOV_TYPE_CAUSTICS = 20
REDSHIFT_AOV_TYPE_CAUSTICS_RAW = 21
REDSHIFT_AOV_TYPE_AMBIENT_OCCLUSION = 22
REDSHIFT_AOV_TYPE_SHADOWS = 23
REDSHIFT_AOV_TYPE_NORMALS = 24
REDSHIFT_AOV_TYPE_BUMP_NORMALS = 25
REDSHIFT_AOV_TYPE_MATTE = 26
REDSHIFT_AOV_TYPE_VOLUME_LIGHTING = 27
REDSHIFT_AOV_TYPE_VOLUME_FOG_TINT = 28
REDSHIFT_AOV_TYPE_VOLUME_FOG_EMISSION = 29
REDSHIFT_AOV_TYPE_TRANSLUCENCY_LIGHTING_RAW = 30
REDSHIFT_AOV_TYPE_TRANSLUCENCY_FILTER = 31
REDSHIFT_AOV_TYPE_TRANSLUCENCY_GI_RAW = 32
REDSHIFT_AOV_TYPE_TOTAL_DIFFUSE_LIGHTING_RAW = 33
REDSHIFT_AOV_TYPE_TOTAL_TRANSLUCENCY_LIGHTING_RAW = 34
REDSHIFT_AOV_TYPE_OBJECT_SPACE_POSITIONS = 35
REDSHIFT_AOV_TYPE_OBJECT_SPACE_BUMP_NORMALS = 36
REDSHIFT_AOV_TYPE_BACKGROUND = 37
REDSHIFT_AOV_TYPE_MAIN = 38
REDSHIFT_AOV_TYPE_CUSTOM = 39
REDSHIFT_AOV_TYPE_IDS_AND_COVERAGE = 40
REDSHIFT_AOV_TYPE_BEAUTY = 41
REDSHIFT_AOV_TYPE_CRYPTOMATTE = 42
REDSHIFT_AOV_TYPE_MAX = 43
REDSHIFT_AOV_TYPE_NONE = 65535

REDSHIFT_AOV_LIGHTGROUP_GLOBALAOV = 1024
REDSHIFT_AOV_LIGHTGROUP_ALL = 1025
REDSHIFT_AOV_LIGHTGROUP_NAMES = 1026

REDSHIFT_AOV_PUZZLE_MATTE_MODE_MATERIAL_ID = 0
REDSHIFT_AOV_PUZZLE_MATTE_MODE_OBJECT_ID = 1


REDSHIFT_AOVS = [
    REDSHIFT_AOV_TYPE_WORLD_POSITION,
    REDSHIFT_AOV_TYPE_DEPTH,
    REDSHIFT_AOV_TYPE_PUZZLE_MATTE,
    REDSHIFT_AOV_TYPE_MOTION_VECTORS,
    REDSHIFT_AOV_TYPE_OBJECT_ID,
    REDSHIFT_AOV_TYPE_DIFFUSE_LIGHTING,
    REDSHIFT_AOV_TYPE_DIFFUSE_LIGHTING_RAW,
    REDSHIFT_AOV_TYPE_DIFFUSE_FILTER,
    REDSHIFT_AOV_TYPE_SPECULAR_LIGHTING,
    REDSHIFT_AOV_TYPE_SUB_SURFACE_SCATTER,
    REDSHIFT_AOV_TYPE_SUB_SURFACE_SCATTER_RAW,
    REDSHIFT_AOV_TYPE_REFLECTIONS,
    REDSHIFT_AOV_TYPE_REFLECTIONS_RAW,
    REDSHIFT_AOV_TYPE_REFLECTIONS_FILTER,
    REDSHIFT_AOV_TYPE_REFRACTIONS,
    REDSHIFT_AOV_TYPE_REFRACTIONS_RAW,
    REDSHIFT_AOV_TYPE_REFRACTIONS_FILTER,
    REDSHIFT_AOV_TYPE_EMISSION,
    REDSHIFT_AOV_TYPE_GLOBAL_ILLUMINATION,
    REDSHIFT_AOV_TYPE_GLOBAL_ILLUMINATION_RAW,
    REDSHIFT_AOV_TYPE_CAUSTICS,
    REDSHIFT_AOV_TYPE_CAUSTICS_RAW,
    REDSHIFT_AOV_TYPE_AMBIENT_OCCLUSION,
    REDSHIFT_AOV_TYPE_SHADOWS,
    REDSHIFT_AOV_TYPE_NORMALS,
    REDSHIFT_AOV_TYPE_BUMP_NORMALS,
    REDSHIFT_AOV_TYPE_MATTE,
    REDSHIFT_AOV_TYPE_VOLUME_LIGHTING,
    REDSHIFT_AOV_TYPE_VOLUME_FOG_TINT,
    REDSHIFT_AOV_TYPE_VOLUME_FOG_EMISSION,
    REDSHIFT_AOV_TYPE_TRANSLUCENCY_LIGHTING_RAW,
    REDSHIFT_AOV_TYPE_TRANSLUCENCY_FILTER,
    REDSHIFT_AOV_TYPE_TRANSLUCENCY_GI_RAW,
    REDSHIFT_AOV_TYPE_TOTAL_DIFFUSE_LIGHTING_RAW,
    REDSHIFT_AOV_TYPE_TOTAL_TRANSLUCENCY_LIGHTING_RAW,
    REDSHIFT_AOV_TYPE_OBJECT_SPACE_POSITIONS,
    REDSHIFT_AOV_TYPE_OBJECT_SPACE_BUMP_NORMALS,
    REDSHIFT_AOV_TYPE_BACKGROUND,
    REDSHIFT_AOV_TYPE_MAIN,
    REDSHIFT_AOV_TYPE_CUSTOM,
    REDSHIFT_AOV_TYPE_IDS_AND_COVERAGE,
    REDSHIFT_AOV_TYPE_BEAUTY,
    REDSHIFT_AOV_TYPE_CRYPTOMATTE,
    REDSHIFT_AOV_TYPE_MAX,
    REDSHIFT_AOV_TYPE_NONE
]

REDSHIFT_AOVS_NAME = [
    'World Position',
    'Z',
    'Puzzle Matte',
    'Motion Vectors',
    'Object Id',
    'Diffuse Lighting',
    'Diffuse Lighting Raw',
    'Diffuse Filter',
    'Specular Lighting',
    'Sub Surface Scatter',
    'Sub Surface Scatter Raw',
    'Reflections',
    'Reflections Raw',
    'Reflections Filter',
    'Refractions',
    'Refractions Raw',
    'Refractions Filter',
    'Emission',
    'Global Illumination',
    'Global Illumination Raw',
    'Caustics',
    'Caustics Raw',
    'Ambient Occlusion',
    'Shadows',
    'Normals',
    'Bump Normals',
    'Matte',
    'Volume Lighting',
    'Volume Fog Tint',
    'Volume Fog Emission',
    'Translucency Lighting Raw',
    'Translucency Filter',
    'Translucency Gi Raw',
    'Total Diffuse Lighting Raw',
    'Total Translucency Lighting Raw',
    'Object Space Positions',
    'Object Space Bump Normals',
    'Background',
    'Main',
    'Custom',
    'Ids And Coverage',
    'Beauty',
    'Cryptomatte',
    'Max',
    'None']


ID_PREFERENCES_NODE = 465001632 # Prefs ID
ID_REDSHIFT = 1036219 # Redshift

ID_REDSHIFT_LIGHT = 1036751
ID_REDSHIFT_RSSKY = 1036754

ID_REDSHIFT_TAG = 1036222
ID_REDSHIFT_ENVIROMENT = 1036757
ID_REDSHIFT_VOLUME = 1038655
ID_REDSHIFT_BAKESET = 1040211

ID_REDSHIFT_PROXY = 1038649

REDSHIFT_PROXY_DISPLAY_MODE_OFF = 0
REDSHIFT_PROXY_DISPLAY_MODE_BOUNDING_BOX = 1
REDSHIFT_PROXY_DISPLAY_MODE_MESH = 2

REDSHIFT_PROXY_MATERIAL_MODE_INTERNAL = 0
REDSHIFT_PROXY_MATERIAL_MODE_SCENE_PLACEHOLDER = 1
REDSHIFT_PROXY_MATERIAL_MODE_SCENE_NAME = 2

REDSHIFT_CAMERA = 1057516