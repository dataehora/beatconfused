import pcbnew,sys
b=pcbnew.LoadBoard(sys.argv[1])
def mm(v): return round(pcbnew.ToMM(v),3)
for f in b.GetFootprints():
    print(f.GetReference(),f.GetFPIDAsString(),mm(f.GetX()-pcbnew.FromMM(10)),mm(f.GetY()-pcbnew.FromMM(17)),f.GetOrientationDegrees(),b.GetLayerName(f.GetLayer()))
    if f.GetReference() in sys.argv[2:]:
        for p in f.Pads():
            s=p.GetSize();print('   pad',p.GetNumber(),p.GetNetname(),mm(p.GetX()-pcbnew.FromMM(10)),mm(p.GetY()-pcbnew.FromMM(17)),mm(s.x),mm(s.y),p.GetAttribute(),mm(p.GetDrillSize().x))
print('zones',b.GetAreaCount())
for i in range(b.GetAreaCount()):
    z=b.GetArea(i);bb=z.GetBoundingBox();print(z.GetZoneName(),z.GetNetname(),z.GetIsRuleArea(),[b.GetLayerName(l) for l in z.GetLayerSet().Seq()],mm(bb.GetX()-pcbnew.FromMM(10)),mm(bb.GetY()-pcbnew.FromMM(17)),mm(bb.GetWidth()),mm(bb.GetHeight()))
print(b.GetBoardEdgesBoundingBox().GetWidth()/1e6)
ds=b.GetDesignSettings();print(ds.m_TrackMinWidth/1e6,ds.m_MinClearance/1e6,ds.GetCurrentTrackWidth()/1e6)
