from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import pickle

# ---------------- TRAINING DATA ----------------

texts = [
    # Refund
    "I want my refund",
    "Please return my money",
    "Refund my order immediately",
    "I need a refund for my purchase",
    "My refund has not been processed",
    "Return my payment",
    "Cancel my order and refund",
    "Money back request",

    # Complaint
    "The product is damaged",
    "Very bad quality product",
    "I am unhappy with the service",
    "Worst experience ever",
    "The delivery was very late",
    "Customer service is terrible",
    "I received a broken item",
    "Extremely disappointed with the order",

    # Inquiry
    "What is the delivery time?",
    "How can I track my order?",
    "Do you have this in size M?",
    "When will my order arrive?",
    "Can you help me with my order?",
    "Is this product available?",
    "How long does shipping take?",
    "Where is my order?",

    # Feedback
    "Great service",
    "I love this product",
    "Very satisfied with the experience",
    "Amazing quality",
    "Keep up the good work",
    "Excellent support",
    "Happy with the purchase",
    "Fantastic experience"
]

labels = [
    # Refund
    "refund","refund","refund","refund","refund","refund","refund","refund",

    # Complaint
    "complaint","complaint","complaint","complaint",
    "complaint","complaint","complaint","complaint",

    # Inquiry
    "inquiry","inquiry","inquiry","inquiry",
    "inquiry","inquiry","inquiry","inquiry",

    # Feedback
    "feedback","feedback","feedback","feedback",
    "feedback","feedback","feedback","feedback"
]

# ---------------- VECTORIZE ----------------
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)

# ---------------- TRAIN MODEL ----------------
model = MultinomialNB()
model.fit(X, labels)

# ---------------- SAVE FILES ----------------
pickle.dump(model, open("intent_model.pkl", "wb"))
pickle.dump(vectorizer, open("vectorizer.pkl", "wb"))

print("✅ Model training complete.")
print("Files saved:")
print("- intent_model.pkl")
print("- vectorizer.pkl")