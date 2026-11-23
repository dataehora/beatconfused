"""R13V4: reads a STEP file with its colours (OCP / XCAF) and tessellates it: [(vertices Nx3 float, triangles Mx3 int, (r, g, b))].

    from stepcolor import read_step
Millimetres, the file's own frame (no re-centring).
"""
import numpy as np
from OCP.BRep import BRep_Tool
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.IFSelect import IFSelect_RetDone
from OCP.Quantity import Quantity_Color
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDF import TDF_LabelSequence
from OCP.TDocStd import TDocStd_Document
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED, TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS
from OCP.XCAFApp import XCAFApp_Application
from OCP.XCAFDoc import XCAFDoc_ColorCurv, XCAFDoc_ColorGen, XCAFDoc_ColorSurf, XCAFDoc_DocumentTool


def _col(ct, shape):
    c = Quantity_Color()
    for kind in (XCAFDoc_ColorSurf, XCAFDoc_ColorGen, XCAFDoc_ColorCurv):
        if ct.GetColor(shape, kind, c):
            return (c.Red(), c.Green(), c.Blue())
    return None


def read_step(path, lin_defl=0.03, ang_defl=0.3):
    app = XCAFApp_Application.GetApplication_s()
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    app.NewDocument(TCollection_ExtendedString("MDTV-XCAF"), doc)
    rd = STEPCAFControl_Reader()
    rd.SetColorMode(True)
    rd.SetNameMode(True)
    if rd.ReadFile(path) != IFSelect_RetDone:
        raise RuntimeError("cannot read " + path)
    rd.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    free = TDF_LabelSequence()
    st.GetFreeShapes(free)
    out = []
    for i in range(1, free.Length() + 1):
        shp = st.GetShape_s(free.Value(i))
        BRepMesh_IncrementalMesh(shp, lin_defl, False, ang_defl, True)
        ex = TopExp_Explorer(shp, TopAbs_SOLID)
        solids = []
        while ex.More():
            solids.append(ex.Current())
            ex.Next()
        if not solids:
            solids = [shp]
        for so in solids:
            base = _col(ct, so)
            fe = TopExp_Explorer(so, TopAbs_FACE)
            while fe.More():
                f = TopoDS.Face_s(fe.Current())
                fe.Next()
                c = _col(ct, f) or base or (0.6, 0.6, 0.6)
                loc = TopLoc_Location()
                tri = BRep_Tool.Triangulation_s(f, loc)
                if tri is None:
                    continue
                tr = loc.Transformation()
                V = np.array([[tri.Node(k).Transformed(tr).X(), tri.Node(k).Transformed(tr).Y(), tri.Node(k).Transformed(tr).Z()] for k in range(1, tri.NbNodes() + 1)])
                T = np.array([[tri.Triangle(k).Value(1) - 1, tri.Triangle(k).Value(2) - 1, tri.Triangle(k).Value(3) - 1] for k in range(1, tri.NbTriangles() + 1)])
                if f.Orientation() == TopAbs_REVERSED:
                    T = T[:, ::-1]
                out.append((V, T, c))
    return out


def bounds(parts):
    V = np.vstack([p[0] for p in parts])
    return V.min(0), V.max(0)


if __name__ == "__main__":
    import sys
    from collections import Counter
    for p in sys.argv[1:]:
        parts = read_step(p)
        lo, hi = bounds(parts)
        cnt = Counter(tuple(round(v, 2) for v in c) for _v, _t, c in parts)
        print(p, len(parts), "faces", lo.round(2), hi.round(2), cnt.most_common(8))
