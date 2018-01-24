# coding: utf-8

from __future__ import unicode_literals

import json
import logging
import numpy as np
import os
import unittest

from amset import AMSET
from tools import rel_diff

test_dir = os.path.dirname(__file__)

class AmsetTest(unittest.TestCase):
    def setUp(self):
        self.model_params = {'bs_is_isotropic': True,
                             'elastic_scatterings': ['ACD', 'IMP', 'PIE'],
                             'inelastic_scatterings': ['POP']}
        self.performance_params = {'dE_min': 0.0001, 'nE_min': 2,
                'parallel': True, 'BTE_iters': 5,'nkdos':29, 'max_nbands': 1,
                'max_normk': 2, 'Ecut': 0.4, 'fermi_kgrid_tp': 'coarse'}
        self.GaAs_params = {'epsilon_s': 12.9, 'epsilon_inf': 10.9,
                'W_POP': 8.73, 'C_el': 139.7, 'E_D': {'n': 8.6, 'p': 8.6},
                'P_PIE': 0.052, 'scissor': 0.5818,
                'important_points':{tp:[[0.0, 0.0, 0.0]] for tp in ['p', 'n']}}
        self.GaAs_path = os.path.join(test_dir, '..', 'test_files', 'GaAs')
        self.GaAs_cube = os.path.join(self.GaAs_path, "fort.123_GaAs_1099kp")

    def tearDown(self):
        pass


    def test_poly_bands(self):
        print('\ntesting test_poly_bands...')
        mass = 0.25
        c = -2e15
        temperatures = [300]
        self.model_params['poly_bands'] = [[[[0.0, 0.0, 0.0], [0.0, mass]]]]
        amset = AMSET(calc_dir=self.GaAs_path,material_params=self.GaAs_params,
                      model_params=self.model_params,
                      performance_params=self.performance_params,
                      dopings=[c], temperatures=temperatures, k_integration=True,
                      e_integration=False, fermi_type='k',
                      loglevel=logging.ERROR)
        amset.run(self.GaAs_cube, kgrid_tp='coarse', write_outputs=False)

        # check fermi level
        # density calculation source: http://hib.iiit-bh.ac.in/Hibiscus/docs/iiit/NBDB/FP008/597_Semiconductor%20in%20Equilibrium&pn%20junction1.pdf
        # density of states source: http://web.eecs.umich.edu/~fredty/public_html/EECS320_SP12/DOS_Derivation.pdf
        for T in temperatures:
            N_c = 2 * (2 * np.pi * mass * 9.11e-31 * 1.3806e-23 * T / ((6.626e-34)**2))**1.5
            expected_fermi_level = amset.cbm_vbm['n']["energy"] - (1.3806e-23 * T * np.log(N_c / (-c * 1e6)) * 6.242e18)

            diff = abs(amset.fermi_level[c][T] - expected_fermi_level)
            avg = (amset.fermi_level[c][T] + expected_fermi_level) / 2
            self.assertTrue(diff / avg < 0.02)

            diff = abs(np.array(amset.mobility['n']['ACD'][c][T]) - \
                       np.array(amset.mobility['n']['SPB_ACD'][c][T]))
            avg = (amset.mobility['n']['ACD'][c][T] + \
                   amset.mobility['n']['SPB_ACD'][c][T]) / 2
            self.assertTrue((diff / avg <= 0.01).all())


    def test_GaAs_isotropic_E(self):
        print('\ntesting test_GaAs_isotropic_E...')
        expected_mu = {'ACD': 52617.3, 'IMP': 154824.3, 'PIE': 111864.7,
                       'POP': 7706.8, 'overall': 5432.5, 'average': 6091.7}
        amset = AMSET(calc_dir=self.GaAs_path, material_params=self.GaAs_params,
                      model_params=self.model_params,
                      performance_params=self.performance_params,
                      dopings=[-2e15], temperatures=[300], k_integration=False,
                      e_integration=True, fermi_type='e',
                      loglevel=logging.DEBUG)
        amset.run(self.GaAs_cube, kgrid_tp='very coarse', write_outputs=False)
        kgrid = amset.kgrid

        # check general characteristics of the grid
        self.assertEqual(kgrid['n']['velocity'][0].shape[0], 100)
        mean_v = np.mean(kgrid['n']['velocity'][0], axis=0)
        self.assertAlmostEqual(np.std(mean_v), 0.00, places=2) # isotropic BS
        self.assertAlmostEqual(mean_v[0], 32253886.41, places=1) # zeroth band

        # check mobility values
        for mu in expected_mu.keys():
            self.assertAlmostEqual(np.std( # test isotropic
                amset.mobility['n'][mu][-2e15][300]), 0.00, places=1)
            self.assertAlmostEqual(amset.mobility['n'][mu][-2e15][300][0],
                    expected_mu[mu], places=1)


    def test_GaAs_isotropic_k(self):
        print('\ntesting test_GaAs_isotropic_k...')
        # if norm(prop)/sq3 is imposed in map_to_egrid if bs_is_isotropic
        # expected_mu = {'ACD': 68036.7, 'IMP': 82349394.9, 'PIE': 172180.7,
        #                'POP': 10113.9, 'overall': 8173.4}

        expected_mu = {'ACD': 101397.6, 'IMP': 120715.8, 'PIE': 325384.2,
                       'POP': 13329.2, 'overall': 9235.7, 'average': 10390.4}
        performance_params = dict(self.performance_params)
        amset = AMSET(calc_dir=self.GaAs_path, material_params=self.GaAs_params,
                      model_params=self.model_params,
                      performance_params=performance_params,
                      dopings=[-3e13], temperatures=[300], k_integration=True,
                      e_integration=False, fermi_type='k',
                      loglevel=logging.ERROR)
        amset.run(self.GaAs_cube, kgrid_tp='very coarse', write_outputs=False)
        mobility = amset.mobility


        # check fermi level
        # expected_fermi = amset.cbm_vbm['n']["energy"] - 0.2477
        # print('expected_fermi = {}'.format(expected_fermi))
        # print('k calculated fermi = {}'.format(amset.fermi_level[-3e13][300]))
        # diff = abs(amset.fermi_level[-3e13][300] - expected_fermi)
        # avg = (amset.fermi_level[-3e13][300] + expected_fermi) / 2
        # self.assertTrue(diff / avg < 0.02)

        self.assertAlmostEqual(amset.fermi_level[-3e13][300], 0.846, 3)

        # check mobility values
        for mu in expected_mu.keys():
            diff = np.std(mobility['n'][mu][-3e13][300])
            avg = np.mean(mobility['n'][mu][-3e13][300])
            self.assertLess(diff / avg, 0.002)
            self.assertAlmostEqual(mobility['n'][mu][-3e13][300][0],
                                   expected_mu[mu], places=1)

    # #TODO: since we run through several different k-meshes now for varous valleys, egrid changes hence egrid tests may be changing and ignored for now
    def test_GaAs_anisotropic(self):
        print('\ntesting test_GaAs_anisotropic...')
        expected_mu = {'ACD': 47957.55, 'IMP': 139521.01, 'PIE': 112012.93,
                       'POP': 8552.04, 'overall': 5914.90, 'average': 6498.66}
        amset = AMSET(calc_dir=self.GaAs_path,
                      material_params=self.GaAs_params,
                      model_params={'bs_is_isotropic': False,
                             'elastic_scatterings': ['ACD', 'IMP', 'PIE'],
                             'inelastic_scatterings': ['POP']},
                      performance_params=self.performance_params,
                      dopings=[-2e15], temperatures=[300], k_integration=False,
                      e_integration=True, fermi_type='e',
                      loglevel=logging.ERROR)
        amset.run(self.GaAs_cube, kgrid_tp='very coarse', write_outputs=False)
        # check mobility values
        for mu in expected_mu.keys():
            self.assertLessEqual(np.std(  # GaAs band structure is isotropic
                amset.mobility['n'][mu][-2e15][300]), 0.02*\
                np.mean(amset.mobility['n'][mu][-2e15][300]))
            self.assertLess(rel_diff(amset.mobility['n'][mu][-2e15][300][0], expected_mu[mu]), 0.02)

    def test_defaults(self):
        print('\ntesting test_defaults...')
        amset = AMSET(self.GaAs_path, material_params={'epsilon_s': 12.9})
        amset.write_input_files()
        with open("material_params.json", "r") as fp:
            material_params = json.load(fp)
        with open("model_params.json", "r") as fp:
            model_params = json.load(fp)
        with open("performance_params.json", "r") as fp:
            performance_params = json.load(fp)

        self.assertEqual(material_params['epsilon_inf'], None)
        self.assertEqual(material_params['W_POP'], None)
        self.assertEqual(material_params['scissor'], 0.0)
        self.assertEqual(material_params['P_PIE'], 0.15)
        self.assertEqual(material_params['E_D'], None)
        self.assertEqual(material_params['N_dis'], 0.1)

        self.assertEqual(model_params['bs_is_isotropic'], True)
        self.assertEqual(model_params['elastic_scatterings'], ['IMP', 'PIE'])
        self.assertEqual(model_params['inelastic_scatterings'], [])

        self.assertEqual(performance_params['max_nbands'], None)
        self.assertEqual(performance_params['max_normk'], 2)
        self.assertEqual(performance_params['dE_min'], 0.0001)
        self.assertEqual(performance_params['nkdos'], 29)
        self.assertEqual(performance_params['dos_bwidth'], 0.05)
        self.assertEqual(performance_params['nkdos'], 29)


    # def test_GaAs_anisotropic_k(self):
    #     print('\ntesting test_GaAs_anisotropic_k...')
    #     # if norm(prop)/sq3 is imposed in map_to_egrid if bs_is_isotropic
    #     # expected_mu = {'ACD': 68036.7, 'IMP': 82349394.9, 'PIE': 172180.7,
    #     #                'POP': 10113.9, 'overall': 8173.4}
    #
    #     expected_mu = {'overall': 4327.095}
    #     performance_params = dict(self.performance_params)
    #     performance_params["max_nbands"] = 1
    #     amset = AMSET(calc_dir=self.GaAs_path, material_params=self.GaAs_params,
    #                   model_params=self.model_params,
    #                   performance_params=performance_params,
    #                   dopings=[-3e13], temperatures=[300], k_integration=True,
    #                   e_integration=False, fermi_type='k',
    #                   loglevel=logging.ERROR)
    #     amset.run(self.GaAs_cube, kgrid_tp='very fine', write_outputs=False, test_k_anisotropic=True)
    #     mobility = amset.mobility
    #     kgrid = amset.kgrid
    #
    #     # check mobility values
    #     for mu in expected_mu.keys():
    #         diff = np.std(mobility['n'][mu][-3e13][300])
    #         avg = np.mean(mobility['n'][mu][-3e13][300])
    #         self.assertLess(diff / avg, 0.002)
    #         diff = abs(mobility['n'][mu][-3e13][300][0] - expected_mu[mu])
    #         avg = (mobility['n'][mu][-3e13][300][0] + expected_mu[mu]) / 2
    #         self.assertTrue(diff / avg <= 0.01)


if __name__ == '__main__':
    unittest.main()