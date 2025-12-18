from app.clients.google_sheets import sheets_client

class GroupClassesClient:
    SHEET_NAME = "group_classes"

    async def get_all(self):
        return await sheets_client._load_departments(self.SHEET_NAME)

    async def get_classes_by_club(self, club_name: str):
        all_classes = await self.get_all()
        return [row["Name"] for row in all_classes if row.get(club_name) == "Да"]

    async def get_clubs_by_class(self, class_name: str):
        all_classes = await self.get_all()
        for row in all_classes:
            if row.get("Name", "").lower() == class_name.lower():
                return [k for k, v in row.items() if k not in {"Name","description","Time","paid"} and v == "Да"]
        return []

group_classes_client = GroupClassesClient()