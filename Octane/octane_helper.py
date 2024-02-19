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
import c4d
from typing import Optional,Union, Any
import os
import sys
import re
import random

import Renderer
from Renderer.constants.octane_id import *

def iterate(node):
    while isinstance(node, c4d.BaseList2D):
        yield node

        for child in iterate(node.GetDown()):
            yield child

        node = node.GetNext()


class AOVHelper:

    """
    Custom helper to modify Arnold AOV(Driver).
    """

    def __init__(self, vp: c4d.documents.BaseDocument = None):
        
        if isinstance(vp, c4d.documents.BaseVideoPost):
            if vp.GetType() == int(Renderer.ID_REDSHIFT):
                self.doc = vp.GetDocument()
                self.vp: c4d.documents.BaseVideoPost = vp
                self.vpname: str = self.vp.GetName()

        elif vp is None:
            self.doc: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
            self.vp: c4d.documents.BaseVideoPost = Renderer.GetVideoPost(self.doc, Renderer.ID_REDSHIFT)
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
    def get_aov_data(self) -> Union[list[c4d.BaseContainer], None]:
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
        
        if aov_name == "":
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
    def get_custom_aov(self, customID: int = 1) -> Union[c4d.BaseList2D, None]:
        """
        Get the custom aov shader of given id.

        :param customID: the custom id, defaults to 1
        :type customID: int, optional
        :return: the aov shader
        :rtype: Union[c4d.BaseList2D, None]
        """
        est_aovs = self.get_aov(RNDAOV_CUSTOM)
        for aov in est_aovs:
            if aov[c4d.RNDAOV_CUSTOM_IDS] == customID - 1: # start at 0
                return aov
        else: return None

    # 添加custom aov（id） ==> ok
    def add_custom_aov(self, customID: int = 1) -> Union[c4d.BaseList2D, None]:
        """
        Add the custom aov shader of given id if it not existed.

        :param customID: the custom id, defaults to 1
        :type customID: int, optional
        :return: the aov shader
        :rtype: Union[c4d.BaseList2D, None]
        """
        if self.get_custom_aov(customID) is None:
            aov = self.create_aov_shader(RNDAOV_CUSTOM)            
            self.add_aov(aov)
            aov[c4d.RNDAOV_CUSTOM_IDS] = customID - 1
            return aov

    # 获取light aov（id） ==> ok
    def get_light_aov(self, lightID: int = 1) -> Union[c4d.BaseList2D, None]:
        """
        Get the light aov shader of given id.

        :param lightID: the light id, defaults to 1
        :type lightID: int, optional
        :return: the aov shader
        :rtype: Union[c4d.BaseList2D, None]
        """
        est_aovs = self.get_aov(RNDAOV_LIGHT)
        if est_aovs is None: return None
        for aov in est_aovs:
            if aov[c4d.RNDAOV_LIGHT_ID] == lightID + 1: # start at 0
                return aov
        else: return None

    # 添加light aov（id） ==> ok
    def add_light_aov(self, lightID: int = 1, lightName: str = None) -> Union[c4d.BaseList2D, None]:
        """
        Add the light aov shader of given id if it not existed.

        :param lightID: the light id, defaults to 1
        :type lightID: int, optional
        :return: the aov shader
        :rtype: Union[c4d.BaseList2D, None]
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
        :rtype: Union[c4d.BaseList2D, None]
        """
        est_aovs = self.get_aov(RNDAOV_LIGHT)
        if est_aovs is None: return None
        for aov in est_aovs:
            if aov[c4d.RNDAOV_LIGHT_ID] == lightID + 1: # start at 0
                aov.Remove()
        self.remove_empty_aov()
        return None


class MaterialHelper:
    """
    material_types:
        ID_OCTANE_STANDARD_SURFACE,
        ID_OCTANE_BASE_MATERIAL,
        ID_OCTANE_COMPOSITE_MATERIAL
    """

    #=============================================
    # Basic
    #=============================================

    def __init__(self, material: c4d.BaseMaterial = None, create_standard: bool = False):
        
        self.materialType: str = "Octane"

        # First we want to modify exsited material
        if isinstance(material, c4d.BaseMaterial):
            if not self.IsOctaneMaterial(material):
                raise ValueError("This is not an Octane Material")
            self.material: c4d.BaseMaterial = material

        else:
            if create_standard:
                self.material: c4d.BaseMaterial = self.CreateStandardMaterial()
            else:
                self.material: c4d.BaseMaterial = self.CreateBasicMaterial(matType = MAT_TYPE_UNIVERSAL)

        # if self.material is None:
        #     raise ValueError(f"Cann't create Octane NodeHelper with {material}")
        
        self.doc = self.SetDocument()

    def __str__(self):
        return (f"A Octane {self.__class__.__name__} Instance with Material : {self.material.GetName()}")

    #=============================================
    # Util
    #=============================================
    
    # 判断是否为Octane材质 ==> ok
    def IsOctaneMaterial(self, material: c4d.BaseMaterial) -> bool:
        """
        Check if the host material is an Octane Material.

        Returns:
            bool: True if the host material is an Octane Material, False otherwise.
        """
        if isinstance(material, c4d.BaseMaterial):
            if material.GetType() in OCTANE_MATERIALS:
                return True
        return False

    # 创建Standard Surface材质 ==> ok
    def CreateStandardMaterial(self, matName: str = None, isMetal: bool = False) -> c4d.BaseMaterial:
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
                material.SetName(MAT_NAME_SYMBOLS.get(ID_OCTANE_STANDARD_SURFACE))
            else:
                material.SetName(matName)
                
            # Update material
            material.Update(True, True)
            return material
        
        except :
            ValueError("Cannot create Octane Material.")

    # 创建基础材质 ==> ok
    def CreateBasicMaterial(self, isMetal: bool = False, matType: int = MAT_TYPE_UNIVERSAL, matName: str = None) -> c4d.BaseMaterial:
        """
        Create an Octane Basic(classic) material of given type and name.
        """

        # Basic Octane Mat Type 
        material = c4d.BaseMaterial(ID_OCTANE_BASE_MATERIAL)
        if material is None:
            raise ValueError("Cannot create a BaseMaterial")

        material[c4d.OCT_MATERIAL_DIFFUSE_COLOR] = c4d.Vector(0.7,0.7,0.7) # albedo

        if matType == MAT_TYPE_SPECULAR:
            material[c4d.OCT_MATERIAL_FAKESHADOW] = True # fake shadow

        if isMetal:
            material[c4d.OCT_MATERIAL_TYPE] = MAT_TYPE_UNIVERSAL
            material.SetName(MAT_NAME_SYMBOLS.get(MAT_TYPE_UNIVERSAL))
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

            # Name
            if not matName:
                for name in MAT_NAME_SYMBOLS.keys():
                    matName = MAT_NAME_SYMBOLS.get(name)
                    if matName == material[c4d.OCT_MATERIAL_TYPE]:
                        material.SetName(DiffuseName)

            else:
                material.SetName(matName)
       
        material.Update(True, True)
        return material

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
                material.SetName(MAT_NAME_SYMBOLS.get(ID_OCTANE_COMPOSITE_MATERIAL))
                
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

    # 设置材质 ==> ok
    def SetMaterial(self, material: c4d.BaseMaterial) -> c4d.BaseMaterial:
        """
        Set the host material of the helper class.

        Args:
            material (c4d.BaseMaterial): the host material.

        Returns:
            c4d.BaseMaterial: #material attribute of the class
        """

        if isinstance(material, c4d.BaseMaterial):
            if not self.IsOctaneMaterial():
                raise ValueError("This is not an Octane Material")
        self.material: c4d.BaseMaterial = material
        return self.material
    
    # 获取材质 ==> ok
    def GetMaterial(self) -> c4d.BaseMaterial:
        """
        Get the host material of the helper class.

        Returns:
            c4d.BaseMaterial: #material attribute of the class
        """
        return self.material

    # 设置文档 ==> ok
    def SetDocument(self, doc: c4d.documents.BaseDocument = None) -> c4d.documents.BaseDocument:
        """
        Set the document of the helper class.

        Args:
            doc (c4d.documents.BaseDocument): the document.

        Returns:
            c4d.documents.BaseDocument: #doc attribute of the class
        """
        if not doc:
            # We try to get the document
            if isinstance(self.material, c4d.BaseMaterial):
                self.doc: c4d.documents.BaseDocument = self.material.GetDocument()

            if self.doc is None:
                self.doc: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
        else:
            if not isinstance(doc, c4d.documents.BaseDocument):
                raise TypeError("The document must be of type c4d.documents.BaseDocument")
            self.doc = doc
        return self.doc

    # 获取文档 ==> ok
    def GetDocument(self) -> c4d.documents.BaseDocument:
        """
        Get the document of the helper class.

        Returns:
            c4d.documents.BaseDocument: #doc attribute of the class
        """
        return self.doc

    # 插入 ==> ok
    def InsertMaterial(self, doc: c4d.documents.BaseDocument = None) -> c4d.BaseMaterial:
        """
        Insert the material to the document.
        """
        if self.material is None: return False
        #self.material.Update(True, True)

        if not doc:
            doc = self.material.GetDocument()
            if doc is None:
                doc = c4d.documents.GetActiveDocument()

        doc.InsertMaterial(self.material)
        doc.AddUndo(c4d.UNDOTYPE_NEW, self.material)
        return self.material

    # 刷新材质 ==> ok
    def Refresh(self):
        """
        Refresh thumbnail.
        """
        self.material.Update(True, True)

    # 设置激活 ==> ok
    def SetActive(self, doc: c4d.documents.BaseDocument = None):
        """
        Set the material active in the document.
        """
        if self.material is not None:
            if not doc:
                doc = self.material.GetDocument()
                if doc is None:
                    doc = c4d.documents.GetActiveDocument()
            doc.SetActiveMaterial(self.material)
            doc.AddUndo(c4d.UNDOTYPE_BITS, self.material)

    # 获取节点名 ==> ok
    def GetName(self, node: c4d.BaseShader) -> str:
        """
        Retrieve the displayed name of a node. 
        This is a function to maintain consistency, and it is generally recommended to use BaseList2D.GetName()

        Args:
            node (maxon.GraphNode): the node

        Returns:
            Optional[str]: the name of the ndoe
        """
        if not isinstance(node, c4d.BaseShader):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a BaseShader, got {type(node)}')
            
        return node.GetName()

    # 设置节点名
    def SetName(self, node: c4d.BaseShader, name: str) -> bool:
        """
        Set the name of a node.
        This is a function to maintain consistency, and it is generally recommended to use BaseList2D.SetName()

        Args:
            node (c4d.BaseShader): the node
            name (str): the name of the node

        Returns:
            bool: True if the name has been changed.
        """
        if not isinstance(node, c4d.BaseShader):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a BaseShader, got {type(node)}')
        
        if not isinstance(name, str):
            raise ValueError('Expected a String, got {}'.format(type(name)))
        
        node.SetName(name)
        return True

    # 获取所有shader ==> ok
    def GetAllShaders(self) -> list[c4d.BaseList2D] :
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

    # 添加Nodes ==> ok
    def AddShader(self, shaderID: int = None, parentNode: c4d.BaseList2D = None) -> c4d.BaseShader:
        """
        Add a shader to the material of the given type and slot.

        """
        theNode = c4d.BaseList2D(shaderID)
        if parentNode:
            self.material[parentNode] = theNode                                     
        self.material.InsertShader(theNode)
        if self.doc is not None:
            self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, self.material)
        return theNode

    # todo
    def AddConnectShader(self):
        pass

    # todo
    def InsertShader(self):
        pass

    # todo
    def RemoveShader(self, shader: c4d.BaseShader) -> None:
        return shader.Remove()

    # 是否是shader ==> ok
    def IsNode(self, node: c4d.BaseShader) -> bool:
        """
        Check if a true node is a valid node.

        Args:
            node (c4d.BaseShader): the node to check

        Returns:
            bool: True if node is a valid True node
        """
        return isinstance(node, c4d.BaseShader)

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

    # 获取属性 ==> ok
    def GetShaderValue(self, node: c4d.BaseShader, paramId: Any = None) -> Any:
        """
        Returns the value stored in the given shader parameter.

        Args:
            node (c4d.BaseShader): the node
            paramId (Any): the port id. Defaults to None.

        Returns:
            maxon.Data: the value assigned to this port
        """
        # standard data type
        
        if not isinstance(node, c4d.BaseShader):
            raise TypeError("The given node is not a shader")
        if paramId is None:
            raise ValueError("The given paramId is None")
        try:
            return node[paramId]
        except Exception:
            return None

    # 设置属性 ==> ok
    def SetShaderValue(self, node: c4d.BaseShader, paramId: Any = None, value: Any = None) -> bool:
        """
        Sets the value stored in the given shader parameter.

        Args:
            node (c4d.BaseShader): the node
            paramId (Any): the port id. Defaults to None.
            value (Any): the value to set. Defaults to None.

        Returns:
            bool: True if the value has been changed.
        """

        if not isinstance(node, c4d.BaseShader):
            raise TypeError("The given node is not a shader")
        if paramId is None:
            raise ValueError("The given paramId is None")
    
        try:
            node[paramId] = value
            return True
        except Exception:
            return False

    # New 获取前方节点(只包含子节点)  ==> ok
    def GetPreNode(self, node: c4d.BaseShader) -> list[c4d.BaseShader]:
        """
        Return the nodes directly connected before the node.

        Args:
            node (c4d.BaseShader): the node

        Returns:
            list[c4d.BaseShader]: Return the nodes directly connected before the node.
        """
        result = list()
        for _ ,shader in self.GetConnections(node):
            result.append(shader)
        return result

    # New 获取后方节点(只包含子节点)  ==> ok
    def GetNextNode(self, node: c4d.BaseShader) -> list[c4d.BaseShader]:
        """
        Return the nodes directly connected after the node.

        Args:
            node (c4d.BaseShader): the node

        Returns:
            list[c4d.BaseShader]: Return the nodes directly connected after the node.
        """
        # Bail when the passed node is not a true node.
        if not isinstance(node, c4d.BaseShader):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a BaseShader, got {type(node)}')
        # The list.
        result: list = []
        for shader in self.GetAllShaders():
            for i in self.GetConnections(shader):
                if i[1] == node:                
                    result.append(shader)
        return result
    
    # New 获取前方节点树(包含节点树)  ==> ok
    def GetPreNodes(self, node: c4d.BaseShader, filter_asset: str = None) -> list:
        """
        Return the nodes connected before the node, include all the node chain.

        Args:
            node (c4d.BaseShader): the node
            filter_asset (str): the shader id we will keep, fill none to disable.

        Returns:
            list[c4d.BaseShader]: Return the nodes connected before the node, include all the node chain.
        """
        # Bail when the passed node is not a true node.
        if not isinstance(node, c4d.BaseShader):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a BaseShader, got {type(node)}')
        
        # The list.
        result: list = []

        for shader in iterate(node):
            if filter_asset is not None:
                if shader.GetType() == filter_asset and shader not in result:
                    result.append(shader)
            else:
                if shader not in result:
                    result.append(shader)

        # remove the node self
        result.remove(node)

        return result
    
    # New 获取后方节点树(包含节点树)  ==> ok
    def GetNextNodes(self, node: c4d.BaseShader, filter_asset: str = None) -> list:
        """
        Return the nodes connected after the node, include all the node chain.

        Args:
            node (c4d.BaseShader): the node

            filter_asset (str): the asset id we will keep, fill none to disable.

        Returns:
            list[c4d.BaseShader]: Return the nodes connected after the node, include all the node chain.
        """
        # Bail when the passed node is not a true node.
        if not isinstance(node, c4d.BaseShader):
            raise ValueError(f'{sys._getframe().f_code.co_name} Expected a BaseShader, got {type(node)}')
        # The list.
        result: list = []

        for shader in self.GetAllShaders():
            if node in self.GetPreNodes(shader):
                result.append(shader)

        return result

    # 获取材质上被连接的端口列表 ==> ok
    def GetRootConnectedNodes(self) -> list[c4d.BaseShader]:
        """
        Get all root connected ports of given node of the shader in a list.

        Returns:
            list[c4d.BaseShader]: A List of all find nodes

        """
        # The list.
        result: list = []

        bc = self.material.GetDataInstance()
        if bc is None:
            raise RuntimeError("Failed to retrieve bc")
        for key in range(len(bc)):           
            key = bc.GetIndexId(key)
            try:
                if isinstance(bc[key], c4d.BaseShader):
                    result.append((key, bc[key]))
            except Exception :
                pass
        return result

    # Shader是否直连材质 ==> ok
    def IsRootShader(self, node: c4d.BaseShader) -> bool:
        """
        Check if the given node is dirctly connect to material.

        Returns:
            bool: True if connect to material, False if not.

        """
        for _, shader in self.GetRootConnectedNodes(node):
            if shader == node:
                return True
        return False
    
    # 获取shader上被连接的端口列表 ==> ok
    def GetConnections(self, node: c4d.BaseShader) -> list[tuple[int, c4d.BaseShader]]:
        """
        Get all connections of given node of the shader in a list.

        Returns:
            list[tuple[int, c4d.BaseShader]]: A list of all find nodes

        """
        # The list.
        result: list = []

        bc = node.GetDataInstance()
        if bc is None:
            raise RuntimeError("Failed to retrieve bc")

        for key in range(len(bc)):           
            key = bc.GetIndexId(key)
            if isinstance(bc[key], c4d.BaseShader):
                result.append((key, bc[key]))        
        return result

    # Shader是否独立
    def IsConnected(self, node: c4d.BaseShader) -> bool:
        """
        Check if the given node is isolated.

        Returns:
            bool: True if isolated, False if not.

        """
        if self.GetPreNode(node) or self.GetNextNode(node) or self.IsRootShader(node):
            return True
        return False

    # 寻找shader在材质上的插槽
    def GetMaterialPort(self, node: c4d.BaseShader) -> int:
        bc = self.material.GetDataInstance()
        #print(img.GetDown().GetMain())
        if bc is None:
            raise RuntimeError("Failed to retrieve bc")

        # Iterates over the content of the BaseContainer using a for loop
        for key in range(len(bc)):
            # Check if the data retrieved can be printed in python (some DataType are not supported in Python)
            key = bc.GetIndexId(key)
            try:
                if bc[key] == node:
                    # print(key, bc[key])
                    return key
            except Exception :
                pass
    
    # New 端口是否连接  ==> ok
    def IsPortConnected(self, node: c4d.BaseShader, port: int) -> bool:
        """
        Check if the port is connected.

        Args:
            port (c4d.BaseShader): The port to check.

        Returns:
            bool: True if the port is connected, False otherwise.
        """

        if not self.IsNode(port):
            raise RuntimeError("The port is not a node")
        if not port:
            raise RuntimeError("The port is empty")
        try:
            return self.IsNode(node[port])
        except Exception:
            return False

    # 查询shader连接的端口
    def GetConnectedPortAfter(self, node: c4d.BaseShader) -> int:
        """
        Add a Transform node to all the Image nodes.
        """
        for _, shader in self.GetRootConnectedNodes(node):
            if shader == node:
                return self.GetMaterialPort(node)
        
        # Get the next node.
        after_node: c4d.BaseShader = node.GetUp()

        bc = after_node.GetDataInstance()
        if bc is None:
            raise RuntimeError("Failed to retrieve bc")

        # Iterates over the content of the BaseContainer using a for loop
        for key in range(len(bc)):
            # Check if the data retrieved can be printed in python (some DataType are not supported in Python)
            key = bc.GetIndexId(key)
            try:
                if bc[key] == node:
                    return key
            except Exception :
                pass
        return False

    # 刷新贴图 ==> ok
    def RefreshTextures(self):
        """
        Reload all the texture shader.

        """
        nodes: list[c4d.BaseShader] = self.GetNodes(ID_OCTANE_IMAGE_TEXTURE)
        for node in nodes:
            node[c4d.IMAGETEXTURE_FORCE_RELOAD] = 1
            node.SetDirty(c4d.DIRTYFLAGS_ALL)
        #c4d.EventAdd()
    
    # 重置压缩 ==> ok
    def ResetCompression(self):
        """
        Reset all the texture shader compression.

        """
        nodes: list[c4d.BaseShader] = self.GetNodes(ID_OCTANE_IMAGE_TEXTURE)
        for node in nodes:
            node[c4d.IMAGETEX_COMPR_FORMAT] = 0  # reset the compression
        c4d.EventAdd()

    #=============================================
    # Presets
    #=============================================

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

    def AddImageTexture(self, texturePath: str = "", nodeName: str = None, isFloat: bool = True, gamma: int = 1,
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

    # 创建材质 ==> ok
    def SetupTextures(self, tex_data: dict = None, mat_name: Optional[str] = None):
        """
        Setup a pbr material with given or selected texture.
        """        
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
                    displacementNode[c4d.DISPLACEMENT_LEVELOFDETAIL] = 11 # 2k
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


class SceneHelper:
    """
    Class for Secne Objects, Tags, Lights, Proxy and so on.
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
    
    def add_hdr_dome(self, texture_path: str = None, visible: bool = False) -> c4d.BaseTag:
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
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,osky)
        osky.SetName('Octane HDR Dome')
        
        if texture_path:        
            env = [i for i in osky.GetTags() if i.CheckType(ID_OCTANE_ENVIRONMENT_TAG)][0]
            img = env[c4d.ENVIRONMENTTAG_TEXTURE]
            img[c4d.IMAGETEXTURE_FILE] = texture_path
            self.doc.SetActiveTag(env)            

        env[c4d.ENVTAG_SLOT] = visible

        return env

    def add_rgb_dome(self, rgb: c4d.Vector = c4d.Vector(0,0,0), visible: bool = True) -> c4d.BaseTag:
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
        env[c4d.ENVTAG_SLOT] = visible
        self.doc.InsertObject(osky)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,osky)
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
        hdr_dome: c4d.BaseObject = self.add_hdr_dome(texture_path).GetObject()
        black_dome: c4d.BaseObject = self.add_rgb_dome(rgb).GetObject()
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
        return hdr_dome

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
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,light)
        return light

    def add_light_texture(self, light_tag: c4d.BaseTag = None,  texture_path: str = None, distribution_path: str = None) -> c4d.BaseTag :
        """
        Add textures to given Octane light tag.

        """
        if not light_tag.CheckType(ID_OCTANE_LIGHT_TAG):
            raise ValueError("This is not an Octane light tag")

        def _GetTexture(host: c4d.BaseList2D) -> Union[list[c4d.BaseList2D],c4d.BaseList2D]:
            """
            Get all nodes of given type of the material in a list.

            Returns:
                list[c4d.BaseList2D]: A List of all find nodes

            """

            # The list.
            result: list = []

            start_shader = host.GetFirstShader()
            if not start_shader:
                raise RuntimeError("No shader found")
            
            for obj in iterate(start_shader):
                if obj.CheckType(ID_OCTANE_IMAGE_TEXTURE):
                    result.append(obj)

            return result[0]     
        tex_shader = light_tag[c4d.LIGHTTAG_EFFIC_OR_TEX]
        if not tex_shader:
            # Texture
            if texture_path:
                imageTextureNode_tex = c4d.BaseList2D(ID_OCTANE_IMAGE_TEXTURE)
                light_tag.InsertShader(imageTextureNode_tex)
                self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,imageTextureNode_tex)

                light_tag[c4d.LIGHTTAG_EFFIC_OR_TEX] = imageTextureNode_tex
                imageTextureNode_tex[c4d.IMAGETEXTURE_FILE] = texture_path
            
            # Distribution
            if distribution_path:
                imageTextureNod_dis = c4d.BaseList2D(ID_OCTANE_IMAGE_TEXTURE)
                light_tag.InsertShader(imageTextureNod_dis)
                self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,imageTextureNod_dis)
                light_tag[c4d.LIGHTTAG_DISTRIBUTION] = imageTextureNod_dis
                imageTextureNod_dis[c4d.IMAGETEXTURE_FILE] = distribution_path      
  
        else:
            if tex_shader.CheckType(ID_OCTANE_IMAGE_TEXTURE):
                tex_shader[c4d.IMAGETEXTURE_FILE] = texture_path
            else:
                tex_shader = _GetTexture(light_tag)
                tex_shader[c4d.IMAGETEXTURE_FILE] = texture_path
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
        sun_exp[c4d.EXPRESSION_ENABLE] = False
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
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,light)
        return light

    def add_light_modifier(self, light: c4d.BaseObject, target: Union[c4d.BaseObject,bool] = None, gsg_link: bool = False, rand_color: bool = False, seed: int = 0):
        """
        Add some modify tagsto given Octane light tag.

        """
        if not isinstance(light,c4d.BaseObject):
            raise ValueError("Need a light BaseObject")
        
        # 新建目标标签
        if target:
            mbtag = c4d.BaseTag(5676) # target
            self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, mbtag)
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
                    self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,linktag)
                    linktag[2001] = ''
            except:
                pass
        
        # 随机颜色
        if rand_color:
            light[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 1
            
            if seed == 0:
                randcolor = c4d.Vector(*Renderer.generate_random_color(1))
            else:
                random.seed(seed)
                randcolor = Renderer.generate_random_color(1)
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
            atag[c4d.OBJTAG_OBJ_COLOR] = c4d.Vector(*Renderer.generate_random_color(1))
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

    def get_light_mask(self, light_id: int) -> int:
        if light_id == 99: #sun
            return c4d.OBJECTTAG_LIGHTID_S
        elif light_id == 100: # dome
            return c4d.OBJECTTAG_LIGHTID_E
        else:
            # light mask 1-8 
            for i in range(0,9):
                if light_id == i:
                    return int(i + c4d.OBJECTTAG_LIGHTID_1 -1)
            # light mask 9-20   
            for i in range(9,21):
                if light_id == i:
                    return int (i + c4d.OBJECTTAG_LIGHTID_9 - 9)
                
    def disable_all_mask(self, tag: c4d.BaseTag) -> None:
        #if tag.CheckType(ID_OCTANE_LIGHT_TAG) and tag[c4d.OBJECTTAG_USE_LGHT_MASK] == 1327:# On:
        tag[c4d.OBJECTTAG_LIGHTID_S] = False
        tag[c4d.OBJECTTAG_LIGHTID_E] = False
        for i in range(0,9):
            tag[int(i + c4d.OBJECTTAG_LIGHTID_1 -1)] = False
        for i in range(9,21):
            tag[int(i + c4d.OBJECTTAG_LIGHTID_9 -9)] = False

    # NEW
    def set_tag_texture(self, tag: c4d.BaseTag = None, slot: int = None, tex_path: str = None):
        if not isinstance(tag, c4d.BaseTag):
            raise ValueError("Only accept c4d.BaseTag")
        if not isinstance(slot, int):
            raise ValueError("Only accept int for slot")        

        image_ndoe: c4d.BaseList2D = tag[slot]
        if image_ndoe is not None:
            # imageTex
            if isinstance(image_ndoe, c4d.BaseShader):
                if image_ndoe.CheckType(ID_OCTANE_IMAGE_TEXTURE):
                    self.doc.AddUndo(c4d.UNDOTYPE_CHANGE, image_ndoe)
                    image_ndoe[c4d.IMAGETEXTURE_FILE] = str(tex_path)                    
                elif image_ndoe.CheckType(c4d.Xbitmap):
                    self.doc.AddUndo(c4d.UNDOTYPE_CHANGE, image_ndoe)
                    image_ndoe[c4d.BITMAPSHADER_FILENAME] = str(tex_path)
            else: return False
        else:
            new_node = c4d.BaseShader(ID_OCTANE_IMAGE_TEXTURE)
            new_node[c4d.IMAGETEXTURE_FILE] = str(tex_path)
            tag.InsertShader(new_node)
            self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, new_node)
            tag[slot] = new_node            

    # NEW
    def set_tag_color(self, tag: c4d.BaseTag = None, slot: int = None, rgb: c4d.Vector = c4d.Vector(1,1,1)):
        if not isinstance(tag, c4d.BaseTag):
            raise ValueError("Only accept c4d.BaseTag")
        if not isinstance(slot, int):
            raise ValueError("Only accept int for slot")        
        if not isinstance(rgb, c4d.Vector):
            raise ValueError("Only accept c4d.Vector for rgb")
        
        image_ndoe: c4d.BaseList2D = tag[slot]
        if image_ndoe is not None:
            # imageTex
            if isinstance(image_ndoe, c4d.BaseShader):
                if image_ndoe.CheckType(ID_OCTANE_RGBSPECTRUM):
                    self.doc.AddUndo(c4d.UNDOTYPE_CHANGE, image_ndoe)
                    image_ndoe[c4d.RGBSPECTRUMSHADER_COLOR] = rgb
                else: return False
        else:
            new_node = c4d.BaseShader(ID_OCTANE_RGBSPECTRUM)
            new_node[c4d.RGBSPECTRUMSHADER_COLOR] = rgb
            tag.InsertShader(new_node)
            self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, new_node)
            tag[slot] = new_node

    # NEW
    def get_tag(self, node: c4d.BaseObject) -> c4d.BaseTag:
        if not isinstance(node, c4d.BaseObject):
            raise ValueError("Only accept c4d.BaseObject")
        if node.CheckType(c4d.Olight) and node[c4d.LIGHT_TYPE] != 3: # Infinite Sun
            tag = node.GetTag(ID_OCTANE_LIGHT_TAG)
        elif node.CheckType(c4d.Osky):
            tag = node.GetTag(ID_OCTANE_ENVIRONMENT_TAG)
        elif node.CheckType(c4d.Olight) and node[c4d.LIGHT_TYPE] == 3:
            tag = node.GetTag(ID_OCTANE_DAYLIGHT_TAG)
        elif node.CheckType(c4d.Ocamera):
            tag = node.GetTag(ID_OCTANE_CAMERATAG)
        else:
            tag = node.GetTag(ID_OCTANE_OBJECTTAG)
        return tag

    # new
    def get_light_mask(self, light_id: Union[int, str]) -> int:
        """
        get the light mask id of given id

        Args:
            light_id (Union[int, str]): the id number show in the ui

        Returns:
            int: the int number of the true mask id
        """
        if light_id == "s": #sun
            return c4d.OBJECTTAG_LIGHTID_S
        elif light_id == "e": # dome
            return c4d.OBJECTTAG_LIGHTID_E
        else:
            # light mask 1-8 
            for i in range(0,9):
                if light_id == i:            
                    return int(i + c4d.OBJECTTAG_LIGHTID_1 -1)
            # light mask 9-20   
            for i in range(9,21):
                if light_id == i:
                    return int (i + c4d.OBJECTTAG_LIGHTID_9 - 9)

    def _disable_all_mask(self, tag: c4d.BaseTag) -> None:
        """
        Disable all mlight mask

        Args:
            tag (c4d.BaseTag): the octane tag
        """
        tag[c4d.OBJECTTAG_LIGHTID_S] = False
        tag[c4d.OBJECTTAG_LIGHTID_E] = False
        for i in range(0,9):           
            tag[int(i + c4d.OBJECTTAG_LIGHTID_1 -1)] = False
        for i in range(9,21):
            tag[int(i + c4d.OBJECTTAG_LIGHTID_9 -9)] = False

    ### Object ###

    def add_scatter(self, generator_node: c4d.BaseObject, scatter_nodes: list[c4d.BaseObject] = None,
                    vertex: c4d.BaseTag = None, count: int = 1000) -> c4d.BaseList2D:
        """
        Add a scatter object of given generator_node and scatter_nodes.
        """
        # __init pram__
        ModifierID = ID_SCATTER_OBJECT
        ModifierName = 'OC Scatter : '  # Modifier Name
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
        self.doc.SetActiveObject(Modifier, c4d.SELECTION_NEW)
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
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,vdb_obj)
        return vdb_obj

    def iso_to_group(self, nodes : list[c4d.BaseObject]) -> c4d.documents.BaseDocument :
        
        if not nodes:
            return
        
        if len(nodes) == 1:
            nullm = nodes[0].GetMg()
        else:
            nullm = c4d.Matrix()
            nullm.off = sum([ob.GetMg().off for ob in nodes])/ len(nodes)

        doc = nodes[0].GetDocument()

        null = c4d.BaseObject(c4d.Onull)
        doc.InsertObject(null)
        null.SetMg(nullm)
        
        for i in nodes:
            mg = i.GetMg()
            clone: c4d.BaseObject = i.GetClone()
            clone.InsertUnder(null)
            clone.SetMg(mg)
            
        null[c4d.ID_BASEOBJECT_REL_POSITION] = c4d.Vector(0, 0, 0)
        
        iso_doc = c4d.documents.IsolateObjects(doc,[null])   
        null.Remove()
        return iso_doc

    def export_orbx(self, selectedFile:list[c4d.BaseObject], folderPath: str, name: str = "OUT_orbx") -> str:
        """
        Export selected nodes to orbx, and return the path.

        Args:
            selectedFile (list[c4d.BaseObject]): the nodes to export
            folderPath (str): the export folder path.
            name (str, optional): the name of the orbx. Defaults to "OUT_orbx".

        Returns:
            str: the full path of the export orbx.
        """
        if not folderPath or not selectedFile:
            raise RuntimeError("Please select a folder path and objects to export.")
   
        #iso_doc = c4d.documents.IsolateObjects(theDoc,selectedFile)
        iso_doc = self.iso_to_group(selectedFile)
        
        iso_rd = iso_doc.GetActiveRenderData()
        iso_rd[c4d.RDATA_RENDERENGINE] = ID_OCTANE_VIDEO_POST
        oc_vp = c4d.documents.BaseVideoPost(ID_OCTANE_VIDEO_POST)
        iso_rd.InsertVideoPost(oc_vp, None)
      
        new_name = name + ".orbx"
        path = os.path.join(folderPath, new_name)
        # Set
        #oc_vp = ocHelper.VideoPostHelper(iso_doc).vp
        oc_vp[c4d.VP_ORBX_SAVE] = True
        oc_vp[c4d.VP_ORBX_WO_RENDER] = True
        oc_vp[c4d.VP_ORBX_OPEN_IN_SA] = False
        oc_vp[c4d.VP_ORBX_SAVEPATH] = path
        
        c4d.documents.InsertBaseDocument(iso_doc)
        c4d.documents.SetActiveDocument(iso_doc)
        c4d.CallButton(oc_vp, c4d.VP_ORBX_EXPORT_BTN)
        c4d.documents.KillDocument(iso_doc)

        return path

    def add_orbx(self, filePath: str):
        if c4d.plugins.FindPlugin(Renderer.ID_OCTANE, type=c4d.PLUGINTYPE_ANY) is not None: 
            doc = c4d.documents.GetActiveDocument()
            proxy = c4d.BaseObject(ID_ORBX_LOADER)
            doc.InsertObject(proxy,checknames=True)
            name = os.path.splitext(os.path.basename(filePath))[0]
            proxy.SetName(name)
            proxy[c4d.ORBXLOADER_FILENAME] = filePath
            proxy[c4d.ORBXLOADER_BBOX] = True

    # 傻瓜导出
    def auto_proxy(self, nodes : Union[list[c4d.BaseObject], c4d.BaseObject], remove_objects=False):

        if isinstance(nodes, c4d.BaseObject):
            nodes = [nodes]

        document_path = self.doc.GetDocumentPath()
        if not document_path:
            raise RuntimeError('Save project before exporting objects')
        proxy_path = os.path.join(self.doc.GetDocumentPath(),"_Proxy") # Proxy Temp Folder
        
        if not os.path.exists(proxy_path):
            os.makedirs(proxy_path)


        path = os.path.join(self.doc.GetDocumentPath(),"_Proxy")
        file = os.path.join(path, "OUT_orbx.orbx")
        self.export_orbx(nodes, path)

        if remove_objects:
            for node in nodes:
                node.Remove()
        
        self.add_orbx(file)

    # todo
    # coding more...