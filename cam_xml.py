#!/usr/bin/env python3
"""
Cam Profile XML generation for CamExtractor.

Builds XML cam profiles following CamProfile.xsd (the schema used by the PLC
project's XMLTest runtime loader). Ported from core_project/User/CAMS/csv_to_xml.py,
but adapted to take master/slave point arrays directly (sourced from the parsed
Excel) and an explicit reject_position (chosen interactively in the UI) instead of
the standalone script's hardcoded reject-position tables.
"""

import os
import re
from datetime import datetime
from typing import List, Optional


# Axis prefix to (AxisName, AxisNumber) mapping.
# Mirrors the hardcoded CASE in core_project Logical/Programs/Data/XMLTest/Main.st.
AXIS_MAPPING = {
    'vac_': ('AXVACUUM', 12),
    'vac1_': ('AXVACUUM', 12),
    'vac2_': ('AXVACUUM', 12),
    'vac3_': ('AXVACUUM', 12),
    'vac4_': ('AXVACUUM', 12),
    'vac5_': ('AXVACUUM', 12),
    'vac6_': ('AXVACUUM', 12),
    'gat3_': ('AXGATE3', 10),
    'horz_': ('AXHORIZ', 4),
    'late_': ('AXLATEGATE', 15),
    'pri_': ('AXPRISLIDE', 13),
    'rec_': ('AXRECIP', 14),
    'rot1_': ('AXROTODEX1', 8),
    'rot2_': ('AXROTODEX2', 7),
    'vert_': ('AXVERTICAL', 3),
}

# Axes that support the RejectPosition motion parameter.
REJECT_AXES = {'AXVACUUM', 'AXRECIP', 'AXGATE3'}

# Distinct axis names, for populating the UI dropdown (preserves mapping order).
AXIS_NAMES = list(dict.fromkeys(name for name, _ in AXIS_MAPPING.values()))


def get_axis_info(prefix: str):
    """Return (AxisName, AxisNumber) for a prefix, or None if unknown."""
    return AXIS_MAPPING.get(prefix)


def is_capping_axis(axis_name: Optional[str]) -> bool:
    """True if the axis carries a RejectPosition (Vac / Recip / Gate3)."""
    return axis_name in REJECT_AXES


def parse_filename(name: str) -> Optional[dict]:
    """
    Best-effort parse of the legacy filename convention into cam metadata.

    Pattern: <prefix>_<index>[-<HMIText>][.ext]
    e.g. "vac4_9-9) Vacuum 4.0mm.xlsx" -> prefix "vac4_", index "9", hmitext "9) Vacuum 4.0mm"

    Returns a dict {prefix, index, hmitext, axis_name, axis_number, is_capping} when the
    prefix_index portion matches, otherwise None (signals "use manual entry in the UI").
    """
    if not name:
        return None

    base = os.path.basename(name)
    # Strip a known cam extension if present.
    root, ext = os.path.splitext(base)
    if ext.lower() not in ('.xlsx', '.xls', '.csv', ''):
        # Unknown extension; treat the whole thing as the name body.
        root = base

    # Split on the first hyphen to separate prefix_index from the HMIText label.
    if '-' in root:
        prefix_index, hmitext = root.split('-', 1)
    else:
        prefix_index, hmitext = root, ''

    prefix_index = prefix_index.strip()
    hmitext = hmitext.strip()

    match = re.match(r'^([a-z]+\d*_)(\d+)$', prefix_index, re.IGNORECASE)
    if not match:
        return None

    prefix = match.group(1).lower()
    index = match.group(2)

    axis_info = get_axis_info(prefix)
    axis_name = axis_info[0] if axis_info else None
    axis_number = axis_info[1] if axis_info else None

    return {
        'prefix': prefix,
        'index': index,
        'hmitext': hmitext,
        'axis_name': axis_name,
        'axis_number': axis_number,
        'is_capping': is_capping_axis(axis_name),
    }


def _clean_text(text: str) -> str:
    """XML-safe, ASCII-clean text: replace ampersands and escape angle brackets."""
    if text is None:
        text = ''
    text = str(text).replace('&', 'AND')
    text = text.replace('<', '(').replace('>', ')')
    return text


def _fmt(value) -> str:
    """Format a numeric point coordinate without trailing noise."""
    f = float(value)
    if f == int(f):
        return str(int(f))
    return repr(f)


def generate_xml(prefix: str, index: str, hmitext: str,
                 axis_name: str, axis_number: int,
                 master: List[float], slave: List[float],
                 reject_position: Optional[float] = None,
                 source_filename: Optional[str] = None) -> str:
    """
    Generate CamProfile.xsd XML content from master/slave point arrays.

    master / slave are paired lists (master = POSITION column, slave = DEGREES column).
    reject_position, when provided, is a normalized master position (0-1) and is only
    emitted for capping axes (Vac / Recip / Gate3); callers should pass None otherwise.
    """
    if len(master) != len(slave):
        raise ValueError(f"master/slave length mismatch: {len(master)} vs {len(slave)}")
    if len(master) < 2:
        raise ValueError(f"Need at least 2 cam points, got {len(master)}")
    if len(master) > 100:
        raise ValueError(f"CamProfile.xsd allows at most 100 points, got {len(master)}")

    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    points_xml = '\n'.join(
        f'    <Point master="{_fmt(m)}" slave="{_fmt(s)}" />'
        for m, s in zip(master, slave)
    )

    motion_params = ''
    if reject_position is not None and is_capping_axis(axis_name):
        motion_params = (
            '  <MotionParams>\n'
            f'    <RejectPosition>{float(reject_position):.6f}</RejectPosition>\n'
            '  </MotionParams>\n'
        )

    notes = f'Converted from {_clean_text(source_filename)}' if source_filename else ''
    name = f'{prefix}{index}' if prefix and index else _clean_text(hmitext)

    axis_info_block = ''
    if axis_name:
        axis_info_block = (
            '  <AxisInfo>\n'
            f'    <AxisName>{_clean_text(axis_name)}</AxisName>\n'
            f'    <AxisNumber>{int(axis_number)}</AxisNumber>\n'
            '    <CamType>Position</CamType>\n'
            '  </AxisInfo>\n'
        )

    xml_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<CamData>\n'
        '  <Metadata>\n'
        f'    <HMIText>{_clean_text(hmitext)}</HMIText>\n'
        f'    <Name>{_clean_text(name)}</Name>\n'
        '    <Version>1.0</Version>\n'
        '    <Author>CamExtractor</Author>\n'
        f'    <Timestamp>{timestamp}</Timestamp>\n'
        f'    <Notes>{notes}</Notes>\n'
        '    <Units>degrees</Units>\n'
        '  </Metadata>\n'
        f'{axis_info_block}'
        f'{motion_params}'
        '  <CamPoints>\n'
        f'{points_xml}\n'
        '  </CamPoints>\n'
        '</CamData>\n'
    )

    return xml_content
