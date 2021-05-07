import unittest
import os
import shutil
import json
from bids_pipeline import pipeline_class as pip
from bids_manager import ins_bids_class as bids
from bids_pipeline import interface_class as itf
from bids_pipeline import export_merge as exp

__main_dir__ = r'D:\Data\testing'
__bids_dir__ = r'D:\Data\testing\test_dataset'
__bids_dataset__ = bids.BidsDataset(__bids_dir__)


class PipelineTest(unittest.TestCase):

    @classmethod
    def setUp(cls):
        cls.software_name = 'testing'

    def test_init(self):
        #Verify that cannot set bids or software not allowed
        with self.assertRaises(EOFError):
            soft_analyse = pip.PipelineSetting(os.path.join(__main_dir__, 'bids_vide'), self.software_name)
        with self.assertRaises(EOFError):
            soft_analyse = pip.PipelineSetting(__bids_dir__, 'h2', soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        with self.assertRaises(EOFError):
            soft_analyse = pip.PipelineSetting(__bids_dataset__, 'testing_path_error',
                                                   soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        with self.assertRaises(EOFError):
            soft_analyse = pip.PipelineSetting(__bids_dataset__, 'testing_paramerror',
                                               soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        with self.assertRaises(KeyError):
            soft_analyse = pip.PipelineSetting(__bids_dataset__, 'testing_output',
                                               soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        soft_analyse = pip.PipelineSetting(__bids_dataset__, self.software_name, soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        keys = [key for key in soft_analyse]
        self.assertEqual(keys, pip.PipelineSetting.keylist)
        for key in soft_analyse['Parameters']:
            if key in pip.Parameters.keylist:
                pass
            elif key in pip.ParametersSide.get_list_subclasses_names():
                self.assertIsInstance(soft_analyse['Parameters'][key], pip.ParametersSide)
            elif key in pip.Parameters.get_list_subclasses_names():
                self.assertIsInstance(soft_analyse['Parameters'][key], pip.Parameters)
            else:
                self.assertIsInstance(soft_analyse['Parameters'][key], pip.Arguments)

    def test_get_arguments(self):
        with self.assertRaises(EOFError):
            soft = pip.PipelineSetting(__bids_dataset__, 'testing_paramerror', soft_path=os.path.join(__main_dir__, 'software_pipeline'))
            param_vars = itf.ParameterInterface(__bids_dataset__, soft['Parameters'])
            in_vars = {}
            for inp in soft['Parameters']['Input']:
                in_vars['Input_'+inp['tag']] = itf.InputParameterInterface(__bids_dataset__, inp)
        soft_analyse = pip.PipelineSetting(__bids_dataset__, self.software_name, soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        param_vars = itf.ParameterInterface(__bids_dataset__, soft_analyse['Parameters'])
        in_vars = {}
        for inp in soft_analyse['Parameters']['Input']:
            in_vars['Input_' + inp['tag']] = itf.InputParameterInterface(__bids_dataset__, inp)
        param_tmp = dict()
        in_tmp = dict()
        keys = ['Mode', '--participants', 'Input_--input_ieeg', 'Input_--input_anat', '--duration', '--criteria', '--criteriadata', '--task', '--file']
        for cnt, elt in enumerate(keys):
            if cnt == 0:
                param_tmp[elt] = dict()
                param_tmp[elt]['attribut'] = 'Listbox'
                param_tmp[elt]['value'] = ['manual', 'automatic']
            elif cnt == 1:
                param_tmp[elt] = dict()
                param_tmp[elt]['attribut'] = 'Bool'
                param_tmp[elt]['value'] = False
            elif cnt == 2:
                in_tmp[elt] = dict()
                in_tmp[elt]['modality'] = {'value': 'Ieeg', 'attribut': 'Label'}
                in_tmp[elt]['run'] = {'value': ['01', '02', '03'], 'attribut': 'Variable'}
                in_tmp[elt]['ses'] = {'value': ['01'], 'attribut': 'Label'}
                #in_tmp[elt]['task'] = {'value': ['ccep'], 'attribut': 'Label'}
            elif cnt == 3:
                in_tmp[elt] = dict()
                in_tmp[elt]['modality'] = {'value': 'Anat', 'attribut': 'Label'}
                in_tmp[elt]['acq'] = {'value': ['postimp', 'preimp'], 'attribut': 'Variable'}
                in_tmp[elt]['ses'] = {'value': ['01'], 'attribut': 'Label'}
                in_tmp[elt]['mod'] = {'value': ['CT', 'T1w'], 'attribut': 'Variable'}
            elif cnt == 4:
                param_tmp[elt] = dict()
                param_tmp[elt]['attribut'] = 'StringVar'
                param_tmp[elt]['value'] = '10sec_--duration'
                param_tmp[elt]['unit'] = 'sec'
            elif cnt == 5:
                param_tmp[elt] = dict()
                param_tmp[elt]['attribut'] = 'Variable'
                # param_tmp[elt]['value'] = ['Begin', 'Post', 'Pre', 'Stim']
                param_tmp[elt]['value'] = ['Begin', 'Pre', 'S 2', 'S 25', 'S 28', 'S 3', 'S 5', 'Spike', 'Stim', 'Stimulation']
            elif cnt == 6:
                param_tmp[elt] = dict()
                param_tmp[elt]['attribut'] = 'Variable'
                param_tmp[elt]['value'] = ['ses', 'task', 'modality']
            elif cnt == 8:
                param_tmp[elt] = dict()
                param_tmp[elt]['attribut'] = 'File'
                param_tmp[elt]['value'] = ['.tsv']
        self.assertEqual(param_vars, param_tmp)
        self.assertEqual(in_vars, in_tmp)

    def test_read_json(self):
        pip_file = 'testing_modality'
        soft = pip.PipelineSetting(__bids_dataset__, pip_file,
                                                   soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        for cnt, elt in enumerate(soft['Parameters']['Input']):
            if cnt == 0:
                self.assertEqual(elt['modality'], ['Ieeg'])
            elif cnt ==1:
                self.assertEqual(elt['modality'], ['Eeg', 'Meg', 'Ieeg'])


class ParameterTest(unittest.TestCase):

    def setUp(self):
        self.results = {}
        self.results['subject_selected'] = ['01', '02', '03']
        self.results['analysis_param'] = {'Mode': 'automatic', '--duration': '20', '--criteria': ['Stim', 'stim'], '--criteriadata': 'ses', '--task': 'acq'}
        self.results['input_param'] = {}
        self.results['input_param']['Input_--input_ieeg'] = {'modality': 'Ieeg', 'ses': '01', 'run': '01'}
        self.results['input_param']['Input_--input_anat'] = {'modality': 'Anat', 'acq': ['preimp'], 'mod': ['T1w']}
        self.output_dir = os.path.join(__bids_dir__, 'derivatives', 'testing')

    def test_multiple_input_output(self):
        analyse = pip.PipelineSetting(__bids_dataset__, 'testing', soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        analyse['Parameters'].update_values(self.results['analysis_param'], self.results['input_param'])
        subjects = pip.SubjectToAnalyse(self.results['subject_selected'], input_dict=self.results['input_param'])
        subjects_results = {'sub': ['01', '02', '03'], 'Input_--input_ieeg': {'modality': ['Ieeg'], 'ses': ['01'], 'run':
            ['01']}, 'Input_--input_anat': {'modality': ['Anat'], 'acq': ['preimp'], 'mod': ['T1w']}}
        self.assertEqual(subjects, subjects_results)
        cmd_arg, cmd_line, order, input_dict, output_dict, interm = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        cmd_tmp = 'D:/Data/testing --input_ieeg {0} --input_anat {1} --output_file {2} --duration 20 --criteria "Stim, stim" --criteriadata ses --task preimp'
        self.assertIsInstance(cmd_arg, pip.Parameters)
        self.assertEqual(cmd_line, cmd_tmp)
        self.assertIsNotNone(order)
        taille, idx_in, in_out, error_in = input_dict.get_input_values(subjects, order)
        output_dict.get_output_values(in_out, taille, order, self.output_dir, idx_in)
        for sub in in_out:
            in_out_res = [['D:\\Data\\testing\\test_dataset\\sub-{0}\\ses-01\\ieeg\\sub-{0}_ses-01_task-ccep_run-01_ieeg.vhdr'.format(sub)], ['D:\\Data\\testing\\test_dataset\\sub-{0}\\ses-01\\anat\\sub-{0}_ses-01_acq-preimp_T1w.nii'.format(sub)], [['D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-{0}\\ses-01\\ieeg\\sub-{0}_ses-01_task-ccep_run-01_testing.mat'.format(sub), 'D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-{0}\\ses-01\\ieeg\\sub-{0}_ses-01_task-ccep_run-01_testing.tsv'.format(sub)]]]
            self.assertEqual(in_out[sub], in_out_res)
            idx = 0
            while idx < taille[sub]:
                use_list = list_for_str_format(in_out[sub], idx)
                cmd = cmd_line.format(*use_list)
                cmd_final = 'D:/Data/testing --input_ieeg D:\\Data\\testing\\test_dataset\\sub-{0}\\ses-01\\ieeg\\sub-{0}_ses-01_task-ccep_run-01_ieeg.vhdr --input_anat D:\\Data\\testing\\test_dataset\\sub-{0}\\ses-01\\anat\\sub-{0}_ses-01_acq-preimp_T1w.nii --output_file "D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-{0}\\ses-01\\ieeg\\sub-{0}_ses-01_task-ccep_run-01_testing.mat, D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-{0}\\ses-01\\ieeg\\sub-{0}_ses-01_task-ccep_run-01_testing.tsv" --duration 20 --criteria "Stim, stim" --criteriadata ses --task preimp'.format(sub)
                self.assertEqual(cmd, cmd_final)
                idx = idx + 1

    def test_bids_directory_input(self):
        self.results['input_param'] = {}
        self.results['input_param']['Input_--input_dir'] = {'modality': 'Ieeg', 'ses': '01', 'run': '01'}
        analyse = pip.PipelineSetting(__bids_dataset__, 'testing_input_dir', soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        analyse['Parameters'].update_values(self.results['analysis_param'], self.results['input_param'])
        subjects = pip.SubjectToAnalyse(self.results['subject_selected'], input_dict=self.results['input_param'])
        cmd_arg, cmd_line, order, input_dict, output_dict, interm = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        self.assertIsInstance(cmd_arg, pip.Parameters)
        self.assertFalse(order)

    def test_input_directory(self):
        self.results['input_param'] = {}
        self.results['input_param']['Input_--input_dir'] = {'modality': 'Ieeg', 'ses': '01', 'run': '01'}
        analyse = pip.PipelineSetting(__bids_dataset__, 'testing_input_directory', soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        analyse['Parameters'].update_values(self.results['analysis_param'], self.results['input_param'])
        subjects = pip.SubjectToAnalyse(self.results['subject_selected'], input_dict=self.results['input_param'])
        cmd_arg, cmd_line, order, input_dict, output_dict, interm = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        self.assertIsInstance(cmd_arg, pip.Parameters)
        self.assertIsNotNone(order)
        taille, idx_in, in_out, error_in = input_dict.get_input_values(subjects, order)
        output_dict.get_output_values(in_out, taille, order, self.output_dir, idx_in)
        for sub in in_out:
            in_out_res = [['D:\\Data\\testing\\test_dataset\\sub-{0}\\ses-01\\ieeg'.format(sub)], [['D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-{0}\\ses-01\\ieeg'.format(sub)]]]
            self.assertEqual(in_out[sub], in_out_res)
        # self.results['input_param'] = {}
        # self.results['input_param']['Input_--input_dir'] = {'modality': 'Anat', 'acq': ['preimp'], 'mod': ['T1w']}
        # subjects_anat = pip.SubjectToAnalyse(self.results['subject_selected'], input_dict=self.results['input_param'])
        # taille, idx_in, in_out_anat = input_dict.get_input_values(subjects_anat, order)
        # output_dict.get_output_values(in_out_anat, taille, order, self.output_dir, idx_in)
        # for sub in in_out_anat:
        #     in_out_res = [['D:\\Data\\testing\\test_dataset\\sub-{0}\\anat'.format(sub)], [
        #         ['D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-{0}\\anat'.format(sub)]]]
        #     self.assertEqual(in_out_anat[sub], in_out_res)

    def test_infile_outdir(self):
        self.results['input_param'] = {}
        self.results['input_param']['Input_--input_ieeg'] = {'modality': 'Ieeg', 'ses': '01', 'run': '01'}
        analyse = pip.PipelineSetting(__bids_dataset__, 'testing_infile_outdir', soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        analyse['Parameters'].update_values(self.results['analysis_param'], self.results['input_param'])
        subjects = pip.SubjectToAnalyse(self.results['subject_selected'], input_dict=self.results['input_param'])
        cmd_arg, cmd_line, order, input_dict, output_dict, interm = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        self.assertIsInstance(cmd_arg, pip.Parameters)
        self.assertIsNotNone(order)
        taille, idx_in, in_out, error_in = input_dict.get_input_values(subjects, order)
        output_dict.get_output_values(in_out, taille, order, self.output_dir, idx_in)
        for sub in in_out:
            in_out_res = [['D:\\Data\\testing\\test_dataset\\sub-{0}\\ses-01\\ieeg\\sub-{0}_ses-01_task-ccep_run-01_ieeg.vhdr'.format(sub)],
                          [['D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-{0}\\ses-01\\ieeg'.format(sub)]]]
            self.assertEqual(in_out[sub], in_out_res)

    def test_instance_parameter(self):
        self.results['input_param'] = {}
        self.results['input_param']['Input_--input_ieeg'] = {'modality': 'Ieeg', 'ses': '01'}
        subjects = pip.SubjectToAnalyse(self.results['subject_selected'], input_dict=self.results['input_param'])
        #assert intermediate instance
        analyse = pip.PipelineSetting(__bids_dataset__, 'h2')
        cmd_arg, cmd_line, order, input_dict, output_dict, interm = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        cmd_tmp = 'C:/anywave_mars/AnyWave.exe --run D:\\Data\\testing\\test_dataset\\derivatives\\testing\\h2_parameters.json --input_file {0} --output_dir {1} --output_file {2} --log_dir C:\\Users\\jegou\\AnyWave\\Log'
        self.assertIsInstance(cmd_arg, pip.AnyWave)
        self.assertEqual(cmd_line, cmd_tmp)

        analyse = pip.PipelineSetting(__bids_dataset__, 'example')
        cmd_arg, cmd_line, order, input_dict, output_dict, interm = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        cmd_tmp = 'docker run -i --rm -v D:\\Data\\testing\\test_dataset:/bids_dataset:ro -v D:\\Data\\testing\\test_dataset\\derivatives\\testing:/outputs bids/example /bids_dataset /outputs --participant_label [01 02 03]'
        self.assertIsInstance(cmd_arg, pip.Docker)
        self.assertEqual(cmd_line, cmd_tmp)

        analyse = pip.PipelineSetting(__bids_dataset__, 'averaging_EP')
        cmd_arg, cmd_line, order, input_dict, output_dict, interm = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        cmd_tmp = "matlab -wait -nosplash -nodesktop -r \"cd('D:\\Matlab'); averaging_EP('{0}', '{1}'); exit\""
        self.assertIsInstance(cmd_arg, pip.Matlab)
        self.assertEqual(cmd_line, cmd_tmp)

        analyse = pip.PipelineSetting(__bids_dataset__, 'statistics_bdd_bool', soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        cmd_arg, cmd_line, order, input_dict, output_dict, interm = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        cmd_tmp = 'D:/Software/Bids_Manager/statistics_bdd.exe --participants False --bidsdirectory D:\\Data\\testing\\test_dataset --outputdirectory D:\\Data\\testing\\test_dataset\\derivatives\\testing --subjectlist "01, 02, 03"'
        self.assertIsInstance(cmd_arg, pip.Parameters)
        self.assertEqual(cmd_line, cmd_tmp)

    def test_validity_input_parameters(self):
        warn, err = pip.verify_subject_has_parameters(__bids_dataset__,
                                                  self.results['subject_selected'],
                                                  self.results['input_param'])
        self.assertEqual(err, '')
        #Test if multiple modality as entry
        self.results['input_param']['Input_--input_ieeg'] = {'modality': ['Ieeg', 'Eeg'], 'ses': '01', 'run': '01'}
        warn, err = pip.verify_subject_has_parameters(__bids_dataset__,
                                                      self.results['subject_selected'],
                                                      self.results['input_param'])
        self.assertEqual(err, 'There is no more subject in the selection.\n Please modify your parameters.\n')#'Modalities selected in the input Input_--input_ieeg are too differents\n.')
        #Test if subjects are removed because don't have the required input
        self.results['subject_selected'] = ['01', '02', '03']
        self.results['input_param']['Input_--input_ieeg'] = {'modality': ['Ieeg'], 'ses': '01', 'run': '02'}
        warn, err = pip.verify_subject_has_parameters(__bids_dataset__,
                                                      self.results['subject_selected'],
                                                      self.results['input_param'])
        self.assertEqual(self.results['subject_selected'], ['01', '02'])

    def test_multiple_input(self):
        analyse = pip.PipelineSetting(__bids_dataset__, 'testing_multiple_input',
                                      soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        self.results['input_param'] = {}
        self.results['input_param']['Input_--input_ieeg'] = {'modality': 'Ieeg', 'ses': '01'}
        self.results['input_param']['Input_--input_delphos'] = {'deriv-folder': 'Delphos', 'modality': 'Ieeg', 'ses': '01'}
        analyse['Parameters'].update_values(self.results['analysis_param'], self.results['input_param'])
        subjects = pip.SubjectToAnalyse(self.results['subject_selected'], input_dict=self.results['input_param'])
        cmd_arg, cmd_line, order, input_dict, output_dict, interm = analyse.create_command_to_run_analysis(self.output_dir,
                                                                                                   subjects)
        self.assertIsInstance(cmd_arg, pip.Parameters)
        self.assertIsNotNone(order)
        taille, idx_in, in_out, error_in = input_dict.get_input_values(subjects, order)
        output_dict.get_output_values(in_out, taille, order, self.output_dir, idx_in)
        self.assertIn('ERROR: The elements in the list don"t have the same size.\nThe subject 01 won"t be analysed because it doesn"t match the inputs specificity.\n', error_in)
        in_out_res = {'02': [['D:\\Data\\testing\\test_dataset\\sub-02\\ses-01\\ieeg\\sub-02_ses-01_task-ccep_run-01_ieeg.vhdr', 'D:\\Data\\testing\\test_dataset\\sub-02\\ses-01\\ieeg\\sub-02_ses-01_task-ccep_run-02_ieeg.vhdr'],
                            ['D:\\Data\\testing\\test_dataset\\derivatives\\Delphos\\sub-02\\ses-01\\ieeg\\sub-02_ses-01_task-ccep_run-01_delphos.mat', 'D:\\Data\\testing\\test_dataset\\derivatives\\Delphos\\sub-02\\ses-01\\ieeg\\sub-02_ses-01_task-ccep_run-02_delphos.mat'],
                            [['D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-02\\ses-01\\ieeg'], ['D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-02\\ses-01\\ieeg']]],
                      '03': [['D:\\Data\\testing\\test_dataset\\sub-03\\ses-01\\ieeg\\sub-03_ses-01_task-ccep_run-01_ieeg.vhdr'],
                             ['D:\\Data\\testing\\test_dataset\\derivatives\\Delphos\\sub-03\\ses-01\\ieeg\\sub-03_ses-01_task-ccep_run-01_delphos.mat'],
                             [['D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-03\\ses-01\\ieeg']]]
                      }
        self.assertDictEqual(in_out, in_out_res)

    def test_multiple_input_dev(self):
        analyse = pip.PipelineSetting(__bids_dataset__, 'testing_multiple_input_dev',
                                      soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        self.results['input_param'] = {}
        self.results['input_param']['Input_in0'] = {'modality': 'Ieeg', 'ses': '01'}
        self.results['input_param']['Input_in1'] = {'deriv-folder': 'Delphos', 'modality': 'Ieeg',
                                                                'ses': '01'}
        analyse['Parameters'].update_values(self.results['analysis_param'], self.results['input_param'])
        subjects = pip.SubjectToAnalyse(self.results['subject_selected'], input_dict=self.results['input_param'])
        cmd_arg, cmd_line, order, input_dict, output_dict, interm = analyse.create_command_to_run_analysis(self.output_dir,
                                                                                                   subjects)
        self.assertIsInstance(cmd_arg, pip.Matlab)
        self.assertIsNotNone(order)
        taille, idx_in, in_out, error_in = input_dict.get_input_values(subjects, order)
        output_dict.get_output_values(in_out, taille, order, self.output_dir, idx_in)
        self.assertIn('ERROR: The elements in the list don"t have the same size.\nThe subject 01 won"t be analysed because it doesn"t match the inputs specificity.\n', error_in)
        in_out_res = {'02': [
            ['D:\\Data\\testing\\test_dataset\\sub-02\\ses-01\\ieeg\\sub-02_ses-01_task-ccep_run-01_ieeg.vhdr',
             'D:\\Data\\testing\\test_dataset\\sub-02\\ses-01\\ieeg\\sub-02_ses-01_task-ccep_run-02_ieeg.vhdr'],
            [
                'D:\\Data\\testing\\test_dataset\\derivatives\\Delphos\\sub-02\\ses-01\\ieeg\\sub-02_ses-01_task-ccep_run-01_delphos.mat',
                'D:\\Data\\testing\\test_dataset\\derivatives\\Delphos\\sub-02\\ses-01\\ieeg\\sub-02_ses-01_task-ccep_run-02_delphos.mat'],
            [['D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-02\\ses-01\\ieeg'],
             ['D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-02\\ses-01\\ieeg']]],
                      '03': [[
                                 'D:\\Data\\testing\\test_dataset\\sub-03\\ses-01\\ieeg\\sub-03_ses-01_task-ccep_run-01_ieeg.vhdr'],
                             [
                                 'D:\\Data\\testing\\test_dataset\\derivatives\\Delphos\\sub-03\\ses-01\\ieeg\\sub-03_ses-01_task-ccep_run-01_delphos.mat'],
                             [['D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-03\\ses-01\\ieeg']]]
                      }
        self.assertDictEqual(in_out, in_out_res)
        cmd_res = "matlab -wait -nosplash -nodesktop -r \"cd('D:/Data/testing/software_pipeline'); testing('{0}', '{1}', '--output_dir', '{2}', '--duration', 20, '--criteria', 'Stim, stim', '--criteriadata', 'ses'); exit\""
        self.assertEqual(cmd_line, cmd_res)


class DerivativesTest(unittest.TestCase):
    def setUp(self):
        self.results = {}
        self.results['subject_selected'] = ['01', '02']
        self.results['analysis_param'] = {'Mode': 'automatic', '--duration': '20', '--criteria': ['Stim', 'stim'], '--criteriadata': 'ses', '--task': 'acq'}
        self.results['input_param'] = {}
        self.results['input_param']['Input_--input_ieeg'] = {'modality': 'Ieeg', 'ses': '01', 'run': '01'}
        self.results['input_param']['Input_--input_anat'] = {'modality': 'Anat', 'acq': ['preimp'], 'mod': ['T1w']}
        self.subject = pip.SubjectToAnalyse(self.results['subject_selected'], input_dict=self.results['input_param'])
        #self.output_dir = os.path.join(__bids_dir__, 'derivatives', 'testing')

    def test_create_output_directory(self):
        if os.path.exists('D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory'):
            shutil.rmtree('D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory')
        if os.path.exists('D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory-v2'):
            shutil.rmtree('D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory-v2')
        if os.path.exists('D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory-v3'):
            shutil.rmtree('D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory-v3')
        if os.path.exists('D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory-v4'):
            shutil.rmtree('D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory-v4')
        __bids_dataset__.parse_bids()
        dev = pip.DerivativesSetting(__bids_dataset__['Derivatives'][0])
        output_directory, output_name, dataset_desc = dev.create_pipeline_directory('testing_input_directory', self.results['analysis_param'], self.subject)
        self.assertEqual(output_directory, 'D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory')
        dev.parse_pipeline(output_directory, output_name)
        # Add subject with same parameter
        new_subject = pip.SubjectToAnalyse(['03'], input_dict=self.results['input_param'])
        output_directory, output_name, dataset_desc = dev.create_pipeline_directory('testing_input_directory', self.results['analysis_param'], new_subject)
        self.assertEqual(output_directory, 'D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory')
        dev.parse_pipeline(output_directory, output_name)
        sub_in = dataset_desc['SourceDataset']['sub']
        sub_in.sort()
        self.assertCountEqual(sub_in, ['01', '02', '03'])
        # Add different acq and run with same subject
        self.results['input_param'] = {}
        self.results['input_param']['Input_--input_ieeg'] = {'modality': 'Ieeg', 'ses': '01', 'run': '02'}
        self.results['input_param']['Input_--input_anat'] = {'modality': 'Anat', 'acq': ['postimp'], 'mod': ['T1w']}
        new_subject = pip.SubjectToAnalyse(['03'], input_dict=self.results['input_param'])
        output_directory, output_name, dataset_desc = dev.create_pipeline_directory('testing_input_directory',
                                                                                    self.results['analysis_param'],
                                                                                    new_subject)
        self.assertEqual(output_directory, 'D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory')
        dataset_desc.update(new_subject, subanalysed=['01', '02', '03'])
        self.assertCountEqual(dataset_desc['SourceDataset']['sub'], ['01', '02', '03'])
        self.assertCountEqual(dataset_desc['SourceDataset']['Input_--input_anat']['acq'], ['preimp', 'postimp'], 'The acq in dataset_description was not well updated')
        self.assertCountEqual(dataset_desc['SourceDataset']['Input_--input_ieeg']['run'], ['01', '02'],
                         'The run in dataset_description was not well updated')
        dev.parse_pipeline(output_directory, output_name)
        # Change the input modality with same subject
        self.results['input_param']['Input_--input_anat'] = {'modality': 'Dwi', 'acq': ['preimp'], 'mod': ['T1w']}
        new_subject = pip.SubjectToAnalyse(['03'], input_dict=self.results['input_param'])
        output_directory, output_name, dataset_desc = dev.create_pipeline_directory('testing_input_directory',
                                                                                    self.results['analysis_param'],
                                                                                    new_subject)
        self.assertEqual(output_directory, 'D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory')
        dataset_desc.update(new_subject, subanalysed=['01', '02', '03'])
        self.assertCountEqual(dataset_desc['SourceDataset']['sub'], ['01', '02', '03'])
        self.assertCountEqual(dataset_desc['SourceDataset']['Input_--input_anat']['modality'], ['Anat', 'Dwi'],
                         'The modality in dataset_description was not well updated')
        dev.parse_pipeline(output_directory, output_name)
        # Change the input session with same subject
        self.results['input_param']['Input_--input_ieeg'] = {'modality': 'Ieeg', 'ses': '02', 'run': '01'}
        new_subject = pip.SubjectToAnalyse(['01'], input_dict=self.results['input_param'])
        output_directory, output_name, dataset_desc = dev.create_pipeline_directory('testing_input_directory',
                                                                                    self.results['analysis_param'],
                                                                                    new_subject)
        self.assertEqual(output_directory, 'D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory')
        dataset_desc.update(new_subject, subanalysed=['01', '02', '03'])
        self.assertCountEqual(dataset_desc['SourceDataset']['sub'], ['01', '02', '03'])
        self.assertCountEqual(dataset_desc['SourceDataset']['Input_--input_ieeg']['ses'], ['01', '02'],
                         'The modality in dataset_description was not well updated')
        dev.parse_pipeline(output_directory, output_name)
        # New directory : Change the input session with same subject but with all session
        self.results['input_param']['Input_--input_ieeg'] = {'modality': 'Ieeg', 'ses': ['01','02'], 'run': '01'}
        self.results['input_param']['Input_--input_anat'] = {'modality': 'Anat', 'acq': ['preimp'], 'mod': ['T1w']}
        new_subject = pip.SubjectToAnalyse(['01'], input_dict=self.results['input_param'])
        output_directory, output_name, dataset_desc = dev.create_pipeline_directory('testing_input_directory',
                                                                                    self.results['analysis_param'],
                                                                                    new_subject)
        self.assertEqual(output_directory, 'D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory-v2')
        dataset_desc.update(new_subject, subanalysed=['01'])
        self.assertCountEqual(dataset_desc['SourceDataset']['sub'], ['01'])
        self.assertCountEqual(dataset_desc['SourceDataset']['Input_--input_ieeg']['ses'], ['01', '02'],
                         'The modality in dataset_description was not well updated')
        dev.parse_pipeline(output_directory, output_name)
        # Create new directory
        self.results['input_param']['Input_--input_ieeg'] = {'modality': 'Ieeg', 'ses': '01', 'run': '01'}
        self.results['input_param']['Input_--input_anat'] = {'modality': 'Anat', 'acq': ['preimp'], 'mod': ['T1w']}
        self.subject = pip.SubjectToAnalyse(self.results['subject_selected'], input_dict=self.results['input_param'])
        output_directory, output_name, dataset_desc = dev.create_pipeline_directory('testing_input_directory',
                                                                                    self.results['analysis_param'],
                                                                                    self.subject)
        self.assertEqual(output_directory, 'D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory-v3')
        dev.parse_pipeline(output_directory, output_name)
        # Create new directory because not same parameters
        self.results['analysis_param'] = {'Mode': 'automatic', '--duration': '40', '--criteria': ['Stim', 'stim'],
                                          '--criteriadata': 'ses', '--task': 'acq'}
        output_directory, output_name, dataset_desc = dev.create_pipeline_directory('testing_input_directory',
                                                                                    self.results['analysis_param'],
                                                                                    self.subject)
        self.assertEqual(output_directory, 'D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory-v4')
        dev.parse_pipeline(output_directory, output_name)
        # test the dataset update by removing an elements
        self.subject.remove('02')
        dataset_desc.update(self.subject, subject2remove=['02'], subanalysed=['01'])
        self.assertCountEqual(dataset_desc['SourceDataset']['sub'], ['01'])

    def test_update_dataset_after_analysis_input_files(self):
        analyse = pip.PipelineSetting(__bids_dataset__, 'ica')
        self.results = {}
        self.results['subject_selected'] = ['02']
        self.results['analysis_param'] = {'Mode': 'automatic', 'hp': '1', 'lp': '70', 'comp': '20'}
        self.results['input_param'] = {'Input_--input_file': {'modality': ['Ieeg'], 'ses': ['01']}}
        self.subject = pip.SubjectToAnalyse(self.results['subject_selected'], input_dict=self.results['input_param'])
        self.assertEqual(self.subject['Input_--input_file'], self.results['input_param']['Input_--input_file'])
        log_analysis, output_name, file_to_write = analyse.set_everything_for_analysis(self.results)
        datadesc = bids.DatasetDescPipeline(os.path.join(__bids_dir__, 'derivatives', output_name, 'dataset_description.json'))
        self.assertNotEqual(self.subject['Input_--input_file'], datadesc['SourceDataset']['Input_--input_file'])
        self.assertCountEqual(datadesc['SourceDataset']['Input_--input_file'], {'modality': ['Ieeg'], 'ses': ['01'], 'task': ['ccep'], 'run': ['01', '02', '03']})
        shutil.rmtree(os.path.join(__bids_dir__, 'derivatives', output_name))

    def test_empty_dirs(self):
        outdev = os.path.join(__main_dir__, 'testempty', 'derivatives')
        if os.path.exists(outdev):
            shutil.rmtree(outdev)
        shutil.copytree(os.path.join(__main_dir__, 'testempty', 'orig'), outdev)
        deriv = pip.DerivativesSetting(outdev)
        self.assertEqual(deriv.log, 'Folder empty has been removed from the derivatives BIDS dataset because it is empty.\n')
        self.assertTrue(len(os.listdir(outdev)) == 2)
        isempty, loghalf = deriv.empty_dirs('half-empty', rmemptysub=True)
        self.assertFalse(isempty)
        self.assertEqual(loghalf, 'Subject sub-01 has been removed from the derivatives folder D:\\Data\\testing\\testempty\\derivatives\\half-empty\n')
        self.assertTrue(len(os.listdir(os.path.join(outdev, 'half-empty'))) == 4)
        isempty, lognot = deriv.empty_dirs('notempty', rmemptysub=True)
        self.assertFalse(isempty)
        self.assertEqual(lognot, '')
        shutil.rmtree(outdev)
        __bids_dataset__.parse_bids()


class RunSoftwareTest(unittest.TestCase):
    def setUp(self):
        self.soft = pip.PipelineSetting(__bids_dataset__, 'statistics_bdd', soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        self.results = {}
        self.results['analysis_param'] = {'Mode': 'automatic', '--participants': True, '--criteriaparticipants': ['age','sex']}
        self.results['input_param'] = {'Input_': {}}
        self.results['subject_selected'] = ['01', '02', '03']
        filename = os.path.join(__main_dir__, 'Test_BM_BP', 'all_data_orig', 'TestParsing', 'parsing_export_dataset.json')
        with open(filename, 'r') as file:
            self.correct_parsing = json.load(file)

    def test_run_analysis(self):
        log_analysis, output_name, file_to_write = self.soft.set_everything_for_analysis(self.results)
        self.assertIn(' has been analyzed with no error\n', log_analysis)
        shutil.rmtree(os.path.join(__bids_dir__, 'derivatives', output_name))

    def test_export_data(self):
        outdev = os.path.join(__main_dir__, 'testexport')
        os.makedirs(outdev, exist_ok=True)
        if os.path.exists(outdev):
            shutil.rmtree(outdev)
        results = {'0_exp':{}}
        results['0_exp']['analysis_param'] = {'output_directory': outdev, 'select_session': ['all'], 'select_modality': ['all'], 'anonymise': 'None', 'derivatives': ['Delphos', 'gardel'], 'defaceanat': ''}
        results['0_exp']['subject_selected'] = ['01', '02']
        exp.export_data(__bids_dataset__, results)
        new_bids = bids.BidsDataset(outdev)
        self.assertEqual(new_bids, self.correct_parsing, 'The parsing is different')
        shutil.rmtree(outdev)


def suite_init():
    suite = unittest.TestSuite()
    #Test the def to create the gui to select the parameters
    # suite.addTest(PipelineTest('test_init'))
    suite.addTest(PipelineTest('test_read_json'))
    suite.addTest(PipelineTest('test_get_arguments'))
    #test the parameter selected
    suite.addTest(ParameterTest('test_multiple_input_output'))
    suite.addTest(ParameterTest('test_bids_directory_input'))
    suite.addTest(ParameterTest('test_input_directory'))
    suite.addTest(ParameterTest('test_infile_outdir'))
    suite.addTest(ParameterTest('test_instance_parameter'))
    suite.addTest(ParameterTest('test_validity_input_parameters'))
    suite.addTest(ParameterTest('test_multiple_input'))
    suite.addTest(ParameterTest('test_multiple_input_dev'))
    ##test the derivatives folder creation
    suite.addTest(DerivativesTest('test_create_output_directory'))
    suite.addTest(DerivativesTest('test_update_dataset_after_analysis_input_files'))
    suite.addTest(DerivativesTest('test_empty_dirs'))
    # Test run analysis
    suite.addTest(RunSoftwareTest('test_run_analysis'))
    # suite.addTest(RunSoftwareTest('test_export_data'))
    return suite


def list_for_str_format(order, idx):
    use_list = []
    for elt in order:
        if isinstance(elt, list):
            if isinstance(elt[idx], list):
                use_list.append('"'+', '.join(elt[idx])+'"')
            else:
                use_list.append(elt[idx])
        else:
            use_list.append(elt)
    return use_list


if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True, verbosity=3)
    curr_suite = suite_init()
    results = runner.run(curr_suite)
    print()
