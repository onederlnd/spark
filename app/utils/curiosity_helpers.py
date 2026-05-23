ABBREVIATIONS = {
    # General
    "idk": "i do not know",
    "imo": "in my opinion",
    "tbh": "to be honest",
    "btw": "by the way",
    "bc": "because",
    "b/c": "because",
    "w/": "with",
    "w/o": "without",
    "thru": "through",
    "tho": "though",
    "prolly": "probably",
    "ngl": "not going to lie",
    "nvm": "never mind",
    "pls": "please",
    "plz": "please",
    "thx": "thanks",
    "ty": "thank you",
    "ur": "your",
    "u": "you",
    "r": "are",
    "y": "why",
    "b4": "before",
    "rn": "right now",
    "ik": "i know",
    "lmk": "let me know",
    "omw": "on my way",
    "smh": "shaking my head",
    "fomo": "fear of missing out",
    # Academic
    "info": "information",
    "intro": "introduction",
    "avg": "average",
    "ex": "example",
    "eg": "for example",
    "ie": "that is",
    "vs": "versus",
    "approx": "approximately",
    "est": "estimate",
    "ref": "reference",
    "req": "requirement",
    "vocab": "vocabulary",
    "prob": "problem",
    "eq": "equation",
    "hw": "homework",
    "sem": "semester",
    # Subjects
    "bio": "biology",
    "chem": "chemistry",
    "phys": "physics",
    "psych": "psychology",
    "soc": "sociology",
    "phil": "philosophy",
    "hist": "history",
    "eng": "english",
    "stats": "statistics",
    "calc": "calculus",
    # Professional
    "asap": "as soon as possible",
    "fyi": "for your information",
    "tbd": "to be determined",
    "eta": "estimated time of arrival",
    "aka": "also known as",
    "atm": "at the moment",
    "wfh": "working from home",
    "dept": "department",
    "prof": "professor",
}


def normalize_question(raw_text):
    """
    Clean and standardize a student's question before hashing or sending to Claude.
    Returns a cleaned string.
    """
    import re

    cleaned = raw_text.lower()
    cleaned = cleaned.strip(" ")

    punctuation = "!#$%&()*+,-./:;<=>?@[\\]^_{|}~"
    for p in punctuation:
        cleaned = cleaned.replace(p, "")

    cleaned = " ".join(cleaned.split())

    for abbr, expanded in ABBREVIATIONS.items():
        cleaned = re.sub(rf"\b{re.escape(abbr)}\b", expanded, cleaned)

    return cleaned


def build_topic_key(subject, area, category, topic):
    """
    Produce a consistent slugified string key from topic components.
    Used as the cache partition key.
    """
    subject, area, category, topic = [
        s.lower().replace(" ", "-") for s in (subject, area, category, topic)
    ]

    topic_key = "_".join([subject, area, category, topic])

    return topic_key


def hash_question(normalized_text):
    """
    Return a short deterministic hash of a normalized question.
    Used as the second part of the cache lookup key.
    """
    import hashlib

    return hashlib.md5(normalized_text.encode("utf-8")).hexdigest()[:16]


def check_response_quality(response_text, grade_level=None):
    flags = []

    if len(response_text) < 100:
        flags.append("response_too_short")
    elif len(response_text) > 1000:
        flags.append("response_too_long")

    try:
        from app.models import get_db

        db = get_db()
        words = [
            row["word"]
            for row in db.execute("SELECT word FROM filtered_words").fetchall()
        ]
        lower_text = response_text.lower()
        for word in words:
            if word.lower() in lower_text:
                flags.append(f"filtered_word:{word}")
    except Exception:
        pass  # no app context — skip filtered words

    if grade_level:
        avg_word_length = sum(len(w) for w in response_text.split()) / max(
            len(response_text.split()), 1
        )
        if grade_level <= 5 and avg_word_length > 6:
            flags.append("readability_too_complex")

    return {"passed": len(flags) == 0, "flags": flags}


def build_enriched_prompt(
    base_prompt,
    topic_prompt,
    cached_context,
    subject,
    area,
    category,
    topic,
    description,
):
    """
    Assemble the full system prompt from all available layers.
    Returns a single system prompt string ready for Claude.
    """

    prompt = [base_prompt]

    if topic_prompt:
        prompt.append(topic_prompt)

    if cached_context:
        prompt.append(cached_context)

    topic_section = "-".join([subject, area, category, topic, description])

    prompt.append(topic_section)
    prompt = "\n\n".join(prompt)

    return prompt
