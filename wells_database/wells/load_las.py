import lasio
from wells.models import Area, Wells, Curve, CurveValue


def parse_las_file(file_path, area_name='User Upload'):
    try:
        las = lasio.read(file_path)
    except Exception as e:
        print(f"Failed to parse {file_path}: {e}")
        return None  # So the view can skip it safely

    def get_value(section, key, default=None):
        try:
            item = section[key]
            return item.value if hasattr(item, 'value') else item
        except KeyError:
            return default

    well_name = get_value(las.well, 'WELL', 'UnknownWell')
    uwi = get_value(las.well, 'UWI', None)
    latitude = get_value(las.well, 'LAT')
    longitude = get_value(las.well, 'LON')
    start = float(get_value(las.well, 'STRT', 0))
    stop = float(get_value(las.well, 'STOP', 0))
    unit_obj = las.well.get('STRT')
    unit = unit_obj.unit if unit_obj and hasattr(unit_obj, 'unit') else 'M'

    curves = []
    try:
        for curve in las.curves:
            depths = las.index
            values = las[curve.mnemonic]

            curve_data = []
            for i in range(len(depths)):
                try:
                    curve_data.append((float(depths[i]), float(values[i])))
                except (ValueError, TypeError):
                    continue

            curves.append({
                'mnemonic': curve.mnemonic,
                'unit': curve.unit,
                'description': curve.descr,
                'values': curve_data
            })
    except Exception as e:
        print(f"Error reading curves from {file_path}: {e}")
        return None

    return {
        'well_name': well_name,
        'uwi': uwi,
        'latitude': float(latitude) if latitude else None,
        'longitude': float(longitude) if longitude else None,
        'depth_start': start,
        'depth_stop': stop,
        'unit': unit,
        'area_name': area_name,
        'curves': curves
    }


