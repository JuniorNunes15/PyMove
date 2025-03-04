"""
Filtering operations.

get_bbox_by_radius,
by_bbox,
by_datetime,
by_label,
by_id,
by_tid,
clean_consecutive_duplicates,
clean_gps_jumps_by_distance,
clean_gps_nearby_points_by_distances,
clean_gps_nearby_points_by_speed,
clean_gps_speed_max_radius,
clean_trajectories_with_few_points,
clean_trajectories_short_and_few_points,
clean_id_by_time_max

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

import numpy as np
from pandas import DataFrame

from pymove.semantic.semantic import outliers
from pymove.utils.constants import (
    DATETIME,
    DIST_TO_PREV,
    LATITUDE,
    LONGITUDE,
    OUTLIER,
    SPEED_TO_PREV,
    TID,
    TIME_TO_PREV,
    TRAJ_ID,
)
from pymove.utils.log import logger

if TYPE_CHECKING:
    from pymove.core.dask import DaskMoveDataFrame
    from pymove.core.pandas import PandasMoveDataFrame


def get_bbox_by_radius(
    coordinates: tuple[float, float], radius: float = 1000
) -> tuple[float, float, float, float]:
    """
    Defines minimum and maximum coordinates, given a distance radius from a point.

    Parameters
    ----------
    coords : tuple (lat, lon)
        The coordinates of point

    radius: float, optional (1000 by default)

    Returns
    -------
    array
        coordinates min and max of the bbox

    References
    ----------
        https://mathmesquita.me/2017/01/16/filtrando-localizacao-em-um-raio.html
    """
    earth_radius = 6371000
    r = radius / earth_radius

    lat, lon = np.radians(coordinates)

    latmin = lat - r
    latmax = lat + r

    delta_lon = np.arcsin(np.sin(r) / np.cos(lat))

    lonmin = lon - delta_lon
    lonmax = lon + delta_lon

    return tuple(np.rad2deg([latmin, lonmin, latmax, lonmax]))  # type: ignore


def by_bbox(
    move_data: DataFrame,
    bbox: tuple[float, float, float, float],
    filter_out: bool = False,
    inplace: bool = False
) -> DataFrame | None:
    """
    Filters points of the trajectories according to specified bounding box.

    Parameters
    ----------
    move_data : dataframe
       The input trajectories data
    bbox : tuple
        Tuple of 4 elements, containing the minimum and maximum values
        of latitude and longitude of the bounding box.
    filter_out : boolean, optional
        If set to false the function will return the trajectories points
        within the bounding box, and the points outside otherwise, by default False
    inplace : boolean, optional
        if set to true the original dataframe will be altered to contain
        the result of the filtering, otherwise a copy will be returned, by default False

    Returns
    -------
    DataFrame
        Returns dataframe with trajectories points filtered by bounding box or None

    """
    filter_ = (
        (move_data[LATITUDE] >= bbox[0])
        & (move_data[LONGITUDE] >= bbox[1])
        & (move_data[LATITUDE] <= bbox[2])
        & (move_data[LONGITUDE] <= bbox[3])
    )
    if filter_out:
        filter_ = ~filter_

    return move_data.drop(index=move_data[~filter_].index, inplace=inplace)


def by_datetime(
    move_data: DataFrame,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
    filter_out: bool = False,
    inplace: bool = False,
) -> DataFrame | None:
    """
    Filters trajectories points according to specified time range.

    Parameters
    ----------
    move_data : dataframe
        The input trajectory data
    start_datetime : str
        The start date and time (Datetime format) of the time range, by default None
    end_datetime : str
        The end date and time (Datetime format) of the time range, by default None
    filter_out : bool, optional
        If set to true, the function will return the points of
        the trajectories with timestamp outside the time range.
        The points whithin the time range will be return if filter_out is False.
        by default False
    inplace : bool, optional
        if set to true the original dataframe will be altered to contain
        the result of the filtering, otherwise a copy will be returned, by default False

    Returns
    -------
    DataFrame
        Returns dataframe with trajectories points filtered by time range or None

    """
    if start_datetime is not None and end_datetime is not None:
        filter_ = (
            (move_data[DATETIME] >= start_datetime)
            & (move_data[DATETIME] <= end_datetime)
        )
    elif end_datetime is not None:
        filter_ = move_data[DATETIME] <= end_datetime
    else:
        filter_ = move_data[DATETIME] >= start_datetime

    if filter_out:
        filter_ = ~filter_

    return move_data.drop(index=move_data[~filter_].index, inplace=inplace)


def by_label(
    move_data: DataFrame,
    value: Any,
    label_name: str,
    filter_out: bool = False,
    inplace: bool = False
) -> DataFrame | None:
    """
    Filters trajectories points according to specified value and column label.

    Parameters
    ----------
    move_data : dataframe
        The input trajectory data
    value : The value to be use to filter the trajectories
        Specifies the value used to filter the trajectories points
    label_name : str
        Specifies the label of the column used in the filtering
    filter_out : bool, optional
        If set to true, the function will return the points of
        the trajectories with timestamp outside the time range.
        The points whithin the time range will be return if filter_out is False.
        by default False
    inplace : bool, optional
        if set to true the original dataframe will be altered to contain
        the result of the filtering, otherwise a copy will be returned, by default False

    Returns
    -------
    DataFrame
        Returns dataframe with trajectories points filtered by label or None

    """
    filter_ = move_data[label_name] == value
    if filter_out:
        filter_ = ~filter_

    return move_data.drop(index=move_data[~filter_].index, inplace=inplace)


def by_id(
    move_data: DataFrame,
    id_: int | None = None,
    label_id: str = TRAJ_ID,
    filter_out: bool = False,
    inplace: bool = False
) -> DataFrame | None:
    """
    Filters trajectories points according to specified trajectory id.

    Parameters
    ----------
    move_data : dataframe
        The input trajectory data
    id_ : int
        Specifies the number of the id used to filter the trajectories points
    label_id : str, optional
        The label of the column which contains the id of the trajectories,
        by default TRAJ_ID
    filter_out : bool, optional
        If set to true, the function will return the points of
        the trajectories with timestamp outside the time range.
        The points whithin the time range will be return if filter_out is False.
        by default False
    inplace : bool, optional
        if set to true the original dataframe will be altered to contain
        the result of the filtering, otherwise a copy will be returned, by default False


    Returns
    -------
    DataFrame
        Returns dataframe with trajectories points filtered by id or None

    """
    return by_label(move_data, id_, label_id, filter_out, inplace)


def by_tid(
    move_data: DataFrame,
    tid_: str | None = None,
    filter_out: bool = False,
    inplace: bool = False
) -> DataFrame | None:
    """
    Filters trajectories points according to a specified  trajectory tid.

    Parameters
    ----------
    move_data : dataframe
        The input trajectory data
    tid_ : str
        Specifies the number of the tid used to filter the trajectories points
    label_tid : str, optional
        The label of the column in the user dataframe which contains
        the tid of the trajectories, by default None
    filter_out : bool, optional
        If set to true, the function will return the points of
        the trajectories with timestamp outside the time range.
        The points whithin the time range will be return if filter_out is False.
        by default False
    inplace : bool, optional
        if set to true the original dataframe will be altered to contain
        the result of the filtering, otherwise a copy will be returned, by default False

    Returns
    -------
    DataFrame
        Returns a dataframe with trajectories points filtered or None

    """
    return by_label(move_data, tid_, TID, filter_out, inplace)


def clean_consecutive_duplicates(
    move_data: DataFrame,
    subset: int | str | None = None,
    keep: str | bool = 'first',
    inplace: bool = False
) -> DataFrame | None:
    """
    Removes consecutive duplicate rows of the Dataframe.

    Optionally only certain columns can be consider.

    Parameters
    ----------
    move_data : dataframe
        The input trajectory data
    subset : Array of str, optional
        Specifies  Column label or sequence of labels, considered for
        identifying duplicates, by default None
    keep : 'first', 'last', optional
        If keep is set as first, all the duplicates except for
        the first occurrence will be dropped.
        On the other hand if set to last, all duplicates except for
        the last occurrence will be dropped.
        If set to False, all duplicates are dropped.
        by default 'first'
    inplace : boolean, optional
        if set to true the original dataframe will be altered,
        the duplicates will be dropped in place,
        otherwise a copy will be returned, by default False

    Returns
    -------
    DataFrame
        The filtered trajectories points without consecutive duplicates or None

    """
    if keep == 'first':
        n = 1
    else:
        n = -1
    if subset is None:
        filter_ = (move_data.shift(n) != move_data).any(axis=1)
    else:
        filter_ = (move_data[subset].shift(n) != move_data[subset]).any(axis=1)

    return move_data.drop(index=move_data[~filter_].index, inplace=inplace)


def _filter_single_by_max(move_data: DataFrame, **kwargs):
    """
    Filters from a dataframe rows with features below value.

    Parameters
    ----------
    move_data : dataframe
        Dataframe to be filtered.
    **kwargs : arguments
        - arg1 : feature
        - arg2 : value

    Returns
    -------
    DataFrame
        Filtered dataframe.

    """
    return move_data[move_data[kwargs['arg1']] <= kwargs['arg2']]


def _filter_speed_max_radius(move_data: DataFrame, **kwargs):
    """
    Filters from a dataframe rows with current or previous row features exceeding value.

    Parameters
    ----------
    move_data : dataframe
        Dataframe to be filtered.
    **kwargs : arguments
        - arg1 : feature
        - arg2 : value

    Returns
    -------
    DataFrame
        Filtered dataframe.

    """
    filter_ = (
        (np.nan_to_num(move_data[kwargs['arg1']].shift(1)) > kwargs['arg2'])
        | (np.nan_to_num(move_data[kwargs['arg1']]) > kwargs['arg2'])
    )
    return move_data[filter_]


def _filter_data(move_data: DataFrame, f: Callable, kwargs: dict):
    """
    Filter the dataframe using condition from given function.

    Parameters
    ----------
    move_data : dataframe
        Dataframe to be filtered.
    f : function
        Filtering function
    **kwargs : arguments
        - arg1 : feature
        - arg2 : value
        - outliers : special behavior if cleaning by outliers

    Returns
    -------
    dataframe
        Filtered dataframe.
    int
        Number of rows to be dropped

    """
    if kwargs['outliers']:
        filter_data_points = f(
            move_data,
            jump_coefficient=kwargs['arg1'],
            threshold=kwargs['arg2'],
            inplace=False
        )
        filter_data_points = filter_data_points[filter_data_points[OUTLIER]]
    else:
        filter_data_points = f(
            move_data,
            arg1=kwargs['arg1'],
            arg2=kwargs['arg2'],
            inplace=False
        )
    rows_to_drop = filter_data_points.shape[0]
    return filter_data_points, rows_to_drop


def _clean_gps(move_data: DataFrame, f: Callable, **kwargs):
    """
    Cleans gps points from a dataframe using condition from given function.

    Parameters
    ----------
    move_data : dataframe
        Dataframe to be filtered.
    f : function
        Filtering function
    **kwargs : arguments
        - arg1 : feature
        - arg2 : value
        - outliers : special behavior if cleaning by outliers

    Returns
    -------
    dataframe
        Filtered dataframe.

    """
    if move_data.index.name is not None:
        logger.debug('...Reset index for filtering\n')
        move_data.reset_index(inplace=True)

    filter_data_points, rows_to_drop = _filter_data(move_data, f, kwargs)

    sum_drop = 0
    while rows_to_drop > 0:
        logger.debug('...Dropping %s rows of gps points\n' % rows_to_drop)
        shape_before = move_data.shape[0]
        move_data.drop(index=filter_data_points.index, inplace=True)
        sum_drop = sum_drop + rows_to_drop
        logger.debug(
            '...Rows before: %s, Rows after:%s, Sum drop:%s\n'
            % (shape_before, move_data.shape[0], sum_drop)
        )

        filter_data_points, rows_to_drop = _filter_data(move_data, f, kwargs)

    logger.debug('%s GPS points were dropped' % sum_drop)

    return move_data


def clean_gps_jumps_by_distance(
    move_data: 'PandasMoveDataFrame' | 'DaskMoveDataFrame',
    label_id: str = TRAJ_ID,
    jump_coefficient: float = 3.0,
    threshold: float = 1,
    label_dtype: Callable = np.float64,
    inplace: bool = False,
) -> 'PandasMoveDataFrame' | 'DaskMoveDataFrame' | None:
    """
    Removes the trajectories points that are outliers from the dataframe.

    Parameters
    ----------
    move_data : dataframe
        The input trajectory data
    label_id : str, optional
         Indicates the label of the id column in the user dataframe, by default TRAJ_ID
    jump_coefficient : float, optional
        by default 3
    threshold : float, optional
        Minimum value that the distance features must have
        in order to be considered outliers, by default 1
    label_dtype : type, optional
        Represents column id type, by default np.float64.
    inplace : boolean, optional
        if set to true the operation is done in place, the original
        dataframe will be altered and None is returned, by default False

    Returns
    -------
    DataFrame
        The filtered trajectories without the gps jumps or None

    """
    if not inplace:
        move_data = move_data.copy()

    if DIST_TO_PREV not in move_data:
        move_data.generate_dist_features(
            label_id=label_id, label_dtype=label_dtype
        )

    logger.debug(
        '\nCleaning gps jumps by distance to jump_coefficient %s...\n'
        % jump_coefficient
    )
    move_data = _clean_gps(
        move_data,
        outliers,
        arg1=jump_coefficient,
        arg2=threshold,
        outliers=True
    )

    if not inplace:
        return move_data


def clean_gps_nearby_points_by_distances(
    move_data: 'PandasMoveDataFrame' | 'DaskMoveDataFrame',
    label_id: str = TRAJ_ID,
    radius_area: float = 10.0,
    label_dtype: Callable = np.float64,
    inplace: bool = False,
) -> 'PandasMoveDataFrame' | 'DaskMoveDataFrame' | None:
    """
    Removes points from the trajectories with smaller distance from the point before.

    Parameters
    ----------
    move_data : dataframe
        The input trajectory data
    label_id : str, optional
         Indicates the label of the id column in the user dataframe, by default TRAJ_ID
    radius_area : float, optional
        Species the minimum distance a point must have to it"srs previous point
        in order not to be dropped, by default 10
    label_dtype : type, optional
        Represents column id type, ,y default np.float64.
    inplace : boolean, optional
        if set to true the operation is done in place, the original
        dataframe will be altered and None is returned, be default False

    Returns
    -------
    DataFrame
        The filtered trajectories without the gps nearby points by distance or None

    """
    if not inplace:
        move_data = move_data.copy()

    if DIST_TO_PREV not in move_data:
        move_data.generate_dist_features(
            label_id=label_id, label_dtype=label_dtype
        )

    logger.debug(
        '\nCleaning gps points from radius of %s meters\n'
        % radius_area
    )

    move_data = _clean_gps(
        move_data,
        _filter_single_by_max,
        arg1=DIST_TO_PREV,
        arg2=radius_area,
        outliers=False
    )
    if not inplace:
        return move_data


def clean_gps_nearby_points_by_speed(
    move_data: 'PandasMoveDataFrame' | 'DaskMoveDataFrame',
    label_id: str = TRAJ_ID,
    speed_radius: float = 0.0,
    label_dtype: Callable = np.float64,
    inplace: bool = False,
) -> 'PandasMoveDataFrame' | 'DaskMoveDataFrame' | None:
    """
    Removes points from the trajectories with smaller speed of travel.

    Parameters
    ----------
    move_data : dataframe
        The input trajectory data
    label_id : str, optional
         Indicates the label of the id column in the user dataframe, be defalt TRAJ_ID
    speed_radius : float, optional
        Species the minimum speed a point must have from it"srs previous point,
        in order not to be dropped, by default 0
    label_dtype : type, optional
        Represents column id type, by default np.float64.
    inplace : boolean, optional
        if set to true the operation is done in place, the original
        dataframe will be altered and None is returned, by default False

    Returns
    -------
    DataFrame
        The filtered trajectories without the gps nearby points by speed or None

    """
    if not inplace:
        move_data = move_data.copy()

    if SPEED_TO_PREV not in move_data:
        move_data.generate_dist_time_speed_features(
            label_id=label_id, label_dtype=label_dtype
        )

    logger.debug(
        '\nCleaning gps points using %s speed radius\n'
        % speed_radius
    )

    move_data = _clean_gps(
        move_data,
        _filter_single_by_max,
        arg1=SPEED_TO_PREV,
        arg2=speed_radius,
        outliers=False
    )
    if not inplace:
        return move_data


def clean_gps_speed_max_radius(
    move_data: 'PandasMoveDataFrame' | 'DaskMoveDataFrame',
    label_id: str = TRAJ_ID,
    speed_max: float = 50.0,
    label_dtype: Callable = np.float64,
    inplace: bool = False,
) -> 'PandasMoveDataFrame' | 'DaskMoveDataFrame' | None:
    """
    Removes trajectories points with higher speed.

    Given any point p of the trajectory, the point will
    be removed if one of the following happens: if the travel speed from the
    point before p to p is greater than the  max value of speed between adjacent
    points set by the user. Or the travel speed between point p and the next
    point is greater than the value set by the user. When the cleaning is done,
    the function will update the time and distance features in the dataframe and
    will call itself again. The function will finish processing when it can no
    longer find points disrespecting the limit of speed.

    Parameters
    ----------
    move_data : dataframe
        The input trajectory data
    label_id : str, optional
        Indicates the label of the id column in the user dataframe, by default TRAJ_ID
    speed_max : float, optional
        Indicates the maximum value a point speed_to_prev and speed_to_next
        should have, in order not to be dropped, by default 50
    label_dtype : type, optional
        Represents column id type, by default np.float64.
    inplace : boolean, optional
        if set to true the operation is done in place, the original
        dataframe will be altered and None is returned, by default False

    Returns
    -------
    DataFrame
        The filtered trajectories without the gps nearby points or None

    """
    if not inplace:
        move_data = move_data.copy()

    if SPEED_TO_PREV not in move_data:
        move_data.generate_dist_time_speed_features(
            label_id=label_id, label_dtype=label_dtype
        )

    logger.debug(
        '\nClean gps points with speed max > %s meters by seconds'
        % speed_max
    )

    move_data = _clean_gps(
        move_data,
        _filter_speed_max_radius,
        arg1=SPEED_TO_PREV,
        arg2=speed_max,
        outliers=False
    )
    if not inplace:
        return move_data


def clean_trajectories_with_few_points(
    move_data: 'PandasMoveDataFrame' | 'DaskMoveDataFrame',
    label_tid: str = TID,
    min_points_per_trajectory: int = 2,
    inplace: bool = False
) -> 'PandasMoveDataFrame' | 'DaskMoveDataFrame' | None:
    """
    Removes from the given dataframe, trajectories with fewer points.

    Parameters
    ----------
    move_data : dataframe
        The input trajectory data
    label_tid : str, optional
        The label of the column which contains the tid of the trajectories, by default TID
    min_points_per_trajectory: int, optional
        Specifies the minimum number of points a trajectory must have
        in order not to be dropped, by default 2
    inplace : boolean, optional
        if set to true the operation is done in place, the original
        dataframe will be altered and None is returned, by default False

    Returns
    -------
    DataFrame
        The filtered trajectories without the minimum number of gps points or None

    Raises
    ------
    KeyError
        If the label feature is not in the dataframe

    """
    if not inplace:
        move_data = move_data.copy()

    if label_tid not in move_data:
        raise KeyError('%s not in dataframe' % label_tid)

    logger.debug(
        '\nCleaning gps points from trajectories of fewer than %s points\n'
        % min_points_per_trajectory
    )

    if move_data.index.name is not None:
        logger.debug('\n...Reset index for filtering\n')
        move_data.reset_index(inplace=True)

    move_datacount_tid = move_data.groupby(by=label_tid).size()
    filter_ = move_datacount_tid < min_points_per_trajectory
    tids_with_few_points = move_datacount_tid[filter_].index
    shape_before_drop = move_data.shape
    idx = move_data[move_data[label_tid].isin(tids_with_few_points)].index

    if idx.shape[0] > 0:
        logger.debug(
            '\n...There are %s ids with few points'
            % tids_with_few_points.shape[0]
        )
        logger.debug(
            '\n...Tids before drop: %s'
            % move_data[label_tid].unique().shape[0]
        )
        move_data.drop(index=idx, inplace=True)
        logger.debug(
            '\n...Tids after drop: %s'
            % move_data[label_tid].unique().shape[0]
        )
        logger.debug(
            '\n...Shape - before drop: %s - after drop: %s'
            % (shape_before_drop, move_data.shape)
        )

    if not inplace:
        return move_data


def clean_trajectories_short_and_few_points(
    move_data: 'PandasMoveDataFrame' | 'DaskMoveDataFrame',
    label_id: str = TID,
    min_trajectory_distance: float = 100,
    min_points_per_trajectory: int = 2,
    label_dtype: Callable = np.float64,
    inplace: bool = False,
) -> 'PandasMoveDataFrame' | 'DaskMoveDataFrame' | None:
    """
    Eliminates from the given dataframe trajectories with fewer points and shorter length.

    Parameters
    ----------
    move_data : dataframe
        The input trajectory data
    label_id : str, optional
        The label of the column which contains the tid of the trajectories, by default TID
    min_trajectory_distance: float, optional
        Specifies the minimun length a trajectory must have
        in order not to be dropped, by default 100
    min_points_per_trajectory: int, optional
        Specifies the minimun number of points a trajectory must have
        in order not to be dropped, by default 2
    label_dtype : type, optional
        Represents column id type, by default np.float64.
    inplace: boolean, optional
        if set to true the operation is done in place, the original
        dataframe will be altered and None is returned, by default False

    Returns
    -------
    DataFrame
        The filtered trajectories with the minimum gps points and distance or None

    Notes
    -----
        remove_tids_with_few_points must be performed before updating features.

    """
    if not inplace:
        move_data = move_data.copy()

    logger.debug('\nRemove short trajectories...')
    clean_trajectories_with_few_points(
        move_data, label_id, min_points_per_trajectory, inplace=True
    )

    if DIST_TO_PREV not in move_data:
        move_data.generate_dist_features(
            label_id=label_id, label_dtype=label_dtype
        )

    logger.debug('\n...Dropping unnecessary trajectories...')

    if move_data.index.name is not None:
        logger.debug('reseting index')
        move_data.reset_index(inplace=True)

    move_dataagg_tid = move_data.groupby(by=label_id).agg(
        {DIST_TO_PREV: 'sum'}
    )
    filter_ = move_dataagg_tid[DIST_TO_PREV] < min_trajectory_distance
    tid_selection = move_dataagg_tid[filter_].index

    logger.debug(
        '\n...short trajectories and trajectories with a minimum distance (%s): %s'
        % (move_dataagg_tid.shape[0], min_trajectory_distance)
    )
    logger.debug('\n...There are %s tid do drop' % tid_selection.shape[0])
    shape_before_drop = move_data.shape

    idx = move_data[move_data[label_id].isin(tid_selection)].index
    if idx.shape[0] > 0:
        tids_before_drop = move_data[label_id].unique().shape[0]
        logger.debug(
            '\n...Tids - before drop: %s - after drop: %s'
            % (tids_before_drop, move_data[label_id].unique().shape[0])
        )
        move_data.drop(index=idx, inplace=True)
        logger.debug(
            '\n...Shape - before drop: %s - after drop: %s'
            % (shape_before_drop, move_data.shape)
        )

    if not inplace:
        return move_data


def clean_id_by_time_max(
    move_data: 'PandasMoveDataFrame' | 'DaskMoveDataFrame',
    label_id: str = TRAJ_ID,
    time_max: float = 3600,
    label_dtype: Callable = np.float64,
    inplace: bool = False,
) -> 'PandasMoveDataFrame' | 'DaskMoveDataFrame' | None:
    """
    Clears GPS points with time by ID greater than a user-defined limit.

    Parameters
    ----------
    move_data: dataframe.
        The input data.
    label_id: str, optional
        The label of the column which contains the id of the trajectories,
        by default TRAJ_ID
    time_max: float, optional
        Indicates the maximum value time a set of points with the
        same id should have in order not to be dropped, by default 3600
    label_dtype : type, optional
        Represents column id type, by default np.float64.
    inplace : boolean, optional
        if set to true the operation is done in place, the original
        dataframe will be altered and None is returned, by default False

    Returns
    -------
    dataframe or None
        The filtered trajectories with the maximum time.

    """
    if not inplace:
        move_data = move_data.copy()

    if TIME_TO_PREV not in move_data:
        move_data.generate_dist_time_speed_features(
            label_id=label_id, label_dtype=label_dtype
        )

    logger.debug(
        '\nClean gps points with time max by id < %s seconds'
        % time_max
    )
    move_dataid_drop = (
        move_data.groupby([label_id], as_index=False)
        .agg({TIME_TO_PREV: 'sum'})
        .query(f'{TIME_TO_PREV} < {time_max}')
    )
    logger.debug(
        '...Ids total: %s\nIds to drop:%s'
        % (
            move_data[label_id].nunique(),
            move_dataid_drop[label_id].nunique()
        )
    )
    if move_dataid_drop.shape[0] > 0:
        before_drop = move_data.shape[0]
        filter_ = move_data[label_id].isin(move_dataid_drop[label_id])
        idx = move_data[filter_].index
        move_data.drop(idx, inplace=True)
        logger.debug(
            '...Rows before drop: %s\n Rows after drop: %s'
            % (before_drop, move_data.shape[0])
        )

    if not inplace:
        return move_data
