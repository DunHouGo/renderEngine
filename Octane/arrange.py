# -*- coding: utf-8 -*-
"""Octane material node auto-arrange and align helpers.

机制（已在 OC 2025.3 实测验证）：
  1. OC 节点位置存放在每个节点的 [ID_OCTANE_NE_SAVER][ID_OCTANE_NE_NODE_POS] = Vector(x, y, 0)
  2. 写入坐标后触发材质隐藏参数 ID_OCTANE_AUTO_ARRANGE（对应节点编辑器右键菜单 Auto-arrange）
     -> OC 会立即刷新打开中的节点编辑器，并保留子容器里的坐标
"""

import c4d
from typing import Optional

from ..constants import ID_OCTANE_NE_SAVER, ID_OCTANE_NE_NODE_POS, ID_OCTANE_AUTO_ARRANGE
from ..utils.node_arrange import (
    ArrangeConfig,
    ALIGN_MODES,
    align_positions,
    distribute_positions,
    get_align_targets,
    layered_positions,
    walk_shaders,
)


def IsOctaneMaterial(material: c4d.BaseMaterial) -> bool:
    """Check if the material is an Octane material.

    Args:
        material: The material to check.

    Returns:
        True when the material belongs to the c4doctane plugin.
    """
    if not isinstance(material, c4d.BaseMaterial):
        return False
    plug = c4d.plugins.FindPlugin(material.GetType(), c4d.PLUGINTYPE_MATERIAL)
    if plug is None:
        return False
    fn = plug.GetFilename()
    return fn is not None and "c4doctane" in fn.lower()


class ArrangeHelper:
    """Auto-arrange, align and inspect nodes of one Octane material.

    Example:
        >>> helper = ArrangeHelper(material)
        >>> helper.Arrange()          # 分层流向布局并刷新节点编辑器
        >>> helper.Align("top")       # 对齐当前选中的节点
    """

    def __init__(self, material: c4d.BaseMaterial, doc: c4d.documents.BaseDocument = None):
        """
        Args:
            material: The host Octane material.
            doc: The document owning the material, defaults to the material document.
        """
        if not IsOctaneMaterial(material):
            raise ValueError("This is not an Octane Material")
        self.material: c4d.BaseMaterial = material
        self.doc: c4d.documents.BaseDocument = doc or material.GetDocument() or c4d.documents.GetActiveDocument()

    # =============================================
    # 节点与位置读写
    # =============================================

    def GetNodes(self) -> list[c4d.BaseList2D]:
        """Get the material root node plus all its shaders.

        Returns:
            The material first, then every shader in its shader tree.
        """
        return [self.material] + walk_shaders(self.material.GetFirstShader())

    def GetNodePosition(self, node: c4d.BaseList2D) -> Optional[c4d.Vector]:
        """Read the stored node editor position of a node.

        Args:
            node: The material or one of its shaders.

        Returns:
            The position vector, or None when the node has no stored position.
        """
        data = node.GetDataInstance()
        if data is None:
            return None
        saver = data.GetContainerInstance(ID_OCTANE_NE_SAVER)
        if saver is None:
            return None
        return saver.GetVector(ID_OCTANE_NE_NODE_POS)

    def SetNodePosition(self, node: c4d.BaseList2D, pos: c4d.Vector) -> bool:
        """Write the node editor position of a node.

        容器不存在时自动创建，新材质的节点没有预存位置也能写入。

        Args:
            node: The material or one of its shaders.
            pos: The position vector to store.

        Returns:
            True when the position was written.
        """
        data = node.GetDataInstance()
        if data is None:
            return False
        saver = data.GetContainerInstance(ID_OCTANE_NE_SAVER)
        if saver is None:
            data.SetContainer(ID_OCTANE_NE_SAVER, c4d.BaseContainer())
            saver = data.GetContainerInstance(ID_OCTANE_NE_SAVER)
        if saver is None:
            return False
        saver.SetVector(ID_OCTANE_NE_NODE_POS, pos)
        return True

    def TriggerAutoArrange(self) -> bool:
        """Trigger the built-in auto-arrange parameter to refresh open editors.

        Returns:
            True when the trigger parameter was set.
        """
        try:
            self.material[ID_OCTANE_AUTO_ARRANGE] = 1
        except Exception:
            try:
                self.material.SetParameter(c4d.DescID(ID_OCTANE_AUTO_ARRANGE), True, c4d.DESCFLAGS_SET_0)
            except Exception:
                return False
        c4d.EventAdd()
        return True

    # =============================================
    # 自动排列 / 对齐
    # =============================================

    def Arrange(self, config: ArrangeConfig = None, trigger: bool = True) -> tuple[int, int]:
        """Apply a layered flow layout to all nodes of the material.

        Args:
            config: Layout parameters, defaults to :class:`ArrangeConfig`.
            trigger: Trigger ID_OCTANE_AUTO_ARRANGE afterwards so open editors refresh.

        Returns:
            (写入位置的节点数, 节点总数)
        """
        nodes = self.GetNodes()
        # 保持原有 shader 顺序作为同层排序依据
        order = {id(node): i for i, node in enumerate(nodes)}
        placements = layered_positions(nodes, id(self.material), config, order)

        written = 0
        for node in nodes:
            pos = placements.get(id(node))
            if pos is not None and self.SetNodePosition(node, pos):
                written += 1
        if trigger and written:
            self.TriggerAutoArrange()
        else:
            c4d.EventAdd()
        return written, len(nodes)

    def GetSelectedNodes(self) -> list[c4d.BaseList2D]:
        """Get shaders currently flagged active.

        节点编辑器中的选择不一定回写 BIT_ACTIVE，取不到时调用方应回退全部节点。

        Returns:
            The active shaders (material root excluded).
        """
        return [s for s in walk_shaders(self.material.GetFirstShader()) if s.GetBit(c4d.BIT_ACTIVE)]

    def Align(self, mode: str = "left", nodes: list[c4d.BaseList2D] = None, trigger: bool = True) -> int:
        """Align nodes along one axis, selected nodes first, all nodes as fallback.

        Args:
            mode: One of :data:`ALIGN_MODES`.
            nodes: Explicit node list, defaults to selected or all nodes.
            trigger: Trigger ID_OCTANE_AUTO_ARRANGE afterwards so open editors refresh.

        Returns:
            The number of updated nodes.
        """
        if mode not in ALIGN_MODES:
            raise ValueError(f"Unknown align mode: {mode}")
        all_nodes = self.GetNodes()
        targets = get_align_targets(all_nodes, nodes, lambda n: n.GetBit(c4d.BIT_ACTIVE))
        positions = {id(n): p for n in targets if (p := self.GetNodePosition(n)) is not None}
        if len(positions) < 2:
            return 0
        aligned = align_positions(positions, mode)
        updated = 0
        for node in targets:
            pos = aligned.get(id(node))
            if pos is not None and self.SetNodePosition(node, pos):
                updated += 1
        if updated and trigger:
            self.TriggerAutoArrange()
        return updated

    def Distribute(
        self, axis: str = "y", nodes: list[c4d.BaseList2D] = None, spacing: float = None, trigger: bool = True
    ) -> int:
        """Distribute nodes evenly along an axis, selected nodes first.

        Args:
            axis: "x" or "y".
            nodes: Explicit node list, defaults to selected or all nodes.
            spacing: Optional fixed gap, defaults to spanning the current range.
            trigger: Trigger ID_OCTANE_AUTO_ARRANGE afterwards so open editors refresh.

        Returns:
            The number of updated nodes.
        """
        all_nodes = self.GetNodes()
        targets = get_align_targets(all_nodes, nodes, lambda n: n.GetBit(c4d.BIT_ACTIVE))
        positions = {id(n): p for n in targets if (p := self.GetNodePosition(n)) is not None}
        if len(positions) < 3:
            return 0
        distributed = distribute_positions(positions, axis, spacing)
        updated = 0
        for node in targets:
            pos = distributed.get(id(node))
            if pos is not None and self.SetNodePosition(node, pos):
                updated += 1
        if updated and trigger:
            self.TriggerAutoArrange()
        return updated


# =============================================
# 模块级便捷函数
# =============================================

def ArrangeMaterial(
    material: c4d.BaseMaterial, config: ArrangeConfig = None, doc: c4d.documents.BaseDocument = None
) -> tuple[int, int]:
    """Arrange all nodes of an Octane material with one call.

    Args:
        material: The Octane material to arrange.
        config: Layout parameters, defaults to :class:`ArrangeConfig`.
        doc: The document owning the material.

    Returns:
        (写入位置的节点数, 节点总数)

    Example:
        >>> import Renderer
        >>> Renderer.Octane.ArrangeMaterial(mat)
        (7, 8)
    """
    return ArrangeHelper(material, doc).Arrange(config)


def AlignMaterial(material: c4d.BaseMaterial, mode: str = "left") -> int:
    """Align nodes of an Octane material with one call.

    Args:
        material: The Octane material to align.
        mode: One of :data:`ALIGN_MODES`.

    Returns:
        The number of updated nodes.
    """
    return ArrangeHelper(material).Align(mode)


__all__ = [
    "ArrangeHelper",
    "ArrangeMaterial",
    "AlignMaterial",
    "IsOctaneMaterial",
]
