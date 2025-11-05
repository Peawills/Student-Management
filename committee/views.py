from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import StudentOffense, TeacherReport
from .forms import StudentOffenseForm, TeacherReportForm
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa



@login_required
def offense_list(request):
    offenses = StudentOffense.objects.all().order_by("-offense_date")
    offenses = StudentOffense.objects.all()
    
    # Search
    query = request.GET.get('q')
    if query:
        offenses = offenses.filter(
            Q(student_name__icontains=query) |
            Q(offense_description__icontains=query)
        )
    
    # Filter by event type
    event_type = request.GET.get('event_type')
    if event_type:
        offenses = offenses.filter(event_type=event_type)
    
    return render(request, 'committee/offense_list.html', {
        'offenses': offenses,
        'query': query,
        'event_type': event_type
    })
    return render(request, "committee/offense_list.html", {"offenses": offenses})


@login_required
def offense_detail(request, offense_id):
    offense = get_object_or_404(StudentOffense, id=offense_id)
    reports = offense.reports.all()

    # Handle adding teacher report
    if request.method == "POST":
        report_form = TeacherReportForm(request.POST)
        if report_form.is_valid():
            report = report_form.save(commit=False)
            report.offense = offense
            report.save()
            messages.success(request, "Teacher report added successfully!")
            return redirect("committee:offense_detail", offense_id=offense.id)
    else:
        report_form = TeacherReportForm()

    context = {"offense": offense, "reports": reports, "report_form": report_form}
    return render(request, "committee/offense_detail.html", context)


@login_required
def offense_create(request):
    if request.method == "POST":
        form = StudentOffenseForm(request.POST)
        if form.is_valid():
            offense = form.save()
            messages.success(
                request,
                f"Offense record for {offense.student_name} created successfully!",
            )
            return redirect("committee:offense_detail", offense_id=offense.id)
    else:
        form = StudentOffenseForm()

    return render(
        request, "committee/offense_form.html", {"form": form, "action": "Create"}
    )


@login_required
def offense_update(request, offense_id):
    offense = get_object_or_404(StudentOffense, id=offense_id)

    if request.method == "POST":
        form = StudentOffenseForm(request.POST, instance=offense)
        if form.is_valid():
            form.save()
            messages.success(request, "Offense record updated successfully!")
            return redirect("committee:offense_detail", offense_id=offense.id)
    else:
        form = StudentOffenseForm(instance=offense)

    return render(
        request,
        "committee/offense_form.html",
        {"form": form, "offense": offense, "action": "Update"},
    )


@login_required
def offense_delete(request, offense_id):
    offense = get_object_or_404(StudentOffense, id=offense_id)

    if request.method == "POST":
        student_name = offense.student_name
        offense.delete()
        messages.success(
            request, f"Offense record for {student_name} deleted successfully!"
        )
        return redirect("committee:offense_list")

    return render(
        request, "committee/offense_confirm_delete.html", {"offense": offense}
    )


@login_required
def render_pdf_view(request, offense_id):
    offense = get_object_or_404(StudentOffense, id=offense_id)
    template_path = "committee/offense_pdf.html"
    context = {"offense": offense}

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="offense_report_{offense.student_name}_{offense.offense_date}.pdf"'
    )

    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("We had some errors <pre>" + html + "</pre>")
    return response
