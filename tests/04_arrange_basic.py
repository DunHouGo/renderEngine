# -*- coding: utf-8 -*-
"""
Arrange / Align 集成测试（c4dpy 运行）。

验证内容：
  1. Octane：分层布局写入与读回、对齐、等间距分布、孤立节点处理
  2. Octane：打开节点编辑器并触发 99011 后坐标是否保留（探针补测）
  3. Corona：无视图时优雅返回；打开 Corona 节点编辑器后真实控件的读写与排列（探针补测）

运行：
  "C:\\Program Files\\Maxon Cinema 4D 2026\\c4dpy.exe" tests/04_arrange_basic.py
结果写入 tests/_arrange_result.json（probe 段由 MessageData 在主循环中补写）。
"""

import sys
sys.path.insert(0, r"E:\Boghma\boghma hub\libs")

import c4d
import json
import time

import Renderer
from Renderer import Octane, Corona
from Renderer.utils.node_arrange import build_children_map

OUT = r"E:\Boghma\boghma hub\libs\Renderer\tests\_arrange_result.json"

# MessageData 探针状态
PROBE_ID = 1063421  # 临时测试 ID，仅本脚本使用
PROBE = {"phase": 0, "t0": 0.0, "result": {}}


def make_octane_scene(doc):
    """创建一个 OC universal 材质：两个通道贴图 + 一个孤立 shader，并赋予可区分名称。"""
    mat = c4d.BaseMaterial(1029501)
    if mat is None:
        return None, None
    doc.InsertMaterial(mat)

    img1 = c4d.BaseShader(1029509)  # ImageTexture
    img2 = c4d.BaseShader(1029509)
    orphan = c4d.BaseShader(1029509)
    img1.SetName("T_DIFF")
    img2.SetName("T_SPEC")
    orphan.SetName("T_ORPHAN")
    for sh in (img1, img2, orphan):
        mat.InsertShader(sh)
    mat[c4d.OCT_MATERIAL_DIFFUSE_LINK] = img1
    mat[c4d.OCT_MATERIAL_SPECULAR_LINK] = img2
    mat.Update(True, True)

    helper = Octane.ArrangeHelper(mat, doc)
    nodes = helper.GetNodes()
    # 拓扑诊断：列出材质容器解析到的子节点名称
    children = build_children_map(nodes)
    diag = {"children_of_mat": [n.GetName() for n in children[id(mat)]]}
    return mat, [img1, img2, orphan], helper, diag


def test_octane(doc, result):
    """数据级验证 OC 的排列、对齐与分布（全部 trigger=False）。"""
    mat, shaders, helper, diag = make_octane_scene(doc)
    info = dict(diag)
    if mat is None:
        info["error"] = "cannot create octane material"
        result["octane"] = info
        return

    # 1. 分层布局：img1/img2 在同一层（x 相同），孤立节点在更左侧
    written, total = helper.Arrange(trigger=False)
    info["arrange"] = {"written": written, "total": total}
    pos = [helper.GetNodePosition(s) for s in shaders]
    info["positions"] = [str(p) for p in pos]
    info["layers_ok"] = pos[0].x == pos[1].x and pos[2].x < pos[0].x

    # 2. 手动摆乱后对齐 top（显式传节点）
    helper.SetNodePosition(shaders[0], c4d.Vector(100, -500, 0))
    helper.SetNodePosition(shaders[1], c4d.Vector(300, 400, 0))
    n = helper.Align("top", [shaders[0], shaders[1]], trigger=False)
    info["align_top"] = {
        "updated": n,
        "y0": helper.GetNodePosition(shaders[0]).y,
        "y1": helper.GetNodePosition(shaders[1]).y,
        "ok": helper.GetNodePosition(shaders[0]).y == helper.GetNodePosition(shaders[1]).y,
    }

    # 3. 分布 y：三节点按固定间距排列
    helper.SetNodePosition(shaders[0], c4d.Vector(0, 0, 0))
    helper.SetNodePosition(shaders[1], c4d.Vector(0, 700, 0))
    helper.SetNodePosition(shaders[2], c4d.Vector(0, 3000, 0))
    n = helper.Distribute("y", shaders, spacing=250.0, trigger=False)
    ys = [helper.GetNodePosition(s).y for s in shaders]
    info["distribute_y"] = {"updated": n, "ys": ys, "ok": ys == [0.0, 250.0, 500.0]}

    # 4. 便捷入口（会触发刷新）
    tr = Octane.Material(mat)
    info["helper_arrange_nodes"] = tr.ArrangeNodes()
    info["module_align"] = Octane.AlignMaterial(mat, "left")

    PROBE["octane_mat"] = mat
    PROBE["octane_helper"] = helper
    result["octane"] = info


def make_corona_scene(doc):
    """创建 Corona 物理材质：BaseColor 贴图 + Bump 贴图 + 一个孤立 shader。"""
    mat = c4d.BaseMaterial(1056306)
    if mat is None:
        return None, None
    doc.InsertMaterial(mat)
    bmp1 = c4d.BaseShader(1036473)
    bmp2 = c4d.BaseShader(1036473)
    orphan = c4d.BaseShader(1036473)
    bmp1.SetName("C_BASE")
    bmp2.SetName("C_BUMP")
    orphan.SetName("C_ORPHAN")
    for sh in (bmp1, bmp2, orphan):
        mat.InsertShader(sh)
    mat[c4d.CORONA_PHYSICAL_MATERIAL_BASE_COLOR_TEXTURE] = bmp1
    mat[c4d.CORONA_PHYSICAL_MATERIAL_BASE_BUMPMAPPING_TEXTURE] = bmp2
    mat.Update(True, True)
    return mat, [bmp1, bmp2, orphan]


def test_corona_graceful(doc, result):
    """无视图时的优雅路径：应返回 (0, n) 而不报错。"""
    info = {}
    mat, shaders = make_corona_scene(doc)
    if mat is None:
        info["error"] = "cannot create corona material"
        result["corona_graceful"] = info
        return

    helper = Corona.ArrangeHelper(mat, doc)
    info["arrange_no_view"] = helper.Arrange()
    info["views_before"] = len(Corona.ArrangeHelper.GetViews(doc))
    tr = Corona.Material(mat)
    info["helper_arrange_nodes"] = tr.ArrangeNodes()
    result["corona_graceful"] = info

    PROBE["corona_mat"] = mat
    PROBE["corona_helper"] = helper
    PROBE["corona_shaders"] = shaders


def probe_tick():
    """MessageData 状态机：读回 OC 触发后坐标 -> 轮询 Corona 视图并做控件验证。"""
    result = PROBE["result"]
    if PROBE["phase"] == 0:
        # OC NE 已在脚本中打开：读回触发自动排列后的标记坐标
        PROBE["phase"] = 1
        PROBE["t0"] = time.time()
        helper = PROBE["octane_helper"]
        node = helper.GetNodes()[1]
        result["oc_pos_after_trigger"] = str(helper.GetNodePosition(node))
        result["oc_pos_marker_ok"] = helper.GetNodePosition(node) == c4d.Vector(123.0, 456.0, 0)
        _flush(result)
    elif PROBE["phase"] == 1:
        # 轮询等待 Corona 视图生成（NE 对话框异步初始化），最多等 20 秒
        helper = PROBE["corona_helper"]
        views = Corona.ArrangeHelper.GetViews(helper.doc)
        if not views and time.time() - PROBE["t0"] < 20:
            return
        PROBE["phase"] = 3
        info = {"views_after": len(views)}
        written, total = helper.Arrange()
        info["arrange"] = {"written": written, "total": total}
        view = helper.FindView()
        info["view_found"] = view is not None
        widgets = helper.GetWidgets(view) if view else []
        info["num_widgets"] = len(widgets)
        wl = []
        for w in widgets:
            node = helper.GetWidgetNode(w)
            wl.append({
                "widget": w.GetName(),
                "node": node.GetName() if node else None,
                "node_type": node.GetType() if node else None,
                "active": bool(w.GetBit(c4d.BIT_ACTIVE)),
                "pos": str(helper.GetWidgetPosition(w)),
                "hidden": helper.IsWidgetHidden(w),
            })
        info["widgets"] = wl
        # 对齐验证：把两个通道贴图 y 对齐
        shaders = PROBE["corona_shaders"]
        w1, w2 = helper.FindWidget(shaders[0]), helper.FindWidget(shaders[1])
        if w1 and w2:
            helper.SetWidgetPosition(w1, c4d.Vector(1.0, 5.0, 0))
            helper.SetWidgetPosition(w2, c4d.Vector(3.0, -7.0, 0))
            info["align_top"] = helper.Align("top", [w1, w2])
            info["after_w1"] = str(helper.GetWidgetPosition(w1))
            info["after_w2"] = str(helper.GetWidgetPosition(w2))
            info["hide_preview"] = helper.SetWidgetHidePreview(w1, True)
        result["corona_ne"] = info
        _flush(result)
        print("ARRANGE TEST PROBE DONE")


def _flush(result):
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1, default=str)


class ArrangeProbe(c4d.plugins.MessageData):
    """临时 MessageData：驱动延迟探针。"""

    def CoreMessage(self, mid, msg):
        try:
            if mid == PROBE_ID and PROBE["phase"] in (0, 1):
                probe_tick()
                if PROBE["phase"] in (0, 1):
                    c4d.SpecialEventAdd(PROBE_ID)
        except Exception:
            import traceback
            PROBE["result"]["probe_fatal"] = traceback.format_exc()
            _flush(PROBE["result"])
        return True


def register_probe():
    try:
        c4d.plugins.RegisterMessagePlugin(PROBE_ID, "ArrangeProbe", 0, ArrangeProbe())
    except Exception:
        pass


def main():
    doc = c4d.documents.GetActiveDocument()
    result = {}
    doc.StartUndo()
    try:
        test_octane(doc, result)
        test_corona_graceful(doc, result)
        # 打开两个节点编辑器（modeless 对话框保活进程，视图由事件循环生成）
        oc_mat = PROBE.get("octane_mat")
        if oc_mat is not None:
            doc.SetActiveMaterial(oc_mat)
            try:
                # 写入标记坐标并触发自动排列，探针阶段读回验证是否保留
                PROBE["octane_helper"].SetNodePosition(PROBE["octane_helper"].GetNodes()[1], c4d.Vector(123.0, 456.0, 0))
                result["oc_trigger_written"] = PROBE["octane_helper"].TriggerAutoArrange()
                Octane.OpenNodeEditor(oc_mat)
            except Exception as e:
                result["oc_ne_open_error"] = str(e)
        corona_mat = PROBE.get("corona_mat")
        if corona_mat is not None:
            doc.SetActiveMaterial(corona_mat)
            c4d.CallCommand(1040908)  # Corona: Node material editor...
        register_probe()
        c4d.SpecialEventAdd(PROBE_ID)
        _flush(result)
        print("ARRANGE TEST PHASE1 OK")
    except Exception:
        import traceback
        result["fatal"] = traceback.format_exc()
        _flush(result)
    finally:
        doc.EndUndo()


if __name__ == "__main__":
    main()
