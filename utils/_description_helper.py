from dataclasses import dataclass, field
from typing import Generator, Any, Dict, Set, Union, Iterator
import c4d
import maxon
import Renderer
from pprint import pp
from maxon import GraphDescription
from mxutils import CheckType
import time
import hashlib
import random
import string
from Renderer import Redshift, Arnold, Octane, Vray, CentiLeo, EasyTransaction, NodeGraghHelper
# from Renderer.constants.descrition_id import *

RS_NODESPACE = "com.redshift3d.redshift4c4d.class.nodespace"
AR_NODESPACE = "com.autodesk.arnold.nodespace" 
VR_NODESPACE = "com.chaos.class.vray_node_renderer_nodespace"
CE_NODESPACE = "com.centileo.class.nodespace"

NODESPACE_INDEX = [RS_NODESPACE, AR_NODESPACE, VR_NODESPACE]

KEYWORD_LIST = ["$type", "$id", "$query", "$qmode", "$commands"]

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

### Mix Node ###
PORT_MIX_1 = [
    "com.redshift3d.redshift4c4d.nodes.core.rsmathmix.input1",
    "input1",
    ""
]

PORT_MIX_2 = [
    "com.redshift3d.redshift4c4d.nodes.core.rsmathmix.input2",
    "input2",
    ""
]

PORT_MIX_MIX = [
    "com.redshift3d.redshift4c4d.nodes.core.rsmathmix.mixamount",
    "mix",
    ""
]

MIX_PORTS = [
    PORT_MIX_1,
    PORT_MIX_2,
    PORT_MIX_MIX
]

MIX_DESCRIPTION = [
    "com.redshift3d.redshift4c4d.nodes.core.rsmathmix",
    "com.autodesk.arnold.shader.mix_rgba",
    "com.chaos.vray_node.texmix",
    "",
    MIX_PORTS
]

DESCRIPTION_MAPS = [
    OUTPUT_DESCRIPTION,
    MATERIAL_DESCRIPTION,
    TEXTURE_DESCRIPTION,
    COLOR_CORRECT_DESCRIPTION,
    MAXON_NOISE_DESCRIPTION,
    MIX_DESCRIPTION
]


@dataclass
class PARTIAL_DESCRIPTION:

    nodeSpaceId: str|maxon.Id

    def __post_init__(self):
        self.index: int = NODESPACE_INDEX.index(self.nodeSpaceId)

    def CreateDescription(self, **kwargs) -> dict:
        """
        This function creates a partial description for a color correct node with a given parent.
        """
    
        if "id" not in kwargs:
            raise ValueError("Please provide an $id for the node.")
        desc = {}

        for key, value in kwargs.items():
            if key == "id":
                desc["$id"] = value
            if key == "type":
                desc["$type"] = value
            if key == "query":
                desc["$query"] = value
            if key == "qmode":
                desc["$qmode"] = value

            if key not in ["id", "type", "query", "qmode"]:
                desc[key] = value

        return {"id": desc["$id"], "desc": desc}

    def OutputDescription(self, hashId: str, **kwargs) -> dict:
        desc = {
            "$type" : OUTPUT_DESCRIPTION[self.index],
            "$id": hashId,
            }

        return {"id": hashId, "desc": desc}

    def MaterialDescription(self, hashId: str, child: str, color: maxon.Col3=None):
        """
        This function creates a partial description for a material node with a given name and color.
        """
        port_desc = ["Surface", "#~.shader"]
        desc = {
            "$type" : MATERIAL_DESCRIPTION[self.index],
            "$id": hashId,
            port_desc[self.index]: child
            }

        return {"id": hashId, "desc": desc}
    
        return {
            # An output node.
            "$type": "#~.material",
            # Its surface input port.
            "#<shader": {
                # A standard material node.
                "$type": "#~.standard_surface",

                "Base/Color": f"{color}"}
            }
    
    def ColorCorrectDescription(self, hashId: str, child: str) -> dict:
        """
        This function creates a partial description for a color correct node with a given parent.
        """
        desc = {
            "$type" : COLOR_CORRECT_DESCRIPTION[self.index],
            "$id": hashId,
            "Input": child
            }

        return {"id": hashId, "desc": desc}
    
    def ImageDescription(self, hashId: str, child: str, filename: str) -> dict:
        """
        This function creates a partial description for an image node with a given filename.
        """
        path_desc = ["#~.tex0", "#~.filename"]
        desc = {
            "$type" : TEXTURE_DESCRIPTION[self.index],
            "$id": hashId,
            path_desc[self.index] : f"{filename}"            
        }

        return {"id": hashId, "desc": desc}

def GetTrueNode(port: maxon.GraphNode) -> maxon.GraphNode:
    """
    Get the actually node host the given port.

    Args:
        port (maxon.GraphNode): the port to test

    Returns:
        maxon.GraphNode: the host true node.
    """
    return port.GetAncestor(maxon.NODE_KIND.NODE)

def GetName(node: maxon.GraphNode) -> str:
    """
    Retrieve the displayed name of a node.

    Args:
        node (maxon.GraphNode): the node

    Returns:
        Optional[str]: the name of the ndoe
    """
    nodeName = node.GetValue(maxon.NODE.BASE.NAME)

    # 此函数在2024.4.0中可以返回正确的值
    # 在2024.2.0中返回None
    if nodeName is None:
        nodeName = node.GetValue(maxon.EffectiveName)

    if nodeName is None:
        nodeName = str(node)

    return nodeName

def GetPortRealName(port: maxon.GraphNode) -> str:
    """
    Get the real name of the port.

    Args:
        port (maxon.GraphNode): the port

    Returns:
        str: The id string of this port
    """
    return str(port.GetId()).split(".")[-1]

def GetNodeDescription(node: maxon.GraphNode) -> str:
    """
    Returns the id for description.

    Example:
        "#com.redshift3d.redshift4c4d.nodes.core.standardmaterial"
    """
    return "#" + str(node.GetValue("net.maxon.node.attribute.assetid"))[1:].split(",")[0]

def GetPortDescription(port: maxon.GraphNode) -> str:
    return f"#<{GetPortRealName(port)}"

def GetUniqueHash() -> str:
    hash_object = hashlib.sha256(str(time.time()).encode('utf-8'))
    hex_dig = hash_object.hexdigest()
    return hex_dig[:8]

def RandomHash():
    random.seed(time.time())
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(22))

def GetConnectedPort(const_port: maxon.GraphNode, node: maxon.GraphNode) -> maxon.GraphNode:
    """
    Check if the port is connected.

    Args:
        port (maxon.GraphNode): The port to check.

    Returns:
        bool: True if the port is connected, False otherwise.
    """
    if node.GetKind() != maxon.NODE_KIND.NODE:
        return None
    
    for the_port in node.GetOutputs().GetChildren():
        #print("out:",the_port)
        if maxon.GraphModelHelper.IsConnected(const_port, the_port):
            return the_port
    for the_port in node.GetInputs().GetChildren():
        #print("in:",the_port)
        if maxon.GraphModelHelper.IsConnected(const_port, the_port):
            return the_port

    return None

def CreateDescription(**kwargs) -> dict:
    description = {}
    for key, value in kwargs.items():
        description[key] = value
    return description

def GetPortId(port: maxon.GraphNode) -> str:
    nodeId: str = str(port.GetId())
    if '>' in nodeId:
        return nodeId.split('>')[-1]
    elif '<' in nodeId:
        return nodeId.split('<')[-1]
    else:
        return nodeId



# ok
@dataclass
class Connection:
    """represents a connection between two ports A -> B in the graph"""

    portA: maxon.GraphNode
    portB: maxon.GraphNode

    def __post_init__(self) -> None:
        self.nodeA = GetTrueNode(self.portA)
        self.nodeB = GetTrueNode(self.portB)

    def __repr__(self) -> str:
        return f"{self.portA} -> {self.portB}"
    
    def GetNodeId(self, port: maxon.GraphNode) -> str:
        return str(GetTrueNode(port).GetId()).split("@")[-1]
    
@dataclass
class PortData:

    port: maxon.GraphNode = field(default_factory=maxon.GraphNode, repr=False)

    def __post_init__(self) -> None:
        self.node = GetTrueNode(self.port)
        self.id = str(GetTrueNode(self.node).GetId())
        self.name = GetName(self.node)

    def IsInput(self) -> bool:
        return self.port.GetKind() == maxon.NODE_KIND.INPORT

    def IsOutput(self) -> bool:
        return self.port.GetKind() == maxon.NODE_KIND.OUTPORT

# ok
@dataclass
class NodeData:

    node: maxon.GraphNode = field(default_factory=maxon.GraphNode, repr=False)

    depth: int = field(default_factory=int)
    query: str = field(default_factory=str, repr=False)
    qmode: int = field(default=GraphDescription.QUERY_FLAGS.MATCH_ALL, repr=False)

    def __post_init__(self) -> None:

        self.asset_type: str = "#" + str(self.node.GetValue("net.maxon.node.attribute.assetid"))[1:].split(",")[0]
        self.asset_id: str = str(GetTrueNode(self.node).GetId())
        self.input_connections: list = maxon.GraphModelHelper.GetDirectSuccessors(self.node, maxon.NODE_KIND.NODE)
        self.output_connections: list = maxon.GraphModelHelper.GetDirectPredecessors(self.node, maxon.NODE_KIND.NODE)

    def __repr__(self) -> str:
        return f"{self.GetNodeName()} (Depth:{self.depth}) ({self.get_hash()})"
    
    def get_hash(self) -> str:
        return self.asset_id.split("@")[-1]
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NodeData):
            return False
        return self.get_hash() == other.get_hash()

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, NodeData):
            return False
        return self.depth < other.depth

    def get_custom_attributes(self):
        custom_attributes = {}
        all_attributes = dir(self)
        for attr in all_attributes:
            if not attr.startswith('__') and not callable(getattr(self, attr)):
                custom_attributes[attr] = getattr(self, attr)
        return custom_attributes

    def get_input_connections(self) -> list[Connection]:
        res = []
        for node in maxon.GraphModelHelper.GetDirectSuccessors(self.node, maxon.NODE_KIND.INPORT):
            res.append(Connection(portA=GetConnectedPort(node, self.node), portB=node))
        return res

    def get_output_connections(self) -> list[Connection]:
        res = []
        for node in maxon.GraphModelHelper.GetDirectPredecessors(self.node, maxon.NODE_KIND.OUTPORT):
            res.append(Connection(portA=node, portB=GetConnectedPort(node, self.node)))
        return res

    def GetPortDescription(self, port: maxon.GraphNode) -> str:
        return f"#<{GetPortId(port)}"

    def GetNodeDescription(self, node: maxon.GraphNode) -> str:
        return f"#{str(node.GetValue('net.maxon.node.attribute.assetid'))[1:].split(',')[0]}"

    def GetNodeName(self) -> str:
        return GetName(GetTrueNode(self.node))

    def GetInputCounts(self) -> int:
        return len(self.get_input_connections())

    def GetOutputCounts(self) -> int:
        return len(self.get_output_connections())
    
    def Show(self) -> None:
        print(f"Node:{' '*4}{self.GetNodeName()} (Depth:{self.depth})")
        print(f"{' '*4}$id: {self.asset_id}")
        print(f"{' '*4}$type: {self.asset_type}")
        # print(f"{' '*4}$query: {self.query}")
        # print(f"{' '*4}$qmode: {self.qmode}")

        for n, input in enumerate(self.get_input_connections(), start=1):
            print(f"{' '*8}Connection {n}: {self.GetPortDescription(input.portA)}")
            print(f"{' '*8}Connection node {n}: {self.GetNodeDescription(GetTrueNode(input.portB))}")

        print(f"{' '*4}---")
        
        for n, output in enumerate(self.get_output_connections(), start=1):
            print(f"{' '*8}Connection {n}: {self.GetPortDescription(output.portB)}")
            print(f"{' '*8}Connection node {n}: {self.GetNodeDescription(GetTrueNode(output.portA))}")

        print("-"*20)

    def CtreateDescription(self, use_query: bool=False, use_qmode: bool=False, enable_output: bool=False) -> dict:
        """ Create a description for the given node. 
        
        ---
        Example:
            ```python
            {
            '$type': '#com.redshift3d.redshift4c4d.node.output',
            '$id': 'output@Z$42uvLhJ9hjmahTpNLcbn',
            '#<com.redshift3d.redshift4c4d.node.output.surface': 'standardmaterial@JPzeQVJWFJmvEc4zo562Eg'
            }
        """
        desc = {}
        desc["$type"] = self.asset_type
        desc["$id"] = self.asset_id
        if use_query:
            desc["$query"] = self.query
        if use_qmode:
            desc["$qmode"] = str(self.qmode)
        if enable_output:
            for input in self.get_input_connections():
                desc[str(self.GetPortDescription(input.portA))] = str(GetTrueNode(input.portB).GetId())
        for output in self.get_output_connections():
            desc[str(self.GetPortDescription(output.portB))] = str(GetTrueNode(output.portA).GetId())
        return desc

# ok
# todo: arnold node id must as the same as the arnold node last id
@dataclass
class DescriptionConverter:

    data: dict[str] = field(default_factory=dict, repr=False)

    sourceSpcace: str = field(default=None, repr=False)

    def __post_init__(self) -> None:

        self._reslut: dict[str, str] = None

        if self.sourceSpcace is None:
            nodespace = self._guess_nodespace()
            if nodespace:
                self.source_index = NODESPACE_INDEX[nodespace]

        if self.sourceSpcace not in NODESPACE_INDEX:
            raise ValueError(f"Invalid source space: {self.sourceSpcace}")

        self.source_index: int = NODESPACE_INDEX.index(self.sourceSpcace)
        self.target_index: int = self.source_index

    def _contains(self, pattern: str) -> bool:
        if isinstance(self.data, dict):
            for key, value in self.data.items():
                if pattern.lower() in key.lower() or (isinstance(value, str) and pattern.lower() in value.lower()):
                    return True
                elif isinstance(value, dict):
                    if self._contains(value):
                        return True
        return False

    def _guess_nodespace(self) -> str:
        """
        Guess the node space of the node from the description.
        """
        if self._contains('redshift'):
            return RS_NODESPACE
        elif self._contains('arnold'):
            return AR_NODESPACE
        elif self._contains('vray'):
            return VR_NODESPACE
        elif self._contains('centileo'):
            return CE_NODESPACE
        else:
            raise ValueError(f"Cannot guess node space from description: please specify the node space manually.")

    def in_desc(self, desc: list, value: str) -> bool:
        """
        Check if the value is in the description.
        """
        for i in desc:
            if isinstance(i, list):
                if value in i:
                    return True
            elif i == value:
                return True
        return False

    def get_desc_index(self,desc: list, value: str) -> int:
        """
        Get the index of the value in the description.
        """
        for index, i in enumerate(desc):
            if self.in_desc(i, value):
                return index
        return -1

    def get_aid_index(self, desc: list, value: str) -> int:
        def _in_desc(desc: list, value: str) -> bool:
            """
            Check if the value is in the description.
            """
            for i in desc:
                if isinstance(i, list):
                    return _in_desc(i, value)
                elif i.split('.')[-1] == value:
                    return True
            return False
        
        for index, i in enumerate(desc):
            if _in_desc(i, value):
                return index
        return -1
    
    # ok
    def replace_type(self, dict_data: dict[str, str]) -> dict[str, str]:
        key: str
        value: str
        search_value = '$type'

        for key, value in dict_data.items():
            if isinstance(value, dict):
                dict_data[key] = self.replace_type(value)
            elif isinstance(value, str):
                if key == search_value:
                    node_type = value.replace('#', '')
                    current_map = DESCRIPTION_MAPS[self.get_desc_index(DESCRIPTION_MAPS, node_type)]
                    dict_data[key] = f'#{current_map[self.target_index]}'
        return dict_data

    def replace_extra_data(self, data: list[dict[str, str]]) -> dict[str, str]:
        """ [{'id': 'texturesampler@AKMaQu48Apav2u1dmdIDQe', 'path': asset:///file_5b6a5fe03176444c~.png}]
        """
        key: str
        value: str
        search_value = 'id'

        for i in data:
            for key, value in i.items():
                if key == search_value:
                    node_type, hash_num = value.split('@')
                    current_map = DESCRIPTION_MAPS[self.get_aid_index(DESCRIPTION_MAPS, node_type)]
                    new_node = str(current_map[self.target_index])
                    new_type = new_node.split('.')[-1]
                    # print(f"{node_type} -> {new_type}")
                    i[key] = f'{new_type}@{hash_num}'
        return data

    # ok, not used because we don't need to replace id, and it will cause problem when we create reference
    def replace_id(self, dict_data: dict[str, str]) -> dict[str, str]:
        key: str
        value: str
        search_value = '$type'
        id_value = '$id'

        for key, value in dict_data.items():
            if isinstance(value, dict):
                dict_data[key] = self.replace_id(value)
            elif isinstance(value, str):
                if key == id_value:
                    old_type = dict_data.get(search_value, '').split('.')[-1]
                    hash_num = value.split('@')[1]
                    new_id = f'{old_type}@{hash_num}'
                    dict_data[key] = new_id
        return dict_data

    # ok
    def replace_slot(self, original_dict: dict[str, str]):
        new_dict = {}
        
        for key, value in original_dict.items():
            # 检查当前键是否以 #< 开头
            if key.startswith('#<'):
                # new_key = key + 'ABC'  # 替换键名称
                node_type = original_dict.get('$type', '').replace('#', '')
                old_key = key.replace('#<', '')
                # print(f"Node type: {node_type}, old key: {old_key}")
                current_map = DESCRIPTION_MAPS[self.get_desc_index(DESCRIPTION_MAPS, node_type)]
                slots_map = current_map[-1]
                # print(f'{ slots_map = }')
                sub_map_index = self.get_desc_index(slots_map, old_key)
                sub_map = slots_map[sub_map_index]
                tar_node_type = sub_map[self.target_index]
                new_key = f'#<{tar_node_type}'
                # print(f"{key} -> {new_key}")
            else:
                new_key = key  # 保持原键名称
            
            # 如果值是字典，进行递归处理
            if isinstance(value, dict):
                new_dict[new_key] = self.replace_slot(value)
            else:
                new_dict[new_key] = value  # 对于非字典类型的值，直接赋值
        
        return new_dict

    def replace_duplicate_ids(self, data: Dict[str, Any],seen_ids: Set[str] = None) -> Dict[str, Union[str, Any]]:
        """
        Replace duplicate `$id` values in a nested dictionary with prefixed `#<value>` strings.
        """
        if seen_ids is None:
            seen_ids = set()

        for key, value in list(data.items()):  # 使用 list 确保安全迭代
            if isinstance(value, dict):
                data[key] = self.replace_duplicate_ids(value, seen_ids)
            elif key == "$id":
                if value in seen_ids:
                    # 如果 $id 是重复的，将其替换为带 `#` 的字符串
                    data = f"#{value}"
                else:
                    # 记录当前的 $id
                    seen_ids.add(value)
        return data

    def convert_to(self, target_space: str) -> dict:
        if target_space not in NODESPACE_INDEX:
            raise ValueError(f"Invalid target space: {target_space}")
        self.target_index: int = NODESPACE_INDEX.index(target_space)
        dict_data: dict[str, str] = self.data
        new_data = self.replace_type(dict_data)
        new_data = self.replace_id(new_data)
        new_data = self.replace_slot(new_data)
        new_data = self.replace_duplicate_ids(new_data)
        return new_data

# ok
@dataclass
class DescriptionHelper(NodeGraghHelper):
    """ Absolute API identifiers are actually not identifiers but node paths, 
    a concept from the Nodes API to describe entities in a graph tree. 
    This is why absolute input port identifiers must start with #< and output port identifiers with #>, 
    as the the < and > characters are used to denote the port type.

    Nested ports are separated by slashes in API identifiers, e.g., #<parent_port/child_port.

    Make sure to include leading dots in lazy identifiers, 
    e.g., #~.base_color to avoid matching against foo.barbase_color. 
    The same applies for nested ports, write #~/path and not #~path.
    
    """
    
    material: c4d.BaseMaterial = field(default_factory=c4d.BaseMaterial, repr=False)

    INPUTS = "<" # The identifier '<', this is used for the input port list of a node.
    OUTPUTS = ">" # The identifier '>', this is used for the output port list of a node.
    TEMPLATE = "#" # The identifier '#', this is used for the template port of a variadic port.
    NESTED = "/" # The identifier '/', this is used for the nested port of a parent port.
    LAZY = "~" # The identifier '~', this is used for lazy identifiers.

    def __post_init__(self) -> None:
        self.data: list[dict[str]] = []
        super().__init__(self.material)

        # self.nodeMaterial: c4d.NodeMaterial = self.material.GetNodeMaterialReference()
        # self.graph: maxon.GraphModelInterface = None
        # for nid in (RS_NODESPACE, AR_NODESPACE, VR_NODESPACE, CE_NODESPACE):
        #     if self.nodeMaterial.HasSpace(nid):
        #         self.graph: maxon.GraphModelRef = self.nodeMaterial.GetGraph(nid)

        #         if c4d.GetC4DVersion() >= 2025000:
        #             self.root: maxon.GraphNode = self.graph.GetViewRoot()
        #         else:
        #             self.root: maxon.GraphNode = self.graph.GetRoot()

    def _iter_tree(self, node: maxon.GraphNode, depth: int=0) -> Iterator[maxon.GraphNode]:

        yield (node, depth)
        for child in maxon.GraphModelHelper.GetDirectPredecessors(node, maxon.NODE_KIND.NODE):
            for item in self._iter_tree(child, depth + 1):
                yield item

    def _traverse_graph(self):
        """ traverse the graph and create a list of NodeData
        """
        with EasyTransaction(self.material) as tr:
            endNode = tr.GetOutput()
            for item in self._iter_tree(endNode):
                node = item[0]
                index = item[1]
                node_data = NodeData(node=node, depth=index)
                node_description = node_data.CtreateDescription()
                self.data.append(node_description)
        return self.data
                        
    def __repr__(self) -> str:
        return f"Description Helper of {self.material.GetName()}"

    def _convert(self) -> list[dict[str, str]]:
        """ convert the data from list to nested dict
        """
        for i in self.data:
            for key, value in list(i.items()):
                if key.startswith('#<'):
                    for other in self.data:
                        if other.get('$id') == value:
                            i[key] = other


    # def replace_duplicate_ids(self, data: Dict[str, Any],seen_ids: Set[str] = None) -> Dict[str, Union[str, Any]]:
    #     """
    #     Replace duplicate `$id` values in a nested dictionary with prefixed `#<value>` strings.
    #     """
    #     if seen_ids is None:
    #         seen_ids = set()

    #     for key, value in list(data.items()):  # 使用 list 确保安全迭代
    #         if isinstance(value, dict):
    #             data[key] = self.replace_duplicate_ids(value, seen_ids)
    #         elif key == "$id":
    #             if value in seen_ids:
    #                 # 如果 $id 是重复的，将其替换为带 `#` 的字符串
    #                 data = f"#{value}"
    #             else:
    #                 # 记录当前的 $id
    #                 seen_ids.add(value)
    #     return data

    def GetDescription(self) -> list[dict[str, str]]:
        """ get the description of the material
        """
        self._traverse_graph()
        self.extra_data = self.get_image_path_data()
        self._convert()
        #self.data = self.replace_duplicate_ids(self.data[0])
        return self.data[0]
    
    def get_asset_id(self, node: maxon.GraphNode) -> str:
        str(node.GetValue("net.maxon.node.attribute.assetid"))[1:].split(",")[0]

    def get_node_by_id(self, material: c4d.BaseMaterial, target_space, node_id: str) -> maxon.GraphNode:
        # node_material = material.GetNodeMaterialReference()
        graph = GraphDescription.GetGraph(material, target_space)
        return maxon.GraphModelHelper.FindNodesById(graph, node_id, kind=maxon.NODE_KIND.NODE, direction=maxon.PORT_DIR.INPUT | maxon.PORT_DIR.OUTPUT, exactId=True, callback=None)[0]

    def get_node_by_assetid(self, asset_id: str) -> list[maxon.GraphNode] :
        result: list[maxon.GraphNode] = []
        maxon.GraphModelHelper.FindNodesByAssetId(self.graph, asset_id, True, result)
        return result

    def in_desc(self, desc: list, value: str) -> bool:
        """
        Check if the value is in the description.
        """
        for i in desc:
            if isinstance(i, list):
                if value in i:
                    return True
            elif i == value:
                return True
        return False

    def get_desc_index(self,desc: list, value: str) -> int:
        """
        Get the index of the value in the description.
        """
        for index, i in enumerate(desc):
            if self.in_desc(i, value):
                return index
        return -1

    # def get_new_id(self, node: maxon.GraphNode) -> str:

    #     current_map = DESCRIPTION_MAPS[self.get_desc_index(DESCRIPTION_MAPS, node_type)]
    #     dict_data[key] = f'#{current_map[self.target_index]}'

    def get_image_path_data(self) -> list[dict[str, str]]:
        image_node_id, texture_port_data = self.GetImageNodeID(include_portData=True)
        inTexturePortId = texture_port_data[1]
        # print(f"Image node id: {image_node_id} [{type(image_node_id)}], texture port id: {texture_port_id} [{type(texture_port_id)}]")
        image_nodes = self.GetNodes(str(image_node_id))
        res = []
        for node in image_nodes:
            data = {}

            port: maxon.GraphNode = self.graph.GetNode(maxon.NodePath(str(node.GetPath()) + '<' + str(inTexturePortId)))
            # if self.nodespaceId == RS_NODESPACE:
            #     port = self.GetPort(node, "com.redshift3d.redshift4c4d.nodes.core.texturesampler.tex0").FindChild("path")
            # elif self.nodespaceId == AR_NODESPACE:
            #     port = self.GetPort(node, "filename")

            data['id'] = str(node.GetId())
            data['path'] = self.GetPortData(port)
            
            res.append(data)
        return res

    def rebuild_image_path(self, material: c4d.BaseMaterial, path_data: list[dict[str, str]], target_space: str) -> None:
        cvt = DescriptionConverter(self.data, target_space)
        ext_data = cvt.replace_extra_data(path_data)
        print(ext_data)

        with EasyTransaction(material, nodespaceId=target_space) as tr:
            for data in ext_data:
                node = self.get_node_by_id(material, target_space, data['id'])
                if target_space == RS_NODESPACE:
                    port = tr.GetPort(node, "com.redshift3d.redshift4c4d.nodes.core.texturesampler.tex0").FindChild("path")
                    tr.SetPortData(port, data['path'])
                elif target_space == AR_NODESPACE:
                    print(node)
                    print(tr.GetAssetId(node))
                    port = tr.GetPort(node, "filename")
                    print(port)
                    tr.SetPortData(port, data['path'])
                    print(f"Set {data['path']} to {port}")

    def get_node_space(self) -> str:
        """
        Get the node space of the material.
        """
        for nodespace in NODESPACE_INDEX:
            if self.nodeMaterial.HasSpace(NODESPACE_INDEX[nodespace]):
                return nodespace

    def ConvertTo(self, data: dict, target_space: str) -> None:
        """ convert the description to the target space
        """
        # img_data = self.get_image_path_data()
        converter = DescriptionConverter(data, self.nodespaceId)
        new_data = converter.convert_to(target_space)
        return new_data
    
    def BuildMaterial(self, name: str, target_space: str, description: dict) -> c4d.BaseMaterial:
        material = c4d.BaseMaterial(c4d.Mmaterial)
        material.SetName(name)
        graph = GraphDescription.GetGraph(material, target_space)
        # graph = GraphDescription.CreateGraph(name=name,nodeSpaceId=target_space)
        # new_description = self.ConvertTo(description, target_space)
        GraphDescription.ApplyDescription(graph, description)

        self.rebuild_image_path(material, self.extra_data, target_space)
        return material

# OC
{
    '$type': '#1029501', # material id
    #'$id': '2516', # material type
    '#<2517' : {     
        '$type': '#1029512', # cc
        '#<1050' : { # texture
            '$type': '#1029508', # img
            '1100' : ''} # file path,
            },
    '#<2533' : { # rough
        '$type': '#1029513', # ramp
        '#<1130' : { # c4d.GRADIENT_TEXTURE_LNK  
            '$type': '#1029512', # cc
            '#<1050' : { # texture
                '$type': '#1029508', # img
                '1100' : ''} # file path,
                }
    }
}

# CR 
{
    '$type': '#1056306', # material id
    '$id': 'material@15asd45', # id
    '#<20202' : {     
        '$type': '#1038518', # cc
        '$id': 'color_correction@576sdad', # id
        '#<11601' : { # texture
            '$type': '#1036473', # img
            '$id': 'bitmap@454sdahd', # id
            '11520' : ''} # file path,
            },
    '#<20209' : { # rough
        '$type': '#1011116', # ramp
        '$id': 'tamp@asdja426', # id
        }
}

MAPPINGS: dict = {
    # The Octane Material model
    "Material": {
        # These are mapping from input port names on a "RS Material" to parameter IDs in a standard
        # material. Added must also be the channel activation ID, e.g., when we map a diffuse color
        # texture, we not only need to set MATERIAL_COLOR_SHADER to the texture, we must also enable
        # MATERIAL_USE_COLOR in the first place.

        # Port name    : (param id,                   channelId)
        "Diffuse Color": (c4d.MATERIAL_COLOR_SHADER, c4d.MATERIAL_USE_COLOR),
        "Refl Color": (c4d.REFLECTION_LAYER_COLOR_TEXTURE, c4d.MATERIAL_USE_REFLECTION),
        "Refl Roughness": (c4d.REFLECTION_LAYER_MAIN_SHADER_ROUGHNESS, c4d.MATERIAL_USE_REFLECTION)
        # Add channel mappings to your liking ...
    },
    # The RS Standard Material model
    "StandardMaterial": {
        "Base Color": (c4d.MATERIAL_COLOR_SHADER, c4d.MATERIAL_USE_COLOR),
        "Refl Color": (c4d.REFLECTION_LAYER_COLOR_TEXTURE, c4d.MATERIAL_USE_REFLECTION),
        "Refl Roughness": (c4d.REFLECTION_LAYER_MAIN_SHADER_ROUGHNESS, c4d.MATERIAL_USE_REFLECTION),
        "Bump Input": (c4d.MATERIAL_BUMP_SHADER, c4d.MATERIAL_USE_BUMP)
        # Add channel mappings to your liking ...
    }
    # Define more material models ...
}

# todolist:
# 1. 实现对Octane材质的解析
# 2. 实现对CR材质的解析
# 3. 实现对材质的转换
@dataclass
class OctaneNodeDescription:

    type: str
    id: str

    inputs: dict[str, str]
    outputs: dict[str, str]

    def __post_init__(self) -> None:
        self.inputs = {}
        self.outputs = {}

    def add_input(self, name: str, node_id: str) -> None:
        self.inputs[name] = node_id

    def add_output(self, name: str, node_id: str) -> None:
        self.outputs[name] = node_id

@dataclass
class CRNodeDescription:

    # material: c4d.BaseMaterial
    data: dict[str]

    def __post_init__(self) -> None:
        material_type = self.data.get('$type', '')
        self.material = c4d.BaseMaterial(material_type)

    def find_level(self, data, target, level=0):
        if isinstance(data, dict):  # 确保数据是字典
            for key, value in data.items(): 
                if key == target or value == target:
                    return level  # 找到键或值，返回当前层级
                
                # 递归调用，层级加1
                found_level = self.find_level(value, target, level + 1)
                if found_level is not None:  # 如果找到了，返回结果
                    return found_level
        return None

    def create_with_type(self, dict_data: dict[str, str]) -> dict[str, str]:
        key: str
        value: str
        material_level: int = 0

        for key, value in dict_data.items():
            if isinstance(value, dict):
                dict_data[key] = self.create_with_type(value)
            elif isinstance(value, str):
                if key == '$type':
                    node_type = value.replace('#', '')
                    node = c4d.BaseShader(node_type)
                    self.material.InsertShader(node)

                    for k, v in dict_data.items():
                        if k.startswith('#<') and isinstance(v, dict):
                            child_id: str = v.get('$type', '')
                            if child_id:
                                child = c4d.BaseShader(int(child_id.replace('#', '')))
                                self.material.InsertShader(child)
                                self.material[int(k.replace('#<', ''))] = c4d.BaseShader(child)

        return dict_data
    
if __name__ == '__main__':
    Renderer.ClearConsole()
    doc: c4d.documents.BaseDocument  = c4d.documents.GetActiveDocument()  # The active document.
    active_material: c4d.BaseMaterial = doc.GetActiveMaterial()  # The currently active material.

    desc_helper = DescriptionHelper(material=active_material)
    data = desc_helper.GetDescription()
    new_data = desc_helper.ConvertTo(data, AR_NODESPACE)
    pp(new_data)
    mat = desc_helper.BuildMaterial("convert_test", AR_NODESPACE, new_data)
    doc.InsertMaterial(mat)

    # pp(data)
    # img_data = desc_helper.get_image_path_data()
    # pp(img_data)
    # converter = DescriptionConverter(data, RS_NODESPACE)
    # nd = converter.convert_to(AR_NODESPACE)
    # pp(nd)
    # GraphDescription.ApplyDescription(GraphDescription.CreateGraph(name="convert_test",nodeSpaceId=AR_NODESPACE), nd)

