import json
from typing import  Iterable, List, cast
from eudoros.text_based.main import LLMProvider
from eudoros.text_based.utility import MessageUtility
from eudoros.text_based.openai_sdk.client import OpenAiClient
from openai.types.chat import ChatCompletionUserMessageParam
import sys
import os

from pydantic import BaseModel

globalPath = "/home/dougl/series/centralized-pipelines-backend"

prompt = """
Given the file, and the associated diff,
review the code as if you were doing a pull request review. 
Do not discuss things like style, standards etc. Instead, focus entirely on logical errors such as bugs.
Very specifically explicit errors, and not possible errors.
Include the entire line of code where the error is verbatim in the response.
"""

class Comment(BaseModel):
    short_summary: str
    problem_code: str

class FileIssues(BaseModel):
    issues: List[Comment]

class IssuesOutput(BaseModel):
    filepath: str
    issuesList: FileIssues
class AllIssues(BaseModel):
    fileList: List[IssuesOutput]


def handleDiff(diff: List[str], gitRoot):
    curPath = gitRoot if (os.path.isdir(gitRoot)) else globalPath
    relFilePath = diff[0].split()[2][2:]
    filePath = os.path.join(curPath, relFilePath)
    print(f"diffing file: {filePath}... ")

    with open(filePath, 'r', encoding='utf-8') as file:
        file_content = file.read()
        prov =LLMProvider.create_llm_client("gpt4m")

        message= prompt + "\nFile:\n```" + file_content+" \n```" + "\nDiff:\n```" + "".join(diff)+ "\n```"

        messages = cast(Iterable[ChatCompletionUserMessageParam], MessageUtility.constructMessage(message, None))
        if (isinstance(prov, OpenAiClient)):
            resp = prov.queryStructured(messages, FileIssues)
        if resp:
            content = json.loads(resp[0].message.content if resp[0].message.content else "")
            
        # regex bs
        retval = []
        for issue in content['issues']:
            found = False
            print(issue)
            # [4:] because we have to trim some info from the start of the diff
            # largely, the names of the files being diffed.
            for i, line in enumerate(diff[4:]): 
                if issue['problem_code'] in line:
                    found = True
                    retval.append({
                        "path": relFilePath,
                        "position": i,
                        "body": issue['short_summary'],
                    })
                    break
            # after enumerate
            if not found: 
                print(f"issue: `{issue['problem_code']}` not found.")
            
        print("done.")
        return retval
        

def split_by_separator(lines: List[str], separator_keyword="diff"):
    result = []
    current_group: List[str] = []

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

print(sys.argv)
with open(sys.argv[1], 'r', encoding='utf-8') as file:
    file_content = file.readlines()
    with open(sys.argv[3], 'w') as fd:
        retval = []
        for x in split_by_separator(file_content):
            retval.extend(handleDiff(x, sys.argv[2]))
        
        json.dump(retval, fd)


