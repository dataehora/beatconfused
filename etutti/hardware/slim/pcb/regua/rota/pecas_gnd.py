import pcbnew,sys
b=pcbnew.LoadBoard(sys.argv[1]); mm=1e-6
gnd=b.FindNet("GND").GetNetCode()
for z in b.Zones():
    if z.GetIsRuleArea(): continue
    L=z.GetLayer(); ps=z.GetFilledPolysList(L)
    for i in range(ps.OutlineCount()):
        s=pcbnew.SHAPE_POLY_SET(); s.AddOutline(ps.COutline(i))
        nv=sum(1 for t in b.GetTracks() if t.GetClass()=="PCB_VIA" and t.GetNetCode()==gnd and s.Collide(t.GetPosition(),10))
        npad=[(fp.GetReference(),p.GetNumber()) for fp in b.GetFootprints() for p in fp.Pads() if p.GetNetCode()==gnd and p.IsOnLayer(L) and s.Collide(p.GetPosition(),10)]
        bb=s.BBox()
        print(z.GetZoneName(), "peca",i,"bbox %.1f %.1f %.1f x %.1f"%(bb.GetX()*mm,bb.GetY()*mm,bb.GetWidth()*mm,bb.GetHeight()*mm),"vias",nv,"pads",npad[:6])
