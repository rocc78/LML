import numpy as np
import pandas as pd



B_cols = ['cangwei', 'action', 'open_price', 'close_price', 'profit']

B = pd.DataFrame(columns=B_cols)
# print(B)
df2 = pd.DataFrame(np.random.randn(1,5),columns=B_cols)
# print(df2)
B = B.append(df2,ignore_index=True)

#B = B.drop(B.index)


#print(B.append(df2,ignore_index=True))

print(B.loc[B.index[1],'cangwei'])
