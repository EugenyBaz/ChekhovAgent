import pytest
from app.clients.google_sheets import sheets_client

@pytest.mark.asyncio
async def test_find_department_live():
    result = await sheets_client.find_department("Chekhov Sport")
    print(result)
    assert result is not None
