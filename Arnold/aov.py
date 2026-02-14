# coding=utf-8

import c4d
from typing import Union,Optional

from ..constants import *
from . material import MaterialHelper
from ..utils import get_nodes, iter_node, GetVideoPost

class AOVHelper:

    """
    Custom helper to modify Arnold AOV(Driver).
    """

    def __init__(self, vp: c4d.documents.BaseVideoPost = None):
        
        if isinstance(vp, c4d.documents.BaseVideoPost):
            if vp.GetType() == int(ID_ARNOLD):
                self.doc = vp.GetDocument()
                self.vp: c4d.documents.BaseVideoPost = vp
                self.vpname: str = self.vp.GetName()

        elif vp is None:
            self.doc: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
            self.vp: c4d.documents.BaseVideoPost = GetVideoPost(self.doc, ID_ARNOLD)
            self.vpname: str = self.vp.GetName()

    def __str__(self) -> str:
        return (f'<Class> {__class__.__name__} with videopost named {self.vpname}')

    def _get_aov_children(self, node: c4d.BaseObject) -> list[c4d.BaseObject]:
        res: list = []
        for node in iter_node(node, False, False):
            if node.GetName() in CDTOA_AOVTYPES:
                res.append(node)
        return res

    # 根据类型查找driver ==> ok
    def get_driver(self, driverType: str = None ) -> Union[bool,c4d.BaseObject]:
        """
        Get the top arnold driver of given driver type.

        Args:
            driverType (str[CAPS], optional): The driver type to find with. Defaults to display.

        Returns:
            list[c4d.BaseObject]:             
            False if no driver finded.
        """
        if driverType == None: # display
            driver_type = C4DAIN_DRIVER_C4D_DISPLAY
        elif driverType == "EXR": 
            driver_type = C4DAIN_DRIVER_EXR
        elif driverType == "PNG": 
            driver_type = C4DAIN_DRIVER_PNG
        elif driverType == "TIFF": 
            driver_type = C4DAIN_DRIVER_TIFF        
        else:
            driver_type = C4DAIN_DRIVER_C4D_DISPLAY

        drivers: list[c4d.BaseObject] = get_nodes(self.doc,TRACKED_TYPES=[ARNOLD_DRIVER])
        
        if drivers == False:
            return None
        
        result = []
        
        for driver in drivers:
            if driver[c4d.C4DAI_DRIVER_TYPE] == driver_type:
                result.append(driver)
                
        return result[0]
  
    # 根据类型查找driver ==> ok
    def get_dispaly_driver(self) -> Union[bool,c4d.BaseObject]:
        """
        Get dispaly arnold drivers in the scene.

        Returns:
            list[c4d.BaseObject]:             
            False if no driver finded.
        """

        drivers: list[c4d.BaseObject] = get_nodes(self.doc,TRACKED_TYPES=[ARNOLD_DRIVER])
        
        if drivers == False:
            return None
        
        result = []
        
        for driver in drivers:
            if driver[c4d.C4DAI_DRIVER_TYPE] == C4DAIN_DRIVER_C4D_DISPLAY:
                result.append(driver)
                
        return result[0]

    # 设置driver渲染路径 ==> ok
    def set_driver_path(self, driver: c4d.BaseObject, path: str):
        '''
        Set driver render.
        '''
        for filename in C4DAIP_DRIVER_ALL_FILENAME:        
            path_id = c4d.DescID(c4d.DescLevel(filename), c4d.DescLevel(1))
            type_id = c4d.DescID(c4d.DescLevel(filename), c4d.DescLevel(2))    
            driver.SetParameter(type_id, 1, c4d.DESCFLAGS_SET_0)
            driver.SetParameter(path_id, path, c4d.DESCFLAGS_SET_0)

    # 创建aov ==> ok
    def create_aov_shader(self, aov_name: str = 'beauty') -> c4d.BaseObject:
        """
        Create an aov object with given name(copy from aov name)

        ----
        :param aov_name: the name of the aov, defaults to 'beauty'
        :type aov_name: str, optional
        """
                
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        if not isinstance(aov_name, str):
            raise ValueError(f"The {aov_name} need a string")
        
        # if aov_name not in CDTOA_AOVTYPES:
        #     raise ValueError(f"The {aov_name} is not an Arnold basic aov type")
            
        # create AOV object
        aov = c4d.BaseObject(ARNOLD_AOV)
        aov.SetName(aov_name)
        
        # init defaults (depends on the name)
        msg = c4d.BaseContainer()
        msg.SetInt32(C4DTOA_MSG_TYPE, C4DTOA_MSG_INIT_DEFAULTS)
        aov.Message(c4d.MSG_BASECONTAINER, msg)
        return aov
    
    # 创建driver ==> ok
    def create_aov_driver(self, isDisplay: bool = True, driver_type: int = C4DAIN_DRIVER_EXR, denoise: bool = True, render_path: str = None, sRGB: bool = True) -> c4d.BaseObject:
        
        # Driver Object
        driver = c4d.BaseObject(ARNOLD_DRIVER)
        driver[c4d.C4DAI_DRIVER_ENABLE_AOVS] = 1
        
        if isDisplay:
            driver[C4DAI_DRIVER_TYPE] = C4DAIN_DRIVER_C4D_DISPLAY
        else:
            driver[C4DAI_DRIVER_TYPE] = driver_type
            
            # Render Path
            if render_path:
                self.set_driver_path(driver, render_path)
                rd = self.doc.GetActiveRenderData() # get raderdata
                if rd:
                    rd[c4d.RDATA_PATH] = render_path
                    rd[c4d.RDATA_FORMAT] = ARNOLD_DUMMY_BITMAP_SAVER
                    if rd[c4d.RDATA_MULTIPASS_ENABLE] == True:
                            rd[c4d.RDATA_FRAMESEQUENCE] = 2 # all frame            
                            rd[c4d.RDATA_MULTIPASS_FILENAME] = render_path
                            rd[c4d.RDATA_MULTIPASS_SAVEFORMAT] = ARNOLD_DUMMY_BITMAP_SAVER
            
            # Color space
            if sRGB:
                colorspace: str = 'sRGB'
            else:
                colorspace: str = 'ACEScg'
            for param in C4DAIP_DRIVER_COLOR_SPACE:
                driver[param] = colorspace
            
            # EXR
            if driver_type == C4DAIN_DRIVER_EXR:            
                if denoise:
                    driver[c4d.C4DAI_DRIVER_MERGE_AOVS] = 1
                    driver[c4d.C4DAI_DRIVER_SETUP_NOICE] = 1
                driver[C4DAIP_DRIVER_EXR_COMPRESSION] = 9 # dwab
                driver[C4DAIP_DRIVER_EXR_HALF_PRECISION] = 1
                driver[C4DAIP_DRIVER_EXR_PRESERVE_LAYER_NAME] = 1
                driver[c4d.C4DAI_DRIVER_MERGE_AOVS] = True
            # PNG    
            elif driver_type == C4DAIN_DRIVER_PNG:
                driver[C4DAIP_DRIVER_PNG_FORMAT] = 1 # 16bit
                         
        self.doc.InsertObject(driver)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,driver)

        return driver

    # 将aov添加到driver ==> ok
    def add_aov(self, driver: c4d.BaseObject, aov: c4d.BaseObject) -> Union[c4d.BaseObject,bool]:
                
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        if not driver.CheckType(ARNOLD_DRIVER):
            raise ValueError(f"The {driver.GetName()} is not an arnold driver object")
        if not aov.CheckType(ARNOLD_AOV):
            raise ValueError(f"The {aov.GetName()} is not an arnold aov object")
        if not self.get_aov(driver,aov.GetName()):
            # add to the driver
            aov.InsertUnderLast(driver)
            self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,aov)
            return aov
        return False

    # 获取指定driver的aov列表 ==> ok
    def get_aovs(self, driver: c4d.BaseObject) -> list[c4d.BaseObject]:
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        if not driver.CheckType(ARNOLD_DRIVER):
            raise ValueError(f"The {driver.GetName()} is not an arnold driver object")

        #res = self._get_aov_children(driver)
        res: list = []
        for node in iter_node(driver, False, False):
            if node.GetName() in CDTOA_AOVTYPES:
                res.append(node)
        return res
    
    # 获取指定类型的aov ==> ok
    def get_aov(self, driver: c4d.BaseObject, aov_name: str = 'beauty') -> Optional[c4d.BaseObject]:
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        if not driver.CheckType(ARNOLD_DRIVER):
            raise ValueError(f"The {driver.GetName()} is not an arnold driver object")        

        for node in iter_node(driver, False, False):
            if node.GetName() in CDTOA_AOVTYPES and node.GetName() == aov_name:
                return node
            
        return None

    # 打印aov ==> ok
    def print_aov(self):
        
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")

        drivers: list[c4d.BaseObject] = get_nodes(self.doc,TRACKED_TYPES=[ARNOLD_DRIVER])
        driverCnt = len(drivers)
        
        print ("--- ARNOLDRENDER ---\n")
        print ("Driver Count:", driverCnt)
        print("="*20)
        for driver in drivers:
            
            print ("Driver Name:", driver.GetName())
            print ("Driver Type:", DRIVER_NAME_MAP[driver[c4d.C4DAI_DRIVER_TYPE]])
            print("Enabled AOVs: %s" % ("Yes" if driver[c4d.C4DAI_DRIVER_ENABLE_AOVS] else "No"))
            aovs = self.get_aovs(driver)
            print ("AOV count:", len(aovs))
            print("--- AOVS ---")
            for aov in aovs:
                aov_name = aov.GetName()
                print("AOV Type: %s" % aov_name)
                
            print("-"*10)
            
        print ("\n--- ARNOLDRENDER ---")
    
    # 设置aov模式 ==> ok 
    def set_driver_mode(self, driver: c4d.BaseObject, mode: int = 3) -> bool:
        """
        Set the driver render mode: 
        0: custom, 1: custom(name based), 2: render setting(image), 3: render setting(mutipass).


        :param driver: the driver object.
        :type driver: c4d.BaseList2D
        :param mode: mode, defaults to 3
        :type mode: int, optional
        :return: True if success, False otherwise.
        :rtype: bool
        """
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        if driver is None:
            raise ValueError(f"We need an Arnold driver object")
        if driver[c4d.C4DAI_DRIVER_TYPE] == C4DAIN_DRIVER_C4D_DISPLAY:
            raise ValueError(f"The driver object shouldn't be display mode")
    
        if driver[c4d.C4DAI_DRIVER_TYPE] != C4DAIN_DRIVER_C4D_DISPLAY :                    
            for file_param in C4DAIP_DRIVER_ALL_FILENAME:
                type_id = c4d.DescID(c4d.DescLevel(file_param), c4d.DescLevel(2)) 
            return driver.SetParameter(type_id, mode, c4d.DESCFLAGS_SET_0) # 3 = mutipass
                
    # 删除最新的aov ==> ok
    def remove_last_aov(self, driver: c4d.BaseObject):
        """
        Remove the last aov shader.

        """        
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        
        aovs = self.get_aovs(driver)
        aovs[0].Remove()
        
    # 删除全部aov ==> ok
    def remove_all_aov(self, driver: c4d.BaseObject):
        """
        Remove all the aov shaders.

        """
        
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        
        aovs = self.get_aovs(driver)
        for aov in aovs:
            aov.Remove()
   
    # 按照Type删除aov ==> ok
    def remove_aov_type(self, driver: c4d.BaseObject, aov_type: str):
        """
        Remove aovs of the given aov type.

        :param aov_type: the aov type to remove
        :type aov_type: str
        """
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        
        aov = self.get_aov(driver,aov_type)
        aov.Remove()        

    # 设置Cryptomatte ==> ok
    def setup_cryptomatte(self, driver: c4d.BaseObject=None):
        if driver is None:
            driver = self.create_aov_driver(isDisplay=False,denoise=False)
            driver.SetName('Cryptomatte_driver')
        if driver.CheckType(ARNOLD_DRIVER):
            driver = driver
        self.add_aov(driver,self.create_aov_shader("crypto_asset"))
        self.add_aov(driver,self.create_aov_shader("crypto_object"))
        self.add_aov(driver,self.create_aov_shader("crypto_material"))
        MaterialHelper.CreateCryptomatte().InsertMaterial()

__all__ = [
    "AOVHelper"
]
