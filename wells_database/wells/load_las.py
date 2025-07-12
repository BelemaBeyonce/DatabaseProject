import lasio
from wells.models import Area, Wells, Curve, CurveValue

def parse_las_file(file_path, area_name):
    las = lasio.read(file_path)

    def get_value(section, key, default):
        try:
            item = section[key]
            return item.value if hasattr(item, 'value') else item
        except KeyError:
            return default

    well_name = get_value(las.well, 'WELL', 'UnknownWell')
    uwi = get_value(las.well, 'UWI', None)
    if Wells.objects.filter(uwi=uwi).exists():
        print(f"Well with UWI {uwi} already exists. Skipping.")
        return 
    latitude = get_value(las.well, 'LAT', None)
    longitude = get_value(las.well, 'LON', None)
    start = float(get_value(las.well, 'STRT', 0))
    stop = float(get_value(las.well, 'STOP', 0))
    unit_obj = las.well.get('STRT')
    unit = unit_obj.unit if unit_obj and hasattr(unit_obj, 'unit') else 'M'

    area, _ = Area.objects.get_or_create(area_name=area_name)
    well = Wells.objects.create(
        area=area,
        well_name=well_name,
        uwi=uwi,
        latitude=float(latitude) if latitude else None,
        longitude=float(longitude) if longitude else None,
        depth_start=start,
        depth_stop=stop,
        unit=unit
    )

    for curve in las.curves:
        c = Curve.objects.create(
            well=well,
            mnemonic=curve.mnemonic,
            unit=curve.unit,
            description=curve.descr
        )

        depths = las.index
        values = las[curve.mnemonic]

        for i in range(len(depths)):
            try:
                depth = float(depths[i])
                value = float(values[i])
                CurveValue.objects.create(curve=c, depth=depth, value=value)
            except (ValueError, TypeError):
                continue

    return well
