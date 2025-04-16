import os
from flask import Flask, render_template, abort
from google.cloud import storage
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Get bucket name from environment variable
bucket_name = nova-staging-bucket
if not bucket_name:
    logging.error("GCS_BUCKET_NAME environment variable not set.")
    # In a real app, you might raise an exception or exit
    # For this example, we'll let it proceed but it will fail later

storage_client = None
if bucket_name:
    try:
        # Initialize the GCS client.
        # This will automatically use the service account credentials
        # attached to the VM instance if running on GCP.
        storage_client = storage.Client()
        logging.info(f"Successfully initialized GCS client for bucket: {bucket_name}")
    except Exception as e:
        logging.error(f"Failed to initialize GCS client: {e}")
        storage_client = None # Ensure client is None if init fails

@app.route('/')
def list_images():
    """Lists images from the GCS bucket and renders them."""
    if not storage_client or not bucket_name:
        abort(500, description="GCS client not initialized or bucket name missing.")

    image_urls = []
    try:
        # Get the bucket
        bucket = storage_client.get_bucket(bucket_name)

        # List blobs (objects) in the bucket
        blobs = bucket.list_blobs()

        for blob in blobs:
            # Simple check for common image types - adjust as needed
            if blob.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                # --- IMPORTANT SECURITY NOTE ---
                # Using blob.public_url requires the object to be publicly readable.
                # This is simpler for demonstration but less secure.
                # For private objects, generate Signed URLs:
                # url = blob.generate_signed_url(version="v4", expiration=timedelta(minutes=15), method="GET")
                # This requires the service account to have 'iam.serviceAccountTokenCreator' role.
                image_urls.append(blob.public_url)
                logging.info(f"Found image: {blob.name}, URL: {blob.public_url}")


    except Exception as e:
        logging.error(f"Error listing blobs in bucket '{bucket_name}': {e}")
        abort(500, description=f"Error accessing GCS bucket: {e}")

    return render_template('index.html', image_urls=image_urls, bucket_name=bucket_name)

# Create a simple template directory and file
if not os.path.exists('templates'):
    os.makedirs('templates')

# c) `templates/index.html`:** (Simple HTML page)
index_html_content = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>GCS Image Viewer</title>
    <style>
        body { font-family: sans-serif; margin: 20px; }
        h1 { color: #333; }
        .image-gallery { display: flex; flex-wrap: wrap; gap: 15px; margin-top: 20px; }
        .image-gallery img { max-width: 200px; height: auto; border: 1px solid #ccc; padding: 5px; }
        .error { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Images from GCS Bucket: {{ bucket_name }}</h1>

    {% if image_urls %}
        <div class="image-gallery">
            {% for url in image_urls %}
                <img src="{{ url }}" alt="Image from GCS">
            {% endfor %}
        </div>
    {% else %}
        <p>No images found in the bucket or unable to list images.</p>
        <p class="error">Ensure the bucket exists, contains images (.png, .jpg, .jpeg, .gif, .webp), and that the objects are publicly readable OR the application is configured to use Signed URLs with appropriate permissions.</p>
    {% endif %}
</body>
</html>
"""
with open('templates/index.html', 'w') as f:
    f.write(index_html_content)


if __name__ == '__main__':
    # Run the app on 0.0.0.0 to be accessible externally
    # Use port 8080, a common alternative HTTP port
    app.run(host='0.0.0.0', port=8080, debug=True) # Turn debug=False for production
