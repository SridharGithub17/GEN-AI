import yaml
 
def load_yaml_file(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)
 
def construct_few_shot_prompt(new_input):
    yaml_file_path = "data.yaml"
    yaml_data = load_yaml_file(yaml_file_path)
    few_shot_prompt = ""
    for example in yaml_data:
        input_example = example['input']
        sql_cmd_example = example['sql_cmd']
        few_shot_prompt += f"Question: {input_example}\n"
        few_shot_prompt += f"SQL Command:\n{sql_cmd_example}\n\n"
    
    few_shot_prompt+='Do not give any explainations and any other quotations before or after the query. \
                Return just the SQL query which can be run on a database server.\
                Use LIKE wildcard when asked to look for records. '
    few_shot_prompt += f"Question: {new_input}\nSQL Command:\n"
 
    return few_shot_prompt
 
# Example Usage
if __name__ == "__main__":
    # Load your YAML file

    new_question = "Find all transactions for 'Burger King' in the last 3 days."
    few_shot_prompt = construct_few_shot_prompt(new_question)
    print(few_shot_prompt)
 