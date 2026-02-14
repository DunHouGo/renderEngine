import c4d


from ..constants import *
from ..utils import GetVideoPost
if c4d.plugins.FindPlugin(ID_REDSHIFT, type=c4d.PLUGINTYPE_ANY) is not None:
    import redshift

class AOVHelper:
    """
    Custom helper to easier modify AOV.
    """

    def __init__(self, vp: c4d.documents.BaseVideoPost = None):
        
        if isinstance(vp, c4d.documents.BaseVideoPost):
            if vp.GetType() == int(ID_REDSHIFT):
                self.doc = vp.GetDocument()
                self.vp: c4d.documents.BaseVideoPost = vp
                self.vpname: str = self.vp.GetName()

        elif vp is None:
            self.doc: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
            self.vp: c4d.documents.BaseVideoPost = GetVideoPost(self.doc, ID_REDSHIFT)
            self.vpname: str = self.vp.GetName()

    def __str__(self) -> str:
        return (f'<Redshift> {__class__.__name__} with videopost named {self.vpname}')

    # 获取aov默认名称 ==> ok
    def get_type_name(self, aov_type: c4d.BaseList2D) -> str:
        """
        Get the name string of given aov type.
        """
        for i in REDSHIFT_AOVS:
            if i == aov_type:
                return REDSHIFT_AOVS_NAME[REDSHIFT_AOVS.index(i)]

    # 获取aov名称 ==> ok
    def get_name(self, aov: int|c4d.redshift.RSAOV = None) -> str:
        """
        Get the name of given aov.
        """
        
        if aov is None:
            return
        
        if isinstance(aov, c4d.redshift.RSAOV):
            return aov.GetParameter(c4d.REDSHIFT_AOV_NAME)

        if isinstance(aov, int):
            return self.get_aov(aov).GetParameter(c4d.REDSHIFT_AOV_NAME)

    # 设置aov名称 ==> ok
    def set_name(self, aov: int|c4d.redshift.RSAOV = None, name: str = None) -> str:
        """
        Set the name of given aov.
        """
        if aov is None:
            return
        
        return self.update_aov(aov, c4d.REDSHIFT_AOV_NAME, aov_attrib = name)

    # 获取所有aov shader ==> ok
    def get_all_aovs(self) -> list[c4d.redshift.RSAOV] :
        """
        Get all aovs in a list.

        Returns:
            list[c4d.BaseShader]: A List of all find aovs
        """

        return redshift.RendererGetAOVs(self.vp)

    # 获取指定类型的aov列表 ==> ok
    def get_aovs(self, aov_type: c4d.BaseList2D) -> list[c4d.redshift.RSAOV]:
        """
        Get all the aovs of given type in a list.

        """
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        
        aov_list: list = []
        
        # keep original aovs
        current_aovs = redshift.RendererGetAOVs(self.vp)
        for aov in current_aovs:
            if aov.GetParameter(c4d.REDSHIFT_AOV_TYPE) == aov_type:
                aov_list.append(aov)

        return aov_list
    
    # 获取指定类型的aov shader ==> ok
    def get_aov(self, aov_type: c4d.BaseList2D) -> c4d.redshift.RSAOV|None:
        """
        Get the aov of given type.

        """
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
                
        # keep original aovs
        current_aovs = redshift.RendererGetAOVs(self.vp)
        for aov in current_aovs:
            if aov.GetParameter(c4d.REDSHIFT_AOV_TYPE) == aov_type:
                return aov

        return None
    
    # 打印aov ==> ok
    def print_aov(self):
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")

        aovs = redshift.RendererGetAOVs(self.vp)
        aovCnt = len(aovs)
        
        print ("--- REDSHIFTRENDER ---")
        
        print ("Name:", self.vp.GetName())
        print ("Color space:", self.vp[c4d.REDSHIFT_RENDERER_COLOR_MANAGEMENT_OCIO_RENDERING_COLORSPACE])
        print ("AOV count:", aovCnt)        
        
        for aov in aovs:
            aov_name = aov.GetParameter(c4d.REDSHIFT_AOV_NAME)
            aov_type = aov.GetParameter(c4d.REDSHIFT_AOV_TYPE)
            if aov_name == '':
                aov_name = REDSHIFT_AOVS_NAME[aov_type]
            
            print("-----------------------------------------------------------")
            print("Name                  :%s" % aov_name)
            print("Type                  :%s" % str(REDSHIFT_AOVS[aov_type]))
            print("Enabled               :%s" % ("Yes" if aov.GetParameter(c4d.REDSHIFT_AOV_ENABLED) else "No"))
            print("Multi-Pass            :%s" % ("Yes" if aov.GetParameter(c4d.REDSHIFT_AOV_MULTIPASS_ENABLED) else "No"))
            print("Direct                :%s" % ("Yes" if aov.GetParameter(c4d.REDSHIFT_AOV_FILE_ENABLED) else "No"))
            print("Direct Path           :%s" % aov.GetParameter(c4d.REDSHIFT_AOV_FILE_PATH))
            print("Direct Effective Path :%s" % aov.GetParameter(c4d.REDSHIFT_AOV_FILE_EFFECTIVE_PATH)) # Available from 2.6.44/3.0.05
        
        print ("--- REDSHIFTRENDER ---")
    
    # 创建aov ==> ok
    def create_aov_shader(self, aov_type: c4d.BaseList2D, aov_enabled: bool = True, aov_name: str = None, muti_enabled: bool = True, muti_bit: int = 16) -> c4d.redshift.RSAOV:
                
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")

        aov: c4d.redshift.RSAOV = redshift.RSAOV()
        aov.SetParameter(c4d.REDSHIFT_AOV_TYPE, aov_type)
        aov.SetParameter(c4d.REDSHIFT_AOV_ENABLED, aov_enabled)
        if aov_name is not None:
            aov.SetParameter(c4d.REDSHIFT_AOV_NAME, aov_name)
        else:
            aov.SetParameter(c4d.REDSHIFT_AOV_NAME, self.get_type_name(aov_type))
        aov.SetParameter(c4d.REDSHIFT_AOV_MULTIPASS_ENABLED, muti_enabled)
        
        # zip
        if muti_bit == 16: 
            bit = c4d.REDSHIFT_AOV_MULTIPASS_BIT_DEPTH_16
        elif muti_bit == 8:
            bit = c4d.REDSHIFT_AOV_MULTIPASS_BIT_DEPTH_8
        elif muti_bit == 32:
            bit = c4d.REDSHIFT_AOV_MULTIPASS_BIT_DEPTH_32
        else:
            bit = c4d.REDSHIFT_AOV_MULTIPASS_BIT_DEPTH_16
        aov.SetParameter(c4d.REDSHIFT_AOV_MULTIPASS_BIT_DEPTH, bit)
        
        # denoise
        try:
            aov.SetParameter(c4d.REDSHIFT_AOV_DENOISE_ENABLED, True)
        except:
            pass        

        return aov
    
    # 为aov添加属性,在添加到vp之前 ==> ok
    def set_aov(self, aov_shader: c4d.BaseList2D , aov_id : int, aov_attrib):
                
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        if not isinstance(aov_shader,c4d.redshift.RSAOV):
            raise ValueError(f"Aov must be the {self.vpname} aov")

        aov_shader.SetParameter(aov_id, aov_attrib)
    
    # 更新aov属性 ==> ok
    # todo新建的AOV会丢失属性
    def update_aov_old(self, aov_type: int|c4d.redshift.RSAOV, aov_id : int, aov_attrib) -> c4d.redshift.RSAOV:
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        
        if isinstance(aov_type, c4d.redshift.RSAOV):
            aovshader = aov_type
        if isinstance(aov_type, int):
            aovshader = self.get_aov(aov_type) 
             
        aovshader = self.get_aov(aov_type)
        if aovshader is None:
            return
        
        aov_list: list = []
        # keep original aovs
        current_aovs = redshift.RendererGetAOVs(self.vp)
        self.remove_aov_type(aov_type)
        for aov in current_aovs:
            if aov.GetParameter(c4d.REDSHIFT_AOV_TYPE) == aov_type:
                aov_list.append(aovshader)
            else:
                aov_list.append(aov)
        
        self.set_aov(aovshader,aov_id, aov_attrib)
        # set aovs
        redshift.RendererSetAOVs(self.vp, aov_list)
        return aovshader

    def update_aov(self, aov_type: int|c4d.redshift.RSAOV, aov_id: int, aov_attrib):
        allaovs = self.get_all_aovs()
        aov_update_list = []
        for aov in allaovs:
            if aov.GetParameter(c4d.REDSHIFT_AOV_TYPE) == aov_type:
                aov_update_list.append(aov)
        aovs_temp = [allaovs.remove(aov_update) for aov_update in aov_update_list]
        [self.set_aov(aov_update, aov_id, aov_attrib) for aov_update in aov_update_list]
        aovs_temp.extend(aov_update_list)
        return redshift.RendererSetAOVs(self.vp, aovs_temp)

    # 将aov添加到vp ==> ok
    def add_aov(self, aov_shader: c4d.redshift.RSAOV|list[c4d.redshift.RSAOV]):
        
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        if not isinstance(aov_shader,c4d.redshift.RSAOV):
            raise ValueError(f"Aov must be the {self.vpname} aov")
        
        aov_list: list = []

        # aov
        if isinstance(aov_shader, c4d.redshift.RSAOV):
            
            # keep original aovs
            current_aovs = redshift.RendererGetAOVs(self.vp)
            for aov in current_aovs:
                aov_list.append(aov)
            # add our new aov  
            aov_list.append(aov_shader)
            # set aovs
            redshift.RendererSetAOVs(self.vp, aov_list)

        # aovs
        if isinstance(aov_shader, list):
            
            # keep original aovs
            current_aovs = redshift.RendererGetAOVs(self.vp)
            # merge aovs
            aov_list = current_aovs + aov_shader
            # set aovs
            redshift.RendererSetAOVs(self.vp, aov_list)
        return aov_shader

    # 删除最新的aov ==> ok
    def remove_last_aov(self):
        """
        Remove the last aov shader.

        """
        # index: Union[int,c4d.BaseList2D]
        
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        
        aovs = redshift.RendererGetAOVs(self.vp)
        del(aovs[-1])
        redshift.RendererSetAOVs(self.vp, aovs)

    # 删除全部aov ==> ok
    def remove_all_aov(self):
        """
        Remove all the aov shaders.

        """
        
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        aovs = []
        redshift.RendererSetAOVs(self.vp, aovs)  
                       
    # 按照Type删除aov ==> ok
    def remove_aov_type(self, aov_type: int):
        """
        Remove aovs of the given aov type.

        :param aov_type: the aov type to remove
        :type aov_type: int
        """
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        
        aov_list: list = []
        
        # keep original aovs
        current_aovs = redshift.RendererGetAOVs(self.vp)
        for aov in current_aovs:
            if aov.GetParameter(c4d.REDSHIFT_AOV_TYPE) == aov_type:
                continue
            aov_list.append(aov)
        # set aovs
        redshift.RendererSetAOVs(self.vp, aov_list)

    # 添加灯光组 ==> ok
    def set_light_group(self, aov: c4d.redshift.RSAOV, group_name: str = None):
        if aov is None:
            return
        if group_name is None:
            return
        
        if isinstance(aov, c4d.redshift.RSAOV):
            aovtype = 	aov.GetParameter(c4d.REDSHIFT_AOV_TYPE)
            aovshader = aov
        if isinstance(aov, int):
            aovtype = aov
            aovshader = self.get_aov(aov)
        or_str = aovshader.GetParameter(c4d.REDSHIFT_AOV_LIGHTGROUP_NAMES)
        if or_str == "":
            group_str = group_name + "\n"
        else:
            group_str = or_str + "\n" + group_name + "\n"
        self.update_aov(aov_type=aovtype, aov_id=c4d.REDSHIFT_AOV_LIGHTGROUP_NAMES, aov_attrib=group_str)

    # 添加灯光组 ==> ok   
    def active_light_group(self, aov: c4d.redshift.RSAOV, group_name: str = None):
        if aov is None:
            return
        if group_name is None:
            return
        or_group = aov.GetParameter(c4d.REDSHIFT_AOV_LIGHTGROUP_NAMES)
        
        if group_name not in or_group:
            group_str = or_group + "\n" + group_name.strip() + "\n"
            self.set_light_group(aov,group_str)
            
    # 添加纯白puzzle matte ==> ok
    def set_puzzle_matte(self, puzzle_id: int = 1, aov_enabled: bool = True, aov_name: str = None, muti_enabled: bool = True, muti_bit: int = 16):
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        if aov_name is not None:
            aov_name = aov_name
        else:
            aov_name =  "Puzzle " + str(puzzle_id)
        
        aov = self.create_aov_shader(REDSHIFT_AOV_TYPE_PUZZLE_MATTE, aov_enabled, aov_name, muti_enabled, muti_bit)
        
        # object mode
        aov.SetParameter(c4d.REDSHIFT_AOV_PUZZLE_MATTE_MODE, REDSHIFT_AOV_PUZZLE_MATTE_MODE_OBJECT_ID)        
        # set a white puzzle
        aov.SetParameter(c4d.REDSHIFT_AOV_PUZZLE_MATTE_RED_ID, puzzle_id)
        aov.SetParameter(c4d.REDSHIFT_AOV_PUZZLE_MATTE_GREEN_ID, puzzle_id)
        aov.SetParameter(c4d.REDSHIFT_AOV_PUZZLE_MATTE_BLUE_ID, puzzle_id)
        aov.SetParameter(c4d.REDSHIFT_AOV_PUZZLE_MATTE_REFLECTION_REFRACTION, False)
        self.add_aov(aov)
        return aov

__all__ = [
    "AOVHelper"
]
