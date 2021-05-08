
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
import re
import datetime
from bs4 import BeautifulSoup
import config


def loadDetail(detailUrl):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('disable-infobars')
    options.add_argument('--lang=zh-CN')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])

    prefs = {
        'profile.default_content_setting_values': {
            'images': 2,  # 禁用图片的加载
        }
    }
    options.add_experimental_option("prefs", prefs)

    # # 在linux上需要添加一下两个参数
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    browser = Chrome(options=options)
    browser.set_page_load_timeout(45)
    browser.set_script_timeout(45)

    try:
        browser.get(detailUrl)
        page_source = browser.page_source

    except:
        print('加载超时')
        pass

    browser.quit
    if page_source != None:
        return page_source


def parsDetail(source_code):
    htmlSoup = BeautifulSoup(source_code, 'html.parser')
    titles = htmlSoup.find('div',attrs={'class':'a-section',
                                        'id':'productDetails_db_sections'
                                        })

    tableSuop = BeautifulSoup(str(titles),'html.parser')
    table = tableSuop.find('table')


    trSuop = BeautifulSoup(str(table),'html.parser')
    tr_arr = trSuop.find_all('tr')


    for tr_title in tr_arr:
        titleSuop = BeautifulSoup(str(tr_title),'html.parser')
        strdiv = str(titleSuop.find('th').contents[0])

        strdiv = strdiv.strip()

        regFloat = re.compile('[^\d+\,\d+]')
        cop = re.compile("[^\u4e00-\u9fa5^a-z^A-Z^0-9]")

        if strdiv == 'Amazon Bestseller-Rang':
            if len(titleSuop.find_all('span')) > 1:
                spans = titleSuop.find_all('span')
                spans.pop(0)
                print(spans )
                for span in spans:
                    span = str(span)
                    spanlist = span.split(' in ')
                    span = regFloat.sub('', str(spanlist[0]))
                    span = cop.sub('',span)
                    print(span)
                    if int(span) > config.AWZ_Max_distanceDate :
                        print('排名太后')
                        return False
            else:
                return False

        elif strdiv == 'Im Angebot von Amazon.de seit':

            timeValue = str(titleSuop.find('td').contents[0])
            timeValue = timeValue.strip()
            timeFloat = re.compile('[.]')
            timeValue = timeFloat.sub('', timeValue)

            now = datetime.datetime.now()

            regFloat = re.compile('[.]')
            timeValue = regFloat.sub('', timeValue)

            timelist = timeValue.split(' ')
            # Januar, Februar , März , April , Mai , Juni , Juli , August , September , Oktober , November , Dezember
            time_dict = {'Januar': '01', 'Februar': '02', 'März': '03', 'April': '04', 'Mai': '05',
                         'Juni': '06', 'Juli': '07', 'August': '08', 'September': '09', 'Oktober': '10',
                         'November': '11', 'Dezember': '12'}

            mothkey = str(timelist[1])
            if mothkey in time_dict.keys():
                timelist[1] = time_dict[mothkey]
                timeValue = ' '.join(timelist)

                pass

            timelist = timeValue.split(' ')
            # Jan , Feb , Mär , Apr , Mai , Jun , Jul , Aug , Sep , Okt , Nov , Dez
            time_dict = {'Jan': '01', 'Feb': '02', 'Mär': '03', 'Apr': '04', 'Mai': '05', 'Jun': '06', 'Jul': '07',
                         'Aug': '08', 'Sep': '09', 'Okt': '10', 'Nov': '11', 'Dez': '12'}
            mothkey = str(timelist[1])
            if mothkey in time_dict.keys():
                timelist[1] = time_dict[mothkey]
                timeValue = ' '.join(timelist)
                pass

            dt = datetime.datetime.strptime(timeValue, "%d %m %Y")
            days = now - dt
            print("相差：" + str(days.days))

            if days.days > config.AWZ_Max_distanceDate :
                return False

    return True


if __name__ == '__main__':
    page_source = loadDetail('https://www.amazon.de/TSG-Downhill-MTB-Helm-Graphic-Design/dp/B0899GXFKW/ref=zg_bs_189731031_26?_encoding=UTF8&psc=1&refRID=ZJ2SZERZZ0ZR1W23ZS55')
    print( parsDetail(page_source) )