from os import listdir
from os.path import isfile, join, basename
from paths import PROTOCOL_DIR

MAX_DOSE_VOLUME = 0.03


class Protocols:
    def __init__(self):
        self.__load()

    def __load(self):
        self.data = {}
        for f in self.file_names:
            file_name = basename(f)
            name = file_name.split('_')[0]
            fxs = file_name.split('_')[1].replace('.scp', '')
            if name not in list(self.data):
                self.data[name] = {}
            self.data[name][fxs] = self.parse_protocol_file(f)

    @property
    def file_names(self):
        return [join(PROTOCOL_DIR, f) for f in listdir(PROTOCOL_DIR) if isfile(join(PROTOCOL_DIR, f)) and '.scp' in f]

    @staticmethod
    def parse_protocol_file(file_path):
        constraints = {}
        current_key = None
        with open(file_path, 'r') as document:
            for line in document:
                if line[0] not in {'\t', ' '}:
                    current_key = line.strip()
                    constraints[current_key] = {}
                else:
                    line_data = line.split()
                    constraints[current_key][line_data[0]] = line_data[1]
        return constraints

    @property
    def protocol_names(self):
        protocols = list(self.data)
        protocols.sort()
        return protocols

    def get_fractionations(self, protocol_name):
        fractionations = list(self.data[protocol_name])
        fractionations.sort()
        fractionations = [fx.replace('fx', '') for fx in fractionations]
        return fractionations

    def get_rois(self, protocol_name, fractionation):
        rois = list(self.data[protocol_name][fractionation])
        rois.sort()
        return rois

    def get_constraints(self, protocol_name, fractionation, roi_name):
        return self.data[protocol_name][fractionation][roi_name]

    def get_column_data(self, protocol_name, fractionation):
        roi_template = []
        keys = ['string_rep', 'operator', 'input_value', 'input_units', 'input_type', 'output_units', 'output_type',
                'input_scale', 'output_scale', 'threshold_value', 'calc_type']
        data = {key: [] for key in keys}

        for roi in self.get_rois(protocol_name, fractionation):
            roi_type = ['OAR', 'PTV']['PTV' in roi]
            for constraint_label, threshold in self.get_constraints(protocol_name, fractionation, roi).items():
                roi_template.append(roi)
                constraint = Constraint(constraint_label, threshold, roi_type=roi_type)
                for key, column in data.items():
                    column.append(getattr(constraint, key))
        data['roi_template'] = roi_template

        return data


class Constraint:
    def __init__(self, constraint_label, threshold, roi_type='OAR'):
        self.constraint_label = constraint_label
        self.threshold = threshold
        self.roi_type = roi_type

    def __str__(self):
        return "%s %s %s" % (self.constraint_label, self.operator, self.threshold)

    def __repr__(self):
        return self.__str__()

    @property
    def threshold_value(self):
        if '%' in self.threshold:
            return float(self.threshold.replace('%', '')) / 100.
        return float(self.threshold)

    @property
    def string_rep(self):
        return self.__str__()

    @property
    def operator(self):
        if self.output_type == 'MVS':
            return ['<', '>']['OAR' in self.roi_type]
        return ['>', '<']['OAR' in self.roi_type]

    @property
    def output_type(self):
        if self.constraint_label == 'Mean':
            return 'D'
        return self.constraint_label.split('_')[0]

    @property
    def output_units(self):
        return ['Gy', 'cc'][self.output_type in {'V', 'MVS'}]

    @property
    def input(self):
        if self.constraint_label == 'Mean':
            return None
        return self.constraint_label.split('_')[1]

    @property
    def input_type(self):
        return ['Volume', 'Dose'][self.output_type in {'V', 'MVS'}]

    @property
    def calc_type(self):
        if 'MVS' in self.constraint_label:
            return 'MVS'
        if 'Mean' in self.constraint_label:
            return 'Mean'
        return self.input_type

    @property
    def input_value(self):
        if self.input is None:
            return None
        if 'max' in self.input:
            return MAX_DOSE_VOLUME
        return float(self.input.replace('%', '').replace('_', ''))

    @property
    def input_scale(self):
        if self.input is None:
            return None
        return ['absolute', 'relative']['%' in self.input]

    @property
    def output_scale(self):
        return ['absolute', 'relative']['%' in self.threshold]

    @property
    def input_units(self):
        if self.input is None:
            return None
        scale = ['absolute', 'relative']['%' in self.input]
        abs_units = ['cc', 'Gy'][self.input_type == 'Dose']
        return ['%', abs_units][scale == 'absolute']
