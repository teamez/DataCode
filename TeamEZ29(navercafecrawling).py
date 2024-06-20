from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd

linkss=[]
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
# "제네시스 고질병","제네시스 단점","제네시스 고장","제네시스 문제","제네시스 현상","제네시스 품질","제네시스 리콜""제네시스 소음", "제네시스 소리","제네시스 경고등","제네시스 불편","제네시스 결함"  "g70 고질병","g70 단점","g70 고장","g70 문제","g70 현상","g70 품질","g70 리콜","g70 소음",
crlist=["g70 소리"]
for gg in crlist:
    try:
        url = f"https://search.naver.com/search.naver?ssc=tab.cafe.all&sm=tab_jum&query=+{gg}"
        driver.get(url)

        # 스크롤을 내릴 웹 요소(예: body) 찾기
        body = driver.find_element(By.TAG_NAME, "body")

        # 스크롤을 끝까지 내리는 반복 작업
        while True:
            # 이전 페이지 높이 저장
            last_height = driver.execute_script("return document.body.scrollHeight")

            # 끝까지 스크롤 다운
            for i in range(10):
                body.send_keys(Keys.END)
                time.sleep(2)  # 로딩 대기

            # 새로운 페이지 높이를 가져와 이전 페이지 높이와 비교
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # 스크롤 완료 후, 페이지의 링크 추출
        links = driver.find_elements(By.CSS_SELECTOR, "a.title_link")
        for link in links:
            url = link.get_attribute('href')  # href 속성 추출
            # print(url)  # URL 출력
            linkss.append(url)
    finally:
        driver.quit()

    # 추출된 링크들에 대한 세부 정보를 저장할 리스트
    article_details = []
    titles=[]
    ggs=[]
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    # 각 링크에 대해서 페이지 내용을 추출합니다.
    for link in linkss:
        driver.get(link)
        try:
            # iframe 전환
            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[id='cafe_main']"))
            )
            # 요소 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".ArticleContentBox"))
            )
            content_box = driver.find_element(By.CSS_SELECTOR, ".article_viewer")
            title = driver.find_element(By.CLASS_NAME, "title_text")
            ggs.append(gg)
            print(title.text)
            print(content_box.text)  # 내용 출력
            titles.append(title.text)
            article_details.append(content_box.text)
            time.sleep(2)
        except Exception as e:
            print(f"Error processing link {link}: {e}")
        finally:
            driver.switch_to.default_content()
    s00 = pd.Series(ggs,name='검색어')
    s01 = pd.Series(titles,name="제목")
    s1 = pd.Series(article_details, name='상세내용')
    s2 = pd.Series(linkss, name='링크')
    result = pd.concat([s00,s01,s1, s2], axis=1)

    # CSV 파일로 저장
    pd.DataFrame(result).to_csv(f'navercafeCrawling({gg}).csv', index=False)