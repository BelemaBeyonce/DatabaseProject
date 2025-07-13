from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import UploadLAS, Wells, Area, Curve, CurveValue
from .forms import UploadLASForm
from .load_las import parse_las_file
import os

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


def uploaded_files_table(request):
    uploaded_files = UploadLAS.objects.all().order_by('-uploaded_at')
    return render(request, 'wells/uploaded_files.html', {'uploaded_files': uploaded_files})


@require_POST
def delete_file(request, file_id):
    file = get_object_or_404(UploadLAS, id=file_id)
    file.files.delete()
    file.delete()
    return redirect('uploaded_files_table')
