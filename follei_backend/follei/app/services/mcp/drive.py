from app.core.ids import short_id


def upload(filename: str, content: str, folder_id: str | None = None) -> dict:
    file_id = str(short_id())
    return {"file_id": file_id, "filename": filename, "folder_id": folder_id, "url": f"https://drive.example.com/{file_id}", "uploaded": True}


def list_files(folder_id: str | None = None, query: str | None = None) -> dict:
    return {"files": [{"id": str(short_id()), "name": "proposal.pdf", "mime_type": "application/pdf", "folder_id": folder_id, "query": query}]}
