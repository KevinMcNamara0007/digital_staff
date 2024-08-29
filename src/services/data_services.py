import json

import pandas as pd


async def data_annotator_service(desc, rows, labels):
    prompt = (f'Instructions:'
              f'1. You are an expert data designer.'
              f'2. You will create {rows} rows of data based on the description: {desc}.'
              f'3. The following labels will be included: {labels},'
              f'4. Create only up to {rows} rows.'
              '5. Respond in format:'
              ' "{"row":"1","label1":"label1Value","label2":"label2Value"},{"row":"2","label1":"label1Value","label2":"label2Value"}"'
              )
    try:
        response = ""

        response_list = []
        response = response \
            .replace("\n","") \
            .replace("```json","") \
            .replace("```","") \
            .replace("[","") \
            .replace("]","")

        list = []
        for row in response.split('},'):
            try:
                if not row.endswith('}'):
                    obj = json.loads(row + '}')
                else:
                    obj = json.loads(row)
                list.append(obj)
            except Exception as exc:
                print(row)
                print(exc)
        return list
    except Exception as exception:
        return f"LLM Error: {exception}"