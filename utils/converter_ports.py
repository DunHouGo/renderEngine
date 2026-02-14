# -*- coding: utf-8 -*-
"""Converter port data for node graph textures (Redshift, Arnold, V-Ray, CentiLeo)."""
import c4d
import maxon
import os
import json
from typing import Union

from ..constants.common_id import (
    RS_NODESPACE,
    AR_NODESPACE,
    VR_NODESPACE,
    CL_NODESPACE,
)


class ConverterPorts:
    """
    Custom Helper for get the "Converter Port" in trick.

    data = {
        "Redshift.json" : {
            "com.redshift3d.redshift4c4d.nodes.core.texturesampler" : {
                "Name" : "Texture"
                "Input" : "None"
                "Output": "com.redshift3d.redshift4c4d.nodes.core.texturesampler.outcolor"
            }
            ...
        }
    }
    """

    def __init__(self, nodespaceId: maxon.Id) -> None:
        self.nodespaceId: maxon.Id = nodespaceId

        FILEPATH, f = os.path.split(__file__)
        parent_dir = os.path.abspath(os.path.join(FILEPATH, os.pardir))

        if self.nodespaceId == RS_NODESPACE:
            self.dataPath = os.path.join(parent_dir, 'constants', "Redshift.json")
        if self.nodespaceId == AR_NODESPACE:
            self.dataPath = os.path.join(parent_dir, 'constants', "Arnold.json")
        if self.nodespaceId == VR_NODESPACE:
            self.dataPath = os.path.join(parent_dir, 'constants', "Vray.json")
        if self.nodespaceId == CL_NODESPACE:
            self.dataPath = os.path.join(parent_dir, 'constants', "CentiLeo.json")
        if not os.path.exists(self.dataPath):
            raise FileNotFoundError(f"the Converter data is not exist at {self.dataPath}")

    @staticmethod
    def _InitData(
        nodespace_id: str,
        asset_prefix: str,
        out_port_candidates: list,
        in_port_candidates: list,
        use_full_port_id: bool,
        create_empty_graph: bool,
        skip_failed_nodes: bool,
    ) -> dict:
        """
        Internal: build converter port data for a node space.
        use_full_port_id: if True, port_id = asset_id + '.' + name; else FindChild(name) only.
        create_empty_graph: if True use CreateEmptyGraph else CreateDefaultGraph.
        skip_failed_nodes: if True wrap each node in try/except.
        """
        repo: maxon.AssetRepositoryRef = maxon.AssetInterface.GetUserPrefsRepository()
        if repo.IsNullValue():
            raise RuntimeError("Could not access the user preferences repository.")
        nodeTemplateDescriptions: list = repo.FindAssets(
            maxon.Id("net.maxon.node.assettype.nodetemplate"), maxon.Id(), maxon.Id(),
            maxon.ASSET_FIND_MODE.LATEST)
        allShaders = [
            str(item.GetId())
            for item in nodeTemplateDescriptions
            if str(item.GetId()).startswith(asset_prefix)
        ]
        output = {}
        space_id = maxon.Id(nodespace_id)

        def _asset_id(shader):
            return str(shader.GetValue("net.maxon.node.attribute.assetid"))[1:].split(",")[0]

        def _GetOutput(shader):
            for out in out_port_candidates:
                port_id = f"{_asset_id(shader)}.{out}" if use_full_port_id else out
                port = shader.GetOutputs().FindChild(port_id)
                if not port.IsNullValue():
                    return str(port.GetId())
            return ""

        def _GetInput(shader):
            for out in in_port_candidates:
                port_id = f"{_asset_id(shader)}.{out}" if use_full_port_id else out
                port = shader.GetInputs().FindChild(port_id)
                if not port.IsNullValue():
                    return str(port.GetId())
            return ""

        if c4d.GetActiveNodeSpaceId() != space_id:
            raise RuntimeError("Make the target renderer the active renderer and node space to run this script.")
        material = c4d.BaseMaterial(c4d.Mmaterial)
        if not material:
            raise MemoryError(f"{material = }")
        nodeMaterial = material.GetNodeMaterialReference()
        if create_empty_graph:
            graph = nodeMaterial.CreateEmptyGraph(space_id)
            if graph.IsNullValue():
                raise RuntimeError("Could not add graph to material.")
        else:
            graph = nodeMaterial.CreateDefaultGraph(space_id)
        with graph.BeginTransaction() as gt:
            for nodeId in allShaders:
                data = {}
                try:
                    node = graph.AddChild(maxon.Id(), maxon.Id(nodeId) if create_empty_graph else nodeId)
                    data["input"] = str(_GetInput(node))
                    data["output"] = str(_GetOutput(node))
                    output[_asset_id(node)] = data
                except Exception:
                    if not skip_failed_nodes:
                        raise
            gt.Commit()
        c4d.documents.GetActiveDocument().InsertMaterial(material)
        c4d.EventAdd()
        return output

    @staticmethod
    def InitRedshiftData() -> dict:
        """
        Get the basic data, then save the date and modity it.
        This should be used if the data is missing or you want to customizd
        Returns:
            dict[dict[str]]: teh data we want
        """
        return ConverterPorts._InitData(
            nodespace_id=RS_NODESPACE,
            asset_prefix="com.redshift3d.redshift4c4d.",
            out_port_candidates=['outcolor', 'output', 'out'],
            in_port_candidates=['color', 'input', 'base_color', 'tex0', 'albedo', 'texture', 'input1', 'x', 'default', 'attribute'],
            use_full_port_id=True,
            create_empty_graph=False,
            skip_failed_nodes=False,
        )

    @staticmethod
    def InitArnoldData() -> dict:
        """
        Get the basic data, then save the date and modity it.
        This should be used if the data is missing or you want to customizd
        Returns:
            dict[dict[str]]: teh data we want
        """
        return ConverterPorts._InitData(
            nodespace_id=AR_NODESPACE,
            asset_prefix="com.autodesk.arnold.",
            out_port_candidates=['outcolor', 'output', 'out'],
            in_port_candidates=['color', 'input', 'base_color', 'filename', 'tex0', 'albedo', 'texture', 'input1', 'x', 'default', 'aov_name'],
            use_full_port_id=False,
            create_empty_graph=False,
            skip_failed_nodes=False,
        )

    @staticmethod
    def InitVrayData() -> dict:
        """
        Get the basic data, then save the date and modity it.
        This should be used if the data is missing or you want to customizd

        Returns:
            dict[dict[str]]: teh data we want
        """
        return ConverterPorts._InitData(
            nodespace_id=VR_NODESPACE,
            asset_prefix="com.chaos.vray_node.",
            out_port_candidates=['output.default', 'outcolor', 'output', 'out'],
            in_port_candidates=['file', 'color', 'input', 'base_color', 'color1', 'color_a', 'value', 'input_color', 'tex0', 'albedo', 'texture', 'float_a', 'texture_x', 'input1', 'x', 'default', 'attribute', 'texture_map', 'basemap'],
            use_full_port_id=True,
            create_empty_graph=True,
            skip_failed_nodes=True,
        )

    @staticmethod
    def InitCentiLeoData() -> dict:
        """
        Get the basic data, then save the date and modity it.
        This should be used if the data is missing or you want to customizd
        Returns:
            dict[dict[str]]: teh data we want
        """
        return ConverterPorts._InitData(
            nodespace_id=CL_NODESPACE,
            asset_prefix="com.centileo.node.",
            out_port_candidates=['result', 'out', 'result_id', 'root_uvw', 'output', 'result_material'],
            in_port_candidates=['filename', 'surface_material', 'diffuse_color', 'emission_color', 'materialref', 'material1', 'material0', 'mtl_direct', 'map_yz', 'color1', 'input_map', 'uvw_map', 'tex_direct', 'displacement_map', 'input_color', 'math_a', 'in', 'distance_map', 'float_a', 'map90', 'uvw_offset', 'seed_map', 'uvw_projection', 'input1', 'x', 'default', 'attribute', 'texture_map', 'basemap'],
            use_full_port_id=True,
            create_empty_graph=True,
            skip_failed_nodes=True,
        )

    # todo
    @staticmethod
    def InitBasicData() -> dict:
        pass

    ### Key methods ###

    def IsGeneratorNode(self, node: maxon.GraphNode) -> bool:
        """
        True if the node don't have a input data. so we call it generator.

        Args:
            node (maxon.GraphNode): the host node

        Returns:
            bool: True if the node don't have a input data.
        """
        if self.GetConvertInput(node) == "":
            return True
        return False

    def GetConvertInput(self, StrOrNode: Union[str, maxon.GraphNode]) -> str:
        """
        Get the default in port of the node.

        Args:
            StrOrNode (Union[str, maxon.GraphNode]): the node or it's string id.

        Returns:
            str: the string id of the default in port, else ""
        """
        assetId = ""
        if isinstance(StrOrNode, str):
            assetId = StrOrNode
        elif isinstance(StrOrNode, maxon.GraphNode):
            if StrOrNode.GetKind() == maxon.NODE_KIND.NODE:
                assetId = str(StrOrNode.GetValue("net.maxon.node.attribute.assetid"))[1:].split(",")[0]

        with open(self.dataPath, 'r', encoding='UTF-8') as file:
            data: dict = json.loads(file.read())

        item: dict = data.get(assetId, "")
        if item == "":
            return ""
        return item.get("input", "")

    def GetConvertOutput(self, StrOrNode: Union[str, maxon.GraphNode]) -> str:
        """
        Get the default out port of the node.

        Args:
            StrOrNode (Union[str, maxon.GraphNode]): the node or it's string id.

        Returns:
            str: the string id of the default out port, else ""
        """
        assetId = ""
        if isinstance(StrOrNode, str):
            assetId = StrOrNode
        elif isinstance(StrOrNode, maxon.GraphNode):
            if StrOrNode.GetKind() == maxon.NODE_KIND.NODE:
                assetId = str(StrOrNode.GetValue("net.maxon.node.attribute.assetid"))[1:].split(",")[0]

        with open(self.dataPath, 'r', encoding='UTF-8') as file:
            data: dict = json.loads(file.read())
        item: dict = data.get(assetId, "")
        if item == "":
            return ""
        return item.get("output", "")
