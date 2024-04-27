from flask import Flask, request, jsonify
import edgedb
import openai
import asyncio

app = Flask(__name__)

# Initialize EdgeDB client
client = edgedb.create_async_client()

# Define the EdgeDB schema
schema = """
    type Story {
        required property id -> uuid {
            default := uuid_generate_v1mc()
        }
        required property age -> str;
        required property art_style -> str;
        required property length -> int64;
        required property core_value -> str;
        required property context -> str;
        property content -> str;
    }
"""


# Create the EdgeDB schema
async def create_schema():
    async with client.transaction():
        await client.execute(schema)


openai.api_key = "YOUR_API_KEY"


async def generate_story_async(age, art_style, length, core_value, context):
    prompt = f"Generate a story with the following parameters:\nAge: {age}\nArt Style: {art_style}\nLength: {length} words\nCore Value: {core_value}\nContext: {context}"
    response = await openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=length,
        n=1,
        stop=None,
        temperature=0.7,
    )
    return response.choices[0].text.strip()


@app.route("/generate_story", methods=["POST"])
async def generate_story():
    age = request.form["age"]
    art_style = request.form["art_style"]
    length = int(request.form["length"])
    core_value = request.form["core_value"]
    context = request.form["context"]

    story_id = await client.query(
        """
        INSERT Story {
            age := <str>$age,
            art_style := <str>$art_style,
            length := <int64>$length,
            core_value := <str>$core_value,
            context := <str>$context
        }
        """,
        age=age,
        art_style=art_style,
        length=length,
        core_value=core_value,
        context=context,
    )

    asyncio.create_task(
        generate_and_save_story(story_id, age, art_style, length, core_value, context)
    )

    return jsonify({"id": str(story_id)})


async def generate_and_save_story(
    story_id, age, art_style, length, core_value, context
):
    generated_story = await generate_story_async(
        age, art_style, length, core_value, context
    )
    await client.query(
        """
        UPDATE Story
        SET {
            content := <str>$content
        }
        FILTER .id = <uuid>$story_id
        """,
        story_id=story_id,
        content=generated_story,
    )


@app.route("/ready_status", methods=["GET"])
async def ready_status():
    story_id = request.args.get("id")
    result = await client.query_single(
        """
        SELECT EXISTS (
            SELECT Story
            FILTER .id = <uuid>$story_id AND .content IS NOT NULL
        )
        """,
        story_id=story_id,
    )
    return jsonify({"ready": result})


@app.route("/get_story", methods=["GET"])
async def get_story():
    story_id = request.args.get("id")
    story = await client.query_single(
        """
        SELECT Story {
            id,
            age,
            art_style,
            length,
            core_value,
            context,
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
                "age": story.age,
                "art_style": story.art_style,
                "length": story.length,
                "core_value": story.core_value,
                "context": story.context,
                "content": story.content,
            }
        )
    else:
        return jsonify({"error": "Story not found"})


if __name__ == "__main__":
    asyncio.run(create_schema())
    app.run()
