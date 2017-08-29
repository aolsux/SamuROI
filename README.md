[<img src="https://readthedocs.org/projects/samuroi/badge/?version=latest">](http://samuroi.readthedocs.io/en/latest/?badge=latest)

# SamuROI
You can find the API documentation and examples at: http://samuroi.readthedocs.io/en/latest/

## Installation
SamuROI installation was tested on:
 - Windows7-64bit, newer windows should also work.
 - Ubuntu 16.04 LTS
 - macOS
 
### Development installation with conda
 1. Download and install [anaconda](https://www.continuum.io/downloads) 
 2. Download and extract or git clone SamuROI
 3. Install dependencies
 
    Open a terminal to first install SamuROI dependencies. Text in `this font` represents terminal commands.
    - `conda install conda-build` 
    - `conda install pyqt`
    - `conda install cached-property` 
    
    Finally, opencv does not ship official packages for all operation systems.
    On windows try `conda install -c menpo opencv=2.4.11`, on linux and mac try `conda install opencv`.
    If the opencv installation fails, SamuROI should still work, but the image stabilization will not be supported.
 4. Install SamuROI as a conda develop package: `conda develop <path/to/samuroi>`. Here <path/to/samuroi> denotes the samuroi root directory where you can e.g. find this Readme.md file.
 
You should now be able to `import samuroi` in python. To try it out open an IPython notebook and type in the following:

```
%matplotlib qt5
import samuroi
import numpy

# create some random data
data = numpy.random.normal(size=(100,100,30))
morphology = numpy.random.normal(size = (100,100))

#show the gui 
app = samuroi.SamuROIWindow(data = data,morphology=morphology)
app.show()
```

### Troubleshooting
If problems with dependency conflicts of python packages arise we recommend to use condas virtual environment functionality.
To do so, open a terminal, navigate to the downloaded samuroi directory, and type:

```conda env create -n samuroi```

This creates an environment with all of the packages that SamuROI is dependent on installed. An environment is a working space with its own version of python. All packages you install into the environment are distinct from your main system's python packages and will not clash with your other installed packages. More info: https://conda.io/docs/using/envs.html

Until we have set up SamuROI installation directly with conda, there is one final step, which tells conda where to look to find your version of SamuROI, which you should have downloaded or cloned somewhere on your computer:

```conda develop -n samuroi <path/to/samuroi>```

When you need to use SamuROI, you need to type `source activate samuroi` in a terminal. If you are using windows you can simply type `activate samuroi`.

    
### Via package manager (hopefully comming soon)
We hope to support a conda package soon! Contributions including a travis-ci setup are highly appreciated.
As there exist no official pip packages for opencv and pyqt, installation of SamuROI via pip is not officially supported.
