import c4d
import maxon
import os
from typing import Optional, Any
from dataclasses import dataclass, field
from Renderer.constants.common_id import ID_REDSHIFT, ID_ARNOLD, ID_OCTANE, ID_VRAY, ID_CORONA, ID_CENTILEO
from Renderer import EasyTransaction
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

from .pbr_helper import (
    PBRPackage,
    IsImageFile,
    GetPBRName,
    InPackage,
    GetPBRImages,
    GetPackageNames,
    pbr_from_file,
    pbr_from_folder,
    IMAGE_EXTENSIONS
)

C4D_VERSION: int = c4d.GetC4DVersion()

RS_NODESPACE: str = "com.redshift3d.redshift4c4d.class.nodespace"
AR_NODESPACE: str = "com.autodesk.arnold.nodespace" 
VR_NODESPACE: str = "com.chaos.class.vray_node_renderer_nodespace"

def GetRenderEngine(document: c4d.documents.BaseDocument = None) -> int:
    """Get the current render engine ID."""
    document = document or c4d.documents.GetActiveDocument()
    return document.GetActiveRenderData()[c4d.RDATA_RENDERENGINE]

def is_valid_path(path: Any) -> bool:
    """Check if a path exists."""
    if path is None:
        return False
    return os.path.exists(str(path))

def _ApplyPBRDescription(material: c4d.BaseMaterial, nodespace: str, data: dict, doc: c4d.documents.BaseDocument) -> bool:
    """Internal helper to apply graph description to a material."""
    if C4D_VERSION < 2024200:
        return False
    
    graph = maxon.GraphDescription.GetGraph(material, nodespace)
    if graph.IsNullValue():
        return False
        
    maxon.GraphDescription.ApplyDescription(graph, data)
    material.Message(c4d.MSG_UPDATE)
    
    if material.GetDocument() is None:
        doc.InsertMaterial(material)
    
    doc.SetActiveMaterial(material)
    material.Update(True, True)
    return True

# =========================================================
# Description Generators
# =========================================================

def GetArnoldDescription(asset: PBRPackage) -> dict:
    """Returns Arnold Graph Description dictionary for a PBRPackage."""
    data = {
        "$type": "#com.autodesk.arnold.material",
        "#<shader": { "$type": "#com.autodesk.arnold.shader.standard_surface" }
    }
    mat_desc = data["#<shader"]
    if is_valid_path(asset.diffuse):
        mat_desc["#<base_color"] = {
            "$type": "#com.autodesk.arnold.shader.color_correct",
            "#<input": {
                "$type": "#com.autodesk.arnold.shader.image",
                "#<filename": asset.diffuse, 
                "#<multiply": {"$type": "#com.autodesk.arnold.shader.image", "#<filename": asset.ao} if is_valid_path(asset.ao) else maxon.Vector(1, 1, 1)
            }
        }
    if is_valid_path(asset.metalness): mat_desc["#<metalness"] = { "$type": "#com.autodesk.arnold.shader.image", "#<filename": asset.metalness }
    if is_valid_path(asset.roughness): mat_desc["#<specular_roughness"] = { "$type": "#com.autodesk.arnold.shader.image", "#<filename": asset.roughness }
    if is_valid_path(asset.alpha): mat_desc["#<opacity"] = { "$type": "#com.autodesk.arnold.shader.image", "#<filename": asset.alpha }
    if is_valid_path(asset.transmission): mat_desc["#<transmission_color"] = { "$type": "#com.autodesk.arnold.shader.image", "#<filename": asset.transmission }
    if is_valid_path(asset.emission): mat_desc["#<emission_color"] = { "$type": "#com.autodesk.arnold.shader.image", "#<filename": asset.emission }
    if is_valid_path(asset.normal):
        mat_desc["#<normal"] = {
            "$type": "#com.autodesk.arnold.shader.normal_map",
            "#<input": { "$type": "#com.autodesk.arnold.shader.image", "#<filename": asset.normal }
        }
    if is_valid_path(asset.displacement):
        data["#<displacement"] = {
            "$type": "#com.autodesk.arnold.shader.displacement",
            "#<normal_displacement_input": { "$type": "#com.autodesk.arnold.shader.image", "#<filename": asset.displacement }
        }
    return data

def GetRedshiftDescription(asset: PBRPackage) -> dict:
    """Returns Redshift Graph Description dictionary for a PBRPackage."""
    data = {
        "$type": "#~.output",
        "#~.surface": { "$type": "#~.standardmaterial" }
    }
    mat_desc = data["#~.surface"]
    if is_valid_path(asset.diffuse):
        mat_desc["#~.base_color"] = {
            "$type": "#~.rscolorcorrection",
            "#~.input": {
                "$type": "#~.texturesampler",
                "#~.tex0/path": asset.diffuse,
                "#~.color_multiplier": {"$type": "#~.texturesampler", "#~.tex0/path": asset.ao} if is_valid_path(asset.ao) else maxon.Vector(1, 1, 1)
            }
        }
    if is_valid_path(asset.metalness): mat_desc["#~.metalness"] = { "$type": "#~.texturesampler", "#~.tex0/path": asset.metalness }
    if is_valid_path(asset.roughness): mat_desc["#~.refl_roughness"] = { "$type": "#~.texturesampler", "#~.tex0/path": asset.roughness }
    if is_valid_path(asset.alpha): mat_desc["#~.opacity_color"] = { "$type": "#~.texturesampler", "#~.tex0/path": asset.alpha }
    if is_valid_path(asset.normal):
        mat_desc["#~.bump_input"] = {
            "$type": "#~.bumpmap", "#~.inputtype": 1,
            "#~.input": { "$type": "#~.texturesampler", "#~.tex0/path": asset.normal }
        }
    if is_valid_path(asset.displacement):
        data["#~.displacement"] = {
            "$type": "#~displacement",
            "#~.texmap": { "$type": "#~.texturesampler", "#~.tex0/path": asset.displacement }
        }
    return data

def GetVRayDescription(asset: PBRPackage) -> dict:
    """Returns VRay Graph Description dictionary for a PBRPackage."""
    data = {
        "$type": "#~.mtlsinglebrdf",
        "#~.brdf": { "$type": "#~.brdfvraymtl" }
    }
    mat_desc = data["#~.brdf"]
    if is_valid_path(asset.diffuse):
        mat_desc["#~.diffuse"] = {
            "$type": "#~.colorcorrection",
            "#~.texture_map": {
                "$type": "#~.texbitmap",
                "#~.file": asset.diffuse,
                "#~.color_mult": {"$type": "#~.texbitmap", "#~.file": asset.ao} if is_valid_path(asset.ao) else maxon.Vector(1, 1, 1)
            }
        }
    if is_valid_path(asset.metalness): mat_desc["#~.metalness"] = { "$type": "#~.texbitmap", "#~.file": asset.metalness }
    if is_valid_path(asset.roughness):
        mat_desc["#~.reflect_glossiness"] = { "$type": "#~.texbitmap", "#~.file": asset.roughness }
        mat_desc["#~.option_use_roughness"] = True
    if is_valid_path(asset.alpha): mat_desc["#~.opacity_color"] = { "$type": "#~.texbitmap", "#~.file": asset.alpha }
    if is_valid_path(asset.normal):
        mat_desc["#~.bump_map"] = {
            "$type": "#~.texnormalbump", "#~.map_type": 1,
            "#~.bump_tex_color": { "$type": "#~.texbitmap", "#~.file": asset.normal }
        }
    return data

# =========================================================
# Description from Package
# =========================================================

def ArnoldDescriptionFromPackage(folder: str, name: str, res: str = None, doc: Optional[c4d.documents.BaseDocument] = None) -> Optional[c4d.BaseMaterial]:
    doc = doc or c4d.documents.GetActiveDocument()
    maker = DescriptionMaterialMaker(folder, name, res)
    if not maker._data or not maker._data.IsValid: return None
    material = c4d.BaseMaterial(c4d.Mmaterial)
    material.SetName(f"{name}_{res}" if res else name)
    if _ApplyPBRDescription(material, AR_NODESPACE, GetArnoldDescription(maker._data), doc):
        return material
    return None

def RedshiftDescriptionFromPackage(folder: str, name: str, res: str = None, doc: Optional[c4d.documents.BaseDocument] = None) -> Optional[c4d.BaseMaterial]:
    doc = doc or c4d.documents.GetActiveDocument()
    maker = DescriptionMaterialMaker(folder, name, res)
    if not maker._data or not maker._data.IsValid: return None
    material = c4d.BaseMaterial(c4d.Mmaterial)
    material.SetName(f"{name}_{res}" if res else name)
    if _ApplyPBRDescription(material, RS_NODESPACE, GetRedshiftDescription(maker._data), doc):
        return material
    return None

def VRayDescriptionFromPackage(folder: str, name: str, res: str = None, doc: Optional[c4d.documents.BaseDocument] = None) -> Optional[c4d.BaseMaterial]:
    doc = doc or c4d.documents.GetActiveDocument()
    maker = DescriptionMaterialMaker(folder, name, res)
    if not maker._data or not maker._data.IsValid: return None
    material = c4d.BaseMaterial(c4d.Mmaterial)
    material.SetName(f"{name}_{res}" if res else name)
    if _ApplyPBRDescription(material, VR_NODESPACE, GetVRayDescription(maker._data), doc):
        return material
    return None

# =========================================================
# Description Material - Direct Slots
# =========================================================

def _ConstructPackage(name: str, **kwargs) -> PBRPackage:
    pkg = PBRPackage(name)
    for slot, path in kwargs.items():
        if path: pkg.selected[slot] = path
    return pkg

def ArnoldDescriptionMaterial(name: str, diffuse: str = None, normal: str = None, roughness: str = None, 
                             metalness: str = None, ao: str = None, alpha: str = None, displacement: str = None,
                             emission: str = None, transmission: str = None, doc: Optional[c4d.documents.BaseDocument] = None) -> Optional[c4d.BaseMaterial]:
    doc = doc or c4d.documents.GetActiveDocument()
    pkg = _ConstructPackage(name, diffuse=diffuse, normal=normal, roughness=roughness, metalness=metalness, ao=ao, alpha=alpha, displacement=displacement, emission=emission, transmission=transmission)
    material = c4d.BaseMaterial(c4d.Mmaterial)
    material.SetName(name)
    if _ApplyPBRDescription(material, AR_NODESPACE, GetArnoldDescription(pkg), doc):
        return material
    return None

def RedshiftDescriptionMaterial(name: str, diffuse: str = None, normal: str = None, roughness: str = None, 
                               metalness: str = None, ao: str = None, alpha: str = None, displacement: str = None,
                               doc: Optional[c4d.documents.BaseDocument] = None) -> Optional[c4d.BaseMaterial]:
    doc = doc or c4d.documents.GetActiveDocument()
    pkg = _ConstructPackage(name, diffuse=diffuse, normal=normal, roughness=roughness, metalness=metalness, ao=ao, alpha=alpha, displacement=displacement)
    material = c4d.BaseMaterial(c4d.Mmaterial)
    material.SetName(name)
    if _ApplyPBRDescription(material, RS_NODESPACE, GetRedshiftDescription(pkg), doc):
        return material
    return None

def VRayDescriptionMaterial(name: str, diffuse: str = None, normal: str = None, roughness: str = None, 
                            metalness: str = None, ao: str = None, alpha: str = None,
                            doc: Optional[c4d.documents.BaseDocument] = None) -> Optional[c4d.BaseMaterial]:
    doc = doc or c4d.documents.GetActiveDocument()
    pkg = _ConstructPackage(name, diffuse=diffuse, normal=normal, roughness=roughness, metalness=metalness, ao=ao, alpha=alpha)
    material = c4d.BaseMaterial(c4d.Mmaterial)
    material.SetName(name)
    if _ApplyPBRDescription(material, VR_NODESPACE, GetVRayDescription(pkg), doc):
        return material
    return None

# =========================================================
# Main Creator Class
# =========================================================

@dataclass
class DescriptionMaterialMaker:
    """
    A class for creating and modifying materials using graph descriptions.

    Example:
        >>> maker = DescriptionMaterialMaker("path/to/folder", "material_name")
        >>> material = maker.MakeMaterial()
    """
    folder: str = field(repr=False)
    name: str
    res: str = field(default=None)
    triplaner: bool = False
    _data: Optional[PBRPackage] = field(init=False, default=None)

    def __post_init__(self) -> None:
        target_res = None
        if self.res:
            try:
                val = int(self.res)
                target_res = val * 1024 if val < 32 else val
            except (ValueError, TypeError): pass
        self._data = pbr_from_folder(self.folder, self.name, target_res)

    def MakeMaterial(self, doc: Optional[c4d.documents.BaseDocument] = None) -> Optional[c4d.BaseMaterial]:
        if C4D_VERSION < 2024200: return None
        if not self._data or not self._data.IsValid: return None
        doc = doc or c4d.documents.GetActiveDocument()
        engine = GetRenderEngine(doc)
        if engine == ID_ARNOLD: return ArnoldDescriptionFromPackage(self.folder, self.name, self.res, doc)
        if engine == ID_REDSHIFT: return RedshiftDescriptionFromPackage(self.folder, self.name, self.res, doc)
        if engine == ID_VRAY: return VRayDescriptionFromPackage(self.folder, self.name, self.res, doc)
        return None

#=============================================
# PBR Material from package (Legacy/Standard API)
#=============================================
def ArnoldPbrFromPackage(folder: str, pbr_name: str, triplanar: bool = True, use_displacement: bool = False, doc: c4d.documents.BaseDocument=None) -> Optional[c4d.BaseMaterial]:
    if doc is None:
        doc = c4d.documents.GetActiveDocument()
    pbrInstance = pbr_from_folder(folder, pbr_name)
    if not pbrInstance:
        return None
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
                node = tr.AddTextureTree(filepath=data['glossiness'], shadername="roughness", target_port=roughnessPort, triplaner_node=triplanar)

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
    pbrInstance = pbr_from_folder(folder, pbr_name)
    if not pbrInstance:
        return None
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
    pbrInstance = pbr_from_folder(folder, pbr_name)
    if not pbrInstance:
        return None
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
            displacementSlotName = c4d.DISPLACEMENT_TEXTURE
            displacementNode[displacementSlotName] = tr.AddImageTexture(texturePath=data['displacement'], nodeName="Displacement")
    if "alpha" in data:
        tr.AddImageTexture(texturePath=data['alpha'], nodeName="Alpha", parentNode=c4d.OCT_MATERIAL_OPACITY_LINK)
    if "emission" in data:
        emission = tr.AddTextureEmission(parentNode=c4d.OCT_MATERIAL_EMISSION)
        tr.AddImageTexture(texturePath=emission, nodeName="Emission", gamma=1, parentNode=emission[c4d.TEXEMISSION_EFFIC_OR_TEX])

    if "transmission" in data:
        tr.AddImageTexture(texturePath=data['transmission'], nodeName="Transmission", gamma=1, parentNode=c4d.OCT_MATERIAL_TRANSMISSION_LINK)
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
    pbrInstance = pbr_from_folder(folder, pbr_name)
    if not pbrInstance:
        return None
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
    pbrInstance = pbr_from_folder(folder, pbr_name)
    if not pbrInstance:
        return None
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
            elif "glossiness" in data and "roughness" not in data:
                tr.SetPortData(useRoughness, False)
                node = tr.AddTexture(filepath=data['glossiness'], shadername="Roughness",target_port=roughnessPort)
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
            albedoNode = mat.AddImagTexture(texturePath=albedo, nodeName="Albedo", isFloat=False, gamma=2.2)
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

