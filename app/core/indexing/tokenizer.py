import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# Make sure resources are available
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

stemmer = PorterStemmer()
STOPWORDS = set(stopwords.words('english'))

def tokenize(text: str):
    tokens = nltk.word_tokenize(text.lower())
    tokens = [re.sub(r'\W+', '', t) for t in tokens if t.isalnum()]
    tokens = [stemmer.stem(t) for t in tokens if t and t not in STOPWORDS]
    return tokens
