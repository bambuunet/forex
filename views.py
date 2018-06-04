
#coding:utf-8
import sys, os
#sys.path.append(os.pardir)

import datetime as dt
import pandas as pd
import numpy as np
import scipy.special
import re #Regular expression
import copy
import json
import yaml
import math
import time
import codecs
import subprocess
from flask import Flask, request, redirect, url_for, render_template, flash, session, jsonify
import logging
from logging.handlers import RotatingFileHandler
import simulate
import func

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = BASE_DIR + '/data/'
SIMULATION_CMD = ''

if 'PYTHON_ENV' in os.environ and os.environ["PYTHON_ENV"] == 'local':
  SIMULATION_CMD = 'python ' + BASE_DIR + '/simulate.py'
  SIMULATION_RELATE_CMD = 'python ' + BASE_DIR + '/simulate_relate.py'
  SIMULATION_KILL_CMD = 'sudo kill '
else:
  SIMULATION_CMD = 'cpulimit -l 90 python3 ' + BASE_DIR + '/simulate.py'
  #SIMULATION_CMD = 'python3 ' + BASE_DIR + '/simulate.py'
  SIMULATION_RELATE_CMD = 'cpulimit -l 90 python3 ' + BASE_DIR + '/simulate_relate.py'
  #SIMULATION_RELATE_CMD = 'python3 ' + BASE_DIR + '/simulate_relate.py'
  SIMULATION_KILL_CMD = 'sudo kill '

X = func.Func()
PERMIT_PROCESS = 1


#
# log
#
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
)
debug_log = os.path.join(app.root_path, 'logs/debug.log')
debug_file_handler = RotatingFileHandler(
    debug_log, maxBytes=100000, backupCount=10
)
debug_file_handler.setLevel(logging.DEBUG)
debug_file_handler.setFormatter(formatter)
app.logger.addHandler(debug_file_handler)
    
error_log = os.path.join(app.root_path, 'logs/error.log')
error_file_handler = RotatingFileHandler(
    error_log, maxBytes=100000, backupCount=10
)    
error_file_handler.setLevel(logging.ERROR)
error_file_handler.setFormatter(formatter)





@app.route('/', methods=['POST', 'GET'])
def index():
  return redirect('/results/')

@app.route('/prepare/<obj>/', methods=['POST', 'GET'])
def prepare(obj):
  res = {}
  res['dataList'] = X.getDataList()
  res['obj'] = obj
  res['optionText'] = ''
  res['optionNum'] = 0

  #if obj == 'calcDayData':
  #  pass
  
  if request.method == 'POST':
    currency = re.search(r'[a-z]{6}', request.form['whichData']).group(0)
    year = re.search(r'[0-9]{4}', request.form['whichData']).group(0)
    data = X.getData(currency, year)
    resArr = []

    if obj == 'event':
      for i in data.T:
        # Events are held at time ingervals of 15 minutes
        if int(data['Timestamp'][i][3:5]) % 15 == 0:
          # Per 1 minites, rate are move 0.15%
          if (data['High'][i] - data['Low'][i]) / data['Open'][i] > 0.0015:
            resArr.append(dt.datetime.strptime(str(data['Date'][i]) + str(data['Timestamp'][i]), '%Y%m%d%H:%M:%S'))
      X.setEvent(currency, year, resArr)

    elif obj == 'dayData':
      op = 0.0
      hi = 0.0
      lo = 0.0
      vl = 0.0
      timeReset = True

      for i in data.T:
        #最初の時刻
        if timeReset:
          op = data['Open'][i]
          hi = data['High'][i]
          lo = data['Low'][i]
          vl = data['Volume'][i]
          timeReset = False
        else:
          if data['High'][i] > hi:
            hi = data['High'][i]
          if data['Low'][i] < lo:
            lo = data['Low'][i]
          vl += data['Volume'][i]
          #最後の時刻
          if i == len(data.index) - 1:
            timeReset = True
            resArr.append([data['Date'][i], op, hi, lo, data['Close'][i], vl])
          elif data['Timestamp'][i + 1][3:5] == '00':
            if X.isSummer(year, str(data['Date'][i])[4:6], str(data['Date'][i])[6:8]):
              if data['Timestamp'][i + 1][0:2] == '20':
                timeReset = True
                resArr.append([data['Date'][i], op, hi, lo, data['Close'][i], vl])
            else:
              if data['Timestamp'][i][0:2] == '21':
                timeReset = True
                resArr.append([data['Date'][i], op, hi, lo, data['Close'][i], vl])

      X.setDayData(currency, year, resArr)

    elif obj == 'dayHighLow':
      dayData = X.getDayData(currency, year)
      columns = ['date', 'month', 'day', 'week', 'weekday', 'res']
      for i in dayData.T:
        month = int(str(dayData['Date'][i])[4:6])
        day = int(str(dayData['Date'][i])[6:8])
        resArr.append([
          dayData['Date'][i],
          month,
          day,
          X.getWeek(year, month, day),
          X.getWeekday(year, month, day),
          dayData['High'][i] - dayData['Low'][i]
          ])

      X.setAnalysis(obj, currency, year, columns, resArr)

    elif obj == 'dayOpenClose':
      dayData = X.getDayData(currency, year)
      columns = ['date', 'month', 'day', 'week', 'weekday', 'res']
      for i in dayData.T:
        month = int(str(dayData['Date'][i])[4:6])
        day = int(str(dayData['Date'][i])[6:8])
        resArr.append([
          dayData['Date'][i],
          month,
          day,
          X.getWeek(year, month, day),
          X.getWeekday(year, month, day),
          dayData['Close'][i] - dayData['Open'][i]
          ])

      X.setAnalysis(obj, currency, year, columns, resArr)

    elif obj == 'dayOpenCloseAbs':
      dayData = X.getDayData(currency, year)
      columns = ['date', 'month', 'day', 'week', 'weekday', 'res']
      for i in dayData.T:
        month = int(str(dayData['Date'][i])[4:6])
        day = int(str(dayData['Date'][i])[6:8])
        resArr.append([
          dayData['Date'][i],
          month,
          day,
          X.getWeek(year, month, day),
          X.getWeekday(year, month, day),
          abs(dayData['Close'][i] - dayData['Open'][i])
          ])

      X.setAnalysis(obj, currency, year, columns, resArr)

    elif obj == 'dayVolume':
      dayData = X.getDayData(currency, year)
      columns = ['date', 'month', 'day', 'week', 'weekday', 'res']
      for i in dayData.T:
        month = int(str(dayData['Date'][i])[4:6])
        day = int(str(dayData['Date'][i])[6:8])
        resArr.append([
          dayData['Date'][i],
          month,
          day,
          X.getWeek(year, month, day),
          X.getWeekday(year, month, day),
          dayData['Volume'][i]
          ])

      X.setAnalysis(obj, currency, year, columns, resArr)

  return render_template('prepare.html', res=res)

@app.route('/reservations/', methods=['POST', 'GET'])
def reservations():
  if request.method == 'POST':
    # get from post
    dic = {'buy':{}, 'sell':{}}
    sortedKeys = sorted(request.form.items())
    codeArr = []
    codeArgArr = []
    codeArgValArr = []

    for k in sortedKeys:
      key = k[0]
      val = k[1]
      keyList = key.split('_') #[buy, OPCL, arg0]

      if keyList[0] == 'buy' or keyList[0] == 'sell':
        # code name
        if val == 'code':
          dic[keyList[0]][keyList[1]] = {}
          codeArr.append(keyList[0][0] + keyList[1])

        # codeがないarg(チェックをつけなかった場合)
        elif keyList[1] not in dic[keyList[0]]:
          continue

        # codeがあるarg
        else:
          dic[keyList[0]][keyList[1]][keyList[2]] = val.split(',')
          codeArgArr.append(keyList[0][0] + keyList[1] + keyList[2][3])
          codeArgValArr.append(val)

    dic['codeArr'] = codeArr
    dic['codeArgArr'] = codeArgArr
    dic['currency'] = re.search(r'[a-z]{6}' , request.form['currencyYear']).group(0)
    dic['year'] = re.search(r'[0-9]{4}' , request.form['currencyYear']).group(0)
    
    X.reservationsAddArgsParse(dic)

  res = {}
  res['reservation'] = X.getReservationArr()
  res['reservation'].reverse()
  res['reservationCount'] = len(res['reservation'])
  res['running'] = X.getReservationRunningArr()
  return render_template('reservations_index.html', res=res)


@app.route('/reservations/<file>/', methods=['POST', 'GET'])
def reservationsFile(file):
  res = {}
  reservation = X.getReservation(file)
  res['link'] = '/results/' + reservation['currency'] + '/' + '_'.join(reservation['codeArr']) + '/' + '_'.join(reservation['codeArgValArr']) + '/' + reservation['year'] + '/'
  res['file'] = reservation
  return render_template('reservations_file.html', res=res)

@app.route('/reservations/running/<file>/', methods=['POST', 'GET'])
def reservationsRunningFile(file):
  res = {}
  reservation = X.getReservationRunning(file)
  res['link'] = '/results/' + reservation['currency'] + '/' + '_'.join(reservation['codeArr']) + '/' + '_'.join(reservation['codeArgValArr']) + '/' + reservation['year'] + '/'
  res['file'] = reservation
  return render_template('reservations_file.html', res=res)

@app.route('/reservations/add/', methods=['POST', 'GET'])
def reservationsAdd():
  res = {}
  res['defVal'] = {} # default value
  res['condition'] = X.getCondition()
  res['dataList'] = X.getDataList()

  if request.method == 'POST':
    # bOPCL0をbOPCLと0に分解
    # テンプレートで文字と数を足せないため
    for k,v in request.form.items():
      if re.match(r'[bs][A-Z]{4}\d' , k):
        kStr = k[0:5]
        kInt = int(k[5:6])
        if not kStr in res['defVal']:
          res['defVal'][kStr] = {}
        res['defVal'][kStr][kInt] = v

  return render_template('reservations_add.html', res=res)

@app.route('/reservations/delete/', methods=['POST', 'GET'])
def reservationsDelete():
  res = {}
  if request.method == 'POST':
    for f in X.getReservationArr():
      os.remove(X.getReservationPath(f))
    for f in X.getReservationRunningArr():
      os.remove(X.getReservationRunningPath(f))
    return redirect('/reservations/')
  return render_template('reservations_delete.html', res=res)

@app.route('/results/', methods=['POST', 'GET'])
def resultsIndex():
  res = {}
  res['code'] = X.getAllCodeArr()
  res['hasCode'] = {}
  res['max'] = {}
  res['count'] = {}

  for currency in X.getResultListCurrencyArr():
    res['hasCode'][currency] = {}
    res['max'][currency] = {}
    res['count'][currency] = {}
    for codeStr in X.getResultListCodeStrArr(currency):
      resultList = X.getResultList(currency, codeStr)
      res['hasCode'][currency][codeStr] = []
      #時期を見てtryはやめる
      try:
        res['max'][currency][codeStr] = resultList.max()['pipsPerMonth']
      except:
        res['max'][currency][codeStr] = 999999
      res['count'][currency][codeStr] = len(resultList)
      for c in res['code']:
        has = False
        for c2 in codeStr.split('_'):
          if c == c2:
            has = True
            res['hasCode'][currency][codeStr].append(has)
            continue
        if not has:
          res['hasCode'][currency][codeStr].append(has)

  return render_template('results_index.html', res=res)

@app.route('/results/<currency>/<codeStr>/', methods=['POST', 'GET'])
def resultsCode(currency, codeStr):
  res = {}
  res['currency'] = currency
  res['codeStr'] = codeStr
  res['argArr'] = []
  res['descriptionArr'] = []
  res['condition'] = X.getCondition()
  res['codeArr'] = codeStr.split('_')
  res['codeArgArr'] = X.getCodeArgArr(codeStr)

  #スプレッド
  spread = X.getSpread(currency)

  #見出し行
  for a in res['codeArgArr']:
    res['argArr'].append(a[5])
    res['descriptionArr'].append(res['condition'][a[0]][a[1:5]]['descriptions']['arg' + a[5]])

  #中身確認＆入力
  resultPath = DATA_DIR + 'results/' + currency + '/' + codeStr + '/'
  resultList = X.getResultList(currency, codeStr)

  for i in resultList.T:
    if resultList.ix[i, 'countPerMonth'] == 0:
      #code
      codeArgValStr = ''
      for a in res['codeArgArr']:
        codeArgValStr += str(resultList.ix[i, a]) + '_'
      codeArgValStr = codeArgValStr.rstrip('_')
      result = pd.read_csv(X.getResultPath(currency, codeStr, codeArgValStr, resultList.ix[i, 'year']))

      monthPerYear = float((dt.datetime.strptime(resultList.ix[i, 'lastDateTime'], '%Y-%m-%d %H:%M:%S') - dt.datetime(resultList.ix[i, 'year'] - 1, 12, 31)).days) / 365 * 12
      deltaRate = result.sum()['delta'] / float((dt.datetime.strptime(resultList.ix[i, 'lastDateTime'], '%Y-%m-%d %H:%M:%S') - dt.datetime(resultList.ix[i, 'year'] - 1, 12, 31)).days) / 60 / 24 * (7 / 5)
      resultList.ix[i, 'average'] = round(result.mean()['gain'], 2)
      resultList.ix[i, 'std'] = round(result.std()['gain'], 2)
      resultList.ix[i, 'pipsPerHour'] = round(result.mean()['gain'] / result.mean()['delta'] * 60, 2)
      if deltaRate > 1:
        resultList.ix[i, 'countPerMonth'] = int(len(result.index) / monthPerYear / deltaRate)
      else:
        resultList.ix[i, 'countPerMonth'] = int(len(result.index) / monthPerYear)
      resultList.ix[i, 'pipsPerMonth'] = int((resultList.ix[i, 'average'] - spread) * resultList.ix[i, 'countPerMonth'])

      resultList.to_csv(X.getResultListPath(currency, codeStr), index=False)

  for i in resultList.T:
    if resultList.ix[i, 'pipsPerMonthTotal'] == 0:
      gain = 0
      span = 0
      for ii in resultList.T:
        if resultList['codeArgValStr'][i] == resultList['codeArgValStr'][ii]:
          monthPerYear = float((dt.datetime.strptime(resultList.ix[ii, 'lastDateTime'], '%Y-%m-%d %H:%M:%S') - dt.datetime(resultList.ix[ii, 'year'] - 1, 12, 31)).days) / 365 * 12
          gain += resultList['pipsPerMonth'][ii] * monthPerYear
          span += monthPerYear
      resultList.ix[i, 'pipsPerMonthTotal'] = int(gain / span)
      resultList.to_csv(X.getResultListPath(currency, codeStr), index=False)

  #条件付き表示(全ての行を再計算 ＆ 保存しない)
  weekday = request.args.get('weekday')
  hour_from = request.args.get('hour_from')
  hour_to = request.args.get('hour_to')
  if not (weekday == None or hour_from == None or hour_to == None):
    if not (weekday == '' and hour_to == '' and hour_to == ''):
      for i in resultList.T:
        codeArgValStr = ''
        for a in res['codeArgArr']:
          codeArgValStr += str(resultList.ix[i, a]) + '_'
        codeArgValStr = codeArgValStr.rstrip('_')
        result = pd.read_csv(X.getResultPath(currency, codeStr, codeArgValStr, resultList.ix[i, 'year']))
        if not weekday == '':
          weekday = int(weekday)
          result = result.loc[(result['weekday'] == weekday)]
        if not hour_from == '':
          hour_from = int(hour_from)
          result = result.loc[(result['hour'] >= hour_from)]
        if not hour_to == '':
          hour_to = int(hour_to)
          result = result.loc[(result['hour'] <= hour_to)]

        monthPerYear = float((dt.datetime.strptime(resultList.ix[i, 'lastDateTime'], '%Y-%m-%d %H:%M:%S') - dt.datetime(resultList.ix[i, 'year'] - 1, 12, 31)).days) / 365 * 12
        deltaRate = result.sum()['delta'] / float((dt.datetime.strptime(resultList.ix[i, 'lastDateTime'], '%Y-%m-%d %H:%M:%S') - dt.datetime(resultList.ix[i, 'year'] - 1, 12, 31)).days) / 60 / 24 * (7 / 5)

        resultList.ix[i, 'average'] = round(result.mean()['gain'], 2)
        resultList.ix[i, 'pipsPerHour'] = round(result.mean()['gain'] / result.mean()['delta'] * 60, 2)
        if deltaRate > 1:
          resultList.ix[i, 'countPerMonth'] = int(len(result.index) / monthPerYear / deltaRate)
        else:
          resultList.ix[i, 'countPerMonth'] = int(len(result.index) / monthPerYear)
        resultList.ix[i, 'pipsPerMonth'] = int((resultList.ix[i, 'average'] - spread) * resultList.ix[i, 'countPerMonth'])

  for i in resultList.T:
    gain = 0
    span = 0
    for ii in resultList.T:
      if resultList['codeArgValStr'][i] == resultList['codeArgValStr'][ii]:
        monthPerYear = float((dt.datetime.strptime(resultList.ix[ii, 'lastDateTime'], '%Y-%m-%d %H:%M:%S') - dt.datetime(resultList.ix[ii, 'year'] - 1, 12, 31)).days) / 365 * 12
        gain += resultList['pipsPerMonth'][ii] * monthPerYear
        span += monthPerYear
    resultList.ix[i, 'pipsPerMonthTotal'] = int(gain / span)

  res['weekday'] = weekday
  res['hour_from'] = hour_from
  res['hour_to'] = hour_to

  #リンク作成
  link = []
  for i in resultList.T:
    variables = ''
    for a in res['codeArgArr']:
      variables += str(resultList.ix[i, a]) + '_'
    variables = variables.rstrip('_')
    link.append('/results/' + currency + '/' + codeStr + '/' + variables + '/' + str(resultList.ix[i, 'year']) + '/')
  link = pd.DataFrame(link, columns=['link'])
  resultList = pd.concat([resultList, link], axis=1)

  #表示順変更
  order_1 = request.args.get('order_1')
  order_2 = request.args.get('order_2')
  if not (order_1 == None or order_2 == None):
    if not (weekday == '' and hour == ''):
      pass

  resultListGrouped = resultList.groupby(['pipsPerMonthTotal', 'codeArgValStr'])

  res['res'] = []
  for codeArgGroup in resultListGrouped:
    row = {}
    row['calc'] = []
    for i in codeArgGroup[1].T:
      if len(row['calc']) == 0:
        for a in resultList:
          row[a] = resultList[a][i]
      calc = {}
      calc['no'] = len(row['calc'])
      calc['year'] = resultList['year'][i]
      calc['lastDateTime'] = resultList['lastDateTime'][i][5:10]
      calc['average'] = resultList['average'][i]
      calc['std'] = resultList['std'][i]
      calc['pipsPerHour'] = resultList['pipsPerHour'][i]
      calc['countPerMonth'] = resultList['countPerMonth'][i]
      calc['pipsPerMonth'] = resultList['pipsPerMonth'][i]
      calc['link'] = resultList['link'][i]
      row['calc'].append(calc)
      row['calcLen'] = len(row['calc'])
    res['res'].append(row)
  res['res'].reverse()

  return render_template('results_code.html', res=res)


@app.route('/results/<currency>/<codeStr>/tactics/', methods=['POST', 'GET'])
def resultsCodeTactics(currency, codeStr):
  res = {}
  res['currency'] = currency
  res['codeStr'] = codeStr
  res['argArr'] = []
  res['descriptionArr'] = []
  res['condition'] = X.getCondition()
  res['codeArr'] = codeStr.split('_')
  res['codeArgArr'] = X.getCodeArgArr(codeStr)

  #スプレッド
  spread = X.getSpread(currency)

  #見出し行
  for a in res['codeArgArr']:
    res['argArr'].append(a[5])
    res['descriptionArr'].append(res['condition'][a[0]][a[1:5]]['descriptions']['arg' + a[5]])

  resultList = X.getResultList(currency, codeStr)

  filterNeuronNum = 30
  learningRate = 0.01
  learnNum = 50
  target = []
  stdArr = []
  avrArr = []

  #arg別
  gainAvr = resultList.mean()['pipsPerMonth']
  gainStd = resultList.std()['pipsPerMonth']
  for k in resultList:
    if re.match(r'[bsA-Z0-9]{6}' , k):
      avrArr.append(resultList.mean()[k])
      stdArr.append(resultList.std()[k])

  avrSr = pd.Series(avrArr, index=res['codeArgArr'])
  stdSr = pd.Series(stdArr, index=res['codeArgArr'])

  avrMtx = np.array([avrArr])
  stdMtx = np.array([stdArr])

  #target
  for i in resultList.T:
    target.append((resultList['pipsPerMonth'][i] - gainAvr) / gainStd * 0.1 + 0.5)
  target = np.array(target)

  inputMtx = []
  for a in res['codeArgArr']:
    row = []
    for i in resultList.T:
      if stdSr[a] == 0:
        row.append(0.5)
      else:
        row.append((resultList[a][i] - avrSr[a]) / stdSr[a] * 0.1 + 0.5)
    inputMtx.append(row)

  hiddenFilterMtx = np.array([[y - 0.5 for y in x] for x in np.random.rand(filterNeuronNum, len(inputMtx))])
  finalFilterMtx = np.array([[y - 0.5 for y in x] for x in np.random.rand(1, filterNeuronNum)])
  for i in range(learnNum):
    hiddenInputMtx = np.dot(hiddenFilterMtx, inputMtx)
    hiddenOutputMtx = np.array([[scipy.special.expit(y) for y in x] for x in hiddenInputMtx])

    finalInputMtx = np.dot(finalFilterMtx, hiddenOutputMtx)
    finalOutputMtx = np.array([[scipy.special.expit(y) for y in x] for x in finalInputMtx])

    outputErrorMtx = target - finalOutputMtx
    hiddenErrorMtx = np.dot(finalFilterMtx.T, outputErrorMtx)

    finalFilterMtx += learningRate * np.dot((outputErrorMtx * finalOutputMtx * (1.0 - finalOutputMtx)), np.transpose(hiddenOutputMtx))
    hiddenFilterMtx += learningRate * np.dot((hiddenErrorMtx * hiddenOutputMtx * (1.0 - hiddenOutputMtx)), np.transpose(inputMtx))

  resMtx = np.ones(( filterNeuronNum, 1 )) * avrMtx + np.multiply( np.ones(( filterNeuronNum, 1 )) * stdMtx * 10, hiddenFilterMtx)

  resDf = pd.DataFrame(resMtx, columns=res['codeArgArr'])
  finalFilterDf = pd.DataFrame(finalFilterMtx.T, columns=['std'])
  res['totalDf'] = pd.concat([finalFilterDf * 100 + 50, resDf], axis=1).sort_values(by='std', ascending=False)[:10]

  res['std'] = stdArr
  res['avr'] = avrArr
  return render_template('results_code_tactics.html', res=res)


@app.route('/results/<currency>/<codeStr>/<codeArgValStr>/<year>/', methods=['POST', 'GET'])
def resultsYear(currency, codeStr, codeArgValStr, year):
  res = {}
  result = X.getResult(currency, codeStr, codeArgValStr, year)
  dayData = X.getDayData(currency, year).set_index('Date')
  res['result'] = result.loc[(result['month'] == 1)].loc[(result['day'] <= 10)]

  res['backLink'] = '/results/' + currency + '/' + codeStr + '/'
  res['month'] = result.groupby(['month', 'dir']).mean().round(1)  
  res['weekday'] = result.groupby(['dir', 'weekday']).mean().round(1)

  gain = result.groupby(['dir']).sum()['gain']
  delta = result.groupby(['dir']).sum()['delta']
  res['pipsPerHour'] = (gain.div(delta) * 60).round(1)

  weekdayGain = result.groupby(['dir', 'weekday']).sum()['gain']
  weekdayDelta = result.groupby(['dir', 'weekday']).sum()['delta']
  res['weekdayPipsPerHour'] = (weekdayGain.div(weekdayDelta) * 60).round(1)

  hourGain = result.groupby(['dir', 'hour']).sum()['gain']
  hourDelta = result.groupby(['dir', 'hour']).sum()['delta']
  res['hourPipsPerHour'] = (hourGain.div(hourDelta ) * 60).round(1)

  weekdayHourGain = result.groupby(['dir', 'weekday', 'hour']).sum()['gain']
  weekdayHourDelta = result.groupby(['dir', 'weekday', 'hour']).sum()['delta']
  res['weekdayHourPipsPerHour'] = (weekdayHourGain.div(weekdayHourDelta ) * 60).round(0)

  f = codecs.open(DATA_DIR + 'configs/currency.yml', 'r', 'utf-8')
  currencyConfig = yaml.load(f) 
  f.close()
  spread = currencyConfig[currency]['spread']
  monthDayGain = result.groupby(['month', 'day', 'dir']).sum()['gain']
  monthDayDelta = result.groupby(['month', 'day', 'dir']).sum()['delta']
  monthDayCount = result.groupby(['month', 'day', 'dir']).count()['gain']
  res['sumLong'] = []
  res['sumShort'] = []
  res['sumLabel'] = []
  res['netGain'] = [] #時系列重複なし
  res['netGainLong'] = [] #時系列重複なし
  res['netGainShort'] = [] #時系列重複なし
  res['close'] = []
  sumLong = 0
  sumShort = 0
  sumLabelCount = 0
  netGain = 0
  netGainLong = 0
  netGainShort = 0

  for m in range(12):
    for d in range(31):
      if m + 1 in monthDayDelta:
        if len(result.loc[(result['month'] == m + 1)].loc[(result['day'] == d + 1)]) == 0:
          continue
        if d + 1 in monthDayDelta[m + 1]:
          date = int(str(year) + str(m + 1).zfill(2) + str(d + 1).zfill(2))
          if date in dayData.index:
            if 1 in monthDayDelta[m + 1][d + 1]:
              if monthDayDelta[m + 1][d + 1][1] > 60 * 24:
                sumLong += monthDayGain[m + 1][d + 1][1] / monthDayDelta[m + 1][d + 1][1] * 60 * 24 - monthDayCount[m + 1][d + 1][1] * spread
              else:
                sumLong += monthDayGain[m + 1][d + 1][1] - monthDayCount[m + 1][d + 1][1] * spread
            if -1 in monthDayDelta[m + 1][d + 1]:
              if monthDayDelta[m + 1][d + 1][-1] > 60 * 24:
                sumShort += monthDayGain[m + 1][d + 1][-1] / monthDayDelta[m + 1][d + 1][-1] * 60 * 24 - monthDayCount[m + 1][d + 1][-1] * spread
              else:
                sumShort += monthDayGain[m + 1][d + 1][-1] - monthDayCount[m + 1][d + 1][-1] * spread
            res['sumLong'].append(int(sumLong))
            res['sumShort'].append(int(sumShort))
            res['sumLabel'].append(str(year) + str(m + 1).zfill(2) + str(d + 1).zfill(2))
            
            res['close'].append(dayData['Close'][date])
            sumLabelCount += 1

            todayResult = result.loc[(result['month'] == m + 1)].loc[(result['day'] == d + 1)]
            todayResultLong = result.loc[(result['dir'] == 1)].loc[(result['month'] == m + 1)].loc[(result['day'] == d + 1)]
            todayResultShort = result.loc[(result['dir'] == -1)].loc[(result['month'] == m + 1)].loc[(result['day'] == d + 1)]

            lastSellTime = dt.datetime(int(year), m + 1, d + 1)
            for i in todayResult.T:
              if dt.datetime.strptime(todayResult['buy_at'][i], '%Y-%m-%d %H:%M:%S') > lastSellTime:
                netGain += todayResult['gain'][i] - spread
                lastSellTime = dt.datetime.strptime(todayResult['sell_at'][i], '%Y-%m-%d %H:%M:%S')
            lastSellTime = dt.datetime(int(year), m + 1, d + 1)
            for i in todayResultLong.T:
              if dt.datetime.strptime(todayResultLong['buy_at'][i], '%Y-%m-%d %H:%M:%S') > lastSellTime:
                netGainLong += todayResultLong['gain'][i] - spread
                lastSellTime = dt.datetime.strptime(todayResultLong['sell_at'][i], '%Y-%m-%d %H:%M:%S')
            lastSellTime = dt.datetime(int(year), m + 1, d + 1)
            for i in todayResultShort.T:
              if dt.datetime.strptime(todayResultShort['buy_at'][i], '%Y-%m-%d %H:%M:%S') > lastSellTime:
                netGainShort += todayResultShort['gain'][i] - spread
                lastSellTime = dt.datetime.strptime(todayResultShort['sell_at'][i], '%Y-%m-%d %H:%M:%S')

            res['netGain'].append(int(netGain))
            res['netGainLong'].append(int(netGainLong))
            res['netGainShort'].append(int(netGainShort))

  res['year'] = year
  res['codeArgArr'] = []
  codeArgArr = X.getCodeArgArr(codeStr)
  codeArgValArr = codeArgValStr.split('_')
  for i in range(len(codeArgArr)):
    res['codeArgArr'].append({
        'key': codeArgArr[i],
        'val': codeArgValArr[i]
      })

  return render_template('results_year.html', res=res)


@app.route('/results/<currency>/<codeStr>/<codeArgValStr>/<year>/<month>/<day>/', methods=['POST', 'GET'])
def resultsDay(currency, codeStr, codeArgValStr, year, month, day):
  monthStr = month.zfill(2)
  dayStr = day.zfill(2)
  month = int(month)
  day = int(day)
  res = {}

  result = X.getResult(currency, codeStr, codeArgValStr, year)
  result = result.loc[(result['month'] == month)].loc[(result['day'] == day)]

  data = X.getData(currency, year)
  todayStr = X.getDateStr(year, month, day)
  today = dt.datetime.strptime(todayStr, '%Y%m%d')
  yesterday = today - dt.timedelta(days=1)
  yesterdayStr = X.getDateStr(year, yesterday.month, yesterday.day)
  tomorrow = today + dt.timedelta(days=1)

  timeDiff = 2
  if X.isSummer(year, month, day):
    timeDiff = 3

  data1 = data.loc[(data['Date'] == int(yesterdayStr))].loc[(data['Timestamp'] >= str(24 - timeDiff) + ':00:00')]
  data2 = data.loc[(data['Date'] == int(todayStr))].loc[(data['Timestamp'] < str(24 - timeDiff) + ':00:00')]
  data = pd.concat([data1, data2])

  res['label'] = []
  for t in data['Timestamp']:
    labelHour = (int(t[0:2]) + timeDiff) % 24
    labelMin = float(t[3:5]) / 60
    label = round(labelHour + labelMin, 2)
    res['label'].append(label)
  res['high'] = data['High'].values.tolist()
  res['low'] = data['Low'].values.tolist()
  res['volume'] = data['Volume'].values.tolist()

  res['region'] = []
  for i in result.T:
    start = round(float(result['buy_at'][i][11:13]) + float(result['buy_at'][i][14:16]) / 60, 2)
    end = round(float(result['sell_at'][i][11:13]) + float(result['sell_at'][i][14:16]) / 60, 2)
    if end < start:
      end = 23.99
    if result['dir'][i] == 1:
      res['region'].append({'axis':'x', 'start':start, 'end':end, 'class':'regionLong'})
    else:
      res['region'].append({'axis':'x', 'start':start, 'end':end, 'class':'regionShort'})

  res['backLink'] = '/results/' + currency +'/' + codeStr + '/'
  res['yearLink'] = '/results/' + currency +'/' + codeStr + '/' + codeArgValStr + '/' + year + '/'
  res['monthStr'] = monthStr
  res['dayStr'] = dayStr
  res['month'] = month
  res['day'] = day
  res['weekday'] = X.getWeekdayStr(year, month, day)
  res['result'] = result

  if today.weekday() == 0:
    yesterday = today - dt.timedelta(days=3)
  if today.weekday() == 4:
    tomorrow = today + dt.timedelta(days=3)
  res['yesterdayLink'] = '/results/' + currency +'/' + codeStr + '/' + codeArgValStr + '/' + year + '/' + str(yesterday.month) + '/' + str(yesterday.day) + '/'
  res['tomorrowLink'] = '/results/' + currency +'/' + codeStr + '/' + codeArgValStr + '/' + year + '/' + str(tomorrow.month) + '/' + str(tomorrow.day) + '/'

  return render_template('results_day.html', res=res)


@app.route('/reflesh/<currency>/<codeStr>/', methods=['POST', 'GET'])
def refleshResultlist(currency, codeStr):
  resultListColumns = X.getCodeArgArr(codeStr) + ['year', 'lastDateTime', 'codeArgValStr', 'average', 'std', 'pipsPerHour', 'countPerMonth', 'pipsPerMonth', 'pipsPerMonthTotal']
  resultListArr = []

  for codeArgValStr in X.getResultCodeArgValStrArr(currency, codeStr):
    for year in X.getResultYearArr(currency, codeStr, codeArgValStr):
      try:
        result = X.getResult(currency, codeStr, codeArgValStr, year)
        arr = codeArgValStr.split('_')
        arr += [year]
        arr += [result['buy_at_utc'][len(result.index) - 1]]
        arr += [codeArgValStr]
        arr += [0, 0, 0, 0, 0, 0]
        resultListArr.append(arr)
      except:
        pass
  resultList = pd.DataFrame(resultListArr, columns=resultListColumns)
  resultList.to_csv(X.getResultListPath(currency, codeStr), index=False)
  return redirect('/results/' + currency + '/' + codeStr + '/')

@app.route('/simulation/', methods=['POST', 'GET'])
def simulation():
  res = {}

  #起動中プロセス数を取得
  try:
    process = subprocess.Popen("ps aux | grep simulate | grep -v grep | wc -l", shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    simulatingProcessNum = int(re.search(r'\d+', str(process)).group(0))
  except:
    simulatingProcessNum = 999
  
  #running内の中途半端なファイルを戻す
  reservationsDirPath = DATA_DIR + 'reservations/'
  runningDirPath = DATA_DIR + 'reservations/running/'
  if simulatingProcessNum == 0:
    for path in os.listdir(runningDirPath):
      if re.match(r'[0-9]+\.json', path):
        f = open(runningDirPath + path, 'r')
        reservation = json.load(f)
        f.close()

        os.remove(runningDirPath + path)
        f = open(reservationsDirPath + path, 'w')
        json.dump(reservation, f)
        f.close()

  if request.method == 'POST':
    if simulatingProcessNum < PERMIT_PROCESS:
      subprocess.call(SIMULATION_CMD, shell=True)

  #起動中プロセス数を再取得
  try:
    process = subprocess.Popen("ps aux | grep simulate | grep -v grep | wc -l", shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    simulatingProcessNum = int(re.search(r'\d+', str(process)).group(0))
  except:
    simulatingProcessNum = 999

  res['simulatingProcessNum'] = simulatingProcessNum
  res['reservation'] = X.getReservationArr()

  return render_template('simulation.html', res=res)

@app.route('/simulation/relate/', methods=['POST', 'GET'])
def simulationRelate():
  if request.method == 'POST':
    try:
      process = subprocess.Popen("ps aux | grep simulate | grep -v grep", shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
      processList = re.findall(r'root +\d+', str(process))
      for p in processList:
        processId = re.search(r'\d+', p).group()
        subprocess.call(SIMULATION_KILL_CMD + processId, shell=True)
      for i in range(PERMIT_PROCESS):
        subprocess.call(SIMULATION_RELATE_CMD, shell=True)
        time.sleep(5)
    except:
      pass
  return redirect('/simulation/')

@app.route('/simulation/kill/', methods=['POST', 'GET'])
def simulationKill():
  try:
    process = subprocess.Popen("ps aux | grep simulate | grep -v grep", shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    processList = re.findall(r'root +\d+', str(process))
    for p in processList:
      processId = re.search(r'\d+', p).group()
      subprocess.call(SIMULATION_KILL_CMD + processId, shell=True)
  except:
    pass
  return redirect('/results/')



if __name__ == "__main__":
    app.run(debug=True)
    #app.run(host='0.0.0.0')
