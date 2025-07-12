from django.shortcuts import render,redirect #displaying html pages and redirecting to other pages.
from .models import UploadLAS #importing the UploadLAS model to handle file uploads
from .forms import UploadLASForm #importing the UploadLASForm to handle file uploads    
from .load_las import parse_las_file #importing the parse_las_file function to handle LAS file parsing. This already exists in the project.
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
import os
from django.contrib import messages
from .models import Wells  # Importing the Wells model to get well information



def upload_las_file(request):
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        well_name = request.POST.get('well_name')

        if not files:
            messages.error(request, "No files were uploaded.")
            return redirect('upload_las_file')

        success_count = 0  # Track how many files were processed

        for file in files:
            try:
                # Save file to database first
                uploaded_file = UploadLAS.objects.create(files=file)

                # Parse the LAS file
                parsed_info = parse_las_file(uploaded_file.files.path, area_name='User Upload')

                uwi = parsed_info.get('uwi')
                location = parsed_info.get('location')
                operator = parsed_info.get('operator')
                field = parsed_info.get('field')
                state = parsed_info.get('state')

                if not uwi:
                    print(f"Skipping {file.name}: UWI not found in LAS.")
                    uploaded_file.delete()
                    continue

                # Get or create well — even if UWI exists, keep adding files
                well, created = Wells.objects.get_or_create(
                    uwi=uwi,
                    defaults={
                        'well_name': well_name,
                        'location': location,
                        'operator': operator,
                        'field': field,
                        'state': state
                    }
                )

                # If well already exists but user gave a different name, we can log it or ignore
                if not created and well.well_name != well_name:
                    print(f"Note: UWI {uwi} exists, ignoring entered well name '{well_name}'")

                uploaded_file.well = well
                uploaded_file.save()
                success_count += 1

            except Exception as e:
                print(f"Error processing {file.name}: {e}")
                if uploaded_file and uploaded_file.pk:
                    uploaded_file.delete()

        if success_count > 0:
            messages.success(request, f"Successfully uploaded {success_count} LAS file(s).")
        else:
            messages.error(request, "No valid LAS files were uploaded.")

        return redirect('upload_las_file')  # Redirects to the same page with message

    return render(request, 'wells/upload_las.html', {'form': UploadLASForm()})



def upload_success(request):
    return render(request, 'wells/upload_success.html')

def uploaded_files_table(request):
    uploaded_files = UploadLAS.objects.all().order_by('-uploaded_at')
    return render(request, 'wells/uploaded_files.html', {'files': uploaded_files})



@require_POST
def delete_file(request, file_id):
    file = get_object_or_404(UploadLAS, id=file_id)
    file.files.delete()  # Delete the file from disk
    file.delete()        # Delete the database entry
    return redirect('uploaded_files_table')


# Create your views here.
