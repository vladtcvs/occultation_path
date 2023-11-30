"""Parse occultation descriptions from www.asteroidoccultation.com"""
import sys
import datetime
import geojson

class PathParser:
    """Parse occultation descriptions from www.asteroidoccultation.com"""
    @staticmethod
    def _select_path_area(lines):
        data_area = False
        data_lines = []
        options = {}
        for line in lines:
            if line.startswith("Path Coordinates"):
                data_area = True
            if data_area and line.startswith("Uncertainty in time"):
                data_area = False
                break
            if data_area:
                if line.strip() != "":
                    data_lines.append(line)
        if "Longitude" in data_lines[5]:
            options["format_lon"] = True
        else:
            options["format_lon"] = False
        data_lines = data_lines[6:]
        return data_lines, options

    @staticmethod
    def parse_lon(line : str):
        sign = 1
        if line[0] == '-':
            sign = -1
        d = int(line[1:4])
        m = int(line[5:7])
        s = int(line[8:10])
        lon = sign * (d + m / 60 + s / 3600)
        return lon, line[10:]

    @staticmethod
    def parse_lat(line : str):
        sign = 1
        if line[0] == '-':
            sign = -1
        d = int(line[1:3])
        m = int(line[4:6])
        s = int(line[7:9])
        lat = sign * (d + m / 60 + s / 3600)
        return lat, line[9:]

    @staticmethod
    def parse_hms(line : str, date : datetime.datetime):
        h = int(line[0:2])
        m = int(line[3:5])
        s = float(line[6:10])
        pd = (line[11] == '+')
        if pd:
            date = date + datetime.timedelta(days=1)
        us = int((s - int(s))*1000000)
        s = int(s)
        ts = datetime.datetime(date.year, date.month, date.day, h, m, s, us)
        ts = ts.isoformat("T")
        return ts, line[12:]

    @staticmethod
    def parse_int(line : str, digits : int):
        return int(line[:digits]), line[digits:]

    @staticmethod
    def parse_float(line : str, digits : int):
        return float(line[:digits]), line[digits:]

    @staticmethod
    def _parse_line(line : str, date : datetime.datetime, format_lon : bool):
        line = line[3:]
        fields = {}
        fields["center_lon"], line = PathParser.parse_lon(line)
        line = line[3:]
        fields["center_lat"], line = PathParser.parse_lat(line)
        line = line[3:]
        fields["UT"], line = PathParser.parse_hms(line, date)
        line = line[2:]
        fields["star_alt"], line = PathParser.parse_int(line, 2)
        line = line[3:]
        fields["star_az"], line = PathParser.parse_int(line, 3)
        line = line[3:]
        fields["sun_alt"], line = PathParser.parse_int(line, 3)

        if format_lon:
            line = line[1:]
            fields["path_limit1_lon"], line = PathParser.parse_lon(line)
            line = line[2:]
            fields["path_limit1_lat"], line = PathParser.parse_lat(line)
            line = line[1:]
            fields["path_limit2_lon"], line = PathParser.parse_lon(line)
            line = line[2:]
            fields["path_limit2_lat"], line = PathParser.parse_lat(line)
            line = line[1:]
            fields["err_limit1_lon"], line = PathParser.parse_lon(line)
            line = line[2:]
            fields["err_limit1_lat"], line = PathParser.parse_lat(line)
            line = line[1:]
            fields["err_limit2_lon"], line = PathParser.parse_lon(line)
            line = line[2:]
            fields["err_limit2_lat"], line = PathParser.parse_lat(line)
        else:
            line = line[2:]
            fields["path_limit1_lat"], line = PathParser.parse_lat(line)
            line = line[2:]
            fields["path_limit2_lat"], line = PathParser.parse_lat(line)
            line = line[2:]
            fields["err_limit1_lat"], line = PathParser.parse_lat(line)
            line = line[2:]
            fields["err_limit2_lat"], line = PathParser.parse_lat(line)
        line = line[2:]
        fields["alt_crn"], line = PathParser.parse_float(line, 5)
        return fields

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
        data_lines, data_options = PathParser._select_path_area(lines)
        timings = []
        ts = datetime.datetime.strptime(event["date"], "%Y %b %d")
        for index, line in enumerate(data_lines):
            try:
                fields = PathParser._parse_line(line, ts, data_options["format_lon"])
            except Exception as e:
                print("Error %s on line #%i skip" % (e, index))
                continue
            timings.append(fields)

        result = {
            "event" : event,
            "timings" : timings,
        }
        return result

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
            lon = fields["center_lon"]
            lat = fields["center_lat"]
            features.append(geojson.Feature(geometry=geojson.Point((lon, lat)),
                                            properties=props))
            if "path_limit1_lon" in fields:
                lon = fields["path_limit1_lon"]
            lat = fields["path_limit1_lat"]
            features.append(geojson.Feature(geometry=geojson.Point((lon, lat)),
                                            properties=props))
            if "path_limit2_lon" in fields:
                lon = fields["path_limit2_lon"]
            lat = fields["path_limit2_lat"]
            features.append(geojson.Feature(geometry=geojson.Point((lon, lat)),
                                            properties=props))

        collection = geojson.FeatureCollection(features=features)
        geojson.dump(collection, f, indent=4)

if __name__ == "__main__":
    process_file_geojson(sys.argv[1], sys.argv[2])
