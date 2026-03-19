
import re
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict
from pathlib import Path

# =========================================================
# Globals & Constants
# =========================================================

# PBR 槽位定义，定义了标准的贴图通道名称
# Standard PBR slot names defined as a tuple for immutability
PBR_SLOTS: tuple[str, ...] = (
    "diffuse", 
    "specular", 
    "metalness", 
    "roughness", 
    "glossiness",
    "ao", 
    "alpha", 
    "bump", 
    "normal", 
    "emission", 
    "displacement",
    "transmission", 
    "sheen", 
    "anisotropy", 
    "coat", 
    "arm", 
    "orm"
)

# 支持的图像文件后缀名
# Common image extensions supported by most render engines
IMAGE_EXTENSIONS: tuple[str, ...] = (
    ".exr", ".tif", ".tiff", ".png", ".tga", ".jpg", ".jpeg", ".bmp", ".hdr"
)

# 格式优先级权重，用于在存在多种格式时自动选择最佳格式（如优先选择 EXR）
# Format priority weights for auto-selection (higher is better)
FORMAT_PRIORITY: dict[str, int] = {
    ".exr": 100, ".tif": 95, ".tiff": 95, ".png": 85,
    ".tga": 80, ".jpg": 60, ".jpeg": 60, ".bmp": 50
}

# 贴图类型的关键字映射表
# Mapping of keywords to their respective PBR map types
MAP_KEYWORDS: dict[str, tuple[str, ...]] = {
    "diffuse": ("diff", "dif", "diffuse", "albedo", "basecolor", "base_color", "color", "col", "base"),
    "normal": ("normal", "nor", "nrm", "normalgl", "normaldx", "opengl", "directx", "nrm_gl", "nrm_dx"),
    "roughness": ("rough", "roughness", "rougher"),
    "glossiness": ("gloss", "glossiness", "glossy"),
    "metalness": ("metal", "metallic", "metalness", "m"),
    "specular": ("spec", "specular", "edgetint", "spec_level"),
    "ao": ("ao", "ambientocclusion", "occlusion", "occ", "mixed_ao"),
    "displacement": ("disp", "displacement", "height", "heightmap", "depth", "displace", "dis"),
    "bump": ("bump", "b"),
    "alpha": ("alpha", "opacity", "opacity_mask", "mask"),
    "emission": ("emission", "emissive", "emit", "emis", "light"),
    "transmission": ("transmission", "translucency", "trans", "sss", "subsurface"),
    "arm": ("arm",),
    "orm": ("orm",),
    "sheen": ("sheen",),
    "coat": ("clearcoat", "coat"),
    "anisotropy": ("anisotropy", "anis", "anisotropy_angle")
}

# 性能优化：将关键字映射表展平，以便在扫描时进行 O(1) 查找
# Optimization: Flatten the keyword dictionary for O(1) reverse lookup
KEYWORD_TO_TYPE: dict[str, str] = {
    kw: map_type for map_type, keywords in MAP_KEYWORDS.items() for kw in keywords
}

# 正则表达式定义
# Regex definitions for capturing metadata from filenames
RESOLUTION_PATTERN = re.compile(r"(?P<k_val>\d+)[kK]|(?P<num_val>512|1024|2048|4096|8192)")
UDIM_PATTERN = re.compile(r"1\d{3}")           # 匹配 UDIM 标准格式 (1001-1999)


def tokenize(filename: str) -> list[str]:
    """
    Split filename into lowercase tokens for easier identification.

    Args:
        filename: The original filename strings.
        
    Returns:
        A list of cleaned-up lowercase tokens.

    Example:
        >>> tokenize("Grass_01_4k_Diffuse.jpg")
        ['grass', '01', '4k', 'diffuse']
    """
    # 移除后缀并根据常见分隔符（点、下划线、空格、横杠）分割字符串
    name = Path(filename).stem
    return list(filter(None, re.split(r"[._\-\s]+", name.lower())))

def detect_map_type(tokens: list[str]) -> Optional[str]:
    """
    Identifies the PBR map type from filename tokens using keyword matching.

    Args:
        tokens: Tokenized parts of the filename.
        
    Returns:
        The matched PBR slot name or None.

    Example:
        >>> detect_map_type(['rock', 'basecolor'])
        'diffuse'
        >>> detect_map_type(['metal', 'nrm'])
        'normal'
    """
    # 遍历令牌，利用全局展平的字典快速查找
    for token in tokens:
        if token in KEYWORD_TO_TYPE:
            return KEYWORD_TO_TYPE[token]
    return None

def detect_resolution(name: str) -> Optional[int]:
    """
    Extracts texture resolution from name (e.g., '2k' -> 2).

    Args:
        name: The filename to search.
        
    Returns:
        Integer resolution or None.

    Example:
        >>> detect_resolution("Concrete_2k_roughness.png")
        2048
        >>> detect_resolution("Wall_4096_ao.exr")
        4096
    """
    match = RESOLUTION_PATTERN.search(name.lower())
    if not match:
        return None
        
    if match.group("k_val"):
        return int(match.group("k_val")) * 1024
    
    if match.group("num_val"):
        return int(match.group("num_val"))
        
    return None

def detect_udim(name: str) -> Optional[int]:
    """
    Identify UDIM sequence identifiers from filename.

    Args:
        name: The filename to search.
        
    Returns:
        The 4-digit UDIM integer or None.

    Example:
        >>> detect_udim("character_diffuse.1001.tif")
        1001
    """
    match = UDIM_PATTERN.search(name)
    return int(match.group()) if match else None

def detect_normal_format(tokens: list[str]) -> Optional[str]:
    """
    Detect normal map format (DirectX vs OpenGL) from filename tokens.

    Args:
        tokens: Tokenized parts of the filename.
        
    Returns:
        Format string or None.

    Example:
        >>> detect_normal_format(['stone', 'normal', 'dx'])
        'directx'
    """
    if any(k in tokens for k in ("dx", "directx", "nrm_dx")): return "directx"
    if any(k in tokens for k in ("gl", "opengl", "nrm_gl")): return "opengl"
    return None

def detect_asset_name(tokens: list[str]) -> str:
    """
    Heuristically reconstruct the asset name by filtering out metadata tokens.

    Args:
        tokens: Tokenized parts of the filename.
        
    Returns:
        The reconstructed asset name string.

    Example:
        >>> detect_asset_name(['rusty', 'metal', '02', '4k', 'diffuse'])
        'rusty_metal_02'
    """
    filtered = []
    all_keywords = set(KEYWORD_TO_TYPE.keys()) | {"dx", "gl", "opengl", "directx"}
    
    for t in tokens:
        # Keep tokens unless they are PBR keywords, resolution tags (e.g., '4k'), or UDIMs.
        if t in all_keywords or re.fullmatch(r"\d+k", t) or UDIM_PATTERN.fullmatch(t):
            continue
        filtered.append(t)

    return "_".join(filtered) if filtered else "asset"


# =========================================================
# Legacy & Helper Functions
# =========================================================

def IsImageFile(file_path: str) -> bool:
    """
    Check if the file is a supported image format and exists.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        True if it's a valid image file.

    Example:
        >>> IsImageFile("C:/Textures/wood_diffuse.jpg")
        True
    """
    path = Path(file_path)
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS

def GetPBRName(filename: str) -> Optional[str]:
    """
    Extract the base asset name from a filename by stripping PBR suffixes.
    
    Args:
        filename: Name of the file.
        
    Returns:
        Base asset name or None if no PBR mapping detected.

    Example:
        >>> GetPBRName("Rock01_4k_diffuse.jpg")
        'rock01'
        >>> GetPBRName("Wood_basecolor.png")
        'wood'
    """
    tokens = tokenize(filename)
    if not detect_map_type(tokens):
        return None
    return detect_asset_name(tokens)

def is_in_package(filename: str, package_name: str) -> bool:
    """
    Verify if a filename belongs to a specific PBR package.
    
    Args:
        filename: Name of the file to check.
        package_name: The base name of the PBR asset.
        
    Returns:
        True if they match.

    Example:
        >>> is_in_package("Metal02_normal.tga", "metal02")
        True
    """
    return GetPBRName(filename) == package_name

def InPackage(filename: str, package_name: str) -> bool:
    """Legacy wrapper for is_in_package."""
    return is_in_package(filename, package_name)

def GetPBRImages(folder_path: str, package_name: str = "") -> list[str]:
    """
    Find all texture files in a folder belonging to a specific PBR package.
    
    Args:
        folder_path: Path to the directory.
        package_name: Base asset name.
        
    Returns:
        List of absolute paths to related textures.

    Example:
        >>> GetPBRImages("C:/Assets/Rock01/", "rock01")
        ['C:/Assets/Rock01/Rock01_diffuse.jpg', 'C:/Assets/Rock01/Rock01_rough.jpg']
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        return []
    
    # If the package_name refers to a subfolder, we prioritize scanning THAT folder
    search_folder = base_folder
    search_package = package_name
    
    if package_name:
        sub_folder = base_folder / package_name
        if sub_folder.is_dir():
            search_folder = sub_folder
            search_package = ""  # Within its own folder, accept all relevant images
            
    results = []
    try:
        for item in search_folder.iterdir():
            if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS:
                if not search_package or is_in_package(item.name, search_package):
                    results.append(str(item.absolute()))
    except (OSError, PermissionError):
        pass
                
    return results

def GetPackageNames(folder_path: str) -> list[str]:
    """
    Scan a directory and return all unique PBR asset names found.
    
    Args:
        folder_path: Path to the directory.
        
    Returns:
        List of unique asset names.

    Example:
        >>> GetPackageNames("C:/MyLibrary/")
        ['brick01', 'concrete_floor', 'metal_rust']
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        return []
        
    names = set()
    try:
        for item in folder.iterdir():
            # 1. Collect asset names from PBR files in the root
            if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS:
                name = GetPBRName(item.name)
                if name:
                    names.add(name)
            # 2. Collect subfolder names (commonly used for PBR packages)
            elif item.is_dir() and not item.name.startswith((".", "_")) and "Thumbnail" not in item.name:
                names.add(item.name)
    except (OSError, PermissionError):
        pass
                
    return sorted(list(names))


@dataclass
class TextureFile:
    """
    Represents a single texture file and its parsed metadata.
    """
    path: str
    asset: str
    map_type: str
    resolution: Optional[int]
    udim: Optional[int]
    extension: str
    normal_format: Optional[str] = None

    def format_priority(self) -> int:
        """Get the numeric priority of the file extension."""
        return FORMAT_PRIORITY.get(self.extension, 0)

@dataclass
class PBRPackage:
    """
    A collection of textures belonging to the same asset, providing resolution and selection logic.

    Example:
        >>> pkg = PBRPackage("rock01")
        >>> pkg.add_texture(TextureFile(path="...", map_type="diffuse", ...))
        >>> pkg.resolve()
        >>> print(pkg.diffuse)  # Direct access to PBR_SLOTS as attributes
        'path/to/diffuse.jpg'
    """
    asset_name: str
    # 存储不同通道下的多个备选贴图（不同分辨率、不同格式）
    textures: dict[str, list[TextureFile]] = field(default_factory=lambda: defaultdict(list))
    # 存储最终选定的每种通道的文件路径
    selected: dict[str, str] = field(default_factory=dict)
    # 存储 UDIM 序列信息
    udim_tiles: dict[str, list[str]] = field(default_factory=dict)
    resolution: Optional[int] = None
    workflow: Optional[str] = None

    def __getattr__(self, name: str) -> Optional[str]:
        """Dynamic access to textures using PBR_SLOTS names."""
        if name in PBR_SLOTS:
            return self.selected.get(name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    @property
    def IsValid(self) -> bool:
        """Check if the package contains any valid textures."""
        return len(self.selected) > 0

    @property
    def use_ao(self) -> bool:
        return self.selected.get("ao") is not None

    @property
    def metalness_roughness_flow(self) -> bool:
        return self.workflow == "metal_rough"

    def add_texture(self, tex: TextureFile) -> None:
        """Add a parsed texture file to the internal collection."""
        self.textures[tex.map_type].append(tex)

    def get_maps(self) -> dict[str, str]:
        """Get the detected maps."""
        return self.selected

    def resolve(self) -> None:
        """
        Process the collection of textures to select the best candidates based on 
        resolution and file format priority.

        Example:
            >>> pkg.add_texture(TextureFile(path="...", ...))
            >>> pkg.resolve()
            >>> print(pkg.resolution)
            4096
        """
        # 针对每个通道优选
        for map_type, files in self.textures.items():
            # 分辨率降序，格式优先级降序
            # (EXR > TIFF > PNG)
            files.sort(key=lambda x: (x.resolution or 0, x.format_priority()), reverse=True)
            
            best = files[0]
            self.selected[map_type] = best.path
            
            # 最高分辨率
            if best.resolution:
                self.resolution = max(self.resolution or 0, best.resolution)

            # UDIM
            if best.udim:
                self.udim_tiles[map_type] = [f.path for f in files if f.udim]

        self.detect_workflow()

    def detect_workflow(self) -> None:
        """Determines if the material uses a Metalness or Specular workflow."""
        if "metalness" in self.selected and "roughness" in self.selected:
            self.workflow = "metal_rough"
        elif "specular" in self.selected and "glossiness" in self.selected:
            self.workflow = "spec_gloss"
        else:
            self.workflow = "unknown"

    def get_valid_dict(self) -> dict[str, str]:
        """
        Returns a mapping of slot names to their selected file paths.

        Example:
            >>> pkg.get_valid_dict()
            {'diffuse': '...', 'normal': '...'}
        """
        return {slot: path for slot, path in self.selected.items() if slot in PBR_SLOTS}

    def to_dict(self) -> dict[str, ...]:
        """
        Serialize package information.

        Returns:
            data = {
                "asset_name": str,
                "resolution": int,
                "workflow": str,
                "maps": dict[str, str],
                "udim_tiles": dict[str, list[str]],
            }
        """

        return {
            "asset_name": self.asset_name,
            "resolution": self.resolution,
            "workflow": self.workflow,
            "maps": self.get_valid_dict(),
            "udim_tiles": self.udim_tiles,
        }

# =========================================================
# Scanner
# =========================================================

class PBRLibraryScanner:
    """
    Recursively scans directories to group individual texture files into coherent PBR packages.

    Example:
        >>> scanner = PBRLibraryScanner("/path/to/textures")
        >>> scanner.scan()
        >>> for pkg in scanner.packages.values():
        ...     print(pkg.name, pkg.resolution)
    """
    def __init__(self, root: str):
        self.root = root
        self.packages: dict[str, PBRPackage] = {}

    def scan(self) -> None:
        """Performs the directory walk and metadata extraction."""
        # 建议优化点：对于海量文件，使用 os.scandir 比 os.path 更快
        # Using pathlib for cleaner directory walking
        root_path = Path(self.root)
        if not root_path.exists():
            return

        for p in root_path.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            filename = p.name
            tokens = tokenize(filename)
            map_type = detect_map_type(tokens)

            if not map_type:
                continue

            asset = detect_asset_name(tokens)
            
            tex = TextureFile(
                path=str(p.absolute()),
                asset=asset,
                map_type=map_type,
                resolution=detect_resolution(filename),
                udim=detect_udim(filename),
                extension=p.suffix.lower(),
                normal_format=detect_normal_format(tokens)
            )

            if asset not in self.packages:
                self.packages[asset] = PBRPackage(asset)

            self.packages[asset].add_texture(tex)

    def build(self) -> dict[str, PBRPackage]:
        """
        Scans, resolves and returns the final package dictionary.

        Example:
            >>> scanner = PBRLibraryScanner("C:/Assets/PBR/")
            >>> packages = scanner.build()
            >>> for name, pkg in packages.items():
            ...     print(name, pkg.workflow)
        """
        self.scan()
        for pkg in self.packages.values():
            pkg.resolve()
        return self.packages

# =========================================================
# Simplified Lookups
# =========================================================

def _build_package_from_paths(paths: list[str], asset_name: str, resolution: Optional[int] = None) -> Optional[PBRPackage]:
    """Helper to convert a list of file paths into a resolved PBRPackage."""
    if not paths:
        return None
        
    package = PBRPackage(asset_name)
    for p in paths:
        path_obj = Path(p)
        tokens = tokenize(path_obj.name)
        map_type = detect_map_type(tokens)
        if not map_type:
            continue
            
        file_res = detect_resolution(path_obj.name)
        # If a specific resolution is requested, filter out others
        if resolution is not None and file_res is not None and file_res != resolution:
            continue

        tex = TextureFile(
            path=str(path_obj.absolute()),
            asset=asset_name,
            map_type=map_type,
            resolution=file_res,
            udim=detect_udim(path_obj.name),
            extension=path_obj.suffix.lower(),
            normal_format=detect_normal_format(tokens)
        )
        package.add_texture(tex)
        
    if package.textures:
        package.resolve()
        return package
    return None

def pbr_from_file(file_path: str, resolution: Optional[int] = None) -> Optional[PBRPackage]:
    """
    Given an absolute path to a single texture, find all related textures in the same folder 
    and return a resolved PBRPackage.

    Example:
        >>> pkg = pbr_from_file("C:/Assets/Rock_01/Rock_01_diffuse.jpg")
    """
    path = Path(file_path)
    if not path.exists() or path.suffix.lower() not in IMAGE_EXTENSIONS:
        return None

    # Identify the asset name from the input file
    tokens = tokenize(path.name)
    asset_name = detect_asset_name(tokens)
    
    # Get all sibling images belonging to this asset
    paths = GetPBRImages(str(path.parent), asset_name)
    return _build_package_from_paths(paths, asset_name, resolution)

def pbr_from_folder(folder: str, name: str, resolution: Optional[int] = None) -> Optional[PBRPackage]:
    """
    Creates a resolved PBRPackage by scanning a folder for textures matching a specific asset name.
    
    Args:
        folder: Path to the directory.
        name: The base asset name to search for.
        resolution: Optional specific resolution to filter by (e.g. 2048).

    Example:
        >>> pkg = pbr_from_folder("C:/Assets/Rock_01", "Rock_01", 2048)
    """
    paths = GetPBRImages(folder, name)
    return _build_package_from_paths(paths, name, resolution)

def get_pbr_package(file_path: str) -> Optional[PBRPackage]:
    """Alias for pbr_from_file."""
    return pbr_from_file(file_path)

# =========================================================
# Example
# =========================================================

def main():

    library = r"D:\Boghma\test boghma hub\Boghma for C4D\Texture Library\PBR Example Library"

    scanner = PBRLibraryScanner(library)

    packages = scanner.build()

    for asset, pkg in packages.items():

        print("Asset:", asset)

        print("Workflow:", pkg.workflow)

        for k, v in pkg.get_maps().items():

            print(" ", k, v)

        if pkg.udim_tiles:

            print(" UDIM:", pkg.udim_tiles)

        print()

    p = r"D:\Boghma\test boghma hub\Boghma for C4D\Texture Library\subFolder Example Library\GSG_MC001_A286_DGreyPlastic\GSG_MC001_A286_DGreyPlastic_4k_basecolor.jpg"

    pack = get_pbr_package(p)

    print(pack)

# if __name__ == "__main__":
#     main()