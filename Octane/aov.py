# coding=utf-8

import c4d
import re
from typing import Iterator

from ..constants import *
from ..utils import iterate, GetVideoPost

class AOVHelper:

    """
    Custom helper to modify Arnold AOV(Driver).
    """

    def __init__(self, vp: c4d.documents.BaseVideoPost = None):
        
        if isinstance(vp, c4d.documents.BaseVideoPost):
            if vp.GetType() == int(ID_OCTANE):
                self.doc = vp.GetDocument()
                self.vp: c4d.documents.BaseVideoPost = vp
                self.vpname: str = self.vp.GetName()

        elif vp is None:
            self.doc: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
            self.vp: c4d.documents.BaseVideoPost = GetVideoPost(self.doc, ID_OCTANE)
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
    def get_aov_data(self) -> list[c4d.BaseContainer]:
        """
        Get all aov data in a list of BaseContainer.
        
        Parameters
        ----------        
        :return: the data list
        :rtype: Union[list[c4d.BaseContainer], None]
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
            #raise RuntimeError("No shader found")
            return result
        for obj in iterate(start_shader):
            if obj[RNDAOV_TYPE] != aov_type:
                continue
            result.append(obj)

        return result

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
    def create_aov_shader(self, aov_type: int = RNDAOV_ZDEPTH, aov_name: str = "") -> c4d.BaseShader :
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
        aov[RNDAOV_TYPE] = aov_type
        # read
        aov_type = aov[RNDAOV_TYPE]
        
        if aov_name is None:
            aov[RNDAOV_NAME] = AOV_SYMBOLS[aov_type]
        else:
            aov[RNDAOV_NAME] = aov_name

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

        # progess aov count
        if self.vp[SET_RENDERAOV_IN_CNT] is None:
            self.vp[SET_RENDERAOV_IN_CNT] = 0

        # new_aovCnt: int = old_aovCnt + 1
        self.vp[SET_RENDERAOV_IN_CNT] += 1
        
        # insert octane_aov to new port
        try:
            self.vp.InsertShader(aov_shader)
            self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,aov_shader)
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
        
        aovs: list = []

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
    def get_custom_aov(self, customID: int = 1) -> c4d.BaseList2D:
        """
        Get the custom aov shader of given id.

        :param customID: the custom id, defaults to 1
        :type customID: int, optional
        :return: the aov shader
        :rtype: c4d.BaseList2D
        """
        est_aovs = self.get_aov(RNDAOV_CUSTOM)
        for aov in est_aovs:
            if aov[c4d.RNDAOV_CUSTOM_IDS] == customID - 1: # start at 0
                return aov
        else: return None

    # 添加custom aov（id） ==> ok
    def add_custom_aov(self, customID: int = 1) -> c4d.BaseList2D:
        """
        Add the custom aov shader of given id if it not existed.

        :param customID: the custom id, defaults to 1
        :type customID: int, optional
        :return: the aov shader
        :rtype: c4d.BaseList2D
        """
        if self.get_custom_aov(customID) is None:
            aov = self.create_aov_shader(RNDAOV_CUSTOM)            
            self.add_aov(aov)
            aov[c4d.RNDAOV_CUSTOM_IDS] = customID - 1
            return aov

    # 获取light aov（id） ==> ok
    def get_light_aov(self, lightID: int = 1) -> c4d.BaseList2D:
        """
        Get the light aov shader of given id.

        :param lightID: the light id, defaults to 1
        :type lightID: int, optional
        :return: the aov shader
        :rtype: c4d.BaseList2D
        """
        est_aovs = self.get_aov(RNDAOV_LIGHT)
        if est_aovs is None: return None
        for aov in est_aovs:
            if aov[c4d.RNDAOV_LIGHT_ID] == lightID + 1: # start at 0
                return aov
        else: return None

    # 添加light aov（id） ==> ok
    def add_light_aov(self, lightID: int = 1, lightName: str = None) -> c4d.BaseList2D:
        """
        Add the light aov shader of given id if it not existed.

        :param lightID: the light id, defaults to 1
        :type lightID: int, optional
        :return: the aov shader
        :rtype: c4d.BaseList2D
        """
        if self.get_light_aov(lightID) is None:
            aov = self.create_aov_shader(RNDAOV_LIGHT, lightName)            
            self.add_aov(aov)
            aov[c4d.RNDAOV_LIGHT_ID] = lightID + 1
            return aov

    # 删除light aov（id） ==> ok
    def remove_light_aov(self, lightID: int = 1) -> None:
        """
        Add the light aov shader of given id if it not existed.

        :param lightID: the light id, defaults to 1
        :type lightID: int, optional
        :return: the aov shader
        :rtype: c4d.BaseList2D
        """
        est_aovs = self.get_aov(RNDAOV_LIGHT)
        if est_aovs is None: return None
        for aov in est_aovs:
            if aov[c4d.RNDAOV_LIGHT_ID] == lightID + 1: # start at 0
                aov.Remove()
        self.remove_empty_aov()
        return None

__all__ = [
    "AOVHelper"
]
