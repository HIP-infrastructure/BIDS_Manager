#  BIDS Manager ![BM](bids_manager.ico "BIDS_Manager")
Package to collect, organise and manage neuroscience data in Brain Imaging Data Structure (BIDS) format.

## Version
BIDS Manager v0.2.8

This version of BIDS Manager uses a version of BIDS Uploader which does not yet handle data transfer via SFTP, the SFTP transfer will me publicly available soon.

## How to cite
* Roehri, N., Medina-Villalon, S., Jegou, A., Colombet, B., Giusiano, B., Ponz, A., & Bénar, C. G., Transfer, collection and organisation of electrophysiological and imaging data for multicenter studies. (submitted)

## Features
* Collect data in differents format:
  * DICOM
  * Nifti
  * Micromed (.trc)
  * Brain products (.vhdr)
  * EDF+ (.edf)
  * EEGLAB (.set)
  * 4D neuroimaging 
* Organise data in BIDS format
* Offer graphical interface to visualise/manage BIDS dataset

## Main Requirements
* Python 3.7
* AnyWave, available here: http://meg.univ-amu.fr/wiki/AnyWave
* dcm2nii or dcm2niix

## Python library required
* pydicom
* PyQt5
* bids-validator
* nibabel
* xlrd

## Authors
* Main developper: Nicolas Roehri <nicolas.roehri@etu.univ-amu.fr>
* Developpers: Samuel Medina (generic_uploader) <samuel.medinavillalon@gmail.com>, 
		      Aude Jegou <aude.jegou@univ-amu.fr>

## License
This project is licensed under the GPLv3 license.

## Comment
If you wish to compile these scripts using PyInstaller 4.0 or above, use the command below:
```
pyinstaller --onefile --icon=bids_manager.ico --hidden-import PyQt5.sip bids_manager\\bids_manager.py
```
An **example dataset** is available here: https://figshare.com/articles/Example_Dataset_for_BIDS_Manager/11687064
