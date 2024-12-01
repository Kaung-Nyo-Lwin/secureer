from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import pandas as pd
import numpy as np
import joblib


transformer = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
job_title_risk_model = joblib.load('./ml_models/job_title_risk_model')
df_title_risk = pd.read_csv('./ml_models/df_title_risk.csv')
df_skill = pd.read_csv('./ml_models/df_skill.csv')
onet_embeddings = transformer.encode(df_skill['O∗NET Description'].to_list())
recommender = joblib.load('./ml_models/recommender_model')
df = pd.read_csv('./ml_models/df_processed.csv')
df_posts = pd.read_excel('./ml_models/job_listings_query_result_2024-11-04T05_58_13.074135Z.xlsx')


def calculate_title_risk(title):
    title_embed = transformer.encode([title])
    cluster = job_title_risk_model.predict(title_embed)[0]
    labels = job_title_risk_model.labels_
    title_risk = float(np.mean(df_title_risk.iloc[np.where(labels == cluster)[0]]['Probability'])).__round__(2)
    return title_risk


def calculate_skill_risk(skills):
    skills_embed = transformer.encode([skills])
    mean_similarity = list()
    for skill in skills_embed:
        similarity = list()
        for onet in onet_embeddings:
            similarity.append(1 - cosine_similarity(skill.reshape(1, skill.shape[0]), onet.reshape(1, onet.shape[0]))[0])
        mean_similarity.append(np.sum(similarity))
    skill_risk = float(np.sum(mean_similarity) / (len(skills_embed) * len(onet_embeddings))).__round__(2)
    return skill_risk


def calculate_job_risk(title, skills):
    alpha = 1
    title_risk = calculate_title_risk(title)
    skill_risk = calculate_skill_risk(skills)
    risk = (title_risk + (alpha * skill_risk)) / 2
    return risk


def recommend_job(skills):
    query_emb = transformer.encode([skills])
    distances, indices = recommender.kneighbors(query_emb)
    recommended_titles = df.iloc[indices[0]]['Title'].to_list()
    recommended_skills = df.iloc[indices[0]]['Job Skills'].to_list()
    return recommended_titles, recommended_skills


def recommend_job_posts(titles):
    recommended_job_posts = list()
    for title in titles:
        recommended_job_posts.extend(
            df_posts[df_posts.Title == title][['Title', 'Updated At', 'Job Summary']].values.tolist())
    return recommended_job_posts