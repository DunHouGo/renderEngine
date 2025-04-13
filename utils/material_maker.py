import c4d
import maxon
import os
import sys
import re
from typing import Union, Optional,TypeAlias, Any, Sequence
from dataclasses import dataclass, field
from functools import lru_cache
import Renderer
# from Renderer.constants.arnold_id import *
from Renderer.constants.common_id import ID_REDSHIFT, ID_ARNOLD, ID_OCTANE, ID_VRAY, ID_CORONA, ID_CENTILEO
from Renderer.utils.node_helper import NodeGraghHelper, EasyTransaction
if c4d.plugins.FindPlugin(ID_REDSHIFT, type=c4d.PLUGINTYPE_ANY) is not None:
    from Renderer import Redshift
if c4d.plugins.FindPlugin(ID_ARNOLD, type=c4d.PLUGINTYPE_ANY) is not None:
    from Renderer import Arnold
if c4d.plugins.FindPlugin(ID_OCTANE, type=c4d.PLUGINTYPE_ANY) is not None:
    from Renderer import Octane
if c4d.plugins.FindPlugin(ID_VRAY, type=c4d.PLUGINTYPE_ANY) is not None:
    from Renderer import Vray
if c4d.plugins.FindPlugin(ID_CORONA, type=c4d.PLUGINTYPE_ANY) is not None:
    from Renderer import Corona
if c4d.plugins.FindPlugin(ID_CENTILEO, type=c4d.PLUGINTYPE_ANY) is not None:
    from Renderer import CentiLeo

regex_dif: str = '[^a-zA-Z0-9^\s](diff|dif|diffuse|albedo|color|col|base.?color)'
regex_spec: str = '[^a-zA-Z0-9^\s](spec|specular|edgetint)'
regex_metal: str = '[^a-zA-Z0-9^\s](metal|metallic|metalness)'
regex_rough: str = '[^a-zA-Z0-9^\s](rough|roughness)'
regex_gloss: str = '[^a-zA-Z0-9^\s](gloss|glossiness)'
regex_ao: str = '[^a-zA-Z0-9^\s](ao|ambient.?occlusion|occlusion|occ|mixed.?ao)'
regex_alpha: str = '[^a-zA-Z0-9^\s](alpha|opacity)'
regex_bump: str = '[^a-zA-Z0-9^\s](bump)'
regex_normal: str = '[^a-zA-Z0-9^\s](normal|nrm|normaldx|normalgl|nor|nor.?dx|nor.?gl|opengl|directx)'
regex_emission: str = '[^a-zA-Z0-9^\s](emission|emissive|emis)'
regex_disp: str = '[^a-zA-Z0-9^\s](displacement|height|disp|depth|dis|displace)'
regex_trans: str = '[^a-zA-Z0-9^\s](trans|transmission|translucency|sss)'
regex_sheen: str = '[^a-zA-Z0-9^\s](sheen)'
regex_anisotropy: str = '[^a-zA-Z0-9^\s](anisotropy|anis)'

regex_PBR: str = '[^a-zA-Z0-9^\s](diff|dif|diffuse|albedo|color|col|base.?color|spec|specular|metal|metallic|metalness|rough|roughness|gloss|glossiness|ao|ambient.?occlusion|occlusion|occ|mixed.?ao|alpha|opacity|bump|normal|nrm|normaldx|normalgl|nor|nor.?dx|nor.?gl|opengl|directx|emisson|emissive|emis|displacement|height|disp|depth|dis|displace|trans|transmission|translucy)'

regex_extensions: str = '.(jpg|jpeg|png|exr|tif|tiff|tga|psd|tx|hdr|exr|bmp|b3d|dds|dpx|iff|psb|rla|rpf|pict)'

IMAGE_EXTENSIONS: tuple[str] = ('.png', '.jpg', '.jpeg', '.tga', '.bmp', ".exr", ".hdr", ".tif", ".tiff","iff", ".psd", ".tx",  ".b3d", ".dds", ".dpx", ".psb", ".rla", ".rpf", ".pict")

#=============================================
# PBR Package
#=============================================
# Check if the file is an image
def IsImageFile(file: str) -> bool:
    """Check if the file is an image"""
    if not file:
        return False
    if not os.path.exists(file):
        return False
    if not os.path.isfile(file):
        return False
    return file.lower().endswith(IMAGE_EXTENSIONS)

# Get the real name of the pbr texture
def GetPBRName(text: str) -> Optional[str]:
    regex_object: re.Match = re.search(regex_PBR, text, re.IGNORECASE)
    if regex_object is None:
        return None
    return text[:regex_object.start()]

# Check if the texture is in the package
def InPackage(text: str, name: str) -> bool:
    return text.startswith(name)

# Get the pbr images from the folder with a name
def GetPBRImages(folder: str, name: str) -> list[str]:
    if not os.path.exists(folder):
        raise FileNotFoundError(f'Folder {folder} does not exist')
    if not os.path.isdir(folder):
        raise NotADirectoryError(f'{folder} is not a folder')
    data: list = []
    for file in os.listdir(folder):
        if InPackage(file, name):            
            data.append(os.path.join(folder, file))
    return data

# Get all pbr names in the folder
def GetPackageNames(folder: str) -> list[str]:
    if not os.path.exists(folder):
        raise FileNotFoundError(f'Folder {folder} does not exist')
    if not os.path.isdir(folder):
        raise NotADirectoryError(f'{folder} is not a folder')
    data: list = []
    for file in os.listdir(folder):
        if (name := GetPBRName(file)) is not None:
            if name not in data:
                data.append(name)
    return data


@dataclass
class PBRPackage:
    """A representation of a PBR texture package, containing slot info and its texture"""

    folder: str = field(default=None, repr=False)
    name: str = field(default=None)

    def __post_init__(self) -> None:
        if not os.path.exists(self.folder):
            raise FileNotFoundError(f'Folder {self.folder} does not exist')
        if not os.path.isdir(self.folder):
            raise NotADirectoryError(f'{self.folder} is not a folder')
        self.diffuse: Optional[str] = None
        self.specular: Optional[str] = None
        self.metalness: Optional[str] = None
        self.roughness: Optional[str] = None
        self.glossiness: Optional[str] = None
        self.ao: Optional[str] = None
        self.alpha: Optional[str] = None
        self.bump: Optional[str] = None
        self.normal: Optional[str] = None
        self.emission: Optional[str] = None
        self.displacement: Optional[str] = None
        self.transmission: Optional[str] = None
        self.sheen: Optional[str] = None
        self.anisotropy: Optional[str] = None

    def __eq__(self, other):
        if isinstance(other, PBRPackage):
            # 定义何时两个PBRPackage实例应被视为相等
            return self.diffuse == other.diffuse
        return False

    def __hash__(self):
        # 返回一个基于对象属性计算的整数，用于哈希值
        return hash(self.diffuse)

    @lru_cache(maxsize=128, typed=False)
    def build(self, folder: str = None, name: str = None) -> None:
        """Builds the PBR package data"""
        if folder is None:
            folder = self.folder
        if name is None:
            name = self.name
        data =  GetPBRImages(folder, name)
        for i in data:
            if self.get_texture(i, regex_dif) is not None:
                self.diffuse: str = i
            elif self.get_texture(i, regex_spec) is not None:
                self.specular: str = i
            elif self.get_texture(i, regex_metal) is not None:
                self.metalness: str = i
            elif self.get_texture(i, regex_rough) is not None:
                self.roughness: str = i
            elif self.get_texture(i, regex_gloss) is not None:
                self.glossiness: str = i
            elif self.get_texture(i, regex_ao) is not None:
                self.ao: str = i
            elif self.get_texture(i, regex_alpha) is not None:
                self.alpha: str = i
            elif self.get_texture(i, regex_bump) is not None:
                self.bump: str = i
            elif self.get_texture(i, regex_normal) is not None:
                self.normal: str = i
            elif self.get_texture(i,regex_emission) is not None:
                self.emission: str = i
            elif self.get_texture(i, regex_disp) is not None:
                self.displacement: str = i
            elif self.get_texture(i, regex_trans) is not None:
                self.transmission: str = i
            elif self.get_texture(i, regex_sheen) is not None:
                self.sheen: str = i
            elif self.get_texture(i, regex_anisotropy) is not None:
                self.anisotropy: str = i

        return self

    def get_texture(self, text: str, regex: str = None) -> str:
        """Returns the texture if it matches the regex"""
        if regex is not None:
            if re.search(regex, text, re.IGNORECASE) is not None:
                return text
    
    @property
    def metalness_roughness_flow(self) -> bool:
        return (self.metalness is not None) and (self.roughness is not None)

    @property
    def use_ao(self) -> bool:
        return self.ao is not None

    @property
    def IsValid(self) -> bool:
        data = self.get_data()
        for key, value in data.items():
            if value is not None:
                return True
        return False

    def get_data(self) -> dict[Optional[str]]:
        return {
            "diffuse": self.diffuse,
            "specular": self.specular,
            "metalness": self.metalness,
            "roughness": self.roughness,
            "glossiness": self.glossiness,
            "ao": self.ao,
            "alpha": self.alpha,
            "bump": self.bump,
            "normal": self.normal,
            "emission": self.emission,
            "displacement": self.displacement,
            "transmission": self.transmission,
            "sheen": self.sheen,
            "anisotropy": self.anisotropy
        }

    def get_valid_dict(self) -> dict:
        data = self.get_data()
        res = {}
        for key, value in data.items():
            if value is not None:
                res[key] = value
        return res

#=============================================
# PBR Material from package
#=============================================
def ArnoldPbrFromPackage(folder: str, pbr_name: str, triplanar: bool = True, use_displacement: bool = False, doc: c4d.documents.BaseDocument=None) -> Optional[c4d.BaseMaterial]:
    if doc is None:
        doc = c4d.documents.GetActiveDocument()
    pbrInstance = PBRPackage(folder, pbr_name)
    pbrInstance.build()
    data = pbrInstance.get_valid_dict()
    material = Arnold.Material(pbr_name)

    with EasyTransaction(material) as tr:
        standard_surface = tr.GetRootBRDF()
        tr.SetName(standard_surface, pbr_name)

        # get ports
        albedoPort = tr.GetPort(standard_surface,'base_color')
        specularPort = tr.GetPort(standard_surface,'specular_color')
        roughnessPort = tr.GetPort(standard_surface,'specular_roughness')
        metalnessPort = tr.GetPort(standard_surface,'metalness')
        opacityPort = tr.GetPort(standard_surface,'opacity')
        transmissionPort = tr.GetPort(standard_surface,'transmission_color')
        emissionPort = tr.GetPort(standard_surface,'emission_color')
        gloss2roughPort = None
        sheenPort = tr.GetPort(standard_surface,'sheen_color')
        anisotropyPort = tr.GetPort(standard_surface,'specular_anisotropy')
        triplanarID = "com.autodesk.arnold.shader.triplanar"

        try:
            # Base Color            
            if "ao" in data:
                aoNode = tr.AddTexture(filepath=data['ao'], shadername="AO")
                if "diffuse" in data:
                    tr.AddTextureTree(filepath=data['diffuse'], shadername="Albedo", raw=False, color_mode=True, color_mutiplier=aoNode, target_port=albedoPort, triplaner_node=triplanar)
            else:
                tr.AddTextureTree(filepath=data['diffuse'], shadername="Albedo", raw=False, target_port=albedoPort, triplaner_node=triplanar)
            # if triplaner:
            #     mat.AddTriPlanar(mat.GetPort(albedo,mat.GetConvertOutput(albedo)), 
            #                     mat.GetPort(albedo_cc := mat.GetNextNode(albedo)[0] ,mat.GetConvertInput(albedo_cc)))
            
            if "metalness" in data:
                node = tr.AddTexture(filepath=data['metalness'], shadername="metalness",target_port=metalnessPort)
                if triplanar:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),"input","output")
                if "anisotropy" in data:
                    node = tr.AddTexture(filepath=data['anisotropy'], shadername="anisotropy",target_port=anisotropyPort)
                    if triplanar:
                        tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),"input","output")
                if "specular" in data:
                    node = tr.AddTexture(filepath=data['specular'], shadername="Specular",target_port=specularPort)
                    if triplanar:
                        tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),"input","output")
            if "sheen" in data:
                node = tr.AddTexture(filepath=data['sheen'], shadername="sheen",target_port=sheenPort)
                if triplanar:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),"input","output")


            if "roughness" in data and "glossiness" not in data:
                node = tr.AddTextureTree(filepath=data['roughness'], shadername="roughness", target_port=roughnessPort, triplaner_node=triplanar)

            elif "glossiness" in data and "roughness" not in data:
                node = tr.AddTextureTree(filepath=data['roughness'], shadername="roughness", target_port=roughnessPort, triplaner_node=triplanar)

            if "normal" in data:
                tr.AddNormalTree(filepath=data['normal'], shadername="Normal", triplaner_node=triplanar)
            
            if "bump" in data and "normal" not in data:  
                tr.AddBumpTree(filepath=data['bump'], shadername="Bump", triplaner_node=triplanar)
            
            if "displacement" in data and use_displacement:
                tr.AddDisplacementTree(filepath=data['displacement'], shadername="Displacement", triplaner_node=triplanar)

            if "alpha" in data:
                node = tr.AddTexture(filepath=data['alpha'], shadername="Alpha",target_port=opacityPort)
                if triplanar:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),"input","output")
            if "emission" in data:
                node = tr.AddTexture(filepath=data['emission'], shadername="Emission", raw=False, target_port=emissionPort)
                if triplanar:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),"input","output")
            if "transmission" in data:
                node = tr.AddTexture(filepath=data['transmission'], shadername="Transmission", raw=True, target_port=transmissionPort)
                if triplanar:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),"input","output")
            tr.material.SetName(pbr_name)

        except Exception as e:
            raise RuntimeError (f"Unable to setup texture with {e}")

    tr.InsertMaterial(doc)
    doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, tr.material)
    tr.SetActive(doc)
    
    return tr.material

def RedshiftPbrFromPackage(folder: str, pbr_name: str, triplaner: bool = True, use_displacement: bool = False, doc: c4d.documents.BaseDocument=None) -> Optional[c4d.BaseMaterial]:
    if doc is None:
        doc = c4d.documents.GetActiveDocument()    
    pbrInstance = PBRPackage(folder, pbr_name)
    pbrInstance.build()
    data = pbrInstance.get_valid_dict()
    material = Redshift.Material(pbr_name)

    with EasyTransaction(material) as tr:
        standard_surface = tr.GetRootBRDF()
        tr.SetName(standard_surface, pbr_name)

        # get ports
        albedoPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.base_color')
        roughnessPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refl_roughness')
        metalnessPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.metalness')
        opacityPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.opacity_color')
        reflectionPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refr_color')
        emissionPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.emission_color')
        gloss2roughPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refr_isglossiness')
        specularPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refl_color')
        sheenPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.material.sheen_color')
        anisotropyPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.material.refl_aniso')
        triplanarID = "com.redshift3d.redshift4c4d.nodes.core.triplanar"
        triplanarInput = "com.redshift3d.redshift4c4d.nodes.core.triplanar.imagex"
        triplanarOutput = "com.redshift3d.redshift4c4d.nodes.core.triplanar.outcolor"

        try:
            if "ao" in data:
                aoNode = tr.AddTexture(filepath=data['ao'], shadername="AO")
                if "diffuse" in data:
                    tr.AddTextureTree(filepath=data['diffuse'], shadername="Albedo", raw=False, color_mode=True, color_mutiplier=aoNode, target_port=albedoPort, triplaner_node=triplaner)
            else:
                tr.AddTextureTree(filepath=data['diffuse'], shadername="Albedo", raw=False, target_port=albedoPort, triplaner_node=triplaner)
            
            if "metalness" in data:
                node = tr.AddTexture(filepath=data['metalness'], shadername="metalness",target_port=metalnessPort)
                if triplaner:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),"input","output")
                if "anisotropy" in data:
                    node = tr.AddTexture(filepath=data['anisotropy'], shadername="anisotropy",target_port=anisotropyPort)
                    if triplaner:
                        tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),triplanarInput,triplanarOutput)

            if "roughness" in data and "glossiness" not in data:
                node = tr.AddTextureTree(filepath=data['roughness'], shadername="roughness", target_port=roughnessPort, triplaner_node=triplaner)
            elif "glossiness" in data and "roughness" not in data:
                tr.SetPortData(gloss2roughPort,True)
                node = tr.AddTextureTree(filepath=data['glossiness'], shadername="roughness", target_port=roughnessPort, triplaner_node=triplaner)

            if "normal" in data:
                tr.AddBumpTree(filepath=data['normal'], shadername="Normal", triplaner_node=triplaner)
            
            if "bump" in data and "normal" not in data:  
                tr.AddBumpTree(filepath=data['bump'], shadername="Bump", triplaner_node=triplaner, bump_mode=0)

            if "displacement" in data and use_displacement:
                tr.AddDisplacementTree(filepath=data['displacement'], shadername="Displacement", triplaner_node=triplaner)

            if "sheen" in data:
                node = tr.AddTexture(filepath=data['sheen'], shadername="sheen",target_port=sheenPort)
                if triplaner:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),triplanarInput,triplanarOutput)
            if "specular" in data:
                node = tr.AddTexture(filepath=data['specular'], shadername="Specular",target_port=specularPort)
                if triplaner:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),triplanarInput,triplanarOutput)


            if "alpha" in data:
                node = tr.AddTexture(filepath=data['alpha'], shadername="Alpha",target_port=opacityPort)
                if triplaner:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),triplanarInput,triplanarOutput)
            if "emission" in data:
                node = tr.AddTexture(filepath=data['emission'], shadername="Emission", raw=False, target_port=emissionPort)
                if triplaner:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),triplanarInput,triplanarOutput)
            if "transmission" in data:
                node = tr.AddTexture(filepath=data['transmission'], shadername="Transmission", raw=True, target_port=reflectionPort)
                if triplaner:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),triplanarInput,triplanarOutput)
            tr.material.SetName(pbr_name)

        except Exception as e:
            raise RuntimeError (f"Unable to setup texture with {e}")

    tr.InsertMaterial(doc)
    doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, tr.material)
    tr.SetActive(doc)
    
    return tr.material

def OctanePbrFromPackage(folder: str, pbr_name: str, triplaner: bool = True, use_displacement: bool = False, doc: c4d.documents.BaseDocument=None) -> Optional[c4d.BaseMaterial]:
    if doc is None:
        doc = c4d.documents.GetActiveDocument()
    pbrInstance = PBRPackage(folder, pbr_name)
    pbrInstance.build()
    data = pbrInstance.get_valid_dict()
    tr = Octane.Material(pbr_name)

    if "diffuse" in data:
        albedoNode = tr.AddImageTexture(texturePath=data['diffuse'], nodeName="Albedo", isFloat=False, gamma=2.2)
        if albedoNode:
            ccAlbedoNode = tr.AddCC(albedoNode)
            if "ao" in data:
                aoNode = tr.AddImageTexture(texturePath=data['ao'], nodeName="AO")
                if aoNode:
                    tr.AddMultiply(ccAlbedoNode, aoNode, c4d.OCT_MATERIAL_DIFFUSE_LINK)
            else:
                tr.material[c4d.OCT_MATERIAL_DIFFUSE_LINK] = ccAlbedoNode

    if "metalness" in data:
        tr.AddImageTexture(data['metalness'], "Metalness",parentNode=c4d.OCT_MAT_SPECULAR_MAP_LINK)
        if "anisotropy" in data:
            tr.AddImageTexture(data['anisotropy'], "Anisotropy",parentNode=c4d.OCT_MAT_ANISOTROPY_FLOAT)
        if "specular" in data:
            tr.AddImageTexture(data['specular'], "Specular",parentNode=c4d.OCT_MATERIAL_SPECULAR_LINK)

    if "roughness" in data:
        tr.AddTextureTree(data['roughness'], "Roughness", parentNode=c4d.OCT_MATERIAL_ROUGHNESS_LINK)

    if "sheen" in data:
        tr.AddTextureTree(data['sheen'], "Sheen", parentNode=c4d.OCT_MAT_SHEEN_MAP_FLOAT)

    if "normal" in data:
        tr.AddImageTexture(texturePath=data['normal'], nodeName="Normal", isFloat=False, gamma=1, parentNode=c4d.OCT_MATERIAL_NORMAL_LINK)
    
    if "bump" in data and "normal" not in data:  
        tr.AddImageTexture(texturePath=data['bump'], nodeName="Bump",parentNode=c4d.OCT_MATERIAL_BUMP_LINK)
    
    if "displacement" in data and use_displacement:
        displacementNode = tr.AddDisplacement(c4d.OCT_MATERIAL_DISPLACEMENT_LINK)
        if displacementNode:
            displacementNode[c4d.DISPLACEMENT_LEVELOFDETAIL] = 11 # 2k
            displacementNode[c4d.DISPLACEMENT_MID] = 0.5
            displacementSlotName = c4d.DISPLACEMENT_TEXTURE
            displacementNode[displacementSlotName] = tr.AddImageTexture(texturePath=data['displacement'], nodeName="Displacement")
    if "alpha" in data:
        tr.AddImageTexture(texturePath=data['alpha'], nodeName="Alpha", parentNode=c4d.OCT_MATERIAL_OPACITY_LINK)
    if "emission" in data:
        emission = tr.AddTextureEmission(parentNode=c4d.OCT_MATERIAL_EMISSION)
        tr.AddImageTexture(texturePath=emission, nodeName="Emission", gamma=1, parentNode=emission[c4d.TEXEMISSION_EFFIC_OR_TEX])

    if "transmission" in data:
        tr.AddImageTexture(texturePath=data['rransmission'], nodeName="Transmission", gamma=1, parentNode=c4d.OCT_MATERIAL_TRANSMISSION_LINK)
        tr.material[c4d.UNIVMAT_TRANSMISSION_TYPE] = 1
    tr.material.SetName(pbr_name)

    if triplaner:
        tr.AddTriplanars()

    tr.InsertMaterial(doc)
    doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, tr.material)
    tr.SetActive(doc)
    
    return tr.material

def CoronaPbrFromPackage(folder: str, pbr_name: str, triplaner: bool = True, use_displacement: bool = False, doc: c4d.documents.BaseDocument=None) -> Optional[c4d.BaseMaterial]:
    if doc is None:
        doc = c4d.documents.GetActiveDocument()
    pbrInstance = PBRPackage(folder, pbr_name)
    pbrInstance.build()
    data = pbrInstance.get_valid_dict()
    tr = Corona.Material(pbr_name)

    # Base Color
    if "diffuse" in data:
        tr.AddBitmapShader(data['diffuse'] , "Albedo", c4d.CORONA_PHYSICAL_MATERIAL_BASE_COLOR_TEXTURE, Corona.CR_COLORSPACE_SRGB)

    if "metalness" in data:
        tr.material[c4d.CORONA_PHYSICAL_MATERIAL_METALLIC_MODE_VALUE] = 0  # metal
        tr.AddBitmapShader(data['metalness'], "Metalness", c4d.CORONA_PHYSICAL_MATERIAL_METALLIC_MODE_TEXTURE)
        if "anisotropy" in data:
            tr.AddBitmapShader(data['anisotropy'], "Anisotropy", c4d.CORONA_PHYSICAL_MATERIAL_BASE_ANISOTROPY_TEXTURE)
        if "specular" in data:
            tr.material[c4d.CORONA_PHYSICAL_MATERIAL_BASE_BUMPMAPPING_ENABLE] = 1
            tr.AddNormalShader(data['specular'], "Specular", c4d.CORONA_PHYSICAL_MATERIAL_BASE_EDGECOLOR_TEXTURE)
    if "sheen" in data:
        tr.material[c4d.CORONA_PHYSICAL_MATERIAL_SHEEN] = 1
        tr.AddNormalShader(data['sheen'], "Sheen", c4d.CORONA_PHYSICAL_MATERIAL_SHEEN_AMOUNT_TEXTURE)

    if "roughness" in data:
        tr.AddBitmapShader(data['roughness'], "Roughness", c4d.CORONA_PHYSICAL_MATERIAL_BASE_ROUGHNESS_TEXTURE)
        tr.material[c4d.CORONA_PHYSICAL_MATERIAL_ROUGHNESS_MODE] = 0
    if "normal" in data:
        tr.material[c4d.CORONA_PHYSICAL_MATERIAL_BASE_BUMPMAPPING_ENABLE] = 1
        tr.AddNormalShader(data['normal'], "Normal", c4d.CORONA_PHYSICAL_MATERIAL_BASE_BUMPMAPPING_TEXTURE)
    if "bump" in data and "normal" not in data:  
        tr.AddBitmapShader(data['bump'], "Bump", c4d.CORONA_PHYSICAL_MATERIAL_BASE_BUMPMAPPING_TEXTURE)
    
    if "displacement" in data and use_displacement:
        tr.material[c4d.CORONA_PHYSICAL_MATERIAL_DISPLACEMENT]=1
        tr.material[c4d.CORONA_PHYSICAL_MATERIAL_DISPLACEMENT_MAX_LEVEL] = 0.1
        tr.AddBitmapShader(data['displacement'], "Displacement", c4d.CORONA_PHYSICAL_MATERIAL_DISPLACEMENT_TEXTURE)
    if "alpha" in data:
        tr.material[c4d.CORONA_PHYSICAL_MATERIAL_ALPHA] = True
        tr.AddBitmapShader(data['alpha'], "Opacity", c4d.CORONA_PHYSICAL_MATERIAL_ALPHA_TEXTURE)
    if "emission" in data:
        tr.AddBitmapShader(data['emission'], "Emission", c4d.CORONA_PHYSICAL_MATERIAL_EMISSION_TEXTURE)

    if "transmission" in data:
        tr.AddBitmapShader(data['transmission'], "Transmission", c4d.CORONA_PHYSICAL_MATERIAL_REFRACT_AMOUNT_TEXTURE)

    tr.InsertMaterial(doc)
    doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, tr.material)
    tr.SetActive(doc)

    return tr.material

def VrayPbrFromPackage(folder: str, pbr_name: str, triplaner: bool = True, use_displacement: bool = False, doc: c4d.documents.BaseDocument=None) -> Optional[c4d.BaseMaterial]:
    if doc is None:
        doc = c4d.documents.GetActiveDocument()
    pbrInstance = PBRPackage(folder, pbr_name)
    pbrInstance.build()
    data = pbrInstance.get_valid_dict()
    material = Vray.Material(pbr_name)

    with EasyTransaction(material) as tr:
        base_material = tr.GetRootBRDF()
        tr.SetName(base_material, pbr_name)

        # get ports
        albedoPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.diffuse')
        roughnessPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.reflect_glossiness')
        metalnessPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.metalness')
        opacityPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.opacity_color')
        reflectionPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.refract')
        useRoughness = tr.GetPort(base_material,"com.chaos.vray_node.brdfvraymtl.option_use_roughness")
        normalPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.bump_map')
        emissionPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.self_illumination')
        sheenPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.sheen_color')
        anisotropyPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.anisotropy')
        specularPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.reflectr')

        triplanarID = "com.chaos.vray_node.textriplanar"
        triplanarInput = "com.chaos.vray_node.textriplanar.texture_x"
        triplanarOutput = "com.chaos.vray_node.textriplanar.output.default"

        try:
            # Base Color            
            if "diffuse" in data and "ao" not in data:
                node = tr.AddTexture(filepath=data['diffuse'], shadername="Albedo", raw=False, target_port=albedoPort)
                if triplaner:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),triplanarInput,triplanarOutput)
            if "diffuse" in data and "ao" in data:
                aoNode = tr.AddTexture(filepath=data['ao'], shadername="AO")
                texNode = tr.AddTexture(filepath=data['diffuse'], shadername="Albedo", raw=False)
                ao_out = tr.GetPort(aoNode,"com.chaos.vray_node.texbitmap.output.default")
                tex_out = tr.GetPort(texNode,"com.chaos.vray_node.texbitmap.output.default")
                tr.AddLayer(tex_out, ao_out, target=albedoPort)
                if triplaner:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(texNode),triplanarInput,triplanarOutput)
                if triplaner:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(aoNode),triplanarInput,triplanarOutput)
            if "metalness" in data:
                node = tr.AddTexture(filepath=data['metalness'], shadername="Metalness",target_port=metalnessPort)
                if triplaner:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),triplanarInput,triplanarOutput)
                if "anisotropy" in data:
                    node = tr.AddTexture(filepath=data['anisotropy'], shadername="Anisotropy",target_port=anisotropyPort)
                    if triplaner:
                        tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),triplanarInput,triplanarOutput)

            if "specular" in data:
                node = tr.AddTexture(filepath=data['specular'], shadername="specular",target_port=specularPort)
                if triplaner:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),triplanarInput,triplanarOutput)

            if "roughness" in data and "glossiness" not in data:
                tr.SetPortData(useRoughness, True)
                node = tr.AddTexture(filepath=data['roughness'], shadername="Roughness",target_port=roughnessPort)
                if triplaner:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),triplanarInput,triplanarOutput)
            elif "glossiness" in data and "glossiness" not in data:
                tr.SetPortData(useRoughness, False)
                node = tr.AddTexture(filepath=data['roughness'], shadername="Roughness",target_port=roughnessPort)
                if triplaner:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),triplanarInput,triplanarOutput)

            if "normal" in data:
                tr.AddBumpTree(filepath=data['normal'], shadername="Normal",bump_mode=1,target_port=normalPort, triplaner_node=triplaner)
            
            if "bump" in data and "normal" not in data:  
                tr.AddBumpTree(filepath=data['bump'], shadername="Bump", triplaner_node=triplaner, bump_mode=0)
            if "displacement" in data and use_displacement:
                pass

            if "sheen" in data:
                node = tr.AddTexture(filepath=data['sheen'], shadername="sheen",target_port=sheenPort)
                if triplaner:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),triplanarInput,triplanarOutput)

            if "alpha" in data:
                node = tr.AddTexture(filepath=data['alpha'], shadername="Alpha",target_port=opacityPort)
                if triplaner:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),triplanarInput,triplanarOutput)
            if "emission" in data:
                node = tr.AddTexture(filepath=data['emission'], shadername="Emission", raw=False, target_port=emissionPort)
                if triplaner:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),triplanarInput,triplanarOutput)
            if "transmission" in data:
                node = tr.AddTexture(filepath=data['transmission'], shadername="Translucency", raw=False, target_port=reflectionPort)
                if triplaner:
                    tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),triplanarInput,triplanarOutput)
            tr.material.SetName(pbr_name)

        except Exception as e:
            raise RuntimeError (f"Unable to setup texture with {e}")

    tr.InsertMaterial(doc)
    doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, tr.material)
    tr.SetActive(doc)
    
    return tr.material

#=============================================
# PBR Material with PBR slots
#=============================================
def ArnoldPbrMaterial(doc: c4d.documents.BaseDocument=None, name: str=None, albedo: str=None, ao: str=None, 
                      metalness: str=None, roughness: str=None, alpha: str=None, bump: str=None, normal: str=None, displacement: str=None, 
                      emission: str=None, transmission: str=None, sheen: str=None, specular: str=None, anisotropy: str=None,
                      triplanar: bool = True) -> Optional[c4d.BaseMaterial]:

    if doc is None:
        doc = c4d.documents.GetActiveDocument()
    # isSpecularWorkflow = not pbrInstance.metalness_roughness_flow
    if Arnold.IsNodeBased():
        try:
            material = Arnold.Material(name)

            with EasyTransaction(material) as tr:
                standard_surface = tr.GetRootBRDF()
                tr.SetName(standard_surface, name)
                # get ports
                albedoPort = tr.GetPort(standard_surface,'base_color')
                roughnessPort = tr.GetPort(standard_surface,'specular_roughness')
                metalnessPort = tr.GetPort(standard_surface,'metalness')
                opacityPort = tr.GetPort(standard_surface,'opacity')
                reflectionPort = tr.GetPort(standard_surface,'transmission_color')
                emissionPort = tr.GetPort(standard_surface,'emission_color')
                gloss2roughPort = None
                sheenPort = tr.GetPort(standard_surface,'sheen_color')
                anisotropyPort = tr.GetPort(standard_surface,'specular_anisotropy')
                specularPort = tr.GetPort(standard_surface,'specular_color')
                triplanarID = "com.autodesk.arnold.shader.triplanar"

                # Base Color            
                if ao:
                    aoNode = tr.AddTexture(filepath=ao, shadername="AO")
                    if albedo:
                        tr.AddTextureTree(filepath=albedo, shadername="Albedo", raw=False, color_mode=True, color_mutiplier=aoNode,triplaner_node=triplanar, target_port=albedoPort)
                else:
                    tr.AddTextureTree(filepath=albedo, shadername="Albedo", raw=False, target_port=albedoPort,triplaner_node=triplanar)
                
                if metalness:
                    node = tr.AddTexture(filepath=metalness, shadername="Metalness",target_port=metalnessPort)
                    if triplanar:
                        tr.InsertShader(triplanarID, tr.GetConnectedPortsAfter(node), "input", "output")
                    if anisotropy:
                        node = tr.AddTexture(filepath=anisotropy, shadername="anisotropy",target_port=anisotropyPort)
                        if triplanar:
                            tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),"input","output")
                    if specular:
                        node = tr.AddTexture(filepath=specular, shadername="Specular",target_port=specularPort)
                        if triplanar:
                            tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),"input","output")
                if roughness:
                    tr.AddTextureTree(filepath=roughness, shadername="Roughness",triplaner_node=triplanar, target_port=roughnessPort)               

                if sheen:
                    node = tr.AddTexture(filepath=sheen, shadername="sheen",target_port=sheenPort)
                    if triplanar:
                        tr.InsertShader(triplanarID,tr.GetConnectedPortsAfter(node),"input","output")

                if normal:
                    tr.AddNormalTree(filepath=normal, shadername="Normal",triplaner_node=triplanar)
                
                if bump is not None and normal is None:  
                    tr.AddBumpTree(filepath=bump, shadername="Bump",triplaner_node=triplanar)
                
                if displacement:
                    tr.AddDisplacementTree(filepath=displacement, shadername="Displacement",triplaner_node=triplanar)

                if alpha:
                    node = tr.AddTexture(filepath=alpha, shadername="Alpha",target_port=opacityPort)
                    if triplanar:
                        tr.InsertShader(triplanarID, tr.GetConnectedPortsAfter(node), "input", "output")
                if emission:
                    node = tr.AddTexture(filepath=emission, shadername="Emission", raw=False, target_port=emissionPort)
                    if triplanar:
                        tr.InsertShader(triplanarID, tr.GetConnectedPortsAfter(node), "input", "output")
                if transmission:
                    node = tr.AddTexture(filepath=transmission, shadername="Transmission", raw=True, target_port=reflectionPort)
                    if triplanar:
                        tr.InsertShader(triplanarID, tr.GetConnectedPortsAfter(node), "input", "output")

            tr.InsertMaterial(doc)
            if isinstance(doc, c4d.documents.BaseDocument):
                doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, tr.material)
            tr.SetActive(doc)
            return tr.material
            
        except Exception as e:
            raise RuntimeError (f"Unable to setup texture with {e}")

def RedshiftPbrMaterial(doc: c4d.documents.BaseDocument=None, name: str=None, albedo: str=None, ao: str=None, 
                      metalness: str=None, roughness: str=None, alpha: str=None, bump: str=None, normal: str=None, displacement: str=None, 
                      emission: str=None, transmission: str=None, sheen: str=None, specular: str=None, anisotropy: str=None, glossiness: str=None,
                      triplanar: bool = True) -> Optional[c4d.BaseMaterial]:
    if doc is None:
        doc = c4d.documents.GetActiveDocument()
    if Redshift.IsNodeBased():
        try:        
            material =  Redshift.Material(name)

            with EasyTransaction(material) as tr:

                standard_surface = tr.GetRootBRDF()
                tr.SetName(standard_surface, name)

                # get ports
                albedoPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.base_color')
                roughnessPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refl_roughness')
                metalnessPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.metalness')
                opacityPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.opacity_color')
                reflectionPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refr_color')
                emissionPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.emission_color')
                gloss2roughPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refr_isglossiness')
                specularPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.refl_color')
                sheenPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.material.sheen_color')
                anisotropyPort = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.material.refl_aniso')
                triplanarID = "com.redshift3d.redshift4c4d.nodes.core.triplanar"
                triplanarInput = "com.redshift3d.redshift4c4d.nodes.core.triplanar.imagex"
                triplanarOutput = "com.redshift3d.redshift4c4d.nodes.core.triplanar.outcolor"

                if ao:
                    aoNode = tr.AddTexture(filepath=ao, shadername="AO")
                    if albedo:
                        tr.AddTextureTree(filepath=albedo, shadername="Albedo", raw=False, color_mode=True, color_mutiplier=aoNode,triplaner_node=triplanar, target_port=albedoPort)
                else:
                    tr.AddTextureTree(filepath=albedo, shadername="Albedo", raw=False, target_port=albedoPort,triplaner_node=triplanar)

                if albedo and ao is not None: 
                    tr.AddTextureTree(filepath=albedo, shadername="Albedo", raw=False, color_mode=True, target_port=albedoPort)
                
                if metalness:
                    node = tr.AddTexture(filepath=metalness, shadername="Metalness",target_port=metalnessPort)
                    if triplanar:
                        tr.InsertShader(triplanarID, tr.GetConnectedPortsAfter(node), triplanarInput, triplanarOutput)
                    if specular:
                        node = tr.AddTexture(filepath=specular, shadername="Specular",target_port=specularPort)
                        if triplanar:
                            tr.InsertShader(triplanarID, tr.GetConnectedPortsAfter(node), triplanarInput, triplanarOutput)
                    if anisotropy:
                        node = tr.AddTexture(filepath=anisotropy, shadername="Anisotropy",target_port=anisotropyPort)
                        if triplanar:
                            tr.InsertShader(triplanarID, tr.GetConnectedPortsAfter(node), triplanarInput, triplanarOutput)

                if roughness and not glossiness:
                    tr.AddTextureTree(filepath=roughness, shadername="Roughness",triplaner_node=triplanar, target_port=roughnessPort)               
                elif glossiness and not roughness:
                    tr.SetPortData(gloss2roughPort,True)
                    node = tr.AddTextureTree(filepath=glossiness, shadername="Roughness", target_port=roughnessPort, triplaner_node=triplanar)
            
                if normal:
                    tr.AddBumpTree(filepath=normal, shadername="Normal",triplaner_node=triplanar)
                
                if bump is not None and normal is None:  
                    tr.AddBumpTree(filepath=bump, shadername="Bump",triplaner_node=triplanar,bump_mode=0)
                
                if displacement:
                    tr.AddDisplacementTree(filepath=displacement, shadername="Displacement",triplaner_node=triplanar)

                if alpha:
                    node = tr.AddTexture(filepath=alpha, shadername="Alpha",target_port=opacityPort)
                    if triplanar:
                        tr.InsertShader(triplanarID, tr.GetConnectedPortsAfter(node), triplanarInput, triplanarOutput)
                if emission:
                    node = tr.AddTexture(filepath=emission, shadername="Emission", raw=False, target_port=emissionPort)
                    if triplanar:
                        tr.InsertShader(triplanarID, tr.GetConnectedPortsAfter(node), triplanarInput, triplanarOutput)
                if transmission:
                    node = tr.AddTexture(filepath=transmission, shadername="Transmission", raw=True, target_port=reflectionPort)
                    if triplanar:
                        tr.InsertShader(triplanarID, tr.GetConnectedPortsAfter(node), triplanarInput, triplanarOutput)
                if sheen:
                    node = tr.AddTexture(filepath=sheen, shadername="Sheen", raw=True, target_port=sheenPort)
                    if triplanar:
                        tr.InsertShader(triplanarID, tr.GetConnectedPortsAfter(node), triplanarInput, triplanarOutput)
            tr.InsertMaterial(doc)
            if isinstance(doc, c4d.documents.BaseDocument):
                doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, tr.material)
            tr.SetActive(doc)
            return tr.material

        except Exception as e:
            raise RuntimeError (f"Unable to setup texture with {e}")

def VrayPbrMaterial(doc: c4d.documents.BaseDocument=None, name: str=None, albedo: str=None, ao: str=None, 
                      metalness: str=None, roughness: str=None, alpha: str=None, bump: str=None, normal: str=None, displacement: str=None, 
                      emission: str=None, transmission: str=None, sheen: str=None, specular: str=None, anisotropy: str=None, glossiness: str=None,
                      triplanar: bool = True) -> Optional[c4d.BaseMaterial]:
    if doc is None:
        doc = c4d.documents.GetActiveDocument()
    try:        
        Material =  Vray.Material(name)

        with EasyTransaction(Material) as tr:

            base_material = tr.GetRootBRDF()

            tr.SetName(base_material, f'{name} Shader')

            # get ports
            albedoPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.diffuse')
            # specularPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.reflect')
            roughnessPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.reflect_glossiness')
            metalnessPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.metalness')
            opacityPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.opacity_color')
            reflectionPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.refract')
            useRoughness = tr.GetPort(base_material,"com.chaos.vray_node.brdfvraymtl.option_use_roughness")
            sheenPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.sheen_color')
            anisotropyPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.anisotropy')
            specularPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.reflectr')

            emissionPort = tr.GetPort(base_material,'com.chaos.vray_node.brdfvraymtl.emission_color')
            triplanarID = "com.chaos.vray_node.textriplanar"
            triplanarInput = "com.chaos.vray_node.textriplanar.texture_x"
            triplanarOutput = "com.chaos.vray_node.textriplanar.output.default"

            # Base Color
            if ao:
                aoNode = tr.AddTexture(filepath=ao, shadername="AO")
                if albedo:
                    tr.AddTextureTree(filepath=albedo, shadername="Albedo", raw=False, color_mode=True, color_mutiplier=aoNode,triplaner_node=triplanar, target_port=albedoPort)
            else:
                tr.AddTextureTree(filepath=albedo, shadername="Albedo", raw=False, target_port=albedoPort,triplaner_node=triplanar)
            
            if metalness:
                node = tr.AddTexture(filepath=metalness, shadername="Metalness",target_port=metalnessPort)
                if triplanar:
                    tr.InsertShader(triplanarID, tr.GetConnectedPortsAfter(node), triplanarInput, triplanarOutput)
                if specular:
                    node = tr.AddTexture(filepath=specular, shadername="Specular",target_port=specularPort)
                    if triplanar:
                        tr.InsertShader(triplanarID, tr.GetConnectedPortsAfter(node), triplanarInput, triplanarOutput)
                if anisotropy:
                    node = tr.AddTexture(filepath=anisotropy, shadername="Anisotropy",target_port=anisotropyPort)
                    if triplanar:
                        tr.InsertShader(triplanarID, tr.GetConnectedPortsAfter(node), triplanarInput, triplanarOutput)

            if roughness and not glossiness:
                tr.SetPortData(useRoughness, True)
                tr.AddTextureTree(filepath=roughness, shadername="Roughness",triplaner_node=triplanar, target_port=roughnessPort)   
            elif glossiness and not roughness:
                tr.SetPortData(useRoughness, False)
                tr.AddTextureTree(filepath=glossiness, shadername="Glossiness",triplaner_node=triplanar, target_port=roughnessPort)

            if normal:
                tr.AddBumpTree(filepath=normal, shadername="Normal",triplaner_node=triplanar,bump_mode=1)
            
            if bump is not None and normal is None:  
                tr.AddBumpTree(filepath=bump, shadername="Bump",triplaner_node=triplanar,bump_mode=0)

            if displacement:
                tr.AddDisplacementTree(filepath=displacement, shadername="Displacement",triplaner_node=triplanar)

            if alpha:
                node = tr.AddTexture(filepath=alpha, shadername="Alpha",target_port=opacityPort)
                if triplanar:
                    tr.InsertShader(triplanarID, tr.GetConnectedPortsAfter(node), triplanarInput, triplanarOutput)
            if emission:
                node = tr.AddTexture(filepath=emission, shadername="Emission", raw=False, target_port=emissionPort)
                if triplanar:
                    tr.InsertShader(triplanarID, tr.GetConnectedPortsAfter(node), triplanarInput, triplanarOutput)
            if transmission:
                node = tr.AddTexture(filepath=transmission, shadername="Transmission", raw=True, target_port=reflectionPort)
                if triplanar:
                    tr.InsertShader(triplanarID, tr.GetConnectedPortsAfter(node), triplanarInput, triplanarOutput)
            if sheen:
                node = tr.AddTexture(filepath=sheen, shadername="Sheen", raw=True, target_port=sheenPort)
                if triplanar:
                    tr.InsertShader(triplanarID, tr.GetConnectedPortsAfter(node), triplanarInput, triplanarOutput)

        tr.InsertMaterial(doc)
        if isinstance(doc, c4d.documents.BaseDocument):
            doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, tr.material)
        tr.SetActive(doc)
        return tr.material

    except Exception as e:
        raise RuntimeError(f"Failed to import the textures {e}")

def OctanePbrMaterial(doc: c4d.documents.BaseDocument=None, name: str=None, albedo: str=None, ao: str=None, 
                      metalness: str=None, roughness: str=None, alpha: str=None, bump: str=None, normal: str=None, displacement: str=None, 
                      emission: str=None, transmission: str=None, sheen: str=None, specular: str=None, anisotropy: str=None,
                      triplanar: bool = True) -> Optional[c4d.BaseMaterial]:
    if doc is None:
        doc = c4d.documents.GetActiveDocument()
    mat = Octane.Material(name)
    try:
        # 
        if albedo:
            albedoNode = mat.AddImageTexture(texturePath=albedo, nodeName="Albedo", isFloat=False, gamma=2.2)
            if albedoNode:
                ccAlbedoNode = mat.AddCC(albedoNode)
                if ao:
                    aoNode = mat.AddImageTexture(texturePath=ao, nodeName="AO")
                    if aoNode:
                        mat.AddMultiply(ccAlbedoNode, aoNode, c4d.OCT_MATERIAL_DIFFUSE_LINK)
                else:
                    mat.material[c4d.OCT_MATERIAL_DIFFUSE_LINK] = ccAlbedoNode

        if metalness:
            mat.AddImageTexture(texturePath=metalness, nodeName="Metalness", parentNode=c4d.OCT_MAT_SPECULAR_MAP_LINK)
            if anisotropy:
                mat.AddImageTexture(anisotropy, "Anisotropy",parentNode=c4d.OCT_MAT_ANISOTROPY_FLOAT)
            if specular:
                mat.AddImageTexture(specular, "Specular",parentNode=c4d.OCT_MATERIAL_SPECULAR_LINK)

        if roughness:
            roughnessNode = mat.AddImageTexture(texturePath=roughness, nodeName="Roughness")
            if roughnessNode:
                mat.AddCC(roughnessNode,parentNode=c4d.OCT_MATERIAL_ROUGHNESS_LINK)

        if bump:  
            mat.AddImageTexture(texturePath=bump, nodeName="Bump",parentNode=c4d.OCT_MATERIAL_BUMP_LINK)

        if normal:  
            mat.AddImageTexture(texturePath=normal, nodeName="Normal", isFloat=False, gamma=1, parentNode=c4d.OCT_MATERIAL_NORMAL_LINK)
        
        if displacement:
            displacementNode = mat.AddDisplacement(c4d.OCT_MATERIAL_DISPLACEMENT_LINK)
            if displacementNode:
                displacementNode[c4d.DISPLACEMENT_LEVELOFDETAIL] = 11 # 2k
                displacementSlotName = c4d.DISPLACEMENT_TEXTURE
                displacementNode[displacementSlotName] = mat.AddImageTexture(texturePath=displacement, nodeName="Displacement")

        if alpha:  
            mat.AddImageTexture(texturePath=alpha, nodeName="Alpha", parentNode=c4d.OCT_MATERIAL_OPACITY_LINK)

        if transmission:  
            mat.AddImageTexture(texturePath=transmission, nodeName="Transmission", gamma=1, parentNode=c4d.OCT_MATERIAL_TRANSMISSION_LINK)
            mat.material[c4d.UNIVMAT_TRANSMISSION_TYPE] = 1

        if sheen:
            mat.AddTextureTree(sheen, "Sheen", parentNode=c4d.OCT_MAT_SHEEN_MAP_FLOAT)

        if emission:  
            emission = mat.AddTextureEmission(parentNode=c4d.OCT_MATERIAL_EMISSION)
            mat.AddImageTexture(texturePath=emission, nodeName="Emission", gamma=1, parentNode=emission[c4d.TEXEMISSION_EFFIC_OR_TEX])
            
        mat.material.SetName(name)

        if triplanar:
            mat.AddTriplanars()

        mat.InsertMaterial(doc)
        if isinstance(doc, c4d.documents.BaseDocument):
            doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, mat.material)
        mat.SetActive(doc)
        return mat.material
    
    except Exception as e:
        pass
        # raise RuntimeError(f"Failed to create the material {e}")
    
def CoronaPbrMaterial(doc: c4d.documents.BaseDocument=None, name: str=None, albedo: str=None, ao: str=None, 
                      metalness: str=None, roughness: str=None, alpha: str=None, bump: str=None, normal: str=None, displacement: str=None, 
                      emission: str=None, transmission: str=None, sheen: str=None, specular: str=None, anisotropy: str=None,
                      triplanar: bool = True) -> Optional[c4d.BaseMaterial]:
    if doc is None:
        doc = c4d.documents.GetActiveDocument()

    tr = Corona.Material(name)
    try:
        if albedo:
            tr.AddBitmapShader(albedo , "Albedo", c4d.CORONA_PHYSICAL_MATERIAL_BASE_COLOR_TEXTURE, Corona.CR_COLORSPACE_SRGB)

        if metalness:
            tr.material[c4d.CORONA_PHYSICAL_MATERIAL_METALLIC_MODE_VALUE] = 0  # metal
            tr.AddBitmapShader(metalness, "Metalness", c4d.CORONA_PHYSICAL_MATERIAL_METALLIC_MODE_TEXTURE)
            if anisotropy:
                tr.AddBitmapShader(anisotropy, "Anisotropy", c4d.CORONA_PHYSICAL_MATERIAL_BASE_ANISOTROPY_TEXTURE)
            if specular:
                tr.material[c4d.CORONA_PHYSICAL_MATERIAL_BASE_BUMPMAPPING_ENABLE] = 1
                tr.AddNormalShader(specular, "Specular", c4d.CORONA_PHYSICAL_MATERIAL_BASE_EDGECOLOR_TEXTURE)
        if roughness:
            tr.AddBitmapShader(roughness, "Roughness", c4d.CORONA_PHYSICAL_MATERIAL_BASE_ROUGHNESS_TEXTURE)
            tr.material[c4d.CORONA_PHYSICAL_MATERIAL_ROUGHNESS_MODE] = 0
        if sheen:
            tr.material[c4d.CORONA_PHYSICAL_MATERIAL_SHEEN] = 1
            tr.AddNormalShader(sheen, "Sheen", c4d.CORONA_PHYSICAL_MATERIAL_SHEEN_AMOUNT_TEXTURE)
        if bump:  
            tr.AddBitmapShader(bump, "Bump", c4d.CORONA_PHYSICAL_MATERIAL_BASE_BUMPMAPPING_TEXTURE)
        if normal:  
            tr.material[c4d.CORONA_PHYSICAL_MATERIAL_BASE_BUMPMAPPING_ENABLE] = 1
            tr.AddNormalShader(normal, "Normal", c4d.CORONA_PHYSICAL_MATERIAL_BASE_BUMPMAPPING_TEXTURE)
        if displacement:
            tr.material[c4d.CORONA_PHYSICAL_MATERIAL_DISPLACEMENT]=1
            tr.material[c4d.CORONA_PHYSICAL_MATERIAL_DISPLACEMENT_MAX_LEVEL] = 0.1
            tr.AddBitmapShader(displacement, "Displacement", c4d.CORONA_PHYSICAL_MATERIAL_DISPLACEMENT_TEXTURE)

        if alpha:  
            tr.material[c4d.CORONA_PHYSICAL_MATERIAL_ALPHA] = True
            tr.AddBitmapShader(alpha, "Opacity", c4d.CORONA_PHYSICAL_MATERIAL_ALPHA_TEXTURE)
        if transmission:  
            tr.AddBitmapShader(transmission, "Transmission", c4d.CORONA_PHYSICAL_MATERIAL_REFRACT_AMOUNT_TEXTURE)
        if emission:  
            tr.AddBitmapShader(emission, "Emission", c4d.CORONA_PHYSICAL_MATERIAL_EMISSION_TEXTURE)

        tr.InsertMaterial(doc)
        tr.SetActive(doc)
        return tr.material
    
    except Exception as e:
        raise RuntimeError(f"Failed to create the material {e}")

# to test
def C4DPbrMaterial(doc: c4d.documents.BaseDocument=None, name: str=None, albedo: str=None, ao: str=None, 
                      metalness: str=None, roughness: str=None, alpha: str=None, bump: str=None, normal: str=None, displacement: str=None, 
                      emission: str=None, transmission: str=None, sheen: str=None, specular: str=None, anisotropy: str=None,
                      triplanar: bool = True) -> Optional[c4d.BaseMaterial]:
    if doc is None:
        doc = c4d.documents.GetActiveDocument()
    # Create a bitmap shader to load a texture
    def _create_bitmap_shader(mat: c4d.BaseMaterial, texPath: str, name: str, link_name: int, colorspace: int, invert: bool = False):
        shader = c4d.BaseList2D(c4d.Xbitmap)
        shader[c4d.BITMAPSHADER_FILENAME] = texPath
        if invert:
            shader[c4d.BITMAPSHADER_BLACKPOINT] = 1
            shader[c4d.BITMAPSHADER_WHITEPOINT] = 0
        shader[c4d.BITMAPSHADER_COLORPROFILE] = 1 if colorspace == "linear" else 2
        shader.SetName(name)
        mat[link_name] = shader
        mat.InsertShader(shader)
        return shader

    # Create a sss shader
    def _create_sss_shader(mat: c4d.BaseMaterial, link_name: int):
        shader = c4d.BaseList2D(1025614)
        shader[c4d.XMBSUBSURFACESHADER_DIFFUSE] = c4d.Vector(1,1,1)
        mat[link_name] = shader
        mat.InsertShader(shader)
        return shader


    mat = c4d.Material(c4d.Mmaterial)
    mat.SetName(name)

    mat.RemoveReflectionLayerIndex(0) #Remove default specular layer
    mat.AddReflectionLayer() # Add lambertian diffuse layer
    mat.AddReflectionLayer() # Add GGX layer
    
    mat[c4d.MATERIAL_USE_COLOR] = True

    color_layer = mat.GetReflectionLayerIndex(1) # Get color layer reference
    refl_layer = mat.GetReflectionLayerIndex(0) # Get metal/non-metal layer reference

    color_layer.SetName("Base Color")
    refl_layer.SetName("Metal" if metalness else "Non-Metal")
    # Setting layers types to lambertian and GGX
    mat[color_layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION] = 7 
    mat[color_layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0 # set Specular strength
    mat[color_layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_BUMP_MODE] = 2 # Set Bump strength mode

    mat[refl_layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION] = 3
    mat[refl_layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0 # set Specular strength
    mat[refl_layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_BUMP_MODE] = 2 # Set Bump strength mode
    mat[refl_layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS] = 1 # 100% roughness
    # Set layer Fresnel properties according to type.
    if metalness:
        mat[refl_layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 1 # 100% specular strength
        mat[refl_layer.GetDataID() + c4d.REFLECTION_LAYER_FRESNEL_MODE] = 2 #conductor
        mat[refl_layer.GetDataID() + c4d.REFLECTION_LAYER_FRESNEL_VALUE_ETA] = 1.524
        #IOR
        mat[refl_layer.GetDataID() + c4d.REFLECTION_LAYER_FRESNEL_OPAQUE] = True # Opaque
    else:
        mat[refl_layer.GetDataID() + c4d.REFLECTION_LAYER_FRESNEL_MODE] = 1 #dielectric
        mat[refl_layer.GetDataID() + c4d.REFLECTION_LAYER_FRESNEL_VALUE_IOR] = 1.52 #IOR
    
    try:
        if albedo:
            _create_bitmap_shader(mat, albedo, "Albedo", color_layer.GetDataID() + c4d.REFLECTION_LAYER_COLOR_TEXTURE, "srgb")
            _create_bitmap_shader(mat, albedo, "Albedo", c4d.MATERIAL_COLOR_SHADER, "srgb")
        # elif item[1] == "metalness":
        #     _create_bitmap_shader(mat, item[2], "Metalness", refl_layer.GetDataID() + c4d.REFLECTION_LAYER_TRANS_TEXTURE, "linear", not isMetal)
        elif roughness:
            _create_bitmap_shader(mat, roughness, "Roughness", refl_layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_SHADER_ROUGHNESS, "linear")
        # elif item[1] == "gloss" and "roughness" not in available_textures:
        #     _create_bitmap_shader(mat, item[2], "Gloss", refl_layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_SHADER_ROUGHNESS, "linear", True)
        elif normal:
            _create_bitmap_shader(mat, normal, "Normals", color_layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_SHADER_BUMP_CUSTOM, "linear")
            _create_bitmap_shader(mat, normal, "Normals", refl_layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_SHADER_BUMP_CUSTOM, "linear")
        elif displacement:
            mat[c4d.MATERIAL_USE_DISPLACEMENT] = True
            _create_bitmap_shader(mat, displacement, "Displacement", c4d.MATERIAL_DISPLACEMENT_SHADER, "linear")
            mat[c4d.MATERIAL_DISPLACEMENT_HEIGHT] = 1
            mat[c4d.MATERIAL_DISPLACEMENT_SUBPOLY] = True
        elif alpha:
            mat[c4d.MATERIAL_USE_ALPHA] = True
            _create_bitmap_shader(mat, alpha, "Opacity", c4d.MATERIAL_ALPHA_SHADER, "linear")

        elif transmission:
            mat[c4d.MATERIAL_USE_LUMINANCE] = True
            sssShader = _create_sss_shader(mat, c4d.MATERIAL_LUMINANCE_SHADER)
            _create_bitmap_shader(sssShader, transmission, "Transmission", c4d.XMBSUBSURFACESHADER_SHADER, "linear")

    except Exception as e:
        raise RuntimeError(f"Failed to import the textures : {e}")

    if(c4d.GetC4DVersion() >= 23000):
        mat[c4d.MATERIAL_DISPLAY_USE_LUMINANCE] = False

    mat.Message(c4d.MSG_UPDATE)
    mat.Update(True, True)
    doc = c4d.documents.GetActiveDocument()
    doc.InsertMaterial(mat)
    return mat


ColorInfo: TypeAlias = Union[str, float, c4d.Vector, Sequence, maxon.Color64, maxon.Color32, maxon.Vector32, maxon.Vector64, maxon.Url]
ValueInfo: TypeAlias = Union[float, int, c4d.Vector, Sequence, maxon.DataType]

@dataclass
class MaterialColorInfo:

    data: Any

    def __post_init__(self):
        self.result: ColorInfo = None

        if isinstance(self.data, (str, c4d.Vector)):
            self.result = self.data
        elif isinstance(self.data, float):
            self.result = c4d.Vector(self.data)
        elif isinstance(self.data, Sequence):
            self.result = c4d.Vector(*self.data)
        
        if self.result is None:
            raise ValueError(f"Invalid color data: {self.data}")
        
    def convert(self):
        ...

def ToC4DColor(data: ColorInfo) -> c4d.Vector:
    if isinstance(data, c4d.Vector):
        result = data
    elif isinstance(data, (float, int)):
        result = c4d.Vector(data)
    elif isinstance(data, Sequence):
        result = c4d.Vector(*data)
    elif isinstance(data, str):
        try:
            result = c4d.Vector(float(data))
        except:
            result = c4d.Vector(0)
    elif isinstance(data, maxon.Color):
        result = c4d.Vector(data.r, data.g, data.b)
    elif isinstance(data, maxon.Vector):
        result = c4d.Vector(data.x, data.y, data.z)
    else:
        raise ValueError(f"Invalid color data: {data}")
    return result

def ToMaxonColor(data: ColorInfo) -> maxon.DataType:
    if isinstance(data, (maxon.Color, maxon.Vector)):
        result = data
    elif isinstance(data, (float, int)):
        result = maxon.Color(data, data, data)
    elif isinstance(data, Sequence):
        result = maxon.Color(data[0], data[1], data[2])
    elif isinstance(data, str):
        try:
            result = maxon.Color(float(data), float(data), float(data))
        except:
            result = maxon.Color(0, 0, 0)
    elif isinstance(data, c4d.Vector):
        result = maxon.Color(data.x, data.y, data.z)
    else:
        raise ValueError(f"Invalid color data: {data}")
    return result


