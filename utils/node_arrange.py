# -*- coding: utf-8 -*-
"""Shared layout engine for classic shader graph auto-arrange and align.

Used by the Octane and Corona arrange helpers. All positions are plain
:c4d.class:`c4d.Vector` values so each engine decides its own unit scale
(Octane stores pixel like vectors, Corona stores node width units).
"""

import c4d
from dataclasses import dataclass
from typing import Callable, Optional

# =========================================================
# Globals & Constants
# =========================================================

# 对齐模式：left/right 对齐 X，top/bottom 对齐 Y，center_x/center_y 对齐到平均值
ALIGN_MODES: tuple[str, ...] = (
    "left", "right", "top", "bottom", "center_x", "center_y",
)


@dataclass
class ArrangeConfig:
    """Layout parameters for the layered flow layout.

    根节点（材质输出）在最右，输入侧逐层向左展开。
    """
    spacing_x: float = 250.0     # 层间距（水平）
    spacing_y: float = 200.0     # 同层节点间距（垂直）
    start_x: float = 0.0         # 布局起点（最深层输入一侧）
    start_y: float = 0.0         # 垂直中点
    orphan_offset_x: float = -4000.0   # 孤立节点相对 start_x 的偏移
    orphan_spacing_y: float = 200.0    # 孤立节点垂直间距


# =========================================================
# Topology
# =========================================================

def walk_shaders(shader: c4d.BaseShader) -> list[c4d.BaseShader]:
    """Iteratively collect a shader tree into a flat list.

    Args:
        shader: The first shader of a material or a subtree root.

    Returns:
        All shaders in the tree, depth first.

    Example:
        >>> walk_shaders(material.GetFirstShader())
        [shader1, shader2, ...]
    """
    result: list[c4d.BaseShader] = []
    stack: list[c4d.BaseShader] = [shader] if shader is not None else []
    while stack:
        current = stack.pop()
        if current is None:
            continue
        result.append(current)
        # 先压 next 再压 down，保证输出顺序接近深度优先
        if current.GetNext() is not None:
            stack.append(current.GetNext())
        if current.GetDown() is not None:
            stack.append(current.GetDown())
    return result


def collect_child_shaders(host: c4d.BaseList2D) -> list[c4d.BaseShader]:
    """Scan a node's BaseContainer and collect directly referenced shaders.

    容器返回的 BaseShader 与 walk 得到的对象可能是不同 Python 包装，
    调用方需要用 (name, type) 双键兜底匹配到规范对象。

    Args:
        host: A material or shader whose container is scanned.

    Returns:
        Shaders directly referenced by the host (deduplicated).
    """
    children: list[c4d.BaseShader] = []

    def _collect(bc: c4d.BaseContainer) -> None:
        if bc is None:
            return
        # 必须用 Python 原生迭代，C++ 迭代器拿不到内嵌容器
        for _id, value in bc:
            if isinstance(value, c4d.BaseContainer):
                _collect(value)
            elif isinstance(value, c4d.BaseShader):
                if not any(value is c for c in children):
                    children.append(value)

    _collect(host.GetDataInstance())
    return children


def build_children_map(nodes: list[c4d.BaseList2D]) -> dict[int, list[c4d.BaseList2D]]:
    """Build a parent -> children adjacency map over the given nodes.

    Args:
        nodes: All graph nodes, the material root first.

    Returns:
        Mapping of ``id(node)`` to the list of directly connected input nodes.
        只保留 nodes 集合内的引用，共享 shader 等外部节点会被忽略。
    """
    # 规范对象集合，容器返回的引用通过 GUID 或 (name, type) 双键解析
    canonical: list[c4d.BaseList2D] = list(nodes)
    by_guid: dict[int, c4d.BaseList2D] = {}
    by_key: dict[tuple, c4d.BaseList2D] = {}
    for n in canonical:
        try:
            by_guid.setdefault(n.GetGUID(), n)
        except Exception:
            pass
        key = (n.GetName(), n.GetType())
        if key not in by_key:
            by_key[key] = n

    def resolve(ref: c4d.BaseList2D) -> Optional[c4d.BaseList2D]:
        try:
            node = by_guid.get(ref.GetGUID())
            if node is not None:
                return node
        except Exception:
            pass
        return by_key.get((ref.GetName(), ref.GetType()))

    children: dict[int, list[c4d.BaseList2D]] = {id(n): [] for n in canonical}
    for node in canonical:
        for ref in collect_child_shaders(node):
            target = resolve(ref)
            # 忽略自环与集合外的节点
            if target is None or target is node:
                continue
            if not any(target is c for c in children[id(node)]):
                children[id(node)].append(target)
    return children


def compute_layers(root_id: int, children: dict[int, list]) -> dict[int, int]:
    """Assign each node a flow layer via reverse BFS from the root.

    Shared nodes are pushed to their deepest layer to reduce wire crossing.

    Args:
        root_id: ``id()`` of the root node (layer 0).
        children: Adjacency map as returned by :func:`build_children_map`.

    Returns:
        Mapping of ``id(node)`` to its layer depth, unknown nodes absent.
    """
    layer: dict[int, int] = {root_id: 0}
    changed = True
    while changed:
        changed = False
        for parent_id, kids in children.items():
            parent_layer = layer.get(parent_id, -1)
            if parent_layer < 0:
                continue
            for kid in kids:
                kid_id = id(kid)
                if layer.get(kid_id, -1) < parent_layer + 1:
                    layer[kid_id] = parent_layer + 1
                    changed = True
    return layer


# =========================================================
# Layout
# =========================================================

def layered_positions(
    nodes: list[c4d.BaseList2D],
    root_id: int,
    config: ArrangeConfig = None,
    order: dict[int, int] = None,
) -> dict[int, c4d.Vector]:
    """Compute a layered flow layout, root on the right edge.

    同层节点 x 相同并垂直居中；未连到根的孤立节点排在左侧远处。

    Args:
        nodes: All graph nodes, the material root first.
        root_id: ``id()`` of the root node.
        config: Layout parameters, defaults to :class:`ArrangeConfig`.
        order: Optional ``id(node) -> index`` used to sort nodes inside a layer.

    Returns:
        Mapping of ``id(node)`` to its new position vector.
    """
    cfg = config if config is not None else ArrangeConfig()
    children = build_children_map(nodes)
    layer = compute_layers(root_id, children)

    if order is None:
        order = {id(n): i for i, n in enumerate(nodes)}

    by_layer: dict[int, list] = {}
    orphans: list = []
    for node in nodes:
        depth = layer.get(id(node))
        if depth is None:
            # 根节点永远参与布局，其余未连到根的视为孤立节点
            if id(node) != root_id:
                orphans.append(node)
            continue
        by_layer.setdefault(depth, []).append(node)

    max_layer = max(by_layer) if by_layer else 0
    placements: dict[int, c4d.Vector] = {}
    for depth, layer_nodes in by_layer.items():
        layer_nodes.sort(key=lambda n: order.get(id(n), 0))
        count = len(layer_nodes)
        for i, node in enumerate(layer_nodes):
            x = cfg.start_x + (max_layer - depth) * cfg.spacing_x
            y = cfg.start_y + (i - (count - 1) * 0.5) * cfg.spacing_y
            placements[id(node)] = c4d.Vector(x, y, 0.0)

    for i, node in enumerate(orphans):
        x = cfg.start_x + cfg.orphan_offset_x
        y = cfg.start_y + i * cfg.orphan_spacing_y
        placements[id(node)] = c4d.Vector(x, y, 0.0)

    return placements


# =========================================================
# Align & Distribute
# =========================================================

def align_positions(
    positions: dict[int, c4d.Vector], mode: str, spacing: float = 0.0
) -> dict[int, c4d.Vector]:
    """Align node positions along one axis.

    Args:
        positions: Current ``id(node) -> position`` mapping.
        mode: One of :data:`ALIGN_MODES`. top 表示最小 Y（节点编辑器 Y 向下）。
        spacing: Reserved for future use, currently ignored.

    Returns:
        A new mapping with aligned positions, input mapping untouched.
    """
    if not positions or mode not in ALIGN_MODES:
        return dict(positions or {})

    xs = [p.x for p in positions.values()]
    ys = [p.y for p in positions.values()]

    if mode == "left":
        target_x = min(xs)
    elif mode == "right":
        target_x = max(xs)
    elif mode == "center_x":
        target_x = (min(xs) + max(xs)) * 0.5
    elif mode == "top":
        target_y = min(ys)
    elif mode == "bottom":
        target_y = max(ys)
    else:  # center_y
        target_y = (min(ys) + max(ys)) * 0.5

    result: dict[int, c4d.Vector] = {}
    for key, pos in positions.items():
        if mode in ("left", "right", "center_x"):
            result[key] = c4d.Vector(target_x, pos.y, 0.0)
        else:
            result[key] = c4d.Vector(pos.x, target_y, 0.0)
    return result


def distribute_positions(
    positions: dict[int, c4d.Vector], axis: str, spacing: Optional[float] = None
) -> dict[int, c4d.Vector]:
    """Distribute nodes evenly along an axis.

    首尾节点保持不动，其余节点在两者之间按相等间距重排。
    当指定 spacing 时从最小坐标开始按固定间距排列。

    Args:
        positions: Current ``id(node) -> position`` mapping.
        axis: "x" or "y".
        spacing: Optional fixed gap instead of spanning the current range.

    Returns:
        A new mapping with distributed positions.
    """
    if not positions or axis not in ("x", "y"):
        return dict(positions or {})

    keys = sorted(positions, key=lambda k: positions[k].x if axis == "x" else positions[k].y)
    if len(keys) < 3:
        return dict(positions)

    coords = [positions[k].x if axis == "x" else positions[k].y for k in keys]
    result: dict[int, c4d.Vector] = {}
    if spacing is not None:
        start = min(coords)
        gaps = [start + i * spacing for i in range(len(keys))]
    else:
        first, last = coords[0], coords[-1]
        step = (last - first) / (len(keys) - 1)
        gaps = [first + i * step for i in range(len(keys))]

    for key, value in zip(keys, gaps):
        pos = positions[key]
        result[key] = c4d.Vector(value, pos.y, 0.0) if axis == "x" else c4d.Vector(pos.x, value, 0.0)
    return result


def get_align_targets(
    nodes: list[c4d.BaseList2D],
    explicit: Optional[list] = None,
    selector: Optional[Callable] = None,
) -> list[c4d.BaseList2D]:
    """Resolve which nodes an align/distribute call should operate on.

    优先使用显式传入的节点，其次 selector（通常检查 BIT_ACTIVE），
    都为空时回退到全部节点。C4D 每次调用会返回新的 Python 包装，
    身份匹配使用 GetGUID 加 (name, type) 双键兜底。

    Args:
        nodes: All candidate nodes.
        explicit: Explicitly provided target nodes.
        selector: Callable returning True for auto-selected nodes.

    Returns:
        The resolved target node list.
    """
    if explicit:
        known_guids: set = set()
        known_keys: set = set()
        for n in nodes:
            try:
                known_guids.add(n.GetGUID())
            except Exception:
                pass
            known_keys.add((n.GetName(), n.GetType()))
        picked: list[c4d.BaseList2D] = []
        for n in explicit:
            try:
                guid = n.GetGUID()
            except Exception:
                guid = None
            if guid in known_guids or (n.GetName(), n.GetType()) in known_keys:
                picked.append(n)
        return picked
    if selector is not None:
        picked = [n for n in nodes if selector(n)]
        if picked:
            return picked
    return list(nodes)
