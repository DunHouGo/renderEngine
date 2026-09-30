# coding=utf-8

import c4d
import re
from typing import Iterator

from ..constants import *
from ..utils import iterate, GetVideoPost

ID_OCTANE_AOV_NODE = 1056125
AOV_NODE_TYPE = 1900
AOV_NODE_NAME = 1901
AOV_INPUT_COUNT = 1800
AOV_COMP_INPUT = 1904
AOV_DENOISER_ALBEDO_INPUT = 1894
AOV_DENOISER_NORMAL_INPUT = 1895
AOV_EFFECTS_LINK = 2159
AOV_RENDER_PASS_ID = 1808
AOV_RENDER_PASS_NAME = 1809
AOV_ENABLE_IMAGER = 1902
AOV_ENABLE_POSTPROC = 1903
AOV_COMPOSITOR = 3390
AOV_OUTPUT_LINK = 3600
# Output AOV links occupy the 100 slots immediately before the count field.
AOV_OUTPUT_SLOT_LIMIT = SET_RENDERAOV_IN_CNT - AOV_OUTPUT_LINK
AOV_TYPE_OUTPUT = 393
AOV_TYPE_RENDER = 391
AOV_TYPE_DENOISE = 441
AOV_TYPE_SDR = 406
AOV_TYPE_EFFECTS = 385
AOV_TYPE_LAYER_GROUP = 388

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
            return result
        
        for obj in iterate(start_shader):

            result.append(obj)

        # Return the object List.
        return result

    def ensure_aov_types(self, aov_types: tuple[int, ...]) -> list[c4d.BaseShader]:
        """Create missing AOV types and return the newly created shaders.

        :param aov_types: AOV type IDs that should exist in the current pass list.
        :return: Newly created AOV shaders, in the requested order.
        :rtype: list[c4d.BaseShader]
        """
        existing_types = {aov[RNDAOV_TYPE] for aov in self.get_all_aovs()}
        created: list[c4d.BaseShader] = []
        for aov_type in aov_types:
            if aov_type in existing_types:
                continue
            aov = self.create_aov_shader(aov_type)
            self.add_aov(aov)
            created.append(aov)
            existing_types.add(aov_type)
        self.remove_empty_aov()
        return created

    def replace_light_aovs(
        self,
        light_ids: list[int],
        light_names: dict[int, str] | None = None,
    ) -> list[c4d.BaseShader]:
        """Replace light AOVs with the supplied zero-based Light IDs.

        :param light_ids: Octane Light IDs using the same convention as
            :meth:`add_light_aov`; Sun and Environment use ``-1`` and ``0``.
        :param light_names: Optional display names keyed by Light ID.
        :return: Newly created light AOV shaders.
        :rtype: list[c4d.BaseShader]
        """
        self.remove_aov_type(RNDAOV_LIGHT)
        created: list[c4d.BaseShader] = []
        names = light_names or {}
        for light_id in dict.fromkeys(light_ids):
            aov = self.add_light_aov(light_id, names.get(light_id, f"Light {light_id}"))
            if aov is not None:
                created.append(aov)
        self.remove_empty_aov()
        return created

    def ensure_light_aovs(
        self,
        light_ids: list[int],
        light_names: dict[int, str] | None = None,
    ) -> list[c4d.BaseShader]:
        """Add missing light AOVs without changing existing AOV settings.

        :param light_ids: Octane Light IDs using the helper's convention; Sun and
            Environment use ``-1`` and ``0``.
        :param light_names: Optional display names keyed by Light ID.
        :return: Newly created light AOV shaders.
        :rtype: list[c4d.BaseShader]
        """
        names = light_names or {}
        existing_ids = {
            int(aov[RNDAOV_LIGHT_ID]) - 1
            for aov in self.get_aov(RNDAOV_LIGHT)
        }
        created: list[c4d.BaseShader] = []
        for light_id in dict.fromkeys(light_ids):
            if light_id in existing_ids:
                continue
            aov = self.add_light_aov(light_id, names.get(light_id, f"Light {light_id}"))
            if aov is not None:
                created.append(aov)
                existing_ids.add(light_id)
        self.remove_empty_aov()
        return created

    def set_all_enabled(self, enabled: bool) -> int:
        """Set the enabled state for every AOV and return the number changed.

        :param enabled: Desired enabled state.
        :return: Number of AOV shaders whose state changed.
        :rtype: int
        """
        changed = 0
        for aov in self.get_all_aovs():
            if bool(aov[RNDAOV_ENABLED]) == enabled:
                continue
            aov[RNDAOV_ENABLED] = enabled
            changed += 1
        return changed

    def create_light_denoise_aovs(
        self,
        light_ids: list[tuple[int, str]],
        with_sdr: bool = True,
    ) -> int:
        """Create Octane Output AOV groups with shared Open Image Denoise.

        :param light_ids: Light Pass IDs and display names. IDs ``99`` and
            ``100`` represent Sunlight and Environment; regular IDs are 1-20.
        :param with_sdr: Add the Convert for SDR display (ACES) layer when true.
        :return: Number of Output AOV groups created.
        :rtype: int
        """
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")
        if not light_ids:
            return 0

        pass_values: dict[int, tuple[str, str]] = {}
        for light_id, name in light_ids:
            if light_id == 99:
                pass_values.setdefault(22, ("Sun light", name or "Sun light"))
            elif light_id == 100:
                pass_values.setdefault(21, ("Ambient light", name or "Ambient light"))
            elif 1 <= light_id <= 20:
                render_pass = 22 + light_id if light_id <= 8 else 76 + light_id
                pass_values.setdefault(render_pass, (f"Light pass {light_id}", name or f"Light {light_id}"))
        if not pass_values:
            return 0

        target_types = {
            AOV_TYPE_OUTPUT,
            AOV_TYPE_RENDER,
            AOV_TYPE_DENOISE,
            AOV_TYPE_SDR,
            AOV_TYPE_EFFECTS,
            AOV_TYPE_LAYER_GROUP,
        }

        def node_type(node: c4d.BaseList2D) -> int | None:
            try:
                return int(node[AOV_NODE_TYPE])
            except (AttributeError, TypeError, ValueError):
                return None

        def children(node: c4d.BaseList2D) -> Iterator[c4d.BaseList2D]:
            child = node.GetDown()
            while isinstance(child, c4d.BaseList2D):
                yield child
                child = child.GetNext()
            try:
                inputs = node.GetInputs()
                input_children = (
                    inputs.GetChildren()
                    if hasattr(inputs, "GetChildren")
                    else inputs
                )
                for child in input_children:
                    if isinstance(child, c4d.BaseList2D):
                        yield child
            except (AttributeError, TypeError):
                return

        def collect(node: c4d.BaseList2D, seen: set[int], result: list[c4d.BaseList2D]) -> None:
            if not isinstance(node, c4d.BaseList2D) or id(node) in seen:
                return
            seen.add(id(node))
            if node_type(node) in target_types:
                result.append(node)
            for child in children(node):
                collect(child, seen, result)

        targets: list[c4d.BaseList2D] = []
        for index in range(AOV_OUTPUT_SLOT_LIMIT):
            slot = self.vp[AOV_OUTPUT_LINK + index]
            if isinstance(slot, c4d.BaseList2D):
                collect(slot, set(), targets)
        shader = self.vp.GetFirstShader()
        while isinstance(shader, c4d.BaseList2D):
            collect(shader, set(), targets)
            shader = shader.GetNext()
        roots: list[c4d.BaseList2D] = []
        for node in targets:
            if not node.IsAlive():
                continue
            top = node
            parent = top.GetUp()
            while isinstance(parent, c4d.BaseList2D) and node_type(parent) in target_types:
                top = parent
                parent = top.GetUp()
            if top.IsAlive() and all(existing is not top for existing in roots):
                roots.append(top)
        for top in roots:
            if top.IsAlive():
                self.doc.AddUndo(c4d.UNDOTYPE_DELETEOBJ, top)
        for index in range(AOV_OUTPUT_SLOT_LIMIT):
            # 输出槽位是动态链接参数，必须使用 None 清空，不能写入 BaseContainer。
            self.vp[AOV_OUTPUT_LINK + index] = None
        self.vp[AOV_COMPOSITOR] = c4d.BaseContainer()
        self.vp[AOV_INPUT_COUNT] = 0
        for top in roots:
            if top.IsAlive():
                top.Remove()

        def new_node(node_type_value: int, name: str = "") -> c4d.BaseList2D:
            node = c4d.BaseList2D(ID_OCTANE_AOV_NODE)
            node[AOV_NODE_TYPE] = node_type_value
            if name:
                node[AOV_NODE_NAME] = name
            self.vp.InsertShader(node)
            self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, node)
            return node

        denoise_albedo = new_node(AOV_TYPE_RENDER, "Denoise albedo")
        denoise_albedo[AOV_RENDER_PASS_ID] = 123
        denoise_albedo[AOV_RENDER_PASS_NAME] = "Denoise albedo"
        denoise_normal = new_node(AOV_TYPE_RENDER, "Denoise normal")
        denoise_normal[AOV_RENDER_PASS_ID] = 40
        denoise_normal[AOV_RENDER_PASS_NAME] = "Denoise normal"
        denoise = new_node(AOV_TYPE_DENOISE)
        denoise[AOV_INPUT_COUNT] = 2
        denoise_albedo.InsertUnder(denoise)
        denoise_normal.InsertUnder(denoise)
        denoise[AOV_DENOISER_ALBEDO_INPUT] = denoise_albedo
        denoise[AOV_DENOISER_NORMAL_INPUT] = denoise_normal
        sdr = new_node(AOV_TYPE_SDR) if with_sdr else None
        effects_layer = new_node(AOV_TYPE_EFFECTS, "Effectslayers")

        denoise_albedo[AOV_EFFECTS_LINK] = effects_layer
        denoise_normal[AOV_EFFECTS_LINK] = effects_layer

        groups = []
        for render_pass, (render_name, display_name) in sorted(pass_values.items()):
            output = new_node(AOV_TYPE_OUTPUT, display_name)
            output[AOV_ENABLE_IMAGER] = True
            output[AOV_ENABLE_POSTPROC] = True
            output[AOV_RENDER_PASS_ID] = render_pass
            render = c4d.BaseList2D(ID_OCTANE_AOV_NODE)
            render[AOV_NODE_TYPE] = AOV_TYPE_RENDER
            render[AOV_RENDER_PASS_ID] = render_pass
            render[AOV_RENDER_PASS_NAME] = render_name
            output.InsertShader(render)
            self.doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, render)
            render[AOV_EFFECTS_LINK] = effects_layer
            output[AOV_COMP_INPUT] = render
            output[AOV_COMP_INPUT + 1] = denoise
            linked_count = 2
            if sdr is not None:
                output[AOV_COMP_INPUT + 2] = sdr
                linked_count = 3
            output[AOV_INPUT_COUNT] = linked_count
            groups.append(output)

        compositor = c4d.BaseContainer()
        for index, output in enumerate(groups):
            entry = c4d.BaseContainer()
            entry.SetInt32(0, AOV_TYPE_OUTPUT)
            entry.SetLink(100, output)
            compositor.SetContainer(index, entry)
            self.vp[AOV_OUTPUT_LINK + index] = output
        self.vp[AOV_COMPOSITOR] = compositor
        self.vp[AOV_INPUT_COUNT] = len(groups)
        self.vp.Message(c4d.MSG_CHANGE)
        self.vp.Message(c4d.MSG_UPDATE)
        return len(groups)

    def get_light_denoise_aov_mode(self) -> bool | None:
        """Return the current light denoise Output AOV mode, if one exists.

        :return: ``True`` for sRGB with SDR conversion, ``False`` for ACES,
            or ``None`` when no light Output AOV is connected to Open Image Denoise.
        :rtype: bool | None
        """
        if self.vp is None:
            raise RuntimeError(f"Can't get the {self.vpname} VideoPost")

        for index in range(AOV_OUTPUT_SLOT_LIMIT):
            output = self.vp[AOV_OUTPUT_LINK + index]
            if not isinstance(output, c4d.BaseList2D):
                continue
            if output[AOV_NODE_TYPE] != AOV_TYPE_OUTPUT:
                continue
            denoise = output[AOV_COMP_INPUT + 1]
            if not isinstance(denoise, c4d.BaseList2D):
                continue
            if denoise[AOV_NODE_TYPE] != AOV_TYPE_DENOISE:
                continue
            sdr = output[AOV_COMP_INPUT + 2]
            return (
                isinstance(sdr, c4d.BaseList2D)
                and sdr[AOV_NODE_TYPE] == AOV_TYPE_SDR
            )
        return None

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
        
        if not aov_name:
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
