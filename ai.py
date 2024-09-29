# Import the list in this file
import base64
import os
import plotly.graph_objects as go
import json
import requests
from pathlib import Path
from openai import OpenAI
from tavily import TavilyClient
from user_questions import user_questions
from ocr_prompt_template import ocr_prompt
from dotenv import load_dotenv


# Function to gather user context and create a system prompt
def create_system_prompt_with_user_context():
    user_context = {}
    for question in user_questions:
        response = input(question + " ")
        user_context[question] = response

    system_prompt = "You are an AI assistant specialized in health and fitness advice. Here's the user's context:\n\n"

    for question, answer in user_context.items():
        system_prompt += f"- {question} {answer}\n"

    system_prompt += "\nPlease use this information to provide personalized and relevant advice to the user's questions."

    return system_prompt


# Function to extract OCR content from an image
def get_ocr_content(image_path):
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "API key for OpenAI is not set. Please set the OPENAI_API_KEY environment variable."
        )

    with Path(image_path).open("rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        image_url = f"data:image/jpeg;base64,{base64_image}"

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": ocr_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                        },
                    },
                ],
            }
        ],
    )

    json_content = response.choices[0].message.content
    extracted_info = format_extracted_info(
        json_content
    )  # New function to format the output

    return extracted_info  # Return the formatted string


def format_extracted_info(json_content):
    import json

    data = json.loads(json_content.strip("```json"))  # Parse the JSON string
    # Create a user-friendly string from the JSON data
    info_string = "Extracted Nutrient Information:\n\n"
    info_string += "Ingredients:\n"

    for ingredient in data.get("Ingredients", []):
        info_string += f"- {ingredient}\n"

    info_string += "\n"
    info_string += "Nutrient Information:\n"

    energy_info = data.get("Nutrient Information", {}).get("Energy", "Not specified")
    info_string += f"Energy: {energy_info}\n\n"

    info_string += "Macro Nutrients:\n"
    for nutrient, amount in (
        data.get("Nutrient Information", {}).get("Macro Nutrients", {}).items()
    ):
        info_string += f"{nutrient}: {amount}\n"

    info_string += "\nMicro Nutrients:\n"
    for nutrient, amount in (
        data.get("Nutrient Information", {}).get("Micro Nutrients", {}).items()
    ):
        info_string += f"{nutrient}: {amount}\n"

    info_string += "\n"
    info_string += "Other Information:\n"

    for info in data.get("Other Information", []):
        info_string += f"- {info}\n"

    return info_string.strip()  # Return the formatted string


def plot_nutrient_info(extracted_info):
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    plot_prompt_template = """
    Given the string:
    {}

    Extract the nutrient information and format it as JSON. The output should follow this structure:
    {{
        "Macro Nutrients": {{
            "Macro Nutrient 1": "Amount",
            // All macro nutrients from the string
        }},
        "Micro Nutrients": {{
            "Micro Nutrient 1": "Amount",
            // All micro nutrients from the string
        }}
    }}

    Only provide the numerical values, without mentioning the unit of measurement.
    Ensure the output is valid JSON.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": plot_prompt_template.format(extracted_info)}
        ],
    )

    # Parse the response to get macro and micro nutrients
    nutrient_data = response.choices[0].message.content
    nutrient_data = json.loads(nutrient_data.strip("```json"))
    macro_nutrients = nutrient_data.get("Macro Nutrients", {})
    micro_nutrients = nutrient_data.get("Micro Nutrients", {})

    # Create pie charts
    fig = go.Figure()

    # Add macro nutrients pie chart
    fig.add_trace(
        go.Pie(
            labels=list(macro_nutrients.keys()),
            values=list(macro_nutrients.values()),
            name="Macro Nutrients",
            domain=dict(x=[0, 0.5]),
            textinfo="label+value",  # Display labels and actual values
        )
    )

    # Add micro nutrients pie chart
    fig.add_trace(
        go.Pie(
            labels=list(micro_nutrients.keys()),
            values=list(micro_nutrients.values()),
            name="Micro Nutrients",
            domain=dict(x=[0.5, 1]),
            textinfo="label+value",  # Display labels and actual values
        )
    )

    # Update layout to show both charts side by side with custom annotations
    fig.update_layout(
        title_text="Nutrient Distribution",
        annotations=[
            dict(
                text="Macro Nutrients in g",
                x=0.25,
                y=1.1,
                font_size=20,
                showarrow=False,
            ),
            dict(
                text="Micro Nutrients in mg",
                x=0.75,
                y=-0.1,
                font_size=20,
                showarrow=False,
            ),
        ],
    )

    # Save the figure
    fig.write_image(
        "nutrient_distribution.png", width=1200, height=600
    )  # Adjust size if needed

    return nutrient_data  # Return the nutrient data if needed


def answer_query(query, user_context, food_info):
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    client = OpenAI(api_key=api_key)
    tavily_client = TavilyClient(api_key=tavily_api_key)

    # Ask GPT-4 if additional information is needed
    system_message = f"You are an AI assistant. Determine if given query requires current information from an external source to be answered accurately. User context: {user_context}, food info: {food_info}"
    user_message = f"Query: {query}\nDoes this query require information from an external source to be answered accurately and precisely? Respond with 'Yes' or 'No' only. Try to get information from the internet in most cases by responding 'Yes'."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
    )

    needs_additional_info = response.choices[0].message.content.strip().lower() == "yes"

    context = ""
    if needs_additional_info:
        context = tavily_client.get_search_context(query=query)

    # Generate the final answer using GPT-4
    system_message = f"You are an AI assistant. Provide a concise and accurate answer to the query based on your knowledge and the additional context if provided. User context: {user_context}, food info: {food_info}. Make the output tailored to the user context and food info by using the values from the food info."
    user_message = f"Query: {query}\n{context}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content.strip()


def main():
    extracted_info = get_ocr_content("coke.jpg")
    # plot_nutrient_info(extracted_info)
    # query = "Harmful effects that each ingredient has on the human body"
    # result = answer_query(query, None, extracted_info)
    print(extracted_info)


if __name__ == "__main__":
    main()
