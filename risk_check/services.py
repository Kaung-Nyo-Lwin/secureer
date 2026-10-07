"""Offline reference matching and the original, lazily loaded ML pipeline.

The demo uses title overlap against the historical occupation table. It does not
pretend to run the semantic model, and returns no score for an unmatched title.
"""

import ast
import csv
import math
import re
from collections import Counter
from functools import lru_cache

from django.conf import settings

MINILM_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MINILM_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"

STOP_WORDS = {
    "and",
    "or",
    "of",
    "the",
    "a",
    "an",
    "at",
    "in",
    "for",
    "to",
    "with",
    "skill",
    "skills",
}


class AssessmentUnavailable(Exception):
    """The configured engine or its local artifacts could not be loaded."""


def tokens(text):
    words = re.findall(r"[\w+#]+", text.casefold())
    return {
        word[:-1]
        if word.endswith("s") and not word.endswith("ss") and len(word) > 3
        else word
        for word in words
        if word not in STOP_WORDS
    }


def split_skills(text):
    seen = {}
    for skill in re.split(r"\band\b|[,;\n]", text, flags=re.IGNORECASE):
        skill = " ".join(skill.split())
        if 2 < len(skill) <= 80:
            seen.setdefault(skill.casefold(), skill)
    return list(seen.values())


def read_csv(filename):
    with (settings.ML_MODELS_DIR / filename).open(
        encoding="utf-8-sig", newline=""
    ) as source:
        return list(csv.DictReader(source))


def risk_summary(score, reference="", explanation=""):
    if score is None:
        band, label = "unknown", "No close reference"
    else:
        score = round(max(0, min(100, float(score))), 1)
        band, label = (
            ("low", "Lower exposure")
            if score <= 40
            else (
                ("moderate", "Moderate exposure")
                if score <= 70
                else ("high", "Higher exposure")
            )
        )
    return {
        "score": score,
        "band": band,
        "label": label,
        "reference": reference,
        "explanation": explanation,
    }


class DemoEngine:
    name = "demo"
    label = "Offline reference demo"

    def __init__(self):
        self.occupations = read_csv("df_title_risk.csv")
        self.jobs = read_csv("df_processed.csv")
        self.job_tokens = [tokens(row["Job Skills"]) for row in self.jobs]
        counts = Counter(word for words in self.job_tokens for word in words)
        self.idf = {
            word: math.log((len(self.jobs) + 1) / (count + 1)) + 1
            for word, count in counts.items()
        }

    def risk(self, title, skills):
        query = tokens(title)
        best, best_score = None, 0
        for row in self.occupations:
            words = tokens(row["Occupation"])
            overlap = len(query & words)
            similarity = (
                2 * overlap / (len(query) + len(words)) if query and words else 0
            )
            if similarity > best_score:
                best, best_score = row, similarity
        if best_score < 0.6:
            return risk_summary(
                None,
                explanation="This title has no close keyword match in the historical occupation table. Try a more common role title.",
            )
        return risk_summary(
            float(best["Probability"]) * 100,
            best["Occupation"],
            "Historical occupation reference selected by title keywords. Your skills inform the career matches, but do not change this demo score.",
        )

    def recommend(self, skills):
        query = tokens(" ".join(skills))
        ranked = []
        for index, words in enumerate(self.job_tokens):
            overlap = query & words
            if not overlap:
                continue
            numerator = sum(self.idf[word] ** 2 for word in overlap)
            denominator = math.sqrt(
                sum(self.idf.get(word, 1) ** 2 for word in query)
                * sum(self.idf[word] ** 2 for word in words)
            )
            ranked.append((numerator / denominator, index))
        ranked.sort(key=lambda item: (-item[0], self.jobs[item[1]]["Title"]))
        return [self.jobs[index] for _, index in ranked[:5]]


class MLEngine(DemoEngine):
    name = "ml"
    label = "Semantic ML model"

    def __init__(self):
        # Import only when a visitor actually requests ML inference.
        import numpy as np
        from sentence_transformers import SentenceTransformer
        from sklearn.cluster import KMeans
        from sklearn.neighbors import NearestNeighbors

        self.np = np
        self.occupations = read_csv("df_title_risk.csv")
        self.jobs = read_csv("df_processed.csv")
        self.transformer = SentenceTransformer(MINILM_MODEL, revision=MINILM_REVISION)
        # The archived recommender contains 878 rows but the bundled CSV has 872.
        # Refit the original algorithms on these exact rows to preserve alignment
        # and avoid loading version-sensitive pickles from the class project.
        title_vectors = self.transformer.encode(
            [row["Occupation"] for row in self.occupations]
        )
        skill_vectors = self.transformer.encode(
            [row["Job Skills"] for row in self.jobs]
        )
        self.title_model = KMeans(n_clusters=20, random_state=42, n_init="auto").fit(
            title_vectors
        )
        self.recommender = NearestNeighbors(n_neighbors=5, metric="cosine").fit(
            skill_vectors
        )
        descriptions = [row["O∗NET Description"] for row in read_csv("df_skill.csv")]
        self.bottlenecks = self.transformer.encode(
            descriptions, normalize_embeddings=True
        )

    def risk(self, title, skills):
        np = self.np
        cluster = self.title_model.predict(self.transformer.encode([title]))[0]
        references = [
            float(row["Probability"])
            for index, row in enumerate(self.occupations)
            if self.title_model.labels_[index] == cluster
        ]
        if not references:
            raise ValueError("No occupation references for the predicted cluster.")
        skill_embedding = self.transformer.encode(
            [" and ".join(skills)], normalize_embeddings=True
        )
        distance = float(np.mean(1 - skill_embedding @ self.bottlenecks.T))
        score = (float(np.mean(references)) + max(0, min(1, distance))) / 2 * 100
        if not math.isfinite(score):
            raise ValueError("The model returned a non-finite score.")
        return risk_summary(
            score,
            "Occupational cluster + skill similarity",
            "Equal weighting of the occupation cluster’s historical average and skill distance from nine O*NET bottleneck descriptions. This experimental index is not a calibrated probability.",
        )

    def recommend(self, skills):
        embedding = self.transformer.encode([" and ".join(skills)])
        _, indices = self.recommender.kneighbors(embedding)
        return [self.jobs[int(index)] for index in indices[0]]


@lru_cache(maxsize=2)
def get_engine(name):
    try:
        return MLEngine() if name == "ml" else DemoEngine()
    except Exception as exc:
        raise AssessmentUnavailable(
            "Could not initialize the assessment engine."
        ) from exc


def assess(position, skills, engine_name=None):
    try:
        engine = get_engine(engine_name or settings.SECUREER_ENGINE)
        risk = engine.risk(position, skills)
        jobs, available_skills, seen_titles = [], [], set()
        query = tokens(" ".join(skills))
        for row in engine.recommend(skills):
            title = row["Title"]
            if title in seen_titles:
                continue
            seen_titles.add(title)
            job_skills = split_skills(row["Job Skills"])
            available_skills.extend(job_skills)
            industries = list(dict.fromkeys(ast.literal_eval(row["Industries"])))
            jobs.append(
                {
                    "title": title,
                    "industry": " · ".join(industries[:2]),
                    "skills": job_skills[:5],
                    "keywords": sorted(query & tokens(row["Job Skills"]))[:5],
                    "risk": engine.risk(title, job_skills),
                }
            )
        known = {frozenset(tokens(skill)) for skill in skills}
        matched = [
            skill
            for skill in skills
            if any(tokens(skill) == tokens(other) for other in available_skills)
        ]
        counts = Counter(
            skill for skill in available_skills if frozenset(tokens(skill)) not in known
        )
        suggested = [skill for skill, _ in counts.most_common(8)]
        return {
            "engine": engine.name,
            "engine_label": engine.label,
            "risk": risk,
            "jobs": jobs,
            "matched_skills": matched,
            "suggested_skills": suggested,
            "skills": skills,
            "position": position,
        }
    except AssessmentUnavailable:
        raise
    except Exception as exc:
        raise AssessmentUnavailable("Could not complete the assessment.") from exc
