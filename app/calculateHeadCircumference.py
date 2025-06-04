import string, os, sys, argparse
import nibabel as nib
import ants


#Define some executables and the template paths
under2_template = '/flywheel/v0/app/templates/under2.nii.gz'
under2_outline  = '/flywheel/v0/app/templates/under2Outline.nii.gz'

over2_template  = '/flywheel/v0/app/templates/over2.nii.gz'
over2_outline   = '/flywheel/v0/app/templates/over2Outline.nii.gz'


parser = argparse.ArgumentParser(description='Calculate Head Circumference based on Structural MRI')

parser.add_argument('--anat_t1w',
                    type=str,
                    help='Structural T1w image',
                    default=None)
                    
parser.add_argument('--age',
                    type=int,
                    help='Age of participant (days)',
                    default=None)

parser.add_argument('--out_dir',
                    type=int,
                    help='Output Directory',
                    default=None)
                    
args, unknown = parser.parse_known_args()
                            
template = ""
outline  = ""

if (args.age <= 720):
    template = under2_template
    outline  = under2_outline
else:
    template = over2_template
    outline  = over2_outline

mytx = ants.registration(fixed = ants.image_read(args.anat_t1w),
                        moving = ants.image_read(args.template),
                        type_of_transform = 'SyN')
                        
warped_outline = ants.apply_transforms(fixed=ants.image_read(args.anat_t1w),
                                    moving=ants.image_read(outline),
                                    transformlist=mytx['fwdtransforms'],
                                    interpolator = 'linear') ### Change to 'linear' if you want a continuous image

warped_outline.to_file(os.join.path(args.out_dir, "head_contour.nii.gz"))


#Now calculate the head circumference by simply summing the values
contour_img  = nib.load(output_contour)
contour_data = contour_img.get_fdata().flatten();
voxel_size   = contour_img.header.get_zooms()[0]

hc = 0.00

for vox in contour_data.shape[0]:
    if vox > 0.00:
        hc += (vox*voxel_size)
        
hc_corrected = (hc + 910.69)/2.6458 #Correction based on previous modeling

return hc, hc_corrected


	





		
		



