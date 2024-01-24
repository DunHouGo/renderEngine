# Renderer
> Older version called **renderEngine** had been move to versions folder, if you still intrested.

Wrapper class for the maxon and c4d API of popular render engine for Cinema 4D.

Intended for more user-friendly manipulation of node materials with the new maxon.GraphNode model.And also with Octane Node Material model.

Provide helper class for convenient access AOV , Material , Scene Object(Object/Tag/Light/...) in Cinema 4D popular renderer.

Happy Rendering and Scpriting!

## Supported Renderer
- Octane
- Node Materials with the new GraphNode model
- Redshift ( Only Node Material for Material Helper)
- Arnold ( Only Node Material for Material Helper)
- Waiting for more...

## About Boghma

Boghma is a open community for c4d developers, we are trying to make it easier for everyone to create plugins and share them.

This library is also included in [Boghma](https://community.boghma.com/) python library.

You can install our free plugin [Boghma Plugin Manager](https://github.com/DunHouGo/Boghma-Plugin-HUB) and install any plugin you want, this library will be automatically installed or updated.

If you want to share your free plugins or libaray, please join us in [Join Us](https://flowus.cn/boghma/share/96035b74-6205-4e6c-b49c-65de7d1e2e62).

```
All the boghma plugins and boghma library are personal FREE.
```

## Installation

1. (**Recommend**) Download [Boghma Plugin Manager](https://github.com/DunHouGo/Boghma-Plugin-HUB) and install any plugin, the boghma lib will auto installed or updated.
2. Download the source code and import it to your Cinema 4D.
   
# Limit
- For some reasons, AddShader-like methods(maxon.GraphModelInterface.AddChild) will add the node in the center of the graph, if we call those methods on exsited material, it will return a mess graph, you can call Renderer.ArrangeAll() after.
- Material(except Octane) helper only support material with the new GraphNode model(Node Material after R26)
- Due to Octane use his Custom UserArea UI base on old layer system, and didn't support python, we can only modify Octane materials in material level, but can not interactive with selections in octane node editor.
- Also Octane materials didn't have a "port" or "wire" context, we can not use all those methods as same as NodeGraghHelper.
- Arnold mask tag SetPrameter has a refresh bug.


# Quick Intro

```python

import c4d
import maxon
from Renderer import Redshift, EasyTransaction, TextureHelper
from pprint import pprint

# Create a TextureHelper instance
# 创建一个 TextureHelper 实例
tex_helper: TextureHelper = TextureHelper()

# Get the url with given asset id
# 获取给定资产ID的URL
# "si-v1_fingerprints_02_15cm.png" with AssetId : file_fa9c42774dd05049
disp: maxon.Url = tex_helper.GetAssetUrl("file_fa9c42774dd05049")

def HowToUse():
    """
    How to reate a redshift material and modify the gragh with EasyTransaction.
    """

    # Create Redshift Node Material instance, if no material filled, we create a new STD material
    # 创建一个Redshift节点材质实例,如果没有材质传入，创建新的STD材质
    material: c4d.BaseMaterial = Redshift.Material("MyMaterial")

    # Use EasyTransaction to modify the graph
    # 使用EasyTransaction来修改材质
    with EasyTransaction(material) as tr:
    
        # the attribute #tr is the instance of Redshift.MaterialHelper, 
        # we got it with just apply to the #material to the EasyTransaction
        # it will inherit from NodeGraghHelper class
        # 属性tr是Redshift.MaterialHelper的实例，通过将材质赋予EasyTransaction获得，继承自NodeGraghHelper

        # Use Redshift.MaterialHelper methods : add a texture + displacement to the Output node
        # 使用Redshift.MaterialHelper中的方法: 添加图片+置换节点到Output节点
        tr.AddDisplacementTree(filepath = disp, shadername = "DISP")

        # Use NodeGraghHelper methods： get the Output(endNode)
        # 使用NodeGraghHelper中的方法: 获取输出节点
        output = tr.GetOutput()
        print(f"{output = }")

        # Insert the material to the document
        # 导入材质(来自Redshift MaterialHelper)
        tr.InsertMaterial()

    # Auto apply GraphTransaction.Commit() to the graph
    # 退出with后, 自动执行GraphTransaction.Commit()

```

# Examples
- [__Material Example__](./tests/01_material_basic.py)
- [__AOV Example__](./tests/02_aov_basic.py)
- [__Scene Example__](./tests/03_scene_basic.py)


# Class Presentation

Renderer
- NodeGraghHelper
- TextureHelper
- EasyTransaction
- Redshift
  - AOV
  - Material
  - Scene
- Octane
  - AOV
  - Material
  - Scene
- Arnold
  - AOV
  - Material
  - Scene
- utils
  - NodeGraghHelper
  - TextureHelper
  - EasyTransaction
- constants
