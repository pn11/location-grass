import datetime
import glob
import svgwrite

COLOR_DICT = {
    "Tochigi": "green",
    "Tokyo": "black",
    "Osaka": "yellow",
    "Kyoto": "brown",
    "Kobe": "red",
    "Hida": "white",
    "USA": "red",
    "Korea": "red",
    "China": "red",
    "Australia": "red"
}

MAX_NUM_WEEK_IN_YEAR = 54
SQUARE_WIDTH = 10
GAP_WIDTH = 2
TOP_MARGIN = 50
LEFT_MARGIN = 50
LEGEND_SQUARE_WIDTH = 20
LEGEND_GAP_WIDTH = 4


def calc_pos(year:int, month:int, day:int):
    date = datetime.datetime(year, month, day)
    isocal = date.isocalendar()
    week_in_year = isocal[1]
    weekday = isocal[2]
    x = (SQUARE_WIDTH+GAP_WIDTH) * (week_in_year-1)
    y = (SQUARE_WIDTH+GAP_WIDTH) * (weekday-1)
    return x, y


def load_data():
    data_dict = {}
    year_list = []
    fnames = glob.glob("data/*.txt")
    for fname in fnames:
        year = int(fname[-8:-4])
        year_list.append(year)
        with open(fname) as f:
            lines = f.readlines()
            for l in lines:
                month = int(l[:2])
                day = int(l[2:5])
                location = l[5:].rstrip()
                datestr = "{:0d}-{:0d}-{:0d}".format(year,month,day)
                x,y = calc_pos(year, month, day)
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
        square_group.add(svgwrite.shapes.Rect(insert=(x, y), size=(SQUARE_WIDTH,SQUARE_WIDTH), fill=COLOR_DICT[location]))
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
    def __init__(self):
        self._dict = {}

    def fill(self, key):
        self._dict[key] = self._dict.get(key, 0) + 1

    def get_dict(self):
        return self._dict

    def show(self):
        print(self.flatten())

    def flatten(self):
        return sorted(self._dict.items(), key=lambda x: -x[1])

    def __str__(self):
        return str(self._dict)

    def __repr__(self):
        return str(self._dict)


def create_histogram(data_dict):
    loc_histo = Histogram()
    for k, v in data_dict.items():
        loc_histo.fill(v['location'])
    return loc_histo


def create_legend(data_dict):
    loc_histo = create_histogram(data_dict)
    legend_group = svgwrite.container.Group()
    dwg = svgwrite.Drawing(filename='image/legend.svg', size=("1000","500"))
    for i, (loc, entries) in enumerate(loc_histo.flatten()):
        square_ypos = (i+0.5)*(LEGEND_SQUARE_WIDTH+LEGEND_GAP_WIDTH)
        legend_group.add(svgwrite.shapes.Rect(insert=(0, square_ypos), size=(LEGEND_SQUARE_WIDTH,LEGEND_SQUARE_WIDTH), fill=COLOR_DICT[loc]))

        label_xpos = LEGEND_SQUARE_WIDTH + LEGEND_GAP_WIDTH
        label_ypos = (i+1)*(LEGEND_SQUARE_WIDTH+LEGEND_GAP_WIDTH)
        legend_group.add(svgwrite.text.Text(text=loc, insert=(label_xpos, label_ypos)))
    dwg.add(legend_group)
    dwg.save()


if __name__ == "__main__":
    year_list, data_dict = load_data()

    for year in year_list:
        dwg = svgwrite.Drawing(filename=f'image/{year}.svg', size=("1000","500"))

        dwg.add(create_square_group(year, data_dict))
        dwg.add(create_day_group())
        dwg.add(create_month_group())

        dwg.save()

    create_legend(data_dict)
