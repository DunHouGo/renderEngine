# -*- coding: utf-8 -*-
"""Corona material node auto-arrange and align helpers.

Corona 节点编辑器的视图与节点控件存储在场景钩子（CNodeSystemViews 分支）下，
每个控件通过 CORONA_NODESYSTEM_NODE_LINK 指向真实文档节点（材质/着色器），
位置等属性用标准 SetParameter/GetParameter 读写（ID 见 nodesystem.h）。

注意：控件只在该材质被 Corona 节点编辑器打开过后才会生成，
没有视图时本模块的排列会优雅跳过，返回 (0, 节点数)。
"""

import c4d
from typing import Optional

from ..constants import (
    CORONA_STR_NODEMATERIALSHOOK,
    CORONA_NODESYSTEM_VIEW_BRANCH,
    CORONA_NODESYSTEM_NODE_POS_X,
    CORONA_NODESYSTEM_NODE_POS_Y,
    CORONA_NODESYSTEM_NODE_HIDE_BODY,
    CORONA_NODESYSTEM_NODE_HIDE_PREVIEW,
    CORONA_NODESYSTEM_NODE_HIDDEN,
    CORONA_NODESYSTEM_NODE_LINK,
)
from ..constants.corona_id import ID_VALID_MATERIALS
from ..utils.node_arrange import (
    ArrangeConfig,
    ALIGN_MODES,
    align_positions,
    distribute_positions,
    get_align_targets,
    layered_positions,
    walk_shaders,
)


def IsCoronaMaterial(material: c4d.BaseMaterial) -> bool:
    """Check if the material is a Corona material.

    Args:
        material: The material to check.

    Returns:
        True when the material type is a valid Corona material.
    """
    return isinstance(material, c4d.BaseMaterial) and material.GetType() in ID_VALID_MATERIALS


class ArrangeHelper:
    """Auto-arrange, align and inspect Corona node editor widgets.

    Example:
        >>> helper = ArrangeHelper(material)
        >>> helper.Arrange()          # 分层流向布局（需材质已在节点编辑器中打开过）
        >>> helper.Align("top")       # 对齐视图中的活动节点
    """

    # Corona 位置使用局部单位空间（默认节点宽度为 1），默认间距按节点宽度倍数给出
    DEFAULT_CONFIG: ArrangeConfig = ArrangeConfig(
        spacing_x=2.4, spacing_y=1.6, start_x=0.0, start_y=0.0,
        orphan_offset_x=-32.0, orphan_spacing_y=1.6,
    )

    def __init__(self, material: c4d.BaseMaterial, doc: c4d.documents.BaseDocument = None):
        """
        Args:
            material: The host Corona material.
            doc: The document owning the material, defaults to the material document.
        """
        if not IsCoronaMaterial(material):
            raise ValueError("This is not a Corona Material")
        self.material: c4d.BaseMaterial = material
        self.doc: c4d.documents.BaseDocument = doc or material.GetDocument() or c4d.documents.GetActiveDocument()

    # =============================================
    # 视图与控件
    # =============================================

    @staticmethod
    def GetViews(doc: c4d.documents.BaseDocument = None) -> list[c4d.BaseList2D]:
        """Get all Corona node editor views stored in the document.

        Args:
            doc: The document to inspect, defaults to the active document.

        Returns:
            The list of view nodes (may be empty when no editor was opened yet).
        """
        if doc is None:
            doc = c4d.documents.GetActiveDocument()
        if doc is None:
            return []
        hook = doc.FindSceneHook(CORONA_STR_NODEMATERIALSHOOK)
        if hook is None:
            return []
        for info in hook.GetBranchInfo():
            if info.get("id") == CORONA_NODESYSTEM_VIEW_BRANCH:
                head = info.get("head")
                return list(head.GetChildren()) if head is not None else []
        return []

    @staticmethod
    def GetWidgets(view: c4d.BaseList2D) -> list[c4d.BaseList2D]:
        """Get the node widgets stored under one view.

        Args:
            view: A view node returned by :meth:`GetViews`.

        Returns:
            The widget nodes of the view.
        """
        if view is None:
            return []
        return list(view.GetChildren())

    @staticmethod
    def GetWidgetNode(widget: c4d.BaseList2D) -> Optional[c4d.BaseList2D]:
        """Get the document node (material or shader) linked by a widget.

        Args:
            widget: A widget node under a view.

        Returns:
            The linked material or shader, None when unavailable.
        """
        if widget is None:
            return None
        try:
            return widget[CORONA_NODESYSTEM_NODE_LINK]
        except Exception:
            return None

    @staticmethod
    def GetWidgetPosition(widget: c4d.BaseList2D) -> Optional[c4d.Vector]:
        """Read the stored position of a widget in local unit space.

        Args:
            widget: A widget node under a view.

        Returns:
            The position vector, None when unavailable.
        """
        if widget is None:
            return None
        try:
            return c4d.Vector(
                float(widget[CORONA_NODESYSTEM_NODE_POS_X]),
                float(widget[CORONA_NODESYSTEM_NODE_POS_Y]),
                0.0,
            )
        except Exception:
            return None

    @staticmethod
    def SetWidgetPosition(widget: c4d.BaseList2D, pos: c4d.Vector) -> bool:
        """Write the position of a widget in local unit space.

        Args:
            widget: A widget node under a view.
            pos: The position vector to store.

        Returns:
            True when the position was written.
        """
        if widget is None:
            return False
        try:
            widget[CORONA_NODESYSTEM_NODE_POS_X] = float(pos.x)
            widget[CORONA_NODESYSTEM_NODE_POS_Y] = float(pos.y)
            return True
        except Exception:
            return False

    @staticmethod
    def SetWidgetHidePreview(widget: c4d.BaseList2D, hide: bool = True) -> bool:
        """Hide or show the preview sphere of a widget.

        Args:
            widget: A widget node under a view.
            hide: True to hide the preview.

        Returns:
            True when the flag was written.
        """
        if widget is None:
            return False
        try:
            widget[CORONA_NODESYSTEM_NODE_HIDE_PREVIEW] = bool(hide)
            return True
        except Exception:
            return False

    @staticmethod
    def SetWidgetHideBody(widget: c4d.BaseList2D, hide: bool = True) -> bool:
        """Hide or show the body with ports of a widget.

        Args:
            widget: A widget node under a view.
            hide: True to hide the body.

        Returns:
            True when the flag was written.
        """
        if widget is None:
            return False
        try:
            widget[CORONA_NODESYSTEM_NODE_HIDE_BODY] = bool(hide)
            return True
        except Exception:
            return False

    @staticmethod
    def IsWidgetHidden(widget: c4d.BaseList2D) -> Optional[bool]:
        """Check if a widget was removed from its view (hidden).

        Args:
            widget: A widget node under a view.

        Returns:
            The hidden state, None when unavailable.
        """
        if widget is None:
            return None
        try:
            return bool(widget[CORONA_NODESYSTEM_NODE_HIDDEN])
        except Exception:
            return None

    # =============================================
    # 材质级操作
    # =============================================

    def GetNodes(self) -> list[c4d.BaseList2D]:
        """Get the material root node plus all its shaders.

        Returns:
            The material first, then every shader in its shader tree.
        """
        return [self.material] + walk_shaders(self.material.GetFirstShader())

    def _node_guid_map(self) -> dict:
        """Build a GUID -> node mapping of all material nodes.

        C4D 每次调用返回新的 Python 包装，跨列表匹配必须用 GUID。
        """
        guids: dict = {}
        for node in self.GetNodes():
            try:
                guids.setdefault(node.GetGUID(), node)
            except Exception:
                continue
        return guids

    def FindView(self) -> Optional[c4d.BaseList2D]:
        """Find the first view containing a widget of this material.

        Returns:
            The view node, None when the material was never opened in the editor.
        """
        guids = self._node_guid_map()
        for view in self.GetViews(self.doc):
            for widget in self.GetWidgets(view):
                node = self.GetWidgetNode(widget)
                if node is None:
                    continue
                try:
                    if node.GetGUID() in guids:
                        return view
                except Exception:
                    continue
        return None

    def FindWidget(self, node: c4d.BaseList2D) -> Optional[c4d.BaseList2D]:
        """Find the widget representing one node of this material.

        Args:
            node: The material or one of its shaders.

        Returns:
            The widget node, None when not present in any view.
        """
        try:
            target_guid = node.GetGUID()
        except Exception:
            return None
        for view in self.GetViews(self.doc):
            for widget in self.GetWidgets(view):
                linked = self.GetWidgetNode(widget)
                if linked is None:
                    continue
                try:
                    if linked.GetGUID() == target_guid or linked == node:
                        return widget
                except Exception:
                    continue
        return None

    def GetActiveWidgets(self, view: c4d.BaseList2D = None) -> list[c4d.BaseList2D]:
        """Get widgets flagged active in a view.

        Corona 会把活动节点重排到视图子列表开头，此处按 BIT_ACTIVE 过滤。

        Args:
            view: The view to scan, defaults to the material view.

        Returns:
            The active widget nodes.
        """
        if view is None:
            view = self.FindView()
        if view is None:
            return []
        return [w for w in self.GetWidgets(view) if w.GetBit(c4d.BIT_ACTIVE)]

    def Arrange(self, config: ArrangeConfig = None) -> tuple[int, int]:
        """Apply a layered flow layout to the widgets of this material.

        材质节点为根（最右），输入侧逐层向左；没有对应控件的节点被跳过。

        Args:
            config: Layout parameters in local unit space,
                defaults to :attr:`DEFAULT_CONFIG`.

        Returns:
            (写入位置的控件数, 材质节点总数)
        """
        nodes = self.GetNodes()
        view = self.FindView()
        if view is None:
            return 0, len(nodes)

        # GUID 映射必须与 nodes 同源构建，保证 id() 键一致
        guids: dict = {}
        for node in nodes:
            try:
                guids.setdefault(node.GetGUID(), node)
            except Exception:
                continue
        # 只对视图中有控件的节点布局，控件与节点按 GUID 匹配
        widget_of: dict[int, c4d.BaseList2D] = {}
        for widget in self.GetWidgets(view):
            linked = self.GetWidgetNode(widget)
            if linked is None:
                continue
            try:
                target = guids.get(linked.GetGUID())
            except Exception:
                target = None
            if target is not None:
                widget_of[id(target)] = widget

        ordered_nodes = [n for n in nodes if id(n) in widget_of]
        order = {id(n): i for i, n in enumerate(nodes)}
        placements = layered_positions(ordered_nodes, id(self.material), config or self.DEFAULT_CONFIG, order)

        written = 0
        for node in ordered_nodes:
            pos = placements.get(id(node))
            if pos is not None and self.SetWidgetPosition(widget_of[id(node)], pos):
                written += 1
        c4d.EventAdd()
        return written, len(nodes)

    def Align(self, mode: str = "left", widgets: list[c4d.BaseList2D] = None) -> int:
        """Align widgets along one axis, active widgets first, all as fallback.

        Args:
            mode: One of :data:`ALIGN_MODES`.
            widgets: Explicit widget list, defaults to active or all widgets of the material view.

        Returns:
            The number of updated widgets.
        """
        if mode not in ALIGN_MODES:
            raise ValueError(f"Unknown align mode: {mode}")
        view = self.FindView()
        if view is None:
            return 0
        all_widgets = self.GetWidgets(view)
        targets = get_align_targets(all_widgets, widgets, lambda w: w.GetBit(c4d.BIT_ACTIVE))
        positions = {id(w): p for w in targets if (p := self.GetWidgetPosition(w)) is not None}
        if len(positions) < 2:
            return 0
        aligned = align_positions(positions, mode)
        updated = 0
        for widget in targets:
            pos = aligned.get(id(widget))
            if pos is not None and self.SetWidgetPosition(widget, pos):
                updated += 1
        if updated:
            c4d.EventAdd()
        return updated

    def Distribute(self, axis: str = "y", widgets: list[c4d.BaseList2D] = None, spacing: float = None) -> int:
        """Distribute widgets evenly along an axis, active widgets first.

        Args:
            axis: "x" or "y".
            widgets: Explicit widget list, defaults to active or all widgets of the material view.
            spacing: Optional fixed gap, defaults to spanning the current range.

        Returns:
            The number of updated widgets.
        """
        view = self.FindView()
        if view is None:
            return 0
        all_widgets = self.GetWidgets(view)
        targets = get_align_targets(all_widgets, widgets, lambda w: w.GetBit(c4d.BIT_ACTIVE))
        positions = {id(w): p for w in targets if (p := self.GetWidgetPosition(w)) is not None}
        if len(positions) < 3:
            return 0
        distributed = distribute_positions(positions, axis, spacing)
        updated = 0
        for widget in targets:
            pos = distributed.get(id(widget))
            if pos is not None and self.SetWidgetPosition(widget, pos):
                updated += 1
        if updated:
            c4d.EventAdd()
        return updated


# =============================================
# 模块级便捷函数
# =============================================

def ArrangeMaterial(material: c4d.BaseMaterial, config: ArrangeConfig = None) -> tuple[int, int]:
    """Arrange all nodes of a Corona material with one call.

    Args:
        material: The Corona material to arrange.
        config: Layout parameters in local unit space.

    Returns:
        (写入位置的控件数, 材质节点总数)，材质未打开过节点编辑器时为 (0, n)。

    Example:
        >>> import Renderer
        >>> Renderer.Corona.ArrangeMaterial(mat)
        (5, 6)
    """
    return ArrangeHelper(material).Arrange(config)


def AlignMaterial(material: c4d.BaseMaterial, mode: str = "left") -> int:
    """Align nodes of a Corona material with one call.

    Args:
        material: The Corona material to align.
        mode: One of :data:`ALIGN_MODES`.

    Returns:
        The number of updated widgets.
    """
    return ArrangeHelper(material).Align(mode)


__all__ = [
    "ArrangeHelper",
    "ArrangeMaterial",
    "AlignMaterial",
    "IsCoronaMaterial",
]
