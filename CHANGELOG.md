# Changelog
All notable changes to BIDS Manager-Pipeline will be documented in this file.

## [Unreleased]
- Export option is working, need to test more the merge option
- Make the interface dynamic
- Possibility to choose a local output in BP
- Possibility to import derivatives folder in BIDS dataset

## [v0.3.1] - 2021-04-30
### Added
- Possibility to apply the change of the name or type of the electrode on multiple files
- Extension '.mtg' and '.mrk' to be parsed in derivatives and called as input in BP
- Management of multiple access to the database
- Write the command line used for the process in derivatives/bids_pipeline/command_line

### Fixed
- Taking into account multiple session to check the integrity of electrode names

### Changed
- During parsing, anywave files are saved in a derivatives folder anywave/username
- Possibility to run analysis on multiple combination of inputs

## [v0.3.0] - 2021-03-10
### Added
- Deface with SPM

## [v0.2.9] - 2021-02-19
### Added
- BiDS Uploader can transfer data in sFTP mode, possibility to compil only BIDS Uploader to give to other center
- Export/Merge button, it can be used to export data or merge 2 BIDS dataset

### Fixed
- While subject is removed in derivatives folder, it is also removed from the dataset_decription.json
- Once the analysis is done, the dataset_description is updated with the subject analysed and the empty folders are removed
- When no subject are selected, ask the user if he wants to do analysis on all subject
- In batch mode, can now launch the same process one after the other

## [v0.2.8] - 2020-10-14
### Added
- PET modality
- Anonymisation of EDF format
- Scrollbar in BIDS Uploader
- Tutorial video
- Possibility to take freesurfer files as input of process (BIDS Pipeline)
- Possibility to rename the variant of the derivatives folder (pipelinename-variant)
- Specificity to anywave plugin to take into account montage file in the process


### Fixed
- Issue with phantom subject (If error in subject importation, subject won't be in the parsing)
- Adapting the GUI to small monitor
- Issue while comparing the pipeline folders to find the good one to write the results
- Sort the elements from list in the requirements file


### Changed
- Arguments for boolean in json file describing the pipeline should be written as {"default":true/false, "incommandline": true/false}
=> if "incommandline":true, the parameter will be displayed in the command line like this "pipeline param true/false"
=> if "incommandline":false, the parameter will be displayed in the command line only if its value is true, else it won't be displayed like this "pipeline param" or "pipeline"