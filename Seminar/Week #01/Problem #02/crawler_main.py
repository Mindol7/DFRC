# Date: 2026/01/10
# Author: Jo Minhyuk
# IDE & Execution environment: VS Code (WSL2 - Ubuntu 22.04)
# Execution method: python3 crawler_main.py 

import os
import time
import json
import pandas as pd
import matplotlib.pyplot as plt
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from wordcloud import WordCloud

# --- STEP 1. 환경 설정---
CHROME_OPTIONS = Options()
CHROME_OPTIONS.add_argument("--headless") # 백그라운드 실행
CHROME_OPTIONS.add_argument("--no-sandbox") # 리눅스/WSL 환경에서 크롬이 죽는 문제 방지
CHROME_OPTIONS.add_argument("--disable-dev-shm-usage") # ''
CHROME_OPTIONS.add_argument("--lang=ko_KR")
CHROME_OPTIONS.add_argument("window-size=1920x1080") # 창 크기 고정
CHROME_OPTIONS.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

CHROME_OPTIONS.add_experimental_option("excludeSwitches", ["enable-automation"]) # 자동화 봇 차단 방지
CHROME_OPTIONS.add_experimental_option('useAutomationExtension', False)

def get_driver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=CHROME_OPTIONS)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    print("Step 1: 환경 설정 완료")
    return driver

# --- STEP 2. 기사 수집 ---
def collect_list(driver):
    print("Step 2: 뉴스 목록 수집 중...")
    url = "https://news.naver.com/breakingnews/section/105/732?date=20251212"
    driver.get(url)
    
    while True:
        try:
            more_btn = WebDriverWait(driver, 1.5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".section_more_inner")))
            driver.execute_script("arguments[0].click();", more_btn)
            time.sleep(1.2) # 로딩을 위해 1.2초 대기
        except:
            break

    soup = BeautifulSoup(driver.page_source, 'html.parser') # 현재 페이지의 HTML
    articles = soup.select('.sa_text') # 각 뉴스 카드 영역 선택
    news_list = []
    for art in articles:
        title_el = art.select_one('.sa_text_title') # 기사 제목
        press_el = art.select_one('.sa_text_press') # 언론
        if title_el:
            news_list.append({
                '제목': title_el.get_text(strip=True),
                '언론사': press_el.get_text(strip=True) if press_el else "N/A",
                'URL': title_el['href']
            })
    
    pd.DataFrame(news_list).to_csv("news_list.csv", index=False, encoding='utf-8-sig')
    print(f"Step 2 완료: 총 {len(news_list)} 개의 기사 수집됨.")
    return news_list

# --- STEP 3. 댓글 목록 분석 ---
def analyze_comments(driver, news_list):
    print("Step 3: 댓글 분석 시작")
    final_data = []
    
    for idx, item in enumerate(news_list):
        driver.get(item['URL'])
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(0.5)
        
        comment_count = 0
        selectors = [".media_end_head_comment_count_text", ".u_cbox_count", ".head_comment_count"]
        
        found = False
        for selector in selectors:
            try:
                el = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                
                txt = el.text.strip()
                count_str = ''.join(filter(str.isdigit, txt))
                if count_str and count_str != "0":
                    comment_count = int(count_str)
                    found = True
                    break

                if found: break
            except:
                continue
            
        item['댓글수'] = comment_count
        final_data.append(item)
        print(f"[{idx+1}/{len(news_list)}] {comment_count}개 : {item['제목'][:20]}...")

    # 가장 댓글 많은 기사 정보 수집 및 JSON 저장
    sorted_news = sorted(final_data, key=lambda x: x['댓글수'], reverse=True)
    best = sorted_news[0]
    
    driver.get(best['URL'])
    
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5) # 로딩 대기 시간 확보
    
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".u_cbox_cnt_recomm"))
        )
    except:
        print("공감 수 요소를 찾지 못했습니다.")

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    body_text = soup.select_one('#newsct_article').get_text(strip=True, separator='\n') if soup.select_one('#newsct_article') else ""
    
    all_recomm_elements = driver.find_elements(By.CSS_SELECTOR, ".u_cbox_cnt_recomm")
    all_comment_elements = driver.find_elements(By.CSS_SELECTOR, ".u_cbox_contents")
    total_recomm_sum = 0
    max_recomm = -1

    for recomm_el, content_el in zip(all_recomm_elements, all_comment_elements):
        try:
            recomm_val = int(recomm_el.text) if recomm_el.text else 0
            total_recomm_sum += recomm_val
            
            if recomm_val > max_recomm:
                max_recomm = recomm_val
                best_comment_text = content_el.text
        except:
            continue

    try:
        best_comment_el = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.u_cbox_contents"))
        )
        best_comment_text = best_comment_el.text
    except:
        best_comment_text = "베스트 댓글이 없거나 로딩되지 않았습니다."

    result_json = {
        "제목": best['제목'],
        "기자명": soup.select_one('.media_end_head_journalist_name').get_text(strip=True) if soup.select_one('.media_end_head_journalist_name') else "정보없음",
        "입력 시간": soup.select_one('.media_end_head_info_dateline_time')['data-date-time'] if soup.select_one('.media_end_head_info_dateline_time') else "정보없음",
        "공감 수": total_recomm_sum,
        "댓글 수": best['댓글수'],
        "기사": best['제목'],
        "첫 문단 본문": body_text.split('\n')[0] if body_text else "",
        "가장 공감을 많이 받은 댓글 본문": best_comment_text
    }
    
    with open("best_article.json", "w", encoding="utf-8") as f:
        json.dump(result_json, f, ensure_ascii=False, indent=4)
    
    return sorted_news

# --- STEP 4. 워드클라우드 생성 ---
def make_wordcloud(driver, news_list):
    print("Step 4: 워드클라우드 생성 중...")
    combined_content = ""
    target_news = [n for n in news_list if n.get('댓글수', 0) >= 10]
    
    for item in target_news:
        driver.get(item['URL'])
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        art_body = soup.select_one('#newsct_article')
        if art_body:
            combined_content += art_body.get_text(strip=True) + " "

    if combined_content.strip():
        f_path = os.path.join(os.getcwd(), "NanumGothic.ttf")
        
        if not os.path.exists(f_path):
            f_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

        try:
            wc = WordCloud(
                font_path=str(f_path),
                width=1200, 
                height=800, 
                background_color='white',
                collocations=False
            ).generate(combined_content)
            
            plt.figure(figsize=(12, 8))
            plt.imshow(wc, interpolation='bilinear')
            plt.axis('off')
            plt.savefig("wordcloud_result.png")
            print("성공: wordcloud_result.png가 생성되었습니다.")
        except Exception as e:
            print(f"에러 상세: {e}")
            # 만약 실패하면 텍스트 파일로라도 저장해서 데이터 확인
            with open("news_text.txt", "w", encoding="utf-8") as f:
                f.write(combined_content)
            print("워드클라우드 실패로 텍스트만 news_text.txt에 저장했습니다.")
    else:
        print("조건 만족 기사 없음")
        
if __name__ == "__main__":
    my_driver = get_driver()
    try:
        list_data = collect_list(my_driver)
        analyzed_data = analyze_comments(my_driver, list_data)
        make_wordcloud(my_driver, analyzed_data)
    finally:
        my_driver.quit()