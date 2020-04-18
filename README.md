# BIDS Manager
Package to collect, organise and manage neuroscience data in Brain Imaging Data Structure (BIDS) format.

## Version
Bids Manager v0.2.5

## Features
* Collect data in differents format:
  * DICOM
  * Nifti
  * Micromed (.trc)
  * Brain products (.vhdr)
  * EDF+ (.edf)
  * EGI (.mff)
  * EEGLAB (.set)
  * SPM (.mat)
  * ANT EEProbe (.cnt)
  * 4D neuroimaging 
* Organise data in BIDS format
* Offer graphical interface to visualise/manage BIDS dataset

## Main Requirements
* Python 3.7
* AnyWave
* dcm2nii or dcm2niix

## Python library required
* pydicom
* PyQt5
* bids-validator

## Authors
Main developper: Nicolas Roehri <nicolas.roehri@etu.univ-amu.fr>
Developpers: Samuel Medina (generic_uploader) <samuel.medinavillalon@gmail.com>, 
			 Aude Jegou <aude.jegou@univ-amu.fr>

## License
This project is licensed under the GPLv3 license.

## Comment
If you worked with Bids Manager version 0.2.4 or previous version, you will have to do some changes if you want to use the new version (0.2.5).
For the Bids database created with previous version, you must change:
- requirements file: Change Imagery in Imaging
- Rename the parsing folder in parsing_old