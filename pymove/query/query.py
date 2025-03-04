"""
Query operations.

range_query,
knn_query

"""
from __future__ import annotations

import numpy as np
import pandas as pd
from pandas import DataFrame

from pymove.utils import distances
from pymove.utils.constants import DATETIME, LATITUDE, LONGITUDE, MEDP, MEDT, TRAJ_ID
from pymove.utils.log import logger, progress_bar


def range_query(
    traj: DataFrame,
    move_df: DataFrame,
    _id: str = TRAJ_ID,
    min_dist: float = 1000,
    distance: str = MEDP,
    latitude: str = LATITUDE,
    longitude: str = LONGITUDE,
    datetime: str = DATETIME
) -> DataFrame:
    """
    Returns all trajectories that have a distance equal to or less than the trajectory.

    Given a distance, a trajectory, and a DataFrame with several trajectories.

    Parameters
    ----------
    traj: dataframe
        The input of one trajectory.
    move_df: dataframe
        The input trajectory data.
    _id: str, optional
        Label of the trajectories dataframe user id, by default TRAJ_ID
    min_dist: float, optional
        Minimum distance measure, by default 1000
    distance: string, optional
        Distance measure type, by default MEDP
    latitude: string, optional
        Label of the trajectories dataframe referring to the latitude,
        by default LATITUDE
    longitude: string, optional
        Label of the trajectories dataframe referring to the longitude,
        by default LONGITUDE
    datetime: string, optional
        Label of the trajectories dataframe referring to the timestamp,
        by default DATETIME

    Returns
    -------
    DataFrame
        dataframe with near trajectories

    Raises
    ------
        ValueError: if distance measure is invalid

    """
    result = traj.copy()
    result.drop(result.index, inplace=True)

    if (distance == MEDP):
        def dist_measure(traj, this, latitude, longitude, datetime):
            return distances.medp(
                traj, this, latitude, longitude
            )
    elif (distance == MEDT):
        def dist_measure(traj, this, latitude, longitude, datetime):
            return distances.medt(
                traj, this, latitude, longitude, datetime
            )
    else:
        raise ValueError('Unknown distance measure. Use MEDP or MEDT')

    for traj_id in progress_bar(
        move_df[_id].unique(), desc=f'Querying range by {distance}'
    ):
        this = move_df.loc[move_df[_id] == traj_id]
        if dist_measure(traj, this, latitude, longitude, datetime) < min_dist:
            result = result.append(this)

    return result


def knn_query(
    traj: DataFrame,
    move_df: DataFrame,
    k: int = 5,
    id_: str = TRAJ_ID,
    distance: str = MEDP,
    latitude: str = LATITUDE,
    longitude: str = LONGITUDE,
    datetime: str = DATETIME
) -> DataFrame:
    """
    Returns the k neighboring trajectories closest to the trajectory.

    Given a k, a trajectory and a DataFrame with multiple paths.

    Parameters
    ----------
    traj: dataframe
        The input of one trajectory.
    move_df: dataframe
        The input trajectory data.
    k: int, optional
        neighboring trajectories, by default 5
    id_: str, optional
        Label of the trajectories dataframe user id, by default TRAJ_ID
    distance: string, optional
        Distance measure type, by default MEDP
    latitude: string, optional
        Label of the trajectories dataframe referring to the latitude,
        by default LATITUDE
    longitude: string, optional
        Label of the trajectories dataframe referring to the longitude,
        by default LONGITUDE
    datetime: string, optional
        Label of the trajectories dataframe referring to the timestamp,
        by default DATETIME

    Returns
    -------
    DataFrame
        dataframe with near trajectories


    Raises
    ------
        ValueError: if distance measure is invalid

    """
    k_list = pd.DataFrame([[np.Inf, 'empty']] * k, columns=['distance', TRAJ_ID])

    if (distance == MEDP):
        def dist_measure(traj, this, latitude, longitude, datetime):
            return distances.medp(
                traj, this, latitude, longitude
            )
    elif (distance == MEDT):
        def dist_measure(traj, this, latitude, longitude, datetime):
            return distances.medt(
                traj, this, latitude, longitude, datetime
            )
    else:
        raise ValueError('Unknown distance measure. Use MEDP or MEDT')

    for traj_id in progress_bar(
        move_df[id_].unique(), desc=f'Querying knn by {distance}'
    ):
        if (traj_id != traj[id_].values[0]):
            this = move_df.loc[move_df[id_] == traj_id]
            this_distance = dist_measure(
                traj, this, latitude, longitude, datetime
            )
            n = 0
            for n in range(k):
                if (this_distance < k_list.loc[n, 'distance']):
                    k_list.loc[n, 'distance'] = this_distance
                    k_list.loc[n, 'traj_id'] = traj_id
                    break
                n = n + 1

    result = traj.copy()
    logger.debug('Generating DataFrame with k nearest trajectories.')
    for n in range(k):
        result = result.append(
            move_df.loc[move_df[id_] == k_list.loc[n, 'traj_id']]
        )

    return result
