from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import UploadLAS, Wells, Area, Curve, CurveValue
from .forms import UploadLASForm
from .load_las import parse_las_file
import os
from .models import DeviationSurvey, Checkshot, WellHeader
import csv

def upload_las_file(request):
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        well_name_input = request.POST.get('well_name')

        if not files:
            messages.error(request, "No files were uploaded.")
            return redirect('upload_las_file')

        for file in files:
            try:
                uploaded_file = UploadLAS.objects.create(files=file)

                parsed_info = parse_las_file(uploaded_file.files.path, area_name='User Upload')
                if not parsed_info:
                    print(f"ERROR: Could not parse {file.name}.")
                    uploaded_file.delete()
                    continue

                uwi = parsed_info.get('uwi')
                location = parsed_info.get('location') or 'Unknown'
                operator = parsed_info.get('operator') or 'Unknown'
                field = parsed_info.get('field') or 'Unknown'
                state = parsed_info.get('state') or 'Unknown'

                if not uwi:
                    print(f"Skipping {file.name}: UWI is missing in LAS file.")
                    uploaded_file.delete()
                    continue

                area_name = parsed_info.get('area_name', 'User Upload')
                area, created = Area.objects.get_or_create(area_name=area_name)

                well, created = Wells.objects.get_or_create(
                    uwi=uwi,
                    defaults={
                        'well_name': well_name_input,
                        'location': location,
                        'operator': operator,
                        'field': field,
                        'state': state,
                        'area': area,
                        
                    }
                )

                # Second parse call was redundant and removed

                if not created and well_name_input and well.well_name != well_name_input:
                    well.well_name = well_name_input
                    well.save()

                uploaded_file.well = well
                uploaded_file.save()

            except Exception as e:
                print(f"ERROR processing {file.name}: {e}")
                if 'uploaded_file' in locals() and uploaded_file.pk:
                    uploaded_file.delete()
                continue

        messages.success(request, "Upload complete. Valid files were saved.")
        return redirect('upload_success')

    return render(request, 'wells/upload_las.html', {'form': UploadLASForm()})



def upload_success(request):
    return render(request, 'wells/upload_success.html', {'message': "Files uploaded successfully."})
    uploaded_devs = DeviationSurvey.objects.select_related('well').order_by('-id')[:100]  # latest 100 records
    return render(request, 'wells/upload_success.html', {'uploaded_devs': uploaded_devs})



def uploaded_files_table(request):
    uploaded_files = UploadLAS.objects.all().order_by('-uploaded_at')
    return render(request, 'wells/uploaded_files.html', {'uploaded_files': uploaded_files})


@require_POST
def delete_file(request, file_id):
    file = get_object_or_404(UploadLAS, id=file_id)
    file.files.delete()
    file.delete()
    return redirect('uploaded_files_table')


def upload_deviation_file(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            messages.error(request, "No file was uploaded.")
            return redirect('upload_deviation_file')

        print(f"File uploaded: {file.name}") # Debug: Confirm file received

        decoded_file = file.read().decode('utf-8').splitlines()

        current_well = None
        rows_processed = 0
        rows_skipped_header = 0
        rows_skipped_metadata = 0
        rows_skipped_invalid_len = 0
        wells_not_found_count = 0
        dev_survey_created_count = 0

        # Iterate through lines directly and split by whitespace
        for i, line in enumerate(decoded_file):
            # Clean the line and split by any whitespace
            row = line.strip().split()
            print(f"--- Processing Line {i+1}: Original='{line.strip()}', Parsed Row={row}") # Debug: See raw row and parsed list

            if not row: # Check if the row is empty after stripping and splitting
                print(f"Skipping empty line: '{line.strip()}'")
                rows_skipped_invalid_len += 1
                continue

            # Detect header row (e.g., 'MD', 'INC', 'AZI' or 'WELL_NAME', 'MD', 'INC', 'AZI')
            # Use .upper() for case-insensitivity
            if 'MD' in [cell.upper() for cell in row] and 'INC' in [cell.upper() for cell in row]:
                print(f"Skipping potential header row: {row}")
                rows_skipped_header += 1
                continue

            # Detect format 1: Well name and KB on the first line (e.g., "TOMBOY-6		KB=34.399931")
            # This line is usually followed by a header and then data.
            # We need to capture the well name from this line if it's the first non-header line.
            if len(row) >= 1 and 'KB=' in line: # Check 'KB=' in the original line to handle it as a single string
                current_well = row[0].strip() # The first part is the well name
                print(f"Detected current_well from KB line: '{current_well}'")
                rows_skipped_metadata += 1 # Treat this as metadata for skipping
                continue

            # Removed the previous 'Detect format 2: Well name on a single line' block
            # as it was potentially redundant and could misinterpret data lines.
            # The two main formats are now handled by the KB line or by the 4-column data line.

            try:
                well_name_to_use = None
                md, inc, azi = None, None, None

                # Case A: Data lines for TOMBOY-6 format (MD, INC, AZI columns, well name from current_well)
                # These lines typically have 3 numeric values.
                if current_well and len(row) == 3:
                    well_name_to_use = current_well
                    md = float(row[0])
                    inc = float(row[1])
                    azi = float(row[2])
                    print(f"Parsed current_well data: Well='{well_name_to_use}', MD={md}, Inc={inc}, Azi={azi}")

                # Case B: Data lines for GABO-13 format (WELL_NAME, MD, INC, AZI columns)
                # These lines typically have 4 values.
                elif len(row) >= 4:
                    well_name_to_use = row[0].strip()
                    md = float(row[1])
                    inc = float(row[2])
                    azi = float(row[3])
                    print(f"Parsed 4-column data: Well='{well_name_to_use}', MD={md}, Inc={inc}, Azi={azi}")

                else:
                    print(f"Skipping row due to unexpected column count or missing current_well context: {row}")
                    rows_skipped_invalid_len += 1
                    continue

                if well_name_to_use is None:
                    print(f"Skipping row {row}: Could not determine well name for data parsing.")
                    continue

                # Find the well in the database (case-insensitive exact match)
                well = Wells.objects.filter(well_name__iexact=well_name_to_use).first()
                if not well:
                    print(f"Well '{well_name_to_use}' not found in database. Skipping row.")
                    wells_not_found_count += 1
                    continue

                # Ensure all necessary data points are present before creating the object
                if md is not None and inc is not None and azi is not None:
                    DeviationSurvey.objects.create(
                        well=well,
                        md=md,
                        incl=inc,
                        azim=azi
                    )
                    dev_survey_created_count += 1
                    print(f"Successfully created DeviationSurvey for {well.well_name} at MD {md}")
                else:
                    print(f"Skipping row {row}: Incomplete data (MD, Incl, or Azi is None after parsing).")
                    rows_skipped_invalid_len += 1

            except ValueError as ve:
                print(f"Error converting data to float in row {row}: {ve}")
                # This often happens if there are non-numeric characters in numeric columns
                continue
            except Exception as e:
                print(f"Generic error processing row {row}: {e}")
                continue

        print(f"\n--- Upload Summary ---")
        print(f"Total lines processed: {i+1}")
        print(f"Lines skipped (header): {rows_skipped_header}")
        print(f"Lines skipped (KB metadata): {rows_skipped_metadata}")
        print(f"Lines skipped (invalid length/format): {rows_skipped_invalid_len}")
        print(f"Wells not found in DB: {wells_not_found_count}")
        print(f"Deviation Surveys created: {dev_survey_created_count}")

        if dev_survey_created_count > 0:
            messages.success(request, f"Deviation file uploaded successfully. {dev_survey_created_count} surveys created.")
        else:
            messages.warning(request, "Deviation file processed, but no surveys were created. Check the file format and console logs for details.")
        return redirect('upload_success')

    wells = Wells.objects.all() # This is for displaying wells on the form, if any
    return render(request, 'wells/upload_deviation.html', {'wells': wells})

def upload_checkshot_files(request):
    if request.method == 'POST' and request.FILES.getlist('checkshot_files'):
        files = request.FILES.getlist('checkshot_files')
        for file in files:
            well_name = os.path.splitext(file.name)[0].split("_")[0].strip().upper()
            well = Wells.objects.filter(well_name__icontains=well_name).first()
            if not well:
                continue

            lines = file.read().decode('utf-8').splitlines()
            reader = csv.reader(lines)

            for row in reader:
                if len(row) < 2:
                    continue
                try:
                    depth = float(row[0])
                    time = float(row[1])
                    # save to CheckshotData or your model
                    # Example:
                    # CheckshotData.objects.create(well=well, depth=depth, time=time)
                except:
                    continue

        return redirect('upload_success')

    return render(request, 'wells/upload_checkshot.html')


    

def upload_header_files(request):
    if request.method == 'POST' and request.FILES.getlist('header_files'):
        files = request.FILES.getlist('header_files')
        for file in files:
            lines = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(lines, delimiter='\t')

            for row in reader:
                try:
                    well_name = row.get('WELL NAME') or row.get('Well Name')
                    x = float(row['X'])
                    y = float(row['Y'])
                    kb = float(row['KB'])
                    md = float(row.get('MD') or row.get('TD(MD)'))

                    Wells.objects.update_or_create(
                        well_name=well_name,
                        defaults={
                            'x': x,
                            'y': y,
                            'kb': kb,
                            'total_depth': md
                        }
                    )
                except Exception as e:
                    print(f"Header upload error: {e}")
                    continue

        return redirect('upload_success')

    return render(request, 'wells/upload_header.html')


