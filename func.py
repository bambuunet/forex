#coding:utf-8
import sys, os
import datetime as dt
import pandas as pd
import numpy as np
import scipy.special
import re #Regular expression
import copy
import json
import yaml
import codecs


#app = Flask(__name__)


'''
### 命名規則 ### 
buySell           : buy, sell
code              : bOPCL
codeArr           : [bOPCL, bHILO]
codeStr           : bOPCL_bHILO
codePart          : OPCL
codePartArr       : [OPCL, OPCL]
arg               : arg0
argArr            : [arg0, arg1]

codeArg           : bOPCL0
codeArgArr        : [bOPCL0, bOPCL1]
codeArgStr        : bOPCL0_bOPCL1
codeArgValArr     : [30, 5, 0]
codeArgValStr     : 30_5_0

currency          : usdjpy
currencyArr       : [usdjpy, eurusd]
year              : 2017
yearArr           : [2016, 2017]

conditionPath     : 
conditionBuy      : buy yaml
conditionSell     : sell yaml

data              : data dataframe
dataPath          : datas/
dataCurrencyPath  : datas/<currency>/
dataYearPath      : datas/<currency>/<year>.csv
dataList          : [usdjpy/2017, eurusd/2017]

event             : event dataframe
eventArr          : event array

reservation       : json
reservationArr    : [999999999999.json, 999999999999.json]
reservationName   : 999999999999.json
reservationPath   : reservation/999999999999.json

datasCu

'''


class Func():
  def __init__(self):
    self.DATA_DIR = os.path.abspath(os.path.dirname(__file__)) + '/data/'

    self.eventColumns = ['DateTime']

    self.dayDataColumns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']

  #
  # data
  #
  def getData(self, currency, year):
    return pd.read_csv(self.DATA_DIR + 'datas/' + currency + '/' + year + '.csv')

  def getDataCurrencyArr(self):
    return [x for x in os.listdir(self.DATA_DIR + 'datas/') if re.match(r'[a-z]+' , x)]

  def getDataYearArr(self, currency):
    return [x.rstrip('.csv') for x in os.listdir(self.DATA_DIR + 'datas/' + currency + '/') if re.match(r'[\d]{4}\.csv' , x)]

  def getDataList(self):
    res = []
    for currency in self.getDataCurrencyArr():
      for year in self.getDataYearArr(currency):
        res.append(currency + '/' + year)
    return res

  #
  # result
  #
  def getResult(self, currency, codeStr, codeArgValStr, year):
    return pd.read_csv(self.DATA_DIR + 'results/' + currency + '/' + codeStr + '/' + codeArgValStr + '/' + str(year) + '.csv')

  def getResultCurrencyArr(self):
    return [x for x in os.listdir(self.DATA_DIR + 'results/') if re.match(r'[a-z]+' , x)]

  def getResultCodeStrArr(self, currency):
    return [x for x in os.listdir(self.DATA_DIR + 'results/' + currency + '/') if re.match(r'[\d\._]+' , x)]

  def getResultCodeArgValStrArr(self, currency, codeStr):
    return [x for x in os.listdir(self.DATA_DIR + 'results/' + currency + '/' + codeStr + '/') if re.match(r'[\d_]+' , x)]

  def getResultYearArr(self, currency, codeStr, codeArgValStr):
    return [x.rstrip('.csv') for x in os.listdir(self.DATA_DIR + 'results/' + currency + '/' + codeStr + '/' + codeArgValStr + '/') if re.match(r'[\d]{4}\.csv' , x)]


  def getResultPath(self, currency, codeStr, codeArgValStr, year):
    return self.DATA_DIR + 'results/' + currency + '/' + codeStr + '/' + codeArgValStr + '/' + str(year) + '.csv'

  #
  # resultList
  #
  def getResultList(self, currency, codeStr):
    return pd.read_csv(self.DATA_DIR + 'resultLists/' + currency + '/' + codeStr + '.csv')

  def getResultListCurrencyArr(self):
    return [x for x in os.listdir(self.DATA_DIR + 'resultLists/') if re.match(r'[a-z]+' , x)]

  def getResultListCodeStrArr(self, currency):
    return [x.rstrip('.csv') for x in os.listdir(self.DATA_DIR + 'resultLists/' + currency + '/') if re.match(r'[bsA-Z_]+\.csv' , x)]

  def getResultListPath(self, currency, codeStr):
    return self.DATA_DIR + 'resultLists/' + currency + '/' + codeStr + '.csv'


  #
  # event
  #
  def setEvent(self, currency, year, eventArr):
    path = self.DATA_DIR + 'events/' + currency + '/'
    if not os.path.exists(path):
      os.mkdir(path)
    path += str(year) + '.csv'
    if not os.path.exists(path):
      f = open(path, 'w')
      f.close()
    event = pd.DataFrame(eventArr, columns=self.eventColumns)
    event.to_csv(path, index=False)
    return event

  def getEvent(self, currency, year):
    path = self.DATA_DIR + 'events/' + currency + '/'
    if not os.path.exists(path):
      return False
    path += str(year) + '.csv'
    return pd.read_csv(path)

  def getEventPath(self, currency, year):
    return self.DATA_DIR + 'events/' + currency + '/' + str(year) + '.csv'

  #
  # day datas
  #
  def setDayData(self, currency, year, dayDataArr):
    path = self.DATA_DIR + 'dayDatas/' + currency + '/'
    if not os.path.exists(path):
      os.mkdir(path)
    path += str(year) + '.csv'
    if not os.path.exists(path):
      f = open(path, 'w')
      f.close()
    data = pd.DataFrame(dayDataArr, columns=self.dayDataColumns)
    data.to_csv(path, index=False)
    return data

  def getDayData(self, currency, year):
    path = self.DATA_DIR + 'dayDatas/' + currency + '/'
    if not os.path.exists(path):
      return False
    path += str(year) + '.csv'
    return pd.read_csv(path)

  def getDayDataPath(self, currency, year):
    return self.DATA_DIR + 'dayDatas/' + currency + '/' + str(year) + '.csv'


  #
  # reservation
  #

  def getReservation(self, reservationName):
    f = open(self.getReservationPath(reservationName), 'r')
    reservation = json.load(f)
    f.close()
    return reservation

  def getReservationRunning(self, reservationName):
    f = open(self.getReservationRunningPath(reservationName), 'r')
    reservation = json.load(f)
    f.close()
    return reservation

  def getReservationArr(self):
    path = self.DATA_DIR + 'reservations/'
    res = []
    for path in os.listdir(path):
      if re.match(r'[0-9]+\.json', path):
        res.append(path)
    res.sort()
    return res

  def getReservationRunningArr(self):
    path = self.DATA_DIR + 'reservations/running/'
    res = []
    for path in os.listdir(path):
      if re.match(r'[0-9]+\.json', path):
        res.append(path)
    res.sort()
    return res

  def getReservationPath(self, reservationName):
    return self.DATA_DIR + 'reservations/' + reservationName

  def getReservationRunningPath(self, reservationName):
    return self.DATA_DIR + 'reservations/running/' + reservationName

  #
  # condition
  #
  def getCondition(self):
    res = {}

    f = codecs.open(self.DATA_DIR + 'conditions/buy.yml', 'r', 'utf-8')
    res['b'] = yaml.load(f)
    f.close()

    f = codecs.open(self.DATA_DIR + 'conditions/sell.yml', 'r', 'utf-8')
    res['s'] = yaml.load(f) 
    f.close()

    return res

  def getCodeArgArr(self, codeStr):
    codeArr = codeStr.split('_')
    res = []
    condition = self.getCondition()

    for c in codeArr:
      for k in condition[c[0]][c[1:5]]['descriptions']:
        res.append(c[0:5] + k[3])

    res.sort()
    return res

  def getCodeArgStr(self, codeStr):
    return '_'.join(self.getCodeArgArr(codeStr))

  def getAllCodeArr(self):
    res = []
    for k in self.getCondition()['b']:
      res.append('b' + k)
    for k in self.getCondition()['s']:
      res.append('s' + k)
    res.sort()
    return res


  #
  # analysis
  #
  def setAnalysis(self, analysisName, currency, year, columns, resArr):
    path = '/'.join([self.DATA_DIR + 'analyses', analysisName])
    if not os.path.exists(path):
      os.mkdir(path)
      os.chmod(path, 0o777)
    path += '/' + currency
    if not os.path.exists(path):
      os.mkdir(path)
      os.chmod(path, 0o777)
    path += '/' + str(year) + '.csv'
    if not os.path.exists(path):
      f = open(path, 'w')
      f.close()
      os.chmod(path, 0o666)
    res = pd.DataFrame(resArr, columns=columns)
    res.to_csv(path, index=False)
    return res

  def getAnalysis(self, analysisName, currency, year):
    path = '/'.join([self.DATA_DIR + 'analyses', analysisName, currency, year + '.csv'])
    print(path)
    if not os.path.exists(path):
      return None
    return pd.read_csv(path)

  def getAnalysisNameArr(self):
    res = []
    path = self.DATA_DIR + 'analyses/'
    for v in os.listdir(path):
      if re.match(r'[a-zA-Z0-9_]+' , v):
        res.append(v)
    res.sort()
    return res

  def getAnalysisCurrencyArr(self, analysisName):
    res = []
    path = '/'.join([self.DATA_DIR + 'analyses', analysisName])
    for v in os.listdir(path):
      if re.match(r'[a-z]+' , v):
        res.append(v)
    return res

  def getAnalysisYearArr(self, analysisName, currency):
    res = []
    path = '/'.join([self.DATA_DIR + 'analyses', analysisName , currency])
    for v in os.listdir(path):
      if re.match(r'\d+' , v):
        res.append(v.rstrip('.csv'))
    return res

  #
  # 日付関係
  #

  def getDate(self, year, month, day):
    return dt.datetime(int(year), int(month), int(day))

  #全サマータイム
  def getSummerTimeArr(self):
    f = codecs.open(self.DATA_DIR + 'configs/summerTime.yml', 'r', 'utf-8')
    summerTimeArr = yaml.load(f)
    f.close()
    return summerTimeArr

  #該当年のサマータイム
  def getSummerTime(self, year):
    return self.getSummerTimeArr()[int(year)]

  #夏時間か
  def isSummer(self, year, month, day):
    start = dt.datetime.strptime(str(self.getSummerTime(year)['start']), '%Y-%m-%d')
    end = dt.datetime.strptime(str(self.getSummerTime(year)['end']), '%Y-%m-%d')
    theDay = dt.datetime.strptime(str(year) + str(month).zfill(2) + str(day).zfill(2), '%Y%m%d')
    if theDay >= start and theDay <= end:
      return True
    return False

  #MT時刻
  def getMtTime(self, utc):
    start = dt.datetime.strptime(str(self.getSummerTime(utc.year)['start']), '%Y-%m-%d')
    end = dt.datetime.strptime(str(self.getSummerTime(utc.year)['end']), '%Y-%m-%d')
    #summer
    if utc > start and utc < end:
      return utc + dt.timedelta(hours=3)
    else:
      return utc + dt.timedelta(hours=2)

  #date int
  def getDateInt(self, year, month, day):
    return int(str(year) + str(month).zfill(2) + str(day).zfill(2))

  #date string
  def getDateStr(self, year, month, day):
    return str(year) + str(month).zfill(2) + str(day).zfill(2)

  #weekday
  def getWeekday(self, year, month, day):
    return self.getDate(year, month, day).weekday()

  #同月の雇用統計のdatetime
  def getUnemploymentRateDate(self, year, month, day):
    today = self.getDate(year, month, day)

    #先月
    lastMonth = today - dt.timedelta(days=31)

    #前月の12日
    lastMonth12 = self.getDate(lastMonth.year, lastMonth.month, 12)

    #前月の12日の金曜日
    lastMonth12frideay = 0
    #日曜日
    if lastMonth12.weekday() == 6:
      lastMonth12frideay = lastMonth12.day + 5
    else:
      lastMonth12frideay = lastMonth12.day + (4 - lastMonth12.weekday())

    res = self.getDate(lastMonth.year, lastMonth.month, lastMonth12frideay) + dt.timedelta(days=21)
    if res.month == 1 and res.day == 1:
      res = self.getDate(lastMonth.year, lastMonth.month, lastMonth12frideay) + dt.timedelta(days=28)
    return res


  #米国雇用統計の週を1とする
  def getWeek(self, year, month, day):
    todayDay = self.getDate(year, month, day).day
    unemploymentRateDay = self.getUnemploymentRateDate(year, month, day).day

    #雇用統計の週の日曜日を7とする=>雇用統計は12
    diff = 12 - unemploymentRateDay
    if month == 1:
      print(unemploymentRateDay, int(todayDay + diff), int(todayDay + diff) / 7)
    return int(todayDay + diff) / 7


  def getWeekdayStr(self, year, month, day):
    w = self.getWeekday(year, month, day)
    if w == 0:
      return 'Monday'
    elif  w == 1:
      return 'Tuesday'
    elif  w == 2:
      return 'Wednesday'
    elif  w == 3:
      return 'Thursday'
    elif  w == 4:
      return 'Friday'
    elif  w == 5:
      return 'Saturday'
    elif  w == 6:
      return 'Sunday'
    else:
      return ''


  #
  # その他諸々
  #

  #スプレッド
  def getSpread(self, currency):
    f = codecs.open(self.DATA_DIR + 'configs/currency.yml', 'r', 'utf-8')
    currencyConfig = yaml.load(f) 
    f.close()
    return currencyConfig[currency]['spread']

  # bOPCL1をbuy,OPCL,arg1に変換。
  # bOPCLをbuy,OPCLに変換。
  def restore(self, codeArg):
    res = {}
    res['buySell'] = 'buy' if codeArg[0] == 'b' else 'sell'
    res['codePart'] = codeArg[1:5]
    if len(codeArg) > 5:
      res['arg'] = 'arg' + codeArg[5]
    return res

  #parse args list and post json file
  def reservationsAddArgsParse(self, dic):
    newDic = copy.deepcopy(dic)
    groupCount = 0 #最後の辞書判定用
    for group in dic:
      if group == 'buy' or group == 'sell':
        groupCount += 1 
        codeCount = 0 #最後の辞書判定用
        for code in dic[group]:
          codeCount += 1
          argCount = 0 #最後の辞書判定用
          for arg in dic[group][code]:
            argCount += 1
            if isinstance(dic[group][code][arg], list):
              for num in dic[group][code][arg]:
                if num == "":
                  continue
                newDic[group][code][arg] = float(num)
                #最後のargかどうかを判定
                if groupCount == 2 and codeCount == len(dic[group]) and argCount == len(dic[group][code]):
                  newDic = self.reservationsAddArgNumList(newDic)
                  self.reservationsAddJson(newDic)
                else:
                  self.reservationsAddArgsParse(newDic)
              return

  def reservationsAddArgNumList(self, dic):
    codeArgValArr = []
    for arg in dic['codeArgArr']:
      a = self.restore(arg)
      num = dic[a['buySell']][a['codePart']][a['arg']]
      if num - round(num, 0) == 0:
        num = int(num)
      codeArgValArr.append(str(num))
    dic['codeArgValArr'] = codeArgValArr
    return dic

  def reservationsAddJson(self, dic):
    jsonDirPath = self.DATA_DIR + 'reservations/'
    now = str(dt.datetime.now().strftime("%Y%m%d%H%M%S%f"))
    f = open(jsonDirPath + now +'.json','w')
    json.dump(dic,f,indent=2)

  def resultsCodeCalcPipsPerMonthTotal(resultList):
    gain = 0
    span = 0
    for ii in resultList.T:
      if resultList['codeArgValStr'][i] == resultList['codeArgValStr'][ii]:
        monthPerYear = float((dt.datetime.strptime(resultList.ix[ii, 'lastDateTime'], '%Y-%m-%d %H:%M:%S') - dt.datetime(resultList.ix[ii, 'year'] - 1, 12, 31)).days) / 365 * 12
        gain += resultList['pipsPerMonth'][ii] * monthPerYear
        span += monthPerYear
    resultList.ix[i, 'pipsPerMonthTotal'] = int(gain / span)
    return resultList


