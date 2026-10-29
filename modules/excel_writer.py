from io import BytesIO
from pathlib import Path
import re,tempfile
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as XLImage
from PIL import Image,ImageOps
TEMPLATE=Path(__file__).resolve().parents[1]/'templates'/'검사결과서.xlsx'
SLOTS=[('검사결과서','A21'),('검사결과서','G21'),('검사결과서(을지)','A11'),('검사결과서(을지)','G11'),('검사결과서(을지)','A24'),('검사결과서(을지)','G24'),('검사결과서(을지)','A37'),('검사결과서(을지)','G37')]
def safe(v): return re.sub(r'[\\/:*?"<>|]+','-',str(v or '미입력')).strip()
def build_report(d,photos,rotations):
 wb=load_workbook(TEMPLATE); q=wb['간편입력']; main=wb['검사결과서']; extra=wb['검사결과서(을지)']
 vals={'B5':d['customer'],'B6':d['part_name'],'B7':d['order_no'],'B8':d['po_step_no'],'B9':d['report_date'],'B10':d['inspection_type'],'B11':d['specification'],'B14':d['actual'],'B15':d['judgment'],'B16':'','B17':d['result'],'B18':d['action'],'B19':d['caption'],'B20':d['inspector']}
 for c,v in vals.items(): q[c]=v
 q['B9'].number_format='yyyy-mm-dd'
 m={'J3':d['document_no'],'C5':d['customer'],'I5':d['inspection_type'],'C6':d['part_name'],'I6':d['po_step_no'],'C7':d['order_no'],'I7':d['report_date'],'A11':d['specification'],'F11':d['actual'],'J11':d['judgment'],'C13':d['result'],'C16':d['action'],'A33':d['caption'],'A37':d['inspector'],'J37':d['judgment']}
 for c,v in m.items(): main[c]=v
 for c,v in {'J3':d['document_no'],'C5':d['customer'],'I5':d['inspection_type'],'C6':d['part_name'],'I6':d['po_step_no'],'C7':d['order_no'],'I7':d['report_date']}.items(): extra[c]=v
 main['I7'].number_format=extra['I7'].number_format='yyyy-mm-dd'
 for ws in (main,extra): ws._images=[]
 for c in ('A21','G21'): main[c]=''
 for c in ('A11','G11','A24','G24','A37','G37'): extra[c]=''
 with tempfile.TemporaryDirectory() as td:
  for i,u in enumerate(photos[:8]):
   u.seek(0); im=ImageOps.exif_transpose(Image.open(u)).convert('RGB'); deg=rotations[i] if i<len(rotations) else 0
   if deg: im=im.rotate(-deg,expand=True)
   im=ImageOps.fit(im,(1406,1000),Image.Resampling.LANCZOS,centering=(.5,.5)); p=f'{td}/{i}.jpg'; im.save(p,quality=91)
   x=XLImage(p); x.width=405; x.height=288; wb[SLOTS[i][0]].add_image(x,SLOTS[i][1])
  out=BytesIO(); wb.save(out)
 return out.getvalue(),f"{safe(d['order_no'])}_{safe(d['inspection_type'])}_{d['report_date']:%Y%m%d}.xlsx"
