#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `codex-africanus` package."""

import numpy as np

import pytest

def test_phase_delay():
    from africanus.rime import phase_delay

    uvw = np.random.random(size=(100,3))
    lm = np.random.random(size=(10,2))
    frequency = np.linspace(.856e9, .856e9*2, 64, endpoint=True)

    from africanus.constants import minus_two_pi_over_c

    # Test complex phase at a particular index in the output
    uvw_i, lm_i, freq_i = 2, 3, 5

    u, v, w = [1,2,3]
    l, m = [0.1, 0.2]
    freq = 0.856e9

    # Set up values in the input
    uvw[uvw_i] = [u, v, w]
    lm[lm_i] = [l, m]
    frequency[freq_i] = freq

    # Compute complex phase
    complex_phase = phase_delay(uvw, lm, frequency)

    # Test singular value vs a point in the output
    n = np.sqrt(1.0 - l**2 - m**2) - 1.0
    phase = minus_two_pi_over_c*(u*l + v*m + w*n)*freq
    assert np.all(np.exp(1j*phase) == complex_phase[lm_i, uvw_i, freq_i])


def test_brightness():
    import numpy as np
    from africanus.rime import brightness

    # One stokes
    stokes = np.asarray([[1], [5]])
    B = brightness(stokes, polarisation_type='linear')
    assert np.all(B == [[1],[5]])

    B = brightness(stokes, polarisation_type='circular')
    assert np.all(B == [[1],[5]])

    # Two stokes parameters
    stokes = np.asarray([[1, 2], [5, 6]], dtype=np.float64)

    # Linear (I and Q)
    B = brightness(stokes, polarisation_type='linear')
    expected = np.asarray([[[1+2], [1-2]], [[5+6], [5-6]]])
    assert np.all(B == expected)

    # Circular (I and V) produce the same result as linear
    B = brightness(stokes, polarisation_type='circular')
    assert np.all(B == expected)

    B = brightness(stokes, polarisation_type='linear', corr_shape='flat')
    assert np.all(B==expected.reshape(2,2))

    # Four stokes parameters
    stokes = np.asarray([[1, 2, 3, 4], [5, 6, 7, 8]], dtype=np.float64)

    # Linear (I,Q,U,V)
    B = brightness(stokes, polarisation_type='linear')
    expected = np.asarray([[1+2, 3+4*1j, 3-4*1j, 1-2],
                            [5+6,7+8*1j,7-8*1j,5-6]])
    assert np.all(B==expected.reshape(2,2,2))

    # Circular (I,Q,U,V)
    B = brightness(stokes, polarisation_type='circular')
    expected = np.asarray([[1+4, 2+3*1j, 2-3*1j, 1-4],
                            [5+8,6+7*1j,6-7*1j,5-8]])
    assert np.all(B==expected.reshape(2,2,2))

    # Test correlation shape
    B = brightness(stokes, polarisation_type='linear', corr_shape='flat')
    expected = np.asarray([[1+2, 3+4*1j, 3-4*1j, 1-2],
                            [5+6,7+8*1j,7-8*1j,5-6]]).reshape(2,4)
    assert np.all(B==expected)


def test_feed_rotation():
    import numpy as np
    from africanus.rime import feed_rotation

    parangles = np.random.random((10, 5))
    pa_sin = np.sin(parangles)
    pa_cos = np.cos(parangles)

    fr = feed_rotation(parangles, feed_type='linear')
    np_expr = np.stack([pa_cos, pa_sin, -pa_sin, pa_cos], axis=2)
    assert np.allclose(fr, np_expr.reshape(10,5,2,2))

    fr = feed_rotation(parangles, feed_type='circular')
    zeros = np.zeros_like(pa_sin)
    np_expr = np.stack([pa_cos - 1j*pa_sin, zeros,
                        zeros, pa_cos + 1j*pa_sin], axis=2)
    assert np.allclose(fr, np_expr.reshape(10,5,2,2))



def test_parallactic_angles():
    import numpy as np
    from africanus.rime import parallactic_angles

    time = np.random.random((5,)).astype(np.float64)
    ant = np.random.random((4,3)).astype(np.float64)
    fc = np.random.random((2,)).astype(np.float64)

    pa = parallactic_angles(time, ant, fc, backend='test')
    assert pa.shape == (5,4)


def test_brightness_shape():
    import numpy as np
    from africanus.rime import brightness

    for pol_type in ('linear', 'circular'):
        # 4 polarisation case
        assert brightness(np.random.random((10,5,3,4)),
            polarisation_type=pol_type,
            corr_shape='matrix').shape == (10,5,3,2,2)

        assert brightness(np.random.random((10,5,3,4)),
            polarisation_type=pol_type,
            corr_shape='flat').shape == (10,5,3,4)

        # 2 polarisation case
        assert brightness(np.random.random((10,5,3,2)),
            polarisation_type=pol_type,
            corr_shape='matrix').shape == (10,5,3,2,1)

        assert brightness(np.random.random((10,5,3,2)),
            polarisation_type=pol_type,
            corr_shape='flat').shape == (10,5,3,2)

        # 1 polarisation case
        assert brightness(np.random.random((10,5,3,1)),
            polarisation_type=pol_type,
            corr_shape='matrix').shape == (10,5,3,1)

        assert brightness(np.random.random((10,5,3,1)),
            polarisation_type=pol_type,
            corr_shape='flat').shape == (10,5,3,1)

from africanus.rime.dask import have_requirements

@pytest.mark.skipif(not have_requirements, reason="requirements not installed")
def test_dask_phase_delay():
    import dask.array as da
    from africanus.rime import phase_delay as np_phase_delay
    from africanus.rime.dask import phase_delay as dask_phase_delay

    uvw = np.random.random(size=(100,3))
    lm = np.random.random(size=(10,2))*0.01 # So that 1 > 1 - l**2 - m**2 >= 0
    frequency = np.linspace(.856e9, .856e9*2, 64, endpoint=True)

    dask_uvw = da.from_array(uvw, chunks=(25,3))
    dask_lm = da.from_array(lm, chunks=(5, 2))
    dask_frequency = da.from_array(frequency, chunks=16)

    dask_phase = dask_phase_delay(dask_uvw, dask_lm, dask_frequency).compute()
    np_phase = np_phase_delay(uvw, lm, frequency)

    # Should agree completely
    assert np.all(np_phase == dask_phase)


@pytest.mark.skipif(not have_requirements, reason="requirements not installed")
def test_dask_parallactic_angles():
    import dask.array as da
    from africanus.rime import parallactic_angles as np_parangle
    from africanus.rime.dask import parallactic_angles as da_parangle

    np_times = np.random.random(size=(5,))
    np_ants = np.random.random(size=(4,3))
    np_fc = np.random.random(size=2)

    np_pa = np_parangle(np_times, np_ants, np_fc, backend='test')

    da_times = da.from_array(np_times, chunks=(2,3))
    da_ants = da.from_array(np_ants, chunks=((2,2),3))
    da_fc = da.from_array(np_fc, chunks=2)

    da_pa = da_parangle(da_times, da_ants, da_fc, backend='test')

    from pprint import pprint

    assert np.all(np_pa == da_pa.compute())


@pytest.mark.skipif(not have_requirements, reason="requirements not installed")
def test_dask_brightness():
    import dask.array as da
    import numpy as np
    from africanus.rime.dask import brightness

    stokes = np.asarray([[1, 2, 3, 4], [5, 6, 7, 8]], dtype=np.float64)
    da_stokes = da.from_array(stokes, (1,4))

    B = brightness(da_stokes, polarisation_type='linear')
    expected = np.asarray([[1+2, 3+4*1j, 3-4*1j, 1-2],
                            [5+6,7+8*1j,7-8*1j,5-6]])
    assert np.all(B.compute()==expected)

    # Test correlation shape
    B = brightness(da_stokes, polarisation_type='linear', corr_shape='matrix')
    assert np.all(B.compute()==expected.reshape(2,2,2))


    B = brightness(da_stokes, polarisation_type='circular')
    expected = np.asarray([[1+4, 2+3*1j, 2-3*1j, 1-4],
                            [5+8,6+7*1j,6-7*1j,5-8]])

    # Test correlation shape
    B = brightness(da_stokes, polarisation_type='circular', corr_shape='matrix')
    assert np.all(B.compute()==expected.reshape(2,2,2))


@pytest.mark.skipif(not have_requirements, reason="requirements not installed")
def test_dask_brightness_shape():
    import dask.array as da
    from africanus.rime.dask import brightness

    for pol_type in ('linear', 'circular'):
        # 4 polarisation case
        stokes = da.random.random((10,5,3,4),chunks=(5,(2,3),(2,1),4))

        assert brightness(stokes,
            polarisation_type=pol_type,
            corr_shape='matrix').compute().shape == (10,5,3,2,2)

        assert brightness(stokes,
            polarisation_type=pol_type,
            corr_shape='flat').shape == (10,5,3,4)

        # 2 polarisation case
        stokes = da.random.random((10,5,3,2),chunks=(5,(2,3),(2,1),2))

        assert brightness(stokes,
            polarisation_type=pol_type,
            corr_shape='matrix').shape == (10,5,3,2,1)

        assert brightness(stokes,
            polarisation_type=pol_type,
            corr_shape='flat').shape == (10,5,3,2)

        # 1 polarisation case
        stokes = da.random.random((10,5,3,1),chunks=(5,(2,3),(2,1),1))

        assert brightness(stokes,
            polarisation_type=pol_type,
            corr_shape='matrix').shape == (10,5,3,1)

        assert brightness(stokes,
            polarisation_type=pol_type,
            corr_shape='flat').shape == (10,5,3,1)


@pytest.mark.skipif(not have_requirements, reason="requirements not installed")
def test_dask_feed_rotation():
    import dask.array as da
    import numpy as np
    from africanus.rime import feed_rotation as np_feed_rotation
    from africanus.rime.dask import feed_rotation

    parangles = np.random.random((10, 5))
    dask_parangles = da.from_array(parangles, chunks=(5, (2,3)))

    np_fr = np_feed_rotation(parangles, feed_type='linear')
    assert np.all(np_fr == feed_rotation(dask_parangles, feed_type='linear'))

    np_fr = np_feed_rotation(parangles, feed_type='circular')
    assert np.all(np_fr == feed_rotation(dask_parangles, feed_type='circular'))