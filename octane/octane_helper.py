# -*- coding: utf-8 -*-  

# Develop for Maxon Cinema 4D version 2023.2.0
#   ++> Octane Render version 2022.1.1

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
__website__ = "https://www.boghma.com/"
__license__ = "Apache-2.0 License"
__version__ = "2023.2.1"

###  ==========  Import from boghma  ==========  ###

from typing import Optional,Union
import c4d
import os,sys
import re
from dataclasses import dataclass
from pprint import pprint
import random
from importlib import reload

try:
    from octane_id import *
except:
    from renderEngine.octane.octane_id import *

from renderEngine import node_helper
reload(node_helper)

###  ==========  Import from disk  ==========  ###

# # import custom API
# PLUGIN_PATH = r"D:\OneDrive\CG_Config\C4D_Boghma_Plugins\Boghma_dev\My Custom API Helper\renderEngine\octane"

# sys.path.insert(0, PLUGIN_PATH)

# try:
#     import octane_id
#     reload(octane_id)  
#     from octane_id import *
    
# except:
#     from renderEngine.octane.octane_id import *
    
# finally:
#     # Remove the path we've just inserted.
#     sys.path.pop(0)


# IDs in octane symbol.h
# from octane_id import *


ID_MATERIAL_MANAGER: int = 12159

doc = c4d.documents.GetActiveDocument()

# 生成随机颜色
def generate_random_color(pastel_factor = 0.5):
    def _color_distance(c1,c2):
        return sum([abs(x[0]-x[1]) for x in zip(c1,c2)])
    #_ 在指定饱和度生成随机颜色 v1.0
    def _get_random_color(pastel_factor):
        return [(x+pastel_factor)/(1.0+pastel_factor) for x in [random.uniform(0,1.0) for i in [1,2,3]]]
    existing_colors = []
    max_distance = None
    best_color = None
    for i in range(0,100):
        color = _get_random_color(pastel_factor = pastel_factor)
        if not existing_colors:
            return color
        best_distance = min([_color_distance(color,c) for c in existing_colors])
        if not max_distance or best_distance > max_distance:
            max_distance = best_distance
            best_color = color
    return best_color

def iterate(node):
    while isinstance(node, c4d.BaseList2D):
        yield node

        for child in iterate(node.GetDown()):
            yield child

        node = node.GetNext()

###  ==========  Octane Class  ==========  ###

# 获取渲染器
def GetRenderEngine(document: c4d.documents.BaseDocument = None) -> int :
    """
    Return current render engine ID.
    """
    if not document:
        document = c4d.documents.GetActiveDocument()
    return doc.GetActiveRenderData()[c4d.RDATA_RENDERENGINE]

# 获取渲染器版本
def GetVersion() -> str :
    """
    Get the version number of Octane.

    Returns:
        str: The version number
    """
    doc = c4d.documents.GetActiveDocument()
    OctaneDialogOpened = False
    
    def GetOctaneDialogOpened():
        return OctaneDialogOpened
    
    def SetOctaneDialogOpened( value = True ):
        OctaneDialogOpened = value
    
    if GetRenderEngine() == ID_OCTANE_VIDEO_POST:
        try:
            bc = doc[ID_OCTANE_LIVEPLUGIN]
            renderer_version = bc[c4d.SET_OCTANE_VERSION]
            SetOctaneDialogOpened()
            return renderer_version
        except Exception as e:
            try:
                if GetOctaneDialogOpened() == False:
                    SetOctaneDialogOpened()
                    c4d.CallCommand(1031193) # Octane Dialog
                bc = doc[ID_OCTANE_LIVEPLUGIN]
                renderer_version = bc[c4d.SET_OCTANE_VERSION]
            except:
                renderer_version = 0
    else: renderer_version = 0
    return renderer_version

# 打开IPR
def OpenIPR() -> None:
    """
    Open Live Viewer.
    """
    c4d.CallCommand(ID_OCTANE_LIVEPLUGIN)  # Octane Live Viewer Window
    
# 打开材质编辑器
def OpenNodeEditor(actmat: c4d.BaseMaterial = None) -> None:
    """
    Open Node Editor for given material.
    """
    if not actmat:
        doc = c4d.documents.GetActiveDocument()
        actmat = doc.GetActiveMaterial()
    doc.AddUndo(c4d.UNDOTYPE_BITS,actmat)
    actmat.SetBit(c4d.BIT_ACTIVE)
    if not actmat:
        raise ValueError("Failed to retrieve a Material.")
        
    if GetRenderEngine() == ID_OCTANE_VIDEO_POST:
        c4d.CallCommand(1033872) # Octane Node Editor
        # Only scroll to the material if material manager is opened
        if c4d.IsCommandChecked(ID_MATERIAL_MANAGER):  
            c4d.CallCommand(16297) # Scroll To Selection

# 打开aov管理器
def AovManager() -> None:
    """
    Open aov Manager.
    """
    c4d.CallCommand(1058335) # aov Manager...

# 打开贴图管理器
def TextureManager() -> None:
    """
    Open Octane Texture Manager.
    """
    c4d.CallCommand(1035275) # Octane Texture Manager

###  ==========  VideoPost  ==========  ###

class VideoPostHelper:
    """
    VideoPost
    """
    def __init__(self, document: c4d.documents.BaseDocument = None):
        if document is None:
            document: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
        self.doc: c4d.documents.BaseDocument = document
        self.vp: c4d.documents.BaseVideoPost = self.get_videopost()
        self.vpname: str = self.vp.GetName()
    
    @property
    def videopost(self) -> c4d.documents.BaseVideoPost:
        return self.vp
    
    ###  通用  ###
    
    # 获取渲染器 ==> ok
    def get_videopost(self) -> c4d.documents.BaseVideoPost:
        """Get the video post"""
        rdata: c4d.documents.RenderData = self.doc.GetActiveRenderData()
        vpost: c4d.documents.BaseVideoPost = rdata.GetFirstVideoPost()
        octVp: c4d.documents.BaseVideoPost = None

        # 获取Octane VP
        while vpost:
            if vpost.GetType() == ID_OCTANE_VIDEO_POST:
                octVp = vpost
            vpost = vpost.GetNext()
        return octVp 
    
    # 辅助：打印vp信息
    def list_vpdata(self):

        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        
        bc: c4d.BaseContainer = self.vp.GetDataInstance()

        for key in range(len(bc)):
            key = bc.GetIndexId(key)
            try:
                print(f"Key: {key}, Value: {bc[key]}, DataType{bc.GetType(key)}")
            except AttributeError:
                print("Entry:{0} is DataType {1} and can't be printed in Python".format(key, bc.GetType(key)))

    # 复制vp设置到相机标签
    def videopost_to_camera(self, tag : c4d.BaseTag ):
        
        sBC = self.doc.GetDataInstance()
        data = sBC.GetContainerInstance( ID_OCTANE_LIVEPLUGIN )

        if tag != None and tag.GetType() == ID_OCTANE_CAMERATAG : 
            
            tag[c4d.OCTANECAMERA_ENABLE_IMAGER] = True
            tag[c4d.OCT_CAMIMAGER_EN_DENOISER] = True # Denoise ON        
            
            tagBC = tag.GetDataInstance()
            
            # Denoise
            tagBC.SetBool(c4d.OCT_CAMIMAGER_DENOISE_VOLUMES,    data.GetBool(c4d.SET_CAMIMAGER_DENOISE_VOLUME)) 
            tagBC.SetBool(c4d.OCT_CAMIMAGER_DENOISE_ON_COMP,    data.GetBool(c4d.SET_CAMIMAGER_DENOISE_ON_COMP)) 
            
            tagBC.SetReal(c4d.OCT_CAMIMAGER_DENOISE_MINSAMPLES,    data.GetReal(c4d.SET_CAMIMAGER_DENOISE_MINSMP)) 
            tagBC.SetReal(c4d.OCT_CAMIMAGER_DENOISE_INTERVAL,    data.GetReal(c4d.SET_CAMIMAGER_DENOISE_INTERVAL))
            tagBC.SetReal(c4d.OCT_CAMIMAGER_DENOISE_BLEND,    data.GetReal(c4d.SET_CAMIMAGER_DENOISE_BLEND)) 
            # Imager
            tagBC.SetReal(c4d.OCTANECAMERA_EXPOSURE,        data.GetReal(c4d.SET_CAMIMAGER_EXPOSURE)) # Exposure        
            tagBC.SetReal(c4d.OCTANECAMERA_HCOMPRESSION,   data.GetReal(c4d.SET_CAMIMAGER_HCOMPRESSION)) # Highlight compression
            
            tagBC.SetInt32(c4d.OCT_CAMERA_IMAGER_ORDER,      data.GetInt32(c4d.SET_CAMIMAGER_ORDER)) # Imager order
            tagBC.SetInt32(c4d.OCTANECAMERA_RESPONSE,      (5000+data.GetInt32(c4d.SET_CAMIMAGER_RESPONSE))) # Response
            tagBC.SetReal(c4d.OCTANECAMERA_GAMMA,          data.GetReal(c4d.SET_CAMIMAGER_GAMMA)) # Gamma
            
            tagBC.SetBool(c4d.OCTANECAMERA_NAT_RESPONSE,    data.GetBool(c4d.SET_CAMIMAGER_NATRESPONSE)) # Natual response
            tagBC.SetReal(c4d.OCTANECAMERA_VIGNETTING,         data.GetReal(c4d.SET_CAMIMAGER_VIGNET)) # Vignetting
            tagBC.SetReal(c4d.OCTANECAMERA_SATURATION,     data.GetReal(c4d.SET_CAMIMAGER_SATURATION)) # Saturation
            tagBC.SetReal(c4d.OCTANECAMERA_HOTPIXEL,     data.GetReal(c4d.SET_CAMIMAGER_HOTREMOVAL)) # Hot pixel removel

            tagBC.SetBool(c4d.OCTANECAMERA_PREMALPHA,       data.GetBool(c4d.SET_CAMIMAGER_PREM_ALPHA)) # Disable partial alpha
            tagBC.SetBool(c4d.OCTANECAMERA_DITHERING,       data.GetBool(c4d.SET_CAMIMAGER_DITHERING)) # Disable partial alpha
            
            tagBC.SetReal(c4d.OCTANECAMERA_SATURATETOWHITE, data.GetReal(c4d.SET_CAMIMAGER_SATURE_TO_WHITE)) # Saturation to white
            tagBC.SetReal(c4d.OCTANECAMERA_MDISP_SAMPLES, data.GetReal(c4d.SET_CAMIMAGER_MDISP_SAMPLES)) # min display samples
            tagBC.SetReal(c4d.OCTANECAMERA_MAX_TM_INTERVAL, data.GetReal(c4d.SET_CAMIMAGER_MAX_TM_INTERVAL)) # max tonemap samples
            
        else:
            return False
        
    
        # 辅助：打印vp信息
    
    # 设置渲染
    def set_render_settings(self, file_path: str, use_exr: bool = True, no_filters: bool = False):
        
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        
        self.vp[c4d.SET_PASSES_ENABLED] = True
        self.vp[c4d.SET_PASSES_BEAUTY_DENOISER2] = True
        self.vp[c4d.SET_PASSES_SAVEPATH] = file_path
        
        if use_exr:        
            self.vp[c4d.SET_PASSES_EXR_COMPR] = 9 # DWAB exr
            self.vp[c4d.SET_PASSES_FILEFORMAT] = 8 # octane exr
        else:
            self.vp[c4d.SET_PASSES_MAKEFOLDER] = True
            
        if no_filters:
            self.vp[c4d.SET_RENDERPASS_INFO_SAMPLINGMODE] = 2 # info sample to no filtering


@dataclass
class AOVData:
    """
    Octane AOV dataclass structure
    """
    aov_shader: c4d.BaseShader
    aov_enabled: bool
    aov_name: str
    aov_type: c4d.BaseList2D
    aov_subdata: list


class AOVHelper:
    """
    用于获取/删除Octane AOV
    """
    def __init__(self, videopost: c4d.documents.BaseVideoPost):
        if isinstance(videopost, c4d.documents.BaseVideoPost):
            self.vp: c4d.documents.BaseVideoPost = videopost
            self.vpname: str = self.vp.GetName()

      # 名称对照字典
    
    @staticmethod
    def convert_namedata(name_list: list[str]) -> dict[int,str]:
        """
        A help function to convert name list from .h to a dict.
        
        Parameters
        ----------               
        :param name_list: the list
        :type name_list: list[str]
        :return: the data dict
        :rtype: dict[int,str]
        """
        
        new_data: dict = {}
        
        for name in name_list:
            name_str = re.sub('[{}]'.format("_")," ", name.replace('RNDAOV',"").title()).strip()
            new_data[name] = name_str
            # new_data["c4d." + name] = name_str
            
        return new_data
    
    # aov data
    def get_aov_data(self) -> list[c4d.BaseContainer] | None:
        """
        Get all aov data in a list of BaseContainer.
        
        Parameters
        ----------        
        :return: the data list
        :rtype: list[c4d.BaseContainer] | None
        """

        if self.vp is None:
            raise RuntimeError("Can't get the Octane VideoPost")
        
        aovCnt: int = self.vp[SET_RENDERAOV_IN_CNT]
        if len(aovCnt) > 0:
            data: list = []
            for i in range(0, aovCnt):
                aov: c4d.BaseShader = self.vp[SET_RENDERAOV_INPUT_0+i]
                aov_data = aov.GetDataInstance()
                data.append(aov_data)
            return data
        else: return None

    # 获取所有aov shader ==> ok
    def get_all_aovs(self) -> list[c4d.BaseShader] :
        """
        Get all octane aovs in a list.

        Returns:
            list[c4d.BaseShader]: A List of all find nodes

        """
        
        # The list.
        result: list = []

        start_shader = self.vp.GetFirstShader()
        
        if not start_shader:
            raise RuntimeError("No shader found")
        
        for obj in iterate(start_shader):

            result.append(obj)

        # Return the object List.
        return result

    # 获取指定类型的aov shader ==> ok
    def get_aov(self, aov_type: c4d.BaseList2D) -> list[c4d.BaseList2D]:
        """
        Get all the aovs of given type in a list.
        
        Args:
            aov_type (Union[c4d.BaseList2D, c4d.BaseShader]): Shader to iterate.
            
        Returns:
            list[c4d.BaseList2D]: A List of all find aovs

        """

        # The list.
        result: list = []

        start_shader = self.vp.GetFirstShader()
        if not start_shader:
            raise RuntimeError("No shader found")
        
        for obj in iterate(start_shader):
            if obj[RNDAOV_TYPE] != aov_type:
                continue
            result.append(obj)

        return result

    # 读取aov ==> ok
    def read_aov(self) -> list[AOVData]:
        """
        Get aov data in a list.
        [
            aov_shader: c4d.BaseShader
            aov_enabled: bool
            aov_name: str
            aov_type: c4d.BaseList2D
            aov_subdata: list
        ]
        
        :return: aov data list.
        :rtype: list[OctaneAOVData]
        """
        
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")

        aovCnt = self.vp[SET_RENDERAOV_IN_CNT]        
        
        aovs: list[AOVData] = []
        
        for i in range(0, aovCnt):
            aov = self.vp[SET_RENDERAOV_INPUT_0+i]
            aov_enabled = aov[RNDAOV_ENABLED]
            aov_name = aov[RNDAOV_NAME]
            aov_type = aov[RNDAOV_TYPE]
            aov_subdata = None
            
            # Z-Depth
            if aov_type == RNDAOV_ZDEPTH:
                aov_subdata = [
                    aov[RNDAOV_ZDEPTH_MAX],
                    aov[RNDAOV_ZDEPTH_ENVDEPTH]
                    ]
                print ("Subdata: Z-depth max:",aov[RNDAOV_ZDEPTH_MAX]," Env.depth:",aov[RNDAOV_ZDEPTH_ENVDEPTH])
                
            # Light
            if aov_type == RNDAOV_LIGHT:
                aov_subdata = [
                    aov[RNDAOV_LIGHT_ID]
                    ]
                print ("Subdata: Light ID:",aov[RNDAOV_LIGHT_ID])  
                
            # Light D
            if aov_type == RNDAOV_LIGHT_D:
                aov_subdata = [
                    aov[RNDAOV_LIGHT_ID]
                    ]
                print ("Subdata: Light ID (direct):",aov[RNDAOV_LIGHT_ID])  
                
            # Light I
            if aov_type == RNDAOV_LIGHT_I:
                aov_subdata = [
                    aov[RNDAOV_LIGHT_ID]
                    ]
                print ("Subdata: Light ID (indirect):",aov[RNDAOV_LIGHT_ID])  
                
            # Custom
            if aov_type == RNDAOV_CUSTOM:
                aov_subdata = [
                    aov[RNDAOV_CUSTOM_IDS],
                    aov[RNDAOV_VISIBLE_AFTER]
                    ]
                print ("Subdata: Custom ID:",aov[RNDAOV_CUSTOM_IDS]," Vis after:", aov[RNDAOV_VISIBLE_AFTER])    
                
            # Cryptomatte
            if aov_type == RNDAOV_CRYPTOMATTE:
                aov_subdata = [
                    aov[RNDAOV_CRYPTO_TYPE]
                    ]
                print ("Subdata: Custom ID:",aov[RNDAOV_CRYPTO_TYPE])    
                                        
            aovs.append(AOVData(aov_shader=aov,
                                      aov_enabled=aov_enabled,
                                      aov_name=aov_name,
                                      aov_type=aov_type,
                                      aov_subdata=aov_subdata))
        return aovs

    # 打印aov ==> ok
    def print_aov(self):
        """
        Print main info of existed aov in python console.

        """
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        
        aovCnt = self.vp[SET_RENDERAOV_IN_CNT]
        color_space = self.vp[VP_COLOR_SPACE]
        if color_space == 0:
            color_str = "sRGB"
        elif color_space == 1:
            color_str = "Linear sRGB"
        elif color_space == 2:
            color_str = "ACES2065-1"          
        elif color_space == 3:
            color_str = "ACEScg"
        elif color_space == 4:
            color_str = "OCIO"
                      
        print ("--- OCTANERENDER ---")
        print ("Name:", self.vp.GetName())
        print ("Color space:", color_str)
        print ("AOV count:", aovCnt)
        
        if aovCnt == 0:
            print("No AOV data in this scene.")
        else:
            for i in range(0, aovCnt):
                aov = self.vp[SET_RENDERAOV_INPUT_0+i]
                if aov is not None:
                    aov_enabled = aov[RNDAOV_ENABLED]
                    aov_name = aov[RNDAOV_NAME]
                    aov_type = aov[RNDAOV_TYPE]

                    print("--"*10)
                    print("Name                  :%s" % aov_name if aov_name else AOV_SYMBOLS[aov_type])
                    print("Type                  :%s" % str(aov_type) + " for " + AOV_SYMBOLS[aov_type])
                    print("Enabled               :%s" % ("Yes" if aov_enabled else "No"))

                    
                    #print(SET_RENDERAOV_INPUT_0)
                    print('aov1',self.vp[SET_RENDERAOV_INPUT_0])
                    #print(SET_RENDERAOV_INPUT_0+1)
                            
                    # Z-Depth
                    if aov_type == RNDAOV_ZDEPTH:
                        print ("Subdata: Z-depth max:",aov[RNDAOV_ZDEPTH_MAX]," Env.depth:",aov[RNDAOV_ZDEPTH_ENVDEPTH])
                        
                    # Light
                    if aov_type == RNDAOV_LIGHT:
                        print ("Subdata: Light ID:",aov[RNDAOV_LIGHT_ID])  
                        
                    # Light D
                    if aov_type == RNDAOV_LIGHT_D:
                        print ("Subdata: Light ID (direct):",aov[RNDAOV_LIGHT_ID])  
                        
                    # Light I
                    if aov_type == RNDAOV_LIGHT_I:
                        print ("Subdata: Light ID (indirect):",aov[RNDAOV_LIGHT_ID])  
                        
                    # Custom
                    if aov_type == RNDAOV_CUSTOM:
                        print ("Subdata: Custom ID:",aov[RNDAOV_CUSTOM_IDS]," Visible After:", aov[RNDAOV_VISIBLE_AFTER])    
                        
                    # Cryptomatte
                    if aov_type == RNDAOV_CRYPTOMATTE:
                        print ("Subdata: Custom ID:",aov[RNDAOV_CRYPTO_TYPE])
                
        print ("--- OCTANERENDER ---")

    # 创建aov ==> ok
    def create_aov_shader(self, aov_tye: int = RNDAOV_ZDEPTH, aov_name: str = "") -> c4d.BaseShader :
        """
        Create a shader of octane aov.

        :param aov_tye: the aov int type, defaults to RNDAOV_ZDEPTH
        :type aov_tye: int, optional
        :param aov_name: the aov name, defaults to ""
        :type aov_name: str, optional 
        :return: the aov shader
        :rtype: c4d.BaseShader
        """
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")

        aov = c4d.BaseList2D(ID_OCTANE_RENDERPASS_AOV)
        # set
        aov[RNDAOV_TYPE] = aov_tye
        # read
        aov_type = aov[RNDAOV_TYPE]
        
        if aov_name == "":
            aov[RNDAOV_NAME] = AOV_SYMBOLS[aov_type]

        return aov
    
    # 将aov添加到vp ==> ok
    def add_aov(self, aov_shader: c4d.BaseList2D) -> c4d.BaseList2D:
        """
        Add the octane aov shader to Octane Render.

        :param aov_shader: the octane aov shader
        :type aov_shader: c4d.BaseList2D
        :return: the octane aov shader
        :rtype: c4d.BaseList2D
        """

        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        if not isinstance(aov_shader, c4d.BaseList2D):
            raise ValueError("Octane AOV must be a c4d.BaseList2D Object")
        
        # add a new port
        old_aovCnt: int = self.vp[SET_RENDERAOV_IN_CNT]
        #new_aovCnt: int = old_aovCnt + 1
        self.vp[SET_RENDERAOV_IN_CNT] += 1
        
        # insert octane_aov to new port
        try:
            self.vp.InsertShader(aov_shader)
        except:
            pass
        self.vp[SET_RENDERAOV_INPUT_0 + old_aovCnt] = aov_shader
        
        return aov_shader
    
    # 为aov添加属性 ==> ok
    def set_aov(self, aov_shader: c4d.BaseList2D , aov_id : int, aov_attrib)-> c4d.BaseShader :
        """
        A helper fucnction to set aov data.

        """
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        if not isinstance(aov_shader,c4d.BaseList2D):
            raise ValueError(f"Aov must be the {self.vpname} aov shader which is a BaseList2D")    
        if aov_shader[aov_id] is not None:
            aov_shader[aov_id] = aov_attrib
        return aov_shader
        
    # 删除最新的aov ==> ok
    def remove_last_aov(self):
        """
        Remove the last aov shader.

        """
        # index: Union[int,c4d.BaseList2D]
        
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        
        aovCnt: int = self.vp[SET_RENDERAOV_IN_CNT]
        self.vp[SET_RENDERAOV_IN_CNT] = aovCnt - 1
        
        # the last shader
        slot_shader = self.vp[SET_RENDERAOV_INPUT_0 + aovCnt - 1]
        
        # None
        if slot_shader == None:
            self.vp[SET_RENDERAOV_IN_CNT] = aovCnt - 1
            
        # shader  
        else:
            
            if slot_shader is not None:
                
                if isinstance(slot_shader, c4d.BaseList2D):
                    slot_shader.Remove()
                
            self.vp[SET_RENDERAOV_IN_CNT] = aovCnt - 1
    
    # 删除空的aov ==> ok
    def remove_empty_aov(self):
        """
        Romove all the empty aov shaders.
        
        """
        
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        
        aovCnt: int = self.vp[SET_RENDERAOV_IN_CNT]
        
        for i in range(0, aovCnt):
            slot_shader = self.vp[SET_RENDERAOV_INPUT_0 + i]
            
            # None 在最后
            if slot_shader is None:                
                self.vp[SET_RENDERAOV_IN_CNT] -= 1
                 
    # 删除全部aov ==> ok
    def remove_all_aov(self):
        """
        Remove all the aov shaders.

        """
        
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        
        aovCnt: int = self.vp[SET_RENDERAOV_IN_CNT]
        
        for i in range(0, aovCnt):
            slot_shader = self.vp[SET_RENDERAOV_INPUT_0 + i]
            
            if slot_shader is not None:
                
                if isinstance(slot_shader, c4d.BaseList2D):
                    slot_shader.Remove()
                
        self.vp[SET_RENDERAOV_IN_CNT] = 0      
                       
    # 按照Type删除aov ==> ok
    def remove_aov_type(self, aov_type: int):
        """
        Remove aovs of the given aov type.

        :param aov_type: the aov type to remove
        :type aov_type: int
        """
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        aovCnt = self.vp[SET_RENDERAOV_IN_CNT]        
        
        aovs: list[AOVData] = []

        for i in range(0, aovCnt):
            aov: c4d.BaseShader = self.vp[SET_RENDERAOV_INPUT_0+i]
            aovtype: int = aov[RNDAOV_TYPE]
            if aovtype == aov_type:
                aov.Remove()
            else:
                aovs.append(aov)
        
        # 清空input
        for i in range(0, aovCnt):
            self.vp[SET_RENDERAOV_INPUT_0+i] = None
        self.remove_empty_aov()
        
        # 重新链接aov shader
        for i in aovs:
            self.add_aov(i)  

    # 获取custom aov（id） ==> ok
    def get_custom_aov(self, customID: int = 1) -> c4d.BaseList2D | None:
        """
        Get the custom aov shader of given id.

        :param customID: the custom id, defaults to 1
        :type customID: int, optional
        :return: the aov shader
        :rtype: c4d.BaseList2D | None
        """
        est_aovs = self.get_aov(RNDAOV_CUSTOM)
        for aov in est_aovs:
            if aov[c4d.RNDAOV_CUSTOM_IDS] == customID - 1: # start at 0
                return aov
        else: return None

    # 添加custom aov（id） ==> ok
    def add_custom_aov(self, customID: int = 1) -> c4d.BaseList2D | None:
        """
        Add the custom aov shader of given id if it not existed.

        :param customID: the custom id, defaults to 1
        :type customID: int, optional
        :return: the aov shader
        :rtype: c4d.BaseList2D | None
        """
        if self.get_custom_aov(customID) is None:
            aov = self.create_aov_shader(RNDAOV_CUSTOM)            
            self.add_aov(aov)
            aov[c4d.RNDAOV_CUSTOM_IDS] = customID - 1
            return aov

    # 获取light aov（id） ==> ok
    def get_light_aov(self, lightID: int = 1) -> c4d.BaseList2D | None:
        """
        Get the light aov shader of given id.

        :param lightID: the light id, defaults to 1
        :type lightID: int, optional
        :return: the aov shader
        :rtype: c4d.BaseList2D | None
        """
        est_aovs = self.get_aov(RNDAOV_LIGHT)
        for aov in est_aovs:
            if aov[c4d.RNDAOV_LIGHT_ID] == lightID + 1: # start at 0
                return aov
        else: return None

    # 添加light aov（id） ==> ok
    def add_light_aov(self, lightID: int = 1) -> c4d.BaseList2D | None:
        """
        Add the light aov shader of given id if it not existed.

        :param lightID: the light id, defaults to 1
        :type lightID: int, optional
        :return: the aov shader
        :rtype: c4d.BaseList2D | None
        """
        if self.get_custom_aov(lightID) is None:
            aov = self.create_aov_shader(RNDAOV_LIGHT)            
            self.add_aov(aov)
            aov[c4d.RNDAOV_LIGHT_ID] = lightID + 1
            return aov

###  ==========  Material  ==========  ###

class NodeHelper:
    
    def __init__(self, document: c4d.documents.BaseDocument = None, material: c4d.BaseMaterial = None):
        if document is None:
            document: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
            self.doc = document
        if material is None:
            material = c4d.documents.GetActiveDocument().GetActiveMaterial()
            if material is None:
                pass
        self.material: c4d.BaseMaterial = material
        if self.material.GetType() not in OCTANE_MATERIALS:
            raise ValueError("This is not an Octane Material")

    # 获取所有shader ==> ok
    def GetAllNodes(self) -> list[c4d.BaseList2D] :
        """
        Get all nodes of the material in a list.

        Returns:
            list[c4d.BaseList2D]: A List of all find nodes

        """

        # The list.
        result: list = []

        start_shader = self.material.GetFirstShader()
        if not start_shader:
            raise RuntimeError("No shader found")
        
        for obj in iterate(start_shader):

            result.append(obj)

        # Return the object List.
        return result

    # 获取特定shader ==> ok
    def GetNodes(self, node_type: c4d.BaseList2D) -> Union[list[c4d.BaseList2D],c4d.BaseList2D]:
        """
        Get all nodes of given type of the material in a list.

        Returns:
            list[c4d.BaseList2D]: A List of all find nodes

        """

        # The list.
        result: list = []

        start_shader = self.material.GetFirstShader()
        if not start_shader:
            raise RuntimeError("No shader found")
        
        for obj in iterate(start_shader):
            if obj.CheckType(node_type):
                result.append(obj)
            
        return result

    # 刷新贴图 ==> ok
    def RefreshTextures(self):
        """
        Reload all the texture shader.

        """
        nodes: list[c4d.BaseList2D] = self.GetNodes(ID_OCTANE_IMAGE_TEXTURE)
        for node in nodes:
            node[c4d.IMAGETEXTURE_FORCE_RELOAD] = 1
            node.SetDirty(c4d.DIRTYFLAGS_ALL)
        #c4d.EventAdd()
    
    # 重置压缩 ==> ok
    def ResetCompression(self):
        """
        Reset all the texture shader compression.

        """
        nodes: list[c4d.BaseList2D] = self.GetNodes(ID_OCTANE_IMAGE_TEXTURE)
        for node in nodes:
            node[c4d.IMAGETEX_COMPR_FORMAT] = 0  # reset the compression
        c4d.EventAdd()

    # Nodes
    def AddShader(self, shaderID: int = None, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:        
        """
        Add a shader to the material of the given type and slot.

        """
        theNode = c4d.BaseList2D(shaderID)                  
        if parentNode:
                self.material[parentNode] = theNode                                     
        self.material.InsertShader(theNode)                        
        return theNode

    def AddTransform(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Transform shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_TRANSFORM, parentNode)
    
    def AddProjection(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Projection shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_TEXTURE_PROJECTION, parentNode)

    def AddMultiply(self, nodeA: c4d.BaseList2D, nodeB: c4d.BaseList2D, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Multiply shader to the given slot(option).

        """
        theNode = self.AddShader(ID_OCTANE_MULTIPLY_TEXTURE, parentNode)
        if nodeA:
            theNode[c4d.MULTIPLY_TEXTURE1] = nodeA
        if nodeB:
            theNode[c4d.MULTIPLY_TEXTURE2] = nodeB
        return theNode
    
    def AddSubtract(self, nodeA: c4d.BaseList2D, nodeB: c4d.BaseList2D, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Subtract shader to the given slot(option).

        """
        theNode = self.AddShader(ID_OCTANE_SUBTRACT_TEXTURE, parentNode)
        if nodeA:
            theNode[c4d.MULTIPLY_TEXTURE1] = nodeA
        if nodeB:
            theNode[c4d.MULTIPLY_TEXTURE2] = nodeB
        return theNode

    def AddMathAdd(self, nodeA: c4d.BaseList2D, nodeB: c4d.BaseList2D, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a MathAdd shader to the given slot(option).

        """
        theNode = self.AddShader(ID_OCTANE_ADD_TEXTURE, parentNode)
        if nodeA:
            theNode[c4d.MULTIPLY_TEXTURE1] = nodeA
        if nodeB:
            theNode[c4d.MULTIPLY_TEXTURE2] = nodeB
        return theNode

    def AddMix(self, mix_amount: float, nodeA: c4d.BaseList2D, nodeB: c4d.BaseList2D, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Mix shader to the given slot(option).

        """
        theNode = self.AddShader(ID_OCTANE_MIXTEXTURE, parentNode)        
        if mix_amount:
            theNode[c4d.MIXTEX_AMOUNT_FLOAT] = mix_amount
        if nodeA:
            theNode[c4d.MULTIPLY_TEXTURE1] = nodeA
        if nodeB:
            theNode[c4d.MULTIPLY_TEXTURE2] = nodeB
        return theNode

    def AddInvert(self, imageTexture: c4d.BaseList2D, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Invert shader to the given slot(option).

        """
        theNode = self.AddShader(ID_OCTANE_INVERT_TEXTURE, parentNode)
        if imageTexture:
            theNode[c4d.INVERT_TEXTURE] = imageTexture       
        return theNode

    def AddFloat(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Float shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_FLOAT_TEXTURE, parentNode)

    def AddRGB(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a RGB shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_RGBSPECTRUM, parentNode)

    def AddImageTexture(self, texturePath: str = None, nodeName: str = None, isFloat: bool = True, gamma: int = 1,
                           invert: bool = False, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a ImageTexture shader to the given slot(option).

        """
        
        theNode = self.AddShader(ID_OCTANE_IMAGE_TEXTURE, parentNode)

        if texturePath:                
            theNode[c4d.IMAGETEXTURE_FILE] = texturePath
            
        theNode[c4d.IMAGETEXTURE_INVERT] = invert
        theNode[c4d.IMAGETEXTURE_GAMMA] = gamma
        
        if isFloat:
            theNode[c4d.IMAGETEXTURE_MODE] = 1 # 1 = Float and 0 is Normal (Color)
        else:
            theNode[c4d.IMAGETEXTURE_MODE] = 0
        
        if nodeName:
            theNode.SetName(nodeName)
        return theNode

    def AddCC(self, imageTexture: c4d.BaseList2D = None, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Color Correction shader to the given slot(option).

        """
        theNode = self.AddShader(ID_OCTANE_COLORCORRECTION, parentNode)
        if imageTexture:
            theNode[c4d.COLORCOR_TEXTURE_LNK] = imageTexture       
        return theNode

    def AddGradient(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Gradient shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_GRADIENT_TEXTURE, parentNode)

    def AddFalloff(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Falloff shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_FALLOFFMAP, parentNode)

    def AddDirt(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Dirt shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_DIRT_TEXTURE, parentNode)

    def AddCurvature(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Curvature shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_CURVATURE_TEX, parentNode)

    def AddNoise4D(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Maxon Noise shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_C4DNOISE_TEX, parentNode)

    def AddNoise(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Octane Noise shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_NOISE_TEXTURE, parentNode)

    def AddTriplanar(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Triplanar shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_TRIPLANAR, parentNode)

    def AddDisplacement(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Displacement shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_DISPLACEMENT, parentNode)

    def AddBlackbodyEmission(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Blackbody Emission shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_BLACKBODY_EMISSION, parentNode)

    def AddTextureEmission(self, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Texture Emission shader to the given slot(option).

        """
        return self.AddShader(ID_OCTANE_TEXTURE_EMISSION, parentNode)

    def AddTextureTree(self, texturePath: str = None, nodeName: str = None, isFloat: bool = True, gamma: int = 1,
                           invert: bool = False, parentNode: c4d.BaseList2D = None) -> c4d.BaseList2D:
        """
        Add a Texture + Color Correction + Gradient shader tree to the given slot(option).

        """
        
        theNode = self.AddShader(ID_OCTANE_IMAGE_TEXTURE, parentNode)

        if texturePath:                
            theNode[c4d.IMAGETEXTURE_FILE] = texturePath
            
        theNode[c4d.IMAGETEXTURE_INVERT] = invert
        theNode[c4d.IMAGETEXTURE_GAMMA] = gamma
        
        if isFloat:
            theNode[c4d.IMAGETEXTURE_MODE] = 1 # 1 = Float and 0 is Normal (Color)
        else:
            theNode[c4d.IMAGETEXTURE_MODE] = 0
        
        if nodeName:
            theNode.SetName(nodeName)
            
        gradientNode = self.AddGradient(parentNode)
        ccNode = self.AddCC(theNode)
        gradientNode[c4d.GRADIENT_TEXTURE_LNK] = ccNode
        ccNode[c4d.COLORCOR_TEXTURE_LNK] = theNode
        
        return theNode


class MaterialHelper(NodeHelper):

    def __init__(self, document: c4d.documents.BaseDocument = None):
        if document is None:
            document: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
        self.doc: c4d.documents.BaseDocument = document
            
        self.material: c4d.BaseMaterial = None

    @property
    def IsOctaneMaterial(self):
        if self.material is None: return False
        if self.material.GetType() in OCTANE_MATERIALS:
            return True
        else: return False

    # 创建基础材质 ==> ok
    def CreateBasicMaterial(self, isMetal: bool = False, matType: int = MAT_TYPE_UNIVERSAL, matName: str = None) -> c4d.BaseMaterial:
        """
        Create an Octane Basic(classic) material of given type and name.
        """

        # Basic Octane Mat Type 
        material = c4d.BaseMaterial(ID_OCTANE_BASE_MATERIAL)            
        if material is None:
            raise ValueError("Cannot create a BaseMaterial")

        if isMetal:
            material[c4d.OCT_MATERIAL_TYPE] = MAT_TYPE_UNIVERSAL
            material.SetName(MetallicName)
            material[c4d.OCT_MAT_BRDF_MODEL] = 6 # ggx energy preserving, for annistropy
            material[c4d.OCT_MAT_USE_COLOR] = c4d.Vector(0,0,0) # albedo black
            
        else:
            try:
                material[c4d.OCT_MATERIAL_TYPE] = matType
            except:
                material[c4d.OCT_MATERIAL_TYPE] = MAT_TYPE_UNIVERSAL                    


            material[c4d.OCT_MAT_BRDF_MODEL] = 6 # ggx energy preserving
            material[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.2
            material[c4d.OCT_MAT_USE_MATERIAL_LAYER] = True

            # Def
            if not matName:
                
                if matType == MAT_TYPE_DIFFUSE:
                    material.SetName(DiffuseName)
                elif matType == MAT_TYPE_GLOSSY:
                    material.SetName(GlossyName)                
                elif matType == MAT_TYPE_SPECULAT:
                    material[c4d.OCT_MATERIAL_TYPE] = BRDF_OCTANE
                    material.SetName(SpecularName)
                elif matType == MAT_TYPE_UNIVERSAL:
                    material.SetName(UniversalName)
                elif matType == MAT_TYPE_METALLIC:
                    material.SetName(MetallicName)
                elif matType == MAT_TYPE_TOON:
                    material.SetName(ToonName)
            else:
                material.SetName(matName)

        # Update material
        self.material = material         
        self.material.Update(True, True)
        return self.material

    # 创建合成材质 ==> ok
    def CreateComposite(self, matName: str = None, compNum: int = 2) -> c4d.BaseMaterial:
        """
        Create an Octane Composite material of given type and name.
        """
        
        try:
            material = c4d.BaseMaterial(ID_OCTANE_COMPOSITE_MATERIAL)
            if material is None:
                raise ValueError("Cannot create a BaseMaterial")
            
            if matName:
                material.SetName(matName)
            else:
                material.SetName('Composite')
                
            material[c4d.BLENDMAT_NUM_OF_MATERIALS] = compNum
            
            for i ,subnode in enumerate(compNum): 
                subnode = c4d.BaseList2D(SUBMaterialNodeID)
                material.InsertShader(subnode)
                material[1300 + i] = subnode
            
            # Update material
            material.Update(True, True)
            return material
            
        except :
            ValueError("Cannot create Octane Material.")

    # 创建Standard Surface材质 ==> ok
    def CreateStandardMaterial(self, isMetal: bool = False, matName: str = None) -> c4d.BaseMaterial:
        """
        Create an Octane Standard Surface material of given type and name.
        """
        try:
            # Basic Octane Mat Type 
            material = c4d.BaseMaterial(ID_OCTANE_STANDARD_SURFACE)            
            if material is None:
                raise ValueError("Cannot create a BaseMaterial") 
            
            material[c4d.STDMAT_BASELAYER_WEIGHT_FLOAT] = 1.0 # albedo
            material[c4d.STDMAT_BASELAYER_DIFROUGH_VAL] = 0.0 # albedo roughness
            material[c4d.STDMAT_SPECULARLAYER_ROUGH_VAL] = 0.2 # specular roughness
            
            if isMetal:
                material[c4d.STDMAT_BASELAYER_METALNESS_VAL] = 1.0
            else:
                material[c4d.STDMAT_BASELAYER_METALNESS_VAL] = 0.0
            
            if not matName:
                material.SetName('Standard Surface')
            else:
                material.SetName(matName)
                
            # Update material
            material.Update(True, True)
            self.material = material
            return self.material
        
        except :
            ValueError("Cannot create Octane Material.")

    # 插入 ==> ok
    def InsertMaterial(self):
        """
        Insert the material to the document.
        """
        if self.material is None: return False
        self.material.Update(True, True)
        self.doc.InsertMaterial(self.material)
        return self.material

    # 刷新材质 ==> ok
    def Refresh(self):
        """
        Refresh thumbnail.
        """
        self.material.Update(True, True)

    # 设置激活 ==> ok
    def SetActive(self):
        """
        Set the material active in the document.
        """
        if self.material is not None:
            self.doc.SetActiveMaterial(self.material)
    
    # 创建材质 ==> ok
    def SetupTextures(self):
        """
        Setup a pbr material with given or selected texture.
        """
        texpack = node_helper.TexPack()
        data_list = texpack.get_texture_data()
        tex_data = data_list[0]
        mat_name = data_list[1]
        
        isSpecularWorkflow = False
        if 'Specular' in list(tex_data.keys()):
            isSpecularWorkflow = True            
        
        try:
            # 
            if "Diffuse" in tex_data:
                albedoNode = self.AddImageTexture(texturePath=tex_data['Diffuse'], nodeName="Albedo", isFloat=False, gamma=2.2)
                if albedoNode:
                    ccAlbedoNode = self.AddCC(albedoNode)
                    if "AO" in tex_data:
                        aoNode = self.AddImageTexture(texturePath=tex_data['AO'], nodeName="AO")
                        if aoNode:
                            self.AddMultiply(ccAlbedoNode, aoNode, c4d.OCT_MATERIAL_DIFFUSE_LINK)
                    else:
                        self.material[c4d.OCT_MATERIAL_DIFFUSE_LINK] = ccAlbedoNode
            
            if isSpecularWorkflow:
                if "Specular" in tex_data:
                    self.AddImageTexture(texturePath=tex_data['Specular'], nodeName="Specular",
                                         isFloat=False, gamma=2.2, parentNode=c4d.OCT_MATERIAL_SPECULAR_LINK)
                
                if "Glossiness" in tex_data:
                    glossNode = self.AddImageTexture(texturePath=tex_data['Glossiness'], nodeName="Gloss")
                    if glossNode:
                        ccGlossNode = self.AddCC(glossNode, parentNode=c4d.OCT_MATERIAL_ROUGHNESS_LINK)
                elif "Roughness" in tex_data:
                    roughnessNode = self.AddImageTexture(texturePath=tex_data['Roughness'], nodeName="Roughness")
                    if roughnessNode:
                        ccRoughnessNode = self.AddCC(roughnessNode, parentNode=c4d.OCT_MATERIAL_ROUGHNESS_LINK)
                        #ccRoughnessNode[c4d.COLORCOR_TEXTURE_LNK] = roughnessNode

            else:
                if "Metalness" in tex_data:
                    self.AddImageTexture(texturePath=tex_data['Metalness'], nodeName="Metalness", parentNode=c4d.OCT_MAT_SPECULAR_MAP_LINK)
                if "Roughness" in tex_data:
                    roughnessNode = self.AddImageTexture(texturePath=tex_data['Roughness'], nodeName="Roughness")
                    if roughnessNode:
                        ccRoughnessNode = self.AddCC(roughnessNode,parentNode=c4d.OCT_MATERIAL_ROUGHNESS_LINK)

                elif "Glossiness" in tex_data:
                    glossNode = self.AddImageTexture(texturePath=tex_data['Glossiness'], nodeName="Gloss")
                    if glossNode:
                        ccGlossNode = self.AddCC(glossNode,parentNode=c4d.OCT_MATERIAL_ROUGHNESS_LINK)
                        # self.material[c4d.OCT_MATERIAL_ROUGHNESS_LINK] = ccGlossNode
                
            if "Bump" in tex_data:  
                self.AddImageTexture(texturePath=tex_data['Bump'], nodeName="Bump",parentNode=c4d.OCT_MATERIAL_BUMP_LINK)

            if "Normal" in tex_data:  
                self.AddImageTexture(texturePath=tex_data['Normal'], nodeName="Normal", isFloat=False, gamma=1, parentNode=c4d.OCT_MATERIAL_NORMAL_LINK)
            
            if "Displacement" in tex_data:
                displacementNode = self.AddDisplacement(c4d.OCT_MATERIAL_DISPLACEMENT_LINK)
                if displacementNode:
                    displacementSlotName = c4d.DISPLACEMENT_TEXTURE
                    displacementNode[displacementSlotName] = self.AddImageTexture(texturePath=tex_data['Displacement'], nodeName="Displacement")

            if "Alpha" in tex_data:  
                self.AddImageTexture(texturePath=tex_data['Alpha'], nodeName="Alpha", parentNode=c4d.OCT_MATERIAL_OPACITY_LINK)

            if "Translucency" in tex_data:  
                self.AddImageTexture(texturePath=tex_data['Translucency'], nodeName="Translucency", gamma=2.2, parentNode=c4d.OCT_MATERIAL_TRANSMISSION_LINK)
                self.material[c4d.UNIVMAT_TRANSMISSION_TYPE] = 1
            elif "Transmission" in tex_data:  
                self.AddImageTexture(texturePath=tex_data['Transmission'], nodeName="Transmission", gamma=1, parentNode=c4d.OCT_MATERIAL_TRANSMISSION_LINK)
                self.material[c4d.UNIVMAT_TRANSMISSION_TYPE] = 1
            self.material.SetName(mat_name)
            
        except Exception as e:
            raise RuntimeError ("Unable to setup texture")    

    # 统一缩放 ==> ok
    def UniTransform(self):
        """
        Add a Transform node to all the Image nodes.
        """
        images = self.GetNodes(ID_OCTANE_IMAGE_TEXTURE)
        trans_node = self.AddTransform()
        for image in images:
            image[c4d.IMAGETEXTURE_TRANSFORM_LINK] = trans_node

###  ==========  Scene  ==========  ###

class SceneHelper:
    """
    Helper class for Octane Secne Objects.
    """
    
    def __init__(self, document: c4d.documents.BaseDocument = None):
        if document is None:
            document: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
        self.doc: c4d.documents.BaseDocument = document

    def _add_unseltag(self, node: c4d.BaseObject):
        if not isinstance(node,c4d.BaseObject):
            raise ValueError("Must be a BaseObject")
        unseltag = c4d.BaseTag(440000164) # Interaction Tag
        unseltag[c4d.INTERACTIONTAG_SELECT] = True # INTERACTIONTAG_SELECT
        node.InsertTag(unseltag) # insert tag 

    ### Light ###
    
    def add_hdr_dome(self, texture_path: str = None, visible: bool = True) -> list[c4d.BaseTag, c4d.BaseObject]:
        """
        Add a texture (hdr) dome light to the scene.

        :param texture_path: HDR image path
        :type texture_path: str
        :param unselect: True if the dome can not be select, defaults to True
        :type unselect: bool, optional
        :param mode: True to primray mode,othervise to visible, defaults to True
        :type mode: bool, optional
        :return: the image texture node and the sky object
        :rtype: list[c4d.BaseTag, c4d.BaseObject]
        """
        osky = c4d.BaseObject(c4d.Osky)
        env = osky.MakeTag(ID_OCTANE_ENVIRONMENT_TAG)
        image = c4d.BaseList2D(ID_OCTANE_IMAGE_TEXTURE)
        env.InsertShader(image)
        env[c4d.ENVIRONMENTTAG_TEXTURE] = image
        self.doc.InsertObject(osky)
        osky.SetName('Octane HDR Dome')
        
        if texture_path:        
            env = [i for i in osky.GetTags() if i.CheckType(ID_OCTANE_ENVIRONMENT_TAG)][0]
            img = env[c4d.ENVIRONMENTTAG_TEXTURE]
            img[c4d.IMAGETEXTURE_FILE] = texture_path
            self.doc.SetActiveTag(env)
            
        if visible:
            env[c4d.ENVTAG_SLOT] = 1
        else:
            env[c4d.ENVTAG_SLOT] = 0


        return env

    def add_rgb_dome(self, rgb: c4d.Vector = c4d.Vector(0,0,0)) -> list[c4d.BaseTag, c4d.BaseObject]:
        """
        Add a rgb dome light to the scene.

        :param rgb: rgb color value
        :type rgb: c4d.Vector
        :param unselect: True if the dome can not be select, defaults to True
        :type unselect: bool, optional
        :param mode: True to primray mode,othervise to visible, defaults to True
        :type mode: bool, optional
        :return: the rgb node and the sky object
        :rtype: list[c4d.BaseTag, c4d.BaseObject]
        """
        osky = c4d.BaseObject(c4d.Osky)
        env = osky.MakeTag(ID_OCTANE_ENVIRONMENT_TAG)
        rgb_tex = c4d.BaseList2D(ID_OCTANE_RGBSPECTRUM)
        env.InsertShader(rgb_tex)
        env[c4d.ENVIRONMENTTAG_TEXTURE] = rgb_tex
        rgb_tex[c4d.RGBSPECTRUMSHADER_COLOR] = rgb
        self.doc.InsertObject(osky)
        osky.SetName('Octane RGB Dome')
        return env

    def add_dome_rig(self, texture_path: str = None, rgb: c4d.Vector = c4d.Vector(0,0,0)):
        """
        Add a HDR and visible dome light folder.

        :param texture_path: hdr image path
        :type texture_path: str
        :param unselect: True if the dome can not be select, defaults to True
        :type unselect: bool, optional
        """
        hdr_dome = self.add_hdr_dome(texture_path).GetObject()
        black_dome = self.add_rgb_dome(rgb).GetObject()
        null = c4d.BaseObject(c4d.Onull)
        null.SetName("Environment")
        null[c4d.ID_BASELIST_ICON_FILE] = '1052837'
        null[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 1
        null[c4d.ID_BASELIST_ICON_COLOR] = c4d.Vector(0.008, 0.659, 0.902)
        doc.InsertObject(null)
        hdr_dome.InsertUnder(null)
        black_dome.InsertUnder(null)
        hdr_dome.DelBit(c4d.BIT_ACTIVE)
        black_dome.DelBit(c4d.BIT_ACTIVE)
        null.SetBit(c4d.BIT_ACTIVE)
        # Unfold the null if it is fold
        if null.GetNBit(c4d.NBIT_OM1_FOLD) == False:
            null.ChangeNBit(c4d.NBIT_OM1_FOLD, c4d.NBITCONTROL_TOGGLE)

    def add_light(self, power: float = 4.0, light_name: str = 'Octane Light', texture_path: str = None, distribution_path: str = None, visibility: bool = False):
        """
        Add an Octane light to the secne.

        """
        # 新建灯光
        light = c4d.BaseObject(c4d.Olight)
        light[c4d.LIGHT_TYPE] = 8
        #light[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 1
        
        # 灯光强度
        octag = c4d.BaseTag(ID_OCTANE_LIGHT_TAG)
        light.InsertTag(octag)
        octag[c4d.LIGHTTAG_POWER] = power
        
        # 可见性控制 （1=可见，0=不可见） 默认不可见。 如果需要可以设置
        if not visibility:
            octag[c4d.LIGHTTAG_OPACITY] = 0.0
            octag[c4d.LIGHTTAG_VIS_CAM] = False 
            
        # Texture
        if texture_path:
            imageTextureNode_tex = c4d.BaseList2D(ID_OCTANE_IMAGE_TEXTURE)
            octag.InsertShader(imageTextureNode_tex)
            octag[c4d.LIGHTTAG_EFFIC_OR_TEX] = imageTextureNode_tex
            imageTextureNode_tex[c4d.IMAGETEXTURE_FILE] = texture_path
        
        # Distribution
        if distribution_path:
            imageTextureNod_dis = c4d.BaseList2D(ID_OCTANE_IMAGE_TEXTURE)
            octag.InsertShader(imageTextureNod_dis)
            octag[c4d.LIGHTTAG_DISTRIBUTION] = imageTextureNod_dis
            imageTextureNod_dis[c4d.IMAGETEXTURE_FILE] = distribution_path
        
        # Name
        light.SetName(light_name)
        # Insert light into document.
        self.doc.InsertObject(light)
        return light
   
    def add_light_texture(self, light_tag: c4d.BaseTag = None,  texture_path: str = None, distribution_path: str = None) -> c4d.BaseTag :
        """
        Add textures to given Octane light tag.

        """
        if not light_tag.CheckType(ID_OCTANE_LIGHT_TAG):
            raise ValueError("This is not an Octane light tag")
        
        # Texture
        if texture_path:
            imageTextureNode_tex = c4d.BaseList2D(ID_OCTANE_IMAGE_TEXTURE)
            light_tag.InsertShader(imageTextureNode_tex)
            light_tag[c4d.LIGHTTAG_EFFIC_OR_TEX] = imageTextureNode_tex
            imageTextureNode_tex[c4d.IMAGETEXTURE_FILE] = texture_path
        
        # Distribution
        if distribution_path:
            imageTextureNod_dis = c4d.BaseList2D(ID_OCTANE_IMAGE_TEXTURE)
            light_tag.InsertShader(imageTextureNod_dis)
            light_tag[c4d.LIGHTTAG_DISTRIBUTION] = imageTextureNod_dis
            imageTextureNod_dis[c4d.IMAGETEXTURE_FILE] = distribution_path        

        return light_tag
        
    def add_ies(self, power: float = 100.0, light_name: str = 'Octane IES', ies_path: str = None, visibility: bool = False):
        """
        Add an Octane ies light to the secne.

        """
        ies = self.add_light(power, light_name, texture_path=None, distribution_path = ies_path, visibility=visibility)
        return ies
    
    def add_gobo(self, power: float = 100.0, light_name: str = 'Octane Gobo', gobo_path: str = None, visibility: bool = False):
        """
        Add an Octane gobo light to the secne.

        """
        gobo = self.add_light(power, light_name, texture_path=None, distribution_path = gobo_path, visibility=visibility)
        return gobo
    
    def add_sun(self, power: float = 1.0, light_name: str = 'Octane Sun', mix_sky: bool = False, imp_samp: bool = False):
        """
        Add an Octane sun light to the secne.

        """
        # 新建灯光
        light = c4d.BaseObject(c4d.Olight)
        light[c4d.LIGHT_TYPE] = 3 # infinite
        light[c4d.DAYLIGHTTAG_POWER] = power
        # Sun Expression
        sun_exp = c4d.BaseTag(5678) # Sun Expression
        light.InsertTag(sun_exp)
        # Octane Sun tag
        octane_sun = c4d.BaseTag(ID_OCTANE_DAYLIGHT_TAG) # Sun
        light.InsertTag(octane_sun)
        if mix_sky:
            light[c4d.DAYLIGHTTAG_USESKY] = mix_sky
        
        if imp_samp: # Importance sampling, need to add the sun to the scene to be able to sample it.
            light[c4d.DAYLIGHTTAG_IMPSAMPLING] = imp_samp
        
        # Name
        light.SetName(light_name)
        self.doc.InsertObject(light)
        return light

    def add_light_modifier(self, light: c4d.BaseObject, target: c4d.BaseObject|bool = None, gsg_link: bool = False, rand_color: bool = False, seed: int = 0):
        """
        Add some modify tagsto given Octane light tag.

        """
        if not isinstance(light,c4d.BaseObject):
            raise ValueError("Need a light BaseObject")
        
        # 新建目标标签
        if target:
            mbtag = c4d.BaseTag(5676) # target
            doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, mbtag)
            if isinstance(target, c4d.BaseObject):
                mbtag[c4d.TARGETEXPRESSIONTAG_LINK] = target
            elif isinstance(target, bool):
                pass
            light.InsertTag(mbtag)
        
        # GSG HDR LINK
        if gsg_link:
            try:            
                gsglink = c4d.plugins.FindPlugin(1037662, type=c4d.PLUGINTYPE_TAG)
                if gsglink:
                    linktag = c4d.BaseTag(1037662)
                    light.InsertTag(linktag)
                    linktag[2001] = ''
            except:
                pass
        
        # 随机颜色
        if rand_color:
            light[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 1
            
            if seed == 0:
                randcolor = c4d.Vector(*generate_random_color(1))
            else:
                random.seed(seed)
                randcolor = generate_random_color(1)
            light[c4d.ID_BASELIST_ICON_COLOR] = randcolor
            
        return light

    ### Tag ###

    def add_object_tag(self, node: c4d.BaseObject, layerID: int = 1) -> c4d.BaseTag:
        """
        Add an object tag to the given object.

        :param node: the object
        :type node: c4d.BaseObject
        :return: the octane object tag
        :rtype: c4d.BaseTag
        """
        
        if not isinstance(node, c4d.BaseObject):
            raise ValueError("Only accept c4d.BaseObject")
        atag = c4d.BaseTag(ID_OCTANE_OBJECTTAG)
        atag[c4d.OBJECTTAG_LAYERID] = layerID
        node.InsertTag(atag)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, atag)
        
        return atag

    def add_objects_tag(self, nodes: list[c4d.BaseObject]) -> None:
        """
        Add object tags to the given objects(enumerate).

        :param node: the object list
        :type node: c4d.BaseObject
        """
        
        if not isinstance(nodes, list):
            raise ValueError("Only accept c4d.BaseObject list")
        for node in nodes:
            atag = c4d.BaseTag(ID_OCTANE_OBJECTTAG)
            atag[c4d.OBJECTTAG_LAYERID] = nodes.index(node)+1
            atag[c4d.OBJECTTAG_INSTANCE_ID] = nodes.index(node)+1
            atag[c4d.OBJECTTAG_BAKEID] = nodes.index(node)+1
            atag[c4d.OBJTAG_OBJ_COLOR] = c4d.Vector(*generate_random_color(1))
            atag[c4d.ID_BASELIST_NAME] = node.GetName()
            node.InsertTag(atag)
            self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,atag)

    def add_custom_aov_tag(self, node: c4d.BaseObject, aovID: int = 1)-> c4d.BaseTag:
        """
        Add an object tag of given custom aov id to the given object.

        :param node: the object
        :type node: c4d.BaseObject
        :return: the octane object tag
        :rtype: c4d.BaseTag
        """
        if not isinstance(node, c4d.BaseObject):
            raise ValueError("Only accept c4d.BaseObject")
        atag = c4d.BaseTag(ID_OCTANE_OBJECTTAG)
        atag[c4d.OBJECTTAG_CUSTOM_AOV] = aovID
        node.InsertTag(atag)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, atag)
        
        return atag
    
    def add_camera_tag(self, node: c4d.CameraObject) -> c4d.BaseTag:
        """
        Add an camera tag to the given camera.

        :param node: the object
        :type node: c4d.BaseObject
        :return: the octane camera tag
        :rtype: c4d.BaseTag
        """
        
        if not isinstance(node, c4d.CameraObject):            
            raise ValueError("Only accept c4d Camera Object")
        if node.CheckType(c4d.Ocamera):
            atag = c4d.BaseTag(ID_OCTANE_CAMERATAG)                
            node.InsertTag(atag)
            self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, atag)
                        
        return atag

    ### Object ###

    def add_scatter(self, generator_node: c4d.BaseObject, scatter_nodes: list[c4d.BaseObject] = None,
                    vertex: c4d.BaseTag = None, count: int = 1000) -> c4d.BaseList2D:
        """
        Add a scatter object of given generator_node and scatter_nodes.
        """
        # __init pram__
        ModifierID = ID_SCATTER_OBJECT
        ModifierName = 'Scatter : '  # Modifier Name
        seed = random.randint(0,9999)
        
        pos = generator_node.GetMg()  # The object’s world matrix.
        objName = generator_node.GetName() # Store select obj Name
        # Modifier config
        Modifier = c4d.BaseObject(ModifierID) #  ID
        #  Config settings                
        Modifier[c4d.INSTANCER_DISTR_TYPE] = 1 # Set surface mode
        Modifier[c4d.INSTANCER_SURFACE] = generator_node
        Modifier[c4d.INSTANCER_NOISE_SEED] = seed
        Modifier[c4d.INSTANCER_COUNT] = count
        
        if vertex is not None:
            Modifier[c4d.INSTANCER_DISTR_VERTEXMAP] = vertex
            
        # Commen
        Modifier.SetName(ModifierName + objName) # Set Name to obj name + Modifier Name
        Modifier.InsertAfter(generator_node) # Insert after seleted obj in obj manager / Keep same level
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,Modifier) # Undo
        Modifier.SetMg(pos) # Set the world (global) matrix.
        
        if scatter_nodes is not None:
            # make child
            for child in scatter_nodes:
                child.InsertUnderLast(Modifier)
        doc.SetActiveObject(Modifier, c4d.SELECTION_NEW)
        #_reset_local_coordinates(node) # reset local coordinates
        # Unfold the null if it is fold
        if Modifier.GetNBit(c4d.NBIT_OM1_FOLD) == False:
            Modifier.ChangeNBit(c4d.NBIT_OM1_FOLD, c4d.NBITCONTROL_TOGGLE)
            
        return Modifier
        
    def add_vdb(self, vdb_path: str = "", animation: bool = False):
        """ 
        Add a vdb loader object with the given path to the scene.
        """
        vdb = c4d.BaseObject(ID_VOLUMEOBJECT) # Create the object.
        vdb.SetName('Octane Vdb') # Set name.
        vdb[10031] = 2 # loader
        vdb[c4d.VOLUMEOBJECT_VDB_FILE] = vdb_path
        if animation: # Animation.
            c4d.CallButton(vdb, c4d.VOLUMEOBJECT_VDB_SEQ_CALC)
        vdb_obj = self.doc.InsertObject(vdb)
        return vdb_obj

# to be move on...