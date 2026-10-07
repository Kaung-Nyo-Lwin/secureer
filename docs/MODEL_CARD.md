# Secureer model card

## Purpose

Secureer is an academic career exploration prototype. It connects a role and a set of skills to historical occupational automation research and related roles from a Myanmar job dataset. Its intended use is exploratory learning and discussion.

The app produces an exposure index, related role examples, exact normalized skill matches, and additional skills observed in those roles. It does not establish hiring suitability or individual employment outcomes.

## Included data

- **872 processed job-title rows:** `ml_models/df_processed.csv`, prepared from MyJob data for the 2024 class project. Each row contains a title, industries, and a combined skill description.
- **702 occupation rows:** `ml_models/df_title_risk.csv`, containing occupation names and historical computerisation probabilities from the Frey and Osborne framework.
- **9 bottleneck descriptions:** `ml_models/df_skill.csv`, covering O*NET variables associated with perception and manipulation, creative intelligence, and social intelligence.

Counts describe the files included in this repository. They do not measure the size, representativeness, or current coverage of the labor market.

## Offline reference demo

The demo uses no learned model or external inference service. Text is lowercased, tokenized, stripped of a short stop-word list, and given conservative plural normalization.

### Title reference

For query tokens `Q` and occupation tokens `O`, title similarity is:

```text
similarity = 2 × |Q ∩ O| / (|Q| + |O|)
```

The occupation with the largest overlap is selected when similarity is at least **0.6**. Ties follow the source-table order. Its historical probability is multiplied by 100 to display a reference index. A weak or absent match produces **no score**, with an explanation.

Skills do not change this demo reference index. Keyword matches can still join occupations that share words but differ in duties, so the matched reference is shown explicitly.

### Role recommendations

The query is the union of submitted skill tokens. Each role is represented by the tokens in its source skill description. A token’s weight is:

```text
idf(token) = log((number_of_roles + 1) / (roles_containing_token + 1)) + 1
```

Binary token vectors weighted by `idf` are compared using cosine similarity. Only roles sharing at least one token are considered; up to five are returned. Role titles break equal-score ties. An unmatched skill query receives an empty result instead of arbitrary suggestions.

Query tokens absent from the source vocabulary receive a weight of 1. Similarity values are used for ordering and are not displayed as skill-fit probabilities.

## Semantic ML pipeline

The optional engine uses `sentence-transformers/all-MiniLM-L6-v2` to encode text into 384-dimensional embeddings. The model revision is pinned to `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, and the direct ML dependencies are pinned in `requirements-ml.txt` to the versions used for the verified semantic run.

1. Encode all included occupation names and fit **K-means with 20 clusters**, `random_state=42`, and `n_init="auto"`.
2. Encode all included career skill descriptions and fit **five-neighbor cosine nearest neighbors**.
3. Encode the nine bottleneck descriptions with normalized embeddings.
4. Assign the submitted role to its nearest occupation cluster and retrieve roles using the submitted skill embedding.

The exposure score is:

```text
title_component = mean(historical probabilities in the predicted cluster)
skill_component = clip(mean(1 − cosine_similarity(skills, each bottleneck)), 0, 1)
index = 100 × (title_component + skill_component) / 2
```

The resulting index is bounded to 0–100 and displayed to one decimal place. Clamping the skill distance prevents negative cosine similarity from taking the index outside the scale. The components retain the original project’s equal weighting; this weighting has not been calibrated to observed job-loss outcomes.

Models are fitted on first use and cached within each process. Package versions and model revisions can affect numerical results. There is no claimed held-out predictive accuracy for individual automation exposure.

### Archived artifact alignment

The archived `job_title_risk_model` and `recommender_model` are scikit-learn 1.4.2 pickles. The recommender contains **878 training rows**, while the included career table contains **872 rows**. It cannot safely index the current table without the exact training-row mapping.

The web application does not load those pickles. Rebuilding both algorithms from the included CSV rows establishes explicit alignment and avoids cross-version deserialization. As a result, semantic results can differ from the original demo video.

## Skills and display bands

Source skill descriptions are split into individual labels. Matches compare normalized token sets, ignoring case, the listed stop words, and conservative plurals. This is stricter than semantic similarity and can produce no exact matches even when a related role is recommended.

Additional skills are ordered by how often they occur in the selected roles, excluding normalized matches to the submitted profile. The app displays up to eight labels. These are observed source skills, not a personalized curriculum.

| Index | Interface band |
|---|---|
| 0–40 | Lower exposure |
| >40–70 | Moderate exposure |
| >70–100 | Higher exposure |
| No close demo reference | No score |

The bands are presentation conventions, not validated decision thresholds. Recommendations are ordered by skill similarity, rather than increasing or decreasing exposure.

## Interpretation limits

The underlying occupation research is historical, predates recent generative AI developments, and describes a different labor market. Transferring its occupation scores to Myanmar is an experimental assumption. Keyword overlap, embeddings, occupational clusters, and mean skill distances cannot establish an individual’s job security.

The source data has inconsistent titles, abbreviated skills, and uneven industry coverage. Similarity does not account for qualifications, working conditions, salary, location, interests, or hiring requirements. The system supplies role examples from a 2024 snapshot and does not verify current vacancies.

## Data handling

Inference runs on the app server. Model weights may be downloaded on first ML use; profile text is not sent to a hosted model service. Name is optional. Submitted names, roles, skills, and report snapshots are stored in the app database.

Reports can only be accessed through the session that created them. The site operator can access the database. A session remembers up to 20 recent reports, and server records remain until deleted. The result page provides a deletion action. Closing a browser or losing its session does not remove stored records; production operators should establish retention and cleanup appropriate to their demo.

## Research materials

See the [original notebook](../Job_Automation_Risk_Prediction.ipynb), [academic report](../Job_Automation_Risk_Prediction_and_job_recommender_system.pdf), and [presentation](../Job_Automation_Risk_Prediction_and_job_recommender_system_presentation.pdf) for the original work and references.
