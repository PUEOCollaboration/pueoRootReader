from analysis.reader import PUEORootReader
from matplotlib import pyplot as plt
import numpy as np

datafile = "data/ROOT/run0839/007900.root"

# an object containing the data. By default, the first run and event found are "active"
data = PUEORootReader(datafile) # you can specify the active event when creating this instance: PUEORootReader(datafile, event=7763)

fig, axes = plt.subplots(ncols=14, nrows=16, figsize=(100,55))
ax = np.ravel(axes)

# plotting all channels
for i, channel in enumerate(data.channel_ids):
    ax[i].plot(data.time, data.getWF(channel))
    ax[i].annotate(f'Ch{channel}', (0,1), xycoords="axes fraction", fontsize=14, ha='left', va='top')

fig.tight_layout()
plt.show()