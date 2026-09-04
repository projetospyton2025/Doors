from app.config import BASE_DIR


def test_create_and_get_application(client, sample_payload):
    created = client.post("/api/applications", json=sample_payload)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["app_name"] == "AudioTo-txt"
    assert body["door"] == 5222
    assert body["docker"] == "Não"
    assert body["plan"] == "work"
    assert body["language"] == "Python"

    fetched = client.get(f"/api/applications/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["path"] == sample_payload["path"]


def test_list_filter_and_search(client, sample_payload):
    client.post("/api/applications", json=sample_payload)
    client.post(
        "/api/applications",
        json={
            **sample_payload,
            "app_name": "Portal",
            "path": "M:\\site",
            "door": 8080,
            "language": "HTML",
            "docker": "Sim",
            "plan": "personal",
            "nginx": "",
        },
    )
    work = client.get("/api/applications", params={"plan": "work"})
    assert work.status_code == 200
    assert work.json()["total"] == 1
    python = client.get("/api/applications", params={"language": "Python"})
    assert python.json()["total"] == 1
    docker_yes = client.get("/api/applications", params={"docker": "Sim"})
    assert docker_yes.json()["total"] == 1
    search = client.get("/api/applications", params={"q": "5222"})
    assert search.json()["total"] == 1


def test_update_and_delete_application(client, sample_payload):
    created = client.post("/api/applications", json=sample_payload).json()
    updated = client.put(
        f"/api/applications/{created['id']}",
        json={**sample_payload, "app_name": "AudioTo-txt-v2", "door": 5223},
    )
    assert updated.status_code == 200
    assert updated.json()["app_name"] == "AudioTo-txt-v2"
    assert updated.json()["door"] == 5223

    deleted = client.delete(f"/api/applications/{created['id']}")
    assert deleted.status_code == 200
    missing = client.get(f"/api/applications/{created['id']}")
    assert missing.status_code == 404


def test_duplicate_door_is_rejected(client, sample_payload):
    assert client.post("/api/applications", json=sample_payload).status_code == 201
    conflict = client.post("/api/applications", json={**sample_payload, "app_name": "Outra"})
    assert conflict.status_code == 422
    assert "porta" in conflict.json()["detail"]["message"].lower()


def test_invalid_door_is_rejected(client, sample_payload):
    invalid = client.post("/api/applications", json={**sample_payload, "door": 70000})
    assert invalid.status_code == 422


def test_dashboard_counts(client, sample_payload):
    client.post("/api/applications", json=sample_payload)
    stats = client.get("/api/dashboard")
    assert stats.status_code == 200
    body = stats.json()
    assert body["total"] == 1
    assert body["work"] == 1
    assert body["python"] == 1
    assert body["docker_yes"] == 0
    assert body["nginx_yes"] == 1


def test_pages_render(client):
    assert client.get("/").status_code == 200
    assert client.get("/applications").status_code == 200
    assert client.get("/settings").status_code == 200
    assert client.get("/health").status_code == 200


def test_create_language(client):
    created = client.post("/api/languages", json={"name": "JavaScript"})
    assert created.status_code == 201
    names = [item["name"] for item in client.get("/api/languages").json()]
    assert "JavaScript" in names
    assert "Python" in names
    assert "HTML" in names


def test_import_original_excel(client):
    xlsx = BASE_DIR / "Doors.xlsx"
    if not xlsx.exists():
        return
    with xlsx.open("rb") as handle:
        response = client.post("/api/import/xlsx", files={"file": ("Doors.xlsx", handle, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert response.status_code == 200
    assert response.json()["created"] >= 1
    listed = client.get("/api/applications", params={"q": "AudioTo-txt"})
    assert listed.json()["total"] >= 1
