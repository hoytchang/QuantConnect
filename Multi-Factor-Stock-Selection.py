# Stock Selection Strategy Based on Fundamental Factors
# Cloned from:
# https://www.quantconnect.com/tutorials/strategy-library/stock-selection-strategy-based-on-fundamental-factors

# Changes from cloned code:
# - Changed factors

import operator
from math import ceil,floor


class CoarseFineFundamentalComboAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2009,1,2)  # Set Start Date
        self.SetEndDate(2017,5,2)    # Set End Date
        self.SetCash(50000)          # Set Strategy Cash
        self.flag1 = 1
        self.flag2 = 0
        self.flag3 = 0
        self.UniverseSettings.Resolution = Resolution.Minute        
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        self.AddEquity("SPY")
        self.numberOfSymbols = 300
        self.numberOfSymbolsFine = 10
        self.num_portfolios = 6
        self._changes = None
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.AfterMarketOpen("SPY"), Action(self.Rebalancing))


    def CoarseSelectionFunction(self, coarse):
        if self.flag1:
            CoarseWithFundamental = [x for x in coarse if x.HasFundamentalData]
            sortedByDollarVolume = sorted(CoarseWithFundamental, key=lambda x: x.DollarVolume, reverse=True) 
            top = sortedByDollarVolume[:self.numberOfSymbols]
            return [i.Symbol for i in top]
        else:
            return []


    def FineSelectionFunction(self, fine):
        if self.flag1:
            self.flag1 = 0
            self.flag2 = 1
        
            filtered_fine = [x for x in fine if x.ValuationRatios.BookValueYield
                                            and x.ValuationRatios.EarningYield
                                            and x.ValuationRatios.FCFYield
                                            and x.ValuationRatios.SalesYield]
    
            sortedByfactor1 = sorted(filtered_fine, key=lambda x: x.ValuationRatios.BookValueYield, reverse=True)
            sortedByfactor2 = sorted(filtered_fine, key=lambda x: x.ValuationRatios.EarningYield, reverse=True)
            sortedByfactor3 = sorted(filtered_fine, key=lambda x: x.ValuationRatios.FCFYield, reverse=True)
            sortedByfactor4 = sorted(filtered_fine, key=lambda x: x.ValuationRatios.SalesYield, reverse=True)
            
            num_stocks = floor(len(filtered_fine)/self.num_portfolios)
        
            stock_dict = {}
            
            for i,ele in enumerate(sortedByfactor1):
                rank1 = sortedByfactor1.index(ele)
                rank2 = sortedByfactor2.index(ele)
                rank3 = sortedByfactor3.index(ele)
                rank4 = sortedByfactor4.index(ele)
                score = [ceil(rank1/num_stocks),
                         ceil(rank2/num_stocks),
                         ceil(rank3/num_stocks),
                         ceil(rank4/num_stocks)]
                score = sum(score)
                stock_dict[ele] = score
            #self.Log("score" + str(score))
            self.sorted_stock = sorted(stock_dict.items(), key=lambda d:d[1],reverse=True)
            sorted_symbol = [self.sorted_stock[i][0] for i in range(len(self.sorted_stock))]
            topFine = sorted_symbol[:self.numberOfSymbolsFine]

            self.flag3 = self.flag3 + 1            
            
            return [i.Symbol for i in topFine]

        else:
            return []


    def OnData(self, data):
        if self.flag3 > 0:
            if self.flag2 == 1:
                self.flag2 = 0
                # if we have no changes, do nothing
                if self._changes == None: return
                # liquidate removed securities
                for security in self._changes.RemovedSecurities:
                    if security.Invested:
                        self.Liquidate(security.Symbol)
                 
                for security in self._changes.AddedSecurities:
                    self.SetHoldings(security.Symbol, 0.8/float(len(self._changes.AddedSecurities)))    
         
                self._changes = None

    # this event fires whenever we have changes to our universe
    def OnSecuritiesChanged(self, changes):
        self._changes = changes
    
    def Rebalancing(self):
        self.flag1 = 1