# Description ID Constants

RS_NODESPACE = "com.redshift3d.redshift4c4d.class.nodespace"
AR_NODESPACE = "com.autodesk.arnold.nodespace" 
VR_NODESPACE = "com.chaos.class.vray_node_renderer_nodespace"
CE_NODESPACE = "com.centileo.class.nodespace"

NODESPACE_INDEX = [RS_NODESPACE, AR_NODESPACE, VR_NODESPACE]

KEYWORD_LIST = ["$type", "$id", "$query", "$qmode"]

### Output Node ###
PORT_OUTPUT_SHADER = [
    "com.redshift3d.redshift4c4d.node.output.surface",
    "shader",
    "",
    ""
]

PORT_OUTPUT_DISPLACEMENT = [
    "com.redshift3d.redshift4c4d.node.output.displacement",
    "displacement",
    "",
    ""
]

OUTPUT_PORTS = [
    PORT_OUTPUT_SHADER,
    PORT_OUTPUT_DISPLACEMENT
]

OUTPUT_DESCRIPTION = [
    "com.redshift3d.redshift4c4d.node.output",
    "com.autodesk.arnold.material",
    ["com.chaos.vray_node.mtlsinglebrdf", "com.chaos.vray_node.mtl2sided"],
    "com.centileo.node.output",
    OUTPUT_PORTS
]
### Material Node ###
PORT_MATERIAL_ALBEDO = [
    "com.redshift3d.redshift4c4d.nodes.core.standardmaterial.base_color",
    "base_color",
    "",
    ""
]

PORT_MATERIAL_ROUGHNESS = [
    "com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refl_roughness",
    "specular_roughness",
    "",
    ""
]

MATERIAL_PORTS = [
    PORT_MATERIAL_ALBEDO,
    PORT_MATERIAL_ROUGHNESS,
]


MATERIAL_DESCRIPTION = [
    ["com.redshift3d.redshift4c4d.nodes.core.standardmaterial", "com.redshift3d.redshift4c4d.nodes.core.material"],
    "com.autodesk.arnold.shader.standard_surface",
    "com.chaos.vray_node.brdfvraymtl",
    "com.centileo.node.material",
    MATERIAL_PORTS
]

### Texture Node ###
PORT_IMAGE_INPUT = [
    "Image/Filename/Path",
    "filename",
    "",
    ""
]

PORT_IMAGE_SPACE = [
    "Image/Filename/Color Space",
    "color_space",
    "",
    ""
]

IAMGE_PORTS = [
    PORT_IMAGE_INPUT,
    PORT_IMAGE_SPACE
]

TEXTURE_DESCRIPTION = [
    "com.redshift3d.redshift4c4d.nodes.core.texturesampler",
    "com.autodesk.arnold.shader.image",
    "com.chaos.vray_node.texbitmap",
    "com.centileo.node.bitmap",
    IAMGE_PORTS
]

### Color Correction Node ###

PORT_CC_INPUT = [
    "com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection.input",
    "input",
    ""
]

PORT_CC_GAMMA = [
    "com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection.gamma",
    "gamma",
    ""
]

PORT_CC_CONTRAST = [
    "com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection.contrast",
    "contrast",
    ""
]

PORT_CC_HUE = [
    "com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection.hue",
    "hue_shift",
    ""
]

PORT_CC_SATURATION = [
    "com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection.saturation",
    "saturation",
    ""
]

PORT_CC_BRIGHTNESS = [
    "com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection.level",
    "exposure",
    ""
]

CC_PORTS = [
    PORT_CC_INPUT,
    PORT_CC_GAMMA,
    PORT_CC_CONTRAST,
    PORT_CC_HUE,
    PORT_CC_SATURATION, 
    PORT_CC_BRIGHTNESS
]

COLOR_CORRECT_DESCRIPTION = [
    "com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection",
    "com.autodesk.arnold.shader.color_correct",
    "com.chaos.vray_node.colorcorrection",
    "com.centileo.node.colorcorrect",
    CC_PORTS
]

# todo
### Maxon Noise Node ###
MAXON_NOISE_TYPE = []

MAXON_NOISE_PORTS = [
    MAXON_NOISE_TYPE
]

MAXON_NOISE_DESCRIPTION = [
    "com.redshift3d.redshift4c4d.nodes.core.maxonnoise",
    "com.autodesk.arnold.shader.c4d_noise",
    "com.chaos.vray_node.maxon_noise",
    "",
    MAXON_NOISE_PORTS
]






MIX_DESCRIPTION = [
    "com.redshift3d.redshift4c4d.nodes.core.rsmathmix",
    "com.autodesk.arnold.shader.mix_rgba",
    "com.chaos.vray_node.texmix",
    ""
]


DESCRIPTION_MAPS = [
    OUTPUT_DESCRIPTION,
    MATERIAL_DESCRIPTION,
    TEXTURE_DESCRIPTION,
    COLOR_CORRECT_DESCRIPTION,
    MAXON_NOISE_DESCRIPTION,
    MIX_DESCRIPTION
]


# todo : add more descriptions

COLOR_DESCRIPTION = ["Color", "Color"]

ADD_DESCRIPTION = ["Add", "#~.add"]

SUBTRACT_DESCRIPTION = ["Subtract", "#~.subtract"]

MULTIPLY_DESCRIPTION = ["Multiply", "#~.multiply"]

DIVIDE_DESCRIPTION = ["Divide", "#~.divide"]

TRIPLANAR_DESCRIPTION = ["Triplanar", "#~.triplanar"]

BUMP_DESCRIPTION = ["Bump", "#~.bump"]

DISPLACEMENT_DESCRIPTION = ["Displacement", "#~.displacement"]

NORMAL_MAP_DESCRIPTION = ["Normal Map", "#~.normal_map"]

FRESNEL_DESCRIPTION = ["Fresnel", "#~.fresnel"]

RAMP_DESCRIPTION = ["Ramp", "#~.ramp"]
