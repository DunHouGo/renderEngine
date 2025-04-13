

### Port descriptions

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