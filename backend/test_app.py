import pytest
from app import app, client
import asyncio
import json


@pytest.fixture
async def client():
    async with app.test_client() as client:
        yield client


@pytest.mark.asyncio
async def test_generate_story(client):
    data = {
        "age": "adult",
        "art_style": "realistic",
        "length": 100,
        "core_value": "friendship",
        "context": "A story about two friends on an adventure",
    }
    response = await client.post("/generate_story", data=data)
    assert response.status_code == 200
    json_data = await response.get_json()
    assert "id" in json_data


@pytest.mark.asyncio
async def test_ready_status(client):
    # Generate a story first
    data = {
        "age": "adult",
        "art_style": "realistic",
        "length": 100,
        "core_value": "friendship",
        "context": "A story about two friends on an adventure",
    }
    response = await client.post("/generate_story", data=data)
    json_data = await response.get_json()
    story_id = json_data["id"]

    # Check ready status
    response = await client.get(f"/ready_status?id={story_id}")
    assert response.status_code == 200
    json_data = await response.get_json()
    assert "ready" in json_data


@pytest.mark.asyncio
async def test_get_story(client):
    # Generate a story first
    data = {
        "age": "adult",
        "art_style": "realistic",
        "length": 100,
        "core_value": "friendship",
        "context": "A story about two friends on an adventure",
    }
    response = await client.post("/generate_story", data=data)
    json_data = await response.get_json()
    story_id = json_data["id"]

    # Wait for the story to be generated
    while True:
        response = await client.get(f"/ready_status?id={story_id}")
        json_data = await response.get_json()
        if json_data["ready"]:
            break
        await asyncio.sleep(1)

    # Get the story
    response = await client.get(f"/get_story?id={story_id}")
    assert response.status_code == 200
    json_data = await response.get_json()
    assert "id" in json_data
    assert "age" in json_data
    assert "art_style" in json_data
    assert "length" in json_data
    assert "core_value" in json_data
    assert "context" in json_data
    assert "content" in json_data
