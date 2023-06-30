# -*- coding: utf-8 -*-  

# Maxon Cinema 4D version 2023.2.1

###  ==========  Copyrights  ==========  ###

"""
    Copyright [2023] [DunHouGo]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

###  ==========  Author INFO  ==========  ###
__author__ = "DunHouGo"
__copyright__ = "Copyright (C) 2023 Boghma"
__license__ = "Apache-2.0 License"
__version__ = "2023.2.1"
###  ==========  Import Libs  ==========  ###
from typing import Optional
import c4d
import os
import sys
import maxon
from importlib import reload
# import custom redshift node material API
#path = r"H:\OneDrive\My Document\My_Custom_Libs\Custom_Redshift_API" # custom path for api lib

Lib_Path = r"D:\OneDrive\CG_Config\C4D_Boghma_Plugins\Boghma_dev\My Custom API Helper"
sys.path.insert(0, Lib_Path)

try:

    #help(shortcut)
    import renderEngine
    reload(renderEngine)

    import renderEngine.redshift.redshift_node_material as rs
    reload(rs)

    import renderEngine.redshift.redshift_customid as rsID
    reload(rsID)

finally:
    # Remove the path we've just inserted.
    sys.path.pop(0)


doc = c4d.documents.GetActiveDocument()

#=============================================
#                  Examples
#=============================================

def GetFileAssetUrl(aid: maxon.Id) -> maxon.Url:
    """Returns the asset URL for the given file asset ID.
    """
    # Bail when the asset ID is invalid.
    if not isinstance(aid, maxon.Id) or aid.IsEmpty():
        raise RuntimeError(f"{aid = } is not a a valid asset ID.")

    # Get the user repository, a repository which contains almost all assets, and try to find the
    # asset description, a bundle of asset metadata, for the given asset ID in it.
    repo: maxon.AssetRepositoryRef = maxon.AssetInterface.GetUserPrefsRepository()
    if repo.IsNullValue():
        raise RuntimeError("Could not access the user repository.")
    
    asset: maxon.AssetDescription = repo.FindLatestAsset(
        maxon.AssetTypes.File(), aid, maxon.Id(), maxon.ASSET_FIND_MODE.LATEST)
    if asset.IsNullValue():
        raise RuntimeError(f"Could not find file asset for {aid}.")

    # When an asset description has been found, return the URL of that asset in the "asset:///"
    # scheme for the latest version of that asset.
    return maxon.AssetInterface.GetAssetUrl(asset, True)

# Node Material is On in preference
# 首选项中节点材质可用
if rs.RedshiftNodeBased():
    
    #---------------------------------------------------------
    # Example 01
    # 创建材质
    # Standard Surface
    #---------------------------------------------------------
    def CreateStandard(name):
        # 创建Standard Surface材质
        redshiftMaterial = rs.RedshiftNodeMaterial.CreateStandardSurface(name)

        # 将Standard Surface材质引入当前Document
        doc.InsertMaterial(redshiftMaterial.material)
        # 将Standard Surface材质设置为激活材质
        doc.SetActiveMaterial(redshiftMaterial.material)
        return redshiftMaterial.material


    #---------------------------------------------------------
    # Example 02
    # 新建节点 修改属性
    # Add and Modify Standard Surface
    #---------------------------------------------------------
    def AddandModify(name):

        redshiftMaterial =  rs.RedshiftNodeMaterial.CreateStandardSurface(name)

        # modification has to be done within a transaction
        with rs.RSMaterialTransaction(redshiftMaterial) as transaction:

            # Find brdf node (in this case : standard surface)
            # 查找Standard Surface节点
            standard_surface = redshiftMaterial.helper.GetRootBRDF()

            # Change a shader name
            # 更改Standard Surface节点名称
            redshiftMaterial.helper.SetName(standard_surface,'My BRDF Shader')


            # TexPath
            # 贴图路径
            url: maxon.Url = GetFileAssetUrl(maxon.Id("file_5b6a5fe03176444c"))
            tar = redshiftMaterial.helper.get_port(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.base_color')
            
            # Add a Texture node and set a tex to it , change color space to RAW
            # 添加一个Texture shader , 设置贴图路径,并将色彩空间设置为RAW
            tex_node = redshiftMaterial.AddTexture(shadername = 'YourTex', filepath = url, raw = True)
            


            # Add a texture tree to base color
            # 将纹理节点树（triplaner）到 base color 节点中
            redshiftMaterial.AddTextureTree(shadername = 'tree', filepath = url, raw = True, triplaner_node = True, scaleramp = False, target_port = tar)
            
            # Add a Displace tree
            # 将置换节点树
            redshiftMaterial.AddDisplacementTree()
            
            # Add a Bump tree
            # 将凹凸节点树
            redshiftMaterial.AddBumpTree()

        # Add the material to the scene
        # 将Standard Surface材质引入当前Document
        doc.InsertMaterial(redshiftMaterial.material)
        doc.SetActiveMaterial(redshiftMaterial.material)
        return redshiftMaterial.material

    #---------------------------------------------------------
    # Example 03
    # 修改已有材质
    # Modify Material
    #---------------------------------------------------------
    def ModifyMaterial(redshiftMaterial):

        if redshiftMaterial is None:
            return
        

        # modification has to be done within a transaction
        with rs.RSMaterialTransaction(redshiftMaterial) as transaction:

            # add a new STD shader
            noise = redshiftMaterial.AddMaxonNoise()
            noise_out = redshiftMaterial.helper.GetPort(noise, 'com.redshift3d.redshift4c4d.nodes.core.maxonnoise.outcolor')
            output = redshiftMaterial.helper.GetRootBRDF()
            
            redshiftMaterial.helper.AddConnection(noise,noise_out, output, rsID.PortStr.base_color)

    #---------------------------------------------------------
    # Example 04
    # 自定义生成ID
    # custom functions for IDs
    #---------------------------------------------------------
    def PrintID():
        # Mostly the string show in the node gui,then them can gennerate maxon id
        # 2023.2.1 Copy Id will not shipping useless str . it is easy to just copy
        # 输入界面显示的字符串就可以生成ID
        # 2023.2.1 复制ID不会附带多余字符串 可以直接复制id使用更方便
        StandardSurfaceShader = rsID.ShaderID.StandardMaterial
        StandardOutputPortString = rsID.PortStr.standard_outcolor
        StandardOutputPortID = rsID.PortID.standard_outcolor
        curvature_out = rsID.StrPortID("curvature", "out")    
        print("Name: " + str(StandardSurfaceShader), "Type: " , type(StandardSurfaceShader) )
        print("Name: " + str(StandardOutputPortString), "Type: " , type(StandardOutputPortString) )
        print("Name: " + str(StandardOutputPortID), "Type: " , type(StandardOutputPortID) )
        print("Name: " + str(curvature_out), "Type: " , type(curvature_out) )
if __name__ == '__main__':
    # --- 1 --- #
    example1 = CreateStandard("1.Standard Surface")
    # --- 2 --- #
    example2 = AddandModify("2.Modify Material")
    # --- 3 --- #
    material = rs.RedshiftNodeMaterial(example1)
    ModifyMaterial(material)
    # --- 4 --- #
    PrintID()

    # Put Refresh
    c4d.EventAdd()