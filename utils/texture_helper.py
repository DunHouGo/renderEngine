import c4d
import maxon
from typing import Union,Optional
import os
import random
import itertools
from pprint import pprint
import shutil
import Renderer
#__all__ = ["TextureHelper","Tex"]

# The Asset BrowserID
CID_ASSET_BROWSER: int = 1054225
CID_NODE_EDITOR: int = 465002211

class TextureHelper:

    def __init__(self) -> None:
        # data json
        self.keys_json: dict = {
            "AO": [
                "AO",
                "ao",
                "Ambient_Occlusion",
                "ambient_occlusion",
                "occlusion",
                "Occlusion",
                "Occ",
                "OCC",
                "Mixed_AO"
            ],
            "Alpha": [
                "Opacity",
                "opacity",
                "Alpha",
                "alpha"
            ],
            "Bump": [
                "Bump",
                "BUMP",
                "bump"
            ],
            "Diffuse": [
                "Base_Color",
                "BaseColor",
                "Basecolor",
                "Base_color",
                "base_color",
                "basecolor",
                "Albedo",
                "COLOR",
                "COL",
                "Color",
                "color"
            ],
            "Displacement": [
                "DISP",
                "DEPTH",
                "Depth",
                "Height",
                "eight",
                "Displacement"
            ],
            "Glossiness": [
                "Gloss",
                "GLOSS",
                "Glossiness"
            ],
            "Metalness": [
                "Metalness",
                "Metallic"
            ],
            "Normal": [
                "Normal",
                "NRM",
                "NORMAL",
                "Normaldx"
            ],
            "Roughness": [
                "ROUGHNESS",
                "Roughness",
                "Rough",
            ],
            "Translucency": [
                "Translucency"
            ],
            "Transmission": [
                "Transmission",
                "transmission",
                "Trans"
            ],
            "Specular": [
                "Specular",
                "Spec"
            ],
            "Emisson": [
                "Emisson",
                "Emissive"
            ]
            }

            
            # 支持的贴图后缀
        
        self.ext_list = [".jpg", ".png", ".exr", ".tif", ".tiff", ".tga"] 
        self.core_version = None
        self.all_textures = None
        self.root_folder: str = None
        self.diskfile: list = []
        self.assetfile: list = []
    
    @property
    def repository(self):
        return maxon.AssetInterface.GetUserPrefsRepository()

    @property
    def DBCache(self):
        return maxon.AssetDataBasesInterface.GetAssetDatabaseCachePath().GetSystemPath()

    def ShowAssetInBrowser(self, asset: maxon.AssetDescription):
        """
        Reveal an asset in the Asset Browser.

        """
        if self.IsAsset(asset):
            # Open the Asset Browser when it is not already open.
            if not c4d.IsCommandChecked(CID_ASSET_BROWSER):
                c4d.CallCommand(CID_ASSET_BROWSER)

            # show assets (even in multiple locations)
            maxon.AssetManagerInterface.RevealAsset([asset])

    def GetAsset(self, asset_id: Union[str,maxon.Url,maxon.Id]) -> maxon.AssetDescription:
        """
        Get the description for asset.        
        """
        if not self.repository:
            raise RuntimeError("Could not access the user preferences repository.")

        trueID = self.GetAssetId(asset_id)
        # Retrieve the asset description for the asset.
        assetDescription = self.repository.FindLatestAsset(
            maxon.AssetTypes.File(), trueID, maxon.Id(), maxon.ASSET_FIND_MODE.LATEST)
        if assetDescription is None:
            raise RuntimeError("Could not find the asset.")
        if maxon.AssetInterface.IsAssetValid(assetDescription) and assetDescription.IsNullValue():
            return assetDescription
    
    def IsAsset(self, asset) -> bool:
        if not isinstance(asset, maxon.AssetDescription):
            return False
            # raise TypeError(f"Expected {maxon.AssetDescription} for 'asset'. Received: {asset}")
        if isinstance(asset, maxon.AssetDescription):
            return True

    def GetTextureList(self, doc: c4d.documents.BaseDocument) -> list[Union[str,maxon.Url]]:
        textures = list()
        c4d.documents.GetAllAssetsNew(doc, False, "", c4d.ASSETDATA_FLAG_TEXTURESONLY, textures)
        self.all_textures = textures
        return textures
    
    def GetAssetId(self, asset_path: Union[str,maxon.Url,maxon.Id]) -> maxon.Id:
        if isinstance(asset_path, maxon.Id):
            if not asset_path.IsEmpty():
                return asset_path
        elif isinstance(asset_path, maxon.Url):
            asset_id = maxon.Id(asset_path.GetName().replace('~',''))
            if not asset_id.IsEmpty():
                return asset_id
        elif isinstance(asset_path, str):
            asset_id = maxon.Id(maxon.Url(asset_path).GetName().replace('~',''))
            if not asset_id.IsEmpty():
                return asset_id
        return None

    def IsVaildPath(self, asset: Union[str,maxon.Url,maxon.Id]) -> bool:
        
        if isinstance(asset, str):
            if asset is None:
                return False
            if asset == '':
                return False
            if os.path.exists(asset):
                return True

            # local tex folder
            for path in self.root_folder:
                if os.path.exists(os.path.join(self.root_folder,asset)):
                    return True
                
            # global texture paths
            paths = c4d.GetGlobalTexturePaths()
            for path, enabled in paths:
                if os.path.exists(os.path.join(path,asset)):
                    return True
                
        if isinstance(asset, maxon.Url):
            textureURL = asset.ClearSuffix()
            assetID = maxon.Id(textureURL.GetName().replace('~',''))
            if not assetID.IsEmpty():
                assetDescription = self.repository.FindLatestAsset(
                                maxon.AssetTypes.File(), assetID, maxon.Id(), maxon.ASSET_FIND_MODE.LATEST)
                if maxon.AssetInterface.IsAssetValid(assetDescription) and not assetDescription.IsNullValue():
                    return True
                
        if isinstance(asset, maxon.Id):
            if not asset.IsEmpty():
                assetDescription = self.repository.FindLatestAsset(
                                maxon.AssetTypes.File(), asset, maxon.Id(), maxon.ASSET_FIND_MODE.LATEST)
                if maxon.AssetInterface.IsAssetValid(assetDescription) and not assetDescription.IsNullValue():
                    return True
                 
        return False

    def GetAssetUrl(self, aid: Union[maxon.Id,str]) -> maxon.Url:
        """Returns the asset URL for the given file asset ID.
        """
        # Bail when the asset ID is invalid.
        if not self.repository:
            raise RuntimeError("Could not access the user preferences repository.")
        if not isinstance(aid, maxon.Id) or aid.IsEmpty():        
            aid = maxon.Id(aid)
            
        if aid.IsEmpty():
            raise RuntimeError("Could not find the maxon id")
        
        asset: maxon.AssetDescription = self.repository.FindLatestAsset(
            maxon.AssetTypes.File(), aid, maxon.Id(), maxon.ASSET_FIND_MODE.LATEST)
        if asset.IsNullValue():
            raise RuntimeError(f"Could not find file asset for {aid}.")

        # When an asset description has been found, return the URL of that asset in the "asset:///"
        # scheme for the latest version of that asset.
        return maxon.AssetInterface.GetAssetUrl(asset, True)

    def GetAssetStr(self, aid: Union[maxon.Id,str]) -> str:
        """Returns the asset str for the given file asset ID.
        """
        return str(self.GetAssetUrl(aid))

    def GetAssetName(self, aid: Union[maxon.Id,str]) -> str:
        """Returns the asset Name for the given file asset ID.
        """
        return self.GetAssetUrl(aid).GetName()

    def GetAllTexturePaths(self, new_file_path, collect_asset: bool = False , collect_tex: bool = True):
        
        if self.all_textures is None:
            return

        for t in self.all_textures:

            textureOwner = t["owner"]
            textureParam = t["paramId"]
            textureURL : maxon.UrlInterface = maxon.Url(t["filename"])
            x = str(textureURL).split(":")

            if collect_asset:
                # 贴图为资产
                if x[0] == 'asset':            
                    textureAsset : maxon.UrlInterface = maxon.Url(t['assetname'])
                    # 资产文件名
                    assetName = textureAsset.GetName()
                    # 资产ID
                    textureSuffix = textureURL.GetSuffix()
                    textureURL.ClearSuffix()
                    assetID = textureURL.GetName().replace('~','')
                    collectState = self.CollectAssetTextures(new_file_path,assetID,name)
                    # 设置
                    if collectState == True:
                        textureOwner[textureParam] = assetName
                    # 归入资产列表
                    self.assetfile.append(assetID)
                    
            if collect_tex:
                # 贴图为本地文件
                if x[0] == 'file':
                    #print('filename : ',t["filename"])
                    name = textureURL.GetName()
                    localPath = textureURL.GetSystemPath()
                    collectState = self.CollectLocalTexture(new_file_path,localPath,name)
                    # 设置
                    if collectState == True:
                        textureOwner[textureParam] = name
                    # 归入本地文件列表
                    self.diskfile.append(x)

    # _ 打包资产纹理
    def CollectAssetTextures(self, new_file_path, assetID : str, assetName:str) -> bool:
        """
        Collect Textures in AssetInterface

        Args:
            assetID (str): asset ID for Asset Browser
            assetName (str): asset displayed file name e.g. si-v1_fingerprints_08_15cm.png

        Returns:
            bool: False if collect is failed
        """
        #? 查找资产
        asset: maxon.AssetDescription = self.GetAsset(self.GetAssetId(assetID))
        # assetName = self.GetAssetName(self.GetAssetId(assetID))
        file = os.path.join(new_file_path, assetName)
        url: maxon.Url = asset.GetUrl()
        #? fileName: str = url.GetUrl() # 优先使用 AssetInterface.GetUrl()
        # 对比文件
        assetlocalpath = url.GetSystemPath() # user asset
        # assetdbfile = os.path.join(self.DBCache,assetlocalpath) # assetDB asset
        file = os.path.join(new_file_path, assetName) # tex文件夹下文件
        #texname = url.GetName()

        # 资产库中存在对应ID的资产
        if os.path.exists(assetlocalpath):
            # tex文件夹中没有对应《名称》的文件
            if not os.path.exists(file):
                shutil.copyfile(assetlocalpath, file)
                state = True
            elif os.path.exists(file):
                state = True
        else:
            print('----------------------')
            print('++ > Asset File : ' , assetName) 
            print('State : ', 'Failed')
            print('Path : ', assetlocalpath)
            print('----------------------')
            state = False
        # # 调试用
        # print("url : ",url)
        # #print("fileName : ",fileName)
        # print("cacheFolder : ",cacheFolder)
        # print("assetdbfile : ",assetdbfile)
        # #print("Tex name : ",texname)
        # print("Asset_local_path : ",assetlocalpath)
        # print('Full name : ', file)
        return state
    
    # TEST
    def CollectTextures(self, doc: c4d.documents.BaseDocument) -> int:
        
        newPath: str = self.GetRootTexFolder(doc)
        
        if not doc.GetDocumentPath():
            c4d.gui.MessageDialog("Not Save")
            return
            
        assetData: list[dict] = []
        c4d.documents.GetAllAssetsNew(doc, False, "", c4d.ASSETDATA_FLAG_TEXTURESONLY, assetData)
        
        if not os.path.exists(newPath):
            raise IOError(f"Target path '{newPath}' does not exist.")

        copy_num: int = 0
        skip_num: int = 0
        
        doc.StartUndo()
        
        for item in assetData:
            assetExists: bool = item.get("exists", False)
            nodePath: str = item.get("nodePath", "")
            nodeSpace: str = item.get("nodeSpace", "")
            oldPath: str = item.get("filename", "")
            filename: str = maxon.Url(oldPath).GetName()
            owner: Optional[c4d.BaseList2D] = item.get("owner", None)
            paramId: int = item.get("paramId", c4d.NOTOK)
            
            if not assetExists or oldPath.startswith("asset:"):
                skip_num += 1
                c4d.StatusSetText(f"Skipping over Asset {filename}.")
                continue
            
            if os.path.exists(os.path.join(newPath, filename)):
                skip_num += 1
                c4d.StatusSetText(f"File {filename} already there.")
        
            if not os.path.exists(os.path.join(newPath, filename)) and not oldPath.startswith("asset:"):
                c4d.StatusSetText(f"Copy file {filename}.")
                # print(f"{file} copy!")
                copy_num += 1
                shutil.copy(oldPath, newPath)

            if isinstance(owner, c4d.BaseShader) and paramId != c4d.NOTOK and nodePath == "":
                doc.AddUndo(c4d.UNDOTYPE_CHANGE, owner)
                owner[paramId] = filename

            # Node material
            if isinstance(owner, c4d.BaseMaterial) and nodePath != "" and nodeSpace != "":

                nodeMaterial: c4d.NodeMaterial = owner.GetNodeMaterialReference()
                if not nodeMaterial:
                    raise MemoryError(f"Cannot access node material of material.")

                graph: maxon.GraphModelInterface = nodeMaterial.GetGraph(nodeSpace)
                if graph.IsNullValue():
                    raise RuntimeError(f"Invalid node space for {owner}: {nodeSpace}")

                # Disable Undo
                settings: maxon.DataDictionaryInterface = maxon.DataDictionary()
                
                with graph.BeginTransaction(settings) as transaction:
                    node: maxon.GraphNode = graph.GetNode(maxon.NodePath(nodePath))
                    if node.IsNullValue():
                        raise RuntimeError(f"Could not retrieve target node {nodePath} in {graph}.")

                    if (nodeSpace == Renderer.RS_NODESPACE and 
                        node.GetId().ToString().split("@")[0] == "texturesampler"):
                        pathPort: maxon.GraphNode = node.GetInputs().FindChild(
                            "com.redshift3d.redshift4c4d.nodes.core.texturesampler.tex0").FindChild(
                                "path")
                        if pathPort.IsNullValue():
                            continue
                        
                        if c4d.GetC4DVersion() >= 2024400: pathPort.SetPortValue(filename)
                        else: pathPort.SetDefaultValue(filename)

                    elif (nodeSpace == Renderer.STANDARD_NODESPACE and 
                        node.GetId().ToString().split("@")[0] == "image"):
                        pathPort: maxon.GraphNode = node.GetInputs().FindChild(
                            "url").FindChild(
                                "path")
                        if pathPort.IsNullValue():
                            continue
                        if c4d.GetC4DVersion() >= 2024400: pathPort.SetPortValue(filename)
                        else: pathPort.SetDefaultValue(filename)

                    elif (nodeSpace == Renderer.AR_NODESPACE and 
                        node.GetId().ToString().split("@")[0] == "image"):
                        pathPort: maxon.GraphNode = node.GetInputs().FindChild(
                            "filename").FindChild(
                                "path")
                        if pathPort.IsNullValue():
                            continue
                        if c4d.GetC4DVersion() >= 2024400: pathPort.SetPortValue(filename)
                        else: pathPort.SetDefaultValue(filename)

                    elif (nodeSpace == Renderer.VR_NODESPACE and 
                        node.GetId().ToString().split("@")[0] == "texbitmap"):
                        pathPort: maxon.GraphNode = node.GetInputs().FindChild(
                            "com.chaos.vray_node.texbitmap.file").FindChild(
                                "path")
                        if pathPort.IsNullValue():
                            continue
                        if c4d.GetC4DVersion() >= 2024400: pathPort.SetPortValue(filename)
                        else: pathPort.SetDefaultValue(filename)        
            
                    # Here you would have to implement other node spaces as for example the standard 
                    # space, Arnold, etc.
                    else:
                        continue
                        
                    transaction.Commit()

        return copy_num

    def GetRootTexFolder(self, doc: c4d.documents.BaseDocument) -> str :
        """
        Get the local tex folder in the expolorer.

        Returns:
            string : tex folder path
        """
        tex_folder = os.path.join(doc.GetDocumentPath(),"tex") # Tex Folder
        if not os.path.exists(tex_folder):
            os.makedirs(tex_folder)
        self.root_folder = tex_folder
        return tex_folder
    
    def GetRootTexturesSize(self, file_names: list = None) :
        if file_names is None:
            file_names = os.listdir(self.root_folder)
            
        total_size = 0        
        for img_file in file_names:
            total_size += os.path.getsize(img_file)
        return total_size

    ###  PBR  ###
    def get_all_keys(self):
        """
        获取关键词数据和原始数据
        :return: 关键词列表，原始数据
        """

        # 所有关键词去重保存
        # sum：拆分嵌套列表合并成一个列表
        # set：列表去重
        keys = list(set(sum(self.keys_json.values(), [])))
        return keys, self.keys_json

    def get_texture_data(self, texture: str = None):
        
        if texture is None:
            # 用户任意选择一张贴图
            texture = c4d.storage.LoadDialog(type=c4d.FILESELECTTYPE_IMAGES, title='Select a texture',
                                        flags=c4d.FILESELECT_LOAD)
            if not texture:
                return
        if texture:
            # 关键词列表， 原始数据
            all_keys, key_data = self.get_all_keys()

            # 用户选择的贴图文件的 路径 和 文件名
            fp, fn = os.path.split(texture)

            # 文件名 和 后缀
            fn, ext = os.path.splitext(fn)

            channels = []  # 贴图通道
            textures = []  # 贴图

            name = ""
            # 遍历关键词列表，k = 关键词
            for k in all_keys:
                if k:
                    if k in fn:
                        # 如果贴图文件名中有某个关键词
                        # 以关键词对文件名拆分，例如：ground_albedo_2k ---> ['ground_', '_2k']
                        # ['asdasd_4k_', ""]
                        words = fn.split(k)

                        for k in all_keys:
                            if k:
                                # 遍历通道，key = 通道名（原始数据字典中的key）
                                for key in key_data:
                                    # 用户的 关键词 在原始数据中的哪个列表里
                                    if k in key_data[key]:
                                        for e in self.ext_list:
                                            # 组合贴图完整路径和名称，开始找贴图
                                            tex = os.path.join(fp, f"{words[0]}{k}{words[1]}{e}")
                                            # 如果贴图存在
                                            if os.path.exists(tex):
                                                # 在通道列表里加入 通道key，贴图列表里加入 贴图tex
                                                channels.append(key)
                                                textures.append(tex)
                                                name = words[0]
                                                # 得到了 贴图属于哪个通道 和 贴图路径
            # 将两个列表组合成一个字典：
            # {"Diffuse": "D:\Texture\ground_albedo_2k.jpg"} ...
            tex_data = dict(zip(channels, textures))
            #print(tex_data)
            if name[-1] == "_" or name[-1] == "-" or name[-1] == " ":
                name = name[:-1]
            elif name == "":
                name = "MyMaterial"
            return tex_data, name
        else:
            return None

    def PBRFromTexture(self,file:str):
        if not os.path.isfile(file) or not os.path.exists(file):
            raise ValueError(f"{file} is not a file or not exist")

        # 用户选择的贴图文件的 路径 和 文件名
        folder_path, file_name = os.path.split(file)
        all_textures = os.listdir(folder_path)

        # 文件名 和 后缀
        file_name, ext = os.path.splitext(file_name)

        channels = []  # 贴图通道
        textures = []  # 贴图
        
        all_keys, key_data = self.get_all_keys()
        
        # 获取贴图名称
        for i in all_keys:
            temp = file_name
            if i.lower() in file_name.lower():
                # 去除名称前后的分隔符
                romoved = file_name.lower().replace(i.lower(),'')
                # 恢复剔除后的大小写
                name = temp[0:len(romoved)]
                
                if name[-1] == "_" or name[-1] == "-" or name[-1] == " ":
                    name = name[:-1]
                #print(name)

        for channel in self.keys_json.keys():
            combinations = list(itertools.product([name], key_data[str(channel)], self.ext_list))
            for c in combinations:
                # 贴图组合
                file = f"{c[0]}_{c[1]}{c[2]}"
                # 如果list中有同名，判定找到贴图
                if file in all_textures:                
                    channels.append(str(channel))
                    textures.append(os.path.join(folder_path, file))
        # 将两个列表组合成一个字典：
        tex_data = dict(zip(channels, textures))
        return tex_data, name

    def PBRFromPath(self, folder_path: str, file: str):
        if folder_path is None or file is None:
            return

        if not os.path.isdir(folder_path) or not os.path.exists(folder_path):
            raise ValueError(f"{folder_path} is not a dir or not exist")
        
        all_textures = os.listdir(folder_path)

        channels = []  # 贴图通道
        textures = []  # 贴图

        all_keys, key_data = self.get_all_keys()

        name = file
        for channel in self.keys_json.keys():
            combinations = list(itertools.product([name], key_data[str(channel)], self.ext_list))
            for c in combinations:
                # 贴图组合
                file = f"{c[0]}_{c[1]}{c[2]}"
                # 如果list中有同名，判定找到贴图
                if file in all_textures:
                    channels.append(str(channel))
                    textures.append(os.path.join(folder_path, file))
        # 将两个列表组合成一个字典：
        tex_data = dict(zip(channels, textures))
        return tex_data

