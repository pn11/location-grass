import datetime
import glob
import svgwrite

MAX_NUM_WEEK_IN_YEAR = 54
SQUARE_WIDTH = 10
GAP_WIDTH = 2
TOP_MARGIN = 30
LEFT_MARGIN = 50
IMAGE_WIDTH = 700 # 54*12+50 = 698
IMAGE_HEIGHT = 120 # 7*12+30 = 114
LEGEND_SQUARE_WIDTH = 20
LEGEND_GAP_WIDTH = 4
LEGEND_IMAGE_WIDTH = 200
LEGEND_IMAGE_HEIGHT = 1500


def get_color(location:str):
    COLOR_DICT = {
        "Tochigi": "green",
        "Tokyo": "black",
        "Osaka": "yellow",
        "Kyoto": "brown",
        "Nara": "#c39143",
        "Kobe": "lightblue",
        "Hida": "lightgray",
        "Toyama": "lightgray",
        "Shizuoka": "lightgreen",
        "Jeju": "orange"
    }

    try:
        return COLOR_DICT[location]
    except Exception:
        return "red"


def calc_pos(year:int, month:int, day:int):
    date = datetime.datetime(year, month, day)
    isocal = date.isocalendar()
    # ISO calendar の年と実際の年の違いを補正
    if isocal[0] < year:
        week_in_year = 0
    elif isocal[0] > year:
        week_in_year = isocal[1] + 52
    else:
        week_in_year = isocal[1]
    weekday = isocal[2]
    x = (SQUARE_WIDTH+GAP_WIDTH) * (week_in_year-1)
    y = (SQUARE_WIDTH+GAP_WIDTH) * (weekday-1)
    return x, y


def daterange(_start, _end):
    for i in range((_end - _start).days):
        yield _start + datetime.timedelta(i)

def load_data():
    data_dict = {}
    year_list = []
    fnames = glob.glob("data/*.tsv")
    for fname in fnames:
        year = int(fname[-8:-4])
        year_list.append(year)
        with open(fname) as f:
            lines = f.readlines()
            for l in lines:
                date, location = l.split('\t')
                location = [l.strip().rstrip() for l in location.split('>')]
                start_date = datetime.date(int(year), int(date[:2]), int(date[2:4]))
                if date.find('-') > 0:
                    end_date = datetime.date(int(year), int(date[5:7]), int(date[7:9])) + datetime.timedelta(1)
                else:
                    end_date = start_date + datetime.timedelta(1)

                for d in daterange(start_date, end_date):
                    datestr = "{:0d}-{:0d}-{:0d}".format(year,d.month,d.day)
                    x,y = calc_pos(year, d.month, d.day)
                    data_dict[datestr] = {"location": location, "x": x, "y": y}
    return year_list, data_dict


def create_square_group(year, data_dict):
    square_group = svgwrite.container.Group(**{"transform":f"translate({LEFT_MARGIN}, {TOP_MARGIN})"})
    for date, data in data_dict.items():
        year_key = int(date[:4])
        if year_key != year:
            continue
        x = data['x']
        y = data['y']
        location = data['location']
        nloc = len(location)
        for i, loc in enumerate(location):
            square_group.add(svgwrite.shapes.Rect(insert=(x, y+i*SQUARE_WIDTH/nloc), size=(SQUARE_WIDTH,SQUARE_WIDTH/nloc), fill=get_color(location[i])))
    return square_group


def create_month_group():
    month_group = svgwrite.container.Group(**{"transform":f"translate({LEFT_MARGIN}, 0)"})

    for month in range(1, 13):
        month_pos = MAX_NUM_WEEK_IN_YEAR / 12 * (SQUARE_WIDTH+GAP_WIDTH) * (month-1)
        month_group.add(svgwrite.text.Text(text=str(month), insert=(month_pos, 20)))
    
    return month_group


def create_day_group():
    isoday_dict = {
        1: "Mon",
        2: "",
        3: "Wed",
        4: "",
        5: "Fri",
        6: "",
        7: "Sun"
    }
    day_group = svgwrite.container.Group(**{"transform":f"translate(0, {TOP_MARGIN})"})

    for day in range(1, 8):
        day_group.add(svgwrite.text.Text(text=isoday_dict[day], insert=(0, 12*day)))
    return day_group


class Histogram:
    ## Change to history data
    ## Add attrinutes: last visited, longest stay, first visited
    def __init__(self):
        self._dict = {}

    def fill(self, key, weight=1):
        self._dict[key] = self._dict.get(key, 0) + weight

    def get_dict(self):
        return self._dict

    def show(self):
        print(self.flatten())

    def flatten(self):
        self.round()
        return sorted(self._dict.items(), key=lambda x: -x[1])

    def round(self):
        for k, v in self._dict.items():
            rounded = round(v, 1)
            if str(rounded)[-1] == "0":
                # ex. 123.0 -> 123
                rounded = int(rounded)
            self._dict[k] = rounded
    def get_entry(self, key):
        return self._dict[key]

    def __str__(self):
        return str(self._dict)

    def __repr__(self):
        return str(self._dict)


def create_histogram(data_dict):
    loc_histo = Histogram()
    for k, v in data_dict.items():
        for loc in v['location']:
            loc_histo.fill(loc, weight=1/len(v['location']))
    return loc_histo


def create_legend(data_dict):
    loc_histo = create_histogram(data_dict)
    legend_group = svgwrite.container.Group()
    dwg = svgwrite.Drawing(filename='image/legend.svg', size=(str(LEGEND_IMAGE_WIDTH), str(LEGEND_IMAGE_HEIGHT)))
    for i, (loc, entries) in enumerate(loc_histo.flatten()):
        square_ypos = (i+0.5)*(LEGEND_SQUARE_WIDTH+LEGEND_GAP_WIDTH)
        legend_group.add(svgwrite.shapes.Rect(insert=(0, square_ypos), size=(LEGEND_SQUARE_WIDTH,LEGEND_SQUARE_WIDTH), fill=get_color(loc)))

        label_xpos = LEGEND_SQUARE_WIDTH + LEGEND_GAP_WIDTH
        label_ypos = (i+1)*(LEGEND_SQUARE_WIDTH+LEGEND_GAP_WIDTH)
        legend_group.add(svgwrite.text.Text(text=f"{loc} ({loc_histo.get_entry(loc)} days)", insert=(label_xpos, label_ypos)))
    dwg.add(legend_group)
    dwg.save()


if __name__ == "__main__":
    year_list, data_dict = load_data()

    for year in year_list:
        dwg = svgwrite.Drawing(filename=f'image/{year}.svg', size=(str(IMAGE_WIDTH), str(IMAGE_HEIGHT)))

        dwg.add(create_square_group(year, data_dict))
        dwg.add(create_day_group())
        dwg.add(create_month_group())

        dwg.save()

    create_legend(data_dict)
