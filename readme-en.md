# Renderer User Guide

Renderer is a Cinema 4D helper library for working with materials, nodes, AOVs, and scene objects across popular renderers.

## Feature Groups

- `Redshift`: Redshift materials, AOVs, and scene operations.
- `Arnold`: Arnold materials, AOVs, and scene operations.
- `Vray`: V-Ray materials and AOV operations.
- `CentiLeo`: CentiLeo materials and AOV operations.
- `Octane`: Octane materials, AOVs, scenes, and node arrangement.
- `Corona`: Corona materials, AOVs, scenes, and node arrangement.
- `utils`: Node, material, texture, PBR, and node arrangement helpers.
- `constants`: Renderer node and port constants.

## Common Parameters

Parameters vary by renderer and operation, but commonly include:

- Material object: the Cinema 4D material to read or modify.
- Node object: the node to connect, move, or inspect.
- Port name or ID: the input or output port on a node.
- File path: the texture, PBR map, or scene resource location.
- Node space ID: the renderer node space when required.
- Arrangement mode: arrange, align, or distribute nodes.

Make sure the relevant renderer is installed before using its helpers, and pass the objects and resources required by each function.

## Interaction Notes

Renderer does not provide a separate window or panel. Node arrangement functions directly change node positions in the Cinema 4D material editor. Arrange, align, and distribute behavior is selected by the function being called; context menus, dragging, and node selection remain handled by Cinema 4D.

## Release Archive

Run `scripts/build_renderer_release.py` to create `Renderer.zip` in the parent `dist` folder. Use the `Renderer` folder contained in the archive after extraction.
