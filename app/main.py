import os
import nibabel as nib
import pandas as pd
import ants

# https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/public/

out_dir = '/flywheel/v0/output'

def calculateHeadCircumference(input, subject_label, session_label, patientSex, age):
    #Define some executables and the template paths
    under2_template = '/flywheel/v0/app/templates/under2.nii.gz'
    under2_outline  = '/flywheel/v0/app/templates/under2Outline.nii.gz'

    over2_template  = '/flywheel/v0/app/templates/over2.nii.gz'
    over2_outline   = '/flywheel/v0/app/templates/over2Outline.nii.gz'
                                
    template = ""
    outline  = ""

    if age is None:
        print("WARNING!!! Age is not available. Using the under 2 template.")
        template = under2_template
        outline  = under2_outline
    elif (age <= 720):
        template = under2_template
        outline  = under2_outline
    else:
        template = over2_template
        outline  = over2_outline

    print("Using template: ", template)
    print("Using outline: ", outline)
    print("Input image: ", input)

    #Now register the template to the input image
    mytx = ants.registration(fixed = ants.image_read(input),
                            moving = ants.image_read(template),
                            type_of_transform = 'SyN')
                            
    warped_outline = ants.apply_transforms(fixed=ants.image_read(input),
                                        moving=ants.image_read(outline),
                                        transformlist=mytx['fwdtransforms'],
                                        interpolator = 'genericLabel')

    warped_outline.to_file(os.path.join(out_dir, "head_contour.nii.gz"))

    output_contour = os.path.join(out_dir, "head_contour.nii.gz")
    #Now calculate the head circumference by simply summing the values
    contour_img  = nib.load(output_contour)
    contour_data = contour_img.get_fdata().flatten()
    voxel_size   = contour_img.header.get_zooms()[0]

    hc = 0.00

    for vox in contour_data: #.shape[0]:
        if vox > 0.00:
            hc += (vox*voxel_size)
            
    hc_corrected = (hc + 910.69)/2.6458 #Correction based on previous modeling
   

    # hc, hc_corrected

    # Create DataFrame  
    data = [{'subject': subject_label, 'session': session_label, 'age': age, 'sex': patientSex, 'hc': hc, 'hc_corrected': hc_corrected, 'hc_units': 'mm'}]  
    df = pd.DataFrame(data)
    df.to_csv(index=False, path_or_buf = out_dir + '/' + subject_label + '-hc.csv')

    # Return 0 if successful
    e_code = 0
    return e_code