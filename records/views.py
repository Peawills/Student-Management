from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.db import transaction
from .models import Student, StudentDocument
from .forms import StudentForm, StudentDocumentForm, MultipleStudentDocumentForm
import logging

logger = logging.getLogger(__name__)


def _is_staff(user):
    """Check if user is authenticated and staff"""
    return user.is_authenticated and user.is_staff

@login_required
def home(request):
    """
    Home page with overview statistics
    """
    # Get statistics
    total_students = Student.objects.count()
    male_count = Student.objects.filter(sex='Male').count()
    female_count = Student.objects.filter(sex='Female').count()
    
    # Get offense count if committee app exists
    try:
        from committee.models import StudentOffense
        offense_count = StudentOffense.objects.count()
    except:
        offense_count = 0
    
    context = {
        'total_students': total_students,
        'male_count': male_count,
        'female_count': female_count,
        'offense_count': offense_count,
    }
    
    return render(request, 'records/homepage.html', context)



@login_required
@user_passes_test(_is_staff)
def student_list(request):
    """Display paginated list of students with search and filters"""
    query = request.GET.get("q", "").strip()
    sex = request.GET.get("sex", "").strip()
    klass = request.GET.get("klass", "").strip()
    sort_by = request.GET.get("sort", "-id")  # Default to newest first

    # Base queryset with optimization
    students_qs = Student.objects.select_related().prefetch_related("documents")

    # Apply search filter
    if query:
        students_qs = students_qs.filter(
            Q(surname__icontains=query)
            | Q(other_name__icontains=query)
            | Q(admission_no__icontains=query)
            | Q(father_name__icontains=query)
            | Q(mother_name__icontains=query)
        )

    # Apply gender filter
    if sex and sex in ["Male", "Female"]:
        students_qs = students_qs.filter(sex=sex)

    # Apply class filter
    if klass:
        students_qs = students_qs.filter(class_at_present__icontains=klass)

    # Apply sorting
    allowed_sorts = [
        "-id",
        "id",
        "surname",
        "-surname",
        "admission_no",
        "-admission_no",
    ]
    if sort_by in allowed_sorts:
        students_qs = students_qs.order_by(sort_by)
    else:
        students_qs = students_qs.order_by("-id")

    # Get unique classes for filter dropdown
    classes = Student.objects.values_list("class_at_present", flat=True).distinct()

    # Pagination
    paginator = Paginator(students_qs, 15)  # 15 students per page
    page_number = request.GET.get("page", 1)

    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    context = {
        "page_obj": page_obj,
        "query": query,
        "sex": sex,
        "klass": klass,
        "sort_by": sort_by,
        "classes": classes,
        "total_results": paginator.count,
    }

    return render(request, "records/student_list.html", context)


@login_required
@user_passes_test(_is_staff)
def admin_dashboard(request):
    """Display admin dashboard with statistics and charts"""
    try:
        # Basic statistics
        total_students = Student.objects.count()
        male_count = Student.objects.filter(sex="Male").count()
        female_count = Student.objects.filter(sex="Female").count()

        # Students by class
        students_by_class = (
            Student.objects.values("class_at_present")
            .annotate(count=Count("id"))
            .order_by("class_at_present")
        )

        # Recent students
        recent_students = Student.objects.order_by("-created_at")[:5]

        # Students with documents
        students_with_docs = (
            Student.objects.filter(documents__isnull=False).distinct().count()
        )

        # Total documents
        total_documents = StudentDocument.objects.count()

        context = {
            "total_students": total_students,
            "male_count": male_count,
            "female_count": female_count,
            "recent_students": recent_students,
            "students_by_class": students_by_class,
            "students_with_docs": students_with_docs,
            "total_documents": total_documents,
        }

        return render(request, "records/admin_dashboard.html", context)

    except Exception as e:
        logger.error(f"Error in admin dashboard: {str(e)}")
        messages.error(request, "An error occurred while loading the dashboard.")
        return redirect("records:student_list")


@login_required
@user_passes_test(_is_staff)
def student_detail(request, pk):
    """Display detailed student information with documents"""
    try:
        student = get_object_or_404(
            Student.objects.prefetch_related("documents"), pk=pk
        )

        # Group documents by type
        documents = student.documents.all().order_by("document_type", "-uploaded_at")
        grouped_documents = {}

        for doc in documents:
            doc_type = doc.get_document_type_display()
            if doc_type not in grouped_documents:
                grouped_documents[doc_type] = []
            grouped_documents[doc_type].append(doc)

        context = {
            "student": student,
            "documents": documents,
            "grouped_documents": grouped_documents,
            "document_count": documents.count(),
        }

        return render(request, "records/student_detail.html", context)

    except Exception as e:
        logger.error(f"Error viewing student {pk}: {str(e)}")
        messages.error(request, "An error occurred while loading student details.")
        return redirect("records:student_list")


@login_required
@user_passes_test(_is_staff)
def student_create(request):
    """Create a new student with optional documents"""
    if request.method == "POST":
        logger.debug(
            "student_create: received POST with keys=%s files=%s",
            list(request.POST.keys()),
            list(request.FILES.keys()),
        )
        form = StudentForm(request.POST, request.FILES)
        document_form = StudentDocumentForm(request.POST, request.FILES)
        multiple_docs_form = MultipleStudentDocumentForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save student
                    student = form.save()

                    # Save single document if provided
                    if document_form.is_valid() and document_form.cleaned_data.get(
                        "file"
                    ):
                        document = document_form.save(commit=False)
                        document.student = student
                        document.save()

                    # Save multiple documents if provided
                    if multiple_docs_form.is_valid():
                        files = multiple_docs_form.cleaned_data.get("files", [])
                        doc_type = multiple_docs_form.cleaned_data.get(
                            "document_type", "other"
                        )
                        name_template = (
                            multiple_docs_form.cleaned_data.get("name") or "Document"
                        )

                        for idx, f in enumerate(files, 1):
                            doc_name = (
                                f"{name_template} {idx}"
                                if len(files) > 1
                                else name_template
                            )
                            StudentDocument.objects.create(
                                student=student,
                                document_type=doc_type,
                                name=doc_name,
                                file=f,
                            )

                messages.success(
                    request,
                    f"Student {student.full_name} ({student.admission_no}) created successfully!",
                )
                return redirect("records:student_detail", pk=student.pk)

            except Exception as e:
                logger.error(f"Error creating student: {str(e)}")
                messages.error(request, "An error occurred while creating the student.")
        else:
            # Log form errors for debugging
            logger.debug(
                "student_create: form invalid errors=%s", form.errors.as_json()
            )
            logger.debug(
                "student_create: document_form errors=%s",
                document_form.errors.as_json(),
            )
            logger.debug(
                "student_create: multiple_docs_form errors=%s",
                multiple_docs_form.errors
                if hasattr(multiple_docs_form, "errors")
                else None,
            )
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentForm()
        document_form = StudentDocumentForm()
        multiple_docs_form = MultipleStudentDocumentForm()

    context = {
        "form": form,
        "document_form": document_form,
        "multiple_docs_form": multiple_docs_form,
        "action": "Create",
    }

    return render(request, "records/student_form.html", context)


@login_required
@user_passes_test(_is_staff)
def student_update(request, pk):
    """Update existing student information"""
    student = get_object_or_404(Student, pk=pk)

    if request.method == "POST":
        logger.debug(
            "student_update: received POST for pk=%s keys=%s files=%s",
            pk,
            list(request.POST.keys()),
            list(request.FILES.keys()),
        )
        # Ensure required parent fields are present in POST; if missing, fallback to existing values
        post_data = request.POST.copy()
        for required_field in ("father_name", "mother_name"):
            if not post_data.get(required_field):
                post_data[required_field] = getattr(student, required_field) or ""

        form = StudentForm(post_data, request.FILES, instance=student)
        document_form = StudentDocumentForm(request.POST, request.FILES)
        multiple_docs_form = MultipleStudentDocumentForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                updated_student = form.save()

                # Save a single new document if provided
                if document_form.is_valid() and document_form.cleaned_data.get("file"):
                    document = document_form.save(commit=False)
                    document.student = updated_student
                    document.save()

                # Save multiple documents if provided
                if multiple_docs_form.is_valid():
                    files = multiple_docs_form.cleaned_data.get("files", [])
                    doc_type = multiple_docs_form.cleaned_data.get(
                        "document_type", "other"
                    )
                    name_template = (
                        multiple_docs_form.cleaned_data.get("name") or "Document"
                    )

                    for idx, f in enumerate(files, 1):
                        doc_name = (
                            f"{name_template} {idx}"
                            if len(files) > 1
                            else name_template
                        )
                        StudentDocument.objects.create(
                            student=updated_student,
                            document_type=doc_type,
                            name=doc_name,
                            file=f,
                        )
                messages.success(
                    request,
                    f"Student {updated_student.full_name} updated successfully!",
                )
                return redirect("records:student_detail", pk=updated_student.pk)

            except Exception as e:
                logger.error(f"Error updating student {pk}: {str(e)}")
                messages.error(request, "An error occurred while updating the student.")
        else:
            logger.debug(
                "student_update: form invalid errors=%s", form.errors.as_json()
            )
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentForm(instance=student)
        document_form = StudentDocumentForm()
        multiple_docs_form = MultipleStudentDocumentForm()

    context = {
        "form": form,
        "student": student,
        "action": "Update",
        "document_form": document_form,
        "multiple_docs_form": multiple_docs_form,
    }

    return render(request, "records/student_form.html", context)


@login_required
@user_passes_test(_is_staff)
@require_http_methods(["GET", "POST"])
def student_delete(request, pk):
    """Delete a student and all associated data"""
    student = get_object_or_404(Student, pk=pk)

    if request.method == "POST":
        try:
            student_name = student.full_name
            admission_no = student.admission_no
            student.delete()

            messages.success(
                request,
                f"Student {student_name} ({admission_no}) deleted successfully.",
            )
            return redirect("records:student_list")

        except Exception as e:
            logger.error(f"Error deleting student {pk}: {str(e)}")
            messages.error(request, "An error occurred while deleting the student.")
            return redirect("records:student_detail", pk=pk)

    # Calculate document count for confirmation
    document_count = student.documents.count()

    context = {
        "student": student,
        "document_count": document_count,
    }

    return render(request, "records/student_confirm_delete.html", context)


@login_required
@user_passes_test(_is_staff)
def upload_document(request, student_id):
    """Upload a new document for a student"""
    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        form = StudentDocumentForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                document = form.save(commit=False)
                document.student = student
                document.save()

                messages.success(
                    request, f"Document '{document.name}' uploaded successfully!"
                )
                return redirect("records:student_detail", pk=student.id)

            except Exception as e:
                logger.error(
                    f"Error uploading document for student {student_id}: {str(e)}"
                )
                messages.error(
                    request, "An error occurred while uploading the document."
                )
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentDocumentForm()

    context = {
        "form": form,
        "student": student,
    }

    return render(request, "records/upload_document.html", context)


@login_required
@user_passes_test(_is_staff)
@require_http_methods(["GET", "POST"])
def delete_document(request, student_id, doc_id):
    """Delete a student document"""
    student = get_object_or_404(Student, id=student_id)
    document = get_object_or_404(student.documents, id=doc_id)

    if request.method == "POST":
        try:
            doc_name = document.name
            document.file.delete()  # Delete the actual file
            document.delete()

            messages.success(request, f"Document '{doc_name}' deleted successfully.")
            return redirect("records:student_detail", pk=student.id)

        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {str(e)}")
            messages.error(request, "An error occurred while deleting the document.")
            return redirect("records:student_detail", pk=student.id)

    context = {
        "student": student,
        "document": document,
    }

    return render(request, "records/document_confirm_delete.html", context)


@login_required
@user_passes_test(_is_staff)
def bulk_upload_documents(request, student_id):
    """Upload multiple documents at once for a student"""
    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        form = MultipleStudentDocumentForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                files = form.cleaned_data.get("files", [])
                doc_type = form.cleaned_data.get("document_type", "other")
                name_template = form.cleaned_data.get("name") or "Document"
                notes = form.cleaned_data.get("notes", "")

                with transaction.atomic():
                    for idx, f in enumerate(files, 1):
                        doc_name = (
                            f"{name_template} {idx}"
                            if len(files) > 1
                            else name_template
                        )
                        StudentDocument.objects.create(
                            student=student,
                            document_type=doc_type,
                            name=doc_name,
                            file=f,
                            notes=notes,
                        )

                messages.success(
                    request, f"{len(files)} document(s) uploaded successfully!"
                )
                return redirect("records:student_detail", pk=student.id)

            except Exception as e:
                logger.error(
                    f"Error bulk uploading documents for student {student_id}: {str(e)}"
                )
                messages.error(request, "An error occurred while uploading documents.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = MultipleStudentDocumentForm()

    context = {
        "form": form,
        "student": student,
    }

    return render(request, "records/bulk_upload_documents.html", context)


@login_required
@user_passes_test(_is_staff)
def student_search_ajax(request):
    """AJAX endpoint for student search autocomplete"""
    query = request.GET.get("q", "").strip()

    if len(query) < 2:
        return JsonResponse({"results": []})

    students = Student.objects.filter(
        Q(surname__icontains=query)
        | Q(other_name__icontains=query)
        | Q(admission_no__icontains=query)
    )[:10]

    results = [
        {
            "id": s.id,
            "full_name": s.full_name,
            "admission_no": s.admission_no,
            "class": s.class_at_present,
        }
        for s in students
    ]

    return JsonResponse({"results": results})
