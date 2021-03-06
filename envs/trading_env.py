import gym
from gym import error, spaces, utils
from gym.utils import seeding
from collections import Counter

import quandl
import numpy as np
from numpy import random
import pandas as pd
import logging
import pdb

import tempfile

log = logging.getLogger(__name__)
log.info('%s logger started.',__name__)


def _sharpe(Returns, freq=252) :
  """Given a set of returns, calculates naive (rfr=0) sharpe """
  return (np.sqrt(freq) * np.mean(Returns))/np.std(Returns)

def _prices2returns(prices):
  px = pd.DataFrame(prices)
  nl = px.shift().fillna(0)
  R = ((px - nl)/nl).fillna(0).replace([np.inf, -np.inf], np.nan).dropna()
  R = np.append( R[0].values, 0)
  return R


class FromCSVEnvSrc(object):
  '''

  '''

  MinPercentileDays = 100
  QuandlAuthToken = "73mzBzhJyDhXL-KDLew8"  # not necessary, but can be used if desired
  Name = "TSE/9994"  # https://www.quandl.com/search (use 'Free' filter)

  def __init__(self, days, name=Name, auth=QuandlAuthToken, scale=True):
    self.name = name
    self.auth = auth
    self.days = days #len(open(r"/home/rocc78/Documents/EURUSD240.csv", 'rU').readlines())
    log.info('getting data for %s from quandl...', FromCSVEnvSrc.Name)
    df  = pd.read_csv('/home/rocc78/Documents/EURUSD240.csv',index_col=[0,1])
    log.info('got data for %s from quandl...', FromCSVEnvSrc.Name)

    df = df[~np.isnan(df.volume)]
    # we calculate returns and percentiles, then kill nans


    if scale:
      mean_values = df.mean(axis=0)
      std_values = df.std(axis=0)
      df = (df - np.array(mean_values)) / np.array(std_values)

    self.min_values = df.min(axis=0)
    self.max_values = df.max(axis=0)
    self.data = df
    self.step = 0

  def reset(self):
    # we want contiguous data
    self.idx = np.random.randint(low=0, high=self.days)
    self.step = 0

  def _step(self):
    obs = self.data.iloc[self.idx].as_matrix()
    self.idx += 1
    self.step += 1
    done = self.step >= self.days
    return obs, done


class TradingSim(object) :
  """ Implements core trading simulator for single-instrument univ """

  def __init__(self, steps, trading_cost_bps = 1e-3, time_cost_bps = 1e-4):
    # invariant for object life
    self.trading_cost_bps = trading_cost_bps
    self.time_cost_bps    = time_cost_bps
    self.steps            = steps
    # change every step
    self.step             = 0
    self.actions          = np.zeros(self.steps)
    self.navs             = np.ones(self.steps)
    self.mkt_nav         = np.ones(self.steps)
    self.strat_retrns     = np.ones(self.steps)
    self.posns            = np.zeros(self.steps)
    self.costs            = np.zeros(self.steps)
    self.trades           = np.zeros(self.steps)
    self.mkt_retrns       = np.zeros(self.steps)

    self.profit           = np.zeros(self.steps)
    self.total_profit     = np.zeros(self.steps)
    self.open_price       = np.zeros(self.steps)
    self.close_price      = np.zeros(self.steps)

    self.days = len(open(r"/home/rocc78/Documents/EURUSD240.csv", 'rU').readlines())

    self.src = FromCSVEnvSrc(days=self.days)
    B_cols = ['cangwei','action','open_price','close_price','profit']


    self.B = pd.DataFrame(columns = B_cols,index=['0'])

  def reset(self):
    self.step = 0
    self.actions.fill(0)
    self.navs.fill(1)
    self.mkt_nav.fill(1)
    self.strat_retrns.fill(0)
    self.posns.fill(0)
    self.costs.fill(0)
    self.trades.fill(0)
    self.mkt_retrns.fill(0)

    self.open_price.fill(0)
    self.close_price.fill(0)
    self.profit.fill(0)
    self.total_profit.fill(0)

    # self.B = self.B.drop(self.B.index)
    
  def _step(self, action, retrn ):
    """ Given an action and return for prior period, calculates costs, navs,
        etc and returns the reward and a  summary of the day's activity. """

    bod_posn = 0.0 if self.step == 0 else self.posns[self.step-1]
    bod_nav  = 1.0 if self.step == 0 else self.navs[self.step-1]
    mkt_nav  = 1.0 if self.step == 0 else self.mkt_nav[self.step-1]

    profit = 0 if self.step == 0 else self.profit[self.step-1]


    self.mkt_retrns[self.step] = retrn
    self.actions[self.step] = action
    
    self.posns[self.step] = action - 1     
    self.trades[self.step] = self.posns[self.step] - bod_posn
    
    trade_costs_pct = abs(self.trades[self.step]) * self.trading_cost_bps 
    self.costs[self.step] = trade_costs_pct +  self.time_cost_bps
    reward = profit
    # self.strat_retrns[self.step] = reward



    if self.step != 0 :

        lots = 0.1
        kaicangshu = self.B.iloc[:, 0].size




        if self.actions[self.step] == 1:
            # print( self.actions[self.step])
            # print(self.src.data.close[self.step])
            for i in range(kaicangshu):
                if self.B.iloc[i].action == 2 and self.B.iloc[i].cangwei == 1:  # 如果有卖单

                    if self.B.iloc[i].close_price == 0:  # 如果有未平的单子。

                        self.B.loc[i,'close_price'] = self.src.data.close[self.step]

                        self.B.loc[i,'profit'] = (self.B.iloc[i].open_price - self.B.iloc[i].close_price) * 10000 * lots

                        # reward = reward + self.B.loc[i,'profit']

                        # if self.B.loc[i, 'profit'] > 0:
                        #     reward = reward + 1
                        # elif self.B.loc[i, 'profit'] < 0:
                        #     reward = reward - 1
                        # else:
                        #     pass

                    else:  # 如果没有未平的
                        pass
                else:
                    pass

            df2 = pd.DataFrame({'cangwei': 1,
                                'action': self.actions[self.step],
                                'open_price': self.src.data.close[self.step],
                                'close_price': 0,
                                'profit': 0
                                }, index=[0])
            self.B = self.B.append(df2, ignore_index=True)
            # print(self.B)


        elif self.actions[self.step] == 2:
                for i in range(kaicangshu):
                    if self.B.iloc[i].action == 1 and self.B.iloc[i].cangwei == 1:  # 如果有卖单

                        if self.B.iloc[i].close_price == 0:  # 如果有未平的单子。

                            self.B.loc[i,'close_price'] = self.src.data.close[self.step]

                            self.B.loc[i,'profit'] = (self.B.iloc[i].close_price - self.B.iloc[i].open_price ) * 10000 * lots

                            # reward = reward + self.B.loc[i, 'profit']

                            # if self.B.loc[i,'profit'] > 0:
                            #     reward = reward + 1
                            # elif self.B.loc[i,'profit'] < 0:
                            #     reward = reward - 1
                            # else:
                            #     pass

                        else:  # 如果没有未平的
                            pass
                    else:
                        pass


                df2 = pd.DataFrame({'cangwei': 1,
                                    'action': 2,
                                    'open_price': self.src.data.close[self.step],
                                    'close_price': 0,
                                    'profit': 0
                                    }, index=[0])
                self.B = self.B.append(df2, ignore_index=True)
                # print(self.B)









        P_line= self.B.apply(lambda x: x.sum())

        self.total_profit = P_line.profit
        reward = self.total_profit
        # print('reward =',reward)
        # print('total is ',self.total_profit)
    #
    #
    #     if profit > 0:
    #         reward = reward + 1
    #         #balance = balance + profit
    #     else:
    #         #balance = balance + profit
    #     #if balance > 20000:
    #         reward = reward + 1000
    #
    #     self.navs[self.step] =  bod_nav * (1 + self.strat_retrns[self.step-1])
    #     self.mkt_nav[self.step] =  mkt_nav * (1 + self.mkt_retrns[self.step-1])
    #
    info = { 'reward': reward, 'nav':self.navs[self.step], 'costs':self.costs[self.step] }

    self.step += 1
    return reward, info

  def to_df(self):
    """returns internal state in new dataframe """
    # cols = ['action', 'bod_nav', 'mkt_nav','mkt_return','sim_return',
    #         'position','costs', 'trade' ]
    # rets = _prices2returns(self.navs)
    # #pdb.set_trace()
    # # df = pd.DataFrame( {'action':     self.actions, # today's action (from agent)
    # #                       'bod_nav':    self.navs,    # BOD Net Asset Value (NAV)
    # #                       'mkt_nav':  self.mkt_nav,
    # #                       'mkt_return': self.mkt_retrns,
    # #                       'sim_return': self.strat_retrns,
    # #                       'position':   self.posns,   # EOD position
    # #                       'costs':  self.costs,   # eod costs
    # #                       'trade':  self.trades },# eod trade
    # #                      columns=cols)
    C_cols = ['action', 'open_price', 'close_price', 'total_profit']

    df = pd.DataFrame({'action': self.actions,
                        'open_price': self.open_price,
                        'close_price': self.close_price,
                        'total_profit': self.total_profit}, columns=C_cols)
    return df

  def to_df1(self):
      C_cols = ['action', 'open_price', 'close_price', 'total_profit']

      df1 = pd.DataFrame({'action': self.actions,
                          'open_price': self.open_price,
                          'close_price': self.close_price,
                          'total_profit':self.total_profit},columns=C_cols)

      return df1


class TradingEnv(gym.Env):
  """This gym implements a simple trading environment for reinforcement learning.

  The gym provides daily observations based on real market data pulled
  from Quandl on, by default, the SPY etf. An episode is defined as 252
  contiguous days sampled from the overall dataset. Each day is one
  'step' within the gym and for each step, the algo has a choice:

  SHORT (0)
  FLAT (1)
  LONG (2)

  If you trade, you will be charged, by default, 10 BPS of the size of
  your trade. Thus, going from short to long costs twice as much as
  going from short to/from flat. Not trading also has a default cost of
  1 BPS per step. Nobody said it would be easy!

  At the beginning of your episode, you are allocated 1 unit of
  cash. This is your starting Net Asset Value (NAV). If your NAV drops
  to 0, your episode is over and you lose. If your NAV hits 2.0, then
  you win.

  The trading env will track a buy-and-hold strategy which will act as
  the benchmark for the game.

  """
  metadata = {'render.modes': ['human']}

  def __init__(self):
    self.days = len(open(r"/home/rocc78/Documents/EURUSD240.csv", 'rU').readlines())
    self.src = FromCSVEnvSrc(days=self.days)
    self.sim = TradingSim(steps=self.days, trading_cost_bps=1e-3,
                          time_cost_bps=1e-4)
    self.action_space = spaces.Discrete( 3 )
    self.observation_space= spaces.Box( self.src.min_values,
                                        self.src.max_values)
    self.reset()

  def _configure(self, display=None):
    self.display = display

  def _seed(self, seed=None):
    self.np_random, seed = seeding.np_random(seed)
    return [seed]

  def _step(self, action):
    assert self.action_space.contains(action), "%r (%s) invalid"%(action, type(action))
    observation, done = self.src._step()
    # Close    Volume     Return  ClosePctl  VolumePctl
    yret = observation[2]

    reward, info = self.sim._step( action, yret )
      
    #info = { 'pnl': daypnl, 'nav':self.nav, 'costs':costs }

    return observation, reward, done, info
  
  def _reset(self):
    self.src.reset()
    self.sim.reset()
    return self.src._step()[0]
    
  def _render(self, mode='human', close=False):
    #... TODO
    pass

  # some convenience functions:
  
  def run_strat(self,  strategy, return_df=True):
    """run provided strategy, returns dataframe with all steps"""
    observation = self.reset()
    done = False
    while not done:
      action = strategy( observation, self ) # call strategy

      observation, reward, done, info = self.step(action)

    return self.sim.to_df1() if return_df else None
      
  def run_strats( self, strategy, episodes=1, write_log=True, return_df=True):
    """ run provided strategy the specified # of times, possibly
        writing a log and possibly returning a dataframe summarizing activity.
    
        Note that writing the log is expensive and returning the df is moreso.  
        For training purposes, you might not want to set both.
    """
    logfile = None
    if write_log:
      logfile = tempfile.NamedTemporaryFile(delete=False)
      log.info('writing log to %s',logfile.name)
      need_df = write_log or return_df

    alldf = None
        
    for i in range(episodes):
      df = self.run_strat(strategy, return_df=need_df)
      if write_log:
        df.to_csv(logfile, mode='a')
        if return_df:
          alldf = df if alldf is None else pd.concat([alldf,df], axis=0)
            
    return alldf


if __name__ == "__main__":

    showdata = TradingEnv()
    #showdata1 = FromCSVEnvSrc(days=)

    print(showdata.sim.B)
