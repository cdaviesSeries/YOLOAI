from typing import List
from eudoros.text_based.main import LLMProvider
from eudoros.text_based.openai_llm.constants import OpenAi_ModelEnum
from eudoros.text_based.utility import MessageUtility

globalPath = "/home/zigzalgo/series/centralized-pipelines-backend"

prompt = """
Given the file, and the associated diff,
review the code as if you were doing a pull request review. 
Do not discuss things like style, standards etc. Instead, focus entirely on logical errors such as bugs.
Very specifically explicit errors, and not possible errors.
"""

def handleDiff(diff: List[str]):
    filePath = globalPath + diff[0].split()[2][1:]
    with open(filePath, 'r', encoding='utf-8') as file:
        file_content = file.read()
        prov = LLMProvider().create_llm_client(OpenAi_ModelEnum.GPT_O_1_PREVIEW.name)

        message= prompt + "\nFile:\n```" + file_content+" \n```" + "\nDiff:\n```" + "".join(diff)+ "\n```"

        messages = MessageUtility.constructMessage(None, message)
        resp = prov.queryLongText(messages)

        with open(f"{diff[0].split()[2][1:].replace("/","_")}.md", "w") as outFile:
            outFile.write(resp)
        

def split_by_separator(lines: List[str], separator_keyword="diff"):
    result = []
    current_group = []

    for line in lines:
        if line.startswith(separator_keyword):
            if current_group:
                result.append(current_group)
            current_group = [line]
        else:
            if current_group:
                current_group.append(line)

    if current_group:
        result.append(current_group)

    return result

with open("diffs.txt", 'r', encoding='utf-8') as file:
    file_content = file.readlines()
    for x in split_by_separator(file_content):
        handleDiff(x)
