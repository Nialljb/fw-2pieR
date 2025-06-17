# 🧠 Head Circumference Estimation from MRI

## Overview

[Usage](#usage)

[FAQ](#faq)

### Summary

This gear estimates head circumference (HC) from a structural MRI by registering the image to a fixed 12-month template, extracting a 2D contour from a predefined axial slice, transforming it into native space, and calculating its circumference in centimeters. Output includes a plot for quality control and a per-subject CSV with the estimated measurement.

### Cite

**license:**  
MIT License

**url:**  
<insert repository or documentation URL here>

**cite:**  


### Classification

*Category:* analysis

*Gear Level:*

* [ ] Project  
* [ ] Subject  
* [ ] Session  
* [ ] Acquisition  
* [x] Analysis

----

### 📁 Inputs

* api-key  
  * **Name**: api-key  
  * **Type**: object  
  * **Optional**: true  
  * **Classification**: api-key  
  * **Description**: Flywheel API key.

* input  
  * **Base**: file  
  * **Description**: Input T1-weighted image (bias-corrected, skull-stripped, and isotropic resolution)  
  * **Optional**: false

### Config

_No additional configuration parameters are required._

### 📤 Outputs

* `contour_on_template_space_native.png`  
  * **Base**: file  
  * **Description**: Smoothed head contour plotted on native image resampled into template space  
  * **Optional**: false

* `<subject_label>-mri_estimated_hc_cm.csv`  
  * **Base**: file  
  * **Description**: CSV file with estimated head circumference in native space (in centimeters)  
  * **Optional**: false

#### Metadata

No metadata currently created by this gear

### Pre-requisites

- A 3D structural image (T1-weighted), already bias-corrected and skull-stripped
- Isotropic resolution is assumed (ideally 1x1x1 mm)

#### Prerequisite Gear Runs

1. **dcm2niix**  
   * Level: Any  
2. **file-metadata-importer**  
   * Level: Any  
3. **file-classifier**  
   * Level: Any  
4. **MRR (or equivalent reconstruction gear)**  


## Usage

This gear is run at the `Analysis` level using a single structural input. It registers the input image to a reference 12-month pediatric brain template using ANTs `SyN`, extracts a binary contour from a predefined axial slice, and calculates the smoothed head circumference in the subject’s native space.

### Description

1. Load the 12-month template and extract a fixed axial slice (z=44).
2. Extract the largest binary contour using `skimage`.
3. Smooth the contour using a low-pass Fourier transform.
4. Register the native image to the template using ANTs `SyN` registration.
5. Transform the smoothed contour to native space.
6. Calculate circumference by summing Euclidean distances between native-space points.
7. Save QC plot and measurement output.

#### File Specifications

* Input NIfTI file must be:
  - 3D structural image (T1-weighted)
  - Bias-corrected
  - Skull-stripped
  - Isotropic resolution
  - `.nii.gz` format

### Workflow

```mermaid
  graph LR;
    A[T1w (preprocessed)]:::input --> REG;
    REG((ANTs Registration)):::gear --> HC;
    HC((Head Circumference Estimation)):::gear --> CSV;
    HC --> IMG;

    classDef input fill:#7a9,color:#fff
    classDef gear fill:#659,color:#fff
    classDef output fill:#57d,color:#fff

    CSV[HC CSV Output]:::output
    IMG[Contour QC Plot]:::output
