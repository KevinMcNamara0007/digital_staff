import json

import fastapi
import pandas as pd
import numpy as np
from sklearn import feature_extraction, preprocessing, metrics
import seaborn as sns
import matplotlib.pyplot as plt

from src.utilities.inference2 import call_llm, call_openai


async def data_annotator_service(desc, rows, labels, model="elf"):
    prompt = (f'Instructions:'
              f'1. You are an expert data designer.'
              f'2. You will create {rows} rows of data based on the description: {desc}.'
              f'3. The following labels will be included: {labels},'
              f'4. Create only up to {rows} rows.'
              f'5. Do not include explanation.'
              '5. Respond in format:'
              ' "{"row":"1","label1":"label1Value","label2":"label2Value"},{"row":"2","label1":"label1Value","label2":"label2Value"}"'
              )
    try:
        if(model == "elf"):
            response = await call_llm(prompt, 6000, "/ask_an_expert")
        else:
            response = await call_openai(prompt)
        response = response \
            .replace("\n", "") \
            .replace("```json", "") \
            .replace("```", "") \
            .replace("[", "") \
            .replace("]", "") \
            .replace("}{", "},{")

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


async def get_matrix_service(key, source, training_set):
    data = json.loads(training_set)

    sentences = [item[source] for item in data]
    genres = [item[key] for item in data]

    vectorizer = feature_extraction.text.TfidfVectorizer()
    sentence_vectors = vectorizer.fit_transform(sentences).toarray()

    encoder = preprocessing.OneHotEncoder(sparse_output=False)
    genre_vectors = encoder.fit_transform(np.array(genres).reshape(-1, 1))

    combined_vectors = np.hstack((sentence_vectors, genre_vectors))
    similarity_matrix = metrics.pairwise.cosine_similarity(combined_vectors)

    df_sim = pd.DataFrame(similarity_matrix, index=[f"{s[:30]}...({g}" for s, g in zip(sentences, genres)],
                          columns=[f"{s[:30]}... ({g})" for s, g in zip(sentences, genres)])

    plt.figure(figsize=(35, 33))
    sns.heatmap(df_sim, annot=True, cmap="Blues", xticklabels=True, yticklabels=True)
    plt.title('Source-Label Correlation Matrix', fontsize=30)
    plt.xticks(fontsize=22)
    plt.yticks(ha="right", fontsize=20)
    plt.savefig('sourceLabel.png')
    plt.close()
    return fastapi.responses.FileResponse("sourceLabel.png")


async def generate_data_report(key, source, training_set):
    data = json.loads(training_set)
    df = pd.DataFrame(data)
    class_distribution = df[key].value_counts()
    classes = class_distribution.index.tolist()
    frequencies = class_distribution.values.tolist()

    plt.figure(figsize=(22,20))
    plt.bar(classes,frequencies)
    plt.title(f"Distribution of {class_distribution}", fontsize=20)
    plt.xticks(fontsize=22)
    plt.yticks(fontsize=22)
    plt.xlabel(key, fontsize=20)
    plt.ylabel("Frequency", fontsize=20)
    plt.xticks(ha="right")
    plt.savefig('balancer.png')
    plt.close()
    return fastapi.responses.FileResponse("balancer.png")

