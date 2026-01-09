from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
_sia = None
def _ensure():
    global _sia
    if _sia is None:
        try:
            _sia = SentimentIntensityAnalyzer()
        except LookupError:
            nltk.download('vader_lexicon')
            _sia = SentimentIntensityAnalyzer()
def polarity(text: str) -> dict:
    _ensure()
    scores = _sia.polarity_scores(text or "")
    c = scores.get("compound", 0.0)
    label = "positive" if c>=0.05 else ("negative" if c<=-0.05 else "neutral")
    return {"label":label, "score":float(c), "raw":scores}
