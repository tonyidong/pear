from flask import Flask, request, jsonify
import edgedb
import openai
import asyncio
import json
from story_teller import StoryTeller

app = Flask(__name__)

client = edgedb.create_client()
story_agent = StoryTeller()

async def generate_story_async(story_params):
    print("before")
    generated_story = story_agent.gen_story_with_image(story_params)
    client.query(
        """
        UPDATE Story
        FILTER .id = <uuid>$story_id
        SET {
            content := <json>$content
        }
        """,
        story_id=story_params["story_id"],
        content=json.dumps(generated_story, indent=4)
    )
    print("after")


@app.route("/generate_story", methods=["POST"])
async def generate_story():
    age = request.form["age"]
    art_style = request.form["art_style"]
    length = int(request.form["length"])
    core_value = request.form["core_value"]
    char_species = request.form["char_species"]
    context = request.form["context"]

    story_insertion = client.query("""
    SELECT (
        INSERT Story {
            is_success := false
        }
    ) {
        id,
    }
    """)

    asyncio.create_task(
        generate_and_save_story(story_insertion[0].id, age, art_style, length, core_value, char_species, context)
    )

    return jsonify({"id": str(story_insertion[0].id)})


async def generate_and_save_story(
    story_id, age, art_style, length, core_value, char_species, context
):
    story_params = {
        "story_id": story_id,
        # "theme": "train",
        "age_range": age,
        "image_style": art_style,
        "value": core_value,
        "story_length": length,
        "char_species": char_species
    }
    await generate_story_async(story_params)



@app.route("/ready_status", methods=["GET"])
async def ready_status():
    story_id = request.args.get("id")
    result = client.query_single(
        """
        SELECT EXISTS (
            SELECT Story
            FILTER .id = <uuid>$story_id AND NOT .content = <json>{}
        )
        """,
        story_id=story_id,
    )
    return jsonify({"ready": result})


@app.route("/get_story", methods=["GET"])
async def get_story():
    story_id = request.args.get("id")
    story = client.query_single(
        """
        SELECT Story {
            id,
            year_range,
            style,
            length_in_min,
            core_value,
            summary,
            content
        }
        FILTER .id = <uuid>$story_id
        """,
        story_id=story_id,
    )
    if story:
        return jsonify(
            {
                "id": str(story.id),
                "age": story.year_range,
                "art_style": story.style,
                "length": story.length_in_min,
                "core_value": story.core_value,
                "summary": story.summary,
                "content": story.content,
            }
        )
    else:
        return jsonify({"error": "Story not found"})


if __name__ == "__main__":
    app.run()
