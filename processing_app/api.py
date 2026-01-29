from ninja import Router, Schema, File
from ninja.files import UploadedFile
from datetime import date
import os, cv2, yaml, json, natsort, threading
import cloudinary
import cloudinary.uploader
from django.conf import settings
from django.db import close_old_connections

from .models import ProjectStatus
from auth_app.otp_service import send_download_link_email, send_rejection_email

processing_router = Router()

# =====================================================
# CLOUDINARY CONFIG
# =====================================================
cloudinary.config(
    cloud_name="dsy9rpwns",
    api_key="621215564975399",
    api_secret="cwayWSta4ldFBmACVKobPkTWu7Q"
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
PROJECT_PATH_MAP = {
    "project_1": r"C:\Users\Sai Kishore\OneDrive\Desktop\AA\django_fastapi_hybrid\Datasets\counting of animals.v1i.yolov12",
    "project_2": r"C:\Users\Sai Kishore\OneDrive\Desktop\AA\django_fastapi_hybrid\Datasets\Mining Vehicles.v1i.yolov12",
    "project_3": r"C:\Users\Sai Kishore\OneDrive\Desktop\AA\django_fastapi_hybrid\Datasets\Vehicle Detection.v1i.yolov12"
}

OUTPUT_DIR = "output_annotated_images"
UPLOAD_DIR = "uploaded_files"

ALERTS_FILE = "alerts-page.json"
PROJECTS_FILE = "projects-page.json"
USER_MANAGEMENT = "user_management.json"
ADMIN_MANAGEMENT = "admin_management.json"
CLIENT_DATA = "clients.json"
DASHBOARD_DATA = "dashboard_data.json"
INDUSTRIES = "industries.json"
RECENT_PROJECTS = "recent_projects.json"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =====================================================
# ANALYTICS GENERATOR
# =====================================================
def update_analytics_data(final_data: dict, project_id: str):

    labels = []
    bar_values = []
    cumulative_values = []
    pie_map = {}
    running_total = 0

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
        "pieData": {
            "labels": list(pie_map.keys()),
            "values": list(pie_map.values())
        },
        "gallery": final_data.get("images", []),
        "summary": {
            "project_id": project_id,
            "total_images": len(labels),
            "total_detections": running_total,
            "generated_on": date.today().isoformat()
        }
    }

    path = os.path.join(settings.BASE_DIR, f"analytics_{project_id}.json")
    with open(path, "w") as f:
        json.dump(analytics, f, indent=2)

# =====================================================
# MAIN PIPELINE (THREAD SAFE)
# =====================================================
def run_pipeline(project_id: str, dataset_path: str):

    close_old_connections()  # 🔥 CRITICAL FOR THREADS

    # deactivate previous projects
    ProjectStatus.objects.all().update(active=False, running=False)

    status = ProjectStatus.objects.create(
        project_id=project_id,
        active=True,
        running=True,
        completed=False
    )

    try:
        with open(os.path.join(dataset_path, "data.yaml")) as f:
            data = yaml.safe_load(f)

        class_names = data["names"]
        images_dir = os.path.join(dataset_path, "train", "images")
        labels_dir = os.path.join(dataset_path, "train", "labels")

        final_data = {"project_id": project_id, "images": []}
        today = date.today().isoformat()

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
                with open(label_path) as f:
                    for line in f:
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
                "cardTitle": f"Detection Result #{idx}",
                "sectionTitle": "Object Statistics",
                "meta": {
                    "date": today,
                    "location": "Processing Lab"
                },
                "metrics": [
                    {"label": "Total Objects", "value": str(count)},
                    {"label": "Detected Classes", "value": ", ".join(classes) if classes else "None"}
                ],
                "_raw": {
                    "count": count,
                    "classes": list(classes)
                }
            })

        # save result
        with open(os.path.join(settings.BASE_DIR, f"result_{project_id}.json"), "w") as f:
            json.dump(final_data, f, indent=2)

        update_analytics_data(final_data, project_id)

        status.completed = True

    except Exception as e:
        with open(os.path.join(settings.BASE_DIR, f"result_{project_id}.json"), "w") as f:
            json.dump({"error": str(e)}, f)

    finally:
        status.running = False
        status.active = True
        status.save()

# =====================================================
# START PROCESSING
# =====================================================
@processing_router.post("/start-processing", tags=["PROJECT PROCESSING API'S"])
def start_processing(request, data: StartProcessRequest):

    dataset_path = PROJECT_PATH_MAP.get(data.project_id)
    if not dataset_path:
        return 404, {"error": "Invalid project_id"}

    threading.Thread(
        target=run_pipeline,
        args=(data.project_id, dataset_path),
        daemon=True
    ).start()

    return {"message": f"Processing started for {data.project_id}"}

# =====================================================
# GET RESULT
# =====================================================
@processing_router.get("/get-result", tags=["PROJECT PROCESSING API'S"])
def get_result(request):

    status = ProjectStatus.objects.filter(active=True).first()
    if not status:
        return {"processing": False, "images": []}

    if status.running:
        return {
            "processing": True,
            "images": [{
                "id": 0,
                "mainImage": "https://via.placeholder.com/600x400?text=Processing",
                "cardTitle": "Processing",
                "sectionTitle": "Please wait",
                "meta": {"date": "", "location": ""},
                "metrics": []
            }]
        }

    path = os.path.join(settings.BASE_DIR, f"result_{status.project_id}.json")
    if not os.path.exists(path):
        return {"processing": False, "images": []}

    return json.load(open(path))

# =====================================================
# GET ANALYTICS
# =====================================================
@processing_router.get("/get-analytics", tags=["PROJECT PROCESSING API'S"])
def get_analytics(request):

    import random

    status = ProjectStatus.objects.filter(active=True).first()

    safe = {
        "barData": [],
        "pieData": [],
        "areaData": [],
        "lineData": []
    }

    if not status:
        return safe

    path = os.path.join(settings.BASE_DIR, f"analytics_{status.project_id}.json")
    if not os.path.exists(path):
        return safe

    with open(path) as f:
        a = json.load(f)

    # BAR
    barData = []
    for label, value in zip(a["barData"]["labels"], a["barData"]["values"]):
        barData.append({"name": f"Image {label}", "Total": value, "Images": 1})

    # PIE
    pieData = []
    colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"]
    for i, (label, value) in enumerate(zip(a["pieData"]["labels"], a["pieData"]["values"])):
        pieData.append({"name": label, "value": value, "color": colors[i % len(colors)]})

    # AREA
    areaData = []
    for i, total in enumerate(a["areaData"]["values"]):
        areaData.append({
            "name": f"Batch {i+1}",
            "Elephant": random.randint(0, total),
            "Deer": random.randint(0, total),
            "Zebra": random.randint(0, total)
        })

    # LINE
    lineData = []
    for i, val in enumerate(a["lineData"]["values"]):
        lineData.append({
            "name": f"Run {i+1}",
            "Detections": val,
            "Confidence": random.randint(85, 98)
        })

    return {
        "barData": barData,
        "pieData": pieData,
        "areaData": areaData,
        "lineData": lineData
    }

# =====================================================
# FILE UPLOAD
# =====================================================
@processing_router.post("/upload-file", tags=["FILE UPLOAD,REJECT API"])
def upload_file(request, file: UploadedFile = File(...)):
    upload = cloudinary.uploader.upload(file.file, resource_type="raw")
    send_download_link_email(upload["secure_url"])
    return {"status": "success", "download_link": upload["secure_url"]}

# =====================================================
# REJECT IMAGE
# =====================================================
@processing_router.post("/reject-image", tags=["FILE UPLOAD,REJECT API"])
def reject_image(request, data: RejectionRequest):
    send_rejection_email(data.image_id, data.image_url)
    return {"status": "success"}

# =====================================================
# STATIC JSON APIs
# =====================================================
def _load_json(path):
    return json.load(open(path)) if os.path.exists(path) else []
# =====================================================
# STATIC JSON APIs
# =====================================================
def _load_json(path):
    return json.load(open(path)) if os.path.exists(path) else []

@processing_router.get("/get-alerts", tags=["ALERT API'S"])
def get_alerts(request): return _load_json(ALERTS_FILE)

@processing_router.get("/get-projects", tags=["PROJECT API'S"])
def get_projects(request): return _load_json(PROJECTS_FILE)

@processing_router.get("/user-management", tags=[" MANAGEMENT API'S"])
def user_management(request): return _load_json(USER_MANAGEMENT)

@processing_router.get("/admin-management", tags=[" MANAGEMENT API'S"])
def admin_management(request): return _load_json(ADMIN_MANAGEMENT)

@processing_router.get("/dashboard-data", tags=[" DASHBOARD API'S"])
def dashboard_data(request): return _load_json(DASHBOARD_DATA)

@processing_router.get("/client-data", tags=[" DASHBOARD API'S"])
def client_data(request): return _load_json(CLIENT_DATA)

@processing_router.get("/industries", tags=[" DASHBOARD API'S"])
def industries(request): return _load_json(INDUSTRIES)

@processing_router.get("/recent-projects", tags=[" DASHBOARD API'S"])
def recent_projects(request): return _load_json(RECENT_PROJECTS)
