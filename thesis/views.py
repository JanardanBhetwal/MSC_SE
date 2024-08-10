
import pandas as pd

from django.shortcuts import render
from django.conf import settings
from django.http import Http404

from django.shortcuts import render, redirect
from django.core.files.storage import default_storage

from . import utils
import os
from thesis.models import Student, CommonFields, Budget, Coordinator
from .forms import NoticeForm, MidTermThesisCommittee, StudentFormset, \
    NoticeFormExtra, CurrentDate, ResultFormset
from django.http import HttpResponse
import uuid
from django.contrib import messages
from django.http import JsonResponse
from .utils import render_to_word
import pypandoc

def health_check(request):
    return JsonResponse({"status": "ok"})

def index(request):
    return render(request, 'thesis/home.html')

def invalid(request):
    return render(request, 'thesis/invalid.html')

# def proposal_entries(request):
#     return render(request, 'thesis/proposal_entries.html')


def midterm_entries(request):
    return render(request, 'thesis/midterm_entries.html')


def final_entries(request):
    return render(request, 'thesis/final_entries.html')

def students(request):
    if request.method == 'POST':
        if 'submit' in request.POST:
            formset = StudentFormset(request.POST)
            if formset.is_valid():
                instances = formset.save(commit=False)
                for i in instances:
                    if i.midterm is False:
                        i.examiner = None
                        i.final = False
                    if not i.internalMarks and not i.finalMarks:
                        i.totalMarks = None
                    if i.final is False:
                        i.internalMarks = None
                        i.finalMarks = None
                        i.totalMarks = None
                    else:
                        if i.internalMarks and i.finalMarks:
                            i.totalMarks = i.internalMarks + i.finalMarks
                        else:
                            i.totalMarks = None
                    i.save()
                messages.success(request, 'Students updated successfully.')
            return redirect('thesis:students')
        
        elif 'delete' in request.POST:
            selected_students = request.POST.getlist('selected_students')
            if selected_students:
                Student.objects.filter(id__in=selected_students).delete()
                messages.success(request, 'Selected students were deleted successfully.')
            else:
                messages.error(request, 'No students were selected for deletion.')
            return redirect('thesis:students')
    
    else:
        formset = StudentFormset(queryset=Student.objects.all())
    return render(request, 'thesis/students.html', {'formset': formset})


def list_proposal_files(request):
    proposal_dir = os.path.join(settings.BASE_DIR, 'Documents', 'Proposal')

    try:
        # Verify if the directory exists and list files
        if os.path.exists(proposal_dir):
            files = [f for f in os.listdir(proposal_dir) if os.path.isfile(os.path.join(proposal_dir, f))]
        else:
            files = []
        
    except Exception as e:
        files = []

    context = {
        'files': files,
    }
    return render(request, 'thesis/proposal_entries.html', context)

def serve_proposal_file(request, filename):
    proposal_dir = os.path.join(settings.BASE_DIR, 'Documents', 'Proposal')
    file_path = os.path.join(proposal_dir, filename)
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = f'attachment; filename={filename}'
            return response
    else:
        raise Http404("File does not exist")
    

import os
import uuid
from django.conf import settings
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Coordinator, CommonFields
from .forms import NoticeForm, NoticeFormExtra
from .utils import render_to_word

def list_midterm_files(request):
    midterm_dir = os.path.join(settings.BASE_DIR, 'Documents', 'Midterm')
    try:
        if os.path.exists(midterm_dir):
            files = [f for f in os.listdir(midterm_dir) if os.path.isfile(os.path.join(midterm_dir, f))]
        else:
            files = []
    except Exception as e:
        files = []

    context = {'files': files}
    return render(request, 'thesis/midterm_entries.html', context)

def serve_midterm_file(request, filename):
    midterm_dir = os.path.join(settings.BASE_DIR, 'Documents', 'Midterm')
    file_path = os.path.join(midterm_dir, filename)

    if os.path.exists(file_path):
        try:
            output = pypandoc.convert_file(file_path, 'html')
            context = {'html': output}
            return render(request, 'thesis/view_document.html', context)
        except Exception as e:
            raise Http404(f"Error converting file: {e}")
    else:
        raise Http404("File does not exist")

def list_final_files(request):
    final_dir = os.path.join(settings.BASE_DIR, 'Documents', 'Final')
    try:
        if os.path.exists(final_dir):
            files = [f for f in os.listdir(final_dir) if os.path.isfile(os.path.join(final_dir, f))]
        else:
            files = []
    except Exception as e:
        files = []

    context = {'files': files}
    return render(request, 'thesis/final_entries.html', context)

def serve_final_file(request, filename):
    final_dir = os.path.join(settings.BASE_DIR, 'Documents', 'Final')
    file_path = os.path.join(final_dir, filename)

    if os.path.exists(file_path):
        try:
            output = pypandoc.convert_file(file_path, 'html')
            context = {'html': output}
            return render(request, 'thesis/view_document.html', context)
        except Exception as e:
            raise Http404(f"Error converting file: {e}")
    else:
        raise Http404("File does not exist")



def proposalNotice(request):
    print("Hello from Proposal Notice")
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES)
        formExtra = NoticeFormExtra(request.POST)
        
        if form.is_valid() and formExtra.is_valid():
            try:
                admins = Coordinator.objects.filter(user=request.user.id).first()
                
                if not admins:
                    messages.error(request, "No coordinator found for the current user.")
                    return redirect('thesis:invalid')
                
                form.save()
                Common = CommonFields.objects.all()
                if len(Common) > 1:
                    Common[0].delete()
                
                context = form.cleaned_data
                contextFormExtra = formExtra.cleaned_data
                defenseDate = str(Common[0].defenseDate)
                studentBatch = str(Common[0].studentBatch)
                
                context['programName'] = str(admins.programName)
                context['coordinatorName'] = str(admins.coordinatorName)
                context['batch'] = studentBatch
                context['defensedate'] = defenseDate
                context['submissionTime'] = contextFormExtra['submissionTime']
                context['submissionDate'] = contextFormExtra['submissionDate']
                
                # Save uploaded file to templates/Proposal
                if 'template_file' in request.FILES:
                    uploaded_file = request.FILES['template_file']
                    template_path = os.path.join(settings.BASE_DIR, 'templates', 'Proposal', uploaded_file.name)
                    with open(template_path, 'wb+') as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)
                else:
                    template_path = os.path.join(
                        settings.BASE_DIR, 'templates', 'Proposal', 'ProposalNotice.docx'
                    )

                output_path = os.path.join(
                    settings.BASE_DIR, 'Documents', 'Proposal',
                    f"ProposalNotice_{uuid.uuid4()}.docx"
                )
                render_to_word(template_path, output_path, context)
                
                response = HttpResponse(open(output_path, 'rb').read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_path)}'
                return response
                
            except Exception as e:
                messages.error(request, f"An unexpected error occurred: {e}")
                return redirect('thesis:invalid')
        else:
            return redirect('thesis:invalid')
    else:
        form = NoticeForm()
        formExtra = NoticeFormExtra()
        return render(request, 'thesis/proposalAndFinalNotice.html', {'form': form, 'formExtra': formExtra})


def midTermNotice(request):
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES)
        formExtra = NoticeFormExtra(request.POST)
        
        if form.is_valid() and formExtra.is_valid():
            try:
                admins = Coordinator.objects.filter(user=request.user.id).first()
                
                if not admins:
                    messages.error(request, "No coordinator found for the current user.")
                    return redirect('thesis:invalid')
                
                form.save()
                Common = CommonFields.objects.all()
                if len(Common) > 1:
                    Common[0].delete()
                
                context = form.cleaned_data
                contextFormExtra = formExtra.cleaned_data
                context['programName'] = str(admins.programName)
                context['coordinatorName'] = str(admins.coordinatorName)
                context['submissionTime'] = contextFormExtra['submissionTime']
                context['submissionDate'] = contextFormExtra['submissionDate']
                
                # Save uploaded file to templates/Midterm
                if 'template_file' in request.FILES:
                    uploaded_file = request.FILES['template_file']
                    template_path = os.path.join(settings.BASE_DIR, 'templates', 'Midterm', uploaded_file.name)
                    with open(template_path, 'wb+') as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)
                else:
                    template_path = os.path.join(
                        settings.BASE_DIR, 'templates', 'Midterm', 'MidtermNotice.docx'
                    )

                output_path = os.path.join(
                    settings.BASE_DIR, 'Documents', 'Midterm',
                    f"MidtermNotice_{uuid.uuid4()}.docx"
                )
                render_to_word(template_path, output_path, context)
                
                response = HttpResponse(open(output_path, 'rb').read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                response['Content-Disposition'] = f'attachment; filename={os.path.basename(output_path)}'
                return response
                
            except Exception as e:
                messages.error(request, f"An unexpected error occurred: {e}")
                return redirect('thesis:invalid')
        else:
            return redirect('thesis:invalid')
    else:
        form = NoticeForm()
        formExtra = NoticeFormExtra()
        return render(request, 'thesis/midTermNotice.html', {'form': form, 'formExtra': formExtra})


def finalNotice(request):
    if request.method == 'POST':
        form = NoticeForm(request.POST)
        formExtra = NoticeFormExtra(request.POST)
        
        if form.is_valid() and formExtra.is_valid():
            try:
                # Use filter and first() to safely get the first matching coordinator or None
                admins = Coordinator.objects.filter(user=request.user.id).first()
                
                if not admins:
                    # Handle case where no coordinator is found
                    messages.error(request, "No coordinator found for the current user.")
                    return redirect('thesis:invalid')  # Or render a specific error page

                form.save()
                Common = CommonFields.objects.all()
                if len(Common) > 1:
                    Common[0].delete()
                
                context = form.cleaned_data
                contextFormExtra = formExtra.cleaned_data
                context['submissionTime'] = contextFormExtra['submissionTime']
                context['submissionDate'] = contextFormExtra['submissionDate']
                context['programName'] = str(admins.programName)
                context['coordinatorName'] = str(admins.coordinatorName)
                
                src_add = os.path.join(
                    os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'), 'Final'),
                    'FinalNotice.docx'
                )
                output_path = os.path.join(
                    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'),
                    'Final', 'finalNotice.docx'
                )
                
                utils.render_to_word(src_add, output_path, context)
                response = HttpResponse(open(output_path, 'rb').read())
                response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                response['Content-Disposition'] = 'attachment; filename=finalNotice.docx'
                
                return response
                
            except Exception as e:
                # Log the exception and handle the error
                messages.error(request, f"An unexpected error occurred: {e}")
                return redirect('thesis:invalid')
        else:
            # Handle form errors
            messages.error(request, "Form validation failed. Please correct the errors and try again.")
            return render(request, 'thesis/proposalAndFinalNotice.html', {'form': form, 'formExtra': formExtra})

    else:
        form = NoticeForm()
        formExtra = NoticeFormExtra()
        return render(request, 'thesis/proposalAndFinalNotice.html', {'form': form, 'formExtra': formExtra})


def midtermthesislist(request):
    if request.method == 'POST':
        budgets = Budget.objects.all().get()
        admins = Coordinator.objects.all().get(user=request.user.id)
        Common = CommonFields.objects.all()
        defenseDate = str(Common[0].defenseDate)
        studentBatch = str(Common[0].studentBatch)
        form = MidTermThesisCommittee(request.POST)
        formset = StudentFormset(request.POST)
        if formset.is_valid() and form.is_valid():
            context1 = form.cleaned_data
            print(context1['Chairman'])
            budgetList = list()  # new
            students = []
            examiners = set()
            supervisor = set()

            stds = formset.save(commit=False)

            for std in stds:
                if std.midterm is True:
                    students.append(std)
                    examiners.add(std.examiner)
                    supervisor.add(std.supervisor)
                std.save()

            noOfStd = len(students)  # new

            budgetList.append({'name': 'Peon', 'post': 'peon', 'number': str(noOfStd),  # new
                               'rate': str(budgets.peon), 'total': str(noOfStd * budgets.peon),
                               'tax': str(float(budgets.tax * noOfStd * budgets.peon * .01)),
                               'net': str(float(noOfStd * budgets.peon - budgets.tax * noOfStd * budgets.peon * .01))})

            budgetList.append({'name': 'Staff', 'post': 'staff', 'number': str(noOfStd),  # new
                               'rate': str(budgets.staff), 'total': str(noOfStd * budgets.staff),
                               'tax': str(float(budgets.tax * noOfStd * budgets.staff * .01)),
                               'net': str(
                                   float(noOfStd * budgets.staff - budgets.tax * noOfStd * budgets.staff * .01))})

            numberOfStudents = str(len(students))

            thesisListElements = dict()
            thesisListElements['CurrentDate'] = context1['CurrentDate']
            thesisListElements['B2'] = studentBatch
            thesisListElements['no'] = numberOfStudents
            thesisListElements['DefenceDate'] = defenseDate
            j = 1
            thesisStdList = list()
            thesisStdList1 = list()

            for std in students:
                evaluation = dict()
                sd = dict()
                sd1 = list()
                sd['id'] = str(j)
                sd['name'] = str(std.name)
                sd['rollNumber'] = str(std.rollNumber)
                sd['thesisTitle'] = str(std.thesisTitle)
                sd['supervisor'] = str(std.supervisor)
                sd['examiner'] = str(std.examiner)
                evaluation.update(sd)
                evaluation['programName'] = str(admins.programName)
                evaluation['date'] = defenseDate
                evaluation['organization'] = str(std.examiner.organization.institute_name)
                thesisStdList.append(sd)

                sd1.append(std.rollNumber)
                sd1.append(std.name)
                sd1.append(std.thesisTitle)
                sd1.append(std.supervisor)
                sd1.append(std.examiner)


                thesisStdList1.append(sd1)


                j = j + 1

                src_add = os.path.join(
                    os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'), 'Midterm'),
                    'evalMid_Committee_Member.docx')
                utils.render_to_word(src_add, os.path.join(os.path.join(os.path.join(
                    os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'), 'Midterm')
                    , 'Evaluation'), 'Committee Member'),
                    (str(std.name) + '\'s_Committe_Member_Evaluation.docx')), evaluation)

                src_add = os.path.join(
                    os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'), 'Midterm'),
                    'evalMid_External_Examiner.docx')
                utils.render_to_word(src_add, os.path.join(os.path.join(os.path.join(
                    os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'), 'Midterm')
                    , 'Evaluation'), 'External Examiner'),
                    (str(std.examiner) + ' External_Evaluation.docx')), evaluation)

                src_add = os.path.join(
                    os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'), 'Midterm'),
                    'evalMid_Supervisor.docx')
                utils.render_to_word(src_add, os.path.join(os.path.join(os.path.join(
                    os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'), 'Midterm')
                    , 'Evaluation'), 'Supervisor'),
                    (str(std.supervisor) + ' Supervisor_Evaluation.docx')), evaluation)

            df1 = pd.DataFrame(thesisStdList1,
                               columns=['Roll NO', 'Name Of Student', 'Thesis Title', 'Supervisor',
                                        ' External Examiner'])
            df1.set_index('Roll NO', inplace=True)
            df1.to_excel(os.path.join(
                os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'), 'Midterm'),
                'candidates-midterm.xlsx'))

            thesisListElements['list'] = thesisStdList
            thesisListElements['programName'] = str(admins.programName)
            thesisListElements['coordinatorName'] = str(admins.coordinatorName)
            thesisListElements['B2'] = studentBatch

            src_add = os.path.join(
                os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'), 'Midterm'),
                'MidtermThesisList.docx')
            utils.make_table(src_add, os.path.join(
                os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'), 'Midterm'),
                'MidtermThesisList.docx'), thesisListElements)

            for suv in supervisor:
                budgetSupervisor = dict()  # new
                i = 0
                for std in students:
                    if str(std.supervisor) == str(suv):
                        i = i + 1

                budgetSupervisor['name'] = str(suv)
                budgetSupervisor['post'] = 'Supervisor'
                budgetSupervisor['number'] = str(i)
                budgetSupervisor['rate'] = str(budgets.supervisor)
                budgetSupervisor['total'] = str(float(budgetSupervisor['rate']) * i)
                budgetSupervisor['tax'] = str(float(float(budgetSupervisor['total']) * budgets.tax * 0.01))
                budgetSupervisor['net'] = str(float(budgetSupervisor['total']) - float(budgetSupervisor['tax']))

                budgetList.append(budgetSupervisor)

            committeeMembers = [str(context1['MemberSecretary']), str(context1['Member']),
                                str(context1['Chairman'])]

            supervisor1 = []

            for i in supervisor:
                supervisor1.append(i)

            k = 0
            for name in committeeMembers:
                if k == 0:
                    post = 'Supervisor Member Secretary'
                elif k == 1:
                    post = 'Supervisor Member'
                else:
                    post = 'Supervisor Chairman'
                k = k + 1
                NOS = noOfStd
                if name in supervisor1:
                    for i in budgetList:
                        if i['name'] == name:
                            NOS = noOfStd - int(i['number'])
                            break

                budgetList.append({'name': name, 'post': post, 'number': str(NOS),  # new
                                   'rate': str(budgets.supervisor), 'total': str(NOS * budgets.supervisor),
                                   'tax': str(float(budgets.tax * NOS * budgets.supervisor * .01)),
                                   'net': str(
                                       float(NOS * budgets.supervisor - budgets.tax * NOS * budgets.supervisor * .01))})

            for examr in examiners:
                context = dict()
                budgetExaminer = dict()  # new
                stdlist = list()
                i = 0
                for std in students:
                    if str(std.examiner) == str(examr):
                        s = dict()
                        s['name'] = str(std.name)
                        s['rollNumber'] = str(std.rollNumber)
                        s['thesisTitle'] = str(std.thesisTitle)
                        stdlist.append(s)
                        i = i + 1
                        s['id'] = str(i)

                budgetExaminer['name'] = str(examr)
                budgetExaminer['post'] = 'External Examiner'
                budgetExaminer['number'] = str(i)
                budgetExaminer['rate'] = str(budgets.externalExaminer)
                budgetExaminer['total'] = str(float(budgetExaminer['rate']) * i)
                budgetExaminer['tax'] = str(float(float(budgetExaminer['total']) * budgets.tax * 0.01))
                budgetExaminer['net'] = str(float(budgetExaminer['total']) - float(budgetExaminer['tax']))

                budgetList.append(budgetExaminer)
                context['programName'] = str(admins.programName)
                context['coordinatorName'] = str(admins.coordinatorName)
                context['ExExaminerName'] = str(examr)
                context['CompanyName'] = str(examr.organization.institute_name)
                context['ComAddress'] = str(examr.organization.address)
                context['CurrentDate'] = context1['CurrentDate']
                context['DefenceDate'] = defenseDate
                context['no'] = numberOfStudents
                context['B2'] = studentBatch

                if len(stdlist) != 0:
                    context['list'] = stdlist
                    src_add = os.path.join(
                        os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'), 'Midterm'),
                        'LetterToExExaminer.docx')
                    utils.make_table(src_add, os.path.join(
                        os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'), 'Midterm'),
                        (str(examr) + ' LetterToExExaminer.docx')), context)

            context2 = dict()
            context2['CurrentDate'] = context1['CurrentDate']
            context2['DefenceDate'] = defenseDate
            context2['no'] = numberOfStudents
            budgetList.reverse()

            for i in range(0, len(budgetList)):
                budgetList[i]['sn'] = str(i + 1)

            context2['list'] = budgetList
            context2['programName'] = str(admins.programName)
            context2['coordinatorName'] = str(admins.coordinatorName)
            context2['taxPercent'] = str(budgets.tax)
            context2['batch'] = studentBatch

            src_add = os.path.join(
                os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'), 'Midterm'),
                'midTermSalaryDistribution.docx')
            utils.make_table(src_add, os.path.join(
                os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'), 'Midterm'),
                'midTermSalaryDistribution.docx'), context2)

            context1['programName'] = str(admins.programName)
            context1['coordinatorName'] = str(admins.coordinatorName)
            context1['DefenceDate'] = defenseDate
            context1['Chairman'] = str(context1['Chairman'])

            context1['Member'] = str(context1['Member'])
            context1['MemberSecretary'] = str(context1['MemberSecretary'])
            context1['Batch'] = studentBatch
            context1['no'] = numberOfStudents

            src_add = os.path.join(
                os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'), 'Midterm'),
                'MidtermCommittee.docx')
            output_path = os.path.join(
                os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'), 'Midterm'),
                'MidtermCommittee.docx')
            utils.render_to_word(src_add, output_path, context1)

            response = HttpResponse(open(output_path, 'rb').read())
            response['Content-Type'] = 'mimetype/submimetype'
            response['Content-Disposition'] = 'attachment; filename=MidtermCommittee.docx'
            # messages.success(request, "The Download is starting...")
            return response

            # return redirect('thesis:index')

    else:
        form = MidTermThesisCommittee()
        formset = StudentFormset(queryset=Student.objects.filter(midterm=False))
    return render(request, 'thesis/midtermthesislist.html', {'form': form, 'formset': formset})


# Finals
# TODO Error, not filling the template
def finalthesislist(request):
    if request.method == 'POST':
        budgets = Budget.objects.all().get()
        admins = Coordinator.objects.all().get(user=request.user.id)
        Common = CommonFields.objects.all()
        defenseDate = str(Common[0].defenseDate)
        studentBatch = str(Common[0].studentBatch)
        form = MidTermThesisCommittee(request.POST)
        formset = StudentFormset(request.POST)
        if formset.is_valid() and form.is_valid():
            context1 = form.cleaned_data
            budgetList = list()
            students = []
            examiners = set()
            supervisor = set()

            stds = formset.save(commit=False)

            for std in stds:
                if std.final is True:
                    std.midterm = True
                    students.append(std)
                    examiners.add(std.examiner)
                    supervisor.add(std.supervisor)
                std.save()

            noOfStd = len(students)  # new

            budgetList.append({'name': 'Peon', 'post': 'peon', 'number': str(noOfStd),  # new
                               'rate': str(budgets.peon), 'total': str(noOfStd * budgets.peon),
                               'tax': str(float(budgets.tax * noOfStd * budgets.peon * .01)),
                               'net': str(float(noOfStd * budgets.peon - budgets.tax * noOfStd * budgets.peon * .01))})

            budgetList.append({'name': 'Staff', 'post': 'staff', 'number': str(noOfStd),  # new
                               'rate': str(budgets.staff), 'total': str(noOfStd * budgets.staff),
                               'tax': str(float(budgets.tax * noOfStd * budgets.staff * .01)),
                               'net': str(
                                   float(noOfStd * budgets.staff - budgets.tax * noOfStd * budgets.staff * .01))})

            numberOfStudents = str(len(students))

            thesisListElements = dict()
            thesisListElements['CurrentDate'] = context1['CurrentDate']
            thesisListElements['Batch'] = studentBatch
            thesisListElements['no'] = numberOfStudents
            thesisListElements['defenceDate'] = defenseDate
            j = 1
            thesisStdList = list()
            thesisStdList1 = list()

            for std in students:
                evaluation = dict()
                sd = dict()
                sd1 = list()
                sd['id'] = str(j)
                sd['name'] = str(std.name)
                sd['rollNumber'] = str(std.rollNumber)
                sd['thesisTitle'] = str(std.thesisTitle)
                sd['supervisor'] = str(std.supervisor)
                sd['examiner'] = str(std.examiner)

                evaluation.update(sd)
                evaluation['programName'] = str(admins.programName)
                evaluation['date'] = defenseDate
                evaluation['organization'] = str(std.examiner.organization.institute_name)

                thesisStdList.append(sd)

                sd1.append(std.rollNumber)
                sd1.append(std.name)
                sd1.append(std.thesisTitle)
                sd1.append(std.supervisor)
                sd1.append(std.examiner)

                thesisStdList1.append(sd1)

                j = j + 1

                src_add = os.path.join(
                    os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'), 'Final'),
                    'evalfinal_Committee_Member.docx')
                utils.render_to_word(src_add, os.path.join(os.path.join(os.path.join(
                    os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'), 'Final')
                    , 'Evaluation'), 'Committee Member'),
                    (str(std.name) + "'s_Committe_Member_Evaluation.docx")), evaluation)

                src_add = os.path.join(
                    os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'), 'Final'),
                    'evalfinal_External_Examiner.docx')
                utils.render_to_word(src_add, os.path.join(os.path.join(os.path.join(
                    os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'), 'Final')
                    , 'Evaluation'), 'External Examiner'),
                    (str(std.examiner) + ' External_Evaluation.docx')), evaluation)

                src_add = os.path.join(
                    os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'), 'Final'),
                    'evalfinal_Supervisor.docx')
                utils.render_to_word(src_add, os.path.join(os.path.join(os.path.join(
                    os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'), 'Final')
                    , 'Evaluation'), 'Supervisor'),
                    (str(std.supervisor) + ' Supervisor_Evaluation.docx')), evaluation)

            df1 = pd.DataFrame(thesisStdList1,
                               columns=['Roll NO', 'Name Of Student', 'Thesis Title', 'Supervisor',
                                        ' External Examiner'])
            df1.set_index('Roll NO', inplace=True)
            df1.to_excel(os.path.join(
                os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'), 'Final'),
                'candidates-final.xlsx'))

            thesisListElements['list'] = thesisStdList
            thesisListElements['defenseDate'] = defenseDate
            thesisListElements['programName'] = str(admins.programName)
            
            thesisListElements['coordinatorName'] = str(admins.coordinatorName)

            src_add = os.path.join(
                os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'), 'Final'),
                'FinalThesisList.docx')
            utils.make_table(src_add, os.path.join(
                os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'), 'Final'),
                'FinalThesisList.docx'), thesisListElements)

            for suv in supervisor:
                budgetSupervisor = dict()  # new
                i = 0
                for std in students:
                    if str(std.supervisor) == str(suv):
                        i = i + 1

                budgetSupervisor['name'] = str(suv)
                budgetSupervisor['post'] = 'Supervisor'
                budgetSupervisor['number'] = str(i)
                budgetSupervisor['rate'] = str(budgets.supervisor)
                budgetSupervisor['total'] = str(float(budgetSupervisor['rate']) * i)
                budgetSupervisor['tax'] = str(float(float(budgetSupervisor['total']) * budgets.tax * 0.01))
                budgetSupervisor['net'] = str(float(budgetSupervisor['total']) - float(budgetSupervisor['tax']))

                budgetList.append(budgetSupervisor)

            committeeMembers = [str(context1['MemberSecretary']), str(context1['Member']),
                                str(context1['Chairman'])]

            supervisor1 = []

            for i in supervisor:
                supervisor1.append(i)

            k = 0
            for name in committeeMembers:
                if k == 0:
                    post = 'Supervisor Member Secretary'
                elif k == 1:
                    post = 'Supervisor Member'
                else:
                    post = 'Supervisor Chairman'
                k = k + 1
                NOS = noOfStd
                if name in supervisor1:
                    for i in budgetList:
                        if i['name'] == name:
                            NOS = noOfStd - int(i['number'])
                            break

                budgetList.append({'name': name, 'post': post, 'number': str(NOS),  # new
                                   'rate': str(budgets.supervisor), 'total': str(NOS * budgets.supervisor),
                                   'tax': str(float(budgets.tax * NOS * budgets.supervisor * .01)),
                                   'net': str(
                                       float(NOS * budgets.supervisor - budgets.tax * NOS * budgets.supervisor * .01))})

            for examr in examiners:
                context = dict()
                budgetExaminer = dict()
                stdlist = list()
                i = 0
                for std in students:
                    if str(std.examiner) == str(examr):
                        s = dict()
                        s['name'] = str(std.name)
                        s['rollNumber'] = str(std.rollNumber)
                        s['thesisTitle'] = str(std.thesisTitle)
                        stdlist.append(s)
                        i = i + 1
                        s['id'] = str(i)

                budgetExaminer['name'] = str(examr)
                budgetExaminer['post'] = 'External Examiner'
                budgetExaminer['number'] = str(i)
                budgetExaminer['rate'] = str(budgets.externalExaminer)
                budgetExaminer['total'] = str(float(budgetExaminer['rate']) * i)
                budgetExaminer['tax'] = str(float(float(budgetExaminer['total']) * budgets.tax * 0.01))
                budgetExaminer['net'] = str(float(budgetExaminer['total']) - float(budgetExaminer['tax']))

                budgetList.append(budgetExaminer)

                context['programName'] =str(admins.programName)
                context['coordinatorName'] = str(admins.coordinatorName)
                context['ExExaminerName'] = str(examr)
                context['CompanyName'] = str(examr.organization.institute_name)
                context['ComAddress'] = str(examr.organization.address)
                context['CurrentDate'] = context1['CurrentDate']
                context['DefenceDate'] = defenseDate
                context['B2'] = studentBatch
                context['no'] = numberOfStudents

                if len(stdlist) != 0:
                    context['list'] = stdlist
                    src_add = os.path.join(
                        os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'), 'Final'),
                        'LetterToExExaminer.docx')
                    utils.make_table(src_add, os.path.join(
                        os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'), 'Final'),
                        (str(examr) + ' LetterToExExaminer.docx')), context)

            context2 = dict()
            context2['CurrentDate'] = context1['CurrentDate']
            context2['DefenceDate'] = defenseDate
            context2['no'] = numberOfStudents
            budgetList.reverse()

            for i in range(0, len(budgetList)):
                budgetList[i]['sn'] = str(i + 1)

            context2['list'] = budgetList
            context2['programName'] = str(admins.programName)
            context2['coordinatorName'] = str(admins.coordinatorName)
            context2['taxPercent'] = str(budgets.tax)
            context2['batch'] = studentBatch

            src_add = os.path.join(
                os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'), 'Final'),
                'finalSalaryDistribution.docx')
            utils.make_table(src_add, os.path.join(
                os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'), 'Final'),
                'finalSalaryDistribution.docx'), context2)

            context1['programName'] = str(admins.programName)
            context1['coordinatorName'] = str(admins.coordinatorName)
            context1['defenseDate'] = defenseDate
            context1['Chairman'] = str(context1['Chairman'])
            context1['Member'] = str(context1['Member'])
            context1['MemberSecretary'] = str(context1['MemberSecretary'])
            context1['Batch'] = studentBatch
            context1['no'] = numberOfStudents

            src_add = os.path.join(
                os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'), 'Final'),
                'FinalThesisList.docx')
            output_path = os.path.join(
                os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'), 'Final'),
                'FinalThesisList.docx')
            utils.render_to_word(src_add, output_path, context1)
            response = HttpResponse(open(output_path, 'rb').read())
            response['Content-Type'] = 'mimetype/submimetype'
            response['Content-Disposition'] = 'attachment; filename=FinalThesisList.docx'
            # messages.success(request, "The Download is starting...")
            return response
            # return redirect('thesis:index')

    else:
        form = MidTermThesisCommittee()
        formset = StudentFormset(queryset=Student.objects.filter(midterm=True).filter(final=False))
    return render(request, 'thesis/finalthesislist.html', {'form': form, 'formset': formset})


# results


def results(request):
    if request.method == 'POST':
        form = CurrentDate(request.POST)
        formset = ResultFormset(request.POST)
        Common = CommonFields.objects.all()
        defenseDate = str(Common[0].defenseDate)
        studentBatch = str(Common[0].studentBatch)
        admins = Coordinator.objects.all().get(user=request.user.id)
        print(formset.errors)
        if formset.is_valid() and form.is_valid():
            context1 = form.cleaned_data
            instances = formset.save(commit=False)
            students = []
            examiners = set()
            for std in instances:
                std.totalMarks = int(std.internalMarks) + int(std.finalMarks)
                std.midterm = True
                std.final = True
                students.append(std)
                examiners.add(std.examiner)
                std.save()

            numberOfStudents = str(len(students))

            thesisListElements = dict()
            thesisListElements['CurrentDate'] = context1['CurrentDate']
            thesisListElements['Batch'] = studentBatch
            thesisListElements['no'] = numberOfStudents
            thesisListElements['defenseDate'] = defenseDate
            j = 1
            thesisStdList = list()
            for std in students:
                sd = dict()
                sd['id'] = str(j)
                sd['name'] = str(std.name)
                sd['rollNumber'] = str(std.rollNumber)
                sd['thesisTitle'] = str(std.thesisTitle)
                sd['supervisor'] = str(std.supervisor)
                sd['examRollNumber'] = str(std.examRollNumber)
                sd['internalMarks'] = str(std.internalMarks)
                sd['finalMarks'] = str(std.finalMarks)
                sd['totalMarks'] = str(std.totalMarks)
                thesisStdList.append(sd)
                j = j + 1

            thesisListElements['programName'] = str(admins.programName)
            thesisListElements['coordinatorName'] = str(admins.coordinatorName)
            thesisListElements['list'] = thesisStdList

            src_add = os.path.join(
                os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'), 'Final'),
                'FinalThesisResultCover.docx')
            utils.make_table(src_add, os.path.join(
                os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'), 'Final'),
                'FinalThesisResultCover.docx'), thesisListElements)

            src_add = os.path.join(
                os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'), 'Final'),
                'FinalThesisResult.docx')
            output_path = os.path.join(
                os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Documents'), 'Final'),
                'FinalThesisResult.docx')
            utils.make_table(src_add, output_path, thesisListElements)
            response = HttpResponse(open(output_path, 'rb').read())
            response['Content-Type'] = 'mimetype/submimetype'
            response['Content-Disposition'] = 'attachment; filename=FinalThesisResult.docx'
            # messages.success(request, "The Download is starting...")
            return response
            # return redirect('thesis:index')
    else:
        form = CurrentDate()
        formset = ResultFormset(
            queryset=Student.objects.filter(midterm=True).filter(final=True).filter(totalMarks=None))
        return render(request, 'thesis/results.html', {'formset': formset, 'form': form})
