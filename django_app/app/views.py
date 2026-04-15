from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .task import analyze_pr_request
from celery.result import AsyncResult
import jwt
from django.conf import settings
from django.contrib.auth.models import User


def get_user_from_token(request):
    """Extract and validate JWT token from request"""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=['HS256']
        )
        user_id = payload.get('user_id')
        if user_id:
            return User.objects.get(id=user_id)
    except:
        pass
    
    return None


@api_view(['POST'])
@permission_classes([AllowAny])
def start_task(request):
    # Validate token
    user = get_user_from_token(request)
    if not user:
        return Response(
            {'error': 'Unauthorized'},
            status=401
        )
    
    data = request.data
    repo_url = data.get('repo_url')
    pr_number = int(data.get('pr_number'))  # Convert to int
    github_token = data.get('github_token')
    task = analyze_pr_request.delay(repo_url, pr_number, github_token)
    return Response({"task_id": task.id , "status": "task has started"})

@api_view(['GET'])
@permission_classes([AllowAny])
def task_status(request, task_id):
    # Validate token
    user = get_user_from_token(request)
    if not user:
        return Response(
            {'error': 'Unauthorized'},
            status=401
        )
    
    result = AsyncResult(task_id)
    
    # Convert exception to string if task failed
    task_result = None
    if result.ready():
        if result.status == 'FAILURE':
            task_result = str(result.result)  # Convert exception to string
        else:
            task_result = result.result
    
    return Response({
        "task_id": task_id,
        "status": result.status,
        "result": task_result
    })
      




