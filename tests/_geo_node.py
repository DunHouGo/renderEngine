import maxon
import c4d

# create scene nodes capsule
# 180420400 = deformer
# 180420600 = mesh primitive
# 180420700 = spline primitive
obj = c4d.BaseObject(180420400)

# set id of node asset to use
# 180420304 is MSG_SET_ASSET_WITH_VERSION
obj.Message(180420304, {'assetid': 'net.maxon.neutron.asset.geo.geometryaxisv3', 'assetversion': ''})

# get node graph
graph = obj.GetNimbusRef('net.maxon.neutron.nodespace').GetGraph()

# configure parameters
with graph.BeginTransaction() as gt:
  # Align Y
  graph.GetNode(maxon.NodePath('<in@AORGkTlNC9sidD4DBLxbKt')).SetPortValue(0.2)
  # Offset
  graph.GetNode(maxon.NodePath('<in@flJKRSTsJB_gWcewzKMRuX')).SetPortValue(maxon.Vector(10, 20, 30))
  gt.Commit()

doc = c4d.documents.GetActiveDocument()
doc.InsertObject(obj)
