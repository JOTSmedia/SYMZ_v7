import cv2, numpy as np, json, sys
im=cv2.imread(sys.argv[1],cv2.IMREAD_UNCHANGED)          # keyed logo, BGRA
b,g,r,a=[im[...,i].astype(float) for i in range(4)]
S=4
def contours(mask,mode=cv2.RETR_CCOMP):
    m=cv2.resize(mask.astype(np.uint8)*255,None,fx=S,fy=S,interpolation=cv2.INTER_CUBIC)
    m=cv2.GaussianBlur(m,(5,5),0);_,m=cv2.threshold(m,127,255,cv2.THRESH_BINARY)
    cs,h=cv2.findContours(m,mode,cv2.CHAIN_APPROX_NONE)
    out=[]
    for c in cs:
        if cv2.contourArea(c)<30*S: continue
        c=cv2.approxPolyDP(c,1.2,True)
        if len(c)>=3: out.append([[float(p[0][0])/S,float(p[0][1])/S] for p in c])
    return out
op=a>110
red=op&(r>g*1.6)&(r>90)
white=op&~red&(np.minimum(np.minimum(r,g),b)>120)
k=np.ones((3,3),np.uint8)
red=cv2.morphologyEx(red.astype(np.uint8),cv2.MORPH_CLOSE,k)>0
white=cv2.morphologyEx(white.astype(np.uint8),cv2.MORPH_CLOSE,k)>0
union=(red|white).astype(np.uint8)
back=cv2.dilate(union,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(41,41)))>0
back=cv2.morphologyEx(back.astype(np.uint8),cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(61,61)))>0
H,W=a.shape
json.dump({'W':W,'H':H,'red':contours(red),'white':contours(white),'back':contours(np.pad(back,30),cv2.RETR_EXTERNAL),'pad':30},open(sys.argv[2],'w'))
print(W,H,{k:len(v) for k,v in json.load(open(sys.argv[2])).items() if isinstance(v,list)})
