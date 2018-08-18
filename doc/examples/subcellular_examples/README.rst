This folder contains a working example for using SamuROI on dendrites and spines. 

- 'exampledendritetimeseries.tif' is the image sequence to be analyzed.

For generating the .swc file in neutube, we first generated a maximum intensity projection of the time series in Fiji. In order to be read by neutube, we generated a 'mock' stack by duplicating the image and merging the two identical images into the 'exampledendritesmockStack.tif' file. This file can be imported into neutube to generate the 'exampledendrite.swc' file. 
When SamuROI imports the swc, it will automatically be flattened.
