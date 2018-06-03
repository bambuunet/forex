#coding:utf-8
import pandas as pd
import os
import re #Regular expression
import copy
import json
import csv
import numpy as np
import func
import simulate

S = simulate.Simulate()
X = func.Func()

def getPipsPerMonth(currency, codeStr, codeArgValStr, year):
  spread = X.getSpread(S.getCurrency())
  try:
    result = X.getResult(currency, codeStr, codeArgValStr, year)
    if len(result.index) > 0:
      month = float(result['month'][len(result.index) - 1]) - 1 + float(result['day'][len(result.index) - 1]) / 31
      deltaRate = result.sum()['delta'] / (60 * 24 * 20 * month)
      average = result.mean()['gain']
      if deltaRate > 1:
        countPerMonth = len(result.index) / month / deltaRate
      else:
        countPerMonth = len(result.index) / month
      return (average - spread) * countPerMonth
    else:
      return 0
  except:
    return -9999

if __name__ == '__main__':
  while True:
    #実行
    S.runOne()

    #reservationの周辺のDFと結果を探索
    #bOPCL0  bOPCL1...
    #    20      10...
    codeArgArr = S.getCodeArgArr()
    codeArgValArr = S.getCodeArgValArr()
    condition = X.getCondition()
    #spread = X.getSpread(S.getCurrency())
    finishFlag = False

    while True:
      baseArgSr = pd.Series(codeArgValArr, index=codeArgArr)
      relateArgArr = []
      for a in codeArgArr:
        baseVal = int(baseArgSr[a])
        spanVal = condition[a[0]][a[1:5]]['span']['arg' + a[5]]
        maxVal = condition[a[0]][a[1:5]]['max']['arg' + a[5]]
        minVal = condition[a[0]][a[1:5]]['min']['arg' + a[5]]

        if baseVal - spanVal >= minVal:
          _baseArgSr = copy.deepcopy(baseArgSr)
          _baseArgSr[a] = baseVal - spanVal
          _baseArgSr['pipsPerMonth'] = getPipsPerMonth(S.getCurrency(), '_'.join(S.getCodeArr()), '_'.join([str(x) for x in _baseArgSr]), S.getYear())
          relateArgArr.append(_baseArgSr)

        if baseVal + spanVal <= maxVal:
          _baseArgSr = copy.deepcopy(baseArgSr)
          _baseArgSr[a] = baseVal + spanVal
          _baseArgSr['pipsPerMonth'] = getPipsPerMonth(S.getCurrency(), '_'.join(S.getCodeArr()), '_'.join([str(x) for x in _baseArgSr]), S.getYear())
          relateArgArr.append(_baseArgSr)

      relateArgColumns = codeArgArr + ['pipsPerMonth']
      relateArgDf = pd.DataFrame(relateArgArr, columns=relateArgColumns)
      relateArgDf = relateArgDf.sort_values(by='pipsPerMonth', ascending=False)
      relateArgDf = relateArgDf.reset_index()
      relateArgDf = relateArgDf.drop('index', axis=1)
      #print(relateArgDf)

      basePipsPerMonth = getPipsPerMonth(S.getCurrency(), '_'.join(S.getCodeArr()), '_'.join([str(x) for x in baseArgSr]), S.getYear())
      noDataDf = relateArgDf.loc[(relateArgDf['pipsPerMonth'] == -9999)]
      noDataDf = noDataDf.reset_index()
      noDataDf = noDataDf.drop('index', axis=1)

      #結果の中で最高の条件
      if relateArgDf['pipsPerMonth'][0] > basePipsPerMonth:
        codeArgValArr = relateArgDf.drop('pipsPerMonth', axis=1).as_matrix()[0]
      #未調査がない
      elif len(noDataDf.index) == 0:
        finishFlag = True
        break
      #次の調査対象を予約
      else:
        rand = np.random.randint(0, len(noDataDf))
        codeArgValArr = [str(x) for x in noDataDf.drop('pipsPerMonth', axis=1).as_matrix()[rand]]
        newReservation = {
          'codeArr': S.getCodeArr(),
          'codeArgArr': S.getCodeArgArr(),
          'codeArgValArr': codeArgValArr,
          'currency': S.getCurrency(),
          'year': S.getYear()
        }

        X.reservationsAddJson(newReservation)
        break

    if finishFlag:
      break




