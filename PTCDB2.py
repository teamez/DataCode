import os
import PyPDF2
import mysql.connector
import json
import pandas as pd
import re
import pdfplumber
import io
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
    "STONIC":"SUV",
    "아반떼NCN&":"승용",
    "스테리아":"MPV",
    "코나hev":"SUV"
    # 필요한 다른 차명과 차량 종류 추가
}

# PDF 파일들이 있는 폴더 경로
folder_path = "C:/Users/15936/OneDrive/바탕 화면/list2"
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

            # 판다스 출력 옵션 설정
            pd.set_option('display.max_columns', None)  # 모든 열을 표시
            pd.set_option('display.max_rows', None)  # 모든 행을 표시
            pd.set_option('display.max_colwidth', None)  # 각 셀의 내용을 생략하지 않고 표시

            # pdf 회전
            def rotate_page_and_extract_table(pdf_path, page_num, rotation_angle=90):
                # PyPDF2로 PDF 파일을 열고 페이지를 회전시킴
                with open(pdf_path, 'rb') as infile:
                    reader = PyPDF2.PdfReader(infile)
                    writer = PyPDF2.PdfWriter()
                    rotated_pdf_stream = io.BytesIO()

                    # 페이지 회전
                    page = reader.pages[page_num]
                    page.rotate(-rotation_angle)
                    writer.add_page(page)

                    # 회전된 PDF를 메모리 스트림에 저장
                    writer.write(rotated_pdf_stream)
                    rotated_pdf_stream.seek(0)

                # pdfplumber로 회전된 PDF에서 표 추출
                with pdfplumber.open(rotated_pdf_stream) as pdf:
                    page = pdf.pages[0]  # 회전된 페이지는 항상 첫 번째 페이지로 처리됨
                    table = page.extract_table()
                    return table

            def extract_tasks(combined_text):
                # 정규 표현식을 사용하여 '0km' 또는 '매'로 시작하는 패턴을 모두 추출
                pattern = r'(0km \w+|매\d+,\d+km \w+|매\d+km \w+)'
                matches = re.findall(pattern, combined_text)
                return ', '.join(matches)  # 리스트를 쉼표로 구분된 문자열로 변환

            file2="C:/Users/15936/OneDrive/바탕 화면/list2" +"/"+ file_name
            # PDF 파일 읽기
            pdf_reader = PyPDF2.PdfReader(open(file2, 'rb'))
            # 패턴 설정
            start_pattern = re.compile(r"통상 조건 점검 주기는")
            end_pattern = re.compile(r"짧은 거리를 반복적으로 주행")

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

            total_data = []
            # '○', '●' 추출
            for page_num in range(int(start_page), int(end_page)):
                tables_processed = []  # 완성본 넣는 리스트
                redata = []  # 데이터 안에 있는 다른페이지 헤더 삭제
                tables = rotate_page_and_extract_table(file2, page_num, rotation_angle=270)
                if tables:
                    # 첫 번째 행 검사
                    first_row = tables[0]
                    # print(first_row)
                    # "일일"이라는 문자열이 first_row 리스트의 어떤 요소에 포함되어 있는지 확인
                    if not any("일일" in cell for cell in first_row if cell is not None):
                        # 첫 번째 행에 "일일"이 없으면 첫 번째 행을 제거
                        cleaned_tables = tables[1:]
                    else:
                        # 첫 번째 행에 "일일"이 있으면 그대로 사용
                        cleaned_tables = tables
                    # print(cleaned_tables)  #['주행거리\n(km)', None, '일일\n점검', '1만', '2만', '3만', '4만', '6만', '8만', '10만', '12만', '14만', '16만'], [....
                    header = [cell.replace('\n', '') if cell else '' for cell in cleaned_tables[0]]
                    # print(header)
                    if '일일점검' in header:
                        index = header.index('일일점검')  # '일일점검' 위치 찾기
                        for row in cleaned_tables:
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
                            header = [col.replace('\n', '') if col is not None else '' for col in tables_processed[0]]
                            data = [[cell.replace('\n', '') if cell is not None else '' for cell in row] for row in
                                    tables_processed1[:]]
                        # print(header)
                        # print('data',data)
                        converted_data = []
                        for row in data:
                            item = row[0]
                            total = [f"{키로수}{점검상태}" if 점검상태 in ['○', '●'] else ''
                                     for 키로수, 점검상태 in zip(header[1:], row[1:])
                                     ]
                            converted_data.append([item, " ".join(total)])
                        total_data.append(converted_data)
            real_total_list = []
            for to in total_data:
                for too in to:
                    real_total_list.append(too)
            new_df = pd.DataFrame(real_total_list, columns=['점검항목', '키로수'])
            new_df = new_df.replace("○", " 점검 ", regex=True).replace("●", " 교환 ", regex=True).replace("일일점검", "0km",regex=True).replace("만", "0,000km", regex=True)

            # 문자추출
            total_data1 = []
            for page_num in range(int(start_page), int(end_page)):
                tables_processed = []  # 완성본 넣는 리스트
                redata = []  # 데이터 안에 있는 다른페이지 헤더 삭제
                tables = rotate_page_and_extract_table(file2, page_num, rotation_angle=270)

                if tables:
                    # 첫 번째 행 검사
                    first_row = tables[0]
                    # print(first_row)
                    # "일일"이라는 문자열이 first_row 리스트의 어떤 요소에 포함되어 있는지 확인
                    if not any("일일" in cell for cell in first_row if cell is not None):
                        # 첫 번째 행에 "일일"이 없으면 첫 번째 행을 제거
                        cleaned_tables = tables[1:]
                    else:
                        # 첫 번째 행에 "일일"이 있으면 그대로 사용
                        cleaned_tables = tables
                    # print(cleaned_tables)  #['주행거리\n(km)', None, '일일\n점검', '1만', '2만', '3만', '4만', '6만', '8만', '10만', '12만', '14만', '16만'], [....
                    header = [cell.replace('\n', '') if cell else '' for cell in cleaned_tables[0]]
                    # print(header)
                    if '일일점검' in header:
                        index = header.index('일일점검')  # '일일점검' 위치 찾기
                        for row in cleaned_tables:
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
                            header = [col.replace('\n', '') if col is not None else '' for col in tables_processed[0]]
                            data1 = [[cell.replace('\n', '') if cell is not None else '' for cell in row] for row in
                                     tables_processed1[:]]
                        # print(header)
                        # print('data',data1)
                        converted_data1 = []
                        for row in data1:
                            item = row[0]
                            total = [f"{점검상태}" for 점검상태 in row[1:]]
                            converted_data1.append([item, "".join(total)])
                        # print(converted_data1)
                        total_data1.append(converted_data1)
            real_total_list1 = []
            for to in total_data1:
                for too in to:
                    real_total_list1.append(too)
            # print(real_total_list1)
            new_df1 = pd.DataFrame(real_total_list1, columns=['점검항목', '키로수'])
            new_df1 = new_df1.replace("○", "", regex=True).replace("●", "", regex=True)
            new_df1 = new_df1.replace("상태에 따라 수시 ", "0km ", regex=True).replace("점검 및 조정", "점검", regex=True).replace(
                "매 12개월", "매 20,000km", regex=True)
            new_df1 = new_df1.replace("또는", "", regex=True).replace("마다", "", regex=True)
            new_df1 = new_df1.replace(r'\b(12|24|36|48|72)개월\b', '', regex=True).replace("48개월", "", regex=True)
            new_df1 = new_df1.replace("  ", " ", regex=True)
            # print(new_df1)

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

            ## maintenance_schedule1이 None일때  ** 다른 데이터 타입일때!! 318~544까지
            if maintenance_schedule1.empty :
                print("아무것도 없다.")
                with (pdfplumber.open('코나hev_2024.pdf') as pdf):
                    tables_processed = []  # 최종적으로 처리된 테이블을 저장할 리스트
                    for page_num in range(0, len(pdf.pages) - 1):
                        page = pdf.pages[page_num]
                        tables = page.extract_table()
                        text = page.extract_text()
                        # print(text)
                        # print(tables)
                        if tables:
                            # 첫 번째 행 검사
                            first_row = tables[0]
                            # print(first_row)
                            if "일일" not in first_row:
                                # 첫 번째 행에 "일일"이 없으면 첫 번째 행을 제거
                                cleaned_tables = tables[1:]
                            else:
                                # 첫 번째 행에 "일일"이 있으면 그대로 사용
                                cleaned_tables = tables
                            # print(cleaned_tables)  #['주행거리\n(km)', None, '일일\n점검', '1만', '2만', '3만', '4만', '6만', '8만', '10만', '12만', '14만', '16만'], [....
                            header = [cell.replace('\n', '') if cell else '' for cell in cleaned_tables[0]]
                            # print(header)
                            if '일일점검' in header:
                                index = header.index('일일점검')  # '일일점검' 위치 찾기
                                for row in cleaned_tables:
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
                                    header = [col.replace('\n', '') if col is not None else '' for col in
                                              tables_processed[0]]
                                    data = [[cell.replace('\n', '') if cell is not None else '' for cell in row] for row
                                            in tables_processed1[:]]
                                    # print(header)
                redata = []  # 데이터 안에 있는 다른페이지 헤더 삭제
                for data1 in data:
                    if data1 == header:
                        pass
                    else:
                        redata.append(data1)
                # print(redata)
                converted_data = []
                for row in redata:
                    item = row[0]
                    total = [f"{키로수}{점검상태}" if 점검상태 in ['○', '●'] else ''
                             for 키로수, 점검상태 in zip(header[1:], row[1:])
                             ]
                    converted_data.append([item, " ".join(total)])
                new_df = pd.DataFrame(converted_data, columns=['점검항목', '키로수'])
                if any('km' in header for header in header):
                    # 'km'이 포함된 경우
                    new_df = (
                        new_df.replace("○", " 점검 ", regex=True).replace("●", " 교환 ", regex=True).replace("일일점검", "0km",
                                                                                                         regex=True).replace(
                            "만", "0,000", regex=True))
                else:
                    # 'km'이 포함되지 않은 경우
                    new_df = (
                        new_df.replace("○", " 점검 ", regex=True).replace("●", " 교환 ", regex=True).replace("일일점검", "0km",
                                                                                                         regex=True).replace(
                            "만", "0,000km", regex=True))
                # print(new_df)

                # 문자 추출
                with (pdfplumber.open(file2) as pdf):
                    tables_processed2 = []  # 최종적으로 처리된 테이블을 저장할 리스트
                    for page_num in range(0, len(pdf.pages)):
                        page = pdf.pages[page_num]
                        tables = page.extract_table()
                        if tables:
                            # 첫 번째 행 검사
                            first_row = tables[0]
                            if "일일" not in first_row:
                                # 첫 번째 행에 "일일"이 없으면 첫 번째 행을 제거
                                cleaned_tables = tables[1:]
                            else:
                                # 첫 번째 행에 "일일"이 있으면 그대로 사용
                                cleaned_tables = tables
                            # print(cleaned_tables)  #['주행거리\n(km)', None, '일일\n점검', '1만', '2만', '3만', '4만', '6만', '8만', '10만', '12만', '14만', '16만'], [....
                            header = [cell.replace('\n', '') if cell else '' for cell in cleaned_tables[0]]
                            # print(header)
                            if '일일점검' in header:
                                index = header.index('일일점검')  # '일일점검' 위치 찾기
                                for row in cleaned_tables:
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
                                    tables_processed2.append(full_row[:])
                                    tables_processed3 = tables_processed2[1:]
                                    header = [col.replace('\n', '') if col is not None else '' for col in
                                              tables_processed2[0]]
                                    data = [[cell.replace('\n', '') if cell is not None else '' for cell in row] for row
                                            in tables_processed3[:]]
                redata1 = []  # 데이터 안에 있는 다른페이지 헤더 삭제
                for data1 in data:
                    if data1 == header:
                        pass
                    else:
                        redata1.append(data1)
                # 각 줄을 열 이름과 함께 변환
                converted_data1 = []
                for row in redata1:
                    item = row[0]
                    total = [f"{점검상태}" for 점검상태 in row[1:]]
                    converted_data1.append([item, "".join(total)])
                new_df1 = pd.DataFrame(converted_data1, columns=['점검항목', '키로수'])
                new_df1 = new_df1.replace("○", "", regex=True).replace("●", "", regex=True)
                new_df1 = new_df1.replace("상태에 따라 수시 ", "0km ", regex=True).replace("점검 및 조정", "점검",
                                                                                    regex=True).replace("매 12개월",
                                                                                                        "매 20,000km",
                                                                                                        regex=True)
                new_df1 = new_df1.replace("또는", "", regex=True).replace("마다", "", regex=True)
                new_df1 = new_df1.replace(r'\b(12|24|36|48|72)개월\b', '', regex=True).replace("48개월", "", regex=True)
                new_df1 = new_df1.replace("  ", " ", regex=True)
                new_df1 = new_df1.replace("0 km", "0km", regex=True)
                # print(new_df1)

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

            else:
                pass

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
            print("삽입완료")
        else:
            print(f"Unexpected format: {file_name}")
connection.commit()
print("레코드가 삽입되었습니다.")

cursor.close()
connection.close()


