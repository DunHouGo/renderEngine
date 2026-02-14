###  ==========  Import Libs  ==========  ###
import c4d
import os
import random
from ..constants import *
from ..utils.node_helper import NodeGraghHelper
from .. utils import generate_random_color

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

    def add_hdr_dome(self, color_space: str = '', texture_path: str = None, intensity: float = 1.0, exposure: float = 0.0, seen_by_cam: bool = True) -> c4d.BaseObject :
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

        light = c4d.BaseObject(ID_REDSHIFT_LIGHT)
        light[c4d.REDSHIFT_LIGHT_TYPE] = 4
        self.doc.InsertObject(light)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,light)
        light.SetName("RS HDR Dome")
        light[c4d.REDSHIFT_LIGHT_DOME_MULTIPLIER] = intensity
        light[c4d.REDSHIFT_LIGHT_DOME_EXPOSURE0] = exposure
        if texture_path:
            light[c4d.REDSHIFT_LIGHT_DOME_TEX0,c4d.REDSHIFT_FILE_PATH] = texture_path
        light[c4d.REDSHIFT_LIGHT_DOME_TEX0,c4d.REDSHIFT_FILE_COLORSPACE] = color_space
        light[c4d.REDSHIFT_LIGHT_DOME_BACKGROUND_ENABLE] = seen_by_cam
        
        return light

    def add_rgb_dome(self, rgb: c4d.Vector = c4d.Vector(0,0,0),intensity: float = 1.0, exposure: float = 0.0, seen_by_cam: bool = True) -> list[c4d.BaseTag, c4d.BaseObject]:
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
        light = c4d.BaseObject(ID_REDSHIFT_LIGHT)
        light[c4d.REDSHIFT_LIGHT_TYPE] = 4
        self.doc.InsertObject(light)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,light)
        light.SetName("RS RGB Dome")
        light[c4d.REDSHIFT_LIGHT_DOME_COLOR] = rgb
        light[c4d.REDSHIFT_LIGHT_DOME_MULTIPLIER] = intensity
        light[c4d.REDSHIFT_LIGHT_DOME_EXPOSURE0] = exposure
        light[c4d.REDSHIFT_LIGHT_DOME_BACKGROUND_ENABLE] = seen_by_cam 
        
        return light
    
    def add_dome_rig(self, texture_path: str, rgb: c4d.Vector = c4d.Vector(0,0,0)):
        """
        Add a HDR and visible dome light folder.

        :param texture_path: hdr image path
        :type texture_path: str
        :param unselect: True if the dome can not be select, defaults to True
        :type unselect: bool, optional
        """
        hdr_dome: c4d.BaseObject = self.add_hdr_dome(texture_path=texture_path, seen_by_cam = False)
        black_dome: c4d.BaseObject = self.add_rgb_dome(rgb=rgb)
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
        
    def add_light(self, light_name: str = None, texture_path: str = None, intensity: float = 1.0, exposure: float = 0.0) -> c4d.BaseObject :        
        
        light = c4d.BaseObject(ID_REDSHIFT_LIGHT)
        self.doc.InsertObject(light)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,light)
        # 定义灯光属性
        light[c4d.REDSHIFT_LIGHT_PHYSICAL_AREA_GEOMETRY] = 0
        if light_name:
            light.SetName(light_name)
        else:
            light.SetName('Redshift Light')
        light[c4d.REDSHIFT_LIGHT_PHYSICAL_INTENSITY] = intensity
        light[c4d.REDSHIFT_LIGHT_PHYSICAL_EXPOSURE] = exposure
        
        if texture_path:
            light[c4d.REDSHIFT_LIGHT_PHYSICAL_TEXTURE,c4d.REDSHIFT_FILE_PATH] = texture_path
         
        return light

    def add_light_texture(self, light: c4d.BaseObject = None,  texture_path: str = None, opacity_texture: bool = True) -> c4d.BaseObject :
        """
        Add textures to given light.

        """
        if not light.CheckType(ID_REDSHIFT_LIGHT):
            raise ValueError("This is not a Redshift light")
        
        # Texture
        if texture_path:
            try:
                light[c4d.REDSHIFT_LIGHT_PHYSICAL_TEXTURE,c4d.REDSHIFT_FILE_PATH] = texture_path
            except:
                light[c4d.REDSHIFT_LIGHT_IES_PROFILE,c4d.REDSHIFT_FILE_PATH] = texture_path                
        return light
        
    def add_ies(self, light_name: str = None, intensity: float = 1.0, exposure: float = 0.0, texture_path: str = None) -> c4d.BaseObject :
        light = c4d.BaseObject(ID_REDSHIFT_LIGHT)
        self.doc.InsertObject(light)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,light)
        # 定义灯光属性
        light[c4d.REDSHIFT_LIGHT_TYPE] = 5 # ies
        if light_name:
            light.SetName(light_name)
        else:
            light.SetName('Redshift IES')
        light[c4d.REDSHIFT_LIGHT_IES_MULTIPLIER] = intensity
        light[c4d.REDSHIFT_LIGHT_IES_EXPOSURE] = exposure
        light[c4d.REDSHIFT_LIGHT_PREVIEW] = False
        
        if texture_path:
            light[c4d.REDSHIFT_LIGHT_IES_PROFILE,c4d.REDSHIFT_FILE_PATH] = texture_path
         
        return light
    
    def add_gobo(self,light_name: str = None, intensity: float = 250000.0, exposure: float = -3.0, texture_path: str = None) -> c4d.BaseObject :
        light = c4d.BaseObject(ID_REDSHIFT_LIGHT)
        self.doc.InsertObject(light)
        
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,light)
        # 定义灯光属性
        light[c4d.REDSHIFT_LIGHT_PHYSICAL_AREA_GEOMETRY] = 2 # spot
        if light_name:
            light.SetName(light_name)
        else:
            light.SetName('Redshift Gobo')
        light[c4d.REDSHIFT_LIGHT_IES_MULTIPLIER] = int(intensity)
        light[c4d.REDSHIFT_LIGHT_IES_EXPOSURE] = int(exposure)
        light[c4d.REDSHIFT_LIGHT_PREVIEW] = False
        
        if texture_path:
            light[c4d.REDSHIFT_LIGHT_PHYSICAL_TEXTURE,c4d.REDSHIFT_FILE_PATH] = texture_path
         
        return light
    
    def add_sun_rig(self, sky_intensity: int = 1, sun_intensity: int =1):
        sky = c4d.BaseObject(ID_REDSHIFT_RSSKY)
        sky.SetName( "Redshift Sky")
        sun = c4d.BaseObject(ID_REDSHIFT_LIGHT)
        sky.SetName( "Redshift Sun")
        sun[c4d.REDSHIFT_LIGHT_PHYSICAL_AREA_GEOMETRY] = 7 # sun
        self.doc.InsertObject(sky)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,sky)
        self.doc.InsertObject(sun)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,sun)
        sky[c4d.REDSHIFT_SKY_PHYSICALSKY_SUN] = sun
        
        sky[c4d.REDSHIFT_SKY_PHYSICALSKY_MULTIPLIER] = int(sky_intensity)
        sky[c4d.REDSHIFT_SKY_PHYSICALSKY_SUN_DISK_INTENSITY] = int(sun_intensity)
         
        return sky

    def add_light_modifier(self, light: c4d.BaseObject, target: c4d.BaseObject = None, gsg_link: bool = False, rand_color: bool = False, seed: int = 0):
        
        # 新建目标标签
        if target is not None:        
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
                randcolor = NodeGraghHelper.generate_random_color(1)
            light[c4d.ID_BASELIST_ICON_COLOR] = randcolor

    ### Tag ###
    
    def add_object_id(self, node : c4d.BaseObject, maskID: int = 2) -> c4d.BaseTag:
        mask_tag = c4d.BaseTag(ID_REDSHIFT_TAG)
        node.InsertTag(mask_tag)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,mask_tag)
        if maskID:
            mask_tag[c4d.REDSHIFT_OBJECT_OBJECTID_OVERRIDE] = True
            mask_tag[c4d.REDSHIFT_OBJECT_OBJECTID_ID] = int(maskID)
        return mask_tag    
        
    def add_object_tag(self, node : c4d.BaseObject) -> c4d.BaseTag:
        object_tag = c4d.BaseTag(ID_REDSHIFT_TAG)
        node.InsertTag(object_tag)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,object_tag)        
        return object_tag
    
    ### Object ### 
                  
    def add_scatter(self, generator_node: c4d.BaseObject, scatter_nodes: list[c4d.BaseObject], selectedtag: c4d.SelectionTag = None, count: int = None) -> c4d.BaseObject :
        """ 
        Add a scatter object of given generator_node and scatter_nodes[vertex optional].
        """
        # __init pram__
        ModifierID = 1018545 # c4d.Omgmatrix # R2023
        ModifierName = 'RS Scatter : '
        objName = generator_node.GetName()
        if count is None:
            count = random.randint(0,1234567)
        # Modifier config
        Modifier = c4d.BaseObject(ModifierID) #  ID
        #  Config settings
        Modifier[c4d.ID_MG_MOTIONGENERATOR_MODE] = 0
        Modifier[c4d.MG_OBJECT_LINK] = generator_node
        Modifier[c4d.MG_POLYSURFACE_SEED] = count
        Modifier[c4d.MG_POLY_MODE_] = 3 # surface
        Modifier.SetName(ModifierName + objName)
        if selectedtag :
            Modifier[c4d.MG_POLY_SELECTION] = selectedtag.GetName()
            
        rs_tag = c4d.BaseTag(ID_REDSHIFT_TAG)
        Modifier.InsertTag(rs_tag)
        
        if scatter_nodes:
            data = c4d.InExcludeData()
            for node in scatter_nodes :
                data.InsertObject(node,1)                
            rs_tag[c4d.REDSHIFT_OBJECT_PARTICLE_MODE] = 4 # object mode
            rs_tag[c4d.REDSHIFT_OBJECT_PARTICLE_CUSTOM_OBJECTS] = data

        self.doc.InsertObject(Modifier)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,Modifier) # Undo
    
        return Modifier

    def add_env(self, emisson: c4d.Vector = c4d.Vector(0,0,0), seen_by_camera: bool = True) -> c4d.BaseObject :
        env = c4d.BaseObject(ID_REDSHIFT_ENVIROMENT)
        self.doc.InsertObject(env)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,env)
        env[c4d.REDSHIFT_ENVIRONMENT_VOLUMESCATTERING_FOG_AMBIENT] = emisson
        if not seen_by_camera:
            env[c4d.REDSHIFT_ENVIRONMENT_VOLUMESCATTERING_FOG_AMBIENT] = 0
        return env
        
    def add_vdb(self, name: str = None, vdb_path: str = None) -> c4d.BaseObject :
        vdb = c4d.BaseObject(ID_REDSHIFT_VOLUME) # Create the object.
        if name:
            vdb.SetName(name)
        else:            
            vdb.SetName('Redshift Volume')
        
        if vdb_path:
            vdb[c4d.REDSHIFT_VOLUME_FILE,c4d.REDSHIFT_FILE_PATH] = vdb_path
            
            try:
                vdb[c4d.REDSHIFT_VOLUME_VELOCITY_GRID_X] = 'velocity'
                vdb[c4d.REDSHIFT_VOLUME_VELOCITY_GRID_Y] = 'velocity'
                vdb[c4d.REDSHIFT_VOLUME_VELOCITY_GRID_Z] = 'velocity'
                vdb[c4d.REDSHIFT_VOLUME_CHANNELS] = 'density\ntemperature\nvelocity\n'
            except:
                pass
        vdb_obj = self.doc.InsertObject(vdb)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,vdb)
        return vdb_obj

    def add_proxy(self, name: str = None, proxy_path: str = None, mesh: bool = True, mode: int = None) -> c4d.BaseObject :
        proxy = c4d.BaseObject(ID_REDSHIFT_PROXY)
        self.doc.InsertObject(proxy)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,proxy)
        if name:
            proxy.SetName(name)
        else:
            proxy.SetName('Redshift Proxy')
        
        if proxy_path:
            if os.path.isfile(str(proxy_path)):
                proxy[c4d.REDSHIFT_PROXY_FILE,c4d.REDSHIFT_FILE_PATH] = proxy_path
                
        if mesh:
            proxy[c4d.REDSHIFT_PROXY_DISPLAY_MODE] = REDSHIFT_PROXY_DISPLAY_MODE_MESH
            
        if mode:
            proxy[c4d.REDSHIFT_PROXY_MATERIAL_MODE] = mode
        return proxy

    def auto_proxy(self, node : c4d.BaseObject , filepath: str = None, remove_objects: bool = False):
        if c4d.plugins.FindPlugin(ID_REDSHIFT, type=c4d.PLUGINTYPE_ANY) is not None:
            try:
                import redshift
            except ImportError:
                raise ImportError("Redshift module not found. Please make sure Redshift is installed and enabled.")
        if not isinstance(node,c4d.BaseObject):
            raise ValueError("must be a BaseObject.")
        
        # Find the Redshift Proxy Export plugin
        plug = c4d.plugins.FindPlugin(redshift.Frsproxyexport, c4d.PLUGINTYPE_SCENESAVER)
        if plug is None:
            raise RuntimeError("Pluging not found")

        # Send MSG_RETRIEVEPRIVATEDATA to the plugin to retrieve the state
        op = {}
        if not plug.Message(c4d.MSG_RETRIEVEPRIVATEDATA, op):
            return False

        # BaseList2D object stored in "imexporter" key holds the settings
        if "imexporter" not in op:
            return False
        imexporter = op["imexporter"]
        
        # Single frame export
        imexporter[c4d.REDSHIFT_PROXYEXPORT_ANIMATION_RANGE] = c4d.REDSHIFT_PROXYEXPORT_ANIMATION_RANGE_CURRENT_FRAME

        # Keep the default beauty config in the proxy. Used primarily when exporting entire scenes for rendering with the redshiftCmdLine tool
        imexporter[c4d.REDSHIFT_PROXYEXPORT_AOV_DEFAULT_BEAUTY]	= False

        # Don't need lights in our proxies
        imexporter[c4d.REDSHIFT_PROXYEXPORT_EXPORT_LIGHTS] = False

        # Automatic object replacement with proxies
        # Proxy contents will be offset around the selection cetner
        imexporter[c4d.REDSHIFT_PROXYEXPORT_OBJECTS] = c4d.REDSHIFT_PROXYEXPORT_OBJECTS_SELECTION
        imexporter[c4d.REDSHIFT_PROXYEXPORT_ORIGIN] = c4d.REDSHIFT_PROXYEXPORT_ORIGIN_WORLD #REDSHIFT_PROXYEXPORT_ORIGIN_OBJECTS for Boundingbox

        imexporter[c4d.REDSHIFT_PROXYEXPORT_AUTOPROXY_CREATE] = True
        imexporter[c4d.REDSHIFT_PROXYEXPORT_REMOVE_OBJECTS] = False
                
        # 对象实例
        ex_node: c4d.BaseObject = node.GetClone()
        mg = c4d.Matrix()
        ex_node.SetMg(mg)
        self.doc.InsertObject(ex_node) # 0,0,0
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, ex_node) 
        
        
        # 执行导出
        for obj in self.doc.GetActiveObjects(1) :
            self.doc.AddUndo(c4d.UNDOTYPE_BITS, obj)
            obj.DelBit(c4d.BIT_ACTIVE)
        
        if filepath is None:
            proxy_path = os.path.join(self.doc.GetDocumentPath(),"_Proxy") # Proxy Temp Folder
            if not os.path.exists(proxy_path):
                os.makedirs(proxy_path)
            filepath = os.path.join(self.doc.GetDocumentPath(), "_Proxy", node.GetName())
        self.doc.SetSelection(ex_node)

        c4d.documents.SaveDocument(self.doc, filepath, c4d.SAVEDOCUMENTFLAGS_DONTADDTORECENTLIST, redshift.Frsproxyexport) 
        self.doc.AddUndo(c4d.UNDOTYPE_DELETEOBJ, ex_node)   
        ex_node.Remove()
        
        # 程序对象
        proxy = self.doc.GetFirstObject()
        if not (isinstance(proxy, c4d.BaseObject) and
                proxy.CheckType(1038649)):
            raise TypeError("Can not find the proxy.")
        self.doc.AddUndo(c4d.UNDOTYPE_CHANGE, proxy)    
        # 重置坐标
        proxy.SetMg(node.GetMg())
        proxy_clone: c4d.BaseObject  = proxy.GetClone()
        self.doc.AddUndo(c4d.UNDOTYPE_DELETEOBJ, node)
        proxy.Remove()
        self.doc.InsertObject(proxy_clone, pred=node, checknames=True)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, proxy)   
        proxy_clone.SetName(node.GetName() + "_Proxy")
        proxy_clone.SetMg(node.GetMg())
        
        if remove_objects == True:
            self.doc.AddUndo(c4d.UNDOTYPE_DELETEOBJ, node)
            node.Remove()   

        return proxy

    def get_bakeable_nodes(self, select_nodes:list[c4d.BaseObject]) -> list :
        nodes = []
        for node in select_nodes :  
                            
            self.doc.AddUndo(c4d.UNDOTYPE_BITS,node)
            node.DelBit(c4d.BIT_ACTIVE)
            
            if isinstance(node, c4d.PointObject):
                if node.GetTag(c4d.Tuvw) is not None :
                    nodes.append(node)
        return nodes

    def add_bakeset(self, nodes : list[c4d.BaseObject], resolution: int = 2048) -> c4d.BaseObject :
        if isinstance(nodes, c4d.BaseObject):
            nodes = [nodes]
        if isinstance(nodes, list):
            nodes = nodes

        data = c4d.InExcludeData()
        nodes = self.get_bakeable_nodes(nodes)
        for node in nodes :
            data.InsertObject(node,1)
            self.doc.AddUndo(c4d.UNDOTYPE_BITS,node)
            node.DelBit(c4d.BIT_ACTIVE)
        bakeset = c4d.BaseObject(ID_REDSHIFT_BAKESET)
        bakeset[c4d.REDSHIFT_BAKESET_WIDTH] = resolution
        bakeset[c4d.REDSHIFT_BAKESET_HEIGHT] = resolution
        bakeset[c4d.REDSHIFT_BAKESET_OBJECTS] = data
        self.doc.InsertObject(bakeset)
        self.doc.AddUndo(c4d.UNDOTYPE_BITS,bakeset)
        bakeset.SetBit(c4d.BIT_ACTIVE)
        self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,bakeset)

__all__ = [
    "RedshiftHelper"
]
