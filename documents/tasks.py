from celery import shared_task
import logging
from positions.models import Position, Application
from django.shortcuts import get_object_or_404
from documents.models import CVSummary
from rag.chains.match_score import generate_match_score
from core.emails import send_application_confirmation

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@shared_task
def create_application_task(cv_id: int, position_id: int):
    """
    Full async pipeline:
    1) Create an application for cv and position
    2) Compute match score
    3) Save score to Application
    4) Send application confirmation email
    """
    logger.info(f"Task: Starting processing for CV {cv_id} for position: {position_id}")
    try:
        position = get_object_or_404(Position, pk=position_id)
        cv_summary = CVSummary.objects.get(cv_id=cv_id)
        
        # 1) Build position details dict
        position_details = {
            "title": position.title,
            "description": position.description,
            "skills_needed": position.skills_needed,
            "seniority": position.seniority,
            "responsibilities": position.responsibilities,
        }

        # 2) Generate match score
        # should JSON be converted to TOON object?
        score_model = generate_match_score(
            cv_summary=cv_summary.summary_json,
            position_details=position_details
        )

        logger.info(f"Task: Generated match score for CV {cv_id} for position {position_id}: {score_model}")
        
        # 3) Update Application with score
        application = Application.objects.create(
            position=position,
            cv_id=cv_id,
            match_score=score_model.score,
            matched_skills=score_model.matched_skills,
            explanation=score_model.explanation,
            status="Reviewed"
        )

        logger.info(
            f"Task: Application created for CV {cv_id} for position {position_id}: "
            f"{application.id}"
        )
        
        # 4) Send application confirmation email
        send_application_confirmation(
            candidate_name=cv_summary.candidate_name,
            position_title=position.title,
            to_email=cv_summary.emails
        )

        logger.info(
            f"Task: Application confirmation email sent for CV {cv_id} for position {position_id}: "
            f"{application.id}"
        )
        
        return True
    except Exception as e:
        logger.error(f"Task: Error processing CV {cv_id} for position {position_id}: {e}")
        raise
