ocr_prompt = """
Extract comprehensive nutrient information and ingredients from the food product label image in a structured JSON format. Ensure to include the unit of measurement for each nutrient and specify the values based on the label's reference (e.g., per ml, per g). The extraction should accommodate any number of macro and micro nutrients present. Please provide only the JSON output to avoid any decoding errors.
Example Output Format:
{
    "Ingredients": ["Ingredient 1", "Ingredient 2", "Ingredient 3"],
    "Nutrient Information": {
        "Energy": "Amount of energy (kcal) per as mentioned on the label",
        "Macro Nutrients": {
            "Amount of Macro Nutrient": "Amount based per ml or per g as mentioned on the label"
            // Include any number of additional macro nutrients as needed
        },
        "Micro Nutrients": {
            "Amount of Micro Nutrient": "Amount based per ml or per g as mentioned on the label"
            // Include any number of additional micro nutrients as needed
        }
    },
    "Other Information": ["Allergens", "Serving Size"],  // This should be in list format only
    // Add any other information you want to extract
}
"""
