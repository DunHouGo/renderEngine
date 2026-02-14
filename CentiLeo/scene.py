# coding=utf-8

import c4d

class SceneHelper:
   def __init__(self, scene: c4d.BaseDocument = None):
        self.scene = scene if scene else c4d.documents.GetActiveDocument()
   

__all__ = [
    "SceneHelper"
]
