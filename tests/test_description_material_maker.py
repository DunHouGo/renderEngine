from Renderer import MaterialMakerNew, PackageData
from pprint import pp
import c4d

def main():
    test_dir = r"C:\Users\DunHou\Documents\PolyHaven Assets\aerial_beach_01\textures"
    package = PackageData(folder=test_dir, name='aerial_beach_01', res='1')
    package.build()
    print(package.diffuse)
    print(package.metalness)
    print(package.ao)
    
    valid_textures = package.get_data()
    pp(valid_textures)
    
    mm = MaterialMakerNew(folder=test_dir, name='aerial_beach_01', res='2')
    mm.MakeMaterial(c4d.documents.GetActiveDocument())
    c4d.EventAdd()
    
if __name__ == '__main__':
    
    main()
    