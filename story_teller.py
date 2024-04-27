from openai import OpenAI
import json


class StoryTeller:
    def __init__(self, system_prompt=None):
        """
        :param system_prompt: prompt related to the attribute of the agent
        """
        self.client = OpenAI()
        self.model = {
            "text_model": "gpt-4-turbo",
            "image_model": "dall-e-3"
        }

        self.system_prompt_template = """
You are a children story teller. Your story is engaging and simple to understand, and it should revolve around a core value, and have satisfying ending. The main character should be non-human, such as but not limited to little bunny, tiger or hamster, whose name is not Timmy. You will generated a detailed description of the main character to use in image generating prompt. You group your story in sections of natural progression, each section should have a prompt for AI to generate relevant illustration of this section. The story should have a relevant title, and it should have some key takeaway for the kid. The result should be in the following JSON format:

      {
        "title" : "<title>",
        "character":"<detailed description of the main character to use in prompt>"
        "story": [
          {
            "section": "<generated story section>",
            "prompt": "<prompt to generate relevant image for this section>"
          },
          {...}
        ],
        "summary":"<summary of this story>"
      }
      
      Please do not generate any numbers
      """

    def _get_text_prompt(self, length, age_range, value, char_species):
        return f"Tell a story about {length} minutes in length, for a {age_range} year old kid as target audience, with core value of {value}. The main character of the story is a {char_species}"

    def _get_image_prompt(self, image_style, image_content, char_des, char_species):
        return f"Image requirement: Family friendly, lively and colorful, fits for a kid's attention in the style of {image_style}. Please generate pure image and no text anywhere. Characters should always be non-human!!! Main charactor should have the following characteristics: species is {char_species}.  {char_des}, Image content: {image_content}"

    def gen_story_with_image(self, params):
        length = params['story_length']
        age_range = params['age_range']
        value = params['value']
        image_style = params['image_style']
        story_id = params['story_id']
        char_species = params['char_species']

        # first call the text_model to return the story text
        story_text_response = self.client.chat.completions.create(
            model=self.model['text_model'],
            messages=[
                {"role": "system", "content": self.system_prompt_template},
                {"role": "user", "content": self._get_text_prompt(length, age_range, value, char_species)}
            ],
            temperature=1.0
        )

        story_text = story_text_response.choices[0].message.content
        story_text_json = json.loads(story_text)

        section_results = []
        for sec_id, section in enumerate(story_text_json["story"]):
            if sec_id < length:
                section_text = section["section"]
                session_image_prompt = section["prompt"]
                char_des = story_text_json["character"]

                image_prompt = self._get_image_prompt(image_style, session_image_prompt, char_des, char_species)

                story_image_response = self.client.images.generate(
                    model=self.model["image_model"],
                    prompt=image_prompt + session_image_prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )
                section_image_url = story_image_response.data[0].url

                section_return_result = {
                    "section_id": sec_id,
                    "section_text": section_text,
                    "section_image_url": section_image_url
                }
                section_results.append(section_return_result)

        story_return_results = {
            "story_id": story_id,
            "story_main_character": story_text_json["character"],
            "main_character_species": story_text_json["character"],
            "story_title": story_text_json["title"],
            "story_summary": story_text_json["summary"],
            "sections": section_results
        }
        return story_return_results


if __name__ == "__main__":
    story_params = {
        "story_id": 1,
        "theme": "train",
        "age_range": "3-7",
        "art": "cartoon",
        "image_style": "japanese animation",
        "value": "honesty",
        "story_length": 5,
        "char_species": "turtle"
    }
    story_agent = StoryTeller()
    story = story_agent.gen_story_with_image(story_params)
    pretty_json = json.dumps(story, indent=4)
    print(pretty_json)
