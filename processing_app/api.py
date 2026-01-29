from ninja import Router, Schema, File
from ninja.files import UploadedFile
from datetime import date
import os, cv2, yaml, json, natsort, threading
import cloudinary
import cloudinary.uploader
from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone

from .models import ProjectStatus
from auth_app.otp_service import send_download_link_email, send_rejection_email

processing_router = Router()

# =====================================================
# CLOUDINARY CONFIG (FROM ENV — SAFE)
# =====================================================
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# =====================================================
# SCHEMAS
# =====================================================
class StartProcessRequest(Schema):
    project_id: str

class RejectionRequest(Schema):
    image_id: str
    image_url: str

# =====================================================
# PROJECT DATASET ROOT PATHS
# =====================================================
BASE_DATASET_DIR = os.path.join(settings.BASE_DIR, "Datasets")

PROJECT_PATH_MAP = {
    "project_1": os.path.join(BASE_DATASET_DIR, "counting of animals.v1i.yolov12"),
    "project_2": os.path.join(BASE_DATASET_DIR, "Mining Vehicles.v1i.yolov12"),
    "project_3": os.path.join(BASE_DATASET_DIR, "Vehicle Detection.v1i.yolov12"),
}

OUTPUT_DIR = os.path.join(settings.BASE_DIR, "output_annotated_images")
UPLOAD_DIR = os.path.join(settings.BASE_DIR, "uploaded_files")

ALERTS_FILE = os.path.join(settings.BASE_DIR, "alerts-page.json")
PROJECTS_FILE = os.path.join(settings.BASE_DIR, "projects-page.json")
USER_MANAGEMENT = os.path.join(settings.BASE_DIR, "user_management.json")
ADMIN_MANAGEMENT = os.path.join(settings.BASE_DIR, "admin_management.json")
CLIENT_DATA = os.path.join(settings.BASE_DIR, "clients.json")
DASHBOARD_DATA = os.path.join(settings.BASE_DIR, "dashboard_data.json")
INDUSTRIES = os.path.join(settings.BASE_DIR, "industries.json")
RECENT_PROJECTS = os.path.join(settings.BASE_DIR, "recent_projects.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =====================================================
# SAFE JSON LOADER
# =====================================================
def safe_load_json(path, default):
    try:
        if os.path.exists(path):
            return json.load(open(path))
    except:
        pass
    return default

# =====================================================
# ANALYTICS GENERATOR
# =====================================================
def update_analytics_data(final_data: dict, project_id: str):
    labels, bar_values, cumulative_values = [], [], []
    pie_map, running_total = {}, 0

    for img in final_data.get("images", []):
        img_id = img.get("id", 0)
        labels.append(img_id)

        raw = img.get("_raw", {})
        count = int(raw.get("count", 0))
        classes = raw.get("classes", [])

        bar_values.append(count)
        running_total += count
        cumulative_values.append(running_total)

        for cls in classes:
            pie_map[cls] = pie_map.get(cls, 0) + 1

    analytics = {
        "barData": {"labels": labels, "values": bar_values},
        "lineData": {"labels": labels, "values": bar_values},
        "areaData": {"labels": labels, "values": cumulative_values},
        "pieData": {"labels": list(pie_map.keys()), "values": list(pie_map.values())},
        "summary": {
            "project_id": project_id,
            "total_images": len(labels),
            "total_detections": running_total,
            "generated_on": date.today().isoformat()
        }
    }

    path = os.path.join(settings.BASE_DIR, f"analytics_{project_id}.json")
    json.dump(analytics, open(path, "w"), indent=2)

# =====================================================
# MAIN PIPELINE
# =====================================================
def run_pipeline(project_id: str, dataset_path: str):
    close_old_connections()

    # deactivate all
    ProjectStatus.objects.all().update(active=False, running=False)

    # SAFE UPSERT
    status, _ = ProjectStatus.objects.update_or_create(
        project_id=project_id,
        defaults={"active": True, "running": True, "completed": False}
    )

    try:
        yaml_path = os.path.join(dataset_path, "data.yaml")
        if not os.path.exists(yaml_path):
            raise Exception(f"Missing data.yaml in {dataset_path}")

        data = yaml.safe_load(open(yaml_path))
        class_names = data["names"]

        images_dir = os.path.join(dataset_path, "train", "images")
        labels_dir = os.path.join(dataset_path, "train", "labels")

        if not os.path.exists(images_dir):
            raise Exception(f"Missing images folder: {images_dir}")

        final_data = {"project_id": project_id, "images": []}

        for idx, img_name in enumerate(natsort.natsorted(os.listdir(images_dir)), start=1):
            if not img_name.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            img_path = os.path.join(images_dir, img_name)
            label_path = os.path.join(labels_dir, os.path.splitext(img_name)[0] + ".txt")

            img = cv2.imread(img_path)
            if img is None:
                continue

            h, w = img.shape[:2]
            count = 0
            classes = set()

            if os.path.exists(label_path):
                for line in open(label_path):
                    cls, x, y, bw, bh = map(float, line.split())
                    label = class_names[int(cls)]
                    count += 1
                    classes.add(label)

                    x1 = int((x - bw / 2) * w)
                    y1 = int((y - bh / 2) * h)
                    x2 = int((x + bw / 2) * w)
                    y2 = int((y + bh / 2) * h)

                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(img, label, (x1, max(20, y1 - 5)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            out_path = os.path.join(OUTPUT_DIR, f"{project_id}_{img_name}")
            cv2.imwrite(out_path, img)

            upload = cloudinary.uploader.upload(out_path)

            final_data["images"].append({
                "id": idx,
                "mainImage": upload["secure_url"],
                "metrics": [
                    {"label": "Total Objects", "value": str(count)},
                    {"label": "Detected Classes", "value": ", ".join(classes) if classes else "None"}
                ],
                "_raw": {"count": count, "classes": list(classes)}
            })

        json.dump(final_data, open(os.path.join(settings.BASE_DIR, f"result_{project_id}.json"), "w"), indent=2)
        update_analytics_data(final_data, project_id)

        status.completed = True

    except Exception as e:
        json.dump({"error": str(e)}, open(os.path.join(settings.BASE_DIR, f"result_{project_id}.json"), "w"))

    finally:
        status.running = False
        status.active = True
        status.save()

# =====================================================
# API ROUTES
# =====================================================
@processing_router.post("/start-processing", tags=["PROJECT PROCESSING API'S"])
def start_processing(request, data: StartProcessRequest):
    dataset_path = PROJECT_PATH_MAP.get(data.project_id)
    if not dataset_path:
        return {"error": "Invalid project_id"}

    if not os.path.exists(dataset_path):
        return {"error": f"Dataset not found: {dataset_path}"}

    threading.Thread(target=run_pipeline, args=(data.project_id, dataset_path), daemon=True).start()
    return {"message": f"Processing started for {data.project_id}"}

@processing_router.get("/get-result", response={200: dict}, tags=["PROJECT PROCESSING API'S"])
def get_result(request):
    status = ProjectStatus.objects.filter(active=True).first()
    if not status:
        return {"processing": False, "images": []}

    if status.running:
        return {"processing": True, "images": []}

    path = os.path.join(settings.BASE_DIR, f"result_{status.project_id}.json")
    return safe_load_json(path, {"processing": False, "images": []})

@processing_router.get("/get-analytics", response={200: dict}, tags=["PROJECT PROCESSING API'S"])
def get_analytics(request):
    status = ProjectStatus.objects.filter(active=True).first()
    if not status:
        return {}

    path = os.path.join(settings.BASE_DIR, f"analytics_{status.project_id}.json")
    return safe_load_json(path, {})

# =====================================================
# FILE UPLOAD & REJECT
# =====================================================
@processing_router.post("/upload-file", tags=["FILE UPLOAD,REJECT API"])
def upload_file(request, file: UploadedFile = File(...)):
    upload = cloudinary.uploader.upload(file.file, resource_type="raw")
    send_download_link_email(upload["secure_url"])
    return {"status": "success", "download_link": upload["secure_url"]}

@processing_router.post("/reject-image", tags=["FILE UPLOAD,REJECT API"])
def reject_image(request, data: RejectionRequest):
    send_rejection_email(data.image_id, data.image_url)
    return {"status": "success"}

# =====================================================
# STATIC JSON APIs
# =====================================================
@processing_router.get("/get-alerts")
def get_alerts(request): return _load_json(ALERTS_FILE)

@processing_router.get("/get-projects")
def get_projects(request): return _load_json(PROJECTS_FILE)

@processing_router.get("/user-management")
def user_management(request): return _load_json(USER_MANAGEMENT)

@processing_router.get("/admin-management")
def admin_management(request): return _load_json(ADMIN_MANAGEMENT)

@processing_router.get("/dashboard-data")
def dashboard_data(request): return _load_json(DASHBOARD_DATA)

@processing_router.get("/client-data")
def client_data(request): return _load_json(CLIENT_DATA)

@processing_router.get("/industries")
def industries(request): return _load_json(INDUSTRIES)

@processing_router.get("/recent-projects")
def recent_projects(request): return _load_json(RECENT_PROJECTS)
