from flask import Blueprint, render_template, request
import requests
from bs4 import BeautifulSoup as bs

test_module = Blueprint("test_module", __name__)

@test_module.route("/currency", methods=["POST"])
def get_ex_rate():
    headers = {   #로봇 아님
        "User-Agent": "Mozilla/5.0",
        "Content-Type" : "text/html; charset=utf-8"
    }

    response1 = requests.get("https://kr.investing.com/currencies/exchange-rates-table" headers=headers)
    print(response1)
  #현제 사이트의 상태 확인 출력
    content1 = bs(response1.content, 'html.parser')


    krw = content1.select("#container > div.aside > div:nth-child(2) > table > tbody > tr:nth-child(1) > td:nth-child(3)")


    return render_template("test_result.html", krwwon=krw[0].text, jpyyen=yen[0].text, eureuro=euro[0].text)


select_name = ["영국 파운드/달러", "유로/달러"]

def return_value(address, addition):
    res = requests.get(address +addition)
    soup = bs(res.content, 'html.parser')

    frame = soup.find('iframe', id="frame_ex2")
    frameaddr = address+frame['src'] #frame내의 연결된 주소 확인 

    res1 = requests.get(frameaddr) # frame내의 연결된 주소를 읽어오기 
    frame_soup = bs(res1.content, 'html.parser')
    items = frame_soup.select('body > div > table > tbody > tr')


    for item in items:
        name = item.select('td')[0].text.replace("\n","")
        name = name.replace("\t", "")
        if (name in select_name): print(item.select('td')[2].text)
        
baseaddress = 'https://finance.naver.com'
info = '/marketindex/?tabSel=worldExchange#tab_section'
return_value(baseaddress, info)