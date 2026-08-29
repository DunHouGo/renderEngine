# -*- coding: utf-8 -*-
"""
OC 材质节点自动排布工具 v3 (C4D 2025.3.3 + OC 2025.3)
====================================================
【完整功能】开着节点编辑器也能自动排布！

核心机制（已实测验证）：
  1. OC 节点位置存放在每个 shader 的 [99000][700] = Vector(x,y,0)
  2. 写入坐标后，触发材质隐藏参数 OCT_AUTO_ARRANGE=99011
     （对应节点编辑器右键菜单的 Auto-arrange）
     -> OC 会立即刷新【打开中的】节点编辑器，并保留 [99000] 里的坐标！
  3. 因此：写入自定义布局 + 触发 99011 = 开着编辑器也能看到自己的排布

布局：分层流向布局
  - 根节点（材质输出）在最右
  - 按信号流向反向分层（BFS），同层 x 相同、垂直居中
  - 共享节点取最深层，避免连线交叉
  - 孤立节点放左侧远处

用法：
  1. 选中 OC 材质（不选则处理全文档 OC 材质）
  2. 调 CONFIG 参数
  3. 运行 -> 节点编辑器（即使开着）自动显示新布局
  4. 想换成自己的排布逻辑：改 compute_layout / 或在 layered_layout 里改

⚠ 每次运行覆盖上次布局，建议先备份 .c4d。
"""

import c4d
from c4d import gui

# ============================================================
# OC 内部常量
# ============================================================
OCT_NE_SAVER = 99000       # 节点编辑器状态子容器
NG_POS = 700               # 节点位置 Vector(x, y, 0)
OCT_AUTO_ARRANGE = 99011   # OC 内置"自动排列"触发参数（刷新+重排）

# ============================================================
# 配置
# ============================================================
CONFIG = {
    "process_selected_only": False,   # True=只处理选中材质

    # 分层布局参数
    "spacing_x": 250.0,               # 层间距（水平）
    "spacing_y": 200.0,               # 同层节点间距（垂直）
    "start_x": 0.0,                   # 布局起点（最深层输入）
    "start_y": 0.0,                   # 垂直中点

    # 孤立节点（未连到材质输出）
    "orphan_offset_x": -4000.0,       # 相对 start_x 的 x
    "orphan_spacing_y": 200.0,

    # 刷新
    "trigger_refresh": True,          # 写入后触发 mat[99011]（开着编辑器也生效）

    # 调试
    "show_debug": False,              # True=打印拓扑分层/父子边
}


# ============================================================
# 基础工具
# ============================================================
def is_octane_material(mat):
    if mat is None:
        return False
    plug = c4d.plugins.FindPlugin(mat.GetType(), c4d.PLUGINTYPE_MATERIAL)
    if plug is None:
        return False
    fn = plug.GetFilename()
    return fn is not None and "c4doctane" in fn.lower()


def walk_shaders(sh, out):
    while sh:
        out.append(sh)
        walk_shaders(sh.GetDown(), out)
        sh = sh.GetNext()


def read_pos(atom):
    bc = atom.GetDataInstance()
    if bc is None:
        return None
    ng = bc.GetContainerInstance(OCT_NE_SAVER)
    if ng is None:
        return None
    return ng.GetVector(NG_POS)


def write_pos(atom, v):
    bc = atom.GetDataInstance()
    if bc is None:
        return False
    ng = bc.GetContainerInstance(OCT_NE_SAVER)
    if ng is None:
        return False
    ng.SetVector(NG_POS, v)
    return True


# ============================================================
# 拓扑解析
# ============================================================
def build_children_map(mat, shaders):
    """父节点 -> [直接输入节点]。容器返回的 BaseShader 与 walk 对象 id 不同，
    用 (name, type) 双键兜底匹配到规范对象。"""
    canonical_set = set(id(s) for s in shaders)
    name_key = {}
    for s in shaders:
        k = (s.GetName(), s.GetType())
        if k not in name_key:
            name_key[k] = s

    def resolve(ln):
        if id(ln) in canonical_set:
            return ln
        return name_key.get((ln.GetName(), ln.GetType()))

    nodes = [mat] + shaders
    children = {id(n): [] for n in nodes}

    def collect_from(parent, bc):
        if bc is None:
            return
        for _id, v in bc:                     # 必须用 Python 原生迭代
            if isinstance(v, c4d.BaseContainer):
                collect_from(parent, v)
            elif isinstance(v, c4d.BaseShader):
                target = resolve(v)
                if target is not None and target is not parent:
                    if not any(c is target for c in children[id(parent)]):
                        children[id(parent)].append(target)

    collect_from(mat, mat.GetDataInstance())
    for s in shaders:
        collect_from(s, s.GetDataInstance())
    return children


def compute_layers(root_id, children):
    """BFS 反向分层：root=0，输入逐层+1，共享节点取最深层。"""
    layer = {root_id: 0}
    changed = True
    while changed:
        changed = False
        for pid, kids in children.items():
            pl = layer.get(pid, -1)
            if pl < 0:
                continue
            for k in kids:
                if layer.get(id(k), -1) < pl + 1:
                    layer[id(k)] = pl + 1
                    changed = True
    return layer


# ============================================================
# 分层布局
# ============================================================
def layered_layout(mat, shaders, cfg, debug_out=None):
    nodes = [mat] + shaders
    children = build_children_map(mat, shaders)
    layer = compute_layers(id(mat), children)

    max_l = max(layer.values()) if layer else 0
    order = {id(mat): -1}
    for i, s in enumerate(shaders):
        order.setdefault(id(s), i)

    by_layer = {}
    orphans = []
    for n in nodes:
        L = layer.get(id(n))
        if L is None:
            if n is not mat:
                orphans.append(n)
            continue
        by_layer.setdefault(L, []).append(n)

    placements = {}
    for L, ns in by_layer.items():
        ns.sort(key=lambda n: order.get(id(n), 0))
        cnt = len(ns)
        for i, n in enumerate(ns):
            x = cfg["start_x"] + (max_l - L) * cfg["spacing_x"]
            y = cfg["start_y"] + (i - (cnt - 1) * 0.5) * cfg["spacing_y"]
            placements[id(n)] = c4d.Vector(x, y, 0.0)

    for i, n in enumerate(orphans):
        x = cfg["start_x"] + cfg["orphan_offset_x"]
        y = cfg["start_y"] + i * cfg["orphan_spacing_y"]
        placements[id(n)] = c4d.Vector(x, y, 0.0)

    if debug_out is not None:
        id_to_node = {id(n): n for n in nodes}
        debug_out.append("== 拓扑分层 (L0=材质输出) ==")
        for L in sorted(by_layer.keys()):
            names = [id_to_node[id(n)].GetName() or id_to_node[id(n)].GetTypeName()
                     for n in by_layer[L]]
            debug_out.append("  L%d: %s" % (L, names))
        if orphans:
            debug_out.append("  孤立: %s" %
                             [n.GetName() or n.GetTypeName() for n in orphans])
        debug_out.append("== 父子边 ==")
        for pid, kids in children.items():
            pname = id_to_node[pid].GetName() or id_to_node[pid].GetTypeName()
            knames = [(id_to_node[id(k)].GetName() or id_to_node[id(k)].GetTypeName())
                      for k in kids if id(k) in id_to_node]
            if knames:
                debug_out.append("  %s -> %s" % (pname, knames))

    return placements


# ============================================================
# 触发刷新（关键：开着编辑器也生效）
# ============================================================
def trigger_refresh(mat):
    """写入坐标后触发 OC 自动排列 -> 打开的节点编辑器立即重读 [99000]。"""
    try:
        mat[OCT_AUTO_ARRANGE] = 1
        c4d.EventAdd()
        return True
    except Exception:
        try:
            mat.SetParameter(c4d.DescID(OCT_AUTO_ARRANGE), True, c4d.DESCFLAGS_SET_0)
            c4d.EventAdd()
            return True
        except Exception:
            return False


# ============================================================
# 主流程
# ============================================================
def arrange_one_material(mat, cfg, debug_out=None):
    shaders = []
    walk_shaders(mat.GetFirstShader(), shaders)

    placements = layered_layout(mat, shaders, cfg, debug_out=debug_out)

    ok_shader = 0
    for n in shaders:
        p = placements.get(id(n))
        if p is not None and write_pos(n, p):
            ok_shader += 1

    ok_mat = 0
    mp = placements.get(id(mat))
    if mp is not None and write_pos(mat, mp):
        ok_mat = 1

    ok_refresh = 0
    if cfg.get("trigger_refresh", True) and trigger_refresh(mat):
        ok_refresh = 1

    return len(shaders), ok_shader, ok_mat, ok_refresh


def main():
    doc = c4d.documents.GetActiveDocument()
    if doc is None:
        return

    mats = doc.GetMaterials()
    if CONFIG["process_selected_only"]:
        target_mats = [m for m in mats if m.GetBit(c4d.BIT_ACTIVE) and is_octane_material(m)]
    else:
        target_mats = [m for m in mats if is_octane_material(m)]

    if not target_mats:
        gui.MessageDialog("没有找到 Octane 材质。")
        return

    summary = []
    debug_log = []
    for m in target_mats:
        n_nodes, ok_s, ok_m, ok_r = arrange_one_material(m, CONFIG,
                                                         debug_out=debug_log if CONFIG["show_debug"] else None)
        summary.append(
            "  %s: 节点 %d/%d, 材质 %d/1, 刷新%s" %
            (m.GetName(), ok_s, n_nodes, ok_m, "OK" if ok_r else "失败")
        )

    msg = "排布完成：\n%s\n\n节点编辑器（即使开着）应已显示新布局。" % "\n".join(summary)
    if debug_log:
        msg += "\n\n== 调试信息 ==\n" + "\n".join(debug_log)
    print(msg)
    gui.MessageDialog(msg)


if __name__ == "__main__":
    main()
