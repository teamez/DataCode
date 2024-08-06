import os
import PyPDF2
import mysql.connector
import json
# MySQL 데이터베이스에 연결
connection = mysql.connector.connect(
    host='db-ojmb8-kr.vpc-pub-cdb.ntruss.com',
    user='teamez',
    password='',
    database='ptc'
)
cursor = connection.cursor()
# 차명과 차량 종류를 매핑하는 딕셔너리
car_type_mapping = {
    "쏘나타": "승용",
    "스포티지": "SUV",
    "아반떼": "승용",
    "올 뉴 카렌스": "SUV",
    "K5 500h(하이브리드)":"승용",
    "K9":"승용",
    "모하비":"SUV",
    "SOUL BOOSTER":"SUV",
    "STONIC":"SUV"
    # 필요한 다른 차명과 차량 종류 추가
}

# PDF 파일들이 있는 폴더 경로
folder_path = "C:/Users/15936/OneDrive/바탕 화면/list"
# 폴더 내의 모든 파일을 순회
for file_name in os.listdir(folder_path):
    if file_name.endswith(".pdf"):  # PDF 파일만 처리
        # 파일 이름에서 확장자를 제거하고 언더스코어(_)를 기준으로 분리
        file_name_parts = os.path.splitext(file_name)[0].split("_")
        print(file_name)
        # 파일 이름이 예상한 형식을 따를 경우 정보 추출
        if len(file_name_parts) == 2:
            car_name, year = file_name_parts
            car_type = car_type_mapping.get(car_name, "Unknown")  # 차명에 따라 차량 종류를 매핑, 없으면 "Unknown"
            info_dict = {
                "car_name": car_name,
                "car_type": car_type,
                "year": year
            }
            from pdfminer.high_level import extract_pages
            from pdfminer.layout import LTTextBox, LTTextLine, LTPage
            import pandas as pd
            import re

            # 판다스 출력 옵션 설정
            pd.set_option('display.max_columns', None)  # 모든 열을 표시
            pd.set_option('display.max_rows', None)  # 모든 행을 표시
            pd.set_option('display.max_colwidth', None)  # 각 셀의 내용을 생략하지 않고 표시

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
                            else:  # 그렇지 않으면 오른쪽 컬럼
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
            pdf_path = folder_path+'/'+file_name
            columns_text = extract_text_by_columns(pdf_path)
            final_text = interleave_columns(columns_text)
            text = ''
            # 최종 텍스트 출력
            for textt in final_text:
                text += textt

            pattern = re.compile(r"일일 점검 항목(.*?)가혹 조건", re.DOTALL)
            match = pattern.search(text)
            if match:
                text1 = match.group(1)
                # 모든 줄바꿈을 공백으로 대체한 후
                text = re.sub(r'\n', ' ', text1)
                text = "일일 점검 항목" + text
                text = text.replace("12개월 마다 점검 항목", '20,000km 점검 항목')
                text = text.replace("□점검", " ")  # 10년 자료중에 구분한 pdf가 있어서 정규식으로 가기위한 통일
                text = text.replace("□교체", " ")  # 10년 자료중에 구분한 pdf가 있어서 정규식으로 가기위한 통일
                text = text.replace(":", "")  # 10년 자료중에 구분한 pdf가 있어서 정규식으로 가기위한 통일
                text = text.replace("•", "□ ")  # 10년 자료중에 구분한 pdf가 있어서 정규식으로 가기위한 통일
                text = text.replace("□□□□", "□ ")  # 10년 자료중에 구분한 pdf가 있어서 정규식으로 가기위한 통일
                text = text.replace("□", "□ ")  # 10년 자료중에 구분한 pdf가 있어서 정규식으로 가기위한 통일
                text = re.sub(r'\*\s*(\d)', r'*\1', text)  # * 기호와 숫자 사이의 공백 제거 (떨어져있는 *와 숫자 연결)
                # text = re.sub(r'\*\d+', '', text)  # * 기호와 숫자만 제거(점검항목에 있는 *+숫자 삭제)
                text = re.sub(r'무점검.*', '', text)
                text = re.sub(r'□', '\n□', text)
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
                pattern = re.compile(r'(\d{1,3}(?:,\d{3})+KM 점검 항목)([\s\S]*?)(?=\d{1,3}(?:,\d{3})+KM 점검 항목|\Z)',
                                     re.IGNORECASE)

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

                sql = "insert into CarInspect (num,CarSize,CarName,CarYear,InspectItem,CheckByDistance) values (%s,%s,%s,%s,%s,%s)"
                # 각 행을 반복하며 데이터베이스에 삽입
                for i, (index, row) in enumerate(df.iterrows()):
                    remaining_columns = row.iloc[1:]  # 현재 행의 나머지 열
                    # 현재 행의 인덱스와 나머지 열을 포함한 JSON 형식으로 변환
                    remaining_columns_dict = remaining_columns.to_dict()
                    remaining_columns_json = pd.Series(remaining_columns_dict).to_json()
                    val = (i,car_type,car_name,year,row['inspect_Item'], remaining_columns_json)
                    cursor.execute(sql, val)


            if match==None:
                print("매km로 반복 표 확인")
                # pdf 필요한 파일 페이지 찾기
                import PyPDF2
                import re
                file2="C:/Users/15936/OneDrive/바탕 화면/list" +"/"+ file_name
                # PDF 파일 읽기
                pdf_reader = PyPDF2.PdfReader(open(file2, 'rb'))
                # 패턴 설정
                start_pattern = re.compile(r"통상조건")
                end_pattern = re.compile(r"가혹조건")

                # 패턴이 있는 페이지 번호 찾기
                start_page = None
                end_page = None
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    # "통상조건"이 있는 마지막 페이지 찾기
                    if start_pattern.search(page_text):
                        start_page = page_num + 1  # 페이지 번호는 1부터 시작하므로 +1
                    # "가혹조건"이 있는 마지막 페이지 찾기
                    if end_pattern.search(page_text):
                        end_page = page_num + 1  # 페이지 번호는 1부터 시작하므로 +1

                # '○', '●' 변환
                import pdfplumber


                def extract_tasks(combined_text):
                    # 정규 표현식을 사용하여 '0km' 또는 '매'로 시작하는 패턴을 모두 추출
                    pattern = r'(0km \w+|매\d+,\d+km \w+|매\d+km \w+)'
                    matches = re.findall(pattern, combined_text)
                    return ', '.join(matches)  # 리스트를 쉼표로 구분된 문자열로 변환


                # PDF 파일 열기
                with pdfplumber.open(file2) as pdf:
                    tables_processed = []  # 최종적으로 처리된 테이블을 저장할 리스트
                    # 10페이지부터 13페이지까지 순회(추후 텍스트를 통해서 페이지를 찾아내는 코드 사용예정)
                    for page_num in range(int(start_page), int(end_page) - 1):  # 페이지 인덱스는 0부터 시작하므로 9에서 시작
                        # print(page_num)
                        page = pdf.pages[page_num]
                        tables = page.extract_tables()  # 페이지에서 테이블 추출
                        # print(tables)
                        for table in tables:
                            # 테이블이 비어있지 않은지 확인
                            if len(table) > 1:  # 최소 두 줄 이상인 경우 처리
                                # "일일 점검"이 포함된 행을 찾기 위한 함수
                                def find_header_with_check(table):
                                    for row in table:
                                        if "일일점검" in row:
                                            return [cell.replace('\n', '') if cell else '' for cell in row]
                                        # "일일 점검"이 포함된 행이 없을 경우 첫 번째 행을 기본 헤더로 사용
                                        return None
                                header = find_header_with_check(table)
                                if header is None:  # "일일 점검"이 포함된 행이 없으면 두 번째 행을 헤더로 사용
                                    if len(table) > 1:  # 두 번째 행이 존재하는지 확인
                                        header = [cell.replace('\n', '') if cell else '' for cell in table[1]]
                                # print(header)
                                if '일일점검' in header:
                                    index = header.index('일일점검')  # '일일점검' 위치 찾기
                                    for row in table:
                                        # 일일점검 앞쪽 부분에서 빈 값 채우기
                                        before_daily = []
                                        for i in range(index):
                                            cell = row[i] if row[i] else ''
                                            before_daily.append(cell.replace('\n', ' '))  # 줄바꿈 문자를 공백으로 대체
                                        # 일일점검 포함 이후 데이터 처리, '-'와 None을 빈칸으로 대체
                                        after_daily = [cell if cell and cell != '-' else '' for cell in row[index:]]
                                        # before_daily_check의 각 행을 하나의 문자열로 합치기
                                        before_daily_string = " ".join(before_daily).strip()
                                        # before_daily_check 문자열과 after_daily_check 리스트를 하나의 리스트로 결합
                                        full_row = [before_daily_string] + after_daily
                                        # 나눈 데이터를 최종 리스트에 추가
                                        tables_processed.append(full_row[:])
                                        tables_processed1 = tables_processed[1:]
                            else:
                                pass
                tables_processed1[0] = [cell.replace('\n', '') if cell is not None else '' for cell in
                                        tables_processed1[0]]  # 줄바꿈 삭제
                all_data = []
                if tables_processed:
                    header = [col.replace('\n', '') if col is not None else '' for col in tables_processed1[0]]
                    data = [[cell.replace('\n', '') if cell is not None else '' for cell in row] for row in
                            tables_processed1[1:]]
                    # 각 줄을 열 이름과 함께 변환
                    converted_data = []
                    for row in data:
                        item = row[0]
                        total = [f"{키로수}{점검상태}" if 점검상태 in ['○', '●'] else ''
                                 for 키로수, 점검상태 in zip(header[1:], row[1:])
                                 ]
                        converted_data.append([item, " ".join(total)])
                    all_data += converted_data
                new_df = pd.DataFrame(all_data, columns=['점검항목', '키로수'])
                new_df = new_df.replace("○", " 점검 ", regex=True).replace("●", " 교환 ", regex=True).replace("일일점검", "0km",
                                                                                                          regex=True)
                # '키로수' 열에서 작업을 추출
                new_df['키로수'] = new_df['키로수'].apply(extract_tasks)

                # 문자추출
                import pdfplumber
                # PDF 파일 열기
                with pdfplumber.open(file2) as pdf:
                    tables_processed2 = []  # 최종적으로 처리된 테이블을 저장할 리스트
                    # 10페이지부터 13페이지까지 순회
                    for page_num in range(int(start_page), int(end_page) - 1):  # (추후 텍스트를 통해서 페이지를 찾아내는 코드 사용예정)
                        page = pdf.pages[page_num]
                        tables = page.extract_tables()  # 페이지에서 테이블 추출
                        for table in tables:
                            # 테이블이 비어있지 않은지 확인
                            if len(table) > 1:  # 최소 두 줄 이상인 경우 처리
                                # "일일 점검"이 포함된 행을 찾기 위한 함수
                                def find_header_with_check(table):
                                    for row in table:
                                        if "일일점검" in row:
                                            return [cell.replace('\n', '') if cell else '' for cell in row]
                                        # "일일 점검"이 포함된 행이 없을 경우 첫 번째 행을 기본 헤더로 사용
                                        return None
                                header = find_header_with_check(table)
                                if header is None:  # "일일 점검"이 포함된 행이 없으면 두 번째 행을 헤더로 사용
                                    if len(table) > 1:  # 두 번째 행이 존재하는지 확인
                                        header = [cell.replace('\n', '') if cell else '' for cell in table[1]]
                                if '일일점검' in header:
                                    index = header.index('일일점검')  # '일일점검' 위치 찾기
                                    for row in table:
                                        # 일일점검 앞쪽 부분에서 빈 값 채우기
                                        before_daily = []
                                        for i in range(index):
                                            cell = row[i] if row[i] else ''
                                            before_daily.append(cell.replace('\n', ' '))  # 줄바꿈 문자를 공백으로 대체
                                        # 일일점검 포함 이후 데이터 처리, '-'와 None을 빈칸으로 대체
                                        after_daily = [cell if cell and cell != '-' else '' for cell in row[index:]]
                                        # before_daily_check의 각 행을 하나의 문자열로 합치기
                                        before_daily_string = " ".join(before_daily).strip()
                                        # before_daily_check 문자열과 after_daily_check 리스트를 하나의 리스트로 결합
                                        full_row = [before_daily_string] + after_daily
                                        # print(full_row)
                                        # 나눈 데이터를 최종 리스트에 추가
                                        tables_processed2.append(full_row[:])
                                        tables_processed3 = tables_processed2[1:]
                            else:
                                pass
                tables_processed3[0] = [cell.replace('\n', '') if cell is not None else '' for cell in
                                        tables_processed3[0]]  # 줄바꿈 삭제
                all_data1 = []
                if tables_processed3:
                    header = [col.replace('\n', '') if col is not None else '' for col in tables_processed3[0]]
                    data = [[cell.replace('\n', '').replace('○', '').replace('●', '').replace('매 ',
                                                                                              '매') if cell is not None else ''
                             for
                             cell in row] for row in tables_processed1[1:]]
                    # 각 줄을 열 이름과 함께 변환
                    converted_data = []
                    for row in data:
                        item = row[0]
                        total = [f"{점검상태}" for 점검상태 in row[1:]]
                        converted_data.append([item, "".join(total)])
                    all_data1 += converted_data
                new_df1 = pd.DataFrame(all_data1, columns=['점검항목', '키로수'])
                new_df1 = new_df1.replace("상태에 따라 수시 ", "0km ", regex=True).replace("점검 및 조정", "점검",regex=True).replace("매12개월","매20,000km",regex=True)
                new_df1 = new_df1.replace("또는", "", regex=True).replace("마다", "", regex=True)
                new_df1 = new_df1.replace(r'\b(12|24|36|48|72)개월\b', '', regex=True).replace("48개월", "", regex=True)
                new_df1 = new_df1.replace(
                    "일일점검매10,000km매20,000km매30,000km매40,000km매60,000km매80,000km매100,000km매120,000km매140,000km매160,000km"," ", regex=True)
                new_df1 = new_df1.replace("  ", " ", regex=True)

                # # #합치기
                # new_df1의 두 번째 열만 선택
                selected_column = new_df1.iloc[:, 1]
                # 새로운 열 이름 지정
                selected_column.name = '키로수2'
                # new_df와 선택한 열을 옆으로 붙임
                result_df = pd.concat([new_df, selected_column], axis=1)
                result_df['combined'] = result_df['키로수'].astype(str).str.strip() + ' ' + result_df['키로수2'].astype(
                    str).str.strip()
                result_df = result_df.drop(columns=['키로수', '키로수2'])
                # "combined" 열에서 콤마만 있는 행 삭제
                result_df = result_df[result_df['combined'].str.strip() != ' ']

                # '점검항목' 열에서 NaN, 빈 문자열, '주행거리 점검항목' 값을 가지는 행을 필터링
                filtered_df = result_df[~(result_df['점검항목'].isna() |
                                          (result_df['점검항목'] == '') |
                                          (result_df['점검항목'] == '주행거리 점검항목'))]
                # 인덱스를 재설정하여 빈 공간이 없도록 함
                filtered_df.reset_index(drop=True, inplace=True)

                # 모든 리스트의 값들을 하나의 집합으로 결합
                all_intervals = set()
                tasks = {}
                max_km = 160000  # 최대 km 설정

                for index, row in filtered_df.iterrows():
                    tasks[row['점검항목']] = {}
                    # 0km 점검을 명시적으로 확인
                    zero_km_check = re.search(r'(^|\s)0km\s+점검($|\s|,|\.|;)?', row['combined'])
                    if zero_km_check:
                        all_intervals.add(0)
                        tasks[row['점검항목']][0] = 1
                        # 특정 단어가 포함되어 있으면 패스
                        if re.search(r'최초\s+교환', row['combined']):
                            continue
                        # 0km 점검 이후의 조건을 처리
                        remaining_string = row['combined'][zero_km_check.end():]
                        # 복합 조건 파싱
                        matches = re.finditer(r'(?<!최초\s)매\s*([\d,]+) km\s+ +.*?(점검|교체|교환)', remaining_string)
                        for match in matches:
                            interval = int(match.group(1).replace(',', ''))
                            if interval == 0:  # 간격이 0인 경우는 스킵
                                continue
                            task_type = match.group(2)
                            task_value = 1 if task_type == '점검' else 2  # 점검은 1, 교체/교환은 2
                            # 모든 필요한 간격 추가
                            for km in range(interval, max_km + 1, interval):
                                tasks[row['점검항목']][km] = task_value
                                all_intervals.add(km)
                    # 복합 조건 최초 설정 파싱
                    first_match = re.search(r'최초\s*([\d,]+)km\s*점검\s*이후\s*매\s*([\d,]+)km.*?점검', row['combined'],
                                            re.IGNORECASE)
                    if first_match:
                        first_interval = int(first_match.group(1).replace(',', ''))
                        repeat_interval = int(first_match.group(2).replace(',', ''))
                        tasks[row['점검항목']][first_interval] = 1  # 최초 점검
                        for km in range(first_interval + repeat_interval, max_km + 1, repeat_interval):
                            tasks[row['점검항목']][km] = 1
                            all_intervals.add(km)
                    else:
                        # 일반적인 경우 파싱
                        matches = re.finditer(r'(?<!최초)([\d,]+)km\s+.*?(점검|교체|교환)', row['combined'])
                        for match in matches:
                            interval = int(match.group(1).replace(',', ''))
                            if interval == 0:  # 간격이 0인 경우는 스킵
                                continue
                            task_type = match.group(2)
                            task_value = 1 if task_type == '점검' else 2  # 점검은 1, 교체/교환은 2

                            # 모든 필요한 간격 추가
                            for km in range(interval, max_km + 1, interval):
                                tasks[row['점검항목']][km] = task_value
                                all_intervals.add(km)
                sorted_intervals = sorted(all_intervals)
                # 2차원 데이터 테이블 생성
                maintenance_schedule1 = pd.DataFrame(index=filtered_df['점검항목'], columns=sorted_intervals).fillna(0)
                for item, values in tasks.items():
                    for km, val in values.items():
                        maintenance_schedule1.at[item, km] = val
                # print(maintenance_schedule1)
                # 열 이름에 "KM" 접미사 추가
                maintenance_schedule1.columns = [str(col) + 'KM' for col in maintenance_schedule1.columns]
                sql = "insert into CarInspect (num,CarSize,CarName,CarYear,InspectItem,CheckByDistance) values (%s,%s,%s,%s,%s,%s)"
                # 각 행을 반복하며 데이터베이스에 삽입
                for i, (index, row) in enumerate(maintenance_schedule1.iterrows()):
                    remaining_columns = row.iloc[:]  # 현재 행의 나머지 열
                    # 현재 행의 인덱스와 나머지 열을 포함한 JSON 형식으로 변환
                    remaining_columns_dict = remaining_columns.to_dict()
                    remaining_columns_json = pd.Series(remaining_columns_dict).to_json()
                    val = (i, car_type, car_name, year,index, remaining_columns_json)
                    cursor.execute(sql, val)
        else:
            print(f"Unexpected format: {file_name}")
connection.commit()
print("레코드가 삽입되었습니다.")

cursor.close()
connection.close()