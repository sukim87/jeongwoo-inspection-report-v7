from datetime import date
from io import BytesIO
from pathlib import Path
import hashlib,streamlit as st
from PIL import Image,ImageOps
from modules.application_reader import read_application
from modules.report_text import make_draft
from modules.excel_writer import build_report
BASE=Path(__file__).resolve().parent
st.set_page_config(page_title='Jeongwoo AI 검사결과서 V7.2',page_icon='📋',layout='wide',initial_sidebar_state='expanded')
CODES=[('서류검토','DR'),('열처리','HT'),('재료검사','MI'),('조립검사','AS'),('마킹검사','MK'),('압력시험','PR'),('취부검사','FU'),('성능시험','PF'),('치수검사','DI'),('비파괴검사','NDE'),('외관검사','VI'),('도장/도금','PT'),('가공검사','MA'),('포장/출하','PK'),('성형검사','FM'),('용접검사','WD')]
st.markdown("""<style>html,body,[class*='css']{font-family:'Malgun Gothic','맑은 고딕',sans-serif!important}.block-container{max-width:1200px;padding-top:2.7rem!important}.hero{background:linear-gradient(110deg,#97001c,#d51c3f);color:white;border-radius:12px;padding:18px 22px}.head{background:#dedac8;border:1px solid #222;text-align:center;font-weight:800;padding:7px;margin-top:13px}.box{border:1px solid #222;border-top:0;padding:13px;background:white}label,.stButton button,.stDownloadButton button{font-weight:800!important}.side{background:white;border:1px solid #ddd;border-top:3px solid #c8102e;border-radius:8px;padding:13px;line-height:1.65;font-size:.84rem}</style>""",unsafe_allow_html=True)
with st.sidebar:
 st.image(str(BASE/'assets/jeongwoo_logo.jpg'),use_container_width=True)
 st.markdown("<div class='side'><b>☎ 시스템 문의 및 지원</b><br><br><b>부서:</b> PS품질팀<br><b>담당자:</b> 김선웅<br><b>이메일:</b> sukim1@jimc.co.kr<br><br><span style='color:#687078'>프로그램 오류, 기능 개선, 검사양식 및 입력항목 변경 요청</span></div><div style='color:#969ca5;font-size:.7rem;margin-top:15px'>ⓒ Jeongwoo Industrial Machine Co., Ltd.<br>All rights reserved.</div>",unsafe_allow_html=True)
st.markdown("<div class='hero'><b>AI로 더 빠르게 만드는 품질검사 결과서</b><br>검사신청서와 사진을 올리고 결과만 확인하세요. 입력 오타를 다듬어 검사 결과서를 작성합니다.</div>",unsafe_allow_html=True)

st.markdown("<div style='background:#fff;border:1px solid #d8dce2;border-left:5px solid #c8102e;border-radius:8px;padding:12px 15px;margin:12px 0 8px'><b>완성 결과서 샘플</b><br>결과서의 사진 배치와 전체 구성을 먼저 확인할 수 있습니다.</div>",unsafe_allow_html=True)
with st.expander('🖼 완성 결과서 샘플 예시 보기',expanded=False):
 sample_path=BASE/'assets/sample_result.png'
 if sample_path.exists():
  st.image(str(sample_path),caption='완성 검사결과서 샘플',use_container_width=True)
  st.caption('샘플 변경: assets/sample_result.png 파일을 같은 이름으로 교체하세요.')
 else:
  st.warning('assets 폴더에 sample_result.png 파일을 추가하세요.')
app=st.file_uploader('검사신청서 PDF 또는 Excel',type=['pdf','xlsx'])
if app:
 sig=hashlib.sha256(app.getvalue()).hexdigest()
 if st.session_state.get('sig')!=sig:
  info,pre=read_application(app)
  for k in ('customer','part_name','order_no','po_step_no','inspection_location'):st.session_state[k]=info.get(k,'')
  st.session_state.sig=sig;st.session_state.pre=pre
 st.success('확실한 기본정보를 자동 입력했습니다. 필요한 항목은 수정하세요.')
 if st.session_state.get('pre') is not None:
  with st.expander('방향 보정된 신청서'):st.image(st.session_state.pre,use_container_width=True)
st.markdown("<div class='head'>기본정보</div><div class='box'>",unsafe_allow_html=True)
a,b=st.columns(2);customer=a.text_input('고객사',key='customer');part=b.text_input('부품명 *',key='part_name')
a,b=st.columns(2);order=a.text_input('수주번호 *',key='order_no');po=b.text_input('발주/공정번호 *',key='po_step_no')
a,b=st.columns(2);inspection_location=a.text_input('검사장소',key='inspection_location',placeholder='신청서의 업체/팀명을 자동 입력하며, 없으면 직접 입력');inspector=b.text_input('검사자')
a,b=st.columns(2);seq=a.number_input('문서 순번',1,999,1);doc=f"IRR-{order or 'ORDER'}-{po or 'PO-STEP'}-{int(seq):03d}";b.text_input('문서번호',doc,disabled=True)
st.markdown('</div>',unsafe_allow_html=True)
st.markdown("<div class='head'>검사종류</div><div class='box'>",unsafe_allow_html=True)
cols=st.columns(4);selected=[]
for i,(n,c) in enumerate(CODES):
 x=f'{n} ({c})'
 if cols[i%4].checkbox(x,key=c):selected.append(x)
st.markdown('</div>',unsafe_allow_html=True)
st.markdown("<div class='head'>검사 기준 및 결과</div><div class='box'>",unsafe_allow_html=True)
rc=st.columns(4);refs=[]
for col,x in zip(rc,('도면','구매사양서','구매발주서','기타')):
 if col.checkbox(x,key='ref'+x):refs.append(x)
other=st.text_input('기타 기준문서 또는 불합격 상세기준');default=' / '.join(refs+([other] if other else []))
if st.button('선택한 확인문서를 검사기준에 적용',use_container_width=True):st.session_state.spec=default;st.rerun()
a,b=st.columns(2);spec=a.text_area('검사기준 *',key='spec');inspection_result=b.text_area('검사결과 *',key='inspection_result',placeholder='오타가 있어도 AI 초안 작성 시 교정됩니다.')
judgment=st.selectbox('판정',['합격','불합격','조건부 합격','N/A'])
st.markdown('</div>',unsafe_allow_html=True)
st.markdown("<div class='head'>검사사진</div><div class='box'>",unsafe_allow_html=True)
photos=st.file_uploader('사진 최대 8장',type=['jpg','jpeg','png'],accept_multiple_files=True);rots=[]
if photos:
 cs=st.columns(2)
 for i,p in enumerate(photos[:8]):
  with cs[i%2]:
   im=ImageOps.exif_transpose(Image.open(BytesIO(p.getvalue())));r=st.selectbox(f'사진 {i+1} 방향',['자동','오른쪽 90°','180°','왼쪽 90°'],key=f'r{i}');deg={'자동':0,'오른쪽 90°':90,'180°':180,'왼쪽 90°':270}[r];rots.append(deg)
   if deg:im=im.rotate(-deg,expand=True)
   st.image(im,use_container_width=True)
st.markdown('</div>',unsafe_allow_html=True)
for k in ('result','action','caption'):
 if k not in st.session_state:st.session_state[k]=''
st.markdown("<div class='head'>AI 검사결과 및 조치사항 미리보기</div><div class='box'>",unsafe_allow_html=True)
if st.button('✨ 오타 교정 후 AI 초안 작성',type='primary',use_container_width=True):
 r,a,c,cs,ci=make_draft(selected,spec,inspection_result,judgment,len(photos),inspection_location)
 st.session_state.result=r
 st.session_state.action=a
 st.session_state.caption=c
 st.session_state.corrected_spec=cs
 st.session_state.corrected_inspection_result=ci

if st.session_state.get('corrected_spec') or st.session_state.get('corrected_inspection_result'):
 st.markdown('**AI 오타 교정 결과**')
 cc1,cc2=st.columns(2)
 cc1.text_area('교정된 검사기준',value=st.session_state.get('corrected_spec',''),height=75,disabled=True)
 cc2.text_area('교정된 검사결과',value=st.session_state.get('corrected_inspection_result',''),height=75,disabled=True)

result=st.text_area('검사결과 문장',key='result')
action=st.text_area('조치요구',key='action')
caption=st.text_area('사진 설명',key='caption')
st.caption('교정된 문구를 확인한 뒤 Excel을 생성하세요. 원래 입력칸은 그대로 유지됩니다.')
st.markdown('</div>',unsafe_allow_html=True)
missing=[n for n,v in [('부품명',part),('수주번호',order),('발주/공정번호',po),('검사종류',selected),('검사기준',spec),('검사결과',inspection_result)] if not v]
if missing:st.warning('필수 입력: '+', '.join(missing))
if st.button('✅ V7.2 Excel 검사결과서 생성',type='primary',use_container_width=True,disabled=bool(missing)):
 final_spec=st.session_state.get('corrected_spec') or spec
 final_inspection_result=st.session_state.get('corrected_inspection_result') or inspection_result
 d={'customer':customer,'part_name':part,'order_no':order,'po_step_no':po,'inspector':inspector,'inspection_location':inspection_location,'date':date.today(),'doc':doc,'types':' / '.join(selected),'spec':final_spec,'inspection_result':final_inspection_result,'judgment':judgment,'result':result,'action':action,'caption':caption}
 st.session_state.out,st.session_state.name=build_report(d,photos[:8],rots)
if st.session_state.get('out'):st.download_button('📥 V7.2 Excel 검사결과서 다운로드',st.session_state.out,file_name=st.session_state.name,mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',type='primary',use_container_width=True)
