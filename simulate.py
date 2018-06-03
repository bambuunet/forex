#coding:utf-8
import datetime as dt
import pandas as pd
import os
import re #Regular expression
import copy
import json
import yaml
import csv
import codecs
import time
import logging
import func

DATA_DIR = os.path.abspath(os.path.dirname(__file__)) + '/data/'
LOG = logging.getLogger(__name__)
X = func.Func()

class Simulate():
  def __init__(self):
    # condition
    self.conditionBuy = None
    self.conditionSell = None

    self.reservationPath = ''

    # 予約のjson
    self.reservation = {}

    # [bOPCL, sOPCL]
    self.codeArr = []

    # bOPCL_sOPCL
    self.codes = ''

    # [bOPCL0, bOPCL1, sOPCL0]
    self.codeArgArr = []

    #[1, 3, 4, 1]
    self.codeArgValArr = []

    #1_3_4_1
    self.codeArgValStr = ''

    #Series -> bOPCL:10...
    self.codeArgValSr = None

    # currency
    self.currency = ''

    # year
    self.year = ''

    # average 
    self.average = 0.0

    # std
    self.std = 0.0

    # pipsPerHour
    self.pipsPerHour = 0.0

    # sum per month
    self.pipsPerMonth = 0.0

    # sum per month total span
    self.pipsPerMonthTotal = 0.0

    # count per month
    self.countPerMonth = 0

    # data
    self.data = None

    # event
    self.event = None

    #result
    self.result = None

    #/csv/results/bOPCL_sOPCL/5_7/2017.csv
    self.resultPath = ''

    self.resultColumns = ['buy_at_utc', 'buy_price', 'dir', 'sell_at_utc', 'sell_price', 'gain', 'buy_at', 'sell_at', 'month', 'weekday', 'day', 'hour', 'delta' ]

    #result list csv
    self.resultList = None

    #/csv/results/list/bOPCL_sOPCL.csv
    self.resultListPath = ''

    # N行目
    self.resultListRow = 0

    # [bOPCL0, bOPCL1, sOPCL0, currency, year, lastDate]
    self.resultListColumns = []

    # pips
    self.pips = 1

    # 前回の最終処理日時
    self.lastDateTime = None


  def run(self):
    getReservation = True
    while getReservation:
      getReservation = self.runOne()
  
  def runOne(self):
    #jsonを1つセット。予約がなければBye
    if not self.setReservation():
      print('No reservation')
      return False
    
    #initをセット
    self.setInit()
    print(self.reservation)
    #running中の条件との重複をチェック
    for r in X.getReservationRunningArr():
      running = X.getReservationRunning(r)
      runningCodeArgValStr = '_'.join(running['codeArgValArr'])
      if self.codeArgValStr == runningCodeArgValStr and self.currency == running['currency'] and self.year == running['year']:
        return True

    #runningをセット
    self.setRunning()
    print('run')
    #EventがDataの範囲まで計算されているか
    if not self.correctEvent():
      print('Add events')
      return False

    #リストを検索し、実行期間を決める
    #重複なし：1/1から実行：return 0101
    #重複あり（toが異なる）：toの翌日から実行 return 実行日
    #重複あり（toが12/30以降）： 実行しない：return false
    yet = self.setDejaData()
    if not yet:
      return True

    i = 0
    while i < len(self.data):
      nowDateTime = dt.datetime.strptime(str(self.data['Date'][i]) + str(self.data['Timestamp'][i]), '%Y%m%d%H:%M:%S')
      
      #処理済みデータの場合戻る
      if nowDateTime <= self.lastDateTime:
        i += 1
        continue

      eventDateTime = self.getNextEvent(nowDateTime)

      finish = False
      buyDir = 0
      buyPrice = 0
      e = {}
      
      #buyの条件チェック
      for c in self.codeArr:
        if c[0] != 'b':
          continue
        buyObj = self.conditionBuy[c[1:5]]

        #変数宣言
        for k, v in buyObj['var'].items():
          e[k] = eval(str(v))

        #iが小さすぎて過去に遡れない場合
        if i <= e['loop'] + e['back']:
            finish = True
            break
        #過去に遡って評価
        for c in range(int(e['loop'] + 1)):
          #i = 20 かつ pastMinute = 15の場合、p = 5, 6 ... 19
          #i = 20 かつ loop = 0 の場合、p = 19
          p = int(i - (e['loop'] + 1) + c)
          if 'put_in_loop' in buyObj:
            for k, v in buyObj['put_in_loop'].items():
              e[k] = eval(str(v))

        #判定
        for v in buyObj['judge']:
          e['judge'] = eval(v)
          if e['judge'] == 'long':
            if buyDir == -1:
              finish = True
            else:
              buyDir = 1
          elif e['judge'] == 'short':
            if buyDir == 1:
              finish = True
            else:
              buyDir = -1
          elif e['judge'] == 'finish':
            finish = True
      
      if finish or buyDir == 0:
        i += 1
        continue

      buyPrice = self.data['Open'][i]
      insert = [nowDateTime, buyPrice, buyDir]

      #buyの場合、sellのためのwhile
      ii = i + 1
      while ii < len(self.data):
        finish = False
        #sellの条件に合致または週の終わり
        for c in self.codeArr:
          if c[0] != 's':
            continue
          sellObj = self.conditionSell[c[1:5]]
          #変数宣言
          for k, v in sellObj['var'].items():
            e[k] = eval(str(v))
          #iが小さすぎて過去に遡れない場合
          if ii <= e['loop'] + e['back']:
            finish = True
            break
          #過去に遡って評価
          sellObj['var']['loop'] = str(sellObj['var']['loop'])
          for c in range(int(e['loop'] + 1)):
            #i = 20 かつ loop = 15の場合、p = 5, 6 ... 19
            #i = 20 かつ loop = 0 の場合、p = 19
            p = int(ii - (e['loop'] + 1) + c)
            if 'put_in_loop' in sellObj:
              for k, v in sellObj['put_in_loop'].items():
                e[k] = eval(str(v))

          #判定
          #週の最後
          if ii + 1 >= len(self.data['Date']):
            finish = True
            break
          if dt.datetime.strptime(str(self.data['Date'][ii+1]) + str(self.data['Timestamp'][ii+1]), '%Y%m%d%H:%M:%S') - dt.datetime.strptime(str(self.data['Date'][ii]) + str(self.data['Timestamp'][ii]), '%Y%m%d%H:%M:%S') > dt.timedelta(days=1):
            finish = True
            break
          #条件に合致
          for v in sellObj['judge']:
            e['judge'] = eval(str(v))
            if e['judge'] == 'finish':
              finish = True
              break

        if finish:
          buyDir = 0
          finishDateTime = dt.datetime.strptime(str(self.data['Date'][ii]) + str(self.data['Timestamp'][ii]), '%Y%m%d%H:%M:%S')
          finishPrice = self.data['Open'][ii]
          gain = (finishPrice - insert[1]) * insert[2] / self.pips
          mt_time_buy_at = X.getMtTime(insert[0])
          mt_time_sell_at = X.getMtTime(finishDateTime)
          mt_month = mt_time_buy_at.month
          mt_weekday = mt_time_buy_at.weekday()
          mt_day = mt_time_buy_at.day
          mt_hour = mt_time_buy_at.hour
          mt_time_delta = (mt_time_sell_at - mt_time_buy_at).seconds / 60

          insert = insert + [finishDateTime, finishPrice, gain, mt_time_buy_at, mt_time_sell_at, mt_month, mt_weekday, mt_day, mt_hour, mt_time_delta]
          insertDataFrame = pd.DataFrame([insert], columns=self.resultColumns)
          self.result = self.result.append(insertDataFrame)
          #保存の頻度を間引き
          if i % 2 == 0:
            self.result.to_csv(self.resultPath, index=False)
            self.updateResultList(nowDateTime)
            #with open(self.resultPath, 'a') as f:
            #  writer = csv.writer(f)
            #  writer.writerow([str(x) for x in insert])
          i += 15
          break
        ii += 1
      i += 1

    #listにaverageを挿入
    self.updateResultList(nowDateTime)
    self.result.to_csv(self.resultPath, index=False)
    os.remove(self.reservationPath)
    return True
  
  def setReservation(self):
    reservationArr = X.getReservationArr()
    reservationArr.reverse()

    if len(reservationArr) > 0:
      self.reservation = X.getReservation(reservationArr[0])
      self.reservationPath = X.getReservationPath(reservationArr[0])
      return True
    else:
      return False

  def setRunning(self):
    runningDirPath = DATA_DIR + 'reservations/running/'

    #reservationをrunningに移動
    os.remove(self.reservationPath)
    self.reservationPath = runningDirPath + re.search(r'\d+\.json', self.reservationPath).group()
    f = open(self.reservationPath, 'w')
    json.dump(self.reservation, f)
    f.close()
    return True

  def setInit(self):
    self.codeArr = self.reservation['codeArr']
    self.codes = '_'.join(self.codeArr)
    self.codeArgArr = self.reservation['codeArgArr']
    self.codeArgValArr = self.reservation['codeArgValArr']
    self.codeArgValStr = '_'.join(self.codeArgValArr)
    self.codeArgValSr = pd.Series([int(x) for x in self.codeArgValArr], index=self.codeArgArr)
    self.currency = self.reservation['currency']
    self.year = self.reservation['year']
    self.data = pd.read_csv(DATA_DIR + 'datas/' + self.currency + '/' + self.year + '.csv')
    self.event = pd.read_csv(DATA_DIR + 'events/' + self.currency + '/' + self.year + '.csv')

    f = codecs.open(DATA_DIR + 'conditions/buy.yml', 'r', 'utf-8')
    self.conditionBuy = yaml.load(f)
    f.close()
    f = codecs.open(DATA_DIR + 'conditions/sell.yml', 'r', 'utf-8')
    self.conditionSell = yaml.load(f)
    f.close()

    #resultのcsvをセット
    #/csv/results/usdjpy/bOPCL_sOPCL/1_3_4_1/2017.csv
    resultPath = DATA_DIR + 'results/' + self.currency + '/'
    if not os.path.exists(resultPath):
      os.mkdir(resultPath)
      os.chmod(resultPath, 0o777)
    resultPath += self.codes + '/'
    if not os.path.exists(resultPath):
      os.mkdir(resultPath)
      os.chmod(resultPath, 0o777)
    resultPath += self.codeArgValStr + '/'
    if not os.path.exists(resultPath):
      os.mkdir(resultPath)
      os.chmod(resultPath, 0o777)
    resultPath += self.year + '.csv'
    if not os.path.exists(resultPath):
      resultCsv = pd.DataFrame([], columns=self.resultColumns)
      resultCsv.to_csv(resultPath, index=False)
      os.chmod(resultPath, 0o666)
    f = open(resultPath, 'r').read()
    if f == '':
      resultCsv = pd.DataFrame([], columns=self.resultColumns)
      resultCsv.to_csv(resultPath, index=False)

    self.resultPath = resultPath
    self.result = pd.read_csv(self.resultPath)

    self.resultListColumns = self.codeArgArr + ['year', 'lastDateTime', 'codeArgValStr', 'average', 'std', 'pipsPerHour', 'countPerMonth', 'pipsPerMonth', 'pipsPerMonthTotal' ]
    resultListPath = DATA_DIR + 'resultLists/' + self.currency + '/'
    if not os.path.exists(resultListPath):
      os.mkdir(resultListPath)
      os.chmod(resultListPath,0o777)
    resultListPath += self.codes + '.csv'
    if not os.path.exists(resultListPath):
      resultListCsv = pd.DataFrame([], columns=self.resultListColumns)
      resultListCsv.to_csv(resultListPath, index=False)
      os.chmod(resultListPath,0o666)
    self.resultListPath = resultListPath
    self.resultList = pd.read_csv(self.resultListPath)

    f = codecs.open(DATA_DIR + 'configs/currency.yml', 'r', 'utf-8')
    currencyList = yaml.load(f)
    f.close()
    self.pips = currencyList[self.currency]['pips']

    return
  
  def correctEvent(self):
    lastDataTime = dt.datetime.strptime(str(self.data['Date'][len(self.data.index) - 1]) + str(self.data['Timestamp'][len(self.data.index) - 1]), '%Y%m%d%H:%M:%S')
    lastEventTime = dt.datetime.strptime(str(self.event['DateTime'][len(self.event.index) - 1]), '%Y-%m-%d %H:%M:%S')

    if (lastDataTime - lastEventTime).days > 30:
      return False

    return True

  def setDejaData(self):
    #リストがなければ作成
    if not os.path.exists(self.resultListPath):
      #タイトル行を挿入
      df = pd.DataFrame([], columns=self.resultListColumns)
      df.to_csv(self.resultListPath, index=False)
    
    #リストから同じ条件の有無を検索
    for i in self.resultList.T:
      check = True
      for a in self.codeArgArr:
        if not self.resultList[a][i] == self.codeArgValSr[a]:
          check = False
          break
      if not str(self.resultList['year'][i]) == self.year:
        check = False
      if not check:
        continue

      #
      #過去データがある場合
      #以上でbreakしない場合、引数と年が同じということ
      #
      #self.lastDateTime = dt.datetime.strptime(str(self.resultList['lastDateTime'][i]), '%Y-%m-%d %H:%M:%S')
      self.lastDateTime = dt.datetime.strptime(self.result['buy_at_utc'][len(self.result.index) - 1], '%Y-%m-%d %H:%M:%S')
      self.resultListRow = i
      if self.lastDateTime.month == 12 and self.lastDateTime.day >= 30:
        return False
      return True

    #
    #過去データがない場合
    #

    # 00:00:01開始
    self.lastDateTime = dt.datetime(int(self.year), 1, 1, 0, 0, 1)

    #result listに追加する値をセット
    resultListVal = []
    for num in self.codeArgValArr:
      resultListVal.append(num)
    resultListVal += [self.year, self.lastDateTime, self.codeArgValStr, self.average, self.std, self.pipsPerHour, self.countPerMonth, self.pipsPerMonth, self.pipsPerMonthTotal]
    resultListValDataFrame = pd.DataFrame([resultListVal], columns=self.resultListColumns)
    self.resultList = pd.read_csv(self.resultListPath)
    self.resultList = self.resultList.append(resultListValDataFrame, ignore_index=True)
    self.resultList.to_csv(self.resultListPath, index=False)

    #n行目
    self.resultListRow = len(self.resultList.index) - 1
    return True

  def getNextEvent(self, now):
    #リストから同じ条件の有無を検索
    nextEvent = dt.datetime(int(self.year), 12, 31, 23, 59, 59)
    for i in self.event.T:
      event = dt.datetime.strptime(str(self.event['DateTime'][i]), '%Y-%m-%d %H:%M:%S')
      if now < event:
        nextEvent = event
        break
    return nextEvent

  def updateResultList(self, lastDateTime):
    i = 0
    while i < 3:
      try:
        self.resultList = pd.read_csv(self.resultListPath)
        break 
      except:
        i += 1
        time.sleep(3)
    self.resultList.loc[self.resultListRow, 'average'] = self.average
    self.resultList.loc[self.resultListRow, 'std'] = self.std
    self.resultList.loc[self.resultListRow, 'pipsPerHour'] = self.pipsPerHour
    self.resultList.loc[self.resultListRow, 'pipsPerMonth'] = self.pipsPerMonth
    self.resultList.loc[self.resultListRow, 'pipsPerMonthTotal'] = self.pipsPerMonthTotal
    self.resultList.loc[self.resultListRow, 'countPerMonth'] = self.countPerMonth
    self.resultList.loc[self.resultListRow, 'lastDateTime'] = lastDateTime
    self.resultList.to_csv(self.resultListPath, index=False)

  def getResultPath(self):
    return self.resultPath

  def getCurrency(self):
    return self.currency

  def getYear(self):
    return self.year

  def getCodeArr(self):
    return self.codeArr

  def getCodeArgArr(self):
    return self.codeArgArr

  def getCodeArgValArr(self):
    return self.codeArgValArr

if __name__ == '__main__':
  a = Simulate()
  a.run()
