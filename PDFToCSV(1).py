from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTTextLine, LTPage
import pandas as pd
import re

def extract_text_by_columns(pdf_path):
    columns_text = []
    for page_layout in extract_pages(pdf_path):
        left_column, right_column = [], []
        page_width = page_layout.width
        mid_point = page_width / 2

        # 페이지 내 모든 텍스트 박스를 순회하며 왼쪽과 오른쪽 컬럼 분류
        for element in page_layout:
            if isinstance(element, LTTextBox):
                if element.bbox[0] < mid_point:  # x 좌표가 중간점보다 작으면 왼쪽 컬럼
                    left_column.append(element.get_text())
                else:                           # 그렇지 않으면 오른쪽 컬럼
                    right_column.append(element.get_text())

        # 각 컬럼의 텍스트를 페이지 별로 저장
        columns_text.append((left_column, right_column))

    return columns_text
def interleave_columns(columns_text):
    interleaved_text = []
    # 모든 페이지의 컬럼 데이터를 번갈아 가며 합치기
    for left, right in columns_text:
        interleaved_text.extend(left)
        interleaved_text.extend(right)

    return interleaved_text

# PDF 파일 경로
pdf_path = 'C:/Users/15936/PycharmProjects/pythonProject/K5 500h(하이브리드) 2013 0.pdf'
columns_text = extract_text_by_columns(pdf_path)
final_text = interleave_columns(columns_text)
text=''
# 최종 텍스트 출력
for textt in final_text:
    # print(text)
    text += textt

pattern = re.compile(r"일일 점검 항목(.*?)가혹 조건", re.DOTALL)
match = pattern.search(text)

if match:
    text1 = match.group(1)
    # 모든 줄바꿈을 공백으로 대체한 후
    text = re.sub(r'\n', ' ', text1)
    # print(text)
    text = "일일 점검 항목" + text
    # print(text)
    text = text.replace("12개월 마다 점검 항목", '20,000km 점검 항목')
    text = text.replace("□점검", " ")  # 10년 자료중에 구분한 pdf가 있어서 정규식으로 가기위한 통일
    text = text.replace("□교체", " ")  # 10년 자료중에 구분한 pdf가 있어서 정규식으로 가기위한 통일
    text = text.replace(":", "")  # 10년 자료중에 구분한 pdf가 있어서 정규식으로 가기위한 통일
    text = text.replace("•", "□ ")  # 10년 자료중에 구분한 pdf가 있어서 정규식으로 가기위한 통일
    text = text.replace("□□□□", "□ ")  # 10년 자료중에 구분한 pdf가 있어서 정규식으로 가기위한 통일
    text = text.replace("□", "□ ")  # 10년 자료중에 구분한 pdf가 있어서 정규식으로 가기위한 통일
    # print(text)
    text = re.sub(r'\*\s*(\d)', r'*\1', text)  # * 기호와 숫자 사이의 공백 제거 (떨어져있는 *와 숫자 연결)
    # text = re.sub(r'\*\d+', '', text)  # * 기호와 숫자만 제거(점검항목에 있는 *+숫자 삭제)
    text = re.sub(r'무점검.*', '', text)
    # print(text)
    text = re.sub(r'□', '\n□', text)
    # print(text)
    # 정규식을 사용하여 특정 패턴 앞에 줄바꿈 추가
    pattern = r'(\s*\d{1,3}(?:,\d{3})+km 점검 항목)'
    text = re.sub(pattern, r'\n\1', text, flags=re.IGNORECASE)
    # print(text)
    # *와 ※ 뒤의 텍스트 삭제
    text = re.sub(r'\*.*\n?', '\n', text)
    text = re.sub(r'※.*\n?', '\n', text)
    text = re.sub(r'\�.*\n?', '\n', text)
    # print(text)
    # km당 점검항목으로 행열 만들기 위해 글자 통일
    text = text.replace("일일 점검 항목", '0,000KM 점검 항목')
    # print(text)
    # KM 점검 항목과 세부 항목 추출
    pattern = re.compile(r'(\d{1,3}(?:,\d{3})+KM 점검 항목)([\s\S]*?)(?=\d{1,3}(?:,\d{3})+KM 점검 항목|\Z)', re.IGNORECASE)

    # 추출한 섹션을 파싱
    sections = pattern.findall(text)
    # 세부 항목과 제목을 저장할 딕셔너리 초기화
    item_dict = {}
    # 각 점검 항목별로 세부 사항 처리 및 출력
    for section in sections:
        title = section[0]  # 점검 항목 제목
        items_text = section[1]  # 해당 점검 항목의 세부 항목 텍스트
        items = re.findall(r'□ (.*?)(?=\n□ |\n\n|\Z|\□ )', items_text, re.S)  # 세부 항목 추출

        # print("{" + title + "}")  # 점검 항목 타이틀 출력
        for item in items:  # 개행 문자가 중간에 있을 경우 이어 붙이기
            item = ' '.join(item.split('\n')).strip()
            # print(f"{item}")
            if item not in item_dict:
                item_dict[item] = {}
            if "점검" in item:
                item_dict[item][title] = 1  # 교환이 포함된 항목에 대해 title에 2 할당
            elif "교환" in item or "교체" in item:
                item_dict[item][title] = 2  # 점검이 포함된 항목에 대해 title에 1 할당
            else:
                item_dict[item][title] = 1  # 기본적으로 title에 1 할당
    # 데이터 프레임 생성
    df = pd.DataFrame.from_dict(item_dict, orient='index').fillna(0).astype(int)
    # 제목에서 "점검 항목" 제거하고 숫자 부분만 추출하여 정렬
    df.columns = [title.replace('점검 항목', '').strip() for title in df.columns]

    # 제목을 숫자로 변환하여 정렬 기준으로 사용
    title_order = {title: int(re.sub(r'[^0-9]', '', title)) for title in df.columns}
    df = df.sort_index(axis=1, key=lambda x: x.map(title_order))

    # 열 이름 설정 (첫 번째 열 이름을 '항목'으로 설정)
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'inspect_Item'}, inplace=True)

    pd.DataFrame(df).to_csv('20240701.csv', index=False)