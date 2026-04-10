import os
import traceback
import uuid
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from api.settings import settings
from api.utils.logging import logger
from api.utils.s3 import (
    generate_s3_uuid,
    get_media_upload_s3_key_from_uuid,
)
from api.models import (
    PresignedUrlRequest,
    PresignedUrlResponse,
    S3FetchPresignedUrlResponse,
)

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB

router = APIRouter()


@router.post("/validate-image")
async def validate_image(file: UploadFile = File(...)):
    """
    Validate an uploaded image using a local CLIP model.
    Returns whether the image is educational (diagrams, code, charts, etc.)
    and rejects selfies, memes, NSFW, and other non-educational content.
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid image type: {file.content_type}. Allowed: png, jpeg, gif, webp.")

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="Image too large. Maximum size is 10 MB.")

    from api.utils.image_filter import classify_image
    result = classify_image(contents)

    if not result["allowed"]:
        raise HTTPException(status_code=422, detail=result["reason"])

    return result


@router.put("/presigned-url/create", response_model=PresignedUrlResponse)
async def get_upload_presigned_url(
    request: PresignedUrlRequest,
) -> PresignedUrlResponse:
    if not settings.s3_bucket_name:
        raise HTTPException(status_code=500, detail="S3 bucket name is not set")
    if not settings.s3_folder_name:
        raise HTTPException(status_code=500, detail="S3 folder name is not set")

    try:
        s3_client = boto3.client(
            "s3",
            region_name="ap-south-1",
            config=boto3.session.Config(signature_version="s3v4"),
        )

        uuid = generate_s3_uuid()
        key = get_media_upload_s3_key_from_uuid(
            uuid, request.content_type.split("/")[1]
        )

        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.s3_bucket_name,
                "Key": key,
                "ContentType": request.content_type,
            },
            ExpiresIn=600,  # URL expires in 1 hour
        )

        return {
            "presigned_url": presigned_url,
            "file_key": key,
            "file_uuid": uuid,
        }

    except ClientError as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate presigned URL")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/presigned-url/get")
async def get_download_presigned_url(
    uuid: str,
    file_extension: str,
) -> S3FetchPresignedUrlResponse:
    if not settings.s3_bucket_name:
        raise HTTPException(status_code=500, detail="S3 bucket name is not set")
    if not settings.s3_folder_name:
        raise HTTPException(status_code=500, detail="S3 folder name is not set")

    try:
        s3_client = boto3.client(
            "s3",
            region_name="ap-south-1",
            config=boto3.session.Config(signature_version="s3v4"),
        )

        key = get_media_upload_s3_key_from_uuid(uuid, file_extension)

        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.s3_bucket_name,
                "Key": key,
            },
            ExpiresIn=600,  # URL expires in 1 hour
        )

        return {"url": presigned_url}

    except ClientError as e:
        logger.error(f"Error generating download presigned URL: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to generate download presigned URL"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.post("/upload-local")
async def upload_file_locally(
    file: UploadFile = File(...), content_type: str = Form(...)
):
    try:
        # Create the folder if it doesn't exist
        os.makedirs(settings.local_upload_folder, exist_ok=True)

        # Generate a unique filename
        file_uuid = str(uuid.uuid4())
        file_extension = content_type.split("/")[1]
        filename = f"{file_uuid}.{file_extension}"
        file_path = os.path.join(settings.local_upload_folder, filename)

        # Save the file
        contents = await file.read()

        # Validate images through CLIP filter
        if content_type in ALLOWED_IMAGE_TYPES:
            from api.utils.image_filter import classify_image
            result = classify_image(contents)
            if not result["allowed"]:
                raise HTTPException(status_code=422, detail=result["reason"])

        with open(file_path, "wb") as f:
            f.write(contents)

        # Generate the URL to access the file statically
        static_url = f"/uploads/{filename}"

        return {
            "file_key": filename,
            "file_path": file_path,
            "file_uuid": file_uuid,
            "static_url": static_url,
        }

    except Exception as e:
        logger.error(f"Error uploading file locally: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to upload file locally")


@router.get("/download-local/")
async def download_file_locally(
    uuid: str,
    file_extension: str,
):
    try:
        file_path = os.path.join(
            settings.local_upload_folder, f"{uuid}.{file_extension}"
        )

        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Return the file as a response
        return FileResponse(
            path=file_path,
            filename=f"{uuid}.{file_extension}",
            media_type="application/octet-stream",
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error downloading file locally: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to download file locally")
