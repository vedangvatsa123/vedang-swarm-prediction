"""
Project persistence — stores each project as a folder with JSON metadata.
No external database required.
"""
import os
import json
import uuid
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..config import Settings


PROJECTS_ROOT = os.path.join(Settings.UPLOAD_DIR, "projects")


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _proj_dir(pid: str) -> str:
    return os.path.join(PROJECTS_ROOT, pid)


def _meta_path(pid: str) -> str:
    return os.path.join(_proj_dir(pid), "meta.json")


def _files_dir(pid: str) -> str:
    return os.path.join(_proj_dir(pid), "files")


def create_project(name: str = "Untitled") -> Dict[str, Any]:
    _ensure_dir(PROJECTS_ROOT)
    pid = f"proj_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat() + "Z"
    meta = {
        "project_id": pid,
        "name": name,
        "status": "created",
        "created_at": now,
        "updated_at": now,
        "files": [],
        "ontology": None,
        "analysis_summary": None,
        "prediction_goal": None,
        "error": None,
    }
    _ensure_dir(_proj_dir(pid))
    _ensure_dir(_files_dir(pid))
    _save_meta(pid, meta)
    return meta


def _save_meta(pid: str, meta: Dict[str, Any]):
    meta["updated_at"] = datetime.utcnow().isoformat() + "Z"
    with open(_meta_path(pid), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def load_project(pid: str) -> Optional[Dict[str, Any]]:
    mp = _meta_path(pid)
    if not os.path.exists(mp):
        return None
    with open(mp, "r", encoding="utf-8") as f:
        return json.load(f)


def update_project(pid: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    meta = load_project(pid)
    if meta is None:
        raise FileNotFoundError(f"Project {pid} not found")
    meta.update(updates)
    _save_meta(pid, meta)
    return meta


def delete_project(pid: str) -> bool:
    d = _proj_dir(pid)
    if not os.path.exists(d):
        return False
    shutil.rmtree(d)
    return True


def list_projects(limit: int = 50) -> List[Dict[str, Any]]:
    _ensure_dir(PROJECTS_ROOT)
    projects = []
    for entry in os.listdir(PROJECTS_ROOT):
        meta = load_project(entry)
        if meta:
            projects.append(meta)
    projects.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    return projects[:limit]


def save_uploaded_file(pid: str, file_storage, original_name: str) -> Dict[str, Any]:
    """Save an uploaded file into the project's files directory."""
    fd = _files_dir(pid)
    _ensure_dir(fd)
    ext = os.path.splitext(original_name)[1].lower()
    safe_name = f"{uuid.uuid4().hex[:8]}{ext}"
    dest = os.path.join(fd, safe_name)
    file_storage.save(dest)
    return {
        "original_name": original_name,
        "saved_name": safe_name,
        "path": dest,
        "size": os.path.getsize(dest),
    }


def save_extracted_text(pid: str, text: str):
    with open(os.path.join(_proj_dir(pid), "full_text.txt"), "w", encoding="utf-8") as f:
        f.write(text)


def get_extracted_text(pid: str) -> Optional[str]:
    p = os.path.join(_proj_dir(pid), "full_text.txt")
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def get_project_files(pid: str) -> List[str]:
    fd = _files_dir(pid)
    if not os.path.exists(fd):
        return []
    return [os.path.join(fd, f) for f in os.listdir(fd) if os.path.isfile(os.path.join(fd, f))]
