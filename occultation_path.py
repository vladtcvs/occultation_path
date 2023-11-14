import sys
import csv

def select_path_area(text):
    lines = text.splitlines()
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

def parse_line(line):
    line = line.replace("-  ", "-00")
    line = line.replace("- ", "-0")
    items = line.split(" ")
    items = [item for item in items if item != '']
    fields = {
        "lon_D" : items[0],
        "lon_M" : items[1],
        "lon_S" : items[2],

        "center_lat_D" : items[3],
        "center_lat_M" : items[4],
        "center_lat_S" : items[5],

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

def transform_DMS(D, M, S):
    if "-" in D:
        sign = -1
    else:
        sign = 1
 
    D = abs(int(D))
    M = int(M)
    S = float(S)
    return sign * (D + M/60 + S/3600)

def transform_fields(fields):
    try:
        transformed = {
            "lon" : transform_DMS(fields["lon_D"], fields["lon_M"], fields["lon_S"]),
            "center_lat" : transform_DMS(fields["center_lat_D"], fields["center_lat_M"], fields["center_lat_S"]),
            "limit1_lat" : transform_DMS(fields["path_limit_1_lat_D"], fields["path_limit_1_lat_M"], fields["path_limit_1_lat_S"]),
            "limit2_lat" : transform_DMS(fields["path_limit_2_lat_D"], fields["path_limit_2_lat_M"], fields["path_limit_2_lat_S"]),
            "limit3_lat" : transform_DMS(fields["err_limit_3_lat_D"], fields["err_limit_3_lat_M"], fields["err_limit_3_lat_S"]),
            "limit4_lat" : transform_DMS(fields["err_limit_4_lat_D"], fields["err_limit_4_lat_M"], fields["err_limit_4_lat_S"]),
            "UT" : "%02i:%02i:%02.1f" % (int(fields["ut_H"]), int(fields["ut_M"]), float(fields["ut_S"])),
            "sun_alt" : int(fields["sun_ALT"]),
            "star_alt" : int(fields["star_ALT"]),
            "star_az" : int(fields["star_AZ"]),
        }
        return transformed
    except:
        return None


def process_file(input_fname, output_fname):
    with open(input_fname) as f:
        text = f.read()

    lines = select_path_area(text)

    with open(output_fname, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["lon", "center_lat", "limit1_lat", "limit2_lat", "limit3_lat", "limit4_lat", "sun_alt", "star_alt", "star_az", "UT"])
        for line in lines:
            fields = transform_fields(parse_line(line))
            if fields is None:
                continue
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

if __name__ == "__main__":
    process_file(sys.argv[1], sys.argv[2])

