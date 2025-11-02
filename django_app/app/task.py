from celery import Celery
from celery import shared_task
from app.utils.github import analysis_pr

app = Celery('django_app')


@shared_task
def analyze_pr_request(repo_url, pr_number, github_token=None):
    return analysis_pr(repo_url, pr_number, github_token)
