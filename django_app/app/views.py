from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .task import analyze_pr_request
from celery.result import AsyncResult


@api_view(['POST'])
def start_task(request):
    data = request.data
    repo_url = data.get('repo_url')
    pr_number = data.get('pr_number')
    github_token = data.get('github_token')
    task = analyze_pr_request.delay(repo_url, pr_number, github_token)
    return Response({"task_id": task.id , "status": "task has started"})

@api_view(['GET'])
def task_status(request , task_id):
    
       result = AsyncResult(task_id)
       return Response({
           "task_id": task_id,
           "status": result.status,
           "result": result.result if result.ready() else None
       })
      




