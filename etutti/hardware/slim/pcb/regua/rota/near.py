import pcbnew,sys
b=pcbnew.LoadBoard(sys.argv[1]); x,y,r=map(float,sys.argv[2:5]); mm=1e-6
for t in b.GetTracks():
    if t.GetClass()=="PCB_VIA":
        p=t.GetPosition()
        if abs(p.x*mm-x)<r and abs(p.y*mm-y)<r: print("VIA",t.GetNetname(),p.x*mm,p.y*mm)
    else:
        a,e=t.GetStart(),t.GetEnd()
        if min(abs(a.x*mm-x),abs(e.x*mm-x))<r and min(abs(a.y*mm-y),abs(e.y*mm-y))<r: print("TR",t.GetNetname(),t.GetLayerName(),a.x*mm,a.y*mm,e.x*mm,e.y*mm,t.GetWidth()*mm)
