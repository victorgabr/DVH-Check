from os.path import isdir, join, isfile, getmtime
from os import walk, listdir
import pydicom as dicom
from pydicom.errors import InvalidDicomError
from datetime import datetime


def get_file_paths(start_path, search_subfolders=True):
    if isdir(start_path):
        if search_subfolders:
            file_paths = []
            for root, dirs, files in walk(start_path, topdown=False):
                for name in files:
                    file_paths.append(join(root, name))
            return file_paths

        return [join(start_path, f) for f in listdir(start_path) if isfile(join(start_path, f))]
    return []


def timestamp_to_string(time_stamp):
    return datetime.fromtimestamp(time_stamp).strftime('%Y-%m-%d %H:%M:%S')


class DicomDirectoryParser:
    def __init__(self, start_path, search_subfolders=True):
        self.start_path = start_path
        self.search_subfolders = search_subfolders
        self.file_types = {'rtplan', 'rtstruct', 'rtdose'}

        self.__parse_directory_new()
        self.__validate()

    def __parse_directory_new(self):
        self.file_paths = get_file_paths(self.start_path, search_subfolders=self.search_subfolders)

        self.dicom_tag_values = {}
        self.dicom_files = {key: [] for key in self.file_types}
        self.plan_file_sets = {}

        # dicom_file_data:  collect necessary dicom tags with a dictionary with file_paths for keys
        # dicom_files:      identify files by modality (key is modality)
        # plan_file_sets:   this will be the useful object in the end, give it "Patient Name - Plan Name", get
        #                   appropriate file paths.  GUI will use this.
        for file_path in self.file_paths:
            ds = self.read_dicom_file(file_path)
            if ds is not None:
                modality = ds.Modality.lower()
                timestamp = getmtime(file_path)

                self.dicom_files[modality].append(file_path)

                self.dicom_tag_values[file_path] = {'timestamp': timestamp,
                                                    'study_instance_uid': ds.StudyInstanceUID,
                                                    'sop_instance_uid': ds.SOPInstanceUID,
                                                    'patient_name': str(ds.PatientName)}

                if modality == 'rtplan':
                    self.dicom_tag_values[file_path]['ref_sop_instance'] = {'type': 'struct',
                                                                            'uid': ds.ReferencedStructureSetSequence[0].ReferencedSOPInstanceUID}
                    plan_key = "%s - %s - %s" % (ds.PatientName, ds.RTPlanLabel, timestamp_to_string(timestamp))
                    self.plan_file_sets[plan_key] = {'rtplan': {'file_path': file_path, 'sop_instance_uid': ds.SOPInstanceUID}}
                elif modality == 'rtdose':
                    self.dicom_tag_values[file_path]['ref_sop_instance'] = {'type': 'plan',
                                                                            'uid': ds.ReferencedRTPlanSequence[0].ReferencedSOPInstanceUID}
                else:
                    self.dicom_tag_values[file_path]['ref_sop_instance'] = {'type': None, 'uid': None}

        # associate appropriate rtdose files to plans
        for dose_file in self.dicom_files['rtdose']:
            dose_tag_values = self.dicom_tag_values[dose_file]
            ref_plan_uid = dose_tag_values['ref_sop_instance']['uid']
            for plan_file_set in self.plan_file_sets.values():
                plan_uid = plan_file_set['rtplan']['sop_instance_uid']
                if plan_uid == ref_plan_uid:
                    plan_file_set['rtdose'] = {'file_path': dose_file,
                                               'sop_instance_uid': dose_tag_values['sop_instance_uid']}
        # associate appropriate rtstruct files to plans
        for plan_file_set in self.plan_file_sets.values():
            plan_file = plan_file_set['rtplan']['file_path']
            ref_struct_uid = self.dicom_tag_values[plan_file]['ref_sop_instance']['uid']
            for struct_file in self.dicom_files['rtstruct']:
                struct_uid = self.dicom_tag_values[struct_file]['sop_instance_uid']
                if struct_uid == ref_struct_uid:
                    plan_file_set['rtstruct'] = {'file_path': struct_file,
                                                 'sop_instance_uid': struct_uid}

    def __validate(self):
        bad_plans = []
        for key, plan_file_set in self.plan_file_sets.items():
            if self.file_types != set(list(plan_file_set)):  # Does plan_file_set not have one of the file_types?
                bad_plans.append(key)

        for plan in bad_plans:
            self.plan_file_sets.pop(plan)

    @staticmethod
    def read_dicom_file(file_path):
        try:
            return dicom.read_file(file_path, stop_before_pixels=True)
        except InvalidDicomError:
            return None

    def get_file_type(self, dicom_file):
        file_type = dicom_file.Modality.lower()
        if file_type not in self.file_types:
            return 'other'
        return file_type

    @property
    def plan_names(self):
        return list(self.plan_file_sets)

    def get_plan_files(self, plan_name):
        return {file_type: self.plan_file_sets[plan_name][file_type]['file_path'] for file_type in self.file_types}

    @property
    def plans(self):
        return {plan_name: self.get_plan_files(plan_name) for plan_name in self.plan_names}


def get_plans(start_path):
    return DicomDirectoryParser(start_path).plans
