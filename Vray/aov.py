# coding=utf-8

import c4d

from typing import Generator, Optional
from ..constants import *
from ..utils import GetVideoPost

class AOVHelper:

    """
    Custom helper to modify Vray AOVs. vray aovs store in render element scene hook with c4d.BaseObject.
    """

    def __init__(self, vp: c4d.documents.BaseVideoPost = None):
        
        if isinstance(vp, c4d.documents.BaseVideoPost):
            if vp.GetType() == int(ID_VRAY):
                self.doc = vp.GetDocument()
                self.vp: c4d.documents.BaseVideoPost = vp
                self.vpname: str = self.vp.GetName()
                self.head: c4d.GeListHead = self.get_master_head()

        elif vp is None:
            self.doc: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
            self.vp: c4d.documents.BaseVideoPost = GetVideoPost(self.doc, ID_VRAY)
            self.vpname: str = self.vp.GetName()
            self.head: c4d.GeListHead = self.get_master_head()

        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        if self.head is None:
            raise RuntimeError(f"Can't get the Render Element for {self.vpname}")

    # 名称对照字典 DEV
    def _convert_namedata(self) -> None:
        """
        A help function to convert list, you should no need use this, just for dev.
        """
        for node in self.get_all_aovs():
            name = f"VRAY_AOV_{node.GetName()}"
            print( name.upper().replace(" ", "_"), "=", [node.GetType(), node.GetParameter(VRAY_RENDER_ELEMENT_CREATE_NODE_TYPE, c4d.DESCFLAGS_GET_NONE), name] )

    # aov data
    def get_aov_data(self) -> Optional[dict[str,int]]:
        """
        Get all aov data in a list of BaseContainer.
        
        Parameters
        ----------        
        :return: the data list
        :rtype: Optional[dict[str,int]]
        """
        pass

    def iterater(self, node: c4d.BaseObject) -> Generator[None, None, c4d.BaseObject]:
        """
        Iterate the aov nodes.

        Args:
            node (c4d.BaseObject): the node we start from.
        """
        while isinstance(node, c4d.BaseObject):
            yield node

            for child in self.iterater(node.GetDown()):
                yield child

            node = node.GetNext()

    # 获取Render Elemnt的GeListHead
    def get_master_head(self) -> Optional[c4d.GeListHead]:
        """Get the master head of the render element.
        """
        sceneHook: c4d.BaseList2D = self.doc.FindSceneHook(ID_VRAY_RENDER_ELEMENTS_SCENE_HOOK)
        if sceneHook is None:
            return None
        info = sceneHook.GetBranchInfo(c4d.GETBRANCHINFO_NONE)
        if info is None:
            return None
        head = info[0]["head"]
        if head is None:
            return None
        return head

    def get_type(self, node: c4d.BaseObject) -> int:
        """Get the type of the given node."""
        return node.GetParameter(VRAY_RENDER_ELEMENT_CREATE_NODE_TYPE, c4d.DESCFLAGS_GET_NONE)

    def get_name(self, node: c4d.BaseObject) -> str:
        """Get the name of the given node."""
        return node.GetName()

    def get_enable(self, node: c4d.BaseObject) -> bool:
        """Get the enable check of the given node."""
        return node.GetParameter(VRAY_RENDER_ELEMENT_ENABLED, c4d.DESCFLAGS_GET_NONE)

    def get_filter(self, node: c4d.BaseObject) -> bool:
        """Get the filter check of the given node."""
        return node.GetParameter(VRAY_RENDER_ELEMENT_FILTER_PARAMETER_ID, c4d.DESCFLAGS_GET_NONE)

    def get_denoise(self, node: c4d.BaseObject) -> bool:
        """Get the denoise check of the given node."""
        return node.GetParameter(VRAY_RENDER_ELEMENT_DENOISE_PARAMETER_ID, c4d.DESCFLAGS_GET_NONE)

    def set_type(self, node: c4d.BaseObject, arg: int) -> bool:
        """Set the type of the given node."""
        return node.SetParameter(VRAY_RENDER_ELEMENT_CREATE_NODE_TYPE, arg, c4d.DESCFLAGS_SET_NONE)

    def set_name(self, node: c4d.BaseObject, arg: str) -> str:
        """Set the name of the given node."""
        return node.SetName(arg)

    def set_enable(self, node: c4d.BaseObject, arg: int) -> bool:
        """Set the enable check of the given node."""
        return node.SetParameter(VRAY_RENDER_ELEMENT_ENABLED, arg, c4d.DESCFLAGS_GET_NONE)

    def set_filter(self, node: c4d.BaseObject, arg: int) -> bool:
        """Set the filter check of the given node."""
        return node.SetParameter(VRAY_RENDER_ELEMENT_FILTER_PARAMETER_ID, arg, c4d.DESCFLAGS_GET_NONE)

    def set_denoise(self, node: c4d.BaseObject, arg: int) -> bool:
        """Set the denoise check of the given node."""
        return node.SetParameter(VRAY_RENDER_ELEMENT_DENOISE_PARAMETER_ID, arg, c4d.DESCFLAGS_GET_NONE)

    # 获取所有aov shader ==> ok
    def get_all_aovs(self) -> list[c4d.BaseShader] :
        """
        Get all vray aovs in a list.

        Returns:
            list[c4d.BaseShader]: A List of all find nodes

        """
        
        """Get all render elements in the scene."""
        res = []
        for node in self.iterater(self.get_master_head().GetFirst()):
            res.append(node)
        return res

    # 获取指定类型的aov shader ==> ok
    def get_aov(self, aov_type: c4d.BaseObject) -> list[c4d.BaseObject]:
        """
        Get all the aovs of given type in a list.
        
        Args:
            aov_type (Union[c4d.BaseObject, c4d.BaseShader]): Shader to iterate.
            
        Returns:
            list[c4d.BaseObject]: A List of all find aovs

        """

        # The list.
        result: list = []

        start_shader = self.get_master_head().GetFirst()
        if not start_shader:
            return result
        for obj in self.iterater(start_shader):
            if self.get_type(obj) != aov_type:
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
        
        aovs = self.get_all_aovs()
        aovCnt = len(aovs)
        color_space = self.vp[c4d.SETTINGSUNITSINFO_RGB_COLOR_SPACE]
        if color_space == 1:
            color_str = "sRGB"
        elif color_space == 2:
            color_str = "ACEScg"
                      
        print ("--- VRAY RENDER ---")
        print ("Name:", self.vp.GetName())
        print ("Color space:", color_str)
        print ("AOV count:", aovCnt)
        
        if aovCnt == 0:
            print("No AOV data in this scene.")
        else:
            for aov in aovs:
                if aov is not None:
                    aov_enabled = self.get_enable(aov)
                    aov_name = self.get_name(aov)
                    aov_type = self.get_type(aov)

                    print("--"*10)
                    print("Name                  :%s" % aov_name)
                    print("Type                  :%s" % str(aov_type))
                    print("Enabled               :%s" % ("Yes" if aov_enabled else "No"))

                    
                    #print(SET_RENDERAOV_INPUT_0)
                    # print('aov1',self.vp[SET_RENDERAOV_INPUT_0])
                    #print(SET_RENDERAOV_INPUT_0+1)
                            
                    # Z-Depth
                    if aov_type == 117:
                        print ("Subdata: Z-depth black:",aov[c4d.RENDERCHANNELZDEPTH_DEPTH_BLACK],
                               "Z-depth white:",aov[c4d.RENDERCHANNELZDEPTH_DEPTH_WHITE],
                               "Invert:",aov[c4d.RENDERCHANNELZDEPTH_DEPTH_INVERT])

                    # Cryptomatte
                    if aov_type == 158:
                        print ("Subdata: Cryptomatte type:", aov[c4d.RENDERCHANNELCRYPTOMATTE_ID_TYPE])
                
        print ("--- VRAY RENDER ---")

    # 创建aov ==> ok
    def create_aov_shader(self, aov_type: list[int], aov_name: str = None) -> c4d.BaseShader :
        """
        Create a shader of vray aov.

        :param aov_tye: the aov int type, this is a list of main id and sub type of the aov, find it in vray_id.py
        :type aov_tye: int, optional
        :param aov_name: the aov name, defaults to ""
        :type aov_name: str, optional 
        :return: the aov shader
        :rtype: c4d.BaseShader
        """
        if not isinstance(aov_type, list):
            raise ValueError("We should use a custom list data here: [the object type, the sub type, aov nae(optional)]")

        aov = c4d.BaseObject(aov_type[0])
        self.set_type(aov, aov_type[1])

        if aov_name:
            self.set_name(aov, aov_name)
        else:
            self.set_name(aov, aov_type[2])

        return aov
    
    # 将aov添加到vp ==> ok
    def add_aov(self, aov_shader: c4d.BaseObject) -> c4d.BaseObject:
        """
        Add the vray aov shader to Octane Render.

        :param aov_shader: the vray aov shader
        :type aov_shader: c4d.BaseObject
        :return: the vray aov shader
        :rtype: c4d.BaseList2D
        """
        if not isinstance(aov_shader, c4d.BaseObject):
            raise ValueError("Vray AOV must be a c4d.BaseObject")
        
        # insert octane_aov to new port
        try:
            self.head.InsertFirst(aov_shader)
            self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,aov_shader)
        except:
            pass        
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
        self.get_all_aovs()[0].Remove()

    # 删除全部aov ==> ok
    def remove_all_aov(self):
        """
        Remove all the aov shaders.

        """
        for aov in self.get_all_aovs():
            if isinstance(aov, c4d.BaseObject):
                aov.Remove()  

    # 按照Type删除aov ==> ok
    def remove_aov_type(self, aov_type: int, filter_type: int = None):
        """
        Remove aovs of the given aov type.

        :param aov_type: the aov type to remove
        :type aov_type: int
        """
        for aov in self.get_all_aovs():
            if aov.CheckType(aov_type):
                if filter_type is not None:
                    if self.get_type(aov) == filter_type:
                        aov.Remove()  
                else:
                    aov.Remove() 


__all__ = [
    "AOVHelper"
]
