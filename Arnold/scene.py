# coding=utf-8

import os
import random
from typing import Union

import c4d

from ..constants import *
from ..utils import EasyTransaction, generate_random_color
# Avoid circular import with package-level functions in __init__
# Delay-import `GetShaderLink`, `SetShaderLink`, `ArnoldShaderLinkCustomData`
# inside methods where they are used.
from .material import MaterialHelper

class SceneHelper:
    """
    Class for Secne Objects, Tags, Lights, Proxy and so on.
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
        from . import SetShaderLink, ArnoldShaderLinkCustomData
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

        from . import GetShaderLink, SetShaderLink, ArnoldShaderLinkCustomData
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
        from . import SetShaderLink
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
        with EasyTransaction(gobo_material) as tr:
            gobo_tex = tr.AddTexture(shadername='Gobo Texture',filepath=texture_path)
            tex_outport = tr.GetPort(gobo_tex)
            endNode = tr.GetOutput()
            endNodePort = tr.GetPort(endNode, "shader")
            gobo_shader = tr.AddGobo(tex_outport,endNodePort)

        tr.InsertMaterial()
        tr.SetActive()        

        gobo = self.add_light(light_name='Arnold Gobo', intensity = intensity,exposure=exposure,light_type=C4DAIN_SPOT_LIGHT)
        
        # InExcludeData
        filter_data = c4d.InExcludeData()
        filter_data.InsertObject(tr.material,1)
        gobo[C4DAI_LIGHT_COMMON_FILTERS] = filter_data
        
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
                randcolor = c4d.Vector(*generate_random_color(1))
            else:
                random.seed(seed)
                randcolor = generate_random_color(1)
            light[c4d.ID_BASELIST_ICON_COLOR] = randcolor

    def add_light_texture(self, light: c4d.BaseObject = None,  texture_path: str = None) -> c4d.BaseObject :
        """
        Add textures to given light.

        """
        from . import ArnoldShaderLinkCustomData, SetShaderLink
        if light.CheckType(ARNOLD_LIGHT):        
            # Texture
            if texture_path:
                shaderlink = ArnoldShaderLinkCustomData()
                shaderlink.type = ArnoldShaderLinkCustomData.TYPE_TEXTURE
                shaderlink.texture = texture_path
                shaderlink.texture_color_space = "linear sRGB"
                # print(type(shaderlink))
                SetShaderLink(light, C4DAIP_QUAD_LIGHT_COLOR , shaderlink)

                
        return light
      
   
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

    # 傻瓜导出
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

__all__ = [
    "SceneHelper"
]
