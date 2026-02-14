from warnings import warn
import c4d
from ..constants import *
from ..utils import GetVideoPost

# todo : not finished yet, wait for CentiLeoupdate their aov system.
class AOVHelper:

    """
    Custom helper to modify CentiLeo AOV.
    """

    def __init__(self, vp: c4d.documents.BaseVideoPost = None):
        
        if isinstance(vp, c4d.documents.BaseVideoPost):
            if vp.GetType() == int(ID_CENTILEO):
                self.doc = vp.GetDocument()
                self.vp: c4d.documents.BaseVideoPost = vp
                self.vpname: str = self.vp.GetName()

        elif vp is None:
            self.doc: c4d.documents.BaseDocument = c4d.documents.GetActiveDocument()
            self.vp: c4d.documents.BaseVideoPost = GetVideoPost(self.doc, ID_CENTILEO)
            self.vpname: str = self.vp.GetName()

        warn("This class is still in development, wait for CentiLeoupdate their aov system.")

    def __str__(self) -> str:
        return (f'<Class> {__class__.__name__} with videopost named {self.vpname}')


__all__ = [
    "AOVHelper"
]