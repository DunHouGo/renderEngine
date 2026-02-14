# coding=utf-8

import c4d
import random
from typing import Union
import os

from ..constants import *
from ..utils import iterate, generate_random_color

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
        image[1118] = 2
        image[c4d.IMAGETEXTURE_GAMMA] = 1.0
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

        def _GetTexture(host: c4d.BaseList2D) -> c4d.BaseList2D:
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

    def add_light_modifier(self, light: c4d.BaseObject, target: c4d.BaseObject= None, gsg_link: bool = False, rand_color: bool = False, seed: int = 0):
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

__all__ = [
    "SceneHelper"
]
