import unittest
import os
import shutil
import datetime
import pipeline_class as pip
import ins_bids_class as bids

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
            param_vars = pip.ParameterInterface(__bids_dataset__, soft['Parameters'])
            in_vars = {}
            for inp in soft['Parameters']['Input']:
                in_vars['Input_'+inp['tag']] = pip.InputParameterInterface(__bids_dataset__, inp)
        soft_analyse = pip.PipelineSetting(__bids_dataset__, self.software_name, soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        param_vars = pip.ParameterInterface(__bids_dataset__, soft_analyse['Parameters'])
        in_vars = {}
        for inp in soft_analyse['Parameters']['Input']:
            in_vars['Input_' + inp['tag']] = pip.InputParameterInterface(__bids_dataset__, inp)
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
                in_tmp[elt]['task'] = {'value': ['ccep'], 'attribut': 'Label'}
            elif cnt == 3:
                in_tmp[elt] = dict()
                in_tmp[elt]['modality'] = {'value': 'Anat', 'attribut': 'Label'}
                in_tmp[elt]['acq'] = {'value': ['postimp', 'preimp'], 'attribut': 'Variable'}
                in_tmp[elt]['ses'] = {'value': ['01'], 'attribut': 'Label'}
                in_tmp[elt]['mod'] = {'value': ['CT', 'T1w'], 'attribut': 'Variable'}
            elif cnt == 4:
                param_tmp[elt] = dict()
                param_tmp[elt]['attribut'] = 'StringVar'
                param_tmp[elt]['value'] = '10sec'
                param_tmp[elt]['unit'] = 'sec'
            elif cnt == 5:
                param_tmp[elt] = dict()
                param_tmp[elt]['attribut'] = 'Variable'
                param_tmp[elt]['value'] = ['Begin', 'Post', 'Pre', 'Stim']
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

    def test_run_analysis(self):
        pass


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
        analyse['Parameters'].update_values(self.results['analysis_param'])
        subjects = pip.SubjectToAnalyse(self.results['subject_selected'], input_dict=self.results['input_param'])
        subjects_results = {'sub': ['01', '02', '03'], 'Input_--input_ieeg': {'modality': ['Ieeg'], 'ses': ['01'], 'run':
            ['01']}, 'Input_--input_anat': {'modality': ['Anat'], 'acq': ['preimp'], 'mod': ['T1w']}}
        self.assertEqual(subjects, subjects_results)
        cmd_arg, cmd_line, order, input_dict, output_dict = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        cmd_tmp = 'D:/Data/testing --input_ieeg {0} --input_anat {1} --output_file {2} --duration 20 --criteria "Stim, stim" --criteriadata ses --task preimp'
        self.assertIsInstance(cmd_arg, pip.Parameters)
        self.assertEqual(cmd_line, cmd_tmp)
        self.assertIsNotNone(order)
        taille, idx_in, in_out = input_dict.get_input_values(subjects, order)
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
        analyse['Parameters'].update_values(self.results['analysis_param'])
        subjects = pip.SubjectToAnalyse(self.results['subject_selected'], input_dict=self.results['input_param'])
        cmd_arg, cmd_line, order, input_dict, output_dict = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        self.assertIsInstance(cmd_arg, pip.Parameters)
        self.assertFalse(order)

    def test_input_directory(self):
        self.results['input_param'] = {}
        self.results['input_param']['Input_--input_dir'] = {'modality': 'Ieeg', 'ses': '01', 'run': '01'}
        analyse = pip.PipelineSetting(__bids_dataset__, 'testing_input_directory', soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        analyse['Parameters'].update_values(self.results['analysis_param'])
        subjects = pip.SubjectToAnalyse(self.results['subject_selected'], input_dict=self.results['input_param'])
        cmd_arg, cmd_line, order, input_dict, output_dict = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        self.assertIsInstance(cmd_arg, pip.Parameters)
        self.assertIsNotNone(order)
        taille, idx_in, in_out = input_dict.get_input_values(subjects, order)
        output_dict.get_output_values(in_out, taille, order, self.output_dir, idx_in)
        for sub in in_out:
            in_out_res = [['D:\\Data\\testing\\test_dataset\\sub-{0}\\ses-01\\ieeg'.format(sub)], [['D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-{0}\\ses-01\\ieeg'.format(sub)]]]
            self.assertEqual(in_out[sub], in_out_res)
        self.results['input_param'] = {}
        self.results['input_param']['Input_--input_dir'] = {'modality': 'Anat', 'acq': ['preimp'], 'mod': ['T1w']}
        subjects_anat = pip.SubjectToAnalyse(self.results['subject_selected'], input_dict=self.results['input_param'])
        taille, idx_in, in_out_anat = input_dict.get_input_values(subjects_anat, order)
        output_dict.get_output_values(in_out_anat, taille, order, self.output_dir, idx_in)
        for sub in in_out_anat:
            in_out_res = [['D:\\Data\\testing\\test_dataset\\sub-{0}\\anat'.format(sub)], [
                ['D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-{0}\\anat'.format(sub)]]]
            self.assertEqual(in_out_anat[sub], in_out_res)

    def test_infile_outdir(self):
        self.results['input_param'] = {}
        self.results['input_param']['Input_--input_ieeg'] = {'modality': 'Ieeg', 'ses': '01', 'run': '01'}
        analyse = pip.PipelineSetting(__bids_dataset__, 'testing_infile_outdir', soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        analyse['Parameters'].update_values(self.results['analysis_param'])
        subjects = pip.SubjectToAnalyse(self.results['subject_selected'], input_dict=self.results['input_param'])
        cmd_arg, cmd_line, order, input_dict, output_dict = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        self.assertIsInstance(cmd_arg, pip.Parameters)
        self.assertIsNotNone(order)
        taille, idx_in, in_out = input_dict.get_input_values(subjects, order)
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
        cmd_arg, cmd_line, order, input_dict, output_dict = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        cmd_tmp = 'C:/anywave_december_2019/AnyWave.exe --run D:\\Data\\testing\\test_dataset\\derivatives\\testing\\h2_parameters.json --input_file {0} --output_dir {1}'
        self.assertIsInstance(cmd_arg, pip.AnyWave)
        self.assertEqual(cmd_line, cmd_tmp)

        analyse = pip.PipelineSetting(__bids_dataset__, 'example')
        cmd_arg, cmd_line, order, input_dict, output_dict = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        cmd_tmp = 'docker run -i --rm -v D:\\Data\\testing\\test_dataset:/bids_dataset:ro -v D:\\Data\\testing\\test_dataset\\derivatives\\testing:/outputs bids/example /bids_dataset /outputs --participant_label [01 02 03]'
        self.assertIsInstance(cmd_arg, pip.Docker)
        self.assertEqual(cmd_line, cmd_tmp)

        analyse = pip.PipelineSetting(__bids_dataset__, 'averaging_EP')
        cmd_arg, cmd_line, order, input_dict, output_dict = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        cmd_tmp = "matlab -wait -nosplash -nodesktop -r \"cd('D:\\Matlab'); averaging_EP('{0}', '{1}'); exit\""
        self.assertIsInstance(cmd_arg, pip.Matlab)
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
        __bids_dataset__.parse_bids()
        dev = pip.DerivativesSetting(__bids_dataset__['Derivatives'][0])
        output_directory, output_name, dataset_desc = dev.create_pipeline_directory('testing_input_directory', self.results['analysis_param'], self.subject)
        self.assertEqual(output_directory, 'D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory')
        dev.pipelines.append(bids.Pipeline())
        dev.pipelines[-1]['name'] = 'testing_input_directory'
        dev.pipelines[-1]['DatasetDescJSON'] = dataset_desc
        #Add subject with same parameter
        new_subject = pip.SubjectToAnalyse(['03'], input_dict=self.results['input_param'])
        output_directory, output_name, dataset_desc = dev.create_pipeline_directory('testing_input_directory', self.results['analysis_param'], new_subject)
        self.assertEqual(output_directory, 'D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory')
        sub_in = dataset_desc['SourceDataset']['sub']
        sub_in.sort()
        self.assertEqual(sub_in, ['01', '02', '03'])
        #Create new directory
        output_directory, output_name, dataset_desc = dev.create_pipeline_directory('testing_input_directory',
                                                                                    self.results['analysis_param'],
                                                                                    self.subject)
        self.assertEqual(output_directory, 'D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory-v2')


class RunSoftwareTest(unittest.TestCase):
    def setUp(self):
        self.soft = pip.PipelineSetting(__bids_dataset__, 'statistics_bdd', soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        self.results = {}
        self.results['analysis_param'] = {'Mode': 'automatic', '--participants': True, '--criteriaparticipants': ['age','sex']}
        self.results['input_param'] = {'Input_': {}}
        self.results['subject_selected'] = ['01', '02', '03']

    def test_run_analysis(self):
        log_analysis, output_name = self.soft.set_everything_for_analysis(self.results)
        self.assertIn(' has been analyzed with no error\n', log_analysis)


def suite_init():
    suite = unittest.TestSuite()
    #Test the def to create the gui to select the parameters
    suite.addTest(PipelineTest('test_init'))
    suite.addTest(PipelineTest('test_get_arguments'))
    #test the parameter selected
    suite.addTest(ParameterTest('test_multiple_input_output'))
    suite.addTest(ParameterTest('test_bids_directory_input'))
    suite.addTest(ParameterTest('test_input_directory'))
    suite.addTest(ParameterTest('test_infile_outdir'))
    suite.addTest(ParameterTest('test_instance_parameter'))
    suite.addTest(ParameterTest('test_validity_input_parameters'))
    #test the derivatives folder creation
    suite.addTest(DerivativesTest('test_create_output_directory'))
    #Test run analysis
    suite.addTest(RunSoftwareTest('test_run_analysis'))
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
