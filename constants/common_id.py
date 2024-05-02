import c4d
import typing
from typing import Union, Optional
import maxon

###  ==========  Ids  ==========  ###

# VideoPost
ID_OCTANE: int = 1029525 # Octane 
ID_REDSHIFT: int = 1036219 # Redshift
ID_ARNOLD: int = 1029988 # Arnold
ID_VRAY: int = 1053272
ID_CORONA: int = 1030480
ID_LOOKS: int = 1054755

# Buildin ID
ID_PREFERENCES_NODE = 465001632 # Prefs ID
CID_ASSET_BROWSER = 1054225 # Asset Browser
ID_MATERIAL_MANAGER: int = 12159 # Material Manager
CID_NODE_EDITOR: int = 465002211 # Node Editor

# redshift
RS_NODESPACE: str = "com.redshift3d.redshift4c4d.class.nodespace"
RS_SHADER_PREFIX: str = "com.redshift3d.redshift4c4d.nodes.core."

# arnold
AR_NODESPACE: str = "com.autodesk.arnold.nodespace" 
AR_SHADER_PREFIX: str = "com.autodesk.arnold.shader."

STANDARD_NODESPACE: str = "net.maxon.nodespace.standard"
VR_NODESPACE: str = "com.chaos.class.vray_node_renderer_nodespace"

# data types
DATATYPE_INT: maxon.Id = maxon.Id("int64")
DATATYPE_COL3: maxon.Id = maxon.Id("net.maxon.parametrictype.col<3,float64>")
DATATYPE_FLOAT64: maxon.Id = maxon.Id("float64")

# align
ALIGNALLNODES: int = 465002363
ALIGNNODES: int = 465002311