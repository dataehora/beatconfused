import pcbnew,sys
b=pcbnew.LoadBoard(sys.argv[1]); x0,x1=float(sys.argv[2]),float(sys.argv[3]); mm=1e-6
for fp in b.GetFootprints():
    for p in fp.Pads():
        bb=p.GetBoundingBox()
        if x0<=bb.GetX()*mm<=x1 or x0<=(bb.GetX()+bb.GetWidth())*mm<=x1:
            print("%-3s %-3s %-6s x %.3f..%.3f y %.3f..%.3f %s %s"%(fp.GetReference(),p.GetNumber(),p.GetNetname(),bb.GetX()*mm,(bb.GetX()+bb.GetWidth())*mm,bb.GetY()*mm,(bb.GetY()+bb.GetHeight())*mm,"npth" if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH else "", "drill%.2f"%(p.GetDrillSize().x*mm) if p.GetDrillSize().x else ""))
