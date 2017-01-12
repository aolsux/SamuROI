import numpy
import scipy
import scipy.signal


def F0(data, mode, **kwargs):
    if mode == "stdv":
        return stdv_F0(data, **kwargs)
    if mode == "median":
        return median_F0(data)
    if mode == "linear_bleech":
        return linbleeched_F0(data)
    raise Exception("Unknown mode: " + mode)


def deltaF(data, mode, windows=None, F0=None, **kwargs):
    if mode == "stdv":
        return stdv_deltaF(data, F0=F0, **kwargs)
    if mode == "median":
        return median_deltaF(data)
    if mode == "linear_bleech":
        return linbleeched_deltaF(data, F0=F0)
    raise Exception("Unknown mode: " + mode)


def stdv_F0(data, windows=None):
    """
    Calculate the baseline for each pixel of data.
    Subdivides data in blocks of B frames and calculate the standard deviation for each block.
    Then takes the block with minimum standard deviation and calculate the mean of that block.
    The above is done on a per pixel basis. I.e. different pixels can have the mean calculated for
    different blocks.

    :param data: NxMxF array, where F is number of frames and NxM is image shape.
    :param windows: The number of windows to use. Default: split the data in blocks of 100 frames. If data.shape[2] mod 100 != 0 drop the frames that are remaining.
    :return: NxM array with baseline for each pixel.
    """
    X, Y, T = data.shape

    # default behaviour, cut of overhanging frames
    if windows is None:
        mod = T % 100
        windows = T / 100
        data = data[..., :windows * 100]
        T = windows * 100
    elif T % windows != 0:
        raise ValueError("Cannot split data with {} frames into {} equally sized blocks".format(T, windows))

    windowed = numpy.reshape(data, newshape=(X, Y, windows, T / windows))

    # calculate stdv over each block for each pixel
    stdvs = numpy.std(windowed, axis=3)

    # find the block where the stdv is minimal
    minblocks = numpy.argmin(stdvs, axis=2)

    # select mean from window with lowes stdv
    # wee need fancy indexing here to get numpy to accept he index array
    # returned by numpy.argmin
    k, j = numpy.meshgrid(numpy.arange(Y), numpy.arange(X))

    means = windowed[j, k, minblocks, :].mean(axis=2)

    return means


def stdv_deltaF(data, F0=None, windows=None):
    """
    Calculate the fraction dF/F0 for each pixel. F0 is assumed to not depend on time, but on spatial coordinates.
    for the definition of F0 see :py:func:`samuroi.plugins.baseline.stdv_F0`.

    :param data: The video data, shape M,N,T
    :param F0: precalculated F0 or None(default calculate F0 internally)
    :param windows: The number of windows, forwarded to stdv_F0
    :return:  numpy.array with shape M,N,T with values :math:`(F(x,y,t)-F0(x,y))/F0(x,y)`
    """
    if F0 is None:
        F0 = stdv_F0(data=data, windows=windows)
    # use numpy broadcasting to do the calculation
    data = (data - F0[..., numpy.newaxis]) / F0[..., numpy.newaxis]

    return data


def power_spectrum(data, fs):
    """
    Calculate the power spectrum for each pixel and then average over all pixels.

    :param data: the 3D video data.
    :param fs: sampling frequency.bla
    :return: tuple(df,avgpower) where df is a 1d array of frequencies and avgpower is a 1D array with the respective average power.
    """
    N = data.shape[-1] / 2
    _dfft = numpy.fft.fft(data, axis=-1)
    avgpower = (_dfft * numpy.conjugate(_dfft)).mean(axis=(0, 1))[0:N].real
    df = numpy.fft.fftfreq(n=data.shape[-1], d=1. / fs)[0:N]
    return df, avgpower


def bandstop(data, fs, start, stop, order = 3):
    """
    Apply bandstop filter on data.

    :param data: 3D video data
    :param fs: sampling frequency
    :param order: the order of butter filter used.
    :param start: lower frequency where band starts
    :param stop: higher frequency where band ends
    :return: the filtered 3d data set.
    """
    nyq = 0.5 * fs
    high = stop / nyq
    low = start / nyq
    order = order
    b, a = scipy.signal.butter(order, [low, high], btype='bandstop')
    # zi = scipy.signal.lfiltic(b, a, y=[0.])
    dataf = scipy.signal.lfilter(b, a, data)
    return dataf


def linbleeched_F0(data):
    """
    Calculate a linear fit (y(t)=m*t+y0) for each pixel, which is assumed to correct for bleeching effects.

    :param data: he video data of shape (M,N,T).
    :return: tuple (m,y0) with two images each with shape (M,N).
    """

    # generate c coordinates
    x = numpy.arange(data.shape[-1])
    # reshape the data to two d array, first dimension is pixel index, second dimension is time
    d = numpy.reshape(data, (data.shape[0] * data.shape[1], data.shape[-1]))
    # find fit parameters
    m, y0 = numpy.polyfit(x, d.T, 1)
    # reshape fit parameters back to image shape
    return m.reshape(data.shape[0:2]), y0.reshape(data.shape[0:2])


def linbleeched_deltaF(data, F0=None):
    """
    Assumes that the fluorescence F0 follows linear bleeching (see  :py:func:`samuroi.plugins.baseline.linbleeched_F0`).
    Determines the linear fit parameters m,y0 for :math:`F_0(t) = m f(t)+y_0`. Then uses :math:`F_0(t)` to calculate
    :math:`(F(t)-F_0(t))/F_0(t)`.

    :param data:  The video data of shape (M,N,T).
    :param F0:
    :return: deltaF/F0 for bleech corrected :math:`F_0(t)`.
    """
    # get fit parameters
    if F0 is None:
        m, y0 = linbleeched_F0(data)
    else:
        m, y0 = F0

    # get x coordinates
    x = numpy.arange(data.shape[-1])
    # do outer product to apply linear drift, then add offset values with new axis, because they don't depend on time
    f0 = numpy.multiply.outer(m, x) + y0[:, :, numpy.newaxis]
    # return deltaF/F0
    return (data - f0) / f0


def median_F0(data):
    """
    Calculate a time dependent F0, which does not depend on spatial coordinates.
    The definition is as follows:
    :math:`F_0(t)` = median(:math:`F(x,y,t)` for all x,y)

    :param data: The video data of shape (M,N,T).
    :return: F0 array of shape (T,).
    """
    return numpy.median(data.reshape(data.shape[0] * data.shape[1], data.shape[-1]), axis=0)


def median_deltaF(data):
    """
    Apply the deltaF/F transformation with :math:`F_0` defined as in :py:func:`samuroi.plugins.baseline.median_F0`.

    :param data: The video data of shape (M,N,T).
    :return: deltaF/F0 for median :math:`F_0(t)`.
    """

    f0 = median_F0(data)
    return (data - f0[numpy.newaxis, numpy.newaxis, :]) / f0[numpy.newaxis, numpy.newaxis, :]
