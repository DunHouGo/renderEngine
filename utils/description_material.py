# coding: utf-8
"""A new material maker module for generating materials for supported renderers.

This version avoids renderer-specific functions for easier use in custom plugins.
"""

import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
# from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import maxon
import c4d
from c4d import BaseMaterial
from c4d.documents import BaseDocument
C4D_VERSION: int = c4d.GetC4DVersion()

    
ID_OCTANE: int = 1029525 # Octane 
ID_REDSHIFT: int = 1036219 # Redshift
ID_ARNOLD: int = 1029988 # Arnold
ID_VRAY: int = 1053272
ID_CORONA: int = 1030480
ID_LOOKS: int = 1054755
ID_CENTILEO: int = 1036821

RS_NODESPACE: str = "com.redshift3d.redshift4c4d.class.nodespace"
RS_SHADER_PREFIX: str = "com.redshift3d.redshift4c4d.nodes.core."

# arnold
AR_NODESPACE: str = "com.autodesk.arnold.nodespace" 
AR_SHADER_PREFIX: str = "com.autodesk.arnold.shader."

STANDARD_NODESPACE: str = "net.maxon.nodespace.standard"
VR_NODESPACE: str = "com.chaos.class.vray_node_renderer_nodespace"

CL_NODESPACE: str = "com.centileo.class.nodespace"


# Texture pattern definitions
TEXTURE_PATTERNS = {
    'diffuse': r'[^a-zA-Z0-9^\s](diff|dif|diffuse|albedo|color|col|base.?color)',
    'specular': r'[^a-zA-Z0-9^\s](spec|specular|edgetint)',
    'metalness': r'[^a-zA-Z0-9^\s](metal|metallic|metalness)',
    'roughness': r'[^a-zA-Z0-9^\s](rough|roughness)',
    'glossiness': r'[^a-zA-Z0-9^\s](gloss|glossiness)',
    'ao': r'[^a-zA-Z0-9^\s](ao|ambient.?occlusion|occlusion|occ|mixed.?ao)',
    'alpha': r'[^a-zA-Z0-9^\s](alpha|opacity)',
    'bump': r'[^a-zA-Z0-9^\s](bump)',
    'normal': r'[^a-zA-Z0-9^\s](normal|nrm|normaldx|normalgl|nor|nor.?dx|nor.?gl|opengl|directx)',
    'emission': r'[^a-zA-Z0-9^\s](emission|emissive|emis)',
    'displacement': r'[^a-zA-Z0-9^\s](displacement|height|disp|depth|dis|displace)',
    'transmission': r'[^a-zA-Z0-9^\s](trans|transmission|translucency|sss)',
    'sheen': r'[^a-zA-Z0-9^\s](sheen)',
    'anisotropy': r'[^a-zA-Z0-9^\s](anisotropy|anis)'
}

PBR_PATTERN = '|'.join(f'({pattern})' for pattern in TEXTURE_PATTERNS.values())
RESOLUTION_PATTERN = re.compile(r'_(\d+)k')
IMAGE_EXTENSIONS = (
    '.png', '.jpg', '.jpeg', '.tga', '.bmp', '.exr', '.hdr', '.tif', '.tiff',
    '.iff', '.psd', '.tx', '.b3d', '.dds', '.dpx', '.psb', '.rla', '.rpf', '.pict'
)


def GetRenderEngine(document: BaseDocument) -> int :
    return document.GetActiveRenderData()[c4d.RDATA_RENDERENGINE]

@lru_cache(maxsize=1)
def _compile_regex(pattern: str) -> re.Pattern:
    """Compile and cache regex patterns"""
    return re.compile(pattern, re.IGNORECASE)

def IsImageFile(file_path: str) -> bool:
    """Check if a file is a supported image format."""
    return file_path.lower().endswith(IMAGE_EXTENSIONS) and os.path.isfile(file_path)

def GetPBRName(text: str) -> Optional[str]:
    """Extract the base name from a PBR texture filename."""
    if match := _compile_regex(PBR_PATTERN).search(text):
        return text[:match.start()]
    return None

def GetResolution(text: str) -> Optional[str]:
    """Extract resolution from filename (e.g., '_1k' returns '1')."""
    match = RESOLUTION_PATTERN.search(text)
    return match.group(1) if match else None

def validate_folder_path(folder: str) -> None:
    """Validate that a folder exists and is accessible."""
    if not os.path.isdir(folder):
        raise NotADirectoryError(f"Path is not a directory: {folder}")
    if not os.access(folder, os.R_OK):
        raise PermissionError(f"No read access to directory: {folder}")

def GetPBRImages(folder: str, base_name: str, resolution: Optional[int] = None) -> List[str]:
    """Get all PBR texture files matching the base name and optional resolution."""
    validate_folder_path(folder)
    
    matching_files = []
    for filename in os.listdir(folder):
        if not filename.startswith(base_name):
            continue
            
        file_path = os.path.join(folder, filename)
        if not IsImageFile(file_path):
            continue
            
        if resolution is not None:
            file_res = GetResolution(filename)
            if file_res is None or int(file_res) != resolution:
                continue
                
        matching_files.append(file_path)
        
    return matching_files

def GetPackageNames(folder: str) -> List[str]:
    """Get all unique PBR package names in a directory."""
    validate_folder_path(folder)
    return sorted({GetPBRName(f) for f in os.listdir(folder) if GetPBRName(f)})

def is_valid_path(path: str) -> bool:
    if path is None:
        path = ''
    return os.path.exists(str(path))

def iterate(node):
    while isinstance(node, c4d.BaseList2D):
        yield node

        for child in iterate(node.GetDown()):
            yield child

        node = node.GetNext()

@dataclass
class PackageData:
    """Represents a PBR texture package with all associated texture maps."""
    
    folder: str = field(default=None, repr=False)
    name: str = field(default=None)
    res: Optional[str] = field(default=None)
    
    def __post_init__(self) -> None:
        """Initialize and validate the package."""
        validate_folder_path(self.folder)
        self._init_texture_attributes()
        self.res = str(self.res) if self.res else None

    def _init_texture_attributes(self) -> None:
        """Initialize all texture attributes to None."""
        # for texture_type in TEXTURE_PATTERNS:
        #     setattr(self, texture_type, None)
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
        
    def __eq__(self, other: object) -> bool:
        """Compare packages based on diffuse texture."""
        if not isinstance(other, PackageData):
            return NotImplemented
        return self.diffuse == other.diffuse

    def __hash__(self) -> int:
        """Hash based on diffuse texture."""
        return hash(self.diffuse)

    @lru_cache(maxsize=128)
    def build(self, folder: Optional[str] = None, name: Optional[str] = None) -> 'PackageData':
        """Scan the folder and populate texture attributes."""
        folder = folder or self.folder
        name = name or self.name
        
        for texture_path in GetPBRImages(folder, name, int(self.res) if self.res else None):
            self._assign_texture(texture_path)
        
        return self

    def _assign_texture(self, texture_path: str) -> None:
        """Assign a texture path to the appropriate attribute."""
        for texture_type, pattern in TEXTURE_PATTERNS.items():
            if self._is_matching_texture(texture_path, pattern):
                setattr(self, texture_type, texture_path)
                break

    def _is_matching_texture(self, texture_path: str, pattern: str) -> bool:
        """Check if texture matches pattern and resolution."""
        filename = os.path.basename(texture_path)
        if not _compile_regex(pattern).search(filename):
            return False
        return self.res is None or self.res in filename

    @property
    def metalness_roughness_flow(self) -> bool:
        """Check if using metalness/roughness workflow."""
        return self.metalness is not None and self.roughness is not None

    @property
    def is_valid(self) -> bool:
        """Check if package contains at least one valid texture."""
        return any(getattr(self, attr) is not None for attr in TEXTURE_PATTERNS)

    def get_data(self) -> Dict[str, Optional[str]]:
        """Get dictionary of all texture data."""
        return {texture_type: getattr(self, texture_type) for texture_type in TEXTURE_PATTERNS}

    def get_valid_textures(self) -> Dict[str, str]:
        """Get dictionary of only present textures."""
        return {k: v for k, v in self.get_data().items() if v is not None}


CR_COLORSPACE_SRGB: int = 2
CR_COLORSPACE_LINEAR: int = 1

class CoronaSetup:

    def __init__(self, asset: PackageData):
        self.asset = asset
        self._material: c4d.BaseMaterial = None
        self.CreateMaterial()
        # self.doc = c4d.documents.GetActiveDocument() if doc is None else doc
        
    @property
    def Material(self) -> c4d.BaseMaterial:
        return self._material

    def _corona_bitmap_shader(self, img_path: str, name: str,  slot: int,  color_space: int = CR_COLORSPACE_LINEAR) -> c4d.BaseShader:
        shader = c4d.BaseList2D(1036473)
        shader[c4d.CORONA_BITMAP_FILENAME] = img_path
        shader.SetName(name)
        shader[c4d.CORONA_BITMAP_COLORPROFILE] = color_space
        self._material.InsertShader(shader)
        self._material[slot] = shader
        return shader

    def _corona_normal_shader(self, img_path: str, name: str, slot: int,  color_space: int = CR_COLORSPACE_LINEAR) -> c4d.BaseShader:
        #color_space: 2 sRGB 1 linear
        normal_shader = c4d.BaseList2D(1035405)
        self._material.InsertShader(normal_shader)
        self._material[slot] = normal_shader

        shader = c4d.BaseList2D(1036473)
        shader[c4d.CORONA_BITMAP_FILENAME] = img_path
        shader[c4d.CORONA_BITMAP_COLORPROFILE] = color_space
        shader.SetName(name)
        self._material.InsertShader(shader)
        normal_shader[c4d.CORONA_NORMALMAP_TEXTURE] = shader
        return normal_shader
    
    def CreateMaterial(self):
        
        self._material: c4d.BaseMaterial = c4d.BaseMaterial(1056306)
        # self._material.SetName(self.asset.aid)
        asset = self.asset
        if is_valid_path(self.asset.metalness):
            self._material[c4d.CORONA_PHYSICAL_MATERIAL_METALLIC_MODE_VALUE] = 0  # metal

        if is_valid_path(asset.diffuse):
            self._corona_bitmap_shader(asset.diffuse, "Albedo", c4d.CORONA_PHYSICAL_MATERIAL_BASE_COLOR_TEXTURE, CR_COLORSPACE_SRGB)
        if is_valid_path(asset.metalness):
            self._corona_bitmap_shader(asset.metalness, "Metalness", c4d.CORONA_PHYSICAL_MATERIAL_METALLIC_MODE_TEXTURE)
        if is_valid_path(asset.roughness):
            self._corona_bitmap_shader(asset.roughness, "Roughness", c4d.CORONA_PHYSICAL_MATERIAL_BASE_ROUGHNESS_TEXTURE)
            self._material[c4d.CORONA_PHYSICAL_MATERIAL_ROUGHNESS_MODE] = 0
        if is_valid_path(asset.normal):
            self._material[c4d.CORONA_PHYSICAL_MATERIAL_BASE_BUMPMAPPING_ENABLE] = 1
            self._corona_normal_shader(asset.normal, "Normal", c4d.CORONA_PHYSICAL_MATERIAL_BASE_BUMPMAPPING_TEXTURE)
        if is_valid_path(asset.displacement):
            self._material[c4d.CORONA_PHYSICAL_MATERIAL_DISPLACEMENT]=1
            self._material[c4d.CORONA_PHYSICAL_MATERIAL_DISPLACEMENT_MAX_LEVEL] = 0.1
            self._corona_bitmap_shader(asset.displacement, "Displacement", c4d.CORONA_PHYSICAL_MATERIAL_DISPLACEMENT_TEXTURE)
        if is_valid_path(asset.alpha):
            self._material[c4d.CORONA_PHYSICAL_MATERIAL_ALPHA] = True
            self._corona_bitmap_shader(asset.alpha, "Opacity", c4d.CORONA_PHYSICAL_MATERIAL_ALPHA_TEXTURE)
        if is_valid_path(asset.transmission):
            self._material[c4d.CORONA_PHYSICAL_MATERIAL_REFRACT]=1
            self._corona_bitmap_shader(asset.transmission, "Translucency", c4d.CORONA_PHYSICAL_MATERIAL_REFRACT_AMOUNT_TEXTURE,CR_COLORSPACE_SRGB)
        if is_valid_path(asset.sheen):
            self._material[c4d.CORONA_PHYSICAL_MATERIAL_SHEEN]=1
            self._corona_bitmap_shader(asset.sheen, "Sheen", c4d.CORONA_PHYSICAL_MATERIAL_SHEEN_COLOR_TEXTURE)
        if is_valid_path(asset.anisotropy):
            self._material[c4d.CORONA_PHYSICAL_MATERIAL_BASE_ANISOTROPY_VALUE]=.2
            self._corona_bitmap_shader(asset.anisotropy, "Anisotropy", c4d.CORONA_PHYSICAL_MATERIAL_BASE_ANISOTROPY_TEXTURE)
        if is_valid_path(asset.emission):
            self._material[c4d.CORONA_PHYSICAL_MATERIAL_EMISSION]=1
            self._corona_bitmap_shader(asset.emission, "Emission", c4d.CORONA_PHYSICAL_MATERIAL_EMISSION_TEXTURE)

MODE_FLOAT: int = 1
MODE_NORMAL: int = 0

class OctaneUniversal():

    def __init__(self, asset: PackageData):
        self.asset = asset
        self._material: c4d.BaseMaterial = None
        self.CreateMaterial()
        
    @property
    def Material(self) -> c4d.BaseMaterial:
        return self._material

    def CreateMaterial(self):
        asset = self.asset
        self._material = c4d.BaseMaterial(1029501)
        self._material[c4d.OCT_MATERIAL_TYPE] = 2516 # universal
        self._material[c4d.OCT_MAT_BRDF_MODEL] = 6 # ggx energy

        if is_valid_path(asset.diffuse):
            albedoNode = self.CreateImageTextureNode(asset.diffuse, "Albedo", MODE_NORMAL, 2.2)
            ccAlbedoNode = self.CreateCCNode(albedoNode)
            if is_valid_path(asset.ao):
                aoNode = self.CreateImageTextureNode(asset.ao, "AO")
                self.CreateMultiplyNode(ccAlbedoNode, aoNode, c4d.OCT_MATERIAL_DIFFUSE_LINK)
            else:
                self._material[c4d.OCT_MATERIAL_DIFFUSE_LINK] = ccAlbedoNode
        if is_valid_path(asset.roughness):
            roughnessNode = self.CreateImageTextureNode(asset.roughness, "Roughness")
            self._material[c4d.OCT_MATERIAL_ROUGHNESS_LINK] = roughnessNode
        if is_valid_path(asset.metalness):
            self.CreateImageTextureNode(asset.metalness, "Metalness", 1, 1, False, c4d.OCT_MAT_SPECULAR_MAP_LINK)

        if is_valid_path(asset.normal):  
            self.CreateImageTextureNode(asset.normal, "Normal", 0, 1, False, c4d.OCT_MATERIAL_NORMAL_LINK)

        if is_valid_path(asset.displacement):
            displacementNode = self.CreateDisplacementNode(c4d.OCT_MATERIAL_DISPLACEMENT_LINK)
            if displacementNode:
                displacementSlotName = c4d.DISPLACEMENT_TEXTURE
                displacementNode[displacementSlotName] = self.CreateImageTextureNode(asset.displacement, "Displacement")
                displacementNode[c4d.DISPLACEMENT_LEVELOFDETAIL] = 11

        if is_valid_path(asset.alpha):
            self.CreateImageTextureNode(asset.alpha, "Opacity", 1, 1, False, c4d.OCT_MATERIAL_OPACITY_LINK)

        if is_valid_path(asset.sheen):
            self.CreateImageTextureNode(asset.sheen, "Sheen", 1, 1, False, c4d.OCT_MAT_SHEEN_MAP_FLOAT)
            
        if is_valid_path(asset.anisotropy):
            self.CreateImageTextureNode(asset.anisotropy, "Anisotropy", 1, 1, False, c4d.OCT_MAT_ANISOTROPY_ROTATION_LINK)

        if is_valid_path(asset.transmission):
            self.CreateImageTextureNode(asset.transmission, "Translucency", 0, 2.2, False, c4d.OCT_MATERIAL_TRANSMISSION_LINK)
            self._material[c4d.UNIVMAT_TRANSMISSION_TYPE] = 1
            
        if is_valid_path(asset.emission):
            self.CreateEmission(asset.emission, "Emission")

    def CreateImageTextureNode(self, filepath, nodeName, textureMode = MODE_FLOAT, gamma = 1, invert = False, parentNode = None):
        imageTextureNode = c4d.BaseList2D(1029508)
        imageTextureNode[c4d.IMAGETEXTURE_FILE] = filepath
        imageTextureNode[c4d.IMAGETEXTURE_INVERT] = invert
        imageTextureNode[c4d.IMAGETEXTURE_GAMMA] = gamma
        imageTextureNode[c4d.IMAGETEXTURE_MODE] = textureMode # 1 = Float and 0 is Normal (Color)
        imageTextureNode.SetName(nodeName)

        if parentNode:
            self._material[parentNode] = imageTextureNode
        self._material.InsertShader(imageTextureNode)
    
        return imageTextureNode

    def CreateTransformNode(self):
        try:
            self.transformNode = c4d.BaseList2D(1030961)
            self._material.InsertShader(self.transformNode)
            self.connectToTransformNode = True
        except Exception as e:
            raise RuntimeError(e)

    def CreateMultiplyNode(self, imageTexture1, imageTexture2, parentNode = None):
        try:
            multiplyNode = c4d.BaseList2D(1029516)
            multiplyNode[c4d.MULTIPLY_TEXTURE1] = imageTexture1
            multiplyNode[c4d.MULTIPLY_TEXTURE2] = imageTexture2
            
            if parentNode:
                self._material[parentNode] = multiplyNode
            self._material.InsertShader(multiplyNode)
            
            return multiplyNode
        except Exception as e:
            raise RuntimeError(e)

    def CreateCCNode(self, imageTexture):
        try:
            colorCorrectionNode = c4d.BaseList2D(1029512)
            colorCorrectionNode[c4d.COLORCOR_TEXTURE_LNK] = imageTexture
            self._material.InsertShader(colorCorrectionNode)
            return colorCorrectionNode
        except Exception as e:
            raise RuntimeError(e)

    def CreateDisplacementNode(self, parentNode = None):
        try:
            displacementNode = c4d.BaseList2D(1031901)
            displacementNode[c4d.DISPLACEMENT_AMOUNT] = 1
            displacementNode[c4d.DISPLACEMENT_MID] = 0.5

            if parentNode:
                self._material[parentNode] = displacementNode
            self._material.InsertShader(displacementNode)

            return displacementNode
        except Exception as e:
            raise RuntimeError(e)

    def CreateEmission(self, filepath, nodeName):
        enode = c4d.BaseList2D(1029642)
        enode[c4d.OCT_MATERIAL_EMISSION] = enode
        enode[c4d.TEXEMISSION_POWER] = 1.0
        self._material.InsertShader(enode)
        
        imageTextureNode = c4d.BaseList2D(1029508)
        imageTextureNode[c4d.IMAGETEXTURE_FILE] = filepath
        imageTextureNode[c4d.IMAGETEXTURE_GAMMA] = 2.2
        imageTextureNode[c4d.IMAGETEXTURE_MODE] = 0 # 1 = Float and 0 is Normal (Color)
        imageTextureNode.SetName(nodeName)
        enode[c4d.TEXEMISSION_EFFIC_OR_TEX] = imageTextureNode
        self._material.InsertShader(imageTextureNode)
        return enode


class OctaneStandard():
    
    STANDARD_SURFACE: int = 1058763
    IMAGE_TEXTURE: int = 1029508
    TRANSFORM: int = 1030961

    def __init__(self, asset: PackageData):
        self.asset = asset
        self._material: c4d.BaseMaterial = None
        self.CreateMaterial()
        
    @property
    def Material(self) -> c4d.BaseMaterial:
        return self._material

    def CreateMaterial(self):
        asset = self.asset
        self._material = c4d.BaseMaterial(self.STANDARD_SURFACE)

        if is_valid_path(asset.diffuse):
            albedoNode = self.CreateImageTextureNode(asset.diffuse, "Albedo", MODE_NORMAL, 2.2)
            ccAlbedoNode = self.CreateCCNode(albedoNode)
            if is_valid_path(asset.ao):
                aoNode = self.CreateImageTextureNode(asset.ao, "AO")
                print(ccAlbedoNode, aoNode)
                self.CreateMultiplyNode(ccAlbedoNode, aoNode, c4d.STDMAT_BASELAYER_COLOR_LINK)
            else:
                self._material[c4d.STDMAT_BASELAYER_COLOR_LINK] = ccAlbedoNode
                
        if is_valid_path(asset.roughness):
            roughnessNode = self.CreateImageTextureNode(asset.roughness, "Roughness")
            self._material[c4d.STDMAT_SPECULARLAYER_ROUGH_LINK] = roughnessNode
        if is_valid_path(asset.metalness):
            self.CreateImageTextureNode(asset.metalness, "Metalness", 1, 1, False, c4d.STDMAT_BASELAYER_METALNESS_LINK)

        if is_valid_path(asset.normal):  
            self.CreateImageTextureNode(asset.normal, "Normal", 0, 1, False, c4d.STDMAT_NORMAL_LINK)

        if is_valid_path(asset.displacement):
            displacementNode = self.CreateDisplacementNode(c4d.STDMAT_DISPLACEMENT_LINK)
            if displacementNode:
                displacementSlotName = c4d.DISPLACEMENT_TEXTURE
                displacementNode[displacementSlotName] = self.CreateImageTextureNode(asset.displacement, "Displacement")
                displacementNode[c4d.DISPLACEMENT_LEVELOFDETAIL] = 11

        if is_valid_path(asset.alpha):
            self.CreateImageTextureNode(asset.alpha, "Opacity", 1, 1, False, c4d.STDMAT_OPACITY_LINK)

        if is_valid_path(asset.sheen):
            self._material[c4d.STDMAT_SHEEN_LINK] = 1
            self.CreateImageTextureNode(asset.sheen, "Sheen", 1, 1, False, c4d.STDMAT_SHEEN_COLOR_LINK)
            
        if is_valid_path(asset.anisotropy):
            self.CreateImageTextureNode(asset.anisotropy, "Anisotropy", 1, 1, False, c4d.STDMAT_SPECULARLAYER_ANISO_LINK)

        if is_valid_path(asset.transmission):
            self.CreateImageTextureNode(asset.transmission, "Translucency", 0, 2.2, False, c4d.STDMAT_TRANSMLAYER_COLOR_LINK)
            self._material[c4d.STDMAT_TRANSMLAYER_WEIGHT_FLOAT] = 1
            
        if is_valid_path(asset.emission):
            self._material[c4d.STDMAT_EMISSION_LINK] = 1
            self.CreateEmission(asset.emission, "Emission")
            
        self.AddUniTransform()

    def GetImages(self) -> list[c4d.BaseList2D] :
        """
        Get all nodes of the material in a list.

        Returns:
            list[c4d.BaseList2D]: A List of all find nodes

        """
        result: list = []
        start_shader = self._material.GetFirstShader()
        if not start_shader:
            return
        
        for obj in iterate(start_shader):
            if obj.CheckType(self.IMAGE_TEXTURE):
                result.append(obj)

        return result

    def AddUniTransform(self):
        node = c4d.BaseList2D(self.TRANSFORM)
        self._material.InsertShader(node)
        for img in self.GetImages():
            img[c4d.IMAGETEXTURE_TRANSFORM_LINK] = node

    def CreateImageTextureNode(self, filepath, nodeName, textureMode = MODE_FLOAT, gamma = 1, invert = False, parentNode = None):
        imageTextureNode = c4d.BaseList2D(self.IMAGE_TEXTURE)
        imageTextureNode[c4d.IMAGETEXTURE_FILE] = filepath
        imageTextureNode[c4d.IMAGETEXTURE_INVERT] = invert
        imageTextureNode[c4d.IMAGETEXTURE_GAMMA] = gamma
        imageTextureNode[c4d.IMAGETEXTURE_MODE] = textureMode # 1 = Float and 0 is Normal (Color)
        imageTextureNode.SetName(nodeName)

        if parentNode:
            self._material[parentNode] = imageTextureNode
        self._material.InsertShader(imageTextureNode)
    
        return imageTextureNode

    def CreateTransformNode(self):
        try:
            self.transformNode = c4d.BaseList2D(1030961)
            self._material.InsertShader(self.transformNode)
            self.connectToTransformNode = True
        except Exception as e:
            raise RuntimeError(e)

    def CreateMultiplyNode(self, imageTexture1, imageTexture2, parentNode = None):
        try:
            multiplyNode = c4d.BaseList2D(1029516)
            multiplyNode[c4d.MULTIPLY_TEXTURE1] = imageTexture1
            multiplyNode[c4d.MULTIPLY_TEXTURE2] = imageTexture2
            
            if parentNode:
                self._material[parentNode] = multiplyNode
            self._material.InsertShader(multiplyNode)
            
            return multiplyNode
        except Exception as e:
            raise RuntimeError(e)

    def CreateCCNode(self, imageTexture):
        try:
            colorCorrectionNode = c4d.BaseList2D(1029512)
            colorCorrectionNode[c4d.COLORCOR_TEXTURE_LNK] = imageTexture
            self._material.InsertShader(colorCorrectionNode)
            return colorCorrectionNode
        except Exception as e:
            raise RuntimeError(e)

    def CreateDisplacementNode(self, parentNode = None):
        try:
            displacementNode = c4d.BaseList2D(1031901)
            displacementNode[c4d.DISPLACEMENT_AMOUNT] = 1
            displacementNode[c4d.DISPLACEMENT_MID] = 0.5

            if parentNode:
                self._material[parentNode] = displacementNode
            self._material.InsertShader(displacementNode)

            return displacementNode
        except Exception as e:
            raise RuntimeError(e)

    def CreateEmission(self, filepath, nodeName):
        enode = c4d.BaseList2D(1029642)
        enode[c4d.STDMAT_EMISSION_EMISSION] = enode
        enode[c4d.TEXEMISSION_POWER] = 1.0
        self._material.InsertShader(enode)
        
        imageTextureNode = c4d.BaseList2D(1029508)
        imageTextureNode[c4d.IMAGETEXTURE_FILE] = filepath
        imageTextureNode[c4d.IMAGETEXTURE_GAMMA] = 2.2
        imageTextureNode[c4d.IMAGETEXTURE_MODE] = 0 # 1 = Float and 0 is Normal (Color)
        imageTextureNode.SetName(nodeName)
        enode[c4d.TEXEMISSION_EFFIC_OR_TEX] = imageTextureNode
        self._material.InsertShader(imageTextureNode)
        return enode


class MaterialCreator:
    
    def __init__(self, folder: str, name: str, res: str=None):
        """
        A Custom NodeHelper for Node Material. Need a material to initalize the instance.

        Args:
            material (c4d.BaseMaterial): the BaseMaterial instance from the C4D document.

        """
        self.folder: str = folder
        self.name: str = name
        self.res: str = res
        
        self.material: c4d.BaseMaterial = c4d.BaseMaterial(c4d.Mmaterial)
        self._data = PackageData(self.folder, self.name, self.res)
        
        self._support_renderers: list = [
            "com.autodesk.arnold.nodespace",
            "com.redshift3d.redshift4c4d.class.nodespace",
            "com.chaos.class.vray_node_renderer_nodespace",
            "com.centileo.class.nodespace"
        ]

        if self.material:

            self.nodeMaterial: c4d.NodeMaterial = self.material.GetNodeMaterialReference()
            for nid in self._support_renderers:
                if not self.nodeMaterial.HasSpace(nid):
                    continue
            # node
            self.nodespaceId: maxon.Id = c4d.GetActiveNodeSpaceId()
            if self.nodespaceId is None:
                raise ValueError("Cannot retrieve the NodeSpace.")
            
            self.nimbusRef: maxon.NimbusBaseInterface = self.material.GetNimbusRef(self.nodespaceId)
            if self.nimbusRef is None:
                raise ValueError("Cannot retrieve the nimbus reference for that NodeSpace.")
            
            self.graph: maxon.GraphModelInterface = self.nodeMaterial.GetGraph(self.nodespaceId)
            if self.graph.IsNullValue():
                raise ValueError("Cannot retrieve the graph of this nimbus NodeSpace.")
            

            if C4D_VERSION >= 2025000:
                self.root: maxon.GraphNode = self.graph.GetViewRoot()
            else:
                self.root: maxon.GraphNode = self.graph.GetRoot()

    def AddShader(self, nodeId: Union[str, maxon.Id], name: str=None) -> maxon.GraphNode:
        """
        Adds a new shader to the graph.

        Args:
            nodeId (Union[str, maxon.Id]): shader id

        Returns:
            maxon.GraphNode: the shader we added.
        """
        node: maxon.GraphNode = self.graph.AddChild(childId=maxon.Id(), nodeId=nodeId, args=maxon.DataDictionary())
        if name: node.SetValue(maxon.NODE.BASE.NAME, self._ConvertData(str(name)))
        return node
    
    def _ConvertData(self, data: Any) -> maxon.data:
        """
        Convert the data to maxon data type for safely.

        Args:
            data (Any): the data to convert

        Returns:
            maxon.data: the converted data
        """
        
        return maxon.MaxonConvert(data, maxon.CONVERSIONMODE.TOMAXON)

    def GetPort(self, shader: maxon.GraphNode, port_id :str = None) -> Union[maxon.GraphNode,bool]:
        """
        Get a port from a Shader node.if port id is None,try to find out port.

        Args:
            shader (maxon.GraphNode): the host shader
            port_id (str, optional): the port id, fill none try to get the output port.

        Returns:
            Union[maxon.GraphNode,bool]: the port we get.
        """
        port: maxon.GraphNode = shader.GetInputs().FindChild(port_id)
        if port.IsNullValue():
            port = shader.GetOutputs().FindChild(port_id)
            if port.IsNullValue():
                return False
        return port

    def GetOutput(self) -> maxon.GraphNode:
        """
        Returns the end node.

        Returns:
            maxon.GraphNode: the end node of this graph
        """
        # Retrieve the end node of this graph
        endNodePath = self.nimbusRef.GetPath(maxon.NIMBUS_PATH.MATERIALENDNODE)
        endNode = self.graph.GetNode(endNodePath)
        return endNode

    def GetImageNodeID(self, include_portData: bool = False) -> Union[maxon.Id, tuple]:
        """
        Returns the image node id (and it's port data).
        Need to convert the NodePath to a string, this is a bug that is going to be fixed in 2024.2

        Returns:
            maxon.GraphNode: the image node id of this graph

        portData 
        .. code-block:: python
            portData = [
                outColorPortId = portData[0],      # The result port.
                inTexturePortId = portData[1],     # The URL of the input image.
                inStartFramePortId = portData[2],  # The index of the starting frame.
                inEndFramePortId = portData[3]     # The index of the ending frame.
                ]
        """
        # Retrieve the nodespace id from the graph
        spaceContext = self.root.GetValue(maxon.nodes.NODESPACE.NodeSpaceContext)
        nodeSpaceId = spaceContext.Get(maxon.nodes.NODESPACE.SPACEID)

        # Retrieve the nodespace data, and its default picture node with the associated port Id
        if c4d.GetC4DVersion() < 2024200:
            # --- Temporary add NodeSpaceHelpersInterface.GetNodeSpaceData() 
            # This is going to be added in 2024.2 as maxon.NodeSpaceHelpersInterface.GetNodeSpaceData() --------------------------
            @maxon.interface.MAXON_INTERFACE_NONVIRTUAL(maxon.consts.MAXON_REFERENCE_STATIC, "net.maxon.nodes.interface.nodespacehelpers")
            class NodeSpaceHelpersInterface:
                
                @staticmethod
                @maxon.interface.MAXON_STATICMETHOD("net.maxon.nodes.interface.nodespacehelpers.GetNodeSpaceData")
                def GetNodeSpaceData(spaceId):
                    pass
            # --- End of fix -----------------------------------------------------------------------------------
            
            spaceData = NodeSpaceHelpersInterface.GetNodeSpaceData(nodeSpaceId)

        else:
            spaceData = maxon.NodeSpaceHelpersInterface.GetNodeSpaceData(nodeSpaceId)

        assetId = spaceData.Get(maxon.nodes.NODESPACE.IMAGENODEASSETID)
        
        if include_portData:
            portData = spaceData.Get(maxon.nodes.NODESPACE.IMAGENODEPORTS)
            return (assetId, portData)
        return assetId

    def SetPortData(self, port: maxon.GraphNode, value) -> bool:
        """
        Sets the value to the given port.

        Args:
            node (maxon.GraphNode): the node
            paramId (Union[maxon.Id,str], optional): the port id. Defaults to None.
            value (_type_, optional): the value to set. Defaults to None.

        Returns:
            bool: True if the value has been changed.
        """


        return port.SetValue("net.maxon.description.data.base.defaultvalue", self._ConvertData(value))

    def AddImageNode(self, url: str, name: str=None, color_space: str = "raw"):
        image_node_id, (outColorPortId, inTexturePortId, _, _) = self.GetImageNodeID(True)
        node = self.AddShader(image_node_id, name)
        outport = self.GetPort(node, outColorPortId)
        texport = self.GetPort(node, inTexturePortId)

    def RSAddTexture(self, shadername :str = 'Texture', filepath: str = None, raw: bool = True, gamma: int = 1, target_port: maxon.GraphNode = None) -> maxon.GraphNode :
        """
        Adds a new texture shader to the graph.
        """
        if self.graph is None:
            return None
        
        nodeId = "texturesampler"
        shader: maxon.GraphNode = self.graph.AddChild("", "com.redshift3d.redshift4c4d.nodes.core." + nodeId, maxon.DataDictionary())
        if shadername: shader.SetValue(maxon.NODE.BASE.NAME, maxon.MaxonConvert(str(shadername), maxon.CONVERSIONMODE.TOMAXON))
        
        texPort: maxon.GraphNode = self.GetPort(shader,"com.redshift3d.redshift4c4d.nodes.core.texturesampler.tex0")
        texFilenamePort: maxon.GraphNode = texPort.FindChild('path')
        colorspacePort: maxon.GraphNode = texPort.FindChild("colorspace")
        gammaPort: maxon.GraphNode = self.GetPort(shader,"com.redshift3d.redshift4c4d.nodes.core.texturesampler.tex0_gamma")
        self.SetPortData(gammaPort, gamma)
        # tex path
        if filepath is not None:
            self.SetPortData(texFilenamePort, filepath)
        
        # color space
        if raw:
            self.SetPortData(colorspacePort, "RS_INPUT_COLORSPACE_RAW")
        else:
            self.SetPortData(colorspacePort, "RS_INPUT_COLORSPACE_SRGB")
        
        # target connect
        if target_port:
            if isinstance(target_port, maxon.GraphNode):
                outPort: maxon.GraphNode = self.GetPort(shader,'com.redshift3d.redshift4c4d.nodes.core.texturesampler.outcolor')
                try:
                    outPort.Connect(target_port)
                except:
                    pass

        return shader

    def ArnoldMaterial(self):
        asset = self._data
        # add graph
        self.nodeMaterial.CreateDefaultGraph(AR_NODESPACE)
        standard_surface = self.AddShader("com.autodesk.arnold.shader.standard_surface")
        surface_out = self.GetPort(standard_surface,'output')
        end_node = self.GetOutput()
        end_shader_in = self.GetPort(end_node,'shader')
        surface_out.Connect(end_shader_in)
        image_node_id, (outColorPortId, inTexturePortId, _, _) = self.GetImageNodeID(True)
        
        # get ports
        albedoPort = self.GetPort(standard_surface,'base_color')
        # specularPort = self.GetPort(standard_surface,'specular_color')
        roughnessPort = self.GetPort(standard_surface,'specular_roughness')
        metalnessPort = self.GetPort(standard_surface,'metalness')
        opacityPort = self.GetPort(standard_surface,'opacity')
        reflectionPort = self.GetPort(standard_surface,'selfansmission_color')
        # normalPort = self.GetPort(standard_surface,'normal')
        if is_valid_path(asset.diffuse):
            node = self.AddShader(image_node_id, asset.diffuse)

    def Modify(self, doc: BaseDocument):
        self._data.build()
        if not self._data.is_valid():
            raise RuntimeError("No valid data in the package.")
        
        doc = doc if doc else c4d.documents.GetActiveDocument()
        with self.graph.BeginTransaction() as transaction:

            if GetRenderEngine(doc) == ID_ARNOLD:
                ...
                
                
                
                
                
            transaction.Commit()


@dataclass
class DescriptionMaterialMaker:

    folder: str = field(repr=False)
    name: str
    res: str = field(default=None)
    triplaner: bool = False

    def __post_init__(self) -> None:
        self._data = PackageData(self.folder, self.name, self.res)

    def GetRenderEngine(self, document: BaseDocument) -> int :
        return document.GetActiveRenderData()[c4d.RDATA_RENDERENGINE]

    def ModifyMaterial(self, material: c4d.BaseMaterial, data: dict, nodespace: str) -> None:
        """
        Modify an existing material with the given data and nodespace.
        """
        graph: maxon.NodesGraphModelRef = maxon.GraphDescription.GetGraph(material, nodespace)
        maxon.GraphDescription.ApplyDescription(graph, data)
        material.Message(c4d.MSG_UPDATE)

    # todo : 2024.2之前没有description，需要支持node api
    def MakeMaterial(self, doc: BaseDocument) -> BaseMaterial:
        self._data.build()
        doc = doc if doc else c4d.documents.GetActiveDocument()
        if GetRenderEngine(doc) == ID_ARNOLD:
            if C4D_VERSION >= 2024200:
                material = c4d.BaseMaterial(c4d.Mmaterial)
                self.ModifyMaterial(material, self.ArnoldDescription(), AR_NODESPACE)
            else:
                raise NotImplementedError('Graph Description is not implemented before R2024.2, use old MaterialMaker version instead')
        elif GetRenderEngine(doc) == ID_REDSHIFT:
            if C4D_VERSION >= 2024200:
                material = c4d.BaseMaterial(c4d.Mmaterial)
                self.ModifyMaterial(material, self.RedshiftDescription(), RS_NODESPACE)
            else:
                raise NotImplementedError('Graph Description is not implemented before R2024.2, use old MaterialMaker version instead')
        elif GetRenderEngine(doc) == ID_VRAY:
            if C4D_VERSION >= 2024200:
                material = c4d.BaseMaterial(c4d.Mmaterial)
                self.ModifyMaterial(material, self.VRayDescription(), VR_NODESPACE)
            else:
                raise NotImplementedError('Graph Description is not implemented before R2024.2, use old MaterialMaker version instead')
        elif GetRenderEngine(doc) == ID_CORONA:
            material = CoronaSetup(self._data).Material
        elif GetRenderEngine(doc) == ID_OCTANE:
            material = OctaneStandard(self._data).Material
            
        # print(material)
        material.SetName(f"{self.name}_{self.res}")
        material.Update(True, True)         
        doc.InsertMaterial(material)
        doc.SetActiveMaterial(material)

    
    def ArnoldDescription(self) -> dict[str, str]:
        asset = self._data
        data = {
            "$type": "#com.autodesk.arnold.material",
            "#<shader":
                {
                    "$type": "#com.autodesk.arnold.shader.standard_surface",
                }
        }
        
        # asset_uid: maxon.Uuid = maxon.Uuid(self.aid)[:8]
        # diff_image_uid: str = f"diff_{self.aid}@{asset_uid}"
        # rough_image_uid: str = f"rough_{self.aid}@{asset_uid}"
        # metal_image_uid: str = f"metal_{self.aid}@{asset_uid}"
        
        material_description = data["#<shader"]

        if is_valid_path(asset.diffuse):
            material_description["#<base_color"] = {
                "$type": "#com.autodesk.arnold.shader.color_correct",
                "#<input": 
                    {
                        "$type": "#com.autodesk.arnold.shader.image",
                        # "$id": diff_image_uid,
                        "#<filename": asset.diffuse, 
                        "#<multiply": {"$type": "#com.autodesk.arnold.shader.image", "#<filename": asset.ao} if is_valid_path(asset.ao) else maxon.Vector(1, 1, 1)
                    }}

        if is_valid_path(asset.metalness):
            material_description["#<metalness"] = {
                "$type": "#com.autodesk.arnold.shader.image",
                "#<filename": asset.metalness}
                # "$id": metal_image_uid}
            
        if is_valid_path(asset.roughness):
            material_description["#<specular_roughness"] = {
                "$type": "#com.autodesk.arnold.shader.image",
                "#<filename": asset.roughness}
                # "$id": rough_image_uid}
            
        if is_valid_path(asset.alpha):
            material_description["#<opacity"] = {
                "$type": "#com.autodesk.arnold.shader.image",
                "#<filename": asset.alpha}
            
        if is_valid_path(asset.transmission):
            material_description["#<transmission_color"] = {
                "$type": "#com.autodesk.arnold.shader.image",
                "#<filename": asset.transmission}
            
        if is_valid_path(asset.emission):
            material_description["#<emission_color"] = {
                "$type": "#com.autodesk.arnold.shader.image",
                "#<filename": asset.emission}
            
        if is_valid_path(asset.sheen):
            material_description["#<sheen_color"] = {
                "$type": "#com.autodesk.arnold.shader.image",
                "#<filename": asset.sheen}
            
        if is_valid_path(asset.specular):
            material_description["#<specular_color"] = {
                "$type": "#com.autodesk.arnold.shader.image",
                "#<filename": asset.specular} 
            
        if is_valid_path(asset.anisotropy):
            material_description["#<specular_anisotropy"] = {
                "$type": "#com.autodesk.arnold.shader.image",
                "#<filename": asset.anisotropy} 
            
        if is_valid_path(asset.normal):
            material_description["#<normal"] = {
                "$type": "#com.autodesk.arnold.shader.normal_map",
                "#<input": 
                    {
                        "$type": "#com.autodesk.arnold.shader.image",
                        "#<filename": asset.normal
                    }}

        if is_valid_path(asset.displacement):
            data["#<displacement"] = {
                "$type": "#com.autodesk.arnold.shader.displacement",
                "#<normal_displacement_input": 
                    {
                        "$type": "#com.autodesk.arnold.shader.image",
                        "#<filename": asset.displacement
                    }}

        return data

    def RedshiftDescription(self) -> dict[str, str]:
        asset = self._data
        data = {
            "$type": "#~.output",
            "#~.surface":
                {
                    "$type": "#~.standardmaterial",
                }
        }
        
        material_description = data["#~.surface"]

        if is_valid_path(asset.diffuse):
            material_description["#~.base_color"] = {
                "$type": "#~.rscolorcorrection",
                "#~.input": 
                    {
                        "$type": "#~.texturesampler",
                        "#~.tex0/path": asset.diffuse,
                        "#~.color_multiplier":  {"$type": "#~.texturesampler", "#~.tex0/path":  asset.ao}  if is_valid_path(asset.ao) else maxon.Vector(1, 1, 1)
                    }}
        
        if is_valid_path(asset.metalness):
            material_description["#~.metalness"] = {
                "$type": "#~.texturesampler",
                "#~.tex0/path": asset.metalness}
            
        if is_valid_path(asset.roughness):
            material_description["#~.refl_roughness"] = {
                "$type": "#~.texturesampler",
                "#~.tex0/path": asset.roughness}
            
        if is_valid_path(asset.alpha):
            material_description["#~.opacity_color"] = {
                "$type": "#~.texturesampler",
                "#~.tex0/path": asset.alpha}
            
        if is_valid_path(asset.transmission):
            material_description["#~.refr_color"] = {
                "$type": "#~.texturesampler",
                "#~.tex0/path": asset.transmission}
            
        if is_valid_path(asset.emission):
            material_description["#~.emission_color"] = {
                "$type": "#~.texturesampler",
                "#~.tex0/path": asset.emission}
            
        if is_valid_path(asset.sheen):
            material_description["#~.sheen_color"] = {
                "$type": "#~.texturesampler",
                "#~.tex0/path": asset.sheen}
            
        if is_valid_path(asset.specular):
            material_description["#~.refl_color"] = {
                "$type": "#~.texturesampler",
                "#~.tex0/path": asset.specular} 
            
        if is_valid_path(asset.anisotropy):
            material_description["#~.refl_aniso"] = {
                "$type": "#~.texturesampler",
                "#~.tex0/path": asset.anisotropy} 
            
        if is_valid_path(asset.normal):
            material_description["#~.bump_input"] = {
                "$type": "#~.bumpmap",
                "#~.inputtype": 1,
                "#~.input": 
                    {
                        "$type": "#~.texturesampler",
                        "#~.tex0/path": asset.normal
                    }}

        if is_valid_path(asset.displacement):
            data["#~.displacement"] = {
                "$type": "#~displacement",
                "#~.texmap": 
                    {
                        "$type": "#~.texturesampler",
                        "#~.tex0/path": asset.displacement
                    }}

        return data

    def VRayDescription(self) -> dict[str, str]:
        asset = self._data
        data = {
            "$type": "#~.mtlsinglebrdf",
            "#~.brdf":
                {
                    "$type": "#~.brdfvraymtl",
                }
        }
        
        material_description = data["#~.brdf"]

        if is_valid_path(asset.diffuse):
            material_description["#~.diffuse"] = {
                "$type": "#~.colorcorrection",
                "#~.texture_map": 
                    {
                        "$type": "#~.texbitmap",
                        "#~.file": asset.diffuse,
                        "#~.color_mult": {"$type": "#~.texbitmap", "#~.file": asset.ao} if is_valid_path(asset.ao) else maxon.Vector(1, 1, 1)
                    }}
        
        if is_valid_path(asset.metalness):
            material_description["#~.metalness"] = {
                "$type": "#~.texbitmap",
                "#~.file": asset.metalness}
            
        if is_valid_path(asset.roughness):
            material_description["#~.reflect_glossiness"] = {
                "$type": "#~.texbitmap",
                "#~.file": asset.roughness}
            material_description["#~.option_use_roughness"] = True
            
        if is_valid_path(asset.alpha):
            material_description["#~.opacity_color"] = {
                "$type": "#~.texbitmap",
                "#~.file": asset.alpha}
            
        if is_valid_path(asset.transmission):
            material_description["#~.refract"] = {
                "$type": "#~.texbitmap",
                "#~.file": asset.transmission}
            
        if is_valid_path(asset.emission):
            material_description["#~.self_illumination"] = {
                "$type": "#~.texbitmap",
                "#~.file": asset.emission}
            
        if is_valid_path(asset.sheen):
            material_description["#~.sheen_color"] = {
                "$type": "#~.texbitmap",
                "#~.file": asset.sheen}
            
        if is_valid_path(asset.specular):
            material_description["#~.reflect"] = {
                "$type": "#~.texbitmap",
                "#~.file": asset.specular} 
            
        if is_valid_path(asset.anisotropy):
            material_description["#~.anisotropy"] = {
                "$type": "#~.texbitmap",
                "#~.file": asset.anisotropy} 
            
        if is_valid_path(asset.normal):
            material_description["#~.bump_map"] = {
                "$type": "#~.texnormalbump",
                "#~.map_type": 1,
                "#~.bump_tex_color": 
                    {
                        "$type": "#~.texbitmap",
                        "#~.file": asset.normal
                    }}

        # if os.path.exists(asset.displacement):
        #     data["#~.displacement"] = {
        #         "$type": "#~displacement",
        #         "#~.texmap": 
        #             {
        #                 "$type": "#~.texbitmap",
        #                 "#~.file": asset.displacement
        #             }}

        return data


if __name__ == '__main__':
    from pprint import pp
    test_dir = r"C:\Users\DunHou\Documents\PolyHaven Assets\aerial_beach_01\textures"
    # package = PackageData(folder=test_dir, name='aerial_beach_01', res='2')
    # package.build()
    # print(package.diffuse)
    # print(package.metalness)
    # print(package.ao)
    
    # valid_textures = package.get_data()
    # pp(valid_textures)
    
    mm = DescriptionMaterialMaker(folder=test_dir, name='aerial_beach_01', res='2')
    mm.MakeMaterial(c4d.documents.GetActiveDocument())
    c4d.EventAdd()
    
    