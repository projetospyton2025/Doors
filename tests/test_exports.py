def test_export_csv_and_xlsx(client, sample_payload):
    client.post("/api/applications", json=sample_payload)

    csv_response = client.get("/api/export/csv", params={"plan": "work"})
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers["content-type"]
    text = csv_response.content.decode("utf-8-sig")
    assert "APP NAME" in text
    assert "AudioTo-txt" in text
    assert "5222" in text

    xlsx_response = client.get("/api/export/xlsx")
    assert xlsx_response.status_code == 200
    assert "spreadsheetml" in xlsx_response.headers["content-type"]
    assert xlsx_response.content[:2] == b"PK"
