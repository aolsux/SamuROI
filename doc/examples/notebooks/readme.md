
In this folder you will find example ipython notebooks to get you started with using SamuROI and some of its optional features.

### Cell population
Here, you will find ipython notebooks and corresponding files to give you a working example for using SamuROI on cell populations:
* `cell_population_fake` will create some fake data set and operate on it as if it was real data for testing purpose.
* `cell_population_real` will run the same scripts on real data (requires download of data files)

Note: these examples require that [ilastik](http://ilastik.org/download.html) is installed.

An example ilastik project file `GCaMP.ilp` is included in the downloadable files. It will be used to call the ilastik relevant functions in the `cell_population_real.ipynb` notebook.

### Dendrites and spines
The `subcellular.ipynb` will give you a touch-base working example for using SamuROI on dendrites and spines. The ‘exampledendritetimeseries.tif’ file is the image sequence to be analyzed. It can be downloaded [here](www.todo-fixme-add-download.foo).
For generating the `.swc` file in neutube, we first generated a maximum intensity projection of the time series in Fiji. In order to be read by neutube, we generated a ‘mock’ stack by duplicating the image and merging the two identical images into the `exampledendritesmockStack.tif` file. This file can be imported into neutube to generate the `exampledendrite.swc` file. When SamuROI imports the swc, it will automatically be flattened.



