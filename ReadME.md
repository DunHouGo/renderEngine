# renderEngine
This is a custom api for most popular render engine like Octane\Redshift\Arnold in Cinema 4D, which is also wiil contains in 'boghma' library.
```
All the boghma plugins and boghma library is FREE.
```

## Installation
To use this library, you have two options:
1. Download the source and import it to your Cinema 4D
2. (**Not Ready Now**) You can also download [Boghma Plugin Manager](https://www.boghma.com/) and install any plugin, the boghma lib will auto installed.

# Limit
- Due to Otoy use a custom userarea for the node editor, and don't support python. We can not get the selection of the node edtor, so it is not possible to interact with node editor. 
- Redshift and Arnold material helper only support NodeGragh, so the Cinema 4D before R26 is not support.
- AddChild() and AddTextureTree() will return a not auto-layout node network now.
- GetID() is broken, wait Maxon fix it, GetParamDataTypeID() can not get vector id


# Examples
- [__Octane Example__](./octane/octane_examples.py) (Beta)
- [__Redshift Example__](./redshift/redshift_examples.py)  (not ready now)
- [__Arnold Example__](./arnold/arnold_examples.py)  (not ready now)


# Class Presentation

## [node_helper](./node_helper.md) (Beta)
- __NodeGraghHelper__ : helper class for Cinema 4D NodeGragh.
- __TexPack__ : helper class to get texture data.
- __methods__ : helper functions.
  - get_all_nodes
  - get_nodes
  - get_tags
  - get_selection_tag
  - get_materials
  - get_texture_tag
  - select_all_materials
  - deselect_all_materials

## [octane](./octane/Octane.md) (Beta)
- __octane_id__ : unique ids for octane object, and name map of aovs.
- __octane_helper__ : all the helper class and function.
  - methods
  - VideoPostHelper (class)
  - AOVData (class)
  - AOVHelper (class)
  - NodeHelper (class)
  - MaterialHelper (class)
  - SceneHelper (class)

## redshift (not ready now)
- __redshift__ : unique ids for redshift object, and name map of aovs.
- __redshift_helper__ : all the helper class and function.
  - methods
  - VideoPostHelper (class)
  - RedshiftAOVData (class)
  - AOVHelper (class)
  - MaterialHelper (class)
  - SceneHelper (class)
  - 
## arnold (not ready now)
- __arnold__ : unique ids for arnold object, and name map of aovs.
- __arnold_helper__ : all the helper class and function.
  - methods
  - VideoPostHelper (class)
  - AOVData (class)
  - AOVHelper (class)
  - MaterialHelper (class)
  - SceneHelper (class)

# Version & Updates
- **0.1.0** : octane_helper and node_helper is beta now. (update@2023.06.30)
- __coming soon...__