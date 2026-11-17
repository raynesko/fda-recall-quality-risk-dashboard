import numpy as np
import pytest

from fda_recall.analysis import spc

TOL = 1e-9


def test_c_chart_hand_calc_no_laney():
    # baseline 2,4,3,5,6: cbar=4, sigma=2, z=-1,0,-.5,.5,1, MR mean=.75, sigma_z=.75/1.128<1 -> no widening
    cl, sigma, sz = spc.c_params(np.array([2, 4, 3, 5, 6]))
    assert cl == pytest.approx(4, abs=TOL) and sigma == pytest.approx(2, abs=TOL)
    assert sz == pytest.approx(0.75 / 1.128, abs=TOL)
    ucl, lcl = spc.limits(cl, sigma, sz)
    assert ucl == pytest.approx(10, abs=TOL) and lcl == pytest.approx(0, abs=TOL)  # 4-6 floored


def test_c_chart_laney_widens():
    # 0,8,0,8: cbar=4, z=-2,2,-2,2, MR=4 -> sigma_z = 4/1.128
    cl, sigma, sz = spc.c_params(np.array([0, 8, 0, 8]))
    assert sz == pytest.approx(4 / 1.128, abs=TOL)
    ucl, _ = spc.limits(cl, sigma, sz)
    assert ucl == pytest.approx(4 + 3 * 2 * 4 / 1.128, abs=TOL)


def test_p_chart_hand_calc():
    x, n = np.array([10, 20, 15]), np.array([100, 100, 100])
    pbar, sz = spc.p_params(x, n)
    assert pbar == pytest.approx(0.15, abs=TOL)
    s = np.sqrt(0.15 * 0.85 / 100)
    z = (np.array([0.10, 0.20, 0.15]) - 0.15) / s
    assert sz == pytest.approx(np.mean(np.abs(np.diff(z))) / 1.128, abs=TOL)
    ucl, lcl = spc.limits(pbar, s, sz)
    assert ucl == pytest.approx(0.15 + 3 * s * max(sz, 1), abs=TOL)
    assert lcl == pytest.approx(max(0.15 - 3 * s * max(sz, 1), 0), abs=TOL)


def test_rules():
    v = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, -1, 1], float)  # 9 above 0, then break
    r2 = spc.rule2(v, 0.0)
    assert r2.tolist() == [False] * 7 + [True, True, False, False]
    assert spc.rule2(np.zeros(10), 0.0).sum() == 0  # points on the CL never count
    r1 = spc.rule1(np.array([5, 11, 0]), np.array([10, 10, 10]), np.array([0, 0, 0]))
    assert r1.tolist() == [False, True, False]  # 0 is not below a floored LCL of 0
    assert spc.rule_id(True, True) == "R1+R2" and spc.rule_id(False, False) == ""


def test_phase1_iterative_removal_logs_outlier():
    v = np.array([3, 4, 3, 5, 4, 3, 40, 4, 5, 3], float)
    res = spc.chart(v, np.ones(10, bool), "c")
    assert 6 in res["removed"] and res["r1"][6]
    assert res["cl"][0] == pytest.approx(np.delete(v, 6).mean(), abs=TOL)


def test_simulation_runs_and_is_bounded():
    r = spc.simulate_false_alarms(5, n_series=50, n=60)
    assert 0 <= r["r1_per_point"] < 0.05 and 0 <= r["r2_any_in_series"] <= 1
