def make_draft(types,spec,actual,judgment,count):
 title=' / '.join(types) if types else '검사'; result=''; action=''
 if spec or actual:
  result=f"{title} 결과, {actual or '확인 결과'}를 확인하였으며 적용 기준({spec or '기준 확인'})에 따른 최종 판정은 {judgment}임."
  action={'합격':'별도 조치사항 없음.','불합격':'부적합 부위를 수정·보수한 후 동일 기준으로 재검사하고 결과를 확인할 것.','조건부 합격':'지정된 보완사항을 완료하고 객관적 증빙 확인 후 최종 승인할 것.','N/A':'해당 없음.'}[judgment]
 return result,action,(f"사진 1~{count}: {title} 대상 및 확인 상태" if count else '')
