# Renderer 用户指南

Renderer 是面向 Cinema 4D 的渲染器辅助库，用于统一处理常用渲染器的材质、节点、AOV 和场景对象。

## 功能分组

- `Redshift`：Redshift 材质、AOV 和场景操作。
- `Arnold`：Arnold 材质、AOV 和场景操作。
- `Vray`：V-Ray 材质和 AOV 操作。
- `CentiLeo`：CentiLeo 材质和 AOV 操作。
- `Octane`：Octane 材质、AOV、场景和节点排列操作。
- `Corona`：Corona 材质、AOV、场景和节点排列操作。
- `utils`：节点、材质、贴图、PBR 和节点排列辅助功能。
- `constants`：各渲染器的节点和端口常量。

## 常用参数

不同渲染器的辅助类参数会随操作类型变化，通常包括以下内容：

- 材质对象：指定要读取或修改的 Cinema 4D 材质。
- 节点对象：指定要连接、移动或读取的节点。
- 端口名称或 ID：指定节点上的输入或输出端口。
- 文件路径：指定纹理、PBR 贴图或场景资源的位置。
- 节点空间 ID：在需要时指定渲染器的节点空间。
- 排列方式：选择排列、对齐或等间距分布节点。

使用前请先确认对应渲染器已安装，并按照各模块提供的函数参数传入对象和资源。

## 交互说明

Renderer 不提供独立的窗口或面板。节点排列功能会直接修改材质节点编辑器中的节点位置；排列、对齐和分布操作由调用的函数决定。右键菜单、拖拽和节点编辑器选择仍由 Cinema 4D 原生界面处理。

## 打包文件

运行 `scripts/build_renderer_release.py` 后，会在上级 `dist` 文件夹生成 `Renderer.zip`。解压后使用压缩包内的 `Renderer` 文件夹。
