import c4d
import maxon
import os
import random
from importlib import reload
from typing import Union,Optional
try:
    from arnold_id import *
    #import arnold_node_material as ar
except:
    from renderEngine.arnold.arnold_id import *
    #from renderEngine.arnold import arnold_node_material as ar

from renderEngine import node_helper
reload(node_helper)

def GetPreference() -> c4d.BaseList2D:
    prefs = c4d.plugins.FindPlugin(ID_PREFERENCES_NODE)
    if not isinstance(prefs, c4d.BaseList2D):
        raise RuntimeError("Could not access preferences node.")
    descIdSettings = c4d.DescID(    
    c4d.DescLevel(1036062, 1, 465001632), # pref ID Arnold
    c4d.DescLevel(888, 133, 465001632)
    )
    # Set 
    return prefs[descIdSettings]

# 首选项设置为Node材质
def IsNodeBased():
    """
    Check if Arnold use node material mode.
    """
    return not GetPreference()[c4d.PARNOLD_MATERIAL_SYSTEM]

# 获取渲染器
def GetRenderEngine(document: c4d.documents.BaseDocument = None) -> int :
    """
    Return current render engine ID.
    """
    if not document:
        document = c4d.documents.GetActiveDocument()
    return document.GetActiveRenderData()[c4d.RDATA_RENDERENGINE]

# 获取渲染器版本
def GetVersion(document: c4d.documents.BaseDocument = None) -> str :
    """
    Get the version number of Arnold.

    Returns:
        str: The version number
    """
    if not document:
        document = c4d.documents.GetActiveDocument()
    arnoldSceneHook = document.FindSceneHook(ARNOLD_SCENE_HOOK)
    if arnoldSceneHook is None:
        return ""

    msg = c4d.BaseContainer()
    msg.SetInt32(C4DTOA_MSG_TYPE, C4DTOA_MSG_GET_VERSION)
    arnoldSceneHook.Message(c4d.MSG_BASECONTAINER, msg)

    return msg.GetString(C4DTOA_MSG_RESP1)

# 获取渲染器核心版本
def GetCoreVersion(document: c4d.documents.BaseDocument = None) -> str :
    """
    Get the core version of Arnold.

    Returns:
        str: The version number
    """
    if not document:
        document = c4d.documents.GetActiveDocument()
    arnoldSceneHook = document.FindSceneHook(ARNOLD_SCENE_HOOK)
    if arnoldSceneHook is None:
        return ""

    msg = c4d.BaseContainer()
    msg.SetInt32(C4DTOA_MSG_TYPE, C4DTOA_MSG_GET_VERSION)
    arnoldSceneHook.Message(c4d.MSG_BASECONTAINER, msg)

    return msg.GetString(C4DTOA_MSG_RESP2)

def OpenIPR():
    c4d.CallCommand(1032195) # Arnold IPR Window 

# 打开材质编辑器
def OpenNodeEditor(actmat: c4d.BaseMaterial = None) -> None:
    """
    Open Node Editor for given material.
    """
    if not actmat:
        doc = c4d.documents.GetActiveDocument()
        actmat = doc.GetActiveMaterial()
    else:
        doc = actmat.GetDocument()
    doc.AddUndo(c4d.UNDOTYPE_BITS,actmat)
    actmat.SetBit(c4d.BIT_ACTIVE)
    if not actmat:
        raise ValueError("Failed to retrieve a Material.")
        
    if GetRenderEngine() == ARNOLD_RENDERER:
        if IsNodeBased():
            c4d.CallCommand(465002211) # Node Editor...
            c4d.CallCommand(465002360) # Material
        else:
            c4d.CallCommand(1033989) # Arnold Shader Graph Editor
            # Only scroll to the material if material manager is opened
            
        if c4d.IsCommandChecked(ID_MATERIAL_MANAGER):  
            c4d.CallCommand(16297) # Scroll To Selection

# 打开材质编辑器
def AovManager(document: c4d.documents.BaseDocument = None, driverType: Union[str,c4d.BaseObject,None] = None) -> None:
    """
    Open aov Manager.
    """
    if not document:
        document = c4d.documents.GetActiveDocument()
    if isinstance(driverType,c4d.BaseObject):
        the_driver = driverType
    if isinstance(driverType, str):
        aov_helper = AOVHelper(VideoPostHelper(document).videopost)
        the_driver = aov_helper.get_driver(driverType)

    if driverType is None:
        aov_helper = AOVHelper(VideoPostHelper(document).videopost)
        drivers = node_helper.get_nodes(document,[ARNOLD_DRIVER])
        if not drivers:
            the_driver: c4d.BaseObject = aov_helper.create_aov_driver(isDisplay=True)
        # 只有一个driver
        if len(drivers) == 1:
            the_driver = drivers[0]
        # 有多个driver
        elif len(drivers) > 1:
            the_driver = aov_helper.get_dispaly_driver()
    c4d.CallButton(the_driver, c4d.C4DAI_DRIVER_SETUP_AOVS)


# 打开贴图管理器
def TextureManager() -> None:
    """
    Open Texture Manager.
    """
    c4d.CallCommand(1034460) # Asset/Tx Manager

# 打开灯光管理器
def LightManager():
    c4d.CallCommand(1039255) # light
    
###  ========== arnold ========== ###

class VideoPostHelper:
    """
    Class for Redshift VideoPost.
    """
    def __init__(self, document: c4d.documents.BaseDocument = None):
        if document is None:
            document: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
        self.doc: c4d.documents.BaseDocument = document
        self.vp: c4d.documents.BaseVideoPost = self.get_videopost()
        self.vpname: str = self.vp.GetName()

    def __str__(self) -> str:
        return (f'<Class> VideoPostHelper with videopost named {self.vpname}')
    
    ###  通用  ###
    @property
    def videopost(self) -> c4d.documents.BaseVideoPost:
        return self.vp
    
    # 获取渲染器
    def get_videopost(self) -> c4d.documents.BaseVideoPost:
        """Get the video post"""
        
        rdata: c4d.documents.RenderData = self.doc.GetActiveRenderData()
        vpost: c4d.documents.BaseVideoPost = rdata.GetFirstVideoPost()
        theVp: c4d.documents.BaseVideoPost = None

        # VP
        while vpost:
            if vpost.GetType() == ARNOLD_RENDERER:
                theVp = vpost
            vpost = vpost.GetNext()
        return theVp 
    
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


class AOVHelper:
    """
    用于获取/删除Arnold AOV(Driver)
    """
    def __init__(self, videopost: c4d.documents.BaseVideoPost):
        if isinstance(videopost, c4d.documents.BaseVideoPost):
            self.vp: c4d.documents.BaseVideoPost = videopost
            self.vpname: str = self.vp.GetName()
            self.doc: c4d.documents.BaseDocument = self.vp.GetDocument()

    def __str__(self) -> str:
        return (f'<Class> AOVHelper with videopost named {self.vpname}')

    def _get_aov_children(self, node: c4d.BaseObject) -> list[c4d.BaseObject]:
        res: list = []
        for node in node_helper.iter_node(node, False, False):
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

        drivers: list[c4d.BaseObject] = node_helper.get_nodes(self.doc,TRACKED_TYPES=[ARNOLD_DRIVER])
        
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

        drivers: list[c4d.BaseObject] = node_helper.get_nodes(self.doc,TRACKED_TYPES=[ARNOLD_DRIVER])
        
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
        for node in node_helper.iter_node(driver, False, False):
            if node.GetName() in CDTOA_AOVTYPES:
                res.append(node)
        return res
    
    # 获取指定类型的aov ==> ok
    def get_aov(self, driver: c4d.BaseObject, aov_name: str = 'beauty') -> Optional[c4d.BaseObject]:
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        if not driver.CheckType(ARNOLD_DRIVER):
            raise ValueError(f"The {driver.GetName()} is not an arnold driver object")        

        for node in node_helper.iter_node(driver, False, False):
            if node.GetName() in CDTOA_AOVTYPES and node.GetName() == aov_name:
                return node
            
        return None

    # 打印aov ==> ok
    def print_aov(self):
        
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")

        drivers: list[c4d.BaseObject] = node_helper.get_nodes(self.doc,TRACKED_TYPES=[ARNOLD_DRIVER])
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


class MaterialHelper:
    # 初始化 ==> OK
    def __init__(self, material, document: c4d.documents.BaseDocument = None):
        if document is None:
            document: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
        self.doc: c4d.documents.BaseDocument = document
        
        if not material:
            material = c4d.documents.GetActiveDocument().GetActiveMaterial()
            if material == None:
                raise ValueError("Cann't Init NodeHelper with out a material or a selected material")
            
        self.material = material
        self.helper: node_helper.NodeGraghHelper = node_helper.NodeGraghHelper(self.material)
        self.graph = None
        self.nimbusRef = self.material.GetNimbusRef(AR_NODESPACE)
        #self.node = maxon.GraphNode # Type of 5 :[true node,  input port, output port, input port list, output port list]
        if self.material is not None:
            if isinstance(self.material, c4d.Material):
                nodeMaterial = self.material.GetNodeMaterialReference()
                self.graph: maxon.GraphModelInterface = nodeMaterial.GetGraph(AR_NODESPACE)
                if self.graph is None:
                    print("[WARNING] Node space is not found in Node Material: %s" % self.material.GetName())
            if isinstance(self.material, c4d.NodeMaterial):
                self.graph: maxon.GraphModelInterface = self.material.GetGraph(AR_NODESPACE)
                if self.graph is None:
                    print("[WARNING] Node space is not found in Node Material: %s" % self.material.GetName())  

    # =====  Material  ===== #

    # 创建材质 ==> OK
    @staticmethod
    def Create(name: str = 'Arnold Material'):
        """
        Creates a new Arnold Node Material with a NAME.

        Parameters
        ----------
        name : str
            The Material entry name.

        """
        # Retrieve the selected baseMaterial
        material = c4d.BaseMaterial(c4d.Mmaterial)
        if material is None:
            raise ValueError("Cannot create a BaseMaterial")            
        material.SetName(name)
        # Retrieve the reference of the material as a node Material.
        nodeMaterial = material.GetNodeMaterialReference()
        if nodeMaterial is None:
            raise ValueError("Cannot retrieve nodeMaterial reference")
        # Add a graph for the redshift node space
        nodeMaterial.CreateDefaultGraph(AR_NODESPACE)
            
        # Return a redshift node material
        return MaterialHelper(material)

    # 创建Cryptomatte
    @staticmethod                                               
    def CreateCryptomatte():
        arnoldMaterial = MaterialHelper.Create('Cryptomatte')
        if arnoldMaterial is None or arnoldMaterial.material is None:
            raise Exception("Failed to create Arnold Standard Surface Material")
        with ARMaterialTransaction(arnoldMaterial) as transaction:
            crypto = arnoldMaterial.helper.AddShader("com.autodesk.arnold.shader.cryptomatte")
            crypto_out = arnoldMaterial.helper.GetPort(crypto)
            end_node = arnoldMaterial.helper.GetOutput()
            end_shader_in = arnoldMaterial.helper.GetPort(end_node,'shader')
            crypto_out.Connect(end_shader_in)
        return arnoldMaterial
    
    # 创建Standard Surface
    @staticmethod                                               
    def CreateStandardSurface(name: str = 'Standard Surface'):
        """
        Creates a new Redshift Starndard Surface Material with a NAME.

        Args:
            name (str): Name of the Material

        Returns:
            Material: Redshift Material instance
        """    
        arnoldMaterial = MaterialHelper.Create(name)
        if arnoldMaterial is None or arnoldMaterial.material is None:
            raise Exception("Failed to create Arnold Standard Surface Material")

        with ARMaterialTransaction(arnoldMaterial) as transaction:
            standard_surface = arnoldMaterial.helper.AddShader("com.autodesk.arnold.shader.standard_surface")
            surface_out = arnoldMaterial.helper.GetPort(standard_surface,'output')
            end_node = arnoldMaterial.helper.GetOutput()
            end_shader_in = arnoldMaterial.helper.GetPort(end_node,'shader')
            surface_out.Connect(end_shader_in)
            
            # specular color white
            # NOTE color is in linear sRGB space       
            arnoldMaterial.helper.SetShaderValue(standard_surface, "base_color", maxon.Color(0.7, 0.7, 0.7))
            # set standard surface specular roughness
            arnoldMaterial.helper.SetShaderValue(standard_surface, "specular_roughness", 0.2)

        exp_list = ['metalness',
                    'specular','specular_color','specular_roughness',
                    'transmission','transmission_color',
                    'emission','emission_color'
                    ]
        
        # expose some useful ports
        #arnoldMaterial.helper.ExposePorts(standard_surface,exp_list)
        # expose port callback
        def ExposeHidePorts(node):
            specular_color = node.GetInputs().FindChild("specular_color")
            specular_roughness = node.GetInputs().FindChild("specular_roughness")
            specular_IOR = node.GetInputs().FindChild("specular_IOR")
            transmission = node.GetInputs().FindChild("transmission")
            transmission_color = node.GetInputs().FindChild("transmission_color")
            emission = node.GetInputs().FindChild("emission")
            emission_color = node.GetInputs().FindChild("emission_color")
            normal = node.GetInputs().FindChild("normal")
            opacity = node.GetInputs().FindChild("opacity")
            # Display the port in the node editor
            with arnoldMaterial.graph.BeginTransaction() as tr:
                specular_color.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(False))
                specular_roughness.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(False))
                specular_IOR.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(False))
                transmission.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(False))
                transmission_color.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(False))
                emission.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(False))
                emission_color.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(False))
                normal.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(False))
                opacity.SetValue(maxon.NODE.ATTRIBUTE.HIDEPORTINNODEGRAPH, maxon.Bool(False))
                tr.Commit()
            return True
        # Do Expose defined ports on standard_surface
        maxon.GraphModelHelper.FindNodesByAssetId(arnoldMaterial.graph, "com.autodesk.arnold.shader.standard_surface", False, ExposeHidePorts)
        
        return arnoldMaterial

    # 插入 ==> ok
    def InsertMaterial(self):
        """
        Insert the material to the document.
        """
        if self.material is None: return False
        #self.material.Update(True, True)
        self.doc.InsertMaterial(self.material)
        self.doc.AddUndo(c4d.UNDOTYPE_NEW, self.material)
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
            self.doc.AddUndo(c4d.UNDOTYPE_BITS, self.material)

    def FastPreview(self, on: bool = True):
        if self.material is not None:
            if on:
                self.material[c4d.MATERIAL_PREVIEWSIZE] = 6 # 64x64
            else:
                self.material[c4d.MATERIAL_PREVIEWSIZE] = 0 # default

    # 创建PBR材质 ==> ok
    def SetupTextures(self, tex_data: dict = None, mat_name: Optional[str] = None):
        """
        Setup a pbr material with given or selected texture.
        """
        
        isSpecularWorkflow = False
        if 'Specular' in list(tex_data.keys()):
            isSpecularWorkflow = True            
 
        # modification has to be done within a transaction
        with ARMaterialTransaction(self) as transaction:

            # Find brdf node (in this case : standard surface)
            # 查找Standard Surface节点
            standard_surface = self.helper.GetRootBRDF()
            output_node = self.helper.GetOutput()

            # Change a shader name
            # 更改Standard Surface节点名称
            self.helper.SetName(standard_surface,f'{mat_name} Shader')

            # get ports
            albedoPort = self.helper.GetPort(standard_surface,'base_color')
            specularPort = self.helper.GetPort(standard_surface,'specular_color')
            roughnessPort = self.helper.GetPort(standard_surface,'specular_roughness')
            metalnessPort = self.helper.GetPort(standard_surface,'metalness')
            opacityPort = self.helper.GetPort(standard_surface,'opacity')
            reflectionPort = self.helper.GetPort(standard_surface,'transmission_color')

            try:
                # Base Color            
                if "AO" in tex_data:
                    aoNode = self.AddTexture(filepath=tex_data['AO'], shadername="AO")
                    if "Diffuse" in tex_data:
                        albedoNode = self.AddTextureTree(filepath=tex_data['Diffuse'], shadername="Albedo", raw=False, color_mode=True, color_mutiplier=aoNode, target_port=albedoPort)
                else:
                    albedoNode = self.AddTextureTree(filepath=tex_data['Diffuse'], shadername="Albedo", raw=False, target_port=albedoPort)

                
                if isSpecularWorkflow:
                    if "Specular" in tex_data:
                        self.AddTextureTree(filepath=tex_data['Specular'], shadername="Specular", raw=False, color_mode=True, target_port=specularPort)
                    
                    if "Glossiness" in tex_data:
                        self.AddTextureTree(filepath=tex_data['Glossiness'], shadername="Glossiness", target_port=roughnessPort)
                        isglossinessPort = self.helper.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refl_isglossiness')
                        isglossinessPort.SetDefaultValue(True)

                    elif "Roughness" in tex_data:
                        roughnessNode = self.AddTextureTree(filepath=tex_data['Roughness'], shadername="Roughness", target_port=roughnessPort)

                else:
                    if "Metalness" in tex_data:
                        aoNode = self.AddTexture(filepath=tex_data['Metalness'], shadername="Metalness",target_port=metalnessPort)

                    if "Roughness" in tex_data:
                        roughnessNode = self.AddTextureTree(filepath=tex_data['Roughness'], shadername="Roughness", target_port=roughnessPort)

                    elif "Glossiness" in tex_data:
                        self.AddTextureTree(filepath=tex_data['Glossiness'], shadername="Glossiness", target_port=roughnessPort)
                        isglossinessPort = self.helper.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refl_isglossiness')
                        isglossinessPort.SetDefaultValue(True)                    

                if "Normal" in tex_data:
                    self.AddBumpTree(filepath=tex_data['Normal'], shadername="Normal")
                
                if "Bump" in tex_data and "Normal" not in tex_data:  
                    self.AddBumpTree(filepath=tex_data['Bump'], shadername="Bump")
                
                if "Displacement" in tex_data:
                    self.AddDisplacementTree(filepath=tex_data['Displacement'], shadername="Displacement")

                if "Alpha" in tex_data:
                    self.AddTexture(filepath=tex_data['Alpha'], shadername="Alpha",target_port=opacityPort)

                if "Translucency" in tex_data:
                    self.AddTexture(filepath=tex_data['Translucency'], shadername="Translucency", raw=False, target_port=reflectionPort)

                elif "Transmission" in tex_data:
                    self.AddTexture(filepath=tex_data['Transmission'], shadername="Transmission", raw=True, target_port=reflectionPort)

                self.material.SetName(mat_name)
                
            except Exception as e:
                raise RuntimeError ("Unable to setup texture")
            
        # 将Standard Surface材质引入当前Document
        self.InsertMaterial()
        # 将Standard Surface材质设置为激活材质
        self.SetActive()
        
        return self.material

    def AddShader(self, nodeId:str):
        """
        Adds a new shader to the graph.

        Parameters
        ----------
        nodeId : str
            The Arnold node entry name.
        """
        if self.graph is None:
            return None

        shader = self.graph.AddChild("", "com.autodesk.arnold.shader." + nodeId, maxon.DataDictionary())


        return shader

    ### Color ###

    # 创建Color jitter ==> OK
    def AddColorJitter(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Color jitter shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.color_jitter",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建shuffle ==> OK
    def AddShuffle(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new shuffle shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.shuffle",
            input_ports = ['color'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建Color convert ==> OK
    def AddColorConvert(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Color Convert shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.color_convert",
            input_ports = ['color'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )

    # 创建color correct ==> OK
    def AddColorCorrect(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new color correct shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.color_correct",
            input_ports = ['color'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    ### Operator ###
   
    # 创建Math Add(Float64) ==> OK
    def AddMathAdd(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Math Add shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.add",
            input_ports = ['input1','input2'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
     
    # 创建Math Sub(Float64) ==> OK
    def AddMathSub(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Math Sub shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.subtract",
            input_ports = ['input1','input2'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )

    # 创建Math Mul(Float64) ==> OK
    def AddMathMul(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Math Mul shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.multiply",
            input_ports = ['input1','input2'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )

    # 创建Math Div(Float64) ==> OK
    def AddMathDiv(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Math Div shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.divide",
            input_ports = ['input1','input2'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建Math Negate ==> OK
    def AddMathNegate(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Negate shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.negate",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )

    # 创建Math Range ==> OK
    def AddMathRange(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Range shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.range",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建Math normalize ==> OK
    def AddMathNormalize(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new normalize shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.normalize",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建Math value ==> OK
    def AddMathvalue(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new value shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.value",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
        
    # 创建Math compare ==> OK
    def AddMathCompare(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new compare shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.compare",
            input_ports = ['input1','input2'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )        
        
    # 创建Math abs ==> OK
    def AddMathAbs(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new abs shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.abs",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )        
        
    # 创建Math Min ==> OK
    def AddMathMin(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Min shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.min",
            input_ports = ['input1','input2','input3','input4','input5','input6','input7','input8'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
        
    # 创建Math Max ==> OK
    def AddMathMax(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Max shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.max",
            input_ports = ['input1','input2'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
        
    ### Bump ###
    # 创建Normal ==> OK
    def AddNormal(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Normal shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.normal_map",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
        
    # 创建Bump ==> OK
    def AddBump2d(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Bump shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.bump2d",
            input_ports = ['bump_map'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
        
    def AddBump3d(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Bump shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.bump3d",
            input_ports = ['bump_map'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
         
    # 创建displacement ==> OK
    def AddDisplacement(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new displacement shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.displacement",
            input_ports = ['normal_displacement_input','vector_displacement_input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )

    # 创建Layer Rgba ==> OK
    def AddLayerRgba(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Layer Rgba shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.bump3d",
            input_ports = ['input1','input2'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
        
    # 创建Layer float ==> OK
    def AddLayerFloat(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Layer float shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.layer_float",
            input_ports = ['input1','input2'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
   
    # 创建Round Corners ==> OK
    def AddRoundCorner(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Round Corners shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.layer_float",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    ### State ###

    # 创建Fresnel ==> OK
    def AddFresnel(self,  target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Fresnel shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.facing_ratio",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建AO ==> OK
    def AddAO(self,  target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new AO shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.ambient_occlusion",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['output'], 
            connect_outNodes = target
            )
   
    # 创建Curvature ==> OK
    def AddCurvature(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Curvature shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.curvature",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建Flakes ==> OK
    def AddFlakes(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new Flakes shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.flakes",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    ### Texture ###
    
    # 创建ramp ==> OK
    def AddRampRGB(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new ramp shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.ramp_rgb",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建scalar ramp ==> OK
    def AddRampFloat(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new scalar ramp shader to the graph.        

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.ramp_float",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建TriPlanar ==> OK
    def AddTriPlanar(self, inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new TriPlanar shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.triplanar",
            input_ports = ['input'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    
    # 创建maxon noise ==> OK
    def AddMaxonNoise(self, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        """
        Adds a new maxonnoise shader to the graph.

        """
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.c4d_noise",
            input_ports = None,
            connect_inNodes = None,
            output_ports=['output'], 
            connect_outNodes = target
            )   
    
    # 创建Texture ==> OK
    def AddTexture(self, shadername :str = 'Texture', filepath: str = None, raw: bool = True, target_port: maxon.GraphNode = None) -> maxon.GraphNode :
        """
        Adds a new texture shader to the graph.
        """
        if self.graph is None:
            return None

        shader: maxon.GraphNode = self.graph.AddChild("", "com.autodesk.arnold.shader.image", maxon.DataDictionary())
        self.helper.SetName(shader,shadername)
        
        texPort: maxon.GraphNode = self.helper.GetPort(shader,"filename")

        colorspacePort: maxon.GraphNode = self.helper.GetPort(shader,"colorspace")

        # tex path
        if filepath is not None:
            texPort.SetDefaultValue(filepath)
        
        # color space
        if raw:
            colorspacePort.SetDefaultValue("raw")
        else:
            colorspacePort.SetDefaultValue("sRGB")
        
        # target connect
        if target_port:
            if isinstance(target_port, maxon.GraphNode):
                outPort: maxon.GraphNode = self.helper.GetPort(shader,'output')
                outPort.Connect(target_port)

        return shader

    def AddGobo(self,inputs: list[Union[str,maxon.GraphNode]] = None, target: list[Union[str,maxon.GraphNode]] = None) -> maxon.GraphNode :
        return self.helper.AddConnectShader(
            nodeID ="com.autodesk.arnold.shader.gobo",
            input_ports = ['slidemap'],
            connect_inNodes = inputs,
            output_ports=['output'], 
            connect_outNodes = target
            )
    ### Tree ###

    # NEW
    def AddTextureTree(self, shadername :str = 'Texture', filepath: str = None, raw: bool = True, color_mode: bool = False,scaleramp: bool = False,color_mutiplier: maxon.GraphNode = None, target_port: maxon.GraphNode = None) -> list[maxon.GraphNode] :
        """
        Adds a texture tree (tex + color correction + ramp) to the graph.
        """
        if self.graph is None:
            return None
        
        # add
        tex_node = self.AddTexture(shadername, filepath, raw)
        color_mutiplier_port = self.helper.GetPort(tex_node,"multiply")
        
        if color_mode:
            cc_node = self.AddColorCorrect(target=target_port)
        
        else:
            cc_node = self.AddColorCorrect()
            if scaleramp:
                ramp_node = self.AddRampFloat(target=target_port)
            else:
                ramp_node = self.AddRampRGB(target=target_port)

        self.helper.AddConnection(tex_node, "output", cc_node, "input")
        
        
        if not color_mode:
            if scaleramp:
                self.helper.AddConnection(cc_node, "output", ramp_node, "input")
            else:
                self.helper.AddConnection(cc_node, "output", ramp_node, "input")
        
        if color_mutiplier:
            self.helper.AddConnection(color_mutiplier, "output", tex_node, color_mutiplier_port)
        
        return tex_node
    
    # NEW
    def AddDisplacementTree(self, shadername :str = 'Displacement', filepath: str = None) -> list[maxon.GraphNode] :
        """
        Adds a displacement tree (tex + displacement) to the graph.
        """
        if self.graph is None:
            return None
        
        # add        
        tex_node = self.AddTexture(shadername, filepath, True)
        tex_out = self.helper.GetPort(tex_node, "output")
        endNode = self.helper.GetOutput()
        disp_port = self.helper.GetPort(endNode,'displacement')
        self.AddDisplacement(tex_out,disp_port)

    # NEW
    def AddBumpTree(self, shadername :str = 'Bump', filepath: str = None) -> list[maxon.GraphNode] :
        """
        Adds a bump tree (tex + bump) to the graph.
        """
        if self.graph is None:
            return None
        
        tex_node = self.AddTexture(shadername, filepath, True)
        tex_out = self.helper.GetPort(tex_node, "output")
        brdf = self.helper.GetRootBRDF()
        disp_port = self.helper.GetPort(brdf,'normal')
        self.AddBump2d(tex_out,disp_port)
        
    # NEW
    def AddNormalTree(self, shadername :str = 'Normal', filepath: str = None) -> list[maxon.GraphNode] :
        """
        Adds a Normal tree (tex + Normal) to the graph.
        """
        if self.graph is None:
            return None
        
        tex_node = self.AddTexture(shadername, filepath, True)
        tex_out = self.helper.GetPort(tex_node, "output")
        brdf = self.helper.GetRootBRDF()
        disp_port = self.helper.GetPort(brdf,'normal')
        self.AddNormal(tex_out,disp_port)
        
    # 连接到Output Surface接口
    def AddtoOutput(self, soure_node, outPort):
        """
        Connects the given shader to RS Output Surface port.

        Parameters
        ----------
        soure_node : maxon.frameworks.graph.GraphNode
            The source shader node.
        outPort : str
            Output port id of the source shader node.
        """
        endNode = self.helper.GetOutput()
        endNodePort = self.helper.GetPort(endNode, "shader")
        return self.helper.AddConnection(soure_node, outPort, endNode, endNodePort) is not None

    # 连接到Output置换接口
    def AddtoDisplacement(self, soure_node, outPort):
        """
        Connects the given shader to AR Output Displacement port.

        Parameters
        ----------
        soure_node : maxon.frameworks.graph.GraphNode
            The source shader node.
        outPort : str
            Output port id of the source shader node.
        """
        rsoutput = self.helper.GetOutput()
        rsoutputPort = self.helper.GetPort(rsoutput, "displacement")
        return self.helper.AddConnection(soure_node, outPort, rsoutput, rsoutputPort) is not None

# Transaction
class ARMaterialTransaction:
    """
    A class used to represent a transaction in an Arnold Node Material.
    Use it in a with statement.
    """

    def __init__(self, material: c4d.BaseMaterial):
        self.material = material
        self.transaction = None
        
        # no undo steps
        settings: maxon.DataDictionaryInterface = maxon.DataDictionary()
        settings.Set(maxon.nodes.UndoMode, maxon.nodes.UNDO_MODE.NONE)
        self.setting = settings
        
    def __enter__(self):
        if self.material is not None and self.material.graph is not None:
            self.transaction: maxon.GraphTransaction = self.material.graph.BeginTransaction()
        return self

    def __exit__(self, type, value, traceback):
        if self.transaction is not None:
            self.transaction.Commit(self.setting)
    

class SceneHelper:
    """
    Class for Arnold Secne Objects.
    """
    def __init__(self, document: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()):
        if document is None:
            document: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
        self.doc: c4d.documents.BaseDocument = document
        
    def _add_unseltag(self, node: c4d.BaseObject):
        if not isinstance(node,c4d.BaseObject):
            raise ValueError("Must be a BaseObject")
        unseltag = c4d.BaseTag(440000164) # Interaction Tag
        unseltag[c4d.INTERACTIONTAG_SELECT] = True # INTERACTIONTAG_SELECT
        node.InsertTag(unseltag) # insert tag 
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,unseltag)
        
    ### Light ###      
    
    def set_link(self, node : c4d.BaseObject, file_path: str = None, raw: bool = False) -> c4d.BaseTag:
        '''Set links to given hdr or light.
        '''
        linkIDs = [2056342262,2010942260,268620635]
        shaderlink = ArnoldShaderLinkCustomData()
        shaderlink.type = ArnoldShaderLinkCustomData.TYPE_TEXTURE
        shaderlink.texture = file_path
        if raw:
            color_space = 'raw'
        else:
            color_space = 'linear sRGB'
        shaderlink.texture_color_space = color_space
        for i in linkIDs:
            SetShaderLink(node, i , shaderlink)

    def add_hdr_dome(self, color_space: str = 'linear sRGB', texture_path: str = None, intensity: float = 1.0, exposure: float = 0.0, seen_by_cam: bool = True) -> c4d.BaseObject :
        """
        Add a texture (hdr) dome light to the scene.

        :param texture_path: HDR image path
        :type texture_path: str
        :param unselect: True if the dome can not be select, defaults to True
        :type unselect: bool, optional
        :param mode: True to primray mode,othervise to visible, defaults to True
        :type mode: bool, optional
        :return: the image texture node and the sky object
        :rtype: lc4d.BaseObject
        """

        light = c4d.BaseObject(ARNOLD_SKY) # arnold sky
        self.doc.InsertObject(light)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,light)
        light.SetName('Arnold Sky')
        light[C4DAIP_SKYDOME_LIGHT_INTENSITY] = intensity
        light[C4DAIP_SKYDOME_LIGHT_EXPOSURE] = exposure
        light[C4DAIP_SKYDOME_LIGHT_CAMERA] = seen_by_cam
        
        # the returned value is of ArnoldShaderLinkCustomData type
        shaderlink = GetShaderLink(light, C4DAIP_SKYDOME_LIGHT_COLOR)
        if shaderlink is not None:
            # example 2: set texture
            shaderlink = ArnoldShaderLinkCustomData()
            shaderlink.type = ArnoldShaderLinkCustomData.TYPE_TEXTURE
            shaderlink.texture = texture_path
            shaderlink.texture_color_space = color_space
            SetShaderLink(light, C4DAIP_SKYDOME_LIGHT_COLOR , shaderlink)
        return light

    def add_rgb_dome(self, rgb: c4d.Vector = c4d.Vector(0,0,0), intensity: float = 1.0, exposure: float = 0.0, seen_by_cam: bool = True) -> c4d.BaseObject:
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
        light = c4d.BaseObject(ARNOLD_LIGHT) # arnold dome
        self.doc.InsertObject(light)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,light)
        light.SetName('Arnold Dome Light')
        light[C4DAIP_SKYDOME_LIGHT_INTENSITY] = intensity
        light[C4DAIP_SKYDOME_LIGHT_EXPOSURE] = exposure
        light[C4DAIP_SKYDOME_LIGHT_CAMERA] = seen_by_cam
        # set the color value
        SetShaderLink(light, C4DAIP_DOME_LIGHT_COLOR , rgb)
        return light

    def add_dome_rig(self, texture_path: str, rgb: c4d.Vector = c4d.Vector(0,0,0)):
        """
        Add a HDR and visible dome light folder.

        :param texture_path: hdr image path
        :type texture_path: str
        :param unselect: True if the dome can not be select, defaults to True
        :type unselect: bool, optional
        """
        hdr_dome: c4d.BaseObject = self.add_hdr_dome(texture_path=texture_path,seen_by_cam=False)
        black_dome: c4d.BaseObject = self.add_rgb_dome(rgb)
        null = c4d.BaseObject(c4d.Onull)
        null.SetName("Environment")
        null[c4d.ID_BASELIST_ICON_FILE] = '1052837'
        null[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 1
        null[c4d.ID_BASELIST_ICON_COLOR] = c4d.Vector(0.008, 0.659, 0.902)
        self.doc.InsertObject(null)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,null)
        hdr_dome.InsertUnder(null)
        black_dome.InsertUnder(null)
        hdr_dome.DelBit(c4d.BIT_ACTIVE)
        black_dome.DelBit(c4d.BIT_ACTIVE)
        null.SetBit(c4d.BIT_ACTIVE)
        # Unfold the null if it is fold
        if null.GetNBit(c4d.NBIT_OM1_FOLD) == False:
            null.ChangeNBit(c4d.NBIT_OM1_FOLD, c4d.NBITCONTROL_TOGGLE)

    def add_light(self,                
                light_name: str = 'Arnold Light',
                color_space: str = 'linear sRGB',
                texture_path: str = None,
                intensity: float = 1.0,
                exposure: float = 0.0,
                samples: int = 1,
                light_type: int = C4DAIN_QUAD_LIGHT,
                ) -> list :        
        
        light = c4d.BaseObject(ARNOLD_LIGHT)
        # 定义灯光属性
        light[c4d.C4DAI_LIGHT_TYPE] = light_type
        light.SetName(light_name)  
        light[C4DAIP_QUAD_LIGHT_INTENSITY] = intensity
        light[C4DAIP_QUAD_LIGHT_EXPOSURE] = exposure
        light[C4DAIP_QUAD_LIGHT_SAMPLES] = samples
        
        # the returned value is of ArnoldShaderLinkCustomData type
        #shaderlink = GetShaderLink(light, C4DAIP_QUAD_LIGHT_COLOR)
        
        if texture_path:
            # example 2: set texture
            shaderlink = ArnoldShaderLinkCustomData()
            shaderlink.type = ArnoldShaderLinkCustomData.TYPE_TEXTURE
            
            shaderlink.texture = texture_path
            shaderlink.texture_color_space = color_space
            SetShaderLink(light, C4DAIP_QUAD_LIGHT_COLOR , shaderlink)
        
        self.doc.InsertObject(light)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,light)
        return light

    def add_ies(self, texture_path: str = None, intensity: float = 1.0, exposure: float = 0.0):
        ies = self.add_light(light_name='Arnold IES',intensity = intensity,exposure=exposure,light_type=C4DAIN_PHOTOMETRIC_LIGHT)

        ies[C4DAIP_PHOTOMETRIC_LIGHT_FILENAME] = texture_path
        return ies
    
    def add_gobo(self, texture_path: str = None, intensity: float = 1.0, exposure: float = 0.0):
        gobo_material = MaterialHelper.Create('Gobo')
        # modification has to be done within a transaction
        with ARMaterialTransaction(gobo_material) as transaction:
            gobo_tex = gobo_material.AddTexture(shadername='Gobo Texture',filepath=texture_path)
            tex_outport = gobo_material.helper.GetPort(gobo_tex)
            endNode = gobo_material.helper.GetOutput()
            endNodePort = gobo_material.helper.GetPort(endNode, "shader")
            gobo_shader = gobo_material.AddGobo(tex_outport,endNodePort)

        gobo_material.InsertMaterial()
        gobo_material.SetActive()        

        gobo = self.add_light(light_name='Arnold Gobo', intensity = intensity,exposure=exposure,light_type=C4DAIN_SPOT_LIGHT)
        
        # InExcludeData
        filter_data = c4d.InExcludeData()
        filter_data.InsertObject(gobo_material.material,1)
        gobo[c4d.C4DAI_LIGHT_COMMON_FILTERS] = filter_data
        
        return gobo
    
    def add_sun(self, light_name: str = 'Arnold Sun'):
        # 新建灯光
        light = c4d.BaseObject(ARNOLD_LIGHT)
        light [c4d.C4DAI_LIGHT_TYPE] = C4DAIN_DISTANT_LIGHT
        # 定义灯光属性                    
        light.SetName('Arnold Infinite Light')
        light[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 1
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, light)      
        # Name
        light.SetName(light_name)
        # Insert light into document.
        self.doc.InsertObject(light)
        return light

    def add_light_modifier(self, light: c4d.BaseObject, target: c4d.BaseObject = None, gsg_link: bool = False, rand_color: bool = False, seed: int = 0):
        
        # 新建目标标签
        if target:        
            mbtag = c4d.BaseTag(5676) # target
            self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, mbtag)
            if isinstance(target, c4d.BaseObject):
                mbtag[c4d.TARGETEXPRESSIONTAG_LINK] = target
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
                randcolor = c4d.Vector(*node_helper.generate_random_color(1))
            else:
                random.seed(seed)
                randcolor = node_helper.generate_random_color(1)
            light[c4d.ID_BASELIST_ICON_COLOR] = randcolor
     
    ### Tag ###

    def add_mask_tag(self, node : c4d.BaseObject, mask_name: str = None) -> c4d.BaseTag:
        tag = c4d.BaseTag(ARNOLD_OBJECTMASK_TAG) # arnold mask tag
        tag[c4d.C4DAI_OBJECTMASK_TAG_AOV_TYPE] = 0
        tag[c4d.C4DAI_OBJECTMASK_TAG_AOV_NAME_MODE] = 0
        tag[c4d.C4DAI_OBJECTMASK_TAG_AOV_NAME] = mask_name
        node.InsertTag(tag)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,tag)
        tag.SetParameter(c4d.C4DAI_OBJECTMASK_TAG_AOV_TYPE, 0, c4d.DESCFLAGS_SET_0)
        return tag
        
    def add_object_tag(self, node : c4d.BaseObject) -> c4d.BaseTag:
        object_tag = c4d.BaseTag(ARNOLD_TAG) # arnold tag
        node.InsertTag(object_tag)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,object_tag)        
        return object_tag
            
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
            atag = c4d.BaseTag(ARNOLD_TAG)                
            node.InsertTag(atag)
            self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, atag)
                        
        return atag

    ### Object ###
    
    def add_scatter(self, generator_node: c4d.BaseObject, scatter_nodes: list[c4d.BaseObject] = None, selectedtag: c4d.SelectionTag = None, count: int = None):
            

        Modifier = c4d.BaseObject(ARNOLD_SCATTER) # 
        Modifier[c4d.C4DAI_SCATTER_SURFACE] = generator_node
        
        if count is None:
            count = random.randint(0,9999)
        Modifier[c4d.C4DAI_SCATTER_DENSITY_MAX_POINTS] = count
        
        if scatter_nodes:  
            # _ InExcludeData方法
            data = c4d.InExcludeData()
            for node in scatter_nodes :
                data.InsertObject(node,1)
                node.DelBit(c4d.BIT_ACTIVE)

            Modifier[c4d.C4DAI_POINTS_POINTS_MODE] = 100 # custom shape
            Modifier[c4d.C4DAI_POINTS_CUSTOM_SHAPES] = data
            Modifier[c4d.C4DAI_POINTS_SHAPE_MODE] = 1 # random
            
        if selectedtag :
            Modifier[c4d.C4DAI_SCATTER_SELECTION] = selectedtag.GetName()            
        
        self.doc.InsertObject(Modifier)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,Modifier)

        return Modifier
        
    def add_vdb(self, vdb_path: str = ""):
        vdb = c4d.BaseObject(ARNOLD_VOLUME) # Create the object.
        vdb.SetName('Arnold Volume') # Set name.
        vdb[C4DAIP_VOLUME_FILENAME] =vdb_path
        vdb_obj = self.doc.InsertObject(vdb)
        return vdb_obj
   
    ### Util ### 
    def add_proxy(self, name: str = None, proxy_path: str = None, mesh: bool = True, mode: int = None) -> c4d.BaseObject :
        proxy = c4d.BaseObject(ARNOLD_PROCEDURAL)
        self.doc.InsertObject(proxy)
        if name:
            proxy.SetName(name)
        else:
            proxy.SetName('Arnold Proxy')
        
        self.doc.InsertObject(proxy)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,proxy)

        proxy[c4d.C4DAI_PROCEDURAL_PATH] = proxy_path
        proxy[c4d.C4DAI_PROCEDURAL_OBJECT_DISPLAY_MODE] = 1
        proxy[c4d.C4DAI_PROCEDURAL_DISPLAY_BBOX] = False
        proxy[c4d.C4DAI_PROCEDURAL_VIEWPORT_COLOR_MODE] = 5
        return proxy

    # 导出ASS
    def export_proxy(self, node : c4d.BaseObject , filename, remove_objects = False ,
                        currentFrame = True , startFrame = None, endFrame = None, stepFrame = 1 ) -> c4d.BaseObject :
        """
        Exports the given scene to file.
        -----------
        # Ass export options
        C4DAI_SCENEEXPORT_FILENAME = 0,
        C4DAI_SCENEEXPORT_ASS_COMPRESSED = 1,
        C4DAI_SCENEEXPORT_BOUNDINGBOX = 2,
        C4DAI_SCENEEXPORT_ASS_BINARY = 3,
        C4DAI_SCENEEXPORT_ASS_EXPANDPROCEDURALS = 4,
        C4DAI_SCENEEXPORT_MASK = 5,
        C4DAI_SCENEEXPORT_START_FRAME = 6,
        C4DAI_SCENEEXPORT_END_FRAME = 7,
        C4DAI_SCENEEXPORT_FRAME_STEP = 8,
        C4DAI_SCENEEXPORT_EXPORT_TYPE = 11,
        C4DAI_SCENEEXPORT_REPLACE_WITH_PROCEDURAL = 12,
        C4DAI_SCENEEXPORT_OBJECT_HIERARCHY = 13,
        C4DAI_SCENEEXPORT_FORMAT = 14,
        C4DAI_SCENEEXPORT_ABSPATHS = 15,     
        """ 
        
        # 容器设置
        options = c4d.BaseContainer()
        if filename is not None:
            options.SetFilename(0, filename)
        # 压缩
        options.SetBool(1, False)
        # bbox
        options.SetBool(2, False)
        # 二进制
        options.SetBool(3, True)
        # expand
        options.SetBool(4, False)
        # mask
        options.SetInt32(5, 0xFFFF)
        # 当前帧
        cf = self.doc.GetTime().GetFrame(self.doc.GetFps())    
        if currentFrame == True:            
            options.SetInt32(6, cf)
            options.SetInt32(7, cf)
        # 动画帧
        else: 
            if startFrame is not None:
                options.SetInt32(6, startFrame)
            if endFrame is not None:
                options.SetInt32(7, endFrame)
            if stepFrame is not None:
                options.SetInt32(8, stepFrame)
        # 导出模式     
        options.SetInt32(11, SCENE_EXPORT_OBJECT_MODE_SELECTED) 
        # 替换原始对象
        options.SetBool(12, False)
        # 层级
        options.SetBool(13, True) 
        # 导出格式
        options.SetInt32(14, SCENE_EXPORT_FORMAT_ASS)
        # 导出设置          
        self.doc.GetSettingsInstance(c4d.DOCUMENTSETTINGS_DOCUMENT).SetContainer(ARNOLD_SCENE_EXPORT, options)
        
        ex_node: c4d.BaseObject=  node.GetClone()
        mg = c4d.Matrix()
        ex_node.SetMg(mg)
        self.doc.InsertObject(ex_node)
        
        # 执行对象
        c4d.CallCommand(100004767) # Deselect All Object
        ex_node.SetBit(c4d.BIT_ACTIVE) 
        c4d.CallCommand(ARNOLD_SCENE_EXPORT) 
        ex_node.Remove() 
        
        #p_node.SetMg(or_mg)
        
        # 程序对象
        proxy = c4d.BaseObject(ARNOLD_PROCEDURAL)
        self.doc.InsertObject(proxy, pred=node, checknames=True)        
        proxy.SetName(node.GetName() + "_Proxy")
        # 重置坐标
        proxy.SetMg(node.GetMg())
        file = node.GetName() + ".ass"
        #randcolor = c4d.Vector(*generate_random_color(randHue))
        proxy[c4d.C4DAI_PROCEDURAL_PATH] = os.path.join(self.doc.GetDocumentPath(),"_Proxy",file)
        proxy[c4d.C4DAI_PROCEDURAL_OBJECT_DISPLAY_MODE] = 1
        proxy[c4d.C4DAI_PROCEDURAL_DISPLAY_BBOX] = False
        proxy[c4d.C4DAI_PROCEDURAL_VIEWPORT_COLOR_MODE] = 5
        #proxy[c4d.C4DAI_PROCEDURAL_VIEWPORT_COLOR] = randcolor
        
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, proxy)
        if remove_objects == True:
            self.doc.AddUndo(c4d.UNDOTYPE_DELETEOBJ, node)
            node.Remove()    
        return proxy

    # 导出命令
    def auto_proxy(self, nodes : Union[list[c4d.BaseObject],c4d.BaseObject], remove_objects=False):
        if isinstance(nodes, c4d.BaseObject):
            nodes = [nodes]

        document_path = self.doc.GetDocumentPath()
        if not document_path:
            raise RuntimeError('Save project before exporting objects')
        proxy_path = os.path.join(self.doc.GetDocumentPath(),"_Proxy") # Proxy Temp Folder
        
        if not os.path.exists(proxy_path):
            os.makedirs(proxy_path)

        for node in nodes:
            name = node.GetName()
            path = os.path.join(self.doc.GetDocumentPath(),"_Proxy",name)
            self.export_proxy(node, path , remove_objects )


#=============================================
# Copyright @Arnold Node Material
#=============================================

# Link
class ArnoldShaderLinkCustomData:
    """
    A class used to represent data stored in the Arnold Shader Link custom gui.
    """

    TYPE_CONSTANT = 1
    TYPE_TEXTURE = 2
    TYPE_MATERIAL = 3
 
    def __init__(self, guiType = TYPE_CONSTANT, value = c4d.Vector(), texture = None, material = None):
        self.type = guiType
        self.value = value
        self.texture = texture
        self.texture_color_space = "sRGB"
        self.material = material

    def __repr__(self):
        if self.type == ArnoldShaderLinkCustomData.TYPE_CONSTANT:
            if self.value is not None:
                return "%f %f %f (constant)" % (self.value.x, self.value.y, self.value.z)
            else:
                return "0 0 0 (constant)"
        elif self.type == ArnoldShaderLinkCustomData.TYPE_TEXTURE:
            return "%s [%s] (texture)" % (self.texture, self.texture_color_space)
        elif self.type == ArnoldShaderLinkCustomData.TYPE_MATERIAL:
            return "%s (material)" % (self.material.GetName() if self.material is not None else "<none>")
        return ""

def GetShaderLink(node, paramId):
    """
    Returns the value defined in the given node parameter.

    Parameters
    ----------
    node : c4d.BaseList2D
        Scene node (e.g. Arnold Light object).
    paramId : Int32
        Id of the parameter.
    """
    if node is None:
        return None

    # get the container which stores the shader link attributes
    shaderLinkMainContainer = node[C4DAI_SHADERLINK_CONTAINER]
    if shaderLinkMainContainer is None:
        return None
    shaderLinkContainer = shaderLinkMainContainer.GetContainer(paramId)
    if shaderLinkContainer is None:
        return None

    # read the shader link attributes
    shaderLinkData = ArnoldShaderLinkCustomData()
    shaderLinkData.type = shaderLinkContainer.GetInt32(C4DAI_SHADERLINK_TYPE,  ArnoldShaderLinkCustomData.TYPE_CONSTANT)
    shaderLinkData.value = node[paramId]
    shader = shaderLinkContainer.GetLink(C4DAI_SHADERLINK_TEXTURE)
    if shader is not None and shader.GetType() == c4d.Xbitmap:
        shaderLinkData.texture = shader[c4d.BITMAPSHADER_FILENAME]
        shaderLinkData.texture_color_space = shader[C4DAI_GVC4DSHADER_BITMAP_COLOR_SPACE]
    else:
        shaderLinkData.texture = None
        shaderLinkData.texture_color_space = ""
    shaderLinkData.material = shaderLinkContainer.GetLink(C4DAI_SHADERLINK_MATERIAL)

    return shaderLinkData
 
def SetShaderLink(node, paramId, value):
    """
    Sets the value of the given node parameter.

    Parameters
    ----------
    node : c4d.BaseList2D
        Scene node (e.g. Arnold Light object).
    paramId : int
        Id of the parameter.
    value : ArnoldShaderLinkCustomData, c4d.Vector, maxon.Color, str, c4d.BaseMaterial
        Value of the parameter to set.
    """
    if node is None:
        return None

    # check the data type of the value
    # accept ArnoldShaderLinkCustomData, Vector, Color, str and BaseMaterial
    if isinstance(value, ArnoldShaderLinkCustomData):
        shaderLinkData = value
    elif isinstance(value, c4d.Vector) or isinstance(value, maxon.Vector):
        shaderLinkData = ArnoldShaderLinkCustomData(ArnoldShaderLinkCustomData.TYPE_CONSTANT, value)
    elif isinstance(value, maxon.Color):
        shaderLinkData = ArnoldShaderLinkCustomData(ArnoldShaderLinkCustomData.TYPE_CONSTANT, c4d.Vector(value.r, value.g, value.b))
    elif isinstance(value, str):
        shaderLinkData = ArnoldShaderLinkCustomData(ArnoldShaderLinkCustomData.TYPE_TEXTURE, texture=value)
    elif isinstance(value, c4d.BaseMaterial):
        shaderLinkData = ArnoldShaderLinkCustomData(ArnoldShaderLinkCustomData.TYPE_MATERIAL, material=value)
    elif value is None:
        shaderLinkData = ArnoldShaderLinkCustomData()
    else:
        print("[WARNING] %s.%s: invalid shader link value, only ArnoldShaderLinkCustomData, Vector, Color, Filename, str or BaseMaterial is accepted" % (node.GetId(), paramId))
        return None

    # create a container to store the shader link attributes
    shaderLinkMainContainer = node[C4DAI_SHADERLINK_CONTAINER]
    if shaderLinkMainContainer is None:
        shaderLinkMainContainer = c4d.BaseContainer()

    shaderLinkContainer = shaderLinkMainContainer.GetContainer(paramId)
    if shaderLinkContainer is None:
        shaderLinkContainer = c4d.BaseContainer()

    # set the type
    shaderLinkContainer[C4DAI_SHADERLINK_TYPE] = shaderLinkData.type

    # set the color value
    if shaderLinkData.type == ArnoldShaderLinkCustomData.TYPE_CONSTANT:
        node[paramId] = shaderLinkData.value
        shaderLinkContainer[C4DAI_SHADERLINK_VALUE] = shaderLinkData.value
    # set the texture (Bitmap shader)
    elif shaderLinkData.type == ArnoldShaderLinkCustomData.TYPE_TEXTURE:
        shader = shaderLinkContainer.GetLink(C4DAI_SHADERLINK_TEXTURE)
        if shader is not None:
            shader.Remove()
        shader = c4d.BaseShader(c4d.Xbitmap)
        shader[c4d.BITMAPSHADER_FILENAME] = shaderLinkData.texture
        shader[C4DAI_GVC4DSHADER_BITMAP_COLOR_SPACE] = shaderLinkData.texture_color_space
        node.InsertShader(shader)
        shaderLinkContainer[C4DAI_SHADERLINK_TEXTURE] = shader
    # set the material link
    elif shaderLinkData.type == ArnoldShaderLinkCustomData.TYPE_MATERIAL:
        shaderLinkContainer[C4DAI_SHADERLINK_MATERIAL] = shaderLinkData.material

    # set the shader link to the node
    shaderLinkMainContainer.SetContainer(paramId, shaderLinkContainer)
    node[C4DAI_SHADERLINK_CONTAINER] = shaderLinkMainContainer


# Color
class ArnoldVColorCustomData:
    """
    A class used to represent data stored in the Arnold Vector/Color custom gui.
    """

    TYPE_COLOR = 1
    TYPE_VECTOR = 2
 
    def __init__(self, value = c4d.Vector(), guiType = TYPE_COLOR):
        self.value = value
        self.type = guiType

    def __repr__(self):
        return "%f %f %f (%s)" % (self.value.x, self.value.y, self.value.z, 
            "color" if self.type == ArnoldVColorCustomData.TYPE_COLOR else "vector")

def GetVColor(node, paramId):
    """
    Returns the value defined in the given node parameter.

    Parameters
    ----------
    node : c4d.BaseList2D or maxon.frameworks.graph.GraphNode
        Scene node (e.g. object).
    paramId : Int32
        Id of the parameter.
    """
    if node is None:
        return None

    vcolorData = ArnoldVColorCustomData()

    if isinstance(node, maxon.GraphNode):
        material = c4d.NodeMaterial.GetMaterial(maxon.Cast(maxon.NodesGraphModelRef, node.GetGraph()))
        if material is None:
            return None

        # send a custom message to the Arnold Scene hook class to get the data
        msg = c4d.BaseContainer()
        msg.SetInt32(C4DTOA_MSG_TYPE, C4DTOA_MSG_GET_NODEMATERIAL_CUSTOMDATA)
        msg.SetLink(C4DTOA_MSG_PARAM1, material)
        msg.SetString(C4DTOA_MSG_PARAM2, node.GetPath())
        msg.SetString(C4DTOA_MSG_PARAM3, paramId)

        doc = c4d.documents.GetActiveDocument()
        arnoldSceneHook = doc.FindSceneHook(ARNOLD_SCENE_HOOK)
        if arnoldSceneHook is None:
            return None
        arnoldSceneHook.Message(c4d.MSG_BASECONTAINER, msg)

        vcolorData.value = msg.GetVector(C4DTOA_MSG_RESP1)
        vcolorData.type = msg.GetInt32(C4DTOA_MSG_RESP2)

    else:
        valueId = c4d.DescID(c4d.DescLevel(paramId), c4d.DescLevel(1))
        vcolorData.value = node.GetParameter(valueId, c4d.DESCFLAGS_GET_0)
        guiTypeId = c4d.DescID(c4d.DescLevel(paramId), c4d.DescLevel(2))
        vcolorData.type = node.GetParameter(guiTypeId, c4d.DESCFLAGS_GET_0)

    return vcolorData
 
def SetVColor(node, paramId, value):
    """
    Sets the value of the given node parameter.

    Parameters
    ----------
    node : c4d.BaseList2D or maxon.frameworks.graph.GraphNode
        Scene node (e.g. object).
    paramId : int
        Id of the parameter.
    value : ArnoldVColorCustomData, c4d.Vector, maxon.Color
        Value of the parameter to set.
    """
    if node is None:
        return None

    # check the data type of the value
    # accept ArnoldVColorCustomData, Vector and Color
    if isinstance(value, ArnoldVColorCustomData):
        vcolorData = value
    elif isinstance(value, c4d.Vector) or isinstance(value, maxon.Vector):
        vcolorData = ArnoldVColorCustomData(value, ArnoldVColorCustomData.TYPE_VECTOR)
    elif isinstance(value, maxon.Color):
        vcolorData = ArnoldVColorCustomData(c4d.Vector(value.r, value.g, value.b), ArnoldVColorCustomData.TYPE_COLOR)
    elif value is None:
        vcolorData = ArnoldVColorCustomData()
    else:
        print("[WARNING] %s.%s: invalid vcolor value, only ArnoldVColorCustomData, Vector or Color is accepted" % (node.GetId(), paramId))
        return None

    if  isinstance(node, maxon.GraphNode):
        material = c4d.NodeMaterial.GetMaterial(maxon.Cast(maxon.NodesGraphModelRef, node.GetGraph()))
        if material is None:
            return None

        # send a custom message to the Arnold Scene hook class to set the data
        msg = c4d.BaseContainer()
        msg.SetInt32(C4DTOA_MSG_TYPE, C4DTOA_MSG_SET_NODEMATERIAL_CUSTOMDATA)
        msg.SetLink(C4DTOA_MSG_PARAM1, material)
        msg.SetString(C4DTOA_MSG_PARAM2, node.GetPath())
        msg.SetString(C4DTOA_MSG_PARAM3, paramId)
        msg.SetVector(C4DTOA_MSG_PARAM4, vcolorData.value)
        msg.SetInt32(C4DTOA_MSG_PARAM5, vcolorData.type)

        doc = c4d.documents.GetActiveDocument()
        arnoldSceneHook = doc.FindSceneHook(ARNOLD_SCENE_HOOK)
        if arnoldSceneHook is None:
            return None
        arnoldSceneHook.Message(c4d.MSG_BASECONTAINER, msg)

    else:     
        valueId = c4d.DescID(c4d.DescLevel(paramId), c4d.DescLevel(1))
        node.SetParameter(valueId, vcolorData.value, c4d.DESCFLAGS_SET_0)
        guiTypeId = c4d.DescID(c4d.DescLevel(paramId), c4d.DescLevel(2))
        node.SetParameter(guiTypeId, vcolorData.type, c4d.DESCFLAGS_SET_0)
        
# todo