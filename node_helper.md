# Node Helper
This is a custom api for new NodeGragh in Cinema 4D above R26.
```
All the boghma plugins and boghma library is FREE.
```
# Limit
- Cinema 4D before R26 is not support.
- AddChild() and AddTextureTree() will return a not auto-layout node network now.
- GetID() is broken, wait Maxon fix it, GetParamDataTypeID() can not get vector id

## node_helper (Beta)
- __NodeGraghHelper__ : helper class for Cinema 4D NodeGragh.
- __TexPack__ : helper class to get texture data.
- __methods__ : helper functions.
  - __get_all_nodes__ : Get all the nodes in object manager.
  - __get_nodes__ : Get all the nodes by given types.
  - __get_tags__ : Get all the tags by given types.
  - __get_selection_tag__ : Get seclection tag for given texture tag.
  - __get_materials__ : Get material for given seclection tag.
  - __get_texture_tag__ : Get texture tag for given seclection tag.
  - __select_all_materials__ : Select all the materials (with undo).
  - __deselect_all_materials__ : Deselect all the materials (with undo).

### NodeHelper Class/method highlighted:

  - __GetAvailableShaders__ : Get all available nodes of current node space.
  - __GetActiveWires__ : Get all selected wires in node editor.
  - __GetActivePorts__ : Get all selected ports in node editor.
  - __GetActiveNodes__ : Get all selected nodes in node editor.
  - __select__ : Select the node.
  - __deselect__ : Deselect the node.
  - __add_shader__ : Add a shader.
  - __remove_shader__ : Remove the given shader.
  - __AddPort__ : Expose the given Expose on the material.
  - __RemovePort__ : Hide the given Expose on the material.
  - __GetTrueNode__ : Get the Node of given port.
  - __GetPort__ : Get the port of the shader node.
  - __GetOutput__ : Get the Output node.
  - __GetRootBRDF__ : Get the Root BRDF shader of the output.
  - __IsPortValid__ : Get the state of the port.
  - __GetParamDataTypeID__ : Get the data type id of given port.
  - __GetParamDataType__ :  Get the data type of given port.
  - __GetShaderValue__ : Get the value of given shader and port.
  - __SetShaderValue__ : Set the value of given shader and port.
  - __GetName__ : Get the node name.
  - __SetName__ : Set the node name.
  - __GetAssetId__ : Get the asset id of the given node.
  - __GetShaderId__ : Get the shader id of the given node.
  - __GetAllConnections__ : Get all the connected wire info.
  - __AddConnection__ : Connect two ports on two diffrent nodes.
  - __RemoveConnection__ : Remove the connection of the given port on a node.
  - __FoldPreview__ : Toggle folding state of the shader previews.
  - __GetNodes__ : Get all Nodes of given shader. (NEW@ v0.1.1)