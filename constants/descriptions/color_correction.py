

PORT_CC_INPUT = [
    "com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection.input",
    "in",
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