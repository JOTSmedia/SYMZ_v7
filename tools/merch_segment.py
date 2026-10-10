# Per-item outlines for the merch lineup (SAM vit-b ONNX via rembg). Writes one mask PNG per item; shapes.json is made from them.
"""Per-item masks for the merch lineup with SAM (vit-b onnx from rembg): one encoder pass, a decoder pass per item."""
import json, numpy as np, onnxruntime as ort, cv2
from PIL import Image
M='/root/.rembg/models/sam/'
enc=ort.InferenceSession(M+'sam_vit_b_01ec64.encoder.onnx'); dec=ort.InferenceSession(M+'sam_vit_b_01ec64.decoder.onnx')
img=np.array(Image.open('/home/claude/symz/img/merch/merch-lineup.jpg').convert('RGB')); H,W=img.shape[:2]
IH,IW=684,1024; s=min(IW/W,IH/H)
canvas=np.zeros((IH,IW,3),np.float32); rs=cv2.resize(img,(round(W*s),round(H*s)),interpolation=cv2.INTER_AREA); canvas[:rs.shape[0],:rs.shape[1]]=rs
emb=enc.run(None,{enc.get_inputs()[0].name:canvas})[0]
items=json.load(open('/tmp/claude-0/scratch/merch_items.json'))
EXTRA={'keychain-round':[[515,870,0],[540,905,0]]}
import sys
if len(sys.argv)>1: items=[i for i in items if i[0] in sys.argv[1:]]
out={}
for it in items:
    key=it[0]; x0,y0,x1,y1=it[3]; hx,hy=it[4]
    pts=[[hx,hy],[x0,y0],[x1,y1]]; lab=[1,2,3]
    for ex in EXTRA.get(key,[]): pts.append(ex[:2]); lab.append(ex[2])
    c=np.array(pts+[[0,0]],np.float32)*s; l=np.array(lab+[-1],np.float32)
    m,iou,_=dec.run(None,{'image_embeddings':emb,'point_coords':c[None],'point_labels':l[None],'mask_input':np.zeros((1,1,256,256),np.float32),'has_mask_input':np.zeros(1,np.float32),'orig_im_size':np.array([IH,IW],np.float32)})
    mk=(m[0,0,:rs.shape[0],:rs.shape[1]]>0).astype(np.uint8)*255
    mk=cv2.resize(mk,(W,H),interpolation=cv2.INTER_LINEAR); mk=(mk>127).astype(np.uint8)
    n,lbl,st,_=cv2.connectedComponentsWithStats(mk)
    keep=np.zeros_like(mk)
    for i in range(1,n):
        if st[i,cv2.CC_STAT_AREA]>800 or lbl[min(H-1,int(hy)),min(W-1,int(hx))]==i: keep[lbl==i]=1
    cv2.imwrite(f'/tmp/claude-0/scratch/msam/{key}.png',keep*255)
    out[key]=float(iou.ravel()[0]); print(key,round(out[key],3),int(keep.sum()),flush=True)
