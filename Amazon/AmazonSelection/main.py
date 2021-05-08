# 这是一个示例 Python 脚本。

# 按 ⌃R 执行或将其替换为您的代码。
# 按 Double ⇧ 在所有地方搜索类、文件、工具窗口、操作和设置。
import config
import requests
from bs4 import BeautifulSoup
from xlutils.copy import copy as xl_copy
import xlrd
import np
import re
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
import time
import random


# 获取
def checkExceltoIDs(Excelname, idSheetName):
    exceldata = xlrd.open_workbook(Excelname, formatting_info=True)
    allSheet = exceldata._sheet_names

    if 'openUrlSheet' in allSheet:
        wb = xl_copy(exceldata)
    else:
        wb = xl_copy(exceldata)
        wb.add_sheet('openUrlSheet')
        wb.add_sheet('caheIdSheet')
        wb.save(Excelname)

    exceldata = xlrd.open_workbook(Excelname, formatting_info=True)
    id_Sheet = exceldata.sheet_by_name(idSheetName)
    id_Arr = id_Sheet.col_values(0, 1)
    caheid_Sheet = exceldata.sheet_by_name('caheIdSheet')
    caheid_Arr = caheid_Sheet.col_values(0, 0)

    print(len(caheid_Arr))

    if len(caheid_Arr) > 0:
        caheid_num = float(caheid_Arr[0])
        index = id_Arr.index(caheid_num)
        id_Arr = np.array(id_Arr)
        id_Arr = id_Arr[index:]

    # 返回还未检查id数组
    return id_Arr


# 加载品类id bestseller 列表数据
# def loadTheid(Excelname,categoryId):
#     print(categoryId)
#     #替换缓存id
#     exceldata = xlrd.open_workbook(Excelname, formatting_info=True)
#     wb = xl_copy(exceldata)
#     caheIdSheet = wb.get_sheet(3)
#     caheIdSheet.write(0, 0, categoryId)
#     wb.save(Excelname)
#     openUrl = config.AWZ_HOST + config.AWZ_PATH + str(int(categoryId))
#     responseHtml = requests.get(openUrl)
#     return responseHtml

def loadTheidbrowser(Excelname, categoryId):
    exceldata = xlrd.open_workbook(Excelname, formatting_info=True)
    wb = xl_copy(exceldata)
    caheIdSheet = wb.get_sheet(3)
    caheIdSheet.write(0, 0, categoryId)
    wb.save(Excelname)
    openUrl = config.AWZ_HOST + config.AWZ_PATH + str(int(categoryId))

    ismain = False
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

    # 在linux上需要添加一下两个参数
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    browser = Chrome(options=options)
    browser.set_page_load_timeout(45)
    browser.set_script_timeout(45)
    source_code = ''
    try:
        browser.get(openUrl)
        source_code = browser.page_source
    except:
        print("加载超时" + str(categoryId))
        pass

    browser.quit
    if source_code != '':
        return source_code
    else:
        return False


# 解析beastseller列表数据
def parsingHtml(responseHtml):
    # htmlSoup =  BeautifulSoup(responseHtml.content, 'lxml')
    htmlSoup = BeautifulSoup(responseHtml, 'html.parser')
    titles = htmlSoup.find_all('div', attrs={'class': 'a-section a-spacing-none aok-relative'})

    if len(titles) <= 0:
        return False

    print('此id下共有' + str(len(titles)) + "个商品")
    i = 0
    for titleCell in titles:
        i += 1
        if i > config.AWZ_Max_index: return False  # 只检查前20个商品,超出范围退出
        if i > len(titles) - 1: return False  # 只检查前20个商品,超出范围退出
        print('\n' + '第' + str(i) + '商品')
        _parsCell(titleCell)


# 解析具体某个商品
def _parsCell(titleCell):
    cellSoup = BeautifulSoup(str(titleCell), 'html.parser')
    # 排名

    # 跟卖
    linkUrl = cellSoup.find('a', attrs={'class': 'a-link-normal'})
    if linkUrl == None:
        print('被跟卖了，为空了')
        return

    linkUrl = linkUrl.get('href')

    # 评论数量 commentMin - commentMax
    cop = re.compile("[^\u4e00-\u9fa5^a-z^A-Z^0-9]")  # 匹配不是中文、大小写、数字的其他字符
    pinglun = cellSoup.find('a', attrs={'class': 'a-size-small a-link-normal'})
    if pinglun == None:
        print('没有评论')
        return

    pinglun = pinglun.contents[0]
    pinglun = cop.sub('', pinglun)
    print(pinglun)
    if int(pinglun) < int(config.AWZ_CommemtMin):
        print('评论太少')
        return
    if int(pinglun) > int(config.AWZ_CommemtMax):
        print('评论太多')
        return

    # 价格区间 priceMin - priceMax
    regFloat = re.compile('[^\d+\,\d+]')
    prices = cellSoup.find_all('span', attrs={'class': 'p13n-sc-price'})
    priceMin = 0
    pirceMax = 0
    if len(prices) < 1: return
    if len(prices) > 0:
        priceMin = prices[0].contents[0]
        priceMin = regFloat.sub('', priceMin)
        priceMin = priceMin.replace(',', '.')

    if len(prices) > 1:
        pirceMax = prices[1].contents[0]
        pirceMax = regFloat.sub('', pirceMax)
        pirceMax = pirceMax.replace(',', '.')

    if float(priceMin) < float(config.AWZ_PriceMin):
        print('价格太低')
        return

    if float(pirceMax) > float(config.AWZ_PriceMax):
        print('价格太高')
        return

    xlsData = xlrd.open_workbook(config.AWZ_Excelname, formatting_info=True)
    wb = xl_copy(xlsData)
    sheeet = xlsData.sheet_by_name('openUrlSheet')
    inNcs = len(sheeet.col(0))
    openSheet = wb.get_sheet(2)
    openSheet.write(inNcs, 0, config.AWZ_HOST + str(linkUrl))
    wb.save(config.AWZ_Excelname)
    print('此商品ok')
    return


# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':

    ids_arr = checkExceltoIDs(config.AWZ_Excelname, config.AWZ_IDSheet)
    index = 0
    for idStr in ids_arr:
        time.sleep(random.randint(2, 5))
        # index += 1
        # if index < 5:
        responseHtml = loadTheidbrowser(config.AWZ_Excelname, idStr)
        if responseHtml == False:
            continue
        else:
            parsingHtml(responseHtml)
        # else:break

    print('运行完成')
    print(ids_arr)

    # responseHtml = loadTheidbrowser(config.AWZ_Excelname, '189731031')
    # print(responseHtml)
    # parsingHtml(responseHtml)
