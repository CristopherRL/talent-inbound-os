"""Profile API router — CRUD and CV upload endpoints."""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response

from talent_inbound.container import Container
from talent_inbound.modules.auth.domain.entities import User
from talent_inbound.modules.auth.presentation.dependencies import get_current_user
from talent_inbound.modules.profile.application.extract_cv_skills import ExtractCVSkills
from talent_inbound.modules.profile.application.get_profile import GetProfile
from talent_inbound.modules.profile.application.update_profile import (
    UpdateProfile,
    UpdateProfileCommand,
)
from talent_inbound.modules.profile.application.upload_cv import (
    UploadCV,
    UploadCVCommand,
)
from talent_inbound.modules.profile.domain.exceptions import (
    FileTooLargeError,
    InvalidFileTypeError,
    ProfileNotFoundError,
)
from talent_inbound.modules.profile.infrastructure.storage import StorageBackend
from talent_inbound.modules.profile.presentation.schemas import (
    CVUploadResponse,
    ExtractCVSkillsResponse,
    ProfileRequest,
    ProfileResponse,
)

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=ProfileResponse)
@inject
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    get_profile_uc: GetProfile = Depends(Provide[Container.get_profile_uc]),
) -> ProfileResponse:
    try:
        profile = await get_profile_uc.execute(current_user.id)
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Create one first.",
        )
    return ProfileResponse(
        display_name=profile.display_name,
        professional_title=profile.professional_title,
        skills=profile.skills,
        min_salary=profile.min_salary,
        preferred_currency=profile.preferred_currency,
        work_model=profile.work_model.value if profile.work_model else None,
        preferred_locations=profile.preferred_locations,
        industries=profile.industries,
        cv_filename=profile.cv_filename,
        follow_up_days=profile.follow_up_days,
        ghosting_days=profile.ghosting_days,
        updated_at=profile.updated_at,
    )


@router.put("/me", response_model=ProfileResponse)
@inject
async def update_my_profile(
    body: ProfileRequest,
    current_user: User = Depends(get_current_user),
    update_profile_uc: UpdateProfile = Depends(Provide[Container.update_profile_uc]),
) -> ProfileResponse:
    profile = await update_profile_uc.execute(
        UpdateProfileCommand(
            candidate_id=current_user.id,
            display_name=body.display_name,
            professional_title=body.professional_title,
            skills=body.skills,
            min_salary=body.min_salary,
            preferred_currency=body.preferred_currency,
            work_model=body.work_model,
            preferred_locations=body.preferred_locations,
            industries=body.industries,
            follow_up_days=body.follow_up_days,
            ghosting_days=body.ghosting_days,
        )
    )
    return ProfileResponse(
        display_name=profile.display_name,
        professional_title=profile.professional_title,
        skills=profile.skills,
        min_salary=profile.min_salary,
        preferred_currency=profile.preferred_currency,
        work_model=profile.work_model.value if profile.work_model else None,
        preferred_locations=profile.preferred_locations,
        industries=profile.industries,
        cv_filename=profile.cv_filename,
        follow_up_days=profile.follow_up_days,
        ghosting_days=profile.ghosting_days,
        updated_at=profile.updated_at,
    )


@router.post("/me/cv", response_model=CVUploadResponse)
@inject
async def upload_cv(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    upload_cv_uc: UploadCV = Depends(Provide[Container.upload_cv_uc]),
) -> CVUploadResponse:
    content = await file.read()

    try:
        profile = await upload_cv_uc.execute(
            UploadCVCommand(
                candidate_id=current_user.id,
                filename=file.filename or "unknown",
                content=content,
            )
        )
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Create a profile before uploading a CV.",
        )
    except InvalidFileTypeError as e:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(e),
        )
    except FileTooLargeError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e),
        )

    return CVUploadResponse(cv_filename=profile.cv_filename or "")


@router.post("/me/cv/extract-skills", response_model=ExtractCVSkillsResponse)
@inject
async def extract_cv_skills(
    current_user: User = Depends(get_current_user),
    extract_cv_skills_uc: ExtractCVSkills = Depends(
        Provide[Container.extract_cv_skills_uc]
    ),
) -> ExtractCVSkillsResponse:
    try:
        skills = await extract_cv_skills_uc.execute(current_user.id)
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found.",
        )
    return ExtractCVSkillsResponse(skills=skills)


@router.get("/me/cv")
@inject
async def download_cv(
    current_user: User = Depends(get_current_user),
    get_profile_uc: GetProfile = Depends(Provide[Container.get_profile_uc]),
    storage: StorageBackend = Depends(Provide[Container.storage_backend]),
) -> Response:
    try:
        profile = await get_profile_uc.execute(current_user.id)
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found."
        )

    if not profile.cv_storage_path or not profile.cv_filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No CV uploaded."
        )

    try:
        content = await storage.retrieve(profile.cv_storage_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="CV file not found on disk."
        )

    ext = profile.cv_filename.rsplit(".", 1)[-1].lower()
    media_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "md": "text/markdown",
    }

    return Response(
        content=content,
        media_type=media_types.get(ext, "application/octet-stream"),
        headers={
            "Content-Disposition": f'attachment; filename="{profile.cv_filename}"'
        },
    )
