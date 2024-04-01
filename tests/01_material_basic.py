import c4d
import maxon
import Renderer
from Renderer import Redshift, Arnold, Octane, EasyTransaction, TextureHelper
from pprint import pprint

""" 
These examples show how to create and modify materials
We can use Renderer.NodeGraghHelper to modify node materials who used new node graph,
And we can use Redshift.Material and Arnold.Material to get some preset helper methods.

For some reasons, AddShader-like methods(maxon.GraphModelInterface.AddChild) will add the node in the center
If we call those methods on exsited material, it will be a mess, you can call Renderer.ArrangeAll() after.

Due to Octane use his Custom UserArea UI base on old layer system, and didn't support python
We can only modify in material level, but can not interactive with selections in octane node editor.


"""

# Create a TextureHelper instance
# 创建一个 TextureHelper 实例
tex_helper: TextureHelper = TextureHelper()

# 获取资产路径, "UV Test Grid.png" with AssetId : file_5b6a5fe03176444c
url: maxon.Url = tex_helper.GetAssetUrl("file_5b6a5fe03176444c")

# "si-v1_fingerprints_02_15cm.png" with AssetId : file_fa9c42774dd05049
disp: maxon.Url = tex_helper.GetAssetUrl("file_fa9c42774dd05049")

# How to reate a redshift material and modify
def create_material():

    """
    How to reate a redshift material and modify the gragh with EasyTransaction.
    """

    # Create Redshift Node Material instance, if no material filled, we create a new STD material.
    # 创建一个Redshift节点材质实例,如果没有材质传入，创建新的STD材质
    material: c4d.BaseMaterial = Redshift.Material("MyMaterial")

    # Use EasyTransaction to modify the graph
    # 使用EasyTransaction来修改材质
    with EasyTransaction(material) as tr:
    
        # the attribute #tr is the instance of Redshift.MaterialHelper, 
        # we got it with just apply to the #material to the EasyTransaction
        # it will inherit from NodeGraghHelper class
        # 属性tr是Redshift.MaterialHelper的实例，通过将材质赋予EasyTransaction获得，继承自NodeGraghHelper

        # Use Redshift.MaterialHelper methods : add a texture + displacement to the Output node
        # 使用Redshift.MaterialHelper中的方法: 添加图片+置换节点到Output节点
        tr.AddDisplacementTree(filepath = disp, shadername = "DISP")

        # Use NodeGraghHelper methods： get the Output(endNode)
        # 使用NodeGraghHelper中的方法: 获取输出节点
        output = tr.GetOutput()
        print(f"{output = }")

        # Insert the material to the document
        # 导入材质(来自Redshift MaterialHelper)
        tr.InsertMaterial()

    # Auto apply GraphTransaction.Commit() to the graph
    # 退出with后, 自动执行GraphTransaction.Commit()

# Modify an exist material
# select the material we just create to call this example
def modify_material():

    # 选择material
    material: c4d.BaseMaterial = c4d.documents.GetActiveDocument().GetActiveMaterial()

    # 自定义EasyTransaction
    # 将材质转换为支持的MaterialHelper实例
    with EasyTransaction(material) as tr:

        # 使用NodeGraghHelper中的方法
        output = tr.GetOutput()
        # 使用NodeGraghHelper中的SetName方法,更改节点名称
        tr.SetName(output, "My Output Node")

        # Find brdf node (in this case : standard surface)
        # 查找Standard Surface节点
        standard_surface = tr.GetRootBRDF()

        # Change a shader name
        # 更改Standard Surface节点名称
        tr.SetName(standard_surface,'My BRDF Shader')
        
        # 获取Standard Surface上的base color端口
        tar = tr.GetPort(standard_surface,'com.redshift3d.redshift4c4d.nodes.core.standardmaterial.base_color')

        # 将纹理节点树（triplaner）到 base color 节点中
        tr.AddTextureTree(shadername = 'Asset UV Map', filepath = url, raw = True, triplaner_node = True, scaleramp = False, target_port = tar)

        # 添加置换树
        tr.AddDisplacementTree()

        # 清理未连接的节点,如果没有指认filterId，则清理全部未连接
        tr.RemoveIsolateNodes()
        
    # 退出with后, 自动执行Commit()

# Modify an exist material with selections
def access_material_data():

    # 选择material
    material: c4d.BaseMaterial = c4d.documents.GetActiveDocument().GetActiveMaterial()

    # 自定义EasyTransaction
    # 将材质转换为支持的MaterialHelper实例
    with EasyTransaction(material) as tr:

        # 获取选择的节点，当single_mode为True时，如果只有一个节点被选中，则返回节点（而不是列表）
        act_node: maxon.GraphNode = tr.GetActiveNodes(single_mode=True)
        act_port: maxon.GraphNode = tr.GetActivePorts(single_mode=True)
        act_wire: list[maxon.GraphNode, maxon.GraphNode, maxon.Wires] = tr.GetActiveWires(single_mode=True)

        # when we select a true node in redshift node space
        # if the selected node is a image node, add a unitransform group to it
        if act_node:
            # Redshift空间
            if tr.nodespaceId == Renderer.RS_NODESPACE:
                # 如果选择的节点是纹理节点
                if tr.GetShaderId(act_node) == "texturesampler":

                    # Set the preview image "OFF"
                    tr.FoldPreview(act_node, False)

                    # 创建一个UniTranform自定义组，统一控制纹理节点的PSR
                    tr.AddUniTransform(tex_shader=act_node)
        
        # when we select a port with data type "color"
        # we add a node tree to this port.
        if act_port:
            # 颜色 / 浮点端口
            if tr.GetPortDataTypeId(act_port) == maxon.Id("net.maxon.parametrictype.col<3,float64>"):
                tr.AddTexture(filepath=url, shadername="Color Texture", raw=False, target_port=act_port)

        # when we select a wire, 
        # we insert a cc node into the wire.
        if act_wire:
            tr.InsertShader("com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection",
                    act_wire,
                    ['com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection.input'],
                    'com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection.outcolor')
        
        # Get all connected ports.
        connect_ports: list = tr.GetAllConnectedPorts()
        print("All Connected Ports:")
        for port in connect_ports:
            print(tr.GetName(port))
        print("="*10)

    # 退出with后, 自动执行Commit()

# Modify an exist Octane material
def modify_octane_material():

    # 如果不传入material，则初始化一个Octane material(Standard/Universal)
    material: Octane.Material = Renderer.Octane.Material(create_standard=False)

    # Add a float texture to roughness port
    material.AddFloat(parentNode = c4d.OCT_MATERIAL_ROUGHNESS_LINK)

    # Add a node tree to Albedo port, and set path and props
    url: maxon.Url = tex_helper.GetAssetStr("file_ed38c13fd1ae85ae")
    material.AddTextureTree(texturePath = url, nodeName = 'Albedo', isFloat = False, gamma = 2.2,
                           invert = False, parentNode = c4d.OCT_MATERIAL_DIFFUSE_LINK)

    # Get all shader in the material
    node_list = material.GetAllShaders()

    # Get all the image nodes, we just have one, so we get it
    imageNode = material.GetNodes(Octane.ID_OCTANE_IMAGE_TEXTURE)[0]
    nodesAfter = material.GetNextNodes(imageNode)

    # Print the info
    print(f'We create an Octane Material with name {material.material.GetName()}')
    print('#-----Shader-----#')
    pprint(node_list)
    print('#-----Image-----#')
    pprint(imageNode)
    print('#-----Shader Tree-----#')
    pprint(nodesAfter)
    print('#----- End -----#')
    
    # Insert the material to the doc, activ doc is defult when None passed.
    material.InsertMaterial()

    # Update the material
    material.Refresh()

    # Push a Refresh to Cinema
    c4d.EventAdd()

    # Open Octane Node Editor with the material
    Octane.OpenNodeEditor(material)

def ConvertTest():

    material: c4d.BaseMaterial = c4d.documents.GetActiveDocument().GetActiveMaterial()

    with EasyTransaction(material) as tr: 

        nodes = tr.GetActiveNodes()
        for node in nodes:
            print(f"Node: {tr.GetName(node)}")
            print(f"Default Input: {tr.GetConvertInput(node)}")
            print(f"Default Output: {tr.GetConvertOutput(node)}")
            print("-"*10)

if __name__ == '__main__':
    Renderer.ClearConsole()
    create_material()
    # modify_material()
    # access_material_data()
    # modify_octane_material()
    # ConvertTest()