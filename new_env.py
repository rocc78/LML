import numpy as np
import pandas as pd





class FromCSVEnvSrc(object):
  '''


  '''


  Name = "TSE/9994"  # https://www.quandl.com/search (use 'Free' filter)

  def __init__(self, days, name=Name, auth=QuandlAuthToken, scale=True):
    self.name = name
    self.auth = auth
    self.days = days #len(open(r"/home/rocc78/Documents/EURUSD240.csv", 'rU').readlines())

    df  = pd.read_csv('/home/rocc78/Documents/EURUSD240.csv',index_col=[0,1])


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

  def render(self):
      pass

  np.random.choice()