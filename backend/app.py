from flask import Flask, request, jsonify
import edgedb
import openai
import asyncio
import json
from story_teller import StoryTeller

app = Flask(__name__)

client = edgedb.create_client()
story_agent = StoryTeller()


def fire_and_forget(f):
    def wrapped(*args, **kwargs):
        return asyncio.get_event_loop().run_in_executor(None, f, *args, *kwargs)

    return wrapped

@fire_and_forget
def generate_story_async(story_params):
    generated_story = story_agent.gen_story_with_image(story_params)
    client.query(
        """
        UPDATE Story
        FILTER .id = <uuid>$story_id
        SET {
            content := <json>$content,
            is_success := true
        }
        """,
        story_id=story_params["story_id"],
        content=json.dumps(generated_story, indent=4)
    )


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

    generate_and_save_story(story_insertion[0].id, age, art_style, length, core_value, char_species, context)
    
    return jsonify({"id": str(story_insertion[0].id)})

def generate_and_save_story(
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
    generate_story_async(story_params)



@app.route("/ready_status", methods=["GET"])
async def ready_status():
    story_id = request.args.get("id")
    result = client.query_single(
        """
        SELECT EXISTS (
            SELECT Story
            FILTER .id = <uuid>$story_id AND .is_success = true
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
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run())
