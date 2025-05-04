#!/usr/bin/env python3
# Author: Jonathan Külz
import gzip
from pathlib import Path
import shutil
import tempfile
from typing import Union

import matplotlib.pyplot as plt
from garmin_fit_sdk import Decoder, Stream
import gpxpy
import pandas as pd

MAXROWS = None


def load_fit(dir_activities: Path):
    """
    Loads all data that is stored as fit file

    :param dir_activities: Directory where the activities are stored.
    """
    points = []
    cnt = 0
    for raw_fl in dir_activities.glob('*.fit.gz'):
        cnt += 1
        if MAXROWS is not None and cnt > MAXROWS:
            break
        with gzip.open(raw_fl, 'rb') as fz:
            with tempfile.NamedTemporaryFile(delete=True) as tmp:
                shutil.copyfileobj(fz, tmp)

                stream = Stream.from_file(tmp.name)
                decoder = Decoder(stream)
                messages, errors = decoder.read()

        record = messages.get('record_mesgs')
        for r in record:
            points.append({
                'time': r.get('timestamp'),
                'lat': r.get('position_lat'),
                'lon': r.get('position_long'),
                'elevation': r.get('enhanced_altitude'),
                'filename': raw_fl.name
            })
    df = pd.DataFrame.from_records(points)
    return df

def load_gpx(dir_activities: Path):
    """
    Loads all data that is stored as gpx file

    :param dir_activities: Directory where the activities are stored.
    """
    points = []
    cnt = 0
    for gpx_fl in dir_activities.glob('*.gpx'):
        cnt += 1
        if MAXROWS is not None and cnt > MAXROWS:
            break
        with gpx_fl.open('r') as f:
            try:
                content = gpxpy.parse(f)
            except gpxpy.gpx.GPXXMLSyntaxException:
                cnt -= 1
                continue

        for track in content.tracks:
            for segment in track.segments:
                for p in segment.points:
                    points.append({
                        'time': p.time,
                        'lat': p.latitude,
                        'lon': p.longitude,
                        'elevation': p.elevation,
                        'uid': gpx_fl.stem
                    })
    df = pd.DataFrame.from_records(points)
    return df

def load_data(loc: Union[str, Path]) -> pd.DataFrame:
    """
    Loads all strava history data into a pandas DataFrame.

    :param loc: Directory where the activities are stored.
    """
    loc = Path(loc)
    dir_activities = loc / 'activities'

    metadata = pd.read_csv(loc / 'activities.csv').rename(columns={'Aktivitäts-ID': 'uid'})
    gpx_data = load_gpx(dir_activities)
    fit_data = load_fit(dir_activities)

    filename_lookup = {str(row['Dateiname']).split('/')[-1]: row['uid'] for _, row in metadata.iterrows()}
    fit_data['uid'] = fit_data.filename.map(filename_lookup)

    df = pd.concat([fit_data, gpx_data], axis=0)

    df = df.sort_values('time')[::4]  # Quarter resolution is usually sufficient
    df = df.dropna(subset=['lat', 'lon'], axis=0)

    min_t, max_t = df['time'].min(), df['time'].max()
    df['color'] = df.time.map(lambda x: [val * 255 for val in plt.cm.plasma((x - min_t) / (max_t - min_t))])

    data = df.groupby('uid').apply(
        lambda group: pd.Series({
            'path': list(zip(group.lon, group.lat)),
            'color': group.color.iloc[0]
        })
    ).reset_index()
    data.uid = data.uid.astype(int)

    data = data \
        .join(metadata.set_index('uid')[['Name der Aktivität', 'Aktivitätsart', 'Aktivitätsdatum']], on='uid') \
        .rename(
            columns={
            'Name der Aktivität': 'name',
            'Aktivitätsart': 'sport',
            'Aktivitätsdatum': 'date'
        }) \
        .fillna('Unknown')

    data.color = data.sport.map({
        'Lauf': [205, 108, 58, 255],
        'Radfahrt': [130, 30, 80, 255],
        'Schwimmen': [13, 8, 135, 255],
        'Wandern': [64, 3, 156, 255],
        'Training': [255, 255, 255, 255],
        'Ski Alpin': [255, 255, 255, 255],
        'Kajak fahren': [255, 255, 255, 255],
        'Gewichtstraining': [255, 255, 255, 255],
        'Inlineskaten': [255, 255, 255, 255],
        'Skilanglaufen': [255, 255, 255, 255],
    })

    return data
