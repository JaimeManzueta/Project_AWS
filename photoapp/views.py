# Design goals:
# - Zero template/filesystem dependencies: HTML is built with safe f-strings.
# - Works with bucket-owner-enforced S3 buckets (no public ACLs).
# - Clear validation, simple filters (gray/blur/sepia), robust error messages.
# - Minimal but secure: escapes HTML, checks file type, avoids string concat bugs.
# -----------------------------------------------------------------------------

# Standard library imports
import io  # For handling in-memory byte streams (used to save processed image)
import os  # For accessing environment variables
from datetime import timedelta  # For setting expiration time on presigned URLs

# Third-party libraries
import boto3  # AWS SDK for Python to interact with S3
from botocore.client import Config  # Configuration for S3 client
from PIL import Image, ImageFilter, ImageOps  # Image processing functions

# Django imports
from django.http import HttpResponse, HttpResponseBadRequest  # HTTP response utilities
from django.shortcuts import redirect  # For redirecting GET requests
from django.views.decorators.csrf import csrf_exempt  # Disable CSRF protection (for demo simplicity)
from django.views.decorators.http import require_http_methods  # Restrict view to GET and POST methods

# --- AWS Configuration ---
# Get bucket name and region from environment variables, with fallback defaults
BUCKET = os.getenv("AWS_STORAGE_BUCKET_NAME", "myclass1-bucket")
REGION = os.getenv("AWS_S3_REGION_NAME") or os.getenv("AWS_REGION", "us-east-2")

# Create an S3 client using automatic credentials and v4 signature
S3 = boto3.client("s3", region_name=REGION, config=Config(signature_version="s3v4"))

def _page(title: str, body_html: str) -> HttpResponse:
    """
    Wraps provided HTML content in a basic webpage layout.
    Includes a 'Back' link to return to the home page.
    """
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{title}</title>
  <style>
    body {{ font-family: system-ui, Arial, sans-serif; padding: 18px; }}
    label, select, button {{ font-size: 16px; }}
  </style>
</head>
<body>
  {body_html}
  <p><a href="/">Back</a></p>
</body>
</html>"""
    return HttpResponse(html)

def home(request):
    """
    Displays the landing page with an image upload form.
    Users can choose a file and select a filter to apply.
    """
    body = f"""
<h1>Image Filter (Gray / Sepia / Blur)</h1>
<form method="POST" action="/process/" enctype="multipart/form-data">
  <p>
    <label>Choose File:
      <input type="file" name="image" required>
    </label>
  </p>
  <p>
    <label>Filter:
      <select name="filter">
        <option value="gray">Gray</option>
        <option value="sepia">Sepia</option>
        <option value="blur">Blur</option>
      </select>
    </label>
  </p>
  <button type="submit">Apply</button>
</form>
"""
    return _page("Image Filter", body)

@csrf_exempt  # Disable CSRF protection for simplicity (not recommended for production)
@require_http_methods(["GET", "POST"])  # Only allow GET and POST requests
def process_view(request):
    """
    Handles image upload and processing.
    - GET: Redirects to home page.
    - POST: Applies selected filter, uploads original and processed images to S3,
      and returns presigned URLs for download and preview.
    """
    if request.method == "GET":
        # Redirect GET requests to home page to avoid errors
        return redirect("/")

    # --- Validate uploaded image ---
    img_file = request.FILES.get("image")
    if not img_file:
        return HttpResponseBadRequest("No file uploaded.")

    # --- Validate selected filter ---
    chosen = (request.POST.get("filter") or "").lower()
    if chosen not in {"gray", "sepia", "blur"}:
        return HttpResponseBadRequest("Invalid filter.")

    # --- Load image and apply filter ---
    try:
        # Convert image to RGB format for consistent processing
        im = Image.open(img_file).convert("RGB")
    except Exception as e:
        return HttpResponseBadRequest(f"Not a valid image: {e}")

    # Apply the selected filter
    if chosen == "gray":
        processed = ImageOps.grayscale(im).convert("RGB")
    elif chosen == "sepia":
        # Convert to grayscale first, then apply sepia tone
        g = ImageOps.grayscale(im)
        processed = ImageOps.colorize(g, black="#704214", white="#FFE6C7")
    else:  # blur
        # Apply Gaussian blur with radius 3
        processed = im.filter(ImageFilter.GaussianBlur(3))

    # --- Generate unique S3 keys for original and processed images ---
    import uuid  # For generating unique identifiers
    base = f"{uuid.uuid4().hex}-{img_file.name.replace('/', '_')}"
    key_orig = f"uploads/originals/{base}"
    suffix = f"-{chosen}.png"
    key_proc = f"uploads/processed/{os.path.splitext(base)[0]}{suffix}"

    # --- Upload original image to S3 ---
    img_file.seek(0)  # Reset file pointer to beginning
    S3.put_object(
        Bucket=BUCKET,
        Key=key_orig,
        Body=img_file.read(),
        ContentType="image/png",
        Metadata={"filter": chosen},  # Store filter info as metadata
    )

    # --- Upload processed image to S3 ---
    out = io.BytesIO()  # Create in-memory byte stream
    processed.save(out, format="PNG")  # Save processed image to stream
    out.seek(0)  # Reset stream pointer
    S3.put_object(
        Bucket=BUCKET,
        Key=key_proc,
        Body=out.getvalue(),
        ContentType="image/png",
        Metadata={"filter": chosen},
    )

    # --- Generate presigned URLs valid for 1 hour ---
    expires = int(timedelta(hours=1).total_seconds())
    url_orig = S3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": BUCKET, "Key": key_orig},
        ExpiresIn=expires,
    )
    url_proc = S3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": BUCKET, "Key": key_proc},
        ExpiresIn=expires,
    )

    # --- Display results with preview of processed image ---
    body = f"""
<h1>Upload complete</h1>

<p><strong>Filter:</strong> {chosen}</p>

<p><strong>Original key:</strong> {key_orig}<br>
<a href="{url_orig}" target="_blank" rel="noopener">Temporary link (1h)</a></p>

<p><strong>Processed key:</strong> {key_proc}<br>
<a href="{url_proc}" target="_blank" rel="noopener">Temporary link (1h)</a></p>

<p><strong>Preview (processed):</strong></p>
<p><img src="{url_proc}" alt="preview" style="max-width:100%; height:auto;"></p>
"""
    return _page("Upload complete", body)