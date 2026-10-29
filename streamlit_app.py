from datetime import date
from io import BytesIO
from pathlib import Path
import hashlib
import streamlit as st
from PIL import Image,ImageOps
from modules.application_reader import read_application
from modules.report_text import make_draft
from modules.excel_writer import build_report
BASE=Path(__file__).resolve().parent
st.set_page_config(page_title='Jeongwoo AI 검사결과서 V7',page_icon='📋',layout='wide')
CODES=[('서류검토','DR'),('열처리','HT'),('재료검사','MI'),('조립검사','AS'),('마킹검사','MK'),('압력시험','PR'),('취부검사','FU'),('성능시험','PF'),('치수검사','DI'),('비파괴검사','NDE'),('외관검사','VI'),('도장/도금','PT'),('가공검사','MA'),('포장/출하','PK'),('성형검사','FM'),('용접검사','WD')]
EX={'치수검사':('500 ±2 mm','500.8 mm'),'외관검사':('승인도면 및 외관기준','손상·부식·변형 없음'),'도장/도금':('DFT Min. 320 μm','256 / 267 / 258 μm'),'압력시험':('15 bar / 30 min','15 bar 유지, 누설 없음')}
st.markdown("""<style>html,body,[class*='css']{font-family:'Malgun Gothic','맑은 고딕',sans-serif!important}.block-container{max-width:1200px;padding-top:2.7rem!important}.hero{background:linear-gradient(110deg,#97001c,#d51c3f);color:white;border-radius:12px;padding:18px 22px}.hero b{font-size:1.3rem}.head{background:#dedac8;border:1px solid #222;text-align:center;font-weight:800;padding:7px;margin-top:13px}.box{border:1px solid #222;border-top:0;padding:13px;background:white}.stButton button,.stDownloadButton button{font-weight:800}label{font-weight:800!important}</style>""",unsafe_allow_html=True)
st.markdown("<div class='hero'><b>AI로 더 빠르게 만드는 품질검사 결과서</b><br>검사신청서와 사진을 올리고 결과만 확인하세요. 핵심 내용을 정리해 새 V7 Excel 양식으로 작성합니다.</div>",unsafe_allow_html=True)
st.subheader('1. 검사신청서 불러오기')
app=st.file_uploader('기존/신규 검사신청서 PDF 또는 Excel',type=['pdf','xlsx'])
if app:
 sig=hashlib.sha256(app.getvalue()).hexdigest()
 if st.session_state.get('appsig')!=sig:
  try:
   info,preview=read_application(app)
   for k in ('customer','part_name','order_no','po_step_no'): st.session_state[k]=info.get(k,'')
   st.session_state.appsig=sig; st.session_state.preview=preview
   names={'customer':'고객사','part_name':'부품명','order_no':'수주번호','po_step_no':'발주/공정번호'}; review=info.get('review_fields',[])
   st.session_state.msg='확실한 기본정보를 자동 입력했습니다.'+((' 확인 필요: '+', '.join(names[x] for x in review)) if review else '')
  except Exception as e: st.session_state.msg=f'신청서 판독 실패: {e}'
 st.success(st.session_state.get('msg',''))
 if st.session_state.get('preview') is not None:
  with st.expander('방향 보정된 신청서 미리보기'): st.image(st.session_state.preview,use_container_width=True)
st.markdown("<div class='head'>기본정보</div><div class='box'>",unsafe_allow_html=True)
a,b=st.columns(2); customer=a.text_input('고객사',key='customer'); part=b.text_input('부품명 *',key='part_name')
a,b=st.columns(2); order=a.text_input('수주번호 *',key='order_no'); po=b.text_input('발주/공정번호 *',key='po_step_no')
a,b=st.columns(2); inspector=a.text_input('검사자'); seq=b.number_input('문서 순번',1,999,1)
doc=f"IRR-{order or 'ORDER'}-{po or 'PO-STEP'}-{int(seq):03d}"; st.text_input('문서번호',doc,disabled=True)
st.markdown('</div>',unsafe_allow_html=True)
st.markdown("<div class='head'>검사종류</div><div class='box'>",unsafe_allow_html=True)
cols=st.columns(4); selected=[]
for i,(name,code) in enumerate(CODES):
 label=f'{name} ({code})'
 if cols[i%4].checkbox(label,key=code): selected.append(label)
st.markdown('</div>',unsafe_allow_html=True)
primary=selected[0].split(' (')[0] if selected else '치수검사'; sex,aex=EX.get(primary,('적용 기준','측정/확인 결과'))
st.markdown("<div class='head'>검사 기준 및 결과</div><div class='box'>",unsafe_allow_html=True)
st.markdown('**합격 시 기본 확인문서**')
rc=st.columns(4); refs=[]
for col,label in zip(rc,('도면','구매사양서','구매발주서','기타')):
 if col.checkbox(label,key='ref_'+label): refs.append(label)
other=st.text_input('기타 기준문서 또는 불합격 상세기준',placeholder='불합격이면 허용기준, 규격, 도면번호 등을 상세 입력')
def_ref=' / '.join(refs+([other] if other else []))
if st.button('선택한 기본 확인문서를 검사기준에 적용',use_container_width=True): st.session_state.spec=def_ref; st.rerun()
a,b=st.columns(2)
if a.button('검사기준 예시 적용',use_container_width=True): st.session_state.spec=sex; st.rerun()
if b.button('측정결과 예시 적용',use_container_width=True): st.session_state.actual=aex; st.rerun()
a,b=st.columns(2); spec=a.text_area('검사기준 *',placeholder=sex,key='spec'); actual=b.text_area('측정결과 *',placeholder=aex,key='actual')
judgment=st.selectbox('판정',['합격','불합격','조건부 합격','N/A'])
st.markdown('</div>',unsafe_allow_html=True)
st.markdown("<div class='head'>검사사진</div><div class='box'>",unsafe_allow_html=True)
photos=st.file_uploader('사진 최대 8장',type=['jpg','jpeg','png'],accept_multiple_files=True); rotations=[]
if photos:
 cs=st.columns(2)
 for i,p in enumerate(photos[:8]):
  with cs[i%2]:
   im=ImageOps.exif_transpose(Image.open(BytesIO(p.getvalue()))); r=st.selectbox(f'사진 {i+1} 방향',['자동','오른쪽 90°','180°','왼쪽 90°'],key=f'r{i}'); deg={'자동':0,'오른쪽 90°':90,'180°':180,'왼쪽 90°':270}[r]; rotations.append(deg)
   if deg: im=im.rotate(-deg,expand=True)
   st.image(im,use_container_width=True)
st.markdown('</div>',unsafe_allow_html=True)
for k in ('result','action','caption'):
 if k not in st.session_state: st.session_state[k]=''
st.markdown("<div class='head'>AI 검사결과 및 조치사항 미리보기</div><div class='box'>",unsafe_allow_html=True)
if st.button('✨ AI 검사결과 초안 작성',type='primary',use_container_width=True): st.session_state.result,st.session_state.action,st.session_state.caption=make_draft(selected,spec,actual,judgment,len(photos))
result=st.text_area('검사결과',key='result'); action=st.text_area('조치요구',key='action'); caption=st.text_area('사진 설명',key='caption')
st.markdown('</div>',unsafe_allow_html=True)
with st.expander('완성 샘플 예시 보기'):
 sample=BASE/'assets/sample_result.png'
 if sample.exists(): st.image(str(sample),use_container_width=True)
missing=[n for n,v in [('부품명',part),('수주번호',order),('발주/공정번호',po),('검사종류',selected),('검사기준',spec),('측정결과',actual)] if not v]
if missing: st.warning('필수 입력: '+', '.join(missing))
if st.button('✅ V7 Excel 검사결과서 생성',type='primary',use_container_width=True,disabled=bool(missing)):
 d={'customer':customer,'part_name':part,'order_no':order,'po_step_no':po,'inspector':inspector,'report_date':date.today(),'document_no':doc,'inspection_type':' / '.join(selected),'specification':spec,'actual':actual,'judgment':judgment,'result':result,'action':action,'caption':caption}
 st.session_state.out,st.session_state.name=build_report(d,photos[:8],rotations)
if st.session_state.get('out'):
 st.success('V7 검사결과서가 완성되었습니다.')
 st.download_button('📥 V7 Excel 검사결과서 다운로드',st.session_state.out,file_name=st.session_state.name,mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',type='primary',use_container_width=True)
