import unittest
import os
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
        soft_analyse = pip.PipelineSetting(__bids_dataset__, self.software_name, soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        param_vars, in_vars, error_log = soft_analyse.create_parameter_to_inform()
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
                in_tmp[elt]['modality'] = dict()
                in_tmp[elt]['modality']['attribut'] = 'Label'
                in_tmp[elt]['modality']['value'] = "Ieeg"
            elif cnt == 3:
                in_tmp[elt] = dict()
                in_tmp[elt]['modality'] = dict()
                in_tmp[elt]['modality']['attribut'] = 'Label'
                in_tmp[elt]['modality']['value'] = "Anat"
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
            elif cnt == 7:
                param_tmp[elt] = dict()
                param_tmp[elt]['attribut'] = 'Label'
                param_tmp[elt]['value'] = 'acq'
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
        self.results['subject_selected'] = {'sub': ['01', '02', '03']}
        self.results['analysis_param'] = {'Mode': 'automatic', '--duration': '10sec', '--criteria': ['Stim', 'stim'], '--criteriadata': 'ses', '--task': 'acq'}
        self.results['input_param'] = {}
        self.results['input_param']['--input_ieeg'] = {'modality': 'Ieeg', 'ses': '01', 'run': '01'}
        self.results['input_param']['--input_anat'] = {'modality': 'T1w', 'acq': ['preimp']}
        self.output_dir = os.path.join(__bids_dir__, 'derivatives', 'testing')

    def test_multiple_input_output(self):
        analyse = pip.PipelineSetting(__bids_dataset__, 'testing', soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        analyse['Parameters'].update_values(self.results['analysis_param'])
        subjects = pip.SubjectToAnalyse(self.results['subject_selected']['sub'], input_dict=self.results['input_param'])
        subjects_results = {'sub': ['01', '02', '03'], '--input_ieeg': {'modality': ['Ieeg'], 'ses': ['01'], 'run': ['01']}, '--input_anat': {'modality': ['T1w'], 'acq': ['preimp']}}
        self.assertEqual(subjects, subjects_results)
        cmd_arg, cmd_line, order, input_dict, output_dict = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        self.assertIsInstance(cmd_arg, pip.Parameters)
        self.assertIsNotNone(order)
        taille, idx_in, in_out = input_dict.get_input_values(subjects, order)
        output_dict.get_output_values(in_out, taille, order, self.output_dir, idx_in)
        for sub in in_out:
            in_out_res = [['D:\\Data\\testing\\test_dataset\\sub-{0}\\ses-01\\ieeg\\sub-{0}_ses-01_task-ccep_run-01_ieeg.vhdr'.format(sub)], ['D:\\Data\\testing\\test_dataset\\sub-{0}\\ses-01\\anat\\sub-{0}_ses-01_acq-preimp_T1w.nii'.format(sub)], [['D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-{0}\\ses-01\\ieeg\\sub-{0}_ses-01_task-ccep_run-01_testing.mat'.format(sub), 'D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-{0}\\ses-01\\ieeg\\sub-{0}_ses-01_task-ccep_run-01_testing.tsv'.format(sub)]]]
            self.assertEqual(in_out[sub], in_out_res)

    def test_bids_directory_input(self):
        self.results['input_param'] = {}
        self.results['input_param']['--input_dir'] = {'modality': 'Ieeg', 'ses': '01', 'run': '01'}
        analyse = pip.PipelineSetting(__bids_dataset__, 'testing_input_dir', soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        analyse['Parameters'].update_values(self.results['analysis_param'])
        subjects = pip.SubjectToAnalyse(self.results['subject_selected']['sub'], input_dict=self.results['input_param'])
        cmd_arg, cmd_line, order, input_dict, output_dict = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        self.assertIsInstance(cmd_arg, pip.Parameters)
        self.assertFalse(order)

    def test_input_directory(self):
        self.results['input_param'] = {}
        self.results['input_param']['--input_dir'] = {'modality': 'Ieeg', 'ses': '01', 'run': '01'}
        analyse = pip.PipelineSetting(__bids_dataset__, 'testing_input_directory', soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        analyse['Parameters'].update_values(self.results['analysis_param'])
        subjects = pip.SubjectToAnalyse(self.results['subject_selected']['sub'], input_dict=self.results['input_param'])
        cmd_arg, cmd_line, order, input_dict, output_dict = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        self.assertIsInstance(cmd_arg, pip.Parameters)
        self.assertIsNotNone(order)
        taille, idx_in, in_out = input_dict.get_input_values(subjects, order)
        output_dict.get_output_values(in_out, taille, order, self.output_dir, idx_in)
        for sub in in_out:
            in_out_res = [['D:\\Data\\testing\\test_dataset\\sub-{0}\\ses-01\\ieeg'.format(sub)], [['D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-{0}\\ses-01\\ieeg'.format(sub)]]]
            self.assertEqual(in_out[sub], in_out_res)
        self.results['input_param'] = {}
        self.results['input_param']['--input_dir'] = {'modality': 'T1w', 'acq': ['preimp']}
        subjects_anat = pip.SubjectToAnalyse(self.results['subject_selected']['sub'], input_dict=self.results['input_param'])
        taille, idx_in, in_out_anat = input_dict.get_input_values(subjects_anat, order)
        output_dict.get_output_values(in_out_anat, taille, order, self.output_dir, idx_in)
        for sub in in_out_anat:
            in_out_res = [['D:\\Data\\testing\\test_dataset\\sub-{0}\\anat'.format(sub)], [
                ['D:\\Data\\testing\\test_dataset\\derivatives\\testing\\sub-{0}\\anat'.format(sub)]]]
            self.assertEqual(in_out_anat[sub], in_out_res)

    def test_infile_outdir(self):
        self.results['input_param'] = {}
        self.results['input_param']['--input_ieeg'] = {'modality': 'Ieeg', 'ses': '01', 'run': '01'}
        analyse = pip.PipelineSetting(__bids_dataset__, 'testing_infile_outdir', soft_path=os.path.join(__main_dir__, 'software_pipeline'))
        analyse['Parameters'].update_values(self.results['analysis_param'])
        subjects = pip.SubjectToAnalyse(self.results['subject_selected']['sub'], input_dict=self.results['input_param'])
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
        self.results['input_param']['--input_ieeg'] = {'modality': 'Ieeg', 'ses': '01'}
        subjects = pip.SubjectToAnalyse(self.results['subject_selected']['sub'], input_dict=self.results['input_param'])
        #assert intermediate instance
        analyse = pip.PipelineSetting(__bids_dataset__, 'h2')
        cmd_arg, cmd_line, order, input_dict, output_dict = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        cmd_tmp = 'C:/anywave_september/AnyWave.exe --run   "D:\\Data\\testing\\test_dataset\\derivatives\\testing\\h2_parameters.json" --input_file {0} --output_dir {1} '
        self.assertIsInstance(cmd_arg, pip.AnyWave)
        self.assertEqual(cmd_line, cmd_tmp)

        analyse = pip.PipelineSetting(__bids_dataset__, 'example')
        cmd_arg, cmd_line, order, input_dict, output_dict = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        cmd_tmp = 'docker run -i --rm -v D:\\Data\\testing\\test_dataset:/bids_dataset:ro -v D:\\Data\\testing\\test_dataset\\derivatives\\testing:/outputs bids/example /bids_dataset /outputs --participant_label [01 02 03] '
        self.assertIsInstance(cmd_arg, pip.Docker)
        self.assertEqual(cmd_line, cmd_tmp)

        analyse = pip.PipelineSetting(__bids_dataset__, 'averaging_EP')
        cmd_arg, cmd_line, order, input_dict, output_dict = analyse.create_command_to_run_analysis(self.output_dir, subjects)
        cmd_tmp = "matlab -wait -nosplash -nodesktop -r \"cd('D:\\Matlab'); averaging_EP('{0}', '{1}'); exit\""
        self.assertIsInstance(cmd_arg, pip.Matlab)
        self.assertEqual(cmd_line, cmd_tmp)


class DerivativesTest(unittest.TestCase):

    def test_create_output_directory(self):
        dev = pip.DerivativesSetting(__bids_dataset__['Derivatives'][0])
        output_directory, output_name = dev.create_pipeline_directory('testing_input_directory', {}, {})
        self.assertEqual(output_directory, 'D:\\Data\\testing\\test_dataset\\derivatives\\testing_input_directory')
        output_directory, output_name = dev.create_pipeline_directory('testing', {}, {})
        self.assertEqual(output_directory, 'D:\\Data\\testing\\test_dataset\\derivatives\\testing-v1')


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
    #suite.addTest(DerivativesTest('test_create_output_directory'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True, verbosity=3)
    curr_suite = suite_init()
    results = runner.run(curr_suite)
    print()
