from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('proposal_entries/', views.list_proposal_files, name='proposal_entries'),
    path('documents/proposal/<str:filename>/', views.serve_proposal_file, name='serve_proposal_file'),
    path('midTermNotice/', views.midTermNotice, name='midTermNotice'),
    path('proposalNotice/', views.proposalNotice, name='proposalNotice'),
    path('finalNotice/', views.finalNotice, name='finalNotice'),
    path('students/', views.students, name='students'),
    # path('supervisor/', views.supervisor, name='supervisor'),
    # path('examiner/', views.examiner, name='examiner'),
    path('midterm_entries/', views.list_midterm_files, name='midterm_entries'),
    path('documents/midterm/<str:filename>/', views.serve_midterm_file, name='serve_midterm_file'),
    path('final_entries/', views.list_final_files, name='final_entries'),  # Added this line
    path('documents/final/<str:filename>/', views.serve_final_file, name='serve_final_file'),  # Added this line
    path('mid_term_thesis_defense_list', views.midtermthesislist, name='mid_term_thesis_defense_list'),
    path('final_thesis_defense_list', views.finalthesislist, name='final_thesis_defense_list'),
    path('results', views.results, name='results'),
    # path('admin_setting', views.admin, name='admin_setting'),
    # path('budget', views.budget, name='budget'),
    path('invalid', views.invalid, name='invalid'),
]