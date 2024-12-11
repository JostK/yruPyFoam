# yruPyFoam
Python functions for OpenFOAM® developed at Yacht Research Unit Kiel.\
This Python module supports reading and writing of entries in OpenFOAM® dictionaries, analysis of log and postProcessing files, grading and y+ calculation, as well as many other functionalities.

## Installation
Requires Python (version 3.9 or newer) to be installed along with the following packages
* numpy
* scipy
* pandas

Now, you can simply go to the folder you want to use *yruPyFoam* in, clone the repository
```bash
git clone https://github.com/JostK/yruPyFoam.git
```
(or download the source code manually).

The required packages are listed in the `requirements.txt` from this repository and can be installed (after download/clone) with 
```bash
cd yruPyFoam
pip install -r requirements.txt
```

## Usage Examples
Read pressure fields from the last time directory and calculate the average:
```python
import numpy as np
from yruPyFoam.readWriteFoam import readKey
from yruPyFoam.postProcessing import getLatestTimeDir

# find the last time dirctory
time = getLatestTimeDir()

# read the fields as lists
internalField = readKey(f"./{time}/p", "internalField")
objectPatch = readKey(f"./{time}/p", "boundaryField/object/value")

# print the mean values
print(f"The mean pressure in the domain is {np.mean(internalField)}")
print(f"The mean on the patch 'object' is {np.mean(objectPatch)}")
```

Set boundary condition for U at patch "inlet":
```python
from yruPyFoam.readWriteFoam import 

bcType = "fixedValue"
velocity = [15, 0, 0] # 15 m/s in x direction

# overwrite possible existing entries by specifying and empty subdict for the patch
writeValue("0/U", "boundaryField/inlet", '{ }')
# specify the boundary condition type as str
writeValue("0/U", "boundaryField/inlet/type", bcType)
# specify the value as list with three entries (vector). yruPyFoam will automatically add the "uniform" keyword.
writeValue("0/U", "boundaryField/inlet/value", velocity)
```

Plot force coefficients from postProcessing file
```python
import numpy as np
import matplotlib.pyplot as plt
from yruPyFoam.readWriteFoam import readPostProcessingFile

# read the file into a pandas dataFrame
data = readPostProcessingFile("./postProcessing/forceCoeffs1/0/coefficient.dat")
time = data["Time"]
Cl = data["Cl"]
Cd = data["Cd"]

# calculate mean values
print(f"mean Cl: {np.mean(Cl)}    Cd: {np.mean(Cd)}")

# plot Cl
plt.plot(time, Cl)
plt.show()
```

## License
*yruPyFoam* is distributed under the [GPL v3](http://www.gnu.org/licenses/quick-guide-gplv3.html) licence.

*yruPyFoam* is research software, it is shared in the hope that it will be useful, but without any warranty; 
without even the implied warranty of merchantability or fitness for a particular purpose. 
See the GNU General Public License for details.

## Contributors
Jan Mense \
Jost Kemper

## Disclaimer
This offering is not approved or endorsed by OpenCFD Limited, producer and distributor of the OpenFOAM software via www.openfoam.com, and owner of the OPENFOAM®  and OpenCFD®  trade marks.

---
*[OpenFOAM®]: OPENFOAM® is a registered trade mark of OpenCFD Limited, producer and distributor of the OpenFOAM software via www.openfoam.com.
