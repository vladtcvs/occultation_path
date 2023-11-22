"""Parse occultation descriptions from www.asteroidoccultation.com"""
import sys
import csv
import datetime
import geojson

class PathParser:
    """Parse occultation descriptions from www.asteroidoccultation.com"""
    @staticmethod
    def _select_path_area(lines):
        data_area = False
        data_lines = []
        for line in lines:
            if line.startswith("Path Coordinates"):
                data_area = True
            if data_area and line.startswith("Uncertainty in time"):
                data_area = False
                break
            if data_area:
                line = line.strip()
                if line != "":
                    data_lines.append(line)
        data_lines = data_lines[6:]
        return data_lines

    @staticmethod
    def _parse_line(line):
        line = line.replace("-  ", "-00")
        line = line.replace("- ", "-0")
        items = line.split(" ")
        items = [item for item in items if item != '']

        plus_day = False
        if items[9] == "+":
            plus_day = True
            del items[9]
        fields = {
            "lon_D" : items[0],
            "lon_M" : items[1],
            "lon_S" : items[2],

            "center_lat_D" : items[3],
            "center_lat_M" : items[4],
            "center_lat_S" : items[5],

            "plus_day" : plus_day,
            "ut_H" : items[6],
            "ut_M" : items[7],
            "ut_S" : items[8],

            "star_ALT" : items[9],
            "star_AZ"  : items[10],

            "sun_ALT"  : items[11],

            "path_limit_1_lat_D" : items[12],
            "path_limit_1_lat_M" : items[13],
            "path_limit_1_lat_S" : items[14],

            "path_limit_2_lat_D" : items[15],
            "path_limit_2_lat_M" : items[16],
            "path_limit_2_lat_S" : items[17],

            "err_limit_3_lat_D" : items[18],
            "err_limit_3_lat_M" : items[19],
            "err_limit_3_lat_S" : items[20],

            "err_limit_4_lat_D" : items[21],
            "err_limit_4_lat_M" : items[22],
            "err_limit_4_lat_S" : items[23],
        }
        return fields

    @staticmethod
    def _transform_DMS(D, M, S):
        if "-" in D:
            sign = -1
        else:
            sign = 1

        D = abs(int(D))
        M = int(M)
        S = float(S)
        return sign * (D + M/60 + S/3600)

    @staticmethod
    def _transform_timestamp(date : str, H : str, M : str, S : str, plus_day : bool):
        ts = datetime.datetime.strptime(date, "%Y %b %d")
        if plus_day:
            ts += datetime.timedelta(days=1)
        h = int(H)
        m = int(M)
        s = float(S)
        us = int((s - int(s))*1000000)
        s = int(s)
        ts = datetime.datetime(ts.year, ts.month, ts.day, h, m, s, us)
        ts = ts.isoformat("T")
        return ts

    @staticmethod
    def _transform_fields(fields : dict, date : str):
        try:
            transform_DMS = PathParser._transform_DMS
            transformed = {
                "lon" : transform_DMS(fields["lon_D"],
                                      fields["lon_M"],
                                      fields["lon_S"]),

                "center_lat" : transform_DMS(fields["center_lat_D"],
                                             fields["center_lat_M"],
                                             fields["center_lat_S"]),

                "limit1_lat" : transform_DMS(fields["path_limit_1_lat_D"],
                                             fields["path_limit_1_lat_M"],
                                             fields["path_limit_1_lat_S"]),

                "limit2_lat" : transform_DMS(fields["path_limit_2_lat_D"],
                                             fields["path_limit_2_lat_M"],
                                             fields["path_limit_2_lat_S"]),

                "limit3_lat" : transform_DMS(fields["err_limit_3_lat_D"],
                                             fields["err_limit_3_lat_M"],
                                             fields["err_limit_3_lat_S"]),

                "limit4_lat" : transform_DMS(fields["err_limit_4_lat_D"],
                                             fields["err_limit_4_lat_M"],
                                             fields["err_limit_4_lat_S"]),

                "UT" : PathParser._transform_timestamp(date,
                                                       fields["ut_H"],
                                                       fields["ut_M"],
                                                       fields["ut_S"],
                                                       fields["plus_day"]),

                "sun_alt" : int(fields["sun_ALT"]),
                "star_alt" : int(fields["star_ALT"]),
                "star_az" : int(fields["star_AZ"]),
            }
            return transformed, ""
        except ValueError as e:
            return None, str(e)

    @staticmethod
    def _parse_event(line : str):
        event = {}
        line = line.strip()
        items = line.split("/")
        event["planet"] = items[0].strip()
        line = items[1]
        items = line.split("event on")
        event["star"] = items[0].strip()
        line = items[1]
        items = line.split(",")
        event["date"] = items[0].strip()
        return event

    @staticmethod
    def parse_data(text : str):
        """Parse occultation prediction"""
        lines = text.splitlines()
        event = PathParser._parse_event(lines[1])
        data_lines = PathParser._select_path_area(lines)
        timings = []
        for index, line in enumerate(data_lines):
            line_items = PathParser._parse_line(line)
            fields, err = PathParser._transform_fields(line_items, event["date"])
            if fields is not None:
                timings.append(fields)
            else:
                print(f"Point #{index} : {err}")
        result = {
            "event" : event,
            "timings" : timings,
        }
        return result

def process_file_csv(input_fname, output_fname):
    """Convert to csv"""
    with open(input_fname, encoding='utf8') as f:
        text = f.read()

    psr = PathParser()
    points = psr.parse_data(text)["timings"]
    with open(output_fname, "w", encoding='utf8') as f:
        writer = csv.writer(f)
        writer.writerow(["lon",
                         "center_lat",
                         "limit1_lat",
                         "limit2_lat",
                         "limit3_lat",
                         "limit4_lat",
                         "sun_alt",
                         "star_alt",
                         "star_az",
                         "UT"])
        for fields in points:
            writer.writerow([fields["lon"],
                             fields["center_lat"],
                             fields["limit1_lat"],
                             fields["limit2_lat"],
                             fields["limit3_lat"],
                             fields["limit4_lat"],
                             fields["sun_alt"],
                             fields["star_alt"],
                             fields["star_az"],
                             fields["UT"]])

def process_file_geojson(input_fname, output_fname):
    """Convert to geojson"""
    with open(input_fname, encoding="utf8") as f:
        text = f.read()

    psr = PathParser()
    data = psr.parse_data(text)
    event = data["event"]
    points = data["timings"]
    with open(output_fname, "w", encoding="utf8") as f:
        features = []

        for fields in points:
            props = {
                "UT": fields["UT"],
                "sun_alt" : fields["sun_alt"],
                "star_az" : fields["star_az"],
                "star_alt" : fields["star_alt"],
                "star" : event["star"],
                "planet" : event["planet"],
            }
            lon = fields["lon"]
            lat = fields["center_lat"]
            features.append(geojson.Feature(geometry=geojson.Point((lon, lat)),
                                            properties=props))
            lat = fields["limit1_lat"]
            features.append(geojson.Feature(geometry=geojson.Point((lon, lat)),
                                            properties=props))
            lat = fields["limit2_lat"]
            features.append(geojson.Feature(geometry=geojson.Point((lon, lat)),
                                            properties=props))

        collection = geojson.FeatureCollection(features=features)
        geojson.dump(collection, f, indent=4)

if __name__ == "__main__":
    process_file_geojson(sys.argv[1], sys.argv[2])
