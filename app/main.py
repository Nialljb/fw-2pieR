import os
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from skimage import measure
from scipy.fft import fft, ifft
import pandas as pd
from nibabel.affines import apply_affine
import ants
 
def calculateHeadCircumference(input, subject_label, session_label, patientSex, age):
    """
    Calculate head circumference from NIfTI files in a specified directory.
    This function processes NIfTI files, registers them to a template, extracts contours,
    and estimates head circumference in centimeters.
    Returns:
        int: Exit code (0 for success).
        str: Path to the output CSV file with head circumference estimates.
    Raises:
        Exception: If any error occurs during processing.
    """

    # # === Paths ===
    # input_dir = 'native_files'
    work_dir = '/flywheel/v0/work'
    out_dir = '/flywheel/v0/output'

    os.makedirs(work_dir, exist_ok=True)
    
    # === Use fixed template and slice index (12M) ===
    template_path = '/flywheel/v0/app/templates/template_12M.nii.gz'
    z_index = 44
    
    all_results = []
        
    try:
        template_img = nib.load(template_path)
        data = template_img.get_fdata()
        affine = template_img.affine

        binary_slice = data[:, :, z_index]
        contours = measure.find_contours(binary_slice, level=0.5)
        if not contours:
            raise ValueError(f"No contours found in slice {z_index} of template")

        contour = max(contours, key=len)
        y, x = contour[:, 0], contour[:, 1]
        z = x + 1j * y
        Z = fft(z)
        N = 20
        Z_trunc = np.zeros_like(Z)
        Z_trunc[:N] = Z[:N]
        Z_trunc[-N+1:] = Z[-N+1:]
        z_smooth = ifft(Z_trunc)
        x_smooth, y_smooth = z_smooth.real, z_smooth.imag
        voxel_coords = np.column_stack((x_smooth, y_smooth, np.full_like(x_smooth, z_index)))
        mm_coords = apply_affine(affine, voxel_coords)
        mm_df = pd.DataFrame(mm_coords, columns=['x', 'y', 'z'])

        native = ants.image_read(input)
        template = ants.image_read(template_path)

        outprefix = os.path.join(os.path.basename(input).replace(".nii.gz", "_"))
        reg = ants.registration(fixed=template, moving=native, type_of_transform='SyN', outprefix=outprefix)

        reg_native = reg['warpedmovout']
        output_fname_native = os.path.basename(input).replace('.nii.gz', '_registered.nii.gz')
        reg_native.to_filename(os.path.join(work_dir, output_fname_native))

        template_in_native = ants.apply_transforms(
            fixed=native, moving=template, transformlist=reg['invtransforms']
        )
        output_fname_template = os.path.basename(input).replace('.nii.gz', '_template_to_native.nii.gz')
        template_in_native.to_filename(os.path.join(work_dir, output_fname_template))

        transformed_df = ants.apply_transforms_to_points(
            dim=3, points=mm_df, transformlist=reg['fwdtransforms']
        )

        coords_native = transformed_df[['x', 'y']].to_numpy()
        coords_native_closed = np.vstack([coords_native, coords_native[0]])
        dists_native = np.sqrt(np.sum(np.diff(coords_native_closed, axis=0) ** 2, axis=1))
        circumference_mm_native = dists_native.sum()
        circumference_cm_native = round(circumference_mm_native / 10.0, 2)

        # === plotting ===
        # fig, ax = plt.subplots(figsize=(6, 6))
        # ax.imshow(binary_slice, cmap='gray', origin='lower')
        # ax.plot(contour[:, 1], contour[:, 0], label='Original', color='red', alpha=0.6)
        # ax.plot(x_smooth, y_smooth, label='Smoothed (FFT)', color='cyan')
        # ax.set_title(f"Z-index: {z_index} | Circumference: {circumference_cm_native} cm")
        # ax.legend()
        # ax.plot([10], [10], 'go')  # Should appear bottom-left if orientation is correct
        # plt.axis('off')
        # plt.savefig(os.path.join(work_dir, 'circumference_plot.png'), bbox_inches='tight')


        # Warp native into template space (so everything aligns)
        native_in_template = ants.apply_transforms(
            fixed=template,
            moving=native,
            transformlist=reg['fwdtransforms']
        )

        # Save or get the array
        native_resampled = native_in_template.numpy()
        slice_index = z_index  # same slice as used for contour extraction
        resampled_slice = native_resampled[:, :, slice_index]

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.imshow(resampled_slice, cmap='gray', origin='lower')
        ax.plot(x_smooth, y_smooth, label='Smoothed Contour (FFT)', color='cyan')
        ax.set_title(f"Z-index: {z_index} | Circumference: {circumference_cm_native} cm")
        ax.legend()
        plt.axis('off')
        plt.savefig(os.path.join(out_dir, 'contour_on_template_space_native.png'), bbox_inches='tight')

        # === Collect results ===
        all_results.append({
            'subject': subject_label,
            'session': session_label,
            'age': age,
            'sex': patientSex,
            'mri_estimated_hc_cm': circumference_cm_native,
        })

        print(f"✅ Estimated HC: {circumference_cm_native:.2f} cm")

    except Exception as e:
        print(f"❌ Failed to process {input}: {e}")
    
    # === Save results ===
    hc_df = pd.DataFrame(all_results)
    hc_df = hc_df[hc_df['mri_estimated_hc_cm'] > 0]
    hc_df.to_csv(index=False, path_or_buf = out_dir + '/' + subject_label + '-mri_estimated_hc_cm.csv')
    print("\n✅ Saved head circumference estimates to 'head_circumference_estimates_only.csv'")

    # Return 0 if successful
    e_code = 0
    return e_code