
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from xlutils.copy import copy as xl_copy
import re
import datetime
from bs4 import BeautifulSoup
import config
import xlrd
import np
import time
import random
import sys


def loadDetail(detailUrl):
    options = Options()
    # options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('disable-infobars')
    options.add_argument('--lang=zh-CN')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])

    prefs = {
        'profile.default_content_setting_values': {
            'images': 2,  # 禁用图片的加载
        }
    }
    # options.add_experimental_option("prefs", prefs)

    # # 在linux上需要添加一下两个参数
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    browser = Chrome(options=options)
    browser.set_page_load_timeout(45)
    browser.set_script_timeout(45)
    source_code = ''
    try:
        browser.get(detailUrl)
        source_code = browser.page_source
    except:
        print("加载超时" + str(detailUrl))
        pass

    browser.quit
    if source_code != '':
        return source_code
    else:
        return False


def parsDetail(source_code):
    htmlSoup = BeautifulSoup(source_code, 'html.parser')

    yanzhenArr = htmlSoup.find_all('div',attrs={'class':'a-container a-padding-double-large'})
    if len(yanzhenArr) > 0:
        print('遇到人机验证')
        sys.exit(1)

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



def checkExceltoUrls(Excelname):
    exceldata = xlrd.open_workbook(Excelname, formatting_info=True)
    allSheet = exceldata._sheet_names

    if 'okUrlSheet' in allSheet:
        wb = xl_copy(exceldata)
    else:
        wb = xl_copy(exceldata)
        wb.add_sheet('okUrlSheet')
        wb.save(Excelname)

    exceldata = xlrd.open_workbook(Excelname, formatting_info=True)
    openUrlSheet = exceldata.sheet_by_name('openUrlSheet')
    openUrlArr = openUrlSheet.col_values(0, 0)

    cahetable = exceldata.sheet_by_name('caheIdSheet')
    caheArr = cahetable.col_values(1, 0)
    print(caheArr)
    if len(caheArr)>0:
        caheUrlStr = str(caheArr[0])
        if caheUrlStr == '':return openUrlArr
        else:
            index = openUrlArr.index(caheUrlStr)
            openUrlArr = np.array(openUrlArr)
            openUrlArr = openUrlArr[index:]
            print('当前违章'+str(index))
            return openUrlArr
    else:
        print('没有换成')
        return openUrlArr


def writeCaheURL(Excelname,caheUrl):
    xlsData = xlrd.open_workbook(Excelname, formatting_info=True)
    wb = xl_copy(xlsData)
    caheIdSheet = wb.get_sheet(3)
    caheIdSheet.write(0, 1, caheUrl)
    wb.save(Excelname)

def writeTheURLWithOk(Excelname,caheUrl):
    xlsData = xlrd.open_workbook(Excelname, formatting_info=True)
    sheeet = xlsData.sheet_by_name('okUrlSheet')
    inNcs = len(sheeet.col(0))

    wb = xl_copy(xlsData)
    okUrlSheet = wb.get_sheet(4)
    okUrlSheet.write(inNcs, 0, str(caheUrl))
    wb.save(Excelname)

if __name__ == '__main__':

    # print('检查完成')
    # sys.exit(1)
    # print('检查完成')

    urlArr = checkExceltoUrls(config.AWZ_Excelname)
    for urlStr  in urlArr:
        time.sleep(random.randint(2, 5))
        writeCaheURL(config.AWZ_Excelname,urlStr)
        page_source = loadDetail(urlStr)

        if page_source == False:
            continue
        else:
            urlISOK = parsDetail(page_source)
            if urlISOK == True:
                writeTheURLWithOk(config.AWZ_Excelname,urlStr)
                print('符合')
            else:
                print('不符合')
                continue



    print('检查完成')
