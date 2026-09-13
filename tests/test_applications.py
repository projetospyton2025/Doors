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
    assert client.get("/links").status_code == 200
    assert client.get("/settings").status_code == 200
    assert client.get("/health").status_code == 200


def test_list_redirect_links(client, sample_payload):
    client.post(
        "/api/applications",
        json={
            **sample_payload,
            "github": "https://github.com/example/audio",
            "drive": "https://drive.google.com/drive/folders/abc",
        },
    )
    all_links = client.get("/api/links")
    assert all_links.status_code == 200
    body = all_links.json()
    assert body["total"] == 3
    types = {item["link_type"] for item in body["items"]}
    assert types == {"remoto", "github", "drive"}

    remoto_only = client.get("/api/links", params={"link_type": "remoto"})
    assert remoto_only.status_code == 200
    assert remoto_only.json()["total"] == 1
    assert remoto_only.json()["items"][0]["url"] == sample_payload["nginx"]

    work = client.get("/api/links", params={"plan": "work", "q": "marcio"})
    assert work.json()["total"] == 1


def test_work_links_seed_not_loaded_in_test_env(client):
    # Em APP_ENV=test o seed Work não roda automaticamente
    listed = client.get("/api/applications", params={"q": "STP-Sistema"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 0


def test_satellite_conference_apps_are_rejected(client, sample_payload):
    response = client.post(
        "/api/applications",
        json={
            **sample_payload,
            "app_name": "LoteriasExtras-Conferencias-MegaSena",
            "door": 5558,
            "nginx": "",
        },
    )
    assert response.status_code == 422


def test_work_remoto_links_can_be_created(client, sample_payload):
    created = client.post(
        "/api/applications",
        json={
            **sample_payload,
            "app_name": "STP-SistemaTransportePacientes",
            "path": r"D:\projetos\python\STP-SistemaTransportePacientes",
            "door": 5022,
            "nginx": "https://marciofernandomaia.com.br/stp/",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["plan"] == "work"
    assert body["remoto"] == "https://marciofernandomaia.com.br/stp/"
    assert body["nginx"] == body["remoto"]

    links = client.get("/api/links", params={"link_type": "remoto", "q": "stp"})
    assert links.status_code == 200
    assert links.json()["total"] == 1
    assert links.json()["items"][0]["url"].endswith("/stp/")


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


def test_import_links_xlsx(client):
    from pathlib import Path
    from app.config import BASE_DIR

    links = BASE_DIR / "links.xlsx"
    if not links.exists():
        return
    with links.open("rb") as handle:
        response = client.post(
            "/api/import/xlsx",
            files={"file": ("links.xlsx", handle, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["source"] == "links.xlsx"
    assert body["total_in_file"] == 17
    assert body["created"] >= 1

    work = client.get("/api/applications", params={"plan": "work", "q": "STP-Sistema"})
    assert work.json()["total"] >= 1
    assert work.json()["items"][0]["remoto"].endswith("/stp/")

    lotteries = client.get("/api/applications", params={"plan": "lotteries", "q": "LoteriasExtras-conferencias"})
    assert lotteries.json()["total"] == 1
    assert "lotocheck" in (lotteries.json()["items"][0]["remoto"] or "")

    # filhas de conferência não entram
    child = client.get("/api/applications", params={"q": "LoteriasExtras-Conferencias-MegaSena"})
    assert child.json()["total"] == 0
