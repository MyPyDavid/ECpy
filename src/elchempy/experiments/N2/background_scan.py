"""

this module prepares a background scan from the N2 data for an ORR measurement

"""

## std lib
from typing import NamedTuple, Tuple, Dict
from collections import namedtuple
from pathlib import Path

import logging

logger = logging.getLogger(__name__)

## local
import elchempy

# from elchempy.dataloaders.fetcher import ElChemData
# from elchempy.experiments.N2.background_scan import contains_background_scan, get_N2_background_data

from elchempy.experiments.N2.plotting import N2_plot_raw_scans_scanrate

## 3rd party
import numpy as np
import pandas as pd
from scipy.stats import linregress, zscore

## constants
EvRHE = "E_vs_RHE"
#%%


def contains_background_scan(N2_CVs, maximum_scanrate=0.011, scan_length=2000):
    """checks if the data possibly contains a N2 background scan"""

    if not isinstance(N2_CVs, pd.DataFrame):
        return False

    if N2_CVs.empty:
        return False

    sr_min = N2_CVs.scanrate.min()

    if not (0 < sr_min <= maximum_scanrate):  # check presence of slow scanrates
        return False

    sr_grp_min = N2_CVs.loc[N2_CVs.scanrate == sr_min]
    if len(sr_grp_min) < scan_length:
        return False

    if not any(
        [n for n, gr in sr_grp_min.groupby("Segment #") if len(gr) == scan_length]
    ):
        return False

    return True


def get_N2_background_data(N2_CVs):

    if not contains_background_scan(N2_CVs):
        return None
    #            N2_scan = grA.get_group(('N2','Cyclic Voltammetry (Multiple Cycles)','0.1'))
    ### === Prepare the background N2 scan (10 mV/s) for ORR with exactly 2000 rows === ###
    preN2_scan = N2_CVs.drop_duplicates()

    sr_min = N2_CVs.scanrate.min()
    srgrpby = N2_CVs.groupby("scanrate")
    sr_grp_min = N2_CVs.loc[N2_CVs.scanrate == sr_min]
    # srgrpby.get_group

    if sr_min > 0.01:
        N2_factor = sr_min / 0.01
        N2_scan = preN2_scan.assign(
            **{"j_normalized_to_10mVs": preN2_scan.loc[:, "j A/cm2"] / N2_factor}
        )
        logger.warning(f"N2 scans minimun scanrate is larger than 10 mV/s")
    #                N2_scan.loc[:,'j A/cm2'] = N2_scan['j A/cm2']/N2_factor
    #                pd.DataFrame([ScanRates.min()])
    try:
        # lenpreN2 = len(preN2_scan)
        # N2_scan = preN2_scan
        if len(sr_grp_min) > 2001:
            logger.warning("!! N2 scan more than 2000 data points.. ")
            """
            select scan with multiple steps: # TODO
                take only scans from length 2000, these are "good" measurements
                take the last from multiple segments
                analyze the current and potential values
            """

            #            N2_act_BG_over2000 = Path(N2_dest_dir.parent).joinpath(N2_fn+'_test2000.xlsx')# test
            #            preN2_scan.to_excel(N2_act_BG_over2000)
            #            logger.warning('!! N2 scan more than 2000 data points.. file saved {0} !! len({1})'.format(N2_fn,lenpreN2))
            # preN2_scan = preN2_scan.loc[
            #     preN2_scan.PAR_file == preN2_scan["PAR_file"].unique()[-1], :
            # ]
            sr_grp_min_2000 = pd.concat(
                [gr for n, gr in sr_grp_min.groupby("Segment #") if len(gr) == 2000]
            )
            if sr_grp_min["Segment #"].nunique() > 1:

                sr_grp_min_2000 = pd.concat(
                    [gr for n, gr in sr_grp_min.groupby("Segment #") if len(gr) == 2000]
                )
                # for i in preN2_scan["Segment #"].unique():
                # if len(preN2_scan.loc[preN2_scan["Segment #"] == i]) == 2000:
                # N2_scan = preN2_scan.loc[preN2_scan["Segment #"] == i]
            # elif len(preN2_scan["Segment #"].unique()) == 1:
            # N2_scan = preN2_scan.drop_duplicates()
        elif len(N2_scan) != 2000:
            logger.warning(
                "!! N2 scan not 2000 data points.. {0} !! len({1})".format(
                    N2_fn, len(N2_scan)
                )
            )
            #            print('!! N2 scan less than 2000 data points.. !! %s' %lenpreN2)
            N2_scan = preN2_scan.loc[
                preN2_scan.PAR_file == preN2_scan["PAR_file"].unique()[0], :
            ]
            if len(preN2_scan["Segment #"].unique()) == 1:
                for i in preN2_scan["Segment #"].unique():
                    if len(preN2_scan.loc[preN2_scan["Segment #"] == i]) == 2000:
                        N2_scan = preN2_scan.loc[preN2_scan["Segment #"] == i]

        elif lenpreN2 < 2000:
            logger.warning(
                "!! N2 scan less than 2000 data points..  {0} !! len({1})".format(
                    N2_fn, lenpreN2
                )
            )
            N2_scan = preN2_scan.loc[
                preN2_scan.PAR_file == preN2_scan["PAR_file"].unique()[0], :
            ]
            if len(preN2_scan["Segment #"].unique()) == 1:
                for i in preN2_scan["Segment #"].unique():
                    if len(preN2_scan.loc[preN2_scan["Segment #"] == i]) == 2000:
                        N2_scan = preN2_scan.loc[preN2_scan["Segment #"] == i]
        #                            if len(preN2_scan.loc[preN2_scan['Segment #'] == i]) != 2000:
        #                            N2_scan = pd.DataFrame([])
        #                            print('!! Wrong size for N2 background!!')
        else:
            logger.info(
                "!! N2 scan has 2000 data points..success  {0} !! len({1})".format(
                    N2_fn, lenpreN2
                )
            )
            N2_scan = preN2_scan
    except Exception as e:
        logger.error("N2 scan length problems %s", e)
        N2_scan = preN2_scan
    if N2_scan.empty:
        logger.warning("!! N2 background is Empty!! {0}".format(N2_FileName))
